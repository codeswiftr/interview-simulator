# Spotify Software Engineer Interview Guide 2024: Process and Preparation

Spotify is one of the world's leading audio streaming platforms — 600M+ users, 100M+ tracks, 5M+ podcasts. Their engineering is known for the "Spotify model" (Squads, Tribes, Chapters, Guilds), a data-driven culture, and deep investment in streaming infrastructure and ML personalization. Here's what their interviews actually test.

## Spotify's Engineering Culture

Spotify's culture values:
- **Autonomy and alignment**: Teams (Squads) own their domain end-to-end. Minimal process overhead. "Be Autonomous, Be Accountable."
- **Data over opinions**: Decisions are backed by experiments. Feature teams run A/B tests before shipping at scale.
- **Fail fast, learn faster**: Postmortems are blameless. Degraded releases are acceptable; prolonged outages are not.
- **Backend systems at scale**: 600M users streaming audio simultaneously. Infrastructure, reliability, and efficiency are first-class concerns.

The engineering blog (engineering.atspotify.com) is required reading — interviewers reference it in system design discussions.

## Interview Format

1. **Recruiter screen** (30 min) — role fit, basics
2. **Technical screen** (60-90 min) — coding + discussion
3. **Virtual onsite** (4-5 rounds):
   - 2 coding rounds
   - 1 system design round
   - 1 behavioral / culture round
   - Occasionally: domain-specific (ML, mobile, infrastructure)
4. **Hiring committee review** (3-5 days)

Spotify interviews vary more by team than most FAANG-adjacent companies — a backend infrastructure team interview differs significantly from a mobile or ML platform team interview. Research your specific team before the onsite.

## Coding Rounds

Spotify's coding bar is solid — LeetCode medium is the floor, medium-hard for senior/staff. The focus is on clean, working code with clear communication.

**High-frequency topics:**
- Arrays, hashmaps, strings
- Trees and graphs
- Priority queues and heaps
- Dynamic programming (moderate)
- Sorting and searching

**Spotify-specific problem flavors:**

*Playlist management:*
> "Design a playlist system that supports: add song, remove song, shuffle (Fisher-Yates), next, previous. Bonus: implement 'smart shuffle' that avoids playing the same artist consecutively."

Tests data structures for sequence management + algorithm knowledge (Fisher-Yates shuffle).

```python
import random

class Playlist:
    def __init__(self):
        self.songs = []
        self.index = -1

    def add(self, song: str):
        self.songs.append(song)

    def shuffle(self):
        # Fisher-Yates in-place shuffle
        for i in range(len(self.songs) - 1, 0, -1):
            j = random.randint(0, i)
            self.songs[i], self.songs[j] = self.songs[j], self.songs[i]
        self.index = 0

    def next(self) -> str:
        self.index = min(self.index + 1, len(self.songs) - 1)
        return self.songs[self.index]

    def prev(self) -> str:
        self.index = max(self.index - 1, 0)
        return self.songs[self.index]
```

*Recommendation deduplication:*
> "Given a stream of song play events (user_id, song_id, timestamp), find the top K songs a user has NOT heard, ranked by global play count."

Set operations + heap for top-K. Tests ability to handle user state vs. global aggregates.

*Podcast chapter navigation:*
> "Given a podcast with N chapters (start_time, end_time, title), implement: seek to time T (return chapter), jump to next chapter, jump to previous chapter."

Binary search on time intervals — clean algorithm with real product context.

*Artist graph (related artists):*
> "Given a list of (artist1, artist2) pairs representing 'fans of artist1 also listen to artist2', find all artists within K hops of a given artist."

BFS/DFS with depth limit. Spotify uses artist graphs for recommendation.

## System Design Round

Spotify's system design questions focus on streaming infrastructure, content delivery, and recommendation systems.

**Common questions:**
- Design Spotify's audio streaming infrastructure
- Design the "Discover Weekly" recommendation pipeline
- Design Spotify's search (artist, track, podcast)
- Design a podcast notification system (new episode alerts)
- Design Spotify's real-time listening activity (friend feed, concerts nearby)

**Audio streaming design (canonical Spotify question):**

*Core components:*

**CDN strategy**: Audio files are large (3-8 MB per song at 320kbps). Content distribution matters. Pre-position popular content at CDN edges. Long-tail content served from origin with aggressive caching headers.

**Adaptive bitrate**: Detect network quality, serve appropriate quality (96/160/320kbps). Pre-buffer next segments while current plays. Use HLS or DASH chunked format — 5-10 second segments.

**Gapless playback**: Start prefetching the next track before current track ends (at ~90% progress). Decodes overlap. Spotify's gapless is a key differentiator.

**Offline mode**: Download tracks to device. Encrypted with user-specific key (DRM). Sync state: which tracks are downloaded, which have been updated/removed.

**Rights enforcement**: Track playback only allowed in licensed territories. Country check at play initiation. Encrypted stream so raw audio can't be extracted from CDN.

**Architecture:**
```
Client → CDN (regional) → Origin storage (GCS/S3)
       ↓
Metadata API → Track service (licenses, URIs)
       ↓
Playback reporting → Event pipeline (Kafka) → Analytics + Royalty calculations
```

**Discover Weekly (ML pipeline design):**

This is a frequently asked Spotify design question. Key components:

1. **Listening history**: Raw play events (song, duration, context) → filtered for "quality" listens (>30 seconds, not skipped)
2. **Collaborative filtering**: Users who listen to similar songs have similar taste. Matrix factorization (ALS) over a user×song implicit feedback matrix.
3. **Content signals**: Audio features (tempo, energy, danceability) from acoustic analysis. Genre embeddings from knowledge graph.
4. **Freshness**: Discover Weekly resets every Monday. Recency bias — don't re-recommend songs heard in last 3 months.
5. **Diversity**: Inject variety: different genres, different popularity tiers, some familiar + some new artists.
6. **Offline batch pipeline**: Weekly batch job (Spark/BigQuery) → candidates → ranking model → playlist construction → push to clients.

Key numbers to know: 400M+ Discover Weekly playlists generated weekly, at ~5-10 second generation time per user.

## The Behavioral Round

Spotify's behavioral round is values-focused. They assess alignment with their culture, not just past experiences.

**"Tell me about a time you made a technical decision that impacted users negatively. What happened?"**
Blameless postmortem mentality. Walk through: what broke, how you detected it, how you mitigated, what changed afterward.

**"Describe how you've worked in a highly autonomous team. What did autonomy enable? What made it harder?"**
Spotify's Squad model gives teams high autonomy. Show you've operated this way and understand both benefits (speed, ownership) and challenges (coordination, alignment).

**"Tell me about an experiment you ran that failed. What did you learn?"**
Data-driven culture — failing experiments are expected and valued. Show you ran it rigorously, accepted the null result, and changed your direction based on data.

**"How do you make decisions when you have incomplete information?"**
Common in streaming/infrastructure context. Show structured thinking: what do you know, what can you instrument, what can you test, what's the reversibility of the decision.

## Domain-Specific: ML Platform Round

For ML-adjacent roles, Spotify adds domain questions about their ML infrastructure (Hendrix, Klio, Beam pipelines).

**"How would you serve a recommendation model for 600M users at low latency?"**
Two-stage retrieval: cheap retrieval model generates candidates (ANN search via FAISS/ScaNN), expensive ranking model scores top-K candidates. Cache popular user embeddings. Pre-compute weekly playlists (Discover Weekly) vs. real-time context-sensitive recommendations (Radio).

**"How do you handle the cold-start problem for new users?"**
Options: demographic-based fallback, onboarding genre selection, content-based similarity before collaborative signals accumulate, popularity-weighted sampling. Spotify uses the "taste survey" at signup.

## Preparation Timeline

**Week 1: Coding**
- 20 LeetCode medium problems (graphs, heaps, BFS/DFS)
- Implement: Fisher-Yates shuffle, LRU cache, top-K stream
- Read Spotify's engineering blog — 3-4 technical posts

**Week 2: System design**
- Deep-dive on CDN + adaptive bitrate streaming
- Design audio streaming and Discover Weekly pipeline
- Study collaborative filtering basics (matrix factorization, ALS)

**Week 3: Domain depth**
- Read Spotify's A/B testing practices (they've published extensively)
- Understand Squad model — read Henrik Kniberg's "Spotify Engineering Culture" videos
- Study Kafka basics (Spotify is heavily Kafka-dependent)

**Week 4: Behavioral + research**
- 8 STAR stories mapped to Spotify values (autonomy, data-driven, blameless culture)
- Research the specific team: playlist, personalization, infrastructure, podcast, mobile
- Understand Spotify's current strategic focus (audiobooks, live audio, creator tools)

## What Makes Spotify Different

Most big-tech companies have strong technical bars. What distinguishes Spotify:

**Data culture is real.** Teams run experiments before shipping at scale. Engineers who've worked in this environment — where you don't ship because you believe in the feature, you ship when the experiment proves it works — fit better. If you've run A/B tests in prior roles, lead with this.

**Scale with taste.** Spotify's product has a distinctive aesthetic sensibility. Engineers here care about the listening experience — gapless playback, shuffle algorithms that feel human, UI that disappears when you just want to hear music. Technical work that improves product feel, not just metrics, is valued.

**The Squad model.** Teams have high autonomy but must coordinate across Squads through deliberate alignment mechanisms (tech roadmaps, guilds for horizontal concerns like security/reliability). Engineers who've worked in distributed team structures where you can't just walk to someone's desk understand this friction viscerally.

That combination — technical rigor, comfort with data-driven decision making, and product sensibility — is what a strong Spotify engineer looks like in an interview.
