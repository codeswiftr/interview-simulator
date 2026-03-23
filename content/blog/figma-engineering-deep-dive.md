# Figma Engineering Deep Dive: Collaborative Design at Scale

When Figma launched in 2016, skeptics called it a toy — a design tool that ran in a browser instead of as a native application. Those skeptics missed something fundamental: Figma was never really a design tool. It was a real-time collaborative document editor that happened to render vector graphics, and it was built on a set of engineering decisions that were, at the time, genuinely radical.

By 2022, Adobe was willing to pay $20 billion to acquire it. When regulators blocked that deal in late 2023, Figma emerged as an independent company with a sky-high valuation, a strengthened engineering culture, and a clear trajectory toward becoming infrastructure for the entire creative software industry. For engineers considering Figma as an employer, understanding the technical depth behind the product is not optional — it is the interview.

---

## The Browser as a Platform: WebAssembly and the C++ Rendering Engine

The single most technically ambitious decision Figma ever made was to build their rendering engine in C++ and compile it to WebAssembly so it could run inside a browser tab.

This was not the obvious choice. Browser-based creative tools at the time used the Canvas 2D API or SVG directly, which meant JavaScript on the hot path for every frame. JavaScript is fine for UI logic, but a design canvas with thousands of nodes, complex blend modes, gradients, and masks cannot be rendered at 60 frames per second in pure JavaScript. The math does not work.

Figma's solution was to write the performance-critical core — the geometry engine, the rasterizer, the layout solver — in C++. They then used Emscripten, a compiler toolchain that targets WebAssembly, to cross-compile that C++ to a `.wasm` binary that browsers can execute at near-native speed.

The architecture looks roughly like this:

```
Browser Host
├── TypeScript / React (UI layer: panels, toolbars, menus)
├── JavaScript bridge (event dispatch, message passing)
└── WebAssembly module (C++ rendering core)
    ├── Scene graph management
    ├── Vector math and bezier evaluation
    ├── Blend mode compositing
    ├── Text layout engine
    └── GPU command generation (WebGL)
```

The C++ core communicates with the TypeScript layer through a narrow message-passing interface. When you move a node on the canvas, a TypeScript event handler captures the pointer delta, serializes it, and posts a message to the WASM module. The module updates its internal scene graph, runs layout, generates a new frame, and signals back that the canvas needs a repaint. The TypeScript layer then schedules a `requestAnimationFrame` call to flush the WebGL draw calls.

This boundary is deliberately thin. The TypeScript layer knows nothing about bezier handles, stroke alignment, or drop shadows. It knows only that messages go in and frames come out. This separation lets Figma evolve the rendering engine independently of the UI, and it means that the C++ engineers can profile and optimize a well-defined surface area without reasoning about React re-renders.

The practical result is a design tool that renders large, complex files faster inside a browser tab than many native applications render equivalent documents. Engineers interviewing at Figma should understand the WebAssembly compilation pipeline, the memory model (WASM has a linear memory heap distinct from the JavaScript heap), and the tradeoffs around serialization cost at the JS/WASM boundary.

---

## The Vector Network: Rejecting SVG's Model

Most vector graphics tools, and the SVG format itself, represent shapes as paths: sequences of moveto, lineto, and curveto commands that trace a single continuous contour. This model works for simple shapes but breaks down when you try to draw anything with branching topology — a fork in a road, a tree branch, an icon with multiple connected endpoints.

Figma invented a different primitive called the Vector Network. Instead of a path (a sequence), a vector network is a graph. Nodes are anchor points with optional bezier control handles. Edges are curve segments connecting pairs of nodes. There is no requirement that the graph be a simple closed loop, and there is no concept of a "start" or "end" anchor.

This has immediate practical consequences for designers — you can draw non-closed shapes with interior fills, you can have T-junctions without duplicating anchor points, and you can edit network topology with operations that have no equivalent in path-based tools. But it also creates significant engineering complexity.

Filling a closed path is straightforward: you run the path through a winding-number algorithm and shade the interior. Filling an arbitrary graph requires first computing the set of enclosed regions, which is a planar graph face enumeration problem. Figma's engine solves this by treating the vector network as a planar subdivision, computing all face boundaries using half-edge data structures, and then running the fill rule over the resulting face set.

Stroke computation is equally involved. A path has a single centerline; stroking it means expanding that centerline outward by the stroke width. A vector network has multiple edges meeting at shared nodes; stroking it requires computing miter or round joins at each node considering all incident edges, not just two adjacent path segments.

This is the kind of computational geometry problem that requires deep algorithmic knowledge to implement correctly and efficiently. It is also the kind of problem that surfaces in Figma engineering interviews, not as trivia, but as a test of whether you can reason about geometric topology under constraint.

---

## Real-Time Multiplayer: CRDTs and the Collaborative Canvas

If the rendering engine is Figma's most impressive individual engineering feat, the multiplayer system is its most consequential architectural decision.

When two users are looking at the same Figma file simultaneously, every action one user takes — moving a layer, changing a color, typing into a text node — must be reflected on the other user's screen within milliseconds, and the two views must converge to the same state even if both users are editing at the same time.

This is the distributed systems problem of conflict-free replicated data types, or CRDTs, applied to a design canvas.

Figma uses an operation-based CRDT model. Every user action is encoded as an immutable operation object rather than a delta to a shared mutable state. Operations have unique IDs (typically a combination of client ID and a logical clock counter), carry their full semantic intent, and are designed so that applying them in any order produces the same result.

A simplified representation of an operation looks like this:

```typescript
type OperationId = {
  clientId: string;
  counter: number;
};

type NodeMoveOperation = {
  type: "MOVE_NODE";
  id: OperationId;
  nodeId: string;
  x: number;
  y: number;
  parentVersion: OperationId; // the state this op was generated against
};

type NodePropertyOperation = {
  type: "SET_PROPERTY";
  id: OperationId;
  nodeId: string;
  property: string;
  value: unknown;
  parentVersion: OperationId;
};

type Operation = NodeMoveOperation | NodePropertyOperation;

class OperationLog {
  private ops: Map<string, Operation> = new Map();

  apply(op: Operation): void {
    const key = `${op.id.clientId}:${op.id.counter}`;
    if (this.ops.has(key)) return; // idempotent
    this.ops.set(key, op);
  }

  converge(remoteOps: Operation[]): Operation[] {
    const newOps: Operation[] = [];
    for (const op of remoteOps) {
      const key = `${op.id.clientId}:${op.id.counter}`;
      if (!this.ops.has(key)) {
        this.apply(op);
        newOps.push(op);
      }
    }
    return newOps;
  }
}
```

The critical property here is commutativity: `apply(op1); apply(op2)` produces the same document state as `apply(op2); apply(op1)`. For independent operations on different nodes this holds trivially. For concurrent operations on the same node property — two users changing the same fill color at the same time — Figma uses a last-write-wins register, where "last" is determined by comparing logical clock values and using client ID as a tiebreaker when clocks are equal.

The Rust layer in Figma's newer infrastructure handles operation serialization, validation, and fanout to connected clients. A session server maintains the authoritative operation log and the current document snapshot. Clients maintain a local optimistic copy, applying their own operations immediately for responsiveness, then reconciling when they receive the server's acknowledgment or other clients' operations.

```rust
use std::collections::HashMap;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct ClientId(pub String);

#[derive(Clone, Debug)]
pub struct LogicalClock {
    counters: HashMap<ClientId, u64>,
}

impl LogicalClock {
    pub fn new() -> Self {
        Self {
            counters: HashMap::new(),
        }
    }

    pub fn tick(&mut self, client: &ClientId) -> u64 {
        let counter = self.counters.entry(client.clone()).or_insert(0);
        *counter += 1;
        *counter
    }

    pub fn observe(&mut self, client: &ClientId, seen: u64) {
        let entry = self.counters.entry(client.clone()).or_insert(0);
        if seen > *entry {
            *entry = seen;
        }
    }

    pub fn happened_before(&self, a: &(ClientId, u64), b: &(ClientId, u64)) -> bool {
        let a_counter = self.counters.get(&a.0).copied().unwrap_or(0);
        let b_counter = self.counters.get(&b.0).copied().unwrap_or(0);
        a.1 <= a_counter && b.1 <= b_counter
    }
}

pub struct LWWRegister<T: Clone> {
    value: T,
    timestamp: (ClientId, u64),
}

impl<T: Clone> LWWRegister<T> {
    pub fn new(initial: T, client: ClientId) -> Self {
        Self {
            value: initial,
            timestamp: (client, 0),
        }
    }

    pub fn write(&mut self, new_value: T, client: ClientId, counter: u64) {
        let incoming_wins = counter > self.timestamp.1
            || (counter == self.timestamp.1 && client.0 > self.timestamp.0.0);
        if incoming_wins {
            self.value = new_value;
            self.timestamp = (client, counter);
        }
    }

    pub fn read(&self) -> &T {
        &self.value
    }
}
```

This model scales to hundreds of simultaneous editors on a single file — something that was genuinely new in 2016 and remains technically non-trivial today. Figma's system design interviewers expect candidates to be able to design this from scratch, including the choice between operational transformation and CRDTs, the handling of undo/redo in a multiplayer context, and the session server's role in ensuring causal consistency.

---

## System Design Interview: Collaborative Canvas

A common Figma system design question is essentially "design Figma." Here is a compressed but realistic treatment.

**Core requirements:** Multiple users edit the same canvas concurrently. Each user's local view is always responsive (no blocking on network). All views converge to the same state. History and undo work correctly.

**Data model:** A document is a tree of nodes. Each node has an ID, a type, a set of properties (position, size, fill, stroke, etc.), and a parent reference. Operations are the unit of replication.

**Client architecture:** The client maintains a local operation log and a current document snapshot derived from it. When the user performs an action, the client immediately applies the operation to the local snapshot (optimistic update), assigns the operation an ID from the client's logical clock, and sends it to the session server over a WebSocket connection.

**Session server:** The server maintains the authoritative operation log. When it receives an operation from a client, it validates it, appends it to the log with a server-assigned sequence number, updates the current snapshot, and fans it out to all connected clients. The sequence number provides a total order over all operations, which is used to resolve concurrent writes to the same register via LWW.

**Conflict resolution:** For concurrent operations on different node properties, they commute — apply both, last write wins on each property independently. For concurrent tree restructuring (two users moving the same node to different parents), Figma uses a tree-aware CRDT that prevents cycles and resolves parent conflicts deterministically.

**Undo/redo:** Because operations from multiple users are interleaved in the log, per-user undo must selectively reverse only that user's operations without disrupting others. This requires generating inverse operations and handling the case where the original operation's effects have been partially overwritten by others.

**Scaling:** A single session server handles one document. Horizontal scaling at the document level (sharding by document ID) is straightforward. Within a single busy document, the session server is the bottleneck; Figma mitigates this with efficient binary serialization (Protocol Buffers) and careful WebSocket framing.

---

## The Adobe Acquisition and What It Revealed

In September 2022, Adobe announced it would acquire Figma for approximately $20 billion in cash and stock — at the time, one of the largest software acquisitions in history. In December 2023, the deal collapsed after the UK Competition and Markets Authority determined it would harm competition in product design software.

The failed acquisition was instructive in several ways. It confirmed that Figma's valuation was not merely speculative — a company the size of Adobe, with every incentive to underestimate the threat, concluded that paying $20 billion was preferable to competing. It also surfaced something about Figma's engineering culture: the company had been built to stand alone, not to be absorbed.

Figma's engineering team responded to the acquisition failure with what observers described as renewed focus. The team had been in a kind of holding pattern during the regulatory review, with major platform investments deferred pending the acquisition's outcome. Once the deal collapsed, Figma accelerated investment in infrastructure, particularly in their Rust-based backend systems and in AI-assisted design tooling.

For engineers evaluating Figma as an employer, the post-acquisition period is probably the most important context. The company re-established itself as a well-funded independent with a clear product vision, a strengthened leadership team, and more equity value accruing to employees rather than Adobe shareholders. The engineering organization is roughly 400 to 600 engineers — small enough that individual contributors have significant impact, large enough to tackle genuinely hard problems.

---

## Technical Stack and Engineering Organization

Figma's stack is layered by domain rather than by layer, and each layer has its own primary language:

The rendering engine is C++. This code is compiled to WebAssembly for the browser client and to native binaries for server-side rendering (used for thumbnails and exports). C++ was chosen because the required operations — floating-point geometry, pixel compositing, font rendering — are latency-sensitive enough that the overhead of a managed runtime is unacceptable.

The browser application shell is TypeScript and React. This layer handles everything the user interacts with that is not the canvas itself: the layers panel, the properties panel, the component library browser, the comment thread UI. React's component model fits this well, and TypeScript's type system catches the class of runtime errors that are expensive in a collaborative editing context.

The server-side infrastructure is increasingly Rust. Figma's session servers, operation log persistence, and cross-document reference resolution are being rewritten from earlier TypeScript and Go implementations into Rust for performance and memory safety. The Rust ecosystem's async runtime (Tokio) and WebSocket libraries (tokio-tungstenite) are well-suited to the high-concurrency, low-latency session server use case.

The backend APIs and data pipeline are Python. Django and FastAPI handle product APIs, user management, file metadata, and billing. Python was a pragmatic early choice that persists for its ecosystem advantages in data work.

---

## The Interview Process

Figma's engineering interview process is designed to surface both frontend depth and systems reasoning. The bar is genuinely high, and the interviews are structured to distinguish candidates who can talk about WebAssembly from candidates who have actually worked with it.

A typical loop for a mid-to-senior software engineer includes two to three coding rounds (algorithm and data structure problems, LeetCode-hard difficulty on occasion, but with an emphasis on graph problems and geometry), one to two system design rounds (the collaborative canvas design question is common, as are questions about rendering pipelines and real-time data sync), and one to two behavioral interviews focused on craft, design sensibility, and cross-functional collaboration.

The system design interviews expect depth on CRDTs versus operational transformation, on WebSocket vs. long-polling tradeoffs, and on the specific challenges of undo in a multiplayer context. Candidates who have only memorized the CAP theorem will struggle; candidates who can derive the CRDT convergence proof from first principles will do well.

Figma also places unusual weight on design empathy in engineering interviews. This does not mean candidates need Figma proficiency, but it does mean they are expected to think about API design from the perspective of a designer using a plugin, or reason about rendering performance from the perspective of a user on a low-end laptop in a slow network environment.

---

## Compensation and Career Trajectory

Figma's total compensation is competitive with other Bay Area product companies of its tier. At the senior engineer level, total compensation (base plus equity) is generally in the $350,000 to $500,000 range depending on level and negotiation, with the equity component now carrying meaningful upside given the company's independent trajectory.

The equity story at Figma is more interesting than at many companies because the failed acquisition reset expectations. Engineers who joined during the Adobe negotiation period took a bet on an uncertain outcome; engineers joining now are betting on a company that has proven it can stand alone and is investing aggressively in new product surface area including AI features, developer tooling, and the FigJam collaborative workspace product.

Career trajectory at Figma is accelerated by the company's size. A staff engineer at a 500-person company has substantially more organizational surface area than a staff engineer at a 50,000-person company. Figma's engineering teams are small enough that senior individual contributors regularly shape product direction, not just implementation.

---

## What Makes Figma Engineering Distinctive

Three things distinguish Figma's engineering culture from comparable product companies.

First, craft obsession is genuine and structural. The company was founded by designers who cared deeply about the feel of interactions — the spring curves on panel open animations, the precision of the snap behavior on the canvas, the latency of real-time cursor rendering. This sensibility propagates into the engineering culture in concrete ways: performance work is celebrated, visual quality is treated as a correctness criterion, and the phrase "good enough" is treated with skepticism.

Second, the technical problems are real. WebAssembly rendering, CRDT-based multiplayer, and computational geometry are not marketing narratives — they are the actual daily work. Engineers who want to push the state of the art in browser-based application performance have few better places to do it.

Third, the company is at an interesting inflection point. Post-acquisition-failure, Figma is investing in platform capabilities that position it as infrastructure rather than an end-user application. The plugin and widget ecosystems, the REST API, the Figma Variables system for design tokens, and the emerging AI features all point toward a company that wants to be the design data layer for the software industry. Engineers joining now are present for that transition.

For candidates preparing to interview at Figma, the preparation agenda is clear: understand WebAssembly deeply, be able to design a CRDT-based collaborative document system from scratch, know the computational geometry behind vector operations, and demonstrate genuine interest in the intersection of software engineering and design craft. The interview is testing for engineers who would have been excited to build Figma's architecture in 2016. The question is whether you are that engineer.
