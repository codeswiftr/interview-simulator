# Interview Simulator - Onboarding Flow Review

**Date:** February 5, 2026  
**App URL:** https://app.codeswiftr.com  
**Status:** LIVE  
**Reviewer:** Agent Fleet (Code Review)

---

## Executive Summary

| Aspect | Score | Status | Change |
|--------|-------|--------|--------|
| Sign-up Friction | 7/10 | 🟡 Good, minor improvements | - |
| First Interview Experience | 8/10 | 🟢 Strong | - |
| Conversion to Paid | 5/10 | 🔴 Needs urgent work | ⬇️ |

**Overall Assessment:** The onboarding flow has solid UX foundations but critical conversion issues remain unaddressed since the last review (Jan 30). Price inconsistencies and missing usage indicators are leaving revenue on the table.

### Changes Since Last Review (Jan 30, 2026)
- ✅ `pending_plan` now triggers upgrade modal after registration
- ⏸️ Price inconsistency still exists ($19 vs $29)
- ❌ No usage progress bar added
- ❌ No social auth added

---

## 1. Sign-up Flow Analysis

### Current Flow
```
Homepage → Register Page → Dashboard (with Welcome Modal) → First Session Prompt
```

### Friction Points

#### 1.1 ❌ Registration Form Has 5 Fields (Too Many)
**File:** `frontend/src/pages/RegisterPage.tsx`

**Current fields:**
| Field | Required | Friction Level |
|-------|----------|----------------|
| Full Name | Yes | Low |
| Email | Yes | Low |
| Password | Yes | Low |
| Confirm Password | Yes | **HIGH** |
| Experience Level | Yes | Medium |

**Issue:** Research shows each additional field reduces conversions by ~10%. "Confirm Password" is outdated UX when password visibility toggle exists.

**Data Point:** Login page already has password visibility toggle (Eye/EyeOff icons) - RegisterPage lacks this consistency.

**Recommendation:**
1. Remove "Confirm Password" - add visibility toggle instead
2. Move "Experience Level" to profile completion (post-first-interview)
3. Estimated conversion lift: **+15-20% signup completion**

**Priority:** 🔴 HIGH

---

#### 1.2 ❌ No Social Sign-in (Competitive Disadvantage)
**Files:** `RegisterPage.tsx`, `LoginPage.tsx`

| Competitor | Google Auth | GitHub Auth | LinkedIn |
|------------|-------------|-------------|----------|
| Pramp | ✅ | ❌ | ✅ |
| Interviewing.io | ❌ | ✅ | ❌ |
| Exponent | ✅ | ❌ | ✅ |
| **Interview Simulator** | ❌ | ❌ | ❌ |

**Impact:** Engineers prefer OAuth. GitHub login is particularly expected for technical interview tools.

**Priority:** 🟡 MEDIUM (Week 2-3)

---

#### 1.3 ✅ Password Strength Indicator Present
**File:** `frontend/src/components/ui/PasswordStrengthIndicator.tsx`

Real-time visual feedback helps users create valid passwords. Well implemented.

---

#### 1.4 ✅ Plan Intent Now Preserved
**File:** `frontend/src/hooks/useDashboardModals.ts:47-55`

```typescript
// Check for pending plan upgrade from registration
useEffect(() => {
  const pendingPlan = sessionStorage.getItem('pending_plan');
  if (!pendingPlan) return;
  sessionStorage.removeItem('pending_plan');
  if (pendingPlan === 'pro' && userSubscriptionTier === 'free') {
    setIsUpgradeOpen(true);
  }
}, [userSubscriptionTier]);
```

**Status:** ✅ FIXED since last review. Users from pricing page now see upgrade modal immediately.

---

## 2. First Interview Experience Analysis

### Current Flow
```
Dashboard → Welcome Modal (3 steps) → First Session Prompt → New Interview Modal → Interview Page → Recording → Feedback
```

### Strengths

#### 2.1 ✅ Multi-Step Welcome Modal
**File:** `frontend/src/components/onboarding/WelcomeModal.tsx`

Three-step progressive onboarding:
1. **"You've Got This"** - Emotional reassurance with social proof
2. **"Speak Naturally"** - Sets recording expectations
3. **"Track Your Growth"** - Shows value proposition

**Highlights:**
- Personalized greeting with user's first name
- Skip option respects user agency
- Step indicators are clickable for non-linear navigation
- Smooth CSS animations (`onboarding-step-enter`)

---

#### 2.2 ✅ First Session Prompt
**File:** `frontend/src/components/onboarding/FirstSessionPrompt.tsx`

Secondary modal if user closes welcome without starting. Includes helpful tip about STAR method.

---

#### 2.3 ✅ Empty State Dashboard
**File:** `frontend/src/pages/DashboardPage.tsx:270-320`

Clear visual guide for new users:
- Choose Topic (Target icon)
- Record Answer (Mic icon) 
- Get Feedback (BarChart2 icon)

Large, prominent "Start Your First Interview" CTA.

---

### Friction Points

#### 2.4 ⚠️ Decision Overload in Interview Setup
**File:** `frontend/src/components/interview/NewInterviewModal.tsx`

**Current options:**
| Category | Options | 
|----------|---------|
| Interview Type | 4 (behavioral, technical, system_design, mixed) |
| Target Company | 11 (including "Any") |
| Difficulty | 4 (easy, medium, hard, mixed) |
| Question Count | 5 (1, 2, 3, 5, 10) |

**Total combinations:** 4 × 11 × 4 × 5 = **880 possible configurations**

**Impact:** Analysis paralysis for first-time users who just want to try the product.

**Recommendation:**
```typescript
// In NewInterviewModal.tsx
const [isFirstSession] = useState(() => {
  const onboarding = localStorage.getItem('interview_simulator_onboarding');
  return !onboarding || !JSON.parse(onboarding).firstSessionCreated;
});

// Show simplified "Quick Start" for first-timers
{isFirstSession && (
  <div className="quick-start-panel">
    <h3>Quick Start (Recommended)</h3>
    <button onClick={() => submitWithDefaults()}>
      Start Behavioral Interview (2 questions)
    </button>
  </div>
)}
```

**Priority:** 🟡 MEDIUM

---

#### 2.5 ⚠️ No Demo/Preview Mode
**Issue:** Users must commit to starting an interview (consuming 1 of 5 free sessions) without seeing what the experience looks like.

**Recommendation:** Add "Watch Demo" button that plays a pre-recorded 30-second video or animated walkthrough.

**Priority:** 🟢 LOW

---

## 3. Conversion to Paid Analysis

### Current Upgrade Triggers

| Trigger | Location | Status |
|---------|----------|--------|
| Free limit reached (5/month) | `DashboardPage.tsx:164` | ✅ Works |
| Pending plan from registration | `useDashboardModals.ts:47` | ✅ Fixed |
| Pricing page CTA | `PricingPage.tsx` | 🟡 Works |
| Homepage pricing preview | `HomePage.tsx:145` | 🟡 Works |
| Upgrade modal | `UpgradeModal.tsx` | 🟡 Has friction |

### Critical Issues

#### 3.1 🔴 CRITICAL: Price Inconsistency ($19 vs $29)
**Status:** Still broken since last review

| Location | Price Displayed |
|----------|-----------------|
| `PricingPage.tsx:15` | `MONTHLY_PRICE = 19` → **$19/month** |
| `PricingPage.tsx:99` | Shows $19 as founding member price |
| `HomePage.tsx:157` | **$29/month** (hardcoded) |
| `UpgradeModal.tsx:131` | **$29/month** (hardcoded) |

**User Journey Problem:**
1. User sees $19 on pricing page → excited
2. User clicks upgrade, sees $29 modal → confused
3. User abandons checkout → lost sale

**Immediate Fix Required:**
```typescript
// Create shared constants file: src/lib/pricing.ts
export const PRICING = {
  PRO_MONTHLY: 19,
  PRO_ANNUAL_MONTHLY_EQUIVALENT: 24,
  PRO_ANNUAL_TOTAL: 290,
};

// Update all hardcoded prices to use PRICING constants
```

**Priority:** 🔴 CRITICAL - Fix immediately

---

#### 3.2 ❌ No Usage Limit Indicator
**File:** `frontend/src/components/dashboard/StatsOverview.tsx`

**Current state:** User has no visibility into "3 of 5 free interviews used" until they hit the limit.

**Missing UI:**
```
┌─────────────────────────────────────────┐
│  Free Plan: 3/5 interviews used         │
│  ████████░░░░░░  |  Upgrade for unlimited → │
└─────────────────────────────────────────┘
```

**Backend support exists:** The API returns session counts via `userStats.total_sessions`.

**Implementation:**
```typescript
// In StatsOverview.tsx or as a new UsageBanner component
const FREE_TIER_LIMIT = 5;

{user?.subscription_tier === 'free' && (
  <Card className="bg-gradient-to-r from-amber-500/10 to-orange-500/10">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">
          Free Plan: {totalSessions}/{FREE_TIER_LIMIT} interviews used
        </span>
        <div className="w-32 h-2 bg-surface-tertiary rounded-full">
          <div 
            className="h-full bg-electric-blue rounded-full"
            style={{ width: `${(totalSessions / FREE_TIER_LIMIT) * 100}%` }}
          />
        </div>
      </div>
      <Link to="/pricing" className="text-electric-blue text-sm hover:underline">
        Upgrade for unlimited →
      </Link>
    </div>
  </Card>
)}
```

**Priority:** 🔴 HIGH - Creates urgency without frustration

---

#### 3.3 ⚠️ Upgrade Modal Pre-Checkout Friction
**File:** `frontend/src/components/subscription/UpgradeModal.tsx:157-190`

Modal asks "What made you click upgrade?" with dropdown + text field **before** showing checkout button.

**Issue:** This adds cognitive load at the critical conversion moment.

**Recommendation:** 
1. Move feedback collection to post-checkout success page
2. Or make it collapsible/optional (currently required)

**Priority:** 🟡 MEDIUM

---

#### 3.4 ⚠️ Trial Messaging Inconsistent
| Location | Trial Mentioned |
|----------|-----------------|
| Homepage Pro card | "7-DAY FREE TRIAL" badge |
| Pricing page | "7-day free trial" badge |
| Upgrade modal | ❌ No mention |

**Recommendation:** Add trial badge to UpgradeModal header.

**Priority:** 🟡 MEDIUM

---

#### 3.5 ⚠️ No High-Score Conversion Prompt
**File:** `frontend/src/pages/FeedbackPage.tsx`

**Opportunity:** When user scores 85+ on an interview, they're in a positive emotional state - perfect for upgrade suggestion.

**Missing:**
```typescript
// In FeedbackPage, after showing score
{overallScore >= 85 && user?.subscription_tier === 'free' && (
  <Card className="bg-gradient-to-r from-electric-blue/10 to-indigo-500/10 p-4 mt-4">
    <div className="flex items-center gap-3">
      <Trophy className="w-6 h-6 text-amber-500" />
      <div>
        <p className="font-semibold">Great job! You scored {overallScore}%</p>
        <p className="text-sm text-text-secondary">
          You're interview-ready! Practice more with unlimited sessions.
        </p>
      </div>
      <Button onClick={() => setShowUpgradeModal(true)}>
        Upgrade to Pro
      </Button>
    </div>
  </Card>
)}
```

**Priority:** 🟡 MEDIUM

---

## 4. Analytics Gaps

### Missing Events
| Event | Description | Where to Add |
|-------|-------------|--------------|
| `REGISTRATION_STARTED` | User lands on /register | `RegisterPage.tsx` onMount |
| `REGISTRATION_FORM_INTERACTION` | User starts typing | First field focus |
| `ONBOARDING_STEP_VIEWED` | Each welcome modal step | `WelcomeModal.tsx` |
| `ONBOARDING_COMPLETED` | User finishes tour | After step 3 or skip |
| `INTERVIEW_SETUP_STARTED` | Opens new interview modal | `NewInterviewModal.tsx` |
| `USAGE_LIMIT_SHOWN` | When limit banner displays | New component |

### Current Funnel Tracking (Incomplete)
```
? Homepage visits
? → Register page views (no REGISTRATION_STARTED event)
✅ → Registration complete (USER_REGISTERED)
? → Onboarding completion  
? → First interview started
✅ → Interview completed (INTERVIEW_COMPLETED)
✅ → Upgrade initiated (UPGRADE_CTA_CLICKED)
✅ → Checkout started (CHECKOUT_STARTED)
? → Subscription created (should come from webhook)
```

**Recommendation:** Add missing events to enable proper funnel analysis.

**Priority:** 🟡 MEDIUM (for optimization)

---

## 5. Action Items

### Immediate (This Week) - Revenue Critical

| # | Issue | File(s) | Est. Impact |
|---|-------|---------|-------------|
| 1 | **Fix price inconsistency** | `HomePage.tsx`, `UpgradeModal.tsx` | Trust, conversion |
| 2 | **Add usage limit indicator** | New `UsageBanner.tsx`, `DashboardPage.tsx` | Urgency → conversion |
| 3 | **Remove Confirm Password field** | `RegisterPage.tsx` | +15% signups |

### Short-term (Week 2-3)

| # | Issue | File(s) | Est. Impact |
|---|-------|---------|-------------|
| 4 | Add trial badge to UpgradeModal | `UpgradeModal.tsx` | Clarity |
| 5 | Move upgrade feedback to post-checkout | `UpgradeModal.tsx` | +5% checkout completion |
| 6 | Add Google OAuth | `RegisterPage.tsx`, `LoginPage.tsx`, backend | +10-15% signups |
| 7 | Add Quick Start for first-time users | `NewInterviewModal.tsx` | -30% time-to-first-interview |

### Medium-term (Month 1)

| # | Issue | File(s) | Est. Impact |
|---|-------|---------|-------------|
| 8 | High-score upgrade prompt | `FeedbackPage.tsx` | Emotional conversion |
| 9 | Demo/preview mode | New component | Reduces signup anxiety |
| 10 | Move experience level to profile | `RegisterPage.tsx`, `SettingsPage.tsx` | Further reduce friction |
| 11 | Add missing analytics events | Multiple | Data for optimization |

---

## 6. Competitive Position

| Feature | Interview Simulator | Pramp | Interviewing.io |
|---------|---------------------|-------|-----------------|
| Free Tier | 5/month | Unlimited peer | Waitlist |
| Social Auth | ❌ | Google, LinkedIn | GitHub |
| Signup Fields | 5 | 4 | 3 |
| Price | $19/mo | $50/mo | $100+/interview |
| AI Feedback | ✅ Real-time | ❌ Peer only | ❌ Human only |

**Our advantages:** AI feedback, lower price, no waitlist
**Our gaps:** Social auth, signup friction

---

## 7. Recommended Metrics Dashboard

### Key Conversion Metrics to Track

```
1. Registration Funnel
   - Register page views → Form started → Completed
   
2. Activation Funnel  
   - Signup → Welcome complete → First interview started → First interview completed
   
3. Conversion Funnel
   - Active free users → Upgrade modal views → Checkout started → Subscription created
   
4. Usage Metrics
   - Avg interviews per free user/month
   - % hitting 5-interview limit
   - Time to first interview (from signup)
```

---

## Appendix: File Reference

| Component | Path | Purpose |
|-----------|------|---------|
| Registration | `frontend/src/pages/RegisterPage.tsx` | Sign-up form |
| Login | `frontend/src/pages/LoginPage.tsx` | Login form |
| Dashboard | `frontend/src/pages/DashboardPage.tsx` | Main hub |
| Homepage | `frontend/src/pages/HomePage.tsx` | Marketing landing |
| Pricing | `frontend/src/pages/PricingPage.tsx` | Pricing page |
| Interview | `frontend/src/pages/InterviewPage.tsx` | Recording flow |
| Feedback | `frontend/src/pages/FeedbackPage.tsx` | Results display |
| New Interview Modal | `frontend/src/components/interview/NewInterviewModal.tsx` | Session config |
| Upgrade Modal | `frontend/src/components/subscription/UpgradeModal.tsx` | Upsell |
| Welcome Modal | `frontend/src/components/onboarding/WelcomeModal.tsx` | New user tour |
| First Session Prompt | `frontend/src/components/onboarding/FirstSessionPrompt.tsx` | Secondary CTA |
| Stats Overview | `frontend/src/components/dashboard/StatsOverview.tsx` | Dashboard stats |
| Auth Hook | `frontend/src/hooks/useAuth.tsx` | Auth state |
| Onboarding Hook | `frontend/src/hooks/useOnboarding.ts` | Onboarding state |
| Dashboard Modals Hook | `frontend/src/hooks/useDashboardModals.ts` | Modal orchestration |
| Analytics | `frontend/src/lib/analytics.ts` | Event tracking |

---

*Report generated from code analysis. Revenue-critical items (#1, #2) should be addressed before any marketing spend increase.*
