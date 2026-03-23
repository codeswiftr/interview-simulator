---
title: "Database Internals Interview Guide"
description: "Deep dive interview preparation on database internals: storage engines (B-tree vs. LSM-tree), transaction isolation levels, MVCC, the WAL, query planning, and what database companies like PlanetScale, Neon, CockroachDB, and senior database engineering roles require."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Database internals interviews separate engineers who have used databases from those who understand them. Whether you are targeting a database engine role at PlanetScale, Neon, or CockroachDB, or pursuing a senior infrastructure position at a large technology company, you will be expected to reason about storage, concurrency, and query execution from first principles. This guide covers the material that consistently appears in these interviews.

## Storage Engines: B-Tree vs. LSM-Tree

Most production databases use one of two storage engine designs, and interviewers expect you to know the tradeoffs cold.

**B-Tree engines** (PostgreSQL heap storage, InnoDB in MySQL) organize data in balanced tree structures that allow O(log n) point reads and range scans. Pages are updated in place, which makes reads fast but writes expensive when page splits are required. A page split cascades upward and requires writing multiple dirty pages plus WAL entries. Under heavy random write workloads, B-tree engines suffer from write amplification and fragmentation.

**LSM-tree engines** (RocksDB, LevelDB, Cassandra, ScyllaDB) buffer writes in an in-memory structure (MemTable), flush sorted immutable files (SSTables) to disk, and merge them periodically through compaction. This design turns random writes into sequential I/O, reducing write amplification. The cost is read amplification: a point read may need to check multiple levels before finding the most recent version. Bloom filters and block caches mitigate this, but LSM-tree reads are structurally more expensive than B-tree reads for the same data volume.

When asked "which is better," the correct answer is: it depends on the workload. B-tree for read-heavy, latency-sensitive workloads; LSM-tree for write-heavy, throughput-oriented workloads.

## ACID Transactions and How Databases Implement Them

ACID is not just a checklist—each property has a concrete implementation mechanism.

- **Atomicity** is enforced through the Write-Ahead Log (WAL) and undo logs. Before modifying a page, the database writes the change to the WAL. If the transaction aborts or the process crashes mid-write, the undo log allows the database to roll back partial work. The WAL ensures that either all changes survive a crash or none do.
- **Consistency** is a shared responsibility. The database enforces structural constraints (foreign keys, unique indexes, check constraints). Application logic enforces semantic invariants the database cannot know about. Databases can only guarantee that constraints hold at commit time.
- **Isolation** is implemented primarily through MVCC (covered below). Without isolation, concurrent transactions can observe each other's intermediate states.
- **Durability** requires that committed data survives crashes. The WAL achieves this only when it is flushed to durable storage. `fsync` is the critical system call here—databases that skip it for performance (e.g., with `synchronous_commit = off` in PostgreSQL) trade durability for throughput.

## Isolation Levels and the Anomalies They Prevent

SQL defines four isolation levels. Interviewers often ask which anomaly each level prevents and what the implementation cost is.

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Write Skew |
|-----------------|-------------|----------------------|---------------|------------|
| Read Uncommitted | Possible | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Possible* | Possible |
| Serializable | Prevented | Prevented | Prevented | Prevented |

*PostgreSQL's Repeatable Read also prevents phantom reads due to its snapshot-based implementation.

**Write skew** is the subtlest anomaly. Two transactions each read a set of rows, make a decision based on that read, and write to disjoint rows—but together their writes violate an invariant that both reads assumed was true. Only Serializable isolation prevents this, typically via Serializable Snapshot Isolation (SSI) in modern databases.

## MVCC: Multi-Version Concurrency Control

MVCC is how modern databases achieve high concurrency without locking readers against writers.

In **PostgreSQL**, every row stores `xmin` (the transaction ID that inserted it) and `xmax` (the transaction ID that deleted or updated it). When a transaction starts, it takes a snapshot—a list of in-progress transaction IDs. A row is visible to the transaction if `xmin` is committed and not in the snapshot, and `xmax` is either zero or not yet committed. Updates are not in-place; PostgreSQL writes a new row version and marks the old one with the updating transaction's ID in `xmax`. This means old row versions accumulate. The `VACUUM` process (or `autovacuum`) reclaims space from row versions that are no longer visible to any active transaction.

In **MySQL InnoDB**, MVCC is implemented through the undo log. The current row version lives in the clustered index. Older versions are reconstructed by traversing undo log records linked from the row header. InnoDB's purge thread cleans up undo log entries that are no longer needed.

The garbage collection problem is a real operational concern. Long-running transactions hold back the oldest visible snapshot, preventing VACUUM or purge from cleaning up old row versions. In PostgreSQL, this manifests as table bloat and eventually transaction ID wraparound. Monitoring `pg_stat_user_tables.n_dead_tup` and long-running transactions is standard operational hygiene.

## Query Planning: Statistics, Cost Models, and EXPLAIN

A query planner's job is to find the cheapest execution plan for a SQL query. Understanding this is important for diagnosing slow queries and for convincing an interviewer you have depth beyond writing SQL.

**Statistics**: PostgreSQL stores column-level statistics in `pg_statistic`, updated by `ANALYZE`. These include the most common values, a histogram of value distribution, and correlation (how ordered the column is on disk). The planner uses these to estimate row counts for filter predicates, which directly affects plan choice.

**Cost-based optimization**: The planner assigns a cost to each candidate plan in units of disk page fetches plus CPU operations. Inaccurate statistics (stale or insufficient due to default `statistics target = 100`) produce bad row estimates, which cascade into wrong plan choices—typically choosing nested loop joins when hash joins would be faster at scale.

**Join algorithms**:
- **Nested Loop Join**: O(n*m), efficient when the inner side is small or indexed. Default for small tables.
- **Hash Join**: Builds a hash table on the smaller side, probes with the larger side. O(n+m) but requires memory for the hash table.
- **Merge Join**: Requires both sides to be sorted on the join key. Efficient when input is already ordered (e.g., from an index scan).

`EXPLAIN ANALYZE` shows actual vs. estimated rows at each node. A large discrepancy between estimated and actual rows is the primary signal of a statistics problem.

## Replication: WAL-Based and Binlog-Based

**PostgreSQL streaming replication** ships WAL records from primary to standby in near real-time. The standby replays WAL entries to maintain a consistent copy. This is physical replication—byte-for-byte identical to the primary. Logical replication (introduced in PostgreSQL 10) ships decoded row-level changes instead, allowing replication to different schema versions or across major versions.

**MySQL binlog replication** ships the binary log, which can operate in statement-based, row-based, or mixed mode. Row-based mode is reliable but verbose; statement-based mode is compact but can produce inconsistencies with non-deterministic functions. MySQL's GTID-based replication tracks transaction identifiers globally, simplifying failover.

**Replication lag** is the core operational concern. A lagging replica may serve stale reads, which is acceptable under eventual consistency but unacceptable for use cases that require read-your-writes. Monitoring replication lag and designing application logic around it (routing reads to the primary after a write, or using synchronous replication for critical reads) is a standard interview discussion point.

## Who Needs This Knowledge and How to Demonstrate It

**Database engine engineers** at companies like PlanetScale (Vitess/MySQL), Neon (serverless PostgreSQL), and CockroachDB (distributed SQL) work directly in storage, transaction, and replication code. Interviews at these companies will include implementation-level questions: how would you handle a transaction that spans network partitions, or how would you design a garbage collection mechanism that does not stall writes?

**Infrastructure engineers** at large technology companies (staff-level and above) are expected to diagnose database performance issues, evaluate storage engine choices for new systems, and reason about the correctness of replication configurations. The bar is not implementation but deep operational understanding.

To demonstrate depth in interviews: explain tradeoffs rather than just naming concepts, use concrete numbers (what does high write amplification actually cost at 100k writes/second), and connect the internals to observable symptoms (why does table bloat happen, how does it affect query performance, what does autovacuum actually do about it). Interviewers are looking for engineers who have encountered these systems under pressure, not those who memorized a glossary.
