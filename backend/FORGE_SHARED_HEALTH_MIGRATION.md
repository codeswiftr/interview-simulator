# Health Check Migration Assessment

**Date:** February 8, 2026  
**File:** `app/api/health.py`  
**forge-shared Module:** `forge_shared.health`

---

## Overview

This document assesses the migration path from the current health check endpoints in `app/api/health.py` to using `forge_shared.health.create_health_router()`.

---

## Current Implementation

**File:** `app/api/health.py` (164 lines)

### Current Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Basic health check | `{"status": "healthy"}` |
| `GET /health/ready` | Readiness probe with dependencies | `{"status": "ready", "database": bool, "redis": bool, "ai_services": bool}` |
| `GET /health/details` | Detailed health with timing | Full status including response times |

### Current Features

- Database connectivity check
- Redis connectivity check
- AI service configuration check (OpenAI, Anthropic, OpenRouter)
- Response timing for each dependency
- Detailed error logging
- Graceful degradation (Redis/AI optional, DB critical)
- Version and environment information in `/health/details`

---

## forge_shared.health.create_health_router()

**File:** `forge_shared/health/router.py` (182 lines)

### forge_shared Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Comprehensive health with check results |
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Kubernetes readiness probe |

### forge_shared Features

- Standardized `HealthResponse` with `HealthStatus` enum
- `HealthCheck` class for custom check functions
- Automatic latency measurement
- Async and sync check function support
- Configurable check list
- `HealthStatus.HEALTHY`, `DEGRADED`, `UNHEALTHY` states

---

## Comparison Matrix

| Feature | Current Implementation | forge_shared |
|---------|----------------------|--------------|
| `/health` endpoint | ✅ Basic response | ✅ Full response with checks |
| `/health/live` | ❌ Missing | ✅ Kubernetes probe |
| `/health/ready` | ✅ With dependencies | ✅ With dependencies |
| `/health/details` | ✅ Detailed timing | ❌ Not included |
| Database check | ✅ Async check | ✅ Custom check function |
| Redis check | ✅ Async check | ✅ Custom check function |
| AI services check | ✅ Configuration check | ❌ Not included |
| Response timing | ✅ In `/health/details` | ✅ Automatic latency_ms |
| Version in response | ✅ In `/health/details` | ✅ In `/health` |
| Status enum | ❌ String-based | ✅ `HealthStatus` enum |
| Custom checks | N/A | ✅ Via `HealthCheck` class |

---

## Migration Plan

### Option 1: Full Migration to forge_shared

Replace current `app/api/health.py` with:

```python
from forge_shared.health import create_health_router, HealthCheck
from app.db import check_db_connection

async def check_database():
    db_ok = await check_db_connection()
    return db_ok, 5.0, "Database connected" if db_ok else "Database failed"

async def check_redis():
    # Implementation from current health.py
    ...

async def check_ai():
    # Check AI service keys are configured
    ...

router = create_health_router(
    name="interview-simulator",
    version="0.1.0",
    checks=[
        HealthCheck("database", check_database),
        HealthCheck("redis", check_redis),
        HealthCheck("ai_services", check_ai),
    ],
    include_live=True,
    include_ready=True,
)
```

**Benefits:**
- Standardized across FORGE portfolio
- Kubernetes-native (liveness/readiness probes)
- Automatic latency tracking
- Consistent response format

**Drawbacks:**
- Loses `/health/details` endpoint (detailed timing)
- Loses current response format (breaking change for monitoring)
- AI services check would need custom implementation
- More complex to add new checks

### Option 2: Add forge_shared Alongside Current

Keep current endpoints and add forge_shared router:

```python
# Current endpoints remain
from app.api.health import router as health_router

# Add forge_shared endpoints at different prefix
from forge_shared.health import create_health_router
forge_health_router = create_health_router(
    name="interview-simulator",
    version="0.1.0",
)

app.include_router(health_router, tags=["Health"])
app.include_router(forge_health_router, prefix="/forge")
```

**Benefits:**
- No breaking changes
- Testing forge_shared in parallel
- Maintains current detailed endpoints

**Drawbacks:**
- Duplicate health endpoints
- Confusion about which to use
- Maintenance overhead

### Option 3: Minimal Integration (Recommended)

Create a wrapper that uses forge_shared patterns but keeps current functionality:

```python
from forge_shared.health import HealthStatus, HealthCheck

# Keep current implementation but add HealthStatus enum
# Use forge_shared response format for /health
# Keep /health/ready and /health/details as-is

from forge_shared.health import create_health_router

# Create a new router using forge_shared patterns
router = create_health_router(
    name="interview-simulator",
    version="0.1.0",
    checks=[
        HealthCheck("database", lambda: (True, 5.0, None)),  # Placeholder
    ],
    include_live=False,  # Use existing /health
    include_ready=False,  # Use existing /health/ready
)

# Include both routers
app.include_router(health_router, tags=["Health"])
app.include_router(router)  # For standardized format
```

---

## Decision: MINIMAL INTEGRATION

**Recommendation:** Do NOT fully migrate health checks to forge_shared

### Rationale

1. **Current Implementation is Comprehensive**: The current `/health/details` endpoint provides more information than forge_shared's `/health` (response times, AI provider details).

2. **Kubernetes Compatibility**: Current `/health/ready` already serves as Kubernetes readiness probe.

3. **Breaking Changes**: Full migration would change response formats, potentially breaking:
   - Monitoring dashboards
   - Alerting rules
   - External uptime monitors

4. **Low Value**: forge_shared health router provides standardization but Interview Simulator's current implementation is more feature-rich.

### When to Revisit

Consider migration if:
- FORGE requires standardized health format across all services
- Kubernetes integration requires forge_shared-specific probes
- Monitoring simplification becomes a priority

---

## Effort Estimate

| Task | Effort | Priority |
|------|--------|----------|
| Assess health migration | 1 hour | COMPLETED |
| Document migration plan | 1 hour | COMPLETED |
| **Full migration** | **4-6 hours** | **NOT RECOMMENDED** |
| **Parallel endpoints** | **2-3 hours** | **LOW PRIORITY** |

---

## Related Documentation

- `FORGE_SHARED_AUDIT.md` - Overall adoption status
- `FORGE_SHARED_CONFIG_MIGRATION.md` - Config migration assessment
- `forge_shared/health/router.py` - Health router source
- `forge_shared/health/__init__.py` - Health module exports
