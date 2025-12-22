# AI Coach – Candidate Profile Pipeline

This service ingests candidate CVs, parses them into structured profiles, and emits events once profiles are ready for downstream consumers.

## Features
- `POST /api/candidates/upload` to accept CV files and persist them to object storage (local disk by default).
- Async worker that extracts text (PDF/DOCX), runs an LLM-style parser, normalizes data into taxonomy tables, and redacts PII before embedding.
- Parsed profile sections are stored with confidence scores; parsing errors are logged and surfaced for correction.
- Emits `profile_ready` events when parsing completes (or `profile_failed` on errors).

## Getting started
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn ai_coach.main:app --reload
```

The worker runs in-process and is fed by the upload endpoint. Parsed data is stored in `ai_coach.db` (SQLite) and raw files in the `storage/` directory by default.
