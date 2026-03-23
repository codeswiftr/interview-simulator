---
title: "Square, Cash App, and Block Interview Guide"
description: "Technical interview preparation for Block (formerly Square) engineering roles across Square POS, Cash App, and Tidal: the Block interview process, payments infrastructure, embedded hardware software, and what the Jack Dorsey-founded company expects from engineers."
date: "2026-03-19"
category: "Company Interview Guides"
---

Block (the company formerly known as Square) is one of the most technically diverse fintech employers in the world. A single interview loop might probe your knowledge of embedded C on payment terminals, distributed systems for real-time money movement, mobile SDK design, and Bitcoin protocol internals — depending on which division is hiring. This guide covers what engineers need to know to prepare.

## Block's Engineering Landscape

Block is not one product — it is several distinct engineering organizations sharing infrastructure, tooling, and culture.

**Square** is the original business. It encompasses point-of-sale hardware (the card reader, Square Terminal, Square Register), merchant services (invoicing, payroll, appointments, online checkout), and a developer platform. Square engineers work across hardware firmware, iOS/Android SDK, backend payment rails, and data infrastructure for merchant analytics.

**Cash App** is the consumer-facing product: peer-to-peer money transfers, the Cash Card (a Visa debit card), Cash App Pay for merchant checkout, stock and ETF investing, and Bitcoin buy/sell/send. It is one of the most widely used financial apps in the US. Cash App engineering is heavy on mobile, real-time transaction systems, and financial compliance infrastructure.

**Tidal** (acquired 2021) is the music streaming platform. Engineering work there centers on content delivery, audio quality infrastructure, and creator monetization tooling.

**TBD** is Block's Bitcoin and Web5 unit, focused on decentralized identity and open Bitcoin development. If you are interviewing here, expect deep protocol-level questions.

## The Interview Process

Block's process follows the standard senior-tech pattern with some fintech-specific additions.

**Recruiter screen (30 min):** Role fit, compensation expectations, timeline. For senior roles, recruiters often ask about systems you have owned end-to-end, not just features you have shipped.

**Technical phone screen (60 min):** A coding problem on a shared editor (typically LeetCode medium difficulty), sometimes followed by a short design question. Cash App screens lean toward graph traversal and dynamic programming. Square hardware-adjacent roles may ask about concurrency and low-level I/O.

**On-site or virtual loop (4-5 hours):** Four rounds, sometimes five for staff roles.

- **Coding (x2):** Algorithm and data structure problems. Block interviewers prefer problems that have a clean brute-force solution and reward candidates who identify and explain the optimized path clearly. Talking through your reasoning matters as much as getting to the right answer.
- **System design (x1):** Architect a large-scale system. Common prompts are covered below.
- **Behavioral (x1):** Leadership principles, conflict resolution, how you handle ambiguity. Block places real weight on the builder mentality — they want people who have shipped products with real constraints, not just designed systems on paper.
- **Cross-functional or hiring manager round (x1, staff+):** Broader scope — how you influence without authority, technical vision, how you have grown other engineers.

## Unique Engineering Challenges at Block

What separates Block from a pure-software fintech is the physical layer. The Square card reader translates a magnetic stripe swipe into an encrypted payload, transmitted to a mobile SDK over audio jack or Bluetooth, which then calls Block's payment API. That chain requires firmware correctness, hardware security modules, mobile SDK stability, and backend reliability all operating in concert. Engineers on Square hardware teams are expected to understand at least two layers of that stack deeply.

**Offline-capable POS** is another differentiator. Square sellers — food trucks, farmers market vendors, pop-up shops — operate in environments with intermittent internet. Square Terminal must queue transactions, handle EMV chip fallbacks, and reconcile offline payments when connectivity returns. The consistency and ordering guarantees here are a legitimate distributed systems problem with physical-world consequences (a merchant cannot reverse a payment that was never transmitted).

**Cash App instant payment infrastructure** is where the consumer-side complexity lives. Moving money between Cash App users is near-instant, but the underlying rails (ACH, RTP, internal ledger) have different settlement windows. Cash App abstracts this with an internal ledger that advances funds before settlement completes, which creates deferred reconciliation requirements and fraud exposure windows that the risk systems must close in real time.

## Payments Domain Knowledge for Cash App Interviews

You do not need to be a payments expert, but you should understand the basics.

- **P2P payment flows:** A send from user A to user B involves identity verification, balance check, ledger debit/credit, push notification, and optional external settlement. Each step can fail independently.
- **Instant transfer mechanics:** Cash App offers instant transfer to a debit card (Visa Direct / Mastercard Send). The card network guarantees delivery in under 30 minutes. Block takes settlement risk in exchange for the fee. Understanding this risk model is relevant for design questions.
- **Bitcoin in a regulated environment:** Cash App supports Bitcoin purchase, sale, and withdrawal. Bitcoin withdrawals go on-chain; purchases may be held custodially. Questions about reconciliation, wallet key management, and FinCEN reporting requirements come up in senior interviews for Bitcoin-adjacent roles.
- **Cash Card backend:** The Cash Card is a Visa debit card backed by an internal ledger. Authorizations hit Block's systems before Visa responds to the merchant. Latency here is critical — card authorization timeouts result in declined transactions.

## System Design at Block

Three design prompts that appear frequently in Block loops:

**Design a merchant payment processing system.** Cover the authorization path (card present vs. card not present), idempotency on payment requests, retry logic, settlement batching, and dispute handling. Be explicit about where you need exactly-once semantics versus at-least-once, and why.

**Design the Cash App instant payment flow.** Start with the happy path (both users on Cash App, internal transfer), then handle external bank transfers, failed transfers, and fraud holds. Address how you would make the ledger consistent under partial failures. Interviewers want to see that you understand the difference between the user-visible state and the underlying settlement state.

**Design an inventory management system for Square sellers.** This is a more classic distributed systems problem. Cover catalog management, stock decrement on sale (ACID requirements), multi-location inventory sync, and low-stock alerting. Offline POS behavior — what happens when a tablet sells the last unit while offline — is a natural follow-up.

## Engineering Culture

Block was founded by Jack Dorsey, and his influence on engineering culture is real. The company has historically favored minimal, purposeful product design — features ship when they are good, not when the roadmap says they must. Engineers are expected to push back on product requirements that add complexity without proportional user value.

Block went fully remote-first in 2022 and maintains distributed teams across time zones. Collaboration tooling (async written communication, explicit documentation) is taken seriously. In behavioral interviews, expect questions about how you work effectively across time zones and how you make decisions without synchronous alignment.

Mobile engineering is a genuine first-class discipline at Block. iOS and Android engineers are not downstream consumers of backend APIs — they own features end-to-end including the backend services that support them. If you are a mobile engineer, be prepared to discuss your backend experience.

## Compensation

Block's compensation is competitive with Stripe, Lyft, and Uber — roughly in the tier below Google/Meta for equivalent levels. For L5 (senior engineer), total compensation in San Francisco typically falls between $280,000 and $380,000, with a meaningful equity component in SQ (NYSE: SQ), which is a publicly traded stock rather than illiquid private equity.

Block offers RSU refresh grants at review cycles, and senior engineers who have a strong first year often receive additional retention grants. Benefits are standard for a large-cap tech company: full health coverage, 401k match, stipends for home office equipment given the remote-first structure.

## Preparation Checklist

- Review payment card industry basics: authorization, clearing, settlement, chargebacks
- Practice system design with consistency and idempotency as primary constraints
- Prepare two or three examples of systems you have owned through failure and recovery
- For Cash App roles: understand Bitcoin UTXO model at a conceptual level
- For Square hardware roles: review how mobile SDKs communicate with peripheral hardware
- Brush up on distributed transaction patterns: saga, two-phase commit, outbox pattern
