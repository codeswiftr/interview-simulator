---
title: "System Design: Payment Processing System"
description: "How to design a payment system in system design interviews — payment lifecycle, idempotency, double-spend prevention, reconciliation, Stripe-like ledger design, and PCI-DSS considerations."
date: "2026-03-20"
category: "System Design"
---

# System Design: Payment Processing System

Payment systems are among the highest-stakes designs in software engineering. A bug in a feed algorithm produces a bad recommendation; a bug in a payment system loses real money. This reality shapes the architecture: correctness and consistency matter more than throughput optimization, and every design decision must account for failure modes that would be acceptable in other domains but catastrophic here.

## Establishing the Scope

Payment system interviews can range from a Stripe-like payment processing platform to an internal ledger to a P2P transfer system. Clarify before designing:

- What are we building: payment initiation, payment processing, ledger/accounting, or all three?
- What payment rails are in scope: cards (Visa/Mastercard), ACH, wire, real-time payments (Pix, FedNow)?
- What's the scale: transactions per second? (assume 1,000 TPS for this discussion — Stripe processes ~250M transactions/day at peak)
- What consistency model is required? (strong consistency — this is non-negotiable for payments)
- Is this a marketplace (multi-party) or direct (two-party) payment flow?

## The Payment Lifecycle

A card payment moves through these stages:

1. **Authorization**: the merchant's system sends a charge request to the payment processor; the processor authorizes with the card network (Visa/Mastercard) and issuing bank; the bank approves or declines; an authorization hold is placed
2. **Capture**: the merchant confirms the goods/service were delivered; funds are captured against the authorization hold
3. **Settlement**: card networks settle with acquiring banks on a T+1 or T+2 basis; funds transfer from issuing bank to merchant's account
4. **Reconciliation**: the payment processor reconciles settled transactions against its ledger

Understanding this lifecycle matters in interviews because it affects API design (authorize-then-capture vs. immediate charge), data models (auth records vs. capture records), and what "success" means at each stage.

## Idempotency: The Central Design Challenge

Idempotency is not a nice-to-have in payment systems — it is the foundational correctness requirement. Networks fail. Clients time out and retry. Without idempotency, retries cause double charges. With it, retrying a payment request is safe because the system recognizes a duplicate and returns the original result.

Design: every payment request carries a client-generated idempotency key (a UUID the client generates once and stores). Before processing any payment, the system checks a persistent idempotency store (Redis with persistence, or a PostgreSQL table) for this key. If found, return the stored result. If not found, process and store the result atomically.

The critical subtlety: the storage must be **atomic with the payment execution**. If you store the idempotency key *after* processing, a crash between processing and storing leaves the system in a state where a retry will double-charge. The standard solution: use a database transaction that includes both the payment record creation and the idempotency key write.

## The Ledger Design

A payment system's ledger is a double-entry accounting system. Every financial event creates at least two entries that sum to zero:

```
DR  Customer Payable    $100.00  (customer owes us)
CR  Revenue             $95.00   (our revenue)
CR  Fee Payable         $5.00    (fee owed to card network)
```

Never store balances as a mutable field. Instead, compute balances by summing ledger entries. This is immutable event sourcing applied to accounting — it makes the ledger auditable, allows point-in-time balance reconstruction, and eliminates the race condition of concurrent balance updates.

In practice, this means your ledger table has entries like:

- `entry_id`, `account_id`, `amount` (positive for credit, negative for debit), `currency`, `transaction_id`, `created_at`

Balances are derived: `SELECT SUM(amount) FROM ledger WHERE account_id = ?`

At scale, this query becomes slow — balance is cached and updated on each ledger write, with the immutable ledger serving as the source of truth for reconciliation.

## Preventing Double Spending

Double-spend prevention requires strong consistency. The approaches:

**Database-level locking**: use `SELECT FOR UPDATE` to lock the account row during the debit operation. Simple and correct, but creates contention at high throughput.

**Optimistic locking with version fields**: read the account balance and version, compute the new balance, write with a `WHERE version = ?` condition. On conflict (version changed), retry. Works well at moderate throughput, fails under high contention.

**Distributed locking (Redis SETNX)**: acquire a lock on the account ID before processing, release after commit. Adds latency overhead but decouples from the database write path.

For most interview contexts, explaining the database-level locking approach with awareness of its throughput limits is sufficient. Very strong candidates discuss the optimistic locking alternative.

## Reconciliation

Reconciliation is the process of verifying that your internal ledger matches external records (bank statements, card network settlement files). Design a reconciliation service that:

1. Receives settlement files from card networks (typically daily, in CSV/ISO 8583 format)
2. Matches settlement records against internal transaction records by payment network reference ID
3. Flags discrepancies: transactions in your ledger not in the settlement file (or vice versa)
4. Handles timing differences: T+1 settlement means today's settlement file covers yesterday's transactions

Unmatched records require human review. Design a discrepancy queue and an operations dashboard for this workflow.

## PCI-DSS Considerations

Payment card data (PANs, CVVs) is subject to PCI-DSS compliance. In an interview, you don't need to enumerate all 12 PCI requirements, but you should demonstrate awareness:

- **Never store CVVs** — ever, under any circumstances
- **Tokenize PANs**: store a token (from your payment provider or a tokenization vault) not the raw card number
- **Encryption in transit and at rest**: TLS for all payment API communication; encrypted storage for any card data
- **Scope minimization**: keep PCI-scope systems isolated; use a third-party processor (Stripe, Adyen) to handle raw card data and reduce your own PCI scope to the minimum

The cleanest answer in interviews: use a third-party processor for card data handling; your system receives a token, never raw card numbers.

## What Makes a Strong Answer

The best answers demonstrate: explicit treatment of idempotency (with the atomic-storage-and-processing requirement), the double-entry ledger model, at least one concrete double-spend prevention mechanism, and awareness of PCI scope. Candidates who draw the payment lifecycle accurately and reason through failure modes (network timeout, processor outage, bank decline) show the systems thinking that payment engineering roles require.
