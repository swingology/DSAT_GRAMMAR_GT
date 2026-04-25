"""Request ID middleware for correlation tracing."""

import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique request ID to every request.

    If the client sends an ``X-Request-ID`` header, that value is used (to
    enable end-to-end tracing).  Otherwise a new UUID is generated.

    The ID is available via ``request.state.request_id`` and is also set on a
    ``ContextVar`` so that ``logging_config.JSONFormatter`` can pick it up.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id: str = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        token = request_id_var.set(req_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id

        request_id_var.reset(token)
        return response


def get_request_id() -> str:
    """Return the current request ID (empty string if no request active)."""
    try:
        return request_id_var.get()
    except LookupError:
        return ""
