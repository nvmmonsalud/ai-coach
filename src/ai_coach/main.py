from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from ai_coach.config.settings import settings
from ai_coach.db.session import get_db, get_session, init_db
from ai_coach.models.candidate import CandidateDocument, DocumentStatus, ParsedSection, ProfileEvent
from ai_coach.services.storage import StorageClient
from ai_coach.services.text_extractor import TextExtractor
from ai_coach.services.parser import ResumeParser
from ai_coach.services.taxonomy import TaxonomyNormalizer
from ai_coach.workers.profile_worker import ProfileProcessingWorker

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Coach Candidate Ingestion")
storage_client = StorageClient()
extractor = TextExtractor()
parser = ResumeParser()
normalizer = TaxonomyNormalizer()
worker = ProfileProcessingWorker(get_session, storage_client, extractor, parser, normalizer)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    await worker.start()


@app.post("/api/candidates/upload")
async def upload_candidate(
    background_tasks: BackgroundTasks,
    candidate_name: str | None = None,
    file: UploadFile = File(...),
    db: Annotated[Session, Depends(get_db)] = None,
) -> JSONResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    storage_path = storage_client.save_file(file.file, file.filename)
    document = CandidateDocument(
        candidate_name=candidate_name,
        filename=file.filename,
        storage_path=str(storage_path),
        status=DocumentStatus.RECEIVED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(worker.enqueue, document.id)

    return JSONResponse(
        {
            "document_id": document.id,
            "status": document.status,
            "storage_path": str(storage_path),
        },
        status_code=202,
    )


@app.get("/api/candidates/{document_id}")
async def get_candidate(document_id: int, db: Annotated[Session, Depends(get_db)] = None):
    document = db.get(CandidateDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = db.exec(select(ParsedSection).where(ParsedSection.document_id == document_id)).all()
    events = db.exec(select(ProfileEvent).where(ProfileEvent.document_id == document_id)).all()

    return {
        "document": document,
        "sections": sections,
        "events": events,
        "error_message": document.error_message,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "storage": str(Path(settings.storage_root).resolve())}
