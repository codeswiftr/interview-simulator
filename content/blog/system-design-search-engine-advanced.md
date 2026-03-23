---
title: "System Design: Search Engine — Building Google-Scale Search Infrastructure"
description: "How to design a web search engine in system design interviews — web crawling, indexing, ranking algorithms (PageRank, TF-IDF, BERT), query serving, and scaling to billions of web pages."
date: "2026-03-20"
category: "System Design"
---

# System Design: Search Engine — Building Google-Scale Search Infrastructure

Search engine design is a pinnacle system design question — it touches crawling, distributed storage, ranking algorithms, query serving, and real-time indexing all at extraordinary scale. While full Google-scale search is an impractical target for most interview designs, understanding the architecture deeply is expected for senior and staff roles at search companies and any company with significant search functionality.

## Requirements

- **Index**: 50 billion web pages; add 1 billion new pages per month
- **Query volume**: 10 billion queries per day (~115K queries/second)
- **Latency**: Results returned in <200ms p95
- **Freshness**: Top-ranked pages indexed within 24 hours of change
- **Result quality**: Relevant, spam-resistant, diverse results

## Web Crawling Architecture

The crawler discovers and fetches web pages. At Google scale this is itself a massive distributed system.

**URL Frontier**: A priority queue of URLs to crawl. Priority = crawl importance (PageRank-based), freshness (how recently was it last crawled), and politeness (don't hammer a single domain).

**Crawler nodes**: Stateless fetching workers. Pick a URL from the frontier, fetch the page (respecting robots.txt), parse HTML, extract new URLs, store the fetched document.

**politeness and rate limiting**: `robots.txt` specifies crawl rules per domain. Beyond that, limit crawl rate to prevent overloading any single server. The URL Frontier's domain-bucketed queue enforces this — only one concurrent request per domain at a time.

**Duplicate detection**: Many pages have near-identical content (mobile vs desktop versions, URL parameter variations). Use SimHash to fingerprint document content — pages with Hamming distance < 3 are near-duplicates. Store SimHash fingerprints in a distributed hash table; skip fetching near-duplicates.

**Distributed crawl coordination**: Assign URL responsibility by domain hash. Each crawler node owns a subset of domains, preventing redundant crawl work.

## Indexing Pipeline

Raw HTML → processed, indexed document through a pipeline:

1. **HTML parsing**: Extract clean text, title, headings, anchor text
2. **Text analysis**: Tokenize, lowercase, remove stop words, stem/lemmatize
3. **Term extraction**: Build TF (term frequency) per document
4. **Link extraction**: Parse all `<a href>` links, add to URL frontier

**Inverted index**: The core data structure. Maps each term to a list of (document_id, term_frequency, field) tuples sorted by document_id. To answer "which documents contain 'machine learning'?", look up the posting lists for both terms and intersect them.

**Index storage**: At 50B pages, the inverted index is petabyte-scale. Shard by term hash across hundreds of index servers. Each shard holds a subset of terms and their posting lists. Replicate shards for availability.

**Index updates**: Batch rebuilds are prohibitively slow. Use a two-tier index: a large main index (refreshed daily/weekly) and a small delta index (updated in near-real-time). Queries merge results from both.

## Ranking Algorithm

Retrieving matching documents is easy. Ranking them relevantly is the hard problem.

**Classic ranking signals**:
- **TF-IDF**: Term frequency × inverse document frequency. High score for terms that appear often in this document but rarely in all documents. The baseline relevance signal.
- **PageRank**: Measures link authority. A page linked to by many high-authority pages has high PageRank. Computed iteratively across the entire web graph.
- **Anchor text**: The text of links pointing to a page. "Click here for machine learning tutorial" → strong signal that the target page is about ML.
- **Freshness**: Recent pages score higher for news queries.
- **User signals**: Click-through rate, dwell time, bounce rate — signals from actual user behavior.

**Modern ML ranking (BERT/LLM-based)**: Two-stage retrieval. First stage: retrieve 1,000 candidate documents using fast BM25 or vector similarity (dense retrieval). Second stage: re-rank with a BERT-based cross-encoder that scores each document against the full query. The cross-encoder is too slow for full index retrieval but accurate enough for re-ranking a short list.

**Learning to Rank**: Train a gradient boosted model (LambdaMART) or neural network on human-labeled relevance data. Features include TF-IDF, PageRank, page freshness, user engagement signals, and query-document semantic similarity.

## Query Serving Architecture

A search query must return results in <200ms from an index of billions of documents.

**Query processing**:
1. Parse query (handle operators: AND, OR, NOT, phrase matching)
2. Expand query (spell correction, synonym expansion)
3. Retrieve posting lists from index shards (fan-out to all shards, merge results)
4. Score and rank top documents
5. Fetch document metadata (title, snippet) for result display
6. Return to user

**Fan-out to index shards**: A query goes to all index shards in parallel. Each shard returns its top K (e.g., 50) results. A centralized merger merges these sorted lists and returns the global top K.

**Result snippet generation**: Extracting the relevant excerpt of a document for display. Cache snippets — they're expensive to generate and reused across many queries.

**Caching**: Query result cache (Redis) for popular queries. Cache hit rate for top 10K queries might cover 20-30% of query volume. Cache with short TTL (minutes-hours) to reflect index freshness.

## Anti-Spam and Quality

Search is heavily gamed. Common spam techniques: keyword stuffing, link farms, cloaking (showing different content to crawlers vs users), scraped content.

Counter-measures: spam classifiers trained on known spam patterns, PageRank filtering (link farms have abnormal link graph structure), content quality signals (thin content, low engagement), and manual review pipelines.

**SafeSearch**: Explicit content filtering via image classifiers and text classifiers applied at indexing time. Safe/unsafe flag stored per document; queries filter by user's SafeSearch setting.

## Scaling Numbers

- **Index size**: 50B pages × 5KB average indexed size = 250TB (before replication)
- **Query load**: 115K QPS → need ~10,000 index server nodes to serve this with headroom
- **Crawl rate**: 1B new pages/month = ~400 pages/second — requires ~1,000 crawler nodes

The fundamental insight interviewers probe: no single machine can hold the index. The entire design is about partitioning index data across many machines while maintaining fast query response. That's the core architectural challenge.
