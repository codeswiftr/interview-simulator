# Interview Simulator - Docker Staging Environment

Production-ready Docker configuration for the Interview Simulator staging environment.

## Overview

This directory contains optimized Docker configurations for deploying the Interview Simulator to a staging environment. The setup includes:

- **Backend**: FastAPI + Python 3.12 (using Astral `uv` for dependency management)
- **Frontend**: React 19 + Vite (served via Nginx)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Reverse Proxy**: Nginx with optimized caching and compression

## Architecture

```
┌─────────────────┐
│   Frontend      │  (Nginx on :80)
│   React + Vite  │
└────────┬────────┘
         │
         ├──► /api/* ──────┐
         │                 │
         │        ┌────────▼────────┐
         │        │   Backend       │  (:8000)
         │        │   FastAPI       │
         │        └────────┬────────┘
         │                 │
         │        ┌────────▼────────┐
         │        │   PostgreSQL    │  (:5432)
         │        └─────────────────┘
         │                 │
         │        ┌────────▼────────┐
         │        │   Redis         │  (:6379)
         │        └─────────────────┘
         │
         └──► Static Assets (cached)
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cd docker
cp .env.staging.example .env.staging

# Edit .env.staging and fill in all required values
# CRITICAL: Change all passwords and secrets!
vim .env.staging
```

**Required Environment Variables:**
- `POSTGRES_PASSWORD` - Database password (min 32 chars)
- `REDIS_PASSWORD` - Redis password (min 32 chars)
- `SECRET_KEY` - JWT secret (generate with: `openssl rand -hex 32`)
- `GROQ_API_KEY` or `OPENAI_API_KEY` - For transcription
- `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` - For AI feedback
- `RESEND_API_KEY` - For password reset emails
- `RESEND_FROM_EMAIL` - Must be from a verified domain

### 2. Build and Deploy

```bash
# Build all services
docker compose -f docker-compose.staging.yml --env-file .env.staging build

# Start all services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# View logs
docker compose -f docker-compose.staging.yml logs -f

# Check service health
docker compose -f docker-compose.staging.yml ps
```

### 3. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# Check frontend
curl http://localhost/

# Check database connection
docker compose -f docker-compose.staging.yml exec postgres psql -U postgres -d interview_simulator_staging -c "SELECT 1;"

# Check Redis
docker compose -f docker-compose.staging.yml exec redis redis-cli -a redis_staging_pass ping
```

## Service Details

### Backend (FastAPI)

- **Image**: Custom multi-stage build using Python 3.12 slim
- **Port**: 8000 (exposed)
- **Health Check**: `/api/v1/health`
- **Resource Limits**: 1 CPU, 1GB RAM
- **Features**:
  - Uses `uv` for fast dependency installation
  - Non-root user for security
  - Automatic database migrations on startup
  - 2 workers (configurable)
  - Structured JSON logging

**Logs:**
```bash
docker compose -f docker-compose.staging.yml logs -f backend
```

### Frontend (React + Nginx)

- **Image**: Multi-stage build (Node.js → Nginx)
- **Port**: 80 (exposed)
- **Resource Limits**: 0.5 CPU, 512MB RAM
- **Features**:
  - Optimized Vite production build
  - Gzip compression enabled
  - Aggressive caching for static assets
  - SPA fallback routing
  - Security headers configured
  - PWA support with offline mode

**Nginx Configuration:**
- Main config: `nginx.conf`
- Site config: `nginx-site.conf`
- API proxy: Forwards `/api/*` to backend
- Static caching: 1 year for immutable assets
- Rate limiting: Protects against abuse

### PostgreSQL 16

- **Image**: postgres:16-alpine
- **Port**: 5432 (exposed)
- **Resource Limits**: 1 CPU, 1GB RAM
- **Features**:
  - UTF-8 encoding
  - UUID extension enabled
  - pg_trgm for text search
  - Optimized for staging workload
  - Persistent volume storage
  - Automatic health checks

**Connection String:**
```
postgresql://postgres:PASSWORD@localhost:5432/interview_simulator_staging
```

### Redis 7

- **Image**: redis:7-alpine
- **Port**: 6379 (exposed)
- **Resource Limits**: 0.5 CPU, 512MB RAM
- **Features**:
  - Password authentication
  - LRU eviction policy (256MB max)
  - Periodic persistence (60s if 1 key changed)
  - Optimized for caching and rate limiting

## Common Operations

### Start Services

```bash
# Start all services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Start specific service
docker compose -f docker-compose.staging.yml up -d backend
```

### Stop Services

```bash
# Stop all services
docker compose -f docker-compose.staging.yml down

# Stop and remove volumes (WARNING: destroys data)
docker compose -f docker-compose.staging.yml down -v
```

### View Logs

```bash
# All services
docker compose -f docker-compose.staging.yml logs -f

# Specific service
docker compose -f docker-compose.staging.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.staging.yml logs --tail=100
```

### Execute Commands

```bash
# Backend shell
docker compose -f docker-compose.staging.yml exec backend /bin/sh

# Database shell
docker compose -f docker-compose.staging.yml exec postgres psql -U postgres -d interview_simulator_staging

# Redis CLI
docker compose -f docker-compose.staging.yml exec redis redis-cli -a YOUR_REDIS_PASSWORD

# Run backend migrations manually
docker compose -f docker-compose.staging.yml exec backend alembic upgrade head
```

### Rebuild Services

```bash
# Rebuild backend after code changes
docker compose -f docker-compose.staging.yml build backend
docker compose -f docker-compose.staging.yml up -d backend

# Rebuild frontend after code changes
docker compose -f docker-compose.staging.yml build --build-arg VITE_API_URL=http://api.staging.com/api/v1 frontend
docker compose -f docker-compose.staging.yml up -d frontend

# Rebuild all
docker compose -f docker-compose.staging.yml build --no-cache
```

## Database Operations

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.staging.yml exec -T postgres pg_dump -U postgres interview_simulator_staging > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup_20231215_143000.sql | docker compose -f docker-compose.staging.yml exec -T postgres psql -U postgres interview_simulator_staging
```

### Run Migrations

```bash
# Apply all pending migrations
docker compose -f docker-compose.staging.yml exec backend alembic upgrade head

# Rollback one migration
docker compose -f docker-compose.staging.yml exec backend alembic downgrade -1

# Check current migration
docker compose -f docker-compose.staging.yml exec backend alembic current
```

### Seed Data

```bash
# Seed questions (runs automatically in DEBUG mode)
docker compose -f docker-compose.staging.yml exec backend python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
```

## Monitoring

### Health Checks

```bash
# Check all service health
docker compose -f docker-compose.staging.yml ps

# Backend API health
curl http://localhost:8000/api/v1/health

# Frontend health
curl http://localhost/health

# Database health
docker compose -f docker-compose.staging.yml exec postgres pg_isready -U postgres

# Redis health
docker compose -f docker-compose.staging.yml exec redis redis-cli -a YOUR_REDIS_PASSWORD ping
```

### Resource Usage

```bash
# View container resource usage
docker stats

# View disk usage
docker system df

# View logs size
docker compose -f docker-compose.staging.yml exec backend du -sh /app/logs
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose -f docker-compose.staging.yml logs backend

# Common issues:
# 1. Database not ready - wait for postgres healthcheck
# 2. Missing environment variables - check .env.staging
# 3. Migration failures - check alembic logs
# 4. Port conflict - ensure 8000 is available
```

### Frontend Shows 404 for API Calls

```bash
# Check nginx configuration
docker compose -f docker-compose.staging.yml exec frontend cat /etc/nginx/conf.d/default.conf

# Verify backend is accessible
docker compose -f docker-compose.staging.yml exec frontend curl http://backend:8000/api/v1/health

# Check CORS settings in backend logs
docker compose -f docker-compose.staging.yml logs backend | grep CORS
```

### Database Connection Issues

```bash
# Verify postgres is running
docker compose -f docker-compose.staging.yml ps postgres

# Check connection from backend
docker compose -f docker-compose.staging.yml exec backend python -c "from app.db import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"

# Verify connection string
docker compose -f docker-compose.staging.yml exec backend env | grep DATABASE_URL
```

### Permission Errors

```bash
# Fix uploads directory permissions
docker compose -f docker-compose.staging.yml exec backend chown -R app:app /app/uploads

# Fix nginx permissions
docker compose -f docker-compose.staging.yml exec frontend chown -R nginx:nginx /usr/share/nginx/html
```

### Out of Memory

```bash
# Check current limits
docker compose -f docker-compose.staging.yml config

# Adjust in docker-compose.staging.yml under deploy.resources.limits
# Then recreate services
docker compose -f docker-compose.staging.yml up -d --force-recreate
```

### Slow Performance

```bash
# Check Redis cache hit rate
docker compose -f docker-compose.staging.yml exec redis redis-cli -a PASSWORD info stats | grep keyspace_hits

# Check database query performance
docker compose -f docker-compose.staging.yml exec postgres psql -U postgres -d interview_simulator_staging -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Monitor backend response times
docker compose -f docker-compose.staging.yml logs backend | grep "request_time"
```

## Security Considerations

### Secrets Management

- **Never commit** `.env.staging` to version control
- Use strong passwords (min 32 characters)
- Rotate secrets regularly
- Use environment-specific API keys (test keys for staging)

### Network Security

- Frontend and backend communicate over internal `app-network`
- Only necessary ports exposed to host
- Rate limiting enabled on nginx
- Security headers configured

### User Permissions

- Backend runs as non-root user `app` (UID 1001)
- Frontend runs as `nginx` user
- Database files owned by `postgres` user

## Production Deployment

For production deployment, consider these changes:

1. **SSL/TLS**: Enable HTTPS in nginx configuration
2. **Secrets**: Use Docker secrets or external vault (HashiCorp Vault, AWS Secrets Manager)
3. **Monitoring**: Add Prometheus, Grafana, or equivalent
4. **Logging**: Centralize logs (ELK stack, Loki, CloudWatch)
5. **Backups**: Automated database backups with retention policy
6. **Scaling**: Use Docker Swarm or Kubernetes for orchestration
7. **CDN**: Put Cloudflare or CloudFront in front of nginx
8. **Health Checks**: Configure external health monitoring (UptimeRobot, Pingdom)

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile.backend` | Multi-stage Python/FastAPI build with uv |
| `Dockerfile.frontend` | Multi-stage Node.js build + Nginx serve |
| `docker-compose.staging.yml` | Complete staging orchestration |
| `nginx.conf` | Main nginx configuration |
| `nginx-site.conf` | Site-specific nginx config (proxy, caching) |
| `.env.staging.example` | Environment variable template |
| `init-db.sh` | PostgreSQL initialization script |
| `README.md` | This file |

## Support

For issues or questions:
- Check logs first: `docker compose logs -f`
- Review CLAUDE.md in project root
- Consult main project documentation in `../docs/`
- Contact: bogdan@codeswiftr.com

---

Built with FORGE standards for CodeSwiftr domain.
