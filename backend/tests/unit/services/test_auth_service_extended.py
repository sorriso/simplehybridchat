"""
Path: backend/tests/unit/services/test_auth_service_extended.py
Version: 1.0

Extended unit tests for AuthService covering edge cases and exception branches.

Tests cover:
- Register exceptions (generic error)
- Login exceptions (generic error)
- SSO disabled user
- SSO duplicate key handling (race condition)
- Change password exceptions
- Token validation edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.models.auth import RegisterRequest, LoginRequest
from src.database.exceptions import DuplicateKeyError


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return Mock()


@pytest.fixture
def mock_db():
    """Mock database"""
    return Mock()


@pytest.fixture
def auth_service(mock_db, mock_user_repo):
    """Auth service with mocked dependencies"""
    service = AuthService(db=mock_db)
    service.user_repo = mock_user_repo
    return service


class TestAuthServiceRegisterExceptions:
    """Test register exception handling"""
    
    @pytest.mark.unit
    def test_register_generic_exception(self, auth_service, mock_user_repo):
        """Test register handles generic exceptions"""
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.side_effect = Exception("Database error")
        
        request = RegisterRequest(
            name="Test User",
            email="test@example.com",
            password_hash="a" * 64  # Valid SHA256 hash length
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register(request)
        
        assert exc_info.value.status_code == 500
        assert "registration failed" in str(exc_info.value.detail).lower()


class TestAuthServiceLoginExceptions:
    """Test login exception handling"""
    
    @pytest.mark.unit
    def test_login_generic_exception(self, auth_service, mock_user_repo):
        """Test login handles generic exceptions"""
        mock_user_repo.get_by_email.side_effect = Exception("Database error")
        
        request = LoginRequest(
            email="test@example.com",
            password_hash="a" * 64
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(request)
        
        assert exc_info.value.status_code == 500
        assert "login failed" in str(exc_info.value.detail).lower()


class TestAuthServiceSSOExceptions:
    """Test SSO verification exception handling"""
    
    @pytest.mark.unit
    def test_verify_sso_session_disabled_user(self, auth_service, mock_user_repo):
        """Test SSO verification with disabled user"""
        mock_user_repo.get_by_email.return_value = {
            "id": "user-disabled",
            "name": "Disabled User",
            "email": "disabled@example.com",
            "role": "user",
            "status": "disabled",  # Disabled!
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_sso_session(
                sso_token="abc123",
                email="disabled@example.com",
                name="Disabled User"
            )
        
        assert exc_info.value.status_code == 403
        assert "disabled" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_verify_sso_session_duplicate_key_race_condition(self, auth_service, mock_user_repo):
        """Test SSO handles race condition (DuplicateKeyError)"""
        # First call: user doesn't exist
        # This simulates race condition where user is created between check and create
        mock_user_repo.get_by_email.side_effect = [
            None,  # First check - user doesn't exist
            {      # Second check after DuplicateKeyError - user now exists
                "id": "user-race",
                "name": "Race Condition User",
                "email": "race@example.com",
                "role": "user",
                "status": "active",
                "group_ids": [],
                "created_at": datetime(2024, 1, 1),
                "updated_at": None
            }
        ]
        mock_user_repo.create.side_effect = DuplicateKeyError("Duplicate key")
        
        result = auth_service.verify_sso_session(
            sso_token="abc123",
            email="race@example.com",
            name="Race Condition User"
        )
        
        # Should recover and return user data
        assert isinstance(result, dict)
        assert result["user"]["email"] == "race@example.com"
    
    @pytest.mark.unit
    def test_verify_sso_session_duplicate_key_user_not_found(self, auth_service, mock_user_repo):
        """Test SSO handles DuplicateKeyError but user not found (edge case)"""
        mock_user_repo.get_by_email.side_effect = [
            None,  # First check
            None   # Second check after DuplicateKeyError - still not found (weird state)
        ]
        mock_user_repo.create.side_effect = DuplicateKeyError("Duplicate key")
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_sso_session(
                sso_token="abc123",
                email="weird@example.com"
            )
        
        assert exc_info.value.status_code == 500
        assert "race condition" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_verify_sso_session_generic_exception(self, auth_service, mock_user_repo):
        """Test SSO handles generic exceptions"""
        mock_user_repo.get_by_email.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_sso_session(
                sso_token="abc123",
                email="error@example.com"
            )
        
        assert exc_info.value.status_code == 500
        assert "sso verification failed" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_verify_sso_session_no_name_derives_from_email(self, auth_service, mock_user_repo):
        """Test SSO derives name from email when not provided"""
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = {
            "id": "user-new",
            "name": "johndoe",  # Derived from email
            "email": "johndoe@example.com",
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        result = auth_service.verify_sso_session(
            sso_token="abc123",
            email="johndoe@example.com",
            name=None  # No name provided
        )
        
        # Should derive name from email
        create_args = mock_user_repo.create.call_args[0][0]
        assert create_args["name"] == "johndoe"


class TestAuthServiceChangePasswordExceptions:
    """Test change_password exception handling"""
    
    @pytest.mark.unit
    def test_change_password_user_not_found(self, auth_service, mock_user_repo):
        """Test change_password with non-existent user"""
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_password(
                user_id="nonexistent",
                current_password="OldPass123",
                new_password="NewPass456"
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_change_password_wrong_current_password(self, auth_service, mock_user_repo):
        """Test change_password with wrong current password"""
        # Create a valid bcrypt hash for SHA256("CorrectPass123")
        import hashlib
        from src.core.security import hash_password
        
        correct_sha256 = hashlib.sha256("CorrectPass123".encode()).hexdigest()
        stored_hash = hash_password(correct_sha256)
        
        mock_user_repo.get_by_id.return_value = {
            "id": "user-123",
            "password_hash": stored_hash
        }
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_password(
                user_id="user-123",
                current_password="WrongPass456",  # Wrong password
                new_password="NewPass789"
            )
        
        assert exc_info.value.status_code == 401
        assert "incorrect" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_change_password_generic_exception(self, auth_service, mock_user_repo):
        """Test change_password handles generic exceptions"""
        mock_user_repo.get_by_id.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_password(
                user_id="user-123",
                current_password="OldPass123",
                new_password="NewPass456"
            )
        
        assert exc_info.value.status_code == 500
        assert "password change failed" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_change_password_success(self, auth_service, mock_user_repo):
        """Test successful password change"""
        import hashlib
        from src.core.security import hash_password
        
        # Create valid hash for current password
        current_sha256 = hashlib.sha256("OldPass123".encode()).hexdigest()
        stored_hash = hash_password(current_sha256)
        
        mock_user_repo.get_by_id.return_value = {
            "id": "user-123",
            "password_hash": stored_hash
        }
        mock_user_repo.update.return_value = {"id": "user-123", "updated_at": datetime.utcnow()}
        
        result = auth_service.change_password(
            user_id="user-123",
            current_password="OldPass123",
            new_password="NewPass456"
        )
        
        assert result is True
        mock_user_repo.update.assert_called_once()


class TestAuthServiceTokenValidation:
    """Test token validation edge cases"""
    
    @pytest.mark.unit
    def test_validate_token_user_not_found(self, auth_service, mock_user_repo):
        """Test token validation when user doesn't exist"""
        with patch('src.services.auth_service.decode_access_token') as mock_decode:
            mock_decode.return_value = {"sub": "nonexistent-user"}
            mock_user_repo.get_by_id.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                auth_service.validate_token("valid-token")
            
            assert exc_info.value.status_code == 401
            assert "not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_validate_token_disabled_user(self, auth_service, mock_user_repo):
        """Test token validation when user is disabled"""
        with patch('src.services.auth_service.decode_access_token') as mock_decode:
            mock_decode.return_value = {"sub": "user-disabled"}
            mock_user_repo.get_by_id.return_value = {
                "id": "user-disabled",
                "email": "disabled@example.com",
                "role": "user",
                "status": "disabled"
            }
            
            with pytest.raises(HTTPException) as exc_info:
                auth_service.validate_token("valid-token")
            
            assert exc_info.value.status_code == 403
            assert "disabled" in str(exc_info.value.detail).lower()
    
    @pytest.mark.unit
    def test_validate_token_invalid_token(self, auth_service):
        """Test token validation with invalid token"""
        with patch('src.services.auth_service.decode_access_token') as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                auth_service.validate_token("invalid-token")
            
            assert exc_info.value.status_code == 401
            assert "invalid" in str(exc_info.value.detail).lower()