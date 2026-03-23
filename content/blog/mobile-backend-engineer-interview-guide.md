---
title: "Mobile Backend Engineer Interview Guide: APIs, Push Notifications & Offline Sync"
description: "Land mobile backend engineering roles — REST/gRPC API design for mobile clients, push notifications (APNs, FCM), offline-first sync, mobile-specific caching, and app store constraints."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Mobile Backend Engineer Interview Guide: APIs, Push Notifications & Offline Sync

Mobile backend engineering is a discipline that looks deceptively similar to general backend engineering on the surface. Both involve APIs, databases, and distributed systems. But the constraints are fundamentally different. Mobile clients run on devices with intermittent connectivity, limited battery, operating system restrictions on background execution, and release cycles controlled by app store review processes that can delay fixes by days or weeks. The backend engineer who serves mobile clients must internalize these constraints as first-class concerns — not afterthoughts. Interview panels at companies with serious mobile products will probe exactly this understanding.

This guide covers the topics that distinguish mobile backend engineering interviews from general backend interviews: API design optimized for mobile consumption, the push notification pipeline, offline-first sync architecture, mobile-specific caching patterns, and the operational constraints imposed by app store ecosystems.

## API Design for Mobile Clients

General-purpose REST API design advice — resource-oriented URLs, stateless requests, standard HTTP status codes — applies to mobile backends, but it is the starting point, not the destination. Mobile clients impose specific constraints that force design decisions you would not encounter when building APIs exclusively for web or service-to-service consumers.

**Bandwidth and latency sensitivity.** Mobile networks are expensive and unreliable. A mobile client on a congested cellular network may have 200ms latency and 1Mbps throughput on a good day and 1000ms latency and near-zero throughput when the user steps into an elevator. API design must minimize the number of round trips required to render a screen and minimize the payload size of each response.

The practical implication: avoid chatty APIs that require multiple sequential requests to render a single view. An API designed for a mobile home feed should return everything needed to render that feed in a single response — not require the client to fetch a list of IDs and then fan out to individual detail endpoints. This is sometimes called the Backend for Frontend (BFF) pattern. A dedicated BFF layer aggregates calls to internal services and returns a response shaped specifically for the mobile client's view model.

**GraphQL as a mobile API layer** solves the over-fetching and under-fetching problems inherent in REST when serving diverse clients. A mobile client can request exactly the fields it needs for a given screen without receiving a payload bloated with fields only the web client uses. Interview question: "When would you choose GraphQL over REST for a mobile API, and what are the operational trade-offs?" Strong answers discuss query complexity attacks (requiring query depth limits and cost analysis), caching challenges (POST-based requests bypass standard HTTP caches), and the operational overhead of schema management versus the flexibility gained.

**Pagination strategies matter for mobile.** Cursor-based pagination is strongly preferred over offset-based pagination for mobile feeds. Offset pagination has a correctness problem when items are inserted or deleted — the user sees duplicates or skips items as they scroll. Cursor-based pagination encodes position as an opaque token (typically a timestamp or primary key value from the last item returned), making it resilient to insertion and deletion. Interviewers at social, content, or e-commerce companies will ask you to compare these approaches and explain why cursor pagination is preferred for real-time feeds.

**gRPC for mobile** is increasingly common in teams that control both the client and server. gRPC uses Protocol Buffers for serialization, which produces significantly smaller payloads than JSON and enables efficient binary encoding of numeric types. gRPC also enables bidirectional streaming, which is useful for real-time features like chat or live activity updates. The interview trade-off question: gRPC requires more investment in tooling and schema management, and debugging is harder than REST because payloads are binary. REST with JSON remains easier to iterate on and inspect.

## Push Notification Architecture

Push notifications are deceptively complex. The happy path is straightforward — call an API, notification arrives on the device. The failure modes span device-level token management, platform-specific delivery semantics, rate limiting by Apple and Google, and the challenge of delivering notifications when devices are offline or the app has been killed by the OS.

**Token lifecycle management** is the foundation. Apple Push Notification service (APNs) and Firebase Cloud Messaging (FCM) both issue device tokens that identify a specific app installation on a specific device. These tokens change: when the user reinstalls the app, when the app is transferred to a new device, when the user resets their device, or when the platform rotates them for security reasons. A backend that does not handle token expiration and rotation will accumulate stale tokens, see rising delivery failure rates, and waste resources attempting to deliver to devices that no longer exist.

The correct architecture: the mobile client registers its token with your backend on every app launch. The backend stores tokens with timestamps and marks them as stale when APNs or FCM returns a specific error code (APNs returns `410 Gone`; FCM returns `registration-token-not-registered`). Stale tokens should be deleted or quarantined immediately — continued attempts to deliver to stale tokens can trigger rate limiting from the push platforms.

**Notification payload design** has platform-specific constraints. APNs payloads have a 4KB limit per notification. FCM has a similar limit. The implication: push notifications cannot carry arbitrary amounts of data. The common pattern for data-heavy notifications is to include a minimal payload (a notification type and a reference ID) and have the client fetch the full data from your API when it processes the notification. This is called a "silent push" or "data-only notification" — the notification wakes the app in the background, the app fetches fresh data, and then displays a locally constructed notification with full context.

**At-scale push infrastructure** requires routing through a notification service that handles fan-out, rate limiting, and retry logic. Sending a push to millions of devices in a single synchronous call is not possible — APNs and FCM have per-second rate limits, and a naively implemented notification blast will hit those limits and result in degraded delivery. A mature push architecture uses a queue (Kafka or SQS) to buffer notification jobs, a fleet of workers that pull from the queue and batch-send to APNs/FCM, and an observability layer that tracks delivery rates, token invalidity rates, and per-device delivery latency.

Interview question: "Design a push notification system for a news app with 50 million users that needs to deliver breaking news notifications within 30 seconds." Key components to discuss: a segmentation service that identifies which users should receive a given notification, a fan-out mechanism that creates per-user notification jobs without creating 50 million database rows synchronously, a queue-based delivery pipeline with backpressure, and a feedback loop that handles token invalidity responses.

## Offline-First Sync Architecture

Offline-first is one of the most technically demanding patterns in mobile backend engineering, and it appears frequently in interviews for roles at companies building productivity, collaboration, or field-operations applications.

The core problem: the mobile client must be usable when the device has no network connection. Changes made offline must be persisted locally, synced to the server when connectivity is restored, and merged correctly with changes that other users or devices made during the offline period.

**Conflict resolution strategies** are the hardest part. When two clients modify the same record while offline, which version wins? Three common approaches:

Last-write-wins (LWW) uses timestamps to determine which version is authoritative. Simple to implement, but clocks on mobile devices are not reliable — they can drift, be set manually, or have low resolution. LWW also discards data: if Alice edits a document offline and Bob edits the same document online, one person's changes are silently overwritten.

Operational Transformation (OT) decomposes changes into operations (insert at position 3, delete character at position 7) and transforms operations from one client against operations from another to produce a merged result. OT is complex to implement correctly and has been largely supplanted by CRDTs for new systems.

Conflict-free Replicated Data Types (CRDTs) are data structures designed so that concurrent modifications from multiple sources can always be merged deterministically without conflicts. Different CRDT types exist for different use cases: G-Counter for incrementing counters, LWW-Register for single values, Observed-Remove Set for collections. CRDTs are increasingly popular in collaborative editing tools and offline-first mobile apps.

**Sync protocol design** must address: how does the client know what has changed since its last sync? A naive approach — send everything — does not scale. The standard approach is a server-side event log or change feed, where each mutation is assigned a monotonically increasing sequence number or timestamp. The client tracks its last-seen sequence number and requests only changes above that watermark on reconnect. The server returns a bounded set of changes, and the client applies them in order.

Interview question: "A field technician app needs to work offline for 8+ hours on remote job sites. Design the sync architecture." Key elements: a local database (SQLite on-device) as the source of truth during offline periods, an operation queue that records mutations with a pending flag, a sync protocol that uploads pending mutations and downloads server-side changes on reconnect, and a conflict resolution policy appropriate to the domain (for field data, last-write-wins by timestamp may be acceptable; for financial records, it may not be).

## Mobile-Specific Caching and App Store Constraints

**HTTP caching for mobile clients** requires explicit Cache-Control headers designed with mobile bandwidth costs in mind. A mobile client that re-fetches the same user profile on every app launch is wasting battery and cellular data. Standard HTTP caching headers (`Cache-Control: max-age`, `ETag`, `Last-Modified`) work correctly in mobile HTTP clients, but APIs must explicitly set them — most mobile frameworks do not cache by default.

The ETag pattern is particularly useful for mobile: the server includes an ETag (a hash of the response content) in the response headers. On subsequent requests, the client sends `If-None-Match: [etag]`. If the content has not changed, the server returns `304 Not Modified` with no body — saving both bandwidth and server processing.

**Background fetch constraints** imposed by iOS and Android affect how your backend must behave. iOS limits how often an app can fetch data in the background, and kills background processes after a few seconds unless the app has specific background mode entitlements. This means a mobile backend cannot rely on the client to poll for updates — push notifications are often the only reliable way to wake a mobile app and trigger a data refresh.

**App store review delays** are a real operational constraint that backend engineers must account for. When an iOS or Android app ships a bug that requires a backend-side workaround, the backend must sometimes maintain compatibility with both the broken old version and the fixed new version for weeks while users update. API versioning, feature flags controllable from the backend, and kill switches (server-side configuration that disables specific client-side features) are the standard toolset for managing this.

**Certificate pinning and security** are mobile-specific API security concerns. Some mobile apps pin the server's TLS certificate — the app will refuse to connect to the server if the certificate does not match a known value. This provides strong protection against man-in-the-middle attacks but creates an operational risk: if you rotate the server certificate without coordinating a client update, pinned clients will fail to connect. Interviewers at security-conscious companies will ask how you manage certificate rotation safely with a pinned client in production.

## Behavioral Signals and Preparation

Mobile backend engineering interviews at senior levels probe whether you have experienced the failure modes firsthand, not just read about them. Your stories about past work should include: how you handled the push notification delivery failures that revealed stale token accumulation, how you designed the sync protocol that allowed field workers to operate reliably on spotty connections, or how you managed API backward compatibility across a phased mobile release.

Prepare to discuss trade-offs rather than advocating for a single correct answer. The choice between REST and gRPC, between LWW and CRDT-based conflict resolution, and between eager and lazy sync strategies all depend on product requirements, team size, and client platform constraints. Candidates who acknowledge this complexity and reason through it with the interviewer are more impressive than candidates who have memorized a single prescribed architecture.

Practice designing the following systems from scratch: a push notification pipeline for 10 million users, an offline-first to-do list that syncs across devices, and a mobile feed API designed to minimize cold-start latency. Being able to walk through these designs fluently, explain the trade-offs at each decision point, and ask the right clarifying questions is what distinguishes strong mobile backend candidates from adequate ones.
