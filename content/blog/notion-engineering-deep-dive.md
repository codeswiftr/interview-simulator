# Notion Engineering Deep Dive: Blocks, Real-Time Sync, and the Sharding Migration That Changed Everything

Here is the core engineering challenge at Notion: build a document editor that is also a relational database that is also a wiki that is also a kanban board that is also a project management tool — and make every one of those things work together in real time, across devices, with offline support, at scale, while integrating AI in a way that actually understands the document's structure. Every one of those requirements, in isolation, is a hard engineering problem. Notion does all of them simultaneously on top of a single unified data model.

That unified data model is the block.

Understanding how blocks work, how they sync, how they scale, and how AI sits on top of them is what Notion engineering interviews are actually testing. This post goes deep on all four.

---

## The Block Data Model: Everything Is a Block

Notion's entire information architecture is built on a single primitive: the block. Pages are blocks. Paragraphs are blocks. Headings, bullet points, code snippets, toggle lists, callouts, databases, database rows, database views, embedded PDFs, images, video embeds — all blocks. This is not a coincidence of naming; it is a deliberate architectural decision with deep consequences for how the data is stored and queried.

A block has a fixed schema with a small number of fields that are the same regardless of type, and a flexible `properties` field (stored as JSONB in Postgres) that holds type-specific content:

```sql
CREATE TABLE blocks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  space_id    UUID NOT NULL,          -- workspace / tenant
  parent_id   UUID REFERENCES blocks(id),
  parent_type TEXT NOT NULL,          -- 'block', 'space', 'user'
  type        TEXT NOT NULL,          -- 'page', 'paragraph', 'database', etc.
  properties  JSONB,                  -- type-specific content (rich text, url, etc.)
  content     UUID[],                 -- ordered list of child block IDs
  permissions JSONB,                  -- access control list
  created_by  UUID NOT NULL,
  edited_by   UUID NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now(),
  edited_at   TIMESTAMPTZ DEFAULT now(),
  alive       BOOLEAN DEFAULT TRUE,   -- soft deletes
  version     BIGINT DEFAULT 0        -- optimistic locking / conflict detection
);

CREATE INDEX idx_blocks_parent ON blocks(parent_id);
CREATE INDEX idx_blocks_space   ON blocks(space_id);
CREATE INDEX idx_blocks_type    ON blocks(type, space_id);
```

The recursive structure is the critical insight. Because a page is just a block with `type = 'page'`, and its children are listed in the `content` array (an ordered list of UUIDs), nesting is infinitely deep and uniform. A toggle block contains child blocks. A column layout block contains column blocks, which contain content blocks. A database block's rows are themselves blocks, and each database property value is an entry in the row block's `properties` JSONB field.

Fetching a full page is a recursive tree walk — load the root block, then recursively fetch all blocks whose IDs appear in `content`, depth-first. Notion exposes this through a `getRecordValues` API that allows bulk block fetches (batching hundreds of IDs in one round trip), and a `loadPageChunk` endpoint that fetches a subtree to a configurable depth, enabling the client to eagerly load visible content and lazy-load collapsed sections.

The practical engineering tradeoff here is flexibility versus queryability. JSONB properties let Notion add a new block type without a schema migration — you just start writing a new `type` value with a new `properties` shape. But it means that full-text search across blocks requires a separate index (Notion maintains an inverted text index, and later added their own in-house search infrastructure on top of Elasticsearch), and complex relational queries across database blocks require denormalized view tables that are kept in sync with the block tree.

---

## Real-Time Collaboration: Simpler Than You Think, Harder Than It Looks

Operational Transform (OT) is the algorithm behind Google Docs. It is also notoriously hard to implement correctly — the number of paper retractions and bug-ridden implementations in OT's history is instructive. CRDTs (Conflict-Free Replicated Data Types) are the academic successor. Notion uses neither of these in their full general form.

Notion's collaboration model is based on a simpler observation: most document edits are not truly concurrent. When two people edit the same Notion page simultaneously, they are almost always editing different blocks — different paragraphs, different database rows, different properties. The block tree's granularity acts as a natural conflict partition. Conflicts within the same block (two people typing into the same paragraph at the same time) are uncommon enough that a last-write-wins strategy with optimistic locking covers the vast majority of real-world cases.

The sync protocol works like this. Every client maintains a local cache of block data indexed by block ID, a version vector tracking the last known version of each block, and a WebSocket connection to Notion's sync server.

When a user makes an edit locally, the client:
1. Applies the change to the local block cache immediately (optimistic update).
2. Emits a transaction to the sync server containing the changed blocks and their expected versions.
3. Receives an acknowledgment with the server-assigned version numbers.

When the sync server receives a transaction:
1. It checks that the expected versions match the current stored versions (optimistic lock check).
2. On version conflict, it rejects the transaction and the client must reconcile.
3. On success, it increments version numbers, persists the changes, and broadcasts the new block states to all other connected clients via their WebSocket connections.

A simplified representation of the transaction payload:

```typescript
type BlockValue = {
  id: string;
  type: string;
  properties: Record<string, unknown>;
  content: string[];  // ordered child IDs
  version: number;
};

type Transaction = {
  id: string;               // idempotency key
  spaceId: string;
  operations: Array<{
    pointer: { table: "block"; id: string };
    command: "set" | "update" | "listBefore" | "listAfter" | "listRemove";
    path: string[];         // JSON path within the block value
    args: unknown;          // the new value or list element
  }>;
};
```

The `listBefore` and `listAfter` commands handle ordering within the `content` array — dragging a block to a new position produces one of these commands rather than replacing the entire array, reducing the serialization surface area and making conflict resolution easier.

Offline support is handled by queueing transactions locally (in IndexedDB on web, in SQLite on mobile) and replaying them when connectivity returns. Replayed transactions go through the same version-check pipeline — if a conflict is detected, Notion generally resolves it by accepting the server state for text blocks and merging non-conflicting property changes where possible.

---

## Sharding the Monolith: The 2022 Postgres Migration

In February 2022, Notion published what became one of the most-read engineering blog posts of that year: a detailed account of how they sharded their Postgres database. It is required reading for anyone interviewing at Notion for backend or infrastructure roles.

The setup: Notion was running on a single Postgres instance. As the product grew to millions of users and tens of millions of blocks, the database became the bottleneck. A single Postgres node has limits — connection pool saturation, replication lag on the replica set, index scan times on tables with hundreds of millions of rows, vacuum contention on high-write tables. Notion hit all of these.

The decision was to shard by `space_id` (workspace ID). This is a natural partition key because almost all queries are scoped to a single workspace — when you open a Notion page, you are fetching blocks, permissions, and user data all within one `space_id`. Cross-workspace queries are rare and can be handled at the application layer by fanning out to multiple shards.

The migration strategy was what made the post famous. They could not just take downtime and copy data — Notion is a real-time collaborative tool that people depend on continuously. Their approach:

1. **Dual-write**: First, modify the application to write every mutation to both the old monolith and the new sharded cluster simultaneously, with the monolith as the source of truth. This ran for weeks to build confidence and allow backfill.
2. **Backfill**: Copy existing data from the monolith to the correct shards in the background, space by space, in batches. The dual-write guarantee meant new writes would not be missed during the backfill window.
3. **Verification**: For each `space_id`, after the backfill completed, run a hash-based consistency check comparing row counts and checksums between the monolith and the target shard.
4. **Cutover**: Flip the routing layer to read from the new shard for the verified `space_id`, stop writing to the monolith for that space, and monitor error rates for regression.
5. **Cleanup**: Once all spaces were migrated and stable, decommission the monolith tables.

The verification step deserves emphasis. They did not trust that the migration was correct — they proved it, space by space, before cutting over. At the scale of millions of spaces, this verification pipeline was itself a distributed systems problem.

The engineering lesson is general: large-scale data migrations require dual-write windows, incremental verification, and space-by-space (or tenant-by-tenant) cutover rather than a single big-bang migration. This pattern appears in interviews as "how would you migrate a multi-tenant database to a sharded architecture with zero downtime?"

---

## Notion AI: LLMs Inside a Block-Aware Document Editor

Integrating LLMs into a document editor is not just a matter of calling an API. The hard parts are context management, streaming, and awareness of document structure.

When a user invokes Notion AI on a block — to rewrite a paragraph, summarize a page, or generate content — the system must construct a prompt that gives the model relevant context from the block tree. This is not trivial. A 10,000-word page cannot be fully included in a prompt due to context window limits (and even if it could, you would not want to — irrelevant context degrades response quality). Notion's approach involves selecting contextually relevant ancestor blocks (the page title, the section header, nearby paragraphs) up to a token budget, then injecting the target block and the user's instruction.

The block tree's uniform structure is valuable here. Because every block has a type, Notion's context-building code can apply type-specific rules: always include the `page` title block, include the nearest `heading_1` and `heading_2` ancestors, include the two preceding sibling blocks and one following sibling block, truncate `database` blocks to their schema rather than all rows.

Streaming is handled at the block level. When the model generates text, each token is streamed back over the WebSocket and applied as an incremental update to the target block's `properties.title` JSONB field. From the database's perspective, this is a high-frequency write pattern on a single block — Notion batches these in-memory and writes to Postgres in coalesced intervals rather than per-token.

The most important engineering decision in Notion AI is that it writes into the same block data model used by everything else. AI-generated content is not a separate entity type — it is blocks, created by the AI with `created_by` set to an AI user ID, subject to the same version, permissions, and collaboration infrastructure as human-authored blocks. This architectural unity means features like "undo AI edit," "collaborative editing of AI-generated content," and "AI edits show in version history" work automatically.

---

## Interview Implications: What Notion Is Actually Testing

Notion's engineering organization is small relative to the product's scale — the company has historically run with fewer engineers than comparable-stage startups, which means high ownership, high scope, and high expectations for ambiguity tolerance.

**System design questions you should be ready for:**

- Design a real-time collaborative document editor. Expect follow-ups on conflict resolution, offline sync, and how you would partition state between client and server.
- Design a block-based CMS that can represent any content type with a single data model. The interviewer wants to see you reason about JSONB vs. normalized columns, recursive tree queries, and the tradeoffs of schema flexibility.
- How would you shard a multi-tenant Postgres database with zero downtime? Dual-write, backfill, verification, and incremental cutover should all appear in your answer.
- How would you integrate an LLM into a document editor such that it writes into the same data model as human edits? Expect questions about context window management, streaming, and undo semantics.

**What Notion looks for in engineers:** ownership instinct, comfort with recursive data structures, distributed systems intuition (especially around eventual consistency and conflict resolution), and the ability to reason about migration strategies for production systems under live load. They also want engineers who have opinions about product — Notion is a tool that engineers use themselves, and the company values people who think about the user experience of technical decisions.

The Notion engineering blog is an unusually rich resource. Reading the Postgres sharding post, their posts on performance improvements to the block editor, and their writing on search infrastructure will give you a concrete picture of the kinds of problems the team works on daily — and the level of technical rigor they expect when you walk in to talk about them.
