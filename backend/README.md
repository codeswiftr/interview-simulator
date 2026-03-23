# CareerSwiftr Interview Simulator Backend

FastAPI + SQLModel service powering the interview simulator. Use `uv run uvicorn app.main:app --reload` to start locally and `uv run pytest` to run tests.

## Running Test Coverage

To run test coverage with database support:

```bash
# Option 1: Use the convenience script (recommended)
./scripts/run_coverage.sh

# Option 2: Manual steps
docker compose up -d postgres  # Start database
uv run pytest --cov=app --cov-report=term-missing --cov-report=json --cov-report=html
```

Coverage reports will be generated:
- Terminal output with line-by-line coverage
- JSON: `coverage.json`
- HTML: `htmlcov/index.html` (open in browser for detailed view)

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

## CLI

Interview Simulator includes an agent-friendly CLI for automation:

```bash
# Install CLI
uv pip install -e .

# Generate questions
interview-sim generate-questions --topic leadership --count 5

# Analyze transcript
interview-sim analyze-transcript --file transcript.txt --session-id <uuid>

# Export metrics
interview-sim export-metrics --period weekly --json

# Batch feedback generation
interview-sim batch-feedback --session-ids sessions.txt
```

All commands support `--json` flag for structured output following FORGE standards.

**Documentation:**
- [CLI Guide](docs/CLI.md) - Complete documentation
- [Quick Reference](docs/CLI_QUICK_REFERENCE.md) - One-page cheatsheet
- [Automation Examples](examples/cli_automation.py) - Python automation patterns

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Test CLI
./scripts/test_cli.sh
```
