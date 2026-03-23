# Twitter/X Engineering Deep Dive: Real-Time Social Infrastructure at Global Scale

Twitter — now X — built one of the most demanding real-time distributed systems in consumer software. Every tweet is delivered to followers within seconds; the Super Bowl half-time show generates peaks the system must absorb without degradation. The engineering decisions that made this possible, and the architectural challenges that remain, are a window into large-scale social infrastructure design.

## The Timeline Architecture: Fan-Out at Scale

Twitter's core technical challenge is the timeline: when you tweet, your tweet must appear in the feeds of your followers (potentially millions of them) in near real-time. The naive solution — reading all tweets from followed accounts at query time — does not scale. Twitter's solution is fan-out on write: when a tweet is posted, the system pre-computes and writes it into the Redis timelines of each follower.

This creates a different scaling problem: a celebrity with 50 million followers generates 50 million writes per tweet. Twitter's solution for high-follower accounts is a hybrid: celebrity tweets are not fanned out at write time; instead, they are injected at read time into the timeline. The fan-out-on-write model applies to normal users; the fan-out-on-read model applies to accounts above a follower threshold. The timeline service merges both at query time.

```python
class TimelineService:
    def get_home_timeline(self, user_id, count=20):
        # Step 1: Get pre-computed fan-out timeline from Redis
        cached_tweets = self.redis.lrange(f"timeline:{user_id}", 0, count * 2)
        
        # Step 2: Identify followed celebrities (above fan-out threshold)
        celebrity_ids = self.get_celebrity_followings(user_id)
        
        # Step 3: Get recent tweets from celebrities directly
        celebrity_tweets = []
        for celeb_id in celebrity_ids:
            tweets = self.tweet_store.get_recent(celeb_id, count=5)
            celebrity_tweets.extend(tweets)
        
        # Step 4: Merge and sort by timestamp
        all_tweets = list(cached_tweets) + celebrity_tweets
        all_tweets.sort(key=lambda t: t.created_at, reverse=True)
        return all_tweets[:count]
```

## FlockDB and Graph Storage

Twitter's social graph — who follows whom — is stored in a custom distributed graph database called FlockDB (open-sourced but now deprecated). The core operation is bidirectional follow traversal: given a user, find all followers and all followings efficiently.

FlockDB shards by user ID. Each user's adjacency list (the list of their followers and their followings) lives on a specific shard, determined by a consistent hash of the user ID. This makes single-user queries fast (one shard lookup), but cross-user operations (mutual follows, graph traversal) require scatter-gather across shards.

The modern X stack has migrated much of this to internal services, but the fundamental sharding architecture — shard by user ID, denormalize follow relationships bidirectionally — remains the pattern.

## Real-Time Search: Earlybird

Twitter's search is powered by Earlybird, a custom Lucene-based index designed for real-time ingestion. Standard Lucene indexes are immutable segments that are merged over time; Earlybird adds a mutable in-memory index that accepts new documents in real time, alongside the immutable historical segments.

The engineering challenge is that tweets must be searchable within seconds of posting. Earlybird achieves this by maintaining a hot in-memory index for recent tweets that is continuously updated, then periodically flushing and merging into the immutable segment layer.

Ranking for search at Twitter is not just text relevance — it incorporates social signals (retweet velocity, engagement from influential accounts, account authority) to surface the most relevant tweets. This blending of full-text search and social graph signals is characteristic of Twitter's ranking infrastructure across products.

## Handling Traffic Spikes: QoS and Load Shedding

Twitter traffic is highly bursty. Global events (sports finals, elections, celebrity deaths) generate spikes that can be 5-10x normal load with almost no warning. The infrastructure must absorb these gracefully.

Twitter's approach involves several layers:

**Quality of Service tiers**: Not all traffic is equal. Timeline reads from the official apps get higher priority than third-party API calls. During overload, lower-priority traffic is shed first.

**Degraded modes**: The timeline service can serve a degraded timeline (fewer sources, older data) when it cannot complete a full merge. Users see a slightly less fresh timeline rather than an error.

**Precomputed trending**: The trending topics algorithm runs continuously and caches results. During a spike, the trending list does not recompute — it serves the cached version. Freshness degrades; availability is maintained.

## The 2022-2023 Architecture Changes

The X ownership transition was accompanied by significant infrastructure reduction. The engineering team was reduced substantially, and many reliability systems were simplified or removed. The public failures during major events in late 2022 and 2023 reflected this.

From a systems design perspective, the lesson is that reliability properties of large distributed systems are not static — they require continuous investment. The infrastructure Twitter built to handle Super Bowl traffic peaks required specific capacity planning, chaos engineering, and operational runbooks. Reducing the team maintaining those systems reduces the reliability ceiling.

## Interview Implications

Twitter/X interviews have historically tested distributed systems depth. Common topics:

**Design Twitter's timeline**: The fan-out on write vs. read trade-off is the core question. Strong answers address: why you need both strategies, how to determine the threshold, how to handle the merge at read time, and what happens during the follower count spike.

**Design Twitter search**: Real-time search indexing is the distinguishing challenge. Earlybird's architecture — mutable in-memory index plus immutable historical segments — is the standard pattern, derived from Lucene's design.

**Rate limiting at scale**: Twitter's API rate limiting operates at the per-user, per-app, and global levels. Implementing rate limiting with Redis and token bucket or sliding window algorithms is a common coding follow-up.

The most revealing interview signal is whether candidates understand the fan-out problem — it is a genuine engineering insight, not just a fact to memorize.

## Related Articles

- [Twitter/X Software Engineer Interview Guide](/blog/twitter-x-software-engineer-interview-guide)
- [Twitter Trending Topics System Design](/blog/twitter-trending-topics-system-design)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Notification System](/blog/system-design-notification-system)
