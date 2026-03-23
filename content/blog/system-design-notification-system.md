---
title: "System Design: Notification System — Push, Email, and SMS at Scale"
description: "A comprehensive system design guide for building a multi-channel notification system. Covers architecture for push notifications, email, SMS, delivery guarantees, rate limiting, and handling failures at scale."
date: "2026-03-20"
category: "System Design"
---

# System Design: Notification System — Push, Email, and SMS at Scale

A notification system is a foundational piece of infrastructure for virtually every consumer and enterprise product. Whether alerting users to a message, a payment, a security event, or a marketing promotion, notification systems must be reliable, fast, and scalable. This is a frequent system design interview topic because it touches on messaging systems, external service integration, idempotency, and failure handling.

## Requirements and Scope

Start by clarifying scope with your interviewer:

- **Channels:** Push notifications (mobile), email, SMS? (Let's handle all three)
- **Scale:** How many notifications per day? (Assume 1 billion per day = ~12,000/second, with peaks up to 100,000/second during major events)
- **Delivery guarantees:** At-least-once? Exactly-once? (At-least-once with deduplication)
- **Latency requirements:** Real-time for critical alerts (< 1s), best-effort for marketing (minutes acceptable)
- **User preferences:** Can users opt out, set quiet hours, control per-channel settings?

## System Components

A notification system has three major concerns: **intake** (accepting notification requests from services), **processing** (routing, deduplicating, applying preferences), and **delivery** (actually sending via third-party providers).

### High-Level Architecture

```
Services (payment, messaging, etc.)
        ↓
Notification API (intake)
        ↓
Message Queue (Kafka/SQS)
        ↓
Notification Workers (per channel)
        ↓
Third-party providers:
  - APNs / FCM (push)
  - SendGrid / Mailgun (email)
  - Twilio / SNS (SMS)
```

The message queue is central: it decouples the notification request from delivery, handles backpressure, and enables retry logic.

## Notification API (Intake Layer)

The API accepts notification requests from internal services. A request looks like:

```json
{
  "user_id": "u_123",
  "type": "payment_confirmed",
  "priority": "high",
  "data": { "amount": "$42.00", "merchant": "Acme" }
}
```

The API does not directly send notifications. Instead, it:
1. Validates the request
2. Looks up user notification preferences (opt-ins, quiet hours, channel preferences)
3. Resolves user device tokens / email / phone from the User Service
4. Writes one or more notification tasks to the queue (one per channel enabled)
5. Returns 202 Accepted

By returning immediately after enqueueing, the API stays fast regardless of downstream delivery speed.

## User Preference Service

Users need control over notifications. The preference service stores:
- Channel opt-ins (push enabled, SMS disabled, etc.)
- Per-notification-type settings ("I want payment alerts but not marketing")
- Quiet hours ("don't send push between 10pm and 8am in my timezone")
- Frequency caps ("no more than 3 marketing notifications per day")

Preferences are read during intake (not delivery) so that the queue only contains notifications that should actually be sent. This avoids doing unnecessary work in the delivery layer.

**Storage:** A key-value store (Redis or DynamoDB) works well here — preferences are read-heavy, structured by user_id, and don't require complex querying.

## Message Queue Design

Use separate topics/queues per channel and per priority:

```
push-notifications-high
push-notifications-normal
email-notifications-high
email-notifications-normal
sms-notifications-high
```

This separation lets you:
- Scale workers independently per channel (SMS is more expensive than push — run fewer SMS workers)
- Apply different retry policies per channel (email can retry for hours; time-sensitive push should fail fast)
- Apply back-pressure without one slow channel blocking another

**Kafka** is a common choice for this scale — it handles millions of messages per second, has strong durability guarantees, and allows consumer groups to scale horizontally.

## Delivery Workers

Each worker consumes from its queue and delivers via the appropriate third-party provider.

### Push Notification Worker

Sends to APNs (Apple) and FCM (Google/Android). Key considerations:

- **Token management:** Device tokens expire or become invalid when users uninstall apps. Track delivery receipts and remove invalid tokens from the database.
- **Payload size limits:** APNs limits payloads to 4KB; keep notification data minimal, load full content on open
- **Silent vs visible:** Some notifications wake the app without displaying to the user (used for data sync)

### Email Worker

Uses providers like SendGrid, Mailgun, or Amazon SES. Key considerations:

- **Deliverability:** Email spam filtering is complex. Use dedicated IP reputation, proper SPF/DKIM/DMARC records
- **Template rendering:** Render HTML templates server-side; store templates in a CMS or version-controlled store
- **Unsubscribe handling:** Must honor unsubscribes immediately; CAN-SPAM and GDPR require this

### SMS Worker

Uses providers like Twilio, AWS SNS, or Vonage. Key considerations:

- **Cost:** SMS is the most expensive channel by far; rate limiting and opt-in verification are critical
- **International:** Carrier routing varies by country; some providers handle this automatically, others require country-specific configuration
- **Message length:** Standard SMS is 160 characters; longer messages are split and cost more

## Delivery Guarantees and Idempotency

Notification systems must be at-least-once: a missed payment alert is worse than a duplicate one. But duplicates should be minimized.

**Deduplication strategy:**
1. Assign a unique `notification_id` at intake time
2. Before delivering, check a deduplication cache (Redis with TTL of 24 hours): `SETNX notification_id:xyz 1 EX 86400`
3. If the key exists, skip delivery (already sent)
4. If not, proceed with delivery

This pattern handles the case where a worker crashes after sending but before acknowledging the queue message (which would cause a redelivery).

**Retry policy:**
- Push: retry 3 times with exponential backoff over 5 minutes; after that, drop (stale)
- Email: retry with backoff for up to 24 hours (email delivery can be delayed legitimately)
- SMS: retry 3–5 times; stop after 1 hour (SMS is time-sensitive)

Dead letter queues capture permanently failed notifications for monitoring and manual review.

## Rate Limiting and Throttling

Notification systems can easily overwhelm recipients if not throttled:

- **Global rate limiting:** Per-channel rate limits based on third-party provider limits (APNs, FCM have throughput limits per certificate)
- **Per-user rate limiting:** Prevent notification storms for a single user (limit to N notifications per type per day)
- **Batch sends:** For marketing notifications, spread sends over hours rather than blasting all users at once — better for deliverability and prevents provider throttling

## Monitoring and Observability

Critical metrics to track:
- **Queue depth** per channel — leading indicator of processing lag
- **Delivery success rate** per channel and provider
- **Latency distribution** from request intake to delivery
- **Bounce and unsubscribe rates** (email) — high rates hurt domain reputation
- **Invalid token rate** (push) — signals app uninstalls or token rotation issues

Alert on queue depth spikes (indicates worker failures), sudden drops in delivery success rates (provider issues), and latency breaches.

## Scaling the System

At 1B notifications/day:
- Notification API: 10–20 horizontally scaled instances behind a load balancer
- Queue: Kafka cluster with partition count sized to peak throughput (100,000/sec → need ~50 partitions per topic at 2,000 msgs/partition/sec)
- Workers: Auto-scaling groups per channel; scale based on queue depth
- Deduplication cache: Redis cluster; estimate ~100M unique notification IDs per day × 100 bytes each = ~10GB, well within Redis capacity

## Common Interview Follow-ups

**Q: How do you handle a major incident where you need to send 100M notifications at once?**
Pre-announce with gradual ramp-up; use provider batch APIs; spread across time windows to avoid throttling. Coordinate with provider support for large campaigns.

**Q: How do you ensure notifications are sent in priority order?**
Separate high/normal priority queues; workers drain high-priority queue first; can use Kafka consumer group priorities.

**Q: How would you add a new channel (e.g., WhatsApp)?**
Add a new queue topic, implement a new worker type for the WhatsApp Business API, update the preference service schema, add user preference UI. The architecture is designed for extensibility.

A well-designed notification system is invisible to users — they receive timely, relevant messages without duplicates or missed alerts. Demonstrating that you understand the reliability engineering behind that simplicity is what interviewers are looking for.

## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Real-Time Chat](/blog/system-design-real-time-chat)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [System Design Interview Framework](/blog/interview-system-design-framework)
