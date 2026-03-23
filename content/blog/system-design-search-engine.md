---
title: "System Design: Search Engine — Web Crawling, Indexing, and Ranking at Scale"
description: "Design a web search engine for interviews — web crawlers, inverted index, ranking algorithms, query processing, and scaling to billions of documents."
date: "2026-03-20"
category: "System Design"
---

# System Design: Search Engine — Web Crawling, Indexing, and Ranking at Scale

The search engine design question tests understanding of large-scale data processing, distributed indexing, and ranking systems. It's asked at Google, Microsoft Bing, Elastic, and companies with internal search infrastructure. The key is breaking the system into well-defined components and discussing the tradeoffs at each layer.

## System Components

A search engine has four major subsystems: crawling, indexing, ranking, and query serving. Each is a large distributed system in itself.

## Web Crawler

The crawler discovers and downloads web pages. Architecture:
- **Frontier:** A priority queue of URLs to crawl. URLs are prioritized by importance (PageRank score, freshness requirement). Implementation: distributed queue (Kafka) with multiple priority tiers.
- **Fetcher workers:** Download pages, respect robots.txt and rate limits (politeness delay per domain). Distributed across regions for global coverage.
- **Content deduplication:** Use SimHash or MinHash to detect near-duplicate pages. Store document fingerprints in a distributed hash map; skip crawling near-duplicates.
- **URL normalization:** Canonicalize URLs (remove tracking parameters, normalize case) before adding to frontier.

Scale: Google crawls tens of billions of pages. At 1 billion pages with 1KB average: 1TB of raw content per billion pages.

## Document Processing and Indexing

**Inverted Index:** The core data structure for text search. Maps each term to a posting list: sorted list of (docId, term frequency, positions) for documents containing that term.

```
"python" → [(doc_1, freq=5, positions=[10,25,42]), 
             (doc_4, freq=2, positions=[5,18]), ...]
```

Building the index:
1. Parse HTML, extract text and metadata
2. Tokenize text (split on whitespace/punctuation)
3. Normalize tokens (lowercase, stemming/lemmatization)
4. Build term → posting list mappings
5. Merge and compress posting lists

**Distributed indexing (MapReduce pattern):**
- Map: emit (term, docId, position) for each token in each document
- Reduce: collect all (docId, position) for each term → posting list

**Index sharding:** With billions of documents, the index is sharded. Two strategies: document sharding (each shard has a complete index for a subset of documents) or term sharding (each shard owns a subset of terms). Document sharding is more common — each shard can answer a query independently, results are merged.

## Query Processing

When a user queries "machine learning python tutorial":

1. **Query parsing:** Tokenize, normalize, apply stemming
2. **Query expansion:** Synonyms, spelling correction (did you mean?)
3. **Index lookup:** Retrieve posting lists for each term
4. **Intersection/union:** Find documents containing all query terms (AND) or scoring based on term presence
5. **Ranking:** Score and sort candidates
6. **Result serving:** Top-K results with snippets and metadata

**Performance:** Posting list retrieval is the bottleneck. Compression (variable-length encoding, delta encoding for sorted docIDs) reduces disk I/O. Frequently accessed posting lists (common terms) are cached in memory.

## Ranking

Ranking is the hardest problem in search. Modern search uses multi-stage ranking:

**TF-IDF (classical):** Term Frequency × Inverse Document Frequency. A term is relevant to a document if it appears frequently in that document (TF) but infrequently across all documents (IDF). High TF-IDF = the term is distinctive to this document.

**BM25:** Improved TF-IDF that handles document length normalization. Standard baseline for text relevance.

**PageRank:** Measures document authority based on link graph. Pages linked to by authoritative pages are themselves authoritative. Computed iteratively over the web graph.

**Learning to Rank:** ML models trained on click data to predict relevance. Features: TF-IDF score, PageRank, query-document feature overlap, user engagement signals (CTR, dwell time). GBDT (gradient boosted decision trees) or neural models.

**Two-stage ranking:** First pass uses BM25 to retrieve 1000 candidates (fast, approximate). Second pass uses expensive ML model to re-rank top 100 (slow but accurate). This reduces the computation of the expensive model by 10-100x.

## Serving and Caching

At Google scale, query volume is billions per day. Performance requirements: P99 < 200ms.

**Result cache:** Cache top-K results for popular queries (news, trending topics change, but "buy shoes" results are stable). Cache at the serving layer with short TTLs for trending queries.

**Partial results caching:** Cache posting lists for common query terms in memory (Redis cluster). Reduces index lookup time.

**Geo-distributed serving:** Queries are routed to the nearest data center. Each data center has a full copy of the index (or a shard) for local serving without cross-continent latency.

## Freshness

News and social content must be indexed within seconds. "Freshness crawlers" prioritize high-update-frequency domains. Dedicated real-time indexing pipeline (Kafka → streaming indexer → serve layer) for time-sensitive content.

This covers the core architecture. In an interview, you'll likely be asked to go deep on one component — often indexing or ranking — and discuss the specific data structures and tradeoffs in detail.

## Related Articles

- [Airbnb Search Ranking System Design](/blog/airbnb-search-ranking-system-design)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [System Design: Recommendation Engine](/blog/system-design-recommendation-engine)
- [System Design Interview Framework](/blog/interview-system-design-framework)
