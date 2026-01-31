# Revenue Sprint - Interview Simulator

**Date**: 2026-01-31
**Goal**: First 5 paying customers
**Status**: In Progress

## Executive Summary

Interview Simulator is LIVE at app.codeswiftr.com with complete infrastructure:
- Backend: FastAPI + SQLModel + PostgreSQL + Redis (Railway)
- Frontend: React 19 + TypeScript + Vite (Cloudflare Pages)
- Payments: Stripe integration fully implemented
- Content: 42k blog, 12k social, 14k email assets ready

## Test Coverage Analysis (Tier 1 Critical)

**Current State**: 67% coverage (585 passed, 12 failed, 554 skipped)
**Target**: 70%+ coverage

### Top 3 Untested Critical Areas

| Priority | Area | Coverage | Revenue Impact |
|----------|------|----------|----------------|
| **P0** | Subscriptions/Billing | 23% | DIRECT - Money path |
| **P0** | Authentication/Users | 25-38% | Trust & Security |
| **P1** | Security Headers Middleware | 0% | Production security |

#### 1. Subscriptions/Billing (23% coverage) - CRITICAL
**File**: `app/api/subscriptions.py`

Untested flows:
- Stripe webhook handlers (`checkout.session.completed`, `subscription.updated`, `subscription.deleted`)
- Checkout session creation with edge cases
- Subscription sync from Stripe API
- Customer portal session creation
- Cancellation at period end
- Trial period handling
- Rewardful affiliate tracking

**Risk**: Payment failures could silently fail without proper test coverage.

#### 2. Authentication & Users (25-38% coverage)
**Files**: `app/api/auth.py`, `app/api/users.py`, `app/dependencies.py`

Untested flows:
- Token refresh rotation
- Password reset flow
- Invalid/expired token handling
- User profile updates
- Email change conflicts
- Delete cascade

**Risk**: Auth bugs block all revenue - users can't sign up or log in.

#### 3. Security Headers Middleware (0% coverage)
**File**: `app/middleware/security_headers.py`

Completely untested:
- HSTS headers
- X-Content-Type-Options
- X-Frame-Options
- CSP headers

**Risk**: Security vulnerabilities in production app handling payments.

### Blocking Issues

1. **12 failing tests** in `test_content_analyzer.py` due to `LLMClient` API change
   - Fix: Update mocks to use current LLM client interface

2. **554 skipped tests** due to "Database not available"
   - Fix: Add test database configuration (pytest-postgresql or Docker)

## Payment Infrastructure Status

### Backend (Verified)
- [x] Stripe SDK integrated
- [x] Checkout session creation (`/api/v1/subscriptions/checkout`)
- [x] Webhook handler (`/api/v1/subscriptions/webhook`)
- [x] Customer portal (`/api/v1/subscriptions/portal`)
- [x] Subscription status sync
- [x] Cancellation flow
- [x] Rewardful affiliate tracking support

### Frontend (Verified)
- [x] `PricingPage.tsx` - Full pricing display (22k lines)
- [x] `UpgradeModal.tsx` - Checkout flow with analytics
- [x] `SettingsPage.tsx` - Billing management (34k lines)
- [x] `BillingInfo.tsx` - Subscription details
- [x] `SubscriptionCard.tsx` - Plan display

### Environment Variables Required
```
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxx
STRIPE_PRICE_ID_PRO_ANNUAL=price_xxx
```

## Agent Dispatch Status

| Agent | Task | Status | Notes |
|-------|------|--------|-------|
| codex | Verify Stripe webhook handlers | Pending | `stripe trigger checkout.session.completed` |
| gemini | Research competitor pricing | Pending | Pramp, Interviewing.io, etc. |
| opencode | Check frontend payment flow | Pending | Visual verification |

## Competitor Pricing Research (To Be Completed)

Target competitors for pricing analysis:
- Pramp (free peer practice)
- Interviewing.io (paid mock interviews)
- Exponent (subscription model)
- LeetCode Premium
- AlgoExpert

## Recommended Next Actions

### Immediate (This Sprint)
1. [ ] Verify Stripe webhooks work in production (`stripe trigger` test)
2. [ ] Complete competitor pricing research
3. [ ] Increase subscription test coverage to 70%+
4. [ ] Fix 12 failing ContentAnalyzer tests

### Short-term (Next Sprint)
1. [ ] Add test database for skipped integration tests
2. [ ] Security headers middleware tests
3. [ ] Auth flow comprehensive testing
4. [ ] Load testing for payment endpoints

### Revenue Activation
1. [ ] Announce Pro tier availability to existing users
2. [ ] Publish pricing page content
3. [ ] Enable Stripe production mode
4. [ ] Set up Rewardful affiliate program

## Blockers Identified

| Blocker | Impact | Owner | Resolution |
|---------|--------|-------|------------|
| LLMClient API change | 12 failing tests | Backend | Update mocks |
| No test DB in CI | 554 skipped tests | DevOps | Add pytest-postgresql |
| Webhook verification | Unknown prod status | Backend | Run `stripe trigger` |

## Session Notes

- Subscriptions.py has full Stripe integration (547 lines)
- Frontend payment flow is complete with analytics tracking
- Content assets ready for launch (42k blog, 12k social, 14k email)
- Fleet agents available: gemini, codex, opencode, pi, kimi
