from app.llm.base import LLMProvider

_provider_registry: list = []


def get_provider(
    provider_name: str,
    api_key: str = "",
    base_url: str = "",
    default_model: str = "",
) -> LLMProvider:
    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=api_key, default_model=default_model or "claude-sonnet-4-6")
    elif provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key, default_model=default_model or "gpt-4o")
    elif provider_name == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        provider = OllamaProvider(base_url=base_url or "http://localhost:11434", default_model=default_model or "kimi-k2")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
    _provider_registry.append(provider)
    return provider


async def close_all_providers() -> None:
    """Close any providers that expose a close() method (e.g. OllamaProvider httpx client)."""
    for p in _provider_registry:
        if hasattr(p, "close"):
            await p.close()
    _provider_registry.clear()