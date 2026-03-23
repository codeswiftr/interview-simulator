# Zoom's Engineering Deep Dive: How They Scaled 30x in 90 Days and What It Means for Your Interview

In March 2020, Zoom's infrastructure faced a challenge that had no precedent in the industry. Daily meeting participants went from 10 million to 300 million in roughly 90 days. Not 30%, not 3x — 30x. The entire system had been engineered for a world where it would never need to handle the load it was suddenly absorbing. What happened next became one of the most closely-studied scale-up stories in distributed systems engineering, and understanding it is critical if you're targeting a role at Zoom.

This post covers the core engineering decisions that define Zoom's architecture, the tradeoffs they made under pressure, and what their engineers actually work on day to day.

## Video Codec Engineering: Quality on Bad Networks

Zoom's core product promise is "it just works" — a claim that lives or dies on codec performance at the edge, where networks are unreliable, bandwidth fluctuates, and latency is unpredictable.

Zoom uses a layered approach to video encoding built on top of VP8/VP9 (via WebRTC) and their own proprietary codec stack, with the central technique being **Scalable Video Coding (SVC)**. Rather than encoding a single bitrate stream, SVC encodes a base layer plus enhancement layers that can be stripped out as bandwidth degrades.

The adaptive bitrate logic operates on a feedback loop between the client and the media server:

```javascript
// Simplified ABR feedback loop (client-side signaling layer)
class BitrateController {
  constructor(targetBitrateBps, minBitrateBps, maxBitrateBps) {
    this.target = targetBitrateBps;
    this.min = minBitrateBps;
    this.max = maxBitrateBps;
    this.rtt = 0;
    this.packetLossRate = 0;
  }

  // Called on each RTCP receiver report from the media server
  onReceiverReport({ rttMs, lostPacketFraction, jitterMs }) {
    this.rtt = rttMs;
    this.packetLossRate = lostPacketFraction;

    if (lostPacketFraction > 0.1) {
      // >10% loss: aggressive downgrade
      this.target = Math.max(this.min, this.target * 0.7);
    } else if (lostPacketFraction < 0.02 && rttMs < 150) {
      // Network healthy: probe upward gradually
      this.target = Math.min(this.max, this.target * 1.08);
    }

    return this.target;
  }
}
```

This mirrors Zoom's published behavior: they probe bandwidth aggressively upward in healthy conditions but cut hard on loss, because a degraded video call is better than a frozen one. Zoom's client also implements **forward error correction (FEC)** at the RTP layer — redundant packets are sent alongside primary data so that isolated packet drops can be recovered without retransmission latency. For audio, they use the Opus codec with its built-in packet loss concealment, hiding gaps of up to 60ms without audible artifacts.

The key insight: Zoom's codec layer is not a commodity decision. It is the product.

## Media Server Architecture: Why Zoom Is Not Peer-to-Peer

Many video systems start with WebRTC's peer-to-peer model: each participant sends their video directly to every other participant. This works at 2-3 participants but collapses at scale — a participant in a 10-person meeting would need to maintain 9 upstream video connections simultaneously, destroying upload bandwidth and CPU on mobile devices.

Zoom uses a **Selective Forwarding Unit (SFU)** architecture, sometimes called a media router. Each participant sends one upstream to Zoom's media server, and the SFU selectively forwards streams downstream to each subscriber. The critical word is "selectively" — the SFU doesn't transcode (which is expensive), it forwards encoded video frames, choosing which SVC layer to send based on each subscriber's available bandwidth.

Zoom's media server network is a distributed, hierarchical system with nodes in multiple regions. When a call is established, the signaling layer assigns a "home" media server to the meeting based on the geographic centroid of participants. As participants join from different regions, their media traffic is routed to regional edge nodes that then relay to the home server, minimizing the number of hops the most latency-sensitive traffic (the video frames) travels.

Their global **TURN server network** handles NAT traversal — the unsolved problem of enterprise firewalls blocking peer connections. Every client first attempts a direct STUN-based connection; if that fails (which it does in roughly 15-20% of enterprise environments), traffic is relayed through TURN servers. Zoom maintains TURN infrastructure in dozens of regions to keep relay latency under 50ms for 99% of users.

## The 30x Scaling Challenge: Multi-Cloud and Control/Data Plane Separation

When the pandemic hit, Zoom's infrastructure team was running primarily on AWS. Within weeks they had to expand to Oracle Cloud and Azure simultaneously, not because AWS was failing but because AWS couldn't provision capacity in specific regions fast enough. This forced a discipline that became a permanent architectural pattern: **hard separation between the control plane and the data plane**.

The control plane — authentication, meeting scheduling, participant management, signaling — runs on Zoom's own infrastructure and AWS. It is stateful and complex but volume is manageable; starting a meeting generates a handful of API calls.

The data plane — actual media traffic — is where the 30x spike hit. Media servers are stateless in the sense that each server handles individual meeting instances independently. This made horizontal scaling tractable: spin up more media server capacity, route new meetings to new nodes, let existing meetings drain naturally. Zoom used Oracle's bare-metal instances specifically for media server workloads because the predictable, dedicated hardware provided lower jitter than shared-tenancy cloud instances — critical for real-time audio/video.

The multi-cloud expansion exposed operational complexity that Zoom hadn't fully solved: observability across three clouds, different networking primitives, different autoscaling APIs. Their SRE team built a unified metrics layer (built on top of Prometheus and their own aggregation pipeline) that normalized cloud-specific signals into a single operational view.

## End-to-End Encryption: The Controversy and the Technical Reality

In April 2020, Zoom claimed to offer end-to-end encryption. Security researchers immediately pointed out this was not true in the standard meaning of the term — Zoom's servers had access to the encryption keys, enabling them to decrypt meeting content.

The controversy forced Zoom to do something technically difficult: implement genuine E2E encryption for video conferencing at scale.

The challenge is architectural. In a standard E2E encrypted messaging system (Signal, iMessage), you encrypt messages with the recipient's public key. In a multi-party video call, you have N participants, each needing to decrypt streams from N-1 others, and the SFU sits in the middle needing to route packets without decrypting them.

Zoom's solution, shipped in late 2020, uses a **meeting-level key hierarchy**. A meeting leader generates a symmetric meeting key and distributes it to participants via asymmetric encryption (each participant's public key). The media is then encrypted with this shared key before it leaves the client. The SFU receives encrypted RTP packets and forwards them without decrypting — it can still perform SVC layer selection because the SVC layer metadata is in the RTP header, not the payload.

The tradeoff: when E2E is enabled, Zoom's cloud-based features that require server-side access to media — live transcription, recording in the cloud, phone dial-in — are disabled. The server can't do what it can't read. This is a genuine cryptographic boundary, not a marketing claim.

## Interview Implications: What Zoom Engineers Actually Work On

Zoom's engineering teams cluster around a few domains that map directly to the problems described above:

**Media infrastructure** teams work on the SFU, codec integration, and the TURN/STUN network. These roles require deep knowledge of RTP, RTCP, WebRTC internals, and network programming in C++.

**Client platform** teams work on the native clients (Windows, macOS, iOS, Android) with a focus on audio/video pipeline performance, CPU optimization, and battery efficiency.

**Reliability engineering** teams own the observability stack, incident response tooling, and the autoscaling systems that have to respond in under 60 seconds to meeting volume spikes.

**Security engineering** teams work on the E2E encryption implementation, key management infrastructure, and compliance tooling.

**System design questions** Zoom interviewers favor include: design a video conferencing system (the canonical question — they want to see SFU vs P2P reasoning, media server selection, signaling layer design), design an adaptive bitrate system, and design a distributed presence system (who is online, who is in a meeting).

When answering these, demonstrate that you understand the difference between media and signaling, can reason about the tradeoffs between transcoding and selective forwarding, and know why peer-to-peer breaks at scale. Zoom interviews value engineers who have genuinely internalized the constraints of real-time media — latency budgets in milliseconds, jitter sensitivity, the impossibility of TCP for live video — not those who've memorized system design patterns without understanding why they exist.

The 2020 scale-up is not just a company history story. It is a design document. Every architectural decision Zoom made under pressure reflects the real tradeoffs in video infrastructure engineering, and those tradeoffs are exactly what they test for in interviews.
