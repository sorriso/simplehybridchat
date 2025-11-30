"""
Path: src/models/responses.py
Version: 4

Standard API response wrappers for consistent format
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
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


class ErrorResponse(BaseModel):
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


class EmptyResponse(BaseModel):
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