from datetime import datetime, timedelta
import logging
from fastapi.templating import Jinja2Templates
from .config import DATA_DIR, BASE_DIR, settings
from .pii import PIIGuard
from .tracing import TraceStore, RetentionManager, RetentionPolicy
from .review_queue import ReviewQueue
from .rate_limit import RateLimiter, RateLimiterConfig
from .ai_client import AIClient

logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Services
pii_guard = PIIGuard()
trace_store = TraceStore(storage_path=DATA_DIR / "traces.json")
review_queue = ReviewQueue(storage_path=DATA_DIR / "feedback.json")
retention_manager = RetentionManager(RetentionPolicy(
    trace_ttl_days=settings.trace_ttl_days,
    feedback_ttl_days=settings.feedback_ttl_days
))
rate_limiter = RateLimiter(RateLimiterConfig(
    max_calls=settings.rate_limit_calls,
    period_seconds=settings.rate_limit_period
))
ai_client = AIClient(tracer=trace_store, pii_guard=pii_guard, rate_limiter=rate_limiter)

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
