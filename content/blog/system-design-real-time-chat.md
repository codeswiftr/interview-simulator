---
title: "System Design: Real-Time Chat — Building WhatsApp or Slack at Scale"
description: "How to design a real-time messaging system in interviews — WebSocket connections, message delivery guarantees, online presence, group messaging, and scaling to billions of messages per day."
date: "2026-03-20"
category: "System Design"
---

# System Design: Real-Time Chat — Building WhatsApp or Slack at Scale

Real-time chat is one of the most common system design questions for senior engineers. It's a rich problem that exercises WebSocket handling, message ordering, delivery guarantees, presence systems, and storage at scale. This guide provides the design with the tradeoffs you'll need to discuss.

## Requirements

- 500M daily active users
- 100B messages per day (~1.2M messages/second peak)
- 1-to-1 messaging and group messaging (max 500 members per group)
- Message delivery confirmation (sent, delivered, read receipts)
- Online/last-seen presence
- Message history (last 30 days accessible, older archived)
- Media support (images, videos, documents)

## Core Architecture: WebSockets

Real-time chat requires persistent connections. HTTP polling (client checks every N seconds) is too slow and wasteful. **WebSockets** provide full-duplex communication over a single TCP connection.

Each user's device connects to a **Chat Server** via WebSocket. When Alice sends a message to Bob, the flow is:

1. Alice's message → Alice's Chat Server (WebSocket)
2. Chat Server → Message Queue (Kafka)
3. Message Processor → determine Bob's Chat Server
4. Bob's Chat Server → Bob's device (WebSocket)
5. Delivery receipt flows back via the same path

This architecture decouples ingestion from delivery. The message queue absorbs load spikes and provides replay capability.

## Connection Management

With 500M DAU and ~1.5 connections per user (mobile + web), you need to handle 750M concurrent WebSocket connections. No single server handles this — you need a fleet of chat servers.

**Session Service**: A Redis cluster stores the mapping `user_id → chat_server_id`. When a user connects, their assigned chat server registers: `SET user:123:server "chat-server-42"`. TTL slightly longer than heartbeat interval to auto-expire stale sessions.

When sending a message to a user:
1. Look up their chat server in the Session Service
2. If they're online (server found), push via WebSocket
3. If they're offline (no server), store in offline message queue

**Load balancing**: Use consistent hashing to distribute users across chat servers. This minimizes session migrations during server additions/removals.

## Message Storage

Messages require two storage patterns:

**Hot storage** (recent messages): Cassandra or DynamoDB. Schema: partition key = `conversation_id`, sort key = `message_id` (time-ordered). This enables efficient "load last 50 messages" queries. Write throughput scales horizontally with Cassandra's partition-level writes.

**Message IDs**: Don't use auto-increment (creates bottlenecks). Use Snowflake IDs: 64-bit integers composed of timestamp + machine ID + sequence. This gives time-ordering, uniqueness without coordination, and ~4096 messages/ms per machine.

**Cold storage**: Messages older than 30 days migrate to object storage (S3) in compressed chunks. Users rarely need old messages but they must be retrievable.

## Delivery Guarantees

WhatsApp-style delivery has three states: **Sent** (server received), **Delivered** (recipient device received), **Read** (recipient opened).

**At-least-once delivery**: The message processor retries delivery until it receives an ACK from the recipient's chat server. The recipient device ACKs receipt and stores the message ID in a local deduplication set. If the same message arrives twice (retry), it's silently dropped.

**Offline delivery**: Messages to offline users are stored in a per-user inbox (Redis list or DynamoDB table). When the user reconnects, the chat server fetches and delivers all pending messages, then subscribes to new messages.

## Group Messaging

Group messages are more complex than 1-to-1. For a group of 500 members, you can't fan-out 500 individual WebSocket pushes synchronously — that's too slow and creates head-of-line blocking.

**Fan-out strategy**:
- For small groups (< 50 members): eager fan-out — deliver to all online members immediately via their chat servers
- For large groups: lazy fan-out — write one message to group storage; clients pull when active

**Delivery receipts for groups**: Track delivery per recipient. "Delivered to 487/500 members" is a Cassandra counter or a bitmap stored with the message.

## Presence System

"Online/last-seen" presence requires handling millions of state changes per second. Users update their presence heartbeat every 30 seconds while active.

**Architecture**: Users publish heartbeats to a Presence Service. The presence service updates `user:123:last_seen` in Redis with TTL of 60 seconds. If the key expires, the user is considered offline.

**Presence notifications**: When Alice comes online, she subscribes to presence updates for her contact list. The presence service publishes state changes to a pub/sub system (Redis Pub/Sub or Kafka), and subscribers receive updates. Scale by sharding the pub/sub by user ID range.

Don't broadcast presence to all contacts for large contact lists — compute presence lazily when a conversation is opened.

## Media Handling

Media (images, video) is not sent through the chat server. The client uploads directly to object storage (S3) via a presigned URL, then sends only the media URL + metadata through the chat message. This offloads bandwidth from chat servers, which are optimized for small text payloads.

CDN fronts media storage for fast delivery. Thumbnails are generated asynchronously by a media processing service.

## Scaling Numbers

- Chat servers: 750M connections / 100K connections per server = 7,500 servers
- Message throughput: 1.2M msg/sec — Kafka cluster with 50 partitions handles this with headroom
- Session service: Redis cluster with 50M active entries is manageable (~4GB in memory)
- Message storage: 100B messages/day × 1KB average = 100TB/day hot storage (partition across Cassandra ring)

## Key Interview Points

Interviewers will probe: what happens when a chat server crashes (reconnection, session migration, in-flight message recovery), how you handle message ordering in distributed delivery, and how you scale presence for celebrity users with millions of contacts. Prepare detailed answers for each.

## Related Articles

- [System Design: Chat Application](/blog/system-design-chat-application)
- [System Design: Notification System](/blog/system-design-notification-system)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design Interview Framework](/blog/interview-system-design-framework)
