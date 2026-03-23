---
title: "How to Write Technical RFCs That Get Approved"
description: "A practical guide to writing effective technical RFCs—structure, common mistakes, how to build consensus before publishing, and using RFCs as a career development tool."
date: "2026-03-21"
category: "Career Guides"
---

# How to Write Technical RFCs That Get Approved

RFC stands for Request for Comments. Technical RFCs are proposals for significant engineering changes, reviewed and approved before implementation. They're used at companies like Google, Meta, Stripe, and most mature engineering organizations as the primary vehicle for technical decision-making.

Writing a good RFC is a high-leverage skill. A strong RFC gets your proposal approved, builds organizational credibility, and creates lasting documentation of important decisions.

## When to Write an RFC

Write an RFC when:
- The change affects more than one team or system
- Multiple reasonable implementation approaches exist
- The decision will be hard to reverse
- Alignment across stakeholders is required before implementation
- The work will take > 2 engineering weeks

Don't write an RFC for:
- Well-understood implementation details
- Changes within your own team's domain
- Bug fixes without design implications
- Urgent hotfixes (ship, then document)

## The RFC Structure

A robust RFC template:

```markdown
# RFC: [Title]

**Status**: Proposed / In Review / Accepted / Rejected / Superseded
**Author(s)**: @your-name, @co-author
**Reviewers**: @person1, @person2
**Created**: 2026-03-21
**Last Updated**: 2026-03-21

## Summary

One paragraph: what is this proposal and what problem does it solve?

## Motivation

Why does this need to change? What's the current pain point?
Include data where possible (incident rate, latency numbers, development friction metrics).

## Proposal

Describe your proposed solution in detail.
Include:
- Architecture diagrams
- API contracts or schema changes
- Migration strategy
- Rollout plan

## Alternatives Considered

List 2-3 alternatives you evaluated, with honest pros and cons for each.
This is critical — it demonstrates you've thought broadly and chose this approach deliberately.

## Impact and Risks

- What teams are affected?
- What can go wrong? How do you mitigate it?
- Performance implications?
- Security implications?
- Backward compatibility?

## Implementation Plan

- Phase 1: [scope] [timeline]
- Phase 2: [scope] [timeline]
- Success metrics: how will you know it worked?

## Open Questions

List unresolved questions. Invite input. Shows intellectual honesty.
```

## The Motivation Section Is the Most Important

Engineers often start RFCs by jumping to the proposal. This is a mistake. Reviewers who don't feel the problem won't engage with the solution.

Make them feel the problem first:

**Weak motivation**: "Our current API design is outdated and hard to work with."

**Strong motivation**: "Over the past 6 months, we've had 8 incidents related to the payment service API. Three of those were caused by undocumented edge cases in the current API contract. Engineers on the checkout team report spending 2-3 hours per sprint debugging API integration issues. The current design also requires 4 round trips for the most common operation, adding ~200ms to our checkout latency."

Data, specificity, and business impact get attention.

## Alternatives Considered: Don't Skip This

The most common RFC failure: describing only your proposed solution without alternatives. This reads as advocacy, not analysis. Reviewers will often reject or delay a RFC specifically to ask "did you consider X?"

**Preempt this**: Include 2-3 alternatives with honest pros/cons. Your proposed solution should win based on the analysis, not by being the only option presented.

A reviewer who sees "I considered alternatives A, B, and C, and here's why they fall short" is far more likely to trust your recommendation than one seeing a single uncontested proposal.

## Building Consensus Before You Publish

The biggest RFC mistake: publishing to a wide audience cold, without prior alignment. This leads to heated comment threads, stalled decisions, and political dynamics that could have been avoided.

**The pre-RFC sequence**:
1. **Talk to 2-3 skeptics first**: Find the engineers most likely to object. Discuss your idea with them informally. Incorporate their concerns into the RFC before publishing. This turns critics into co-authors and surfaces objections early.

2. **Align your manager and tech leads**: Get buy-in from decision-makers before the RFC goes wide. They can champion it (or tell you it's DOA, saving you the public rejection).

3. **Share a draft with trusted peers**: 2-3 people who can give you early feedback on clarity, completeness, and gaps.

4. **Publish with clear reviewers named**: "I'd specifically like feedback from @alice (auth impact), @bob (database migration), and @carol (frontend impact)" gives structure to the review.

## Responding to RFC Feedback

**Respond to every substantive comment**: Even if you disagree. "I considered this and here's why I'm not taking this approach" is better than silence.

**Update the RFC**: When feedback improves your understanding, update the proposal. Track changes in a "Revision History" section.

**Know when to close debate**: At some point, a decision must be made. If consensus isn't emerging after 2-3 rounds, escalate to a named decision-maker: "We've had good discussion but haven't converged. I'd like @director to make the call."

## Common Failure Modes

**Too long, too detailed**: A 20-page RFC with detailed implementation code gets skimmed. Keep the proposal focused on the "what" and "why" — implementation details belong in code, not the RFC.

**Vague problem statement**: "Improve our data architecture" without specific problems described. No one can evaluate a proposal against a vague requirement.

**Ignoring organizational dynamics**: Who owns the affected systems? Who will be doing the implementation work? Who are the senior technical voices whose buy-in matters? RFCs exist in a social context, not just a technical one.

**Writing the RFC to win, not to decide**: An RFC should genuinely invite alternatives and input. If you're just using it to rubber-stamp a decision already made, people will sense this and it will undermine trust.

## RFCs as Career Artifacts

A track record of well-written RFCs that drove important technical decisions is powerful career evidence:
- Shows senior/staff-level thinking (analyzing options, weighing tradeoffs, driving consensus)
- Demonstrates communication ability beyond code
- Creates permanent documentation of your technical reasoning
- Generates visibility across teams who reviewed and approved your proposals

Keep an index of RFCs you've authored. Reference them in performance reviews, in job searches, and in conversations about senior IC promotion. They're tangible, specific evidence of impact that resumes alone can't provide.
