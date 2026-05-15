from app.llm.base import LLMProvider

# Keyed by (provider_name, api_key, base_url, default_model) so identical configs share one instance.
_provider_cache: dict = {}
# Flat list of all instantiated providers — used by close_all_providers().
_provider_registry: list = []


def get_provider(
    provider_name: str,
    api_key: str = "",
    base_url: str = "",
    default_model: str = "",
) -> LLMProvider:
    cache_key = (provider_name, api_key, base_url, default_model)
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=api_key, default_model=default_model or "claude-sonnet-4-6")
    elif provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key, default_model=default_model or "gpt-4o")
    elif provider_name == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        provider = OllamaProvider(
            base_url=base_url or "http://localhost:11434",
            default_model=default_model or "deepseek-v4-pro:cloud",
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
    _provider_cache[cache_key] = provider
    _provider_registry.append(provider)
    return provider


def get_ocr_client(base_url: str, model: str):
    """Return a DeepSeekOCRClient for the given local endpoint."""
    cache_key = ("deepseek_ocr", base_url, model)
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]
    from app.parsers.ocr import DeepSeekOCRClient
    client = DeepSeekOCRClient(base_url=base_url, model=model)
    _provider_cache[cache_key] = client
    _provider_registry.append(client)
    return client


async def close_all_providers() -> None:
    """Close any providers that expose a close() method (e.g. OllamaProvider httpx client)."""
    for p in _provider_registry:
        if hasattr(p, "close"):
            await p.close()
    _provider_cache.clear()
    _provider_registry.clear()
