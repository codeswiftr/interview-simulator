# User Activation Funnel Analysis

**Product:** Interview Simulator (codeswiftr-com)  
**Analysis Date:** 2026-03-18  
**Status:** LIVE (app.codeswiftr.com)

---

## Executive Summary

The activation funnel spans from user signup to first completed interview. This analysis identifies friction points in the current flow and provides actionable improvements to increase activation rates.

**Current Definition of "Activated":** User completes first interview session (status: COMPLETED + `activated_at` timestamp set)

---

## Activation Funnel Breakdown

### Step 1: Signup
**Endpoint:** `POST /api/v1/users/register`
- Captures: email, password, full_name, experience_level (optional)
- Analytics: `is_user_registered`
- Auto-login after registration (frontend flow)

### Step 2: Login
**Endpoint:** `POST /api/v1/users/login`
- Returns JWT access + refresh tokens
- Analytics: `is_user_logged_in`
- Updates `last_login_at` timestamp

### Step 3: Dashboard Onboarding
**Route:** `/dashboard`
- **WelcomeModal:** 3-step tour (Welcome → How It Works → Start)
- **FirstSessionPrompt:** Secondary CTA after WelcomeModal
- Both stored in localStorage (`interview_simulator_onboarding`)

### Step 4: Interview Creation
**Endpoint:** `POST /api/v1/interviews`
- Creates session with status=SCHEDULED
- Enforces quota: 3 free/month for free tier
- Analytics: `is_interview_created`
- Returns `remaining_interviews` for free users

### Step 5: Interview Start
**Endpoint:** `POST /api/v1/interviews/{id}/start`
- Changes status to IN_PROGRESS
- Assigns random questions based on interview_type
- Analytics: `is_interview_started`, `is_activation_started`

### Step 6: Response Recording
**Flow:** Frontend recording → Upload audio → Transcription
- **Endpoint:** `POST /api/v1/interviews/{id}/responses`
- Supports audio_url, transcript, or both
- Background async processing via `process_response_audio_async()`
- Analytics: `is_response_submitted`

### Step 7: Interview Completion
**Endpoint:** `POST /api/v1/interviews/{id}/end`
- Changes status to COMPLETED
- Calculates `duration_seconds`
- Sets `user.activated_at` (first completion only)
- Triggers background feedback generation
- Analytics: `is_interview_completed`, `is_activation_completed`

---

## Friction Points Identified

### 1. **Double Modal Barrier**
New users must navigate through **WelcomeModal (3 steps)** → **FirstSessionPrompt** before creating their first interview. This creates unnecessary friction before users experience value.

### 2. **No Guest/Trial Mode**
Users must complete full registration before experiencing the core value (getting feedback). No way to "try before signing up."

### 3. **Silent Audio Permission Failures**
If microphone permission is denied, there's no clear recovery path or fallback guidance in the InterviewPage.

### 4. **Feedback Generation Uncertainty**
After ending an interview, users see no indication that feedback is being generated. The background task runs silently.

### 5. **No Progress Visibility**
Users have no visibility into their progress toward the "15-minute promise" during the interview session.

### 6. **Experience Level Asked Too Early**
Experience level is collected at signup but not used to personalize the first interview (questions are randomly assigned).

---

## Actionable Improvements

### 1. Implement "Skip to First Interview" CTA
**Priority:** High | **Effort:** Low

Add a prominent "Skip Tour & Start Interview" button on the first step of WelcomeModal. Pre-populate with smart defaults:
- Interview type: BEHAVIORAL (lowest friction)
- Question count: 1 (quick win)
- Difficulty: MEDIUM (based on experience_level if provided)

**Implementation:**
```typescript
// In WelcomeModal.tsx, step 1
<button 
  onClick={() => createInstantSession({ 
    interview_type: 'behavioral', 
    question_count: 1 
  })}
  className="btn-primary"
>
  Skip Tour & Start First Interview →
</button>
```

**Expected Impact:** Reduce time-to-first-interview by ~60 seconds; increase activation rate by reducing drop-off between modals.

---

### 2. Add Interview Progress Indicator
**Priority:** Medium | **Effort:** Low

Add a persistent progress bar in InterviewHeader showing:
- Current question / total questions
- Estimated time remaining
- "You're X minutes away from your score"

**Implementation:**
```typescript
// In InterviewHeader component
<div className="progress-bar">
  <span>Question {currentIndex + 1} of {total}</span>
  <Progress value={(currentIndex / total) * 100} />
  <span>~{estimatedMinutesLeft} min to your score</span>
</div>
```

**Expected Impact:** Reinforces the 15-minute promise; reduces abandonment during multi-question interviews.

---

### 3. Add Feedback Generation Loading State
**Priority:** Medium | **Effort:** Medium

After `POST /interviews/{id}/end`, redirect to a "Generating Your Feedback" page with:
- Animated progress indicator
- Expected wait time (~30-60 seconds based on response count)
- Preview of what feedback will include (scores, strengths, improvements)
- Option to enable notifications when ready

**Implementation:**
```typescript
// New endpoint or WebSocket for real-time status
GET /api/v1/interviews/{id}/feedback-status
// Returns: { status: 'generating' | 'ready', progress_percent: 75 }
```

**Expected Impact:** Reduces perceived wait time; prevents users from leaving before seeing feedback; increases return rate.

---

## Metrics to Track

1. **Time to First Interview** (signup → interview creation)
2. **Time to Activation** (signup → first completion)
3. **Modal Drop-off Rate** (% who close WelcomeModal without starting interview)
4. **Interview Abandonment Rate** (% who start but don't complete)
5. **Feedback View Rate** (% of completed interviews where feedback is viewed within 5 minutes)

---

## Appendix: Current Analytics Events

| Event | Trigger |
|-------|---------|
| `is_user_registered` | After successful signup |
| `is_user_logged_in` | After successful login |
| `is_interview_created` | After POST /interviews |
| `is_interview_started` | After POST /interviews/{id}/start |
| `is_activation_started` | Same as above |
| `is_response_submitted` | After POST /interviews/{id}/responses |
| `is_interview_completed` | After POST /interviews/{id}/end |
| `is_activation_completed` | Same as above |
| `is_feedback_generated` | After background feedback complete |
| `is_feedback_viewed` | When user views feedback page |

---

*Document generated for activation optimization. Do not commit - for internal review only.*
