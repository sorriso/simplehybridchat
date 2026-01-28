# path: Makefile
# version: 7.0
# Changes in v7.0:
# - Added dev-up, dev-down, dev-logs, dev-restart for development workflow
# - Simplified commands: just "make dev-up" to start development environment
# - Uses docker-compose.yaml (single file for dev)
# Changes in v6.3:
# - Added automatic patch for nginx ingress controller after installation
# - Enables snippet annotations for custom nginx configuration
# Changes in v6.2:
# - Added install-ingress-kube command to install NGINX Ingress Controller v1.14.1
# Changes in v6.1:
# - Added build-images-kube command to build Docker images for k8s
# - up-kube now builds images before deploying
# - Added REGISTRY and IMAGE_TAG variables for image configuration
#
# Development environment: Docker Compose (docker-compose.yaml)
# Production: Kubernetes (k8s/)

# Kubernetes image configuration
REGISTRY ?= localhost:5000
IMAGE_TAG ?= latest
BACKEND_IMAGE = $(REGISTRY)/chatbot-backend:$(IMAGE_TAG)
FRONTEND_IMAGE = $(REGISTRY)/chatbot-frontend:$(IMAGE_TAG)

.PHONY: help dev-up dev-down dev-logs dev-restart dev-build dev-clean dev-shell-backend dev-shell-frontend
.PHONY: up-kube down-kube logs-kube status-kube build-images-kube install-ingress-kube

.DEFAULT_GOAL := help

help: ## Show help
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🚀 Development Commands (Docker Compose)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  make dev-up              - Start all services (hot-reload enabled)"
	@echo "  make dev-down            - Stop all services"
	@echo "  make dev-logs            - Show logs (all services)"
	@echo "  make dev-restart         - Restart all services"
	@echo "  make dev-build           - Rebuild images"
	@echo "  make dev-clean           - Stop services and remove volumes"
	@echo "  make dev-shell-backend   - Open shell in backend container"
	@echo "  make dev-shell-frontend  - Open shell in frontend container"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ☸️  Kubernetes Commands (Production)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  make install-ingress-kube - Install NGINX Ingress Controller"
	@echo "  make build-images-kube   - Build Docker images for k8s"
	@echo "  make up-kube             - Build images + Deploy to k8s"
	@echo "  make down-kube           - Remove from k8s"
	@echo "  make status-kube         - Show k8s deployment status"
	@echo "  make logs-kube           - Show k8s pod logs"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🌐 URLs (Development)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  ArangoDB:  http://localhost:8529 (root/changeme)"
	@echo "  MinIO:     http://localhost:9001 (minioadmin/minioadmin)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  📝 Quick Start"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  1. Copy backend/.env.example to backend/.env"
	@echo "  2. Run: make dev-up"
	@echo "  3. Edit code in backend/src/ or frontend/src/"
	@echo "  4. See changes automatically!"
	@echo ""

# =============================================================================
# Development Commands (Docker Compose)
# =============================================================================

dev-up: ## Start development environment
	@echo "🚀 Starting development environment..."
	@if [ ! -f backend/.env ]; then \
		echo "⚠️  backend/.env not found"; \
		if [ -f backend/env.example ]; then \
			echo "📝 Creating backend/.env from env.example..."; \
			cp backend/env.example backend/.env; \
			echo "✅ Created backend/.env"; \
		else \
			echo "❌ backend/env.example not found"; \
			echo "Please create backend/.env manually"; \
			exit 1; \
		fi \
	fi
	@docker-compose up -d
	@echo "✅ Services started"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🌐 Access your application:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"
	@echo "   ArangoDB:  http://localhost:8529"
	@echo "   MinIO:     http://localhost:9001"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "💡 Hot-reload is enabled:"
	@echo "   • Edit backend/src/ → Backend restarts automatically"
	@echo "   • Edit frontend/src/ → Browser reloads automatically"
	@echo ""
	@echo "📋 View logs: make dev-logs"
	@echo ""

dev-down: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	@docker-compose down
	@echo "✅ Services stopped"

dev-logs: ## Show logs from all services
	@docker-compose logs -f

dev-restart: ## Restart all services
	@echo "🔄 Restarting services..."
	@docker-compose restart
	@echo "✅ Services restarted"

dev-build: ## Rebuild development images
	@echo "🔨 Rebuilding development images..."
	@docker-compose build --no-cache
	@echo "✅ Images rebuilt"

dev-clean: ## Stop services and remove volumes
	@echo "🧹 Cleaning development environment..."
	@docker-compose down -v
	@echo "✅ Cleaned (containers and volumes removed)"

dev-shell-backend: ## Open shell in backend container
	@docker-compose exec backend /bin/bash

dev-shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend /bin/sh

# =============================================================================
# Kubernetes Commands (Production)
# =============================================================================

install-ingress-kube: ## Install NGINX Ingress Controller v1.14.1
	@echo "🔄 Installing NGINX Ingress Controller v1.14.1..."
	@kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.14.1/deploy/static/provider/cloud/deploy.yaml
	@echo "✅ NGINX Ingress Controller manifest applied"
	@echo ""
	@echo "⏳ Waiting for ingress controller to be ready (this may take a few minutes)..."
	@kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=300s
	@echo ""
	@echo "✅ NGINX Ingress Controller is ready!"
	@echo ""
	@echo "🔧 Applying patches to enable snippet annotations..."
	@echo "   → Patching deployment..."
	@kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
		--type='json' --patch-file k8s/ingress/nginx-ingress-controller-patch.json
	@echo "   → Patching configmap..."
	@kubectl patch configmap ingress-nginx-controller -n ingress-nginx \
		--type='merge' --patch-file k8s/ingress/nginx-ingress-configmap-patch.json
	@echo "✅ Patches applied successfully"
	@echo ""
	@echo "♻️  Restarting ingress controller..."
	@kubectl delete pods -n ingress-nginx -l app.kubernetes.io/component=controller
	@echo "✅ Pod deleted, waiting for new pod to be ready..."
	@echo ""
	@echo "⏳ Waiting for controller to restart with new configuration..."
	@kubectl rollout status deployment ingress-nginx-controller -n ingress-nginx --timeout=120s
	@echo ""
	@echo "✅ NGINX Ingress Controller patched and ready!"
	@echo ""
	@echo "📊 Ingress controller status:"
	@kubectl get pods -n ingress-nginx
	@echo ""
	@kubectl get svc -n ingress-nginx
	@echo ""
	@echo "⚠️  Note: This project will be retired in March 2026"
	@echo "    Consider migrating to Gateway API or F5 NGINX Ingress Controller"

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

up-kube: build-images-kube ## Build images + Deploy to Kubernetes
	@echo ""
	@echo "🔄 Updating deployment images..."
	@sed -i.bak "s|image:.*chatbot-backend:.*|image: $(BACKEND_IMAGE)|g" k8s/backend/deployment.yaml
	@sed -i.bak "s|image:.*chatbot-frontend:.*|image: $(FRONTEND_IMAGE)|g" k8s/frontend/deployment.yaml
	@rm -f k8s/backend/deployment.yaml.bak k8s/frontend/deployment.yaml.bak
	@echo "✅ Deployment images updated"
	@echo ""
	@echo "🚀 Deploying to Kubernetes..."
	kubectl apply -k k8s/
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
	kubectl delete -k k8s/
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

logs-kube: ## Show logs from Kubernetes pods
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