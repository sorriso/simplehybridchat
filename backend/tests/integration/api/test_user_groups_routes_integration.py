"""
Path: backend/tests/integration/api/test_user_groups_routes_integration.py
Version: 1.1

Changes in v1.1:
- FIX: test_update_group_as_manager_forbidden now creates group WITHOUT manager in manager_ids
- Managers CAN update groups they manage, but NOT groups they don't manage
- The test was incorrectly adding manager to manager_ids, allowing update

Integration tests for user groups routes.

Tests cover:
- List user groups (by role)
- Get user group by ID
- Create user group (root only)
- Update user group (root or group manager)
- Toggle group status
- Member management (add/remove)
- Manager assignment (root only)
"""

import pytest
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend behavior)"""
    return hashlib.sha256(password.encode()).hexdigest()


ROOT_PASS_HASH = compute_password_hash("RootPass123")


@pytest.fixture
def client(arango_container_function):
    """Test client with database"""
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
    for collection in ["users", "user_groups"]:
        if not db.collection_exists(collection):
            db.create_collection(collection)
    
    # Clean existing test data
    for email in ["root@example.com", "manager@example.com", "user@example.com"]:
        existing = db.find_one("users", {"email": email})
        if existing:
            db.delete("users", existing["id"])
    
    # Create test users
    create_root_user(db)
    
    yield TestClient(app)


def create_root_user(db):
    """Create root user for tests"""
    return db.create("users", {
        "name": "Root User",
        "email": "root@example.com",
        "password_hash": hash_password(ROOT_PASS_HASH),
        "role": "root",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


def create_manager_user(db):
    """Create manager user for tests"""
    return db.create("users", {
        "name": "Manager User",
        "email": "manager@example.com",
        "password_hash": hash_password(ROOT_PASS_HASH),
        "role": "manager",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


def create_regular_user(db):
    """Create regular user for tests"""
    return db.create("users", {
        "name": "Regular User",
        "email": "user@example.com",
        "password_hash": hash_password(ROOT_PASS_HASH),
        "role": "user",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


def login_as(client, email):
    """Login and return token"""
    response = client.post("/api/auth/login", json={
        "email": email,
        "password_hash": ROOT_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.mark.integration
class TestUserGroupsList:
    """Test listing user groups"""
    
    def test_list_groups_as_root(self, client, arango_container_function):
        """Test root can list all groups"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        
        # Create some groups
        db.create("user_groups", {
            "name": "Engineering",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        db.create("user_groups", {
            "name": "Marketing",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.get(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        groups = response.json()["data"]
        assert len(groups) >= 2
    
    def test_list_groups_as_manager(self, client, arango_container_function):
        """Test manager sees only managed groups"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group with manager
        db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        # Create group without manager
        db.create("user_groups", {
            "name": "Other Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.get(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        groups = response.json()["data"]
        # Manager should only see groups they manage
        assert all(manager["id"] in g["managerIds"] for g in groups)
    
    def test_list_groups_as_user(self, client, arango_container_function):
        """Test user sees only groups they're member of"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Create group with user as member
        db.create("user_groups", {
            "name": "User's Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [user["id"]],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "user@example.com")
        
        response = client.get(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        groups = response.json()["data"]
        # User should only see groups they are member of
        assert all(user["id"] in g["memberIds"] for g in groups)


@pytest.mark.integration
class TestUserGroupsGet:
    """Test getting user group by ID"""
    
    def test_get_group_as_root(self, client, arango_container_function):
        """Test root can get any group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        
        # Create group
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.get(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == group["id"]
        assert data["name"] == "Test Group"
    
    def test_get_group_as_manager_of_group(self, client, arango_container_function):
        """Test manager can get their managed group"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group with manager
        group = db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.get(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_get_group_forbidden(self, client, arango_container_function):
        """Test user cannot get group they're not member of"""
        db = arango_container_function
        create_regular_user(db)
        
        # Create group without user
        group = db.create("user_groups", {
            "name": "Other Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "user@example.com")
        
        response = client.get(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_get_group_not_found(self, client, arango_container_function):
        """Test getting non-existent group"""
        token = login_as(client, "root@example.com")
        
        response = client.get(
            "/api/user-groups/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestUserGroupsCreate:
    """Test creating user groups"""
    
    def test_create_group_as_root(self, client, arango_container_function):
        """Test root can create group"""
        token = login_as(client, "root@example.com")
        
        response = client.post(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Engineering Team"}
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "New Engineering Team"
        assert data["status"] == "active"
        assert data["managerIds"] == []
        assert data["memberIds"] == []
    
    def test_create_group_as_manager_forbidden(self, client, arango_container_function):
        """Test manager cannot create group"""
        db = arango_container_function
        create_manager_user(db)
        
        token = login_as(client, "manager@example.com")
        
        response = client.post(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Forbidden Group"}
        )
        
        assert response.status_code == 403
    
    def test_create_group_as_user_forbidden(self, client, arango_container_function):
        """Test user cannot create group"""
        db = arango_container_function
        create_regular_user(db)
        
        token = login_as(client, "user@example.com")
        
        response = client.post(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Forbidden Group"}
        )
        
        assert response.status_code == 403


@pytest.mark.integration
class TestUserGroupsUpdate:
    """Test updating user groups"""
    
    def test_update_group_as_root(self, client, arango_container_function):
        """Test root can update group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        
        # Create group
        group = db.create("user_groups", {
            "name": "Old Name",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.put(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Name"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "New Name"
    
    def test_update_group_as_manager_of_group(self, client, arango_container_function):
        """Test manager CAN update groups they manage"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group WITH manager as manager
        group = db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],  # Manager manages this group
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.put(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated by Manager"}
        )
        
        # Manager CAN update groups they manage
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated by Manager"
    
    def test_update_group_as_manager_forbidden(self, client, arango_container_function):
        """Test manager CANNOT update groups they don't manage"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group WITHOUT manager in manager_ids
        group = db.create("user_groups", {
            "name": "Other Group",
            "status": "active",
            "manager_ids": [],  # Manager is NOT a manager of this group
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.put(
            f"/api/user-groups/{group['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Forbidden Update"}
        )
        
        # Manager CANNOT update groups they don't manage
        assert response.status_code == 403


@pytest.mark.integration
class TestUserGroupsStatus:
    """Test toggling group status"""
    
    def test_toggle_status_as_root(self, client, arango_container_function):
        """Test root can toggle group status"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        
        # Create active group
        group = db.create("user_groups", {
            "name": "Active Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        # Disable group
        response = client.put(
            f"/api/user-groups/{group['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "disabled"
        
        # Re-enable group
        response = client.put(
            f"/api/user-groups/{group['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "active"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "active"
    
    def test_toggle_status_as_manager(self, client, arango_container_function):
        """Test manager can toggle their managed group status"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group with manager
        group = db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.put(
            f"/api/user-groups/{group['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "disabled"


@pytest.mark.integration
class TestUserGroupsMembers:
    """Test member management"""
    
    def test_add_member_as_root(self, client, arango_container_function):
        """Test root can add member to group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        user = create_regular_user(db)
        
        # Create group
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.post(
            f"/api/user-groups/{group['id']}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": user["id"]}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert user["id"] in data["memberIds"]
    
    def test_add_member_as_manager(self, client, arango_container_function):
        """Test manager can add member to their group"""
        db = arango_container_function
        manager = create_manager_user(db)
        user = create_regular_user(db)
        
        # Create group with manager
        group = db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.post(
            f"/api/user-groups/{group['id']}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": user["id"]}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert user["id"] in data["memberIds"]
    
    def test_remove_member_as_root(self, client, arango_container_function):
        """Test root can remove member from group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        user = create_regular_user(db)
        
        # Create group with user as member
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [user["id"]],
            "created_at": datetime.utcnow()
        })
        
        response = client.delete(
            f"/api/user-groups/{group['id']}/members/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert user["id"] not in data["memberIds"]
    
    def test_add_member_forbidden_as_user(self, client, arango_container_function):
        """Test user cannot add member"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Create group
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [user["id"]],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "user@example.com")
        
        response = client.post(
            f"/api/user-groups/{group['id']}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": "another-user-id"}
        )
        
        assert response.status_code == 403


@pytest.mark.integration
class TestUserGroupsManagers:
    """Test manager assignment (root only)"""
    
    def test_assign_manager_as_root(self, client, arango_container_function):
        """Test root can assign manager to group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        manager = create_manager_user(db)
        
        # Create group
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.post(
            f"/api/user-groups/{group['id']}/managers",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": manager["id"]}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert manager["id"] in data["managerIds"]
    
    def test_remove_manager_as_root(self, client, arango_container_function):
        """Test root can remove manager from group"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        manager = create_manager_user(db)
        
        # Create group with manager
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.delete(
            f"/api/user-groups/{group['id']}/managers/{manager['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert manager["id"] not in data["managerIds"]
    
    def test_assign_manager_as_manager_forbidden(self, client, arango_container_function):
        """Test manager cannot assign other managers"""
        db = arango_container_function
        manager = create_manager_user(db)
        
        # Create group with manager
        group = db.create("user_groups", {
            "name": "Managed Group",
            "status": "active",
            "manager_ids": [manager["id"]],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        token = login_as(client, "manager@example.com")
        
        response = client.post(
            f"/api/user-groups/{group['id']}/managers",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": "another-manager-id"}
        )
        
        assert response.status_code == 403
    
    def test_assign_user_as_manager_requires_manager_role(self, client, arango_container_function):
        """Test cannot assign user without manager role as manager"""
        db = arango_container_function
        token = login_as(client, "root@example.com")
        user = create_regular_user(db)  # role="user"
        
        # Create group
        group = db.create("user_groups", {
            "name": "Test Group",
            "status": "active",
            "manager_ids": [],
            "member_ids": [],
            "created_at": datetime.utcnow()
        })
        
        response = client.post(
            f"/api/user-groups/{group['id']}/managers",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": user["id"]}
        )
        
        # Should fail - user doesn't have manager role
        assert response.status_code == 400
        assert "manager" in response.json()["detail"].lower() or "role" in response.json()["detail"].lower()