# path: Makefile
# version: 5.2 - ADDED: rebuild-frontend and rebuild-backend commands for independent rebuilds
#
# Development environment
# Production: Kubernetes

.PHONY: help up down logs clean rebuild rebuild-frontend rebuild-backend rebuild-all clean-images

.DEFAULT_GOAL := help

help: ## Show help
	@echo "Development Commands:"
	@echo "  make up                  - Start services"
	@echo "  make down                - Stop services"
	@echo "  make logs                - Show logs"
	@echo "  make restart             - Restart services"
	@echo "  make clean               - Remove containers"
	@echo "  make rebuild             - Rebuild frontend + backend (delete old images + no cache)"
	@echo "  make rebuild-frontend    - Rebuild frontend only (delete old image + no cache)"
	@echo "  make rebuild-backend     - Rebuild backend only (delete old image + no cache)"
	@echo "  make rebuild-all         - Rebuild all services (delete old images + no cache)"
	@echo "  make clean-images        - Remove all project images"
	@echo ""
	@echo "URLs:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  ArangoDB:  http://localhost:8529 (root/changeme)"
	@echo "  MinIO:     http://localhost:9001 (minioadmin/minioadmin)"
	@echo ""

up: ## Start services
	docker-compose up -d
	@echo "✅ Services started"

down: ## Stop services
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

restart: ## Restart services
	docker-compose restart

clean: ## Remove containers and volumes
	docker-compose down -v

rebuild: ## Rebuild frontend + backend (delete old images + no cache)
	@echo "🛑 Stopping frontend and backend..."
	@docker-compose stop frontend backend
	@echo "🗑️  Removing frontend and backend containers..."
	@docker-compose rm -f frontend backend
	@echo "🗑️  Removing frontend and backend images..."
	@docker rmi simplehybridchat-main-backend:latest 2>/dev/null || echo "No backend image found"
	@docker rmi simplehybridchat-main-frontend:latest 2>/dev/null || echo "No frontend image found"
	@echo "🔨 Building frontend and backend (no cache)..."
	@docker-compose build --no-cache backend
	@docker-compose build --no-cache frontend
	@echo "🚀 Starting frontend and backend..."
	@docker-compose up -d frontend backend
	@echo "✅ Frontend and backend rebuilt successfully"
	@echo "📋 Checking logs (wait 3 seconds)..."
	@sleep 3
	@docker-compose logs --tail=30 backend frontend

rebuild-frontend: ## Rebuild frontend only (delete old image + no cache)
	@echo "🛑 Stopping frontend..."
	@docker-compose stop frontend
	@echo "🗑️  Removing frontend container..."
	@docker-compose rm -f frontend
	@echo "🗑️  Removing frontend image..."
	@docker rmi simplehybridchat-main-frontend:latest 2>/dev/null || echo "No frontend image found"
	@echo "🔨 Building frontend (no cache)..."
	@docker-compose build --no-cache frontend
	@echo "🚀 Starting frontend..."
	@docker-compose up -d frontend
	@echo "✅ Frontend rebuilt successfully"
	@echo "📋 Checking logs (wait 3 seconds)..."
	@sleep 3
	@docker-compose logs --tail=30 frontend

rebuild-backend: ## Rebuild backend only (delete old image + no cache)
	@echo "🛑 Stopping backend..."
	@docker-compose stop backend
	@echo "🗑️  Removing backend container..."
	@docker-compose rm -f backend
	@echo "🗑️  Removing backend image..."
	@docker rmi simplehybridchat-main-backend:latest 2>/dev/null || echo "No backend image found"
	@echo "🔨 Building backend (no cache)..."
	@docker-compose build --no-cache backend
	@echo "🚀 Starting backend..."
	@docker-compose up -d backend
	@echo "✅ Backend rebuilt successfully"
	@echo "📋 Checking logs (wait 3 seconds)..."
	@sleep 3
	@docker-compose logs --tail=30 backend

rebuild-all: ## Rebuild all services (delete old images + no cache)
	@echo "🛑 Stopping all services..."
	@docker-compose down
	@echo "🗑️  Removing all project images..."
	@docker images --filter "reference=simplehybridchat*" --format "{{.ID}}" | xargs -r docker rmi -f
	@echo "🔨 Building all services (no cache)..."
	@docker-compose build --no-cache
	@echo "🚀 Starting all services..."
	@docker-compose up -d
	@echo "✅ All services rebuilt successfully"

clean-images: ## Remove all project images
	@echo "🗑️  Removing all project images..."
	@docker images --filter "reference=simplehybridchat*" --format "{{.ID}}" | xargs -r docker rmi -f
	@echo "✅ Images removed"