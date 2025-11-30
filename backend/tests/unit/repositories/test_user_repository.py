"""
Path: tests/unit/repositories/test_user_repository.py
Version: 2

Changes in v2:
- Modified all assertions: assert "_key" in → assert "id" in
- Modified all user accesses: user["_key"] → user["id"]
- Tests now verify repository returns 'id' from MockDatabase

Unit tests for UserRepository
"""

import pytest
from datetime import datetime

from src.repositories.user_repository import UserRepository
from src.database.exceptions import DuplicateKeyError, NotFoundError
from tests.unit.mocks.mock_database import MockDatabase


class TestUserRepository:
    """Test UserRepository with mock database"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("users")
        return db
    
    @pytest.fixture
    def user_repo(self, mock_db):
        """Provide UserRepository with mock database"""
        return UserRepository(db=mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Sample user data"""
        return {
            "name": "Test User",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "role": "user",
            "status": "active"
        }
    
    # Create Tests
    
    @pytest.mark.unit
    def test_create_user_with_validation(self, user_repo, sample_user):
        """Test creating user with validation"""
        user = user_repo.create_with_validation(sample_user)
        
        assert user["name"] == sample_user["name"]
        assert user["email"] == sample_user["email"]
        assert "id" in user
        assert "created_at" in user
    
    @pytest.mark.unit
    def test_create_user_duplicate_email(self, user_repo, sample_user):
        """Test duplicate email raises error"""
        user_repo.create_with_validation(sample_user)
        
        with pytest.raises(DuplicateKeyError, match="Email already exists"):
            user_repo.create_with_validation(sample_user)
    
    # Read Tests
    
    @pytest.mark.unit
    def test_get_by_email(self, user_repo, sample_user):
        """Test get user by email"""
        created = user_repo.create_with_validation(sample_user)
        
        found = user_repo.get_by_email(sample_user["email"])
        
        assert found is not None
        assert found["id"] == created["id"]
        assert found["email"] == sample_user["email"]
    
    @pytest.mark.unit
    def test_get_by_email_not_found(self, user_repo):
        """Test get by email returns None if not found"""
        result = user_repo.get_by_email("nonexistent@example.com")
        assert result is None
    
    @pytest.mark.unit
    def test_email_exists(self, user_repo, sample_user):
        """Test email exists check"""
        assert user_repo.email_exists(sample_user["email"]) is False
        
        user_repo.create_with_validation(sample_user)
        
        assert user_repo.email_exists(sample_user["email"]) is True
    
    @pytest.mark.unit
    def test_email_exists_exclude_id(self, user_repo, sample_user):
        """Test email exists with ID exclusion"""
        user = user_repo.create_with_validation(sample_user)
        
        # Same email, same ID = False (excluded)
        assert user_repo.email_exists(sample_user["email"], exclude_id=user["id"]) is False
        
        # Same email, different ID = True
        assert user_repo.email_exists(sample_user["email"], exclude_id="other-id") is True
    
    # Update Tests
    
    @pytest.mark.unit
    def test_update_with_validation(self, user_repo, sample_user):
        """Test update user with validation"""
        user = user_repo.create_with_validation(sample_user)
        
        updated = user_repo.update_with_validation(
            user["id"],
            {"name": "Updated Name"}
        )
        
        assert updated["name"] == "Updated Name"
        assert updated["email"] == sample_user["email"]
        assert "updated_at" in updated
    
    @pytest.mark.unit
    def test_update_email_duplicate(self, user_repo, sample_user):
        """Test update with duplicate email raises error"""
        user1 = user_repo.create_with_validation(sample_user)
        
        user2_data = sample_user.copy()
        user2_data["email"] = "other@example.com"
        user2 = user_repo.create_with_validation(user2_data)
        
        # Try to update user2 email to user1's email
        with pytest.raises(DuplicateKeyError, match="Email already exists"):
            user_repo.update_with_validation(
                user2["id"],
                {"email": sample_user["email"]}
            )
    
    @pytest.mark.unit
    def test_update_not_found(self, user_repo):
        """Test update non-existent user raises error"""
        with pytest.raises(NotFoundError):
            user_repo.update_with_validation("nonexistent-id", {"name": "Test"})
    
    # Filter Tests
    
    @pytest.mark.unit
    def test_get_by_role(self, user_repo, sample_user):
        """Test get users by role"""
        # Create users with different roles
        user1 = sample_user.copy()
        user1["email"] = "user1@example.com"
        user1["role"] = "user"
        user_repo.create_with_validation(user1)
        
        user2 = sample_user.copy()
        user2["email"] = "user2@example.com"
        user2["role"] = "manager"
        user_repo.create_with_validation(user2)
        
        user3 = sample_user.copy()
        user3["email"] = "user3@example.com"
        user3["role"] = "user"
        user_repo.create_with_validation(user3)
        
        # Get users by role
        users = user_repo.get_by_role("user")
        managers = user_repo.get_by_role("manager")
        
        assert len(users) == 2
        assert len(managers) == 1
        assert all(u["role"] == "user" for u in users)
        assert managers[0]["role"] == "manager"
    
    @pytest.mark.unit
    def test_get_by_status(self, user_repo, sample_user):
        """Test get users by status"""
        # Create users with different statuses
        user1 = sample_user.copy()
        user1["email"] = "user1@example.com"
        user1["status"] = "active"
        user_repo.create_with_validation(user1)
        
        user2 = sample_user.copy()
        user2["email"] = "user2@example.com"
        user2["status"] = "disabled"
        user_repo.create_with_validation(user2)
        
        # Get users by status
        active = user_repo.get_by_status("active")
        disabled = user_repo.get_by_status("disabled")
        
        assert len(active) == 1
        assert len(disabled) == 1
        assert active[0]["status"] == "active"
        assert disabled[0]["status"] == "disabled"
    
    # Count Tests
    
    @pytest.mark.unit
    def test_count_by_role(self, user_repo, sample_user):
        """Test count users by role"""
        user1 = sample_user.copy()
        user1["email"] = "user1@example.com"
        user1["role"] = "user"
        user_repo.create_with_validation(user1)
        
        user2 = sample_user.copy()
        user2["email"] = "user2@example.com"
        user2["role"] = "user"
        user_repo.create_with_validation(user2)
        
        assert user_repo.count_by_role("user") == 2
        assert user_repo.count_by_role("manager") == 0
    
    @pytest.mark.unit
    def test_count_by_status(self, user_repo, sample_user):
        """Test count users by status"""
        user1 = sample_user.copy()
        user1["email"] = "user1@example.com"
        user_repo.create_with_validation(user1)
        
        assert user_repo.count_by_status("active") == 1
        assert user_repo.count_by_status("disabled") == 0