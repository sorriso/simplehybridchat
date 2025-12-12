"""
Path: backend/tests/integration/api/test_conversations_routes_integration.py
Version: 3

Changes in v3:
- FIX: Lines 300, 306 - "timestamp" changed to "created_at"
- Reason: MessageResponse expects created_at field

Changes in v2:
- FIXED: All db.create() now use snake_case field names
- owner_id instead of ownerId
- shared_with_group_ids instead of sharedWithGroupIds
- group_id instead of groupId
- created_at instead of createdAt
- updated_at instead of updatedAt
- conversation_id instead of conversationId

This matches what the backend code expects internally.

Integration tests for conversation management routes
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.main import app
from src.core.security import hash_password


@pytest.fixture
def client(arango_container_function):
    """Test client with database and root user"""
    db = arango_container_function
    
    # Create collections
    if not db.collection_exists("users"):
        db.create_collection("users")
    if not db.collection_exists("conversations"):
        db.create_collection("conversations")
    if not db.collection_exists("messages"):
        db.create_collection("messages")
    
    # Clean any existing test users
    existing_root = db.find_one("users", {"email": "root@example.com"})
    if existing_root:
        db.delete("users", existing_root["id"])
    
    # Create root user for tests
    create_root_user(db)
    
    yield TestClient(app)


def create_root_user(db):
    """Helper to create root user"""
    return db.create("users", {
        "name": "Root User",
        "email": "root@example.com",
        "password_hash": hash_password("RootPass123"),
        "role": "root",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


def create_regular_user(db):
    """Helper to create regular user"""
    return db.create("users", {
        "name": "Regular User",
        "email": "user@example.com",
        "password_hash": hash_password("RootPass123"),
        "role": "user",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


def login_user(client, email="root@example.com", password="RootPass123"):
    """Helper to login and get token"""
    response = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.integration
class TestConversationRoutes:
    """Integration tests for conversation routes"""
    
    def test_create_conversation(self, client, arango_container_function):
        """Test creating a conversation"""
        token = login_user(client)
        
        response = client.post(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test Conversation"}
        )
        
        assert response.status_code == 201
        conv = response.json()["conversation"]
        assert conv["title"] == "Test Conversation"
        assert conv["ownerId"] is not None
        assert conv["isShared"] is False
        assert conv["messageCount"] == 0
    
    def test_list_conversations(self, client, arango_container_function):
        """Test listing user's conversations"""
        db = arango_container_function
        token = login_user(client)
        
        # Create some conversations with SNAKE_CASE (backend internal format)
        root_user = db.find_one("users", {"email": "root@example.com"})
        db.create("conversations", {
            "title": "Conv 1",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        db.create("conversations", {
            "title": "Conv 2",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        conversations = response.json()["conversations"]
        assert len(conversations) >= 2
    
    def test_get_conversation(self, client, arango_container_function):
        """Test getting a specific conversation"""
        db = arango_container_function
        token = login_user(client)
        
        # Create conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Test Conv",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.get(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        result = response.json()["conversation"]
        assert result["id"] == conv["id"]
        assert result["title"] == "Test Conv"
    
    def test_update_conversation(self, client, arango_container_function):
        """Test updating a conversation"""
        db = arango_container_function
        token = login_user(client)
        
        # Create conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Old Title",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.put(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "New Title"}
        )
        
        assert response.status_code == 200
        result = response.json()["conversation"]
        assert result["title"] == "New Title"
    
    def test_delete_conversation(self, client, arango_container_function):
        """Test deleting a conversation"""
        db = arango_container_function
        token = login_user(client)
        
        # Create conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "To Delete",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.delete(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify deleted
        verify_response = client.get(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == 404
    
    def test_share_conversation(self, client, arango_container_function):
        """Test sharing a conversation with groups"""
        db = arango_container_function
        token = login_user(client)
        
        # Create conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "To Share",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.post(
            f"/api/conversations/{conv['id']}/share",
            headers={"Authorization": f"Bearer {token}"},
            json={"groupIds": ["group-1", "group-2"]}
        )
        
        assert response.status_code == 200
        result = response.json()["conversation"]
        assert "group-1" in result["sharedWithGroupIds"]
        assert "group-2" in result["sharedWithGroupIds"]
        assert result["isShared"] is True
    
    def test_unshare_conversation(self, client, arango_container_function):
        """Test unsharing a conversation from groups"""
        db = arango_container_function
        token = login_user(client)
        
        # Create shared conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Shared Conv",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": ["group-1", "group-2"],  # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        response = client.post(
            f"/api/conversations/{conv['id']}/unshare",
            headers={"Authorization": f"Bearer {token}"},
            json={"groupIds": ["group-1"]}
        )
        
        assert response.status_code == 200
        result = response.json()["conversation"]
        assert "group-1" not in result["sharedWithGroupIds"]
        assert "group-2" in result["sharedWithGroupIds"]
    
    def test_get_conversation_messages(self, client, arango_container_function):
        """Test getting messages for a conversation"""
        db = arango_container_function
        token = login_user(client)
        
        # Create conversation with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Test Conv",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        # Create messages with SNAKE_CASE
        db.create("messages", {
            "conversation_id": conv["id"],            # Ã¢â€ Â snake_case
            "role": "user",
            "content": "Hello",
            "created_at": datetime.utcnow()
        })
        db.create("messages", {
            "conversation_id": conv["id"],            # Ã¢â€ Â snake_case
            "role": "assistant",
            "content": "Hi there",
            "created_at": datetime.utcnow()
        })
        
        response = client.get(
            f"/api/conversations/{conv['id']}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


@pytest.mark.integration
class TestConversationPermissions:
    """Test conversation permission system"""
    
    def test_non_owner_cannot_update(self, client, arango_container_function):
        """Test that non-owner cannot update conversation"""
        db = arango_container_function
        
        # Create second user
        user2 = create_regular_user(db)
        
        # Create conversation as root with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Root's Conv",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        # Login as user2
        token = login_user(client, "user@example.com")
        
        # Try to update
        response = client.put(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Hacked"}
        )
        
        assert response.status_code == 403
    
    def test_non_owner_cannot_delete(self, client, arango_container_function):
        """Test that non-owner cannot delete conversation"""
        db = arango_container_function
        
        # Create second user
        user2 = create_regular_user(db)
        
        # Create conversation as root with SNAKE_CASE
        root_user = db.find_one("users", {"email": "root@example.com"})
        conv = db.create("conversations", {
            "title": "Root's Conv",
            "owner_id": root_user["id"],              # Ã¢â€ Â snake_case
            "shared_with_group_ids": [],              # Ã¢â€ Â snake_case
            "group_id": None,                         # Ã¢â€ Â snake_case
            "created_at": datetime.utcnow(),          # Ã¢â€ Â snake_case
            "updated_at": datetime.utcnow()           # Ã¢â€ Â snake_case
        })
        
        # Login as user2
        token = login_user(client, "user@example.com")
        
        # Try to delete
        response = client.delete(
            f"/api/conversations/{conv['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403