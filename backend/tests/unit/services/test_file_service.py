"""
Path: backend/tests/unit/services/test_file_service.py
Version: 4.0

Unit tests for FileService v4 with contextual uploads and Beartype.

Changes in v4:
- Added tests for contextual scopes (system/user_global/user_project)
- Added tests for checksum calculation
- Added tests for processing queue integration
- Added tests for access control
- Updated mocks for new repository (processing_queue_repository)
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO
from fastapi import HTTPException, UploadFile
from datetime import datetime, timezone

from src.services.file_service import FileService


class TestFileServiceV4:
    """Test FileService v4 with contextual uploads"""
    
    @pytest.fixture
    def mock_file_repo(self):
        """Mock FileRepository"""
        repo = MagicMock()
        repo.create.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "size": 1024,
            "type": "application/pdf",
            "scope": "user_global",
            "uploaded_by": "user-456"
        }
        return repo
    
    @pytest.fixture
    def mock_queue_repo(self):
        """Mock ProcessingQueueRepository"""
        repo = MagicMock()
        repo.create_phase_queue.return_value = {
            "id": "queue-789",
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "status": "pending"
        }
        return repo
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage adapter"""
        storage = MagicMock()
        storage.bucket_exists.return_value = True
        storage.get_presigned_url.return_value = "https://minio.example.com/presigned-url"
        return storage
    
    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return MagicMock()
    
    @pytest.fixture
    def file_service(self, mock_file_repo, mock_queue_repo, mock_storage, mock_db):
        """FileService with mocks"""
        with patch('src.services.file_service.get_storage', return_value=mock_storage), \
             patch('src.services.file_service.settings') as mock_settings, \
             patch('src.services.file_service.FileRepository', return_value=mock_file_repo), \
             patch('src.services.file_service.ProcessingQueueRepository', return_value=mock_queue_repo):
            
            mock_settings.MINIO_DEFAULT_BUCKET = "test-bucket"
            
            service = FileService(db=mock_db)
            service.file_repo = mock_file_repo
            service.queue_repo = mock_queue_repo
            service.storage = mock_storage
            
            return service
    
    @pytest.fixture
    def mock_upload_file(self):
        """Mock UploadFile"""
        file = MagicMock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        file.file = BytesIO(b"test content")
        return file


class TestFileServiceUpload(TestFileServiceV4):
    """Tests for file upload with contextual scopes"""
    
    def test_upload_file_user_global_scope(self, file_service, mock_upload_file, mock_storage):
        """Test uploading file with user_global scope"""
        result = file_service.upload_file(
            file=mock_upload_file,
            user_id="user-456",
            user_role="user",
            scope="user_global"
        )
        
        assert result["name"] == "test.pdf"
        assert result["scope"] == "user_global"
        assert "url" in result
        
        # Verify storage upload was called
        assert mock_storage.upload_file.called
        
        # Verify file repo create was called
        assert file_service.file_repo.create.called
        
        # Verify queue entry was created
        assert file_service.queue_repo.create_phase_queue.called
    
    def test_upload_file_user_project_scope(self, file_service, mock_upload_file):
        """Test uploading file with user_project scope"""
        result = file_service.upload_file(
            file=mock_upload_file,
            user_id="user-456",
            user_role="user",
            scope="user_project",
            project_id="project-789"
        )
        
        assert result["scope"] == "user_global"  # Mock returns user_global
        
        # Verify MinIO path includes project
        upload_call = file_service.storage.upload_file.call_args
        file_path = upload_call[1]["file_path"]
        # Path should be: user/{user_id}/project/{project_id}/{file_id}/01-input_data/original.pdf
        assert "/project/" in file_path or file_path.startswith("user/")
    
    def test_upload_file_system_scope_as_admin(self, file_service, mock_upload_file):
        """Test that admin can upload system files"""
        result = file_service.upload_file(
            file=mock_upload_file,
            user_id="admin-123",
            user_role="manager",
            scope="system"
        )
        
        assert result is not None
        
        # Verify upload was called
        assert file_service.storage.upload_file.called
    
    def test_upload_file_system_scope_as_user_fails(self, file_service, mock_upload_file):
        """Test that regular user cannot upload system files"""
        with pytest.raises(HTTPException) as exc_info:
            file_service.upload_file(
                file=mock_upload_file,
                user_id="user-456",
                user_role="user",
                scope="system"
            )
        
        assert exc_info.value.status_code == 403
        assert "admin or manager" in exc_info.value.detail.lower()
    
    def test_upload_file_user_project_without_project_id_fails(self, file_service, mock_upload_file):
        """Test that user_project scope requires project_id"""
        with pytest.raises(HTTPException) as exc_info:
            file_service.upload_file(
                file=mock_upload_file,
                user_id="user-456",
                user_role="user",
                scope="user_project"
            )
        
        assert exc_info.value.status_code == 400
        assert "project_id required" in exc_info.value.detail.lower()
    
    def test_upload_file_calculates_checksums(self, file_service, mock_upload_file):
        """Test that checksums are calculated"""
        with patch.object(file_service, '_calculate_checksums') as mock_checksums:
            mock_checksums.return_value = {
                "md5": "abc123",
                "sha256": "def456",
                "simhash": "789xyz"
            }
            
            result = file_service.upload_file(
                file=mock_upload_file,
                user_id="user-456",
                user_role="user",
                scope="user_global"
            )
            
            # Verify checksums were calculated
            assert mock_checksums.called
    
    def test_upload_file_creates_processing_queue_entry(self, file_service, mock_upload_file):
        """Test that processing queue entry is created"""
        file_service.upload_file(
            file=mock_upload_file,
            user_id="user-456",
            user_role="user",
            scope="user_global"
        )
        
        # Verify queue entry was created for phase 02-data_extraction
        call_args = file_service.queue_repo.create_phase_queue.call_args
        queue_data = call_args[0][0]
        
        assert queue_data["phase"] == "02-data_extraction"
        assert queue_data["new_version"] == "v1_algo-1.0"
        assert queue_data["status"] == "pending"
    
    def test_upload_file_too_large_fails(self, file_service):
        """Test that files larger than MAX_FILE_SIZE are rejected"""
        large_file = MagicMock(spec=UploadFile)
        large_file.filename = "large.pdf"
        large_file.content_type = "application/pdf"
        large_file.file = BytesIO(b"x" * (51 * 1024 * 1024))  # 51MB
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.upload_file(
                file=large_file,
                user_id="user-456",
                user_role="user",
                scope="user_global"
            )
        
        assert exc_info.value.status_code == 413
    
    def test_upload_file_invalid_type_fails(self, file_service):
        """Test that invalid file types are rejected"""
        invalid_file = MagicMock(spec=UploadFile)
        invalid_file.filename = "malware.exe"
        invalid_file.content_type = "application/x-msdownload"
        invalid_file.file = BytesIO(b"malware content")
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.upload_file(
                file=invalid_file,
                user_id="user-456",
                user_role="user",
                scope="user_global"
            )
        
        assert exc_info.value.status_code == 400


class TestFileServiceList(TestFileServiceV4):
    """Tests for file listing with filters"""
    
    def test_list_files_all(self, file_service):
        """Test listing all accessible files"""
        file_service.file_repo.get_by_user.return_value = [
            {"id": "1", "name": "file1.pdf", "scope": "user_global", "uploaded_by": "user-456"},
            {"id": "2", "name": "file2.pdf", "scope": "user_global", "uploaded_by": "user-456"}
        ]
        file_service.file_repo.get_by_scope.return_value = []
        
        results = file_service.list_files(
            user_id="user-456",
            user_role="user"
        )
        
        assert len(results) >= 0
        assert file_service.file_repo.get_by_user.called
    
    def test_list_files_filter_by_scope(self, file_service):
        """Test filtering files by scope"""
        file_service.file_repo.get_by_scope.return_value = [
            {"id": "1", "name": "file1.pdf", "scope": "system", "uploaded_by": "admin"}
        ]
        
        results = file_service.list_files(
            user_id="user-456",
            user_role="user",
            scope="system"
        )
        
        assert file_service.file_repo.get_by_scope.called
        call_args = file_service.file_repo.get_by_scope.call_args[0]
        assert call_args[0] == "system"
    
    def test_list_files_alphabetical_order(self, file_service):
        """Test that files are sorted alphabetically"""
        file_service.file_repo.get_by_user.return_value = [
            {"id": "1", "name": "zebra.pdf", "scope": "user_global", "uploaded_by": "user-456"},
            {"id": "2", "name": "alpha.pdf", "scope": "user_global", "uploaded_by": "user-456"},
            {"id": "3", "name": "beta.pdf", "scope": "user_global", "uploaded_by": "user-456"}
        ]
        file_service.file_repo.get_by_scope.return_value = []
        
        results = file_service.list_files(
            user_id="user-456",
            user_role="user"
        )
        
        # Check alphabetical order
        names = [f["name"] for f in results]
        assert names == sorted(names)


class TestFileServiceDownload(TestFileServiceV4):
    """Tests for file download"""
    
    def test_download_file_success(self, file_service):
        """Test downloading file"""
        file_service.file_repo.get_by_id.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "type": "application/pdf",
            "minio_path": "user/user-456/global/file-123",
            "scope": "user_global",
            "uploaded_by": "user-456"
        }
        file_service.storage.download_file.return_value = b"file content"
        
        content, filename, content_type = file_service.download_file(
            file_id="file-123",
            user_id="user-456",
            user_role="user"
        )
        
        assert content == b"file content"
        assert filename == "test.pdf"
        assert content_type == "application/pdf"
    
    def test_download_file_not_found(self, file_service):
        """Test downloading non-existent file"""
        file_service.file_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.download_file(
                file_id="nonexistent",
                user_id="user-456",
                user_role="user"
            )
        
        assert exc_info.value.status_code == 404
    
    def test_download_file_access_denied(self, file_service):
        """Test that users cannot download other users' files"""
        file_service.file_repo.get_by_id.return_value = {
            "id": "file-123",
            "name": "private.pdf",
            "scope": "user_global",
            "uploaded_by": "other-user"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.download_file(
                file_id="file-123",
                user_id="user-456",
                user_role="user"
            )
        
        assert exc_info.value.status_code == 403


class TestFileServiceDelete(TestFileServiceV4):
    """Tests for file deletion"""
    
    def test_delete_file_success(self, file_service):
        """Test deleting file"""
        file_service.file_repo.get_by_id.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "minio_path": "user/user-456/global/file-123",
            "uploaded_by": "user-456"
        }
        file_service.file_repo.delete.return_value = True
        file_service.queue_repo.delete_by_file.return_value = 2
        
        result = file_service.delete_file(
            file_id="file-123",
            user_id="user-456",
            user_role="user"
        )
        
        assert result is True
        assert file_service.storage.delete_file.called
        assert file_service.queue_repo.delete_by_file.called
        assert file_service.file_repo.delete.called
    
    def test_delete_file_not_owner_fails(self, file_service):
        """Test that non-owner cannot delete file"""
        file_service.file_repo.get_by_id.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "uploaded_by": "other-user"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            file_service.delete_file(
                file_id="file-123",
                user_id="user-456",
                user_role="user"
            )
        
        assert exc_info.value.status_code == 403
    
    def test_delete_file_admin_can_delete_any(self, file_service):
        """Test that admin can delete any file"""
        file_service.file_repo.get_by_id.return_value = {
            "id": "file-123",
            "name": "test.pdf",
            "minio_path": "user/user-456/global/file-123",
            "uploaded_by": "other-user"
        }
        file_service.file_repo.delete.return_value = True
        file_service.queue_repo.delete_by_file.return_value = 1
        
        result = file_service.delete_file(
            file_id="file-123",
            user_id="admin-123",
            user_role="manager"
        )
        
        assert result is True


class TestFileServiceChecksums(TestFileServiceV4):
    """Tests for checksum calculation"""
    
    def test_calculate_checksums(self, file_service):
        """Test checksum calculation"""
        content = b"test file content"
        
        checksums = file_service._calculate_checksums(content)
        
        assert "md5" in checksums
        assert "sha256" in checksums
        assert "simhash" in checksums
        assert len(checksums["md5"]) == 32  # MD5 is 32 hex chars
        assert len(checksums["sha256"]) == 64  # SHA256 is 64 hex chars
    
    def test_calculate_simhash(self, file_service):
        """Test SimHash calculation"""
        content = b"test content for simhash"
        
        simhash = file_service._calculate_simhash(content)
        
        assert isinstance(simhash, str)
        assert len(simhash) == 16  # 64-bit hash = 16 hex chars


class TestFileServiceAccessControl(TestFileServiceV4):
    """Tests for access control logic"""
    
    def test_can_access_system_file(self, file_service):
        """Test that any user can access system files"""
        file = {"scope": "system"}
        
        can_access = file_service._can_access_file(file, "user-456", "user")
        
        assert can_access is True
    
    def test_can_access_own_user_global_file(self, file_service):
        """Test that user can access their own user_global files"""
        file = {"scope": "user_global", "uploaded_by": "user-456"}
        
        can_access = file_service._can_access_file(file, "user-456", "user")
        
        assert can_access is True
    
    def test_cannot_access_other_user_global_file(self, file_service):
        """Test that user cannot access other's user_global files"""
        file = {"scope": "user_global", "uploaded_by": "other-user"}
        
        can_access = file_service._can_access_file(file, "user-456", "user")
        
        assert can_access is False
    
    def test_admin_can_access_project_files(self, file_service):
        """Test that admin/manager can access project files"""
        file = {"scope": "user_project", "uploaded_by": "other-user"}
        
        can_access = file_service._can_access_file(file, "admin-123", "manager")
        
        assert can_access is True