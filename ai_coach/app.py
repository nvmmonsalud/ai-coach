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

from .config import BASE_DIR
from .routers import ai, feedback, landing, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get("VERCEL"):
    DATA_DIR = Path(tempfile.gettempdir()) / "ai_coach_data"
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="AI Coach Safety and Observability")

app.include_router(ai.router)
app.include_router(feedback.router)
app.include_router(landing.router)
app.include_router(system.router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
