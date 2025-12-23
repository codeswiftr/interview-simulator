# =============================================================================
# Interview Simulator - Docker Staging Environment Makefile
# Convenience commands for managing the staging environment
# =============================================================================

.PHONY: help validate build up down restart logs logs-backend logs-frontend logs-db health shell-backend shell-db backup restore clean

# Default target
.DEFAULT_GOAL := help

# Environment file
ENV_FILE := .env.staging
COMPOSE := docker compose -f docker-compose.staging.yml --env-file $(ENV_FILE)

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Interview Simulator - Docker Staging Environment$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick start:$(NC)"
	@echo "  1. cp .env.staging.example .env.staging"
	@echo "  2. Edit .env.staging with your values"
	@echo "  3. make validate"
	@echo "  4. make build"
	@echo "  5. make up"
	@echo ""

validate: ## Validate environment configuration
	@echo "$(CYAN)Validating configuration...$(NC)"
	@./validate.sh

build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	$(COMPOSE) build --parallel

build-backend: ## Build backend image only
	@echo "$(CYAN)Building backend image...$(NC)"
	$(COMPOSE) build backend

build-frontend: ## Build frontend image only
	@echo "$(CYAN)Building frontend image...$(NC)"
	$(COMPOSE) build frontend

build-no-cache: ## Build all images without cache
	@echo "$(CYAN)Building images without cache...$(NC)"
	$(COMPOSE) build --no-cache --parallel

up: ## Start all services
	@echo "$(CYAN)Starting services...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Run 'make health' to check status$(NC)"

down: ## Stop all services
	@echo "$(CYAN)Stopping services...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)Services stopped!$(NC)"

down-volumes: ## Stop all services and remove volumes (WARNING: deletes data!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		echo "$(GREEN)Services and volumes removed!$(NC)"; \
	fi

restart: ## Restart all services
	@echo "$(CYAN)Restarting services...$(NC)"
	$(COMPOSE) restart
	@echo "$(GREEN)Services restarted!$(NC)"

restart-backend: ## Restart backend service only
	@echo "$(CYAN)Restarting backend...$(NC)"
	$(COMPOSE) restart backend
	@echo "$(GREEN)Backend restarted!$(NC)"

restart-frontend: ## Restart frontend service only
	@echo "$(CYAN)Restarting frontend...$(NC)"
	$(COMPOSE) restart frontend
	@echo "$(GREEN)Frontend restarted!$(NC)"

logs: ## View logs from all services
	$(COMPOSE) logs -f

logs-backend: ## View backend logs
	$(COMPOSE) logs -f backend

logs-frontend: ## View frontend logs
	$(COMPOSE) logs -f frontend

logs-db: ## View database logs
	$(COMPOSE) logs -f postgres

logs-redis: ## View Redis logs
	$(COMPOSE) logs -f redis

ps: ## Show running containers
	$(COMPOSE) ps

health: ## Check health of all services
	@echo "$(CYAN)Checking service health...$(NC)"
	@echo ""
	@$(COMPOSE) ps
	@echo ""
	@echo "$(CYAN)Backend health:$(NC)"
	@curl -s http://localhost:8000/api/v1/health | python3 -m json.tool || echo "$(RED)Backend not responding$(NC)"
	@echo ""
	@echo "$(CYAN)Frontend health:$(NC)"
	@curl -s http://localhost/health || echo "$(RED)Frontend not responding$(NC)"
	@echo ""

shell-backend: ## Open shell in backend container
	$(COMPOSE) exec backend /bin/sh

shell-frontend: ## Open shell in frontend container
	$(COMPOSE) exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	$(COMPOSE) exec postgres psql -U postgres -d interview_simulator_staging

shell-redis: ## Open Redis CLI
	@echo "$(YELLOW)Enter Redis password from .env.staging$(NC)"
	$(COMPOSE) exec redis redis-cli

migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	$(COMPOSE) exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

migrate-rollback: ## Rollback last migration
	@echo "$(CYAN)Rolling back last migration...$(NC)"
	$(COMPOSE) exec backend alembic downgrade -1
	@echo "$(GREEN)Rollback complete!$(NC)"

migrate-status: ## Show migration status
	$(COMPOSE) exec backend alembic current

seed: ## Seed database with initial data
	@echo "$(CYAN)Seeding database...$(NC)"
	$(COMPOSE) exec backend python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
	@echo "$(GREEN)Database seeded!$(NC)"

backup: ## Backup database
	@echo "$(CYAN)Creating database backup...$(NC)"
	@mkdir -p ./backups
	@$(COMPOSE) exec -T postgres pg_dump -U postgres interview_simulator_staging > ./backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in ./backups/$(NC)"

restore: ## Restore database from backup (specify FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)ERROR: Please specify backup file with FILE=path/to/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(CYAN)Restoring database from $(FILE)...$(NC)"
	@cat $(FILE) | $(COMPOSE) exec -T postgres psql -U postgres interview_simulator_staging
	@echo "$(GREEN)Database restored!$(NC)"

stats: ## Show container resource usage
	docker stats --no-stream

clean: ## Remove stopped containers and unused images
	@echo "$(CYAN)Cleaning up Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: ## Remove all containers, images, and volumes (WARNING: destructive!)
	@echo "$(RED)WARNING: This will remove all Docker resources!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v; \
		docker system prune -af --volumes; \
		echo "$(GREEN)All resources removed!$(NC)"; \
	fi

update: ## Pull latest base images and rebuild
	@echo "$(CYAN)Pulling latest base images...$(NC)"
	docker pull python:3.12-slim
	docker pull node:22-alpine
	docker pull nginx:1.27-alpine
	docker pull postgres:16-alpine
	docker pull redis:7-alpine
	@echo "$(GREEN)Base images updated! Run 'make build' to rebuild.$(NC)"
