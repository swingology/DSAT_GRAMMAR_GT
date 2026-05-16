"""Shared concurrency controls for background LLM jobs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.config import get_settings


T = TypeVar("T")

_job_semaphore: asyncio.Semaphore | None = None
_job_limit: int | None = None


def _get_job_semaphore() -> asyncio.Semaphore:
    global _job_semaphore, _job_limit
    limit = max(1, int(getattr(get_settings(), "max_concurrent_jobs", 4)))
    if _job_semaphore is None or _job_limit != limit:
        _job_semaphore = asyncio.Semaphore(limit)
        _job_limit = limit
    return _job_semaphore


async def run_with_job_limit(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """Run a background job while respecting the global active-job cap."""
    async with _get_job_semaphore():
        return await coro_factory()
