"""
Path: src/models/auth.py
Version: 1.0

Authentication models and schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """User registration request"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    email: str
    role: str
    exp: int  # expiration timestamp


class LogoutRequest(BaseModel):
    """Logout request (optional token blacklist)"""
    token: Optional[str] = None


class AuthStatus(BaseModel):
    """Current authentication status"""
    authenticated: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class AuthConfig(BaseModel):
    """Authentication configuration"""
    auth_mode: str
    allow_registration: bool
    sso_enabled: bool
    sso_token_header: Optional[str] = None
    sso_name_header: Optional[str] = None
    sso_email_header: Optional[str] = None