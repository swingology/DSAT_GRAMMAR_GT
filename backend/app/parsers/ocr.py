"""DeepSeek OCR-2 client — sends images to local vLLM/LMDeploy server, returns text."""
import time
import httpx
from app.llm.base import ImageContent, LLMResponse


class DeepSeekOCRClient:
    """Thin HTTP client for DeepSeek-OCR-2 running locally via vLLM or LMDeploy."""

    OCR_SYSTEM_PROMPT = (
        "You are a document OCR specialist. Extract all text from the provided image(s) "
        "exactly as it appears. Preserve the question structure, answer choices (A/B/C/D), "
        "and passage text. Output plain Markdown text only — no commentary, no fences."
    )

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def extract(self, images: list[ImageContent], max_tokens: int = 4096) -> LLMResponse:
        """Send images to DeepSeek-OCR-2 and return extracted Markdown text."""
        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{img.mime_type};base64,{img.b64}"},
            }
            for img in images
        ]
        content.append({
            "type": "text",
            "text": "Extract all text from this document page. Preserve structure.",
        })

        start = time.time()
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": self.OCR_SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
            },
        )
        latency_ms = int((time.time() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            raw_text=raw_text,
            model=self.model,
            provider="deepseek_ocr",
            latency_ms=latency_ms,
            token_usage={
                "input": usage.get("prompt_tokens", 0),
                "output": usage.get("completion_tokens", 0),
            },
        )

    async def close(self):
        await self.client.aclose()
