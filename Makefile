# path: Makefile
# version: 6.1
# Changes in v6.1:
# - Added build-images-kube command to build Docker images for Kubernetes
# - up-kube now builds images before deploying
# - Added REGISTRY and IMAGE_TAG variables for image configuration
#
# Development environment: Docker Compose
# Production: Kubernetes

# Kubernetes image configuration
REGISTRY ?= localhost:5000
IMAGE_TAG ?= latest
BACKEND_IMAGE = $(REGISTRY)/chatbot-backend:$(IMAGE_TAG)
FRONTEND_IMAGE = $(REGISTRY)/chatbot-frontend:$(IMAGE_TAG)

.PHONY: help up down logs clean rebuild rebuild-frontend rebuild-backend rebuild-all clean-images
.PHONY: up-kube down-kube logs-kube status-kube build-images-kube

.DEFAULT_GOAL := help

help: ## Show help
	@echo "Development Commands (Docker Compose):"
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
	@echo "Kubernetes Commands:"
	@echo "  make build-images-kube   - Build Docker images for Kubernetes"
	@echo "  make up-kube             - Build images + Deploy to Kubernetes"
	@echo "  make down-kube           - Remove from Kubernetes"
	@echo "  make status-kube         - Show Kubernetes deployment status"
	@echo "  make logs-kube           - Show Kubernetes pod logs"
	@echo ""
	@echo "Kubernetes Configuration:"
	@echo "  REGISTRY=<registry>      - Docker registry (default: localhost:5000)"
	@echo "  IMAGE_TAG=<tag>          - Image tag (default: latest)"
	@echo "  Example: make up-kube REGISTRY=myregistry.io IMAGE_TAG=v1.0.0"
	@echo ""
	@echo "URLs (Docker Compose):"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  ArangoDB:  http://localhost:8529 (root/changeme)"
	@echo "  MinIO:     http://localhost:9001 (minioadmin/minioadmin)"
	@echo ""
	@echo "URLs (Kubernetes):"
	@echo "  Application: http://app.domain.local (configure /etc/hosts)"
	@echo ""

# =============================================================================
# Docker Compose Commands
# =============================================================================

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

# =============================================================================
# Kubernetes Commands
# =============================================================================

build-images-kube: ## Build Docker images for Kubernetes
	@echo "🔨 Building backend image: $(BACKEND_IMAGE)"
	docker build -t $(BACKEND_IMAGE) ./backend
	@echo "✅ Backend image built"
	@echo ""
	@echo "🔨 Building frontend image: $(FRONTEND_IMAGE)"
	docker build -t $(FRONTEND_IMAGE) ./frontend
	@echo "✅ Frontend image built"
	@echo ""
	@echo "📦 Images created:"
	@echo "  Backend:  $(BACKEND_IMAGE)"
	@echo "  Frontend: $(FRONTEND_IMAGE)"
	@echo ""
	@if [ "$(REGISTRY)" != "localhost:5000" ] && [ "$(REGISTRY)" != "minikube" ] && [ "$(REGISTRY)" != "kind" ]; then \
		echo "💡 To push images to registry, run:"; \
		echo "  docker push $(BACKEND_IMAGE)"; \
		echo "  docker push $(FRONTEND_IMAGE)"; \
	fi

up-kube: build-images-kube ## Build images + Deploy to Kubernetes using kustomization.yaml
	@echo ""
	@echo "🔄 Updating deployment images..."
	@sed -i.bak "s|image:.*chatbot-backend:.*|image: $(BACKEND_IMAGE)|g" kubernetes/backend/deployment.yaml
	@sed -i.bak "s|image:.*chatbot-frontend:.*|image: $(FRONTEND_IMAGE)|g" kubernetes/frontend/deployment.yaml
	@rm -f kubernetes/backend/deployment.yaml.bak kubernetes/frontend/deployment.yaml.bak
	@echo "✅ Deployment images updated"
	@echo ""
	@echo "🚀 Deploying to Kubernetes..."
	kubectl apply -k kubernetes/
	@echo "✅ Deployment completed"
	@echo ""
	@echo "⏳ Waiting for pods to be ready (this may take a few minutes)..."
	@echo ""
	@kubectl wait --for=condition=ready pod -l app=arangodb -n chatbot --timeout=300s 2>/dev/null || true
	@kubectl wait --for=condition=ready pod -l app=minio -n chatbot --timeout=300s 2>/dev/null || true
	@kubectl wait --for=condition=ready pod -l app=ollama -n chatbot --timeout=300s 2>/dev/null || true
	@kubectl wait --for=condition=ready pod -l app=backend -n chatbot --timeout=300s 2>/dev/null || true
	@kubectl wait --for=condition=ready pod -l app=frontend -n chatbot --timeout=300s 2>/dev/null || true
	@kubectl wait --for=condition=ready pod -l app=caddy -n chatbot --timeout=300s 2>/dev/null || true
	@echo ""
	@echo "✅ All pods are ready!"
	@echo ""
	@echo "📊 Current status:"
	@kubectl get pods -n chatbot
	@echo ""
	@echo "🌐 Access your application at: http://app.domain.local"
	@echo "⚠️  Don't forget to add '127.0.0.1 app.domain.local' to /etc/hosts"

down-kube: ## Remove deployment from Kubernetes
	@echo "🛑 Removing deployment from Kubernetes..."
	kubectl delete -k kubernetes/
	@echo "✅ Deployment removed"

status-kube: ## Show Kubernetes deployment status
	@echo "📊 Namespace chatbot status:"
	@echo ""
	@echo "=== Pods ==="
	@kubectl get pods -n chatbot -o wide
	@echo ""
	@echo "=== Services ==="
	@kubectl get services -n chatbot
	@echo ""
	@echo "=== Ingress ==="
	@kubectl get ingress -n chatbot
	@echo ""
	@echo "=== Persistent Volume Claims ==="
	@kubectl get pvc -n chatbot

logs-kube: ## Show logs from Kubernetes pods (use POD=<name> or APP=<app-label>)
	@if [ -n "$(POD)" ]; then \
		echo "📋 Logs for pod $(POD):"; \
		kubectl logs -n chatbot $(POD) -f; \
	elif [ -n "$(APP)" ]; then \
		echo "📋 Logs for app $(APP):"; \
		kubectl logs -n chatbot -l app=$(APP) -f --all-containers=true; \
	else \
		echo "📋 Available pods in chatbot namespace:"; \
		kubectl get pods -n chatbot --no-headers -o custom-columns=":metadata.name"; \
		echo ""; \
		echo "Usage:"; \
		echo "  make logs-kube POD=<pod-name>     - Show logs for specific pod"; \
		echo "  make logs-kube APP=backend        - Show logs for all backend pods"; \
		echo "  make logs-kube APP=frontend       - Show logs for all frontend pods"; \
		echo "  make logs-kube APP=caddy          - Show logs for all caddy pods"; \
	fi