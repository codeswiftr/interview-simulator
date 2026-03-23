---
title: "Robinhood Trading Infrastructure: Fractional Shares, Options, and Crypto Under the Hood"
description: "A technical deep dive into how Robinhood built fractional share trading, options pricing, and crypto execution — and what the 2021 outages revealed about the limits of that architecture."
date: "2026-03-19"
category: "Company Deep Dives"
---

## The Infrastructure Bet That Built a Brokerage

Robinhood entered the market with one engineering bet: if you remove the per-trade commission, you need extreme cost efficiency across every layer of the stack. That shaped everything — the early Python/Django monolith, the eventual Go migration, and the decisions that later caused outages that made national headlines.

This post is not a puff piece. It covers what Robinhood actually built, how the pieces fit together, where the architecture cracked under load, and what engineers interviewing there are expected to know.

---

## Order Routing and Execution

Robinhood is a broker-dealer, which means they route customer orders to market makers and exchanges rather than executing them on their own exchange. The primary mechanism is payment for order flow (PFOF): market makers like Citadel Securities and Virtu pay Robinhood for the right to fill customer orders. This is how zero-commission trading remains economically viable.

From an engineering standpoint, the order routing layer has to handle:

- **Order validation** — margin checks, pattern-day-trader flags, options level eligibility, buying power calculation in real time
- **Smart order routing (SOR)** — selecting the venue (market maker, exchange) that offers best execution at the time of submission
- **Order lifecycle management** — tracking fill status, partial fills, cancellations, and corrections across external systems

The core challenge is latency asymmetry. Retail orders are not high-frequency, but customers expect near-instant confirmation. The system must validate, route, and surface a response in under a second while maintaining correctness guarantees. That means the buying-power calculation service has to be consistent enough to prevent overselling (selling shares you don't own) without adding enough latency to noticeably degrade UX.

---

## Fractional Shares: A Data Model Problem

Fractional shares are harder than they look. When a customer buys $10 of Apple stock, Robinhood does not buy 0.054 shares from an exchange — exchanges only trade whole shares. Robinhood aggregates fractional demand internally and trades whole shares on behalf of the pool, then allocates fractions to individual accounts.

This creates a few non-trivial engineering problems:

**Precision and rounding.** Dollar amounts and share quantities need high-precision arithmetic throughout. Floating-point is not safe for this. Robinhood uses fixed-point decimal arithmetic in their financial calculations to avoid accumulated rounding errors that could create regulatory compliance issues.

**Internal ledger vs. external custody.** The customer sees 0.054 shares, but the DTC (Depository Trust Company) only holds whole shares under Robinhood's DTCC account. Robinhood maintains an internal ledger that maps fractional positions to whole-share custody, reconciling continuously against their clearing house records.

**Corporate actions.** When Apple does a 4-for-1 stock split, every fractional position needs to be updated atomically. The system must process the split, recalculate all fractional balances, and reflect those changes before markets open — at scale, across millions of accounts.

In interviews, Robinhood engineers describe the fractional shares system as one of the more genuinely complex data consistency problems in their codebase, because it involves coordinating across internal ledgers, external custody records, and real-time pricing while preserving penny-accurate correctness.

---

## Options Pricing Infrastructure

Options are more infrastructure-intensive than equities. A stock has one live price. An options chain has hundreds of contracts per underlying, each with its own bid/ask, implied volatility, and Greeks (delta, gamma, theta, vega). For a liquid name like SPY or AAPL, there can be thousands of active contracts.

The pricing pipeline works roughly like this:

1. **Market data ingestion** — raw quote and trade data comes in over OPRA (Options Price Reporting Authority) feed, which carries over a billion messages per day at peak
2. **Greeks calculation** — implied volatility and Greeks are calculated in near-real time using Black-Scholes and its variants; this is CPU-intensive and has to be parallelized across the contract universe
3. **Display layer** — the mobile app shows a simplified view, but the backend has to maintain the full options chain with enough freshness to support placing trades

The latency requirement for options display is looser than equities (a few seconds is usually acceptable for retail), but the throughput is dramatically higher. OPRA is one of the highest-volume market data feeds in U.S. markets, and consuming it efficiently requires careful use of kernel bypass networking, UDP multicast, and low-garbage processing pipelines.

Robinhood's move toward Go was partly driven by this: Python's GIL makes it difficult to run CPU-bound and I/O-bound work concurrently at scale. Go's goroutine model maps more naturally onto the fan-out pattern of market data processing.

---

## Crypto Trading: An Exchange Inside a Brokerage

Robinhood Crypto is a different regulatory and technical entity from the equities brokerage. It operates as a licensed money transmitter in most states and as an exchange for crypto trading, meaning Robinhood internalizes crypto order flow rather than routing to external venues.

This introduces infrastructure the equities side doesn't have:

**24/7 trading.** Crypto markets don't close. The system can't rely on overnight batch jobs or end-of-day reconciliation windows. Every operational process — risk checks, custody reconciliation, incident response — has to work continuously.

**Custody and key management.** Holding customer crypto requires secure key management infrastructure. This is not a software problem you can outsource cheaply; it involves HSMs (hardware security modules), cold storage procedures, and auditability requirements. A bug here is irreversible.

**Exchange matching engine.** For crypto, Robinhood runs a matching engine that pairs buy and sell orders. The core invariant is simple (price-time priority), but implementing a lock-free order book that handles cancellations, partial fills, and self-match prevention at low latency is legitimately difficult.

**Blockchain settlement.** When customers deposit or withdraw crypto, Robinhood has to watch blockchain state, detect confirmations, and update internal balances — all asynchronously, with no guaranteed delivery time and the possibility of chain reorganizations.

---

## Market Data Ingestion and Distribution

The infrastructure that pushes prices to millions of mobile clients is a fan-out problem. At market open, every active customer potentially refreshes their portfolio simultaneously. The naive architecture — each client polling a price service — doesn't scale.

Robinhood's approach is a publish-subscribe pipeline:

- **Ingest tier:** Dedicated feed handlers consume raw market data (OPRA, CTA/UTP for equities) and normalize it into internal events
- **Processing tier:** Kafka carries events between the ingest tier and downstream consumers. Each consumer (Greeks calculator, portfolio valuation engine, display cache) subscribes to the relevant topics
- **Distribution tier:** WebSocket connections push price updates to mobile clients. The session layer partitions subscribers by instrument so each price update is published once and fanned out to all active sessions holding that instrument

The portfolio calculation service is the hottest component at market open. It has to recompute unrealized P&L for every active session that holds a position in an instrument that just moved. This requires maintaining a low-latency join between live price data and stored position data — one of the few places where the architecture genuinely resembles a stream processing problem more than a request-response one.

---

## The 2021 Outages: What Failed and Why

The March 2020 outage (not 2021, but part of the same pattern) was the first major public failure. Robinhood went down for most of a trading day. The official explanation cited DNS issues, but the proximate cause was a cascade: unprecedented trading volume from COVID volatility caused database connection pools to exhaust, which caused service health checks to fail, which caused load balancers to cycle traffic in a way that amplified the problem.

The January 2021 GameStop episode was different in character. The infamous decision to restrict purchases of GME, AMC, and others was not primarily a software failure — it was a capital requirement failure. DTCC's clearing house requires brokers to post collateral proportional to the volatility and volume of securities they're clearing. Robinhood's collateral requirement jumped by an order of magnitude overnight. They didn't have enough liquidity and had to restrict trading to reduce their settlement exposure.

What this exposes technically:

- **Risk system coupling.** The buying power and position limit systems are downstream of clearing constraints, but the relationship wasn't tight enough to automatically reduce exposure before a crisis
- **Operational communication.** The engineering team had to push a change to production that restricted trading on specific symbols under regulatory time pressure — exactly the kind of high-stakes, high-velocity change where deployment pipelines and feature flag systems get tested
- **Resilience under correlated load.** The outages happened when volume was highest — precisely when the system most needed to work. Load testing at 10x normal volume, with correlated bursts across all assets simultaneously, is much harder than standard load testing

---

## What Robinhood Engineering Interviews Test

Robinhood's engineering interviews concentrate on a few recurring themes:

**Financial systems correctness.** They expect candidates to reason carefully about decimal precision, atomicity, and idempotency. A common pattern: "walk me through how you'd implement a fund transfer that's safe to retry." The correct answer involves idempotency keys, two-phase commits or compensating transactions, and explicit handling of the partially-failed state.

**High-throughput data pipelines.** Expect questions about Kafka consumer group design, partition key selection, and handling consumer lag. They care whether you've thought about backpressure and what happens when a downstream consumer is slow.

**Reliability under load.** Circuit breakers, bulkheads, graceful degradation. They've been burned by cascading failures; they want engineers who think about failure modes proactively rather than just building the happy path.

**The Go migration context.** If you're interviewing for backend roles, knowing why Go replaced Python for their performance-critical services — and the tradeoffs involved — signals that you understand production systems rather than just language syntax.

---

## The Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Backend services | Go (performance-critical), Python/Django (legacy and internal tooling) |
| Message bus | Apache Kafka |
| Cloud infrastructure | AWS (EC2, RDS, ElastiCache) |
| Mobile clients | Swift (iOS), Kotlin (Android) |
| Market data | OPRA (options), CTA/UTP (equities), proprietary feeds (crypto) |
| Crypto custody | HSMs, cold storage, multi-sig |

---

## Preparing for the Interview

The most useful thing you can do before a Robinhood interview is read their engineering blog posts on the GameStop incident and their infrastructure scaling work. They're unusually candid about what broke and why. Candidates who show up having absorbed those lessons — and who can reason about similar failure modes in system design questions — consistently report better outcomes.

The core signal they're looking for: do you build systems that are correct under failure, or just correct in the happy path? In fintech, those are very different things.
