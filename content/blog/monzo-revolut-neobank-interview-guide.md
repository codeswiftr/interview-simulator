---
title: "Monzo and Revolut Engineering Interview Guide"
description: "UK neobank engineering interviews: microservices at scale, banking regulation and compliance engineering, real-time payment processing, and what Monzo and Revolut each look for in engineers."
date: "2026-03-19"
category: "Company Interview Guides"
---

## Two Neobanks, Two Very Different Cultures

Monzo and Revolut are both headquartered in London, both founded within a year of each other, and both disrupted UK retail banking in ways the incumbents never anticipated. Yet their engineering cultures diverge sharply — and that divergence shows up in how they hire.

Preparing for an interview at either company without understanding this distinction is one of the most common mistakes candidates make. The technical content overlaps considerably: payment rails, ledger design, fraud systems, and regulatory compliance are universal concerns. But the values those companies signal through their interview process, and the engineer archetypes they reward, are quite different.

## Monzo's Engineering Culture

Monzo built its reputation in part through radical transparency about how it works. The Monzo engineering blog is one of the most substantive technical publishing efforts of any bank in the world — engineers write candidly about production incidents, architectural decisions, and scaling challenges. This is not a marketing exercise. It reflects a genuine belief that building trust with customers and with the wider engineering community requires showing your work.

The stack is Go-first, almost by constitution. Monzo's core platform runs on hundreds of Go microservices, each owning a narrow domain: accounts, cards, payments, notifications. Services communicate over Kafka, with Cassandra as the primary datastore for high-volume, low-latency reads. The choice of Cassandra reflects a deliberate trade-off — eventual consistency is acceptable in most read paths, but correctness on writes is non-negotiable, especially for transaction records and balance updates.

Operationally, Monzo practices what they call ops-driven development — the engineer who writes a service is expected to understand how it behaves in production, owns its runbooks, and is on call for it. This is not unusual in SRE-mature organisations, but Monzo enforces it with more rigour than most fintechs of comparable size. In interviews, this manifests as questions about observability, alerting philosophy, and how you reason about partial failures in distributed systems.

## Revolut's Engineering Culture

Revolut operates at a different tempo. The company has expanded into over 35 countries, launched products across stock trading, crypto, insurance, and business banking, and done so with a pace of execution that borders on chaotic by traditional financial services standards. Engineers at Revolut are expected to move fast, context-switch often, and tolerate a higher degree of ambiguity than they would at Monzo.

The technology stack is deliberately polyglot. Backend services run across Java, Kotlin, and Go depending on the team and the vintage of the codebase. Java and Kotlin dominate the older core banking services; Go is increasingly used for newer infrastructure and high-throughput components. This means engineers need to be adaptable rather than deeply opinionated about a single language — Revolut values engineers who can pick up an unfamiliar service and ship a fix rather than those who want to design things perfectly from scratch.

Revolut's international expansion focus also shapes technical priorities in ways that Monzo's more UK-centric operation does not face in the same way. Multi-currency handling, cross-border payment routing, and the regulatory patchwork of operating under different national frameworks simultaneously are live engineering concerns, not theoretical ones.

## Where the Technical Worlds Overlap

Despite their cultural differences, both companies deal with the same fundamental infrastructure: the UK's Faster Payments Service, SEPA credit transfers for European markets, and SWIFT for international wires. Engineers at either company are expected to understand not just the happy path of a payment but its failure modes — what happens when a payment is accepted by the scheme but the recipient bank rejects it, how refunds interact with settlement windows, and how you reconcile internal ledger state against scheme confirmations that arrive asynchronously.

Regulatory compliance is deeply embedded in the technical work. Both companies operate under FCA authorisation, which means AML checks, transaction monitoring, and suspicious activity reporting are engineering concerns as much as compliance ones. PSD2 and open banking requirements add further complexity: Strong Customer Authentication, consent management, and secure API access for third-party providers all require careful systems design. In interviews at both companies, candidates who can discuss these requirements in technical terms — not just as business constraints but as architectural drivers — stand out meaningfully.

Fraud and anti-fraud systems are another shared domain. Both companies operate real-time transaction scoring pipelines that make accept/decline decisions in milliseconds, alongside slower batch systems that review transaction patterns over days or weeks. The engineering challenge is maintaining model freshness and low false-positive rates while absorbing hundreds of millions of transactions.

## System Design Questions You Should Expect

Two system design questions appear consistently across Monzo and Revolut pipelines, in various forms.

### Design a Real-Time Fraud Detection System

The core challenge is latency under load. You need to score transactions synchronously in the payment flow — which means your feature extraction and model serving path must complete well within the authorisation window, typically under 100ms end-to-end. Candidates are expected to discuss event streaming architecture (Kafka is the natural fit), feature stores for low-latency feature reads, and how you handle the cold-start problem for new accounts with no transaction history. The distinction between synchronous (hard block) and asynchronous (soft flag, trigger review) fraud signals is worth addressing explicitly.

### Design a Multi-Currency Account Ledger

This is a deceptively hard problem. A naive approach uses floating-point arithmetic and breaks under rounding across currencies. A correct approach uses integer arithmetic in the minor unit of each currency, maintains separate ledger entries per currency, and separates the ledger (what happened, immutable) from the balance (a derived view, cacheable). Candidates should be able to discuss double-entry bookkeeping as an architectural pattern, explain why you never delete or update ledger rows, and describe how foreign exchange conversions create paired entries across currency ledgers.

## How the Interviews Differ in Practice

Monzo's interview process tends to involve more discussion of engineering values and less speed-based technical screening. You will likely have a conversation about how you have handled a production incident, what you learned from it, and how you think about the trade-off between moving fast and operating reliably. The bar for cultural alignment is genuinely high — Monzo has turned down technically strong candidates who seemed indifferent to transparency or ownership.

Revolut's process is more volume-oriented. The pipeline moves faster, the technical screens are more standardised, and the emphasis is on demonstrated ability to execute rather than extended philosophical discussions about engineering culture. If you can show that you have shipped complex features in distributed systems, reasoned correctly under pressure in a system design interview, and are comfortable with ambiguity, you will progress. Revolut hires at higher volume and moves candidates through the pipeline more quickly — which means the interview experience can feel less personalised, but also means decisions come faster.

Both companies are worth serious preparation. The technical depth they require is genuine, and the systems they operate are among the most interesting in European fintech.
