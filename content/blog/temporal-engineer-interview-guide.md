---
title: "Temporal Engineer Interview Guide: Workflow Orchestration & Durable Execution"
description: "Prepare for Temporal engineering interviews with coverage of durable execution, workflow determinism, activity patterns, SDK usage, and compensation data for 2026."
date: "2026-03-20"
category: "Company Interview Guides"
---

# Temporal Engineer Interview Guide: Workflow Orchestration & Durable Execution

Temporal has become one of the most sought-after platforms in backend infrastructure. Companies like Netflix, DoorDash, Stripe, and Snap rely on it to coordinate long-running business logic without losing state on failure. If you're interviewing for a Temporal engineering role — either at Temporal the company or at an organization adopting it — this guide covers exactly what to expect.

## What Temporal Actually Is

Temporal is a durable execution engine. The core idea: your workflow code runs as if it's a regular function, but Temporal persists every state transition to its event history. If a worker crashes mid-execution, Temporal replays the history and resumes from where it left off — your code sees no difference.

This differs fundamentally from task queues like Celery or Sidekiq, which deliver jobs to workers with no built-in state persistence. It also differs from Airflow, which is a DAG scheduler optimized for batch data pipelines rather than arbitrary application logic. Temporal's execution model is closer to virtual threads for distributed systems — the developer writes sequential code, and the platform handles fault tolerance.

## Core Concepts Interviewers Expect You to Know

**Workflows vs Activities:** Workflows are the coordination layer — they define the sequence of operations and must be deterministic. Activities are the side-effectful units of work: HTTP calls, database writes, sending emails. Activities can be retried independently, and their results are cached in the event history.

**Determinism constraints:** Workflow code must be deterministic because Temporal replays it. This means no direct calls to `time.Now()`, `rand.Intn()`, or external APIs inside workflow functions. Instead, use `workflow.Now()` and call those operations as activities. Interviewers often ask candidates to spot determinism violations in code snippets.

**Signals and queries:** Signals allow external processes to send events into a running workflow asynchronously. Queries allow read-only inspection of workflow state. These are fundamental for building interactive workflows — for example, a human approval step implemented as a signal wait.

**Child workflows:** Temporal supports spawning child workflows from a parent, useful for fan-out patterns or encapsulating logical sub-processes. Understanding when to use child workflows versus activities is a common interview discussion point.

## Interview Focus Areas

**SDK knowledge (Go and Java):** Temporal's primary SDKs are Go and Java, though TypeScript and Python SDKs exist. Expect to write workflow and activity code on a whiteboard or in a collaborative editor. Common tasks include implementing retry logic, handling signals, and structuring saga-style compensation flows.

**Workflow versioning:** When you deploy new workflow code, in-flight workflows are still replaying old history. Temporal's `workflow.GetVersion()` API lets you introduce branching logic to handle both old and new execution paths without breaking determinism. This is a nuanced topic that separates experienced Temporal engineers from novices.

**Sagas and compensation:** Temporal is frequently used to implement the saga pattern — where a long-running transaction consists of a series of steps, each with a compensating action that can undo it on failure. Expect to design a saga for a payment flow or order fulfillment process.

**Visibility and observability:** Temporal's visibility layer (backed by Elasticsearch or the SQL visibility store) allows querying workflow state. Interviewers may ask about structuring search attributes and building operational dashboards.

## Sample Interview Questions and Answers

**Q: Why can't you call `time.Sleep()` directly in a workflow?**
A: `time.Sleep()` is a system call that blocks the goroutine and doesn't integrate with Temporal's event history. You'd use `workflow.Sleep()` instead, which creates a timer in Temporal's state machine and survives worker restarts. When the workflow replays, the timer is resolved from history rather than re-executing.

**Q: How do you handle a third-party API that has no retry mechanism and sometimes returns transient 503 errors?**
A: Wrap the API call in an activity with a configured `RetryPolicy` — set `MaxAttempts`, `InitialInterval`, and `BackoffCoefficient`. The activity executes outside the workflow's replay path, so retries are safe regardless of determinism constraints.

**Q: Explain the difference between a workflow timeout and an activity timeout.**
A: Workflow timeouts (`WorkflowExecutionTimeout`, `WorkflowRunTimeout`) govern the entire workflow. Activity timeouts (`ScheduleToCloseTimeout`, `StartToCloseTimeout`, `HeartbeatTimeout`) govern individual activity executions. Heartbeat timeouts are particularly important for long-running activities — they detect stuck workers faster than the full schedule-to-close timeout.

## Compensation and Culture

Temporal the company is Series B and engineering-driven. Compensation for senior engineers in San Francisco ranges from **$180K-$250K base**, with total comp including equity reaching $300K+ at senior and staff levels. For engineers using Temporal at adopting companies, specialized knowledge commands a **15-25% premium** over equivalent distributed systems roles.

The interview process at Temporal itself typically includes a systems design round focused on workflow orchestration use cases, an SDK coding round, and a distributed systems fundamentals discussion covering consistency, failure modes, and CAP tradeoffs.

The key differentiator Temporal values: engineers who understand the tradeoffs between durability and performance, and who can reason about execution semantics under partial failure.
