# Interview Simulator - User Onboarding Flow Review

**Date:** January 30, 2026  
**App URL:** https://app.codeswiftr.com  
**Status:** LIVE  
**Reviewer:** Agent (Code Review)

---

## Executive Summary

| Aspect | Score | Status |
|--------|-------|--------|
| Sign-up Friction | 7/10 | 🟡 Good, minor improvements |
| First Interview Experience | 8/10 | 🟢 Strong |
| Conversion to Paid | 6/10 | 🟡 Needs attention |

**Overall Assessment:** The onboarding flow is functional and well-designed, but has opportunities to reduce friction and improve conversion.

---

## 1. Sign-up Flow Analysis

### Current Flow
```
Homepage → Register → Dashboard (with Welcome Modal)
```

### Friction Points Identified

#### 1.1 ❌ Registration Form Has Too Many Fields
**File:** `src/pages/RegisterPage.tsx`

**Current fields (5):**
1. Full Name
2. Email
3. Password
4. Confirm Password
5. Experience Level

**Issue:** Each additional field reduces conversion by ~10%. The "Confirm Password" field is outdated UX.

**Recommendation:**
```diff
- Confirm Password field (use password visibility toggle instead ✅ already on login)
- Move Experience Level to post-registration profile setup
```

**Priority:** 🔴 HIGH - Could increase signups by 15-20%

---

#### 1.2 ⚠️ No Social Sign-in Options
**File:** `src/pages/RegisterPage.tsx`, `src/pages/LoginPage.tsx`

No OAuth/social login options available:
- ❌ Google Sign-in
- ❌ GitHub Sign-in  
- ❌ LinkedIn Sign-in

**Impact:** Engineers often prefer GitHub/Google auth. Missing this increases friction.

**Recommendation:** Add Google OAuth at minimum (LinkedIn for enterprise credibility)

**Priority:** 🟡 MEDIUM - Competitive disadvantage

---

#### 1.3 ✅ Good: Password Strength Indicator Present
**File:** `src/components/ui/PasswordStrengthIndicator.tsx`

Real-time feedback helps users create valid passwords on first try. Well implemented.

---

#### 1.4 ⚠️ No Email Verification During Signup
**File:** `src/hooks/useAuth.tsx:92-121`

Users go directly to dashboard after registration without email verification. While this reduces friction, it can lead to:
- Invalid email addresses in database
- Unable to send password reset emails
- Lower email deliverability scores

**Current:** Verify email only when user tries to change it later.

**Recommendation:** Add soft verification prompt (non-blocking) on dashboard after first session.

**Priority:** 🟢 LOW - Current approach is acceptable for growth stage

---

#### 1.5 ✅ Good: Plan Intent Preservation
**File:** `src/pages/RegisterPage.tsx:24-29`

```typescript
useEffect(() => {
  const plan = searchParams.get('plan');
  if (plan) {
    sessionStorage.setItem('pending_plan', plan);
  }
}, [searchParams]);
```

Users coming from `/pricing?plan=pro` have their intent preserved. However, this intent is stored but **not acted upon after registration**.

**Issue:** `pending_plan` is stored but never read post-registration.

**Recommendation:** After registration, check `sessionStorage.getItem('pending_plan')` and show upgrade modal immediately.

**Priority:** 🔴 HIGH - Direct revenue impact

---

## 2. First Interview Experience Analysis

### Current Flow
```
Dashboard → New Interview Modal → Interview Type Selection → Start → Record Answer → Submit → Feedback
```

### Strengths ✅

#### 2.1 ✅ Welcome Modal for New Users
**File:** `src/components/onboarding/WelcomeModal.tsx`

3-step onboarding tour:
1. "You've Got This" - Emotional reassurance
2. "Speak Naturally" - Sets expectations
3. "Track Your Growth" - Shows value

**Well-designed:** Progressive disclosure, skip option, smooth animations.

---

#### 2.2 ✅ First Session Prompt
**File:** `src/components/onboarding/FirstSessionPrompt.tsx`

Secondary prompt if user closes welcome modal without starting.

---

#### 2.3 ✅ Empty State Dashboard is Inviting
**File:** `src/pages/DashboardPage.tsx:280-320`

Clear 3-step visual guide:
1. Choose Topic
2. Record Answer  
3. Get Feedback

Large "Start Your First Interview" CTA.

---

### Friction Points

#### 2.4 ⚠️ New Interview Modal Has Decision Overload
**File:** `src/components/interview/NewInterviewModal.tsx`

**Current options:**
- 4 interview types
- 11 target companies
- 4 difficulty levels
- 5 question count options

**Total combinations:** 4 × 11 × 4 × 5 = **880 options**

**Impact:** Analysis paralysis for new users.

**Recommendation:** 
```
First-time users: Show simplified "Quick Start"
- "Behavioral" preset (most common)
- 2 questions (quick win)
- Medium difficulty
- Skip company selection

Returning users: Show full options
```

**Priority:** 🟡 MEDIUM - Affects time-to-first-value

---

#### 2.5 ⚠️ No Sample Question Preview
**File:** `src/components/interview/NewInterviewModal.tsx`

Users commit to starting without seeing what questions they'll face.

**Recommendation:** Add "Preview sample question" link showing one example question per type.

**Priority:** 🟢 LOW - Nice to have

---

#### 2.6 ✅ Good: Browser Audio Permission Handled
**File:** `src/pages/InterviewPage.tsx`

Recording section handles microphone permissions gracefully.

---

#### 2.7 ⚠️ No Practice/Demo Mode
**Issue:** Users can't see what the full experience looks like without consuming one of their 5 free interviews.

**Recommendation:** Add "Try Demo" that shows a pre-recorded interview flow (read-only).

**Priority:** 🟡 MEDIUM - Reduces signup-to-first-interview anxiety

---

## 3. Conversion to Paid Analysis

### Current Upgrade Triggers

| Trigger | Location | Effectiveness |
|---------|----------|---------------|
| Free limit reached | `DashboardPage.tsx:164` | ✅ Captures intent |
| Pricing page CTA | `PricingPage.tsx` | 🟡 Standard |
| Homepage preview | `HomePage.tsx:145-180` | 🟡 Passive |
| Upgrade modal | `UpgradeModal.tsx` | ✅ Good design |

### Conversion Issues

#### 3.1 ❌ Price Inconsistency Across Pages
**Files:** Multiple

| Location | Price Shown |
|----------|-------------|
| `HomePage.tsx:157` | $29/month |
| `PricingPage.tsx:15` | $19/month (MONTHLY_PRICE) |
| `UpgradeModal.tsx:131` | $29/month |

**Critical Issue:** Homepage and UpgradeModal show $29, but PricingPage shows $19.

**Recommendation:** Centralize pricing constants. Update all to match actual Stripe pricing.

**Priority:** 🔴 CRITICAL - Trust/credibility issue

---

#### 3.2 ⚠️ Trial Messaging is Inconsistent
**File:** `src/pages/HomePage.tsx:142`

```tsx
<span className="...">7-DAY FREE TRIAL</span>
```

But the `UpgradeModal.tsx` doesn't mention the trial at all.

**Recommendation:** Consistent trial messaging across all upgrade surfaces.

**Priority:** 🔴 HIGH - Trial is a key conversion driver

---

#### 3.3 ⚠️ No Usage Progress Bar
**File:** `src/pages/DashboardPage.tsx`

Users don't see "3 of 5 interviews used this month" until they hit the limit.

**Recommendation:** Add subtle progress indicator in dashboard header:
```
Free Plan: 3/5 interviews used | Upgrade for unlimited →
```

**Priority:** 🔴 HIGH - Creates urgency without frustration

---

#### 3.4 ⚠️ Upgrade Modal Asks "Why" Before Checkout
**File:** `src/components/subscription/UpgradeModal.tsx:157-190`

Asking for upgrade reason before letting user pay adds friction.

**Recommendation:** Move feedback form to post-checkout thank you page.

**Priority:** 🟡 MEDIUM - Reduces checkout completion

---

#### 3.5 ❌ pending_plan Not Used After Registration
**File:** `src/pages/RegisterPage.tsx:24-29`

User clicks "Start Free Trial" from pricing → Registers → Lands on dashboard → **Trial intent lost**.

The `pending_plan` is stored but never checked.

**Fix in `src/hooks/useAuth.tsx` register function:**
```typescript
// After navigate('/dashboard')
const pendingPlan = sessionStorage.getItem('pending_plan');
if (pendingPlan === 'pro') {
  // Trigger upgrade modal or redirect to checkout
  sessionStorage.removeItem('pending_plan');
}
```

**Priority:** 🔴 HIGH - Direct revenue loss

---

#### 3.6 ⚠️ No Upgrade Prompt After Great Performance
**Issue:** When a user scores 85+ on their first interview, that's the perfect moment to say "You're ready! Upgrade to practice more."

**Recommendation:** Add contextual upgrade prompt in `FeedbackPage.tsx` for high scores.

**Priority:** 🟡 MEDIUM - Positive reinforcement timing

---

## 4. Recommended Action Items

### Immediate (Week 1) - High Impact

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| 1 | Fix price inconsistency ($19 vs $29) | `HomePage.tsx`, `UpgradeModal.tsx` | Trust |
| 2 | Implement `pending_plan` checkout flow | `useAuth.tsx`, `DashboardPage.tsx` | Revenue |
| 3 | Add usage progress bar to dashboard | `DashboardPage.tsx` | Conversion |
| 4 | Remove "Confirm Password" field | `RegisterPage.tsx` | Signups +15% |

### Short-term (Week 2-3)

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| 5 | Consistent trial messaging | `UpgradeModal.tsx`, `HomePage.tsx` | Trust |
| 6 | Simplified first interview flow | `NewInterviewModal.tsx` | Time-to-value |
| 7 | Move upgrade feedback to post-checkout | `UpgradeModal.tsx` | Conversion |
| 8 | Add Google OAuth | `LoginPage.tsx`, `RegisterPage.tsx` | Signups |

### Medium-term (Month 1)

| # | Issue | File(s) | Impact |
|---|-------|---------|--------|
| 9 | Demo/preview mode | New component | Reduces anxiety |
| 10 | Contextual upgrade on high scores | `FeedbackPage.tsx` | Conversion |
| 11 | Move experience level to profile | `RegisterPage.tsx`, `SettingsPage.tsx` | Signups |

---

## 5. Metrics to Track

### Funnel Metrics
```
Homepage visits → Register page → Registration complete → First interview started → First interview completed → Upgrade initiated → Upgrade complete
```

### Key Conversion Points
| Metric | Current (est.) | Target |
|--------|----------------|--------|
| Homepage → Register | Unknown | 15% |
| Register → Complete signup | Unknown | 70% |
| Signup → First interview | Unknown | 60% |
| First interview → Complete | Unknown | 80% |
| Free → Paid (of actives) | Unknown | 5% |

**Recommendation:** Ensure PostHog/analytics tracks each step. Add `Events.REGISTRATION_STARTED` event on Register page load.

---

## 6. Competitive Analysis Notes

| Competitor | Sign-up Fields | Social Auth | Free Tier |
|------------|---------------|-------------|-----------|
| Pramp | 4 (no confirm pw) | Google, LinkedIn | Unlimited peer practice |
| Interviewing.io | 3 | GitHub | Waitlist model |
| Interview Simulator | 5 | None | 5/month |

**Gap:** We have more friction with fewer free features than competitors.

---

## 7. Technical Debt Identified

1. **No loading state on registration submit** - Button shows "Creating account..." but no spinner
2. **Error messages could be friendlier** - "Password validation failed" should be more specific
3. **Welcome modal state persists incorrectly** - Uses localStorage, should reset on logout
4. **Analytics events missing** - No `REGISTRATION_STARTED` event, only `USER_REGISTERED`

---

## Appendix: File Reference

| Component | Path | Purpose |
|-----------|------|---------|
| Registration | `src/pages/RegisterPage.tsx` | Sign-up form |
| Login | `src/pages/LoginPage.tsx` | Login form |
| Dashboard | `src/pages/DashboardPage.tsx` | Main hub, onboarding |
| Homepage | `src/pages/HomePage.tsx` | Marketing, CTAs |
| Pricing | `src/pages/PricingPage.tsx` | Pricing page |
| Interview | `src/pages/InterviewPage.tsx` | Recording flow |
| New Interview Modal | `src/components/interview/NewInterviewModal.tsx` | Session config |
| Upgrade Modal | `src/components/subscription/UpgradeModal.tsx` | Upsell |
| Welcome Modal | `src/components/onboarding/WelcomeModal.tsx` | New user tour |
| Auth Hook | `src/hooks/useAuth.tsx` | Auth state |

---

*Report generated from frontend code analysis. Recommend A/B testing before major changes.*
