"""
Path: backend/tests/integration/api/test_chat_routes_openrouter_integration.py
Version: 9.0

Changes in v9:
- Fix test_conversation fixture structure to match ConversationInDB model:
  - Use "owner_id" instead of "user_id" (correct field name)
  - Add missing "group_id" and "shared_with_group_ids" fields
  - Set updated_at to datetime (not None) for consistency
- Fix all test calls to use test_conversation["id"] instead of ["_key"]
  - Lines 142, 191: conversationId parameter
- Architecture: ArangoDB adapter maps _key â†’ id for service layer consistency

Changes in v8:
- Fix test_conversation fixture to use test_user["id"] instead of ["_key"]
- ArangoDB adapter maps _key to id for service layer

Changes in v7:
- Fix auth_headers to use accessToken (camelCase) - converter is active

Changes in v6:
- Remove module reload entirely - not needed with lazy-loading
- setup_openrouter already calls reset_llm(), no additional reload needed
- Preserves all DB connections and singleton state

Integration tests for chat streaming routes using OpenRouter

These tests require OPENROUTER_API_KEY to be set.
They will be skipped if the key is not available.
"""

import pytest
import os
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password
from src.llm.factory import reset_llm
from src.core.config import settings


# Skip all tests in this file if no OpenRouter API key
pytestmark = pytest.mark.skipif(
    not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "",
    reason="OPENROUTER_API_KEY not configured"
)


@pytest.fixture(autouse=True)
def setup_openrouter():
    """Configure environment to use OpenRouter for all tests"""
    # Save original env
    original_env = {
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER"),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
        "OPENROUTER_MODEL": os.environ.get("OPENROUTER_MODEL"),
    }
    
    # Set OpenRouter config
    os.environ["LLM_PROVIDER"] = "openrouter"
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY or ""
    os.environ["OPENROUTER_MODEL"] = "google/gemini-flash-1.5"  # Fast and cheap model
    
    # Reset LLM singleton to pick up new config
    reset_llm()
    
    yield
    
    # Restore original env
    for k, v in original_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    
    # Reset LLM singleton
    reset_llm()


@pytest.fixture
def client(arango_container_function, setup_openrouter):
    """Test client with database and LLM setup"""
    # No module reload needed - ChatService lazy-loads LLM
    # setup_openrouter already calls reset_llm()
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
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
        "password_hash": hash_password("password123"),
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
        "password": "password123"
    })
    assert response.status_code == 200
    
    # SuccessResponse wraps data in "data" field
    # Converter returns camelCase, so it's accessToken not access_token
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_conversation(arango_container_function, test_user):
    """
    Create test conversation
    
    Structure matches ConversationInDB model:
    - owner_id (not user_id)
    - group_id, shared_with_group_ids for sharing features
    - created_at, updated_at as datetime objects
    """
    db = arango_container_function
    return db.create("conversations", {
        "title": "Test Conversation",
        "owner_id": test_user["id"],  # Correct field: owner_id (not user_id)
        "group_id": None,
        "shared_with_group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })


def test_stream_chat_success_openrouter(client, auth_headers, test_conversation):
    """
    Test successful chat streaming with OpenRouter
    
    This test verifies that the chat endpoint works with OpenRouter as the LLM provider.
    It costs a small amount (< $0.01) per run.
    """
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "conversationId": test_conversation["id"],  # Use 'id' - adapter maps _key to id
            "message": "Say 'Hello' and nothing else"  # Keep token usage minimal
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Verify we got some content
    content = response.text
    assert len(content) > 0
    
    # Should contain SSE data lines
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
    
    assert response.status_code == 422  # Validation error


def test_stream_chat_empty_message(client, auth_headers, test_conversation):
    """Test streaming with empty message"""
    response = client.post(
        "/api/chat/stream",
        headers=auth_headers,
        json={
            "conversationId": test_conversation["id"],  # Use 'id' - adapter maps _key to id
            "message": ""
        }
    )
    
    assert response.status_code == 422  # Validation error