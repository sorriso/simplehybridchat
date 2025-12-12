"""
Path: backend/tests/integration/repositories/test_user_group_repository_integration.py
Version: 2

Changes in v2:
- FIX: Replaced repo.get() with repo.get_by_id() globally (4 occurrences)
- Affects: All tests that retrieve groups after operations
- Reason: BaseRepository has get_by_id(), not get()

Integration tests for UserGroupRepository with real ArangoDB
"""

import pytest
from datetime import datetime

from src.repositories.user_group_repository import UserGroupRepository
from src.database.exceptions import DuplicateKeyError, NotFoundError


@pytest.mark.integration
@pytest.mark.integration_slow
class TestUserGroupRepositoryIntegration:
    """Test UserGroupRepository with real ArangoDB container"""
    
    def test_create_and_retrieve_group(self, arango_container_function):
        """Test creating and retrieving group from real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({
            "name": "Engineering Team",
            "status": "active"
        })
        
        # Retrieve group
        retrieved = repo.get_by_id(group["id"])
        
        assert retrieved is not None
        assert retrieved["name"] == "Engineering Team"
        assert retrieved["status"] == "active"
        assert "created_at" in retrieved
        assert retrieved["manager_ids"] == []
        assert retrieved["member_ids"] == []
    
    def test_create_duplicate_name_raises_error(self, arango_container_function):
        """Test duplicate name validation with real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create first group
        repo.create_with_validation({"name": "Unique Team"})
        
        # Try to create with same name
        with pytest.raises(DuplicateKeyError, match="already exists"):
            repo.create_with_validation({"name": "Unique Team"})
    
    def test_get_by_name(self, arango_container_function):
        """Test finding group by name"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        created = repo.create_with_validation({"name": "Search Team"})
        
        # Find by name
        found = repo.get_by_name("Search Team")
        
        assert found is not None
        assert found["id"] == created["id"]
        assert found["name"] == "Search Team"
    
    def test_name_exists_check(self, arango_container_function):
        """Test name existence check"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "Existing Team"})
        
        # Check existence
        assert repo.name_exists("Existing Team") is True
        assert repo.name_exists("Non-Existing Team") is False
        
        # Check with exclusion
        assert repo.name_exists("Existing Team", exclude_id=group["id"]) is False
    
    def test_update_group(self, arango_container_function):
        """Test updating group in real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "Original Name"})
        group_id = group["id"]
        
        # Update group
        updated = repo.update(group_id, {
            "name": "Updated Name",
            "status": "disabled"
        })
        
        assert updated["name"] == "Updated Name"
        assert updated["status"] == "disabled"
        assert "updated_at" in updated
    
    def test_delete_group(self, arango_container_function):
        """Test deleting group from real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "To Delete"})
        group_id = group["id"]
        
        # Delete group
        result = repo.delete(group_id)
        
        assert result is True
        
        # Verify deleted
        assert repo.get_by_id(group_id) is None
    
    def test_add_and_remove_member(self, arango_container_function):
        """Test member management with real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "Member Test"})
        group_id = group["id"]
        
        # Add member
        updated = repo.add_member(group_id, "user-1")
        assert "user-1" in updated["member_ids"]
        
        # Add another member
        updated = repo.add_member(group_id, "user-2")
        assert len(updated["member_ids"]) == 2
        
        # Remove member
        updated = repo.remove_member(group_id, "user-1")
        assert "user-1" not in updated["member_ids"]
        assert "user-2" in updated["member_ids"]
    
    def test_add_member_no_duplicates(self, arango_container_function):
        """Test adding same member twice doesn't create duplicates"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "Test Group"})
        
        # Add member twice
        repo.add_member(group["id"], "user-1")
        updated = repo.add_member(group["id"], "user-1")
        
        # Should only appear once
        assert updated["member_ids"].count("user-1") == 1
    
    def test_add_member_not_found_raises_error(self, arango_container_function):
        """Test adding member to non-existent group raises error"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        with pytest.raises(NotFoundError, match="not found"):
            repo.add_member("nonexistent-id", "user-1")
    
    def test_add_and_remove_manager(self, arango_container_function):
        """Test manager management with real database"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({"name": "Manager Test"})
        group_id = group["id"]
        
        # Add manager
        updated = repo.add_manager(group_id, "manager-1")
        assert "manager-1" in updated["manager_ids"]
        
        # Add another manager
        updated = repo.add_manager(group_id, "manager-2")
        assert len(updated["manager_ids"]) == 2
        
        # Remove manager
        updated = repo.remove_manager(group_id, "manager-1")
        assert "manager-1" not in updated["manager_ids"]
        assert "manager-2" in updated["manager_ids"]
    
    def test_get_by_manager(self, arango_container_function):
        """Test retrieving groups by manager"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create groups
        group1 = repo.create_with_validation({"name": "Team 1"})
        group2 = repo.create_with_validation({"name": "Team 2"})
        group3 = repo.create_with_validation({"name": "Team 3"})
        
        # Assign manager to groups 1 and 2
        repo.add_manager(group1["id"], "manager-1")
        repo.add_manager(group2["id"], "manager-1")
        repo.add_manager(group3["id"], "manager-2")
        
        # Get groups managed by manager-1
        groups = repo.get_by_manager("manager-1")
        
        assert len(groups) == 2
        group_names = [g["name"] for g in groups]
        assert "Team 1" in group_names
        assert "Team 2" in group_names
        assert "Team 3" not in group_names
    
    def test_get_all_groups(self, arango_container_function):
        """Test retrieving all groups"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create multiple groups
        repo.create_with_validation({"name": "Team A"})
        repo.create_with_validation({"name": "Team B"})
        repo.create_with_validation({"name": "Team C"})
        
        # Get all groups
        groups = repo.get_all()
        
        assert len(groups) == 3
        names = [g["name"] for g in groups]
        assert "Team A" in names
        assert "Team B" in names
        assert "Team C" in names
    
    def test_complex_workflow(self, arango_container_function):
        """Test complex workflow with multiple operations"""
        db = arango_container_function
        db.create_collection("user_groups")
        
        repo = UserGroupRepository(db=db)
        
        # Create group
        group = repo.create_with_validation({
            "name": "Engineering",
            "status": "active"
        })
        group_id = group["id"]
        
        # Add managers
        repo.add_manager(group_id, "manager-1")
        repo.add_manager(group_id, "manager-2")
        
        # Add members
        repo.add_member(group_id, "user-1")
        repo.add_member(group_id, "user-2")
        repo.add_member(group_id, "user-3")
        
        # Update status
        repo.update(group_id, {"status": "disabled"})
        
        # Retrieve and verify
        final = repo.get_by_id(group_id)
        
        assert final["name"] == "Engineering"
        assert final["status"] == "disabled"
        assert len(final["manager_ids"]) == 2
        assert len(final["member_ids"]) == 3
        assert "manager-1" in final["manager_ids"]
        assert "user-3" in final["member_ids"]
        
        # Remove some members and managers
        repo.remove_member(group_id, "user-2")
        repo.remove_manager(group_id, "manager-1")
        
        # Final check
        final = repo.get_by_id(group_id)
        assert len(final["manager_ids"]) == 1
        assert len(final["member_ids"]) == 2
        assert "user-2" not in final["member_ids"]
        assert "manager-1" not in final["manager_ids"]