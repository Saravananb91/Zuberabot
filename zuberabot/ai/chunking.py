"""Semantic text chunking for RAG processing."""

import re
from typing import List, Dict, Any

class SemanticChunker:
    """Implement semantic chunking that respects document structure and sentence boundaries."""
    
    def __init__(self, max_chunk_size: int = 500, overlap: int = 50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
    def chunk_text(self, text: str, metadata: dict = None) -> List[Dict[str, Any]]:
        """Split text into chunks based on paragraphs and sentences while maintaining meaning."""
        if metadata is None:
            metadata = {}
            
        # Split by double newlines to isolate separate paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for p in paragraphs:
            # If a single paragraph combined with the current chunk is too long
            if len(current_chunk) + len(p) > self.max_chunk_size and current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": current_chunk.strip(), 
                    "metadata": metadata.copy()
                })
                chunk_index += 1
                
                # Start new chunk with trailing overlap from the previous chunk
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + p + "\n\n"
            else:
                current_chunk += p + "\n\n"
                
        if current_chunk.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "content": current_chunk.strip(), 
                "metadata": metadata.copy()
            })
            
        return chunks
        
    def _get_overlap_text(self, text: str) -> str:
        """Get the last few sentences for overlap context to prevent hard breaks."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        overlap_chars = 0
        overlap_sentences = []
        
        for s in reversed(sentences):
            if overlap_chars + len(s) <= self.overlap:
                overlap_sentences.insert(0, s)
                overlap_chars += len(s)
            else:
                break
                
        return " ".join(overlap_sentences) + " " if overlap_sentences else ""
