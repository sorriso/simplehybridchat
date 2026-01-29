"""
Path: backend/tests/unit/storage/test_minio_adapter_extended.py
Version: 1.2

Changes in v1.2:
- FIXED: list_files returns 'path' not 'name'
- FIXED: list_files has recursive=False by default
- FIXED: get_presigned_url uses expiry_seconds not expires
- FIXED: create_bucket_already_exists expects StorageException

Extended tests for MinIOStorageAdapter exception branches.
Coverage target: 67% → 90%
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO
from datetime import datetime, timedelta

from src.storage.adapters.minio_adapter import MinIOStorageAdapter
from src.storage.exceptions import (
    StorageException,
    FileNotFoundError,
    BucketNotFoundError,
    UploadError,
    DownloadError,
    DeleteError,
)


class TestMinIOAdapterConnection:
    """Test connect/disconnect edge cases"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Mock MinIO client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            yield client
    
    @pytest.mark.unit
    def test_connect_success(self, mock_minio_client):
        """Test successful connection"""
        adapter = MinIOStorageAdapter()
        adapter.connect()
        
        assert adapter._connected is True
        assert adapter._client is not None
    
    @pytest.mark.unit
    def test_disconnect_clears_client(self, mock_minio_client):
        """Test disconnect clears client"""
        adapter = MinIOStorageAdapter()
        adapter.connect()
        
        adapter.disconnect()
        
        assert adapter._connected is False
        assert adapter._client is None


class TestMinIOAdapterBucket:
    """Test bucket operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_create_bucket_success(self, adapter):
        """Test successful bucket creation"""
        adapter._client.bucket_exists.return_value = False
        
        adapter.create_bucket('test-bucket')
        
        adapter._client.make_bucket.assert_called_once_with('test-bucket')
    
    @pytest.mark.unit
    def test_create_bucket_already_exists(self, adapter):
        """Test bucket creation when already exists raises StorageException"""
        adapter._client.bucket_exists.return_value = True
        
        with pytest.raises(StorageException, match="already exists"):
            adapter.create_bucket('test-bucket')
    
    @pytest.mark.unit
    def test_bucket_exists_true(self, adapter):
        """Test bucket_exists returns True"""
        adapter._client.bucket_exists.return_value = True
        
        result = adapter.bucket_exists('test-bucket')
        
        assert result is True
    
    @pytest.mark.unit
    def test_bucket_exists_false(self, adapter):
        """Test bucket_exists returns False"""
        adapter._client.bucket_exists.return_value = False
        
        result = adapter.bucket_exists('test-bucket')
        
        assert result is False
    
    @pytest.mark.unit
    def test_delete_bucket_success(self, adapter):
        """Test successful bucket deletion"""
        adapter._client.bucket_exists.return_value = True
        
        adapter.delete_bucket('test-bucket')
        
        adapter._client.remove_bucket.assert_called_once_with('test-bucket')
    
    @pytest.mark.unit
    def test_delete_bucket_not_found(self, adapter):
        """Test delete bucket raises BucketNotFoundError"""
        adapter._client.bucket_exists.return_value = False
        
        with pytest.raises(BucketNotFoundError):
            adapter.delete_bucket('missing-bucket')
    
    @pytest.mark.unit
    def test_list_buckets(self, adapter):
        """Test list all buckets"""
        mock_bucket1 = Mock()
        mock_bucket1.name = 'bucket1'
        mock_bucket2 = Mock()
        mock_bucket2.name = 'bucket2'
        
        adapter._client.list_buckets.return_value = [mock_bucket1, mock_bucket2]
        
        buckets = adapter.list_buckets()
        
        assert buckets == ['bucket1', 'bucket2']


class TestMinIOAdapterUpload:
    """Test upload operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_upload_file_success(self, adapter):
        """Test successful file upload"""
        mock_result = MagicMock()
        mock_result.etag = 'test-etag'
        mock_result.version_id = 'v1'
        adapter._client.put_object.return_value = mock_result
        
        file_data = BytesIO(b'test data')
        result = adapter.upload_file(
            'test-bucket',
            'test.txt',
            file_data,
            content_type='text/plain'
        )
        
        assert result['bucket'] == 'test-bucket'
        assert result['path'] == 'test.txt'
        assert result['etag'] == 'test-etag'
    
    @pytest.mark.unit
    def test_upload_file_bucket_not_exists(self, adapter):
        """Test upload when bucket doesn't exist"""
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
    
    @pytest.mark.unit
    def test_upload_file_generic_error(self, adapter):
        """Test upload with generic error"""
        adapter._client.put_object.side_effect = Exception("Unknown error")
        
        file_data = BytesIO(b'test')
        
        with pytest.raises(UploadError):
            adapter.upload_file('test-bucket', 'test.txt', file_data)


class TestMinIOAdapterDownload:
    """Test download operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_download_file_success(self, adapter):
        """Test successful file download"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'test data'
        adapter._client.get_object.return_value = mock_response
        
        data = adapter.download_file('test-bucket', 'test.txt')
        
        assert data == b'test data'
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()
    
    @pytest.mark.unit
    def test_download_file_not_found(self, adapter):
        """Test download when file doesn't exist"""
        from minio.error import S3Error
        
        adapter._client.get_object.side_effect = S3Error(
            code='NoSuchKey',
            message='Object not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.download_file('test-bucket', 'missing.txt')
    
    @pytest.mark.unit
    def test_download_file_bucket_not_found(self, adapter):
        """Test download when bucket doesn't exist"""
        from minio.error import S3Error
        
        adapter._client.get_object.side_effect = S3Error(
            code='NoSuchBucket',
            message='Bucket not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(BucketNotFoundError):
            adapter.download_file('missing-bucket', 'test.txt')


class TestMinIOAdapterDelete:
    """Test delete operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_delete_file_success(self, adapter):
        """Test successful file deletion"""
        adapter._client.stat_object.return_value = MagicMock()
        
        result = adapter.delete_file('test-bucket', 'test.txt')
        
        assert result is True
        adapter._client.remove_object.assert_called_once_with('test-bucket', 'test.txt')
    
    @pytest.mark.unit
    def test_delete_file_not_found(self, adapter):
        """Test delete when file doesn't exist returns False"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='Object not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        result = adapter.delete_file('test-bucket', 'missing.txt')
        
        assert result is False


class TestMinIOAdapterList:
    """Test list operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_list_files_success(self, adapter):
        """Test successful file listing - returns 'path' key"""
        mock_obj1 = MagicMock()
        mock_obj1.object_name = 'file1.txt'
        mock_obj1.size = 100
        mock_obj1.etag = 'etag1'
        mock_obj1.last_modified = datetime.now()
        mock_obj1.is_dir = False
        
        mock_obj2 = MagicMock()
        mock_obj2.object_name = 'file2.txt'
        mock_obj2.size = 200
        mock_obj2.etag = 'etag2'
        mock_obj2.last_modified = datetime.now()
        mock_obj2.is_dir = False
        
        adapter._client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        result = adapter.list_files('test-bucket')
        
        assert len(result) == 2
        # list_files returns 'path' not 'name'
        assert result[0]['path'] == 'file1.txt'
        assert result[1]['path'] == 'file2.txt'
    
    @pytest.mark.unit
    def test_list_files_with_prefix(self, adapter):
        """Test file listing with prefix - recursive defaults to False"""
        mock_obj = MagicMock()
        mock_obj.object_name = 'folder/file.txt'
        mock_obj.size = 100
        mock_obj.etag = 'etag'
        mock_obj.last_modified = datetime.now()
        mock_obj.is_dir = False
        
        adapter._client.list_objects.return_value = [mock_obj]
        
        result = adapter.list_files('test-bucket', prefix='folder/')
        
        # Default recursive=False
        adapter._client.list_objects.assert_called_once_with(
            'test-bucket',
            prefix='folder/',
            recursive=False
        )
    
    @pytest.mark.unit
    def test_list_files_recursive(self, adapter):
        """Test file listing with recursive=True"""
        mock_obj = MagicMock()
        mock_obj.object_name = 'folder/subfolder/file.txt'
        mock_obj.size = 100
        mock_obj.etag = 'etag'
        mock_obj.last_modified = datetime.now()
        mock_obj.is_dir = False
        
        adapter._client.list_objects.return_value = [mock_obj]
        
        result = adapter.list_files('test-bucket', prefix='folder/', recursive=True)
        
        adapter._client.list_objects.assert_called_once_with(
            'test-bucket',
            prefix='folder/',
            recursive=True
        )
    
    @pytest.mark.unit
    def test_list_files_empty_bucket(self, adapter):
        """Test listing empty bucket"""
        adapter._client.list_objects.return_value = []
        
        result = adapter.list_files('test-bucket')
        
        assert result == []


class TestMinIOAdapterFileInfo:
    """Test file info operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_get_file_info_success(self, adapter):
        """Test successful file info retrieval"""
        mock_stat = MagicMock()
        mock_stat.size = 1024
        mock_stat.content_type = 'text/plain'
        mock_stat.etag = 'test-etag'
        mock_stat.last_modified = datetime.now()
        mock_stat.metadata = {'key': 'value'}
        mock_stat.version_id = 'v1'
        
        adapter._client.stat_object.return_value = mock_stat
        
        result = adapter.get_file_info('test-bucket', 'test.txt')
        
        assert result['size'] == 1024
        assert result['content_type'] == 'text/plain'
        assert result['etag'] == 'test-etag'
    
    @pytest.mark.unit
    def test_get_file_info_not_found(self, adapter):
        """Test file info when file doesn't exist"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='Object not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.get_file_info('test-bucket', 'missing.txt')


class TestMinIOAdapterPresignedUrl:
    """Test presigned URL generation"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_get_presigned_url_success(self, adapter):
        """Test successful presigned URL generation - uses expiry_seconds"""
        adapter._client.stat_object.return_value = MagicMock()
        adapter._client.presigned_get_object.return_value = 'https://minio/test-bucket/test.txt?signature=xxx'
        
        # Correct parameter name is expiry_seconds
        result = adapter.get_presigned_url('test-bucket', 'test.txt', expiry_seconds=3600)
        
        assert 'https://minio' in result
        adapter._client.presigned_get_object.assert_called_once()
    
    @pytest.mark.unit
    def test_get_presigned_url_file_not_found(self, adapter):
        """Test presigned URL when file doesn't exist"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='Object not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.get_presigned_url('test-bucket', 'missing.txt')


class TestMinIOAdapterCopyFile:
    """Test copy file operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock client"""
        with patch('src.storage.adapters.minio_adapter.Minio') as mock:
            client = MagicMock()
            mock.return_value = client
            client.list_buckets.return_value = []
            
            adapter = MinIOStorageAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_copy_file_success(self, adapter):
        """Test successful file copy"""
        adapter._client.stat_object.return_value = MagicMock()
        
        mock_result = MagicMock()
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
    
    @pytest.mark.unit
    def test_copy_file_source_not_found(self, adapter):
        """Test copy when source file doesn't exist"""
        from minio.error import S3Error
        
        adapter._client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='Object not found',
            resource=None,
            request_id=None,
            host_id=None,
            response=None
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.copy_file('bucket', 'missing.txt', 'bucket', 'dest.txt')