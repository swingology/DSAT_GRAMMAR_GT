from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware import RequestIDMiddleware
from app.routers import health, questions, student, admin, ingest, generate, users, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
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