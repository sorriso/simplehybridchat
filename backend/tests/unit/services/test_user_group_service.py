"""
Path: backend/tests/unit/services/test_user_group_service.py
Version: 7

Changes in v7:
- FIX: Line 190 error message assertion matches actual service message
- Changed: "Cannot manage this group" -> "Not a manager of this group"
- Reason: Match actual UserGroupService._check_can_manage_group() error

Changes in v6:
- FIX: Added MagicMock to imports
- Import: from unittest.mock import Mock, MagicMock
- FIX: Added mock_db fixture
- FIX: UserGroupService() now instantiated with db parameter: UserGroupService(db=mock_db)

Changes in v4:
- FIX: UserGroupService() now instantiated with db parameter

Changes in v3:
- FIX: Replaced mock_user_repo.get() with mock_user_repo.get_by_id()

Changes in v2:
- FIX: Replaced all mock_group_repo.get with mock_group_repo.get_by_id

Unit tests for UserGroupService
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi import HTTPException

from src.services.user_group_service import UserGroupService
from src.database.exceptions import NotFoundError, DuplicateKeyError


class TestUserGroupService:
    """Test UserGroupService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return MagicMock()
    
    @pytest.fixture
    def mock_group_repo(self):
        """Mock UserGroupRepository"""
        return Mock()
    
    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepository"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db, mock_group_repo, mock_user_repo):
        """UserGroupService with mocked repositories"""
        service = UserGroupService(db=mock_db)
        service.group_repo = mock_group_repo
        service.user_repo = mock_user_repo
        return service
    
    @pytest.fixture
    def root_user(self):
        """Root user for testing"""
        return {
            "id": "root-1",
            "name": "Root User",
            "email": "root@example.com",
            "role": "root"
        }
    
    @pytest.fixture
    def manager_user(self):
        """Manager user for testing"""
        return {
            "id": "manager-1",
            "name": "Manager User",
            "email": "manager@example.com",
            "role": "manager"
        }
    
    @pytest.fixture
    def regular_user(self):
        """Regular user for testing"""
        return {
            "id": "user-1",
            "name": "Regular User",
            "email": "user@example.com",
            "role": "user"
        }
    
    @pytest.fixture
    def sample_group(self):
        """Sample group data"""
        return {
            "id": "group-1",
            "name": "Engineering Team",
            "status": "active",
            "manager_ids": ["manager-1"],
            "member_ids": ["user-1", "user-2"]
        }
    
    # List Groups Tests
    
    @pytest.mark.unit
    def test_list_groups_as_root(self, service, mock_group_repo, root_user):
        """Test root user sees all groups"""
        mock_group_repo.get_all.return_value = [
            {"id": "group-1", "name": "Team 1"},
            {"id": "group-2", "name": "Team 2"}
        ]
        
        groups = service.list_groups(root_user)
        
        assert len(groups) == 2
        mock_group_repo.get_all.assert_called_once()
    
    @pytest.mark.unit
    def test_list_groups_as_manager(self, service, mock_group_repo, manager_user):
        """Test manager sees only their groups"""
        mock_group_repo.get_by_manager.return_value = [
            {"id": "group-1", "name": "Team 1", "manager_ids": ["manager-1"]}
        ]
        
        groups = service.list_groups(manager_user)
        
        assert len(groups) == 1
        mock_group_repo.get_by_manager.assert_called_once_with("manager-1")
    
    @pytest.mark.unit
    def test_list_groups_as_user(self, service, mock_user_repo, mock_group_repo, regular_user):
        """Test regular user sees only their own groups"""
        # Mock user_repo to return user with group_ids
        mock_user_repo.get_by_id.return_value = {
            **regular_user,
            "group_ids": ["group-1", "group-2"]
        }
        
        # Mock group_repo to return groups
        mock_group_repo.get_by_id.side_effect = [
            {"id": "group-1", "name": "Team 1", "status": "active"},
            {"id": "group-2", "name": "Team 2", "status": "active"}
        ]
        
        groups = service.list_groups(regular_user)
        
        assert len(groups) == 2
        assert groups[0]["id"] == "group-1"
        assert groups[1]["id"] == "group-2"
    
    @pytest.mark.unit
    def test_list_groups_returns_empty_list(self, service, mock_group_repo, root_user):
        """Test list_groups returns empty list, never None"""
        mock_group_repo.get_all.return_value = None
        
        groups = service.list_groups(root_user)
        
        assert groups == []
    
    # Get Group Tests
    
    @pytest.mark.unit
    def test_get_group_as_root(self, service, mock_group_repo, root_user, sample_group):
        """Test root can get any group"""
        mock_group_repo.get_by_id.return_value = sample_group
        
        group = service.get_group("group-1", root_user)
        
        assert group["id"] == "group-1"
        mock_group_repo.get_by_id.assert_called_once_with("group-1")
    
    @pytest.mark.unit
    def test_get_group_as_manager_own_group(self, service, mock_group_repo, manager_user, sample_group):
        """Test manager can get their own group"""
        mock_group_repo.get_by_id.return_value = sample_group
        
        group = service.get_group("group-1", manager_user)
        
        assert group["id"] == "group-1"
    
    @pytest.mark.unit
    def test_get_group_as_manager_not_managed(self, service, mock_group_repo, manager_user):
        """Test manager cannot get group they don't manage"""
        group = {
            "id": "group-2",
            "name": "Other Team",
            "manager_ids": ["manager-2"]  # Different manager
        }
        mock_group_repo.get_by_id.return_value = group
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_group("group-2", manager_user)
        
        assert exc_info.value.status_code == 403
        assert "Not a manager of this group" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_get_group_not_found(self, service, mock_group_repo, root_user):
        """Test get non-existent group raises 404"""
        mock_group_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_group("nonexistent", root_user)
        
        assert exc_info.value.status_code == 404
    
    # Create Group Tests
    
    @pytest.mark.unit
    def test_create_group_as_root(self, service, mock_group_repo, root_user):
        """Test root can create group"""
        mock_group_repo.create_with_validation.return_value = {
            "id": "group-new",
            "name": "New Team",
            "status": "active"
        }
        
        group = service.create_group({"name": "New Team"}, root_user)
        
        assert group["name"] == "New Team"
        mock_group_repo.create_with_validation.assert_called_once()
    
    @pytest.mark.unit
    def test_create_group_as_manager_forbidden(self, service, manager_user):
        """Test manager cannot create group"""
        with pytest.raises(HTTPException) as exc_info:
            service.create_group({"name": "New Team"}, manager_user)
        
        assert exc_info.value.status_code == 403
        assert "Only root" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_create_group_duplicate_name(self, service, mock_group_repo, root_user):
        """Test create with duplicate name raises 400"""
        mock_group_repo.create_with_validation.side_effect = Exception("already exists")
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_group({"name": "Existing Team"}, root_user)
        
        assert exc_info.value.status_code == 400
    
    # Update Group Tests
    
    @pytest.mark.unit
    def test_update_group_as_manager(self, service, mock_group_repo, manager_user, sample_group):
        """Test manager can update their group"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_group_repo.name_exists.return_value = False
        mock_group_repo.update.return_value = {**sample_group, "name": "Updated Team"}
        
        updated = service.update_group("group-1", {"name": "Updated Team"}, manager_user)
        
        assert updated["name"] == "Updated Team"
        mock_group_repo.update.assert_called_once()
    
    @pytest.mark.unit
    def test_update_group_name_conflict(self, service, mock_group_repo, root_user, sample_group):
        """Test update with existing name raises 400"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_group_repo.name_exists.return_value = True
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_group("group-1", {"name": "Existing Name"}, root_user)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
    
    # Toggle Status Tests
    
    @pytest.mark.unit
    def test_toggle_status(self, service, mock_group_repo, root_user, sample_group):
        """Test toggling group status"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_group_repo.update.return_value = {**sample_group, "status": "disabled"}
        
        updated = service.toggle_status("group-1", "disabled", root_user)
        
        assert updated["status"] == "disabled"
        mock_group_repo.update.assert_called_once_with("group-1", {"status": "disabled"})
    
    # Delete Group Tests
    
    @pytest.mark.unit
    def test_delete_group_as_root(self, service, mock_group_repo, root_user, sample_group):
        """Test root can delete group"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_group_repo.delete.return_value = True
        
        result = service.delete_group("group-1", root_user)
        
        assert result is True
        mock_group_repo.delete.assert_called_once_with("group-1")
    
    @pytest.mark.unit
    def test_delete_group_as_manager_forbidden(self, service, manager_user):
        """Test manager cannot delete group"""
        with pytest.raises(HTTPException) as exc_info:
            service.delete_group("group-1", manager_user)
        
        assert exc_info.value.status_code == 403
        assert "Only root" in str(exc_info.value.detail)
    
    # Member Management Tests
    
    @pytest.mark.unit
    def test_add_member(self, service, mock_group_repo, mock_user_repo, root_user, sample_group):
        """Test adding member to group"""
        mock_group_repo.get_by_id.return_value = sample_group
        
        # Mock user_repo to return user with existing group_ids
        mock_user_repo.get_by_id.return_value = {
            "id": "user-3",
            "name": "New User",
            "group_ids": ["group-5"]  # User already in another group
        }
        
        mock_group_repo.add_member.return_value = {
            **sample_group,
            "member_ids": ["user-1", "user-2", "user-3"]
        }
        
        updated = service.add_member("group-1", "user-3", root_user)
        
        assert "user-3" in updated["member_ids"]
        mock_group_repo.add_member.assert_called_once_with("group-1", "user-3")
        
        # Verify user's group_ids were updated (bidirectional)
        mock_user_repo.update.assert_called_once_with("user-3", {"group_ids": ["group-5", "group-1"]})
    
    
    @pytest.mark.unit
    def test_add_member_user_not_found(self, service, mock_group_repo, mock_user_repo, root_user, sample_group):
        """Test adding non-existent user raises 404"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            service.add_member("group-1", "nonexistent", root_user)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_remove_member(self, service, mock_group_repo, mock_user_repo, root_user, sample_group):
        """Test removing member from group"""
        mock_group_repo.get_by_id.return_value = sample_group
        
        # Mock user_repo to return user with group_ids
        mock_user_repo.get_by_id.return_value = {
            "id": "user-1",
            "name": "User 1",
            "group_ids": ["group-1", "group-2"]
        }
        
        mock_group_repo.remove_member.return_value = {
            **sample_group,
            "member_ids": ["user-2"]
        }
        
        updated = service.remove_member("group-1", "user-1", root_user)
        
        assert "user-1" not in updated["member_ids"]
        mock_group_repo.remove_member.assert_called_once_with("group-1", "user-1")
        
        # Verify user's group_ids were updated (bidirectional)
        mock_user_repo.update.assert_called_once_with("user-1", {"group_ids": ["group-2"]})
    
    # Manager Assignment Tests
    
    @pytest.mark.unit
    def test_assign_manager(self, service, mock_group_repo, mock_user_repo, root_user, sample_group):
        """Test assigning manager to group"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_user_repo.get_by_id.return_value = {
            "id": "manager-2",
            "name": "New Manager",
            "role": "manager"
        }
        mock_group_repo.add_manager.return_value = {
            **sample_group,
            "manager_ids": ["manager-1", "manager-2"]
        }
        
        updated = service.assign_manager("group-1", "manager-2", root_user)
        
        assert "manager-2" in updated["manager_ids"]
        mock_group_repo.add_manager.assert_called_once_with("group-1", "manager-2")
    
    @pytest.mark.unit
    def test_assign_manager_as_manager_forbidden(self, service, manager_user):
        """Test manager cannot assign managers"""
        with pytest.raises(HTTPException) as exc_info:
            service.assign_manager("group-1", "manager-2", manager_user)
        
        assert exc_info.value.status_code == 403
        assert "Only root" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_assign_manager_user_not_manager_role(self, service, mock_group_repo, mock_user_repo, root_user, sample_group):
        """Test cannot assign user without manager role"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_user_repo.get_by_id.return_value = {
            "id": "user-3",
            "name": "Regular User",
            "role": "user"  # Not manager!
        }
        
        with pytest.raises(HTTPException) as exc_info:
            service.assign_manager("group-1", "user-3", root_user)
        
        assert exc_info.value.status_code == 400
        assert "must have manager or root role" in str(exc_info.value.detail)
    
    @pytest.mark.unit
    def test_remove_manager(self, service, mock_group_repo, root_user, sample_group):
        """Test removing manager from group"""
        mock_group_repo.get_by_id.return_value = sample_group
        mock_group_repo.remove_manager.return_value = {
            **sample_group,
            "manager_ids": []
        }
        
        updated = service.remove_manager("group-1", "manager-1", root_user)
        
        assert "manager-1" not in updated["manager_ids"]
        mock_group_repo.remove_manager.assert_called_once_with("group-1", "manager-1")