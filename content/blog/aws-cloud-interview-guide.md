---
title: "AWS Cloud Interview Guide: Core Services, Architecture, and Cost Optimization"
description: "AWS interview preparation for software engineers — core services (EC2, S3, RDS, Lambda), architecture patterns, IAM, networking, and cloud cost optimization strategies."
date: "2026-03-20"
category: "Cloud"
---

# AWS Cloud Interview Guide: Core Services, Architecture, and Cost Optimization

AWS knowledge is increasingly expected for backend, platform, and infrastructure engineering roles. Whether you're interviewing for a cloud-native startup or a large enterprise, understanding the core services, how they compose into architectures, and how to control costs will set you apart.

## Core Compute and Storage Services

**EC2** is the foundational compute service. Key interview topics: instance families (compute-optimized C-series, memory-optimized R-series, GPU P/G-series), placement groups (cluster for low latency, spread for fault isolation, partition for large distributed systems), and Auto Scaling Groups with mixed instance policies for cost efficiency. Spot Instances can reduce costs by 70–90% but may be interrupted — appropriate for fault-tolerant batch workloads and stateless services.

**S3** provides object storage with eleven 9s of durability. Know the storage classes: Standard, Intelligent-Tiering, Standard-IA, One Zone-IA, Glacier Instant Retrieval, Glacier Flexible Retrieval, and Deep Archive. Lifecycle policies automate transitions. S3 is also the backbone for data lakes — queried directly via Athena (serverless SQL) and processed by Glue (managed ETL). S3 strong consistency (since late 2020) means GET after PUT is always consistent.

**RDS** manages relational databases with automated backups, Multi-AZ failover, and read replicas. Aurora is AWS's cloud-native relational engine — compatible with MySQL and PostgreSQL, up to 5x faster than MySQL, and uses a distributed storage layer that replicates six copies across three AZs. Aurora Serverless v2 scales in fine-grained increments, suitable for unpredictable workloads.

**DynamoDB** is the go-to managed NoSQL service. Key concepts: partition key (determines shard), sort key (range within partition), Global Secondary Indexes (GSIs) for alternate access patterns, and DynamoDB Streams for change data capture. On-demand mode eliminates capacity planning; provisioned mode with auto-scaling suits predictable workloads. Single-digit millisecond latency at any scale with DynamoDB Accelerator (DAX) as an in-memory cache layer.

## VPC and Networking

A VPC is a logically isolated virtual network. Public subnets route through an Internet Gateway; private subnets route through a NAT Gateway for outbound internet access. Security Groups are stateful (return traffic is automatic); Network ACLs are stateless and apply at the subnet level.

**VPC Peering** connects two VPCs privately — no transitive peering. **Transit Gateway** solves the full mesh problem: a regional hub that connects hundreds of VPCs and on-premises networks. **PrivateLink** exposes services to consumers without traffic touching the internet, avoiding data exfiltration risks.

**Route 53** handles DNS with routing policies: Simple, Weighted (A/B traffic split), Latency-based (route to lowest-latency region), Failover (active-passive), Geolocation, and Geoproximity. Health checks power automatic failover.

**CloudFront** is the CDN — caches at 450+ edge locations worldwide. Integrates with S3, ALB, API Gateway, and Lambda@Edge for compute at the edge. Origin Shield adds a caching layer between CloudFront and the origin to reduce origin load.

## IAM Roles and Policies

IAM is the authorization backbone of AWS. Key concepts: Users, Groups, Roles, and Policies. Roles use temporary credentials via STS AssumeRole — always preferred over long-lived access keys. Instance profiles attach roles to EC2; service-linked roles allow AWS services to manage resources on your behalf.

Policy types: Identity-based (attached to principals), Resource-based (attached to resources like S3 bucket policies), Permission Boundaries (limit maximum permissions), SCPs (Service Control Policies in AWS Organizations — guardrails for entire accounts).

Policy evaluation order: explicit Deny always wins, then Organizations SCP, then Permission Boundary, then Identity-based policy, then Resource-based policy. Understanding this order is essential for debugging access issues.

**IAM best practices**: least privilege, no root account usage, require MFA, rotate credentials, use IAM Access Analyzer to detect overly permissive policies.

## Serverless and Event-Driven Architecture

**Lambda** executes code without managing servers. Concurrency model: Lambda scales by creating new execution environments (up to account limits). Cold starts are the primary latency concern — mitigated with Provisioned Concurrency, SnapStart (Java), and keeping functions warm. Lambda@Edge and CloudFront Functions enable compute at the CDN layer.

**API Gateway** fronts Lambda for HTTP APIs. REST API offers full control; HTTP API is cheaper and lower-latency for simple proxy use cases. WebSocket API supports real-time bidirectional communication.

Event-driven patterns use **SQS** (pull-based, durable queues — standard for at-least-once, FIFO for exactly-once ordering), **SNS** (push-based fan-out to multiple subscribers), and **EventBridge** (event bus with schema registry, routing rules, and SaaS integration). A common pattern: SNS fan-out to multiple SQS queues so multiple consumers process the same event independently.

**Step Functions** orchestrate multi-step serverless workflows with built-in error handling, retries, and parallel execution. Prefer Step Functions over hand-rolled state machines in Lambda for complex, long-running workflows.

## Cost Optimization Strategies

AWS costs balloon without deliberate management. Core strategies:

**Right-sizing**: Use Compute Optimizer recommendations. Downsize over-provisioned EC2, RDS, and Lambda memory. Many teams over-provision by 2-4x.

**Reserved Instances and Savings Plans**: Compute Savings Plans offer up to 66% savings with flexibility across EC2, Lambda, and Fargate. Reserved Instances (1 or 3 year commitment) suit stable workloads. Convertible RIs allow instance family changes.

**Spot Instances**: Use for batch processing, ML training, and stateless web tiers with graceful interruption handling. Spot interruption notices give 2 minutes to checkpoint.

**Storage tiering**: Move infrequently accessed S3 data to IA or Glacier. Enable S3 Intelligent-Tiering for unpredictable access patterns. Delete unattached EBS volumes and unused snapshots.

**Data transfer costs**: Data transfer out is expensive ($0.09/GB). Minimize cross-region traffic. Use VPC endpoints to avoid NAT Gateway costs for S3 and DynamoDB. Compress API responses.

## AWS Well-Architected Framework

The six pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability. Interviewers frequently ask you to evaluate a design against these pillars.

Reliability pillar highlights: multi-AZ deployments for high availability, multi-region active-active or active-passive for disaster recovery, chaos engineering with AWS Fault Injection Simulator, and circuit breakers in service-to-service calls.

## Common AWS Interview Questions

- **How would you design a highly available web application on AWS?** — Multi-AZ EC2 behind an ALB, RDS Multi-AZ, ElastiCache for session state, CloudFront for static assets, Route 53 health checks for failover.
- **What is the difference between SQS and SNS?** — SQS is a pull-based queue for point-to-point; SNS is push-based fan-out. Use both together for fan-out to multiple queues.
- **How do you secure an S3 bucket?** — Block all public access, use bucket policies and IAM roles, enable server-side encryption (SSE-S3 or SSE-KMS), enable versioning, enable access logging, use Macie for sensitive data detection.
- **How does Lambda handle concurrency limits?** — Account-level concurrency limit (default 1000). Function-level reserved concurrency prevents one function from consuming all capacity. Provisioned concurrency eliminates cold starts.

AWS expertise is increasingly table stakes at modern engineering teams. Understanding not just what services exist, but how they compose and where they break, is what senior engineers must demonstrate.
