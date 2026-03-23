---
title: "Stripe Atlas Engineering Deep Dive: Global Entity Formation at Fintech Scale"
date: "2024-01-15"
author: "Interview Simulator Team"
tags: ["stripe", "fintech", "distributed-systems", "api-design", "reliability", "engineering"]
description: "How Stripe Atlas tackles the infrastructure challenge of forming companies in 50+ countries — and what it means for your Stripe engineering interview."
---

# Stripe Atlas Engineering Deep Dive: Global Entity Formation at Fintech Scale

Stripe Atlas has a deceptively simple pitch: fill out a form, pay a fee, and get a real US company incorporated with a bank account. Behind that simplicity is one of the most interesting distributed systems problems in fintech — coordinating unreliable government APIs, legal document generation, KYC/KYB pipelines, and multi-currency banking setups across dozens of jurisdictions, all while guaranteeing exactly-once semantics on operations that touch money and legal filings.

## The Core Problem: Orchestrating Unreliable External Systems

Most distributed systems problems involve services you control. Atlas is different. The critical path runs through third-party registrars in Delaware (CT Corporation, Registered Agent Inc.), banking partners like SVB and Mercury, KYC vendors like Persona, and government filing systems that were never designed for programmatic access. Some of these APIs have availability below 99%. Some have no API at all — filings happen via email or web scraping.

Stripe's engineering approach to this problem follows a pattern they call **durable execution**: every step of the formation workflow is persisted before execution, retried with exponential backoff, and tracked against a canonical state machine. No step is assumed to succeed until confirmed by the external system.

The state machine for a typical Delaware C-Corp formation looks like this:

```
CREATED
  → KYC_SUBMITTED
  → KYC_APPROVED
  → DOCUMENTS_GENERATED
  → FILING_SUBMITTED
  → FILING_CONFIRMED
  → BANK_APPLICATION_SUBMITTED
  → BANK_ACCOUNT_OPENED
  → STRIPE_ACCOUNT_LINKED
  → COMPLETED
```

Each transition is idempotent. If the process crashes between `FILING_SUBMITTED` and `FILING_CONFIRMED`, recovery polls the registrar API and resumes from the last confirmed state rather than resubmitting the filing (which would result in a duplicate incorporation).

## Idempotent Workflow Design

Here is a simplified version of the idempotency pattern Stripe uses for multi-step entity formation. The key insight: each step receives a deterministic idempotency key derived from the formation ID and the step name. External systems that support idempotency keys (Stripe's own APIs, some KYC vendors) receive this key with every request.

```python
import hashlib
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FormationState(Enum):
    CREATED = "created"
    KYC_SUBMITTED = "kyc_submitted"
    KYC_APPROVED = "kyc_approved"
    DOCUMENTS_GENERATED = "documents_generated"
    FILING_SUBMITTED = "filing_submitted"
    FILING_CONFIRMED = "filing_confirmed"
    BANK_APPLICATION_SUBMITTED = "bank_application_submitted"
    BANK_ACCOUNT_OPENED = "bank_account_opened"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Formation:
    id: str
    state: FormationState
    idempotency_seed: str
    metadata: dict

def idempotency_key(formation_id: str, step: str) -> str:
    """
    Derive a stable, collision-resistant idempotency key for a
    (formation, step) pair. Using HMAC-SHA256 ensures the key is
    deterministic across restarts but not guessable by external parties.
    """
    raw = f"{formation_id}:{step}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def advance_formation(formation: Formation, db, external_clients) -> Formation:
    """
    Advance formation by exactly one state transition.
    Safe to call repeatedly — will no-op if already past the target state.
    """
    state = formation.state

    if state == FormationState.CREATED:
        key = idempotency_key(formation.id, "kyc_submit")
        result = external_clients.kyc.submit(
            applicant=formation.metadata["founder"],
            idempotency_key=key
        )
        formation = db.transition(formation, FormationState.KYC_SUBMITTED, {
            "kyc_reference": result.reference_id
        })

    elif state == FormationState.KYC_APPROVED:
        # Document generation is local — still idempotent via database lock
        docs = generate_formation_documents(formation)
        formation = db.transition(formation, FormationState.DOCUMENTS_GENERATED, {
            "document_ids": [d.id for d in docs]
        })

    elif state == FormationState.DOCUMENTS_GENERATED:
        key = idempotency_key(formation.id, "filing_submit")
        result = external_clients.registrar.file_incorporation(
            documents=formation.metadata["document_ids"],
            state="DE",
            idempotency_key=key  # Not all registrars support this
        )
        formation = db.transition(formation, FormationState.FILING_SUBMITTED, {
            "filing_reference": result.tracking_id
        })

    # ... additional states omitted for brevity

    return formation

def run_formation_with_retry(formation_id: str, db, clients, max_attempts=5):
    """
    Outer retry loop. Each call to advance_formation moves the state
    machine forward by one step. Crashes are safe — we resume from
    the last persisted state.
    """
    formation = db.get_formation(formation_id)

    for attempt in range(max_attempts):
        try:
            formation = advance_formation(formation, db, clients)
            if formation.state == FormationState.COMPLETED:
                return formation
        except ExternalServiceError as e:
            wait = (2 ** attempt) + random_jitter()
            log_retry(formation, e, attempt, wait)
            time.sleep(wait)
        except DuplicateFilingError:
            # Registrar already has this filing — recover the reference ID
            # and continue as if the submission succeeded
            formation = recover_filing_reference(formation, db, clients)

    raise FormationStuck(f"Formation {formation_id} exceeded retry budget")
```

The critical design decision here is separating **submission** from **confirmation**. Submitting a filing and knowing the filing was accepted are two different API calls, often with different reliability characteristics. Atlas polls for confirmation rather than blocking, which decouples the latency of government systems from user-facing response times.

## KYC/KYB Across Jurisdictions

Know Your Customer (KYC) and Know Your Business (KYB) requirements vary dramatically by country. A US Delaware C-Corp requires identity verification of all founders and beneficial owners. A UK Ltd requires Companies House filings with director details. Some jurisdictions require notarized documents; others accept electronic signatures.

Stripe abstracts this via a jurisdiction rules engine — a configuration layer that maps `(country, entity_type)` to a checklist of required documents, verification steps, and third-party integrations. Adding a new country is a configuration change, not a code change, which is what enabled Atlas to expand from a US-only product to 50+ countries without rewriting the core workflow engine.

The KYC pipeline itself uses a vendor-agnostic adapter pattern. Stripe initially integrated with a single KYC vendor but designed the interface so that vendor-specific logic lives behind an abstraction layer. When the primary vendor has downtime, the system can route to a backup vendor or queue the verification for later processing.

## Reliability Engineering for Unreliable Third Parties

When your critical path runs through government APIs, you cannot achieve traditional SLOs. Stripe Atlas handles this with a combination of:

**Async-first design.** Formation completion is never promised to happen synchronously. The user submits their information, receives an acknowledgment, and gets notified when each stage completes. This means a 48-hour government processing delay does not translate to a 48-hour hanging HTTP request.

**Compensating transactions.** If banking setup fails after a company is already incorporated, Atlas doesn't leave the customer in a half-formed state. Compensating transactions either reverse prior steps (if reversible) or flag the formation for human review with a complete audit trail.

**Synthetic monitoring.** Stripe runs canary formations — real but minimal entity formations — in each jurisdiction to detect when external systems degrade before customers notice.

## What This Means for Your Stripe Interview

Stripe interviews consistently probe distributed systems fundamentals through fintech scenarios. Knowing Atlas gives you concrete grounding.

**Likely interview topics:**

- **API design**: Design an API for multi-step workflows with partial failure recovery. Expect follow-ups about idempotency key schemes, polling vs. webhooks, and partial success responses.
- **Reliability**: How do you build reliable systems on top of unreliable dependencies? Bring up circuit breakers, bulkheads, queue-based decoupling, and the distinction between retryable and non-retryable errors.
- **Distributed systems**: Exactly-once semantics, state machine design, the difference between at-least-once and at-most-once delivery — Atlas is a real-world example of why these matter.
- **Data modeling**: How do you model a formation entity that can be in dozens of states across multiple jurisdictions? Talk about event sourcing vs. snapshot models and their tradeoffs.

The most common mistake candidates make in Stripe systems design interviews is treating external APIs as reliable. In Stripe's domain, designing for failure is the baseline expectation, not a differentiator.

---

*Practice Stripe-style distributed systems and API design questions with Interview Simulator's fintech interview track. Our AI interviewer uses real Stripe engineering scenarios to help you build the muscle memory you need on interview day.*
