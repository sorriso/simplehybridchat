"""
Path: backend/src/repositories/file_repository.py
Version: 4.2

Repository for file metadata storage in ArangoDB.
Files are stored in MinIO with hierarchical structure, metadata in ArangoDB.
Supports contextual uploads (system/user_global/user_project) and versioning.

Changes in v4.2:
- FIX: Access AQL via self.db._db.aql instead of self.db.aql (2 occurrences)
- ArangoDatabaseAdapter stores StandardDatabase in ._db attribute

Changes in v4.1:
- Made beartype import optional for development/testing compatibility
"""

from typing import Optional, Any
from datetime import datetime, timezone

# Optional beartype import for type validation
try:
    from beartype import beartype
except ImportError:
    # Fallback: no-op decorator if beartype not installed
    def beartype(func):
        return func

from src.repositories.base import BaseRepository
from src.database.interface import IDatabase


class FileRepository(BaseRepository):
    """
    Repository for file metadata with contextual scopes.
    
    Handles file metadata for:
    - System files (accessible to all users)
    - User global files (user-specific, no project)
    - User project files (project-specific)
    
    Supports versioning per processing phase.
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """
        Initialize repository with collection name.
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        if db is None:
            from src.database.factory import get_database
            db = get_database()
        super().__init__(db=db, collection="files")
    
    @beartype
    def create(
        self,
        file_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create file metadata.
        
        Args:
            file_data: File metadata containing:
                - name: Original filename
                - size: File size in bytes
                - type: MIME type
                - minio_path: Base path in MinIO
                - scope: File scope (system/user_global/user_project)
                - project_id: Project ID (if scope=user_project)
                - checksums: File checksums (md5, sha256, simhash)
                - processing_status: Processing phases status
            user_id: User ID who uploaded the file (optional for system files)
        
        Returns:
            Created file document with id and timestamps
        """
        now = datetime.now(timezone.utc)
        metadata = {
            **file_data,
            "uploaded_by": user_id,
            "uploaded_at": now.isoformat(),
            "promoted": False,
            "promoted_at": None,
            "promoted_by": None,
            "promoted_from": None
        }
        
        return super().create(metadata)
    
    @beartype
    def get_by_id(self, file_id: str) -> Optional[dict[str, Any]]:
        """
        Get file metadata by ID.
        
        Args:
            file_id: File identifier
        
        Returns:
            File metadata or None if not found
        """
        return super().get_by_id(file_id)
    
    @beartype
    def get_by_user(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all files uploaded by a user.
        
        Includes user_global and user_project files.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of file metadata documents
        """
        return super().get_all(filters={"uploaded_by": user_id})
    
    @beartype
    def get_by_scope(
        self,
        scope: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get files by scope with optional filters.
        
        Args:
            scope: File scope (system/user_global/user_project)
            user_id: Filter by user (for user_global/user_project)
            project_id: Filter by project (for user_project)
        
        Returns:
            List of file metadata documents
        """
        filters: dict[str, Any] = {"scope": scope}
        
        if user_id:
            filters["uploaded_by"] = user_id
        
        if project_id:
            filters["project_id"] = project_id
        
        return super().get_all(filters=filters)
    
    @beartype
    def get_by_project(self, project_id: str) -> list[dict[str, Any]]:
        """
        Get all files for a project.
        
        Args:
            project_id: Project identifier
        
        Returns:
            List of file metadata documents
        """
        return super().get_all(filters={
            "scope": "user_project",
            "project_id": project_id
        })
    
    @beartype
    def search_by_name(
        self,
        search_term: str,
        scope: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Search files by partial name match.
        
        Args:
            search_term: Search term (case-insensitive partial match)
            scope: Optional scope filter
            user_id: Optional user filter
            project_id: Optional project filter
        
        Returns:
            List of matching file metadata documents
        """
        query = "FOR file IN files FILTER LOWER(file.name) LIKE @search"
        bind_vars: dict[str, Any] = {"search": f"%{search_term.lower()}%"}
        
        if scope:
            query += " AND file.scope == @scope"
            bind_vars["scope"] = scope
        
        if user_id:
            query += " AND file.uploaded_by == @user_id"
            bind_vars["user_id"] = user_id
        
        if project_id:
            query += " AND file.project_id == @project_id"
            bind_vars["project_id"] = project_id
        
        query += " SORT file.name ASC RETURN file"
        
        cursor = self.db._db.aql.execute(query, bind_vars=bind_vars)
        return [doc for doc in cursor]
    
    @beartype
    def update_processing_status(
        self,
        file_id: str,
        phase: str,
        status: str,
        version: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """
        Update processing status for a phase.
        
        Args:
            file_id: File identifier
            phase: Processing phase (02-data_extraction, etc)
            status: New status (pending/processing/completed/failed)
            version: Optional version to add to available_versions
        
        Returns:
            Updated file document or None if not found
        """
        file = self.get_by_id(file_id)
        if not file:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Update phase status
        if "processing_status" not in file:
            file["processing_status"] = {"phases": {}}
        
        if phase not in file["processing_status"]["phases"]:
            file["processing_status"]["phases"][phase] = {
                "status": status,
                "active_version": None,
                "available_versions": [],
                "last_updated": now.isoformat()
            }
        else:
            file["processing_status"]["phases"][phase]["status"] = status
            file["processing_status"]["phases"][phase]["last_updated"] = now.isoformat()
        
        # Add version to available versions if provided
        if version:
            available = file["processing_status"]["phases"][phase]["available_versions"]
            if version not in available:
                available.append(version)
        
        # Update global status
        all_statuses = [
            p["status"]
            for p in file["processing_status"]["phases"].values()
        ]
        
        if all(s == "completed" for s in all_statuses):
            file["processing_status"]["global"] = "completed"
        elif any(s == "failed" for s in all_statuses):
            file["processing_status"]["global"] = "failed"
        elif any(s == "processing" for s in all_statuses):
            file["processing_status"]["global"] = "processing"
        else:
            file["processing_status"]["global"] = "pending"
        
        file["processing_status"]["last_updated"] = now.isoformat()
        
        return self.update(file_id, file)
    
    @beartype
    def set_active_version(
        self,
        file_id: str,
        phase: str,
        version: str
    ) -> Optional[dict[str, Any]]:
        """
        Set active version for a phase.
        
        Args:
            file_id: File identifier
            phase: Processing phase
            version: Version to set as active
        
        Returns:
            Updated file document or None if not found
        """
        file = self.get_by_id(file_id)
        if not file:
            return None
        
        if "processing_status" not in file or phase not in file["processing_status"]["phases"]:
            return None
        
        # Verify version exists
        available = file["processing_status"]["phases"][phase]["available_versions"]
        if version not in available:
            return None
        
        file["processing_status"]["phases"][phase]["active_version"] = version
        
        # Update active_configuration if exists
        if "active_configuration" not in file:
            file["active_configuration"] = {}
        
        file["active_configuration"][phase] = version
        file["active_configuration"]["last_modified"] = datetime.now(timezone.utc).isoformat()
        
        return self.update(file_id, file)
    
    @beartype
    def mark_promoted(
        self,
        file_id: str,
        promoted_by: str,
        promoted_from: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Mark file as promoted to system scope.
        
        Args:
            file_id: File identifier
            promoted_by: User who promoted the file
            promoted_from: Original file metadata
        
        Returns:
            Updated file document or None if not found
        """
        file = self.get_by_id(file_id)
        if not file:
            return None
        
        now = datetime.now(timezone.utc)
        file["promoted"] = True
        file["promoted_at"] = now.isoformat()
        file["promoted_by"] = promoted_by
        file["promoted_from"] = promoted_from
        
        return self.update(file_id, file)
    
    @beartype
    def delete(self, file_id: str) -> bool:
        """
        Delete file metadata.
        
        Args:
            file_id: File identifier
        
        Returns:
            True if deleted, False if not found
        """
        return super().delete(file_id)
    
    @beartype
    def get_by_minio_path(self, minio_path: str) -> Optional[dict[str, Any]]:
        """
        Get file metadata by MinIO base path.
        
        Useful for cleanup operations.
        
        Args:
            minio_path: MinIO base path
        
        Returns:
            File metadata or None if not found
        """
        files = super().get_all(filters={"minio_path": minio_path})
        return files[0] if files else None
    
    @beartype
    def get_by_checksum(
        self,
        checksum_type: str,
        checksum_value: str
    ) -> list[dict[str, Any]]:
        """
        Get files by checksum (for duplicate detection).
        
        Args:
            checksum_type: Type of checksum (md5, sha256, simhash)
            checksum_value: Checksum value
        
        Returns:
            List of files with matching checksum
        """
        query = f"""
        FOR file IN files
            FILTER file.checksums.{checksum_type} == @checksum_value
            RETURN file
        """
        
        cursor = self.db._db.aql.execute(
            query,
            bind_vars={"checksum_value": checksum_value}
        )
        
        return [doc for doc in cursor]