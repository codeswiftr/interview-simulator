---
title: "Google Cloud Platform (GCP) Interview Guide: Cloud Engineer and Architect Questions"
description: "Prepare for GCP-focused cloud engineering interviews — BigQuery, GKE, Cloud Run, Pub/Sub, IAM, and how to answer Google Cloud architecture questions."
date: "2026-03-20"
category: "Cloud & DevOps"
---

# Google Cloud Platform (GCP) Interview Guide: Cloud Engineer and Architect Questions

GCP interviews appear when you're applying to Google-adjacent companies, cloud engineering roles at enterprises that have standardized on Google Cloud, or Google itself. The questions split between GCP-specific services, cloud-agnostic architecture, and data engineering (GCP is strong in data). Here's how to prepare.

## Why GCP? Know the Positioning

Interviewers often open with "why Google Cloud over AWS/Azure?" Have a genuine answer: GCP excels at data analytics (BigQuery), machine learning infrastructure (Vertex AI, TPUs), Kubernetes (Google invented it; GKE is the reference implementation), and global networking (private fiber backbone). Companies choose GCP when they're heavy on analytics or already in the Google ecosystem (Workspace, etc.).

## Core Compute: GKE and Cloud Run

**GKE (Google Kubernetes Engine):** The managed Kubernetes service. Interview topics: autopilot vs. standard mode (autopilot manages node pools, standard gives more control), workload identity for pod-level IAM, vertical and horizontal pod autoscaling, multi-cluster setups with Anthos.

Expect the question: "How do you handle pod IAM permissions in GKE?" Answer: Workload Identity — bind a Kubernetes service account to a GCP service account, allowing pods to authenticate to GCP services without credentials in environment variables.

**Cloud Run:** Fully managed serverless container platform. Scales to zero, charges per request. Best for stateless HTTP services, event-driven workloads, and microservices with variable traffic. Compare with App Engine: Cloud Run is container-based and more flexible; App Engine is more opinionated. Cloud Run vs. GKE: Cloud Run for simplicity and auto-scaling to zero; GKE for stateful workloads, complex networking, and when you need more control.

## Storage: GCS, Cloud SQL, Bigtable, Spanner

**Cloud Storage (GCS):** Object storage. Key interview topics: storage classes (Standard, Nearline, Coldline, Archive — different access frequencies), object versioning, lifecycle rules for cost management, signed URLs for time-limited access, uniform vs. fine-grained bucket IAM.

**Cloud SQL vs. Cloud Spanner:** Cloud SQL is managed PostgreSQL/MySQL — regional, familiar, appropriate for most transactional workloads. Cloud Spanner is Google's globally distributed, horizontally scalable relational database — globally consistent, handles millions of QPS, expensive. Choose Spanner when you need global consistency at scale. Most workloads don't justify Spanner's cost.

**Bigtable:** NoSQL wide-column store, inspired by Google's internal Bigtable paper. Designed for high-throughput, low-latency reads/writes at petabyte scale. Best for time-series data, IoT telemetry, and analytics workloads where you have a clear row key design. Row key design is critical — poor key design causes hotspots.

**Firestore:** Document database with real-time sync. Better for mobile/web apps needing offline support and real-time listeners. Not for high-volume analytics.

## Data: BigQuery

BigQuery is GCP's signature service and the most common interview topic for data engineering roles on GCP.

Key concepts: serverless analytics, columnar storage, separation of storage and compute, slot-based pricing vs. on-demand pricing, partitioned and clustered tables (partition on date/timestamp for cost and performance, cluster on high-cardinality columns used in WHERE clauses).

Interview question: "How do you optimize a slow BigQuery query?" Answer framework: check if you're scanning full tables (add partitioning), check column selection (avoid SELECT *, columnar storage rewards selecting only needed columns), use clustering on join/filter columns, push filters as early as possible, use APPROX_COUNT_DISTINCT for large cardinality counts.

## Messaging: Pub/Sub

Cloud Pub/Sub is GCP's managed message queue / event streaming service. Key properties: at-least-once delivery, push or pull subscription, global message ordering (with ordering keys), exactly-once processing (with deduplication windows on Pub/Sub Lite).

Interview: "Design a pipeline that processes events from Pub/Sub into BigQuery." Answer: Pub/Sub → Cloud Dataflow (Apache Beam) → BigQuery streaming inserts, or Pub/Sub → BigQuery direct subscription (now GA). Handle late data in Dataflow using watermarks and windowing.

## IAM and Security

GCP IAM: principals (users, service accounts, groups), roles (primitive, predefined, custom), policy bindings. The principle of least privilege is tested: use predefined roles when possible, create custom roles only when predefined roles are too broad.

Service accounts: the GCP-native way for services to authenticate. Best practice: each service gets its own service account with minimal permissions. Avoid using the default Compute Engine service account — it has Editor permissions project-wide.

Organization hierarchy: Organization → Folders → Projects → Resources. IAM policies are inherited downward. This is a common interview topic for enterprise GCP: how do you enforce security policies across a large organization? Answer: Organization Policies (constraints), VPC Service Controls (data exfiltration prevention), centralized logging with Log Sinks to a security project.

## Networking

VPC (Virtual Private Cloud) in GCP: global (unlike AWS where VPCs are regional), subnets are regional. Shared VPC for connecting multiple projects to a common network. VPC Peering for connecting two VPCs. Cloud Interconnect / Cloud VPN for on-premises connectivity.

Cloud Load Balancing: several types — Global External (HTTP/HTTPS, anycast IP), Regional External (TCP/UDP), Internal. GCP's global LB is unique: single anycast IP routes to the nearest healthy backend globally, providing both load balancing and global routing.

## Interview Preparation Tips

GCP interviews at cloud engineering roles often include a whiteboard architecture problem. Common: "Design a data pipeline to ingest 1 million events/second from IoT devices." Expected answer: IoT Core (or direct Pub/Sub publish) → Pub/Sub → Dataflow → Bigtable (for real-time queries) + BigQuery (for analytics).

Know the GCP decision matrix: Cloud Run vs. GKE, Cloud SQL vs. Spanner, Bigtable vs. Firestore vs. BigQuery. Being able to articulate these tradeoffs clearly is what differentiates prepared candidates.
