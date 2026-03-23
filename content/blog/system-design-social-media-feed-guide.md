---
title: "System Design: Social Media Feed (Twitter/Instagram Timeline Architecture)"
description: "How to design a social media news feed in system design interviews — fanout on write vs read, follower graphs, ranking/personalization, hot users, and storage."
date: "2026-03-20"
category: "System Design"
---

# System Design: Social Media Feed (Twitter/Instagram Timeline Architecture)

The social media feed is one of the most commonly asked system design questions, and for good reason: it surfaces real architectural tradeoffs around consistency, latency, storage, and the infamous "celebrity problem." Understanding how to reason through feed design — not just recite a memorized architecture — demonstrates the kind of distributed systems thinking that senior engineering roles demand.

## Framing the Problem

Before drawing any boxes, establish the scale and requirements. A good interviewer expects you to ask:

- How many daily active users? (assume 500M for this discussion)
- What's the average number of follows per user? (assume 500)
- What's the read/write ratio? (feeds are heavily read-dominant — typically 100:1 or higher)
- Do we need real-time updates or is eventual consistency acceptable?
- Are we ranking feeds chronologically or by relevance?

These answers drive everything. A chronological feed with 1M users is a fundamentally different problem than a ranked feed with 500M users.

## The Core Tradeoff: Fanout on Write vs. Fanout on Read

This is the heart of the feed design question, and you should address it explicitly.

**Fanout on write (push model):** When a user posts, the system immediately distributes that post to all followers' pre-computed feed caches. A post by a user with 1,000 followers triggers 1,000 writes. Reads are fast — just fetch the pre-computed feed from cache. The problem: a celebrity with 50 million followers creates 50 million writes on a single post. Twitter's early architecture used this model and famously struggled with celebrity tweets causing write amplification storms.

**Fanout on read (pull model):** No pre-computation. When a user requests their feed, the system fetches recent posts from everyone they follow and assembles the feed on-demand. Reads become expensive — potentially querying hundreds of users' post stores per feed request. Works well for celebrities (no write amplification) but degrades at scale for users with many follows.

**Hybrid approach (what most production systems use):** Fanout on write for regular users; fanout on read for celebrities (users above a follower threshold, say 1M followers). When a user requests their feed, the system merges their pre-computed feed cache with recent posts from celebrity accounts they follow. This is Twitter's documented production approach and the answer interviewers expect when they ask follow-up questions.

## Data Model and Storage

The core entities:
- **Users**: user_id, metadata
- **Posts**: post_id, user_id, content, timestamp, media_urls
- **Follows**: (follower_id, followee_id, created_at) — a graph relationship

**Post storage**: A write-optimized store (Cassandra is the canonical answer, modeled by Twitter's experience) with a partition key of user_id and clustering key of post_id descending. This enables efficient "get last N posts for user X" queries.

**Feed cache**: Redis sorted sets are the standard choice. Each user has a sorted set keyed by user_id, where members are post_ids and scores are timestamps. Feed assembly means ZREVRANGE to get the top N post_ids, then a bulk fetch for post content.

**Graph storage**: The follower/followee relationship graph. At scale, this is often stored in a purpose-built graph database or a distributed adjacency list (Cassandra or DynamoDB). For feed fanout, you need efficient "get all followers of user X" — the write-time fanout query.

## Ranking and Personalization

For ranked feeds (Instagram, Facebook — not purely chronological), the system adds a ranking layer:

1. Candidate generation: retrieve N candidate posts from the user's social graph (using the fanout mechanisms above)
2. Scoring: apply ML models that score each post on predicted engagement, recency, relationship strength, and content quality
3. Re-ranking: apply business rules (diversity, content safety, ads injection)
4. Serving: return the top K ranked posts

The ranking model itself is usually a two-tower neural network or gradient-boosted trees trained on engagement signals. In an interview, you don't need to describe the ML architecture in detail — acknowledging the need for a ranking service and its inputs/outputs is sufficient.

## Handling Hot Users and Edge Cases

Interviewers often probe with edge cases:

- **Celebrity posts**: handled by the hybrid fanout model described above
- **Deleted posts**: the feed cache may contain post_ids for deleted posts; handle with a deletion tombstone and filter on read
- **Private accounts**: check follow relationship at read time; don't include private posts in fanout to non-followers
- **Feed staleness**: pre-computed feeds should have a TTL; users who haven't opened the app in weeks get a fresh feed on next open

## Rough Scale Estimates

This is important to show in interviews:
- 500M DAU × 2 feed reads/day = 1B feed requests/day ≈ 12,000 requests/second
- At 20ms p99 target, you need feed cache hit rates above 99%
- Each feed entry in Redis: ~100 bytes; 500 posts per user cache = 50KB; 500M users = 25TB of feed cache

25TB of Redis at this scale requires a large cluster — this is where you'd mention Redis Cluster, consistent hashing for shard assignment, and replica sets for read scaling.

## What Makes a Strong Answer

The strongest answers: frame the tradeoffs explicitly, choose an architecture and justify it, address the celebrity problem specifically (it's almost always probed), and demonstrate awareness of the operational complexity (cache invalidation, write amplification, storage costs). Candidates who have a real opinion about the design — not just a list of components — consistently score higher in these interviews.
