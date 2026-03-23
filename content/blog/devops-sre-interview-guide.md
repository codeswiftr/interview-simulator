# DevOps / SRE Interview Guide 2024: What's Actually Tested

Site Reliability Engineering and DevOps roles require a fundamentally different interview preparation than general software engineering. The coding problems are often simpler, but the systems knowledge, operational thinking, and automation depth go much further. Here's what to expect and how to prepare.

## DevOps vs. SRE: What's the Difference?

**SRE (Site Reliability Engineering)** — originated at Google. SREs are software engineers who solve operations problems: reliability, scalability, incident response. They write a lot of code, set error budgets, and own the reliability of large-scale systems. Coding bar is higher at SRE-specific roles.

**DevOps Engineering** — broader scope: CI/CD pipelines, infrastructure-as-code, container orchestration, monitoring/observability, developer productivity. More tooling-focused, less pure engineering.

In practice, many companies use these titles interchangeably. Read the job description carefully — some "DevOps" roles are essentially SRE; some "SRE" roles are mostly Kubernetes administration.

## Interview Format

**SRE (Google/Spotify/Netflix style):**
- 1-2 coding rounds (LeetCode medium + scripting)
- 1-2 system design / reliability design rounds
- 1 troubleshooting/debugging round
- 1 behavioral round

**DevOps/Platform Engineering (typical startup/scaleup):**
- 1 practical exercise (CI/CD pipeline, Terraform IaC, Kubernetes debugging)
- 1 system design / infrastructure architecture
- 1 behavioral + culture round
- Sometimes: live debugging session on a broken environment

## Coding Rounds

SRE coding rounds are LeetCode easy-to-medium, but with heavy emphasis on **scripting and automation problems**. DevOps roles may skip algorithmic coding entirely in favor of practical exercises.

**What's tested:**
- String parsing and log processing
- File system operations
- Network programming (sockets, HTTP clients)
- Process management and signaling
- Regular expressions
- Data aggregation on command-line-style problems

**Common scripting problems:**

*Log parsing:*
```python
# Given an nginx access log, count requests by status code and find top 10 IPs by request count
import re
from collections import defaultdict

def analyze_logs(log_file: str):
    status_counts = defaultdict(int)
    ip_counts = defaultdict(int)
    pattern = r'(\S+) .* HTTP/\S+" (\d+)'

    with open(log_file) as f:
        for line in f:
            if m := re.match(pattern, line):
                ip, status = m.groups()
                status_counts[status] += 1
                ip_counts[ip] += 1

    top_ips = sorted(ip_counts, key=ip_counts.get, reverse=True)[:10]
    return status_counts, top_ips
```

*Retry with backoff:*
```python
import time
import random

def retry_with_backoff(fn, max_attempts=5, base_delay=1.0):
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

*Rate limiter (Token Bucket):* — also common in SRE coding rounds. See Backend Engineer Guide for full implementation.

**Bash/shell scripting:** Many DevOps interviews include a shell scripting question. Practice:
- `awk`, `sed` for log parsing
- `xargs`, `parallel` for batch operations
- `jq` for JSON processing
- Shell arithmetic and string manipulation

## Infrastructure and Tools Knowledge

This is where DevOps/SRE interviews differ most from SWE. You need operational depth.

### Kubernetes

Must-know concepts:
- **Pod lifecycle**: Pending → Running → Succeeded/Failed; restartPolicy behaviors
- **Services**: ClusterIP (internal), NodePort, LoadBalancer; why DNS round-robin isn't load balancing
- **Deployments**: Rolling updates (`maxSurge`, `maxUnavailable`); rollback with `kubectl rollout undo`
- **Resource limits**: `requests` vs. `limits`; what happens when a container exceeds `limits.memory` (OOMKilled)
- **Health probes**: `livenessProbe` (kill and restart if failing), `readinessProbe` (remove from service endpoints)
- **ConfigMaps and Secrets**: How they mount into pods; why Secrets should use external secret management (Vault, AWS Secrets Manager)

**Common debugging scenarios:**
- Pod stuck in `CrashLoopBackOff` → `kubectl logs --previous`, check exit codes
- Service not responding → `kubectl exec` into pod, `curl` the service directly (bypass DNS), check endpoints
- Deployment not rolling out → `kubectl rollout status`, check resource constraints, image pull errors

### Terraform / Infrastructure as Code

Know the lifecycle: `init` → `plan` → `apply`. Key concepts:
- **State**: Remote state (S3 + DynamoDB lock) prevents concurrent modifications
- **Modules**: DRY principle for reusable infrastructure components
- **`depends_on`**: Explicit dependency when Terraform can't infer
- **`lifecycle { prevent_destroy }`**: Guard against accidental database deletion
- **Data sources**: Reference existing infrastructure (existing VPC, current AMI)

Practical question: "Walk me through how you'd Terraform a new AWS environment including VPC, private/public subnets, EKS cluster, and RDS."

### CI/CD Pipelines

Understand the pipeline stages: lint → test → build → security scan → deploy → smoke test → rollback-if-fail.

**Deployment strategies** (interviewers love these):
- **Blue/Green**: Run old and new environments in parallel; switch traffic atomically; easy rollback (cost: double infrastructure during transition)
- **Canary**: Route 5% → 25% → 100% gradually; rollback if error rate spikes (most production-safe for user-facing services)
- **Rolling**: Replace instances one by one; reduced cost but harder rollback mid-deploy

**Feature flags**: Decouple deployment from feature release. Ship dark, enable progressively per user cohort.

### Monitoring and Observability

The **three pillars**: Metrics (Prometheus/Datadog), Logs (ELK/Loki), Traces (Jaeger/Tempo/X-Ray).

**The USE method** for resource analysis:
- Utilization: % of time resource is busy
- Saturation: work queue depth
- Errors: error rate

**The RED method** for services:
- Rate: requests per second
- Errors: error rate
- Duration: latency distribution

**Alerting principles:**
- Alert on symptoms, not causes (high error rate → alert; high CPU → probably don't alert unless it causes symptoms)
- SLO-based alerting: burn rate alerts catch slow-burn degradation better than threshold alerts
- Avoid alert fatigue: each alert must be actionable

## System Design: Reliability Focus

SRE/DevOps system design rounds emphasize reliability, not just functionality.

**Common questions:**
- Design a monitoring and alerting system
- Design a CI/CD pipeline for 100 microservices
- Design a disaster recovery strategy for a stateful service
- Design a deployment system that handles database migrations safely
- Design on-call rotation + incident response workflow

**Reliability framework:**

**SLOs and error budgets:**
SLO = the target availability (e.g., 99.9% = 43 minutes downtime/month allowed). Error budget = how much you can burn on risky changes. When error budget is exhausted, freeze deployments until it replenishes.

**Blast radius reduction:**
- Feature flags to disable problematic features without redeploy
- Circuit breakers to prevent cascade failures
- Bulkheads to isolate failures to one service

**Runbooks:**
For every alert, there should be a runbook: what it means, what to check first, common causes, how to remediate. Interviewers ask how you operationalize systems.

**Worked example: CI/CD for 100 microservices**

- Monorepo vs. polyrepo: Monorepo (Bazel/Nx for incremental builds) avoids dependency hell; polyrepo gives team autonomy
- Trunk-based development: Short-lived branches, frequent merges to main; feature flags instead of long feature branches
- Pipeline stages: lint → unit test → integration test → build Docker image → push to registry → deploy to staging → smoke test → canary → promote to prod
- Deployment orchestration: ArgoCD (GitOps) — desired state in Git, ArgoCD reconciles cluster state; every prod change is a Git commit
- Rollback: `git revert` + re-deploy, or ArgoCD app rollback to previous sync
- Database migrations: Schema changes forward-compatible with both old and new code; deploy new code before running migration; never rename columns (add, copy, deprecate old)

## The SRE Troubleshooting Round

Some companies run a live debugging round: they give you a broken environment and watch how you diagnose it.

**Your approach:**
1. **Define the problem**: What should be happening vs. what is?
2. **Gather data**: Logs, metrics, recent deployments, changes in the past 24h
3. **Hypothesis → Test**: "I think it's X because Y. Let me verify by checking Z."
4. **Communicate**: Think aloud. SRE interviews reward structured thinking.

**Common scenarios:**
- Service returning 502 → check upstream health, LoadBalancer target group health, pod readiness probes
- Latency spike → check CPU/memory saturation, DB slow queries, external dependencies, recent deploys
- Pod OOMKilled → check memory limits, heap dumps, memory leak in application
- CrashLoopBackOff → `kubectl logs --previous`, check exit codes, config/secret mounting issues

## Behavioral: The SRE/DevOps Lens

**"Tell me about a production incident you led or participated in."**
Walk through: detection (how did you find out?), diagnosis (what was your process?), remediation (how did you fix it?), post-mortem (blameless, 5-whys, systemic changes).

**"How do you decide what to monitor and alert on?"**
They want: SLO-based thinking, symptom vs. cause alerting, alert fatigue awareness.

**"Tell me about a time you improved developer productivity."**
They want: platform thinking, multiplier impact, building self-service tools rather than being a bottleneck.

**"What's your philosophy on on-call?"**
They want: sustainable rotations, runbook culture, reducing toil, escalation protocols.

## Preparation Timeline

**Week 1: Scripting + Tools**
- Write 10 log-parsing scripts in Python and bash
- Set up a local Kubernetes cluster (minikube or k3d), deploy and debug a broken app
- Write a Terraform module for a simple AWS resource

**Week 2: System design + reliability**
- Design a monitoring system and CI/CD pipeline
- Study SLOs, error budgets, burn rate alerts
- Read Google's SRE book (free at sre.google)

**Week 3: Troubleshooting + behavioral**
- Practice 5 incident diagnosis scenarios
- Write STAR stories for incident response, productivity improvement, on-call sustainability
- Review Kubernetes debugging cheat sheet

## The One Differentiator

The SREs and DevOps engineers who land offers share one trait: **they optimize for the whole system, not their component**. They don't just make their pipeline faster — they make every team's deployments safer. They don't just fix the current incident — they make the next one faster to detect and cheaper to resolve.

This systems-level thinking — treating the engineering organization as the system you're operating — is what separates a good SRE from a great one. Show it in every answer.
