# Backend Engineer Interview Guide 2024: Complete Preparation Strategy

Backend engineering interviews are broader than many candidates expect. They test DSA, system design, API design, database knowledge, and often distributed systems depth — all in one loop. Here's exactly what's covered and how to prepare efficiently.

## What Backend Interviews Actually Test

Backend roles have wider variance than frontend. A backend loop at a startup tests API design and database schema. At FAANG, it tests distributed systems and scale. Know what tier you're targeting.

**Common to all backend interviews:**
- Data structures and algorithms (LeetCode medium floor)
- Database design (SQL schemas, query optimization, indexing)
- API design (REST best practices, versioning, idempotency)
- System design (distributed or not, depending on seniority)

**Senior/staff-level additions:**
- Distributed systems fundamentals (CAP theorem, consensus, partitioning)
- Observability (metrics, tracing, logging strategy)
- Reliability patterns (circuit breaker, retry with backoff, rate limiting)

## Coding Round: The Backend Twist

Backend coding rounds are standard DSA with an applied flavor. Interviewers often frame problems in terms of the backend context: "You're building a caching layer..." or "This is a rate limiter implementation."

**Core topics:**
- Hash tables and their collision strategies
- Trees, graphs, BFS/DFS
- Sorting and searching
- Sliding window and two pointers
- Dynamic programming (less common at non-FAANG)

**Backend-specific implementations interviewers love:**

*LRU Cache:*
```python
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> node
        # Doubly linked list for O(1) eviction
        self.head, self.tail = DNode(), DNode()
        self.head.next = self.tail
        self.tail.prev = self.head
```
Know this cold — O(1) get and put using an OrderedDict or manual doubly linked list.

*Rate limiter (Token Bucket):*
```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

*Consistent hashing:*
Know the algorithm conceptually: virtual nodes on a ring, hash keys to nodes, handle node addition/removal with minimal key remapping. Interviewers ask this in system design too.

## Database Design: What You Must Know

Database questions come up in coding rounds, system design, and dedicated DB rounds at infrastructure companies.

### Schema Design

**Normalization vs. denormalization:**
- Normalized: less duplication, better consistency, more joins (OLTP workloads)
- Denormalized: faster reads, more storage, more complex writes (analytics, high-read APIs)

**Common interview schema problems:**
- Design a social network schema (users, connections, posts, comments)
- Design an e-commerce schema (products, orders, inventory, payments)
- Design a booking system (resources, reservations, availability)

**Key constraints to mention:** Primary keys, foreign keys, unique constraints, check constraints. Interviewers notice when you don't discuss integrity.

### Indexing

B-tree indexes: Great for equality and range queries. Not useful for low-cardinality columns (e.g., boolean fields).

Composite indexes: Column order matters. `(user_id, created_at)` supports queries on both, but only optimizes `user_id` prefix scans efficiently.

When NOT to index: High write tables with many mutations — index maintenance overhead can hurt more than it helps.

**Covering index**: Index includes all columns needed for a query — the DB never touches the main table row. Huge performance win for read-heavy queries.

### Query Optimization

When a query is slow:
1. `EXPLAIN ANALYZE` — find sequential scans and high row estimates
2. Add indexes on WHERE clause columns and JOIN conditions
3. Rewrite subqueries as JOINs where possible
4. Use connection pooling (PgBouncer, HikariCP) to avoid connection overhead

**N+1 problem**: Fetching a list of users, then querying each user's orders separately → N+1 database calls. Fix: JOIN or IN clause for batch fetch.

### SQL Fluency

Write these without hesitation:

```sql
-- Window function: rank users by spend per region
SELECT
  user_id,
  region,
  total_spend,
  RANK() OVER (PARTITION BY region ORDER BY total_spend DESC) as rank
FROM orders
JOIN users USING (user_id);

-- CTE for complex multi-step queries
WITH monthly_revenue AS (
  SELECT
    DATE_TRUNC('month', created_at) as month,
    SUM(amount) as revenue
  FROM payments
  WHERE status = 'completed'
  GROUP BY 1
)
SELECT month, revenue, LAG(revenue) OVER (ORDER BY month) as prev_month
FROM monthly_revenue;
```

## API Design: The Art of the Contract

Many backend interviews include an API design component, especially for senior roles. Key principles:

**RESTful resource naming:**
- Nouns for resources: `/users`, `/orders/{id}`, not `/getUser`
- HTTP verbs carry action semantics: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE
- Hierarchical for relationships: `/users/{id}/orders`

**Idempotency (essential for backend engineers):**
- GET, PUT, DELETE: inherently idempotent
- POST: not idempotent by default → use idempotency keys for payment/booking endpoints
```
POST /payments
Idempotency-Key: client-generated-uuid-123
```

**Versioning strategies:**
- URL path versioning (`/v1/users`) — simple, explicit, favored for public APIs
- Header versioning (`Accept: application/vnd.api.v2+json`) — cleaner URLs, harder to test in browser
- Never break compatibility without deprecation notice and migration window

**Error responses:**
```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Account balance is insufficient for this transaction",
    "details": { "available": 42.00, "required": 100.00 }
  }
}
```
Use standardized error shapes. Include machine-readable codes (for client handling) and human-readable messages (for debugging).

**Pagination:**
- Offset pagination (`?page=2&limit=20`): simple but degrades at high offsets and has consistency issues with concurrent writes
- Cursor-based (`?after=cursor_token`): stable across writes, required for real-time feeds and large datasets

## System Design: The Backend Depth

Backend system design questions focus on data flow, consistency, and reliability:

**Common questions:**
- Design a URL shortener
- Design a notification service
- Design a job queue / background worker system
- Design a caching layer
- Design a distributed rate limiter

**URL shortener (canonical example):**
- Encoding: hash (MD5, take 6 chars) or base62 counter (simpler, sequential)
- Storage: `short_code → original_url` in a key-value store (Redis) or relational DB
- Redirect: 301 (cached by browser, fewer server hits) vs. 302 (analytics tracked, but more server load)
- Scale: Read-heavy → CDN or edge cache for hot links; write path is trivial

**Notification system:**
- Fan-out problem: 1 event → N notifications (email, push, SMS)
- Queue-based delivery (Kafka/SQS) for decoupling and retry
- Delivery channels as plugins: each channel has own retry policy and rate limits
- Deduplication: idempotency key on notification ID prevents duplicate sends
- User preferences: per-channel opt-out stored in fast key-value store

**Distributed rate limiter:**
- Token bucket in Redis: `INCRBY` with TTL, or Lua script for atomic check-and-decrement
- Fixed window vs. sliding window: fixed is simpler but allows burst at window boundary; sliding window is accurate but more complex
- Per-user vs. per-IP vs. global: different limits for different granularities

## Reliability Patterns: Mention These in Design Rounds

**Circuit breaker**: Prevent cascading failures. Track failure rate; open circuit (fail fast) when threshold exceeded; test with probe requests after timeout.

**Retry with exponential backoff + jitter**: `delay = base * 2^attempt + random(0, base)`. Jitter prevents thundering herd when many clients retry simultaneously.

**Bulkhead**: Separate connection pools for different downstream services — a slow dependency can't exhaust all threads.

**Saga pattern**: Distributed transactions without 2PC. Each step publishes an event; compensating transactions roll back on failure.

## The Behavioral Component

Backend engineers are often viewed as more technical and less "soft skills" — which means candidates sometimes under-prepare behaviorally. Don't.

**Key backend-specific behavioral themes:**

**Production incidents:**
> "Tell me about a time you debugged a production issue under pressure."
Know your incident response playbook: how you triage, how you communicate, how you do post-mortems without blame.

**Technical debt:**
> "How have you dealt with inherited technical debt?"
Show you can triage pragmatically — what to pay down now vs. accept vs. document for later.

**Scale challenges:**
> "Tell me about a system you built that didn't scale as expected. What happened?"
Honest post-mortems with lessons learned demonstrate engineering maturity.

## Preparation Plan: 5 Weeks

**Week 1: Algorithms**
- LeetCode: 25 medium problems (focus on hash tables, graphs, trees)
- Implement LRU cache and rate limiter from scratch

**Week 2: Databases**
- Write 15 SQL queries using CTEs, window functions, GROUP BY aggregations
- Design 3 schemas from scratch (social, e-commerce, booking)
- Practice reading and interpreting EXPLAIN ANALYZE output

**Week 3: System design**
- Design URL shortener, notification system, distributed rate limiter
- Study CAP theorem, consistent hashing, message queue semantics

**Week 4: API design + reliability**
- Design APIs for 3 systems: user management, order processing, search
- Study circuit breaker, bulkhead, retry patterns

**Week 5: Behavioral + mock interviews**
- 3-5 STAR stories on incidents, technical debt, scaling failures
- 2-3 mock system design sessions with a partner

## The Backend Engineer Mindset

The engineers who excel in backend interviews share one quality: they naturally **surface the failure modes**. They don't just describe how a system works — they describe what breaks it.

When you design a payment API, mention idempotency before being asked. When you propose a caching layer, mention cache invalidation and stale data. When you design a queue, mention dead letter queues and poison messages.

This failure-mode instinct is what separates engineers who build reliable systems from engineers who build systems that mostly work. Interviewers are evaluating exactly that.
