"""Ingestion module for semantic RAG."""

from typing import Dict, Any, Optional
from loguru import logger

from zuberabot.database.postgres import get_db_manager
from zuberabot.database.vector_store import Document, DocumentChunk
from zuberabot.ai.chunking import SemanticChunker
from zuberabot.ai.embeddings import embedding_service

class IngestionService:
    """Service to process raw text, extract chunks, embed, and store into the database."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.db = get_db_manager()
        self.chunker = SemanticChunker(max_chunk_size=chunk_size, overlap=chunk_overlap)
        
    def ingest_document(self, user_id: str, content: str, filename: Optional[str] = None, metadata: dict = None) -> Document:
        """
        Process text content and save it to the vector store.
        """
        if metadata is None:
            metadata = {}
            
        with self.db.get_session() as session:
            # 1. Create the parent Document record
            doc = Document(
                user_id=user_id,
                filename=filename or "direct_input.txt",
                content=content,
                metadata_json=metadata
            )
            session.add(doc)
            session.flush() # flush to get doc.id
            
            # 2. Chunk the text semantically
            chunks = self.chunker.chunk_text(content, metadata=metadata)
            logger.info(f"Split document into {len(chunks)} semantic chunks.")
            
            # 3. Generate embeddings concurrently/batch
            texts_to_embed = [c["content"] for c in chunks]
            embeddings = embedding_service.generate_embeddings(texts_to_embed)
            
            # 4. Save the chunks to the database
            for i, chunk_data in enumerate(chunks):
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    metadata_json=chunk_data["metadata"],
                )
                
                # Always store as a plain Python list (JSON column)
                chunk_record.embedding = embeddings[i]
                    
                session.add(chunk_record)
                
            session.commit()
            logger.info(f"Successfully ingested document {doc.id} with {len(chunks)} vector chunks.")
            return doc
