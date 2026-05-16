import asyncio
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_run_with_job_limit_caps_active_jobs(monkeypatch):
    import app.job_limits as job_limits

    monkeypatch.setattr(job_limits, "get_settings", lambda: SimpleNamespace(max_concurrent_jobs=4))
    job_limits._job_semaphore = None
    job_limits._job_limit = None

    active = 0
    max_active = 0
    release = asyncio.Event()
    entered = asyncio.Event()

    async def work():
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        if active == 4:
            entered.set()
        await release.wait()
        active -= 1

    tasks = [
        asyncio.create_task(job_limits.run_with_job_limit(work))
        for _ in range(6)
    ]

    await asyncio.wait_for(entered.wait(), timeout=1)
    await asyncio.sleep(0)
    assert max_active == 4
    assert active == 4

    release.set()
    await asyncio.gather(*tasks)
