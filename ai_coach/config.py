import os
import tempfile
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get("VERCEL"):
    DATA_DIR = Path(tempfile.gettempdir()) / "ai_coach_data"
else:
    DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

class AppConfig(BaseModel):
    rate_limit_calls: int = 30
    rate_limit_period: int = 60
    trace_ttl_days: int = 30
    feedback_ttl_days: int = 90

settings = AppConfig()
