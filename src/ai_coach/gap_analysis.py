"""Generate gap analyses and actionable plans from match explanations."""

from collections import Counter
from typing import Dict, Iterable, List

from .models import ActionItem, GapAnalysis, Plan, Recommendation, SkillGap
from .recommendations import generate_recommendations
from .taxonomy import SkillTaxonomy


def _infer_severity(count: int) -> str:
    if count >= 3:
        return "high"
    if count == 2:
        return "medium"
    return "low"


def _extract_gaps(explanations: Iterable[str], taxonomy: SkillTaxonomy) -> List[SkillGap]:
    lower_explanations = " ".join(explanations).lower()
    matched_skills: Counter[str] = Counter()
    evidence: Dict[str, str] = {}

    for skill in taxonomy.all_skills:
        if skill.lower() in lower_explanations:
            occurrences = lower_explanations.count(skill.lower())
            matched_skills[skill] = occurrences
            evidence[skill] = f"Mentioned {occurrences} time(s) across match feedback."

    gaps: List[SkillGap] = []
    for skill, count in matched_skills.items():
        gaps.append(
            SkillGap(
                skill=skill,
                severity=_infer_severity(count),
                evidence=evidence.get(skill, "Detected via match explanation analysis."),
            )
        )
    return gaps


def _create_action_item(skill: str, category: str, taxonomy: SkillTaxonomy, resource: Dict[str, str]) -> ActionItem:
    return ActionItem(
        title=resource["title"],
        description=resource["description"],
        category=category,
        skill=skill,
        resource_type=resource.get("resource_type", "exercise"),
        estimated_minutes=resource.get("estimated_minutes", 30),
    )


def _build_plan(gaps: List[SkillGap], taxonomy: SkillTaxonomy) -> Plan:
    plan = Plan()
    for gap in gaps:
        resources = taxonomy.resources_for_skill(gap.skill)
        for resource in resources.get("quick_wins", []):
            plan.quick_wins.append(_create_action_item(gap.skill, "quick_win", taxonomy, resource))
        for resource in resources.get("medium_term", []):
            plan.medium_term.append(_create_action_item(gap.skill, "medium_term", taxonomy, resource))
        for resource in resources.get("interview_prep", []):
            plan.interview_prep.append(_create_action_item(gap.skill, "interview_prep", taxonomy, resource))
    return plan


def generate_gap_analysis(
    explanations: Iterable[str],
    taxonomy: SkillTaxonomy,
    completed_resources: Dict[str, List[str]] | None = None,
) -> GapAnalysis:
    """Create a gap analysis, plan, and recommendations from match explanations."""

    completed_resources = completed_resources or {}
    gaps = _extract_gaps(explanations, taxonomy)
    plan = _build_plan(gaps, taxonomy)
    recommendations: List[Recommendation] = generate_recommendations(
        gaps=gaps, taxonomy=taxonomy, completed_resources=completed_resources
    )
    return GapAnalysis(gaps=gaps, plan=plan, recommendations=recommendations)
