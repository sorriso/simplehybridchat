"""
Path: backend/src/templates/service_template.py
Version: 1

Generic CRUD Service Template

Copy this template and replace:
- ResourceService -> YourResourceService (e.g., ConversationService)
- resource -> your_resource (e.g., conversation)
- resources -> your_resources (e.g., conversations)
- ResourceRepository -> YourResourceRepository
- ResourceCreate -> YourResourceCreate
- ResourceUpdate -> YourResourceUpdate
- ResourceResponse -> YourResourceResponse

This template provides:
- Full CRUD with permission checks
- Business logic layer
- Validation
- Error handling
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.models.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from src.repositories.resource_repository import ResourceRepository
from src.database.interface import IDatabase
from src.core.permissions import check_permission


class ResourceService:
    """
    Resource management service
    
    Provides CRUD operations with business logic and permission checks.
    
    Permissions (customize for your resource):
    - create_resource: authenticated users
    - get_resource: owner or manager+
    - list_resources: owner's resources or manager+ all
    - update_resource: owner or manager+
    - delete_resource: owner or root
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """
        Initialize service with repository
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        self.resource_repo = ResourceRepository(db=db)
    
    # ========================================================================
    # CREATE
    # ========================================================================
    
    def create_resource(
        self,
        resource_data: ResourceCreate,
        current_user: Dict[str, Any]
    ) -> ResourceResponse:
        """
        Create new resource
        
        Args:
            resource_data: Resource creation data
            current_user: Current authenticated user
            
        Returns:
            Created resource
            
        Raises:
            HTTPException 403: If insufficient permissions
            HTTPException 409: If resource already exists (e.g., duplicate name)
        """
        # Permission check (customize based on your requirements)
        # Example: All authenticated users can create
        # For restricted creation, use: if not check_permission(current_user, "manager"):
        
        # Business validation
        # Example: Check for duplicates
        existing = self.resource_repo.get_by_field("name", resource_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource with name '{resource_data.name}' already exists"
            )
        
        # Prepare data for DB
        db_data = resource_data.model_dump()
        db_data["owner_id"] = current_user["id"]
        db_data["created_at"] = datetime.utcnow()
        db_data["updated_at"] = None
        
        # Create resource
        resource = self.resource_repo.create(db_data)
        
        return ResourceResponse(**resource)
    
    # ========================================================================
    # READ
    # ========================================================================
    
    def get_resource(
        self,
        resource_id: str,
        current_user: Dict[str, Any]
    ) -> ResourceResponse:
        """
        Get resource by ID
        
        Args:
            resource_id: Resource ID
            current_user: Current authenticated user
            
        Returns:
            Resource data
            
        Raises:
            HTTPException 403: If insufficient permissions
            HTTPException 404: If resource not found
        """
        # Get resource
        resource = self.resource_repo.get_by_id(resource_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        # Permission check: owner or manager+
        is_owner = resource.get("owner_id") == current_user["id"]
        is_manager_or_above = check_permission(current_user, "manager")
        
        if not (is_owner or is_manager_or_above):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you can only view your own resources"
            )
        
        return ResourceResponse(**resource)
    
    def list_resources(
        self,
        current_user: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ResourceResponse]:
        """
        List resources with filters
        
        Args:
            current_user: Current authenticated user
            skip: Number to skip (pagination)
            limit: Max results
            status_filter: Optional status filter
            search: Optional search term
            
        Returns:
            List of resources
            
        Raises:
            HTTPException 403: If insufficient permissions for listing all
        """
        # Permission-based filtering
        if check_permission(current_user, "manager"):
            # Manager/root can see all resources
            filters = {}
            if status_filter:
                filters["status"] = status_filter
            
            if search:
                # Use search method
                resources = self.resource_repo.search(
                    search_term=search,
                    search_fields=["name", "description"],
                    skip=skip,
                    limit=limit
                )
            else:
                resources = self.resource_repo.find_by_filters(
                    filters=filters,
                    skip=skip,
                    limit=limit
                )
        else:
            # Regular users see only their own
            resources = self.resource_repo.get_by_owner(
                owner_id=current_user["id"],
                skip=skip,
                limit=limit
            )
            
            # Apply additional filters if needed
            if status_filter:
                resources = [r for r in resources if r.get("status") == status_filter]
            
            if search:
                search_lower = search.lower()
                resources = [
                    r for r in resources
                    if search_lower in r.get("name", "").lower()
                    or search_lower in r.get("description", "").lower()
                ]
        
        return [ResourceResponse(**r) for r in resources]
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    def update_resource(
        self,
        resource_id: str,
        updates: ResourceUpdate,
        current_user: Dict[str, Any]
    ) -> ResourceResponse:
        """
        Update resource
        
        Args:
            resource_id: Resource ID
            updates: Update data (all fields optional)
            current_user: Current authenticated user
            
        Returns:
            Updated resource
            
        Raises:
            HTTPException 403: If insufficient permissions
            HTTPException 404: If resource not found
        """
        # Get existing resource
        resource = self.resource_repo.get_by_id(resource_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        # Permission check: owner or manager+
        is_owner = resource.get("owner_id") == current_user["id"]
        is_manager_or_above = check_permission(current_user, "manager")
        
        if not (is_owner or is_manager_or_above):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you can only update your own resources"
            )
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        
        # Business logic: some fields may be restricted
        # Example: only managers can change status
        if "status" in update_data and not check_permission(current_user, "manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only managers can change resource status"
            )
        
        # Update timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Merge updates
        for key, value in update_data.items():
            resource[key] = value
        
        # Save to DB
        updated_resource = self.resource_repo.update(resource_id, resource)
        
        if not updated_resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return ResourceResponse(**updated_resource)
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    def delete_resource(
        self,
        resource_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete resource
        
        Args:
            resource_id: Resource ID
            current_user: Current authenticated user
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException 403: If insufficient permissions
            HTTPException 404: If resource not found
        """
        # Get resource
        resource = self.resource_repo.get_by_id(resource_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        # Permission check: owner or root
        is_owner = resource.get("owner_id") == current_user["id"]
        is_root = check_permission(current_user, "root")
        
        if not (is_owner or is_root):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you can only delete your own resources"
            )
        
        # Delete resource
        deleted = self.resource_repo.delete(resource_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return True
    
    # ========================================================================
    # Additional business logic methods
    # ========================================================================
    
    def toggle_resource_status(
        self,
        resource_id: str,
        new_status: str,
        current_user: Dict[str, Any]
    ) -> ResourceResponse:
        """
        Toggle resource status (example additional method)
        
        Args:
            resource_id: Resource ID
            new_status: New status value
            current_user: Current authenticated user
            
        Returns:
            Updated resource
        """
        # Permission check: manager+
        if not check_permission(current_user, "manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only managers can change resource status"
            )
        
        # Get resource
        resource = self.resource_repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        # Update status
        resource["status"] = new_status
        resource["updated_at"] = datetime.utcnow()
        
        updated = self.resource_repo.update(resource_id, resource)
        return ResourceResponse(**updated)