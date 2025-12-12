"""
Path: backend/tests/integration/api/test_auth_routes_integration.py
Version: 7.0

Changes in v7.0:
- FIX: Use ["data"] instead of ["user"] for /auth/me responses
- Route /auth/me returns SuccessResponse format {success, data}

Changes in v6.0:
- FRONTEND COMPATIBILITY: Updated for new auth response formats
- /login returns {token, user} instead of {success, data: {accessToken, ...}}
- /config returns {config: {...}} instead of {success, data: {...}}
- /verify and /me return {user: {...}} instead of {success, data: {...}}

Integration tests for authentication routes

Changes in v5:
- Fixed cleanup: existing["_key"] â†’ existing["id"]
- Final cleanup of remaining _key references

Changes in v4:
- Fixed test_get_me_success and test_complete_auth_flow: /api/users/me -> /api/auth/me
- Endpoint is on auth router (/api/auth), not users router

Changes in v3:
- Already using hash_password() dynamically in fixture (no changes needed)

Changes in v2:
- Fixed test_register_duplicate_email to expect 409 instead of 400
- Fixed test_get_me_success and test_complete_auth_flow to use UserService(db=db)

Changes in v1:
- FIX CRITIQUE: Toutes les assertions utilisent response.json()["data"] correctement
- Ajout test /api/auth/me (get_me_success)
- Ajout tests change_password
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client(arango_container_function):
    """Test client with database and root user"""
    from src.core.security import hash_password
    from datetime import datetime
    
    db = arango_container_function
    
    # Create users collection
    if not db.collection_exists("users"):
        db.create_collection("users")
    
    # Create root user for tests
    root_user = {
        "name": "Root User",
        "email": "root@test.com",
        "password_hash": hash_password("RootPass123"),
        "role": "root",
        "status": "active",
        "createdAt": datetime.utcnow(),
        "updatedAt": None
    }
    
    # Delete if exists (cleanup from previous test)
    existing = db.find_one("users", {"email": "root@test.com"})
    if existing:
        db.delete("users", existing["id"])
    
    # Create root user
    db.create("users", root_user)
    
    yield TestClient(app)


@pytest.mark.integration
class TestAuthRoutesIntegration:
    """Integration tests for auth routes"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "StrongPass123"
        })
        
        assert response.status_code == 201
        
        # STRUCTURE: {"success": true, "data": {...}, "message": "..."}
        json_response = response.json()
        assert "data" in json_response
        data = json_response["data"]
        
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert data["status"] == "active"
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_register_duplicate_email(self, client):
        """Test registering with duplicate email"""
        # Register first user
        client.post("/api/auth/register", json={
            "name": "User 1",
            "email": "duplicate@example.com",
            "password": "StrongPass123"
        })
        
        # Try to register with same email
        response = client.post("/api/auth/register", json={
            "name": "User 2",
            "email": "duplicate@example.com",
            "password": "AnotherPass456"
        })
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "weak"
        })
        
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "not-an-email",
            "password": "StrongPass123"
        })
        
        assert response.status_code == 422
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user first
        client.post("/api/auth/register", json={
            "name": "Login Test",
            "email": "login@example.com",
            "password": "StrongPass123"
        })
        
        # Login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "StrongPass123"
        })
        
        assert response.status_code == 200
        
        # STRUCTURE: {"token": "...", "user": {...}}
        json_response = response.json()
        assert "token" in json_response
        assert "user" in json_response
        assert len(json_response["token"]) > 0
        assert json_response["user"]["email"] == "login@example.com"
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # Register user
        client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "CorrectPass123"
        })
        
        # Try login with wrong password
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPass456"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "AnyPass123"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_me_success(self, client):
        """Test get current user profile"""
        # Register and login
        client.post("/api/auth/register", json={
            "name": "Me Test",
            "email": "me@example.com",
            "password": "StrongPass123"
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "me@example.com",
            "password": "StrongPass123"
        })
        
        # Extract token correctly
        token = login_response.json()["token"]
        
        # Get own profile
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "me@example.com"
    
    def test_logout(self, client):
        """Test logout endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "name": "Logout Test",
            "email": "logout@example.com",
            "password": "StrongPass123"
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "logout@example.com",
            "password": "StrongPass123"
        })
        
        # Extract token correctly
        token = login_response.json()["token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_change_password_success(self, client):
        """Test successful password change"""
        # Register and login
        client.post("/api/auth/register", json={
            "name": "Password Test",
            "email": "password@example.com",
            "password": "OldPass123"
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password": "OldPass123"
        })
        
        token = login_response.json()["token"]
        
        # Change password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "OldPass123",
                "new_password": "NewPass456"
            }
        )
        
        assert response.status_code == 200
        
        # Login with new password should work
        new_login = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password": "NewPass456"
        })
        assert new_login.status_code == 200
    
    def test_change_password_wrong_current(self, client):
        """Test password change with wrong current password"""
        # Register and login
        client.post("/api/auth/register", json={
            "name": "Password Test",
            "email": "password2@example.com",
            "password": "CorrectPass123"
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "password2@example.com",
            "password": "CorrectPass123"
        })
        
        token = login_response.json()["token"]
        
        # Try to change with wrong current password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPass123",
                "new_password": "NewPass456"
            }
        )
        
        assert response.status_code == 401
    
    def test_get_auth_config(self, client):
        """Test get authentication configuration"""
        response = client.get("/api/auth/config")
        
        assert response.status_code == 200
        config = response.json()["config"]
        
        assert "mode" in config
        assert config["mode"] in ["none", "local", "sso"]
        assert "maintenanceMode" in config


@pytest.mark.integration
class TestAuthFlow:
    """Test complete authentication flow"""
    
    def test_complete_auth_flow(self, client):
        """Test register -> login -> authenticated request -> logout"""
        # 1. Register
        register_response = client.post("/api/auth/register", json={
            "name": "Flow Test",
            "email": "flow@example.com",
            "password": "StrongPass123"
        })
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post("/api/auth/login", json={
            "email": "flow@example.com",
            "password": "StrongPass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # 3. Authenticated request (get own profile)
        profile_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()["data"]
        assert profile_data["email"] == "flow@example.com"
        
        # 4. Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200