# Affiliate Program Implementation Plan

## Interview Simulator - Affiliate & Referral System

**Date**: 2024-12-21
**Status**: Planning
**Priority**: Revenue expansion feature

---

## Executive Summary

Implement a comprehensive affiliate program for Interview Simulator to leverage partner-driven growth. The program will offer recurring commissions to affiliates who refer new paying subscribers, with automated tracking via Stripe integration and a self-service affiliate dashboard.

**Key Benefits**:
- Lower customer acquisition cost vs. paid advertising
- Recurring passive income attracts high-quality affiliates
- Network of educators and advocates promoting the product
- Scalable growth channel with performance-based costs

---

## Research Findings Summary

### Industry Benchmarks (SaaS 2025)

| Metric | Industry Standard | Recommended for Interview Simulator |
|--------|-------------------|-------------------------------------|
| Commission Rate | 20-30% | 25% recurring (12 months) |
| Cookie Duration | 30-90 days | 60 days |
| Payout Threshold | $50-100 | $50 minimum |
| Payment Frequency | Monthly | Monthly (NET 30) |

### Tracking Platform Comparison

| Platform | Price | Best For | Stripe Integration |
|----------|-------|----------|-------------------|
| [Rewardful](https://www.rewardful.com/) | $49/mo | Startups, simple setup | Native |
| [FirstPromoter](https://firstpromoter.com/) | $49-99/mo | SaaS, email automation | Native |
| [PartnerStack](https://partnerstack.com/) | $500+/mo | Enterprise, marketplaces | Native |
| Custom Build | Dev time | Full control | Direct API |

**Recommendation**: Start with **Rewardful** for MVP, migrate to FirstPromoter as program scales.

---

## Program Structure

### Commission Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Commission Structure                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Tier 1: Standard Affiliate                                 │
│  ├── 25% recurring commission                               │
│  ├── 12-month payout window                                 │
│  └── All subscription tiers eligible                        │
│                                                              │
│  Tier 2: Premium Partner (10+ conversions/month)            │
│  ├── 30% recurring commission                               │
│  ├── Lifetime payout window                                 │
│  └── Early access to new features                           │
│                                                              │
│  Tier 3: Strategic Partner (custom)                         │
│  ├── 35-50% negotiated                                      │
│  ├── Co-marketing opportunities                             │
│  └── Dedicated account manager                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Revenue Examples

| Plan | Monthly Price | Affiliate Earns (25%) | Annual Earnings |
|------|--------------|----------------------|-----------------|
| Pro | $29/mo | $7.25/mo | $87/year |
| Premium | $79/mo | $19.75/mo | $237/year |
| Team | $199/mo | $49.75/mo | $597/year |

### Cookie & Attribution

- **Cookie Duration**: 60 days (industry standard)
- **Attribution Model**: Last-click with first-touch override for existing affiliates
- **Coupon Tracking**: Unique discount codes as backup attribution
- **Cross-Device**: Server-side tracking via email/account linking

---

## Technical Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Affiliate System Architecture                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Frontend (React)                    Backend (FastAPI)              │
│  ┌──────────────────┐               ┌──────────────────────┐        │
│  │ Affiliate Portal │               │ /api/v1/affiliates   │        │
│  │ - Dashboard      │◄─────────────▶│ - Registration       │        │
│  │ - Referral Links │               │ - Link Generation    │        │
│  │ - Earnings       │               │ - Stats & Reporting  │        │
│  │ - Payouts        │               │ - Payout Requests    │        │
│  └──────────────────┘               └──────────┬───────────┘        │
│                                                │                     │
│  Public Site                                   │                     │
│  ┌──────────────────┐               ┌──────────▼───────────┐        │
│  │ Landing Pages    │               │ Attribution Service  │        │
│  │ - ?ref=CODE      │──────────────▶│ - Cookie Setting     │        │
│  │ - Coupon Entry   │               │ - Click Tracking     │        │
│  └──────────────────┘               │ - Conversion Match   │        │
│                                     └──────────┬───────────┘        │
│                                                │                     │
│                                     ┌──────────▼───────────┐        │
│                                     │ Stripe Integration   │        │
│                                     │ - Webhook Listener   │        │
│                                     │ - Commission Calc    │        │
│                                     │ - Payout Processing  │        │
│                                     └──────────────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Database Schema

```python
# backend/app/models/affiliate.py

class Affiliate(SQLModel, table=True):
    """Affiliate partner account"""
    __tablename__ = "affiliates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True)

    # Affiliate info
    referral_code: str = Field(unique=True, max_length=20)  # e.g., "JOHN25"
    referral_link: str  # Full URL with tracking
    coupon_code: Optional[str] = Field(unique=True)  # Discount code

    # Status
    status: str = Field(default="pending")  # pending, approved, suspended
    tier: str = Field(default="standard")  # standard, premium, strategic

    # Commission settings
    commission_rate: float = Field(default=0.25)  # 25%
    payout_window_months: int = Field(default=12)

    # Payout details
    payout_method: str = Field(default="paypal")  # paypal, stripe, bank
    payout_email: Optional[str] = None
    stripe_connect_id: Optional[str] = None

    # Stats (denormalized for performance)
    total_clicks: int = Field(default=0)
    total_signups: int = Field(default=0)
    total_conversions: int = Field(default=0)
    total_revenue: float = Field(default=0.0)
    total_earned: float = Field(default=0.0)
    total_paid: float = Field(default=0.0)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    last_payout_at: Optional[datetime] = None


class AffiliateClick(SQLModel, table=True):
    """Track affiliate link clicks"""
    __tablename__ = "affiliate_clicks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    affiliate_id: UUID = Field(foreign_key="affiliates.id")

    # Tracking
    ip_hash: str  # Hashed for privacy
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    landing_page: str

    # Attribution
    session_id: str  # For matching to conversion

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AffiliateConversion(SQLModel, table=True):
    """Track successful conversions"""
    __tablename__ = "affiliate_conversions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    affiliate_id: UUID = Field(foreign_key="affiliates.id")
    referred_user_id: UUID = Field(foreign_key="users.id")

    # Conversion details
    subscription_id: Optional[str] = None  # Stripe subscription ID
    plan_type: str  # pro, premium, team

    # Commission
    revenue_amount: float
    commission_rate: float
    commission_amount: float
    currency: str = Field(default="USD")

    # Status
    status: str = Field(default="pending")  # pending, approved, paid, refunded

    # Timing
    converted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # For recurring commissions
    billing_period: int = Field(default=1)  # Which billing cycle
    is_recurring: bool = Field(default=True)


class AffiliatePayout(SQLModel, table=True):
    """Payout records"""
    __tablename__ = "affiliate_payouts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    affiliate_id: UUID = Field(foreign_key="affiliates.id")

    # Payout details
    amount: float
    currency: str = Field(default="USD")
    method: str  # paypal, stripe, bank

    # Status
    status: str = Field(default="pending")  # pending, processing, completed, failed

    # External reference
    transaction_id: Optional[str] = None
    payout_batch_id: Optional[str] = None

    # Timing
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None
    failure_reason: Optional[str] = None
```

### API Endpoints

```python
# backend/app/api/affiliates.py

# === Public Endpoints ===

POST /api/v1/affiliates/apply
# Apply to become an affiliate
# Body: { motivation: str, website?: str, audience_size?: int }
# Returns: { affiliate_id, status: "pending" }

GET /api/v1/affiliates/track
# Track click (called via redirect)
# Query: ?ref=CODE&landing=/pricing
# Sets cookie, records click, redirects to landing

# === Affiliate Portal (auth required) ===

GET /api/v1/affiliates/me
# Get affiliate dashboard data
# Returns: { profile, stats, recent_conversions, pending_payout }

GET /api/v1/affiliates/me/stats
# Detailed statistics
# Query: ?period=30d|90d|12m|all
# Returns: { clicks, signups, conversions, revenue, earnings, charts }

GET /api/v1/affiliates/me/conversions
# List all conversions
# Query: ?status=pending|approved|paid&page=1&limit=20
# Returns: { conversions[], pagination }

GET /api/v1/affiliates/me/links
# Get referral links and assets
# Returns: { referral_link, coupon_code, banners[], email_templates[] }

POST /api/v1/affiliates/me/payout/request
# Request payout
# Body: { amount?: float }  # If not specified, request all available
# Returns: { payout_id, amount, estimated_date }

PUT /api/v1/affiliates/me/settings
# Update payout settings
# Body: { payout_method, payout_email?, stripe_connect_id? }

# === Admin Endpoints ===

GET /api/v1/admin/affiliates
# List all affiliates
# Query: ?status=pending|approved&tier=standard|premium

PUT /api/v1/admin/affiliates/{id}/approve
# Approve affiliate application

PUT /api/v1/admin/affiliates/{id}/suspend
# Suspend affiliate (fraud, violation)

POST /api/v1/admin/affiliates/payouts/process
# Process pending payouts batch

# === Webhook Endpoints ===

POST /api/v1/webhooks/stripe/affiliate
# Handle Stripe events for affiliate tracking
# Events: invoice.paid, customer.subscription.deleted, charge.refunded
```

### Stripe Integration

```python
# backend/app/services/affiliate_service.py

class AffiliateService:
    """Handle affiliate tracking and commissions"""

    async def track_click(
        self,
        referral_code: str,
        request: Request,
        landing_page: str
    ) -> str:
        """Record click and return session ID for attribution"""
        affiliate = await self.get_affiliate_by_code(referral_code)
        if not affiliate or affiliate.status != "approved":
            return None

        session_id = secrets.token_urlsafe(16)

        click = AffiliateClick(
            affiliate_id=affiliate.id,
            ip_hash=self._hash_ip(request.client.host),
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            landing_page=landing_page,
            session_id=session_id
        )

        await self.db.add(click)

        # Update denormalized stats
        affiliate.total_clicks += 1
        await self.db.commit()

        return session_id

    async def attribute_conversion(
        self,
        user_id: UUID,
        stripe_subscription_id: str,
        plan_type: str,
        amount: float
    ) -> Optional[AffiliateConversion]:
        """
        Attribute a conversion to an affiliate.
        Called from Stripe webhook on invoice.paid
        """
        # Check for attribution cookie/session
        attribution = await self._find_attribution(user_id)
        if not attribution:
            return None

        affiliate = await self.get_affiliate(attribution.affiliate_id)
        commission = amount * affiliate.commission_rate

        conversion = AffiliateConversion(
            affiliate_id=affiliate.id,
            referred_user_id=user_id,
            subscription_id=stripe_subscription_id,
            plan_type=plan_type,
            revenue_amount=amount,
            commission_rate=affiliate.commission_rate,
            commission_amount=commission,
            billing_period=1,
            status="approved"  # Auto-approve first conversion
        )

        await self.db.add(conversion)

        # Update affiliate stats
        affiliate.total_conversions += 1
        affiliate.total_revenue += amount
        affiliate.total_earned += commission

        await self.db.commit()

        # Send notification
        await self._notify_affiliate_conversion(affiliate, conversion)

        return conversion

    async def process_recurring_commission(
        self,
        stripe_subscription_id: str,
        amount: float,
        billing_period: int
    ):
        """
        Process recurring commission on subscription renewal.
        Called from Stripe webhook on invoice.paid (renewal)
        """
        # Find original conversion
        original = await self.get_conversion_by_subscription(
            stripe_subscription_id
        )
        if not original:
            return

        affiliate = await self.get_affiliate(original.affiliate_id)

        # Check if still within payout window
        months_since = self._months_between(
            original.converted_at,
            datetime.now(timezone.utc)
        )

        if months_since > affiliate.payout_window_months:
            return  # Past payout window

        commission = amount * affiliate.commission_rate

        conversion = AffiliateConversion(
            affiliate_id=affiliate.id,
            referred_user_id=original.referred_user_id,
            subscription_id=stripe_subscription_id,
            plan_type=original.plan_type,
            revenue_amount=amount,
            commission_rate=affiliate.commission_rate,
            commission_amount=commission,
            billing_period=billing_period,
            is_recurring=True,
            status="approved"
        )

        await self.db.add(conversion)
        affiliate.total_revenue += amount
        affiliate.total_earned += commission
        await self.db.commit()

    async def handle_refund(
        self,
        stripe_subscription_id: str,
        refund_amount: float
    ):
        """Reverse commission on refund"""
        conversions = await self.get_conversions_by_subscription(
            stripe_subscription_id,
            status="approved"
        )

        for conversion in conversions:
            if conversion.status == "paid":
                # Already paid - need to deduct from next payout
                await self._create_commission_adjustment(
                    conversion.affiliate_id,
                    -conversion.commission_amount,
                    reason=f"Refund for subscription {stripe_subscription_id}"
                )
            else:
                # Not yet paid - just mark as refunded
                conversion.status = "refunded"

        await self.db.commit()
```

---

## Frontend Implementation

### Affiliate Portal Pages

```
frontend/src/pages/affiliate/
├── AffiliateApplyPage.tsx      # Application form
├── AffiliateDashboardPage.tsx  # Main dashboard
├── AffiliateLinksPage.tsx      # Referral links & assets
├── AffiliateEarningsPage.tsx   # Earnings & conversions
├── AffiliatePayoutsPage.tsx    # Payout history & requests
└── AffiliateSettingsPage.tsx   # Payout settings
```

### Dashboard Components

```tsx
// frontend/src/components/affiliate/AffiliateDashboard.tsx

interface AffiliateStats {
  clicks: number;
  signups: number;
  conversions: number;
  conversionRate: number;
  revenue: number;
  earnings: number;
  pendingPayout: number;
}

export function AffiliateDashboard() {
  const { data: stats } = useAffiliateStats();
  const { data: recentConversions } = useRecentConversions();

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Clicks"
          value={stats.clicks}
          change={stats.clicksChange}
        />
        <StatCard
          title="Conversions"
          value={stats.conversions}
          subtitle={`${stats.conversionRate}% rate`}
        />
        <StatCard
          title="Total Earnings"
          value={formatCurrency(stats.earnings)}
          change={stats.earningsChange}
        />
        <StatCard
          title="Pending Payout"
          value={formatCurrency(stats.pendingPayout)}
          action={<RequestPayoutButton />}
        />
      </div>

      {/* Referral Link */}
      <Card>
        <CardHeader>
          <CardTitle>Your Referral Link</CardTitle>
        </CardHeader>
        <CardContent>
          <CopyableLink link={stats.referralLink} />
          <div className="mt-4 flex gap-2">
            <ShareButton platform="twitter" />
            <ShareButton platform="linkedin" />
            <ShareButton platform="email" />
          </div>
        </CardContent>
      </Card>

      {/* Earnings Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Earnings Over Time</CardTitle>
          <PeriodSelector />
        </CardHeader>
        <CardContent>
          <EarningsChart data={stats.chartData} />
        </CardContent>
      </Card>

      {/* Recent Conversions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Conversions</CardTitle>
        </CardHeader>
        <CardContent>
          <ConversionsTable conversions={recentConversions} />
        </CardContent>
      </Card>
    </div>
  );
}
```

### Referral Link Tracking

```tsx
// frontend/src/hooks/useAffiliateTracking.ts

export function useAffiliateTracking() {
  useEffect(() => {
    // Check for referral code in URL
    const params = new URLSearchParams(window.location.search);
    const refCode = params.get('ref');

    if (refCode) {
      // Store in cookie (60 days)
      setCookie('affiliate_ref', refCode, 60);

      // Track click via API
      fetch(`/api/v1/affiliates/track?ref=${refCode}&landing=${window.location.pathname}`);

      // Clean URL
      params.delete('ref');
      const newUrl = params.toString()
        ? `${window.location.pathname}?${params}`
        : window.location.pathname;
      window.history.replaceState({}, '', newUrl);
    }
  }, []);
}

// Use in App.tsx or layout
function App() {
  useAffiliateTracking();
  // ...
}
```

---

## Payout System

### Payout Methods

| Method | Fees | Min Payout | Processing Time |
|--------|------|------------|-----------------|
| PayPal | 2% + $0.30 | $50 | 1-3 days |
| Stripe Connect | 0.25% + $0.25 | $50 | 2-7 days |
| Bank Transfer (Wise) | $1-5 flat | $100 | 1-4 days |

### Payout Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Payout Process                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Affiliate requests payout (or auto-monthly)             │
│     └── Minimum $50 balance required                        │
│                                                              │
│  2. System validates                                        │
│     ├── Check balance ≥ minimum                             │
│     ├── Verify no pending fraud review                      │
│     └── Confirm payout details on file                      │
│                                                              │
│  3. Admin review (optional for amounts > $500)              │
│     └── Approve or request verification                     │
│                                                              │
│  4. Process payout                                          │
│     ├── PayPal: PayPal Payouts API                          │
│     ├── Stripe: Stripe Connect Transfer                     │
│     └── Bank: Wise Business API                             │
│                                                              │
│  5. Update records                                          │
│     ├── Mark conversions as "paid"                          │
│     ├── Update affiliate.total_paid                         │
│     └── Send confirmation email                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### PayPal Payouts Integration

```python
# backend/app/services/payout_service.py

import paypalrestsdk

class PayoutService:
    def __init__(self):
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,  # sandbox or live
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET
        })

    async def process_paypal_payout(
        self,
        payout: AffiliatePayout,
        affiliate: Affiliate
    ) -> bool:
        """Process payout via PayPal"""

        sender_batch_id = f"affiliate_{payout.id}_{int(time.time())}"

        payout_request = paypalrestsdk.Payout({
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "Interview Simulator Affiliate Payout",
                "email_message": f"You have received a payout of ${payout.amount}"
            },
            "items": [{
                "recipient_type": "EMAIL",
                "amount": {
                    "value": str(payout.amount),
                    "currency": "USD"
                },
                "receiver": affiliate.payout_email,
                "note": f"Affiliate commission payout - {payout.id}",
                "sender_item_id": str(payout.id)
            }]
        })

        if payout_request.create():
            payout.status = "processing"
            payout.payout_batch_id = payout_request.batch_header.payout_batch_id
            await self.db.commit()
            return True
        else:
            payout.status = "failed"
            payout.failure_reason = payout_request.error.message
            await self.db.commit()
            return False
```

---

## Fraud Prevention

### Detection Rules

```python
# backend/app/services/fraud_detection.py

class FraudDetectionService:
    """Detect and prevent affiliate fraud"""

    FRAUD_RULES = [
        # Self-referral
        {
            "name": "self_referral",
            "check": lambda conv: conv.referred_user_id == conv.affiliate.user_id,
            "action": "reject",
            "severity": "high"
        },
        # Same IP as affiliate
        {
            "name": "same_ip",
            "check": lambda conv: self._check_same_ip(conv),
            "action": "flag",
            "severity": "medium"
        },
        # Rapid conversions (> 5 in 1 hour)
        {
            "name": "velocity",
            "check": lambda conv: self._check_velocity(conv.affiliate_id, 5, hours=1),
            "action": "flag",
            "severity": "medium"
        },
        # High refund rate (> 30%)
        {
            "name": "refund_rate",
            "check": lambda conv: self._check_refund_rate(conv.affiliate_id) > 0.3,
            "action": "suspend",
            "severity": "high"
        },
        # Conversion from blocked country
        {
            "name": "geo_block",
            "check": lambda conv: self._check_geo_block(conv),
            "action": "reject",
            "severity": "low"
        }
    ]

    async def evaluate_conversion(
        self,
        conversion: AffiliateConversion
    ) -> tuple[bool, list[str]]:
        """
        Evaluate conversion for fraud.
        Returns (is_approved, [triggered_rules])
        """
        triggered = []
        should_approve = True

        for rule in self.FRAUD_RULES:
            if rule["check"](conversion):
                triggered.append(rule["name"])

                if rule["action"] == "reject":
                    should_approve = False
                elif rule["action"] == "flag":
                    conversion.status = "pending_review"
                elif rule["action"] == "suspend":
                    await self._suspend_affiliate(
                        conversion.affiliate_id,
                        reason=f"Triggered {rule['name']}"
                    )
                    should_approve = False

        return should_approve, triggered
```

### Terms & Conditions Requirements

Required clauses for affiliate agreement:

1. **Prohibited Activities**
   - No self-referrals
   - No cookie stuffing or forced clicks
   - No trademark bidding in paid ads
   - No false claims about the product
   - No spam or unsolicited communications

2. **Disclosure Requirements**
   - FTC-compliant disclosure on all promotional content
   - Clear identification as affiliate/partner
   - Honest representation of product capabilities

3. **Commission Rules**
   - Commissions only for valid, non-refunded subscriptions
   - Right to withhold payment for suspected fraud
   - 30-day hold period for chargebacks/refunds

4. **Termination**
   - Either party can terminate with 30 days notice
   - Immediate termination for fraud/violations
   - Earned commissions paid out on termination

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

| Task | Description | Effort |
|------|-------------|--------|
| Database models | Create Affiliate, Click, Conversion, Payout models | 4h |
| Alembic migration | Generate and apply migration | 1h |
| Basic API endpoints | CRUD for affiliates, tracking endpoint | 8h |
| Stripe webhook integration | Handle invoice.paid for attribution | 4h |
| Click tracking | Cookie setting, click recording | 4h |

**Deliverable**: Basic tracking working, conversions attributed

### Phase 2: Affiliate Portal (Week 3-4)

| Task | Description | Effort |
|------|-------------|--------|
| Apply form | Application page for new affiliates | 4h |
| Dashboard page | Stats overview, earnings chart | 8h |
| Links page | Referral links, coupon codes, assets | 4h |
| Conversions page | List with filters and export | 4h |
| Settings page | Payout method configuration | 4h |

**Deliverable**: Self-service affiliate portal

### Phase 3: Payouts (Week 5)

| Task | Description | Effort |
|------|-------------|--------|
| PayPal integration | Payouts API setup | 6h |
| Stripe Connect | Alternative payout method | 6h |
| Payout request flow | UI and API for requesting payouts | 4h |
| Admin payout management | Approve/process payouts | 4h |

**Deliverable**: Automated payout system

### Phase 4: Admin & Fraud (Week 6)

| Task | Description | Effort |
|------|-------------|--------|
| Admin dashboard | Affiliate management UI | 6h |
| Fraud detection | Implement detection rules | 6h |
| Reporting | Export, analytics, insights | 4h |
| Email notifications | Conversion, payout, status emails | 4h |

**Deliverable**: Full admin controls, fraud prevention

### Phase 5: Polish & Launch (Week 7)

| Task | Description | Effort |
|------|-------------|--------|
| Affiliate marketing page | Public-facing program info | 4h |
| Documentation | Terms, FAQ, getting started guide | 4h |
| Testing | E2E tests for full flow | 6h |
| Soft launch | Invite initial affiliates | 2h |

---

## Success Metrics

### KPIs to Track

| Metric | Target (Month 1) | Target (Month 6) |
|--------|-----------------|------------------|
| Affiliates Enrolled | 20 | 100 |
| Active Affiliates (≥1 click/mo) | 10 | 50 |
| Affiliate-Driven Signups | 50 | 500 |
| Affiliate Conversion Rate | 5% | 8% |
| Revenue from Affiliates | $500 | $5,000 |
| Avg Commission per Affiliate | $25 | $50 |

### Monitoring Dashboard

Track in real-time:
- New affiliate applications
- Click volume by affiliate
- Conversion attribution rate
- Fraud detection triggers
- Pending payouts
- Affiliate satisfaction (NPS)

---

## Alternative: Third-Party Platform

If build vs. buy analysis favors buying:

### Rewardful Setup (Fastest)

```bash
# 1. Sign up at rewardful.com
# 2. Connect Stripe account
# 3. Add tracking script

# In frontend/index.html
<script>(function(w,r){w._rwq=r;w[r]=w[r]||function(){(w[r].q=w[r].q||[]).push(arguments)}})(window,'rewardful');</script>
<script async src='https://r.wdfl.co/rw.js' data-rewardful='YOUR_API_KEY'></script>

# 4. Pass referral to Stripe checkout
const { data: checkout } = await stripe.checkout.sessions.create({
  // ... other params
  client_reference_id: window.Rewardful?.referral || undefined,
});
```

**Pros**: 1-hour setup, full-featured, $49/mo
**Cons**: Revenue caps, less customization, external dependency

---

## Sources

- [Impact.com - Ultimate Guide to SaaS Affiliate Marketing](https://impact.com/partnerships/ultimate-guide-to-saas-affiliate-marketing/)
- [Rewardful - Affiliate Commission Guide](https://www.rewardful.com/articles/affiliate-commission-explained)
- [Tapfiliate - SaaS Affiliate Commissions Guide](https://tapfiliate.com/blog/a-complete-guide-for-saas-affiliate-commissions/)
- [FirstPromoter vs Rewardful vs PartnerStack Comparison](https://new.firstpromoter.com/blog/comparing-top-affiliate-tracking-solutions-firstpromoter-vs-rewardful-vs-partnerstack-vs-leaddyno)
- [Rewardful - Fraud Detection Guide](https://www.rewardful.com/guides/how-to-detect-and-prevent-affiliate-fraud)
- [Rewardful - Terms and Conditions](https://www.rewardful.com/articles/affiliate-terms-and-conditions)
- [FTC Affiliate Compliance](https://www.postaffiliatepro.com/faq/affiliate-program-legal-compliance/)
- [Baymard - Self-Service UX Best Practices 2025](https://baymard.com/blog/current-state-accounts-selfservice)
- [ReferralCandy - Affiliate Dashboard Examples](https://www.referralcandy.com/blog/affiliate-dashboard-examples)
