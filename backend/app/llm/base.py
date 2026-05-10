from typing import Optional, Dict, List, Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class LLMResponse:
    raw_text: str
    model: str
    provider: str
    latency_ms: int = 0
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


@dataclass
class ImageContent:
    b64: str
    mime_type: str  # e.g. "image/png", "image/jpeg"


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        ...

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: List["ImageContent"],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError(f"{type(self).__name__} does not support vision")