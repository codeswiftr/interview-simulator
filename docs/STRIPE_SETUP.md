# Stripe Setup Guide for Interview Simulator

This guide covers configuring Stripe for the Interview Simulator subscription system.

## Overview

The Interview Simulator uses Stripe for:
- **Checkout Sessions** - Subscription upgrades via hosted checkout
- **Customer Portal** - Self-service subscription management
- **Webhooks** - Real-time subscription status updates

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `STRIPE_SECRET_KEY` | Stripe API secret key (starts with `sk_`) | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Webhook endpoint signing secret (starts with `whsec_`) | `whsec_...` |
| `STRIPE_PRICE_ID_PRO_MONTHLY` | Price ID for monthly Pro subscription | `price_1ABC...` |
| `STRIPE_PRICE_ID_PRO_ANNUAL` | Price ID for annual Pro subscription | `price_1XYZ...` |
| `STRIPE_TRIAL_DAYS` | Free trial period in days (optional, default: 7) | `7` |

---

## Step 1: Create Stripe Products and Prices

### In Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Products** → **Add product**

### Create Pro Monthly Product

1. Click **Add product**
2. Fill in:
   - **Name**: `Interview Simulator Pro - Monthly`
   - **Description**: `Unlimited interviews, AI feedback, advanced analytics`
3. Under **Pricing**:
   - **Model**: Recurring
   - **Price**: `$19.00` (or your chosen price)
   - **Billing period**: Monthly
4. Click **Save product**
5. Copy the **Price ID** (e.g., `price_1ABC123def456GHI`)

### Create Pro Annual Product

1. Click **Add product**
2. Fill in:
   - **Name**: `Interview Simulator Pro - Annual`
   - **Description**: `Unlimited interviews, AI feedback, advanced analytics (2 months free)`
3. Under **Pricing**:
   - **Model**: Recurring
   - **Price**: `$190.00` (or your chosen price - typically ~20% discount)
   - **Billing period**: Yearly
4. Click **Save product**
5. Copy the **Price ID** (e.g., `price_1XYZ789abc012DEF`)

---

## Step 2: Create Webhook Endpoint

### Webhook URL

**Production:**
```
https://interview-simulator-api-production.up.railway.app/api/v1/subscriptions/webhook
```

**Local development (with Stripe CLI):**
```
http://localhost:8000/api/v1/subscriptions/webhook
```

### In Stripe Dashboard

1. Navigate to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Fill in:
   - **Endpoint URL**: (use production URL above)
   - **Description**: `Interview Simulator subscription events`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Click **Add endpoint**
6. Click **Reveal** under Signing secret
7. Copy the signing secret (starts with `whsec_`)

---

## Step 3: Configure Railway Environment Variables

### Using Railway CLI

```bash
# Set Stripe secret key
railway variables --service interview-simulator-api \
  --set 'STRIPE_SECRET_KEY=sk_live_your_key_here'

# Set webhook signing secret
railway variables --service interview-simulator-api \
  --set 'STRIPE_WEBHOOK_SECRET=whsec_your_secret_here'

# Set price IDs
railway variables --service interview-simulator-api \
  --set 'STRIPE_PRICE_ID_PRO_MONTHLY=price_1ABC123def456GHI'

railway variables --service interview-simulator-api \
  --set 'STRIPE_PRICE_ID_PRO_ANNUAL=price_1XYZ789abc012DEF'

# Set trial days (optional)
railway variables --service interview-simulator-api \
  --set 'STRIPE_TRIAL_DAYS=7'

# Redeploy to apply changes
railway redeploy --service interview-simulator-api -y
```

### Using Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select the `interview-simulator-api` service
3. Click **Variables** tab
4. Add each variable listed above
5. Redeploy the service

---

## Step 4: Configure Customer Portal

The Customer Portal allows users to manage their subscription (update payment, view invoices, cancel).

### In Stripe Dashboard

1. Navigate to **Settings** → **Billing** → **Customer portal**
2. Configure settings:
   - **Payment method**: Allow customers to update
   - **Invoices**: Allow customers to view invoice history
   - **Subscriptions**: Allow customers to cancel
   - **Cancel subscriptions**: Set to "Cancel at end of billing period"
3. Under **Business information**:
   - **Terms of service URL**: `https://app.codeswiftr.com/terms`
   - **Privacy policy URL**: `https://app.codeswiftr.com/privacy`
4. Click **Save changes**

---

## Step 5: Local Development Setup

### Using Stripe CLI

1. Install Stripe CLI:
   ```bash
   brew install stripe/stripe-cli/stripe
   ```

2. Login to Stripe:
   ```bash
   stripe login
   ```

3. Forward webhooks to local server:
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook
   ```

4. Copy the webhook signing secret from the CLI output (starts with `whsec_`)

5. Add to your local `.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_test_your_test_key
   STRIPE_WEBHOOK_SECRET=whsec_from_cli_output
   STRIPE_PRICE_ID_PRO_MONTHLY=price_test_monthly_id
   STRIPE_PRICE_ID_PRO_ANNUAL=price_test_annual_id
   ```

### Test Mode vs Live Mode

- Use **test mode** keys (prefix `sk_test_`) for development
- Use **live mode** keys (prefix `sk_live_`) for production
- Create separate products/prices in test mode for development

---

## Verification

### Check Stripe Configuration

After deployment, verify the configuration:

```bash
# Check the pricing endpoint returns configured prices
curl https://interview-simulator-api-production.up.railway.app/api/v1/subscriptions/pricing
```

Expected response:
```json
{
  "pro_monthly_price_id": "price_1ABC123def456GHI",
  "pro_annual_price_id": "price_1XYZ789abc012DEF"
}
```

### Test Webhook Delivery

1. In Stripe Dashboard → Webhooks → your endpoint
2. Click **Send test webhook**
3. Select `checkout.session.completed`
4. Click **Send test webhook**
5. Check for successful delivery (200 response)

---

## Troubleshooting

### "Stripe is not configured" Error

**Cause**: `STRIPE_SECRET_KEY` not set or empty

**Fix**: Verify the environment variable is set correctly:
```bash
railway variables --service interview-simulator-api
```

### "Stripe webhook secret not configured" Error

**Cause**: `STRIPE_WEBHOOK_SECRET` not set

**Fix**: Add the webhook signing secret from Stripe Dashboard

### Webhook Returns 400 "Invalid signature"

**Cause**: Webhook secret mismatch between Stripe and Railway

**Fix**:
1. Go to Stripe Dashboard → Webhooks → your endpoint
2. Click "Reveal" on signing secret
3. Update the `STRIPE_WEBHOOK_SECRET` in Railway with the exact value

### Subscription Status Not Updating

**Cause**: Webhook events not reaching the server

**Check**:
1. Stripe Dashboard → Webhooks → your endpoint → Recent events
2. Look for failed delivery attempts
3. Verify the endpoint URL is correct

---

## Security Notes

- Never commit Stripe keys to version control
- Use test mode keys for development, live keys only in production
- Webhook secrets are different for each endpoint
- Rotate keys periodically via Stripe Dashboard → Developers → API keys

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/subscriptions/pricing` | GET | Get configured price IDs |
| `/api/v1/subscriptions/status` | GET | Get user's subscription status |
| `/api/v1/subscriptions/checkout` | POST | Create Stripe Checkout session |
| `/api/v1/subscriptions/portal` | POST | Create Customer Portal session |
| `/api/v1/subscriptions/cancel` | POST | Cancel subscription at period end |
| `/api/v1/subscriptions/webhook` | POST | Stripe webhook endpoint |
