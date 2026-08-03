import time
from typing import Optional, List
import anthropic
from app.llm.base import LLMResponse, ImageContent
from app.llm.errors import LLMAPIError, token_usage_from_payload
from app.llm.retry import with_retry


def _first_text_block(response) -> str:
    """Return the first text block's content, skipping non-text blocks.

    response.content[0].text assumes the first block is text. That holds for
    Anthropic's own models, but a reasoning model served through the LiteLLM
    proxy (e.g. local qwen3.6:27b) puts a ThinkingBlock first, which has no
    .text attribute. Select by block type instead of position.
    """
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text is not None:
            return text
    return ""


class AnthropicProvider:
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-6", base_url: str = ""):
        # base_url lets this provider target the LiteLLM proxy, which exposes an
        # Anthropic-compatible route alongside its OpenAI one. Empty string keeps
        # the SDK's own default endpoint.
        self.client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url or None)
        self.default_model = default_model

    @with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
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
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            raise LLMAPIError(
                f"anthropic API request failed: {exc}",
                provider="anthropic",
                model=model,
                status_code=getattr(exc, "status_code", None),
                token_usage=token_usage_from_payload(getattr(exc, "body", None)),
            ) from exc
        latency_ms = int((time.time() - start) * 1000)
        raw_text = _first_text_block(response)
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

    @with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
    async def complete_cached(
        self,
        system_static: str,
        system_dynamic: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Annotate with prompt caching enabled.

        system_static (the rules block, ~10-17K tokens) is marked cache_control:ephemeral
        so Anthropic caches it across calls within the same 5-minute window.
        system_dynamic (base instructions + content_origin) is sent fresh each call.
        """
        model = model or self.default_model
        start = time.time()
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=[
                    {
                        "type": "text",
                        "text": system_static,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": system_dynamic,
                    },
                ],
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            raise LLMAPIError(
                f"anthropic API request failed: {exc}",
                provider="anthropic",
                model=model,
                status_code=getattr(exc, "status_code", None),
                token_usage=token_usage_from_payload(getattr(exc, "body", None)),
            ) from exc
        latency_ms = int((time.time() - start) * 1000)
        raw_text = _first_text_block(response)
        token_usage = {
            "input": getattr(response.usage, "input_tokens", 0),
            "output": getattr(response.usage, "output_tokens", 0),
        }
        cache_token_usage = {
            "cache_creation": getattr(response.usage, "cache_creation_input_tokens", 0),
            "cache_read": getattr(response.usage, "cache_read_input_tokens", 0),
        }
        return LLMResponse(
            raw_text=raw_text,
            model=model,
            provider="anthropic",
            latency_ms=latency_ms,
            token_usage=token_usage,
            cache_token_usage=cache_token_usage,
        )

    @with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
    async def complete_vision(
        self,
        system: str,
        user: str,
        images: List[ImageContent],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        model = model or self.default_model
        start = time.time()
        content: list = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.mime_type,
                    "data": img.b64,
                },
            }
            for img in images
        ]
        content.append({"type": "text", "text": user})
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:
            raise LLMAPIError(
                f"anthropic API request failed: {exc}",
                provider="anthropic",
                model=model,
                status_code=getattr(exc, "status_code", None),
                token_usage=token_usage_from_payload(getattr(exc, "body", None)),
            ) from exc
        latency_ms = int((time.time() - start) * 1000)
        raw_text = _first_text_block(response)
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
