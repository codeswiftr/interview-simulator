# Chime Engineering Deep Dive: Neobank Infrastructure at Consumer Scale

Chime is the largest neobank in the United States with over 20 million customers — more than many traditional banks. Unlike traditional banks that built software on top of decades-old core banking systems, Chime was born digital, which means their engineering team faces a different set of constraints: they must deliver consumer-grade UX with mobile-first expectations while operating with the reliability requirements of financial infrastructure. The interesting engineering problems at Chime sit at the intersection of fintech compliance, real-time consumer features, and the challenge of moving money quickly in a system that traditionally moves slowly.

## Core Banking Integration: The Middleware Layer

Chime does not have a banking license — it operates through partner banks (Stride Bank and The Bancorp Bank). This means Chime's engineering team built a middleware layer that sits between their consumer-facing products and the partner banks' core banking systems.

The partner banks run legacy core banking software (often FIS or Fiserv) that was built for batch processing, not real-time APIs. Chime's middleware abstracts this away, translating their real-time product requirements into the asynchronous, batch-friendly interface the core banking systems expect.

The main engineering challenge: when a user opens the Chime app and sees their balance, that number must be accurate and instantly available. But the source of truth — the core banking ledger — is a batch system that may not have processed all of today's transactions yet. Chime maintains a "shadow ledger" that they update in real time as transactions flow through their system, reconciling against the core banking system periodically:

```python
class ShadowLedger:
    def __init__(self, redis_client, postgres_client):
        self.redis = redis_client  # Real-time balance cache
        self.db = postgres_client  # Durable transaction log

    def apply_transaction(self, account_id, amount_cents, transaction_id):
        """Apply transaction to shadow ledger atomically"""
        # Write to durable log first (idempotent via transaction_id)
        self.db.execute("""
            INSERT INTO shadow_transactions
                (transaction_id, account_id, amount_cents, applied_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (transaction_id) DO NOTHING
        """, (transaction_id, account_id, amount_cents))

        # Update real-time balance cache
        self.redis.incrby(f"balance:{account_id}", amount_cents)

    def get_balance(self, account_id):
        """Get real-time balance from cache"""
        cached = self.redis.get(f"balance:{account_id}")
        if cached is not None:
            return int(cached)
        # Cache miss: recompute from transaction log
        return self.recompute_balance(account_id)
```

The reconciliation process runs continuously, comparing the shadow ledger against the core banking system's settled transactions and flagging discrepancies for investigation.

## SpotMe: Real-Time Overdraft Engineering

Chime's SpotMe feature allows members to overdraft their account by up to $200 without a fee. This sounds simple; the engineering is not. Chime must make a real-time credit decision at the point of transaction — when the card is presented at a checkout terminal — and that decision must complete in under 150ms (the card network timeout).

The SpotMe eligibility model runs as a pre-computed result. Rather than computing overdraft eligibility at transaction time, Chime runs a batch process that evaluates each account's eligibility periodically and stores the result. At authorization time, the authorization service reads the pre-computed eligibility flag rather than running the model live.

This pre-computation approach sacrifices freshness for latency: a customer who just received a direct deposit may not have their SpotMe limit updated for a few minutes. Chime decided this trade-off was acceptable. The alternative — running the eligibility model live at authorization time — was too slow and added too much risk to the authorization path.

## Get Paid Early: Direct Deposit Detection and Funds Availability

Chime's "Get Paid Early" feature — where customers receive direct deposits up to two days before their employer's payroll date — is one of their most popular features and a key differentiator from traditional banking.

The engineering works by identifying ACH pre-notifications: payroll providers send notification files before the actual funds transfer. When Chime receives this notification, they immediately credit the customer's account from their own funds, ahead of the ACH settlement. The actual bank-to-bank transfer settles 1-2 days later, at which point Chime's advance is replenished.

The risk Chime takes is that the pre-notified direct deposit does not arrive (payroll failure, account closure, etc.). Their machine learning model evaluates the likelihood of the pre-notification converting to actual deposit based on historical patterns for that employer, direct deposit frequency, and account history.

## Mobile-First Engineering: Real-Time Push Notifications at Scale

Chime sends millions of push notifications daily — every transaction triggers a notification. The notification pipeline must be fast (users expect to feel their card being charged before they put their wallet away) and reliable (a missed payment notification erodes trust).

Their notification pipeline is event-driven: the authorization system publishes a transaction event to Kafka, a notification service consumes it, personalizes the message, and routes it to APNs (Apple) or FCM (Google). The end-to-end latency target is under 2 seconds from transaction authorization to notification appearing on the user's phone.

Personalization at scale requires understanding which notifications each user has opted into, what their locale and timezone is, and whether they are in quiet hours. Chime manages this configuration in Redis for fast access, with PostgreSQL as the durable store.

## Interview Implications

Chime interviews focus on financial systems reliability and consumer product engineering. Interviewers expect comfort with the constraints of the banking system — settlement timelines, ACH mechanics, card network authorization flows.

**System design questions**: design a real-time balance system for a neobank, design a push notification system for financial events, design a real-time fraud detection system for consumer debit. These questions have Chime-specific flavors: how do you handle the bank partner integration? What is your reconciliation strategy?

**Domain knowledge**: Understanding ACH (Automated Clearing House) basics — same-day ACH, ACH returns, NACHA rules — is valued. Chime engineers work with these constraints daily, and candidates who understand them can have richer technical conversations.

**Mobile engineering**: Chime is primarily a mobile product. iOS and Android experience is valued across the engineering org, not just on mobile-specific teams.
