---
title: "System Design: Video Streaming Platform (Netflix/YouTube)"
description: "Design a video streaming platform for 100M users — video upload pipeline, transcoding, CDN architecture, adaptive bitrate streaming, search, recommendations, and availability guarantees."
date: "2026-03-20"
category: "System Design"
---

# System Design: Video Streaming Platform (Netflix/YouTube)

Video streaming system design appears in senior and staff engineer interviews regularly. It tests your knowledge of CDNs, video processing pipelines, large-scale storage, and distributed systems under read-heavy load. Here's how to approach it from first principles.

## Requirements Clarification

Before drawing any boxes, establish scope. Functional: upload videos, process and transcode, stream to users, search, browse recommendations. Non-functional: 100M daily active users, 500M video views/day, 100K concurrent uploads, 99.99% availability, low latency streaming worldwide.

Key questions: What video resolutions? (360p to 4K). Live streaming or VOD? (Start with VOD). How long should upload complete? (Within minutes). What's the monetization model? (Subscriptions — affects which content is accessible).

## Upload Pipeline

Video upload is a write-heavy, latency-tolerant flow. Users don't expect instant availability — YouTube takes minutes to process a new video.

1. **Client upload**: Direct upload to object storage (S3/GCS) using presigned URLs. Don't proxy through your API servers — that wastes bandwidth and compute.
2. **Upload completion notification**: Storage event triggers a message queue (SQS/Kafka).
3. **Transcoding workers**: Pull from queue, transcode to multiple formats and resolutions. This is compute-intensive — use spot/preemptible VMs, queue-based scaling.
4. **Output storage**: Transcoded segments stored in object storage, organized by video ID and quality.
5. **Metadata update**: Mark video as available in the database.

Transcoding is the bottleneck. For a 2-hour video at 4K input, producing 360p/720p/1080p/4K outputs takes minutes. Use a transcoding farm that scales with queue depth. Services: AWS Elastic Transcoder, Google Transcoder API, or custom FFmpeg workers.

## Storage Architecture

Videos need two types of storage:

**Object storage** (S3/GCS): For video segments and thumbnails. Cheap, highly durable, designed for large sequential reads. Videos are accessed as chunked byte ranges.

**Metadata database**: Video title, description, uploader, upload time, view count, like count. This is relational data — PostgreSQL or MySQL. Shard by video ID at scale. Add read replicas for read-heavy workloads.

**Search index**: Elasticsearch for full-text search on titles and descriptions. Index metadata, not video content.

## CDN and Streaming Architecture

99% of streaming load is reads. CDNs are essential — serve video from edge nodes close to users.

**Adaptive Bitrate Streaming (HLS/DASH):** The video is split into short segments (2-10 seconds). The manifest file lists available qualities and segment URLs. The client player downloads the manifest, then requests segments at the highest quality the network supports. When network degrades, the player switches to lower quality segments mid-playback. This is how Netflix/YouTube prevent buffering — they adapt to your connection.

**CDN architecture for video:**
- Origin: object storage with your video segments
- CDN edge nodes: cache segments locally after first request
- Cache TTL: very long (segments are immutable by content hash)
- Cache hit rate: ~95%+ for popular content, <50% for long-tail

For extremely popular content (Super Bowl, viral videos), pre-push to CDN edge nodes before traffic spikes.

## Recommendation System

Recommendations drive 70%+ of views on YouTube. This is a two-stage pipeline:

**Candidate generation**: From millions of videos, generate hundreds of candidates for a user. Uses collaborative filtering (users who watched X also watched Y) and content-based filtering (similar topics, creators). This runs on a precomputed model, often matrix factorization or two-tower neural networks.

**Ranking**: Re-rank the hundreds of candidates using heavier features: user engagement history with this specific content type, predicted click-through rate, predicted watch completion rate. This runs per-request but on a small candidate set.

**Offline vs online:** Collaborative filtering runs offline (batch) on a daily or hourly basis. The final ranking runs online per-request. Precomputed user and video embeddings are stored in a feature store (Redis or a dedicated serving system).

## Search

Search for a video platform needs to be fast (<200ms), handle typos, and rank by relevance + quality signals.

Use Elasticsearch with inverted indexes on title and description. Index update: when a video is transcoded and metadata saved, write to Elasticsearch asynchronously. Boost results by engagement signals (view count, like/dislike ratio). For typo handling: fuzzy matching with edit distance.

## Hot Video / Traffic Spikes

A video going viral creates a sudden 1000× traffic spike on specific segments. Strategies:

**CDN caching:** The CDN absorbs most traffic. First few requests miss cache; subsequent millions hit it.

**Request coalescing at CDN:** If 10,000 users request the same segment simultaneously before it's cached, the CDN sends only one origin request and serves all 10,000 from that one response.

**Hotspot detection:** Monitor CDN miss rates. If a video's miss rate spikes (viral event), proactively push to more edge nodes.

## Availability and Reliability

For 99.99% availability (52 minutes downtime/year), key investments:

- Multi-region deployment with automatic failover
- CDN provides resilience for streaming (user fails over to another edge)
- Metadata database with synchronous replication to a standby in another AZ
- Upload pipeline: queue-based so temporary worker outages don't lose uploads
- Circuit breakers on all external service calls

The streaming path (CDN → user) is the most critical and also the most resilient — CDN providers have massive redundancy built in.

## Monitoring

Key metrics: video startup time, buffering ratio (time spent buffering / total watch time), video quality score (average bitrate served), CDN cache hit rate, upload processing time (P50/P95/P99), and transcoding queue depth.

Alert on: startup time P95 > 3s, buffering ratio > 1%, transcoding queue depth > 10K (indicates worker capacity issue).

## Interview Walkthrough

When presenting this design: start with requirements, then flow left-to-right through upload pipeline and streaming pipeline separately. Discuss CDN early — it's the most important architectural element for scale. Spend time on adaptive bitrate since it's central to user experience. Mention recommendations if asked about engagement features. Finish with monitoring and failure scenarios.


## Related Articles

- [Netflix Personalization System Design](/blog/netflix-personalization-system-design)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [System Design: Recommendation Engine](/blog/system-design-recommendation-engine)
- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
