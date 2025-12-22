import logging
import random
import time
from typing import Optional

from fastapi import HTTPException

from .pii import PIIGuard
from .rate_limit import RateLimitExceeded, RateLimiter
from .tracing import TraceStore, build_trace

logger = logging.getLogger(__name__)


class AIClient:
    """Thin adapter around AI calls that adds tracing, redaction, rate limits, and retries."""

    def __init__(
        self,
        tracer: TraceStore,
        pii_guard: PIIGuard,
        rate_limiter: RateLimiter,
        default_model: str = "gpt-4o-mini",
    ) -> None:
        self.tracer = tracer
        self.pii_guard = pii_guard
        self.rate_limiter = rate_limiter
        self.default_model = default_model

    def _estimate_tokens(self, prompt: str, completion: str) -> tuple[int, int]:
        return max(1, len(prompt.split())), max(1, len(completion.split()))

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return round((prompt_tokens * 0.000002 + completion_tokens * 0.000004), 6)

    def call(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 2,
        backoff_base: float = 0.3,
    ) -> dict:
        chosen_model = model or self.default_model
        redacted_prompt = self.pii_guard.redact(prompt)
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                self.rate_limiter.check()
                start = time.perf_counter()
                # Simulate latency from an AI provider.
                simulated_latency = random.uniform(0.05, 0.25)
                time.sleep(simulated_latency)
                completion = f"[simulated {chosen_model} completion] {redacted_prompt[::-1]}"
                latency_ms = (time.perf_counter() - start) * 1000
                prompt_tokens, completion_tokens = self._estimate_tokens(redacted_prompt, completion)
                cost = self._estimate_cost(prompt_tokens, completion_tokens)
                record = build_trace(
                    prompt=redacted_prompt,
                    model=chosen_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    status="success",
                )
                self.tracer.add(record)
                logger.info(
                    "AI call success | trace=%s model=%s latency_ms=%.2f cost=$%.5f",
                    record.trace_id,
                    chosen_model,
                    latency_ms,
                    cost,
                )
                return {
                    "trace_id": record.trace_id,
                    "model": chosen_model,
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "completion": completion,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                }
            except RateLimitExceeded as exc:
                logger.warning("Rate limit hit: %s", exc)
                raise HTTPException(status_code=429, detail=str(exc)) from exc
            except Exception as exc:  # noqa: PERF203
                last_error = exc
                logger.exception("AI call failed (attempt %s/%s)", attempt + 1, max_retries + 1)
                if attempt >= max_retries:
                    record = build_trace(
                        prompt=redacted_prompt,
                        model=chosen_model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        latency_ms=0,
                        cost_usd=0,
                        status="failed",
                        metadata={"error": str(exc)},
                    )
                    self.tracer.add(record)
                    raise HTTPException(status_code=502, detail="AI provider error") from exc
                time.sleep(backoff_base * (2**attempt))
        if last_error:
            raise last_error
        raise HTTPException(status_code=500, detail="Unknown AI error")
