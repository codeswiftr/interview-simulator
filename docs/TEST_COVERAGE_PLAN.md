# Interview Simulator - Test Coverage Gap Analysis

**Date:** 2026-02-08  
**Coverage:** ~40% backend | 29 frontend tests (all passing)

---

## 1. Source Modules by Coverage

| Module | Coverage | Status |
|--------|----------|--------|
| **Services** | | |
| `interview_service.py` | HIGH | 21K test + edge cases |
| `video_service.py` | HIGH | 24K tests |
| `aggregation_service.py` | HIGH | 13K tests |
| `question_recommender.py` | HIGH | 14K tests |
| `share_service.py` | HIGH | 13K tests |
| `pdf_export_service.py` | HIGH | 14K tests |
| `email_service.py` | MEDIUM | 4K tests |
| `feedback_persistence.py` | MEDIUM | 9K tests |
| `scoring_service.py` | LOW | Basic only |
| `feedback_service.py` | LOW | Basic only |
| **API Endpoints (11 files)** | | |
| `auth.py` | MEDIUM | Inherited tests |
| All others | **NONE** | No dedicated tests |
| **Utilities** | | |
| `password_validation.py` | LOW | Unit tests |
| `validators.py` | NONE | No tests |
| `content_sanitizer.py` | NONE | No tests |
| **Middleware** | | |
| `security_headers.py` | MEDIUM | Tests |
| `rate_limit.py` | NONE | No tests |

---

## 2. Critical Untested Paths

**High Priority (Business Critical):**
| Path | Why |
|------|-----|
| Auth flows | Security, user data |
| Stripe webhook | Revenue, payments |
| Subscription upgrades | Revenue tracking |
| Interview CRUD | Core business |

**Medium Priority:**
| Path | Why |
|------|-----|
| Feedback submission | User engagement |
| Transcription API | Core feature |
| Question retrieval | User value |

---

## 3. Prioritized Test Plan

### Week 1: Core Business
1. `auth.py` - JWT, refresh, password reset
2. `interviews.py` - CRUD, state transitions
3. `stripe_webhook.py` - Payment events

### Week 2: Core Features
4. `feedback.py` - Submission, persistence
5. `transcription.py` - Async processing
6. `questions.py` - Retrieval, filtering

### Week 3: Revenue & Growth
7. `subscriptions.py` - Plan management
8. `coaching.py` - Tips generation
9. `upload.py` - File handling

### Week 4: Infrastructure
10. `rate_limit.py` - Abuse prevention
11. `validators.py` - Input validation

---

## 4. Test Patterns

```python
# Fixture (existing pattern)
@pytest.fixture
async def test_interview(db_session):
    return await create_test_interview(db_session)

# Async test
@pytest.mark.asyncio
async def test_create(db_session, auth_token):
    client = AsyncClient(app=app, auth=auth_token)
    response = await client.post("/api/interviews", json={...})
    assert response.status_code == 201

# Mocking
with patch("stripe.Customer.create") as mock:
    mock.return_value = {"id": "cus_test"}
    yield mock
```

---

## 5. Coverage Targets

| Target | Current | Goal |
|--------|---------|------|
| Services | ~70% | 90% |
| APIs | 0% | 80% |
| Overall | ~40% | 85% |

**Best pattern reference:** `test_interview_service.py`
