from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB pool, LLM clients, etc.
    yield
    # Shutdown: close DB pool, etc.


app = FastAPI(title="DSAT Grammar API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)