# Testing Quick Reference - Interview Simulator

**Current Coverage**: 64.2% (3,639/5,664 statements)
**Test Suite**: 820 passing tests
**Last Updated**: 2026-02-20

## Quick Commands

### Run All Tests
```bash
cd /Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/backend
.venv-test/bin/pytest -v
```

### Run Tests with Coverage
```bash
cd /Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/backend
.venv-test/bin/pytest --cov=app --cov-report=html --cov-report=term-missing
```

### View HTML Coverage Report
```bash
open /Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/backend/htmlcov/index.html
```

### Run Specific Test Categories
```bash
# Service tests
.venv-test/bin/pytest tests/services/ -v

# API tests
.venv-test/bin/pytest tests/api/ -v

# Security tests
.venv-test/bin/pytest tests/test_security*.py -v

# Auth tests
.venv-test/bin/pytest tests/test_auth*.py -v

# Subscription tests
.venv-test/bin/pytest tests/test_subscriptions*.py -v
```

### Run Single Test File
```bash
.venv-test/bin/pytest tests/services/test_interview_service.py -v
```

### Run with Coverage for Specific Module
```bash
.venv-test/bin/pytest tests/api/test_subscriptions.py \
  --cov=app/api/subscriptions \
  --cov-report=term-missing
```

### Check Coverage Percentage
```bash
cd /Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/backend
.venv-test/bin/python -c "
import json
data = json.load(open('coverage.json'))
pct = data['totals']['percent_covered']
print(f'Coverage: {pct:.1f}%')
print('✓ Above 60%' if pct >= 60 else '✗ Below 60%')
"
```

## Coverage Breakdown

### Excellent (90-100%)
- ✅ Interview Service: 100%
- ✅ Audio Service: 100%
- ✅ Video Service: 100%
- ✅ Email Service: 100%
- ✅ Content Sanitization: 100%
- ✅ Scoring Service: 100%
- ✅ Security Headers: 100%
- ✅ All Models: 93-100%
- ✅ Rate Limiting: 95%

### Good (70-89%)
- ✅ Feedback Service: 73%
- ✅ Auth Rate Limit: 83%
- ✅ API Key Model: 88%

### Needs Improvement (<60%)
- ⚠️ Subscriptions API: 22%
- ⚠️ Users API: 24%
- ⚠️ Interviews API: 27%
- ⚠️ Feedback API: 30%
- ⚠️ Preparation API: 33%
- ⚠️ Auth API: 39%

## Test Environment Setup

### Python 3.12 Virtual Environment

The project uses a Python 3.12 virtual environment due to librosa/llvmlite dependencies:

```bash
# Location
/Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/backend/.venv-test

# Activate (if needed)
source .venv-test/bin/activate

# Verify Python version
.venv-test/bin/python --version  # Should show Python 3.12.x
```

### Dependencies

All test dependencies are installed:
- pytest 9.0.2
- pytest-cov 7.0.0
- pytest-asyncio 1.3.0
- httpx (for API testing)
- All project dependencies

## Common Issues

### Issue: "ModuleNotFoundError"
**Solution**: Ensure you're using `.venv-test/bin/pytest`, not system pytest

### Issue: "Database not available" (850 skipped tests)
**Impact**: Integration tests skip when DB not running
**Solution**: For full coverage, run with Docker Compose database:
```bash
docker compose up -d postgres
# Then run tests
```

### Issue: CLI tests failing
**Impact**: 31 CLI tests fail (0% coverage on CLI)
**Solution**: Low priority (developer tooling), can be fixed with:
```bash
.venv-test/bin/pip install -e .
```

## Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Coverage Analysis | Detailed breakdown | `/Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/COVERAGE_ANALYSIS_2026-02-20.md` |
| Test Improvement Plan | Roadmap to 70% | `/Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/TEST_IMPROVEMENT_PLAN.md` |
| Task Summary | TEST-COV-60 results | `/Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/TEST-COV-60-SUMMARY.md` |
| This Guide | Quick reference | `/Users/moltbot/work/FORGE/codeswiftr-com/interview-simulator/TESTING_QUICK_REFERENCE.md` |

## Next Steps

### To Maintain 64% Coverage
- Run tests before committing: `.venv-test/bin/pytest --cov=app`
- Ensure coverage doesn't drop below 60%
- Add tests for new features

### To Reach 70% Coverage
Follow the Test Improvement Plan:
1. Fix failing tests (2h)
2. Auth API tests (2-3h)
3. Subscription API tests (2-3h)
4. Interview API tests (1-2h)

**Total effort**: 7-10 hours

## CI/CD Integration

For continuous integration, add to GitHub Actions:

```yaml
- name: Run Tests with Coverage
  run: |
    cd backend
    .venv-test/bin/pytest --cov=app --cov-report=xml --cov-fail-under=60

- name: Upload Coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

## Contact

For questions about test coverage or testing strategy:
- Guardian (QA Agent)
- See task: TEST-COV-60
- Date: 2026-02-20
