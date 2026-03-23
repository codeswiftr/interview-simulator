---
title: "System Design: Real-Time Chat Application (WhatsApp/Slack)"
description: "Design a real-time chat system for 500M users — WebSocket connections, message delivery guarantees, presence indicators, push notifications, media storage, end-to-end encryption architecture, and scaling chat servers."
date: "2026-03-20"
category: "System Design"
---

# System Design: Real-Time Chat Application (WhatsApp/Slack)

Chat system design tests your knowledge of long-lived connections, message delivery guarantees, and real-time state synchronization across massive scale. It's a common system design interview question with several tricky requirements that surface important tradeoffs.

## Requirements

Functional: one-on-one messaging, group chats (up to 500 members), message delivery status (sent/delivered/read), media sharing (images, video, documents), presence (online/offline), push notifications for offline users, message history.

Non-functional: 500M daily active users, 100B messages/day, <100ms message latency for online users, 5 nines availability for message delivery, messages stored for 7 years (compliance), end-to-end encryption (optional feature discussion).

## Connection Architecture

The fundamental challenge: servers need to push messages to clients. HTTP is request-response — clients can't receive messages unless they poll. Two main approaches:

**WebSockets:** Bidirectional persistent TCP connection between client and server. Ideal for chat — server can push messages instantly. The complication: 500M DAU with average session length of 2 hours means ~100M concurrent connections at peak.

**Long polling:** Client makes HTTP request; server holds it open until a message arrives, then responds. Simpler than WebSockets, works everywhere, but less efficient and higher latency.

**Server-Sent Events (SSE):** Server-to-client streaming over HTTP. Works for notifications but can't send client-to-server messages over the same channel.

**Recommendation:** WebSockets for mobile and desktop clients. Fall back to long polling for restricted environments.

## Chat Server Architecture

You can't handle 100M concurrent WebSocket connections on a single server. Use a chat server tier:

**Connection Servers:** Each server maintains a pool of WebSocket connections. With 10K connections per server, you need 10K servers for 100M concurrent connections. Stateful — connection state is local to the server.

**Problem:** User A (connected to server 1) sends a message to User B (connected to server 7). Server 1 doesn't have a direct connection to User B.

**Solution — Message Bus:** Chat servers communicate via a message bus (Kafka or Redis Pub/Sub). Each user's presence is registered in a routing service (Redis). When server 1 receives a message for User B, it looks up which server User B is connected to and publishes the message to that server's channel.

## Message Storage

**Hot path (recent messages):** Cassandra or DynamoDB. Optimized for high write throughput. Key design: partition by conversation ID, sort key by message timestamp. This enables: "get last N messages in conversation X" as a single partition scan.

**Cold storage (older messages):** Archive to S3/GCS after 90 days. User requests load from cold storage on scroll.

**Message ID generation:** Globally unique, roughly time-ordered (for display sorting). Use Snowflake IDs (Twitter's pattern): 41-bit timestamp + 10-bit machine ID + 12-bit sequence number = 63-bit integer, ~4096 IDs/ms/machine.

## Message Delivery Guarantees

Three-phase delivery tracking:

1. **Sent:** Server acknowledged receipt from sender (message saved to DB)
2. **Delivered:** Server pushed to recipient's device (WebSocket delivered or APNs/FCM queued)
3. **Read:** Recipient opened the conversation

Implementation: each message has a status field. Connection server sends delivery receipt when it successfully pushes to recipient. Recipient app sends read receipt when conversation is opened.

For offline recipients: message saved to DB, push notification sent via APNs (iOS) or FCM (Android). Device fetches undelivered messages when reconnecting.

**At-least-once delivery:** Better to deliver twice than not at all. Recipients deduplicate by message ID.

## Presence System

"Online" state for 500M users changes constantly. Design constraints: updates must propagate within 5 seconds, reading someone's status must be fast.

**Heartbeat-based presence:** Connected clients send heartbeat every 30 seconds. If no heartbeat within 60 seconds, mark offline. On disconnect, mark offline immediately.

**Storage:** Redis with 60-second TTL per user. Online = key exists. Setting the key on each heartbeat refreshes the TTL.

**Fan-out problem:** User X has 1000 contacts. When X goes offline, you need to notify all 1000. At scale (500M users × average 100 contacts), updating presence is expensive. Optimization: only update presence for users who are currently viewing X's contact or in a conversation with X.

## Group Chat Architecture

Groups up to 500 members. Message fan-out: one message must reach 500 group members.

**Approach 1 — Fan-out on write:** When a message is sent to a group, create 500 individual message delivery tasks. Simple, but expensive for large groups.

**Approach 2 — Fan-out on read:** Store one copy of the message. When a user reads group history, query for messages in that group ID. Efficient storage, but more complex read path.

**Hybrid:** For small groups (<50 members), fan-out on write. For large groups, fan-out on read. This is what WhatsApp reportedly does.

## Media Storage

Images and video: don't send through your chat servers. Client uploads directly to object storage (S3) and sends the URL in the message. Recipients download from the URL.

**Thumbnail generation:** For images, generate a thumbnail for preview in the chat list. For videos, generate a thumbnail and preview clip. Use a transcoding pipeline (same pattern as video streaming).

**URL signing:** Media URLs should be signed (expiring) — not publicly accessible to anyone with the URL. Sign with a time-limited token when the recipient downloads.

## End-to-End Encryption Architecture

E2E encryption means the server never sees message plaintext. Key design: public/private key pairs per device.

WhatsApp's Signal Protocol: Each device has a long-term key pair and a set of one-time prekeys. The server stores public keys. When Alice wants to message Bob, she fetches Bob's public keys from the server and establishes a shared secret without the server ever knowing it. Messages are encrypted with this shared secret.

Server role in E2E: route encrypted blobs. Store encrypted message data (can't read it). Handle key distribution.

Tradeoffs: message backup requires encrypting the backup with a user-controlled key. Key loss = data loss. Harder to implement message search, spam detection.

## Monitoring

Key metrics: message delivery latency (P50/P95/P99), connection establishment time, failed delivery rate, WebSocket reconnection rate, push notification delivery rate.

Alert on: P95 delivery latency > 500ms, failed delivery rate > 0.1%, connection server memory pressure (WebSocket connections are ~10KB each — 100M × 10KB = 1TB RAM).


## Related Articles

- [System Design: Real-Time Chat](/blog/system-design-real-time-chat)
- [System Design: Notification System](/blog/system-design-notification-system)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design Interview Framework](/blog/interview-system-design-framework)
