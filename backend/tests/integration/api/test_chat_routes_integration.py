"""
Path: backend/tests/integration/api/test_chat_routes_integration.py
Version: 15.0

Changes in v15:
- Fix auth_headers to use accessToken (camelCase) - converter is active

Changes in v14:
- Remove module reload entirely - not needed with lazy-loading
- setup_ollama already calls reset_llm(), no additional reload needed
- Preserves all DB connections and singleton state

Integration tests for chat streaming routes
"""

import pytest
import os
import logging
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password
from src.llm.factory import reset_llm

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def setup_ollama(ollama_config):
    """Configure environment to use Ollama for all tests"""
    # Save original env
    original_env = {
        k: os.environ.get(k) 
        for k in ollama_config.keys()
    }
    
    # Set Ollama config
    os.environ.update(ollama_config)
    
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
def client(arango_container_function, setup_ollama):
    """Test client with database and LLM setup"""
    # No module reload needed - ChatService lazy-loads LLM
    # setup_ollama already calls reset_llm()
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
    for collection in ["users", "conversations", "messages"]:
        if not db.collection_exists(collection):
            db.create_collection(collection)
    
    # Verify chat routes are registered
    routes = [route.path for route in app.routes]
    
    if "/api/chat/stream" not in routes:
        logger.error("Chat routes NOT registered!")
        logger.error(f"Available routes: {routes}")
        raise RuntimeError("Chat routes failed to register")
    
    logger.info("âœ“ Chat routes registered")
    
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


def test_stream_chat_success(client, auth_headers, test_conversation):
    """Test successful chat streaming"""
    import time
    import os
    
    # Log test start and configuration
    print(f"\nðŸ§ª Starting test_stream_chat_success", flush=True)
    print(f"   LLM_PROVIDER: {os.environ.get('LLM_PROVIDER')}", flush=True)
    print(f"   OLLAMA_BASE_URL: {os.environ.get('OLLAMA_BASE_URL')}", flush=True)
    print(f"   OLLAMA_TIMEOUT: {os.environ.get('OLLAMA_TIMEOUT')}", flush=True)
    print(f"   Conversation ID: {test_conversation['id']}\n", flush=True)
    
    start_time = time.time()
    
    try:
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "message": "Say hello",  # Short prompt
                "conversationId": test_conversation["id"]
            },
            headers=auth_headers,
            timeout=45.0  # Add explicit timeout
        ) as response:
            elapsed = time.time() - start_time
            print(f"   âœ“ Response received in {elapsed:.2f}s", flush=True)
            print(f"   Status: {response.status_code}", flush=True)
            
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            print(f"   âœ“ Test passed\n", flush=True)
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   âœ— Test failed after {elapsed:.2f}s", flush=True)
        print(f"   Error: {e}\n", flush=True)
        raise


def test_stream_chat_conversation_not_found(client, auth_headers):
    """Test streaming with non-existent conversation"""
    response = client.post(
        "/api/chat/stream",
        json={
            "message": "Test message",
            "conversationId": "nonexistent-conv"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_stream_chat_missing_conversation_id(client, auth_headers):
    """Test streaming without conversation ID"""
    response = client.post(
        "/api/chat/stream",
        json={
            "message": "Test message"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_stream_chat_empty_message(client, auth_headers, test_conversation):
    """Test streaming with empty message"""
    response = client.post(
        "/api/chat/stream",
        json={
            "message": "",
            "conversationId": test_conversation["id"]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_stream_chat_unauthenticated(client, test_conversation):
    """Test streaming without authentication"""
    response = client.post(
        "/api/chat/stream",
        json={
            "message": "Test",
            "conversationId": test_conversation["id"]
        }
    )
    
    assert response.status_code == 401