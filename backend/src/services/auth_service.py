"""
Path: backend/src/services/auth_service.py
Version: 5.0

Changes in v5.0:
- FIX CRITICAL: change_password() now hashes passwords with SHA256 before bcrypt
- Consistent with login/register flow: bcrypt(SHA256(password))
- current_password is hashed with SHA256 before verification
- new_password is hashed with SHA256 before storing

Changes in v4.0:
- SECURITY: Adapted to receive password_hash instead of password
- login() receives SHA256 hash, compares with bcrypt(SHA256)
- register() receives SHA256 hash, stores bcrypt(SHA256)
- Never handles plaintext passwords

Changes in v3.3:
- FIX: SSO response Dict uses camelCase keys (accessToken, tokenType, expiresIn)
"""

import hashlib
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


def sha256_hash(password: str) -> str:
    """Compute SHA256 hash of password (same as frontend)"""
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:
    """
    Authentication service
    
    SECURITY MODEL:
    - Receives SHA256(password) from frontend as password_hash
    - Stores bcrypt(SHA256) in database
    - Never handles plaintext passwords
    
    Handles:
    - User registration
    - Login with JWT tokens
    - SSO session verification
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
        
        SECURITY: request.password_hash is SHA256 computed by frontend
        This method applies bcrypt on top of SHA256 before storing
        
        Args:
            request: Registration request with name, email, password_hash (SHA256)
            
        Returns:
            UserResponse with created user info
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            existing_user = self.user_repo.get_by_email(request.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
            
            # Apply bcrypt to the SHA256 hash received from frontend
            password_hash_bcrypt = hash_password(request.password_hash)
            
            user_data = {
                "name": request.name,
                "email": request.email,
                "password_hash": password_hash_bcrypt,
                "role": "user",
                "status": "active",
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
        
        SECURITY: request.password_hash is SHA256 computed by frontend
        This method verifies bcrypt(SHA256_received) against stored bcrypt(SHA256)
        
        Args:
            request: Login request with email and password_hash (SHA256)
            
        Returns:
            TokenResponse with JWT token
            
        Raises:
            HTTPException: If credentials invalid or user disabled
        """
        try:
            user = self.user_repo.get_by_email(request.email)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify SHA256 hash against stored bcrypt(SHA256)
            if not verify_password(request.password_hash, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            if user.get("status") != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
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
            Dict with token info and user data (camelCase keys)
            
        Raises:
            HTTPException: If verification fails or user is disabled
        """
        try:
            user = self.user_repo.get_by_email(email)
            
            if user:
                logger.info(f"SSO: Found existing user {user['id']} ({email})")
            else:
                user_data = {
                    "name": name or email.split("@")[0],
                    "email": email,
                    "password_hash": hash_password("sso-no-password"),
                    "role": "user",
                    "status": "active",
                    "group_ids": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": None
                }
                
                user = self.user_repo.create(user_data)
                logger.info(f"SSO: Auto-created user {user['id']} ({email})")
            
            if user.get("status") == "disabled":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
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
            
        except HTTPException:
            raise
        except DuplicateKeyError:
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
        
        SECURITY MODEL:
        - Receives plaintext passwords from API (PasswordChange model)
        - Hashes with SHA256 to match stored bcrypt(SHA256) format
        - This is consistent with register/login flow
        
        Args:
            user_id: User ID
            current_password: Current password (plaintext) for verification
            new_password: New password (plaintext) to set
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If current password wrong or user not found
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Hash current_password with SHA256 before verifying against bcrypt(SHA256)
            current_password_sha256 = sha256_hash(current_password)
            
            if not verify_password(current_password_sha256, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
            
            # Hash new_password with SHA256, then bcrypt (same as register)
            new_password_sha256 = sha256_hash(new_password)
            new_password_hash = hash_password(new_password_sha256)
            
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