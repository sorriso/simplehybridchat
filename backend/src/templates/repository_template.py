"""
Path: backend/src/templates/repository_template.py
Version: 1

Generic CRUD Repository Template

Copy this template and replace:
- ResourceRepository -> YourResourceRepository (e.g., ConversationRepository)
- resource -> your_resource (e.g., conversation)
- resources -> your_resources (e.g., conversations)

This template provides:
- Full CRUD operations (create, read, update, delete)
- Search/filter capabilities
- Count operations
- Pagination support
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class ResourceRepository(BaseRepository):
    """
    Repository for managing resources
    
    Provides CRUD operations and queries for resources.
    Inherits common operations from BaseRepository.
    """
    
    def __init__(self, db=None):
        """
        Initialize repository with collection name
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        super().__init__(collection_name="resources", db=db)
    
    # ========================================================================
    # Basic CRUD - Inherited from BaseRepository
    # ========================================================================
    # - create(data: Dict[str, Any]) -> Dict[str, Any]
    # - get_by_id(id: str) -> Optional[Dict[str, Any]]
    # - get_all(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]
    # - update(id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]
    # - delete(id: str) -> bool
    # - exists(id: str) -> bool
    # - count() -> int
    
    # ========================================================================
    # Custom Query Methods
    # ========================================================================
    
    def get_by_field(self, field_name: str, field_value: Any) -> Optional[Dict[str, Any]]:
        """
        Get resource by specific field
        
        Example: get_by_field("email", "user@example.com")
        
        Args:
            field_name: Name of field to search
            field_value: Value to match
            
        Returns:
            Resource dict or None if not found
        """
        return self.db.find_one(self.collection_name, {field_name: field_value})
    
    def find_by_filters(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "created_at",
        sort_order: int = -1
    ) -> List[Dict[str, Any]]:
        """
        Find resources with multiple filters
        
        Example: find_by_filters({"status": "active", "type": "premium"})
        
        Args:
            filters: Dictionary of field:value filters
            skip: Number of results to skip (pagination)
            limit: Maximum results to return
            sort_field: Field to sort by
            sort_order: 1 for ascending, -1 for descending
            
        Returns:
            List of matching resources
        """
        return self.db.get_all(
            self.collection_name,
            filters=filters,
            skip=skip,
            limit=limit,
            sort={sort_field: sort_order}
        )
    
    def count_by_filter(self, filters: Dict[str, Any]) -> int:
        """
        Count resources matching filters
        
        Example: count_by_filter({"status": "active"})
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Count of matching resources
        """
        # For ArangoDB, we can use a custom query
        # For now, get all and count (inefficient but works)
        results = self.db.get_all(self.collection_name, filters=filters)
        return len(results)
    
    def get_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get resources owned by specific user
        
        Assumes resources have 'owner_id' or 'user_id' field.
        
        Args:
            owner_id: ID of owner
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of resources
        """
        return self.find_by_filters(
            filters={"owner_id": owner_id},
            skip=skip,
            limit=limit,
            sort_field="created_at",
            sort_order=-1
        )
    
    def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search resources across multiple fields
        
        Example: search("john", ["name", "email", "description"])
        
        Note: This is a simple implementation. For production,
        consider using full-text search capabilities of your database.
        
        Args:
            search_term: Term to search for
            search_fields: List of field names to search in
            skip: Pagination skip
            limit: Max results
            
        Returns:
            List of matching resources
        """
        # Simple implementation: get all and filter in Python
        # For production, use database-level search
        all_resources = self.db.get_all(self.collection_name, skip=skip, limit=limit * 10)
        
        results = []
        search_lower = search_term.lower()
        
        for resource in all_resources:
            for field in search_fields:
                if field in resource:
                    field_value = str(resource[field]).lower()
                    if search_lower in field_value:
                        results.append(resource)
                        break
        
        return results[:limit]
    
    def bulk_create(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple resources at once
        
        Args:
            resources: List of resource data dicts
            
        Returns:
            List of created resources with IDs
        """
        created = []
        for resource_data in resources:
            # Add timestamps
            resource_data["created_at"] = datetime.utcnow()
            resource_data["updated_at"] = None
            
            created_resource = self.db.create(self.collection_name, resource_data)
            created.append(created_resource)
        
        return created
    
    def bulk_delete(self, resource_ids: List[str]) -> int:
        """
        Delete multiple resources at once
        
        Args:
            resource_ids: List of resource IDs to delete
            
        Returns:
            Count of successfully deleted resources
        """
        deleted_count = 0
        for resource_id in resource_ids:
            if self.db.delete(self.collection_name, resource_id):
                deleted_count += 1
        
        return deleted_count
    
    # ========================================================================
    # Example: Resource-specific methods
    # ========================================================================
    
    def get_active_resources(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get only active resources
        
        Assumes resources have 'status' field with 'active' value.
        Customize this method for your resource.
        """
        return self.find_by_filters(
            filters={"status": "active"},
            skip=skip,
            limit=limit
        )
    
    def count_active_resources(self) -> int:
        """Count active resources"""
        return self.count_by_filter({"status": "active"})