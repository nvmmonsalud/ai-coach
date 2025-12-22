"""CLI demo for AI Coach capabilities."""

from datetime import datetime, timedelta
from pathlib import Path

from .dashboard import build_notifications, progress_report
from .gap_analysis import generate_gap_analysis
from .practice import evaluate_behavioral_response, evaluate_functional_response, practice_catalog
from .taxonomy import SkillTaxonomy
from .models import ProgressSnapshot


def _sample_explanations() -> list[str]:
    return [
        "Candidate needs stronger system design fundamentals and API design rigor.",
        "Communication was good but they struggled with caching strategies.",
        "Would like to see better behavioral stories and STAR framing.",
    ]


def _sample_responses():
    behavioral_response = (
        "In my last role, the situation involved a delayed launch. My task was to align the "
        "team. I set up a plan (action) and communicated dependencies; as a result, we shipped "
        "on time and improved customer satisfaction by 10%."
    )
    functional_response = (
        "I would decompose the platform into services: candidate profile, coaching engine, "
        "content catalog, and notifications. APIs expose progress and recommendations. I'd "
        "scale with caching and async jobs."
    )
    return behavioral_response, functional_response


def run_demo() -> None:
    taxonomy_path = Path(__file__).resolve().parent / "data" / "skill_taxonomy.json"
    taxonomy = SkillTaxonomy.from_json(taxonomy_path)

    analysis = generate_gap_analysis(
        explanations=_sample_explanations(),
        taxonomy=taxonomy,
        completed_resources={"System Design": ["Designing Data-Intensive Applications"]},
    )

    behavioral_response, functional_response = _sample_responses()
    behavioral_eval = evaluate_behavioral_response(practice_catalog[0].name, behavioral_response)
    functional_eval = evaluate_functional_response(practice_catalog[1].name, functional_response)

    snapshots = [
        ProgressSnapshot(
            recorded_at=datetime.utcnow() - timedelta(days=7),
            completed_resources=3,
            total_resources=8,
            behavioral_scores=[5, 6],
            functional_scores=[4, 5],
        ),
        ProgressSnapshot(
            recorded_at=datetime.utcnow(),
            completed_resources=5,
            total_resources=8,
            behavioral_scores=behavioral_eval.overall_score and [behavioral_eval.overall_score],
            functional_scores=functional_eval.overall_score and [functional_eval.overall_score],
        ),
    ]

    report = progress_report(snapshots)
    reminders = build_notifications(report, practice_catalog, pending_recommendations=len(analysis.recommendations))

    print("=== Gap Analysis ===")
    for gap in analysis.gaps:
        print(f"- {gap.skill} ({gap.severity}): {gap.evidence}")

    print("\n=== Action Plan ===")
    for item in analysis.plan.quick_wins:
        print(f"[Quick Win] {item.skill}: {item.title} - {item.description}")
    for item in analysis.plan.medium_term:
        print(f"[Medium Term] {item.skill}: {item.title} - {item.description}")
    for item in analysis.plan.interview_prep:
        print(f"[Interview Prep] {item.skill}: {item.title} - {item.description}")

    print("\n=== Recommendations ===")
    for rec in analysis.recommendations:
        status = "completed" if rec.completed else "pending"
        print(f"- {rec.skill}: {rec.title} ({rec.resource_type}, {status})")

    print("\n=== Practice Feedback ===")
    print(f"Behavioral score: {behavioral_eval.overall_score}/{behavioral_eval.max_score} -> {behavioral_eval.summary}")
    print(f"Functional score: {functional_eval.overall_score}/{functional_eval.max_score} -> {functional_eval.summary}")

    print("\n=== Progress Dashboard ===")
    print(f"Completion rate: {report.completion_rate}")
    print(f"Behavioral trend: {report.behavioral_trend}")
    print(f"Functional trend: {report.functional_trend}")

    print("\n=== Reminders ===")
    for reminder in reminders:
        print(f"- {reminder.category}: {reminder.message} (due {reminder.due_at.date()})")


if __name__ == "__main__":
    run_demo()
