# LinkedIn Engineering Deep Dive: Graph Scale, Kafka Origins, and Feed Ranking

Every social network is a graph problem. But LinkedIn's graph is not just about who follows whom — it is a professional identity layer for 950 million members, where the distance between two people carries economic weight, where a second-degree connection might be a hiring manager, and where the system must answer graph traversal queries in under 100ms at scale. That constraint — real-time graph operations on a network approaching a billion nodes — has driven nearly every major architectural decision LinkedIn has made over the past fifteen years.

This post covers what LinkedIn's engineering blog and public talks have documented about the systems under the hood: the member graph and Voldemort, feed ranking and the viral score, Kafka (which LinkedIn invented), and the data tier isolation model. If you are interviewing at LinkedIn, this is the technical foundation the interviewers assume you are familiar with.

---

## The Member Graph and Voldemort: Storage at 950M Nodes

LinkedIn's member graph is the canonical example of a graph that is too large and too hot to serve from a traditional RDBMS. The member-to-member connection table alone, at 950 million nodes with an average degree above 200, represents tens of billions of edges. Serving graph traversal queries — "find all second-degree connections of member X" — from a relational database would saturate any join operation at this fanout.

LinkedIn's answer was a dedicated graph service backed by custom storage. The underlying key-value store is **Voldemort**, an open-source distributed key-value store LinkedIn built and released in 2009. Voldemort is modeled on Amazon's Dynamo paper: consistent hashing for key distribution, tunable quorum reads/writes (R + W > N), and a pluggable storage backend (BerkeleyDB was the original backend; RocksDB is now common).

For the member graph specifically, the adjacency list is stored as a Voldemort value: member ID maps to a serialized list of connection IDs. The critical design choice is that LinkedIn stores the adjacency list in both directions — when A connects to B, both `A → [B, ...]` and `B → [A, ...]` are updated. This doubles write amplification but eliminates join operations on reads. For a read-heavy workload (feed generation, search, recommendations), this is the correct trade.

The graph service sits on top of Voldemort and handles multi-hop traversals. A breadth-first traversal for second-degree connections looks roughly like:

```python
def second_degree_connections(member_id: str, graph_client) -> set[str]:
    first_degree = set(graph_client.get_neighbors(member_id))
    second_degree = set()
    for connection in first_degree:
        neighbors = graph_client.get_neighbors(connection)
        second_degree.update(neighbors)
    # Remove first-degree and self
    second_degree -= first_degree
    second_degree.discard(member_id)
    return second_degree
```

At production scale, LinkedIn does not execute this naively. The graph service shards member adjacency lists by member ID hash, parallelizes the second-hop fan-out across shards, and applies a cap on first-degree connection count before the traversal begins. Members with extremely high degree (10,000+ connections) use pre-computed snapshots rather than live traversal.

LinkedIn also built **Expresso**, a document-oriented storage layer on top of MySQL that handles more structured member data (profiles, skills, endorsements). Expresso provides multi-tenancy, secondary indexing, and schema evolution — things that raw Voldemort does not support. The split between Voldemort (graph edges, hot path) and Expresso (document data, richer queries) reflects a deliberate tier separation that appears throughout LinkedIn's architecture.

---

## Feed Ranking: The Viral Score and Three-Feed Merge

LinkedIn's feed is not a simple reverse-chronological stream. By 2015, LinkedIn had moved to a ranked feed — what they internally called **"Updates"** — that merges three distinct sub-feeds and applies a real-time ML ranking layer.

The three feeds that merge:

1. **Network updates** — posts and activity from first and second-degree connections
2. **Followed entity updates** — content from companies, influencers, and hashtags a member follows
3. **Viral updates** — content that a connection has engaged with (liked, commented), which re-surfaces in the member's feed

The viral update stream is the most architecturally interesting. When member A likes a post by member C (who is not in member B's network), that engagement event is a candidate for insertion into member B's feed if A is in B's network. This requires a real-time join between the engagement event stream and the social graph. LinkedIn routes engagement events through Kafka, applies a graph lookup to determine which first-degree connections of the actor (A) should see the viral update, and inserts the update into a priority queue for those members' feeds.

The ranking model assigns a **viral score** to each candidate update. LinkedIn has published details of their ranking approach in engineering blog posts: the model takes features including actor-recipient relationship strength (edge weight in the social graph), content type, predicted engagement probability, recency decay, and content quality signals (spam score, click-bait detection). The model runs in real-time as a member loads their feed, scoring each candidate in the candidate set and ordering the final result.

Feed generation in pseudocode:

```python
def generate_feed(member_id: str, page_size: int = 20) -> list[FeedItem]:
    # Fetch candidates from three sub-feeds (parallel)
    network_candidates = fetch_network_updates(member_id, limit=200)
    followed_candidates = fetch_followed_updates(member_id, limit=200)
    viral_candidates = fetch_viral_updates(member_id, limit=100)

    all_candidates = network_candidates + followed_candidates + viral_candidates

    # Score each candidate
    scored = []
    for candidate in all_candidates:
        features = extract_features(candidate, member_id)
        score = ranking_model.predict(features)
        scored.append((score, candidate))

    # Sort descending and return top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:page_size]]
```

The actual production system caches candidate sets and uses incremental ranking rather than re-ranking from scratch on every request. LinkedIn's engineering posts describe a two-stage approach: a lightweight retrieval model narrows the candidate pool, and a heavier scoring model ranks the filtered set. This mirrors the retrieve-then-rank pattern common in recommendation systems at scale.

---

## Apache Kafka: LinkedIn Invented It, and Here Is Why

Kafka was built at LinkedIn in 2010 to solve a specific problem: the company had dozens of data pipelines — activity tracking, metrics, log aggregation, recommendations — all implemented as point-to-point connections between services. The result was an O(n²) integration mesh that was operationally unsustainable.

The core insight behind Kafka's design is the separation of storage from messaging. Traditional message queues like RabbitMQ delete messages after delivery. Kafka retains messages in a durable, ordered, partitioned log. Consumers maintain their own offset — a position in the log — and can read at their own pace. This means LinkedIn can attach a new consumer to a Kafka topic and replay historical events, which is impossible with traditional queues.

LinkedIn's production Kafka cluster handles approximately **7 trillion messages per day** across hundreds of clusters. The system architecture:

- **Producers** publish events to topics, partitioned by key (typically member ID or content ID)
- **Brokers** store partitioned logs on disk using a sequential write pattern (extremely efficient for spinning disks and SSDs alike)
- **Consumers** in consumer groups divide partitions among themselves, providing horizontal read scalability

A Kafka producer writing connection events might look like:

```java
// LinkedIn-style Kafka producer for member connection events
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker-01:9092,kafka-broker-02:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "io.confluent.kafka.serializers.KafkaAvroSerializer");
props.put("acks", "all");          // Wait for full replication
props.put("retries", 3);
props.put("linger.ms", 5);         // Small batching window

KafkaProducer<String, ConnectionEvent> producer = new KafkaProducer<>(props);

ConnectionEvent event = ConnectionEvent.newBuilder()
    .setActorMemberId(actorId)
    .setRecipientMemberId(recipientId)
    .setEventType(ConnectionEventType.CONNECTED)
    .setTimestampMs(System.currentTimeMillis())
    .build();

// Partition by actor ID ensures ordering for a given member's events
ProducerRecord<String, ConnectionEvent> record =
    new ProducerRecord<>("member-connections", actorId, event);

producer.send(record, (metadata, exception) -> {
    if (exception != null) {
        log.error("Failed to publish connection event", exception);
    }
});
```

LinkedIn uses Avro schemas with Confluent Schema Registry for all Kafka messages — this enforces compatibility between producers and consumers as schemas evolve, and is standard practice for large Kafka deployments. The consumer side reads from this topic to update the social graph, trigger feed updates for the recipient's connections, and feed analytics pipelines.

LinkedIn also built **Brooklin**, an internal system for mirroring Kafka streams across data centers and bridging to non-Kafka systems (HDFS, databases). Brooklin is the data movement layer that underpins cross-region replication and the handoff from real-time streams to batch processing.

---

## The Isolation Layer: Li-Fi and Data Tier Separation

As LinkedIn scaled, a recurring failure mode emerged: a slow analytics query on production data would cause latency spikes for user-facing APIs sharing the same database cluster. LinkedIn's architectural response was a strict **data tier isolation** model, sometimes referred to internally as Li-Fi (LinkedIn's federated infrastructure).

The core principle: **online** (user-facing, latency-sensitive), **nearline** (near-real-time, seconds to minutes), and **offline** (batch, Hadoop/Spark, hours) data tiers must not share storage or compute resources.

The data flows between tiers via Kafka. A user action (viewing a profile, clicking a post) generates an event that is immediately acknowledged and written to Kafka by the online service. Nearline consumers pick up events within seconds and update recommendation models, feed candidates, and counters. Offline consumers drain events into HDFS in micro-batches for training data, compliance logs, and analytics.

```
[Online Service] → Kafka → [Nearline Consumers] → Derived Stores (Pinot, Espresso)
                                    ↓
                         [Offline Consumers] → HDFS → Spark → Model Training
```

LinkedIn uses **Apache Pinot** for nearline analytics — a real-time OLAP system that can answer analytical queries (aggregations, filters) on streaming data with sub-second latency. Pinot ingests directly from Kafka. This is what powers LinkedIn's "who viewed your profile" feature with near-real-time counts.

The separation is enforced at the infrastructure level, not just by convention. Online services have no direct access to offline storage. This prevents the category of incidents where an analyst runs a full-table scan against a production Postgres replica and causes cascading latency across API servers.

---

## Interview Implications: What LinkedIn Looks For

LinkedIn's engineering culture emphasizes **trust through transparency** — one of their five stated engineering values alongside building things that matter, moving fast but not breaking trust, measurable impact, and inclusion. The trust emphasis shows up in their interview process: they pay attention to how candidates reason about reliability, backward compatibility, and the downstream effects of their decisions.

**System design questions you should be prepared for:**

1. **Design LinkedIn's feed** — The canonical LinkedIn system design question. The correct answer layers retrieval (graph-based candidate set), ranking (ML scoring model), and storage (Kafka, Pinot for nearline). Show that you understand the three sub-feed merge and can speak to the viral score concept. Do not ignore the social graph as the foundation; candidates who jump to "store posts in S3 and use Redis for caching" miss the core problem.

2. **Design member search** — LinkedIn search must rank members by relevance to a query while weighting social distance (first-degree connections rank higher). This requires full-text search (Elasticsearch or LinkedIn's internal Galene search) combined with graph signal injection at ranking time. Discuss index design, multi-field scoring, and how you would handle the cold-start problem for new members.

3. **Design a notification system at LinkedIn scale** — Involves Kafka for event streaming, fanout decisions (push vs. pull for high-degree members), deduplication, and delivery guarantees. LinkedIn sends billions of notifications per day across email, push, and in-app channels.

**Coding interviews** at LinkedIn use LeetCode-style problems but with an emphasis on graph algorithms — BFS/DFS, shortest path, cycle detection — that directly reflect the member graph domain. Practice problems involving adjacency lists, topological sort, and connected components.

**Behavioral interviews** focus on the engineering values. LinkedIn interviewers specifically probe for situations where you prioritized reliability over speed, handled a production incident with transparency, or made a technical decision that affected teams downstream. The "measurable impact" value means your stories should include numbers — latency reduced by X%, throughput increased by Y, error rate dropped from Z% to near-zero.

LinkedIn's engineering blog at engineering.linkedin.com remains one of the most technically dense company blogs in the industry. Reading their posts on Kafka (authored by Jay Kreps and Neha Narkhede, the Kafka co-creators), on Espresso and Voldemort, and on their feed ranking infrastructure will give you specific details that distinguish a candidate who has done deep research from one who read a prep guide. That distinction is exactly what LinkedIn's interviewers are looking for.

## Related Articles

- [LinkedIn Software Engineer Interview Guide](/blog/linkedin-software-engineer-interview-guide)
- [LinkedIn Feed Ranking System Design](/blog/linkedin-feed-ranking-system-design)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [Graph Algorithms Interview Guide](/blog/graph-algorithms-interview-guide)
