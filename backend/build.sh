#!/bin/bash
################################################################################
# FastAPI Backend Setup - Inline Script
# Copier-coller directement dans le terminal
################################################################################

set -e
PROJECT_NAME="chatbot-backend"

echo "🚀 Creating FastAPI Backend Structure..."

# Check if directory exists
if [ -d "$PROJECT_NAME" ]; then
    echo "⚠️  Directory '$PROJECT_NAME' exists. Removing..."
    rm -rf "$PROJECT_NAME"
fi

mkdir -p "$PROJECT_NAME" && cd "$PROJECT_NAME"

# Create directory structure
echo "📁 Creating directories..."
mkdir -p src/{api/{auth,users,user_groups,conversations,conversation_groups,chat,files,settings,admin},core,db,models,schemas,services,repositories,middleware,utils}
mkdir -p tests/{unit/{api,services,repositories,utils},integration,e2e,helpers}
mkdir -p {migrations/versions,scripts,docs,.github/workflows}

# Create all __init__.py files
echo "📝 Creating __init__.py files..."
find src tests -type d -exec touch {}/__init__.py \;

################################################################################
# ROOT FILES
################################################################################

cat > .gitignore << 'GITIGNORE'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
venv/
env/
.venv
.pytest_cache/
.coverage
htmlcov/
.tox/
coverage.xml
.vscode/
.idea/
*.swp
.DS_Store
.env
.env.local
*.log
logs/
.mypy_cache/
.ruff_cache/
GITIGNORE

cat > .dockerignore << 'DOCKERIGNORE'
__pycache__/
*.py[cod]
venv/
.pytest_cache/
.coverage
htmlcov/
.vscode/
.idea/
.DS_Store
.env
.env.local
tests/
docs/
*.md
!README.md
.github/
DOCKERIGNORE

cat > .env.example << 'ENVEXAMPLE'
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=true
ARANGO_HOST=localhost
ARANGO_PORT=8529
ARANGO_DATABASE=chatbot
ARANGO_USER=root
ARANGO_PASSWORD=changeme
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=chatbot-files
MINIO_SECURE=false
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=12
AUTH_MODE=local
ALLOW_MULTI_LOGIN=false
OPENAI_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4
ENVEXAMPLE

cat > requirements.txt << 'REQUIREMENTS'
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-arango==7.8.0
minio==7.2.0
redis==5.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.26.0
aiofiles==23.2.1
openai==1.10.0
REQUIREMENTS

cat > requirements-dev.txt << 'REQUIREMENTSDEV'
pytest==7.4.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.12.0
ruff==0.1.0
mypy==1.8.0
REQUIREMENTSDEV

cat > pytest.ini << 'PYTESTINI'
[pytest]
minversion = 7.0
addopts = -ra -q --strict-markers --cov=src --cov-report=term-missing --cov-report=html
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
PYTESTINI

cat > mypy.ini << 'MYPYINI'
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
no_implicit_optional = True
ignore_missing_imports = True

[mypy-tests.*]
disallow_untyped_defs = False
MYPYINI

cat > ruff.toml << 'RUFFTOML'
line-length = 100
target-version = "py311"
select = ["E", "W", "F", "I", "C", "B", "UP"]
ignore = ["E501", "B008", "C901"]

[per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*.py" = ["S101"]
RUFFTOML

cat > Makefile << 'MAKEFILE'
.PHONY: help install dev test lint format clean

PYTHON := python3.11
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
RUFF := $(PYTHON) -m ruff
UVICORN := $(PYTHON) -m uvicorn

help:
	@echo "make install       - Install dependencies"
	@echo "make dev           - Run development server"
	@echo "make test          - Run all tests"
	@echo "make test-coverage - Run tests with coverage"
	@echo "make lint          - Check code quality"
	@echo "make format        - Format code"
	@echo "make clean         - Clean generated files"
	@echo "make docker-up     - Start Docker services"
	@echo "make init-db       - Initialize database"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt

dev:
	$(UVICORN) src.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTEST) tests -v

test-coverage:
	$(PYTEST) tests --cov=src --cov-report=html --cov-report=term-missing

lint:
	$(RUFF) check src tests

format:
	$(BLACK) src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage .pytest_cache .mypy_cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

init-db:
	$(PYTHON) scripts/init_db.py

create-root:
	$(PYTHON) scripts/create_root_user.py
MAKEFILE

cat > Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
COPY scripts/ ./scripts/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

cat > docker-compose.yml << 'DOCKERCOMPOSE'
version: '3.8'
services:
  api:
    build: .
    container_name: chatbot-api
    ports:
      - "8000:8000"
    environment:
      - ARANGO_HOST=arangodb
      - MINIO_ENDPOINT=minio:9000
      - REDIS_HOST=redis
    env_file:
      - .env.local
    depends_on:
      - arangodb
      - minio
      - redis
    networks:
      - chatbot

  arangodb:
    image: arangodb:latest
    container_name: chatbot-arangodb
    environment:
      - ARANGO_ROOT_PASSWORD=changeme
    ports:
      - "8529:8529"
    volumes:
      - arangodb-data:/var/lib/arangodb3
    networks:
      - chatbot

  minio:
    image: minio/minio:latest
    container_name: chatbot-minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio-data:/data
    networks:
      - chatbot

  redis:
    image: redis:7-alpine
    container_name: chatbot-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - chatbot

networks:
  chatbot:
    driver: bridge

volumes:
  arangodb-data:
  minio-data:
  redis-data:
DOCKERCOMPOSE

################################################################################
# SRC FILES
################################################################################

cat > src/main.py << 'MAINPY'
"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="Chatbot API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

@app.get("/")
async def root():
    return {"message": "Chatbot API", "version": "1.0.0", "docs": "/docs"}
MAINPY

cat > src/core/config.py << 'CONFIGPY'
"""Application configuration"""
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    ARANGO_HOST: str = "localhost"
    ARANGO_PORT: int = 8529
    ARANGO_DATABASE: str = "chatbot"
    ARANGO_USER: str = "root"
    ARANGO_PASSWORD: str = "changeme"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "chatbot-files"
    MINIO_SECURE: bool = False
    JWT_SECRET: str = "change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 12
    AUTH_MODE: str = "local"
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True

settings = Settings()
CONFIGPY

cat > src/core/security.py << 'SECURITYPY'
"""Security utilities"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except:
        raise ValueError("Invalid token")
SECURITYPY

cat > src/core/permissions.py << 'PERMISSIONSPY'
"""Permission checking utilities"""
from typing import Dict, Any

def check_permission(user: Dict[str, Any], required_role: str) -> bool:
    role_hierarchy = {"user": 1, "manager": 2, "root": 3}
    user_level = role_hierarchy.get(user.get("role", "user"), 0)
    required_level = role_hierarchy.get(required_role, 999)
    return user_level >= required_level
PERMISSIONSPY

cat > src/core/logging.py << 'LOGGINGPY'
"""Logging configuration"""
import logging
import sys
from src.core.config import settings

def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
LOGGINGPY

cat > src/db/arango.py << 'ARANGOPY'
"""ArangoDB connection"""
from arango import ArangoClient
from arango.database import StandardDatabase
from src.core.config import settings

_db_instance = None

def get_arango_db() -> StandardDatabase:
    global _db_instance
    if _db_instance is None:
        client = ArangoClient(hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}")
        _db_instance = client.db(
            settings.ARANGO_DATABASE,
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD
        )
    return _db_instance
ARANGOPY

cat > src/db/redis.py << 'REDISPY'
"""Redis connection"""
import redis.asyncio as redis
from typing import Optional
from src.core.config import settings

_redis_instance: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    return _redis_instance
REDISPY

cat > src/db/minio.py << 'MINIOPY'
"""MinIO connection"""
from minio import Minio
from typing import Optional
from src.core.config import settings

_minio_instance: Optional[Minio] = None

def get_minio_client() -> Minio:
    global _minio_instance
    if _minio_instance is None:
        _minio_instance = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        if not _minio_instance.bucket_exists(settings.MINIO_BUCKET):
            _minio_instance.make_bucket(settings.MINIO_BUCKET)
    return _minio_instance
MINIOPY

cat > src/models/common.py << 'COMMONPY'
"""Common Pydantic models"""
from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
COMMONPY

cat > src/utils/constants.py << 'CONSTANTSPY'
"""Application constants"""
USER_ROLE = "user"
MANAGER_ROLE = "manager"
ROOT_ROLE = "root"
STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"
AUTH_MODE_NONE = "none"
AUTH_MODE_LOCAL = "local"
AUTH_MODE_SSO = "sso"
MAX_FILE_SIZE = 10 * 1024 * 1024
CONSTANTSPY

################################################################################
# TESTS
################################################################################

cat > tests/conftest.py << 'CONFTESTPY'
"""Global pytest fixtures"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_user():
    return {
        "id": "user-test-1",
        "name": "Test User",
        "email": "test@example.com",
        "role": "user",
        "status": "active",
    }
CONFTESTPY

cat > tests/unit/test_example.py << 'TESTUNITPY'
"""Example unit test"""
import pytest

@pytest.mark.unit
def test_example():
    assert 1 + 1 == 2

@pytest.mark.unit
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
TESTUNITPY

cat > tests/integration/test_example.py << 'TESTINTEGRATIONPY'
"""Example integration test"""
import pytest

@pytest.mark.integration
async def test_root_endpoint(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
TESTINTEGRATIONPY

################################################################################
# SCRIPTS
################################################################################

cat > scripts/init_db.py << 'INITDBPY'
#!/usr/bin/env python3
"""Initialize database"""
from arango import ArangoClient
from src.core.config import settings

def init_database():
    client = ArangoClient(hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}")
    sys_db = client.db("_system", username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
    
    if not sys_db.has_database(settings.ARANGO_DATABASE):
        sys_db.create_database(settings.ARANGO_DATABASE)
        print(f"✅ Database '{settings.ARANGO_DATABASE}' created")
    
    db = client.db(settings.ARANGO_DATABASE, username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
    
    collections = ["users", "user_groups", "conversations", "conversation_groups", "messages", "files", "sessions", "settings", "system_config"]
    
    for col in collections:
        if not db.has_collection(col):
            db.create_collection(col)
            print(f"✅ Collection '{col}' created")
    
    db.collection("users").add_hash_index(fields=["email"], unique=True)
    db.collection("conversations").add_hash_index(fields=["ownerId"])
    print("✅ Indexes created")

if __name__ == "__main__":
    init_database()
INITDBPY

cat > scripts/create_root_user.py << 'CREATEROOTPY'
#!/usr/bin/env python3
"""Create root user"""
from getpass import getpass
from arango import ArangoClient
from src.core.config import settings
from src.core.security import hash_password

def create_root_user():
    print("=== Create Root User ===\n")
    name = input("Name: ")
    email = input("Email: ")
    password = getpass("Password: ")
    
    client = ArangoClient(hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}")
    db = client.db(settings.ARANGO_DATABASE, username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
    
    user_data = {
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "root",
        "status": "active",
        "groupIds": [],
    }
    
    try:
        result = db.collection("users").insert(user_data)
        print(f"\n✅ Root user created: {result['_key']}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_root_user()
CREATEROOTPY

chmod +x scripts/*.py

################################################################################
# README
################################################################################

cat > README.md << 'README'
# Chatbot Backend API

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
README

################################################################################
# SUMMARY
################################################################################

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📊 Summary:"
echo "   - Files created: $(find . -type f | wc -l)"
echo "   - Directories: $(find . -type d | wc -l)"
echo ""
echo "🚀 Next Steps:"
echo "   1. cd $PROJECT_NAME"
echo "   2. python3.11 -m venv venv"
echo "   3. source venv/bin/activate"
echo "   4. make install-dev"
echo "   5. cp .env.example .env.local"
echo "   6. make docker-up"
echo "   7. make init-db"
echo "   8. make create-root"
echo "   9. make dev"
echo ""
echo "📚 Documentation: http://localhost:8000/docs"
echo ""