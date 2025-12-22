from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Column, Field, JSON, SQLModel


class DocumentStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class SectionType(str, Enum):
    ROLE = "role"
    EDUCATION = "education"
    SKILL = "skill"
    ACHIEVEMENT = "achievement"
    EXPERIENCE = "experience"


class TaxonomyType(str, Enum):
    ROLE = "role"
    SKILL = "skill"
    EDUCATION = "education"
    ACHIEVEMENT = "achievement"


class CandidateDocument(SQLModel, table=True):
    __tablename__ = "candidate_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_name: Optional[str] = Field(default=None, index=True)
    filename: str
    storage_path: str
    status: DocumentStatus = Field(default=DocumentStatus.RECEIVED)
    raw_text: Optional[str] = Field(default=None, sa_column=Column("raw_text", JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class ParsedSection(SQLModel, table=True):
    __tablename__ = "parsed_sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="candidate_documents.id")
    section_type: SectionType
    content: str
    confidence: float = Field(default=0.5)
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    redacted_content: Optional[str] = None


class NormalizedTaxonomy(SQLModel, table=True):
    __tablename__ = "normalized_taxonomy"

    id: Optional[int] = Field(default=None, primary_key=True)
    section_id: int = Field(foreign_key="parsed_sections.id")
    taxonomy_type: TaxonomyType
    raw_value: str
    canonical_value: str
    confidence: float = Field(default=0.5)


class ProfileEvent(SQLModel, table=True):
    __tablename__ = "profile_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="candidate_documents.id")
    event_type: str
    payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
