"""
Path: backend/src/services/file_service.py
Version: 4.2

File service with contextual uploads, versioning, and Beartype validation.

Features:
- Contextual uploads (system/user_global/user_project)
- Hierarchical MinIO storage with versioning per phase
- Checksum calculation (MD5, SHA256, SimHash)
- Processing queue integration
- File promotion (project → system)
- Download with access control

Changes in v4.2:
- FIX: Import UploadFile from starlette.datastructures instead of fastapi
- Beartype requires exact type match, fastapi.UploadFile is alias to starlette's

Changes in v4.1:
- Made beartype import optional for development/testing compatibility
"""

import logging
import uuid
import hashlib
import json
from io import BytesIO
from typing import Optional, Literal, Any
from datetime import datetime, timezone

# Optional beartype import for type validation
try:
    from beartype import beartype
except ImportError:
    # Fallback: no-op decorator if beartype not installed
    def beartype(func):
        return func

from fastapi import HTTPException, status
from starlette.datastructures import UploadFile

from src.repositories.file_repository import FileRepository
from src.repositories.processing_queue_repository import ProcessingQueueRepository
from src.storage.factory import get_storage
from src.core.config import settings
from src.database.interface import IDatabase

logger = logging.getLogger(__name__)

# Type aliases for clarity
Scope = Literal["system", "user_global", "user_project"]
ProcessingPhase = Literal[
    "02-data_extraction",
    "03-summary",
    "04-chunking",
    "05-graph_extraction",
    "06-graph_aggregation"
]


class FileService:
    """
    File service with contextual uploads and versioning.
    
    All methods decorated with @beartype for runtime type validation.
    Supports hierarchical storage and processing pipeline.
    """
    
    # File validation constraints
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {
        '.pdf', '.txt', '.csv', '.json', '.md',
        '.docx', '.pptx', '.xlsx'
    }
    ALLOWED_CONTENT_TYPES = {
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json',
        'text/markdown',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    # Processing phases
    PHASES: list[ProcessingPhase] = [
        "02-data_extraction",
        "03-summary",
        "04-chunking",
        "05-graph_extraction",
        "06-graph_aggregation"
    ]
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize service with repositories and storage"""
        self.file_repo = FileRepository(db=db)
        self.queue_repo = ProcessingQueueRepository(db=db)
        self.storage = get_storage()
        self._ensure_bucket()
    
    @beartype
    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            if not self.storage.bucket_exists(settings.MINIO_DEFAULT_BUCKET):
                self.storage.create_bucket(settings.MINIO_DEFAULT_BUCKET)
                logger.info(f"Created bucket: {settings.MINIO_DEFAULT_BUCKET}")
        except Exception as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    @beartype
    def _validate_file_size(self, file: UploadFile) -> None:
        """
        Validate file size.
        
        Args:
            file: Uploaded file
        
        Raises:
            HTTPException 413: File too large
        """
        contents = file.file.read()
        file_size = len(contents)
        file.file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max: {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
    
    @beartype
    def _validate_file_type(self, file: UploadFile) -> None:
        """
        Validate file extension and content type.
        
        Args:
            file: Uploaded file
        
        Raises:
            HTTPException 400: Invalid file type
        """
        filename = file.filename or ""
        extension = None
        if '.' in filename:
            extension = '.' + filename.rsplit('.', 1)[1].lower()
        
        if extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        content_type = file.content_type
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type: {content_type}"
            )
    
    @beartype
    def _calculate_checksums(self, content: bytes) -> dict[str, Any]:
        """
        Calculate file checksums for integrity and duplicate detection.
        
        Args:
            content: File content bytes
        
        Returns:
            Dictionary with checksums (md5, sha256, simhash)
        """
        return {
            "md5": hashlib.md5(content).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "simhash": self._calculate_simhash(content)
        }
    
    @beartype
    def _calculate_simhash(self, content: bytes) -> str:
        """
        Calculate SimHash for near-duplicate detection.
        
        Simplified implementation using hash of decoded text.
        Real implementation would use proper simhash library.
        
        Args:
            content: File content bytes
        
        Returns:
            64-bit SimHash as hex string
        """
        try:
            text = content.decode('utf-8', errors='ignore')
        except Exception:
            text = str(content)
        
        # Simplified: use hash of text
        hash_value = hash(text) & 0xFFFFFFFFFFFFFFFF
        return f"{hash_value:016x}"
    
    @beartype
    def _build_minio_path(
        self,
        scope: Scope,
        user_id: str,
        file_id: str,
        project_id: Optional[str] = None
    ) -> str:
        """
        Build MinIO base path based on scope.
        
        Args:
            scope: File scope
            user_id: User identifier
            file_id: File identifier
            project_id: Project identifier (required for user_project)
        
        Returns:
            MinIO base path
        
        Raises:
            ValueError: If project_id missing for user_project scope
        """
        if scope == "system":
            return f"system/{file_id}"
        elif scope == "user_global":
            return f"user/{user_id}/global/{file_id}"
        else:  # user_project
            if not project_id:
                raise ValueError("project_id required for user_project scope")
            return f"user/{user_id}/project/{project_id}/{file_id}"
    
    @beartype
    def _initialize_processing_status(self) -> dict[str, Any]:
        """
        Initialize processing status structure for all phases.
        
        Returns:
            Processing status dictionary with all phases
        """
        phases = {}
        for phase in self.PHASES:
            phases[phase] = {
                "status": "pending",
                "active_version": None,
                "available_versions": []
            }
        
        return {
            "global": "pending",
            "phases": phases,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    @beartype
    def _create_metadata_file(
        self,
        base_path: str,
        file_id: str,
        original_name: str,
        size: int,
        content_type: str,
        scope: Scope,
        user_id: str,
        project_id: Optional[str],
        checksums: dict[str, Any]
    ) -> None:
        """
        Create metadata.json file in MinIO.
        
        Args:
            base_path: MinIO base path
            file_id: File identifier
            original_name: Original filename
            size: File size in bytes
            content_type: MIME type
            scope: File scope
            user_id: User identifier
            project_id: Optional project identifier
            checksums: File checksums
        """
        metadata = {
            "file_id": file_id,
            "original_name": original_name,
            "size": size,
            "content_type": content_type,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": user_id,
            "scope": scope,
            "project_id": project_id,
            "checksums": checksums
        }
        
        metadata_path = f"{base_path}/metadata.json"
        metadata_content = json.dumps(metadata, indent=2).encode('utf-8')
        
        self.storage.upload_file(
            bucket=settings.MINIO_DEFAULT_BUCKET,
            file_path=metadata_path,
            file_data=BytesIO(metadata_content),
            content_type="application/json"
        )
    
    @beartype
    def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        user_role: str,
        scope: Scope = "user_global",
        project_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Upload file with contextual scope.
        
        Args:
            file: Uploaded file
            user_id: User identifier
            user_role: User role (for permission check)
            scope: File scope (system/user_global/user_project)
            project_id: Project identifier (required if scope=user_project)
        
        Returns:
            File metadata with processing status and presigned URL
        
        Raises:
            HTTPException 400: Invalid request
            HTTPException 403: Permission denied
            HTTPException 413: File too large
            HTTPException 500: Upload failed
        """
        # Validate permissions
        if scope == "system" and user_role not in ["root", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requires admin or manager role for system uploads"
            )
        
        if scope == "user_project" and not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id required for user_project scope"
            )
        
        # Validate file
        self._validate_file_size(file)
        self._validate_file_type(file)
        
        # Generate file ID and extract extension
        file_id = str(uuid.uuid4())
        original_name = file.filename or "unnamed"
        extension = ""
        if '.' in original_name:
            extension = original_name.rsplit('.', 1)[1].lower()
        
        # Read file content
        content = file.file.read()
        file_size = len(content)
        file.file.seek(0)
        
        # Calculate checksums
        checksums = self._calculate_checksums(content)
        
        # Check for duplicates
        duplicates = self.file_repo.get_by_checksum("sha256", checksums["sha256"])
        if duplicates:
            logger.warning(f"Duplicate file detected: {original_name} (SHA256: {checksums['sha256']})")
        
        # Build MinIO paths
        base_path = self._build_minio_path(scope, user_id, file_id, project_id)
        input_path = f"{base_path}/01-input_data/original.{extension}"
        
        try:
            # Upload file to MinIO
            file_data = BytesIO(content)
            self.storage.upload_file(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=input_path,
                file_data=file_data,
                content_type=file.content_type or "application/octet-stream",
                metadata={"original_name": original_name}
            )
            
            logger.info(f"Uploaded file to MinIO: {input_path}")
            
            # Create metadata.json in MinIO
            self._create_metadata_file(
                base_path=base_path,
                file_id=file_id,
                original_name=original_name,
                size=file_size,
                content_type=file.content_type or "application/octet-stream",
                scope=scope,
                user_id=user_id,
                project_id=project_id,
                checksums=checksums
            )
            
            # Store metadata in ArangoDB
            metadata = {
                "id": file_id,
                "name": original_name,
                "size": file_size,
                "type": file.content_type or "application/octet-stream",
                "minio_path": base_path,
                "scope": scope,
                "project_id": project_id,
                "checksums": checksums,
                "processing_status": self._initialize_processing_status(),
                "active_configuration": {}
            }
            
            file_doc = self.file_repo.create(metadata, user_id)
            
            # Create processing queue entry for first phase
            self.queue_repo.create_phase_queue({
                "file_id": file_id,
                "phase": "02-data_extraction",
                "new_version": "v1_algo-1.0",
                "algorithm_version": "1.0",
                "algorithm_name": "basic_extraction",
                "status": "pending",
                "parameters": {},
                "dependencies": {},
                "metadata": {
                    "user_id": user_id,
                    "project_id": project_id,
                    "file_name": original_name,
                    "file_size": file_size,
                    "minio_base_path": base_path
                }
            })
            
            # Generate presigned URL for download
            url = self.storage.get_presigned_url(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=input_path,
                expiry_seconds=7 * 24 * 3600  # 7 days
            )
            
            return {
                **file_doc,
                "url": url,
                "duplicate_detected": len(duplicates) > 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {str(e)}"
            )
    
    @beartype
    def list_files(
        self,
        user_id: str,
        user_role: str,
        scope: Optional[Scope] = None,
        project_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        List files with access control and filters.
        
        Args:
            user_id: User identifier
            user_role: User role (for system file access)
            scope: Optional scope filter
            project_id: Optional project filter
            search: Optional search term (partial filename match)
        
        Returns:
            List of file metadata sorted alphabetically
        """
        # Get files based on filters
        if scope and project_id:
            files = self.file_repo.get_by_scope(scope, user_id, project_id)
        elif scope:
            files = self.file_repo.get_by_scope(scope, user_id)
        elif project_id:
            files = self.file_repo.get_by_project(project_id)
        else:
            files = self.file_repo.get_by_user(user_id)
        
        # Add system files (accessible to all)
        if not scope or scope == "system":
            system_files = self.file_repo.get_by_scope("system")
            files.extend(system_files)
        
        # Filter by access rights
        accessible_files = []
        for file in files:
            if self._can_access_file(file, user_id, user_role):
                accessible_files.append(file)
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            accessible_files = [
                f for f in accessible_files
                if search_lower in f["name"].lower()
            ]
        
        # Remove duplicates (by id)
        seen = set()
        unique_files = []
        for file in accessible_files:
            if file["id"] not in seen:
                seen.add(file["id"])
                unique_files.append(file)
        
        # Sort alphabetically by name
        unique_files.sort(key=lambda f: f["name"].lower())
        
        # Generate presigned URLs
        for file in unique_files:
            try:
                extension = file["name"].rsplit('.', 1)[1] if '.' in file["name"] else ""
                input_path = f"{file['minio_path']}/01-input_data/original.{extension}"
                url = self.storage.get_presigned_url(
                    bucket=settings.MINIO_DEFAULT_BUCKET,
                    file_path=input_path,
                    expiry_seconds=7 * 24 * 3600
                )
                file["url"] = url
            except Exception as e:
                logger.warning(f"Failed to generate URL for {file['id']}: {e}")
                file["url"] = None
        
        return unique_files
    
    @beartype
    def _can_access_file(
        self,
        file: dict[str, Any],
        user_id: str,
        user_role: str
    ) -> bool:
        """
        Check if user can access file.
        
        Args:
            file: File metadata
            user_id: User identifier
            user_role: User role
        
        Returns:
            True if user can access file
        """
        scope = file.get("scope")
        
        if scope == "system":
            return True
        elif scope == "user_global":
            return file.get("uploaded_by") == user_id
        elif scope == "user_project":
            # TODO: Check project membership via project service
            # For now, allow if user is owner or has project access
            return file.get("uploaded_by") == user_id or user_role in ["root", "manager"]
        
        return False
    
    @beartype
    def download_file(
        self,
        file_id: str,
        user_id: str,
        user_role: str
    ) -> tuple[bytes, str, str]:
        """
        Download file with access control.
        
        Args:
            file_id: File identifier
            user_id: User identifier (for permission check)
            user_role: User role
        
        Returns:
            Tuple of (file_content, filename, content_type)
        
        Raises:
            HTTPException 403: Access denied
            HTTPException 404: File not found
            HTTPException 500: Download failed
        """
        file = self.file_repo.get_by_id(file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        if not self._can_access_file(file, user_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        try:
            extension = file["name"].rsplit('.', 1)[1] if '.' in file["name"] else ""
            input_path = f"{file['minio_path']}/01-input_data/original.{extension}"
            
            content = self.storage.download_file(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=input_path
            )
            
            return (content, file["name"], file["type"])
            
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Download failed: {str(e)}"
            )
    
    @beartype
    def delete_file(
        self,
        file_id: str,
        user_id: str,
        user_role: str
    ) -> bool:
        """
        Delete file and all associated data.
        
        Deletes:
        - File from MinIO (entire directory structure)
        - Metadata from ArangoDB
        - Processing queue entries
        
        Args:
            file_id: File identifier
            user_id: User identifier (for permission check)
            user_role: User role
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException 403: Access denied
            HTTPException 404: File not found
            HTTPException 500: Deletion failed
        """
        file = self.file_repo.get_by_id(file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Check ownership or admin
        if file.get("uploaded_by") != user_id and user_role not in ["root", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not file owner"
            )
        
        try:
            # Delete all files in MinIO directory
            base_path = file["minio_path"]
            # TODO: Implement recursive delete in storage adapter
            # For now, delete known structure
            
            extension = file["name"].rsplit('.', 1)[1] if '.' in file["name"] else ""
            input_path = f"{base_path}/01-input_data/original.{extension}"
            
            try:
                self.storage.delete_file(
                    bucket=settings.MINIO_DEFAULT_BUCKET,
                    file_path=input_path
                )
            except Exception as e:
                logger.warning(f"Failed to delete file from MinIO: {e}")
            
            # Delete metadata.json
            try:
                self.storage.delete_file(
                    bucket=settings.MINIO_DEFAULT_BUCKET,
                    file_path=f"{base_path}/metadata.json"
                )
            except Exception as e:
                logger.warning(f"Failed to delete metadata.json: {e}")
            
            # Delete processing queue entries
            self.queue_repo.delete_by_file(file_id)
            
            # Delete metadata from ArangoDB
            self.file_repo.delete(file_id)
            
            logger.info(f"Deleted file {file_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deletion failed: {str(e)}"
            )
    
    @beartype
    def get_file_info(
        self,
        file_id: str,
        user_id: str,
        user_role: str
    ) -> dict[str, Any]:
        """
        Get file metadata with presigned URL.
        
        Args:
            file_id: File identifier
            user_id: User identifier (for permission check)
            user_role: User role
        
        Returns:
            File metadata with URL
        
        Raises:
            HTTPException 403: Access denied
            HTTPException 404: File not found
        """
        file = self.file_repo.get_by_id(file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        if not self._can_access_file(file, user_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate presigned URL
        try:
            extension = file["name"].rsplit('.', 1)[1] if '.' in file["name"] else ""
            input_path = f"{file['minio_path']}/01-input_data/original.{extension}"
            url = self.storage.get_presigned_url(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=input_path,
                expiry_seconds=7 * 24 * 3600
            )
            file["url"] = url
        except Exception as e:
            logger.warning(f"Failed to generate URL: {e}")
            file["url"] = None
        
        return file