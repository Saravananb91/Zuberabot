"""User-isolated memory system for multi-user support."""

from pathlib import Path
from datetime import datetime, timedelta

from zuberabot.utils.helpers import ensure_dir, today_date
from zuberabot.database.postgres import DatabaseManager
from loguru import logger


class UserMemoryStore:
    """
    User-isolated memory system.
    
    Each user has their own workspace with separate memory files.
    Supports daily notes (memory/YYYY-MM-DD.md) and long-term memory (MEMORY.md).
    """
    
    def __init__(self, user_id: str, db_manager: DatabaseManager, base_workspace: Path = None):
        """
        Initialize user memory store.
        
        Args:
            user_id: User identifier
            db_manager: Database manager for workspace lookup
            base_workspace: Base workspace directory (optional)
        """
        self.user_id = user_id
        self.db = db_manager
        
        # Get or create user-specific workspace
        workspace_path = db_manager.get_workspace_path(user_id)
        if not workspace_path:
            workspace = db_manager.get_or_create_workspace(user_id)
            workspace_path = workspace.workspace_path
        
        self.workspace = Path(workspace_path)
        self.memory_dir = ensure_dir(self.workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        
        logger.debug(f"User memory store initialized for {user_id} at {self.workspace}")
    
    def get_today_file(self) -> Path:
        """Get path to today's memory file."""
        return self.memory_dir / f"{today_date()}.md"
    
    def read_today(self) -> str:
        """Read today's memory notes."""
        today_file = self.get_today_file()
        if today_file.exists():
            return today_file.read_text(encoding="utf-8")
        return ""
    
    def append_today(self, content: str) -> None:
        """Append content to today's memory notes."""
        today_file = self.get_today_file()
        
        if today_file.exists():
            existing = today_file.read_text(encoding="utf-8")
            content = existing + "\n" + content
        else:
            # Add header for new day
            header = f"# {today_date()}\n\n"
            content = header + content
        
        today_file.write_text(content, encoding="utf-8")
    
    def read_long_term(self) -> str:
        """Read long-term memory (MEMORY.md)."""
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""
    
    def write_long_term(self, content: str) -> None:
        """Write to long-term memory (MEMORY.md)."""
        self.memory_file.write_text(content, encoding="utf-8")
    
    def get_recent_memories(self, days: int = 7) -> str:
        """
        Get memories from the last N days.
        
        Args:
            days: Number of days to look back.
        
        Returns:
            Combined memory content.
        """
        memories = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            file_path = self.memory_dir / f"{date_str}.md"
            
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                memories.append(content)
        
        return "\n\n---\n\n".join(memories)
    
    def list_memory_files(self) -> list[Path]:
        """List all memory files sorted by date (newest first)."""
        if not self.memory_dir.exists():
            return []
        
        files = list(self.memory_dir.glob("????-??-??.md"))
        return sorted(files, reverse=True)
    
    def get_memory_context(self) -> str:
        """
        Get memory context for the agent.
        
        Returns:
            Formatted memory context including long-term and recent memories.
        """
        parts = []
        
        # Long-term memory
        long_term = self.read_long_term()
        if long_term:
            parts.append("## Long-term Memory\n" + long_term)
        
        # Today's notes
        today = self.read_today()
        if today:
            parts.append("## Today's Notes\n" + today)
        
        return "\n\n".join(parts) if parts else ""


class MemoryStoreFactory:
    """Factory for creating user-specific memory stores."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize memory store factory.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._cache: dict[str, UserMemoryStore] = {}
    
    def get_memory_store(self, user_id: str) -> UserMemoryStore:
        """
        Get or create memory store for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserMemoryStore instance
        """
        if user_id not in self._cache:
            self._cache[user_id] = UserMemoryStore(user_id, self.db)
        return self._cache[user_id]
    
    def clear_cache(self):
        """Clear cached memory stores."""
        self._cache.clear()
