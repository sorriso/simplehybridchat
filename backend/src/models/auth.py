"""
Path: backend/src/models/auth.py
Version: 5.0

Changes in v5.0:
- SECURITY: LoginRequest accepts password_hash (SHA256) instead of password
- SECURITY: RegisterRequest accepts password_hash (SHA256) instead of password
- Frontend computes SHA256 client-side before transmission
- Backend receives SHA256 hash and stores bcrypt(SHA256)
- Never receives or stores plaintext passwords

Changes in v4.0:
- CLEAN AUTHENTICATION: Only 'email' field, no 'username' permissiveness
- Use EmailStr validation for proper email format enforcement
- Clear error messages for invalid email format
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.models.base import CamelCaseModel
from src.models.user import UserResponse


class LoginRequest(BaseModel):
    """
    Login credentials with SHA256 pre-hashed password
    
    SECURITY MODEL:
    - Frontend: password → SHA256 → password_hash (64 hex chars)
    - Backend: receives password_hash → bcrypt(password_hash) → compare
    - Never receives plaintext password
    
    Valid email examples:
    - user@example.com
    - admin@company.local
    - root@server.domain.com
    """
    email: EmailStr = Field(..., description="User email address (RFC-compliant format)")
    password_hash: str = Field(
        ..., 
        description="SHA256 hash of password (computed client-side)",
        min_length=64,
        max_length=64
    )
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: EmailStr) -> EmailStr:
        """Validate email format with clear error messages"""
        email_str = str(v)
        
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
    """
    User registration request with SHA256 pre-hashed password
    
    SECURITY MODEL:
    - Frontend: password → SHA256 → password_hash (64 hex chars)
    - Backend: receives password_hash → bcrypt(password_hash) → store
    - Never receives plaintext password
    """
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="User email address (RFC-compliant format)")
    password_hash: str = Field(
        ..., 
        description="SHA256 hash of password (computed client-side)",
        min_length=64,
        max_length=64
    )
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
    expires_in: int


class LoginResponse(BaseModel):
    """
    Login response wrapper
    
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
    sub: str
    email: str
    role: str
    exp: int


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


class SsoConfigData(CamelCaseModel):
    """
    SSO configuration data
    
    Fields serialized to camelCase:
    - token_header → tokenHeader
    - name_header → nameHeader
    - email_header → emailHeader
    - first_name_header → firstNameHeader
    - last_name_header → lastNameHeader
    """
    token_header: str
    name_header: Optional[str] = None
    email_header: Optional[str] = None
    first_name_header: Optional[str] = None
    last_name_header: Optional[str] = None


class AuthConfigData(CamelCaseModel):
    """
    Authentication configuration
    
    Fields serialized to camelCase:
    - allow_multi_login → allowMultiLogin
    - maintenance_mode → maintenanceMode
    - sso_config → ssoConfig
    """
    mode: str
    allow_multi_login: bool
    maintenance_mode: bool
    sso_config: Optional[SsoConfigData] = None


class ConfigResponse(BaseModel):
    """
    Config response wrapper
    
    Frontend expects:
    {
      "config": {...}
    }
    """
    config: AuthConfigData