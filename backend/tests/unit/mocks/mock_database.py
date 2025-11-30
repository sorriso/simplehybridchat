"""
Path: tests/unit/mocks/mock_database.py
Version: 3

In-memory mock database for testing
Implements IDatabase interface without requiring actual database connection

Changes in v3:
- BEHAVIOR: Auto-add created_at/updated_at for 'users' collection
- Matches production behavior where timestamps are auto-generated
- Fixes ValidationError in tests (UserResponse requires created_at)

Changes in v2:
- ARCHITECTURE: Added DB-to-Service layer mapping (matches ArangoDatabaseAdapter)
- Added _map_to_service(): converts _key -> id, removes _id/_rev
- Added _map_to_db(): mapping id -> _key
- Modified create(): returns documents with 'id' instead of '_key'
- Modified get_by_id(): accepts 'id', returns with 'id'
- Modified get_all(): returns all documents with 'id'
- Modified update(): accepts 'id', returns with 'id'
- Modified delete(): accepts 'id'
- Modified exists(): accepts 'id'
"""

from typing import Optional, List, Dict, Any
import copy

from src.database.interface import IDatabase
from src.database.exceptions import (
    NotFoundError,
    DuplicateKeyError,
    CollectionNotFoundError,
)


class MockDatabase(IDatabase):
    """
    In-memory mock database for testing
    
    Stores data in dictionaries, simulates database behavior.
    Useful for unit tests without requiring actual database.
    
    Example:
        # In tests
        mock_db = MockDatabase()
        mock_db.connect()
        
        # Inject into repository
        user_repo = UserRepository(db=mock_db)
        
        # Test operations
        user = user_repo.create({"name": "Test"})
        assert user["name"] == "Test"
    """
    
    def __init__(self):
        """Initialize empty mock database"""
        self.collections: Dict[str, Dict[str, dict]] = {}
        self.indexes: Dict[str, List[Dict[str, Any]]] = {}
        self._counter = 0
        self._connected = False
    
    def connect(self) -> None:
        """Mock connection (no-op)"""
        self._connected = True
    
    def disconnect(self) -> None:
        """Mock disconnection (clears data)"""
        self.collections = {}
        self.indexes = {}
        self._counter = 0
        self._connected = False
    
    def _ensure_collection_exists(self, collection: str) -> None:
        """Ensure collection exists, create if not"""
        if collection not in self.collections:
            self.collections[collection] = {}
            self.indexes[collection] = []
    
    def _generate_id(self) -> str:
        """Generate unique document ID"""
        self._counter += 1
        return f"mock-{self._counter}"
    
    def _map_to_service(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map database document to service layer format
        
        Converts internal fields (_key, _id, _rev) to API format (id).
        Matches behavior of ArangoDatabaseAdapter.
        
        Args:
            document: Document from mock DB (with _key, _id, _rev)
            
        Returns:
            Document with 'id' field instead of '_key'
        """
        if not document:
            return document
        
        mapped = document.copy()
        
        # Map _key to id (API format)
        if '_key' in mapped:
            mapped['id'] = mapped.pop('_key')
        
        # Remove internal fields
        mapped.pop('_id', None)
        mapped.pop('_rev', None)
        
        return mapped
    
    def _map_to_db(self, doc_id: str) -> str:
        """
        Map service layer ID to database key
        
        Args:
            doc_id: Document ID from service layer
            
        Returns:
            Database key (_key format)
        """
        # ID and _key are the same value
        return doc_id
    
    def _check_unique_constraints(self, collection: str, document: Dict[str, Any]) -> None:
        """
        Check if document violates unique indexes
        
        Raises:
            DuplicateKeyError: If unique constraint violated
        """
        if collection not in self.indexes:
            return
        
        for index in self.indexes[collection]:
            if not index.get("unique"):
                continue
            
            # Check if any existing document has same values for indexed fields
            for doc_id, existing_doc in self.collections[collection].items():
                match = True
                for field in index["fields"]:
                    if document.get(field) != existing_doc.get(field):
                        match = False
                        break
                
                if match and document.get("_key") != doc_id:
                    raise DuplicateKeyError(
                        f"Duplicate key on fields {index['fields']}: "
                        f"{[document.get(f) for f in index['fields']]}"
                    )
    
    def create(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create document in mock collection"""
        self._ensure_collection_exists(collection)
        
        # Generate ID if not provided
        doc_copy = copy.deepcopy(document)
        if "_key" not in doc_copy:
            doc_copy["_key"] = self._generate_id()
        
        doc_id = doc_copy["_key"]
        
        # Add timestamps for users collection if not present
        # This matches production behavior where DB adds timestamps
        if collection == "users":
            if "created_at" not in doc_copy:
                from datetime import datetime
                doc_copy["created_at"] = datetime.utcnow()
            if "updated_at" not in doc_copy:
                doc_copy["updated_at"] = None
        
        # Check unique constraints
        self._check_unique_constraints(collection, doc_copy)
        
        # Add metadata
        doc_copy["_id"] = f"{collection}/{doc_id}"
        doc_copy["_rev"] = "1"
        
        # Store
        self.collections[collection][doc_id] = doc_copy
        
        # Map to service format (id instead of _key)
        return self._map_to_service(copy.deepcopy(doc_copy))
    
    def get_by_id(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if collection not in self.collections:
            return None
        
        # Map service ID to database _key
        db_key = self._map_to_db(doc_id)
        doc = self.collections[collection].get(db_key)
        
        if doc:
            # Map to service format
            return self._map_to_service(copy.deepcopy(doc))
        
        return None
    
    def get_all(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents with filters, pagination, and sorting"""
        if collection not in self.collections:
            return []
        
        # Get all documents
        docs = list(self.collections[collection].values())
        
        # Apply filters
        if filters:
            filtered_docs = []
            for doc in docs:
                match = True
                for key, value in filters.items():
                    if doc.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
            docs = filtered_docs
        
        # Apply sort
        if sort:
            for field, direction in reversed(list(sort.items())):
                reverse = direction < 0
                docs.sort(
                    key=lambda d: d.get(field, ""),
                    reverse=reverse
                )
        
        # Apply pagination
        docs = docs[skip:skip + limit]
        
        # Map all documents to service format
        return [self._map_to_service(copy.deepcopy(doc)) for doc in docs]
    
    def update(
        self,
        collection: str,
        doc_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update document"""
        if collection not in self.collections:
            raise NotFoundError(f"Collection '{collection}' not found")
        
        # Map service ID to database _key
        db_key = self._map_to_db(doc_id)
        
        if db_key not in self.collections[collection]:
            raise NotFoundError(f"Document '{doc_id}' not found in {collection}")
        
        # Get existing document
        doc = self.collections[collection][db_key]
        
        # Merge updates
        updated_doc = {**doc, **updates, "_key": db_key}
        
        # Check unique constraints
        self._check_unique_constraints(collection, updated_doc)
        
        # Update revision
        rev_num = int(updated_doc.get("_rev", "1")) + 1
        updated_doc["_rev"] = str(rev_num)
        
        # Store
        self.collections[collection][db_key] = updated_doc
        
        # Map to service format
        return self._map_to_service(copy.deepcopy(updated_doc))
    
    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete document"""
        if collection not in self.collections:
            return False
        
        # Map service ID to database _key
        db_key = self._map_to_db(doc_id)
        
        if db_key in self.collections[collection]:
            del self.collections[collection][db_key]
            return True
        
        return False
    
    def find_one(
        self,
        collection: str,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find first document matching filters"""
        results = self.get_all(collection, filters=filters, limit=1)
        return results[0] if results else None
    
    def find_many(
        self,
        collection: str,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching filters"""
        return self.get_all(collection, filters=filters, skip=skip, limit=limit, sort=sort)
    
    def count(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count documents"""
        if collection not in self.collections:
            return 0
        
        if not filters:
            return len(self.collections[collection])
        
        # Count with filters
        count = 0
        for doc in self.collections[collection].values():
            match = True
            for key, value in filters.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        
        return count
    
    def exists(self, collection: str, doc_id: str) -> bool:
        """Check if document exists"""
        if collection not in self.collections:
            return False
        
        # Map service ID to database _key
        db_key = self._map_to_db(doc_id)
        return db_key in self.collections[collection]
    
    def create_index(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        sparse: bool = False
    ) -> None:
        """Create index (stored but not enforced except unique)"""
        self._ensure_collection_exists(collection)
        
        index = {
            "fields": fields,
            "unique": unique,
            "sparse": sparse,
        }
        
        self.indexes[collection].append(index)
    
    def drop_index(self, collection: str, index_name: str) -> None:
        """Drop index (mock - no-op)"""
        pass
    
    def collection_exists(self, collection: str) -> bool:
        """Check if collection exists"""
        return collection in self.collections
    
    def create_collection(self, collection: str) -> None:
        """Create collection"""
        if collection in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' already exists")
        
        self.collections[collection] = {}
        self.indexes[collection] = []
    
    def drop_collection(self, collection: str) -> None:
        """Drop collection"""
        if collection not in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' not found")
        
        del self.collections[collection]
        if collection in self.indexes:
            del self.indexes[collection]
    
    def truncate_collection(self, collection: str) -> None:
        """Clear all documents from collection"""
        if collection not in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' not found")
        
        self.collections[collection] = {}
    
    def reset(self) -> None:
        """
        Reset mock database to clean state
        
        Useful between tests to ensure isolation
        """
        self.collections = {}
        self.indexes = {}
        self._counter = 0