import time
from typing import Optional
import httpx
from app.llm.base import LLMResponse


class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "kimi-k2"):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

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
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        latency_ms = int((time.time() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
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

    async def close(self):
        await self.client.aclose()