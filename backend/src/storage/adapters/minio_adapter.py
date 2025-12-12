"""
Path: backend/src/storage/adapters/minio_adapter.py
Version: 2

MinIO/S3-compatible storage adapter implementation
"""

import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

from src.core.config import settings
from src.storage.interface import IFileStorage
from src.storage.exceptions import (
    StorageException,
    FileNotFoundError,
    BucketNotFoundError,
    ConnectionError,
    UploadError,
    DownloadError,
    DeleteError,
)

logger = logging.getLogger(__name__)


class MinIOStorageAdapter(IFileStorage):
    """
    MinIO/S3-compatible storage adapter
    
    Implements IFileStorage interface using MinIO client.
    Compatible with MinIO, AWS S3, and other S3-compatible services.
    """
    
    def __init__(self):
        """Initialize MinIO adapter"""
        self._client: Optional[Minio] = None
        self._connected = False
    
    def connect(self) -> None:
        """
        Establish connection to MinIO
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._client = Minio(
                endpoint=f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Test connection by listing buckets
            list(self._client.list_buckets())
            
            self._connected = True
            logger.info(
                f"Connected to MinIO: {settings.MINIO_HOST}:{settings.MINIO_PORT}"
            )
            
        except (S3Error, MaxRetryError) as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            raise ConnectionError(f"MinIO connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MinIO: {e}")
            raise ConnectionError(f"MinIO connection failed: {str(e)}")
    
    def disconnect(self) -> None:
        """Close MinIO connection"""
        if self._client:
            self._client = None
            self._connected = False
            logger.info("MinIO connection closed")
    
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload file to MinIO"""
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning
            
            # Upload
            result = self._client.put_object(
                bucket_name=bucket,
                object_name=file_path,
                data=file_data,
                length=file_size,
                content_type=content_type or 'application/octet-stream',
                metadata=metadata
            )
            
            logger.info(f"Uploaded file: {bucket}/{file_path} ({file_size} bytes)")
            
            return {
                'bucket': bucket,
                'path': file_path,
                'etag': result.etag,
                'size': file_size,
                'version_id': result.version_id
            }
            
        except S3Error as e:
            if e.code == 'NoSuchBucket':
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            logger.error(f"Upload failed: {e}")
            raise UploadError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise UploadError(f"Failed to upload file: {str(e)}")
    
    def download_file(self, bucket: str, file_path: str) -> bytes:
        """Download file from MinIO"""
        try:
            response = self._client.get_object(bucket, file_path)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {bucket}/{file_path} ({len(data)} bytes)")
            return data
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {bucket}/{file_path}")
            if e.code == 'NoSuchBucket':
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            logger.error(f"Download failed: {e}")
            raise DownloadError(f"Failed to download file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise DownloadError(f"Failed to download file: {str(e)}")
    
    def download_file_to_path(
        self,
        bucket: str,
        file_path: str,
        local_path: str
    ) -> None:
        """Download file to local filesystem"""
        try:
            self._client.fget_object(bucket, file_path, local_path)
            logger.info(f"Downloaded file to: {local_path}")
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {bucket}/{file_path}")
            if e.code == 'NoSuchBucket':
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            logger.error(f"Download to path failed: {e}")
            raise DownloadError(f"Failed to download file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise DownloadError(f"Failed to download file: {str(e)}")
    
    def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file from MinIO"""
        try:
            # Check if file exists first
            if not self.file_exists(bucket, file_path):
                return False
            
            self._client.remove_object(bucket, file_path)
            logger.info(f"Deleted file: {bucket}/{file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Delete failed: {e}")
            raise DeleteError(f"Failed to delete file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected delete error: {e}")
            raise DeleteError(f"Failed to delete file: {str(e)}")
    
    def file_exists(self, bucket: str, file_path: str) -> bool:
        """Check if file exists"""
        try:
            self._client.stat_object(bucket, file_path)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey' or e.code == 'NoSuchBucket':
                return False
            raise
        except Exception:
            return False
    
    def get_file_info(self, bucket: str, file_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            stat = self._client.stat_object(bucket, file_path)
            
            return {
                'bucket': bucket,
                'path': file_path,
                'size': stat.size,
                'content_type': stat.content_type,
                'etag': stat.etag,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata,
                'version_id': stat.version_id
            }
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {bucket}/{file_path}")
            if e.code == 'NoSuchBucket':
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            raise StorageException(f"Failed to get file info: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to get file info: {str(e)}")
    
    def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """List files in bucket"""
        try:
            objects = self._client.list_objects(
                bucket,
                prefix=prefix,
                recursive=recursive
            )
            
            files = []
            for obj in objects:
                files.append({
                    'path': obj.object_name,
                    'size': obj.size,
                    'etag': obj.etag,
                    'last_modified': obj.last_modified,
                    'is_dir': obj.is_dir
                })
            
            return files
            
        except S3Error as e:
            if e.code == 'NoSuchBucket':
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            raise StorageException(f"Failed to list files: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to list files: {str(e)}")
    
    def get_presigned_url(
        self,
        bucket: str,
        file_path: str,
        expiry_seconds: int = 3600
    ) -> str:
        """Generate presigned URL"""
        try:
            # Check if file exists
            if not self.file_exists(bucket, file_path):
                raise FileNotFoundError(f"File not found: {bucket}/{file_path}")
            
            url = self._client.presigned_get_object(
                bucket,
                file_path,
                expires=timedelta(seconds=expiry_seconds)
            )
            
            return url
            
        except FileNotFoundError:
            raise
        except S3Error as e:
            raise StorageException(f"Failed to generate presigned URL: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to generate presigned URL: {str(e)}")
    
    def bucket_exists(self, bucket: str) -> bool:
        """Check if bucket exists"""
        try:
            return self._client.bucket_exists(bucket)
        except Exception as e:
            logger.error(f"Error checking bucket existence: {e}")
            return False
    
    def create_bucket(self, bucket: str) -> None:
        """Create new bucket"""
        try:
            if self.bucket_exists(bucket):
                raise StorageException(f"Bucket already exists: {bucket}")
            
            self._client.make_bucket(bucket)
            logger.info(f"Created bucket: {bucket}")
            
        except StorageException:
            raise
        except S3Error as e:
            raise StorageException(f"Failed to create bucket: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to create bucket: {str(e)}")
    
    def delete_bucket(self, bucket: str, force: bool = False) -> None:
        """Delete bucket"""
        try:
            if not self.bucket_exists(bucket):
                raise BucketNotFoundError(f"Bucket not found: {bucket}")
            
            # If force, delete all objects first
            if force:
                objects = self.list_files(bucket, recursive=True)
                for obj in objects:
                    self.delete_file(bucket, obj['path'])
            
            self._client.remove_bucket(bucket)
            logger.info(f"Deleted bucket: {bucket}")
            
        except BucketNotFoundError:
            raise
        except S3Error as e:
            if e.code == 'BucketNotEmpty':
                raise StorageException(
                    f"Bucket not empty: {bucket}. Use force=True to delete anyway."
                )
            raise StorageException(f"Failed to delete bucket: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to delete bucket: {str(e)}")
    
    def list_buckets(self) -> List[str]:
        """List all buckets"""
        try:
            buckets = self._client.list_buckets()
            return [bucket.name for bucket in buckets]
        except Exception as e:
            raise StorageException(f"Failed to list buckets: {str(e)}")
    
    def copy_file(
        self,
        source_bucket: str,
        source_path: str,
        dest_bucket: str,
        dest_path: str
    ) -> Dict[str, Any]:
        """Copy file within storage"""
        try:
            # Check source exists
            if not self.file_exists(source_bucket, source_path):
                raise FileNotFoundError(
                    f"Source file not found: {source_bucket}/{source_path}"
                )
            
            # Try CopySource from commonconfig (minio >= 7.1.0)
            try:
                from minio.commonconfig import CopySource
                copy_source = CopySource(source_bucket, source_path)
            except ImportError:
                # Fallback: use string format for older versions
                copy_source = f"{source_bucket}/{source_path}"
            
            result = self._client.copy_object(
                dest_bucket,
                dest_path,
                copy_source
            )
            
            logger.info(
                f"Copied file: {source_bucket}/{source_path} -> "
                f"{dest_bucket}/{dest_path}"
            )
            
            return {
                'source_bucket': source_bucket,
                'source_path': source_path,
                'dest_bucket': dest_bucket,
                'dest_path': dest_path,
                'etag': result.etag,
                'version_id': result.version_id
            }
            
        except FileNotFoundError:
            raise
        except S3Error as e:
            raise StorageException(f"Failed to copy file: {str(e)}")
        except Exception as e:
            raise StorageException(f"Failed to copy file: {str(e)}")
    
    def get_file_size(self, bucket: str, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            info = self.get_file_info(bucket, file_path)
            return info['size']
        except Exception:
            raise