---
title: "LinkedIn Feed Ranking System Design"
description: "How LinkedIn's professional feed works—content scoring, professional graph traversal, viral coefficient controls, and the ML pipeline ranking posts for 1 billion members."
date: "2026-03-21"
category: "System Design"
---

# LinkedIn Feed Ranking System Design

LinkedIn's feed is the primary engagement surface for a billion professional users. Unlike social feeds optimized for entertainment, LinkedIn's feed must balance professional value, content quality, and connection relevance without becoming a low-quality engagement farm. This makes it an interesting design case with unique constraints.

## Requirements

**Functional:**
- Show relevant posts from connections, follows, and organizations
- Mix organic posts, job recommendations, and promoted content (ads)
- Handle reshares, articles, and multimedia posts
- Surface professional insights: job postings, skill endorsements, milestones

**Non-functional:**
- 1 billion members, 300M active monthly
- Feed freshness: < 5 minutes for content from close connections
- P99 feed generation < 500ms
- Optimize for professional engagement (comments, shares) over viral spread

## Content Graph

LinkedIn's content graph differs from Twitter/Instagram:

- **First-degree connections**: mutual professional connections (bidirectional)
- **Second-degree**: connections of connections (huge fan-out)
- **Follows**: one-directional; follow a thought leader without being connected
- **Organizations**: companies, schools, groups

Feed candidates come from all these sources. A key challenge: the professional graph is dense (average 200+ connections vs Twitter's 200 follows) and second-degree reach is enormous.

## Two-Stage Pipeline

**Stage 1 — Candidate Generation (offline + near-realtime)**:
- Pull recent posts (last 48h) from user's connections + follows
- Fan-out on write for users with < 10K connections
- Fan-out on read for high-degree nodes (top influencers with millions of followers)
- Store candidates in per-user feed candidate set (Redis sorted set, scored by recency)

**Stage 2 — Feed Ranking (online, per request)**:
- Retrieve up to 1,000 candidates from candidate store
- Score each with ML ranking model
- Filter spam and low-quality content
- Assemble final feed (organic + promoted content interleaved)

## Ranking Model

LinkedIn uses a multi-objective ranking model that optimizes for:

1. **Immediate engagement**: P(comment | post shown), P(like | post shown)
2. **Viral quality**: Does engagement come from thoughtful professionals or bots?
3. **Long-term value**: Does this post type lead to session completion vs bounce?

Features:
- **Poster credibility**: follower count, engagement history, account age, connections in common
- **Content quality**: text length, image/video quality scores, language fluency
- **Topic relevance**: match between post topics and user's professional interests
- **Temporal signals**: post age, velocity of early engagement
- **Social proof**: engagement from user's close connections (if your manager liked something, that's high signal)
- **User context**: device, time of day, session context

The model is a deep neural network (LinkedIn's open-sourced an architecture called "Temporal Attentional Networks" for session-aware ranking).

## Viral Coefficient Control

A key LinkedIn design challenge: viral posts can overwhelm professional content. A meme or a "relatable workplace story" can get 100K shares, flooding everyone's feed.

LinkedIn explicitly **dampens virality**:
- Cap how much a single post contributes to feed slots (max 1 post per entity per feed load)
- Penalize posts with low comment-to-like ratio (likes without comments = passive resharing)
- Boost posts with substantive comments (> 50 characters, multiple commenters)
- Reduce distribution for posts that get "hide" or "not interested" feedback signals

This is a product tradeoff: sacrifice some engagement metrics to maintain feed quality. LinkedIn documented this decision and the resulting 40% reduction in viral "junk" while maintaining overall session time.

## Professional Content Signals

LinkedIn's feed has unique content types:
- **Job change announcements**: High-value, auto-generated. Shown prominently to close connections.
- **Skill endorsements**: Lower priority (can be gamed).
- **Work anniversaries**: Shown at reduced frequency (can become noise).
- **Published articles**: Long-form, shown to followers. Quality-gated by initial engagement.
- **Company posts**: Lower organic reach than personal posts (similar to Facebook's page algorithm).

## Freshness vs Quality Tradeoff

A high-quality post from 2 days ago vs a mediocre post from 5 minutes ago. Which shows first?

LinkedIn uses a **freshness-quality score**:
```
score = quality_score × freshness_decay(age)
freshness_decay(age) = exp(-λ × age_hours)
```

The decay rate λ varies by content type:
- Breaking news / company announcements: fast decay (high λ)
- Evergreen professional advice: slow decay (low λ)
- Personal milestones (promotions): medium decay

## Promoted Content Integration

Ads are interleaved at fixed positions (positions 3, 7, 12, etc.). The ad ranking system runs separately, selecting the highest-bid + most relevant ad. The merged feed respects user ad frequency caps (max N ads per session) and topic overlap limits (don't show the same ad 3 times in one session).

## Feed Caching

Pre-compute feeds for active users:
- Generate ranked feed every 5 minutes for users active in last 24h
- Store in Redis: `feed:{user_id}` → ordered list of post_ids
- On feed request: retrieve cached feed, apply real-time filters (deleted posts, blocked users)
- TTL: 10 minutes (regenerated before expiry for active users)

For users returning after long absence: compute fresh feed on demand (cache miss path).

## Interview Tips

LinkedIn's feed design has several unique aspects worth highlighting:

1. **Viral dampening** — unique to LinkedIn vs consumer social; shows product thinking
2. **Professional signals** — job changes, work anniversaries as first-class ranking signals
3. **Dense professional graph** — fan-out strategy must account for high connection counts
4. **Multi-objective ranking** — quality + freshness + relevance as separate objectives
5. **Ad integration** — always mention when asked about feed systems

The viral dampening decision is the most interesting design choice — be prepared to defend why optimizing for engagement maximization alone would destroy LinkedIn's value proposition.

## Related Articles

- [LinkedIn Software Engineer Interview Guide](/blog/linkedin-software-engineer-interview-guide)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design: Recommendation Engine](/blog/system-design-recommendation-engine)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Notification System](/blog/system-design-notification-system)
