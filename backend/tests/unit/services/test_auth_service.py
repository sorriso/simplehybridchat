"""
Path: tests/unit/services/test_auth_service.py
Version: 2

Unit tests for AuthService

Changes in v2:
- FIX: test_register_duplicate_email expects 409 (Conflict) not 400
- FIX: test_login_disabled_account expects 401 (security: generic error message)
- REMOVED: test_get_auth_config (method doesn't exist in AuthService)

Changes in v1.3:
- FIX: Syntax error line 156 - removed quotes around 'password' parameter
- Fixed: "password": "value" → password="value"

Changes in v1.2:
- FIX: Utilise hash bcrypt valide au lieu de "fake_hash"
- FIX: test_register_duplicate_email - RegisterRequest validation
- FIX: test_login_disabled_account - Hash correct pour passer password check
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.models.auth import RegisterRequest, LoginRequest
from tests.unit.mocks.mock_database import MockDatabase


# Hash bcrypt prÃ©-calculÃ© pour "StrongPass123"
VALID_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeblhQ7N3OxvKl1yG"


@pytest.fixture
def mock_db():
    """Provide clean mock database"""
    db = MockDatabase()
    db.connect()
    db.create_collection("users")
    yield db
    db.disconnect()


@pytest.fixture
def auth_service(mock_db):
    """Provide AuthService with mocked database"""
    service = AuthService()
    service.user_repo.db = mock_db
    return service


class TestAuthService:
    """Unit tests for AuthService"""
    
    def test_register_success(self, auth_service):
        """Test successful user registration"""
        request = RegisterRequest(
            name="Test User",
            email="test@example.com",
            password="StrongPass123"
        )
        
        user = auth_service.register(request)
        
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.status == "active"
    
    def test_register_duplicate_email(self, auth_service):
        """Test registration with duplicate email"""
        # Register first user
        request1 = RegisterRequest(
            name="User 1",
            email="duplicate@example.com",
            password="StrongPass123"
        )
        auth_service.register(request1)
        
        # Try to register with same email
        request2 = RegisterRequest(
            name="User 2",
            email="duplicate@example.com",
            password="AnotherPass456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register(request2)
        
        assert exc_info.value.status_code == 409  # Conflict
        assert "already registered" in str(exc_info.value.detail).lower()
    
    def test_login_success(self, auth_service):
        """Test successful login"""
        # Register user first
        register_request = RegisterRequest(
            name="Login Test",
            email="login@example.com",
            password="StrongPass123"
        )
        auth_service.register(register_request)
        
        # Login
        login_request = LoginRequest(
            email="login@example.com",
            password="StrongPass123"
        )
        
        token_response = auth_service.login(login_request)
        
        assert token_response.access_token is not None
        assert token_response.token_type == "bearer"
        assert token_response.expires_in > 0
    
    def test_login_wrong_password(self, auth_service):
        """Test login with wrong password"""
        # Register user
        register_request = RegisterRequest(
            name="Test User",
            email="test@example.com",
            password="CorrectPass123"
        )
        auth_service.register(register_request)
        
        # Try login with wrong password
        login_request = LoginRequest(
            email="test@example.com",
            password="WrongPass456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value.detail).lower()
    
    def test_login_nonexistent_user(self, auth_service):
        """Test login with non-existent email"""
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="AnyPass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value.detail).lower()
    
    def test_login_disabled_account(self, auth_service):
        """Test login with disabled account"""
        # Create disabled user with VALID hash
        auth_service.user_repo.db.create("users", {
            "name": "Disabled User",
            "email": "disabled@example.com",
            "password_hash": VALID_PASSWORD_HASH,  # Hash pour "StrongPass123"
            "role": "user",
            "status": "disabled"
        })
        
        # Try to login
        login_request = LoginRequest(
            email="disabled@example.com",
            password="StrongPass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        # Returns 401 with generic message (security: don't reveal account status)
        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value.detail).lower()