"""
Path: backend/src/templates/routes_template.py
Version: 1

Generic CRUD Routes Template

Copy this template and replace:
- resources -> your_resources (e.g., conversations)
- Resource -> YourResource (e.g., Conversation)
- ResourceService -> YourResourceService
- ResourceCreate -> YourResourceCreate
- ResourceUpdate -> YourResourceUpdate
- ResourceResponse -> YourResourceResponse

This template provides:
- Full REST API endpoints
- Proper HTTP status codes
- Response models matching frontend expectations
- Permission enforcement via dependencies
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.models.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from src.models.responses import (
    EmptyResponse,
    SingleResourceResponse,
    ResourceListResponse
)
from src.services.resource_service import ResourceService
from src.api.deps import get_database, UserFromRequest


router = APIRouter(prefix="/resources", tags=["Resources"])


# ============================================================================
# CREATE - POST /api/resources
# ============================================================================

@router.post("", response_model=SingleResourceResponse[ResourceResponse], status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleResourceResponse[ResourceResponse]:
    """
    Create new resource
    
    Creates a new resource owned by the authenticated user.
    
    Request body:
    - **name**: Resource name (required)
    - **description**: Resource description (optional)
    - **status**: Resource status (default: "active")
    
    Returns:
    - 201 Created: Resource created successfully
    - 403 Forbidden: Insufficient permissions
    - 409 Conflict: Resource already exists
    
    Requires authentication.
    """
    resource_service = ResourceService(db=db)
    resource = resource_service.create_resource(resource_data, current_user)
    
    return SingleResourceResponse(resource=resource)


# ============================================================================
# READ - GET /api/resources
# ============================================================================

@router.get("", response_model=ResourceListResponse[ResourceResponse])
async def list_resources(
    current_user: UserFromRequest,
    skip: int = Query(0, ge=0, description="Number of resources to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of resources to return"),
    status_filter: Optional[str] = Query(None, pattern="^(active|inactive|deleted)$", description="Filter by status"),
    search: Optional[str] = Query(None, min_length=1, description="Search term"),
    db = Depends(get_database)
) -> ResourceListResponse[ResourceResponse]:
    """
    List resources
    
    Returns paginated list of resources. Regular users see only their own,
    managers and root see all.
    
    Query parameters:
    - **skip**: Number to skip (for pagination, default: 0)
    - **limit**: Max results (1-500, default: 100)
    - **status**: Filter by status (active/inactive/deleted)
    - **search**: Search in name/description
    
    Returns:
    - 200 OK: List of resources
    - 403 Forbidden: Insufficient permissions
    
    Requires authentication.
    """
    resource_service = ResourceService(db=db)
    
    resources = resource_service.list_resources(
        current_user=current_user,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        search=search
    )
    
    return ResourceListResponse(resources=resources)


# ============================================================================
# READ - GET /api/resources/{resource_id}
# ============================================================================

@router.get("/{resource_id}", response_model=SingleResourceResponse[ResourceResponse])
async def get_resource(
    resource_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleResourceResponse[ResourceResponse]:
    """
    Get resource by ID
    
    Returns resource details. Users can view their own resources,
    managers and root can view all.
    
    Path parameters:
    - **resource_id**: Resource ID
    
    Returns:
    - 200 OK: Resource data
    - 403 Forbidden: Not owner and not manager+
    - 404 Not Found: Resource doesn't exist
    
    Requires authentication.
    """
    resource_service = ResourceService(db=db)
    resource = resource_service.get_resource(resource_id, current_user)
    
    return SingleResourceResponse(resource=resource)


# ============================================================================
# UPDATE - PUT /api/resources/{resource_id}
# ============================================================================

@router.put("/{resource_id}", response_model=SingleResourceResponse[ResourceResponse])
async def update_resource(
    resource_id: str,
    updates: ResourceUpdate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleResourceResponse[ResourceResponse]:
    """
    Update resource
    
    Updates resource information. Users can update their own resources.
    Managers and root can update all resources.
    
    Path parameters:
    - **resource_id**: Resource ID
    
    Request body (all optional):
    - **name**: New name
    - **description**: New description
    - **status**: New status (managers+ only)
    
    Returns:
    - 200 OK: Resource updated
    - 403 Forbidden: Not owner and not manager+
    - 404 Not Found: Resource doesn't exist
    
    Requires authentication.
    """
    resource_service = ResourceService(db=db)
    resource = resource_service.update_resource(resource_id, updates, current_user)
    
    return SingleResourceResponse(resource=resource)


# ============================================================================
# DELETE - DELETE /api/resources/{resource_id}
# ============================================================================

@router.delete("/{resource_id}", response_model=EmptyResponse)
async def delete_resource(
    resource_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> EmptyResponse:
    """
    Delete resource
    
    Permanently deletes a resource. Users can delete their own resources,
    root can delete any resource.
    
    Path parameters:
    - **resource_id**: Resource ID
    
    Returns:
    - 200 OK: Resource deleted
    - 403 Forbidden: Not owner and not root
    - 404 Not Found: Resource doesn't exist
    
    Requires authentication.
    """
    resource_service = ResourceService(db=db)
    resource_service.delete_resource(resource_id, current_user)
    
    return EmptyResponse(message="Resource deleted successfully")


# ============================================================================
# ADDITIONAL ENDPOINTS - Customize as needed
# ============================================================================

@router.put("/{resource_id}/status", response_model=SingleResourceResponse[ResourceResponse])
async def toggle_resource_status(
    resource_id: str,
    status_data: StatusUpdateRequest,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleResourceResponse[ResourceResponse]:
    """
    Toggle resource status
    
    Changes resource status. Only managers and root can change status.
    
    Path parameters:
    - **resource_id**: Resource ID
    
    Request body:
    - **status**: New status (active/inactive/deleted)
    
    Returns:
    - 200 OK: Status updated
    - 403 Forbidden: Not manager+
    - 404 Not Found: Resource doesn't exist
    
    Requires manager or root permission.
    """
    resource_service = ResourceService(db=db)
    resource = resource_service.toggle_resource_status(
        resource_id,
        status_data.status,
        current_user
    )
    
    return SingleResourceResponse(resource=resource)


# ============================================================================
# NOTES
# ============================================================================

# Frontend-compatible response formats:
# - POST /api/resources → {"resource": {...}}
# - GET /api/resources → {"resources": [...]}
# - GET /api/resources/{id} → {"resource": {...}}
# - PUT /api/resources/{id} → {"resource": {...}}
# - DELETE /api/resources/{id} → {"success": true, "message": "..."}

# Remember to create corresponding response models in src/models/responses.py:
# - SingleResourceResponse (wraps single resource)
# - ResourceListResponse (wraps list of resources)

# Don't forget to:
# 1. Create models in src/models/resource.py (ResourceCreate, ResourceUpdate, ResourceResponse)
# 2. Create repository in src/repositories/resource_repository.py
# 3. Create service in src/services/resource_service.py
# 4. Create response models in src/models/responses.py
# 5. Register router in src/main.py: app.include_router(resource_router, prefix="/api")
# 6. Create tests in tests/integration/api/test_resource_routes_integration.py