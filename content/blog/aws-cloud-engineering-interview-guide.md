---
title: "AWS Cloud Engineering Interview Guide"
description: "A practical guide to AWS cloud infrastructure interview questions covering core services, IaC, serverless vs containers, cost optimization, HA/DR design, and the Well-Architected Framework."
date: "2026-03-19"
category: "Cloud Infrastructure"
---

## What Cloud Engineering Interviews Actually Test

AWS interviews for cloud infrastructure and platform engineering roles are not trivia contests about service limits. They are design conversations. Interviewers want to see how you reason about trade-offs — availability vs cost, managed vs self-managed, speed vs operational complexity. Knowing EC2 instance families matters less than knowing when to use EC2 at all.

This guide covers the service areas and design patterns that come up most frequently in cloud engineering, SRE, and platform engineering interviews.

---

## Core AWS Services: What Interviewers Actually Ask

### EC2 and Compute

Beyond "what is an instance type," interviewers test placement decisions:

- **When do you choose EC2 over Lambda or ECS?** Long-running workloads, stateful applications, or anything requiring persistent local storage or GPU access. Lambda cold starts and 15-minute execution limits rule it out for sustained compute.
- **Spot vs On-Demand vs Reserved:** Spot for fault-tolerant batch jobs and CI/CD runners. Reserved for stable baseline capacity. On-demand for unpredictable or short-lived needs.
- **Auto Scaling Group design:** Know the difference between target tracking, step scaling, and scheduled scaling. Be ready to explain how you handle scale-in protection for stateful workers.

### S3

S3 questions cluster around access patterns and lifecycle management:

- **Storage class selection:** S3 Standard for frequently accessed data, Standard-IA for monthly access, Glacier Instant Retrieval for archival with sub-second restore, Glacier Deep Archive for cold compliance storage. Be ready to justify cost trade-offs.
- **Pre-signed URLs vs bucket policies vs IAM:** Pre-signed URLs grant temporary access without exposing credentials. Bucket policies control cross-account and public access. IAM roles govern service-to-service access.
- **Consistency model:** S3 provides strong read-after-write consistency for all objects since late 2020. Knowing this prevents incorrect distributed locking designs.

### RDS and Databases

- **Multi-AZ vs Read Replicas:** Multi-AZ is for durability and automatic failover (synchronous replication to standby). Read Replicas are for scaling reads (asynchronous). A common interview mistake is using read replicas for failover — they are not the same thing.
- **Aurora vs RDS:** Aurora's distributed storage architecture provides faster failover (typically under 30 seconds), up to 15 read replicas, and storage that auto-scales. Use it when you need MySQL/PostgreSQL compatibility with higher availability requirements.
- **RDS Proxy:** Reduces connection pooling overhead for serverless and containerized workloads where connection counts spike rapidly.

### Lambda and Serverless

Interviewers probe edge cases, not happy paths:

- **Cold start mitigation:** Provisioned concurrency for latency-sensitive paths. Keep runtimes lean. Avoid VPC attachment unless necessary (adds 100-500ms to cold starts).
- **Execution limits:** 15-minute timeout, 10GB memory, 512MB ephemeral storage (expandable to 10GB). These constraints define Lambda's boundaries.
- **Event source mapping:** Know how Lambda consumes from SQS (batch windows, partial batch failure handling), Kinesis (checkpointing, bisect-on-error), and DynamoDB streams.

### ECS and EKS

- **ECS Fargate vs EC2 launch type:** Fargate removes node management entirely — you pay per task vCPU and memory. EC2 launch type gives you more control over placement, instance types, and GPU access, at the cost of managing the underlying fleet.
- **EKS trade-offs:** Kubernetes brings portability and a rich ecosystem, but operational overhead is real. Control plane management, node group upgrades, and add-on compatibility are ongoing work. EKS Auto Mode (GA in 2024) reduces this significantly.
- **Service mesh decisions:** When does adding Istio or App Mesh justify the complexity? Answer: when you need mTLS between services, fine-grained traffic control for canary deployments, or detailed service-to-service observability.

### VPC Networking

VPC questions are a filter for platform engineers:

- **Subnet design:** Public subnets for load balancers and NAT gateways, private subnets for application tier and databases. Never put RDS in a public subnet.
- **VPC peering vs Transit Gateway:** Peering is non-transitive and works for simple hub-and-spoke. Transit Gateway handles complex multi-account, multi-VPC routing at scale but adds cost (~$0.05/attachment-hour plus data processing).
- **Security groups vs NACLs:** Security groups are stateful (return traffic automatically allowed). NACLs are stateless and processed in order. Security groups are the primary control; NACLs add a coarse network-layer boundary.

### IAM

IAM is frequently tested because it separates engineers who understand security from those who just deploy things:

- **Least privilege:** Start with no permissions and add what's needed. Avoid `*` resource ARNs in production policies.
- **Roles vs users:** Never use IAM users for service-to-service auth. Always use roles with instance profiles, task roles, or OIDC federation.
- **Permission boundaries:** Used to delegate permission management without allowing privilege escalation. Common in multi-account setups where platform teams provision accounts for product teams.

---

## Serverless vs Containers: The Trade-Off Question

This is a standard system design interview topic. Frame your answer around four dimensions:

| Dimension | Lambda/Serverless | ECS/EKS Containers |
|-----------|------------------|--------------------|
| Startup latency | 10ms–500ms (cold) | Seconds (container start) |
| Execution duration | Up to 15 minutes | Unlimited |
| State | Stateless by design | Can be stateful |
| Operational overhead | Near zero | Moderate to high |
| Cost model | Per-request | Per-hour (compute) |

**Interview answer pattern:** Use Lambda for event-driven, short-duration, stateless workloads (API handlers, file processors, scheduled jobs). Use containers when you need persistent connections, long-running processing, custom runtimes, or GPU access. For many production systems, you use both — Lambda at the edge and for async processing, ECS/EKS for core services.

---

## Cost Optimization Questions

Cost questions are common for senior and staff-level roles:

- **Compute Savings Plans vs Reserved Instances:** Savings Plans are more flexible (apply across instance families and regions). Reserved Instances lock to specific instance types and regions but offer slightly higher discounts.
- **Identifying waste:** Use AWS Cost Explorer, Trusted Advisor, and Compute Optimizer. Common waste: idle EC2 instances, over-provisioned RDS, S3 data never accessed, NAT gateway data transfer for traffic that could stay within a VPC or use VPC endpoints.
- **Data transfer costs:** Often overlooked. Cross-AZ traffic costs $0.01/GB each way. Design services to minimize cross-AZ calls in the hot path. Use S3 VPC endpoints to eliminate NAT gateway charges for S3 access.

---

## High Availability and Disaster Recovery

Expect design questions framed as: "Walk me through a multi-AZ deployment for a critical service" or "How do you achieve an RTO of 1 hour and RPO of 15 minutes?"

**Multi-AZ web application design:**

1. ALB spanning at least two AZs
2. Auto Scaling Group with instances distributed across AZs
3. RDS Multi-AZ with automatic failover
4. ElastiCache with Multi-AZ replication
5. S3 for static assets (99.999999999% durability, cross-region replication if needed)

**DR tiers:**

- **Backup and restore (RTO hours, RPO hours):** Cheapest. Restore from snapshots. Acceptable for non-critical workloads.
- **Pilot light (RTO ~30 min):** Core infrastructure always on, data replication active, scale up on failover.
- **Warm standby (RTO minutes):** Scaled-down replica always running. Fastest to promote.
- **Multi-site active/active (RTO near zero):** Full duplicate stack. Most expensive. Required for strict SLAs.

---

## AWS Well-Architected Framework as Interview Structure

The six pillars give you a framework to structure open-ended design answers. When asked "how would you design X," walk through relevant pillars:

- **Operational Excellence:** How do you deploy changes safely? (Blue/green, canary, feature flags.) How do you run operations? (Runbooks, automated remediation.)
- **Security:** Encryption at rest and in transit. IAM least privilege. Network segmentation. Detective controls (CloudTrail, GuardDuty, Config).
- **Reliability:** Multi-AZ. Health checks and automatic replacement. Retry logic with exponential backoff and jitter.
- **Performance Efficiency:** Right-sizing. Caching (CloudFront, ElastiCache). Database indexing and query optimization.
- **Cost Optimization:** Savings Plans. Auto Scaling. Lifecycle policies. Architecture that scales to zero when idle.
- **Sustainability:** Graviton instances (up to 40% better price/performance than x86). Spot for batch. Right-sizing to eliminate idle capacity.

---

## IaC: CDK vs Terraform

This is a direct question in most platform engineering interviews.

**Terraform:**
- HCL is readable and approachable for cross-functional teams
- Mature state management (remote state, state locking)
- Provider ecosystem covers every major cloud and SaaS tool
- Plan/apply cycle makes drift detection explicit
- Weakness: imperative logic is verbose; abstraction through modules has limits

**AWS CDK:**
- Full programming languages (TypeScript, Python, Go) — loops, conditionals, and abstractions are native
- Constructs are composable and testable with `aws-cdk-lib/assertions`
- Strong for AWS-only stacks where type safety and IDE support matter
- Synthesizes to CloudFormation, which introduces CloudFormation's constraints and rollback behavior
- Weakness: synthesized output is verbose and hard to audit; less portable than Terraform

**Interview answer:** Neither is universally better. Use Terraform when you have multi-cloud requirements, an existing Terraform state ecosystem, or teams that prefer declarative configuration. Use CDK when you are AWS-only, value type safety, need to generate infrastructure dynamically, or want to write unit tests against your infrastructure definitions.

---

## Design Scenario: Highly Available Web Application on AWS

A common closing question: "Design a highly available, scalable web application on AWS."

**Core architecture:**

- Route 53 with health checks and latency-based routing
- CloudFront distribution for static assets and edge caching
- ALB across two or three AZs
- ECS Fargate or EC2 Auto Scaling Group for application tier
- RDS Aurora Multi-AZ (or Aurora Serverless v2 for variable workloads)
- ElastiCache Redis (Multi-AZ) for session state and caching
- SQS for async job queuing; Lambda or ECS workers for processing
- CloudWatch for metrics, alarms, and dashboards; X-Ray for distributed tracing
- AWS Secrets Manager for credentials rotation

**Key decisions to articulate in the interview:**

1. Why ALB over NLB (HTTP/HTTPS routing, path-based rules, WAF integration)
2. How you handle database connection pooling at scale (RDS Proxy)
3. Where you place caching and what cache invalidation strategy you use
4. How deployments happen without downtime (rolling updates or blue/green via CodeDeploy)
5. How you handle a single AZ failure (Auto Scaling health checks, Multi-AZ data layer)

Interviewers are not looking for a perfect answer. They are evaluating whether you ask clarifying questions about load patterns and SLAs, whether you acknowledge trade-offs, and whether you can explain why you made each choice.
