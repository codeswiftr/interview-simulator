---
title: "System Design: Notification Service (Push, Email, SMS)"
description: "Design a notification service that delivers 100M notifications/day across push, email, and SMS channels — delivery guarantees, rate limiting, user preferences, retry logic, template management, and observability."
date: "2026-03_20"
category: "System Design"
---

# System Design: Notification Service (Push, Email, SMS)

A notification service is a frequently asked system design problem at senior engineer interviews. It appears deceptively simple but surfaces important questions about delivery guarantees, fan-out, rate limiting, and reliability. Here's the full design.

## Requirements

Functional: send notifications via push (APNs/FCM), email, and SMS; support user preferences (opt-in/opt-out per channel and category); template-based notifications; deduplication; scheduled delivery; notification history.

Non-functional: 100M notifications/day (1,200/second average, 10,000/second peak), delivery latency <5 seconds for push, <30 seconds for email/SMS, 99.5% delivery rate, at-least-once semantics with deduplication.

## High-Level Architecture

```
Event Source → Notification API → Message Queue → Channel Workers → Delivery Providers
                                       ↓
                              User Preferences Service
                              Template Service
```

**Notification API:** Receives notification requests. Validates, enriches with user preferences, applies templates, publishes to the queue. Stateless, horizontally scalable.

**Message Queue (Kafka):** Buffer between API and workers. One topic per channel: `notifications.push`, `notifications.email`, `notifications.sms`. Kafka provides durable storage if workers are slow — notifications won't be lost.

**Channel Workers:** Consumer groups per channel. Each worker pulls from its topic and calls the respective delivery provider.

**Delivery Providers:** APNs (Apple Push) and FCM (Firebase/Google Push) for mobile push. SendGrid, SES, Mailchimp for email. Twilio, Vonage, SNS for SMS.

## User Preferences

Before sending, check user preferences:
- Is the user opted into this channel? (global opt-out)
- Is the user opted into this category on this channel? (e.g., marketing emails but not SMS)
- Is the user in a quiet hours window? (schedule for their next available window)
- Is the user in a country where this channel is restricted?

Store preferences in Redis (low latency reads) with a backing PostgreSQL store for durability. Cache TTL: 5 minutes — preference changes take up to 5 minutes to propagate.

## Template Management

Notifications should use templates, not raw strings. Advantages: translations, A/B testing, change content without code deployment.

Template service: stores templates with variables (`{{user_name}}`, `{{order_total}}`). Notification API calls template service to render the final content. Support localization — template lookup by locale.

## Delivery and Retry Logic

**At-least-once delivery:** Kafka consumer commits offset only after successful delivery. If delivery fails, the message will be retried.

**Retry strategy:** Exponential backoff with jitter. First retry: 1 minute. Second: 5 minutes. Third: 30 minutes. Fourth: 2 hours. Max retries: 5. After max retries, move to dead-letter queue (DLQ).

**Dead-letter queue:** Failed notifications land here for investigation. Alerting fires when DLQ grows. Ops team can reprocess or discard.

**Deduplication:** Idempotency key = notification_id. Before delivering, check Redis for notification_id — if seen, skip. Store with TTL = 24 hours.

## Push Notification Architecture

Push is the most complex channel because of device token management:

**Device token registry:** Each user can have multiple devices. Each device has a push token (APNs device token or FCM registration ID). Tokens change when users reinstall apps or upgrade devices. When delivery fails with "invalid token," remove the token.

**APNs vs FCM:** iOS devices use APNs; Android uses FCM. Your worker must route based on device type. Both support bulk push (send to many tokens in one API call) — batch device tokens per user before sending.

**Priority:** APNs and FCM support normal and high priority. High priority wakes the device; normal is delivered when convenient. Use high priority only for time-sensitive notifications.

## Rate Limiting

Rate limiting prevents notification flooding:

**Per-user limits:** A user should not receive more than N notifications per hour per channel. Store last notification timestamps in Redis. Check before sending.

**Per-category limits:** Marketing emails: max 1/day. Transactional emails: unlimited.

**Per-provider rate limits:** Email providers have sending limits (e.g., SES: 14 emails/second on free tier). Workers respect provider limits via Redis-based rate limiters.

## Observability

Key metrics per channel:
- **Delivery rate:** Notifications sent / notifications delivered (accounting for opt-outs)
- **Delivery latency:** Time from notification request to delivery confirmation
- **Failure rate:** Failed / total (by failure type: invalid token, rate limited, provider error)
- **DLQ depth:** Alert when > threshold

Per notification type:
- **Open rate / click rate** (for marketing notifications)
- **Delivery success by notification category**

Tracing: include notification_id in all log lines. End-to-end trace from API receipt to provider confirmation.

## Scheduling

For scheduled notifications (send at 9am user's local time): at notification creation, compute UTC delivery time from user's timezone. Store in a scheduled notifications table. A scheduler service polls for notifications due in the next minute and publishes them to the queue.

For recurring notifications (weekly digest): use cron expressions stored per notification type. Scheduler generates individual notification records from the cron schedule.

## Scaling to 10K/second Peak

During peak (e.g., product launch sending to all users simultaneously):
- Queue absorbs the burst — API writes to Kafka at 10K/second
- Workers scale horizontally based on queue lag (Kubernetes HPA on consumer group lag metric)
- Email providers: batch-send up to 1,000 emails per API call to reduce overhead
- Pre-warm device token cache before a large push campaign

The key insight: queues decouple the rate of notification creation from the rate of delivery. You can create 10M notifications in 10 minutes and deliver them over 2 hours — no single component needs to handle 10M requests simultaneously.

