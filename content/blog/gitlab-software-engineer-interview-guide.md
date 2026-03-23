---
title: "GitLab Software Engineer Interview Guide"
description: "GitLab engineering interviews: all-remote culture, DevSecOps platform architecture, Git at scale, CI/CD pipeline design, and what candidates need to know for backend and platform roles."
date: "2026-03-19"
category: "Company Interview Guides"
---

GitLab occupies a unique position in the software industry — it is simultaneously a company that builds a DevSecOps platform and one of the most deliberate examples of fully distributed engineering at scale. Interviewing at GitLab is not just a technical evaluation; it is also a cultural one, and candidates who treat those two dimensions as separate will be underprepared.

## The All-Remote Culture and Why It Shapes Interviews

GitLab has been all-remote since its founding, long before it became fashionable. Their entire operating model is codified in the GitLab Handbook, a publicly readable document that covers everything from how to run a one-on-one to how to escalate a security incident. Handbook-first is not a slogan — it is literally the default mechanism for making decisions and communicating norms. When a process is not in the handbook, it effectively does not exist yet.

For candidates, this matters at the interview stage in two concrete ways. First, expect questions about how you have worked asynchronously in the past. GitLab interviews will probe for examples of async communication, written clarity, and the ability to make decisions without being in the same room as your teammates. Second, expect behavioral questions framed around values from the handbook: collaboration, results, efficiency, diversity, iteration, and transparency (the CREDIT values). These are not abstract platitudes — interviewers will be looking for evidence of these values in specific past situations.

If you are accustomed to co-located engineering cultures, you should think carefully before your interviews about how you demonstrate thoughtful written communication, how you handle disagreement asynchronously, and how you contribute to distributed team processes.

## The Technology Stack

GitLab's platform is large and has grown organically over many years. The main application — the Rails monolith at `gitlab-org/gitlab` — is one of the largest Ruby on Rails codebases in existence. The backend is primarily Ruby, with Rails handling the web layer, Sidekiq handling background jobs, and a significant portion of business logic spread across service objects and workers. The frontend is Vue.js. The primary database is PostgreSQL, and Redis is used extensively for caching, feature flags, distributed locks, and pub/sub patterns.

Go appears in the infrastructure and performance-critical components. Gitaly, the service responsible for all Git repository access, is written in Go. Workhorse, the reverse proxy layer that handles large file uploads and downloads and offloads work from Rails, is also Go. If you are interviewing for a platform, infrastructure, or backend-adjacent role, expect Go to come up.

Kubernetes and cloud infrastructure (particularly GCP for GitLab.com) are relevant for SRE and platform roles. GitLab's own CI/CD system is used to build and ship GitLab itself, which means the engineering teams eat their own cooking daily and have deeply practical intuitions about where CI systems break under load.

## Core Technical Interview Themes

### Git Storage at Scale with Gitaly

Before Gitaly existed, GitLab Rails called Git commands directly via shell — a common early architecture that does not scale. Gitaly was introduced to centralize all Git storage access behind a gRPC service. This decoupling allows horizontal scaling of Git storage separately from the application layer and is a prerequisite for features like Geo (disaster recovery and geographic replication).

If you are interviewing for a role that touches Gitaly or storage, expect questions about how you would design a system that routes repository access requests across a fleet of Gitaly nodes, handles consistency during failover, and serves both read-heavy and write-heavy workloads. Understanding the tradeoffs between strong consistency (required for operations like branch protection checks before a merge) and eventual consistency (acceptable for things like repository statistics) is exactly the kind of nuance GitLab engineers think about daily.

### CI/CD Pipeline Execution

GitLab's CI/CD system is one of its most-used features and one of its most complex subsystems. Pipelines are defined in `.gitlab-ci.yml`, parsed and validated at pipeline creation time, and then dispatched to runners — ephemeral agents that execute jobs in isolated environments (Docker containers, VMs, Kubernetes pods, or even bare shell). The coordination layer inside GitLab Rails is responsible for job queuing, assignment to runners, status polling, and artifact collection.

Technical interviews for backend roles often explore this domain. A common system design question is to walk through how you would design a CI pipeline execution engine from scratch: how jobs are enqueued, how runners poll for available work, how you handle job retries on runner failure, how you model DAG dependencies between jobs, and how you surface real-time status to users. The design surface is rich and touches queuing theory, distributed systems consistency, database design for high write throughput, and WebSocket/SSE for live UI updates.

### Merge Request Workflows and Permissions

Merge requests are the primary unit of collaboration at GitLab and are deeply integrated with nearly every other feature — code review, CI pipelines, approvals, security scans, deployment tracking. Interview questions in this space often focus on access control (how you model project memberships, protected branch rules, approval rules, and CODEOWNERS in a way that is both flexible and auditable), and on how you would design the notification and subscription model for a feature like merge request reviews without generating email spam at scale.

## System Design: What to Prepare

The two system design scenarios most likely to come up in GitLab backend interviews are a CI/CD execution engine and a distributed Git repository storage system at millions-of-repos scale. For the CI/CD design, your answer should articulate how you separate the control plane (job scheduling, state management, UI) from the data plane (runner execution), how you handle partial failures, and how you scale the polling mechanism as the runner fleet grows. For the Git storage design, focus on partitioning strategy, metadata vs. object storage separation, consistency requirements per operation type, and how you would implement replication for Geo-like use cases.

Be prepared to go deep on PostgreSQL — GitLab has invested heavily in database sharding and decomposition (splitting the monolithic database into logical domains), and there is a real expectation that senior backend engineers understand query performance, indexing strategies, and migration safety in a zero-downtime deployment environment.

## GitLab vs. GitHub: Competing Products, Different Cultures

The comparison is inevitable. Both GitLab and GitHub build developer platforms on top of Git, but the companies are quite different in culture and architecture. GitHub was acquired by Microsoft and operates with a more traditional hybrid-remote culture. GitLab is fully independent (as of this writing) and fully remote by design. GitHub's backend has historically leaned Go-heavy in its core infrastructure, while GitLab's heart is a Ruby on Rails monolith with Go at the edges.

Culturally, GitLab's handbook-driven transparency means that a great deal of their engineering decision-making is visible in public issues, RFCs, and handbook pages. Candidates can and should read GitLab's engineering blog and public issues before interviewing — it is unusually possible to understand the technical direction and open debates at the company before you ever walk into the interview. GitHub's culture is less publicly documented, which makes it harder to calibrate to in advance.

The interview process itself reflects these cultural differences. GitLab interviews weight async communication skills heavily and may include a take-home component where the artifact is as important as the solution. GitHub interviews tend to be more similar to the standard FAANG interview playbook: structured coding rounds, systems design, and behavioral.

## Preparing for the GitLab Interview Loop

Read the handbook before your interviews — specifically the engineering section and the values pages. This is not performative; GitLab interviewers genuinely use the handbook as a shared reference point and will be impressed by candidates who engage with it concretely. Study Gitaly's architecture using GitLab's public documentation and engineering blog posts. Practice system design problems that involve high-write-throughput coordination, distributed job queuing, and access control modeling. And prepare clear examples from your own experience of working asynchronously, writing up decisions in documents rather than in meetings, and iterating in public rather than waiting for perfection.

GitLab interviews are technically rigorous and culturally specific. Candidates who take both dimensions seriously — and who can credibly articulate why all-remote engineering appeals to them — will find GitLab a genuinely differentiated place to interview and, if hired, to work.
