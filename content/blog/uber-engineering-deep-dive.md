# Uber Engineering Deep Dive: Real-Time Dispatch at Scale

When you open the Uber app and tap "Request," you trigger one of the most demanding real-time matching problems in consumer software. Within seconds, a system ingesting millions of location updates per second, running geospatial queries across hundreds of thousands of concurrent drivers, and balancing surge multipliers across city-scale demand grids has to find you the right driver, commit to an ETA, and price the ride — all before the loading spinner disappears.

Understanding how Uber built this infrastructure is not just useful background knowledge. For engineers interviewing at Uber, it is the core of what the system design rounds actually test. This post breaks down the engineering foundations, the infrastructure Uber built that the industry now borrows from, and what interviewers are actually looking for.

---

## The Matching Problem at Uber Scale

Uber operates in roughly 70 countries and 10,000-plus cities. At peak, the platform handles over 25 million trips per day, with millions of GPS pings per second flowing in from active drivers. The dispatch system has to continuously solve a bipartite matching problem: assign drivers to riders in a way that minimizes pickup time globally across a region, not just locally for each request.

This is different from a naive nearest-driver algorithm. If every request grabbed the closest available driver, the overall system would fragment badly — a cluster of three requests and three drivers in a small area might leave requests on the edge under-served while drivers nearby go unmatched. Uber runs a global optimization pass that treats all open requests and available drivers in a city simultaneously, producing a matching that minimizes aggregate estimated time of arrival (ETA) rather than just satisfying each request greedily.

The matching runs on a cadence measured in seconds. Every few seconds, the dispatch service recomputes the optimal assignment and re-evaluates existing offers. This is not a background batch job — it is a hot, continuously running loop with hard latency requirements, because drivers and riders are moving.

---

## H3: Uber's Hexagonal Hierarchical Index

No discussion of Uber's geospatial engineering is complete without H3, which Uber open-sourced in 2018. H3 is a hierarchical geospatial indexing system that decomposes the Earth's surface into a grid of hexagons at multiple resolutions.

The choice of hexagons is deliberate and consequential. Square grids suffer from directional bias: diagonal movement crosses more cells than cardinal movement across the same distance, making density calculations inconsistent depending on direction. Hexagonal cells have a single nearest-neighbor distance — every adjacent cell center is equidistant from the origin cell center. This makes hexagonal grids fundamentally better for spatial aggregation, nearest-neighbor queries, and density smoothing.

H3 defines 16 resolution levels. At resolution 9, each hexagon covers approximately 0.1 square kilometers — roughly the size of a city block. At resolution 7, each hexagon covers about 5.16 square kilometers. Uber uses different resolutions for different purposes: surge pricing zones are computed at a coarser resolution so pricing areas don't fragment into unusably small patches, while driver supply and demand density is measured at finer resolutions for dispatch accuracy.

The hexagonal hierarchy also enables efficient spatial joins. A hexagon at resolution 7 contains exactly seven children at resolution 8 (six surrounding one center), and each of those contains exactly seven children at resolution 9. This clean, consistent containment relationship makes rolling up fine-grained demand signals into coarser pricing zones computationally cheap — it is integer arithmetic, not floating-point polygon intersection.

A minimal Go implementation that illustrates the core H3 indexing concept:

```go
package h3

import "math"

// LatLng represents a geographic coordinate.
type LatLng struct {
    Lat float64
    Lng float64
}

// CellIndex represents an H3 hexagonal cell at a given resolution.
type CellIndex uint64

// Resolution returns the resolution encoded in an H3 cell index.
// Resolutions 0–15, encoded in bits 52–55 of the 64-bit index.
func (c CellIndex) Resolution() int {
    return int((uint64(c) >> 52) & 0xF)
}

// ToParent returns the cell index of the parent at the specified resolution.
// This is equivalent to zero-ing the lower resolution bits.
func (c CellIndex) ToParent(resolution int) CellIndex {
    current := c.Resolution()
    if resolution >= current {
        return c
    }
    // Mask off bits for resolutions finer than the target.
    shift := uint(3 * (15 - resolution))
    mask := ^((uint64(1) << shift) - 1)
    return CellIndex(uint64(c) & mask)
}

// DrivingZone aggregates supply and demand within an H3 cell.
type DrivingZone struct {
    Cell          CellIndex
    AvailDrivers  int
    OpenRequests  int
    SurgeMultiple float64
}

// DemandRatio returns the demand-to-supply ratio for surge calculation.
func (z *DrivingZone) DemandRatio() float64 {
    if z.AvailDrivers == 0 {
        return math.MaxFloat64
    }
    return float64(z.OpenRequests) / float64(z.AvailDrivers)
}
```

In production, H3 cell indices serve as shard keys, cache keys, and routing identifiers across Uber's geospatial services. A driver location update resolves to an H3 cell in microseconds, and the cell index routes the update to the correct dispatch shard without any additional database lookup.

---

## Uber's Custom Infrastructure Stack

One of the most distinctive things about Uber engineering is that the company built significant infrastructure from scratch — not because off-the-shelf options didn't exist, but because the real-time constraints were strict enough that existing tools became bottlenecks.

### Ringpop: Consistent Hashing with Gossip

Ringpop is Uber's consistent hashing library for building scalable, fault-tolerant distributed applications. It implements a gossip protocol so nodes in a cluster can self-discover and self-heal without a centralized coordinator.

The core insight Ringpop was built around: dispatch nodes needed to own specific geographic regions of the city, so that location updates for a given set of drivers always routed to the same node. This locality property meant the dispatch node for a region could maintain a hot, in-memory state of all drivers and requests in its zone without expensive cross-node coordination on every update. Ringpop's consistent hashing ensured that geographic regions — identified by H3 cell IDs — mapped deterministically to specific nodes, and that the mapping redistributed gracefully as nodes came up or went down.

### TChannel: Uber's RPC Protocol

Before the industry standardized on gRPC, Uber built TChannel — a multiplexed, framed RPC protocol designed for low-latency, high-throughput inter-service communication. TChannel supports request multiplexing over a single TCP connection, explicit call IDs for tracking, and built-in retry semantics.

Uber later migrated most services to gRPC, but TChannel defined the service mesh patterns that Uber's infrastructure still reflects: every service call is traced end-to-end, every call carries context propagation headers, and the RPC layer is responsible for timeout enforcement rather than individual application logic.

### Cadence: Durable Workflow Engine

Cadence is Uber's open-source workflow engine, now maintained by the community as Temporal. It solves a genuinely hard distributed systems problem: how do you write long-running business processes (trip lifecycle, payment processing, driver onboarding) in a way that is durable across failures without hand-rolling state machines and retry logic in every service?

Cadence provides a programming model where you write workflow code as ordinary Go functions with sequential logic, and the engine handles making that logic durable — automatically checkpointing progress, retrying failed activity calls, and replaying state after crashes. For Uber, this means the code path for "driver accepted trip, rider is being tracked, trip completed, payment processed, receipt sent" is written as a single coherent workflow rather than an ad-hoc chain of event handlers.

```go
// Cadence/Temporal workflow example: simplified trip lifecycle
func TripWorkflow(ctx workflow.Context, tripID string) error {
    ao := workflow.ActivityOptions{
        StartToCloseTimeout: 10 * time.Second,
        RetryPolicy: &temporal.RetryPolicy{
            MaximumAttempts: 3,
        },
    }
    ctx = workflow.WithActivityOptions(ctx, ao)

    // Each activity is durable — failures are automatically retried.
    var driverID string
    if err := workflow.ExecuteActivity(ctx, MatchDriver, tripID).Get(ctx, &driverID); err != nil {
        return fmt.Errorf("matching failed: %w", err)
    }

    if err := workflow.ExecuteActivity(ctx, TrackTripToCompletion, tripID, driverID).Get(ctx, nil); err != nil {
        return fmt.Errorf("trip tracking failed: %w", err)
    }

    if err := workflow.ExecuteActivity(ctx, ProcessPayment, tripID).Get(ctx, nil); err != nil {
        return fmt.Errorf("payment failed: %w", err)
    }

    return workflow.ExecuteActivity(ctx, SendReceipt, tripID).Get(ctx, nil)
}
```

### M3: Uber's Metrics Platform

M3 is Uber's open-source distributed time-series database and aggregation service. At Uber's scale, metrics collection itself becomes an engineering challenge — millions of services emitting metrics continuously would saturate any naive aggregation tier. M3 uses a distributed aggregation layer that downsamples metrics before storage, configurable per-metric based on retention needs.

---

## Surge Pricing: The System Design Problem

Surge pricing is Uber's mechanism for balancing supply and demand in real time. When demand in a region outpaces supply, the system raises the price multiplier to simultaneously attract more drivers (higher earnings) and reduce demand (price-sensitive riders wait). Designing this system end-to-end is a common Uber system design interview question.

The key components:

**Demand signal collection.** Every open ride request is tagged with its origin H3 cell. A streaming aggregation service (Apache Kafka + Flink at Uber's scale) continuously computes request counts per cell per resolution level, producing a demand density map that refreshes every 30-60 seconds.

**Supply signal collection.** Every active driver's location update resolves to an H3 cell. The dispatch service maintains a driver supply count per cell, accounting for drivers currently on trips (unavailable) versus idle drivers (available).

**Demand forecasting.** Historical trip patterns — day of week, hour of day, weather, events — inform a short-horizon forecast (15-30 minutes) that smooths out the surge calculation. Without forecasting, surge pricing reacts too slowly (lags demand spikes) or too aggressively (oscillates as drivers flood into surge zones). Uber uses gradient boosting models trained on historical data to predict demand 15 minutes ahead per H3 cell.

**Multiplier computation.** The surge multiplier is a function of the demand-to-supply ratio, calibrated per city so that the model's price elasticity estimates hold. A demand/supply ratio of 1.0 means equilibrium — no surge. As the ratio rises, the multiplier increases non-linearly, with a cap to prevent extreme prices that generate political backlash.

```go
// SurgeMultiplier computes a price multiplier from demand/supply ratio.
// Base calibration: ratio 1.0 -> 1.0x, ratio 2.0 -> ~1.5x, ratio 4.0 -> ~2.5x.
func SurgeMultiplier(demandSupplyRatio float64, maxMultiplier float64) float64 {
    if demandSupplyRatio <= 1.0 {
        return 1.0
    }
    // Log-linear curve: grows fast initially, tapers at high ratios.
    multiplier := 1.0 + 0.7*math.Log(demandSupplyRatio)
    if multiplier > maxMultiplier {
        return maxMultiplier
    }
    return math.Round(multiplier*4) / 4 // Round to nearest 0.25x
}
```

**Zone propagation.** Surge zones use H3 cells at resolution 7 (city-block clusters), and the multiplier is smoothed across adjacent cells using a weighted average so riders don't see sharp price discontinuities at invisible cell boundaries.

**Driver incentives.** Alongside surge pricing, Uber runs "quests" — structured bonus programs that pay drivers a flat bonus for completing N trips in a time window. These are computed per region using the same H3 demand density maps to target bonuses at the right drivers at the right time.

---

## From Monolith to Microservices (and Lessons Learned)

Uber's architecture history is a case study in microservice migration done at extreme speed. The original Uber codebase was a Python monolith. As the company scaled from one city to hundreds, the monolith's deployment bottlenecks and scaling constraints became critical. Starting around 2014-2015, Uber aggressively migrated to microservices — eventually reaching over 2,000 distinct services.

The scale of this migration created its own problems. Services had deep, undocumented transitive dependencies. A change in a low-level utility service could cascade failures three or four layers up. Deployment coordination became complex enough that Uber built dedicated tooling (Makisu for container builds, Peloton for job scheduling) just to manage the microservice ecosystem.

By the early 2020s, Uber had pulled back from the extreme end of microservice granularity. Some services were consolidated — not into a monolith, but into what the industry now calls "macroservices" or domain-bounded services. The dispatch domain, for instance, consolidates logic that had been fragmented across a dozen services back into a coherent module with clear internal boundaries but a single deployment unit.

The lesson Uber's engineers draw from this: microservices are the right answer for independent scaling and team autonomy, but the granularity should map to team ownership boundaries, not to individual functions. If a single team owns five services that always deploy together and share the same database, you have the operational overhead of microservices without the benefits.

---

## Culture Shift: From "Go Big or Go Home" to Operational Excellence

The Travis Kalanick era at Uber was defined by aggressive growth at the expense of engineering discipline. "Move fast" meant accumulating technical debt, cutting corners on reliability, and treating operational incidents as the cost of speed. The culture was results-oriented to a fault — what worked was celebrated regardless of how it was built.

When Dara Khosrowshahi took over in 2017, the engineering culture shifted in measurable ways. Reliability metrics were elevated to first-class engineering goals. On-call rotations became better staffed. Post-mortems shifted from blame-finding to systemic improvement. The SRE function grew significantly.

For engineers interviewing at Uber today, this history is relevant because it means the interview process probes for operational maturity — not just the ability to write correct code, but the ability to reason about failure modes, instrument systems effectively, and design for observability. A system design candidate who builds an elegant architecture without discussing monitoring, alerting, and degraded operation modes will score lower than one who builds a simpler system but thinks carefully about what happens when it breaks.

---

## The Coding Interview: What Uber Actually Tests

Uber's coding bar sits at the medium-hard LeetCode tier. The focus areas reflect the engineering work:

**Graph and shortest-path problems.** Real-time routing is fundamentally a shortest-path problem on a graph. Expect Dijkstra's algorithm, A* variations, and problems involving weighted graphs with dynamic edge costs (analogous to real-time traffic).

**Sliding window and stream aggregation.** Demand monitoring is a streaming aggregation problem. Rate limiting, demand spike detection, and ETA recalculation all have analogues in sliding window problems.

**Interval problems.** Driver availability scheduling and trip forecasting involve interval overlap, merge, and coverage problems.

**Geospatial reasoning.** Questions involving coordinate math, nearest-neighbor in 2D space, and range queries appear. Understanding K-D trees and their use in spatial indexing is useful context.

Go is Uber's primary backend language, and interviewers are accustomed to reviewing Go solutions. If you write Go, lean into the language's idioms — goroutines for concurrent simulations, channels for producer-consumer patterns, defer for resource cleanup.

```go
// NearestDrivers returns the k closest available drivers to a request location.
// Uses a max-heap to maintain the k nearest seen so far in O(n log k) time.
func NearestDrivers(request LatLng, drivers []Driver, k int) []Driver {
    h := &DriverHeap{}
    heap.Init(h)

    for _, d := range drivers {
        dist := haversineKm(request, d.Location)
        heap.Push(h, DriverDist{Driver: d, Dist: dist})
        if h.Len() > k {
            heap.Pop(h) // Evict the farthest
        }
    }

    result := make([]Driver, h.Len())
    for i := len(result) - 1; i >= 0; i-- {
        result[i] = heap.Pop(h).(DriverDist).Driver
    }
    return result
}
```

---

## System Design Interviews

Uber's system design rounds are among the most demanding in the industry because the problems are authentic — "design Uber's dispatch system" is not a hypothetical at Uber, it is documentation. Interviewers have built or operated the systems being discussed and will probe for real understanding, not pattern-matching to a blog post outline.

Strong candidates in Uber system design rounds:

- Start with the data model and access patterns before jumping to architecture
- Reason explicitly about the geospatial sharding strategy (H3 cells as shard keys)
- Address the ETA accuracy problem — GPS drift, traffic model staleness, map tile freshness
- Discuss how surge pricing zones are computed and propagated without creating sharp discontinuities at zone boundaries
- Acknowledge the CAP theorem tradeoffs: dispatch favors availability over consistency — a driver might receive two requests simultaneously during a network partition, and the system handles the conflict after reconnection
- Talk about observability: what metrics you'd alert on, what a degraded-mode operation looks like, how you'd detect a matching algorithm regression in production

---

## Compensation and Interview Process

Uber's compensation sits solidly in the FAANG-adjacent tier. For a senior software engineer (L5), total compensation typically lands in the $350k-$500k range in San Francisco, with meaningful equity participation through RSUs that vest quarterly. The equity program is notable because Uber has been a public company since 2019 — RSUs vest into liquid stock rather than pre-IPO options, which reduces risk compared to late-stage private companies.

The standard interview loop runs:

1. Recruiter screen (30 minutes) — background, motivation, timeline
2. Technical phone screen (60 minutes) — two coding problems, medium difficulty
3. Online assessment (optional for some roles) — algorithmic coding, 90 minutes
4. Virtual onsite (4-5 rounds):
   - Two coding rounds (algorithm, data structures)
   - One system design round
   - One domain-specific round (backend, infrastructure, ML platform depending on team)
   - One behavioral/leadership round

The behavioral round at Uber uses situational judgment questions more than pure STAR-format storytelling. Expect questions about handling disagreements with technical decisions, shipping under ambiguity, and what you do when you disagree with a technical direction but need to move forward.

---

## Preparing for Uber

If you are targeting Uber specifically:

Study H3 and hexagonal grid spatial indexing. It comes up in system design conversations repeatedly, and even basic familiarity signals that you have done real homework.

Understand Cadence/Temporal at the conceptual level. Long-running workflow management is a real pattern in Uber's codebase and interviewers appreciate candidates who understand why you would reach for a workflow engine versus a simple event-driven system.

Prepare a surge pricing design end-to-end. The demand/supply signal collection, the forecasting layer, the multiplier computation, the zone propagation, and the driver incentive mechanisms are all individually discussable. A strong candidate can go deep on any one of them.

Practice Go. You are not required to use it, but being comfortable in Go signals alignment with Uber's current stack and demonstrates real-world language breadth.

Think operationally. For every system you design in an interview, add a section on monitoring, alerting, and degraded operation. Uber post-Kalanick prizes engineers who build for reliability from the start, not as an afterthought.

The depth of Uber's engineering problems — geospatial indexing, real-time global optimization, durable workflow orchestration — makes it one of the more technically interesting companies to work at in the FAANG tier. The interview process is demanding precisely because the work is demanding. Candidates who come in having genuinely studied the infrastructure walk out with an edge that no amount of LeetCode grinding can fully replicate.

## Related Articles

- [Uber Interview Guide](/blog/uber-interview-guide)
- [Uber Surge Pricing System Design](/blog/uber-surge-pricing-system-design)
- [System Design: Ride Sharing](/blog/system-design-ride-sharing)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Real-Time Chat](/blog/system-design-real-time-chat)
