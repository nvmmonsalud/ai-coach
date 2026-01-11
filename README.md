# AI Coach

A FastAPI-based application that acts as a proxy for AI calls, providing safety mechanisms, observability, and feedback tooling.

## Features

- **Request Tracing**: Captures prompts (redacted), model versions, latencies, token counts, and estimated costs.
- **Rate Limiting**: In-memory sliding window rate limiter (default: 30 calls/minute) with exponential backoff support.
- **PII Guard**: Regex-based detection and redaction of PII (emails, phone numbers, SSNs, credit cards) before logging or embedding.
- **Feedback Loop**: Web interface for submitting and reviewing feedback (bias, hallucinations, parsing errors).
- **Data Retention**: Automated purging of old traces (30 days) and feedback (90 days).
- **Evaluation**: Documentation and workflows for evaluating model quality (`docs/evaluation.md`).

## Directory Structure

- `ai_coach/`: Core application logic (FastAPI app, rate limiting, PII guard, persistence).
- `api/`: Vercel serverless entry point.
- `data/`: JSON storage for traces and feedback (created at runtime).
- `docs/`: Documentation, including evaluation protocols.
- `static/`: Static assets (CSS, JS).
- `templates/`: Jinja2 templates for the web interface.

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

Start the application using Uvicorn:

```bash
uvicorn ai_coach.app:app --reload
```

The API will be available at `http://localhost:8000`.

### Vercel Deployment

The project is configured for deployment on Vercel via `vercel.json` and `api/index.py`.

## API Reference

### AI & Embeddings

- `POST /api/ai-call`
  - Body: `{"prompt": "string", "model": "optional_string"}`
  - Returns: Simulated AI response with tracing metadata.

- `POST /api/embed`
  - Body: `{"text": "string"}`
  - Returns: Sanitized text and detected PII.

### Feedback & Review

- `POST /api/feedback`
  - Submit feedback via API.
  - Body: `{"category": "string", "description": "string", "reporter": "optional_string", "trace_id": "optional_string"}`

- `GET /feedback`
  - HTML form for submitting feedback.

- `GET /review-queue`
  - HTML interface for reviewing submitted feedback.

- `POST /review-queue/{feedback_id}/close`
  - Close a feedback item.

### System & Maintenance

- `GET /health`
  - Health check endpoint. Also triggers retention cleanup.

- `GET /traces`
  - List recent traces.

- `POST /retention/purge`
  - Manually trigger data retention purge.

## Configuration

Configuration is currently handled in `ai_coach/app.py`:

- **Rate Limits**: Configured in `RateLimiterConfig` (default: 30 calls per 60 seconds).
- **Data Retention**: Configured in `RetentionPolicy` (Traces: 30 days, Feedback: 90 days).

## Data Persistence

Data is stored in JSON files within the `data/` directory:
- `traces.json`: Stores AI call traces.
- `feedback.json`: Stores submitted feedback items.

## Evaluation

See [docs/evaluation.md](docs/evaluation.md) for details on evaluation datasets, quality checks, and safety scorecards.
