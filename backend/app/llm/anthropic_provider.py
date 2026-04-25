import time
from typing import Optional
import anthropic
from app.llm.base import LLMResponse
from app.llm.retry import with_retry


class AnthropicProvider:
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
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