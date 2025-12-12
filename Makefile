# Path: backend/Makefile
# Version: 12

.PHONY: help install-all install-app install-test clean-all clean-cache test test-unit test-int test-cov dev lint format docker-clean list-files

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
	@echo "  cyschat Backend - Makefile Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install-all      Full reset + install (clean-all + install)"
	@echo "  make install-app      Install app dependencies only"
	@echo "  make install-test     Install test dependencies only"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean-all        Full cleanup (venv + all caches)"
	@echo "  make clean-cache      Remove Python caches only"
	@echo ""
	@echo "🧪 Testing (all tests run in parallel):"
	@echo "  make test             Run all tests (auto-cleans cache)"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-int         Run integration tests (Docker required)"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "🐳 Docker Management:"
	@echo "  make docker-clean     Remove stopped testcontainers"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev              Run development server"
	@echo "  make lint             Run linter checks"
	@echo "  make format           Format code"
	@echo ""
	@echo "📋 Utilities:"
	@echo "  make list-files       List all Python files in project"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# INSTALLATION
# ============================================================================

install-all: clean-all
	@echo "🔄 Full installation: cleaning + installing..."
	@$(MAKE) install-app
	@$(MAKE) install-test
	@echo "✅ Full installation complete"

install-app:
	@echo "📦 Installing application dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "🔧 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PYTHON) -m pip install -r requirements.txt
	@echo "✅ Application dependencies installed"

install-test:
	@echo "📦 Installing test dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install-app' first."; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install -r requirements-test.txt
	@echo "✅ Test dependencies installed"

# ============================================================================
# CLEANUP
# ============================================================================

clean-all:
	@echo "🧹 Full cleanup: removing venv and all caches..."
	@$(MAKE) -s clean-cache
	@chmod -R 777 $(VENV) 2>/dev/null || true
	@rm -rf $(VENV) 2>/dev/null || true
	@echo "✅ Full cleanup complete (venv removed)"

clean-cache:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/ coverage.xml 2>/dev/null || true

# ============================================================================
# TESTING (all tests run in parallel with auto cache cleanup)
# ============================================================================

test: clean-cache
	@echo "🧪 Running all tests in parallel..."
	@$(VENV_PYTHON) -m pytest tests/ -n auto -v --cache-clear
	@echo "✅ All tests completed"

test-unit: clean-cache
	@echo "🧪 Running unit tests in parallel..."
	@$(VENV_PYTHON) -m pytest tests/unit/ -n auto -v -m unit
	@echo "✅ Unit tests completed"

test-int: clean-cache
	@echo "🧪 Running integration tests in parallel (Docker required)..."
	@$(VENV_PYTHON) -m pytest tests/integration/ -n auto -v -m integration
	@$(MAKE) -s docker-clean
	@echo "✅ Integration tests completed"

test-cov: clean-cache
	@echo "🧪 Running tests with coverage..."
	@$(VENV_PYTHON) -m pytest tests/ -n auto -v \
		--cov=src/database \
		--cov=src/storage \
		--cov=src/api \
		--cov=src/middleware \
		--cov=src/models \
		--cov=src/repositories \
		--cov=src/services \
		--cov-report=html \
		--cov-report=term-missing
	@echo ""
	@echo "📊 Coverage report generated: htmlcov/index.html"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	@echo "🚀 Starting development server..."
	@$(VENV_PYTHON) -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
	@echo "🔍 Running linter..."
	@$(VENV_PYTHON) -m ruff check src/ tests/

lint-fix:
	@echo "🔧 Fixing linting issues..."
	@$(VENV_PYTHON) -m ruff check --fix src/ tests/

format:
	@echo "🎨 Formatting code..."
	@$(VENV_PYTHON) -m black src/ tests/

format-check:
	@echo "🔍 Checking code formatting..."
	@$(VENV_PYTHON) -m black --check src/ tests/

typecheck:
	@echo "🔍 Running type checker..."
	@$(VENV_PYTHON) -m mypy src/

# ============================================================================
# DOCKER
# ============================================================================

docker-clean:
	@echo "🧹 Cleaning testcontainers..."
	@docker ps -aq --filter "label=testcontainer=true" | xargs -r docker stop 2>/dev/null || true
	@docker ps -aq --filter "label=testcontainer=true" | xargs -r docker rm -f -v 2>/dev/null || true
	@docker container prune -f
	@echo "✅ Docker cleanup complete"

docker-ps:
	@echo "📋 Listing testcontainers..."
	@docker ps -a --filter "label=testcontainer=true" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

docker-stats:
	@echo "📊 Resource usage of testcontainers:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
		$$(docker ps --filter "label=testcontainer=true" -q) 2>/dev/null || echo "No testcontainers running"

# ============================================================================
# QUALITY
# ============================================================================

quality: lint format-check typecheck
	@echo "✅ All quality checks passed"

# ============================================================================
# UTILITIES
# ============================================================================

list-files:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  📋 Project File Structure"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "🔹 Source Files (src/):"
	@find src -type f -name "*.py" | sort | sed 's|^src/|  |'
	@echo ""
	@echo "🔹 Test Files (tests/):"
	@find tests -type f -name "*.py" | sort | sed 's|^tests/|  |'
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Statistics:"
	@printf "  Source files:  "
	@find src -type f -name "*.py" | wc -l
	@printf "  Test files:    "
	@find tests -type f -name "*.py" | wc -l
	@printf "  Total Python:  "
	@find src tests -type f -name "*.py" | wc -l
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"