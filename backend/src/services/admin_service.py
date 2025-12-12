"""
Path: backend/src/services/admin_service.py
Version: 2.0

Changes in v2.0:
- Added list_sessions() method as public alias for get_all_sessions()
- Added revoke_user_session(user_id) method to revoke sessions by user
- Support for session management from auth routes

Service for admin operations (maintenance mode, sessions)
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service for admin operations
    
    Handles:
    - Maintenance mode toggle
    - Sessions management (in-memory for MVP)
    
    Note: In production, sessions should be stored in database/redis
    """
    
    # In-memory sessions storage (MVP)
    # In production: use Redis or ArangoDB collection
    _sessions: Dict[str, Dict[str, Any]] = {}
    
    # Maintenance mode flag (runtime)
    _maintenance_mode: bool = False
    
    @classmethod
    def toggle_maintenance(cls, enabled: bool) -> Dict[str, Any]:
        """
        Toggle maintenance mode
        
        When enabled, only root users can access the API.
        Regular users receive 503 Service Unavailable.
        
        Args:
            enabled: Enable or disable maintenance mode
            
        Returns:
            Dict with maintenance_mode status and message
        """
        cls._maintenance_mode = enabled
        
        status = "enabled" if enabled else "disabled"
        logger.warning(f"Maintenance mode {status}")
        
        return {
            "maintenance_mode": enabled,
            "message": f"Maintenance mode {status}"
        }
    
    @classmethod
    def is_maintenance_mode(cls) -> bool:
        """
        Check if maintenance mode is active
        
        Returns:
            True if maintenance mode is enabled
        """
        return cls._maintenance_mode
    
    @classmethod
    def add_session(
        cls,
        session_id: str,
        user_id: str,
        user_email: str,
        created_at: datetime,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None
    ) -> None:
        """
        Register a new session
        
        Called by auth service when token is created.
        
        Args:
            session_id: Unique session identifier (JWT jti claim)
            user_id: User ID
            user_email: User email
            created_at: Session creation time
            expires_at: Session expiration time
            ip_address: Client IP address
            user_agent: Client user agent
        """
        cls._sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "user_email": user_email,
            "created_at": created_at,
            "expires_at": expires_at,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        logger.info(f"Session registered: {session_id} for user {user_id}")
    
    @classmethod
    def get_all_sessions(cls) -> List[Dict[str, Any]]:
        """
        Get all active sessions
        
        Returns:
            List of session info dicts
        """
        now = datetime.utcnow()
        
        # Filter out expired sessions
        active_sessions = [
            session for session in cls._sessions.values()
            if session["expires_at"] > now
        ]
        
        # Clean up expired sessions
        expired_ids = [
            sid for sid, session in cls._sessions.items()
            if session["expires_at"] <= now
        ]
        for sid in expired_ids:
            del cls._sessions[sid]
        
        return active_sessions
    
    @classmethod
    def revoke_all_sessions(cls) -> int:
        """
        Revoke all sessions
        
        Clears all active sessions, forcing all users to re-authenticate.
        
        Returns:
            Number of sessions revoked
        """
        count = len(cls._sessions)
        cls._sessions.clear()
        
        logger.warning(f"All sessions revoked: {count} sessions")
        
        return count
    
    @classmethod
    def revoke_session(cls, session_id: str) -> bool:
        """
        Revoke a specific session
        
        Args:
            session_id: Session ID to revoke
            
        Returns:
            True if session was found and revoked
        """
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            logger.info(f"Session revoked: {session_id}")
            return True
        
        return False
    
    @classmethod
    def is_session_valid(cls, session_id: str) -> bool:
        """
        Check if a session is valid (exists and not expired)
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if session is valid
        """
        if session_id not in cls._sessions:
            return False
        
        session = cls._sessions[session_id]
        now = datetime.utcnow()
        
        if session["expires_at"] <= now:
            # Session expired, remove it
            del cls._sessions[session_id]
            return False
        
        return True
    
    @classmethod
    def get_session(cls, session_id: str) -> Dict[str, Any] | None:
        """
        Get session info
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info dict or None if not found
        """
        return cls._sessions.get(session_id)
    
    @classmethod
    def list_sessions(cls) -> List[Dict[str, Any]]:
        """
        List all active sessions (public API)
        
        Alias for get_all_sessions() with serializable datetime format.
        
        Returns:
            List of session info dicts with ISO formatted timestamps
        """
        sessions = cls.get_all_sessions()
        
        # Convert datetime objects to ISO strings for JSON serialization
        serialized_sessions = []
        for session in sessions:
            serialized = session.copy()
            if isinstance(serialized.get("created_at"), datetime):
                serialized["created_at"] = serialized["created_at"].isoformat()
            if isinstance(serialized.get("expires_at"), datetime):
                serialized["expires_at"] = serialized["expires_at"].isoformat()
            serialized_sessions.append(serialized)
        
        return serialized_sessions
    
    @classmethod
    def revoke_user_session(cls, user_id: str) -> int:
        """
        Revoke all sessions for a specific user
        
        Args:
            user_id: User ID whose sessions to revoke
            
        Returns:
            Number of sessions revoked
        """
        sessions_to_revoke = [
            sid for sid, session in cls._sessions.items()
            if session["user_id"] == user_id
        ]
        
        for sid in sessions_to_revoke:
            del cls._sessions[sid]
        
        if sessions_to_revoke:
            logger.info(f"Revoked {len(sessions_to_revoke)} sessions for user {user_id}")
        
        return len(sessions_to_revoke)