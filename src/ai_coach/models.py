"""Domain models for AI Coach."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ActionItem:
    """An actionable recommendation tied to a skill gap."""

    title: str
    description: str
    category: str  # quick_win, medium_term, interview_prep
    skill: str
    resource_type: str  # course, project, reading, exercise
    estimated_minutes: int


@dataclass
class SkillGap:
    """Represents a gap detected from a match explanation."""

    skill: str
    severity: str  # low, medium, high
    evidence: str


@dataclass
class Plan:
    """Aggregates actionable steps for a candidate."""

    quick_wins: List[ActionItem] = field(default_factory=list)
    medium_term: List[ActionItem] = field(default_factory=list)
    interview_prep: List[ActionItem] = field(default_factory=list)


@dataclass
class Recommendation:
    """Learning resources tied to a skill taxonomy."""

    skill: str
    title: str
    resource_type: str  # course, project, reading
    url: Optional[str]
    estimated_minutes: int
    completed: bool = False


@dataclass
class PracticeModule:
    """Practice prompt with rubric-based evaluation dimensions."""

    name: str
    module_type: str  # behavioral or functional
    prompt: str
    rubric: Dict[str, str]


@dataclass
class EvaluationDimension:
    """A scored rubric dimension."""

    name: str
    score: int
    max_score: int
    feedback: str


@dataclass
class EvaluationResult:
    """LLM-style structured feedback for practice modules."""

    module: str
    overall_score: int
    max_score: int
    summary: str
    dimensions: List[EvaluationDimension]
    recommendations: List[str]


@dataclass
class Reminder:
    """A lightweight nudge for the candidate dashboard."""

    message: str
    category: str  # progress, practice, recommendation
    due_at: datetime


@dataclass
class GapAnalysis:
    """Gap analysis derived from match explanations."""

    gaps: List[SkillGap]
    plan: Plan
    recommendations: List[Recommendation]


@dataclass
class ProgressSnapshot:
    """Time-series entry for candidate improvement."""

    recorded_at: datetime
    completed_resources: int
    total_resources: int
    behavioral_scores: List[int] = field(default_factory=list)
    functional_scores: List[int] = field(default_factory=list)


@dataclass
class ProgressReport:
    """Computed progress view for the dashboard."""

    completion_rate: float
    behavioral_trend: Optional[float]
    functional_trend: Optional[float]
    recent_scores: Dict[str, List[int]]
