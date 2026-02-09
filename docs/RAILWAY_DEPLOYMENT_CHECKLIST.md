# Railway Deployment Checklist: Interview Simulator

**Project:** `codeswiftr-com/interview-simulator`
**Audit Date:** 2026-02-06
**Status:** ✅ READY FOR DEPLOYMENT (with minor config update)

## 1. Core Requirements

| Check | Status | Notes |
|-------|:------:|-------|
| **Dockerfile** | **PASS** | Multi-stage, `uv`-optimized, non-root user configured. |
| **Dependencies** | **PASS** | `pyproject.toml` defines all required packages. |
| **Env Vars** | **PASS** | `.env.example` is comprehensive and documented. |
| **Migrations** | **PASS** | `alembic.ini` present; migrations run on deploy. |
| **Health Check** | **PASS** | `/api/v1/health` endpoint exists and is used in Dockerfile. |

## 2. Configuration Audit

| Check | Status | Fix Command |
|-------|:------:|-------------|
| **Config File** | **FAIL** | Replace legacy `railway.toml` with standard `railway.json`. |
| **Watch Patterns** | **FAIL** | Missing in current config; prevents spurious rebuilds. |
| **Health Path** | **FAIL** | Explicit `healthcheckPath` missing in Railway config. |

## 3. Required Actions

The backend is code-ready, but the deployment configuration needs modernization to match the FORGE standard.

### Fix 1: Create `railway.json`

Run the following to replace `railway.toml` with the standardized JSON config:

```bash
# Delete legacy config
rm backend/railway.toml

# Create new standard config
cat > backend/railway.json <<EOF
{
  "\$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile",
    "watchPatterns": ["app/**", "alembic/**", "pyproject.toml", "uv.lock"]
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT --proxy-headers --forwarded-allow-ips='*'",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/api/v1/health",
    "healthcheckTimeout": 100,
    "numReplicas": 1
  }
}
EOF
```

### Fix 2: Verify GitHub Actions (Optional)

If using CI/CD, ensure `.github/workflows/railway-deploy.yml` exists as per `docs/templates/RAILWAY_TEMPLATE.md`.

## 4. Deployment Verification

After applying the fix:

1.  **Commit changes**:
    ```bash
    git add backend/railway.json backend/railway.toml
    git commit -m "chore: standardize railway config"
    ```
2.  **Deploy**:
    ```bash
    railway up --service interview-simulator-api
    ```
