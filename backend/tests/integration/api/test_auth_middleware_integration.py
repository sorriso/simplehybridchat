"""
Path: tests/integration/api/test_auth_middleware_integration.py
Version: 3

Integration tests for authentication middleware with FastAPI
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.middleware.auth_middleware import AuthenticationMiddleware
from src.core.security import create_access_token
from src.core.config import settings


@pytest.fixture
def app():
    """Create FastAPI app with auth middleware"""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    
    # Public endpoint
    @app.get("/")
    def root():
        return {"message": "Public endpoint"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    # Protected endpoint
    @app.get("/api/protected")
    def protected(request: Request):
        # Access user from request.scope (injected by middleware)
        user = request.scope.get("user")
        return {"user": user}
    
    @app.get("/api/users/me")
    def get_me(request: Request):
        user = request.scope.get("user")
        return {"user": user}
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.mark.integration
class TestAuthMiddlewareIntegration:
    """Test authentication middleware with real FastAPI app"""
    
    def test_public_endpoint_no_auth(self, client):
        """Test public endpoint doesn't require auth"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Public endpoint"
    
    def test_health_endpoint_no_auth(self, client):
        """Test health endpoint doesn't require auth"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_protected_endpoint_with_valid_token(self, client):
        """Test protected endpoint with valid JWT token"""
        # Create valid token
        token = create_access_token({"sub": "user123", "role": "user"})
        
        # Call protected endpoint
        response = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == "user123"
        assert data["user"]["role"] == "user"
    
    def test_protected_endpoint_without_token(self, client):
        """Test protected endpoint without token"""
        response = client.get("/api/protected")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Missing Authorization header" in data["error"]
    
    def test_protected_endpoint_invalid_token_format(self, client):
        """Test with invalid token format (no Bearer prefix)"""
        response = client.get(
            "/api/protected",
            headers={"Authorization": "InvalidToken123"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Invalid Authorization header format" in data["error"]
    
    def test_protected_endpoint_expired_token(self, client):
        """Test with expired token"""
        from datetime import timedelta
        
        # Create expired token (negative expiration)
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-10)  # Expired 10 seconds ago
        )
        
        response = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Invalid or expired token" in data["error"]
    
    def test_protected_endpoint_invalid_token(self, client):
        """Test with invalid/malformed token"""
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer invalid-token-string"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_auth_mode_none_injects_generic_user(self, client, monkeypatch):
        """Test AUTH_MODE=none injects generic user"""
        # Temporarily set AUTH_MODE to none
        monkeypatch.setattr(settings, "AUTH_MODE", "none")
        
        response = client.get("/api/protected")
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == "john-doe"
    
    def test_multiple_protected_endpoints(self, client):
        """Test multiple protected endpoints share same token"""
        token = create_access_token({"sub": "user456", "role": "manager"})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Call first endpoint
        response1 = client.get("/api/protected", headers=headers)
        assert response1.status_code == 200
        assert response1.json()["user"]["id"] == "user456"
        
        # Call second endpoint with same token
        response2 = client.get("/api/users/me", headers=headers)
        assert response2.status_code == 200
        assert response2.json()["user"]["id"] == "user456"
    
    def test_user_state_injection(self, client):
        """Test user is properly injected into request.state"""
        token = create_access_token({
            "sub": "user789",
            "role": "root",
            "email": "admin@example.com"
        })
        
        response = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # User should be in response
        user = data["user"]
        assert user["id"] == "user789"
        assert user["role"] == "root"


@pytest.mark.integration
class TestAuthMiddlewarePublicRoutes:
    """Test public routes don't require authentication"""
    
    def test_docs_endpoint_public(self, client):
        """Test /docs is public"""
        response = client.get("/docs")
        
        # Should not return 401
        assert response.status_code != 401
    
    def test_openapi_endpoint_public(self, client):
        """Test /openapi.json is public"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        # Should return OpenAPI schema
        data = response.json()
        assert "openapi" in data