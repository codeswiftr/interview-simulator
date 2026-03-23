---
title: "PagerDuty Software Engineer Interview Guide"
description: "PagerDuty engineering interviews: on-call infrastructure, incident management at scale, reliability engineering, and the technical bar for SRE and backend roles."
date: "2026-03-19"
category: "Company Interview Guides"
---

## Engineering at PagerDuty

PagerDuty occupies a peculiar position in the software industry: it is a company whose entire reason for existing is to wake engineers up at 3am when something breaks. That mission shapes the engineering culture in ways that go far deeper than a branding exercise. Reliability is not a feature at PagerDuty — it is the product. Engineers there live on-call themselves, carry the same pagers their customers carry, and operate services that must be available precisely when everything else is failing. The company's tolerance for uptime compromise is essentially zero, and that mindset seeps into how they hire.

If you are used to interviewing at product-focused SaaS companies where the questions skew toward feature velocity and API design aesthetics, PagerDuty will feel different. Expect the conversation to pivot quickly toward failure modes, blast radius, graceful degradation, and what happens to your system when a dependency goes dark at peak traffic.

## The Tech Stack

PagerDuty's backend has a mixed heritage. The platform was originally built on Ruby on Rails, and Rails still powers a significant portion of the product. As the company scaled, newer services were added in Go, particularly in the data plane where latency budgets are tighter and throughput demands are higher. Kafka sits at the center of their event pipeline — ingesting millions of alert events per minute from customer integrations and routing them through enrichment, deduplication, and escalation logic. Kubernetes handles container orchestration, and PostgreSQL remains the system of record for much of the relational data around schedules, teams, and policies.

Understanding this stack matters for interviews not because you will be quizzed on Rails specifics, but because the architectural decisions made at scale reveal what the team cares about: durable messaging, backpressure handling, consumer group lag as an operational signal, and the tradeoffs involved in moving logic from synchronous request paths into async queue workers.

## What the Interview Process Actually Tests

PagerDuty interviews are organized around a mix of coding, system design, and behavioral rounds. The coding portion is fairly standard — expect LeetCode-style problems in the medium range with some graph traversal and string manipulation, but the interviewers tend to probe how you reason about edge cases more than whether you land on the optimal solution immediately.

Where PagerDuty diverges sharply from typical SaaS interview processes is in the system design and operational reasoning rounds. The questions here are not generic. They are pulled directly from the domain of incident management and reliability infrastructure.

A common prompt is to design an alert routing system. At first glance this sounds simple — receive an event, look up a policy, notify someone. But the interviewer is waiting for you to surface the hard parts: What happens when the event volume spikes 100x during a widespread outage? How do you handle deduplication across events that describe the same underlying failure but originate from different monitoring tools? What does your data model look like for escalation chains that need to retry across multiple tiers before declaring a miss? How do you ensure that notification delivery is at-least-once without flooding an on-call engineer with duplicate pages?

Another common design question asks you to model a service dependency graph for incident correlation — essentially, given a topology of services and their upstream/downstream relationships, how do you identify that five separate alerts across five different teams are all symptoms of a single database host failure? This requires you to think about graph traversal, cycle detection, confidence scoring, and the UX implications of grouping alerts automatically versus surfacing them individually for human judgment.

## SRE Versus Backend Versus Platform Roles

PagerDuty distinguishes meaningfully between these roles in interviews, and understanding the difference will help you prepare the right material.

SRE candidates are evaluated heavily on their understanding of SLIs, SLOs, and error budget policy. You should be able to articulate how you would instrument a new service, what signals you would use to define reliability, and how you would structure an incident retrospective process. Expect questions about capacity planning, runbook design, and how you have handled cascading failures in production. The bar here is not just theoretical — interviewers want evidence that you have carried the pager and made judgment calls under pressure.

Backend engineering candidates face more emphasis on API design, data modeling, and service decomposition. However, because PagerDuty's product sits on the critical path of other companies' incident response, operational concerns still surface. Expect to be asked how you would design a service that must remain available even when its database is in read-only mode, or how you would handle a Kafka consumer that is falling behind its partition offset in a latency-sensitive pipeline.

Platform engineering roles skew toward infrastructure abstraction: Kubernetes operator patterns, internal developer tooling, deployment safety mechanisms like canary releases and feature flags, and how you think about the contract between platform teams and product teams. Here, the interview often explores your experience designing systems that other engineers depend on, and your philosophy around making safe defaults easy and unsafe defaults hard.

## How to Differentiate Yourself

Most candidates who reach the system design round at PagerDuty can describe a reasonable distributed system. What separates strong candidates is the instinct to reason about failure before success. When given a design prompt, start by asking what happens when each component fails, not what happens when everything works. Enumerate your consistency tradeoffs explicitly. Talk about observability from the start — what metrics would tell you the system is healthy, and what alerts would you configure on those metrics?

PagerDuty engineers will also respond well to candidates who demonstrate genuine curiosity about the incident management domain. The product deals with deeply human problems: reducing alert fatigue, building escalation policies that match how real teams are structured, and designing notification systems that interrupt people as precisely and rarely as possible. Candidates who have thought about these problems from a user perspective — not just a systems perspective — tend to stand out. If you have built internal tooling for on-call rotation management, implemented alert deduplication logic, or written runbooks that others actually used, surface those experiences directly. At PagerDuty, operational credibility is a genuine differentiator.
