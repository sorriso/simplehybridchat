"""
Path: src/storage/exceptions.py
Version: 1

Storage-specific exceptions for file operations
All storage adapters should raise these exceptions for consistent error handling
"""


class StorageException(Exception):
    """
    Base exception for all storage operations
    
    All storage-related errors should inherit from this exception
    to allow catching all storage errors with a single except clause.
    """
    pass


class FileNotFoundError(StorageException):
    """
    File not found in storage
    
    Raised when attempting to access a file that doesn't exist.
    """
    pass


class BucketNotFoundError(StorageException):
    """
    Bucket/container doesn't exist
    
    Raised when attempting to access a non-existent bucket.
    """
    pass


class ConnectionError(StorageException):
    """
    Storage connection error
    
    Raised when unable to establish or maintain connection to storage.
    """
    pass


class UploadError(StorageException):
    """
    File upload error
    
    Raised when file upload fails.
    """
    pass


class DownloadError(StorageException):
    """
    File download error
    
    Raised when file download fails.
    """
    pass


class DeleteError(StorageException):
    """
    File deletion error
    
    Raised when file deletion fails.
    """
    pass


class ValidationError(StorageException):
    """
    File validation error
    
    Raised when file doesn't meet validation requirements (size, type, etc.).
    """
    pass


class PermissionError(StorageException):
    """
    Storage permission error
    
    Raised when storage user doesn't have sufficient privileges.
    """
    pass


class QuotaExceededError(StorageException):
    """
    Storage quota exceeded
    
    Raised when storage quota/limit is exceeded.
    """
    pass


class InvalidFileTypeError(StorageException):
    """
    Invalid file type
    
    Raised when file type is not allowed.
    """
    pass