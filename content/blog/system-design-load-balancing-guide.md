---
title: "Load Balancing and High Availability in System Design Interviews"
description: "Master load balancing concepts for system design interviews. Covers load balancing algorithms, health checks, session persistence, horizontal vs vertical scaling, and high availability patterns."
date: "2025-10-30"
category: "Technical Skills Guides"
---

# Load Balancing and High Availability in System Design Interviews

Load balancing and high availability (HA) are foundational topics in system design interviews. Almost every large-scale system design — whether you're designing Twitter, Uber, or a URL shortener — requires discussing how to distribute load and ensure the system stays up.

## What Load Balancers Do

A load balancer sits between clients and your server fleet, distributing incoming requests across multiple servers to:
- Prevent any single server from being overwhelmed
- Enable horizontal scaling (add more servers to handle more load)
- Provide fault tolerance (route around unhealthy servers)
- Enable zero-downtime deployments (drain traffic from servers being updated)

## Load Balancing Algorithms

**Round Robin**: Requests rotate through servers in order (S1, S2, S3, S1, S2...). Simple, works well when servers are identical and requests are similar in cost.

**Weighted Round Robin**: Each server gets a weight proportional to its capacity. A server with 2x the CPU gets 2x the requests.

**Least Connections**: Route to the server with the fewest active connections. Better than round robin when requests vary significantly in duration (e.g., a mix of fast and slow queries).

**IP Hash**: Hash the client IP to determine which server handles requests from that IP. Provides "sticky sessions" without server-side state — the same client always hits the same server.

**Least Response Time**: Route to the server with the lowest combination of active connections and response time. The most sophisticated algorithm; used by HAProxy and Nginx in advanced configurations.

**Random**: Randomly pick a server. Surprisingly effective at large scale — statistical randomness balances well with many servers.

**Interview guidance**: "I'd default to least connections for most web applications since request cost is rarely uniform. For stateless microservices with uniform load, round robin is simpler and effective."

## Health Checks

Load balancers need to detect unhealthy servers and stop routing to them.

**Passive health checks**: Monitor actual traffic for errors (5xx responses, timeouts). Take servers out of rotation when error rate exceeds a threshold.

**Active health checks**: The load balancer periodically pings each server (HTTP GET `/health`, TCP connection attempt). Detects failures even when no real traffic is flowing to that server.

**Health check best practices**:
- `/health` endpoint should check actual dependencies (DB connection, cache connection), not just return 200
- Distinguish between liveness (is the process running?) and readiness (is the process ready for traffic?)
- Kubernetes uses both: liveness probes restart unhealthy pods, readiness probes remove them from service endpoints

## Session Persistence ("Sticky Sessions")

Some applications store session state in server memory, requiring the same client to always hit the same server.

**IP-based stickiness**: Hash the client IP. Simple but breaks with NAT (many clients sharing an IP) and CDNs.

**Cookie-based stickiness**: The load balancer injects a cookie identifying which backend server to use. More reliable than IP-based.

**Better approach**: Move session state out of servers entirely — store sessions in Redis or a database. Now all servers can handle any session, and you can scale freely. This is the correct architectural answer in most system design interviews.

## Layer 4 vs. Layer 7 Load Balancing

**Layer 4 (Transport)**: Load balancer sees IP and TCP/UDP headers but not the application protocol. Routes based on IP:port. Very fast (no packet inspection); can't make routing decisions based on HTTP path, headers, or cookies.

**Layer 7 (Application)**: Load balancer sees and can modify HTTP headers, URL paths, and bodies. Enables routing by URL path (`/api` to service A, `/static` to service B), A/B testing by header, and SSL termination. Slightly more overhead than L4.

**Interview guidance**: "For a simple web application, Layer 7 load balancing gives us the flexibility to route by path and handle SSL termination at the load balancer. For raw TCP services (non-HTTP), Layer 4 load balancing is appropriate."

## High Availability Patterns

**Active-Passive**: Primary server handles traffic; standby server takes over on failure. Simple, low overhead. Single point of failure during failover.

**Active-Active**: Multiple servers handle traffic simultaneously. Load balanced across all. No failover delay; higher throughput; more complex (need to handle split-brain scenarios).

**Multi-region Active-Active**: Traffic served from multiple geographic regions simultaneously. Highest availability; eliminates single-region failures. Requires careful data consistency design.

## Redundancy at Every Layer

True high availability requires eliminating single points of failure at every layer:

```
DNS (with TTL-based failover)
   → Load Balancer cluster (active-active or active-passive pair)
      → Application server fleet (auto-scaling group)
         → Cache cluster (Redis Cluster with replicas)
            → Database (primary + replicas, or distributed DB)
               → Storage (replicated object store)
```

## Auto-Scaling

Load balancers pair naturally with auto-scaling groups:
- **Scale out**: Add servers when average CPU/memory/request rate exceeds threshold
- **Scale in**: Remove servers when load drops (with cooldown period to prevent flapping)
- **Predictive scaling**: Pre-scale based on expected traffic patterns (daily cycles, known events)

**Interview framing**: "I'd use an auto-scaling group behind the load balancer. For baseline load, maintain 3 instances across 3 availability zones for HA. During peak load (which I'd determine from traffic patterns), scale out up to 20 instances."

Load balancing and HA discussions in system design interviews reward candidates who go beyond the basics — showing you understand the algorithms, the health check patterns, the session state trade-offs, and the multi-layer redundancy needed for true five-nines availability.
