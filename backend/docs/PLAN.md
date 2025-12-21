# Milestone: Fix Backend Test Failures

## Status: Ready
## Target: Dec 2025 Sprint

---

## Overview

Fix the remaining 33 backend test failures to achieve a green test suite. The failures are concentrated in security-related tests that test middleware behavior, rate limiting, and integration scenarios. Most appear to be test configuration issues rather than actual application bugs.

## Success Criteria

- [ ] All 641 tests pass (currently 594 passing, 33 failing)
- [ ] No tests skipped without documented reason
- [ ] Coverage remains ≥34%

---

## Failure Analysis

### Summary by File

| File | Failures | Root Cause |
|------|----------|------------|
| `test_security_api.py` | 14 | Rate limit middleware not applied in tests, IP validation mocking |
| `test_security_integration.py` | 14 | Missing middleware, auth flow expectations |
| `test_interview_flow_integration.py` | 1 | Quota enforcement logic |
| `test_preparation.py` | 1 | 404 on list preparations endpoint |
| `test_video_feedback.py` | 1 | File save/upload path issue |
| `test_rate_limit.py` | 14 skipped | Rate limiting not configured in test client |

### Root Causes

1. **Middleware Not Applied**: Tests use `AsyncClient` directly without full app middleware stack
2. **Rate Limit Config**: Tests don't mock or configure rate limiting properly
3. **IP Validation**: Cloudflare/Railway IP trust tests need proper header mocking
4. **Path Issues**: Some tests expect different API paths or file locations

---

## Implementation Plan

### Phase 1: Security API Tests (14 failures)
**Goal**: Fix rate limit and IP validation test infrastructure

| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Review `test_security_api.py` setup - check if middleware is applied | 30m |
| 1.2 | Fix `TestRateLimitSecurity::test_rate_limit_sliding_window` - mock rate limiter | 30m |
| 1.3 | Fix `TestIPValidationSecurity` tests - proper header mocking for CF/Railway | 45m |
| 1.4 | Fix `TestSuspiciousActivityDetection` tests - mock detection config | 30m |
| 1.5 | Fix `TestRateLimitMiddleware` tests - ensure middleware in test app | 45m |
| 1.6 | Fix `TestDDoSProtection` tests - mock request size limits | 30m |

**Checkpoint**: 14 security_api tests pass

### Phase 2: Security Integration Tests (14 failures)
**Goal**: Fix integration test setup for auth flows and rate limiting

| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Fix `TestAuthenticationFlowSecurity` - password migration mocking | 45m |
| 2.2 | Fix `TestAPIRateLimitingIntegration` - rate limit test setup | 45m |
| 2.3 | Fix `TestContentSecurityIntegration` - sanitization expectations | 30m |
| 2.4 | Fix `TestCORSSecurityIntegration` - CORS preflight headers | 20m |
| 2.5 | Fix `TestFileUploadSecurity` - path traversal prevention | 30m |
| 2.6 | Fix `TestSessionTimeoutSecurity` - token expiration mocking | 30m |

**Checkpoint**: 14 security_integration tests pass

### Phase 3: Other Failures (3 failures)
**Goal**: Fix remaining isolated test failures

| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Fix `test_quota_enforcement_integration` - expects 402, gets 201 | 30m |
| 3.2 | Fix `test_list_preparations` - expects 200, gets 404 | 20m |
| 3.3 | Fix `test_upload_video_updates_response_and_saves_file` | 30m |

**Checkpoint**: All 641 tests pass

### Phase 4: Cleanup
**Goal**: Document and organize

| Task | Description | Est |
|------|-------------|-----|
| 4.1 | Enable skipped rate_limit tests or document why skipped | 30m |
| 4.2 | Run full test suite, verify all pass | 15m |
| 4.3 | Commit changes | 10m |

---

## Technical Notes

### Test Client Setup Pattern

Current issue: Tests may use `AsyncClient(app=app)` without middleware:

```python
# Current (may skip middleware)
async with AsyncClient(app=app, base_url="http://test") as client:
    ...

# Fix: Use transport to include middleware
from httpx import ASGITransport
async with AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test"
) as client:
    ...
```

### Rate Limit Mocking

```python
# Mock rate limiter in tests
@pytest.fixture
def mock_rate_limiter(monkeypatch):
    monkeypatch.setattr("app.middleware.rate_limit.check_rate_limit", lambda *args: True)
```

### IP Trust Headers

```python
# For Cloudflare tests
headers = {
    "CF-Connecting-IP": "1.2.3.4",
    "CF-Ray": "abc123",
    "X-Forwarded-For": "1.2.3.4"
}
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| Fixing tests may reveal actual bugs | Document any found, fix separately |
| Rate limit tests may be flaky | Use deterministic mocks, not real timing |
| Middleware order matters | Test with full app stack when possible |

---

## Estimated Effort

| Phase | Tasks | Est |
|-------|-------|-----|
| Phase 1 | 6 tasks | ~3.5h |
| Phase 2 | 6 tasks | ~3.5h |
| Phase 3 | 3 tasks | ~1.5h |
| Phase 4 | 3 tasks | ~1h |

**Total**: ~9.5 hours

---

## Commands

```bash
# Run all tests
cd backend && uv run pytest

# Run specific failing file
uv run pytest tests/test_security_api.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run single test
uv run pytest tests/test_security_api.py::TestRateLimitSecurity::test_rate_limit_sliding_window -v
```
