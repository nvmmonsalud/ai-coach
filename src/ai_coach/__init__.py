"""AI Coach package for candidate skill development and interview preparation."""

from .models import (
    ActionItem,
    GapAnalysis,
    Plan,
    PracticeModule,
    Recommendation,
    Reminder,
    SkillGap,
)
from .gap_analysis import generate_gap_analysis
from .recommendations import generate_recommendations
from .practice import evaluate_behavioral_response, evaluate_functional_response, practice_catalog
from .dashboard import build_notifications, progress_report

__all__ = [
    "ActionItem",
    "GapAnalysis",
    "Plan",
    "PracticeModule",
    "Recommendation",
    "Reminder",
    "SkillGap",
    "generate_gap_analysis",
    "generate_recommendations",
    "evaluate_behavioral_response",
    "evaluate_functional_response",
    "practice_catalog",
    "build_notifications",
    "progress_report",
]
