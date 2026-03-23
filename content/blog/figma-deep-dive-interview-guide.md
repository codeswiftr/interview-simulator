---
title: "Figma Engineering Deep Dive: WebGL Rendering, CRDTs, and Collaboration at Scale"
description: "Complete guide to Figma engineering interviews: WebGL canvas, CRDT-based multiplayer, WebAssembly architecture, LiveGraph, and what their technical interviews actually test."
date: "2026-03-20"
category: "Company Interview Guides"
---

# Figma Engineering Deep Dive: WebGL Rendering, CRDTs, and Collaboration at Scale

Figma is one of the most technically ambitious frontend products ever built. Running a collaborative vector graphics editor in a browser — with real-time multiplayer, complex rendering, and massive document scale — required solving problems that pushed the boundaries of what the web platform could do. Engineering interviews at Figma reflect this: they are among the most technically demanding in the industry.

## Figma's Core Technical Architecture

**WebGL Canvas Rendering**: Figma renders its canvas using WebGL rather than the DOM or Canvas 2D API. This enables GPU-accelerated vector rendering, handling documents with millions of nodes without the performance ceiling of DOM-based layout. The renderer is a custom Bézier curve engine that runs on the GPU.

**WebAssembly (WASM)**: Figma's core rendering engine, originally written in C++, is compiled to WebAssembly. This runs at near-native speed in the browser, enabling complex operations (boolean path operations, vector math, image compositing) that would be prohibitively slow in JavaScript.

**CRDT-Based Multiplayer**: Figma's real-time collaboration uses a custom CRDT implementation. Every document mutation is an operation that can be applied in any order and produce the same result. This enables low-latency optimistic updates and conflict-free merging.

**LiveGraph**: Figma's reactive data layer — a dependency graph that tracks which parts of the document state each component depends on. When state changes, only the affected components re-render. This is conceptually similar to React's virtual DOM reconciliation but purpose-built for Figma's document model.

## WebGL Rendering Deep Dive

Why WebGL over Canvas 2D? Canvas 2D is CPU-bound — path operations, compositing, and clipping run on the main thread. WebGL offloads work to the GPU, enabling hardware-accelerated rendering of thousands of vector objects simultaneously.

Figma's rendering pipeline:
1. Traverse the document tree to determine what's visible in the viewport
2. Tessellate vector paths into triangles (GPU can only render triangles)
3. Upload geometry to GPU buffers (VBOs)
4. Run vertex and fragment shaders to composite layers with correct blending
5. Present the framebuffer to the screen

Interviewers may not expect you to implement a shader, but they want to know that you understand the CPU/GPU boundary, why tessellation is needed, and what the performance bottlenecks are (CPU tessellation, draw call overhead, texture uploads).

## CRDT Implementation

Figma's multiplayer is built on an operation-based CRDT where every change to the document — moving a layer, editing text, changing a color — is represented as an immutable operation.

The key properties:
- **Commutativity**: Operations can be applied in any order and produce the same result
- **Idempotency**: Applying the same operation twice has the same effect as applying it once
- **No coordination required**: Clients don't need to agree on operation order before applying

For tree-structured data (Figma's document is a tree of layers), the hard problem is concurrent moves: what happens if two users simultaneously move the same node to different parents? CRDTs for trees must handle this without creating cycles or duplicating nodes.

Figma's solution uses a "move" CRDT where each move operation records the old parent, new parent, and a logical timestamp. When concurrent moves are detected, one is chosen (typically by timestamp) and the other is undone via a compensating operation.

```
// Conceptual CRDT operation structure
{
  type: 'MOVE_NODE',
  nodeId: 'n123',
  fromParentId: 'frame_a',
  toParentId: 'frame_b', 
  position: 2,
  timestamp: 1711234567890,
  clientId: 'client_xyz'
}
```

## WebAssembly Architecture

Figma compiles their C++ rendering engine to WASM using Emscripten. The WASM module runs in a Web Worker (off the main thread) to avoid blocking UI interactions.

The JavaScript and WASM layers communicate through shared memory (ArrayBuffer/SharedArrayBuffer) and message passing. The document state is serialized in a compact binary format, passed to the WASM module for processing, and results are serialized back.

Interview question: "Why use WASM instead of rewriting in JavaScript?" The answer involves: WASM runs at ~70-80% of native C++ speed vs JavaScript's potentially 10-50% for compute-intensive work; the C++ codebase already existed; and complex geometric algorithms (Bézier intersection, boolean operations) are difficult to optimize in JavaScript due to JIT unpredictability.

## What Figma Tests in Interviews

**Algorithms and Data Structures**: Standard FAANG-level coding — graphs (document trees are trees, after all), dynamic programming, string manipulation. Figma's bar is comparable to Google.

**Graphics and Rendering**: For roles on the rendering or editor team, expect questions about computational geometry (Bézier curves, hit testing, coordinate transforms), rendering pipelines, and GPU programming concepts.

**Distributed State**: CRDT theory, operational transformation, eventual consistency, conflict resolution. Understand the CAP theorem and why Figma chooses availability over consistency.

**TypeScript and System Design**: Figma's codebase is TypeScript-heavy. Expect deep TypeScript (advanced generics, type-level programming, conditional types). System design questions focus on document sync, collaborative editing, and real-time presence.

**Performance**: How to profile and fix rendering jank, memory leaks in long-running browser apps, WebGL draw call optimization.

## Sample Interview Questions

**Q: How does Figma's multiplayer collaboration work at a high level?**
A: Each client maintains a local copy of the document state. Changes are encoded as CRDT operations and applied locally immediately (optimistic). Operations are sent to the server, which broadcasts them to other clients. All clients apply incoming operations to their local state. Because operations are CRDTs, they merge correctly regardless of arrival order.

**Q: Why does Figma use WebGL instead of the DOM for rendering?**
A: The DOM imposes layout and paint overhead that scales poorly with element count. Figma documents can have hundreds of thousands of layers. WebGL renders to a single canvas element with direct GPU access — no layout, no repaint, just geometry and shaders. This enables complex scenes at 60fps where DOM rendering would stall.

**Q: How would you implement a "find all layers containing point X,Y" query efficiently?**
A: Build a spatial index (R-tree or quadtree) over the bounding boxes of all layers, updated incrementally on document changes. For a click at (x, y), query the spatial index for candidate layers, then perform precise hit testing (point-in-polygon for vector shapes, including clipping masks) on candidates only.

**Q: What's the challenge with implementing undo/redo in a CRDT-based system?**
A: CRDTs are append-only — you can't retract operations. Undo must generate a compensating operation that reverses the effect. In a collaborative setting, undoing your operation while another user has built on top of it requires careful design: Figma implements undo as "undo my operations in this session" which generates inverse operations and may produce unexpected results if others have since modified the same elements.

**Q: Explain how a viewport culling system would work for a large Figma document.**
A: Maintain a spatial index (bounding volume hierarchy) of all layers. On pan/zoom, compute the visible viewport rectangle in document coordinates. Query the BVH for layers whose bounding boxes intersect the viewport. Only these layers need geometry sent to the GPU. Additionally, use level-of-detail: render simplified geometry for small or distant objects, full detail only for objects occupying significant screen area.

## Compensation

Figma (post-Adobe acquisition attempt, now independent, 2026): Senior SWE $220K-$290K base + equity. Staff roles $280K-$350K. Specialized roles (graphics, compiler, WASM) command a premium. Figma's equity package is meaningful given their valuation trajectory.

The company is selective — they hire engineers who are genuinely excited about creative tools and the hard technical problems they present. Coming in with genuine curiosity about their rendering architecture, not just memorized answers, is what makes the difference.
