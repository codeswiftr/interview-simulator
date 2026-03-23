# Square/Block Engineering Deep Dive: Payments, Bitcoin, and the Builder Culture

Square started as a company that gave a small white card reader to your local farmer's market vendor and let them swipe a credit card with an iPhone. That origin story still defines who Block hires, what they value, and what the engineering problems actually look like day to day. If you are interviewing at Block, you need to understand that you are not interviewing at a typical FAANG-adjacent company. This is a company with a genuine ideological north star — financial inclusion — and increasingly, a bet that Bitcoin is how you get there globally.

This guide covers the technical substance you need to prepare, the cultural expectations that differentiate Block from its peers, and a candid look at what thriving there actually requires.

---

## The Square to Block Rebrand and Why It Matters

In December 2021, Square Inc. renamed itself Block. This was not a cosmetic rebrand. Jack Dorsey was signaling that Square the point-of-sale company was now just one business unit inside a broader ecosystem, and that the company's real ambition was much larger and stranger than payments.

The Block umbrella now contains four distinct businesses:

**Square** handles merchant-facing services: the physical card readers, the software POS, payroll, inventory, appointments, and the banking products for small businesses. This is the mature, profitable core.

**Cash App** is where the growth story lives. What began as a simple peer-to-peer payment app has become a full financial services platform for consumers — with a Visa debit card (the Cash Card), Bitcoin buying and selling, stock investing, tax filing, and direct deposit. As of 2023, Cash App generated more gross profit than the Square seller ecosystem.

**Tidal** is the music streaming acquisition that Dorsey has positioned as a tool for artist financial empowerment. It is the most unusual piece of the portfolio and arguably the one least integrated into the engineering culture, but it exists as proof of the broader "creator economy" thesis.

**TBD** (legally TBD54566975) is the most technically ambitious and most speculative piece. It is a standalone business unit building open-source protocols for decentralized identity and financial services on top of Bitcoin. The flagship project is Web5 — Dorsey's explicit rejection of Ethereum-based Web3 in favor of a Bitcoin-native decentralized web. TBD is small, moves fast, publishes everything openly, and operates more like a protocol research organization than a product team.

For engineering candidates, this structure matters because the role you interview for sits inside one of these units, and the technical culture differs meaningfully between them. A Square seller ecosystem engineer is dealing with POS hardware reliability, offline-capable sync, and the messy reality of card-present payments. A Cash App engineer is dealing with hyper-growth consumer fintech, regulatory compliance, and real-time money movement at scale. A TBD engineer is writing Rust and Go against nascent Bitcoin Layer 2 protocols with no existing playbook.

---

## Cash App: The Growth Engine

Cash App is one of the most remarkable product trajectories in recent fintech history. It grew from a simple Venmo competitor into a primary financial account for tens of millions of Americans, many of whom are underbanked or unbanked. That is not an accident — it is the product of deliberate design choices targeting users that traditional banks treat poorly.

The technical surface area of Cash App is broad:

**P2P payments** remain the core interaction: send money to a $cashtag, request money, split bills. The back-end requirements are deceptively complex — instant settlement expectations, fraud detection on every transaction, AML screening, and the need to handle failure gracefully when a bank transfer bounces three days after the user spent the balance.

**Cash Card** is a Visa debit card issued by Sutton Bank and powered by Cash App's ledger. When a user taps their Cash Card at a merchant, the transaction flows through Visa's network, gets routed to Sutton Bank, and then Cash App's system authorizes or declines it in real time. The engineering challenge is sub-100ms authorization decisions that incorporate fraud signals, available balance, and any active Cash Card boosts (their loyalty/discount system).

**Bitcoin** is where Cash App diverged most sharply from competitors. Cash App users can buy, sell, and receive Bitcoin. They can also use Lightning Network for fast low-fee Bitcoin payments. Block mines Bitcoin at industrial scale through its mining business unit, and Dorsey has said explicitly that he would work on Bitcoin and nothing else if he were not running Block. Bitcoin is not a feature at Cash App — it is a strategic commitment.

**Investing** lets users buy fractional shares of stocks and ETFs. This launched in 2019 and remains a secondary product to the payments and Bitcoin features, but it adds complexity to the regulatory surface area Cash App must manage.

---

## Square POS: Hardware and Software Co-Design

The Square seller products represent a different class of engineering challenge than consumer fintech. When you are building POS hardware and software together, the failure modes are different and the tolerances are tighter in specific ways.

The original Square reader used the headphone jack to transmit audio-encoded card data. That was clever and fragile. The modern Square hardware stack is substantially more sophisticated:

**EMV chip readers** must implement the full EMV protocol, which is a state machine defined by specifications from Europay, Mastercard, and Visa. An EMV transaction involves multiple round trips between the card and the terminal, cryptographic verification of the card, and finally authorization from the issuing bank. Getting this wrong means either accepting fraudulent transactions (liability shifts to the merchant) or falsely declining legitimate ones (lost sales).

**NFC contactless payments** add Apple Pay, Google Pay, and contactless card support. The NFC stack involves reading the card's NDEF data, handling different contactless protocols (Visa's qVSDC, Mastercard's MCCS), and fitting within the tight timing windows that contactless specifications require.

**Offline capability** is a hard requirement for a POS system because merchants lose internet connectivity. Square terminals must queue transactions, apply risk controls for offline card-present transactions, and reconcile when connectivity returns. The sync model here is non-trivial.

**Bluetooth pairing and firmware updates** add device management complexity. Square ships new hardware versions regularly, and the software that runs on those readers must be updated reliably across millions of devices in the field.

The POS engineering team sits at the intersection of embedded firmware, mobile SDKs (Swift for iOS, Kotlin for Android), and cloud backend services. It is a rare combination that attracts engineers who find the hardware-software boundary genuinely interesting.

---

## Bitcoin, TBD, and the Ideological Bet

You cannot understand Block's engineering culture without engaging seriously with the Bitcoin conviction. Dorsey is not a Bitcoin speculator. He has publicly said he believes Bitcoin is the most important thing happening in his lifetime. He donated the equivalent of 28% of his Square stock to a fund for pandemic relief — in Bitcoin. He donated 10% of his Block equity in a Bitcoin endowment for Black communities.

The TBD unit is the engineering expression of that conviction. Web5 is built on the Decentralized Identifiers (DID) standard and Verifiable Credentials, using Bitcoin as the anchoring layer for identity rather than a centralized authority. The technical work includes:

- `tbDEX`: an open-source liquidity protocol for exchanging currencies and assets without intermediaries
- Decentralized Web Nodes (DWN): a personal data store model that lets users own their data
- DID methods anchored to the Bitcoin blockchain via the ION protocol

This is genuinely speculative engineering. Some of it will not work, or will not achieve adoption, or will be superseded by alternatives. Block is making this bet because they believe that if decentralized identity and financial rails succeed, Block should have built the infrastructure — not because it is a guaranteed business outcome.

For engineering candidates interested in TBD, the relevant background is: Bitcoin Layer 2 protocols, peer-to-peer networking, cryptographic identity, and the practical problems of decentralized systems (key management, recovery, Sybil resistance). It is a different interview track than Square or Cash App.

---

## The Technical Stack

Block does not have a single uniform stack. The different business units have different histories and different technical choices, but there are dominant patterns:

**Backend services** are primarily Kotlin and Java on the JVM, running as microservices on AWS. The older Square infrastructure has significant Ruby on Rails legacy code, particularly in the merchant-facing web products. Go is used for newer, high-throughput services, particularly where latency matters.

**Mobile** is Swift on iOS and Kotlin on Android. Square's hardware SDK has native iOS and Android implementations. Cash App runs separate iOS and Android apps with significant feature parity requirements.

**Data infrastructure** uses BigQuery and Redshift for analytics, Kafka for event streaming, and a mix of PostgreSQL, MySQL, and distributed stores depending on the service. The payments domain requires durable, strongly consistent storage for ledger operations — you will not find eventual consistency in the places that matter for money movement.

**Fraud and risk systems** are machine learning models running on real-time feature pipelines. The Cash Card authorization path processes transactions under 100ms budget, which constrains what ML inference is practical inline versus what gets deferred to asynchronous review.

**Bitcoin and crypto** infrastructure uses Go heavily. TBD publishes most of its protocol work as open source, so you can review the actual code at github.com/TBD54566975.

---

## System Design: P2P Payment System

A common system design question at Block is designing Cash App's P2P payment flow. Here is the architecture worth walking through in an interview.

**Core entities:**
- User account with an associated ledger
- Bank account linked via ACH
- Cash App balance (stored value)
- Transaction record

**The happy path** for sending $50 to a friend:
1. Sender initiates transfer via mobile client
2. Backend validates: sender identity verified, sufficient balance or linked bank, recipient exists
3. Compliance check: AML screening against OFAC lists, velocity checks (how many transactions today/this week)
4. Ledger debit for sender, ledger credit for recipient — this must be atomic
5. Push notification to recipient
6. If recipient's balance exceeds threshold or they request it, initiate ACH pull to their bank

**The hard parts:**

**Idempotency** is critical. Mobile networks drop connections. Users double-tap. Your payment endpoint must be idempotent — sending the same request twice must not result in two debits. The standard approach is client-generated idempotency keys stored in a database with the transaction state.

**Regulatory compliance** is not optional. Cash App holds money transmission licenses in most US states plus federal registration with FinCEN as a Money Services Business (MSB). This means:
- KYC (Know Your Customer): identity verification for users above threshold transaction volumes
- AML (Anti-Money Laundering): monitoring for structuring, unusual velocity, high-risk counterparties
- SAR filing: Suspicious Activity Reports to FinCEN when thresholds are met
- Transaction record retention: 5 years minimum

**Bank transfer reliability** is the messiest layer. ACH is a batch system. Standard ACH takes 1-3 business days. Instant bank transfers (which Cash App charges for) use RTP (Real-Time Payments) or FedNow rails where available, falling back to push-to-debit for faster settlement. When a bank transfer fails (insufficient funds, closed account), you have already credited the recipient — you need to handle that debit recovery gracefully without penalizing an innocent recipient.

**Fraud detection** on P2P is uniquely difficult because unlike card fraud, you often cannot reverse a completed P2P transfer. The sender voluntarily authorized it — even if they were socially engineered into it. Block's fraud models must balance false positive rate (blocking legitimate transactions, which destroys product experience) against false negative rate (allowing fraud).

---

## Kotlin Code Example: Payment Validation

Here is the shape of a payment validation service in idiomatic Kotlin:

```kotlin
data class PaymentRequest(
    val senderId: String,
    val recipientId: String,
    val amountCents: Long,
    val idempotencyKey: String,
    val currency: Currency = Currency.USD
)

sealed class PaymentResult {
    data class Success(val transactionId: String) : PaymentResult()
    data class Failed(val reason: FailureReason) : PaymentResult()
}

enum class FailureReason {
    INSUFFICIENT_BALANCE,
    RECIPIENT_NOT_FOUND,
    COMPLIANCE_BLOCKED,
    DAILY_LIMIT_EXCEEDED,
    DUPLICATE_REQUEST
}

class PaymentService(
    private val ledgerRepository: LedgerRepository,
    private val userRepository: UserRepository,
    private val complianceService: ComplianceService,
    private val idempotencyStore: IdempotencyStore
) {

    suspend fun sendPayment(request: PaymentRequest): PaymentResult {
        // Check idempotency first — return existing result if this key was seen
        idempotencyStore.get(request.idempotencyKey)?.let { existingResult ->
            return existingResult
        }

        val sender = userRepository.findById(request.senderId)
            ?: return PaymentResult.Failed(FailureReason.RECIPIENT_NOT_FOUND)

        val recipient = userRepository.findById(request.recipientId)
            ?: return PaymentResult.Failed(FailureReason.RECIPIENT_NOT_FOUND)

        // Validate available balance
        val balance = ledgerRepository.getAvailableBalance(request.senderId)
        if (balance < request.amountCents) {
            return PaymentResult.Failed(FailureReason.INSUFFICIENT_BALANCE)
        }

        // Check daily send limit
        val dailySent = ledgerRepository.getDailySentTotal(
            userId = request.senderId,
            date = LocalDate.now()
        )
        if (dailySent + request.amountCents > sender.dailySendLimitCents) {
            return PaymentResult.Failed(FailureReason.DAILY_LIMIT_EXCEEDED)
        }

        // AML / compliance screening
        val complianceDecision = complianceService.evaluate(
            senderId = request.senderId,
            recipientId = request.recipientId,
            amountCents = request.amountCents
        )
        if (complianceDecision == ComplianceDecision.BLOCK) {
            return PaymentResult.Failed(FailureReason.COMPLIANCE_BLOCKED)
        }

        // Atomic ledger operation
        val transactionId = ledgerRepository.transferAtomic(
            fromUserId = request.senderId,
            toUserId = request.recipientId,
            amountCents = request.amountCents,
            idempotencyKey = request.idempotencyKey
        )

        val result = PaymentResult.Success(transactionId)
        idempotencyStore.set(request.idempotencyKey, result)
        return result
    }
}
```

The key interview discussion points here: why `suspend` (Kotlin coroutines for non-blocking I/O), why the idempotency check is first (before any database writes), why the ledger transfer is a single atomic operation, and how you would handle the compliance service being slow or unavailable.

---

## The Interview Process

Block's interview process is fairly standard for a large tech company in structure, but the specific calibration differs from FAANG:

**Coding rounds** tend toward medium to hard difficulty. They test standard algorithmic competency — graph traversal, dynamic programming, string manipulation — but the framing is often in a payments or financial context. Expect to discuss time and space complexity and to write clean, compilable code.

**System design** is where Block differentiates most. They want to see that you understand distributed systems in the context of financial correctness. The classic pitfalls: not mentioning idempotency, treating money movement as eventually consistent, ignoring regulatory requirements. Mentioning FinCEN compliance, money transmission licensing, or AML requirements will distinguish you from candidates who treat the problem as a generic distributed systems exercise.

**Behavioral interviews** use the "builder culture" lens. Block wants engineers who identify with making things work for people who have been underserved. The Stripe interview culture rewards intellectual precision; the Google culture rewards scale thinking; Block rewards genuine mission identification. That does not mean you have to perform enthusiasm you do not feel, but it does mean that "I want to work on interesting technical problems" as a primary motivation is less resonant here than "I want to make financial tools accessible to people who currently pay 10% to cash a paycheck."

**Bitcoin questions** may or may not appear depending on the team, but familiarity with Bitcoin's basics — how transactions work, what the Lightning Network does, why decentralized identity is hard — will serve you well and may come up in conversation even when not formally assessed.

---

## Compensation

Block's total compensation is competitive with senior roles at comparably-sized tech companies, but not at the top of the FAANG range. The equity component is meaningful and tied to Block's stock price, which has been significantly more volatile than a company like Apple or Google given its fintech exposure and the correlation between Bitcoin sentiment and BSTK performance.

One notable cultural signal: Jack Dorsey took his salary down to $1 as CEO of Square in 2020 and publicly committed to donating significant portions of his equity to charitable causes. He has said publicly that wealth accumulation is not his goal. This sets a cultural tone around compensation that is different from companies where the leadership visibly optimizes for personal wealth. Block attracts engineers who are motivated by the mission and willing to accept somewhat more salary volatility in exchange for working on something they believe in.

---

## Who Thrives at Block

Block is a good fit for a specific kind of engineer, and a mediocre fit for others. Being honest about this will help you decide whether to prioritize this opportunity or treat it as a hedge.

You will thrive at Block if:
- You are genuinely interested in financial inclusion as a problem space, not just as a resume line
- You are comfortable with ideologically motivated technical bets (Bitcoin, Web5) that may not pay off
- You want to build products for consumers and small businesses at scale, not infrastructure for infrastructure's sake
- You find the intersection of regulatory compliance and system design interesting rather than annoying
- You prefer a culture of builders over a culture of researchers

Block is harder if:
- You are primarily motivated by compensation maximization (better options elsewhere)
- You are skeptical of Bitcoin as a meaningful technology and would find the internal emphasis grating
- You want to work at the absolute frontier of infrastructure technology (better options at places like Cloudflare, Databricks, or AWS itself)
- You prefer working in a single well-defined stack rather than navigating multiple tech cultures across business units

The Bitcoin idealism is real and pervasive enough that if you find it credulous or naive, you will feel it in meetings, in priorities, and in how leadership talks about the company's direction. That is not a criticism — it is just useful self-knowledge before you accept an offer.

---

## Preparing for Your Interview

The practical preparation for a Block interview:

Use Cash App for a month before your interview. Pay someone, buy some Bitcoin, use the Cash Card. The product fluency will show in your system design approach and your behavioral answers.

Read about the payments infrastructure landscape: ACH, RTP, FedNow, card networks (Visa/Mastercard interchange), and what it means to hold a money transmission license. The Block engineering blog publishes regularly and covers real problems — their posts on Cash App fraud detection and Cash Card authorization latency are worth reading.

For system design, practice designing systems with explicit correctness constraints. Financial systems have invariants that distributed systems problems typically do not: money cannot be created or destroyed, every debit must have a corresponding credit, and regulatory requirements are non-negotiable. Practice articulating these constraints first, then designing to satisfy them.

For behavioral questions, think through your experiences with products that had real-world impact on users who were not technically sophisticated. Square and Cash App's users are not developers — they are merchants and everyday consumers. Engineers who have built for non-technical users in environments with high stakes (healthcare, finance, small business) have directly relevant stories to tell.

Block is building something unusual: a company that combines the operational discipline of a payments processor, the growth velocity of a consumer fintech app, and the ideological conviction of an open-source protocol organization, all under one roof. The engineering challenges are real, the mission is genuine, and the culture has a distinct texture that you should engage with honestly rather than pretend to share or dismiss.
