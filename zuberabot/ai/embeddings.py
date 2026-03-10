"""Embedding generation for semantic search."""

from typing import List
from loguru import logger

class EmbeddingService:
    """Service to generate vector embeddings for text chunks."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        
    def _get_model(self):
        """Lazy load the embedding model to avoid startup delay."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.error("sentence-transformers not installed. Fallback to dummy embeddings.")
                return None
        return self._model
        
    def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding vector for a piece of text."""
        model = self._get_model()
        if not model:
            # Return dummy 384-dimensional vector if model failed
            return [0.0] * 384
            
        # generate embedding and convert to list of floats
        embedding = model.encode(text)
        return embedding.tolist()
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch."""
        model = self._get_model()
        if not model:
            return [[0.0] * 384 for _ in texts]
            
        embeddings = model.encode(texts)
        return embeddings.tolist()

# Global instance for app-wide use
embedding_service = EmbeddingService()
