---
title: "Search Infrastructure Engineer Interview Guide: Elasticsearch, Ranking & Relevance"
description: "Master search engineering interviews — inverted index internals, Elasticsearch cluster management, BM25 vs TF-IDF, learning-to-rank, query understanding, and vector search."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Search Infrastructure Engineer Interview Guide: Elasticsearch, Ranking & Relevance

Search engineering is a discipline that blends information retrieval theory, distributed systems, and machine learning. Search teams at Google, Amazon, LinkedIn, Airbnb, Shopify, and every major consumer platform need engineers who understand relevance ranking, search infrastructure, and the product thinking behind great search experiences. This guide covers what search infrastructure interviews test.

## Inverted Index and Information Retrieval Fundamentals

Understanding how search engines work at the data structure level is the foundation interviewers build on:

**Inverted index**: Maps terms to the documents containing them, with frequency and position information. Building an inverted index involves tokenization (splitting text into terms), normalization (lowercasing, stemming, lemmatization), stopword removal, and term-frequency collection. This is the core data structure of Lucene (which powers Elasticsearch, Solr, OpenSearch).

**TF-IDF**: Term Frequency × Inverse Document Frequency. TF rewards terms that appear frequently in a document; IDF penalizes terms that appear in many documents (common words). The product gives a relevance signal that downweights stop words and upweights discriminative terms.

**BM25 (Best Match 25)**: The modern evolution of TF-IDF, used as the default in Elasticsearch 5+. Introduces document length normalization (prevents long documents from always winning) and a saturation term (term frequency has diminishing returns after a point). Know the key parameters: `k1` (term frequency saturation) and `b` (document length normalization). Be ready to explain why BM25 outperforms vanilla TF-IDF.

**Tokenization and analysis**: Elasticsearch analyzers compose tokenizers + token filters. Standard analyzer (whitespace split + lowercase + common word removal) vs. language-specific analyzers vs. custom. ngram tokenizers for prefix search, edge-ngram for autocomplete, pattern tokenizers for structured fields.

## Elasticsearch Cluster Architecture

Production Elasticsearch involves operational complexity beyond simple queries:

**Cluster roles**: Master nodes (cluster state management, index creation/deletion — CPU-light, stability-critical), data nodes (shard storage and search — disk/memory intensive), coordinating nodes (query fan-out/aggregation — network intensive), and ingest nodes (document preprocessing pipelines). Separating roles prevents data node instability from crashing the cluster.

**Shard design**: Sharding affects parallelism and scalability. Over-sharding (too many small shards) wastes overhead; under-sharding (too few large shards) limits parallelism. A practical heuristic: 10-50GB per shard. Primary shards are fixed at index creation — plan for growth. Replica shards improve read throughput and availability.

**Index lifecycle management (ILM)**: Time-series data (logs, events) naturally grows unbounded. ILM policies automate rollover (create new index when old exceeds size/age), shrink (reduce shard count on older data), freeze (move to cold tier), and delete. This is essential knowledge for log/observability platform roles.

**Query performance tuning**: `filter` context vs. `query` context — filters are cached (use for structured data: date ranges, status fields); query context scores documents (use for full-text search). `_source` filtering, `docvalue_fields` for structured data retrieval, and `profile` API for query plan analysis.

## Learning to Rank and Relevance Tuning

Pure BM25 is insufficient for high-quality search at scale. Relevance engineering combines retrieval with ranking:

**Feature engineering for ranking**: User behavior signals (click-through rate, dwell time, conversion), document quality signals (PageRank-style authority, freshness, completeness), and query-document features (BM25 score, field match coverage). Feature engineering is often the highest-leverage work in search relevance.

**Learning-to-rank (LTR)**: Supervised ranking using LambdaMART, RankNet, or LightGBM. Requires human-labeled relevance judgments or implicit feedback (clicks, purchases). Elasticsearch's LTR plugin integrates with Elasticsearch's `function_score` or `rescore` query. Know the evaluation metrics: NDCG (Normalized Discounted Cumulative Gain) and MAP (Mean Average Precision).

**Query understanding**: Before ranking, understand what the user wants. Spell correction (Noisy Channel Model, SymSpell), query expansion (synonyms, related terms), entity extraction (recognize "iPhone 15" as a product, not a bag of words), and intent classification (navigational vs. informational vs. transactional).

## Vector Search and Neural Retrieval

Semantic search has transformed the field — every search engineering interview now touches dense retrieval:

**Dense vector embeddings**: Encode documents and queries as dense vectors using sentence-transformers or proprietary models. Similarity search (cosine similarity, dot product) finds semantically similar documents that don't share exact keywords. Elasticsearch's `dense_vector` field and KNN search.

**Approximate Nearest Neighbor (ANN)**: Exact KNN is O(n) per query — too slow for large corpora. HNSW (Hierarchical Navigable Small World graphs), IVF (Inverted File Index), and FAISS implement ANN with controllable recall/latency tradeoffs. Know HNSW parameters: `m` (graph connectivity) and `ef_construction` (build time/quality tradeoff).

**Hybrid search**: Combining BM25 (keyword recall) with dense retrieval (semantic recall) via Reciprocal Rank Fusion (RRF) or learned combination. Practical wisdom: dense retrieval excels on long-tail queries; BM25 excels on exact-match and technical queries. Hybrid consistently outperforms either alone.

## Interview Preparation

- Build a search system with Elasticsearch: index documents, implement BM25 search, add autocomplete with edge-ngrams, and tune relevance with function_score
- Implement BM25 from scratch in Python to understand the formula deeply
- Study Elasticsearch's query DSL thoroughly — bool queries, nested queries, aggregations
- Read the Elasticsearch documentation on relevance and scoring
- Explore FAISS or Qdrant for vector search — build a semantic search demo

Search engineering is rare and high-impact. Engineers who combine information retrieval fundamentals with distributed systems knowledge and ML for ranking are in high demand at consumer platforms, e-commerce companies, and enterprise software.
