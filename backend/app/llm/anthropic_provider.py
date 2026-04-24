import time
from typing import Optional
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