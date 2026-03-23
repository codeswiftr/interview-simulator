# Interview Simulator Development Commands
# Usage: make <target>

.PHONY: help context install dev test lint clean db-up db-down db-reset seed migrate backend frontend

# Default target
help:
	@echo "Interview Simulator - Development Commands"
	@echo ""
	@echo "Context:"
	@echo "  make context     Print repo context (docs + git)"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install all dependencies (backend + frontend)"
	@echo "  make setup       Full setup: install, start db, migrate, seed"
	@echo ""
	@echo "Development:"
	@echo "  make dev         Start both backend and frontend (requires 2 terminals)"
	@echo "  make backend     Start backend server with hot reload"
	@echo "  make frontend    Start frontend dev server"
	@echo ""
	@echo "Database:"
	@echo "  make db-up       Start PostgreSQL and Redis containers"
	@echo "  make db-down     Stop database containers"
	@echo "  make db-reset    Reset database (delete all data)"
	@echo "  make migrate     Run database migrations"
	@echo "  make seed        Seed sample questions"
	@echo ""
	@echo "Testing:"
	@echo "  make test        Run all backend tests"
	@echo "  make test-cov    Run tests with coverage report"
	@echo "  make build       Build frontend for production"
	@echo ""
	@echo "Quality:"
	@echo "  make lint        Lint backend and frontend code"
	@echo "  make format      Format backend code"
	@echo "  make check       Run lint + tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       Remove generated files and caches"

# =============================================================================
# Context
# =============================================================================

context:
	@{ set +e; trap '' PIPE; \
		echo "=== Repo ==="; \
		echo "Path: $$(pwd)"; \
		echo "Branch: $$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"; \
		echo "Commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"; \
		echo ""; \
		echo "=== Active Context (docs/active-context.md) ==="; \
		sed -n '1,240p' docs/active-context.md 2>/dev/null || echo "Missing: docs/active-context.md"; \
		echo ""; \
		echo "=== Tech Context (docs/tech-context.md) ==="; \
		sed -n '1,240p' docs/tech-context.md 2>/dev/null || echo "Missing: docs/tech-context.md"; \
		echo ""; \
		echo "=== Plan (docs/PLAN.md) ==="; \
		sed -n '1,120p' docs/PLAN.md 2>/dev/null || echo "Missing: docs/PLAN.md"; \
		exit 0; } 2>/dev/null

# =============================================================================
# Setup
# =============================================================================

install:
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done! Run 'make setup' for full setup or 'make dev' to start."

setup: install db-up
	@echo "Waiting for database to be ready..."
	@sleep 3
	@$(MAKE) migrate
	@$(MAKE) seed
	@echo ""
	@echo "Setup complete! Run 'make backend' and 'make frontend' in separate terminals."

# =============================================================================
# Development
# =============================================================================

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"
	@echo ""
	@echo "Or run: make dev-backend & make dev-frontend"

backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# =============================================================================
# Database
# =============================================================================

db-up:
	docker compose up -d
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d
	@echo "Waiting for database to be ready..."
	@sleep 3
	@$(MAKE) migrate
	@$(MAKE) seed
	@echo "Database reset complete."

migrate:
	cd backend && uv run alembic upgrade head

seed:
	cd backend && uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
	@echo "Seeded sample questions."

# =============================================================================
# Testing
# =============================================================================

test:
	cd backend && uv run pytest -q

test-cov:
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: backend/htmlcov/index.html"

build:
	cd frontend && npm run build
	@echo "Frontend build: frontend/dist/"

# =============================================================================
# Quality
# =============================================================================

lint:
	@echo "Linting backend..."
	cd backend && uv run ruff check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	cd backend && uv run ruff format .
	cd backend && uv run ruff check --fix .

check: lint test
	@echo "All checks passed!"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning up..."
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf backend/.coverage
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."
