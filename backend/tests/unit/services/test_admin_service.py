"""
Path: backend/tests/unit/services/test_admin_service.py
Version: 1

Unit tests for AdminService
"""

import pytest
from datetime import datetime, timedelta

from src.services.admin_service import AdminService


class TestAdminService:
    """Test AdminService"""
    
    def setup_method(self):
        """Reset state before each test"""
        AdminService._sessions.clear()
        AdminService._maintenance_mode = False
    
    def test_toggle_maintenance_enable(self):
        """Test enable maintenance mode"""
        result = AdminService.toggle_maintenance(True)
        
        assert result["maintenance_mode"] is True
        assert "enabled" in result["message"]
        assert AdminService.is_maintenance_mode() is True
    
    def test_toggle_maintenance_disable(self):
        """Test disable maintenance mode"""
        AdminService.toggle_maintenance(True)
        result = AdminService.toggle_maintenance(False)
        
        assert result["maintenance_mode"] is False
        assert "disabled" in result["message"]
        assert AdminService.is_maintenance_mode() is False
    
    def test_is_maintenance_mode_default(self):
        """Test maintenance mode is disabled by default"""
        assert AdminService.is_maintenance_mode() is False
    
    def test_add_session(self):
        """Test add session"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        AdminService.add_session(
            session_id="session-1",
            user_id="user-1",
            user_email="user@example.com",
            created_at=now,
            expires_at=expires,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        sessions = AdminService.get_all_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "session-1"
        assert sessions[0]["user_id"] == "user-1"
    
    def test_get_all_sessions(self):
        """Test get all active sessions"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        # Add multiple sessions
        for i in range(3):
            AdminService.add_session(
                session_id=f"session-{i}",
                user_id=f"user-{i}",
                user_email=f"user{i}@example.com",
                created_at=now,
                expires_at=expires
            )
        
        sessions = AdminService.get_all_sessions()
        assert len(sessions) == 3
    
    def test_get_all_sessions_filters_expired(self):
        """Test get_all_sessions filters out expired sessions"""
        now = datetime.utcnow()
        
        # Add active session
        AdminService.add_session(
            session_id="session-active",
            user_id="user-1",
            user_email="user1@example.com",
            created_at=now,
            expires_at=now + timedelta(hours=12)
        )
        
        # Add expired session
        AdminService.add_session(
            session_id="session-expired",
            user_id="user-2",
            user_email="user2@example.com",
            created_at=now - timedelta(hours=24),
            expires_at=now - timedelta(hours=1)
        )
        
        sessions = AdminService.get_all_sessions()
        
        # Only active session should be returned
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "session-active"
        
        # Expired session should be cleaned up
        assert "session-expired" not in AdminService._sessions
    
    def test_revoke_all_sessions(self):
        """Test revoke all sessions"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        # Add sessions
        for i in range(3):
            AdminService.add_session(
                session_id=f"session-{i}",
                user_id=f"user-{i}",
                user_email=f"user{i}@example.com",
                created_at=now,
                expires_at=expires
            )
        
        count = AdminService.revoke_all_sessions()
        
        assert count == 3
        assert len(AdminService._sessions) == 0
        assert len(AdminService.get_all_sessions()) == 0
    
    def test_revoke_session(self):
        """Test revoke specific session"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        AdminService.add_session(
            session_id="session-1",
            user_id="user-1",
            user_email="user1@example.com",
            created_at=now,
            expires_at=expires
        )
        AdminService.add_session(
            session_id="session-2",
            user_id="user-2",
            user_email="user2@example.com",
            created_at=now,
            expires_at=expires
        )
        
        result = AdminService.revoke_session("session-1")
        
        assert result is True
        sessions = AdminService.get_all_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "session-2"
    
    def test_revoke_session_not_found(self):
        """Test revoke nonexistent session"""
        result = AdminService.revoke_session("nonexistent")
        assert result is False
    
    def test_is_session_valid(self):
        """Test check if session is valid"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        AdminService.add_session(
            session_id="session-1",
            user_id="user-1",
            user_email="user1@example.com",
            created_at=now,
            expires_at=expires
        )
        
        assert AdminService.is_session_valid("session-1") is True
        assert AdminService.is_session_valid("nonexistent") is False
    
    def test_is_session_valid_expired(self):
        """Test expired session is not valid"""
        now = datetime.utcnow()
        
        AdminService.add_session(
            session_id="session-expired",
            user_id="user-1",
            user_email="user1@example.com",
            created_at=now - timedelta(hours=24),
            expires_at=now - timedelta(hours=1)
        )
        
        # Session should be invalid and removed
        assert AdminService.is_session_valid("session-expired") is False
        assert "session-expired" not in AdminService._sessions
    
    def test_get_session(self):
        """Test get session info"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=12)
        
        AdminService.add_session(
            session_id="session-1",
            user_id="user-1",
            user_email="user1@example.com",
            created_at=now,
            expires_at=expires,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        session = AdminService.get_session("session-1")
        
        assert session is not None
        assert session["session_id"] == "session-1"
        assert session["user_id"] == "user-1"
        assert session["ip_address"] == "192.168.1.1"
    
    def test_get_session_not_found(self):
        """Test get nonexistent session"""
        session = AdminService.get_session("nonexistent")
        assert session is None
    
    def test_sessions_isolated_between_tests(self):
        """Test sessions don't leak between tests"""
        # This test verifies setup_method works
        assert len(AdminService._sessions) == 0
        assert AdminService.is_maintenance_mode() is False