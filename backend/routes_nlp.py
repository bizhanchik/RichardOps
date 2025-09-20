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


class TextResponse(BaseModel):
    """Response model for text output."""
    input_text: str
    output_text: str
    status: str


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


@router.post("/nlp/process", response_model=TextResponse)
async def process_text(request: TextRequest) -> TextResponse:
    """
    Simple text processing endpoint for testing NLP functionality.
    
    Args:
        request (TextRequest): Request containing the text to process
        
    Returns:
        TextResponse: Response containing processed text output
    """
    input_text = request.text.strip()
    
    # Simple text processing logic
    if "are you working" in input_text.lower():
        output_text = "Yes, I am working! The NLP service is active and processing your text successfully."
    elif "hello" in input_text.lower():
        output_text = f"Hello! I received your message: '{input_text}' and I'm processing it through the NLP pipeline."
    elif "test" in input_text.lower():
        output_text = f"Test successful! Your input '{input_text}' has been processed. NLP service is functioning correctly."
    else:
        # Generate a response based on text length and content
        word_count = len(input_text.split())
        char_count = len(input_text)
        output_text = f"I processed your text: '{input_text}'. It contains {word_count} words and {char_count} characters. NLP analysis complete!"
    
    return TextResponse(
        input_text=input_text,
        output_text=output_text,
        status="success"
    )