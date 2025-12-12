"""
Path: backend/tests/integration/storage/test_storage_integration.py
Version: 1

Integration tests for MinIO storage with testcontainers
"""

import pytest
from io import BytesIO

from src.storage.exceptions import (
    FileNotFoundError,
    BucketNotFoundError,
    StorageException
)


@pytest.mark.integration
class TestStorageIntegrationFunctionScope:
    """
    Integration tests using function-scoped MinIO container
    
    Each test gets a fresh MinIO container for complete isolation.
    Slower but guarantees no side effects between tests.
    """
    
    def test_upload_and_download_file(self, minio_container_function):
        """Test upload and download file"""
        storage = minio_container_function
        
        # Create bucket
        storage.create_bucket('test-bucket')
        
        # Upload file
        file_data = BytesIO(b'Hello, MinIO!')
        result = storage.upload_file(
            'test-bucket',
            'test.txt',
            file_data,
            content_type='text/plain'
        )
        
        assert result['bucket'] == 'test-bucket'
        assert result['path'] == 'test.txt'
        assert result['size'] == 13
        assert 'etag' in result
        
        # Download file
        downloaded = storage.download_file('test-bucket', 'test.txt')
        assert downloaded == b'Hello, MinIO!'
    
    def test_file_exists(self, minio_container_function):
        """Test file existence check"""
        storage = minio_container_function
        
        # Create bucket
        storage.create_bucket('test-bucket')
        
        # File doesn't exist yet
        assert storage.file_exists('test-bucket', 'test.txt') is False
        
        # Upload file
        file_data = BytesIO(b'test')
        storage.upload_file('test-bucket', 'test.txt', file_data)
        
        # Now file exists
        assert storage.file_exists('test-bucket', 'test.txt') is True
    
    def test_get_file_info(self, minio_container_function):
        """Test get file metadata"""
        storage = minio_container_function
        
        # Create bucket and upload file
        storage.create_bucket('test-bucket')
        file_data = BytesIO(b'test data')
        storage.upload_file('test-bucket', 'test.txt', file_data, content_type='text/plain')
        
        # Get file info
        info = storage.get_file_info('test-bucket', 'test.txt')
        
        assert info['bucket'] == 'test-bucket'
        assert info['path'] == 'test.txt'
        assert info['size'] == 9
        assert info['content_type'] == 'text/plain'
        assert 'etag' in info
        assert 'last_modified' in info
    
    def test_delete_file(self, minio_container_function):
        """Test file deletion"""
        storage = minio_container_function
        
        # Create bucket and upload file
        storage.create_bucket('test-bucket')
        file_data = BytesIO(b'test')
        storage.upload_file('test-bucket', 'test.txt', file_data)
        
        # File exists
        assert storage.file_exists('test-bucket', 'test.txt') is True
        
        # Delete file
        deleted = storage.delete_file('test-bucket', 'test.txt')
        assert deleted is True
        
        # File no longer exists
        assert storage.file_exists('test-bucket', 'test.txt') is False
        
        # Delete again returns False
        deleted = storage.delete_file('test-bucket', 'test.txt')
        assert deleted is False
    
    def test_list_files(self, minio_container_function):
        """Test list files in bucket"""
        storage = minio_container_function
        
        # Create bucket and upload files
        storage.create_bucket('test-bucket')
        storage.upload_file('test-bucket', 'file1.txt', BytesIO(b'data1'))
        storage.upload_file('test-bucket', 'file2.txt', BytesIO(b'data2'))
        storage.upload_file('test-bucket', 'dir/file3.txt', BytesIO(b'data3'))
        
        # List all files
        files = storage.list_files('test-bucket', recursive=True)
        assert len(files) == 3
        
        paths = [f['path'] for f in files]
        assert 'file1.txt' in paths
        assert 'file2.txt' in paths
        assert 'dir/file3.txt' in paths
        
        # List with prefix
        files = storage.list_files('test-bucket', prefix='dir/', recursive=True)
        assert len(files) == 1
        assert files[0]['path'] == 'dir/file3.txt'
    
    def test_bucket_operations(self, minio_container_function):
        """Test bucket creation, existence, and deletion"""
        storage = minio_container_function
        
        # Bucket doesn't exist
        assert storage.bucket_exists('new-bucket') is False
        
        # Create bucket
        storage.create_bucket('new-bucket')
        assert storage.bucket_exists('new-bucket') is True
        
        # List buckets
        buckets = storage.list_buckets()
        assert 'new-bucket' in buckets
        
        # Delete empty bucket
        storage.delete_bucket('new-bucket')
        assert storage.bucket_exists('new-bucket') is False
    
    def test_delete_bucket_with_files(self, minio_container_function):
        """Test delete bucket with files (force=True)"""
        storage = minio_container_function
        
        # Create bucket with files
        storage.create_bucket('test-bucket')
        storage.upload_file('test-bucket', 'file1.txt', BytesIO(b'data1'))
        storage.upload_file('test-bucket', 'file2.txt', BytesIO(b'data2'))
        
        # Delete bucket without force should fail
        with pytest.raises(StorageException, match="not empty"):
            storage.delete_bucket('test-bucket', force=False)
        
        # Delete with force=True should succeed
        storage.delete_bucket('test-bucket', force=True)
        assert storage.bucket_exists('test-bucket') is False
    
    def test_copy_file(self, minio_container_function):
        """Test copy file within storage"""
        storage = minio_container_function
        
        # Create bucket and upload file
        storage.create_bucket('test-bucket')
        file_data = BytesIO(b'original data')
        storage.upload_file('test-bucket', 'source.txt', file_data)
        
        # Copy file
        result = storage.copy_file(
            'test-bucket',
            'source.txt',
            'test-bucket',
            'dest.txt'
        )
        
        assert result['source_bucket'] == 'test-bucket'
        assert result['dest_bucket'] == 'test-bucket'
        assert 'etag' in result
        
        # Both files exist
        assert storage.file_exists('test-bucket', 'source.txt') is True
        assert storage.file_exists('test-bucket', 'dest.txt') is True
        
        # Content is same
        source_data = storage.download_file('test-bucket', 'source.txt')
        dest_data = storage.download_file('test-bucket', 'dest.txt')
        assert source_data == dest_data
    
    def test_get_file_size(self, minio_container_function):
        """Test get file size"""
        storage = minio_container_function
        
        # Create bucket and upload file
        storage.create_bucket('test-bucket')
        file_data = BytesIO(b'12345')
        storage.upload_file('test-bucket', 'test.txt', file_data)
        
        # Get file size
        size = storage.get_file_size('test-bucket', 'test.txt')
        assert size == 5
    
    def test_upload_with_metadata(self, minio_container_function):
        """Test upload file with custom metadata"""
        storage = minio_container_function
        
        # Create bucket
        storage.create_bucket('test-bucket')
        
        # Upload with metadata
        file_data = BytesIO(b'test')
        storage.upload_file(
            'test-bucket',
            'test.txt',
            file_data,
            content_type='text/plain',
            metadata={'author': 'test-user', 'version': '1.0'}
        )
        
        # Get file info and check metadata
        info = storage.get_file_info('test-bucket', 'test.txt')
        assert 'metadata' in info
    
    def test_file_not_found_error(self, minio_container_function):
        """Test FileNotFoundError is raised"""
        storage = minio_container_function
        
        # Create bucket
        storage.create_bucket('test-bucket')
        
        # Download non-existent file
        with pytest.raises(FileNotFoundError):
            storage.download_file('test-bucket', 'missing.txt')
        
        # Get info for non-existent file
        with pytest.raises(FileNotFoundError):
            storage.get_file_info('test-bucket', 'missing.txt')
    
    def test_bucket_not_found_error(self, minio_container_function):
        """Test BucketNotFoundError is raised"""
        storage = minio_container_function
        
        # Upload to non-existent bucket
        with pytest.raises(BucketNotFoundError):
            file_data = BytesIO(b'test')
            storage.upload_file('missing-bucket', 'test.txt', file_data)
        
        # Download from non-existent bucket
        with pytest.raises(BucketNotFoundError):
            storage.download_file('missing-bucket', 'test.txt')


@pytest.mark.integration
@pytest.mark.integration_fast
class TestStorageIntegrationModuleScope:
    """
    Integration tests using module-scoped MinIO container
    
    All tests share one MinIO container for speed.
    Tests must clean up their data or use unique bucket names.
    """
    
    def test_upload_file_module_scope(self, minio_container_module):
        """Test upload with shared container"""
        storage = minio_container_module
        
        # Use unique bucket name to avoid conflicts
        bucket = 'test-module-1'
        storage.create_bucket(bucket)
        
        file_data = BytesIO(b'test data')
        result = storage.upload_file(bucket, 'test.txt', file_data)
        
        assert result['bucket'] == bucket
        assert result['size'] == 9
        
        # Cleanup
        storage.delete_bucket(bucket, force=True)
    
    def test_multiple_buckets_module_scope(self, minio_container_module):
        """Test multiple bucket operations with shared container"""
        storage = minio_container_module
        
        # Create multiple buckets
        bucket1 = 'test-module-2'
        bucket2 = 'test-module-3'
        
        storage.create_bucket(bucket1)
        storage.create_bucket(bucket2)
        
        # Upload to different buckets
        storage.upload_file(bucket1, 'file1.txt', BytesIO(b'data1'))
        storage.upload_file(bucket2, 'file2.txt', BytesIO(b'data2'))
        
        # Both files exist
        assert storage.file_exists(bucket1, 'file1.txt') is True
        assert storage.file_exists(bucket2, 'file2.txt') is True
        
        # Cleanup
        storage.delete_bucket(bucket1, force=True)
        storage.delete_bucket(bucket2, force=True)


@pytest.mark.integration
class TestStorageIntegrationCleanFixture:
    """
    Integration tests using clean storage fixture
    
    Storage is cleaned before each test (all buckets deleted).
    Provides fresh state while reusing container for speed.
    """
    
    def test_with_clean_storage(self, clean_storage_module):
        """Test with clean storage state"""
        storage = clean_storage_module
        
        # No buckets should exist
        buckets = storage.list_buckets()
        assert len(buckets) == 0
        
        # Create and use bucket
        storage.create_bucket('clean-test')
        storage.upload_file('clean-test', 'test.txt', BytesIO(b'data'))
        
        assert storage.file_exists('clean-test', 'test.txt') is True
    
    def test_another_with_clean_storage(self, clean_storage_module):
        """Test that previous test's data is cleaned"""
        storage = clean_storage_module
        
        # Storage should be clean again
        buckets = storage.list_buckets()
        assert len(buckets) == 0
        
        # Previous test's bucket shouldn't exist
        assert storage.bucket_exists('clean-test') is False