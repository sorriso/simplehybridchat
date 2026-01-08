"""
Path: backend/tests/unit/services/test_conversation_service.py
Version: 1

Unit tests for ConversationService
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.services.conversation_service import ConversationService
from src.models.conversation import ConversationCreate, ConversationUpdate, ShareConversationRequest, UnshareConversationRequest
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Mock database"""
    db = MockDatabase()
    db.create_collection("conversations")
    return db


@pytest.fixture
def conversation_service(mock_db):
    """ConversationService with mock database"""
    return ConversationService(db=mock_db)


@pytest.fixture
def current_user():
    """Current user fixture"""
    return {
        "id": "user-1",
        "email": "user@example.com",
        "role": "user",
        "group_ids": ["group-1", "group-2"]
    }


@pytest.fixture
def other_user():
    """Other user fixture"""
    return {
        "id": "user-2",
        "email": "other@example.com",
        "role": "user",
        "group_ids": ["group-3"]
    }


class TestConversationServiceCreate:
    """Tests for conversation creation"""
    
    def test_create_conversation_success(self, conversation_service, current_user):
        """Test creating a conversation successfully"""
        conversation_data = ConversationCreate(title="Test Conv")
        
        result = conversation_service.create_conversation(conversation_data, current_user)
        
        assert result.title == "Test Conv"
        assert result.owner_id == current_user["id"]
        assert result.is_shared is False
        assert result.message_count == 0
    
    def test_create_conversation_with_group(self, conversation_service, current_user):
        """Test creating a conversation with group_id"""
        conversation_data = ConversationCreate(title="Work Conv", group_id="group-work")
        
        result = conversation_service.create_conversation(conversation_data, current_user)
        
        assert result.group_id == "group-work"
    
    def test_create_conversation_default_title(self, conversation_service, current_user):
        """Test creating a conversation with default title"""
        conversation_data = ConversationCreate()
        
        result = conversation_service.create_conversation(conversation_data, current_user)
        
        assert result.title == "New Conversation"


class TestConversationServiceRead:
    """Tests for conversation retrieval"""
    
    def test_get_conversation_as_owner(self, conversation_service, mock_db, current_user):
        """Test getting conversation as owner"""
        conv = mock_db.create("conversations", {
            "title": "My Conv",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = conversation_service.get_conversation(conv["id"], current_user)
        
        assert result.id == conv["id"]
        assert result.title == "My Conv"
    
    def test_get_conversation_with_shared_access(self, conversation_service, mock_db, current_user):
        """Test getting conversation with shared access"""
        # Mock user_repo to return current_user with group_ids
        conversation_service.user_repo.get_by_id = Mock(return_value=current_user)
        
        conv = mock_db.create("conversations", {
            "title": "Shared Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-1"],  # current_user is in group-1
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = conversation_service.get_conversation(conv["id"], current_user)
        
        assert result.id == conv["id"]
        assert result.is_shared is True
    
    def test_get_conversation_access_denied(self, conversation_service, mock_db, current_user):
        """Test getting conversation without access"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-999"],  # current_user not in this group
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        with pytest.raises(HTTPException) as exc_info:
            conversation_service.get_conversation(conv["id"], current_user)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
    
    def test_get_conversation_not_found(self, conversation_service, current_user):
        """Test getting non-existent conversation"""
        with pytest.raises(HTTPException) as exc_info:
            conversation_service.get_conversation("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404
    
    def test_list_conversations(self, conversation_service, mock_db, current_user):
        """Test listing user's conversations"""
        mock_db.create("conversations", {
            "title": "Conv 1",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        mock_db.create("conversations", {
            "title": "Conv 2",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = conversation_service.list_conversations(current_user)
        
        assert len(result) == 2
        assert all(conv.owner_id == current_user["id"] for conv in result)
    
    def test_list_shared_conversations(self, conversation_service, mock_db, current_user):
        """Test listing conversations shared with user"""
        # Mock user_repo to return current_user with group_ids
        conversation_service.user_repo.get_by_id = Mock(return_value=current_user)
        
        mock_db.create("conversations", {
            "title": "Shared Conv 1",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-1"],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        mock_db.create("conversations", {
            "title": "Shared Conv 2",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-2"],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        mock_db.create("conversations", {
            "title": "Not Shared",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-999"],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = conversation_service.list_shared_conversations(current_user)
        
        assert len(result) == 2


class TestConversationServiceUpdate:
    """Tests for conversation updates"""
    
    def test_update_conversation_as_owner(self, conversation_service, mock_db, current_user):
        """Test updating conversation as owner"""
        conv = mock_db.create("conversations", {
            "title": "Old Title",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        updates = ConversationUpdate(title="New Title")
        result = conversation_service.update_conversation(conv["id"], updates, current_user)
        
        assert result.title == "New Title"
    
    def test_update_conversation_not_owner(self, conversation_service, mock_db, current_user):
        """Test updating conversation as non-owner fails"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        updates = ConversationUpdate(title="Hacked")
        
        with pytest.raises(HTTPException) as exc_info:
            conversation_service.update_conversation(conv["id"], updates, current_user)
        
        assert exc_info.value.status_code == 403
        assert "owner" in exc_info.value.detail.lower()
    
    def test_update_conversation_ungroup(self, conversation_service, mock_db, current_user):
        """Test ungrouping conversation (group_id = None)"""
        conv = mock_db.create("conversations", {
            "title": "Grouped Conv",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": "group-work",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        updates = ConversationUpdate(group_id=None)
        result = conversation_service.update_conversation(conv["id"], updates, current_user)
        
        assert result.group_id is None


class TestConversationServiceDelete:
    """Tests for conversation deletion"""
    
    def test_delete_conversation_as_owner(self, conversation_service, mock_db, current_user):
        """Test deleting conversation as owner"""
        conv = mock_db.create("conversations", {
            "title": "To Delete",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = conversation_service.delete_conversation(conv["id"], current_user)
        
        assert result is True
        # Verify deleted
        assert mock_db.get_by_id("conversations", conv["id"]) is None
    
    def test_delete_conversation_not_owner(self, conversation_service, mock_db, current_user):
        """Test deleting conversation as non-owner fails"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        with pytest.raises(HTTPException) as exc_info:
            conversation_service.delete_conversation(conv["id"], current_user)
        
        assert exc_info.value.status_code == 403


class TestConversationServiceSharing:
    """Tests for conversation sharing"""
    
    def test_share_conversation(self, conversation_service, mock_db, current_user):
        """Test sharing conversation with groups"""
        conv = mock_db.create("conversations", {
            "title": "My Conv",
            "owner_id": current_user["id"],
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        share_data = ShareConversationRequest(group_ids=["group-a", "group-b"])
        result = conversation_service.share_conversation(conv["id"], share_data, current_user)
        
        assert "group-a" in result.shared_with_group_ids
        assert "group-b" in result.shared_with_group_ids
        assert result.is_shared is True
    
    def test_share_conversation_not_owner(self, conversation_service, mock_db, current_user):
        """Test sharing conversation as non-owner fails"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        share_data = ShareConversationRequest(group_ids=["group-a"])
        
        with pytest.raises(HTTPException) as exc_info:
            conversation_service.share_conversation(conv["id"], share_data, current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_unshare_conversation(self, conversation_service, mock_db, current_user):
        """Test unsharing conversation from groups"""
        conv = mock_db.create("conversations", {
            "title": "Shared Conv",
            "owner_id": current_user["id"],
            "shared_with_group_ids": ["group-a", "group-b", "group-c"],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        unshare_data = UnshareConversationRequest(group_ids=["group-a", "group-c"])
        result = conversation_service.unshare_conversation(conv["id"], unshare_data, current_user)
        
        assert "group-a" not in result.shared_with_group_ids
        assert "group-b" in result.shared_with_group_ids
        assert "group-c" not in result.shared_with_group_ids
    
    def test_unshare_all_groups_sets_is_shared_false(self, conversation_service, mock_db, current_user):
        """Test that unsharing all groups sets is_shared to False"""
        conv = mock_db.create("conversations", {
            "title": "Shared Conv",
            "owner_id": current_user["id"],
            "shared_with_group_ids": ["group-a"],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        unshare_data = UnshareConversationRequest(group_ids=["group-a"])
        result = conversation_service.unshare_conversation(conv["id"], unshare_data, current_user)
        
        assert result.is_shared is False