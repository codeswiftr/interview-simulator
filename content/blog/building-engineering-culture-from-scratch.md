---
title: "Building Engineering Culture from Scratch"
description: "How to build a healthy engineering culture at an early-stage company—hiring standards, technical practices, communication norms, and the specific decisions that compound into culture over time."
date: "2026-03-21"
category: "Career Guides"
---

# Building Engineering Culture from Scratch

Culture is not what you say — it's what you do when it's inconvenient. The engineering culture of any company is established in its first 12-18 months by the decisions its early engineers make under pressure. Most of those decisions happen unconsciously, which is why intentional culture-building is so valuable.

## What Culture Actually Is

Engineering culture is the set of norms, expectations, and behaviors that are "just how we do things here." It includes:
- How decisions are made (consensual? top-down? RFC-based?)
- How quality is enforced (code review? tests required? optional?)
- How failure is handled (blame-free post-mortems? silent blame?)
- How growth works (people get promoted by tenure? by demonstrated impact?)
- How work-life balance is treated (always-on expectation? explicit boundaries respected?)

These norms are not stated in your employee handbook. They're inferred from what gets rewarded, what gets tolerated, and what the leaders model.

## The First Decision: Who You Hire

Culture is made of people. The single most powerful cultural act is the hiring decision. Every engineer you hire either strengthens or degrades the culture you're trying to build.

**Define your engineering values before your first hire**:
- Are you optimizing for speed or quality? (Both matters, but in what ratio at this stage?)
- Do you want specialists or generalists?
- What behaviors are culture-adds vs culture-mismatches?

Write these down. Make them explicit. Use them in hiring: "Tell me about a time you received critical code review feedback—how did you respond?" tests whether someone takes quality seriously and receives feedback well.

**Beware of "brilliant jerks"**: A technically excellent engineer who is condescending, dismissive of others' ideas, or who manipulates social dynamics for personal benefit will damage your culture in ways that are hard to measure but very real. The damage often exceeds their technical contribution. Be honest about this tradeoff.

## Technical Practices: Set Them on Day One

The technical practices you establish in the first month become defaults that are very hard to change later.

**Code review**: Decide whether code review is required. If yes, enforce it from the first commit. "We review everything" as a norm from the start is normal. Introducing mandatory code review after 18 months of optional review will feel like a demotion of engineers' judgment.

**Test coverage**: Decide your testing philosophy. "We write tests for everything we can" or "we write tests for business-critical paths" are both defensible. "We write tests when we have time" is a culture that will have no tests. Choose intentionally.

**Documentation**: Who writes the runbooks? Who maintains the architecture docs? If the answer is "whoever feels like it," the answer will be "no one." Assign ownership.

**On-call**: When you go to production, define your incident response process. Who is on-call? What is the escalation path? "We'll figure it out when something breaks" creates chaos. A simple on-call rotation with documented escalation paths, set up before your first incident, is a cultural statement that you take reliability seriously.

## Psychological Safety

The most important cultural variable in high-performing teams (per Google's Project Aristotle) is psychological safety: the belief that you won't be punished for speaking up, asking questions, or admitting mistakes.

Psychological safety is built or destroyed by how leaders respond to vulnerability:

**Build it by**:
- Sharing your own mistakes in retrospectives: "I made an incorrect assumption about the cache invalidation, which caused the outage. Here's what I'd do differently."
- Responding to "I don't know" with curiosity, not disappointment
- Responding to "I made a mistake" with "how do we prevent this next time?" not "why did you do that?"

**Destroy it by**:
- Criticizing engineers publicly for failures
- Responding to questions with impatience ("you should know this")
- Blaming individuals in post-mortems rather than examining systems

Psychological safety is not about comfort or the absence of accountability. Teams with high psychological safety can have high performance bars precisely because people feel safe surfacing problems early, before they become crises.

## Communication Norms

How does information flow in your team? The default (as your team grows) is: information does not flow. Everyone is in meetings all day and nobody knows what anyone else is doing.

**Decisions**:
- How are technical decisions made? Document the options, the decision, and the reasoning. An ADR (Architecture Decision Record) for significant decisions is a habit that pays dividends.
- How are product/engineering priorities set? Who has final say?

**Async communication**:
- Write things down. Meeting notes posted to Slack. Decisions documented in Notion/Confluence. This scales; memory doesn't.
- Define what goes where: quick questions in Slack, architectural discussions in RFCs, decisions in ADRs.

**Transparency level**: How much does each engineer know about the company's financial situation, strategic direction, and challenges? More transparency builds trust and helps engineers make better decisions aligned with company priorities. Many engineering culture failures come from information asymmetry: engineers making technical decisions without business context.

## Career Growth Structures

Culture includes expectations about how growth works. If you never articulate this, engineers will develop their own theories, usually inaccurate.

**Establish a simple leveling framework** once you're past 10 engineers:
- Junior: executes well-defined tasks with guidance
- Mid-level: designs and delivers features independently
- Senior: designs systems, mentors others, owns outcomes

Even a 1-page description of what these levels mean gives engineers clarity and gives you a framework for fair, consistent promotion decisions.

**Feedback cadence**: Annual performance reviews are insufficient for fast-growing teams. Quarterly feedback conversations (not formal reviews — just honest "how's it going, here's what I see") prevent surprises and accelerate development.

## The Culture Debt Trap

Technical debt is familiar—shortcuts taken under pressure that cost more to fix later. Culture debt is the same phenomenon in organizational form: norms tolerated under early pressure that become load-bearing walls you can't easily remove.

The most common culture debt items:
- No interview process (hired friends informally → inconsistent bar once you formalize it)
- No code review (every engineer sets their own quality standard → chaotic codebase)
- Always-on expectations (nobody draws boundaries → burnout at company scale)
- Undiscussable topics (leaders who can't receive feedback → systemic blindspots)

The time to prevent culture debt is now, in the first 12 months, when changing norms is relatively cheap. Culture debt compounds just like technical debt. The earlier you address it, the less it costs.

## The Leadership Obligation

If you're the senior or founding engineer, you are the primary culture setter—not HR, not the CEO, not a team offsite. You set culture by what you do, what you reinforce, and what you tolerate.

Be the engineer you want your team to be. Write good tests. Review code thoughtfully. Document decisions. Admit mistakes in post-mortems. Treat junior engineers with respect. These are not soft skills—they're the most leveraged technical work you can do.
