---
title: "Search Engineering Interview Guide"
description: "Search infrastructure in technical interviews: inverted indexes, ranking algorithms, relevance tuning, query understanding, and how companies like Elasticsearch, Algolia, and Google approach search engineering."
date: "2026-03-19"
category: "Technical Skills"
---

# Search Engineering Interview Guide

Search engineering appears in interviews at companies where search is a core product — Elasticsearch/OpenSearch, Algolia, Pinterest, Etsy, LinkedIn, Amazon — and at any company with a significant search surface. This guide covers the data structures, ranking concepts, and system design knowledge that search engineering interviews test.

## The Inverted Index: Foundation of Everything

The inverted index is the data structure behind virtually every text search system. Instead of mapping documents to terms, it maps terms to the documents containing them:

```
"coffee" → [doc_3, doc_7, doc_12, doc_45]
"shop"   → [doc_3, doc_7, doc_19]
"espresso" → [doc_3, doc_45, doc_67]
```

To find documents containing "coffee shop", you intersect the posting lists for "coffee" and "shop": `[doc_3, doc_7]`.

Interviewers ask candidates to explain why this is efficient and what its limitations are. The efficiency: once built, query time is proportional to result count, not document count. The limitations: updates require re-indexing (adding/removing terms from posting lists), and the index itself can be large.

**Posting list compression**: Production search systems store billions of document IDs. Naive storage is expensive. Interviewers at companies with large search indexes ask about delta encoding (storing differences between sorted IDs rather than IDs themselves) and variable-length encoding.

## Text Analysis: What Happens Before Indexing

Before text is indexed, it passes through an analysis pipeline. Understanding this pipeline explains why "running" and "ran" find the same documents.

**Tokenization**: Split text into terms. "The quick brown fox" → ["the", "quick", "brown", "fox"]. Language-specific tokenizers handle contractions, hyphens, Unicode.

**Normalization**: Lowercase, remove diacritics, expand abbreviations.

**Stop words**: Remove high-frequency words with low discriminative value ("the", "a", "is"). Controversial — "to be or not to be" breaks if you remove stop words.

**Stemming/Lemmatization**: Reduce words to root form. "running" → "run", "better" → "good". Lemmatization uses vocabulary knowledge; stemming uses heuristic rules. Both enable matching inflected forms.

**Synonyms**: Query-time or index-time expansion. "sofa" → also index/search "couch", "settee". Interviewers ask: index-time or query-time synonym expansion, and why each matters (index-time expands storage; query-time adds latency but is easier to update).

## Relevance Ranking

The hardest search problem is not finding documents that match — it's ranking them by relevance. Interviewers at search-focused companies probe ranking deeply.

**TF-IDF**: The classic baseline. Term Frequency (how often the term appears in this document) × Inverse Document Frequency (log of total documents / documents containing the term). A term that appears often in a document but rarely across the corpus is highly specific — high TF-IDF. Common words that appear everywhere have low IDF and pull down TF-IDF.

**BM25**: BM25 (Best Match 25) is the modern replacement for TF-IDF. It adds document length normalization (a term appearing 5 times in a 100-word document is more significant than in a 10,000-word document) and term frequency saturation (the 100th occurrence of a term contributes less than the 10th). BM25 is the default ranking model in Elasticsearch and most production search systems.

**Learning to Rank (LTR)**: For high-stakes search (e-commerce, job listings, content recommendations), pure lexical matching is insufficient. LTR uses machine learning models trained on human-judged relevance labels or implicit signals (clicks, conversions) to re-rank results. Common algorithms: RankNet, LambdaMART, LambdaRank.

## Vector Search and Hybrid Search

Modern search increasingly combines lexical (BM25) with semantic (vector) search. Interviewers at companies building AI-enhanced search probe this.

**Dense retrieval**: Encode documents and queries as dense vectors using transformer models. Semantically similar text has similar vectors. Enables finding "hotel near Times Square" when no document contains "Times Square" — the semantics match even without keyword overlap.

**Approximate nearest neighbor (ANN)**: Finding exact nearest neighbors in high-dimensional vector space is expensive. ANN algorithms (HNSW, IVF) trade recall for speed. Interviewers ask: what recall do you need, and what latency can you tolerate?

**Hybrid search**: Combine BM25 scores and vector similarity scores. Reciprocal Rank Fusion (RRF) is a common technique: instead of merging raw scores (which have different scales), merge rank positions from each system. Candidate appears at rank 3 in BM25 and rank 5 in vector search → combined RRF score combines these ranks.

## System Design: Search Infrastructure

Common system design questions in search engineering interviews:

**Design a type-ahead search system**: Prefix trie or prefix index, low-latency serving (sub-50ms), personalization layer, caching strategy. The key insight: autocomplete latency must be extremely low because it fires on every keystroke.

**Design a product search system for an e-commerce company**: Crawl/index pipeline, faceted search (filter by price, category, brand), relevance ranking that incorporates business signals (margin, inventory), real-time updates for price changes.

**Design a search system that handles 10 billion documents**: Sharding strategy, distributed index, query routing, replication for availability, incremental vs. batch re-indexing.

## What to Study

- **Elasticsearch documentation**: Practical understanding of how a production search system works — mappings, analyzers, query DSL, aggregations
- **Introduction to Information Retrieval** (Manning, Raghavan, Schütze): Free online, the authoritative academic reference
- **Pinecone and Weaviate documentation**: For vector search concepts
- **Algolia engineering blog**: Well-written explanations of production search engineering challenges

Search engineering rewards candidates who have built and debugged real search systems. "Why are these results returning in this order?" is a debugging question that only experience with a real system can prepare you for.
