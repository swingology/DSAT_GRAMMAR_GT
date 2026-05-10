# OCR Integration — Phased Task Plan

**Target:** Seamless OCR for scanned PDFs and image uploads in the existing ingest pipeline.
**PRD reference:** `docs/PRD/INGESTION_PRD.md` §8 — OCR Strategy
**Setup guide:** `DEEPSEEK_OCR.md`
**Status:** Not started

---

## Architecture Summary (for context)

The ingest pipeline today:

```
Route handler
  → _parse_pdf_content() / parse_image()  → raw_text (may be "")
  → _run_pipeline() [background task]
      → line 329: raw_text = pass1_json.get("raw_text", "")
      → line 330: if not raw_text → fail("no_raw_text")   ← OCR GATE GOES HERE
      → Pass 1: build_extract_prompt(raw_text) → provider.complete()
      → Pass 2: build_annotate_prompt(q_data) → provider.complete()
      → overlap_check → validate → persist
```

OCR replaces or bypasses the `raw_text` failure:
- **DeepSeek OCR** (Option A): images → HTTP → Markdown text → back into `raw_text` → Pass 1 unchanged
- **Ollama VLM** (Option B): images → `complete_vision()` → structured JSON → directly into `pass1_json` → skip Pass 1, go straight to Pass 2

Both options are configured simultaneously; admin selects per-job via `ocr_strategy` form param.

---

## Phase 1 — Config and Foundation

**Goal:** Add new settings; ensure both OCR providers are configurable side-by-side.

### Task 1.1 — Add OCR settings to `Settings`

**File:** `backend/app/config.py`

Add to the `Settings` class (after the existing OCR block):

```python
# OCR — Option A: DeepSeek OCR (local via Docker/Ollama)
deepseek_ocr_base_url: str = "http://localhost:8001"   # vLLM Docker default
deepseek_ocr_model: str = "deepseek-ai/DeepSeek-OCR-2"
```

Existing settings already cover Option B (`ocr_vision_provider`, `ocr_vision_model`,
`ocr_strategy`, `ocr_fallback`, `vision_max_images`). No changes needed for those.

**Verify:** `get_settings().deepseek_ocr_base_url` returns `"http://localhost:8001"`.

---

### Task 1.2 — Add `ImageContent` and `complete_vision()` to the LLM protocol

**File:** `backend/app/llm/base.py`

Add `ImageContent` dataclass and extend `LLMProvider` with an optional `complete_vision()`:

```python
@dataclass
class ImageContent:
    b64: str
    mime_type: str   # "image/png", "image/jpeg", etc.

class LLMProvider(Protocol):
    async def complete(self, system: str, user: str, ...) -> LLMResponse: ...

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list["ImageContent"],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError(f"{type(self).__name__} does not support vision")
```

`complete_vision()` is an optional protocol method — providers that don't implement it
raise `NotImplementedError`. The pipeline catches this and falls back per `OCR_FALLBACK`.

**Verify:** Import `ImageContent` from `app.llm.base` without errors.

---

## Phase 2 — Ollama VLM Provider (Option B)

**Goal:** Implement `complete_vision()` on `OllamaProvider` using Ollama's existing
`/v1/chat/completions` endpoint, which accepts `image_url` content blocks.

### Task 2.1 — Implement `complete_vision()` on `OllamaProvider`

**File:** `backend/app/llm/ollama_provider.py`

Add after the existing `complete()` method:

```python
async def complete_vision(
    self,
    system: str,
    user: str,
    images: list,          # list[ImageContent] — avoid circular import
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> LLMResponse:
    from app.llm.base import ImageContent   # local import to avoid circular dep
    model = model or self.default_model
    start = time.time()

    # Build content blocks: images first, then text
    content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:{img.mime_type};base64,{img.b64}"},
        }
        for img in images
    ]
    content.append({"type": "text", "text": user})

    response = await self.client.post(
        "/v1/chat/completions",
        json={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
        },
    )
    latency_ms = int((time.time() - start) * 1000)
    response.raise_for_status()
    data = response.json()
    raw_text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return LLMResponse(
        raw_text=raw_text,
        model=model,
        provider="ollama",
        latency_ms=latency_ms,
        token_usage={
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
        },
    )
```

**Notes:**
- No new dependencies — Ollama's `/v1/chat/completions` already supports `image_url`
  content blocks when the loaded model is vision-capable.
- The existing `@with_retry` decorator does not wrap `complete_vision()` — add it if
  desired (import `with_retry` from `app.llm.retry`).

---

## Phase 3 — DeepSeek OCR Provider (Option A)

**Goal:** Create a standalone OCR client that POSTs images to the local DeepSeek-OCR-2
server (vLLM Docker or LMDeploy) and returns extracted Markdown text.

### Task 3.1 — Create `app/parsers/ocr.py`

**File:** `backend/app/parsers/ocr.py` *(new file)*

```python
"""DeepSeek OCR-2 client — sends images to local vLLM/LMDeploy server, returns text."""
import time
import httpx
from app.llm.base import ImageContent, LLMResponse


class DeepSeekOCRClient:
    """Thin HTTP client for DeepSeek-OCR-2 running locally via vLLM or LMDeploy."""

    OCR_SYSTEM_PROMPT = (
        "You are a document OCR specialist. Extract all text from the provided image(s) "
        "exactly as it appears. Preserve the question structure, answer choices (A/B/C/D), "
        "and passage text. Output plain Markdown text only — no commentary, no fences."
    )

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def extract(self, images: list[ImageContent], max_tokens: int = 4096) -> LLMResponse:
        """Send images to DeepSeek-OCR-2 and return extracted Markdown text."""
        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{img.mime_type};base64,{img.b64}"},
            }
            for img in images
        ]
        content.append({
            "type": "text",
            "text": "Extract all text from this document page. Preserve structure.",
        })

        start = time.time()
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": self.OCR_SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
            },
        )
        latency_ms = int((time.time() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            raw_text=raw_text,
            model=self.model,
            provider="deepseek_ocr",
            latency_ms=latency_ms,
            token_usage={
                "input": usage.get("prompt_tokens", 0),
                "output": usage.get("completion_tokens", 0),
            },
        )

    async def close(self):
        await self.client.aclose()
```

### Task 3.2 — Add `get_ocr_client()` to `factory.py`

**File:** `backend/app/llm/factory.py`

Add a factory function for the OCR client, separate from the main LLM provider:

```python
def get_ocr_client(base_url: str, model: str):
    """Return a DeepSeekOCRClient for the given local endpoint."""
    from app.parsers.ocr import DeepSeekOCRClient
    client = DeepSeekOCRClient(base_url=base_url, model=model)
    _provider_registry.append(client)   # registered for close_all_providers()
    return client
```

`close_all_providers()` already calls `await p.close()` if available — `DeepSeekOCRClient`
exposes `close()`, so cleanup is automatic.

---

## Phase 4 — Vision Extraction Prompt

**Goal:** Add a prompt variant for vision-based extraction (Ollama VLM path). Same system
prompt as Pass 1 but a simpler user message since the model reads from images.

### Task 4.1 — Add `build_vision_extract_prompt()` to `extract_prompt.py`

**File:** `backend/app/prompts/extract_prompt.py`

Add after `build_extract_prompt()`:

```python
def build_vision_extract_prompt(source_metadata: dict = None) -> tuple[str, str]:
    """Build prompts for vision-fused extraction (Ollama VLM path, Option B).

    The model reads directly from image content — no raw_text in the user message.
    Same JSON schema is expected in the response.
    """
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource metadata:\n" + "\n".join(hints) if hints else ""

    user = (
        f"Extract ALL questions from the image(s) above. "
        f"Follow the JSON schema exactly. Include every numbered question.{source_hints}"
    )
    return EXTRACT_SYSTEM_PROMPT, user
```

---

## Phase 5 — Pipeline Gate (Core Integration)

**Goal:** Insert the OCR gate into `_run_pipeline()` at the exact point where `raw_text`
is checked. This is the single most critical change — everything else feeds into it.

### Task 5.1 — Add `_collect_page_images()` helper in `ingest.py`

**File:** `backend/app/routers/ingest.py`

Add a helper that extracts all page images from a stored PDF using pymupdf's
`page.get_pixmap()` (rasterizes the page — works even if no images are embedded):

```python
def _collect_page_images(pass1_json: dict) -> list:
    """Extract images from pass1_json._page_images if pre-stored, else return []."""
    from app.llm.base import ImageContent
    raw_images = (pass1_json or {}).get("_page_images", [])
    return [
        ImageContent(b64=img["b64"], mime_type=img.get("mime_type", "image/png"))
        for img in raw_images
        if img.get("b64")
    ]
```

Images are stored in `pass1_json._page_images` at route time (see Task 5.2 below) so
the background task doesn't need to re-read from disk.

---

### Task 5.2 — Store page images in `pass1_json` at route time

**File:** `backend/app/routers/ingest.py`

**In `ingest_official_pdf()` (line ~541):**

Currently:
```python
pdf_result = _parse_pdf_content(content)
raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
```

Change to:
```python
pdf_result = _parse_pdf_content(content)
raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
# If scanned (no extractable text), pre-store page images for the OCR gate
page_images = []
if not raw_text.strip():
    settings_tmp = get_settings()
    max_images = settings_tmp.vision_max_images
    for page in pdf_result["pages"][:max_images]:
        for img in page.get("images", []):
            page_images.append({
                "b64": img["b64"],
                "mime_type": f"image/{img.get('ext', 'png')}",
                "page_number": page["page_number"],
            })
```

Then update the `pass1_json` construction to include `_page_images`:
```python
pass1_json={
    "raw_text": raw_text[:50000],
    "pages": len(pdf_result["pages"]),
    "_page_images": page_images,          # populated only for scanned PDFs
    "source_metadata": { ... },
    "_ocr_strategy": ocr_strategy,        # from form param (Task 6.1)
}
```

Apply the same pattern in `ingest_unofficial_file()` for PDF mime type (line ~631).

**For image uploads (line ~603):**

Remove the existing `raise HTTPException(422, ...)` block. Replace with:
```python
if mime_type in IMAGE_MIME_TYPES:
    from app.parsers.image_parser import parse_image
    import tempfile, pathlib
    # Store the image as a page image for the OCR gate
    with tempfile.NamedTemporaryFile(suffix=pathlib.Path(file.filename or "img").suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        img_data = parse_image(tmp_path)
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)
    raw_text = ""
    page_images = [{"b64": img_data["b64"], "mime_type": img_data["mime_type"], "page_number": 0}]
```

---

### Task 5.3 — Insert OCR gate in `_run_pipeline()`

**File:** `backend/app/routers/ingest.py`

**Current code at line 329–334:**
```python
raw_text = (job.pass1_json or {}).get("raw_text", "")
if not raw_text:
    orch.fail("extracting", "no_raw_text", "No raw text available")
    job.status = "failed"
    await db.commit()
    return
```

**Replace with:**
```python
raw_text = (job.pass1_json or {}).get("raw_text", "")
page_images = _collect_page_images(job.pass1_json)
ocr_strategy = (job.pass1_json or {}).get("_ocr_strategy") or settings.ocr_strategy

if not raw_text and page_images:
    # ── OCR gate ──────────────────────────────────────────────────────────
    orch.advance()
    job.status = "extracting"
    await db.commit()

    form_meta = (job.pass1_json or {}).get("source_metadata", {})
    resolved_strategy = _resolve_ocr_strategy(ocr_strategy, settings)

    if resolved_strategy == "deepseek":
        # Option A: DeepSeek OCR → raw_text → existing Pass 1
        from app.llm.factory import get_ocr_client
        ocr_client = get_ocr_client(
            base_url=settings.deepseek_ocr_base_url,
            model=settings.deepseek_ocr_model,
        )
        try:
            ocr_result = await ocr_client.extract(page_images)
            raw_text = ocr_result.raw_text
            job.pass1_json["raw_text"] = raw_text
            job.pass1_json["_ocr_meta"] = {
                "strategy": "deepseek",
                "model": settings.deepseek_ocr_model,
                "page_count": len(page_images),
                "latency_ms": ocr_result.latency_ms,
            }
            await db.commit()
        except Exception as e:
            orch.fail("extracting", "ocr_error", f"DeepSeek OCR failed: {e}")
            job.status = "failed"
            job.validation_errors_jsonb = [{"step": "ocr", "error": str(e)}]
            await db.commit()
            return

    elif resolved_strategy == "ollama":
        # Option B: Ollama VLM — fused OCR + extraction, skip Pass 1
        from app.prompts.extract_prompt import build_vision_extract_prompt
        system, user = build_vision_extract_prompt(form_meta)
        try:
            vision_result = await provider.complete_vision(
                system=system,
                user=user,
                images=page_images,
                model=settings.ocr_vision_model,
                max_tokens=16000,
            )
            extract_root = extract_json_from_text(
                vision_result.raw_text, job.provider_name, job.model_name
            )
            job.pass1_json = {
                **extract_root,
                "_llm_meta": {
                    "provider": "ollama",
                    "model": settings.ocr_vision_model,
                    "latency_ms": vision_result.latency_ms,
                },
                "_ocr_meta": {
                    "strategy": "ollama",
                    "model": settings.ocr_vision_model,
                    "page_count": len(page_images),
                    "latency_ms": vision_result.latency_ms,
                },
                "source_metadata": form_meta,
            }
            await db.commit()
            # Skip the Pass 1 text extraction below — jump directly to per-question loop
            # by setting raw_text to a sentinel and using the already-populated pass1_json
            raw_text = "_vision_fused_"   # non-empty sentinel; Pass 1 block is skipped
            extract_root_override = extract_root  # used below instead of re-running Pass 1
        except Exception as e:
            orch.fail("extracting", "vision_error", f"Ollama VLM OCR failed: {e}")
            job.status = "failed"
            job.validation_errors_jsonb = [{"step": "ocr", "error": str(e)}]
            await db.commit()
            return

    else:
        orch.fail("extracting", "no_ocr_provider", f"No OCR provider available for strategy '{ocr_strategy}'")
        job.status = "failed"
        await db.commit()
        return
    # ── end OCR gate ──────────────────────────────────────────────────────

elif not raw_text:
    orch.fail("extracting", "no_raw_text", "No raw text available")
    job.status = "failed"
    await db.commit()
    return
```

**Note on the Ollama vision-fused path:** After the OCR gate block, the existing Pass 1
code calls `build_extract_prompt(raw_text)`. Add a check immediately before it:

```python
# Ollama VLM fused path: pass1_json already populated; skip re-running Pass 1
if raw_text == "_vision_fused_":
    extract_root = extract_root_override
else:
    # existing Pass 1 code here
    system, user = build_extract_prompt(raw_text[:100000], form_meta)
    result = await provider.complete(system=system, user=user, max_tokens=16000)
    extract_root = extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
    job.pass1_json = {**extract_root, "_llm_meta": {...}}
```

---

### Task 5.4 — Add `_resolve_ocr_strategy()` helper in `ingest.py`

**File:** `backend/app/routers/ingest.py`

```python
def _resolve_ocr_strategy(requested: str | None, settings) -> str:
    """Resolve the effective OCR strategy from per-job request or config default.

    "auto": try ollama first (if vision_provider=ollama), then deepseek (if base_url set).
    Returns "deepseek" or "ollama" or raises ValueError.
    """
    strategy = (requested or settings.ocr_strategy or "auto").strip().lower()

    if strategy == "deepseek":
        return "deepseek"
    if strategy in ("ollama", "vision"):
        return "ollama"
    if strategy == "auto":
        # Prefer Ollama VLM; fall back to DeepSeek if base_url is configured
        if settings.ocr_vision_provider == "ollama":
            return "ollama"
        if settings.deepseek_ocr_base_url:
            return "deepseek"
    raise ValueError(f"No OCR provider available for strategy '{strategy}'")
```

---

## Phase 6 — Admin Selection via Form Parameter

**Goal:** Expose `ocr_strategy` as an optional form field on all ingest endpoints.

### Task 6.1 — Add `ocr_strategy` param to route handlers

**File:** `backend/app/routers/ingest.py`

**`ingest_official_pdf()` signature (line ~515):** add:
```python
ocr_strategy: str | None = Form(None),
```

**`ingest_unofficial_file()` signature (line ~593):** add:
```python
ocr_strategy: str | None = Form(None),
```

**`ingest_unofficial_batch()` (batch route):** add the same param and forward it to
each per-file job creation.

Store the value in `pass1_json._ocr_strategy` (see Task 5.2). No other changes needed —
`_run_pipeline()` reads it from there.

**Validation:** If `ocr_strategy` is provided and not in `{"deepseek", "ollama", "auto"}`,
return 422 immediately in the route handler:

```python
if ocr_strategy and ocr_strategy not in {"deepseek", "ollama", "auto"}:
    raise HTTPException(status_code=422, detail="ocr_strategy must be 'deepseek', 'ollama', or 'auto'")
```

---

## Phase 7 — PDF Page Rendering Fallback

**Goal:** Handle scanned PDFs where `parse_pdf()` finds no embedded image objects but the
page itself is a scan. Use pymupdf's `page.get_pixmap()` to rasterize pages.

### Task 7.1 — Update `parse_pdf()` to render pages when no images found

**File:** `backend/app/parsers/pdf_parser.py`

In the page loop, after the existing `page.get_images()` extraction, add:

```python
# If page has no extractable text and no embedded images, render the page as a bitmap
if not text.strip() and not images:
    mat = fitz.Matrix(2.0, 2.0)   # 2x scale = ~144 DPI
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_b64 = base64.standard_b64encode(pix.tobytes("png")).decode("utf-8")
    images.append({"index": 0, "b64": img_b64, "ext": "png", "rendered": True})
```

The `rendered: True` flag distinguishes rasterized pages from embedded image objects
(informational only — the OCR pipeline treats both identically).

**Note:** Pymupdf (fitz) is already a project dependency — no new packages needed.

---

## Phase 8 — Tests

**Goal:** Unit/integration tests for each new component.

### Task 8.1 — Test `DeepSeekOCRClient.extract()`

**File:** `backend/tests/test_ocr.py` *(new file)*

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.parsers.ocr import DeepSeekOCRClient
from app.llm.base import ImageContent

@pytest.mark.asyncio
async def test_deepseek_ocr_returns_text():
    client = DeepSeekOCRClient(base_url="http://localhost:8001", model="deepseek-ocr-2")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Question 1: What is..."}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    with patch.object(client.client, "post", new_callable=AsyncMock, return_value=mock_response):
        images = [ImageContent(b64="abc123", mime_type="image/png")]
        result = await client.extract(images)
    assert result.raw_text == "Question 1: What is..."
    assert result.provider == "deepseek_ocr"
```

### Task 8.2 — Test `OllamaProvider.complete_vision()`

**File:** `backend/tests/test_ocr.py`

```python
@pytest.mark.asyncio
async def test_ollama_complete_vision():
    from app.llm.ollama_provider import OllamaProvider
    from app.llm.base import ImageContent
    provider = OllamaProvider(base_url="http://localhost:11434", default_model="qwen2.5-vl:7b")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"questions": []}'}}],
        "usage": {},
    }
    with patch.object(provider.client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        images = [ImageContent(b64="abc", mime_type="image/jpeg")]
        result = await provider.complete_vision("system", "user", images)
    assert result.provider == "ollama"
    # Verify image_url block was sent
    call_json = mock_post.call_args.kwargs["json"]
    user_content = call_json["messages"][1]["content"]
    assert any(c["type"] == "image_url" for c in user_content)
```

### Task 8.3 — Test OCR gate in `_run_pipeline()` — DeepSeek path

**File:** `backend/tests/test_backend_regressions.py` (extend existing file)

Add a test that patches `DeepSeekOCRClient.extract` and verifies the pipeline
processes an OCR result through to Pass 2 annotation without calling `provider.complete`
for Pass 1:

```python
def test_pipeline_uses_deepseek_ocr_when_no_raw_text(client, monkeypatch):
    # job has no raw_text but has _page_images and _ocr_strategy=deepseek
    # verify: ocr_client.extract() is called, raw_text is populated, pipeline continues
    pass  # implementation via mock DB session following existing test patterns
```

### Task 8.4 — Test OCR gate — Ollama VLM path

Verify that when `_ocr_strategy=ollama`, `provider.complete_vision()` is called and
`pass1_json` is updated with `_ocr_meta.strategy == "ollama"` and Pass 1 is skipped.

### Task 8.5 — Test `ocr_strategy` form param validation

**File:** `backend/tests/test_backend_regressions.py`

```python
def test_ingest_official_pdf_rejects_invalid_ocr_strategy(client):
    resp = client.post(
        "/ingest/official/pdf",
        headers={"X-API-Key": "admin-test-key"},
        data={"source_exam_code": "PT06", "source_module_code": "01",
              "source_subject_code": "verbal", "ocr_strategy": "invalid-value"},
        files={"file": ("test.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert resp.status_code == 422
```

### Task 8.6 — Run full test suite

```bash
cd backend && uv run pytest -x -q
```

Expected: all prior 182 tests pass; new OCR tests pass.

---

## Phase 9 — Configuration Verification and Smoke Test

**Goal:** End-to-end manual verification before considering the feature complete.

### Task 9.1 — Verify DeepSeek OCR path (requires Docker running)

```bash
# Start DeepSeek-OCR-2 via vLLM Docker
docker run -d --runtime nvidia --gpus all --ipc=host -p 8001:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model deepseek-ai/DeepSeek-OCR-2 \
  --logits-processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching --mm-processor-cache-gb 0 \
  --trust-remote-code --max-model-len 4096

# .env
DEEPSEEK_OCR_BASE_URL=http://localhost:8001
DEEPSEEK_OCR_MODEL=deepseek-ai/DeepSeek-OCR-2

# Upload a scanned PDF with explicit DeepSeek strategy
curl -X POST http://localhost:8000/ingest/unofficial/file \
  -H "X-API-Key: admin-key" \
  -F "file=@scanned_test.pdf" \
  -F "ocr_strategy=deepseek"

# Check job status
curl http://localhost:8000/ingest/jobs/<job_id> -H "X-API-Key: admin-key"
# Expect: pass1_json._ocr_meta.strategy == "deepseek"
```

### Task 9.2 — Verify Ollama VLM path (requires Ollama + qwen2.5-vl:7b)

```bash
# Pull model if not already present
ollama pull qwen2.5-vl:7b

# .env
OCR_VISION_PROVIDER=ollama
OCR_VISION_MODEL=qwen2.5-vl:7b

# Upload a scanned image with Ollama strategy
curl -X POST http://localhost:8000/ingest/unofficial/file \
  -H "X-API-Key: admin-key" \
  -F "file=@question_screenshot.png" \
  -F "ocr_strategy=ollama"

# Expect: pass1_json._ocr_meta.strategy == "ollama", questions extracted
```

### Task 9.3 — Verify `auto` strategy selection

Upload with no `ocr_strategy` param and verify the resolved strategy matches the
`OCR_STRATEGY` env var (default `auto`, which picks Ollama if configured).

### Task 9.4 — Verify existing text-layer PDFs are unaffected

Upload a normal (non-scanned) PDF. The OCR gate should not activate — `raw_text` is
non-empty so the gate condition `not raw_text and page_images` is false. Confirm
`pass1_json._ocr_meta` is absent.

---

## Phase 10 — Update Anatomy and Debug Log

### Task 10.1 — Update `anatomy.md`

Add entries for:
- `backend/app/parsers/ocr.py` — DeepSeek-OCR-2 HTTP client
- `backend/tests/test_ocr.py` — OCR provider unit tests

### Task 10.2 — Update `DEBUG_LOG.md`

After all phases are complete, add a new audit entry documenting the implementation,
any bugs found during testing, and the final test suite result.

---

## Completion Checklist

| Phase | Task | File(s) | Status |
|---|---|---|---|
| 1 | Config: add `deepseek_ocr_base_url`, `deepseek_ocr_model` | `config.py` | [x] |
| 1 | Protocol: `ImageContent`, `complete_vision()` on `LLMProvider` | `llm/base.py` | [x] |
| 2 | `OllamaProvider.complete_vision()` | `llm/ollama_provider.py` | [x] |
| 3 | `DeepSeekOCRClient` | `parsers/ocr.py` | [x] |
| 3 | `get_ocr_client()` factory | `llm/factory.py` | [x] |
| 4 | `build_vision_extract_prompt()` | `prompts/extract_prompt.py` | [x] |
| 5 | `_collect_page_images()` helper | `routers/ingest.py` | [x] |
| 5 | Store `_page_images` in `pass1_json` at route time | `routers/ingest.py` | [x] |
| 5 | OCR gate in `_run_pipeline()` | `routers/ingest.py` | [x] |
| 5 | `_resolve_ocr_strategy()` | `routers/ingest.py` | [x] |
| 6 | `ocr_strategy` form param on ingest routes | `routers/ingest.py` | [x] |
| 6 | Remove 422 block for image uploads | `routers/ingest.py` | [x] |
| 7 | `page.get_pixmap()` fallback in `parse_pdf()` | `parsers/pdf_parser.py` | [x] |
| 8 | `test_deepseek_ocr_returns_text` | `tests/test_ocr.py` | [x] |
| 8 | `test_ollama_complete_vision` | `tests/test_ocr.py` | [x] |
| 8 | Pipeline gate tests (DeepSeek + Ollama paths) | `tests/test_ocr.py` | [x] |
| 8 | `ocr_strategy` param validation test | `tests/test_ingest_router.py` | [x] |
| 8 | Full test suite passes (`uv run pytest`) | — | [x] 197 passed, 2 skipped |
| 9 | Smoke test: DeepSeek path with real Docker | — | [ ] |
| 9 | Smoke test: Ollama VLM path with real model | — | [ ] |
| 9 | Smoke test: auto strategy resolution | — | [ ] |
| 9 | Verify text-layer PDFs unaffected | — | [ ] |
| 10 | `anatomy.md` updated | `.wolf/anatomy.md` | [x] auto-updated |
| 10 | `DEBUG_LOG.md` entry added | `DEBUG_LOG.md` | [x] |
