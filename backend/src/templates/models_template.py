"""
Path: backend/src/templates/models_template.py
Version: 1

Generic Pydantic Models Template

Copy this template and replace:
- Resource -> YourResource (e.g., Conversation)
- resource -> your_resource (e.g., conversation)

This template provides:
- Base model with common fields
- Create model (request body for POST)
- Update model (request body for PUT, all fields optional)
- Response model (API response, no sensitive data)
- InDB model (database representation)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# BASE MODEL - Common fields
# ============================================================================

class ResourceBase(BaseModel):
    """
    Base resource fields
    
    Contains fields common to all resource operations.
    Inherit from this for Create/Update models.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Resource name")
    description: Optional[str] = Field(None, max_length=1000, description="Resource description")
    status: str = Field(default="active", pattern="^(active|inactive|deleted)$", description="Resource status")
    
    # Add your resource-specific fields here
    # Example:
    # category: str = Field(..., pattern="^(type1|type2|type3)$")
    # priority: int = Field(default=0, ge=0, le=10)
    # tags: List[str] = Field(default_factory=list)


# ============================================================================
# CREATE MODEL - For POST requests
# ============================================================================

class ResourceCreate(ResourceBase):
    """
    Resource creation request
    
    Used for POST /api/resources
    Contains all required fields for creating a new resource.
    """
    # Inherit all fields from ResourceBase
    # Add creation-specific validations
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate name field
        
        Add custom validation logic here.
        """
        # Example: Ensure name doesn't start with numbers
        if v[0].isdigit():
            raise ValueError('Name cannot start with a digit')
        
        # Example: Sanitize name
        v = v.strip()
        
        return v
    
    # Add more validators as needed
    # @field_validator('field_name')
    # @classmethod
    # def validate_field(cls, v: Any) -> Any:
    #     # validation logic
    #     return v


# ============================================================================
# UPDATE MODEL - For PUT/PATCH requests
# ============================================================================

class ResourceUpdate(BaseModel):
    """
    Resource update request
    
    Used for PUT /api/resources/{id}
    All fields are optional - only provided fields are updated.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(active|inactive|deleted)$")
    
    # Add your resource-specific optional fields here
    # Example:
    # category: Optional[str] = Field(None, pattern="^(type1|type2|type3)$")
    # priority: Optional[int] = Field(None, ge=0, le=10)
    # tags: Optional[List[str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided"""
        if v is None:
            return v
        
        if v[0].isdigit():
            raise ValueError('Name cannot start with a digit')
        
        return v.strip()


# ============================================================================
# RESPONSE MODEL - For API responses
# ============================================================================

class ResourceResponse(BaseModel):
    """
    Resource response
    
    Used for all API responses (GET, POST, PUT).
    Contains all fields that should be returned to the client.
    NEVER include sensitive data like passwords, tokens, etc.
    """
    id: str = Field(..., description="Resource unique identifier")
    name: str
    description: Optional[str] = None
    status: str
    
    # Ownership/relationship fields
    owner_id: str = Field(..., description="ID of user who owns this resource")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Add your resource-specific fields here
    # Example:
    # category: str
    # priority: int
    # tags: List[str]
    
    class Config:
        """Pydantic config"""
        from_attributes = True  # Allow creation from ORM/dict
        json_schema_extra = {
            "example": {
                "id": "resource-123",
                "name": "Example Resource",
                "description": "This is an example",
                "status": "active",
                "owner_id": "user-456",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }
        }


# ============================================================================
# DATABASE MODEL - For internal use
# ============================================================================

class ResourceInDB(ResourceBase):
    """
    Resource as stored in database
    
    Internal model - NOT exposed via API.
    Contains database-specific fields.
    """
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Add database-specific fields here
    # Example:
    # _key: str  # ArangoDB internal key
    # _rev: str  # ArangoDB revision


# ============================================================================
# ADDITIONAL MODELS - For specific operations
# ============================================================================

class ResourceStatusUpdate(BaseModel):
    """
    Status update request
    
    Used for PUT /api/resources/{id}/status
    """
    status: str = Field(..., pattern="^(active|inactive|deleted)$")


class ResourceSearch(BaseModel):
    """
    Search request
    
    Used for POST /api/resources/search
    """
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[dict] = Field(None, description="Additional filters")
    limit: int = Field(default=100, ge=1, le=500, description="Max results")


# ============================================================================
# NOTES
# ============================================================================

# Field validation examples:
# - min_length/max_length: String length constraints
# - ge/le: Greater/less than or equal (numbers)
# - pattern: Regex pattern (string)
# - default: Default value if not provided
# - default_factory: Function to generate default (e.g., list, dict)

# Common validators:
# @field_validator('email')
# @classmethod
# def validate_email(cls, v: str) -> str:
#     # Use EmailStr type from pydantic or custom validation
#     return v.lower().strip()

# @field_validator('url')
# @classmethod  
# def validate_url(cls, v: str) -> str:
#     from pydantic import HttpUrl
#     # Validate URL format
#     return str(HttpUrl(v))

# Model validators (validate multiple fields):
# @model_validator(mode='after')
# def check_dates(self) -> 'ResourceCreate':
#     if self.end_date < self.start_date:
#         raise ValueError('end_date must be after start_date')
#     return self