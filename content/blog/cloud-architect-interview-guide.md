# Cloud/AWS Architect Interview Guide 2024: Design at Infrastructure Scale

Cloud architect interviews are different from software engineering interviews in a specific way: the correct answer is almost never "use X." The correct answer is almost always "it depends, and here is the decision framework." The candidates who impress in cloud architecture interviews are the ones who lead with tradeoffs — who can explain why a multi-AZ active-passive RDS setup is right for one use case and Aurora Global Database is right for another, and who know where those choices show up in the monthly bill.

This guide is for engineers pursuing cloud architect, solutions architect, or cloud engineer roles. It covers the AWS Well-Architected Framework in practical terms, the design decisions that come up repeatedly in interviews, and the service-level depth expected for the most commonly tested scenarios.

## The Cloud Architect Environment: What the Work Actually Looks Like

A cloud architect spends their time at the intersection of engineering, operations, and finance. On any given week they might:

- Review a proposed architecture with a product team and push back on a design that uses a synchronous API call where an event-driven pattern would be more resilient
- Write or review Terraform modules that will be used by 15 engineering teams, knowing that a mistake in the module becomes a systemic problem
- Investigate a 40% spike in AWS spend and trace it to an oversized RDS instance class and a Lambda function that was inadvertently processing the same SQS message multiple times
- Prepare a runbook and failover test for a disaster recovery exercise that will simulate an entire regional outage
- Work with the security team to enforce guardrails via AWS Organizations Service Control Policies

The role requires both depth (knowing the internals of a specific service well enough to diagnose failures and make informed capacity decisions) and breadth (being able to reason about how a change to the data tier affects the compute tier, which affects the CDN caching behavior, which affects the billing model).

## Interview Process: Typical Stages and What Each Tests

**Recruiter screen**: Basic cloud experience, certifications, scope of environments managed (number of accounts, monthly spend, whether multi-region or single-region, team size).

**Technical phone screen**: Expect a 30-minute mix of service knowledge and one open-ended design question. Common questions at this stage: "Walk me through the difference between an Application Load Balancer and a Network Load Balancer and when you would use each." "What is the difference between a NAT Gateway and a VPC endpoint?" "How does S3 eventual consistency work?" These test whether you have operational experience, not just certification-level familiarity.

**Architecture deep dive**: A one-hour session where you design a system from scratch. The interviewer will give you a problem statement and let you drive. More on the common design prompts below.

**Hands-on or whiteboard round**: Some companies give you a real environment (or an account in a sandbox) and ask you to diagnose a problem — a Lambda function that is hitting rate limits, an RDS instance with high read latency, a misconfigured security group blocking traffic. This tests operational depth.

**Cost and optimization round**: Common at companies where cloud cost is a significant budget item. You will be given an architecture diagram and asked to identify cost optimization opportunities. Know Reserved Instances, Savings Plans, spot instances, right-sizing, S3 storage tiers, and data transfer costs.

**Behavioral and leadership round**: How you have influenced architectural decisions you disagreed with, how you have brought engineering teams along on a migration or compliance change, how you have handled a production incident.

## The AWS Well-Architected Framework: Five Pillars in Practice

The Well-Architected Framework is the baseline mental model for cloud architecture interviews. Do not just know the names of the pillars — know the specific questions they generate.

### Operational Excellence

"How do you know when something is broken before your users do?" Questions here are about observability — CloudWatch metrics, logs, and alarms; distributed tracing with X-Ray; synthetic monitoring; runbooks and operational procedures. Interviewers want to see that you design for operations from the start, not as an afterthought.

Key pattern: operational readiness reviews (ORRs) before launching a new service, game day exercises to test failure hypotheses, post-mortems that produce systemic improvements rather than blame.

### Security

Shared responsibility model is table stakes: AWS secures the infrastructure (physical data centers, hypervisors, managed service control planes); you secure everything you run on it (OS patches on EC2, S3 bucket policies, IAM permissions, application code). Where the line falls depends on the service — for Lambda, AWS handles the runtime environment; for EC2, you own the OS.

Key pattern: least-privilege IAM everywhere, VPC private subnets for data tiers, GuardDuty for threat detection, CloudTrail for audit, AWS Config for compliance drift detection, Macie for sensitive data discovery in S3.

### Reliability

"What happens when an AZ goes down?" This is the most common reliability framing in interviews. Your answer should cover which components are multi-AZ, which have automated failover, what the failover time is (RDS Multi-AZ failover typically takes 60-120 seconds — this matters for RPO/RTO calculations), and what happens to in-flight requests during failover.

Key concepts: **RPO** (Recovery Point Objective — maximum acceptable data loss, measured in time), **RTO** (Recovery Time Objective — maximum acceptable downtime). A business might say "we can lose at most 5 minutes of data (RPO=5min) and tolerate at most 30 minutes of downtime (RTO=30min)." Your architecture has to satisfy both.

### Performance Efficiency

Right-sizing compute, choosing the right storage type for the access pattern (block storage vs. object storage vs. file storage vs. in-memory), and using CDN and caching to reduce latency and origin load. Interviewers will give you a slow-API scenario and expect you to diagnose: is it a database query problem, a compute saturation problem, a cold-start problem (Lambda), or a network latency problem?

Key pattern: CloudFront for static and dynamic content, ElastiCache Redis for session storage and hot-path caching, read replicas for read-heavy database workloads, connection pooling (RDS Proxy) for Lambda-to-RDS connections.

### Cost Optimization

Cloud spend is a product of resource type, resource size, and utilization rate. The four levers are:
1. **Right-sizing**: Is the instance class actually appropriate for the workload? CloudWatch CPU/memory metrics tell you. A t3.xlarge running at 5% CPU is a candidate for a t3.medium.
2. **Pricing models**: On-Demand for variable/unpredictable workloads, Reserved Instances (1-year or 3-year commitment for up to 72% discount) or Savings Plans (more flexible commitment) for steady-state workloads, Spot instances for fault-tolerant batch workloads (can be interrupted with a 2-minute notice).
3. **Storage tiers**: S3 Intelligent-Tiering, Glacier for archival, EBS gp3 vs. io2 for block storage (gp3 is almost always the right default unless you need >16,000 IOPS).
4. **Data transfer**: Intra-AZ traffic is free; inter-AZ traffic costs money; internet egress is the most expensive. Design your architecture to minimize unnecessary data movement — use VPC endpoints to keep S3/DynamoDB traffic within the AWS network, co-locate compute and databases in the same AZ where possible.

## Multi-Region vs. Multi-AZ: The Decision Framework

This is one of the most common architecture decision questions. Many candidates conflate multi-AZ with multi-region and treat them as points on a spectrum. They are fundamentally different things.

**Multi-AZ** is the default reliability pattern for any production workload. AWS Availability Zones are independent data centers within a region, connected by low-latency (<2ms) high-bandwidth links. RDS Multi-AZ, ECS tasks across multiple AZs, ALB distributing traffic — this is table stakes, not differentiation.

**Multi-region** is a choice you make when you need to meet one or more of these requirements:
- **Latency**: Users in Asia Pacific can get 200ms+ to a US East endpoint. A Singapore or Tokyo region deployment reduces that to 20-30ms.
- **Data residency**: GDPR and local data laws may require that European user data never leaves an EU region.
- **Disaster recovery with very aggressive RTO**: If you need to survive an entire AWS regional failure (which is rare but has happened — us-east-1 has had significant incidents), you need a secondary region that is pre-warmed, not cold.

Multi-region is operationally expensive. You now have two (or more) deployments to manage, data replication to operate (Aurora Global Database, DynamoDB Global Tables, S3 replication), and routing logic (Route 53 with latency-based or geolocation routing, or active-passive with health-check failover). The additional cost and operational burden needs to be justified by the requirement.

In interviews, when asked to design a multi-region system, start by asking which of these requirements is driving it. Interviewers value the question more than they value a candidate who immediately starts drawing a two-region diagram.

## Infrastructure as Code: Terraform vs. CloudFormation vs. CDK

This comes up frequently and the answer is genuinely nuanced:

**Terraform**: Multi-cloud, strong community module ecosystem (Terraform Registry), declarative HCL, mature state management (remote state in S3 with DynamoDB locking), provider-based architecture means you can manage AWS alongside Cloudflare, Datadog, GitHub, etc. in a single workflow. The trade-off: state management complexity, the potential for state drift, and the need to manage the Terraform binary and version.

**CloudFormation**: Native to AWS, deep integration with AWS services (some new services only have CloudFormation support before they get a Terraform provider), no state file to manage (AWS manages the state), stack drift detection built in, native integration with AWS Service Catalog and AWS Control Tower. The trade-off: verbose JSON/YAML, slower feedback loops (stack updates can be slow and difficult to debug), no cross-cloud applicability.

**CDK (Cloud Development Kit)**: Write infrastructure in TypeScript, Python, Java, or Go and synthesize it to CloudFormation. Best of both worlds in some ways — type safety, IDE completion, reusable constructs as npm/PyPI packages — but you are still ultimately deploying CloudFormation under the hood, which means you inherit its limitations. The cognitive overhead of understanding what CloudFormation is generated is a real cost.

In interviews, the expected answer for "which would you choose?" is: Terraform for organizations with multi-cloud footprints or strong DevOps culture, CDK for organizations that want type-safe IaC with deep AWS integration and can accept CloudFormation's constraints, CloudFormation for organizations that want AWS-native and minimal toolchain. The wrong answer is asserting one is always right.

## Serverless vs. Container vs. VM: The Real Tradeoffs

**Lambda (serverless)**: Best for event-driven workloads with variable or unpredictable traffic patterns — API backends, file processing pipelines, cron jobs, stream consumers. Eliminates server management. Constraints: 15-minute maximum execution time, cold start latency (can be mitigated with Provisioned Concurrency but at cost), 10GB maximum memory, 512MB-10GB ephemeral storage, concurrency limits per region. Connection pooling to RDS requires RDS Proxy because Lambda functions can exhaust the RDS connection pool at scale.

**ECS / EKS (containers)**: Best for long-running services, workloads that exceed Lambda limits, applications that need persistent processes (WebSockets, gRPC streaming), or applications where the team already has container expertise. ECS with Fargate eliminates EC2 management; ECS with EC2 gives more control over instance types (useful for GPU workloads or specific hardware). EKS is Kubernetes — bring it only if you need the ecosystem (Helm charts, Kubernetes-native tooling, multi-cloud portability). Do not bring Kubernetes to a team that does not have Kubernetes expertise; the operational overhead is significant.

**EC2 (VMs)**: Best for workloads that require specific instance types (GPU, high-memory, high-IOPS storage), applications that cannot be containerized, lift-and-shift migrations, and workloads where you need OS-level control. EC2 Auto Scaling Groups with Launch Templates are the standard pattern for production. The operational burden (OS patching, monitoring agents, AMI management) is real — if a container or serverless option meets the requirements, prefer it.

## Common Design Questions: Worked Approaches

### Design a Highly Available E-Commerce Platform

Start by clarifying the requirements: expected traffic (requests per second at peak), consistency requirements (can inventory counts be eventually consistent?), what "highly available" means to them (99.9%? 99.99%?), and data residency requirements.

A standard answer:
- Route 53 with latency-based routing and health checks to ALB
- ALB distributing across ECS Fargate tasks (or EC2 ASG) in multiple AZs
- Aurora PostgreSQL Multi-AZ for transactional data (inventory, orders, user accounts) — Aurora because it handles read scaling better than standard RDS Multi-AZ, with up to 15 read replicas and automatic failover typically under 30 seconds
- ElastiCache Redis cluster for session storage, shopping cart (can tolerate loss on node failure), and product catalog caching
- S3 + CloudFront for static assets (images, CSS, JS) — CloudFront with origin failover to a secondary S3 bucket in a second region for resilience
- SQS for decoupling order processing from inventory updates and notification emails
- CloudWatch alarms driving Auto Scaling policies — scale out when CPU > 70% for 2 consecutive minutes

The discussion that impresses: when should inventory reads hit the cache vs. the database? If you cache inventory counts, you might show 3 items in stock when there are actually 0 (cache invalidation lag). For e-commerce, this is a real business problem — talk through the tradeoff between cache hit rate/performance and consistency.

### Design a Data Lake

A data lake ingests raw data from multiple sources, stores it in a queryable format, and serves analytics workloads.

Key components:
- **Ingestion layer**: Kinesis Data Firehose for streaming data (clickstream, events), AWS DMS for database change data capture, S3 Transfer Acceleration or Snowball for large batch migrations
- **Storage**: S3 as the backbone — raw zone (unprocessed, compressed originals), curated zone (transformed, validated, partitioned Parquet files), consumption zone (aggregated tables optimized for specific query patterns)
- **Processing**: AWS Glue for ETL (serverless Spark), EMR for large-scale transformations where you need more control, Lambda for lightweight transformations on streaming data
- **Catalog**: AWS Glue Data Catalog to make S3 data discoverable to query engines
- **Query**: Athena for ad-hoc SQL queries over S3 (pay per TB scanned — partition your data by date and filter on partition columns to control cost), Redshift Spectrum for complex analytics where you need the Redshift optimizer, QuickSight for business intelligence dashboards

Partitioning strategy: partition by `year/month/day/hour` for time-series data so queries can skip irrelevant partitions. Converting from JSON to Parquet reduces Athena query cost by 60-80% because Parquet is columnar and only the needed columns are read.

### Design a Multi-Tenant SaaS Platform

Multi-tenancy has three standard isolation models:

**Pool model**: All tenants share infrastructure (same database tables with a tenant_id column, same ECS cluster). Cheapest to operate, hardest to ensure isolation. Appropriate for SMB SaaS where per-tenant cost is a primary concern.

**Silo model**: Each tenant gets dedicated infrastructure (their own RDS instance, their own ECS service). Maximum isolation, highest cost, easy compliance story. Appropriate for enterprise SaaS with data isolation requirements.

**Bridge model**: Shared compute, isolated storage (each tenant gets their own database schema or their own S3 prefix). A reasonable middle ground. RDS supports multiple schemas in a single PostgreSQL instance.

In the interview, lead with the question: what is the tenant size and count? 10,000 SMB customers suggests pool or bridge. 50 enterprise customers with strict data isolation requirements suggests silo. The right answer is always driven by the requirements.

## AWS Service Depth: The Decision Frameworks

### ECS vs. EKS

Use ECS when: your team is AWS-first and wants the lower operational overhead, you do not need the Kubernetes ecosystem (Helm, service mesh, custom controllers), and you want tight native AWS integration (IAM task roles, CloudMap service discovery, CloudWatch Container Insights).

Use EKS when: you need Kubernetes-specific tooling or portability, you have existing Kubernetes expertise on the team, or you need features Kubernetes has that ECS does not (custom schedulers, CRDs, complex network policies).

Both run on Fargate (serverless, no EC2 management) or EC2 (more control, lower cost at scale).

### RDS vs. Aurora vs. DynamoDB

**RDS (PostgreSQL/MySQL)**: Use when you need a relational database, the application is already written against standard PostgreSQL/MySQL, and you do not need Aurora's advanced scaling features. Multi-AZ for HA, read replicas for read scaling.

**Aurora PostgreSQL/MySQL**: Use when you need faster failover (< 30 seconds vs. RDS Multi-AZ's 60-120 seconds), more read replicas (up to 15 vs. RDS's 5), or Aurora Serverless v2 (auto-scales compute, good for variable workloads). Aurora is roughly 2x the cost of equivalent RDS but 5x the performance per the AWS marketing. For most production relational workloads, Aurora is the right default.

**DynamoDB**: Use when: your access patterns are simple and well-defined (you know the primary key structure), you need single-digit millisecond latency at any scale, you need automatic horizontal scaling without operational intervention, or you need multi-region active-active replication (DynamoDB Global Tables). Do NOT use DynamoDB if you need: arbitrary SQL queries, complex joins, or if your access patterns are still evolving (DynamoDB schema changes and GSI management can be painful mid-evolution).

The classic DynamoDB failure mode: a team uses it because "it scales infinitely" and then discovers at 6 months that their analytics queries require full table scans, which cost a fortune and are slow. DynamoDB is a key-value/document store with specific query patterns — choose it for those patterns, not as a default.

## Behavioral: What Architects Are Evaluated On

**Technical judgment under ambiguity**: Interviewers want to see that you can make a defensible architectural decision without perfect information. "I don't have enough data to know for certain, but based on X and Y, I would start with Z and instrument it to validate the assumption" is the right answer structure.

**Cost consciousness**: Cloud architects who treat spend as an engineering metric — not just an accounting line — are rare and valued. Be ready to give concrete cost estimates for your designs ("this would add roughly $400/month for a Multi-AZ RDS instance at the size we discussed") and to identify the cost drivers in any architecture.

**Influencing without authority**: Architects often cannot mandate choices — they have to convince. Talk about how you have made a case for a migration or a refactor, how you handled resistance from teams who did not want to change, and how you ensured adoption of standards you wrote.

**Incident ownership**: What was the most serious production issue you were involved in? How did you diagnose it? What was the customer impact? What changed afterward? Interviewers are listening for calmness under pressure, systematic diagnosis, and follow-through on improvement.

## Preparation Timeline

**Six weeks out**: If you do not have the AWS Solutions Architect Associate or Professional certification, decide whether to pursue it. The SAA-C03 (Associate) exam is a good forcing function for learning service breadth. The SAP-C02 (Professional) is appropriate for architect roles. Study using Adrian Cantrill's course or the official AWS materials.

**Four weeks out**: Work through the three canonical design problems (e-commerce platform, data lake, multi-tenant SaaS) until you can draw each on a whiteboard in 20 minutes with no prompting. Then practice with variations — what changes if you need 99.99% availability? What changes if you need to cut cost by 30%?

**Two weeks out**: Review the Well-Architected Framework review questions (available free from AWS). Practice walking through an architecture you know against each pillar and identifying gaps.

**One week out**: Study the specific services used most in the job description. If they mention Kafka, understand MSK. If they mention Kubernetes, be ready for EKS depth. If they mention Snowflake or Databricks, understand how those integrate with AWS networking and IAM.

**Day of**: Draw before you talk. Grab the whiteboard or your notepad, sketch the components, and then walk the interviewer through it. This slows you down productively, gives the interviewer something to point at, and ensures you are designing, not just narrating.

## Practical Advice

**Know your numbers**: What is the approximate latency of a cross-AZ call? (~1ms within a region.) What is S3 per-GB cost in US East 1? (~$0.023.) What is approximate Lambda cost for 1 million invocations? (~$0.20 per million requests + compute time cost.) Knowing rough magnitudes signals hands-on experience.

**Build something real**: The strongest candidates have personal AWS projects — a home lab with a VPC, an actual deployed architecture they have evolved, experience running real workloads that generated real bills and real incidents. This is what separates someone who has studied cloud from someone who has operated in it.

**Understand the failure modes of managed services**: Interviewers at senior levels will probe whether you understand that DynamoDB has hot partition problems, that Lambda cold starts are a real latency concern, that RDS Multi-AZ failover causes brief downtime, that S3 eventual consistency was replaced with strong consistency in December 2020. Knowing the edges and gotchas of services you recommend is the mark of operational depth.

**Use the Well-Architected Framework as a structure in real-time**: In a design round, it is completely appropriate to say "let me walk through this against the five pillars." Interviewers will follow along and it ensures you do not forget a dimension. Operational excellence, security, reliability, performance efficiency, cost optimization — in that order.

Cloud architecture at scale is fundamentally about making good decisions with incomplete information under real constraints of time, cost, and organizational capability. The candidates who succeed in these interviews are the ones who have internalized the decision frameworks deeply enough that they can apply them confidently while thinking out loud — and who have enough operational scar tissue to know where each architectural choice tends to fail in practice.
