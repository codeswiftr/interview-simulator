---
title: "System Design: Notification System (Push, Email, SMS at Scale)"
description: "How to design a multi-channel notification system — fanout architecture, push notifications (APNs/FCM), email delivery, rate limiting, user preferences, and retry strategies."
date: "2026-03-20"
category: "System Design"
---

# System Design: Notification System (Push, Email, SMS at Scale)

Notification systems appear deceptively simple but contain real complexity around delivery guarantees, channel routing, rate limiting, and user preference management. Designing one well in an interview demonstrates understanding of message queues, third-party service integration, idempotency, and the practical challenges of delivering billions of messages reliably.

## Clarifying Requirements

Before designing, establish the scope:

- Which channels are in scope: push notifications (iOS/Android), email, SMS, in-app?
- What's the scale: daily notification volume (assume 100M/day for this discussion)?
- What delivery guarantee is required: at-most-once, at-least-once, exactly-once?
- Is there a latency requirement: transactional notifications (OTP, 2FA) vs. marketing (weekly digest)?
- Does the system need to handle user opt-out and notification preferences?

The answers matter significantly. An OTP delivery system has hard latency requirements and needs exactly-once delivery. A marketing email system prioritizes throughput over latency and can tolerate eventual delivery. Most real systems must handle both.

## High-Level Architecture

A notification system has four main components:

1. **Notification Service (API layer)**: Receives notification requests from upstream services (order service, payment service, social graph service). Validates inputs, looks up user preferences, and routes to the appropriate channel queues.

2. **Message Queues (per channel)**: Separate queues for push, email, and SMS. This decouples the intake rate from the delivery rate and provides backpressure when third-party providers are slow or rate-limiting.

3. **Channel Workers**: Consumers that read from queues and call third-party providers (APNs, FCM, SendGrid, Twilio).

4. **Delivery Tracking and Retry**: Records delivery status, handles failures, and implements retry logic with backoff.

## Push Notification Delivery (APNs and FCM)

Push notifications are delivered through Apple Push Notification Service (APNs) for iOS and Firebase Cloud Messaging (FCM) for Android. Both are asynchronous: you send a payload to the provider's API, and they handle delivery to the device.

Key design considerations:

**Device token management**: Users can have multiple devices. Your system needs a device token registry mapping user_id → [device_tokens], updated when users register or refresh tokens. Stale tokens (returned as errors by APNs/FCM) must be cleaned up promptly — sending to invalid tokens repeatedly is a bad actor signal.

**Payload size limits**: APNs limits payloads to 4KB; FCM is similar. For rich notifications with media, the notification payload contains a URL and the device fetches the media separately.

**Delivery semantics**: APNs and FCM both offer best-effort delivery. If a device is offline, notifications are held (APNs for up to 30 days, FCM configurable). Your system should not treat non-delivery as a hard failure.

## Email Delivery Architecture

Email at scale is handled through providers like SendGrid, Amazon SES, or Mailgun. The design concerns are different from push:

**Reputation management**: Email deliverability depends on IP reputation, domain authentication (SPF, DKIM, DMARC), and spam signal avoidance. In your design, note that transactional emails (receipts, OTPs) should use dedicated IP pools separate from marketing email — a spam complaint on marketing email shouldn't affect OTP delivery.

**Template management**: At scale, notification content is managed through a template service. The notification event carries a template_id and variable substitution data, not pre-rendered content. This enables A/B testing, localization, and content updates without code deploys.

**Unsubscribe handling**: CAN-SPAM and GDPR require honoring unsubscribes. Your system needs a suppression list and must check it before sending any email.

## SMS Delivery (Twilio, AWS SNS)

SMS is the most expensive channel per message ($0.0075–$0.05/message depending on destination) and has the strictest latency expectations (users expect SMS in seconds, not minutes). Design considerations:

- Route time-sensitive messages (2FA, OTPs) to SMS with priority queue treatment
- Maintain a fallback chain: if SMS fails, can you fall back to email or push?
- Phone number validation: invalid numbers waste money; validate E.164 format before sending

## Rate Limiting and User Preferences

**Rate limiting** is essential for avoiding notification fatigue and protecting provider SLAs:

- Per-user limits: no user should receive more than N notifications of type X per hour/day
- Global limits: stay within provider rate limits (APNs has per-connection throughput caps)
- Priority tiers: transactional notifications bypass marketing rate limits

**User preferences** add routing logic: if a user has disabled marketing push notifications but left email on, the preference service must gate delivery at the routing layer, not the channel layer.

## Retry Strategy and Idempotency

Transient failures (network timeouts, provider 5xx errors) require retry logic. Design:

- **Exponential backoff with jitter**: first retry at 1s, then 2s, 4s, 8s, up to a max retry interval
- **Dead letter queue (DLQ)**: messages that exhaust retries move to DLQ for manual inspection or alerting
- **Idempotency keys**: notification requests should carry idempotency keys so that retries don't cause duplicate delivery. Check idempotency key in a Redis store before processing.

The idempotency check is critical: without it, a retry storm during an outage can deliver the same notification dozens of times to every user.

## Delivery Tracking and Analytics

Each notification should generate delivery events: sent, delivered (where provider confirms), opened (where trackable via pixel or push callback), and failed. These events feed:

- Real-time dashboards for operations (delivery rate, failure rate by channel)
- User-facing notification history
- Upstream feedback loops (e.g., mark a marketing campaign as failed if delivery rate drops below threshold)

## What Interviewers Are Looking For

Strong candidates address the multi-channel routing architecture, the retry/idempotency problem explicitly, and rate limiting at the user level. Very strong candidates also discuss the operational complexity of provider SLA dependencies and how to design for graceful degradation when a third-party provider (SendGrid, Twilio) experiences an outage.
