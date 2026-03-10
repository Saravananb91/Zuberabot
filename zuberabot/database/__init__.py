"""Database package for user management and storage."""

from zuberabot.database.models import (
    Base,
    User,
    Verification,
    UserPreferences,
    Conversation,
    Recommendation,
    ChatSession,
    UserWorkspace,
)
from zuberabot.database.postgres import (
    DatabaseManager,
    get_db_manager,
    init_database,
)

__all__ = [
    "Base",
    "User",
    "Verification",
    "UserPreferences",
    "Conversation",
    "Recommendation",
    "ChatSession",
    "UserWorkspace",
    "DatabaseManager",
    "get_db_manager",
    "init_database",
]
