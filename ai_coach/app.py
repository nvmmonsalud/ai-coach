import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .ai_client import AIClient
from .pii import PIIGuard
from .rate_limit import RateLimiter, RateLimiterConfig
from .review_queue import ReviewQueue
from .tracing import RetentionManager, RetentionPolicy, TraceStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get("VERCEL"):
    DATA_DIR = Path(tempfile.gettempdir()) / "ai_coach_data"
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="AI Coach Safety and Observability")

pii_guard = PIIGuard()
trace_store = TraceStore(storage_path=DATA_DIR / "traces.json")
review_queue = ReviewQueue(storage_path=DATA_DIR / "feedback.json")
retention_manager = RetentionManager(RetentionPolicy(trace_ttl_days=30, feedback_ttl_days=90))
rate_limiter = RateLimiter(RateLimiterConfig(max_calls=30, period_seconds=60))
ai_client = AIClient(tracer=trace_store, pii_guard=pii_guard, rate_limiter=rate_limiter)


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


def apply_retention() -> None:
    removed_traces = retention_manager.apply_traces(trace_store)
    cutoff_feedback = datetime.utcnow() - timedelta(days=retention_manager.policy.feedback_ttl_days)
    removed_feedback = review_queue.purge_older_than(cutoff_feedback)
    if removed_traces or removed_feedback:
        logger.info(
            "Retention purged traces=%s feedback=%s (cutoff=%s)",
            removed_traces,
            removed_feedback,
            cutoff_feedback.date(),
        )


@app.get("/health")
def healthcheck() -> dict:
    apply_retention()
    return {"status": "ok"}


@app.post("/api/ai-call")
def ai_call(request: PromptRequest) -> dict:
    apply_retention()
    return ai_client.call(prompt=request.prompt, model=request.model)


@app.post("/api/embed")
def embed(request: EmbeddingRequest) -> dict:
    apply_retention()
    sanitized = pii_guard.sanitize_for_embeddings(request.text)
    return {"sanitized": sanitized, "pii_detected": [match.label for match in pii_guard.detect(request.text)]}


@app.post("/api/feedback")
def feedback(request: FeedbackRequest) -> dict:
    item = review_queue.submit(
        category=request.category,
        description=pii_guard.redact(request.description),
        reporter=request.reporter,
        source_trace_id=request.trace_id,
        metadata={"source": "api"},
    )
    return {"feedback_id": item.feedback_id, "status": item.status}


@app.get("/traces")
def traces() -> dict:
    return {"traces": [trace.__dict__ for trace in trace_store.list_recent(limit=100)]}


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_form(request: Request) -> HTMLResponse:  # type: ignore[override]
    return templates.TemplateResponse("feedback.html", {"request": request})


@app.post("/feedback", response_class=HTMLResponse)
async def feedback_submit(  # type: ignore[override]
    request: Request,
    category: str = Form(...),
    description: str = Form(...),
    reporter: Optional[str] = Form(None),
    trace_id: Optional[str] = Form(None),
) -> HTMLResponse:
    redacted_description = pii_guard.redact(description)
    item = review_queue.submit(
        category=category,
        description=redacted_description,
        reporter=reporter,
        source_trace_id=trace_id,
        metadata={"source": "ui"},
    )
    return templates.TemplateResponse(
        "feedback.html",
        {
            "request": request,
            "submitted": True,
            "feedback_id": item.feedback_id,
        },
    )


@app.get("/review-queue", response_class=HTMLResponse)
async def review_queue_view(request: Request) -> HTMLResponse:  # type: ignore[override]
    items = review_queue.list_items()
    return templates.TemplateResponse("review_queue.html", {"request": request, "items": items})


@app.post("/review-queue/{feedback_id}/close")
def close_feedback(feedback_id: str) -> dict:
    item = review_queue.update_status(feedback_id, status="closed")
    if not item:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"feedback_id": item.feedback_id, "status": item.status}


@app.post("/retention/purge")
def purge() -> dict:
    removed_traces = retention_manager.apply_traces(trace_store)
    cutoff_feedback = datetime.utcnow() - timedelta(days=retention_manager.policy.feedback_ttl_days)
    removed_feedback = review_queue.purge_older_than(cutoff_feedback)
    return {"removed_traces": removed_traces, "removed_feedback": removed_feedback}


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
