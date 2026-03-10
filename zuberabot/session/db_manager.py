"""Database-backed session manager for multi-user support."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from zuberabot.database.postgres import DatabaseManager


@dataclass
class SessionWrapper:
    """
    Wrapper for database session to provide consistent API.
    
    This maintains compatibility with the existing Session class
    while using database-backed storage.
    """
    
    key: str  # channel:chat_id
    user_id: str
    db_manager: DatabaseManager
    _db_session: Any = None  # Database Session model instance
    
    def __post_init__(self):
        """Load or create database session."""
        self._db_session = self.db_manager.get_or_create_session(self.key, self.user_id)
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get messages from database session."""
        return self._db_session.messages or []
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata from database session."""
        return self._db_session.session_metadata or {}
    
    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._db_session.created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get last updated timestamp."""
        return self._db_session.updated_at
    
    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """
        Add a message to the session.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content
            **kwargs: Additional message metadata
        """
        self.db_manager.add_session_message(self.key, role, content, **kwargs)
        # Refresh local cache
        self._db_session = self.db_manager.get_or_create_session(self.key, self.user_id)
    
    def get_history(self, max_messages: int = 50) -> List[Dict[str, Any]]:
        """
        Get message history for LLM context.
        
        Args:
            max_messages: Maximum messages to return.
        
        Returns:
            List of messages in LLM format.
        """
        return self.db_manager.get_session_history(self.key, max_messages)
    
    def clear(self) -> None:
        """Clear all messages in the session."""
        # This would require a new database method
        logger.warning(f"Session.clear() called for {self.key} - not implemented for DB sessions")


class DatabaseSessionManager:
    """
    Database-backed session manager for multi-user support.
    
    Replaces file-based session management with PostgreSQL-backed storage.
    Provides user isolation and concurrent access support.
    """
    
    def __init__(self, db_manager: DatabaseManager, workspace: Path = None):
        """
        Initialize database session manager.
        
        Args:
            db_manager: Database manager instance
            workspace: Legacy workspace path (kept for compatibility)
        """
        self.db = db_manager
        self.workspace = workspace or Path.home() / ".nanobot"
        self._cache: Dict[str, SessionWrapper] = {}
        
        logger.info("Database session manager initialized")
    
    def get_or_create(self, key: str) -> SessionWrapper:
        """
        Get an existing session or create a new one.
        
        Args:
            key: Session key (format: channel:chat_id)
        
        Returns:
            SessionWrapper instance
        """
        # Check cache
        if key in self._cache:
            return self._cache[key]
        
        # Extract user_id from key
        user_id = self._extract_user_id(key)
        
        # Ensure user exists
        channel, phone = key.split(':', 1)
        self.db.get_or_create_user(phone, channel)
        
        # Create or get workspace for user
        self.db.get_or_create_workspace(user_id)
        
        # Create session wrapper
        session = SessionWrapper(
            key=key,
            user_id=user_id,
            db_manager=self.db
        )
        
        # Cache it
        self._cache[key] = session
        
        return session
    
    def _extract_user_id(self, session_key: str) -> str:
        """
        Extract user_id from session key.
        
        Args:
            session_key: Session key (format: channel:chat_id)
        
        Returns:
            User identifier (format: channel:phone)
        """
        # For WhatsApp: session_key = "whatsapp:+919876543210"
        # user_id should also be "whatsapp:+919876543210"
        return session_key
    
    def save(self, session: SessionWrapper) -> None:
        """
        Save session to database.
        
        In database-backed sessions, this is a no-op since
        changes are committed immediately. Kept for API compatibility.
        
        Args:
            session: Session to save
        """
        # No-op: database sessions auto-save
        pass
    
    def delete(self, key: str) -> bool:
        """
        Delete a session.
        
        Args:
            key: Session key.
        
        Returns:
            True if deleted, False if not found.
        """
        # Remove from cache
        self._cache.pop(key, None)
        
        # Mark as inactive in database
        from zuberabot.database.models import ChatSession
        
        try:
            with self.db.get_session() as session:
                db_session = session.query(ChatSession).filter_by(session_key=key).first()
                if db_session:
                    db_session.is_active = False
                    session.commit()
                    logger.info(f"Deactivated session: {key}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting session {key}: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Returns:
            List of session info dicts.
        """
        from zuberabot.database.models import ChatSession
        
        try:
            with self.db.get_session() as session:
                active_sessions = session.query(ChatSession).filter_by(is_active=True).all()
                return [
                    {
                        "key": s.session_key,
                        "user_id": s.user_id,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                        "message_count": len(s.messages) if s.messages else 0
                    }
                    for s in active_sessions
                ]
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def cleanup_inactive_sessions(self, days: int = 7) -> int:
        """
        Cleanup sessions inactive for specified days.
        
        Args:
            days: Number of days of inactivity
            
        Returns:
            Number of sessions cleaned up
        """
        count = self.db.cleanup_inactive_sessions(days)
        # Clear cache for cleaned up sessions
        self._cache.clear()
        return count
    
    def get_user_workspace(self, user_id: str) -> Optional[str]:
        """
        Get workspace path for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Workspace path or None
        """
        return self.db.get_workspace_path(user_id)
