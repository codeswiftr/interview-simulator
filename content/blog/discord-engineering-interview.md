---
title: "Discord Engineering Interview Guide: Real-Time Messaging, Guild Architecture, and Go at Discord"
description: "Prepare for Discord engineering interviews with deep knowledge of their real-time messaging stack, guild and channel data models, WebSocket gateway design, and Discord's move to Go and Rust."
date: "2026-03-20"
category: "Company Guides"
---

# Discord Engineering Interview Guide

Discord handles over 19 million concurrent users with a real-time messaging system that must feel instantaneous. Their engineering blog is among the most technically candid in the industry — from their famous "How Discord Stores Billions of Messages" (Cassandra → ScyllaDB) to "Why Discord is Switching from Go to Rust." Knowing this content is table stakes for a Discord interview.

## Discord's Engineering Identity

Discord's engineering culture is defined by a few core tensions they manage well:

- **Real-time vs. reliability**: Messages must arrive in milliseconds, but message delivery must be guaranteed
- **Scale vs. simplicity**: Supporting millions of concurrent connections without drowning in complexity
- **Flexibility vs. performance**: Users customize Discord heavily; the system must handle wildly varied load patterns per server (guild)

Discord engineers are expected to think in terms of these tensions, not just implement features.

## The Interview Process

Discord's interview loop typically includes:

- **Technical screen**: 1–2 coding problems (medium difficulty, real-world flavor)
- **System design**: Often gateway-related, message storage, or notification system
- **Architecture deep-dive**: For senior roles, a discussion of a system you've built at scale
- **Behavioral**: Values-based questions, team collaboration, handling ambiguity

## Real-Time Messaging Architecture

This is Discord's core competency. Know it deeply.

**The WebSocket Gateway:**
Discord uses a persistent WebSocket connection per client. When you open Discord, your client connects to a gateway server that:
1. Authenticates your session
2. Subscribes you to events for your guilds and DMs
3. Maintains a heartbeat to detect stale connections
4. Delivers events (messages, presence updates, voice state changes) in real-time

**Gateway dispatch model:**
Events are distributed from backend services to gateway nodes via a message queue (Discord uses Elixir + their own "manifold" system internally). Each gateway node knows which client sessions are subscribed to which guilds and routes events accordingly.

**Interview design question:** "Design the Discord gateway service."

Your answer should address:
- Session storage: Where do you track which gateway server holds which user session? (Redis or a distributed coordination service)
- Event fan-out: When a message is sent in a 500,000-member server, how do you deliver it to all online members without overwhelming the system?
- Reconnection: How do clients resume a session without missing messages? (Discord sends a `resume` sequence number; clients can replay missed events)
- Sharding: Discord uses "gateway sharding" — each bot shard handles a subset of guilds

## Guild and Channel Data Model

Understanding Discord's data model is essential for system design rounds.

**Guild (server):** The top-level container. A guild has:
- Members (user + guild-specific profile/nickname)
- Channels (text, voice, stage, forum, thread)
- Roles with permission bitsets
- Emojis, stickers, webhooks

**Permission system:** Discord uses a layered permission system:
1. Base guild permissions per role
2. Channel overrides per role
3. Channel overrides per user
4. Effective permission = bitwise combination of all applicable rules

This is a common design question: "How would you design a permission system for Discord?" Answer using bitmasks and cascading overrides.

**Message storage:**
Discord famously migrated from MongoDB to Cassandra to ScyllaDB. Key insight: messages are append-heavy, read-recent-first, and distributed by channel. Cassandra's partition key on `(channel_id, bucket)` and clustering key on `message_id` (Snowflake ID) gives efficient range scans for recent messages.

**Snowflake IDs:** Discord uses Twitter-style Snowflake IDs — 64-bit integers composed of:
- Timestamp (ms since Discord epoch)
- Worker ID
- Increment

This gives time-ordered IDs without a central coordinator, which is critical for distributed message storage.

## Go at Discord: What You Need to Know

Discord has used Go for several services, most famously their Read States service (which tracks what messages you've read across all channels). The blog post "How Discord Handles 2.5 Million Concurrent Voice Users Using WebRTC" and related posts reveal Go's role.

**Why Discord moved parts from Go to Rust:**
The specific issue was garbage collection pauses in Go causing latency spikes. For a soft real-time system, predictable latency matters more than average latency. Rust's memory model eliminates GC pauses.

In a Discord interview, being able to articulate this tradeoff — "Go is faster to write and deploy, but GC pauses introduce tail latency that matters for real-time systems" — demonstrates genuine systems understanding.

**Concurrency patterns in Go relevant to Discord:**

```go
// Fan-out pattern: broadcast an event to N subscribers
type EventBus struct {
    mu          sync.RWMutex
    subscribers map[string][]chan Event
}

func (b *EventBus) Publish(guildID string, event Event) {
    b.mu.RLock()
    defer b.mu.RUnlock()
    for _, ch := range b.subscribers[guildID] {
        select {
        case ch <- event:
        default:
            // Slow subscriber — drop or buffer
        }
    }
}
```

The `select` with `default` prevents a slow subscriber from blocking the entire fan-out — a critical pattern for Discord's scale.

## Voice and WebRTC

Discord's voice is built on WebRTC with a custom server-side mixing layer. Key concepts:

- **TURN/STUN**: For NAT traversal — know the difference
- **Selective Forwarding Unit (SFU)**: Discord uses an SFU architecture, forwarding individual participant streams rather than mixing server-side (saves CPU, allows client-side mix control)
- **Opus codec**: The audio codec of choice for real-time — know its properties (variable bitrate, resilient to packet loss)

## Coding Round Preparation

Discord's coding questions tend to be practical rather than abstract:

- Implement a simplified pub/sub system
- Design a rate limiter for the API gateway
- Parse a permission bitset and compute effective permissions
- Implement a sliding window for message rate limiting per user
- LRU cache for caching channel metadata

**Emphasis on correctness:** Discord interviewers pay attention to concurrent access patterns. If you write a cache without considering thread safety, expect follow-up questions.

## System Design Scenarios to Prepare

1. **Message storage at scale** — partitioning strategy, consistency model, read patterns
2. **Notification delivery** — push vs pull, reliability, battery optimization
3. **Presence system** — tracking online/offline/idle for millions of users
4. **Voice channel server assignment** — region-aware load balancing, failover

## Values and Behavioral Prep

Discord's culture emphasizes:
- **Ship with care**: Real-time systems with millions of users have no tolerance for P0s — discuss how you've tested and rolled out high-risk changes
- **User trust**: Discord serves young users — privacy, safety, and trust matter deeply
- **Collaboration over ego**: Discord team is noted for low-ego collaboration

The best Discord interview prep combines their engineering blog (read every post), Go/Rust knowledge, and genuine enthusiasm for the product. Discord engineers are usually avid Discord users — let that show.
