"""
Path: backend/tests/unit/repositories/test_user_group_repository.py
Version: 2

Changes in v2:
- FIX: Replaced group_repo.get() with group_repo.get_by_id() in test_delete_group
- Reason: BaseRepository has get_by_id(), not get()

Unit tests for UserGroupRepository
"""

import pytest
from datetime import datetime

from src.repositories.user_group_repository import UserGroupRepository
from src.database.exceptions import DuplicateKeyError, NotFoundError
from tests.unit.mocks.mock_database import MockDatabase


class TestUserGroupRepository:
    """Test UserGroupRepository with mock database"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("user_groups")
        return db
    
    @pytest.fixture
    def group_repo(self, mock_db):
        """Provide UserGroupRepository with mock database"""
        return UserGroupRepository(db=mock_db)
    
    @pytest.fixture
    def sample_group(self):
        """Sample user group data"""
        return {
            "name": "Engineering Team",
            "status": "active"
        }
    
    # Create Tests
    
    @pytest.mark.unit
    def test_create_group_with_validation(self, group_repo, sample_group):
        """Test creating group with validation"""
        group = group_repo.create_with_validation(sample_group)
        
        assert group["name"] == sample_group["name"]
        assert group["status"] == sample_group["status"]
        assert "id" in group
        assert "created_at" in group
        assert group["manager_ids"] == []
        assert group["member_ids"] == []
    
    @pytest.mark.unit
    def test_create_group_duplicate_name(self, group_repo, sample_group):
        """Test duplicate name raises error"""
        group_repo.create_with_validation(sample_group)
        
        with pytest.raises(DuplicateKeyError, match="already exists"):
            group_repo.create_with_validation(sample_group)
    
    @pytest.mark.unit
    def test_create_group_default_status(self, group_repo):
        """Test group created with default active status"""
        group = group_repo.create_with_validation({"name": "Test Group"})
        
        assert group["status"] == "active"
    
    # Read Tests
    
    @pytest.mark.unit
    def test_get_by_name(self, group_repo, sample_group):
        """Test get group by name"""
        created = group_repo.create_with_validation(sample_group)
        
        found = group_repo.get_by_name(sample_group["name"])
        
        assert found is not None
        assert found["id"] == created["id"]
        assert found["name"] == sample_group["name"]
    
    @pytest.mark.unit
    def test_get_by_name_not_found(self, group_repo):
        """Test get by name returns None if not found"""
        found = group_repo.get_by_name("NonExistent Group")
        
        assert found is None
    
    @pytest.mark.unit
    def test_name_exists(self, group_repo, sample_group):
        """Test name_exists returns True for existing name"""
        group_repo.create_with_validation(sample_group)
        
        assert group_repo.name_exists(sample_group["name"]) is True
        assert group_repo.name_exists("Other Name") is False
    
    @pytest.mark.unit
    def test_name_exists_exclude_id(self, group_repo, sample_group):
        """Test name_exists can exclude specific group"""
        group = group_repo.create_with_validation(sample_group)
        
        # Same name but excluding this group should return False
        assert group_repo.name_exists(sample_group["name"], exclude_id=group["id"]) is False
    
    @pytest.mark.unit
    def test_get_by_manager(self, group_repo, sample_group):
        """Test get groups by manager"""
        # Create groups
        group1 = group_repo.create_with_validation(sample_group)
        group2_data = sample_group.copy()
        group2_data["name"] = "Marketing Team"
        group2 = group_repo.create_with_validation(group2_data)
        
        # Assign manager to groups
        group_repo.add_manager(group1["id"], "manager-1")
        group_repo.add_manager(group2["id"], "manager-1")
        
        # Get groups managed by manager-1
        groups = group_repo.get_by_manager("manager-1")
        
        assert len(groups) == 2
        group_ids = [g["id"] for g in groups]
        assert group1["id"] in group_ids
        assert group2["id"] in group_ids
    
    # Member Management Tests
    
    @pytest.mark.unit
    def test_add_member(self, group_repo, sample_group):
        """Test adding member to group"""
        group = group_repo.create_with_validation(sample_group)
        
        updated = group_repo.add_member(group["id"], "user-1")
        
        assert "user-1" in updated["member_ids"]
        assert len(updated["member_ids"]) == 1
    
    @pytest.mark.unit
    def test_add_member_no_duplicates(self, group_repo, sample_group):
        """Test adding same member twice doesn't create duplicates"""
        group = group_repo.create_with_validation(sample_group)
        
        group_repo.add_member(group["id"], "user-1")
        updated = group_repo.add_member(group["id"], "user-1")
        
        assert updated["member_ids"].count("user-1") == 1
    
    @pytest.mark.unit
    def test_add_member_not_found(self, group_repo):
        """Test add member to non-existent group raises error"""
        with pytest.raises(NotFoundError, match="not found"):
            group_repo.add_member("nonexistent-id", "user-1")
    
    @pytest.mark.unit
    def test_remove_member(self, group_repo, sample_group):
        """Test removing member from group"""
        group = group_repo.create_with_validation(sample_group)
        group_repo.add_member(group["id"], "user-1")
        group_repo.add_member(group["id"], "user-2")
        
        updated = group_repo.remove_member(group["id"], "user-1")
        
        assert "user-1" not in updated["member_ids"]
        assert "user-2" in updated["member_ids"]
        assert len(updated["member_ids"]) == 1
    
    @pytest.mark.unit
    def test_remove_member_not_present(self, group_repo, sample_group):
        """Test removing non-present member does nothing"""
        group = group_repo.create_with_validation(sample_group)
        
        updated = group_repo.remove_member(group["id"], "user-1")
        
        assert updated["member_ids"] == []
    
    # Manager Management Tests
    
    @pytest.mark.unit
    def test_add_manager(self, group_repo, sample_group):
        """Test adding manager to group"""
        group = group_repo.create_with_validation(sample_group)
        
        updated = group_repo.add_manager(group["id"], "manager-1")
        
        assert "manager-1" in updated["manager_ids"]
        assert len(updated["manager_ids"]) == 1
    
    @pytest.mark.unit
    def test_add_manager_no_duplicates(self, group_repo, sample_group):
        """Test adding same manager twice doesn't create duplicates"""
        group = group_repo.create_with_validation(sample_group)
        
        group_repo.add_manager(group["id"], "manager-1")
        updated = group_repo.add_manager(group["id"], "manager-1")
        
        assert updated["manager_ids"].count("manager-1") == 1
    
    @pytest.mark.unit
    def test_remove_manager(self, group_repo, sample_group):
        """Test removing manager from group"""
        group = group_repo.create_with_validation(sample_group)
        group_repo.add_manager(group["id"], "manager-1")
        group_repo.add_manager(group["id"], "manager-2")
        
        updated = group_repo.remove_manager(group["id"], "manager-1")
        
        assert "manager-1" not in updated["manager_ids"]
        assert "manager-2" in updated["manager_ids"]
        assert len(updated["manager_ids"]) == 1
    
    @pytest.mark.unit
    def test_remove_manager_not_present(self, group_repo, sample_group):
        """Test removing non-present manager does nothing"""
        group = group_repo.create_with_validation(sample_group)
        
        updated = group_repo.remove_manager(group["id"], "manager-1")
        
        assert updated["manager_ids"] == []
    
    # Update Tests
    
    @pytest.mark.unit
    def test_update_group_name(self, group_repo, sample_group):
        """Test updating group name"""
        group = group_repo.create_with_validation(sample_group)
        
        updated = group_repo.update(group["id"], {"name": "Updated Team"})
        
        assert updated["name"] == "Updated Team"
        assert updated["status"] == sample_group["status"]
    
    # Delete Tests
    
    @pytest.mark.unit
    def test_delete_group(self, group_repo, sample_group):
        """Test deleting group"""
        group = group_repo.create_with_validation(sample_group)
        
        result = group_repo.delete(group["id"])
        
        assert result is True
        assert group_repo.get_by_id(group["id"]) is None