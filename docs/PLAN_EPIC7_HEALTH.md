# Detailed Plan: Production Health & Observability

## Overview
Implement real health checks that validate actual database, Redis, and AI service connectivity. Replace stubbed TODOs with working implementations to enable production deployments to detect failures.

## Scope

**In Scope**:
- Implement actual database connectivity check in `/health/ready`
- Implement actual Redis connectivity check in `/health/ready`
- Add startup validation (connection pooling initialization)
- Add graceful shutdown (connection cleanup)
- Return proper HTTP status codes (503 on failure)

**Explicitly Out of Scope**:
- Sentry integration (already exists, optional)
- Performance metrics/APM
- Distributed tracing
- AI model warm-up (external APIs, not needed)

---

## Files to Modify

### `backend/app/api/health.py`
**Purpose**: Fix the `/health/ready` endpoint to perform actual connectivity checks

| Function | Change | Description |
|----------|--------|-------------|
| `check_database() -> bool` | ADD | Execute `SELECT 1` query to verify DB connectivity |
| `check_redis() -> bool` | ADD | Execute `PING` command to verify Redis connectivity |
| `check_ai_services() -> dict` | ADD | Verify API keys are present (no actual API calls) |
| `readiness_check() -> dict` | MODIFY | Call actual check functions, return 503 on critical failure |

### `backend/app/main.py`
**Purpose**: Implement startup initialization and graceful shutdown

| Function | Change | Description |
|----------|--------|-------------|
| `init_database_pool() -> bool` | ADD | Verify database connection pool is ready |
| `init_redis_connection() -> redis.Redis | None` | ADD | Create and verify Redis connection |
| `close_connections() -> None` | ADD | Gracefully close database and Redis connections |
| `lifespan()` | MODIFY | Call init functions on startup, cleanup on shutdown |

### `backend/app/db.py`
**Purpose**: Add health check helper function

| Function | Change | Description |
|----------|--------|-------------|
| `check_db_connection() -> bool` | ADD | Execute test query, return True/False |

---

## Tests to Write

### `backend/tests/test_health.py` (extend existing)

| Test Name | Behavior Verified |
|-----------|-------------------|
| `test_readiness_check_returns_actual_db_status` | `/health/ready` shows real DB status |
| `test_readiness_check_returns_actual_redis_status` | `/health/ready` shows real Redis status |
| `test_readiness_returns_503_when_db_down` | Returns HTTP 503 when database unreachable |
| `test_health_ready_includes_all_components` | Response includes database, redis, ai_services keys |

### `backend/tests/test_startup.py` (new file)

| Test Name | Behavior Verified |
|-----------|-------------------|
| `test_database_pool_initializes_on_startup` | DB pool created during lifespan startup |
| `test_startup_logs_connection_status` | Startup logs show connection results |
| `test_shutdown_closes_connections_gracefully` | Connections closed on app shutdown |

---

## Implementation Order

1. **Add database check helper** (`backend/app/db.py`)
   - Add `check_db_connection()` function
   - Simple SELECT 1 with error handling

2. **Write health check tests** (`backend/tests/test_health.py`)
   - TDD: Add tests for real connectivity checks
   - Tests should pass with current implementation (green)

3. **Implement real health checks** (`backend/app/api/health.py`)
   - Replace TODOs with actual `check_database()`, `check_redis()` calls
   - Return 503 status code when critical services down

4. **Add startup/shutdown logic** (`backend/app/main.py`)
   - Implement `init_database_pool()` and `init_redis_connection()`
   - Call from lifespan context manager
   - Add `close_connections()` for shutdown

5. **Write startup tests** (`backend/tests/test_startup.py`)
   - Verify initialization happens on startup
   - Verify cleanup happens on shutdown

6. **Integration testing**
   - Run full test suite
   - Verify 91+ tests still pass

---

## Dependencies
- `redis.asyncio` (already in requirements)
- `sqlalchemy` (already in requirements)

## Risks
- **Redis not running locally** → Tests may fail; use try/except to make Redis optional
- **Connection timeouts** → Add 5-second timeout to all checks

---

## Acceptance Criteria
- [ ] `/health/ready` returns actual database connectivity status
- [ ] `/health/ready` returns actual Redis connectivity status
- [ ] `/health/ready` returns HTTP 503 when database is down
- [ ] Startup logs show connection verification results
- [ ] Shutdown gracefully closes all connections
- [ ] All 91+ existing tests still pass
- [ ] 4+ new tests added for health checks
