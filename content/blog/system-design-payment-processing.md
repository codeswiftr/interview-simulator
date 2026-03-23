---
title: "System Design: Payment Processing System — Reliability, Idempotency, and Scale"
description: "A deep dive into designing a payment processing system. Covers idempotency, exactly-once semantics, reconciliation, fraud detection hooks, and how to build reliable financial infrastructure."
date: "2026-03-20"
category: "System Design"
---

# System Design: Payment Processing System — Reliability, Idempotency, and Scale

Payment systems are among the most demanding software engineering challenges. Money cannot be duplicated, lost, or corrupted. A payment system must be simultaneously reliable, consistent, fast, and auditable — often while integrating with external providers that have their own failure modes. This is a high-signal system design interview topic because it probes your understanding of data consistency, idempotency, distributed transactions, and failure recovery.

## Requirements and Scope

Define scope clearly before designing:

- **Transaction types:** Card payments, ACH transfers, or both? (Let's focus on card payments via a payment processor like Stripe or Adyen)
- **Scale:** 1 million transactions per day (~12/second average, with peak bursts to 500/second during sales events)
- **Consistency requirement:** Financial consistency is non-negotiable — we must not charge a customer twice or lose a completed transaction
- **Latency:** p99 < 3 seconds for payment completion (synchronous from user's perspective)
- **Reconciliation:** End-of-day reconciliation with the payment processor

## Core System Components

```
Client (mobile/web)
       ↓
Payment API Service
       ↓
Idempotency Layer
       ↓
Payment Processor (Stripe/Adyen) ← external
       ↓
Transaction Database
       ↓
Event Bus (Kafka)
       ↓
Downstream consumers:
  - Order Service
  - Notification Service
  - Analytics
  - Reconciliation Service
```

## The Idempotency Problem

Idempotency is the central challenge in payment engineering. Consider:

1. Client sends payment request
2. Server processes the payment and money is debited
3. Server attempts to respond to the client
4. Network failure — client never receives the response
5. Client retries the payment request

Without idempotency, the customer gets charged twice. This is catastrophic.

### Idempotency Keys

The solution is to assign every payment attempt a unique idempotency key (generated client-side):

```
POST /payments
Idempotency-Key: idem_2f8a3c9b1d4e
{
  "amount": 5000,
  "currency": "USD",
  "payment_method_id": "pm_abc123"
}
```

Server behavior:
1. Check idempotency store for this key
2. If found AND request payload matches: return cached response (whether success or failure)
3. If found AND payload differs: return 422 (different request, same key — client error)
4. If not found: process the payment, store the response under the key, return response

**Storage for idempotency records:** Redis with a TTL of 24–48 hours. Key = idempotency key, value = serialized response. Use `SETNX` (set if not exists) to handle concurrent requests with the same key:

```
SETNX idem_2f8a3c9b1d4e "processing" EX 300
```

If `SETNX` returns 0 (key already exists), another request is in flight — return 409 Conflict or wait and retry.

## Transaction State Machine

Every payment goes through defined states:

```
PENDING → PROCESSING → SUCCEEDED
                    ↘ FAILED
                    ↘ CANCELLED
```

Never skip states. The state machine must be enforced at the database level with CHECK constraints and careful application logic. A payment should never jump from PENDING directly to SUCCEEDED without passing through PROCESSING.

**Database design for transactions:**

```sql
CREATE TABLE payments (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  amount        BIGINT NOT NULL,           -- Store as cents; never use FLOAT for money
  currency      CHAR(3) NOT NULL,
  status        payment_status NOT NULL DEFAULT 'pending',
  processor_id  VARCHAR(255),              -- External reference (Stripe charge ID)
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata      JSONB
);
```

Critical notes:
- **Store amounts as integers** (cents/smallest currency unit). Never use floating-point for financial amounts.
- **`processor_id`** is the external reference returned by Stripe/Adyen — critical for reconciliation
- **`idempotency_key`** has a UNIQUE constraint — the database enforces deduplication even if the application layer has a bug

## Handling External Payment Processor Calls

Calling Stripe or Adyen is a synchronous HTTP call to an external system. Several failure modes exist:

1. **Request never reaches processor:** Retry safely (no money moved yet)
2. **Processor receives request, charges card, but response is lost:** Retrying would double-charge without idempotency
3. **Processor returns timeout:** Did the charge succeed? Unknown.

For case 3 (timeout/unknown status), the correct approach is:
- Record the payment as `PROCESSING` with the idempotency key
- Query the processor's reconciliation API (most processors support querying by your idempotency key)
- Update local state based on the reconciliation result

Never assume a timed-out payment failed — always verify with the processor.

## Exactly-Once Downstream Events

After a payment succeeds, you need to notify downstream systems (order service, notifications). But how do you avoid sending duplicate events if your service crashes after committing the transaction but before publishing the event?

**Transactional outbox pattern:**
1. In the same database transaction that marks payment as SUCCEEDED, also insert a row into an `outbox` table
2. A separate poller (or Debezium CDC) reads from the outbox and publishes to Kafka
3. Mark outbox records as published after successful Kafka acknowledgment

This ensures the event is published exactly once per committed payment. Downstream consumers should still be idempotent (Kafka delivers at-least-once), but the outbox pattern eliminates the most common source of duplicates.

## Reconciliation

End-of-day reconciliation compares your internal records with the processor's settlement report:

1. Download settlement file from processor (typically CSV/JSON via SFTP or API)
2. Match each processor transaction ID against your `processor_id` column
3. Flag discrepancies:
   - Processor shows charge, you don't have it → investigate immediately (possibly a bug in your recording logic)
   - You show SUCCEEDED, processor shows refunded → update your records
   - Amount mismatch → escalate to finance team

Reconciliation should run automatically on a schedule and alert on any discrepancies above a threshold. It's your safety net — catching any failures in the idempotency or recording logic.

## Fraud Detection Integration

A payment system needs fraud detection hooks. Rather than building ML models from scratch:

1. Before calling the processor, call a fraud scoring service (Stripe Radar, internal model, or a third-party like Kount)
2. If score > threshold: decline immediately, return 402 Payment Required with a user-facing message
3. If score in "review" range: process but flag for manual review
4. Log all fraud scores for model retraining

Fraud detection must be fast (< 200ms) to keep total payment latency acceptable.

## Handling Refunds

Refunds require careful state management:
- A SUCCEEDED payment can have zero or more refunds, up to the original amount
- Track refunds in a separate `refunds` table linked to the payment
- Sum of refunds should never exceed payment amount (enforce in application + database constraint)
- Refunds call the processor's refund API; apply the same idempotency pattern

## Scaling the Payment System

At 500 payments/second peak:
- **Payment API:** 10–20 horizontally scaled instances; stateless (all state in database)
- **Database:** PostgreSQL with synchronous replication (not async — we cannot lose committed transactions); use pgBouncer for connection pooling
- **Idempotency store:** Redis cluster; fast reads/writes, TTL-based cleanup
- **External processor:** Most processors handle your volume easily; implement circuit breakers to gracefully degrade if the processor is slow

## Key Interview Points

When discussing payment system design, emphasize these principles:

1. **Idempotency everywhere** — every operation that touches money must be idempotent
2. **Never float** — use integer arithmetic for money (BigDecimal in application code, BIGINT in database)
3. **Verify before assuming** — timeout ≠ failure; always reconcile with the source of truth
4. **Outbox pattern for events** — transactional correctness extends to downstream notifications
5. **Reconciliation as a safety net** — catches bugs that real-time guarantees miss

Payment systems are where correctness engineering meets financial responsibility. Demonstrating deep understanding of these patterns in an interview signals that you can be trusted to build the infrastructure companies depend on.
