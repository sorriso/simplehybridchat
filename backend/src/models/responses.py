"""
Path: backend/src/models/responses.py
Version: 8

Standard API response wrappers for consistent format

Changes in v8:
- Added FileListResponse and SingleFileResponse for files endpoints

Changes in v7:
- Added MessageListResponse for GET /api/conversations/{id}/messages

Changes in v6:
- Added ConversationListResponse for GET /api/conversations
- Added SingleConversationResponse for single conversation endpoints

Changes in v5:
- Added UserListResponse for GET /api/users (frontend-compatible format)
- Added SingleUserResponse for single user endpoints (frontend-compatible format)
- Added StatusUpdateRequest for PUT /api/users/{id}/status
- Added RoleUpdateRequest for PUT /api/users/{id}/role
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from src.models.base import CamelCaseModel
from pydantic import BaseModel, Field


T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """
    Success response wrapper
    
    Wraps successful API responses with consistent format.
    
    Example:
        return SuccessResponse(
            success=True,
            data={"id": "123", "name": "John"},
            message="User created"
        )
        
        # Returns:
        # {
        #   "success": true,
        #   "data": {"id": "123", "name": "John"},
        #   "message": "User created"
        # }
    """
    success: bool = True
    data: T
    message: Optional[str] = None


class ErrorResponse(CamelCaseModel):
    """
    Error response wrapper
    
    Wraps error responses with consistent format.
    
    Example:
        return ErrorResponse(
            success=False,
            error="User not found",
            code="NOT_FOUND",
            details={"user_id": "123"}
        )
        
        # Returns:
        # {
        #   "success": false,
        #   "error": "User not found",
        #   "code": "NOT_FOUND",
        #   "details": {"user_id": "123"}
        # }
    """
    success: bool = False
    error: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response wrapper
    
    Wraps paginated results with metadata.
    
    Example:
        return PaginatedResponse(
            success=True,
            data=[user1, user2, user3],
            total=100,
            page=1,
            per_page=10,
            pages=10
        )
        
        # Returns:
        # {
        #   "success": true,
        #   "data": [...],
        #   "pagination": {
        #     "total": 100,
        #     "page": 1,
        #     "per_page": 10,
        #     "pages": 10,
        #     "has_next": true,
        #     "has_prev": false
        #   }
        # }
    """
    success: bool = True
    data: List[T]
    pagination: Dict[str, Union[int, bool]] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int = 1,
        per_page: int = 10
    ) -> "PaginatedResponse[T]":
        """
        Factory method for paginated response
        
        Args:
            data: List of items
            total: Total count of items
            page: Current page number (1-indexed)
            per_page: Items per page
            
        Returns:
            PaginatedResponse with metadata
        """
        pages = (total + per_page - 1) // per_page  # Ceiling division
        
        return cls(
            success=True,
            data=data,
            pagination={
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": pages,
                "has_next": bool(page < pages),
                "has_prev": bool(page > 1)
            }
        )


class EmptyResponse(CamelCaseModel):
    """
    Empty success response
    
    Used for operations that don't return data (e.g., delete).
    
    Example:
        return EmptyResponse(message="User deleted")
        
        # Returns:
        # {
        #   "success": true,
        #   "message": "User deleted"
        # }
    """
    success: bool = True
    message: Optional[str] = None


class UserListResponse(BaseModel, Generic[T]):
    """
    User list response (frontend-compatible format)
    
    Returns list of users wrapped in 'users' key.
    
    Example:
        return UserListResponse(users=[user1, user2])
        
        # Returns:
        # {
        #   "users": [...]
        # }
    """
    users: List[T]


class SingleUserResponse(BaseModel, Generic[T]):
    """
    Single user response (frontend-compatible format)
    
    Returns single user wrapped in 'user' key.
    
    Example:
        return SingleUserResponse(user=user_data)
        
        # Returns:
        # {
        #   "user": {...}
        # }
    """
    user: T


class StatusUpdateRequest(BaseModel):
    """
    Request to update user status
    
    Example:
        {"status": "disabled"}
    """
    status: str = Field(..., pattern="^(active|disabled)$")


class RoleUpdateRequest(BaseModel):
    """
    Request to update user role
    
    Example:
        {"role": "manager"}
    """
    role: str = Field(..., pattern="^(user|manager|root)$")


class ConversationListResponse(BaseModel, Generic[T]):
    """
    Conversation list response (frontend-compatible format)
    
    Returns list of conversations wrapped in 'conversations' key.
    
    Example:
        return ConversationListResponse(conversations=[conv1, conv2])
        
        # Returns:
        # {
        #   "conversations": [...]
        # }
    """
    conversations: List[T]


class SingleConversationResponse(BaseModel, Generic[T]):
    """
    Single conversation response (frontend-compatible format)
    
    Returns single conversation wrapped in 'conversation' key.
    
    Example:
        return SingleConversationResponse(conversation=conv_data)
        
        # Returns:
        # {
        #   "conversation": {...}
        # }
    """
    conversation: T


class MessageListResponse(BaseModel, Generic[T]):
    """
    Message list response (frontend-compatible format)
    
    Returns list of messages wrapped in 'messages' key.
    
    Example:
        return MessageListResponse(messages=[msg1, msg2])
        
        # Returns:
        # {
        #   "messages": [...]
        # }
    """
    messages: List[T]


class FileListResponse(BaseModel, Generic[T]):
    """File list response (frontend-compatible format)"""
    files: List[T]


class SingleFileResponse(BaseModel, Generic[T]):
    """Single file response (frontend-compatible format)"""
    file: T