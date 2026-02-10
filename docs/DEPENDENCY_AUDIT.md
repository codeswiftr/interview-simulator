# Interview Simulator - Dependency Audit

**Date:** 2026-02-10
**Audited By:** Claude Code + pip-audit
**Scope:** `codeswiftr-com/interview-simulator/backend`
**Python Version:** 3.12+
**Total Packages:** ~200 installed

---

## Executive Summary

| Metric | Status |
|--------|--------|
| Critical CVEs | 0 |
| High CVEs | 4 |
| Medium CVEs | 32+ |
| Overall Risk | MEDIUM |

**Key Finding:** pyproject.toml has many versions correctly pinned, but pip-audit detected vulnerabilities in transitive dependencies.

---

## HIGH Severity Vulnerabilities

| Package | Installed | Vulnerability | Fix |
|---------|-----------|---------------|-----|
| **aiohttp** | 3.12.14 | GHSA-6mq8-rvhq-8wgg (DoS) | 3.13.3 |
| **aiohttp** | 3.12.14 | GHSA-54jq-c3m8-4m76 (Request Splitting) | 3.13.3 |
| **python-jose** | 3.3.0 | PYSEC-2024-232 (Timing Attack) | 3.4.0 |
| **python-jose** | 3.3.0 | PYSEC-2024-233 | 3.4.0 |

---

## MEDIUM Severity (Key Ones)

| Package | Installed | Vulnerability | Fix |
|---------|-----------|---------------|-----|
| jinja2 | 3.1.3 | GHSA-h75v-3vvj-5mfj | 3.1.6 |
| starlette | 0.38.6 | GHSA-f96h-pmfr-66vw | 0.40.0 |
| werkzeug | 3.1.3 | GHSA-hgf8-39gv-g3f2 | 3.1.5 |
| urllib3 | 2.5.0 | GHSA-gm62-xv2j-4w53 | 2.6.0 |
| mlflow | 2.11.3 | 15+ CVEs | Remove |
| filelock | 3.12.4 | GHSA-w853-jp5j-5j7f | 3.20.3 |

---

## pyproject.toml Assessment

**Strengths:**
- `python-multipart>=0.0.22` - Correctly pinned (CVE fix)
- `urllib3>=2.6.3` - Correctly pinned
- `pyasn1>=0.6.2` - Correctly pinned
- `filelock>=3.20.3` - Correctly pinned

**Concerns:**
- `python-jose>=3.3.0` - Has HIGH vulnerabilities, should be `>=3.4.0`
- aiohttp vulnerabilities come from transitive deps (httpx depends on it)

---

## Recommendations

### Immediate (This Week)

```bash
cd backend

# Fix python-jose HIGH vulnerabilities
uv pip install "python-jose[cryptography]>=3.4.0"

# Check aiohttp source
uv pip show httpx | grep -i aiohttp
```

### This Sprint

```bash
# Update Jinja2
uv pip install "jinja2>=3.1.6"

# Update starlette
uv pip install "starlette>=0.40.0"

# Update werkzeug
uv pip install "werkzeug>=3.1.5"
```

---

## CI/CD Status

**Good:** pip-audit is already in dev dependencies (`dependency-groups.dev`)

```bash
# Run audit
uv run pip-audit
```

---

## Risk Assessment

| Area | Status | Notes |
|------|--------|-------|
| Authentication Libs | ⚠️ MEDIUM | python-jose needs update |
| HTTP Libraries | ⚠️ MEDIUM | aiohttp from httpx |
| ML Dependencies | ⚠️ HIGH | mlflow has 15+ CVEs |
| Template Engine | ⚠️ MEDIUM | jinja2 needs update |
| Overall | ⚠️ MEDIUM | Fixable in 1 week |

---

**Report Generated:** 2026-02-10
**Next Audit:** 2026-03-10
