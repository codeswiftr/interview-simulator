# Sentry Configuration - Interview Simulator

**Purpose**: Quick reference for Sentry setup on deployment day.

---

## Environment Variables

Add to Railway environment variables:

```bash
# Required
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# Should already be set
ENVIRONMENT=production
DEBUG=false
```

---

## Current Integration

**Status**: ✅ Sentry SDK installed (`sentry-sdk[fastapi]>=2.48.0`)

**Implementation**: `app/main.py` lines 101-127

**Init function**: `init_error_monitoring()`

**Called from**: `lifespan()` startup (line 145)

---

## Integrations Configured

- `FastApiIntegration()` - Automatic endpoint tracking
- `SqlalchemyIntegration()` - Database query monitoring

---

## Sample Rate

```python
traces_sample_rate=0.1  # 10% of transactions
```

---

## Critical Events to Monitor

1. **Payment Processing**
   - Stripe webhook failures
   - Payment intent errors
   - Subscription mismatches

2. **AI Services**
   - OpenAI/Anthropic timeouts
   - Transcription errors (Whisper)
   - Feedback generation failures
   - Rate limiting

3. **Database**
   - Connection pool exhaustion
   - Query timeouts

4. **Interview Sessions**
   - Audio upload failures
   - Transcription processing errors
   - Feedback generation timeouts

---

## Critical Endpoints

Monitor performance for:
- `/api/v1/transcription/transcribe` (LLM-dependent)
- `/api/v1/feedback/generate` (LLM-dependent)
- `/api/v1/interviews/{id}/complete` (critical path)

---

## Testing After Deployment

1. Check Railway logs for: `"Sentry error monitoring initialized"`
2. Trigger test error (create in admin panel)
3. Verify event appears in Sentry dashboard
4. Check environment tag = `production`

---

## Alert Recommendations

**Immediate (Slack/Email)**:
- Stripe webhook failures
- Database connection loss
- LLM quota exhausted
- Audio upload failures

**Daily Digest**:
- Individual API timeouts
- Rate limit hits

---

**See also**: `/Users/bogdan/work/FORGE/docs/SENTRY_SETUP_GUIDE.md`
