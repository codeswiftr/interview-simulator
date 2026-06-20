# Current Public Status

Last updated: 2026-06-20

Interview Simulator is a public product/codebase for AI-assisted interview
practice. The free-tier surface is live, and the repository contains the
FastAPI backend, React frontend, Stripe integration code, deployment notes, and
historical launch/revenue planning.

## Operating Truth

- Free-tier product surface: live.
- Deployment and analytics: ready enough for measurement.
- Billing and Team tier: implemented in code, but the paid upgrade path still
  needs Stripe Dashboard keys/webhooks and an end-to-end production checkout
  verification before it should be presented as fully live.
- Historical production/readiness docs remain useful as operating records, but
  they may describe a specific moment in the launch process rather than current
  truth.

## Before Claiming "Production-Ready"

Re-verify:

```bash
cd backend && uv run pytest
cd frontend && npm run build
gh pr checks <repair-pr>
```

For paid-path claims, also verify:

- Stripe products/prices exist in the intended mode.
- Webhook endpoint is registered and receiving events.
- Checkout succeeds from the live frontend.
- Subscription state is updated server-side after webhook delivery.
