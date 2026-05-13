"""Unit tests for OCR providers: DeepSeekOCRClient and OllamaProvider.complete_vision()."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.parsers.ocr import DeepSeekOCRClient
from app.llm.base import ImageContent
from app.llm.ollama_provider import OllamaProvider
from app.prompts.extract_prompt import build_vision_extract_prompt
from app.routers.ingest import _collect_page_images, _resolve_ocr_strategy


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
