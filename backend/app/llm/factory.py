from app.llm.base import LLMProvider


def get_provider(
    provider_name: str,
    api_key: str = "",
    base_url: str = "",
    default_model: str = "",
) -> LLMProvider:
    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key, default_model=default_model or "claude-sonnet-4-6")
    elif provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, default_model=default_model or "gpt-4o")
    elif provider_name == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url=base_url or "http://localhost:11434", default_model=default_model or "kimi-k2")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")