---
title: "Designing a Distributed Task Scheduler"
description: "How to build a distributed task scheduler like Celery, Temporal, or AWS Step Functions—job queues, at-least-once execution, cron scheduling, and fault tolerance at scale."
date: "2026-03-21"
category: "System Design"
---

# Designing a Distributed Task Scheduler

Every large-scale application needs background job processing: sending emails, processing uploads, running reports, syncing data. A distributed task scheduler coordinates this work across many workers. Understanding its design—and the subtle correctness requirements—is essential for senior engineering interviews.

## Requirements

**Functional:**
- Submit one-time tasks (execute ASAP)
- Schedule recurring tasks (cron expressions)
- Task dependencies (task B runs after task A succeeds)
- Retry logic with configurable backoff
- Task status visibility (dashboard + API)
- Cancel running tasks

**Non-functional:**
- At-least-once execution (never lose a task)
- Exactly-once semantics where possible (for idempotent tasks)
- Scale: 1M tasks/day, 10K concurrent workers
- Task latency: < 1 second from submission to execution start

## Core Architecture

```
Submit API → Task Store (DB)
                 ↓
          Scheduler (polls/listens)
                 ↓
          Message Queue (Kafka/SQS)
                 ↓
          Worker Pool (autoscaled)
                 ↓
          Update Task Store → Webhook/callback
```

## Task Store

Store task state in a relational database with the following schema:

```sql
CREATE TABLE tasks (
    task_id        UUID PRIMARY KEY,
    task_type      VARCHAR(100),
    payload        JSONB,
    status         ENUM('pending','scheduled','running','succeeded','failed','cancelled'),
    priority       INT DEFAULT 5,
    scheduled_at   TIMESTAMP,
    started_at     TIMESTAMP,
    completed_at   TIMESTAMP,
    retry_count    INT DEFAULT 0,
    max_retries    INT DEFAULT 3,
    worker_id      VARCHAR(64),
    lease_expires  TIMESTAMP,  -- for at-most-once execution
    parent_task_id UUID,
    created_at     TIMESTAMP
);
```

The `lease_expires` column is key for fault tolerance (explained below).

## At-Least-Once Execution

The hardest correctness problem: what happens when a worker crashes mid-execution?

**Lease-based execution**:
1. Worker picks up task: sets `status = running`, `worker_id = self`, `lease_expires = now() + 30s`
2. Worker heartbeats every 10s: `UPDATE tasks SET lease_expires = now() + 30s WHERE task_id = ?`
3. If worker crashes: lease expires; a "watchdog" process finds expired leases and resets them to `pending`
4. Another worker picks up and executes

This guarantees at-least-once: if the worker crashes, the task runs again. For idempotent tasks, this is fine. For non-idempotent tasks (e.g., send email), implement application-level deduplication.

**Exactly-once semantics** is achievable only if:
1. The task itself is idempotent (same input always produces same side effect)
2. The task's outcome is checkpointed atomically with its completion status

## Queue Architecture

Don't use a database as the queue (polling is inefficient). Use a purpose-built queue:

**Option 1: Redis Streams** (simpler, lower scale)
- Consumer groups for worker pools
- XACK for manual acknowledgment after task completion
- Redis Sorted Set for scheduled tasks (score = execution timestamp)

**Option 2: Kafka** (higher scale, better durability)
- Topic per priority tier (high/medium/low)
- Consumer group per worker pool
- Manual offset commit after task completion

**Scheduled tasks** (run at specific time):
Store in a sorted set: `ZADD scheduled_tasks {unix_timestamp} {task_id}`. A scheduler process runs every second:
```python
tasks = redis.zrangebyscore('scheduled_tasks', 0, time.now())
for task in tasks:
    publish_to_queue(task)
    redis.zrem('scheduled_tasks', task)
```

## Cron Scheduling

Cron tasks create a new one-time task on each trigger:

```python
# Cron trigger
def process_cron_jobs():
    jobs = db.query("SELECT * FROM cron_jobs WHERE next_run <= NOW()")
    for job in jobs:
        create_task(job.task_type, job.payload)
        next_run = compute_next_run(job.cron_expression, now())
        db.update_cron_job(job.id, next_run=next_run)
```

Cron expression parsing: use a library (cronparser) or implement a simplified version. The critical detail: `next_run` is computed by the scheduler, not the worker — prevents missed runs if a worker is slow.

## Worker Pool

Workers are stateless processes that pull from the queue:

```python
while True:
    task = queue.poll(timeout=5s)
    if task is None:
        continue

    with lease_manager(task, timeout=30s):  # heartbeats automatically
        handler = get_handler(task.task_type)
        result = handler.execute(task.payload)
        db.mark_complete(task.task_id, result)
        queue.ack(task)
```

Worker pools autoscale based on queue depth: if queue depth > 1000 tasks, scale up; if < 100 tasks, scale down.

## Task Dependencies (DAG Execution)

For workflows (task B after task A):

```
A → B → D
↓       ↑
C ──────┘
```

Store dependency graph:
```sql
CREATE TABLE task_dependencies (
    task_id UUID,
    depends_on UUID
);
```

When task A completes:
1. Check if any tasks depend on A
2. For each dependent: check if all its dependencies are complete
3. If all dependencies complete: transition dependent to `scheduled`

This is a simple DAG traversal with atomic state transitions.

## Priority Queues

Different tasks have different urgency:
- P0: user-facing (send confirmation email — immediate)
- P1: business-critical (fraud scan, payment processing)
- P2: batch analytics (daily reports)
- P3: maintenance (log cleanup, cache warming)

Implement as separate queues with separate worker pools. P0 workers are never used for P3 work. This prevents a batch job surge from delaying user-visible tasks.

## Dead Letter Queue

Tasks that fail beyond max_retries go to a dead letter queue (DLQ). Engineers can inspect, fix the underlying issue, and requeue. Never silently discard failed tasks.

## Observability

Key metrics:
- Queue depth per priority
- Task latency (submission → execution start)
- Worker utilization per pool
- Task failure rate per task_type
- DLQ size (growing DLQ = systemic failure somewhere)

Dashboard shows real-time queue depth, task status distribution, and slowest task types.

## Interview Tips

1. **Lease-based execution** — the watchdog + heartbeat pattern for fault tolerance
2. **At-least-once vs exactly-once** — explain when you need application-level deduplication
3. **Scheduled tasks via sorted sets** — the polling scheduler trick
4. **Priority queues as separate queues** — isolation prevents starvation
5. **DAG dependencies** — trigger-on-completion pattern

The lease expiry / watchdog pattern is the most important thing to get right — it's what separates a naive job queue from a production-grade scheduler.
