# Platform Engineer Interview Guide 2024: Internal Developer Platforms and Infrastructure

Platform engineering has emerged as one of the most consequential roles in modern software organizations. Where DevOps asked developers to own operations and SREs focused on reliability, platform engineering takes a different approach entirely: build the infrastructure, tooling, and abstractions that make product engineers fast, safe, and autonomous. If you are interviewing for a platform engineering role in 2024, you need to understand this distinction deeply, because interviewers will probe whether you think like a product manager for internal customers or like a traditional ops person reacting to incidents.

This guide covers the full scope of what platform engineering interviews test, from conceptual framing through hands-on system design questions, and gives you the vocabulary and depth to answer confidently.

## Platform Engineering vs. DevOps vs. SRE: Getting the Framing Right

This question comes up in almost every platform engineering interview, often as an opening warm-up. Getting it wrong signals that you are applying for the job title rather than understanding the role.

**DevOps** is a cultural movement and set of practices. It broke down the wall between development and operations by asking developers to take ownership of their deployments, monitoring, and on-call. The goal was faster feedback loops. DevOps as a job title became muddled—it often describes someone who writes Jenkins pipelines and manages cloud infrastructure reactively.

**SRE (Site Reliability Engineering)** is Google's formalization of applying software engineering to operations problems. SREs focus on reliability: they define SLOs and SLIs, manage error budgets, respond to incidents, and build automation to reduce toil. SRE is inherently service-reliability-focused.

**Platform Engineering** is about building the Internal Developer Platform—the shared infrastructure, tooling, and workflows that product engineers use to build and ship their services. Platform engineers think in terms of developer experience, not operational reliability. They ask: "How do I make deploying a new service take ten minutes instead of two weeks?" They treat internal developers as customers, product-manage their platform roadmap, and measure success by developer productivity metrics, not incident counts.

The key insight interviewers want to see: platform engineers build products for internal users. That mental model changes everything about how you approach the work.

## Internal Developer Platforms: What They Actually Are

An Internal Developer Platform (IDP) is the collection of tools, services, and workflows that a platform team builds and maintains to enable product engineers to self-serve. A mature IDP typically includes:

- **Self-service infrastructure provisioning**: Engineers can create databases, queues, and compute resources through a UI or CLI without filing tickets
- **Standardized deployment pipelines**: Golden path CI/CD templates that handle security scanning, testing, and progressive rollout
- **Observability scaffolding**: Automatic integration with logging, metrics, and tracing when a new service is registered
- **Secret management**: Self-service access to Vault or cloud-native secret stores with appropriate access controls
- **Environment management**: On-demand preview environments, ephemeral staging environments, production promotion workflows
- **Developer portal**: A unified interface (often Backstage) where engineers can discover services, APIs, documentation, and runbooks

The distinction between an IDP and "just using Kubernetes" is the abstraction layer. Product engineers should not need to understand Kubernetes internals to deploy their service. The IDP exposes higher-level concepts—service, environment, deployment—and handles the orchestration underneath.

## Golden Paths: The Core Philosophy

A golden path is the recommended, well-supported way to do something on your platform. The term comes from Spotify's platform team, who coined it to describe their internal service templates and deployment workflows.

Golden paths are not mandates. Engineers can deviate from them, but deviating means accepting higher friction and less support. The platform team's job is to make the golden path so good that deviating from it is rarely worth the cost.

A well-designed golden path for a new microservice might include:
- A project scaffold that generates a repository with linting, testing, and CI configuration already wired up
- A Dockerfile following security best practices (non-root user, distroless base, minimal attack surface)
- A Helm chart template or Kubernetes manifest generator with resource limits, liveness probes, and pod disruption budgets pre-configured
- An onboarding script that registers the service in the developer portal, creates the monitoring dashboards, and provisions the initial secrets

The golden path concept comes up in interviews because it forces you to articulate a philosophy: you are not enforcing standards by locking things down; you are making the right thing the easy thing.

## Backstage: The Developer Portal Standard

Backstage, originally built by Spotify and now a CNCF project, has become the de facto standard for developer portals. If you are interviewing at a company large enough to have a platform team, there is a reasonable chance they use Backstage or are considering it.

**What Backstage does:**

Backstage is a service catalog and developer portal framework. Its core entity is the component—a service, library, website, or pipeline registered in a YAML manifest (catalog-info.yaml) checked into the source repository. The catalog gives you a searchable inventory of everything your organization runs, who owns it, what its dependencies are, and where its documentation lives.

Beyond the catalog, Backstage's plugin architecture allows platform teams to embed functionality directly into the portal: deploy triggers, Kubernetes resource views, cost attribution dashboards, on-call schedules, incident history, API documentation via Swagger or AsyncAPI.

**What interviewers expect you to know:**

You should understand the Software Catalog and TechDocs (Backstage's documentation system, which treats docs as code by building MkDocs sites from repository markdown). You should know that Backstage plugins come in two flavors—frontend React plugins and backend Node.js plugins—and that the plugin architecture is what makes Backstage extensible without becoming a monolith.

The critical operational insight: Backstage's value compounds over time as more services are cataloged and more workflows are embedded. The risk is catalog staleness—if engineers don't keep their catalog-info.yaml files up to date, the portal becomes untrustworthy. Good platform teams automate staleness detection and treat catalog hygiene as a first-class concern.

## Building Kubernetes Platforms: Operators, CRDs, and Admission Controllers

For platform engineering roles that involve Kubernetes deeply, you need to go beyond "I know how to write a Deployment manifest." Interviewers will probe your understanding of how to extend Kubernetes itself.

**Custom Resource Definitions (CRDs)** allow you to extend the Kubernetes API with your own resource types. Instead of exposing raw Deployments and Services to product engineers, you might create a `Service` CRD (with a capital S, distinct from the core Service type) that represents your organization's concept of a deployable service—including its SLO targets, team ownership, and scaling policy. Product engineers interact with your abstraction, not with Kubernetes primitives.

**Operators** are controllers that reconcile CRDs. An operator watches for changes to your custom resources and translates them into Kubernetes primitives. The controller pattern—observe desired state, compare to actual state, take action to converge—is fundamental to Kubernetes architecture and you should be able to explain it fluently. Operators are typically built with controller-runtime (Go) or operator-sdk.

**Admission controllers** are webhooks that intercept API requests before they are persisted. They come in two flavors:
- **Validating admission webhooks** reject requests that violate policy (a pod requesting more than 4 CPU cores, a deployment without resource limits, an image from a non-approved registry)
- **Mutating admission webhooks** modify requests before they are stored (injecting a sidecar container, adding required labels, setting default resource requests)

Platform teams use admission controllers to enforce security and operational standards without requiring product engineers to remember rules. You write the enforcement once; it applies everywhere automatically.

A design question you might get: "How would you prevent engineers from deploying container images that haven't passed your security scanning pipeline?" A strong answer uses a combination of admission controllers (validate that images come from an approved registry, which only receives images after scanning), image signing (Sigstore/Cosign), and policy engines like OPA Gatekeeper or Kyverno for richer policy logic.

## CI/CD Platform Design at Scale

Designing CI/CD infrastructure is a core platform engineering competency. You need to understand not just "how do GitHub Actions work" but how to design pipelines that are maintainable, secure, and performant at scale.

**Reusable workflows and shared actions** are the golden path for CI/CD. At scale, you cannot allow every team to write their own pipeline from scratch—you end up with hundreds of subtly different implementations, each with its own security gaps. Platform teams build reusable workflow templates (in GitHub Actions, these are called reusable workflows; in Jenkins, they are shared libraries; in Tekton, they are Tasks and Pipelines in a catalog).

**Tekton** is a Kubernetes-native CI/CD framework. It models pipelines as Kubernetes resources (Tasks, Pipelines, PipelineRuns), which gives you the full Kubernetes tooling ecosystem for observability, RBAC, and resource management. Tekton is cloud-native by design and integrates naturally with the rest of your Kubernetes platform. The trade-off versus GitHub Actions is that Tekton requires more infrastructure to operate but gives you more control and runs entirely on your infrastructure.

**Argo Workflows** is another Kubernetes-native workflow engine, more general-purpose than Tekton (not CI/CD-specific). It excels at complex DAG-shaped pipelines, data processing workflows, and multi-step ML training runs. Many platform teams use both: Tekton for CI/CD and Argo Workflows for data pipelines.

**Security considerations** interviewers probe: secret injection (never store secrets in environment variables in the pipeline definition; use Vault agent injection or cloud-native secret managers), OIDC token-based authentication (GitHub Actions supports OIDC federation with AWS/GCP, eliminating the need for long-lived credentials), and pipeline isolation (runners should be ephemeral—provisioned for one run and destroyed, preventing secret leakage across runs).

**GitOps** is the practice of using Git as the single source of truth for desired state, with an automated agent continuously reconciling actual state to match. The two dominant implementations are ArgoCD and Flux.

ArgoCD has a richer UI and application-centric model (applications are a first-class resource). Flux is more modular and Kubernetes-native in its approach, built around the Flux controllers that each handle a specific reconciliation concern (source, kustomize, helm). The interview question "ArgoCD vs Flux" rarely has a right answer—the right answer is understanding the trade-offs and which matters for the organization's context. ArgoCD's UI is often preferred in organizations with many teams who need visibility; Flux's modularity is preferred by teams who want to compose their GitOps setup from independent pieces.

## DORA Metrics: Measuring What Matters

The DevOps Research and Assessment (DORA) team's research identified four metrics that predict software delivery performance. Platform teams use these metrics both to measure their own effectiveness and to help product teams understand their delivery health.

**Deployment Frequency**: How often you deploy to production. Elite performers deploy multiple times per day. This metric captures how well your CI/CD pipeline, testing infrastructure, and deployment process support frequent releases. Platform engineers improve deployment frequency by reducing pipeline execution time, enabling feature flags for safe partial rollouts, and making rollbacks instant and reliable.

**Lead Time for Changes**: The time from code commit to production deployment. Elite: less than one hour. This measures end-to-end pipeline efficiency. Long lead times often indicate slow test suites, manual approval gates that could be automated, or deployment processes that require manual steps.

**Mean Time to Recovery (MTTR)**: How long it takes to restore service after an incident. Elite: less than one hour. This is where platform investments in observability (fast detection), progressive delivery (blast radius reduction), and automated rollback pay off. If your deployment system can automatically detect a bad deploy via SLO burn rate and rollback in under five minutes, your MTTR floor is very low.

**Change Failure Rate**: The percentage of deployments that cause degraded service or require remediation. Elite: 0–15%. Platform investments in testing infrastructure, integration testing environments, and canary deployments reduce change failure rate.

In interviews, expect to discuss how specific platform capabilities map to specific DORA metric improvements. "We built ephemeral preview environments for integration testing" → lower change failure rate. "We automated rollback triggered by SLO burn rate" → lower MTTR.

## Platform as a Product: The Mental Model Shift

This is the most important conceptual shift in platform engineering, and interviewers frequently probe whether you have genuinely internalized it.

Platform teams have internal customers: the product engineers. Treating the platform as a product means:

- Running user research: talking to engineers about their pain points, not guessing
- Maintaining a public roadmap that teams can see and influence
- Measuring adoption and satisfaction (developer NPS surveys, time-to-first-deploy for new engineers)
- Defining SLOs for the platform itself (the CI system should be available 99.9% of the time; pipeline execution should complete in under ten minutes at P95)
- Doing dogfooding: platform teams build their own services on the platform they maintain

The anti-pattern is "build it and they will come" platform development—building capabilities engineers didn't ask for, or building capabilities in isolation without feedback loops. Platform teams that operate this way often end up with a technically sophisticated platform that nobody uses, because it doesn't solve the right problems.

A question you might get: "How would you prioritize your platform roadmap for the next quarter?" The answer should include: talking to engineering teams to understand their biggest productivity blockers, looking at metrics (where are engineers spending time on non-product work?), considering security and compliance requirements as non-negotiables, and balancing quick wins (which build trust) against longer-term infrastructure investments.

## Technical Interview Topics and Design Questions

**Design a multi-tenant Kubernetes platform:**

Key axes of multi-tenancy are namespace isolation (each team gets namespaces), network policies (teams cannot reach each other's services by default), resource quotas (fair sharing of cluster capacity), RBAC (teams can only manage their own resources), and admission policies (enforced platform-wide). You need to decide where in the spectrum from "hard multi-tenancy" (separate clusters per team) to "soft multi-tenancy" (shared cluster with namespace isolation) to operate. The trade-offs are cost (separate clusters are expensive), operational overhead (more clusters to upgrade), and blast radius (a compromised namespace in a shared cluster is more dangerous than a compromised cluster in isolated tenancy).

**Design a self-service deployment system:**

Start from the user journey: an engineer merges a PR and their service is deployed to staging, then production, with appropriate safety mechanisms. Work backward through the layers: the IDP UI or CLI accepts a deployment trigger; the CI/CD pipeline builds, tests, and produces an artifact; a GitOps controller reconciles the artifact version to the staging environment; automated smoke tests run; a canary deployment to production starts at 5% traffic; SLO-based progressive traffic shifting continues if error rates are nominal; full production deployment completes. The platform team owns every layer of this path.

**Terraform module design:**

Good Terraform module design follows the principle of making the easy thing the safe thing. Module interfaces should expose business-level parameters (app_name, environment, instance_type_tier) rather than raw cloud parameters. The module handles naming conventions, tagging, security group rules, and encryption settings internally. Version pinning in module sources is critical for stability. A question interviewers probe: "How do you handle Terraform state in a multi-team environment?" The answer involves remote state (S3 + DynamoDB for AWS), state locking, per-environment state files, and RBAC on who can apply state changes.

## What Strong Candidates Demonstrate

Platform engineering interviewers are looking for engineers who can hold two perspectives simultaneously: the technical depth to build sophisticated distributed systems infrastructure, and the product thinking to understand why they are building it and whether it is solving the right problem. The best answers in platform engineering interviews connect technical decisions to developer experience outcomes: "We chose ArgoCD over Flux because our 80 product teams needed visibility into their deployment status without Kubernetes expertise, and ArgoCD's UI addressed that directly."

The role is ultimately about leverage—building things that make tens or hundreds of other engineers faster and safer. Demonstrating that you think about impact at that scale is what separates strong platform engineering candidates from infrastructure engineers who happen to know Kubernetes.
