"""
Path: backend/tests/unit/repositories/test_processing_queue_repository.py
Version: 1.1

Changes in v1.1:
- Fixed import: use inline mock_database fixture instead of tests.unit.conftest

Unit tests for processing_queue_repository with Beartype validation.

Tests:
- create_phase_queue: Creating queue entries
- get_pending_entries: Retrieving pending/processing entries with priority sorting
- update_phase_status: Status transitions and timestamps
- get_by_file_and_phase: Filtering by file and phase
- delete_by_file: Cascade deletion
- Beartype validation: Type checking
"""

import pytest
from datetime import datetime, timezone
from beartype.roar import BeartypeCallHintParamViolation

from src.repositories.processing_queue_repository import ProcessingQueueRepository


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    from tests.unit.mock_database import MockDatabase
    return MockDatabase()


class TestProcessingQueueRepositoryCreate:
    """Tests for creating queue entries"""
    
    def test_create_phase_queue_success(self, mock_database):
        """Test creating processing queue entry"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        queue_data = {
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "algorithm_name": "basic_extraction",
            "parameters": {"test": "value"},
            "dependencies": {},
            "metadata": {
                "user_id": "user-123",
                "project_id": "project-456",
                "file_name": "test.pdf"
            }
        }
        
        result = repo.create_phase_queue(queue_data)
        
        assert result["file_id"] == "file-123"
        assert result["phase"] == "02-data_extraction"
        assert result["new_version"] == "v1_algo-1.0"
        assert result["status"] == "pending"
        assert result["priority"] == 5  # Default priority
        assert "created_at" in result
        assert "updated_at" in result
        assert result["started_at"] is None
        assert result["completed_at"] is None
        assert result["error"] is None
    
    def test_create_phase_queue_with_custom_priority(self, mock_database):
        """Test creating queue entry with custom priority"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        queue_data = {
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v2_algo-2.0",
            "algorithm_version": "2.0",
            "priority": 8,
            "status": "pending"
        }
        
        result = repo.create_phase_queue(queue_data)
        
        assert result["priority"] == 8
        assert result["status"] == "pending"
    
    def test_create_phase_queue_sets_timestamps(self, mock_database):
        """Test that timestamps are set correctly"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        queue_data = {
            "file_id": "file-123",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        }
        
        before = datetime.now(timezone.utc)
        result = repo.create_phase_queue(queue_data)
        after = datetime.now(timezone.utc)
        
        created_at = datetime.fromisoformat(result["created_at"])
        updated_at = datetime.fromisoformat(result["updated_at"])
        
        assert before <= created_at <= after
        assert before <= updated_at <= after
        assert created_at == updated_at  # Should be same on creation
    
    def test_create_phase_queue_invalid_type_fails(self, mock_database):
        """Test that invalid types raise Beartype error"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.create_phase_queue("not a dict")  # Should be dict
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.create_phase_queue(None)  # Should be dict


class TestProcessingQueueRepositoryRetrieve:
    """Tests for retrieving queue entries"""
    
    def test_get_pending_entries_default_limit(self, mock_database):
        """Test getting pending entries with default limit"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create multiple queue entries
        for i in range(15):
            repo.create_phase_queue({
                "file_id": f"file-{i}",
                "phase": "02-data_extraction",
                "new_version": "v1_algo-1.0",
                "algorithm_version": "1.0",
                "status": "pending",
                "priority": i % 10
            })
        
        results = repo.get_pending_entries()
        
        assert len(results) == 10  # Default limit
        assert all(r["status"] in ["pending", "processing"] for r in results)
    
    def test_get_pending_entries_custom_limit(self, mock_database):
        """Test getting pending entries with custom limit"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        for i in range(10):
            repo.create_phase_queue({
                "file_id": f"file-{i}",
                "phase": "02-data_extraction",
                "new_version": "v1_algo-1.0",
                "algorithm_version": "1.0",
                "status": "pending"
            })
        
        results = repo.get_pending_entries(limit=5)
        
        assert len(results) == 5
    
    def test_get_pending_entries_priority_order(self, mock_database):
        """Test that entries are sorted by priority (desc) then created_at (asc)"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create entries with different priorities
        repo.create_phase_queue({
            "file_id": "file-1",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "priority": 3
        })
        
        repo.create_phase_queue({
            "file_id": "file-2",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "priority": 8
        })
        
        repo.create_phase_queue({
            "file_id": "file-3",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "priority": 5
        })
        
        results = repo.get_pending_entries()
        
        # Should be ordered by priority descending
        priorities = [r["priority"] for r in results]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_pending_entries_excludes_completed(self, mock_database):
        """Test that completed/failed entries are excluded"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create entries with different statuses
        pending = repo.create_phase_queue({
            "file_id": "file-1",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "status": "pending"
        })
        
        processing = repo.create_phase_queue({
            "file_id": "file-2",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "status": "processing"
        })
        
        completed = repo.create_phase_queue({
            "file_id": "file-3",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "status": "completed"
        })
        
        failed = repo.create_phase_queue({
            "file_id": "file-4",
            "phase": "05-graph_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0",
            "status": "failed"
        })
        
        results = repo.get_pending_entries()
        
        result_ids = [r["id"] for r in results]
        assert pending["id"] in result_ids
        assert processing["id"] in result_ids
        assert completed["id"] not in result_ids
        assert failed["id"] not in result_ids
    
    def test_get_by_file_and_phase(self, mock_database):
        """Test filtering by file_id and phase"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create entries for different files and phases
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.create_phase_queue({
            "file_id": "file-456",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        results = repo.get_by_file_and_phase("file-123", "02-data_extraction")
        
        assert len(results) == 1
        assert results[0]["file_id"] == "file-123"
        assert results[0]["phase"] == "02-data_extraction"
    
    def test_get_by_file_and_phase_with_version(self, mock_database):
        """Test filtering by file, phase, and version"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v2_algo-2.0",
            "algorithm_version": "2.0"
        })
        
        results = repo.get_by_file_and_phase(
            "file-123",
            "04-chunking",
            version="v2_algo-2.0"
        )
        
        assert len(results) == 1
        assert results[0]["new_version"] == "v2_algo-2.0"


class TestProcessingQueueRepositoryUpdate:
    """Tests for updating queue entries"""
    
    def test_update_phase_status_to_processing(self, mock_database):
        """Test updating status to processing sets started_at"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        before = datetime.now(timezone.utc)
        updated = repo.update_phase_status(entry["id"], "processing")
        after = datetime.now(timezone.utc)
        
        assert updated is not None
        assert updated["status"] == "processing"
        assert updated["started_at"] is not None
        
        started_at = datetime.fromisoformat(updated["started_at"])
        assert before <= started_at <= after
    
    def test_update_phase_status_to_completed(self, mock_database):
        """Test updating status to completed sets completed_at"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        # First set to processing
        repo.update_phase_status(entry["id"], "processing")
        
        # Then complete
        before = datetime.now(timezone.utc)
        updated = repo.update_phase_status(entry["id"], "completed")
        after = datetime.now(timezone.utc)
        
        assert updated["status"] == "completed"
        assert updated["completed_at"] is not None
        
        completed_at = datetime.fromisoformat(updated["completed_at"])
        assert before <= completed_at <= after
    
    def test_update_phase_status_to_failed_with_error(self, mock_database):
        """Test updating status to failed sets error message"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        error_msg = "Failed to process: Invalid format"
        updated = repo.update_phase_status(entry["id"], "failed", error=error_msg)
        
        assert updated["status"] == "failed"
        assert updated["error"] == error_msg
        assert updated["completed_at"] is not None
    
    def test_update_phase_status_updates_timestamp(self, mock_database):
        """Test that updated_at changes on each update"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "05-graph_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        original_updated_at = entry["updated_at"]
        
        # Wait a bit and update
        import time
        time.sleep(0.1)
        
        updated = repo.update_phase_status(entry["id"], "processing")
        
        assert updated["updated_at"] != original_updated_at
        assert updated["updated_at"] > original_updated_at
    
    def test_update_phase_status_not_found_returns_none(self, mock_database):
        """Test updating non-existent entry returns None"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        result = repo.update_phase_status("nonexistent-id", "completed")
        
        assert result is None
    
    def test_update_phase_status_invalid_types_fail(self, mock_database):
        """Test that invalid types raise Beartype error"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.update_phase_status(123, "completed")  # queue_id should be str
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.update_phase_status(entry["id"], 123)  # status should be str


class TestProcessingQueueRepositoryDelete:
    """Tests for deleting queue entries"""
    
    def test_delete_by_file_success(self, mock_database):
        """Test deleting all entries for a file"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create multiple entries for same file
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "03-summary",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.create_phase_queue({
            "file_id": "file-456",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        deleted_count = repo.delete_by_file("file-123")
        
        assert deleted_count == 2
        
        # Verify file-123 entries are gone
        remaining = repo.get_by_file_and_phase("file-123", "02-data_extraction")
        assert len(remaining) == 0
        
        # Verify file-456 entries still exist
        file456_entries = repo.get_by_file_and_phase("file-456", "02-data_extraction")
        assert len(file456_entries) == 1
    
    def test_delete_by_file_no_entries_returns_zero(self, mock_database):
        """Test deleting entries for file with no entries"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        deleted_count = repo.delete_by_file("nonexistent-file")
        
        assert deleted_count == 0
    
    def test_delete_by_file_invalid_type_fails(self, mock_database):
        """Test that invalid file_id type raises Beartype error"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.delete_by_file(123)  # Should be str
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.delete_by_file(None)  # Should be str


class TestProcessingQueueRepositoryBeartypeValidation:
    """Tests for Beartype type validation"""
    
    def test_get_pending_entries_invalid_limit_type(self, mock_database):
        """Test that invalid limit type raises Beartype error"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.get_pending_entries(limit="10")  # Should be int
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.get_pending_entries(limit=None)  # Should be int
    
    def test_get_by_file_and_phase_invalid_types(self, mock_database):
        """Test that invalid parameter types raise Beartype error"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.get_by_file_and_phase(123, "02-data_extraction")  # file_id should be str
        
        with pytest.raises(BeartypeCallHintParamViolation):
            repo.get_by_file_and_phase("file-123", 123)  # phase should be str
    
    def test_create_phase_queue_returns_correct_type(self, mock_database):
        """Test that create_phase_queue returns dict"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        result = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        # Beartype ensures this is dict[str, Any]
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())
    
    def test_get_pending_entries_returns_list_of_dicts(self, mock_database):
        """Test that get_pending_entries returns list[dict]"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        results = repo.get_pending_entries()
        
        # Beartype ensures this is list[dict[str, Any]]
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, dict)
            assert all(isinstance(k, str) for k in item.keys())


class TestProcessingQueueRepositoryIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_processing_workflow(self, mock_database):
        """Test complete workflow from creation to completion"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create entry
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "02-data_extraction",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        assert entry["status"] == "pending"
        
        # Get pending entries
        pending = repo.get_pending_entries()
        assert len(pending) >= 1
        assert any(e["id"] == entry["id"] for e in pending)
        
        # Start processing
        updated = repo.update_phase_status(entry["id"], "processing")
        assert updated["status"] == "processing"
        assert updated["started_at"] is not None
        
        # Still in pending list (includes processing)
        pending = repo.get_pending_entries()
        assert any(e["id"] == entry["id"] for e in pending)
        
        # Complete
        completed = repo.update_phase_status(entry["id"], "completed")
        assert completed["status"] == "completed"
        assert completed["completed_at"] is not None
        
        # No longer in pending list
        pending = repo.get_pending_entries()
        assert not any(e["id"] == entry["id"] for e in pending)
    
    def test_failed_processing_workflow(self, mock_database):
        """Test workflow with failure"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create and start processing
        entry = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        repo.update_phase_status(entry["id"], "processing")
        
        # Fail with error
        failed = repo.update_phase_status(
            entry["id"],
            "failed",
            error="Algorithm timeout"
        )
        
        assert failed["status"] == "failed"
        assert failed["error"] == "Algorithm timeout"
        assert failed["completed_at"] is not None
        
        # No longer in pending list
        pending = repo.get_pending_entries()
        assert not any(e["id"] == entry["id"] for e in pending)
    
    def test_multiple_versions_same_file(self, mock_database):
        """Test handling multiple versions of same phase for one file"""
        repo = ProcessingQueueRepository(db=mock_database)
        
        # Create v1
        v1 = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v1_algo-1.0",
            "algorithm_version": "1.0"
        })
        
        # Complete v1
        repo.update_phase_status(v1["id"], "completed")
        
        # Create v2 (reprocessing)
        v2 = repo.create_phase_queue({
            "file_id": "file-123",
            "phase": "04-chunking",
            "new_version": "v2_algo-2.0",
            "algorithm_version": "2.0"
        })
        
        # Get all entries for this file/phase
        entries = repo.get_by_file_and_phase("file-123", "04-chunking")
        assert len(entries) == 2
        
        # Can filter by version
        v2_entries = repo.get_by_file_and_phase(
            "file-123",
            "04-chunking",
            version="v2_algo-2.0"
        )
        assert len(v2_entries) == 1
        assert v2_entries[0]["new_version"] == "v2_algo-2.0"