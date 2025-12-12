"""
Path: backend/tests/unit/services/test_auth_service_sso.py
Version: 1.3

Changes in v1.3:
- FIX: Tests now use camelCase keys (accessToken, tokenType, expiresIn)
- Matches SSO service response with camelCase Dict keys

Changes in v1.2:
- FIX: verify_sso_session now returns Dict, not TokenResponse
- Tests now access result["user"] instead of result.user
- Tests now access result["accessToken"] instead of result.access_token
- Dict structure: {accessToken, tokenType, expiresIn, user}

Changes in v1.1:
- FIX: Corrected fixture to patch AUTH_MODE at attribute level
- FIX: Patch in both config and middleware modules
- Ensures AUTH_MODE changes are visible to all imported modules

Unit tests for AuthService SSO verification
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.database.exceptions import DuplicateKeyError


@pytest.fixture
def mock_database():
    """Mock database instance"""
    return Mock()


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return Mock()


@pytest.fixture
def auth_service(mock_database, mock_user_repo):
    """Auth service with mocked dependencies"""
    service = AuthService(db=mock_database)
    service.user_repo = mock_user_repo
    return service


class TestAuthServiceSSO:
    """Test AuthService.verify_sso_session() method"""
    
    def test_verify_sso_session_existing_user(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification with existing user"""
        # Mock existing user
        mock_user_repo.get_by_email.return_value = {
            "id": "user-123",
            "name": "John Doe",
            "email": "john@example.com",
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        result = auth_service.verify_sso_session(
            sso_token="abc123",
            email="john@example.com",
            name="John Doe"
        )
        
        # Result is Dict, not TokenResponse
        assert isinstance(result, dict)
        assert result["accessToken"] == "sso-authenticated"
        assert result["tokenType"] == "sso"
        assert result["expiresIn"] == 0
        
        # User data is nested dict
        assert result["user"]["id"] == "user-123"
        assert result["user"]["email"] == "john@example.com"
        
        # Should not create user
        mock_user_repo.create.assert_not_called()
    
    def test_verify_sso_session_new_user(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification with new user (auto-create)"""
        # Mock: user doesn't exist initially
        mock_user_repo.get_by_email.return_value = None
        
        # Mock: user creation
        mock_user_repo.create.return_value = {
            "id": "user-new",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        result = auth_service.verify_sso_session(
            sso_token="xyz789",
            email="jane@example.com",
            name="Jane Doe"
        )
        
        # Result is Dict
        assert isinstance(result, dict)
        assert result["accessToken"] == "sso-authenticated"
        assert result["tokenType"] == "sso"
        assert result["expiresIn"] == 0
        
        # User was created
        assert result["user"]["id"] == "user-new"
        assert result["user"]["email"] == "jane@example.com"
        assert result["user"]["name"] == "Jane Doe"
        
        # Should have called create
        mock_user_repo.create.assert_called_once()
        create_args = mock_user_repo.create.call_args[0][0]
        assert create_args["email"] == "jane@example.com"
        assert create_args["name"] == "Jane Doe"
        assert create_args["role"] == "user"
        assert create_args["status"] == "active"
    
    def test_verify_sso_session_new_user_no_name(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification without name (derive from email)"""
        # Mock: user doesn't exist
        mock_user_repo.get_by_email.return_value = None
        
        # Mock: user creation
        mock_user_repo.create.return_value = {
            "id": "user-noname",
            "name": "bob",  # Derived from email
            "email": "bob@example.com",
            "role": "user",
            "status": "active",
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        result = auth_service.verify_sso_session(
            sso_token="noname123",
            email="bob@example.com",
            name=None  # No name provided
        )
        
        # Result is Dict
        assert isinstance(result, dict)
        assert result["user"]["email"] == "bob@example.com"
        assert result["user"]["name"] == "bob"
        
        # Should have called create with derived name
        mock_user_repo.create.assert_called_once()
        create_args = mock_user_repo.create.call_args[0][0]
        assert create_args["name"] == "bob"  # Derived from email
    
    def test_verify_sso_session_disabled_user(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification with disabled user"""
        # Mock: disabled user
        mock_user_repo.get_by_email.return_value = {
            "id": "user-disabled",
            "name": "Disabled User",
            "email": "disabled@example.com",
            "role": "user",
            "status": "disabled",
            "group_ids": [],
            "created_at": datetime(2024, 1, 1),
            "updated_at": None
        }
        
        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_sso_session(
                sso_token="disabled123",
                email="disabled@example.com",
                name="Disabled User"
            )
        
        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail.lower()
    
    def test_verify_sso_session_handles_race_condition(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification handles race condition (duplicate user)"""
        # Mock: first check returns None
        # Mock: create raises DuplicateKeyError
        # Mock: second get_by_email returns the user
        mock_user_repo.get_by_email.side_effect = [
            None,  # First call: user doesn't exist
            {      # Second call (after DuplicateKeyError): user exists now
                "id": "user-race",
                "name": "Race User",
                "email": "race@example.com",
                "role": "user",
                "status": "active",
                "group_ids": [],
                "created_at": datetime(2024, 1, 1),
                "updated_at": None
            }
        ]
        
        mock_user_repo.create.side_effect = DuplicateKeyError("users", "email", "race@example.com")
        
        result = auth_service.verify_sso_session(
            sso_token="race123",
            email="race@example.com",
            name="Race User"
        )
        
        # Result is Dict
        assert isinstance(result, dict)
        assert result["user"]["email"] == "race@example.com"
        
        # Should have tried to create, then retrieved
        assert mock_user_repo.create.call_count == 1
        assert mock_user_repo.get_by_email.call_count == 2
    
    def test_verify_sso_session_race_condition_still_fails(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test SSO verification handles race condition but user still not found"""
        # Mock: first check returns None
        # Mock: create raises DuplicateKeyError
        # Mock: second get_by_email STILL returns None (edge case)
        mock_user_repo.get_by_email.side_effect = [None, None]
        mock_user_repo.create.side_effect = DuplicateKeyError("users", "email", "race2@example.com")
        
        # Should raise 500
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_sso_session(
                sso_token="race456",
                email="race2@example.com",
                name="Race User 2"
            )
        
        assert exc_info.value.status_code == 500
        assert "race condition" in exc_info.value.detail.lower()