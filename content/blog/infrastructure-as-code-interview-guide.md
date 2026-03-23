---
title: "Infrastructure as Code Interview Guide"
description: "IaC interviews covering Terraform, Pulumi, AWS CDK, and CloudFormation — state management, module design, drift detection, and the platform engineering skills that matter in production."
date: "2026-03-19"
category: "Technical Skills"
---

# Infrastructure as Code Interview Guide

Infrastructure as Code has moved from a DevOps specialty to a mainstream engineering skill. Platform engineering teams, SRE roles, and even backend engineers at infrastructure-heavy companies are now expected to know Terraform, understand state management, and design reusable infrastructure modules. This guide covers what IaC interviews actually test.

## Why IaC Appears in Interviews

The shift to cloud-native infrastructure means most production systems are defined in code rather than through manual configuration. Senior engineers who have only worked at the application layer increasingly encounter IaC in interviews because:

- Platform teams interview for engineers who can own infrastructure definitions end-to-end
- Startup engineering roles often require the same person to write application code and manage infrastructure
- System design interviews increasingly include "how would you provision and manage this?" as part of the scope

Companies with significant platform engineering investments (Stripe, GitHub, Cloudflare, Shopify) interview IaC skills as seriously as application code. Understanding the principles behind IaC tools matters more than memorizing specific syntax.

## Terraform: The Default Standard

Terraform by HashiCorp is the most commonly interviewed IaC tool. The core concepts that appear in interviews:

### State Management

Terraform tracks infrastructure in a state file that maps configuration to real resources. Interviewers probe state management because it's where most production problems occur.

Key concepts:
- **Remote state**: Local state files don't work for teams. Remote backends (S3 + DynamoDB for locking, Terraform Cloud) allow concurrent work without conflicts.
- **State locking**: Prevents concurrent applies that could corrupt state. DynamoDB provides locking for S3 backends.
- **`terraform import`**: Brings existing infrastructure under Terraform management without recreating it — important when adopting IaC incrementally.
- **State drift**: When real infrastructure diverges from state (manual console changes). `terraform plan` detects drift; fixing it is a discipline question.

A common interview question: "You run `terraform plan` and see 50 resources marked for replacement that shouldn't change. What happened and how do you investigate?" Strong answers: check for provider version changes, look for state drift from out-of-band changes, check for `lifecycle` block issues in resource definitions.

### Module Design

Modules are Terraform's reusability unit. Interviewers ask about module design because poorly designed modules create maintenance debt at scale.

Good module design:
- Modules should have clear input/output contracts defined in `variables.tf` and `outputs.tf`
- Avoid over-abstraction: a module that wraps a single resource with a different variable name adds no value
- Versioned modules (from a module registry or Git tags) prevent unexpected breaking changes
- Opinionated modules for your organization's standards (e.g., "S3 bucket with encryption, versioning, and logging enabled") are more valuable than thin wrappers

Interview question: "How would you structure Terraform for a company with 50 engineering teams sharing the same AWS account?" The answer involves workspace or account isolation strategy, shared module registry, and governance for who can modify what.

### Terraform vs. Alternatives

Interviewers at companies that have made infrastructure tooling choices will ask you to discuss trade-offs:

**Pulumi**: Uses real programming languages (TypeScript, Python, Go, C#) instead of HCL. Enables loops, conditionals, and abstraction patterns that are awkward in Terraform. Better for complex logic; steeper learning curve, smaller ecosystem.

**AWS CDK**: AWS-specific, uses TypeScript/Python/Java. Excellent for AWS-native infrastructure with the full power of a programming language. Less portable than Terraform.

**CloudFormation**: AWS's native IaC. Verbose, but deeply integrated with AWS services and the canonical "source of truth" for some organizations. CDK compiles to CloudFormation.

The honest trade-off: Terraform's declarative HCL is simpler for straightforward infrastructure but fights you for complex logic. Pulumi and CDK are more powerful but require real software engineering discipline to keep manageable.

## Platform Engineering Concepts

IaC interviews at companies building internal developer platforms (IDPs) go deeper than just "can you write Terraform." They test platform thinking:

### Self-Service Infrastructure

The goal of an IDP is to let application teams provision infrastructure without help from platform teams. This requires:
- Abstraction: application teams specify *what* they need (a database with these capacity requirements) not *how* to provision it
- Guard rails: enforce security policies (encryption, tagging) automatically rather than relying on manual review
- Escape hatches: let teams override defaults when they have legitimate reasons

Interview question: "How would you design a self-service database provisioning system so that any team can get a PostgreSQL instance in 5 minutes, with security policies enforced automatically?" Strong answers address Terraform modules, CI/CD pipeline for infrastructure, approval workflows for high-cost resources, and observability.

### Drift Detection and Remediation

Production IaC requires ongoing maintenance, not just initial provisioning. Drift detection systems run `terraform plan` on a schedule and alert when real infrastructure diverges from the IaC definition. Remediation strategies: automated revert (risky), alert and require manual fix (safe), or accept the drift and update the IaC to match.

## What to Study

- Terraform documentation — especially state, backends, and modules
- The Gruntwork Terragrunt documentation — their approach to large-scale Terraform organization is widely adopted
- AWS Well-Architected Framework — IaC interviews often test whether you know what good infrastructure looks like, not just how to provision it
- A real project: deploy a non-trivial application to AWS or GCP using Terraform end-to-end. The hands-on experience shows immediately in interviews.

The engineers who do best in IaC interviews have shipped infrastructure that broke in production and debugged it. Theoretical knowledge of state management doesn't compare to having spent two hours debugging why `terraform apply` wanted to replace a load balancer that had traffic on it.
