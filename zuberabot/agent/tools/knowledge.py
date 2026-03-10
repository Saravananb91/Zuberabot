"""Tool for the agent to memorize long-term knowledge in the RAG system."""

from typing import Any
from loguru import logger

from zuberabot.agent.tools.base import Tool
from zuberabot.ai.ingestion import IngestionService

class StoreKnowledgeTool(Tool):
    """Tool that allows the agent to self-record important information into long-term vector memory."""
    
    name = "store_knowledge"
    description = (
        "Store important financial data, documents, or context into long-term vector memory. "
        "Use this when a user gives you detailed text, references, or preferences that you "
        "will need to remember across different sessions or far into the future."
    )
    
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The exact text or data to store in memory."
            },
            "source_type": {
                "type": "string",
                "description": "Where the data came from (e.g., 'user_chat', 'document_upload', 'financial_report')."
            }
        },
        "required": ["content", "source_type"]
    }
    
    def __init__(self):
        super().__init__()
        self.ingestion = IngestionService()
        self.user_id = "default_user" # Handled contextually if needed

    def set_context(self, user_id: str):
        """Set the user ID to associate the knowledge properly."""
        self.user_id = user_id

    async def execute(self, **kwargs: Any) -> Any:
        content = kwargs.get("content")
        source_type = kwargs.get("source_type")
        
        if not content:
            return "Error: content is required to store knowledge."
            
        try:
            doc = self.ingestion.ingest_document(
                user_id=self.user_id,
                content=content,
                filename=source_type,
                metadata={"source": source_type, "agent_stored": True}
            )
            return f"Success. Knowledge stored permanently with Document ID: {doc.id}"
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            return f"Error storing knowledge: {str(e)}"
