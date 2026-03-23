---
title: "System Design: Social Media Feed — News Feed Architecture at Scale"
description: "A complete walkthrough of designing a social media news feed system. Covers feed generation strategies (push vs pull), ranking, storage, caching, and handling millions of active users."
date: "2026-03-20"
category: "System Design"
---

# System Design: Social Media Feed — News Feed Architecture at Scale

The social media news feed is one of the canonical system design interview problems. Companies like Facebook, Twitter, Instagram, and LinkedIn all rely on news feed systems to surface relevant content to hundreds of millions of users. Understanding how to design such a system demonstrates competence in distributed systems, storage design, caching, and trade-off analysis.

This guide walks through the key design decisions you need to discuss in an interview — not just the final architecture, but the reasoning behind each choice.

## Defining the Scope

Before diving into architecture, clarify requirements with your interviewer. Good scope-setting questions:

- How many users? (Let's assume 100M DAU)
- What's the read:write ratio? (Typically 80:20 — feeds are read far more than written)
- Is the feed chronological, ranked, or a mix?
- Do we need to support live stories, ads, or just posts?
- What's the acceptable latency for loading a feed? (Target: p99 < 200ms)

For this walkthrough, we'll design a core feed system: users can post content, follow other users, and see a ranked feed of posts from people they follow.

## Core Components

A news feed system needs to handle three distinct workflows:

1. **Write path:** A user creates a post → store it → distribute it to followers' feeds
2. **Read path:** A user opens the app → retrieve and render their personalized feed
3. **Ranking/ML:** Determine which posts from the eligible set are most relevant

## Feed Generation: Push vs Pull

This is the central trade-off in feed system design.

### Pull (Fan-in on Read)

When a user requests their feed, the system queries recent posts from all users they follow and merges the results in real time.

**Pros:**
- Simple write path (just store the post)
- Feed is always up-to-date
- No wasted work for inactive users

**Cons:**
- Read latency increases with follow count (celebrity with 50M followers → user has to query all of them)
- Database hotspots at popular accounts
- Expensive N+1 query pattern

### Push (Fan-out on Write / Precomputed Feed)

When a user creates a post, the system immediately writes it to the feed tables of all their followers.

**Pros:**
- O(1) read — just fetch pre-built feed list
- Very fast reads; predictable latency

**Cons:**
- Expensive write path for accounts with millions of followers (writing to 5M feed rows = huge fanout)
- Storage cost for inactive users (we're writing to their feed even if they never log in)
- Feed may be slightly stale in high-volume situations

### Hybrid Approach (Recommended for Interviews)

Most production systems use a hybrid:
- For normal users (< 10,000 followers): push their posts to followers' precomputed feeds
- For celebrities/high-follower accounts: use pull at read time, merging celebrity posts into the pre-built feed

This limits fanout cost while maintaining fast reads for the vast majority of feed loads.

## Data Model

**Users table:**
```
user_id (PK), username, created_at, follower_count
```

**Posts table:**
```
post_id (PK), user_id (FK), content, media_url, created_at, like_count
```

**Follows table:**
```
follower_id, followee_id, created_at
Index: (followee_id) for fanout; (follower_id) for "who am I following"
```

**Feed table (precomputed, for push model):**
```
user_id, post_id, post_created_at, score
Index: (user_id, score DESC) for efficient feed retrieval
```

The feed table stores references (post IDs) rather than content — the actual post data is fetched separately and cached.

## Storage Layer

**Posts and user data:** A relational database (PostgreSQL, MySQL) works well for the primary data store. Partition posts by `user_id` or `post_id` range to distribute load.

**Feed table:** At scale (100M users × 1,000 feed items = 100B rows), this becomes a challenge for traditional RDBMS. Options:
- **Redis Sorted Sets** — excellent for precomputed feeds; `ZRANGEBYSCORE` gives O(log N) retrieval; naturally handles score-based ranking
- **Cassandra** — wide-column store; partition key = `user_id`, cluster by score descending; high write throughput makes it good for fan-out

For 100M DAU systems, Redis Sorted Sets per user are a common production choice for the "hot" recent feed (keeping last 1,000 posts per user), with fallback to persistent storage for older items.

## Caching Strategy

Caching is critical for feed performance:

- **L1 (application cache):** Cache feed results for 30–60 seconds per user; prevents hammering storage on rapid refreshes
- **L2 (CDN/Redis):** Cache post content and media metadata; posts don't change after creation
- **Celebrity post cache:** Popular posts from high-follower accounts should be aggressively cached since the same post appears in millions of feeds

Cache invalidation is simpler here than in many systems because posts are largely immutable after creation. Edits and deletes require cache eviction.

## Feed Ranking

A purely chronological feed doesn't maximize engagement. A ranking service scores posts using signals like:

- Recency (time decay function)
- Interaction history (do you usually like this person's posts?)
- Post engagement rate (likes, comments in first N minutes)
- Content type affinity (does this user engage more with videos or text?)

The ranking service runs as a separate component: the feed service retrieves N candidate posts (e.g., 200 recent posts) and passes them to the ranking service, which returns the top K (e.g., 20) for display.

At massive scale, ML ranking models run on batched pre-scoring rather than per-request inference to keep latency acceptable.

## Handling the Write Path

When a post is created:

1. Write to Posts table (primary storage)
2. Publish event to message queue (Kafka)
3. Fan-out service consumes the event, looks up followers
4. For normal users: write post_id to each follower's feed (Redis Sorted Set or Cassandra)
5. For celebrities: skip fan-out; handle at read time

The message queue decouples the write from the fan-out, preventing the post creation from blocking on potentially millions of feed writes.

## Scaling Considerations

- **Sharding:** Shard users and posts by user_id; consistent hashing for the feed cache
- **Read replicas:** Heavy read traffic → multiple replicas for the Posts table
- **Rate limiting:** Prevent abuse; limit posts per user per hour
- **CDN:** Media content (images, videos) served from CDN; only references stored in the database

## Common Follow-up Questions

**Q: How do you handle real-time feed updates?**
Long-polling or WebSocket connections notify clients of new posts. The client can show "2 new posts — tap to refresh" rather than auto-inserting, which disrupts reading context.

**Q: How do you handle deletions?**
Mark as deleted in the Posts table, then asynchronously remove from feed tables. CDN cache TTL means deleted content may briefly remain accessible — acceptable for most use cases.

**Q: How do you prevent a thundering herd when a celebrity posts?**
Stagger fan-out using a delayed queue. Add jitter to cache TTLs. Pre-warm caches for accounts with known posting schedules (sports teams during game time, etc.).

## Interview Summary

The news feed design demonstrates your grasp of the push/pull fan-out trade-off, storage selection for different access patterns, caching hierarchies, and asynchronous processing. Be prepared to defend your choices and discuss what you'd change as scale increases. The best answers show you understand the trade-offs, not just the happy-path architecture.

## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Notification System](/blog/system-design-notification-system)
- [Twitter Trending Topics System Design](/blog/twitter-trending-topics-system-design)
- [LinkedIn Feed Ranking System Design](/blog/linkedin-feed-ranking-system-design)
- [System Design: Real-Time Chat](/blog/system-design-real-time-chat)
