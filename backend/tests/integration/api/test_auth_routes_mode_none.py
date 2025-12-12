"""
Path: backend/tests/integration/api/test_auth_routes_mode_none.py
Version: 2.0.3

Changes in v1.3:
- FIX: test_change_password_forbidden uses valid passwords for Pydantic validation
- Changed "new123" (6 chars) to "NewPass456" (10 chars) to pass min_length=8 requirement

Changes in v1.2:
- FIX: test_change_password_forbidden now uses snake_case (current_password, new_password)
- PasswordChange model expects snake_case, not camelCase

Changes in v1.1:
- FIX: Corrected fixture to patch AUTH_MODE at attribute level
- FIX: Patch in both config and middleware modules
- Ensures AUTH_MODE changes are visible to all imported modules

Integration tests for auth endpoints in "none" mode
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client_none_mode(arango_container_function):
    """Test client with AUTH_MODE=none"""
    # Patch settings in both config and middleware modules
    with patch('src.core.config.settings.AUTH_MODE', 'none'), \
         patch('src.middleware.auth_middleware.settings.AUTH_MODE', 'none'):
        
        from src.main import app
        client = TestClient(app)
        yield client


class TestAuthModeNone:
    """Test auth endpoints in 'none' mode"""
    
    def test_generic_endpoint_returns_user(self, client_none_mode):
        """Test GET /auth/generic returns generic user"""
        response = client_none_mode.get("/api/auth/generic")
        
        assert response.status_code == 200
        data = response.json()["user"]
        
        # Should return generic user
        assert data["id"] == "user-generic"
        assert data["name"] == "John Doe"
        assert data["email"] == "generic@example.com"
        assert data["role"] == "user"
        assert data["status"] == "active"
    
    def test_protected_endpoints_accessible_without_token(self, client_none_mode):
        """Test protected endpoints work without token in 'none' mode"""
        # Try to access protected endpoint without token
        response = client_none_mode.get("/api/auth/me")
        
        # Should succeed (generic user injected by middleware)
        assert response.status_code == 200
    
    def test_login_endpoint_forbidden(self, client_none_mode):
        """Test /auth/login returns 403 in 'none' mode"""
        response = client_none_mode.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        
        # Should be forbidden
        assert response.status_code == 403
        assert "none" in response.json()["detail"].lower()
    
    def test_register_endpoint_forbidden(self, client_none_mode):
        """Test /auth/register returns 403 in 'none' mode"""
        response = client_none_mode.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password123"
        })
        
        # Should be forbidden
        assert response.status_code == 403
        assert "none" in response.json()["detail"].lower()
    
    def test_change_password_forbidden(self, client_none_mode):
        """Test /auth/change-password returns 403 in 'none' mode"""
        response = client_none_mode.post("/api/auth/change-password", json={
            "current_password": "OldPass123",
            "new_password": "NewPass456"
        })
        
        # Should be forbidden
        assert response.status_code == 403
        assert "none" in response.json()["detail"].lower()
    
    def test_config_endpoint_shows_none_mode(self, client_none_mode):
        """Test /auth/config returns 'none' mode info"""
        response = client_none_mode.get("/api/auth/config")
        
        assert response.status_code == 200
        data = response.json()["config"]
        
        assert data["mode"] == "none"
        assert data["allowMultiLogin"] is False or data["allowMultiLogin"] is True  # Can be either
        assert data["maintenanceMode"] is False


class TestAuthModeNoneMiddleware:
    """Test middleware behavior in 'none' mode"""
    
    def test_all_routes_accessible_without_auth(self, client_none_mode, arango_container_function):
        """Test that all routes work without authentication"""
        db = arango_container_function
        
        # Ensure collections exist
        if not db.collection_exists("conversations"):
            db.create_collection("conversations")
        
        # Try various protected endpoints
        endpoints = [
            ("/api/auth/status", "get"),
            ("/api/conversations", "get"),
        ]
        
        for path, method in endpoints:
            if method == "get":
                response = client_none_mode.get(path)
            elif method == "post":
                response = client_none_mode.post(path, json={})
            
            # Should not be 401 Unauthorized
            assert response.status_code != 401, f"{method.upper()} {path} returned 401"


class TestAuthModeNoneVsLocal:
    """Test that 'none' mode behaves differently from 'local' mode"""
    
    def test_generic_endpoint_not_available_in_local_mode(self, arango_container_function):
        """Test /auth/generic returns 403 in 'local' mode"""
        with patch('src.core.config.settings.AUTH_MODE', 'local'), \
             patch('src.middleware.auth_middleware.settings.AUTH_MODE', 'local'):
            
            from src.main import app
            client = TestClient(app)
            
            response = client.get("/api/auth/generic")
            
            # Should be forbidden in local mode
            assert response.status_code == 403
            assert "local" in response.json()["detail"].lower()