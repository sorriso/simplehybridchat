"""
Path: backend/tests/unit/services/test_group_service.py
Version: 1

Unit tests for GroupService
"""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from src.services.group_service import GroupService


class TestGroupService:
    """Test GroupService"""
    
    def test_create_group(self):
        """Test create group"""
        mock_repo = MagicMock()
        mock_repo.create.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-1"}
        result = service.create_group({"name": "Work"}, current_user)
        
        assert result["id"] == "group-1"
        mock_repo.create.assert_called_once_with({"name": "Work"}, "user-1")
    
    def test_get_group_success(self):
        """Test get group by owner"""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-1"}
        result = service.get_group("group-1", current_user)
        
        assert result["id"] == "group-1"
    
    def test_get_group_not_found(self):
        """Test get nonexistent group"""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_group("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404
    
    def test_get_group_access_denied(self):
        """Test get group by non-owner"""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-2"}  # Different user
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_group("group-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_list_groups(self):
        """Test list user's groups"""
        mock_repo = MagicMock()
        mock_repo.get_by_owner.return_value = [
            {"id": "group-1", "name": "Work"},
            {"id": "group-2", "name": "Personal"}
        ]
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-1"}
        results = service.list_groups(current_user)
        
        assert len(results) == 2
        mock_repo.get_by_owner.assert_called_once_with("user-1")
    
    def test_update_group_success(self):
        """Test update group by owner"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        mock_group_repo.update.return_value = {
            "id": "group-1",
            "name": "Work Projects",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        
        current_user = {"id": "user-1"}
        result = service.update_group("group-1", {"name": "Work Projects"}, current_user)
        
        assert result["name"] == "Work Projects"
    
    def test_update_group_access_denied(self):
        """Test update group by non-owner"""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-2"}
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_group("group-1", {"name": "Hacked"}, current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_delete_group_success(self):
        """Test delete group and cleanup conversations"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1",
            "conversation_ids": ["conv-1", "conv-2"]
        }
        mock_group_repo.delete.return_value = True
        
        mock_conv_repo = MagicMock()
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1"}
        result = service.delete_group("group-1", current_user)
        
        assert result is True
        
        # Verify conversations were updated
        assert mock_conv_repo.update.call_count == 2
        mock_conv_repo.update.assert_any_call("conv-1", {"group_id": None})
        mock_conv_repo.update.assert_any_call("conv-2", {"group_id": None})
        
        # Verify group was deleted
        mock_group_repo.delete.assert_called_once_with("group-1")
    
    def test_delete_group_access_denied(self):
        """Test delete group by non-owner"""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_repo
        
        current_user = {"id": "user-2"}
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_group("group-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_add_conversation_to_group_success(self):
        """Test add conversation to group"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1",
            "conversation_ids": []
        }
        mock_group_repo.add_conversation.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1",
            "conversation_ids": ["conv-1"]
        }
        
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = {
            "id": "conv-1",
            "owner_id": "user-1"
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1"}
        result = service.add_conversation_to_group("group-1", "conv-1", current_user)
        
        assert "conv-1" in result["conversation_ids"]
        
        # Verify conversation.group_id was updated
        mock_conv_repo.update.assert_called_once_with("conv-1", {"group_id": "group-1"})
    
    def test_add_conversation_not_owner(self):
        """Test add conversation user doesn't own"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = {
            "id": "conv-1",
            "owner_id": "user-2"  # Different owner
        }
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            service.add_conversation_to_group("group-1", "conv-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_add_conversation_not_found(self):
        """Test add nonexistent conversation"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1"
        }
        
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = None
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            service.add_conversation_to_group("group-1", "nonexistent", current_user)
        
        assert exc_info.value.status_code == 404
    
    def test_remove_conversation_from_group_success(self):
        """Test remove conversation from group"""
        mock_group_repo = MagicMock()
        mock_group_repo.get_by_id.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1",
            "conversation_ids": ["conv-1"]
        }
        mock_group_repo.remove_conversation.return_value = {
            "id": "group-1",
            "name": "Work",
            "owner_id": "user-1",
            "conversation_ids": []
        }
        
        mock_conv_repo = MagicMock()
        
        service = GroupService(db=MagicMock())
        service.group_repo = mock_group_repo
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1"}
        result = service.remove_conversation_from_group("group-1", "conv-1", current_user)
        
        assert "conv-1" not in result["conversation_ids"]
        
        # Verify conversation.group_id was set to null
        mock_conv_repo.update.assert_called_once_with("conv-1", {"group_id": None})