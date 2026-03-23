---
title: "Designing a Feature Flag System"
description: "How to build a production-grade feature flag system—flag evaluation, targeting rules, gradual rollouts, kill switches, and the infrastructure used by LaunchDarkly and similar platforms."
date: "2026-03-21"
category: "System Design"
---

# Designing a Feature Flag System

Feature flags (also called feature toggles or feature gates) are one of the most impactful developer tools for modern software delivery. They enable continuous deployment without continuous release, A/B testing at the infrastructure level, and instant rollback without a deployment. Building a feature flag system is an excellent system design question that tests distributed systems, performance, and product thinking.

## Why Feature Flags Matter

Without feature flags:
- Deploying new code = releasing to all users simultaneously
- Rollback = redeploy old code (5-20 minutes)
- A/B testing = complex infrastructure work

With feature flags:
- Deploy code → release to 1% of users → monitor → ramp to 100%
- Rollback = flip a switch (milliseconds)
- A/B testing = configure targeting rules, no code change

## Requirements

**Functional:**
- Create flags with multiple variations (boolean, string, number, JSON)
- Target rules: show variation A to users in segment X, variation B to everyone else
- Gradual rollouts: 1% → 5% → 10% → 50% → 100%
- Kill switches: immediately disable a feature for all users
- Audit log of all flag changes
- SDKs for multiple languages (server-side and client-side)

**Non-functional:**
- Flag evaluation: < 1ms (in the hot path of every request)
- Propagation: flag changes visible to all SDK instances within 30 seconds
- 100% availability for flag reads (even if flag service is down, fall back to last known state)
- Support 10,000 flags, 100M monthly active users

## Core Data Model

```sql
CREATE TABLE flags (
    flag_id      VARCHAR(64) PRIMARY KEY,
    name         VARCHAR(256),
    description  TEXT,
    variations   JSONB,  -- [{value: true, name: "on"}, {value: false, name: "off"}]
    default_rule JSONB,  -- {percentage: [{variation: 0, weight: 10000}]} -- 100% off
    targeting    JSONB,  -- ordered list of rules
    is_enabled   BOOLEAN,
    created_at   TIMESTAMP,
    updated_at   TIMESTAMP
);

CREATE TABLE flag_history (
    event_id     BIGINT PRIMARY KEY,
    flag_id      VARCHAR(64),
    changed_by   VARCHAR(64),
    change_type  VARCHAR(32),
    old_config   JSONB,
    new_config   JSONB,
    created_at   TIMESTAMP
);
```

A flag's targeting config is a list of ordered rules:
```json
{
  "rules": [
    {
      "conditions": [{"attribute": "email", "operator": "ends_with", "value": "@company.com"}],
      "variation": "on",
      "weight": 10000
    },
    {
      "conditions": [],  // matches everyone else
      "percentage": [{"variation": "on", "weight": 1000}, {"variation": "off", "weight": 9000}],
      // 10% of remaining users see "on"
    }
  ]
}
```

## Flag Evaluation Logic

```python
def evaluate_flag(flag, user_context):
    # 1. Check if flag is enabled
    if not flag.is_enabled:
        return flag.off_variation

    # 2. Iterate targeting rules in order
    for rule in flag.rules:
        if rule.matches(user_context):
            return rule.get_variation(user_context, flag.flag_id)

    # 3. Fall through to default rule
    return flag.default_rule.get_variation(user_context, flag.flag_id)

def get_variation_by_percentage(rule, user_context, flag_id):
    # Consistent bucketing: same user always gets same variation
    bucket_key = f"{flag_id}:{user_context.user_id}"
    bucket = hash(bucket_key) % 10000  # 0-9999
    cumulative = 0
    for variation in rule.percentage:
        cumulative += variation.weight
        if bucket < cumulative:
            return variation.value
    return rule.percentage[-1].value
```

The consistent bucketing (hash of flag_id + user_id) ensures a user in the 10% rollout sees the same variation across requests and devices.

## SDK Architecture

**Server-side SDK** (Node.js, Go, Python, Java):
- Downloads full flag configuration on startup
- Evaluates flags locally (no network call per evaluation)
- Polls for updates every 30 seconds (or streams via SSE/WebSocket)

```python
client = FeatureFlagClient(sdk_key="sdk-server-xxx")
client.wait_for_initialization()

variation = client.variation("new-checkout-flow", user, default=False)
if variation:
    render_new_checkout()
else:
    render_old_checkout()
```

Local evaluation is critical: flags appear in the hot path of every request. Network call per evaluation would add 10-50ms latency to every endpoint. Caching the full config locally eliminates this.

**Client-side SDK** (JavaScript, iOS, Android):
- Fetches only the flags relevant to the current user on page/app load
- Updates via SSE for real-time changes
- Stores in localStorage for offline access

## Flag Delivery: Streaming Updates

Server-side SDKs need fresh flag configs. Two approaches:

**Polling**: SDK requests `/flags/config?hash={current_hash}` every 30 seconds. If hash unchanged, returns 304 Not Modified (cheap). If changed, returns new config. Simple, reliable.

**Streaming (SSE/WebSocket)**: Flag service streams change events to connected SDKs. Sub-second propagation. More complex, requires persistent connections.

LaunchDarkly uses streaming by default for server SDKs, polling for mobile (to save battery).

## Flag Service Architecture

```
SDK → CDN Edge Cache (config hash check)
       → Flag Delivery Service (stateless)
       → Redis (flag configs, low latency reads)
       → Flag Management API
       → PostgreSQL (source of truth)
```

When a flag is updated:
1. Management API writes to PostgreSQL + publishes event to Kafka
2. Kafka consumer updates Redis
3. Flag Delivery Service SSE connection sends update to all connected SDKs
4. CDN cache invalidated

The CDN edge cache handles polling at scale: 100K SDK instances polling every 30s = 3,333 requests/second. With CDN serving unchanged configs as 304s, this is trivially cheap.

## Circuit Breaker: SDK Fallback

What if the flag service is down? SDKs must not fail:
- Server SDKs cache last-known-good config in memory
- Client SDKs cache in localStorage/UserDefaults
- Flag evaluations continue using cached config
- Default value returned only if cache is empty (first request, cold start)

This is why flag availability is 100% — the evaluation is local; the service is only needed for updates.

## Analytics and Experimentation

Every flag evaluation can be logged:
```
{flag_id, user_id, variation_served, timestamp, request_context}
```

These events feed into analytics:
- Experiment analysis: compare metrics (conversion, latency) across variation groups
- Flag health: usage rate per variation, flag coverage
- Stale flags: flags that haven't been evaluated in 30 days → candidates for removal

The analytics pipeline is Kafka → Spark → data warehouse (BigQuery/Redshift). Real-time stats for quick experiment checks; batch jobs for statistically rigorous analysis.

## Interview Tips

Feature flag systems are popular because they intersect multiple domains:

1. **Local SDK evaluation** — explain why network-per-call is unacceptable
2. **Consistent bucketing via hash** — same user always gets same variation
3. **SSE/polling tradeoff** — streaming for fast propagation vs polling for simplicity
4. **Circuit breaker (cached fallback)** — flags must work even when service is down
5. **Percentage rollout mechanics** — how to implement gradual rollout correctly

A common interviewer follow-up: "How do you ensure users don't flip between variations?" That's answered by the hash-based bucketing. Make sure you explain it clearly — that's the key correctness insight.
