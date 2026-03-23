---
title: "Stripe Payment Processing Architecture"
description: "A deep dive into Stripe's payment processing system—idempotency, ledger design, charge flows, fraud detection, and the infrastructure handling billions of transactions annually."
date: "2026-03-21"
category: "System Design"
---

# Stripe Payment Processing Architecture

Stripe processes hundreds of billions of dollars in payments annually. Payment systems have uniquely strict requirements: no double charges, no lost transactions, perfect auditability, and compliance with banking regulations. This design question tests your ability to handle money—where bugs have real financial consequences.

## Requirements

**Functional:**
- Create charges (card, ACH, bank transfer)
- Manage refunds, partial refunds, disputes
- Webhooks for asynchronous payment events
- Idempotent API (no double charges)
- Real-time fraud detection

**Non-functional:**
- Exactly-once semantics for charges
- P99 API response < 500ms
- 100% transaction durability (never lose a payment record)
- PCI-DSS compliance
- 99.99% availability

## Idempotency — The Core Design Challenge

The most critical requirement in payment systems: **idempotency**. A network timeout on a charge request must not result in a double charge when the client retries.

Stripe's solution: **idempotency keys**. Client includes a unique key with each request:

```
POST /v1/charges
Idempotency-Key: customer-123-cart-456-attempt-1

{amount: 1000, currency: "usd", source: "tok_visa"}
```

Server behavior:
1. Hash the idempotency key
2. Check if key exists in idempotency store
3. If exists: return the stored response (don't process again)
4. If not: process the charge, atomically store `(key → response)` in idempotency store
5. Return response

The atomic store in step 4 uses a database transaction. The idempotency key record includes the request fingerprint (method, path, body hash) so mismatched retries are rejected.

```sql
CREATE TABLE idempotency_keys (
    key_hash      VARCHAR(64) PRIMARY KEY,
    request_hash  VARCHAR(64),  -- fingerprint of request body
    response      JSON,
    created_at    TIMESTAMP,
    locked_at     TIMESTAMP    -- concurrent request locking
);
```

## Ledger Design

Financial systems use a **double-entry ledger** — every transaction has a debit and a credit that sum to zero. This is the standard in banking and ensures integrity.

```
Charge $100 from customer:
  DEBIT  customer_payable   $100  (customer owes us)
  CREDIT stripe_escrow       $100  (funds received)

Payout to merchant:
  DEBIT  stripe_escrow      $100  (releasing funds)
  CREDIT merchant_balance    $100  (merchant receives)
```

Each entry is immutable. Never UPDATE a ledger row — INSERT a new reversal entry. This creates a complete audit trail.

```sql
CREATE TABLE ledger_entries (
    entry_id       UUID PRIMARY KEY,
    transaction_id UUID,
    account_id     VARCHAR(64),
    amount         BIGINT,  -- in cents, never DECIMAL for money
    currency       CHAR(3),
    entry_type     ENUM('debit', 'credit'),
    created_at     TIMESTAMP,
    description    VARCHAR(256)
);

-- Balance is always computed:
SELECT SUM(CASE entry_type WHEN 'credit' THEN amount ELSE -amount END)
FROM ledger_entries
WHERE account_id = ?
```

**Always store money as integers (cents).** Floating-point arithmetic is forbidden for financial calculations.

## Charge Flow

```
1. API receives charge request
2. Idempotency check (< 1ms Redis lookup)
3. Validate card token, merchant permissions
4. Risk/fraud scoring (< 50ms ML model)
5. Network submission to card network (Visa/Mastercard/etc.)
   → Authorization request to issuing bank
   → Authorization response (approve/decline) (~200ms)
6. Write to ledger (atomic transaction)
7. Store idempotency response
8. Return to caller
9. Async: emit webhook event, update reporting tables
```

The network submission (step 5) is the slowest and externally dependent step. Stripe acts as a Payment Service Provider (PSP), interfacing with card networks via proprietary gateway protocols (ISO 8583 messages).

## Handling Network Failures

Between step 5 and 6: the card was authorized, but writing to ledger failed. What happens?

This is the **dual-write problem**. Solutions:

**Outbox pattern**: Write the ledger entry and an outbox record in the same transaction. A background worker processes the outbox and confirms/voids the authorization if ledger commit failed.

**Compensation**: If ledger write fails, immediately send a void/reversal to the card network. The authorization is released. Return an error to the caller (they retry with same idempotency key, which starts fresh).

In practice: Stripe uses transaction-level retries with database-level durability guarantees. The outbox approach handles the edge case of process crashes.

## Fraud Detection

Real-time fraud scoring happens before network submission (step 4). ML model features:

- Card velocity: how many charges on this card in last 24h?
- Merchant profile: new merchant vs established?
- Amount distribution: unusual amount for this merchant category?
- Device fingerprint: known fraudulent device?
- IP geolocation: card billing address vs IP location mismatch?
- Behavioral signals: how fast did user fill out form?

Model outputs a risk score. High-risk: decline immediately. Medium-risk: route through 3D Secure (additional authentication). Low-risk: proceed.

Rules engine handles known fraud patterns (block specific card bins, IPs) without ML latency. ML handles novel patterns.

## Webhooks

Stripe's webhook system delivers events to merchants asynchronously. Challenges:

- Must deliver at-least-once (no lost events)
- Respect merchant's endpoint reliability (back off on failures)
- Order matters (charge.succeeded before charge.refunded)

Architecture:
1. Event emitted to internal Kafka topic
2. Webhook worker consumes, delivers to merchant endpoint
3. On failure (timeout, 5xx): exponential backoff retry for 3 days
4. Merchant can replay events via dashboard

Webhook signing: each delivery is HMAC-signed with merchant's secret. Merchants verify the signature to reject spoofed deliveries.

## PCI Compliance

Card data (PAN, CVV) must be handled in a PCI-DSS environment:
- Card numbers stored encrypted (vault service, separate network segment)
- CVV never stored (network rules prohibit it)
- TLS everywhere, certificate pinning on mobile SDKs
- Network segmentation: card vault completely isolated from business logic
- Audit logging: every access to card data is logged

Stripe's hosted fields (card element JS) means card data never touches the merchant's server — it goes directly from browser to Stripe's vault.

## Interview Tips

Payment systems interviews reward depth in:
1. **Idempotency** — the dual-write problem and the idempotency key pattern
2. **Double-entry ledger** — money as integers, immutable entries
3. **Charge flow** — the authorization → capture two-step
4. **Fraud detection** — rules engine + ML, pre-auth timing
5. **Exactly-once semantics** — the hardest distributed systems problem in finance

Show that you understand why correctness matters more than performance here, and what "eventual consistency" means in a financial context (it means "we'll reconcile tonight" — not "we don't know if the charge happened").

## Related Articles

- [Stripe Interview Guide](/blog/stripe-interview-guide)
- [System Design: Payment Gateway](/blog/system-design-payment-gateway)
- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [API Design Best Practices Guide](/blog/api-design-best-practices-guide)
