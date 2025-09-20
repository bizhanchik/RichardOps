"""
NLP Model module for text embeddings using Sentence Transformers.
"""

from sentence_transformers import SentenceTransformer
from typing import List

# Load the pretrained model at import time
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for the given text using the loaded Sentence Transformer model.
    
    Args:
        text (str): The input text to generate embedding for
        
    Returns:
        List[float]: The embedding vector as a list of floats
    """
    # Generate embedding and convert to list
    embedding = model.encode(text)
    return embedding.tolist()