"""Progress tracking and dashboard utilities."""

from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List, Optional

from .models import PracticeModule, ProgressReport, ProgressSnapshot, Reminder


def progress_report(snapshots: List[ProgressSnapshot]) -> ProgressReport:
    if not snapshots:
        return ProgressReport(
            completion_rate=0.0,
            behavioral_trend=None,
            functional_trend=None,
            recent_scores={"behavioral": [], "functional": []},
        )

    sorted_snaps = sorted(snapshots, key=lambda s: s.recorded_at)
    latest = sorted_snaps[-1]
    completion_rate = (
        latest.completed_resources / latest.total_resources if latest.total_resources else 0.0
    )

    behavioral_trend = _trend([s.behavioral_scores for s in sorted_snaps])
    functional_trend = _trend([s.functional_scores for s in sorted_snaps])

    recent_scores = {
        "behavioral": latest.behavioral_scores[-5:],
        "functional": latest.functional_scores[-5:],
    }

    return ProgressReport(
        completion_rate=round(completion_rate, 2),
        behavioral_trend=behavioral_trend,
        functional_trend=functional_trend,
        recent_scores=recent_scores,
    )


def build_notifications(
    report: ProgressReport, modules: List[PracticeModule], pending_recommendations: int
) -> List[Reminder]:
    reminders: List[Reminder] = []
    now = datetime.utcnow()

    if report.completion_rate < 0.5:
        reminders.append(
            Reminder(
                message="You are under 50% of assigned resources. Schedule two quick wins this week.",
                category="progress",
                due_at=now + timedelta(days=2),
            )
        )

    if pending_recommendations:
        reminders.append(
            Reminder(
                message=f"You have {pending_recommendations} recommended items waiting.",
                category="recommendation",
                due_at=now + timedelta(days=1),
            )
        )

    if modules:
        reminders.append(
            Reminder(
                message=f"Book a {modules[0].module_type} practice: {modules[0].name}.",
                category="practice",
                due_at=now + timedelta(days=3),
            )
        )

    return reminders


def _trend(score_series: List[List[int]]) -> Optional[float]:
    flattened = [mean(scores) for scores in score_series if scores]
    if len(flattened) < 2:
        return None
    first, last = flattened[0], flattened[-1]
    if first == 0:
        return None
    return round((last - first) / first, 2)
