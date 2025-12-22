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


class ReviewQueue:
    def __init__(self) -> None:
        self.items: List[FeedbackItem] = []

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
        self.items.append(item)
        return item

    def list_items(self, status: Optional[str] = None) -> List[FeedbackItem]:
        results = self.items
        if status:
            results = [item for item in results if item.status == status]
        return sorted(results, key=lambda i: i.created_at, reverse=True)

    def update_status(self, feedback_id: str, status: str) -> Optional[FeedbackItem]:
        for item in self.items:
            if item.feedback_id == feedback_id:
                item.status = status
                return item
        return None

    def purge_older_than(self, cutoff: datetime) -> int:
        before = len(self.items)
        self.items = [item for item in self.items if item.created_at >= cutoff]
        return before - len(self.items)
