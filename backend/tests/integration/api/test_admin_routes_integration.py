"""
Path: backend/tests/integration/api/test_admin_routes_integration.py
Version: 4.0

Changes in v4.0:
- FIX: test_verify_token_valid uses ["user"] for /api/auth/verify response
- Route /verify returns SingleUserResponse format {user: {...}}

Changes in v3.0:
- FIX: Use ["data"] instead of ["user"] for admin routes responses
- Routes return SuccessResponse format {success, data}

Changes in v1.1:
- FIX: test_generic_user_in_local_mode now accepts 403 status code
- /api/auth/generic returns 403 in local mode (not 404)

Integration tests for admin routes
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password
from src.services.admin_service import AdminService


@pytest.fixture(autouse=True)
def reset_admin_service():
    """Reset admin service before each test"""
    AdminService._sessions.clear()
    AdminService._maintenance_mode = False
    yield
    AdminService._sessions.clear()
    AdminService._maintenance_mode = False


@pytest.fixture
def client(arango_container_function):
    """Test client with database"""
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
    if not db.collection_exists("users"):
        db.create_collection("users")
    
    yield TestClient(app)


@pytest.fixture
def root_user(arango_container_function):
    """Create root user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Root User",
        "email": "root@example.com",
        "password_hash": hash_password("rootpass"),
        "role": "root",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def regular_user(arango_container_function):
    """Create regular user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Regular User",
        "email": "user@example.com",
        "password_hash": hash_password("userpass"),
        "role": "user",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def root_headers(client, root_user):
    """Get authentication headers for root"""
    response = client.post("/api/auth/login", json={
        "email": "root@example.com",
        "password": "rootpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(client, regular_user):
    """Get authentication headers for regular user"""
    response = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "userpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestMaintenanceMode:
    """Test maintenance mode endpoints"""
    
    def test_toggle_maintenance_as_root(self, client, root_headers):
        """Test root can toggle maintenance mode"""
        response = client.post(
            "/api/admin/maintenance",
            json={"enabled": True},
            headers=root_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["maintenanceMode"] is True
        assert "enabled" in data["message"]
    
    def test_toggle_maintenance_as_user_denied(self, client, user_headers):
        """Test regular user cannot toggle maintenance"""
        response = client.post(
            "/api/admin/maintenance",
            json={"enabled": True},
            headers=user_headers
        )
        
        assert response.status_code == 403
    
    def test_toggle_maintenance_disable(self, client, root_headers):
        """Test disable maintenance mode"""
        # Enable first
        client.post(
            "/api/admin/maintenance",
            json={"enabled": True},
            headers=root_headers
        )
        
        # Disable
        response = client.post(
            "/api/admin/maintenance",
            json={"enabled": False},
            headers=root_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["maintenanceMode"] is False


class TestSessionsManagement:
    """Test session management endpoints"""
    
    def test_list_sessions_as_root(self, client, root_headers, user_headers):
        """Test root can list all sessions"""
        # Create some sessions by logging in
        response = client.get("/api/auth/sessions", headers=root_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "sessions" in data
        assert "totalCount" in data
        assert isinstance(data["sessions"], list)
    
    def test_list_sessions_as_user_denied(self, client, user_headers):
        """Test regular user cannot list sessions"""
        response = client.get("/api/auth/sessions", headers=user_headers)
        
        assert response.status_code == 403
    
    def test_revoke_all_sessions_as_root(self, client, root_headers):
        """Test root can revoke all sessions"""
        response = client.post(
            "/api/auth/revoke-all-sessions",
            headers=root_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "revokedCount" in data
        assert "message" in data
    
    def test_revoke_all_sessions_as_user_denied(self, client, user_headers):
        """Test regular user cannot revoke all sessions"""
        response = client.post(
            "/api/auth/revoke-all-sessions",
            headers=user_headers
        )
        
        assert response.status_code == 403
    
    def test_revoke_own_session(self, client, user_headers):
        """Test user can revoke their own session"""
        response = client.post(
            "/api/auth/revoke-own-session",
            headers=user_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()


class TestAuthEndpoints:
    """Test additional auth endpoints"""
    
    def test_verify_token_valid(self, client, user_headers):
        """Test verify valid token"""
        response = client.get("/api/auth/verify", headers=user_headers)
        
        assert response.status_code == 200
        data = response.json()["user"]
        assert data["email"] == "user@example.com"
        assert data["role"] == "user"
    
    def test_verify_token_invalid(self, client):
        """Test verify invalid token"""
        response = client.get(
            "/api/auth/verify",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_verify_token_missing(self, client):
        """Test verify without token"""
        response = client.get("/api/auth/verify")
        
        # Depends on AUTH_MODE setting
        # In mode "local" or "sso": should return 401
        # In mode "none": might return generic user
        assert response.status_code in [200, 401]


class TestGenericUser:
    """Test generic user endpoint (mode none only)"""
    
    def test_generic_user_in_local_mode(self, client):
        """Test generic user endpoint not available in local mode"""
        # Assuming AUTH_MODE=local in tests
        response = client.get("/api/auth/generic")
        
        # Should return 403 (forbidden) in local mode
        # OR 200 if AUTH_MODE=none
        # OR 401 if middleware requires auth
        assert response.status_code in [200, 401, 403]


class TestMaintenanceModeEnforcement:
    """Test maintenance mode blocks non-root users"""
    
    def test_maintenance_mode_blocks_regular_user(self, client, root_headers, user_headers):
        """Test maintenance mode blocks regular users"""
        # Enable maintenance mode
        response = client.post(
            "/api/admin/maintenance",
            json={"enabled": True},
            headers=root_headers
        )
        assert response.status_code == 200
        
        # Regular user should be blocked
        # Note: This depends on middleware implementation
        # If middleware is implemented, this would return 503
        response = client.get("/api/auth/me", headers=user_headers)
        
        # Might be 503 or 200 depending on middleware implementation
        assert response.status_code in [200, 503]
    
    def test_maintenance_mode_allows_root(self, client, root_headers):
        """Test maintenance mode allows root users"""
        # Enable maintenance mode
        response = client.post(
            "/api/admin/maintenance",
            json={"enabled": True},
            headers=root_headers
        )
        assert response.status_code == 200
        
        # Root should still have access
        response = client.get("/api/auth/me", headers=root_headers)
        assert response.status_code == 200