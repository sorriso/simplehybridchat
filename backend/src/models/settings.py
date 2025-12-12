"""
Path: backend/src/models/settings.py
Version: 3

Changes in v3:
- KEEP SettingsResponse (used by routes)
- UserSettings inherits from CamelCaseModel
- SettingsResponse wraps UserSettings

User settings models
"""

from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


class UserSettings(CamelCaseModel):
    """
    User settings
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - prompt_customization → promptCustomization
    """
    prompt_customization: str = Field(default="", description="Custom prompt instructions")
    theme: str = Field(default="light", pattern="^(light|dark)$")
    language: str = Field(default="en", pattern="^(en|fr|es|de)$")


class SettingsResponse(BaseModel):
    """
    Settings response wrapper
    
    NOTE: Uses BaseModel (not CamelCaseModel) because it just wraps UserSettings.
    UserSettings already handles camelCase conversion.
    """
    settings: UserSettings