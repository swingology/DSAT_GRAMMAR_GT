import re
import time
from typing import Optional
import httpx
from app.llm.base import LLMResponse
from app.llm.errors import raise_for_status_with_usage
from app.llm.retry import with_retry


def _extract_content(message: dict) -> str:
    """Return the text content from an OpenAI-compat chat message.

    Some thinking models (qwen3-vl in reasoning mode) return an empty `content`
    field and place their answer in a `reasoning` field. Fall back to that field,
    then strip any residual <think>…</think> wrapper.
    """
    raw = message.get("content") or message.get("reasoning") or ""
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


class OllamaProvider:
    # Vision inference is significantly slower than text (model loads + OCR decode)
    VISION_TIMEOUT = 600.0
    # Large extraction payloads (30K+ chars against cloud models) regularly exceed
    # the prior 120s ceiling; give text completion a wider, but still bounded, limit.
    TEXT_TIMEOUT = 300.0

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "deepseek-v4-pro:cloud"):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.TEXT_TIMEOUT)
        self.vision_client = httpx.AsyncClient(base_url=self.base_url, timeout=self.VISION_TIMEOUT)

    @with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        disable_thinking: bool = False,
    ) -> LLMResponse:
        model = model or self.default_model
        start = time.time()
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if disable_thinking:
            payload["options"] = {"thinking": False}
        response = await self.client.post(
            "/v1/chat/completions",
            json=payload,
        )
        latency_ms = int((time.time() - start) * 1000)
        raise_for_status_with_usage(response, provider="ollama", model=model)
        data = response.json()
        raw_text = _extract_content(data["choices"][0]["message"])
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

    @with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        from app.llm.base import ImageContent  # noqa: F401 — local import avoids circular dep
        model = model or self.default_model
        start = time.time()

        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{img.mime_type};base64,{img.b64}"},
            }
            for img in images
        ]
        content.append({"type": "text", "text": user})

        response = await self.vision_client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                # Disable thinking mode for structured extraction — thinking models (qwen3-vl)
                # suppress their answer into reasoning tokens, returning empty content.
                "options": {"thinking": False},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": content},
                ],
            },
        )
        latency_ms = int((time.time() - start) * 1000)
        raise_for_status_with_usage(response, provider="ollama", model=model)
        data = response.json()
        raw_text = _extract_content(data["choices"][0]["message"])
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

    async def close(self):
        await self.client.aclose()
        await self.vision_client.aclose()
