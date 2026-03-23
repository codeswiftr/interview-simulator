---
title: "Platform Engineering Interview: Internal Developer Platforms and Golden Paths"
description: "Comprehensive guide to platform engineering interviews covering internal developer portals, golden paths, DORA metrics, and the distinction between platform engineering, DevOps, and SRE."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# Platform Engineering Interview: Internal Developer Platforms and Golden Paths

Platform engineering has emerged as a distinct discipline from DevOps and SRE, with dedicated roles at companies from mid-stage startups to hyperscalers. Where DevOps focuses on culture and SRE focuses on reliability, platform engineering focuses on *developer productivity at scale* — building the internal tools and abstractions that let hundreds of product teams ship without drowning in infrastructure complexity. Interviews in this space test a unique blend of systems thinking, product sensibility, and deep technical knowledge.

## Platform Engineering vs DevOps vs SRE

Interviewers almost always open with this distinction because many candidates conflate the three roles. A precise answer matters.

**DevOps** is a cultural and organizational movement emphasizing shared ownership of the delivery pipeline between development and operations. A "DevOps engineer" in practice often means someone who writes CI/CD pipelines and manages cloud infrastructure — the role is defined by tooling rather than a product.

**SRE (Site Reliability Engineering)** is Google's formalization of operations as a software engineering problem. SREs focus on availability, latency, and toil reduction. Their primary artifacts are SLOs, error budgets, and runbooks.

**Platform engineering** treats internal developers as customers and builds a product for them: an Internal Developer Platform (IDP). The platform team owns the abstractions between product teams and infrastructure — Kubernetes operators, deployment templates, secret management, environment provisioning — and exposes them through a self-service portal. The key word is *self-service*: the platform succeeds when teams can deploy to production without filing a ticket with the platform team.

## Internal Developer Portals and Backstage

**Backstage**, open-sourced by Spotify in 2020, is the dominant framework for building internal developer portals. Understanding it deeply is expected for senior platform engineering roles.

Backstage's core is a **software catalog** — a YAML-defined registry of all services, libraries, APIs, and infrastructure components in the organization. Each entity has an owner, lifecycle stage, dependencies, and links to documentation, CI/CD dashboards, and runbooks. The catalog solves the "where does this service live?" problem that plagues organizations with hundreds of microservices.

The plugin architecture extends the catalog with capabilities: the Kubernetes plugin surfaces pod health; the PagerDuty plugin shows incident status; the TechDocs plugin renders markdown documentation from the service's own repository. Platform engineers spend significant time writing and maintaining plugins.

**Software templates** (Scaffolder) are the other critical Backstage feature. Templates define golden paths — opinionated starting points for new services that include the right CI/CD configuration, observability setup, secret management patterns, and compliance hooks baked in from day one. When a developer creates a new microservice through the portal, they get a repository with a working pipeline rather than a blank slate.

## Golden Paths

The golden path concept deserves its own emphasis. A golden path is the recommended, supported way to do something in your organization. It's not the *only* way — developers can deviate — but it's the path that's maintained, documented, and automatically compliant with security and operational requirements.

Effective golden paths reduce cognitive overhead. A new engineer shouldn't need to understand Kubernetes networking, Vault secret injection, and Datadog instrumentation to ship their first service. They should be able to follow a template that handles all of it.

Interview questions on golden paths often take the form of scenarios: "Product teams keep using different logging formats, making log aggregation painful. How would you address this with a platform approach?" The answer involves an opinionated logging library published as a golden path dependency, integrated into the service template, with documentation explaining why it was chosen — not a policy document mandating compliance.

## Platform KPIs and DORA Metrics

Platform teams are evaluated on developer productivity outcomes, not infrastructure uptime alone. The **DORA metrics** (from the DevOps Research and Assessment program) are the standard framework:

- **Deployment Frequency**: how often teams deploy to production
- **Lead Time for Changes**: time from code commit to production deployment
- **Change Failure Rate**: percentage of deployments causing production incidents
- **Mean Time to Restore (MTTR)**: time to recover from production failures

Strong candidates can explain how platform investments move these metrics. Self-service environment provisioning reduces lead time. Standardized rollout strategies with automatic canary analysis reduce change failure rate. Runbook templates and incident tooling reduce MTTR.

Additional platform-specific metrics include **portal adoption rate** (percentage of teams using the IDP), **ticket deflection rate** (support requests avoided because teams self-served), and **time to first deployment for new services**.

## What Platform Engineering Interviews Test

Technical rounds typically include: designing an internal developer portal from scratch, debugging a broken CI/CD pipeline, explaining Kubernetes admission controllers and their role in platform policy enforcement, and discussing infrastructure-as-code patterns (Terraform modules, Crossplane, Pulumi components).

Behavioral rounds focus on: how you've handled teams resisting platform adoption, how you prioritize the platform roadmap when every product team has different needs, and how you measure success when your customers are internal.

**Sample questions with strong answer patterns:**

"How do you get engineers to actually use your platform?" — The answer centers on reducing friction below the point of rolling your own, providing exceptional documentation, and embedding platform advocates within product teams rather than waiting for adoption to happen organically.

"What's the difference between a platform and a shared service?" — A shared service is consumed as-is; a platform provides building blocks that teams compose. Kubernetes is a platform; a managed Postgres cluster is a shared service.

Platform engineering interviews reward candidates who think like product managers about their internal customers while maintaining the systems depth to build reliable infrastructure at scale.
