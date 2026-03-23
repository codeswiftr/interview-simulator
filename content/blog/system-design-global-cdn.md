---
title: "System Design: Build a Global Content Delivery Network"
description: "A structured walkthrough of designing a global CDN from first principles — edge nodes, origin servers, cache invalidation strategies, anycast routing, TLS termination, and the real tradeoffs that distinguish passing answers from strong ones."
date: "2026-03-20"
category: "System Design"
---

Designing a Content Delivery Network is one of the most technically rich system design problems you'll encounter in senior and staff-level interviews. It touches caching at scale, global networking, consistency tradeoffs, and the operational realities of serving hundreds of millions of requests per second. A strong answer requires understanding not just what a CDN does, but why each architectural choice exists.

## Clarify Requirements First

Before drawing any boxes, establish the problem boundaries:

- **Scale:** How many requests per second at peak? (Assume 10M RPS globally for a major CDN)
- **Content types:** Static assets only (JS, CSS, images), video streams, or API responses?
- **Latency requirements:** P99 latency target at the edge?
- **Freshness:** Is strong consistency required or is eventual consistency acceptable?
- **Geo distribution:** Which regions must be covered?

For this walkthrough, we design a CDN serving static assets and video content globally, targeting sub-50ms P95 latency at the edge, with eventual consistency acceptable for most content.

## High-Level Architecture

A CDN has three tiers:

**Origin servers** — The authoritative source of truth. These are the customer's web servers or object storage buckets. Content is created and updated here. The origin is not expected to serve the majority of traffic; it serves cache misses and content that hasn't been distributed yet.

**Mid-tier caches (shield nodes)** — An optional layer between edge and origin that aggregates cache miss traffic. Without a shield layer, a cache miss at every one of 200 edge nodes for a popular asset causes 200 requests to hit the origin. With a shield layer, all edge nodes in a region miss to the regional shield, and the shield makes a single request to origin. This dramatically reduces origin load.

**Edge nodes (PoPs — Points of Presence)** — Geographically distributed servers that serve content to end users. An edge node receives a request, checks its cache, serves the cached response on a hit, or fetches from the shield/origin on a miss. There are typically 100–300 PoPs in a large CDN covering major metropolitan areas globally.

## DNS and Anycast Routing

How does a user's request reach the nearest edge node? Two primary mechanisms:

**DNS-based routing (GeoDNS):** The CDN's authoritative DNS server returns different IP addresses based on the requester's geographic location (inferred from resolver IP). A user in Tokyo gets the IP of the Tokyo PoP; a user in Frankfurt gets the Frankfurt PoP IP. DNS TTLs are kept short (30–60 seconds) to enable fast failover.

**Anycast routing:** The more sophisticated approach used by most modern CDNs. All edge nodes advertise the same IP address block via BGP. The internet's routing protocol automatically directs traffic to the topologically nearest node advertising that prefix. Anycast provides automatic failover and load distribution without application-level DNS logic. Cloudflare uses anycast for all their edge traffic.

In practice, large CDNs use both: anycast for initial routing and DNS overrides for fine-grained traffic steering or region-specific policy.

## Caching: The Core Problem

**Cache keys** — A cache entry is identified by a key, typically derived from the URL, request method, and sometimes headers (like `Accept-Encoding` or `Vary` headers). Cache key design matters: too broad means incorrect cache sharing (serving gzipped content to a client that doesn't support it); too narrow means low hit rates.

**TTL and Cache-Control headers** — Content sets its own caching policy via HTTP headers: `Cache-Control: max-age=86400` tells edge nodes to serve the cached copy for 24 hours. Different content types warrant different TTLs: a logo image might be cached for a year; an API response for 30 seconds.

**Cache hit ratio** — The fraction of requests served from cache without hitting origin. A good CDN achieves 95–99% hit ratios for cacheable content. Low hit ratios indicate either too-short TTLs, poor cache key design, or content that is genuinely uncacheable (personalized or user-specific responses).

**Negative caching** — Caching 404 responses prevents origin hammering for non-existent resources. Set a short TTL (60 seconds) to avoid staling 404s that become 200s after deployment.

## Cache Invalidation: The Hard Part

Cache invalidation is the second hardest problem in computer science (after naming things). In a CDN, there are three main approaches:

**TTL expiration** — Let cache entries expire naturally. Simple, but introduces latency between content update and cache refresh. Unacceptable for time-sensitive updates.

**Purge API** — The CDN exposes an API that allows customers to immediately invalidate specific URLs or URL patterns. The purge request propagates to all edge nodes (eventually consistently). Propagation typically takes seconds to minutes depending on CDN size. This is the standard mechanism for deployment-triggered invalidation.

**Surrogate keys (cache tags)** — An advanced technique where content is tagged with logical identifiers. Purging a tag invalidates all objects sharing that tag. A news article might be tagged with its article ID, its author's ID, and its category. Updating the author's name triggers a purge of the author tag, invalidating all that author's articles simultaneously. Fastly and Varnish support this natively.

**Versioned URLs** — The most reliable approach: embed a content hash in the URL. `main.a3f9b2c.js` never changes (it's content-addressed), so it can be cached forever. A deployment generates a new URL with a new hash. No invalidation needed — the old URL simply stops being referenced. This is the recommended approach for static assets in modern frontend builds.

## TLS Termination at the Edge

TLS handshakes are expensive and geographically sensitive — a TLS handshake between a browser in Sydney and an origin in Virginia adds 200–400ms of latency just for the handshake. Edge nodes terminate TLS, meaning the encrypted HTTPS session ends at the PoP. Traffic from the PoP to origin may be over a CDN's private network backbone (often unencrypted or re-encrypted over a separate TLS session within the CDN's infrastructure).

Key considerations for TLS at the edge:
- **Certificate distribution:** SSL certificates must be deployed to all edge nodes. Wildcard certs (`*.example.com`) simplify distribution.
- **Session resumption:** TLS 1.3 session resumption allows subsequent connections from the same client to skip the full handshake. Edge nodes must share session state (or use session tickets) across the PoP's servers.
- **OCSP stapling:** Edge nodes staple OCSP responses to TLS handshakes, saving clients an additional round trip for certificate revocation checking.

## Handling Video Streaming

Video content introduces distinct requirements:

**Chunked delivery:** Video is delivered as a sequence of small segments (typically 2–10 seconds each) using protocols like HLS or MPEG-DASH. Each segment is a separate cacheable object. Edge nodes cache individual segments, not full video files.

**Byte-range requests:** Clients may request specific byte ranges of a file. CDN must support partial content (HTTP 206) and handle cache keys that include range headers correctly.

**Adaptive bitrate:** Clients switch between quality levels based on available bandwidth. Each quality level is a separate set of segment URLs, all cacheable independently.

## Observability and Reliability

A CDN serving 10M RPS needs:

- **Real-time edge metrics:** Cache hit ratio, P50/P95/P99 latency, error rates — surfaced per PoP and globally
- **Health checks:** Each PoP continuously checks origin and shield health. Unhealthy origins trigger failover to cached content (serve stale) or error pages.
- **Anomaly detection:** DDoS traffic patterns (traffic spikes, signature payloads) must be detected and mitigated at the edge before reaching origin.

## Interview Summary

The strongest answers to CDN design questions demonstrate understanding of:
1. Why anycast is architecturally elegant compared to DNS-only routing
2. The tradeoff between TTL-based and purge-based invalidation
3. Why versioned URLs solve invalidation cleanly for static assets
4. The shield layer's role in protecting origin during traffic spikes
5. TLS termination's latency impact and why edge nodes must hold certificates

CDN design is an excellent vehicle for demonstrating that you understand how networking, caching, and distributed systems interact at production scale.
