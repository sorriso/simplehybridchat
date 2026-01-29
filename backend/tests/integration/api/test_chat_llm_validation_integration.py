"""
Path: backend/tests/integration/api/test_chat_llm_validation_integration.py
Version: 11.0

Changes in v11:
- FIX: Use password_hash instead of password in login requests
- Added compute_password_hash() helper for SHA256 hashing
- Store bcrypt(SHA256) in DB, send SHA256 to login API

Changes in v10:
- Fix test_conversation fixture structure to match ConversationInDB model

Integration tests for chat streaming routes using OpenRouter
"""

import pytest
import os
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password
from src.llm.factory import reset_llm
from src.core.config import settings


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend)"""
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hash
TEST_PASS_HASH = compute_password_hash("password123")


# Skip all tests in this file if no OpenRouter API key
pytestmark = pytest.mark.skipif(
    not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "",
    reason="OPENROUTER_API_KEY not configured"
)


@pytest.fixture(autouse=True)
def setup_openrouter():
    """Configure environment to use OpenRouter for all tests"""
    original_env = {
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER"),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
        "OPENROUTER_MODEL": os.environ.get("OPENROUTER_MODEL"),
    }
    
    os.environ["LLM_PROVIDER"] = "openrouter"
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY or ""
    os.environ["OPENROUTER_MODEL"] = "google/gemini-flash-1.5"
    
    reset_llm()
    
    yield
    
    for k, v in original_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    
    reset_llm()


@pytest.fixture
def client(arango_container_function, setup_openrouter):
    """Test client with database and LLM setup"""
    from src.main import app
    
    db = arango_container_function
    
    for collection in ["users", "conversations", "messages"]:
        if not db.collection_exists(collection):
            db.create_collection(collection)
    
    yield TestClient(app)


@pytest.fixture
def test_user(arango_container_function):
    """Create test user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": hash_password(TEST_PASS_HASH),
        "role": "user",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password_hash": TEST_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_conversation(arango_container_function, test_user):
    """Create test conversation"""
    db = arango_container_function
    return db.create("conversations", {
        "title": "Test Conversation",
        "owner_id": test_user["id"],
        "group_id": None,
        "shared_with_group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })


def test_stream_chat_success_openrouter(client, auth_headers, test_conversation):
    """Test successful chat streaming with OpenRouter"""
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "conversationId": test_conversation["id"],
            "message": "Say 'Hello' and nothing else"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    content = response.text
    assert len(content) > 0
    assert "data:" in content


def test_stream_chat_conversation_not_found(client, auth_headers):
    """Test streaming with non-existent conversation"""
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "conversationId": "nonexistent",
            "message": "Hello"
        }
    )
    
    assert response.status_code == 404


def test_stream_chat_missing_conversation_id(client, auth_headers):
    """Test streaming without conversation ID"""
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "message": "Hello"
        }
    )
    
    assert response.status_code == 422


def test_stream_chat_empty_message(client, auth_headers, test_conversation):
    """Test streaming with empty message"""
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "conversationId": test_conversation["id"],
            "message": ""
        }
    )
    
    assert response.status_code == 422