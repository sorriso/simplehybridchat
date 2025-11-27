# =============================================================================
# Makefile - Frontend Application
# =============================================================================
# path: ./Makefile
# version: 16
#
# Description:
#   Simple and complete Makefile for Next.js chatbot frontend application.
#
# Usage:
#   make help              - Show all available commands
#   make install-app       - Install application (npm dependencies)
#   make dev               - Start development server
#   make build             - Build for production (with lint + format check)
#   make test              - Run all tests
#   make lint              - Run linter
#   make format            - Auto-format code
#   make list-files        - List all project files
# =============================================================================

.DEFAULT_GOAL := help

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help:
	@echo ""
	@echo "==================================================="
	@echo "  Frontend Application - Commands"
	@echo "==================================================="
	@echo ""
	@echo "INSTALLATION:"
	@echo "  make install-app     Install application only (npm deps)"
	@echo "  make install-tests   Install EVERYTHING (app + ALL browsers)"
	@echo ""
	@echo "DEVELOPMENT:"
	@echo "  make dev             Start dev server (hot reload)"
	@echo "  make build           Build for production (with lint + format check)"
	@echo "  make start           Start production server"
	@echo ""
	@echo "TESTS:"
	@echo "  make test            Run ALL tests (all browsers)"
	@echo "  make test-unit       Unit tests only"
	@echo "  make test-int        Integration tests only"
	@echo "  make test-e2e        E2E tests (Chromium + Firefox + Webkit)"
	@echo "  make test-coverage   Run tests with coverage report"
	@echo ""
	@echo "CODE QUALITY:"
	@echo "  make lint            Run linter"
	@echo "  make lint-fix        Fix lint issues automatically"
	@echo "  make format          Auto-format code with prettier"
	@echo "  make format-check    Check code formatting"
	@echo "  make check           Run lint + format check"
	@echo ""
	@echo "OPTIONAL - Test single browser:"
	@echo "  make test-e2e-chromium    E2E Chromium only (fastest)"
	@echo "  make test-e2e-firefox     E2E Firefox only"
	@echo "  make test-e2e-webkit      E2E Webkit only"
	@echo ""
	@echo "MAINTENANCE:"
	@echo "  make clean           Clean build artifacts"
	@echo "  make reset           HARD RESET everything"
	@echo "  make list-files      List all project files (exclude build dirs)"
	@echo ""

# =============================================================================
# INSTALLATION
# =============================================================================

.PHONY: install-app
install-app:
	@echo "==================================================="
	@echo "  Installing Application"
	@echo "==================================================="
	npm install

.PHONY: install-tests
install-tests:
	@echo "==================================================="
	@echo "  Installing Application + Test Browsers"
	@echo "==================================================="
	@echo ""
	@echo "[1/2] Installing npm dependencies..."
	npm install
	@echo ""
	@echo "[2/2] Installing Playwright browsers (Chromium + Firefox + Webkit)..."
	npx playwright install
	@echo ""
	@echo "Done! All dependencies and browsers installed."

# =============================================================================
# DEVELOPMENT
# =============================================================================

.PHONY: dev
dev:
	@echo "Starting dev server -> http://localhost:3000"
	npm run dev

.PHONY: build
build:
	@echo "==================================================="
	@echo "  Building for Production"
	@echo "==================================================="
	@echo ""
	@echo "[1/4] Linting code..."
	@npm run lint
	@echo ""
	@echo "[2/4] Formatting code..."
	@npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"
	@echo "Code formatted!"
	@echo ""
	@echo "[3/4] Cleaning previous builds..."
	@rm -rf .next out 2>/dev/null || true
	@echo ""
	@echo "[4/4] Building..."
	@npm run build
	@echo ""
	@echo "Build complete!"

.PHONY: start
start:
	@echo "Starting production -> http://localhost:3000"
	npx serve@latest out -l 3000

# =============================================================================
# TESTS
# =============================================================================

.PHONY: test
test: test-unit test-int

.PHONY: test-unit
test-unit:
	@echo "Unit tests..."
	npx jest tests/unit

.PHONY: test-int
test-int:
	@echo "Integration tests..."
	npx jest tests/integration

.PHONY: test-e2e
test-e2e:
	@echo "E2E tests (all browsers)..."
	npx playwright test

.PHONY: test-e2e-chromium
test-e2e-chromium:
	@echo "E2E tests (Chromium only)..."
	npx playwright test --project=chromium

.PHONY: test-e2e-firefox
test-e2e-firefox:
	@echo "E2E tests (Firefox only)..."
	npx playwright test --project=firefox

.PHONY: test-e2e-webkit
test-e2e-webkit:
	@echo "E2E tests (Webkit only)..."
	npx playwright test --project=webkit

.PHONY: test-coverage
test-coverage:
	@echo "==================================================="
	@echo "  Running tests with coverage"
	@echo "==================================================="
	@echo ""
	npx jest --coverage
	@echo ""
	@echo "Coverage report generated in coverage/"
	@echo "   Open coverage/lcov-report/index.html in browser to see details"

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: lint
lint:
	@echo "Linting code..."
	@npm run lint

.PHONY: lint-fix
lint-fix:
	@echo "Fixing lint issues..."
	@npm run lint:fix
	@echo "Lint issues fixed!"

.PHONY: format
format:
	@echo "Formatting code..."
	npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"
	@echo "Code formatted!"

.PHONY: format-check
format-check:
	@echo "Checking code format..."
	npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"

.PHONY: check
check:
	@echo "==================================================="
	@echo "  Running code quality checks"
	@echo "==================================================="
	@echo ""
	@echo "[1/2] Linting..."
	@npm run lint
	@echo ""
	@echo "[2/2] Checking format..."
	@npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"
	@echo ""
	@echo "All checks passed!"

# =============================================================================
# MAINTENANCE
# =============================================================================

.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf .next out coverage playwright-report test-results
	@echo "Clean complete!"

.PHONY: reset
reset:
	@echo "==================================================="
	@echo "  HARD RESET - Deleting everything"
	@echo "==================================================="
	@echo ""
	@echo "This will delete:"
	@echo "  - node_modules/"
	@echo "  - package-lock.json"
	@echo "  - All build artifacts"
	@echo ""
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo ""
	@echo "Deleting..."
	rm -rf node_modules package-lock.json .next out coverage playwright-report test-results
	@echo ""
	@echo "Done! Run 'make install-app' to reinstall."

.PHONY: list-files
list-files:
	@echo "Listing all project files..."
	@find . -type f ! -path "*/node_modules/*" ! -path "*/.next/*" ! -path "*/coverage/*" ! -path "*/playwright-report/*" ! -path "*/test-results/*" | sort

# =============================================================================
# USAGE NOTES
# =============================================================================
#
# FIRST TIME:
#   make install-app      (for dev only)
#   make install-tests    (for dev + tests)
#
# DAILY DEV:
#   make dev              (start coding)
#   make test-unit        (quick tests)
#
# BEFORE COMMIT:
#   make build            (verify build)
#   make test             (all tests)
#
# IF BROKEN:
#   make reset            (fix 90% of issues)
#