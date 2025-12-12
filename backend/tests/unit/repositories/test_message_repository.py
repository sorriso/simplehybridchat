"""
Path: backend/tests/unit/repositories/test_message_repository.py
Version: 1

Unit tests for MessageRepository
"""

import pytest
from datetime import datetime

from src.repositories.message_repository import MessageRepository
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Mock database for testing"""
    return MockDatabase()


@pytest.fixture
def message_repo(mock_db):
    """MessageRepository with mock database"""
    return MessageRepository(db=mock_db)


class TestMessageRepository:
    """Unit tests for MessageRepository"""
    
    def test_get_by_conversation(self, message_repo, mock_db):
        """Test get_by_conversation returns messages sorted chronologically"""
        # Setup
        mock_db.create_collection("messages")
        msg1 = mock_db.create("messages", {
            "conversation_id": "conv-1",
            "role": "user",
            "content": "Hello",
            "timestamp": datetime(2024, 1, 15, 10, 0, 0)
        })
        msg2 = mock_db.create("messages", {
            "conversation_id": "conv-1",
            "role": "assistant",
            "content": "Hi there",
            "timestamp": datetime(2024, 1, 15, 10, 0, 5)
        })
        msg3 = mock_db.create("messages", {
            "conversation_id": "conv-2",
            "role": "user",
            "content": "Other conv",
            "timestamp": datetime(2024, 1, 15, 10, 0, 3)
        })
        
        # Execute
        result = message_repo.get_by_conversation("conv-1")
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == msg1["id"]  # Oldest first
        assert result[1]["id"] == msg2["id"]
    
    def test_count_by_conversation(self, message_repo, mock_db):
        """Test count_by_conversation returns correct count"""
        # Setup
        mock_db.create_collection("messages")
        for i in range(5):
            mock_db.create("messages", {
                "conversation_id": "conv-1",
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.utcnow()
            })
        for i in range(3):
            mock_db.create("messages", {
                "conversation_id": "conv-2",
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.utcnow()
            })
        
        # Execute
        result = message_repo.count_by_conversation("conv-1")
        
        # Assert
        assert result == 5
    
    def test_create_message(self, message_repo, mock_db):
        """Test create_message creates a message with timestamp"""
        # Setup
        mock_db.create_collection("messages")
        
        # Execute
        result = message_repo.create_message(
            conversation_id="conv-1",
            role="user",
            content="Test message"
        )
        
        # Assert
        assert result["conversation_id"] == "conv-1"
        assert result["role"] == "user"
        assert result["content"] == "Test message"
        assert "timestamp" in result
        assert "id" in result
    
    def test_delete_by_conversation(self, message_repo, mock_db):
        """Test delete_by_conversation deletes all messages in conversation"""
        # Setup
        mock_db.create_collection("messages")
        for i in range(3):
            mock_db.create("messages", {
                "conversation_id": "conv-1",
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.utcnow()
            })
        mock_db.create("messages", {
            "conversation_id": "conv-2",
            "role": "user",
            "content": "Other conv message",
            "timestamp": datetime.utcnow()
        })
        
        # Execute
        deleted_count = message_repo.delete_by_conversation("conv-1")
        
        # Assert
        assert deleted_count == 3
        remaining = message_repo.get_by_conversation("conv-1")
        assert len(remaining) == 0
        other_conv = message_repo.get_by_conversation("conv-2")
        assert len(other_conv) == 1