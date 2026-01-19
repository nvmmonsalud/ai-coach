from typing import Optional
from pydantic import BaseModel, Field

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="User prompt to send to the AI model")
    model: Optional[str] = Field(None, description="Model name to invoke")


class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Payload that will be sanitized for embeddings")


class FeedbackRequest(BaseModel):
    category: str = Field(..., description="parse_error | bias | hallucination | other")
    description: str
    reporter: Optional[str] = None
    trace_id: Optional[str] = None
