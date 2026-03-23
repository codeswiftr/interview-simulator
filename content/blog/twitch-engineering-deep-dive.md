# Twitch Engineering Deep Dive: Live Video and Real-Time Community Infrastructure

Twitch handles over 100,000 concurrent live streams, serves millions of simultaneous viewers, and processes chat messages at a rate that spikes into the millions per second during major events. The engineering decisions behind those numbers show up constantly in system design interviews — not because interviewers expect you to know Twitch's internal architecture, but because the problems Twitch solved are canonical examples of real-time distributed systems challenges.

## Video Transcoding Pipeline: HLS and Adaptive Bitrate at Scale

When a streamer goes live on Twitch, their encoder (typically OBS or Twitch's own software) pushes an RTMP stream to a Twitch ingest server. From that ingest point, Twitch must transcode the stream into multiple quality levels — typically 1080p60, 720p60, 480p, and 360p — and package those into HLS (HTTP Live Streaming) segments that can be served from a CDN to millions of viewers simultaneously.

The transcoding step is where the compute cost lives. Transcoding a single 1080p60 stream to five output quality levels in real time requires significant GPU or CPU resources. Multiply that by 100,000 concurrent streams and you have one of the largest real-time media compute workloads in the world. Twitch handles this through a combination of purpose-built transcoder farms and intelligent routing: not every stream gets transcoded at all quality levels. Partner and affiliate streams get full transcoding; smaller streams may only receive a single quality pass.

The output of transcoding is a stream of HLS segments — typically 2-second chunks of video encoded in H.264 or H.265, plus a continuously-updated M3U8 playlist file. The manifest tells the player which segments are available and at which quality levels. A viewer's player polls the manifest every few seconds, then fetches the segment URLs it hasn't seen yet. This polling model is intentionally simple: it means HLS players are stateless and can be served entirely from a CDN without any persistent connection to an origin server.

The adaptive bitrate logic runs entirely on the client. The player monitors its own download throughput and buffer health, and switches quality levels by requesting segments from a different quality stream. This is a pull model, which is why HLS scales horizontally — segment files are static, CDN-cacheable, and require no per-viewer server state.

## Chat: IRC-Over-WebSocket at Millions of Messages Per Second

Twitch chat is architecturally one of the most interesting parts of the platform because it has to solve a problem that video does not: it's a multi-writer fan-out system, not a single-writer broadcast. Anyone in a channel can send a message, and every connected viewer must receive it with low latency.

Twitch's chat protocol is IRC transported over WebSocket. This is a deliberate choice: IRC is a simple, well-understood, text-based protocol with a 40-year history. By wrapping it in WebSocket, Twitch gets persistent bidirectional connections in browsers without needing a custom protocol. The tradeoff is that IRC wasn't designed for millions of simultaneous users in a single channel, which is where Twitch's infrastructure diverges from vanilla IRC.

The real scaling challenge is fan-out. When a popular streamer has 100,000 concurrent viewers and their chat is active, you might have 10,000 messages per minute arriving and needing to be delivered to those 100,000 connections. A naive architecture where each message is delivered point-to-point doesn't work — that's 10,000 × 100,000 = 1 billion delivery operations per minute for a single channel.

The solution is a hierarchical fan-out architecture:

```
# Chat fan-out: pseudocode for a single message delivery

# Layer 1: Message arrives at chat edge server
def handle_incoming_message(websocket_conn, raw_irc_message):
    channel = parse_channel(raw_irc_message)
    message = parse_and_validate(raw_irc_message)

    # Rate limit check (per-user, per-channel)
    if not rate_limiter.allow(message.user_id, channel):
        send_error(websocket_conn, "NOTICE :Your messages are being sent too quickly")
        return

    # Publish to channel topic in pub/sub backbone
    pubsub.publish(
        topic=f"chat:{channel}",
        payload=message.serialize(),
        ttl_ms=5000  # drop stale messages; viewers tolerate gap
    )

# Layer 2: Edge servers subscribe to channels their connected viewers watch
def on_pubsub_message(topic, payload):
    channel = topic.removeprefix("chat:")

    # Fan out only to local connections subscribed to this channel
    for conn in local_connections.get_by_channel(channel):
        conn.send_irc(payload)

# Layer 3: Local connection registry (in-process, not distributed)
class LocalConnectionRegistry:
    def __init__(self):
        self.by_channel: dict[str, set[Connection]] = defaultdict(set)

    def subscribe(self, conn: Connection, channel: str):
        self.by_channel[channel].add(conn)

    def unsubscribe(self, conn: Connection, channel: str):
        self.by_channel[channel].discard(conn)

    def get_by_channel(self, channel: str) -> set[Connection]:
        return self.by_channel.get(channel, set())
```

Each edge server maintains its own local registry of which WebSocket connections are subscribed to which channels. When a message arrives on the pub/sub backbone, the edge server fans it out only to its local subscribers. This means the pub/sub message is delivered once per edge server, not once per viewer — a multiplicative reduction in backbone traffic.

## PubSub Infrastructure: Routing Events to Millions of Clients

Chat is one consumer of Twitch's pub/sub backbone, but the same infrastructure handles stream-online/offline events, channel point redemptions, subscription notifications, and dozens of other event types. The design requirements are strict: low latency (events should reach clients in under a second), high throughput (millions of events per second across all topics), and at-least-once delivery (missing a "stream went live" notification is a product failure).

Twitch built their pub/sub system on a fanout-first design: topics are the primary routing unit, and every subscriber to a topic receives every message. This is different from a work queue where each message is consumed by exactly one worker. The topology is a tree: a small number of root pub/sub nodes receive all published messages, and a larger layer of edge nodes subscribe to the roots, filtering to only the topics their connected clients care about.

One key design insight: for topics with many subscribers (like popular streamer events), the edge layer is doing most of the work. For topics with few subscribers (like a small streamer's channel points), the overhead of routing is minimal and the system naturally scales. This asymmetry is worth calling out in interviews — good pub/sub architectures are not uniformly expensive across all topics.

## Recommendations: Live vs. Anonymous

Twitch's recommendation system has two very different modes depending on authentication state. For logged-in users, it has a rich history of watch time, follows, and engagement signals — the standard collaborative filtering problem. For anonymous users, it has nothing but the current session and whatever browser fingerprinting is allowed.

The practical architecture uses a two-tier approach. A pre-computed recommendation layer generates candidate stream lists for each logged-in user asynchronously, stored in a low-latency key-value store. At request time, the serving layer retrieves that candidate list and applies real-time filters — is the stream still live? has the user already dismissed it? — before returning results. This decouples expensive ML inference from the request path.

For anonymous users, the fallback is popularity-based ranking with contextual signals: the game being browsed, time of day, and region. This is far simpler and scales trivially because the ranking function has no per-user state. Knowing when to use personalization versus when to fall back to simpler ranking is a judgment call that defines the architecture of most large-scale recommendation systems.

## Interview Implications

Twitch's architecture surfaces three canonical interview themes. First, the difference between push and pull delivery: HLS uses pull (client polls for segments), chat uses push (server fans out to connected clients). The choice between them determines your scaling model. Second, the fan-out problem: how do you deliver one message to a million clients without proportional server-side work? The answer is hierarchical fan-out — pub/sub backbones, edge aggregation, local delivery. Third, stateful connections at scale: WebSocket connections are stateful, which means they tie up a server thread or file descriptor. At Twitch's scale, connection management is an infrastructure discipline unto itself, typically handled with async I/O servers (Go, Erlang, Node) that can hold hundreds of thousands of idle connections per process.

The through-line connecting all of these is the tradeoff between simplicity and scale. HLS is simpler than a custom streaming protocol, and it scales because simplicity enables caching. IRC over WebSocket is simpler than a custom chat protocol, and it scales because the protocol overhead is low enough that the real work can be done in the routing layer. When you explain Twitch in an interview, emphasize how they achieved scale not by solving novel problems, but by composing well-understood primitives under extreme load.
