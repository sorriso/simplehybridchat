"""
Path: backend/tests/unit/mocks/mock_database.py
Version: 5

In-memory mock database for testing
Implements IDatabase interface without requiring actual database connection

Changes in v5:
- FIX: LIMIT clause now correctly handles @param bind variables
- FIX: Sort comparison handles mixed types (int/str) safely
- FIX: Priority sorting now casts to int for proper comparison

Changes in v4:
- ADDED: MockAQL class to simulate AQL query execution
- ADDED: aql property returning MockAQL instance

Changes in v3:
- BEHAVIOR: Auto-add created_at/updated_at for 'users' collection
"""

from typing import Optional, List, Dict, Any, Iterator
import copy
import re

from src.database.interface import IDatabase
from src.database.exceptions import (
    NotFoundError,
    DuplicateKeyError,
    CollectionNotFoundError,
)


class MockAQLCursor:
    """Mock AQL cursor that iterates over results"""
    
    def __init__(self, results: List[Any]):
        self._results = results
        self._index = 0
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self._results)
    
    def __next__(self) -> Any:
        if self._index >= len(self._results):
            raise StopIteration
        result = self._results[self._index]
        self._index += 1
        return result
    
    def batch(self) -> List[Any]:
        return self._results


class MockAQL:
    """
    Mock AQL query executor
    
    Simulates basic AQL query execution for testing.
    Supports common patterns used in repositories.
    """
    
    def __init__(self, database: 'MockDatabase'):
        self._db = database
    
    def execute(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None
    ) -> MockAQLCursor:
        """Execute AQL query and return cursor"""
        bind_vars = bind_vars or {}
        query_upper = query.upper().strip()
        
        # Handle REMOVE operations (DELETE)
        if "REMOVE" in query_upper:
            return self._execute_remove(query, bind_vars)
        
        # Handle SELECT-style queries (FOR ... RETURN)
        if query_upper.startswith("FOR"):
            return self._execute_select(query, bind_vars)
        
        return MockAQLCursor([])
    
    def _execute_select(
        self,
        query: str,
        bind_vars: Dict[str, Any]
    ) -> MockAQLCursor:
        """Execute SELECT-style query (FOR ... RETURN)"""
        # Extract collection name from "FOR doc IN collection"
        match = re.search(r'FOR\s+(\w+)\s+IN\s+(\w+)', query, re.IGNORECASE)
        if not match:
            return MockAQLCursor([])
        
        var_name = match.group(1)
        collection = match.group(2)
        
        if collection not in self._db.collections:
            return MockAQLCursor([])
        
        docs = [copy.deepcopy(doc) for doc in self._db.collections[collection].values()]
        docs = self._apply_filters(query, docs, var_name, bind_vars)
        docs = self._apply_sort(query, docs, var_name)
        docs = self._apply_limit(query, docs, bind_vars)
        docs = [self._db._map_to_service(doc) for doc in docs]
        
        return MockAQLCursor(docs)
    
    def _execute_remove(
        self,
        query: str,
        bind_vars: Dict[str, Any]
    ) -> MockAQLCursor:
        """Execute REMOVE query (DELETE)"""
        match = re.search(r'FOR\s+(\w+)\s+IN\s+(\w+)', query, re.IGNORECASE)
        if not match:
            return MockAQLCursor([])
        
        var_name = match.group(1)
        collection = match.group(2)
        
        if collection not in self._db.collections:
            return MockAQLCursor([])
        
        docs = list(self._db.collections[collection].values())
        docs = self._apply_filters(query, docs, var_name, bind_vars)
        
        removed = []
        for doc in docs:
            doc_key = doc.get("_key")
            if doc_key and doc_key in self._db.collections[collection]:
                del self._db.collections[collection][doc_key]
                removed.append(1)
        
        return MockAQLCursor(removed)
    
    def _apply_filters(
        self,
        query: str,
        docs: List[Dict],
        var_name: str,
        bind_vars: Dict[str, Any]
    ) -> List[Dict]:
        """Apply FILTER clauses to documents"""
        # Pattern: FILTER var.field == @param
        filter_pattern = rf'FILTER\s+{var_name}\.(\w+)\s*(==|!=|>|<|>=|<=)\s*@(\w+)'
        
        for match in re.finditer(filter_pattern, query, re.IGNORECASE):
            field = match.group(1)
            operator = match.group(2)
            param_name = match.group(3)
            
            if param_name not in bind_vars:
                continue
            
            value = bind_vars[param_name]
            filtered = []
            
            for doc in docs:
                doc_value = doc.get(field)
                
                if operator == "==":
                    if doc_value == value:
                        filtered.append(doc)
                elif operator == "!=":
                    if doc_value != value:
                        filtered.append(doc)
                elif operator == ">":
                    if doc_value is not None and doc_value > value:
                        filtered.append(doc)
                elif operator == "<":
                    if doc_value is not None and doc_value < value:
                        filtered.append(doc)
                elif operator == ">=":
                    if doc_value is not None and doc_value >= value:
                        filtered.append(doc)
                elif operator == "<=":
                    if doc_value is not None and doc_value <= value:
                        filtered.append(doc)
            
            docs = filtered
        
        # Handle status IN [...] pattern
        status_in_pattern = rf'{var_name}\.status\s+IN\s+\[(.*?)\]'
        match = re.search(status_in_pattern, query, re.IGNORECASE)
        if match:
            statuses_str = match.group(1)
            statuses = [s.strip().strip('"\'') for s in statuses_str.split(',')]
            docs = [doc for doc in docs if doc.get("status") in statuses]
        
        return docs
    
    def _safe_sort_key(self, doc: Dict, field: str) -> tuple:
        """
        Create a sort key that handles None and mixed types safely.
        
        Returns tuple: (is_none, numeric_value, string_value)
        - is_none: True if value is None (sorts last)
        - numeric_value: int/float for numeric comparison
        - string_value: string for string comparison
        """
        value = doc.get(field)
        
        if value is None:
            return (True, 0, "")
        
        # Try to convert to number for numeric fields like priority
        if isinstance(value, (int, float)):
            return (False, value, "")
        
        # Try to parse as number
        try:
            numeric = float(value)
            return (False, numeric, "")
        except (ValueError, TypeError):
            pass
        
        # Fall back to string comparison
        return (False, 0, str(value))
    
    def _apply_sort(
        self,
        query: str,
        docs: List[Dict],
        var_name: str
    ) -> List[Dict]:
        """Apply SORT clauses to documents"""
        sort_pattern = rf'SORT\s+{var_name}\.(\w+)\s*(ASC|DESC)?(?:\s*,\s*{var_name}\.(\w+)\s*(ASC|DESC)?)?'
        match = re.search(sort_pattern, query, re.IGNORECASE)
        
        if not match:
            return docs
        
        sorts = []
        field1 = match.group(1)
        dir1 = (match.group(2) or "ASC").upper()
        sorts.append((field1, dir1 == "DESC"))
        
        if match.group(3):
            field2 = match.group(3)
            dir2 = (match.group(4) or "ASC").upper()
            sorts.append((field2, dir2 == "DESC"))
        
        # Apply sorts in reverse order (last sort first for stable multi-key sort)
        for field, reverse in reversed(sorts):
            docs.sort(
                key=lambda d, f=field: self._safe_sort_key(d, f),
                reverse=reverse
            )
        
        return docs
    
    def _apply_limit(
        self,
        query: str,
        docs: List[Dict],
        bind_vars: Dict[str, Any]
    ) -> List[Dict]:
        """Apply LIMIT clause to documents"""
        # Pattern 1: LIMIT @param (bind variable)
        limit_bind_pattern = r'LIMIT\s+@(\w+)'
        match = re.search(limit_bind_pattern, query, re.IGNORECASE)
        if match:
            param_name = match.group(1)
            if param_name in bind_vars:
                limit_value = bind_vars[param_name]
                if isinstance(limit_value, int) and limit_value > 0:
                    return docs[:limit_value]
            return docs
        
        # Pattern 2: LIMIT N or LIMIT skip, count (literal numbers)
        limit_pattern = r'LIMIT\s+(\d+)(?:\s*,\s*(\d+))?'
        match = re.search(limit_pattern, query, re.IGNORECASE)
        
        if not match:
            return docs
        
        if match.group(2):
            skip = int(match.group(1))
            count = int(match.group(2))
        else:
            skip = 0
            count = int(match.group(1))
        
        return docs[skip:skip + count]


class MockDatabase(IDatabase):
    """In-memory mock database for testing"""
    
    def __init__(self):
        self.collections: Dict[str, Dict[str, dict]] = {}
        self.indexes: Dict[str, List[Dict[str, Any]]] = {}
        self._counter = 0
        self._connected = False
        self._aql = MockAQL(self)
    
    @property
    def aql(self) -> MockAQL:
        """Get AQL query executor"""
        return self._aql
    
    def connect(self) -> None:
        self._connected = True
    
    def disconnect(self) -> None:
        self.collections = {}
        self.indexes = {}
        self._counter = 0
        self._connected = False
    
    def _ensure_collection_exists(self, collection: str) -> None:
        if collection not in self.collections:
            self.collections[collection] = {}
            self.indexes[collection] = []
    
    def _generate_id(self) -> str:
        self._counter += 1
        return f"mock-{self._counter}"
    
    def _map_to_service(self, document: Dict[str, Any]) -> Dict[str, Any]:
        if not document:
            return document
        
        mapped = document.copy()
        if '_key' in mapped:
            mapped['id'] = mapped.pop('_key')
        mapped.pop('_id', None)
        mapped.pop('_rev', None)
        return mapped
    
    def _map_to_db(self, doc_id: str) -> str:
        return doc_id
    
    def _check_unique_constraints(self, collection: str, document: Dict[str, Any]) -> None:
        if collection not in self.indexes:
            return
        
        for index in self.indexes[collection]:
            if not index.get("unique"):
                continue
            
            for doc_id, existing_doc in self.collections[collection].items():
                match = True
                for field in index["fields"]:
                    if document.get(field) != existing_doc.get(field):
                        match = False
                        break
                
                if match and document.get("_key") != doc_id:
                    raise DuplicateKeyError(
                        f"Duplicate key on fields {index['fields']}"
                    )
    
    def create(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_collection_exists(collection)
        
        doc_copy = copy.deepcopy(document)
        if "_key" not in doc_copy:
            doc_copy["_key"] = self._generate_id()
        
        doc_id = doc_copy["_key"]
        
        if collection == "users":
            if "created_at" not in doc_copy:
                from datetime import datetime
                doc_copy["created_at"] = datetime.utcnow()
            if "updated_at" not in doc_copy:
                doc_copy["updated_at"] = None
        
        self._check_unique_constraints(collection, doc_copy)
        
        doc_copy["_id"] = f"{collection}/{doc_id}"
        doc_copy["_rev"] = "1"
        
        self.collections[collection][doc_id] = doc_copy
        return self._map_to_service(copy.deepcopy(doc_copy))
    
    def get_by_id(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        if collection not in self.collections:
            return None
        
        db_key = self._map_to_db(doc_id)
        doc = self.collections[collection].get(db_key)
        
        if doc:
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
        if collection not in self.collections:
            return []
        
        docs = list(self.collections[collection].values())
        
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
        
        if sort:
            for field, direction in reversed(list(sort.items())):
                reverse = direction < 0
                docs.sort(key=lambda d: d.get(field, ""), reverse=reverse)
        
        docs = docs[skip:skip + limit]
        return [self._map_to_service(copy.deepcopy(doc)) for doc in docs]
    
    def update(
        self,
        collection: str,
        doc_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        if collection not in self.collections:
            raise NotFoundError(f"Collection '{collection}' not found")
        
        db_key = self._map_to_db(doc_id)
        
        if db_key not in self.collections[collection]:
            raise NotFoundError(f"Document '{doc_id}' not found in {collection}")
        
        doc = self.collections[collection][db_key]
        updated_doc = {**doc, **updates, "_key": db_key}
        self._check_unique_constraints(collection, updated_doc)
        
        rev_num = int(updated_doc.get("_rev", "1")) + 1
        updated_doc["_rev"] = str(rev_num)
        
        self.collections[collection][db_key] = updated_doc
        return self._map_to_service(copy.deepcopy(updated_doc))
    
    def delete(self, collection: str, doc_id: str) -> bool:
        if collection not in self.collections:
            return False
        
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
        return self.get_all(collection, filters=filters, skip=skip, limit=limit, sort=sort)
    
    def count(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        if collection not in self.collections:
            return 0
        
        if not filters:
            return len(self.collections[collection])
        
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
        if collection not in self.collections:
            return False
        db_key = self._map_to_db(doc_id)
        return db_key in self.collections[collection]
    
    def create_index(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        sparse: bool = False
    ) -> None:
        self._ensure_collection_exists(collection)
        self.indexes[collection].append({
            "fields": fields,
            "unique": unique,
            "sparse": sparse,
        })
    
    def drop_index(self, collection: str, index_name: str) -> None:
        pass
    
    def collection_exists(self, collection: str) -> bool:
        return collection in self.collections
    
    def create_collection(self, collection: str) -> None:
        if collection in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' already exists")
        self.collections[collection] = {}
        self.indexes[collection] = []
    
    def drop_collection(self, collection: str) -> None:
        if collection not in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' not found")
        del self.collections[collection]
        if collection in self.indexes:
            del self.indexes[collection]
    
    def truncate_collection(self, collection: str) -> None:
        if collection not in self.collections:
            raise CollectionNotFoundError(f"Collection '{collection}' not found")
        self.collections[collection] = {}
    
    def reset(self) -> None:
        self.collections = {}
        self.indexes = {}
        self._counter = 0