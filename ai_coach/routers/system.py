from datetime import datetime, timedelta
from fastapi import APIRouter
from ai_coach.dependencies import apply_retention, trace_store, retention_manager, review_queue

router = APIRouter(tags=["System"])

@router.get("/health")
def healthcheck() -> dict:
    apply_retention()
    return {"status": "ok"}


@router.get("/traces")
def traces() -> dict:
    return {"traces": [trace.__dict__ for trace in trace_store.list_recent(limit=100)]}


@router.post("/retention/purge")
def purge() -> dict:
    removed_traces = retention_manager.apply_traces(trace_store)
    cutoff_feedback = datetime.utcnow() - timedelta(days=retention_manager.policy.feedback_ttl_days)
    removed_feedback = review_queue.purge_older_than(cutoff_feedback)
    return {"removed_traces": removed_traces, "removed_feedback": removed_feedback}
