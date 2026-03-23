# Intercom Engineering Deep Dive: Customer Messaging Infrastructure

Intercom sits at a peculiar intersection: it is simultaneously a real-time messaging platform (low latency, high availability, stateful connections), a behavioral analytics system (ingesting and processing billions of user events), and a marketing automation tool (evaluating dynamic rules against large user populations to decide who gets which message when). Each of these problems is hard independently. Running them as one integrated system that serves over 25,000 businesses creates engineering constraints that are not obvious from the outside.

This post covers the infrastructure decisions behind Intercom's core capabilities, why they are designed the way they are, and what that means if you are preparing for a technical interview there.

---

## Real-Time Messaging: WebSocket Infrastructure at Scale

Every Intercom Messenger widget on a webpage or in a mobile app maintains a persistent connection to Intercom's servers. At peak load, that is millions of simultaneous connections. The connection has to be fast to establish (customers notice slow chat widget loads), resilient (mobile apps frequently disconnect and reconnect), and consistent (a message sent while the user was offline needs to deliver exactly once when they reconnect).

### Connection Architecture

Intercom's messenger connections are handled by a gateway tier of servers whose sole responsibility is maintaining WebSocket connections. This tier is intentionally stateless: gateway servers do not store message history or user state. They hold the connection, route inbound messages to backend services, and push outbound events from a pub/sub subscription.

This separation matters at scale. WebSocket connections are long-lived and consume memory proportional to connection count, not request rate. A traditional request-handling server optimized for throughput is poorly suited to holding a million idle connections. The gateway tier can be scaled purely on connection count without carrying the weight of business logic.

```go
// Simplified gateway connection handler
type GatewayServer struct {
    pubsub   PubSubClient
    router   MessageRouter
    sessions sync.Map // connectionID -> *Session
}

type Session struct {
    conn       *websocket.Conn
    userID     string
    workspaceID string
    sub        PubSubSubscription
}

func (g *GatewayServer) HandleConnection(conn *websocket.Conn, userID, workspaceID string) {
    session := &Session{
        conn:        conn,
        userID:      userID,
        workspaceID: workspaceID,
    }

    // Subscribe to events for this user
    channelKey := fmt.Sprintf("user:%s:workspace:%s", userID, workspaceID)
    session.sub = g.pubsub.Subscribe(channelKey)
    g.sessions.Store(conn.RemoteAddr().String(), session)

    defer func() {
        session.sub.Unsubscribe()
        g.sessions.Delete(conn.RemoteAddr().String())
    }()

    // Fan-out inbound and outbound concurrently
    go g.pumpOutbound(session)
    g.pumpInbound(session)
}

func (g *GatewayServer) pumpOutbound(s *Session) {
    for event := range s.sub.Events() {
        if err := s.conn.WriteJSON(event); err != nil {
            return // Connection closed
        }
    }
}
```

### Message Delivery State Machine

Intercom's message delivery model tracks four states: `sent` (written to the server), `delivered` (the client's WebSocket connection acknowledged receipt), `seen` (the user focused the conversation view), and `replied`. Each transition is an event in the message's history.

The engineering challenge is that "delivered" and "seen" require a round-trip confirmation from the client. On unreliable mobile connections, these confirmations may arrive out of order, arrive multiple times (retry logic), or not arrive at all. The server must handle idempotent delivery — applying a state transition that has already been applied must be a no-op, not an error.

Intercom implements this with event sourcing for message state: each state transition is appended to an immutable log. The current state is derived from the log by replaying transitions in order. Duplicate events are deduplicated by event ID before appending. This design means the delivery system can safely retry any operation and guarantees eventual consistency even when confirmations arrive late.

---

## User Segmentation Engine: Evaluating Rules at Population Scale

Intercom's most technically interesting system is its segmentation engine. Segmentation is how Intercom decides which users receive which automated messages, which product tours are triggered, and which users appear in filtered lists in the operator inbox.

A segment is a set of rules evaluated against user properties and behavioral events. A simple segment might be: `plan = "professional" AND last_seen_at > 30 days ago AND has_used_feature("dashboard") = false`. An operator might define hundreds of segments, each evaluated against a user population of millions.

### Dynamic vs. Static Segment Evaluation

Static segments are lists that are computed once and manually updated. Dynamic segments are re-evaluated continuously as user properties change. The dynamic evaluation problem is where the engineering gets interesting.

The naive approach — re-evaluate all segments for all users whenever any user property changes — does not scale. A single user event (a page view, a feature interaction) would trigger evaluation of every segment that includes behavioral conditions, across a user population of millions.

Intercom inverts this with a reverse index: for each user property and event type that appears in any segment rule, an index maps that property/event to the set of segments that reference it. When a user property changes, the system looks up only the segments that care about that property, then re-evaluates just those segments for just that user.

```python
class SegmentEvaluator:
    def __init__(self):
        # property_name -> set of segment IDs that reference it
        self.property_index: dict[str, set[str]] = defaultdict(set)
        self.segments: dict[str, Segment] = {}

    def index_segment(self, segment: Segment) -> None:
        self.segments[segment.id] = segment
        for rule in segment.rules:
            self.property_index[rule.property_name].add(segment.id)

    def on_user_property_changed(
        self,
        user_id: str,
        changed_property: str,
        user_context: UserContext,
    ) -> list[SegmentMembership]:
        # Only evaluate segments that reference the changed property
        affected_segment_ids = self.property_index.get(changed_property, set())
        results = []

        for segment_id in affected_segment_ids:
            segment = self.segments[segment_id]
            is_member = self._evaluate_segment(segment, user_context)
            results.append(SegmentMembership(
                user_id=user_id,
                segment_id=segment_id,
                is_member=is_member,
            ))

        return results

    def _evaluate_segment(self, segment: Segment, ctx: UserContext) -> bool:
        # AND semantics — all rules must pass
        return all(self._evaluate_rule(rule, ctx) for rule in segment.rules)

    def _evaluate_rule(self, rule: SegmentRule, ctx: UserContext) -> bool:
        value = ctx.get_property(rule.property_name)
        match rule.operator:
            case "eq": return value == rule.value
            case "gt": return value > rule.value
            case "contains": return rule.value in (value or "")
            case "event_count_gte":
                count = ctx.get_event_count(rule.event_name, rule.time_window_days)
                return count >= rule.value
            case _: return False
```

### Behavioral Event Processing

Segment rules that reference behavioral events (number of page views, feature usage frequency, last activity date) require Intercom to process and aggregate event streams in near real-time. An event fires when a user views a page, clicks a button, or triggers any tracked action. These events flow into a processing pipeline that updates per-user aggregates.

The pipeline architecture is a classic Lambda-style design: a streaming layer (Kafka consumers) processes events in real time to update hot aggregates (recent event counts, last-seen timestamps), while a batch layer periodically recomputes full historical aggregates for consistency. The hot aggregates are stored in a low-latency key-value store (Redis), with PostgreSQL as the source of truth for full user records.

---

## Inbox Routing: AI-Powered Conversation Assignment

Intercom's inbox handles inbound conversations from customers to support teams. Like Zendesk's routing, the problem is assigning conversations to the right agent or team. Intercom's approach leans more heavily on ML-based intent classification as a first-class input to routing.

An inbound conversation is passed through a classification model that predicts: likely topic, estimated urgency, and recommended team. These predictions are combined with operator-configured routing rules (if topic = "billing" → billing team, if customer tier = "enterprise" → priority queue). The ML predictions fill in routing decisions when explicit rules do not match.

The model is trained on historical conversation outcomes: given the first message of a conversation, predict which team eventually resolved it and how urgently. This framing — routing as a retrospective prediction problem — means the training data is generated naturally from resolved conversations without requiring manual labeling.

---

## Data Pipeline: Billions of Events for Segmentation and Analytics

Intercom's user event volume is in the billions per day across all customer workspaces. This data drives segmentation, the behavioral analytics product, and the ML models underlying routing and message recommendations.

The pipeline is built around Kafka as the central event bus. Events arrive from web (JavaScript SDK), mobile (iOS/Android SDKs), and server-side API calls. Each event is a structured record: workspace ID, user ID, event name, timestamp, and a properties map. The Kafka consumer fleet handles deduplication (the same event may arrive multiple times from mobile clients with retry logic), enrichment (joining event records with current user properties from a cache), and fan-out to downstream consumers.

Downstream consumers include: the segment evaluation system described above, a time-series aggregation pipeline that maintains event count windows for segment rule evaluation, an analytics warehouse (events are copied to a columnar store for operator-facing analytics queries), and the ML feature pipeline that generates training data for routing and recommendation models.

The engineering decision to run all of this on a shared Kafka cluster with workspace-level partitioning (each workspace's events land on the same partition set) has significant implications for isolation. A workspace with unusually high event volume can cause lag in that workspace's partition without affecting others. Consumer groups are configured per downstream system, so the segment evaluation consumer can lag independently from the analytics warehouse consumer.

---

## Interview Implications

Intercom's interviews focus on distributed systems, real-time infrastructure, and data pipeline design. The segmentation engine is a canonical example of the kind of problem they ask about: given a large user population and a set of continuously evaluated rules, how do you make rule evaluation efficient as properties change? The reverse index pattern — inverting segment rules so that property changes look up affected segments rather than re-evaluating all segments — is the core insight, and it generalizes to many rule evaluation problems.

For messaging infrastructure questions, practice WebSocket architecture at scale: how do you handle millions of simultaneous connections, what does the gateway/backend separation look like, and how do you implement exactly-once delivery with idempotent state transitions. The four-state delivery model (sent, delivered, seen, replied) is a common interview topic because it requires reasoning about distributed state and client-server round trips with unreliable networks.

For data pipeline questions, be ready to discuss Kafka consumer group isolation, the trade-off between Lambda and Kappa architectures for event aggregation, and the specific challenges of multi-tenant event pipelines where one customer's volume should not degrade another's. These are not hypothetical for Intercom — they are operational realities that shape every architectural decision in their data infrastructure.
