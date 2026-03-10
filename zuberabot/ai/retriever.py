"""Retrieval implementation including Hybrid Search and RRF."""

import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger

from zuberabot.database.vector_store import DocumentChunk
from zuberabot.ai.embeddings import embedding_service

class HybridRetriever:
    """Implement hybrid search combining semantic (vector) and keyword search."""
    
    def __init__(self, session: Session):
        self.session = session

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using cosine similarity computed in Python (no pgvector needed)."""
        query_embedding = embedding_service.generate_embedding(query)
        
        # Check if we have real embeddings (model loaded) or fallback zeros
        if all(v == 0.0 for v in query_embedding[:10]):
            logger.warning("Embedding model not loaded, skipping semantic search")
            return []
        
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        
        # Load all chunks and compute cosine similarity in Python
        all_chunks = self.session.query(DocumentChunk).all()
        
        import json
        scored = []
        for chunk in all_chunks:
            if not chunk.embedding:
                continue
            try:
                # Handle cases where SQL/SQLAlchemy returns it as a string
                emb_data = chunk.embedding
                if isinstance(emb_data, str):
                    emb_data = json.loads(emb_data)
                    
                c_vec = np.array(emb_data, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if c_norm == 0:
                    continue
                similarity = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                scored.append((similarity, chunk))
            except Exception as e:
                logger.error(f"Failed parsing chunk id {chunk.id} embedding: {e}")
                continue
        
        # Sort descending by similarity
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        
        logger.info(f"Semantic search found {len(top)} results for: '{query[:40]}'")
        return [{"chunk": c, "id": c.id, "content": c.content} for _, c in top]

    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using SQL ILIKE matching for exact keywords."""
        keywords = query.split()
        
        # Build an OR query for all key terms in the query
        filters = [DocumentChunk.content.ilike(f"%{word}%") for word in keywords if len(word) > 3]
        
        if not filters:
            return []
            
        results = self.session.query(DocumentChunk).filter(or_(*filters)).limit(top_k).all()
        
        return [{"chunk": c, "id": c.id, "content": c.content} for c in results]

    def rr_fusion(self, semantic_results: List[dict], keyword_results: List[dict], 
                  k: int = 60, top_k: int = 5) -> List[DocumentChunk]:
        """
        Combine semantic and keyword results using Reciprocal Rank Fusion (RRF).
        RRF Score = 1 / (k + rank)
        """
        scores = {}
        chunks_map = {}
        
        # Score Semantic Results
        for rank, item in enumerate(semantic_results):
            chunk_id = item["id"]
            chunks_map[chunk_id] = item["chunk"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank + 1))
            
        # Score Keyword Results
        for rank, item in enumerate(keyword_results):
            chunk_id = item["id"]
            chunks_map[chunk_id] = item["chunk"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank + 1))
            
        # Sort by maximum RRF score
        sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return the actual DocumentChunk objects
        return [chunks_map[chunk_id] for chunk_id, score in sorted_chunks[:top_k]]

    def retrieve(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        """Perform full hybrid retrieval for the user query."""
        semantic_res = self.semantic_search(query, top_k=top_k*2)
        keyword_res = self.keyword_search(query, top_k=top_k*2)
        
        return self.rr_fusion(semantic_res, keyword_res, top_k=top_k)
