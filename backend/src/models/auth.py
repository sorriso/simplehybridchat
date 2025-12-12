"""
Path: backend/src/models/auth.py
Version: 4.0

Changes in v4.0:
- CLEAN AUTHENTICATION: Only 'email' field, no 'username' permissiveness
- Use EmailStr validation for proper email format enforcement
- Clear error messages for invalid email format
- Removed username/email compatibility layer (no bidouillage)

Changes in v3.0:
- FRONTEND COMPATIBILITY: LoginRequest accepts both 'email' and 'username'
- FRONTEND COMPATIBILITY: Add ConfigResponse for /config endpoint
- FRONTEND COMPATIBILITY: Add LoginResponse for /login endpoint

Authentication models and schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.models.base import CamelCaseModel
from src.models.user import UserResponse


class LoginRequest(BaseModel):
    """
    Login credentials
    
    CLEAN IMPLEMENTATION: Only accepts email (RFC-compliant format)
    No username field, no permissiveness, strict validation.
    
    Valid email examples:
    - user@example.com
    - admin@company.local
    - root@server.domain.com
    
    Invalid formats (will return 422 with clear error):
    - root@localhost (localhost not a valid domain)
    - user123 (not an email)
    - admin (not an email)
    """
    email: EmailStr = Field(..., description="User email address (RFC-compliant format)")
    password: str = Field(..., min_length=1, description="User password")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: EmailStr) -> EmailStr:
        """
        Additional email validation with clear error messages
        
        Pydantic EmailStr already validates RFC format, but we add
        custom error message for better frontend UX.
        """
        email_str = str(v)
        
        # Check for common mistakes
        if '@' not in email_str:
            raise ValueError("Email must contain '@' symbol")
        
        local_part, domain = email_str.rsplit('@', 1)
        
        if not local_part:
            raise ValueError("Email must have a local part before '@'")
        
        if not domain or '.' not in domain:
            raise ValueError(
                "Email domain must be valid (e.g., example.com, not 'localhost'). "
                "Use a proper domain format: user@domain.com"
            )
        
        return v


class RegisterRequest(BaseModel):
    """User registration request"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="User email address (RFC-compliant format)")
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: EmailStr) -> EmailStr:
        """Validate email format for registration"""
        email_str = str(v)
        
        if '@' not in email_str:
            raise ValueError("Email must contain '@' symbol")
        
        local_part, domain = email_str.rsplit('@', 1)
        
        if not domain or '.' not in domain:
            raise ValueError(
                "Email domain must be valid (e.g., example.com, not 'localhost'). "
                "Use a proper domain format: user@domain.com"
            )
        
        return v


class TokenResponse(CamelCaseModel):
    """
    JWT token response (internal use)
    
    Fields are automatically serialized to camelCase:
    - access_token → accessToken
    - token_type → tokenType
    - expires_in → expiresIn
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """
    FRONTEND COMPATIBILITY: Login response wrapper
    
    Frontend expects:
    {
      "token": "jwt-token",
      "user": {...}
    }
    """
    token: str
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload (internal, not returned to client)"""
    sub: str  # user_id
    email: str
    role: str
    exp: int  # expiration timestamp


class LogoutRequest(BaseModel):
    """Logout request (optional token blacklist)"""
    token: Optional[str] = None


class AuthStatus(CamelCaseModel):
    """
    Current authentication status
    
    Fields serialized to camelCase:
    - user_id → userId
    """
    authenticated: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class SsoConfigData(BaseModel):
    """
    FRONTEND COMPATIBILITY: SSO configuration structure
    
    Frontend expects camelCase:
    {
      "tokenHeader": "X-Auth-Token",
      "nameHeader": "X-User-Name",
      "emailHeader": "X-User-Email"
    }
    """
    token_header: str = Field(alias="tokenHeader")
    name_header: Optional[str] = Field(None, alias="nameHeader")
    email_header: Optional[str] = Field(None, alias="emailHeader")
    first_name_header: Optional[str] = Field(None, alias="firstNameHeader")
    last_name_header: Optional[str] = Field(None, alias="lastNameHeader")
    
    class Config:
        populate_by_name = True


class AuthConfigData(BaseModel):
    """
    FRONTEND COMPATIBILITY: Authentication configuration data
    
    Frontend expects:
    {
      "mode": "local",
      "allowMultiLogin": false,
      "maintenanceMode": false,
      "ssoConfig": null
    }
    """
    mode: str = Field(..., pattern="^(none|local|sso)$")
    allow_multi_login: bool = Field(alias="allowMultiLogin")
    maintenance_mode: bool = Field(alias="maintenanceMode")
    sso_config: Optional[SsoConfigData] = Field(None, alias="ssoConfig")
    
    class Config:
        populate_by_name = True


class ConfigResponse(BaseModel):
    """
    FRONTEND COMPATIBILITY: Configuration response wrapper
    
    Frontend expects EXACTLY this structure:
    {
      "config": {
        "mode": "local",
        "allowMultiLogin": false,
        "maintenanceMode": false,
        "ssoConfig": null
      }
    }
    """
    config: AuthConfigData


class AuthConfig(CamelCaseModel):
    """
    DEPRECATED - Use ConfigResponse instead
    Kept for backward compatibility
    
    Fields serialized to camelCase:
    - auth_mode → authMode
    - allow_registration → allowRegistration
    - sso_enabled → ssoEnabled
    - sso_token_header → ssoTokenHeader
    - sso_name_header → ssoNameHeader
    - sso_email_header → ssoEmailHeader
    """
    auth_mode: str
    allow_registration: bool
    sso_enabled: bool
    sso_token_header: Optional[str] = None
    sso_name_header: Optional[str] = None
    sso_email_header: Optional[str] = None


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)