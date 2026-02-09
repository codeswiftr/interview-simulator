# Config Migration Assessment

**Date:** February 8, 2026  
**File:** `app/config.py`  
**forge-shared Module:** `forge_shared.config`

---

## Overview

This document assesses the migration path from the current `app/config.py` (custom `Settings` class extending `pydantic_settings.BaseSettings`) to using `forge_shared.config.BaseConfig`.

---

## Current Implementation

**File:** `app/config.py` (198 lines)

The current `Settings` class provides:
- Environment variable loading via `.env`
- Application metadata (name, debug, environment)
- Database and Redis configuration
- Security settings (secret key, JWT expire times)
- AI service API keys (Anthropic, OpenAI, OpenRouter, Groq)
- Stripe billing configuration
- CORS origins with development/production logic
- Storage configuration
- Error monitoring (Sentry)
- Email/SMTP and Resend configuration
- PostHog analytics configuration
- Production validation (`validate_for_production()`)
- Custom `effective_cors_origins` property
- Custom `async_database_url` property

---

## forge_shared.config.BaseConfig

**File:** `forge_shared/config/base.py` (158 lines)

`BaseConfig` provides:
- `app_name`, `app_version`, `environment`, `debug`
- `host`, `port`
- `secret_key`, `jwt_algorithm`, `jwt_expire_minutes`
- `database_url`, `database_pool_size`
- `redis_url`
- `posthog_api_key`, `posthog_host`
- `log_level`, `log_format`
- `is_production`, `is_development` properties
- `get_database_url()` method with async driver conversion

---

## Comparison Matrix

| Feature | Current `Settings` | forge_shared `BaseConfig` |
|---------|-------------------|---------------------------|
| Environment loading | ✅ `.env` support | ✅ `.env` support |
| Case sensitive config | ✅ `case_sensitive=False` | ✅ `case_sensitive=False` |
| Extra fields | `extra="ignore"` | `extra="ignore"` |
| App name | ✅ Custom | ✅ Default `"forge-app"` |
| Debug mode | ✅ Custom | ✅ Default `False` |
| Environment | ✅ Custom | ✅ Default `"development"` |
| Secret key | ✅ Custom | ✅ Default `"change-me"` |
| JWT algorithm | ❌ Missing (hardcoded `"HS256"`) | ✅ Included |
| JWT expire | ✅ Custom | ✅ Default 30 min |
| Database URL | ✅ Custom | ✅ Included |
| Redis URL | ✅ Custom | ✅ Default `"redis://localhost:6379"` |
| PostHog API key | ✅ Custom | ✅ Included |
| PostHog host | ✅ Custom | ✅ Default |
| CORS origins | ✅ Extensive custom logic | ❌ Not included |
| AI providers | ✅ Anthropic, OpenAI, OpenRouter, Groq | ❌ Not included |
| Stripe config | ✅ Secret key, webhook secret, price IDs | ❌ Not included |
| Email/SMTP | ✅ SMTP and Resend support | ❌ Not included |
| Storage bucket | ✅ Storage bucket/URL | ❌ Not included |
| Sentry DSN | ✅ Error monitoring | ❌ Not included |
| Production validation | ✅ Custom `validate_for_production()` | ❌ Not included |

---

## Migration Plan

### Fields to Keep (Cannot Migrate)

These fields are **Interview-Simulator specific** and have no forge-shared equivalent:

| Field | Reason |
|-------|--------|
| `anthropic_api_key` | AI provider key (Interview Simulator specific) |
| `openai_api_key` | AI provider key |
| `openrouter_api_key` | AI provider key |
| `groq_api_key` | AI provider key |
| `transcription_provider` | Interview Simulator feature flag |
| `content_analysis_provider` | Interview Simulator feature flag |
| `stripe_secret_key` | Stripe integration |
| `stripe_webhook_secret` | Stripe webhook verification |
| `stripe_price_id_pro_monthly` | Product pricing |
| `stripe_price_id_pro_annual` | Product pricing |
| `stripe_price_id_team_monthly` | Product pricing |
| `stripe_price_id_team_annual` | Product pricing |
| `stripe_trial_days` | Trial configuration |
| `cors_origins` | Domain-specific CORS |
| `_dev_cors_origins` | Development CORS origins |
| `effective_cors_origins` | Custom property (complex logic) |
| `storage_bucket` | S3/storage bucket name |
| `storage_url` | Storage URL |
| `sentry_dsn` | Error monitoring (forge-shared doesn't validate format) |
| `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password` | SMTP configuration |
| `smtp_from_email` | SMTP sender |
| `resend_api_key` | Resend email provider |
| `resend_from_email`, `resend_from_name` | Resend configuration |
| `frontend_url` | Frontend URL for email links |
| `video_features_enabled` | Feature flag |

### Fields That Can Migrate (Replace with forge_shared)

| Current Field | forge_shared Equivalent | Action |
|---------------|------------------------|--------|
| `app_name` | `BaseConfig.app_name` | ✅ Can use forge-shared default or override |
| `environment` | `BaseConfig.environment` | ✅ Can use forge-shared default or override |
| `debug` | `BaseConfig.debug` | ✅ Can use forge-shared default or override |
| `secret_key` | `BaseConfig.secret_key` | ✅ Can use forge-shared default or override |
| `access_token_expire_minutes` | `BaseConfig.jwt_expire_minutes` | ⚠️ Rename field |
| `refresh_token_expire_days` | ❌ No equivalent | Keep custom |
| `database_url` | `BaseConfig.database_url` | ✅ Can use forge-shared |
| `database_pool_size` | `BaseConfig.database_pool_size` | ⚠️ Add if needed |
| `redis_url` | `BaseConfig.redis_url` | ✅ Can use forge-shared |
| `posthog_api_key` | `BaseConfig.posthog_api_key` | ✅ Can use forge-shared |
| `posthog_host` | `BaseConfig.posthog_host` | ✅ Can use forge-shared |
| `async_database_url` property | `BaseConfig.get_database_url()` | ⚠️ Different API |
| `validate_for_production()` | ❌ No equivalent | Keep custom |

### Recommended Migration Approach

**Option 1: Minimal Change (Recommended)**
```python
# Keep Settings extending BaseSettings
# No migration needed - current implementation works well
# forge_shared adds minimal value for config
```

**Option 2: Partial Migration**
```python
from forge_shared.config import BaseConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseConfig, BaseSettings):
    # Interview Simulator-specific fields only
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    # ... other AI/Stripe/email fields
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
```

**Risk of Option 2:**
- `BaseConfig` inherits from `BaseSettings` - potential method resolution order (MRO) issues
- Duplicate fields between BaseConfig and custom Settings
- Complex property overrides (`effective_cors_origins`)

---

## Decision: SKIP MIGRATION

**Recommendation:** Do NOT migrate config.py to forge_shared.config

### Rationale

1. **Low Value Add**: forge_shared's `BaseConfig` provides generic defaults that Interview Simulator already has or needs to override.

2. **High Complexity**: Migration requires careful field mapping and potential MRO issues with pydantic.

3. **Works Well**: Current `Settings` class is well-designed with:
   - Comprehensive production validation
   - Feature flags (video features)
   - Complex CORS logic (dev/prod separation)
   - AI provider flexibility
   - Stripe integration

4. **No Breaking Changes Needed**: The config system works reliably in production.

### When to Revisit

Consider migration if:
- forge_shared adds comprehensive Stripe/billing config
- forge_shared adds AI provider configuration
- New FORGE-wide feature requires shared config patterns
- Standardization becomes critical across many projects

---

## Effort Estimate

| Task | Effort | Priority |
|------|--------|----------|
| Assess config migration | 2 hours | COMPLETED |
| Document migration plan | 1 hour | COMPLETED |
| **Implement migration** | **4-6 hours** | **NOT RECOMMENDED** |

---

## Related Documentation

- `FORGE_SHARED_AUDIT.md` - Overall adoption status
- `FORGE_SHARED_HEALTH_MIGRATION.md` - Health check migration
- `forge_shared/config/base.py` - BaseConfig source
- `forge_shared/config/domain.py` - DomainConfig source
