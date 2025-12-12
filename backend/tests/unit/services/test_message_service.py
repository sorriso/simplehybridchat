"""
Path: backend/tests/unit/services/test_message_service.py
Version: 1

Unit tests for MessageService
"""

import pytest
from datetime import datetime
from fastapi import HTTPException

from src.services.message_service import MessageService
from src.models.message import MessageCreate
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Mock database"""
    db = MockDatabase()
    db.create_collection("conversations")
    db.create_collection("messages")
    return db


@pytest.fixture
def message_service(mock_db):
    """MessageService with mock database"""
    return MessageService(db=mock_db)


@pytest.fixture
def current_user():
    """Current user fixture"""
    return {
        "id": "user-1",
        "email": "user@example.com",
        "role": "user",
        "group_ids": ["group-1"]
    }


@pytest.fixture
def owned_conversation(mock_db, current_user):
    """Conversation owned by current user"""
    return mock_db.create("conversations", {
        "title": "My Conv",
        "owner_id": current_user["id"],
        "shared_with_group_ids": [],
        "group_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })


@pytest.fixture
def shared_conversation(mock_db, current_user):
    """Conversation shared with current user"""
    return mock_db.create("conversations", {
        "title": "Shared Conv",
        "owner_id": "user-other",
        "shared_with_group_ids": ["group-1"],
        "group_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })


class TestMessageServiceRead:
    """Tests for message retrieval"""
    
    def test_get_conversation_messages_as_owner(self, message_service, mock_db, current_user, owned_conversation):
        """Test getting messages for owned conversation"""
        # Create messages
        mock_db.create("messages", {
            "conversation_id": owned_conversation["id"],
            "role": "user",
            "content": "Hello",
            "timestamp": datetime(2024, 1, 15, 10, 0, 0)
        })
        mock_db.create("messages", {
            "conversation_id": owned_conversation["id"],
            "role": "assistant",
            "content": "Hi there",
            "timestamp": datetime(2024, 1, 15, 10, 0, 5)
        })
        
        result = message_service.get_conversation_messages(owned_conversation["id"], current_user)
        
        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"
    
    def test_get_conversation_messages_with_shared_access(self, message_service, mock_db, current_user, shared_conversation):
        """Test getting messages for shared conversation"""
        # Create message
        mock_db.create("messages", {
            "conversation_id": shared_conversation["id"],
            "role": "user",
            "content": "Test",
            "timestamp": datetime.utcnow()
        })
        
        result = message_service.get_conversation_messages(shared_conversation["id"], current_user)
        
        assert len(result) == 1
    
    def test_get_conversation_messages_no_access(self, message_service, mock_db, current_user):
        """Test getting messages without access fails"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        with pytest.raises(HTTPException) as exc_info:
            message_service.get_conversation_messages(conv["id"], current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_get_conversation_messages_not_found(self, message_service, current_user):
        """Test getting messages for non-existent conversation"""
        with pytest.raises(HTTPException) as exc_info:
            message_service.get_conversation_messages("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404


class TestMessageServiceCreate:
    """Tests for message creation"""
    
    def test_create_message_as_owner(self, message_service, mock_db, current_user, owned_conversation):
        """Test creating message as conversation owner"""
        message_data = MessageCreate(
            conversation_id=owned_conversation["id"],
            role="user",
            content="Test message"
        )
        
        result = message_service.create_message(message_data, current_user)
        
        assert result.conversation_id == owned_conversation["id"]
        assert result.role == "user"
        assert result.content == "Test message"
        assert result.id is not None
    
    def test_create_message_shared_user_denied(self, message_service, mock_db, current_user, shared_conversation):
        """Test that shared users cannot create messages"""
        message_data = MessageCreate(
            conversation_id=shared_conversation["id"],
            role="user",
            content="Test message"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            message_service.create_message(message_data, current_user)
        
        assert exc_info.value.status_code == 403
        assert "owner" in exc_info.value.detail.lower()
    
    def test_create_message_no_access(self, message_service, mock_db, current_user):
        """Test creating message without access fails"""
        conv = mock_db.create("conversations", {
            "title": "Other's Conv",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "group_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        message_data = MessageCreate(
            conversation_id=conv["id"],
            role="user",
            content="Test"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            message_service.create_message(message_data, current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_create_message_conversation_not_found(self, message_service, current_user):
        """Test creating message for non-existent conversation"""
        message_data = MessageCreate(
            conversation_id="nonexistent",
            role="user",
            content="Test"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            message_service.create_message(message_data, current_user)
        
        assert exc_info.value.status_code == 404


class TestMessageServiceCount:
    """Tests for message counting"""
    
    def test_get_message_count(self, message_service, mock_db, owned_conversation):
        """Test getting message count for conversation"""
        # Create messages
        for i in range(5):
            mock_db.create("messages", {
                "conversation_id": owned_conversation["id"],
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.utcnow()
            })
        
        result = message_service.get_message_count(owned_conversation["id"])
        
        assert result == 5
    
    def test_get_message_count_empty(self, message_service, owned_conversation):
        """Test getting message count for conversation with no messages"""
        result = message_service.get_message_count(owned_conversation["id"])
        
        assert result == 0