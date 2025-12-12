"""
Path: backend/src/repositories/base.py
Version: 1

Base repository with generic CRUD operations
All repositories should inherit from this class
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
import logging

from src.database.interface import IDatabase
from src.database.exceptions import NotFoundError, DatabaseException

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Dict[str, Any])


class BaseRepository(Generic[T]):
    """
    Base repository with generic CRUD operations
    
    Provides common database operations that can be reused
    across all repositories.
    
    Example:
        class UserRepository(BaseRepository):
            def __init__(self, db: IDatabase):
                super().__init__(db, collection="users")
            
            def get_by_email(self, email: str) -> Optional[Dict]:
                return self.find_one({"email": email})
    """
    
    def __init__(self, db: IDatabase, collection: str):
        """
        Initialize repository
        
        Args:
            db: Database instance
            collection: Collection/table name
        """
        self.db = db
        self.collection = collection
    
    # ========================================================================
    # CREATE
    # ========================================================================
    
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create new document
        
        Args:
            data: Document data
            
        Returns:
            Created document with generated ID
            
        Raises:
            DatabaseException: If creation fails
            
        Example:
            user = repo.create({
                "name": "John Doe",
                "email": "john@example.com"
            })
        """
        try:
            document = self.db.create(self.collection, data)
            logger.info(f"Created document in {self.collection}: {document.get('_key')}")
            return document
        except DatabaseException as e:
            logger.error(f"Failed to create document in {self.collection}: {e}")
            raise
    
    # ========================================================================
    # READ
    # ========================================================================
    
    def get_by_id(self, doc_id: str) -> Optional[T]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID (_key)
            
        Returns:
            Document or None if not found
            
        Example:
            user = repo.get_by_id("user123")
        """
        try:
            document = self.db.get_by_id(self.collection, doc_id)
            if document:
                logger.debug(f"Retrieved document from {self.collection}: {doc_id}")
            return document
        except Exception as e:
            logger.warning(f"Error getting document {doc_id}: {e}")
            return None
    
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[T]:
        """
        Get all documents with optional filters and pagination
        
        Args:
            filters: Query filters (e.g., {"status": "active"})
            skip: Number to skip (for pagination)
            limit: Maximum to return
            sort: Sort specification (e.g., {"createdAt": -1})
            
        Returns:
            List of documents
            
        Example:
            # Get active users, page 2, 10 per page
            users = repo.get_all(
                filters={"status": "active"},
                skip=10,
                limit=10,
                sort={"createdAt": -1}
            )
        """
        try:
            documents = self.db.get_all(
                self.collection,
                filters=filters,
                skip=skip,
                limit=limit,
                sort=sort
            )
            logger.debug(f"Retrieved {len(documents)} documents from {self.collection}")
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents from {self.collection}: {e}")
            return []
    
    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """
        Find first document matching filters
        
        Args:
            filters: Query filters
            
        Returns:
            First matching document or None
            
        Example:
            user = repo.find_one({"email": "john@example.com"})
        """
        try:
            document = self.db.find_one(self.collection, filters)
            if document:
                logger.debug(f"Found document in {self.collection} matching {filters}")
            return document
        except Exception as e:
            logger.warning(f"Error finding document: {e}")
            return None
    
    def find_many(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[T]:
        """
        Find multiple documents matching filters
        
        Args:
            filters: Query filters (required)
            skip: Number to skip
            limit: Maximum to return
            sort: Sort specification
            
        Returns:
            List of matching documents
            
        Example:
            active_users = repo.find_many(
                {"status": "active"},
                limit=50
            )
        """
        return self.get_all(filters=filters, skip=skip, limit=limit, sort=sort)
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in collection
        
        Args:
            filters: Optional query filters
            
        Returns:
            Number of matching documents
            
        Example:
            total = repo.count()
            active_count = repo.count({"status": "active"})
        """
        try:
            count = self.db.count(self.collection, filters=filters)
            logger.debug(f"Counted {count} documents in {self.collection}")
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def exists(self, doc_id: str) -> bool:
        """
        Check if document exists
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if exists, False otherwise
            
        Example:
            if repo.exists("user123"):
                print("User exists")
        """
        try:
            return self.db.exists(self.collection, doc_id)
        except Exception:
            return False
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    def update(self, doc_id: str, updates: Dict[str, Any]) -> T:
        """
        Update document with partial data
        
        Args:
            doc_id: Document ID
            updates: Fields to update
            
        Returns:
            Updated document
            
        Raises:
            NotFoundError: If document not found
            DatabaseException: If update fails
            
        Example:
            updated = repo.update("user123", {
                "status": "active",
                "lastLogin": "2024-01-15"
            })
        """
        try:
            document = self.db.update(self.collection, doc_id, updates)
            logger.info(f"Updated document in {self.collection}: {doc_id}")
            return document
        except NotFoundError:
            logger.warning(f"Document not found for update: {doc_id}")
            raise
        except DatabaseException as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
            
        Example:
            deleted = repo.delete("user123")
            if deleted:
                print("User deleted")
        """
        try:
            result = self.db.delete(self.collection, doc_id)
            if result:
                logger.info(f"Deleted document from {self.collection}: {doc_id}")
            else:
                logger.debug(f"Document not found for deletion: {doc_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None
    ) -> tuple[List[T], int]:
        """
        Get paginated results with total count
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            filters: Query filters
            sort: Sort specification
            
        Returns:
            Tuple of (items, total_count)
            
        Example:
            items, total = repo.get_paginated(page=2, per_page=10)
            # Returns items 11-20 and total count
        """
        # Calculate skip
        skip = (page - 1) * per_page
        
        # Get items
        items = self.get_all(
            filters=filters,
            skip=skip,
            limit=per_page,
            sort=sort
        )
        
        # Get total count
        total = self.count(filters=filters)
        
        return items, total
    
    def bulk_create(self, documents: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple documents
        
        Args:
            documents: List of documents to create
            
        Returns:
            List of created documents
            
        Example:
            users = repo.bulk_create([
                {"name": "User 1"},
                {"name": "User 2"}
            ])
        """
        created = []
        for doc in documents:
            try:
                created_doc = self.create(doc)
                created.append(created_doc)
            except DatabaseException as e:
                logger.error(f"Failed to create document in bulk: {e}")
                # Continue with other documents
        
        logger.info(f"Bulk created {len(created)}/{len(documents)} documents")
        return created