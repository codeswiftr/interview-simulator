---
title: "YouTube Video Transcoding Pipeline"
description: "How YouTube processes 500 hours of video uploaded per minute—chunked uploads, parallel transcoding, adaptive bitrate streaming, and the distributed media processing infrastructure."
date: "2026-03-21"
category: "System Design"
---

# YouTube Video Transcoding Pipeline

500 hours of video are uploaded to YouTube every minute. Each video must be transcoded into multiple resolutions and codecs, processed for content ID matching, indexed for search, and made globally available within minutes of upload. This is one of the most compute-intensive data processing pipelines in existence.

## Requirements

**Functional:**
- Chunked video upload (handle large files, resume on failure)
- Transcode to multiple formats: 360p, 480p, 720p, 1080p, 4K; H.264, VP9, AV1
- Generate thumbnails
- HLS/DASH manifest generation for adaptive bitrate streaming
- Content ID scanning (copyright matching)
- Caption/transcript generation

**Non-functional:**
- Processing latency: video available within 5 minutes of upload (at 1080p)
- Scale: 500 hours/minute = ~30,000 video files/minute
- Durability: 100% — no lost uploads
- Cost: transcoding is GPU-intensive, optimize for efficiency

## Chunked Upload Protocol

Raw video files can be tens of gigabytes. Standard HTTP upload fails on any network interruption.

YouTube uses **resumable uploads**:
1. Client requests upload URL (POST /upload/videos) → receives `upload_id`
2. Client splits file into 256KB–10MB chunks
3. Client uploads each chunk: `PUT /upload?upload_id=xxx&offset=N&length=L`
4. On failure: query resume position (`GET /upload?upload_id=xxx`) → server returns last confirmed offset → resume from there
5. Server reassembles chunks into complete file in GCS (Google Cloud Storage)

Each chunk upload is idempotent (same offset + same length + same content = same result). Checksum verification per chunk prevents corruption.

## Upload Service

```
Client → Upload Service → GCS (raw uploads bucket)
                              ↓ (completion event)
                         Pub/Sub (video_uploaded topic)
                              ↓
                    Transcoding Coordinator
```

The Upload Service is stateless. GCS is the persistent store. A Pub/Sub notification triggers downstream processing when all chunks are assembled.

## Transcoding Pipeline

Transcoding is CPU/GPU intensive and parallelizable across output formats.

**Transcoding Coordinator**:
1. Receives video_uploaded event
2. Creates transcoding jobs (one per output format)
3. Publishes jobs to priority queues (higher resolution = lower priority — start 360p first for fast availability)
4. Workers pull from queues and transcode

**Parallelism strategy**:
- **Spatial parallelism**: Multiple workers transcode different output resolutions in parallel
- **Temporal parallelism**: Split a long video into 10-second segments, transcode segments in parallel, concatenate
- Combined: a 2-hour video at 1080p might use 100 workers simultaneously

Temporal splitting reduces transcoding latency from hours to minutes:
```
2-hour video → 720 × 10-second segments
               → 720 parallel transcode jobs
               → ~5 minutes wall clock time
```

## Output Formats

For each input video, generate:

| Format | Container | Codec | Use Case |
|--------|-----------|-------|----------|
| 360p   | WebM, MP4 | VP9, H.264 | Mobile, slow connections |
| 720p   | WebM, MP4 | VP9, H.264 | Standard HD |
| 1080p  | WebM, MP4 | VP9, H.264 | Full HD |
| 4K     | WebM     | AV1, VP9   | Premium, newer devices |
| 480p   | MP4      | H.264      | Legacy device compatibility |

AV1 is the newest codec — 30-40% better compression than H.264 at same quality, but 3-5x more expensive to encode. Used for stored content where one-time encode cost is amortized across many views.

## HLS/DASH Manifest Generation

After all segments are transcoded, generate manifests for adaptive bitrate streaming:

**HLS (HTTP Live Streaming)**:
```m3u8
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p/index.m3u8
```

The client's player starts with the bandwidth-appropriate quality and switches up/down based on network conditions. Each quality level's manifest lists the segment files (10-second chunks, stored in GCS, served via CDN).

## Thumbnail Generation

Extract frames at regular intervals, apply ML-based scoring (blur detection, exposure, faces) to select the best thumbnail candidates. Creator gets a choice of 3-5 generated thumbnails plus the option to upload custom.

Auto-generated thumbnails:
1. Extract frames at 10% intervals
2. Score with quality model (no blur, good exposure, faces preferred, interesting composition)
3. Select top-3 frames as suggestions

## Content ID Scanning

YouTube's Content ID system matches uploaded videos against a database of copyrighted content. This runs asynchronously post-upload:

1. Extract video fingerprint (perceptual hash of video frames at regular intervals)
2. Extract audio fingerprint (chromaprint or similar)
3. Match against Content ID database (100M+ reference files)
4. If match: apply copyright holder's policy (block, monetize, or track)

The fingerprint matching uses an inverted index over frame hashes. Near-duplicate detection handles re-encoded copies.

## Storage Architecture

Raw uploads: temporary bucket (auto-deleted after 7 days if processing succeeds)
Transcoded output: CDN origin buckets (regional, multi-region replication)
Manifest files: CDN-served globally
Thumbnails: CDN-served, multiple resolutions

Storage estimation:
- 500 hours/minute × 60 = 30,000 videos/hour
- Average video 10 minutes × 500MB average storage per video per quality = 5GB per video across all qualities
- 30,000 × 5GB = 150TB/hour of new transcoded content
- CDN handles serving; origin bucket is authoritative

## Queue Architecture for Transcoding

Multiple priority queues:
- **P0**: First 360p transcode (fast availability — < 2 minutes)
- **P1**: 720p transcode
- **P2**: 1080p, 4K transcode
- **P3**: AV1 re-encode (happens days after upload for popular videos)

Workers autoscale based on queue depth. GKE (Google Kubernetes Engine) pods with GPU/CPU allocation per job type.

## Interview Tips

Key depth areas for this question:

1. **Chunked upload with resumability** — the offset-based resume protocol
2. **Temporal parallelism** — splitting video into segments for parallel transcoding
3. **Priority queues for output formats** — 360p first for fast availability
4. **HLS/DASH adaptive bitrate** — the client-side quality switching mechanism
5. **Content ID fingerprinting** — perceptual hashing at scale

The most impressive insight: temporal parallelism (splitting video into segments) is not obvious but reduces latency from hours to minutes for long videos.
