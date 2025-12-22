from __future__ import annotations

from dataclasses import dataclass

from ai_coach.models.candidate import SectionType, TaxonomyType


@dataclass
class NormalizedTerm:
    taxonomy_type: TaxonomyType
    raw_value: str
    canonical_value: str
    confidence: float


class TaxonomyNormalizer:
    ROLE_ALIASES = {
        "software engineer": "Software Engineer",
        "developer": "Software Engineer",
        "data analyst": "Data Analyst",
    }
    SKILL_ALIASES = {
        "py": "Python",
        "python": "Python",
        "js": "JavaScript",
    }
    EDUCATION_ALIASES = {
        "bachelor": "Bachelor's Degree",
        "master": "Master's Degree",
        "phd": "PhD",
    }

    def normalize(self, section_type: SectionType, value: str, confidence: float) -> NormalizedTerm | None:
        if section_type == SectionType.ROLE:
            canonical = self._normalize_value(value, self.ROLE_ALIASES)
            return NormalizedTerm(TaxonomyType.ROLE, value, canonical, confidence)
        if section_type == SectionType.SKILL:
            canonical = self._normalize_value(value, self.SKILL_ALIASES)
            return NormalizedTerm(TaxonomyType.SKILL, value, canonical, confidence)
        if section_type == SectionType.EDUCATION:
            canonical = self._normalize_value(value, self.EDUCATION_ALIASES)
            return NormalizedTerm(TaxonomyType.EDUCATION, value, canonical, confidence)
        if section_type == SectionType.ACHIEVEMENT:
            return NormalizedTerm(TaxonomyType.ACHIEVEMENT, value, value.strip().capitalize(), confidence)
        return None

    @staticmethod
    def _normalize_value(value: str, aliases: dict[str, str]) -> str:
        lowered = value.lower()
        for hint, canonical in aliases.items():
            if hint in lowered:
                return canonical
        return value.strip().title()
