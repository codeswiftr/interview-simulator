# Fintech Startup Engineer Interview Guide 2024: Brex, Stripe, Mercury, and the Modern Stack

Engineering at Brex, Mercury, Ramp, or Plaid is not the same as engineering at a FAANG company, and it is certainly not the same as engineering at a traditional bank. The problems are different, the constraints are different, and interviewers are filtering for a different profile. Candidates who prepare with generic software engineering interview material often underestimate how much domain-specific knowledge matters at modern fintech companies.

This guide covers what makes fintech engineering distinctive, what specific topics come up in interviews at these companies, and how to prepare for the technical questions that separate strong candidates from the rest.

## Why Fintech Engineering Is Different

The fundamental constraint in fintech engineering is correctness over performance. In most software domains, a bug that causes a wrong answer is recoverable — you fix it and move on. In financial software, a bug that processes a transaction incorrectly has legal, regulatory, and reputational consequences that are extremely difficult to unwind. A payment sent to the wrong account, a balance displayed incorrectly, a fee charged twice — these are not normal software bugs. They are financial events with real-world consequences.

This correctness requirement shapes every engineering decision at a fintech company. It is why fintech engineers care so deeply about ACID transactions when many modern distributed systems have moved away from them. It is why idempotency is non-negotiable, not a nice-to-have. It is why the codebase for money movement at a company like Stripe or Brex tends to be more conservative in its use of new technology than the codebase for their marketing website or internal tooling.

The second distinctive constraint is regulatory compliance. Fintech companies operate under PCI DSS, SOC 2, KYC (Know Your Customer), and AML (Anti-Money Laundering) requirements. These are not abstractions — they shape the data model, the access control design, the audit logging requirements, and the incident response playbook. Engineers at fintech companies have to understand compliance as an engineering constraint, not just a legal checkbox.

## Double-Entry Bookkeeping and the Ledger Model

This is one of the most important concepts to understand before interviewing at a fintech company, and most software engineers have never encountered it.

Double-entry bookkeeping is the accounting principle that every financial transaction must be recorded as both a debit to one account and a credit to another account of equal value. The system of accounts must always balance: total debits equal total credits. This is not just a bookkeeping convention — it is a mathematical invariant that makes errors detectable.

Modern fintech companies model their data around a ledger built on this principle. Rather than storing balances as mutable state that you update when money moves, you store an immutable log of journal entries. The balance at any point in time is derived by summing all entries. This design has several important properties: you can always audit the complete history of any account, you can detect inconsistencies by checking that the ledger balances, and you cannot lose information through an overwrite.

Interviewers may ask you to design a payment processing system or a wallet system, and the expected answer at a fintech company models the state as a ledger with immutable journal entries rather than as a table of mutable balance records. Candidates who default to a simple balance field that you increment and decrement are showing that they have not thought carefully about the accounting model.

The practical implementation typically involves a journal_entries table with columns for the source account, destination account, amount, currency, and a reference to the business transaction that caused the entry. You derive balances by querying this table, often with materialized views or cached balance snapshots for performance.

## Idempotency as a Non-Negotiable Requirement

Network failures happen. Clients retry requests. In most software, duplicate requests cause duplicate actions — if you submit a form twice, you see a harmless error or an annoying duplicate entry. In financial software, duplicate requests can charge a customer twice, send a payment twice, or create two accounts for the same person.

Idempotency is the property that a request can be executed multiple times with the same result as executing it once. Achieving idempotency in financial APIs requires careful design.

The standard approach uses client-generated idempotency keys. The client generates a unique key (a UUID or similar) for each logical operation and includes it in the request header. The server stores the idempotency key alongside the result of the first successful execution. If the same key arrives again, the server returns the stored result without re-executing the operation.

The implementation complexity is in the edge cases. What happens if the first request arrives, starts processing, and the server crashes before completing? The idempotency key is stored but the operation is incomplete. The second request arrives with the same key — should you return the cached (incomplete) result or re-execute? The answer depends on where you store the idempotency key relative to the transaction that processes the operation.

A common interview question: implement an idempotent payment API endpoint. The expected answer includes: the idempotency key lookup before processing, the atomic operation that marks the key as used and records the transaction, and the response behavior for duplicate requests. Candidates who can articulate the race conditions and explain why the atomic operation is necessary demonstrate the depth that fintech interviewers are looking for.

Stripe's API design — widely regarded as the gold standard for financial APIs — uses idempotency keys throughout. Studying Stripe's API documentation is useful preparation not just for Stripe interviews but for any fintech company whose API design was influenced by Stripe's model.

## ACID Transactions and When They Matter

Modern distributed systems have popularized eventual consistency and BASE properties as an alternative to ACID transactions. In many domains this is the right trade-off: you get better availability and partition tolerance at the cost of some consistency. In financial systems, this trade-off is almost always wrong for core money movement.

ACID properties — Atomicity, Consistency, Isolation, Durability — are what make financial operations reliable. Atomicity means that a transfer either debits one account and credits another, or does neither — there is no state where money has left one account but not arrived in the other. Consistency means the database remains in a valid state after every transaction. Isolation means concurrent transactions do not see each other's incomplete work. Durability means committed transactions survive system failures.

PostgreSQL is the dominant database at modern fintech companies (Stripe, Brex, Mercury all use Postgres), precisely because it provides strong ACID guarantees while being performant enough for the transaction volumes these companies handle. The engineering culture at these companies reflects a deliberate choice: use strong consistency for financial data, accept the trade-offs in scalability, and solve the scalability problems with better application-layer sharding and read replicas rather than by weakening consistency.

Interviewers will test your understanding of when strong consistency is required versus when eventual consistency is acceptable. The answer for balance queries, payment processing, and fund transfers is strong consistency. The answer for analytics queries, dashboard aggregations, and non-financial state may be eventual consistency. Being able to articulate this distinction with specific examples is important.

## Fraud Detection Engineering

Fraud detection is a significant engineering domain at every fintech company, and it appears in both system design and behavioral interviews.

The core technical challenge is that fraud detection is a real-time classification problem under adversarial conditions. You are trying to classify transactions as fraudulent or legitimate, in milliseconds, using features that fraudsters actively work to defeat. The engineering requirements are:

Real-time feature computation. You need to compute features like "how many transactions has this user made in the last 10 minutes" or "is this IP address associated with recent fraud" with very low latency. This typically requires a combination of streaming feature computation (Kafka + Flink or similar) and fast feature stores (Redis for real-time features, a feature store like Feast or Tecton for more complex feature pipelines).

Rule-based and model-based detection in combination. Pure ML models are difficult to explain to regulators and to customers disputing false positives. Pure rule-based systems cannot generalize to new fraud patterns. Most production fraud systems layer deterministic rules (block this specific card number, block transactions over $X without additional verification) over ML models that score transaction risk, with human review queues for edge cases.

Feedback loops and false positive management. A fraud detection system that blocks legitimate transactions damages customer trust and revenue. The engineering challenge is building feedback loops that incorporate dispute outcomes back into the model, tracking false positive rates by customer segment, and providing customers with clear paths to resolve false positives.

A common interview question: design a fraud detection pipeline for a payments company. The expected answer covers the feature computation layer, the scoring layer, the decision layer (block/allow/review), and the feedback loop. Candidates who also address latency requirements, explainability, and the ops model for the human review queue demonstrate senior-level thinking.

## Banking API Integration Patterns

Plaid is the dominant API for connecting to consumer bank accounts in the US, but understanding the broader ecosystem of banking integrations is important for fintech interviews.

Plaid acts as an aggregator: it connects to thousands of financial institutions on behalf of developers, handling the authentication complexity and the data normalization across institutions that use completely different data formats. From an engineering perspective, Plaid gives you a normalized transaction data model, but it also introduces a third-party dependency with its own reliability and data freshness characteristics. A transaction you see in Plaid may be hours or days behind the actual bank ledger.

For direct bank integrations — ACH (Automated Clearing House) for US bank transfers, SEPA for European transfers, FedWire for same-day large transfers — the patterns are different. ACH is asynchronous with multi-day settlement windows. A payment initiated today may not settle for two to three business days, and reversals are possible during that window. Engineering a product on top of ACH requires modeling the settlement lifecycle explicitly, handling notifications from the ACH network, and designing UX that does not confuse users about when money is "really" available.

The engineering pattern for all of these integrations involves event-driven state machines. A payment is not a single event — it is a state machine with transitions: initiated, pending, cleared, settled, returned, disputed. The database model must represent these states, the transitions must be atomic, and the system must handle messages from external networks that arrive out of order or multiple times.

## Compliance as an Engineering Constraint

PCI DSS (Payment Card Industry Data Security Standard) governs how you handle card data. The most important engineering implication is tokenization: raw card numbers (PANs) should never touch your servers. You use a payment processor (Stripe, Adyen, Braintree) to tokenize cards at the client side, and you store only the token. This reduces your PCI scope dramatically — if you never handle raw card data, most of the PCI requirements do not apply to your systems directly.

SOC 2 compliance requires demonstrating that you have controls around security, availability, processing integrity, confidentiality, and privacy. From an engineering perspective, this means comprehensive audit logging (who accessed what data, when, from where), access control reviews, vulnerability scanning, and documented incident response. SOC 2 is relevant in engineering interviews when discussing system design, because interviewers want to see that you naturally include audit logging and access control in your designs.

KYC (Know Your Customer) and AML (Anti-Money Laundering) requirements mandate that fintech companies verify customer identities before allowing financial transactions and monitor for suspicious patterns. Engineeringly, this means integrating with identity verification vendors (Persona, Jumio, Onfido), building sanctions screening against government watch lists (OFAC, etc.), and implementing transaction monitoring rules that flag suspicious patterns for compliance review. A common design question: how would you design the onboarding flow for a business banking product? The expected answer includes identity verification, beneficial ownership verification for businesses, document collection, and the workflow for compliance review.

## The Monorepo Culture

Most of the modern fintech startups — Stripe, Brex, Ramp — use monorepos. Understanding monorepo tooling and culture is useful preparation.

The rationale is atomic cross-service changes. When you change a shared data model or API contract, you can update all consumers in a single commit and verify they all work together in CI. This is significantly harder in a polyrepo setup where each service has its own repository.

The tooling for large monorepos (Bazel, Nx, Turborepo) handles the dependency graph to avoid rebuilding and testing everything on every change. Interviewers at companies with large monorepos may ask about your experience with monorepo tooling, build caching, and how you structure services within a monorepo.

The code sharing patterns that work well in monorepos (shared libraries, generated client code) are different from the patterns that work in polyrepo setups. Understanding the trade-offs — and being able to articulate why a financial company might choose the coordination overhead of a monorepo over the independence of a polyrepo — demonstrates engineering maturity.

## The Modern Fintech Stack

The dominant stack at the companies in this guide is TypeScript for product services, Go for core financial infrastructure, PostgreSQL for financial data, Kafka for event streaming, and Redis for caching and real-time features.

TypeScript has largely displaced pure JavaScript at serious fintech companies because financial logic needs to be type-safe. The TypeScript strictness settings at these companies tend to be high — no implicit any, no null escapes — because the cost of a type error is higher than in typical web software.

Go is preferred for anything in the critical payment path: the ledger service, the payment processor integration layer, the fraud scoring service. Go's performance characteristics, strong standard library support for network services, and explicit error handling (no exceptions) fit the correctness requirements of financial infrastructure.

Kafka is used for event streaming between services and for the audit log. Every significant financial event — a transaction initiated, a payment settled, a user account state change — is published to Kafka. Downstream services consume these events to update read models, trigger downstream processes, and feed analytics. The Kafka consumer offset provides a mechanism for reprocessing events, which is valuable for backfill operations and for recovering from processing bugs.

## What Interviewers at Fintech Look For vs. FAANG

FAANG interviews optimize heavily for algorithmic problem solving. A strong FAANG candidate can implement a balanced BST under time pressure and discuss the trade-offs between different sorting algorithms. Fintech interviews optimize for domain knowledge and engineering judgment.

At a fintech company, the system design interviews are more likely to involve payment systems, ledger design, and fraud detection than URL shorteners and notification systems. The coding interviews are more likely to test your ability to write correct, maintainable code in a domain with real constraints than your ability to optimize an algorithm to O(n log n).

The behavioral interviews at fintech companies probe for ownership and judgment under ambiguity. Financial systems have edge cases that are not obvious until you encounter them in production. Interviewers want to understand how you handle discovering that your code has a financial error, how you prioritize correctness versus velocity, and how you think about the downstream consequences of your technical decisions.

The strongest fintech candidates can talk fluently about the accounting model, have thought carefully about consistency and idempotency, understand the regulatory environment at a practical level, and have opinions about how to build systems that handle money correctly at scale. This combination — strong engineering fundamentals plus fintech domain knowledge — is genuinely rare, and companies pay accordingly.

## Preparation Strategy

Read Stripe's API documentation thoroughly. It is a masterclass in financial API design — idempotency, pagination, versioning, error handling, and event modeling are all done well and explained clearly. Even if you are not interviewing at Stripe, understanding their patterns prepares you for questions at any modern fintech company.

Practice designing financial systems. Design a digital wallet from scratch: what is the data model, how do you handle concurrent balance updates, how do you implement idempotency, how do you reconcile with an external payment network? Design a payment splitting system for a corporate expense management product.

Understand the accounting model. Work through a simple double-entry bookkeeping example until it is intuitive: what accounts exist, what journal entries are created when a payment is made, how you compute the balance of any account at any point in time.

For coding interviews, practice writing code with explicit error handling, clear transaction boundaries, and correctness as the primary goal. Practice writing idempotent operations. The fintech coding interview is not testing whether you can write clever code — it is testing whether you write code you would trust to touch real money.

The fintech engineering market is competitive but highly rewarding for engineers who take the time to develop genuine domain expertise. The companies in this space are building the financial infrastructure that businesses and individuals depend on, and the engineering challenges are genuinely interesting. Candidates who can demonstrate that they understand what is at stake when writing financial software stand out immediately.
