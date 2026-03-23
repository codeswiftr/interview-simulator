---
title: "The First 90 Days: How to Hit the Ground Running as a New Software Engineer"
description: "A week-by-week framework for onboarding well — how to read a codebase fast, build trust, make early contributions, and know when to challenge vs. accept what's already there."
date: "2025-06-19"
category: "Career Growth"
tags: ["onboarding", "new job", "software engineer", "career", "first 90 days"]
readTime: "10 min read"
---

Most engineering onboarding advice boils down to "be curious and ask questions." That's fine, but it doesn't tell you what to actually do in week two when you're staring at a 400k-line codebase and your first standup is in 20 minutes.

The first 90 days aren't about performing confidence you don't have. They're about building enough context to become genuinely useful — and enough trust that people want to work with you on the hard problems.

Here's a framework that works at companies of any size, for engineers at any level.

## The Three Phases

Think of the first 90 days in three distinct phases:

- **Days 1–30: Learn.** Your job is to understand, not to produce. Read, listen, ask, map the system.
- **Days 31–60: Contribute.** Start shipping small, high-quality work. Build a track record.
- **Days 61–90: Lead.** Identify gaps, propose improvements, and start taking ownership beyond your assigned tickets.

Most engineers skip phase one and rush to produce. This is the most common onboarding mistake. The cost shows up two months later when you've built something that conflicts with a decision made 18 months ago, or when you've optimized a service that's scheduled to be deprecated.

## Days 1–30: How to Read a Codebase Effectively

You can't read a large codebase top to bottom. You need a strategy.

**Start at the edges, not the core.** The most useful entry points are request handlers, queue consumers, and CLI entry points — the places where outside inputs enter your system. From there, follow a single request or job end to end. Don't try to understand everything on the first pass; just understand the happy path.

**Map the data, not the functions.** After you understand one flow, look at the data models. What are the core entities? How do they relate to each other? An engineer who understands the data model understands 60% of the system's intent, regardless of the implementation language.

**Find the load-bearing seams.** Every codebase has a handful of files or modules that everything depends on. These are usually the most commented, most tested, or most carefully structured files. Find them early — breaking them has outsized consequences.

**Ask: "What breaks on a bad deploy?"** This question usually produces a 20-minute explanation that teaches you more about the system than three days of reading. It reveals the highest-stakes subsystems, the historical failures, and the areas where the team is most careful.

**Read the commit history, not just the code.** `git log --oneline -50` on a critical file is worth more than an hour of reading the file itself. Commit messages tell you why things are the way they are — including the workarounds, the emergency fixes, and the compromises that made sense in 2021 but haven't been revisited since.

## Building Trust Quickly: The Fundamentals

Technical competence is necessary but not sufficient. You also need to be trusted — and trust is built through behavior, not skill demonstrations.

**Ask questions in public.** New engineers often ask questions privately to avoid embarrassment. Do the opposite. Ask in Slack channels, in code review, in standups. It shows intellectual honesty, and your questions often surface things that senior engineers stopped noticing years ago. "I'm new so maybe I'm missing context — why do we make two separate database calls here instead of one?" is a question everyone benefits from hearing.

**Over-communicate blockers early.** Nothing damages trust faster than going silent for three days on a task that's stuck. The moment you're blocked — on access, on a confusing behavior, on an unclear requirement — say so. The message is simple: "I've been working on X. I'm blocked because Y. I'm going to try Z in the meantime — does anyone have more context?" This shows initiative even when you're stuck.

**Document what you learn.** As a new engineer, you see the system with fresh eyes that your colleagues lost long ago. Write down what confused you and what you learned. This isn't just useful for your own reference — it becomes the onboarding documentation that didn't exist before you arrived. Teams notice this and appreciate it enormously.

**Repeat back what you heard.** In meetings, get in the habit of summarizing: "So if I understand correctly, the plan is X, and the open question is Y?" This signals engagement, catches misunderstandings early, and makes you the person who brings clarity to ambiguous discussions.

## The Small PR Strategy

The most important tactical decision you'll make in the first 30 days is what your first pull requests look like.

The instinct is to show what you can do — ship something impressive. Resist this. Your first PRs should be small, surgical, and impeccable.

A small PR isn't a sign of low ambition. It's a signal that you understand how to scope work, write a clear description, anticipate review questions, and ship without introducing risk. Senior engineers who review your early work aren't looking for impressive — they're looking for reliable.

Ideal first PRs:
- Fix a bug that's been in the backlog (low risk, high goodwill)
- Add a test for existing behavior (pure upside, zero risk)
- Clean up a confusing variable name or add a comment (shows you're reading the code deeply)
- Add a small, well-scoped feature to a non-critical path

Write PR descriptions as if the reviewer knows nothing about your task. State what changed, why, and what you tested. Link to the ticket. Flag anything you're uncertain about. This alone puts you ahead of most engineers at any level.

## Week-by-Week Framework

**Week 1:** Set up your environment, run the test suite, deploy a change to a non-production environment. Meet your immediate team. Ask your manager: "What does success look like in 30, 60, and 90 days?" Write down the answer and revisit it.

**Week 2:** Follow a single request end-to-end through the system. Identify the three most critical services or modules. Read the last 30 commit messages on each. Map the data model on paper.

**Week 3:** Identify one small, well-scoped task you can own completely. Start it. Ask for a code review from someone you haven't worked with yet — this is a relationship-building move as much as a technical one.

**Week 4:** Ship your first PR. Ask for feedback on the PR itself, not just the code — was the description clear? Was the scope right? Use the answer to calibrate future PRs.

**Weeks 5–8:** Take on progressively larger tasks. Aim for one completed ticket per sprint minimum. Start attending architecture discussions or design reviews even as an observer. Ask one clarifying question per meeting so you're visible without being disruptive.

**Weeks 9–12:** Identify something that could be improved — a piece of tech debt, a missing test, a process that slows the team down. Write a short proposal (a paragraph, not a doc) and share it with your manager. This is the transition from "contributor" to "owner."

## Navigating Team Politics and Implicit Power

Every team has a social structure that doesn't appear on any org chart. There are engineers whose opinion shapes decisions regardless of title. There are ongoing disagreements about architecture or process. There are historical decisions that nobody is happy with but everyone has stopped fighting about.

Learning this structure takes time, but you can accelerate it:

- Watch who people look at in meetings when someone raises a hard question.
- Notice whose code reviews tend to be most detailed and whose comments most engineers defer to.
- Ask your manager early: "Are there any ongoing debates or tensions I should know about as context?"

You're not collecting this information to play politics. You're collecting it so you don't accidentally step into a minefield by reopening a resolved debate in your first week, or by proposing something that was tried and failed 18 months ago.

## When to Challenge vs. When to Accept

A common mistake: new engineers who see something they disagree with either stay silent indefinitely or push back immediately and loudly. Both extremes cost you.

**In the first 30 days:** accept almost everything. You don't have enough context to know why things are the way they are. Your job is to understand, not to optimize.

**Days 31–60:** start asking questions in the form of curiosity rather than challenge. "I noticed we do X — I'm trying to understand the reason. Was it a performance constraint, or something else?" This gives the team room to explain (and often, they'll surface the tension themselves).

**Days 61–90:** propose, don't push. Write up your observation and a concrete alternative. Share it with your manager first. If they think it's worth raising, do it. If there's context you're missing, you'll learn it without having made it a public debate.

The engineers who gain influence fastest aren't the ones who challenge everything — they're the ones who challenge the right things at the right time, with enough context to make the argument credibly.

## The Underlying Goal

All of this comes down to one thing: becoming the person your teammates instinctively trust with the hard problems. That reputation is built slowly, in the small moments — the well-scoped PR, the early blocker communication, the question that made everyone think.

At 90 days, you won't know the whole system. That's fine. What you'll have is a clear picture of where you can add the most value, a set of relationships with the people who can help you do it, and a reputation for being reliable. That's the foundation everything else gets built on.

---

*Want to practice the communication skills that accelerate onboarding — handling ambiguous tasks, asking for help without losing credibility, navigating difficult technical conversations? Interview Simulator's behavioral practice scenarios cover exactly these situations.*
