# Pre-Launch Checklist - Interview Simulator

**Purpose**: Every item must be TRUE before accepting first paying customer.
**Last Updated**: 2026-01-31

---

## CRITICAL PATH (Blocking)

### Stripe Configuration
- [ ] Stripe account in **live mode** (not test)
- [ ] Products created:
  - [ ] Pro Monthly ($19/mo) - `price_xxx`
  - [ ] Pro Annual ($290/yr) - `price_xxx`
  - [ ] Founding Member ($19/mo lifetime) - `price_xxx`
- [ ] Webhook endpoint registered: `https://interview-simulator-api-production.up.railway.app/api/v1/subscriptions/webhook`
- [ ] Webhook events enabled:
  - [ ] `checkout.session.completed`
  - [ ] `customer.subscription.updated`
  - [ ] `customer.subscription.deleted`
- [ ] Webhook secret set in Railway: `STRIPE_WEBHOOK_SECRET`

### Environment Variables (Railway Backend)
- [ ] `STRIPE_SECRET_KEY` = `sk_live_xxx` (LIVE key, not test)
- [ ] `STRIPE_WEBHOOK_SECRET` = `whsec_xxx`
- [ ] `STRIPE_PRICE_ID_PRO_MONTHLY` = actual price ID
- [ ] `STRIPE_PRICE_ID_PRO_ANNUAL` = actual price ID
- [ ] `DATABASE_URL` = production PostgreSQL
- [ ] `SECRET_KEY` = secure random string
- [ ] `FRONTEND_URL` = `https://app.codeswiftr.com`

### Frontend Build
- [ ] `npm run build` succeeds without errors
- [ ] `.env.production` has correct `VITE_API_URL`
- [ ] Deployed to Cloudflare Pages
- [ ] `https://app.codeswiftr.com` loads correctly

### Backend Health
- [ ] `https://interview-simulator-api-production.up.railway.app/health` returns 200
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Redis connection working (if used)

---

## PAYMENT FLOW VERIFICATION

### End-to-End Test (Do This Manually)
- [ ] Create test account on app.codeswiftr.com
- [ ] Navigate to Pricing page
- [ ] Click "Upgrade to Pro"
- [ ] Complete Stripe checkout (use test card if still in test mode)
- [ ] Verify webhook received (check Railway logs)
- [ ] Verify user upgraded in database
- [ ] Verify subscription status shows on Settings page
- [ ] Test cancellation flow
- [ ] Test customer portal access

### Stripe Dashboard Checks
- [ ] Test webhook with: `stripe trigger checkout.session.completed`
- [ ] Verify webhook logs show successful delivery
- [ ] Check for any failed webhook attempts

---

## USER EXPERIENCE

### Registration Flow
- [ ] Sign up with email works
- [ ] Email verification sends (if enabled)
- [ ] Login works after registration
- [ ] Password reset flow works

### Core Product
- [ ] User can create interview session
- [ ] Audio recording works
- [ ] Transcription processes correctly
- [ ] AI feedback generates
- [ ] Results display properly

### Subscription Limits
- [ ] Free tier limited to 5 interviews/month
- [ ] Pro tier has unlimited interviews
- [ ] Limit enforcement works correctly
- [ ] Upgrade prompt shows when limit reached

---

## LEGAL & COMPLIANCE

- [ ] Terms of Service page exists and is linked
- [ ] Privacy Policy page exists and is linked
- [ ] Stripe checkout shows correct business name
- [ ] Refund policy documented
- [ ] GDPR/data handling documented (if EU users)

---

## MONITORING & ALERTS

- [ ] Error tracking configured (Sentry/similar)
- [ ] Payment failure alerts set up
- [ ] Uptime monitoring for API endpoint
- [ ] Log retention configured in Railway

---

## CONTENT READY

- [ ] Pricing page copy finalized
- [ ] Feature descriptions accurate
- [ ] FAQ answers common questions
- [ ] First blog post ready to publish
- [ ] Social media posts drafted

---

## FOUNDING MEMBER SPECIFIC

- [ ] Founding member price created in Stripe
- [ ] Counter mechanism for 20-customer limit
- [ ] Founding member messaging on pricing page
- [ ] Scarcity/urgency copy reviewed

---

## QUICK VERIFICATION COMMANDS

```bash
# Check backend health
curl https://interview-simulator-api-production.up.railway.app/health

# Check frontend loads
curl -I https://app.codeswiftr.com

# Test Stripe webhook (requires stripe CLI)
stripe trigger checkout.session.completed \
  --stripe-account default

# Check Railway logs
railway logs --service interview-simulator-api

# Verify frontend build
cd frontend && npm run build

# Check env vars are set (Railway)
railway variables --service interview-simulator-api
```

---

## SIGN-OFF

| Area | Verified By | Date |
|------|-------------|------|
| Stripe Live Mode | | |
| Payment Flow E2E | | |
| Frontend Deployed | | |
| Backend Healthy | | |
| Legal Pages | | |
| **LAUNCH APPROVED** | | |

---

## ROLLBACK PLAN

If critical issues found post-launch:

1. **Payment Issues**: Switch Stripe to test mode, notify affected users
2. **Backend Down**: Railway automatic rollback or `railway rollback`
3. **Frontend Issues**: Cloudflare rollback to previous deployment
4. **Data Issues**: Restore from Railway PostgreSQL backup

---

## EMERGENCY CONTACTS

- Stripe Support: dashboard.stripe.com/support
- Railway Support: railway.app/help
- Cloudflare Support: dash.cloudflare.com/support
