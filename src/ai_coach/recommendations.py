"""Generate learning recommendations tied to a skill taxonomy."""

from typing import Dict, List

from .models import Recommendation, SkillGap
from .taxonomy import SkillTaxonomy


RESOURCE_PRIORITY = ["course", "reading", "project"]


def generate_recommendations(
    gaps: List[SkillGap], taxonomy: SkillTaxonomy, completed_resources: Dict[str, List[str]]
) -> List[Recommendation]:
    recommendations: List[Recommendation] = []
    completed_resources = completed_resources or {}

    for gap in gaps:
        resources = taxonomy.resources_for_skill(gap.skill)
        prioritized = _prioritize_resources(resources)
        for resource in prioritized:
            recommendations.append(
                Recommendation(
                    skill=gap.skill,
                    title=resource["title"],
                    resource_type=resource.get("resource_type", "reading"),
                    url=resource.get("url"),
                    estimated_minutes=resource.get("estimated_minutes", 30),
                    completed=resource["title"] in completed_resources.get(gap.skill, []),
                )
            )
    return recommendations


def _prioritize_resources(resources: Dict[str, List[Dict]]) -> List[Dict]:
    prioritized: List[Dict] = []
    for resource_type in ("quick_wins", "medium_term", "interview_prep"):
        bucket = resources.get(resource_type, [])
        sorted_bucket = sorted(
            bucket,
            key=lambda item: RESOURCE_PRIORITY.index(item.get("resource_type", "reading"))
            if item.get("resource_type", "reading") in RESOURCE_PRIORITY
            else len(RESOURCE_PRIORITY),
        )
        prioritized.extend(sorted_bucket)
    return prioritized
