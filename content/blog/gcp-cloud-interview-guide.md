---
title: "Google Cloud Platform (GCP) Interview Guide: BigQuery, Cloud Run, and GCP Architecture"
description: "GCP interview preparation for software engineers — core services (BigQuery, Cloud Run, GKE, Spanner), GCP architecture patterns, and how GCP differs from AWS in interviews."
date: "2026-03-20"
category: "Cloud"
---

# Google Cloud Platform (GCP) Interview Guide: BigQuery, Cloud Run, and GCP Architecture

GCP interview questions surface in two contexts: interviews at Google itself (where GCP is the default infrastructure) and interviews at companies that have standardized on Google Cloud. The questions differ subtly from AWS questions — GCP has distinct strengths in data engineering and serverless, and interviewers will probe whether you know where GCP shines versus where it defers to AWS.

## GCP Core Services You Must Know

**Compute Engine** is GCP's IaaS layer — virtual machines on Google's network. Know the instance families (general-purpose N-series, compute-optimized C-series, memory-optimized M-series) and preemptible/spot instances for cost reduction. Comparable to EC2.

**Cloud Run** is GCP's serverless container platform. You push a container image, and Cloud Run handles scaling (including scale-to-zero). No cluster management, billed per 100ms of CPU and memory. This is where GCP genuinely leads — Cloud Run's cold start performance and HTTP/2 support are strong interview talking points. Comparable to AWS App Runner or Fargate, but more opinionated about the deployment model.

**GKE (Google Kubernetes Engine)** is managed Kubernetes. GCP invented Kubernetes, so GKE is generally considered the most mature managed Kubernetes offering. Know Autopilot mode (GKE manages nodes, you pay per pod) vs Standard mode (you manage node pools).

**Cloud Storage** is GCP's object storage — conceptually identical to S3. Know storage classes: Standard, Nearline (access less than once per month), Coldline, Archive. Lifecycle policies work the same way as S3 lifecycle rules.

**BigQuery** is GCP's flagship data warehouse and the service most interviewers associate with GCP's unique value. Serverless, columnar, petabyte-scale SQL analytics. Key interview points: you do not provision capacity (on-demand vs flat-rate billing), data is stored in Capacitor format (proprietary columnar), queries are billed by bytes scanned. Partitioning (by date/column) and clustering (physical sort order) reduce scan costs dramatically.

**Pub/Sub** is GCP's managed messaging service, comparable to SNS+SQS combined. Push subscriptions deliver to endpoints; pull subscriptions let consumers poll. Used for event-driven architectures and decoupling microservices. Know at-least-once delivery semantics.

**Cloud Spanner** is GCP's globally distributed relational database — the only production-grade system that offers both horizontal scalability and ACID transactions with external consistency. It uses TrueTime (GPS + atomic clocks) for global timestamps. Use it when you genuinely need global consistency at scale; it is expensive, and most applications do not need it.

## GCP vs AWS: What Interviewers Actually Ask

Interviewers rarely ask you to recite service comparisons. They ask architecture questions and probe whether you reach for the right GCP tool. The meaningful differences:

- **Data engineering**: GCP is the clear choice. BigQuery + Dataflow (managed Apache Beam) + Pub/Sub is a complete serverless data pipeline with no cluster management. AWS has Redshift + Glue + Kinesis but requires more configuration.
- **Kubernetes**: GKE Autopilot is more hands-off than EKS. If the question is "I want Kubernetes with minimal ops overhead," GKE wins.
- **Networking**: GCP's global VPC is a single entity — no concept of "regions" for the VPC itself. AWS VPCs are regional. This simplifies multi-region networking on GCP.
- **Serverless functions**: Cloud Functions (event-driven, comparable to Lambda) vs Cloud Run (containerized, more flexible). Know when to choose which.

## Data Engineering on GCP

If you are interviewing for a data-heavy role on GCP, you need the full pipeline: **Pub/Sub** (ingest events) → **Dataflow** (transform via streaming or batch, managed Apache Beam) → **BigQuery** (warehouse) → **Looker/Data Studio** (visualization).

BigQuery ML allows you to train and run ML models in SQL — interviewers occasionally ask about this for data science roles. Know that BigQuery supports federated queries against Cloud Storage and Cloud Bigtable.

**Cloud Bigtable** is the wide-column NoSQL store for high-throughput, low-latency workloads (time-series, IoT, AdTech). Comparable to HBase (Bigtable was the inspiration for HBase). Choose it when you need single-digit millisecond reads at millions of operations per second.

## IAM on GCP

GCP IAM uses **principals** (Google accounts, service accounts, groups, domains) and **roles** (collections of permissions). Three types of roles: primitive (Owner/Editor/Viewer — avoid these, they are too broad), predefined (e.g., `roles/bigquery.dataViewer`), and custom. Service accounts are identities for workloads; prefer Workload Identity Federation over downloading service account keys.

Key interview question: "How would you give a Cloud Run service access to a BigQuery table?" Answer: create a service account, grant it `roles/bigquery.dataViewer` on the dataset, and configure Cloud Run to run as that service account. No key files needed.

## Common GCP Interview Questions

- "Design a real-time analytics pipeline that processes 1M events per second." — Pub/Sub → Dataflow streaming → BigQuery with streaming inserts.
- "When would you choose Cloud Spanner over Cloud SQL?" — Global writes with strong consistency. Cloud SQL (managed PostgreSQL/MySQL) for single-region relational workloads; Spanner when you need multi-region writes with ACID.
- "How does BigQuery achieve query performance without indexes?" — Columnar storage, Dremel query execution, slot-based parallelism, and partitioning/clustering as the user-facing performance levers.
- "What is the difference between Cloud Run and Cloud Functions?" — Cloud Run is container-based and handles any HTTP workload; Cloud Functions is event-triggered and limited to single functions. Cloud Run has replaced Cloud Functions for most new development.

## Preparation Approach

If you do not have hands-on GCP experience, spend a few hours with the GCP free tier running BigQuery queries against public datasets and deploying a containerized service to Cloud Run. Understanding the operational experience — console navigation, IAM assignment, monitoring with Cloud Monitoring — adds credibility that pure study cannot.
