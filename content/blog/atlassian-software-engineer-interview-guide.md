# Atlassian Software Engineer Interview Guide 2024: Process and Preparation

Atlassian builds the collaboration tools that power engineering teams worldwide — Jira, Confluence, Trello, Bitbucket, and Loom. Their engineering interview is known for being thorough but fair, with a strong emphasis on values alignment and system-level thinking. Here's what to expect.

## Atlassian's Engineering Culture

Atlassian operates with five core values: **Open company, no bullshit** / **Build with heart and balance** / **Don't #@!% the customer** / **Play, as a team** / **Be the change you seek**. These aren't wall decorations — interviewers actively evaluate how you embody these values.

The engineering culture is shaped by:
- **Team autonomy**: Teams own their domains end-to-end — design, build, operate
- **ShipIt hackathons**: 24-hour innovation events that have spawned real products
- **Distributed-first**: Atlassian has operated TEAM Anywhere (fully distributed) since 2020 — async communication skills matter
- **Breadth + depth**: Engineers are expected to understand their systems fully, from the API down to the database schema

## Interview Format

The standard process for mid-level to senior engineers:

1. **Recruiter screen** (30 min) — background, role fit, logistics
2. **Technical screen** (60 min) — coding problem, often with follow-up complexity questions
3. **Virtual onsite** (4-5 rounds, typically one day):
   - 2 coding rounds
   - 1 system design round
   - 1 values interview
   - Occasionally: domain-specific (infrastructure, mobile, security)
4. **Hiring decision** (3-5 business days)

The values interview is taken as seriously as the technical rounds — failing it means no offer regardless of technical performance.

## Coding Rounds

Atlassian's coding bar is consistent LeetCode medium, occasionally medium-hard for senior roles.

**High-frequency topics:**
- Arrays, hashmaps, sliding window
- Trees and graphs (moderate emphasis)
- String manipulation
- Object-oriented design

**Atlassian-specific problem flavors:**

*Dependency resolution (Jira-inspired):*
> "Given a list of tasks where each task may depend on others, determine a valid execution order or detect if a cycle exists."

Topological sort — classic DAG problem. Know Kahn's algorithm (BFS-based) and DFS-based cycle detection.

```python
from collections import defaultdict, deque

def topological_sort(n: int, deps: list[tuple[int, int]]) -> list[int]:
    graph = defaultdict(list)
    in_degree = [0] * n

    for u, v in deps:  # v depends on u
        graph[u].append(v)
        in_degree[v] += 1

    queue = deque(i for i in range(n) if in_degree[i] == 0)
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order if len(order) == n else []  # Empty = cycle detected
```

*Permission system (Confluence-inspired):*
> "Design a class to model a permissions hierarchy where users can have permissions on spaces and pages, with inheritance from parent spaces. Support: grant permission, revoke permission, check if a user can perform an action."

Tests OO design thinking, permission inheritance, and edge cases (explicit deny vs. inherited allow).

*Rate limiter / throttler:*
> "Implement a token bucket rate limiter. Support: n requests per second per user. Multiple users. Thread-safe."

Common system building block — know token bucket vs. sliding window log vs. fixed window counter.

*Event log query:*
> "Given a stream of events (user_id, action, timestamp), implement: get all actions for a user in a time window, get top K users by event count in a period."

Similar in spirit to Jira audit logs — time-range queries, top-K with heaps.

**Common pitfalls Atlassian interviewers watch for:**
- Not asking clarifying questions (they value communication)
- Jumping straight to code before discussing the approach
- Ignoring edge cases (empty inputs, cycles, concurrent access)
- Not talking through time/space complexity unprompted

## System Design Round

Atlassian's system design questions lean toward collaboration tools and enterprise SaaS patterns.

**Common questions:**
- Design a collaborative document editor (Confluence-like)
- Design an issue tracking system (Jira-like)
- Design a notification system for a project management tool
- Design Bitbucket's pull request review workflow
- Design a real-time board (Trello-like)

**Collaborative document editor (canonical Atlassian design):**

This is the most frequently asked Atlassian system design question. Cover:

*Conflict resolution for concurrent edits:*
- **Operational Transformation (OT)**: Used by Google Docs. Each operation is transformed relative to concurrent operations before applying. Complex to implement correctly.
- **CRDTs (Conflict-free Replicated Data Types)**: Used by Figma, Notion. Operations are designed to be commutative/associative — always converge. Newer approach, better for distributed systems.
- For the interview: explain the tradeoff. OT is mature but complex. CRDTs are cleaner but require careful data type design.

*Architecture:*
- **Presence service**: WebSocket connections to track who's currently viewing/editing. Cursor positions broadcast via pub/sub.
- **Document storage**: Content stored as a sequence of operations (not the document snapshot). Enables undo, history, conflict replay.
- **Snapshot + delta**: Store snapshots every N operations for fast load; apply deltas on top.
- **Permission layer**: Can this user read this document? Can they edit? Does the sharing link allow access?

*Scale considerations:*
- Documents are typically session-bounded — most edits happen when a user has the doc open. Design for latency within a session.
- Cold load (user opens old document): rebuild from latest snapshot + trailing deltas.
- Pub/sub fanout: a doc with 50 concurrent editors means 50 WebSocket connections receiving every keystroke. Use presence rooms.

**Issue tracking system (Jira-inspired):**

Key entities: Project, Issue, Comment, Attachment, Workflow, Sprint, Board.

*Workflow engine*: Issues have states (To Do → In Progress → Done) with configurable transitions. This is a state machine — model it explicitly. Jira's power comes from customizable workflows per project.

*JQL (Jira Query Language)*: Users search issues with structured queries: `project = FORGE AND assignee = currentUser() AND status != Done`. This is essentially a SQL query builder over an issues table with many foreign keys. Indexing strategy matters: (project_id, status, assignee_id) covering index for common filters.

*Notification system*: Events (issue created, status changed, comment added) trigger notifications. Fan-out: an event on a high-priority issue might notify 20 watchers. Use async message queue (Kafka/SQS) for notification delivery.

## The Values Interview

This is Atlassian's most distinctive round. They use a structured behavioral interview mapped to their values.

**Preparation approach:**

For each value, prepare a story that demonstrates it:

*"Open company, no bullshit"* — Tell me about a time you delivered difficult feedback or surfaced a problem others were avoiding.

*"Build with heart and balance"* — Describe a decision where you had to choose between speed and quality. What did you do?

*"Don't #@!% the customer"* — Tell me about a time a user/customer was affected by something you built. How did you respond?

*"Play, as a team"* — Give an example of when you helped a teammate succeed, possibly at cost to your own work.

*"Be the change you seek"* — Tell me about an improvement you drove without being asked to.

**What interviewers are evaluating:**
- Specificity: vague answers get poor marks. "I helped my team" is not a story.
- Ownership: do you use "I" or "we"? They want to understand *your* contribution.
- Reflection: what did you learn? Would you do it differently?
- Alignment: does your instinct actually match Atlassian's values, or are you performing alignment?

**STAR+ format:**
- **Situation**: Context (brief — 2-3 sentences)
- **Task**: What was your responsibility?
- **Action**: What you specifically did (most of your time)
- **Result**: Outcome with metrics where possible
- **+Reflection**: What you learned or would do differently (Atlassian adds this)

## Behavioral Questions

**"Atlassian is distributed. How do you work effectively when your team is across time zones?"**

Concrete answer: async-first communication (Confluence pages > meetings where possible), explicit decision logs, clear async ownership, over-documentation of context. Mention specific tools/patterns you've used.

**"Tell me about a time you disagreed with a technical decision your team made."**

They want: you voiced the disagreement respectfully, you understood the counterarguments, you committed to the outcome once decided. "Disagree and commit" culture.

**"Describe a system you're proud of building. What would you change now?"**

Both parts matter. The "what would you change" reveals engineering maturity — senior engineers always have things they'd do differently.

## Preparation Timeline

**Week 1: Coding**
- 20 LeetCode medium problems (graphs, trees, hashmaps)
- Implement topological sort, token bucket rate limiter, LRU cache from scratch
- Practice explaining your approach before writing code

**Week 2: System design**
- Design a collaborative document editor (3 deep-dives: conflict resolution, presence, storage)
- Design an issue tracking system with workflow engine
- Read Atlassian Engineering blog (atlassian.com/engineering)

**Week 3: Values interview**
- Map your best stories to each of the 5 Atlassian values
- Practice STAR+ format — have 8-10 stories ready, crossmap to different values
- Read "The Atlassian Team Playbook" (free on their site) — understand their collaboration philosophy

**Week 4: Research + polish**
- Research specific team you're interviewing for (platform, mobile, Jira/Confluence/Trello)
- Practice 2 mock interviews with the "explain before coding" discipline
- Review Atlassian's public engineering talks (Atlassian Summit recordings on YouTube)

## What Sets Atlassian Candidates Apart

The engineers who succeed at Atlassian are genuinely comfortable with two things that trip up most candidates:

**1. Collaboration isn't soft.** Atlassian treats collaboration as a first-class engineering skill. Being able to discuss tradeoffs with a team, document decisions asynchronously, and hand off context to distributed colleagues — these are real skills that senior Atlassian engineers exercise daily.

**2. You own your system.** Atlassian engineers understand not just their code but their operational footprint — what breaks, how to debug it, what the failure modes are, how customers experience degradation. Strong candidates bring operational thinking to system design, not just architecture diagrams.

The combination of technical rigor, genuine values alignment, and collaborative working style is what makes a strong Atlassian candidate. The values interview isn't a checkbox — it's the mechanism they use to filter for people who'll thrive in a distributed, high-autonomy engineering culture.
