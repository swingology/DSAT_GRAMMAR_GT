import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware import RequestIDMiddleware
from app.routers import health, questions, student, admin, ingest, generate, users, dashboard, student_auth

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS = {"admin-key-change-me", "student-key-change-me"}
_INSECURE_JWT_SECRET = "change-me-in-production"


def _check_insecure_keys(settings) -> None:
    active = set(settings.admin_api_key_list) | set(settings.student_api_key_list)
    if active & _INSECURE_DEFAULTS:
        if settings.env == "production":
            raise RuntimeError(
                "SECURITY: Default API keys are active in production. "
                "Set ADMIN_API_KEYS and STUDENT_API_KEYS environment variables."
            )
        logger.warning(
            "SECURITY WARNING: Default API keys are active. "
            "Set ADMIN_API_KEYS and STUDENT_API_KEYS environment variables before deploying."
        )
    if settings.jwt_secret_key == _INSECURE_JWT_SECRET:
        if settings.env == "production":
            raise RuntimeError(
                "SECURITY: Default JWT secret key is active in production. "
                "Set JWT_SECRET_KEY environment variable."
            )
        logger.warning(
            "SECURITY WARNING: Default JWT secret key is active. "
            "Set JWT_SECRET_KEY environment variable before deploying."
        )
    if settings.env == "production" and "*" in settings.cors_origins_list:
        raise RuntimeError(
            "CORS_ALLOW_ALL_ORIGINS is not permitted in production. "
            "Set CORS_ALLOWED_ORIGINS to a comma-separated list of allowed domains."
        )


async def _seed_admin_user(settings):
    """Ensure the tutor's email exists as an active admin so Google sign-in works.

    Idempotent: promotes/reactivates an existing row rather than duplicating it.
    Password stays null — this account signs in with Google only.
    """
    from sqlalchemy import func, select
    from app.database import async_session
    from app.models.db import User

    email = settings.admin_seed_email.strip().lower()
    if not email:
        return

    async with async_session() as db:
        result = await db.execute(select(User).where(func.lower(User.email) == email))
        user = result.scalars().first()

        if user is not None:
            changed = False
            if user.role != "admin":
                user.role = "admin"
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                await db.commit()
                logger.info("Admin seed: promoted existing user %s to active admin", email)
            return

        # username is unique-constrained; don't collide with an unrelated account.
        username = settings.admin_seed_username
        taken = await db.execute(select(User).where(User.username == username))
        if taken.scalars().first():
            username = f"{username}-admin-{uuid.uuid4().hex[:6]}"

        db.add(User(username=username, email=email, role="admin", is_active=True))
        await db.commit()
        logger.info("Admin seed: created admin user %s (username=%s)", email, username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    _check_insecure_keys(settings)
    try:
        from sqlalchemy import update
        from app.database import async_session
        from app.models.db import QuestionJob
        _STUCK_STATUSES = ["parsing", "extracting", "annotating", "validating", "overlap_checking", "generating"]
        async with async_session() as _db:
            _result = await _db.execute(
                update(QuestionJob)
                .where(QuestionJob.status.in_(_STUCK_STATUSES))
                .values(
                    status="failed",
                    validation_errors_jsonb=[{"step": "startup_recovery", "error": "Server restarted while job was in-progress"}],
                )
            )
            await _db.commit()
            if _result.rowcount:
                logger.warning("Startup: marked %d stuck job(s) as failed", _result.rowcount)
    except Exception as _startup_err:
        logger.warning("Startup recovery skipped (DB unavailable): %s", _startup_err)

    try:
        await _seed_admin_user(settings)
    except Exception as _seed_err:
        # Never let seeding take the API down — it only gates Google admin sign-in.
        logger.warning("Admin seed skipped: %s", _seed_err)

    # Background sweeper: periodically mark stuck jobs as failed
    _sweeper_task = None
    if settings.job_sweeper_interval_s > 0:

        async def _stuck_job_sweeper():
            while True:
                await asyncio.sleep(settings.job_sweeper_interval_s)
                try:
                    _cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.pipeline_timeout_s)
                    async with async_session() as _db:
                        _result = await _db.execute(
                            update(QuestionJob)
                            .where(
                                QuestionJob.status.in_(_STUCK_STATUSES),
                                QuestionJob.updated_at < _cutoff,
                            )
                            .values(
                                status="failed",
                                validation_errors_jsonb=[{"step": "sweeper", "error": "Job timed out"}],
                            )
                        )
                        await _db.commit()
                        if _result.rowcount:
                            logger.warning("Sweeper: marked %d stuck job(s) as failed", _result.rowcount)
                except Exception as _sweep_err:
                    logger.warning("Sweeper error: %s", _sweep_err)

        _sweeper_task = asyncio.create_task(_stuck_job_sweeper())

    yield
    from app.database import engine
    from app.llm.factory import close_all_providers
    if _sweeper_task:
        _sweeper_task.cancel()
    await close_all_providers()
    await engine.dispose()


app = FastAPI(title="DSAT Grammar API", version="0.1.0", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(health.router)
app.include_router(questions.router)
app.include_router(student.router)
app.include_router(admin.router)
app.include_router(ingest.router)
app.include_router(generate.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(student_auth.router)