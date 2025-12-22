from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import FairnessReport, Feedback, MatchResult


class MatchStorage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"matches": [], "feedback": [], "fairness": {}})

    def _read(self) -> Dict:
        with self.path.open() as file:
            return json.load(file)

    def _write(self, payload: Dict) -> None:
        with self.path.open("w") as file:
            json.dump(payload, file, default=self._serializer, indent=2)

    def _serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "dict"):
            return obj.dict()
        return str(obj)

    def add_match(self, match: MatchResult) -> MatchResult:
        data = self._read()
        data["matches"].append(match)
        fairness = data.get("fairness", {})
        fairness.setdefault("removed_attributes", {})
        for note in match.explanation.fairness_notes:
            if "Removed protected attribute" in note:
                attribute = note.split(":")[-1].strip()
                fairness["removed_attributes"][attribute] = (
                    fairness["removed_attributes"].get(attribute, 0) + 1
                )
        fairness.setdefault("fit_score_distribution", []).append(match.fit_score)
        fairness.setdefault("growth_score_distribution", []).append(
            match.growth_potential
        )
        fairness["last_updated"] = datetime.utcnow().isoformat()
        data["fairness"] = fairness
        self._write(data)
        return match

    def update_status(self, match_id: str, status: str) -> Optional[MatchResult]:
        data = self._read()
        for item in data.get("matches", []):
            if item["match_id"] == match_id:
                item["status"] = status
                self._write(data)
                return MatchResult.parse_obj(item)
        return None

    def add_feedback(
        self, match_id: str, feedback: Feedback
    ) -> Optional[MatchResult]:
        data = self._read()
        target = None
        for item in data.get("matches", []):
            if item["match_id"] == match_id:
                item.setdefault("feedback", []).append(feedback)
                target = item
                break
        if target:
            self._write(data)
            return MatchResult.parse_obj(target)
        return None

    def list_by_candidate(self, candidate_id: str) -> List[MatchResult]:
        data = self._read()
        return [
            MatchResult.parse_obj(item)
            for item in data.get("matches", [])
            if item["candidate_id"] == candidate_id
        ]

    def list_by_job(self, job_id: str) -> List[MatchResult]:
        data = self._read()
        return [
            MatchResult.parse_obj(item)
            for item in data.get("matches", [])
            if item["job_id"] == job_id
        ]

    def fairness_report(self) -> FairnessReport:
        data = self._read()
        fairness = data.get("fairness", {})
        last_updated = fairness.get("last_updated")
        return FairnessReport(
            removed_attributes=fairness.get("removed_attributes", {}),
            fit_score_distribution=fairness.get("fit_score_distribution", []),
            growth_score_distribution=fairness.get("growth_score_distribution", []),
            last_updated=datetime.fromisoformat(last_updated)
            if last_updated
            else None,
        )

