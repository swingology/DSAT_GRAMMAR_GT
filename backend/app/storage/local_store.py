"""Local filesystem asset storage.
Stores raw assets (PDFs, images, markdown) as files on disk.
Paths are recorded in question_assets.storage_path.
"""
import hashlib
import re
import uuid
from pathlib import Path
from app.config import get_settings


def _archive_dir() -> Path:
    settings = get_settings()
    path = Path(settings.local_archive_mirror)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_path_part(value: str) -> str:
    part = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return part[:180] or "upload"


def _safe_filename(filename: str) -> str:
    return _safe_path_part(Path(filename).name)


def _safe_subfolder(subfolder: str) -> str:
    folder = Path(subfolder)
    if folder.is_absolute() or ".." in folder.parts:
        raise ValueError("subfolder must be relative and stay within archive root")
    return "/".join(_safe_path_part(part) for part in folder.parts if part not in ("", "."))


async def save_asset(filename: str, content: bytes, subfolder: str = "") -> str:
    """Save a raw asset file to the local archive.
    Returns the storage path relative to the archive root.
    """
    archive = _archive_dir().resolve()
    if subfolder:
        target = archive / _safe_subfolder(subfolder)
    else:
        target = archive
    target.mkdir(parents=True, exist_ok=True)

    dest = target / f"{uuid.uuid4().hex}_{_safe_filename(filename)}"
    if not dest.resolve().is_relative_to(archive):
        raise ValueError("asset path escapes archive root")
    dest.write_bytes(content)
    return str(dest)


async def read_asset(storage_path: str) -> bytes:
    """Read a raw asset from the local archive."""
    return Path(storage_path).read_bytes()


def compute_checksum(content: bytes) -> str:
    """SHA-256 checksum for deduplication."""
    return hashlib.sha256(content).hexdigest()
