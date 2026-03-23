# Test Expansion Plan - Interview Simulator
## Date: 2026-02-02
## Goal: Expand coverage from 67% to 75%+ (focusing on critical gaps)

---

## Current Coverage Status

Based on TEST_COVERAGE_REPORT.md:
- **Overall Coverage**: 67% (4453 statements, 1460 missed)
- **Test Count**: 585 passing, 554 skipped, 12 failing
- **Blockers**: ContentAnalyzer tests failing due to LLM API changes

---

## Priority Areas for Test Expansion

### P0 - Critical Gaps (Target: +8-10% coverage)

#### 1. Middleware - Security Headers (0% → 90%+)
**File**: `app/middleware/security_headers.py`
**Lines**: 67 total
**Current Coverage**: 0%
**Impact**: High (security-critical)

**Test Requirements**:
- Security headers applied in production mode
- Headers skipped in debug mode
- CSP directives validated
- HSTS header verification
- X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- Permissions-Policy validation
- Error path coverage

**Test File**: `tests/middleware/test_security_headers.py`
**Estimated Tests**: 8-10 tests

---

#### 2. Coaching API (28% → 70%+)
**File**: `app/api/coaching.py`
**Lines**: 333 total (94 missed)
**Current Coverage**: 28%
**Impact**: Medium (new feature, revenue-related)

**Test Requirements**:
- Rate limiting (5 hints per minute per user)
- Question type validation
- AI client initialization
- Streaming response handling
- Fallback to static hints
- API errors and retries
- OpenRouter integration mocking
- Concurrent requests handling

**Test File**: `tests/api/test_coaching.py`
**Estimated Tests**: 15-18 tests

---

#### 3. Fix ContentAnalyzer Tests (12 failing → 0 failing)
**File**: `tests/test_content_analyzer.py`
**Issue**: `LLMClient` interface change
**Impact**: High (blocks accurate coverage measurement)

**Fix Requirements**:
- Update mock to match current LLM client interface
- Verify all 12 tests pass
- Restore coverage in `app/ai/content_analyzer.py`

**Estimated Work**: 1 test file update

---

### P1 - Important Gaps (Target: +5-7% coverage)

#### 4. Users API Edge Cases (25% → 65%+)
**File**: `app/api/users.py`
**Current Coverage**: 25%

**Test Requirements**:
- User profile updates with validation
- Email change conflicts (duplicate email)
- Password validation edge cases
- User deletion cascade
- Permission checks
- Rate limiting on registration
- Email verification flow

**Test File**: `tests/api/test_users_edge_cases.py`
**Estimated Tests**: 12-15 tests

---

#### 5. Subscriptions API - Payment Flows (23% → 60%+)
**File**: `app/api/subscriptions.py`
**Current Coverage**: 23%

**Test Requirements**:
- Plan upgrades and downgrades
- Trial period handling
- Cancellation edge cases
- Invalid Stripe events
- Webhook retry logic
- Missing payment method
- Subscription status transitions

**Test File**: `tests/api/test_subscriptions_edge_cases.py`
**Estimated Tests**: 10-12 tests

---

#### 6. Interviews API - Session Management (28% → 65%+)
**File**: `app/api/interviews.py`
**Current Coverage**: 28%

**Test Requirements**:
- Invalid question counts (boundary testing)
- Concurrent session limits by tier
- Interview completion edge cases
- Response submission validation
- Cross-user access prevention
- Partial interview cleanup
- Video/audio upload failures

**Test File**: `tests/api/test_interviews_edge_cases.py`
**Estimated Tests**: 14-16 tests

---

### P2 - Service Layer Enhancement (Target: +3-5% coverage)

#### 7. Feedback Service Error Paths
**File**: `app/services/feedback_service.py`
**Current Coverage**: Good baseline, needs error paths

**Test Requirements**:
- AI API failures and retries
- Malformed AI responses
- Database errors during feedback save
- Concurrent feedback generation
- Rate limiting per tier

**Test File**: `tests/services/test_feedback_service_errors.py`
**Estimated Tests**: 8-10 tests

---

#### 8. Interview Service - Complex Flows
**File**: `app/services/interview_service.py`
**Current Coverage**: 18% (needs significant improvement)

**Test Requirements**:
- Question assignment algorithm
- Category filtering edge cases
- Difficulty distribution
- Time limit validation
- Session state management
- Database transaction handling

**Test File**: `tests/services/test_interview_service_coverage.py` (enhance existing)
**Estimated Tests**: 10-12 tests

---

## Test Implementation Strategy

### Testing Patterns to Follow

Based on existing tests, use these patterns:

#### 1. API Testing Pattern
```python
@pytest.mark.asyncio
@requires_db
async def test_endpoint_name(client: AsyncClient, test_user):
    """Test description."""
    # Arrange
    token = await register_and_login(client)

    # Act
    response = await client.post(
        "/api/v1/endpoint",
        headers={"Authorization": token},
        json={"key": "value"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["field"] == expected_value
```

#### 2. Service Testing Pattern
```python
@pytest.mark.asyncio
async def test_service_method(db_session: AsyncSession):
    """Test description."""
    # Arrange
    service = ServiceClass()

    # Act
    result = await service.method(db_session, param)

    # Assert
    assert result is not None
```

#### 3. Mocking External Services
```python
@pytest.mark.asyncio
@patch("app.api.coaching.get_coaching_client")
async def test_with_mock(mock_client, client):
    """Test with mocked external service."""
    # Setup mock
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="hint text"))]
    mock_client.return_value.chat.completions.create.return_value = mock_response

    # Test logic
```

---

## Test Execution Plan

### Phase 1: Fix Blockers (Day 1)
1. Fix ContentAnalyzer tests (12 failing → 0 failing)
2. Verify database connection for skipped tests
3. Run full test suite to establish baseline

### Phase 2: Critical Coverage (Day 2-3)
1. Add middleware tests (security_headers)
2. Add coaching API tests
3. Run coverage report: target 70%+

### Phase 3: API Layer (Day 4-5)
1. Users API edge cases
2. Subscriptions edge cases
3. Interviews edge cases
4. Run coverage report: target 73%+

### Phase 4: Service Layer (Day 6)
1. Feedback service errors
2. Interview service coverage
3. Run final coverage report: target 75%+

---

## Success Metrics

| Metric | Before | Target | Stretch |
|--------|--------|--------|---------|
| Line Coverage | 67% | 75% | 80% |
| Test Count | 585 | 660+ | 700+ |
| Failing Tests | 12 | 0 | 0 |
| Skipped Tests | 554 | 0 | 0 |
| API Coverage | ~25-40% | 65%+ | 75%+ |
| Middleware Coverage | 0% | 90%+ | 95%+ |
| Service Coverage | ~40-60% | 70%+ | 80%+ |

---

## Quality Gates

All new tests must:
- ✅ Use descriptive names following `test_<action>_<expected_result>` pattern
- ✅ Include comprehensive docstrings
- ✅ Follow AAA pattern (Arrange, Act, Assert)
- ✅ Mock external services (Stripe, OpenAI, OpenRouter)
- ✅ Be independent (no shared state)
- ✅ Use existing fixtures from conftest.py
- ✅ Handle async/await correctly with FastAPI
- ✅ Include both happy path and error cases

---

## Files to Create

### New Test Files
1. `tests/middleware/test_security_headers.py` (~250 lines, 8-10 tests)
2. `tests/api/test_coaching.py` (~500 lines, 15-18 tests)
3. `tests/api/test_users_edge_cases.py` (~400 lines, 12-15 tests)
4. `tests/api/test_subscriptions_edge_cases.py` (~350 lines, 10-12 tests)
5. `tests/api/test_interviews_edge_cases.py` (~450 lines, 14-16 tests)
6. `tests/services/test_feedback_service_errors.py` (~300 lines, 8-10 tests)

### Enhanced Test Files
1. `tests/services/test_interview_service_coverage.py` (add 10-12 tests)
2. `tests/test_content_analyzer.py` (fix 12 failing tests)

### Total Estimated Addition
- **New Lines**: ~2,250 lines of test code
- **New Tests**: 75-85 tests
- **Expected Coverage Gain**: +8-10 percentage points

---

## Exclusions (DO NOT TEST)

Per project requirements:
- ❌ Auth token generation logic (covered in existing tests)
- ❌ Billing/Stripe integration internals (only webhook handling)
- ❌ Third-party API internals (mock boundaries only)
- ❌ Database connection management (framework-level)

---

## Commands for Validation

```bash
# Run all tests with coverage
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv run pytest --cov=app --cov-report=html --cov-report=term-missing -v

# Run specific test file
uv run pytest tests/middleware/test_security_headers.py -v

# Run only new tests
uv run pytest tests/api/test_coaching.py tests/middleware/test_security_headers.py -v

# Check coverage for specific module
uv run pytest --cov=app.middleware.security_headers --cov-report=term-missing

# Generate JSON coverage for analysis
uv run pytest --cov=app --cov-report=json --cov-report=html
```

---

## Dependencies Required

All dependencies already in pyproject.toml:
- pytest
- pytest-asyncio
- pytest-cov
- httpx
- sqlalchemy
- fastapi
- unittest.mock (stdlib)

---

## Risk Assessment

### Low Risk
- Middleware tests (isolated, no DB)
- Coaching API tests (mocked external service)

### Medium Risk
- Users API tests (requires DB, careful with fixtures)
- ContentAnalyzer fix (API interface changes)

### High Risk
- Subscriptions tests (Stripe webhook simulation)
- Interviews tests (complex state management)

### Mitigation
- Test in isolated transaction per test
- Use proper mocking for external services
- Follow existing patterns from conftest.py
- Run tests incrementally to catch issues early

---

## Next Steps

1. **Human Review**: Approve this plan
2. **Agent Assignment**: Delegate to Guardian (QA specialist) for implementation
3. **Execution**: Follow phases 1-4
4. **Validation**: Generate coverage report at each phase
5. **Report**: Final test expansion report with metrics

---

## Report Output Location

Final report will be written to:
`/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/.forge/test-expansion-report.md`

---

**Plan Created**: 2026-02-02
**Status**: Ready for execution
**Estimated Timeline**: 6 days
**Expected Coverage**: 67% → 75%+
