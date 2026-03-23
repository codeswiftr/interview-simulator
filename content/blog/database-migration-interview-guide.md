---
title: "Database Migration Interview Guide"
description: "Zero-downtime database migrations, schema changes at scale, blue-green deployments, backward compatibility strategies, and how to talk about data migrations in system design interviews."
date: "2026-03-19"
category: "Technical Skills"
---

Database migrations are one of those topics where your answer immediately signals whether you've shipped production systems or only worked in controlled environments. Interviewers ask about them at the senior level for a simple reason: migrations have brought down major services at companies like GitHub, Shopify, and Cloudflare. They're not hypothetical risks. A carelessly written `ALTER TABLE` on a busy PostgreSQL table will lock every write behind it, and if that table handles user logins or payment records, you're looking at an incident within seconds.

The underlying tension is that databases are the one component in your stack where you can't just blue-green deploy your way out of trouble. Application servers are stateless — swap them and traffic flows. Schema changes are permanent, often irreversible mid-flight, and the data already there has to survive the transition. That combination of high stakes and operational constraint is exactly what interviewers want to probe.

## Zero-Downtime Migrations: The Expand-Contract Pattern

The gold standard for schema changes in a running system is the expand-contract pattern, sometimes called "parallel change." The core idea is that you never make a breaking change in a single step — you expand the schema to support both old and new shapes simultaneously, migrate the data, then contract by removing what's no longer needed.

In practice, this plays out in three phases. In the first phase, you add the new column as nullable (or with a default that doesn't break existing inserts), deploy application code that writes to both the old and new column simultaneously, and do nothing else. Your database now accepts both forms. In the second phase, you backfill existing rows — more on how to do this safely below. In the third phase, once the backfill is complete and you've verified data integrity, you deploy application code that reads only from the new column, then drop the old column in a separate migration.

The reason you need dual-write in phase one before backfilling is subtle but critical: if you backfill first and then deploy dual-write code, any row written by the old code path after the backfill completes will have a null in your new column. The sequence matters.

Feature flags tie into this cleanly. Rather than coordinating a precise deployment window, you can gate the "read from new column" behavior behind a flag. This lets you gradually shift traffic — 1%, 10%, 50%, 100% — while monitoring error rates and query performance at each step. If something looks wrong at 10%, you flip the flag off and you're back to the old behavior without touching the database.

## Large Table Migrations: Why ALTER TABLE Is Dangerous

PostgreSQL's `ALTER TABLE` acquires an `AccessExclusiveLock` for most structural changes. On a table with 500 million rows, adding a column with a default value used to mean PostgreSQL would rewrite the entire table while holding that lock — every read and write blocked until it finished. Modern PostgreSQL (12+) handles `ADD COLUMN` with a stored default without a rewrite, but renaming a column, changing a type, or adding a constraint still triggers blocking behavior.

The production-safe approach for large tables uses online schema change tools. `gh-ost` (GitHub's Online Schema Change) is the most widely deployed. It works by creating a shadow table with the new schema, replaying the binlog to keep it in sync with ongoing writes, and then doing a near-instantaneous table swap when the shadow table catches up. The actual cutover lock is held for milliseconds rather than minutes. `pt-online-schema-change` from Percona follows a similar pattern but uses triggers rather than binlog-based replication.

Understanding the shadow table approach at a conceptual level is enough for most interviews: create a copy with the new schema, stream changes from the original to the copy, catch up, swap. The interview follow-up is usually about what happens if replication lag is high or if the cutover itself fails — both cases where gh-ost has explicit abort logic that leaves the original table untouched.

## Rollback Planning

Here's the question that separates people who've actually run migrations from people who've only written them: "Your migration is 2% through a 100-million-row backfill and something goes wrong. What do you do?"

The answer depends entirely on what "wrong" means and whether you planned for it. If your migration is purely additive — new column, default null, no constraint — you can abort the backfill and roll back application code with zero data loss. The column exists but is partially populated; that's fine if your application treats null as a legitimate state.

If you added a NOT NULL constraint or changed a column type in place, rollback is much harder. This is why most experienced engineers treat forward-only migrations as the default and design rollback as an explicit planning exercise before the migration runs, not after something breaks. The pre-migration checklist should answer: what does a rollback require? Can we do it in under five minutes? Does it require its own backfill?

Practically, rollback for a bad backfill usually means stopping the backfill job, validating the state of partially migrated rows, and deciding whether to truncate-and-restart (if the migration is idempotent) or leave the partial state and fix forward. Leaving partial state is often the right call if fixing forward is cheaper than re-running everything.

## Migration Frameworks: Alembic, Flyway, Liquibase

Migration frameworks solve two problems: tracking which migrations have run against which environment, and providing a structured way to write and apply schema changes. Alembic (Python/SQLAlchemy), Flyway (JVM), and Liquibase (JVM, XML or YAML) all maintain a migrations table in the database that records applied versions.

The most important conceptual distinction is forward-only versus reversible migrations. Flyway by default is forward-only — each migration is a numbered SQL script that runs exactly once. Alembic supports `upgrade` and `downgrade` functions, which sounds appealing but creates a false sense of safety. A `downgrade` function that drops a column gives you a path back, but it destroys data in doing so. For this reason, many teams using Alembic simply leave `downgrade` unimplemented and treat all migrations as forward-only in practice.

In interviews, you're expected to know that migration frameworks handle ordering and idempotency, and that the real discipline is in how you write the migrations — not just that a tool runs them.

## The Classic Interview Scenario

"You need to add a NOT NULL column to a table with 500 million rows in a live production system. Walk me through your approach."

A strong answer has three beats. First: you can't add a NOT NULL column with no default in a single step — the database will reject any existing rows that don't satisfy the constraint. Even with a default, a naive migration will lock the table during the rewrite. So you start by adding the column as nullable with no constraint, and deploy code that populates it on every new write.

Second: you backfill existing rows in chunks — typically 1,000 to 10,000 rows per batch, with a small sleep between batches to avoid saturating I/O. You track progress by storing the last processed primary key, so if the backfill fails mid-run you can resume rather than restart. You monitor replication lag and query latency throughout; if either spikes, you slow the batch rate.

Third: once all rows are populated, you add the NOT NULL constraint. In PostgreSQL, you can use `ADD CONSTRAINT ... NOT VALID` to add the constraint without scanning existing rows, then `VALIDATE CONSTRAINT` in a separate transaction — the validation takes a weaker lock and can run while the table is live. This is one of the more obscure but genuinely useful techniques to know for interviews.

## Data Backfills in Production

A backfill is not just a migration job that runs once and finishes. In production, it's a long-running operation that competes for I/O and CPU with real traffic, can fail partway through, and has to tolerate the data it's operating on changing underneath it.

Chunked updates are the baseline: rather than `UPDATE big_table SET new_col = compute(old_col)`, you write a loop that processes rows in batches keyed off the primary key. You sleep between batches. You log progress. You design the update to be idempotent — running it twice on the same row produces the same result — so you can safely retry on failure.

The most common mistake is not having a way to track progress independently of the database. If your backfill job crashes at row 47 million and you have no checkpoint, you're starting from zero. Storing the last processed ID in a separate tracking table, a Redis key, or even a flat file gives you resumability and visibility into how far along you are.

Handling failures mid-backfill is about deciding in advance what a failed row means. If a computation fails for a specific row (bad data, unexpected null), you either skip and log it, or halt and fix the root cause before continuing. Silently skipping corrupt rows often feels pragmatic in the moment and creates data quality debt that surfaces months later in production queries. The more defensible approach is to log failures explicitly, continue the backfill, and run a reconciliation pass afterward to handle the skipped rows.

The interview goal with this topic is to demonstrate that you understand the operational reality — not just the SQL syntax, but the thinking that goes into keeping a 500-million-row migration from becoming a 3am incident.
