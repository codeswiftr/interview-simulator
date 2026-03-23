# GitHub Software Engineer Interview Guide 2024: What to Expect

GitHub is where the world's software lives. Owned by Microsoft since 2018 for $7.5 billion, GitHub hosts 100M+ developers, 330M+ repositories, and runs infrastructure that the entire software industry depends on daily — GitHub Actions, Copilot, Packages, Codespaces, and the version control layer underneath almost every production codebase on earth. With roughly 3,000 employees and a remote-first culture that predates the pandemic by over a decade, GitHub is one of the most interesting engineering organizations to join. There is also a particular irony in interviewing to work at GitHub: you are almost certainly using GitHub to store your interview prep code while preparing for a GitHub interview. Lean into that.

## GitHub Engineering Culture

GitHub has been remote-first since 2008 — before Zoom existed, before "distributed team" was a job description buzzword. This is not a pandemic-era adaptation. It is the original operating model, and it shapes everything about how GitHub engineers work and how they interview.

Key cultural values GitHub evaluates:

- **Async by default**: Written communication is a first-class skill. Pull request descriptions, GitHub Issues, and internal RFCs are how decisions get made, not Slack threads
- **Transparency**: Code, decisions, and process are visible. Engineers expect access to context and give context freely
- **Open source commitment**: GitHub engineers are expected to care about and contribute to open source, not just host it
- **Developer empathy**: The users are developers. GitHub engineers are expected to feel the friction developers feel and fix it

Microsoft ownership brought substantial resources — compute, enterprise distribution, and the capital to build Copilot — but GitHub has largely preserved its engineering culture. The Hubbers community (what GitHub employees call themselves) maintains a distinct identity within the larger Microsoft organization.

## Interview Process

GitHub's hiring process runs four stages:

1. **Recruiter screen** (30 min) — background, compensation alignment, logistics
2. **Take-home project** (3-7 days) — build a real feature, not a toy puzzle
3. **Technical review** (60 min) — walk through your take-home, defend decisions, discuss extensions
4. **Onsite** (3-4 rounds, virtual): 1-2 coding rounds + 1 system design round + 1 GitHub values fit interview

The take-home is the most distinctive element. GitHub does not rely primarily on LeetCode-style whiteboard sessions. Instead, you receive a spec for a small but real feature — something like a simplified version of a GitHub feature — and you build it over several days. The expectation is that your submission reflects how you actually work: commit history, code organization, README documentation, tests, and thoughtful tradeoffs.

**Critical take-home advice**: Do your work in a public GitHub repository. Your commit history should tell a coherent story. Squashing everything into one commit, or having messages like "fix fix fix more fix," signals you do not work the way GitHub expects engineers to work.

## Git Internals: The Knowledge They Expect

GitHub engineers are expected to understand Git at a level most engineers never reach. The expectation is not just "knows how to rebase" — it is "understands what a rebase actually does to the object graph."

**Git's object model**

Git stores everything in a content-addressable object store. There are four object types:

```
blob     — file contents (no filename, just bytes hashed to a SHA)
tree     — directory listing (maps filenames to blob/tree SHA references)
commit   — snapshot pointer (tree SHA + parent SHAs + metadata)
tag      — annotated tag (pointer to a commit with a signed message)
```

Every object is identified by `SHA-1(type + size + content)`. This means identical content — across repositories, across time — always produces the same hash. That is the deduplication mechanism.

**Pack files**

Individual loose objects are efficient for writes but expensive for network transfer. Git periodically runs `git gc` to pack loose objects into pack files using delta compression. A pack file stores a base object plus a series of deltas (binary diffs) to reconstruct subsequent versions. This is why `git clone` of a large repository is orders of magnitude smaller than the sum of all file versions ever committed.

**How `git push` works end-to-end**

```
1. Client sends "want" and "have" lists via the pack protocol (reference negotiation)
2. Server computes the minimal set of objects the client lacks
3. Server generates a pack file with delta compression for those objects
4. Client receives pack, verifies checksums, applies to local object store
5. Server updates refs atomically (fast-forward check; reject non-fast-forwards by default)
```

When you push to a remote, Git is not sending "the diff" — it is sending a pack file containing the full object graph of any commits the remote does not have, compressed with deltas relative to objects the remote does have. GitHub's infrastructure handles billions of these negotiation cycles daily.

**Interview application**: When a GitHub interviewer asks "what happens when you run `git push`?", the answer that gets offers goes through the pack protocol, reference negotiation, and delta compression — not just "it sends your commits to the remote."

## Large-Scale Object Storage

GitHub stores billions of Git objects across hundreds of millions of repositories. Designing storage systems at this scale is a genuine technical challenge they work on internally, and they expect senior candidates to reason about it.

**Key design considerations for a content-addressable object store at GitHub's scale:**

**Deduplication via content addressing**: Because SHA-1 (and increasingly SHA-256) uniquely identifies content, identical blobs stored across millions of repositories need only one physical copy. A popular open source library's `README.md` might be referenced by 10,000 repositories but stored once.

**Hot/cold storage tiering**: Repositories have highly skewed access patterns. Active repositories receive frequent pack fetches; archived or rarely-accessed repositories may go months without a read. Tiering objects to cheaper storage (object stores like S3 Glacier equivalents) for cold repositories dramatically reduces cost.

**Pack file management at scale**: With 10M+ pack files across a cluster, pack file indexing (the `.idx` file format that enables binary search into a pack without decompressing it) becomes critical. GitHub has written about their work on geometric repacking — maintaining a small set of pack files per repository using a geometric progression strategy to balance read and write amplification.

**Write path design**:
```
push received
  → loose object writes (fast, simple)
  → async pack consolidation job
  → geometric repack to maintain pack file count
  → cold tier migration for inactive repositories
```

## CI/CD Systems: GitHub Actions Architecture

GitHub Actions is a major product line and a core part of GitHub's infrastructure. Understanding its architecture deeply signals genuine product knowledge.

**Core concepts:**

- **Workflows**: YAML files in `.github/workflows/` — triggered by events (push, pull_request, schedule, workflow_dispatch)
- **Jobs**: Units of work that run on a runner; jobs within a workflow can run in parallel or sequentially via `needs`
- **Steps**: Individual commands or action calls within a job
- **Actions**: Reusable units of automation, either JavaScript or Docker container-based
- **Runners**: The compute that executes jobs — GitHub-hosted (ephemeral VMs) or self-hosted

**Runner architecture**:

GitHub-hosted runners are ephemeral VMs spun up per job and destroyed after completion. This has significant implications:

```yaml
# Each job gets a fresh VM — state does NOT persist between jobs
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4  # Must explicitly pass state between jobs
        with:
          name: dist
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4  # Retrieve what build produced
        with:
          name: dist
```

**Caching**: The `actions/cache` action uses a key-based content store. Cache keys typically include the OS, language version, and a hash of the dependency lockfile. Cache hits restore the directory; misses populate it after the job completes.

**Concurrency limits**: Workflows can configure concurrency groups to prevent redundant runs:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancel older run when newer push arrives
```

This is a real production pattern for preventing deploy races on busy repositories.

## System Design: Pull Request Notification System

A common GitHub system design question: design the notification system that powers pull request activity — reviewers get notified, watchers get updates, @mentions trigger targeted alerts, and nothing becomes spam.

**Scale parameters**:
- GitHub has millions of active pull requests daily
- A popular open source repository might have thousands of watchers
- Notification channels: web (bell icon), email, mobile push

**Core design decisions**:

**Subscription model, not broadcast**: Users should receive notifications based on their explicit or implicit subscription state — not because they happen to watch a noisy repository. Notification preferences are hierarchical: repository-level watching (all activity vs. participating only), issue/PR-level subscription, and @mention overrides.

**Fanout on write vs. fanout on read**: For a user with thousands of watchers, writing a notification to every subscriber on every comment would be expensive. GitHub's approach involves lazy fanout — notifications are written to a queue, and fan-out happens asynchronously:

```
Event: PR comment created
  → Write event to notification queue
  → Worker: compute subscriber list (watchers + participants + @mentions)
  → For each subscriber: apply notification preference filter
  → Write to per-user notification inbox
  → Async: send email digest / mobile push based on user preferences
```

**Deduplication**: A user watching a PR and @mentioned in the same comment should not receive two notifications. Dedup by (user_id, event_id) before delivery.

**Email digesting**: Sending an email per comment on a busy PR is a spam vector. Digest mode batches notifications within a time window (typically 10 minutes) into a single email thread, maintaining In-Reply-To headers so email clients thread them correctly.

**Muting and unsubscribing**: Any notification must carry a one-click unsubscribe. Marking a thread as "done" in the GitHub notifications UI should suppress future notifications for that thread until you are re-mentioned.

## Behavioral Questions

**"Tell me about a contribution you made to an open source project."**

*What they are really asking*: Do you actually participate in open source, or did you just write "passionate about open source" in your cover letter? GitHub employees are expected to have genuine relationships with the open source ecosystem.

STAR example: You found a bug in a library you used daily, traced it through the source, submitted a minimal reproduction issue, and then a pull request with a fix and a test. You engaged with maintainer feedback through two rounds of review. The fix shipped in the next minor version and closed three other issues that were duplicates of the same root cause.

**"Describe a time you collaborated effectively with a distributed team."**

*What they are really asking*: Can you work async? Can you write clearly? Can you make decisions without being in the same room?

STAR example: You were the only engineer in a European time zone on a team spread across North America and Asia. You established a pattern of writing detailed PRs with context, decision rationale, and explicit "questions for reviewers" sections. You pre-recorded short Loom walkthroughs for complex changes. Review cycles that used to require synchronous meetings dropped from 3 days to 6 hours.

**"Tell me about a developer tool you built or improved that genuinely made someone's workflow better."**

*What they are really asking*: Do you care about developer experience specifically? GitHub is a developer-tools company; they want engineers who feel what developers feel.

STAR example: You noticed your team spent 20 minutes per deploy manually verifying that staging matched production configuration. You built an internal tool that diffed the two environments and surfaced discrepancies in a PR comment automatically. Deploy incidents caused by configuration drift dropped to zero for that quarter.

## 4-Week Preparation Plan

**Week 1: Git internals**

Read "Pro Git" (free at git-scm.com) — specifically chapters 10 (Git Internals) and chapter 9 (Distributed Git). Implement a minimal Git in your language of choice: content-addressable blob storage, tree construction, and commit creation. Understanding how to write a commit object from scratch makes the conceptual model concrete.

**Week 2: Large-scale storage and CI/CD architecture**

Study content-addressable storage systems: read about how IPFS, Nix, and git-lfs approach large object storage. Review GitHub's engineering blog for their public writing on Gitaly (their Git RPC layer) and Actions infrastructure. Build a toy CI system: a workflow YAML parser that executes steps in a temporary directory and reports results.

**Week 3: Developer tools product sense and system design**

Practice the notification system design and similar problems: design GitHub's code search (how do you index 330M repositories?), design a merge queue for high-velocity monorepos, design the GitHub Packages registry. For each, anchor the design in developer experience — the user is an engineer; friction is the enemy.

**Week 4: Mock interviews and GitHub product deep dive**

Do three mock technical interviews with a partner or using a practice platform. Spend two hours on GitHub's own documentation — read the GitHub Actions documentation end to end, understand GitHub Packages, Codespaces, and Copilot's architecture at a surface level. Know what GitHub Copilot Enterprise is and how it differs from the individual plan.

## What Sets GitHub Candidates Apart

GitHub is a company where the product is the platform that developers use to build everything else. The engineers who get offers understand the recursive quality of that: working at GitHub means your tools are used to build your tools. The developers you are building for have extremely high expectations — they are professionals who will notice rough edges immediately.

The strongest candidates have a GitHub profile that tells a story — not just green squares on the contribution graph, but evidence of taste: clean repositories with thoughtful READMEs, open source contributions that show you can navigate an unfamiliar codebase, and projects that demonstrate you understand the problem you were solving.

Know GitHub Actions deeply. It is the product GitHub is betting its CI/CD future on, it is used internally for GitHub's own deploys, and it comes up in almost every technical conversation. If you cannot walk through a non-trivial workflow YAML and explain the concurrency, caching, and artifact behavior, spend another week on it before your onsite.

When you discuss your past work, frame it from the perspective of the developer using what you built. GitHub engineers care about the quality of the developer experience above almost everything else. A system that is technically correct but painful to use is a failed system at GitHub. A system that is slightly less optimal but a joy to operate is a success.
