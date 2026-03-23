# Docker Configuration - File Index

Quick reference guide to all Docker configuration files.

## Start Here

| File | Purpose | When to Use |
|------|---------|-------------|
| [README_LOCAL_DEV.md](./README_LOCAL_DEV.md) | Local development setup | Development workflow |
| [QUICKSTART.md](./QUICKSTART.md) | 5-minute staging deployment | First time staging setup |
| [README.md](./README.md) | Staging environment docs | Detailed staging reference |
| [SUMMARY.md](./SUMMARY.md) | Implementation summary | Understanding the setup |

## Configuration Files

### Docker Images

| File | Service | Description |
|------|---------|-------------|
| [Dockerfile.backend](./Dockerfile.backend) | Backend | FastAPI + Python 3.12 with uv (production) |
| [Dockerfile.frontend](./Dockerfile.frontend) | Frontend | React 19 + Vite → Nginx (production) |
| [Dockerfile.frontend.dev](./Dockerfile.frontend.dev) | Frontend | Vite dev server with HMR (development) |

### Orchestration

| File | Purpose |
|------|---------|
| [docker-compose.yml](./docker-compose.yml) | Local development environment |
| [docker-compose.staging.yml](./docker-compose.staging.yml) | Staging environment |

### Web Server

| File | Purpose |
|------|---------|
| [nginx.conf](./nginx.conf) | Main Nginx configuration |
| [nginx-site.conf](./nginx-site.conf) | Site-specific config (proxy, caching, SPA routing) |

### Database

| File | Purpose |
|------|---------|
| [init-db.sh](./init-db.sh) | PostgreSQL initialization and tuning |

### Environment

| File | Purpose |
|------|---------|
| [.env.example](./.env.example) | Local development env template |
| [.env.staging.example](./.env.staging.example) | Staging environment template |
| [.gitignore](./.gitignore) | Git exclusions for secrets |

## Automation Tools

| File | Purpose | Usage |
|------|---------|-------|
| [Makefile.dev](./Makefile.dev) | Local development commands | `make -f Makefile.dev help` |
| [Makefile](./Makefile) | Staging environment commands | `make help` |
| [validate.sh](./validate.sh) | Pre-deployment validation | `./validate.sh` |

## Documentation

| File | Audience | Content |
|------|----------|---------|
| [README_LOCAL_DEV.md](./README_LOCAL_DEV.md) | Developers | Local development guide |
| [QUICKSTART.md](./QUICKSTART.md) | New users | Fast staging setup (5 min) |
| [README.md](./README.md) | Operators | Staging environment guide |
| [SUMMARY.md](./SUMMARY.md) | Architects | Technical details |
| [INDEX.md](./INDEX.md) | Everyone | This file |

## Quick Commands Reference

### Local Development
```bash
# Setup
cd docker
cp .env.example .env
make -f Makefile.dev dev-up

# Daily operations
make -f Makefile.dev dev-logs          # View logs
make -f Makefile.dev dev-restart       # Restart all
make -f Makefile.dev dev-test-backend  # Run tests

# Cleanup
make -f Makefile.dev dev-down          # Stop services
```

### Staging Environment
```bash
# Setup
cp .env.staging.example .env.staging
./validate.sh
make build
make up

# Daily operations
make logs              # View logs
make restart           # Restart all
make health            # Check health
make backup            # Backup database

# Cleanup
make down              # Stop services
```

## File Tree

```
docker/
├── README_LOCAL_DEV.md            # Local development guide
├── README.md                      # Staging environment guide
├── QUICKSTART.md                  # 5-minute staging guide
├── SUMMARY.md                     # Implementation summary
├── INDEX.md                       # This file
│
├── Dockerfile.backend             # Backend image (production)
├── Dockerfile.frontend            # Frontend image (production)
├── Dockerfile.frontend.dev        # Frontend image (development)
│
├── docker-compose.yml             # Local development orchestration
├── docker-compose.staging.yml     # Staging orchestration
│
├── nginx.conf                     # Nginx main config
├── nginx-site.conf                # Nginx site config
│
├── init-db.sh                     # Database init
│
├── .env.example                   # Local development env template
├── .env.staging.example           # Staging env template
├── .gitignore                     # Git exclusions
│
├── Makefile.dev                   # Local development commands
├── Makefile                       # Staging environment commands
└── validate.sh                    # Config validation
```

## Architecture Overview

```
┌─────────────────────────────────────┐
│  Frontend (Nginx) :80               │
│  ├── Static files (cached 1y)      │
│  ├── /api/* → Backend proxy        │
│  └── SPA routing → index.html      │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  Backend (FastAPI) :8000            │
│  ├── 2 Uvicorn workers              │
│  ├── JWT authentication             │
│  ├── AI integrations (Whisper + Claude) │
│  └── Auto-migrations on startup     │
└────────────┬────────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼─────┐    ┌────▼─────┐
│PostgreSQL│    │  Redis   │
│  :5432   │    │  :6379   │
│ 1GB RAM  │    │ 512MB RAM│
└──────────┘    └──────────┘
```

## Resource Allocation

| Service | CPU | RAM | Storage |
|---------|-----|-----|---------|
| Backend | 1 core | 1GB | Minimal |
| Frontend | 0.5 core | 512MB | ~50MB |
| PostgreSQL | 1 core | 1GB | 5-20GB (data) |
| Redis | 0.5 core | 512MB | ~100MB |
| **Total** | **3 cores** | **3GB** | **~20GB** |

## Security Checklist

- [ ] Strong passwords (32+ chars) in `.env.staging`
- [ ] Secret key generated with `openssl rand -hex 32`
- [ ] API keys from secure sources (not shared)
- [ ] `.env.staging` in `.gitignore`
- [ ] Non-root containers verified
- [ ] CORS origins properly restricted
- [ ] Rate limiting enabled
- [ ] Health checks configured
- [ ] Logs reviewed for sensitive data

## Support

**Primary**: [README.md](./README.md) - Comprehensive troubleshooting
**Quick**: [QUICKSTART.md](./QUICKSTART.md) - Common operations
**Deep**: [SUMMARY.md](./SUMMARY.md) - Technical architecture

**Project Documentation**: `../docs/`
**Project Rules**: `../CLAUDE.md`

**Contact**: bogdan@codeswiftr.com

---

Last updated: 2025-12-22
