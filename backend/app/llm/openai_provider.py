import time
from typing import Optional, List
import openai
from app.llm.base import LLMResponse, ImageContent
from app.llm.errors import LLMAPIError, token_usage_from_payload
from app.llm.retry import with_retry


class OpenAIProvider:
    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=90.0)
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
            response = await self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:
            raise LLMAPIError(
                f"openai API request failed: {exc}",
                provider="openai",
                model=model,
                status_code=getattr(exc, "status_code", None),
                token_usage=token_usage_from_payload(getattr(exc, "body", None)),
            ) from exc
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

    async def complete_cached(
        self,
        system_static: str,
        system_dynamic: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """OpenAI automatically caches stable prompt prefixes >= 1024 tokens.
        Concatenate static + dynamic and send as a normal request — no API change needed.
        """
        return await self.complete(
            system=system_static + "\n\n" + system_dynamic,
            user=user,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
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
                "type": "image_url",
                "image_url": {"url": f"data:{img.mime_type};base64,{img.b64}"},
            }
            for img in images
        ]
        content.append({"type": "text", "text": user})
        try:
            response = await self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": content},
                ],
            )
        except Exception as exc:
            raise LLMAPIError(
                f"openai API request failed: {exc}",
                provider="openai",
                model=model,
                status_code=getattr(exc, "status_code", None),
                token_usage=token_usage_from_payload(getattr(exc, "body", None)),
            ) from exc
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
