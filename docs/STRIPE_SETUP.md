# Stripe Pricing Tiers Setup Guide

**Purpose:** Configure Stripe products and prices for Interview Simulator tiers.  
**Task:** Stripe Pricing Tiers Deployment (Priority #5)

---

## Tier Summary

| Tier | Price | Interviews/month | Stripe Product |
|------|-------|------------------|----------------|
| **Free** | $0 | 3 | (No product – built-in) |
| **Pro** | $29/month | Unlimited | Product: "Interview Simulator Pro" |
| **Enterprise** | Custom | Custom | Contact sales – no Stripe product |

---

## Step 1: Create Pro Product in Stripe Dashboard

1. Go to [Stripe Dashboard → Products](https://dashboard.stripe.com/products)
2. Click **Add product**
3. Configure:
   - **Name:** Interview Simulator Pro
   - **Description:** Unlimited interview practice with advanced AI feedback
   - **Image:** (Optional) Upload app logo

---

## Step 2: Create Pro Prices

### Pro Monthly ($29/month)

1. In the Pro product, click **Add price**
2. **Pricing model:** Recurring
3. **Price:** $29.00 USD
4. **Billing period:** Monthly
5. **Price description:** Pro Monthly
6. Save – copy the **Price ID** (e.g. `price_1ABC123...`)

### Pro Annual ($290/year – 2 months free)

1. Add another price to the Pro product
2. **Price:** $290.00 USD
3. **Billing period:** Yearly
4. **Price description:** Pro Annual
5. Save – copy the **Price ID**

---

## Step 3: Environment Variables

Add to `.env` (backend) and Railway environment:

```bash
# Stripe (required for checkout)
STRIPE_SECRET_KEY=sk_live_xxx          # or sk_test_xxx for test mode
STRIPE_WEBHOOK_SECRET=whsec_xxx        # From Stripe Webhooks

# Price IDs (from Step 2)
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxx
STRIPE_PRICE_ID_PRO_ANNUAL=price_xxx

# Optional: Trial
STRIPE_TRIAL_DAYS=7                   # 7-day free trial (optional)
```

---

## Step 4: Webhook Configuration

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. **Add endpoint**
3. **Endpoint URL:** `https://interview-simulator-api-production.up.railway.app/api/v1/subscriptions/webhook`
4. **Events to listen:**
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Save – copy the **Signing secret** (`whsec_...`) to `STRIPE_WEBHOOK_SECRET`

---

## Step 5: Test Mode Checklist

Before going live:

1. Use `sk_test_...` and `whsec_...` (test webhook) in development
2. Create test products/prices in Stripe Test mode
3. Run checkout flow: Register → Settings → Upgrade → Stripe Checkout
4. Use test card `4242 4242 4242 4242`
5. Verify webhook receives events (Stripe Dashboard → Webhooks → Logs)

---

## Backend Reference

The backend maps price IDs to tiers in `app/api/subscriptions.py`:

- `stripe_price_id_pro_monthly` → Pro tier
- `stripe_price_id_pro_annual` → Pro tier
- `stripe_price_id_team_monthly` → Team tier (if used)
- `stripe_price_id_team_annual` → Team tier (if used)

Enterprise is custom – no price ID; handled via contact sales.

---

## Free Tier Limit

The free tier limit (3 interviews/month) is enforced in:

- `app/dependencies.py` – `check_interview_quota`
- `app/api/subscriptions.py` – `get_subscription_status`

No Stripe configuration needed for free tier.
