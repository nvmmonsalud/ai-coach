"""Practice modules with rubric-based evaluation."""

from typing import Dict, List

from .models import EvaluationDimension, EvaluationResult, PracticeModule


practice_catalog: List[PracticeModule] = [
    PracticeModule(
        name="Behavioral: Conflict Resolution",
        module_type="behavioral",
        prompt=(
            "Share a time you navigated a team conflict. Use the STAR format "
            "(Situation, Task, Action, Result) and emphasize communication."
        ),
        rubric={
            "Structure": "Clear STAR structure with concise context and resolution.",
            "Reflection": "Shows ownership, learning, and empathy.",
            "Impact": "Quantifies results or shows meaningful outcome.",
        },
    ),
    PracticeModule(
        name="Functional: System Design - Service Decomposition",
        module_type="functional",
        prompt=(
            "Design an interview prep platform that serves personalized learning."
            " Cover requirements, data flows, APIs, and trade-offs."
        ),
        rubric={
            "Requirements": "Captures core and edge requirements for candidates.",
            "Architecture": "Provides modular components with clear responsibilities.",
            "Depth": "Discusses data, APIs, scaling, and trade-offs.",
        },
    ),
]


def evaluate_behavioral_response(module_name: str, response: str) -> EvaluationResult:
    dimensions = [
        _score_dimension(
            name="Structure",
            response=response,
            cues=["situation", "task", "action", "result"],
            weight=3,
        ),
        _score_dimension(
            name="Reflection",
            response=response,
            cues=["learn", "growth", "empath", "improv"],
            weight=2,
        ),
        _score_dimension(
            name="Impact",
            response=response,
            cues=["result", "%", "customer", "metric", "deliver"],
            weight=3,
        ),
    ]
    summary = _summarize(dimensions, module_name)
    return EvaluationResult(
        module=module_name,
        overall_score=sum(d.score for d in dimensions),
        max_score=sum(d.max_score for d in dimensions),
        summary=summary,
        dimensions=dimensions,
        recommendations=_module_recommendations(dimensions),
    )


def evaluate_functional_response(module_name: str, response: str) -> EvaluationResult:
    dimensions = [
        _score_dimension(
            name="Requirements",
            response=response,
            cues=["candidate", "coach", "notification", "progress"],
            weight=3,
        ),
        _score_dimension(
            name="Architecture",
            response=response,
            cues=["service", "api", "module", "component", "cache"],
            weight=3,
        ),
        _score_dimension(
            name="Depth",
            response=response,
            cues=["trade-off", "scal", "database", "latency", "storage"],
            weight=4,
        ),
    ]
    summary = _summarize(dimensions, module_name)
    return EvaluationResult(
        module=module_name,
        overall_score=sum(d.score for d in dimensions),
        max_score=sum(d.max_score for d in dimensions),
        summary=summary,
        dimensions=dimensions,
        recommendations=_module_recommendations(dimensions),
    )


def _score_dimension(name: str, response: str, cues: List[str], weight: int) -> EvaluationDimension:
    lowered = response.lower()
    hits = sum(1 for cue in cues if cue in lowered)
    max_score = weight
    score = min(hits, weight)
    feedback = (
        f"Great coverage for {name}." if score == max_score else f"Add more detail on {name.lower()}."
    )
    return EvaluationDimension(name=name, score=score, max_score=max_score, feedback=feedback)


def _module_recommendations(dimensions: List[EvaluationDimension]) -> List[str]:
    recommendations = []
    for dim in dimensions:
        if dim.score < dim.max_score:
            recommendations.append(dim.feedback)
    if not recommendations:
        recommendations.append("Keep refining timing and clarity for concise delivery.")
    return recommendations


def _summarize(dimensions: List[EvaluationDimension], module_name: str) -> str:
    completed = [d for d in dimensions if d.score == d.max_score]
    gaps = [d for d in dimensions if d.score < d.max_score]
    parts = [f"Evaluated {module_name}."]
    if completed:
        parts.append("Strengths: " + ", ".join(d.name for d in completed) + ".")
    if gaps:
        parts.append("Focus: " + ", ".join(d.name for d in gaps) + ".")
    return " ".join(parts)
