# OpenAI Engineering Deep Dive: GPT Infrastructure and API at Consumer Scale

OpenAI went from a research lab to running one of the most heavily trafficked services on the internet inside of two years. ChatGPT crossed 100 million users in two months — faster than any consumer application in history. Behind that growth is a set of genuinely hard engineering problems: distributed training at scale, a serving architecture that streams tokens to millions of concurrent sessions, and an API platform that handles billing, rate limiting, and function orchestration for hundreds of thousands of developers. If you're interviewing for an engineering role at OpenAI or at any AI-first company, understanding how these systems work is table stakes.

## Distributed Training: Thousands of GPUs Working as One

GPT-4 was trained on tens of thousands of A100 and H100 GPUs. Coordinating a job at that scale requires solving problems that don't exist at smaller sizes.

The core challenge is that a single model may not fit in the VRAM of even a single node. OpenAI uses a combination of three parallelism strategies:

**Tensor parallelism** splits individual layers across GPUs. A single attention head computation is sharded so that each GPU handles a slice, and an AllReduce collective combines results at the end of each layer. This requires extremely fast interconnects — NVLink within a node, InfiniBand between nodes — because the communication overhead is on the critical path for every forward pass.

**Pipeline parallelism** assigns different layers to different groups of GPUs. Each micro-batch flows through stages like an assembly line. Bubble time (GPUs sitting idle waiting for upstream stages) is minimized by interleaving multiple micro-batches in flight simultaneously (the 1F1B schedule).

**Data parallelism** runs multiple pipeline replicas in parallel on different data shards, with gradient synchronization across replicas at the end of each step.

Mixed-precision training runs activations in FP16 or BF16 to double effective memory bandwidth, while keeping master weights in FP32 to avoid accumulation errors. Gradient checkpointing trades compute for memory: rather than storing all activations in the forward pass, only checkpoint activations at layer boundaries and recompute the rest during backprop. This cuts activation memory by roughly the square root of the number of layers, at the cost of about 33% more compute.

## ChatGPT Serving: Streaming Tokens to 100 Million Users

The shift from research to consumer product forced OpenAI to solve inference at a scale GPT-3 never anticipated. Two architectural decisions define how ChatGPT works at the API boundary.

**KV-cache management** is the central challenge in LLM serving. For each token in the context window, the attention mechanism computes key and value matrices that can be reused for subsequent token generation. Caching these avoids recomputing attention over the entire context for every output token, but the cache grows with sequence length and must be managed across thousands of concurrent requests. Systems like PagedAttention (the technique behind vLLM) treat KV-cache as virtual memory pages that can be allocated, swapped, and shared across requests — enabling much higher throughput than naive implementations.

**Streaming via Server-Sent Events** is how tokens appear to users in real time rather than after the full response is generated. The model generates one token at a time; each token is flushed to the client immediately over an SSE connection. This dramatically improves perceived latency — the first token appears in under a second, even for responses that take ten seconds to complete.

```python
import openai

client = openai.OpenAI()

def stream_completion(prompt: str) -> None:
    """Stream tokens as they're generated rather than waiting for full response."""
    with client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content is not None:
                # Each chunk arrives as soon as the token is generated
                print(delta.content, end="", flush=True)
        print()  # Newline after streaming completes

stream_completion("Explain gradient checkpointing in three sentences.")
```

When ChatGPT went from 0 to 100M users, OpenAI had to scale horizontally across many inference clusters, implement aggressive request batching (grouping multiple short requests together to maximize GPU utilization), and manage speculative decoding where a smaller draft model generates candidate tokens that the larger model verifies in parallel.

## The OpenAI API: Token Economics and Rate Limiting

The API platform has to solve three hard problems simultaneously: accurate billing by the token, fair multi-tenant resource allocation, and developer-friendly tooling.

**Token-based pricing** requires counting tokens at both the input and output side. Tokenization is done with tiktoken, a BPE tokenizer. The billing system must be accurate to the token because small rounding errors at scale become significant revenue discrepancies.

**Rate limiting** operates on two dimensions: tokens per minute (TPM) and requests per minute (RPM). TPM is the more important constraint because it maps directly to GPU capacity. A single request consuming 128k tokens blocks the equivalent of hundreds of short requests. Rate limits are enforced per API key with token-bucket algorithms: a bucket refills at a steady rate up to a maximum capacity, and requests that would exceed the bucket are rejected with a 429.

**Function calling** is architecturally interesting because it requires the model to output structured JSON that conforms to a user-provided schema, rather than free-form text. The system prompt is augmented with a serialized description of available functions; the model learns to emit function call objects that the client can dispatch and return results for. This enables the multi-turn tool-use loops that underlie ChatGPT's Plugins and Assistants APIs.

## Multimodal: CLIP and DALL-E Integration

GPT-4V and DALL-E 3 represent OpenAI's multimodal surface. CLIP (Contrastive Language–Image Pre-Training) trains a vision encoder and a text encoder jointly, pulling together embeddings of matching image-text pairs and pushing apart non-matching ones. The resulting embedding space lets you compare images and text directly by cosine similarity.

DALL-E 3 uses a diffusion model conditioned on CLIP text embeddings, with an additional recaptioning step where GPT-4 rewrites user prompts into more detailed descriptions before generation. This pipeline produces images that are more faithful to complex prompts than earlier approaches because the conditioning signal is richer.

For interviews, the key insight is that multimodal systems often require separate model towers per modality with a shared embedding space — and the engineering challenge is managing the latency and cost of running multiple models per request.

## Interview Implications

When interviewing at OpenAI or similar AI-first companies, expect system design questions that require reasoning about GPU topology, memory hierarchies, and the specific trade-offs of serving long-context models. Know the difference between tensor and pipeline parallelism and when you'd use each. Understand why streaming requires different infrastructure than batch inference. Be able to describe how you'd implement rate limiting for a multi-tenant API where cost is denominated in tokens rather than requests.

For coding rounds, streaming and async patterns are common. You should be comfortable writing Python that handles SSE streams, implements retry logic with exponential backoff around 429s, and correctly counts tokens using tiktoken before sending requests.

The scale OpenAI operates at is not accidental — it reflects deliberate architectural choices made under pressure, and understanding those choices is what separates candidates who have read the docs from candidates who have thought deeply about the problems.
