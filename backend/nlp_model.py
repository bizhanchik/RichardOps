"""
NLP Model module for text embeddings using Sentence Transformers.
"""

import hashlib
import random
from typing import List

# Mock implementation for testing (replace with actual sentence-transformers when available)
def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for the given text using a mock implementation.
    
    Args:
        text (str): The input text to generate embedding for
        
    Returns:
        List[float]: The embedding vector as a list of floats (384 dimensions for all-MiniLM-L6-v2)
    """
    # Create a deterministic seed based on text content
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    # Generate a mock 384-dimensional embedding (same as all-MiniLM-L6-v2)
    embedding = [random.uniform(-1.0, 1.0) for _ in range(384)]
    
    return embedding