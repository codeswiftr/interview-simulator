# Coverage Improvement Quick Start

## What Was Created

**3 new comprehensive test files** with **85+ test cases** targeting coverage gaps in:
- `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend/app/services/interview_service.py` (18% → 50%+ target)
- `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend/app/services/video_service.py` (46% → 70%+ target)

## New Test Files

1. **`backend/tests/test_interview_service_edge_cases.py`** (28 tests)
   - Mixed interview types, company filtering, difficulty variations
   - Error message formatting, inactive question filtering

2. **`backend/tests/test_video_service_edge_cases.py`** (33 tests)
   - Video file handling, metric value ranges, path variations
   - Processing status states, decimal precision

3. **`backend/tests/test_interview_state_transitions.py`** (24 tests)
   - Full interview lifecycle, progressive question availability
   - Sequential ordering, randomization verification

## Quick Run Commands

### Run All New Tests
```bash
cd backend
uv run pytest tests/test_interview_service_edge_cases.py \
             tests/test_interview_state_transitions.py \
             tests/test_video_service_edge_cases.py -v
```

### Run with Coverage Report
```bash
cd backend
uv run pytest tests/ \
    --cov=app/services/interview_service \
    --cov=app/services/video_service \
    --cov-report=html \
    --cov-report=term-missing
```

### View Coverage Report
```bash
cd backend
open htmlcov/index.html
```

### Use Verification Script
```bash
cd backend
./scripts/verify_coverage.sh
```

## What to Expect

### Test Execution Time
- Each test file: ~10-30 seconds
- Full coverage run: ~2-3 minutes
- Total new tests: **85+**

### Coverage Improvements

**Before:**
- `interview_service.py`: 18% line coverage
- `video_service.py`: 46% line coverage

**After (Expected):**
- `interview_service.py`: **50%+** line coverage (+32 points)
- `video_service.py`: **70%+** line coverage (+24 points)

### Test Success Criteria
All tests should PASS. If any fail:
1. Check database is running: `docker compose up -d`
2. Run migrations: `uv run alembic upgrade head`
3. Verify test database: Set `TEST_DATABASE_URL` env var

## File Locations

```
interview-simulator/
├── backend/
│   ├── tests/
│   │   ├── test_interview_service_edge_cases.py      [NEW] 28 tests
│   │   ├── test_interview_state_transitions.py       [NEW] 24 tests
│   │   └── test_video_service_edge_cases.py          [NEW] 33 tests
│   ├── scripts/
│   │   └── verify_coverage.sh                        [NEW] Verification script
│   └── htmlcov/                                       Coverage report output
└── .forge/
    ├── coverage-improvement-report.md                 [NEW] Full analysis
    └── COVERAGE_QUICK_START.md                        [NEW] This file
```

## Key Test Scenarios

### Interview Service
- ✓ Mixed interview types (behavioral + technical + system design)
- ✓ Company-specific filtering (case-insensitive)
- ✓ Difficulty variations (easy, medium, hard, mixed, none)
- ✓ Fallback to general pool when company questions insufficient
- ✓ Error handling for insufficient questions
- ✓ Sequential question ordering
- ✓ Inactive question exclusion
- ✓ Time limit inheritance
- ✓ Specific question assignment

### Video Service
- ✓ Video file existence validation
- ✓ Path handling (spaces, relative, absolute)
- ✓ File format variations (.mp4, .webm)
- ✓ Metric value ranges (0.0 to 1.0, zero counts, max counts)
- ✓ Duplicate feedback prevention
- ✓ Processing status states (PENDING, FAILED, COMPLETED)
- ✓ Decimal precision preservation
- ✓ Multiple responses per session
- ✓ Response validation

## Troubleshooting

### Database Connection Error
```bash
# Start PostgreSQL
docker compose up -d

# Verify database
psql -h localhost -U postgres -d interview_simulator
```

### Import Errors
```bash
# Sync dependencies
cd backend
uv sync
```

### Coverage Not Showing
```bash
# Ensure pytest-cov is installed
uv pip install pytest-cov

# Run with verbose output
uv run pytest --cov=app/services --cov-report=term-missing -v
```

## Next Steps

1. **Run verification script:**
   ```bash
   cd backend && ./scripts/verify_coverage.sh
   ```

2. **Review coverage report:**
   - Open `backend/htmlcov/index.html`
   - Check highlighted lines for remaining gaps

3. **Integrate into CI/CD:**
   - Add coverage threshold checks
   - Fail builds if coverage drops below 50%

4. **Maintain coverage:**
   - Update tests when service logic changes
   - Add tests for new features before merging

## Success Metrics

- [x] 85+ new test cases created
- [ ] All tests passing
- [ ] interview_service.py coverage ≥ 50%
- [ ] video_service.py coverage ≥ 70%
- [ ] No decrease in coverage for other modules
- [ ] HTML coverage report generated

## Documentation

- **Full Report:** `.forge/coverage-improvement-report.md`
- **Test Patterns:** See existing tests in `tests/conftest.py`
- **Service Code:**
  - `app/services/interview_service.py`
  - `app/services/video_service.py`

---

**Status:** Tests created, ready for verification
**Total Lines Added:** ~1,500 lines of test code
**Expected Coverage Gain:** +56 percentage points combined
