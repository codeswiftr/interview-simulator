"""Industry-specific question seed data.

This module contains 100 curated interview questions across 5 industries:
- SaaS (20 questions)
- Fintech (20 questions)
- Healthcare (20 questions)
- Gaming (20 questions)
- E-commerce (20 questions)

Each industry has a mix of behavioral and technical questions at various difficulty levels.
"""

from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.question import Difficulty, Industry, Question, QuestionCategory, Role

# ========== SAAS INDUSTRY (20 questions) ==========
SAAS_QUESTIONS = [
    # Behavioral Questions (10)
    Question(
        content="Tell me about a time you had to balance customer feature requests with technical debt reduction in a SaaS product.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "HubSpot", "Atlassian"],
        topic_tags=["prioritization", "technical_debt", "customer_focus"],
        expected_duration_seconds=240,
        sample_answer="""**Situation**: At my previous SaaS company, our customer success team received multiple feature requests for advanced reporting while our backend was struggling with performance issues due to technical debt in our data pipeline.

**Task**: As the backend lead, I needed to balance immediate customer needs with critical infrastructure improvements that would affect long-term product reliability.

**Action**: I conducted a cost-benefit analysis showing that unaddressed technical debt would slow feature development by 40% within 6 months. I proposed a hybrid approach: dedicate 60% of sprint capacity to the reporting features customers wanted, and 40% to refactoring the data pipeline. I created visibility by tracking both feature velocity and technical health metrics in our sprint reviews. I also involved customers in the discussion, explaining how infrastructure work would enable faster feature delivery long-term.

**Result**: Over 3 months, we shipped the core reporting features while reducing query response times by 65%. Customer satisfaction scores improved, and our feature velocity actually increased by 25% as technical debt decreased. The stakeholders appreciated the transparency and data-driven approach to balancing priorities.""",
        evaluation_criteria={
            "demonstrates_balance": "Shows understanding of both customer needs and technical sustainability",
            "quantitative_reasoning": "Uses data and metrics to justify decisions",
            "stakeholder_communication": "Explains technical concepts to non-technical audiences",
            "long_term_thinking": "Considers long-term implications, not just short-term wins"
        }
    ),
    Question(
        content="Describe how you've handled a production incident that affected multiple SaaS customers.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.DEVOPS,
        company_tags=["Twilio", "Atlassian", "Salesforce"],
        topic_tags=["incident_response", "communication", "reliability"],
        expected_duration_seconds=200,
        sample_answer="""**Situation**: During a routine deployment, a configuration change caused API rate limiting to malfunction, affecting 30% of our customers who started receiving 429 errors.

**Task**: As the on-call engineer, I needed to quickly restore service while keeping affected customers informed and preventing future occurrences.

**Action**: I immediately rolled back the deployment within 5 minutes of detecting the issue. I posted a status page update acknowledging the problem and providing an ETA. Once service was restored, I conducted a thorough postmortem identifying the root cause: inadequate testing of rate limit changes. I implemented safeguards including canary deployments for config changes and automated rate limit testing in our CI/CD pipeline.

**Result**: Service was restored in 8 minutes. Zero customers churned as a result of the incident, and several mentioned appreciating our transparent communication. The postmortem resulted in 3 process improvements that prevented similar issues. Our incident response became a case study in our company handbook for handling multi-customer outages.""",
        evaluation_criteria={
            "incident_response": "Quick action to restore service",
            "communication": "Proactive customer communication",
            "root_cause_analysis": "Goes beyond symptoms to identify underlying issues",
            "continuous_improvement": "Implements preventive measures"
        }
    ),
    Question(
        content="How have you optimized multi-tenant architecture for performance and isolation in a SaaS platform?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "HubSpot"],
        topic_tags=["multi_tenancy", "performance", "architecture"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Tell me about your experience implementing usage-based billing or metering in a SaaS product.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Twilio", "Stripe", "AWS"],
        topic_tags=["billing", "metering", "product"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe a time you improved onboarding experience to reduce time-to-value for SaaS customers.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.PRODUCT_MANAGER,
        company_tags=["HubSpot", "Atlassian", "Salesforce"],
        topic_tags=["onboarding", "ux", "customer_success"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How do you approach API versioning and deprecation in a SaaS product with thousands of integrations?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.ENGINEERING_MANAGER,
        company_tags=["Salesforce", "Twilio", "Stripe"],
        topic_tags=["api_design", "backwards_compatibility", "deprecation"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Tell me about a time you built or improved a webhook system for SaaS integrations.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Twilio", "HubSpot"],
        topic_tags=["webhooks", "integrations", "reliability"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe your approach to feature flagging and gradual rollouts in a multi-tenant SaaS environment.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Atlassian", "HubSpot"],
        topic_tags=["feature_flags", "deployment", "risk_management"],
        expected_duration_seconds=180,
    ),
    Question(
        content="How have you handled customer data export or migration requests in compliance with data portability requirements?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "HubSpot"],
        topic_tags=["data_portability", "compliance", "customer_success"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with SaaS metrics like MRR, churn, or customer acquisition cost and how you've used them to drive decisions.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        industry=Industry.SAAS,
        role=Role.PRODUCT_MANAGER,
        company_tags=["HubSpot", "Atlassian"],
        topic_tags=["metrics", "business", "analytics"],
        expected_duration_seconds=180,
    ),

    # Technical Questions (10)
    Question(
        content="Design a rate limiting system for a multi-tenant SaaS API with different tier limits.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Twilio", "Stripe", "Salesforce"],
        topic_tags=["rate_limiting", "api", "multi_tenancy"],
        expected_duration_seconds=300,
        sample_answer="""I would design a distributed rate limiting system with the following components:

**Architecture**:
1. **Redis Cluster**: Store rate limit counters using sliding window algorithm
2. **API Gateway**: First line of defense, checks limits before routing
3. **Tenant Service**: Maintains tier configurations (free: 100 req/min, pro: 1000 req/min, enterprise: custom)

**Implementation**:
- Use Redis INCR with TTL for request counting
- Key structure: `ratelimit:{tenant_id}:{window}` where window is timestamp rounded to minute
- Sliding window algorithm: check last N windows to smooth out bursts
- Return standard 429 response with `Retry-After` header
- Implement token bucket for burst allowance

**Scalability**:
- Redis Cluster for horizontal scaling
- Separate read replicas for analytics
- Circuit breakers to fail open if Redis is unavailable (degraded mode)

**Monitoring**:
- Track rejection rates per tenant
- Alert on unusually high rejection rates (potential DDoS or misconfigured client)
- Dashboard showing tier utilization

This design handles millions of requests/second while maintaining per-tenant isolation.""",
        evaluation_criteria={
            "scalability": "Design handles high throughput",
            "fairness": "Different tiers are properly isolated",
            "reliability": "System degrades gracefully",
            "observability": "Includes monitoring and alerting"
        }
    ),
    Question(
        content="How would you implement a background job system for processing customer webhooks with retry logic and dead letter queue?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Twilio"],
        topic_tags=["async", "queues", "reliability"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a search system for a SaaS application with millions of documents across thousands of tenants.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "Atlassian"],
        topic_tags=["search", "elasticsearch", "multi_tenancy"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Explain how you would implement database connection pooling for a multi-tenant SaaS application.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "HubSpot"],
        topic_tags=["database", "connection_pooling", "performance"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Design a notification system for a SaaS platform supporting email, SMS, and in-app notifications with user preferences.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["HubSpot", "Atlassian"],
        topic_tags=["notifications", "event_driven", "user_preferences"],
        expected_duration_seconds=240,
    ),
    Question(
        content="How would you implement audit logging for compliance in a multi-tenant SaaS environment?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "HubSpot"],
        topic_tags=["audit_logging", "compliance", "security"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a caching strategy for a SaaS application with tenant-specific data and shared reference data.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "Atlassian"],
        topic_tags=["caching", "redis", "performance"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Explain how you would implement zero-downtime deployments for a critical SaaS application.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.DEVOPS,
        company_tags=["Salesforce", "Twilio", "Atlassian"],
        topic_tags=["deployment", "blue_green", "availability"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Design an analytics pipeline for tracking SaaS product usage across millions of events per day.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.DATA_ENGINEER,
        company_tags=["HubSpot", "Atlassian"],
        topic_tags=["analytics", "data_pipeline", "big_data"],
        expected_duration_seconds=300,
    ),
    Question(
        content="How would you implement role-based access control (RBAC) in a SaaS application with custom roles per tenant?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Salesforce", "Atlassian"],
        topic_tags=["rbac", "security", "authorization"],
        expected_duration_seconds=200,
    ),
]

# ========== FINTECH INDUSTRY (20 questions) ==========
FINTECH_QUESTIONS = [
    # Behavioral Questions (10)
    Question(
        content="Tell me about a time you had to ensure financial transaction accuracy and consistency under high load.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Plaid", "Square"],
        topic_tags=["transactions", "consistency", "reliability"],
        expected_duration_seconds=240,
        sample_answer="""**Situation**: Our payment processing system was experiencing transaction inconsistencies during peak load periods - about 1 in 10,000 transactions had mismatched states between payment gateway and our ledger.

**Task**: As the payments engineer, I needed to identify and fix the consistency issue while ensuring zero financial discrepancies and maintaining high throughput.

**Action**: I implemented distributed tracing to track the entire transaction lifecycle. I discovered race conditions in our async webhook handling where payment confirmations could arrive before transaction creation completed. I redesigned the flow using the saga pattern with compensating transactions and added idempotency keys for all payment operations. I implemented a reconciliation job that ran every 15 minutes to detect and alert on any remaining discrepancies. I added database-level constraints to prevent invalid state transitions.

**Result**: Transaction consistency improved to 99.9999% (1 error per million transactions, down from 100 per million). The reconciliation system caught the few remaining edge cases before they reached customers. We processed Black Friday traffic (5x normal volume) with zero financial discrepancies. The architecture changes became our standard pattern for all financial workflows.""",
        evaluation_criteria={
            "attention_to_detail": "Understands the critical nature of financial accuracy",
            "systematic_debugging": "Uses proper tools and methodology to find root cause",
            "defensive_programming": "Implements multiple layers of protection",
            "monitoring": "Adds observability and reconciliation"
        }
    ),
    Question(
        content="Describe how you've implemented or worked with fraud detection systems in a fintech application.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square", "Robinhood"],
        topic_tags=["fraud_detection", "security", "machine_learning"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you approached regulatory compliance (PCI-DSS, SOC 2, GDPR) in your fintech work?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.ENGINEERING_MANAGER,
        company_tags=["Stripe", "Plaid", "Square"],
        topic_tags=["compliance", "security", "regulations"],
        expected_duration_seconds=200,
        sample_answer="""**Situation**: Our startup was pursuing enterprise fintech customers who required SOC 2 Type II and PCI-DSS compliance before signing contracts.

**Task**: As engineering lead, I needed to implement compliance requirements without slowing down product development velocity.

**Action**: I created a compliance-first architecture: all card data stored in a PCI-compliant third-party vault (no card numbers in our database), encryption at rest and in transit for all sensitive data, comprehensive audit logging with tamper-proof storage, and role-based access controls with principle of least privilege. I worked with our security consultant to conduct quarterly penetration tests and addressed findings within 30 days. I implemented automated compliance checks in CI/CD (credential scanning, vulnerability scanning). I established a culture where compliance was a feature, not an obstacle.

**Result**: We achieved SOC 2 Type II certification in 6 months and PCI-DSS Level 1 in 9 months. The compliance-first architecture actually improved our development velocity because security was built-in rather than bolted-on. We won 3 major enterprise deals worth $2M ARR that required these certifications. Zero compliance violations in our first year of certification.""",
        evaluation_criteria={
            "compliance_knowledge": "Understands major fintech compliance frameworks",
            "practical_implementation": "Describes concrete technical measures",
            "business_impact": "Connects compliance to business outcomes",
            "cultural_mindset": "Views compliance as enabler, not blocker"
        }
    ),
    Question(
        content="Tell me about your experience with double-entry bookkeeping or ledger systems in software.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["ledger", "accounting", "financial_systems"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Describe a time you had to handle a money movement error or financial discrepancy.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Plaid", "Square"],
        topic_tags=["incident_response", "financial_accuracy", "accountability"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How have you implemented idempotency in payment or financial transaction APIs?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["idempotency", "api_design", "reliability"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with KYC (Know Your Customer) or identity verification systems.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Plaid", "Stripe", "Robinhood"],
        topic_tags=["kyc", "identity", "compliance"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe how you've approached testing for financial systems to ensure correctness.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["testing", "quality", "financial_accuracy"],
        expected_duration_seconds=180,
    ),
    Question(
        content="How have you handled currency conversion and multi-currency support in a fintech application?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Wise"],
        topic_tags=["currency", "internationalization", "precision"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about a time you improved the performance of a financial transaction processing system.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square", "Robinhood"],
        topic_tags=["performance", "optimization", "scalability"],
        expected_duration_seconds=200,
    ),

    # Technical Questions (10)
    Question(
        content="Design a payment processing system that handles credit card transactions with proper security and PCI compliance.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["payments", "security", "pci_compliance"],
        expected_duration_seconds=300,
        sample_answer="""I would design a PCI-compliant payment processing system with the following architecture:

**Security-First Design**:
1. **Card Data Isolation**: Never store full card numbers. Use tokenization (Stripe, Braintree) to exchange sensitive data for tokens.
2. **API Flow**: Client -> Our API (receives token, never card) -> Payment Processor -> Bank
3. **PCI Scope Reduction**: By using tokenization, our servers never touch card data, reducing PCI scope to SAQ-A (simplest level).

**System Components**:
- **Frontend**: Uses Stripe Elements (hosted fields) to collect card data. Card data POSTs directly to Stripe, returns token to our client.
- **Backend API**: Receives token + payment amount, creates payment intent in Stripe, returns client secret.
- **Webhook Handler**: Receives async payment status updates (succeeded, failed, requires_action).
- **Reconciliation Service**: Matches payment intents with database orders, runs hourly.
- **Ledger**: Double-entry bookkeeping system recording all debits/credits.

**Data Flow**:
1. User enters card -> Stripe Elements
2. Stripe returns token -> Our frontend
3. Frontend calls our API with token + amount
4. We create payment intent via Stripe API
5. Stripe processes payment -> webhook to us
6. We update order status + ledger

**Security Measures**:
- TLS 1.2+ for all connections
- API keys stored in secrets manager (HashiCorp Vault)
- IP allowlisting for webhook endpoints
- HMAC signature verification for webhooks
- Idempotency keys for payment operations
- Rate limiting (100 requests/min per user)

**Monitoring**:
- Payment success rate alerts (<95% triggers page)
- Reconciliation gap alerts (mismatch between Stripe and our DB)
- Fraud score tracking (Stripe Radar integration)

This design achieves PCI compliance, handles 10,000 TPS, and maintains 99.99% accuracy.""",
        evaluation_criteria={
            "security_awareness": "Prioritizes PCI compliance and security",
            "architecture_knowledge": "Understands tokenization and payment flows",
            "completeness": "Addresses reconciliation, monitoring, error handling",
            "practical_experience": "References real tools (Stripe, payment processors)"
        }
    ),
    Question(
        content="How would you implement a distributed ledger system for tracking financial transactions across microservices?",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["ledger", "distributed_systems", "consistency"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Design a real-time fraud detection system for financial transactions.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square", "Robinhood"],
        topic_tags=["fraud_detection", "real_time", "machine_learning"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Explain how you would handle database transactions for a money transfer between two accounts ensuring ACID properties.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square", "Plaid"],
        topic_tags=["acid", "transactions", "databases"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a reconciliation system to detect discrepancies between payment gateway and internal ledger.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["reconciliation", "data_integrity", "financial_accuracy"],
        expected_duration_seconds=240,
    ),
    Question(
        content="How would you implement a rate limiter for financial APIs to prevent abuse while allowing legitimate high-volume users?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Plaid"],
        topic_tags=["rate_limiting", "security", "api_design"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a system for managing and rotating API keys with different permission scopes for financial services.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Plaid"],
        topic_tags=["api_keys", "security", "access_control"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Explain how you would implement a retry mechanism for failed financial transactions with proper idempotency.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["retry", "idempotency", "reliability"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Design a webhook delivery system for financial events that guarantees at-least-once delivery.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Plaid"],
        topic_tags=["webhooks", "reliability", "event_driven"],
        expected_duration_seconds=240,
    ),
    Question(
        content="How would you implement decimal precision arithmetic for financial calculations to avoid rounding errors?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        industry=Industry.FINTECH,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Stripe", "Square"],
        topic_tags=["precision", "arithmetic", "financial_calculations"],
        expected_duration_seconds=150,
    ),
]

# ========== HEALTHCARE INDUSTRY (20 questions) ==========
HEALTHCARE_QUESTIONS = [
    # Behavioral Questions (10)
    Question(
        content="Tell me about your experience ensuring HIPAA compliance in healthcare software development.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva", "Tempus"],
        topic_tags=["hipaa", "compliance", "security"],
        expected_duration_seconds=240,
        sample_answer="""**Situation**: I was technical lead for a patient portal that needed HIPAA compliance to handle protected health information (PHI).

**Task**: I needed to ensure our system met all HIPAA technical safeguards while maintaining a good user experience for patients and providers.

**Action**: I implemented multiple layers of protection: end-to-end encryption for PHI at rest (AES-256) and in transit (TLS 1.3), role-based access control with audit logging of all PHI access, automatic session timeout after 15 minutes of inactivity, and secure authentication with MFA for healthcare providers. I worked with our compliance officer to complete a thorough risk assessment and document all safeguards in our policies. I implemented automated HIPAA compliance checks in our CI/CD pipeline (no PHI in logs, proper encryption, secure API endpoints). We conducted quarterly security awareness training for the entire team.

**Result**: We passed our HIPAA audit on first attempt with zero findings. The comprehensive audit trail helped us respond to patient access requests within required timeframes. We achieved our target of <2 second load times despite encryption overhead. Zero HIPAA violations or breaches in 2 years of operation. The architecture became our template for all healthcare products.""",
        evaluation_criteria={
            "compliance_depth": "Demonstrates detailed understanding of HIPAA requirements",
            "technical_implementation": "Describes specific security measures",
            "holistic_approach": "Considers people, process, and technology",
            "risk_management": "Balances security with usability"
        }
    ),
    Question(
        content="Describe how you've handled patient data privacy and consent management in a healthcare application.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["privacy", "consent", "patient_data"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Tell me about a time you had to ensure data accuracy in a clinical or medical records system.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Tempus", "Flatiron Health"],
        topic_tags=["data_quality", "medical_records", "accuracy"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How have you approached integrating with HL7 or FHIR standards in healthcare systems?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["hl7", "fhir", "interoperability"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Describe your experience with Electronic Health Records (EHR) system integration or development.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems"],
        topic_tags=["ehr", "integration", "healthcare_it"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about a time you had to balance healthcare provider workflow efficiency with patient safety requirements.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.PRODUCT_MANAGER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["workflow", "safety", "usability"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you handled audit trails and access logging for sensitive medical data?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva", "Tempus"],
        topic_tags=["audit_logging", "compliance", "security"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe your experience with clinical decision support systems or medical algorithms.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Tempus", "Flatiron Health"],
        topic_tags=["clinical_decision_support", "algorithms", "ai_in_healthcare"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Tell me about a time you had to handle a security incident involving patient data.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.ENGINEERING_MANAGER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["incident_response", "security", "breach_notification"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you ensured medication or treatment order accuracy in healthcare software?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems"],
        topic_tags=["medication_orders", "safety", "accuracy"],
        expected_duration_seconds=180,
    ),

    # Technical Questions (10)
    Question(
        content="Design a HIPAA-compliant system for storing and retrieving patient medical records with proper encryption and access controls.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["hipaa", "encryption", "access_control"],
        expected_duration_seconds=300,
        sample_answer="""I would design a HIPAA-compliant medical records system with these components:

**Security Architecture**:
1. **Encryption Layer**:
   - At-rest: AES-256 encryption for all PHI in database and file storage
   - In-transit: TLS 1.3 for all API communications
   - Field-level encryption for highly sensitive data (SSN, insurance ID)

2. **Access Control**:
   - Role-Based Access Control (RBAC): physician, nurse, admin, patient roles
   - Attribute-Based Access Control (ABAC): can only access records where provider-patient relationship exists
   - Break-glass access for emergencies (logged and reviewed)
   - Principle of least privilege enforced at database and API level

3. **Audit System**:
   - Comprehensive audit log: who accessed what PHI, when, from where, and why
   - Immutable audit trail using append-only storage
   - Real-time alerting on suspicious access patterns (e.g., provider accessing 100 records in 1 minute)
   - Quarterly audit log reviews

**System Components**:
- **API Gateway**: Authentication, authorization, rate limiting
- **Auth Service**: SAML/OAuth integration with hospital SSO, MFA for sensitive operations
- **Record Service**: CRUD operations with automatic audit logging
- **Encryption Service**: Key management using AWS KMS or HashiCorp Vault
- **Audit Service**: Writes to immutable log storage (WORM - Write Once Read Many)
- **Data Store**: PostgreSQL with row-level security, encrypted volumes

**Data Flow**:
1. Provider authenticates via SSO + MFA
2. Request to view patient record
3. Authorization check: Does provider have active relationship with patient?
4. Audit log created: timestamp, user, patient ID, action, IP address
5. Decrypt record using patient-specific key
6. Return to provider
7. Auto-logout after 15 min inactivity

**Compliance Features**:
- Automatic session timeout (15 minutes)
- Minimum necessary principle: only return fields provider needs
- Patient portal for viewing access logs
- Right to access: patient can download all their records
- Data retention policies enforced automatically

**Disaster Recovery**:
- Encrypted backups to separate region
- Point-in-time recovery (30 days)
- Backup encryption keys in separate system

This design meets all HIPAA technical safeguards and scales to millions of records.""",
        evaluation_criteria={
            "hipaa_knowledge": "Demonstrates understanding of HIPAA technical safeguards",
            "defense_in_depth": "Multiple layers of security",
            "auditability": "Comprehensive logging and monitoring",
            "practical_implementation": "References real technologies and patterns"
        }
    ),
    Question(
        content="How would you implement a patient matching algorithm to prevent duplicate medical records?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems"],
        topic_tags=["patient_matching", "data_quality", "algorithms"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a clinical alerting system that notifies providers of critical lab results or drug interactions.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Tempus"],
        topic_tags=["clinical_alerts", "safety", "real_time"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Explain how you would implement data anonymization for using patient data in research while maintaining HIPAA compliance.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.DATA_ENGINEER,
        company_tags=["Tempus", "Flatiron Health"],
        topic_tags=["anonymization", "research", "privacy"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Design a medication order verification system to prevent dangerous drug interactions and dosing errors.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems"],
        topic_tags=["medication_safety", "clinical_decision_support", "algorithms"],
        expected_duration_seconds=300,
    ),
    Question(
        content="How would you implement real-time data synchronization between multiple healthcare systems while maintaining HIPAA compliance?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["data_sync", "interoperability", "hipaa"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a consent management system for clinical trials that tracks patient consent versions and changes.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Veeva", "Tempus"],
        topic_tags=["consent", "clinical_trials", "compliance"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Explain how you would implement backup and disaster recovery for a critical healthcare application.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.DEVOPS,
        company_tags=["Epic Systems", "Veeva"],
        topic_tags=["disaster_recovery", "backup", "high_availability"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a system for tracking and reporting adverse events in clinical software.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.HEALTHCARE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Veeva", "Tempus"],
        topic_tags=["adverse_events", "safety", "reporting"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How would you implement a clinical data warehouse that aggregates data from multiple source systems?",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.HEALTHCARE,
        role=Role.DATA_ENGINEER,
        company_tags=["Tempus", "Flatiron Health"],
        topic_tags=["data_warehouse", "etl", "analytics"],
        expected_duration_seconds=300,
    ),
]

# ========== GAMING INDUSTRY (20 questions) ==========
GAMING_QUESTIONS = [
    # Behavioral Questions (10)
    Question(
        content="Tell me about a time you optimized game server performance to handle thousands of concurrent players.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Unity", "Riot Games", "Epic Games"],
        topic_tags=["performance", "scalability", "game_servers"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Describe your experience with real-time multiplayer game networking and handling latency.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games", "Valve"],
        topic_tags=["networking", "multiplayer", "latency"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you approached anti-cheat systems or preventing exploits in online games?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Valve", "Epic Games"],
        topic_tags=["anti_cheat", "security", "exploits"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Tell me about a time you had to balance game feature development with technical debt in a live service game.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.ENGINEERING_MANAGER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["prioritization", "technical_debt", "live_service"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Describe your experience with game analytics and how you've used player data to drive decisions.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.DATA_ENGINEER,
        company_tags=["Unity", "Riot Games"],
        topic_tags=["analytics", "player_data", "data_driven"],
        expected_duration_seconds=180,
    ),
    Question(
        content="How have you handled a critical game-breaking bug in a live production environment?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games", "Valve"],
        topic_tags=["incident_response", "debugging", "live_ops"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Tell me about your experience with game economy design or virtual currency systems.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["game_economy", "virtual_currency", "monetization"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe how you've approached player matchmaking systems to ensure fair and engaging matches.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Valve"],
        topic_tags=["matchmaking", "algorithms", "player_experience"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you implemented or improved content delivery systems for game updates and patches?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.DEVOPS,
        company_tags=["Unity", "Epic Games"],
        topic_tags=["cdn", "content_delivery", "updates"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with player progression systems and how you've ensured they're engaging.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.PRODUCT_MANAGER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["progression", "engagement", "game_design"],
        expected_duration_seconds=180,
    ),

    # Technical Questions (10)
    Question(
        content="Design a matchmaking system for a competitive multiplayer game that balances skill, latency, and queue times.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Valve"],
        topic_tags=["matchmaking", "algorithms", "system_design"],
        expected_duration_seconds=300,
    ),
    Question(
        content="How would you implement a leaderboard system that handles millions of players with real-time updates?",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["leaderboards", "scalability", "real_time"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a game server architecture that can handle 100,000 concurrent players across multiple regions.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games", "Valve"],
        topic_tags=["game_servers", "scalability", "distributed_systems"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Explain how you would implement client-side prediction and server reconciliation for a fast-paced action game.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["networking", "prediction", "game_physics"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a virtual currency and in-game purchase system with fraud prevention.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["monetization", "virtual_currency", "fraud_prevention"],
        expected_duration_seconds=240,
    ),
    Question(
        content="How would you implement a replay system that allows players to watch their past games?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Valve"],
        topic_tags=["replays", "storage", "game_state"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a chat and social system for a multiplayer game with moderation and reporting.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["chat", "moderation", "social"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Explain how you would implement delta compression for game state synchronization in a multiplayer game.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["compression", "networking", "optimization"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Design a system for A/B testing game features across millions of players.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Unity", "Riot Games"],
        topic_tags=["ab_testing", "experimentation", "analytics"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How would you implement a content moderation system for user-generated content in games?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.GAMING,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Riot Games", "Epic Games"],
        topic_tags=["moderation", "ugc", "safety"],
        expected_duration_seconds=200,
    ),
]

# ========== E-COMMERCE INDUSTRY (20 questions) ==========
ECOMMERCE_QUESTIONS = [
    # Behavioral Questions (10)
    Question(
        content="Tell me about a time you optimized checkout flow to reduce cart abandonment in an e-commerce application.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.PRODUCT_MANAGER,
        company_tags=["Shopify", "Amazon", "Instacart"],
        topic_tags=["conversion", "ux", "optimization"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Describe your experience handling inventory synchronization across multiple sales channels (web, mobile, retail).",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["inventory", "synchronization", "distributed_systems"],
        expected_duration_seconds=220,
    ),
    Question(
        content="How have you approached search and discovery optimization to improve product findability?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Etsy"],
        topic_tags=["search", "discovery", "relevance"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with recommendation systems for personalized product suggestions.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.DATA_ENGINEER,
        company_tags=["Amazon", "Shopify"],
        topic_tags=["recommendations", "personalization", "machine_learning"],
        expected_duration_seconds=220,
    ),
    Question(
        content="Describe how you've handled a critical payment processing outage during peak shopping season.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["incident_response", "payments", "availability"],
        expected_duration_seconds=200,
    ),
    Question(
        content="How have you implemented or improved fraud detection for e-commerce transactions?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["fraud_detection", "security", "risk_management"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with pricing strategy implementation or dynamic pricing systems.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Instacart"],
        topic_tags=["pricing", "dynamic_pricing", "algorithms"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Describe how you've approached mobile app performance optimization for e-commerce.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Shopify", "Instacart"],
        topic_tags=["mobile", "performance", "optimization"],
        expected_duration_seconds=180,
    ),
    Question(
        content="How have you handled order fulfillment and shipping integrations with third-party logistics providers?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["fulfillment", "shipping", "integrations"],
        expected_duration_seconds=180,
    ),
    Question(
        content="Tell me about your experience with A/B testing for e-commerce features and how you measured impact.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        industry=Industry.ECOMMERCE,
        role=Role.PRODUCT_MANAGER,
        company_tags=["Amazon", "Shopify", "Etsy"],
        topic_tags=["ab_testing", "experimentation", "metrics"],
        expected_duration_seconds=180,
    ),

    # Technical Questions (10)
    Question(
        content="Design a scalable product catalog system that handles millions of SKUs with real-time inventory updates.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Shopify"],
        topic_tags=["catalog", "scalability", "inventory"],
        expected_duration_seconds=300,
    ),
    Question(
        content="How would you implement a shopping cart system that handles concurrent updates and prevents overselling?",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["cart", "concurrency", "inventory"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a search and filtering system for e-commerce products with faceted search and relevance ranking.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Etsy"],
        topic_tags=["search", "elasticsearch", "relevance"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Explain how you would implement a distributed order management system across multiple warehouses.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Shopify"],
        topic_tags=["order_management", "distributed_systems", "logistics"],
        expected_duration_seconds=300,
    ),
    Question(
        content="Design a flash sale system that can handle 100x normal traffic without crashing.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Shopify"],
        topic_tags=["flash_sales", "scalability", "performance"],
        expected_duration_seconds=300,
    ),
    Question(
        content="How would you implement a recommendation engine that suggests products based on browsing and purchase history?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.ECOMMERCE,
        role=Role.DATA_ENGINEER,
        company_tags=["Amazon", "Shopify"],
        topic_tags=["recommendations", "machine_learning", "personalization"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Design a returns and refunds system that integrates with payment processors and inventory management.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["returns", "refunds", "payments"],
        expected_duration_seconds=240,
    ),
    Question(
        content="Explain how you would implement real-time inventory reservation during checkout to prevent overselling.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["inventory", "reservation", "concurrency"],
        expected_duration_seconds=200,
    ),
    Question(
        content="Design a customer review and rating system with spam detection and moderation.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Amazon", "Etsy"],
        topic_tags=["reviews", "moderation", "ugc"],
        expected_duration_seconds=240,
    ),
    Question(
        content="How would you implement a coupon and promotional discount system with complex rules and stacking logic?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        industry=Industry.ECOMMERCE,
        role=Role.SOFTWARE_ENGINEER,
        company_tags=["Shopify", "Amazon"],
        topic_tags=["coupons", "promotions", "business_logic"],
        expected_duration_seconds=200,
    ),
]

# Combine all questions
ALL_INDUSTRY_QUESTIONS = (
    SAAS_QUESTIONS +
    FINTECH_QUESTIONS +
    HEALTHCARE_QUESTIONS +
    GAMING_QUESTIONS +
    ECOMMERCE_QUESTIONS
)


async def seed_industry_questions(session: "AsyncSession | None" = None, auto_commit: bool = True):
    """Seed industry-specific questions. Idempotent - skips existing questions with same content.

    Args:
        session: Optional AsyncSession. If not provided, creates a new session from app engine.
        auto_commit: Whether to commit the session automatically. Set to False in tests.
    """
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession

    # If no session provided, create one from app engine (for CLI usage)
    if session is None:
        from app.db import engine
        async with AsyncSession(engine) as session:
            return await seed_industry_questions(session, auto_commit=True)

    # Get existing question contents to avoid duplicates
    existing_result = await session.exec(select(Question.content))
    existing_contents = set(existing_result.all())

    added_count = 0
    skipped_count = 0

    for question_template in ALL_INDUSTRY_QUESTIONS:
        if question_template.content in existing_contents:
            skipped_count += 1
            continue

        # Create a fresh instance to avoid ID conflicts when reseeding
        fresh_question = Question(
            content=question_template.content,
            category=question_template.category,
            difficulty=question_template.difficulty,
            industry=question_template.industry,
            role=question_template.role,
            company_tags=question_template.company_tags.copy(),
            topic_tags=question_template.topic_tags.copy(),
            expected_duration_seconds=question_template.expected_duration_seconds,
            sample_answer=question_template.sample_answer,
            evaluation_criteria=question_template.evaluation_criteria.copy(),
        )
        session.add(fresh_question)
        added_count += 1

    if auto_commit:
        await session.commit()

    print(f"✅ Industry questions seeded: {added_count} added, {skipped_count} skipped (already exist)")
    print(f"📊 Total industry questions in database: {len(existing_contents) + added_count}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_industry_questions())
