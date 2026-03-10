"""User-isolated context builder for multi-user support."""

from pathlib import Path
from typing import Any

from loguru import logger

from zuberabot.agent.user_memory import UserMemoryStore
from zuberabot.agent.skills import SkillsLoader


class UserContextBuilder:
    """
    Build context for the agent with user isolation.
    
    This version creates user-specific contexts with isolated memory and skills.
    """
    
    def __init__(self, workspace: Path, memory_store: UserMemoryStore = None):
        """
        Initialize context builder.
        
        Args:
            workspace: User-specific workspace path
            memory_store: User-specific memory store (optional)
        """
        self.workspace = workspace
        self.memory = memory_store
        self.skills = SkillsLoader(workspace)
    
    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        media: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Build the message list for the LLM.
        
        Args:
            history: Previous conversation messages
            current_message: Current user message
            media: Optional media URLs/paths
            
        Returns:
            Full message list with system prompt, history, and current message
        """
        messages = []
        
        # System message with context
        system_content = self._build_system_prompt()
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        messages.extend(history)
        
        # Add current message
        if media:
            # Multi-modal message (image + text)
            content_parts = [{"type": "text", "text": current_message}]
            for media_url in media:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": media_url}
                })
            messages.append({"role": "user", "content": content_parts})
        else:
            # Text-only message
            messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with memory and skills context.
        
        Returns:
            System prompt string
        """
        parts = [
            "You are Zubera Bot, a helpful AI assistant.",
            "You have access to tools that you can use to help the user.",
            "Use the tools when necessary to accomplish tasks.",
        ]
        
        # Add memory context if available
        if self.memory:
            memory_context = self.memory.get_memory_context()
            if memory_context:
                parts.append(f"\n## Your Memory\n{memory_context}")
        
        # Add skills context if available
        skills_context = self.skills.get_context()
        if skills_context:
            parts.append(f"\n## Available Skills\n{skills_context}")
        
        return "\n\n".join(parts)
    
    def add_assistant_message(
        self,
        messages: list[dict[str, Any]],
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """
        Add assistant message with optional tool calls.
        
        Args:
            messages: Current message list
            content: Assistant response content
            tool_calls: Tool calls made by assistant
            
        Returns:
            Updated message list
        """
        msg = {"role": "assistant"}
        
        if content:
            msg["content"] = content
        
        if tool_calls:
            msg["tool_calls"] = tool_calls
        
        messages.append(msg)
        return messages
    
    def add_tool_result(
        self,
        messages: list[dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        result: str
    ) -> list[dict[str, Any]]:
        """
        Add tool execution result.
        
        Args:
            messages: Current message list
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result
            
        Returns:
            Updated message list
        """
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result
        })
        return messages
