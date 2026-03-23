---
title: "Brex Engineering Interview Guide"
description: "Technical interview preparation for Brex engineering roles: the Brex interview process, Elixir-heavy backend, corporate card infrastructure, financial platform engineering, and what one of Y Combinator's most successful companies expects from engineers."
date: "2026-03-19"
category: "Company Interview Guides"
---

## What Brex Does

Brex is a fintech company that provides corporate cards, expense management, and business banking products to startups and enterprises. Founded in 2017 and backed by Y Combinator, Brex reached unicorn status in under two years and is now one of the most prominent fintech companies in the US.

The company competes directly with Ramp on the spend management side and with legacy providers like American Express and Visa commercial cards on the credit side. Brex's differentiation has been underwriting based on company fundamentals rather than personal credit, real-time spend controls, and a modern software platform that integrates natively with accounting tools like QuickBooks and NetSuite.

Brex's engineering team is building infrastructure that moves significant dollar volume daily. The technical challenges are real: sub-second transaction authorization, credit risk at scale, multi-currency ledger integrity, and regulatory compliance across jurisdictions.

## The Elixir Factor

Brex made an unusual architectural choice: its backend runs primarily on Elixir, making it one of the largest production Elixir codebases in the world. This is not a minor implementation detail — it shapes the entire engineering culture and interview process.

Elixir runs on the BEAM virtual machine (the same runtime as Erlang), which was designed for telecommunications systems requiring nine-nines uptime. For financial transaction processing, the properties BEAM provides are directly relevant:

- **Fault isolation**: each process (in the actor model sense) is isolated; a crash in one does not cascade
- **Concurrency without shared state**: the actor model uses message passing, eliminating entire classes of race conditions that plague shared-memory concurrency
- **Hot code upgrades**: production systems can be updated without downtime
- **Supervision trees**: OTP provides a structured way to monitor, restart, and recover processes automatically

For a company that cannot afford transaction failures, authorization timeouts, or ledger corruption, these properties are engineering requirements, not preferences.

## Interview Process

The Brex interview process typically follows this structure:

1. **Recruiter screen**: 30 minutes, focused on role fit, compensation expectations, and work authorization. Expect questions about why fintech and why Brex specifically.

2. **Technical phone screen**: 45-60 minutes with a senior engineer. Coding exercise, usually in the candidate's language of choice. However, Brex does expect engineers to be willing to work in Elixir or to learn it, so familiarity with functional programming is advantageous. Some interviewers will ask about Elixir specifically.

3. **System design**: For senior roles, a separate session covering distributed systems design. Financial system scenarios are common: design a ledger, design a card authorization system, design a fraud detection pipeline.

4. **On-site (virtual)**: Four to five sessions covering coding, system design, cross-functional collaboration, and behavioral interviews. On-site loops at Brex are selective — pass rates are lower than at many comparable companies.

Brex has a reputation for high hiring bars. The team is relatively small for the transaction volume it handles, which means each engineer carries more surface area than at larger companies.

## Elixir-Specific Technical Expectations

If you are interviewing for a backend role, prepare for Elixir-specific questions even if you have not used it professionally:

**OTP and supervision trees**: Understand how supervisors monitor worker processes, restart strategies (one-for-one, one-for-all, rest-for-one), and why OTP's fault tolerance model matters for reliability. Be able to explain what happens when a GenServer crashes and how the supervision tree recovers.

**GenServer patterns**: Know how to implement a GenServer, the difference between `call` and `cast`, how state is managed across requests, and how to handle timeouts. Brex uses GenServers extensively for stateful processes like session management and rate limiting.

**The actor model in financial contexts**: Be ready to explain why message-passing concurrency is preferable to shared-state concurrency for financial transaction processing. Interviewers may ask you to design a system where multiple processes need to coordinate on account balances without deadlocks.

**Phoenix and Ecto**: Brex's web layer runs on Phoenix. Ecto is the database library — understand changesets, associations, and query composition. Ecto's explicit changesets make data validation auditable, which matters for financial applications.

**Pattern matching and immutability**: These are fundamental Elixir idioms. Be comfortable reading and writing pattern-matched function heads, using `with` for sequential operations, and working without mutation.

## Financial Engineering Challenges

The problems Brex's engineers solve are domain-specific and worth understanding before your interview:

**Credit underwriting**: Brex underwrites based on company data (funding, runway, spending patterns) rather than personal FICO scores. The engineering challenge is building models that assess credit risk in real time, update limits dynamically, and comply with credit regulations. Expect questions about how you would model credit risk or design a limit adjustment system.

**Real-time transaction authorization**: Every Brex card transaction requires an authorization decision in under a second. The system must check available credit, apply spend controls (category limits, per-transaction limits), detect fraud signals, and respond to the card network. Latency and availability are critical — a timeout results in a declined transaction.

**Double-entry ledger systems**: Every financial transaction in a properly implemented system creates two ledger entries: a debit and a credit. Brex implements this in Elixir with strong consistency guarantees. Be prepared to discuss double-entry accounting, ledger integrity constraints, and how you would implement reconciliation.

**Card network integration**: Brex issues Visa cards, which means integrating with Visa's authorization network (VisaNet). The protocols involved (ISO 8583, for example) are low-level and specific. You are not expected to know them in detail, but understanding that card payments involve multiple parties (issuer, acquirer, network) and multiple settlement steps is useful context.

## Engineering Culture

Brex is remote-first. The engineering organization operates across US time zones with some international presence. Remote-first at Brex means it is designed for async communication, not a hybrid arrangement where remote engineers are second-class participants.

The team is known for high standards and selective hiring. Engineers are expected to own their systems end-to-end: design, implementation, deployment, and on-call. There is less specialization than at larger companies, which means broader scope but also more autonomy.

Brex invests in engineering infrastructure. The decision to build one of the largest Elixir codebases in the world reflects an organization willing to make unconventional choices for technical reasons. Engineers who thrive here tend to be opinionated about technical quality and interested in the domain specifics of fintech.

## Compensation

Brex compensates at a level comparable to Stripe and Coinbase for comparable roles — competitive with the upper tier of fintech companies. Total compensation includes:

- Base salary in the $180,000-$250,000+ range for senior engineers depending on level and location
- Equity in a private company valued at unicorn scale, with meaningful upside contingent on IPO or acquisition
- Standard benefits including health, dental, vision, 401(k), and paid parental leave
- Remote work allowances and equipment stipends

Equity at a private company carries illiquidity risk. Brex has not yet gone public, which means equity value is not realized until a liquidity event. Factor this into your total compensation evaluation.

## Preparation Priorities

For Brex backend roles, prioritize in this order:

- Functional programming fundamentals (even if you use another language in the screen)
- Distributed systems design with emphasis on consistency and fault tolerance
- Financial systems concepts: ledgers, double-entry accounting, transaction processing, credit risk
- Elixir syntax and OTP patterns — at minimum, be able to read Elixir code and reason about GenServer behavior
- Behavioral preparation around ownership, high-stakes failures, and cross-functional collaboration

Brex is a company that has built a technically unusual and financially critical system. Interviewers are looking for engineers who understand both the technical choices and the domain constraints that drove them.
