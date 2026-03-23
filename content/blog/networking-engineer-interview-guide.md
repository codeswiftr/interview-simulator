---
title: "Computer Networking Interview Guide for Software Engineers"
description: "Networking fundamentals that software engineers actually get asked in interviews: TCP/IP deep dive, HTTP/2 and HTTP/3, DNS internals, load balancing algorithms, and how networking shows up in system design questions."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Computer Networking Interview Guide for Software Engineers

Networking questions appear in two interview contexts: specialist roles (network engineering, infrastructure, systems) where deep protocol knowledge is required, and general software engineering system design interviews where networking fundamentals inform architecture decisions. This guide covers both.

## TCP: What Every Engineer Needs to Know

TCP is the foundation of most application communication, and interviewers probe whether you understand it beyond "reliable byte stream."

**The three-way handshake**: SYN → SYN-ACK → ACK. Why three steps? The client proves it can send (SYN), the server proves it received and can respond (SYN-ACK), the client acknowledges (ACK). Two-way wouldn't confirm the server's packets reach the client.

**Flow control**: The receiver advertises a window size — how much data it can accept before the sender must pause. Prevents a fast sender from overwhelming a slow receiver. The window size is in each TCP segment header.

**Congestion control**: TCP detects network congestion (packet loss signals) and reduces its sending rate. Algorithms: Cubic (default Linux), BBR (Google's bandwidth-based algorithm, used in cloud providers). Why does this matter? In high-latency networks, TCP can be artificially slow because it's interpreting latency-based packet loss as congestion.

**TCP_NODELAY / Nagle's algorithm**: Nagle's algorithm batches small writes into larger segments to reduce overhead. This adds latency for interactive applications. `TCP_NODELAY` disables it. Know this for any application where you've tuned socket options.

**TIME_WAIT**: After closing a TCP connection, the socket stays in TIME_WAIT for 2 × MSL (Maximum Segment Lifetime, typically 60s). This prevents delayed packets from a previous connection being mistaken for a new connection. High-traffic servers with many short-lived connections can exhaust ephemeral ports. Solutions: `SO_REUSEADDR`, `SO_REUSEPORT`, connection pooling.

## HTTP/1.1 vs HTTP/2 vs HTTP/3

**HTTP/1.1**: text protocol, one request per connection (with keep-alive: sequential requests on one connection). Head-of-line blocking: if request 3 is slow, requests 4+ wait. Common workaround: open multiple connections (browsers typically open 6 per domain).

**HTTP/2**: binary framing, multiplexing (multiple streams on one connection, interleaved), header compression (HPACK), server push. Solves HTTP/1.1 head-of-line blocking at the application layer. But still has TCP head-of-line blocking: a lost packet stalls all streams on the TCP connection.

**HTTP/3**: runs over QUIC (UDP-based transport). Multiplexing without TCP head-of-line blocking — each QUIC stream has independent loss recovery. Faster connection establishment (0-RTT for resumed connections). Lower latency on lossy networks (mobile, high-latency paths). Tradeoff: UDP traversal can be blocked by enterprise firewalls; QUIC's encryption means middleboxes can't inspect traffic.

**Interview relevance**: "Why might HTTP/2 not improve performance over HTTP/1.1 for an application with many long-lived streaming responses?" — The multiplexing benefit applies most to many short parallel requests. For long-lived streams, the TCP head-of-line blocking problem may remain significant.

## DNS: The Actual Resolution Chain

Most engineers know DNS translates names to IPs. Fewer know the full chain:

1. Browser checks its DNS cache
2. OS checks `/etc/hosts` and its resolver cache
3. Stub resolver queries the recursive resolver (usually your ISP or 8.8.8.8)
4. Recursive resolver checks its cache; if miss:
5. Queries a root nameserver (which delegates to .com TLD servers)
6. Queries the .com TLD server (which delegates to authoritative nameserver)
7. Queries the authoritative nameserver (returns the A/AAAA record)

**TTL implications**: DNS records have TTLs. During a deployment, you lower the TTL before switching (so clients don't cache the old IP for long). After switching, you raise the TTL back.

**DNS and load balancing**: Round-robin DNS (return multiple A records), GeoDNS (return different IPs based on client geography), Anycast (same IP announced from multiple locations — request goes to nearest BGP-adjacent PoP). Understanding which is which matters for global system design questions.

## Load Balancing Algorithms

**Round-robin**: Requests distributed evenly across backends. Simple, works when requests are roughly equal in cost.

**Weighted round-robin**: Some backends get more requests (for heterogeneous hardware).

**Least connections**: Route to the backend with fewest active connections. Better than round-robin when request durations vary significantly.

**Consistent hashing**: Hash request attributes (user ID, session token) to route the same client to the same backend. Reduces cache misses for stateful backends. Used in distributed caching (Memcached sharding), database query routing.

**Session affinity (sticky sessions)**: Route all requests from a client to the same backend. Required for stateful applications that store session data in memory. Problematic for scaling (removing a backend drops sessions). Better architecture: externalize session state to Redis.

## Key System Design Applications

Understanding networking informs better system design answers:

"Design a global CDN": discuss anycast for PoP selection, origin shield for cache fill efficiency, HTTP/2 push for asset preloading, Brotli vs. gzip compression.

"Design a real-time chat system": discuss WebSocket (persistent TCP connection, bidirectional), the overhead of HTTP polling vs. long-polling vs. WebSocket, server-side events (SSE) for one-directional streaming.

"Why is your API slow for users in Southeast Asia?": TCP slow start on high-latency connections, TLS handshake RTT cost, DNS resolution time, geographic proximity of origin servers.

Networking knowledge isn't just for infrastructure engineers — it's what separates system design answers that sound sophisticated from ones that actually are.
