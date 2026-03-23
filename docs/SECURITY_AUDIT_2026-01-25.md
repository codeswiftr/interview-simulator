# Dependency Audit Report - Interview Simulator

**Date**: 2026-01-25
**Auditor**: TECH AGENT
**Project**: codeswiftr-com/interview-simulator

---

## Security Summary

| Severity | Backend | Frontend | Action Required |
|----------|---------|----------|-----------------|
| Critical | 0 | 0 | - |
| High | 0 | 2 | 24 hours |
| Medium | 0 | 3 | 1 week |
| Low | 1* | 0 | No fix available |

*ecdsa CVE-2024-23342 has no fix version available

---

## Backend Vulnerabilities (Python)

### Known CVEs

| Package | Version | CVE | Severity | Fix Version |
|---------|---------|-----|----------|-------------|
| ecdsa | 0.19.1 | CVE-2024-23342 | Low | No fix available |

**Note**: The ecdsa vulnerability relates to timing attacks in signature verification. This is a transitive dependency and has no available fix.

### Outdated Packages (26 packages)

| Package | Current | Latest | Priority |
|---------|---------|--------|----------|
| fastapi | 0.124.4 | 0.128.0 | Medium |
| anthropic | 0.75.0 | 0.76.0 | Low |
| openai | 2.11.0 | 2.15.0 | Low |
| sqlmodel | 0.0.27 | 0.0.31 | Medium |
| starlette | 0.50.0 | 0.52.1 | Medium |
| uvicorn | 0.38.0 | 0.40.0 | Low |
| stripe | 14.0.1 | 14.2.0 | Low |
| sentry-sdk | 2.48.0 | 2.50.0 | Low |
| numpy | 2.3.5 | 2.4.1 | Low |
| scipy | 1.16.3 | 1.17.0 | Low |

---

## Frontend Vulnerabilities (JavaScript)

### Known CVEs

| Package | Version | CVE/Advisory | Severity | Fix Available |
|---------|---------|--------------|----------|---------------|
| preact | 10.28.x | GHSA-36hm-qxxp-pg3m | High | Yes |
| react-router | 7.x | GHSA-h5cw-625j-3rxh | High | Yes |
| react-router | 7.x | GHSA-2w69-qvjg-hvjx | High | Yes |
| react-router | 7.x | GHSA-8v8x-cx79-35w7 | High | Yes |
| lodash | 4.17.21 | GHSA-xxjr-mmjv-4gpg | Moderate | Yes |
| lodash-es | 4.17.22 | GHSA-xxjr-mmjv-4gpg | Moderate | Yes |

### Fix Command
```bash
cd frontend && npm audit fix
```

---

## Recommendations

### Immediate (24 hours)
1. **Frontend**: Run `npm audit fix` to patch react-router and preact vulnerabilities
2. **Frontend**: Review react-router CSRF and XSS fixes for any breaking changes

### This Week
1. **Backend**: Update fastapi 0.124.4 → 0.128.0
2. **Backend**: Update sqlmodel 0.0.27 → 0.0.31
3. **Backend**: Update starlette 0.50.0 → 0.52.1

### Scheduled Maintenance
1. **Backend**: Bulk update minor versions (anthropic, openai, stripe, etc.)
2. **Backend**: Monitor ecdsa for fix release

---

## License Compliance

All dependencies use permissive licenses (MIT, Apache-2.0, BSD) compatible with commercial use.

---

## Next Audit

Scheduled: 2026-02-01 (weekly cadence)
