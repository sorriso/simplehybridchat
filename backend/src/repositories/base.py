"""
Path: backend/src/repositories/base.py
Version: 2

Changes in v2:
- ADDED: bulk_create() method for batch document creation
- ADDED: find_many() method (already existed as get_all, this is an alias)
- Reason: Tests require these methods for comprehensive CRUD operations

Base repository with generic CRUD operations
All repositories should inherit from this class
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic, Tuple
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
    
    def __init__(self, db: IDatabase = None, collection: str = None):
        """
        Initialize repository
        
        Args:
            db: Database instance
            collection: Collection/table name
        """
        if db is None:
            from src.database.factory import get_database
            db = get_database()
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
    
    def bulk_create(self, documents: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple documents in batch
        
        Args:
            documents: List of document data dicts
            
        Returns:
            List of created documents with generated IDs
            
        Raises:
            DatabaseException: If creation fails
            
        Example:
            users = repo.bulk_create([
                {"name": "John", "email": "john@example.com"},
                {"name": "Jane", "email": "jane@example.com"}
            ])
        """
        created = []
        for doc_data in documents:
            try:
                doc = self.create(doc_data)
                created.append(doc)
            except DatabaseException as e:
                logger.error(f"Failed to create document in bulk: {e}")
                # Continue with other documents
                continue
        return created
    
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
            return document
        except NotFoundError:
            return None
        except DatabaseException as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[T]:
        """
        Get all documents matching filters
        
        Args:
            filters: Optional filter criteria
            skip: Number of documents to skip
            limit: Maximum documents to return
            sort: Sort specification (field: direction)
            
        Returns:
            List of matching documents
            
        Example:
            active_users = repo.get_all(filters={"status": "active"}, limit=50)
        """
        try:
            documents = self.db.find_many(
                self.collection,
                filters=filters or {},
                skip=skip,
                limit=limit,
                sort=sort
            )
            return documents
        except DatabaseException as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def find_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[T]:
        """
        Alias for get_all() - find multiple documents matching filters
        
        Args:
            filters: Optional filter criteria
            skip: Number of documents to skip
            limit: Maximum documents to return
            sort: Sort specification (field: direction)
            
        Returns:
            List of matching documents
            
        Example:
            active_users = repo.find_many(filters={"status": "active"})
        """
        return self.get_all(filters=filters, skip=skip, limit=limit, sort=sort)
    
    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """
        Find first document matching filters
        
        Args:
            filters: Filter criteria
            
        Returns:
            First matching document or None
            
        Example:
            user = repo.find_one({"email": "john@example.com"})
        """
        try:
            return self.db.find_one(self.collection, filters)
        except DatabaseException as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching filters
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            Count of matching documents
            
        Example:
            total_users = repo.count()
            active_users = repo.count({"status": "active"})
        """
        try:
            return self.db.count(self.collection, filters)
        except DatabaseException as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def exists(self, doc_id: str) -> bool:
        """
        Check if document exists
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if document exists
            
        Example:
            if repo.exists("user123"):
                print("User exists")
        """
        try:
            return self.db.exists(self.collection, doc_id)
        except DatabaseException:
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
    # PAGINATION
    # ========================================================================
    
    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None
    ) -> Tuple[List[T], int]:
        """
        Get paginated results with total count
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            filters: Optional filter criteria
            sort: Sort specification
            
        Returns:
            Tuple of (items, total_count)
            
        Example:
            users, total = repo.get_paginated(page=2, per_page=10)
            print(f"Showing {len(users)} of {total} users")
        """
        skip = (page - 1) * per_page
        items = self.get_all(filters=filters, skip=skip, limit=per_page, sort=sort)
        total = self.count(filters=filters)
        return items, total