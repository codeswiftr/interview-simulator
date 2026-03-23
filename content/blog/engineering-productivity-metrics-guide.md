---
title: "Engineering Productivity Metrics: What to Measure and What to Ignore"
description: "A guide to meaningful engineering productivity metrics—DORA metrics, SPACE framework, what to measure for different team goals, and the metrics that actively harm engineering culture."
date: "2026-03-21"
category: "Career Guides"
---

# Engineering Productivity Metrics: What to Measure and What to Ignore

Engineering productivity measurement is one of the most contested topics in engineering management. Done well, metrics create clarity, drive improvement, and help teams communicate value. Done poorly, they optimize for the wrong things, destroy trust, and degrade quality. This guide covers what works and what doesn't.

## Why Measurement Is Hard

Engineering productivity is multidimensional and context-dependent. A team doing foundational infrastructure work looks "unproductive" by story points. A team shipping features rapidly might be accumulating technical debt that will slow them for years.

Any single metric will be gamed. When you measure lines of code, engineers write verbose code. When you measure story point velocity, estimates inflate. When you measure PR count, engineers split work into small PRs. "Campbell's Law": when a measure becomes a target, it ceases to be a good measure.

The goal is not to find the perfect metric — it's to use a small portfolio of metrics as a diagnostic tool, not as a performance evaluation tool.

## DORA Metrics: The Industry Standard

The DORA (DevOps Research and Assessment) metrics, developed by the DORA research team at Google, are the most validated productivity metrics in the industry. Four core metrics:

**1. Deployment Frequency**: How often does the team deploy to production?
- Elite: Multiple times per day
- High: Once per day to once per week
- Medium: Once per week to once per month
- Low: Less than once per month

**2. Lead Time for Changes**: Time from code committed to running in production.
- Elite: < 1 hour
- High: 1 hour to 1 day
- Medium: 1 day to 1 week
- Low: > 1 week

**3. Change Failure Rate**: % of deployments causing incidents or requiring rollback.
- Elite: 0-5%
- High: 5-10%
- Medium: 10-15%
- Low: > 15%

**4. Mean Time to Restore (MTTR)**: How quickly do you recover from incidents?
- Elite: < 1 hour
- High: < 1 day
- Medium: 1 day to 1 week
- Low: > 1 week

**Why DORA metrics work**: They measure the delivery system, not individual engineers. They can't easily be gamed without actually improving the system. They correlate with business outcomes (high performers on DORA metrics have better business performance).

## The SPACE Framework

A newer framework (from Microsoft Research and GitHub) acknowledges that productivity is multi-dimensional:

**S — Satisfaction and Wellbeing**: Are engineers satisfied with their work and their tools? Measured via surveys.

**P — Performance**: Quality and impact of output. Code review metrics, incident rate, feature usage.

**A — Activity**: Quantitative counts (commits, PRs, deployments). Useful as context, not as primary measures.

**C — Communication and Collaboration**: Code review participation, documentation quality, knowledge sharing.

**E — Efficiency and Flow**: Time in flow state, interruption frequency, CI/CD pipeline times.

SPACE is a framework for thinking comprehensively, not a scorecard. Pick 1-2 dimensions to focus on based on your team's current challenges.

## What to Actually Measure by Situation

**Situation: Team wants to ship faster**
Measure: Lead time for changes, deployment frequency
Root cause analysis: Where is time lost? (Code review bottleneck? Long CI? Manual deployment steps? Code quality slowing code review?)

**Situation: Too many production incidents**
Measure: Change failure rate, MTTR
Root cause analysis: What types of changes cause failures? Are incidents caught by monitoring or reported by users?

**Situation: Team feels overwhelmed and burned out**
Measure: Interruption rate, meeting percentage of work hours, survey-based wellbeing
Root cause analysis: Too many on-call pages? Too many ad-hoc requests? Too many meetings?

**Situation: Product asks why engineering is slow**
Measure: Lead time + feature cycle time + unplanned work percentage
Root cause analysis: Technical debt? Too many parallel tracks? Unclear requirements causing rework?

## Metrics That Harm Engineering Culture

**Lines of code**: Rewards verbose, complex code. Punishes good refactoring (which reduces lines). Never use.

**Story point velocity**: Useful for team-level planning within stable contexts. Harmful when used to compare teams, judge individuals, or set targets. Estimates are not productivity.

**Number of tickets closed**: Incentivizes closing easy tickets. Doesn't capture quality or difficulty.

**Individual commit/PR counts**: Measures activity, not output. A thorough code reviewer who writes three large features is more productive than someone who opens twenty small PRs.

**"Utilization rate"**: % of time billed to projects. Misses all the maintenance, learning, mentoring, and planning that make teams effective.

These metrics are actively used by non-engineers to evaluate engineering teams. If you're asked to report on any of these, explain why they're misleading and propose better alternatives.

## Surveys: The Missing Input

Quantitative metrics tell you what happened. Surveys tell you why. Run a quarterly developer experience survey:

- "How often can you focus for > 2 hours without interruption?" (1-5 scale)
- "How confident are you in the team's technical direction?" (1-5 scale)
- "How easy is it to deploy a change to production?" (1-5 scale)
- "What's the biggest thing slowing you down right now?" (open text)

The open text responses are often the most valuable. Patterns in "what's slowing you down" directly identify improvement opportunities.

## Communicating Metrics to Stakeholders

When reporting to product management or leadership:

**Frame as system health, not individual performance**: "Our deployment frequency is twice per month, which means product changes take 2-3 weeks to reach users. We're working on reducing this to once per day, which will cut user feedback cycles from weeks to hours."

**Connect to business outcomes**: "Our MTTR improved from 4 hours to 45 minutes this quarter, which means revenue-impacting incidents resolve 5x faster than they did 6 months ago."

**Trend over time, not absolute numbers**: A deployment frequency of once per week is bad or good depending on where it was 6 months ago. Improvement matters more than benchmarks.

The engineering teams that build the most trust with leadership are those who report honestly on their own performance — including where they're struggling — and show a credible plan for improvement. Transparency builds trust more durably than optimized metrics.
