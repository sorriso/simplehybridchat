"""
Path: src/middleware/auth_middleware.py
Version: 4

Authentication middleware
Validates JWT tokens and injects user into request state
"""

import logging
from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.security import decode_access_token
from src.core.config import settings

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware
    
    Validates JWT tokens on protected routes and injects
    user information into request state.
    
    Public routes (no auth required):
    - /docs, /openapi.json
    - /health, /
    - /api/auth/login, /api/auth/register, /api/auth/config
    
    Protected routes (auth required):
    - Everything else
    
    Example:
        from src.middleware.auth_middleware import AuthenticationMiddleware
        
        app = FastAPI()
        app.add_middleware(AuthenticationMiddleware)
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/config",
    ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ):
        """
        Process request and validate authentication
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from handler
        """
        # Check if route is public
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Check AUTH_MODE
        if settings.AUTH_MODE == "none":
            # No authentication required - inject generic user
            request.scope["user"] = {
                "id": "john-doe",
                "name": "John Doe",
                "email": "john@example.com",
                "role": "user"
            }
            response = await call_next(request)
            return response
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Missing Authorization header",
                    "code": "UNAUTHORIZED"
                },
                status_code=401
            )
        
        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Invalid Authorization header format",
                    "code": "UNAUTHORIZED"
                },
                status_code=401
            )
        
        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Decode and validate JWT
            payload = decode_access_token(token)
            
            # Extract user info from token
            user_id = payload.get("sub")
            
            if not user_id:
                return JSONResponse(
                    content={
                        "success": False,
                        "error": "Invalid token payload",
                        "code": "UNAUTHORIZED"
                    },
                    status_code=401
                )
            
            # Inject user into request scope (persists through middleware stack)
            request.scope["user"] = {
                "id": user_id,
                "role": payload.get("role", "user")
            }
            
            logger.debug(f"Authenticated user: {user_id}")
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Invalid or expired token",
                    "code": "UNAUTHORIZED"
                },
                status_code=401
            )
        
        # Continue to next handler
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """
        Check if route is public (doesn't require auth)
        
        Args:
            path: Request path
            
        Returns:
            True if public, False if protected
        """
        # Check exact matches first
        if path in self.PUBLIC_ROUTES:
            return True
        
        # Check prefixes only for non-root routes
        # Avoid matching everything with "/"
        for public_path in self.PUBLIC_ROUTES:
            if public_path != "/" and path.startswith(public_path + "/"):
                return True
        
        return False