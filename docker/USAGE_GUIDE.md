# Interview Simulator - Docker Usage Guide

Complete guide to using Docker for local development and staging deployment.

## Overview

This directory contains two complete Docker environments:

1. **Local Development** (`docker-compose.yml`) - For active development with hot-reloading
2. **Staging Environment** (`docker-compose.staging.yml`) - Production-like deployment for testing

## Which Environment Should I Use?

| Use Case | Environment | File |
|----------|-------------|------|
| Writing code, debugging | Local Development | `docker-compose.yml` |
| Testing before Railway deploy | Local Development | `docker-compose.yml` |
| Full-stack integration testing | Local Development | `docker-compose.yml` |
| QA demos, stakeholder testing | Staging | `docker-compose.staging.yml` |
| Performance testing | Staging | `docker-compose.staging.yml` |
| Production-like validation | Staging | `docker-compose.staging.yml` |

## Local Development Setup

### Quick Start (5 minutes)

```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/docker

# 1. Initialize environment
make -f Makefile.dev dev-init

# 2. (Optional) Edit .env to add API keys
vim .env

# 3. Start everything
make -f Makefile.dev dev-up

# 4. Access services
# Frontend: http://localhost:5173
# Backend: http://localhost:8000/docs
```

### What You Get

- **Frontend**: Vite dev server with Hot Module Reloading (HMR)
- **Backend**: FastAPI with auto-reload on code changes
- **Database**: PostgreSQL 16 with automatic migrations
- **Redis**: For caching and rate limiting
- **No build step**: Just edit code and see changes instantly

### Development Workflow

1. **Start environment**: `make -f Makefile.dev dev-up`
2. **Edit code**: Changes in `backend/app/` or `frontend/src/` auto-reload
3. **View logs**: `make -f Makefile.dev dev-logs`
4. **Run tests**: `make -f Makefile.dev dev-test-backend`
5. **Stop when done**: `make -f Makefile.dev dev-down`

### Common Development Commands

```bash
# View all logs
make -f Makefile.dev dev-logs

# View backend logs only
make -f Makefile.dev dev-logs-backend

# Run database migrations
make -f Makefile.dev dev-migrate

# Seed database with test data
make -f Makefile.dev dev-seed

# Open backend shell
make -f Makefile.dev dev-shell-backend

# Open database shell
make -f Makefile.dev dev-shell-db

# Check service health
make -f Makefile.dev dev-health

# Restart after config changes
make -f Makefile.dev dev-restart
```

### Key Files for Development

- **Configuration**: `.env` (created from `.env.example`)
- **Commands**: `Makefile.dev`
- **Orchestration**: `docker-compose.yml`
- **Frontend Dockerfile**: `Dockerfile.frontend.dev`
- **Backend Dockerfile**: `Dockerfile.backend` (builder stage)
- **Documentation**: `README_LOCAL_DEV.md`

## Staging Environment Setup

### Quick Start (10 minutes)

```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/docker

# 1. Copy staging environment template
cp .env.staging.example .env.staging

# 2. Edit with production-like values
vim .env.staging
# CRITICAL: Set strong passwords and API keys!

# 3. Validate configuration
./validate.sh

# 4. Build images
make build

# 5. Start all services
make up

# 6. Check health
make health
```

### What You Get

- **Frontend**: Production Nginx serving optimized static files
- **Backend**: FastAPI with 2 workers (production mode)
- **Database**: PostgreSQL 16 with performance tuning
- **Redis**: With password authentication and persistence
- **Resource Limits**: CPU and memory constraints enforced
- **Security**: Non-root containers, strong passwords, CORS restrictions

### Staging Workflow

1. **Configure**: Edit `.env.staging` with real credentials
2. **Validate**: Run `./validate.sh` to check configuration
3. **Build**: `make build` to create production images
4. **Deploy**: `make up` to start all services
5. **Monitor**: `make health` and `make logs` to verify
6. **Test**: Run full integration and E2E tests
7. **Teardown**: `make down` when finished

### Common Staging Commands

```bash
# Build and start
make build && make up

# View logs
make logs

# Check health
make health

# Run migrations
make migrate

# Backup database
make backup

# Restart after changes
make build-backend && make restart-backend

# Stop everything
make down

# Full cleanup (WARNING: deletes data)
make down-volumes
```

### Key Files for Staging

- **Configuration**: `.env.staging` (created from `.env.staging.example`)
- **Commands**: `Makefile`
- **Orchestration**: `docker-compose.staging.yml`
- **Frontend Dockerfile**: `Dockerfile.frontend`
- **Backend Dockerfile**: `Dockerfile.backend`
- **Nginx Config**: `nginx.conf`, `nginx-site.conf`
- **Validation**: `validate.sh`
- **Documentation**: `README.md`, `QUICKSTART.md`

## Comparison

| Feature | Local Development | Staging |
|---------|------------------|---------|
| **Frontend Server** | Vite dev (:5173) | Nginx production (:80) |
| **Hot Reloading** | ✅ Enabled | ❌ Disabled |
| **Backend Workers** | 1 (with reload) | 2 (production) |
| **Debug Mode** | ✅ Enabled | ❌ Disabled |
| **Build Required** | ❌ No | ✅ Yes |
| **Resource Limits** | Relaxed | Enforced |
| **CORS** | Permissive | Restricted |
| **Secrets** | Dev defaults OK | Strong required |
| **Logging** | DEBUG | INFO/WARNING |
| **Performance** | Slower (dev mode) | Optimized |
| **Security** | Relaxed | Hardened |

## Environment Variables

### Required for Both

```bash
POSTGRES_PASSWORD=...       # Database password
SECRET_KEY=...              # JWT secret (32+ chars)
```

### Optional but Recommended

```bash
# AI Services
GROQ_API_KEY=...            # For transcription (free tier available)
OPENROUTER_API_KEY=...      # For AI feedback (cost-effective Claude)

# Email
RESEND_API_KEY=...          # For password reset emails

# Analytics
POSTHOG_API_KEY=...         # For usage tracking
```

### Staging-Specific

```bash
CORS_ORIGINS=...            # Restrict to your staging domain
FRONTEND_URL=...            # Your staging domain URL
SENTRY_DSN=...              # Error tracking (optional)
```

## Troubleshooting

### Problem: Services won't start

**Check**:
```bash
# Local dev
make -f Makefile.dev dev-ps
make -f Makefile.dev dev-logs

# Staging
make ps
make logs
```

**Common causes**:
1. Port conflicts (8000, 5173, 5432, 6379)
2. Database not ready (wait 10-30s)
3. Missing environment variables
4. Out of disk space

### Problem: Backend connection errors

**Check database**:
```bash
# Local dev
make -f Makefile.dev dev-shell-db

# Staging
make shell-db
```

**Check backend logs**:
```bash
# Local dev
make -f Makefile.dev dev-logs-backend | grep -i error

# Staging
make logs-backend | grep -i error
```

### Problem: Frontend shows 404 for API

**Check CORS**:
```bash
# Local dev - should see CORS origins in logs
make -f Makefile.dev dev-logs-backend | grep CORS

# Staging - check nginx config
docker compose -f docker-compose.staging.yml exec frontend cat /etc/nginx/conf.d/default.conf
```

### Problem: Hot reload not working (Local Dev)

**Backend**: Check uvicorn logs for reload messages:
```bash
make -f Makefile.dev dev-logs-backend | grep Reloading
```

**Frontend**: Check Vite dev server:
```bash
make -f Makefile.dev dev-logs-frontend
```

**Fix**: Restart the service:
```bash
make -f Makefile.dev dev-restart-backend
# or
make -f Makefile.dev dev-restart-frontend
```

## Migration Path

### Development → Staging → Railway

```bash
# 1. Develop locally
cd docker
make -f Makefile.dev dev-up
# ... make code changes ...
make -f Makefile.dev dev-test-backend

# 2. Test in staging
cp .env.staging.example .env.staging
vim .env.staging  # Set production-like values
./validate.sh
make build && make up
# ... run integration tests ...

# 3. Deploy to Railway (existing process)
cd ../backend
railway up
cd ../frontend
npm run build
wrangler pages deploy dist
```

## Best Practices

### For Local Development

1. ✅ Use dev environment for all coding work
2. ✅ Commit often, push to feature branches
3. ✅ Run tests before committing: `make -f Makefile.dev dev-test-backend`
4. ✅ Seed database for consistent state: `make -f Makefile.dev dev-seed`
5. ❌ Don't use staging for active development (too slow)

### For Staging

1. ✅ Use for QA and integration testing
2. ✅ Mirror production configuration as closely as possible
3. ✅ Always validate before deploying: `./validate.sh`
4. ✅ Backup before major changes: `make backup`
5. ✅ Use strong passwords and real API keys
6. ❌ Don't commit `.env.staging` (contains secrets)

## Performance Tips

### Speed Up Local Development

```bash
# Use builder cache
docker builder prune --filter="until=24h"

# Stop services when not needed
make -f Makefile.dev dev-down

# Check resource usage
make -f Makefile.dev dev-stats
```

### Optimize Staging Builds

```bash
# Parallel builds
make build  # Already uses --parallel

# Update base images
make update

# Clean old images
make clean
```

## Getting Help

### Documentation

| Question | Document |
|----------|----------|
| How do I develop locally? | [README_LOCAL_DEV.md](./README_LOCAL_DEV.md) |
| How do I deploy staging? | [README.md](./README.md) |
| Quick staging setup? | [QUICKSTART.md](./QUICKSTART.md) |
| What are all these files? | [INDEX.md](./INDEX.md) |
| Technical architecture? | [SUMMARY.md](./SUMMARY.md) |

### Common Issues

```bash
# View all commands
make -f Makefile.dev help  # Local dev
make help                   # Staging

# Check service status
make -f Makefile.dev dev-health
make health

# View logs
make -f Makefile.dev dev-logs
make logs
```

### Still Stuck?

1. Check logs first
2. Review environment variables
3. Verify Docker is running and has resources
4. Consult project CLAUDE.md
5. Contact: bogdan@codeswiftr.com

## Summary

**For daily development**: Use `docker-compose.yml` with `Makefile.dev`
```bash
make -f Makefile.dev dev-up
# ... develop with hot-reload ...
make -f Makefile.dev dev-down
```

**For staging testing**: Use `docker-compose.staging.yml` with `Makefile`
```bash
cp .env.staging.example .env.staging
vim .env.staging
./validate.sh
make build && make up
# ... test thoroughly ...
make down
```

---

Built following FORGE standards for developer experience and operational excellence.
