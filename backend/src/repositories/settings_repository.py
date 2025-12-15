"""
Path: backend/src/repositories/settings_repository.py
Version: 3

Changes in v3:
- CRITICAL FIX: get_by_user() now searches by user_id filter (not _key)
- upsert() now correctly finds existing settings by user_id before update
- Fixes 409 Duplicate key error when settings already exist
- Previous v2 searched by _key=user_id, but _key is auto-generated

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
    
    Each user has one settings document linked by user_id field
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
        super().__init__(db=db, collection="settings")
    
    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get settings for a user
        
        Searches by user_id field (not _key).
        
        Args:
            user_id: User ID
            
        Returns:
            Settings document or None if not found
        """
        settings_list = self.db.get_all(
            self.collection,
            filters={"user_id": user_id},
            limit=1
        )
        
        return settings_list[0] if settings_list else None
    
    def upsert(self, user_id: str, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update user settings
        
        If settings exist for user_id, updates them.
        If not, creates new settings document.
        
        Args:
            user_id: User ID
            settings_data: Settings fields to update
            
        Returns:
            Updated settings document with id
        """
        # Check if settings exist by user_id
        existing = self.get_by_user(user_id)
        
        if existing:
            # Update existing settings
            settings_id = existing["id"]
            update_data = {
                **settings_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            return self.db.update(self.collection, settings_id, update_data)
        else:
            # Create new settings
            create_data = {
                "user_id": user_id,
                **settings_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            }
            return self.create(create_data)
    
    def delete_by_user(self, user_id: str) -> bool:
        """
        Delete user settings
        
        Useful for cleanup when user is deleted.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        existing = self.get_by_user(user_id)
        if existing:
            return self.delete(existing["id"])
        return False