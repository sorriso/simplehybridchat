"""
Path: backend/tests/integration/api/test_deps_integration.py
Version: 2

Changes in v2:
- Modified all user accesses: user["_key"] â†’ user["id"]
- Modified all assertions: "_key" â†’ "id"
- Tests now verify dependency injection with correct format

Integration tests for API dependencies with real database
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from src.api.deps import get_current_user
from src.core.security import create_access_token


@pytest.mark.integration
@pytest.mark.integration_slow
class TestGetCurrentUserIntegration:
    """Test get_current_user with real database"""
    
    def test_get_current_user_from_database(self, arango_container_function):
        """Test retrieving user from real database"""
        db = arango_container_function
        
        # Create users collection
        db.create_collection("users")
        
        # Create test user
        user = db.create("users", {
            "name": "Test User",
            "email": "test@example.com",
            "status": "active",
            "role": "user"
        })
        user_id = user["id"]
        
        # Create JWT token for this user
        token = create_access_token({"sub": user_id, "role": "user"})
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = token
        
        # Get current user (should fetch from DB)
        result = get_current_user(credentials, db)
        
        assert result is not None
        assert result["id"] == user_id
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["status"] == "active"
    
    def test_get_current_user_inactive_user(self, arango_container_function):
        """Test with inactive user"""
        db = arango_container_function
        
        # Create users collection
        db.create_collection("users")
        
        # Create inactive user
        user = db.create("users", {
            "name": "Inactive User",
            "email": "inactive@example.com",
            "status": "disabled",  # Not active
            "role": "user"
        })
        user_id = user["id"]
        
        # Create JWT token
        token = create_access_token({"sub": user_id})
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = token
        
        # Should raise exception for inactive user
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "disabled" in exc_info.value.detail
    
    def test_get_current_user_deleted_user(self, arango_container_function):
        """Test with user that was deleted"""
        db = arango_container_function
        
        # Create users collection
        db.create_collection("users")
        
        # Create user then delete
        user = db.create("users", {
            "name": "Deleted User",
            "email": "deleted@example.com",
            "status": "active"
        })
        user_id = user["id"]
        
        # Create token
        token = create_access_token({"sub": user_id})
        
        # Delete user from database
        db.delete("users", user_id)
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = token
        
        # Should raise exception (user not found)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "not found" in exc_info.value.detail.lower()