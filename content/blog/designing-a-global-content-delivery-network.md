---
title: "Designing a Global Content Delivery Network"
description: "How to design a CDN from scratch—edge node architecture, cache hierarchies, anycast routing, TLS termination, and origin shielding for serving global traffic at terabit scale."
date: "2026-03-21"
category: "System Design"
---

# Designing a Global Content Delivery Network

A CDN is foundational infrastructure for any large-scale web application. Designing one from scratch tests your understanding of networking, distributed caching, routing, and geographic distribution. Cloudflare, Fastly, and Akamai are the major players—but many large companies (Netflix, Meta, Apple) operate their own CDN infrastructure.

## Requirements

**Functional:**
- Serve static assets (images, JS, CSS, video) from the edge
- Cache dynamic content with configurable TTLs
- Support custom domains and TLS/SSL termination
- Purge cache on demand (content invalidation)
- Analytics: cache hit rate, latency percentiles, origin bandwidth saved

**Non-functional:**
- Global: edge nodes in 100+ cities
- Latency: < 20ms to nearest edge for 95% of global population
- Throughput: 1 Tbps+ aggregate
- Availability: 99.99%

## Architecture Overview

```
User → DNS (Anycast) → Nearest Edge Node
                             ↓ (cache hit)
                         Response to User
                             ↓ (cache miss)
                    Regional PoP (Parent Cache)
                             ↓ (still miss)
                         Origin Server
```

Three layers:
1. **Edge nodes** (hundreds, globally distributed): closest to users, L1 cache
2. **Regional PoPs** (points of presence, 20-30): regional aggregation, L2 cache
3. **Origin**: customer's server, the authoritative source

## Anycast Routing

The "nearest edge node" selection uses **BGP anycast**. Multiple edge nodes advertise the same IP address prefix. BGP routing protocol (the internet's routing backbone) naturally routes traffic to the topologically closest node.

```
IP: 104.16.0.0/12 (advertised by ALL CDN edge nodes globally)

User in Tokyo → BGP routes → Tokyo edge node
User in London → BGP routes → London edge node
```

This works for UDP-based protocols. For TCP (HTTP/HTTPS), connections must reach the same node they started on (TCP state), so anycast works because the TCP handshake and all subsequent packets follow the same BGP path.

Alternative: **GeoDNS**. DNS server returns different IP based on querying resolver's location. Less precise than anycast (depends on resolver location, not client location), but simpler to implement.

## Edge Node Architecture

Each edge node is a cluster of servers:

```
Incoming traffic → Load Balancer (L4, ECMP)
                        ↓
                  HTTP Proxy Layer
                  (Nginx/Envoy/Varnish)
                  ├─ TLS termination
                  ├─ HTTP/2 + HTTP/3
                  ├─ Cache lookup
                  └─ Origin fetch (on miss)
                        ↓ (cache storage)
                  SSD Cache
                  (tiered: hot in RAM, warm on NVMe)
```

TLS termination at the edge means the TLS handshake (100-200ms for new connections) happens at the nearest edge node, not at the distant origin. This is a major latency win.

## Cache Key Design

The cache key determines whether two requests share a cached response. Standard key:

```
cache_key = scheme + "://" + host + path + normalize(query_params)
```

Configuration per cache rule:
- **Ignore query params**: `image.jpg?size=large&v=2` → cached under `image.jpg`
- **Vary by header**: `Accept-Encoding`, `Accept-Language` (for multi-language assets)
- **Vary by cookie**: for authenticated content (use with care — fragments cache badly)

## Cache Hierarchy

**L1 (edge memory)**: In-RAM cache, 10-100GB per node. Sub-millisecond lookup. LRU eviction. Best for very hot content (viral images, popular JS bundles).

**L2 (edge SSD)**: NVMe SSDs, 1-10TB per node. 1-5ms access. Holds the long tail of popular content.

**L3 (regional PoP)**: Aggregates edge misses from multiple edge nodes in a region. Prevents all edges in a region from simultaneously hitting origin. This is called **origin shielding**.

Origin shielding: only one regional PoP contacts the origin for any given cache miss. If Tokyo, Osaka, and Fukuoka edge nodes all miss on the same asset, only the APAC regional PoP fetches from origin—once.

## Cache Invalidation

Two mechanisms:

**TTL-based**: Content expires after `Cache-Control: max-age=N`. Edge serves stale content without checking origin until TTL expires. Set appropriately: JS bundles get fingerprinted filenames, so `max-age=31536000` (1 year); HTML pages get `max-age=300` (5 minutes).

**Explicit purge**: Operator or customer triggers a purge. CDN must propagate purge to all edge nodes within seconds.

Purge propagation:
1. Customer hits purge API (`DELETE /cache?url=...`)
2. CDN control plane writes purge record to a distributed pub/sub (Kafka)
3. Edge nodes subscribe and process purge events
4. Edge marks cached object as stale; next request triggers origin fetch

At 100K+ edge nodes, propagation of a URL purge to all nodes in < 5 seconds is challenging. Use a tiered broadcast: control plane → regional controllers → edge nodes. Each hop is a Kafka consumer group.

**Surrogate keys (cache tags)**: Tag cached responses with logical keys (`product:123`, `user:456`). Purge all objects tagged with `product:123` in one operation. Akamai calls these "Fast Purge" keys; Fastly calls them "surrogate keys."

## TLS Management

At 100+ PoPs, managing TLS certificates is non-trivial:
- **Wildcard certificates**: `*.example.com` covers all customer subdomains
- **Certificate issuance**: Let's Encrypt ACME protocol, automated via DNS-01 challenge
- **Certificate storage**: distributed secret store (HashiCorp Vault or equivalent), replicated to all edge nodes
- **Renewal**: automated 30 days before expiry

For customer custom domains: provision Let's Encrypt certificate per domain, distribute to the edge nodes that serve that domain.

## HTTP/3 and QUIC

Modern CDNs support HTTP/3 (QUIC protocol). Benefits over HTTP/2:
- No head-of-line blocking (each stream is independent)
- Faster connection establishment (0-RTT for repeat connections)
- Better performance on lossy networks (mobile)

Edge nodes advertise HTTP/3 support via `Alt-Svc` header; clients that support QUIC upgrade automatically.

## Observability

Key metrics per edge node:
- Cache hit ratio (target > 90%)
- Origin traffic reduction (bandwidth savings)
- P99 latency (end-to-end)
- Error rate (5xx from origin)
- Bandwidth in/out

Aggregate to regional and global dashboards. Alert on cache hit ratio drop (may indicate cache poisoning or misconfiguration).

## Interview Tips

1. Start with anycast vs GeoDNS — shows networking knowledge
2. Explain the three-tier cache hierarchy and origin shielding
3. Cache key design is subtle — Vary header, query param handling
4. Purge propagation at scale (tiered broadcast, surrogate keys)
5. TLS termination at edge — always mention the latency benefit

The cache invalidation question ("how do you invalidate cache globally in < 5 seconds") is the hardest and most interesting part of this design.
