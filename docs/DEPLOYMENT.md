# Deployment Guide - CareerSwiftr Interview Simulator

This guide covers deploying the Interview Simulator to production.

## Prerequisites

- PostgreSQL database (Neon, Supabase, Railway, or self-hosted)
- OpenAI API key (for Whisper transcription)
- Anthropic API key (for Claude feedback)
- Stripe account with production keys
- Cloud hosting account (Cloud Run, Railway, Render, or similar)
- CDN/static hosting (Vercel, Netlify, or Cloudflare Pages)

---

## Backend Deployment

### Option 1: Railway (Recommended for Simplicity)

1. **Create PostgreSQL Database**
   ```bash
   # Railway CLI
   railway login
   railway init
   railway add postgres
   railway variables get DATABASE_URL
   ```

2. **Deploy Backend**
   ```bash
   # From backend directory
   railway up
   ```

3. **Set Environment Variables in Railway Dashboard**
   ```
   DATABASE_URL=<auto-populated from postgres addon>
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_ID_PRO_MONTHLY=price_...
   CORS_ORIGINS=https://your-frontend-domain.com
   DEBUG=false
   ```

### Option 2: Google Cloud Run

1. **Build and Push Docker Image**
   ```bash
   cd backend

   # Authenticate with GCP
   gcloud auth configure-docker

   # Build image
   docker build -t gcr.io/YOUR_PROJECT_ID/interview-simulator-api:latest .

   # Push to Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/interview-simulator-api:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy interview-simulator-api \
     --image gcr.io/YOUR_PROJECT_ID/interview-simulator-api:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "DATABASE_URL=postgresql://...,OPENAI_API_KEY=sk-...,ANTHROPIC_API_KEY=sk-ant-...,STRIPE_SECRET_KEY=sk_live_...,CORS_ORIGINS=https://your-frontend.com"
   ```

3. **Set up Cloud SQL for PostgreSQL**
   ```bash
   gcloud sql instances create interview-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1

   gcloud sql databases create interview_simulator \
     --instance=interview-db
   ```

### Option 3: Render

1. **Create Web Service** from GitHub repo
2. **Set Build Command**: `cd backend && pip install uv && uv sync`
3. **Set Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add PostgreSQL database** from Render dashboard
5. **Configure environment variables** in Render dashboard

---

## Database Setup

### Run Migrations

After database is provisioned, run Alembic migrations:

```bash
cd backend

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"

# Run migrations
uv run alembic upgrade head

# Seed initial questions
uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
```

### Verify Connection

```bash
uv run python -c "
from app.db import get_session
import asyncio

async def test():
    async for session in get_session():
        result = await session.execute('SELECT 1')
        print('Database connected:', result.scalar())
        break

asyncio.run(test())
"
```

---

## Frontend Deployment

### Option 1: Vercel (Recommended)

1. **Connect GitHub Repository** to Vercel
2. **Configure Project**:
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Root Directory: `frontend`

3. **Set Environment Variables**:
   ```
   VITE_API_URL=https://your-backend-url.com/api/v1
   ```

4. **Deploy**: Push to main branch or use `vercel deploy`

### Option 2: Netlify

1. **Connect Repository**
2. **Build Settings**:
   - Base Directory: `frontend`
   - Build Command: `npm run build`
   - Publish Directory: `frontend/dist`

3. **Add Redirect Rule** (create `frontend/public/_redirects`):
   ```
   /*    /index.html   200
   ```

4. **Environment Variables**:
   ```
   VITE_API_URL=https://your-backend-url.com/api/v1
   ```

### Option 3: Cloudflare Pages

1. **Connect Repository**
2. **Build Configuration**:
   - Build command: `cd frontend && npm install && npm run build`
   - Build output directory: `frontend/dist`

3. **Environment Variables** in Settings > Environment Variables

---

## Stripe Configuration

### 1. Create Products and Prices

In Stripe Dashboard:
1. Go to **Products** > **Add Product**
2. Create "Interview Simulator Pro" product
3. Add monthly price (e.g., $19.99/month)
4. Copy the `price_id` (starts with `price_`)

### 2. Configure Webhook

1. Go to **Developers** > **Webhooks** > **Add endpoint**
2. Set URL: `https://your-backend-url.com/api/v1/subscriptions/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook signing secret (`whsec_...`)

### 3. Update Environment Variables

```bash
STRIPE_SECRET_KEY=sk_live_...          # From Stripe Dashboard > API keys
STRIPE_WEBHOOK_SECRET=whsec_...         # From webhook endpoint
STRIPE_PRICE_ID_PRO_MONTHLY=price_...   # From product pricing
```

### 4. Test Webhook (Optional)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook

# Trigger test event
stripe trigger checkout.session.completed
```

---

## Environment Variables Reference

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `OPENAI_API_KEY` | OpenAI API key for Whisper | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | `sk-ant-...` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |
| `STRIPE_PRICE_ID_PRO_MONTHLY` | Stripe price ID for Pro tier | `price_...` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `https://app.example.com` |
| `DEBUG` | Debug mode (false in production) | `false` |

### Backend (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT signing | Auto-generated |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.example.com/api/v1` |

---

## Post-Deployment Checklist

```
Verification:
[ ] Backend health check: GET /api/v1/health returns 200
[ ] Frontend loads without errors
[ ] User registration works
[ ] User login works
[ ] Create interview works
[ ] Audio upload works
[ ] Transcription processes (check logs)
[ ] Feedback generation works
[ ] Stripe checkout redirects correctly
[ ] Stripe webhook received (check Stripe dashboard)
[ ] Subscription upgrade reflected in app

Monitoring:
[ ] Set up error alerting (Sentry recommended)
[ ] Configure uptime monitoring
[ ] Set up database backups
[ ] Monitor API response times
[ ] Track Stripe webhook failures
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection string
psql "postgresql://user:pass@host:5432/db" -c "SELECT 1"

# Check async driver
# Ensure DATABASE_URL uses postgresql+asyncpg:// not postgresql://
```

### CORS Errors

1. Verify `CORS_ORIGINS` includes frontend domain with protocol
2. Check for trailing slashes (should not have any)
3. Ensure backend is accessible from frontend domain

### Stripe Webhook Failures

1. Check webhook signing secret matches
2. Verify endpoint URL is accessible
3. Check Stripe dashboard for webhook logs
4. Ensure SSL certificate is valid

### Audio Processing Issues

1. Verify `OPENAI_API_KEY` is set and valid
2. Check audio file permissions in uploads directory
3. Monitor background task logs for errors

---

## Security Recommendations

1. **Use environment secrets**, never commit API keys
2. **Enable HTTPS** for all endpoints
3. **Set `DEBUG=false`** in production
4. **Configure rate limiting** (already implemented in middleware)
5. **Regular database backups** via provider's backup system
6. **Monitor for suspicious activity** in Stripe dashboard
7. **Rotate API keys** periodically
