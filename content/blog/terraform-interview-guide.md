---
title: "Terraform Interview Guide: Infrastructure as Code, State Management, and Modules"
description: "Prepare for Terraform interviews with coverage of HCL syntax, state management, remote backends, drift detection, module design, workspace strategies, and team-scale IaC best practices."
date: "2026-03-20"
category: "Technical Skills"
---

# Terraform Interview Guide: Infrastructure as Code, State Management, and Modules

Terraform interviews test whether you've moved beyond writing basic resource blocks into the territory of managing IaC at team scale. The common failure point for candidates is knowing the syntax but not understanding state, drift, and the operational challenges that emerge when multiple people work on the same infrastructure.

## HCL Fundamentals

Terraform's configuration language is declarative. You describe desired state; Terraform figures out how to get there.

**Core constructs:**

```hcl
variable "instance_type" {
  type    = string
  default = "t3.medium"
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  tags = {
    Name = "web-${terraform.workspace}"
  }
}

output "instance_ip" {
  value = aws_instance.web.public_ip
}
```

**Data sources** query existing infrastructure without managing it. `data.aws_ami.ubuntu` above reads the latest Ubuntu AMI without Terraform owning that resource.

**Locals** reduce repetition for computed values used in multiple places:

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Team        = "platform"
    ManagedBy   = "terraform"
  }
}
```

**Interview Q&A:**

Q: "What's the difference between `count` and `for_each`?"

A: `count` creates N instances of a resource indexed by number. `for_each` creates one instance per key in a map or set. The key difference: removing an element from a `count` list renumbers subsequent resources, causing Terraform to destroy and recreate them. `for_each` uses stable keys, so removing one entry only removes that resource. Use `for_each` for anything where identity matters.

## State Management

Terraform state is a JSON file mapping your configuration to real infrastructure. It stores resource IDs, attributes, and dependency relationships.

**Remote state.** Never use local state in production or teams. Remote backends (S3 + DynamoDB, Terraform Cloud, GCS) enable:
- Shared access by multiple team members
- State locking to prevent concurrent applies
- State versioning for recovery

**S3 backend with locking:**

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "platform/vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
```

The DynamoDB table must have a `LockID` string partition key. Terraform creates and releases locks atomically around apply operations.

**State drift.** Drift occurs when real infrastructure diverges from Terraform state — typically from manual changes, other tools, or resource changes outside Terraform's control. `terraform plan` detects drift by comparing state to actual resource attributes. `terraform refresh` updates state from real infrastructure without making changes (deprecated in favor of `-refresh-only` plan).

**Interview Q&A:**

Q: "An engineer manually changed a security group in the AWS console. How do you reconcile this?"

A: Run `terraform plan -refresh-only` to see what Terraform detects. Then decide: if the manual change was correct, import the change into a code update and apply. If the manual change was wrong, run a normal `apply` to revert it. Document the incident in your runbook — manual changes in Terraform-managed resources should be prohibited except in declared emergencies.

## Module Design

Modules are reusable units of Terraform configuration. Good module design is a senior-level concern.

**Module interface principles:**
- Input variables should have types and descriptions. Validation blocks for non-obvious constraints.
- Outputs should expose what consumers need without exposing internal implementation details.
- Modules should not include provider configuration — callers configure providers.
- Pin module sources to versions for stability.

**Module versioning:**

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Allow 5.x, not 6.x
}
```

For internal modules in a monorepo, use Git ref pinning:

```hcl
module "rds" {
  source = "git::ssh://git@github.com/myorg/terraform-modules.git//rds?ref=v2.1.0"
}
```

**Module size.** A module that creates a VPC, all subnets, route tables, NAT gateways, and VPC endpoints is reasonably sized. A module that creates a VPC and also configures IAM roles, EKS, and RDS is too large — its blast radius is unacceptable and testing is difficult.

## Workspace Strategies

Terraform workspaces provide isolated state files within a single backend configuration. They are appropriate for:
- Short-lived environments (feature branches, PR environments)
- Small teams with simple environment structures

For larger teams, separate state files per environment with separate variable files is more explicit and safer. Many teams use a directory-per-environment structure:

```
terraform/
  modules/
    vpc/
    rds/
  environments/
    dev/
    staging/
    prod/
```

Each environment directory has its own backend configuration and `terraform.tfvars`. This prevents accidental cross-environment state operations.

**Interview Q&A:**

Q: "When would you use workspaces versus separate state files?"

A: Workspaces for dynamic, short-lived environments where the configuration is identical and you want programmatic creation. Separate state files for long-lived environments (dev, staging, prod) where configuration differences between environments are significant and you want strong isolation guarantees.

## Team-Scale Best Practices

**State access controls.** Restrict who can run `apply`. At minimum, production applies should require peer review and use a service account with limited permissions, not personal credentials. Terraform Cloud/Enterprise and Atlantis both provide PR-based workflow gates.

**Sensitive values.** Use `sensitive = true` on outputs and variables containing secrets. This prevents Terraform from printing them in plan output. Use Vault provider or AWS SSM Parameter Store for runtime secret injection rather than storing secrets in state.

**Dependency management.** Avoid implicit dependencies between modules through data source lookups into each other's state. Use explicit remote state data sources for cross-module dependencies:

```hcl
data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "platform/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**Testing.** Terratest (Go) and `terraform test` (native, 1.6+) enable unit and integration testing of modules. At minimum, test module instantiation with required variables in a sandboxed account.

**Upgrade strategy.** Pin the Terraform version with a `required_version` constraint. Upgrade versions deliberately, testing in non-production first. Provider upgrades are separate from Terraform core upgrades — manage them independently.

The key signal in a Terraform interview is whether you think in terms of operational risk. Every decision — module size, state structure, workspace strategy — is really a decision about who can break what, and how quickly you can recover.
