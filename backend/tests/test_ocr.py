"""Unit tests for OCR providers: DeepSeekOCRClient and OllamaProvider.complete_vision()."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.parsers.ocr import DeepSeekOCRClient
from app.llm.base import ImageContent, LLMResponse
from app.llm.ollama_provider import OllamaProvider
from app.prompts.extract_prompt import build_vision_extract_prompt
from app.routers.ingest import (
    _build_ocr_chain,
    _collect_page_image_entries,
    _collect_page_images,
    _ocr_page_concurrency,
    _resolve_ocr_strategy,
    _run_pagewise_deepseek_ocr,
    _run_pagewise_vision_ocr,
    _strategy_image_entries,
)


# ── DeepSeekOCRClient ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deepseek_ocr_returns_text():
    client = DeepSeekOCRClient(base_url="http://localhost:8001", model="deepseek-ai/DeepSeek-OCR-2")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Question 1: What is the main idea?"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    with patch.object(client.client, "post", new_callable=AsyncMock, return_value=mock_response):
        images = [ImageContent(b64="abc123", mime_type="image/png")]
        result = await client.extract(images)

    assert result.raw_text == "Question 1: What is the main idea?"
    assert result.provider == "deepseek_ocr"
    assert result.model == "deepseek-ai/DeepSeek-OCR-2"
    assert result.token_usage == {"input": 100, "output": 50}


@pytest.mark.asyncio
async def test_deepseek_ocr_sends_image_url_block():
    client = DeepSeekOCRClient(base_url="http://localhost:8001", model="deepseek-ai/DeepSeek-OCR-2")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "extracted text"}}],
        "usage": {},
    }
    with patch.object(client.client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        images = [ImageContent(b64="abc", mime_type="image/jpeg")]
        await client.extract(images)

    call_json = mock_post.call_args.kwargs["json"]
    user_content = call_json["messages"][1]["content"]
    image_blocks = [c for c in user_content if c.get("type") == "image_url"]
    assert len(image_blocks) == 1
    assert "data:image/jpeg;base64,abc" in image_blocks[0]["image_url"]["url"]


# ── OllamaProvider.complete_vision ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_ollama_complete_vision_returns_response():
    provider = OllamaProvider(base_url="http://localhost:11434", default_model="qwen2.5-vl:7b")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"questions": []}'}}],
        "usage": {"prompt_tokens": 200, "completion_tokens": 10},
    }
    with patch.object(provider.vision_client, "post", new_callable=AsyncMock, return_value=mock_response):
        images = [ImageContent(b64="abc", mime_type="image/jpeg")]
        result = await provider.complete_vision("system prompt", "user prompt", images)

    assert result.provider == "ollama"
    assert result.raw_text == '{"questions": []}'


@pytest.mark.asyncio
async def test_ollama_complete_vision_sends_image_url_blocks():
    provider = OllamaProvider(base_url="http://localhost:11434", default_model="qwen2.5-vl:7b")
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "{}"}}],
        "usage": {},
    }
    with patch.object(provider.vision_client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        images = [
            ImageContent(b64="aaa", mime_type="image/png"),
            ImageContent(b64="bbb", mime_type="image/jpeg"),
        ]
        await provider.complete_vision("sys", "user", images)

    call_json = mock_post.call_args.kwargs["json"]
    user_content = call_json["messages"][1]["content"]
    image_blocks = [c for c in user_content if c.get("type") == "image_url"]
    assert len(image_blocks) == 2
    # Images come before the text block
    text_block = next(c for c in user_content if c.get("type") == "text")
    assert user_content.index(text_block) > user_content.index(image_blocks[0])


# ── Helper functions ──────────────────────────────────────────────────────────

def test_collect_page_images_returns_image_content():
    pass1_json = {
        "_page_images": [
            {"b64": "abc", "mime_type": "image/png", "page_number": 0},
            {"b64": "def", "mime_type": "image/jpeg", "page_number": 1},
        ]
    }
    images = _collect_page_images(pass1_json)
    assert len(images) == 2
    assert images[0].b64 == "abc"
    assert images[0].mime_type == "image/png"
    assert images[1].mime_type == "image/jpeg"


def test_collect_page_image_entries_preserves_page_numbers():
    pass1_json = {
        "_page_images": [
            {"b64": "abc", "mime_type": "image/png", "page_number": 7},
        ]
    }

    entries = _collect_page_image_entries(pass1_json)

    assert len(entries) == 1
    assert entries[0]["page_number"] == 7
    assert entries[0]["image"].b64 == "abc"


def test_collect_page_images_skips_empty_b64():
    pass1_json = {
        "_page_images": [
            {"b64": "", "mime_type": "image/png"},
            {"b64": "real", "mime_type": "image/png"},
        ]
    }
    images = _collect_page_images(pass1_json)
    assert len(images) == 1
    assert images[0].b64 == "real"


def test_collect_page_images_handles_none():
    assert _collect_page_images(None) == []
    assert _collect_page_images({}) == []


def test_strategy_image_entries_only_caps_vlm_fused_strategies():
    settings = SimpleNamespace(vision_max_images=2)
    entries = [{"image": object(), "page_number": i} for i in range(5)]

    assert _strategy_image_entries("glm", entries, settings) == entries
    assert _strategy_image_entries("deepseek", entries, settings) == entries
    assert _strategy_image_entries("ollama", entries, settings) == entries[:2]
    assert _strategy_image_entries("anthropic", entries, settings) == entries[:2]


@pytest.mark.asyncio
async def test_run_pagewise_vision_ocr_sends_one_image_per_request():
    provider = MagicMock()
    provider.complete_vision = AsyncMock(side_effect=[
        LLMResponse(
            raw_text="page one text",
            model="glm",
            provider="ollama",
            latency_ms=10,
            token_usage={"input": 1, "output": 2},
        ),
        LLMResponse(
            raw_text="page two text",
            model="glm",
            provider="ollama",
            latency_ms=20,
            token_usage={"input": 3, "output": 4},
        ),
    ])
    entries = [
        {"image": ImageContent(b64="one", mime_type="image/png"), "page_number": 0},
        {"image": ImageContent(b64="two", mime_type="image/png"), "page_number": 1},
    ]

    result = await _run_pagewise_vision_ocr(
        provider,
        image_entries=entries,
        system="sys",
        user="user",
        model="glm-ocr:latest",
        max_tokens=4096,
    )

    assert result["raw_text"] == "--- Page 1 ---\npage one text\n\n--- Page 2 ---\npage two text"
    assert result["latency_ms"] == 30
    assert result["token_usage"] == {"input": 4, "output": 6}
    assert provider.complete_vision.await_count == 2
    for call in provider.complete_vision.await_args_list:
        assert len(call.kwargs["images"]) == 1


@pytest.mark.asyncio
async def test_run_pagewise_vision_ocr_caps_async_concurrency():
    active = 0
    max_active = 0

    async def complete_vision(**kwargs):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return LLMResponse(
            raw_text=f"text {kwargs['images'][0].b64}",
            model="glm",
            provider="ollama",
            latency_ms=5,
            token_usage={"input": 1, "output": 1},
        )

    provider = MagicMock()
    provider.complete_vision = AsyncMock(side_effect=complete_vision)
    entries = [
        {"image": ImageContent(b64=str(i), mime_type="image/png"), "page_number": i}
        for i in range(6)
    ]

    result = await _run_pagewise_vision_ocr(
        provider,
        image_entries=entries,
        system="sys",
        user="user",
        model="glm-ocr:latest",
        max_tokens=4096,
        max_concurrency=99,
    )

    assert max_active == 3
    assert provider.complete_vision.await_count == 6
    assert result["raw_text"].startswith("--- Page 1 ---\ntext 0")
    assert "--- Page 6 ---\ntext 5" in result["raw_text"]


@pytest.mark.asyncio
async def test_run_pagewise_vision_ocr_retries_blank_pages_sequentially():
    provider = MagicMock()
    provider.complete_vision = AsyncMock(side_effect=[
        LLMResponse(
            raw_text="",
            model="glm",
            provider="ollama",
            latency_ms=10,
            token_usage={"input": 1, "output": 1},
        ),
        LLMResponse(
            raw_text="page two text",
            model="glm",
            provider="ollama",
            latency_ms=10,
            token_usage={"input": 1, "output": 1},
        ),
        LLMResponse(
            raw_text="page one retry text",
            model="glm",
            provider="ollama",
            latency_ms=10,
            token_usage={"input": 1, "output": 1},
        ),
    ])
    entries = [
        {"image": ImageContent(b64="one", mime_type="image/png"), "page_number": 0},
        {"image": ImageContent(b64="two", mime_type="image/png"), "page_number": 1},
    ]

    result = await _run_pagewise_vision_ocr(
        provider,
        image_entries=entries,
        system="sys",
        user="user",
        model="glm-ocr:latest",
        max_tokens=4096,
        max_concurrency=2,
    )

    assert provider.complete_vision.await_count == 3
    assert result["pages"][0]["attempt"] == 2
    assert result["raw_text"] == "--- Page 1 ---\npage one retry text\n\n--- Page 2 ---\npage two text"


@pytest.mark.asyncio
async def test_run_pagewise_deepseek_ocr_sends_one_image_per_request():
    client = MagicMock()
    client.extract = AsyncMock(side_effect=[
        LLMResponse(
            raw_text="page one text",
            model="deepseek",
            provider="deepseek_ocr",
            latency_ms=10,
            token_usage={"input": 1, "output": 2},
        ),
        LLMResponse(
            raw_text="page two text",
            model="deepseek",
            provider="deepseek_ocr",
            latency_ms=20,
            token_usage={"input": 3, "output": 4},
        ),
    ])
    entries = [
        {"image": ImageContent(b64="one", mime_type="image/png"), "page_number": 0},
        {"image": ImageContent(b64="two", mime_type="image/png"), "page_number": 1},
    ]

    result = await _run_pagewise_deepseek_ocr(
        client,
        image_entries=entries,
        max_concurrency=3,
    )

    assert result["raw_text"] == "--- Page 1 ---\npage one text\n\n--- Page 2 ---\npage two text"
    assert result["latency_ms"] == 30
    assert result["token_usage"] == {"input": 4, "output": 6}
    assert client.extract.await_count == 2
    for call in client.extract.await_args_list:
        assert len(call.args[0]) == 1


def test_ocr_page_concurrency_defaults_and_caps_at_three():
    assert _ocr_page_concurrency(SimpleNamespace()) == 3
    assert _ocr_page_concurrency(SimpleNamespace(ocr_page_concurrency=0)) == 1
    assert _ocr_page_concurrency(SimpleNamespace(ocr_page_concurrency=2)) == 2
    assert _ocr_page_concurrency(SimpleNamespace(ocr_page_concurrency=8)) == 3


def test_resolve_ocr_strategy_explicit():
    class FakeSettings:
        ocr_strategy = "auto"
        ocr_vision_provider = "ollama"
        deepseek_ocr_base_url = "http://localhost:8001"

    s = FakeSettings()
    assert _resolve_ocr_strategy("deepseek", s) == "deepseek"
    assert _resolve_ocr_strategy("ollama", s) == "ollama"
    assert _resolve_ocr_strategy("vision", s) == "ollama"


def test_resolve_ocr_strategy_auto_prefers_glm():
    class FakeSettings:
        ocr_strategy = "auto"
        glm_ocr_model = "glm-ocr:latest"
        ocr_vision_provider = "ollama"
        deepseek_ocr_base_url = "http://localhost:8001"

    assert _resolve_ocr_strategy(None, FakeSettings()) == "glm"


def test_resolve_ocr_strategy_explicit_glm():
    class FakeSettings:
        ocr_strategy = "auto"
        glm_ocr_model = "glm-ocr:latest"
        ocr_vision_provider = "none"
        deepseek_ocr_base_url = ""

    assert _resolve_ocr_strategy("glm", FakeSettings()) == "glm"


def test_resolve_ocr_strategy_auto_falls_back_to_deepseek():
    class FakeSettings:
        ocr_strategy = "auto"
        glm_ocr_model = ""
        ocr_vision_provider = "none"
        deepseek_ocr_base_url = "http://localhost:8001"

    assert _resolve_ocr_strategy(None, FakeSettings()) == "deepseek"


def test_resolve_ocr_strategy_auto_falls_back_to_ollama():
    class FakeSettings:
        ocr_strategy = "auto"
        glm_ocr_model = ""
        ocr_vision_provider = "ollama"
        deepseek_ocr_base_url = ""

    assert _resolve_ocr_strategy(None, FakeSettings()) == "ollama"


def test_build_ocr_chain_prefers_two_step_before_vlm():
    class FakeSettings:
        ocr_fallback = True
        glm_ocr_model = "glm-ocr:latest"
        deepseek_ocr_base_url = "http://localhost:8001"
        ocr_vision_provider = "ollama"
        ollama_base_url = "http://localhost:11434"
        anthropic_api_key = "test-key"
        openai_api_key = ""

    # Resolved strategy runs first; fallbacks prefer two-step (glm/deepseek)
    # over VLM-fused (anthropic/ollama/openai).
    assert _build_ocr_chain("ollama", FakeSettings()) == [
        "ollama", "glm", "deepseek", "anthropic",
    ]


def test_build_ocr_chain_two_step_resolved_falls_back_to_other_two_step():
    class FakeSettings:
        ocr_fallback = True
        glm_ocr_model = "glm-ocr:latest"
        deepseek_ocr_base_url = "http://localhost:8001"
        ocr_vision_provider = "ollama"
        ollama_base_url = "http://localhost:11434"
        anthropic_api_key = ""
        openai_api_key = ""

    # glm fails → deepseek is the first fallback (the other two-step), then VLM.
    assert _build_ocr_chain("glm", FakeSettings()) == ["glm", "deepseek", "ollama"]


def test_build_ocr_chain_returns_single_when_fallback_disabled():
    class FakeSettings:
        ocr_fallback = False
        glm_ocr_model = "glm-ocr:latest"
        deepseek_ocr_base_url = "http://localhost:8001"
        ocr_vision_provider = "ollama"
        ollama_base_url = "http://localhost:11434"
        anthropic_api_key = "test-key"
        openai_api_key = ""

    assert _build_ocr_chain("glm", FakeSettings()) == ["glm"]


def test_resolve_ocr_strategy_raises_when_no_provider():
    class FakeSettings:
        ocr_strategy = "auto"
        glm_ocr_model = ""
        ocr_vision_provider = "none"
        deepseek_ocr_base_url = ""

    with pytest.raises(ValueError, match="No OCR provider"):
        _resolve_ocr_strategy(None, FakeSettings())


# ── Prompt ────────────────────────────────────────────────────────────────────

def test_build_vision_extract_prompt_no_metadata():
    system, user = build_vision_extract_prompt()
    assert "Extract ALL questions" in user
    assert "JSON" in system


def test_build_vision_extract_prompt_with_metadata():
    system, user = build_vision_extract_prompt({"source_exam_code": "PT01"})
    assert "PT01" in user
