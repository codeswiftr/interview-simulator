# How to Prepare for System Design Interviews in 30 Days: A Structured Plan

System design interviews are the great equalizer in senior engineering hiring. Candidates who can grind LeetCode for months still walk out of system design rounds dazed, having designed a Twitter clone with a single MySQL table. The gap between passing and failing is not raw intelligence — it is structured knowledge and practiced communication. This guide gives you a day-by-day, week-by-week roadmap to go from uncertain to confident in 30 days.

Before anything else: system design is a communication exercise first and a technical exercise second. The interviewer wants to see how you think, how you decompose ambiguity, how you reason about tradeoffs. A candidate who designs an imperfect system while clearly articulating why they made each choice will consistently outscore one who produces a technically superior design while narrating it poorly.

---

## The Answer Framework: Clarify, Estimate, Design, Deep Dive

Every system design answer should follow this four-stage structure. Internalizing it early will give your practice sessions a consistent shape.

**Clarify (3-5 minutes).** Before drawing a single box, ask questions. What is the scale? Is this read-heavy or write-heavy? Does the system need to be globally distributed? What are the latency requirements? What consistency guarantees matter? What is out of scope? Clarifying questions do two things: they prevent you from designing the wrong system, and they signal to the interviewer that you do not jump to solutions.

**Estimate (3-5 minutes).** Back-of-the-envelope math grounds your design. If you are building a URL shortener for 100 million daily active users, you should know roughly: how many writes per second, how much storage you need after five years, what your read-to-write ratio looks like, whether you will saturate a single database server. Rough numbers (within an order of magnitude) are fine. The discipline of estimation prevents over-engineering small systems and under-engineering large ones.

**Design (15-20 minutes).** Draw the high-level architecture. Identify the major components: clients, API gateway or load balancer, application servers, caches, databases, message queues, CDN. Walk through a user request end to end. State your assumptions explicitly. Make tradeoff decisions out loud.

**Deep Dive (10-15 minutes).** The interviewer will steer you toward specific areas they want to probe. This is where you discuss your database schema, your caching eviction strategy, how you handle hotspot keys, how your system behaves when a node fails, what your replication topology looks like.

Keep this framework visible during your practice sessions. After each practice design, grade yourself on each stage.

---

## Week 1: Fundamentals (Days 1-7)

The first week is about building vocabulary and conceptual depth. Do not skip this phase to get to practice problems faster — engineers who skip it produce designs that sound right but fall apart under questioning.

**Day 1-2: CAP Theorem and Consistency Models**

CAP theorem states that a distributed system can provide at most two of three guarantees: Consistency, Availability, and Partition tolerance. Because network partitions are unavoidable in any real distributed system, the practical choice is between CP (consistent but may be unavailable during partitions) and AP (available but may return stale data during partitions).

Go deeper than the theorem itself. Learn the consistency spectrum: strong consistency (linearizability), sequential consistency, causal consistency, eventual consistency, read-your-own-writes consistency. Understand which databases and systems operate at which level. Cassandra is AP by default with tunable consistency. Zookeeper and etcd are CP. DynamoDB gives you eventual consistency by default with optional strongly consistent reads at a cost in latency. When you understand this spectrum, you can make intentional choices in your designs rather than defaulting to "use Postgres everywhere."

Resources: the Dynamo paper (Amazon, 2007), the Spanner paper (Google, 2012), Martin Kleppmann's "Designing Data-Intensive Applications" chapters 5 and 9.

**Day 3: Replication and Sharding**

Replication is making copies of data across nodes for durability and availability. Learn single-leader replication (one node accepts all writes, replicas apply the same writes), multi-leader replication (multiple nodes accept writes, conflicts must be resolved), and leaderless replication (any node can accept writes, read quorums detect stale data). Understand synchronous versus asynchronous replication and the durability versus latency tradeoff each implies.

Sharding (horizontal partitioning) is splitting data across multiple nodes so no single node holds everything. Learn range-based sharding (partition by key range, prone to hotspots), hash-based sharding (distribute by hash of key, poor range queries), and consistent hashing (used in systems like Cassandra and Chord to minimize reshuffling as nodes join and leave).

**Day 4: Load Balancing and CDNs**

A load balancer distributes incoming requests across a pool of servers. Layer 4 load balancers operate at the TCP level (fast, fewer features). Layer 7 load balancers operate at the HTTP level (can route based on URL path, host headers, cookies). Learn the major algorithms: round robin, weighted round robin, least connections, IP hash (session affinity).

CDNs (Content Delivery Networks) cache static assets and sometimes dynamic content at edge nodes geographically close to users. Understand push CDNs (you push content proactively) versus pull CDNs (the CDN fetches on first request and caches). Know when a CDN reduces origin load versus when it does not help (highly personalized content, real-time data).

**Day 5-6: Caching Layers**

Caching is the highest-leverage primitive in distributed systems. Learn where caches live: client-side (browser), CDN, reverse proxy (Nginx, Varnish), application-level (in-process), distributed cache (Redis, Memcached), database query cache.

Master the eviction policies: LRU (Least Recently Used), LFU (Least Frequently Used), TTL-based expiration. Understand write strategies: write-through (write to cache and database simultaneously, strong consistency, higher write latency), write-behind (write to cache, asynchronously flush to database, lower write latency, risk of data loss), cache-aside (application reads from cache, misses go to database and populate cache, most common pattern).

Know how to handle cache invalidation — "there are only two hard things in computer science" — and cache stampedes (many requests miss simultaneously and hammer the database). Cache stampede mitigations include probabilistic early expiration and request coalescing.

**Day 7: DNS, API Gateways, Rate Limiting Basics**

Understand what happens from the moment a user types a URL to when they receive a response. DNS resolution, TCP handshake, TLS handshake, HTTP request, load balancer, application server. Every hop matters for latency.

API gateways sit in front of your services and handle cross-cutting concerns: authentication, rate limiting, request routing, SSL termination, logging. Know when an API gateway adds value (microservices with shared concerns) versus when it adds unnecessary complexity (monolith, small team).

---

## Week 2: Storage Systems Deep Dive (Days 8-14)

**Day 8-9: SQL vs. NoSQL Tradeoffs**

The question is never "which is better" — it is "what are you optimizing for." SQL databases (PostgreSQL, MySQL) provide ACID transactions, strong schemas, powerful query language, and mature tooling. They scale vertically well and horizontally with effort (read replicas, sharding). They are the right default for most applications.

NoSQL databases sacrifice some guarantees for specific scaling properties or data model flexibility. Document stores (MongoDB, Firestore) work well when your access patterns match document boundaries. Key-value stores (Redis, DynamoDB) excel at single-key lookups at high scale. Wide-column stores (Cassandra, HBase) are optimized for time-series data and write-heavy workloads. Graph databases (Neo4j) handle relationship-heavy queries that would require many JOINs in SQL.

The interview trap: candidates recommend NoSQL because "it scales better" without specifying what tradeoffs they are accepting. Always articulate what you are giving up.

**Day 10: Object Storage and File Systems**

S3, Google Cloud Storage, and Azure Blob Storage are object stores: they store arbitrary blobs addressable by key, with high durability (typically 11 nines), eventually consistent metadata operations, and no filesystem hierarchy (though you can simulate it with key prefixes). They are the right answer for user-uploaded files, media, backups, and data lake storage.

Understand when object storage is inappropriate: frequent small random reads and writes (use a database or block storage), low-latency metadata operations (object stores have non-trivial list API latency at scale).

**Day 11: Message Queues and Event Streaming**

Message queues (RabbitMQ, SQS) decouple producers and consumers, enable retries, and smooth traffic spikes. Event streaming platforms (Kafka, Kinesis) add persistent, replayable, ordered logs of events that multiple consumers can read independently.

Know the difference: queues are typically for task distribution (process this job), streams are for event sourcing and analytics (replay all events since timestamp X). Understand consumer groups in Kafka, at-least-once versus exactly-once delivery semantics, and the performance implications of partition count.

**Day 12-13: Search Engines and Full-Text Search**

Elasticsearch (and OpenSearch) are the industry standard for full-text search and log analytics. Understand the inverted index: instead of mapping documents to terms, it maps terms to documents, enabling fast term lookups. Learn about analyzers (tokenization, stemming, lowercasing), relevance scoring (BM25 by default), and sharding strategies for Elasticsearch.

Know when you need a dedicated search engine versus when a database full-text index (Postgres tsvector, MySQL FULLTEXT) suffices. Database full-text search is good enough for moderate scale and simpler operations. Elasticsearch shines for complex queries, faceting, and large-scale log analysis.

**Day 14: Review and Connection-Building**

Do not add new material today. Review weeks one and two. For each concept, write one sentence about when you would use it and one sentence about its primary tradeoff. If you cannot do this, you need more depth on that concept. This is also a good day to create a personal reference document with your notes — you will use it during practice in week three.

---

## Week 3: Design Practice (Days 15-21)

This week you design five canonical systems, one per day (with two days for deeper practice). Each session: spend 5 minutes clarifying requirements, 5 minutes estimating, 20 minutes designing on paper or a whiteboard, then review what you missed.

**Day 15: URL Shortener**

This is the entry-level system design problem and teaches you more than you might expect. The core challenge: how do you generate short codes that are unique, not sequential (to avoid enumeration), and can be resolved quickly at read time? Topics: hashing versus auto-increment IDs, database choice (key-value store maps short code to long URL), caching the lookup (read-heavy workload, perfect for Redis), handling redirects (301 permanent versus 302 temporary and what each means for analytics), custom domains, expiration.

**Day 16: Rate Limiter**

A rate limiter enforces request quotas. The interesting design questions: where does it live (client-side, API gateway, per-service), what algorithm does it use (token bucket allows bursting, leaky bucket enforces smooth output, fixed window counters are simple but have boundary problems, sliding window log is accurate but memory-heavy, sliding window counter is a good compromise), where is the state stored (in-process limits to single instance, Redis allows distributed enforcement), and how do you handle partial failures (if Redis is unavailable, do you fail open or closed)?

**Day 17: News Feed (Social Media)**

Facebook News Feed or Twitter timeline. This is a complex fan-out problem. Write path: user posts something, how do you distribute it to followers? Fan-out on write (precompute each follower's feed at write time) is fast to read but expensive if a user has millions of followers. Fan-out on read (compute feed at read time by merging followed users' posts) avoids celebrity user problems but is expensive to read. Hybrid approaches handle celebrity users specially. Also covers: ranking signals, pagination (cursor-based versus offset), how to handle new posts appearing while a user is paginating.

**Day 18: Notification System**

Push notifications (iOS APNs, Android FCM), email, SMS. The notification system teaches you about: fan-out at massive scale, priority queues (transactional notifications should go before marketing emails), rate limiting notifications to users (do not spam), deduplication (same event should not trigger two notifications if retried), user preferences (opt-out per channel per notification type), and the integration surface with third-party providers.

**Day 19: Distributed Cache (Design Your Own Redis)**

Designing a distributed caching system covers: consistent hashing for key distribution, replication for availability, TTL implementation (lazy expiration versus active expiration background jobs), memory limits and eviction policies, the RESP protocol for client communication, and the CAP tradeoffs of a cache that prioritizes availability. This problem tests deep understanding rather than breadth.

**Day 20-21: Review and Self-Assessment**

For each of the five designs: what did you miss that you only discovered in post-session review? Which topics require more depth? What questions could you not answer during the deep dive phase? Write down your three biggest gaps and allocate week four's deep dives accordingly.

---

## Week 4: Advanced Topics and Mock Interviews (Days 22-30)

**Day 22-23: Distributed Transactions and Consensus**

Two-phase commit (2PC): coordinator asks all participants to prepare, then commits or aborts. Synchronous, blocks if coordinator fails. Used in relational databases with distributed transactions. Three-phase commit (3PC) adds a pre-commit phase to reduce blocking but does not eliminate it.

The Raft consensus algorithm is worth understanding at a conceptual level. A Raft cluster elects a leader. The leader receives all writes, replicates to a majority of nodes before committing. If the leader fails, a new election occurs. etcd, Consul, and CockroachDB use Raft. You do not need to implement Raft but understanding leader election, log replication, and safety properties will sharpen your distributed systems answers.

**Day 24: Real-Time Systems**

WebSockets for bidirectional, low-latency communication (chat, live collaboration, multiplayer games). Server-Sent Events (SSE) for server-to-client streaming (stock tickers, live feeds). Long polling as a fallback. When designing real-time systems: how do you route messages to the right WebSocket server when you have a fleet behind a load balancer (pub/sub through Redis or Kafka), how do you handle reconnects and message replay, how do you scale to millions of concurrent connections.

**Day 25-26: Mock Interview Practice**

Simulate actual interview conditions. Set a 45-minute timer. Pick a problem you have not practiced. Do not look at notes during the session. Record yourself or narrate aloud. After the session, review against your framework: did you clarify, estimate, design, and deep dive in proportion? Were there questions you could not answer? Where did you get stuck?

Common sticking points: being asked "how would you handle a database failure" and not knowing how your chosen database handles it; being asked "how would you monitor this system" and having no answer; not knowing what SLA your design can realistically offer.

**Day 27: Common Mistakes and How to Avoid Them**

Jumping to solutions: the single most common failure mode. Candidates hear "design Twitter" and immediately start drawing databases. Force yourself to ask at least three clarifying questions before touching the whiteboard.

Ignoring scale: a design that works for 1,000 users may not work for 100 million. Always revisit your capacity estimates and ask whether any component becomes a bottleneck at the stated scale.

Over-engineering: adding Kafka, Elasticsearch, Redis, a CDN, and a service mesh to a system that handles 10 requests per second. Match the complexity of your design to the stated scale requirements.

Not owning your decisions: saying "we could use Postgres or Cassandra" without committing to one and explaining why is a red flag. Make a choice and defend it.

**Day 28: Handling Being Stuck**

Every interviewer expects you to get stuck. What they evaluate is how you handle it. When stuck: narrate your thinking ("I know we need to handle fan-out here, let me think through the tradeoffs"). Ask a clarifying question ("Can we assume the read-to-write ratio is 100:1?"). Propose a simple approach first and note its limitations ("A naive approach would be to compute the feed on every read, but that is O(n) for n followed users — let me think about how to precompute it").

Never go silent for more than 30 seconds. Silence is the only answer that earns zero credit.

**Day 29: Right Level of Detail by Time Frame**

For a 45-minute interview: 5 minutes clarifying, 5 minutes estimating, 20 minutes on high-level design, 10-15 minutes on deep dives. Do not spend 10 minutes on database schema when you have not covered how data flows through the system. Do not draw individual API endpoints at the expense of drawing component boundaries.

For the high-level design, every major component should be on the diagram. You do not need to detail every API. For deep dives, you should be able to go to the level of "the events table has a UUID primary key, a user_id foreign key, a type enum, a payload JSONB column, and a created_at timestamp, and we index on (user_id, created_at) for the feed query."

**Day 30: Final Review and Mental Preparation**

Review your personal reference document. Review the five designs from week three. Identify the three topics you are least confident about and do one final pass on each. Practice your opening clarifying questions until they are automatic.

---

## Resources by Week

**Week 1:** "Designing Data-Intensive Applications" by Martin Kleppmann (chapters 1-6). The system design primer on GitHub (donnemartin/system-design-primer). ByteByteGo newsletter issues on CAP theorem and caching.

**Week 2:** The Dynamo paper and the Bigtable paper. "Designing Data-Intensive Applications" chapters 10-12. Elasticsearch documentation on index design.

**Week 3:** Grokking the System Design Interview (Educative) for problem walkthroughs. ByteByteGo "System Design Interview" books volumes 1 and 2. Excalidraw or draw.io for diagramming practice.

**Week 4:** The Raft paper ("In Search of an Understandable Consensus Algorithm"). High Scalability blog for real-world system architectures. Mock interview practice via Interviewing.io or Pramp.

---

The 30-day timeline is aggressive but achievable if you commit two to three hours per day. The biggest predictor of success is not the volume of material you cover — it is the quality of your practice sessions. One well-reviewed mock interview is worth more than ten half-hearted ones. Design out loud. Take notes on what you missed. Return to concepts you cannot explain clearly. The system design interview rewards engineers who have built a coherent mental model of distributed systems, not ones who have memorized a list of architectures.
