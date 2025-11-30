"""
Path: src/storage/factory.py
Version: 1

Storage factory pattern implementation
Provides single point to get storage instance based on configuration
"""

from typing import Optional
import logging

from src.core.config import settings
from src.storage.interface import IFileStorage
from src.storage.exceptions import StorageException

logger = logging.getLogger(__name__)

# Singleton instance
_storage_instance: Optional[IFileStorage] = None


def get_storage() -> IFileStorage:
    """
    Factory function to get storage instance based on configuration
    
    Returns appropriate storage adapter based on settings.STORAGE_TYPE:
        - "minio": MinIO/S3 adapter
        - "azure": Azure Blob Storage adapter (future)
        - "gcs": Google Cloud Storage adapter (future)
    
    Returns:
        IFileStorage implementation (singleton)
        
    Raises:
        ValueError: If STORAGE_TYPE is not supported
        StorageException: If connection fails
    """
    global _storage_instance
    
    if _storage_instance is None:
        logger.info(f"Initializing storage adapter: {settings.STORAGE_TYPE}")
        
        # Import and instantiate appropriate adapter
        if settings.STORAGE_TYPE == "minio":
            from src.storage.adapters.minio_adapter import MinIOStorageAdapter
            _storage_instance = MinIOStorageAdapter()
            
        elif settings.STORAGE_TYPE == "azure":
            # Future implementation
            try:
                from src.storage.adapters.azure_adapter import AzureBlobAdapter
                _storage_instance = AzureBlobAdapter()
            except ImportError:
                raise StorageException(
                    "Azure Blob adapter not implemented yet. "
                    "Set STORAGE_TYPE=minio in configuration."
                )
            
        elif settings.STORAGE_TYPE == "gcs":
            # Future implementation
            try:
                from src.storage.adapters.gcs_adapter import GCSAdapter
                _storage_instance = GCSAdapter()
            except ImportError:
                raise StorageException(
                    "Google Cloud Storage adapter not implemented yet. "
                    "Set STORAGE_TYPE=minio in configuration."
                )
            
        else:
            raise ValueError(
                f"Unsupported STORAGE_TYPE: {settings.STORAGE_TYPE}. "
                f"Supported types: minio, azure, gcs"
            )
        
        # Establish connection
        try:
            _storage_instance.connect()
            logger.info(f"Storage connection established: {settings.STORAGE_TYPE}")
        except Exception as e:
            logger.error(f"Failed to connect to storage: {e}")
            _storage_instance = None
            raise StorageException(f"Storage connection failed: {str(e)}")
    
    return _storage_instance


def reset_storage() -> None:
    """
    Reset storage singleton instance
    
    Useful for testing or forcing reconnection.
    Closes existing connection and clears singleton.
    """
    global _storage_instance
    
    if _storage_instance is not None:
        try:
            _storage_instance.disconnect()
            logger.info("Storage connection closed")
        except Exception as e:
            logger.warning(f"Error disconnecting storage: {e}")
        finally:
            _storage_instance = None


def get_storage_type() -> str:
    """
    Get configured storage type
    
    Returns:
        Storage type string (minio, azure, gcs)
    """
    return settings.STORAGE_TYPE


def is_connected() -> bool:
    """
    Check if storage is connected
    
    Returns:
        True if storage instance exists and is connected
    """
    return _storage_instance is not None