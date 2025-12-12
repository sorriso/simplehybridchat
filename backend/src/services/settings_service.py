"""
Path: backend/src/services/settings_service.py
Version: 1

Service for user settings management
"""

import logging
from typing import Dict, Any

from src.repositories.settings_repository import SettingsRepository
from src.database.interface import IDatabase

logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service for user settings operations
    
    Handles:
    - Default settings generation
    - Partial updates (merge)
    - Settings retrieval
    """
    
    # Default settings values
    DEFAULT_SETTINGS = {
        "prompt_customization": "",
        "theme": "light",
        "language": "en"
    }
    
    def __init__(self, db: IDatabase = None):
        """Initialize service with repository"""
        self.settings_repo = SettingsRepository(db=db)
    
    def get_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user settings
        
        Returns stored settings or defaults if none exist.
        Always returns a complete settings object.
        
        Args:
            user_id: User ID
            
        Returns:
            Complete settings dict with all fields
        """
        # Try to get stored settings
        stored_settings = self.settings_repo.get_by_user(user_id)
        
        if stored_settings:
            # Merge with defaults to ensure all fields present
            # (in case new fields were added to DEFAULT_SETTINGS)
            settings = {**self.DEFAULT_SETTINGS}
            
            # Update with stored values
            for key in self.DEFAULT_SETTINGS.keys():
                if key in stored_settings:
                    settings[key] = stored_settings[key]
            
            logger.debug(f"Retrieved settings for user {user_id}")
            return settings
        else:
            # Return defaults for new user
            logger.debug(f"No settings found for user {user_id}, returning defaults")
            return self.DEFAULT_SETTINGS.copy()
    
    def update_settings(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user settings (partial update)
        
        Performs a merge: only updates provided fields,
        keeps existing values for other fields.
        
        Steps:
        1. Get current settings (or defaults)
        2. Merge with provided updates
        3. Save to database
        4. Return complete updated settings
        
        Args:
            user_id: User ID
            updates: Fields to update (partial)
            
        Returns:
            Complete updated settings dict
            
        Example:
            # User has: {theme: "dark", language: "fr", prompt: ""}
            update_settings(user_id, {"language": "en"})
            # Result: {theme: "dark", language: "en", prompt: ""}
        """
        # Get current settings
        current_settings = self.get_settings(user_id)
        
        # Merge updates (only update provided fields)
        merged_settings = {**current_settings}
        for key, value in updates.items():
            if key in self.DEFAULT_SETTINGS:
                merged_settings[key] = value
            else:
                logger.warning(f"Ignoring unknown setting field: {key}")
        
        # Save to database
        self.settings_repo.upsert(user_id, merged_settings)
        
        logger.info(f"Updated settings for user {user_id}: {list(updates.keys())}")
        
        return merged_settings
    
    def reset_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Reset user settings to defaults
        
        Deletes stored settings and returns defaults.
        
        Args:
            user_id: User ID
            
        Returns:
            Default settings dict
        """
        self.settings_repo.delete_by_user(user_id)
        logger.info(f"Reset settings for user {user_id}")
        return self.DEFAULT_SETTINGS.copy()
    
    def delete_settings(self, user_id: str) -> bool:
        """
        Delete user settings
        
        Used for cleanup when user is deleted.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        deleted = self.settings_repo.delete_by_user(user_id)
        if deleted:
            logger.info(f"Deleted settings for user {user_id}")
        return deleted