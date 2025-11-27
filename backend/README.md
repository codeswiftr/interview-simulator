# CareerSwiftr Interview Simulator Backend

FastAPI + SQLModel service powering the interview simulator. Use `uv run uvicorn app.main:app --reload` to start locally and `uv run pytest` to run tests.

## Environment Setup

Create a `.env` file in the `backend/` directory with the following variables:

### Required Variables

- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+asyncpg://postgres:postgres@localhost:5432/interview_simulator`)
- `REDIS_URL`: Redis connection string (e.g., `redis://localhost:6379/0`)
- `SECRET_KEY`: Strong random key for JWT signing (generate with: `openssl rand -hex 32`)
- `ANTHROPIC_API_KEY`: Claude API key for content analysis
- `OPENAI_API_KEY`: OpenAI API key for Whisper transcription

### Optional Variables (for Subscriptions)

- `STRIPE_SECRET_KEY`: Stripe secret key (test mode: `sk_test_...`)
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret (from Stripe dashboard)
- `STRIPE_PRICE_ID_PRO_MONTHLY`: Stripe price ID for Pro monthly subscription
- `STRIPE_PRICE_ID_PRO_ANNUAL`: Stripe price ID for Pro annual subscription

### Stripe Webhook Setup (Local Development)

1. Install ngrok: `brew install ngrok` (macOS) or download from ngrok.com
2. Start ngrok: `ngrok http 8000`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. In Stripe Dashboard → Developers → Webhooks, add endpoint:
   - URL: `https://abc123.ngrok.io/api/v1/subscriptions/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
5. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET` in your `.env` file
