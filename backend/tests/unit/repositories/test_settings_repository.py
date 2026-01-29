"""
Path: backend/tests/unit/repositories/test_settings_repository.py
Version: 1.1

Changes in v1.1:
- FIX: test_init_without_db_uses_factory now patches 'src.database.factory.get_database'
- get_database is imported inside __init__, not at module level

Unit tests for SettingsRepository.

Tests cover:
- Initialization (with/without db)
- get_by_user()
- upsert() (create and update paths)
- delete_by_user()
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.repositories.settings_repository import SettingsRepository
from tests.unit.mocks.mock_database import MockDatabase


class TestSettingsRepositoryInit:
    """Test SettingsRepository initialization"""
    
    @pytest.mark.unit
    def test_init_with_provided_db(self):
        """Test initialization with provided database"""
        mock_db = MockDatabase()
        mock_db.connect()
        mock_db.create_collection("settings")
        
        repo = SettingsRepository(db=mock_db)
        
        assert repo.db == mock_db
        assert repo.collection == "settings"
    
    @pytest.mark.unit
    def test_init_without_db_uses_factory(self):
        """Test initialization without db uses factory"""
        # Patch at source module where get_database is defined
        with patch('src.database.factory.get_database') as mock_factory:
            mock_db = MagicMock()
            mock_factory.return_value = mock_db
            
            repo = SettingsRepository(db=None)
            
            mock_factory.assert_called_once()
            assert repo.db == mock_db


class TestSettingsRepositoryGetByUser:
    """Test get_by_user method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("settings")
        return db
    
    @pytest.fixture
    def settings_repo(self, mock_db):
        """Provide SettingsRepository with mock database"""
        return SettingsRepository(db=mock_db)
    
    @pytest.mark.unit
    def test_get_by_user_found(self, settings_repo, mock_db):
        """Test getting settings for existing user"""
        # Create settings directly in DB
        mock_db.create("settings", {
            "user_id": "user-123",
            "prompt_customization": "Custom prompt",
            "theme": "dark",
            "language": "en"
        })
        
        result = settings_repo.get_by_user("user-123")
        
        assert result is not None
        assert result["user_id"] == "user-123"
        assert result["theme"] == "dark"
    
    @pytest.mark.unit
    def test_get_by_user_not_found(self, settings_repo):
        """Test getting settings for non-existent user"""
        result = settings_repo.get_by_user("nonexistent-user")
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_by_user_multiple_users(self, settings_repo, mock_db):
        """Test getting correct user's settings when multiple exist"""
        # Create settings for multiple users
        mock_db.create("settings", {
            "user_id": "user-1",
            "theme": "light"
        })
        mock_db.create("settings", {
            "user_id": "user-2",
            "theme": "dark"
        })
        
        result = settings_repo.get_by_user("user-2")
        
        assert result is not None
        assert result["user_id"] == "user-2"
        assert result["theme"] == "dark"


class TestSettingsRepositoryUpsert:
    """Test upsert method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("settings")
        return db
    
    @pytest.fixture
    def settings_repo(self, mock_db):
        """Provide SettingsRepository with mock database"""
        return SettingsRepository(db=mock_db)
    
    @pytest.mark.unit
    def test_upsert_creates_new_settings(self, settings_repo):
        """Test upsert creates new settings when none exist"""
        result = settings_repo.upsert("user-new", {
            "theme": "dark",
            "language": "fr"
        })
        
        assert result is not None
        assert result["user_id"] == "user-new"
        assert result["theme"] == "dark"
        assert result["language"] == "fr"
        assert "created_at" in result
    
    @pytest.mark.unit
    def test_upsert_updates_existing_settings(self, settings_repo, mock_db):
        """Test upsert updates existing settings"""
        # Create initial settings
        mock_db.create("settings", {
            "user_id": "user-existing",
            "theme": "light",
            "language": "en",
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Upsert with new values
        result = settings_repo.upsert("user-existing", {
            "theme": "dark"
        })
        
        assert result is not None
        assert result["theme"] == "dark"
        assert "updated_at" in result
        assert result["updated_at"] is not None
    
    @pytest.mark.unit
    def test_upsert_preserves_user_id(self, settings_repo):
        """Test upsert sets correct user_id"""
        result = settings_repo.upsert("user-456", {
            "prompt_customization": "Be helpful"
        })
        
        assert result["user_id"] == "user-456"


class TestSettingsRepositoryDeleteByUser:
    """Test delete_by_user method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("settings")
        return db
    
    @pytest.fixture
    def settings_repo(self, mock_db):
        """Provide SettingsRepository with mock database"""
        return SettingsRepository(db=mock_db)
    
    @pytest.mark.unit
    def test_delete_by_user_success(self, settings_repo, mock_db):
        """Test deleting existing user settings"""
        # Create settings
        mock_db.create("settings", {
            "user_id": "user-to-delete",
            "theme": "dark"
        })
        
        # Verify it exists
        assert settings_repo.get_by_user("user-to-delete") is not None
        
        # Delete
        result = settings_repo.delete_by_user("user-to-delete")
        
        assert result is True
        assert settings_repo.get_by_user("user-to-delete") is None
    
    @pytest.mark.unit
    def test_delete_by_user_not_found(self, settings_repo):
        """Test deleting non-existent user settings returns False"""
        result = settings_repo.delete_by_user("nonexistent-user")
        
        assert result is False
    
    @pytest.mark.unit
    def test_delete_by_user_only_deletes_target_user(self, settings_repo, mock_db):
        """Test delete only affects target user's settings"""
        # Create settings for multiple users
        mock_db.create("settings", {
            "user_id": "user-keep",
            "theme": "light"
        })
        mock_db.create("settings", {
            "user_id": "user-delete",
            "theme": "dark"
        })
        
        # Delete one user
        settings_repo.delete_by_user("user-delete")
        
        # Other user's settings should remain
        assert settings_repo.get_by_user("user-keep") is not None
        assert settings_repo.get_by_user("user-delete") is None