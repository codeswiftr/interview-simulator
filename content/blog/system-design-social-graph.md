---
title: "System Design: Social Graph (Follow/Friend Relationships at Scale)"
description: "Design a social graph for a platform like Twitter or Instagram — storing directed follow relationships, feed generation, mutual friends, graph traversal at scale, and the data models behind Facebook, Twitter, and LinkedIn."
date: "2026-03-20"
category: "System Design"
---

# System Design: Social Graph (Follow/Friend Relationships at Scale)

Social graph design appears in interviews at Twitter, LinkedIn, Meta, and any platform with follow/friend features. The core problem looks simple — store who follows whom — but the scale challenges are substantial: billions of users, real-time feed generation, graph traversal for friend suggestions, and mutual connection queries.

## Requirements and Scale

Clarify before designing:
- **Directed or undirected?** Twitter: directed (follow). Facebook: undirected (friend, requires mutual confirmation). LinkedIn: directed but "connection" implies mutual.
- **Scale:** 1B users, average 300 followers, 10B follower relationships, 100K follow/unfollow operations/second
- **Read pattern:** Mostly reads — show follower count, check if following, generate feed
- **Features:** Follower/following counts, is-following check, follower/following lists, mutual connections, friend-of-friend suggestions

## Core Data Model

For a directed follow graph, the fundamental relationship is `(follower_id, followee_id, timestamp)`. Two access patterns:

- "Who does user A follow?" → scan by `follower_id`
- "Who follows user A?" → scan by `followee_id`

These access patterns suggest a relational table with two indexes:

```sql
CREATE TABLE follows (
    follower_id BIGINT NOT NULL,
    followee_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (follower_id, followee_id),
    INDEX (followee_id, follower_id)  -- Reverse lookup
);
```

For 10B rows, this table is too large for a single PostgreSQL instance. It needs sharding.

## Sharding Strategy

**Shard by follower_id:** All follows originating from one user are on the same shard. "Who does A follow?" is a single-shard query. "Who follows A?" is a scatter-gather across all shards. Optimal for publishing (fan-out-on-write).

**Shard by followee_id:** Opposite tradeoffs. Optimal for aggregating a user's followers.

**Dual write:** Maintain two tables — one sharded by follower_id, one by followee_id. Writes go to both. Reads are single-shard for either access pattern. Doubles storage and write complexity.

Production answer (Twitter's approach): dual write with eventual consistency between the two tables. A brief period where the two are inconsistent is acceptable.

## Follow/Unfollow at Scale

A follow operation must:
1. Insert `(follower_id, followee_id)` into the follows table
2. Update the follower_count of followee
3. Update the following_count of follower
4. If feed generation is push-based: add followee's recent posts to follower's feed

Operations 2 and 3 can be done with atomic counters in Redis (faster) with periodic sync to the database.

Operation 4 (feed fan-out) is expensive for users with millions of followers. This is the celebrity problem.

## Celebrity Problem: Pull vs. Push Feed

**Push (fan-out on write):** When a user posts, pre-compute the feed for each follower. O(n) writes per post where n = follower count. Terrible for celebrities (50M followers × 1 post = 50M writes).

**Pull (fan-out on read):** When a user requests their feed, query the last posts from everyone they follow. O(k) reads per feed load where k = following count. Terrible for heavy followers.

**Hybrid (Twitter's solution):**
- Regular users: push model. Feed is precomputed in Redis.
- Celebrities (>10K followers): pull model. Their posts are not fanned out.
- At feed generation: merge precomputed feed (from push) with real-time posts from followed celebrities (pull).

The threshold for "celebrity" is configurable. The hybrid approach serves the common case (regular user posting to modest follower count) efficiently while handling the outlier case (celebrity with millions of followers).

## Mutual Connection Queries

"Do A and B have mutual friends?" or "What mutual connections do A and B have?"

Naive: load A's follow set, load B's follow set, compute intersection. For users with 10K+ connections, this is expensive.

**Efficient approach:** Use sorted sets for each user's connections (sorted by user_id). Merge-join two sorted sets: O(|A| + |B|). For users with small connection sets, this is fast.

**Bloom filter optimization:** For the binary "do they have any mutual connection" question, store each user's connection set as a Bloom filter. Check B's Bloom filter for each of A's connections. O(|A|) with low false positive rate. False positives require follow-up verification; false negatives don't occur.

**Graph databases:** Neo4j, Amazon Neptune, or a custom adjacency list store can answer multi-hop graph queries ("friends of friends who work at the same company") that are impractical with relational approaches.

## Graph Traversal at Scale: Friend Suggestions

"People you may know" features require BFS/DFS over the social graph to find friends-of-friends.

Challenge: the full social graph of 1B users doesn't fit in memory on one machine. Approaches:

**Distributed BFS:** Shard the graph by user_id. BFS from user A: load A's neighbors from shard(A), load their neighbors from the respective shards. Cross-shard lookups add latency but are manageable for 2-hop BFS.

**Offline precomputation:** Periodically compute friend suggestions in batch (Spark/Hadoop job), store results in a recommendations table. Serve from table rather than computing on-demand. Staleness of a few hours is acceptable for this feature.

## Follower Count at Scale

Counting followers accurately at scale has a surprising complexity. Options:

**Exact count in DB:** `SELECT COUNT(*) FROM follows WHERE followee_id = ?`. Too slow for real-time display — full table scan.

**Denormalized counter:** Maintain a `user_stats(user_id, follower_count)` table. Increment/decrement on follow/unfollow. Cheap to read. Risk: counter drift on failures.

**Redis counter:** Store `follower_count:{user_id}` in Redis. O(1) reads and writes with `INCR`/`DECR`. Periodic backup to database. Fast and reliable.

**Approximate count (HyperLogLog):** For very approximate display ("12M followers" vs. "12,341,897 followers"), Redis's HyperLogLog provides O(1) cardinality estimates using minimal memory. Used when exact counts aren't necessary.
