# Test Coverage Report — Interview Simulator Backend

Date: 2026-01-27

## How this report was generated
- Command: `uv run pytest --cov=app --cov=backend --cov-report=term-missing --cov-report=xml --cov-report=html`
- Working directory: `codeswiftr-com/interview-simulator/backend`

## Test run summary
- Result: **Failed** (tests did not fully pass)
- Totals: **12 failed, 585 passed, 554 skipped**
- Coverage: **67% total** (4453 statements, 1460 missed)
- Coverage artifacts:
  - HTML: `htmlcov/`
  - XML: `coverage.xml`

### Primary failures blocking full run
All failures are from `tests/test_content_analyzer.py` and are caused by `LLMClient` no longer exposing `.messages`:
```
AttributeError: 'LLMClient' object has no attribute 'messages'
```
Affected tests:
- `test_analyze_behavioral_question`
- `test_analyze_technical_question`
- `test_analyze_system_design_question`
- `test_analyze_handles_json_in_markdown`
- `test_analyze_handles_api_errors`
- `test_analyze_handles_malformed_json`
- `test_prompt_includes_star_instruction_for_behavioral`
- `test_prompt_excludes_star_instruction_for_technical`
- `test_prompt_includes_junior_experience_context`
- `test_prompt_includes_senior_experience_context`
- `test_prompt_includes_mid_experience_context_by_default`
- `test_prompt_uses_mid_for_unknown_experience_level`

These failures reduce coverage in `app/ai/content_analyzer.py` and related paths.

### Skipped tests (coverage impact)
Large portions of API coverage are skipped because database-dependent tests are marked with “Database not available”. This causes low coverage in most API routers and several core flows (auth, interviews, preparation, subscriptions, users, etc.).

## Coverage summary (top gaps)

### Critical API routes (low coverage)
- `app/api/subscriptions.py` — **23%**
- `app/api/users.py` — **25%**
- `app/api/interviews.py` — **28%**
- `app/api/coaching.py` — **28%**
- `app/api/feedback.py` — **30%**
- `app/api/preparation.py` — **33%**
- `app/api/questions.py` — **34%**
- `app/api/upload.py` — **37%**
- `app/api/auth.py` — **38%**
- `app/api/transcription.py` — **40%**

### Middleware / security
- `app/middleware/security_headers.py` — **0%** (completely uncovered)
- `app/dependencies.py` — **35%**
- `app/main.py` — **38%**

### AI / analysis modules
- `app/ai/content_analyzer.py` — **61%** (blocked by failing tests)
- `app/ai/video_analyzer.py` — **69%**
- `app/ai/audio_analyzer.py` — **79%**

### Healthy coverage areas (good baseline)
- Many service modules are strong: `email_service`, `video_service`, `audio_service`, `interview_service`, `background_tasks`.
- Core models are near 100%.

## Recommendations (priority order)

### P0 — Fix broken tests in `ContentAnalyzer`
- Update tests to mock the current LLM client interface (likely `client.responses.create` or similar, depending on implementation).
- Add a thin adapter interface in `content_analyzer.py` to simplify mocking and reduce API churn in tests.
- Once fixed, re-run coverage to recover ~20–30% in `app/ai/content_analyzer.py`.

### P0 — Enable DB-backed integration tests
Most API coverage is skipped due to missing DB.
- Provide a local test database (dockerized Postgres or sqlite with SQLModel).
- Add a `pytest` mark to conditionally spin up and tear down DB (e.g., via `pytest-postgresql` or Docker Compose in CI).
- Ensure `tests/test_api.py` and `tests/api/*` run as part of CI for coverage.

### P1 — Strengthen authentication and user flows
Critical security and core functionality are low coverage.
Add tests to cover:
- Login, refresh token rotation, password reset, and invalid token handling.
- Auth middleware error paths and permission checks.
- User profile updates, email change conflict, and delete cascade.

### P1 — Coverage for subscriptions & billing
- Add tests for Stripe webhook validation, plan upgrades, cancellation, and trial edge cases.
- Verify `subscriptions.py` handles missing/invalid states, and covers error responses and retries.

### P1 — Preparation pipeline end-to-end
`app/api/preparation.py` is ~33%.
- Implement happy-path and edge-case tests for preparation stages (detective → draft → practice → completion).
- Add tests for rate limiting, maximum questions, and attempt state transitions.

### P2 — Middleware and bootstrapping
- Add tests for `security_headers` middleware (headers applied on success and error paths).
- Add `app/main.py` tests for startup configuration, routers, CORS config, and exception handlers.

### P2 — Upload/Transcription/Feedback
- Add tests for file upload validation, audio conversion errors, and transcription failures.
- Expand feedback routes to cover error cases and permission checks.

## Suggested next steps
1. Fix `ContentAnalyzer` mocks and re-run coverage to confirm stability.
2. Wire a reproducible test DB in CI to remove skips and cover API flows.
3. Target auth + subscriptions + preparation routes with integration tests first.

## Coverage artifacts
- `htmlcov/index.html`
- `coverage.xml`

