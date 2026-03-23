---
title: "Architecture Decision Records: A Practical Guide"
description: "How to write effective Architecture Decision Records (ADRs)—templates, when to write them, how to use them in code review, and building an ADR culture that captures institutional knowledge."
date: "2026-03-21"
category: "Career Guides"
---

# Architecture Decision Records: A Practical Guide

Architecture Decision Records (ADRs) are short documents that capture significant technical decisions: what was decided, why, and what alternatives were considered. They're one of the highest-ROI documentation practices available to engineering teams—and one of the most consistently skipped.

This guide explains what makes a good ADR, how to build the habit, and how to use ADRs as a career growth tool.

## Why ADRs Matter

Every codebase accumulates "archaeology"—decisions made years ago that nobody remembers. Why do we use REST here but GraphQL there? Why is the auth service a separate process? Why did we choose PostgreSQL over MongoDB for this service?

Without documentation, these decisions get revisited repeatedly—often by engineers who were not present for the original conversation and must reverse-engineer the reasoning from the code. "Why is it done this way?" consumes significant senior engineering time.

With ADRs:
- New engineers get context quickly ("read ADR-012 on the auth decision")
- Decisions aren't relitigated endlessly because the reasoning is documented
- Teams learn from past decisions (successes and failures)
- Institutional knowledge survives when engineers leave

## The ADR Format

The most widely used format (from Michael Nygard's original template):

```markdown
# ADR-001: Use PostgreSQL for the primary datastore

Date: 2026-03-21
Status: Accepted
Deciders: @alice, @bob, @carol

## Context

We are building a new financial transaction service. We need to choose a primary datastore.
The service will have complex relational queries, strict consistency requirements,
and needs to support ACID transactions for financial operations.

## Decision

We will use PostgreSQL 16 as the primary datastore.

## Rationale

We evaluated PostgreSQL, MySQL, and MongoDB.

PostgreSQL was chosen because:
- ACID compliance is essential for financial data
- We have strong team familiarity with PostgreSQL
- JSONB support allows flexible schema for metadata fields without sacrificing relational structure
- Better support for complex queries (CTEs, window functions) than MySQL
- Extensive ecosystem for migrations, ORMs, and monitoring

MongoDB was eliminated because:
- Lacks true ACID transactions across multiple documents (even in newer versions, this adds complexity)
- Financial data has inherently relational structure that MongoDB's document model fights

MySQL was not chosen because:
- Less support for advanced SQL features we use
- Less team familiarity

## Consequences

- Team must manage PostgreSQL schema migrations (Flyway or Liquibase)
- Backup and recovery procedures need to be established
- Connection pooling (PgBouncer) will be required as we scale
- Future: if we need horizontal write scaling, we'll need to evaluate Citus or migration to a different architecture
```

## What Deserves an ADR

Not every decision warrants an ADR. General guideline: write an ADR when:

- Multiple reasonable options exist and you're choosing one
- The decision will be hard or costly to reverse
- Other teams or future engineers will be affected
- The decision involves significant tradeoffs
- You want to remember why you made this choice in 18 months

Does NOT need an ADR:
- Standard implementation details (how to write a function)
- Decisions with obvious "correct" answers
- Trivial choices (tab size, import order)

## When to Write Them

The right time to write an ADR is when you're making the decision, not after. Pre-decision ADRs (where the status is "Proposed" or "In Review") are the most valuable—they force the team to articulate options and reasoning before committing, and they invite input.

Post-decision ADRs ("we already did this, now I'm documenting it") are still valuable for capturing archaeology, but the decision quality benefit is lost.

**The RFC-ADR pattern**: Write an RFC (Request for Comments) to propose and discuss a decision. After consensus, the RFC becomes the accepted ADR. This gives you both the discussion artifact and the final decision record.

## Numbering and Filing

Keep ADRs in the codebase, not in a wiki. Common patterns:

```
docs/adr/
  ADR-001-use-postgresql.md
  ADR-002-event-sourcing-for-order-processing.md
  ADR-003-reject-microservices-for-v1.md
  INDEX.md  (overview table of all ADRs)
```

Keeping ADRs in the codebase (checked into Git):
- ADRs are versioned with the code they describe
- ADRs appear in pull requests when changed
- Searchable with the same tools used for code
- Never silently deleted (Git history)

## Handling Superseded Decisions

Decisions get reversed. Mark the old ADR as "Superseded" and link to the new one:

```markdown
Status: Superseded by ADR-015

## Update (2026-09-15)

After 18 months, we discovered that our relational queries were creating performance
bottlenecks at 100M+ users. We migrated to a hybrid approach (see ADR-015).
```

This preserves the history: you can see that you chose PostgreSQL, why, and then why you moved away from it 18 months later. This is invaluable institutional knowledge.

## ADRs in Code Review

Reference ADRs in code review:
- "This design contradicts ADR-008. Either we need a new ADR to update our approach, or we should align with the existing decision."
- "Per ADR-003, we're not introducing microservices for v1. Let's keep this in the monolith."

ADRs become living documents that shape ongoing decisions, not historical artifacts. This requires the team to actually read them—which requires keeping them accessible and well-indexed.

## The Career Angle

Writing ADRs is a high-visibility practice that builds career capital:

**It demonstrates senior thinking**: Articulating options, tradeoffs, and reasoning clearly is what senior and staff engineers do. ADRs make that thinking visible.

**It builds institutional memory**: Being the person who "wrote ADR-007 that saved us from rebuilding this twice" has reputational value.

**It scales your influence**: A well-written ADR influences decisions made by teams and engineers you'll never meet.

**It prepares you for system design interviews**: The same "options → decision → reasoning → consequences" structure that makes good ADRs makes good system design interview answers.

Start writing ADRs for your team this week. Even one ADR describing a recent technical decision creates momentum. The habit compounds.
