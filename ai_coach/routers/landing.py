from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ai_coach.dependencies import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def landing_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("landing.html", {"request": request})
