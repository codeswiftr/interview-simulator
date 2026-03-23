---
title: "Technical Writing for Engineers: RFCs, Design Docs, and Postmortems"
description: "How to write effective technical documents as a software engineer — RFC structure, design document best practices, postmortem writing, runbooks, and how writing quality affects your career progression."
date: "2026-03-20"
category: "Career Guides"
---

# Technical Writing for Engineers: RFCs, Design Docs, and Postmortems

Writing is the most underrated skill in software engineering. Senior and staff engineers spend 20-40% of their time writing — design documents, RFCs, postmortems, runbooks, ADRs. Yet most engineering education teaches code, not prose.

Good technical writing multiplies your impact. A well-written RFC influences a dozen engineers without requiring individual conversations. A clear postmortem prevents future incidents across teams. Bad writing wastes everyone's time and erodes trust in your judgment.

## The Core Principle: Write for the Reader, Not Yourself

Every technical document has a purpose and a reader. Before writing a single sentence, answer: Who will read this? What decision do they need to make? What do they need to believe to make that decision?

Failing to do this produces documents full of implementation details the reader doesn't need, missing the context they do need. The author writes to explain what they built; the reader wants to know whether to approve it, use it, or trust it.

## Design Documents

Design documents (design docs, technical specs) describe a system before or during implementation. Purpose: align stakeholders, surface concerns early, create a record of what was intended.

**Structure:**
- **Overview** (1-3 paragraphs): What is being built and why. The reader should understand the scope and motivation without reading the rest.
- **Background/Context**: Why now? What's the current state? What pain is this solving?
- **Goals and Non-Goals**: Explicit non-goals prevent scope creep and focus discussion.
- **Proposed Design**: How it works. Diagrams help. Go as deep as needed for your audience.
- **Alternatives Considered**: This is critical. It proves you thought rigorously and weren't just advocating for your first idea.
- **Open Questions**: Unresolved decisions. Surfaces what still needs input.
- **Implementation Plan**: Phases, milestones, rollback plan.

Write the alternatives section honestly. If you only had one option, say so and explain why. If you considered three options and one is clearly better, explain the tradeoffs that make it better. Weak alternatives sections ("we could use X but it would be bad") read as rationalization.

## RFCs (Request for Comments)

RFCs are process documents — they're requesting input before a decision is made. The key difference from design docs: the decision isn't made yet. An RFC's success is measured by the quality of discussion it generates and the decision it produces.

**Write the problem statement before the solution.** If your RFC opens with "I propose we use X," readers will debate X before agreeing on the problem. Open with a clear, agreed-upon problem statement. Then propose solutions.

**Set a decision deadline.** RFCs without deadlines don't close. "Comments due March 15, decision by March 22" creates urgency and respects everyone's time.

**Distinguish between bike-shedding and substantive concerns.** Some comments are preferences. Some are material objections. Acknowledge preferences ("noted, will factor in if we revisit"), address material objections ("this is a valid concern, here's how we handle it").

## Postmortems

A postmortem (incident report) documents what happened in an outage and what will prevent recurrence. Bad postmortems assign blame. Good postmortems find systemic causes.

**Timeline**: What happened, when. Keep this factual and dense — it's a reference document.

**Root cause analysis**: Why did it happen? Use "5 Whys" — ask why repeatedly until you reach something actionable. "A bug was deployed" is not a root cause. "Our staging environment doesn't replicate production database load, so performance issues aren't caught before deployment" is a root cause.

**Action items**: Specific, assigned, dated. "Improve monitoring" is not an action item. "Add an alert for p99 latency exceeding 500ms on the payment endpoint (owner: @jane, by March 15)" is.

**Blameless culture**: Never name individuals in a postmortem unless they're the owner of an action item. Blame prevents honest disclosure of future incidents. The question is never "who did this" but "what conditions allowed this to happen."

## ADRs (Architecture Decision Records)

ADRs capture architectural decisions with context. Short format: title, status (proposed/accepted/deprecated), context (why this decision was needed), decision, consequences (tradeoffs).

The value of ADRs isn't the document — it's that six months later when someone asks "why do we use event sourcing here?" there's a written record of the reasoning, including what alternatives were rejected. This prevents relitigating decided questions and accelerates onboarding.

## Runbooks

Runbooks document operational procedures: how to investigate an alert, how to restart a service, how to perform a database migration. Audience: on-call engineers, often at 2am.

Write runbooks assuming the reader is intelligent but may not know your system deeply. Include: when to use this runbook, prerequisites, step-by-step procedures with expected outputs, and escalation paths if the procedure fails.

Test runbooks by having someone unfamiliar with the system follow them. If they get stuck, the runbook is wrong.

## Writing Quality and Career Progression

Writing quality correlates strongly with career progression at staff+ levels. The reason is structural: staff engineers influence through documents, not code. An illegible RFC means your ideas don't spread. A confusing design doc creates alignment debt that slows the team.

Improve your writing by: reading good technical writing (Google's engineering practices documents, Stripe's API design philosophy, Martin Fowler's blog), getting feedback by asking a specific colleague to edit your docs with focus on clarity, and writing regularly — the only way to get better is practice.

The bar is not literary excellence. The bar is: does the reader understand what you intended? Can they act on it? Would they read the next document you write?

