from __future__ import annotations

import time
from functools import wraps
from typing import Callable, TypeVar

import requests.exceptions as _req_err

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T")

_RETRYABLE = (
    ConnectionError,
    TimeoutError,
    OSError,
    _req_err.ConnectionError,
    _req_err.ChunkedEncodingError,
)


class RateLimiter:
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last = time.monotonic()


def with_retry(max_retries: int = 3, wait: float = 1.0, max_wait: float = 30.0):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=wait, max=max_wait),
            retry=retry_if_exception_type(_RETRYABLE),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
