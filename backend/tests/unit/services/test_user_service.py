"""
Path: tests/unit/services/test_user_service.py
Version: 3

Changes in v3:
- Fixed user1["_key"] → user1["id"] (line 157)
- Fixed user2["_key"] → user2["id"] (line 161)

Changes in v2:
- Modified all user dict mocks: {"_key": ...} → {"id": ...}
- Modified all user accesses: user["_key"] → user["id"]
- Fixed test_delete_self_forbidden: expects 403 not 400
- Tests now use middleware format (id) for current_user mocks

Unit tests for UserService

Changes in v1.2:
- FIX: Patch 'src.core.security.hash_password' au lieu de 'src.services.user_service.hash_password'
- FIX: user_repo.db mock correct
- FIX: UserResponse validation - ajout _key et _id
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.services.user_service import UserService
from src.models.user import UserCreate, UserUpdate
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_db():
    """Provide clean mock database"""
    db = MockDatabase()
    db.connect()
    db.create_collection("users")
    yield db
    db.disconnect()


@pytest.fixture
def user_service(mock_db):
    """Provide UserService with mocked repository"""
    service = UserService()
    service.user_repo.db = mock_db
    return service


class TestUserService:
    """Unit tests for UserService"""
    
    @patch('src.core.security.hash_password')
    def test_create_user_as_root(self, mock_hash, user_service):
        """Test creating user as root"""
        mock_hash.return_value = "hashed_password"
        
        root_user = {"id": "root-id", "role": "root"}
        
        user_data = UserCreate(
            name="New User",
            email="newuser@example.com",
            password="StrongPass123",
            role="user",
            status="active"
        )
        
        user = user_service.create_user(user_data, root_user)
        
        assert user.name == "New User"
        assert user.email == "newuser@example.com"
        assert user.role == "user"
    
    def test_create_user_as_manager_forbidden(self, user_service):
        """Test that manager cannot create users"""
        manager_user = {"id": "manager-id", "role": "manager"}
        
        user_data = UserCreate(
            name="New User",
            email="newuser@example.com",
            password="StrongPass123",
            role="user",
            status="active"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_user(user_data, manager_user)
        
        assert exc_info.value.status_code == 403
    
    def test_create_user_as_user_forbidden(self, user_service):
        """Test that regular user cannot create users"""
        regular_user = {"id": "user-id", "role": "user"}
        
        user_data = UserCreate(
            name="New User",
            email="newuser@example.com",
            password="StrongPass123",
            role="user",
            status="active"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_user(user_data, regular_user)
        
        assert exc_info.value.status_code == 403
    
    def test_get_user_self(self, user_service):
        """Test user can get their own profile"""
        # Create user with all required fields
        user = user_service.user_repo.db.create("users", {
            "name": "Test User",
            "email": "test@example.com",
            "role": "user",
            "status": "active"
        })
        
        user_id = user["id"]
        current_user = {"id": user_id, "role": "user"}
        
        # Get own profile
        retrieved = user_service.get_user(user_id, current_user)
        
        assert retrieved.name == "Test User"
        assert retrieved.email == "test@example.com"
    
    def test_get_other_user_as_manager(self, user_service):
        """Test manager can get other user's profile"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "Other User",
            "email": "other@example.com",
            "role": "user",
            "status": "active"
        })
        
        manager_user = {"id": "manager-id", "role": "manager"}
        
        # Get other user's profile
        retrieved = user_service.get_user(user["id"], manager_user)
        
        assert retrieved.name == "Other User"
    
    def test_get_other_user_as_user_forbidden(self, user_service):
        """Test user cannot get other user's profile"""
        # Create two users
        user1 = user_service.user_repo.db.create("users", {
            "name": "User 1",
            "email": "user1@example.com",
            "role": "user",
            "status": "active"
        })
        
        user2 = user_service.user_repo.db.create("users", {
            "name": "User 2",
            "email": "user2@example.com",
            "role": "user",
            "status": "active"
        })
        
        current_user = {"id": user1["id"], "role": "user"}
        
        # Try to get user2's profile
        with pytest.raises(HTTPException) as exc_info:
            user_service.get_user(user2["id"], current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_list_users_as_manager(self, user_service):
        """Test manager can list users"""
        # Create users
        user_service.user_repo.db.create("users", {
            "name": "User 1",
            "role": "user",
            "status": "active",
            "email": "user1@example.com"
        })
        user_service.user_repo.db.create("users", {
            "name": "User 2",
            "role": "user",
            "status": "active",
            "email": "user2@example.com"
        })
        user_service.user_repo.db.create("users", {
            "name": "User 3",
            "role": "user",
            "status": "active",
            "email": "user3@example.com"
        })
        
        manager_user = {"id": "manager-id", "role": "manager"}
        
        # List users
        users = user_service.list_users(manager_user)
        
        assert len(users) == 3
    
    def test_list_users_as_user_forbidden(self, user_service):
        """Test regular user cannot list users"""
        regular_user = {"id": "user-id", "role": "user"}
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.list_users(regular_user)
        
        assert exc_info.value.status_code == 403
    
    def test_update_self(self, user_service):
        """Test user can update their own profile"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "Original Name",
            "email": "test@example.com",
            "role": "user",
            "status": "active"
        })
        
        user_id = user["id"]
        current_user = {"id": user_id, "role": "user"}
        
        # Update name
        update_data = UserUpdate(name="Updated Name")
        updated = user_service.update_user(user_id, update_data, current_user)
        
        assert updated.name == "Updated Name"
    
    def test_update_role_as_user_forbidden(self, user_service):
        """Test user cannot update their own role"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "Test User",
            "email": "test@example.com",
            "role": "user",
            "status": "active"
        })
        
        user_id = user["id"]
        current_user = {"id": user_id, "role": "user"}
        
        # Try to update role
        update_data = UserUpdate(role="root")
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.update_user(user_id, update_data, current_user)
        
        assert exc_info.value.status_code == 403
    
    def test_update_role_as_manager(self, user_service):
        """Test manager can update user's role"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "Test User",
            "email": "test@example.com",
            "role": "user",
            "status": "active"
        })
        
        manager_user = {"id": "manager-id", "role": "manager"}
        
        # Update role
        update_data = UserUpdate(role="manager")
        updated = user_service.update_user(user["id"], update_data, manager_user)
        
        assert updated.role == "manager"
    
    def test_delete_user_as_root(self, user_service):
        """Test root can delete users"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "User to Delete",
            "email": "delete@example.com",
            "role": "user",
            "status": "active"
        })
        
        root_user = {"id": "root-id", "role": "root"}
        
        # Delete user
        deleted = user_service.delete_user(user["id"], root_user)
        
        assert deleted is True
    
    def test_delete_user_as_manager_forbidden(self, user_service):
        """Test manager cannot delete users"""
        # Create user
        user = user_service.user_repo.db.create("users", {
            "name": "User",
            "email": "user@example.com",
            "role": "user",
            "status": "active"
        })
        
        manager_user = {"id": "manager-id", "role": "manager"}
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.delete_user(user["id"], manager_user)
        
        assert exc_info.value.status_code == 403
    
    def test_delete_self_forbidden(self, user_service):
        """Test user cannot delete themselves"""
        # Create root user
        root = user_service.user_repo.db.create("users", {
            "name": "Root",
            "email": "root@example.com",
            "role": "root",
            "status": "active"
        })
        
        root_user = {"id": root["id"], "role": "root"}
        
        # Try to delete self
        with pytest.raises(HTTPException) as exc_info:
            user_service.delete_user(root["id"], root_user)
        
        assert exc_info.value.status_code == 403