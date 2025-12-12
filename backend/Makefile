# path: Makefile
# version: 3.0
#
# Development environment
# Production: Kubernetes

.PHONY: help up down logs clean

.DEFAULT_GOAL := help

help: ## Show help
	@echo "Development Commands:"
	@echo "  make up      - Start services"
	@echo "  make down    - Stop services"
	@echo "  make logs    - Show logs"
	@echo "  make restart - Restart services"
	@echo "  make clean   - Remove containers"
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