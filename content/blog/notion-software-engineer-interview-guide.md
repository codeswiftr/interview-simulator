# Notion Software Engineer Interview Guide 2024: Joining the Productivity Platform

Notion is one of the most deceptive products in the history of B2B software. On the surface it is a notes app. Underneath it is a real-time collaborative editor, a relational database engine, a flexible schema system, an offline sync engine, an API platform, and — as of 2023 — a deeply integrated AI product, all built on a single recursive block data model by an engineering team that, even after rapid growth, numbers in the hundreds. At its 2021 Series C, Notion was valued at $10 billion with fewer than 500 employees. The ratio of product quality to headcount is extraordinary by any measure.

That ratio is not an accident. It is a hiring philosophy. Notion is one of the most selective engineering employers in consumer software, and its interview process reflects a specific belief: the right engineers, given the right tools and environment, can build software that millions of people genuinely love. The interview process is designed to find those engineers — which means it tests for things that most standard interview prep does not address.

## The Notion Engineering Environment

Notion's engineering culture has a handful of distinguishing characteristics that directly affect what the interview evaluates.

**Craft as a non-negotiable.** Notion's editor is one of the most polished pieces of software in the productivity space. The way blocks reorder, the way slash commands appear, the way drag handles behave, the way the inline database renders — every interaction was built and iterated on to feel right. This level of craft is expensive to build and requires engineers who notice when something feels wrong even when it technically passes its tests. Interviewers are trying to identify that instinct.

**Small team, visible impact.** Every engineer's work is visible to tens of millions of users. There is no place to hide behind a large organization or a single microservice that nobody uses. Notion's team structure means engineers own significant surface area and are expected to make product decisions, not just implement tickets from a PM.

**Deliberate, slow hiring.** Notion moves slowly in its hiring process by design. The take-home assignment and subsequent technical review are a meaningful time investment — typically 6–12 hours of work plus a 60-minute review session. This filters out candidates who want a fast offer more than they want to work at Notion.

**Design as a first-class partner.** Design is not downstream of engineering at Notion. Design and engineering collaborate from problem definition. Engineers are expected to have product opinions and interact with design as peers, not as implementers of a specification. The values round often explores whether candidates bring that orientation.

**AI as genuine product architecture.** Notion AI, launched in 2023 and now deeply integrated into the product, is not a sidebar chatbot. It can draft content in the context of a page, fill database properties based on the row's content, summarize linked pages, and write formulas. The integration is architectural: AI outputs are blocks, AI operations compose with the same editing primitives as user actions. Engineers hired today are expected to engage seriously with how AI extends the block model.

The Notion engineering blog has excellent posts on the block model, database architecture, and performance work at scale. The CEO Ivan Zhao's public interviews and Notion's product philosophy documents are also worth reading — they reveal a consistent philosophy about "building blocks vs. features" that engineers at Notion are expected to internalize.

## Interview Format

Notion's process differs from most tech companies in one important way: the take-home assignment replaces the standard phone screen coding round.

1. **Recruiter screen** (30 minutes) — Background, role fit, timeline, and a genuine check on whether you have used and formed opinions about Notion as a product.

2. **Take-home coding project** (3–5 days to complete, 6–12 hours of work) — Not a LeetCode problem. Typically a mini-feature or system component that resembles real Notion engineering work: a simplified block editor, a collaborative state synchronization module, a database query engine stub, or a real-time presence system. You choose your language. The output is a working implementation with tests and a written explanation of your design decisions.

3. **Take-home review** (60 minutes) — A live session where you walk through your implementation, explain your decisions, field alternative approaches, and discuss how you would extend it. This is where interviewers probe deeply. The question "what would you change if you had another week?" is common. So is "show me the hardest part to get right and why."

4. **Onsite** (3–4 rounds):
   - Coding round — algorithms, data structures, or an implementation problem
   - System design round — collaborative document infrastructure, database layer, or sync system
   - Values round — craft orientation, product thinking, collaboration, how you handle ambiguity

5. **Offer or debrief** — Timeline is 4–8 weeks total. Notion has declined technically strong candidates on the values round. Take it seriously.

For senior and staff roles, the system design round is heavier and may include a discussion of architectural trade-offs across Notion's entire data model.

## Technical Deep Dives: What Notion Actually Tests

### The Block Data Model

Notion's entire product is built on a single recursive data structure: the block. Every element in Notion — a paragraph, a heading, a to-do item, an image, a database, an embedded page, a column layout, a toggle — is a block with a type, a set of properties, an ordered list of children, and a reference to its parent.

```typescript
interface Block {
  id: string;                      // UUID, globally unique
  type: BlockType;                 // "paragraph" | "heading_1" | "database" | "page" | ...
  properties: Record<string, PropertyValue>;
  content: string[];               // Ordered list of child block IDs
  parent_id: string;               // Parent block ID or page ID
  parent_table: "block" | "workspace" | "collection";
  created_time: number;
  last_edited_time: number;
  alive: boolean;                  // Soft delete flag
}
```

The block tree is a general-purpose hierarchical document model. A page is a block whose children are content blocks. A database is a block of type `collection` whose children are row blocks. A heading is a block whose children are inline annotation spans. The same structural primitives compose into everything Notion does.

Rich text within a block is stored as an array of annotated text runs, not as raw HTML. This is a critical design choice:

```typescript
type RichText = [string, Annotation[]?][];
// Example: "Hello **world**" →
// [["Hello "], ["world", [["b"]]]]
```

Storing annotations as structured data rather than HTML makes it straightforward to serialize to any target format (Markdown, plain text, HTML, PDF) without parsing, and provides a stable intermediate representation for operational transformation. You should understand why raw HTML as storage is a design anti-pattern for a collaborative editor.

For interviews, be prepared to discuss: how would you design this data model to support efficient rendering of a 10,000-block page? How would you handle the case where a user pastes 500 blocks from a Google Doc? What are the consistency guarantees you need between the block tree and the property values stored on each block?

### Real-Time Collaborative Editing and Operational Transformation

This is the most technically demanding area Notion tests engineers on. Collaborative editing is a hard distributed systems problem, and Notion's approach involves specific trade-offs that interviewers will probe.

**The fundamental problem.** Two users edit the same document simultaneously. User A (on a laptop) types "beautiful" before "world". User B (on a phone) deletes "world" at the same moment. Neither user can wait for the other's operation to arrive before editing — that would make the editor feel unresponsive. When the operations arrive at the server, how do you produce a result that both users see, that reflects both operations faithfully, and that is consistent?

**Operational Transformation.** Notion uses OT with the server as the single authoritative arbiter. OT works by defining a `transform` function: given two concurrent operations O1 and O2 that were both based on the same document state, `transform(O1, O2)` produces O1' — a version of O1 that, when applied after O2, produces the same result as applying O2 after O1 would have. The key property is convergence: regardless of the order operations are processed, all clients reach the same state.

For text insertions:

```
State: "hello world"

User A (offset 5): Insert " beautiful"
User B (offset 6): Delete 5 chars ("world")

If B arrives at server first:
  Apply B → "hello "
  Transform A against B: A inserted at offset 5 which is before B's range
  Transformed A is unchanged: Insert " beautiful" at offset 5
  Apply transformed A → "hello  beautiful"  (note: "world" was deleted before A's insert)

If A arrives at server first:
  Apply A → "hello  beautiful world"
  Transform B against A: B deleted at offset 6 originally,
    but A inserted 10 chars at offset 5, so B's offset shifts to 16
  Apply transformed B (delete 5 chars starting at offset 16) → "hello  beautiful "

Both orderings converge on "hello  beautiful " — this is correct OT behavior.
```

The implementation complexity increases substantially for rich text with overlapping annotations, for block-level operations (deleting a block while another user adds a child to it), and for operations on database properties. Interviewers will probe whether you understand that OT is not trivial to implement correctly at the full complexity of Notion's block model.

**The server-as-arbiter model and its implications.** The server assigns a total order to all operations. Clients submit operations tagged with the server revision they were based on. If the server is ahead, the operation is transformed against the intervening history before being applied. This gives you strong consistency but has a cost: clients cannot apply operations optimistically to their local state without a server round-trip if they need a guarantee of correctness. In practice, Notion does apply changes optimistically for user experience and reconciles on the server response — but the conflict resolution on reconciliation can sometimes cause jarring resets if the user's local state diverged significantly.

**CRDT vs. OT trade-off discussion.** Interviewers may ask why Notion uses OT rather than CRDTs (Conflict-free Replicated Data Types). CRDTs allow true peer-to-peer collaboration without a server — operations can be applied in any order and still converge. The cost is that CRDT implementations for rich text are more complex (Yjs and Automerge are production CRDTs for text, but they have higher memory overhead per character and more complex data structures than OT). For Notion's use case — where there is always a server, and the server provides a convenient ordering oracle — OT is a reasonable choice that keeps the client-side model simpler. Know both approaches and be ready to articulate the trade-offs.

### Large Document Performance: 10,000-Block Pages

Notion's performance with large documents is a known engineering challenge and a topic that appears in interviews and in Notion's own engineering discussions.

The naive approach to rendering a Notion page: fetch all blocks, build the full React tree, render. For a 50-block page this is instant. For a 10,000-block page, this approach fails in multiple ways:

- **Initial load**: Fetching 10,000 blocks from the API is slow. Even with batching, you are waiting for multiple round trips before rendering anything.
- **React reconciliation**: A 10,000-element React tree is expensive to reconcile on every state change. A single keystroke triggering a re-render of 10,000 components is perceptible.
- **DOM node count**: 10,000 DOM nodes with attached event listeners consume significant memory on mobile devices.

The solution is virtualization combined with incremental loading:

**Block virtualization.** Only render blocks that are in or near the user's viewport. Blocks that scroll out of view are unmounted from the DOM (or replaced with a fixed-height placeholder). As the user scrolls, blocks are mounted and unmounted. The block tree structure makes this slightly harder than virtualized flat lists (react-window pattern) because blocks have variable height and nested children — a collapsed toggle does not render its children at all, while an expanded database table may render hundreds of rows inline.

**Incremental loading.** Fetch only the top-level blocks initially. Load children on demand — when a toggle is expanded, fetch its children. When the user scrolls to the bottom of the page, prefetch the next batch of blocks. This keeps initial page load fast regardless of document size.

**Optimistic updates.** When a user types, update the local block model immediately without waiting for server confirmation. This makes typing feel instantaneous. The server confirmation arrives within 100–500ms; if there is a conflict (rare), the client reconciles.

**Offline support.** Notion's desktop and mobile apps support editing while offline. Changes buffer locally in IndexedDB (web) or SQLite (mobile). On reconnect, the buffered operations are submitted to the server and the document is reconciled. For long offline periods with many changes, the reconciliation can be complex — particularly if another user made conflicting changes to the same blocks. Notion's practical approach is to handle the common case (short offline periods, non-overlapping edits) gracefully and surface a conflict state for the edge case.

### Notion's Database-as-Document Duality

One of Notion's most technically interesting design challenges is that a database is also a block. The same document tree that contains paragraphs and headings can contain an inline database with its own schema, views, filters, and sorts. This duality creates interesting engineering problems.

**The collection data model.** A Notion database is a `collection` block. Its rows are `page` blocks that are children of the collection. The collection block stores the schema: a mapping from property ID to property definition (type, name, options for select properties, expression for formulas, etc.). Each row page stores its property values in its block's properties.

**Property types and their storage.** Notion's property types include text, number, select, multi-select, date, person, relation, rollup, formula, created time, and last edited time. Most are stored as structured values in the row block's properties. Relation properties store references to other block IDs. Rollup properties are computed at query time by evaluating an aggregation function over a related collection. Formula properties store an expression string and are evaluated at read time.

**Query efficiency at 100,000+ rows.** For most Notion databases the row count is in the hundreds or low thousands, and a naive full-scan filter works fine. For databases with 100K+ rows (a CRM, a content backlog, an inventory system), filter performance matters. Notion indexes select and multi-select values, dates, and person references for efficient filtering. Full-text search within text properties requires a separate search index (Notion uses a dedicated search service rather than indexing text in the main data store). Formula columns and rollup columns cannot be efficiently indexed because their values are computed — sorting or filtering by a formula requires materializing the result for every row, which is expensive at scale. This is a known limitation and a reasonable topic for a system design discussion about how you would redesign it.

**Views as presentation layers.** The same collection data can be viewed as a Table, Board (Kanban), Calendar, Gallery, Timeline, or List. Views store their configuration (active filters, sort orders, visible properties, group-by property) in a separate view block that references the collection. Switching views is a client-side operation: the same fetched rows are re-rendered according to the new view configuration. This means views are cheap to add (no new server infrastructure per view type) but require the client to handle arbitrary combinations of filters, sorts, and groupings efficiently.

## System Design at Notion

Notion system design rounds test deep understanding of the collaborative document domain. Generic distributed systems answers are a weak signal — interviewers want to see that you have internalized the specific constraints of Notion's architecture.

**Worked example: Design Notion's real-time collaboration for a document with 50 simultaneous editors**

*Requirements*: Real-time visibility of other users' edits. Presence indicators (see who is in the document and where their cursor is). Character-level conflict handling. Offline sync. Reconnection handling.

**Separation of concerns: ephemeral vs. durable state.**

Presence (who is viewing the document) and cursor positions are ephemeral — they do not need to persist across page reloads or survive server restarts. They change at cursor-move frequency (many times per second) and become stale quickly. Handle them on a separate channel from document operations.

Document operations are durable — every edit must be persisted and replayed to new clients joining the session.

**Presence and cursor channel.**

```
Client → WebSocket server → broadcast to all clients in same document session
```

Each client broadcasts its presence state (user ID, cursor position as block ID + character offset, selection range) at a rate-limited frequency (roughly 30 updates per second during active editing). The WebSocket server is a pure relay — it does not store presence state beyond in-memory session state. When a client disconnects, the server broadcasts a presence-removed event for that user's cursor.

**Document operation pipeline.**

```
User types character
    → Local optimistic apply: update React state immediately (sub-1ms)
    → Append to pending operations buffer
    → Send to server over WebSocket with base_revision number

Server receives operation
    → Acquire per-document write lock (target: held <5ms)
    → If client's base_revision < server's current revision:
          Transform operation against intervening operations (OT)
    → Apply transformed operation to document state
    → Increment document revision
    → Persist operation to database (append-only operations log)
    → Broadcast transformed operation to all other clients in session
    → Send acknowledgment to originating client with server revision
    → Release lock

Other clients receive broadcast
    → Transform against local pending operations (client-side OT)
    → Apply to local state and re-render affected blocks
```

**Offline sync design.**

The client buffers operations locally in IndexedDB (web) or SQLite (native apps). On reconnect:

1. Client sends its last known server revision and its buffered operation list.
2. Server fetches all operations since that revision.
3. Server transforms the client's buffered operations against the server's operations (the standard OT merge).
4. If the client's buffer exceeds a threshold (e.g., more than 500 operations accumulated during a long offline period), the server may return a "full reload required" response rather than attempting a complex multi-operation transform. The client discards its local buffer and reloads the current document state from the server.

**Scale for 50 simultaneous editors.** The per-document lock is the serialization point. At 50 editors typing simultaneously, you might have 50 operations per second competing for the lock. Lock hold time must be short — the transform-and-apply operation needs to complete in under 5ms to keep the queue from backing up. For the presence channel, fan-out to 50 WebSocket connections is trivial. For operations, the broadcast to 49 other connections plus the DB write must complete within the lock hold or be pipelined carefully.

## Behavioral at Notion

The values round at Notion is not a formality. Strong technical candidates have been declined because the values round revealed a mismatch. The themes Notion probes:

**"Tell me about a time you obsessed over a product quality detail that most engineers would have let slide."**

Notion interviewers are looking for intrinsic craft motivation — the instinct to notice when something feels wrong and fix it even when it was not required. Strong answers describe a specific, concrete detail: a 16ms frame drop during a drag animation, a confusing error message in an edge case, a keyboard shortcut that did not behave as users would expect. Weak answers describe doing a code review or writing comprehensive tests (those are expected, not exceptional).

**"Tell me about something you built that users genuinely loved, not just used."**

This is about the gap between functional and beloved. "Loved" means users told other people about it, or complained when it was removed, or posted on Twitter about how it changed their workflow. If you have shipped something with that kind of response, tell the full story: what made it resonate, what feedback signals confirmed it, what you would do differently.

**"Describe a time you found a simpler model for a complex problem."**

Notion's block model is itself an example of radical simplification — one recursive data structure that handles every content type. Interviewers at Notion deeply value this kind of thinking. Strong answers describe discovering that two apparently separate concepts were the same thing at a deeper level, or that a complex conditional system could be replaced with a single general primitive.

**"Tell me about a time you worked closely with design and how you shaped the outcome together."**

Notion's design-engineering partnership is real and unusual. Engineers who have only ever worked as spec-implementers will struggle here. The interviewer wants to hear how you brought technical perspective to a design problem, pushed back on a design that was technically expensive for no user benefit, or proposed a design variant that unlocked a better engineering solution.

## Preparation Timeline

### Week 1: Block-Based Editor Architecture

Read the ProseMirror guide in full at `prosemirror.net/docs/guide`. It is the clearest available explanation of how production collaborative editors are architected. ProseMirror's concepts — schema, document model, transactions, plugins, the view layer — map closely to how Notion thinks about its editor, and Notion engineers have referenced it publicly. Do not skim: understand the document model, the transform system, and why the view is kept separate from the state.

Read the Slate.js architecture documentation and explore its source. Slate uses a simpler model than ProseMirror and is closer in spirit to Notion's block model. Build a minimal block-based editor: a React component that maintains a block model as state and renders each block type differently. Implement bold/italic formatting as annotations. This is the best use of your preparation time in week one.

### Week 2: Operational Transformation and Collaborative Editing

Read the ShareDB documentation at `github.com/share/sharedb`. ShareDB is a production OT implementation widely used in collaborative tools. Understanding its API — particularly how operations are structured and how the transform function is defined — gives you a concrete vocabulary.

For theory: read the Wikipedia article on Operational Transformation and trace through the examples by hand. Implement a simple OT system for plain text yourself: define `Insert(position, chars)` and `Delete(position, length)` operations, write the `transform(op1, op2)` function that handles all four combinations (insert/insert, insert/delete, delete/insert, delete/delete), and write tests for concurrent operations. This is the most valuable thing you can do for Notion interview preparation.

Read at least one paper on the CRDTs-vs-OT trade-off: Martin Kleppmann's "A Conflict-Free Replicated JSON Datatype" gives a clear comparison. Know how Yjs works at a high level — it is used in production collaborative tools and Notion interviewers may reference it.

### Week 3: Database Design, Query Efficiency, and Notion's Product Depth

Design Notion's database and property type system from scratch. Work through: how do you store formula expressions and evaluate them at query time? How do you efficiently filter 100K rows by a select property? How do you handle relation properties that reference rows in another collection that may have been deleted?

Study how competitors solve the same problem — Airtable's engineering blog, Coda's architecture posts. Note where their approaches differ from Notion's and understand why.

Use Notion intensively this week. Build a complex workspace: a project tracker with a linked task database, a content calendar with a relation to a team database, a personal CRM with rollup properties counting linked meetings. Use formula properties. Find the edges — where does Notion feel awkward? Where does the block model impose constraints on what you can do? Having specific, genuine product opinions is essential for the values round.

### Week 4: Mock Interviews, Notion AI, and Final Prep

Spend several hours understanding Notion AI as a product and as an engineering challenge. How does AI output integrate with the block model? When Notion AI drafts a document, what data flows between the AI service and the editor? When Notion AI fills a database property, what API calls does that represent? Think about how you would architect AI-generated blocks so they compose correctly with user edits, undo history, and OT transforms.

Do two to three full mock system design sessions on Notion-specific problems. Do one full behavioral prep session with STAR stories for each theme above. Prepare specific, genuine Notion product feedback: what you find magical, what frustrates you, and what you would build next. This is not flattery — interviewers can tell the difference between genuine product engagement and preparation theater.

## Practical Advice

**Use Notion as your actual workspace during preparation.** Use it for your interview prep notes, your reading list, your practice problem tracking. This builds genuine fluency and genuine opinions. Candidates who use Notion as a checkbox (downloaded it, opened it once, looked at the block model) are transparent in interviews.

**Know ProseMirror by name.** Notion's engineering team has referenced it publicly. When discussing the editor architecture, using ProseMirror's vocabulary — schema, document model, transactions — signals that you have gone beyond surface preparation. If you have actually built something with ProseMirror, mention it.

**Understand Notion's product philosophy, not just its features.** Notion's "building blocks vs. features" philosophy — the decision to provide primitives (block types, relations, formulas, views) rather than opinionated templates — is deeply intentional. It is why Notion can be used as a note-taking app, a project manager, a CRM, and a wiki without being purpose-built for any of them. Understanding why this is a hard design choice (and what it costs in onboarding complexity) demonstrates business-level product thinking.

**Common failure modes:**

Treating the take-home as a speed exercise. Notion's take-home is assessed on design quality, code clarity, and thoughtfulness of trade-offs — not on how many features you packed in. A clean, well-tested, well-explained implementation of a smaller scope is better than a complete but messy implementation.

Generic behavioral answers about "writing clean code" and "shipping on time." Notion's values round is not checking whether you are professional and diligent. It is checking whether you have the specific orientation toward craft and product quality that Notion's culture requires. The bar is higher than "I care about quality" — it requires specific stories that demonstrate that caring.

Not having real product opinions. Candidates who cannot articulate what they love about Notion or what they find frustrating — from genuine product use, not from Googling "Notion weaknesses" — do not pass the values round. This is not about passing a test. It is about whether you have the same relationship to great software that the people who built Notion have.

The engineers who succeed at Notion are the ones for whom software quality is intrinsically motivating — not because it helps with performance reviews, but because software that feels wrong bothers them the same way a misaligned table bothers a carpenter. That instinct is what the entire Notion interview process is designed to find.
