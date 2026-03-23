---
title: "System Design: Distributed Job Scheduler — Building Celery or Kubernetes Jobs at Scale"
description: "A rigorous system design walkthrough for building a distributed job scheduler at scale — covering task queues, worker management, failure handling, cron scheduling, and the architectural decisions that separate toy implementations from production systems."
date: "2026-03-20"
category: "System Design"
---

# System Design: Distributed Job Scheduler — Building Celery or Kubernetes Jobs at Scale

Distributed job schedulers are foundational infrastructure. Celery, Sidekiq, Bull, Kubernetes Jobs, Airflow, and Temporal all solve variants of the same problem: reliably execute units of work, possibly at a specified time, across a fleet of workers. This is a system design question that rewards engineers who understand failure modes deeply — because correctness in distributed systems is fundamentally about handling failures, not the happy path.

## Clarifying Requirements

**Functional requirements:**
- Schedule one-off jobs (execute this function once, now or in the future)
- Recurring jobs (execute this every hour / every day at 9am)
- Priority queues (some jobs are more urgent than others)
- Job dependencies (Job B runs only after Job A completes)
- Retry with backoff on failure
- Job cancellation
- Status visibility: pending, running, completed, failed

**Non-functional requirements:**
- Scale: 1M jobs/day, burst to 100k jobs/hour
- Latency: jobs should start within 5 seconds of their scheduled time
- At-least-once execution (with deduplication to approach exactly-once)
- Durability: no job loss on system restart or worker crash
- Observability: query job status, view logs, alert on failure rates

## Core Architecture

```
Producers → Job API → Job Store (DB + Queue) → Worker Pool → Result Store
                           ↓
                    Scheduler (cron engine)
                    Dead Letter Queue
                    Admin Dashboard
```

## Job Store: The Heart of the System

The job store must be durable and support efficient queries for:
1. Ready-to-run jobs (status=pending, scheduled_at <= now())
2. Jobs by ID (status checks)
3. Stuck jobs (status=running, started_at < now() - timeout)

**Database choice:** A relational database (PostgreSQL) is the right choice here — not a message queue, not Redis alone. Jobs have complex state (pending → running → completed/failed/retrying), need transactions, and need to be queryable. Redis is excellent as a *queue* but poor as the *store of record*.

**Schema:**
```sql
CREATE TABLE jobs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  queue       VARCHAR(128) NOT NULL DEFAULT 'default',
  status      VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending/running/completed/failed/cancelled
  priority    INT NOT NULL DEFAULT 5,                   -- lower = higher priority
  payload     JSONB NOT NULL,
  max_retries INT NOT NULL DEFAULT 3,
  retry_count INT NOT NULL DEFAULT 0,
  scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at  TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  worker_id   VARCHAR(128),
  error       TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_ready ON jobs (queue, priority, scheduled_at)
  WHERE status = 'pending';
CREATE INDEX idx_jobs_stuck ON jobs (started_at)
  WHERE status = 'running';
```

## The Queue Layer

Workers need to be notified of new jobs without polling. Two options:

**Option A: PostgreSQL LISTEN/NOTIFY** — producers issue `NOTIFY job_available` after inserting; workers `LISTEN` and wake up. Simple, zero additional infrastructure. Scales to tens of thousands of jobs/minute. Trade-off: limited fan-out; all listeners on one Postgres connection hear the notify but only one should claim the job.

**Option B: Redis Sorted Set as queue** — `ZADD queue:default {scheduled_at_unix} {job_id}`. Workers use `ZRANGEBYSCORE` + `ZREM` to atomically claim jobs. Fast, low latency, natural priority/time ordering. Trade-off: Redis is not durable by default; requires AOF persistence or RDB snapshots. Postgres remains the store of record; Redis is a fast index.

**Recommended hybrid:** Postgres as durable store + Redis sorted set as dispatch queue. On job creation, write to Postgres AND add to Redis. On worker claim, remove from Redis sorted set and update Postgres status atomically (using a Lua script in Redis + Postgres transaction, or accept the minor inconsistency and rely on the stuck-job reaper).

## Worker Management

Workers are stateless processes that:
1. Block on the queue (BRPOPLPUSH or Redis BLPOP equivalent)
2. Claim a job (atomic: mark running + set worker_id + set timeout)
3. Execute the job function
4. Update status and store result

**Claiming a job must be atomic.** Use `SELECT ... FOR UPDATE SKIP LOCKED` in Postgres — this is the key SQL pattern for distributed queue implementations. Multiple workers can race to claim jobs; only one wins.

```sql
BEGIN;
SELECT id FROM jobs
WHERE status = 'pending'
  AND scheduled_at <= NOW()
  AND queue = $1
ORDER BY priority ASC, scheduled_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;

UPDATE jobs SET status = 'running', worker_id = $2, started_at = NOW()
WHERE id = $3;
COMMIT;
```

**Worker heartbeat:** Running workers update `updated_at` every 30 seconds. The reaper detects jobs where `status='running' AND updated_at < NOW() - 90 seconds` — these workers crashed. Reaper resets them to `pending` and increments `retry_count`.

## Failure Handling

This is where systems fail in practice:

**Worker crash mid-execution:** Detected by heartbeat timeout. Job is requeued. Result: at-least-once execution. If the job is idempotent, this is fine. If not, design jobs to be idempotent (idempotency key pattern).

**Retry with exponential backoff:** On failure, set `scheduled_at = NOW() + (2^retry_count * base_delay)`. This prevents thundering herd on transient failures.

**Dead letter queue:** After `max_retries` exhausted, move to `status = 'dead'`. These require human inspection. Expose a `/admin/dead-jobs` endpoint. Never silently drop failed jobs.

**Poison pill detection:** If a job consistently crashes workers (OOM, infinite loop), detect via `retry_count` exceeding threshold and quarantine it. Log the job payload for debugging.

## Cron Scheduler

For recurring jobs, store cron specs separately:

```sql
CREATE TABLE cron_jobs (
  id          UUID PRIMARY KEY,
  name        VARCHAR(256) UNIQUE NOT NULL,
  cron_spec   VARCHAR(128) NOT NULL,  -- "0 9 * * 1-5" (9am weekdays)
  queue       VARCHAR(128) NOT NULL DEFAULT 'default',
  payload     JSONB NOT NULL,
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ NOT NULL,
  enabled     BOOLEAN NOT NULL DEFAULT true
);
```

A single scheduler process (with leader election via a Postgres advisory lock to prevent double-firing) polls every 10 seconds, finds cron jobs where `next_run_at <= NOW()`, inserts job records, and updates `next_run_at`.

**Leader election:** `SELECT pg_try_advisory_lock(12345)` — returns true only to one process. If the process crashes, Postgres releases the lock. Other processes continuously retry. This gives you automatic failover without Zookeeper.

## Job Dependencies (DAG Execution)

For workflow-style dependencies (A → B → C):

Store parent job IDs. After job completion, check if any jobs are waiting on this job. Use a `job_dependencies` join table. A separate DAG executor process resolves readiness and queues dependent jobs.

This is the core of what Airflow and Temporal implement — Temporal additionally persists workflow state as an event log, giving you full replay capability.

## Capacity Estimation

- 1M jobs/day = ~12 jobs/second average
- Peak burst: 100k jobs/hour = 28 jobs/second
- At 100 workers × 10 concurrent jobs each = 1000 concurrent executions
- Postgres handles 10k+ INSERT/UPDATE per second easily at this scale
- Redis sorted set handles 100k+ operations/second

This architecture scales to tens of millions of jobs/day before needing sharding.

## Key Interview Talking Points

1. **At-least-once vs exactly-once:** True exactly-once requires two-phase commit or idempotent operations. For most systems, at-least-once with idempotent jobs is the right trade-off.
2. **Clock skew:** Different machines have different times. Scheduled jobs should use server-side timestamps; don't trust client-provided `scheduled_at` without bounds checking.
3. **Thundering herd:** When a scheduler comes back online after downtime, thousands of past-due jobs all become ready simultaneously. Rate-limit the release of overdue jobs.
4. **Horizontal scaling of the scheduler:** Single scheduler is a bottleneck. Use consistent hashing over job IDs to partition cron job ownership across a pool of schedulers.

The depth of failure-handling discussion here — heartbeats, stuck job detection, dead letter queues, idempotency — is precisely what separates a thorough system design answer from a superficial one.
