"""Retry wrapper for LLM provider calls with exponential backoff."""

import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Type

from httpx import HTTPStatusError, RequestError, TimeoutException

logger = logging.getLogger(__name__)

RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

_RETRYABLE_EXCEPTIONS: tuple[Type[Exception], ...] = (
    TimeoutException,
    RequestError,
    ConnectionError,
)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, HTTPStatusError):
        return exc.response.status_code in RETRYABLE_HTTP_CODES
    return False


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> Callable:
    """Decorator: retry an async LLM call on rate limits, server errors, or network failures.

    Uses exponential backoff with jitter.  Logs each retry with attempt number and delay.
    """
    def decorator(
        fn: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if not _is_retryable(exc) or attempt == max_attempts:
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    import random
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    logger.warning(
                        "LLM call attempt %d/%d failed: %s.  Retrying in %.2fs",
                        attempt, max_attempts, exc, total_delay,
                    )
                    await asyncio.sleep(total_delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
