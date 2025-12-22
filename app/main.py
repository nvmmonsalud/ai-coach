import json
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .auth import CurrentUser, get_current_user
from .database import Base, engine, get_db
from .parser import parse_job_description
from .schemas import (
    AuditLogOut,
    JobListingOut,
    JobPostingOut,
    JobRequirementOut,
    JobSubmission,
    RubricItemOut,
    ScreeningSettingsOut,
)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title="AI Coach Recruiter Tools")


@app.on_event("startup")
def seed_users():
    with next(get_db()) as db:
        if db.query(models.Recruiter).count() == 0:
            db.add_all(
                [
                    models.Recruiter(name="Recruiter One", role="recruiter"),
                    models.Recruiter(name="Admin", role="admin"),
                ]
            )
            db.commit()


def _serialize_screening_setting(setting: models.ScreeningSetting) -> ScreeningSettingsOut:
    knockout_rules = json.loads(setting.knockout_rules) if setting.knockout_rules else []
    desired_industries = (
        json.loads(setting.desired_industries) if setting.desired_industries else []
    )
    return ScreeningSettingsOut(
        knockout_rules=knockout_rules,
        desired_industries=desired_industries,
        work_authorization=setting.work_authorization,
    )


def _build_rubric(requirements: List[models.JobRequirement]) -> List[models.RubricItem]:
    rubric_items = []
    for requirement in requirements:
        weight = 1.0 if requirement.mandatory else 0.5
        requirement_type = "mandatory" if requirement.mandatory else "preferred"
        rubric_items.append(
            models.RubricItem(
                label=requirement.description[:100],
                weight=weight,
                requirement_type=requirement_type,
            )
        )
    return rubric_items


def _create_audit_log(db: Session, recruiter_id: int, action: str, job_id: int, details: str):
    db.add(
        models.AuditLog(
            recruiter_id=recruiter_id, action=action, job_id=job_id, details=details
        )
    )
    db.commit()


@app.get("/recruiter", response_class=HTMLResponse)
async def recruiter_portal(request: Request):
    return templates.TemplateResponse("recruiter.html", {"request": request})


@app.post("/api/jobs", response_model=JobPostingOut)
async def create_job(
    submission: JobSubmission,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.user.role not in ("recruiter", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")

    job = models.JobPosting(
        title=submission.title,
        function=submission.function,
        industry=submission.industry,
        location=submission.location,
        seniority=submission.seniority,
        compensation=submission.compensation,
        job_description=submission.job_description,
        recruiter_id=current_user.user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    parsed_requirements = parse_job_description(submission.job_description)
    requirement_rows = []
    for req in parsed_requirements:
        requirement_row = models.JobRequirement(
            job_id=job.id,
            description=req.description,
            mandatory=req.mandatory,
            min_years_experience=req.min_years_experience,
        )
        requirement_rows.append(requirement_row)

    db.add_all(requirement_rows)
    db.commit()

    rubric_items = _build_rubric(requirement_rows)
    for item in rubric_items:
        item.job_id = job.id
    db.add_all(rubric_items)

    screening_setting = models.ScreeningSetting(
        job_id=job.id,
        knockout_rules=json.dumps(submission.screening_settings.knockout_rules),
        desired_industries=json.dumps(submission.screening_settings.desired_industries),
        work_authorization=submission.screening_settings.work_authorization,
    )
    db.add(screening_setting)
    db.commit()

    _create_audit_log(
        db=db,
        recruiter_id=current_user.user.id,
        action="create_job",
        job_id=job.id,
        details="Created job and generated rubric",
    )

    db.refresh(job)
    db.refresh(screening_setting)

    return JobPostingOut(
        id=job.id,
        title=job.title,
        function=job.function,
        industry=job.industry,
        location=job.location,
        seniority=job.seniority,
        compensation=job.compensation,
        job_description=job.job_description,
        created_at=job.created_at,
        requirements=[JobRequirementOut.from_orm(req) for req in requirement_rows],
        screening_settings=_serialize_screening_setting(screening_setting),
        rubric=[RubricItemOut.from_orm(item) for item in rubric_items],
    )


@app.get("/api/jobs", response_model=List[JobListingOut])
async def list_jobs(
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    query = db.query(models.JobPosting)
    if current_user.user.role != "admin":
        query = query.filter(models.JobPosting.recruiter_id == current_user.user.id)
    jobs = query.order_by(models.JobPosting.created_at.desc()).all()
    return [JobListingOut.from_orm(job) for job in jobs]


@app.get("/api/jobs/{job_id}", response_model=JobPostingOut)
async def get_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    current_user.ensure_can_access_job(job)

    screening_setting = job.screening_setting
    requirements = job.requirements
    rubric_items = job.rubric_items

    return JobPostingOut(
        id=job.id,
        title=job.title,
        function=job.function,
        industry=job.industry,
        location=job.location,
        seniority=job.seniority,
        compensation=job.compensation,
        job_description=job.job_description,
        created_at=job.created_at,
        requirements=[JobRequirementOut.from_orm(req) for req in requirements],
        screening_settings=_serialize_screening_setting(screening_setting),
        rubric=[RubricItemOut.from_orm(item) for item in rubric_items],
    )


@app.get("/api/audit", response_model=List[AuditLogOut])
async def audit_logs(
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    query = db.query(models.AuditLog)
    if current_user.user.role != "admin":
        query = query.filter(models.AuditLog.recruiter_id == current_user.user.id)
    logs = query.order_by(models.AuditLog.created_at.desc()).all()
    return [AuditLogOut.from_orm(log) for log in logs]
