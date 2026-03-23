---
title: "System Design: Gaming Backend — Leaderboards, Matchmaking, and Real-Time Game State"
description: "How to design a gaming backend in system design interviews — real-time leaderboards with Redis sorted sets, matchmaking algorithms, game state synchronization, and scaling to millions of concurrent players."
date: "2026-03-20"
category: "System Design"
---

# System Design: Gaming Backend — Leaderboards, Matchmaking, and Real-Time Game State

Gaming backend questions are increasingly common in senior system design interviews, particularly at companies like Riot, King, Electronic Arts, Unity, and gaming-adjacent tech companies. The domain combines real-time systems, data structures for leaderboards, low-latency matchmaking, and state synchronization — all at significant scale. This guide provides a complete design with the reasoning interviewers expect.

## Requirements

- **Leaderboard**: Global top-100, friend leaderboard, per-player rank lookup. Updates after every game (~1M games/day, ~12 games/second)
- **Matchmaking**: Match 10 players within 30 seconds with similar skill ratings
- **Game sessions**: 10-minute average game, 100K concurrent games, 100 players per large-scale game
- **Player state**: Player inventory, progress, currency — must be consistent
- **Notifications**: Game results, achievements, rank changes pushed to clients

## Leaderboard Design

Leaderboards are the canonical Redis sorted set problem. Redis ZADD/ZRANK/ZRANGE operations make this efficient at scale.

**Data structure**: `ZADD global:leaderboard <score> <player_id>`. Score is the player's rating or point total. ZADD is O(log N) — fine for millions of players.

**Rank lookup**: `ZREVRANK global:leaderboard <player_id>` returns 0-indexed rank in O(log N).

**Top-K query**: `ZREVRANGE global:leaderboard 0 99 WITHSCORES` returns top 100 with scores in O(log N + K).

**At 1M games/day (12 writes/second)**, a single Redis instance handles this trivially. Redis is single-threaded for commands but processes 100K+ commands/second. Use a Redis Cluster for horizontal scaling if needed.

**Friend leaderboard**: Build a separate sorted set per user containing only their friends' scores. When friends list changes (add/remove friend), update the player's friend leaderboard set. This enables fast `ZREVRANGE user:123:friends_leaderboard 0 9` without scanning the global set.

**Eventual consistency**: Leaderboard updates can be slightly delayed. After a game ends, publish the score update to Kafka. A leaderboard consumer processes updates from the queue. This decouples game completion from leaderboard writes.

**Historical leaderboards**: Weekly/monthly leaderboards use a separate key per time bucket: `ZADD global:leaderboard:2026-03 <score> <player_id>`. At bucket close (end of month), persist the final rankings to PostgreSQL for historical queries.

## Matchmaking System

Matchmaking is a constraint satisfaction problem: find N players with similar skill who are all available.

**ELO/MMR-based matching**: The most common approach. Each player has a numeric matchmaking rating (MMR). Ideal match: all players within ±50 MMR. Relaxed match (after 30s wait): expand to ±100 MMR.

**Architecture**:
1. Player requests match → enters matchmaking queue (Redis sorted set, keyed by MMR)
2. Matchmaking Service scans the queue every 500ms
3. For each waiting player, find the closest-MMR players also waiting
4. When N players found within threshold, create a game session
5. Notify all players via WebSocket/push

**Queue structure**: `ZADD matchmaking:queue <mmr> <player_id>:<timestamp>`. Use `ZRANGEBYSCORE` to find players within MMR range. The timestamp in the value lets you track wait time and expand the MMR range as wait grows.

**Regional queues**: Latency matters in gaming. Use regional queues (US-West, US-East, EU-West, APAC). Match within region first; cross-region match only when queues are thin or player explicitly requests.

**Anti-smurf protection**: High-MMR players using new accounts will have artificially low MMR. Detect via placement match performance analysis, IP clustering, and behavioral signals. Flag accounts for adjusted placement.

## Game Session Architecture

Once players are matched, a Game Server handles the actual gameplay.

**Session allocation**: When a match is created, the Matchmaking Service requests a game server from the Session Manager. The Session Manager maintains a pool of pre-warmed game server instances. On-demand cloud scaling (Kubernetes HPA or custom autoscaler) ensures pool size matches demand.

**State synchronization** (multiplayer real-time games): Two models:

- **Authoritative server**: The server holds all game state. Clients send input; server processes and broadcasts authoritative state. Prevents cheating. Used by most competitive games.
- **Peer-to-peer**: Clients share state directly. Lower latency, but prone to cheating. Used in some casual/mobile games.

For authoritative model: clients send input at 60fps; server ticks at 20fps (common competitive game rate); server sends delta state updates to all clients. Each client runs client-side prediction (applies local inputs immediately) and server reconciliation (corrects prediction errors when authoritative state arrives).

**Game state persistence**: At game end, the server writes the final state (scores, stats, match replay) to object storage. This is append-only — game history is never modified. Aggregate statistics write to PostgreSQL.

## Player Data Consistency

Player inventory and currency require strong consistency — double-spending a currency unit is a serious bug in any game economy.

Use PostgreSQL with row-level locking for inventory mutations. All currency transactions use ACID transactions with serializable isolation.

Caching player data in Redis is fine for reads (inventory display, profile). On write (purchase, reward), update PostgreSQL first, then invalidate or update the Redis cache. Never write to cache before the database.

## Notification Pipeline

Achievement unlocks, rank changes, and game result notifications go through a notification service:
1. Game result written to Kafka
2. Achievement processor consumes events, evaluates achievement rules
3. Rank calculator updates leaderboards
4. Notification service pushes to player's connected WebSocket or queues for push notification

Keep the hot path (game end → result recorded) decoupled from downstream enrichment. Game result recording should be fast; achievement processing can be eventual.
