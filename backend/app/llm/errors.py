"""LLM provider error helpers."""

from __future__ import annotations

from typing import Any

import httpx


class LLMAPIError(RuntimeError):
    """Provider API failure with optional token-usage metadata."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str,
        status_code: int | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.token_usage = token_usage


def token_usage_from_payload(payload: Any) -> dict[str, int] | None:
    if not isinstance(payload, dict):
        return None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        error = payload.get("error")
        usage = error.get("usage") if isinstance(error, dict) else None
    if not isinstance(usage, dict):
        return None
    token_usage = {
        "input": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
        "output": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
    }
    return token_usage if token_usage["input"] or token_usage["output"] else None


def raise_for_status_with_usage(
    response: httpx.Response,
    *,
    provider: str,
    model: str,
) -> None:
    try:
        response.raise_for_status()
        return
    except httpx.HTTPStatusError as exc:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        message = f"{provider} API request failed"
        if response.status_code:
            message = f"{message} with HTTP {response.status_code}"
        raise LLMAPIError(
            message,
            provider=provider,
            model=model,
            status_code=response.status_code,
            token_usage=token_usage_from_payload(payload),
        ) from exc


def _exception_message(exc: Exception) -> str:
    """Return a non-empty, human-readable message for an exception.

    Some exceptions (httpx.TimeoutException, httpx.ConnectError) have an empty
    ``str()``, which would otherwise produce ``{"error": ""}`` — useless for
    diagnosing a failed job.
    """
    message = str(exc).strip()
    if message:
        return message
    return f"{type(exc).__name__} (no message)"


def error_payload(step: str, exc: Exception) -> dict:
    payload: dict[str, object] = {
        "step": step,
        "error": _exception_message(exc),
        "error_type": type(exc).__name__,
    }
    provider = getattr(exc, "provider", None)
    model = getattr(exc, "model", None)
    status_code = getattr(exc, "status_code", None)
    token_usage = getattr(exc, "token_usage", None)
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    if status_code:
        payload["status_code"] = status_code
    if token_usage:
        payload["token_usage"] = token_usage
    return payload
