# Sprint 12: Scale Readiness

## Status: In Progress
## Target: January 2025

---

## Previous Sprint Summary

### Sprint 11: Soft Launch Hardening - COMPLETED
- **Epic 1**: Critical Path Tests - DONE (email, auth, preparation, content sanitizer tests)
- **Epic 2**: Question Recommendations - DONE (backend service + frontend integration)
- **Epic 3**: Interview Export & Sharing - DONE (PDF export, share links, public view)
- **Epic 4**: Sentry Integration - DONE (backend + frontend error monitoring)

**Achievements:**
- 782 backend tests (up from 385)
- PDF export with WeasyPrint
- Share link system with 7-day expiry
- Sentry error tracking integrated
- Question recommendation engine live

---

## Overview

Sprint 12 focuses on **scale readiness** - preparing the platform for increased user load and ensuring a polished, professional experience. The four epics address the most critical gaps identified in our due diligence review.

**Why These 4 Epics?**
1. **Epic 5**: Frontend tests (0% → 40%) - Critical gap in every audit
2. **Epic 6**: Auth hardening - Security-critical for production
3. **Epic 7**: Performance optimization - User-facing quality
4. **Epic 8**: Production resilience - Stability under load

**What We're NOT Doing:**
- Video Analysis MVP (defer to Sprint 13 - 30h effort)
- B2B Team Features (defer to Sprint 14 - 45h effort)
- These require dedicated sprints

---

## Success Criteria

- [ ] Frontend test coverage ≥ 40% (from 0%)
- [ ] Refresh token rotation working
- [ ] Main bundle < 500KB (from 837KB)
- [ ] Password policy enforced (8+ chars)
- [ ] All auth flows have retry/fallback
- [ ] Mobile responsive polish complete

---

## Epic 5: Frontend Test Foundation (P0)

**ICE Score**: 10/10 (Impact: 10, Confidence: 10, Ease: 8)
**Priority**: CRITICAL - 0% frontend coverage is unacceptable
**Effort**: 16-20 hours

### Rationale

Every audit identifies "Frontend test coverage: 0%" as the #1 gap. Test infrastructure exists (Vitest + RTL + MSW) but no tests are written. This creates:
- Zero confidence in frontend changes
- Manual QA burden
- Risk of regressions

### Current State

| Metric | Current | Target |
|--------|---------|--------|
| Frontend tests | 0 | 50+ |
| Coverage | 0% | 40% |
| Critical paths covered | 0 | 5 |

### Implementation Plan

#### Phase 5.1: Test Infrastructure Setup (2h)

**Files to Create:**
- `frontend/src/test/setup.ts` - Global test setup
- `frontend/src/test/mocks/handlers.ts` - MSW API handlers
- `frontend/src/test/mocks/server.ts` - MSW server setup
- `frontend/src/test/utils.tsx` - Test utilities (render with providers)

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `renderWithProviders()` | Wraps components with Router, Query, Auth contexts |
| `createMockUser()` | Generates test user data |
| `createMockInterview()` | Generates test interview data |
| `createMockFeedback()` | Generates test feedback data |
| `setupMockServer()` | Initializes MSW with default handlers |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_setup_renders_without_crash` | Verifies test utilities work |
| `test_mock_server_intercepts_requests` | MSW catches API calls |

---

#### Phase 5.2: Auth Hook Tests (4h)

**Files to Create:**
- `frontend/src/hooks/useAuth.test.tsx`

**Functions to Test:**
| Function | Purpose |
|----------|---------|
| `login()` | Authenticates user, stores tokens |
| `logout()` | Clears tokens, resets state |
| `register()` | Creates account, auto-logs in |
| `refreshToken()` | Refreshes expired access token |
| `isAuthenticated` | Returns true when logged in |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_login_stores_tokens` | Tokens saved to localStorage |
| `test_login_sets_user_state` | User object populated |
| `test_login_invalid_credentials` | Shows error message |
| `test_logout_clears_tokens` | localStorage cleared |
| `test_logout_redirects_to_login` | Navigates to /login |
| `test_register_creates_account` | API called with form data |
| `test_register_auto_logs_in` | User logged in after register |
| `test_refresh_token_on_401` | Automatically refreshes |
| `test_is_authenticated_true_with_token` | Returns true |
| `test_is_authenticated_false_without_token` | Returns false |

---

#### Phase 5.3: Critical Component Tests (6h)

**Files to Create:**
- `frontend/src/components/interview/RecordButton.test.tsx`
- `frontend/src/components/feedback/ScoreRing.test.tsx`
- `frontend/src/components/layout/Header.test.tsx`

**Components to Test:**
| Component | Purpose |
|-----------|---------|
| `RecordButton` | Audio recording control |
| `ScoreRing` | Circular score display |
| `Header` | Navigation, auth status |
| `Toast` | Notification display |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_record_button_starts_recording` | Shows recording state |
| `test_record_button_stops_recording` | Returns audio blob |
| `test_record_button_disabled_during_upload` | Prevents double-submit |
| `test_score_ring_displays_value` | Shows percentage |
| `test_score_ring_colors_by_threshold` | Red/yellow/green |
| `test_header_shows_login_when_logged_out` | Login button visible |
| `test_header_shows_user_when_logged_in` | User menu visible |
| `test_header_mobile_menu_toggles` | Hamburger works |
| `test_toast_displays_message` | Shows notification |
| `test_toast_auto_dismisses` | Disappears after timeout |

---

#### Phase 5.4: Page Integration Tests (4h)

**Files to Create:**
- `frontend/src/pages/LoginPage.test.tsx`
- `frontend/src/pages/InterviewPage.test.tsx`
- `frontend/src/pages/FeedbackPage.test.tsx`

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_login_page_submits_form` | Calls API with credentials |
| `test_login_page_shows_error` | Displays API error |
| `test_login_page_redirects_on_success` | Navigates to dashboard |
| `test_interview_page_loads_questions` | Fetches from API |
| `test_interview_page_records_audio` | Recording UI works |
| `test_interview_page_submits_response` | Uploads audio |
| `test_interview_page_beforeunload_warning` | Prevents accidental close |
| `test_feedback_page_displays_scores` | Shows all metrics |
| `test_feedback_page_polls_for_processing` | Updates when ready |
| `test_feedback_page_export_button` | Downloads PDF |
| `test_feedback_page_share_button` | Opens share modal |

---

### Testing Strategy

```bash
# Run all frontend tests
cd frontend && npm run test

# Run with coverage
npm run test:coverage

# Run specific file
npm run test -- src/hooks/useAuth.test.tsx
```

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MSW setup complexity | Medium | Follow official examples |
| React 19 compatibility | Low | Use @testing-library/react 16+ |
| Async state testing | Medium | Use waitFor() utilities |

---

## Epic 6: Authentication Hardening (P0)

**ICE Score**: 9/10 (Impact: 10, Confidence: 9, Ease: 8)
**Priority**: CRITICAL - Security for production users
**Effort**: 12-16 hours

### Rationale

Multiple security and UX issues identified:
- Refresh token stored but never used (users logged out after 30min)
- Password minimum is 6 chars (should be 8+)
- Email change without verification
- No MediaRecorder browser check

### Current State

| Issue | Status | Risk |
|-------|--------|------|
| Refresh token not working | BROKEN | HIGH - users logged out |
| Password policy weak | INSECURE | MEDIUM - weak passwords |
| Email change unverified | INSECURE | MEDIUM - account hijack |
| Browser compatibility | MISSING | LOW - cryptic errors |

### Implementation Plan

#### Phase 6.1: Refresh Token Implementation (6h)

**Files to Change:**
- `frontend/src/lib/api.ts` - Add token refresh interceptor
- `frontend/src/hooks/useAuth.tsx` - Handle refresh flow
- `backend/app/api/auth.py` - Verify refresh endpoint works

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `refreshAccessToken()` | Calls /auth/refresh with refresh token |
| `setupTokenRefreshInterceptor()` | Intercepts 401, retries with new token |
| `isTokenExpiringSoon()` | Checks if access token expires in <5min |
| `proactiveTokenRefresh()` | Refreshes before expiry |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_401_triggers_refresh` | Automatically refreshes token |
| `test_refresh_retries_original_request` | Original request succeeds |
| `test_refresh_failure_logs_out` | User redirected to login |
| `test_concurrent_refresh_deduped` | Only one refresh at a time |
| `test_proactive_refresh_before_expiry` | Refreshes with 5min left |

---

#### Phase 6.2: Password Policy Enhancement (3h)

**Files to Change:**
- `backend/app/api/auth.py` - Add password validation
- `backend/app/utils/password_validation.py` - Password rules
- `frontend/src/pages/RegisterPage.tsx` - Password strength UI
- `frontend/src/pages/SettingsPage.tsx` - Password change validation

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `validate_password_strength()` | Enforces 8+ chars, complexity |
| `get_password_strength_score()` | Returns 0-100 strength score |
| `get_password_feedback()` | Returns improvement suggestions |

**Password Rules:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (optional but encouraged)

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_password_minimum_length` | Rejects < 8 chars |
| `test_password_requires_uppercase` | Requires uppercase |
| `test_password_requires_lowercase` | Requires lowercase |
| `test_password_requires_number` | Requires digit |
| `test_password_strength_score` | Returns 0-100 |
| `test_password_feedback_helpful` | Suggests improvements |

---

#### Phase 6.3: Email Verification for Changes (2h)

**Files to Change:**
- `backend/app/api/users.py` - Add email change verification
- `backend/app/services/email_service.py` - Send verification email
- `frontend/src/pages/SettingsPage.tsx` - Show verification pending

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `request_email_change()` | Sends verification to new email |
| `confirm_email_change()` | Validates token, updates email |
| `send_email_change_verification()` | Sends verification link |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_email_change_requires_verification` | Not immediate |
| `test_email_change_sends_verification` | Email sent |
| `test_email_change_token_expires` | 24h expiry |
| `test_email_change_confirms_with_token` | Updates on valid token |

---

#### Phase 6.4: Browser Compatibility Checks (1h)

**Files to Change:**
- `frontend/src/hooks/useAudioRecording.ts` - Add capability check
- `frontend/src/components/interview/BrowserWarning.tsx` - Create warning

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `checkBrowserCompatibility()` | Returns supported features |
| `isMediaRecorderSupported()` | Checks MediaRecorder API |
| `getRecommendedBrowser()` | Suggests Chrome/Firefox |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_compatibility_check_runs` | Executes on mount |
| `test_warning_shown_for_unsupported` | Modal appears |
| `test_warning_dismissible` | User can continue anyway |

---

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token refresh race conditions | High | Use mutex/queue |
| Password policy breaks existing users | Low | Only for new passwords |
| Email verification complexity | Medium | Simple token-based flow |

---

## Epic 7: Performance & UX Optimization (P1)

**ICE Score**: 8/10 (Impact: 8, Confidence: 9, Ease: 7)
**Priority**: HIGH - User-facing quality
**Effort**: 10-12 hours

### Rationale

Due diligence identified:
- Main bundle 837KB (target: <500KB)
- DashboardPage 498KB (Recharts heavy)
- Mobile responsiveness "Partial"
- Some UX polish needed

### Current State

| Metric | Current | Target |
|--------|---------|--------|
| Main bundle | 837KB | <500KB |
| Dashboard chunk | 498KB | <200KB |
| Mobile responsive | Partial | Complete |
| Lighthouse performance | ~70 | >85 |

### Implementation Plan

#### Phase 7.1: Code Splitting & Lazy Loading (4h)

**Files to Change:**
- `frontend/vite.config.ts` - Manual chunk configuration
- `frontend/src/App.tsx` - Dynamic imports for pages
- `frontend/src/pages/DashboardPage.tsx` - Lazy load Recharts

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `lazyLoadChart()` | Dynamically imports Recharts |
| `ChartSkeleton` | Shows while chart loads |
| Vite `manualChunks` config | Splits vendor bundles |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_chart_lazy_loads` | Not in initial bundle |
| `test_skeleton_shows_while_loading` | Loading state visible |
| `test_vendor_chunks_separate` | React/Recharts split |

---

#### Phase 7.2: Bundle Optimization (3h)

**Files to Change:**
- `frontend/vite.config.ts` - Optimize build
- `frontend/package.json` - Check for heavy deps

**Optimization Targets:**
| Target | Action |
|--------|--------|
| Recharts | Lazy load, tree-shake |
| React Query | Already efficient |
| Lucide icons | Import specific icons only |
| Unused code | Remove dead exports |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_build_size_under_limit` | Main < 500KB |
| `test_no_duplicate_react` | Single React instance |
| `test_tree_shaking_works` | Unused code removed |

---

#### Phase 7.3: Mobile Responsiveness Polish (3h)

**Files to Change:**
- `frontend/src/pages/DashboardPage.tsx` - Stats stacking
- `frontend/src/pages/InterviewPage.tsx` - Header overflow
- `frontend/src/components/interview/ShareModal.tsx` - Modal width
- `frontend/src/index.css` - Mobile-specific styles

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_dashboard_stacks_on_mobile` | Grid becomes single column |
| `test_interview_header_no_overflow` | Text truncates |
| `test_modal_fits_mobile_screen` | Full width on small screens |
| `test_touch_targets_adequate` | 44px minimum |

---

#### Phase 7.4: Loading States & Skeletons (2h)

**Files to Create:**
- `frontend/src/components/ui/Skeleton.tsx`

**Files to Change:**
- `frontend/src/pages/DashboardPage.tsx` - Add skeletons
- `frontend/src/pages/FeedbackPage.tsx` - Add skeletons

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_skeleton_shows_during_load` | Placeholder visible |
| `test_skeleton_replaced_with_content` | Real data appears |
| `test_skeleton_accessible` | Has aria-busy |

---

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lazy loading flash | Low | Use Suspense with skeleton |
| Chart not loading | Medium | Error boundary fallback |
| Breaking mobile UI | Low | Test on real devices |

---

## Epic 8: Production Resilience (P1)

**ICE Score**: 8/10 (Impact: 9, Confidence: 8, Ease: 7)
**Priority**: HIGH - Stability under load
**Effort**: 8-10 hours

### Rationale

As we scale, we need:
- Graceful degradation when services fail
- Retry logic for transient errors
- Circuit breakers for external APIs
- Better error recovery UX

### Current State

| Feature | Status |
|---------|--------|
| API retry logic | Partial (uploads only) |
| AI service fallbacks | Missing |
| Error recovery UI | Basic |
| Rate limit handling | Backend only |

### Implementation Plan

#### Phase 8.1: API Retry & Timeout Handling (3h)

**Files to Change:**
- `frontend/src/lib/api.ts` - Add retry interceptor
- `frontend/src/lib/retry.ts` - Create retry utility

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `withRetry()` | Wraps API calls with retry logic |
| `isRetryableError()` | Determines if error is transient |
| `exponentialBackoff()` | Calculates retry delay |
| `withTimeout()` | Adds timeout to requests |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_retry_on_network_error` | Retries transient failures |
| `test_no_retry_on_4xx` | Doesn't retry client errors |
| `test_exponential_backoff` | Delays increase |
| `test_max_retries_exceeded` | Eventually fails |
| `test_timeout_triggers_error` | Request times out |

---

#### Phase 8.2: AI Service Fallbacks (3h)

**Files to Change:**
- `backend/app/ai/transcriber.py` - Add fallback provider
- `backend/app/ai/content_analyzer.py` - Add fallback
- `backend/app/services/feedback_service.py` - Graceful degradation

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `transcribe_with_fallback()` | Tries primary, falls back to secondary |
| `analyze_with_fallback()` | Tries Claude, falls back to simpler analysis |
| `generate_fallback_feedback()` | Returns basic feedback if AI fails |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_transcription_fallback_to_groq` | Uses Groq if OpenAI fails |
| `test_analysis_fallback_graceful` | Returns partial feedback |
| `test_fallback_notifies_user` | Shows degraded mode notice |

---

#### Phase 8.3: Error Recovery UX (2h)

**Files to Change:**
- `frontend/src/components/ErrorBoundary.tsx` - Enhance recovery
- `frontend/src/components/ui/RetryButton.tsx` - Create component
- `frontend/src/pages/FeedbackPage.tsx` - Add retry for failed feedback

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `RetryButton` | Button with loading state for retries |
| `useRetry()` | Hook for retry state management |
| `ErrorRecoveryOptions` | Component with retry/refresh/home options |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_retry_button_shows_loading` | Spinner during retry |
| `test_error_recovery_options` | Shows multiple options |
| `test_successful_retry_clears_error` | Error state reset |

---

#### Phase 8.4: Rate Limit Handling (2h)

**Files to Change:**
- `frontend/src/lib/api.ts` - Handle 429 responses
- `frontend/src/components/ui/RateLimitWarning.tsx` - Create component

**Functions to Implement:**
| Function | Purpose |
|----------|---------|
| `handleRateLimitResponse()` | Extracts retry-after, shows warning |
| `RateLimitWarning` | Displays countdown until retry |
| `queueRequestsOnRateLimit()` | Queues requests during limit |

**Test Cases:**
| Test Name | Behavior |
|-----------|----------|
| `test_429_shows_warning` | User sees rate limit message |
| `test_retry_after_countdown` | Shows time remaining |
| `test_requests_queue_during_limit` | Doesn't spam server |

---

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fallback quality lower | Medium | Notify user of degraded mode |
| Retry loops | High | Max retry limit, exponential backoff |
| UX confusion | Low | Clear messaging |

---

## Sprint 12 Summary

### Total Estimated Effort

| Epic | Effort | Priority | ROI |
|------|--------|----------|-----|
| Epic 5: Frontend Test Foundation | 16-20h | P0 | 10/10 |
| Epic 6: Auth Hardening | 12-16h | P0 | 9/10 |
| Epic 7: Performance Optimization | 10-12h | P1 | 8/10 |
| Epic 8: Production Resilience | 8-10h | P1 | 8/10 |
| **Total** | **46-58h** | | |

### Execution Order

1. **Week 1**: Epic 5 (Phase 5.1-5.2) + Epic 6 (Phase 6.1-6.2)
2. **Week 2**: Epic 5 (Phase 5.3-5.4) + Epic 6 (Phase 6.3-6.4)
3. **Week 3**: Epic 7 (all phases) + Epic 8 (all phases)

### Files Changed Summary

**Frontend (New):**
- `src/test/setup.ts`
- `src/test/mocks/handlers.ts`
- `src/test/mocks/server.ts`
- `src/test/utils.tsx`
- `src/hooks/useAuth.test.tsx`
- `src/components/interview/RecordButton.test.tsx`
- `src/components/feedback/ScoreRing.test.tsx`
- `src/pages/LoginPage.test.tsx`
- `src/pages/InterviewPage.test.tsx`
- `src/pages/FeedbackPage.test.tsx`
- `src/components/interview/BrowserWarning.tsx`
- `src/components/ui/Skeleton.tsx`
- `src/components/ui/RetryButton.tsx`
- `src/components/ui/RateLimitWarning.tsx`
- `src/lib/retry.ts`

**Frontend (Modified):**
- `src/lib/api.ts` (token refresh, retry, rate limit)
- `src/hooks/useAuth.tsx` (refresh flow)
- `src/hooks/useAudioRecording.ts` (compatibility check)
- `src/pages/RegisterPage.tsx` (password strength)
- `src/pages/SettingsPage.tsx` (email verification, password)
- `src/pages/DashboardPage.tsx` (lazy load, skeletons, mobile)
- `src/pages/InterviewPage.tsx` (mobile)
- `src/components/ErrorBoundary.tsx` (recovery options)
- `vite.config.ts` (code splitting)

**Backend (Modified):**
- `app/api/auth.py` (password validation)
- `app/api/users.py` (email change verification)
- `app/services/email_service.py` (verification emails)
- `app/ai/transcriber.py` (fallback)
- `app/ai/content_analyzer.py` (fallback)
- `app/services/feedback_service.py` (graceful degradation)

---

## Deferred to Future Sprints

### Sprint 13: Video Analysis MVP (30h)
- Video recording UI
- Basic video analysis (posture, eye contact)
- Video feedback display
- Integration with feedback page

### Sprint 14: B2B Team Features (45h)
- Team/Organization models
- Admin dashboard
- Seat-based licensing
- Member invitation flow
- Team analytics

### Sprint 15: Advanced Features
- Interview comparison (A/B your answers)
- Mock interviewer personas
- Custom question banks
- API for enterprise integrations

---

## References

- [CODEBASE_AUDIT.md](./CODEBASE_AUDIT.md) - Coverage metrics
- [DUE_DILIGENCE_REPORT.md](./DUE_DILIGENCE_REPORT.md) - Overall assessment
- [SOFT_LAUNCH_REVIEW.md](./SOFT_LAUNCH_REVIEW.md) - Frontend gaps
- [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) - Security posture
