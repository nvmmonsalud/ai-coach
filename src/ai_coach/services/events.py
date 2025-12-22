from __future__ import annotations

import logging
from typing import Iterable

from sqlmodel import Session

from ai_coach.models.candidate import ProfileEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self, session: Session):
        self.session = session

    def publish(self, document_id: int, event_type: str, payload: dict | None = None) -> None:
        event = ProfileEvent(document_id=document_id, event_type=event_type, payload=payload)
        self.session.add(event)
        self.session.commit()
        logger.info("Emitted event %s for document %s", event_type, document_id)

    def fetch_events(self, document_id: int) -> Iterable[ProfileEvent]:
        return self.session.query(ProfileEvent).filter(ProfileEvent.document_id == document_id).all()
