import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware import RequestIDMiddleware
from app.routers import health, questions, student, admin, ingest, generate, users, dashboard

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS = {"admin-key-change-me", "student-key-change-me"}


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
    yield
    from app.database import engine
    from app.llm.factory import close_all_providers
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