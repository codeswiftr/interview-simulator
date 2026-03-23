# Square / Block Software Engineer Interview Guide 2024: Process and Preparation

Square (now Block, the parent company of Square, Cash App, TIDAL, and TBD) builds payment infrastructure used by millions of merchants and consumers. Their engineering interviews blend fintech rigor with consumer product thinking — you need both technical depth and genuine interest in democratizing financial access. Here's the complete guide.

## Block's Engineering Culture

Block's mission is "economic empowerment" — building financial tools for those underserved by traditional banking. The engineering culture reflects this:

- **Inclusion in design**: Products are built for merchants who may not be tech-savvy, consumers in underbanked communities, small business owners. Accessibility and simplicity are first-class concerns.
- **Ownership mentality**: Engineers are expected to own their systems end-to-end — from design through production reliability
- **Payments expertise**: Every engineer is expected to understand the payment ecosystem (card networks, ACH, interchange)
- **Open source culture**: Block has significant open source contributions (Square APIs, Cash App libraries, developer tools)

Block operates several distinct businesses (Square, Cash App, TBD for crypto, Afterpay for BNPL), so your preparation should be calibrated to which business unit you're targeting.

## Interview Format

1. Recruiter screen (30 min)
2. Technical phone screen (60 min) — coding
3. Virtual onsite (4-5 rounds):
   - 2 coding rounds
   - 1 system design round
   - 1 behavioral round
   - Occasionally: domain-specific (payments, mobile, crypto)
4. Offer (2-3 weeks)

## Coding Rounds

Block's coding bar is solid — LeetCode medium to hard, consistent with other tier-2 companies.

**High-frequency topics:**
- Arrays, hashmaps, strings
- Trees and graphs
- Object-oriented design
- Concurrency patterns (threading, async)

**Block/Square-specific problem flavors:**

*Payment processing:*
> "Design a class that processes a list of payment transactions, handles refunds, and calculates daily settlement amounts per merchant."

Tests domain modeling, idempotency thinking, and financial arithmetic.

*Catalog management:*
> "Implement a product catalog that supports: add item, update price, apply category discounts, and calculate cart totals with stacked promotions."

Discount composition — multiple discount types, order of application, edge cases (negative totals).

*ACH batch processing:*
> "Given a list of ACH transfer requests, group them into batches of maximum N items, and return the batches in priority order (by transfer amount, descending)."

Sorting + batching — straightforward algorithm problem, but the domain framing is important.

**Critical: Money arithmetic:**
```kotlin
// WRONG: floating point
val price = 9.99
val tax = price * 0.08  // Not exactly 0.7992

// CORRECT: BigDecimal in Kotlin/Java
val price = BigDecimal("9.99")
val taxRate = BigDecimal("0.08")
val tax = price.multiply(taxRate).setScale(2, RoundingMode.HALF_UP)

// Or use integer cents
val priceCents = 999  // $9.99
val taxCents = (priceCents * 8) / 100  // Integer division, truncate (handle rounding explicitly)
```

## System Design: Payment Infrastructure

Block's system design rounds cover payment processing, merchant tools, and consumer financial products.

**Common questions:**
- Design Square's point-of-sale (POS) system
- Design Cash App's peer-to-peer payment flow
- Design a merchant analytics dashboard
- Design the dispute and chargeback management system
- Design Square's card reader offline mode

**Framework for Block system design:**

**1. Payment card network fundamentals**
Know the actors: Cardholder → Card Network (Visa/MC) → Issuing Bank → Acquiring Bank → Merchant. Square acts as both acquiring bank (for some merchants) and payment facilitator.

Interchange: the fee paid by the acquiring bank to the issuing bank per transaction (~1.5-2.5%). Square's business model: charge merchant ~2.6%, keep the margin over interchange.

**2. Idempotency is life**
Payment APIs must be idempotent. A retry should not double-charge:
```
POST /v2/payments
Idempotency-Key: merchant-generated-uuid-123
{
  "amount_money": { "amount": 1000, "currency": "USD" },
  "source_id": "card_nonce_from_client"
}
```
Same idempotency key → return original response, don't charge again.

**3. Offline mode (Square's key challenge)**
Square's card reader must work without internet:
- Store transaction locally with pending status
- Queue for sync when connectivity returns
- Handle conflicts: same card used while offline at two locations
- Void timeout: after X hours offline, transactions auto-void for fraud protection

**4. Merchant settlement**
Funds captured via card are not immediately available. Settlement timeline:
- Authorization: card network holds funds
- Capture: merchant confirms transaction (immediate for present transactions)
- Settlement: daily batch process, funds transferred to merchant's bank account (T+1 or T+2)
- Reserves: Block holds a percentage for potential chargebacks

**5. Dispute / chargeback**
Customer disputes charge → issuing bank reverses → Block receives chargeback notice → notifies merchant → merchant has 7-14 days to respond with evidence → resolution. This flow involves: automated fraud scoring, evidence collection UI, response templates, batch processing with card networks.

**Worked example: P2P payment system (Cash App)**

*Happy path*:
1. Sender enters recipient (Cashtag/phone/email) + amount
2. Balance check: sender has sufficient balance or linked payment method
3. Risk scoring: ML model rates transaction risk; high-risk routed to manual review
4. Transaction created with status PENDING; atomic debit from sender's ledger
5. Credit to recipient's ledger (or pending if recipient not yet registered)
6. Push notifications to both parties
7. Both balances updated; settlement batch includes the transaction

*Fraud considerations*:
- Velocity limits: $250/day for unverified users, $7,500/week for verified
- Suspicious patterns: burst transactions, new account + high value, device fingerprint mismatch
- Synthetic identity detection: name + SSN that doesn't match for verified users

## The Behavioral Round

**"Tell me about a time you built something that improved financial access for underserved users."**
Block's mission is economic empowerment. If you've worked on products serving underbanked communities or simplifying financial access, these stories are gold.

**"Describe a production incident and how you handled it."**
They want: structured incident response (detect → diagnose → mitigate → resolve → post-mortem). Payment outages affect real transactions.

**"How have you ensured correctness in financial or high-stakes systems?"**
Testing strategy: unit tests for calculation logic, property-based tests for edge cases, reconciliation jobs, double-entry bookkeeping.

**"Tell me about a time you improved developer experience for an internal or external API."**
Block builds developer-facing APIs (Square for Business). API quality is a first-class concern.

## Cash App vs. Square: Which Business Unit?

**Square (merchant-focused):**
- POS systems, card processing, inventory management, payroll
- Backend heavy, payments infrastructure, real-time authorization
- Java/Kotlin backend, Objective-C/Swift for Square hardware

**Cash App (consumer-focused):**
- P2P payments, direct deposit, investing, Bitcoin
- Mobile-first (iOS + Android), real-time feeds, financial products
- Kotlin/Swift for mobile, Go/Kotlin for backend

**TBD (crypto/Web3):**
- Bitcoin-focused financial services, decentralized identity
- Rust, Go, protocol work

Calibrate your preparation to your target business unit.

## Preparation Timeline

**Week 1-2: Coding + payments domain**
- 25 LeetCode medium-hard problems
- Implement an order/payment processing system with idempotency
- Learn payment network fundamentals (Visa/MC flow, authorization vs. capture)

**Week 3: System design**
- Design Cash App P2P payment and Square POS with offline mode
- Study ACH and card network settlement mechanics
- Read Square Engineering blog (developer.squareup.com/blog)

**Week 4: Behavioral + domain**
- STAR stories for reliability, financial correctness, inclusion/accessibility
- Research Block's portfolio (Square, Cash App, Afterpay, TBD) — shows genuine interest
- Practice explaining P2P fraud detection trade-offs

## What Sets Block Candidates Apart

Block hires engineers who understand that **financial access is uneven** — and that technology can change that. The best candidates have thought about why someone without a bank account uses Cash App, why a food truck owner prefers Square over a traditional POS system, and what happens when the payment infrastructure fails for these users who have fewer alternatives.

This combination of technical rigor and genuine mission alignment — not performative, but reflected in how you talk about products and trade-offs — is what distinguishes top Block candidates.
