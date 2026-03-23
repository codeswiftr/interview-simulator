# Railway Deployment Checklist - Interview Simulator Backend

**Project**: Interview Simulator API
**Domain**: app.codeswiftr.com (API)
**Stack**: FastAPI + PostgreSQL + Redis
**Deploy Time**: ~5-7 minutes (first deploy), ~2-3 minutes (updates)

---

## Prerequisites

### 1. Railway Account Setup
- [ ] Create account at [railway.app](https://railway.app)
- [ ] Add payment method (required for custom domains and production use)
- [ ] Verify email address

### 2. Install Railway CLI
```bash
# macOS (Homebrew)
brew install railway

# Or npm
npm install -g @railway/cli

# Verify installation
railway --version

# Login to Railway
railway login
```

### 3. Prepare Secrets
Gather the following API keys and secrets before starting:
- [ ] `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- [ ] `OPENAI_API_KEY` - From [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] `ANTHROPIC_API_KEY` - From [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- [ ] `STRIPE_SECRET_KEY` - From [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
- [ ] `STRIPE_WEBHOOK_SECRET` - From Stripe webhook configuration
- [ ] `RESEND_API_KEY` - From [resend.com/api-keys](https://resend.com/api-keys) (optional)
- [ ] `SENTRY_DSN` - From [sentry.io](https://sentry.io) (optional)
- [ ] `POSTHOG_API_KEY` - From [posthog.com](https://posthog.com) (optional)

---

## Step 1: Create Railway Project

### 1.1 Initialize from Backend Directory
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend

# Create new Railway project
railway init

# Follow prompts:
# - Project name: "interview-simulator" or similar
# - Start with empty project: Yes
```

### 1.2 Link to Existing Project (if already created via web)
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend

# List available projects
railway projects

# Link to existing project
railway link
# Select your project from the list
```

---

## Step 2: Add PostgreSQL Database

### 2.1 Add PostgreSQL Plugin
```bash
# Via CLI (in backend directory)
railway add --plugin postgresql

# Or via Railway Dashboard:
# 1. Go to your project
# 2. Click "+ New"
# 3. Select "Database" → "PostgreSQL"
```

### 2.2 Verify Database Connection String
Railway automatically creates and injects `DATABASE_URL` into your service.

**Important**: Railway's default `DATABASE_URL` uses `postgresql://` format. Your FastAPI app with asyncpg needs `postgresql+asyncpg://`.

The app's config.py already handles this via the `async_database_url` property, but you can manually set it:
```bash
# View auto-injected DATABASE_URL
railway variables

# The app will automatically convert postgresql:// to postgresql+asyncpg://
# No manual action needed unless you want to override
```

---

## Step 3: Add Redis Cache

### 3.1 Add Redis Plugin
```bash
# Via CLI (in backend directory)
railway add --plugin redis

# Or via Railway Dashboard:
# 1. Go to your project
# 2. Click "+ New"
# 3. Select "Database" → "Redis"
```

### 3.2 Verify Redis Connection String
Railway automatically creates `REDIS_URL`:
```bash
railway variables

# Look for: REDIS_URL=redis://default:...@...railway.app:PORT
```

---

## Step 4: Configure Environment Variables

### 4.1 Set Critical Environment Variables
```bash
# Navigate to backend directory
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend

# Generate and set SECRET_KEY
export SECRET_KEY=$(openssl rand -hex 32)
railway variables --set "SECRET_KEY=$SECRET_KEY"

# Or set directly
railway variables --set "SECRET_KEY=$(openssl rand -hex 32)"

# Set AI API keys
railway variables --set "OPENAI_API_KEY=sk-..."
railway variables --set "ANTHROPIC_API_KEY=sk-ant-..."

# Set Stripe keys (for payments)
railway variables --set "STRIPE_SECRET_KEY=sk_live_..."
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_..."

# Set Stripe price IDs (from your Stripe dashboard)
railway variables --set "STRIPE_PRICE_ID_PRO_MONTHLY=price_..."
railway variables --set "STRIPE_PRICE_ID_PRO_ANNUAL=price_..."
railway variables --set "STRIPE_PRICE_ID_TEAM_MONTHLY=price_..."
railway variables --set "STRIPE_PRICE_ID_TEAM_ANNUAL=price_..."
```

### 4.2 Set Application Configuration
```bash
# Set environment to production
railway variables --set "ENVIRONMENT=production"
railway variables --set "DEBUG=false"

# Set CORS origins (critical for security)
# Include both custom domain and Cloudflare Pages domain
railway variables --set "CORS_ORIGINS=https://app.codeswiftr.com,https://interview-simulator-4bo.pages.dev"

# Set frontend URL (for email links)
railway variables --set "FRONTEND_URL=https://app.codeswiftr.com"
```

### 4.3 Set Optional Services
```bash
# Email (Resend - recommended)
railway variables --set "RESEND_API_KEY=re_..."
railway variables --set "RESEND_FROM_EMAIL=hello@codeswiftr.com"
railway variables --set "RESEND_FROM_NAME=Interview Simulator"

# Or SMTP (alternative)
railway variables --set "SMTP_HOST=smtp.gmail.com"
railway variables --set "SMTP_PORT=587"
railway variables --set "SMTP_USER=your-email@gmail.com"
railway variables --set "SMTP_PASSWORD=your-app-password"

# Error monitoring (Sentry)
railway variables --set "SENTRY_DSN=https://...@sentry.io/..."

# Analytics (PostHog)
railway variables --set "POSTHOG_API_KEY=phc_..."
railway variables --set "POSTHOG_HOST=https://app.posthog.com"
```

### 4.4 Verify All Variables
```bash
railway variables

# Expected variables:
# - DATABASE_URL (auto-injected by PostgreSQL plugin)
# - REDIS_URL (auto-injected by Redis plugin)
# - SECRET_KEY
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - STRIPE_SECRET_KEY
# - STRIPE_WEBHOOK_SECRET
# - STRIPE_PRICE_ID_PRO_MONTHLY
# - STRIPE_PRICE_ID_PRO_ANNUAL
# - CORS_ORIGINS
# - ENVIRONMENT=production
# - DEBUG=false
# - FRONTEND_URL
```

---

## Step 5: Deploy Application

### 5.1 Deploy from Local Directory
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend

# Deploy current directory
railway up

# This will:
# 1. Upload your code to Railway
# 2. Build using Dockerfile
# 3. Run database migrations (alembic upgrade head)
# 4. Start the service with uvicorn
```

### 5.2 Monitor Deployment
```bash
# Watch deployment logs
railway logs

# Or via Railway Dashboard:
# Go to your service → "Deployments" tab → Click latest deployment
```

### 5.3 Deployment Troubleshooting
**Build fails with "uv not found"**:
- Railway.json specifies Dockerfile, so this shouldn't happen
- Verify `railway.json` has `"builder": "DOCKERFILE"`

**Migration fails**:
- Check DATABASE_URL is set: `railway variables | grep DATABASE_URL`
- Verify database is running: Check PostgreSQL service in dashboard

**Health check fails**:
- Verify `/health` endpoint exists in your app
- Check port binding: Railway injects `$PORT` environment variable
- Dockerfile CMD uses `--port $PORT`

**App crashes immediately**:
- Check for missing environment variables: `railway logs | grep "Missing"`
- Verify SECRET_KEY is set and not default value

---

## Step 6: Custom Domain Setup

### 6.1 Generate Railway Domain
Railway automatically provides a domain like `interview-simulator-api-production.up.railway.app`.

To verify:
```bash
railway domain
```

### 6.2 Add Custom Domain (api.codeswiftr.com)
```bash
# Add custom domain via CLI
railway domain

# Or via Dashboard (recommended):
# 1. Go to service settings
# 2. Click "Settings" → "Public Networking"
# 3. Click "Custom Domain"
# 4. Enter: api.codeswiftr.com
```

### 6.3 Configure DNS (Cloudflare)
1. Go to Cloudflare dashboard → `codeswiftr.com` → DNS
2. Add CNAME record:
   ```
   Type: CNAME
   Name: api
   Target: interview-simulator-api-production.up.railway.app
   Proxy status: DNS only (grey cloud) - IMPORTANT!
   TTL: Auto
   ```
3. Railway will automatically provision SSL certificate via Let's Encrypt (5-10 minutes)

**Note**: Do NOT use Cloudflare proxy (orange cloud) initially. Once SSL is provisioned by Railway, you can enable proxy if needed.

### 6.4 Update Frontend API URL
Update frontend environment to use custom domain:
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend

# Update .env.production
echo 'VITE_API_URL=https://api.codeswiftr.com/api/v1' > .env.production

# Rebuild and redeploy frontend
npm run build
wrangler pages deploy dist --project-name=interview-simulator --branch=main
```

### 6.5 Update CORS Configuration
```bash
# Update backend CORS to include custom domain
railway variables --set "CORS_ORIGINS=https://app.codeswiftr.com,https://interview-simulator-4bo.pages.dev"

# Redeploy backend
railway redeploy -y
```

---

## Step 7: Post-Deploy Verification

### 7.1 Health Check
```bash
# Test Railway domain
curl https://interview-simulator-api-production.up.railway.app/health

# Expected response:
# {"status":"healthy","timestamp":"..."}

# Test custom domain (if configured)
curl https://api.codeswiftr.com/health
```

### 7.2 API Documentation
```bash
# Check Swagger docs
open https://interview-simulator-api-production.up.railway.app/docs

# Or custom domain
open https://api.codeswiftr.com/docs
```

### 7.3 Database Migrations
```bash
# Verify migrations ran successfully
railway logs | grep "alembic upgrade head"

# Should see: "Running upgrade ... -> head"

# Or manually check migration status
railway run alembic current
```

### 7.4 Test Critical Endpoints
```bash
# Test authentication endpoint
curl -X POST https://api.codeswiftr.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'

# Expected: 201 Created with user data
```

### 7.5 Monitor Application Logs
```bash
# Stream live logs
railway logs --follow

# Filter for errors
railway logs | grep ERROR

# Check recent deployments
railway deployments
```

### 7.6 Test Frontend Integration
1. Open https://app.codeswiftr.com
2. Try to register/login
3. Verify CORS is working (no CORS errors in browser console)
4. Test core features: interview creation, audio upload, feedback generation

---

## Step 8: Production Readiness

### 8.1 Configure Stripe Webhooks
1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. Add endpoint: `https://api.codeswiftr.com/api/v1/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy webhook signing secret
5. Update Railway:
   ```bash
   railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_..."
   railway redeploy -y
   ```

### 8.2 Configure Email Domain (Resend)
1. Go to [Resend Dashboard → Domains](https://resend.com/domains)
2. Add domain: `codeswiftr.com`
3. Add DNS records to Cloudflare:
   - SPF: `v=spf1 include:_spf.resend.com ~all`
   - DKIM: (provided by Resend)
   - DMARC: `v=DMARC1; p=none`
4. Verify domain in Resend
5. Confirm `RESEND_FROM_EMAIL=hello@codeswiftr.com` in Railway

### 8.3 Set Up Monitoring Alerts
Via Railway Dashboard:
1. Go to Project Settings → Notifications
2. Add Slack/Discord webhook (optional)
3. Enable deployment notifications
4. Enable error alerts

Via Sentry (recommended):
1. Set `SENTRY_DSN` in Railway variables
2. Configure alert rules in Sentry dashboard
3. Set up error rate alerts

### 8.4 Database Backups
Railway automatically backs up PostgreSQL databases. To verify:
1. Go to PostgreSQL service → Backups tab
2. Ensure automatic backups are enabled
3. Manual backup: Click "Create Backup"

---

## Step 9: Rollback Procedure

### 9.1 View Deployment History
```bash
# List recent deployments
railway deployments

# Or via Dashboard:
# Go to service → Deployments tab
```

### 9.2 Rollback to Previous Deployment
```bash
# Via Dashboard (recommended):
# 1. Go to Deployments tab
# 2. Find working deployment
# 3. Click "..." → "Redeploy"

# Via CLI (if deployment ID known):
railway redeploy <deployment-id>
```

### 9.3 Rollback Database Migration (if needed)
```bash
# Connect to Railway shell
railway run bash

# View migration history
alembic history

# Downgrade one migration
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision-id>

# Exit shell
exit
```

### 9.4 Emergency Rollback Checklist
If production is broken:
1. **Immediate**: Rollback deployment via Railway dashboard (< 1 minute)
2. **Verify**: Check health endpoint and critical features
3. **Investigate**: Review logs for root cause
   ```bash
   railway logs --tail 100
   ```
4. **Fix**: Fix issue locally and test thoroughly
   ```bash
   cd backend && uv run pytest && uv run alembic upgrade head
   ```
5. **Deploy**: Deploy fix with confidence
   ```bash
   railway up
   ```
6. **Monitor**: Watch logs and metrics for 15 minutes

---

## Common Issues and Solutions

### Issue: 502 Bad Gateway
**Cause**: App not binding to correct port or not starting
**Solution**:
```bash
# Verify PORT environment variable in logs
railway logs | grep PORT

# Ensure Dockerfile CMD uses $PORT:
# CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Issue: Database Connection Failed
**Cause**: Wrong DATABASE_URL format or database not ready
**Solution**:
```bash
# Verify DATABASE_URL is injected
railway variables | grep DATABASE_URL

# The app auto-converts to postgresql+asyncpg://
# If issues persist, check PostgreSQL service status in dashboard
```

### Issue: CORS Errors in Browser
**Cause**: CORS_ORIGINS not set correctly
**Solution**:
```bash
# Verify CORS origins
railway variables | grep CORS_ORIGINS

# Should include frontend domains:
# CORS_ORIGINS=https://app.codeswiftr.com,https://interview-simulator-4bo.pages.dev

# Update if needed:
railway variables --set "CORS_ORIGINS=https://app.codeswiftr.com,https://interview-simulator-4bo.pages.dev"
railway redeploy -y
```

### Issue: Migrations Don't Run
**Cause**: Migration command failing in railway.json startCommand
**Solution**:
```bash
# Check logs for migration errors
railway logs | grep alembic

# Manually run migrations:
railway run alembic upgrade head

# If successful, issue is in startCommand
# Verify railway.json has:
# "startCommand": "alembic upgrade head && uvicorn ..."
```

### Issue: Custom Domain SSL Not Provisioning
**Cause**: Cloudflare proxy enabled or DNS misconfigured
**Solution**:
1. Disable Cloudflare proxy (grey cloud) temporarily
2. Wait 5-10 minutes for Railway to provision SSL
3. Verify SSL: `curl -I https://api.codeswiftr.com`
4. Check Railway dashboard for SSL status
5. Re-enable Cloudflare proxy if needed (after SSL provisioned)

### Issue: "Missing required environment variables"
**Cause**: Critical env vars not set or using default values
**Solution**:
```bash
# Check which vars are missing
railway logs | grep "Missing"

# Set missing variables:
railway variables --set "VARIABLE_NAME=value"
railway redeploy -y

# Critical vars: SECRET_KEY, DATABASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY
```

---

## Performance Optimization

### Enable Connection Pooling (PostgreSQL)
Railway PostgreSQL includes connection pooling by default via PgBouncer. No action needed.

### Configure Redis Caching
Redis is already configured via `REDIS_URL`. To verify:
```bash
# Test Redis connection
railway run python -c "import redis; import os; r = redis.from_url(os.getenv('REDIS_URL')); print('Redis OK:', r.ping())"

# Should print: Redis OK: True
```

### Monitor Resource Usage
```bash
# Via Railway Dashboard:
# Service → Metrics tab
# Shows: CPU, Memory, Network, Request rate

# Adjust replica count if needed (in railway.json):
# "numReplicas": 2
```

---

## Maintenance Tasks

### Update Dependencies
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend

# Update dependencies
uv sync --upgrade

# Run tests
uv run pytest

# Deploy
railway up
```

### Run Database Backup
```bash
# Via Railway Dashboard:
# PostgreSQL service → Backups → "Create Backup"

# Restore from backup:
# PostgreSQL service → Backups → Select backup → "Restore"
```

### View Application Metrics
```bash
# Via Railway Dashboard:
# Service → Metrics tab

# Shows: CPU, Memory, Network, Request rate, Error rate
```

### Check for Security Updates
```bash
cd backend

# Run security audit
uv run pip-audit

# Update vulnerable packages
uv sync --upgrade
```

---

## Security Checklist

- [ ] `SECRET_KEY` is randomly generated (not default value)
- [ ] `DEBUG=false` in production
- [ ] `ENVIRONMENT=production`
- [ ] `CORS_ORIGINS` set to specific domains (no wildcards)
- [ ] All API keys stored in Railway variables (not in code)
- [ ] HTTPS enforced for custom domain
- [ ] Stripe webhook secret configured
- [ ] Database credentials rotated from defaults
- [ ] Sentry DSN configured for error monitoring
- [ ] PostgreSQL backups enabled
- [ ] No default passwords in use

---

## Quick Reference Commands

```bash
# Deploy
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
railway up

# View logs
railway logs --follow

# List environment variables
railway variables

# Set environment variable
railway variables --set "KEY=value"

# Redeploy (after env var change)
railway redeploy -y

# Open Railway dashboard
railway open

# Connect to database
railway run psql

# Run shell in production environment
railway run bash

# View service status
railway status

# View deployments
railway deployments

# Run Alembic migrations manually
railway run alembic upgrade head

# Check current migration
railway run alembic current

# View migration history
railway run alembic history
```

---

## Support and Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Project CLAUDE.md**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/CLAUDE.md`
- **Backend README**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend/README.md`
- **Production Readiness**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/docs/PRODUCTION_READINESS.md`

---

## Deployment Status Tracking

| Component | Status | URL | Notes |
|-----------|--------|-----|-------|
| Backend API | 🔴 Not Deployed | - | Ready to deploy |
| PostgreSQL | - | - | Will auto-provision |
| Redis | - | - | Will auto-provision |
| Custom Domain | 🔴 Not Configured | api.codeswiftr.com | DNS pending |
| SSL Certificate | - | - | Auto-provisions after DNS |
| Stripe Webhooks | 🔴 Not Configured | - | Configure post-deploy |

**Next Steps**:
1. Run through Steps 1-5 to deploy backend
2. Configure custom domain (Step 6)
3. Verify deployment (Step 7)
4. Configure webhooks and monitoring (Step 8)

---

**Last Updated**: 2026-02-06
**Deployment Ready**: Yes
**Estimated Time**: 20-30 minutes (first deploy)
