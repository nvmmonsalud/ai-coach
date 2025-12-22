from app.matching import build_match_result, score_match
from app.models import CandidateProfile, JobDescription


def test_missing_required_skills_reduce_fit_score():
    candidate = CandidateProfile(
        candidate_id="cand-1",
        name="Alex",
        skills=["python", "sql"],
        experience_years=3,
    )
    job = JobDescription(
        job_id="job-1",
        title="Data Engineer",
        required_skills=["python", "airflow"],
        preferred_skills=["sql", "docker"],
        description="Pipelines and orchestration",
    )

    explanation = score_match(candidate, job)

    assert "airflow" in explanation.missing_skills
    assert explanation.fit_score < 1.5  # penalized for missing mandatory skill
    assert explanation.growth_potential >= 0.6


def test_protected_attributes_are_removed_from_scoring():
    candidate = CandidateProfile(
        candidate_id="cand-2",
        name="Sam",
        skills=["go"],
        experience_years=5,
        attributes={"gender": "non-binary", "work_style": "remote"},
    )
    job = JobDescription(
        job_id="job-2", title="Backend", required_skills=["go"], preferred_skills=[]
    )

    match = build_match_result("match-123", candidate, job)

    assert any("Removed protected attribute" in note for note in match.explanation.fairness_notes)
    assert match.fit_score >= 1.0  # required skill matched even after sanitization
    assert match.explanation.fairness_notes
