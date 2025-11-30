"""
Path: src/api/routes/auth.py
Version: 2.1 - Fix NameError AuthConfig

Authentication endpoints

Changes in v2.1:
- FIX: Import AuthConfig en haut du fichier (pas dynamique)
- FIX: Import settings pour get_auth_config()

Changes in v2:
- Added GET /auth/config route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, AuthStatus, AuthConfig
from src.models.user import UserResponse, PasswordChange
from src.models.responses import SuccessResponse, EmptyResponse
from src.services.auth_service import AuthService
from src.api.deps import get_database, UserFromRequest


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Register new user
    
    Creates a new user account with default 'user' role.
    Password must be at least 8 characters with uppercase, lowercase, and digit.
    
    - **name**: User full name
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    
    Returns created user without password.
    """
    auth_service = AuthService(db=db)
    user = auth_service.register(request)
    
    return SuccessResponse(
        data=user,
        message="User registered successfully"
    )


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    request: LoginRequest,
    db = Depends(get_database)
) -> SuccessResponse[TokenResponse]:
    """
    Login with email and password
    
    Authenticates user and returns JWT access token.
    Token expires after configured duration (default 12 hours).
    
    - **email**: User email
    - **password**: User password
    
    Returns JWT token to use in Authorization header: `Bearer <token>`
    """
    auth_service = AuthService(db=db)
    token = auth_service.login(request)
    
    return SuccessResponse(
        data=token,
        message="Login successful"
    )


@router.post("/logout", response_model=EmptyResponse)
async def logout(
    user: UserFromRequest
) -> EmptyResponse:
    """
    Logout current user
    
    Currently JWT tokens are stateless, so logout is handled client-side
    by discarding the token. Future implementation may include token blacklist.
    
    Requires authentication.
    """
    return EmptyResponse(message="Logged out successfully")


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_current_user(
    user: UserFromRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Get current authenticated user profile
    
    Returns the profile of the currently authenticated user.
    
    Requires authentication.
    """
    from src.services.user_service import UserService
    
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
    Change current user password
    
    Changes the password of the currently authenticated user.
    Requires current password for verification.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, uppercase, lowercase, digit)
    
    Requires authentication.
    """
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
    
    Requires authentication.
    """
    status_data = AuthStatus(
        authenticated=True,
        user_id=user["id"],
        email=user["email"],
        role=user["role"]
    )
    
    return SuccessResponse(data=status_data)


@router.get("/config", response_model=SuccessResponse[AuthConfig])
async def get_auth_config() -> SuccessResponse[AuthConfig]:
    """
    Get authentication configuration
    
    Returns current auth mode and SSO configuration.
    Public endpoint (no authentication required).
    """
    config_data = AuthConfig(
        auth_mode=settings.AUTH_MODE,
        allow_registration=settings.AUTH_MODE == "local",
        sso_enabled=settings.AUTH_MODE == "sso",
        sso_token_header=settings.SSO_TOKEN_HEADER if settings.AUTH_MODE == "sso" else None,
        sso_name_header=settings.SSO_NAME_HEADER if settings.AUTH_MODE == "sso" else None,
        sso_email_header=settings.SSO_EMAIL_HEADER if settings.AUTH_MODE == "sso" else None
    )
    
    return SuccessResponse(data=config_data)