# Rippling Engineering Deep Dive: The Architecture Behind the Compound Startup

Most enterprise software companies pick a lane. Workday owns HR. Okta owns identity. Jamf owns device management. Expensify owns expense reports. Rippling's founding thesis was that keeping all of these in separate systems is itself the bug — and that the right answer is to build them all, tightly integrated, from a single data model. That thesis has produced one of the most technically ambitious engineering organizations in enterprise software, and one of the most demanding interview processes in the industry.

This post goes deep on four architectural domains where Rippling's engineering decisions are both technically interesting and directly relevant to interview preparation.

---

## The Compound Startup Model: Ten Products, One Data Graph

Rippling ships payroll, benefits administration, device management, spend management, corporate cards, learning management, headcount planning, IT security, and App Management — simultaneously, as a single product. The traditional enterprise software vendor builds one of these and partners for the rest. Rippling builds them in-house and connects them to a shared employee record.

The engineering challenge this creates is not obvious until you think about the data layer. In a siloed world, your payroll system knows each employee's compensation. Your IT system knows what laptops each employee has. Your identity system knows what SaaS apps each employee can access. Each of these systems has its own data model, its own database, its own API. Integrations between them are batch jobs, webhook syncs, or manual processes. They drift out of sync constantly.

Rippling's architectural bet is that these systems should all write to and read from a single source of truth about every employee — the unified employee record. When a manager marks an employee as terminated, that single event propagates atomically: payroll is halted, laptop MDM policies are unenrolled, SSO access is revoked, SaaS app licenses are reclaimed. No sync lag, no orphaned access, no manual checklist.

Building this requires solving a problem that distributed systems engineers will recognize: you have ten separate subsystems, each with their own domain logic and data requirements, but they need to share a consistent view of the world. The engineering choices around consistency (eventual vs. strong), transaction boundaries (can you terminate employment atomically across all subsystems, or do you need a saga pattern with compensating transactions?), and schema evolution (what happens when the payroll system needs a field on the employee record that no other system cares about?) are exactly the class of problems Rippling's engineers navigate daily.

The interview implication is immediate: Rippling does not hire engineers who think in isolated services. They hire engineers who understand cross-cutting data models, consistency trade-offs, and the operational complexity of keeping ten product domains synchronized.

---

## The Payroll Computation Engine: Compliance as Code

Payroll is deceptively complex. On the surface, it looks like multiplication: hours worked times hourly rate, minus taxes. In practice, payroll computation is one of the most compliance-dense calculations in business software, and Rippling runs it for companies in 140+ countries.

Consider just the US multi-state tax problem. An employee who lives in New Jersey but works in New York owes income tax to both states, with a credit mechanism to prevent double taxation. An employee who works remotely across multiple states in a given pay period triggers nexus obligations for the employer in each state they worked. Supplemental wages (bonuses, commissions) are taxed at different rates than regular wages at the federal level, and each state has its own treatment. Garnishments — court-ordered deductions for child support, student loans, or creditor judgments — have priority ordering rules and consumption limits defined by both federal law and varying state statutes.

Rippling's approach to this problem is a rule engine for payroll compliance: a structured system for encoding tax regulations, garnishment priorities, benefit contribution limits, and direct deposit routing rules as computable logic rather than hardcoded business logic. This design matters because tax law changes constantly. A hardcoded payroll system requires an engineer to update code for every regulatory change. A rule engine externalizes the rules, making compliance updates a data change rather than a code deployment.

The technical architecture of such an engine involves several non-trivial components: a rule representation format expressive enough to capture federal and 50-state tax tables, phase-in computations, and multi-variable thresholds; a computation graph that determines the correct order of operations (gross pay must be computed before pre-tax deductions, which must be computed before taxable income, which must be computed before withholding); and an audit trail that records the exact rule versions applied to each paycheck so that historical recomputation is possible during a tax audit.

Direct deposit routing adds another layer. ACH transactions in the US must be submitted to the Federal Reserve's network with specific file formats, cutoff times, and error handling procedures. International payments across 140 countries require integrations with dozens of local banking rails, each with their own formatting requirements, settlement timelines, and failure modes.

The interview implication: if Rippling gives you a system design question involving financial computation, compliance, or batch processing, the evaluator is looking for domain awareness alongside systems thinking. A candidate who designs a payroll system without mentioning rule versioning, audit trails, or idempotent reprocessing has not thought about the real problem.

---

## Device Management at Scale: MDM as Infrastructure

Rippling's IT product manages laptops, phones, and tablets for thousands of companies. When an employee is hired, Rippling can automatically enroll their MacBook into a Mobile Device Management profile, install company-required applications, enforce disk encryption, configure Wi-Fi credentials, and push security policies — all without an IT administrator manually touching the device.

The underlying protocol for Apple devices is MDM, Apple's own protocol for remotely managing enrolled iOS and macOS devices. Apple Business Manager (ABM) is the enrollment layer: companies register with ABM, which allows them to automatically enroll every Apple device purchased through Apple's supply chain into their MDM server without requiring the employee to manually install a management profile.

From an engineering perspective, MDM is a command-queue protocol. The server enqueues commands (install this application, enforce this security policy, lock the device, wipe the device) against a device identifier. The device checks in periodically via an Apple Push Notification — Apple's APNs infrastructure acts as the always-on channel that wakes the device to check its command queue. This architecture means the MDM server must maintain durable command queues per device, handle device check-in events at scale, track command acknowledgment and failure states, and retry commands when devices are offline.

Rippling manages this fleet across Windows (via Microsoft Intune-compatible protocols and the WinMDM protocol stack), Android (Google Workspace device management), and Apple. Each platform has a different protocol, a different certificate management story, and different failure modes. The engineering challenge is building an abstraction layer over these three incompatible ecosystems while preserving the platform-specific capabilities that make each protocol useful.

Certificate lifecycle management is a particular operational hazard. MDM communication is secured by device certificates and push certificates, both of which expire. A push certificate expiration for an Apple MDM server breaks communication with every enrolled Apple device simultaneously. Rippling's infrastructure must monitor certificate expiration across thousands of customer MDM configurations and renew them proactively before they break.

---

## The Unified Identity and Access Model: SCIM, SSO, and the Access Graph

Rippling's core value proposition — that onboarding an employee provisions every system automatically — depends on a system that knows two things at all times: who this person is, and what they should be able to access.

The "who" is handled through SCIM (System for Cross-domain Identity Management), an open standard for provisioning user accounts across SaaS applications. When Rippling onboards an employee, it creates a user account in the company's identity directory, then pushes SCIM provision requests to every connected application: Slack gets a new user, GitHub gets a new organization member, Salesforce gets a new account, Zoom gets a new license. When the employee is offboarded, SCIM deprovision requests revoke all of this in the reverse order.

The "what they can access" is the harder problem. Access rights are determined by a combination of the employee's role, their department, their location, their employment type, and sometimes individual grants or exceptions. Rippling models this as a policy graph: nodes are employees, groups, resources, and permissions; edges encode membership and grant relationships. Evaluating whether a given employee should have access to a given resource traverses this graph, applying the policies in priority order.

SSO integration (Okta-compatible SAML and OIDC) means that Rippling can act as the identity provider for every application in a company's stack. When an employee logs into Salesforce, Salesforce redirects to Rippling's SSO endpoint, which authenticates the employee and issues a SAML assertion granting access. This gives Rippling real-time control over access: revoking an employee's SSO session terminates their active sessions in every connected application simultaneously.

The engineering challenge is consistency at the access boundary. The SCIM provisioning model is eventually consistent — it takes time to push provision requests to every application, and during that window, an employee might exist in Rippling's directory but not yet in Salesforce. The SSO model is synchronous — access is granted or denied at authentication time based on the current policy graph state. Building a system that is operationally consistent across both models, handles provisioning failures gracefully, and provides an audit log of every access grant and revocation requires careful design of the event pipeline, retry logic, and compensation mechanisms.

---

## Interview Implications: What Rippling Actually Evaluates

Rippling is publicly known for an unusually high hiring bar. Rejection rates are high even for candidates with strong FAANG experience. Understanding what they actually evaluate changes how you prepare.

Rippling's system design bar is domain-aware. A generic distributed systems answer — "use Kafka for event streaming, partition by user ID, use idempotency keys for deduplication" — is necessary but not sufficient. The evaluator wants to see that you understand why the domain creates specific constraints: why payroll requires strong consistency for computation but can tolerate eventual consistency for reporting; why MDM command delivery has different reliability requirements depending on whether the command is "install this app" versus "wipe this device"; why SCIM provisioning failures need different retry strategies depending on the downstream application's idempotency guarantees.

Fundamentals remain non-negotiable. Rippling's engineering bar includes strong algorithms and data structures evaluation — not LeetCode grinding for its own sake, but a genuine test of whether you can reason about computational complexity when the domain complexity is already high. An engineer who cannot reason about algorithmic trade-offs will not be able to evaluate whether a rule engine evaluation approach is efficient enough to run on payroll batches of 50,000 employees in a four-hour window.

The clearest preparation signal is this: Rippling hires engineers who have thought about business domain complexity as an engineering problem, not just as product requirements. The companies that built siloed HR, IT, and finance systems did not fail because of bad engineering — they failed to see that the data model was the product. Demonstrating that you understand why integration is hard, and how to build systems that make it tractable, is the difference between a strong candidate and a hire at Rippling.
