# Affirm Engineering Deep Dive: Credit Infrastructure, BNPL Architecture, and What Their Interviews Actually Test

Affirm sits at the intersection of consumer lending and real-time payments infrastructure, which creates a set of engineering constraints that are genuinely unusual. A credit decision has to be made in under one second, at checkout, while the customer is actively waiting. The decision has to be right — not in a "we'll improve the model later" way, but in a way where the error rate has direct P&L consequences. And the integration surface spans thousands of merchants, from Shopify checkout flows to Walmart's payment terminals, each of which fails in its own specific way.

This post is about what those constraints produce: an engineering culture that is simultaneously more data-driven and more financially rigorous than most software companies, and what that culture means for how Affirm interviews engineers.

---

## Real-Time Credit Underwriting: A Decision in Under One Second

When a customer selects Affirm at checkout, the system has approximately 900 milliseconds to do the following: verify identity, pull credit bureau data, compute hundreds of real-time features, run the loan application through an ML scoring model, apply regulatory decisioning rules, price the loan (interest rate, term structure), and return an approval or decline.

That is not a typical ML inference problem. It is an ML inference problem with hard latency SLAs, real financial consequences for each decision, and regulatory requirements that constrain what signals can be used and how.

### Alternative Data Signals and Feature Engineering

Traditional credit scores (FICO, VantageScore) are computed monthly from tradeline data — credit cards, mortgages, auto loans. They are useful but backward-looking and systematically exclude people who are new to credit or who have thin credit files.

Affirm's underwriting uses alternative signals alongside bureau data. The engineering challenge is computing these signals in real time. Some representative categories:

**Transaction graph features.** Affirm can observe purchase patterns across its merchant network. A customer who has made twelve on-time BNPL purchases over eighteen months is a meaningfully different risk than a new customer with the same bureau score. Computing "historical repayment performance" sounds simple until you realize it requires joining across purchase history, payment event streams, and credit bureau pulls, with point-in-time correctness — you cannot use future information to evaluate a past loan.

**Merchant-specific risk signals.** The same customer buying electronics at Best Buy and buying furniture for a new apartment represent different risk profiles. Return rates, item categories, and purchase timing all correlate with eventual repayment behavior. These features require merchant-side metadata to be available at inference time.

**Application-time behavioral signals.** How long did the checkout process take? Was the same device used for multiple applications in a short window? These signals require low-latency feature stores — a Redis or Cassandra layer that aggregates streaming events and can serve features with sub-10ms latency.

### Model Serving Infrastructure

The ML pipeline is structured to meet the <300ms model inference SLA within the broader <1 second end-to-end budget. The rough allocation:

- ~100ms: identity verification and bureau data pull (external network calls, partially cached)
- ~50ms: feature retrieval from feature store (hot path, in-memory)
- ~150ms: model inference (batched features through gradient boosting or neural model)
- ~100ms: decisioning rules, regulatory checks, loan pricing
- ~50ms: remaining network and serialization overhead

The infrastructure for serving at this latency requires: feature pre-computation where possible (nightly batch jobs populate base features for known customers), a low-latency feature store for real-time deltas, model serving infrastructure that can handle the burst traffic pattern of checkout flows (not uniformly distributed — heavily correlated with merchant promotional events and holiday traffic), and circuit breakers that fail gracefully when external data providers are slow.

The critical engineering insight is that model accuracy and inference latency are in tension. Larger models with more features are more accurate but slower. Affirm's ML infrastructure must optimize across both dimensions simultaneously, which means A/B testing not just model accuracy metrics but end-to-end credit decision latency under load.

---

## The Loan Lifecycle System: From Origination to Payoff

Affirm originates installment loans — typically two, four, six, or twelve installments paid over weeks to months. The financial data model for this is more complex than it first appears.

### The Installment Loan Data Model

A loan is not just an amount and a due date. It is a schedule of cash flows with precise legal definitions. The canonical data structure needs to represent:

**The amortization schedule.** Each installment has a principal component and an interest component. The split changes over the life of the loan as the outstanding principal decreases. Affirm must store both the original schedule (as disclosed to the borrower at origination, with regulatory implications) and the live schedule (which may differ if payments are early, late, or partial).

**Payment application rules.** When a customer makes a payment, how is it applied? Typically: fees first, then interest, then principal. This ordering is not arbitrary — it is often legally mandated by state lending regulations and affects both the customer's outstanding balance and Affirm's accounting.

**Interest accrual.** Interest accrues daily on the outstanding principal balance, using the daily periodic rate (APR / 365). A payment made one day late changes the accrual calculation. These are small numbers per loan, but at scale (millions of active loans), the accounting must be exact.

```
-- Simplified loan schedule representation
CREATE TABLE loan_schedules (
    loan_id         UUID NOT NULL,
    installment_num INTEGER NOT NULL,
    due_date        DATE NOT NULL,
    principal_due   BIGINT NOT NULL,  -- stored in cents, integer arithmetic only
    interest_due    BIGINT NOT NULL,
    fee_due         BIGINT NOT NULL,
    status          TEXT NOT NULL,    -- scheduled, paid, late, settled
    paid_at         TIMESTAMPTZ,
    amount_paid     BIGINT,
    PRIMARY KEY (loan_id, installment_num)
);
```

The data type choice here is not accidental. Financial amounts are stored as integers (cents) rather than floating-point numbers because floating-point arithmetic introduces rounding errors that compound over large portfolios. $0.001 in rounding error per loan across ten million active loans is $10,000 in unexplained variance per accounting period.

### Late Payments, Collections, and Settlements

When a payment is missed, the loan servicing system must trigger a sequence of events: charge a late fee (where permitted by state law), update the loan status, trigger dunning communications, and eventually (if the loan remains unpaid) route it to collections or charge it off against Affirm's loss reserves.

Each of these state transitions must be idempotent and auditable. The loan's status history is a legal record. The event sourcing pattern is common in loan servicing systems for this reason: every state change is an immutable event appended to a log, and the current state is derived from replaying the event log. This makes it possible to audit the exact sequence of events that led to any given loan status, which is essential for regulatory examinations and dispute resolution.

Collections at Affirm's scale involve external debt collection agencies and credit bureau reporting. Both require precise, timely data feeds. A loan reported to a bureau in the wrong state (e.g., reported as charged-off when a payment was actually received) creates regulatory liability and customer harm.

---

## Merchant Integration Infrastructure: Payments at Every Checkout

Affirm's core technical challenge on the merchant side is being a reliable payment method across an enormous variety of checkout implementations. A payment method that fails 1% of the time is not competitive with credit cards. The reliability bar is closer to 99.9%.

### The Integration Surface

Affirm integrates with merchants through several layers:

**Direct API integrations.** Large merchants (Walmart, Peloton) have custom integrations where Affirm's API is called directly from the merchant's backend. These have the most flexibility but also the most custom failure modes per merchant.

**Platform plugins.** Shopify, WooCommerce, Magento, and BigCommerce each have Affirm plugins. A plugin bug affects all merchants on that platform simultaneously. The engineering tradeoff is between feature richness (which requires platform-specific code) and reliability (which favors thin integrations that change less frequently).

**Payment network integrations.** Affirm has Visa and Mastercard virtual card integrations that allow the loan to be used at any merchant that accepts those networks without a direct Affirm integration. This expands reach dramatically but adds complexity: the merchant sees a card authorization, not an Affirm transaction, which affects dispute handling and reconciliation.

### Reliability Engineering

The checkout integration path is synchronous and customer-facing. An Affirm timeout during checkout is a failed sale for the merchant and a lost customer for Affirm. The reliability engineering considerations include:

**Timeout budgets.** Every external call in the checkout path has a hard timeout. If the identity verification provider responds slowly, the system must decide whether to fail the credit decision or return a conservative fallback (often a decline). The timeout values are calibrated against real customer experience data — too short and you decline approvable customers due to transient latency; too long and you create unacceptable checkout friction.

**Graceful degradation.** Some underwriting signals are "nice to have" rather than required. If the real-time behavioral feature store is unavailable, the credit model falls back to base features from the bureau pull. The model's accuracy degrades but the system continues functioning.

**Idempotency across the merchant-Affirm boundary.** If a merchant's checkout sends the same transaction twice (due to a timeout and retry), Affirm must not originate two loans. This requires idempotency keys at the API layer, backed by a deduplication store that persists across the retry window.

---

## Fraud Prevention in BNPL: Different Vectors, Different Models

BNPL fraud is structurally different from credit card fraud, and building fraud models that do not account for this leads to systematically wrong predictions.

### Unique Fraud Vectors

**Synthetic identity fraud.** A synthetic identity is a fabricated identity that blends real PII (like a valid Social Security Number belonging to a minor or deceased person) with fabricated information. Synthetic identities often have thin credit files and look like new-to-credit consumers — which makes them attractive targets for BNPL lenders who serve the thin-file population.

Detecting synthetic identities requires signals that go beyond credit bureau data: device fingerprinting consistency, email domain age, phone number validity and tenure, and address verification patterns. The challenge is that legitimate thin-file consumers look similar on these signals to synthetic identities, so the false positive rate on aggressive detection rules is high.

**Friendly fraud and return abuse.** In traditional credit card fraud, "friendly fraud" is a cardholder disputing a legitimate charge. In BNPL, the equivalent is a customer making a purchase, receiving the goods, and then defaulting on the loan while claiming they never received the item — or, more aggressively, returning the item to the merchant for a refund while Affirm's loan remains outstanding.

This requires Affirm to have data pipelines that connect merchant return and refund events to outstanding loan balances. A refund to the customer should trigger a corresponding reduction in the loan balance. If that data feed fails or lags, it creates an arbitrage opportunity.

**Account takeover at origination.** Unlike credit cards, which take over existing accounts, BNPL account takeover often happens at loan origination — a fraudster uses a victim's PII to apply for a loan and ship goods to a third address. The shipping address mismatch signal is useful but not sufficient (people ship to work addresses, gift recipients, etc.).

### Real-Time vs. Post-Purchase Fraud Signals

Credit card fraud detection systems have trained for decades on real-time authorization signals. BNPL fraud detection has a different temporal structure.

Some signals are only observable post-purchase: whether the item was returned, whether the first payment was made, whether the shipping address received the item. These post-purchase signals are highly predictive but arrive too late to prevent the fraud.

The engineering solution is a two-stage model: a real-time approval model that operates within the <1 second checkout window, and a post-purchase risk model that continues scoring the loan for the first 30-60 days as early repayment signals arrive. The post-purchase model can trigger enhanced authentication for subsequent purchases or flag accounts for manual review, even if the initial loan was already approved.

This is a meaningful architectural difference from credit card fraud: the fraud signal and the fraud prevention action are decoupled in time.

---

## Interview Implications: What Affirm Actually Looks For

### Engineering Culture

Affirm's engineering culture has two defining characteristics that are worth internalizing before interviews.

**Financial domain depth is a genuine differentiator.** At most software companies, domain knowledge is a nice-to-have that you can pick up on the job. At Affirm, shallow domain knowledge produces bugs with real regulatory and financial consequences. Engineers who understand why integer arithmetic matters for financial calculations, why regulatory constraints shape data schema decisions, and why loan state transitions must be auditable rather than just correct — those engineers make better design decisions at every level.

**Data and ML are first-class infrastructure concerns.** The credit model is not something the data science team owns while engineering maintains the infrastructure around it. The ML pipeline, feature store, model serving latency, and A/B testing infrastructure are engineering problems that require the same rigor as payment processing reliability. Engineers who treat ML systems as a black box do not thrive at Affirm.

### System Design Questions to Prepare For

**Design a real-time credit scoring system.** This is the canonical Affirm system design question. A strong answer covers: the data flow from checkout event to credit decision, the feature store architecture (what lives in Redis vs. what requires a database join), the model serving latency budget and how it is enforced, graceful degradation when external data providers are slow, and the monitoring strategy for model performance drift.

The weak answer treats this as a generic ML serving problem. The strong answer accounts for the sub-second SLA, the regulatory requirement to log every decision with its inputs, the cold-start problem for new customers, and the feedback loop latency between loan outcomes and model retraining.

**Design a loan servicing platform.** This question tests financial data modeling and event sourcing. Cover: the installment schedule data model, how payments are applied to principal, interest, and fees, the event log that makes state transitions auditable, the data feeds to credit bureaus and collection agencies, and how the system handles the concurrent update problem (multiple payment processors attempting to update the same loan simultaneously).

The trap in this question is treating it as a generic CRUD service design problem. The strong answer addresses idempotency at every layer, the audit trail requirement, and the regulatory implications of incorrect state transitions.

### What They Are Looking For

Affirm interviewers are specifically evaluating whether you think in terms of **correctness before optimization**. In most software systems, a bug means a degraded user experience. In a loan servicing system, a bug means a customer is incorrectly reported to a credit bureau, or a payment is applied in the wrong order and the customer's balance is wrong, or a loan is originated twice. These are not the same class of problem.

The second thing they evaluate is **comfort with uncertainty quantification**. Credit decisions are probabilistic. The model is wrong some percentage of the time — that is unavoidable. What is not acceptable is being wrong in ways that are systematically biased (by demographic group, by merchant category, by time of year) that are not explained by legitimate credit risk factors. Engineers at Affirm need to understand model fairness metrics, not just accuracy metrics.

Finally, they evaluate **systems thinking across the merchant-customer-lender triangle**. Affirm's technical decisions affect three different parties simultaneously: the customer experience, the merchant conversion rate, and Affirm's own credit performance. A timeout threshold change that improves merchant checkout reliability may increase fraud; an aggressive fraud rule that protects credit performance may decline creditworthy customers. Good Affirm engineers track these second-order effects.

The preparation that actually moves the needle is: understand basic consumer lending concepts (amortization, APR, payment application order), understand how ML systems fail in production (not just how they work), and practice designing systems where correctness is a hard requirement rather than a quality preference. That combination is rarer than it should be, and it is exactly what Affirm is hiring for.
