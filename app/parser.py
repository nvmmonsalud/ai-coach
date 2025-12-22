import re
from typing import List

from .schemas import JobRequirementIn

MANDATORY_MARKERS = ["must", "required", "responsible for", "need to"]
PREFERRED_MARKERS = ["preferred", "nice to have", "bonus", "plus"]


def _contains_keywords(text: str, keywords: List[str]) -> bool:
    lower_text = text.lower()
    return any(marker in lower_text for marker in keywords)


def _extract_years_experience(text: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years", text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_job_description(job_description: str) -> List[JobRequirementIn]:
    requirements: List[JobRequirementIn] = []
    for raw_line in job_description.splitlines():
        line = raw_line.strip("-• \t")
        if not line:
            continue

        years = _extract_years_experience(line)
        is_mandatory = True
        if _contains_keywords(line, PREFERRED_MARKERS):
            is_mandatory = False
        elif _contains_keywords(line, MANDATORY_MARKERS):
            is_mandatory = True
        requirements.append(
            JobRequirementIn(
                description=line,
                mandatory=is_mandatory,
                min_years_experience=years,
            )
        )

    return requirements
