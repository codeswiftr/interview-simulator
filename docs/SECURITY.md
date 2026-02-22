# Interview Simulator Security Documentation

**Last Updated:** 2026-02-22  
**Status:** Production Hardened  
**OWASP Top 10 Coverage:** Complete

---

## Overview

This document describes the security measures implemented in the Interview Simulator application to protect user data and prevent common attacks.

---

## Security Controls Summary

| Control | Status | Implementation |
|---------|--------|----------------|
| Password Complexity | ✅ Enforced | 8+ chars, uppercase, lowercase, digit required |
| Account Lockout | ✅ Enforced | 5 failed attempts → 15 min lockout |
| Rate Limiting | ✅ Enforced | Login: 10/min, Register: 5/min, API: 60/min |
| Security Headers | ✅ Enforced | HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| CORS | ✅ Restricted | Production domains only, no wildcards |
| SQL Injection Prevention | ✅ Protected | Parameterized queries via SQLModel |
| XSS Prevention | ✅ Protected | Input sanitization via bleach |
| Session Management | ✅ Implemented | JWT with refresh token rotation |
| PII Protection | ✅ Enforced | Email masking in logs |
| Input Validation | ✅ Strict | Pydantic strict mode on all inputs |

---

## Authentication Security

### Password Requirements

```python
# app/utils/password_validation.py
MIN_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL = False  # Optional for UX
BLOCKED_PASSWORDS = ["password", "123456", "qwerty", ...]  # Common passwords
```

### Account Lockout

- **Threshold:** 5 failed login attempts within 15 minutes
- **Lockout Duration:** 15 minutes
- **Scope:** Per email address (case-insensitive)
- **Implementation:** `app/services/account_lockout.py`

### Session Management

| Token Type | Expiration | Storage |
|------------|------------|---------|
| Access Token | 30 minutes | Client-side |
| Refresh Token | 7 days | Database (SHA-256 hashed) |

### Token Security

- JWT signed with HS256 algorithm
- Refresh tokens stored as SHA-256 hashes (not plaintext)
- Token rotation on refresh (old token invalidated)
- Secure token generation via `secrets.token_urlsafe(32)`

---

## Input Validation

### Pydantic Strict Mode

All request schemas use Pydantic strict mode:

```python
class UserCreate(SQLModel):
    model_config = ConfigDict(strict=True)
    
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]
```

### SQL Injection Prevention

All database queries use parameterized queries via SQLModel/SQLAlchemy:

```python
# Safe - uses parameterized query
result = await session.exec(select(User).where(User.email == email))

# Never use string formatting in queries
# UNSAFE: session.exec(f"SELECT * FROM users WHERE email = '{email}'")
```

### XSS Prevention

Input sanitization for user-provided content:

```python
import bleach

ALLOWED_TAGS = []  # Strip all HTML
ALLOWED_ATTRIBUTES = {}

sanitized = bleach.clean(user_input, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

---

## Security Headers

All responses include security headers enforced via middleware:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | XSS filter (legacy browsers) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Content-Security-Policy` | (configured per environment) | XSS prevention |

**Implementation:** `app/middleware/security_headers.py` and `forge_shared.middleware.SecurityMiddleware`

---

## CORS Configuration

### Production

```python
# Production - restricted origins only
CORS_ORIGINS = [
    "https://app.codeswiftr.com",
    "https://interview-simulator-4bo.pages.dev",
]
# No localhost, no wildcards
```

### Development

```python
# Development - includes localhost for testing
allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1|[\w.-]+\.local)(:\d+)?$"
```

**Validation:** Production config rejects localhost origins and wildcards at startup.

---

## Rate Limiting

### Per-Endpoint Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/users/login` | 10 requests | 1 minute |
| `/api/v1/users/register` | 5 requests | 1 minute |
| `/api/v1/auth/forgot-password` | 5 requests | 1 minute |
| All other API endpoints | 60 requests | 1 minute |

### Implementation

- **Auth endpoints:** In-memory sliding window (`app/middleware/auth_rate_limit.py`)
- **General API:** Redis-backed via `forge_shared.middleware.RateLimitMiddleware`

---

## Data Protection

### PII Handling

- Email addresses masked in all log output
- Passwords never logged
- Refresh tokens stored as SHA-256 hashes

```python
class _EmailMaskingFilter(logging.Filter):
    def filter(self, record):
        record.msg = mask_emails_in_text(str(record.msg))
        return True
```

### Database Security

- All connections use SSL in production
- Credentials stored in environment variables
- No hardcoded secrets

---

## Monitoring & Auditing

### Security Events Logged

- Failed login attempts (with IP, timestamp)
- Account lockouts
- Password reset requests
- API key usage

### Error Monitoring

Sentry integration for production error tracking:

```python
if settings.sentry_dsn and not settings.debug:
    sentry_sdk.init(dsn=settings.sentry_dsn, ...)
```

---

## Security Testing

### Test Coverage

- `tests/test_security_hardening.py` - 688 lines, comprehensive coverage
- `tests/test_account_lockout.py` - Account lockout integration
- `tests/test_password_validation.py` - Password complexity validation

### Run Security Tests

```bash
cd backend
uv run pytest tests/test_security_hardening.py tests/test_account_lockout.py -v
```

### Security Scanning

```bash
# Dependency vulnerabilities
uv run safety check

# Code security analysis
uv run bandit -r app/

# SAST scanning
uv run semgrep --config=auto app/
```

---

## OWASP Top 10 Compliance

| Risk | Status | Implementation |
|------|--------|----------------|
| A01: Broken Access Control | ✅ | JWT auth, RBAC ready |
| A02: Cryptographic Failures | ✅ | bcrypt hashing, HTTPS only |
| A03: Injection | ✅ | Parameterized queries, input validation |
| A04: Insecure Design | ✅ | Security-by-design architecture |
| A05: Security Misconfiguration | ✅ | Production validation, no defaults |
| A06: Vulnerable Components | ✅ | Regular dependency updates |
| A07: Auth Failures | ✅ | Lockout, rate limiting, secure tokens |
| A08: Data Integrity Failures | ✅ | Input sanitization, CSRF protection |
| A09: Logging/Monitoring | ✅ | Security event logging, Sentry |
| A10: SSRF | ✅ | No user-controlled URLs |

---

## Incident Response

### Security Incident Checklist

1. **Identify** - Review Sentry alerts, log anomalies
2. **Contain** - Revoke compromised tokens, lock affected accounts
3. **Eradicate** - Patch vulnerability, rotate secrets
4. **Recover** - Restore from clean backup if needed
5. **Post-Mortem** - Document incident, update security measures

### Contact

- Security issues: security@codeswiftr.com

---

## Changelog

### 2026-02-22
- Documented existing security controls
- Verified OWASP Top 10 compliance
- Added security testing documentation

### Sprint 9 (Feb 2026)
- Implemented account lockout after failed attempts
- Added rate limiting on auth endpoints
- Enforced security headers
- Added PII masking in logs
- Comprehensive security test suite
