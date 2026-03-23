---
title: "System Design: Video Streaming Platform (YouTube/Netflix Architecture)"
description: "How to design a video streaming platform in system design interviews — upload and transcoding pipeline, CDN distribution, adaptive bitrate streaming, recommendation, and storage."
date: "2026-03-20"
category: "System Design"
---

# System Design: Video Streaming Platform (YouTube/Netflix Architecture)

Video streaming is a staple of senior system design interviews. The question tests your understanding of large binary data pipelines, CDN architecture, and the specific challenges of delivering variable-quality video to billions of devices. This guide walks through a complete architecture, separating the write path (upload and processing) from the read path (streaming delivery).

## Clarify Scope and Requirements

Before designing, establish scale:

- Upload volume: YouTube processes ~500 hours of video per minute
- Viewers: Netflix serves 250M+ subscribers; YouTube 2B+ monthly users
- Latency tolerance: video-on-demand can buffer a few seconds; live streaming needs < 10s end-to-end latency
- Device diversity: mobile (3G to 5G), smart TV, laptop, varying screen resolutions

For a standard interview: focus on video-on-demand (not live), 1B daily active users, video up to 4K resolution, global distribution.

## Video Upload Pipeline

The upload pipeline has two phases: ingestion and processing.

**Ingestion**: large files (multi-GB) cannot be uploaded in a single HTTP request reliably. Use **chunked upload**: the client splits the video into 5–10MB chunks, uploads each independently with a chunk index, and the server reassembles. If the upload is interrupted, the client retries only failed chunks. This is exactly how YouTube's resumable upload API works.

Each chunk lands in temporary object storage (S3-equivalent). Once all chunks are received, the server triggers the transcoding pipeline.

**Transcoding workers**: raw video (often H.264 or ProRes from a camera) must be encoded into multiple formats and resolutions:

- Resolutions: 360p, 480p, 720p, 1080p, 1440p, 4K
- Codecs: H.264 (universal compatibility), H.265/HEVC (better compression, newer devices), AV1 (open, excellent compression, newer hardware)
- Container format: MP4 for download/VOD, fragmented MP4 (fMP4) for HLS/DASH streaming

Transcoding is CPU-intensive. Use a job queue (SQS or Kafka) with a pool of transcoding workers — autoscale this pool based on queue depth. Each worker produces a set of output files (one per resolution/codec combination) and writes them to a permanent object store bucket.

A **metadata service** records the job status, output URLs, and video metadata (duration, dimensions, thumbnail timestamps) in a relational database.

## Packaging for Adaptive Bitrate Streaming

Transcoded video files alone aren't enough for smooth streaming. You need to package them for adaptive bitrate (ABR) streaming protocols: **HLS** (HTTP Live Streaming, dominant on iOS/Mac) and **DASH** (Dynamic Adaptive Streaming over HTTP, dominant on Android/web).

ABR packaging splits each resolution's video into short **segments** (typically 2–6 seconds each) and generates a **manifest file** (`.m3u8` for HLS, `.mpd` for DASH) that lists all segments and their URLs, organized by quality level.

The client player downloads the manifest, then selects which quality level to start at and adjusts dynamically based on measured download throughput and buffer state. This is the adaptive in ABR — it switches quality mid-stream without interruption.

Store segments in object storage organized by `{video_id}/{resolution}/{segment_number}.ts` (or `.m4s` for DASH). The manifest is a small text file, typically < 10KB.

## CDN Strategy

Object storage alone has too much latency for global delivery — a viewer in Jakarta should not be fetching segments from a US-East S3 bucket.

**CDN (Content Delivery Network)**: a global network of edge PoPs (points of presence) caches video segments close to viewers. On a cache miss, the edge fetches from the origin (your object store), caches it, and serves subsequent requests from cache.

Key CDN design decisions:

- **Cache TTL**: video segments are immutable once published. Set a long TTL (hours to days). Manifests may update (live streams) and need shorter TTLs.
- **Origin selection**: use a multi-region object storage setup. CDN PoPs should be configured with a regional origin — US PoPs pull from us-east, Asian PoPs pull from ap-southeast.
- **Cache warming**: for viral or scheduled content (major sporting events, new releases), pre-populate CDN caches before traffic hits. Netflix does this with its Open Connect appliances placed directly in ISP networks.
- **Cost optimization**: CDN egress is expensive. For long-tail (rarely watched) videos, it's cheaper to serve from origin on cache miss rather than pre-distribute everywhere.

## Metadata, Storage, and Database

The system has two fundamentally different data types:

**Video files** (large blobs): object storage (S3). Never store binary video in a relational database. Use object storage versioning to keep original source video alongside transcoded outputs.

**Metadata** (small structured data): video title, description, uploader, upload timestamp, view count, tags, transcoding status, segment URLs. A relational database (PostgreSQL) works for most metadata. View counts are high-write and can be batched — write view events to Kafka, aggregate periodically, update the count.

**Search index**: video metadata feeds an Elasticsearch or Solr index for full-text search on titles and descriptions.

## Recommendation System Interaction

The recommendation system is a large separate subsystem, but you should know how it connects:

- **Signals ingested**: watch time, completion rate, likes, shares, search queries, co-views (users who watched A also watched B)
- **Model types**: collaborative filtering (user-item matrix), content-based (video embedding similarity), two-tower neural models for large-scale retrieval
- **Serving**: pre-compute recommendation lists per user and store in a key-value store (Redis or DynamoDB) for fast retrieval at page load

In the interview, you don't need to design the recommendation system in depth — acknowledge it exists, mention 2–3 signals, and note it's a separate ML system.

## Analytics Pipeline

Video platforms need to track detailed playback analytics: quality switches, buffering events, play duration per device, geographic distribution.

Stream these events into a Kafka pipeline → batch aggregation (Spark/Flink) → analytical data warehouse (BigQuery, Redshift). The analytics pipeline is separate from the transactional path and should not affect video delivery latency.

## Common Follow-Up Questions

**How do you handle video deduplication?** Compute a perceptual hash of the video at upload time and check against a hash store. Used for copyright enforcement (Content ID) and storage deduplication.

**How do you support live streaming?** Live streaming requires a separate low-latency ingest path (RTMP ingest → real-time segmenter → CDN push). Segment duration drops to 1–2s, and manifests update every segment. The end-to-end latency target is typically 5–30s for broadcast, < 1s for real-time (WebRTC).

**How do you handle 4K HDR efficiently?** Serve AV1 codec to capable devices — ~30% better compression than H.264. Use client capability detection (via User-Agent or explicit API) to select the right codec manifest.

**What happens during a CDN outage?** Configure CDN failover to origin with rate limiting. For major outages, serve lower-resolution content from backup CDN providers.

The key to answering this question well is separating the upload/processing pipeline from the read/serving path, and demonstrating you understand why CDN is the dominant cost and performance driver in video delivery.
