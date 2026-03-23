---
title: "GitHub Code Review System Architecture"
description: "How GitHub's pull request and code review system works—diff generation, inline comments, review state machines, CI integration, and the infrastructure supporting 100M developers."
date: "2026-03-21"
category: "System Design"
---

# GitHub Code Review System Architecture

GitHub hosts 100 million developers and processes millions of pull requests daily. The code review system—diffs, inline comments, review approvals, CI integration—is a complex distributed application built on top of Git's content-addressable storage model.

## Requirements

**Functional:**
- Create pull requests (branch comparison with diff view)
- Inline comments on specific lines
- Review states: approve, request changes, comment
- Suggested changes (editable inline patches)
- CI/CD status checks integration
- Merge strategies: merge commit, squash, rebase

**Non-functional:**
- Diff generation < 3 seconds for files up to 10K lines
- Support repos with 1M+ commits (Linux kernel, React)
- Handle large PRs (1,000 changed files, 50,000 changed lines)
- Consistent view: all reviewers see the same diff

## Git as the Foundation

Git's model is perfect for code review:
- Every commit is a content-addressed SHA1/SHA256 hash
- Diff = comparing two tree objects
- PR = proposal to merge `feature_branch` into `main`

The PR stores: `{head_sha, base_sha, repo_id}`. The diff is computed on-demand from these two commits.

## Diff Generation

Computing a diff between two commits:

```python
def compute_diff(repo, base_sha, head_sha):
    base_tree = repo.get_commit(base_sha).tree
    head_tree = repo.get_commit(head_sha).tree

    changed_files = compare_trees(base_tree, head_tree)
    for file in changed_files:
        base_blob = base_tree.get(file.path)
        head_blob = head_tree.get(file.path)
        yield generate_file_diff(base_blob, head_blob)
```

File-level diff uses Myers diff algorithm (optimized for programmer diffs — prefers contiguous hunks). Output is unified diff format.

**Large file handling**: Files > 10K lines skip syntax highlighting and show raw diffs. Files > 50K lines display a "file too large" message. Binary files get a change summary only.

**Caching**: Diffs are computationally expensive. Cache the diff for a given `(base_sha, head_sha)` pair. The key is deterministic—same two commits always produce the same diff. Invalidate only when the PR's base branch advances (rebase scenario).

## Inline Comment Data Model

Inline comments are attached to specific positions in a diff. The tricky part: the diff changes as new commits are pushed.

GitHub's approach: store comments with both position in the diff and the absolute line number in the head commit.

```sql
CREATE TABLE pr_comments (
    comment_id     BIGINT PRIMARY KEY,
    pr_id          BIGINT,
    commit_sha     VARCHAR(40),   -- which commit was the file at
    file_path      TEXT,
    diff_line_pos  INT,           -- position in the unified diff
    original_line  INT,           -- line in the file at commit_sha
    body           TEXT,
    author_id      BIGINT,
    is_outdated    BOOLEAN,       -- diff changed since comment was made
    created_at     TIMESTAMP
);
```

When a new commit is pushed to the PR, GitHub re-maps comment positions. If the commented line hasn't changed, the comment stays visible inline. If the file changed around the comment, it's marked "outdated" and collapsed.

**Position tracking algorithm**: Apply the new commit's diff as a transformation to existing comment positions. Lines above the comment shift its line number; if the commented line itself changes, mark outdated.

## Review State Machine

A PR review has a state machine:

```
PENDING → COMMENTED → APPROVED
                    ↓
             CHANGES_REQUESTED
```

States per reviewer, not per PR. The PR is "approved" when N required reviewers have approved and no blocking "Changes Requested" reviews exist (or all blocking reviews have been dismissed).

```python
def can_merge(pr):
    required_count = pr.branch_protection.required_approvals
    approvals = [r for r in pr.reviews if r.state == 'APPROVED']
    blocking = [r for r in pr.reviews if r.state == 'CHANGES_REQUESTED']
    return len(approvals) >= required_count and len(blocking) == 0
```

Dismissing a review invalidates it: creates a new event, moves review back to DISMISSED state.

## CI Status Checks

Pull requests integrate with CI systems via the Checks API:
- CI creates a Check Run: `{pr_id, check_name, status, conclusion}`
- GitHub displays pass/fail status on the PR
- Branch protection can require specific checks to pass before merge

The Checks API is webhook-driven:
1. PR opened → GitHub sends `pull_request` webhook to CI (GitHub Actions, CircleCI, etc.)
2. CI runs tests, posts back Check Run status via API
3. GitHub updates PR merge button (green checkmark vs red X)

For GitHub Actions specifically, the workflow runs on GitHub's compute infrastructure, eliminating the webhook round-trip.

## Merge Implementation

Three strategies:

**Merge commit**: Creates a new commit with two parents (head + base). Preserves full history. `git merge --no-ff`

**Squash merge**: Combines all PR commits into a single new commit on base. Clean linear history. Loses individual commit history. `git merge --squash`

**Rebase**: Replays PR commits on top of current base HEAD. Linear history, preserves individual commits. Most complex — each commit is rewritten (new SHA). `git rebase --onto base_sha`

These operations run on dedicated Git servers (git service layer), not the web server. GitHub executes actual Git commands in a locked repository context to prevent concurrent modification.

## Conflict Detection

Before merge, check for conflicts:
1. Attempt a dry-run merge in a scratch clone of the repo
2. If conflict markers appear, mark PR as "Has Conflicts"
3. Show which files conflict in the PR UI
4. Resolution: user must either rebase locally or use web editor

Conflict detection is cached per `(head_sha, base_sha)`. Re-checked when either branch advances.

## Large PR Handling

PRs with 1,000+ changed files:
- Load file list lazily (infinite scroll in UI)
- Don't compute all file diffs simultaneously — compute on scroll/expand
- Diff summary stats (insertions, deletions) computed from Git summary, not full diff parse
- For CI: apply stricter timeouts, parallelize test splitting

## Interview Tips

The most interesting aspects to cover:

1. **Diff caching by (base_sha, head_sha)** — content-addressable Git objects make this deterministic
2. **Inline comment position tracking across commits** — the outdated comment problem
3. **Review state machine** — multi-reviewer approval logic
4. **Merge operations on dedicated Git servers** — not on API servers
5. **Conflict detection as a dry-run merge** — simple implementation, cache the result

This question pairs well with asking about large monorepo challenges (a GitHub specialty given they host the Linux kernel, Kubernetes, etc.) — be ready to discuss scaling to millions of commits.
