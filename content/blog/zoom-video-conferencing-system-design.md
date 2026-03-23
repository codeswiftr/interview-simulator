---
title: "Zoom Video Conferencing System Design"
description: "How to design Zoom—WebRTC vs SFU architecture, media routing, recording pipelines, and the scalable meeting infrastructure that handled 300M daily participants."
date: "2026-03-21"
category: "System Design"
---

# Zoom Video Conferencing System Design

At its 2020 peak, Zoom served 300 million daily meeting participants. Designing a real-time video conferencing system tests your knowledge of media protocols, latency optimization, and scaling stateful connections. This is among the hardest system design problems—the constraints are unforgiving.

## Requirements

**Functional:**
- Video/audio calls with up to 1,000 participants
- Screen sharing
- Chat, reactions, polls
- Cloud recording and transcription
- Breakout rooms

**Non-functional:**
- Audio latency < 150ms end-to-end (human hearing threshold for conversation)
- Video latency < 300ms
- Scale: 1M concurrent meetings
- Graceful degradation: audio stays clear even on poor networks

## Architecture Approaches: P2P vs MCU vs SFU

**Peer-to-Peer (P2P)**: Direct connection between participants. Fine for 2-3 people. Each participant sends video to every other participant. N(N-1) streams. Fails beyond ~6 participants.

**MCU (Multipoint Control Unit)**: Central server receives all streams, mixes/composites them, sends one combined stream to each participant. Low bandwidth for participants, but server CPU is massive. Used by legacy enterprise systems.

**SFU (Selective Forwarding Unit)**: Central server receives all streams, selectively forwards each participant's stream to others without compositing. Participant receives N-1 streams but server CPU is much lower than MCU.

Zoom uses SFU. Modern WebRTC-based systems all use SFU.

## SFU Design

```
Participant A ──sends── SFU ──sends to A──► streams from B, C, D
Participant B ──sends── SFU ──sends to B──► streams from A, C, D
Participant C ──sends── SFU ──sends to C──► streams from A, B, D
```

Each participant uploads one video/audio stream. The SFU forwards the appropriate streams to each participant. For 50 participants, the SFU forwards 50 streams to 49 participants each = 2,450 forwarding operations per tick. This is manageable.

**Simulcast**: Each client encodes the same video at 3 qualities (1080p, 720p, 360p) and sends all three to the SFU. The SFU selects which quality to forward to each subscriber based on their network bandwidth. This is how Zoom degrades gracefully for participants on weak connections.

## WebRTC and Custom Protocols

Zoom doesn't actually use standard WebRTC. They use their own protocol built on UDP, optimized for their use case. Reasons:
- WebRTC is browser-standard but adds overhead Zoom doesn't need
- Zoom's native apps can use optimized codecs (Opus for audio, VP8/H.264/H.265 for video)
- Custom congestion control (more aggressive than WebRTC's default)

The transport layer is UDP with custom reliability: audio uses FEC (Forward Error Correction) — redundant packets allow recovering from loss without retransmit. Video uses selective NACK: receiver requests retransmission of lost keyframes only (not every frame — losing a non-keyframe is recoverable via interpolation).

## Media Server Architecture

```
Client → TURN/STUN Server (NAT traversal)
       → Media Gateway (entry point)
       → SFU Cluster (media routing)
       → Recording Service (async)
       → Transcription Pipeline (async)
```

**TURN server**: Relays media for clients behind NAT/firewalls that block direct UDP. ~20% of Zoom calls use TURN relay; 80% use direct or STUN-assisted peer connections.

**SFU Cluster**: Stateful. Each meeting is assigned to a specific SFU cluster based on geographic proximity to participants. Meetings with global participants may use a **cascade** of SFUs across regions, linked via dedicated network.

## Meeting Routing

When a meeting starts:
1. Meeting service assigns a **Meeting Connector** (SFU instance) based on host location
2. Participants join by connecting to their geographically nearest SFU edge
3. Edge SFUs connect to the meeting's primary SFU via low-latency backbone
4. Primary SFU distributes streams; edge SFUs relay to their local participants

This geo-distributed SFU cascade reduces last-mile latency — Tokyo participants don't need to reach a US data center.

## Signaling Service

Separate from media routing, the signaling service manages:
- Meeting join/leave events
- Participant metadata (name, video on/off, mute state)
- WebSocket connections for real-time control

Signaling is much lower bandwidth than media. It uses WebSocket connections to stateless signaling servers backed by a shared state store (Redis for participant lists, Kafka for event streaming).

## Adaptive Bitrate and Congestion Control

Zoom constantly adjusts video quality based on network conditions:

- Each media stream has a target bitrate
- SFU monitors packet loss, RTT, and jitter per subscriber
- High loss/jitter: SFU switches to lower quality simulcast tier
- Congestion signals flow back to senders via RTCP

If network degrades badly:
1. First: reduce video resolution
2. Next: reduce frame rate
3. Finally: switch to audio only

Audio is always prioritized — the UX impact of video freeze is tolerable; choppy audio kills a meeting.

## Recording Architecture

Cloud recording is asynchronous:
1. SFU writes media to object storage (S3-compatible) as raw streams during the meeting
2. Post-meeting: a processing pipeline mixes audio/video streams, adds participant names
3. Generates MP4 (standard layout) or individual streams (per-participant recording)
4. Transcription runs via speech-to-text API (Google ASR or Zoom's own model)
5. Storage + download link delivered to host within 30 minutes

Recording doesn't go through the SFU's critical path — it subscribes as a passive "bot" participant.

## Breakout Rooms

Breakout rooms create sub-meetings within a meeting:
- Host assigns participants to rooms
- Each room gets its own SFU context (separate media streams)
- Main session SFU is paused (no video/audio) while breakouts are active
- Host can broadcast to all rooms simultaneously (one-to-many from main SFU to all breakout SFUs)

## Scalability Limits

Per SFU server: ~100 concurrent meetings at 25 participants each = 2,500 simultaneous streams. Scale by adding SFU instances (horizontal scaling within a meeting is limited — one meeting = one SFU context).

For very large meetings (1,000+), cascade multiple SFUs. Only the "active speaker" stream is forwarded in real-time; others receive low-quality thumbnails.

## Interview Tips

Key points for video conferencing system design:

1. **SFU vs MCU tradeoff** — SFU is the right answer for > 6 participants
2. **Simulcast for adaptive quality** — multiple quality streams, SFU selects per subscriber
3. **UDP + FEC + NACK** — reliability without TCP's retransmit delays
4. **Audio prioritization** — always maintain audio quality before video
5. **Geo-distributed SFU cascade** — reduces latency for global participants

The latency constraints (< 150ms audio) are what drive all the UDP/FEC decisions. Make sure your answer explains why TCP is inappropriate for real-time media.
