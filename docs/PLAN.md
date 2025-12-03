# Milestone: Fix Test Suite Regressions

## Status: Ready
## Target: Immediate (2-4 hours)

---

## Overview
The test suite has 9 failing tests after recent changes to the ContentAnalyzer (multi-provider support) and subscription webhook (Stripe API structure changes). These tests were written for the old implementation and need to be updated to match the current code.

## Success Criteria
- [ ] All 95 tests pass (currently 86 passing, 9 failing)
- [ ] Test coverage maintained at ≥69%
- [ ] No new regressions introduced

## Root Cause Analysis

### Issue 1: ContentAnalyzer Tests (8 failures)
**Problem**: Tests patch `analyzer.client.messages.create` but the refactored `ContentAnalyzer` now uses:
- `self.anthropic_client` (for Anthropic provider)
- `self.openrouter_client` (for OpenRouter provider)

**Tests affected**:
- `test_analyze_behavioral_question`
- `test_analyze_technical_question`
- `test_analyze_system_design_question`
- `test_analyze_handles_json_in_markdown`
- `test_analyze_handles_api_errors`
- `test_analyze_handles_malformed_json`
- `test_prompt_includes_star_instruction_for_behavioral`
- `test_prompt_excludes_star_instruction_for_technical`

**Fix**: Update patches to use `analyzer.anthropic_client.messages.create`

### Issue 2: Subscription Webhook Test (1 failure)
**Problem**: Test mocks `stripe.Subscription.retrieve()` but the new code accesses `subscription["items"]["data"][0]["current_period_end"]` (dict-like) instead of `subscription.current_period_end` (object attribute).

**Test affected**:
- `test_webhook_checkout_completed_upgrades_user`

**Fix**: Configure mock to return proper nested dict structure with `current_period_end` on subscription item

---

## Implementation Plan

### Phase 1: Fix ContentAnalyzer Tests
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Update mock patches from `analyzer.client` to `analyzer.anthropic_client` | 30m |
| 1.2 | Run content analyzer tests and verify all 8 pass | 10m |

**Changes Required** (tests/test_content_analyzer.py):
```python
# OLD (broken):
with patch.object(analyzer.client.messages, "create", new=AsyncMock(...)):

# NEW (fixed):
with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(...)):
```

**Checkpoint**: All `test_content_analyzer.py` tests pass (11/11)

### Phase 2: Fix Subscription Webhook Test
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Update mock subscription to return dict-like structure | 30m |
| 2.2 | Run subscription tests and verify all pass | 10m |

**Changes Required** (tests/test_subscriptions.py):
```python
# OLD (broken):
mock_subscription = MagicMock()
mock_subscription.status = "active"
mock_subscription.current_period_end = 1735689600
mock_subscription.items.data = [MagicMock(price=MagicMock(id="price_pro_monthly"))]

# NEW (fixed):
mock_subscription = {
    "status": "active",
    "items": {
        "data": [{
            "price": {"id": "price_pro_monthly"},
            "current_period_end": 1735689600,
        }]
    },
}
```

**Checkpoint**: All `test_subscriptions.py` tests pass (5/5)

### Phase 3: Verification
| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Run full test suite to ensure no regressions | 5m |
| 3.2 | Commit with conventional commit format | 5m |

**Checkpoint**: Full test suite passes (95/95)

---

## Testing Strategy
- **Unit Tests**: Run affected test files individually first
- **Full Suite**: Run complete pytest suite to catch regressions
- **Commands**:
  ```bash
  uv run pytest tests/test_content_analyzer.py -v
  uv run pytest tests/test_subscriptions.py -v
  uv run pytest -q  # Full suite
  ```

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Mock changes break other tests | Medium | Run full suite after each change |
| Provider logic differs between tests | Low | Ensure tests use default Anthropic provider |

## Files to Modify
1. `backend/tests/test_content_analyzer.py` - Update 8 patches
2. `backend/tests/test_subscriptions.py` - Update 1 mock structure

## References
- Content Analyzer: `backend/app/ai/content_analyzer.py:86-100` (new client structure)
- Subscription Handler: `backend/app/api/subscriptions.py:210-225` (new Stripe API access)
