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


def _warn_if_insecure_keys(settings) -> None:
    active = set(settings.admin_api_key_list) | set(settings.student_api_key_list)
    if active & _INSECURE_DEFAULTS:
        logger.warning(
            "SECURITY WARNING: Default API keys are active. "
            "Set ADMIN_API_KEYS and STUDENT_API_KEYS environment variables before deploying."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    _warn_if_insecure_keys(settings)
    yield
    from app.database import engine
    from app.llm.factory import close_all_providers
    await close_all_providers()
    await engine.dispose()


app = FastAPI(title="DSAT Grammar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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