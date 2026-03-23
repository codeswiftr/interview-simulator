# Figma Engineering Deep Dive: Real-Time Collaborative Design at Scale

Figma is one of the most technically ambitious products ever shipped in a web browser. What looks like a design tool on the surface is actually a custom real-time 3D renderer written in C++, a distributed collaborative editing engine, a novel mathematical model for vector graphics, and a cloud-scale document storage system — all running inside a browser tab. If you're interviewing at Figma, the depth of their engineering problems is genuinely uncommon, and understanding the technical architecture is not optional preparation. It's table stakes.

## The Multiplayer Engine: CRDTs and Collaborative Editing at Scale

Figma's multiplayer system is one of the most sophisticated real-time collaboration engines in production software. The core challenge is deceptively simple to state: when 100 users are simultaneously editing the same design file, every edit must be applied correctly on every client, with no data loss, no corruption, and perceived latency under 100ms.

Early systems for collaborative editing used Operational Transformation (OT), the same approach Google Docs pioneered. OT works by transforming operations against each other: if Alice moves a shape right while Bob is simultaneously moving it up, the system transforms Alice's operation to account for Bob's and vice versa. The math works for text editing but becomes combinatorially complex for rich document structures with arbitrary nesting, properties, and object graphs.

Figma ultimately moved toward a hybrid model with CRDT (Conflict-free Replicated Data Type) principles for parts of their document tree. CRDTs are data structures that can be merged automatically without conflict — the mathematical structure guarantees that any two replicas, merged in any order, converge to the same result. For Figma's use case, this means clients can apply edits optimistically to local state and sync with the server asynchronously, with guaranteed eventual consistency. The server acts as both a persistence layer and a tie-breaker for true conflicts.

What makes Figma's implementation notable is scale: they handle files with hundreds of thousands of nodes, edited by dozens of simultaneous users, with a sync protocol that batches and compresses operation streams to minimize bandwidth. The WebSocket connection between client and server carries a binary protocol, not JSON, specifically to reduce serialization overhead at high operation rates.

## The WebAssembly Renderer: Bringing C++ to the Browser

Figma's rendering engine is the technical story that put them on the map in engineering circles. When they built the product, the browser's Canvas 2D API was too slow for complex design files — rendering thousands of shapes with Bezier curves, gradients, drop shadows, and masks on every frame was not feasible at 60fps through JavaScript. WebGL offered GPU access but required writing raw shader programs, which is a prohibitive level of complexity for building a design tool renderer on top of.

The solution Figma chose was to write their renderer in C++ and compile it to WebAssembly. This was 2015, before WebAssembly was even a formal standard — they were using asm.js, a precursor, and later migrated to full WebAssembly. The renderer implements a scene graph, a tile-based rasterization system, a font rendering pipeline using FreeType compiled to WASM, and a GPU-accelerated compositing pass via WebGL. All of this runs inside a WASM module loaded alongside the JavaScript application.

The practical result is that Figma can render designs at 60fps that would be impossible with any pure-JavaScript approach. The C++ code can use SIMD intrinsics (via WebAssembly SIMD), cache-conscious memory layouts, and tight inner loops that the WASM runtime JITs to near-native performance. The architecture also means that the rendering logic is shared between the browser client and their server-side thumbnail generation, ensuring pixel-perfect consistency between what the user sees and what gets exported.

## Vector Networks: Reinventing the Pen Tool

Most vector graphics programs use Bezier paths — sequences of cubic curves connected at endpoints, forming closed or open contours. This model traces back to PostScript and has been the foundation of Adobe Illustrator, Sketch, and every other design tool for decades. It has a fundamental limitation: topology. Paths are linear chains; you cannot create a path that branches or that has a node where three curves meet.

Figma invented Vector Networks as an alternative mathematical model. In a Vector Network, the representation is an undirected graph where nodes are anchor points and edges are Bezier curve segments. There is no concept of a "start" or "end" to a path — any node can connect to any number of edges. This means you can draw Y-shapes, asterisks, and complex topologies that are literally impossible to represent in the traditional path model.

From an implementation standpoint, Vector Networks required Figma to build entirely new algorithms for hit testing, region detection (determining which enclosed areas should be filled), and path export. When you need to export a Vector Network as SVG, you have to decompose the graph back into a set of SVG path elements, which may require solving a combinatorial region problem to determine the correct winding rules. The math here draws on computational geometry — planar graph traversal, face detection in embedded graphs, and proper Bezier intersection algorithms. It's not standard software engineering fare, and it signals the depth of the graphics engineering investment Figma has made.

## Infrastructure for Design Files at Scale

Design files in Figma can grow to hundreds of megabytes of document data — not binary assets, but structured document trees representing potentially millions of design nodes. How Figma stores, versions, and syncs this data is a significant distributed systems problem.

Figma's backend separates concerns cleanly. Document metadata — file names, permissions, project membership, sharing settings — lives in CockroachDB, their distributed SQL database. The actual document content, the serialized node tree, lives in a custom storage layer optimized for the append-heavy, snapshot-heavy access pattern of collaborative documents. Every saved state is essentially a snapshot plus a delta log of operations since the last full snapshot.

The sync protocol is designed around the asymmetry between reads and writes. Loading a file is a read-heavy operation: the server sends the client a full document snapshot at the last saved checkpoint, and then replays any uncommitted operation log on top. Writing is an append-heavy operation: clients send operation batches that the server applies to the in-memory state and appends to the log. Periodically, the server collapses the log into a new snapshot to bound the replay time for future loads.

Version history — Figma's ability to show you every saved state of a file going back months — is built on this snapshot/delta architecture. Each named version is a pointer to a snapshot in storage. The storage costs are bounded by deduplication at the node level: if 95% of a file's nodes haven't changed between versions, only the 5% delta is stored.

## Interview Implications: What Figma Actually Looks For

Figma is deeply technical in a way that few product companies are. Their graphics engineering and infrastructure teams regularly hire PhD-level engineers with backgrounds in computer graphics, programming languages, and distributed systems. But even their product engineering roles expect a level of systems thinking that goes beyond typical software engineering interviews.

For system design questions, be prepared for problems like: design a real-time collaborative editing system for a structured document; design a renderer that achieves 60fps for complex vector graphics in a browser; or design a file versioning system that supports arbitrarily long version history without unbounded storage growth. The answers should reflect understanding of consistency models (eventual consistency vs. strong consistency and when each is appropriate), memory management and bandwidth optimization, and the tradeoffs between client-side and server-side computation.

On fundamentals, Figma values engineers who understand WebAssembly and browser performance constraints, the basics of graphics rendering (rasterization, compositing, the GPU pipeline), and distributed consistency. You don't need to have built a CRDT from scratch, but you should be able to explain the problem CRDTs solve and why OT becomes difficult at scale.

Above all, Figma looks for engineers who are genuinely curious about the hard problems at the intersection of graphics, distributed systems, and product. The company was built on the conviction that the web could do things everyone said were impossible — and their engineering culture still reflects that conviction.
