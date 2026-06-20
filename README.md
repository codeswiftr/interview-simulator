# CareerSwiftr Interview Simulator

AI-powered interview practice platform for software engineers. Practice behavioral and technical interviews with real-time audio analysis and AI-generated feedback.

## Current Status

Interview Simulator is a public product/codebase for AI-assisted interview
practice. The free-tier product surface is live, while the paid upgrade path
and Stripe Team tier remain under verification. Treat the deployment and
revenue docs in `docs/` as historical operating records unless a current
checklist says otherwise.

## Quick Start (5 minutes)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Node.js 18+](https://nodejs.org/)

### 1. Clone and Setup

```bash
git clone https://github.com/codeswiftr/interview-simulator.git
cd interview-simulator
```

### 2. Start Database

```bash
docker compose up -d
```

This starts PostgreSQL on port 5432 and Redis on port 6379.

### 3. Backend Setup

```bash
cd backend

# Create environment file
cp .env.example .env

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Seed sample questions
uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"

# Start backend server
uv run uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000 (API docs at http://localhost:8000/docs)

### 4. Frontend Setup (new terminal)

```bash
cd frontend

# Create environment file
cp .env.example .env

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at http://localhost:5173

### 5. Test It Works

1. Open http://localhost:5173
2. Register a new account
3. Create an interview session
4. Answer questions with audio recording
5. View AI-generated feedback

---

## Development Commands

### Backend

```bash
cd backend

# Run server with hot reload
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy app

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Reset database (delete all data)
docker compose down -v
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/interview_simulator` |
| `SECRET_KEY` | Yes | JWT signing key (32+ chars) | Dev key provided |
| `OPENAI_API_KEY` | For transcription | OpenAI API key for Whisper | - |
| `ANTHROPIC_API_KEY` | For AI feedback | Anthropic API key for Claude | - |
| `STRIPE_SECRET_KEY` | For payments | Stripe secret key | - |
| `STRIPE_WEBHOOK_SECRET` | For payments | Stripe webhook signing secret | - |
| `STRIPE_PRICE_ID_PRO_MONTHLY` | For payments | Stripe price ID | - |
| `DEBUG` | No | Enable debug mode | `true` |
| `CORS_ORIGINS` | No | Allowed CORS origins (JSON array) | `["http://localhost:3000", "http://localhost:5173"]` |

### Frontend (`frontend/.env`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `VITE_API_URL` | No | Backend API URL | `http://localhost:8000/api/v1` |

---

## Project Structure

```
interview-simulator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # SQLModel database models
│   │   ├── services/       # Business logic
│   │   ├── ai/             # AI integration (Whisper, Claude)
│   │   └── middleware/     # Custom middleware
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest tests
│   └── uploads/            # Audio file storage
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # API client, utilities
│   │   └── types/          # TypeScript definitions
│   └── public/             # Static assets
├── docs/                   # Documentation
│   ├── PLAN.md            # Sprint planning
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── DESIGN_SYSTEM.md   # UI design specs
└── docker-compose.yml      # Local services
```

---

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Create new user account |
| `POST /api/v1/auth/login` | Login and get JWT token |
| `GET /api/v1/auth/me` | Get current user info |
| `GET /api/v1/interviews` | List user's interview sessions |
| `POST /api/v1/interviews` | Create new interview session |
| `POST /api/v1/interviews/{id}/start` | Start interview |
| `POST /api/v1/interviews/{id}/responses` | Submit answer (with audio) |
| `POST /api/v1/interviews/{id}/end` | End interview and trigger feedback |
| `GET /api/v1/feedback/session/{id}` | Get session feedback |
| `GET /api/v1/subscriptions/status` | Get subscription status |
| `POST /api/v1/subscriptions/checkout` | Create Stripe checkout session |

Full API documentation: http://localhost:8000/docs (when backend is running)

---

## Testing

### Run All Tests

```bash
# Backend tests (71 tests, ~73% coverage)
cd backend && uv run pytest

# Frontend build check
cd frontend && npm run build
```

### Test Coverage Report

```bash
cd backend
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Common Issues

### Database connection failed

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart services
docker compose down && docker compose up -d

# Check logs
docker compose logs postgres
```

### "No questions found" when creating interview

```bash
# Seed the question database
cd backend
uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
```

### Audio transcription not working

- Ensure `OPENAI_API_KEY` is set in `backend/.env`
- Check you have API credits available
- Audio files must be in webm/mp3/wav format

### AI feedback not generating

- Ensure `ANTHROPIC_API_KEY` is set in `backend/.env`
- Check API key has valid credits

### CORS errors in browser

- Verify frontend URL is in `CORS_ORIGINS` in `backend/.env`
- Default: `["http://localhost:3000", "http://localhost:5173"]`

---

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115+
- **ORM**: SQLModel (async)
- **Database**: PostgreSQL 16+
- **Cache**: Redis 7+
- **AI**: OpenAI Whisper, Anthropic Claude
- **Audio**: Librosa for analysis
- **Payments**: Stripe

### Frontend
- **Framework**: React 19 + TypeScript
- **Build**: Vite 7
- **Styling**: TailwindCSS v4
- **Routing**: React Router v7
- **HTTP**: Axios

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions covering:
- Railway / Cloud Run / Render deployment
- Vercel / Netlify frontend hosting
- PostgreSQL database setup
- Stripe webhook configuration

---

## License

MIT - CodeSwiftr Interview Simulator
