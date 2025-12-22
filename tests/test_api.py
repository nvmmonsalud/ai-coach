import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_app(tmp_path, monkeypatch):
    storage_path = tmp_path / "matches.json"
    monkeypatch.setenv("MATCH_STORAGE_PATH", str(storage_path))
    # Reload the module to ensure it uses the temp storage path
    app_module = importlib.import_module("app.main")
    importlib.reload(app_module)
    yield app_module.app
    importlib.reload(app_module)  # clean up state


def test_match_lifecycle_and_fairness_report(temp_app: "FastAPI"):
    client = TestClient(temp_app)

    candidate = {
        "candidate_id": "cand-9",
        "name": "Jordan",
        "skills": ["python", "ml"],
        "experience_years": 4,
        "attributes": {"gender": "prefer-not-to-say", "location": "remote"},
    }
    job = {
        "job_id": "job-9",
        "title": "ML Engineer",
        "required_skills": ["python", "ml"],
        "preferred_skills": ["docker"],
        "description": "Deploy models",
    }

    response = client.post("/api/match", json={"candidate": candidate, "job": job})
    assert response.status_code == 200
    match = response.json()
    match_id = match["match_id"]
    assert match["status"] == "pending"
    assert match["explanation"]["matched_skills"]

    shortlist = client.post(f"/api/matches/{match_id}/shortlist")
    assert shortlist.status_code == 200
    assert shortlist.json()["status"] == "shortlisted"

    feedback = client.post(
        f"/api/matches/{match_id}/feedback",
        json={"source": "candidate", "comments": "Looks good", "score_adjustment": 0.1},
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback"]

    fairness = client.get("/api/fairness/summary")
    assert fairness.status_code == 200
    report = fairness.json()
    assert "removed_attributes" in report
    assert isinstance(report["fit_score_distribution"], list)
