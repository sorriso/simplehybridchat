"""
Path: backend/tests/integration/api/test_users_routes_integration.py
Version: 6.0

Changes in v6:
- Updated response format to match frontend spec
- POST/GET/PUT /api/users now return {"user": {...}} instead of {"data": {...}}
- GET /api/users returns {"users": [...]} instead of {"data": [...]}
- DELETE still returns {"success": true, "message": "..."}

Changes in v5:
- Fixed 9 remaining _key references Ã¢â€ â€™ id (lines 234, 261, 286, 311, 337, 363, 391, 415, 442)
- All user/manager/root_user accesses now use ['id']

Changes in v4:
- Fixed cleanup: existing_root["_key"] Ã¢â€ â€™ existing_root["id"]
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
        "createdAt": datetime.utcnow(),
        "updatedAt": None
    })


def create_manager_user(db):
    """Helper to create manager user"""
    return db.create("users", {
        "name": "Manager User",
        "email": "manager@example.com",
        "password_hash": hash_password("RootPass123"),
        "role": "manager",
        "status": "active",
        "createdAt": datetime.utcnow(),
        "updatedAt": None
    })


def create_regular_user(db):
    """Helper to create regular user"""
    return db.create("users", {
        "name": "Regular User",
        "email": "user@example.com",
        "password_hash": hash_password("RootPass123"),
        "role": "user",
        "status": "active",
        "createdAt": datetime.utcnow(),
        "updatedAt": None
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
        token = login_response.json()["token"]
        
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
        user = response.json()["user"]
        
        assert user["name"] == "New User"
        assert user["email"] == "newuser@example.com"
        assert user["role"] == "user"
        assert "password" not in user
    
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
        token = login_response.json()["token"]
        
        # Try to create user
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "NewPass123"
            }
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "user"
        assert "permission" in response.json()["detail"].lower()
    
    def test_create_user_as_user_forbidden(self, client, arango_container_function):
        """Test regular user cannot create users"""
        db = arango_container_function
        create_regular_user(db)
        
        # Login as user
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Try to create user
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "NewPass123"
            }
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "user"
        assert "permission" in response.json()["detail"].lower()
    
    def test_list_users_as_root(self, client, arango_container_function):
        """Test root can list all users"""
        db = arango_container_function
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # List users
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        users = response.json()["users"]
        
        assert isinstance(users, list)
        assert len(users) >= 1  # At least root user
        assert any(u["email"] == "root@example.com" for u in users)
    
    def test_get_user_by_id(self, client, arango_container_function):
        """Test getting user by ID"""
        db = arango_container_function
        
        # Create a test user
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Get user by ID
        response = client.get(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        retrieved_user = response.json()["user"]
        
        assert retrieved_user["id"] == user["id"]
        assert retrieved_user["email"] == "user@example.com"
    
    def test_update_user(self, client, arango_container_function):
        """Test updating user"""
        db = arango_container_function
        
        # Create a test user
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Update user
        response = client.put(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated User Name"
            }
        )
        
        assert response.status_code == 200
        updated_user = response.json()["user"]
        
        assert updated_user["name"] == "Updated User Name"
        assert updated_user["id"] == user["id"]
    
    def test_delete_user(self, client, arango_container_function):
        """Test deleting user"""
        db = arango_container_function
        
        # Create a test user
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Delete user
        response = client.delete(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify user is deleted
        verify_response = client.get(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert verify_response.status_code == 404
    
    def test_delete_user_as_root(self, client, arango_container_function):
        """Test root can delete users"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Delete user
        response = client.delete(
            f"/api/users/{user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
    def test_delete_self_forbidden(self, client, arango_container_function):
        """Test user cannot delete themselves"""
        db = arango_container_function
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Get root user
        root_user = db.find_one("users", {"email": "root@example.com"})
        
        # Try to delete self
        response = client.delete(
            f"/api/users/{root_user['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "user"
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
        token = login_response.json()["token"]
        
        # Try to list users (manager+ only)
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        # Error responses have "detail", not "user"
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
        token = login_response.json()["token"]
        
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
        # Error responses have "detail", not "user"
        assert "permission" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUserStatusToggle:
    """Test user status toggle endpoint"""
    
    def test_toggle_user_status_as_root(self, client, arango_container_function):
        """Test root can toggle user status"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Disable user
        response = client.put(
            f"/api/users/{user['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        
        assert response.status_code == 200
        updated_user = response.json()["user"]
        assert updated_user["status"] == "disabled"
        
        # Re-enable user
        response = client.put(
            f"/api/users/{user['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "active"}
        )
        
        assert response.status_code == 200
        updated_user = response.json()["user"]
        assert updated_user["status"] == "active"
    
    def test_toggle_self_status_forbidden(self, client, arango_container_function):
        """Test cannot disable own account"""
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Get root user
        db = arango_container_function
        root_user = db.find_one("users", {"email": "root@example.com"})
        
        # Try to disable self
        response = client.put(
            f"/api/users/{root_user['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        
        assert response.status_code == 403
        assert "cannot disable yourself" in response.json()["detail"].lower()
    
    def test_toggle_status_as_user_forbidden(self, client, arango_container_function):
        """Test regular user cannot toggle status"""
        db = arango_container_function
        user1 = create_regular_user(db)
        user2 = db.create("users", {
            "name": "User Two",
            "email": "user2@example.com",
            "password_hash": hash_password("RootPass123"),
            "role": "user",
            "status": "active",
            "createdAt": datetime.utcnow(),
            "updatedAt": None
        })
        
        # Login as user1
        login_response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Try to disable user2
        response = client.put(
            f"/api/users/{user2['id']}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUserRoleAssignment:
    """Test user role assignment endpoint"""
    
    def test_assign_role_as_root(self, client, arango_container_function):
        """Test root can assign roles"""
        db = arango_container_function
        user = create_regular_user(db)
        
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Promote to manager
        response = client.put(
            f"/api/users/{user['id']}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "manager"}
        )
        
        assert response.status_code == 200
        updated_user = response.json()["user"]
        assert updated_user["role"] == "manager"
        
        # Demote to user
        response = client.put(
            f"/api/users/{user['id']}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "user"}
        )
        
        assert response.status_code == 200
        updated_user = response.json()["user"]
        assert updated_user["role"] == "user"
    
    def test_assign_role_as_manager_forbidden(self, client, arango_container_function):
        """Test manager cannot assign roles"""
        db = arango_container_function
        manager = create_manager_user(db)
        user = create_regular_user(db)
        
        # Login as manager
        login_response = client.post("/api/auth/login", json={
            "email": "manager@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Try to promote user
        response = client.put(
            f"/api/users/{user['id']}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "manager"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_demote_self_from_root_forbidden(self, client, arango_container_function):
        """Test cannot demote yourself from root"""
        # Login as root
        login_response = client.post("/api/auth/login", json={
            "email": "root@example.com",
            "password": "RootPass123"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Get root user
        db = arango_container_function
        root_user = db.find_one("users", {"email": "root@example.com"})
        
        # Try to demote self
        response = client.put(
            f"/api/users/{root_user['id']}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "user"}
        )
        
        assert response.status_code == 403
        assert "cannot demote yourself" in response.json()["detail"].lower()