"""
Path: backend/tests/unit/services/test_auth_service.py
Version: 5.0

Changes in v5.0:
- FIX: test_login_disabled_account expects 403 (not 401)
- Per specification: disabled accounts return 403 Forbidden
- 401 is only for invalid credentials (wrong password/email)

Changes in v4.0:
- FIX: Use password_hash instead of password for RegisterRequest and LoginRequest
- Models expect SHA256 hash (64 hex chars), not plaintext password

Unit tests for AuthService
"""

import pytest
import hashlib
from unittest.mock import Mock
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.models.auth import RegisterRequest, LoginRequest
from tests.unit.mocks.mock_database import MockDatabase


def compute_sha256(password: str) -> str:
    """
    Compute SHA256 hash of password (simulates frontend behavior)
    
    Args:
        password: Plaintext password
        
    Returns:
        64-character hex string (SHA256 hash)
    """
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hashes for test passwords
STRONG_PASS_HASH = compute_sha256("StrongPass123")
CORRECT_PASS_HASH = compute_sha256("CorrectPass123")
WRONG_PASS_HASH = compute_sha256("WrongPass456")
ANOTHER_PASS_HASH = compute_sha256("AnotherPass456")
ANY_PASS_HASH = compute_sha256("AnyPass123")


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
    service = AuthService(db=mock_db)
    return service


class TestAuthService:
    """Unit tests for AuthService"""
    
    def test_register_success(self, auth_service):
        """Test successful user registration"""
        request = RegisterRequest(
            name="Test User",
            email="test@example.com",
            password_hash=STRONG_PASS_HASH
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
            password_hash=STRONG_PASS_HASH
        )
        auth_service.register(request1)
        
        # Try to register with same email
        request2 = RegisterRequest(
            name="User 2",
            email="duplicate@example.com",
            password_hash=ANOTHER_PASS_HASH
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
            password_hash=STRONG_PASS_HASH
        )
        auth_service.register(register_request)
        
        # Login with same password hash
        login_request = LoginRequest(
            email="login@example.com",
            password_hash=STRONG_PASS_HASH
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
            password_hash=CORRECT_PASS_HASH
        )
        auth_service.register(register_request)
        
        # Try login with wrong password
        login_request = LoginRequest(
            email="test@example.com",
            password_hash=WRONG_PASS_HASH
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value.detail).lower()
    
    def test_login_nonexistent_user(self, auth_service):
        """Test login with non-existent email"""
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password_hash=ANY_PASS_HASH
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value.detail).lower()
    
    def test_login_disabled_account(self, auth_service):
        """Test login with disabled account returns 403"""
        # Create disabled user directly in DB
        # Need to use bcrypt hash of the SHA256 password hash
        from src.core.security import hash_password
        
        auth_service.user_repo.db.create("users", {
            "name": "Disabled User",
            "email": "disabled@example.com",
            "password_hash": hash_password(STRONG_PASS_HASH),
            "role": "user",
            "status": "disabled"
        })
        
        # Try to login
        login_request = LoginRequest(
            email="disabled@example.com",
            password_hash=STRONG_PASS_HASH
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_request)
        
        # Per specification: disabled accounts return 403 Forbidden
        # 401 is only for invalid credentials (wrong password/email)
        assert exc_info.value.status_code == 403
        assert "disabled" in str(exc_info.value.detail).lower()


class TestAuthServiceSSO:
    """Test AuthService.verify_sso_session() method"""
    
    def test_verify_sso_session_existing_user(self, auth_service):
        """Test SSO verification with existing user"""
        # Register user first via regular registration
        register_req = RegisterRequest(
            name="John Doe",
            email="john@example.com",
            password_hash=STRONG_PASS_HASH
        )
        auth_service.register(register_req)
        
        # Now verify SSO session
        result = auth_service.verify_sso_session(
            sso_token="abc123",
            email="john@example.com",
            name="John Doe"
        )
        
        # Result is Dict with camelCase keys
        assert isinstance(result, dict)
        assert result["accessToken"] == "sso-authenticated"
        assert result["tokenType"] == "sso"
        assert result["expiresIn"] == 0
        
        # User data is nested dict
        assert result["user"]["email"] == "john@example.com"
        assert result["user"]["name"] == "John Doe"
    
    def test_verify_sso_session_new_user(self, auth_service):
        """Test SSO verification creates new user"""
        result = auth_service.verify_sso_session(
            sso_token="xyz789",
            email="jane@example.com",
            name="Jane Doe"
        )
        
        # Result is Dict with camelCase keys
        assert isinstance(result, dict)
        assert result["accessToken"] == "sso-authenticated"
        assert result["tokenType"] == "sso"
        assert result["expiresIn"] == 0
        
        # New user created
        assert result["user"]["email"] == "jane@example.com"
        assert result["user"]["name"] == "Jane Doe"
        assert result["user"]["role"] == "user"
        assert result["user"]["status"] == "active"