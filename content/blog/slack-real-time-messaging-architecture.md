---
title: "Slack Real-Time Messaging Architecture"
description: "How Slack's real-time messaging works—WebSocket multiplexing, message delivery guarantees, search indexing, and the architecture handling 10B+ messages per day."
date: "2026-03-21"
category: "System Design"
---

# Slack Real-Time Messaging Architecture

Slack handles 10 billion messages per day across 750,000+ organizations. Real-time delivery, message search, threading, and offline sync make this a multi-dimensional system design problem that tests WebSocket handling, message queuing, and search infrastructure.

## Requirements

**Functional:**
- Send/receive messages in channels, DMs, group DMs
- Threading (replies to messages)
- Real-time delivery with read receipts
- Full-text search across message history
- File attachments and link unfurling
- Offline message buffering (mobile)

**Non-functional:**
- Message delivery < 100ms for 99% of messages
- 750K organizations, avg 200 users each = 150M users
- At-least-once delivery (no dropped messages)
- Message ordering per channel guaranteed

## Real-Time Delivery: WebSockets

Slack clients maintain a persistent WebSocket connection to a gateway server. Each user's WebSocket connection is routed to a specific gateway node.

```
Client A ──WebSocket──> Gateway Node 1 (GW1)
Client B ──WebSocket──> Gateway Node 2 (GW2)
Client C ──WebSocket──> Gateway Node 1 (GW1)
```

When Client A sends a message to a channel where Clients B and C are members:

```
1. Client A → GW1 (via WebSocket)
2. GW1 → Message Service (HTTP/gRPC)
3. Message Service → persists to DB
4. Message Service → publishes to Pub/Sub (Kafka)
5. Pub/Sub → all gateway nodes subscribed to this channel
6. GW1 → Client C (WebSocket)
7. GW2 → Client B (WebSocket)
```

The challenge: A channel can have thousands of members. Step 5 (fan-out) must be efficient.

## Fan-Out Architecture

For small channels (< 1,000 members): fan-out on write. When a message is published, push to every member's connection immediately.

For large channels (100K+ members, like big company-wide announcements): fan-out on read. Members poll or receive push notifications on their next interaction.

Hybrid in practice:
- Maintain "active presence" per user (WebSocket connected in last 30s)
- Push only to currently active members
- Offline members get messages on reconnect via a sync protocol

## Message Delivery Guarantee

At-least-once delivery with deduplication:

1. Each message has a globally unique `message_id` (client-generated UUID + timestamp)
2. Client sends message with `client_msg_id` for idempotency
3. Server ACKs with server-assigned `ts` (timestamp, used as message ID in Slack's API)
4. If client doesn't receive ACK within 5 seconds, retry with same `client_msg_id`
5. Server deduplicates on `client_msg_id` — duplicate writes are no-ops

Ordering: messages within a channel are ordered by server timestamp (`ts`). The server assigns `ts` at write time, ensuring consistent ordering even when multiple clients send simultaneously.

## Message Storage

Slack uses a sharded relational database (originally MySQL, moved to a custom sharding layer called Vitess).

Sharding strategy:
- **By workspace**: all messages for a workspace live on the same shard. Enables efficient workspace-scoped queries.
- **Hotspot mitigation**: very large workspaces (enterprise accounts) get their own dedicated shard.

Schema (simplified):
```sql
CREATE TABLE messages (
    workspace_id BIGINT,
    channel_id   BIGINT,
    ts           DECIMAL(17,6),  -- Unix timestamp, nanosecond precision
    user_id      BIGINT,
    content      TEXT,
    thread_ts    DECIMAL(17,6),  -- NULL for top-level, parent ts for replies
    is_deleted   BOOLEAN,
    PRIMARY KEY (workspace_id, channel_id, ts)
);
```

The `ts` serves as both ordering key and unique ID. Replies store `thread_ts` pointing to their parent.

## Message Search

Full-text search over 10B+ messages requires a dedicated search index.

Architecture:
1. Message write → dual-write to Kafka
2. Kafka consumer → Elasticsearch (or Lucene-based index)
3. Index partitioned by workspace (each workspace in its own Elasticsearch index)
4. Search queries target the workspace index with filters on channel membership

Elasticsearch features used:
- **Term-level queries**: exact matches on user mentions, channel names
- **Full-text queries**: tokenized content search with relevance ranking
- **Filters**: date range, channel, sender
- **Highlighting**: return matched text with context

Indexing latency: messages typically searchable within 5 seconds of send.

**ACL enforcement**: Search results filtered server-side to channels the requesting user is a member of. Never return results from private channels the user can't access.

## Presence and Typing Indicators

These are high-frequency, low-durability signals:
- Typing indicator: user is typing in channel X
- Presence: user is active (online/away/offline)

Don't store in DB. Handle via Pub/Sub only:
- Typing: published to channel's Pub/Sub topic, forwarded to active members, expires after 5 seconds
- Presence: aggregated from WebSocket connection state, published to a user's "friends/colleagues" subscriber list

## Offline Sync

Mobile clients disconnect frequently. On reconnect:

```
1. Client sends: "I was last synced at ts=1700000000.123"
2. Server returns: all messages since that ts across user's channels
3. Client applies updates, updates local ts
```

The server queries per channel since the last_sync_ts. Efficiently answered by the primary key (workspace_id, channel_id, ts) with a range scan.

## Link Unfurling

When you paste a URL, Slack shows a preview (title, description, image). This involves:

1. Message arrives → URL detected
2. Unfurl service queues URL fetch (async, doesn't block message delivery)
3. Worker fetches URL, extracts Open Graph tags
4. Metadata stored in cache (Redis, TTL 1 hour)
5. Update message with unfurl payload → pushed to channel members

Cached to avoid re-fetching the same URL multiple times. Rate-limited to avoid being a DDoS proxy.

## Interview Tips

Key points to cover:

1. **WebSocket multiplexing** — one connection per client, gateway fan-out
2. **At-least-once with deduplication** — explain `client_msg_id` idempotency
3. **Hybrid fan-out** — push for active users, pull for offline
4. **Sharding by workspace** — locality of access pattern
5. **Search architecture** — Elasticsearch with ACL enforcement at read time

The most interesting depth area: typing indicators and presence as ephemeral Pub/Sub (not stored in DB) contrasted with messages that require durable storage.
