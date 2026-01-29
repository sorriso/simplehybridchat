"""
Path: backend/tests/integration/api/test_auth_routes_mode_sso.py
Version: 3.0

Changes in v3.0:
- FIX: Use password_hash instead of password for login/register tests
- LoginRequest and RegisterRequest models expect password_hash (SHA256, 64 chars)
- Pydantic validation was failing (422) before mode check could return 403

Changes in v1.1:
- FIX: Corrected fixture to patch AUTH_MODE and SSO headers at attribute level
- FIX: Patch in both config and middleware modules
- Ensures SSO configuration is visible to all imported modules

Integration tests for auth endpoints in "sso" mode
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import datetime

from src.core.security import hash_password


# Valid SHA256 hash (64 hex characters) for tests
# This is SHA256("Password123") - actual value doesn't matter for mode check tests
VALID_SHA256_HASH = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"


@pytest.fixture
def client_sso_mode(arango_container_function):
    """Test client with AUTH_MODE=sso"""
    # Patch settings in both config and middleware modules
    with patch('src.core.config.settings.AUTH_MODE', 'sso'), \
         patch('src.middleware.auth_middleware.settings.AUTH_MODE', 'sso'), \
         patch('src.core.config.settings.SSO_TOKEN_HEADER', 'X-Auth-Token'), \
         patch('src.middleware.auth_middleware.settings.SSO_TOKEN_HEADER', 'X-Auth-Token'), \
         patch('src.core.config.settings.SSO_NAME_HEADER', 'X-User-Name'), \
         patch('src.middleware.auth_middleware.settings.SSO_NAME_HEADER', 'X-User-Name'), \
         patch('src.core.config.settings.SSO_EMAIL_HEADER', 'X-User-Email'), \
         patch('src.middleware.auth_middleware.settings.SSO_EMAIL_HEADER', 'X-User-Email'):
        
        from src.main import app
        
        db = arango_container_function
        
        # Ensure collections exist
        if not db.collection_exists("users"):
            db.create_collection("users")
        
        client = TestClient(app)
        yield client, db


class TestAuthModeSSO:
    """Test auth endpoints in 'sso' mode"""
    
    def test_sso_verify_endpoint_new_user(self, client_sso_mode):
        """Test /auth/sso/verify creates new user"""
        client, db = client_sso_mode
        
        response = client.get(
            "/api/auth/sso/verify",
            headers={
                "X-Auth-Token": "sso-token-123",
                "X-User-Name": "Jane Doe",
                "X-User-Email": "jane@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should return user info
        assert data["user"]["email"] == "jane@example.com"
        assert data["user"]["name"] == "Jane Doe"
        assert data["user"]["role"] == "user"
        assert data["tokenType"] == "sso"
        
        # User should be created in database
        user = db.find_one("users", {"email": "jane@example.com"})
        assert user is not None
        assert user["name"] == "Jane Doe"
    
    def test_sso_verify_endpoint_existing_user(self, client_sso_mode):
        """Test /auth/sso/verify with existing user"""
        client, db = client_sso_mode
        
        # Create existing user
        db.create("users", {
            "name": "Existing User",
            "email": "existing@example.com",
            "password_hash": hash_password("dummy"),
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
        
        response = client.get(
            "/api/auth/sso/verify",
            headers={
                "X-Auth-Token": "sso-token-456",
                "X-User-Name": "Existing User",
                "X-User-Email": "existing@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should return existing user
        assert data["user"]["email"] == "existing@example.com"
        assert data["user"]["name"] == "Existing User"
    
    def test_sso_verify_missing_headers(self, client_sso_mode):
        """Test /auth/sso/verify fails without required headers"""
        client, _ = client_sso_mode
        
        # Missing email header
        response = client.get(
            "/api/auth/sso/verify",
            headers={
                "X-Auth-Token": "sso-token-789"
            }
        )
        
        assert response.status_code == 401
        assert "Missing" in response.json()["detail"]
    
    def test_sso_verify_without_name_header(self, client_sso_mode):
        """Test /auth/sso/verify works without name header"""
        client, db = client_sso_mode
        
        response = client.get(
            "/api/auth/sso/verify",
            headers={
                "X-Auth-Token": "sso-token-999",
                "X-User-Email": "noname@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should use email prefix as name
        assert data["user"]["email"] == "noname@example.com"
        assert data["user"]["name"] == "noname"
    
    def test_login_endpoint_forbidden_in_sso_mode(self, client_sso_mode):
        """Test /auth/login returns 403 in 'sso' mode"""
        client, _ = client_sso_mode
        
        # Must use password_hash (SHA256, 64 chars) - LoginRequest model requirement
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password_hash": VALID_SHA256_HASH
        })
        
        # Should be forbidden (mode check happens after validation)
        assert response.status_code == 403
        assert "sso" in response.json()["detail"].lower()
    
    def test_register_endpoint_forbidden_in_sso_mode(self, client_sso_mode):
        """Test /auth/register returns 403 in 'sso' mode"""
        client, _ = client_sso_mode
        
        # Must use password_hash (SHA256, 64 chars) - RegisterRequest model requirement
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password_hash": VALID_SHA256_HASH
        })
        
        # Should be forbidden (mode check happens after validation)
        assert response.status_code == 403
        assert "sso" in response.json()["detail"].lower()
    
    def test_config_endpoint_shows_sso_mode(self, client_sso_mode):
        """Test /auth/config returns 'sso' mode info"""
        client, _ = client_sso_mode
        
        response = client.get("/api/auth/config")
        
        assert response.status_code == 200
        data = response.json()["config"]
        
        assert data["mode"] == "sso"
        assert data["ssoConfig"] is not None
        assert data["ssoConfig"]["tokenHeader"] == "X-Auth-Token"
        assert data["ssoConfig"]["nameHeader"] == "X-User-Name"
        assert data["ssoConfig"]["emailHeader"] == "X-User-Email"


class TestAuthModeSSO_Middleware:
    """Test middleware behavior in 'sso' mode"""
    
    def test_protected_endpoints_require_sso_headers(self, client_sso_mode):
        """Test protected endpoints require SSO headers"""
        client, db = client_sso_mode
        
        # Try to access protected endpoint without SSO headers
        response = client.get("/api/auth/me")
        
        # Should require SSO headers
        assert response.status_code == 401
        assert "Missing" in response.json()["error"]
    
    def test_protected_endpoints_work_with_sso_headers(self, client_sso_mode):
        """Test protected endpoints work with valid SSO headers"""
        client, db = client_sso_mode
        
        # Create user first
        db.create("users", {
            "name": "SSO User",
            "email": "ssouser@example.com",
            "password_hash": hash_password("dummy"),
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
        
        # Access protected endpoint with SSO headers
        response = client.get(
            "/api/auth/me",
            headers={
                "X-Auth-Token": "valid-token",
                "X-User-Email": "ssouser@example.com",
                "X-User-Name": "SSO User"
            }
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "ssouser@example.com"
    
    def test_auto_creates_user_on_first_access(self, client_sso_mode):
        """Test middleware auto-creates user on first access"""
        client, db = client_sso_mode
        
        # Ensure collections exist
        if not db.collection_exists("conversations"):
            db.create_collection("conversations")
        
        # Access protected endpoint with new user SSO headers
        response = client.get(
            "/api/conversations",
            headers={
                "X-Auth-Token": "new-user-token",
                "X-User-Email": "newuser@example.com",
                "X-User-Name": "New User"
            }
        )
        
        # Should succeed (user auto-created by middleware)
        assert response.status_code == 200
        
        # User should exist in database
        user = db.find_one("users", {"email": "newuser@example.com"})
        assert user is not None
        assert user["name"] == "New User"


class TestAuthModeSSO_VsLocal:
    """Test that 'sso' mode behaves differently from 'local' mode"""
    
    def test_sso_verify_not_available_in_local_mode(self, arango_container_function):
        """Test /auth/sso/verify returns 403 in 'local' mode"""
        with patch('src.core.config.settings.AUTH_MODE', 'local'), \
             patch('src.middleware.auth_middleware.settings.AUTH_MODE', 'local'):
            
            from src.main import app
            client = TestClient(app)
            
            response = client.get(
                "/api/auth/sso/verify",
                headers={
                    "X-Auth-Token": "token",
                    "X-User-Email": "test@example.com"
                }
            )
            
            # Should be forbidden in local mode
            assert response.status_code == 403
            assert "local" in response.json()["detail"].lower()