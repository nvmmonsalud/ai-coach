from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from ai_coach.models import FeedbackRequest
from ai_coach.dependencies import review_queue, pii_guard, templates

router = APIRouter(tags=["Feedback"])

@router.post("/api/feedback")
def feedback(request: FeedbackRequest) -> dict:
    item = review_queue.submit(
        category=request.category,
        description=pii_guard.redact(request.description),
        reporter=request.reporter,
        source_trace_id=request.trace_id,
        metadata={"source": "api"},
    )
    return {"feedback_id": item.feedback_id, "status": item.status}


@router.get("/feedback", response_class=HTMLResponse)
async def feedback_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("feedback.html", {"request": request})


@router.post("/feedback", response_class=HTMLResponse)
async def feedback_submit(
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


@router.get("/review-queue", response_class=HTMLResponse)
async def review_queue_view(request: Request) -> HTMLResponse:
    items = review_queue.list_items()
    return templates.TemplateResponse("review_queue.html", {"request": request, "items": items})


@router.post("/review-queue/{feedback_id}/close")
def close_feedback(feedback_id: str) -> dict:
    item = review_queue.update_status(feedback_id, status="closed")
    if not item:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"feedback_id": item.feedback_id, "status": item.status}
