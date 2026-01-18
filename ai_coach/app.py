import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR
from .routers import ai, feedback, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="AI Coach Safety and Observability")

app.include_router(ai.router)
app.include_router(feedback.router)
app.include_router(system.router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
