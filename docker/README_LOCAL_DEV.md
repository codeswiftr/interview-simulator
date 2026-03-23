# Interview Simulator - Local Development with Docker

Complete Docker setup for local development with hot-reloading and debugging support.

## Overview

This configuration provides a full-stack local development environment with:

- **Backend**: FastAPI + Python 3.12 with hot-reloading
- **Frontend**: React 19 + Vite dev server with HMR
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Networking**: All services on shared bridge network

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Docker Network (app-network)            │
│                                                          │
│  ┌─────────────┐         ┌─────────────┐              │
│  │  Frontend   │         │   Backend   │              │
│  │  Vite HMR   │         │   FastAPI   │              │
│  │  :5173      │◄────────│   :8000     │              │
│  └─────────────┘         └──────┬──────┘              │
│                                  │                      │
│                          ┌───────┴────────┐            │
│                          │                │            │
│                     ┌────▼─────┐    ┌────▼─────┐      │
│                     │Postgres  │    │  Redis   │      │
│                     │  :5432   │    │  :6379   │      │
│                     └──────────┘    └──────────┘      │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Initialize Environment

```bash
cd docker
make -f Makefile.dev dev-init
```

This creates `.env` from `.env.example`. Edit `.env` to add API keys if needed (optional for basic development).

### 2. Start Development Environment

```bash
make -f Makefile.dev dev-up
```

This will:
- Build development images
- Start all services
- Run database migrations automatically
- Enable hot-reloading for code changes

### 3. Access Services

- **Frontend**: http://localhost:5173 (Vite dev server with HMR)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Database**: localhost:5432 (user: postgres, password: postgres)
- **Redis**: localhost:6379

### 4. View Logs

```bash
# All services
make -f Makefile.dev dev-logs

# Specific service
make -f Makefile.dev dev-logs-backend
make -f Makefile.dev dev-logs-frontend
```

## Development Workflow

### Hot Reloading

Both frontend and backend support hot-reloading:

**Frontend**: Changes to files in `frontend/src/` automatically reload in browser
**Backend**: Changes to files in `backend/app/` automatically restart the server

### Making Code Changes

1. Edit files in your local `frontend/src/` or `backend/app/` directories
2. Changes are automatically detected and applied
3. No need to rebuild containers for code changes

### Database Migrations

```bash
# Create new migration
cd ../backend
docker compose -f ../docker/docker-compose.yml exec backend alembic revision --autogenerate -m "description"

# Apply migrations
make -f Makefile.dev dev-migrate

# Rollback migration
make -f Makefile.dev dev-migrate-rollback
```

### Seed Database

```bash
make -f Makefile.dev dev-seed
```

### Running Tests

```bash
# Backend tests
make -f Makefile.dev dev-test-backend

# Backend tests with coverage
make -f Makefile.dev dev-test-backend-coverage
```

## Common Commands

| Command | Description |
|---------|-------------|
| `make -f Makefile.dev dev-up` | Start development environment |
| `make -f Makefile.dev dev-down` | Stop development environment |
| `make -f Makefile.dev dev-restart` | Restart all services |
| `make -f Makefile.dev dev-logs` | View logs from all services |
| `make -f Makefile.dev dev-shell-backend` | Open shell in backend container |
| `make -f Makefile.dev dev-shell-db` | Open PostgreSQL shell |
| `make -f Makefile.dev dev-health` | Check service health |
| `make -f Makefile.dev dev-clean` | Remove containers and volumes |

## Environment Variables

The `.env` file contains all configuration. Key variables:

### Required for Basic Development
```bash
POSTGRES_PASSWORD=postgres      # Database password
SECRET_KEY=dev_secret_key...    # JWT secret (dev default provided)
```

### Optional (for full functionality)
```bash
# AI Services
GROQ_API_KEY=gsk_...            # For audio transcription
OPENROUTER_API_KEY=sk-or-...    # For AI feedback

# Email (for password reset)
RESEND_API_KEY=re_...

# Payments (for subscription features)
STRIPE_SECRET_KEY=sk_test_...
```

## Service Details

### Backend (Development Mode)

- **Port**: 8000
- **Reload**: Enabled (uvicorn --reload)
- **Workers**: 1 (for debugging)
- **Debug Mode**: Enabled
- **Source Mount**: `backend/app/` → `/app/app` (read-only)
- **Logs**: Verbose with DEBUG level

### Frontend (Development Mode)

- **Port**: 5173
- **Dev Server**: Vite with HMR
- **Source Mount**: `frontend/src/` → `/app/src` (read-only)
- **Node Modules**: Cached in anonymous volume for performance

### PostgreSQL

- **Port**: 5432
- **User**: postgres
- **Password**: postgres (configurable in .env)
- **Database**: interview_simulator
- **Extensions**: UUID, pg_trgm

### Redis

- **Port**: 6379
- **Max Memory**: 128MB (LRU eviction)
- **Persistence**: Enabled (60s snapshots)

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
make -f Makefile.dev dev-logs-backend

# Common issues:
# 1. Database not ready - wait 10s and restart
# 2. Port 8000 in use - check .env BACKEND_PORT
# 3. Migration errors - check database connection
```

### Frontend Shows Connection Error

```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend logs
make -f Makefile.dev dev-logs-backend | grep CORS

# Ensure VITE_API_URL is correct in .env
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
make -f Makefile.dev dev-ps

# Test connection from backend
make -f Makefile.dev dev-shell-backend
python -c "from app.db import engine; print(engine)"
```

### Hot Reload Not Working

**Backend**: Ensure files are saved. Check if uvicorn detected changes in logs:
```bash
make -f Makefile.dev dev-logs-backend | grep "Reloading"
```

**Frontend**: Ensure Vite dev server is running and browser has no cache issues:
```bash
make -f Makefile.dev dev-logs-frontend
```

### Permission Errors

```bash
# Fix uploads directory
docker compose -f docker-compose.yml exec backend chown -R app:app /app/uploads
```

## Differences from Staging

| Feature | Local Development | Staging |
|---------|------------------|---------|
| Frontend Server | Vite dev server (:5173) | Nginx production (:80) |
| Backend Workers | 1 (with reload) | 2 (production mode) |
| Debug Mode | Enabled | Disabled |
| CORS | Permissive | Restricted |
| Resource Limits | Relaxed | Enforced (CPU/RAM) |
| Secrets | Dev defaults | Strong passwords required |
| SSL/TLS | Not enabled | Can be enabled |
| Logging | DEBUG level | INFO/WARNING level |

## Performance Tips

### Speed Up Builds

```bash
# Use builder cache
make -f Makefile.dev dev-build

# Clear cache only when needed
docker builder prune
```

### Reduce Disk Usage

```bash
# Remove unused images/containers
docker system prune

# Remove all (including volumes - WARNING: deletes data!)
make -f Makefile.dev dev-clean-all
```

### Check Resource Usage

```bash
make -f Makefile.dev dev-stats
```

## Integration with IDE

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "/app/.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "ruff"
}
```

### PyCharm

1. Configure Python interpreter: Docker Compose → backend service
2. Set working directory: `/app`
3. Enable Django support for better FastAPI support

## Next Steps

After getting the local environment running:

1. **Explore API**: Visit http://localhost:8000/docs
2. **Make Changes**: Edit code and see hot-reload in action
3. **Run Tests**: `make -f Makefile.dev dev-test-backend`
4. **Seed Data**: `make -f Makefile.dev dev-seed`
5. **Deploy to Staging**: See [README.md](./README.md) for staging deployment

## Support

**Documentation**:
- Staging deployment: [README.md](./README.md)
- Quick start: [QUICKSTART.md](./QUICKSTART.md)
- Project rules: [../CLAUDE.md](../CLAUDE.md)

**Contact**: bogdan@codeswiftr.com

---

Built following FORGE standards for developer experience.
