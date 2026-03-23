---
title: "Atlassian Engineering Interview Guide"
description: "Technical interview preparation for Atlassian: JIRA and Confluence at enterprise scale, multi-tenancy, cloud migration (server to cloud), and the structured interview process including the distinctive values-based behavioral questions."
date: "2026-03-19"
category: "Company Interview Guides"
---

Atlassian powers the way over 300,000 companies plan, track, and ship software. Jira is the backbone of engineering workflows at Fortune 500 companies and startups alike. Confluence holds institutional knowledge for hundreds of thousands of teams. Bitbucket, Trello, Loom, Atlas, and Compass round out a suite that touches nearly every part of the software development lifecycle.

If you are targeting an engineering role at Atlassian, you are preparing to work on some of the most heavily used enterprise software in the world — with all the scale, complexity, and architectural pressure that entails. Here is what you need to know.

## The Product Context You Must Understand

Atlassian products are not greenfield applications. They carry enormous legacy weight, especially Jira and Confluence, which have been running in customer data centers for over fifteen years. The company has been executing one of the largest enterprise software migrations in history: moving customers off self-managed Jira Server and Confluence Server installations onto Jira Cloud and Confluence Cloud.

This migration is not just a deployment change. It is a fundamental shift in how those products are architected, operated, and monetized. A significant portion of Atlassian engineering effort — across platform, data, and product teams — is tied to this migration. If you join, you will likely touch it in some capacity.

The company is Australian-founded and maintains offices in Sydney, Austin, New York, Amsterdam, and San Francisco. Since 2020, Atlassian has operated as Team Anywhere: a distributed-first company where no location is treated as the default. They went through significant restructuring and layoffs in 2023 and 2024 as part of a shift to focus engineering investment on cloud and AI.

## The Technical Areas That Come Up in Interviews

**Multi-tenancy at enterprise scale.** Jira Cloud hosts projects for hundreds of thousands of separate organizations, all running on shared infrastructure. You should be comfortable discussing data isolation strategies, noisy neighbor protection, and per-tenant rate limiting. The naive approach — separate databases per tenant — does not scale economically. The fully shared approach — one schema for all tenants — creates serious isolation and performance risk. Know the tradeoffs of hybrid models: shared schema with tenant partitioning, separate resource pools for large tenants, circuit breakers at the tenant boundary.

**Cloud migration engineering.** Migrating a customer's Jira Server instance to Jira Cloud means moving years of issue history, attachments, workflows, permissions configurations, and integrations. The schema differences between server and cloud are non-trivial. The constraints are strict: no data loss is acceptable, SLAs must be maintained during migration, and the customer's team may not be able to tolerate extended downtime. Be ready to discuss migration patterns — dual-write, shadow read, cutover windows — and how you would validate data integrity across the migration boundary.

**Search at scale.** Jira Query Language (JQL) powers the way users filter and report on millions of issues. Behind it is a search index that must stay consistent with a database being written to continuously by users, automation, and integrations. Be prepared to discuss how you would design a system where writes are frequent, reads are latency-sensitive, and the index can fall behind without the user noticing. Know enough about Elasticsearch and Solr to talk through tradeoffs — index refresh intervals, denormalization strategies, eventual consistency in search results.

**Permissions evaluation in hot paths.** Jira's permission model is notoriously complex: project roles, global roles, issue-level security, space permissions in Confluence, and customer-defined custom schemes layered on top. The problem is that permissions must be checked on nearly every API call, and the computation is expensive when done naively. Interviewers will probe how you would cache permission results, invalidate that cache correctly when permissions change, and handle edge cases like bulk operations where individual permission checks would kill throughput.

**Performance diagnosis.** Jira has a long-standing reputation for being slow under enterprise workloads. If you get a performance question, do not jump to solutions. Show that you know how to diagnose first: instrumentation, query plans, identifying the difference between a slow individual query and a slow aggregate load. Then talk about solutions in layers — database indexing, caching, pagination, async processing for heavy workflows.

## The Interview Process

Atlassian runs a structured process with clearly defined stages:

1. **Codescreen** — an automated coding assessment, typically timed and run asynchronously. Straightforward algorithmic problems. Clean code matters here; they review your solution, not just whether it passes tests.

2. **Technical Round** — a live interview combining algorithms/data structures with system design. Expect a Jira-scale system design question. "Design the Jira issue tracker" or "How would you build JQL search for millions of issues" are realistic prompts. Show that you can reason about scale, not just functionality.

3. **Values Round** — this is where Atlassian differentiates. Every behavioral question in this round maps explicitly to one of Atlassian's five values. They will tell you this upfront. The values are:
   - Open company, no bullshit
   - Build with heart and balance
   - Don't #@!% the customer
   - Play as a team
   - Be the change you seek

## Preparing Behavioral Answers Against the Values

Do not treat this as a normal behavioral round where generic STAR stories will do. Atlassian interviewers are evaluating whether your instincts match their values. Prepare specific stories for each value.

**Don't #@!% the customer** is the one candidates most often underprepare. They want examples where you put user needs ahead of something easier or more convenient for you — shipping a fix you did not cause, speaking up about a product decision that was going to hurt users, staying on an incident until the customer was actually unblocked (not just until your team's part was resolved).

**Play as a team** should involve cross-functional examples. Shipping something by coordinating with design, product, and another engineering team is a stronger answer than a pure engineering collaboration story.

**Be the change you seek** should be a story where you did not wait to be assigned a problem. You identified something broken, proposed a solution, and drove it. Process improvement counts here, not just feature work.

## The Australian Culture Factor

Atlassian maintains a direct, low-ego culture that traces back to its Australian origins. This means over-polished answers often land worse than honest ones. If you made a mistake and learned from it, say so plainly. If you disagree with a technical direction, say why. They value people who can hold an opinion and explain their reasoning, not people who agree gracefully.

Do not oversell. Atlassian interviewers tend to be skeptical of candidates who present everything as a success. Show them you can think critically about your own work.

## How to Prepare

Use the products. Run Jira and Confluence for a project — your own, a side project, anything. You should be able to speak naturally about workflows, issue hierarchies, JQL basics, and how Confluence spaces map to team structures. You will work on tools that engineers use daily; not knowing them is a gap.

Read the Atlassian engineering blog. They publish detailed technical posts on their cloud migration work, Jira's search infrastructure, and platform architecture decisions. These give you real signal on the problems the team is actually solving.

Map your experience to the five values before your values round. Write them down. Concrete examples, not general principles.

Atlassian is a company that has been around long enough to have real architectural debt, a customer base that is fiercely loyal and demanding, and a migration challenge that will define the next five years of the platform. The engineers who do well there are the ones who can hold the complexity of a legacy system in one hand and a clear path forward in the other.
