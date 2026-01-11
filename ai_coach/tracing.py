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


import threading
from pathlib import Path
from .persistence import JsonStore


class TraceStore:
    def __init__(self, storage_path: Path) -> None:
        self.store = JsonStore(storage_path, TraceRecord)
        self.lock = threading.Lock()

    def add(self, record: TraceRecord) -> TraceRecord:
        with self.lock:
            self.store.add(record)
        return record

    def list_recent(self, limit: int = 50) -> List[TraceRecord]:
        with self.lock:
            records = self.store.get_all()
        return sorted(records, key=lambda r: r.created_at, reverse=True)[:limit]

    def purge_older_than(self, cutoff: datetime) -> int:
        with self.lock:
            records = self.store.get_all()
            before = len(records)
            surviving = [r for r in records if r.created_at >= cutoff]
            self.store.replace_all(surviving)
            return before - len(surviving)


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
