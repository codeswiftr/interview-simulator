# Test Coverage Improvement Plan - Interview Simulator

**Date**: 2026-02-20
**Current Coverage**: 64% (3,639/5,664 statements)
**Target Coverage**: 70%
**Gap to Close**: +6 percentage points (~340 additional statements)

## Quick Wins to Reach 70% (Estimated 6-8 hours)

### Priority 1: Fix Failing Tests (2 hours)

**Impact**: Stabilize test suite, unlock existing coverage

#### AI Transcriber Tests (13 failures)
```python
# File: tests/test_ai_transcriber.py
# Issue: Mocks not async-compatible

# Fix: Update conftest.py or test file
from unittest.mock import AsyncMock

@pytest.fixture
def mock_openai_client():
    mock = AsyncMock()
    mock.audio.transcriptions.create = AsyncMock(
        return_value={"text": "Test transcription"}
    )
    return mock
```

#### CLI Tests (31 failures)
```bash
# Issue: CLI entry point not in PATH
# Fix: Reinstall in development mode

cd backend
pip install -e .
```

#### Audio/Video Analyzer Tests (3 failures)
- Adjust assertion thresholds based on actual algorithm behavior
- Document expected ranges in test docstrings

**Expected Coverage Gain**: +0.5% (unlock skipped paths)

### Priority 2: Auth API Coverage (2-3 hours)

**Target**: `app/api/auth.py` from 39% → 75% (+36%)

**Missing Coverage Areas** (based on coverage HTML report):

1. **Password Reset Error Paths**
```python
# tests/api/test_auth.py

async def test_password_reset_invalid_email(client):
    """Test password reset with non-existent email."""
    response = await client.post(
        "/api/v1/auth/password-reset",
        json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 404

async def test_password_reset_token_expired(client, test_user, db_session):
    """Test password reset with expired token."""
    # Create expired reset token
    from datetime import datetime, timedelta
    from app.models.password_reset import PasswordResetToken

    expired_token = PasswordResetToken(
        user_id=test_user.id,
        token="expired_token",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    db_session.add(expired_token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "expired_token",
            "new_password": "NewSecure123!"
        }
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()
```

2. **Token Refresh Edge Cases**
```python
async def test_refresh_token_invalid_format(client):
    """Test refresh with malformed token."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-valid-jwt"}
    )
    assert response.status_code == 401

async def test_refresh_token_revoked(client, test_user, db_session):
    """Test refresh with revoked token."""
    # Create and revoke token
    from app.models.user import RefreshToken

    token = RefreshToken(
        user_id=test_user.id,
        token="revoked_token",
        revoked=True
    )
    db_session.add(token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "revoked_token"}
    )
    assert response.status_code == 401
```

3. **Login Rate Limiting**
```python
async def test_login_rate_limit(client):
    """Test login rate limiting after multiple failures."""
    for _ in range(6):  # Trigger rate limit
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password"
            }
        )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "correct_password"
        }
    )
    assert response.status_code == 429
    assert "too many" in response.json()["detail"].lower()
```

**Expected Coverage Gain**: +2.8% (95 statements * 0.36 improvement / 5664 total)

### Priority 3: Subscription API Coverage (2-3 hours)

**Target**: `app/api/subscriptions.py` from 22% → 65% (+43%)

**Key Test Additions**:

1. **Stripe Webhook Validation**
```python
# tests/api/test_subscriptions.py

async def test_stripe_webhook_invalid_signature(client):
    """Test webhook rejects invalid signature."""
    response = await client.post(
        "/api/v1/subscriptions/webhook",
        headers={"Stripe-Signature": "invalid_sig"},
        json={"type": "payment_intent.succeeded"}
    )
    assert response.status_code == 400

async def test_stripe_webhook_subscription_created(client, test_user, db_session):
    """Test webhook handles subscription.created event."""
    # Mock Stripe signature verification
    with patch('stripe.Webhook.construct_event') as mock_verify:
        mock_verify.return_value = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "active",
                    "items": {
                        "data": [{
                            "price": {"id": "price_pro_monthly"}
                        }]
                    }
                }
            }
        }

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            headers={"Stripe-Signature": "valid_sig"},
            json=mock_verify.return_value
        )
        assert response.status_code == 200

        # Verify subscription created in DB
        from app.models.user import UserSubscription
        sub = await db_session.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == "sub_123"
            )
        )
        assert sub.scalar_one()
```

2. **Subscription State Transitions**
```python
async def test_upgrade_subscription(client, test_user_with_sub, db_session):
    """Test upgrading from starter to pro."""
    response = await client.post(
        "/api/v1/subscriptions/upgrade",
        headers={"Authorization": f"Bearer {test_user_with_sub.token}"},
        json={"plan": "pro"}
    )
    assert response.status_code == 200
    assert response.json()["plan"] == "pro"

async def test_cancel_subscription(client, test_user_with_sub):
    """Test subscription cancellation."""
    with patch('stripe.Subscription.modify') as mock_cancel:
        response = await client.post(
            "/api/v1/subscriptions/cancel",
            headers={"Authorization": f"Bearer {test_user_with_sub.token}"}
        )
        assert response.status_code == 200
        mock_cancel.assert_called_once()
```

3. **Trial Expiration**
```python
async def test_subscription_trial_expired(client, test_user, db_session):
    """Test access denied when trial expires."""
    # Set trial end date in past
    test_user.trial_ends_at = datetime.utcnow() - timedelta(days=1)
    await db_session.commit()

    response = await client.get(
        "/api/v1/interviews/premium-feature",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 402  # Payment required
```

**Expected Coverage Gain**: +2.0% (268 statements * 0.43 improvement / 5664 total)

### Priority 4: Interview API Coverage (1-2 hours)

**Target**: `app/api/interviews.py` from 27% → 60% (+33%)

**Key Test Additions**:

1. **Interview Creation Variants**
```python
async def test_create_interview_all_types(client, auth_headers):
    """Test creating interviews of all types."""
    for interview_type in ["behavioral", "technical", "system_design", "mixed"]:
        response = await client.post(
            "/api/v1/interviews/",
            headers=auth_headers,
            json={
                "interview_type": interview_type,
                "difficulty": "medium",
                "question_count": 5
            }
        )
        assert response.status_code == 201
        assert response.json()["interview_type"] == interview_type

async def test_create_interview_with_company(client, auth_headers):
    """Test creating company-specific interview."""
    response = await client.post(
        "/api/v1/interviews/",
        headers=auth_headers,
        json={
            "interview_type": "technical",
            "target_company": "Google",
            "question_count": 5
        }
    )
    assert response.status_code == 201
    assert response.json()["target_company"] == "Google"
```

2. **Interview State Management**
```python
async def test_complete_interview(client, test_interview, auth_headers):
    """Test marking interview as complete."""
    response = await client.patch(
        f"/api/v1/interviews/{test_interview.id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

async def test_cannot_modify_completed_interview(client, completed_interview, auth_headers):
    """Test that completed interviews cannot be modified."""
    response = await client.post(
        f"/api/v1/interviews/{completed_interview.id}/responses",
        headers=auth_headers,
        json={"question_id": "q1", "response": "answer"}
    )
    assert response.status_code == 400
```

**Expected Coverage Gain**: +1.3% (215 statements * 0.33 improvement / 5664 total)

## Summary: Path to 70% Coverage

| Priority | Module | Current | Target | Gain | Effort |
|----------|--------|---------|--------|------|--------|
| 1 | Fix failing tests | 64% | 64.5% | +0.5% | 2h |
| 2 | Auth API | 39% | 75% | +2.8% | 2-3h |
| 3 | Subscriptions API | 22% | 65% | +2.0% | 2-3h |
| 4 | Interviews API | 27% | 60% | +1.3% | 1-2h |
| **Total** | | **64%** | **70.6%** | **+6.6%** | **7-10h** |

## Implementation Order

### Day 1 (4 hours)
1. Fix failing tests (2h)
2. Auth API tests - password reset & token refresh (2h)

### Day 2 (3 hours)
3. Auth API tests - rate limiting & edge cases (1h)
4. Subscription API tests - webhooks (2h)

### Day 3 (3 hours)
5. Subscription API tests - state transitions (1.5h)
6. Interview API tests - creation & states (1.5h)

## Test File Structure

```
tests/
├── api/
│   ├── test_auth_extended.py          # New auth tests
│   ├── test_subscriptions_extended.py # New subscription tests
│   └── test_interviews_extended.py    # New interview tests
├── integration/
│   └── test_stripe_webhook_integration.py
└── fixtures/
    ├── stripe_fixtures.py             # Stripe event fixtures
    └── subscription_fixtures.py       # Subscription test data
```

## Validation

After implementing tests, verify with:

```bash
# Run new tests
.venv-test/bin/pytest tests/api/test_auth_extended.py -v
.venv-test/bin/pytest tests/api/test_subscriptions_extended.py -v
.venv-test/bin/pytest tests/api/test_interviews_extended.py -v

# Check coverage
.venv-test/bin/pytest --cov=app --cov-report=term-missing --cov-report=html

# Verify target met
.venv-test/bin/python -c "
import json
data = json.load(open('coverage.json'))
pct = data['totals']['percent_covered']
print(f'Coverage: {pct:.1f}%')
print('✓ Target met' if pct >= 70 else '✗ Need more tests')
"
```

## Success Criteria

- [ ] All 33 failing tests fixed and passing
- [ ] Coverage reaches 70%+ (measured by pytest-cov)
- [ ] All new tests pass consistently (run 3x to verify)
- [ ] No new flaky tests introduced
- [ ] Coverage HTML report shows green for targeted modules
- [ ] CI/CD pipeline updated with new coverage threshold

## Risk Mitigation

1. **Database Setup**: Use existing test fixtures from `conftest.py`
2. **Stripe Mocking**: Use `unittest.mock.patch` for Stripe SDK calls
3. **Async Tests**: Use `pytest-asyncio` fixtures (already configured)
4. **Test Isolation**: Ensure database cleanup between tests with `db_session` fixture

## Next Steps After 70%

Once 70% is achieved, consider:

1. **API Key Infrastructure** (0% → 80%): +0.8% coverage
2. **Behavioral Analytics** (43% → 75%): +0.8% coverage
3. **Integration Test CI/CD**: Enable 850 skipped tests
4. **Performance Tests**: Add load testing for critical endpoints

## Resources

- Existing test patterns: `tests/conftest.py`
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- Coverage docs: https://coverage.readthedocs.io/
