from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from sqlmodel import Session

from ai_coach.models.candidate import CandidateDocument, DocumentStatus, NormalizedTaxonomy, ParsedSection
from ai_coach.services.events import EventPublisher
from ai_coach.services.parser import ResumeParser
from ai_coach.services.storage import StorageClient
from ai_coach.services.taxonomy import TaxonomyNormalizer
from ai_coach.services.text_extractor import TextExtractor

logger = logging.getLogger(__name__)


class ProfileProcessingWorker:
    def __init__(
        self,
        session_factory,
        storage_client: StorageClient,
        extractor: TextExtractor,
        parser: ResumeParser,
        normalizer: TaxonomyNormalizer,
    ) -> None:
        self.session_factory = session_factory
        self.storage_client = storage_client
        self.extractor = extractor
        self.parser = parser
        self.normalizer = normalizer
        self.queue: asyncio.Queue[int] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def enqueue(self, document_id: int) -> None:
        logger.info("Enqueued document %s", document_id)
        self.queue.put_nowait(document_id)

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())
            logger.info("Profile processing worker started")

    async def _run(self) -> None:
        while True:
            document_id = await self.queue.get()
            try:
                await self._process(document_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to process document %s", document_id)
            finally:
                self.queue.task_done()

    async def _process(self, document_id: int) -> None:
        with self.session_factory() as session:
            document = session.get(CandidateDocument, document_id)
            if not document:
                logger.warning("Document %s not found", document_id)
                return

            event_publisher = EventPublisher(session)
            document.status = DocumentStatus.PROCESSING
            session.add(document)
            session.commit()

            try:
                path = Path(document.storage_path)
                text = self.extractor.extract(path)
                document.raw_text = text
                parsed = self.parser.parse(text)

                if parsed.errors:
                    document.error_message = " | ".join(parsed.errors)

                sections = []
                for segment in parsed.segments:
                    redacted = self.parser.redact_pii(segment.content)
                    section = ParsedSection(
                        document_id=document.id,
                        section_type=segment.section_type,
                        content=segment.content,
                        redacted_content=redacted,
                        confidence=segment.confidence,
                        metadata=segment.metadata,
                    )
                    sections.append(section)
                    session.add(section)
                    session.flush()

                    normalized = self.normalizer.normalize(
                        segment.section_type, segment.content, segment.confidence
                    )
                    if normalized:
                        session.add(
                            NormalizedTaxonomy(
                                section_id=section.id,
                                taxonomy_type=normalized.taxonomy_type,
                                raw_value=normalized.raw_value,
                                canonical_value=normalized.canonical_value,
                                confidence=normalized.confidence,
                            )
                        )

                session.commit()

                document.status = DocumentStatus.READY
                document.updated_at = datetime.utcnow()
                session.add(document)
                session.commit()

                event_publisher.publish(
                    document_id=document.id,
                    event_type="profile_ready",
                    payload={"sections": len(sections), "errors": parsed.errors},
                )
            except Exception as exc:  # noqa: BLE001
                document.status = DocumentStatus.FAILED
                document.error_message = str(exc)
                session.add(document)
                session.commit()
                event_publisher.publish(
                    document_id=document.id,
                    event_type="profile_failed",
                    payload={"error": str(exc)},
                )
                raise
