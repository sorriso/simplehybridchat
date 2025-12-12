"""
Path: backend/tests/unit/services/test_file_service.py
Version: 3

Changes in v3:
- BUGFIX: Mock settings.MINIO_DEFAULT_BUCKET in fixture
- Prevents AttributeError when FileService accesses settings

Changes in v2:
- Fixed: Mock get_storage to prevent real MinIO connection in unit tests
- Added @patch decorator on all test methods

Unit tests for FileService
"""

import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from fastapi import HTTPException, UploadFile

from src.services.file_service import FileService


class TestFileService:
    """Test FileService"""
    
    @pytest.fixture
    def mock_file_repo(self):
        """Mock FileRepository"""
        return MagicMock()
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter"""
        storage = MagicMock()
        storage.bucket_exists.return_value = True
        return storage
    
    @pytest.fixture
    def file_service(self, mock_file_repo, mock_storage):
        """FileService with mocks - patch get_storage and settings before instantiation"""
        with patch('src.services.file_service.get_storage', return_value=mock_storage), \
             patch('src.services.file_service.settings') as mock_settings:
            # Configure mock settings
            mock_settings.MINIO_DEFAULT_BUCKET = "test-bucket"
            
            service = FileService(db=MagicMock())
            service.file_repo = mock_file_repo
            return service
    
    def test_validate_file_size_success(self, file_service):
        """Test file size validation passes for valid size"""
        # Create file under 10MB
        file_data = BytesIO(b"x" * 1024)  # 1KB
        file = UploadFile(filename="test.txt", file=file_data)
        
        # Should not raise
        file_service._validate_file_size(file)
    
    def test_validate_file_size_too_large(self, file_service):
        """Test file size validation fails for too large file"""
        # Create file over 10MB
        file_data = BytesIO(b"x" * (11 * 1024 * 1024))  # 11MB
        file = UploadFile(filename="test.txt", file=file_data)
        
        with pytest.raises(HTTPException) as exc_info:
            file_service._validate_file_size(file)
        
        assert exc_info.value.status_code == 413
    
    def test_validate_file_type_pdf_success(self, file_service):
        """Test PDF file type validation passes"""
        file_data = BytesIO(b"fake pdf content")
        file = UploadFile(
            filename="document.pdf",
            file=file_data,
            headers={"content-type": "application/pdf"}
        )
        
        # Should not raise
        file_service._validate_file_type(file)
    
    def test_validate_file_type_invalid_extension(self, file_service):
        """Test invalid file extension fails validation"""
        file_data = BytesIO(b"content")
        file = UploadFile(
            filename="malware.exe",
            file=file_data,
            headers={"content-type": "application/octet-stream"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            file_service._validate_file_type(file)
        
        assert exc_info.value.status_code == 400
    
    def test_upload_file_success(self, file_service, mock_file_repo, mock_storage):
        """Test successful file upload"""
        # Mock file
        file_data = BytesIO(b"test content")
        file = UploadFile(
            filename="test.pdf",
            file=file_data,
            headers={"content-type": "application/pdf"}
        )
        
        # Mock repository response
        mock_file_repo.create.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "size": 12,
            "type": "application/pdf",
            "minio_path": "uploads/user-1/file-123.pdf",
            "uploaded_by": "user-1"
        }
        
        # Mock storage presigned URL
        mock_storage.get_presigned_url.return_value = "https://minio.example.com/uploads/file-123.pdf?signature=..."
        
        # Upload
        result = file_service.upload_file(file, "user-1")
        
        assert result["id"] == "file-123"
        assert result["name"] == "test.pdf"
        assert "url" in result
        mock_storage.upload_file.assert_called_once()
        mock_file_repo.create.assert_called_once()
    
    def test_upload_file_validation_fails(self, file_service):
        """Test upload fails on validation"""
        # Invalid file type
        file_data = BytesIO(b"content")
        file = UploadFile(
            filename="bad.exe",
            file=file_data,
            headers={"content-type": "application/octet-stream"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.upload_file(file, "user-1")
        
        assert exc_info.value.status_code == 400
    
    def test_list_files(self, file_service, mock_file_repo, mock_storage):
        """Test list user files"""
        # Mock repository response
        mock_file_repo.get_by_user.return_value = [
            {
                "id": "file-1",
                "name": "doc1.pdf",
                "minio_path": "uploads/user-1/file-1.pdf",
                "size": 1024,
                "type": "application/pdf"
            },
            {
                "id": "file-2",
                "name": "doc2.txt",
                "minio_path": "uploads/user-1/file-2.txt",
                "size": 512,
                "type": "text/plain"
            }
        ]
        
        # Mock presigned URLs
        mock_storage.get_presigned_url.return_value = "https://minio.example.com/file"
        
        # List files
        files = file_service.list_files("user-1")
        
        assert len(files) == 2
        assert files[0]["id"] == "file-1"
        assert files[1]["id"] == "file-2"
        assert all("url" in f for f in files)
    
    def test_delete_file_success(self, file_service, mock_file_repo, mock_storage):
        """Test successful file deletion"""
        # Mock repository response
        mock_file_repo.get_by_id.return_value = {
            "id": "file-1",
            "name": "doc.pdf",
            "minio_path": "uploads/user-1/file-1.pdf",
            "uploaded_by": "user-1"
        }
        
        # Delete
        result = file_service.delete_file("file-1", "user-1")
        
        assert result is True
        mock_storage.delete_file.assert_called_once()
        mock_file_repo.delete.assert_called_once_with("file-1")
    
    def test_delete_file_not_found(self, file_service, mock_file_repo):
        """Test delete nonexistent file"""
        mock_file_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.delete_file("nonexistent", "user-1")
        
        assert exc_info.value.status_code == 404
    
    def test_delete_file_not_owner(self, file_service, mock_file_repo):
        """Test delete file by non-owner"""
        # Mock repository response
        mock_file_repo.get_by_id.return_value = {
            "id": "file-1",
            "uploaded_by": "user-2"  # Different user
        }
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.delete_file("file-1", "user-1")
        
        assert exc_info.value.status_code == 403
    
    def test_get_file_info(self, file_service, mock_file_repo, mock_storage):
        """Test get file info"""
        # Mock repository response
        mock_file_repo.get_by_id.return_value = {
            "id": "file-1",
            "name": "doc.pdf",
            "minio_path": "uploads/user-1/file-1.pdf",
            "uploaded_by": "user-1",
            "size": 1024,
            "type": "application/pdf"
        }
        
        # Mock presigned URL
        mock_storage.get_presigned_url.return_value = "https://minio.example.com/file"
        
        # Get info
        info = file_service.get_file_info("file-1", "user-1")
        
        assert info["id"] == "file-1"
        assert "url" in info
    
    def test_get_file_info_not_owner(self, file_service, mock_file_repo):
        """Test get file info by non-owner"""
        mock_file_repo.get_by_id.return_value = {
            "id": "file-1",
            "uploaded_by": "user-2"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.get_file_info("file-1", "user-1")
        
        assert exc_info.value.status_code == 403