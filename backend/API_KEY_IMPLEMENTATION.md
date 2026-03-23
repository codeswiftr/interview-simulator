# API Key Management Implementation

## Overview

Implemented secure API key management for the Interview Simulator, allowing programmatic access to the platform via API keys in addition to JWT tokens.

## Implementation Date
2026-02-20

## Components Created

### 1. Database Model (`app/models/api_key.py`)

**Features:**
- Secure bcrypt hashing for API keys (never stores plain keys)
- Key prefix storage for identification (first 8 chars)
- Scope-based permissions (read, write, admin)
- Per-key rate limiting configuration
- Expiration support
- Usage tracking (last_used_at, request_count)

**Model Fields:**
```python
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- name: str (human-readable name)
- key_hash: str (bcrypt hash)
- key_prefix: str (for identification)
- scopes: str (comma-separated permissions)
- rate_limit: int (requests per minute)
- last_used_at: datetime
- request_count: int
- is_active: bool
- expires_at: datetime (optional)
- created_at/updated_at: datetime
```

**Scopes:**
- `read`: Read-only access to user's data
- `write`: Create/modify user's data
- `admin`: Full access (for admin keys)

### 2. Service Layer (`app/services/api_key_service.py`)

**Key Functions:**
- `generate_api_key()`: Generates secure API keys with format `is_XXXXXXXX...` (43 chars)
- `hash_api_key()`: Bcrypt hashing with 12 rounds
- `verify_api_key()`: Constant-time key verification
- `create_api_key()`: Create new API key (max 10 per user)
- `get_user_api_keys()`: List user's API keys
- `update_api_key()`: Update key properties
- `delete_api_key()`: Remove API key
- `verify_api_key_and_get_user()`: Authenticate requests via API key

**Security Features:**
- Cryptographically secure key generation using `secrets.token_urlsafe()`
- Bcrypt hashing (12 rounds)
- Key prefix indexing for efficient lookups
- User ownership verification on all operations
- Maximum 10 keys per user limit

### 3. API Endpoints (`app/api/api_keys.py`)

**Routes:**
```
POST   /api/v1/api-keys/           Create API key (returns plain key ONCE)
GET    /api/v1/api-keys/           List all user's API keys
GET    /api/v1/api-keys/{key_id}   Get specific API key details
PATCH  /api/v1/api-keys/{key_id}   Update API key properties
DELETE /api/v1/api-keys/{key_id}   Delete API key
```

**Authentication:**
All endpoints require JWT authentication (existing user auth).

**Response Format:**
```json
{
  "key": "is_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "api_key": {
    "id": "uuid",
    "user_id": "uuid",
    "name": "My API Key",
    "key_prefix": "is_XXXXX",
    "scopes": "read,write",
    "rate_limit": 60,
    "is_active": true,
    "last_used_at": "2026-02-20T...",
    "request_count": 42,
    "expires_at": null,
    "created_at": "2026-02-20T..."
  }
}
```

### 4. Authentication Dependencies (`app/dependencies_api_key.py`)

**New Dependencies:**
- `get_user_from_api_key()`: Extract user from API key
- `require_api_key()`: Enforce API key authentication
- `get_user_flexible()`: Support both JWT and API key auth

**Usage:**
```python
# API key only
@router.get("/data")
async def get_data(user: User = Depends(require_api_key)):
    ...

# JWT or API key
@router.get("/data")
async def get_data(user: User = Depends(get_user_flexible)):
    ...
```

### 5. Rate Limiting Middleware (`app/middleware/api_key_rate_limit.py`)

**Features:**
- Per-key rate limiting based on configured limit
- Sliding window algorithm (60-second windows)
- In-memory request tracking
- Rate limit headers in responses:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: When the limit resets
- Only applies to API key requests (JWT has separate rate limiting)

**Implementation:**
- Middleware intercepts API key requests
- Checks rate limit from database
- Tracks requests in memory per key prefix
- Returns 429 Too Many Requests if exceeded

### 6. Database Migration (`alembic/versions/0015_add_api_keys_table.py`)

**Migration:**
- Creates `api_keys` table
- Adds indexes on `user_id`, `key_prefix`, `name`
- Foreign key constraint to users table with CASCADE delete

**Run Migration:**
```bash
cd backend
uv run alembic upgrade head
```

### 7. Comprehensive Tests (`tests/test_api_keys.py`)

**Test Coverage:**
- API key generation format and uniqueness
- Hashing and verification
- CRUD operations (create, read, update, delete)
- User ownership verification
- Rate limiting
- Expiration handling
- Authentication with API keys
- Authorization (users can't access others' keys)
- Edge cases (invalid keys, expired keys, inactive keys)

**Test Classes:**
- `TestAPIKeyGeneration`: Key generation and hashing
- `TestAPIKeyService`: Service layer functions
- `TestAPIKeyEndpoints`: API endpoint integration tests

## Security Considerations

### Implemented Protections

1. **Secure Key Generation**
   - Uses `secrets.token_urlsafe()` for cryptographic randomness
   - 40 characters of entropy (240 bits)
   - URL-safe format (no special characters)

2. **Secure Storage**
   - Keys are hashed with bcrypt (12 rounds)
   - Plain keys never stored in database
   - Only shown once during creation

3. **Rate Limiting**
   - Per-key configurable limits (default: 60 req/min)
   - Prevents abuse and DoS attacks
   - Sliding window algorithm

4. **Access Control**
   - Scope-based permissions
   - Users can only manage their own keys
   - Key ownership verified on all operations

5. **Expiration Support**
   - Optional expiration dates
   - Automatic rejection of expired keys

6. **Usage Tracking**
   - Last used timestamp
   - Total request count
   - Helps identify unused/compromised keys

### Best Practices

1. **Key Rotation**
   - Users should rotate keys periodically
   - Easy to create new keys and delete old ones
   - Max 10 keys per user encourages cleanup

2. **Minimal Scopes**
   - Create keys with minimal required permissions
   - Use `read` scope for read-only operations
   - Reserve `admin` scope for privileged operations

3. **Monitoring**
   - Track usage via `last_used_at` and `request_count`
   - Deactivate suspicious keys immediately
   - Monitor rate limit violations

## Usage Examples

### Creating an API Key

**Request:**
```bash
curl -X POST https://api.example.com/api/v1/api-keys/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["read", "write"],
    "rate_limit": 120
  }'
```

**Response:**
```json
{
  "key": "is_abc123xyz789XXXXXXXXXXXXXXXXXXXXXXXXX",
  "api_key": {
    "id": "...",
    "name": "Production API Key",
    "scopes": "read,write",
    "rate_limit": 120,
    ...
  }
}
```

**Important:** Save the `key` value immediately. It cannot be retrieved later!

### Using an API Key

**Request:**
```bash
curl https://api.example.com/api/v1/interviews \
  -H "Authorization: Bearer is_abc123xyz789XXXXXXXXXXXXXXXXXXXXXXXXX"
```

### Listing API Keys

**Request:**
```bash
curl https://api.example.com/api/v1/api-keys/ \
  -H "Authorization: Bearer JWT_TOKEN"
```

**Response:**
```json
[
  {
    "id": "...",
    "name": "Production API Key",
    "key_prefix": "is_abc12",
    "scopes": "read,write",
    "rate_limit": 120,
    "is_active": true,
    "last_used_at": "2026-02-20T10:30:00Z",
    "request_count": 1523,
    ...
  }
]
```

### Updating an API Key

**Request:**
```bash
curl -X PATCH https://api.example.com/api/v1/api-keys/{key_id} \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "is_active": false
  }'
```

### Deleting an API Key

**Request:**
```bash
curl -X DELETE https://api.example.com/api/v1/api-keys/{key_id} \
  -H "Authorization: Bearer JWT_TOKEN"
```

## Integration with Existing System

### Changes to Existing Files

1. **`app/main.py`**
   - Added `api_keys` router import
   - Included API keys router in application

2. **`app/models/__init__.py`**
   - Added `APIKey` and `APIKeyScope` exports

3. **Database Schema**
   - New `api_keys` table (migration required)

### Backward Compatibility

- All existing JWT authentication continues to work unchanged
- API keys are additive - optional feature
- No breaking changes to existing API endpoints

## Testing

### Run Tests

```bash
cd backend

# Run all API key tests
pytest tests/test_api_keys.py -v

# Run specific test class
pytest tests/test_api_keys.py::TestAPIKeyGeneration -v

# Run with coverage
pytest tests/test_api_keys.py --cov=app.services.api_key_service --cov=app.api.api_keys
```

### Test Database Setup

Tests use the existing test fixtures from `conftest.py`:
- `session`: Async database session
- `test_user`: Pre-created test user
- `auth_headers`: JWT authentication headers
- `client`: Async HTTP test client

## Deployment Checklist

- [ ] Run database migration: `uv run alembic upgrade head`
- [ ] Verify API endpoints in `/docs` (development only)
- [ ] Test API key creation via UI or API
- [ ] Monitor rate limiting metrics
- [ ] Document API key usage for external developers
- [ ] Add API key management UI (future enhancement)
- [ ] Set up monitoring/alerts for suspicious API key usage

## Future Enhancements

1. **Frontend UI**
   - API key management dashboard
   - Copy-to-clipboard for new keys
   - Usage statistics visualization
   - One-click key rotation

2. **Advanced Features**
   - IP whitelisting per key
   - Webhook support for key events
   - Key usage analytics
   - Automatic key rotation
   - Key templates for common use cases

3. **Enterprise Features**
   - Team-level API keys
   - Audit logs for all key operations
   - Advanced rate limiting (per-endpoint, per-resource)
   - Multiple rate limit tiers
   - Key cost tracking

## Related Files

### Core Implementation
- `/app/models/api_key.py` - Database model
- `/app/services/api_key_service.py` - Business logic
- `/app/api/api_keys.py` - API endpoints
- `/app/dependencies_api_key.py` - Auth dependencies
- `/app/middleware/api_key_rate_limit.py` - Rate limiting

### Integration
- `/app/main.py` - Application setup
- `/app/models/__init__.py` - Model exports
- `/alembic/versions/0015_add_api_keys_table.py` - Database migration

### Testing
- `/tests/test_api_keys.py` - Comprehensive test suite

## API Documentation

Full API documentation available at `/docs` endpoint when running in development mode:
```bash
cd backend
uv run uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

Look for the "API Keys" section in the Swagger UI.

## Support

For questions or issues with API key implementation:
1. Check this documentation
2. Review test cases in `tests/test_api_keys.py`
3. Check API documentation at `/docs`
4. Review security best practices above
