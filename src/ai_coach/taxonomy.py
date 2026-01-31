"""Skill taxonomy and resource mapping."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class SkillTaxonomy:
    """Loads skills and learning resources from a JSON taxonomy file."""

    skills: Dict[str, Dict]

    @classmethod
    def from_json(cls, path: Path) -> "SkillTaxonomy":
        raw = json.loads(path.read_text())
        return cls(skills=raw["skills"])

    @property
    def all_skills(self) -> List[str]:
        return list(self.skills.keys())

    def resources_for_skill(self, skill: str) -> Dict[str, List[Dict]]:
        return self.skills.get(skill, {}).get("resources", {})

    def taxonomy_for_skill(self, skill: str) -> Dict:
        return self.skills.get(skill, {})
