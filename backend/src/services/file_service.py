"""
Path: backend/src/services/file_service.py
Version: 3

Changes in v3:
- BUGFIX: Use expiry_seconds instead of expires in get_presigned_url() calls
- Parameter name in MinIOStorageAdapter is expiry_seconds, not expires
- Fixed 5 occurrences (upload_file x2, list_files, get_file_info)

Changes in v2:
- BUGFIX: Use settings.MINIO_DEFAULT_BUCKET instead of MINIO_BUCKET
- Variable name in config.py is MINIO_DEFAULT_BUCKET

Service for file upload/management with MinIO integration
"""

import logging
import uuid
from typing import List, Dict, Any
from io import BytesIO
from fastapi import HTTPException, status, UploadFile

from src.repositories.file_repository import FileRepository
from src.storage.factory import get_storage
from src.core.config import settings
from src.database.interface import IDatabase

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for file operations
    
    Handles:
    - File validation (size, type)
    - Upload to MinIO
    - Metadata storage in ArangoDB
    - Presigned URL generation
    - File deletion (MinIO + metadata)
    """
    
    # File validation constraints
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        # Documents
        '.pdf', '.txt', '.csv', '.json', '.md',
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.webp'
    }
    ALLOWED_CONTENT_TYPES = {
        # Documents
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json',
        'text/markdown',
        # Images
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/webp'
    }
    
    def __init__(self, db: IDatabase = None):
        """Initialize service with repositories"""
        self.file_repo = FileRepository(db=db)
        self.storage = get_storage()
        
        # Ensure bucket exists
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.warning(f"Could not ensure bucket: {e}")
    
    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            if not self.storage.bucket_exists(settings.MINIO_DEFAULT_BUCKET):
                self.storage.create_bucket(settings.MINIO_DEFAULT_BUCKET)
                logger.info(f"Created MinIO bucket: {settings.MINIO_DEFAULT_BUCKET}")
        except Exception as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def _validate_file_size(self, file: UploadFile) -> None:
        """
        Validate file size
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException 413: File too large
        """
        # Read file to get size
        contents = file.file.read()
        file_size = len(contents)
        
        # Reset file pointer
        file.file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
    
    def _validate_file_type(self, file: UploadFile) -> None:
        """
        Validate file type
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException 400: Invalid file type
        """
        # Check extension
        filename = file.filename or ""
        extension = None
        if '.' in filename:
            extension = '.' + filename.rsplit('.', 1)[1].lower()
        
        # Check content type
        content_type = file.content_type
        
        # Validate
        if extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type: {content_type}"
            )
    
    def upload_file(
        self,
        file: UploadFile,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Upload file to MinIO and store metadata
        
        Steps:
        1. Validate file size
        2. Validate file type
        3. Generate unique filename
        4. Upload to MinIO
        5. Store metadata in ArangoDB
        6. Return file info with presigned URL
        
        Args:
            file: Uploaded file
            user_id: User ID
            
        Returns:
            File metadata with presigned URL
            
        Raises:
            HTTPException 400: Invalid file type
            HTTPException 413: File too large
            HTTPException 500: Upload failed
        """
        # Validate
        self._validate_file_size(file)
        self._validate_file_type(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_name = file.filename or "unnamed"
        extension = ""
        if '.' in original_name:
            extension = '.' + original_name.rsplit('.', 1)[1].lower()
        
        minio_path = f"uploads/{user_id}/{file_id}{extension}"
        
        try:
            # Read file contents
            contents = file.file.read()
            file_size = len(contents)
            file.file.seek(0)
            
            # Upload to MinIO
            file_data = BytesIO(contents)
            
            self.storage.upload_file(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=minio_path,
                file_data=file_data,
                content_type=file.content_type,
                metadata={
                    "original_name": original_name,
                    "uploaded_by": user_id
                }
            )
            
            logger.info(f"Uploaded file to MinIO: {minio_path}")
            
            # Store metadata in ArangoDB
            metadata = {
                "name": original_name,
                "size": file_size,
                "type": file.content_type or "application/octet-stream",
                "minio_path": minio_path
            }
            
            file_doc = self.file_repo.create(metadata, user_id)
            
            # Generate presigned URL (7 days expiration)
            url = self.storage.get_presigned_url(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=minio_path,
                expiry_seconds=7 * 24 * 3600  # 7 days in seconds
            )
            
            return {
                **file_doc,
                "url": url
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )
    
    def list_files(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List user's files with presigned URLs
        
        Args:
            user_id: User ID
            
        Returns:
            List of file metadata with presigned URLs
        """
        files = self.file_repo.get_by_user(user_id)
        
        # Generate presigned URLs
        for file in files:
            try:
                url = self.storage.get_presigned_url(
                    bucket=settings.MINIO_DEFAULT_BUCKET,
                    file_path=file["minio_path"],
                    expiry_seconds=7 * 24 * 3600  # 7 days
                )
                file["url"] = url
            except Exception as e:
                logger.warning(f"Failed to generate URL for {file['id']}: {e}")
                file["url"] = None
        
        return files
    
    def delete_file(
        self,
        file_id: str,
        user_id: str
    ) -> bool:
        """
        Delete file from MinIO and metadata
        
        Verifies ownership before deletion.
        
        Args:
            file_id: File ID
            user_id: User ID (for ownership check)
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException 404: File not found
            HTTPException 403: Not file owner
            HTTPException 500: Deletion failed
        """
        # Get file metadata
        file = self.file_repo.get_by_id(file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Check ownership
        if file["uploaded_by"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not file owner"
            )
        
        try:
            # Delete from MinIO
            self.storage.delete_file(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=file["minio_path"]
            )
            
            logger.info(f"Deleted file from MinIO: {file['minio_path']}")
            
            # Delete metadata
            self.file_repo.delete(file_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File deletion failed: {str(e)}"
            )
    
    def get_file_info(
        self,
        file_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get file metadata with presigned URL
        
        Args:
            file_id: File ID
            user_id: User ID (for ownership check)
            
        Returns:
            File metadata with URL
            
        Raises:
            HTTPException 404: File not found
            HTTPException 403: Not file owner
        """
        file = self.file_repo.get_by_id(file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Check ownership
        if file["uploaded_by"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not file owner"
            )
        
        # Generate presigned URL
        try:
            url = self.storage.get_presigned_url(
                bucket=settings.MINIO_DEFAULT_BUCKET,
                file_path=file["minio_path"],
                expiry_seconds=7 * 24 * 3600
            )
            file["url"] = url
        except Exception as e:
            logger.warning(f"Failed to generate URL: {e}")
            file["url"] = None
        
        return file