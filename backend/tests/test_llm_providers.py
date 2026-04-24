import pytest
import inspect
from unittest.mock import AsyncMock, patch
from app.llm.base import LLMProvider, LLMResponse
from app.llm.factory import get_provider


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
    assert hasattr(LLMProvider, "complete")
    sig = inspect.signature(LLMProvider.complete)
    params = list(sig.parameters.keys())
    assert "system" in params
    assert "user" in params


# --- Factory tests ---

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


# --- Provider mock tests ---

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


@pytest.mark.asyncio
async def test_openai_complete():
    from app.llm.openai_provider import OpenAIProvider
    provider = OpenAIProvider(api_key="test-key")

    mock_choice = AsyncMock()
    mock_choice.message = AsyncMock(content='{"question_text": "test"}')
    mock_response = AsyncMock(choices=[mock_choice], model="gpt-4o")
    mock_response.usage = AsyncMock(prompt_tokens=100, completion_tokens=50)

    with patch.object(provider, "client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await provider.complete(system="You are a test", user="Extract this")
        assert result.provider == "openai"


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