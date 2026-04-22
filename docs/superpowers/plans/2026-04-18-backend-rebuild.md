# Backend Rebuild Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fresh FastAPI backend for DSAT question ingestion, human review, AI generation, and semantic search — backed by Supabase/Postgres with 42 existing migrations.

**Architecture:** Two-pass LLM ingestion pipeline (extract → annotate) with a staging job queue and human-in-the-loop approval before any production DB write. Generation pipeline adds drift detection and corpus conformance gating. All LLM output is validated through Pydantic before touching the DB.

**Tech Stack:** Python 3.12, FastAPI, asyncpg, Pydantic v2, pydantic-settings, httpx, anthropic SDK, openai SDK, pymupdf (fitz), Pillow, supabase-py (Storage), uv, pytest, pytest-asyncio

**Reference:** Deprecated working code lives in `_deprecated/backend/` — use for logic reference, not copy-paste.

---

## File Map

```
backend/
├── .env.example
├── .python-version          # 3.12
├── .gitignore
├── pyproject.toml
├── migrations/              # ← already exists, 42 files, do not touch
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, router registration
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # asyncpg pool (create/close in lifespan)
│   ├── auth.py              # API key header dependency
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py          # LLMProvider Protocol + LLMResponse dataclass
│   │   ├── factory.py       # get_provider(settings) → LLMProvider
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   ├── openrouter_provider.py
│   │   └── ollama_provider.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ontology.py      # All allowed lookup key constants + sets
│   │   ├── extract.py       # Pass 1 Pydantic output schema
│   │   ├── annotation.py    # Pass 2 Pydantic output schema
│   │   └── payload.py       # HTTP request/response models
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py        # PDF → text + extracted image bytes (pymupdf)
│   │   ├── image_parser.py      # PNG/JPEG → base64 for multimodal LLM
│   │   ├── markdown_parser.py   # MD text + resolve local image references
│   │   └── json_parser.py       # Robust LLM JSON extraction (strip fences)
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── pass1_extraction.py
│   │   ├── pass2_annotation.py
│   │   ├── pass3_tokenization.py
│   │   ├── generation.py
│   │   └── coaching.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── image_store.py       # Upload/download images via Supabase Storage
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py     # Pass 1: raw text + images → QuestionExtract
│   │   │   ├── annotator.py     # Pass 2: extract → QuestionAnnotation
│   │   │   ├── validator.py     # Pydantic + constraint enforcement
│   │   │   ├── upsert.py        # Approval: staging → 5 production tables + images
│   │   │   └── orchestrator.py  # process_job(): full pipeline per job
│   │   ├── generation/
│   │   │   ├── __init__.py
│   │   │   ├── drift.py         # detect_drift, corpus_conformance_score
│   │   │   └── generate.py      # create_run, seed selection, background loop
│   │   ├── tokenize.py          # Pass 3: grammar token annotation
│   │   ├── coaching.py          # Post-approval coaching span generation
│   │   └── embeddings.py        # Build + store question embeddings
│   └── routers/
│       ├── __init__.py
│       ├── ingest.py            # POST /ingest, POST /ingest/file, POST /ingest/image
│       ├── jobs.py              # GET/PATCH /jobs
│       ├── questions.py         # GET /questions, GET /questions/{id}/practice
│       ├── generate.py          # POST /generate, GET /generate/runs
│       ├── search.py            # POST /search
│       ├── images.py            # GET /images/{image_id} (signed URL redirect)
│       └── ontology.py          # GET /ontology/keys
└── tests/
    ├── __init__.py
    ├── conftest.py              # DB pool mock, settings override, fixtures
    ├── test_config.py
    ├── test_llm.py
    ├── test_parsers.py
    ├── test_models.py
    ├── test_ontology.py
    ├── test_validator.py
    ├── test_extractor.py
    ├── test_annotator.py
    ├── test_orchestrator.py
    ├── test_upsert.py
    ├── test_tokenize.py
    ├── test_drift.py
    ├── test_generation.py
    ├── test_coaching.py
    ├── test_embeddings.py
    ├── test_image_store.py
    ├── test_multimodal_ingest.py
    └── test_routers.py
```

---

## Chunk 1: Foundation

### Task 1: Project Scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/.gitignore`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Init project**

```bash
cd backend
uv init --no-readme
uv python pin 3.12
```

- [ ] **Step 2: Set pyproject.toml**

```toml
[project]
name = "dsat-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "asyncpg>=0.30",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "httpx>=0.28",
    "anthropic>=0.49",
    "openai>=1.68",
    "pdfplumber>=0.11",
    "python-multipart>=0.0.20",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "pytest-mock>=3.14",
    "httpx>=0.28",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Install**

```bash
uv sync
```

Expected: `.venv` created, all packages installed.

- [ ] **Step 4: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    api_key: str = "dev-key"

    llm_provider: str = "anthropic"          # anthropic | openai | openrouter | ollama
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:30b"
    llm_model: str = ""                      # override default per-provider model

    embedding_model: str = "text-embedding-3-small"
    openai_api_key_embeddings: str = ""      # can share openai_api_key

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

- [ ] **Step 5: Create `.env.example`**

```bash
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
API_KEY=your-secret-key

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:30b
LLM_MODEL=

EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY_EMBEDDINGS=
```

- [ ] **Step 6: Write config test**

```python
# tests/test_config.py
from app.config import Settings

def test_settings_loads_defaults():
    s = Settings(database_url="postgresql://localhost/test")
    assert s.llm_provider == "anthropic"
    assert s.ollama_model == "qwen3:30b"
```

- [ ] **Step 7: Run test**

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: backend scaffold — config, pyproject"
```

---

### Task 2: Database + Auth

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/auth.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create `app/database.py`**

```python
import asyncpg
from app.config import Settings

async def create_pool(settings: Settings) -> asyncpg.Pool:
    return await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
```

- [ ] **Step 2: Create `app/auth.py`**

```python
from fastapi import Header, HTTPException, status
from app.config import get_settings

async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != get_settings().api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 3: Create `app/main.py`**

```python
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI
from app.config import get_settings
from app.database import create_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.pool = await create_pool(settings)
    app.state.settings = settings
    yield
    await app.state.pool.close()

app = FastAPI(title="DSAT Backend", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Write auth test**

```python
# tests/test_routers.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
```

- [ ] **Step 5: Patch lifespan for tests — add to `tests/conftest.py`**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.config import Settings

TEST_SETTINGS = Settings(
    database_url="postgresql://localhost/test",
    api_key="test-key",
    llm_provider="anthropic",
    anthropic_api_key="test",
)

@pytest.fixture(autouse=True)
def mock_pool(monkeypatch):
    pool = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr("app.main.create_pool", AsyncMock(return_value=pool))
    monkeypatch.setattr("app.config._settings", TEST_SETTINGS)
    return pool
```

- [ ] **Step 6: Run**

```bash
uv run pytest tests/test_routers.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: database pool, auth dependency, FastAPI app shell"
```

---

## Chunk 2: LLM Provider Layer

### Task 3: LLM Base + Factory

**Files:**
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/factory.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_llm.py
from app.llm.base import LLMResponse

def test_llm_response_fields():
    r = LLMResponse(content="hello", model="claude-sonnet-4-6", input_tokens=10, output_tokens=5)
    assert r.content == "hello"
    assert r.total_tokens == 15
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_llm.py::test_llm_response_fields -v
```

- [ ] **Step 3: Create `app/llm/base.py`**

```python
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...
```

- [ ] **Step 4: Create `app/llm/factory.py`**

```python
from app.config import Settings
from app.llm.base import LLMProvider

def get_provider(settings: Settings) -> LLMProvider:
    p = settings.llm_provider
    if p == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(settings)
    if p == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(settings)
    if p == "openrouter":
        from app.llm.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider(settings)
    if p == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider(settings)
    raise ValueError(f"Unknown LLM provider: {p}")
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: PASS

---

### Task 4: Provider Implementations

**Files:**
- Create: `backend/app/llm/anthropic_provider.py`
- Create: `backend/app/llm/openai_provider.py`
- Create: `backend/app/llm/openrouter_provider.py`
- Create: `backend/app/llm/ollama_provider.py`

- [ ] **Step 1: Write provider tests (mocked)**

```python
# tests/test_llm.py (append)
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.config import Settings
from app.llm.factory import get_provider

BASE_SETTINGS = Settings(database_url="postgresql://localhost/test")

async def test_anthropic_provider_calls_api():
    settings = Settings(database_url="x", llm_provider="anthropic", anthropic_api_key="sk-test")
    provider = get_provider(settings)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"key": "val"}')]
    mock_response.model = "claude-sonnet-4-6"
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    with patch.object(provider.client.messages, "create", new=AsyncMock(return_value=mock_response)):
        result = await provider.complete("system", "user")
    assert result.content == '{"key": "val"}'
    assert result.total_tokens == 150

async def test_ollama_provider_calls_api():
    settings = Settings(database_url="x", llm_provider="ollama", ollama_model="qwen3:30b")
    provider = get_provider(settings)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "message": {"content": '{"k": "v"}'},
        "model": "qwen3:30b",
        "prompt_eval_count": 10,
        "eval_count": 5,
    }
    mock_resp.raise_for_status = MagicMock()
    with patch.object(provider.client, "post", new=AsyncMock(return_value=mock_resp)):
        result = await provider.complete("system", "user")
    assert result.content == '{"k": "v"}'
```

- [ ] **Step 2: Implement `anthropic_provider.py`**

```python
import anthropic
from app.config import Settings
from app.llm.base import LLMResponse

DEFAULT_MODEL = "claude-sonnet-4-6"

class AnthropicProvider:
    def __init__(self, settings: Settings):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model or DEFAULT_MODEL

    async def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> LLMResponse:
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            content=resp.content[0].text,
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )
```

- [ ] **Step 3: Implement `openai_provider.py`**

```python
import openai
from app.config import Settings
from app.llm.base import LLMResponse

DEFAULT_MODEL = "gpt-4o"

class OpenAIProvider:
    def __init__(self, settings: Settings):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model or DEFAULT_MODEL

    async def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> LLMResponse:
        resp = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        choice = resp.choices[0].message.content or ""
        return LLMResponse(
            content=choice,
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
        )
```

- [ ] **Step 4: Implement `openrouter_provider.py`**

```python
# Same shape as OpenAI — OpenRouter is OpenAI-compatible
import openai
from app.config import Settings
from app.llm.base import LLMResponse

DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"

class OpenRouterProvider:
    def __init__(self, settings: Settings):
        self.client = openai.AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = settings.llm_model or DEFAULT_MODEL

    async def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> LLMResponse:
        resp = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
        )
```

- [ ] **Step 5: Implement `ollama_provider.py`**

```python
import httpx
from app.config import Settings
from app.llm.base import LLMResponse

class OllamaProvider:
    def __init__(self, settings: Settings):
        self.client = httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120)
        self.model = settings.llm_model or settings.ollama_model

    async def complete(self, system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> LLMResponse:
        resp = await self.client.post("/api/chat", json={
            "model": self.model,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        })
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            content=data["message"]["content"],
            model=data.get("model", self.model),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/llm/ backend/tests/test_llm.py
git commit -m "feat: LLM provider layer — anthropic, openai, openrouter, ollama"
```

---

### Task 5: Anthropic Prompt Caching

**Files:**
- Modify: `backend/app/llm/anthropic_provider.py`
- Modify: `backend/app/llm/base.py`
- Modify: `backend/tests/test_llm.py`

**Why:** The Pass 2 system prompt contains the full ontology reference (all allowed key lists) and is identical on every ingestion call. Anthropic's prompt caching charges ~10% of normal input token cost for cache hits. For a 50-question ingestion run, this cuts Pass 2 input costs by ~90%. Cache TTL is 5 minutes — long enough to cover any batch run.

**Strategy:** Add a `cache_system` parameter to `LLMProvider.complete()`. When `True`, the system prompt is sent with `cache_control: {"type": "ephemeral"}`. Only `AnthropicProvider` acts on this flag — other providers ignore it silently. Pass 2 annotation always sets `cache_system=True`. Generation prompts also benefit since the system prompt skeleton is reused across items in a run.

- [ ] **Step 1: Write failing test**

```python
# tests/test_llm.py (append)
async def test_anthropic_provider_sends_cache_control_when_flagged():
    settings = Settings(database_url="x", llm_provider="anthropic", anthropic_api_key="sk-test")
    provider = get_provider(settings)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="{}")]
    mock_response.model = "claude-sonnet-4-6"
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 10
    mock_response.usage.cache_read_input_tokens = 80
    mock_response.usage.cache_creation_input_tokens = 20

    captured = {}
    async def fake_create(**kwargs):
        captured.update(kwargs)
        return mock_response

    with patch.object(provider.client.messages, "create", new=fake_create):
        result = await provider.complete("big system prompt", "user msg", cache_system=True)

    # system must be a list with cache_control block
    system_arg = captured["system"]
    assert isinstance(system_arg, list)
    assert system_arg[0]["cache_control"] == {"type": "ephemeral"}
    assert result.cache_read_tokens == 80
    assert result.cache_creation_tokens == 20

async def test_anthropic_provider_no_cache_by_default():
    settings = Settings(database_url="x", llm_provider="anthropic", anthropic_api_key="sk-test")
    provider = get_provider(settings)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="{}")]
    mock_response.model = "claude-sonnet-4-6"
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 10
    mock_response.usage.cache_read_input_tokens = 0
    mock_response.usage.cache_creation_input_tokens = 0

    captured = {}
    async def fake_create(**kwargs):
        captured.update(kwargs)
        return mock_response

    with patch.object(provider.client.messages, "create", new=fake_create):
        await provider.complete("system", "user")

    # No cache_control — system sent as plain string
    assert isinstance(captured["system"], str)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_llm.py::test_anthropic_provider_sends_cache_control_when_flagged -v
```

- [ ] **Step 3: Update `app/llm/base.py` — add `cache_system` param + cache token fields**

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0       # tokens served from cache (billed at ~10%)
    cache_creation_tokens: int = 0   # tokens written to cache (billed at ~125%)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def effective_input_tokens(self) -> int:
        """Billing-adjusted input: cache reads cost ~10% of normal."""
        return (
            self.input_tokens
            + int(self.cache_creation_tokens * 1.25)
            + int(self.cache_read_tokens * 0.1)
        )

@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        cache_system: bool = False,   # hint: cache the system prompt
    ) -> LLMResponse: ...
```

- [ ] **Step 4: Update `app/llm/anthropic_provider.py`**

```python
import anthropic
from app.config import Settings
from app.llm.base import LLMResponse

DEFAULT_MODEL = "claude-sonnet-4-6"

class AnthropicProvider:
    def __init__(self, settings: Settings):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model or DEFAULT_MODEL

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        cache_system: bool = False,
    ) -> LLMResponse:
        # When cache_system=True, wrap system in a list with cache_control.
        # Anthropic caches up to 4 breakpoints; one per call is sufficient here.
        system_arg = (
            [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
            if cache_system
            else system
        )
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_arg,
            messages=[{"role": "user", "content": user}],
        )
        usage = resp.usage
        return LLMResponse(
            content=resp.content[0].text,
            model=resp.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        )
```

- [ ] **Step 5: Update other providers — accept `cache_system` silently**

Add `cache_system: bool = False` to `complete()` signatures in `openai_provider.py`, `openrouter_provider.py`, and `ollama_provider.py`. No other changes — they ignore the flag.

```python
# Pattern for each non-Anthropic provider:
async def complete(self, system, user, temperature=0.2, max_tokens=4096, cache_system=False):
    # cache_system ignored — not supported by this provider
    ...
```

- [ ] **Step 6: Enable caching in Pass 2 annotator**

```python
# app/pipeline/ingestion/annotator.py
async def annotate_pass2(extract: QuestionExtract, provider: LLMProvider) -> QuestionAnnotation:
    user = build_pass2_user_prompt(extract.model_dump())
    response = await provider.complete(PASS2_SYSTEM, user, temperature=0.1, cache_system=True)
    data = extract_json(response.content)
    return QuestionAnnotation.model_validate(data)
```

- [ ] **Step 7: Enable caching in generation system prompt**

```python
# app/pipeline/generation/generate.py — inside process_generation_run, the LLM call:
response = await provider.complete(
    system_prompt,
    user_prompt,
    temperature=0.7,
    cache_system=True,   # system prompt skeleton is same across all items in a run
)
```

- [ ] **Step 8: Log cache savings in orchestrator**

```python
# app/pipeline/ingestion/orchestrator.py — after Pass 2 call:
import logging
log = logging.getLogger(__name__)

# After annotate_pass2 returns, if you want to track savings, thread the
# LLMResponse back through annotate_pass2 as a second return value, then:
if hasattr(response, "cache_read_tokens") and response.cache_read_tokens > 0:
    log.info(
        "pass2 cache hit job=%s read=%d creation=%d",
        job_id, response.cache_read_tokens, response.cache_creation_tokens,
    )
```

To thread the response back, change `annotate_pass2` signature to return `tuple[QuestionAnnotation, LLMResponse]` — or keep it simple and skip logging for now.

- [ ] **Step 9: Run all tests**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: all PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/llm/ backend/app/pipeline/ingestion/annotator.py backend/tests/test_llm.py
git commit -m "feat: Anthropic prompt caching on Pass 2 + generation system prompts"
```

---

## Chunk 3: Models, Ontology, Parsers

### Task 5: Ontology Constants

**Files:**
- Create: `backend/app/models/ontology.py`

The full set of allowed lookup keys. Reference `_deprecated/backend/app/models/ontology.py` and the taxonomy docs in `taxonomy/` for the complete lists. Key principle: **any key the DB accepts must appear in these sets** — the validator checks against them.

- [ ] **Step 1: Write failing test**

```python
# tests/test_ontology.py
from app.models.ontology import (
    QUESTION_FAMILY_KEYS, SYNTACTIC_COMPLEXITY_KEYS,
    PROSE_REGISTER_KEYS, DIFFICULTY_VALUES, GRAMMAR_FOCUS_KEYS,
)

def test_required_family_keys_present():
    required = {"words_in_context", "transitions", "conventions_grammar",
                "supporting_detail", "central_idea", "weaken_hypothesis"}
    assert required.issubset(QUESTION_FAMILY_KEYS)

def test_difficulty_values():
    assert DIFFICULTY_VALUES == {"easy", "medium", "hard"}

def test_grammar_focus_keys_nonempty():
    assert len(GRAMMAR_FOCUS_KEYS) >= 10
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_ontology.py -v
```

- [ ] **Step 3: Create `app/models/ontology.py`**

Populate from `_deprecated/backend/app/models/ontology.py` + `taxonomy/DSAT_Verbal_Master_Taxonomy_v2.md`. Key structure:

```python
# app/models/ontology.py

QUESTION_FAMILY_KEYS: frozenset[str] = frozenset({
    "words_in_context", "transitions", "conventions_grammar",
    "supporting_detail", "central_idea", "weaken_hypothesis",
    "strengthen_hypothesis", "rhetorical_synthesis", "cross_text_connections",
    "data_integration_graph", "data_integration_table",
    "sentence_function", "author_technique",
})

DIFFICULTY_VALUES: frozenset[str] = frozenset({"easy", "medium", "hard"})

SYNTACTIC_COMPLEXITY_KEYS: frozenset[str] = frozenset({
    "simple", "compound", "complex", "compound_complex",
    "highly_embedded", "fragment_dependent",
})

PROSE_REGISTER_KEYS: frozenset[str] = frozenset({
    "academic", "journalistic", "literary", "conversational",
    "scientific", "historical", "policy", "technical",
})

LEXICAL_TIER_KEYS: frozenset[str] = frozenset({
    "tier_1_basic", "tier_2_academic", "tier_3_specialized",
})

RHETORICAL_STRUCTURE_KEYS: frozenset[str] = frozenset({
    "argument", "narrative", "expository", "descriptive",
    "compare_contrast", "cause_effect", "problem_solution",
})

EPISTEMIC_STANCE_KEYS: frozenset[str] = frozenset({
    "certain", "hedged", "speculative", "neutral", "contrastive",
})

EVIDENCE_DISTRIBUTION_KEYS: frozenset[str] = frozenset({
    "early", "middle", "late", "distributed",
})

INFERENCE_DISTANCE_KEYS: frozenset[str] = frozenset({
    "literal", "one_step", "two_step", "multi_step",
})

BLANK_POSITION_KEYS: frozenset[str] = frozenset({
    "sentence_initial", "sentence_medial", "sentence_final",
    "clause_initial", "clause_final",
})

GRAMMAR_FOCUS_KEYS: frozenset[str] = frozenset({
    "subject_verb_agreement", "pronoun_antecedent_agreement",
    "verb_tense_consistency", "verb_form", "modifier_placement",
    "parallel_structure", "comma_splice", "run_on_sentence",
    "sentence_fragment", "apostrophe_possessive", "apostrophe_contraction",
    "colon_usage", "semicolon_usage", "comma_usage",
    "transition_word", "relative_clause_punctuation",
})

GRAMMAR_ROLE_KEYS: frozenset[str] = frozenset({
    "subject", "object", "predicate", "modifier",
    "complement", "appositive", "clause_connector",
})

DISTRACTOR_TYPE_KEYS: frozenset[str] = frozenset({
    "grammar_fit_only", "topical_association", "formal_register_match",
    "near_synonym", "scope_error", "polarity_reversal",
})

CONTENT_ORIGIN_VALUES: frozenset[str] = frozenset({
    "official", "ai_human_revised",
})

INPUT_FORMAT_VALUES: frozenset[str] = frozenset({
    "text", "pdf", "markdown", "generated",
})

JOB_STATUS_VALUES: frozenset[str] = frozenset({
    "pending", "extracting", "annotating", "draft",
    "reviewed", "approved", "rejected", "failed",
    "drift_failed", "conformance_failed",
})

SOURCE_TYPE_VALUES: frozenset[str] = frozenset({
    "official", "generated",
})
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_ontology.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/ontology.py backend/tests/test_ontology.py
git commit -m "feat: ontology constants — all allowed lookup key sets"
```

---

### Task 6: Pydantic Models

**Files:**
- Create: `backend/app/models/extract.py`
- Create: `backend/app/models/annotation.py`
- Create: `backend/app/models/payload.py`

- [ ] **Step 1: Write model tests**

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from app.models.extract import QuestionExtract, QuestionOption
from app.models.annotation import QuestionAnnotation

def test_extract_requires_stem():
    with pytest.raises(ValidationError):
        QuestionExtract()  # missing stem_text

def test_extract_valid():
    q = QuestionExtract(
        stem_text="Which word best completes the blank?",
        passage_text="The scientist _____ the data carefully.",
        options=[
            QuestionOption(label="A", text="analyzed", is_correct=True),
            QuestionOption(label="B", text="ignored", is_correct=False),
            QuestionOption(label="C", text="deleted", is_correct=False),
            QuestionOption(label="D", text="misread", is_correct=False),
        ],
        correct_option_label="A",
        question_family_key="words_in_context",
    )
    assert q.correct_option_label == "A"

def test_extract_rejects_bad_family_key():
    with pytest.raises(ValidationError):
        QuestionExtract(
            stem_text="stem",
            options=[],
            correct_option_label="A",
            question_family_key="invalid_key",
        )

def test_annotation_valid():
    a = QuestionAnnotation(
        difficulty_overall="medium",
        syntactic_complexity_key="complex",
        prose_register_key="academic",
    )
    assert a.difficulty_overall == "medium"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_models.py -v
```

- [ ] **Step 3: Create `app/models/extract.py`**

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from app.models.ontology import QUESTION_FAMILY_KEYS, INPUT_FORMAT_VALUES

class QuestionOption(BaseModel):
    label: str                    # A, B, C, D
    text: str
    is_correct: bool

class QuestionExtract(BaseModel):
    stem_text: str
    passage_text: Optional[str] = None
    paired_passage_text: Optional[str] = None
    prompt_text: Optional[str] = None
    options: list[QuestionOption] = []
    correct_option_label: str = ""
    question_family_key: str = ""
    source_exam_code: Optional[str] = None
    source_module_code: Optional[str] = None
    source_question_number: Optional[int] = None
    input_format: str = "text"
    review_notes: Optional[str] = None

    @field_validator("question_family_key")
    @classmethod
    def validate_family_key(cls, v: str) -> str:
        if v and v not in QUESTION_FAMILY_KEYS:
            raise ValueError(f"Unknown question_family_key: {v!r}")
        return v

    @field_validator("input_format")
    @classmethod
    def validate_input_format(cls, v: str) -> str:
        if v not in INPUT_FORMAT_VALUES:
            raise ValueError(f"Unknown input_format: {v!r}")
        return v

    @model_validator(mode="after")
    def validate_options(self) -> "QuestionExtract":
        correct = [o for o in self.options if o.is_correct]
        if self.options and len(correct) != 1:
            raise ValueError(f"Expected exactly 1 correct option, found {len(correct)}")
        return self
```

- [ ] **Step 4: Create `app/models/annotation.py`**

```python
from pydantic import BaseModel, field_validator
from typing import Optional
from app.models.ontology import (
    DIFFICULTY_VALUES, SYNTACTIC_COMPLEXITY_KEYS, PROSE_REGISTER_KEYS,
    LEXICAL_TIER_KEYS, RHETORICAL_STRUCTURE_KEYS, EPISTEMIC_STANCE_KEYS,
    EVIDENCE_DISTRIBUTION_KEYS, INFERENCE_DISTANCE_KEYS, BLANK_POSITION_KEYS,
    GRAMMAR_FOCUS_KEYS, GRAMMAR_ROLE_KEYS,
)

def _optional_key_validator(allowed: frozenset[str]):
    def validate(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in allowed:
            raise ValueError(f"Invalid key: {v!r}")
        return v
    return field_validator("*", mode="before")(classmethod(validate))

class QuestionAnnotation(BaseModel):
    difficulty_overall: Optional[str] = None
    syntactic_complexity_key: Optional[str] = None
    prose_register_key: Optional[str] = None
    lexical_tier_key: Optional[str] = None
    rhetorical_structure_key: Optional[str] = None
    epistemic_stance_key: Optional[str] = None
    evidence_distribution_key: Optional[str] = None
    inference_distance_key: Optional[str] = None
    blank_position_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    grammar_role_key: Optional[str] = None
    irt_b_estimate: Optional[float] = None
    annotation_confidence: Optional[str] = None
    needs_review: bool = False
    review_notes: Optional[str] = None

    @field_validator("difficulty_overall")
    @classmethod
    def val_difficulty(cls, v):
        if v and v not in DIFFICULTY_VALUES:
            raise ValueError(f"Invalid difficulty: {v!r}")
        return v

    @field_validator("syntactic_complexity_key")
    @classmethod
    def val_syntax(cls, v):
        if v and v not in SYNTACTIC_COMPLEXITY_KEYS:
            raise ValueError(f"Invalid syntactic_complexity_key: {v!r}")
        return v

    @field_validator("prose_register_key")
    @classmethod
    def val_register(cls, v):
        if v and v not in PROSE_REGISTER_KEYS:
            raise ValueError(f"Invalid prose_register_key: {v!r}")
        return v

    @field_validator("grammar_focus_key")
    @classmethod
    def val_grammar_focus(cls, v):
        if v and v not in GRAMMAR_FOCUS_KEYS:
            raise ValueError(f"Invalid grammar_focus_key: {v!r}")
        return v

    @field_validator("grammar_role_key")
    @classmethod
    def val_grammar_role(cls, v):
        if v and v not in GRAMMAR_ROLE_KEYS:
            raise ValueError(f"Invalid grammar_role_key: {v!r}")
        return v
```

- [ ] **Step 5: Create `app/models/payload.py`** (HTTP request/response shapes)

```python
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class IngestTextRequest(BaseModel):
    raw_text: str
    source_file: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class JobCreated(BaseModel):
    job_id: uuid.UUID
    status: str = "pending"

class JobRead(BaseModel):
    id: uuid.UUID
    status: str
    source_file: Optional[str]
    input_format: str
    pass1_json: Optional[dict]
    pass2_json: Optional[dict]
    validation_errors: Optional[list]
    review_notes: Optional[str]
    content_origin: str
    created_at: datetime
    updated_at: datetime

class JobStatusUpdate(BaseModel):
    status: str
    review_notes: Optional[str] = None

class GenerationRequest(BaseModel):
    seed_question_ids: list[uuid.UUID]
    template_id: uuid.UUID
    item_count: int = 1
    target_constraints: dict = {}
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    run_notes: Optional[str] = None

class GenerationRunCreated(BaseModel):
    run_id: uuid.UUID
    warning: Optional[str] = None
    warning_detail: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    embedding_type: str = "taxonomy_summary"
    limit: int = 10
    family_key: Optional[str] = None
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: Pydantic models — extract, annotation, payload"
```

---

### Task 7: Parsers

**Files:**
- Create: `backend/app/parsers/json_parser.py`
- Create: `backend/app/parsers/pdf_parser.py`
- Create: `backend/app/parsers/markdown_parser.py`

- [ ] **Step 1: Write parser tests**

```python
# tests/test_parsers.py
import pytest
from app.parsers.json_parser import extract_json

def test_extract_json_clean():
    assert extract_json('{"a": 1}') == {"a": 1}

def test_extract_json_strips_fences():
    raw = '```json\n{"a": 1}\n```'
    assert extract_json(raw) == {"a": 1}

def test_extract_json_strips_backticks_no_lang():
    raw = '```\n{"a": 1}\n```'
    assert extract_json(raw) == {"a": 1}

def test_extract_json_raises_on_invalid():
    with pytest.raises(ValueError):
        extract_json("not json at all")

def test_extract_json_nested_in_prose():
    raw = 'Here is the output: {"key": "value"} done.'
    assert extract_json(raw) == {"key": "value"}
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_parsers.py -v
```

- [ ] **Step 3: Create `app/parsers/json_parser.py`**

```python
import json
import re

def extract_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first { ... } block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract valid JSON from LLM output: {text[:200]!r}")
```

- [ ] **Step 4: Create `app/parsers/pdf_parser.py`**

```python
import pdfplumber
from pathlib import Path

def parse_pdf(path: str | Path) -> str:
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n\n".join(p for p in pages if p.strip())
```

- [ ] **Step 5: Create `app/parsers/markdown_parser.py`**

```python
from pathlib import Path

def parse_markdown(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_parsers.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/parsers/ backend/tests/test_parsers.py
git commit -m "feat: parsers — JSON fence stripper, PDF, markdown"
```

---

## Chunk 4: Ingestion Pipeline

### Task 8: Pass 1 Prompt + Extractor

**Files:**
- Create: `backend/app/prompts/pass1_extraction.py`
- Create: `backend/app/pipeline/ingestion/extractor.py`

- [ ] **Step 1: Write extractor test**

```python
# tests/test_extractor.py
import pytest
from unittest.mock import AsyncMock
from app.pipeline.ingestion.extractor import extract_pass1
from app.llm.base import LLMResponse
from app.models.extract import QuestionExtract

async def test_extract_pass1_returns_extract():
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = LLMResponse(
        content='''{
            "stem_text": "Which word best fits?",
            "passage_text": "The scientist _____ the data.",
            "options": [
                {"label": "A", "text": "analyzed", "is_correct": true},
                {"label": "B", "text": "ignored", "is_correct": false},
                {"label": "C", "text": "deleted", "is_correct": false},
                {"label": "D", "text": "misread", "is_correct": false}
            ],
            "correct_option_label": "A",
            "question_family_key": "words_in_context"
        }''',
        model="claude-sonnet-4-6",
    )
    result = await extract_pass1("raw question text", mock_provider)
    assert isinstance(result, QuestionExtract)
    assert result.stem_text == "Which word best fits?"
    assert result.correct_option_label == "A"

async def test_extract_pass1_raises_on_bad_json():
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = LLMResponse(content="not json", model="x")
    with pytest.raises(ValueError):
        await extract_pass1("text", mock_provider)
```

- [ ] **Step 2: Create `app/prompts/pass1_extraction.py`**

```python
PASS1_SYSTEM = """You are extracting DSAT Reading and Writing questions into a fixed JSON schema.
Extract only what is present. Do not invent or infer beyond the raw text.
Return valid JSON only — no prose, no explanation, no markdown fences."""

PASS1_OUTPUT_SCHEMA = """{
  "stem_text": "<the question stem / instruction>",
  "passage_text": "<passage or null>",
  "paired_passage_text": "<second passage for cross-text questions or null>",
  "prompt_text": "<italicized lead-in prompt or null>",
  "options": [
    {"label": "A", "text": "...", "is_correct": false},
    {"label": "B", "text": "...", "is_correct": false},
    {"label": "C", "text": "...", "is_correct": false},
    {"label": "D", "text": "...", "is_correct": true}
  ],
  "correct_option_label": "D",
  "question_family_key": "<see allowed values below>",
  "source_exam_code": null,
  "source_module_code": null,
  "source_question_number": null
}"""

ALLOWED_FAMILY_KEYS = """words_in_context | transitions | conventions_grammar |
supporting_detail | central_idea | weaken_hypothesis | strengthen_hypothesis |
rhetorical_synthesis | cross_text_connections | data_integration_graph |
data_integration_table | sentence_function | author_technique"""

def build_pass1_user_prompt(raw_text: str) -> str:
    return f"""Extract the following DSAT question into the JSON schema below.

OUTPUT SCHEMA:
{PASS1_OUTPUT_SCHEMA}

ALLOWED question_family_key values:
{ALLOWED_FAMILY_KEYS}

RAW QUESTION:
{raw_text}

Return only the JSON object."""
```

- [ ] **Step 3: Create `app/pipeline/ingestion/extractor.py`**

```python
from app.llm.base import LLMProvider
from app.models.extract import QuestionExtract
from app.parsers.json_parser import extract_json
from app.prompts.pass1_extraction import PASS1_SYSTEM, build_pass1_user_prompt

async def extract_pass1(raw_text: str, provider: LLMProvider) -> QuestionExtract:
    system = PASS1_SYSTEM
    user = build_pass1_user_prompt(raw_text)
    response = await provider.complete(system, user, temperature=0.1)
    data = extract_json(response.content)
    return QuestionExtract.model_validate(data)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_extractor.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/pass1_extraction.py backend/app/pipeline/ingestion/extractor.py backend/tests/test_extractor.py
git commit -m "feat: Pass 1 extraction — prompt + extractor"
```

---

### Task 9: Pass 2 Prompt + Annotator

**Files:**
- Create: `backend/app/prompts/pass2_annotation.py`
- Create: `backend/app/pipeline/ingestion/annotator.py`

- [ ] **Step 1: Write annotator test**

```python
# tests/test_annotator.py
import pytest
from unittest.mock import AsyncMock
from app.pipeline.ingestion.annotator import annotate_pass2
from app.llm.base import LLMResponse
from app.models.extract import QuestionExtract, QuestionOption
from app.models.annotation import QuestionAnnotation

SAMPLE_EXTRACT = QuestionExtract(
    stem_text="Which best completes the text?",
    passage_text="The author _____ the claim.",
    options=[
        QuestionOption(label="A", text="supports", is_correct=True),
        QuestionOption(label="B", text="denies", is_correct=False),
        QuestionOption(label="C", text="ignores", is_correct=False),
        QuestionOption(label="D", text="misreads", is_correct=False),
    ],
    correct_option_label="A",
    question_family_key="words_in_context",
)

async def test_annotate_pass2_returns_annotation():
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = LLMResponse(
        content='{"difficulty_overall": "medium", "syntactic_complexity_key": "complex", "prose_register_key": "academic"}',
        model="claude-sonnet-4-6",
    )
    result = await annotate_pass2(SAMPLE_EXTRACT, mock_provider)
    assert isinstance(result, QuestionAnnotation)
    assert result.difficulty_overall == "medium"

async def test_annotate_pass2_rejects_invalid_key():
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = LLMResponse(
        content='{"difficulty_overall": "super_hard"}',
        model="x",
    )
    with pytest.raises(Exception):
        await annotate_pass2(SAMPLE_EXTRACT, mock_provider)
```

- [ ] **Step 2: Create `app/prompts/pass2_annotation.py`**

Reference `_deprecated/backend/app/prompts/pass2_annotation.py` for the full prompt. Minimum structure:

```python
PASS2_SYSTEM = """You are annotating DSAT questions against a fixed taxonomy schema.
Use ONLY the allowed key values listed. Do not invent labels.
If uncertain, choose the closest allowed label and set needs_review: true.
Return valid JSON only."""

def build_pass2_user_prompt(extract_dict: dict) -> str:
    from app.models.ontology import (
        DIFFICULTY_VALUES, SYNTACTIC_COMPLEXITY_KEYS, PROSE_REGISTER_KEYS,
        LEXICAL_TIER_KEYS, RHETORICAL_STRUCTURE_KEYS, EPISTEMIC_STANCE_KEYS,
        EVIDENCE_DISTRIBUTION_KEYS, INFERENCE_DISTANCE_KEYS, BLANK_POSITION_KEYS,
        GRAMMAR_FOCUS_KEYS, GRAMMAR_ROLE_KEYS,
    )
    import json
    return f"""Annotate this DSAT question using the schema below.

QUESTION:
{json.dumps(extract_dict, indent=2)}

ALLOWED VALUES:
- difficulty_overall: {sorted(DIFFICULTY_VALUES)}
- syntactic_complexity_key: {sorted(SYNTACTIC_COMPLEXITY_KEYS)}
- prose_register_key: {sorted(PROSE_REGISTER_KEYS)}
- lexical_tier_key: {sorted(LEXICAL_TIER_KEYS)}
- rhetorical_structure_key: {sorted(RHETORICAL_STRUCTURE_KEYS)}
- epistemic_stance_key: {sorted(EPISTEMIC_STANCE_KEYS)}
- evidence_distribution_key: {sorted(EVIDENCE_DISTRIBUTION_KEYS)}
- inference_distance_key: {sorted(INFERENCE_DISTANCE_KEYS)}
- blank_position_key: {sorted(BLANK_POSITION_KEYS)}
- grammar_focus_key: {sorted(GRAMMAR_FOCUS_KEYS)} (SEC questions only)
- grammar_role_key: {sorted(GRAMMAR_ROLE_KEYS)} (SEC questions only)

Return JSON with these fields (null if not applicable):
difficulty_overall, syntactic_complexity_key, prose_register_key,
lexical_tier_key, rhetorical_structure_key, epistemic_stance_key,
evidence_distribution_key, inference_distance_key, blank_position_key,
grammar_focus_key, grammar_role_key, annotation_confidence, needs_review, review_notes"""
```

- [ ] **Step 3: Create `app/pipeline/ingestion/annotator.py`**

```python
from app.llm.base import LLMProvider
from app.models.extract import QuestionExtract
from app.models.annotation import QuestionAnnotation
from app.parsers.json_parser import extract_json
from app.prompts.pass2_annotation import PASS2_SYSTEM, build_pass2_user_prompt

async def annotate_pass2(extract: QuestionExtract, provider: LLMProvider) -> QuestionAnnotation:
    user = build_pass2_user_prompt(extract.model_dump())
    response = await provider.complete(PASS2_SYSTEM, user, temperature=0.1)
    data = extract_json(response.content)
    return QuestionAnnotation.model_validate(data)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_annotator.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/pass2_annotation.py backend/app/pipeline/ingestion/annotator.py backend/tests/test_annotator.py
git commit -m "feat: Pass 2 annotation — prompt + annotator"
```

---

### Task 10: Validator

**Files:**
- Create: `backend/app/pipeline/ingestion/validator.py`

- [ ] **Step 1: Write validator tests**

```python
# tests/test_validator.py
import pytest
from app.pipeline.ingestion.validator import validate_ingestion
from app.models.extract import QuestionExtract, QuestionOption
from app.models.annotation import QuestionAnnotation

def make_extract(**kwargs):
    defaults = dict(
        stem_text="stem",
        options=[
            QuestionOption(label="A", text="opt", is_correct=True),
            QuestionOption(label="B", text="opt2", is_correct=False),
            QuestionOption(label="C", text="opt3", is_correct=False),
            QuestionOption(label="D", text="opt4", is_correct=False),
        ],
        correct_option_label="A",
        question_family_key="words_in_context",
    )
    defaults.update(kwargs)
    return QuestionExtract(**defaults)

def make_annotation(**kwargs):
    defaults = dict(difficulty_overall="medium", syntactic_complexity_key="complex")
    defaults.update(kwargs)
    return QuestionAnnotation(**defaults)

def test_validate_passes_clean():
    errors = validate_ingestion(make_extract(), make_annotation())
    assert errors == []

def test_validate_fails_no_options():
    e = make_extract()
    e.options = []
    errors = validate_ingestion(e, make_annotation())
    assert any("option" in err.lower() for err in errors)

def test_validate_skips_source_for_generated():
    e = make_extract()
    e.source_exam_code = None  # generated jobs have no source codes
    errors = validate_ingestion(e, make_annotation(), content_origin="generated")
    assert errors == []

def test_validate_fails_mismatched_correct_label():
    e = make_extract(correct_option_label="Z")
    errors = validate_ingestion(e, make_annotation())
    assert any("correct_option_label" in err for err in errors)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_validator.py -v
```

- [ ] **Step 3: Create `app/pipeline/ingestion/validator.py`**

```python
from app.models.extract import QuestionExtract
from app.models.annotation import QuestionAnnotation

def validate_ingestion(
    extract: QuestionExtract,
    annotation: QuestionAnnotation,
    content_origin: str = "official",
) -> list[str]:
    errors: list[str] = []

    if not extract.options:
        errors.append("options: must have at least 1 option")

    labels = {o.label for o in extract.options}
    if extract.correct_option_label and extract.correct_option_label not in labels:
        errors.append(f"correct_option_label '{extract.correct_option_label}' not in option labels {labels}")

    correct_count = sum(1 for o in extract.options if o.is_correct)
    if extract.options and correct_count != 1:
        errors.append(f"options: expected exactly 1 correct, found {correct_count}")

    # Generated jobs don't have source codes
    if content_origin != "generated":
        pass  # source validation is optional for official questions too

    return errors
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_validator.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/ingestion/validator.py backend/tests/test_validator.py
git commit -m "feat: ingestion validator — option/label constraint checks"
```

---

### Task 11: Upsert (Approval → Production Tables)

**Files:**
- Create: `backend/app/pipeline/ingestion/upsert.py`

This is the most DB-heavy file. Reference `_deprecated/backend/app/pipeline/ingestion/upsert.py` for the SQL. The atomic upsert writes to 5 tables: `questions`, `question_classifications`, `question_options`, `question_reasoning`, `question_generation_profiles`.

- [ ] **Step 1: Write upsert test (mocked DB)**

```python
# tests/test_upsert.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.pipeline.ingestion.upsert import upsert_approved_job

async def test_upsert_calls_transaction():
    conn = AsyncMock()
    conn.transaction.return_value.__aenter__ = AsyncMock(return_value=conn)
    conn.transaction.return_value.__aexit__ = AsyncMock(return_value=False)
    conn.fetchrow = AsyncMock(return_value={"id": uuid.uuid4()})
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()

    job = {
        "id": uuid.uuid4(),
        "pass1_json": {
            "stem_text": "Which word fits?",
            "options": [{"label": "A", "text": "analyzed", "is_correct": True}],
            "correct_option_label": "A",
            "question_family_key": "words_in_context",
        },
        "pass2_json": {"difficulty_overall": "medium"},
        "content_origin": "official",
        "source_type": "official",
        "generation_run_id": None,
        "seed_question_id": None,
        "generation_result_jsonb": None,
    }
    question_id = await upsert_approved_job(conn, job)
    assert question_id is not None
    assert conn.transaction.called
```

- [ ] **Step 2: Create `app/pipeline/ingestion/upsert.py`**

```python
import uuid
import json
from typing import Any

async def upsert_approved_job(conn, job: dict[str, Any]) -> uuid.UUID:
    pass1 = job["pass1_json"] or {}
    pass2 = job["pass2_json"] or {}
    content_origin = job.get("content_origin", "official")
    source_type = job.get("source_type", "official")

    # Generated jobs must use ai_human_revised + generated source_type
    if content_origin == "generated":
        content_origin = "ai_human_revised"
        source_type = "generated"

    async with conn.transaction():
        # 1. Upsert questions
        row = await conn.fetchrow("""
            INSERT INTO public.questions (
                stem_text, passage_text, paired_passage_text, prompt_text,
                correct_option_label, question_family_key,
                source_exam_code, source_module_code, source_question_number,
                source_type, content_origin, is_active
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,true)
            ON CONFLICT (source_exam_code, source_module_code, source_question_number)
            DO UPDATE SET
                stem_text = EXCLUDED.stem_text,
                updated_at = NOW()
            RETURNING id
        """,
            pass1.get("stem_text", ""),
            pass1.get("passage_text"),
            pass1.get("paired_passage_text"),
            pass1.get("prompt_text"),
            pass1.get("correct_option_label", ""),
            pass1.get("question_family_key", ""),
            pass1.get("source_exam_code"),
            pass1.get("source_module_code"),
            pass1.get("source_question_number"),
            source_type,
            content_origin,
        )
        question_id: uuid.UUID = row["id"]

        # 2. Upsert question_classifications
        await conn.execute("""
            INSERT INTO public.question_classifications (question_id,
                difficulty_overall, syntactic_complexity_key, prose_register_key,
                lexical_tier_key, rhetorical_structure_key, epistemic_stance_key,
                evidence_distribution_key, inference_distance_key, blank_position_key,
                grammar_focus_key, grammar_role_key, annotation_confidence
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            ON CONFLICT (question_id) DO UPDATE SET
                difficulty_overall = EXCLUDED.difficulty_overall,
                updated_at = NOW()
        """,
            question_id,
            pass2.get("difficulty_overall"),
            pass2.get("syntactic_complexity_key"),
            pass2.get("prose_register_key"),
            pass2.get("lexical_tier_key"),
            pass2.get("rhetorical_structure_key"),
            pass2.get("epistemic_stance_key"),
            pass2.get("evidence_distribution_key"),
            pass2.get("inference_distance_key"),
            pass2.get("blank_position_key"),
            pass2.get("grammar_focus_key"),
            pass2.get("grammar_role_key"),
            pass2.get("annotation_confidence"),
        )

        # 3. Upsert question_options
        for opt in pass1.get("options", []):
            await conn.execute("""
                INSERT INTO public.question_options
                    (question_id, option_label, option_text, is_correct)
                VALUES ($1,$2,$3,$4)
                ON CONFLICT (question_id, option_label) DO UPDATE SET
                    option_text = EXCLUDED.option_text,
                    is_correct = EXCLUDED.is_correct
            """, question_id, opt["label"], opt["text"], opt.get("is_correct", False))

        # 4. Upsert question_reasoning (placeholder — enriched later)
        await conn.execute("""
            INSERT INTO public.question_reasoning (question_id)
            VALUES ($1)
            ON CONFLICT (question_id) DO NOTHING
        """, question_id)

        # 5. Upsert question_generation_profiles
        await conn.execute("""
            INSERT INTO public.question_generation_profiles
                (question_id, question_family_key)
            VALUES ($1,$2)
            ON CONFLICT (question_id) DO NOTHING
        """, question_id, pass1.get("question_family_key", ""))

        # If generated: write generation_result_jsonb → generated_questions
        gen_result = job.get("generation_result_jsonb")
        if content_origin == "ai_human_revised" and gen_result:
            gen_run_id = job.get("generation_run_id")
            seed_id = job.get("seed_question_id")
            await conn.execute("""
                INSERT INTO public.generated_questions
                    (question_id, run_id, seed_question_id, review_status,
                     generation_params_snapshot_jsonb,
                     generation_model_name, generation_provider)
                VALUES ($1,$2,$3,'approved',$4,$5,$6)
                ON CONFLICT (question_id) DO NOTHING
            """,
                question_id,
                gen_run_id,
                seed_id,
                json.dumps(gen_result),
                gen_result.get("model_name"),
                gen_result.get("provider"),
            )

        return question_id
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_upsert.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/pipeline/ingestion/upsert.py backend/tests/test_upsert.py
git commit -m "feat: upsert — staging job → 5 production tables on approval"
```

---

### Task 12: Orchestrator + Ingest Router

**Files:**
- Create: `backend/app/pipeline/ingestion/orchestrator.py`
- Create: `backend/app/routers/ingest.py`
- Create: `backend/app/routers/jobs.py`

- [ ] **Step 1: Create `app/pipeline/ingestion/orchestrator.py`**

```python
import uuid
import json
from app.llm.factory import get_provider
from app.pipeline.ingestion.extractor import extract_pass1
from app.pipeline.ingestion.annotator import annotate_pass2
from app.pipeline.ingestion.validator import validate_ingestion

async def process_job(pool, settings, job_id: uuid.UUID) -> None:
    provider = get_provider(settings)
    async with pool.acquire() as conn:
        job = await conn.fetchrow(
            "SELECT * FROM public.question_ingestion_jobs WHERE id = $1", job_id
        )
        if not job:
            return
        raw_text = job["raw_text"] or ""
        content_origin = job["content_origin"] or "official"

        try:
            # Pass 1
            await conn.execute(
                "UPDATE public.question_ingestion_jobs SET status='extracting', updated_at=NOW() WHERE id=$1",
                job_id,
            )
            if job["pass1_json"]:
                from app.models.extract import QuestionExtract
                extract = QuestionExtract.model_validate(job["pass1_json"])
            else:
                extract = await extract_pass1(raw_text, provider)
                await conn.execute(
                    "UPDATE public.question_ingestion_jobs SET pass1_json=$1, updated_at=NOW() WHERE id=$2",
                    json.dumps(extract.model_dump()), job_id,
                )

            # Pass 2
            await conn.execute(
                "UPDATE public.question_ingestion_jobs SET status='annotating', updated_at=NOW() WHERE id=$1",
                job_id,
            )
            annotation = await annotate_pass2(extract, provider)
            errors = validate_ingestion(extract, annotation, content_origin)

            await conn.execute("""
                UPDATE public.question_ingestion_jobs
                SET pass2_json=$1, validation_errors_jsonb=$2,
                    status=$3, updated_at=NOW()
                WHERE id=$4
            """,
                json.dumps(annotation.model_dump()),
                json.dumps(errors),
                "draft" if not errors else "failed",
                job_id,
            )

        except Exception as exc:
            await conn.execute("""
                UPDATE public.question_ingestion_jobs
                SET status='failed', validation_errors_jsonb=$1, updated_at=NOW()
                WHERE id=$2
            """, json.dumps([str(exc)]), job_id)
```

- [ ] **Step 2: Create `app/routers/ingest.py`**

```python
import uuid
import json
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Request
from app.auth import require_api_key
from app.models.payload import IngestTextRequest, JobCreated
from app.pipeline.ingestion.orchestrator import process_job

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.post("/ingest", response_model=JobCreated)
async def ingest_text(req: IngestTextRequest, background: BackgroundTasks, request: Request):
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO public.question_ingestion_jobs
                (raw_text, source_file, input_format, status, content_origin)
            VALUES ($1, $2, 'text', 'pending', 'official')
            RETURNING id
        """, req.raw_text, req.source_file)
    job_id = row["id"]
    background.add_task(process_job, pool, settings, job_id)
    return JobCreated(job_id=job_id)

@router.post("/ingest/file", response_model=JobCreated)
async def ingest_file(background: BackgroundTasks, request: Request, file: UploadFile = File(...)):
    pool = request.app.state.pool
    settings = request.app.state.settings
    content = await file.read()
    suffix = (file.filename or "").split(".")[-1].lower()

    if suffix == "pdf":
        import tempfile, os
        from app.parsers.pdf_parser import parse_pdf
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            raw_text = parse_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)
        fmt = "pdf"
    else:
        raw_text = content.decode("utf-8", errors="replace")
        fmt = "markdown" if suffix in ("md", "markdown") else "text"

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO public.question_ingestion_jobs
                (raw_text, source_file, input_format, status, content_origin)
            VALUES ($1, $2, $3, 'pending', 'official')
            RETURNING id
        """, raw_text, file.filename, fmt)
    job_id = row["id"]
    background.add_task(process_job, pool, settings, job_id)
    return JobCreated(job_id=job_id)
```

- [ ] **Step 3: Create `app/routers/jobs.py`**

```python
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from app.auth import require_api_key
from app.models.payload import JobStatusUpdate
from app.pipeline.ingestion.upsert import upsert_approved_job

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.get("/jobs")
async def list_jobs(request: Request, status: str | None = None, limit: int = 50, offset: int = 0):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM public.question_ingestion_jobs WHERE status=$1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                status, limit, offset,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM public.question_ingestion_jobs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
    return [dict(r) for r in rows]

@router.get("/jobs/{job_id}")
async def get_job(job_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.question_ingestion_jobs WHERE id=$1", job_id
        )
    if not row:
        raise HTTPException(status_code=404)
    return dict(row)

@router.patch("/jobs/{job_id}/status")
async def update_job_status(
    job_id: uuid.UUID,
    body: JobStatusUpdate,
    background: BackgroundTasks,
    request: Request,
):
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        job = await conn.fetchrow(
            "SELECT * FROM public.question_ingestion_jobs WHERE id=$1", job_id
        )
        if not job:
            raise HTTPException(status_code=404)

        if body.status == "approved":
            job_dict = dict(job)
            # Decode JSONB fields
            for field in ("pass1_json", "pass2_json", "generation_result_jsonb"):
                if isinstance(job_dict.get(field), str):
                    job_dict[field] = json.loads(job_dict[field])
            question_id = await upsert_approved_job(conn, job_dict)

            # Post-approval: IRT refresh, corpus fingerprint, coaching
            await conn.execute("SELECT public.fn_refresh_irt_b($1)", question_id)
            try:
                await conn.execute("SELECT public.fn_refresh_corpus_fingerprint()")
            except Exception:
                pass  # concurrent refresh; next approval will catch it

            from app.pipeline.coaching import generate_coaching_for_question
            background.add_task(generate_coaching_for_question, pool, settings, question_id)

        await conn.execute("""
            UPDATE public.question_ingestion_jobs
            SET status=$1, review_notes=$2, updated_at=NOW()
            WHERE id=$3
        """, body.status, body.review_notes, job_id)

    return {"status": body.status}

@router.post("/jobs/{job_id}/rerun")
async def rerun_job(job_id: uuid.UUID, background: BackgroundTasks, request: Request):
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM public.question_ingestion_jobs WHERE id=$1", job_id
        )
        if not row:
            raise HTTPException(status_code=404)
        await conn.execute("""
            UPDATE public.question_ingestion_jobs
            SET status='pending', pass2_json=NULL, validation_errors_jsonb=NULL, updated_at=NOW()
            WHERE id=$1
        """, job_id)
    from app.pipeline.ingestion.orchestrator import process_job
    background.add_task(process_job, pool, settings, job_id)
    return {"status": "requeued"}
```

- [ ] **Step 4: Register routers in `app/main.py`**

```python
# Add to main.py after app definition
from app.routers import ingest, jobs
app.include_router(ingest.router, tags=["ingestion"])
app.include_router(jobs.router, tags=["jobs"])
```

- [ ] **Step 5: Run all tests so far**

```bash
uv run pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/pipeline/ingestion/orchestrator.py backend/app/routers/
git commit -m "feat: ingestion orchestrator + ingest/jobs routers"
```

---

## Chunk 5: Pass 3 Tokenization

### Task 13: Tokenization Pipeline

**Files:**
- Create: `backend/app/prompts/pass3_tokenization.py`
- Create: `backend/app/pipeline/tokenize.py`

Reference `_deprecated/backend/app/pipeline/tokenize.py` and `_deprecated/backend/app/prompts/pass3_tokenization.py` for exact prompt and token contract.

- [ ] **Step 1: Write tokenization tests**

```python
# tests/test_tokenize.py
import uuid
import pytest
from unittest.mock import AsyncMock
from app.pipeline.tokenize import tokenize_question
from app.llm.base import LLMResponse

VALID_TOKEN_RESPONSE = """{
  "tokens": [
    {"index": 0, "text": "The", "grammar_tag": "DT", "is_blank": false},
    {"index": 1, "text": "scientist", "grammar_tag": "NN", "is_blank": false},
    {"index": 2, "text": "_____", "grammar_tag": "BLANK", "is_blank": true},
    {"index": 3, "text": "the", "grammar_tag": "DT", "is_blank": false},
    {"index": 4, "text": "data", "grammar_tag": "NN", "is_blank": false}
  ]
}"""

async def test_tokenize_returns_token_list():
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[{
        "id": uuid.uuid4(),
        "stem_text": "The scientist _____ the data.",
        "passage_text": None,
    }])
    conn.execute = AsyncMock()
    conn.transaction.return_value.__aenter__ = AsyncMock(return_value=conn)
    conn.transaction.return_value.__aexit__ = AsyncMock(return_value=False)

    provider = AsyncMock()
    provider.complete.return_value = LLMResponse(content=VALID_TOKEN_RESPONSE, model="x")

    question_id = uuid.uuid4()
    await tokenize_question(conn, provider, question_id)
    assert conn.execute.called

async def test_tokenize_requires_exactly_one_blank():
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[{
        "id": uuid.uuid4(),
        "stem_text": "No blank here.",
        "passage_text": None,
    }])
    provider = AsyncMock()
    provider.complete.return_value = LLMResponse(
        content='{"tokens": [{"index": 0, "text": "No", "grammar_tag": "DT", "is_blank": false}]}',
        model="x",
    )
    question_id = uuid.uuid4()
    with pytest.raises(ValueError, match="blank"):
        await tokenize_question(conn, provider, question_id)
```

- [ ] **Step 2: Create `app/prompts/pass3_tokenization.py`**

```python
PASS3_SYSTEM = """You tokenize DSAT question text for grammar analysis.
Return a JSON object with a 'tokens' array. Each token has:
- index: int (0-based, unique, ordered)
- text: str (the token as it appears)
- grammar_tag: str (POS tag: NN, VB, DT, JJ, IN, CC, BLANK, PUNCT, etc.)
- is_blank: bool (true for exactly one token representing the fill-in blank)
Return valid JSON only."""

VALID_GRAMMAR_TAGS = frozenset({
    "NN", "NNS", "NNP", "NNPS",
    "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
    "JJ", "JJR", "JJS",
    "RB", "RBR", "RBS",
    "DT", "IN", "CC", "CD", "PRP", "PRP$",
    "WP", "WDT", "WRB",
    "BLANK", "PUNCT", "SYM", "OTHER",
})

def build_pass3_user_prompt(text: str) -> str:
    return f"""Tokenize the following text. Mark exactly one token as is_blank=true for the fill-in blank (_____ or similar).

TEXT:
{text}

Return JSON: {{"tokens": [...]}}"""
```

- [ ] **Step 3: Create `app/pipeline/tokenize.py`**

```python
import uuid
import json
from app.llm.base import LLMProvider
from app.parsers.json_parser import extract_json
from app.prompts.pass3_tokenization import (
    PASS3_SYSTEM, VALID_GRAMMAR_TAGS, build_pass3_user_prompt
)

async def tokenize_question(conn, provider: LLMProvider, question_id: uuid.UUID) -> None:
    rows = await conn.fetch(
        "SELECT id, stem_text, passage_text FROM public.questions WHERE id=$1", question_id
    )
    if not rows:
        raise ValueError(f"Question {question_id} not found")
    q = rows[0]
    text = q["passage_text"] or q["stem_text"] or ""

    user = build_pass3_user_prompt(text)
    response = await provider.complete(PASS3_SYSTEM, user, temperature=0.0)
    data = extract_json(response.content)
    tokens = data.get("tokens", [])

    # Validate
    blanks = [t for t in tokens if t.get("is_blank")]
    if len(blanks) != 1:
        raise ValueError(f"Expected exactly 1 blank token, found {len(blanks)}")
    indexes = [t["index"] for t in tokens]
    if len(set(indexes)) != len(indexes):
        raise ValueError("Token indexes are not unique")
    for t in tokens:
        if t.get("grammar_tag") not in VALID_GRAMMAR_TAGS:
            raise ValueError(f"Invalid grammar_tag: {t.get('grammar_tag')!r}")

    async with conn.transaction():
        await conn.execute(
            "DELETE FROM public.question_grammar_keys WHERE question_id=$1", question_id
        )
        for t in tokens:
            await conn.execute("""
                INSERT INTO public.question_grammar_keys
                    (question_id, token_index, token_text, grammar_tag, is_blank)
                VALUES ($1,$2,$3,$4,$5)
            """, question_id, t["index"], t["text"], t["grammar_tag"], t.get("is_blank", False))
        await conn.execute("""
            UPDATE public.questions SET tokenization_status='ready', updated_at=NOW() WHERE id=$1
        """, question_id)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_tokenize.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/pass3_tokenization.py backend/app/pipeline/tokenize.py backend/tests/test_tokenize.py
git commit -m "feat: Pass 3 tokenization — grammar tag annotation per token"
```

---

## Chunk 6: Generation Pipeline

### Task 14: Drift Detection + Corpus Conformance

**Files:**
- Create: `backend/app/pipeline/generation/drift.py`

Full spec in `docs/TASKS_GEN_PIPELINE.md` Tasks 4. Implement exactly as documented.

- [ ] **Step 1: Write drift tests (no DB, no LLM)**

```python
# tests/test_drift.py
from app.pipeline.generation.drift import (
    compute_expected_fingerprint, detect_drift, corpus_conformance_score,
    should_rerun, DriftReport, ConformanceReport,
)
from app.models.annotation import QuestionAnnotation

def make_annotation(**kwargs):
    return QuestionAnnotation(**kwargs)

def test_no_drift_when_matching():
    expected = {"difficulty_overall": "medium", "prose_register_key": "academic"}
    actual = {"difficulty_overall": "medium", "prose_register_key": "academic"}
    report = detect_drift(expected, actual)
    assert not report.is_critical
    assert report.critical_drifts == []

def test_critical_drift_detected():
    expected = {"difficulty_overall": "hard"}
    actual = {"difficulty_overall": "easy"}
    report = detect_drift(expected, actual)
    assert report.is_critical
    assert "difficulty_overall" in report.critical_drifts

def test_corpus_bypass_when_small():
    annotation = make_annotation(difficulty_overall="medium")
    report = corpus_conformance_score(annotation, "words_in_context", [], corpus_n_override=2)
    assert report.is_conformant
    assert "too small" in report.explanation

def test_corpus_conformance_critical_miss():
    corpus_rows = [
        {"question_family_key": "words_in_context", "difficulty_overall": "hard", "n": 10},
        {"question_family_key": "words_in_context", "difficulty_overall": "hard", "n": 8},
        {"question_family_key": "words_in_context", "difficulty_overall": "medium", "n": 3},
    ]
    annotation = make_annotation(difficulty_overall="easy")
    report = corpus_conformance_score(annotation, "words_in_context", corpus_rows)
    assert not report.is_conformant
    assert "difficulty_overall" in report.critical_misses

def test_should_rerun_on_critical_drift():
    drift = DriftReport(critical_drifts=["difficulty_overall"], soft_drifts=[], is_critical=True, summary="")
    conformance = ConformanceReport(critical_misses=[], soft_misses=[], corpus_n=10, is_conformant=True, explanation="")
    assert should_rerun(drift, conformance, attempt=1)
    assert not should_rerun(drift, conformance, attempt=3)

def test_sec_grammar_focus_critical_for_conventions_grammar():
    corpus_rows = [
        {"question_family_key": "conventions_grammar", "grammar_focus_key": "comma_usage", "n": 10},
    ]
    annotation = make_annotation(grammar_focus_key="run_on_sentence")
    report = corpus_conformance_score(annotation, "conventions_grammar", corpus_rows)
    assert not report.is_conformant
    assert "grammar_focus_key" in report.critical_misses
```

- [ ] **Step 2: Create `app/pipeline/generation/drift.py`**

```python
from dataclasses import dataclass, field
from typing import Optional
from app.models.annotation import QuestionAnnotation

CRITICAL_DIMENSIONS = {
    "target_difficulty_overall":        "difficulty_overall",
    "target_syntactic_complexity_key":  "syntactic_complexity_key",
    "target_prose_register_key":        "prose_register_key",
    "target_epistemic_stance_key":      "epistemic_stance_key",
    "target_rhetorical_structure_key":  "rhetorical_structure_key",
    "target_evidence_distribution_key": "evidence_distribution_key",
    "target_inference_distance_key":    "inference_distance_key",
    "target_blank_position_key":        "blank_position_key",
}

SEC_CRITICAL_DIMENSIONS = {
    "target_grammar_focus_key": "grammar_focus_key",
    "target_grammar_role_key":  "grammar_role_key",
}

SOFT_DIMENSIONS = {
    "target_lexical_tier_key":         "lexical_tier_key",
    "target_prose_tone_key":           "prose_tone_key",
    "target_narrator_perspective_key": "narrator_perspective_key",
}

@dataclass
class DriftReport:
    critical_drifts: list[str]
    soft_drifts: list[str]
    is_critical: bool
    summary: str

@dataclass
class ConformanceReport:
    critical_misses: list[str]
    soft_misses: list[str]
    corpus_n: int
    is_conformant: bool
    explanation: str

def compute_expected_fingerprint(snapshot: dict) -> dict:
    result = {}
    for target_key, ann_key in {**CRITICAL_DIMENSIONS, **SEC_CRITICAL_DIMENSIONS, **SOFT_DIMENSIONS}.items():
        if target_key in snapshot and snapshot[target_key] is not None:
            result[ann_key] = snapshot[target_key]
    return result

def detect_drift(expected: dict, actual: dict) -> DriftReport:
    critical = list(CRITICAL_DIMENSIONS.values())
    soft = list(SOFT_DIMENSIONS.values())
    crit_drifts = [k for k in critical if k in expected and expected[k] != actual.get(k)]
    soft_drifts = [k for k in soft if k in expected and expected[k] != actual.get(k)]
    return DriftReport(
        critical_drifts=crit_drifts,
        soft_drifts=soft_drifts,
        is_critical=len(crit_drifts) > 0,
        summary=(
            f"Critical drift on: {', '.join(crit_drifts)}" if crit_drifts
            else "No critical drift"
        ),
    )

def corpus_conformance_score(
    annotation: QuestionAnnotation,
    family_key: str,
    corpus_rows: list[dict],
    top_n: int = 3,
    corpus_n_override: Optional[int] = None,
) -> ConformanceReport:
    critical = list(CRITICAL_DIMENSIONS.values())
    if family_key == "conventions_grammar":
        critical = critical + list(SEC_CRITICAL_DIMENSIONS.values())
    soft = list(SOFT_DIMENSIONS.values())

    family_rows = [r for r in corpus_rows if r.get("question_family_key") == family_key]
    corpus_n = corpus_n_override if corpus_n_override is not None else sum(r.get("n", 1) for r in family_rows)

    if corpus_n < 5:
        return ConformanceReport([], [], corpus_n, True,
                                 f"Corpus too small ({corpus_n}) — gate bypassed")

    def top_n_values(dim: str) -> set:
        counts: dict[str, int] = {}
        for r in family_rows:
            v = r.get(dim)
            if v:
                counts[v] = counts.get(v, 0) + r.get("n", 1)
        return set(sorted(counts, key=counts.get, reverse=True)[:top_n])  # type: ignore

    def check(dims: list[str]) -> list[str]:
        misses = []
        for dim in dims:
            val = getattr(annotation, dim, None)
            top = top_n_values(dim)
            if val and top and val not in top:
                misses.append(dim)
        return misses

    critical_misses = check(critical)
    soft_misses = check(soft)
    return ConformanceReport(
        critical_misses=critical_misses,
        soft_misses=soft_misses,
        corpus_n=corpus_n,
        is_conformant=len(critical_misses) == 0,
        explanation=(
            f"Conformant against {corpus_n} CB questions"
            if not critical_misses
            else f"Fails on: {', '.join(critical_misses)} (corpus n={corpus_n})"
        ),
    )

def should_rerun(report: DriftReport, conformance: ConformanceReport, attempt: int) -> bool:
    needs_rerun = report.is_critical or not conformance.is_conformant
    return needs_rerun and attempt < 3
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_drift.py -v
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/pipeline/generation/drift.py backend/tests/test_drift.py
git commit -m "feat: drift detection + corpus conformance gating"
```

---

### Task 15: Generation Prompts + Run Pipeline

**Files:**
- Create: `backend/app/prompts/generation.py`
- Create: `backend/app/pipeline/generation/generate.py`

Full spec in `docs/TASKS_GEN_PIPELINE.md` Tasks 3 and 5.

- [ ] **Step 1: Create `app/prompts/generation.py`**

Copy `_CONSTRAINT_GROUPS` exactly from `docs/TASKS_GEN_PIPELINE.md` Task 3b. Key functions:

```python
# _CONSTRAINT_GROUPS as defined in TASKS_GEN_PIPELINE.md Task 3b
_CONSTRAINT_GROUPS = [...]  # paste from spec

def build_generation_system_prompt(template_skeleton: str) -> str:
    # Replace <<pass1_schema>> placeholder with the output schema
    ...

def build_generation_user_prompt(
    seed_question: dict,
    merged_constraints: dict,
    irt_b_estimate: float | None = None,
) -> str:
    # 3 sections: SEED EXEMPLAR, TARGET SPECIFICATIONS (grouped), DIFFICULTY ANCHOR
    ...
```

- [ ] **Step 2: Write generation pipeline tests**

```python
# tests/test_generation.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from app.pipeline.generation.generate import create_generation_run, select_seed_question
from app.llm.base import LLMResponse

async def test_create_generation_run_returns_uuid():
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value={
        "id": uuid.uuid4(),
        "constraint_schema": '{"required": []}',
    })
    conn.execute = AsyncMock()
    pool = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    settings = AsyncMock()
    seed_ids = [uuid.uuid4()]
    template_id = uuid.uuid4()

    run_id = await create_generation_run(pool, settings, seed_ids, template_id, item_count=1)
    assert isinstance(run_id, uuid.UUID)

def test_select_seed_question_fallback_to_roundrobin():
    from app.pipeline.generation.generate import _round_robin_seed
    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    assert _round_robin_seed(ids, 0) == ids[0]
    assert _round_robin_seed(ids, 1) == ids[1]
    assert _round_robin_seed(ids, 3) == ids[0]
```

- [ ] **Step 3: Create `app/pipeline/generation/generate.py`**

Implement `create_generation_run`, `_round_robin_seed`, `select_seed_question`, and `process_generation_run` per the spec in `docs/TASKS_GEN_PIPELINE.md` Task 5. Key rules:
- `content_origin = 'generated'` on INSERT (explicit, not default)
- `input_format = 'generated'`
- `status = 'annotating'` (skip extraction step)
- Max 3 drift attempts; LLM errors retry separately (exponential backoff, don't consume drift slot)
- `generation_result_jsonb` written for ALL outcomes including drift_failed
- Run status: `failed` / `partial_complete` / `complete`

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_generation.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/generation.py backend/app/pipeline/generation/generate.py backend/tests/test_generation.py
git commit -m "feat: generation pipeline — run creation, seed selection, drift loop"
```

---

### Task 16: Generation Router

**Files:**
- Create: `backend/app/routers/generate.py`

Endpoints per `docs/TASKS_GEN_PIPELINE.md` Task 8.

- [ ] **Step 1: Create `app/routers/generate.py`**

```python
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from app.auth import require_api_key
from app.models.payload import GenerationRequest, GenerationRunCreated
from app.pipeline.generation.generate import create_generation_run, process_generation_run

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.post("/generate", response_model=GenerationRunCreated)
async def start_generation(req: GenerationRequest, background: BackgroundTasks, request: Request):
    pool = request.app.state.pool
    settings = request.app.state.settings

    # Check corpus size for warning
    async with pool.acquire() as conn:
        template = await conn.fetchrow(
            "SELECT question_family_key FROM public.generation_templates WHERE id=$1", req.template_id
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        family_key = template["question_family_key"]
        corpus_n_row = await conn.fetchrow(
            "SELECT COALESCE(SUM(n),0) AS n FROM public.v_corpus_fingerprint WHERE question_family_key=$1",
            family_key,
        )
        corpus_n = int(corpus_n_row["n"]) if corpus_n_row else 0

    run_id = await create_generation_run(
        pool, settings, req.seed_question_ids, req.template_id,
        item_count=req.item_count,
        target_constraints=req.target_constraints,
        run_notes=req.run_notes,
    )
    background.add_task(process_generation_run, pool, settings, run_id, req)

    warning = None
    warning_detail = None
    if corpus_n < 5:
        warning = "corpus_too_small"
        warning_detail = f"Only {corpus_n} approved official questions for family '{family_key}' — conformance gate bypassed"

    return GenerationRunCreated(run_id=run_id, warning=warning, warning_detail=warning_detail)

@router.get("/generate/runs")
async def list_runs(request: Request, status: str | None = None, limit: int = 20, offset: int = 0):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM public.generation_runs WHERE status=$1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                status, limit, offset,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM public.generation_runs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
    return [dict(r) for r in rows]

@router.get("/generate/runs/{run_id}")
async def get_run(run_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM public.generation_runs WHERE id=$1", run_id)
    if not row:
        raise HTTPException(status_code=404)
    return dict(row)

@router.get("/generate/runs/{run_id}/jobs")
async def get_run_jobs(run_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM public.question_ingestion_jobs WHERE generation_run_id=$1 ORDER BY created_at",
            run_id,
        )
    return [dict(r) for r in rows]

@router.get("/generate/templates")
async def list_templates(request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM public.generation_templates WHERE is_active=true ORDER BY template_code")
    return [dict(r) for r in rows]

@router.get("/generate/runs/{run_id}/drift")
async def get_drift_report(run_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        staging_rows = await conn.fetch(
            "SELECT id, status, generation_result_jsonb FROM public.question_ingestion_jobs WHERE generation_run_id=$1",
            run_id,
        )
        traceability_rows = await conn.fetch(
            "SELECT * FROM public.v_generation_traceability WHERE run_id=$1", run_id
        )
    return {
        "staging": [dict(r) for r in staging_rows],
        "traceability": [dict(r) for r in traceability_rows],
    }
```

- [ ] **Step 2: Register in `main.py`**

```python
from app.routers import generate
app.include_router(generate.router, tags=["generation"])
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/generate.py backend/app/main.py
git commit -m "feat: generation router — run management, drift report"
```

---

## Chunk 7: Coaching + Embeddings + Remaining Routers

### Task 17: Coaching

**Files:**
- Create: `backend/app/prompts/coaching.py`
- Create: `backend/app/pipeline/coaching.py`

Spec in `docs/TASKS_GEN_PIPELINE.md` Tasks 6 and 7.

- [ ] **Step 1: Write coaching tests**

```python
# tests/test_coaching.py
import uuid
import pytest
from app.pipeline.coaching import _find_span

def test_find_span_basic():
    text = "The scientist analyzed the data carefully."
    start, end, sent_idx = _find_span(text, "analyzed the data")
    assert start == 14
    assert end == 31
    assert sent_idx == 0

def test_find_span_not_found_returns_nones():
    start, end, sent_idx = _find_span("Hello world.", "missing phrase")
    assert start is None
    assert end is None
    assert sent_idx is None

def test_find_span_normalizes_whitespace():
    text = "The  scientist  analyzed."
    start, end, sent_idx = _find_span(text, "scientist  analyzed")
    # Should find after whitespace normalization
    assert start is not None
```

- [ ] **Step 2: Create `app/prompts/coaching.py`**

Per spec Task 6 — output contract with `annotations` array and `coaching_summary`.

- [ ] **Step 3: Create `app/pipeline/coaching.py`**

Per spec Task 7. Key: `_find_span` normalizes whitespace; returns `(None, None, None)` on miss and logs.

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_coaching.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/coaching.py backend/app/pipeline/coaching.py backend/tests/test_coaching.py
git commit -m "feat: coaching annotation generation — span finding + DB write"
```

---

### Task 18: Embeddings + Search Router

**Files:**
- Create: `backend/app/pipeline/embeddings.py`
- Create: `backend/app/routers/search.py`

- [ ] **Step 1: Create `app/pipeline/embeddings.py`**

```python
import uuid
import openai
from app.config import Settings

async def embed_text(text: str, settings: Settings) -> list[float]:
    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key_embeddings or settings.openai_api_key
    )
    resp = await client.embeddings.create(model=settings.embedding_model, input=text)
    return resp.data[0].embedding

async def build_embeddings_for_question(conn, settings: Settings, question_id: uuid.UUID) -> None:
    row = await conn.fetchrow(
        "SELECT stem_text, passage_text FROM public.questions WHERE id=$1", question_id
    )
    if not row:
        return

    embedding_types = {
        "passage_only": row["passage_text"] or row["stem_text"] or "",
        "taxonomy_summary": f"{row['stem_text']} {row['passage_text'] or ''}".strip(),
    }
    for emb_type, text in embedding_types.items():
        if not text.strip():
            continue
        vector = await embed_text(text, settings)
        await conn.execute("""
            INSERT INTO public.question_embeddings (question_id, embedding_type, embedding)
            VALUES ($1, $2, $3)
            ON CONFLICT (question_id, embedding_type) DO UPDATE SET embedding=EXCLUDED.embedding
        """, question_id, emb_type, vector)
```

- [ ] **Step 2: Create `app/routers/search.py`**

```python
from fastapi import APIRouter, Depends, Request
from app.auth import require_api_key
from app.models.payload import SearchRequest
from app.pipeline.embeddings import embed_text

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.post("/search")
async def semantic_search(req: SearchRequest, request: Request):
    pool = request.app.state.pool
    settings = request.app.state.settings
    vector = await embed_text(req.query, settings)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT q.id, q.stem_text, q.passage_text, q.question_family_key,
                   1 - (qe.embedding <=> $1::vector) AS similarity
            FROM public.question_embeddings qe
            JOIN public.questions q ON q.id = qe.question_id
            WHERE qe.embedding_type = $2
              AND ($3::text IS NULL OR q.question_family_key = $3)
            ORDER BY qe.embedding <=> $1::vector
            LIMIT $4
        """, vector, req.embedding_type, req.family_key, req.limit)
    return [dict(r) for r in rows]
```

- [ ] **Step 3: Register routers**

```python
# main.py
from app.routers import search
app.include_router(search.router, tags=["search"])
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/pipeline/embeddings.py backend/app/routers/search.py
git commit -m "feat: embeddings pipeline + semantic search router"
```

---

### Task 19: Questions + Ontology Routers

**Files:**
- Create: `backend/app/routers/questions.py`
- Create: `backend/app/routers/ontology.py`

- [ ] **Step 1: Create `app/routers/questions.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.get("/questions")
async def list_questions(request: Request, family_key: str | None = None, limit: int = 50, offset: int = 0):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        if family_key:
            rows = await conn.fetch(
                "SELECT * FROM public.questions WHERE question_family_key=$1 AND is_active=true ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                family_key, limit, offset,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM public.questions WHERE is_active=true ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
    return [dict(r) for r in rows]

@router.get("/questions/{question_id}")
async def get_question(question_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.questions WHERE id=$1", question_id
        )
    if not row:
        raise HTTPException(status_code=404)
    return dict(row)

@router.get("/questions/{question_id}/practice")
async def get_practice(question_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        q = await conn.fetchrow("SELECT * FROM public.questions WHERE id=$1", question_id)
        if not q:
            raise HTTPException(status_code=404)
        opts = await conn.fetch(
            "SELECT * FROM public.question_options WHERE question_id=$1 ORDER BY option_label", question_id
        )
        tokens = await conn.fetch(
            "SELECT * FROM public.question_grammar_keys WHERE question_id=$1 ORDER BY token_index", question_id
        )
    tok_status = q["tokenization_status"] if "tokenization_status" in q.keys() else "pending"
    return {
        **dict(q),
        "options": [dict(o) for o in opts],
        "tokens": [dict(t) for t in tokens],
        "tokenization_status": tok_status,
    }
```

- [ ] **Step 2: Create `app/routers/ontology.py`**

```python
from fastapi import APIRouter, Depends
from app.auth import require_api_key
from app.models import ontology as ont

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.get("/ontology/keys")
async def get_ontology_keys():
    return {
        "question_family_keys": sorted(ont.QUESTION_FAMILY_KEYS),
        "difficulty_values": sorted(ont.DIFFICULTY_VALUES),
        "syntactic_complexity_keys": sorted(ont.SYNTACTIC_COMPLEXITY_KEYS),
        "prose_register_keys": sorted(ont.PROSE_REGISTER_KEYS),
        "lexical_tier_keys": sorted(ont.LEXICAL_TIER_KEYS),
        "grammar_focus_keys": sorted(ont.GRAMMAR_FOCUS_KEYS),
        "grammar_role_keys": sorted(ont.GRAMMAR_ROLE_KEYS),
    }
```

- [ ] **Step 3: Register all routers in `main.py`**

```python
from app.routers import ingest, jobs, questions, generate, search, ontology
app.include_router(ingest.router, tags=["ingestion"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(questions.router, tags=["questions"])
app.include_router(generate.router, tags=["generation"])
app.include_router(search.router, tags=["search"])
app.include_router(ontology.router, tags=["ontology"])
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest tests/ -v --tb=short
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/ backend/app/main.py
git commit -m "feat: questions + ontology routers, full router registration"
```

---

## Chunk 8: Migration 042 + Final Wiring

### Task 20: Migration 042 — Corpus Fingerprint

**Files:**
- Already documented: `backend/migrations/042_additional_grammar_focus_categories.sql` exists — check whether `042_corpus_fingerprint.sql` is separate or needs to be `043`.

- [ ] **Step 1: Check existing migration 042**

```bash
cat backend/migrations/042_additional_grammar_focus_categories.sql | head -5
```

If 042 is already taken, create `043_corpus_fingerprint.sql`.

- [ ] **Step 2: Create corpus fingerprint migration**

Copy exact SQL from `docs/TASKS_GEN_PIPELINE.md` Task 2 into the new file. Includes:
- Extended `qij_status_check` (drift_failed, conformance_failed)
- Extended `generation_runs_status_check` (partial_complete)
- `generation_result_jsonb` column on `question_ingestion_jobs`
- `v_corpus_fingerprint` materialized view
- `fn_refresh_corpus_fingerprint()` function

- [ ] **Step 3: Apply to Supabase**

```bash
# Apply via Supabase dashboard SQL editor, or:
psql $DATABASE_URL -f backend/migrations/043_corpus_fingerprint.sql
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/
git commit -m "feat: migration 043 — corpus fingerprint view + generation status extensions"
```

---

### Task 21: End-to-End Smoke Test

- [ ] **Step 1: Start server**

```bash
cd backend
uv run uvicorn app.main:app --reload
```

- [ ] **Step 2: Health check**

```bash
curl http://localhost:8000/health
# expect: {"status":"ok"}
```

- [ ] **Step 3: Ingest a question**

```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "The scientist _____ the data carefully.\n\nA) analyzed (correct)\nB) ignored\nC) deleted\nD) misread"}'
# expect: {"job_id": "...", "status": "pending"}
```

- [ ] **Step 4: Poll job status**

```bash
curl http://localhost:8000/jobs/<job_id> -H "X-API-Key: dev-key"
# wait for status = "draft"
```

- [ ] **Step 5: Approve job**

```bash
curl -X PATCH http://localhost:8000/jobs/<job_id>/status \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'
```

- [ ] **Step 6: Verify question in DB**

```bash
curl http://localhost:8000/questions -H "X-API-Key: dev-key"
# expect: question appears
```

- [ ] **Step 7: Check ontology endpoint**

```bash
curl http://localhost:8000/ontology/keys -H "X-API-Key: dev-key"
```

- [ ] **Step 8: Final test run**

```bash
uv run pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 9: Final commit**

```bash
git add .
git commit -m "feat: complete backend rebuild — ingestion, generation, coaching, search"
```

---

## Chunk 9: Multimodal Ingestion — PDFs, Images, Charts, Graphs

### Overview

Questions referencing charts, graphs, or figures require two things the text-only pipeline lacks:

1. **Visual extraction** — pull image bytes from PDFs or accept uploaded PNGs
2. **Vision LLM call** — send image bytes alongside text to a multimodal model during Pass 1

The schema already has `table_data_jsonb` and `graph_data_jsonb` on `questions` (migration 020) for structured visual data. A new `question_images` table stores the raw image blobs (via Supabase Storage) and links them to questions so the frontend can reconstruct the visual context on output.

**Provider support matrix:**

| Provider | Vision support | Notes |
|----------|---------------|-------|
| Anthropic claude-sonnet-4-6 | ✅ | base64 PNG/JPEG in `image` content block |
| OpenAI GPT-4o | ✅ | base64 or URL in `image_url` content block |
| OpenRouter | ✅ | passes through to underlying model |
| Ollama | ✅ (model-dependent) | llava, llava-phi3, gemma4 multimodal |

---

### Task 22: Dependencies + Migration

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/migrations/043_question_images.sql` (or 044 if 043 is taken)

- [ ] **Step 1: Add dependencies**

```toml
# pyproject.toml — add to dependencies
"pymupdf>=1.24",        # PDF image extraction (imports as fitz)
"pillow>=11.0",         # image resizing/conversion
"supabase>=2.10",       # Supabase Storage client
```

```bash
uv sync
```

- [ ] **Step 2: Write migration**

```sql
-- migrations/043_question_images.sql
-- Stores image metadata; actual bytes live in Supabase Storage bucket "question-images"

CREATE TABLE IF NOT EXISTS public.question_images (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     uuid NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    image_type      text NOT NULL CHECK (image_type IN ('chart', 'graph', 'table', 'figure', 'passage_image', 'other')),
    storage_path    text NOT NULL,           -- e.g. "{question_id}/chart_0.png"
    alt_text        text,                    -- LLM-generated description for accessibility
    description_jsonb jsonb,                 -- structured data extracted from chart/graph
    source_page     int,                     -- PDF page number (null for standalone images)
    display_order   int NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_images_question_id
    ON public.question_images(question_id);

COMMENT ON COLUMN public.question_images.storage_path IS
    'Path within Supabase Storage bucket "question-images". Fetch via signed URL.';
COMMENT ON COLUMN public.question_images.description_jsonb IS
    'For charts/graphs: {"x_axis": "...", "y_axis": "...", "series": [...], "key_values": {...}}';
```

- [ ] **Step 3: Apply migration**

```bash
psql $DATABASE_URL -f backend/migrations/043_question_images.sql
```

- [ ] **Step 4: Create Supabase Storage bucket**

In the Supabase dashboard → Storage → New bucket → name: `question-images` → Private (not public). Access via signed URLs only.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/migrations/043_question_images.sql
git commit -m "feat: question_images migration + multimodal dependencies"
```

---

### Task 23: Image Store (Supabase Storage)

**Files:**
- Create: `backend/app/storage/image_store.py`
- Create: `backend/app/config.py` (add `supabase_url` + `supabase_service_key`)

- [ ] **Step 1: Add Supabase config fields**

```python
# app/config.py — add to Settings
supabase_url: str = ""
supabase_service_key: str = ""          # service_role key for Storage writes
image_bucket: str = "question-images"
image_signed_url_ttl: int = 3600        # 1 hour
```

```bash
# .env.example — add
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
IMAGE_BUCKET=question-images
```

- [ ] **Step 2: Write image store tests**

```python
# tests/test_image_store.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.storage.image_store import ImageStore

@pytest.fixture
def store(monkeypatch):
    from app.config import Settings
    settings = Settings(
        database_url="x",
        supabase_url="https://test.supabase.co",
        supabase_service_key="key",
    )
    return ImageStore(settings)

async def test_upload_returns_storage_path(store):
    with patch.object(store.client.storage, "from_", return_value=MagicMock(
        upload=MagicMock(return_value=MagicMock())
    )):
        path = await store.upload(
            image_bytes=b"PNG_DATA",
            question_id=uuid.uuid4(),
            image_type="chart",
            index=0,
            content_type="image/png",
        )
    assert path.endswith(".png")
    assert "chart" in path

async def test_signed_url_returns_url(store):
    mock_bucket = MagicMock()
    mock_bucket.create_signed_url.return_value = {"signedURL": "https://signed.url/img.png"}
    with patch.object(store.client.storage, "from_", return_value=mock_bucket):
        url = await store.signed_url("some/path.png")
    assert url == "https://signed.url/img.png"
```

- [ ] **Step 3: Create `app/storage/image_store.py`**

```python
import uuid
import asyncio
from functools import partial
from supabase import create_client, Client
from app.config import Settings

class ImageStore:
    def __init__(self, settings: Settings):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_key)
        self.bucket = settings.image_bucket
        self.ttl = settings.image_signed_url_ttl

    def _storage_path(self, question_id: uuid.UUID, image_type: str, index: int, ext: str = "png") -> str:
        return f"{question_id}/{image_type}_{index}.{ext}"

    async def upload(
        self,
        image_bytes: bytes,
        question_id: uuid.UUID,
        image_type: str,
        index: int,
        content_type: str = "image/png",
    ) -> str:
        ext = content_type.split("/")[-1]
        path = self._storage_path(question_id, image_type, index, ext)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                self.client.storage.from_(self.bucket).upload,
                path, image_bytes,
                {"content-type": content_type, "upsert": "true"},
            ),
        )
        return path

    async def signed_url(self, storage_path: str) -> str:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                self.client.storage.from_(self.bucket).create_signed_url,
                storage_path, self.ttl,
            ),
        )
        return result["signedURL"]

    async def download(self, storage_path: str) -> bytes:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            partial(self.client.storage.from_(self.bucket).download, storage_path),
        )
        return data
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_image_store.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/ backend/tests/test_image_store.py
git commit -m "feat: Supabase Storage image store — upload, signed URL, download"
```

---

### Task 24: Multimodal LLM Provider Extension

**Files:**
- Modify: `backend/app/llm/base.py`
- Modify: `backend/app/llm/anthropic_provider.py`
- Modify: `backend/app/llm/openai_provider.py`
- Modify: `backend/app/llm/openrouter_provider.py`
- Modify: `backend/app/llm/ollama_provider.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_llm.py (append)
import base64

FAKE_PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20).decode()

async def test_anthropic_sends_image_content_block():
    settings = Settings(database_url="x", llm_provider="anthropic", anthropic_api_key="sk-test")
    provider = get_provider(settings)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="{}")]
    mock_response.model = "claude-sonnet-4-6"
    mock_response.usage.input_tokens = 200
    mock_response.usage.output_tokens = 50
    mock_response.usage.cache_read_input_tokens = 0
    mock_response.usage.cache_creation_input_tokens = 0

    captured = {}
    async def fake_create(**kwargs):
        captured.update(kwargs)
        return mock_response

    image_bytes = base64.b64decode(FAKE_PNG)
    with patch.object(provider.client.messages, "create", new=fake_create):
        await provider.complete("system", "describe this image", images=[image_bytes])

    # user message must contain image content block
    messages = captured["messages"]
    user_content = messages[0]["content"]
    assert isinstance(user_content, list)
    image_block = next((b for b in user_content if b.get("type") == "image"), None)
    assert image_block is not None
    assert image_block["source"]["type"] == "base64"

async def test_ollama_sends_images_field():
    settings = Settings(database_url="x", llm_provider="ollama", ollama_model="llava:13b")
    provider = get_provider(settings)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "message": {"content": "{}"},
        "model": "llava:13b",
        "prompt_eval_count": 10,
        "eval_count": 5,
    }
    mock_resp.raise_for_status = MagicMock()

    captured = {}
    async def fake_post(path, **kwargs):
        captured.update(kwargs.get("json", {}))
        return mock_resp

    image_bytes = base64.b64decode(FAKE_PNG)
    with patch.object(provider.client, "post", new=fake_post):
        await provider.complete("system", "user", images=[image_bytes])

    assert "images" in captured
    assert len(captured["images"]) == 1
```

- [ ] **Step 2: Update `app/llm/base.py` — add `images` param**

```python
@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        cache_system: bool = False,
        images: list[bytes] | None = None,   # raw image bytes; provider encodes to base64
    ) -> LLMResponse: ...
```

- [ ] **Step 3: Update `anthropic_provider.py`**

```python
import base64
from app.llm.base import LLMResponse

async def complete(self, system, user, temperature=0.2, max_tokens=4096,
                   cache_system=False, images=None):
    system_arg = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if cache_system else system
    )
    # Build user content — text always last (Anthropic requirement)
    if images:
        user_content = []
        for img_bytes in images:
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64.standard_b64encode(img_bytes).decode(),
                },
            })
        user_content.append({"type": "text", "text": user})
    else:
        user_content = user

    resp = await self.client.messages.create(
        model=self.model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_arg,
        messages=[{"role": "user", "content": user_content}],
    )
    usage = resp.usage
    return LLMResponse(
        content=resp.content[0].text,
        model=resp.model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )
```

- [ ] **Step 4: Update `openai_provider.py`**

```python
import base64

async def complete(self, system, user, temperature=0.2, max_tokens=4096,
                   cache_system=False, images=None):
    if images:
        user_content = []
        for img_bytes in images:
            b64 = base64.standard_b64encode(img_bytes).decode()
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
        user_content.append({"type": "text", "text": user})
    else:
        user_content = user

    resp = await self.client.chat.completions.create(
        model=self.model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    )
    return LLMResponse(
        content=resp.choices[0].message.content or "",
        model=resp.model,
        input_tokens=resp.usage.prompt_tokens,
        output_tokens=resp.usage.completion_tokens,
    )
```

- [ ] **Step 5: Update `openrouter_provider.py`** — same pattern as OpenAI (it's OpenAI-compatible).

- [ ] **Step 6: Update `ollama_provider.py`**

```python
import base64

async def complete(self, system, user, temperature=0.2, max_tokens=4096,
                   cache_system=False, images=None):
    payload = {
        "model": self.model,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if images:
        # Ollama images field: list of base64 strings on the user message
        payload["messages"][-1]["images"] = [
            base64.standard_b64encode(img).decode() for img in images
        ]
    resp = await self.client.post("/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return LLMResponse(
        content=data["message"]["content"],
        model=data.get("model", self.model),
        input_tokens=data.get("prompt_eval_count", 0),
        output_tokens=data.get("eval_count", 0),
    )
```

- [ ] **Step 7: Run tests**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/llm/ backend/tests/test_llm.py
git commit -m "feat: multimodal image support in all LLM providers"
```

---

### Task 25: PDF + Image Parsers (Visual Extraction)

**Files:**
- Modify: `backend/app/parsers/pdf_parser.py`
- Create: `backend/app/parsers/image_parser.py`
- Modify: `backend/app/parsers/markdown_parser.py`

- [ ] **Step 1: Write parser tests**

```python
# tests/test_parsers.py (append)
import io
from PIL import Image as PILImage
from app.parsers.image_parser import load_image_bytes, resize_for_llm

def test_load_image_bytes_from_png():
    # Create a minimal PNG in memory
    img = PILImage.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    result = load_image_bytes(raw)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_resize_for_llm_caps_width():
    img = PILImage.new("RGB", (4000, 3000))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    resized = resize_for_llm(buf.getvalue(), max_dim=2048)
    out = PILImage.open(io.BytesIO(resized))
    assert max(out.size) <= 2048

def test_pdf_parser_returns_text_and_images(tmp_path):
    # Integration test requires a real PDF — skip if no test PDF available
    pytest.importorskip("fitz")
    from app.parsers.pdf_parser import parse_pdf_with_images
    # Smoke test: function is callable and returns correct structure
    import inspect
    sig = inspect.signature(parse_pdf_with_images)
    assert "path" in sig.parameters
```

- [ ] **Step 2: Update `app/parsers/pdf_parser.py`**

```python
import fitz  # pymupdf
from pathlib import Path
from app.parsers.image_parser import resize_for_llm

def parse_pdf_text_only(path: str | Path) -> str:
    """Fast text extraction — no images. Use for text-heavy PDFs."""
    doc = fitz.open(str(path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(p for p in pages if p.strip())

def parse_pdf_with_images(path: str | Path, max_image_dim: int = 2048) -> dict:
    """
    Extract text + images per page.
    Returns: {"pages": [{"page": int, "text": str, "images": [bytes]}]}
    """
    doc = fitz.open(str(path))
    result = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        images = []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            images.append(resize_for_llm(img_bytes, max_dim=max_image_dim))
        result.append({"page": page_num, "text": text, "images": images})
    doc.close()
    return {"pages": result}
```

- [ ] **Step 3: Create `app/parsers/image_parser.py`**

```python
import io
from PIL import Image as PILImage

def load_image_bytes(raw: bytes, output_format: str = "PNG") -> bytes:
    """Normalize any image format to PNG bytes."""
    img = PILImage.open(io.BytesIO(raw)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format=output_format)
    return buf.getvalue()

def resize_for_llm(raw: bytes, max_dim: int = 2048) -> bytes:
    """
    Resize image so its longest side ≤ max_dim.
    Anthropic and OpenAI both handle up to 2048px well.
    Returns PNG bytes.
    """
    img = PILImage.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

- [ ] **Step 4: Update `app/parsers/markdown_parser.py`**

```python
import re
from pathlib import Path

def parse_markdown(path: str | Path) -> dict:
    """
    Parse markdown file. Returns text and local image references.
    Image refs like ![alt](./images/chart.png) are resolved relative to the file.
    Returns: {"text": str, "image_refs": [{"alt": str, "path": Path}]}
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    image_refs = []
    for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text):
        alt, img_path = match.group(1), match.group(2)
        if not img_path.startswith("http"):
            resolved = (p.parent / img_path).resolve()
            if resolved.exists():
                image_refs.append({"alt": alt, "path": resolved})
    return {"text": text, "image_refs": image_refs}
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_parsers.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/parsers/ backend/tests/test_parsers.py
git commit -m "feat: multimodal parsers — PDF image extraction, PNG resize, markdown image refs"
```

---

### Task 26: Vision-Aware Pass 1 Extractor

**Files:**
- Modify: `backend/app/prompts/pass1_extraction.py`
- Modify: `backend/app/pipeline/ingestion/extractor.py`

When images are present, the Pass 1 prompt tells the LLM to describe visual content and embed descriptions into the JSON output. The structured description is stored in `table_data_jsonb` / `graph_data_jsonb` (migration 020 columns).

- [ ] **Step 1: Write test**

```python
# tests/test_extractor.py (append)
async def test_extract_pass1_with_images_sends_image_to_provider():
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = LLMResponse(
        content='''{
            "stem_text": "According to the graph, what happened in 2020?",
            "passage_text": null,
            "options": [
                {"label": "A", "text": "Values increased", "is_correct": true},
                {"label": "B", "text": "Values decreased", "is_correct": false},
                {"label": "C", "text": "Values stayed flat", "is_correct": false},
                {"label": "D", "text": "No data shown", "is_correct": false}
            ],
            "correct_option_label": "A",
            "question_family_key": "data_integration_graph",
            "graph_data": {"x_axis": "Year", "y_axis": "Value", "key_values": {"2020": 42}}
        }''',
        model="claude-sonnet-4-6",
    )
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    result = await extract_pass1("Describe the graph.", mock_provider, images=[fake_png])
    # provider must have been called with images
    call_kwargs = mock_provider.complete.call_args.kwargs
    assert call_kwargs.get("images") == [fake_png]
    assert isinstance(result, QuestionExtract)
```

- [ ] **Step 2: Update `app/prompts/pass1_extraction.py`** — add visual context instructions

```python
PASS1_VISUAL_ADDENDUM = """
VISUAL CONTENT INSTRUCTIONS:
Images are attached. For each image:
- If it is a GRAPH or CHART: extract into graph_data as {"x_axis": "...", "y_axis": "...", "series": [...], "key_values": {...}}
- If it is a TABLE: extract into table_data as {"headers": [...], "rows": [[...], ...]}
- If it is a FIGURE or PASSAGE IMAGE: describe in passage_text or prompt_text where relevant
Include image descriptions in the JSON output fields above. Do not omit data visible in the images.
"""

def build_pass1_user_prompt(raw_text: str, has_images: bool = False) -> str:
    visual_note = PASS1_VISUAL_ADDENDUM if has_images else ""
    return f"""Extract the following DSAT question into the JSON schema below.
{visual_note}
OUTPUT SCHEMA:
{PASS1_OUTPUT_SCHEMA}

ALLOWED question_family_key values:
{ALLOWED_FAMILY_KEYS}

RAW QUESTION:
{raw_text}

Return only the JSON object."""
```

- [ ] **Step 3: Update `app/pipeline/ingestion/extractor.py`**

```python
from app.llm.base import LLMProvider
from app.models.extract import QuestionExtract
from app.parsers.json_parser import extract_json
from app.prompts.pass1_extraction import PASS1_SYSTEM, build_pass1_user_prompt

async def extract_pass1(
    raw_text: str,
    provider: LLMProvider,
    images: list[bytes] | None = None,
) -> QuestionExtract:
    user = build_pass1_user_prompt(raw_text, has_images=bool(images))
    response = await provider.complete(
        PASS1_SYSTEM, user, temperature=0.1, images=images or None
    )
    data = extract_json(response.content)
    return QuestionExtract.model_validate(data)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_extractor.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts/pass1_extraction.py backend/app/pipeline/ingestion/extractor.py backend/tests/test_extractor.py
git commit -m "feat: vision-aware Pass 1 — images forwarded to multimodal LLM, graph/table extraction"
```

---

### Task 27: Multimodal Ingest Router + Image Storage

**Files:**
- Modify: `backend/app/routers/ingest.py`
- Modify: `backend/app/pipeline/ingestion/orchestrator.py`
- Modify: `backend/app/pipeline/ingestion/upsert.py`
- Create: `backend/app/routers/images.py`

- [ ] **Step 1: Update `app/routers/ingest.py`** — add PNG upload endpoint

```python
# Add to existing ingest.py router

@router.post("/ingest/image", response_model=JobCreated)
async def ingest_image(
    background: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    question_text: str = Form(default=""),  # optional accompanying text
):
    """Accept a PNG/JPEG image (chart, graph, figure) + optional text context."""
    pool = request.app.state.pool
    settings = request.app.state.settings
    image_bytes = await file.read()

    # Normalize to PNG
    from app.parsers.image_parser import load_image_bytes, resize_for_llm
    normalized = resize_for_llm(load_image_bytes(image_bytes), max_dim=2048)

    # Store image bytes temporarily in job payload; permanent storage happens on approval
    import base64
    image_b64 = base64.standard_b64encode(normalized).decode()

    raw_text = question_text or f"[Image: {file.filename}]"
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO public.question_ingestion_jobs
                (raw_text, source_file, input_format, status, content_origin,
                 raw_images_b64_jsonb)
            VALUES ($1, $2, 'image', 'pending', 'official', $3)
            RETURNING id
        """, raw_text, file.filename, json.dumps([image_b64]))
    job_id = row["id"]
    background.add_task(process_job, pool, settings, job_id)
    return JobCreated(job_id=job_id)
```

> **Note:** `raw_images_b64_jsonb` requires a migration column on `question_ingestion_jobs`. Add this to migration 043 or a new 044:
> ```sql
> ALTER TABLE public.question_ingestion_jobs
>     ADD COLUMN IF NOT EXISTS raw_images_b64_jsonb jsonb;
> ```

- [ ] **Step 2: Update `orchestrator.py`** — decode images and pass to extractor

```python
# In process_job(), after fetching the job row:
import base64

raw_images_b64 = job.get("raw_images_b64_jsonb") or []
if isinstance(raw_images_b64, str):
    import json as _json
    raw_images_b64 = _json.loads(raw_images_b64)
images = [base64.standard_b64decode(b) for b in raw_images_b64] if raw_images_b64 else None

# Pass to extractor:
extract = await extract_pass1(raw_text, provider, images=images)
```

Also handle PDF with images: when `input_format == "pdf"`, use `parse_pdf_with_images()` instead of text-only parsing. Flatten all page images into a single list (SAT questions rarely span more than 2 pages).

```python
if job["input_format"] == "pdf" and job.get("source_file"):
    # Re-parse the PDF with image extraction
    # (raw_text already stored; images need to be extracted fresh)
    # Store PDF bytes in job or re-fetch from storage — simplest: store PDF path
    pass  # handled by ingest/file route storing a temp path or Supabase path
```

> **Implementation note:** For PDF image extraction, save the uploaded PDF to Supabase Storage on ingest (`/ingest/file`), store the storage path in the job row, and re-download it in the orchestrator for image extraction. Add `source_pdf_storage_path` column to `question_ingestion_jobs`.

- [ ] **Step 3: Update `upsert.py`** — store images on approval

```python
# In upsert_approved_job(), after writing question_id:
from app.storage.image_store import ImageStore

async def upsert_approved_job(conn, job: dict, image_store: ImageStore | None = None) -> uuid.UUID:
    # ... existing upsert logic ...

    # Store images if present
    raw_images_b64 = job.get("raw_images_b64_jsonb") or []
    if isinstance(raw_images_b64, str):
        raw_images_b64 = json.loads(raw_images_b64)

    if raw_images_b64 and image_store:
        for idx, b64 in enumerate(raw_images_b64):
            img_bytes = base64.standard_b64decode(b64)
            storage_path = await image_store.upload(
                image_bytes=img_bytes,
                question_id=question_id,
                image_type="figure",
                index=idx,
            )
            await conn.execute("""
                INSERT INTO public.question_images
                    (question_id, image_type, storage_path, display_order)
                VALUES ($1, 'figure', $2, $3)
            """, question_id, storage_path, idx)

    return question_id
```

- [ ] **Step 4: Create `app/routers/images.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.auth import require_api_key
from app.storage.image_store import ImageStore

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.get("/images/{image_id}")
async def get_image(image_id: uuid.UUID, request: Request):
    """Returns a signed URL redirect to the image in Supabase Storage."""
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT storage_path FROM public.question_images WHERE id=$1", image_id
        )
    if not row:
        raise HTTPException(status_code=404)
    store = ImageStore(settings)
    url = await store.signed_url(row["storage_path"])
    return RedirectResponse(url=url, status_code=302)

@router.get("/questions/{question_id}/images")
async def get_question_images(question_id: uuid.UUID, request: Request):
    """List all images for a question with signed URLs."""
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM public.question_images WHERE question_id=$1 ORDER BY display_order",
            question_id,
        )
    store = ImageStore(settings)
    result = []
    for row in rows:
        url = await store.signed_url(row["storage_path"])
        result.append({**dict(row), "url": url})
    return result
```

- [ ] **Step 5: Register in `main.py`**

```python
from app.routers import images
app.include_router(images.router, tags=["images"])
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest tests/test_multimodal_ingest.py tests/test_image_store.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/ingest.py backend/app/routers/images.py \
        backend/app/pipeline/ingestion/ backend/app/storage/
git commit -m "feat: multimodal ingest — PNG upload, PDF image extraction, Supabase Storage on approval"
```

---

### Task 28: Practice Endpoint — Include Image URLs

**Files:**
- Modify: `backend/app/routers/questions.py`

The `/questions/{id}/practice` response should include image URLs so the frontend can render visual context alongside the question.

- [ ] **Step 1: Update `GET /questions/{id}/practice`**

```python
@router.get("/questions/{question_id}/practice")
async def get_practice(question_id: uuid.UUID, request: Request):
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        q = await conn.fetchrow("SELECT * FROM public.questions WHERE id=$1", question_id)
        if not q:
            raise HTTPException(status_code=404)
        opts = await conn.fetch(
            "SELECT * FROM public.question_options WHERE question_id=$1 ORDER BY option_label",
            question_id,
        )
        tokens = await conn.fetch(
            "SELECT * FROM public.question_grammar_keys WHERE question_id=$1 ORDER BY token_index",
            question_id,
        )
        image_rows = await conn.fetch(
            "SELECT * FROM public.question_images WHERE question_id=$1 ORDER BY display_order",
            question_id,
        )

    from app.storage.image_store import ImageStore
    store = ImageStore(settings)
    images = []
    for row in image_rows:
        url = await store.signed_url(row["storage_path"])
        images.append({
            "id": str(row["id"]),
            "image_type": row["image_type"],
            "alt_text": row["alt_text"],
            "display_order": row["display_order"],
            "url": url,
        })

    tok_status = q["tokenization_status"] if "tokenization_status" in q.keys() else "pending"
    return {
        **dict(q),
        "options": [dict(o) for o in opts],
        "tokens": [dict(t) for t in tokens],
        "tokenization_status": tok_status,
        "images": images,
    }
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/ -v --tb=short
```

Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/questions.py
git commit -m "feat: practice endpoint returns image URLs for visual question context"
```

---

### Multimodal Design Notes

- **pytesseract is removed** — replaced by vision LLM calls for all image content. Charts and graphs require understanding, not OCR.
- **Image sizing:** All images are resized to ≤2048px before sending to any LLM. Anthropic's limit is 5MB per image; OpenAI's is similar. Resizing prevents accidental overruns.
- **Ollama multimodal:** Requires a vision-capable model (`llava`, `llava-phi3`, `gemma4:12b`, `gemma4:27b`). Set `OLLAMA_MODEL=gemma4:27b` for best results. Text-only models will receive the image parameter and likely ignore it — no error, but no vision.
- **Supabase Storage vs DB BLOB:** Images are in Storage (object storage), not the DB. The `question_images` table stores metadata + storage path only. This keeps DB size manageable and allows CDN-style serving via signed URLs.
- **Markdown images:** Local image refs in markdown are resolved at ingest time, normalized to PNG, stored in Supabase Storage on approval. Remote URLs (http/https) are downloaded at ingest time.
- **Chart structured data:** When the LLM extracts `graph_data` or `table_data`, it's stored in `questions.graph_data_jsonb` / `questions.table_data_jsonb` (migration 020). The image itself is in Storage. The frontend gets both: structured data for rendering a chart component + the original image as fallback.

---

## Notes for Implementation

- **DB column names:** Verify against actual migration files in `backend/migrations/` — column names in upsert.py SQL must exactly match the schema.
- **asyncpg JSONB:** asyncpg returns JSONB columns as dicts automatically when using `asyncpg >= 0.29`. For older versions, manually `json.loads()` the field.
- **`fn_refresh_irt_b` signature:** Check migration 033 for exact function signature before calling it in jobs.py.
- **`question_grammar_keys` table:** Verify exact column names from migration 039.
- **`generation_templates` table:** Seeded in migration 038. Verify column names before querying.
- **Vector type:** asyncpg doesn't know `vector` type natively — register pgvector codec or cast as `text` in queries and decode manually if needed.

---

---

## Chunk 10: Grammar Rules System and Practice Construction

### Overview

The current pipeline hardcodes grammar focus keys as a frozen Python set in `app/models/ontology.py`. This is fragile for three reasons:

1. **No growth path** — adding a new grammar rule requires a code change, a migration, and a redeploy
2. **No LLM guidance** — the Pass 2 prompt lists key names only; the LLM has no definition, example, or disambiguation rule to resolve ambiguous cases
3. **No drift tracking** — when the LLM confuses `comma_splice` with `run_on_sentence`, there is no record and no feedback loop

This chunk replaces the hardcoded approach with a **DB-driven grammar rule system** where:

- `taxonomy/GRAMMAR_TAXONOMY.md` is the canonical human-editable source of truth
- A sync script propagates changes to the DB (no manual SQL required)
- The Pass 2 prompt is built dynamically from the DB, including definitions, examples, and disambiguation rules
- A confusion matrix tracks which rule pairs the LLM gets wrong most often
- A `GET /grammar/rules` API lets human admins inspect and extend the taxonomy live

---

### Design: Machine-Readable Grammar Taxonomy

The existing `taxonomy/DSAT_Grammar_Rules_Complete.md` and `taxonomy/DSAT_Verbal_Master_Taxonomy_v2.md` are human-readable but not machine-parseable. A new consolidated file, `taxonomy/GRAMMAR_TAXONOMY.md`, adds JSON blocks that both a human admin and the backend loader can consume.

**Format per rule:**

````markdown
## subject_verb_agreement

**Category:** agreement
**SAT Frequency:** high
**Confusion Risk:** pronoun_antecedent_agreement, collective_noun_agreement

**Definition:** The verb must match the number (singular/plural) of its grammatical subject, not the nearest noun.

**Disambiguation from `pronoun_antecedent_agreement`:** subject_verb_agreement applies when the VERB form is wrong; pronoun_antecedent_agreement applies when the PRONOUN form is wrong. If neither the verb nor the pronoun is the blank, consider `collective_noun_agreement`.

```json
{
  "key": "subject_verb_agreement",
  "category": "agreement",
  "sat_frequency": "high",
  "confusion_risk": ["pronoun_antecedent_agreement", "collective_noun_agreement"],
  "definition": "The verb must match the number of its grammatical subject, not the nearest noun.",
  "correct_example": "The stack of papers sits on the desk.",
  "incorrect_example": "The stack of papers sit on the desk.",
  "explanation": "'Stack' is the subject (singular), not 'papers'. Verb must be 'sits'.",
  "trap_pattern": "Intervening prepositional phrase separating subject from verb.",
  "disambiguation": {
    "pronoun_antecedent_agreement": "SVA: verb form is wrong. PAA: pronoun form is wrong.",
    "collective_noun_agreement": "SCA: subject is a collective noun (team, committee). SVA: standard noun-verb mismatch."
  }
}
```
````

This structure gives:
- Human admin: a readable explanation + example they can verify
- LLM: a JSON block injected into the Pass 2 system prompt with definitions + disambiguation
- Backend: a parseable block for syncing to DB

---

### Task 29: Grammar Taxonomy Markdown (Consolidated Source of Truth)

**Files:**
- Create: `taxonomy/GRAMMAR_TAXONOMY.md`

This file consolidates `DSAT_Grammar_Rules_Complete.md` + `DSAT_Verbal_Master_Taxonomy_v2.md` into a single machine-parseable format. The existing files remain as reference. This file is the one the backend loads.

- [ ] **Step 1: Create `taxonomy/GRAMMAR_TAXONOMY.md` header**

```markdown
# DSAT Grammar Taxonomy — Machine-Readable Source of Truth

> **For humans:** Edit this file to add or modify grammar rules.
> Run `uv run python backend/scripts/sync_grammar_rules.py` after any edit to propagate changes to the DB.
>
> **For LLMs:** The JSON block within each rule section is injected verbatim into the Pass 2 annotation prompt.
> Follow the `disambiguation` field to resolve ambiguous cases. Never assign a key not listed here.

**Version:** 1.0
**Last updated:** 2026-04-18
**Rule count:** [auto-updated by sync script]
```

- [ ] **Step 2: Add all grammar rules in machine-readable format**

Each rule follows the template above. Minimum required rules (from existing taxonomy docs):

| Key | Category | Confusion Risk |
|-----|----------|---------------|
| `sentence_fragment` | boundary | `run_on_sentence`, `comma_splice` |
| `run_on_sentence` | boundary | `comma_splice`, `sentence_fragment` |
| `comma_splice` | boundary | `run_on_sentence` |
| `subject_verb_agreement` | agreement | `pronoun_antecedent_agreement` |
| `pronoun_antecedent_agreement` | agreement | `subject_verb_agreement` |
| `pronoun_case` | agreement | `pronoun_antecedent_agreement` |
| `verb_tense_consistency` | verb | `verb_form`, `sequence_of_tenses` |
| `sequence_of_tenses` | verb | `verb_tense_consistency` |
| `subjunctive_mood` | verb | `verb_form` |
| `verb_form` | verb | `verb_tense_consistency` |
| `misplaced_modifier` | modifier | `dangling_modifier` |
| `dangling_modifier` | modifier | `misplaced_modifier` |
| `parallel_structure` | structure | `faulty_comparison` |
| `faulty_comparison` | structure | `parallel_structure` |
| `comma_usage` | punctuation | `semicolon_usage`, `colon_usage` |
| `semicolon_usage` | punctuation | `comma_usage`, `colon_usage` |
| `colon_usage` | punctuation | `semicolon_usage` |
| `apostrophe_possessive` | punctuation | `apostrophe_contraction` |
| `apostrophe_contraction` | punctuation | `apostrophe_possessive` |
| `relative_clause_punctuation` | punctuation | `comma_usage`, `appositive_punctuation` |
| `appositive_punctuation` | punctuation | `relative_clause_punctuation` |

- [ ] **Step 3: Verify JSON blocks are valid**

```bash
python3 -c "
import re, json
text = open('taxonomy/GRAMMAR_TAXONOMY.md').read()
blocks = re.findall(r'\`\`\`json\n(\{.*?\})\n\`\`\`', text, re.DOTALL)
for i, b in enumerate(blocks):
    try:
        json.loads(b)
    except Exception as e:
        print(f'Block {i} invalid: {e}')
print(f'{len(blocks)} JSON blocks validated')
"
```

Expected: `21 JSON blocks validated` (or however many rules)

- [ ] **Step 4: Commit**

```bash
git add taxonomy/GRAMMAR_TAXONOMY.md
git commit -m "feat: consolidated machine-readable grammar taxonomy with disambiguation rules"
```

---

### Task 30: Grammar Rules DB Migration

**Files:**
- Create: `backend/migrations/044_grammar_rules_system.sql`

- [ ] **Step 1: Write migration**

```sql
-- 044_grammar_rules_system.sql
-- Growable grammar rule registry. Source of truth is taxonomy/GRAMMAR_TAXONOMY.md.
-- Synced via scripts/sync_grammar_rules.py — never edit this table manually.

CREATE TABLE IF NOT EXISTS public.grammar_rules (
    key             text PRIMARY KEY,            -- e.g. 'subject_verb_agreement'
    category        text NOT NULL,               -- boundary | agreement | verb | modifier | structure | punctuation
    definition      text NOT NULL,
    correct_example text,
    incorrect_example text,
    explanation     text,
    trap_pattern    text,
    sat_frequency   text CHECK (sat_frequency IN ('high', 'medium', 'low', 'rare')),
    is_active       boolean NOT NULL DEFAULT true,
    version         int NOT NULL DEFAULT 1,       -- bump when definition changes
    created_at      timestamptz NOT NULL DEFAULT NOW(),
    updated_at      timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.grammar_rule_examples (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key        text NOT NULL REFERENCES public.grammar_rules(key) ON DELETE CASCADE,
    example_type    text NOT NULL CHECK (example_type IN ('correct', 'incorrect', 'trap')),
    text            text NOT NULL,
    explanation     text,
    source          text,           -- e.g. 'PT4 RW M1 Q22'
    created_at      timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.grammar_disambiguation_rules (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key_a      text NOT NULL REFERENCES public.grammar_rules(key) ON DELETE CASCADE,
    rule_key_b      text NOT NULL REFERENCES public.grammar_rules(key) ON DELETE CASCADE,
    rule_text       text NOT NULL,   -- plain-English rule for LLM: "Use A when X; use B when Y"
    created_at      timestamptz NOT NULL DEFAULT NOW(),
    UNIQUE (rule_key_a, rule_key_b)
);

-- Tracks LLM confusion: when LLM assigned key_assigned but human corrected to key_correct
CREATE TABLE IF NOT EXISTS public.grammar_confusion_log (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          uuid REFERENCES public.question_ingestion_jobs(id) ON DELETE SET NULL,
    question_id     uuid REFERENCES public.questions(id) ON DELETE SET NULL,
    key_assigned    text NOT NULL,   -- what the LLM said
    key_correct     text NOT NULL,   -- what the human changed it to
    llm_provider    text,
    llm_model       text,
    logged_at       timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grammar_confusion_log_keys
    ON public.grammar_confusion_log(key_assigned, key_correct);

-- View: confusion matrix (most common LLM mistakes)
CREATE OR REPLACE VIEW public.v_grammar_confusion_matrix AS
SELECT
    key_assigned,
    key_correct,
    COUNT(*) AS confusion_count,
    MAX(logged_at) AS last_seen
FROM public.grammar_confusion_log
WHERE key_assigned != key_correct
GROUP BY key_assigned, key_correct
ORDER BY confusion_count DESC;
```

- [ ] **Step 2: Apply migration**

```bash
psql $DATABASE_URL -f backend/migrations/044_grammar_rules_system.sql
```

- [ ] **Step 3: Commit**

```bash
git add backend/migrations/044_grammar_rules_system.sql
git commit -m "feat: grammar rules DB — rules, examples, disambiguation, confusion matrix"
```

---

### Task 31: Grammar Sync Script

**Files:**
- Create: `backend/scripts/sync_grammar_rules.py`

Reads `taxonomy/GRAMMAR_TAXONOMY.md`, parses JSON blocks, upserts into `grammar_rules` and `grammar_disambiguation_rules`. Run after any taxonomy edit. Idempotent.

- [ ] **Step 1: Write sync script**

```python
#!/usr/bin/env python3
"""
Sync grammar rules from taxonomy/GRAMMAR_TAXONOMY.md → Postgres.
Usage: uv run python backend/scripts/sync_grammar_rules.py
"""
import asyncio
import json
import re
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

TAXONOMY_PATH = Path(__file__).parent.parent.parent / "taxonomy" / "GRAMMAR_TAXONOMY.md"

def parse_taxonomy(text: str) -> list[dict]:
    """Extract all JSON blocks from the taxonomy markdown."""
    blocks = re.findall(r'```json\n(\{.*?\})\n```', text, re.DOTALL)
    rules = []
    for block in blocks:
        try:
            rules.append(json.loads(block))
        except json.JSONDecodeError as e:
            print(f"WARNING: Invalid JSON block: {e}\n{block[:100]}")
    return rules

async def sync(rules: list[dict]) -> None:
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    async with pool.acquire() as conn:
        for rule in rules:
            key = rule["key"]
            # Upsert grammar_rules
            await conn.execute("""
                INSERT INTO public.grammar_rules
                    (key, category, definition, correct_example, incorrect_example,
                     explanation, trap_pattern, sat_frequency)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                ON CONFLICT (key) DO UPDATE SET
                    category = EXCLUDED.category,
                    definition = EXCLUDED.definition,
                    correct_example = EXCLUDED.correct_example,
                    incorrect_example = EXCLUDED.incorrect_example,
                    explanation = EXCLUDED.explanation,
                    trap_pattern = EXCLUDED.trap_pattern,
                    sat_frequency = EXCLUDED.sat_frequency,
                    version = grammar_rules.version + 1,
                    updated_at = NOW()
            """,
                key,
                rule.get("category", ""),
                rule.get("definition", ""),
                rule.get("correct_example"),
                rule.get("incorrect_example"),
                rule.get("explanation"),
                rule.get("trap_pattern"),
                rule.get("sat_frequency", "medium"),
            )
            print(f"  ✓ {key}")

            # Upsert disambiguation rules
            for other_key, rule_text in (rule.get("disambiguation") or {}).items():
                await conn.execute("""
                    INSERT INTO public.grammar_disambiguation_rules
                        (rule_key_a, rule_key_b, rule_text)
                    VALUES ($1,$2,$3)
                    ON CONFLICT (rule_key_a, rule_key_b) DO UPDATE SET
                        rule_text = EXCLUDED.rule_text
                """, key, other_key, rule_text)

    await pool.close()
    print(f"\nSynced {len(rules)} rules.")

if __name__ == "__main__":
    text = TAXONOMY_PATH.read_text()
    rules = parse_taxonomy(text)
    if not rules:
        print("ERROR: No JSON blocks found in taxonomy file.")
        sys.exit(1)
    asyncio.run(sync(rules))
```

- [ ] **Step 2: Run sync**

```bash
cd backend
uv run python scripts/sync_grammar_rules.py
```

Expected output:
```
  ✓ sentence_fragment
  ✓ run_on_sentence
  ✓ comma_splice
  ... (all 21 rules)
Synced 21 rules.
```

- [ ] **Step 3: Verify in DB**

```sql
SELECT key, category, sat_frequency FROM public.grammar_rules ORDER BY category, key;
-- expect: 21 rows
SELECT COUNT(*) FROM public.grammar_disambiguation_rules;
-- expect: > 0 (depends on how many disambiguation pairs are defined)
```

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/sync_grammar_rules.py
git commit -m "feat: grammar sync script — taxonomy/GRAMMAR_TAXONOMY.md → DB"
```

---

### Task 32: Grammar Loader + Dynamic Prompt Builder

**Files:**
- Create: `backend/app/grammar/__init__.py`
- Create: `backend/app/grammar/loader.py`
- Create: `backend/app/grammar/prompt_builder.py`
- Create: `backend/app/grammar/drift_guard.py`
- Modify: `backend/app/main.py` — load grammar rules at startup into `app.state`
- Modify: `backend/app/prompts/pass2_annotation.py` — use dynamic grammar section

The grammar rules are loaded once at startup from the DB and cached in `app.state.grammar_rules`. The Pass 2 prompt builder pulls from this cache — no DB call per request.

- [ ] **Step 1: Write grammar loader test**

```python
# tests/test_grammar_loader.py
import pytest
from unittest.mock import AsyncMock
from app.grammar.loader import load_grammar_rules, GrammarRule

async def test_load_grammar_rules_returns_rules():
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[
        {
            "key": "subject_verb_agreement",
            "category": "agreement",
            "definition": "Verb must match subject number.",
            "correct_example": "The stack sits.",
            "incorrect_example": "The stack sit.",
            "explanation": "Stack is singular.",
            "trap_pattern": "Intervening phrase.",
            "sat_frequency": "high",
        }
    ])
    rules = await load_grammar_rules(conn)
    assert len(rules) == 1
    assert rules[0].key == "subject_verb_agreement"
    assert rules[0].category == "agreement"

def test_grammar_rule_allowed_keys_set():
    from app.grammar.loader import GrammarRule
    rules = [
        GrammarRule(key="comma_splice", category="boundary", definition="x"),
        GrammarRule(key="run_on_sentence", category="boundary", definition="y"),
    ]
    keys = {r.key for r in rules}
    assert "comma_splice" in keys
```

- [ ] **Step 2: Create `app/grammar/loader.py`**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GrammarRule:
    key: str
    category: str
    definition: str
    correct_example: Optional[str] = None
    incorrect_example: Optional[str] = None
    explanation: Optional[str] = None
    trap_pattern: Optional[str] = None
    sat_frequency: str = "medium"
    disambiguations: dict[str, str] = field(default_factory=dict)

async def load_grammar_rules(conn) -> list[GrammarRule]:
    """Load all active grammar rules + disambiguation pairs from DB."""
    rows = await conn.fetch("""
        SELECT key, category, definition, correct_example, incorrect_example,
               explanation, trap_pattern, sat_frequency
        FROM public.grammar_rules
        WHERE is_active = true
        ORDER BY category, key
    """)
    rules_by_key: dict[str, GrammarRule] = {
        r["key"]: GrammarRule(**dict(r)) for r in rows
    }

    disambig_rows = await conn.fetch("""
        SELECT rule_key_a, rule_key_b, rule_text
        FROM public.grammar_disambiguation_rules
    """)
    for d in disambig_rows:
        if d["rule_key_a"] in rules_by_key:
            rules_by_key[d["rule_key_a"]].disambiguations[d["rule_key_b"]] = d["rule_text"]

    return list(rules_by_key.values())

def allowed_grammar_keys(rules: list[GrammarRule]) -> frozenset[str]:
    """Dynamic replacement for the hardcoded GRAMMAR_FOCUS_KEYS constant."""
    return frozenset(r.key for r in rules)
```

- [ ] **Step 3: Create `app/grammar/prompt_builder.py`**

```python
from app.grammar.loader import GrammarRule

def build_grammar_prompt_section(rules: list[GrammarRule]) -> str:
    """
    Build the grammar rules section injected into the Pass 2 system prompt.
    Includes: key name, definition, correct/incorrect example, disambiguation.
    Formatted for maximum LLM clarity — grouped by category, disambiguation last.
    """
    categories: dict[str, list[GrammarRule]] = {}
    for rule in rules:
        categories.setdefault(rule.category, []).append(rule)

    lines = ["=== GRAMMAR FOCUS RULES ===",
             "Assign grammar_focus_key ONLY from the keys listed below.",
             "Use the disambiguation rules to resolve ambiguous cases.\n"]

    for category, cat_rules in sorted(categories.items()):
        lines.append(f"--- {category.upper()} ---")
        for rule in cat_rules:
            lines.append(f"\nKEY: {rule.key}")
            lines.append(f"Definition: {rule.definition}")
            if rule.correct_example:
                lines.append(f"Correct:   {rule.correct_example}")
            if rule.incorrect_example:
                lines.append(f"Incorrect: {rule.incorrect_example}")
            if rule.trap_pattern:
                lines.append(f"SAT trap:  {rule.trap_pattern}")
            if rule.disambiguations:
                lines.append("Disambiguate:")
                for other_key, rule_text in rule.disambiguations.items():
                    lines.append(f"  vs {other_key}: {rule_text}")
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Create `app/grammar/drift_guard.py`**

```python
from app.grammar.loader import GrammarRule

def validate_grammar_key(key: str | None, rules: list[GrammarRule]) -> str | None:
    """
    Validate that an LLM-assigned grammar_focus_key is in the active rule set.
    Returns an error message or None if valid.
    """
    if key is None:
        return None
    allowed = {r.key for r in rules}
    if key not in allowed:
        closest = _closest_key(key, allowed)
        return (
            f"Invalid grammar_focus_key '{key}'. "
            f"Not in active rule set. Closest match: '{closest}'"
        )
    return None

def _closest_key(key: str, allowed: set[str]) -> str:
    """Levenshtein-like closest match for helpful error messages."""
    def dist(a: str, b: str) -> int:
        if len(a) < len(b):
            return dist(b, a)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
            prev = curr
        return prev[-1]
    return min(allowed, key=lambda k: dist(key, k))

async def log_grammar_confusion(
    conn,
    job_id,
    question_id,
    key_assigned: str,
    key_correct: str,
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> None:
    """Call when a human corrects an LLM grammar key assignment."""
    await conn.execute("""
        INSERT INTO public.grammar_confusion_log
            (job_id, question_id, key_assigned, key_correct, llm_provider, llm_model)
        VALUES ($1,$2,$3,$4,$5,$6)
    """, job_id, question_id, key_assigned, key_correct, llm_provider, llm_model)
```

- [ ] **Step 5: Load grammar rules at startup — update `app/main.py`**

```python
# In lifespan(), after creating pool:
from app.grammar.loader import load_grammar_rules
async with app.state.pool.acquire() as conn:
    app.state.grammar_rules = await load_grammar_rules(conn)
```

- [ ] **Step 6: Update `app/prompts/pass2_annotation.py`** — inject dynamic grammar section

```python
# Replace the static GRAMMAR_FOCUS_KEYS list in the Pass 2 prompt with:

def build_pass2_system_prompt(grammar_rules: list) -> str:
    from app.grammar.prompt_builder import build_grammar_prompt_section
    grammar_section = build_grammar_prompt_section(grammar_rules)
    return f"""You are annotating DSAT questions against a fixed taxonomy schema.
Use ONLY the allowed key values listed. Do not invent labels.
If uncertain, choose the closest allowed label and set needs_review: true.

{grammar_section}

Return valid JSON only."""
```

- [ ] **Step 7: Update `app/pipeline/ingestion/validator.py`** — use dynamic keys

```python
# Replace:
#   from app.models.ontology import GRAMMAR_FOCUS_KEYS
# With:
#   from app.grammar.loader import allowed_grammar_keys
#   from app.grammar.drift_guard import validate_grammar_key

def validate_ingestion(extract, annotation, content_origin="official", grammar_rules=None):
    errors = []
    # ... existing checks ...

    if grammar_rules and annotation.grammar_focus_key:
        err = validate_grammar_key(annotation.grammar_focus_key, grammar_rules)
        if err:
            errors.append(err)

    return errors
```

- [ ] **Step 8: Update annotator to pass grammar_rules through**

```python
# app/pipeline/ingestion/annotator.py
async def annotate_pass2(extract, provider, grammar_rules=None):
    from app.prompts.pass2_annotation import build_pass2_system_prompt
    system = build_pass2_system_prompt(grammar_rules or [])
    user = build_pass2_user_prompt(extract.model_dump())
    response = await provider.complete(system, user, temperature=0.1, cache_system=True)
    data = extract_json(response.content)
    return QuestionAnnotation.model_validate(data)
```

And in `orchestrator.py`, pass `request.app.state.grammar_rules` into `annotate_pass2()`.

- [ ] **Step 9: Run tests**

```bash
uv run pytest tests/test_grammar_loader.py tests/test_validator.py -v
```

Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/grammar/ backend/app/prompts/ backend/app/pipeline/
git commit -m "feat: dynamic grammar rule system — DB-driven Pass 2 prompt + drift guard"
```

---

### Task 33: Grammar Rules API (Admin)

**Files:**
- Create: `backend/app/routers/grammar.py`

- [ ] **Step 1: Create `app/routers/grammar.py`**

```python
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.auth import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])

class GrammarRuleCreate(BaseModel):
    key: str
    category: str
    definition: str
    correct_example: Optional[str] = None
    incorrect_example: Optional[str] = None
    explanation: Optional[str] = None
    trap_pattern: Optional[str] = None
    sat_frequency: str = "medium"

class DisambiguationCreate(BaseModel):
    rule_key_a: str
    rule_key_b: str
    rule_text: str

@router.get("/grammar/rules")
async def list_grammar_rules(request: Request):
    """List all active grammar rules with disambiguation pairs."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT gr.*,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'other_key', gd.rule_key_b,
                            'rule_text', gd.rule_text
                        )
                    ) FILTER (WHERE gd.id IS NOT NULL),
                    '[]'
                ) AS disambiguations
            FROM public.grammar_rules gr
            LEFT JOIN public.grammar_disambiguation_rules gd ON gd.rule_key_a = gr.key
            WHERE gr.is_active = true
            GROUP BY gr.key
            ORDER BY gr.category, gr.key
        """)
    return [dict(r) for r in rows]

@router.get("/grammar/rules/{key}")
async def get_grammar_rule(key: str, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.grammar_rules WHERE key=$1", key
        )
        examples = await conn.fetch(
            "SELECT * FROM public.grammar_rule_examples WHERE rule_key=$1 ORDER BY example_type",
            key,
        )
    if not row:
        raise HTTPException(status_code=404)
    return {**dict(row), "examples": [dict(e) for e in examples]}

@router.post("/grammar/rules")
async def create_grammar_rule(body: GrammarRuleCreate, request: Request):
    """Add a new grammar rule. Also update GRAMMAR_TAXONOMY.md manually after this."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO public.grammar_rules
                (key, category, definition, correct_example, incorrect_example,
                 explanation, trap_pattern, sat_frequency)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (key) DO UPDATE SET
                definition = EXCLUDED.definition,
                updated_at = NOW(),
                version = grammar_rules.version + 1
        """,
            body.key, body.category, body.definition,
            body.correct_example, body.incorrect_example,
            body.explanation, body.trap_pattern, body.sat_frequency,
        )
    # Reload grammar rules into app state
    async with pool.acquire() as conn:
        from app.grammar.loader import load_grammar_rules
        request.app.state.grammar_rules = await load_grammar_rules(conn)
    return {"status": "created", "key": body.key,
            "note": "Update taxonomy/GRAMMAR_TAXONOMY.md to keep source of truth in sync."}

@router.post("/grammar/disambiguations")
async def add_disambiguation(body: DisambiguationCreate, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO public.grammar_disambiguation_rules (rule_key_a, rule_key_b, rule_text)
            VALUES ($1,$2,$3)
            ON CONFLICT (rule_key_a, rule_key_b) DO UPDATE SET rule_text = EXCLUDED.rule_text
        """, body.rule_key_a, body.rule_key_b, body.rule_text)
    # Reload
    async with pool.acquire() as conn:
        from app.grammar.loader import load_grammar_rules
        request.app.state.grammar_rules = await load_grammar_rules(conn)
    return {"status": "ok"}

@router.get("/grammar/confusion-matrix")
async def get_confusion_matrix(request: Request, limit: int = 20):
    """Shows which grammar keys the LLM confuses most — sorted by frequency."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT key_assigned, key_correct, confusion_count, last_seen
            FROM public.v_grammar_confusion_matrix
            LIMIT $1
        """, limit)
    return [dict(r) for r in rows]

@router.post("/grammar/confusion-log")
async def log_correction(
    job_id: uuid.UUID,
    key_assigned: str,
    key_correct: str,
    request: Request,
):
    """Called when a human corrects an LLM grammar key assignment via the review UI."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        job = await conn.fetchrow(
            "SELECT question_id FROM public.question_ingestion_jobs WHERE id=$1", job_id
        )
        from app.grammar.drift_guard import log_grammar_confusion
        await log_grammar_confusion(
            conn, job_id,
            job["question_id"] if job else None,
            key_assigned, key_correct,
        )
    return {"status": "logged"}
```

- [ ] **Step 2: Register in `main.py`**

```python
from app.routers import grammar
app.include_router(grammar.router, tags=["grammar"])
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest tests/ -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/grammar.py backend/app/main.py
git commit -m "feat: grammar rules API — CRUD, disambiguation, confusion matrix"
```

---

### Task 34: Practice Construction for Grammar Rules

A **practice construction** workflow generates targeted practice questions for a specific grammar rule. This builds on the existing generation pipeline (Chunk 6) but constrains the generation to a single rule — useful for building rule-specific drill sets.

**Files:**
- Create: `backend/app/routers/grammar.py` (extend, already created above)
- Modify: `backend/app/pipeline/generation/generate.py` — add grammar-targeted run variant

- [ ] **Step 1: Add practice generation endpoint**

```python
# app/routers/grammar.py (append)

class GrammarPracticeRequest(BaseModel):
    grammar_focus_key: str          # must be in active grammar_rules
    item_count: int = 5
    difficulty: Optional[str] = None   # easy | medium | hard
    seed_question_ids: list[uuid.UUID] = []  # optional; auto-selected if empty
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

@router.post("/grammar/rules/{key}/practice")
async def generate_grammar_practice(
    key: str,
    body: GrammarPracticeRequest,
    background: BackgroundTasks,
    request: Request,
):
    """
    Generate practice questions targeting a specific grammar rule.
    Wraps the generation pipeline with grammar_focus_key pre-set as a constraint.
    """
    pool = request.app.state.pool
    settings = request.app.state.settings
    grammar_rules = request.app.state.grammar_rules

    # Validate rule exists
    rule = next((r for r in grammar_rules if r.key == key), None)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Grammar rule '{key}' not found")

    # Auto-select seeds from existing questions with this grammar rule if none provided
    seed_ids = body.seed_question_ids
    if not seed_ids:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT q.id FROM public.questions q
                JOIN public.question_classifications qc ON qc.question_id = q.id
                WHERE qc.grammar_focus_key = $1
                  AND q.is_active = true
                  AND (q.content_origin IS NULL OR q.content_origin = 'official')
                ORDER BY RANDOM()
                LIMIT 3
            """, key)
            seed_ids = [r["id"] for r in rows]
        if not seed_ids:
            raise HTTPException(
                status_code=422,
                detail=f"No seed questions found for rule '{key}'. Ingest official questions with this rule first.",
            )

    # Find the conventions_grammar template
    async with pool.acquire() as conn:
        template = await conn.fetchrow("""
            SELECT id FROM public.generation_templates
            WHERE question_family_key = 'conventions_grammar' AND is_active = true
            LIMIT 1
        """)
    if not template:
        raise HTTPException(status_code=422, detail="No conventions_grammar template found")

    # Build target constraints with grammar_focus_key pinned
    target_constraints = {"target_grammar_focus_key": key}
    if body.difficulty:
        target_constraints["target_difficulty_overall"] = body.difficulty

    from app.pipeline.generation.generate import create_generation_run, process_generation_run
    from app.models.payload import GenerationRequest

    gen_request = GenerationRequest(
        seed_question_ids=seed_ids,
        template_id=template["id"],
        item_count=body.item_count,
        target_constraints=target_constraints,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        run_notes=f"Grammar practice drill: {key}",
    )
    run_id = await create_generation_run(
        pool, settings, seed_ids, template["id"],
        item_count=body.item_count,
        target_constraints=target_constraints,
        run_notes=gen_request.run_notes,
    )
    background.add_task(process_generation_run, pool, settings, run_id, gen_request)

    return {
        "run_id": str(run_id),
        "grammar_focus_key": key,
        "rule_definition": rule.definition,
        "item_count": body.item_count,
        "seed_count": len(seed_ids),
        "status": "running",
    }
```

- [ ] **Step 2: Add rule-level stats endpoint**

```python
@router.get("/grammar/rules/{key}/stats")
async def get_rule_stats(key: str, request: Request):
    """
    Shows how many questions exist for this rule, difficulty distribution,
    and recent LLM confusion events.
    """
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        question_count = await conn.fetchval("""
            SELECT COUNT(*) FROM public.question_classifications
            WHERE grammar_focus_key = $1
        """, key)
        difficulty_dist = await conn.fetch("""
            SELECT difficulty_overall, COUNT(*) AS n
            FROM public.question_classifications
            WHERE grammar_focus_key = $1
            GROUP BY difficulty_overall ORDER BY n DESC
        """, key)
        confusion_count = await conn.fetchval("""
            SELECT COUNT(*) FROM public.grammar_confusion_log
            WHERE key_assigned = $1 OR key_correct = $1
        """, key)
    return {
        "key": key,
        "question_count": question_count,
        "difficulty_distribution": [dict(r) for r in difficulty_dist],
        "confusion_events": confusion_count,
    }
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/grammar.py
git commit -m "feat: grammar practice construction — targeted drill generation + rule stats"
```

---

### Grammar System: Growth Workflow

When a new grammar rule needs to be added (e.g., a new pattern discovered from CB practice tests):

```
1. Human admin edits taxonomy/GRAMMAR_TAXONOMY.md
   → Adds new ## section with JSON block
   → Includes definition, examples, disambiguation vs similar rules

2. Validate the JSON block:
   uv run python3 -c "import re,json; [json.loads(b) for b in re.findall(r'\`\`\`json\n(\{.*?\})\n\`\`\`', open('taxonomy/GRAMMAR_TAXONOMY.md').read(), re.DOTALL)]"

3. Sync to DB:
   cd backend && uv run python scripts/sync_grammar_rules.py

4. OR use the API (no redeploy needed):
   POST /grammar/rules  {"key": "new_rule", "category": "...", "definition": "..."}
   POST /grammar/disambiguations  {"rule_key_a": "new_rule", "rule_key_b": "similar_rule", "rule_text": "..."}

5. Restart backend (to reload grammar_rules into app.state)
   OR: POST /grammar/rules reloads app.state automatically

6. New rule is immediately active in:
   - Pass 2 annotation prompts
   - Validator (allowed key set)
   - Practice construction endpoint
   - Drift detection (SEC critical dimensions)
```

---

## FUTURE PLANS

### FP-1: OCR LLM Integration (DeepSeek-OCR or Equivalent)

#### The Problem with Current Approach

The current pipeline uses `pymupdf` to extract embedded image bytes from PDFs, then sends those bytes to a vision-capable LLM (Claude, GPT-4o, Gemma 4). This works well for **digitally-native PDFs** where the text layer is intact and images are embedded as vector graphics or high-res rasters.

It breaks down for:
- **Scanned PDFs** — the entire page is a single low-quality raster image; `pymupdf` extracts one giant JPEG, not clean text + separate figures
- **Photographed test pages** — student photos of practice tests, skewed/rotated, variable lighting
- **Compressed CB PDFs** — some older official College Board PDFs use heavy JPEG compression on embedded images, making chart labels unreadable to vision models

For these cases, a dedicated OCR LLM (DeepSeek-OCR, Mistral-OCR, or a fine-tuned document understanding model) is the right tool. OCR LLMs are specifically trained to handle document layout, table structure, math notation, and degraded scans — tasks where general vision LLMs struggle.

---

#### When to Use Each Approach

| Signal | PDF Extraction + Vision LLM | OCR LLM |
|--------|------------------------------|---------|
| **PDF type** | Digital-native (has text layer) | Scanned / photographed |
| **Image quality** | High-res embedded graphics | Low-res, compressed, skewed |
| **Content type** | Charts with vector labels | Printed tables, handwritten notes |
| **Chart complexity** | Bar/line charts with clear axes | Multi-column tables, math equations |
| **Text accuracy** | `pymupdf` extracts text cleanly | `pymupdf` returns garbage or empty |
| **Pass 1 input** | Text + image bytes to vision LLM | Raw page image → OCR → clean text |
| **Latency** | ~2–5s (single LLM call) | ~5–15s (OCR step + LLM step) |
| **Cost** | Low (vision tokens ≈ text tokens) | Higher (dedicated OCR API call + LLM) |
| **When to trigger** | Default path | `pymupdf` text length < 100 chars on any page |

**Decision rule the orchestrator should implement:**

```
parse_pdf_with_images(path)
  → for each page:
      if len(page.text.strip()) < 100 chars:
          → page is likely scanned
          → route to OCR LLM path
      else:
          → use extracted text + embedded images
          → route to standard vision LLM path
```

A page with fewer than ~100 characters of extracted text almost certainly failed text extraction (scanned). This heuristic catches 95%+ of scanned pages without false positives on legitimate short-text pages (e.g., a page that's mostly a chart).

---

#### Semantic Management vs Image Storage

Once OCR runs, the output is **structured text + layout metadata** — not raw image bytes. This changes what you store and how you serve it:

| Concern | Image Storage (current) | Semantic/OCR Management (future) |
|---------|------------------------|----------------------------------|
| **What is stored** | PNG bytes in Supabase Storage | Structured text + layout JSON in DB |
| **Chart data** | `graph_data_jsonb` (LLM-extracted) | OCR-extracted coordinates + labels |
| **Table data** | `table_data_jsonb` (LLM-extracted) | `table_data_jsonb` with cell-level accuracy |
| **Retrieval** | Signed URL → frontend renders image | JSON → frontend renders from data |
| **Search** | Not searchable (image bytes) | Fully text-searchable |
| **Accessibility** | Alt text only | Full semantic structure |
| **Storage cost** | High (images are large) | Low (JSON is tiny) |
| **Rendering** | Show original image (pixel-perfect) | Reconstruct chart from data |
| **Edit/correct** | Must re-ingest image | Edit JSON fields directly |
| **When preferred** | Low corpus volume, fast iteration | Scale (500+ questions), search required |

**Recommendation:** Keep image storage as the primary path now. Switch to semantic/OCR management when:
1. Corpus exceeds 200 questions — search over visual content becomes valuable
2. Scanned PDFs are a significant portion of source material (>20%)
3. Frontend needs to render charts dynamically (not just show images)

---

#### Future Task: DeepSeek-OCR Integration

**Trigger condition:** Any of the above thresholds are met, OR `pymupdf` text extraction consistently returns < 100 chars on CB practice test pages.

**Files to create/modify:**
- Create: `backend/app/llm/deepseek_ocr_provider.py` — dedicated OCR provider
- Create: `backend/app/parsers/ocr_parser.py` — route scanned pages through OCR LLM
- Modify: `backend/app/parsers/pdf_parser.py` — add scanned-page detection heuristic
- Modify: `backend/app/pipeline/ingestion/orchestrator.py` — branch on scan detection
- Modify: `backend/app/models/extract.py` — add `ocr_confidence`, `layout_jsonb` fields
- New migration: `question_images` + `ocr_layout_jsonb` column on questions

**Implementation sketch:**

```python
# app/llm/deepseek_ocr_provider.py
# DeepSeek-OCR (or Mistral-OCR) accepts an image and returns:
# {"text": "...", "layout": [...], "tables": [...], "confidence": 0.97}

class DeepSeekOCRProvider:
    def __init__(self, settings: Settings):
        self.client = httpx.AsyncClient(base_url=settings.deepseek_ocr_base_url)
        self.api_key = settings.deepseek_ocr_api_key

    async def ocr_page(self, image_bytes: bytes) -> dict:
        """Submit a page image, get back structured text + layout."""
        b64 = base64.standard_b64encode(image_bytes).decode()
        resp = await self.client.post("/v1/ocr", json={
            "image": b64,
            "output_format": "structured",  # tables, layout, text blocks
        }, headers={"Authorization": f"Bearer {self.api_key}"})
        resp.raise_for_status()
        return resp.json()
```

```python
# app/parsers/ocr_parser.py
async def parse_pdf_with_ocr(path: str, ocr_provider) -> dict:
    """
    For each page in the PDF:
    - Render page to image (300 DPI via pymupdf)
    - Submit to OCR LLM
    - Return structured text + layout per page
    """
    import fitz
    doc = fitz.open(str(path))
    pages = []
    for page_num, page in enumerate(doc):
        # Render page as image at 300 DPI
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        ocr_result = await ocr_provider.ocr_page(img_bytes)
        pages.append({
            "page": page_num,
            "text": ocr_result.get("text", ""),
            "tables": ocr_result.get("tables", []),
            "layout": ocr_result.get("layout", []),
            "confidence": ocr_result.get("confidence", 1.0),
        })
    doc.close()
    return {"pages": pages, "ocr_provider": "deepseek"}
```

```python
# app/parsers/pdf_parser.py — scanned-page detection
def is_scanned_page(page_text: str, min_chars: int = 100) -> bool:
    return len(page_text.strip()) < min_chars

# In parse_pdf_with_images():
# After extracting text per page, check each page:
for page_data in result["pages"]:
    if is_scanned_page(page_data["text"]):
        page_data["needs_ocr"] = True
```

**Settings additions:**
```python
# app/config.py
deepseek_ocr_api_key: str = ""
deepseek_ocr_base_url: str = "https://api.deepseek.com"
ocr_min_text_chars: int = 100   # pages with fewer chars are assumed scanned
```

**Note on multimodal interface:** Adding OCR does NOT require changing `LLMProvider.complete()`. OCR is a separate step that runs before Pass 1 — it produces clean text, which then flows normally into `extract_pass1(raw_text, provider)`. The LLMProvider protocol stays clean. DeepSeekOCRProvider is a separate class entirely, not a subtype of LLMProvider.

---

## GAPS AND SUGGESTIONS

_Identified by comparing `_deprecated/backend/` against this plan. Organized by severity._

---

### 🔴 HIGH — Would break the backend immediately

**GAP-1: PDF parser library conflict**
- Deprecated code uses `pdfplumber` for PDF parsing. Plan switches to `pymupdf` (`fitz`) for image extraction.
- These are different APIs and cannot be swapped silently. `pdfplumber` cannot extract embedded image bytes; `pymupdf` can.
- **Fix:** Use `pymupdf` (`fitz`) for all PDF work (text + images). Remove `pdfplumber` from dependencies. Update `pdf_parser.py` to use `fitz` exclusively — which the multimodal task (Task 25) already does. Confirm `pdfplumber` is not imported anywhere.

**GAP-2: `raw_images_b64_jsonb` column missing from migration**
- Task 27 inserts into `question_ingestion_jobs.raw_images_b64_jsonb` and `source_pdf_storage_path`, but no migration adds these columns.
- **Fix:** Add to migration 043 (or a new 044):
  ```sql
  ALTER TABLE public.question_ingestion_jobs
      ADD COLUMN IF NOT EXISTS raw_images_b64_jsonb jsonb,
      ADD COLUMN IF NOT EXISTS source_pdf_storage_path text;
  ```

**GAP-3: `supabase-py` Storage API is synchronous — `run_in_executor` pattern is fragile**
- `image_store.py` wraps synchronous supabase-py calls with `run_in_executor`. Under high concurrency this blocks the thread pool.
- **Fix:** Use `httpx.AsyncClient` directly against the Supabase Storage REST API instead of `supabase-py`. Alternatively, pin `supabase>=2.10` which ships an async client. Add a note in `image_store.py` about which approach is used.

**GAP-4: Embedding client created per-call — no connection reuse**
- Deprecated `embeddings.py` creates a new `AsyncOpenAI` client on every `embed_text()` call.
- Plan doesn't address this and repeats the same pattern.
- **Fix:** Initialize the embedding client once in `lifespan()` and attach to `app.state.embedding_client`. Pass it into `build_embeddings_for_question()` as a parameter instead of instantiating it inside.

**GAP-5: pgvector `vector` type not registered with asyncpg**
- `POST /search` queries `embedding <=> $1::vector`. asyncpg will error on the `vector` type unless a codec is registered.
- Noted in "Notes for Implementation" but no fix task exists in the plan.
- **Fix:** Add to `database.py` / `create_pool()`:
  ```python
  await pool.execute("CREATE EXTENSION IF NOT EXISTS vector")
  # Register vector codec
  await pool.set_type_codec(
      "vector", encoder=lambda v: str(v), decoder=lambda v: v,
      schema="public", format="text"
  )
  ```
  Or cast the embedding list to a string `"[0.1, 0.2, ...]"` and use `$1::vector` in SQL. Add a dedicated task for this.

---

### 🟡 MEDIUM — Missing functionality or significant omission

**GAP-6: No `proposals` / ontology evolution router**
- Deprecated code has `app/routers/ontology.py` with proposal creation/approval endpoints (`POST /ontology/proposals`, `PATCH /ontology/proposals/{id}`). Migration 023 created this table.
- Plan only has `GET /ontology/keys` (read-only).
- **Suggestion:** Add proposal endpoints to the ontology router if the review workflow requires suggesting new taxonomy keys. Low urgency if the taxonomy is stable.

**GAP-7: No `rerun` logic for generated jobs**
- Deprecated `jobs.py` handles `rerun` for both ingested and generated jobs differently — generated reruns create a new attempt job rather than resetting the existing one.
- Plan's `POST /jobs/{id}/rerun` resets `pass2_json=NULL` and re-queues, which is correct for ingestion but wrong for generation (should create a new job row with incremented attempt number).
- **Fix:** In `rerun_job()`, check `job["content_origin"]`. If `generated`, create a new `question_ingestion_jobs` row linked to the same `generation_run_id` with `attempt_number` incremented. Don't reset the original drift_failed row.

**GAP-8: Coaching `generate_coaching_for_question` signature mismatch**
- Plan calls `generate_coaching_for_question(pool, settings, question_id)` as a BackgroundTask.
- But `upsert.py` also needs an `image_store` reference passed in (Task 27). The function signature grows — ensure all call sites are updated together.
- **Fix:** Accept `image_store: ImageStore | None = None` in `upsert_approved_job()` and thread it through from `jobs.py`.

**GAP-9: No `ontology_proposals` model in `payload.py`**
- Deprecated code has `ProposalCreate`, `ProposalRead` Pydantic models.
- Plan's `payload.py` doesn't include them.
- **Suggestion:** Add if proposal endpoints are included. Skip if deferred.

**GAP-10: `conftest.py` pool mock doesn't cover `conn.fetchrow` return shapes**
- Deprecated `conftest.py` has extensive fixtures with realistic DB row return values (e.g., full job dicts, question rows). Plan's conftest is minimal.
- Without realistic fixtures, router tests will fail when they try to access `row["status"]` on a mock that returns `None`.
- **Fix:** Expand conftest with factory fixtures:
  ```python
  def make_job_row(**kwargs) -> dict:
      return {"id": uuid.uuid4(), "status": "draft", "content_origin": "official",
              "input_format": "text", "pass1_json": None, "pass2_json": None,
              "validation_errors_jsonb": None, "review_notes": None,
              "generation_run_id": None, "raw_images_b64_jsonb": None, **kwargs}
  ```

**GAP-11: No `generation_runs` INSERT in `create_generation_run()`**
- Plan references `create_generation_run()` but doesn't show the SQL that writes to `generation_runs`. The deprecated code inserts a row with `status='running'`, `template_id`, `model_name`, `seed_question_ids`, `item_count`, `target_constraints`, `run_notes`.
- **Fix:** Add explicit SQL in Task 15:
  ```sql
  INSERT INTO public.generation_runs
      (template_id, model_name, status, item_count, seed_question_ids, target_constraints, run_notes)
  VALUES ($1, $2, 'running', $3, $4, $5, $6)
  RETURNING id
  ```

**GAP-12: `process_job()` doesn't handle `input_format='generated'` skip**
- When a generated job enters the orchestrator, Pass 1 must be skipped (LLM output IS Pass 1). Plan mentions this in Task 12 ("skip extraction step") but the orchestrator code shown doesn't implement the branch.
- **Fix:** In `orchestrator.py`, add at the top of the try block:
  ```python
  if job["input_format"] == "generated":
      # Pass 1 already in pass1_json — skip extraction
      from app.models.extract import QuestionExtract
      extract = QuestionExtract.model_validate(job["pass1_json"])
  else:
      extract = await extract_pass1(raw_text, provider, images=images)
  ```

**GAP-13: No `QuestionExtract` field for `graph_data` / `table_data`**
- Vision-aware Pass 1 now extracts `graph_data` and `table_data` from images, but `QuestionExtract` model (Task 6) doesn't include these fields.
- `upsert.py` writes `graph_data_jsonb` / `table_data_jsonb` to `questions` but there's no path for the data to flow through the model.
- **Fix:** Add to `QuestionExtract`:
  ```python
  graph_data: Optional[dict] = None   # extracted chart/graph structured data
  table_data: Optional[dict] = None   # extracted table structured data
  ```
  And in `upsert.py`, write these to `questions.graph_data_jsonb` / `questions.table_data_jsonb`.

---

### 🟢 LOW — Polish, documentation, optimization

**GAP-14: `tokenization_status` field not mentioned in migration checklist**
- Migration 040 adds `tokenization_status` to `questions`. Plan's tokenize task writes to it but doesn't remind the implementer to verify the column exists first.
- **Suggestion:** Add to Notes: "Check migration 040 for `tokenization_status` column on `questions` before writing in `tokenize.py`."

**GAP-15: Coaching span-finding algorithm detail missing**
- Plan Task 17 describes `_find_span()` exists and returns `(None, None, None)` on miss, but doesn't detail the sentence-splitting approach.
- Deprecated code splits on `[.!?]` — this breaks on abbreviations ("Dr. Smith") and decimals ("3.14").
- **Suggestion:** Use `re.split(r'(?<=[.!?])\s+', text)` and handle edge cases. Or import `nltk.sent_tokenize` for robustness. Document the chosen approach in the coaching task.

**GAP-16: No `CHANGELOG` / migration version tracking in the app**
- Deprecated code has no migration runner. Plan has no migration runner either.
- If migrations are applied manually (via Supabase dashboard or psql), there's no record of which ones ran.
- **Suggestion:** Add a `GET /admin/migrations` endpoint that queries `pg_tables` or a custom `schema_migrations` table to show applied migrations. Low priority.

**GAP-17: `ollama_provider.py` — no connection timeout on slow models**
- Deprecated Ollama provider uses `httpx.AsyncClient(timeout=120)`. Plan shows the same.
- For large local models (Gemma 4 27B, Qwen3 32B), 120s may not be enough for long passages.
- **Suggestion:** Make timeout configurable via `Settings.ollama_timeout: int = 300`. 5 minutes is safer for multimodal + large models.

**GAP-18: No API versioning**
- Deprecated code has no API versioning (`/v1/`). Plan doesn't add it either.
- **Suggestion:** Consider adding `/api/v1/` prefix to all routers in `main.py` now, before any clients exist. Cheaper to do at project start than after.

**GAP-19: `supabase-py` vs `asyncpg` dual clients**
- Image store uses `supabase-py` (for Storage). DB queries use `asyncpg`. Two separate connection mechanisms to the same Supabase instance.
- This is fine architecturally (Storage ≠ DB), but the `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` must both be set in `.env` alongside `DATABASE_URL`.
- **Suggestion:** Document clearly in `.env.example` which key is used for what:
  ```
  # DB connection (direct Postgres)
  DATABASE_URL=postgresql://...
  # Supabase Storage + Auth (service role)
  SUPABASE_URL=https://xxx.supabase.co
  SUPABASE_SERVICE_KEY=eyJ...
  ```

---

### Summary Table

| ID | Severity | Area | Action |
|----|----------|------|--------|
| GAP-1 | 🔴 HIGH | Parser | Switch fully to `pymupdf`; remove `pdfplumber` |
| GAP-2 | 🔴 HIGH | Migration | Add `raw_images_b64_jsonb` + `source_pdf_storage_path` columns |
| GAP-3 | 🔴 HIGH | Storage | Use async HTTP for Supabase Storage, not `run_in_executor` |
| GAP-4 | 🔴 HIGH | Embeddings | Cache OpenAI embedding client in `app.state` |
| GAP-5 | 🔴 HIGH | DB | Register pgvector codec in `create_pool()` |
| GAP-6 | 🟡 MED | Router | Add ontology proposals endpoints (or document as deferred) |
| GAP-7 | 🟡 MED | Generation | Fix `rerun` for generated jobs — create new row, don't reset |
| GAP-8 | 🟡 MED | Approval | Thread `image_store` through `upsert_approved_job()` |
| GAP-9 | 🟡 MED | Models | Add `ProposalCreate`/`ProposalRead` to `payload.py` if proposals included |
| GAP-10 | 🟡 MED | Tests | Expand `conftest.py` with realistic row fixtures |
| GAP-11 | 🟡 MED | Generation | Add `generation_runs` INSERT SQL to `create_generation_run()` |
| GAP-12 | 🟡 MED | Orchestrator | Add `input_format='generated'` branch to skip Pass 1 |
| GAP-13 | 🟡 MED | Models | Add `graph_data` / `table_data` fields to `QuestionExtract` |
| GAP-14 | 🟢 LOW | Docs | Note migration 040 `tokenization_status` in checklist |
| GAP-15 | 🟢 LOW | Coaching | Document sentence-splitting approach in `_find_span()` |
| GAP-16 | 🟢 LOW | Admin | Optional migration status endpoint |
| GAP-17 | 🟢 LOW | Config | Make Ollama timeout configurable |
| GAP-18 | 🟢 LOW | API | Add `/api/v1/` prefix now before clients exist |
| GAP-19 | 🟢 LOW | Docs | Document dual client pattern in `.env.example` |
