import time
from typing import Optional
import openai
from app.llm.base import LLMResponse


class OpenAIProvider:
    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
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