---
title: "Vector Database Engineer Guide: Embeddings, ANN, and RAG Architecture"
description: "Complete guide to vector database engineering for AI infrastructure interviews: embeddings, HNSW and IVF algorithms, Pinecone vs Weaviate vs Qdrant vs pgvector, RAG patterns, and hybrid search."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# Vector Database Engineer Guide: Embeddings, ANN, and RAG Architecture

Vector databases have gone from a niche research topic to a foundational component of production AI systems in under three years. Engineering roles at AI companies, developer tool startups, and enterprises building LLM-powered products now require genuine understanding of how vector search works — not just which API to call. This guide prepares you for AI infrastructure engineering interviews where vector databases are a core topic.

## Embeddings and Similarity Search

An **embedding** is a dense numerical vector that encodes semantic meaning — produced by models like OpenAI's `text-embedding-3-large`, Cohere's Embed v3, or open-source models like `nomic-embed-text` or `bge-large-en`. Two pieces of text with similar meaning should produce vectors that are close together in the embedding space, while semantically different texts should be far apart.

**Similarity metrics** are the first concepts interviewers probe. **Cosine similarity** measures the angle between two vectors, making it invariant to vector magnitude — the right choice when the magnitude of an embedding carries no semantic information (common for normalized embeddings). **Dot product** is equivalent to cosine similarity when vectors are L2-normalized, but preferred when magnitude encodes relevance signal (like in ColBERT-style multi-vector models). **Euclidean distance (L2)** is geometrically intuitive but sensitive to magnitude — used in some image embedding contexts. Know which metric a given model was trained with and match it at query time; mixing metrics degrades recall.

The core challenge: finding the most similar vectors in a corpus of millions or billions requires sub-linear search — exhaustive comparison of every pair is O(n) per query and becomes unacceptably slow at scale. This is why approximate nearest neighbor (ANN) algorithms exist.

## ANN Algorithms: HNSW, IVF, and ScaNN

**HNSW (Hierarchical Navigable Small World)** builds a multi-layer graph where each node connects to its approximate nearest neighbors. The top layers contain long-range connections (skipping far across the space); lower layers contain progressively shorter-range connections. Query traversal starts at the top layer, greedily navigates toward the target, then descends. HNSW achieves excellent recall/speed tradeoffs and supports incremental insertion without rebuilding — making it the dominant algorithm in most vector databases. Key parameters: `M` (connections per node — affects memory and recall), `ef_construction` (beam width during index build — recall vs. build time), `ef` (beam width during query — recall vs. query latency).

**IVF (Inverted File Index)** partitions the vector space into Voronoi cells using k-means clustering. Each vector is assigned to its nearest centroid. At query time, you probe the `nprobe` nearest centroids and search only within those cells. IVF is memory-efficient and amenable to compression via **PQ (Product Quantization)** — which divides vectors into subvectors and quantizes each independently, compressing 1536-dimensional float32 vectors (6KB) to as few as 64 bytes. IVF+PQ (commonly called IVFFlat vs IVFPQ in FAISS) is the standard for memory-constrained billion-scale search.

**ScaNN (Scalable Nearest Neighbors)** from Google uses anisotropic quantization that optimizes for the direction of maximum importance during query, achieving higher recall than symmetric PQ at comparable compression ratios. It underpins Google's search and is available as an open-source library.

## Major Vector Databases: Pinecone, Weaviate, Qdrant, pgvector

**Pinecone** is a fully managed vector database with a simple API optimized for production LLM applications. It handles infrastructure entirely (no index tuning exposed), supports metadata filtering with ANN (not post-filtering), and offers pods (dedicated compute) and serverless (pay-per-query) tiers. Tradeoffs: less configurability, vendor lock-in, cost at scale.

**Weaviate** is an open-source vector database with a strong schema and multi-tenancy model, built-in text vectorization (can call embedding models automatically on ingest), hybrid search (BM25 + vector), and a GraphQL query interface. Runs self-hosted or as a managed cloud service. Good fit for complex schemas with rich metadata.

**Qdrant** is a high-performance open-source vector store written in Rust, emphasizing speed and filtering efficiency. Its **payload indexing** enables efficient pre-filtering before ANN search (not all systems handle this well — some do ANN first, then filter, losing recall). Supports named vectors per point (multiple embeddings per document).

**pgvector** is a PostgreSQL extension that adds vector similarity search to Postgres. It uses HNSW or IVFFlat indexes depending on version and supports exact and approximate queries. The compelling proposition: if you already run Postgres, you don't need a separate vector database for moderate scale (tens of millions of vectors). Tradeoffs versus dedicated vector DBs: lower throughput at scale, no horizontal sharding native to the extension.

## RAG Architecture Patterns

**Retrieval-Augmented Generation (RAG)** is the dominant pattern for grounding LLMs in proprietary or recent data. The basic pipeline: chunk documents, generate embeddings, store in a vector database, embed the user query, retrieve top-k similar chunks, inject retrieved context into the LLM prompt, generate a response.

Advanced RAG patterns worth knowing for senior interviews: **HyDE (Hypothetical Document Embeddings)** — generate a hypothetical answer to the query first, embed that, and retrieve against it (improves recall for question-answering). **Multi-vector retrieval** (parent-child chunking, summary indexing). **Re-ranking** — retrieve a larger candidate set with ANN, then re-rank with a cross-encoder for higher precision. **Query decomposition** for multi-hop questions.

## Hybrid Search: Dense + Sparse Vectors

Pure semantic search misses exact keyword matches — a user searching for a product SKU or a proper noun expects exact match behavior. **Hybrid search** combines dense vector similarity with sparse retrieval (BM25 or SPLADE sparse neural models). The scores from both systems are merged using Reciprocal Rank Fusion (RRF) or a weighted combination. Weaviate, Qdrant, and Elasticsearch all support hybrid search natively. Knowing how to tune the relative weighting between semantic and keyword signals, and when each dominates (brand new terminology → sparse; conceptual questions → dense), is a practical skill interviewers probe.
