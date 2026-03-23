# Atlassian Engineering Deep Dive: How the Company That Makes Dev Tools Builds Them

There is something unusual about Atlassian's engineering position: the people using Jira, Confluence, Bitbucket, and Trello every day are often the same kind of engineers building them. This creates a feedback loop that few companies have — Atlassian engineers are direct users of their own products, and the engineering culture reflects that. The decisions they have made about architecture, scaling, and tooling are not made in the abstract. They are made by people who feel the consequences.

Understanding what those decisions actually are — not the marketing version, but the technical reality — is what distinguishes a strong Atlassian candidate from one who just read the docs. This guide goes into four areas where Atlassian's engineering choices are substantive, publicly documented, and directly relevant to what interviewers evaluate.

---

## Jira's Architecture: From Monolith to Multi-Tenant Cloud

Jira began in 2002 as a monolithic Java application — a single deployable unit running against a single database schema per customer. This worked fine when "at scale" meant a few thousand issues per installation, and when Atlassian sold perpetual licenses for on-premises deployment. It became untenable when Atlassian shifted to cloud-first and had to support 200,000+ customers on shared infrastructure.

The core problem is tenant isolation in a multi-tenant SaaS environment. In the original model, each customer had their own database schema. Moving to the cloud meant Atlassian had to decide: maintain separate schemas per customer (expensive, operationally complex) or move to a shared schema with tenant IDs (cheaper, but every query needs a tenant discriminator and a schema design mistake exposes customer data across tenants).

Atlassian's approach for Jira Cloud uses a combination of both. High-volume customers get dedicated database infrastructure. Smaller tenants are co-located on shared database clusters with schema-level isolation. The routing layer — which determines which database cluster a given request goes to — is a critical component that must be fast, highly available, and consistent. A routing failure does not degrade performance for one customer; it degrades it for all customers whose tenant mappings live in the same routing partition.

The migration from the server-era monolith to this architecture required Atlassian to extract the Jira "platform" (authentication, permissions, search indexing, notifications, workflow engine) into services that could be operated independently. This is not a clean microservices decomposition — it is a pragmatic extraction of components that had independent scaling requirements. The result is a system where the workflow engine (which evaluates state machine transitions for issue status changes) is a separate service from the issue storage layer, which is separate from the search indexing pipeline.

**The interview implication.** When Atlassian asks you to design an issue tracking system, the candidate who describes a single service with a monolithic database is not wrong — that is how Jira started. The candidate who earns a strong hire demonstrates awareness of the isolation problem at multi-tenant scale: how do you ensure one customer's expensive JQL query does not starve another customer's throughput? How do you handle a tenant migration when you need to move a large customer to dedicated infrastructure without downtime? These are the operational problems Atlassian engineers live with.

---

## Search at Atlassian: Elasticsearch, CQL, and the Intelligence Layer

Atlassian uses Elasticsearch as the core search index for both Jira and Confluence. The choice is not surprising — Elasticsearch's distributed indexing, relevance scoring via BM25, and faceted search support align well with the query patterns both products need. But the implementation details matter more than the technology selection.

For Jira, the search surface is JQL (Jira Query Language), a structured query language that translates user queries into Elasticsearch queries. A JQL statement like:

```
project = MYPROJ AND assignee = currentUser() AND status != Done ORDER BY updated DESC
```

must be parsed, resolved (currentUser() is a function that resolves at query time to the authenticated user's account ID), and translated into an Elasticsearch bool query with term filters, a must_not clause, and a sort spec. The parser handles operator precedence, quoting, function calls, and a set of reserved field names that map to specific Elasticsearch index fields. Atlassian open-sourced parts of this infrastructure, and their engineering blog has detailed posts on the parser architecture.

The indexing pipeline is where the complexity concentrates. Every time an issue is updated — a field changes, a comment is added, a transition fires — the change must be reflected in the Elasticsearch index. Atlassian uses an event-driven pipeline: issue mutations publish change events to a queue (Kafka internally), a set of index workers consume those events, fetch the current issue state from the source of truth database, and apply a partial update to the Elasticsearch document. The challenge is consistency under concurrent updates: if an issue receives five rapid field changes, the index workers must apply them in order, or the final indexed state will not match the database state.

Confluence's search uses a similar architecture but indexes structured and unstructured content differently. A Confluence page contains a mix of structured data (page title, space key, creator, labels, last-modified date) and unstructured content (the body text, which can be complex wiki markup or structured macros). The indexing pipeline must extract searchable text from the page body, handle embedded content (PDFs attached to pages, table data in macros), and apply field boosting so that matches in the title rank higher than matches in body text.

**Atlassian Intelligence** is the AI feature layer that Atlassian began shipping in 2023. It is built on top of existing infrastructure but adds a retrieval-augmented generation (RAG) layer: when a user asks a question in Confluence's AI search, the system retrieves candidate pages using vector similarity search (embeddings stored in a vector index alongside the existing Elasticsearch index), augments the LLM prompt with those retrieved chunks, and generates an answer grounded in the actual Confluence content of that organization. The key engineering challenge is freshness: the vector index must be kept in sync with page updates at the same rate as the text index. A page edited five minutes ago that is not yet reflected in the vector index will not be retrieved as a candidate for AI-generated answers, leading to stale or incorrect responses.

---

## Bitbucket: Git at Scale

Bitbucket's engineering challenge is different from Jira's and Confluence's. Git is a fundamentally local-first, filesystem-based system. The reference implementation (`git` the CLI) is designed to run on a developer's machine against a local repository. Scaling it to serve millions of push, pull, and clone operations per day across repositories that range from a few kilobytes to hundreds of gigabytes requires a different approach.

Atlassian has published details on their Git serving infrastructure. The core architecture separates repository storage from request serving. Repository data (Git objects, refs) is stored on distributed object storage — S3-compatible in their cloud infrastructure. The serving layer (the component that speaks the Git wire protocol to `git clone` and `git push` on the client side) is a stateless service that reads and writes to object storage. This allows the serving fleet to scale horizontally without each node needing a local copy of every repository.

The Git wire protocol is a binary streaming protocol. When you run `git clone`, the server first sends a reference advertisement (the set of all ref names and their SHA1 object IDs). The client responds with a list of objects it wants (the ones it does not already have). The server then streams a packfile — a compressed binary bundle of Git objects — back to the client. This protocol was not designed with horizontal scale in mind: the traditional implementation held the entire negotiation state in memory on a single server. Atlassian's implementation must handle this statefully-appearing protocol across a stateless serving layer, typically by externalizing the negotiation state to a fast key-value store.

Large File Storage (LFS) compounds the problem. LFS separates large binary files (videos, design assets, ML model weights) from the Git object graph, storing them in external blob storage and only putting pointers in the Git repo itself. Bitbucket's LFS implementation must handle parallel uploads and downloads of large files without saturating the serving layer, enforce storage quotas per repository, and handle partial uploads gracefully (a client that abandons a 2GB upload midway must not leave orphaned objects that consume quota without being reachable).

For very large repositories, Bitbucket supports partial clone and shallow clone operations that limit the amount of history transferred to a client. This requires the serving layer to compute an appropriate packfile that satisfies the client's constraints (only objects reachable from refs since a given date, or only blobs above a certain size threshold) efficiently — the naive implementation of walking the entire object graph for every clone operation does not scale.

---

## Real-Time Collaboration in Confluence: Operational Transformation at Production Scale

Confluence's collaborative editing — the ability for multiple people to edit the same page simultaneously and see each other's changes in real time — is one of the harder distributed systems problems in the Atlassian product suite.

The core challenge is concurrency. If two users edit the same paragraph at the same time, both starting from the same document state, their changes must be merged in a way that preserves the intent of both edits. The naive approach (last-write-wins) discards one user's work. The correct approach requires a concurrency control algorithm.

Atlassian's Confluence collaborative editing is built on Operational Transformation (OT). OT defines a set of primitive operations (insert character, delete character, retain range) and a transformation function that takes two concurrent operations and produces a version of each that can be applied after the other without conflict. The canonical example: if user A inserts "hello" at position 0 and user B inserts "world" at position 0 concurrently, the OT algorithm transforms B's operation to insert "world" at position 5 (after A's insert), so that both insertions are preserved in the final document.

The implementation challenge with OT is maintaining the transformation invariants under arbitrary concurrency. The algorithm must be correct under all interleavings of concurrent operations, not just the simple two-user case. Atlassian uses a server-centric OT model: all operations are serialized through a central server that applies the transformation and broadcasts the transformed operation to all clients. This avoids the peer-to-peer consistency problem at the cost of adding server latency to every keystroke.

The WebSocket infrastructure that supports this is substantial. A Confluence page with 30 concurrent editors has 30 persistent WebSocket connections that must all receive every operation in order, at low latency. The WebSocket serving layer is partitioned by document: all connections for a given document are routed to the same server node, which maintains the authoritative operation log and transformation state for that document. If a node fails, the connections are re-established against a new node that reconstructs the document state from persistent storage — the operation log is written to durable storage synchronously before acknowledging any client operation.

Here is a simplified illustration of the OT server loop in Python:

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class Operation:
    type: Literal["insert", "delete", "retain"]
    position: int
    content: str = ""  # for inserts
    length: int = 0    # for deletes/retains

def transform_insert_insert(op_a: Operation, op_b: Operation) -> Operation:
    """Transform op_b against a concurrent op_a (both inserts)."""
    if op_a.position <= op_b.position:
        # A inserts before B's position — shift B right
        return Operation(
            type="insert",
            position=op_b.position + len(op_a.content),
            content=op_b.content
        )
    return op_b  # A inserts after B — B's position unchanged

class OTServer:
    def __init__(self):
        self.document = ""
        self.operation_log: list[Operation] = []

    def apply_client_operation(self, op: Operation, client_revision: int) -> Operation:
        """
        Transform and apply a client operation.
        client_revision: the server revision the client was at when they generated op.
        """
        # Transform op against all server operations since client_revision
        transformed_op = op
        for server_op in self.operation_log[client_revision:]:
            if transformed_op.type == "insert" and server_op.type == "insert":
                transformed_op = transform_insert_insert(server_op, transformed_op)

        self._apply_to_document(transformed_op)
        self.operation_log.append(transformed_op)
        return transformed_op  # broadcast this to all other clients

    def _apply_to_document(self, op: Operation) -> None:
        if op.type == "insert":
            self.document = (
                self.document[:op.position]
                + op.content
                + self.document[op.position:]
            )
        elif op.type == "delete":
            self.document = (
                self.document[:op.position]
                + self.document[op.position + op.length:]
            )
```

This is a minimal illustration — production OT handles a richer operation set, attribute changes (bold, italic, heading levels), and concurrent deletes against concurrent inserts, each of which has its own transformation rule. The correctness of the transformation function across all operation type pairs is what determines whether two concurrent edits converge to a consistent document state.

The alternative to OT — CRDTs (Conflict-free Replicated Data Types) — is used by Figma and Notion. CRDTs achieve convergence by construction: operations are designed to be commutative and associative, so any ordering of concurrent operations produces the same result. The tradeoff is that CRDT document representations are more complex and tend to accumulate tombstones (deleted elements that must be retained to ensure convergence), requiring periodic compaction. OT requires a central server but keeps the document representation clean. For a product like Confluence where collaboration happens in sessions with a bounded set of concurrent editors, the centralized OT model is a reasonable choice.

---

## Interview Implications: What Atlassian Is Actually Testing

Atlassian's technical interview evaluates two things that are related but distinct: whether you can solve the problems, and whether you think about them the way Atlassian engineers think about them.

The "thinking like an Atlassian engineer" component shows up in specific patterns. First, they expect you to reason about enterprise-scale multi-tenancy — the fact that Jira serves 200,000+ customers on shared infrastructure is not background color, it is the central constraint that shapes every architectural decision. When you design an issue tracker, the interviewer will push on tenant isolation. When you design a search system, they will push on query fairness across tenants.

Second, they expect operational awareness. Atlassian's engineers own their systems end to end. Questions about collaborative editing are not just asking whether you know what OT is — they are asking whether you understand the failure modes: what happens when the WebSocket node holding a document's state crashes mid-session? How do you reconstruct document state? How do you prevent clients from diverging during the reconnection window?

Third, the values interview (which they take as seriously as the technical rounds) uses STAR format with an added reflection step. They are not looking for stories where everything went perfectly. They are looking for stories where you made a decision under uncertainty, owned the outcome — good or bad — and extracted something concrete from the experience. "Build with heart and balance" is not a platitude to them; it is an evaluation criterion. Candidates who describe shipping a feature by cutting corners on reliability, without acknowledging the tradeoff they made and why it was or was not worth it, do not align with this value in the interview.

The strongest Atlassian candidates are engineers who have thought seriously about the problems their tools create for users — and who can demonstrate, with specificity, that they approach engineering decisions the same way. Atlassian's engineering culture is one where the customer (often another engineer) is visible and close. Interview like someone who knows that, and the rest follows.
