---
title: "System Design: Payment Gateway and Processing System"
description: "Design a payment gateway handling 10K transactions/second — transaction processing pipeline, idempotency, fraud detection integration, payment state machine, reconciliation, and PCI DSS compliance architecture."
date: "2026-03-20"
category: "System Design"
---

# System Design: Payment Gateway and Processing System

Payment systems are the most demanding distributed systems in terms of correctness requirements. Money must not be lost, created, or double-counted. Partial failures must not corrupt state. This design question tests whether you can reason about consistency, idempotency, and exactly-once semantics in a high-stakes context.

## Requirements

Functional: accept payments via card/bank transfer, route to payment processors, track transaction status, support refunds, handle disputes.

Non-functional: 10K transactions/second, P99 latency <500ms, 99.999% availability (5 nines = ~5 minutes downtime/year), exactly-once transaction processing, PCI DSS compliance.

## The Transaction State Machine

Every transaction follows a strict state machine. Getting this right is more important than the infrastructure architecture:

```
INITIATED → AUTHORIZING → AUTHORIZED → CAPTURING → CAPTURED → SETTLED
                ↓                           ↓             ↓
            AUTH_FAILED               CAPTURE_FAILED   REFUNDED
                                                          ↓
                                                       DISPUTED
```

Never skip states or allow backward transitions (except REFUNDED from SETTLED). Each state transition is a database write that must be atomic.

**Why explicit state machines:** Partial failures happen. If the payment processor confirms authorization but your network call drops before you receive the response, you must be able to determine the state from the processor's side (via a status check or reconciliation) and correctly advance the state.

## Idempotency — The Core Design Requirement

Every payment operation must be idempotent. If you send an authorization request and the network fails, you'll retry. Without idempotency, you may charge the customer twice.

**Idempotency key design:**
1. Client generates a unique idempotency key (UUID) before the request
2. Server checks if this key has been processed before
3. If yes: return the cached response
4. If no: process the request, store the response with the key
5. If currently processing: wait and return when complete (or return PROCESSING status)

Storage: Redis with TTL for recent keys (fast lookup), PostgreSQL for permanent record.

```sql
CREATE TABLE idempotency_keys (
    key UUID PRIMARY KEY,
    request_hash TEXT,  -- hash of request body to detect key reuse with different params
    response_body TEXT,
    response_status INT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

## Payment Processing Pipeline

```
1. Client submits payment → API Gateway → Payment Service
2. Payment Service validates request (amount, currency, method)
3. Check idempotency key — if exists, return cached response
4. Store transaction in DB with status INITIATED
5. Submit to Risk Service (fraud check, async or sync depending on latency budget)
6. Route to appropriate Payment Processor (Stripe, Adyen, Braintree)
7. Processor returns authorization → update DB to AUTHORIZED
8. Trigger capture (immediate or delayed, depending on business flow)
9. Processor confirms capture → update DB to CAPTURED
10. Async: reconciliation job confirms settlement
```

Steps 6-9 are the critical path. Failures here require careful handling.

## Handling Payment Processor Failures

**Timeout scenario:** You send an authorization request to Stripe, it times out. Did Stripe process it? Unknown. 

**Correct approach:**
1. Do NOT immediately mark as failed
2. Set status to AUTHORIZING_PENDING
3. Schedule a status check job: after N seconds, query Stripe for the status of this authorization
4. If Stripe has it: advance state accordingly
5. If Stripe doesn't have it: mark as AUTH_FAILED

**Retry with idempotency:** When retrying, use the same idempotency key with the processor. Stripe, Adyen, etc. all support idempotency keys — they won't double-charge.

## Database Design

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    idempotency_key UUID UNIQUE,
    merchant_id BIGINT NOT NULL,
    customer_id BIGINT,
    amount BIGINT NOT NULL,  -- store in cents/minor units, never float
    currency CHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL,
    processor VARCHAR(20),  -- stripe, adyen, etc.
    processor_transaction_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

**Never store amounts as float.** Floating point is inexact: `0.1 + 0.2 != 0.3`. Store all monetary amounts as integers (cents, pence, smallest currency unit).

**Optimistic locking for state transitions:**
```sql
UPDATE transactions 
SET status = 'AUTHORIZED', processor_transaction_id = $1, updated_at = NOW()
WHERE id = $2 AND status = 'AUTHORIZING';
-- If 0 rows updated, someone else already transitioned this state
```

## Reconciliation

Daily (or more frequent) reconciliation ensures your records match the processor's records.

1. Download transaction report from each processor
2. For each processor transaction, find the matching record in your DB
3. Flag mismatches: transactions in processor but not in your DB, transactions in your DB with different status, amounts that don't match

Common causes of mismatches: network failures during status updates, clock skew between systems, manual interventions by processor ops. Reconciliation catches everything that slipped through real-time processing.

## PCI DSS Compliance Architecture

Card data (PANs, CVVs) must not touch your systems if possible. Use tokenization:

1. Customer enters card data in a payment form hosted by your payment processor (not your domain)
2. Processor returns a token representing the card
3. Your system stores only the token, never the raw card data
4. To charge the card, pass the token to the processor

This dramatically reduces PCI DSS scope — you're a SAQ A merchant, not SAQ D. The processor is responsible for raw card data security.

If you must handle card data: dedicated PCI environment isolated from your main infrastructure, separate network segments, encryption in transit and at rest, strict access controls, comprehensive audit logging. Costly and complex — tokenization is far preferable.

## Scaling

At 10K TPS, the bottleneck is typically the database write path. Solutions:

**Database partitioning:** Shard by merchant_id or transaction_id. Each shard handles a subset of transactions. Use consistent hashing so a transaction always goes to the same shard.

**Write-ahead with eventual reads:** Accept the transaction write, return 200. Downstream processing (fraud check, processor submission) happens asynchronously. This reduces P99 latency from processor latency (200-500ms) to your DB write latency (<10ms). Tradeoff: the payment is not immediately confirmed.

**Read replicas:** Transaction status reads go to replicas. Writes go to primary.

## Monitoring and Alerting

Critical alerts: authorization success rate below 95% (payment processor issue), P99 latency > 1s, idempotency key collision rate above baseline (potential replay attack), reconciliation mismatches above threshold, failed state transitions (stuck transactions).


## Related Articles

- [Stripe Payment Processing Architecture](/blog/stripe-payment-processing-architecture)
- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [API Design Best Practices Guide](/blog/api-design-best-practices-guide)
