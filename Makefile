# path: Makefile
# version: 6.3
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
# Development environment: Docker Compose
# Production: k8s

# k8s image configuration
REGISTRY ?= localhost:5000
IMAGE_TAG ?= latest
BACKEND_IMAGE = $(REGISTRY)/chatbot-backend:$(IMAGE_TAG)
FRONTEND_IMAGE = $(REGISTRY)/chatbot-frontend:$(IMAGE_TAG)

.PHONY: help up down logs clean rebuild rebuild-frontend rebuild-backend rebuild-all clean-images
.PHONY: up-kube down-kube logs-kube status-kube build-images-kube install-ingress-kube

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
	@echo "k8s Commands:"
	@echo "  make install-ingress-kube - Install NGINX Ingress Controller v1.14.1"
	@echo "  make build-images-kube   - Build Docker images for k8s"
	@echo "  make up-kube             - Build images + Deploy to k8s"
	@echo "  make down-kube           - Remove from k8s"
	@echo "  make status-kube         - Show k8s deployment status"
	@echo "  make logs-kube           - Show k8s pod logs"
	@echo ""
	@echo "k8s Configuration:"
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
	@echo "URLs (k8s):"
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
# k8s Commands
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
		--type='json' --patch-file k8s/nginx-ingress-controller-patch.json
	@echo "   → Patching configmap..."
	@kubectl patch configmap ingress-nginx-controller -n ingress-nginx \
		--type='merge' --patch-file k8s/nginx-ingress-configmap-patch.json
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

build-images-kube: ## Build Docker images for k8s
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

up-kube: build-images-kube ## Build images + Deploy to k8s using kustomization.yaml
	@echo ""
	@echo "🔄 Updating deployment images..."
	@sed -i.bak "s|image:.*chatbot-backend:.*|image: $(BACKEND_IMAGE)|g" k8s/backend/deployment.yaml
	@sed -i.bak "s|image:.*chatbot-frontend:.*|image: $(FRONTEND_IMAGE)|g" k8s/frontend/deployment.yaml
	@rm -f k8s/backend/deployment.yaml.bak k8s/frontend/deployment.yaml.bak
	@echo "✅ Deployment images updated"
	@echo ""
	@echo "🚀 Deploying to k8s..."
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
	@kubectl get pods -n chatbotmake 
	@echo ""
	@echo "🌐 Access your application at: http://app.domain.local"
	@echo "⚠️  Don't forget to add '127.0.0.1 app.domain.local' to /etc/hosts"

down-kube: ## Remove deployment from k8s
	@echo "🛑 Removing deployment from k8s..."
	kubectl delete -k k8s/
	@echo "✅ Deployment removed"

status-kube: ## Show k8s deployment status
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

logs-kube: ## Show logs from k8s pods (use POD=<name> or APP=<app-label>)
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