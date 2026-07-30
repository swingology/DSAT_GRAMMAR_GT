"""Config-driven object storage for local S3/Supabase-style ingestion assets."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from app.config import get_settings


_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent


@dataclass(frozen=True)
class StoredObject:
    kind: str
    bucket: str
    key: str
    storage_path: str
    local_path: Path | None
    mime_type: str | None = None


_KIND_TEMPLATE_KEYS = {
    "raw_source_pdf": {"official": "official_pdf", "unofficial": "unofficial_file", "generated": "unofficial_file"},
    "raw_source_file": {"official": "official_pdf", "unofficial": "unofficial_file", "generated": "unofficial_file"},
    "rendered_page": {"official": "official_page", "unofficial": "unofficial_page", "generated": "unofficial_page"},
    "question_crop": "question_crop",
    "table_crop": "table_crop",
    "chart_crop": "chart_crop",
    "figure_crop": "figure_crop",
    "table_asset": "table_json",
    "chart_asset": "chart_json",
    "figure_asset": "figure_manifest",
    "ocr_text": "page_text",
    "ocr_layout": "page_layout",
    "ocr_diagnostics": "diagnostics",
    "benchmark_markdown": "markdown_report",
    "benchmark_json": "json_result",
}


def _safe_part(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._")
    return text[:180] or "unknown"


def _safe_filename(filename: str | None) -> str:
    return _safe_part(Path(filename or "object").name)


def _resolve_existing_path(value: str) -> Path:
    raw = Path(value)
    candidates = [
        raw,
        _BACKEND_ROOT / raw,
        _REPO_ROOT / raw,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (_BACKEND_ROOT / raw).resolve()


def _resolve_local_root(layout: dict) -> Path:
    settings = get_settings()
    configured = getattr(settings, "object_storage_local_root", "") or ""
    if configured:
        root = Path(configured)
        if not root.is_absolute():
            root = _BACKEND_ROOT / root
        return root.resolve()

    layout_root = Path(layout["backends"]["local_fs"]["root"])
    if layout_root.is_absolute():
        return layout_root.resolve()
    return (_REPO_ROOT / layout_root).resolve()


@lru_cache(maxsize=1)
def load_storage_layout() -> dict:
    settings = get_settings()
    config_path = _resolve_existing_path(settings.object_storage_layout_config)
    with config_path.open("r", encoding="utf-8") as f:
        layout = yaml.safe_load(f) or {}
    if "buckets" not in layout or "object_kinds" not in layout:
        raise ValueError(f"Invalid storage layout config: {config_path}")
    return layout


def _active_backend(layout: dict) -> str:
    settings = get_settings()
    return getattr(settings, "object_storage_backend", None) or layout.get("active_backend", "local_fs")


def _bucket_config(kind: str, layout: dict) -> tuple[str, dict]:
    try:
        bucket_name = layout["object_kinds"][kind]["bucket"]
        bucket = layout["buckets"][bucket_name]
    except KeyError as exc:
        raise ValueError(f"Unknown object kind '{kind}'") from exc
    return bucket_name, bucket


def _template_key(kind: str, context: dict) -> str:
    template_key = _KIND_TEMPLATE_KEYS.get(kind)
    if template_key is None:
        raise ValueError(f"No object key template mapping for kind '{kind}'")
    if isinstance(template_key, dict):
        origin = str(context.get("content_origin") or "unofficial").lower()
        return template_key.get(origin, template_key["unofficial"])
    return template_key


def _format_context(context: dict, filename: str | None) -> dict:
    formatted = {key: value for key, value in context.items()}
    formatted["filename"] = _safe_filename(filename or context.get("filename"))

    for key, value in list(formatted.items()):
        if key in {"page_number"}:
            formatted[key] = int(value)
        elif key.endswith("_number") and value is not None:
            try:
                formatted[key] = int(value)
            except (TypeError, ValueError):
                formatted[key] = _safe_part(value)
        else:
            formatted[key] = _safe_part(value)
    return formatted


def object_uri(bucket: str, key: str) -> str:
    layout = load_storage_layout()
    scheme = layout["backends"].get("local_fs", {}).get("uri_scheme", "local-s3")
    return f"{scheme}://{bucket}/{key.lstrip('/')}"


def format_object_key(kind: str, context: dict, filename: str | None = None) -> tuple[str, str]:
    layout = load_storage_layout()
    _, bucket = _bucket_config(kind, layout)
    template_name = _template_key(kind, context)
    try:
        template = bucket["object_keys"][template_name]
    except KeyError as exc:
        raise ValueError(f"Missing template '{template_name}' for object kind '{kind}'") from exc
    key = template.format(**_format_context(context, filename))
    return bucket["local_prefix"], key


def local_path(bucket: str, key: str) -> Path:
    layout = load_storage_layout()
    root = _resolve_local_root(layout)
    path = (root / bucket / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("object path escapes local object-store root")
    return path


def put_object(
    kind: str,
    context: dict,
    content: bytes | str,
    filename: str | None = None,
    mime_type: str | None = None,
) -> StoredObject:
    layout = load_storage_layout()
    backend = _active_backend(layout)
    bucket, key = format_object_key(kind, context, filename)

    if backend != "local_fs":
        raise NotImplementedError("Supabase object storage is configured but not implemented yet")

    data = content.encode("utf-8") if isinstance(content, str) else content
    path = local_path(bucket, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    return StoredObject(
        kind=kind,
        bucket=bucket,
        key=key,
        storage_path=object_uri(bucket, key),
        local_path=path,
        mime_type=mime_type,
    )


def read_object(storage_path: str) -> bytes:
    parsed = urlparse(storage_path)
    if not parsed.scheme:
        return Path(storage_path).read_bytes()
    if parsed.scheme != load_storage_layout()["backends"].get("local_fs", {}).get("uri_scheme", "local-s3"):
        raise NotImplementedError(f"Reading {parsed.scheme} storage paths is not implemented")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return local_path(bucket, key).read_bytes()


def public_url(storage_path: str) -> str:
    """Return a URL for a stored object's storage_path.

    The local-fs backend has no public HTTP surface yet, so this returns the
    object URI as-is (e.g. ``local-s3://bucket/key``). The admin
    stimulus-asset browser treats it as an opaque handle until a dedicated
    serving route is added. ``read_object`` can resolve it back to bytes.
    """
    return storage_path
