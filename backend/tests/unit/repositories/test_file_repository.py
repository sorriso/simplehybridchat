"""
Path: backend/tests/unit/repositories/test_file_repository.py
Version: 1.1

Changes in v1.1:
- FIX: test_init_without_db_uses_factory now patches 'src.database.factory.get_database'
- get_database is imported inside __init__, not at module level

Unit tests for FileRepository with contextual scopes and versioning.

Tests cover:
- CRUD operations (create, get_by_id, update, delete)
- Scoped queries (get_by_user, get_by_scope, get_by_project)
- Search functionality (search_by_name)
- Processing status management (update_processing_status, set_active_version)
- File promotion (mark_promoted)
- Checksum queries (get_by_checksum, get_by_minio_path)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.repositories.file_repository import FileRepository
from src.database.exceptions import NotFoundError
from tests.unit.mocks.mock_database import MockDatabase


class TestFileRepositoryCreate:
    """Test FileRepository create operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.fixture
    def sample_file_data(self):
        """Sample file metadata"""
        return {
            "name": "document.pdf",
            "size": 1024000,
            "type": "application/pdf",
            "minio_path": "user_global/user-123/document.pdf",
            "scope": "user_global",
            "checksums": {
                "md5": "abc123def456",
                "sha256": "sha256hash123",
                "simhash": "simhash456"
            },
            "processing_status": {
                "global": "pending",
                "phases": {}
            }
        }
    
    @pytest.mark.unit
    def test_create_file_with_user(self, file_repo, sample_file_data):
        """Test creating file with user ID"""
        file = file_repo.create(sample_file_data, user_id="user-123")
        
        assert file["name"] == "document.pdf"
        assert file["size"] == 1024000
        assert file["scope"] == "user_global"
        assert file["uploaded_by"] == "user-123"
        assert "uploaded_at" in file
        assert file["promoted"] is False
        assert file["promoted_at"] is None
        assert "id" in file
    
    @pytest.mark.unit
    def test_create_file_without_user(self, file_repo, sample_file_data):
        """Test creating system file without user ID"""
        sample_file_data["scope"] = "system"
        file = file_repo.create(sample_file_data)
        
        assert file["scope"] == "system"
        assert file["uploaded_by"] is None
        assert "id" in file
    
    @pytest.mark.unit
    def test_create_file_with_project(self, file_repo, sample_file_data):
        """Test creating project-scoped file"""
        sample_file_data["scope"] = "user_project"
        sample_file_data["project_id"] = "project-456"
        
        file = file_repo.create(sample_file_data, user_id="user-123")
        
        assert file["scope"] == "user_project"
        assert file["project_id"] == "project-456"
        assert file["uploaded_by"] == "user-123"


class TestFileRepositoryRead:
    """Test FileRepository read operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.fixture
    def populated_db(self, file_repo):
        """Populate database with test files"""
        files = [
            {
                "name": "report.pdf",
                "size": 1000,
                "type": "application/pdf",
                "scope": "user_global",
                "minio_path": "user_global/user-1/report.pdf",
                "checksums": {"md5": "md5-1", "sha256": "sha256-1"}
            },
            {
                "name": "data.csv",
                "size": 500,
                "type": "text/csv",
                "scope": "user_global",
                "minio_path": "user_global/user-1/data.csv",
                "checksums": {"md5": "md5-2", "sha256": "sha256-2"}
            },
            {
                "name": "project_doc.pdf",
                "size": 2000,
                "type": "application/pdf",
                "scope": "user_project",
                "project_id": "project-1",
                "minio_path": "user_project/user-2/project-1/doc.pdf",
                "checksums": {"md5": "md5-3", "sha256": "sha256-3"}
            },
            {
                "name": "system_template.docx",
                "size": 3000,
                "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "scope": "system",
                "minio_path": "system/template.docx",
                "checksums": {"md5": "md5-4", "sha256": "sha256-4"}
            }
        ]
        
        created = []
        for i, f in enumerate(files):
            user_id = f"user-{(i % 2) + 1}" if f["scope"] != "system" else None
            created.append(file_repo.create(f, user_id=user_id))
        
        return created
    
    @pytest.mark.unit
    def test_get_by_id_existing(self, file_repo, populated_db):
        """Test getting file by ID"""
        file_id = populated_db[0]["id"]
        file = file_repo.get_by_id(file_id)
        
        assert file is not None
        assert file["name"] == "report.pdf"
        assert file["id"] == file_id
    
    @pytest.mark.unit
    def test_get_by_id_nonexistent(self, file_repo, populated_db):
        """Test getting non-existent file returns None"""
        file = file_repo.get_by_id("nonexistent-id")
        assert file is None
    
    @pytest.mark.unit
    def test_get_by_user(self, file_repo, populated_db):
        """Test getting files by user"""
        files = file_repo.get_by_user("user-1")
        
        assert len(files) >= 2
        assert all(f["uploaded_by"] == "user-1" for f in files)
    
    @pytest.mark.unit
    def test_get_by_scope_user_global(self, file_repo, populated_db):
        """Test getting files by user_global scope"""
        files = file_repo.get_by_scope("user_global")
        
        assert len(files) >= 2
        assert all(f["scope"] == "user_global" for f in files)
    
    @pytest.mark.unit
    def test_get_by_scope_with_user_filter(self, file_repo, populated_db):
        """Test getting files by scope with user filter"""
        files = file_repo.get_by_scope("user_global", user_id="user-1")
        
        assert len(files) >= 1
        assert all(f["scope"] == "user_global" for f in files)
        assert all(f["uploaded_by"] == "user-1" for f in files)
    
    @pytest.mark.unit
    def test_get_by_scope_with_project_filter(self, file_repo, populated_db):
        """Test getting files by scope with project filter"""
        files = file_repo.get_by_scope("user_project", project_id="project-1")
        
        assert len(files) >= 1
        assert all(f["scope"] == "user_project" for f in files)
        assert all(f["project_id"] == "project-1" for f in files)
    
    @pytest.mark.unit
    def test_get_by_project(self, file_repo, populated_db):
        """Test getting files by project"""
        files = file_repo.get_by_project("project-1")
        
        assert len(files) >= 1
        assert all(f["project_id"] == "project-1" for f in files)
        assert all(f["scope"] == "user_project" for f in files)
    
    @pytest.mark.unit
    def test_get_by_scope_system(self, file_repo, populated_db):
        """Test getting system files"""
        files = file_repo.get_by_scope("system")
        
        assert len(files) >= 1
        assert all(f["scope"] == "system" for f in files)


class TestFileRepositorySearchByName:
    """Test FileRepository search_by_name method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide mock database with AQL support"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        repo = FileRepository(db=mock_db)
        # Mock the AQL execute method
        mock_aql = MagicMock()
        mock_db._db = MagicMock()
        mock_db._db.aql = mock_aql
        return repo
    
    @pytest.mark.unit
    def test_search_by_name_basic(self, file_repo):
        """Test basic name search"""
        # Setup mock response
        mock_cursor = [
            {"id": "file-1", "name": "report_2024.pdf", "scope": "user_global"},
            {"id": "file-2", "name": "annual_report.pdf", "scope": "user_global"}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.search_by_name("report")
        
        assert len(results) == 2
        assert all("report" in r["name"].lower() for r in results)
        file_repo.db._db.aql.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_search_by_name_with_scope(self, file_repo):
        """Test name search with scope filter"""
        mock_cursor = [
            {"id": "file-1", "name": "system_config.json", "scope": "system"}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.search_by_name("config", scope="system")
        
        assert len(results) == 1
        # Verify scope was included in query
        call_args = file_repo.db._db.aql.execute.call_args
        assert "scope" in call_args[1]["bind_vars"]
    
    @pytest.mark.unit
    def test_search_by_name_with_user(self, file_repo):
        """Test name search with user filter"""
        mock_cursor = [
            {"id": "file-1", "name": "my_document.pdf", "uploaded_by": "user-123"}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.search_by_name("document", user_id="user-123")
        
        assert len(results) == 1
        call_args = file_repo.db._db.aql.execute.call_args
        assert "user_id" in call_args[1]["bind_vars"]
    
    @pytest.mark.unit
    def test_search_by_name_with_project(self, file_repo):
        """Test name search with project filter"""
        mock_cursor = [
            {"id": "file-1", "name": "project_spec.md", "project_id": "proj-456"}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.search_by_name("spec", project_id="proj-456")
        
        assert len(results) == 1
        call_args = file_repo.db._db.aql.execute.call_args
        assert "project_id" in call_args[1]["bind_vars"]
    
    @pytest.mark.unit
    def test_search_by_name_no_results(self, file_repo):
        """Test name search with no results"""
        file_repo.db._db.aql.execute.return_value = iter([])
        
        results = file_repo.search_by_name("nonexistent")
        
        assert len(results) == 0
    
    @pytest.mark.unit
    def test_search_by_name_case_insensitive(self, file_repo):
        """Test search is case insensitive"""
        mock_cursor = [
            {"id": "file-1", "name": "UPPERCASE.PDF"}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.search_by_name("uppercase")
        
        assert len(results) == 1
        # Verify search term was lowercased
        call_args = file_repo.db._db.aql.execute.call_args
        assert "%uppercase%" in call_args[1]["bind_vars"]["search"]


class TestFileRepositoryProcessingStatus:
    """Test FileRepository processing status management"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.fixture
    def file_with_processing(self, file_repo):
        """Create file with initial processing status"""
        file_data = {
            "name": "process_me.pdf",
            "size": 5000,
            "type": "application/pdf",
            "scope": "user_global",
            "minio_path": "user_global/user-1/process_me.pdf",
            "processing_status": {
                "global": "pending",
                "phases": {}
            }
        }
        return file_repo.create(file_data, user_id="user-1")
    
    @pytest.mark.unit
    def test_update_processing_status_new_phase(self, file_repo, file_with_processing):
        """Test updating processing status for new phase"""
        file_id = file_with_processing["id"]
        
        result = file_repo.update_processing_status(
            file_id=file_id,
            phase="02-data_extraction",
            status="processing"
        )
        
        assert result is not None
        assert "processing_status" in result
        assert "02-data_extraction" in result["processing_status"]["phases"]
        assert result["processing_status"]["phases"]["02-data_extraction"]["status"] == "processing"
    
    @pytest.mark.unit
    def test_update_processing_status_with_version(self, file_repo, file_with_processing):
        """Test updating processing status with version"""
        file_id = file_with_processing["id"]
        
        result = file_repo.update_processing_status(
            file_id=file_id,
            phase="02-data_extraction",
            status="completed",
            version="v1"
        )
        
        assert result is not None
        phase_status = result["processing_status"]["phases"]["02-data_extraction"]
        assert "v1" in phase_status["available_versions"]
    
    @pytest.mark.unit
    def test_update_processing_status_global_completed(self, file_repo, file_with_processing):
        """Test global status becomes completed when all phases complete"""
        file_id = file_with_processing["id"]
        
        # Complete all phases
        phases = ["02-data_extraction", "03-summary", "04-chunking"]
        for phase in phases:
            file_repo.update_processing_status(file_id, phase, "completed")
        
        result = file_repo.get_by_id(file_id)
        # Global status should reflect all completed
        assert result["processing_status"]["global"] == "completed"
    
    @pytest.mark.unit
    def test_update_processing_status_global_failed(self, file_repo, file_with_processing):
        """Test global status becomes failed if any phase fails"""
        file_id = file_with_processing["id"]
        
        file_repo.update_processing_status(file_id, "02-data_extraction", "completed")
        file_repo.update_processing_status(file_id, "03-summary", "failed")
        
        result = file_repo.get_by_id(file_id)
        assert result["processing_status"]["global"] == "failed"
    
    @pytest.mark.unit
    def test_update_processing_status_global_processing(self, file_repo, file_with_processing):
        """Test global status is processing when any phase is processing"""
        file_id = file_with_processing["id"]
        
        file_repo.update_processing_status(file_id, "02-data_extraction", "completed")
        file_repo.update_processing_status(file_id, "03-summary", "processing")
        
        result = file_repo.get_by_id(file_id)
        assert result["processing_status"]["global"] == "processing"
    
    @pytest.mark.unit
    def test_update_processing_status_nonexistent_file(self, file_repo):
        """Test updating processing status for non-existent file"""
        result = file_repo.update_processing_status(
            file_id="nonexistent",
            phase="02-data_extraction",
            status="processing"
        )
        
        assert result is None


class TestFileRepositorySetActiveVersion:
    """Test FileRepository set_active_version method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.fixture
    def file_with_versions(self, file_repo):
        """Create file with multiple versions"""
        file_data = {
            "name": "versioned.pdf",
            "size": 5000,
            "type": "application/pdf",
            "scope": "user_global",
            "minio_path": "user_global/user-1/versioned.pdf",
            "processing_status": {
                "global": "completed",
                "phases": {
                    "02-data_extraction": {
                        "status": "completed",
                        "active_version": None,
                        "available_versions": ["v1", "v2", "v3"],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }
            }
        }
        return file_repo.create(file_data, user_id="user-1")
    
    @pytest.mark.unit
    def test_set_active_version_success(self, file_repo, file_with_versions):
        """Test setting active version successfully"""
        file_id = file_with_versions["id"]
        
        result = file_repo.set_active_version(
            file_id=file_id,
            phase="02-data_extraction",
            version="v2"
        )
        
        assert result is not None
        assert result["processing_status"]["phases"]["02-data_extraction"]["active_version"] == "v2"
        assert result["active_configuration"]["02-data_extraction"] == "v2"
    
    @pytest.mark.unit
    def test_set_active_version_nonexistent_version(self, file_repo, file_with_versions):
        """Test setting non-existent version returns None"""
        file_id = file_with_versions["id"]
        
        result = file_repo.set_active_version(
            file_id=file_id,
            phase="02-data_extraction",
            version="v99"  # Non-existent
        )
        
        assert result is None
    
    @pytest.mark.unit
    def test_set_active_version_nonexistent_phase(self, file_repo, file_with_versions):
        """Test setting version for non-existent phase returns None"""
        file_id = file_with_versions["id"]
        
        result = file_repo.set_active_version(
            file_id=file_id,
            phase="99-nonexistent",
            version="v1"
        )
        
        assert result is None
    
    @pytest.mark.unit
    def test_set_active_version_nonexistent_file(self, file_repo):
        """Test setting version for non-existent file returns None"""
        result = file_repo.set_active_version(
            file_id="nonexistent",
            phase="02-data_extraction",
            version="v1"
        )
        
        assert result is None


class TestFileRepositoryPromotion:
    """Test FileRepository file promotion"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.fixture
    def user_file(self, file_repo):
        """Create user file for promotion"""
        file_data = {
            "name": "promote_me.pdf",
            "size": 5000,
            "type": "application/pdf",
            "scope": "user_global",
            "minio_path": "user_global/user-1/promote_me.pdf"
        }
        return file_repo.create(file_data, user_id="user-1")
    
    @pytest.mark.unit
    def test_mark_promoted_success(self, file_repo, user_file):
        """Test marking file as promoted"""
        file_id = user_file["id"]
        original_metadata = {"scope": "user_global", "uploaded_by": "user-1"}
        
        result = file_repo.mark_promoted(
            file_id=file_id,
            promoted_by="admin-1",
            promoted_from=original_metadata
        )
        
        assert result is not None
        assert result["promoted"] is True
        assert result["promoted_by"] == "admin-1"
        assert result["promoted_from"] == original_metadata
        assert result["promoted_at"] is not None
    
    @pytest.mark.unit
    def test_mark_promoted_nonexistent_file(self, file_repo):
        """Test promoting non-existent file returns None"""
        result = file_repo.mark_promoted(
            file_id="nonexistent",
            promoted_by="admin-1",
            promoted_from={}
        )
        
        assert result is None


class TestFileRepositoryDelete:
    """Test FileRepository delete operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.mark.unit
    def test_delete_file_success(self, file_repo):
        """Test deleting file successfully"""
        file = file_repo.create({
            "name": "delete_me.pdf",
            "size": 1000,
            "type": "application/pdf",
            "scope": "user_global",
            "minio_path": "path/to/file"
        }, user_id="user-1")
        
        result = file_repo.delete(file["id"])
        
        assert result is True
        assert file_repo.get_by_id(file["id"]) is None
    
    @pytest.mark.unit
    def test_delete_nonexistent_file(self, file_repo):
        """Test deleting non-existent file returns False"""
        result = file_repo.delete("nonexistent-id")
        
        assert result is False


class TestFileRepositoryMinioPath:
    """Test FileRepository get_by_minio_path method"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide clean mock database"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        return FileRepository(db=mock_db)
    
    @pytest.mark.unit
    def test_get_by_minio_path_found(self, file_repo):
        """Test getting file by minio path"""
        minio_path = "user_global/user-1/unique_file.pdf"
        file_repo.create({
            "name": "unique_file.pdf",
            "size": 1000,
            "type": "application/pdf",
            "scope": "user_global",
            "minio_path": minio_path
        }, user_id="user-1")
        
        result = file_repo.get_by_minio_path(minio_path)
        
        assert result is not None
        assert result["minio_path"] == minio_path
    
    @pytest.mark.unit
    def test_get_by_minio_path_not_found(self, file_repo):
        """Test getting file by non-existent minio path"""
        result = file_repo.get_by_minio_path("nonexistent/path")
        
        assert result is None


class TestFileRepositoryChecksum:
    """Test FileRepository checksum queries"""
    
    @pytest.fixture
    def mock_db(self):
        """Provide mock database with AQL support"""
        db = MockDatabase()
        db.connect()
        db.create_collection("files")
        return db
    
    @pytest.fixture
    def file_repo(self, mock_db):
        """Provide FileRepository with mock database"""
        repo = FileRepository(db=mock_db)
        # Mock the AQL execute method
        mock_aql = MagicMock()
        mock_db._db = MagicMock()
        mock_db._db.aql = mock_aql
        return repo
    
    @pytest.mark.unit
    def test_get_by_checksum_md5(self, file_repo):
        """Test finding files by MD5 checksum"""
        mock_cursor = [
            {"id": "file-1", "name": "dup1.pdf", "checksums": {"md5": "abc123"}},
            {"id": "file-2", "name": "dup2.pdf", "checksums": {"md5": "abc123"}}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.get_by_checksum("md5", "abc123")
        
        assert len(results) == 2
        file_repo.db._db.aql.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_get_by_checksum_sha256(self, file_repo):
        """Test finding files by SHA256 checksum"""
        mock_cursor = [
            {"id": "file-1", "name": "unique.pdf", "checksums": {"sha256": "sha256hash"}}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.get_by_checksum("sha256", "sha256hash")
        
        assert len(results) == 1
    
    @pytest.mark.unit
    def test_get_by_checksum_no_duplicates(self, file_repo):
        """Test finding files with no matching checksum"""
        file_repo.db._db.aql.execute.return_value = iter([])
        
        results = file_repo.get_by_checksum("md5", "nonexistent")
        
        assert len(results) == 0
    
    @pytest.mark.unit
    def test_get_by_checksum_simhash(self, file_repo):
        """Test finding files by SimHash (for similarity detection)"""
        mock_cursor = [
            {"id": "file-1", "name": "similar1.txt", "checksums": {"simhash": "sim123"}},
            {"id": "file-2", "name": "similar2.txt", "checksums": {"simhash": "sim123"}}
        ]
        file_repo.db._db.aql.execute.return_value = iter(mock_cursor)
        
        results = file_repo.get_by_checksum("simhash", "sim123")
        
        assert len(results) == 2


class TestFileRepositoryInitialization:
    """Test FileRepository initialization"""
    
    @pytest.mark.unit
    def test_init_with_provided_db(self):
        """Test initialization with provided database"""
        mock_db = MockDatabase()
        mock_db.connect()
        mock_db.create_collection("files")
        
        repo = FileRepository(db=mock_db)
        
        assert repo.db == mock_db
        assert repo.collection == "files"
    
    @pytest.mark.unit
    def test_init_without_db_uses_factory(self):
        """Test initialization without db uses factory"""
        # Patch at source module where get_database is defined
        with patch('src.database.factory.get_database') as mock_factory:
            mock_db = MagicMock()
            mock_factory.return_value = mock_db
            
            repo = FileRepository(db=None)
            
            mock_factory.assert_called_once()
            assert repo.db == mock_db