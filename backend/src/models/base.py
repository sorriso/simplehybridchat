"""
Path: backend/src/models/base.py
Version: 2

Changes in v2:
- Added BaseRequestModel for API request schemas
- BaseRequestModel accepts camelCase from frontend

Base Pydantic model with automatic snake_case to camelCase serialization
This is the proper way to handle case conversion in Pydantic v2

Usage:
    from src.models.base import CamelCaseModel, BaseRequestModel
    
    # For responses (output):
    class UserResponse(CamelCaseModel):
        user_id: str  # Automatically serialized as "userId"
        created_at: datetime  # Automatically serialized as "createdAt"
    
    # For requests (input):
    class ShareRequest(BaseRequestModel):
        group_ids: List[str]  # Accepts both "groupIds" and "group_ids"
"""

from pydantic import BaseModel, ConfigDict


def to_camel_case(string: str) -> str:
    """
    Convert snake_case to camelCase
    
    Args:
        string: String in snake_case
        
    Returns:
        String in camelCase
        
    Examples:
        >>> to_camel_case('user_id')
        'userId'
        >>> to_camel_case('created_at')
        'createdAt'
        >>> to_camel_case('shared_with_group_ids')
        'sharedWithGroupIds'
    """
    components = string.split('_')
    # First component stays lowercase, rest are capitalized
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelCaseModel(BaseModel):
    """
    Base model that automatically converts snake_case fields to camelCase in JSON
    
    This is the Pydantic v2 way to handle case conversion.
    All response models should inherit from this.
    
    Example:
        class UserResponse(CamelCaseModel):
            user_id: str
            created_at: datetime
        
        user = UserResponse(user_id="123", created_at=datetime.now())
        user.model_dump()  # {'user_id': '123', 'created_at': ...}
        user.model_dump(by_alias=True)  # {'userId': '123', 'createdAt': ...}
        
        # FastAPI automatically uses by_alias=True when serializing responses
    """
    
    model_config = ConfigDict(
        # Generate camelCase aliases for all fields
        alias_generator=to_camel_case,
        
        # Allow both snake_case and camelCase in input
        populate_by_name=True,
        
        # Use aliases when serializing (FastAPI does this automatically)
        by_alias=True,
    )


class BaseRequestModel(BaseModel):
    """
    Base model for API request schemas that accepts camelCase from frontend
    
    This model allows the frontend to send camelCase while the backend
    works internally with snake_case.
    
    Example:
        class ShareRequest(BaseRequestModel):
            group_ids: List[str]
        
        # Frontend can send:
        {"groupIds": ["group-1"]}  # ✅ Accepted (via alias)
        {"group_ids": ["group-1"]}  # ✅ Also accepted (via populate_by_name)
        
        # Backend receives:
        request.group_ids  # Always snake_case internally
    """
    
    model_config = ConfigDict(
        # Generate camelCase aliases for all fields
        alias_generator=to_camel_case,
        
        # Allow both snake_case and camelCase in input
        populate_by_name=True,
    )