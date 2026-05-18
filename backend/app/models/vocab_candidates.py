"""Controlled-vocabulary review queue.

When the pipeline meets a key the LLM invented that is not yet in the
controlled vocabulary, it records the key here instead of either silently
accepting it (drift) or hard-failing the question (lost data). A human reviews
the queue with ``python scripts/gen_vocab.py --list-candidates`` and promotes
real keys into ``vocabulary/master.json`` with ``--promote``.

Recording is non-blocking: the question still ingests. The candidate file is
append/merge only — it never affects validation outcomes.

Writes are guarded by an ``fcntl`` lock because Pass-2 annotation runs
concurrently (see ``OLLAMA_MAX_CONCURRENT``); without the lock concurrent
read-modify-write cycles would clobber each other.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
from pathlib import Path
from app.models.vocab_fields import BASE_FIELD_TO_VOCAB

try:  # POSIX file locking — present on the Linux deploy target
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

logger = logging.getLogger(__name__)

# vocabulary/candidates.json — sibling of master.json, repo-root/vocabulary/.
_REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATES_PATH = _REPO_ROOT / "vocabulary" / "candidates.json"

SCHEMA_VERSION = 1
_MAX_SAMPLES = 5  # cap stored job_ids / contexts per candidate

# Maps an annotation field name to the master.json vocabulary it belongs to.
# Used so callers can pass the field they were validating and let this module
# resolve the vocabulary.
FIELD_TO_VOCAB = BASE_FIELD_TO_VOCAB


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _empty() -> dict:
    return {"schema_version": SCHEMA_VERSION, "candidates": []}


def _load(fh) -> dict:
    fh.seek(0)
    raw = fh.read()
    if not raw.strip():
        return _empty()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("candidates.json is corrupt — starting a fresh queue")
        return _empty()
    data.setdefault("candidates", [])
    return data


def record_candidate(
    vocab: str,
    value: str,
    *,
    field: str | None = None,
    job_id: str | None = None,
    context: str | None = None,
) -> None:
    """Record an unknown vocabulary key in the review queue (non-blocking).

    Safe to call from any pipeline stage; never raises on I/O failure — a lost
    candidate must not abort an ingestion.
    """
    if not vocab or not value:
        return
    try:
        CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
        # open in r+ (create if absent), hold an exclusive lock across the
        # whole read-modify-write so concurrent annotators do not clobber.
        with open(CANDIDATES_PATH, "a+", encoding="utf-8") as fh:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                data = _load(fh)
                row = next(
                    (c for c in data["candidates"]
                     if c["vocab"] == vocab and c["value"] == value),
                    None,
                )
                now = _now()
                if row is None:
                    data["candidates"].append({
                        "vocab": vocab,
                        "value": value,
                        "field": field,
                        "first_seen": now,
                        "last_seen": now,
                        "occurrences": 1,
                        "job_ids": [job_id] if job_id else [],
                        "contexts": [context] if context else [],
                    })
                else:
                    row["occurrences"] += 1
                    row["last_seen"] = now
                    if job_id and job_id not in row["job_ids"]:
                        row["job_ids"] = (row["job_ids"] + [job_id])[-_MAX_SAMPLES:]
                    if context and context not in row["contexts"]:
                        row["contexts"] = (row["contexts"] + [context])[-_MAX_SAMPLES:]
                fh.seek(0)
                fh.truncate()
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            finally:
                if fcntl is not None:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError as exc:  # pragma: no cover - disk/permission failure
        logger.warning("could not record vocab candidate %s=%r: %s",
                        vocab, value, exc)


def record_unknown_field(
    field: str,
    value: str,
    *,
    job_id: str | None = None,
    context: str | None = None,
) -> None:
    """Convenience wrapper: resolve ``field`` to its vocabulary and record."""
    vocab = FIELD_TO_VOCAB.get(field)
    if vocab is None:
        logger.debug("no vocabulary mapped for field %r — candidate dropped", field)
        return
    record_candidate(vocab, value, field=field, job_id=job_id, context=context)
