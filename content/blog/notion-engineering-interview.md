---
title: "Notion Engineering Interview: Block Model, Database Architecture, and What to Prepare"
description: "A technical deep dive into Notion's engineering stack, block-based data model, database-as-a-spreadsheet architecture, and how to prepare for their software engineering interviews."
date: "2026-03-20"
category: "Company Deep Dives"
---

# Notion Engineering Interview: Block Model, Database Architecture, and What to Prepare

Notion has become one of the most technically interesting productivity companies to interview at, not because the problems are necessarily harder than FAANG, but because the product's architecture demands careful thinking about collaborative data models, real-time sync, and schema flexibility. Understanding how Notion actually works makes you a far better candidate.

## The Block Data Model

Everything in Notion is a block. Pages, paragraphs, headings, databases, images, embeds — all are represented as a uniform `Block` entity in the data model. This design choice drives most of Notion's engineering tradeoffs.

A simplified block schema looks like:

```typescript
interface Block {
  id: string;           // UUID
  type: BlockType;      // "paragraph" | "heading_1" | "database" | "page" | ...
  properties: Record<string, PropertyValue>;
  content: string[];    // ordered list of child block IDs
  parent_id: string;
  parent_table: "block" | "space" | "collection";
  version: number;
  created_time: number;
  last_edited_time: number;
  alive: boolean;
}
```

The `content` array contains ordered child block IDs, making the document structure an n-ary tree stored in a flat key-value store. This enables efficient updates — moving a block is just rewriting the `content` arrays of two parent blocks, not restructuring a hierarchical table.

**Why this matters for interviews**: Notion interviewers love asking candidates to design collaborative document editing systems. The block model is Notion's answer to the problem of representing arbitrary document structure without a fixed schema. Be ready to discuss its tradeoffs: the simplicity of a uniform entity type vs. the overhead of assembling deep page trees through multiple lookups.

## Databases as a Spreadsheet: Collections

Notion's "databases" are a layer built on top of the block model. Internally, they're called **Collections**. A Collection is a set of page blocks with a shared schema — each row is a full Notion page, and the columns are properties attached to that page's block.

```typescript
interface Collection {
  id: string;
  schema: Record<PropertyId, PropertySchema>;
  // schema example:
  // "title": { name: "Name", type: "title" }
  // "status": { name: "Status", type: "select", options: [...] }
  // "due_date": { name: "Due Date", type: "date" }
}
```

A Collection View (table, board, gallery, calendar, timeline) is a separate entity that references the collection and applies filtering, sorting, and grouping rules client-side or through a server-side query engine.

This architecture means that "switching a database to board view" doesn't mutate data — it's purely a view configuration change. Multiple users can have different views open on the same underlying collection simultaneously, which simplifies the collaboration model significantly.

## Real-Time Collaboration: The Sync Engine

Notion's real-time collaboration infrastructure uses Operational Transformation (OT) rather than CRDTs, which is an interesting choice given that most modern collaborative editors have moved toward CRDTs (Figma, Linear, and Google Docs' current implementation all use CRDT variants).

The decision to use OT was partly historical (Notion was built before CRDTs became mainstream in production) and partly because OT fits naturally with Notion's server-authoritative model: the server always has the canonical state, and clients submit operations that are transformed against the server's current version before being applied.

Operations are typed by block action:

```typescript
type Operation =
  | { command: "set"; id: string; path: string[]; args: Record<string, any> }
  | { command: "update"; id: string; path: string[]; args: Record<string, any> }
  | { command: "listAfter"; id: string; path: string[]; args: { id: string; after?: string } }
  | { command: "listRemove"; id: string; path: string[]; args: { id: string } };
```

The `listAfter` and `listRemove` commands handle the `content` array (ordered child blocks) with position-aware semantics, while `set` and `update` handle property changes. This typed operation vocabulary is what makes transformation tractable — the OT engine only needs to handle a small set of commuting operations.

## The Tech Stack

Notion's current stack (from engineering blog posts and job listings):

- **Frontend**: React + TypeScript, custom rich text editor built on a virtual DOM specific to their block model
- **Backend**: Node.js + TypeScript for the API layer, Go for performance-critical services
- **Data layer**: PostgreSQL as the primary store (blocks stored in a JSONB column), Redis for real-time pub/sub, AWS S3 for file storage
- **Sync**: WebSocket-based real-time connection per workspace, operations fanned out via Redis pub/sub to connected clients
- **Search**: Elasticsearch for full-text search across block content

The PostgreSQL + JSONB choice is notable. Block properties are stored as JSONB, allowing schema flexibility without migrations every time a new block type or property type is added. The tradeoff is weaker query performance for structured queries — filtering a database by a select property requires a JSONB path expression, not a standard column index.

## Interview Process

Notion's interview process typically consists of:

1. **Recruiter screen** (30 min): Background, motivation, compensation alignment
2. **Technical phone screen** (60 min): One medium LeetCode-style problem + light system design
3. **Take-home project** (some roles): Build a small feature — often related to text editing or block manipulation
4. **Onsite / virtual loop** (4–5 rounds):
   - Two coding rounds (data structures and algorithms, medium-hard difficulty)
   - System design round (collaborative editing, database sync, or similar)
   - Cross-functional / product thinking round
   - Hiring manager behavioral round

**What Notion looks for**: Engineers who think about product experience, not just technical correctness. Notion's team is famously small for the scale they operate at — they want generalists who can own systems end-to-end and have strong opinions about product quality.

## Preparation Tips

**For the coding rounds**: Focus on tree traversal, graph algorithms, and string manipulation — all relevant to the block model. LeetCode mediums are the target bar; a few hards if you're interviewing for senior roles.

**For system design**: Practice designing collaborative editing systems. Know the difference between OT and CRDTs. Be ready to discuss conflict resolution in concurrent edits, cursor synchronization, and presence indicators.

**For the product round**: Use Notion heavily beforehand. Form opinions about what works and what doesn't. Notion interviewers respond well to candidates who have real frustrations with the product and concrete ideas for improvement grounded in technical understanding.

**Key concepts to review**: B-tree indexes on JSONB, WebSocket multiplexing, event sourcing vs. operation logs, and the CAP theorem implications for a server-authoritative sync model.

Notion is a company where deep product curiosity and technical rigor reinforce each other. The engineers who thrive there are the ones who can't stop thinking about how the product works — and how it could work better.
