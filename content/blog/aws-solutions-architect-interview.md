---
title: "AWS Solutions Architect Interview Guide: Services, Architecture Patterns, and Well-Architected Framework"
description: "Prepare for AWS Solutions Architect interviews — core services (EC2, S3, RDS, Lambda, VPC), architecture patterns, the Well-Architected Framework, and how to design scalable, cost-effective AWS systems."
date: "2026-03-20"
category: "Cloud Engineering"
---

# AWS Solutions Architect Interview Guide: Services, Architecture Patterns, and Well-Architected Framework

AWS solutions architecture interviews appear at cloud-native companies, consulting firms, and enterprises undergoing cloud migration. They test your ability to select the right AWS services for a given scenario, architect for reliability and cost, and apply security and operational best practices. This guide covers the core knowledge and patterns you need.

## Core Compute Services

**EC2 (Elastic Compute Cloud)**: Virtual machines. Key decisions: instance type (general purpose t3/m6i, compute c6i, memory r6i, GPU p3/g4), pricing model (On-Demand, Reserved 1-3yr, Spot for interruptible workloads).

**Lambda**: Serverless functions. Scales to zero, no server management. Maximum 15-minute execution. Use for event-driven workloads: API backends, S3 event processing, scheduled tasks. Cold start latency (100-500ms) matters for latency-sensitive APIs — use provisioned concurrency to pre-warm.

**ECS/EKS**: Container orchestration. ECS (Elastic Container Service) is AWS-native and simpler. EKS (Elastic Kubernetes Service) is managed Kubernetes — use when you need Kubernetes-specific features or already have Kubernetes expertise. Fargate runs containers serverlessly without managing EC2 instances.

**Auto Scaling**: Horizontal EC2 scaling based on CloudWatch metrics (CPU, custom metrics). Define min/max/desired capacity. Use target tracking policies (maintain 70% CPU) over step scaling policies.

## Storage Architecture

**S3 (Simple Storage Service)**: Object storage. 11 nines durability. Unlimited capacity. Use for: static assets, media files, backups, data lake storage, logs. Storage classes: Standard, Intelligent-Tiering (auto-moves between tiers), Standard-IA (infrequent access), Glacier (archive, minutes-to-hours retrieval), Glacier Deep Archive (hours).

**EBS (Elastic Block Store)**: Block storage attached to EC2. Like a hard drive — formatted, mounted. GP3 (general purpose SSD) for most use cases; IO2 for high IOPS database workloads. Snapshots to S3 for backup.

**EFS (Elastic File System)**: Managed NFS. Multiple EC2 instances can mount simultaneously. Use for shared file storage across instances.

**RDS**: Managed relational databases (MySQL, PostgreSQL, Aurora, SQL Server). Multi-AZ deployments for HA (synchronous replication, automatic failover). Read replicas for read scaling (async replication). Aurora is AWS's MySQL/PostgreSQL-compatible engine with 3-5x performance improvement and serverless variant (Aurora Serverless v2).

**DynamoDB**: Fully managed NoSQL. Single-digit millisecond latency at any scale. Partitioned by hash key. DAX (DynamoDB Accelerator) for microsecond caching layer. Use for: session storage, IoT data, gaming leaderboards (use TTL for expiration).

**ElastiCache**: Managed Redis or Memcached. Redis supports persistence, pub/sub, sorted sets, streams. Memcached is simpler, multi-threaded.

## Networking: VPC Architecture

**VPC (Virtual Private Cloud)**: Your private network in AWS. Create subnets in multiple Availability Zones. 

**Public vs private subnets**: Public subnets have a route to an Internet Gateway — EC2 instances here get public IPs. Private subnets route internet-bound traffic via NAT Gateway (for outbound only).

**Security Groups**: Instance-level firewalls. Stateful — allow inbound rule automatically allows the response outbound. Default deny all inbound.

**NACLs (Network ACLs)**: Subnet-level firewall. Stateless — must explicitly allow both inbound and outbound. Ordered rule evaluation.

**Load Balancers**: ALB (Application Load Balancer) for HTTP/HTTPS — path-based routing, host-based routing, WebSocket support. NLB (Network Load Balancer) for TCP/UDP — lowest latency, static IPs, used for non-HTTP protocols.

**Route 53**: DNS service. Routing policies: Simple, Weighted (A/B testing), Failover, Geolocation, Latency-based. Health checks monitor endpoint health and trigger failover.

## The Well-Architected Framework

The five pillars provide structure for architecture reviews:

**1. Operational Excellence**: Define operations as code (CloudFormation, CDK). Make frequent, small, reversible changes. Anticipate failure. Use CloudWatch for monitoring; CloudTrail for audit.

**2. Security**: Apply least privilege (IAM roles, not root accounts). Enable all regions' security services (GuardDuty, Security Hub). Encrypt data at rest (KMS) and in transit (TLS). Use VPC endpoints to keep traffic off the public internet.

**3. Reliability**: Automatically recover from failure. Test recovery procedures. Scale horizontally. Stop guessing capacity (use Auto Scaling). Manage change through automation.

**4. Performance Efficiency**: Use serverless architectures. Go global in minutes (CloudFront CDN, multi-region deployment). Experiment with services as they evolve.

**5. Cost Optimization**: Adopt a consumption model (pay for what you use). Use Reserved Instances for predictable workloads. Right-size instances. Use S3 Intelligent-Tiering. Analyze with Cost Explorer; set budgets and alerts.

## Common Architecture Patterns

**Serverless web application**: API Gateway → Lambda → DynamoDB. CloudFront CDN for static assets in S3. Route 53 for DNS. Simple to operate, scales to zero, pay per request.

**Three-tier web application**: ALB → ECS/EC2 ASG (application tier) → RDS Multi-AZ (database tier). ElastiCache between app and DB. S3 + CloudFront for static assets.

**Event-driven architecture**: S3 event → Lambda → SQS → Lambda processors → DynamoDB. Or Kinesis for streaming data. Decouples producers from consumers; handles bursty workloads.

**Disaster recovery**: Active-Active (full multi-region, lowest RTO/RPO, highest cost), Active-Passive Warm Standby (scaled-down replica ready), Pilot Light (minimal running infrastructure, scale up on failover), Backup and Restore (cheapest, highest RTO).

## Interview Scenarios

**"Design a highly available, scalable web application"**: Multi-AZ deployment, ALB across AZs, Auto Scaling group, RDS Multi-AZ, ElastiCache, CloudFront CDN, Route 53 health checks.

**"How would you reduce costs for this architecture?"**: Reserved Instances for predictable baseline, Spot Instances for batch processing, S3 Intelligent-Tiering, right-sizing via Compute Optimizer, CloudFront to reduce origin data transfer.

**"A Lambda function is experiencing cold starts"**: Use provisioned concurrency for latency-critical paths. Reduce deployment package size. Keep Lambda warm with scheduled invocations (less reliable). Consider moving to ECS/EC2 if latency requirements are strict.

Demonstrating that you can translate business requirements into AWS service choices, articulate the trade-offs, and apply the Well-Architected Framework is the core skill these interviews assess.
