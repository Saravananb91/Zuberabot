"""RAG Knowledge tool using Postgres pgvector."""

import os
from typing import Any
from zuberabot.agent.tools.base import Tool
from zuberabot.ai.retriever import HybridRetriever
from zuberabot.database.postgres import get_db_manager
from zuberabot.ai.ingestion import IngestionService

class RAGTool(Tool):
    """Manage and query a local knowledge base (RAG)."""
    
    name = "rag_knowledge"
    description = "Retrieve financial knowledge about mutual funds, insurance, or specific concepts stored in the system. Use this tool specifically when the user asks about mutual funds, insurance, financial planning, or B2C app rules."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "add"],
                "description": "Action to perform (usually 'search')."
            },
            "query": {
                "type": "string",
                "description": "Query string to search for."
            },
            "content": {
                "type": "string",
                "description": "Content to add (for action='add')"
            }
        },
        "required": ["action"]
    }
    
    def __init__(self, workspace_path: str = None):
        pass # No longer needs workspace_path for Chroma

    async def execute(self, action: str, query: str | None = None, content: str | None = None, **kwargs: Any) -> str:
        try:
            db_manager = get_db_manager()
            
            if action == "search":
                if not query:
                    return "Error: query is required for 'search' action"
                
                with db_manager.get_session() as session:
                    retriever = HybridRetriever(session)
                    # Limit to top 3 chunks for context
                    chunks = retriever.retrieve(query, top_k=3)
                    
                    if not chunks:
                        return "No relevant knowledge found in the database."
                    
                    output = ["Found relevant information:"]
                    for chunk in chunks:
                        output.append(f"- {chunk.content}")
                    
                    return "\n\n".join(output)
                    
            elif action == "add":
                if not content:
                    return "Error: content is required for 'add' action"
                    
                ingestion_service = IngestionService()
                # Simple ingestion
                doc = ingestion_service.ingest_document(
                    user_id="system:zuberabot",
                    content=content,
                    filename="agent_added",
                    metadata={"source": "agent", "category": "general"}
                )
                return f"✅ Added knowledge to database (Doc ID: {doc.id})"
                
            return f"Unknown action: {action}"
            
        except Exception as e:
            return f"RAG Error: {e}"
