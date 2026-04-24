"""Local filesystem asset storage.
Stores raw assets (PDFs, images, markdown) as files on disk.
Paths are recorded in question_assets.storage_path.
"""
import os
import hashlib
from pathlib import Path
from app.config import get_settings


def _archive_dir() -> Path:
    settings = get_settings()
    path = Path(settings.local_archive_mirror)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_asset(filename: str, content: bytes, subfolder: str = "") -> str:
    """Save a raw asset file to the local archive.
    Returns the storage path relative to the archive root.
    """
    archive = _archive_dir()
    if subfolder:
        target = archive / subfolder
    else:
        target = archive
    target.mkdir(parents=True, exist_ok=True)

    dest = target / filename
    dest.write_bytes(content)
    return str(dest)


async def read_asset(storage_path: str) -> bytes:
    """Read a raw asset from the local archive."""
    return Path(storage_path).read_bytes()


def compute_checksum(content: bytes) -> str:
    """SHA-256 checksum for deduplication."""
    return hashlib.sha256(content).hexdigest()