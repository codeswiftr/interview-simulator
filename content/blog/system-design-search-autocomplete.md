---
title: "System Design: Search Autocomplete / Typeahead"
description: "Design a search autocomplete system for 1B users — trie vs inverted index, ranking suggestions by frequency, real-time updates, personalization, distributed trie design, and caching strategies."
date: "2026-03-20"
category: "System Design"
---

# System Design: Search Autocomplete / Typeahead

Search autocomplete is a common system design interview question that tests your knowledge of tries, caching, and distributed systems. Google's search bar, Amazon's product search, and Spotify's search all use autocomplete. Here's how to design one for massive scale.

## Requirements

Functional: as user types, return top 5 suggestions in real-time, suggestions ranked by popularity/relevance, support for billions of queries/day, latency <100ms (ideally <50ms), suggestions update based on trending terms.

Non-functional: 10M concurrent users, 10B search queries/day, suggestions must be fresh (trending terms appear within 30-60 minutes).

## Core Data Structure: Trie

A trie (prefix tree) is the natural data structure for prefix matching. Each node represents a character; paths from root to node spell out prefixes. To find all completions for "sea": traverse to the "sea" node, collect all words in the subtree.

**Problem with naive trie at scale:** A trie for all English words is manageable. A trie for 10B search queries with frequency data across multiple languages is not — it won't fit in memory on a single machine.

**Optimization: Top-K at each node.** Instead of storing all completions, store the top 5 most frequent completions at each node. When a user types "sea", the "sea" node already has the top 5 suggestions — no subtree traversal needed. This trades accuracy (might miss a freshly popular query) for speed.

## Architecture

**Two-tier architecture:**

**Aggregation tier (batch/near-realtime):** Collects search queries, computes frequencies, updates the trie periodically. Frequency computation runs as a MapReduce or Spark job over the query log. Trie updates run every 30-60 minutes or near-realtime for trending terms.

**Serving tier:** Read-only trie replicas that handle autocomplete requests. Queries come in, trie lookup returns top-K, response sent. No writes — entirely read-optimized.

## Query Flow

1. User types "se" — frontend sends request after short debounce (100-200ms) to avoid firing on every keystroke
2. API gateway routes to autocomplete service
3. Service checks Redis cache for "se" prefix
4. Cache hit: return cached suggestions (most prefixes are cached)
5. Cache miss: query trie, store result in Redis with TTL, return
6. Frontend displays suggestions

## Caching Strategy

The key insight: popular prefixes are queried millions of times. The top-100 prefixes ("the", "a", "how to", "what is") account for a huge fraction of all queries.

Cache suggestions for each prefix in Redis. TTL: 30-60 minutes. With a 1M prefix cache and 50 bytes per suggestion list, this fits easily in Redis.

Cache warming: after trie update, proactively populate cache for top N prefixes. Cold starts are unacceptable for "how to" — it would cause a thundering herd on trie servers.

## Distributed Trie

For global scale, a single trie server won't work. Partition by prefix: "a*" → shard 1, "b*" → shard 2, etc. A routing layer maps prefix to the correct shard.

Problem: uneven prefix distribution ("s" prefixes are far more common than "x" prefixes). Solution: shard by observed traffic patterns rather than alphabetically. Use consistent hashing with each shard owning a range of the prefix hash space.

**Replication:** Each shard has multiple replicas. Writes (trie updates) go to a primary; reads distributed across replicas. Updates propagate from primary to replicas asynchronously — slight staleness acceptable.

## Ranking and Personalization

**Global ranking:** Frequency-based. The most-searched completions appear first. Simple and effective for generic queries.

**Personalization:** User's own search history and click behavior can boost relevant suggestions. A "sea" might suggest "Seattle weather" for a Seattle resident and "sea turtle" for a marine biology researcher. Requires user profile lookup at query time — adds latency.

**Trending queries:** Queries that spike suddenly (a news event, celebrity news, product launch) should surface quickly. A separate near-realtime trending system computes query velocity over the last 30 minutes and injects trending terms into autocomplete results.

## Freshness vs Consistency

Trie updates create a staleness problem. Between batch updates (every 30-60 minutes), new trending queries don't appear in autocomplete.

Solutions:
1. **More frequent updates:** Update trie every 5 minutes. Higher compute cost.
2. **Real-time supplement:** In addition to the batch trie, run a real-time stream processing layer (Kafka + Flink) that tracks query frequency in the last 15 minutes. Merge real-time trending terms into trie-based results at query time.
3. **Client-side trending:** Push trending terms to clients periodically, supplement on-device.

Google uses option 2: batch trie for stable completions + real-time layer for trending.

## Filtering and Safety

Autocomplete surfaces what people search for — which includes offensive, harmful, and legally sensitive content. You need filtering:

- **Blocklist:** Hard filter for illegal content, hate speech, personal information
- **Safe search:** User-controlled; filters adult content
- **Regional filtering:** Some queries acceptable globally are illegal in specific jurisdictions
- **Real-time monitoring:** Flag unusual query patterns (coordinated search campaigns trying to surface specific suggestions)

Filtering runs as a post-processing step on suggestions before returning to the client.

## Interview Walkthrough

Present the design in this order: trie fundamentals → top-K at each node optimization → caching layer → batch trie update pipeline → real-time trending supplement → personalization (if asked). Discuss filtering at the end as a reliability/safety concern.

The common follow-up: "How do you handle updates to the trie?" Answer: batch MapReduce job rebuilds trie from query log snapshots; deploy to serving tier atomically by swapping pointers (blue-green); near-realtime layer handles recency gaps.

