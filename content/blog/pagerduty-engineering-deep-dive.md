# PagerDuty Engineering Deep Dive: Incident Management Infrastructure

PagerDuty sits at one of the most demanding intersections in software infrastructure: it must be reliably available precisely when everything else is broken. The system that alerts engineers to production incidents cannot itself become a production incident. Understanding how PagerDuty achieves this, and the engineering decisions behind it, is essential preparation for anyone interviewing there or for any system design interview touching reliability, alerting, or distributed systems.

## The Alert Routing Engine: From Noise to Signal

PagerDuty ingests millions of monitoring alerts per day from tools like Datadog, CloudWatch, Prometheus, Nagios, and hundreds of other integrations. The first engineering challenge is deduplication: a single production incident — say, a database that goes down — might generate ten thousand alerts in minutes as every monitoring tool, every health check, and every dependent service fires. Without deduplication, the on-call engineer receives ten thousand pages instead of one.

PagerDuty's deduplication logic operates on a concept called the dedup key: a deterministic string derived from the alert source, alert class, and affected component. All alerts sharing a dedup key within an active incident window are collapsed into a single incident record. The dedup key is set either by the alerting tool (which knows what it is monitoring) or by PagerDuty's Event Rules engine, which applies regex and field-matching rules to normalize keys across heterogeneous alert sources.

The routing engine then applies escalation policies to determine who to notify. An escalation policy is a directed graph: alert the primary on-call engineer; if no acknowledgment within N minutes, escalate to the secondary; if still unacknowledged, escalate to the team lead; ultimately escalate to the support queue. Executing this graph reliably requires a durable, fault-tolerant workflow engine that survives restarts, handles clock skew, and guarantees that escalations fire even when individual nodes fail.

The engineering of this escalation execution engine is a classic distributed systems problem. PagerDuty uses a persistent timer queue backed by durable storage: each escalation step is scheduled as a future job. When a job fires, the system checks the incident state — if acknowledged, the escalation chain terminates; if not, the next escalation step fires and a new timer is scheduled. The correctness requirement is strict: a missed escalation in a real production incident has real consequences.

## On-Call Scheduling at Scale: Time Zones, Fairness, and Human Complexity

Managing on-call rotations for thousands of engineering teams is a hard scheduling problem. A rotation must distribute on-call burden fairly across team members while respecting holidays, time zone differences between distributed teams, individual unavailability windows, and business continuity requirements like ensuring a minimum number of on-call engineers at all times.

PagerDuty's scheduling algorithm treats the calendar as a constraint satisfaction problem. A schedule is a mapping from time windows to on-call engineers. Rotation layers allow teams to define separate schedules for primary, secondary, and tertiary coverage. Override layers allow individual engineers to block out vacation or swap shifts. The algorithm must produce a schedule that is at all times fully covered while respecting all constraints.

Time zone handling is particularly subtle. A rotation defined as "9am to 9pm local time" for a globally distributed team requires the system to track each engineer's local time zone and correctly compute handoff moments in UTC for comparison with alert timestamps. Daylight saving transitions — which happen at different times in the US, EU, and other regions — must be handled without creating coverage gaps.

The calendar integration with Google Calendar and Outlook is bidirectional: on-call schedules export to personal calendars, and personal calendar events (PTO, holidays) can be imported to auto-generate schedule overrides. The integration requires handling OAuth2 token refresh, rate limiting by calendar providers, and idempotent event creation (so that schedule recalculations do not create duplicate calendar events).

## Event Intelligence: Machine Learning for Alert Correlation

PagerDuty's Event Intelligence layer uses ML to group related alerts into incidents automatically, beyond what rule-based dedup keys can achieve. The problem it solves is alert storms: a cascading failure might generate alerts from dozens of different monitoring sources, each describing a different symptom of the same underlying cause. A database failure generates alerts from the database monitor, from the application health check, from the API latency monitor, from the queue depth monitor, and from the downstream service dependency check. These alerts have different dedup keys but represent a single incident.

Training the grouping model required a large corpus of labeled historical data: alert sequences where engineers had manually consolidated multiple alerts into a single incident. PagerDuty has a significant proprietary data advantage here — years of real incident data across thousands of customers provides training signal that no new entrant can easily replicate.

The model must balance two competing error types. False negatives — failing to group related alerts — result in alert fatigue: the on-call engineer receives multiple pages for the same incident. False positives — incorrectly grouping unrelated alerts — result in merged incidents that obscure distinct problems. In practice, PagerDuty calibrates toward lower false positive rates, because merging distinct incidents has higher operational cost than receiving a few extra pages.

The inference path for alert grouping must operate in near-real-time: an alert received at 2am needs to be grouped with its related alerts within seconds, before the engineer is notified, not minutes later. This requires a low-latency serving infrastructure with in-memory model state, not a batch pipeline.

## The Notification Delivery Pipeline: Guaranteed Delivery Under Failure

PagerDuty's notification pipeline must deliver pages via SMS, voice call, push notification, and email with strong delivery guarantees. "Guaranteed delivery" is a non-trivial engineering claim when the delivery channels themselves are unreliable.

SMS delivery fails for predictable reasons: carrier routing issues, number portability lag, message filtering by spam heuristics, and international routing failures. PagerDuty's SMS infrastructure maintains relationships with multiple SMS aggregators and implements carrier failover: if a message sent through primary carrier A is not confirmed delivered within a timeout window, it retries through carrier B. The confirmation signal comes from delivery receipts, which are themselves unreliable (not all carriers send them accurately), requiring heuristic inference about delivery status.

Voice call delivery is used as a high-urgency fallback. When a critical alert fires and SMS delivery cannot be confirmed, PagerDuty's system initiates a phone call with a synthesized voice message reading the alert details. Voice calls cut through DND mode on most phones, making them the last-resort channel before escalating to the next person in the escalation policy.

The SLA for notification delivery — the time from alert receipt to first engineer notification — is a core product metric. PagerDuty publishes uptime SLAs for its notification infrastructure and maintains independent monitoring of its own delivery pipeline. The retry and escalation logic must account for the delivery pipeline's own latency: an acknowledgment timeout must be long enough that engineers receive and have time to respond, but short enough that escalations fire promptly when an engineer is genuinely unavailable.

## What PagerDuty Engineering Interviews Actually Test

PagerDuty's engineering culture is deeply shaped by its product domain. Engineers who work on reliability infrastructure develop strong opinions about fault tolerance, observability, and graceful degradation. The interview process reflects this: interviewers are looking for candidates who reason carefully about failure modes, not just happy-path behavior.

Classic system design questions at PagerDuty map directly to the infrastructure described above. "Design an on-call notification system" requires you to reason about alert deduplication, escalation policy execution, multi-channel notification with carrier failover, and acknowledgment tracking. "Design an alert deduplication system that handles 10,000 alerts per second" requires you to think about dedup key generation, windowing semantics, and the storage layer for active incident state. "Design a scheduling system for on-call rotations" requires constraint satisfaction thinking, time zone handling, and calendar integration.

PagerDuty also tests for reliability-first thinking in coding interviews. They want to see candidates who handle error cases explicitly, who think about retry semantics and idempotency, and who design APIs that behave correctly under partial failure. A candidate who writes a notification delivery function without considering what happens if the first delivery attempt fails will not perform well.

The operational experience that PagerDuty engineers accumulate — being on-call for the on-call system — creates a distinctive engineering culture. Candidates who can demonstrate genuine understanding of reliability engineering, not just the ability to recite CAP theorem, will stand out. Interview Simulator's PagerDuty-specific question sets are built to test exactly that depth.
