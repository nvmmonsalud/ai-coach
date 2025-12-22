from __future__ import annotations

import logging
import re
from typing import Iterable

from pydantic import BaseModel

from ai_coach.models.candidate import SectionType

logger = logging.getLogger(__name__)


class ParsedSegment(BaseModel):
    section_type: SectionType
    content: str
    confidence: float = 0.6
    metadata: dict | None = None


class ParserResult(BaseModel):
    segments: list[ParsedSegment]
    errors: list[str] = []


class ResumeParser:
    """LLM-assisted parser stub.

    In a production system this would call an LLM with a controlled schema prompt.
    Here we rely on lightweight heuristics while keeping the contract identical.
    """

    SKILL_HINTS = {"python", "javascript", "sql", "aws", "docker", "kubernetes"}
    ROLE_HINTS = {"engineer", "developer", "manager", "analyst", "consultant"}
    EDUCATION_HINTS = {"bachelor", "master", "phd", "university", "college"}

    def parse(self, text: str) -> ParserResult:
        segments: list[ParsedSegment] = []
        errors: list[str] = []

        try:
            segments.extend(self._extract_roles(text))
            segments.extend(self._extract_skills(text))
            segments.extend(self._extract_education(text))
            segments.extend(self._extract_achievements(text))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to parse resume text")
            errors.append(str(exc))

        return ParserResult(segments=segments, errors=errors)

    def _extract_roles(self, text: str) -> Iterable[ParsedSegment]:
        for line in text.splitlines():
            if any(hint in line.lower() for hint in self.ROLE_HINTS):
                yield ParsedSegment(section_type=SectionType.ROLE, content=line.strip(), confidence=0.75)

    def _extract_skills(self, text: str) -> Iterable[ParsedSegment]:
        skills_found = {hint for hint in self.SKILL_HINTS if hint in text.lower()}
        for skill in skills_found:
            yield ParsedSegment(section_type=SectionType.SKILL, content=skill, confidence=0.7)

    def _extract_education(self, text: str) -> Iterable[ParsedSegment]:
        for line in text.splitlines():
            if any(hint in line.lower() for hint in self.EDUCATION_HINTS):
                yield ParsedSegment(section_type=SectionType.EDUCATION, content=line.strip(), confidence=0.65)

    def _extract_achievements(self, text: str) -> Iterable[ParsedSegment]:
        bullet_lines = [line for line in text.splitlines() if line.strip().startswith("-")]
        for bullet in bullet_lines:
            yield ParsedSegment(
                section_type=SectionType.ACHIEVEMENT,
                content=bullet.strip("- "),
                confidence=0.55,
                metadata={"bullet": True},
            )

    @staticmethod
    def redact_pii(text: str) -> str:
        redacted = re.sub(r"[\w.-]+@[\w.-]+", "[redacted email]", text)
        redacted = re.sub(r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b", "[redacted id]", redacted)
        redacted = re.sub(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d{3}[\s-]?){2}\d{4}\b", "[redacted phone]", redacted)
        return redacted
