---
title: "Advanced DevOps Interview Guide: CI/CD, Infrastructure, and Platform Engineering"
description: "Deep-dive DevOps interview preparation — CI/CD pipeline design, GitOps, infrastructure as code, container orchestration, and platform engineering patterns."
date: "2026-03-20"
category: "DevOps"
---

# Advanced DevOps Interview Guide: CI/CD, Infrastructure, and Platform Engineering

Senior DevOps interviews have evolved beyond "do you know Jenkins and Ansible." Modern interviews probe your ability to design reliable delivery systems, reason about organizational scaling, and build platforms that other engineering teams can use without constant support. This guide covers the advanced topics that separate senior candidates from mid-level ones.

## CI/CD Pipeline Design

Interviewers will frequently ask you to design a CI/CD pipeline from scratch or critique one they describe. The depth of this question reveals whether you think about pipelines as configuration or as engineered systems.

A robust pipeline design covers: source triggers and branch strategies, build isolation (containerized builds prevent environment drift), artifact management (immutable artifacts versioned by commit SHA), test stages ordered by speed and cost (unit first, integration second, E2E last), security scanning integration (SAST, dependency vulnerability checks), and deployment gates with automated rollback.

Know the difference between continuous delivery (code is always releasable, deployment is a manual decision) and continuous deployment (every passing build deploys to production automatically). Be able to articulate when each is appropriate and what organizational maturity they require.

Pipeline performance matters at scale. Discuss parallelism (test splitting, fan-out stages), caching strategies (build caches, dependency caches), and how you'd diagnose a pipeline that's grown from 5 minutes to 45 minutes.

## GitOps Workflow

GitOps treats Git as the single source of truth for both application code and infrastructure configuration. Interviewers at companies running Kubernetes often ask about this pattern in depth.

The core loop: a change is merged to the desired-state repository, a GitOps operator (ArgoCD, Flux) detects the diff between desired state and actual cluster state, and reconciles by applying the changes. This gives you a complete audit log (git history), easy rollbacks (revert the commit), and eliminates configuration drift.

Be able to discuss the two-repo pattern (application code repo separate from config/manifest repo), why it matters for security and access control, and how you'd structure environments (overlays in Kustomize, values files in Helm) within a GitOps model.

Common interview challenge: "Your GitOps sync keeps failing — walk me through how you'd diagnose it." Discuss checking operator logs, verifying RBAC permissions, looking for resource conflicts, and distinguishing sync errors from health errors.

## Infrastructure as Code Principles

IaC questions at senior level go beyond syntax. Interviewers want to see how you structure IaC at scale, handle drift, and make it safe for teams to collaborate on.

Key principles: declarative over imperative (describe desired state, not the steps to get there), idempotency (running the same code twice produces the same result), modularity (reusable components with clear interfaces), and version control with code review for all changes.

Module design is a frequent deep-dive. A good module has a single responsibility, a stable interface with sensible defaults, input validation, and outputs that downstream modules can consume. Know the difference between a module you'd publish to a registry (very stable interface, thorough documentation) and an internal module (can evolve faster, tighter coupling acceptable).

Testing IaC is an area many candidates overlook. Know the testing pyramid for IaC: static analysis (linting, security scanning with tfsec/checkov), unit tests (mocking provider calls with tools like Terratest), and integration tests (actually creating real resources in an isolated environment).

## Container Orchestration

Even for DevOps roles that aren't purely Kubernetes-focused, container orchestration knowledge is expected. Interviewers test both depth (Kubernetes internals) and breadth (how orchestration fits in a delivery system).

Know the Kubernetes control plane components and their roles: API server (single entry point), etcd (cluster state), scheduler (pod placement), controller manager (reconciliation loops). Understand the data plane: kubelet (runs pods on nodes), kube-proxy (network rules), container runtime (containerd, CRI-O).

Deployment strategies are a common topic: rolling updates (gradual replacement, zero downtime but mixed versions co-exist briefly), blue/green (instant cutover, full duplicate environment cost), and canary (small percentage of traffic to new version, requires traffic splitting). Know when to use each and how you'd implement them in Kubernetes.

## Deployment Strategies and Risk Management

The choice of deployment strategy is fundamentally a risk management decision. Interviewers want to see that you frame it that way.

Blue/green deployments minimize risk by keeping the old environment live until you're confident. The cost is resource doubling. Canary deployments minimize cost by only running the new version for a small traffic slice, but require sophisticated traffic routing and metric analysis. Feature flags decouple deployment from release entirely — code ships dark and enables gradually.

Be ready to discuss the operational overhead of each: blue/green requires environment management, canary requires metric evaluation automation, feature flags require a management system and discipline around flag cleanup.

## DevSecOps and Secrets Management

Security integrated into the delivery pipeline is a requirement, not an afterthought. Be ready to discuss where security gates fit in the pipeline and how you'd implement secrets management.

For secrets: never store secrets in code or environment variables baked into images. Know the patterns — secrets management systems (HashiCorp Vault, AWS Secrets Manager), Kubernetes secrets (understand their limitations — base64 encoded, not encrypted at rest by default without additional configuration), and sealed secrets for GitOps workflows.

Supply chain security is increasingly tested: image signing (Cosign, Notary), software bill of materials (SBOM), and verifying image provenance before deployment. Know SLSA (Supply-chain Levels for Software Artifacts) as a framework for reasoning about supply chain security maturity.

## Platform Engineering

Platform engineering represents the maturation of DevOps thinking: instead of every team managing their own infrastructure, a platform team builds internal products that make other teams self-sufficient.

The key shift is from "DevOps team as a service" (bottleneck) to "DevOps team as a platform product team" (force multiplier). Interviewers at companies with mature engineering organizations will probe your thinking here.

Know the Internal Developer Platform (IDP) concept: a curated set of tools and workflows that give product teams self-service access to environments, deployments, and observability without requiring platform team involvement for every request. Discuss the golden path — an opinionated, well-supported path that works for most teams — versus escape hatches for teams with special requirements.

The hardest part of platform engineering isn't the technology — it's product thinking. Treat internal developers as your customers. Interview them, measure adoption, collect feedback, and prioritize based on impact across the engineering organization.
