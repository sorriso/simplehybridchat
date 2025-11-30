"""
Path: tests/unit/api/test_deps.py
Version: 1

Unit tests for FastAPI dependencies
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.api.deps import get_db, get_file_storage, get_current_user, require_role


class TestGetDatabase:
    """Test get_db dependency"""
    
    @pytest.mark.unit
    @patch('src.api.deps.get_database')
    def test_get_db_returns_database(self, mock_get_database):
        """Test get_db returns database instance"""
        mock_db = Mock()
        mock_get_database.return_value = mock_db
        
        result = get_db()
        
        assert result == mock_db
        mock_get_database.assert_called_once()


class TestGetStorage:
    """Test get_file_storage dependency"""
    
    @pytest.mark.unit
    @patch('src.api.deps.get_storage')
    def test_get_storage_returns_storage(self, mock_get_storage):
        """Test get_file_storage returns storage instance"""
        mock_storage = Mock()
        mock_get_storage.return_value = mock_storage
        
        result = get_file_storage()
        
        assert result == mock_storage
        mock_get_storage.assert_called_once()


class TestGetCurrentUser:
    """Test get_current_user dependency"""
    
    @pytest.mark.unit
    @patch('src.api.deps.decode_access_token')
    def test_get_current_user_valid_token(self, mock_decode):
        """Test getting user with valid token"""
        # Mock token payload
        mock_decode.return_value = {"sub": "user123", "role": "user"}
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = "valid-token"
        
        # Mock database
        db = Mock()
        db.get_by_id.return_value = {
            "_key": "user123",
            "name": "Test User",
            "status": "active"
        }
        
        result = get_current_user(credentials, db)
        
        assert result["_key"] == "user123"
        assert result["status"] == "active"
        mock_decode.assert_called_once_with("valid-token")
        db.get_by_id.assert_called_once_with("users", "user123")
    
    @pytest.mark.unit
    @patch('src.api.deps.decode_access_token')
    def test_get_current_user_invalid_payload(self, mock_decode):
        """Test with invalid token payload (no sub)"""
        mock_decode.return_value = {"role": "user"}  # Missing "sub"
        
        credentials = Mock()
        credentials.credentials = "token"
        
        db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('src.api.deps.decode_access_token')
    def test_get_current_user_not_found(self, mock_decode):
        """Test when user not found in database"""
        mock_decode.return_value = {"sub": "user123"}
        
        credentials = Mock()
        credentials.credentials = "token"
        
        db = Mock()
        db.get_by_id.return_value = None  # User not found
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('src.api.deps.decode_access_token')
    def test_get_current_user_inactive(self, mock_decode):
        """Test with inactive user"""
        mock_decode.return_value = {"sub": "user123"}
        
        credentials = Mock()
        credentials.credentials = "token"
        
        db = Mock()
        db.get_by_id.return_value = {
            "_key": "user123",
            "status": "disabled"  # Not active
        }
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "disabled" in exc_info.value.detail


class TestRequireRole:
    """Test require_role dependency factory"""
    
    @pytest.mark.unit
    def test_require_role_sufficient_permission(self):
        """Test with sufficient permission"""
        user = {"role": "manager"}
        
        role_checker = require_role("user")
        result = role_checker(user)
        
        assert result == user  # Should return user
    
    @pytest.mark.unit
    def test_require_role_exact_match(self):
        """Test with exact role match"""
        user = {"role": "manager"}
        
        role_checker = require_role("manager")
        result = role_checker(user)
        
        assert result == user
    
    @pytest.mark.unit
    def test_require_role_insufficient_permission(self):
        """Test with insufficient permission"""
        user = {"role": "user"}
        
        role_checker = require_role("manager")
        
        with pytest.raises(HTTPException) as exc_info:
            role_checker(user)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
    
    @pytest.mark.unit
    def test_require_role_root_can_access_all(self):
        """Test that root can access manager and user routes"""
        user = {"role": "root"}
        
        # Root can access user routes
        user_checker = require_role("user")
        assert user_checker(user) == user
        
        # Root can access manager routes
        manager_checker = require_role("manager")
        assert manager_checker(user) == user
        
        # Root can access root routes
        root_checker = require_role("root")
        assert root_checker(user) == user