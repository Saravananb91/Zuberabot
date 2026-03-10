"""Fallback communication tool for handling unavailable users"""

from typing import Any
from loguru import logger
from datetime import datetime, timedelta

from zuberabot.agent.tools.base import Tool


class FallbackTool(Tool):
    """Tool for detecting user unavailability and sending fallback messages."""
    
    def __init__(self, bus):
        self.bus = bus
        self._user_timeouts = {}  # Track last message time per user
        self.timeout_threshold = 300  # 5 minutes in seconds
    
    @property
    def name(self) -> str:
        return "fallback_messenger"
    
    @property
    def description(self) -> str:
        return "Send fallback messages when user is unavailable or after timeout. Use when user hasn't responded in a while or needs important follow-up."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_timeout", "send_fallback"],
                    "description": "Check if user timed out or send fallback message"
                },
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID"
                },
                "channel": {
                    "type": "string",
                    "enum": ["whatsapp"],
                    "description": "Channel to send message on"
                },
                "message": {
                    "type": "string",
                    "description": "Fallback message to send"
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, action: str, **kwargs) -> str:
        """Execute fallback operation."""
        try:
            if action == "check_timeout":
                return await self._check_timeout(**kwargs)
            elif action == "send_fallback":
                return await self._send_fallback(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Fallback tool error: {e}")
            return f"Error: {str(e)}"
    
    async def _check_timeout(self, chat_id: str, **kwargs) -> str:
        """Check if user has timed out."""
        if chat_id not in self._user_timeouts:
            self._user_timeouts[chat_id] = datetime.now()
            return "❌ No timeout - user is active"
        
        last_seen = self._user_timeouts[chat_id]
        seconds_elapsed = (datetime.now() - last_seen).total_seconds()
        
        if seconds_elapsed > self.timeout_threshold:
            return f"✅ User timed out ({int(seconds_elapsed)}s since last message)"
        
        return f"❌ User active (last seen {int(seconds_elapsed)}s ago)"
    
    async def _send_fallback(self, chat_id: str, channel: str, message: str, **kwargs) -> str:
        """Send fallback message via specified channel."""
        from zuberabot.bus.events import OutboundMessage
        
        try:
            await self.bus.publish_outbound(OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=f"📢 [Fallback Notice]\n{message}"
            ))
            
            # Reset timeout
            self._user_timeouts[chat_id] = datetime.now()
            
            return f"✅ Fallback message sent via {channel}"
        except Exception as e:
            return f"❌ Failed to send fallback: {e}"
    
    def update_user_activity(self, chat_id: str):
        """Update user's last activity time."""
        self._user_timeouts[chat_id] = datetime.now()
