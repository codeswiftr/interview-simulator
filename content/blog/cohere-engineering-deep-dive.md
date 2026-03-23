# Cohere Engineering Deep Dive: LLM Infrastructure, RAG at Enterprise Scale, and What the Interview Tests

Cohere occupies a distinct position in the LLM landscape. Unlike OpenAI, which built consumer products first and enterprise offerings second, Cohere was designed from day one as a B2B AI infrastructure company. The company's thesis is that the enterprises with the most valuable data — banks, healthcare systems, legal firms, logistics providers — cannot hand that data to a third-party API. They need models they can run inside their own cloud environment. This architectural bet shapes everything: how Cohere builds models, how they serve them, and what they look for in the engineers they hire.

## LLM Serving Infrastructure: Latency, Throughput, and the KV Cache

Serving a 70-billion-parameter language model at commercial scale is a different class of engineering problem from training one. Training is batch-optimal: you can afford to wait for a gradient step. Inference is interactive: users and downstream systems expect tokens in milliseconds, not seconds, and they expect that latency to hold as concurrent request volume grows.

The fundamental constraint is the **key-value (KV) cache**. During autoregressive generation, every new token must attend to all previous tokens. The key and value projections for those previous tokens are computed once and cached in GPU VRAM. This cache grows linearly with sequence length: a 32K-context Command R model attending to a 30,000-token enterprise document holds roughly `2 × num_layers × num_kv_heads × head_dim × seq_len × dtype_bytes` per sequence. For a typical large model, that is 4–8 GB of VRAM per long-context sequence. Multiply by concurrent users, and the memory ceiling becomes the binding constraint, not FLOP capacity.

**Continuous batching** is the production-critical technique for maximizing GPU utilization under this constraint. Naive static batching groups requests into fixed batches and waits for the entire batch to finish before admitting new requests. Because sequences finish generating at different times — a two-sentence answer finishes long before a 2,000-word report — this approach leaves GPU cores idle for the tail of every batch. Continuous batching (iteration-level scheduling) evicts finished sequences and admits new ones at every forward pass:

```python
class ContinuousBatchScheduler:
    def __init__(self, max_tokens_in_flight: int):
        self.active: dict[str, Sequence] = {}
        self.waiting: deque[Request] = deque()
        self.max_tokens = max_tokens_in_flight

    def step(self) -> list[GeneratedToken]:
        # Evict sequences that hit EOS or max_new_tokens
        finished = [sid for sid, s in self.active.items() if s.is_done()]
        for sid in finished:
            del self.active[sid]

        # Admit waiting requests if token budget allows
        while self.waiting:
            req = self.waiting[0]
            projected = sum(s.allocated_tokens for s in self.active.values())
            if projected + req.max_new_tokens > self.max_tokens:
                break
            self.active[req.id] = Sequence(req)
            self.waiting.popleft()

        # One forward pass: all active sequences advance one token
        return self.model_forward(list(self.active.values()))
```

**Speculative decoding** addresses the latency half of the equation. A small draft model (1–3B parameters) generates candidate tokens cheaply; the larger target model verifies a block of candidates in a single parallel forward pass. When the draft is correct — which happens most of the time for common phrases and boilerplate — the target model advances by 3–5 tokens for the cost of one forward pass, cutting wall-clock latency by 2–3x on typical enterprise text without changing output distribution.

For Cohere specifically, their Command models are served via the Cohere API and also packaged for private deployment. The serving stack must handle both paths with the same correctness guarantees.

## RAG at Enterprise Scale: Embed, Rerank, and the Architecture of Retrieval

Cohere's most technically distinctive product line is their embedding and reranking infrastructure. Most LLM companies treat retrieval as the customer's problem. Cohere treats it as a core engineering investment, and their Embed and Rerank models exist as first-class API products precisely because enterprise RAG pipelines are where their deployment story is strongest.

A production RAG pipeline has three latency-sensitive stages that Cohere's models are designed to slot into:

**Stage 1: Offline indexing.** Documents are chunked, embedded using Cohere Embed (1024-dimensional dense vectors for semantic search), and written to a vector store (Pinecone, Weaviate, OpenSearch with kNN, or pgvector). At enterprise scale — millions of documents across a legal database or an internal knowledge base — this indexing pipeline runs continuously as documents are added or updated. Embedding throughput is measured in documents per second; Cohere's batch embedding API is optimized for this.

**Stage 2: Online retrieval.** A user query arrives. Hybrid retrieval combines dense vector search (semantic similarity via approximate nearest neighbor, typically HNSW) with sparse retrieval (BM25 keyword matching). Neither alone is sufficient: dense search finds semantically related but keyword-different results; sparse search finds exact matches but misses paraphrases. The union typically improves recall@K by 15–30% over either approach individually. Reciprocal Rank Fusion (RRF) is the standard technique for merging the two ranked lists without requiring calibrated scores.

**Stage 3: Reranking.** The initial retrieval returns 20–100 candidates quickly (ANN search is fast). A cross-encoder reranker reads each candidate document alongside the query and produces a calibrated relevance score. Cross-encoders are accurate but slow — O(k) sequential forward passes instead of one. Cohere Rerank runs this step, and the engineering tradeoff is explicit: reranking 20 documents with Rerank adds 80–150ms of latency but typically improves NDCG@5 by 20–40% over vector search alone. For an enterprise search use case where the user reads the top result, that quality improvement justifies the latency.

The systems design implication is a two-tier architecture: a fast ANN index for recall, a cross-encoder reranker for precision, with the reranker's top-K fed to the LLM context window. The choice of K (how many documents to rerank, how many to pass to the LLM) is an engineering decision that trades latency, cost, and context window utilization.

## Model Training Infrastructure: Parallelism at Scale

Training Command-scale models requires coordinated compute across hundreds to thousands of GPUs. The parallelism strategy determines whether that coordination is efficient or wasteful.

**Data parallelism** is the simplest approach: each GPU holds a full model replica and processes a different micro-batch. Gradients are all-reduced across replicas (ring-allreduce) after each backward pass. This scales well in compute but hits a hard ceiling when the model itself does not fit in one GPU's VRAM.

**Tensor parallelism** (intra-layer) shards individual weight matrices across GPUs. An attention layer's query, key, and value projections are split column-wise across N GPUs; each GPU computes its shard of the attention output, and an allreduce synchronizes before the next layer. This requires synchronization at every layer, so it is best suited for GPUs with fast intra-node interconnects (NVLink). Typically applied within a single node (8 GPUs).

**Pipeline parallelism** (inter-layer) assigns different transformer layers to different GPUs. GPU 0 holds layers 0–8, GPU 1 holds layers 9–16, and so on. Micro-batches flow through the pipeline, and GPUs process different micro-batches at different stages simultaneously (1F1B scheduling). This allows models that would not fit on any single node to be distributed across nodes connected by slower inter-node fabric.

At Cohere's scale, these three strategies are combined: data parallelism across pipeline stages, tensor parallelism within each node, pipeline parallelism across nodes. Managing training runs at this scale requires robust checkpoint storage (model states, optimizer states, and gradient scalers checkpoint every few hundred steps against GPU failures), experiment tracking (Weights & Biases or internal tooling for loss curves, gradient norms, activation statistics), and fault-tolerant training loops that resume from the last clean checkpoint without restarting the entire run.

## Enterprise Deployment Patterns: Private Cloud and Quantization

Cohere's commercial differentiation lives here. Their model deployment story targets enterprises that want Command-quality models running inside their AWS VPC, Azure subscription, or on-premises GPU cluster — not making API calls that route their data through Cohere's infrastructure.

Packaging an LLM for private deployment requires solving several problems that API serving does not:

**Container packaging.** The model weights, serving runtime, and dependencies must be bundled into a container image deployable to standard Kubernetes environments. Cohere packages their models as Helm charts deployable to EKS, GKE, or AKS. The image size for a 70B model is non-trivial, and layer caching in container registries is an operational concern.

**Quantization for cost reduction.** Full-precision (BF16) inference requires approximately 140 GB of GPU VRAM for a 70B model. INT8 quantization halves that to ~70 GB; INT4 quantization reduces it to ~35 GB. Techniques like GPTQ and AWQ apply post-training quantization with minimal quality degradation by quantizing weights while preserving activation precision. For enterprise customers, the ability to run a Command R model on a single 8×A10G node (80 GB × 8 = 640 GB total, but per-model footprint determines concurrent capacity) rather than requiring 8×A100-80GB nodes significantly changes the economics.

**Serving SLA management.** An enterprise running LLMs privately owns their own SLA. The deployment must include autoscaling (scale replicas based on request queue depth), health checking, rolling updates that avoid serving disruption, and observability (token throughput, queue latency, VRAM utilization) via Prometheus-compatible metrics endpoints.

## Interview Implications: What Cohere Actually Tests

Cohere's engineering culture sits at the intersection of ML knowledge and systems depth — closer to the ML-systems engineering profile at DeepMind or Google Brain than to the pure software engineering culture at Stripe or Shopify, but more production-engineering-focused than pure ML research organizations.

The company is not hiring researchers to discover new architectures. They are hiring engineers to make large models reliable, fast, and deployable in production environments that range from multi-tenant API to customer-controlled VPCs. That profile shows up directly in their interview design.

**System design questions** will ask you to design an LLM serving system — expect to demonstrate knowledge of KV cache management, continuous batching, request scheduling, autoscaling under memory constraints, and latency vs. throughput tradeoffs. "Design a RAG pipeline for enterprise document search" is another common framing: expect to cover chunking strategy, embedding model choice, ANN index selection, hybrid retrieval, reranking, prompt construction, and observability.

**ML depth** is tested but at the application layer, not the research layer. You should understand transformer attention mechanics well enough to reason about KV cache size and memory footprint. You should know the tradeoffs between different quantization methods. You should be able to discuss why speculative decoding works and when the acceptance rate degrades.

**Distributed systems** come up through the lens of training infrastructure: data parallelism vs. model parallelism, gradient communication patterns, fault tolerance in long-running training jobs, checkpoint design under storage and latency constraints.

What Cohere values is an engineer who sees LLM infrastructure as a systems problem first — one that requires the same distributed systems rigor as building a high-throughput database or a low-latency stream processor, applied to a domain where the compute primitive is a transformer forward pass rather than a disk read or a network packet.
