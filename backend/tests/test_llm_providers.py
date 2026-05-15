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
    assert p.default_model == "deepseek-v4-pro:cloud"


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


@pytest.mark.asyncio
async def test_ollama_complete_can_disable_thinking():
    from app.llm.ollama_provider import OllamaProvider
    provider = OllamaProvider(base_url="http://localhost:11434")

    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {
        "choices": [{"message": {"content": '{"questions": []}'}}],
        "usage": {},
    }

    with patch.object(provider, "client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        await provider.complete(
            system="You are a test",
            user="Extract this",
            disable_thinking=True,
        )

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["options"] == {"thinking": False}


@pytest.mark.asyncio
async def test_close_all_providers_calls_close():
    """close_all_providers() calls close() on providers that have it and clears registry."""
    from app.llm import factory
    from unittest.mock import MagicMock

    mock_provider = MagicMock()
    mock_provider.close = AsyncMock()
    original = factory._provider_registry[:]
    factory._provider_registry.append(mock_provider)

    await factory.close_all_providers()

    mock_provider.close.assert_called_once()
    assert mock_provider not in factory._provider_registry
    # Restore any pre-existing entries that were cleared
    factory._provider_registry.extend(original)


# --- Retry tests ---
# Use plain Exception subclasses with status_code set directly — the SDK constructors
# require real httpx.Response objects which are unnecessary for testing _is_retryable.

def test_retry_fires_on_429_status_code():
    """_is_retryable returns True for any exception with status_code=429."""
    from app.llm.retry import _is_retryable

    class FakeRateLimit(Exception):
        status_code = 429

    assert _is_retryable(FakeRateLimit())


def test_retry_fires_on_500_status_code():
    """_is_retryable returns True for any exception with status_code=500."""
    from app.llm.retry import _is_retryable

    class FakeServerError(Exception):
        status_code = 500

    assert _is_retryable(FakeServerError())


def test_retry_not_retryable_on_401_status_code():
    """_is_retryable returns False for auth errors (status_code=401)."""
    from app.llm.retry import _is_retryable

    class FakeAuthError(Exception):
        status_code = 401

    assert not _is_retryable(FakeAuthError())


def test_retry_fires_on_anthropic_connection_error():
    """_is_retryable returns True for anthropic.APIConnectionError."""
    import anthropic
    from app.llm.retry import _is_retryable
    from unittest.mock import MagicMock

    request = MagicMock()
    exc = anthropic.APIConnectionError(request=request)
    assert _is_retryable(exc)


def test_retry_not_retryable_on_unknown_exception():
    """_is_retryable returns False for arbitrary unrelated exceptions."""
    from app.llm.retry import _is_retryable
    assert not _is_retryable(ValueError("some parse error"))
