"""
Path: backend/src/api/routes/admin.py
Version: 2

Changes in v2:
- Fix response format: use SuccessResponse wrapper for consistency

Admin routes for system operations
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import UserFromRequest
from src.services.admin_service import AdminService
from src.models.admin import MaintenanceRequest, MaintenanceResponse
from src.models.responses import SuccessResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


def check_root_permission(current_user: UserFromRequest) -> None:
    """
    Verify user is root
    
    Raises:
        HTTPException 403: If user is not root
    """
    if current_user.get("role") != "root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: root permission required"
        )


@router.post(
    "/maintenance",
    response_model=SuccessResponse[MaintenanceResponse],
    summary="Toggle maintenance mode"
)
async def toggle_maintenance(
    request: MaintenanceRequest,
    current_user: UserFromRequest
):
    """
    Toggle maintenance mode (root only)
    
    When enabled:
    - Only root users can access the API
    - All other users receive 503 Service Unavailable
    
    This is useful for:
    - System upgrades
    - Database migrations
    - Emergency maintenance
    """
    check_root_permission(current_user)
    
    result = AdminService.toggle_maintenance(request.enabled)
    
    return SuccessResponse(data=MaintenanceResponse(**result))