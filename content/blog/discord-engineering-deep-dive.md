# Discord Engineering Deep Dive: Real-Time Communication at Gaming Scale

Discord runs one of the most technically demanding communication platforms on the internet. Over a billion messages are delivered daily, millions of voice channels operate simultaneously, and the system must feel instantaneous to a user base that has zero patience for lag. The engineering decisions Discord has made — and publicly documented in extraordinary detail — reveal a company willing to make dramatic architectural shifts when the evidence demands it. If you are interviewing at Discord, understanding why these decisions were made matters more than memorizing what they were.

## The Go to Rust Migration: A Case Study in Performance Engineering

In July 2020, Discord published "Why Discord is switching from Go to Rust," one of the most widely read engineering blog posts of the decade. The subject was the Read States service: a component responsible for tracking which messages each user has read across all their channels. At first glance, this seems like a minor feature. In practice, it is one of Discord's most write-heavy services, updating on virtually every user action.

The Go implementation had a latency problem. Not the kind of latency you see in steady state — Go performed well there. The problem appeared at regular intervals: every two minutes, the Go garbage collector would pause the service, and during those pauses, tail latency would spike dramatically. A service that typically responded in under one millisecond would suddenly take hundreds of milliseconds. For users, this manifested as a brief but noticeable freeze, exactly the kind of experience that erodes trust in a real-time platform.

The Go garbage collector is generational and concurrent, designed to minimize stop-the-world pauses. But "minimize" is not "eliminate," and the Discord team found that no amount of tuning fully resolved the issue. The fundamental problem was that the Read States service maintained a large, hot LRU cache. Go's GC had to scan this cache periodically, and no configuration change could avoid the work entirely.

Rust does not have a garbage collector. Memory is managed through ownership and borrowing, enforced at compile time. There is no runtime pause because there is no runtime that needs to pause. The Discord team rewrote the Read States service in Rust and saw immediate results: the latency spikes disappeared, and median and tail latency both improved substantially.

What made this migration technically credible rather than just a rewrite-in-a-new-language experiment was the discipline of the comparison. The Go and Rust implementations ran side by side. The metrics were specific: p99 latency dropped from around 10ms to under 1ms, and the periodic spikes that reached 100ms-plus in Go became flat lines in Rust. The blog post included graphs. Discord was not doing this for engineering culture points — they were solving a real, measurable problem.

The broader lesson for Discord engineers, and for interview candidates, is that language choice is a systems decision, not a preference decision. Go's garbage collector is excellent for most services. For a service with a massive hot cache and strict latency requirements, the tradeoff changes. Rust's ownership model demands more from the programmer but delivers deterministic performance.

Here is a simplified illustration of how Discord's Rust caching logic might handle eviction without GC pressure:

```rust
use std::collections::HashMap;
use std::time::{Duration, Instant};

struct ReadStateCache {
    entries: HashMap<u64, CacheEntry>,
    capacity: usize,
}

struct CacheEntry {
    last_read_id: u64,
    last_accessed: Instant,
}

impl ReadStateCache {
    fn new(capacity: usize) -> Self {
        ReadStateCache {
            entries: HashMap::with_capacity(capacity),
            capacity,
        }
    }

    fn get(&mut self, user_id: u64) -> Option<u64> {
        if let Some(entry) = self.entries.get_mut(&user_id) {
            entry.last_accessed = Instant::now();
            Some(entry.last_read_id)
        } else {
            None
        }
    }

    fn set(&mut self, user_id: u64, last_read_id: u64) {
        if self.entries.len() >= self.capacity {
            self.evict_lru();
        }
        self.entries.insert(user_id, CacheEntry {
            last_read_id,
            last_accessed: Instant::now(),
        });
    }

    fn evict_lru(&mut self) {
        if let Some((&oldest_key, _)) = self.entries
            .iter()
            .min_by_key(|(_, entry)| entry.last_accessed)
        {
            self.entries.remove(&oldest_key);
        }
    }
}
```

No GC scan, no pause, no spike. The eviction is deterministic and triggered exactly when needed.

## WebSocket at Scale: Persistent Connections for a Billion Daily Messages

Discord's messaging infrastructure is built on WebSocket. HTTP request-response works for most web applications, but Discord's core value proposition is real-time. Polling scales poorly. Server-sent events are one-directional. WebSocket gives a persistent, bidirectional connection over a single TCP connection that works through most firewalls and proxies.

Each connected client holds a persistent connection to a gateway server. When a message is sent, the gateway fans it out to every online member of that server. Discord's gateway uses a sharding model: each connection is assigned to a shard based on guild ID, so fan-out for a guild happens locally within a shard process, avoiding cross-shard coordination in the common case.

The protocol is event-based: HELLO with a heartbeat interval on connect, READY with initial state, then a stream of events — MESSAGE_CREATE, PRESENCE_UPDATE, VOICE_STATE_UPDATE. Clients that fail to acknowledge heartbeats are dropped as zombies.

Backpressure is handled by closing connections that fall too far behind and allowing reconnection with a resume token that replays missed events from a buffer.

## Voice Infrastructure: Where Real-Time Becomes Non-Negotiable

Voice calls have latency requirements that make text messaging look forgiving. The human ear perceives delays above roughly 150 milliseconds as unnatural. Above 300 milliseconds, conversation rhythm breaks down entirely. Discord targets end-to-end audio latency well below these thresholds, which means the entire stack — from microphone capture through encoding, transport, decoding, and speaker playback — must operate with minimal buffering.

Discord uses WebRTC for voice transport. WebRTC uses UDP rather than TCP: TCP guarantees delivery by retransmitting lost packets and blocking until gaps are filled. For audio, a retransmitted packet arriving 200 milliseconds late is worse than useless — it plays out of order or requires buffering that defeats the latency target. UDP drops late packets and keeps moving.

The audio codec is Opus. Opus is the right tool for voice over IP in 2024: it is a hybrid codec that handles both speech (where SILK mode excels) and music (where CELT mode excels), adapts its bitrate to network conditions, and operates efficiently at low latencies. Crucially, Opus has built-in packet loss concealment. When a packet is lost, the decoder does not produce silence — it extrapolates from prior audio frames using the known statistical properties of speech signals. A 20-millisecond packet loss is largely inaudible when concealed correctly.

SRTP (Secure Real-time Transport Protocol) wraps the UDP audio stream with encryption and authentication. Discord encrypts voice traffic between clients and voice servers, and between voice servers when relaying across regions. The encryption overhead on modern hardware is negligible compared to the audio encoding/decoding work.

Voice servers are distributed geographically. When you connect to a voice channel, Discord selects a voice server region close to the majority of participants. The client performs ICE negotiation to establish the best path to that server — direct if possible, through a TURN relay if NAT traversal requires it. Most consumer NAT configurations allow direct UDP connections when both sides initiate, so full relay is relatively uncommon.

## The Database Journey: Cassandra, Migration, and ScyllaDB

Discord's database history is an engineering story worth knowing because it illustrates the real cost of data at scale. In 2017, Discord published "How Discord Stores Billions of Messages," describing their move from MongoDB to Cassandra. The reasoning was straightforward: message data is append-mostly, reads are typically by channel and time range, and Cassandra's data model maps naturally to this access pattern. MongoDB struggled with the random I/O patterns of a growing message history.

Cassandra delivered on its promises initially. But by 2020, Discord was experiencing problems familiar to anyone who has run Cassandra at extreme scale: hot partitions, GC pressure on the JVM, and slow reads when the on-disk data structures required compaction. The "Why We're Moving Away from Cassandra" post (2023) detailed the investigation.

The culprit was largely latency spikes caused by Cassandra's JVM garbage collection — an irony given that Go's GC issues drove the Rust migration. Cassandra's JVM heap contains live data structures that represent the memtable and bloom filters. Under load, GC pauses would cause p99 latency to spike, affecting user-visible reads of message history.

ScyllaDB, Cassandra's C++ reimplementation, eliminates the JVM from the picture. It uses a shard-per-core architecture and the Seastar asynchronous framework, which eliminates most context-switching overhead. Discord's ScyllaDB migration was gradual: they ran shadow writes to ScyllaDB while still serving from Cassandra, validated consistency, and then shifted read traffic over. The results showed dramatically reduced tail latency and lower hardware requirements.

The data model remained largely the same — wide rows partitioned by channel ID, clustered by message ID (a Snowflake-format integer encoding the timestamp). This design enables efficient range scans for message history while keeping related messages on the same node.

## Elixir for Presence: Scaling to Five Million Concurrent Users

In 2017, Discord published "How Discord Scaled Elixir to 5,000,000 Concurrent Users," describing their use of Elixir and the Erlang VM (BEAM) for the presence system. Presence tracking — who is online, what game they are playing, what their status is — is a fundamentally distributed problem. Every status change must propagate to every relevant connected client.

Elixir on BEAM is purpose-built for this workload. The BEAM scheduler supports millions of lightweight processes, preemptive scheduling, and no global GC pause — each process has its own small heap. Erlang was built for telecom switching, where the requirement is millions of concurrent connections at high availability.

Discord's presence system uses a CRDT-based approach (Conflict-free Replicated Data Type) to merge presence state across nodes without coordination. When two nodes receive conflicting presence updates — common in a distributed system with network partitions — CRDTs guarantee a consistent merge outcome based on the data structure's mathematical properties rather than requiring a distributed lock or consensus protocol.

Phoenix PubSub handles fan-out of presence events: a status change publishes to a topic, and all subscribed gateway connection processes forward the update to their clients.

## System Design: Real-Time Messaging with Connection State Management

A Discord-style system design interview question typically asks you to design a real-time messaging system with presence and voice. Here is a structured approach.

**Core components:**

The gateway layer accepts WebSocket connections from clients. Each gateway server manages a shard of guilds, with clients routed via consistent hashing on guild ID. The message service writes to a distributed log (Kafka) before fanning out to connected clients through the gateway layer. Message storage uses ScyllaDB partitioned by channel ID and clustered by message ID, enabling efficient range scans for history.

Connection state records to Redis on connect and clears on disconnect. The presence system subscribes to these session events. Voice uses a separate cluster for WebRTC signaling and media relay.

**Handling fan-out for large guilds:**

A server with 500,000 members creates a fan-out problem: a single message could require notifying all of them. Discord limits events to users who are actively viewing a channel (lazy loading) and distributes fan-out work across gateway workers using pub/sub.

**Presence at scale:**

Presence state is ephemeral and high-write. Discord keeps it in memory across a cluster of Elixir processes and replicates using CRDT merge. Gateway servers aggregate client subscriptions and pull presence data from the presence cluster.

## Interview Process and Coding Bar

Discord's process runs four to five rounds: recruiter screen, technical phone screen (one medium LeetCode problem with discussion), two coding rounds (medium to hard, preference for graphs, trees, or real-time systems), and a system design round.

The system design round focuses on real-time systems: messaging, presence, notification fanout. They want to see tradeoff reasoning around consistency versus latency, and opinions about why you would choose a wide-column store over relational for certain access patterns.

The behavioral rounds emphasize Discord's cultural values: building things you would use yourself, operating what you build, and developer empathy. They want specific examples of owning a service through failure and building features requiring cross-team coordination.

The coding bar is high but not adversarial. Explaining your approach before coding, discussing tradeoffs as you implement, and being honest about uncertainty all reflect positively. Discord values engineers who communicate clearly about what they do not know.

## Compensation and Equity

Discord's compensation is competitive with mid-tier FAANG rates, positioned below the highest-paying companies (Google, Meta at senior levels) but above the median for the industry. As of recent data, senior software engineers at Discord earn total compensation in the $250,000-$350,000 range depending on level and equity. Staff engineers reach $350,000-$500,000.

The equity picture requires care. Discord raised at a $15 billion valuation in 2021 before a market correction and has not pursued an IPO, creating uncertainty about liquidity. Evaluate strike price, preferred share overhang, and path to liquidity carefully.

Discord has real revenue (Nitro subscriptions, server boosts) and a product that has expanded beyond gaming into general community building. If an IPO or acquisition occurs at a strong valuation, earlier equity grants could be meaningful.

## Engineering Culture: Gaming DNA and Developer Empathy

Discord's culture reflects its origin as a product for gamers, built by engineers who are themselves gamers. This has concrete implications for how the team thinks about product quality. Gamers are among the most demanding users of real-time communication software — they have experienced voice chat in games with latency problems, they notice jitter, they feel the difference between 50ms and 150ms round-trip time. Discord's engineering culture takes that experience seriously.

"We build it, we run it" is not just a slogan at Discord. On-call rotations mean that the engineers who write services own those services in production. This creates strong incentives to build systems that are observable, that fail gracefully, and that have good runbooks. The Go-to-Rust migration for Read States was driven by engineers who were paged at 2am when latency spikes woke up the monitoring system. They solved the problem at the source rather than alerting around it.

The polyglot architecture — Python for tooling, Go for fast-iteration services, Rust for performance-critical paths, Elixir for concurrent presence work, React on the frontend — reflects a culture of using the right tool rather than mandating a single language. Breadth matters alongside depth.

Developer experience is an explicit value. Discord invests in internal tooling, clear service boundaries, and documentation. The engineering blog is evidence: teams are encouraged to write publicly about what they built and learned, creating accountability and a culture of thorough thinking.

## Technical Stack Summary

The Discord stack includes Python and Go for various backend services, Rust for latency-critical paths, Elixir on BEAM for presence, React and TypeScript for web and desktop, Kotlin and Swift for mobile, WebRTC and Opus for voice, WebSocket for event delivery, ScyllaDB for message storage, Postgres for relational data, Redis for caching, Kafka for event streaming, and GCP as the primary cloud provider.

This is not a stack you join to work in one language. It is a stack you join because you want to work across a distributed system that has solved hard real-time problems in public and continues to push on what communication infrastructure can be.
