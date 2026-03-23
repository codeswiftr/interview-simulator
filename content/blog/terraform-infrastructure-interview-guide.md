---
title: "Terraform and Infrastructure as Code Interview Guide"
description: "Infrastructure as Code interview prep — Terraform fundamentals, state management, module design, provider patterns, Terraform Cloud, and IaC best practices for cloud platforms."
date: "2026-03-20"
category: "DevOps"
---

# Terraform and Infrastructure as Code Interview Guide

Terraform interviews test both conceptual understanding and practical experience. Interviewers want to know that you've actually managed Terraform at scale — dealt with state problems, designed module hierarchies, and made the tradeoff decisions that only surface in production. This guide covers the topics that consistently appear across infrastructure and DevOps interviews.

## Terraform Fundamentals

Before going deep, interviewers establish your baseline. Know the core concepts cold: providers (plugins that interact with APIs), resources (infrastructure objects managed by Terraform), data sources (read-only lookups of existing infrastructure), outputs (values exported from a module or root configuration), and variables (parameterization).

The plan/apply lifecycle is fundamental. `terraform plan` creates an execution plan by comparing desired state (your configuration) to actual state (what's recorded in the state file). `terraform apply` executes that plan. Know what happens when state drifts — when someone manually changes infrastructure outside Terraform, the next plan will show a diff that may surprise you. Discuss `terraform refresh` and `terraform import` as tools for reconciling drift.

Be ready to explain what `terraform destroy` does and when you'd use it versus more targeted approaches like `terraform apply -target`. Know the `-target` flag's limitations: it's useful for surgical operations but can leave your configuration and state inconsistent if overused.

## State Management

State is the most operationally sensitive part of Terraform. Interviews often probe this area because it's where production teams get into trouble.

Remote state backends (S3, Azure Blob, GCS, Terraform Cloud) are required for team environments. Local state is only acceptable for individual experimentation. Know the essential backend configuration: state locking (prevents concurrent applies that corrupt state), encryption at rest, versioning (allows rollback to a previous state file), and access control (who can read/write state, since state often contains sensitive values).

State file contains sensitive information — resource IDs, sometimes secrets. This is a known limitation and a common interview question: "How do you handle sensitive values in Terraform state?" The honest answer is that Terraform state is sensitive, it should be encrypted at rest, access should be restricted, and you should use `sensitive = true` on outputs to prevent them from being displayed in plan output — but the values are still in state.

Workspace concepts often trip people up. Terraform workspaces are a lightweight mechanism for maintaining multiple state files with the same configuration — useful for managing dev/staging/prod environments when the differences are minimal. Know their limitations: all workspaces share the same code, which can lead to drift in configuration between environments. Many teams prefer separate directories or separate configurations per environment instead.

## Module Design

Module design questions reveal seniority more than almost any other Terraform topic. Bad modules have too many responsibilities, leak implementation details, and are impossible to reuse across contexts.

A well-designed module has a clear single purpose, a stable interface (inputs and outputs), sensible defaults that work for 80% of use cases, and input validation. Know how to write validation blocks for variables. Know when to use `optional()` for optional object attributes.

The root module vs. child module distinction matters. The root module is what you run `terraform apply` against. Child modules are reusable components called by the root or other modules. Design child modules to be testable in isolation — they shouldn't assume specific values for variables that would only make sense in one specific context.

Module versioning is critical for stable infrastructure. Use module version pinning when sourcing from a registry or Git repository. Discuss semantic versioning for modules: breaking interface changes warrant a major version bump, backward-compatible additions are minor, bug fixes are patch. Know how to evaluate whether an interface change is breaking.

## Provider Patterns and Versioning

Provider version constraints are a common source of problems in Terraform. Know the constraint syntax: `~> 5.0` pins to `>= 5.0, < 6.0` (safe upgrades within a major version), `>= 5.0, < 5.10` pins more tightly. The `.terraform.lock.hcl` file locks to specific provider versions for reproducibility — this should be committed to version control.

Multi-provider configurations come up in system design questions. Interviewers may ask how you'd manage infrastructure across multiple AWS accounts or cloud providers. Discuss provider aliasing, the `providers` argument in module calls, and how to avoid cross-account state coupling.

The `depends_on` meta-argument is a code smell when overused. If you find yourself using it frequently, it often signals that you're working around an ordering issue that could be resolved by proper resource references — which Terraform uses to build its dependency graph automatically.

## Drift Detection and Day-2 Operations

Creating infrastructure is table stakes. Senior interviews probe what happens after.

Drift detection is the process of identifying when actual infrastructure diverges from Terraform state. Discuss strategies: scheduled `terraform plan` runs that alert on non-empty diffs, using Terraform Cloud's continuous validation, or dedicated drift detection tools. The harder question is what you do when drift is detected: always reconcile via Terraform, never by manual change.

Refactoring Terraform configurations is an underappreciated skill. When you rename a resource or move it into a module, Terraform sees it as destroying the old resource and creating a new one — which is catastrophic for production databases. Know `terraform state mv` for moving resources within state and the `moved` block (introduced in Terraform 1.1) for tracking moves in configuration that collaborators can apply safely.

## Terraform vs. Pulumi vs. CDK

Interviewers at companies evaluating IaC tooling will sometimes ask for a comparison. Frame it around the tradeoffs rather than declaring a winner.

Terraform uses HCL — a declarative language that's approachable but limited in expressiveness. Pulumi uses general-purpose languages (Python, TypeScript, Go) — more powerful but introduces the full complexity of a programming language into infrastructure. CDK (AWS CDK or CDK for Terraform) takes a similar approach but generates CloudFormation or Terraform configurations, adding an abstraction layer.

The key questions for tool selection: Does your team want infrastructure code to look like application code (Pulumi/CDK) or be clearly separate (Terraform)? How important is the ecosystem and community (Terraform wins on provider breadth)? Do you need fine-grained programmatic logic in your infrastructure definitions (Pulumi/CDK advantage)?

## Security with IaC

IaC security questions appear in almost every infrastructure interview. Know the common vulnerabilities: overly permissive IAM policies created for convenience, security groups with wide-open ingress rules, unencrypted storage resources, and public S3 buckets.

Static analysis tools (tfsec, Checkov, Terrascan) can catch many of these issues before apply. Know how to integrate them into a CI pipeline as a required gate. Discuss the policy-as-code pattern: defining organizational security standards as machine-readable policies that are automatically enforced in the pipeline.

For practical interview questions, prepare specific examples: a state management problem you solved, a module you designed and why, or a security issue you caught in code review. Concrete stories with real constraints and outcomes are far more persuasive than generic descriptions of best practices.
