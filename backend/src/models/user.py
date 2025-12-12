"""
Path: backend/src/models/user.py
Version: 3.0

Changes in v3.0:
- FRONTEND COMPATIBILITY: Add firstName, lastName fields (computed from name)
- FRONTEND COMPATIBILITY: Add isActive computed field (from status)
- Auto-compute firstName/lastName from name if not in DB
- Maintain backward compatibility with existing DB schema

Changes in v2:
- UserResponse now inherits from CamelCaseModel
- Ensures camelCase serialization for frontend compatibility

User models and schemas for API requests/responses
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field

from src.models.base import CamelCaseModel


class UserBase(BaseModel):
    """Base user fields"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = Field(default="user", pattern="^(user|manager|root)$")
    status: str = Field(default="active", pattern="^(active|disabled)$")


class UserCreate(UserBase):
    """User creation request"""
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    def model_post_init(self, __context) -> None:
        """Auto-generate name from firstName/lastName if not provided"""
        if not hasattr(self, 'name') or not self.name:
            if self.first_name and self.last_name:
                self.name = f"{self.first_name} {self.last_name}"
            elif self.first_name:
                self.name = self.first_name
            elif self.last_name:
                self.name = self.last_name


class UserUpdate(BaseModel):
    """User update request (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(user|manager|root)$")
    status: Optional[str] = Field(None, pattern="^(active|disabled)$")
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(CamelCaseModel):
    """
    User response model (without password)
    
    FRONTEND COMPATIBILITY:
    - Includes firstName, lastName (computed from name if not in DB)
    - Includes isActive (computed from status)
    - Maintains backward compatibility with name and status
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - created_at â†’ createdAt
    - updated_at â†’ updatedAt
    - last_login â†’ lastLogin
    - first_name â†’ firstName
    - last_name â†’ lastName
    - is_active â†’ isActive
    """
    id: str
    name: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # Frontend compatibility fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """
        Computed field: isActive from status
        
        Maps:
        - status == "active" â†’ isActive = true
        - status == "disabled" â†’ isActive = false
        """
        return self.status == "active"
    
    def model_post_init(self, __context) -> None:
        """
        Auto-compute firstName/lastName from name if not provided
        
        Rules:
        - If firstName/lastName already in DB: use them
        - Otherwise: split 'name' on first space
          - "John Doe" â†’ firstName="John", lastName="Doe"
          - "John" â†’ firstName="John", lastName=None
        """
        if not self.first_name and not self.last_name and self.name:
            parts = self.name.split(' ', 1)
            if len(parts) >= 1:
                self.first_name = parts[0]
            if len(parts) >= 2:
                self.last_name = parts[1]


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v