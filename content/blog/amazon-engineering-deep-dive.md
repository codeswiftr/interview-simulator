# Amazon Engineering Deep Dive: What They Really Want

Most interview prep for Amazon stops at "learn the 16 Leadership Principles and write STAR stories." That is the wrong frame. Amazon is not testing whether you know the LPs — they are testing whether you have actually lived them. The interviewers are calibrated to detect the difference between a candidate who memorized a framework and one who genuinely operates this way under pressure.

This guide is for engineers who want to understand the real mechanics: how interviewers score, what the Bar Raiser actually does, what the level bars mean in practice, and how to design systems the Amazon way. If you want the surface-level guide, you already have a dozen options. This one goes deeper.

---

## The Leadership Principles Are the Evaluation Rubric, Not Just the Topic

Amazon's LPs are not a PR slogan. They are the literal scorecard. After each interview, the interviewer opens a document with their assigned LP or LPs at the top, writes their observations under those headers, and assigns a hire/no-hire vote. Every question asked maps to a specific LP. This means that when an interviewer asks you about a time you disagreed with a decision, they are not making small talk — they are evaluating "Have Backbone; Disagree and Commit" and filling out a structured form.

Understanding this changes how you prep. You are not reciting stories at an interviewer. You are providing evidence for a scoring form.

### Customer Obsession: How Interviewers Score It

Customer Obsession is the first and most important LP. Interviewers scoring it look for three things: Did the candidate start from the customer and work backward? Did they make trade-offs that sacrificed short-term engineering elegance for customer benefit? Did they quantify or at least articulate customer impact?

A weak answer identifies the customer at some point in the story. A strong answer starts with the customer — the first sentence establishes who is affected and how. The best answers show that the candidate actively discovered a customer need that was not in the requirements, and built something for that rather than the spec.

Interviewers specifically watch for candidates who default to "the user wanted X." That is too shallow. They want to see: How did you know that? Did you read support tickets? Did you talk to the customer success team? Did you instrument the product and look at the data? The methodology matters as much as the outcome.

### Ownership: The Line Between SDE2 and SDE3

Ownership is where the level bar becomes visible. At SDE2, interviewers want to see that you take responsibility for your component end-to-end — you did not hand it off when the first version shipped. You monitored it, you handled the on-call incidents, you iterated based on data.

At SDE3 and above, Ownership stories need to extend beyond your direct scope. They want to see you identify a gap that nobody asked you to fill, advocate for fixing it, and drive it to resolution even when it meant uncomfortable conversations or working across teams that had competing priorities. The question is never really "did you finish the project" — it is "what did you take on that you did not have to."

A common failure mode: candidates describe ownership of a specific task, but the interviewer scores it low because everything described was within the candidate's assigned job description. Ownership at Amazon means taking responsibility for things that were not assigned to you.

### Dive Deep: The LP That Trips Up Senior Engineers

Senior engineers from companies that prize delegation often struggle with Dive Deep, because at those companies, detailed technical knowledge is handed off as you get more senior. Amazon goes the opposite direction. Principal Engineers at Amazon are expected to have hands-on familiarity with the systems two or three layers below their direct ownership.

Interviewers scoring Dive Deep are looking for moments where you went significantly below the abstraction layer you were expected to operate at, and where that depth produced a non-obvious insight or fix. The tell is specificity — they want actual numbers, actual root cause findings, actual lines of code or configuration flags that mattered.

A weak Dive Deep story: "I investigated the issue by looking at our logs and found the root cause was a database query." A strong one: "Our p99 latency was spiking to 800ms on writes every 8 to 12 minutes. I dumped the active queries during the spike window and found a VACUUM operation on our PostgreSQL table was acquiring a brief exclusive lock. We had 40 million rows and autovacuum was kicking in on a fixed schedule. I rewrote the maintenance window to trigger on dead tuple ratio rather than time, which eliminated the pattern entirely. Latency normalized within 48 hours."

Specificity is the signal. Vagueness is the disqualifier.

### Bias for Action: How to Demonstrate It Without Sounding Reckless

Bias for Action is frequently misunderstood. Candidates either interpret it as "move fast and break things," which sounds reckless, or they add so many caveats about calculated risk that the story loses its force entirely.

What interviewers want: a situation where waiting for more information or more approval would have been the easier path, and you chose not to wait. The action should be reversible where possible — Amazon explicitly values reversible decisions taken quickly over irreversible decisions delayed for consensus. The key phrase from the LP itself is "many decisions and actions are reversible and do not need extensive study." Your story should demonstrate that you understood this distinction and made the call consciously.

The best Bias for Action stories involve a deadline, a gap in information or ownership, and a decision you made with what you had. The outcome matters less than the quality of the reasoning.

---

## The Bar Raiser: What Everyone Gets Wrong

Every Amazon loop includes a Bar Raiser (BR). The BR is not your future manager's representative. They are an independent voice whose job is to protect the standard of the hiring bar company-wide.

Here is what most candidates do not know: the BR has veto power. If the BR votes No Hire, the loop will not result in a hire regardless of how many other interviewers voted Hire. The hiring manager can advocate, but they cannot override the BR. This is by design.

BRs are chosen from a pool of senior engineers and managers who have been trained specifically for the role and have completed a certification process. They are typically from a different team than the one hiring. Their interview style tends to be more probing, more abstract, and more focused on pattern recognition across all your stories — they are reading for consistency and authenticity in a way that individual interviewers are not.

What makes the BR round hard is not difficulty of content. It is depth. A BR who suspects a story is rehearsed or exaggerated will probe until the story breaks or holds. They will ask for the version of events where things went wrong. They will ask what you would do differently. They will ask about the person on your team who did not agree with your approach. These follow-up chains are where underprepared candidates fall apart — their stories do not have the texture of real experience.

Prepare for the BR by knowing your stories three levels deep. The top-level narrative, the complications and setbacks in the middle, and the honest retrospective at the end. If you can answer "what would you do differently with what you know now?" with a real answer that is not just "nothing, it went great" — you will hold up under BR probing.

---

## The SDE Ladder: What Each Bar Means in Practice

**SDE1** is the new-graduate or early-career bar. Interviewers are looking for strong coding fundamentals, ability to operate within a team structure, and clear potential. LP stories can be from internships, academic projects, or side work. The technical bar is algorithm and data structure fluency, not system design depth.

**SDE2** is the workhorse level at Amazon, and it is where most lateral hires land. The bar is genuine independence on a well-defined scope. You can take a project from design to production without being managed step by step. Your LP stories should come from professional experience at this point. System design interviews exist at this level but are scoped to components — design a URL shortener, not a global content delivery network.

**SDE3** is the point where many engineers plateau. The bar is not "very good SDE2." It is a qualitative shift toward influence and scope extension. Interviewers at this level are specifically looking for evidence that you have improved the team around you, driven technical decisions that outlasted your involvement, and operated in ambiguous spaces without requiring a defined problem. Your most powerful stories should be about things nobody asked you to do.

**Principal Engineer** is where system design and LP stories converge. You are expected to drive multi-team technical direction. The system design bar at this level is not correctness — it is trade-off articulation, organizational feasibility, and long-term maintainability. Your LP stories should involve organizational influence, not just team-level impact.

---

## Two-Pizza Teams and What They Mean for Engineering Culture

Jeff Bezos's two-pizza rule — that every team should be small enough to be fed by two pizzas — is not just an org chart preference. It has direct implications for how engineers at Amazon work.

Two-pizza teams are designed to be independently operable. Each team owns a service or a set of services end-to-end: build, deploy, monitor, on-call. There is no shared infra team that handles your deployments or a separate ops team that takes your on-call. When something breaks at 2am, it is your team's pager that fires.

This drives a specific engineering culture. Amazon engineers tend to be more operationally aware than engineers at companies with centralized SRE functions. They write runbooks. They instrument their own services. They own their own alarms. The interview question "tell me about a time you dealt with a production incident" is not abstract at Amazon — it is assumed to be something you have direct experience with.

In the interview, this culture surfaces as an expectation that candidates understand the operational consequences of their technical decisions. When you describe a system design, the Amazon interviewer is listening for: Who is on call for this? How do you know when it is unhealthy? What is the recovery path? What is the blast radius if it fails? These are not afterthought questions — they are central to how Amazon engineers think.

---

## AWS vs. Consumer Retail: Two Different Worlds Inside One Company

Amazon is not a monolithic engineering culture. The AWS and Consumer Retail sides have meaningfully different technical expectations.

On AWS, you are working on infrastructure that runs a significant fraction of the global internet. The reliability bar is correspondingly higher. Your failure modes affect paying enterprise customers who have SLAs. The system design problems you will encounter — multi-region replication, consistency models, hardware failure at scale, blast radius isolation — are not theoretical. Engineers on AWS teams are expected to have deep distributed systems intuition, not just familiarity.

On the Consumer Retail side (search, recommendations, personalization, fulfillment), the scale is also massive but the engineering problems are different. Here the challenges are real-time processing of enormous event streams, machine learning inference pipelines, inventory and logistics optimization, and building customer-facing systems that work globally with subsecond response times.

When you choose which Amazon role to target, match your experience to the domain. If your background is database internals, networking, or infrastructure engineering, lean AWS. If your background is consumer products, recommendation systems, or large-scale data pipelines, lean retail. Your LP stories will land differently depending on alignment — an engineer whose best Dive Deep story is about TCP congestion control will be more credible in an AWS interview than a Prime Video product interview.

---

## System Design: Amazon's Order Processing System

Design Amazon's order processing system, from shopping cart to payment to fulfillment.

**Scope the problem first.** At peak (Prime Day), Amazon processes millions of orders per hour. The system must handle bursts 10x above normal load. Order processing is both time-critical (customers expect sub-second feedback) and money-critical (payment processing cannot be incorrect). These two requirements create direct tension.

**Shopping Cart Service.** The cart is a pre-order state that does not need the consistency guarantees of an actual order. Store cart data in a low-latency key-value store (DynamoDB is the natural choice at Amazon) keyed by session and user ID. Cart data can tolerate eventual consistency — if two browser tabs show slightly stale cart state, the impact is low. Carts are ephemeral: set a TTL of 30 days, and do not invest in heavy synchronization logic.

**Order Creation: The Idempotency Problem.** When a customer clicks "Place Order," you must guarantee exactly-once processing. Network failures and retries mean the same request may arrive multiple times. Assign an idempotency key (client-generated UUID) to every order creation request. Persist the key with the result of the first successful processing. Subsequent requests with the same key return the cached result without re-processing. This is the standard pattern for any financial-adjacent write in a distributed system.

**Payment Processing.** Payment is the highest-consistency component. Use a two-phase approach: first, authorize the payment (reserve the funds without capturing), then capture after inventory is confirmed. This avoids charging customers for orders you cannot fulfill. The authorization step can be done synchronously in the order creation flow with a 3-5 second timeout. Capture is asynchronous, triggered after inventory reservation succeeds.

**Inventory Reservation.** Inventory is a contended resource. Naive implementations using database row locks do not scale. Amazon's approach is probabilistic inventory with reservation queues: maintain an in-memory count with a soft buffer (if inventory shows 10, accept orders up to 12, with the extra 2 handled through supplier overflow or cancellation). Hard inventory reservation uses optimistic locking — read the current count, write the decrement only if the count has not changed since the read, retry on conflict. For high-traffic SKUs (a popular item during Prime Day), use a reservation token queue: pre-generate N tokens per SKU and hand them out. When tokens run out, inventory is exhausted.

**Fulfillment Pipeline.** Order fulfillment is a state machine: Created → Payment Authorized → Inventory Reserved → Routed to Fulfillment Center → Picked → Packed → Shipped → Delivered. Each state transition is a domain event published to an event bus (Amazon uses internal systems similar to Kinesis for this). Each fulfillment center subscribes to the events for its geographic region. This decouples order creation (latency-sensitive) from physical fulfillment (latency-tolerant).

**Failure handling.** What happens when inventory reservation succeeds but payment capture fails? Implement a saga pattern with compensating transactions. The saga coordinator tracks the state of each step. On failure, it triggers compensations in reverse order: release inventory reservation, void the payment authorization, notify the customer. Each compensation is itself an idempotent operation. The saga state is persisted to DynamoDB so recovery can continue after coordinator failure.

**Observability.** Define the critical path SLO: order-to-confirmation under 2 seconds at p99. Instrument with distributed tracing across all services. Set alarms on the order creation error rate and the inventory reservation failure rate. The fulfillment SLO is separate: first scan at fulfillment center within 24 hours for standard shipping.

---

## LP Story Framework for the Top 5 Most-Asked LPs

**1. Customer Obsession.** Open with who the customer is and what they were experiencing. Establish that you discovered this through direct evidence, not assumption. Describe the trade-off you made in their favor. Close with the customer outcome, quantified if possible.

**2. Ownership.** Set up the gap — something nobody owned, or something outside your defined scope. Explain why you chose to take it on rather than wait for someone else. Walk through the obstacles you hit that most people would have used to justify stopping. Close with the outcome and what the ongoing ownership looks like.

**3. Invent and Simplify.** This LP requires a before-and-after structure. What was the existing process or system? What made it unnecessarily complex or limiting? What was your approach, and what assumptions did you challenge? What is the simpler version, and how much complexity did you remove?

**4. Are Right, A Lot.** The best stories for this LP involve a moment where you had a strong conviction, the data or consensus was against you, and you turned out to be correct. The risk with this LP is sounding arrogant — counter it by being honest about the evidence that made you uncertain and the process you used to resolve the uncertainty.

**5. Deliver Results.** This is the LP where candidates most often oversimplify. The story should not be "we had a goal and we hit it." It should involve obstacles — technical, organizational, resource-related — that genuinely threatened the outcome. How you navigated those is the content. The result is just confirmation that the approach worked.

---

## Disagree and Commit: How to Use It in Interview Answers

"Have Backbone; Disagree and Commit" is one of the most misunderstood LPs. Candidates interpret it as permission to describe conflicts where they were right and others were wrong. That is the wrong reading.

The LP has two parts. Having backbone means you voiced your disagreement clearly and specifically, with evidence, at the right time and to the right people. Commit means that once the decision was made — regardless of whether you prevailed — you executed with full effort and without undermining the decision.

The best interview stories for this LP show both halves with equal weight. Describe how you challenged the decision. Describe the evidence or reasoning you brought. Then describe what happened when the decision went against your position. Did you vocalize the decision to the team and execute on it cleanly? Did you set up the conditions for learning whether the decision was right? Did you go back later with post-decision data?

What interviewers watch for: candidates who stop the story when the decision is made, implying they either always won the disagreement or did not actually commit after losing. Both are red flags. The genuinely strong answer includes a decision where you were overruled and describes how you acted afterward — because that is where the LP actually lives.

---

## Post-Layoff Amazon: The Culture Shift

Amazon's 2023 layoffs and the subsequent reorganization changed the operating environment. The company is more explicit now about the ownership expectation per headcount. Engineers are expected to cover more scope, with less administrative overhead and less tolerance for dependencies on other teams to get things done.

In practical terms, this means two things for interview candidates. First, your stories about scope and ownership need to reflect a genuine comfort with doing things yourself rather than waiting for support. Second, the interview bar for "are you someone who creates work for others" has risen. Interviewers are specifically watching for candidates who describe themselves as the blocking dependency, or who escalate frequently rather than resolving independently.

The culture has also shifted toward higher scrutiny on business impact. Being a strong engineer is necessary but not sufficient at Amazon now. The interview questions that end with "what was the impact?" are not rhetorical — interviewers want to hear you connect your technical work to revenue, cost, latency, or customer satisfaction in specific terms. If you cannot make that connection for your most important projects, spend time before the interview building that narrative.

---

## The Written LP Exercise

Some Amazon loops — particularly for senior roles — include a written component where you are asked to fill out an LP questionnaire before or during the process. This is not the same as a behavioral interview. It is a structured document where you match specific examples to specific LPs.

Write each LP story as a compressed STAR narrative: one sentence on situation, one on task, two to three on action, one on result. The entire example should fit in one paragraph. Avoid padding with context that does not affect the scoring criteria. The interviewers who read these documents are calibrated to value density — they want signal-per-sentence, not comprehensive storytelling.

Have six to eight core stories that you can map to different LPs depending on the angle you emphasize. A single project can yield a Customer Obsession story, an Ownership story, and a Deliver Results story if you structure the emphasis differently. This is not dishonest — it is understanding that different LPs illuminate different aspects of the same experience.

Proofread the written document more carefully than you would prep for verbal answers. The written exercise is read before your on-site. First impressions from that document influence how interviewers approach your loop. Errors in the written exercise signal carelessness — which is the opposite of what you want to communicate going into a company that values high standards.

---

## Final Honest Assessment

Amazon is a harder cultural interview than most FAANG companies because the rubric is both explicit and deeply evaluated. The explicit part works in your favor — you know exactly what is being scored. The deep evaluation part works against underprepared candidates, because the follow-up questions will expose shallow stories.

The engineers who do best in Amazon loops are the ones who have actually operated with the values the LPs describe, and who can talk about their work with the specificity and ownership that comes from genuine experience. Preparation accelerates this — it helps you recall and structure real experiences more effectively — but it cannot substitute for the underlying substance.

Start from your most impactful projects and work backward to the LPs. Do not start from the LPs and search your memory for matching stories. The first approach produces authentic, specific answers. The second produces the kind of story that BRs are trained to identify and reject.

## Related Articles

- [Amazon Interview Guide](/blog/amazon-interview-guide)
- [Amazon Leadership Principles Interview Guide](/blog/amazon-leadership-principles-interview-guide)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [Behavioral Interview Mastery: The Complete Guide](/blog/behavioral-interview-mastery-guide)
