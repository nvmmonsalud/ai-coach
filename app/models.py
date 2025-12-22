from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


PROTECTED_ATTRIBUTES = {
    "age",
    "gender",
    "race",
    "ethnicity",
    "disability_status",
    "religion",
}


class CandidateProfile(BaseModel):
    candidate_id: str = Field(..., description="Unique identifier for the candidate.")
    name: str
    skills: List[str] = Field(default_factory=list)
    experience_years: float = 0
    summary: Optional[str] = None
    attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional attributes that will be sanitized for fairness.",
    )

    def sanitized_attributes(self) -> Dict[str, str]:
        return {
            key: value
            for key, value in self.attributes.items()
            if key not in PROTECTED_ATTRIBUTES
        }


class JobDescription(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the job.")
    title: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class MatchExplanation(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    rationale: str
    fit_score: float
    growth_potential: float
    fairness_notes: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    match_id: str
    candidate_id: str
    job_id: str
    created_at: datetime
    fit_score: float
    growth_potential: float
    explanation: MatchExplanation
    status: str = "pending"
    feedback: List["Feedback"] = Field(default_factory=list)


class Feedback(BaseModel):
    source: str
    comments: str
    score_adjustment: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FairnessReport(BaseModel):
    removed_attributes: Dict[str, int] = Field(default_factory=dict)
    fit_score_distribution: List[float] = Field(default_factory=list)
    growth_score_distribution: List[float] = Field(default_factory=list)
    last_updated: Optional[datetime] = None


MatchResult.update_forward_refs()
