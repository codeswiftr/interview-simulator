# DoorDash Software Engineer Interview Guide 2024: Process and Prep

DoorDash has grown from a startup into one of the most technically complex logistics companies in the world. Coordinating millions of orders, drivers, restaurants, and customers in real-time requires some genuinely hard engineering. Their interview loop reflects that complexity — they're particularly strong on backend, distributed systems, and real-time operational problems.

## DoorDash Engineering Culture

DoorDash's mission is to empower local economies. Their engineering is defined by:

- **Real-time operational scale**: Orders must be matched to Dashers within seconds; restaurant ETAs must be accurate; the margin for error is low
- **Marketplace dynamics**: DoorDash is a three-sided marketplace (consumer, merchant, Dasher) — every engineering decision affects all three parties
- **Move fast with accountability**: Fast delivery of features balanced against the consequence of logistics failures (a missed delivery affects income for a Dasher and dinner for a family)
- **Data-driven**: Decisions at DoorDash are grounded in experiment results and metrics

## Interview Format

1. Recruiter phone screen (30 min)
2. Technical phone screen (60 min) — 1-2 LeetCode problems
3. Virtual onsite (4-5 rounds):
   - 2 coding rounds
   - 1 system design round
   - 1 behavioral round
   - Occasionally: domain-specific (data systems, mobile, ML)
4. Hiring committee → offer

Timeline: 3-4 weeks typically.

## Coding Rounds

DoorDash coding interviews skew toward practical, applied problems. LeetCode medium is the floor; senior roles see hard.

**Core topic areas:**
- Graphs (routing, shortest path — very common at a logistics company)
- Priority queues and heaps
- Interval problems (scheduling, time windows)
- Hash tables and aggregation
- Object-oriented design

**DoorDash-flavored problem types:**

*Delivery routing:*
> "Given a list of restaurants, Dashers, and customer locations with lat/long coordinates, find the optimal assignment of Dashers to orders minimizing total delivery time."

This is an assignment problem. Brute force: O(n!) permutations. Practical approach: greedy assignment (nearest Dasher), or bipartite matching (Hungarian algorithm) for smaller sets. Interviewers want to see you recognize it's NP-hard in the general case and propose practical approximations.

*Order ETA:*
> "Design a function that estimates delivery time given: restaurant prep time estimate, Dasher pickup time, historical traffic data for the route, and a safety buffer."

Weighted sum problem with uncertainty. Discuss percentile-based estimates vs. point estimates; why you'd pick p90 (under-promise) vs. p50 (accurate but risky).

*Dasher scheduling:*
> "Given Dashers with availability windows and restaurants with peak hours, design a scheduling system that maximizes coverage during demand peaks."

Interval scheduling — greedy (earliest deadline first), or optimization formulation. Classic interval overlap detection.

**What DoorDash interviewers care about:**
- Handling real-world messiness: null locations, restaurants that close, Dashers who go offline mid-assignment
- Complexity awareness: state upfront, then optimize
- Edge cases for geographic/temporal problems: timezones, distance at poles, restaurant last-call cutoffs

## System Design: Logistics at Scale

DoorDash system design rounds typically involve real-time operations systems. These are meaty design problems.

**Common questions:**
- Design DoorDash's order dispatch system
- Design DoorDash's real-time tracking system
- Design a restaurant ETA prediction service
- Design a surge pricing system
- Design the Dasher earnings guarantee system

**Framework for DoorDash system design:**

**1. Three-sided marketplace constraints**
Every design must account for three parties: consumer experience (fast, reliable), Dasher experience (fair earnings, efficient routing), merchant experience (accurate prep time requests, manageable demand).

**2. Real-time requirements**
DoorDash's core operations are real-time:
- Order dispatch: Dasher assignment must complete in <2 seconds
- Location tracking: Dasher GPS updates every 10-30 seconds; consumer view is near-real-time
- ETA updates: Recalculated on every meaningful event (Dasher picked up order, traffic update, etc.)

**3. Consistency vs. availability trade-offs**
For order state (placed → confirmed → picked up → delivered), you need strong consistency — two Dashers shouldn't pick up the same order. Use optimistic locking or distributed lock.

For analytics and dashboards, eventual consistency is acceptable.

**Worked example: Order dispatch system**

*Problem*: A consumer places an order. Assign a Dasher within 2 seconds.

*Architecture*:
- **Assignment engine**: On order creation, fetch available Dashers within radius (geospatial query, PostGIS or custom R-tree). Score candidates: proximity, current assignment count, Dasher rating, active shift status.
- **Dasher pool**: Redis geo-index for O(log n) radius queries; updated via Dasher app location pings every 15 seconds.
- **Assignment lock**: Redis SET NX with TTL to reserve a Dasher atomically — prevents double-assignment race condition.
- **Fallback**: If no Dasher available within radius, expand radius incrementally; trigger surge pricing signal if expansion hits limit.
- **Event stream**: Kafka for order lifecycle events; consumed by ETA service, consumer notification service, restaurant service.
- **Retry**: If Dasher doesn't accept within 30 seconds, reassign from pool.

*Scale considerations*:
- Peak: ~500K orders/hour on major holidays
- Partition Kafka by geographic region; assignment engines are region-sharded
- Dasher location store: Redis cluster, sharded by geo-hash prefix

## Behavioral: DoorDash's Focus Areas

DoorDash behavioral rounds assess ownership, data-driven thinking, and impact.

**Key themes:**

**"Tell me about a time you improved a system's reliability or reduced latency."**
They want: root cause analysis, instrumentation, iterative improvement, measurable outcome.

**"Describe a time you made a decision with incomplete data."**
They want: comfort with uncertainty, using proxies when perfect data isn't available, willingness to iterate.

**"Tell me about a project you drove from idea to production."**
They want: ownership over the full lifecycle — you didn't just implement; you understood requirements, made architectural decisions, monitored, iterated.

**"How have you influenced a team without formal authority?"**
They want: written communication (DoorDash is documentation-heavy), persuasion through data, coalition building.

**DoorDash-specific behavioral tip**: Connect everything to three-sided marketplace impact. "We reduced order confirmation latency" is good. "We reduced order confirmation latency by 40%, which increased Dasher acceptance rates by 8% and improved consumer NPS by 12 points" is what they want.

## The DoorDash Tech Stack

Knowing this isn't required, but useful for framing designs:

- **Languages**: Kotlin (backend microservices), Python (ML, data), Swift/Kotlin (mobile)
- **Infrastructure**: AWS, Kubernetes
- **Data**: Apache Kafka (event streaming), Apache Flink/Spark (stream/batch processing), Snowflake (analytics), Redis (caching, geo-index), PostgreSQL
- **Geospatial**: PostGIS, custom geohash indices
- **ML**: DoorDash has a substantial ML platform (delivery time prediction, menu recommendation, fraud detection)

When designing systems, these references show domain literacy — but always explain your choices rather than just naming technologies.

## Preparation Plan: 5 Weeks

**Weeks 1-2: Coding**
- 30 LeetCode medium problems (graphs, heaps, intervals heavily)
- Implement Dijkstra's and A* pathfinding from scratch
- Practice interval scheduling and assignment problems

**Weeks 3-4: System design**
- Deep-dive order dispatch + real-time tracking systems
- Study geospatial indexing (R-tree, Geohash, PostGIS)
- Read DoorDash Engineering blog (doordash.engineering)

**Weeks 5: Behavioral + polish**
- STAR stories mapped to ownership, data-driven decision, reliability themes
- Frame every story in terms of three-sided marketplace impact where applicable
- Mock interviews with real-time problem framing

## What Sets DoorDash Candidates Apart

The engineers who get DoorDash offers think naturally about **operations under failure**. They don't design happy-path systems — they immediately ask: What if the Dasher goes offline? What if the restaurant confirms but never starts the order? What if the consumer's payment fails after the Dasher has already picked up the food?

This operational mindset, combined with the ability to measure impact across all three marketplace participants, is what DoorDash's interviewers are actually looking for.
