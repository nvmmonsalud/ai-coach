from fastapi import APIRouter
from ai_coach.models import PromptRequest, EmbeddingRequest
from ai_coach.dependencies import ai_client, pii_guard, apply_retention

router = APIRouter(prefix="/api", tags=["AI"])

@router.post("/ai-call")
def ai_call(request: PromptRequest) -> dict:
    apply_retention()
    return ai_client.call(prompt=request.prompt, model=request.model)


@router.post("/embed")
def embed(request: EmbeddingRequest) -> dict:
    apply_retention()
    sanitized = pii_guard.sanitize_for_embeddings(request.text)
    return {"sanitized": sanitized, "pii_detected": [match.label for match in pii_guard.detect(request.text)]}
