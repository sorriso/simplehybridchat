"""
Path: backend/src/database/interface.py
Version: 2

Changes in v2:
- Fixed docstring example: doc["_key"] â†’ doc["id"]
- Documentation now reflects actual adapter behavior

Abstract database interface defining contract for all database adapters
This interface ensures database implementation can be swapped without changing application code
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IDatabase(ABC):
    """
    Abstract interface for database operations
    
    All database adapters must implement this interface to ensure
    consistent behavior across different database technologies.
    
    Implementations:
        - ArangoDatabaseAdapter: ArangoDB document store
        - MongoDatabaseAdapter: MongoDB document store (future)
        - PostgresDatabaseAdapter: PostgreSQL relational (future)
    
    Usage:
        db = get_database()  # Returns configured adapter
        doc = db.create("users", {"name": "John"})
        user = db.get_by_id("users", doc["id"])
    """
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish database connection
        
        Called once during initialization by factory.
        Should handle connection pooling, authentication, etc.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close database connection
        
        Should cleanup resources, close connections, etc.
        Called during application shutdown.
        """
        pass
    
    @abstractmethod
    def create(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in collection
        
        Args:
            collection: Collection/table name
            document: Document data to insert
            
        Returns:
            Created document with generated ID (_key, _id, id, etc.)
            
        Raises:
            DatabaseException: If creation fails
            DuplicateKeyError: If unique constraint violated
            
        Example:
            user = db.create("users", {
                "name": "John Doe",
                "email": "john@example.com",
                "role": "user"
            })
            # Returns: {"id": "abc123", "name": "John Doe", ...}
        """
        pass
    
    @abstractmethod
    def get_by_id(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            collection: Collection/table name
            doc_id: Document identifier (_key, _id, id, etc.)
            
        Returns:
            Document dict if found, None otherwise
            
        Example:
            user = db.get_by_id("users", "abc123")
            if user:
                print(user["name"])
        """
        pass
    
    @abstractmethod
    def get_all(
        self, 
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents with optional filters and pagination
        
        Args:
            collection: Collection/table name
            filters: Query filters as dict (e.g., {"status": "active", "role": "user"})
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return
            sort: Sort specification as dict (e.g., {"createdAt": -1} for descending)
            
        Returns:
            List of matching documents
            
        Example:
            # Get active users, skip first 20, limit to 10, sorted by creation date
            users = db.get_all(
                "users",
                filters={"status": "active"},
                skip=20,
                limit=10,
                sort={"createdAt": -1}
            )
        """
        pass
    
    @abstractmethod
    def update(
        self, 
        collection: str, 
        doc_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update document with partial data
        
        Args:
            collection: Collection/table name
            doc_id: Document identifier
            updates: Fields to update (partial update, not replacement)
            
        Returns:
            Updated document with all fields
            
        Raises:
            NotFoundError: If document with doc_id doesn't exist
            DatabaseException: If update fails
            
        Example:
            updated_user = db.update("users", "abc123", {
                "status": "disabled",
                "lastModified": "2024-01-15T10:00:00Z"
            })
            # Only updates specified fields, keeps others unchanged
        """
        pass
    
    @abstractmethod
    def delete(self, collection: str, doc_id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            collection: Collection/table name
            doc_id: Document identifier
            
        Returns:
            True if document was deleted, False if not found
            
        Example:
            deleted = db.delete("users", "abc123")
            if deleted:
                print("User deleted successfully")
        """
        pass
    
    @abstractmethod
    def find_one(
        self, 
        collection: str, 
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find first document matching filters
        
        Args:
            collection: Collection/table name
            filters: Query filters
            
        Returns:
            First matching document or None if no match
            
        Example:
            user = db.find_one("users", {"email": "john@example.com"})
            if user:
                print(f"Found user: {user['name']}")
        """
        pass
    
    @abstractmethod
    def find_many(
        self,
        collection: str,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching filters
        
        Alias for get_all() with filters required.
        
        Args:
            collection: Collection/table name
            filters: Query filters (required)
            skip: Number to skip
            limit: Maximum to return
            sort: Sort specification
            
        Returns:
            List of matching documents
            
        Example:
            active_users = db.find_many(
                "users",
                {"status": "active", "role": "user"},
                limit=50
            )
        """
        pass
    
    @abstractmethod
    def count(
        self, 
        collection: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents in collection
        
        Args:
            collection: Collection/table name
            filters: Optional query filters
            
        Returns:
            Number of matching documents
            
        Example:
            total_users = db.count("users")
            active_users = db.count("users", {"status": "active"})
        """
        pass
    
    @abstractmethod
    def exists(self, collection: str, doc_id: str) -> bool:
        """
        Check if document exists
        
        Args:
            collection: Collection/table name
            doc_id: Document identifier
            
        Returns:
            True if document exists, False otherwise
            
        Example:
            if db.exists("users", "abc123"):
                print("User exists")
        """
        pass
    
    @abstractmethod
    def create_index(
        self, 
        collection: str, 
        fields: List[str],
        unique: bool = False,
        sparse: bool = False
    ) -> None:
        """
        Create index on fields
        
        Args:
            collection: Collection/table name
            fields: List of field names to index
            unique: If True, enforce uniqueness constraint
            sparse: If True, index only documents with field present
            
        Raises:
            DatabaseException: If index creation fails
            
        Example:
            # Create unique index on email
            db.create_index("users", ["email"], unique=True)
            
            # Create compound index
            db.create_index("users", ["status", "createdAt"])
        """
        pass
    
    @abstractmethod
    def drop_index(self, collection: str, index_name: str) -> None:
        """
        Drop index from collection
        
        Args:
            collection: Collection/table name
            index_name: Name of index to drop
            
        Raises:
            DatabaseException: If index doesn't exist or drop fails
        """
        pass
    
    @abstractmethod
    def collection_exists(self, collection: str) -> bool:
        """
        Check if collection exists
        
        Args:
            collection: Collection/table name
            
        Returns:
            True if collection exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_collection(self, collection: str) -> None:
        """
        Create new collection/table
        
        Args:
            collection: Collection/table name
            
        Raises:
            DatabaseException: If collection already exists or creation fails
        """
        pass
    
    @abstractmethod
    def drop_collection(self, collection: str) -> None:
        """
        Drop collection/table
        
        WARNING: This permanently deletes all data in collection
        
        Args:
            collection: Collection/table name
            
        Raises:
            DatabaseException: If collection doesn't exist or drop fails
        """
        pass
    
    @abstractmethod
    def truncate_collection(self, collection: str) -> None:
        """
        Remove all documents from collection but keep collection structure
        
        Args:
            collection: Collection/table name
            
        Raises:
            DatabaseException: If truncate fails
            
        Example:
            # Clear all users but keep collection and indexes
            db.truncate_collection("users")
        """
        pass