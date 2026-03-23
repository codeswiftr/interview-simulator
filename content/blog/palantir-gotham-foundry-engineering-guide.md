---
title: "Palantir Gotham and Foundry: A Technical Engineering Guide"
description: "A deep dive into what Palantir actually builds — the ontology-driven data model, the two core platforms, and what engineers really do there. Covers architecture, engineering challenges, and how Palantir interviews."
date: "2026-03-19"
category: "Company Deep Dives"
---

## What Palantir Actually Builds

Most companies build software that stores and processes data. Palantir builds software that makes sense of data that was never designed to work together. That distinction shapes everything — the architecture, the engineering culture, and what they test in interviews.

Palantir has two platforms that serve fundamentally different markets but share the same underlying technical model:

**Gotham** is built for intelligence and defense agencies — the NSA, CIA, DHS, UK GCHQ, military contractors. It ingests streams of surveillance data, financial records, communications intercepts, and geospatial feeds, then surfaces connections across them. The canonical use case is counterterrorism analysis, but it's also used for fraud detection at the FBI, battlefield logistics, and signals intelligence.

**Foundry** is the commercial data operations platform. A pharma company uses it to unify clinical trial data, EHR records, and supply chain systems. An airline uses it to coordinate fleet maintenance, crew scheduling, and logistics data. The problems are less dramatic than Gotham's but structurally identical: heterogeneous data sources that need to behave as a coherent system.

Both platforms run on the same core abstraction: the ontology.

## The Ontology: Palantir's Central Architectural Bet

The ontology is the piece of Palantir's architecture that most engineers outside the company don't fully understand until they work there.

Rather than building a schema around tables and joins, Palantir models the world as **objects and links**. A Person is an object. A Phone Number is an object. The relationship between them — *has_device* — is a link. An Event (a wire transfer, a border crossing, a hospital admission) is an object with temporal properties. The ontology is the formal specification of what objects exist, what properties they have, and how they relate.

This matters because it separates the semantic model from the underlying storage. Behind the objects, data can live in Postgres, Spark tables, S3, external REST APIs, or legacy Oracle databases. The ontology layer abstracts that away. Engineers building analysis applications write against objects and links, not SQL.

The practical payoff: an analyst can query "show me everyone who flew into Hamburg in the 48 hours before an event, who also has a phone contact in common with a flagged individual" without any SQL, without any knowledge of which backend systems hold each piece of data, and without a data engineer writing a one-off integration first.

Building and maintaining the ontology is a real engineering problem. You need:
- Schema resolution when two source systems represent the same concept differently
- Change data capture pipelines that keep object properties current
- A graph query engine that can traverse link relationships at scale
- Permission controls that are attribute-based, not just role-based (an analyst can see a person object but not the raw intercept that populated a property on that object)

## Engineering Challenges Worth Understanding

### Integrating Disparate Data Sources

Palantir's connectors ingest from hundreds of source types: JDBC databases, REST APIs, S3, Kafka streams, SFTP batch files, government-specific formats like NIEM XML. Each source has its own schema, its own reliability characteristics, and its own update frequency. Building a pipeline that maps source rows to ontology objects requires schema mapping, entity resolution (deciding two records in different systems refer to the same real-world entity), and continuous reconciliation as source schemas change.

The hard part isn't the ETL itself — it's the entity resolution. If the FBI database uses Social Security Numbers as identifiers and the Interpol database uses passport numbers, how do you decide these two records describe the same person? Palantir has built probabilistic matching infrastructure around names, addresses, biometric identifiers, and behavioral patterns. This is fundamentally a machine learning and graph problem embedded inside what looks like a data pipeline problem.

### Graph-Based Querying at Scale

The Gotham query model is fundamentally graph traversal. Finding third-degree connections between a set of seed entities, filtering on properties at each hop, and returning ranked results — this is not what relational databases are optimized for. Palantir uses a custom graph query execution layer on top of distributed storage. Engineering challenges include:

- Query planning for arbitrary-depth traversals with predicate pushdown
- Caching strategies for hot subgraphs
- Incremental query updates when new data arrives (the answer to a standing query should update, not require a full recompute)

### Privacy and Access Control

Both Gotham and Foundry deal with sensitive data under strict regulatory regimes. Access control at Palantir is not table-level or column-level — it is cell-level and purpose-bound. A field analyst can see that a person object exists and has a location property, but the raw GPS coordinates may be masked. A supervisor with a different clearance sees the actual coordinates. An auditor sees the access log for both queries.

Implementing this requires tagging every data element with sensitivity classifications and evaluating policy at query time against the requesting principal's attributes. It's an attribute-based access control (ABAC) system where the policy engine sits in the query path, which has obvious performance implications.

### Air-Gapped Deployments

Government deployments frequently run in classified networks with no internet connectivity. Palantir's software must operate fully offline, which means no SaaS dependencies, no external CDNs, no cloud-hosted license validation. Every service must be self-contained and deployable into an air-gapped environment via physical media. This shapes how updates are delivered (offline update bundles), how telemetry works (it doesn't, or gets batched for manual extraction), and how engineers test their code (air-gapped staging environments that mirror production classified networks).

## What Makes Palantir Engineering Unusual

**Forward-Deployed Engineers (FDEs).** Palantir embeds engineers directly at customer sites for weeks or months. An FDE at a pharmaceutical company isn't writing features back at HQ — they're on-site helping the customer's data scientists configure the ontology, debug pipeline failures, and customize the platform to the domain. This role blurs the line between software engineer and solutions architect. Palantir interviews for and promotes engineers who can do both.

**Data-model-first development.** At most companies, engineers build features against an existing data model. At Palantir, defining the data model *is* the feature. Getting the ontology right for a new customer domain — what objects to create, what properties to expose, how to handle historical data — is the primary engineering decision. Downstream tooling (search, visualization, alerting) often works without additional code once the ontology is configured correctly.

**Operating in regulated environments.** FedRAMP, IL4, IL5, IL6 authorizations. ITAR compliance. HIPAA. Engineers need to understand the compliance implications of their technical decisions. Adding a logging call that captures PII in a HIPAA-regulated deployment is a compliance incident, not just a code smell.

## The Interview Process

Palantir's process typically runs four to six rounds: a recruiter screen, a technical phone screen, a Hackerrank or similar take-home, and then an on-site or virtual on-site with four to five interviews.

**What they actually test:**

Coding rounds focus on graph problems, tree traversals, and data structure design — consistent with the ontology-graph model that underlies their products. You are unlikely to get a dynamic programming puzzle. You are likely to get questions about designing a graph traversal, implementing BFS/DFS with constraints, or building a cache with specific eviction properties.

System design rounds tend to emphasize data pipelines and distributed systems. Expect questions like: design a system that ingests data from 500 heterogeneous sources and makes it queryable as a unified graph. The interviewer wants to see how you handle schema heterogeneity, consistency guarantees, and access control — not just throughput scaling.

The FDE-track interviews include a decomposition exercise: given a business problem (a hospital system wants to track patient outcomes across three disconnected EHR systems), define the ontology and describe how you would build the integrations. This tests product thinking, not just technical depth.

Palantir also runs behavioral interviews that are heavier on judgment and ambiguity tolerance than most companies. Working in classified environments, on sensitive data, means engineers encounter situations where the right technical answer and the right ethical or policy answer diverge. Interviewers probe how candidates think through tradeoffs in these situations.

**Preparation priorities:** Graph algorithms (BFS, DFS, cycle detection, shortest path), system design with an emphasis on data integration and access control, and being able to articulate tradeoffs clearly under pressure. The company hires for engineering judgment as much as raw implementation speed.
