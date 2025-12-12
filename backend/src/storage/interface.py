"""
Path: backend/src/storage/interface.py
Version: 1

Abstract storage interface defining contract for all storage adapters
This interface ensures storage implementation can be swapped without changing application code
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime


class IFileStorage(ABC):
    """
    Abstract interface for file storage operations
    
    All storage adapters must implement this interface to ensure
    consistent behavior across different storage technologies.
    
    Implementations:
        - MinIOStorageAdapter: MinIO/S3 object storage
        - AzureBlobAdapter: Azure Blob Storage (future)
        - GCSAdapter: Google Cloud Storage (future)
    """
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish storage connection
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close storage connection
        """
        pass
    
    @abstractmethod
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to storage
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            file_data: File data as binary stream
            content_type: MIME type (e.g., 'image/png', 'application/pdf')
            metadata: Optional metadata dict
            
        Returns:
            Dict with upload info (url, etag, size, etc.)
            
        Raises:
            UploadError: If upload fails
            BucketNotFoundError: If bucket doesn't exist
        """
        pass
    
    @abstractmethod
    def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Download file from storage
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            
        Returns:
            File data as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            DownloadError: If download fails
        """
        pass
    
    @abstractmethod
    def download_file_to_path(
        self,
        bucket: str,
        file_path: str,
        local_path: str
    ) -> None:
        """
        Download file to local filesystem
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            local_path: Local filesystem path to save file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            DownloadError: If download fails
        """
        pass
    
    @abstractmethod
    def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DeleteError: If deletion fails
        """
        pass
    
    @abstractmethod
    def file_exists(self, bucket: str, file_path: str) -> bool:
        """
        Check if file exists
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_info(self, bucket: str, file_path: str) -> Dict[str, Any]:
        """
        Get file metadata
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            
        Returns:
            Dict with file info (size, content_type, etag, last_modified, etc.)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in bucket
        
        Args:
            bucket: Bucket/container name
            prefix: Optional prefix to filter files
            recursive: If True, list all files recursively
            
        Returns:
            List of file info dicts
        """
        pass
    
    @abstractmethod
    def get_presigned_url(
        self,
        bucket: str,
        file_path: str,
        expiry_seconds: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary file access
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            expiry_seconds: URL validity duration in seconds
            
        Returns:
            Presigned URL string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    def bucket_exists(self, bucket: str) -> bool:
        """
        Check if bucket exists
        
        Args:
            bucket: Bucket/container name
            
        Returns:
            True if bucket exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_bucket(self, bucket: str) -> None:
        """
        Create new bucket
        
        Args:
            bucket: Bucket/container name
            
        Raises:
            StorageException: If bucket already exists or creation fails
        """
        pass
    
    @abstractmethod
    def delete_bucket(self, bucket: str, force: bool = False) -> None:
        """
        Delete bucket
        
        Args:
            bucket: Bucket/container name
            force: If True, delete even if bucket contains files
            
        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageException: If bucket not empty and force=False
        """
        pass
    
    @abstractmethod
    def list_buckets(self) -> List[str]:
        """
        List all buckets
        
        Returns:
            List of bucket names
        """
        pass
    
    @abstractmethod
    def copy_file(
        self,
        source_bucket: str,
        source_path: str,
        dest_bucket: str,
        dest_path: str
    ) -> Dict[str, Any]:
        """
        Copy file within storage
        
        Args:
            source_bucket: Source bucket name
            source_path: Source file path
            dest_bucket: Destination bucket name
            dest_path: Destination file path
            
        Returns:
            Dict with copy info
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageException: If copy fails
        """
        pass
    
    @abstractmethod
    def get_file_size(self, bucket: str, file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            bucket: Bucket/container name
            file_path: Path/key for file in storage
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass