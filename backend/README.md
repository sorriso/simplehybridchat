# Chatbot Backend API
# Path: backend/README.md
# Version: 1

FastAPI backend for chatbot application.

## Quick Start

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
make install-dev

# Setup environment
cp .env.example .env.local

# Start services
make docker-up

# Initialize database
make init-db
make create-root

# Run development server
make dev
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Commands

- `make dev` - Run development server
- `make test` - Run tests
- `make test-coverage` - Run with coverage
- `make lint` - Check code quality
- `make format` - Format code
- `make docker-up` - Start Docker services

## Services

- API: http://localhost:8000
- ArangoDB: http://localhost:8529 (root/changeme)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Redis: localhost:6379
