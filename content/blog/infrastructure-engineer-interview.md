---
title: "Infrastructure Engineer Interview Guide: Linux, Networking, and Cloud Architecture"
description: "Complete infrastructure engineer interview preparation — Linux system administration, TCP/IP and DNS deep dive, Terraform and IaC patterns, container orchestration, observability, and common infrastructure system design questions."
date: "2026-03-20"
category: "Career Guides"
---

# Infrastructure Engineer Interview Guide: Linux, Networking, and Cloud Architecture

Infrastructure engineering interviews blend deep Linux knowledge, networking fundamentals, cloud architecture, and automation. Unlike SWE interviews, you'll rarely solve LeetCode puzzles — instead you'll troubleshoot systems, design deployments, and demonstrate that you can keep production running reliably.

## Linux Fundamentals

**File system and permissions:**
- `ls -la` to view files with permissions. Permissions: `rwxrwxrwx` (owner/group/other). `chmod 755` = rwxr-xr-x.
- `find / -name "*.log" -mtime +7` — find logs older than 7 days
- `du -sh /var/log/*` — disk usage by directory
- Inodes: a file has an inode (metadata: size, permissions, timestamps, pointers to data blocks) and directory entries pointing to the inode. `df -i` shows inode usage. "No space left" with available disk space = inode exhaustion.

**Process management:**
- `ps aux` — all processes. `ps -ef` — full-format listing.
- `top` / `htop` — real-time view. CPU%, MEM%, load average.
- `kill -9 PID` — SIGKILL (unblockable, immediate termination). `kill -15` — SIGTERM (graceful). Prefer SIGTERM first.
- `strace -p PID` — trace system calls of a running process. Invaluable for debugging "what is this process actually doing."
- `lsof -p PID` — open file descriptors for a process. `lsof -i :8080` — what's listening on port 8080.

**Memory:**
- `free -h` — total/used/free memory. Buffered vs cached memory (can be reclaimed).
- `vmstat 1` — virtual memory stats per second. `si`/`so` = swap in/out (nonzero = memory pressure).
- OOM killer: when memory is exhausted, the kernel kills processes based on OOM score. Check `/proc/PID/oom_score` to understand which processes are at risk.

**Load average:** 3 numbers (1min, 5min, 15min). On a 4-core system, load of 4.0 = fully utilized. Load > core count = processes waiting for CPU.

## Networking Deep Dive

**TCP three-way handshake:** SYN → SYN-ACK → ACK. Before any data. `TIME_WAIT` state after connection close: 2×MSL (Maximum Segment Lifetime) to catch delayed packets. Large numbers of TIME_WAIT sockets can exhaust port ranges.

**DNS resolution:** Browser check → OS cache → `/etc/hosts` → resolver (usually your router or 8.8.8.8) → root nameservers → TLD nameservers → authoritative nameserver → IP. `dig +trace example.com` shows each step. TTL controls caching duration.

**Common ports to know:** 22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis), 27017 (MongoDB), 9200 (Elasticsearch), 9092 (Kafka).

**Troubleshooting toolkit:**
- `curl -v URL` — verbose HTTP request showing headers
- `netstat -tlnp` / `ss -tlnp` — listening ports with process names
- `tcpdump -i eth0 port 80` — packet capture on interface
- `nmap -sV host` — port scan with service detection
- `traceroute` / `mtr` — path to host with latency per hop

**Load balancers:** L4 (TCP) — routes by IP:port, no content inspection, lower latency. L7 (HTTP) — routes by URL, headers, cookies, can terminate TLS. Examples: HAProxy, Nginx, AWS ALB (L7) vs NLB (L4).

## Terraform and IaC

Terraform's declarative model: describe desired state, `plan` computes diff, `apply` makes it real.

**State file:** Terraform tracks actual infrastructure in a state file. Remote state (S3+DynamoDB lock) required for teams — prevents two operators from running `apply` simultaneously.

**Key commands:**
```bash
terraform init       # Initialize providers and modules
terraform plan       # Show changes to be made
terraform apply      # Apply changes
terraform import     # Import existing resource into state
terraform state mv   # Move resources between state entries
terraform destroy    # Destroy all managed resources
```

**Module patterns:** Reusable infrastructure components. A VPC module, an ECS service module, a PostgreSQL module — each encapsulates best-practice configurations. `terraform-aws-modules` on GitHub has production-quality examples.

**Drift detection:** When someone makes manual changes in the AWS console, Terraform state diverges from reality. `terraform plan` shows the drift. `terraform import` brings manual resources under management. Prevent manual changes via IAM policies that only allow Terraform's service account to make changes.

## Container Orchestration

Kubernetes core concepts (re: DevOps interview guide) — know these for infra roles too. Additional infra-specific topics:

**Cluster networking:** Pods get IPs from the cluster CIDR. Services get IPs from the service CIDR. `kube-proxy` implements service routing (iptables or IPVS rules). CNI plugins (Calico, Flannel, Cilium) handle pod-to-pod networking.

**Persistent storage:** PersistentVolume (PV) — a piece of storage provisioned by the admin or dynamically by a StorageClass. PersistentVolumeClaim (PVC) — a request for storage by a pod. StorageClass — defines how to dynamically provision PVs (EBS, EFS, local disk).

**Cluster autoscaling:** HPA scales pod replicas. Cluster Autoscaler scales nodes. KEDA (Kubernetes Event-Driven Autoscaling) scales based on queue depth, custom metrics.

## Observability Architecture

The three pillars (metrics, logs, traces) are table stakes. Infrastructure engineers also implement:

**Infrastructure metrics:** Node exporter (CPU, memory, disk, network per host), kube-state-metrics (Kubernetes object states), blackbox exporter (endpoint availability from external perspective).

**Log aggregation:** Fluentd or Fluent Bit as DaemonSet on each node. Ships container logs to Elasticsearch, Loki, or Splunk. Structured logging (JSON) is critical — free-form text logs can't be filtered at scale.

**Alerting:** Prometheus Alertmanager or Grafana Alerting. Rules: `rate(http_requests_total{status=~"5.."}[5m]) > 0.01`. Route alerts by severity, team, and product.

## Infrastructure System Design Questions

"Design a highly available PostgreSQL deployment" — primary with 2 synchronous replicas, automatic failover via Patroni or AWS RDS Multi-AZ, connection pooling via PgBouncer, read replicas for analytics load, point-in-time recovery with continuous WAL archiving.

"How would you migrate a monolith to microservices with zero downtime?" — strangler fig pattern, parallel run with traffic splitting, database decomposition via the strangler fig (APIs in front of shared DB, then split DB), contract testing between services.

"Design the infrastructure for a global SaaS application" — multi-region active-active or active-passive, global load balancer (Cloudflare, AWS Route53 latency routing), regional databases with replication, CDN for static assets, feature flags for phased rollouts, runbooks for regional failover.

