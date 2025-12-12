"""
Path: backend/tests/unit/repositories/test_group_repository.py
Version: 3

Changes in v3:
- Fixed exception import: DocumentNotFoundError â†’ NotFoundError (correct exception in src.database.exceptions)

Changes in v2:
- Changed from MagicMock to MockDatabase (matches ConversationRepository test pattern)
- Fixed all tests to use MockDatabase properly with create_collection
- Removed mock_db.create/get_by_id/find_by_criteria mocking - use real MockDatabase methods

Unit tests for GroupRepository
"""

import pytest
from datetime import datetime

from src.repositories.group_repository import GroupRepository
from src.database.exceptions import NotFoundError
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Mock database for testing"""
    return MockDatabase()


@pytest.fixture
def group_repo(mock_db):
    """GroupRepository with mock database"""
    mock_db.create_collection("conversation_groups")
    return GroupRepository(db=mock_db)


class TestGroupRepository:
    """Test GroupRepository"""
    
    def test_create_group(self, group_repo, mock_db):
        """Test create group"""
        result = group_repo.create({"name": "Work"}, "user-1")
        
        assert result["id"] is not None
        assert result["name"] == "Work"
        assert result["owner_id"] == "user-1"
        assert result["conversation_ids"] == []
        assert "created_at" in result
    
    def test_get_by_id(self, group_repo, mock_db):
        """Test get group by ID"""
        # Create group
        created = group_repo.create({"name": "Work"}, "user-1")
        
        # Get by ID
        result = group_repo.get_by_id(created["id"])
        
        assert result["id"] == created["id"]
        assert result["name"] == "Work"
    
    def test_get_by_id_not_found(self, group_repo):
        """Test get nonexistent group returns None"""
        result = group_repo.get_by_id("nonexistent")
        assert result is None
    
    def test_get_by_owner(self, group_repo, mock_db):
        """Test get groups by owner"""
        # Create groups for user-1
        group1 = group_repo.create({"name": "Work"}, "user-1")
        group2 = group_repo.create({"name": "Personal"}, "user-1")
        
        # Create group for user-2
        group3 = group_repo.create({"name": "Other"}, "user-2")
        
        # Get groups for user-1
        results = group_repo.get_by_owner("user-1")
        
        assert len(results) == 2
        names = [g["name"] for g in results]
        assert "Work" in names
        assert "Personal" in names
        assert "Other" not in names
    
    def test_get_by_owner_empty(self, group_repo):
        """Test get groups for user with no groups"""
        results = group_repo.get_by_owner("user-1")
        assert results == []
    
    def test_update_group(self, group_repo, mock_db):
        """Test update group"""
        # Create group
        created = group_repo.create({"name": "Work"}, "user-1")
        
        # Update
        result = group_repo.update(created["id"], {"name": "Work Projects"})
        
        assert result["name"] == "Work Projects"
        assert result["id"] == created["id"]
    
    def test_update_group_not_found(self, group_repo):
        """Test update nonexistent group"""
        with pytest.raises(NotFoundError):
            group_repo.update("nonexistent", {"name": "New Name"})
    
    def test_delete_group(self, group_repo, mock_db):
        """Test delete group"""
        # Create group
        created = group_repo.create({"name": "Work"}, "user-1")
        
        # Delete
        result = group_repo.delete(created["id"])
        assert result is True
        
        # Verify deleted
        deleted = group_repo.get_by_id(created["id"])
        assert deleted is None
    
    def test_delete_group_not_found(self, group_repo):
        """Test delete nonexistent group"""
        result = group_repo.delete("nonexistent")
        assert result is False
    
    def test_add_conversation_to_group(self, group_repo, mock_db):
        """Test add conversation to group"""
        # Create group
        group = group_repo.create({"name": "Work"}, "user-1")
        assert group["conversation_ids"] == []
        
        # Add conversation
        result = group_repo.add_conversation(group["id"], "conv-1")
        
        assert "conv-1" in result["conversation_ids"]
        assert len(result["conversation_ids"]) == 1
    
    def test_add_conversation_already_in_group(self, group_repo, mock_db):
        """Test adding conversation that's already in group (idempotent)"""
        # Create group
        group = group_repo.create({"name": "Work"}, "user-1")
        
        # Add conversation first time
        result1 = group_repo.add_conversation(group["id"], "conv-1")
        assert len(result1["conversation_ids"]) == 1
        
        # Add same conversation again
        result2 = group_repo.add_conversation(group["id"], "conv-1")
        assert len(result2["conversation_ids"]) == 1
        assert result1["conversation_ids"] == result2["conversation_ids"]
    
    def test_add_conversation_group_not_found(self, group_repo):
        """Test add conversation when group doesn't exist"""
        with pytest.raises(NotFoundError):
            group_repo.add_conversation("nonexistent", "conv-1")
    
    def test_add_multiple_conversations_to_group(self, group_repo, mock_db):
        """Test add multiple conversations to group"""
        # Create group
        group = group_repo.create({"name": "Work"}, "user-1")
        
        # Add conversations
        result1 = group_repo.add_conversation(group["id"], "conv-1")
        result2 = group_repo.add_conversation(group["id"], "conv-2")
        result3 = group_repo.add_conversation(group["id"], "conv-3")
        
        assert len(result3["conversation_ids"]) == 3
        assert "conv-1" in result3["conversation_ids"]
        assert "conv-2" in result3["conversation_ids"]
        assert "conv-3" in result3["conversation_ids"]
    
    def test_remove_conversation_from_group(self, group_repo, mock_db):
        """Test remove conversation from group"""
        # Create group
        group = group_repo.create({"name": "Work"}, "user-1")
        
        # Add conversations
        group_repo.add_conversation(group["id"], "conv-1")
        group_repo.add_conversation(group["id"], "conv-2")
        
        # Remove one
        result = group_repo.remove_conversation(group["id"], "conv-1")
        
        assert "conv-1" not in result["conversation_ids"]
        assert "conv-2" in result["conversation_ids"]
        assert len(result["conversation_ids"]) == 1
    
    def test_remove_conversation_not_in_group(self, group_repo, mock_db):
        """Test removing conversation that's not in group (idempotent)"""
        # Create group with conversation
        group = group_repo.create({"name": "Work"}, "user-1")
        group_repo.add_conversation(group["id"], "conv-2")
        
        # Remove conversation that's not in group
        result = group_repo.remove_conversation(group["id"], "conv-1")
        
        # Should not change anything
        assert "conv-2" in result["conversation_ids"]
        assert len(result["conversation_ids"]) == 1
    
    def test_remove_conversation_group_not_found(self, group_repo):
        """Test remove conversation when group doesn't exist"""
        with pytest.raises(NotFoundError):
            group_repo.remove_conversation("nonexistent", "conv-1")
    
    def test_get_groups_containing_conversation(self, group_repo, mock_db):
        """Test get groups containing a conversation"""
        # Create groups
        group1 = group_repo.create({"name": "Work"}, "user-1")
        group2 = group_repo.create({"name": "Projects"}, "user-1")
        group3 = group_repo.create({"name": "Personal"}, "user-1")
        
        # Add conv-1 to group1 and group2
        group_repo.add_conversation(group1["id"], "conv-1")
        group_repo.add_conversation(group1["id"], "conv-2")
        group_repo.add_conversation(group2["id"], "conv-1")
        group_repo.add_conversation(group2["id"], "conv-3")
        
        # Get groups containing conv-1
        results = group_repo.get_groups_containing_conversation("conv-1")
        
        assert len(results) == 2
        group_ids = [g["id"] for g in results]
        assert group1["id"] in group_ids
        assert group2["id"] in group_ids
        assert group3["id"] not in group_ids
    
    def test_get_groups_containing_conversation_none(self, group_repo, mock_db):
        """Test get groups containing conversation that's in no groups"""
        # Create group without the conversation
        group_repo.create({"name": "Work"}, "user-1")
        
        # Search for conversation
        results = group_repo.get_groups_containing_conversation("conv-1")
        
        assert results == []