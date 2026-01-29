"""
Path: backend/tests/integration/api/test_groups_routes_integration.py
Version: 2.0

Changes in v2.0:
- FIX: Use password_hash instead of password in login requests
- Added compute_password_hash() helper for SHA256 hashing
- Store bcrypt(SHA256) in DB, send SHA256 to login API

Integration tests for conversation groups API endpoints
"""

import pytest
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend)"""
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hashes
TEST_PASS_HASH = compute_password_hash("password123")
OTHER_PASS_HASH = compute_password_hash("password123")


@pytest.fixture
def client(arango_container_function):
    """Test client with database"""
    from src.main import app
    
    db = arango_container_function
    
    for collection in ["users", "conversations", "conversation_groups"]:
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
def other_user(arango_container_function):
    """Create another test user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Other User",
        "email": "other@example.com",
        "password_hash": hash_password(OTHER_PASS_HASH),
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
def other_auth_headers(client, other_user):
    """Get authentication headers for other user"""
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password_hash": OTHER_PASS_HASH
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
        "shared_with_user_ids": [],
        "shared_with_group_ids": [],
        "group_id": None,
        "message_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })


class TestGroupsAPI:
    """Test groups API endpoints"""
    
    def test_create_group(self, client, auth_headers):
        """Test POST /api/groups - Create group"""
        response = client.post(
            "/api/groups",
            json={"name": "Work"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Work"
        assert "id" in data
        assert "ownerId" in data
        assert data["conversationIds"] == []
        assert "createdAt" in data
    
    def test_create_group_missing_name(self, client, auth_headers):
        """Test create group without name"""
        response = client.post(
            "/api/groups",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_create_group_unauthenticated(self, client):
        """Test create group without authentication"""
        response = client.post(
            "/api/groups",
            json={"name": "Work"}
        )
        
        assert response.status_code == 401
    
    def test_list_groups_empty(self, client, auth_headers):
        """Test GET /api/groups - Empty list"""
        response = client.get("/api/groups", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data == []
    
    def test_list_groups(self, client, auth_headers, arango_container_function, test_user):
        """Test GET /api/groups - List user's groups"""
        db = arango_container_function
        
        db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        db.create("conversation_groups", {
            "name": "Personal",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.get("/api/groups", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        names = [g["name"] for g in data]
        assert "Work" in names
        assert "Personal" in names
    
    def test_list_groups_only_own(self, client, auth_headers, arango_container_function, test_user, other_user):
        """Test list groups returns only user's own groups"""
        db = arango_container_function
        
        db.create("conversation_groups", {
            "name": "My Group",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        db.create("conversation_groups", {
            "name": "Other Group",
            "owner_id": other_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.get("/api/groups", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "My Group"
    
    def test_get_group_by_id(self, client, auth_headers, arango_container_function, test_user):
        """Test GET /api/groups/{id} - Get specific group"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": ["conv-1"],
            "created_at": datetime.utcnow()
        })
        
        response = client.get(f"/api/groups/{group['id']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == group["id"]
        assert data["name"] == "Work"
        assert len(data["conversationIds"]) == 1
    
    def test_get_group_not_found(self, client, auth_headers):
        """Test get nonexistent group"""
        response = client.get("/api/groups/nonexistent", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_group_access_denied(self, client, auth_headers, other_auth_headers, arango_container_function, other_user):
        """Test get group belonging to another user"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Other's Group",
            "owner_id": other_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.get(f"/api/groups/{group['id']}", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_group(self, client, auth_headers, arango_container_function, test_user):
        """Test PUT /api/groups/{id} - Update group"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.put(
            f"/api/groups/{group['id']}",
            json={"name": "Work Projects"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Work Projects"
    
    def test_update_group_access_denied(self, client, auth_headers, arango_container_function, other_user):
        """Test update group belonging to another user"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Other's Group",
            "owner_id": other_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.put(
            f"/api/groups/{group['id']}",
            json={"name": "Hacked"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_delete_group(self, client, auth_headers, arango_container_function, test_user):
        """Test DELETE /api/groups/{id} - Delete group"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.delete(f"/api/groups/{group['id']}", headers=auth_headers)
        
        assert response.status_code == 204
        
        deleted = db.get_by_id("conversation_groups", group["id"])
        assert deleted is None
    
    def test_delete_group_clears_conversation_group_id(self, client, auth_headers, arango_container_function, test_user):
        """Test delete group sets conversation.group_id to null"""
        db = arango_container_function
        
        conv = db.create("conversations", {
            "title": "Test",
            "owner_id": test_user["id"],
            "group_id": None,
            "shared_with_user_ids": [],
            "shared_with_group_ids": [],
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [conv["id"]],
            "created_at": datetime.utcnow()
        })
        
        db.update("conversations", conv["id"], {"group_id": group["id"]})
        
        response = client.delete(f"/api/groups/{group['id']}", headers=auth_headers)
        assert response.status_code == 204
        
        updated_conv = db.get_by_id("conversations", conv["id"])
        assert updated_conv["group_id"] is None
    
    def test_delete_group_access_denied(self, client, auth_headers, arango_container_function, other_user):
        """Test delete group belonging to another user"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Other's Group",
            "owner_id": other_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.delete(f"/api/groups/{group['id']}", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_add_conversation_to_group(self, client, auth_headers, arango_container_function, test_user):
        """Test POST /api/groups/{id}/conversations - Add conversation"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        conv = db.create("conversations", {
            "title": "Test",
            "owner_id": test_user["id"],
            "group_id": None,
            "shared_with_user_ids": [],
            "shared_with_group_ids": [],
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        response = client.post(
            f"/api/groups/{group['id']}/conversations",
            json={"conversationId": conv["id"]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert conv["id"] in data["conversationIds"]
        
        updated_conv = db.get_by_id("conversations", conv["id"])
        assert updated_conv["group_id"] == group["id"]
    
    def test_add_conversation_not_owner(self, client, auth_headers, arango_container_function, test_user, other_user):
        """Test add conversation user doesn't own"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        })
        
        conv = db.create("conversations", {
            "title": "Test",
            "owner_id": other_user["id"],
            "group_id": None,
            "shared_with_user_ids": [],
            "shared_with_group_ids": [],
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        response = client.post(
            f"/api/groups/{group['id']}/conversations",
            json={"conversationId": conv["id"]},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_remove_conversation_from_group(self, client, auth_headers, arango_container_function, test_user):
        """Test DELETE /api/groups/{id}/conversations/{convId} - Remove conversation"""
        db = arango_container_function
        
        conv = db.create("conversations", {
            "title": "Test",
            "owner_id": test_user["id"],
            "group_id": None,
            "shared_with_user_ids": [],
            "shared_with_group_ids": [],
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        group = db.create("conversation_groups", {
            "name": "Work",
            "owner_id": test_user["id"],
            "conversation_ids": [conv["id"]],
            "created_at": datetime.utcnow()
        })
        
        db.update("conversations", conv["id"], {"group_id": group["id"]})
        
        response = client.delete(
            f"/api/groups/{group['id']}/conversations/{conv['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert conv["id"] not in data["conversationIds"]
        
        updated_conv = db.get_by_id("conversations", conv["id"])
        assert updated_conv["group_id"] is None
    
    def test_remove_conversation_access_denied(self, client, auth_headers, arango_container_function, other_user):
        """Test remove conversation from group owned by another user"""
        db = arango_container_function
        
        group = db.create("conversation_groups", {
            "name": "Other's Group",
            "owner_id": other_user["id"],
            "conversation_ids": ["conv-1"],
            "created_at": datetime.utcnow()
        })
        
        response = client.delete(
            f"/api/groups/{group['id']}/conversations/conv-1",
            headers=auth_headers
        )
        
        assert response.status_code == 403