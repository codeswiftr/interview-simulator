---
title: "System Design: Building a Search Engine (From Web Crawling to Ranked Results)"
description: "System design interview guide for building a search engine — web crawling, inverted index, ranking signals, query processing, and how to answer search system design questions."
date: "2026-03-20"
category: "System Design"
---

# System Design: Building a Search Engine (From Web Crawling to Ranked Results)

Designing a search engine is one of the most intellectually rich system design questions you'll encounter. It spans distributed systems, data structures, information retrieval theory, and machine learning — all in a single question. This guide gives you a structured approach to answering it, whether the scope is a full web search engine or a product search feature.

## Clarify the Scope First

A search engine question can range enormously in scope. Before designing, ask:

- Are we indexing the entire web, a specific domain (e.g., e-commerce products, internal documents), or a controlled corpus?
- What query types must we support — keyword, phrase matching, boolean operators, semantic/natural language?
- Is freshness critical (news search) or acceptable at hours/days delay?
- What query volume (QPS) are we targeting?

For a senior interview, assume: web-scale (50 billion pages), keyword + phrase queries, latency target of 200ms p99, 100K QPS.

## Web Crawler Design

The crawler discovers and downloads web content. It has several critical properties:

**Politeness**: Don't hammer a single domain with requests. Use per-domain rate limiting and respect `robots.txt` rules. Maintain a URL frontier (priority queue) and distribute URLs across crawler workers, ensuring workers handling the same domain are throttled.

**Frontier management**: BFS from seed URLs sounds simple, but in practice you need a priority queue that weights pages by estimated importance (PageRank score, link freshness, domain authority). High-priority pages get re-crawled more frequently.

**Deduplication**: The web has massive content duplication. Use URL normalization (canonicalization) to detect the same page at multiple URLs. For near-duplicate detection, compute a document fingerprint (SimHash or MinHash) and skip pages that are too similar to already-indexed content.

**Storage**: Crawler workers download raw HTML to a distributed object store (S3-equivalent). A separate document processing pipeline reads from there.

## Document Processing Pipeline

Raw HTML is not indexable. The pipeline transforms it:

1. **Parse and extract** text, title, meta description, anchor text, outgoing links
2. **Language detection** — route to language-specific analyzers
3. **Tokenization** — split text into tokens (words)
4. **Normalization** — lowercase, remove punctuation
5. **Stop word removal** — filter "the", "and", "is"
6. **Stemming or lemmatization** — reduce "running", "ran" to "run"
7. **Emit (token, doc_id, position, field) tuples** to the indexing pipeline

This pipeline is a classic MapReduce or streaming job. Use Kafka between crawling and processing to decouple throughput.

## Inverted Index

The inverted index maps each token to a list of documents containing it — a **posting list**.

```
token: "distributed" → [(doc_1, tf=3, positions=[12,45,67]), (doc_5, tf=1, positions=[3]), ...]
```

Each posting stores:
- **doc_id**: which document
- **term frequency (tf)**: how often the term appears
- **positions**: for phrase matching

The index is built offline via MapReduce: map phase emits (token, posting), reduce phase merges and sorts postings by doc_id.

At query time, you look up each query token and **intersect** posting lists to find documents matching all terms (AND), or **union** for OR queries. Intersection is efficient because posting lists are sorted — two-pointer merge in O(n+m).

## TF-IDF and BM25 Ranking

Raw term frequency isn't enough — common words appear in nearly every document and shouldn't rank highly.

**TF-IDF** weights a term by how frequently it appears in a document (TF) divided by how common it is across all documents (IDF — inverse document frequency). Documents with rare, relevant terms score higher.

**BM25** (Best Match 25) is the modern standard, used by Elasticsearch and many search engines as a baseline. It addresses TF saturation (adding more occurrences of a term has diminishing returns) and normalizes for document length (longer documents shouldn't win simply by having more words).

For the interview, you don't need to recite the BM25 formula — knowing it exists, what it corrects for, and that it's the standard starting point is sufficient.

## Query Processing

When a query arrives:

1. **Tokenize and normalize** using the same pipeline as indexing
2. **Lookup**: retrieve posting lists for each token from the index
3. **Intersect/union**: produce candidate document set
4. **Score**: compute BM25 or composite ranking score for each candidate
5. **Top-K selection**: return top 10 results (use a min-heap for efficiency)
6. **Snippet generation**: extract the most relevant passage from each result

Query latency is dominated by posting list retrieval and scoring. Keep hot posting lists (for common queries) in memory or a fast cache (Redis). Shard the index across many machines to parallelize lookup.

## Ranking Signals Beyond Text Relevance

Production search engines use hundreds of signals layered on top of text matching:

- **PageRank / authority**: how many high-quality pages link to this page
- **Anchor text**: the text of links pointing at a page is a strong relevance signal
- **Freshness**: newer content ranks higher for time-sensitive queries
- **Click-through rate (CTR)**: pages that users click and don't immediately bounce from rank higher
- **User signals**: dwell time, return-to-SERP rate
- **Spam signals**: excessive keyword stuffing, thin content, link farms

These signals are combined using a learning-to-rank model (LambdaMART, neural rankers) that takes a query-document feature vector and predicts relevance.

For the interview, mentioning 2–3 categories of signals and noting they're combined via a learned ranking model demonstrates strong practical knowledge.

## Sharding the Index

A 50-billion-page index doesn't fit on one machine. Two sharding strategies:

**Document sharding (horizontal)**: each shard holds all tokens for a subset of documents. A query goes to all shards in parallel; results are merged and re-ranked. This is the standard approach — used by Google and most large search engines.

**Term sharding (vertical)**: each shard holds a subset of tokens. A query goes only to shards containing its terms. Less fan-out per query, but some queries touch many shards and merging is complex.

Document sharding is simpler and more fault-tolerant. Replicate each shard 3x for availability.

## Common Follow-Up Questions

**How do you handle freshness?** Maintain a separate real-time index for new/updated documents that is merged at query time with the main index. News search uses this pattern.

**How do you handle typos?** Query expansion with edit-distance spell correction. Pre-compute a phonetic or character n-gram index for fuzzy matching.

**How do you scale query serving?** Horizontal scaling of query servers behind a load balancer. Cache popular query results at the query layer with a short TTL.

**How do you prevent spam/SEO manipulation?** Regularly retrain ranking models on feedback signals. Manual quality rater programs. Graph-based spam detection to identify link farms.

Structuring your answer around these five layers — crawling, processing, indexing, query processing, ranking — gives you a complete, credible architecture that covers the full pipeline.
