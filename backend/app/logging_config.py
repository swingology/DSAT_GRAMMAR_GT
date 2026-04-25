"""Structured JSON logging configuration for the DSAT Grammar API."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines with consistent fields."""

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload: dict[str, object] = {
            "timestamp": now.isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        request_id: Optional[str] = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        exc_info = getattr(record, "exc_info", None)
        if exc_info and record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)

        extra_keys = getattr(record, "extra", None)
        if extra_keys:
            payload.update(extra_keys)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure the root logger with JSON or plain formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"))

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for lib in ("httpx", "httpcore", "anthropic", "openai", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)
