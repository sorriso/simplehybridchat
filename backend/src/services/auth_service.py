"""
Path: backend/src/services/auth_service.py
Version: 3.3

Changes in v3.3:
- FIX: SSO response Dict now uses camelCase keys (accessToken, tokenType, expiresIn)
- Matches API convention for consistent frontend integration

Changes in v3.2:
- FIX: verify_sso_session now returns Dict[str, Any] instead of TokenResponse
- Dict includes: access_token, token_type, expires_in, user (UserResponse)
- TokenResponse in project doesn't support 'user' field
- This allows SSO to return both token info and user data

Changes in v3.1:
- FIX: Added expires_in=0 to TokenResponse in verify_sso_session()
- SSO tokens don't expire (handled by SSO provider)

Changes in v3:
- Added verify_sso_session() method for SSO authentication
- Auto-creates user if doesn't exist in SSO mode
- Returns TokenResponse with user info and dummy token

Authentication service for login, register, token management
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import logging

from src.core.security import hash_password, verify_password, create_access_token, decode_access_token
from src.core.config import settings
from src.repositories.user_repository import UserRepository
from src.database.interface import IDatabase
from src.database.exceptions import DuplicateKeyError, NotFoundError
from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, TokenPayload
from src.models.user import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service
    
    Handles user authentication operations:
    - User registration
    - Login with JWT tokens
    - SSO session verification (mode "sso")
    - Token validation
    """
    
    def __init__(self, db: IDatabase):
        """
        Initialize auth service
        
        Args:
            db: Database interface
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register(self, request: RegisterRequest) -> UserResponse:
        """
        Register new user
        
        Args:
            request: Registration request with name, email, password
            
        Returns:
            UserResponse with created user info
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            # Check if email exists
            existing_user = self.user_repo.get_by_email(request.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
            
            # Hash password
            password_hash = hash_password(request.password)
            
            # Create user
            user_data = {
                "name": request.name,
                "email": request.email,
                "password_hash": password_hash,
                "role": "user",  # Default role
                "status": "active",  # Default status
                "group_ids": [],
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            
            user = self.user_repo.create(user_data)
            
            return UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                status=user.get("status", "active"),
                group_ids=user.get("group_ids", []),
                created_at=user["created_at"],
                updated_at=user.get("updated_at")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate user and generate JWT token
        
        Args:
            request: Login request with email and password
            
        Returns:
            TokenResponse with JWT token
            
        Raises:
            HTTPException: If credentials invalid or user disabled
        """
        try:
            # Find user by email
            user = self.user_repo.get_by_email(request.email)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not verify_password(request.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check user status
            if user.get("status") != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
            # Generate JWT token
            token_data = {
                "sub": user["id"],
                "email": user["email"],
                "role": user["role"]
            }
            
            access_token = create_access_token(token_data)
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.JWT_EXPIRATION_HOURS * 3600
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dict
            
        Raises:
            HTTPException: If token invalid or expired
        """
        try:
            payload = decode_access_token(token)
            
            # Get user to verify still exists and is active
            user = self.user_repo.get_by_id(payload["sub"])
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if user.get("status") != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "role": user["role"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def verify_sso_session(
        self,
        sso_token: str,
        email: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify SSO session and get/create user
        
        Used in SSO mode to validate SSO headers and return user info.
        Auto-creates user if doesn't exist in database.
        
        Args:
            sso_token: SSO token from header
            email: User email from SSO header
            name: User name from SSO header (optional)
            
        Returns:
            Dict with token info and user data (camelCase keys):
            {
                "accessToken": "sso-authenticated",
                "tokenType": "sso",
                "expiresIn": 0,
                "user": UserResponse model (as dict via .model_dump())
            }
            
        Raises:
            HTTPException: If verification fails or user is disabled
        """
        try:
            # Check if user exists
            user = self.user_repo.get_by_email(email)
            
            if user:
                # User exists - return it
                logger.info(f"SSO: Found existing user {user['id']} ({email})")
            else:
                # User doesn't exist - create it
                user_data = {
                    "name": name or email.split("@")[0],
                    "email": email,
                    "password_hash": hash_password("sso-no-password"),  # Dummy password
                    "role": "user",
                    "status": "active",
                    "group_ids": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": None
                }
                
                user = self.user_repo.create(user_data)
                logger.info(f"SSO: Auto-created user {user['id']} ({email})")
            
            # Check user status
            if user.get("status") == "disabled":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
            # Prepare user response
            user_response = UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                status=user.get("status", "active"),
                group_ids=user.get("group_ids", []),
                created_at=user["created_at"],
                updated_at=user.get("updated_at")
            )
            
            # In SSO mode, return token info + user data as dict
            # (TokenResponse doesn't support 'user' field in the project)
            # Use camelCase keys for API consistency
            return {
                "accessToken": "sso-authenticated",  # Dummy token
                "tokenType": "sso",
                "expiresIn": 0,  # No expiration for SSO
                "user": user_response.model_dump(by_alias=True)
            }
            
        except HTTPException:
            raise
        except DuplicateKeyError:
            # Race condition: user was created between check and create
            # Retry once
            user = self.user_repo.get_by_email(email)
            if user:
                user_response = UserResponse(
                    id=user["id"],
                    name=user["name"],
                    email=user["email"],
                    role=user["role"],
                    status=user.get("status", "active"),
                    group_ids=user.get("group_ids", []),
                    created_at=user["created_at"],
                    updated_at=user.get("updated_at")
                )
                return {
                    "accessToken": "sso-authenticated",
                    "tokenType": "sso",
                    "expiresIn": 0,
                    "user": user_response.model_dump(by_alias=True)
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SSO verification failed: race condition"
                )
        except Exception as e:
            logger.error(f"SSO verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SSO verification failed: {str(e)}"
            )
    
    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If current password wrong or user not found
        """
        try:
            # Get user
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(current_password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            update_data = {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
            
            self.user_repo.update(user_id, update_data)
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change failed: {str(e)}"
            )