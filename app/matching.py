from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from .models import (
    CandidateProfile,
    JobDescription,
    MatchExplanation,
    MatchResult,
    PROTECTED_ATTRIBUTES,
)


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in text.split() if token.strip()]


def build_vector(tokens: Iterable[str]) -> Dict[str, float]:
    vector: Dict[str, float] = {}
    for token in tokens:
        vector[token] = vector.get(token, 0.0) + 1.0
    return vector


def cosine_similarity(left: Dict[str, float], right: Dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in overlap)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def sanitize_profile(profile: CandidateProfile) -> Tuple[CandidateProfile, List[str]]:
    notes: List[str] = []
    sanitized = profile.copy(deep=True)
    filtered_attributes = sanitized.attributes.copy()
    for protected in PROTECTED_ATTRIBUTES:
        if protected in filtered_attributes:
            filtered_attributes.pop(protected)
            notes.append(f"Removed protected attribute: {protected}")
    sanitized.attributes = filtered_attributes
    return sanitized, notes


def calculate_similarity(profile: CandidateProfile, job: JobDescription) -> float:
    candidate_text = " ".join(
        [
            profile.summary or "",
            " ".join(profile.skills),
            " ".join(f"{k}:{v}" for k, v in profile.sanitized_attributes().items()),
        ]
    )
    job_text = " ".join(
        [
            job.description or "",
            " ".join(job.required_skills),
            " ".join(job.preferred_skills),
        ]
    )
    candidate_vector = build_vector(tokenize(candidate_text))
    job_vector = build_vector(tokenize(job_text))
    return cosine_similarity(candidate_vector, job_vector)


def score_match(profile: CandidateProfile, job: JobDescription) -> MatchExplanation:
    sanitized_profile, fairness_notes = sanitize_profile(profile)
    similarity = calculate_similarity(sanitized_profile, job)

    matched_skills = [skill for skill in job.required_skills if skill in profile.skills]
    missing_required = [
        skill for skill in job.required_skills if skill not in profile.skills
    ]
    matched_preferred = [
        skill for skill in job.preferred_skills if skill in profile.skills
    ]
    missing_preferred = [
        skill for skill in job.preferred_skills if skill not in profile.skills
    ]

    required_weight = 0.6
    preferred_weight = 0.4
    if job.required_skills:
        required_coverage = len(matched_skills) / len(job.required_skills)
    else:
        required_coverage = 1.0
    preferred_coverage = (
        len(matched_preferred) / len(job.preferred_skills)
        if job.preferred_skills
        else 0.5
    )

    fit_score = round(
        0.5 * similarity
        + required_weight * required_coverage
        + preferred_weight * preferred_coverage,
        4,
    )
    growth_potential = round(
        min(1.0, 0.6 + 0.2 * (1 - required_coverage) + 0.2 * preferred_coverage), 4
    )

    rationale_parts = [
        f"Similarity {similarity:.2f} from embedding-style token overlap",
        f"{len(matched_skills)}/{len(job.required_skills) or 1} required skills covered",
        f"{len(matched_preferred)}/{len(job.preferred_skills) or 1} preferred skills covered",
    ]
    if missing_required:
        rationale_parts.append(
            f"Mandatory skills missing: {', '.join(missing_required)}"
        )
    explanation = MatchExplanation(
        matched_skills=matched_skills + matched_preferred,
        missing_skills=missing_required + missing_preferred,
        rationale="; ".join(rationale_parts),
        fit_score=fit_score,
        growth_potential=growth_potential,
        fairness_notes=fairness_notes,
    )
    return explanation


def build_match_result(match_id: str, profile: CandidateProfile, job: JobDescription):
    explanation = score_match(profile, job)
    return MatchResult(
        match_id=match_id,
        candidate_id=profile.candidate_id,
        job_id=job.job_id,
        created_at=datetime.utcnow(),
        fit_score=explanation.fit_score,
        growth_potential=explanation.growth_potential,
        explanation=explanation,
    )
