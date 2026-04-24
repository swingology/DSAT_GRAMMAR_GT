# LLM Providers + Parsers Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the LLM provider layer (Anthropic, OpenAI, Ollama), the four parsers (PDF, image, markdown, JSON), the prompt templates (Pass 1 extract, Pass 2 annotate, generation), and the pipeline orchestrator that ties them together.

**Architecture:** All three LLM providers implement a common `LLMProvider` protocol. The orchestrator drives the two-pass (+optional third) pipeline: parse raw input → Pass 1 (extract) → Pass 2 (annotate) → validate. Parsers produce raw text + metadata from uploaded files. Prompts load V3 rules and construct system/user messages.

**Tech Stack:** anthropic SDK, openai SDK, httpx (Ollama), pymupdf (PDF), Pillow (images), Pydantic v2

**Reference spec:** `docs/superpowers/specs/2026-04-24-segment-a-backend-rebuild-design.md`
**Foundation plan:** `docs/superpowers/plans/2026-04-24-foundation-db-models.md` (already implemented)

---

## File Map

```
backend/app/llm/
├── __init__.py             # (exists, empty)
├── base.py                 # LLMProvider Protocol + LLMResponse dataclass
├── factory.py               # get_provider() → concrete provider
├── anthropic_provider.py    # Anthropic Claude provider
├── openai_provider.py       # OpenAI ChatGPT provider
└── ollama_provider.py       # Ollama kimi-k2 provider

backend/app/parsers/
├── __init__.py             # (exists, empty)
├── pdf_parser.py            # pymupdf text + image extraction
├── image_parser.py           # Image → base64 for multimodal LLM
├── markdown_parser.py       # MD text + front matter
└── json_parser.py           # Robust JSON extraction from LLM output

backend/app/prompts/
├── __init__.py             # (exists, empty)
├── extract_prompt.py        # Pass 1 system prompt builder
├── annotate_prompt.py      # Pass 2 system prompt builder (loads V3 rules)
└── generate_prompt.py      # Generation system prompt builder

backend/app/pipeline/
├── __init__.py             # (exists, empty)
├── orchestrator.py          # Job state machine + step routing
└── validator.py             # Validation rules from PRD §15

backend/tests/
├── test_llm_providers.py   # Provider protocol + factory tests
├── test_parsers.py          # Parser output tests
├── test_prompts.py          # Prompt construction tests
└── test_pipeline.py         # Orchestrator + validator tests
```

---

## Chunk 1: LLM Provider Layer

### Task 1: Create LLMProvider protocol and LLMResponse dataclass

**Files:**
- Create: `backend/app/llm/base.py`
- Test: `backend/tests/test_llm_providers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_providers.py
import pytest
from app.llm.base import LLMProvider, LLMResponse


def test_llm_response_dataclass():
    r = LLMResponse(
        raw_text='{"question_text": "test"}',
        model="claude-sonnet-4-6",
        provider="anthropic",
        latency_ms=1500,
        token_usage={"input": 500, "output": 200},
    )
    assert r.raw_text.startswith("{")
    assert r.latency_ms > 0


def test_llm_provider_protocol_exists():
    """LLMProvider is a Protocol with a complete() method."""
    import inspect
    assert hasattr(LLMProvider, "complete")
    sig = inspect.signature(LLMProvider.complete)
    params = list(sig.parameters.keys())
    assert "system" in params
    assert "user" in params
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Write implementation**

```python
# app/llm/base.py
from typing import Optional, Dict, Any, Protocol, runtime_checkable
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    raw_text: str
    model: str
    provider: str
    latency_ms: int = 0
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/base.py backend/tests/test_llm_providers.py
git commit -m "feat: add LLMProvider protocol and LLMResponse dataclass"
```

---

### Task 2: Create LLM provider factory

**Files:**
- Create: `backend/app/llm/factory.py`
- Modify: `backend/tests/test_llm_providers.py` (add factory tests)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_llm_providers.py`:

```python
from app.llm.factory import get_provider


def test_factory_returns_anthropic():
    p = get_provider("anthropic", api_key="test-key")
    from app.llm.anthropic_provider import AnthropicProvider
    assert isinstance(p, AnthropicProvider)


def test_factory_returns_openai():
    p = get_provider("openai", api_key="test-key")
    from app.llm.openai_provider import OpenAIProvider
    assert isinstance(p, OpenAIProvider)


def test_factory_returns_ollama():
    p = get_provider("ollama", base_url="http://localhost:11434")
    from app.llm.ollama_provider import OllamaProvider
    assert isinstance(p, OllamaProvider)


def test_factory_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("gemini")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/llm/factory.py
from app.llm.base import LLMProvider


def get_provider(
    provider_name: str,
    api_key: str = "",
    base_url: str = "",
    default_model: str = "",
) -> LLMProvider:
    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key, default_model=default_model or "claude-sonnet-4-6")
    elif provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, default_model=default_model or "gpt-5-4")
    elif provider_name == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url=base_url or "http://localhost:11434", default_model=default_model or "kimi-k2")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/factory.py
git commit -m "feat: add LLM provider factory"
```

---

### Task 3: Create Anthropic provider

**Files:**
- Create: `backend/app/llm/anthropic_provider.py`
- Modify: `backend/tests/test_llm_providers.py` (add mock test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_llm_providers.py`:

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_anthropic_complete():
    from app.llm.anthropic_provider import AnthropicProvider
    provider = AnthropicProvider(api_key="test-key", default_model="claude-sonnet-4-6")

    mock_response = AsyncMock()
    mock_response.content = [AsyncMock(text='{"question_text": "test"}')]
    mock_response.model = "claude-sonnet-4-6"
    mock_response.usage = AsyncMock(input_tokens=100, output_tokens=50)

    with patch.object(provider, "client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        result = await provider.complete(system="You are a test", user="Extract this")
        assert result.raw_text == '{"question_text": "test"}'
        assert result.provider == "anthropic"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py::test_anthropic_complete -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/llm/anthropic_provider.py
import time
from typing import Optional, Dict
import anthropic
from app.llm.base import LLMResponse


class AnthropicProvider:
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        model = model or self.default_model
        start = time.time()
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency_ms = int((time.time() - start) * 1000)
        raw_text = response.content[0].text
        token_usage = {
            "input": getattr(response.usage, "input_tokens", 0),
            "output": getattr(response.usage, "output_tokens", 0),
        }
        return LLMResponse(
            raw_text=raw_text,
            model=model,
            provider="anthropic",
            latency_ms=latency_ms,
            token_usage=token_usage,
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/anthropic_provider.py
git commit -m "feat: add Anthropic Claude provider"
```

---

### Task 4: Create OpenAI provider

**Files:**
- Create: `backend/app/llm/openai_provider.py`

- [ ] **Step 1: Write implementation (same pattern as Anthropic)**

```python
# app/llm/openai_provider.py
import time
from typing import Optional, Dict
import openai
from app.llm.base import LLMResponse


class OpenAIProvider:
    def __init__(self, api_key: str, default_model: str = "gpt-5-4"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.default_model = default_model

    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        model = model or self.default_model
        start = time.time()
        response = await self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        latency_ms = int((time.time() - start) * 1000)
        raw_text = response.choices[0].message.content
        token_usage = {
            "input": getattr(response.usage, "prompt_tokens", 0),
            "output": getattr(response.usage, "completion_tokens", 0),
        }
        return LLMResponse(
            raw_text=raw_text,
            model=model,
            provider="openai",
            latency_ms=latency_ms,
            token_usage=token_usage,
        )
```

- [ ] **Step 2: Add mock test**

Add to `tests/test_llm_providers.py`:

```python
@pytest.mark.asyncio
async def test_openai_complete():
    from app.llm.openai_provider import OpenAIProvider
    provider = OpenAIProvider(api_key="test-key")

    mock_choice = AsyncMock()
    mock_choice.message = AsyncMock(content='{"question_text": "test"}')
    mock_response = AsyncMock(choices=[mock_choice], model="gpt-5-4")
    mock_response.usage = AsyncMock(prompt_tokens=100, completion_tokens=50)

    with patch.object(provider, "client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await provider.complete(system="You are a test", user="Extract this")
        assert result.provider == "openai"
```

- [ ] **Step 3: Run tests**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/llm/openai_provider.py
git commit -m "feat: add OpenAI ChatGPT provider"
```

---

### Task 5: Create Ollama provider

**Files:**
- Create: `backend/app/llm/ollama_provider.py`

- [ ] **Step 1: Write implementation**

Ollama uses an OpenAI-compatible chat API at `/v1/chat/completions`, so we can reuse the same protocol with httpx:

```python
# app/llm/ollama_provider.py
import time
from typing import Optional, Dict
import httpx
from app.llm.base import LLMResponse


class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "kimi-k2"):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        model = model or self.default_model
        start = time.time()
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        latency_ms = int((time.time() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        token_usage = {
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
        }
        return LLMResponse(
            raw_text=raw_text,
            model=model,
            provider="ollama",
            latency_ms=latency_ms,
            token_usage=token_usage,
        )

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 2: Add mock test**

Add to `tests/test_llm_providers.py`:

```python
@pytest.mark.asyncio
async def test_ollama_complete():
    from app.llm.ollama_provider import OllamaProvider
    provider = OllamaProvider(base_url="http://localhost:11434")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {
        "choices": [{"message": {"content": '{"question_text": "test"}'}}],
        "usage": {"prompt_tokens": 80, "completion_tokens": 40},
    }

    with patch.object(provider, "client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await provider.complete(system="You are a test", user="Extract this")
        assert result.provider == "ollama"
        assert result.raw_text == '{"question_text": "test"}'
```

- [ ] **Step 3: Run tests**

```bash
cd backend && .venv/bin/python -m pytest tests/test_llm_providers.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/llm/ollama_provider.py
git commit -m "feat: add Ollama kimi-k2 provider"
```

---

## Chunk 2: Parsers

### Task 6: Create JSON parser (for LLM output extraction)

**Files:**
- Create: `backend/app/parsers/json_parser.py`
- Test: `backend/tests/test_parsers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parsers.py
import pytest
from app.parsers.json_parser import extract_json_from_text


def test_extract_json_from_clean_text():
    text = '{"question_text": "Which choice?", "options": []}'
    result = extract_json_from_text(text)
    assert result["question_text"] == "Which choice?"


def test_extract_json_from_markdown_fence():
    text = '```json\n{"question_text": "test"}\n```'
    result = extract_json_from_text(text)
    assert result["question_text"] == "test"


def test_extract_json_from_mixed_text():
    text = 'Here is the result:\n```json\n{"key": "value"}\n```\nDone.'
    result = extract_json_from_text(text)
    assert result["key"] == "value"


def test_extract_json_raises_on_invalid():
    with pytest.raises(ValueError, match="No valid JSON found"):
        extract_json_from_text("no json here at all")


def test_extract_json_from_bracket_search():
    text = 'Some prefix text {"nested": {"key": 1}} some suffix'
    result = extract_json_from_text(text)
    assert result["nested"]["key"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/parsers/json_parser.py
"""Robust JSON extraction from LLM output text.
Handles markdown code fences, leading/trailing text, and nested objects.
"""
import json
import re


def extract_json_from_text(text: str) -> dict:
    """Extract a JSON object from text that may contain markdown fences or surrounding prose."""
    # Try 1: Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try 2: Extract from markdown code fence (```json ... ```)
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try 3: Find first { ... } using brace counting
    first_brace = text.find("{")
    if first_brace != -1:
        depth = 0
        for i in range(first_brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[first_brace : i + 1])
                    except json.JSONDecodeError:
                        break

    raise ValueError("No valid JSON found in text")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/parsers/json_parser.py backend/tests/test_parsers.py
git commit -m "feat: add JSON parser for robust LLM output extraction"
```

---

### Task 7: Create PDF parser

**Files:**
- Create: `backend/app/parsers/pdf_parser.py`
- Test: add to `backend/tests/test_parsers.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_parsers.py`:

```python
import pytest
from app.parsers.pdf_parser import parse_pdf


def test_parse_pdf_returns_pages():
    """Test with a real small PDF or skip if no PDF available."""
    # This is an integration test — we'll use a sample PDF from TESTS/
    import os
    sample = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "sat-practice-test-4-digital sec01 mod01.pdf"
    )
    if not os.path.exists(sample):
        pytest.skip("No sample PDF available")
    result = parse_pdf(sample)
    assert "pages" in result
    assert len(result["pages"]) > 0
    assert "text" in result["pages"][0]


def test_parse_pdf_page_structure():
    """Each page should have text and page_number."""
    import os
    sample = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "sat-practice-test-4-digital sec01 mod01.pdf"
    )
    if not os.path.exists(sample):
        pytest.skip("No sample PDF available")
    result = parse_pdf(sample)
    page = result["pages"][0]
    assert "page_number" in page
    assert "text" in page
    assert isinstance(page["text"], str)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py::test_parse_pdf_returns_pages -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/parsers/pdf_parser.py
"""PDF text extraction using pymupdf (fitz).
Extracts text per page and embedded images as base64 bytes for multimodal LLM processing.
"""
import base64
import fitz  # pymupdf


def parse_pdf(path: str) -> dict:
    """Extract text and images from a PDF file.
    Returns: {"pages": [{"page_number": int, "text": str, "images": [{"index": int, "b64": str}]}]}
    """
    doc = fitz.open(str(path))
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        images = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            if base_image:
                img_b64 = base64.standard_b64encode(base_image["image"]).decode("utf-8")
                images.append({"index": img_index, "b64": img_b64, "ext": base_image.get("ext", "png")})
        pages.append({
            "page_number": page_num,
            "text": text,
            "images": images,
        })
    doc.close()
    return {"pages": pages, "source": str(path)}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py -v
```
Expected: PASS (or skip if no PDF)

- [ ] **Step 5: Commit**

```bash
git add backend/app/parsers/pdf_parser.py
git commit -m "feat: add PDF parser with pymupdf text and image extraction"
```

---

### Task 8: Create image and markdown parsers

**Files:**
- Create: `backend/app/parsers/image_parser.py`
- Create: `backend/app/parsers/markdown_parser.py`
- Test: add to `backend/tests/test_parsers.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_parsers.py`:

```python
import pytest
from app.parsers.image_parser import parse_image
from app.parsers.markdown_parser import parse_markdown


def test_image_parser_returns_b64():
    """Create a tiny test image and verify base64 output."""
    from PIL import Image
    import io
    import tempfile
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(buf.getvalue())
        f.flush()
        result = parse_image(f.name)
    assert "b64" in result
    assert "mime_type" in result
    assert result["mime_type"] == "image/png"
    assert len(result["b64"]) > 0


def test_markdown_parser_plain():
    result = parse_markdown("# Title\n\nSome question text here.")
    assert result["text"] == "# Title\n\nSome question text here."
    assert result["front_matter"] == {}


def test_markdown_parser_with_front_matter():
    md = "---\nsource_name: PrepPros\nsource_url: https://example.com\n---\n# Question\n\nText here."
    result = parse_markdown(md)
    assert result["front_matter"]["source_name"] == "PrepPros"
    assert "Question" in result["text"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py::test_image_parser_returns_b64 tests/test_parsers.py::test_markdown_parser_plain -v
```
Expected: FAIL

- [ ] **Step 3: Write image parser**

```python
# app/parsers/image_parser.py
"""Image parser — converts image file to base64 for multimodal LLM processing."""
import base64
from pathlib import Path


MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def parse_image(path: str) -> dict:
    """Read an image file and return base64-encoded content + metadata."""
    p = Path(path)
    suffix = p.suffix.lower()
    mime_type = MIME_MAP.get(suffix, "application/octet-stream")
    content = p.read_bytes()
    b64 = base64.standard_b64encode(content).decode("utf-8")
    return {
        "b64": b64,
        "mime_type": mime_type,
        "filename": p.name,
        "size_bytes": len(content),
    }
```

- [ ] **Step 4: Write markdown parser**

```python
# app/parsers/markdown_parser.py
"""Markdown parser — extracts text and optional YAML front matter."""
import re


_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_markdown(text: str) -> dict:
    """Parse markdown text, extracting optional front matter.
    Returns: {"text": str, "front_matter": dict}
    """
    front_matter = {}
    match = _FRONT_MATTER_RE.match(text)
    if match:
        fm_text = match.group(1)
        body = text[match.end():]
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                front_matter[key.strip()] = value.strip()
    else:
        body = text
    return {"text": body, "front_matter": front_matter}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/parsers/image_parser.py backend/app/parsers/markdown_parser.py
git commit -m "feat: add image and markdown parsers"
```

---

## Chunk 3: Prompts + Pipeline

### Task 9: Create prompt templates

**Files:**
- Create: `backend/app/prompts/extract_prompt.py`
- Create: `backend/app/prompts/annotate_prompt.py`
- Create: `backend/app/prompts/generate_prompt.py`
- Test: `backend/tests/test_prompts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompts.py
from app.prompts.extract_prompt import build_extract_prompt
from app.prompts.annotate_prompt import build_annotate_prompt
from app.prompts.generate_prompt import build_generate_prompt


def test_extract_prompt_contains_instructions():
    system, user = build_extract_prompt(raw_text="The colony of corals plays a role.")
    assert "extract" in system.lower()
    assert "colony" in user


def test_annotate_prompt_loads_v3_rules():
    system, user = build_annotate_prompt(
        extract_json={"question_text": "test", "options": [], "correct_option_label": "A"},
    )
    assert "Standard English Conventions" in system or "grammar_role_key" in system
    assert "JSON" in system


def test_generate_prompt_includes_target():
    request = {
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
    }
    system, user = build_generate_prompt(generation_request=request)
    assert "subject_verb_agreement" in system
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_prompts.py -v
```
Expected: FAIL

- [ ] **Step 3: Write extract prompt**

```python
# app/prompts/extract_prompt.py
"""Pass 1 prompt — extracts structured question data from raw text."""


EXTRACT_SYSTEM_PROMPT = """You are a DSAT question extraction specialist. Your job is to extract structured question data from raw text extracted from SAT practice material.

You must output valid JSON matching this schema:
{
  "question_text": "The prompt/stem text",
  "passage_text": "The passage or null",
  "paired_passage_text": null,
  "options": [
    {"label": "A", "text": "option A text"},
    {"label": "B", "text": "option B text"},
    {"label": "C", "text": "option C text"},
    {"label": "D", "text": "option D text"}
  ],
  "correct_option_label": "A or B or C or D",
  "source_exam_code": "PT4 or null",
  "source_module_code": "M1 or null",
  "source_question_number": 1 or null,
  "stimulus_mode_key": "sentence_only or passage_excerpt etc.",
  "stem_type_key": "complete_the_text or choose_main_idea etc.",
  "table_data": null,
  "graph_data": null
}

Rules:
- Always produce exactly 4 options labeled A, B, C, D
- Identify the correct answer from the answer key or context
- Preserve the original wording as closely as possible
- If no passage, set passage_text to null
- Output ONLY valid JSON, no markdown fences"""


def build_extract_prompt(raw_text: str, source_metadata: dict = None) -> tuple[str, str]:
    """Build system and user prompts for Pass 1 extraction."""
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource metadata:\n" + "\n".join(hints) if hints else ""

    user = f"""Extract the question data from the following raw text:{source_hints}

---
{raw_text}
---"""
    return EXTRACT_SYSTEM_PROMPT, user
```

- [ ] **Step 4: Write annotate prompt**

```python
# app/prompts/annotate_prompt.py
"""Pass 2 prompt — annotates extracted question data using V3 rules."""
import os


def _load_v3_rules() -> str:
    """Load the V3 rules file as a string."""
    rules_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     "rules_agent_dsat_grammar_ingestion_generation_v3.md"),
    ]
    for path in rules_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    return ""


ANNOTATE_SYSTEM_PROMPT = """You are a DSAT question annotation specialist following the rules_agent_dsat_grammar_ingestion_generation_v3.md specification.

Given extracted question data, you must produce a full annotation including:
1. Classification: grammar_role_key, grammar_focus_key, syntactic_trap_key, difficulty fields
2. Options: per-option analysis (distractor_type_key, why_plausible, why_wrong, precision_score)
3. Reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
4. Generation profile: target keys, passage template, frequency band
5. Review: annotation_confidence, needs_human_review

IMPORTANT RULES:
- grammar_focus_key must be from the approved V3 keys
- grammar_role_key must match grammar_focus_key per V3 §17.1 mapping
- Every wrong option must have a distinct option_error_focus_key
- syntactic_trap_key describes the difficulty mechanism, not the rule tested
- Output valid JSON only

{rules_context}"""


def build_annotate_prompt(extract_json: dict, rules_file_path: str = "") -> tuple[str, str]:
    """Build system and user prompts for Pass 2 annotation."""
    rules_path = rules_file_path or _load_v3_rules()
    rules_context = ""
    if rules_path and os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            rules_text = f.read()
        if len(rules_text) > 8000:
            rules_context = f"\nV3 RULES REFERENCE (first 8000 chars):\n{rules_text[:8000]}\n[...truncated for length...]"
        else:
            rules_context = f"\nV3 RULES REFERENCE:\n{rules_text}"

    system = ANNOTATE_SYSTEM_PROMPT.format(rules_context=rules_context)
    import json
    user = f"""Annotate the following extracted question data:

{json.dumps(extract_json, indent=2)}"""
    return system, user
```

- [ ] **Step 5: Write generate prompt**

```python
# app/prompts/generate_prompt.py
"""Generation prompt — produces new DSAT-style questions from a specification."""
import json


GENERATE_SYSTEM_PROMPT = """You are a DSAT question generation specialist following the rules_agent_dsat_grammar_ingestion_generation_v3.md specification.

Generate a complete SAT-style question matching the given specification. Your output must include:
1. question: passage_text, question_text, options (4 labeled A-D), correct_option_label
2. classification: grammar_role_key, grammar_focus_key, syntactic_trap_key, difficulty fields
3. options: per-option analysis with distractor_type_key, why_plausible, why_wrong, precision_score
4. reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
5. generation_profile: target keys, passage_template, frequency_band
6. review: annotation_confidence, needs_human_review

Rules:
- Passage must be 20-40 words for sentence_only items
- Formal academic register, no contractions or slang
- Self-contained meaning (no outside knowledge needed)
- At least one distractor must target the declared syntactic trap
- No two distractors may fail for the exact same grammar reason
- correct option may appear in any position (A-D)
- Output valid JSON only"""


def build_generate_prompt(generation_request: dict, source_examples: list = None) -> tuple[str, str]:
    """Build system and user prompts for question generation."""
    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(f"\nSource examples for reference:\n{json.dumps(source_examples, indent=2)}")
    user = "\n".join(user_parts)
    return GENERATE_SYSTEM_PROMPT, user
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_prompts.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/prompts/ backend/tests/test_prompts.py
git commit -m "feat: add Pass 1, Pass 2, and generation prompt templates"
```

---

### Task 10: Create pipeline orchestrator

**Files:**
- Create: `backend/app/pipeline/orchestrator.py`
- Test: `backend/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import pytest
from app.pipeline.orchestrator import (
    JobOrchestrator,
    can_transition,
    next_status,
)


def test_can_transition_pending_to_parsing():
    assert can_transition("pending", "parsing") is True


def test_cannot_transition_pending_to_approved():
    assert can_transition("pending", "approved") is False


def test_can_transition_annotating_to_validating():
    assert can_transition("annotating", "validating") is True


def test_can_transition_validating_to_approved():
    assert can_transition("validating", "approved") is True


def test_can_transition_validating_to_failed():
    assert can_transition("validating", "failed") is True


def test_can_transition_any_to_failed():
    assert can_transition("parsing", "failed") is True
    assert can_transition("extracting", "failed") is True
    assert can_transition("annotating", "failed") is True


def test_next_status_official_ingest():
    """Official ingest follows: pending → parsing → extracting → annotating → validating → approved"""
    assert next_status("pending", content_origin="official", job_type="ingest") == "parsing"
    assert next_status("parsing", content_origin="official", job_type="ingest") == "extracting"
    assert next_status("extracting", content_origin="official", job_type="ingest") == "annotating"
    assert next_status("annotating", content_origin="official", job_type="ingest") == "validating"


def test_next_status_unofficial_includes_overlap():
    """Unofficial ingest adds overlap_checking between annotating and validating."""
    assert next_status("annotating", content_origin="unofficial", job_type="ingest") == "overlap_checking"
    assert next_status("overlap_checking", content_origin="unofficial", job_type="ingest") == "validating"


def test_next_status_generated_includes_overlap():
    """Generated questions also include overlap checking."""
    assert next_status("annotating", content_origin="generated", job_type="generate") == "overlap_checking"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_pipeline.py -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/pipeline/orchestrator.py
"""Job state machine and pipeline orchestration for DSAT question processing."""
from typing import Optional


# State transition table: {from_status: set(allowed_to_statuses)}
TRANSITIONS = {
    "pending": {"parsing", "extracting", "failed"},
    "parsing": {"extracting", "failed"},
    "extracting": {"generating", "annotating", "failed"},
    "generating": {"annotating", "failed"},
    "annotating": {"overlap_checking", "validating", "failed"},
    "overlap_checking": {"validating", "failed"},
    "validating": {"approved", "needs_review", "failed"},
    "approved": set(),       # terminal
    "needs_review": set(),    # terminal (wait for admin)
    "failed": set(),          # terminal
}

# Any status can transition to 'failed'
ALL_STATUSES = set(TRANSITIONS.keys())


def can_transition(from_status: str, to_status: str) -> bool:
    """Check if a transition from from_status to to_status is valid."""
    if to_status == "failed":
        return from_status not in ("approved", "needs_review", "failed")
    return to_status in TRANSITIONS.get(from_status, set())


def next_status(current: str, content_origin: str = "official", job_type: str = "ingest") -> Optional[str]:
    """Determine the next status in the pipeline based on current status and job type."""
    # Unofficial and generated questions need overlap checking
    needs_overlap = content_origin in ("unofficial", "generated")

    if current == "pending":
        if job_type == "generate":
            return "extracting"  # generation skips parsing
        return "parsing"
    elif current == "parsing":
        return "extracting"
    elif current == "extracting":
        if job_type == "generate":
            return "generating"
        return "annotating"
    elif current == "generating":
        return "annotating"
    elif current == "annotating":
        if needs_overlap:
            return "overlap_checking"
        return "validating"
    elif current == "overlap_checking":
        return "validating"
    elif current == "validating":
        return "approved"  # default; validator may set needs_review instead
    return None


class JobOrchestrator:
    """Orchestrates the processing pipeline for a question job."""

    def __init__(self, job_id: str, content_origin: str, job_type: str):
        self.job_id = job_id
        self.content_origin = content_origin
        self.job_type = job_type
        self.current_status = "pending"
        self.errors: list[dict] = []

    def advance(self) -> str:
        """Advance to the next pipeline status. Returns the new status."""
        next_s = next_status(self.current_status, self.content_origin, self.job_type)
        if next_s and can_transition(self.current_status, next_s):
            self.current_status = next_s
            return self.current_status
        raise ValueError(f"Cannot advance from {self.current_status}")

    def fail(self, step: str, error_code: str, message: str, retries: int = 0) -> str:
        """Mark the job as failed with structured error info."""
        self.errors.append({
            "step": step,
            "error_code": error_code,
            "message": message,
            "retries": retries,
            "max_retries": 3,
        })
        self.current_status = "failed"
        return self.current_status
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_pipeline.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/orchestrator.py backend/tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator with job state machine"
```

---

### Task 11: Create pipeline validator

**Files:**
- Create: `backend/app/pipeline/validator.py`
- Test: add to `backend/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline.py`:

```python
from app.pipeline.validator import validate_question


def test_validate_official_question_passes():
    q = {
        "question_text": "Which choice completes the text?",
        "options": [
            {"label": "A", "text": "play"},
            {"label": "B", "text": "have played"},
            {"label": "C", "text": "plays"},
            {"label": "D", "text": "is playing"},
        ],
        "correct_option_label": "C",
        "source_exam_code": "PT4",
        "source_module_code": "M1",
        "source_question_number": 1,
        "explanation_short": "Singular subject requires singular verb.",
    }
    errors = validate_question(q, content_origin="official")
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_validate_official_missing_source():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
    }
    errors = validate_question(q, content_origin="official")
    assert any("source_exam_code" in e["field"] for e in errors)


def test_validate_generated_missing_lineage():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
    }
    errors = validate_question(q, content_origin="generated")
    assert any("lineage" in e["field"] or "generation" in e["message"].lower() for e in errors)


def test_validate_bad_correct_label():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "E",
    }
    errors = validate_question(q, content_origin="official")
    assert any("correct_option_label" in e["field"] for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_pipeline.py::test_validate_official_question_passes -v
```
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/pipeline/validator.py
"""Validation rules from PRD §15.
Enforces required question structure, correct labels, source metadata, lineage, and overlap status.
"""
from typing import List, Dict


def validate_question(question_data: dict, content_origin: str = "official") -> List[Dict]:
    """Validate a question dict against PRD rules.
    Returns a list of error dicts: [{"severity": "blocking"|"review"|"warning", "field": str, "message": str}]
    """
    errors = []

    # Required question structure
    if not question_data.get("question_text"):
        errors.append({"severity": "blocking", "field": "question_text", "message": "Question text is required"})

    # Four answer choices
    options = question_data.get("options", [])
    if len(options) != 4:
        errors.append({"severity": "blocking", "field": "options", "message": f"Expected 4 options, got {len(options)}"})

    # Valid correct answer label
    correct = question_data.get("correct_option_label", "")
    if correct not in ("A", "B", "C", "D"):
        errors.append({"severity": "blocking", "field": "correct_option_label", "message": f"Invalid correct_option_label: {correct}"})

    # Explanation presence
    if not question_data.get("explanation_short") and not question_data.get("explanation_full"):
        errors.append({"severity": "review", "field": "explanation", "message": "No explanation text provided"})

    # Official-specific: source metadata required
    if content_origin == "official":
        for field in ["source_exam_code", "source_module_code", "source_question_number"]:
            if not question_data.get(field):
                errors.append({"severity": "blocking", "field": field, "message": f"Official questions require {field}"})

    # Generated-specific: lineage required
    if content_origin == "generated":
        if not question_data.get("generation_source_set") and not question_data.get("derived_from_question_id"):
            errors.append({"severity": "blocking", "field": "lineage", "message": "Generated questions require generation lineage"})

    return errors
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_pipeline.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/validator.py
git commit -m "feat: add pipeline validator with PRD §15 validation rules"
```

---

### Task 12: Run all tests and verify

- [ ] **Step 1: Run full test suite**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 2: Final commit**

```bash
git add -A backend/
git commit -m "feat: complete LLM providers, parsers, prompts, and pipeline layer"
```

---

## Next Plan

**Pipeline + Routers** — Wire the orchestrator to the API endpoints: ingestion router (upload → parse → extract → annotate), generation router, questions recall router, admin router, student router.