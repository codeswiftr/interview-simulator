---
title: "Platform Engineering Interview Guide"
description: "Technical interview preparation for platform engineering roles: internal developer platforms, golden paths, self-service infrastructure, Backstage developer portals, infrastructure abstraction patterns, and what companies building engineering productivity at scale expect from platform engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Platform Engineering Interview Guide

Platform engineering has emerged as a distinct discipline from DevOps and SRE — focused not on operating infrastructure, but on building internal products that make other engineers more productive. The platform engineer's customer is the software engineer. The deliverable is not a feature for end users, but tooling, abstractions, and self-service capabilities that let development teams move faster with less operational burden. As organizations scale past 100-200 engineers, the investment in platform engineering typically yields exponential returns in organizational velocity.

## What Platform Engineering Is (and Isn't)

**Platform engineering vs. DevOps**: DevOps is a cultural and practices movement emphasizing collaboration between development and operations. Platform engineering is an organizational model where a dedicated team builds and operates an Internal Developer Platform (IDP) that other teams use. The platform team is a product team whose users are internal engineers.

**Platform engineering vs. SRE**: SRE (Site Reliability Engineering) focuses on reliability of production systems — incident response, SLOs, error budgets, chaos engineering. Platform engineering focuses on developer productivity — making it easy to build, deploy, observe, and operate services. The two often work closely together but have different primary concerns.

**The Internal Developer Platform (IDP)**: The set of tools, services, and abstractions that compose the platform. Typically includes: self-service infrastructure provisioning (create a new service in 5 minutes), deployment pipelines (automated from commit to production), observability integration (logs, metrics, traces pre-configured), secrets management, environment management, and a developer portal for discovery and documentation.

## Core Platform Engineering Concepts

**The Golden Path**: The "paved road" or "golden path" is the opinionated, well-supported way to do common tasks — creating a new microservice, deploying to production, adding observability. The golden path hides complexity while offering flexibility for teams with specialized needs to go off-path. The key design principle: the golden path must be genuinely better than the alternatives for most teams to adopt it willingly.

**Self-service infrastructure**: Instead of filing tickets for database provisioning, VPC setup, or Kubernetes namespace creation, development teams should be able to provision infrastructure through self-service tools. Backstage (Spotify's open-source developer portal), Terraform modules exposed through self-service portals, or custom internal CLIs enable this. The platform team builds the guardrails; development teams provision within them.

**Developer portal with Backstage**: Backstage is the de facto standard for internal developer portals — a catalog of all services, their documentation, ownership, deployment status, and on-call information in one place. Platform engineers build plugins for the services their company uses (PagerDuty, DataDog, GitHub Actions, ArgoCD) and maintain the catalog of service metadata. Understanding Backstage's architecture (plugin system, catalog API, TechDocs integration) is expected for platform roles at companies using it.

**Infrastructure abstraction layers**: Raw Kubernetes, Terraform, and cloud APIs are too complex for application developers to use directly. Platform engineers build abstractions: a Helm chart for a standard microservice (configure 20 variables instead of writing 500 lines of YAML), a Terraform module for a production-grade database (opinionated VPC placement, encryption, backup policy, monitoring), or a CLI that wraps kubectl with company-specific workflows.

## Deployment and CI/CD Platform Design

**GitOps pattern**: Infrastructure and application configuration stored in Git; an operator (ArgoCD, Flux) reconciles actual state with desired state. The Git repository is the source of truth. Changes happen through pull requests, providing an audit trail, code review, and rollback capability.

**Progressive delivery**: Feature flags, canary deployments, and blue-green deployments as primitives in the deployment platform. The platform abstracts the complexity of progressive delivery so application engineers can configure "10% canary" in a deploy configuration rather than manually managing load balancer weights.

**Deployment observability**: Every deployment should automatically generate deployment markers in the observability platform (DataDog, Prometheus, Grafana) — enabling "did this deployment cause the latency spike?" correlation without manual annotation.

**Rollback automation**: Detecting failed deployments and automatically reverting is more reliable than human-triggered rollbacks. Platform-level rollback triggers based on error rate increase, latency SLO breach, or health check failures.

## What Platform Engineering Interviews Assess

**Product thinking**: Platform engineers must think like product managers for their developer audience. Interviewers assess: how do you discover what developers need? How do you prioritize across competing requests? How do you measure adoption and success of platform features? Candidates who only think technically without the product lens fail platform interviews.

**Technical depth in infrastructure**: Kubernetes internals, Terraform best practices, cloud provider services, networking fundamentals. The difference from pure infrastructure engineering is the abstraction mindset — not just knowing how to use Kubernetes, but knowing how to build a product on top of Kubernetes that hides its complexity.

**Developer empathy**: Platform engineers must deeply understand the developer experience they're optimizing. Being able to articulate friction in the development lifecycle, and propose specific platform improvements to address it, is the core platform engineering skill.

**Measuring developer productivity**: DORA metrics (deployment frequency, lead time for changes, change failure rate, time to restore service) are the industry standard for measuring the impact of platform improvements. Platform engineers who can speak to these metrics and how their work moved them demonstrate operational maturity.

## Who Hires Platform Engineers

Dedicated platform engineering roles exist at companies with 100+ engineers. Companies with particularly strong platform engineering cultures: Spotify (Backstage creators), Netflix (pioneered many internal platform tools), Google (Borg → Kubernetes origin), Shopify, and large banks (engineering modernization through platform abstraction).

Platform engineering is one of the fastest-growing engineering specializations because the value proposition scales with organization size — the larger the engineering organization, the higher the leverage of investing in the platform.
