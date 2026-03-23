---
title: 14-Day Validation Scoreboard (Interview Simulator)
last_updated: 2025-12-14
---

# 14-Day Validation Scoreboard · Interview Simulator

**Goal (Day 14):** prove a repeatable path to paid users with acceptable activation + early retention.

**Primary decision:** double down on acquisition (scale) vs fix onboarding/value (iterate) vs reposition.

## North Star + guardrails

- **North Star (NSM):** `Activated users / week`  
  Definition: users who complete ≥1 interview and view feedback (see activation definition).
- **Guardrails:** latency + reliability (avoid growth masking product failure)
  - p95 “submit → feedback view” < 2 minutes (instrumentation task below)
  - error rate for interview submission < 2%

## Funnel definitions (must be consistent)

### Acquisition
- **Visitor:** `page_viewed` from marketing sites for Interview Simulator pages.
- **Signup:** `user_registered` in app.

### Activation (Aha)
- **Activated user (primary):** within **24h of signup**, user triggers:
  - `interview_started` **AND**
  - `interview_completed` **AND**
  - `feedback_viewed`
- **Activated user (fallback):** within 24h of signup, `interview_completed` (if feedback tracking is noisy).

### Retention
- **D2 retained:** user triggers `interview_started` on day 2 after signup (24–48h window).
- **D7 retained:** user triggers `interview_started` in days 7–8 after signup.

### Monetization
- **Upgrade intent:** `upgrade_modal_opened` or `checkout_started`
- **Paid conversion:** `subscription_created` (server-side Stripe webhook)

## PostHog event map (source of truth)

### Marketing (marketing-template)
- `page_viewed` (props: `domain`, `product`, `path`, `utm_*`)
- `cta_clicked` (props: `domain`, `product`, `button_id`, `button_text`, `page`, `utm_*`)
- `lead_form_submitted` (props: `domain`, `product`, `form_id`, `lead_magnet_slug?`, `utm_*`)
- `lead_magnet_requested` (props: `domain`, `product`, `lead_magnet_slug`, `lead_magnet_title`, `utm_*`)

### App (interview-simulator frontend)
- `user_registered` (props: `product`, `domain`, `signup_method`, `experience_level`)
- `user_logged_in` (props: `product`, `domain`, `login_method`)
- `interview_started` (props: interview metadata if available)
- `interview_completed`
- `feedback_viewed` (props: includes `session_id`)
- `upgrade_modal_opened` (props: `surface`)
- `upgrade_cta_clicked` (props: `surface`, `plan`)
- `checkout_started` (props: `plan`)

### Billing (interview-simulator backend)
- `subscription_created` (props: `tier`, `subscription_id`, `amount?`, `currency?`)
- `subscription_canceled`

## Scoreboard (pass/fail gates)

### Day 3 gate (are we getting enough signal?)
- **Signup volume:** ≥ 10 `user_registered`
- **Activation rate:** ≥ 25% of signups reach `interview_started` within 24h
- **Quality proxy:** ≥ 60% of `interview_completed` have `feedback_viewed`
- **Fail condition:** < 5 signups OR < 15% start rate → fix top-of-funnel + onboarding before shipping features

### Day 7 gate (is the product sticky enough to monetize?)
- **Signups:** ≥ 25 total
- **Activated users:** ≥ 8 (primary activation definition)
- **D2 retained:** ≥ 15% of signups
- **Upgrade intent:** ≥ 10 `checkout_started` + `upgrade_cta_clicked` combined
- **Fail condition:** Activation < 25% OR D2 < 10% → iterate on first-session flow, not acquisition

### Day 14 gate (is there a path to $10k MRR?)
- **Signups:** ≥ 50 total
- **Activated users:** ≥ 20 total
- **Paid conversions:** ≥ 5 `subscription_created` (or ≥ 8% of activated, whichever is higher)
- **D7 retained:** ≥ 12% of signups
- **Pass condition:** hit all four → scale acquisition + add Team tier experiment

## Dashboard widgets to build in PostHog

- **Funnel:** `user_registered → interview_started → interview_completed → feedback_viewed → checkout_started → subscription_created`
- **Activation cohort:** signup cohorts with day-0 activation % and D2/D7 retention
- **Channel report:** signups by `utm_source`, `utm_campaign`, referrer (from marketing `page_viewed`)
- **Billing:** checkout_started vs subscription_created (drop-off)

## Instrumentation gaps (tasks)

1. Add timing props for feedback latency:
   - on backend: include `feedback_generated_at` on feedback object
   - on frontend: emit `feedback_viewed` with `latency_ms`
2. Capture “signup intent source”:
   - persist UTM parameters from marketing → app (localStorage) and attach to `user_registered`
3. Add a lightweight in-app “why did you upgrade?” survey event:
   - `upgrade_reason_submitted` (props: reason enum + free text length)

