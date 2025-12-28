# Due Diligence Tooling Gap Analysis

**Date:** December 28, 2025
**Project:** Interview Simulator
**Tool:** tech-diligence-snapshot

---

## Executive Summary

The `tech-diligence-snapshot` tool is **partially functional** but has gaps preventing automated due diligence on the interview-simulator project. This document outlines what's working, what's missing, and recommendations for completion.

---

## Tool Status: 70% Complete

### What's Working

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI Backend | Running | Server starts on port 8002 |
| Database (SQLite) | Working | Job records created successfully |
| Redis | Working | Health check passes |
| Celery Worker | Running | Processes jobs asynchronously |
| Job Queue | Working | Jobs submitted and tracked |
| API Endpoints | Complete | /analyze, /status, /reports |
| Security Scanners | Integrated | Bandit, Semgrep, CodeQL, Snyk |
| Report Generation | Implemented | PDF generation with WeasyPrint |

### What's Blocking

| Issue | Impact | Resolution |
|-------|--------|------------|
| **GitHub-only support** | HIGH | Tool rejects local file paths |
| **No interview-simulator GitHub repo** | HIGH | Repo not publicly accessible |
| **Missing GitHub token** | MEDIUM | Private repos require PAT |
| **Snyk token missing** | LOW | Dependency audit won't run |

---

## Attempted Workflow

### 1. Server Started Successfully
```bash
cd ~/work/FORGE/codeswiftr-com/tech-diligence-snapshot/backend
uv run uvicorn app.main:app --port 8002
# Result: Server running, health check passes
```

### 2. Job Submitted Successfully
```bash
curl -X POST http://localhost:8002/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "file:///Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator",
    "investor_name": "FORGE Due Diligence",
    "startup_name": "Interview Simulator"
  }'
# Result: Job ID created: f0d30f7e-4127-41e1-86d2-abd500edf72e
```

### 3. Celery Worker Started
```bash
uv run celery -A app.core.celery_app:celery_app worker --loglevel=info
# Result: Worker connected to Redis, processing tasks
```

### 4. Job Failed - GitHub-Only
```
ValueError: Only GitHub repositories are supported: file:///...
```

**Root Cause:** `app/services/github_ingestion.py:111` rejects non-GitHub URLs.

---

## Required Changes to Enable Local Analysis

### Option A: Add Local Repository Support (Recommended)

**Files to Modify:**

1. **`app/services/github_ingestion.py`**
   - Add `clone_local_repository()` method
   - Support `file://` URLs
   - Skip GitHub API calls for local repos

2. **`app/api/v1/analysis.py`**
   - Detect URL scheme (file:// vs https://)
   - Route to appropriate ingestion method

**Effort:** 4-6 hours

### Option B: Push to GitHub and Analyze

1. Push interview-simulator to GitHub (public or private)
2. Configure GitHub PAT in `.env`
3. Run analysis with GitHub URL

**Effort:** 30 minutes (if repo already on GitHub)

### Option C: Manual Analysis Pipeline

Run individual security scanners directly:

```bash
cd ~/work/FORGE/codeswiftr-com/interview-simulator

# Bandit (Python security)
bandit -r backend/app -f json -o bandit-results.json

# Semgrep (multi-language)
semgrep --config auto backend/ frontend/ --json > semgrep-results.json

# npm audit (frontend deps)
cd frontend && npm audit --json > npm-audit.json

# pip-audit (backend deps)
cd backend && pip-audit --format json > pip-audit.json
```

**Effort:** 1 hour

---

## Current Due Diligence Coverage

Given the tooling gap, here's what we have vs. what's missing:

### Available (Manual Reports)

| Report | Location | Last Updated |
|--------|----------|--------------|
| Codebase Audit | `docs/CODEBASE_AUDIT.md` | Dec 13, 2025 |
| Security Audit | `docs/SECURITY_AUDIT.md` | Dec 22, 2025 |
| Test Coverage | `docs/TEST_COVERAGE.md` | Dec 22, 2025 |
| Due Diligence Summary | `docs/DUE_DILIGENCE_REPORT.md` | Dec 27, 2025 |

### Missing (Automated Scanning)

| Report | Tool | Status |
|--------|------|--------|
| SAST Report | Bandit/Semgrep | **NOT RUN** |
| Dependency Vulnerabilities | Snyk/npm-audit | **NOT RUN** |
| CodeQL Analysis | CodeQL | **NOT RUN** |
| Aggregated Risk Score | tech-diligence | **NOT RUN** |
| Investor PDF Report | WeasyPrint | **NOT RUN** |

---

## Recommendations

### Immediate (This Week)

1. **Run manual security scans** using Option C above
2. **Document results** in existing audit files
3. **Push interview-simulator to GitHub** if not already there

### Short-Term (Next Sprint)

1. **Add local repository support** to tech-diligence-snapshot
2. **Configure GitHub PAT and Snyk tokens** in `.env`
3. **Run full automated pipeline** on interview-simulator

### Long-Term

1. **Integrate with CI/CD** for automatic due diligence on each PR
2. **Build customer-facing UI** for tech-diligence-snapshot
3. **Add more scanners** (CodeQL, OWASP ZAP, etc.)

---

## Environment Setup Required

To run the full pipeline, the following must be configured in `.env`:

```bash
# Already Working
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
REDIS_URL=redis://localhost:6379/0

# Need Configuration
GITHUB_TOKEN=ghp_xxxx              # For private repo access
SNYK_TOKEN=xxxx                    # For dependency scanning
JWT_SECRET=xxxx                    # For API authentication
ENCRYPTION_KEY=xxxx                # For report storage
```

---

## Appendix: Full Error Log

```
ValueError: Only GitHub repositories are supported: file:///Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator
  File "app/services/github_ingestion.py", line 111, in _parse_github_url
    raise ValueError(f"Only GitHub repositories are supported: {repo_url}")
```

---

**Status:** Tooling gap documented. Manual due diligence reports available.
**Next Action:** Either push to GitHub and run automated scan, or add local repo support to tool.
