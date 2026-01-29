"""
Path: backend/tests/integration/api/test_auth_routes_integration.py
Version: 9.0

Changes in v9.0:
- FIX CRITICAL: Use password_hash (SHA256) instead of password for all API calls
- LoginRequest requires password_hash (64 hex chars), not password
- RegisterRequest requires password_hash (64 hex chars), not password
- Added compute_password_hash() helper function

Changes in v8.0:
- FIX CRITICAL: Moved 'from src.main import app' INSIDE fixture

Integration tests for authentication routes
"""

import pytest
import hashlib
from fastapi.testclient import TestClient


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend behavior)"""
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hashes for test passwords
ROOT_PASS_HASH = compute_password_hash("RootPass123")
TEST_PASS_HASH = compute_password_hash("StrongPass123")
NEW_PASS_HASH = compute_password_hash("NewPass456")
OLD_PASS_HASH = compute_password_hash("OldPass123")
CORRECT_PASS_HASH = compute_password_hash("CorrectPass123")
WRONG_PASS_HASH = compute_password_hash("WrongPass456")
ANOTHER_PASS_HASH = compute_password_hash("AnotherPass456")
ANY_PASS_HASH = compute_password_hash("AnyPass123")


@pytest.fixture
def client(arango_container_function):
    """Test client with database and root user"""
    # CRITICAL: Import app INSIDE fixture, after container is ready
    from src.main import app
    from src.core.security import hash_password
    from datetime import datetime
    
    db = arango_container_function
    
    # Create users collection
    if not db.collection_exists("users"):
        db.create_collection("users")
    
    # Create root user for tests
    # Store bcrypt(SHA256(password)) in DB
    root_user = {
        "name": "Root User",
        "email": "root@test.com",
        "password_hash": hash_password(ROOT_PASS_HASH),
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
            "password_hash": TEST_PASS_HASH
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
            "password_hash": TEST_PASS_HASH
        })
        
        # Try to register with same email
        response = client.post("/api/auth/register", json={
            "name": "User 2",
            "email": "duplicate@example.com",
            "password_hash": ANOTHER_PASS_HASH
        })
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password hash (invalid length)"""
        # SHA256 must be exactly 64 chars - this is too short
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password_hash": "tooshort"
        })
        
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "not-an-email",
            "password_hash": TEST_PASS_HASH
        })
        
        assert response.status_code == 422
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user first
        login_pass_hash = compute_password_hash("LoginPass123")
        client.post("/api/auth/register", json={
            "name": "Login Test",
            "email": "login@example.com",
            "password_hash": login_pass_hash
        })
        
        # Login with same hash
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password_hash": login_pass_hash
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
            "password_hash": CORRECT_PASS_HASH
        })
        
        # Try login with wrong password hash
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password_hash": WRONG_PASS_HASH
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password_hash": ANY_PASS_HASH
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_me_success(self, client):
        """Test get current user profile"""
        # Register and login
        me_pass_hash = compute_password_hash("MePass123")
        client.post("/api/auth/register", json={
            "name": "Me Test",
            "email": "me@example.com",
            "password_hash": me_pass_hash
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "me@example.com",
            "password_hash": me_pass_hash
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
        logout_pass_hash = compute_password_hash("LogoutPass123")
        client.post("/api/auth/register", json={
            "name": "Logout Test",
            "email": "logout@example.com",
            "password_hash": logout_pass_hash
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "logout@example.com",
            "password_hash": logout_pass_hash
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
            "password_hash": OLD_PASS_HASH
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password_hash": OLD_PASS_HASH
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
            "password_hash": NEW_PASS_HASH
        })
        assert new_login.status_code == 200
    
    def test_change_password_wrong_current(self, client):
        """Test password change with wrong current password"""
        # Register and login
        client.post("/api/auth/register", json={
            "name": "Password Test",
            "email": "password2@example.com",
            "password_hash": CORRECT_PASS_HASH
        })
        
        login_response = client.post("/api/auth/login", json={
            "email": "password2@example.com",
            "password_hash": CORRECT_PASS_HASH
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
        flow_pass_hash = compute_password_hash("FlowPass123")
        
        # 1. Register
        register_response = client.post("/api/auth/register", json={
            "name": "Flow Test",
            "email": "flow@example.com",
            "password_hash": flow_pass_hash
        })
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post("/api/auth/login", json={
            "email": "flow@example.com",
            "password_hash": flow_pass_hash
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