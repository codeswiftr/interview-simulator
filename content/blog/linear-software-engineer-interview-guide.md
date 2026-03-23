# Linear Software Engineer Interview Guide 2024: The Craft-Focused Productivity Startup

Linear has built something unusual in enterprise software: a product that engineers actually enjoy using. In an industry where project management tools are synonymous with sprawl, slowness, and feature bloat, Linear ships a keyboard-first, opinionated, fast productivity tool that has developed a genuine following among software teams. Their homepage once declared that most software is "designed by committee" and promised something different—software designed by people with strong opinions about quality.

That identity saturates the interview process. Linear does not just evaluate whether you can write correct code or design scalable systems. They evaluate whether you have taste. Whether you can make a judgment call about what a feature should be and what it should not be. Whether you feel the difference between an interaction that is delightful and one that merely works. This makes preparing for a Linear interview qualitatively different from preparing for most FAANG interviews, and candidates who approach it purely as a technical exercise tend to struggle.

Linear is a small company—fewer than 100 engineers—with a correspondingly high bar per engineer. Every person they hire has a significant leverage multiplier on the product. The hiring process reflects this reality: it is thorough, thoughtful, and explicitly filters for engineers who will raise the quality bar rather than just execute on tickets.

## Engineering Environment

Linear's engineering culture is defined by the word "craft." This is not marketing copy—it is reflected in specific, observable engineering practices.

The frontend codebase is built in TypeScript with React and bundled with Electron for the desktop app. Linear ships as a web app, a macOS/Windows desktop app, and a mobile app for iOS and Android. The core architectural commitment is offline-first: the application must be fully functional without a network connection, syncing changes to the server when connectivity is restored and resolving conflicts gracefully.

This offline-first requirement drove the choice of SQLite as the on-device database. Linear's client stores the full working set of issues, projects, cycles, and comments in a local SQLite database. The application reads and writes to this local database directly, and a sync engine handles bidirectional synchronization with the backend. This means the UI is always snappy—there are no loading spinners for basic operations because all reads hit local storage.

The sync engine is the most technically complex part of Linear's architecture. It handles conflict resolution when two users edit the same issue concurrently, offline edits that need to be reconciled with server state, and the ordering of operations during reconnection. Linear uses an operational transformation approach (similar in spirit to CRDTs, though not strictly conforming to the formal CRDT definition) that allows optimistic local updates to be applied immediately and reconciled with the authoritative server state asynchronously.

The backend runs on Node.js with TypeScript, backed by PostgreSQL. Linear uses GraphQL for its API, both for the web client and for its public developer API. The data model is relatively straightforward—the complexity lies in the sync layer—but the backend must handle concurrent updates to shared resources (issues being edited by multiple team members simultaneously) and propagate those updates to connected clients in real time via WebSocket subscriptions.

Linear engineers operate with significant autonomy. The engineering team is small enough that individuals own entire features end to end, from product decision through backend API through frontend rendering through mobile implementation. This means Linear looks for engineers who are comfortable and competent across the stack, even if they have a specialization.

The product philosophy, sometimes called "high signal," explicitly favors removing features over adding them. When a feature does not clearly serve the core use case, Linear removes it. This manifests in the interview process as an expectation that you can reason about product decisions under constraint—not just "how would you build this" but "should you build this, and if so, what is the minimum scope that delivers the value?"

## Interview Process

Linear's interview process is structured but conversational. It consists of roughly four to five rounds:

**Initial Screen (30 minutes):** A recruiter or engineering manager call to assess mutual fit, discuss your background, and explain the role. This is genuinely two-way—Linear wants to know if you have used the product and what you think of it.

**Technical Take-Home (4-8 hours):** Linear typically assigns a take-home project rather than a phone screen coding problem. The take-home is substantive—it may involve building a small React component with specific interaction behavior, implementing a simplified version of part of their sync engine, or writing a full CRUD API with a specified data model. The rubric focuses heavily on code quality: naming, structure, error handling, and whether the solution reflects good judgment about tradeoffs, not just whether it works.

Do not rush the take-home. Linear explicitly uses it to assess craft. An implementation that is correct but sloppily structured will not advance.

**Engineering Interview Rounds (3-4 rounds, typically over two days):**

- System design (60 minutes): Deep architectural discussion, often focused on sync systems, real-time collaboration, or product feature design.
- Technical depth (45 minutes): A deep dive into your area of expertise—frontend, backend, mobile, or infrastructure—often starting from your take-home or past project work.
- Product/judgment round (45 minutes): Discussions about product decisions, feature scoping, and how you think about quality. This is where "taste" is evaluated most explicitly.
- Values/culture round (30 minutes): Conversation about how you work, what you care about in software, and how you handle disagreement.

There are no whiteboard LeetCode problems in the Linear interview. Coding evaluation happens through the take-home and through conversational technical depth questions. If you are hoping to brute-force your way through with competitive programming skills, you will be disappointed.

## Technical Deep Dives

### The Sync Engine and Offline-First Architecture

The most important technical system to understand for a Linear interview is their sync engine. Offline-first architecture is notoriously difficult to get right, and Linear's approach is worth studying carefully.

The core challenge is this: user A is offline and edits issue #47, changing the title and the priority. Simultaneously, user B is online and also edits issue #47, changing the description and assigning it to a new person. When user A comes back online, how do you reconcile these concurrent changes without losing work or creating an inconsistent state?

Linear uses an operation-based approach. Every mutation is represented as an explicit operation with a unique ID, a timestamp, a reference to the entity being modified, the specific field being changed, and the new value. Operations are stored locally and synced to the server. The server applies a total ordering to operations (using logical timestamps, specifically a Lamport-clock-style monotonic counter), and clients reconcile their local state against the server's canonical operation log when they reconnect.

This approach makes conflict resolution tractable for most cases: if two users edited different fields of the same issue, both edits apply cleanly. If two users edited the same field, the operation with the later server timestamp wins, and the losing operation is rolled back locally.

The truly hard cases are structural conflicts: what if user A deleted an issue while user B was editing it? What if user A moved an issue to a different project while user B was reassigning it to a different team member? These cases require explicit conflict resolution policies that Linear has had to define for every type of concurrent mutation in their data model.

When discussing this in an interview, demonstrate that you understand the tradeoffs between different conflict resolution strategies:
- **Last-write-wins**: Simple to implement, but users can silently lose work.
- **Three-way merge**: More complex, produces better results for text fields, requires a common ancestor.
- **Operational transformation**: Correct for concurrent edits, expensive to implement correctly, prone to subtle bugs.
- **CRDTs**: Mathematically correct for specific data types (counters, sets, sequences), but not all application data fits cleanly into CRDT data types.

Linear's approach is pragmatic: most of their data is not free-form text, so last-field-wins with explicit rollback on the client is sufficient for most cases. Rich text (issue descriptions) is handled with a separate CRDT-based editor built on top of ProseMirror.

### SQLite on the Client

The decision to use SQLite in the browser and desktop app is not obvious, and understanding why Linear made this choice reveals a lot about their engineering philosophy.

Web applications traditionally store client state in JavaScript objects in memory, often managed by Redux or similar state libraries. This approach has a fundamental limitation: the state is ephemeral. When you refresh the page, the state is gone, and you need to re-fetch it from the server.

Linear chose SQLite as a persistent local store, accessed via WebAssembly in the browser (using the official SQLite WASM build) and via native bindings in the Electron app. This enables:

- **Full offline operation**: The application can render any view without a network request because all data is local.
- **Complex local queries**: With SQL, you can do complex filtering, sorting, and aggregation entirely on the client without round-tripping to the server.
- **Persistent cache**: The local database serves as a perfect LRU cache that survives page refreshes and application restarts.

The tradeoff is complexity: you now have two sources of truth (local SQLite and the remote PostgreSQL), and you need a sync engine to keep them consistent. You also have to manage SQLite migrations on the client as your schema evolves—a deployment concern most web developers never face.

Be prepared to discuss this architecture in depth. A strong answer will include the schema design choices that make sync tractable (for example, using server-assigned UUIDs rather than auto-increment IDs to avoid collision during offline creation of entities), the migration strategy for schema changes, and how you handle the case where a client's local database is severely out of sync after a long period offline.

### Real-Time Collaboration and WebSocket Architecture

Linear issues can be edited by multiple users simultaneously, and changes need to propagate to other connected users in near-real-time. This requires a WebSocket-based subscription system on the backend.

The architecture follows a standard pub/sub pattern: when a client subscribes to changes on a project or workspace, the backend tracks that subscription. When an operation is applied to the database, the backend enumerates all active subscriptions that include the affected entity and pushes the operation to those clients via WebSocket.

The interesting engineering challenges here are:
- **Connection management at scale**: With tens of thousands of concurrent users, the backend needs efficient subscription tracking. A naive implementation that stores subscriptions in memory does not survive server restarts or horizontal scaling.
- **Operation replay for reconnection**: When a client reconnects after a period offline, it sends the logical timestamp of the last operation it received. The backend must efficiently retrieve all operations after that timestamp that affect the client's subscribed entities.
- **Presence and awareness**: Linear shows you when other users are viewing the same issue or project. This requires a lightweight presence protocol separate from the main sync channel.

### GitHub and Slack Integrations

Linear's integrations with GitHub and Slack are deeply used features that involve non-trivial engineering. Understanding them is relevant both for system design questions and for demonstrating product engagement.

The GitHub integration links Linear issues to GitHub pull requests, branches, and commits. When a PR is merged, linked Linear issues can be automatically closed. When a PR is opened, the linked issue status is updated. This requires:
- A GitHub App that receives webhook events for PR and commit activity
- A mapping layer that extracts issue references from PR titles and commit messages using configurable patterns
- A reliable webhook processing pipeline that handles out-of-order delivery, duplicate events, and GitHub's rate limits

The Slack integration allows creating and updating issues from Slack messages and sending notifications about issue activity to Slack channels. The challenging part is the bidirectional nature: changes in Linear should flow to Slack, and actions taken in Slack (clicking a button in a notification to change issue status) should flow back to Linear. This requires a careful state machine for the integration's action handling.

## System Design

### Design a Sync Engine for a Collaborative Productivity App

This is the most likely system design question at Linear. The problem is to design a system that allows multiple clients to edit shared data concurrently, supports offline operation, and converges to a consistent state when clients reconnect.

Start by establishing constraints: How many users per workspace? (Linear serves teams of 5-500 engineers.) How many entities per workspace? (A large team might have 100,000 issues.) What is the acceptable latency for real-time updates to propagate to other users? (Linear targets under 500ms end-to-end.)

The architecture has three key components:

**Client-side state**: SQLite database with the full workspace state. Every mutation is written to SQLite first (optimistic update) and queued for sync. The sync queue is also persisted in SQLite so it survives application restarts.

**Sync protocol**: When the client connects, it sends its latest known server timestamp. The server responds with all operations since that timestamp that affect the client's workspace. Ongoing operations are sent in real time via WebSocket. The client applies received operations to its local SQLite database using the total server ordering.

**Conflict resolution**: For field-level conflicts, last-write-wins by server timestamp. For structural conflicts (delete vs. edit), the server applies the operation and notifies clients of the resolution. Clients must be prepared to roll back optimistic updates that the server rejected.

Call out the schema considerations: operations must be idempotent (applying the same operation twice should be a no-op) because clients may receive the same operation multiple times via different delivery paths. Use operation IDs and an `applied_operations` table in the local SQLite to deduplicate.

### Design Linear's Real-Time Notification System

A less common but equally valid system design question is the notification system: when an issue is assigned to you, or a comment is left on something you're watching, you should receive a notification immediately in the app, via email, and optionally via Slack.

This is a fan-out problem with multiple delivery channels. The key design decisions are:
- How do you determine who should receive a notification for a given event? (Subscription model: users subscribe to issues, projects, or workspace-wide activity.)
- How do you avoid notification spam while ensuring important events are surfaced? (Notification digesting: if ten comments are left in two minutes, batch them into one notification.)
- How do you handle notification delivery failures? (Idempotent operations with retry queues per delivery channel.)

## Behavioral and Culture Fit

Linear's values-based interview questions are less structured than Amazon's Leadership Principles but probe for a specific profile. The qualities Linear is most explicitly looking for:

**Taste**: Can you identify what makes software good or bad at a level of specificity beyond "it was fast" or "it was easy to use"? Be ready to articulate specific UX decisions that you admire or criticize and explain why in concrete terms—what interaction model was chosen, what alternatives existed, what tradeoffs were made.

**Judgment about scope**: The most common Linear values question is some variant of "Tell me about a time you advocated for doing less." They want to see that you understand the cost of feature bloat and have actively pushed back against unnecessary complexity. If you have stories about negotiating scope down rather than up, surface them here.

**Ownership**: Linear engineers own features end to end. They want to see that you can take a problem from fuzzy product requirement to shipped feature without requiring constant hand-holding. Describe a project where you made significant independent decisions.

**Directness**: Linear has a notably flat communication culture. Engineers are expected to disagree openly and argue for their positions rather than deferring to hierarchy. Stories about productive disagreement—where you pushed back on a product decision, an architecture choice, or a process—are valued.

Avoid giving answers that are primarily about quantity of output (shipped N features, closed N tickets). Linear cares much more about the quality and impact of what you built than the volume.

## Preparation Timeline

**Eight weeks out**: Get a Linear account if you do not have one and use it as your primary task management tool for the next two months. This is the most important preparation you can do. Using the product gives you genuine intuitions about the design decisions—the keyboard shortcuts, the command palette, the issue hierarchy—that you cannot get from reading about it.

**Six weeks out**: Study offline-first architecture deeply. Read "Local-first software" by Ink & Switch (a seminal essay that is directly relevant to Linear's approach). Study the Automerge and Yjs CRDT libraries. Understand SQLite well enough to design a schema and write complex queries.

**Four weeks out**: Study real-time collaboration systems. Read the Google Docs operational transformation paper. Study the Liveblocks and PartyKit documentation to understand modern approaches to collaborative editing infrastructure. Be able to explain the tradeoffs between OT and CRDT approaches.

**Two weeks out**: Polish your take-home submission quality. Pick a previous project or side project and refactor it to the level of quality you would want to show Linear. Pay attention to naming, code organization, error handling, and test coverage. Linear will evaluate how you write code when you have time to do it right.

**One week out**: Prepare product opinions. Write down three things you would change about Linear and why. Prepare to discuss them specifically—not vague impressions, but concrete interaction design critiques with proposed alternatives. This preparation also demonstrates that you have used the product seriously.

## Practical Advice

The take-home assignment is the highest-leverage preparation investment you can make. Linear uses it to evaluate craft, so submit work that reflects your best engineering—not your fastest engineering. Add comments where design decisions were made. Write tests. Handle edge cases. Structure the code as if you were going to maintain it for two years.

Read Linear's product changelog and blog before your interviews. Linear publishes thoughtful writing about their product decisions and engineering choices. Referencing specific decisions from their public writing signals that you have engaged with their product thinking seriously.

When discussing the sync engine or offline-first architecture in system design, do not pretend the problem is easier than it is. Linear engineers have spent years solving the hard edge cases. Saying "and conflict resolution is handled with operational transforms" without being able to describe what that means in concrete terms will not land well. Acknowledge the hard parts and explain how you would approach them.

One common mistake is treating Linear like a startup where you demonstrate enthusiasm by proposing sweeping new features. The culture respects restraint. When asked what you would add to Linear, give a considered answer that accounts for the product's existing scope and philosophy. Even better: describe what you would remove or simplify, and why.

Finally, the culture fit assessment is genuinely important at a company this small. Linear is not looking for someone who will fit in—they are looking for someone who will push the quality bar upward. The best way to demonstrate this is to show that you have strong opinions, can articulate them clearly, and have a track record of translating those opinions into tangible improvements in the software you have built.
