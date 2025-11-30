"""
Path: src/database/adapters/arango_adapter.py
Version: 3

ArangoDB implementation of IDatabase interface
Provides full CRUD operations for ArangoDB document store

Changes in v3:
- ARCHITECTURE: Added DB-to-Service layer mapping
- Added _map_to_service(): converts _key -> id, removes _id/_rev
- Added _map_to_db(): semantic mapping (id -> _key lookup)
- Modified create(): returns documents with 'id' instead of '_key'
- Modified get_by_id(): accepts 'id', returns with 'id'
- Modified get_all(): returns all documents with 'id'
- Modified update(): accepts 'id', returns with 'id'
- Modified delete(): accepts 'id' for deletion
- Service layer now uses 'id' everywhere, DB internals use '_key'

Changes in v2:
- Added _serialize_document() method for datetime to ISO string conversion
- Modified create() to serialize datetime objects before insertion
- Modified update() to serialize datetime objects before update
- Import datetime module
"""

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import (
    DocumentInsertError,
    DocumentGetError,
    DocumentUpdateError,
    DocumentDeleteError,
    AQLQueryExecuteError,
)

from src.core.config import settings
from src.database.interface import IDatabase
from src.database.exceptions import (
    DatabaseException,
    NotFoundError,
    DuplicateKeyError,
    ConnectionError,
    QueryError,
    CollectionNotFoundError,
)

logger = logging.getLogger(__name__)


class ArangoDatabaseAdapter(IDatabase):
    """
    ArangoDB implementation of database interface
    
    Provides document-oriented storage using ArangoDB.
    Implements all IDatabase methods with ArangoDB-specific logic.
    
    Connection details configured via environment variables:
        - ARANGO_HOST
        - ARANGO_PORT
        - ARANGO_DATABASE
        - ARANGO_USER
        - ARANGO_PASSWORD
    
    Example:
        db = ArangoDatabaseAdapter()
        db.connect()
        
        user = db.create("users", {"name": "John", "email": "john@example.com"})
        all_users = db.get_all("users", filters={"status": "active"})
    """
    
    def __init__(self):
        """Initialize adapter (connection not established yet)"""
        self._client: Optional[ArangoClient] = None
        self._db: Optional[StandardDatabase] = None
        self._connected: bool = False
    
    def connect(self) -> None:
        """
        Establish connection to ArangoDB
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Create ArangoDB client
            self._client = ArangoClient(
                hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}"
            )
            
            # Connect to database
            self._db = self._client.db(
                settings.ARANGO_DATABASE,
                username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD
            )
            
            # Test connection
            self._db.version()
            
            self._connected = True
            logger.info(
                f"Connected to ArangoDB: {settings.ARANGO_HOST}:{settings.ARANGO_PORT}/"
                f"{settings.ARANGO_DATABASE}"
            )
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            raise ConnectionError(f"ArangoDB connection failed: {str(e)}")
    
    def disconnect(self) -> None:
        """Close ArangoDB connection"""
        if self._connected:
            self._client = None
            self._db = None
            self._connected = False
            logger.info("Disconnected from ArangoDB")
    
    def _ensure_connected(self) -> None:
        """Ensure database is connected before operations"""
        if not self._connected or self._db is None:
            raise ConnectionError("Database not connected. Call connect() first.")
    
    def _get_collection(self, collection: str):
        """
        Get collection object
        
        Args:
            collection: Collection name
            
        Returns:
            ArangoDB collection object
            
        Raises:
            CollectionNotFoundError: If collection doesn't exist
        """
        self._ensure_connected()
        
        if not self._db.has_collection(collection):
            raise CollectionNotFoundError(f"Collection '{collection}' does not exist")
        
        return self._db.collection(collection)
    
    def _serialize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize document for ArangoDB storage
        
        Converts datetime objects to ISO format strings recursively.
        
        Args:
            document: Document to serialize
            
        Returns:
            Serialized document
        """
        serialized = {}
        for key, value in document.items():
            if isinstance(value, datetime):
                # Convert datetime to ISO string
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                # Recursively serialize nested dicts
                serialized[key] = self._serialize_document(value)
            elif isinstance(value, list):
                # Serialize list items
                serialized[key] = [
                    self._serialize_document(item) if isinstance(item, dict)
                    else item.isoformat() if isinstance(item, datetime)
                    else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized
    
    def _map_to_service(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map database document to service layer format
        
        Converts ArangoDB internal fields (_key, _id, _rev) to API format (id).
        This ensures the service layer only works with 'id', not '_key'.
        
        Args:
            document: Document from ArangoDB (with _key, _id, _rev)
            
        Returns:
            Document with 'id' field instead of '_key'
        """
        if not document:
            return document
        
        mapped = document.copy()
        
        # Map _key to id (API format)
        if '_key' in mapped:
            mapped['id'] = mapped.pop('_key')
        
        # Remove ArangoDB internal fields
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
        # ID and _key are the same value, just semantic mapping
        return doc_id
    
    def create(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document in ArangoDB
        
        Args:
            collection: Collection name
            document: Document data
            
        Returns:
            Created document with 'id' (mapped from _key)
            
        Raises:
            DuplicateKeyError: If unique constraint violated
            DatabaseException: If creation fails
        """
        try:
            col = self._get_collection(collection)
            
            # Serialize datetime objects to ISO strings
            serialized_doc = self._serialize_document(document)
            
            result = col.insert(serialized_doc, return_new=True)
            
            logger.debug(f"Created document in {collection}: {result['_key']}")
            
            # Map _key to id for service layer
            return self._map_to_service(result['new'])
            
        except DocumentInsertError as e:
            # Check if duplicate key error
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                raise DuplicateKeyError(f"Duplicate key in {collection}: {str(e)}")
            raise DatabaseException(f"Failed to create document in {collection}: {str(e)}")
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Unexpected error creating document: {str(e)}")
    
    def get_by_id(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            collection: Collection name
            doc_id: Document ID (mapped to _key internally)
            
        Returns:
            Document dict with 'id' or None if not found
        """
        try:
            col = self._get_collection(collection)
            
            # Map service ID to database _key
            db_key = self._map_to_db(doc_id)
            doc = col.get(db_key)
            
            if doc:
                logger.debug(f"Retrieved document from {collection}: {doc_id}")
                # Map _key to id for service layer
                return self._map_to_service(doc)
            
            return None
            
        except DocumentGetError:
            return None
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"Error getting document {doc_id} from {collection}: {e}")
            return None
    
    def get_all(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents with optional filters, pagination, and sorting
        
        Args:
            collection: Collection name
            filters: Query filters (e.g., {"status": "active"})
            skip: Number to skip
            limit: Maximum to return
            sort: Sort specification (e.g., {"createdAt": -1})
            
        Returns:
            List of documents
        """
        try:
            self._ensure_connected()
            
            # Build AQL query
            query_parts = [f"FOR doc IN {collection}"]
            bind_vars = {}
            
            # Add filters
            if filters:
                filter_conditions = []
                for i, (key, value) in enumerate(filters.items()):
                    param_name = f"filter_{i}"
                    filter_conditions.append(f"doc.{key} == @{param_name}")
                    bind_vars[param_name] = value
                
                query_parts.append("FILTER " + " AND ".join(filter_conditions))
            
            # Add sort
            if sort:
                sort_clauses = []
                for field, direction in sort.items():
                    sort_dir = "ASC" if direction >= 0 else "DESC"
                    sort_clauses.append(f"doc.{field} {sort_dir}")
                query_parts.append("SORT " + ", ".join(sort_clauses))
            
            # Add pagination
            query_parts.append(f"LIMIT {skip}, {limit}")
            query_parts.append("RETURN doc")
            
            query = " ".join(query_parts)
            
            # Execute query
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
            
            logger.debug(
                f"Retrieved {len(results)} documents from {collection} "
                f"(skip={skip}, limit={limit})"
            )
            
            # Map all documents from _key to id
            return [self._map_to_service(doc) for doc in results]
            
        except AQLQueryExecuteError as e:
            raise QueryError(f"AQL query failed: {str(e)}")
        except Exception as e:
            raise DatabaseException(f"Error retrieving documents: {str(e)}")
    
    def update(
        self,
        collection: str,
        doc_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update document with partial data
        
        Args:
            collection: Collection name
            doc_id: Document ID (mapped to _key internally)
            updates: Fields to update
            
        Returns:
            Updated document with 'id'
            
        Raises:
            NotFoundError: If document not found
            DatabaseException: If update fails
        """
        try:
            col = self._get_collection(collection)
            
            # Map service ID to database _key
            db_key = self._map_to_db(doc_id)
            
            # Check if document exists
            if not col.has(db_key):
                raise NotFoundError(f"Document {doc_id} not found in {collection}")
            
            # Serialize datetime objects to ISO strings
            serialized_updates = self._serialize_document(updates)
            
            # Update document (merge updates, don't replace)
            result = col.update(
                {"_key": db_key, **serialized_updates},
                return_new=True,
                merge=True
            )
            
            logger.debug(f"Updated document in {collection}: {doc_id}")
            
            # Map _key to id for service layer
            return self._map_to_service(result['new'])
            
        except NotFoundError:
            raise
        except DocumentUpdateError as e:
            if "not found" in str(e).lower():
                raise NotFoundError(f"Document {doc_id} not found in {collection}")
            raise DatabaseException(f"Failed to update document: {str(e)}")
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Unexpected error updating document: {str(e)}")
    
    def delete(self, collection: str, doc_id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            collection: Collection name
            doc_id: Document ID (mapped to _key internally)
            
        Returns:
            True if deleted, False if not found
        """
        try:
            col = self._get_collection(collection)
            
            # Map service ID to database _key
            db_key = self._map_to_db(doc_id)
            
            # Check if exists
            if not col.has(db_key):
                logger.debug(f"Document {doc_id} not found in {collection}")
                return False
            
            # Delete
            col.delete(db_key)
            logger.debug(f"Deleted document from {collection}: {doc_id}")
            return True
            
        except DocumentDeleteError as e:
            logger.warning(f"Error deleting document {doc_id}: {e}")
            return False
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting document: {e}")
            return False
    
    def find_one(
        self,
        collection: str,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find first document matching filters
        
        Args:
            collection: Collection name
            filters: Query filters
            
        Returns:
            First matching document or None
        """
        try:
            results = self.get_all(collection, filters=filters, limit=1)
            return results[0] if results else None
            
        except Exception as e:
            logger.warning(f"Error in find_one: {e}")
            return None
    
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
        
        Alias for get_all() with filters required
        """
        return self.get_all(collection, filters=filters, skip=skip, limit=limit, sort=sort)
    
    def count(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents in collection
        
        Args:
            collection: Collection name
            filters: Optional query filters
            
        Returns:
            Number of matching documents
        """
        try:
            self._ensure_connected()
            
            # Build AQL query
            query_parts = [f"FOR doc IN {collection}"]
            bind_vars = {}
            
            # Add filters
            if filters:
                filter_conditions = []
                for i, (key, value) in enumerate(filters.items()):
                    param_name = f"filter_{i}"
                    filter_conditions.append(f"doc.{key} == @{param_name}")
                    bind_vars[param_name] = value
                
                query_parts.append("FILTER " + " AND ".join(filter_conditions))
            
            query_parts.append("COLLECT WITH COUNT INTO length RETURN length")
            query = " ".join(query_parts)
            
            # Execute query
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            count = next(cursor, 0)
            
            logger.debug(f"Counted {count} documents in {collection}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def exists(self, collection: str, doc_id: str) -> bool:
        """Check if document exists"""
        try:
            col = self._get_collection(collection)
            return col.has(doc_id)
        except CollectionNotFoundError:
            return False
        except Exception:
            return False
    
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
            collection: Collection name
            fields: List of field names
            unique: Enforce uniqueness
            sparse: Index only non-null values
        """
        try:
            col = self._get_collection(collection)
            
            # Determine index type
            if len(fields) == 1:
                # Hash index for single field
                col.add_hash_index(
                    fields=fields,
                    unique=unique,
                    sparse=sparse
                )
            else:
                # Persistent index for compound
                col.add_persistent_index(
                    fields=fields,
                    unique=unique,
                    sparse=sparse
                )
            
            logger.info(
                f"Created index on {collection}.{fields} "
                f"(unique={unique}, sparse={sparse})"
            )
            
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to create index: {str(e)}")
    
    def drop_index(self, collection: str, index_name: str) -> None:
        """Drop index from collection"""
        try:
            col = self._get_collection(collection)
            col.delete_index(index_name)
            logger.info(f"Dropped index {index_name} from {collection}")
            
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to drop index: {str(e)}")
    
    def collection_exists(self, collection: str) -> bool:
        """Check if collection exists"""
        try:
            self._ensure_connected()
            return self._db.has_collection(collection)
        except Exception:
            return False
    
    def create_collection(self, collection: str) -> None:
        """Create new collection"""
        try:
            self._ensure_connected()
            
            if self._db.has_collection(collection):
                raise DatabaseException(f"Collection '{collection}' already exists")
            
            self._db.create_collection(collection)
            logger.info(f"Created collection: {collection}")
            
        except DatabaseException:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to create collection: {str(e)}")
    
    def drop_collection(self, collection: str) -> None:
        """Drop collection (WARNING: Deletes all data)"""
        try:
            self._ensure_connected()
            
            if not self._db.has_collection(collection):
                raise CollectionNotFoundError(f"Collection '{collection}' does not exist")
            
            self._db.delete_collection(collection)
            logger.warning(f"Dropped collection: {collection}")
            
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to drop collection: {str(e)}")
    
    def truncate_collection(self, collection: str) -> None:
        """Remove all documents from collection"""
        try:
            col = self._get_collection(collection)
            col.truncate()
            logger.info(f"Truncated collection: {collection}")
            
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to truncate collection: {str(e)}")