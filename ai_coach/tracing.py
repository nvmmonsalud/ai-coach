import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class TraceRecord:
    trace_id: str
    prompt: str
    model: str
    latency_ms: float
    cost_usd: float
    prompt_tokens: int
    completion_tokens: int
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = field(default_factory=dict)


class TraceStore:
    def __init__(self) -> None:
        self.records: List[TraceRecord] = []

    def add(self, record: TraceRecord) -> TraceRecord:
        self.records.append(record)
        return record

    def list_recent(self, limit: int = 50) -> List[TraceRecord]:
        return sorted(self.records, key=lambda r: r.created_at, reverse=True)[:limit]

    def purge_older_than(self, cutoff: datetime) -> int:
        before = len(self.records)
        self.records = [r for r in self.records if r.created_at >= cutoff]
        return before - len(self.records)


@dataclass
class RetentionPolicy:
    trace_ttl_days: int = 30
    feedback_ttl_days: int = 90


class RetentionManager:
    def __init__(self, policy: RetentionPolicy):
        self.policy = policy

    def apply_traces(self, store: TraceStore) -> int:
        cutoff = datetime.utcnow() - timedelta(days=self.policy.trace_ttl_days)
        return store.purge_older_than(cutoff)


def build_trace(
    prompt: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    cost_usd: float,
    status: str,
    metadata: Optional[Dict[str, str]] = None,
) -> TraceRecord:
    return TraceRecord(
        trace_id=str(uuid.uuid4()),
        prompt=prompt,
        model=model,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        status=status,
        metadata=metadata or {},
    )
