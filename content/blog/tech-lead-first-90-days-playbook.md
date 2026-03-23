---
title: "Tech Lead First 90 Days Playbook"
description: "A practical playbook for newly promoted tech leads—how to establish technical direction, build team trust, navigate the IC-to-lead transition, and avoid the most common first-time tech lead mistakes."
date: "2026-03-21"
category: "Career Guides"
---

# Tech Lead First 90 Days Playbook

Being promoted to tech lead is one of the most significant transitions in an engineering career. The skills that made you an excellent senior engineer — technical depth, reliable execution, good judgment — are necessary but insufficient for the tech lead role. The job description changes in ways that aren't always well-communicated.

This playbook covers the first 90 days.

## Understanding the New Job

Before anything else: clarify what "tech lead" means at your company. The title means different things in different organizations:

- At some companies, tech lead is a pure technical role (no people management, all architecture and technical direction)
- At others, it includes line management of 3-6 engineers
- At many, it's a hybrid: technical ownership + coaching without direct management authority

Know which version you've been handed. If it's unclear, ask your manager explicitly. The ambiguity often has a cost: tech leads who think they're in one role but are being evaluated on another will fail quietly.

## The First 30 Days: Listen Before You Lead

The most common new tech lead mistake: arriving with a change agenda before you've earned the right to implement one. Engineers who were your peers yesterday will not automatically accept your technical direction because of a title change.

**Days 1-30 are for listening**:

- Schedule 1:1s with every engineer on the team (30 minutes each)
- Listen: What's working? What's frustrating? What's the biggest technical problem they'd solve if they could?
- Read the codebase areas you don't know well
- Understand the product roadmap and how the technical work maps to it
- Identify the team's current technical pain points (what slows them down most?)

**Ask your manager**:
- What does success in this role look like in 6 months?
- What's the most important technical problem I should prioritize?
- What should I avoid doing?

The listening period builds the trust and context that your future technical direction will need.

## The Technical Vision

By day 60, you should have a draft of a technical vision document:
- Where is the system now (honest assessment)
- Where does it need to be in 18-24 months (aligned with product roadmap)
- What are the 3-4 technical bets that will get it there

This document should be co-created with the team, not handed down. Share a draft, get feedback, iterate. The process of creating the vision is as valuable as the document itself — it aligns the team around a shared understanding.

**Avoid**: grand technical ambitions that don't connect to product outcomes. "We should rewrite this in [language]" without a clear product reason will lose team engagement and management support.

## Running Technical Decision-Making

Tech leads own technical decisions. How you make them determines team trust:

**For small decisions** (implementation within your own code): Make them. Don't over-consult.

**For medium decisions** (architecture within a feature): Propose, discuss with affected engineers, decide. Document the reasoning.

**For large decisions** (cross-team impact, hard to reverse): Write an RFC, get broad review, make a clear decision with documented reasoning.

**The golden rule**: Separate "deciding" from "consulting." You can and should consult widely. But decision authority must be clear. Teams that don't know who decides get stuck in endless discussions.

## Managing Technical Debt Priorities

You'll quickly inherit a backlog of technical debt. You cannot address all of it. Framework for prioritization:

**Severity**: How much does this slow feature delivery? How high is the incident risk?

**Remediation cost**: How long will fixing this take?

**Payback period**: Cost / ongoing_friction_reduction → months to payback

Address high-severity, low-cost items first. Make a quarterly case to your manager for the high-severity, high-cost items (budget them formally).

Explicitly deprioritize low-severity items — it's okay to say "we're not addressing this this year." Clear deprioritization is better than ambiguous "we'll get to it eventually."

## The IC Transition: What to Give Up

The hardest part of the tech lead transition: giving up some of your individual coding time.

In the first 90 days, you should be coding less and thinking more about:
- Unblocking others (your code review turnaround time is now a team velocity issue)
- Technical direction (writing the vision, the RFCs, the architecture docs)
- Communicating upward (translating technical work into product and business terms)

This feels wrong at first. You were promoted for your technical excellence; stepping back from coding feels like regressing. It's not. Your leverage is multiplied when your decisions and unblocking enable 5 engineers to move faster — not when you personally ship one more feature.

**What you must protect**: Some coding time. Tech leads who stop coding lose credibility and lose the practical understanding of their system that makes their technical direction valuable. Aim for 30-40% of your time in code; accept that it's less than before.

## Building Trust with Your Former Peers

You were promoted over engineers who may be equally capable. This creates social complexity that most tech lead advice ignores.

**Be explicit about the relationship change**: "My role has changed, but I still see you as peers and I want your input on technical decisions" — said explicitly, not assumed.

**Don't over-authority**: The worst new tech leads become the most hierarchical people in the room. You have influence through competence and relationship, not title.

**Give public credit generously**: When an engineer's idea improves a design, say so. In team meetings, in code review, in your communication with stakeholders.

**Address the resentment directly if needed**: If a specific engineer is visibly resistant to your leadership, have a private, direct conversation. "I noticed some tension around the technical direction on X — I'd like to understand your perspective." Don't let it fester.

## The 90-Day Review

By day 90, you should have:
- A written technical vision document (even a draft) aligned with the product roadmap
- A prioritized list of the top 3-5 technical investments for the next 6 months
- A reputation within the team for fair, transparent decision-making
- A clear read on each engineer's strengths and development needs

This is a starting point, not an endpoint. The tech lead role is one of continuous learning — about systems, people, and organizational dynamics simultaneously.
