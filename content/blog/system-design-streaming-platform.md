---
title: "System Design: Video Streaming Platform — Building Netflix at Scale"
description: "How to design a video streaming platform in system design interviews — video ingestion, transcoding pipelines, CDN strategy, adaptive bitrate streaming, and handling 200M concurrent viewers."
date: "2026-03-20"
category: "System Design"
---

# System Design: Video Streaming Platform — Building Netflix at Scale

Video streaming is a top-tier system design question that appears in senior and staff interviews at Netflix, YouTube, Amazon, and their competitors. It combines storage, CDN, encoding pipelines, and real-time delivery at a scale that tests your understanding of every distributed systems concept. This guide walks through the complete design with the depth interviewers expect.

## Requirements Clarification

Before designing, establish scope:

- **Users**: 200 million daily active users, 500 million total
- **Content**: 50,000 hours of video uploaded per day; catalog of 15,000 titles
- **Playback**: Peak concurrent viewers 10 million
- **Quality**: 360p to 4K HDR; mobile, web, TV clients
- **Latency**: Playback starts within 2 seconds; buffering under 1%

## High-Level Architecture

The system has two major flows: **upload/ingestion** and **playback**.

**Upload flow**: Creator → Upload Service → Object Storage → Transcoding Pipeline → CDN

**Playback flow**: Viewer → Client App → API Gateway → Content Metadata Service → CDN (video segments)

## Video Ingestion and Transcoding

Raw video uploads go to a staging bucket (S3 or equivalent). The Upload Service validates file integrity (checksum), splits large files into chunks for resumable uploads, and triggers the transcoding pipeline.

**Transcoding** converts raw video into multiple formats and resolutions. A single 2-hour movie generates 20-40 output files: different resolutions (360p, 480p, 720p, 1080p, 4K), different codecs (H.264, H.265/HEVC, AV1), and different audio tracks (stereo, 5.1 surround, multiple languages).

The transcoding pipeline is CPU-intensive and embarrassingly parallel — each chunk of a video can be transcoded independently. Use a distributed job queue (Kafka or SQS) to distribute transcoding work across a fleet of GPU/CPU workers. Workers pick up jobs, transcode a segment, and write output to the CDN origin store.

**Why multiple codecs?** H.264 has universal support. H.265 gives 40% better compression at equivalent quality. AV1 gives another 30% improvement but requires more powerful devices. Serving AV1 to modern devices reduces CDN costs significantly at Netflix's scale.

## Adaptive Bitrate Streaming (ABR)

ABR is the technology that makes streaming resilient to network changes. Instead of serving one continuous video file, the video is divided into short segments (2-10 seconds each) at multiple quality levels. The client selects which segment to download based on current bandwidth.

The standard protocols are **HLS** (HTTP Live Streaming, Apple) and **MPEG-DASH** (Dynamic Adaptive Streaming over HTTP). Both use a manifest file that lists available quality levels and segment URLs. The client downloads the manifest, then selects segments based on its ABR algorithm.

The ABR algorithm tracks download speed and buffer level. If the buffer is growing, it requests higher quality. If the buffer is shrinking, it steps down. Netflix's per-title encoding adjusts segment sizes based on scene complexity — a static scene compresses to much smaller files than an action sequence.

## CDN Architecture

Content is expensive to serve from origin. CDNs solve this by caching content close to users. Netflix uses a combination of commercial CDNs (Akamai, Fastly) and its own Open Connect CDN (ISPs host Netflix appliances inside their networks).

**Cache key design**: Segment URLs include quality level, segment number, and content ID. This ensures different quality levels don't evict each other from cache.

**CDN hit rate**: Popular new releases should achieve >99% CDN hit rate. Long-tail catalog may serve from origin more frequently. Pre-position (pre-warm) major new releases to CDN edges before launch by pushing content during off-peak hours.

**Geo-routing**: DNS-based routing sends users to the nearest CDN edge. Anycast routing provides automatic failover — if one edge is overloaded, traffic automatically routes elsewhere.

## Metadata and Catalog Service

Video metadata (title, description, thumbnails, cast, ratings) is stored in a PostgreSQL database with read replicas. Search uses Elasticsearch. Recommendations use a separate ML platform (collaborative filtering + content-based).

The catalog service is read-heavy. Cache metadata in Redis with TTL of 1-5 minutes. Invalidate on content updates. A separate CDN layer can cache thumbnail images and poster art — these are static and highly cacheable.

## DRM and Content Protection

Studio licenses require Digital Rights Management. Widevine (Google), FairPlay (Apple), and PlayReady (Microsoft) cover all major platforms. The content key service issues decryption keys to authenticated clients. Keys are short-lived (24-48 hours) and tied to the user's account and device.

Never serve unencrypted master files via CDN. Only the encrypted, transcoded segments go to CDN; decryption keys are fetched separately via HTTPS to an authenticated endpoint.

## Failure Handling

- **Transcoding failure**: Retry with exponential backoff; alert on repeated failures; maintain a dead letter queue for manual review
- **CDN origin unavailable**: Fall back to secondary origin; use circuit breaker to avoid cascading failures
- **Playback errors**: Client retries with lower quality; switch to backup CDN if primary fails; degrade gracefully before showing error

## Monitoring and SLOs

Key metrics: playback start time (p95 < 2s), buffering ratio (< 0.5%), error rate (< 0.1%), rebuffer events per hour. Alert on anomalies — a 10x spike in buffering in a region usually indicates CDN or network issues.

This design covers the core system. Interviewers will probe specific components — be prepared to go deep on transcoding parallelism, CDN cache consistency, or ABR algorithm design.
