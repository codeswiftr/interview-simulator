# Quick Start Guide - Interview Simulator Staging

5-minute guide to get the staging environment running.

## Prerequisites

- Docker 24+ and Docker Compose v2
- 4GB RAM available
- 10GB disk space

## Step 1: Environment Setup (2 minutes)

```bash
cd docker

# Copy environment template
cp .env.staging.example .env.staging

# Edit with your values
nano .env.staging  # or vim, code, etc.
```

**Minimum required changes in `.env.staging`:**

```bash
# Generate with: openssl rand -hex 32
POSTGRES_PASSWORD=your_32_char_password_here
REDIS_PASSWORD=your_32_char_password_here
SECRET_KEY=your_32_char_secret_here

# AI Services (choose one for each)
GROQ_API_KEY=gsk_...              # For transcription
OPENROUTER_API_KEY=sk-or-...     # For AI feedback

# Email (for password reset)
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=hello@yourdomain.com

# Frontend URL
FRONTEND_URL=http://your-staging-domain.com
VITE_API_URL=http://your-staging-domain.com/api/v1
```

## Step 2: Validate Configuration (30 seconds)

```bash
./validate.sh
```

If validation fails, fix the errors shown and run again.

## Step 3: Build and Deploy (2 minutes)

```bash
# Build all images
make build

# Start all services
make up

# Check health
make health
```

## Step 4: Verify (30 seconds)

Open in browser:
- Frontend: http://localhost
- Backend API: http://localhost:8000/docs (if DEBUG=true)
- Health check: http://localhost/health

Or use curl:
```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Frontend health
curl http://localhost/health
```

## Common Commands

```bash
# View logs
make logs                 # All services
make logs-backend        # Backend only
make logs-frontend       # Frontend only

# Restart services
make restart             # All services
make restart-backend     # Backend only

# Database operations
make migrate             # Run migrations
make seed               # Seed initial data
make backup             # Create backup
make shell-db           # PostgreSQL shell

# Stop everything
make down               # Stop services
make down-volumes       # Stop and delete data (DESTRUCTIVE!)
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
make logs-backend

# Common fixes:
# 1. Wait for database to be ready (30s)
# 2. Check environment variables
# 3. Verify API keys are set
```

### Frontend shows 404 for API calls
```bash
# Verify backend is accessible
docker compose -f docker-compose.staging.yml exec frontend curl http://backend:8000/api/v1/health

# Check nginx config
make logs-frontend
```

### Database connection errors
```bash
# Verify database is running
make ps

# Test connection
make shell-backend
# Inside container:
python -c "from app.db import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"
```

## Next Steps

After successful deployment:

1. **SSL/TLS**: Configure HTTPS in nginx-site.conf
2. **Domain**: Point your domain to the server
3. **Monitoring**: Set up health checks and alerting
4. **Backups**: Schedule automated database backups
5. **Review**: Check README.md for detailed documentation

## Emergency Commands

```bash
# Everything broken? Reset completely
make down-volumes
make clean
make build
make up

# Out of disk space?
docker system prune -af

# Memory issues?
docker stats  # Check usage
# Adjust limits in docker-compose.staging.yml
```

## Getting Help

1. Check logs: `make logs`
2. Review README.md for detailed docs
3. Check project CLAUDE.md
4. Contact: bogdan@codeswiftr.com

---

For detailed documentation, see [README.md](./README.md)
