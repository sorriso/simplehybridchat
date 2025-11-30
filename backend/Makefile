# Path: Makefile
# Version: 10
#
# Changes in v10:
# - Changed test-int-p from -n 5 to -n auto
# - Now uses all available CPU cores for integration tests
# - Automatically adapts to machine resources
#
# Changes in v9:
# - Changed test-int-p workers from 4 to 5 (-n 5)
# - Allows 5 parallel Docker containers for integration tests
#
# Changes in v8:
# - Added clean-cache target (fast, silent cache cleanup)
# - ALL test targets now auto-clean caches before running
# - Removes: __pycache__, .pytest_cache, .coverage, .mypy_cache, .ruff_cache

.PHONY: help install install-app install-test clean clean-cache clean-all uninstall test test-unit test-integration dev lint format list-files

# Python interpreter
PYTHON := python3
PIP := $(PYTHON) -m pip

# Virtual environment
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Default target
.DEFAULT_GOAL := help

help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Chatbot Backend - Makefile Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install          Install app + test dependencies"
	@echo "  make install-app      Install only app dependencies"
	@echo "  make install-test     Install only test dependencies"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean-cache      Remove Python caches (fast)"
	@echo "  make clean            Remove cache, coverage, build files"
	@echo "  make clean-all        Full reset (clean + remove venv)"
	@echo "  make uninstall        Uninstall all packages (keep venv)"
	@echo ""
	@echo "🧪 Testing (auto-cleans cache before running):"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-int         Run integration tests (Docker required)"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo ""
	@echo "⚡ Parallel Testing (FAST):"
	@echo "  make test-parallel    Run all tests in parallel (auto workers)"
	@echo "  make test-unit-p      Run unit tests in parallel"
	@echo "  make test-int-p       Run integration tests in parallel"
	@echo "  make test-fast        Run unit tests parallel + fast mode"
	@echo "  make test-cov-p       Run tests with coverage in parallel"
	@echo ""
	@echo "🐳 Docker Management:"
	@echo "  make docker-ps        List testcontainers"
	@echo "  make docker-stats     Show resource usage"
	@echo "  make docker-clean     Remove stopped testcontainers"
	@echo "  make docker-clean-all Force remove all testcontainers"
	@echo "  make docker-clean-orphans Clean ArangoDB containers without labels"
	@echo "  make check-containers Check for orphaned containers"
	@echo "  make check-docker     Verify Docker availability"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev              Run development server"
	@echo "  make lint             Run linter checks"
	@echo "  make format           Format code with black"
	@echo ""
	@echo "📋 Utilities:"
	@echo "  make list-files       List all project files"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# INSTALLATION
# ============================================================================

install: install-app install-test
	@echo "✅ All dependencies installed (app + test)"

install-app:
	@echo "📦 Installing application dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "🔧 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@$(VENV_BIN)/python -m pip install --upgrade pip
	@$(VENV_BIN)/python -m pip install -r requirements.txt
	@echo "✅ Application dependencies installed"

install-test: install-app
	@echo "📦 Installing test dependencies..."
	@$(VENV_BIN)/python -m pip install -r requirements-test.txt
	@echo "✅ Test dependencies installed"

# ============================================================================
# CLEANUP
# ============================================================================

clean-cache:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true

clean: clean-cache
	@echo "🧹 Cleaning cache and build files..."
	@find . -type f -name "*.coverage" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf coverage.xml 2>/dev/null || true
	@rm -rf dist/ 2>/dev/null || true
	@rm -rf build/ 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean
	@echo "🧹 Full reset: removing virtual environment..."
	@chmod -R 777 $(VENV) 2>/dev/null || true
	@rm -rf $(VENV) 2>/dev/null || true
	@echo "✅ Full reset complete (venv removed)"

uninstall:
	@echo "🗑️  Uninstalling all packages..."
	@if [ -f "$(VENV_PIP)" ]; then \
		$(VENV_PIP) freeze | grep -v "^-e" | xargs $(VENV_PIP) uninstall -y 2>/dev/null || true; \
		echo "✅ All packages uninstalled (venv kept)"; \
	else \
		echo "⚠️  Virtual environment not found"; \
	fi

# ============================================================================
# TESTING (all targets auto-clean cache)
# ============================================================================

test: clean-cache
	@echo "🧪 Running all tests..."
	@$(VENV_BIN)/python -m pytest tests/ -v

test-unit: clean-cache
	@echo "🧪 Running unit tests..."
	@$(VENV_BIN)/python -m pytest tests/unit/ -v

test-int: clean-cache
	@echo "🧪 Running integration tests (Docker required)..."
	@$(VENV_BIN)/python -m pytest tests/integration/ -v -m integration
	@$(MAKE) -s docker-clean

test-integration-fast: clean-cache
	@echo "🧪 Running fast integration tests (shared containers)..."
	@$(VENV_BIN)/python -m pytest tests/integration/ -v -m integration_fast
	@$(MAKE) -s docker-clean

test-integration-slow: clean-cache
	@echo "🧪 Running slow integration tests (isolated containers)..."
	@$(VENV_BIN)/python -m pytest tests/integration/ -v -m integration_slow
	@$(MAKE) -s docker-clean

test-coverage: clean-cache
	@echo "🧪 Running tests with coverage..."
	@$(VENV_BIN)/python -m pytest tests/ -v \
		--cov=src/database \
		--cov-report=html \
		--cov-report=term-missing
	@echo ""
	@echo "📊 Coverage report generated: htmlcov/index.html"

# ============================================================================
# PARALLEL TESTING
# ============================================================================

test-parallel: clean-cache
	@echo "⚡ Running all tests in parallel (auto workers)..."
	@$(VENV_BIN)/python -m pytest tests/ -n auto -v

test-unit-p: clean-cache
	@echo "⚡ Running unit tests in parallel..."
	@$(VENV_BIN)/python -m pytest tests/unit/ -n auto -v -m unit

test-int-p: clean-cache
	@echo "⚡ Running integration tests in parallel..."
	@$(VENV_BIN)/python -m pytest tests/integration/ -n auto -v -m integration
	@$(MAKE) -s docker-clean

test-fast: clean-cache
	@echo "⚡ Fast unit tests (parallel + minimal output)..."
	@$(VENV_BIN)/python -m pytest tests/unit/ -n auto -m unit --tb=short

test-cov-p: clean-cache
	@echo "⚡ Running tests with coverage in parallel..."
	@$(VENV_BIN)/python -m pytest tests/ -n auto -v \
		--cov=src/database \
		--cov=src/storage \
		--cov=src/api \
		--cov=src/middleware \
		--cov=src/models \
		--cov-report=html \
		--cov-report=term-missing
	@echo ""
	@echo "📊 Coverage report generated: htmlcov/index.html"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	@echo "🚀 Starting development server..."
	@$(VENV_BIN)/python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
	@echo "🔍 Running linter..."
	@$(VENV_BIN)/python -m ruff check src/ tests/

lint-fix:
	@echo "🔧 Fixing linting issues..."
	@$(VENV_BIN)/python -m ruff check --fix src/ tests/

format:
	@echo "🎨 Formatting code..."
	@$(VENV_BIN)/python -m black src/ tests/

format-check:
	@echo "🔍 Checking code formatting..."
	@$(VENV_BIN)/python -m black --check src/ tests/

typecheck:
	@echo "🔍 Running type checker..."
	@$(VENV_BIN)/python -m mypy src/

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t chatbot-backend .

docker-up:
	@echo "🐳 Starting Docker services..."
	@docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	@docker-compose down

docker-logs:
	@echo "📋 Docker logs..."
	@docker-compose logs -f

docker-ps:
	@echo "📋 Listing testcontainers..."
	@docker ps -a --filter "label=testcontainer=true" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

docker-stats:
	@echo "📊 Resource usage of testcontainers:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
		$$(docker ps --filter "label=testcontainer=true" -q) 2>/dev/null || echo "No testcontainers running"

docker-clean:
	@echo "🧹 Cleaning testcontainers..."
	@docker ps -aq --filter "label=testcontainer=true" | xargs -r docker stop 2>/dev/null || true
	@docker ps -aq --filter "label=testcontainer=true" | xargs -r docker rm -f -v 2>/dev/null || true
	@docker container prune -f
	@echo "✅ Docker cleanup complete"

docker-clean-all: docker-clean
	@echo "🧹 Force cleaning all Docker resources..."
	@docker stop $$(docker ps -aq --filter "name=testcontainers") 2>/dev/null || true
	@docker rm -f $$(docker ps -aq --filter "name=testcontainers") 2>/dev/null || true
	@docker volume prune -f
	@echo "✅ Full Docker cleanup complete"

check-containers:
	@echo "🔍 Checking for orphaned containers..."
	@COUNT=$$(docker ps -aq --filter "label=testcontainer=true" | wc -l); \
	if [ $$COUNT -gt 0 ]; then \
		echo "⚠️  Found $$COUNT orphaned testcontainer(s)"; \
		docker ps -a --filter "label=testcontainer=true" --format "  - {{.ID}} {{.Names}} ({{.Status}})"; \
		echo "Run 'make docker-clean' to remove them"; \
	else \
		echo "✅ No orphaned testcontainers found"; \
	fi

check-docker:
	@echo "🔍 Checking Docker availability..."
	@docker ps > /dev/null 2>&1 && echo "✅ Docker is available" || (echo "❌ Docker is not available" && exit 1)

docker-clean-orphans:
	@echo "🧹 Cleaning orphaned ArangoDB containers (no labels)..."
	@docker ps -aq --filter "ancestor=arangodb:latest" | xargs -r docker stop 2>/dev/null || true
	@docker ps -aq --filter "ancestor=arangodb:latest" | xargs -r docker rm -f -v 2>/dev/null || true
	@echo "✅ Orphaned ArangoDB containers cleaned"

# ============================================================================
# DATABASE
# ============================================================================

init-db:
	@echo "🗄️  Initializing database..."
	@$(VENV_BIN)/python scripts/init_db.py

create-root:
	@echo "👤 Creating root user..."
	@$(VENV_BIN)/python scripts/create_root_user.py

# ============================================================================
# QUALITY
# ============================================================================

quality: lint format-check typecheck
	@echo "✅ All quality checks passed"

# ============================================================================
# UTILITIES
# ============================================================================

list-files:
	@echo "📋 Listing all project files..."
	@find . -type f \
		! -path "*/node_modules/*" \
		! -path "*/.next/*" \
		! -path "*/coverage/*" \
		! -path "*/playwright-report/*" \
		! -path "*/test-results/*" \
		! -path "*/venv/*" \
		! -path "*/__pycache__/*" \
		! -path "*/.pytest_cache/*" \
		! -path "*/htmlcov/*" \
		! -path "*/.ruff_cache/*" \
		! -path "*/.mypy_cache/*" \
		! -path "*/.git/*" \
		! -path "*/dist/*" \
		! -path "*/build/*" \
		! -path "*/.*" \
		| sort

# ============================================================================
# COMPOSITE COMMANDS
# ============================================================================

reset: clean-all install
	@echo "🔄 Full reset and reinstall complete"

rebuild: clean install
	@echo "🔄 Rebuild complete"