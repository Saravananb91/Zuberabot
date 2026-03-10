"""Models for the Vector Database and RAG system."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from zuberabot.database.models import Base

class Document(Base):
    """Source documents for the RAG system."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False)
    filename = Column(String(255))
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    user = relationship("User")

class DocumentChunk(Base):
    """Semantic chunks of documents with vector embeddings."""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Store embeddings as JSON list of floats — no pgvector extension needed.
    embedding = Column(JSON, default=list)
        
    metadata_json = Column(JSON, default=dict)
    
    document = relationship("Document", back_populates="chunks")
