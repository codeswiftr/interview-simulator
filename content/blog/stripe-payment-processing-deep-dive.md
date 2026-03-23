# Stripe Payment Processing Deep Dive: Idempotency, Retries, and Financial Correctness

Building a reliable payment integration is not just about calling an API and handling success or failure. Financial systems demand a level of correctness that most software does not. When a network request fails mid-flight, you cannot tell whether the charge happened or not. When a webhook arrives twice, you cannot apply it twice. When a user double-clicks the checkout button, you cannot charge them twice. Every one of these scenarios has a wrong answer that costs real money, and Stripe's API is designed to make the right answer the easy answer — if you know how to use it.

## Idempotency Keys: The Foundation of Financial Correctness

An idempotency key is a client-generated unique string that you attach to a mutating API request. When Stripe receives a request with an idempotency key it has seen before, it returns the same response it returned the first time — without re-executing the operation. This makes your payment requests safe to retry without fear of duplicate charges.

The key technical requirement is that the idempotency key must be unique per logical operation. A common pattern is to derive it from the order ID and the payment attempt number: `order_${orderId}_attempt_${attemptNumber}`. If you use a random UUID generated at request time, you lose the benefit — a retry will generate a new UUID and create a new charge.

Stripe stores idempotency keys for 24 hours. During that window, any request with the same key and the same endpoint will return the cached response. If the parameters differ, Stripe returns a 400 error — an intentional safety check that prevents you from accidentally reusing a key with different amounts or currencies.

The atomicity requirement is subtle. Your application must persist the idempotency key before sending the request. If you generate the key, send the request, and then store the key after receiving the response, a crash between request and storage means you will generate a new key on retry and potentially double-charge. The safe pattern is: generate key, persist key to your database with the order in a pending state, then send the request.

## The Payment State Machine

A Stripe PaymentIntent moves through a well-defined state machine. Understanding the states is essential for building correct UI flows and webhook handlers.

The initial state is `requires_payment_method` — the intent exists but has no card attached. After a card is attached, it moves to `requires_confirmation`. After confirmation, it enters `processing`, where the card network authorization is happening. From `processing`, it transitions to `succeeded`, `requires_action` (for 3D Secure challenges), or `canceled`.

The `requires_action` state is worth special attention. When 3D Secure is triggered, your frontend must handle the redirect challenge and then confirm the payment again. Many integrations silently drop users who hit 3D Secure because the frontend assumes `processing` always resolves on its own.

The `canceled` state is terminal — you cannot uncanceled a PaymentIntent. If a user abandons checkout and returns later, you must create a new PaymentIntent. This has implications for your order model: an order should be able to hold multiple PaymentIntents, not a one-to-one relationship.

## Retry Logic and Exponential Backoff

Stripe's API returns HTTP 5xx errors for transient server issues and specific 4xx errors for idempotency conflicts or rate limits. Your retry logic needs to distinguish between these.

Safe to retry: 429 (rate limit), 500, 502, 503, 504. Not safe to retry without a new idempotency key: 400 with an idempotency conflict. Never retry: 402 (card declined) — retrying a declined card will not succeed and will annoy the customer.

Exponential backoff with jitter is standard: wait `min(cap, base * 2^attempt) + random_jitter` milliseconds between retries. The jitter prevents thundering herd problems when many clients retry simultaneously after a Stripe incident. A reasonable default is base=500ms, cap=30s, jitter=±20%.

The number of retries matters. Three to five retries covers the vast majority of transient failures. Beyond five retries, you are more likely dealing with a systematic problem than a transient one, and continuing to retry burns rate limit budget.

## Webhook Delivery Guarantees

Stripe delivers webhooks with at-least-once semantics. A webhook may be delivered more than once — Stripe retries failed deliveries (non-2xx responses or timeouts) over 72 hours with exponential backoff.

Your webhook handler must be idempotent. The standard pattern is to store the Stripe event ID in your database and check for it before processing. If the event ID already exists, return 200 immediately without re-processing.

Webhook signature verification is not optional. Stripe signs every webhook with your endpoint's signing secret using HMAC-SHA256. Skipping verification means any attacker can POST fake payment.succeeded events to your endpoint. The verification is a single function call in every Stripe SDK — there is no excuse for skipping it.

Webhook ordering is not guaranteed. A `payment_intent.succeeded` event might arrive before `payment_intent.created` in rare cases. Your handler must be defensive: if a webhook references an order that does not exist yet, either create a stub record or enqueue the event for later processing. Never silently discard an event because the referenced object does not exist.

## Engineering Implications for Interview Questions

When Stripe payment integration comes up in system design interviews, the questions that reveal deep understanding are about failure modes: what happens if your server crashes between charging and fulfilling the order, how do you handle a webhook that arrives for an order you already marked as fulfilled, and what does your retry loop look like when Stripe is degraded.

The answers all connect back to the same principle: financial operations require explicit handling of every state transition, not just the happy path. Idempotency keys, state machines, and at-least-once webhook processing are not Stripe-specific abstractions — they are the vocabulary of any correct distributed financial system.
