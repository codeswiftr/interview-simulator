---
title: "Database Transactions and ACID: Isolation Levels, Deadlocks, and Concurrency Control"
description: "Deep dive into database transactions for interviews — ACID properties, isolation levels, read phenomena, optimistic vs pessimistic locking, and handling deadlocks in production."
date: "2026-03-20"
category: "System Design"
---

# Database Transactions and ACID: Isolation Levels, Deadlocks, and Concurrency Control

Database transaction questions appear in senior backend and system design interviews to test whether you understand how databases maintain consistency under concurrent access. Most engineers know ACID at a surface level; what distinguishes strong candidates is understanding the tradeoffs between isolation levels and their real-world implications.

## ACID Properties

**Atomicity:** A transaction either completes entirely or not at all. If a system failure occurs mid-transaction, the database rolls back to the pre-transaction state. Implemented via write-ahead log (WAL) — changes are written to the log before being applied to the data.

**Consistency:** Transactions maintain database invariants. A transaction that would violate a constraint (foreign key, unique, not null) is rejected. Note: application-level consistency is your responsibility — the database enforces schema constraints, not business rules.

**Isolation:** Concurrent transactions execute as if they ran serially. How strictly this is enforced is controlled by the isolation level — the central tradeoff in database concurrency.

**Durability:** Once committed, a transaction's changes persist even through system failures. Implemented via flushing the WAL to disk before acknowledging the commit.

## Isolation Levels and Read Phenomena

Three read phenomena that isolation levels control:

**Dirty read:** Reading uncommitted data from another transaction. If that transaction rolls back, you've read data that never existed.

**Non-repeatable read:** Within a transaction, reading the same row twice yields different values because another transaction committed an update between the reads.

**Phantom read:** Within a transaction, a range query returns different rows on two executions because another transaction committed inserts or deletes in that range.

The four SQL isolation levels:

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads |
|-------|------------|---------------------|---------------|
| Read Uncommitted | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Possible |
| Serializable | Prevented | Prevented | Prevented |

**In practice:** PostgreSQL defaults to Read Committed (most do). MySQL InnoDB defaults to Repeatable Read. Serializable is used when absolute consistency is required (financial transfers, inventory management) but has the highest overhead.

## Optimistic vs. Pessimistic Locking

**Pessimistic locking:** Lock the row when you read it, preventing others from modifying it until you commit. `SELECT ... FOR UPDATE` in SQL. Safe, but reduces concurrency and can cause lock contention.

```sql
BEGIN;
SELECT balance FROM accounts WHERE id = 123 FOR UPDATE;
-- Account is locked until this transaction commits
UPDATE accounts SET balance = balance - 100 WHERE id = 123;
COMMIT;
```

**Optimistic locking:** Don't lock on read. Include a version number in your update condition; if another transaction modified the row, the update finds 0 rows and the application retries.

```sql
-- Read with version
SELECT balance, version FROM accounts WHERE id = 123;
-- version = 5

-- Update only if version hasn't changed
UPDATE accounts 
SET balance = balance - 100, version = version + 1
WHERE id = 123 AND version = 5;
-- If 0 rows affected, someone else updated — retry
```

**When to use each:** Pessimistic for high-contention data (the same rows are frequently updated concurrently). Optimistic for low-contention data (conflicts are rare) — it avoids the overhead of acquiring locks on every read.

## Deadlocks

A deadlock occurs when transaction A holds a lock needed by transaction B, while transaction B holds a lock needed by transaction A. Neither can proceed.

**Detection:** Databases detect deadlocks by finding cycles in the wait-for graph and killing one transaction (the victim — chosen by lowest cost to rollback). The application must handle deadlock errors and retry.

**Prevention:** Acquire locks in a consistent order across all transactions. If every transaction locks accounts in ascending ID order, deadlocks between two accounts become impossible.

```python
def transfer(from_id, to_id, amount):
    # Always lock lower ID first to prevent deadlocks
    ids = sorted([from_id, to_id])
    with lock(ids[0]), lock(ids[1]):
        # perform transfer
```

**Monitoring:** `pg_locks` in PostgreSQL shows current locks. Deadlock events are logged — monitor for deadlock frequency as a signal of locking contention.

## Two-Phase Locking (2PL)

The theoretical foundation for serializability. A transaction first acquires all needed locks (growing phase), performs work, then releases all locks (shrinking phase). Strict 2PL holds all locks until commit/rollback — this is what most databases implement.

Understanding 2PL helps explain why serializable isolation reduces concurrency: the database must hold locks for the full transaction duration, increasing contention.

## MVCC (Multi-Version Concurrency Control)

PostgreSQL, MySQL InnoDB, and most modern databases use MVCC instead of traditional locking for reads. Each row has multiple versions (created by different transactions). Read operations see the version that was current at the transaction's start time, without acquiring any locks.

This is why reads don't block writes in PostgreSQL: the reader sees an older version; the writer creates a new version. MVCC enables high read concurrency while maintaining isolation.

The tradeoff: dead versions accumulate (the "bloat" problem in PostgreSQL). VACUUM reclaims this space — understanding when and why to run VACUUM is relevant for production PostgreSQL operations.

Mastering isolation levels, locking strategies, and MVCC demonstrates you can design systems that are both correct and performant under concurrent load — a key senior engineering skill.
