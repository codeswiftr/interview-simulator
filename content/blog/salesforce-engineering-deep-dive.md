---
title: "Salesforce Engineering Deep Dive: CRM at Enterprise Scale"
date: 2026-03-19
category: engineering
tags: [salesforce, crm, apex, multi-tenant, enterprise, interview-prep]
readingTime: 9
summary: "A technical deep-dive into Salesforce's multi-tenant architecture, metadata-driven platform, Apex governor limits, Heroku integration, and enterprise permission models. Essential reading before any Salesforce engineering interview."
---

# Salesforce Engineering Deep Dive: CRM at Enterprise Scale

Salesforce runs more than 150,000 enterprise customers — including most of the Fortune 500 — on a shared database infrastructure that has been operational since 1999. The engineering decisions made to support that scale are unusual enough that they catch most software engineers off guard in interviews. This post covers the platform's core architecture so you can discuss it with precision.

---

## The Multi-Tenant Architecture: One Database, Thousands of Customers

Salesforce's foundational engineering bet was that running every customer on shared infrastructure — rather than giving each customer their own database instance — would be dramatically more operationally efficient. The challenge is enforcing strict data isolation when rows for thousands of customers live in the same physical tables.

The mechanism is simple but profound: **every table in the Salesforce schema has an `OrgId` column**. Every query emitted by the Salesforce application layer includes `WHERE OrgId = :currentOrgId`. The application is the isolation boundary — there is no row-level security enforced by the database engine itself. This is a deliberate tradeoff: it allows the database to be tuned and indexed as a unified system while placing isolation responsibility on the application.

The infrastructure beneath this is Oracle RAC clusters (historically) and more recently a proprietary distributed store, with a heavily denormalized schema. The shared tables are sized for the aggregate of all customers, so index design decisions affect every customer simultaneously — there is no "per-tenant index."

This architecture creates an interesting organizational dynamic: a database schema change at Salesforce is a production event that must be backward-compatible for every customer simultaneously. Rolling out schema changes is a multi-week, multi-stage process involving careful versioning.

**Interview implication:** Questions about the tradeoffs of shared-schema multi-tenancy versus separate-schema (one DB per tenant) or separate-instance approaches are extremely common. Know the cost and benefit of each along the dimensions of operational overhead, isolation guarantees, and customization flexibility.

---

## The Metadata-Driven Architecture: Configuration as Data

The Force.com platform's most unusual property is that **customer customizations — custom objects, fields, layouts, validation rules, workflows — are stored as metadata rows in the database, not as schema changes**.

When a Salesforce administrator creates a custom object called `Opportunity_Stage_Review__c`, no `CREATE TABLE` statement runs. Instead, a row is inserted into an internal metadata table describing the object. When a user accesses that object, the Salesforce application layer reads the metadata and dynamically constructs the query, form, and list view at runtime.

This is what makes it possible for Salesforce to deploy a single codebase to 150,000 customers with radically different data models. The application is a metadata interpreter, not a fixed schema application.

The tradeoff: dynamic query construction based on metadata is slower than hand-written queries against a known schema, and it is harder to optimize. Salesforce compensates with aggressive caching of metadata (object definitions, page layouts, validation rules) in memory, with cache invalidation triggered when an admin changes configuration.

---

## Apex: A Proprietary Language in a Sandboxed Governor-Limited Environment

Apex is Salesforce's proprietary programming language for writing server-side business logic. It looks like Java. It is not Java. The critical difference is that Apex runs inside the Salesforce platform's execution context, which enforces **governor limits** — hard caps on resource consumption per transaction.

Governor limits exist because Apex code runs on shared infrastructure. A customer's runaway Apex transaction cannot be allowed to consume unbounded CPU, memory, or database queries — that would degrade service for every other customer on the same pod. The limits are the platform's mechanism for multi-tenant fairness.

Key governor limits per synchronous Apex transaction:
- Maximum SOQL queries issued: 100
- Maximum records returned by SOQL: 50,000
- Maximum DML statements: 150
- Maximum records processed by DML: 10,000
- Maximum CPU time (synchronous): 10,000 ms
- Maximum heap size: 6 MB

The limits for asynchronous contexts (Batch Apex, Queueable Apex, Future methods) are more generous, which is why any operation touching large data volumes must be moved out of the synchronous request path.

Here is a pattern for governor-limit-aware batch processing — the correct way to process large volumes of Salesforce records:

```java
// BatchApexExample.cls
// Implements the Database.Batchable interface. The platform will call
// execute() in chunks (200 records by default, configurable up to 2000).
// Each execute() call runs in its own transaction — its own governor limit
// context — so you cannot accumulate state across chunks in instance variables
// that touch governor-limited resources.

public class AccountSyncBatch implements Database.Batchable<SObject>, Database.Stateful {

    // Database.Stateful preserves instance variable values across execute() chunks.
    // Use it only for accumulators (counters, error lists) — not for SObject collections,
    // which would re-introduce heap limit problems at scale.
    private Integer processedCount = 0;
    private List<String> errors = new List<String>();

    // start() runs once. Return a QueryLocator — the platform streams records
    // from this query into execute() in chunks. This bypasses the 50,000 SOQL
    // row limit that applies to normal queries; QueryLocator can handle up to
    // 50 million records.
    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator(
            'SELECT Id, Name, BillingCountry, LastModifiedDate ' +
            'FROM Account ' +
            'WHERE LastModifiedDate = LAST_N_DAYS:7'
        );
    }

    // execute() is called once per chunk (default 200 records).
    // Every DML statement and SOQL query here counts against the per-chunk
    // governor limits, NOT a global limit across all chunks.
    public void execute(Database.BatchableContext ctx, List<Account> records) {
        List<Account> toUpdate = new List<Account>();

        for (Account acc : records) {
            // Business logic: normalize country codes
            if (acc.BillingCountry == 'United States') {
                acc.BillingCountry = 'US';
                toUpdate.add(acc);
            }
        }

        if (!toUpdate.isEmpty()) {
            // Database.update with allOrNone=false: partial success is allowed.
            // A DML exception on one record does not roll back the entire chunk.
            List<Database.SaveResult> results = Database.update(toUpdate, false);

            for (Database.SaveResult sr : results) {
                if (!sr.isSuccess()) {
                    // Collect errors — instance variable preserved by Database.Stateful
                    errors.add(sr.getErrors()[0].getMessage());
                }
            }
        }

        processedCount += records.size();
    }

    // finish() runs once after all chunks complete.
    // Appropriate for sending summary notifications or triggering follow-on jobs.
    public void finish(Database.BatchableContext ctx) {
        if (!errors.isEmpty()) {
            // Send failure summary via platform email service
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            mail.setToAddresses(new List<String>{'ops-alerts@example.com'});
            mail.setSubject('AccountSyncBatch completed with ' + errors.size() + ' errors');
            mail.setPlainTextBody(String.join(errors, '\n'));
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{mail});
        }
    }
}

// To invoke from anonymous Apex or a trigger:
// Database.executeBatch(new AccountSyncBatch(), 200);
```

The design principle the code above enforces: keep each chunk's DML and SOQL count well below the limits so that unexpected additions to the chunk (from platform callbacks, triggers on the same object) do not push you over. A common failure mode is writing a batch that uses exactly 100 SOQL queries per chunk, then a new trigger is added to the Account object that issues 2 SOQL queries per execution — every batch run starts failing.

---

## Heroku Integration: Polyglot Compute Adjacent to Salesforce Data

Heroku is Salesforce's PaaS platform, acquired in 2010. The integration story centers on **Heroku Connect** — a bidirectional sync service that replicates Salesforce data into a PostgreSQL database on Heroku in near real-time, and writes changes back.

The engineering value: developers can run arbitrary compute (Python, Node, Ruby, any language or framework) against a real PostgreSQL database — no governor limits, no SOQL, no metadata abstraction — while staying synchronized with the Salesforce org. This is the pattern used for computationally intensive operations that would be impossible within Apex governor limits: machine learning scoring, bulk ETL, complex reporting queries with arbitrary JOINs.

The tradeoff is latency: Heroku Connect sync has a lag (typically 30–60 seconds). Applications built on this pattern must tolerate reading data that may be slightly stale relative to the Salesforce org.

---

## Enterprise Permission Model: Sharing Rules and Field-Level Security

Salesforce's permission model has four independent layers that are evaluated together to determine whether a user can see a record:

1. **Object-level security (OLS):** Can this user's profile read the Account object at all?
2. **Record-level access (sharing):** Given OLS grants read access, can this user see *this specific Account record*? Determined by ownership, role hierarchy, sharing rules, and manual shares.
3. **Field-level security (FLS):** Given record access, can this user see the `AnnualRevenue` field on that Account?
4. **Page layout:** Given FLS access, is the field included on the layout the user sees? (Layout is a UI concern — it does not substitute for FLS.)

Sharing rules are evaluated lazily in most contexts but are pre-computed into a **sharing table** (an internal `AccountShare`-style table) for performance on large orgs. The platform maintains this table as records are created, roles change, and sharing rules are modified.

**Interview implication:** Many candidates conflate these layers. Interviewers at Salesforce will ask you to walk through why a user cannot see a record even though they have "Read" permission on the object — the answer almost always involves the sharing model. Understand that FLS is enforced by the platform only in standard UI flows and Apex code using `WITH SECURITY_ENFORCED` — custom API integrations bypassing the Apex layer bypass FLS unless the developer explicitly checks `FieldPermissions` records.

---

## Key Interview Topics for Salesforce Engineering Roles

- **Bulkification:** Why is `for (Id id : ids) { Account a = [SELECT ... WHERE Id = :id]; }` inside a loop catastrophic? (It burns through the 100 SOQL limit instantly.) What is the correct pattern?
- **Trigger context:** A trigger fires once per DML statement, not once per record. What does this mean for governor limit math?
- **Sharing model design:** When would you choose criteria-based sharing rules versus Apex managed sharing? What are the maintenance implications of each?
- **Metadata API vs. Tooling API:** When deploying configuration changes between orgs, which API is appropriate and why?
- **Platform Events vs. Change Data Capture:** Both emit events from Salesforce changes. What is the architectural difference and when would you use each?

Salesforce engineering is unusual because the platform's constraints are as important as the business requirements. Candidates who demonstrate they understand *why* governor limits exist — not just what they are — consistently perform better in technical screens.
