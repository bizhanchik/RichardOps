"""
NLP routes for text processing and embeddings.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from nlp_model import get_embedding

# Create APIRouter instance
router = APIRouter()


class TextRequest(BaseModel):
    """Request model for text input."""
    text: str


class EmbeddingResponse(BaseModel):
    """Response model for embedding output."""
    text: str
    embedding: List[float]


@router.post("/nlp/test", response_model=EmbeddingResponse)
async def test_nlp_embedding(request: TextRequest) -> EmbeddingResponse:
    """
    Test endpoint for generating text embeddings.
    
    Args:
        request (TextRequest): Request containing the text to process
        
    Returns:
        EmbeddingResponse: Response containing the original text and its embedding
    """
    # Get embedding for the input text
    embedding = get_embedding(request.text)
    
    # Return response with original text and embedding
    return EmbeddingResponse(
        text=request.text,
        embedding=embedding
    )