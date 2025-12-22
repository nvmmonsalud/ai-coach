# AI Coach controls and observability

This FastAPI prototype adds safety, observability, and feedback tooling for AI calls.

## Features
- **Request tracing**: Captures prompts (redacted), model versions, latencies, token counts, and estimated costs for each AI call.
- **Rate limits + retries**: In-memory sliding window to protect providers; exponential backoff with structured logging on retry.
- **PII detection and redaction**: Regex-based guard that redacts PII for logs and embedding payloads and annotates detections.
- **Feedback UI and queue**: Web forms to flag parse issues, bias, or hallucinations routed into a review queue with status updates.
- **Retention workflows**: Purge endpoints for traces and feedback aligned to data retention policies.
- **Evaluation documentation**: Datasets and periodic quality checks for parsing and matching are captured in `docs/evaluation.md`.

## Getting started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the API and UI:
   ```bash
   uvicorn ai_coach.app:app --reload
   ```
3. Try endpoints:
   - `POST /api/ai-call` with `{ "prompt": "Hello" }`
   - `POST /api/embed` with `{ "text": "My email is user@example.com" }`
   - Visit `/feedback` to submit reports and `/review-queue` to view them.

## Data retention
- Trace records are retained for 30 days; feedback is retained for 90 days.
- Trigger manual purges via `POST /retention/purge`.

## Notes
- The AI client is simulated but includes latency, cost estimation, rate limiting, retries, and redaction to mirror production controls.
- Extend `AIClient.call` to integrate with your provider SDK and forward tracing metadata.
