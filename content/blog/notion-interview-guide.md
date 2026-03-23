---
title: "Notion Engineering Interview Guide"
description: "Technical interview preparation for Notion: block-based document architecture, real-time collaboration, database-as-a-spreadsheet systems, and what the all-in-one workspace company looks for in software engineers."
date: "2026-03-19"
category: "Company Interview Guides"
---

Notion is one of the more technically interesting product-engineering companies to interview at. The surface looks like a note-taking app. Under the hood it is a document editor, a relational database, a spreadsheet, a project management tool, and a wiki — all unified by a single data model. If you are targeting a product-engineering role at a B2B SaaS company, this is worth studying carefully.

## What Notion Builds

Everything in Notion is a block. A paragraph is a block. An image is a block. A table row is a block. A database with hundreds of entries is a block. A sub-page is a block that contains other blocks. This uniformity is what makes the product composable — you can embed a database inside a page inside another database — and it is also what makes the engineering hard.

Notion has 30M+ users across consumer and business segments. The product spans:

- A rich-text block editor with formatting, embeds, and slash commands
- A database system that lets you view the same data as a table, board, calendar, gallery, or timeline
- Formulas and rollups that work like spreadsheet functions over relational data
- Real-time collaboration with cursor presence and instant sync
- An offline mode that reconciles changes when you reconnect
- A public API used by thousands of integrations

The engineering org is organized around these product surfaces. You are likely interviewing for one of: Editor/Rendering, Databases, Sync and Collaboration, Infrastructure, or API Platform.

## Technical Interview Areas

### Block Tree Architecture

This is Notion's foundational system design problem. A Notion document is a tree of blocks. A user's workspace might have millions of blocks spread across thousands of pages. How do you build a system that makes this feel fast?

Key concepts to understand:

- **Lazy loading**: you do not load an entire document up front. You load the top-level blocks and fetch children on demand as the user scrolls or expands sections.
- **Virtual scrolling**: for large documents, only the visible blocks are in the DOM. Blocks above and below the viewport are unmounted. This is non-trivial when blocks have variable height.
- **Tree mutations**: when a user types, reorders, or deletes blocks, you are mutating a tree. How do mutations propagate? How do you avoid re-rendering the entire tree on every keystroke?
- **Block IDs and references**: blocks reference their parent and children by ID. A move operation changes parent references, not the block data itself.

Expect questions like: "How would you design the data model for Notion's block system?" and "How do you efficiently render a document with 10,000 blocks?"

### Offline-First and Sync

Notion works offline. If you edit on a plane and reconnect, your changes sync. This sounds simple. It is not.

The core problem is conflict resolution: you made changes offline, the server state changed while you were offline, and now you need to reconcile. Concepts you should know:

- **Optimistic updates**: apply changes locally immediately, send to server asynchronously, roll back if the server rejects.
- **CRDTs (Conflict-free Replicated Data Types)**: data structures that can be merged without conflicts. Text CRDTs (like Yjs or Automerge) allow concurrent edits to the same string to merge correctly. Notion has written publicly about their sync layer; it is worth reading.
- **Operational transforms**: the older approach to collaborative editing, used by Google Docs. Each operation is transformed relative to concurrent operations before applying.
- **Event ordering**: when you have offline edits and server edits, you need a strategy for which wins, or how to merge both.

Expect questions like: "How would you design an offline-first sync system for a document editor?" Focus on the conflict resolution strategy and how you handle the client/server state machine.

### Database Views

Notion databases are blocks that expose multiple views of the same underlying data. A table view, a board view, a calendar view, and a timeline view all render the same rows differently. Formulas let you compute derived fields. Rollups let you aggregate data from related databases.

Interesting design challenges here:

- **View as a render concern, not a data concern**: the underlying data is row/column. Each view is a different projection and sort of that data. How do you design the view layer to be extensible?
- **Formulas over relational data**: Notion formulas look like spreadsheet functions but operate on database properties. How do you evaluate formulas efficiently when dependent properties change?
- **Filters and sorts**: each view can have its own filters and sorts. How do you design a filter DSL that is flexible enough for users but efficient to evaluate?

System design question: "Design a flexible database view system that supports table, board, and calendar views with formulas."

### Real-Time Collaboration

Multiple users editing the same Notion page simultaneously. This requires:

- **Awareness protocol**: knowing where other users' cursors are, which block they are editing, what their selection is. This is separate from the document state — it is ephemeral presence data.
- **CRDT or OT layer**: the underlying mechanism for merging concurrent edits without data loss.
- **Broadcast infrastructure**: changes need to reach all connected clients with low latency. Think WebSockets, pub/sub, and how you fan out updates to N subscribers efficiently.

## System Design Questions to Prepare

- Design Notion's block storage system: how do you store, query, and update a tree of blocks at scale?
- Design real-time collaboration for a document editor: what is your sync protocol, conflict resolution strategy, and presence system?
- Design a flexible database view system: how do you support multiple views with formulas over relational data?
- Design the Notion API: how do you expose block tree operations as a REST/GraphQL API with rate limiting and pagination?

## The Interview Process

Notion runs a practical interview process. Technical screens include coding problems, but they are usually closer to product-relevant problems than abstract algorithmic puzzles. Expect questions about trees, graphs, and string manipulation — but framed around document editing or database systems rather than "reverse a linked list."

More distinctively, Notion interviewers ask product-design questions in engineering interviews. "How would you improve Notion databases?" is a real question they ask engineers. They want to know that you think about the product, not just the code. This is not a trap — they genuinely weight product intuition when hiring engineers.

## Culture

Notion is a mid-size company (several hundred engineers) with a product-obsessed culture. Engineers are expected to have strong opinions about product design and to push back when engineering decisions hurt the product. The bar for product knowledge is real: interviewers notice when candidates have not used Notion seriously.

One practical signal: if you can only describe Notion as "a note-taking app," you are not ready for the interview. Understand the block model, understand databases and their views, know what rollups and relations do.

## How to Prepare

Start by using Notion seriously for 2-4 weeks before your interview. Build a project management system for a real or fake project. Set up a personal wiki. Create a database with relations, rollups, and formulas. Use the calendar and board views. Notice what feels fast, what feels slow, what you would change.

Read Notion's engineering blog. They have published about their block sync architecture and the tradeoffs they made — this is directly relevant to system design questions.

Study CRDTs at a conceptual level. You do not need to implement one, but you should be able to explain why they matter for collaborative editing and what problem they solve better than operational transforms.

Review tree data structures and algorithms. Depth-first traversal, parent/child manipulation, lazy loading strategies. These come up directly in Notion's problem domain.

Finally, have an opinion about the product. What would you build next? What is broken? Engineers who have thought carefully about Notion as a product — not just as a technical system — stand out in interviews there.

The combination of strong systems thinking and genuine product intuition is what Notion is hiring for. Both are learnable. Start with the product.
