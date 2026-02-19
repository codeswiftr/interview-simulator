# Interview Simulator - Security Features

## Overview

This document outlines the security hardening implemented in Interview Simulator to protect user accounts, data, and prevent common attack vectors.

## Security Features

### 1. Account Lockout (Brute Force Protection)

**Implementation**: `app/services/account_lockout.py`

Prevents brute force password attacks by:
- Tracking failed login attempts per email address
- Locking accounts after 5 failed attempts within 15 minutes
- Auto-unlocking after 15-minute lockout period
- Recording attempt IP addresses for security monitoring
- Clearing failed attempts on successful login

**Configuration**:
```python
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15
LOCKOUT_DURATION_MINUTES = 15
```

**Database**: `login_attempts` table tracks all authentication attempts

### 2. Password Complexity Requirements

**Implementation**: `app/utils/password_validation.py`

Enforces strong password policies:
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- Blocks 18 most common passwords (password, 123456, etc.)
- Prevents password matching username or email
- Optional special character requirement (configurable)

**Validation Points**:
- User registration (`UserCreate`)
- Password change (`PasswordChange`)
- Password reset (`ResetPasswordRequest`)

### 3. Rate Limiting

**Implementation**: `app/dependencies.py` + `forge_shared.middleware.RateLimitMiddleware`

**Per-Endpoint Limits** (in-memory, per IP):
- Login: 10 requests/minute
- Registration: 5 requests/minute
- Password reset: 5 requests/minute

**Global Limits** (Redis-backed, production only):
- 60 requests/minute per IP
- 1000 requests/hour per IP

**Excludes**: `/health`, `/docs`, `/openapi.json`, static files

### 4. Security Headers

**Implementation**: `forge_shared.middleware.SecurityMiddleware`

**Headers Set**:
- `Strict-Transport-Security`: HTTPS enforcement (max-age=31536000)
- `X-Content-Type-Options`: nosniff (prevents MIME sniffing)
- `X-Frame-Options`: DENY (prevents clickjacking)
- `X-XSS-Protection`: 1; mode=block (legacy XSS protection)
- `Referrer-Policy`: strict-origin-when-cross-origin

### 5. CORS Configuration

**Implementation**: `app/main.py`

**Production**:
- Strict origin whitelist (app.codeswiftr.com, Cloudflare Pages)
- No wildcard origins allowed
- Credentials enabled for authenticated requests

**Development**:
- Regex-based localhost/127.0.0.1 on any port
- .local domains (for Caddy proxy)

### 6. Input Validation

**Implementation**: Pydantic with `ConfigDict(strict=True)`

**Protections**:
- Type coercion disabled (strict mode)
- EmailStr validation on all email fields
- Max length constraints (full_name: 200, token: 200)
- Prevents SQL injection via parameterized queries (SQLModel)

**Models with Strict Validation**:
- `UserCreate`, `UserLogin`, `UserUpdate`
- `PasswordChange`, `ResetPasswordRequest`
- `RefreshTokenRequest`, `ForgotPasswordRequest`

### 7. Authentication & Authorization

**Implementation**: JWT via `forge_shared.auth`

**Features**:
- JWT access tokens (short-lived, configurable expiry)
- Refresh tokens (7-day expiry, stored in database)
- Token rotation on refresh (old token invalidated)
- Bcrypt password hashing (12 rounds, migrated from pbkdf2_sha256)
- Lazy password hash migration on login

**JWT Claims**:
- `sub`: User ID (UUID)
- `email`: User email
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp

### 8. Session Management

**Features**:
- Refresh tokens stored in database (single device per user)
- Token expiration tracking (`refresh_token_expires_at`)
- Last login timestamp tracking
- Manual token invalidation on logout (clear refresh token)

### 9. Password Reset Security

**Implementation**: `app/api/auth.py`

**Features**:
- Secure token generation (32-byte URL-safe random)
- One-hour token expiration
- Single-use tokens (marked as `used` after redemption)
- Generic responses (don't reveal if email exists)
- Email delivery errors don't expose user existence

### 10. Error Handling

**Principles**:
- Generic error messages for auth failures
- No user enumeration via timing or error messages
- Structured error responses with machine-readable codes
- Sensitive errors logged server-side only

## Security Testing

### Test Coverage

**Account Lockout** (`tests/test_account_lockout.py`):
- Failed attempt tracking
- Lockout after 5 failures
- Auto-unlock after 15 minutes
- Case-insensitive email matching
- Integration with login endpoint

**Password Complexity** (`tests/test_password_complexity.py`):
- Uppercase/lowercase/digit requirements
- Minimum length validation
- Common password blocking
- Email/username matching prevention
- Strength scoring

**Security Hardening** (`tests/test_security_hardening.py`):
- Input validation (strict mode)
- Email format validation
- Max length enforcement
- Rate limiting behavior
- Security headers presence

### Running Security Tests

```bash
cd backend

# All security tests
uv run pytest tests/test_account_lockout.py tests/test_password_complexity.py tests/test_security_hardening.py -v

# Specific test suite
uv run pytest tests/test_account_lockout.py -v
```

## Security Monitoring

### Logged Events

- Failed login attempts (email, IP, timestamp)
- Account lockouts (email, lockout expiration)
- Password changes
- Email changes (with verification)
- Account deletions

### Metrics to Monitor

- Failed login rate (per email, per IP)
- Lockout frequency
- Password reset request volume
- Token refresh failures
- Rate limit violations

## Known Limitations

### 1. CSRF Protection

**Status**: Not implemented

**Reason**: SPA architecture with JWT in Authorization header (not cookies) reduces CSRF risk. CSRF tokens would be needed if using cookie-based sessions.

**Mitigation**: Strict CORS policy, SameSite cookies if cookies are added

### 2. Session Timeout

**Status**: JWT expiration only, no inactivity timeout

**Reason**: Stateless JWT tokens don't track activity

**Mitigation**: Short access token expiry (15-30 min recommended), refresh token rotation

### 3. In-Memory Rate Limiting

**Status**: Per-endpoint limits are in-memory (lost on restart)

**Reason**: Simpler implementation for endpoint-specific limits

**Mitigation**: Global Redis-backed rate limiting in production, per-endpoint limits provide additional layer

### 4. Account Enumeration

**Status**: Partial protection

**Email Validation**: Generic responses on password reset, but email validation on registration reveals if email exists

**Login**: Generic "Invalid credentials" message

**Mitigation**: Consider rate limiting registration endpoint more aggressively

## Compliance Considerations

### OWASP Top 10 2021

| Risk | Mitigation |
|------|------------|
| A01: Broken Access Control | JWT authentication, role-based checks |
| A02: Cryptographic Failures | Bcrypt password hashing, HTTPS enforcement (HSTS) |
| A03: Injection | Parameterized queries (SQLModel), input validation |
| A04: Insecure Design | Security by default, fail-safe defaults |
| A05: Security Misconfiguration | Security headers, strict CORS, no debug in prod |
| A06: Vulnerable Components | Regular dependency updates (Dependabot) |
| A07: Authentication Failures | Account lockout, password complexity, JWT expiry |
| A08: Data Integrity Failures | Input validation, strict mode, type checking |
| A09: Logging Failures | Structured logging, security event tracking |
| A10: SSRF | N/A (no user-controlled URL fetching) |

### Data Protection

- Passwords: Bcrypt hashed (never stored plaintext)
- Tokens: Secure random generation (secrets.token_urlsafe)
- PII: Soft delete with anonymization (email, name)
- Database: PostgreSQL with prepared statements

## Security Checklist

Before deploying to production:

- [ ] `SECRET_KEY` is strong random value (not default)
- [ ] `DEBUG=false` in production
- [ ] Database credentials are secure and rotated
- [ ] CORS origins are explicitly whitelisted (no wildcards)
- [ ] HTTPS is enforced (HSTS header set)
- [ ] Redis is secured (authentication enabled)
- [ ] Sentry or error monitoring is configured
- [ ] Rate limiting is enabled (Redis-backed)
- [ ] Database backups are automated
- [ ] Security headers are verified (use securityheaders.com)
- [ ] Dependencies are up to date (run `uv pip list --outdated`)

## Incident Response

### Account Lockout

If legitimate users are locked out:

1. Check `login_attempts` table for the email
2. Delete failed attempts: `DELETE FROM login_attempts WHERE email = 'user@example.com'`
3. User can log in immediately

### Suspicious Activity

If detecting brute force attempts:

1. Query `login_attempts` for patterns:
   ```sql
   SELECT ip_address, COUNT(*) as attempts
   FROM login_attempts
   WHERE attempted_at > NOW() - INTERVAL '1 hour'
   GROUP BY ip_address
   ORDER BY attempts DESC;
   ```

2. Block IP at infrastructure level (Cloudflare, Railway)

### Database Migration

Migration `0014_add_login_attempts_table` adds the lockout tracking table. Run with:

```bash
uv run alembic upgrade head
```

## Future Enhancements

### Recommended Additions

1. **CSRF Protection**: Add CSRF tokens if moving to cookie-based auth
2. **Session Timeout**: Implement inactivity-based token invalidation
3. **2FA/MFA**: Add TOTP or SMS-based two-factor authentication
4. **Password Breach Detection**: Check against HaveIBeenPwned API
5. **Geolocation Alerts**: Notify users of logins from new locations
6. **IP Allowlisting**: Allow enterprise customers to restrict IPs
7. **Audit Logs**: Comprehensive audit trail for compliance (GDPR, SOC2)
8. **API Key Management**: For programmatic access
9. **OAuth2 Social Login**: Google, GitHub, LinkedIn

### Monitoring Improvements

1. Alert on high failed login rates (> 100/hour globally)
2. Dashboard for lockout metrics
3. Automated security scanning (SAST/DAST)
4. Penetration testing (annual or before major releases)

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [forge-shared Security Middleware](https://github.com/FORGE/forge-shared)

## Contact

For security issues or questions:
- Email: security@codeswiftr.com
- Report vulnerabilities via private disclosure (do not open public issues)
