from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .matching import build_match_result
from .models import CandidateProfile, Feedback, JobDescription, MatchResult
from .storage import MatchStorage

DATA_PATH = Path(os.environ.get("MATCH_STORAGE_PATH", "data/matches.json"))

app = FastAPI(title="AI Coach Matching Service")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

storage = MatchStorage(DATA_PATH)


class MatchRequest(BaseModel):
    candidate: CandidateProfile
    job: JobDescription


class FeedbackRequest(BaseModel):
    source: str
    comments: str
    score_adjustment: float | None = None


@app.post("/api/match", response_model=MatchResult)
def create_match(request: MatchRequest):
    match_id = str(uuid.uuid4())
    result = build_match_result(match_id, request.candidate, request.job)
    storage.add_match(result)
    return result


@app.get("/api/candidates/{candidate_id}/matches", response_model=List[MatchResult])
def candidate_matches(candidate_id: str):
    return storage.list_by_candidate(candidate_id)


@app.get("/api/recruiters/{job_id}/matches", response_model=List[MatchResult])
def recruiter_matches(job_id: str):
    return storage.list_by_job(job_id)


@app.post("/api/matches/{match_id}/shortlist", response_model=MatchResult)
def shortlist_match(match_id: str):
    updated = storage.update_status(match_id, "shortlisted")
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return updated


@app.post("/api/matches/{match_id}/decline", response_model=MatchResult)
def decline_match(match_id: str):
    updated = storage.update_status(match_id, "declined")
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return updated


@app.post("/api/matches/{match_id}/feedback", response_model=MatchResult)
async def submit_feedback(match_id: str, request: Request):
    if request.headers.get("content-type", "").startswith(
        "application/x-www-form-urlencoded"
    ):
        form = await request.form()
        payload = dict(form)
    else:
        payload = await request.json()
    feedback_request = FeedbackRequest(**payload)
    feedback = Feedback(
        source=feedback_request.source,
        comments=feedback_request.comments,
        score_adjustment=feedback_request.score_adjustment,
    )
    updated = storage.add_feedback(match_id, feedback)
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return updated


@app.get("/api/fairness/summary")
def fairness_summary():
    return storage.fairness_report()


@app.get("/candidates/{candidate_id}", response_class=HTMLResponse)
def candidate_view(request: Request, candidate_id: str):
    matches = storage.list_by_candidate(candidate_id)
    return templates.TemplateResponse(
        "candidate.html",
        {"request": request, "matches": matches, "candidate_id": candidate_id},
    )


@app.get("/recruiters/{job_id}", response_class=HTMLResponse)
def recruiter_view(request: Request, job_id: str):
    matches = storage.list_by_job(job_id)
    return templates.TemplateResponse(
        "recruiter.html", {"request": request, "matches": matches, "job_id": job_id}
    )
