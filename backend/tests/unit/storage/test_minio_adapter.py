"""
Path: tests/unit/storage/test_minio_adapter.py
Version: 1

Unit tests for MinIO storage adapter with mocking
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO
from datetime import datetime

from src.storage.adapters.minio_adapter import MinIOStorageAdapter
from src.storage.exceptions import (
    ConnectionError,
    FileNotFoundError,
    BucketNotFoundError,
    UploadError,
    DownloadError,
    DeleteError,
    StorageException
)


class TestMinIOAdapter:
    """Unit tests for MinIO adapter with mocked client"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Mock MinIO client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            
            # Mock list_buckets for connection test
            client.list_buckets.return_value = []
            
            yield client
    
    @pytest.fixture
    def adapter(self, mock_minio_client):
        """Create adapter with mocked client"""
        adapter = MinIOStorageAdapter()
        adapter.connect()
        return adapter
    
    # Connection Tests
    
    def test_connect_success(self, mock_minio_client):
        """Test successful connection"""
        adapter = MinIOStorageAdapter()
        adapter.connect()
        
        assert adapter._connected is True
        assert adapter._client is not None
        mock_minio_client.list_buckets.assert_called_once()
    
    def test_connect_failure(self, mock_minio_client):
        """Test connection failure"""
        from minio.error import S3Error
        
        mock_minio_client.list_buckets.side_effect = S3Error(
            code='ConnectionError',
            message='Connection failed',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        adapter = MinIOStorageAdapter()
        with pytest.raises(ConnectionError):
            adapter.connect()
    
    def test_disconnect(self, adapter):
        """Test disconnect"""
        adapter.disconnect()
        assert adapter._connected is False
        assert adapter._client is None
    
    # Upload Tests
    
    def test_upload_file_success(self, adapter):
        """Test successful file upload"""
        mock_result = Mock()
        mock_result.etag = 'test-etag'
        mock_result.version_id = 'v1'
        
        adapter._client.put_object.return_value = mock_result
        
        file_data = BytesIO(b'test data')
        result = adapter.upload_file(
            'test-bucket',
            'test.txt',
            file_data,
            content_type='text/plain',
            metadata={'key': 'value'}
        )
        
        assert result['bucket'] == 'test-bucket'
        assert result['path'] == 'test.txt'
        assert result['etag'] == 'test-etag'
        assert result['size'] == 9
        
        adapter._client.put_object.assert_called_once()
    
    def test_upload_file_bucket_not_found(self, adapter):
        """Test upload to non-existent bucket"""
        from minio.error import S3Error
        
        adapter._client.put_object.side_effect = S3Error(
            code='NoSuchBucket',
            message='Bucket not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        file_data = BytesIO(b'test')
        with pytest.raises(BucketNotFoundError):
            adapter.upload_file('missing-bucket', 'test.txt', file_data)
    
    # Download Tests
    
    def test_download_file_success(self, adapter):
        """Test successful file download"""
        mock_response = Mock()
        mock_response.read.return_value = b'test data'
        mock_response.close = Mock()
        mock_response.release_conn = Mock()
        
        adapter._client.get_object.return_value = mock_response
        
        data = adapter.download_file('test-bucket', 'test.txt')
        
        assert data == b'test data'
        adapter._client.get_object.assert_called_once_with('test-bucket', 'test.txt')
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()
    
    def test_download_file_not_found(self, adapter):
        """Test download non-existent file"""
        from minio.error import S3Error
        
        adapter._client.get_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.download_file('test-bucket', 'missing.txt')
    
    def test_download_file_to_path_success(self, adapter):
        """Test download file to path"""
        adapter._client.fget_object.return_value = None
        
        adapter.download_file_to_path('test-bucket', 'test.txt', '/tmp/test.txt')
        
        adapter._client.fget_object.assert_called_once_with(
            'test-bucket',
            'test.txt',
            '/tmp/test.txt'
        )
    
    # Delete Tests
    
    def test_delete_file_success(self, adapter):
        """Test successful file deletion"""
        # Mock file exists
        adapter._client.stat_object.return_value = Mock()
        adapter._client.remove_object.return_value = None
        
        result = adapter.delete_file('test-bucket', 'test.txt')
        
        assert result is True
        adapter._client.remove_object.assert_called_once_with('test-bucket', 'test.txt')
    
    def test_delete_file_not_found(self, adapter):
        """Test delete non-existent file"""
        from minio.error import S3Error
        
        # Mock file doesn't exist
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        result = adapter.delete_file('test-bucket', 'missing.txt')
        assert result is False
    
    # File Info Tests
    
    def test_file_exists_true(self, adapter):
        """Test file exists check (exists)"""
        adapter._client.stat_object.return_value = Mock()
        
        exists = adapter.file_exists('test-bucket', 'test.txt')
        assert exists is True
    
    def test_file_exists_false(self, adapter):
        """Test file exists check (not exists)"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        exists = adapter.file_exists('test-bucket', 'missing.txt')
        assert exists is False
    
    def test_get_file_info_success(self, adapter):
        """Test get file metadata"""
        mock_stat = Mock()
        mock_stat.size = 1024
        mock_stat.content_type = 'text/plain'
        mock_stat.etag = 'test-etag'
        mock_stat.last_modified = datetime(2024, 1, 1)
        mock_stat.metadata = {'key': 'value'}
        mock_stat.version_id = 'v1'
        
        adapter._client.stat_object.return_value = mock_stat
        
        info = adapter.get_file_info('test-bucket', 'test.txt')
        
        assert info['size'] == 1024
        assert info['content_type'] == 'text/plain'
        assert info['etag'] == 'test-etag'
        assert info['bucket'] == 'test-bucket'
        assert info['path'] == 'test.txt'
    
    def test_get_file_info_not_found(self, adapter):
        """Test get info for non-existent file"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.get_file_info('test-bucket', 'missing.txt')
    
    # List Files Tests
    
    def test_list_files_success(self, adapter):
        """Test list files in bucket"""
        mock_obj1 = Mock()
        mock_obj1.object_name = 'file1.txt'
        mock_obj1.size = 100
        mock_obj1.etag = 'etag1'
        mock_obj1.last_modified = datetime(2024, 1, 1)
        mock_obj1.is_dir = False
        
        mock_obj2 = Mock()
        mock_obj2.object_name = 'file2.txt'
        mock_obj2.size = 200
        mock_obj2.etag = 'etag2'
        mock_obj2.last_modified = datetime(2024, 1, 2)
        mock_obj2.is_dir = False
        
        adapter._client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        files = adapter.list_files('test-bucket', prefix='file', recursive=True)
        
        assert len(files) == 2
        assert files[0]['path'] == 'file1.txt'
        assert files[1]['path'] == 'file2.txt'
        
        adapter._client.list_objects.assert_called_once_with(
            'test-bucket',
            prefix='file',
            recursive=True
        )
    
    # Bucket Tests
    
    def test_bucket_exists_true(self, adapter):
        """Test bucket exists check (exists)"""
        adapter._client.bucket_exists.return_value = True
        
        exists = adapter.bucket_exists('test-bucket')
        assert exists is True
    
    def test_bucket_exists_false(self, adapter):
        """Test bucket exists check (not exists)"""
        adapter._client.bucket_exists.return_value = False
        
        exists = adapter.bucket_exists('missing-bucket')
        assert exists is False
    
    def test_create_bucket_success(self, adapter):
        """Test create bucket"""
        adapter._client.bucket_exists.return_value = False
        adapter._client.make_bucket.return_value = None
        
        adapter.create_bucket('new-bucket')
        
        adapter._client.make_bucket.assert_called_once_with('new-bucket')
    
    def test_create_bucket_already_exists(self, adapter):
        """Test create bucket that already exists"""
        adapter._client.bucket_exists.return_value = True
        
        with pytest.raises(StorageException, match="already exists"):
            adapter.create_bucket('existing-bucket')
    
    def test_delete_bucket_success(self, adapter):
        """Test delete bucket"""
        adapter._client.bucket_exists.return_value = True
        adapter._client.remove_bucket.return_value = None
        
        adapter.delete_bucket('test-bucket')
        
        adapter._client.remove_bucket.assert_called_once_with('test-bucket')
    
    def test_delete_bucket_not_found(self, adapter):
        """Test delete non-existent bucket"""
        adapter._client.bucket_exists.return_value = False
        
        with pytest.raises(BucketNotFoundError):
            adapter.delete_bucket('missing-bucket')
    
    def test_list_buckets(self, adapter):
        """Test list all buckets"""
        mock_bucket1 = Mock()
        mock_bucket1.name = 'bucket1'
        
        mock_bucket2 = Mock()
        mock_bucket2.name = 'bucket2'
        
        adapter._client.list_buckets.return_value = [mock_bucket1, mock_bucket2]
        
        buckets = adapter.list_buckets()
        
        assert buckets == ['bucket1', 'bucket2']
    
    # Presigned URL Tests
    
    def test_get_presigned_url_success(self, adapter):
        """Test generate presigned URL"""
        adapter._client.stat_object.return_value = Mock()
        adapter._client.presigned_get_object.return_value = 'https://test-url'
        
        url = adapter.get_presigned_url('test-bucket', 'test.txt', expiry_seconds=3600)
        
        assert url == 'https://test-url'
    
    def test_get_presigned_url_file_not_found(self, adapter):
        """Test presigned URL for non-existent file"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.get_presigned_url('test-bucket', 'missing.txt')
    
    # Copy File Tests
    
    def test_copy_file_success(self, adapter):
        """Test copy file"""
        # Mock source exists
        adapter._client.stat_object.return_value = Mock()
        
        mock_result = Mock()
        mock_result.etag = 'copy-etag'
        mock_result.version_id = 'v2'
        adapter._client.copy_object.return_value = mock_result
        
        result = adapter.copy_file(
            'source-bucket',
            'source.txt',
            'dest-bucket',
            'dest.txt'
        )
        
        assert result['source_bucket'] == 'source-bucket'
        assert result['dest_bucket'] == 'dest-bucket'
        assert result['etag'] == 'copy-etag'
    
    def test_copy_file_source_not_found(self, adapter):
        """Test copy non-existent file"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='File not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.copy_file('bucket', 'missing.txt', 'bucket', 'dest.txt')
    
    # File Size Tests
    
    def test_get_file_size(self, adapter):
        """Test get file size"""
        mock_stat = Mock()
        mock_stat.size = 2048
        mock_stat.content_type = 'text/plain'
        mock_stat.etag = 'test-etag'
        mock_stat.last_modified = datetime(2024, 1, 1)
        mock_stat.metadata = {}
        mock_stat.version_id = 'v1'
        
        adapter._client.stat_object.return_value = mock_stat
        
        size = adapter.get_file_size('test-bucket', 'test.txt')
        assert size == 2048