import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class FeedbackItem:
    feedback_id: str
    category: str
    description: str
    source_trace_id: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "open"
    reporter: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


import threading
from pathlib import Path

from .persistence import JsonStore


class ReviewQueue:
    def __init__(self, storage_path: Path) -> None:
        self.store = JsonStore(storage_path, FeedbackItem)
        self.lock = threading.Lock()

    def submit(
        self,
        category: str,
        description: str,
        reporter: Optional[str] = None,
        source_trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> FeedbackItem:
        item = FeedbackItem(
            feedback_id=str(uuid.uuid4()),
            category=category,
            description=description,
            reporter=reporter,
            source_trace_id=source_trace_id,
            metadata=metadata or {},
        )
        with self.lock:
            self.store.add(item)
        return item

    def list_items(self, status: Optional[str] = None) -> List[FeedbackItem]:
        with self.lock:
            results = self.store.get_all()
        if status:
            results = [item for item in results if item.status == status]
        return sorted(results, key=lambda i: i.created_at, reverse=True)

    def update_status(self, feedback_id: str, status: str) -> Optional[FeedbackItem]:
        with self.lock:
            items = self.store.get_all()
            updated_item = None
            for item in items:
                if item.feedback_id == feedback_id:
                    item.status = status
                    updated_item = item
                    break
            if updated_item:
                self.store.replace_all(items)
            return updated_item

    def purge_older_than(self, cutoff: datetime) -> int:
        with self.lock:
            items = self.store.get_all()
            before = len(items)
            surviving = [item for item in items if item.created_at >= cutoff]
            self.store.replace_all(surviving)
            return before - len(surviving)
