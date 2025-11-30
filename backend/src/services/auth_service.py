"""
Path: src/services/auth_service.py
Version: 2

Authentication service for login, register, token management
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from src.core.security import hash_password, verify_password, create_access_token, decode_access_token
from src.core.config import settings
from src.repositories.user_repository import UserRepository
from src.database.interface import IDatabase
from src.database.exceptions import DuplicateKeyError, NotFoundError
from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, TokenPayload
from src.models.user import UserResponse


class AuthService:
    """
    Authentication service
    
    Handles user authentication operations:
    - Login (email/password)
    - Registration
    - Token generation/validation
    - Password verification
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """
        Initialize auth service
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        self.user_repo = UserRepository(db=db)
    
    def register(self, request: RegisterRequest) -> UserResponse:
        """
        Register new user
        
        Args:
            request: Registration data
            
        Returns:
            Created user (without password)
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            # Hash password
            password_hash = hash_password(request.password)
            
            # Create user data
            user_data = {
                "name": request.name,
                "email": request.email,
                "password_hash": password_hash,
                "role": "user",  # Default role
                "status": "active"
            }
            
            # Create user with validation
            user = self.user_repo.create_with_validation(user_data)
            
            # Return response (exclude password)
            return UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                status=user["status"],
                created_at=datetime.fromisoformat(user["created_at"]),
                updated_at=None
            )
            
        except DuplicateKeyError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already registered: {request.email}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate user and return JWT token
        
        Args:
            request: Login credentials
            
        Returns:
            JWT token response
            
        Raises:
            HTTPException: If credentials invalid
        """
        # Get user by email
        user = self.user_repo.get_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check user is active
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
                "role": user["role"],
                "name": user["name"]
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user from token
        
        Args:
            token: JWT token
            
        Returns:
            User dict
            
        Raises:
            HTTPException: If token invalid
        """
        return self.validate_token(token)
    
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
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            HTTPException: If validation fails
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
            
            # Update user
            self.user_repo.update(user_id, {"password_hash": new_password_hash})
            
            return True
            
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change failed: {str(e)}"
            )