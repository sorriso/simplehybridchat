"""
Path: tests/integration/api/test_users_routes_integration.py
Version: 5

Changes in v5:
- Fixed 9 remaining _key references → id (lines 234, 261, 286, 311, 337, 363, 391, 415, 442)
- All user/manager/root_user accesses now use ['id']

Changes in v4:
- Fixed cleanup: existing_root["_key"] → existing_root["id"]
- Matches adapter behavior (returns 'id')

Changes in v3:
- Already using hash_password() dynamically in fixtures

Integration tests for user management routes

Changes in v3:
- Removed pre-calculated bcrypt hash constant
- All helpers now generate hash dynamically using hash_password()
- Import hash_password from src.core.security

Changes in v2:
- Fixed test_create_user_as_root: removed duplicate create_root_user call
- Fixed test_delete_user_as_root: removed duplicate create_root_user call
- Fixed all forbidden tests: use response.json()["detail"] for error responses instead of ["data"]
- Tests expecting 403/401 now correctly access error detail, not data

Changes in v1:
- Added created_at/updated_at to all create_*_user helpers
- Import datetime
- FIX CRITIQUE: All response.json() accesses use ["data"]
- Systematic verification of "data" presence
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
    
    if not db.collection_exists("users"):
        db.create_collection("users")
    
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


def create_manager_user(db):
    """Helper to create manager user"""
    return db.create("users", {
        "name": "Manager User",
        "email": "manager@example.com",
        "password_hash": hash_password("RootPass123"),
        "role": "manager",
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


@pytest.mark.integration
class TestUsersRoutesIntegration:
    """Integration tests for user management routes"""
    
    def test_create_user_as_root(self, client, arango_container_function):
        """Test root can create users"""
        # Root user already created by fixture - no need to create again
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Create new user
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "NewPass123",
                "role": "user",
                "status": "active"
            }
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        
        assert data["name"] == "New User"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "password" not in data
    
    def test_create_user_as_manager_forbidden(self, client, arango_container_function):
        """Test manager cannot create users"""
        db = arango_container_function
        create_manager_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to create user
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "NewPass123",
                "role": "user",
                "status": "active"
            }
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_list_users_as_regular_forbidden(self, client, arango_container_function):
        """Test regular user cannot list users"""
        db = arango_container_function
        create_regular_user(db)
        
        # Login as regular user
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to list users
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_list_users_as_manager(self, client, arango_container_function):
        """Test manager can list users"""
        db = arango_container_function
        create_manager_user(db)
        create_regular_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # List users
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should have at least root, manager, and regular user
        assert len(data) >= 3
    
    def test_get_own_profile(self, client, arango_container_function):
        """Test user can get their own profile"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Get own profile
        response = client.get(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["email"] == "user@example.com"
        assert data["role"] == "user"
    
    def test_get_other_user_as_regular_forbidden(self, client, arango_container_function):
        """Test regular user cannot get other user's profile"""
        db = arango_container_function
        create_regular_user(db)
        manager = create_manager_user(db)
        
        # Login as regular user
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to get manager's profile
        response = client.get(
            f"/api/users/{manager['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_get_user_by_id_as_manager(self, client, arango_container_function):
        """Test manager can get any user's profile"""
        db = arango_container_function
        create_manager_user(db)
        user = create_regular_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Get user profile
        response = client.get(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["email"] == "user@example.com"
    
    def test_update_own_profile(self, client, arango_container_function):
        """Test user can update their own profile"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Update own profile
        response = client.put(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["name"] == "Updated Name"
    
    def test_update_own_role_forbidden(self, client, arango_container_function):
        """Test user cannot update their own role"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to update own role
        response = client.put(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "root"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_update_user_role_as_manager(self, client, arango_container_function):
        """Test manager can update user role"""
        db = arango_container_function
        create_manager_user(db)
        user = create_regular_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Update user role
        response = client.put(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "manager"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["role"] == "manager"
    
    def test_delete_user_as_root(self, client, arango_container_function):
        """Test root can delete users"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Root user already created by fixture - no need to create again
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Delete user
        response = client.delete(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_delete_user_as_manager_forbidden(self, client, arango_container_function):
        """Test manager cannot delete users"""
        db = arango_container_function
        create_manager_user(db)
        user = create_regular_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to delete user
        response = client.delete(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_delete_self_forbidden(self, client, arango_container_function):
        """Test user cannot delete themselves"""
        # Root user already created by fixture
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Get own user ID from token
        db = arango_container_function
        root_user = db.find_one("users", {"email": "root@example.com"})
        
        # Try to delete self
        response = client.delete(
            f"/api/users/{root_user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "cannot delete yourself" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUserPermissions:
    """Test permission system thoroughly"""
    
    def test_user_cannot_access_manager_endpoints(self, client, arango_container_function):
        """Test user role cannot access manager-only endpoints"""
        db = arango_container_function
        create_regular_user(db)
        
        # Login as user
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to list users (manager+ only)
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()
    
    def test_manager_cannot_access_root_endpoints(self, client, arango_container_function):
        """Test manager role cannot access root-only endpoints"""
        db = arango_container_function
        create_manager_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # Try to create user (root only)
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "NewPass123",
                "role": "user",
                "status": "active"
            }
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "data"
        assert "permission" in response.json()["detail"].lower()