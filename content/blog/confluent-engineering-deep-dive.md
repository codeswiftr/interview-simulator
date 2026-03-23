# Confluent Engineering Deep Dive: Kafka Internals, Cloud Architecture, and What It Takes to Get Hired

Jay Kreps, Neha Narkhede, and Jun Rao left LinkedIn in 2014 carrying a single conviction: the world's data infrastructure was fundamentally broken because it was built around databases, not streams. They had already written Apache Kafka inside LinkedIn to solve the problem for themselves. Now they wanted to solve it for everyone. Confluent's mission — "set data in motion" — is not marketing language. It is a precise engineering thesis: data at rest is dead weight; data in motion is the only data worth building systems around.

That thesis has consequences for how Confluent hires. Engineers there are expected to understand distributed systems at the level of implementation, not just API. If you want to work there, you need to know what actually happens inside the broker when a producer sends a batch, why the consumer group rebalance protocol exists, and how tiered storage decouples retention from disk capacity. This post gives you that foundation.

---

## 1. Kafka's Log-Based Architecture: Why the Commit Log Changes Everything

Kafka's central abstraction is the distributed commit log. Every topic is partitioned, and every partition is an append-only, ordered log stored on disk. Producers append to the tail; consumers read from any offset.

This is not a queue. A queue destroys a message after it is consumed. A log retains it. That distinction has architectural consequences that cascade through every downstream system that uses Kafka.

**Partitions and replication.** Each partition is replicated across a configurable number of brokers. One broker holds the leader replica and handles all reads and writes for that partition. The others hold follower replicas and replicate from the leader. The in-sync replica set (ISR) is the subset of replicas that are caught up within a configurable lag threshold. A producer ack of `acks=all` waits for every ISR member to acknowledge the write before returning success. If the ISR shrinks to one (the leader), a write can still succeed — but you have sacrificed durability. Confluent engineers understand this tradeoff at the bit level.

**Consumer groups and the offset commit protocol.** Multiple consumers can form a group and collectively consume a topic. Kafka assigns each partition to exactly one consumer in the group, guaranteeing that no two consumers in the same group process the same message. Offsets are committed back to an internal Kafka topic (`__consumer_offsets`), not to the broker's in-memory state. This means consumer position survives broker restarts. When a consumer joins or leaves a group, a rebalance is triggered. The group coordinator broker orchestrates it. This rebalance is a stop-the-world event — all consumers in the group stop processing while partitions are reassigned. Incremental cooperative rebalancing (introduced in Kafka 2.4) mitigates this by only revoking the partitions that need to move, not all of them.

**Exactly-once semantics.** Kafka's exactly-once semantics (EOS) involves three coordinated mechanisms: idempotent producers, transactional producers, and read-committed consumers.

An idempotent producer is assigned a producer ID (PID) and attaches a sequence number to every batch. The broker deduplicates retried batches using (PID, partition, sequence number). Transactions extend this: a transactional producer can write to multiple partitions atomically. It uses a two-phase commit protocol with a transaction coordinator. When the producer calls `commitTransaction()`, the coordinator writes a commit marker to every partition involved in the transaction. Consumers configured with `isolation.level=read_committed` skip records inside uncommitted transactions.

```java
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "broker:9092");
props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "my-transactional-producer-1");
props.put(ProducerConfig.ACKS_CONFIG, "all");
props.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
producer.initTransactions();

try {
    producer.beginTransaction();
    producer.send(new ProducerRecord<>("orders", key, orderJson));
    producer.send(new ProducerRecord<>("audit-log", key, auditJson));
    producer.commitTransaction();
} catch (ProducerFencedException | OutOfOrderSequenceException e) {
    // Fatal — cannot recover; close and recreate the producer
    producer.close();
} catch (KafkaException e) {
    // Transient — abort and retry the transaction
    producer.abortTransaction();
}
```

The `TRANSACTIONAL_ID_CONFIG` must be stable across producer restarts. If a new producer starts with the same transactional ID, it fences out the old one — preventing zombie producers from committing stale transactions.

---

## 2. Confluent Cloud and the Kora Storage Engine

Running Kafka as a managed service at cloud scale required Confluent to re-architect the storage layer. The result is Kora, Confluent's proprietary storage engine that powers Confluent Cloud.

Standard Apache Kafka ties retention directly to broker disk. Longer retention means more disk. More disk means larger, more expensive broker instances. At petabyte scale this is not viable. Kora's tiered storage breaks this coupling by offloading older log segments to object storage (S3, GCS, Azure Blob) while keeping only the hot tail on local disk. From the consumer's perspective, the behavior is identical — Kafka's fetch API abstracts away whether the segment is on disk or in the object store. From an operations perspective, you can now retain data indefinitely without touching broker instance sizes.

Beyond tiered storage, Kora re-architects the broker itself to be cloud-native. Traditional Kafka brokers mix compute and storage: each broker holds partition replicas on its local disk. Kora separates compute from storage. Replication is handled by a dedicated replication layer, and broker compute nodes can scale independently. A partition leader failure in traditional Kafka requires electing a new leader from the ISR and then waiting for the new leader's disk to catch up. In Kora, because storage is shared, failover is near-instantaneous — the new leader simply starts serving reads from the shared store.

Confluent Cloud also multi-tenants clusters. Multiple customers share broker infrastructure, which requires strict partition-level resource quotas enforced at the broker to prevent noisy-neighbor effects. This is a meaningful systems engineering problem: enforcing byte-rate and request-rate quotas consistently without adding measurable latency to tenant workloads.

---

## 3. ksqlDB: Stream Processing with SQL Semantics

ksqlDB is Confluent's stream processing engine. It exposes a SQL dialect over Kafka topics, handles stateful computations, and persists intermediate state to changelog topics backed by RocksDB.

The core abstraction is the duality between streams and tables. A **stream** is an unbounded sequence of events. A **table** is the materialized view of the latest value per key — a compacted projection of a stream. ksqlDB lets you create both and query either.

```sql
-- Create a stream over a raw topic
CREATE STREAM page_views (
  user_id VARCHAR KEY,
  url     VARCHAR,
  duration_ms BIGINT
) WITH (
  KAFKA_TOPIC = 'raw-page-views',
  VALUE_FORMAT = 'AVRO'
);

-- Tumbling window aggregation: views per user per 5 minutes
CREATE TABLE views_per_user_5m AS
  SELECT
    user_id,
    COUNT(*) AS view_count,
    SUM(duration_ms) AS total_duration_ms
  FROM page_views
  WINDOW TUMBLING (SIZE 5 MINUTES)
  GROUP BY user_id
  EMIT CHANGES;
```

The output of `views_per_user_5m` is itself a Kafka topic. Downstream consumers can read it like any other topic. This composability is by design — every ksqlDB query is a topology that reads from one or more input topics and writes to an output topic.

Fault tolerance is achieved through changelog topics. RocksDB state stores are backed by a Kafka topic that replays the full state on recovery. If a ksqlDB node fails, it restarts, replays the changelog from Kafka, rebuilds the RocksDB state, and resumes processing from its last committed offset. No external coordination layer is required.

The hardest problem in stream processing is windowing semantics under out-of-order data. ksqlDB supports tumbling, hopping, and session windows. All of them must decide when a window is "closed" — i.e., when late-arriving data will no longer be accepted. This is the watermark problem. ksqlDB uses stream-time (the maximum timestamp seen so far) to advance watermarks and close windows. Setting the grace period too short drops late data; too long increases latency. Knowing this tradeoff, and being able to articulate it, is exactly what Confluent interviews test.

---

## 4. Schema Registry: Evolving Data Contracts at Scale

Every message written to Kafka is serialized bytes. Nothing in the protocol enforces structure. Schema Registry solves this by providing a centralized catalog of schemas with compatibility guarantees.

Producers register schemas before writing. A schema ID (4 bytes) is prepended to every message payload. Consumers fetch the schema by ID on first encounter and cache it. Deserialization is then deterministic — even if the schema evolves, the consumer can still decode older messages using the schema ID they were written with.

The compatibility modes are precise and worth understanding at the API level:

| Mode | Guarantee |
|------|-----------|
| `BACKWARD` | New schema can read data written with the previous schema |
| `FORWARD` | Previous schema can read data written with the new schema |
| `FULL` | Both backward and forward |
| `BACKWARD_TRANSITIVE` | New schema can read data written with **any** previous schema |

Adding an optional field with a default value is backward compatible — old readers ignore the new field; new readers supply the default when reading old data. Deleting a field without a default is not backward compatible — new readers cannot reconstruct the old field's value. Renaming a field breaks compatibility in every mode unless you use Avro aliases.

Schema Registry enforces compatibility at registration time by running a compatibility check against the subject's latest schema. If the new schema violates the configured compatibility mode, the registration is rejected with an error before any producer has written a single byte. This makes schema evolution a compile-time (registration-time) problem rather than a runtime one.

---

## Interview Implications: What Confluent Actually Tests

Confluent's technical bar is high and highly specific. Interviewers are often Kafka contributors or have deep streaming systems experience. Generic distributed systems answers will not pass.

**Know Kafka internals cold.** Expect questions like: "What happens when a broker in the ISR falls behind?" (The controller removes it from the ISR; writes continue if `min.insync.replicas` is still satisfied.) "What causes a consumer group rebalance?" (Member join/leave, session timeout, subscription change.) "How does idempotent delivery work under a producer restart?" (The broker tracks (PID, sequence) per partition; a restarted producer with a new PID will not benefit from deduplication, which is why `transactional.id` must be stable.)

**System design questions emphasize streaming.** Common prompts: design a distributed message queue with at-least-once delivery guarantees; design an event sourcing system for financial transactions with exactly-once semantics; design a real-time fraud detection pipeline. For every design, ground your choices in Kafka primitives — partitioning strategy, replication factor, consumer group topology, and offset management.

**The streaming mindset.** Confluent evaluates whether you think naturally in streams, not in request-response cycles. When you see a problem involving state changes over time, your instinct should be to model it as an event log first. Databases are derived views. Events are the source of truth. This is not a philosophical preference — it is the architectural worldview that Confluent's entire product stack is built on, and they want engineers who share it.

If you walk into a Confluent interview knowing why `acks=all` is not the same as durability without `min.insync.replicas >= 2`, why exactly-once semantics require both idempotent producers and read-committed consumers, and how tiered storage decouples retention from compute cost, you are already in the top tier of candidates.
