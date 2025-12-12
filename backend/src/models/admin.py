"""
Path: backend/src/models/admin.py
Version: 1

Models for admin operations (maintenance, sessions)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


class MaintenanceRequest(BaseModel):
    """Request to toggle maintenance mode"""
    enabled: bool = Field(..., description="Enable or disable maintenance mode")


class MaintenanceResponse(CamelCaseModel):
    """
    Response for maintenance mode status
    
    Serialized to camelCase:
    - maintenance_mode → maintenanceMode
    """
    maintenance_mode: bool
    message: str


class SessionInfo(CamelCaseModel):
    """
    Session information
    
    Serialized to camelCase:
    - session_id → sessionId
    - user_id → userId
    - created_at → createdAt
    - expires_at → expiresAt
    - ip_address → ipAddress
    - user_agent → userAgent
    """
    session_id: str
    user_id: str
    user_email: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionsListResponse(CamelCaseModel):
    """Response for sessions list"""
    sessions: list[SessionInfo]
    total_count: int


class RevokeSessionsResponse(CamelCaseModel):
    """Response for session revocation"""
    revoked_count: int
    message: str