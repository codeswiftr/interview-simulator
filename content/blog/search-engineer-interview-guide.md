---
title: "Search Engineer Interview Guide"
description: "Technical interview preparation for search engineering roles: information retrieval fundamentals, Elasticsearch internals, relevance ranking (BM25, learning to rank), query understanding, and what companies like Elastic, Algolia, Spotify, LinkedIn, and search-heavy products expect."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Search Engineer Interview Guide

Search engineering combines information retrieval theory, distributed systems, and product intuition. Almost every significant consumer or enterprise product has a search feature, and the quality of that search experience directly affects business metrics — conversion rates for e-commerce, content discovery for media platforms, productivity for developer tools. Companies build dedicated search teams when search quality becomes a product differentiator. The roles range from backend engineers configuring Elasticsearch for a product, to researchers developing novel ranking algorithms, to infrastructure engineers building search systems at Google or Bing scale.

## Information Retrieval Fundamentals

**Inverted index**: The core data structure underlying all text search. An inverted index maps terms to the documents containing them (with position and frequency information). Building a search index means tokenizing documents, normalizing terms, and building this term → document mapping. Queries look up terms in the index and merge the document lists. Understanding why full-text SQL `LIKE '%search%'` is slow (full table scan, no index) versus inverted index lookup (O(1) term lookup + merge) is foundational.

**TF-IDF (Term Frequency-Inverse Document Frequency)**: The classic relevance scoring function. TF (term frequency): how often does the search term appear in this document? More occurrences → higher relevance. IDF (inverse document frequency): how rare is this term across all documents? Common terms ("the", "and") have low IDF; rare, specific terms have high IDF. TF-IDF = TF × IDF. Documents matching rare terms score higher than documents matching common terms.

**BM25 (Best Match 25)**: The industry standard relevance algorithm, improving on TF-IDF with document length normalization (shorter documents aren't penalized relative to longer ones) and term frequency saturation (diminishing returns for additional term occurrences — the 100th occurrence of "python" contributes less than the 1st). Elasticsearch defaults to BM25. Understanding the k1 and b parameters and how to tune them is expected.

**Recall vs. Precision**: Recall = what fraction of relevant documents were returned. Precision = what fraction of returned documents are relevant. The tension: improving recall (returning more results) often reduces precision (more irrelevant results). Evaluation metrics: MRR (Mean Reciprocal Rank — where did the first relevant result appear?), NDCG (Normalized Discounted Cumulative Gain — accounts for graded relevance and position), precision@k.

## Elasticsearch Architecture

**Inverted index and Lucene**: Elasticsearch is built on Apache Lucene. A Lucene index consists of immutable segments (sorted lists of term → posting entries). Writes create new small segments; periodic merges combine segments. Immutability enables lock-free reads. Deletions are soft (marked in a bitset); compacted on merge.

**Sharding and replication**: An Elasticsearch index is divided into shards (each shard is a Lucene index). Primary shards handle writes; replica shards serve reads and provide failover. Choosing shard count at index creation is important — you can't change it later (requires reindex). Rule of thumb: shards of 10–50GB; avoid too many shards (overhead per shard for JVM heap).

**Relevance tuning**: Boosting fields (title match more important than body match), function score (boost by recency, popularity, or any numeric field), query-time boosting vs. index-time boosting. Analyzers (how text is tokenized and normalized): standard analyzer, language analyzers (English stemming), custom analyzers for specific domains.

**Near real-time search**: Elasticsearch refreshes (makes new documents visible) every 1 second by default. This is NOT a write confirmation — documents may be in memory before refresh. For durability, Elasticsearch uses a translog (write-ahead log) flushed periodically. Understanding the distinction between refresh (visibility), flush (durability), and merge (optimization) is expected.

## Ranking and Relevance

**Learning to Rank (LTR)**: Using machine learning to rank search results rather than purely algorithmic scoring. Three approaches: pointwise (predict relevance score per document), pairwise (predict which of two documents is more relevant), listwise (directly optimize ranking metrics like NDCG). Feature engineering for LTR: query-document features (BM25 score, field match ratios), document features (click history, freshness, authority score), query features (query length, query clarity).

**Query understanding**: Classifying user intent (navigational — user wants a specific page; informational — user wants to learn something; transactional — user wants to do something). Spell correction and query normalization. Query expansion (synonyms, related terms). Entity recognition (identifying that "Apple" is the company, not the fruit, based on query context).

**Semantic search**: Traditional search matches keywords; semantic search matches meaning. Dense retrieval: encode queries and documents as dense vectors (using BERT, Sentence Transformers); retrieve by vector similarity (approximate nearest neighbor with HNSW or FAISS). Hybrid search: combine BM25 (good for exact keyword matches, rare terms) with dense retrieval (good for semantic similarity, paraphrase matching). Elasticsearch introduced sparse and dense vector search; Pinecone and Weaviate are purpose-built vector databases.

**Personalization**: Incorporating user history to re-rank results. Collaborative filtering signals (users who clicked X also clicked Y), user intent signals (time of day, recent queries), explicit preferences. The cold start problem: new users have no history.

## Interview Patterns

**Design a search system for a given product** (e-commerce, job listings, code search). Tests: index design (what fields, which analyzers), ranking approach (relevance signals specific to the domain), query understanding, scalability considerations.

**Why is BM25 better than TF-IDF?** Expected: document length normalization, term frequency saturation, and the ability to tune these with parameters.

**How would you evaluate search quality?** Expected: offline metrics (NDCG using rated query-document pairs), online metrics (CTR, dwell time, zero-result rate, time to successful click).

**Explain the Elasticsearch shard vs. replica model.** Expected: shards for horizontal scaling, replicas for read scaling and failover, immutable Lucene segments, the merge process.

## Who Hires Search Engineers

**Search vendors**: Elastic (Elasticsearch, Kibana), Algolia (search-as-a-service), Coveo, Swiftype, Constructor.io (e-commerce search).

**Major search products**: Google, Microsoft Bing, DuckDuckGo — highly specialized, competitive, PhDs common in research roles.

**Large tech with significant search surface area**: LinkedIn (people search, job search), Spotify (music and podcast discovery), Pinterest (visual search), Airbnb (listing search), Booking.com.

**E-commerce**: Amazon (enormous search investment), Shopify (storefront search), Wayfair. Search quality directly impacts conversion rates.

Search engineering is a specialty where deep knowledge of information retrieval theory, Elasticsearch internals, and product intuition combine in ways that are difficult to fake — engineers who have worked on real ranking problems stand out clearly.
