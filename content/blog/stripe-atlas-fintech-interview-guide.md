# Fintech Infrastructure Interview Guide: Payments, Banking APIs, and Financial Systems

Fintech engineering interviews occupy a distinct niche between web engineering and financial systems engineering. The companies — Stripe, Plaid, Brex, Chime, Robinhood, Klarna, Affirm, and dozens of others — all have unique technical stacks, but they share a common set of engineering challenges that come up in interviews across the space. If you are preparing for a fintech role, understanding these shared challenges gives you a significant advantage over candidates who only prepared for generic system design.

## The Idempotency Requirement: Every Fintech System's Foundation

Financial systems fail. Networks partition. Clients retry. A payment that was "sent" may or may not have been received by the bank. The defining engineering challenge of fintech is handling these failures without creating double charges, double credits, or lost transactions.

The solution is idempotency. Every mutation endpoint in a financial API must be idempotent: calling it twice with the same input must produce the same result as calling it once, with no duplicate side effects.

Stripe pioneered the Idempotency-Key header for REST APIs:

```python
import stripe

# First call — charge succeeds
charge = stripe.Charge.create(
    amount=2000,
    currency="usd",
    source="tok_visa",
    idempotency_key="order_12345_attempt_1"
)

# Network failure — client retries with same key
# Second call returns the original charge, no duplicate
charge = stripe.Charge.create(
    amount=2000,
    currency="usd",
    source="tok_visa",
    idempotency_key="order_12345_attempt_1"
)
```

On the server side, idempotency is implemented via a request log: store the idempotency key and the response before completing the request. On retry, return the stored response without re-executing the operation. The challenge is ensuring atomicity: you must store the response at the same moment you complete the operation, or you can have a window where a crash between "execute" and "store" creates duplicate execution on retry. Most implementations use database transactions to make the store and execute atomic.

In interviews, fintech companies will ask you to design systems that handle this. "Design a payment processing system" almost always has idempotency as a core requirement. If you do not proactively mention it, that is a red flag.

## Ledger Architecture: Double-Entry Bookkeeping at Software Scale

Traditional bookkeeping uses double-entry accounting: every transaction must have equal debits and credits. A payment from Alice to Bob creates two ledger entries — a debit from Alice's account and a credit to Bob's. The sum of all entries must always be zero.

Fintech companies implement this as an append-only ledger:

```sql
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    account_id UUID NOT NULL,
    amount_cents BIGINT NOT NULL, -- positive = credit, negative = debit
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    idempotency_key VARCHAR(255) UNIQUE,
    metadata JSONB
);

-- Account balance = sum of all entries for that account
-- Never UPDATE or DELETE entries — only INSERT
CREATE INDEX ON ledger_entries(account_id, created_at);
```

The append-only constraint is non-negotiable. Financial regulations require a complete audit trail. You cannot delete or modify past transactions; you can only add correcting entries. This has significant implications: balance queries are aggregations over potentially large sets of rows, which is why fintech companies use materialized views, balance snapshots, and event sourcing to keep balance reads fast without sacrificing audit integrity.

## Regulatory Constraints That Shape Architecture

Fintech architecture is shaped by regulations that most engineers do not think about until they join a fintech company:

**PCI DSS**: If your system touches credit card numbers, you must comply with Payment Card Industry Data Security Standard. The practical implication is that raw card numbers must never touch your servers — they are tokenized at the browser/mobile level using a JavaScript SDK that sends the token to your server, never the number. This is why Stripe.js exists. Your servers receive tokens; Stripe's servers do the actual card number storage with their PCI-compliant infrastructure.

**KYC/AML**: Know Your Customer and Anti-Money Laundering requirements mandate that you verify user identity and monitor for suspicious transactions. This creates engineering problems: identity verification pipelines (document scanning, database checks), transaction monitoring ML models, suspicious activity report (SAR) filing workflows.

**SOC 2**: Most B2B fintech companies pursue SOC 2 certification to sell to enterprise customers. This shapes engineering practices: audit logging for all data access, access controls on production systems, change management processes.

When interviewing at fintech companies, demonstrating awareness of these constraints — not just the technical implementation — signals that you have worked in or thought seriously about regulated environments.

## Real-Time vs. Batch: The Two Modes of Financial Processing

Financial systems operate in two fundamentally different modes depending on the latency requirement:

**Real-time authorization** (milliseconds): Credit card authorizations, fraud checks at point of sale, real-time balance checks. These must respond in under 200ms or the payment network times out. They run against in-memory data stores and simplified models — there is not time for complex ML inference or database joins across large tables.

**Batch settlement** (hours): The actual movement of money happens in batch windows. ACH payments settle in 1-3 business days. Card payments settle overnight. This batch layer can do heavy processing: reconciliation, detailed fraud analysis, reporting, ledger balancing.

Understanding this two-tier architecture matters in interviews. A candidate who proposes a real-time system for a problem that can run in batch is over-engineering. A candidate who proposes batch processing for a fraud prevention system that needs millisecond decisions misunderstands the domain.

## Interview Patterns Across Fintech Companies

**Payment system design**: Almost universal. The canonical question is "design a payment processing system" or "design Venmo." Strong answers cover idempotency, ledger architecture, fraud prevention, reconciliation, and webhook delivery for payment events. Weak answers focus only on the happy path.

**Fraud detection**: "Design a real-time fraud detection system" tests your understanding of feature engineering under latency constraints, the cost of false positives (legitimate transactions declined) vs. false negatives (fraudulent transactions approved), and how you handle model updates without downtime.

**Reconciliation systems**: Less common but high signal. "How would you detect if your payment processor's records disagree with yours?" Tests understanding of distributed system inconsistencies and financial audit requirements.

**Reliability expectations**: Fintech companies have SLA requirements that are stricter than typical web companies. "Five nines" (99.999% uptime, ~5 minutes downtime/year) is common for payment infrastructure. Design discussions should address circuit breakers, graceful degradation, and runbooks for failure scenarios.

The fintech interview bar rewards engineers who think about the consequences of failure in financial terms, not just technical terms. A database outage is not just a technical problem — it is a problem where customers cannot access their money, where regulatory obligations may not be met, where audit trails may have gaps. That framing matters.
