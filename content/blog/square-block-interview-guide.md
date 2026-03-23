---
title: "Square/Block Engineering Interview Guide"
description: "Technical interview preparation for Square and Block: payment processing infrastructure, POS hardware software, Bitcoin/Lightning (Spiral/TBD), and what the Jack Dorsey-led fintech conglomerate looks for in engineers."
date: "2026-03-19"
category: "Company Interview Guides"
---

Block is not a single company — it is a conglomerate of distinct businesses under Jack Dorsey's leadership. Square handles merchant point-of-sale hardware and software. Cash App is a consumer finance platform with 51M+ monthly active users. Tidal is a music streaming service. TBD builds open-source Web5 infrastructure. Spiral funds Bitcoin open-source development. Understanding which part of Block you are interviewing for changes what you need to prepare.

That said, all of Block shares some common ground: financial transactions, distributed systems that must be correct, and an increasingly Bitcoin-forward culture under Dorsey.

## The Business Landscape

**Square** is what most engineers picture when they hear "Block." It sells physical payment hardware — the Square Reader (magstripe and chip), Square Terminal, Square Register — and the software that runs on top: invoicing, appointments, inventory, payroll, and developer APIs. Merchant payments processing at scale means handling authorization, capture, settlement, and chargebacks across card networks. This is the traditional fintech core.

**Cash App** started as a P2P payment tool and has grown into a full consumer finance product: the Cash App Card (a Visa debit card), stock and Bitcoin investing, direct deposit, and tax filing. The engineering surface is broad — mobile apps, real-time payment rails (ACH, RTP, card), investing infrastructure, and fraud detection. 51M monthly active users creates significant distributed systems challenges.

**TBD** (formerly Square Crypto) is building Web5, an identity and data protocol on top of Bitcoin. If you are interviewing for TBD, you need to understand Decentralized Identifiers (DIDs), Verifiable Credentials, and why Dorsey believes user-owned identity is the next infrastructure layer. This is genuinely early-stage work — think infrastructure research, not product sprints.

**Spiral** funds Bitcoin open-source developers directly. They do not ship products; they fund contributors to Bitcoin Core, Lightning Development Kit (LDK), and related libraries.

## Technical Depth: What Interviewers Actually Test

### Payments Processing

This is the core of Square's engineering and appears in system design rounds across teams.

The card payment triangle: a merchant's payment terminal contacts the **acquirer** (Square, in this case), which routes the authorization request over the card network (Visa, Mastercard) to the **issuer** (the cardholder's bank), which approves or declines. The approval comes back the same way, and later, settlement moves the actual funds.

Know **ISO 8583** — the message format for card transaction requests and responses. You do not need to memorize field bitmaps, but understanding that a payment message is a structured binary format with message type indicators (MTIs), bitmaps, and data elements helps you reason about the protocol.

Know **EMV** (Europay, Mastercard, Visa) — the chip card standard. EMV transactions involve a cryptographic handshake between the card and the terminal, producing a Transaction Certificate (TC) that proves the genuine card was present. For hardware roles, understand the Application Transaction Counter (ATC), the ARQC/ARPC exchange, and how offline vs. online authorization decisions are made.

**Idempotency** is non-negotiable in financial systems. If a network timeout occurs mid-authorization, the system must be able to retry without double-charging the customer. Interviewers will probe your understanding of idempotency keys, how you design retry logic, and how you detect duplicate requests at the database level. A naive "just check if it exists" approach is insufficient at scale.

### Distributed Systems for Financial Accuracy

Financial systems have a higher consistency bar than most distributed systems work. The CAP theorem tradeoff that is acceptable for a recommendation system is not acceptable for a ledger.

Expect questions on:
- **Ledger design**: immutable append-only event logs vs. mutable balance tables, double-entry bookkeeping, how to reconstruct account state from events
- **Reconciliation**: how do you detect when your internal ledger disagrees with card network settlement files? How do you design a system that catches discrepancies automatically?
- **Strong consistency**: when do you need synchronous writes vs. eventual consistency? How do you handle distributed transactions without two-phase commit overhead?

### PCI DSS and Security

Square handles cardholder data at scale. You will not be expected to recite PCI DSS requirements verbatim, but understanding what cardholder data is (PAN, CVV, expiration date), why it must be tokenized, and how cryptographic key management works in payment terminals is relevant for hardware and payments platform roles. The hardware security module (HSM) is a recurring topic — understand its purpose (tamper-resistant key storage and crypto operations) even if you have not worked with one directly.

### Bitcoin and Lightning (TBD/Spiral Roles)

If you are targeting TBD or a Spiral-adjacent role, you need real Bitcoin protocol depth:

- **Lightning Network**: payment channels, how HTLCs (Hash Time Locked Contracts) enable routing payments without on-chain transactions, channel liquidity management, and failure modes (force-close, stuck HTLCs)
- **BOLT specifications**: the Lightning Network RFCs. BOLT-1 (base protocol), BOLT-2 (peer protocol), BOLT-11 (invoice format)
- **Bitcoin Script**: the stack-based scripting language. Understand P2PKH, P2SH, and SegWit output types; how multisig works; why Script is intentionally not Turing-complete

For LDK-adjacent work, understand the architecture difference between a full node (bitcoind) and a light client, and how a payment library like LDK fits into a mobile wallet stack.

## The Interview Process

Block interviews vary significantly by team but follow a recognizable pattern:

1. **Recruiter screen** — background, motivation, level calibration
2. **Technical coding assessment** — one or two sessions, usually 45–60 minutes. Block is polyglot; Python, Java, Go, and Ruby are all in use. Bring your strongest language. Problems skew toward data structures and algorithms but with practical framing (e.g., transaction deduplication, pagination of financial records)
3. **System design** — one or two rounds. Fintech context means you should expect payment-adjacent prompts: design a payment processing system, design a ledger, design a fraud detection pipeline. Come prepared to discuss consistency tradeoffs, not just scalability
4. **Behavioral** — Block uses structured behavioral interviews. The relevant themes are ownership, working across ambiguous boundaries (given Block's decentralized structure), and handling disagreement

For senior roles, expect a deeper system design round and closer scrutiny of past architectural decisions.

## Culture and What It Means for Your Interview

Post-Twitter Dorsey is more ideologically unified than the Block of 2020. Bitcoin is not just a product feature — it is a strategic direction. This affects culture in observable ways: Bitcoin literacy is respected even in non-Bitcoin teams, the company is fully remote and async-first, and there is a genuine tension between Square's traditional fintech business (which prints money) and the Bitcoin/Web5 ambitions (which are long-horizon bets).

In behavioral interviews, demonstrate that you can operate autonomously in a remote, async environment. Block does not have the dense coordination culture of a Google or Meta. Engineers are expected to drive their own work.

Do not fake Bitcoin enthusiasm if you have none — fintech credibility matters more for Square/Cash App roles. But if you are interviewing for TBD or Spiral, genuine alignment with the open-source and decentralized finance philosophy is a real signal.

## How to Prepare

Start with the fundamentals that apply across all Block teams:

- **Idempotency patterns**: read about idempotency keys in Stripe's API documentation (publicly available, well-written). Understand the difference between at-most-once and at-least-once delivery
- **EMV payment flows**: the EMV specification is publicly available. At minimum, understand the three-domain model (card, terminal, issuer) and why chip cards are more secure than magstripe
- **Ledger design**: search for "double-entry bookkeeping for software engineers" — several good write-ups exist. Understand why financial systems prefer immutable event logs over mutable state
- **The Square or Cash App engineering blog**: Block publishes engineering posts. Read a few to understand the scale they operate at and the problems they find interesting
- **For TBD roles**: read the Web5 specification on the TBD website and the Lightning Network whitepaper by Poon and Dryja

The engineers who do well at Block understand that financial systems are not just fast CRUD apps — they are systems where correctness is a hard requirement, not a goal. Design for that, explain your consistency tradeoffs, and you will stand out.
