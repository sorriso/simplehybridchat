"""
Path: backend/src/api/deps.py
Version: 2

FastAPI dependency injection functions
Provides database, storage, and authentication dependencies
"""

from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database.interface import IDatabase
from src.database.factory import get_database
from src.storage.interface import IFileStorage
from src.storage.factory import get_storage
from src.core.security import decode_access_token
from src.core.permissions import check_permission

# Security scheme for JWT
security = HTTPBearer()


def get_db() -> IDatabase:
    """
    Get database instance
    
    Dependency that provides database connection.
    
    Example:
        @app.get("/users")
        def get_users(db: IDatabase = Depends(get_db)):
            users = db.get_all("users")
            return users
    """
    return get_database()


def get_file_storage() -> IFileStorage:
    """
    Get file storage instance
    
    Dependency that provides storage connection.
    
    Example:
        @app.post("/upload")
        def upload(storage: IFileStorage = Depends(get_file_storage)):
            storage.upload_file(...)
    """
    return get_storage()


def get_user_from_request(request: Request) -> dict:
    """
    Get user from request scope (injected by auth middleware)
    
    Helper function to extract user from request.scope.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User dict
        
    Raises:
        HTTPException 401: If no user in scope
    """
    user = request.scope.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[IDatabase, Depends(get_db)]
) -> dict:
    """
    Get current authenticated user
    
    Extracts JWT token from Authorization header, validates it,
    and returns user from database.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database instance
        
    Returns:
        User dict with user data
        
    Raises:
        HTTPException 401: If token invalid or user not found
        
    Example:
        @app.get("/me")
        def get_me(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    try:
        # Extract token
        token = credentials.credentials
        
        # Decode and validate token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        user = db.get_by_id("users", user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is active
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


def require_role(required_role: str) -> Callable:
    """
    Factory for role-based access control dependency
    
    Creates a dependency that checks if user has required role.
    
    Args:
        required_role: Required role ("user", "manager", "root")
        
    Returns:
        Dependency function that checks role
        
    Example:
        # Only managers and root can access
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: str,
            user: dict = Depends(require_role("manager"))
        ):
            # user is guaranteed to be manager or root
            ...
    """
    def role_checker(
        user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        """Check if user has required role"""
        if not check_permission(user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return user
    
    return role_checker


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Annotated[IDatabase, Depends(get_db)] = None
) -> dict | None:
    """
    Get current user (optional)
    
    Same as get_current_user but returns None if no token provided.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer token
        db: Database instance
        
    Returns:
        User dict if authenticated, None otherwise
        
    Example:
        @app.get("/items")
        def get_items(user: dict | None = Depends(get_current_user_optional)):
            if user:
                # Return user-specific items
                ...
            else:
                # Return public items
                ...
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


# Type aliases for cleaner type hints
CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_current_user_optional)]
DatabaseDep = Annotated[IDatabase, Depends(get_db)]
StorageDep = Annotated[IFileStorage, Depends(get_file_storage)]

# Helper for getting user from request scope (when using auth middleware)
UserFromRequest = Annotated[dict, Depends(get_user_from_request)]