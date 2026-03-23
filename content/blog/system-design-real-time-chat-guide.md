---
title: "System Design: Real-Time Chat Application (WhatsApp/Slack Scale)"
description: "How to design a real-time chat application in system design interviews — WebSocket vs polling, message delivery guarantees, presence, read receipts, group chat scaling, and storage."
date: "2026-03-20"
category: "System Design"
---

# System Design: Real-Time Chat Application (WhatsApp/Slack Scale)

Real-time chat is a classic system design interview question. It tests your understanding of persistent connections, message delivery guarantees, and the challenges of fan-out at scale. This guide walks through each layer of a production-grade chat system — the kind you'd see at WhatsApp, Slack, or Discord.

## Establishing the Scope

Before drawing boxes, clarify requirements with your interviewer. Key questions: How many daily active users? Is this 1:1 only or group chat? What's the max group size? Do we need message history? Are media attachments in scope?

Reasonable defaults for a senior-level question: 500M DAU, 1:1 and groups up to 500 members, 5 years of message history, text + media.

Write down your assumptions. Interviewers reward structured thinking.

## Transport: WebSocket vs Polling vs SSE

The first major decision is how clients receive messages in real time.

**Long polling** has the client send a request and the server hold it open until a message arrives. Simple to implement, but wastes connections and adds latency on message receipt.

**Server-Sent Events (SSE)** is a one-way push channel over HTTP. Good for notifications but not bidirectional — the client still needs a separate channel to send.

**WebSockets** provide a full-duplex persistent connection over a single TCP socket. This is the right choice for chat: low latency, bidirectional, efficient for high-frequency updates. WhatsApp, Slack, and Discord all use WebSockets.

Your architecture needs a fleet of **chat servers** that maintain WebSocket connections. Users connect to a chat server; messages route through it. Since a single server can hold ~50K–100K concurrent WebSocket connections, you need a connection registry (Redis or a distributed store) to track which server holds which user's connection.

## Message Delivery Guarantees

At-least-once delivery with idempotent consumption is the industry standard for chat.

The send flow: client sends a message with a client-generated **idempotency key** → chat server writes to a message queue (Kafka is common) → a delivery worker reads from the queue and fans out to recipients → the server pushes to the recipient's WebSocket if online, or queues for push notification if offline.

The client should show a "pending" state until it receives an ACK from the server. The server ACKs only after the message is durably persisted. If the client times out, it retransmits with the same idempotency key — the server deduplicates using the key.

Never use fire-and-forget for a chat message. Losing a message is a trust-breaking failure.

## Presence System

Presence (online/offline/last seen) is a high-write, high-read subsystem. With 500M users, even 10% active at once is 50M concurrent presence records.

A practical design: each chat server publishes heartbeats to **Redis pub/sub** on behalf of its connected users. A presence service subscribes and maintains a TTL-based record per user. If the heartbeat stops, the TTL expires and the user is marked offline. Clients query the presence service when opening a conversation.

Avoid fan-out storms: don't broadcast presence changes to all of a user's contacts in real time. Instead, clients poll presence lazily when they bring a conversation into focus.

## Read Receipts and Delivery Confirmation

Delivery receipts confirm the server received the message. Read receipts confirm the recipient opened it (WhatsApp's double blue check model).

Design receipts as events flowing back through the same pipeline: recipient's client sends a receipt event → chat server writes to the receipts queue → delivery worker routes the receipt back to the original sender's WebSocket.

Store receipts in a dedicated table keyed by `(message_id, user_id, receipt_type)`. This is write-heavy but reads are simple lookups.

## Group Chat and Fan-Out

Group chat introduces a fan-out problem. When a user sends a message to a group of 500 members, you need to deliver it to up to 500 WebSocket connections potentially spread across 500 different chat servers.

Two strategies:

**Write fan-out (push)**: when a message arrives, immediately enqueue 500 delivery tasks. Low read latency for clients, but high write amplification. Works for groups up to a few thousand members.

**Read fan-out (pull)**: store the message once; clients pull their group's message feed. Lower write cost, but clients need to poll or maintain a cursor. Used by Slack for large channels.

For typical group sizes (< 500), write fan-out is simpler and works well.

## Message Storage

For the message store, you have two architectural choices:

**Per-conversation storage**: messages stored in a table keyed by `(conversation_id, message_id)`. Simple, but reading a user's inbox requires querying every conversation.

**Per-user inbox**: each user has their own message table. Enables fast inbox reads but requires write fan-out to every participant's inbox. WhatsApp uses a variant of this.

Use **Cassandra** or a similar wide-column store: it handles high write throughput, supports range scans by timestamp (critical for fetching message history), and partitions well by conversation ID.

For media (images, video, audio), store files in object storage (S3 or equivalent) and store only the URL in the message record. Pre-sign URLs at fetch time for access control.

## Common Follow-Up Questions

**How do you handle offline message delivery?** Messages for offline users are queued in the database and delivered when the user reconnects. Use push notifications (APNs, FCM) for mobile wake-up.

**How do you handle network partitions or chat server failure?** The client reconnects to any available chat server. The new server fetches any undelivered messages from the message store. Client maintains a local message cursor (last seen message ID) to request only new messages.

**How would you scale to 5B users?** Shard chat servers by user ID range. Shard Cassandra by conversation ID. Use regional deployments with cross-region message routing for international conversations.

**How do you handle message ordering in groups?** Assign a monotonically increasing sequence number per conversation using a counter service (Redis INCR or a dedicated sequencer). Clients sort by sequence number, not client timestamp.

Interviewers are looking for awareness of trade-offs at each layer: you don't need to solve every problem, but you should demonstrate you know which problems exist.
