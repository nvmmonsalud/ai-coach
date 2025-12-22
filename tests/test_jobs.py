from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.auth import CurrentUser, get_current_user
from app.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_recruiters():
    db = TestingSessionLocal()
    if db.query(models.Recruiter).count() == 0:
        db.add_all(
            [
                models.Recruiter(id=1, name="Recruiter One", role="recruiter"),
                models.Recruiter(id=2, name="Other Recruiter", role="recruiter"),
                models.Recruiter(id=3, name="Admin", role="admin"),
            ]
        )
        db.commit()
    db.close()


seed_recruiters()
app.dependency_overrides[get_db] = override_get_db


def get_user(user_id: int) -> CurrentUser:
    db = TestingSessionLocal()
    user = db.query(models.Recruiter).filter(models.Recruiter.id == user_id).first()
    db.close()
    return CurrentUser(user=user)


def override_user_one():
    return get_user(1)


def override_user_two():
    return get_user(2)


def override_admin():
    return get_user(3)


client = TestClient(app)
app.dependency_overrides[get_current_user] = override_user_one


def _submit_job(client: TestClient):
    payload = {
        "title": "Senior Backend Engineer",
        "function": "Engineering",
        "industry": "Software",
        "location": "Remote",
        "seniority": "Senior",
        "compensation": "$180k - $220k",
        "job_description": "\n".join(
            [
                "Must have 5+ years building REST APIs with Python",
                "Experience with FastAPI preferred",
                "Required: PostgreSQL or MySQL experience",
                "Nice to have: AWS or GCP exposure",
            ]
        ),
        "screening_settings": {
            "knockout_rules": ["No relocation", "No sponsorship"],
            "desired_industries": ["SaaS", "AI"],
            "work_authorization": "US Citizen",
        },
    }
    return client.post("/api/jobs", json=payload, headers={"X-User-Id": "1"})


def test_create_job_parses_requirements_and_screening_settings():
    response = _submit_job(client)
    assert response.status_code == 200

    body = response.json()
    assert body["title"] == "Senior Backend Engineer"
    requirements = body["requirements"]
    assert len(requirements) == 4

    mandatory_flags = [req["mandatory"] for req in requirements]
    assert mandatory_flags.count(True) == 2
    assert mandatory_flags.count(False) == 2

    years_values = [req["min_years_experience"] for req in requirements]
    assert any(years and years >= 5 for years in years_values)

    screening = body["screening_settings"]
    assert screening["knockout_rules"] == ["No relocation", "No sponsorship"]
    assert screening["desired_industries"] == ["SaaS", "AI"]
    assert screening["work_authorization"] == "US Citizen"

    rubric = body["rubric"]
    assert len(rubric) == len(requirements)

    audit_response = client.get("/api/audit", headers={"X-User-Id": "1"})
    assert audit_response.status_code == 200
    audit_entries = audit_response.json()
    assert any(entry["action"] == "create_job" for entry in audit_entries)


def test_permission_prevents_other_recruiters_from_accessing_job():
    create_response = _submit_job(client)
    job_id = create_response.json()["id"]

    app.dependency_overrides[get_current_user] = override_user_two
    forbidden_response = client.get(f"/api/jobs/{job_id}", headers={"X-User-Id": "2"})
    assert forbidden_response.status_code == 403

    app.dependency_overrides[get_current_user] = override_admin
    admin_response = client.get(f"/api/jobs/{job_id}", headers={"X-User-Id": "3"})
    assert admin_response.status_code == 200

    app.dependency_overrides[get_current_user] = override_user_one
