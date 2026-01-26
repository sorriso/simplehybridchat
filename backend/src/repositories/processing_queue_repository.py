"""
Path: backend/src/repositories/processing_queue_repository.py
Version: 1.0

Repository for processing queue management with Beartype validation.
Handles queue entries for file processing phases.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from beartype import beartype

from src.repositories.base import BaseRepository
from src.database.interface import IDatabase


class ProcessingQueueRepository(BaseRepository):
    """
    Repository for managing processing queue entries.
    
    Each entry represents a phase processing task for a file.
    Supports priority-based scheduling and status tracking.
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize repository with database connection"""
        if db is None:
            from src.database.factory import get_database
            db = get_database()
        super().__init__(db=db, collection="processing_queue")
    
    @beartype
    def create_phase_queue(
        self,
        queue_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create processing queue entry for a phase.
        
        Args:
            queue_data: Queue entry data containing:
                - file_id: File identifier
                - phase: Processing phase (02-data_extraction, 03-summary, etc)
                - new_version: Version being created (e.g., v1_algo-1.0)
                - algorithm_version: Algorithm version number
                - status: Initial status (default: pending)
                - priority: Queue priority (default: 5)
                - metadata: Additional metadata
        
        Returns:
            Created queue document with timestamps
        """
        # Add UTC timestamps
        now = datetime.now(timezone.utc)
        queue_data["created_at"] = now.isoformat()
        queue_data["updated_at"] = now.isoformat()
        
        # Set defaults
        queue_data.setdefault("priority", 5)
        queue_data.setdefault("status", "pending")
        queue_data.setdefault("started_at", None)
        queue_data.setdefault("completed_at", None)
        queue_data.setdefault("error", None)
        
        return self.create(queue_data)
    
    @beartype
    def get_pending_entries(
        self,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get pending queue entries sorted by priority.
        
        Retrieves entries with status 'pending' or 'processing',
        ordered by priority (descending) and creation time (ascending).
        
        Args:
            limit: Maximum number of entries to return (default: 10)
        
        Returns:
            List of pending queue entries
        """
        # Query for pending/processing entries
        query = """
        FOR queue IN processing_queue
            FILTER queue.status IN ['pending', 'processing']
            SORT queue.priority DESC, queue.created_at ASC
            LIMIT @limit
            RETURN queue
        """
        
        cursor = self.db.aql.execute(
            query,
            bind_vars={"limit": limit}
        )
        
        return [doc for doc in cursor]
    
    @beartype
    def update_phase_status(
        self,
        queue_id: str,
        status: str,
        error: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """
        Update phase processing status.
        
        Automatically sets timestamps based on status:
        - 'processing': Sets started_at
        - 'completed'/'failed': Sets completed_at
        
        Args:
            queue_id: Queue entry identifier
            status: New status (pending/processing/completed/failed)
            error: Error message if status is 'failed'
        
        Returns:
            Updated queue entry or None if not found
        """
        entry = self.get_by_id(queue_id)
        if not entry:
            return None
        
        now = datetime.now(timezone.utc)
        entry["status"] = status
        entry["updated_at"] = now.isoformat()
        
        if status == "processing":
            entry["started_at"] = now.isoformat()
        elif status in ["completed", "failed"]:
            entry["completed_at"] = now.isoformat()
        
        if error:
            entry["error"] = error
        
        return self.update(queue_id, entry)
    
    @beartype
    def get_by_file_and_phase(
        self,
        file_id: str,
        phase: str,
        version: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get queue entries for a specific file and phase.
        
        Args:
            file_id: File identifier
            phase: Processing phase
            version: Optional version filter
        
        Returns:
            List of matching queue entries
        """
        filters = {
            "file_id": file_id,
            "phase": phase
        }
        
        if version:
            filters["new_version"] = version
        
        return self.get_all(filters=filters)
    
    @beartype
    def delete_by_file(
        self,
        file_id: str
    ) -> int:
        """
        Delete all queue entries for a file.
        
        Used when file is deleted to cleanup queue.
        
        Args:
            file_id: File identifier
        
        Returns:
            Number of deleted entries
        """
        query = """
        FOR queue IN processing_queue
            FILTER queue.file_id == @file_id
            REMOVE queue IN processing_queue
            RETURN 1
        """
        
        cursor = self.db.aql.execute(
            query,
            bind_vars={"file_id": file_id}
        )
        
        return sum(1 for _ in cursor)