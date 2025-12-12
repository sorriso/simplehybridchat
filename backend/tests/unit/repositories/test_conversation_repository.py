"""
Path: backend/tests/unit/repositories/test_conversation_repository.py
Version: 1

Unit tests for ConversationRepository
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.repositories.conversation_repository import ConversationRepository
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Mock database for testing"""
    return MockDatabase()


@pytest.fixture
def conversation_repo(mock_db):
    """ConversationRepository with mock database"""
    return ConversationRepository(db=mock_db)


class TestConversationRepository:
    """Unit tests for ConversationRepository"""
    
    def test_get_by_owner(self, conversation_repo, mock_db):
        """Test get_by_owner returns user's conversations"""
        # Setup
        mock_db.create_collection("conversations")
        conv1 = mock_db.create("conversations", {
            "title": "Conv 1",
            "owner_id": "user-1",
            "updated_at": datetime(2024, 1, 15)
        })
        conv2 = mock_db.create("conversations", {
            "title": "Conv 2",
            "owner_id": "user-1",
            "updated_at": datetime(2024, 1, 14)
        })
        conv3 = mock_db.create("conversations", {
            "title": "Conv 3",
            "owner_id": "user-2",
            "updated_at": datetime(2024, 1, 13)
        })
        
        # Execute
        result = conversation_repo.get_by_owner("user-1")
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == conv1["id"]  # Newest first
        assert result[1]["id"] == conv2["id"]
    
    def test_get_shared_with_user(self, conversation_repo, mock_db):
        """Test get_shared_with_user returns conversations shared with user's groups"""
        # Setup
        mock_db.create_collection("conversations")
        conv1 = mock_db.create("conversations", {
            "title": "Shared Conv 1",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-1"],
            "updated_at": datetime(2024, 1, 15)
        })
        conv2 = mock_db.create("conversations", {
            "title": "Shared Conv 2",
            "owner_id": "user-other",
            "shared_with_group_ids": ["group-2", "group-3"],
            "updated_at": datetime(2024, 1, 14)
        })
        conv3 = mock_db.create("conversations", {
            "title": "Not Shared",
            "owner_id": "user-other",
            "shared_with_group_ids": [],
            "updated_at": datetime(2024, 1, 13)
        })
        
        # Execute - user belongs to group-1 and group-2
        result = conversation_repo.get_shared_with_user(["group-1", "group-2"])
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == conv1["id"]
        assert result[1]["id"] == conv2["id"]
    
    def test_get_shared_with_user_no_groups(self, conversation_repo, mock_db):
        """Test get_shared_with_user returns empty list if user has no groups"""
        result = conversation_repo.get_shared_with_user([])
        assert result == []
    
    def test_get_by_group(self, conversation_repo, mock_db):
        """Test get_by_group returns conversations in a group"""
        # Setup
        mock_db.create_collection("conversations")
        conv1 = mock_db.create("conversations", {
            "title": "Work Conv 1",
            "group_id": "group-work",
            "owner_id": "user-1",
            "updated_at": datetime(2024, 1, 15)
        })
        conv2 = mock_db.create("conversations", {
            "title": "Work Conv 2",
            "group_id": "group-work",
            "owner_id": "user-1",
            "updated_at": datetime(2024, 1, 14)
        })
        conv3 = mock_db.create("conversations", {
            "title": "Personal Conv",
            "group_id": "group-personal",
            "owner_id": "user-1",
            "updated_at": datetime(2024, 1, 13)
        })
        
        # Execute
        result = conversation_repo.get_by_group("group-work")
        
        # Assert
        assert len(result) == 2
        assert all(c["group_id"] == "group-work" for c in result)
    
    def test_set_shared_groups(self, conversation_repo, mock_db):
        """Test set_shared_groups replaces shared groups list"""
        # Setup
        mock_db.create_collection("conversations")
        conv = mock_db.create("conversations", {
            "title": "Test Conv",
            "owner_id": "user-1",
            "shared_with_group_ids": ["group-1", "group-2"],
            "updated_at": datetime(2024, 1, 15)
        })
        
        # Execute
        result = conversation_repo.set_shared_groups(conv["id"], ["group-3", "group-4"])
        
        # Assert
        assert result is True
        updated_conv = conversation_repo.get_by_id(conv["id"])
        assert updated_conv["shared_with_group_ids"] == ["group-3", "group-4"]
    
    def test_add_shared_group(self, conversation_repo, mock_db):
        """Test add_shared_group adds group to shared list"""
        # Setup
        mock_db.create_collection("conversations")
        conv = mock_db.create("conversations", {
            "title": "Test Conv",
            "owner_id": "user-1",
            "shared_with_group_ids": ["group-1"],
            "updated_at": datetime(2024, 1, 15)
        })
        
        # Execute
        result = conversation_repo.add_shared_group(conv["id"], "group-2")
        
        # Assert
        assert result is True
        updated_conv = conversation_repo.get_by_id(conv["id"])
        assert "group-2" in updated_conv["shared_with_group_ids"]
    
    def test_add_shared_group_no_duplicate(self, conversation_repo, mock_db):
        """Test add_shared_group does not add duplicates"""
        # Setup
        mock_db.create_collection("conversations")
        conv = mock_db.create("conversations", {
            "title": "Test Conv",
            "owner_id": "user-1",
            "shared_with_group_ids": ["group-1"],
            "updated_at": datetime(2024, 1, 15)
        })
        
        # Execute
        result = conversation_repo.add_shared_group(conv["id"], "group-1")
        
        # Assert
        updated_conv = conversation_repo.get_by_id(conv["id"])
        assert updated_conv["shared_with_group_ids"].count("group-1") == 1
    
    def test_remove_shared_group(self, conversation_repo, mock_db):
        """Test remove_shared_group removes group from shared list"""
        # Setup
        mock_db.create_collection("conversations")
        conv = mock_db.create("conversations", {
            "title": "Test Conv",
            "owner_id": "user-1",
            "shared_with_group_ids": ["group-1", "group-2"],
            "updated_at": datetime(2024, 1, 15)
        })
        
        # Execute
        result = conversation_repo.remove_shared_group(conv["id"], "group-1")
        
        # Assert
        assert result is True
        updated_conv = conversation_repo.get_by_id(conv["id"])
        assert "group-1" not in updated_conv["shared_with_group_ids"]
        assert "group-2" in updated_conv["shared_with_group_ids"]