"""Session management using PostgreSQL."""

from pathlib import Path
from typing import Any, List, Dict
from loguru import logger
from sqlalchemy.orm.attributes import flag_modified

# Import the model for type hinting
from zuberabot.database.models import ChatSession

class SessionManager:
    """
    Manages conversation sessions using PostgreSQL.
    """
    
    def __init__(self, workspace: Path, db_manager=None):
        self.workspace = workspace
        self.db = db_manager
        if not self.db:
            logger.warning("SessionManager initialized without DatabaseManager! Persistance will fail.")
    
    def get_or_create(self, key: str) -> ChatSession:
        """
        Get an existing session or create a new one from the database.
        
        Args:
            key: Session key (channel:chat_id)
            
        Returns:
            ChatSession object (SQLAlchemy model)
        """
        if not self.db:
            raise RuntimeError("DatabaseManager not configured")

        # Derive user_id from key
        # Format usually: channel:chat_id
        if ':' in key:
            channel, chat_id = key.split(':', 1)
            # For WhatsApp, chat_id is the phone number (or remoteJid)
            # We use the key itself as user_id for simplicity unless it's a group?
            # Existing logic uses channel:phone as user_id.
            
            # Simple heuristic: Use the key as user_id for now for 1:1 map
            user_id = key 
        else:
            user_id = f"cli:{key}"
            
        return self.db.get_or_create_session(session_key=key, user_id=user_id)
    
    def save(self, session: ChatSession) -> None:
        """
        Save session changes to the database.
        
        Args:
            session: The ChatSession model instance to save.
        """
        if not self.db:
            return

        try:
            with self.db.get_session() as db_session:
                # Merge the detached object back into this session
                s = db_session.merge(session)
                
                # Explicitly flag 'messages' as modified because it's a JSON column
                # and in-place list appends aren't always detected automaticallly
                flag_modified(s, "messages")
                
                # Commit is handled by the context manager
        except Exception as e:
            logger.error(f"Failed to save session {session.session_key}: {e}")

    def delete(self, key: str) -> bool:
        """Delete a session."""
        if not self.db:
            return False
        return self.db.delete_session(session_key=key)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List recent sessions."""
        if not self.db:
            return []
        return self.db.list_sessions()
