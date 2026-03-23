---
title: "Designing Instagram Stories Architecture"
description: "A system design breakdown of Instagram Stories—ephemeral media storage, real-time view counts, story ordering, and how Meta handles 500M daily active story users."
date: "2026-03-21"
category: "System Design"
---

# Designing Instagram Stories Architecture

Instagram Stories has 500 million daily active users. Stories are ephemeral (24-hour TTL), ordered by engagement, and involve real-time view tracking. This is a nuanced system design question because it combines media storage, social graph traversal, and real-time analytics.

## Requirements

**Functional:**
- Create a story (photo/video, up to 15s, with stickers/text overlay)
- View stories from followed accounts, ordered by engagement
- Story expires 24 hours after creation
- View counts and seen-by list (visible to creator)
- Reactions and replies to stories

**Non-functional:**
- 500M DAU, assume 50M stories created per day
- P99 story load < 500ms
- View tracking: eventual consistency acceptable (counts lag by seconds is fine)
- 99.9% availability; brief outages during feed generation tolerable

## Media Storage

Stories contain media that must be served globally at low latency.

**Upload flow:**
1. Client uploads raw media to edge upload endpoint
2. Edge node acknowledges and writes to regional object store
3. Background transcoding pipeline processes video into multiple resolutions (240p, 480p, 720p) and formats (HLS for streaming)
4. CDN origins are populated; CDN edge nodes cache on first access

For photos, generate multiple resolutions (320px for thumbnails, 1080px for full view).

**Storage estimation:**
- 50M stories/day × 2MB average = 100TB/day
- 24-hour TTL means max active storage = 100TB
- With CDN caching, origin bandwidth is 10-20x less than total served

Use object storage (S3/GCS) with lifecycle rules to delete expired media. Don't rely on application-level TTL enforcement — storage lifecycle rules are the safety net.

## Story Metadata

Store story metadata in a distributed database:

```
stories table:
- story_id (UUID)
- creator_user_id
- created_at (timestamp)
- expires_at (created_at + 24h)
- media_url
- media_type (image/video)
- view_count (approximate)
- is_deleted
```

Use Cassandra or a similar wide-column store for write throughput. Stories are time-series data — write-heavy, with TTL reads common.

## Story Feed Generation

When you open Instagram, you see story rings from people you follow. The ordering is not chronological — it's engagement-weighted (accounts you interact with most appear first).

**Options:**

**Pull model (fan-out on read)**: When user X opens the app, query X's following list, check each for active stories, rank by engagement score. Expensive for users following 10K accounts.

**Push model (fan-out on write)**: When Y posts a story, write to each follower's story feed precomputed. Fast reads, expensive writes for celebrities with millions of followers.

**Hybrid**: Push for users with < 10K followers. Pull for mega-accounts (celebrities, brands). This is what Instagram actually does.

**Ranking signal** for ordering:
- Recency of story creation
- Historical interaction rate (likes, replies, profile visits)
- DM frequency
- Story view completion rate (if you always finish their stories)

The score is computed and stored in Redis sorted sets per user.

```
REDIS KEY: story_feed:{user_id}
TYPE: Sorted Set
SCORE: ranking_score (float, higher = shown first)
MEMBER: {creator_id}:{story_id}
TTL: 24 hours
```

## View Tracking

Stories need accurate-enough view counts and seen-by lists.

**View count**: Use an approximate counter. Write view events to a Kafka topic. A stream processor (Flink) aggregates counts and writes to Redis. The story metadata DB is updated asynchronously every 60 seconds. Eventual consistency is fine — creators don't need the exact real-time count.

**Seen-by list**: Creators can see who viewed their story, but only up to the 24-hour expiry. Store this in Redis as a sorted set (viewer_id, view_timestamp). Cap at displaying first 10K viewers for very popular creators.

```python
# Record a view
redis.zadd(f"story_views:{story_id}", {viewer_id: timestamp})
redis.expire(f"story_views:{story_id}", 86400)  # 24 hours

# Get viewer list
viewers = redis.zrangebyscore(f"story_views:{story_id}", 0, "+inf")
```

## Expiration

24-hour TTL requires:

1. **Soft delete in DB**: Set `expires_at` at creation. Background job sweeps expired stories every 5 minutes.
2. **Feed cleanup**: Remove expired story IDs from Redis sorted sets using `ZREMRANGEBYSCORE`.
3. **Media deletion**: Storage lifecycle rules delete objects 25 hours after creation (1-hour buffer for clock skew).
4. **CDN purge**: Trigger CDN purge when story expires to prevent stale cached content.

## Close Friends Feature

Stories can be posted to "Close Friends" — a restricted audience. Implement this as a whitelist stored in the social graph service. During fan-out, check if the viewer is in the creator's close-friends list before writing to their feed.

## Interview Tips

Key decisions to highlight:
1. **Why hybrid fan-out** — pure push doesn't work for celebrities, pure pull is slow
2. **Approximate view counts** — explain why exact counts are unnecessary and the tradeoff
3. **Storage lifecycle TTL** — don't just say "delete after 24h," explain how
4. **CDN strategy** — stories are globally distributed, CDN reduces origin load dramatically

This question is really about combining ephemeral storage, social graph systems, and real-time analytics. Show that you understand all three dimensions.
