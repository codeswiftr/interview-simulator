# GitHub Actions Engineering Deep Dive: CI/CD Infrastructure at GitHub Scale

GitHub Actions is the dominant CI/CD platform in the industry, and yet most engineers who use it daily have only a surface-level understanding of how it actually works. Knowing how the runner architecture operates, how the YAML is parsed and executed, how artifacts and caching are stored, and how secrets are secured is not just useful trivia — it changes how you design workflows, debug failures, and think about CI/CD in system design interviews.

## Runner Architecture: Ephemeral VMs at Scale

When you push a commit and a workflow triggers, GitHub's control plane must find or provision a compute resource to run your job. For GitHub-hosted runners, this means pulling a pre-baked VM image from a pool, assigning it to your job, and destroying it when the job completes.

The VM images are built and published weekly by the `actions/runner-images` repository. Each image is a snapshot of Ubuntu, Windows, or macOS with a curated set of pre-installed tools — compilers, language runtimes, Docker, common CLIs. The image is immutable during a job run. When your job finishes (success, failure, or cancellation), the VM is discarded entirely. There is no state left behind. This is the ephemeral guarantee that makes GitHub-hosted runners safe to share across organizations.

Self-hosted runners invert this model. You register a machine (physical or virtual, on-premises or cloud) with the GitHub Actions service. The runner process polls the GitHub API for job assignments over a long-lived HTTPS connection. When a job is assigned, the runner clones the repository, executes the steps, and reports results. The machine is not destroyed — it persists between jobs, which is both a capability (warm caches, private network access) and a risk (secret leakage, state accumulation between runs).

The runner process itself is open source (`actions/runner`). It speaks a REST-based protocol to the GitHub Actions service, receives job definitions as JSON, and executes steps in subprocess shells. Understanding this architecture is why certain things that seem like they should work do not: environment variables set in one step are not visible in a subsequent step unless you write them to `$GITHUB_ENV`, because each step runs in a fresh shell process.

## YAML Parsing, Job DAGs, and Expression Evaluation

A GitHub Actions workflow is a YAML file that describes a directed acyclic graph of jobs, where each job is a sequence of steps. The parsing happens on GitHub's control plane before any runner is involved.

Job dependencies are declared with `needs`. When you write `needs: [build, lint]`, the control plane builds a DAG where your job has edges from both `build` and `lint`. The runner for your job is not provisioned until all upstream jobs have completed. This DAG evaluation happens server-side — the runner only ever sees a single flattened job, not the full workflow graph.

Expression evaluation (`${{ }}` syntax) is a mini-language evaluated by the control plane. Contexts like `github`, `env`, `secrets`, and `needs` are resolved before the job definition is sent to the runner. This has a critical security implication: expressions evaluated in certain contexts can inject content into the shell command that follows. If you write `run: echo "${{ github.event.pull_request.title }}"` and the PR title contains shell metacharacters, you have a command injection vulnerability. The safe pattern is to pass untrusted input through environment variables, which are not shell-interpolated.

Matrix strategies are expanded at the YAML parsing layer. A 3x3 matrix produces 9 job instances, each receiving their own runner. The control plane is responsible for fan-out, collecting results, and applying `fail-fast` semantics if any matrix job fails.

## Artifact Storage and Caching

Artifacts and caches both use GitHub's artifact storage service, which is backed by Azure Blob Storage. The difference is their lifecycle and purpose.

Artifacts persist after the workflow completes and can be downloaded by humans or other workflows. They are uploaded via the `actions/upload-artifact` action, which tarballs the specified path, streams it to the storage service, and records a pointer in the workflow run's metadata. Retention defaults to 90 days.

Caches are scoped to the repository and branch, and their purpose is to speed up future runs. The `actions/cache` action computes a cache key from a hash of specified files (typically lock files like `package-lock.json` or `go.sum`), checks for a hit at the start of the job, and saves the cache at the end if it was a miss. Cache keys support a fallback chain with `restore-keys`, so a partial cache hit can still accelerate the build even when the exact key is missing.

Cache storage is capped per repository (10 GB by default). When the limit is reached, the least-recently-used caches are evicted. This means very large caches — gigabyte-scale node_modules or build outputs — can evict each other in a thrash loop if multiple branches are active. The mitigation is to include the branch name in the cache key for branch-specific artifacts.

## Secret Management and OIDC Token Federation

Secrets stored in GitHub Actions settings are encrypted at rest and injected into the runner environment at job start. They are automatically redacted from logs — any string matching a secret value is replaced with `***`. This redaction is best-effort: base64-encoded secrets or secrets embedded in larger strings may not be caught.

The traditional model of storing long-lived cloud credentials as GitHub secrets is being replaced by OIDC token federation. Instead of storing an AWS access key or GCP service account key, you configure the cloud provider to trust GitHub's OIDC token issuer. At job start, the runner requests a short-lived OIDC token signed by GitHub, exchanges it with the cloud provider for temporary credentials, and those credentials expire when the job ends.

This eliminates the secret rotation problem, eliminates the risk of secret leakage persisting after a key is revoked, and enables fine-grained policies: the cloud provider can inspect the token's claims (repository, branch, environment) and issue credentials with only the permissions appropriate for that specific workflow.

## Interview Implications

In a system design context, GitHub Actions is a useful reference for how to build a large-scale job execution platform. The interesting engineering problems are runner provisioning and scheduling (how do you minimize queue time while controlling cost), artifact storage at scale (how do you handle millions of small uploads efficiently), cache invalidation across concurrent branches, and the security boundary between untrusted workflow code and the host environment.

When these topics come up, the depth that separates candidates is whether they can speak to failure modes: what happens when a runner loses connectivity mid-job, how do you prevent resource exhaustion when a workflow has a bug that creates an infinite loop of triggered workflows, and how do you design the YAML expression evaluator to be safe against injection attacks. Those are the questions that reveal whether you understand the system or just its interface.
