---
title: "Monorepo Engineering Interview: Turborepo, Nx, and Large-Scale Code Organization"
description: "Monorepo interview guide for platform and DX engineers — monorepo vs polyrepo trade-offs, build tools (Turborepo, Nx, Bazel), remote caching, affected builds, and code sharing patterns."
date: "2026-03-20"
category: "Technical Skills"
---

# Monorepo Engineering Interview: Turborepo, Nx, and Large-Scale Code Organization

Monorepo engineering questions appear in platform engineer, developer experience engineer, and senior frontend architect interviews. They test whether you understand the organizational and technical trade-offs of large-scale code organization — a genuinely hard problem that affects engineering velocity at scale.

## Monorepo vs Polyrepo: The Real Trade-offs

**Monorepo:** All related code in a single repository. Teams work in separate directories within one repo.

**Polyrepo:** Each team/service/library has its own repository.

The trade-off isn't "monorepo is better" or "polyrepo is better" — it depends on organizational scale, tooling maturity, and release coupling.

**Monorepo advantages:**
- **Atomic cross-repo changes:** Update a shared library and all consumers in one PR. No coordinated multi-repo PRs.
- **Visibility:** Easier to understand system-wide impact of changes. `git log` and code search work across everything.
- **Tooling consistency:** Single CI/CD pipeline, linting config, testing framework.
- **Refactoring:** Rename a function across all callers in one operation.

**Monorepo disadvantages:**
- **CI/CD scale:** Running all tests on every commit is unsustainable at large scale. Requires sophisticated build tools for affected-only builds.
- **Access control:** Coarser-grained permissions. Harder to restrict who can see what.
- **Repository size:** `git clone` time grows. Sparse checkout and virtual filesystems (Microsoft's VFSForGit/GVFS, Meta's EdenFS) are needed at extreme scale.
- **Cognitive overhead:** Harder to reason about blast radius of changes when everything is visible.

**Who uses monorepos:** Google (the original Blaze/Bazel monorepo at massive scale), Meta (similar scale), Microsoft, Uber, Airbnb, Stripe. Also many modern JavaScript projects (Next.js, Remix, React).

**Who uses polyrepo:** Most microservices architectures default here because service independence is a core value.

**The hybrid:** Many organizations run "workspaced monorepos" — a monorepo per product area or domain, with polyrepo between domains.

## Build System Tools

**Turborepo:**
- Designed for JavaScript/TypeScript workspaces (npm/yarn/pnpm workspaces)
- Remote caching: computationally identical tasks return cached results from the cloud (Vercel's cache or self-hosted)
- Task graph: runs tasks in parallel where dependencies allow
- Pruned builds: only builds packages needed for a given workspace

```json
// turbo.json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],  // ^ means run parent's build first
      "outputs": [".next/**", "dist/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "inputs": ["src/**/*.ts", "test/**/*.ts"]
    }
  }
}
```

**Nx:**
- More opinionated, language-agnostic (JS, Go, Java, Python)
- First-class support for affected commands: `nx affected --target=build` only builds packages touched by your PR
- Nx Cloud for remote caching
- Strong plugin ecosystem (React, Next.js, NestJS, Storybook)

**Bazel (Pants, Buck2):**
- The heavy-duty option. Hermetic builds — identical inputs always produce identical outputs, regardless of machine.
- Language-agnostic with good polyglot support
- Complex learning curve but massive CI/CD speedup at scale
- Used by Google, Meta, Uber at extreme scale

## Remote Caching Architecture

The key insight: most CI tasks produce deterministic outputs given identical inputs. Cache the output keyed by a hash of the inputs, and you never redo work.

**Cache key construction:**
- Source files hashed
- Environment variables (Node version, etc.)
- Dependencies (package.json lockfile)
- Task configuration

**Cache storage:** Vercel Remote Cache (Turborepo), Nx Cloud, custom S3 bucket with cache server.

**Cache hit rates in practice:** Well-tuned monorepos see 70-90% remote cache hit rates in CI, dramatically reducing build times. First build after a major change is slower; incremental builds are fast.

## Affected Builds

The core CI optimization: only run tests/builds for packages affected by the PR.

**How "affected" is computed:**
1. Compare changed files in the PR to the base branch
2. Build the dependency graph (which packages depend on which)
3. Mark all packages with changed files as affected
4. Transitively mark all packages that depend on affected packages

```bash
# Nx affected
nx affected --target=test --base=origin/main

# Turborepo filter
turbo run test --filter=...[origin/main]
```

**Interview Q: What's the blast radius problem in affected builds?**
If you change a foundational shared library used by 80 packages, "affected" means running 80 test suites. The solution: maintain a well-factored dependency graph, avoid circular dependencies, and split frequently-changed utilities from rarely-changed foundational packages.

## Code Sharing Patterns

**Internal packages:** Shared code lives in `packages/` or `libs/` directory. Consumed via npm workspace protocols (`"my-lib": "workspace:*"`).

**Feature flags:** Shared configuration often lives in a monorepo. Feature flag evaluator code shared across apps.

**Generated code:** Types from API schemas (OpenAPI, Protobuf), database query types. In a monorepo, regenerate in one place, all consumers update atomically.

**Version pinning vs workspace protocol:** Some teams pin internal package versions (more control, more churn) vs using workspace protocol (always current, risk of breaking changes).

## Common Interview Questions

**Q: We have 50 engineers in a JavaScript monorepo. CI takes 45 minutes. How do you fix it?**
Diagnosis first: profile what takes the longest. Likely answer: enable remote caching (Turborepo or Nx Cloud), configure affected-only builds, parallelize test runs across CI workers (e.g., 10 workers each running a shard of affected tests), optimize slow test suites. Typical result: 45 min → 8-12 min for most PRs.

**Q: When would you split a monorepo back into polyrepo?**
When: services are being open-sourced (can't expose internal code), different teams need truly independent release cycles and the coupling benefits don't outweigh the overhead, security requirements demand strong repo-level isolation, or the monorepo has grown to a size where build tools can no longer adequately optimize (this threshold is extremely high — billions of lines of code).
