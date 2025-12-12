"""
Path: backend/tests/unit/services/test_settings_service.py
Version: 1

Unit tests for SettingsService
"""

import pytest
from unittest.mock import MagicMock

from src.services.settings_service import SettingsService


class TestSettingsService:
    """Test SettingsService"""
    
    @pytest.fixture
    def mock_settings_repo(self):
        """Mock SettingsRepository"""
        return MagicMock()
    
    @pytest.fixture
    def settings_service(self, mock_settings_repo):
        """SettingsService with mocks"""
        service = SettingsService(db=MagicMock())
        service.settings_repo = mock_settings_repo
        return service
    
    def test_get_settings_returns_defaults_when_none_exist(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test get_settings returns defaults for new user"""
        # Mock no stored settings
        mock_settings_repo.get_by_user.return_value = None
        
        # Get settings
        settings = settings_service.get_settings("user-1")
        
        # Should return defaults
        assert settings == {
            "prompt_customization": "",
            "theme": "light",
            "language": "en"
        }
    
    def test_get_settings_returns_stored_settings(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test get_settings returns stored settings"""
        # Mock stored settings
        mock_settings_repo.get_by_user.return_value = {
            "id": "user-1",
            "prompt_customization": "Be concise",
            "theme": "dark",
            "language": "fr"
        }
        
        # Get settings
        settings = settings_service.get_settings("user-1")
        
        # Should return stored values
        assert settings["prompt_customization"] == "Be concise"
        assert settings["theme"] == "dark"
        assert settings["language"] == "fr"
    
    def test_get_settings_merges_with_defaults(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test get_settings fills missing fields with defaults"""
        # Mock partial stored settings (missing prompt_customization)
        mock_settings_repo.get_by_user.return_value = {
            "id": "user-1",
            "theme": "dark",
            "language": "fr"
        }
        
        # Get settings
        settings = settings_service.get_settings("user-1")
        
        # Should have stored values + default for missing field
        assert settings["theme"] == "dark"
        assert settings["language"] == "fr"
        assert settings["prompt_customization"] == ""  # Default
    
    def test_update_settings_partial_update(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test update_settings only updates provided fields"""
        # Mock current settings
        mock_settings_repo.get_by_user.return_value = {
            "id": "user-1",
            "prompt_customization": "Be brief",
            "theme": "dark",
            "language": "fr"
        }
        
        # Update only language
        updates = {"language": "en"}
        result = settings_service.update_settings("user-1", updates)
        
        # Should keep other fields unchanged
        assert result["prompt_customization"] == "Be brief"
        assert result["theme"] == "dark"
        assert result["language"] == "en"  # Updated
        
        # Verify upsert was called
        mock_settings_repo.upsert.assert_called_once()
    
    def test_update_settings_multiple_fields(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test update_settings with multiple fields"""
        # Mock current settings
        mock_settings_repo.get_by_user.return_value = None  # New user
        
        # Update multiple fields
        updates = {
            "theme": "dark",
            "language": "es"
        }
        result = settings_service.update_settings("user-1", updates)
        
        # Should have updated values + defaults for others
        assert result["theme"] == "dark"
        assert result["language"] == "es"
        assert result["prompt_customization"] == ""  # Default
    
    def test_update_settings_ignores_unknown_fields(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test update_settings ignores unknown fields"""
        # Mock current settings
        mock_settings_repo.get_by_user.return_value = None
        
        # Update with unknown field
        updates = {
            "theme": "dark",
            "unknown_field": "value"  # Should be ignored
        }
        result = settings_service.update_settings("user-1", updates)
        
        # Should have valid field, ignore unknown
        assert result["theme"] == "dark"
        assert "unknown_field" not in result
    
    def test_update_settings_creates_if_not_exist(
        self,
        settings_service,
        mock_settings_repo
    ):
        """Test update_settings creates settings for new user"""
        # Mock no existing settings
        mock_settings_repo.get_by_user.return_value = None
        
        # Update
        updates = {"theme": "dark"}
        settings_service.update_settings("user-1", updates)
        
        # Verify upsert was called
        mock_settings_repo.upsert.assert_called_once_with(
            "user-1",
            {
                "prompt_customization": "",
                "theme": "dark",
                "language": "en"
            }
        )
    
    def test_reset_settings(self, settings_service, mock_settings_repo):
        """Test reset_settings deletes and returns defaults"""
        # Reset settings
        result = settings_service.reset_settings("user-1")
        
        # Should delete from repo
        mock_settings_repo.delete_by_user.assert_called_once_with("user-1")
        
        # Should return defaults
        assert result == {
            "prompt_customization": "",
            "theme": "light",
            "language": "en"
        }
    
    def test_delete_settings(self, settings_service, mock_settings_repo):
        """Test delete_settings"""
        # Mock successful deletion
        mock_settings_repo.delete_by_user.return_value = True
        
        # Delete settings
        result = settings_service.delete_settings("user-1")
        
        # Should return True
        assert result is True
        mock_settings_repo.delete_by_user.assert_called_once_with("user-1")
    
    def test_delete_settings_not_found(self, settings_service, mock_settings_repo):
        """Test delete_settings when settings don't exist"""
        # Mock not found
        mock_settings_repo.delete_by_user.return_value = False
        
        # Delete settings
        result = settings_service.delete_settings("user-1")
        
        # Should return False
        assert result is False