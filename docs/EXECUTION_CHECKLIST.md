# Interview Simulator - Revenue Launch Execution Checklist

**Date**: 2026-01-31
**Goal**: First 5 paying customers
**Pricing**: $19/mo | $290/yr | Founding Member $19/mo for life (first 20)

---

## Phase 1: Pricing Configuration

### Backend
- [ ] Create Stripe products and prices:
  - [ ] Pro Monthly: $19/mo (`price_pro_monthly`)
  - [ ] Pro Annual: $290/yr (`price_pro_annual`)
  - [ ] Founding Member: $19/mo recurring (`price_founding_member`)
- [ ] Update Railway environment variables:
  - [ ] `STRIPE_PRICE_ID_PRO_MONTHLY`
  - [ ] `STRIPE_PRICE_ID_PRO_ANNUAL`
  - [ ] `STRIPE_PRICE_ID_FOUNDING` (new)
- [ ] Verify webhook endpoint is registered in Stripe Dashboard
- [ ] Test webhooks with `stripe trigger checkout.session.completed`

### Frontend
- [ ] Update PricingPage.tsx with new prices:
  - [ ] Monthly: $19/mo
  - [ ] Annual: $290/yr (save $38)
  - [ ] Add Founding Member badge/tier (limited to 20)
- [ ] Verify UpgradeModal fetches correct price IDs
- [ ] Add founding member countdown/scarcity indicator
- [ ] Test checkout flow end-to-end

---

## Phase 2: Content Publishing (Staggered)

### Week 1: Dev.to + LinkedIn
| Day | Platform | Content Type | Status |
|-----|----------|--------------|--------|
| Mon | Dev.to | Technical blog post #1 | [ ] |
| Tue | LinkedIn | Launch announcement | [ ] |
| Wed | Dev.to | Technical blog post #2 | [ ] |
| Thu | LinkedIn | Feature highlight | [ ] |
| Fri | Dev.to | Tutorial post | [ ] |

### Week 2: Reddit + HN
| Day | Platform | Content Type | Status |
|-----|----------|--------------|--------|
| Mon | r/cscareerquestions | Value post (not promo) | [ ] |
| Tue | r/learnprogramming | Tutorial/resource share | [ ] |
| Wed | Hacker News | Show HN post | [ ] |
| Thu | Reddit follow-up | Engage comments | [ ] |
| Fri | HN engagement | Respond to feedback | [ ] |

### Week 3: Email Campaign
| Day | Segment | Email Type | Status |
|-----|---------|------------|--------|
| Mon | Waitlist | Launch announcement | [ ] |
| Wed | Engaged users | Founding member offer | [ ] |
| Fri | All subscribers | Feature deep-dive | [ ] |

---

## Phase 3: Founding Member Program

### Setup
- [ ] Create Stripe coupon for founding member pricing
- [ ] Set up tracking for 20-customer limit
- [ ] Design founding member badge for UI
- [ ] Create urgency messaging (X of 20 remaining)

### Landing Page Updates
- [ ] Add founding member section to PricingPage
- [ ] Countdown/scarcity widget
- [ ] Testimonial placeholders (update as received)
- [ ] FAQ section for founding member benefits

### Benefits to Communicate
- [x] $19/mo locked for life (vs $19/mo standard)
- [ ] Early access to new features
- [ ] Direct feedback channel
- [ ] Founding member badge on profile

---

## Phase 4: Launch Day Checklist

### Pre-Launch (T-1 day)
- [ ] Final pricing verification in Stripe
- [ ] Test complete checkout flow (use test mode)
- [ ] Verify email templates
- [ ] Prepare social media posts
- [ ] Brief support channel

### Launch (T-0)
- [ ] Switch Stripe to live mode
- [ ] Publish first Dev.to post
- [ ] Post LinkedIn announcement
- [ ] Send waitlist email
- [ ] Monitor error logs

### Post-Launch (T+1 day)
- [ ] Check for failed payments
- [ ] Respond to all comments/questions
- [ ] Track conversion metrics
- [ ] Gather early feedback

---

## Metrics to Track

| Metric | Target | Tracking |
|--------|--------|----------|
| Signups | 50 in week 1 | PostHog |
| Free → Pro conversion | 10% | Stripe Dashboard |
| Founding members | 20 (cap) | Manual count |
| Content engagement | 1000 views | Platform analytics |
| Email open rate | 30%+ | Email provider |

---

## Content Assets Ready

| Type | Count | Location |
|------|-------|----------|
| Blog posts | 42k words | `/content/blog/` |
| Social posts | 12k words | `/content/social/` |
| Email sequences | 14k words | `/content/email/` |

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Stripe webhook failure | Monitor logs, manual sync fallback | Backend |
| Content flagged as spam | Stagger posts, add value first | Marketing |
| Founding member oversell | Real-time counter, hard cap | Frontend |
| Negative feedback | Prepare response templates | Support |

---

## Agent Dispatch Log

| Time | Agent | Task | Status |
|------|-------|------|--------|
| 2026-01-31 | codex | Verify backend pricing config | Dispatched |
| 2026-01-31 | gemini | Competitor pricing research | Dispatched |
| 2026-01-31 | opencode | Check PricingPage structure | Dispatched |
| 2026-01-31 | codex | Verify pricing consistency | Dispatched |

---

## Quick Commands

```bash
# Check agent progress
tmux capture-pane -t forge-codeswiftr-com:codex -p | tail -30
tmux capture-pane -t forge-codeswiftr-com:opencode -p | tail -30

# Test Stripe webhooks
cd backend && stripe trigger checkout.session.completed

# Deploy frontend
cd frontend && npm run build && wrangler pages deploy dist

# Deploy backend
cd backend && railway up
```

---

## Sign-off

- [ ] Pricing verified (Backend + Frontend)
- [ ] Content scheduled
- [ ] Stripe live mode ready
- [ ] Monitoring in place
- [ ] **LAUNCH APPROVED**
