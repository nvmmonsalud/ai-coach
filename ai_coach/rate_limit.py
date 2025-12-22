import time
from collections import deque
from dataclasses import dataclass
from typing import Deque


class RateLimitExceeded(Exception):
    pass


@dataclass
class RateLimiterConfig:
    max_calls: int
    period_seconds: float


class RateLimiter:
    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self.calls: Deque[float] = deque()

    def check(self) -> None:
        now = time.time()
        window_start = now - self.config.period_seconds
        while self.calls and self.calls[0] < window_start:
            self.calls.popleft()
        if len(self.calls) >= self.config.max_calls:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {self.config.max_calls} calls per {self.config.period_seconds} seconds"
            )
        self.calls.append(now)
