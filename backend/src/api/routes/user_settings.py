"""
Path: backend/src/api/routes/user_settings.py
Version: 2

Changes in v2:
- Implemented get_settings using SettingsService
- Implemented update_settings with partial merge
- Removed 501 stubs

User settings endpoints
"""

from fastapi import APIRouter, Depends
from typing import Optional

from src.models.settings import UserSettings, SettingsResponse
from src.models.responses import SuccessResponse
from src.services.settings_service import SettingsService
from src.api.deps import get_database, UserFromRequest

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "",
    response_model=SuccessResponse[UserSettings],
    summary="Get user settings"
)
async def get_settings(
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    Get user settings
    
    Returns stored settings or defaults if user has no settings yet.
    
    Default values:
    - prompt_customization: "" (empty string)
    - theme: "light"
    - language: "en"
    """
    service = SettingsService(db=db)
    settings_dict = service.get_settings(current_user["id"])
    
    return SuccessResponse(
        data=UserSettings(**settings_dict)
    )


@router.put(
    "",
    response_model=SuccessResponse[UserSettings],
    summary="Update user settings"
)
async def update_settings(
    settings: UserSettings,
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    Update user settings (partial update)
    
    Only provided fields are updated, other fields keep their current values.
    
    Example:
    - Current: {theme: "dark", language: "fr", promptCustomization: "Be brief"}
    - Update: {language: "en"}
    - Result: {theme: "dark", language: "en", promptCustomization: "Be brief"}
    
    Validation:
    - theme: must be "light" or "dark"
    - language: must be "en", "fr", "es", or "de"
    - promptCustomization: any string (can be empty)
    """
    service = SettingsService(db=db)
    
    # Convert Pydantic model to dict
    # exclude_unset=True: only include fields that were explicitly set in request
    updates = settings.model_dump(exclude_unset=True)
    
    # Update settings (merge)
    updated_settings = service.update_settings(current_user["id"], updates)
    
    return SuccessResponse(
        data=UserSettings(**updated_settings),
        message="Settings updated successfully"
    )