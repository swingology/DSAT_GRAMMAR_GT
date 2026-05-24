from typing import Optional, Dict, List, Protocol, runtime_checkable
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    raw_text: str
    model: str
    provider: str
    latency_ms: int = 0
    token_usage: Optional[Dict[str, int]] = None
    # Cache-specific usage (Anthropic: cache_creation / cache_read; Ollama: not reported)
    cache_token_usage: Dict[str, int] = field(default_factory=dict)
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

    async def complete_cached(
        self,
        system_static: str,
        system_dynamic: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Variant of complete() that separates the cacheable static rules block
        from the per-call dynamic instructions.

        Providers implement this differently:
          - Anthropic: system=[{static, cache_control:ephemeral}, {dynamic}]
          - Ollama: concatenate + set num_keep to lock static prefix in KV cache
          - Others: fall back to complete(system_static+system_dynamic, user)
        """
        return await self.complete(
            system=system_static + "\n\n" + system_dynamic,
            user=user,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

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