"""
Path: backend/src/api/routes/auth.py
Version: 6.0

Changes in v6.0:
- FRONTEND COMPATIBILITY: Use ConfigResponse instead of SuccessResponse for /config
- FRONTEND COMPATIBILITY: Use LoginResponse instead of SuccessResponse for /login
- FRONTEND COMPATIBILITY: Use SingleUserResponse for /generic, /verify
- Accept both 'email' and 'username' in LoginRequest
- Return {token, user} format for /login
- Return {config: {...}} format for /config

Changes in v5.0:
- Added GET /auth/verify endpoint for token verification
- Added GET /auth/sessions endpoint (root only) for session listing
- Added POST /auth/revoke-all-sessions endpoint (root only)
- Added POST /auth/revoke-own-session endpoint for current user session revocation
- Session management uses AdminService for session tracking

Authentication endpoints
"""

from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.models.auth import (
    LoginRequest, RegisterRequest, TokenResponse, AuthStatus, 
    ConfigResponse, AuthConfigData, SsoConfigData, LoginResponse
)
from src.models.user import UserResponse, PasswordChange
from src.models.responses import SuccessResponse, EmptyResponse, SingleUserResponse
from src.services.auth_service import AuthService
from src.services.admin_service import AdminService
from src.api.deps import get_database, UserFromRequest


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# MODE-SPECIFIC ENDPOINTS
# ============================================================================

@router.get("/generic", response_model=SingleUserResponse[UserResponse])
async def get_generic_user() -> SingleUserResponse[UserResponse]:
    """
    Get generic user (mode "none" only)
    
    Returns the generic user used when AUTH_MODE=none.
    This endpoint is only available when authentication is disabled.
    
    Frontend expects:
    {
      "user": {...}
    }
    
    Returns:
    - 200 OK: Generic user info
    - 403 Forbidden: Not in "none" mode
    
    No authentication required (only works in "none" mode).
    """
    if settings.AUTH_MODE != "none":
        raise HTTPException(
            status_code=403,
            detail=f"This endpoint is only available in 'none' auth mode. Current mode: {settings.AUTH_MODE}"
        )
    
    # Return generic user
    from datetime import datetime
    generic_user = UserResponse(
        id="user-generic",
        name="John Doe",
        email="generic@example.com",
        role="user",
        status="active",
        created_at=datetime(2024, 1, 1),
        updated_at=None
    )
    
    return SingleUserResponse(user=generic_user)


@router.get("/sso/verify", response_model=SuccessResponse[Dict[str, Any]])
async def verify_sso_session(
    request: Request,
    db = Depends(get_database)
) -> SuccessResponse[Dict[str, Any]]:
    """
    Verify SSO session (mode "sso" only)
    
    Validates SSO headers and returns user info.
    Auto-creates user if doesn't exist.
    
    Required headers (configured via settings):
    - X-Auth-Token (or configured SSO_TOKEN_HEADER)
    - X-User-Email (or configured SSO_EMAIL_HEADER)
    - X-User-Name (or configured SSO_NAME_HEADER, optional)
    
    Returns:
    - 200 OK: User verified/created with token and user data
    - 401 Unauthorized: Missing/invalid SSO headers
    - 403 Forbidden: Not in "sso" mode
    
    No Bearer token required (uses SSO headers).
    """
    if settings.AUTH_MODE != "sso":
        raise HTTPException(
            status_code=403,
            detail=f"This endpoint is only available in 'sso' auth mode. Current mode: {settings.AUTH_MODE}"
        )
    
    # Extract SSO headers
    token = request.headers.get(settings.SSO_TOKEN_HEADER)
    name = request.headers.get(settings.SSO_NAME_HEADER)
    email = request.headers.get(settings.SSO_EMAIL_HEADER)
    
    # Validate required headers
    if not all([token, email]):
        raise HTTPException(
            status_code=401,
            detail=f"Missing required SSO headers: {settings.SSO_TOKEN_HEADER}, {settings.SSO_EMAIL_HEADER}"
        )
    
    # Verify SSO session and get/create user
    auth_service = AuthService(db=db)
    sso_data = auth_service.verify_sso_session(
        sso_token=token,
        email=email,
        name=name
    )
    
    # sso_data is Dict: {access_token, token_type, expires_in, user}
    return SuccessResponse(
        data=sso_data,
        message="SSO session verified"
    )


# ============================================================================
# LOCAL AUTH ENDPOINTS
# ============================================================================

@router.post("/register", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Register new user (mode "local" only)
    
    Creates a new user account with default 'user' role.
    Password must be at least 8 characters with uppercase, lowercase, and digit.
    
    - **name**: User full name
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    
    Returns:
    - 201 Created: User registered successfully
    - 403 Forbidden: Not in "local" mode
    - 409 Conflict: Email already exists
    
    No authentication required.
    """
    if settings.AUTH_MODE != "local":
        raise HTTPException(
            status_code=403,
            detail=f"Registration is only available in 'local' auth mode. Current mode: {settings.AUTH_MODE}"
        )
    
    auth_service = AuthService(db=db)
    user = auth_service.register(request)
    
    return SuccessResponse(
        data=user,
        message="User registered successfully"
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db = Depends(get_database)
) -> LoginResponse:
    """
    Login with email and password (mode "local" only)
    
    Authenticates user and returns JWT access token with user info.
    Token expires after configured duration (default 12 hours).
    
    Frontend expects:
    {
      "token": "jwt-token",
      "user": {...}
    }
    
    - **email** or **username**: User email/username
    - **password**: User password
    
    Returns:
    - 200 OK: Login successful with JWT token and user info
    - 401 Unauthorized: Invalid credentials
    - 403 Forbidden: Not in "local" mode
    
    Use returned token in Authorization header: `Bearer <token>`
    
    No authentication required.
    """
    if settings.AUTH_MODE != "local":
        raise HTTPException(
            status_code=403,
            detail=f"Login is only available in 'local' auth mode. Current mode: {settings.AUTH_MODE}"
        )
    
    auth_service = AuthService(db=db)
    
    # Get token
    token_response = auth_service.login(request)
    
    # Get user info from repository
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(db=db)
    user_data = user_repo.get_by_email(request.email)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Build user response
    user_response = UserResponse(**user_data)
    
    return LoginResponse(
        token=token_response.access_token,
        user=user_response
    )


# ============================================================================
# COMMON ENDPOINTS (ALL MODES)
# ============================================================================

@router.post("/logout", response_model=EmptyResponse)
async def logout(
    user: UserFromRequest
) -> EmptyResponse:
    """
    Logout current user
    
    Invalidates current session (if applicable).
    In JWT mode, client should discard the token.
    
    Returns:
    - 200 OK: Logout successful
    - 401 Unauthorized: Not authenticated
    
    Requires authentication.
    """
    # In JWT mode, logout is client-side (discard token)
    # In SSO mode, logout might need to redirect to SSO provider
    # For now, just return success
    
    return EmptyResponse(message="Logout successful")


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_current_user(
    user: UserFromRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Get current authenticated user
    
    Returns complete user information for the authenticated user.
    
    Returns:
    - 200 OK: User information
    - 401 Unauthorized: Not authenticated
    
    Requires authentication.
    """
    from src.services.user_service import UserService
    from datetime import datetime
    
    # In "none" mode, return generic user directly (not in DB)
    if settings.AUTH_MODE == "none":
        generic_user = UserResponse(
            id=user["id"],
            name=user.get("name", "John Doe"),
            email=user.get("email", "generic@example.com"),
            role=user.get("role", "user"),
            status=user.get("status", "active"),
            group_ids=user.get("group_ids", []),
            created_at=datetime(2024, 1, 1),
            updated_at=None
        )
        return SuccessResponse(data=generic_user)
    
    # For other modes, load full user profile from DB
    user_service = UserService(db=db)
    profile = user_service.get_current_user_profile(user)
    
    return SuccessResponse(data=profile)


@router.post("/change-password", response_model=EmptyResponse)
async def change_password(
    request: PasswordChange,
    user: UserFromRequest,
    db = Depends(get_database)
) -> EmptyResponse:
    """
    Change user password (mode "local" only)
    
    Changes password for the authenticated user.
    Requires current password for verification.
    
    - **current_password**: Current password
    - **new_password**: New password (min 8 chars, uppercase, lowercase, digit)
    
    Returns:
    - 200 OK: Password changed
    - 401 Unauthorized: Current password incorrect
    - 403 Forbidden: Not in "local" mode
    
    Requires authentication.
    """
    if settings.AUTH_MODE != "local":
        raise HTTPException(
            status_code=403,
            detail=f"Password change is only available in 'local' auth mode. Current mode: {settings.AUTH_MODE}"
        )
    
    auth_service = AuthService(db=db)
    auth_service.change_password(
        user_id=user["id"],
        current_password=request.current_password,
        new_password=request.new_password
    )
    
    return EmptyResponse(message="Password changed successfully")


@router.get("/status", response_model=SuccessResponse[AuthStatus])
async def auth_status(
    user: UserFromRequest
) -> SuccessResponse[AuthStatus]:
    """
    Get authentication status
    
    Returns current authentication status and user information.
    
    Returns:
    - 200 OK: Auth status
    - 401 Unauthorized: Not authenticated
    
    Requires authentication.
    """
    status_data = AuthStatus(
        authenticated=True,
        user_id=user["id"],
        email=user.get("email", ""),
        role=user.get("role", "user")
    )
    
    return SuccessResponse(data=status_data)


@router.get("/config", response_model=ConfigResponse)
async def get_auth_config() -> ConfigResponse:
    """
    Get authentication configuration
    
    Returns current auth mode and SSO configuration.
    Useful for frontend to adapt UI based on auth mode.
    
    Frontend expects:
    {
      "config": {
        "mode": "local",
        "allowMultiLogin": false,
        "maintenanceMode": false,
        "ssoConfig": null
      }
    }
    
    Returns:
    - 200 OK: Auth configuration
    
    No authentication required (public endpoint).
    """
    # Build SSO config if in SSO mode
    sso_config = None
    if settings.AUTH_MODE == "sso":
        sso_config = SsoConfigData(
            token_header=settings.SSO_TOKEN_HEADER,
            name_header=settings.SSO_NAME_HEADER,
            email_header=settings.SSO_EMAIL_HEADER
        )
    
    config_data = AuthConfigData(
        mode=settings.AUTH_MODE,
        allow_multi_login=settings.ALLOW_MULTI_LOGIN,
        maintenance_mode=AdminService.is_maintenance_mode(),
        sso_config=sso_config
    )
    
    return ConfigResponse(config=config_data)


@router.get("/verify", response_model=SingleUserResponse[UserResponse])
async def verify_token(
    user: UserFromRequest,
    db = Depends(get_database)
) -> SingleUserResponse[UserResponse]:
    """
    Verify JWT token validity
    
    Validates the current JWT token and returns user information.
    Useful for frontend to check if token is still valid.
    
    Frontend expects:
    {
      "user": {...}
    }
    
    Returns:
    - 200 OK: Token valid with user info
    - 401 Unauthorized: Token invalid or expired
    
    Requires authentication.
    """
    from src.services.user_service import UserService
    
    user_service = UserService(db=db)
    profile = user_service.get_current_user_profile(user)
    
    return SingleUserResponse(user=profile)


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS (ROOT ONLY)
# ============================================================================

def _check_root_permission(current_user: UserFromRequest) -> None:
    """
    Verify user is root
    
    Raises:
        HTTPException 403: If user is not root
    """
    if current_user.get("role") != "root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: root permission required"
        )


@router.get("/sessions", response_model=SuccessResponse[Dict[str, Any]])
async def list_sessions(
    current_user: UserFromRequest
) -> SuccessResponse[Dict[str, Any]]:
    """
    List all active sessions (root only)
    
    Returns list of all active user sessions with metadata.
    Useful for monitoring and admin purposes.
    
    Returns:
    - 200 OK: List of active sessions
    - 403 Forbidden: Not root user
    
    Requires root authentication.
    """
    _check_root_permission(current_user)
    
    sessions = AdminService.list_sessions()
    
    return SuccessResponse(
        data={
            "sessions": sessions,
            "totalCount": len(sessions)
        },
        message=f"Found {len(sessions)} active sessions"
    )


@router.post("/revoke-all-sessions", response_model=SuccessResponse[Dict[str, Any]])
async def revoke_all_sessions(
    current_user: UserFromRequest
) -> SuccessResponse[Dict[str, Any]]:
    """
    Revoke all user sessions (root only)
    
    Invalidates all active sessions for all users.
    Useful for emergency situations or security incidents.
    
    Returns:
    - 200 OK: Sessions revoked
    - 403 Forbidden: Not root user
    
    Requires root authentication.
    """
    _check_root_permission(current_user)
    
    revoked_count = AdminService.revoke_all_sessions()
    
    return SuccessResponse(
        data={
            "revokedCount": revoked_count,
            "message": f"Revoked {revoked_count} sessions"
        },
        message="All sessions revoked successfully"
    )


@router.post("/revoke-own-session", response_model=EmptyResponse)
async def revoke_own_session(
    current_user: UserFromRequest
) -> EmptyResponse:
    """
    Revoke own session
    
    Invalidates the current user's session.
    Useful for explicit logout with session tracking.
    
    Returns:
    - 200 OK: Session revoked
    - 401 Unauthorized: Not authenticated
    
    Requires authentication.
    """
    user_id = current_user.get("id")
    AdminService.revoke_user_session(user_id)
    
    return EmptyResponse(message="Session revoked successfully")