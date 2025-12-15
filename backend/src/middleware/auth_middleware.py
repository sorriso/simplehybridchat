"""
Path: backend/src/middleware/auth_middleware.py
Version: 9.0

Changes in v9.0:
- CRITICAL FIX: Load group_ids from database in local auth mode
- After decoding JWT token, fetch full user from DB to get group_ids
- Without group_ids, shared conversation access fails with 403
- Now matches SSO behavior (both modes load full user with group_ids)

Changes in v8.0:
- CRITICAL FIX: Add CORS headers to all 401 error responses
- Without CORS headers on error responses, browser blocks even 401 errors
- Uses settings.get_cors_origins() to get configured origins
- Allows credentials in CORS responses

Changes in v7.0:
- FIX: Allow OPTIONS requests (CORS preflight) to pass without authentication
- Prevents 401 errors on preflight requests that block CORS
- OPTIONS requests now bypass all authentication checks

Changes in v6.0:
- FIX: Use 'id' instead of '_key' when extracting user ID from DB
- Adapter now returns documents with 'id' field (not '_key')
- Fixed SSO user creation and existing user extraction
- Resolves "NoneType is not iterable" error in SSO mode

Authentication middleware
Validates tokens and injects user into request state
Supports 3 auth modes: none, local, sso
"""

import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.security import decode_access_token
from src.core.config import settings
from src.database.factory import get_database

logger = logging.getLogger(__name__)


# Generic user for "none" mode
GENERIC_USER = {
    "id": "user-generic",
    "name": "John Doe",
    "email": "generic@example.com",
    "role": "user",
    "status": "active",
    "group_ids": []
}


def get_cors_headers() -> Dict[str, str]:
    """
    Get CORS headers for error responses
    
    Returns:
        Dict with CORS headers
    """
    origins = settings.get_cors_origins()
    return {
        "Access-Control-Allow-Origin": origins[0] if origins else "*",
        "Access-Control-Allow-Credentials": "true"
    }


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware
    
    Supports 3 authentication modes:
    
    1. "none" - No authentication, generic user injected
    2. "local" - JWT token validation (default)
    3. "sso" - Single Sign-On via headers
    
    Public routes (no auth required):
    - /docs, /openapi.json, /redoc
    - /health, /
    - /api/auth/login, /api/auth/register, /api/auth/config
    - /api/auth/generic (only in "none" mode)
    - /api/auth/sso/verify (only in "sso" mode)
    - OPTIONS requests (CORS preflight)
    
    Protected routes (auth required):
    - Everything else
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
        "/api/auth/generic",      # Mode-specific, returns 403 if wrong mode
        "/api/auth/sso/verify",   # Mode-specific, returns 403 if wrong mode
    ]
    
    # Routes specific to auth modes
    MODE_SPECIFIC_ROUTES = {
        "none": ["/api/auth/generic"],
        "sso": ["/api/auth/sso/verify"],
    }
    
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
        # ====================================================================
        # Allow OPTIONS requests (CORS preflight) without authentication
        # ====================================================================
        if request.method == "OPTIONS":
            logger.debug(f"OPTIONS request to {request.url.path} - bypassing auth")
            return await call_next(request)
        
        # Check if route is public
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Check mode-specific public routes
        if self._is_mode_specific_public_route(request.url.path):
            return await call_next(request)
        
        # ====================================================================
        # MODE: none - No authentication required
        # ====================================================================
        if settings.AUTH_MODE == "none":
            logger.debug("Auth mode: none - injecting generic user")
            request.scope["user"] = GENERIC_USER
            return await call_next(request)
        
        # ====================================================================
        # MODE: sso - Single Sign-On via headers
        # ====================================================================
        elif settings.AUTH_MODE == "sso":
            return await self._handle_sso_auth(request, call_next)
        
        # ====================================================================
        # MODE: local - JWT token validation (default)
        # ====================================================================
        elif settings.AUTH_MODE == "local":
            return await self._handle_local_auth(request, call_next)
        
        # Unknown mode
        else:
            logger.error(f"Unknown AUTH_MODE: {settings.AUTH_MODE}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Invalid authentication configuration",
                    "code": "INTERNAL_ERROR"
                },
                status_code=500,
                headers=get_cors_headers()  # v8.0: Add CORS headers
            )
    
    async def _handle_sso_auth(
        self,
        request: Request,
        call_next: Callable
    ):
        """
        Handle SSO authentication via headers
        
        Extracts user info from configured SSO headers.
        Auto-creates user if not exists.
        
        Args:
            request: Incoming request
            call_next: Next handler
            
        Returns:
            Response or error
        """
        # Extract SSO headers
        token = request.headers.get(settings.SSO_TOKEN_HEADER)
        email = request.headers.get(settings.SSO_EMAIL_HEADER)
        name = request.headers.get(settings.SSO_NAME_HEADER)
        
        if not all([token, email]):
            logger.warning(f"Missing SSO headers: token={bool(token)}, email={bool(email)}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Missing required SSO headers: {settings.SSO_TOKEN_HEADER}, {settings.SSO_EMAIL_HEADER}",
                    "code": "UNAUTHORIZED"
                },
                status_code=401,
                headers=get_cors_headers()  # v8.0: Add CORS headers
            )
        
        # Get or create user
        try:
            db = get_database()
            
            # Check if user exists
            existing_user = db.find_one("users", {"email": email})
            
            if existing_user:
                # User exists - use it
                user = {
                    "id": existing_user.get("id"),
                    "name": existing_user.get("name"),
                    "email": existing_user.get("email"),
                    "role": existing_user.get("role", "user"),
                    "status": existing_user.get("status", "active"),
                    "group_ids": existing_user.get("group_ids", [])
                }
                logger.debug(f"SSO: Found existing user {user['id']}")
            else:
                # User doesn't exist - create it
                from datetime import datetime
                from src.core.security import hash_password
                
                new_user = db.create("users", {
                    "name": name or email.split("@")[0],
                    "email": email,
                    "password_hash": hash_password("sso-no-password"),  # Dummy password
                    "role": "user",
                    "status": "active",
                    "group_ids": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": None
                })
                
                user = {
                    "id": new_user.get("id"),
                    "name": new_user.get("name"),
                    "email": new_user.get("email"),
                    "role": "user",
                    "status": "active",
                    "group_ids": []
                }
                logger.info(f"SSO: Auto-created user {user['id']} for {email}")
            
            # Inject user into request
            request.scope["user"] = user
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"SSO auth failed: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "success": False,
                    "error": "SSO authentication failed",
                    "code": "UNAUTHORIZED"
                },
                status_code=401,
                headers=get_cors_headers()  # v8.0: Add CORS headers
            )
    
    async def _handle_local_auth(
        self,
        request: Request,
        call_next: Callable
    ):
        """
        Handle local JWT authentication
        
        Validates Bearer token and extracts user.
        v9.0: Loads full user from DB to get group_ids.
        
        Args:
            request: Incoming request
            call_next: Next handler
            
        Returns:
            Response or error
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Missing Authorization header",
                    "code": "UNAUTHORIZED"
                },
                status_code=401,
                headers=get_cors_headers()  # v8.0: Add CORS headers
            )
        
        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Invalid Authorization header format",
                    "code": "UNAUTHORIZED"
                },
                status_code=401,
                headers=get_cors_headers()  # v8.0: Add CORS headers
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
                    status_code=401,
                    headers=get_cors_headers()  # v8.0: Add CORS headers
                )
            
            # v9.0: Load full user from database to get group_ids
            try:
                db = get_database()
                db_user = db.get_by_id("users", user_id)
                
                if not db_user:
                    logger.warning(f"User {user_id} from token not found in DB")
                    return JSONResponse(
                        content={
                            "success": False,
                            "error": "User not found",
                            "code": "UNAUTHORIZED"
                        },
                        status_code=401,
                        headers=get_cors_headers()  # v8.0: Add CORS headers
                    )
                
                # Inject full user with group_ids
                request.scope["user"] = {
                    "id": db_user.get("id"),
                    "name": db_user.get("name"),
                    "email": db_user.get("email"),
                    "role": db_user.get("role", "user"),
                    "status": db_user.get("status", "active"),
                    "group_ids": db_user.get("group_ids", [])
                }
                
                logger.debug(f"Authenticated user: {user_id} with groups: {db_user.get('group_ids', [])}")
                
            except Exception as db_error:
                logger.error(f"Failed to load user from DB: {db_error}")
                # Fallback to token payload only (no group_ids)
                request.scope["user"] = {
                    "id": user_id,
                    "role": payload.get("role", "user"),
                    "group_ids": []
                }
                logger.warning(f"Fallback: User {user_id} loaded without group_ids")
            
            logger.debug(f"Authenticated user: {user_id}")
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Invalid or expired token",
                    "code": "UNAUTHORIZED"
                },
                status_code=401,
                headers=get_cors_headers()  # v8.0: Add CORS headers
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
        for public_path in self.PUBLIC_ROUTES:
            if public_path != "/" and path.startswith(public_path + "/"):
                return True
        
        return False
    
    def _is_mode_specific_public_route(self, path: str) -> bool:
        """
        Check if route is mode-specific public route
        
        Routes like /api/auth/generic (none mode) or /api/auth/sso/verify (sso mode)
        should be accessible without auth in their respective modes.
        
        Args:
            path: Request path
            
        Returns:
            True if mode-specific public route
        """
        mode_routes = self.MODE_SPECIFIC_ROUTES.get(settings.AUTH_MODE, [])
        return path in mode_routes