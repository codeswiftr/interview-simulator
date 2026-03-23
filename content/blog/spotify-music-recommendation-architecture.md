---
title: "Spotify Music Recommendation Architecture"
description: "How Spotify builds Discover Weekly, Spotify Wrapped, and its recommendation engine—audio analysis, collaborative filtering, NLP on playlists, and the infrastructure behind 600M users."
date: "2026-03-21"
category: "System Design"
---

# Spotify Music Recommendation Architecture

Spotify's recommendation system is arguably the best in music streaming. Discover Weekly (updated every Monday) has a cult following. Understanding how it's built—combining audio analysis, collaborative filtering, and NLP on playlist data—is essential preparation for music, media, or any personalization-focused system design interview.

## Scale

- 600M users, 100M+ tracks in catalog
- 4B+ playlists (user-created and editorial)
- 400M+ Discover Weekly playlists generated weekly
- Audio fingerprinting and analysis for every track

## Three Pillars of Spotify Recommendations

Spotify combines three data sources, each capturing different aspects of music affinity:

### 1. Collaborative Filtering

"Users who listen to X also listen to Y." Matrix factorization over the play history matrix.

The interaction matrix is sparse: 600M users × 100M tracks. Spotify processes this with **implicit feedback** (play counts, skips, saves, playlist adds) rather than explicit ratings.

Spotify uses a custom implementation of matrix factorization optimized for implicit feedback (similar to iALS). The resulting embeddings capture acoustic style, genre, energy level, and cultural associations—without knowing what those concepts are explicitly.

### 2. Natural Language Processing on Playlists

Spotify has 4 billion playlists. Playlists have names and track sequences. This is a goldmine:

- Playlist name: "chill morning vibes", "gym bangers 2026", "sad indie hours"
- Track sequence within playlist implies similarity

Treat tracks like words, playlists like sentences. Apply word2vec-style training (specifically song2vec) where tracks appearing in similar playlist contexts have similar embeddings.

This allows Spotify to understand cultural meaning: tracks appearing in "wedding reception" playlists are semantically related even without explicit genre tagging.

### 3. Audio Analysis

For cold-start (new tracks with no listen history), use audio features extracted from the audio signal itself:

- **Mel spectrogram**: 2D representation of frequency over time
- **CNN-based audio model**: trained to predict taste cluster from spectrogram
- **Audio features**: tempo, key, loudness, danceability, energy, valence (Essentia + Echo Nest features)

New tracks get audio-feature embeddings immediately. When a track gets enough listens, collaborative filtering takes over as the dominant signal.

## Discover Weekly Pipeline

Discover Weekly runs as a weekly batch job on Monday mornings (UTC):

```
Step 1: Generate user taste profile
  → Collect past 30 days of play history (weighted: recent > old)
  → Produce user embedding from collaborative filtering model

Step 2: Candidate retrieval
  → ANN search over track embeddings using user embedding as query
  → Retrieve top-10,000 candidates (FAISS index over 100M tracks)
  → Filter out: already heard tracks, explicit content if restricted

Step 3: Ranking
  → Score candidates with multi-signal ranking model
  → Features: CF similarity, audio similarity, NLP similarity, newness, diversity
  → Ensure genre/mood diversity (no 30 similar tracks)

Step 4: Playlist assembly
  → Select 30 tracks optimized for listening flow
  → Order by energy arc (avoid jarring transitions)
  → Cache in user playlist store
```

The entire pipeline runs on a Hadoop/Spark cluster over several hours, completing before Monday morning.

## Audio Embedding Generation

For audio analysis, Spotify uses CNNs trained on spectrograms:

```python
# Simplified audio embedding pipeline
def get_audio_embedding(track_id):
    audio_signal = load_audio(track_id, sample_rate=22050)
    mel_spec = compute_mel_spectrogram(audio_signal, n_mels=128)
    # CNN trained on taste-cluster prediction
    embedding = audio_cnn.forward(mel_spec)  # returns 128-dim vector
    return embedding
```

These embeddings are pre-computed for all 100M tracks and stored in a vector database (approximate NN index).

## Personalized Radio (Autoplay)

When a song ends, Spotify's autoplay selects the next track. This is a different problem—sequential recommendation:

- Context: current track + session history
- Goal: immediate engagement (no skip in first 30 seconds)
- Latency: < 100ms (must be ready before the track ends)

Use a lighter model (pre-cached nearest neighbors + session context adjustment). Pre-compute `k=100` neighbors for every track; at runtime, re-rank neighbors using session context.

## Spotify Wrapped

Yearly personalized story of your listening. This is analytics + personalization:

- Count plays, minutes listened, artist counts from event log (Kafka + BigQuery)
- Compute "audio aura" (mood profile based on valence/energy of top tracks)
- Generate share cards (personalized images) using template service

The engineering challenge: Spotify Wrapped sees 100M+ social shares on a single day. Pre-generate all wrapped stories (December 1 launch date is known), cache aggressively, serve from CDN.

## Feature Store Architecture

```
Online Feature Store (Redis Cluster):
  user:{user_id}:embedding → 256-dim float vector
  user:{user_id}:recent_plays → sorted set by timestamp
  track:{track_id}:embedding → 128-dim float vector

Offline Feature Store (HDFS + Parquet):
  play_history (partitioned by date + user)
  user_embeddings (weekly snapshot)
  track_embeddings (daily refresh for new tracks)
```

## Interview Tips

The audio analysis + NLP + collaborative filtering combination is what makes Spotify's approach uniquely interesting. Key points to hit:

1. **Three data sources** — explain why each captures different aspects of music taste
2. **Cold-start via audio features** — crucial for new artists and independent music
3. **Weekly batch vs real-time** — Discover Weekly is batch; Radio is real-time; explain why
4. **Diversity in results** — pure similarity produces boring playlists; explain diversity injection
5. **Scale** — 100M tracks ANN search requires purpose-built index (FAISS, Annoy, ScaNN)

Spotify's blog has detailed technical posts on all these components — reading them will give you authentic details to mention in interviews.
