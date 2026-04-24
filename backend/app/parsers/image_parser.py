"""Image parser — converts image file to base64 for multimodal LLM processing."""
import base64
from pathlib import Path


MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def parse_image(path: str) -> dict:
    """Read an image file and return base64-encoded content + metadata."""
    p = Path(path)
    suffix = p.suffix.lower()
    mime_type = MIME_MAP.get(suffix, "application/octet-stream")
    content = p.read_bytes()
    b64 = base64.standard_b64encode(content).decode("utf-8")
    return {
        "b64": b64,
        "mime_type": mime_type,
        "filename": p.name,
        "size_bytes": len(content),
    }