"""
Path: backend/src/repositories/file_repository.py
Version: 1

Repository for file metadata storage in ArangoDB
Files are stored in MinIO, metadata in ArangoDB
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class FileRepository(BaseRepository):
    """
    Repository for file metadata
    
    Stores metadata about files uploaded to MinIO:
    - name, size, type
    - minio_path (object name in MinIO)
    - uploaded_by, uploaded_at
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
        super().__init__(db=db, collection="files")
    
    def create(self, file_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create file metadata
        
        Args:
            file_data: File metadata (name, size, type, minio_path)
            user_id: User ID who uploaded the file
            
        Returns:
            Created file document with id
        """
        metadata = {
            **file_data,
            "uploaded_by": user_id,
            "uploaded_at": datetime.utcnow()
        }
        return super().create(metadata)
    
    def get_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by ID
        
        Args:
            file_id: File ID
            
        Returns:
            File metadata or None if not found
        """
        return super().get_by_id(file_id)
    
    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all files uploaded by a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of file metadata documents
        """
        return super().get_all(filters={"uploaded_by": user_id})
    
    def delete(self, file_id: str) -> bool:
        """
        Delete file metadata
        
        Args:
            file_id: File ID
            
        Returns:
            True if deleted, False if not found
        """
        return super().delete(file_id)
    
    def get_by_minio_path(self, minio_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by MinIO path
        
        Useful for cleanup operations.
        
        Args:
            minio_path: MinIO object name
            
        Returns:
            File metadata or None if not found
        """
        files = super().get_all(filters={"minio_path": minio_path})
        return files[0] if files else None