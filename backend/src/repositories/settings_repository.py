"""
Path: backend/src/repositories/settings_repository.py
Version: 1

Repository for user settings persistence in ArangoDB
"""

from typing import Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    """
    Repository for user settings
    
    Stores user preferences and configuration:
    - prompt_customization
    - theme (light/dark)
    - language (en/fr/es/de)
    
    Uses user_id as _key for 1:1 relationship with users
    """
    
    def __init__(self, db=None):
        """
        Initialize repository with collection name
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        from src.database.factory import get_database
        if db is None:
            db = get_database()
        super().__init__(db=db, collection="user_settings")
    
    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get settings for a user
        
        Uses user_id as _key for direct lookup.
        
        Args:
            user_id: User ID
            
        Returns:
            Settings document or None if not found
        """
        return super().get_by_id(user_id)
    
    def upsert(self, user_id: str, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update user settings
        
        Uses user_id as _key. If settings exist, updates them.
        If not, creates new settings document.
        
        Args:
            user_id: User ID
            settings_data: Settings fields to update
            
        Returns:
            Updated settings document with id
        """
        # Check if settings exist
        existing = self.get_by_user(user_id)
        
        if existing:
            # Update existing settings
            update_data = {
                **settings_data,
                "updated_at": datetime.utcnow()
            }
            return super().update(user_id, update_data)
        else:
            # Create new settings with user_id as _key
            create_data = {
                "_key": user_id,
                **settings_data,
                "updated_at": datetime.utcnow()
            }
            return super().create(create_data)
    
    def delete_by_user(self, user_id: str) -> bool:
        """
        Delete user settings
        
        Useful for cleanup when user is deleted.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        return super().delete(user_id)