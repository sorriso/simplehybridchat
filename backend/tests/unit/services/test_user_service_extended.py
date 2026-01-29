"""
Path: backend/tests/unit/services/test_user_service_extended.py
Version: 1.4

Changes in v1.4:
- FIXED: UserService.update_user() calls user_repo.update_with_validation() not update()
- FIXED: UserService.create_user() calls user_repo.create_with_validation() not create()
- Must mock the correct method names

Extended tests for UserService to cover missing branches.
Coverage target: 81% → 95%
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.services.user_service import UserService
from src.models.user import UserCreate, UserUpdate


def make_user_dict(user_id, name, email, role="user", status="active", group_ids=None):
    """Helper to create complete user dict with all required fields"""
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "status": status,
        "group_ids": group_ids or [],
        "created_at": datetime(2024, 1, 1, 0, 0, 0),
        "updated_at": None
    }


class TestUserServiceGetUser:
    """Test get_user() permission branches"""
    
    @pytest.mark.unit
    def test_get_user_self_access(self):
        """Test user can view their own profile"""
        # Setup
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = make_user_dict(
            "user-1", "John", "john@example.com"
        )
        
        current_user = {"id": "user-1", "role": "user", "group_ids": []}
        
        # Act
        result = service.get_user("user-1", current_user)
        
        # Assert
        assert result.id == "user-1"
    
    @pytest.mark.unit
    def test_get_user_root_can_view_any(self):
        """Test root can view any user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = make_user_dict(
            "user-2", "Jane", "jane@example.com", group_ids=["group-1"]
        )
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        result = service.get_user("user-2", current_user)
        
        assert result.id == "user-2"
    
    @pytest.mark.unit
    def test_get_user_not_found(self):
        """Test get_user with non-existent user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = None
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_user("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404


class TestUserServiceListUsers:
    """Test list_users() permission and filtering branches"""
    
    @pytest.mark.unit
    def test_list_users_root_sees_all(self):
        """Test root sees all users"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_all.return_value = [
            make_user_dict("u1", "User 1", "u1@test.com"),
            make_user_dict("u2", "User 2", "u2@test.com")
        ]
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        result = service.list_users(current_user)
        
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_list_users_user_forbidden(self):
        """Test regular user cannot list users"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "user-1", "role": "user", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.list_users(current_user)
        
        assert exc_info.value.status_code == 403


class TestUserServiceUpdateUser:
    """Test update_user() permission and validation branches"""
    
    @pytest.mark.unit
    def test_update_user_self_basic_fields(self):
        """Test user can update their own basic fields"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        # Create fresh mock with proper return values
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = make_user_dict(
            "user-1", "John", "john@example.com"
        )
        # CRITICAL: update_user calls update_with_validation, not update
        mock_repo.update_with_validation.return_value = make_user_dict(
            "user-1", "John Updated", "john@example.com"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "user-1", "role": "user", "group_ids": []}
        update_data = UserUpdate(name="John Updated")
        
        result = service.update_user("user-1", update_data, current_user)
        
        assert result.name == "John Updated"
        mock_repo.update_with_validation.assert_called_once()
    
    @pytest.mark.unit
    def test_update_user_not_found(self):
        """Test update_user with non-existent user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = None
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        update_data = UserUpdate(name="New Name")
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_user("nonexistent", update_data, current_user)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.unit
    def test_update_user_root_can_update_any(self):
        """Test root can update any user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = make_user_dict(
            "user-2", "Jane", "jane@example.com"
        )
        # CRITICAL: update_user calls update_with_validation, not update
        mock_repo.update_with_validation.return_value = make_user_dict(
            "user-2", "Jane Updated", "jane@example.com"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        update_data = UserUpdate(name="Jane Updated")
        
        result = service.update_user("user-2", update_data, current_user)
        
        assert result.name == "Jane Updated"
    
    @pytest.mark.unit
    def test_update_user_privileged_fields_forbidden_for_user(self):
        """Test regular user cannot update role/status fields"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = make_user_dict(
            "user-1", "John", "john@example.com"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "user-1", "role": "user", "group_ids": []}
        # Try to update role - should be forbidden for regular user
        update_data = UserUpdate(role="manager")
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_user("user-1", update_data, current_user)
        
        assert exc_info.value.status_code == 403
        assert "only managers" in exc_info.value.detail


class TestUserServiceToggleStatus:
    """Test toggle_user_status() edge cases"""
    
    @pytest.mark.unit
    def test_toggle_status_activate_user(self):
        """Test activating a disabled user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = make_user_dict(
            "user-1", "John", "john@example.com", status="disabled"
        )
        # toggle_user_status calls user_repo.update, not update_with_validation
        mock_repo.update.return_value = make_user_dict(
            "user-1", "John", "john@example.com", status="active"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        result = service.toggle_user_status("user-1", "active", current_user)
        
        assert result.status == "active"
    
    @pytest.mark.unit
    def test_toggle_status_cannot_disable_self(self):
        """Test user cannot disable themselves"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "user-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.toggle_user_status("user-1", "disabled", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_toggle_status_user_not_found(self):
        """Test toggle_user_status with non-existent user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = None
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.toggle_user_status("nonexistent", "active", current_user)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.unit
    def test_toggle_status_user_forbidden(self):
        """Test regular user cannot toggle status"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "user-1", "role": "user", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.toggle_user_status("user-2", "disabled", current_user)
        
        assert exc_info.value.status_code == 403


class TestUserServiceAssignRole:
    """Test assign_user_role() edge cases"""
    
    @pytest.mark.unit
    def test_assign_role_root_only(self):
        """Test only root can assign roles"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "manager-1", "role": "manager", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.assign_user_role("user-1", "manager", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_assign_role_cannot_demote_self(self):
        """Test root cannot demote themselves"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = make_user_dict(
            "root-1", "Root", "root@example.com", role="root"
        )
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.assign_user_role("root-1", "user", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_assign_role_success(self):
        """Test successful role assignment"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = make_user_dict(
            "user-1", "John", "john@example.com"
        )
        # assign_user_role calls user_repo.update, not update_with_validation
        mock_repo.update.return_value = make_user_dict(
            "user-1", "John", "john@example.com", role="manager"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        result = service.assign_user_role("user-1", "manager", current_user)
        
        assert result.role == "manager"
    
    @pytest.mark.unit
    def test_assign_role_user_not_found(self):
        """Test assign_user_role with non-existent user"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.get_by_id.return_value = None
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.assign_user_role("nonexistent", "manager", current_user)
        
        assert exc_info.value.status_code == 404


class TestUserServiceDeleteUser:
    """Test delete_user() edge cases"""
    
    @pytest.mark.unit
    def test_delete_user_root_only(self):
        """Test only root can delete users"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "manager-1", "role": "manager", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_user("user-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_delete_user_cannot_delete_self(self):
        """Test root cannot delete themselves (returns 403)"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_user("root-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_delete_user_success(self):
        """Test successful user deletion"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        service.user_repo = MagicMock()
        service.user_repo.delete.return_value = True
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        
        result = service.delete_user("user-1", current_user)
        
        assert result is True


class TestUserServiceCreateUser:
    """Test create_user() edge cases"""
    
    @pytest.mark.unit
    def test_create_user_root_only(self):
        """Test only root can create users"""
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        current_user = {"id": "manager-1", "role": "manager", "group_ids": []}
        user_data = UserCreate(
            name="New User",
            email="new@example.com",
            password="Password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_user(user_data, current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    @patch('src.core.security.hash_password')
    def test_create_user_success(self, mock_hash):
        """Test successful user creation"""
        mock_hash.return_value = "hashed_password_123"
        
        mock_db = MagicMock()
        service = UserService(db=mock_db)
        
        mock_repo = MagicMock()
        # CRITICAL: create_user calls create_with_validation, not create
        mock_repo.create_with_validation.return_value = make_user_dict(
            "new-user", "New User", "new@example.com"
        )
        service.user_repo = mock_repo
        
        current_user = {"id": "root-1", "role": "root", "group_ids": []}
        user_data = UserCreate(
            name="New User",
            email="new@example.com",
            password="Password123"
        )
        
        result = service.create_user(user_data, current_user)
        
        assert result.name == "New User"
        assert result.email == "new@example.com"
        mock_repo.create_with_validation.assert_called_once()
        mock_hash.assert_called_once_with("Password123")