# Makefile for Awesome Docify

# Variables
BACKEND_DIR=fastapi_backend
FRONTEND_DIR=nextjs-frontend
DOCKER_COMPOSE=docker compose

# Help
.PHONY: help
help:
	@echo "Available commands:"
	@awk '/^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | head -10

# Development commands
.PHONY: install start-backend start-frontend dev

install: ## Install all dependencies
	cd $(BACKEND_DIR) && uv sync
	cd $(FRONTEND_DIR) && pnpm install

start-backend: ## Start backend server locally
	cd $(BACKEND_DIR) && ./start.sh

start-frontend: ## Start frontend server locally
	cd $(FRONTEND_DIR) && npm run dev

# Docker commands
.PHONY: docker-up docker-down docker-build docker-logs docker-status

docker-up: ## Start all services with Docker Compose
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down

docker-build: ## Build Docker images
	$(DOCKER_COMPOSE) build

docker-logs: ## Show Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-status: ## Show Docker status
	$(DOCKER_COMPOSE) ps
