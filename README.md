# AI Coach Matching Service

Hybrid embedding-style similarity and rules-based screening for matching candidates to job descriptions.

## Features
- Match candidates to job descriptions using token-based embedding similarity blended with mandatory-skill weighting.
- Store per-match explanations: matched and missing skills, rationale, fit score, and growth potential.
- Endpoints and lightweight UI views for candidates and recruiters to review matches, shortlist or decline, and add feedback.
- Fairness guardrails remove protected attributes from scoring and track score distributions.

## Getting started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Open dashboards:
   - Candidate view: `http://localhost:8000/candidates/<candidate_id>`
   - Recruiter view: `http://localhost:8000/recruiters/<job_id>`

## Testing
```bash
python -m pytest
```
