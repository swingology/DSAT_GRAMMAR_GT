import uuid
import re
import asyncio
import logging
import tempfile
import base64
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.job_limits import run_with_job_limit
from app.llm.errors import error_payload
from app.models.db import (
    QuestionJob, QuestionJobQuestion, QuestionAsset, Question, QuestionVersion,
    QuestionAnnotation, QuestionOption, QuestionSourceSpan, QuestionStimulusAsset,
)
from app.storage.local_store import compute_checksum
from app.storage.object_store import put_object, read_object
from app.storage.crop_detector import detect_layout, match_region_for_question, match_stimulus_regions_for_question, crop_and_store
from app.parsers.pdf_parser import parse_pdf
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
from app.pipeline.orchestrator import JobOrchestrator
from app.pipeline.validator import validate_question
from app.pipeline.annotation_sanitizer import sanitize_annotation_keys
from app.pipeline.option_hydration import option_analyses_by_label, option_annotation_fields, apply_option_annotations
from app.models.payload import JobResponse, ReannotateRequest, OCRJobResult, OCRBenchmarkResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _sanitize_source_name(filename: str | None) -> str | None:
    """Remove path separators and control chars from upload filenames before DB storage."""
    if not filename:
        return filename
    return re.sub(r'[/\\<>:"|?*\x00-\x1f]', '_', filename)[:200]


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Background ingest task failed", exc_info=task.exception(), extra={"task": task.get_name()})

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "image/gif", "text/markdown", "text/plain", "application/json",
}
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_PAGE_RENDER_BYTES = 10 * 1024 * 1024  # 10 MB per decoded page image
OCR_TEXT_EXTRACT_PROVIDER = "ollama"
OCR_TEXT_EXTRACT_MODEL = "qwen3-vl:235b-instruct-cloud"


def _resolve_provider_and_model(
    settings,
    provider_name: str | None,
    model_name: str | None,
) -> tuple[str, str]:
    provider = (provider_name or settings.default_annotation_provider or "ollama").strip()
    model = (model_name or "").strip()
    if model:
        return provider, model
    if provider == "ollama":
        return provider, settings.default_ollama_model
    if provider == "anthropic":
        if settings.default_annotation_provider == "anthropic":
            return provider, settings.default_annotation_model
        return provider, "claude-sonnet-4-6"
    if provider == "openai":
        if settings.default_annotation_provider == "openai":
            return provider, settings.default_annotation_model
        return provider, "gpt-4o"
    return provider, settings.default_annotation_model


def _provider_api_key(settings, provider_name: str) -> str:
    if provider_name == "anthropic":
        return settings.anthropic_api_key
    if provider_name == "openai":
        return settings.openai_api_key
    return ""


def _should_disable_ollama_thinking_for_extraction(job: QuestionJob) -> bool:
    return (
        job.provider_name == "ollama"
        and job.model_name == "deepseek-v4-pro:cloud"
    )


def _should_disable_thinking(provider_name: str, model_name: str) -> bool:
    return provider_name == "ollama" and model_name == OCR_TEXT_EXTRACT_MODEL


def _should_auto_activate_official(settings) -> bool:
    return bool(getattr(settings, "official_auto_activate_for_testing", False))


# Fixed namespace for all official College Board question UUIDs.
# Never change this — altering it would invalidate every existing official question ID.
_OFFICIAL_Q_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 URL namespace


def _official_question_uuid(
    exam_code: str,
    subject_code: str,
    section_code: str,
    module_code: str,
    question_number: int,
) -> uuid.UUID:
    """Return a deterministic UUID5 for an official College Board question.

    The canonical key is exam:subject:section:module:question_number, e.g.
    "PT1:verbal:01:01:3".  Same inputs always produce the same UUID, making
    re-ingestion of the same question idempotent.
    """
    canonical = f"{exam_code.upper()}:{subject_code.lower()}:{section_code}:{module_code}:{question_number}"
    return uuid.uuid5(_OFFICIAL_Q_NAMESPACE, canonical)


def _normalize_source_subject_code(value: str | None) -> str | None:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    aliases = {
        "verbal": "verbal",
        "reading_writing": "verbal",
        "reading-writing": "verbal",
        "rw": "verbal",
        "english": "verbal",
        "math": "math",
        "mathematics": "math",
        "m": "math",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"verbal", "math"}:
        raise HTTPException(status_code=422, detail="source_subject_code must be 'verbal' or 'math'")
    return normalized


def _normalize_source_slot(value: str | None, field_name: str) -> str | None:
    normalized = (value or "").strip().upper()
    if not normalized:
        return None
    aliases = {
        "S1": "01",
        "S2": "02",
        "M1": "01",
        "M2": "02",
        "1": "01",
        "2": "02",
        "01": "01",
        "02": "02",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"01", "02"}:
        raise HTTPException(status_code=422, detail=f"{field_name} must be '01' or '02'")
    return normalized


def _normalize_source_metadata(
    source_subject_code: str | None,
    source_section_code: str | None,
    source_module_code: str | None,
) -> tuple[str | None, str | None, str | None]:
    return (
        _normalize_source_subject_code(source_subject_code),
        _normalize_source_slot(source_section_code, "source_section_code"),
        _normalize_source_slot(source_module_code, "source_module_code"),
    )


def _generation_profile_payload(*sources: dict | None) -> dict | None:
    """Extract a stored generation profile when annotation output includes one."""
    merged: dict = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        profile = source.get("generation_profile")
        if isinstance(profile, dict):
            merged.update(profile)
    return merged or None


# Expected question count per subject per module — matches the official
# DSAT practice-test PDFs in TESTS/DATA_SRC (verbal modules carry 33 questions,
# not the 27 of the adaptive College Board spec).
_DSAT_QUESTION_RANGES: dict[tuple[str, str], tuple[int, int]] = {
    ("verbal", "01"): (1, 33),
    ("verbal", "02"): (1, 33),
    ("math",   "01"): (1, 22),
    ("math",   "02"): (1, 22),
}


# Keys produced by Pass 1 extraction that are the structural source of truth.
# Pass 2 annotation must never overwrite these — the annotation's "options"
# block carries per-option *analysis* (distractor type, etc.) keyed by
# "option_label" with no/blank "label", so merging it over the extraction
# options blanks out the A/B/C/D labels and validation fails.
_EXTRACTION_OWNED_KEYS = (
    "options",
    "question_text",
    "passage_text",
    "paired_passage_text",
    "correct_option_label",
    "source_question_number",
    "stimulus_assets",
)


def _merge_for_validation(q_data: dict, annotate_json: dict) -> dict:
    """Merge extraction + annotation for validation without losing structure.

    Annotation contributes classification keys; extraction owns the structural
    fields in _EXTRACTION_OWNED_KEYS. On any key collision, extraction wins.

    After the merge, option dicts are normalized so that option_label/option_text
    (annotation format from rules v8 examples) fall back to label/text (extraction
    and internal format). This prevents validation failures when the annotation LLM
    returns options with the wrong key names.
    """
    merged = {**q_data, **annotate_json}
    for key in _EXTRACTION_OWNED_KEYS:
        if key in q_data:
            merged[key] = q_data[key]

    # Normalize option key names: annotation uses option_label/option_text,
    # extraction and internal code use label/text. Ensure both are present.
    for opt in merged.get("options", []):
        if isinstance(opt, dict):
            if "label" not in opt or not opt["label"]:
                opt["label"] = opt.get("option_label", "")
            if "text" not in opt or not opt["text"]:
                opt["text"] = opt.get("option_text", "")

    return merged


def _validate_question_numbers(
    questions: list[dict],
    subject_code: str | None,
    module_code: str | None,
) -> list[dict]:
    """Validate LLM-inferred source_question_number values for a batch.

    Checks performed (in order):
      1. Each question has a non-null integer question number.
      2. Numbers fall within the expected range for this subject/module.
      3. Numbers within the batch are unique (no duplicates).
      4. Numbers form a contiguous sequence (no gaps).

    Returns a list of warning dicts (empty = clean). Does NOT raise — callers
    attach warnings to validation_errors_jsonb and continue ingestion.
    """
    warnings: list[dict] = []
    key = (subject_code or "", module_code or "")
    valid_range = _DSAT_QUESTION_RANGES.get(key)

    nums: list[int | None] = []
    for i, q in enumerate(questions):
        raw = q.get("source_question_number")
        if raw is None:
            n = None
            warnings.append({
                "step": "question_number_validation",
                "question_index": i,
                "issue": "non_integer",
                "value": None,
                "detail": f"question_index {i}: source_question_number is null — UUID5 cannot be assigned",
            })
        else:
            try:
                n = int(raw)
            except (TypeError, ValueError):
                n = None
                warnings.append({
                    "step": "question_number_validation",
                    "question_index": i,
                    "issue": "non_integer",
                    "value": raw,
                    "detail": f"question_index {i}: source_question_number '{raw}' is not an integer",
                })
        nums.append(n)

    # Range check
    if valid_range:
        lo, hi = valid_range
        for i, n in enumerate(nums):
            if n is not None and not (lo <= n <= hi):
                warnings.append({
                    "step": "question_number_validation",
                    "question_index": i,
                    "issue": "out_of_range",
                    "value": n,
                    "detail": f"question_index {i}: number {n} outside expected range {lo}–{hi} for {subject_code}/mod{module_code}",
                })
    elif subject_code and module_code:
        warnings.append({
            "step": "question_number_validation",
            "issue": "unknown_module",
            "detail": f"No expected range defined for subject='{subject_code}' module='{module_code}' — range check skipped",
        })

    # Duplicate check
    valid_nums = [n for n in nums if n is not None]
    seen: set[int] = set()
    for i, n in enumerate(valid_nums):
        if n in seen:
            warnings.append({
                "step": "question_number_validation",
                "issue": "duplicate",
                "value": n,
                "detail": f"question number {n} appears more than once in this batch",
            })
        seen.add(n)

    # Contiguous sequence check
    sorted_nums = sorted(seen)
    if len(sorted_nums) >= 2:
        expected = list(range(sorted_nums[0], sorted_nums[0] + len(sorted_nums)))
        if sorted_nums != expected:
            gaps = [n for n in expected if n not in seen]
            warnings.append({
                "step": "question_number_validation",
                "issue": "non_contiguous",
                "found": sorted_nums,
                "gaps": gaps,
                "detail": f"question numbers are not contiguous — found {sorted_nums}, gaps at {gaps}",
            })

    return warnings


def _scan_qnums_from_ocr(ocr_text: str) -> list[int]:
    """Extract question numbers from raw OCR text using regex heuristics.

    GLM-OCR emits each question number on its own line before the passage text.
    This scan looks for standalone integers (1–50) that appear on a line by
    themselves, returning them in document order as a cross-check source.
    """
    import re
    # Collect every bare integer candidate in document order first, then walk
    # them enforcing a strictly contiguous +1 sequence after the first value.
    # Question numbers in a module are 1, 2, 3, … so any candidate that does
    # not equal previous+1 (passage line numbers like 5, 10, 15; OCR misreads;
    # stray duplicates) is dropped. If the very first candidate is a passage
    # line number rather than a real question number, the function will
    # return a short list — but _verify_qnums_against_ocr bails out when the
    # scan is sparser than the question count, which keeps that case safe.
    candidates: list[int] = []
    for line in ocr_text.splitlines():
        stripped = line.strip()
        # Match a bare number, optionally followed by . or ) — e.g. "3", "3.", "3)"
        m = re.fullmatch(r"(\d{1,2})[.)]?", stripped)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 50:
                candidates.append(n)

    found: list[int] = []
    for n in candidates:
        if not found:
            found.append(n)
        elif n == found[-1] + 1:
            found.append(n)
    return found


def _verify_qnums_against_ocr(
    questions: list[dict],
    ocr_text: str,
) -> list[dict]:
    """Cross-check LLM-extracted question numbers against OCR-scanned numbers.

    Returns mismatch warning dicts. Empty list means the two sources agree.
    Only fires when the OCR scan finds at least as many numbers as there are
    questions — if OCR picked up fewer numbers we can't do a reliable comparison.
    """
    warnings: list[dict] = []
    ocr_nums = _scan_qnums_from_ocr(ocr_text)

    if not ocr_nums or len(ocr_nums) < len(questions):
        return []  # OCR scan too sparse to cross-check

    for i, q in enumerate(questions):
        llm_num = q.get("source_question_number")
        try:
            llm_int = int(llm_num) if llm_num is not None else None
        except (TypeError, ValueError):
            llm_int = None

        ocr_int = ocr_nums[i] if i < len(ocr_nums) else None

        if llm_int is None and ocr_int is not None:
            warnings.append({
                "step": "qnum_ocr_crosscheck",
                "question_index": i,
                "issue": "llm_missing_ocr_found",
                "ocr_value": ocr_int,
                "detail": f"question_index {i}: LLM returned no number but OCR text shows {ocr_int}",
            })
        elif llm_int is not None and ocr_int is not None and llm_int != ocr_int:
            warnings.append({
                "step": "qnum_ocr_crosscheck",
                "question_index": i,
                "issue": "mismatch",
                "llm_value": llm_int,
                "ocr_value": ocr_int,
                "detail": f"question_index {i}: LLM extracted {llm_int} but OCR text shows {ocr_int}",
            })

    return warnings


def _clean_option_label(label: str | None) -> str:
    """Normalize VLM-emitted option labels like 'A)', 'A.', 'a' → 'A'."""
    if not label:
        return label or ""
    return label.strip().rstrip(").").upper()


# High-confidence SAT stem openers — phrases that almost always begin a question
# stem rather than passage content. Ambiguous phrases like "the author" or
# "the narrator" are excluded because they commonly appear inside passages.
_HIGH_CONFIDENCE_STEM_OPENERS: tuple[str, ...] = (
    "as used in the text",
    "as used in line",
    "based on the passage",
    "based on the text",
    "which choice",
    "which quotation",
    "what does the word",
    "what is the word",
    "which finding",
    "according to the passage",
    "according to the text",
    "over the course of the passage",
    "over the course of the text",
    "it can reasonably be inferred",
    "it can be inferred",
    "which statement",
    "which claim",
    "which idea",
    "which sentence",
    "which provides",
    "which best",
    "which most",
    "which most effectively",
    "which most logically",
    "what is the main",
    "what is the primary",
    "how does the",
    "how is the",
    "why does the",
)

# Passage-bearing stimulus modes — only these should have passage_text.
_PASSAGE_MODES = frozenset({
    "passage_excerpt", "paired_passages", "table_and_passage", "graph_and_passage",
    "notes_and_prompt",
})


def _split_passage_from_question(q_data: dict) -> None:
    """Detect passage content embedded in question_text and split it out.

    Many VLMs dump the passage + stem into ``question_text`` instead of
    separating them into ``passage_text``. This function looks for a
    stem-opener pattern at a sentence boundary and moves everything
    before it into ``passage_text``. Mutates ``q_data`` in place.
    """
    if q_data.get("passage_text"):
        return  # already separated

    qt: str = q_data.get("question_text", "")
    if not qt:
        return

    # Search for the first high-confidence stem-opener in the text.
    # The stem must be at a sentence boundary — preceded by a period,
    # blank (_______), newline, or the start of the text.
    best_pos = -1
    qt_lower = qt.lower()
    for opener in _HIGH_CONFIDENCE_STEM_OPENERS:
        pos = 0
        while True:
            idx = qt_lower.find(opener, pos)
            if idx < 0:
                break
            # Check that the opener is at a sentence boundary.
            at_boundary = idx == 0
            if not at_boundary:
                # Two boundary patterns:
                # 1. After a period/sentence-end (possibly with spaces): "text. Which..."
                # 2. After a fill-in-the-blank (_______): "_______ Which..."
                #    The _______ itself counts as a boundary.
                prefix = qt[:idx].rstrip()
                if prefix.endswith("_______"):
                    at_boundary = True
                else:
                    # Look back through spaces/underscores/dashes for a period
                    for back in range(1, min(11, idx + 1)):
                        c = qt[idx - back]
                        if c in ".!?\n":
                            at_boundary = True
                            break
                        if c not in " _-":
                            break
            if at_boundary:
                # Only split if there's meaningful passage content before
                # the stem — skip if the opener IS the entire question_text.
                passage_part = qt[:idx].strip()
                if len(passage_part) > 30:
                    if best_pos < 0 or idx < best_pos:
                        best_pos = idx
                    break  # take the first boundary match for this opener
            pos = idx + 1

    if best_pos > 0:
        passage = qt[:best_pos].strip()
        stem = qt[best_pos:].strip()
        q_data["passage_text"] = passage
        q_data["question_text"] = stem


def _recover_passage_from_raw_text(q_data: dict, raw_text: str) -> None:
    """Recover a dropped passage from pymupdf raw_text.

    When the VLM completely omits a passage (e.g., Q1's passage about
    "The King's Coin"), this function locates the passage in the pymupdf
    raw text by finding the question stem first, then looking backwards
    for the question number marker. Mutates ``q_data`` in place.
    """
    if q_data.get("passage_text"):
        return  # already have passage

    mode = q_data.get("stimulus_mode_key", "")
    if mode not in _PASSAGE_MODES:
        return  # no passage expected for this mode

    qnum = q_data.get("source_question_number")
    if qnum is None:
        return

    stem = q_data.get("question_text", "").strip()
    if not stem:
        return

    # Strategy: find the stem in raw_text first, then look backwards for
    # the question number. This avoids false matches on page headers like
    # "Module \n1 \nReading and Writing" which also contain the number 1.
    stem_pos = _find_stem_in_raw_text(stem, raw_text)
    if stem_pos < 0:
        return

    # Look backwards from the stem position for the question number marker.
    # The marker is typically "\n{N}\n" on its own line, or "  {N}  " inline.
    qnum_str = str(int(qnum))
    # Search backwards for a line that is just the question number.
    # SAT passages can be long (multiple paragraphs), so allow up to 2000 chars.
    search_start = max(0, stem_pos - 2000)
    chunk = raw_text[search_start:stem_pos]
    # Find the LAST occurrence of the question number on its own line
    qnum_pattern = re.compile(rf"(?:^|\n)\s*{qnum_str}\s*\n")
    best_match = None
    for m in qnum_pattern.finditer(chunk):
        best_match = m
    if best_match is None:
        return

    # Extract text from the question number to the stem
    abs_start = search_start + best_match.end()
    passage = raw_text[abs_start:stem_pos].strip()
    if len(passage) < 30:
        return  # too short to be a real passage

    q_data["passage_text"] = passage


def _find_stem_in_raw_text(stem: str, raw_text: str) -> int:
    """Find the position of a question stem in pymupdf raw text.

    Handles whitespace differences between the VLM-extracted stem and
    the pymupdf text (line breaks, extra spaces, etc.).
    """
    # Try progressively shorter exact anchors (fast path)
    for length in (40, 30, 20):
        anchor = stem[:length]
        pos = raw_text.find(anchor)
        if pos >= 0:
            return pos

    # Try first few words as anchor — handles line-break differences
    words = stem.split()
    if len(words) >= 4:
        word_anchor = " ".join(words[:4])
        pos = raw_text.find(word_anchor)
        if pos >= 0:
            return pos
        # Also try with the words on separate lines
        for i in range(len(raw_text) - len(word_anchor)):
            if re.sub(r"\s+", " ", raw_text[i:i + len(word_anchor) + 20])[:len(word_anchor)] == word_anchor:
                return i

    return -1


def _normalize_extracted_questions(extract_root: dict, raw_text: str = "") -> tuple[list[dict], str | None, dict, list[dict]]:
    """Normalize LLM extract output to a list of per-question dicts.

    Handles both the new format (``{passage_text, questions: [...]}``) and
    the legacy single-question format (flat top-level fields).

    Returns ``(questions, shared_passage, shared_source, norm_errors)`` where
    each question dict has its own ``question_text``, ``options``,
    ``correct_option_label``, ``source_question_number``, etc., with shared
    ``passage_text`` and source fields merged in. ``norm_errors`` surfaces
    dropped questions (empty stem after passage split, duplicate composite key)
    as validation errors so silent loss is visible in ``validation_errors_jsonb``.
    """
    shared_passage = extract_root.get("passage_text")
    shared_source = {
        "source_exam_code": extract_root.get("source_exam_code"),
        "source_subject_code": extract_root.get("source_subject_code"),
        "source_section_code": extract_root.get("source_section_code"),
        "source_module_code": extract_root.get("source_module_code"),
    }

    if "questions" in extract_root and isinstance(extract_root["questions"], list):
        raw_questions = extract_root["questions"]
    else:
        raw_questions = [extract_root]

    # Dedupe by (question_text, source_question_number) so SAT-shaped near-duplicate
    # stems ("Which choice best…", "As used in the text…") are retained when their
    # question numbers differ. The single-stem key was destructive: after
    # _split_passage_from_question carved passages off, multiple early questions
    # collapsed to the same generic stem and got silently dropped.
    seen_keys: set[tuple[str, object]] = set()
    questions = []
    norm_errors: list[dict] = []
    for raw_idx, q in enumerate(raw_questions):
        enriched = dict(q)
        for k, v in shared_source.items():
            if v and not enriched.get(k):
                enriched[k] = v
        if shared_passage and not enriched.get("passage_text"):
            enriched["passage_text"] = shared_passage

        # Post-extraction: separate passage from question_text when VLM
        # dumps passage content into the stem field.
        _split_passage_from_question(enriched)

        # Normalize correct_option_label: "A)" / "A." / "a" → "A"
        if "correct_option_label" in enriched:
            enriched["correct_option_label"] = _clean_option_label(enriched["correct_option_label"])

        # Normalize each option label
        for opt in enriched.get("options", []):
            if isinstance(opt, dict) and "label" in opt:
                opt["label"] = _clean_option_label(opt["label"])

        # Backfill positional labels when the LLM emitted 4 options with no
        # labels at all (a recurring failure mode that otherwise fails the
        # validator with "Option labels must be exactly {A, B, C, D}, got ['']").
        opts = enriched.get("options", [])
        if len(opts) == 4 and all(
            isinstance(o, dict) and not o.get("label") for o in opts
        ):
            for idx, opt in enumerate(opts):
                opt["label"] = "ABCD"[idx]

        # Drop blanks and surface as a validation error so silent loss is
        # visible. Most often triggers when _split_passage_from_question moves
        # the entire stem into passage_text.
        q_text_key = (enriched.get("question_text") or "").strip().lower()
        if not q_text_key:
            logger.warning(
                "_normalize_extracted_questions: skipping entry with empty question_text (raw index %d)",
                raw_idx,
            )
            norm_errors.append({
                "step": "normalize",
                "issue": "dropped_empty_stem",
                "raw_index": raw_idx,
                "source_question_number": enriched.get("source_question_number"),
                "detail": (
                    f"raw_index {raw_idx}: question_text empty after passage split — "
                    f"source_question_number={enriched.get('source_question_number')!r}"
                ),
            })
            continue

        # Composite dedupe key. The LLM's source_question_number is included so
        # SAT stems shared across multiple questions are not collapsed.
        dedupe_key = (q_text_key, enriched.get("source_question_number"))
        if dedupe_key in seen_keys:
            norm_errors.append({
                "step": "normalize",
                "issue": "dropped_duplicate_stem",
                "raw_index": raw_idx,
                "source_question_number": enriched.get("source_question_number"),
                "detail": (
                    f"raw_index {raw_idx}: duplicate (question_text, source_question_number) — "
                    f"source_question_number={enriched.get('source_question_number')!r}"
                ),
            })
            continue
        seen_keys.add(dedupe_key)
        questions.append(enriched)

    # Pymupdf fallback: recover passages the VLM completely dropped.
    # For the VLM-fused path, raw_text is the sentinel "_vision_fused_";
    # the actual pymupdf text lives in extract_root["raw_text"].
    _pymupdf_raw = raw_text
    if raw_text == "_vision_fused_":
        _pymupdf_raw = (extract_root or {}).get("raw_text", "")
    if _pymupdf_raw:
        for enriched in questions:
            _recover_passage_from_raw_text(enriched, _pymupdf_raw)

    return questions, shared_passage, shared_source, norm_errors


async def _persist_single_question(
    db: AsyncSession,
    job: QuestionJob,
    q_data: dict,
    annotate_json: dict,
    passage_text: str | None,
    passage_group_id: uuid.UUID | None,
    overlaps: list,
    section_code: str | None,
    question_index: int = 0,
    layout_data: dict | None = None,
    layout_paths: dict | None = None,
    provider=None,
    suspect_question_indices: set[int] | None = None,
    defer_activation: bool = False,
) -> uuid.UUID:
    """Create Question + QuestionVersion + QuestionAnnotation + QuestionOption rows.

    Returns the newly created ``question_id`` UUID.
    Official questions with complete metadata use a deterministic UUID5 so that
    re-ingesting the same question produces the same ID (idempotent).
    """
    now = datetime.now(timezone.utc)

    exam = q_data.get("source_exam_code")
    subject = q_data.get("source_subject_code")
    section = q_data.get("source_section_code") or section_code
    module = q_data.get("source_module_code")
    q_num = q_data.get("source_question_number")

    is_suspect = bool(suspect_question_indices and question_index in suspect_question_indices)
    if not is_suspect and job.content_origin == "official" and all([exam, subject, section, module, q_num]):
        try:
            question_id = _official_question_uuid(exam, subject, section, module, int(q_num))
        except (TypeError, ValueError):
            logger.warning("source_question_number %r is not an integer — using UUID4", q_num)
            question_id = uuid.uuid4()
    else:
        question_id = uuid.uuid4()

    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()

    # Idempotency: skip if this official question already exists
    if job.content_origin == "official":
        existing_q = await db.get(Question, question_id)
        if existing_q:
            logger.info("Official question %s already exists — skipping re-insert", question_id)
            return question_id

    official_auto_activate = _should_auto_activate_official(get_settings())
    if defer_activation:
        # Job carries validation warnings — hold the question out of student
        # rotation as a draft until an admin clears it from the review queue.
        practice_status = "draft"
    else:
        practice_status = (
            "active"
            if job.content_origin == "official" and official_auto_activate
            else "draft" if job.content_origin == "official" else "active"
        )
    overlap_status = "possible" if overlaps else "none"

    question = Question(
        id=question_id,
        content_origin=job.content_origin,
        source_exam_code=q_data.get("source_exam_code"),
        source_subject_code=q_data.get("source_subject_code"),
        source_section_code=q_data.get("source_section_code"),
        source_module_code=q_data.get("source_module_code"),
        source_question_number=q_data.get("source_question_number"),
        stimulus_mode_key=q_data.get("stimulus_mode_key"),
        stem_type_key=q_data.get("stem_type_key"),
        current_question_text=q_data.get("question_text", ""),
        current_passage_text=passage_text or q_data.get("passage_text"),
        current_paired_passage_text=q_data.get("paired_passage_text"),
        current_underlined_text=q_data.get("underlined_text"),
        current_correct_option_label=q_data.get("correct_option_label", ""),
        current_explanation_text=annotate_json.get("explanation_short", ""),
        practice_status=practice_status,
        official_overlap_status=overlap_status,
        passage_group_id=passage_group_id,
        is_admin_edited=False,
        metadata_managed_by_llm=True,
        created_at=now,
        updated_at=now,
    )
    db.add(question)

    db.add(QuestionVersion(
        id=version_id,
        question_id=question_id,
        version_number=1,
        change_source="ingest",
        question_text=q_data.get("question_text", ""),
        passage_text=passage_text or q_data.get("passage_text"),
        paired_passage_text=q_data.get("paired_passage_text"),
        underlined_text=q_data.get("underlined_text"),
        choices_jsonb=q_data.get("options", []),
        correct_option_label=q_data.get("correct_option_label", ""),
        explanation_text=annotate_json.get("explanation_short"),
        created_at=now,
    ))

    await db.flush()

    annotate_json = sanitize_annotation_keys(
        annotate_json, job_id=str(job.id)
    )
    db.add(QuestionAnnotation(
        id=annotation_id,
        question_id=question_id,
        question_version_id=version_id,
        provider_name=job.provider_name,
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        rules_version=job.rules_version,
        annotation_jsonb=annotate_json,
        explanation_jsonb={"explanation_full": annotate_json.get("explanation_full", "")},
        generation_profile_jsonb=_generation_profile_payload(q_data, annotate_json),
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))

    await db.flush()

    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id

    correct_label = q_data.get("correct_option_label", "")
    opt_analyses = option_analyses_by_label(annotate_json)
    for opt in q_data.get("options", []):
        label = opt.get("label", "")
        db.add(QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=version_id,
            option_label=label,
            option_text=opt.get("text", ""),
            is_correct=label == correct_label,
            option_role="correct" if label == correct_label else "distractor",
            created_at=now,
            **option_annotation_fields(opt_analyses.get(label, {})),
        ))

    # Link asset to the first created question
    if job.raw_asset_id and not job.question_id:
        asset = await db.get(QuestionAsset, job.raw_asset_id)
        if asset:
            asset.question_id = question_id
            if not asset.source_section_code and section_code:
                asset.source_section_code = section_code

    if overlaps:
        from app.pipeline.overlap import persist_overlap_relations
        await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)

    # Layout enrichment: match detected regions, crop, and optionally annotate
    crop_path = None
    matched_region = None
    page_number = _source_page_number(q_data, 0)
    page_images_data = (job.pass1_json or {}).get("_page_images", [])

    if layout_data:
        matched_region = match_region_for_question(layout_data, q_data, question_index)
        if matched_region:
            result = crop_and_store(matched_region, page_images_data, question_id)
            if result:
                crop_path = result.storage_path

    # layout_paths is keyed by 0-based page_index (from enumerate), while
    # page_number from _source_page_number may be 1-based (LLM output).
    # Prefer the matched region's page_index; fall back to both keys.
    if matched_region is not None:
        layout_json_path = (layout_paths or {}).get(matched_region.page_index)
        source_span_page_number = _page_number_for_region(job, matched_region.page_index)
    else:
        layout_json_path = (
            (layout_paths or {}).get(page_number)
            or (layout_paths or {}).get(page_number - 1)
        )
        source_span_page_number = page_number

    source_span = _build_question_source_span(
        job=job,
        question_id=question_id,
        q_data=q_data,
        question_index=question_index,
        crop_path=crop_path,
        layout_json_path=layout_json_path,
        source_page_number=source_span_page_number,
    )
    db.add(source_span)
    await db.flush()

    # Stimulus region enrichment: crop table/chart/figure regions detected by layout pass,
    # optionally annotate each via vision LLM, and create provenance spans.
    stimulus_source_spans: list[QuestionSourceSpan] = []
    if layout_data and matched_region:
        s_regions = match_stimulus_regions_for_question(layout_data, matched_region)
        for s_region in s_regions:
            s_kind = _crop_kind_for_stimulus(s_region.type)
            s_crop_result = crop_and_store(s_region, page_images_data, question_id, kind=s_kind)
            s_source_span_id = uuid.uuid4()
            s_page_number = _page_number_for_region(job, s_region.page_index)
            s_layout_json_path = (layout_paths or {}).get(s_region.page_index)

            # Vision annotation of the crop — feeds structured_data and render_hints
            s_annotation: dict = {}
            if s_crop_result and provider:
                s_annotation = await _annotate_layout_stimulus(
                    provider=provider,
                    crop_path=s_crop_result.storage_path,
                    region_type=s_region.type,
                )

            # Merge into q_data["stimulus_assets"] so _build_stimulus_asset_rows picks it up
            existing_assets = q_data.get("stimulus_assets")
            if not isinstance(existing_assets, list):
                existing_assets = []
            existing_assets.append({
                "stimulus_type": s_region.type,
                "title": s_annotation.get("title"),
                "structured_data": s_annotation.get("structured_data"),
                "render_hints": s_annotation.get("render_hints"),
                "_layout_label": s_region.label,
                "_crop_path": s_crop_result.storage_path if s_crop_result else None,
                "_layout_json_path": s_layout_json_path,
                "_source_span_id": s_source_span_id,
                "_source_page_number": s_page_number,
            })
            q_data["stimulus_assets"] = existing_assets

            stimulus_source_spans.append(QuestionSourceSpan(
                id=s_source_span_id,
                question_id=question_id,
                question_job_id=job.id,
                raw_asset_id=job.raw_asset_id,
                source_page_number=s_page_number,
                source_region_role=s_region.type,
                extraction_method=_extraction_method(job),
                rendered_page_path=_rendered_page_path_for_region(job, s_region.page_index),
                crop_path=s_crop_result.storage_path if s_crop_result else None,
                ocr_text_path=None,
                layout_json_path=s_layout_json_path,
                pymupdf_text=None,
                ocr_text=None,
                diagnostics_jsonb={
                    "layout_label": s_region.label,
                    "layout_bbox": s_region.bbox,
                    "stimulus_annotation": s_annotation,
                },
                confidence_jsonb=None,
                created_at=datetime.now(timezone.utc),
            ))

    for s_span in stimulus_source_spans:
        db.add(s_span)

    for stimulus in _build_stimulus_asset_rows(
        job=job,
        question_id=question_id,
        q_data=q_data,
        source_span_id=source_span.id,
    ):
        db.add(stimulus)

    return question_id


def _source_page_number(q_data: dict, fallback: int = 0) -> int:
    for key in ("source_page_number", "page_number", "page"):
        value = q_data.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                break
    return fallback


def _extraction_method(job: QuestionJob) -> str:
    ocr_meta = (job.pass1_json or {}).get("_ocr_meta") or {}
    strategy = (ocr_meta.get("strategy") or "").lower()
    if strategy == "glm":
        return "glm_ocr"
    if strategy == "deepseek":
        return "deepseek_ocr"
    if strategy in {"ollama", "anthropic", "openai"}:
        return "vlm_layout"
    return "pymupdf"


def _rendered_page_path(job: QuestionJob, page_number: int) -> str | None:
    for image in (job.pass1_json or {}).get("_page_images", []):
        try:
            image_page = int(image.get("page_number", 0))
        except (TypeError, ValueError):
            image_page = 0
        if image_page == page_number and image.get("storage_path"):
            return image["storage_path"]
    images = (job.pass1_json or {}).get("_page_images", [])
    if images and images[0].get("storage_path"):
        return images[0]["storage_path"]
    return None


def _page_number_for_region(job: QuestionJob, page_index: int) -> int:
    images = (job.pass1_json or {}).get("_page_images", [])
    if 0 <= page_index < len(images):
        try:
            return int(images[page_index].get("page_number", page_index))
        except (TypeError, ValueError):
            return page_index
    return page_index


def _rendered_page_path_for_region(job: QuestionJob, page_index: int) -> str | None:
    images = (job.pass1_json or {}).get("_page_images", [])
    if 0 <= page_index < len(images) and images[page_index].get("storage_path"):
        return images[page_index]["storage_path"]
    return _rendered_page_path(job, _page_number_for_region(job, page_index))


def _first_ocr_text_path(job: QuestionJob) -> str | None:
    for artifact in (job.pass1_json or {}).get("_ocr_artifacts", []):
        if artifact.get("kind") == "ocr_text" and artifact.get("storage_path"):
            return artifact["storage_path"]
    return None


def _build_question_source_span(
    job: QuestionJob,
    question_id: uuid.UUID,
    q_data: dict,
    question_index: int,
    crop_path: str | None = None,
    layout_json_path: str | None = None,
    source_page_number: int | None = None,
) -> QuestionSourceSpan:
    page_number = source_page_number if source_page_number is not None else _source_page_number(q_data, 0)
    extraction_method = _extraction_method(job)
    raw_text = (job.pass1_json or {}).get("raw_text")
    ocr_meta = (job.pass1_json or {}).get("_ocr_meta")

    return QuestionSourceSpan(
        id=uuid.uuid4(),
        question_id=question_id,
        question_job_id=job.id,
        raw_asset_id=job.raw_asset_id,
        source_page_number=page_number,
        source_region_role="question_block",
        extraction_method=extraction_method,
        rendered_page_path=_rendered_page_path(job, page_number),
        crop_path=crop_path,
        ocr_text_path=_first_ocr_text_path(job),
        layout_json_path=layout_json_path,
        pymupdf_text=raw_text if extraction_method == "pymupdf" else None,
        ocr_text=raw_text if extraction_method != "pymupdf" else None,
        diagnostics_jsonb={
            "ocr_meta": ocr_meta,
            "llm_meta": (job.pass1_json or {}).get("_llm_meta"),
            "source_question_number": q_data.get("source_question_number"),
        },
        confidence_jsonb=q_data.get("source_confidence_jsonb") or q_data.get("confidence_jsonb"),
        created_at=datetime.now(timezone.utc),
    )


def _stimulus_candidates(q_data: dict) -> list[dict]:
    candidates: list[dict] = []
    for key in ("stimulus_assets", "visual_assets"):
        values = q_data.get(key)
        if isinstance(values, list):
            candidates.extend(v for v in values if isinstance(v, dict))
    for key, stimulus_type in (("tables", "table"), ("charts", "chart"), ("graphs", "graph"), ("figures", "figure")):
        values = q_data.get(key)
        if isinstance(values, list):
            for value in values:
                if isinstance(value, dict):
                    candidates.append({"stimulus_type": stimulus_type, **value})
    return candidates


def _stimulus_kind(stimulus_type: str) -> str:
    normalized = (stimulus_type or "").lower()
    if normalized == "table":
        return "table_asset"
    if normalized in {"chart", "graph"}:
        return "chart_asset"
    return "figure_asset"


def _crop_kind_for_stimulus(stimulus_type: str) -> str:
    normalized = (stimulus_type or "").lower()
    if normalized == "table":
        return "table_crop"
    if normalized in {"chart", "graph"}:
        return "chart_crop"
    return "figure_crop"


async def _annotate_layout_stimulus(provider, crop_path: str, region_type: str) -> dict:
    """Vision-annotate a cropped stimulus region. Returns annotation dict or {} on failure."""
    import base64
    from app.storage.object_store import read_object
    from app.llm.base import ImageContent
    from app.prompts.stimulus_prompt import build_stimulus_annotation_prompt

    try:
        crop_bytes = read_object(crop_path)
        b64 = base64.standard_b64encode(crop_bytes).decode("utf-8")
        system, user = build_stimulus_annotation_prompt(region_type)
        result = await provider.complete_vision(
            system=system,
            user=user,
            images=[ImageContent(b64=b64, mime_type="image/png")],
            max_tokens=2048,
            temperature=0.0,
        )
        parsed = extract_json_from_text(result.raw_text, "vision", "stimulus")
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        logger.warning("Stimulus annotation failed for %s: %s", crop_path, exc)
        return {}


def _build_stimulus_asset_rows(
    job: QuestionJob,
    question_id: uuid.UUID,
    q_data: dict,
    source_span_id: uuid.UUID,
) -> list[QuestionStimulusAsset]:
    rows: list[QuestionStimulusAsset] = []
    for candidate in _stimulus_candidates(q_data):
        stimulus_type = (candidate.get("stimulus_type") or candidate.get("type") or "figure").lower()
        asset_id = uuid.uuid4()
        page_number = _source_page_number(
            candidate,
            candidate.get("_source_page_number", _source_page_number(q_data, 0)),
        )
        candidate_source_span_id = candidate.get("_source_span_id") or source_span_id
        crop_path = candidate.get("_crop_path")
        layout_json_path = candidate.get("_layout_json_path")
        payload = {
            "question_id": str(question_id),
            "question_job_id": str(job.id),
            "raw_asset_id": str(job.raw_asset_id) if job.raw_asset_id else None,
            "stimulus_type": stimulus_type,
            "source_page_number": page_number,
            "source_span_id": str(candidate_source_span_id) if candidate_source_span_id else None,
            "crop_path": crop_path,
            "layout_json_path": layout_json_path,
            "title": candidate.get("title"),
            "structured_data": candidate.get("structured_data") or candidate.get("data"),
            "render_hints": candidate.get("render_hints"),
        }
        stored = put_object(
            _stimulus_kind(stimulus_type),
            {
                "question_id": question_id,
                "asset_id": asset_id,
                "page_number": page_number,
            },
            json.dumps(payload, indent=2, sort_keys=True),
            filename=f"{asset_id}.json",
            mime_type="application/json",
        )
        rows.append(QuestionStimulusAsset(
            id=asset_id,
            question_id=question_id,
            question_job_id=job.id,
            raw_asset_id=job.raw_asset_id,
            stimulus_type=stimulus_type,
            storage_path=stored.storage_path,
            source_page_number=page_number,
            source_span_id=candidate_source_span_id,
            title=candidate.get("title"),
            structured_data_jsonb=payload["structured_data"],
            render_hints_jsonb=payload["render_hints"],
            created_at=datetime.now(timezone.utc),
        ))
    return rows


def _export_question(job: QuestionJob, q_data: dict, annotate_json: dict, question_id: uuid.UUID) -> None:
    """Export a single question to YAML after successful persistence."""
    from app.storage.yaml_export import export_official_question, export_generated_question
    from app.config import get_settings

    settings = get_settings()
    source_meta = (job.pass1_json or {}).get("source_metadata", {})
    exam_code = q_data.get("source_exam_code") or source_meta.get("source_exam_code")
    section_code = q_data.get("source_section_code") or source_meta.get("source_section_code")
    module_code = q_data.get("source_module_code") or source_meta.get("source_module_code")

    if job.content_origin == "official" and exam_code and module_code:
        export_official_question(
            question_id=str(question_id),
            exam_code=exam_code,
            module_code=module_code,
            question_number=q_data.get("source_question_number"),
            extract_json=q_data,
            annotate_json=annotate_json,
            section_code=section_code,
            base_dir=settings.local_archive_mirror,
        )
    elif job.content_origin in ("unofficial", "generated"):
        export_generated_question(
            question_id=str(question_id),
            extract_json=q_data,
            annotate_json=annotate_json,
            base_dir=settings.local_archive_mirror,
        )


def _store_page_render(
    *,
    asset_id: uuid.UUID,
    job_id: uuid.UUID,
    content_origin: str,
    source_metadata: dict,
    source_stem: str,
    page_number: int,
    b64: str,
    ext: str,
) -> dict:
    decoded = base64.b64decode(b64)
    if len(decoded) > MAX_PAGE_RENDER_BYTES:
        logger.warning(
            "Page render for job %s page %d is %d bytes (limit %d); skipping",
            job_id, page_number, len(decoded), MAX_PAGE_RENDER_BYTES,
        )
        return None
    stored = put_object(
        "rendered_page",
        {
            "asset_id": asset_id,
            "job_id": job_id,
            "content_origin": content_origin,
            "source_exam_code": source_metadata.get("source_exam_code"),
            "source_subject_code": source_metadata.get("source_subject_code"),
            "source_section_code": source_metadata.get("source_section_code"),
            "source_module_code": source_metadata.get("source_module_code"),
            "page_number": page_number,
            "ext": ext,
        },
        decoded,
        filename=f"{source_stem}_p{page_number:03d}.{ext}",
        mime_type=f"image/{ext}",
    )
    return {
        "path": str(stored.local_path) if stored.local_path else None,
        "storage_path": stored.storage_path,
        "mime_type": f"image/{ext}",
        "page_number": page_number,
    }


def _store_pdf_page_renders(
    *,
    pdf_result: dict,
    asset_id: uuid.UUID,
    job_id: uuid.UUID,
    content_origin: str,
    source_metadata: dict,
    source_stem: str,
    max_images: int,
) -> list[dict]:
    """Store one full-page render per PDF page for OCR/layout enrichment."""
    page_images = []
    for page in pdf_result.get("pages", [])[:max_images]:
        img = page.get("render")
        if not img:
            img = next((i for i in page.get("images", []) if i.get("rendered")), None)
        if not img:
            img = next(iter(page.get("images", [])), None)
        if not img:
            continue
        ext = img.get("ext", "png")
        stored = _store_page_render(
            asset_id=asset_id,
            job_id=job_id,
            content_origin=content_origin,
            source_metadata=source_metadata,
            source_stem=source_stem,
            page_number=page["page_number"],
            b64=img["b64"],
            ext=ext,
        )
        if stored is not None:
            page_images.append(stored)
    return page_images


def _store_raw_upload(
    *,
    asset_id: uuid.UUID,
    job_id: uuid.UUID,
    content_origin: str,
    source_metadata: dict,
    filename: str,
    content: bytes,
    mime_type: str,
) -> str:
    kind = "raw_source_pdf" if mime_type == "application/pdf" else "raw_source_file"
    stored = put_object(
        kind,
        {
            "asset_id": asset_id,
            "job_id": job_id,
            "content_origin": content_origin,
            "source_exam_code": source_metadata.get("source_exam_code"),
            "source_subject_code": source_metadata.get("source_subject_code"),
            "source_section_code": source_metadata.get("source_section_code"),
            "source_module_code": source_metadata.get("source_module_code"),
        },
        content,
        filename=filename,
        mime_type=mime_type,
    )
    return stored.storage_path


def _store_ocr_text(job: QuestionJob, raw_text: str, method: str) -> str:
    stored = put_object(
        "ocr_text",
        {
            "job_id": job.id,
            "page_number": 0,
            "method": method,
        },
        raw_text,
        filename=f"{method}.txt",
        mime_type="text/plain",
    )
    artifacts = list((job.pass1_json or {}).get("_ocr_artifacts", []))
    artifacts.append({
        "kind": "ocr_text",
        "method": method,
        "storage_path": stored.storage_path,
    })
    job.pass1_json = {
        **(job.pass1_json or {}),
        "_ocr_artifacts": artifacts,
    }
    return stored.storage_path


def _gc_page_images(archive_mirror: str, max_age_days: int = 30) -> int:
    """Delete image files older than max_age_days. Returns the count of deleted files."""
    import time
    images_dir = Path(archive_mirror) / "images"
    if not images_dir.exists():
        return 0
    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    for f in images_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
            deleted += 1
    return deleted


def _collect_page_images(pass1_json: dict) -> list:
    """Extract pre-stored page images from pass1_json._page_images.

    Entries may carry a ``path`` key (named file on disk) or an inline ``b64``.
    Path-based entries are preferred; b64 is the fallback for legacy records.
    """
    from app.llm.base import ImageContent
    raw_images = (pass1_json or {}).get("_page_images", [])
    result = []
    for img in raw_images:
        mime = img.get("mime_type", "image/png")
        page_idx = img.get("page_number", "?")
        if img.get("path"):
            try:
                b64 = base64.b64encode(Path(img["path"]).read_bytes()).decode()
                result.append(ImageContent(b64=b64, mime_type=mime))
                continue
            except (OSError, FileNotFoundError):
                pass  # fall through to b64 fallback
        if img.get("storage_path"):
            try:
                b64 = base64.b64encode(read_object(img["storage_path"])).decode()
                result.append(ImageContent(b64=b64, mime_type=mime))
                continue
            except (OSError, FileNotFoundError, NotImplementedError):
                pass
        if img.get("b64"):
            result.append(ImageContent(b64=img["b64"], mime_type=mime))
        else:
            logger.warning("_collect_page_images: dropping unreadable page image (page=%s)", page_idx)
    return result


def _resolve_ocr_strategy(requested: str | None, settings) -> str:
    """Resolve the effective OCR strategy.

    Returns "glm", "deepseek", "ollama", "anthropic", or "openai".
    Raises ValueError if the requested provider is unavailable.
    """
    strategy = (requested or settings.ocr_strategy or "auto").strip().lower()
    if strategy == "glm":
        return "glm"
    if strategy == "deepseek":
        if not settings.deepseek_ocr_base_url:
            raise ValueError("deepseek_ocr_base_url not configured")
        return "deepseek"
    if strategy in ("ollama", "vision"):
        return "ollama"
    if strategy == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("anthropic_api_key not configured")
        return "anthropic"
    if strategy == "openai":
        if not settings.openai_api_key:
            raise ValueError("openai_api_key not configured")
        return "openai"
    if strategy == "auto":
        if getattr(settings, "glm_ocr_model", None):
            return "glm"
        if settings.deepseek_ocr_base_url:
            return "deepseek"
        if settings.ocr_vision_provider == "ollama":
            return "ollama"
        if getattr(settings, "anthropic_api_key", None):
            return "anthropic"
        if getattr(settings, "openai_api_key", None):
            return "openai"
    raise ValueError(f"No OCR provider available for strategy '{strategy}'")


def _vlm_model_for_strategy(strategy: str, settings) -> str:
    """Return the model name to use for a VLM-fused OCR strategy."""
    if strategy == "ollama":
        return settings.ocr_vision_model
    if strategy == "anthropic":
        if settings.default_annotation_provider == "anthropic":
            return settings.default_annotation_model
        return "claude-sonnet-4-6"
    if strategy == "openai":
        return "gpt-4o"
    return ""


def _available_ocr_strategies(settings) -> list[str]:
    """Return all strategies that can run given the current configuration."""
    available = []
    if getattr(settings, "glm_ocr_model", None):
        available.append("glm")
    if settings.deepseek_ocr_base_url:
        available.append("deepseek")
    if settings.ocr_vision_provider == "ollama" or settings.ollama_base_url:
        available.append("ollama")
    if settings.anthropic_api_key:
        available.append("anthropic")
    if settings.openai_api_key:
        available.append("openai")
    return available


def _build_ocr_chain(resolved: str, settings) -> list[str]:
    """Ordered OCR strategy fallback chain.

    The resolved strategy runs first; the remaining available strategies follow
    with two-step OCR (``glm``, ``deepseek``) preferred over VLM-fused providers,
    so a failed run falls back to a two-step path before a VLM path.
    """
    if not getattr(settings, "ocr_fallback", True):
        return [resolved]
    preference = ["glm", "deepseek", "anthropic", "openai", "ollama"]
    available = set(_available_ocr_strategies(settings))
    chain = [resolved]
    for candidate in preference:
        if candidate != resolved and candidate in available:
            chain.append(candidate)
    return chain


async def _run_pipeline(job: QuestionJob, db: AsyncSession):
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt_parts, enforce_nullability, _detect_domain

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=_provider_api_key(settings, job.provider_name),
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )
    orch = JobOrchestrator(str(job.id), job.content_origin, job.job_type)

    raw_text = (job.pass1_json or {}).get("raw_text", "")
    page_images = _collect_page_images(job.pass1_json)
    ocr_strategy_req = (job.pass1_json or {}).get("_ocr_strategy")
    # Capture form metadata before pass1_json may be overwritten by LLM output
    form_meta = (job.pass1_json or {}).get("source_metadata", {})
    extract_root = None
    stimulus_provider = provider
    text_extraction_provider = provider
    text_extraction_provider_name = job.provider_name
    text_extraction_model_name = job.model_name

    if raw_text:
        # Embedded text present — check if some pages lack text (mixed PDF)
        _page_texts = [
            p.get("text", "") for p in (job.pass1_json or {}).get("_page_texts", [])
        ]
        if _page_texts and not all(t.strip() for t in _page_texts):
            # Some pages have no text — collect images for those pages only
            _empty_page_indices = [i for i, t in enumerate(_page_texts) if not t.strip()]
            _partial_images = [img for i, img in enumerate(page_images) if i in _empty_page_indices]
            if _partial_images:
                logger.info(
                    "Mixed PDF detected for job %s: %d/%d pages need OCR",
                    job.id, len(_empty_page_indices), len(_page_texts),
                )
                page_images = _partial_images[:settings.vision_max_images]
                # Fall through to OCR gate below with partial page images
                raw_text = ""  # Clear raw_text so OCR gate runs
                # Preserve full raw text for later concatenation
                _full_raw_text = (job.pass1_json or {}).get("raw_text", "")
            else:
                _full_raw_text = None
                job.pass1_json = {**(job.pass1_json or {}), "_ocr_strategy": "bypassed"}
        else:
            _full_raw_text = None
            job.pass1_json = {**(job.pass1_json or {}), "_ocr_strategy": "bypassed"}
    else:
        _full_raw_text = None

    if not raw_text and page_images:
        page_images = page_images[:settings.vision_max_images]
        # ── OCR gate ─────────────────────────────────────────────────────
        try:
            resolved_strategy = _resolve_ocr_strategy(ocr_strategy_req, settings)
        except ValueError as e:
            orch.fail("extracting", "no_ocr_provider", str(e))
            job.status = "failed"
            await db.commit()
            return

        # Ordered fallback chain — the resolved strategy runs first, then the
        # remaining available strategies with two-step OCR (glm, deepseek)
        # preferred over VLM-fused providers.
        _ocr_chain = _build_ocr_chain(resolved_strategy, settings)
        _ocr_done = False
        _ocr_last_err: Exception | None = None

        logger.info(
            "OCR chain for job %s: %s (fallback=%s)",
            job.id, _ocr_chain, settings.ocr_fallback,
        )

        for _idx, _strategy in enumerate(_ocr_chain):
            if _ocr_done:
                break
            if _idx > 0:
                logger.info(
                    "OCR fallback: trying strategy %s for job %s (previous strategy failed: %s)",
                    _strategy, job.id, _ocr_last_err,
                )

            if _strategy == "glm":
                # GLM-OCR: two-step — glm-ocr:latest via Ollama vision → raw_text → Pass 1 LLM
                from app.llm.ollama_provider import OllamaProvider as _OllamaProvider
                glm_model = settings.glm_ocr_model
                glm_provider = _OllamaProvider(
                    base_url=settings.ollama_base_url,
                    default_model=glm_model,
                )
                _GLM_OCR_SYSTEM = (
                    "You are a precise OCR engine. Extract all text from the image exactly as it "
                    "appears. Preserve question numbers on their own lines, option labels (A/B/C/D), "
                    "and blank markers (______). Return only the extracted text."
                )
                try:
                    ocr_result = await glm_provider.complete_vision(
                        system=_GLM_OCR_SYSTEM,
                        user="Extract all text from this image.",
                        images=page_images,
                        model=glm_model,
                        max_tokens=4096,
                        temperature=0.0,
                    )
                    raw_text = ocr_result.raw_text
                    ocr_text_path = _store_ocr_text(job, raw_text, "glm")
                    job.pass1_json = {
                        **(job.pass1_json or {}),
                        "raw_text": raw_text,
                        "_ocr_meta": {
                            "strategy": "glm",
                            "model": glm_model,
                            "page_count": len(page_images),
                            "latency_ms": ocr_result.latency_ms,
                            "token_usage": getattr(ocr_result, "token_usage", None) or {},
                            "ocr_text_path": ocr_text_path,
                        },
                    }
                    await db.commit()
                    text_extraction_provider = get_provider(
                        OCR_TEXT_EXTRACT_PROVIDER,
                        base_url=settings.ollama_base_url,
                        default_model=OCR_TEXT_EXTRACT_MODEL,
                    )
                    text_extraction_provider_name = OCR_TEXT_EXTRACT_PROVIDER
                    text_extraction_model_name = OCR_TEXT_EXTRACT_MODEL
                    logger.info(
                        "OCR strategy glm succeeded for job %s: two-step extraction via %s/%s",
                        job.id, text_extraction_provider_name, text_extraction_model_name,
                    )
                    _ocr_done = True
                except Exception as e:
                    _ocr_last_err = e
                    logger.warning("GLM-OCR failed (%s)", e)
                finally:
                    await glm_provider.close()

            elif _strategy == "deepseek":
                # Option A: DeepSeek OCR-2 → raw_text → Pass 1 LLM extraction
                from app.llm.factory import get_ocr_client
                ocr_client = get_ocr_client(
                    base_url=settings.deepseek_ocr_base_url,
                    model=settings.deepseek_ocr_model,
                )
                try:
                    ocr_result = await ocr_client.extract(page_images)
                    raw_text = ocr_result.raw_text
                    ocr_text_path = _store_ocr_text(job, raw_text, "deepseek")
                    job.pass1_json = {
                        **(job.pass1_json or {}),
                        "raw_text": raw_text,
                        "_ocr_meta": {
                            "strategy": "deepseek",
                            "model": settings.deepseek_ocr_model,
                            "page_count": len(page_images),
                            "latency_ms": ocr_result.latency_ms,
                            "token_usage": getattr(ocr_result, "token_usage", None) or {},
                            "ocr_text_path": ocr_text_path,
                        },
                    }
                    await db.commit()
                    text_extraction_provider = get_provider(
                        OCR_TEXT_EXTRACT_PROVIDER,
                        base_url=settings.ollama_base_url,
                        default_model=OCR_TEXT_EXTRACT_MODEL,
                    )
                    text_extraction_provider_name = OCR_TEXT_EXTRACT_PROVIDER
                    text_extraction_model_name = OCR_TEXT_EXTRACT_MODEL
                    logger.info(
                        "OCR strategy deepseek succeeded for job %s: two-step extraction via %s/%s",
                        job.id, text_extraction_provider_name, text_extraction_model_name,
                    )
                    _ocr_done = True
                except Exception as e:
                    _ocr_last_err = e
                    logger.warning("DeepSeek OCR failed (%s)", e)

            elif _strategy in ("ollama", "anthropic", "openai"):
                # Option B/C/D: VLM fused — one provider call for both OCR and
                # extraction, with a 3-attempt JSON-parse retry.
                from app.prompts.extract_prompt import build_vision_extract_prompt
                from app.llm.factory import get_provider as _get_provider

                orch.advance()
                job.status = "extracting"
                await db.commit()
                system, user = build_vision_extract_prompt(form_meta)
                vlm_model = _vlm_model_for_strategy(_strategy, settings)
                vlm_provider = _get_provider(
                    _strategy,
                    api_key=_provider_api_key(settings, _strategy),
                    base_url=settings.ollama_base_url if _strategy == "ollama" else "",
                    default_model=vlm_model,
                )
                stimulus_provider = vlm_provider
                for _v_attempt in range(3):
                    try:
                        vision_result = await vlm_provider.complete_vision(
                            system=system,
                            user=user,
                            images=page_images,
                            model=vlm_model,
                            max_tokens=16000,
                        )
                        ocr_text_path = _store_ocr_text(job, vision_result.raw_text, _strategy)
                        extract_root = extract_json_from_text(
                            vision_result.raw_text, _strategy, vlm_model
                        )
                        prior_pass1 = job.pass1_json or {}
                        job.pass1_json = {
                            **extract_root,
                            "_page_images": prior_pass1.get("_page_images", []),
                            "_ocr_artifacts": prior_pass1.get("_ocr_artifacts", []),
                            "_llm_meta": {
                                "provider": _strategy,
                                "model": vlm_model,
                                "latency_ms": vision_result.latency_ms,
                                "token_usage": getattr(vision_result, "token_usage", None) or {},
                            },
                            "_ocr_meta": {
                                "strategy": _strategy,
                                "model": vlm_model,
                                "page_count": len(page_images),
                                "latency_ms": vision_result.latency_ms,
                                "token_usage": getattr(vision_result, "token_usage", None) or {},
                                "ocr_text_path": ocr_text_path,
                            },
                            "source_metadata": form_meta,
                        }
                        await db.commit()
                        raw_text = "_vision_fused_"  # sentinel: Pass 1 is skipped below
                        logger.info(
                            "OCR strategy %s (VLM-fused) succeeded for job %s: extraction done inline, Pass 1 skipped",
                            _strategy, job.id,
                        )
                        _ocr_done = True
                        break
                    except ValueError as _vjson_err:
                        _ocr_last_err = _vjson_err
                        logger.warning(
                            "VLM fused JSON parse failed (strategy %s, attempt %d/3, job %s): %s",
                            _strategy, _v_attempt + 1, job.id, _vjson_err,
                        )
                        if _v_attempt < 2:
                            await asyncio.sleep(0.5 * (2 ** _v_attempt))
                    except Exception as _vexc:
                        _ocr_last_err = _vexc
                        logger.warning("VLM fused OCR failed (strategy %s): %s", _strategy, _vexc)
                        break

        if not _ocr_done:
            _err = _ocr_last_err or Exception("OCR failed and no fallback succeeded")
            orch.fail("extracting", "ocr_error", f"OCR failed: {_err}")
            job.status = "failed"
            job.validation_errors_jsonb = [error_payload("ocr", _err)]
            await db.commit()
            return
        # ── end OCR gate ──────────────────────────────────────────────────

        # For mixed PDFs: append OCR text to the preserved full raw text
        if _full_raw_text and raw_text and raw_text != "_vision_fused_":
            raw_text = _full_raw_text + "\n\n" + raw_text
            _full_raw_text = None  # consumed
        elif _full_raw_text and raw_text == "_vision_fused_":
            # VLM fused path already extracted questions from OCR pages;
            # we need to also run extraction on the text-bearing pages
            # and merge the results later in pass1
            _full_raw_text = None  # will be handled in pass1
            # For now, the VLM fused output already contains everything
            pass

    elif not raw_text:
        orch.fail("extracting", "no_raw_text", "No raw text available")
        job.status = "failed"
        await db.commit()
        return

    # Capture OCR provenance before Pass 1 may overwrite pass1_json
    ocr_meta = (job.pass1_json or {}).get("_ocr_meta")

    # ---- Pass 1: Extract (single call, may return multiple questions) ----
    if raw_text == "_vision_fused_":
        # VLM fused path: extract_root already populated in OCR gate
        pass
    else:
        orch.advance()
        job.status = "extracting"
        await db.commit()

        system, user = build_extract_prompt(raw_text[:100000], form_meta)
        extract_root = None
        _last_p1_err: Exception | None = None
        for _p1_attempt in range(3):
            try:
                if _should_disable_thinking(text_extraction_provider_name, text_extraction_model_name):
                    result = await text_extraction_provider.complete(
                        system=system,
                        user=user,
                        model=text_extraction_model_name,
                        max_tokens=getattr(settings, "extraction_max_tokens", 32000),
                        disable_thinking=True,
                    )
                else:
                    result = await text_extraction_provider.complete(
                        system=system,
                        user=user,
                        model=text_extraction_model_name,
                        max_tokens=getattr(settings, "extraction_max_tokens", 32000),
                    )
                extract_root = extract_json_from_text(
                    result.raw_text,
                    text_extraction_provider_name,
                    text_extraction_model_name,
                )
                # Structural check: JSON can parse cleanly yet still carry no
                # usable questions. Treat that as a retryable extraction failure
                # rather than proceeding to annotation with an empty payload.
                _extracted_qs = (
                    extract_root.get("questions")
                    if isinstance(extract_root.get("questions"), list)
                    else [extract_root]
                )
                if not any(
                    isinstance(eq, dict) and (eq.get("question_text") or "").strip()
                    for eq in _extracted_qs
                ):
                    raise ValueError(
                        "extraction returned no questions with non-empty question_text"
                    )
                prior_pass1 = job.pass1_json or {}
                job.pass1_json = {
                    **extract_root,
                    "raw_text": raw_text,
                    "_page_images": prior_pass1.get("_page_images", []),
                    "_ocr_artifacts": prior_pass1.get("_ocr_artifacts", []),
                    "source_metadata": form_meta,
                    "_llm_meta": {
                        "provider": result.provider,
                        "model": result.model,
                        "latency_ms": result.latency_ms,
                        "token_usage": getattr(result, "token_usage", None) or {},
                    },
                }
                if ocr_meta:
                    job.pass1_json["_ocr_meta"] = ocr_meta
                break
            except ValueError as _json_err:
                _last_p1_err = _json_err
                logger.warning(
                    "Pass 1 JSON parse failed (attempt %d/3, job %s): %s",
                    _p1_attempt + 1, job.id, _json_err,
                )
                if _p1_attempt < 2:
                    await asyncio.sleep(0.5 * (2 ** _p1_attempt))
            except Exception as _exc:
                _last_p1_err = _exc
                break
        if extract_root is None:
            orch.fail("extracting", "llm_error", str(_last_p1_err))
            job.status = "failed"
            job.validation_errors_jsonb = [error_payload("extracting", _last_p1_err)]
            await db.commit()
            return

    # Normalize to a list of per-question dicts (handles both new and legacy formats)
    questions_data, shared_passage, shared_source, norm_errors = _normalize_extracted_questions(
        extract_root, raw_text=raw_text,
    )
    if norm_errors:
        logger.warning(
            "Normalization dropped %d question(s) for job %s: %s",
            len(norm_errors), job.id, norm_errors,
        )

    # Record extraction count for benchmark comparison (questions after dedup, before validation)
    job.pass1_json = {
        **(job.pass1_json or {}),
        "_extracted_count": len(questions_data),
    }

    # Assign passage_group_id per distinct passage_text shared by 2+ questions.
    # Single-question passages and questions without passage_text get None.
    _passage_counts: dict[str, int] = {}
    for _q in questions_data:
        _pt = (_q.get("passage_text") or "").strip()
        if _pt:
            _passage_counts[_pt] = _passage_counts.get(_pt, 0) + 1
    _passage_to_group: dict[str, uuid.UUID] = {
        pt: uuid.uuid4() for pt, cnt in _passage_counts.items() if cnt > 1
    }
    def _get_passage_group_id(q: dict) -> uuid.UUID | None:
        pt = (q.get("passage_text") or "").strip()
        return _passage_to_group.get(pt)

    # Form-submitted metadata takes precedence; fall back to LLM-extracted values
    exam_code = form_meta.get("source_exam_code") or shared_source.get("source_exam_code")
    subject_code = form_meta.get("source_subject_code") or shared_source.get("source_subject_code")
    section_code = form_meta.get("source_section_code") or shared_source.get("source_section_code")
    module_code = form_meta.get("source_module_code") or shared_source.get("source_module_code")

    # Validate LLM-inferred question numbers for official batches
    all_errors: list[dict] = []
    suspect_qnum_indices: set[int] = set()
    # Surface normalization drops (empty stems, duplicates) in validation_errors_jsonb
    # so they're visible in the job record, not just server logs.
    if norm_errors:
        all_errors.extend(norm_errors)
    if job.content_origin == "official":
        qnum_warnings = _validate_question_numbers(questions_data, subject_code, module_code)
        if qnum_warnings:
            logger.warning(
                "Question number validation issues for job %s: %s",
                job.id, qnum_warnings,
            )
            all_errors.extend(qnum_warnings)

        # Cross-check LLM numbers against OCR text (when OCR text is available)
        ocr_raw = (job.pass1_json or {}).get("raw_text", "")
        if ocr_raw:
            crosscheck_warnings = _verify_qnums_against_ocr(questions_data, ocr_raw)
            if crosscheck_warnings:
                logger.warning(
                    "Question number OCR cross-check mismatches for job %s: %s",
                    job.id, crosscheck_warnings,
                )
                all_errors.extend(crosscheck_warnings)
                suspect_qnum_indices = {w["question_index"] for w in crosscheck_warnings if "question_index" in w}

    # ---- Layout detection (enrichment, never a gate) ----
    layout_data: dict[int, list] = {}
    layout_paths: dict[int, str] = {}
    page_images_data = (job.pass1_json or {}).get("_page_images", [])
    layout_can_run = bool(
        getattr(settings, "glm_ocr_model", None)
        or getattr(settings, "anthropic_api_key", None)
    )
    if settings.layout_detection_enabled and page_images_data and layout_can_run:
        try:
            layout_data = await detect_layout(page_images_data, settings)
            for page_index, regions in layout_data.items():
                stored = put_object(
                    "ocr_layout",
                    {"job_id": job.id, "page_number": _page_number_for_region(job, page_index), "method": "vision_layout"},
                    json.dumps(
                        {
                            "page_index": page_index,
                            "page_number": _page_number_for_region(job, page_index),
                            "regions": [asdict(r) for r in regions],
                        },
                        indent=2,
                    ),
                    filename="vision_layout.json",
                    mime_type="application/json",
                )
                layout_paths[page_index] = stored.storage_path
        except Exception as e:
            logger.warning("Layout detection failed for job %s: %s", job.id, e)
            layout_data, layout_paths = {}, {}

    # ---- Per-job OCR diagnostics file ----
    ocr_meta_for_diag = (job.pass1_json or {}).get("_ocr_meta")
    if ocr_meta_for_diag:
        try:
            diag = put_object(
                "ocr_diagnostics",
                {"job_id": job.id, "page_number": 0},
                json.dumps(ocr_meta_for_diag, indent=2),
                filename="diagnostics.json",
                mime_type="application/json",
            )
            job.pass1_json = {
                **(job.pass1_json or {}),
                "_ocr_meta": {**ocr_meta_for_diag, "diagnostics_path": diag.storage_path},
            }
        except Exception as e:
            logger.warning("Diagnostics write failed for job %s: %s", job.id, e)

    # Any pre-persist warning (question-number / OCR cross-check) routes the
    # whole job into the manual review queue and holds its questions as drafts.
    defer_activation = bool(all_errors)

    # ---- Per-question loop ----
    created_question_ids: list[uuid.UUID] = []
    pass2_meta_list: list[dict] = []
    pass2_annotation_records: list[dict] = []
    amendment_proposal_records: list[dict] = []

    # ---- Phase 1: Concurrent annotation ----
    # Sort questions by domain so identical system prompts run consecutively,
    # enabling Ollama KV-prefix caching across same-domain questions.
    _domain_order = {"grammar": 0, "reading": 1, "writing": 2}
    _annot_order = sorted(
        range(len(questions_data)),
        key=lambda idx: _domain_order.get(_detect_domain(questions_data[idx]), 99),
    )

    # Apply form metadata before annotation starts
    for i, q_data in enumerate(questions_data):
        if exam_code:
            q_data["source_exam_code"] = exam_code
        q_data.setdefault("source_subject_code", subject_code)
        q_data.setdefault("source_section_code", section_code)
        q_data.setdefault("source_module_code", module_code)

    _annot_semaphore = asyncio.Semaphore(settings.ollama_max_concurrent)

    async def _annotate_one(idx: int) -> tuple[int, dict | None, Exception | None, dict | None]:
        """Annotate a single question with retry. Returns (idx, annotate_json, last_err, meta)."""
        from app.prompts.annotate_prompt import build_annotate_prompt_parts
        q_data = questions_data[idx]
        prompt_q_data = {**q_data, "content_origin": job.content_origin}
        sys_static, sys_dynamic, user = build_annotate_prompt_parts(prompt_q_data)
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                async with _annot_semaphore:
                    result = await provider.complete_cached(
                        system_static=sys_static, system_dynamic=sys_dynamic,
                        user=user, max_tokens=8192,
                    )
                parsed = extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
                if not parsed:
                    raise ValueError("LLM returned empty or un-parseable annotation JSON")
                annotate_json = normalize_annotation(parsed)
                annotate_json = enforce_nullability(annotate_json, _detect_domain(q_data))
                meta = {
                    "question_index": idx,
                    "provider": result.provider,
                    "model": result.model,
                    "latency_ms": result.latency_ms,
                    "token_usage": getattr(result, "token_usage", None) or {},
                }
                return idx, annotate_json, None, meta
            except ValueError as json_err:
                last_err = json_err
                logger.warning(
                    "Annotation JSON parse failed (attempt %d/3) for question_index %d: %s",
                    attempt + 1, idx, json_err,
                )
                if attempt < 2:
                    await asyncio.sleep(0.3 * (2 ** attempt))
            except Exception as exc:
                last_err = exc
                break
        return idx, None, last_err, None

    # Fire all annotation calls concurrently, bounded by semaphore
    job.status = "annotating"
    await db.commit()

    annot_results = await asyncio.gather(
        *[_annotate_one(idx) for idx in _annot_order],
        return_exceptions=False,
    )
    # Build index: question_index -> (annotate_json, last_err, meta)
    _annot_by_idx: dict[int, tuple[dict | None, Exception | None, dict | None]] = {}
    for idx, ajson, err, meta in annot_results:
        _annot_by_idx[idx] = (ajson, err, meta)
        if meta:
            pass2_meta_list.append(meta)

    # ---- Phase 2: Serial validate + persist (original question order) ----
    for i, q_data in enumerate(questions_data):
        annotate_json, _last_err, _meta = _annot_by_idx.get(i, (None, None, None))

        if annotate_json is None:
            all_errors.append({
                "question_index": i,
                "step": "annotating",
                "error": str(_last_err) if _last_err else "annotation returned None",
                "source_question_number": q_data.get("source_question_number"),
            })
            continue

        try:
            from app.pipeline.amendments import capture_amendment_proposal, extract_amendment_proposal
            pass2_annotation_records.append({
                "question_index": i,
                "source_question_number": q_data.get("source_question_number"),
                "annotation": annotate_json,
            })
            amendment_proposal = extract_amendment_proposal(annotate_json)
            if amendment_proposal:
                amendment_proposal_records.append({
                    "source_question_number": q_data.get("source_question_number"),
                    "q_data": {
                        "source_exam_code": q_data.get("source_exam_code"),
                        "source_subject_code": q_data.get("source_subject_code"),
                        "source_section_code": q_data.get("source_section_code"),
                        "source_module_code": q_data.get("source_module_code"),
                        "source_question_number": q_data.get("source_question_number"),
                        "question_text": q_data.get("question_text"),
                        "skill_family_key": q_data.get("skill_family_key"),
                        "grammar_role_key": q_data.get("grammar_role_key"),
                    },
                    "amendment_proposal": amendment_proposal,
                })
            capture_amendment_proposal(job=job, q_data=q_data, annotate_json=annotate_json)
        except Exception as exc:
            logger.warning(
                "amendment proposal capture failed for job %s q%s: %s",
                job.id,
                q_data.get("source_question_number") or i + 1,
                exc,
            )

        # ---- Overlap check (unofficial/generated only) ----
        overlaps: list = []
        if job.content_origin in ("unofficial", "generated"):
            job.status = "overlap_checking"
            await db.commit()

            from app.pipeline.overlap import detect_overlaps

            question_text = q_data.get("question_text", "")
            passage_text = shared_passage or q_data.get("passage_text")

            overlaps = await detect_overlaps(
                question_id=None,
                annotation_jsonb=annotate_json,
                passage_text=passage_text,
                question_text=question_text,
                db=db,
            )

        # ---- Validate ----
        job.status = "validating"
        merged = _merge_for_validation(q_data, annotate_json)
        errors = validate_question(merged, content_origin=job.content_origin)

        if any(e["severity"] == "blocking" for e in errors):
            all_errors.append({"question_index": i, "step": "validating", "errors": errors, "source_question_number": q_data.get("source_question_number")})
            continue

        # ---- Persist ----
        try:
            async with db.begin_nested():  # SAVEPOINT: failure rolls back only this question
                question_id = await _persist_single_question(
                    db=db,
                    job=job,
                    q_data=q_data,
                    annotate_json=annotate_json,
                    passage_text=q_data.get("passage_text") or shared_passage,
                    passage_group_id=_get_passage_group_id(q_data),
                    overlaps=overlaps,
                    section_code=section_code,
                    question_index=i,
                    layout_data=layout_data,
                    layout_paths=layout_paths,
                    provider=stimulus_provider,
                    suspect_question_indices=suspect_qnum_indices,
                    defer_activation=defer_activation,
                )
                db.add(QuestionJobQuestion(job_id=job.id, question_id=question_id))
            created_question_ids.append(question_id)
            _export_question(job, q_data, annotate_json, question_id)
        except Exception as _persist_err:
            logger.error(
                "Persist failed for question_index %d (job %s): %s",
                i, job.id, _persist_err,
            )
            # Session is restored to savepoint — no rollback needed, loop continues cleanly
            all_errors.append({
                "question_index": i,
                "step": "persisting",
                "error": str(_persist_err),
                "source_question_number": q_data.get("source_question_number"),
            })
            continue

    # ---- Final job status ----
    pass2_payload: dict = {}
    if len(pass2_annotation_records) == 1:
        pass2_payload.update(pass2_annotation_records[0]["annotation"])
    elif pass2_annotation_records:
        pass2_payload["_annotations"] = pass2_annotation_records
    if pass2_meta_list:
        pass2_payload["_pass2_meta"] = pass2_meta_list
    if amendment_proposal_records:
        pass2_payload["_amendment_proposals"] = amendment_proposal_records
    if pass2_payload:
        job.pass2_json = pass2_payload

    existing_job_warnings = [
        item for item in (job.validation_errors_jsonb or [])
        if isinstance(item, dict) and item.get("severity") == "warning"
    ]
    combined_validation_records = [*existing_job_warnings, *all_errors]
    job.validation_errors_jsonb = combined_validation_records if combined_validation_records else None

    if created_question_ids:
        # At least one question succeeded
        job.question_id = created_question_ids[0]  # primary question for the job
        needs_review = (
            (job.content_origin == "official" and not _should_auto_activate_official(settings))
            or bool(all_errors)
        )
        job.status = "needs_review" if needs_review else "approved"
        job.pass1_json = {
            **(job.pass1_json or {}),
            "_created_question_ids": [str(qid) for qid in created_question_ids],
        }
        if job.content_origin == "official":
            try:
                from app.pipeline.ingestion_analysis import write_ingestion_analysis
                write_ingestion_analysis(job)
            except Exception as exc:
                logger.warning("failed to write ingestion analysis for job %s: %s", job.id, exc)
    else:
        # All questions failed
        job.status = "failed"

    await db.commit()


async def _run_pipeline_with_session(job_id: uuid.UUID):
    timeout_s = getattr(get_settings(), "pipeline_timeout_s", 1800)
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if not job:
            return
        try:
            await asyncio.wait_for(_run_pipeline(job, db), timeout=timeout_s)
        except asyncio.TimeoutError:
            logger.error("Pipeline exceeded %ss timeout (job %s)", timeout_s, job_id)
            # The timed-out task's session may be mid-operation and unusable;
            # mark the job failed on a fresh session.
            async with async_session() as db2:
                j2 = await db2.get(QuestionJob, job_id)
                if j2 and j2.status not in ("approved", "needs_review", "failed"):
                    j2.status = "failed"
                    j2.validation_errors_jsonb = [{
                        "step": "pipeline_timeout",
                        "error": f"Pipeline exceeded {timeout_s}s timeout",
                        "error_type": "TimeoutError",
                    }]
                    await db2.commit()


async def _safe_read(file: UploadFile, max_bytes: int) -> bytes:
    """Check Content-Length before reading to avoid loading oversized files into RAM."""
    cl = file.headers.get("content-length")
    if cl and int(cl) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    return content


def _normalize_mime(mime: str | None) -> str:
    return (mime or "").split(";", 1)[0].strip().lower()


def _validate_upload_mime(mime: str | None, allowed: set[str] = ALLOWED_MIME) -> str:
    normalized = _normalize_mime(mime)
    if normalized not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type. Allowed: {allowed_list}",
        )
    return normalized


def _parse_pdf_content(content: bytes) -> dict:
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            tmp_path = Path(tmp.name)
        return parse_pdf(str(tmp_path))
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


def _asset_type_from_mime(mime: str) -> str:
    if "pdf" in mime:
        return "pdf"
    elif "image" in mime:
        return "image"
    elif "markdown" in mime:
        return "markdown"
    elif "json" in mime:
        return "json"
    return "text"


@router.post("/official/pdf", response_model=JobResponse)
async def ingest_official_pdf(
    file: UploadFile = File(...),
    source_exam_code: str = Form(""),
    source_subject_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    ocr_strategy: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if ocr_strategy and ocr_strategy not in {"glm", "deepseek", "ollama", "vision", "anthropic", "openai", "auto"}:
        raise HTTPException(status_code=422, detail="ocr_strategy must be 'glm', 'deepseek', 'ollama', 'vision', 'anthropic', 'openai', or 'auto'")

    # Official questions require complete metadata for deterministic UUID generation.
    missing = [f for f, v in [
        ("source_exam_code", source_exam_code),
        ("source_subject_code", source_subject_code),
        ("source_section_code", source_section_code),
        ("source_module_code", source_module_code),
    ] if not (v or "").strip()]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Official PDF ingestion requires: {', '.join(missing)}. "
                   "These fields are used to generate stable question IDs and prevent duplicates.",
        )

    mime_type = _validate_upload_mime(file.content_type, {"application/pdf"})
    content = await _safe_read(file, MAX_FILE_SIZE)
    if not content[:4] == b"%PDF":
        raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF (bad magic bytes)")
    source_subject_code, source_section_code, source_module_code = _normalize_source_metadata(
        source_subject_code,
        source_section_code,
        source_module_code,
    )

    checksum = compute_checksum(content)
    existing = await db.execute(select(QuestionAsset).where(QuestionAsset.checksum == checksum))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="This file has already been ingested (duplicate checksum).")

    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()
    source_metadata = {
        "source_exam_code": source_exam_code,
        "source_subject_code": source_subject_code,
        "source_section_code": source_section_code,
        "source_module_code": source_module_code,
    }
    storage_path = _store_raw_upload(
        asset_id=asset_id,
        job_id=job_id,
        content_origin="official",
        source_metadata=source_metadata,
        filename=file.filename or "upload.pdf",
        content=content,
        mime_type=mime_type,
    )

    pdf_result = _parse_pdf_content(content)
    raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])

    # Store full-page renders for OCR/layout enrichment, even for text-layer PDFs.
    page_images = _store_pdf_page_renders(
        pdf_result=pdf_result,
        asset_id=asset_id,
        job_id=job_id,
        content_origin="official",
        source_metadata=source_metadata,
        source_stem=Path(file.filename or "upload").stem,
        max_images=len(pdf_result["pages"]),
    )

    asset = QuestionAsset(
        id=asset_id,
        content_origin="official",
        asset_type="pdf",
        storage_path=storage_path,
        mime_type=mime_type,
        page_start=0,
        page_end=len(pdf_result["pages"]) - 1,
        source_name=_sanitize_source_name(file.filename),
        source_exam_code=source_exam_code or None,
        source_subject_code=source_subject_code,
        source_section_code=source_section_code or None,
        source_module_code=source_module_code or None,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    settings = get_settings()
    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="official",
        input_format="pdf",
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v8.0",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={
            "raw_text": raw_text[:100000],
            "_truncated": len(raw_text) > 100000,
            "pages": len(pdf_result["pages"]),
            "_page_images": page_images,
            "_page_texts": [{"page_number": p["page_number"], "text": p.get("text", "")} for p in pdf_result["pages"]],
            "_ocr_strategy": ocr_strategy,
            "source_metadata": {
                **source_metadata,
                "page_count": len(pdf_result["pages"]),
            },
        },
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(
        run_with_job_limit(lambda: _run_pipeline_with_session(job_id))
    ).add_done_callback(_log_task_exception)

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


@router.post("/unofficial/file", response_model=JobResponse)
async def ingest_unofficial_file(
    file: UploadFile = File(...),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    ocr_strategy: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if ocr_strategy and ocr_strategy not in {"glm", "deepseek", "ollama", "vision", "anthropic", "openai", "auto"}:
        raise HTTPException(status_code=422, detail="ocr_strategy must be 'glm', 'deepseek', 'ollama', 'vision', 'anthropic', 'openai', or 'auto'")
    mime_type = _validate_upload_mime(file.content_type)
    content = await _safe_read(file, MAX_FILE_SIZE)

    checksum = compute_checksum(content)
    existing = await db.execute(select(QuestionAsset).where(QuestionAsset.checksum == checksum))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="This file has already been ingested (duplicate checksum).")

    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()
    source_metadata: dict = {}
    storage_path = _store_raw_upload(
        asset_id=asset_id,
        job_id=job_id,
        content_origin="unofficial",
        source_metadata=source_metadata,
        filename=file.filename or "upload",
        content=content,
        mime_type=mime_type,
    )

    asset_type = _asset_type_from_mime(mime_type)

    if asset_type == "pdf" and not content[:4] == b"%PDF":
        raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF (bad magic bytes)")

    asset = QuestionAsset(
        id=asset_id,
        content_origin="unofficial",
        asset_type=asset_type,
        storage_path=storage_path,
        mime_type=mime_type,
        source_name=_sanitize_source_name(file.filename),
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    raw_text = ""
    page_images: list = []
    if asset_type == "pdf":
        pdf_result = _parse_pdf_content(content)
        raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
        page_images = _store_pdf_page_renders(
            pdf_result=pdf_result,
            asset_id=asset_id,
            job_id=job_id,
            content_origin="unofficial",
            source_metadata=source_metadata,
            source_stem=Path(file.filename or "upload").stem,
            max_images=len(pdf_result["pages"]),
        )
    elif asset_type in ("text", "markdown"):
        raw_text = content.decode("utf-8", errors="replace")
    elif asset_type == "json":
        import json
        try:
            data = json.loads(content)
            raw_text = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            raw_text = content.decode("utf-8", errors="replace")
    elif asset_type == "image":
        from app.parsers.image_parser import parse_image
        import pathlib
        suffix = pathlib.Path(file.filename or "img").suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            img_data = parse_image(tmp_path)
        finally:
            pathlib.Path(tmp_path).unlink(missing_ok=True)
        source_stem = Path(file.filename or "upload").stem
        ext = suffix.lstrip(".")
        page_images = [
            _store_page_render(
                asset_id=asset_id,
                job_id=job_id,
                content_origin="unofficial",
                source_metadata=source_metadata,
                source_stem=source_stem,
                page_number=0,
                b64=img_data["b64"],
                ext=ext,
            )
        ]

    settings = get_settings()
    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="unofficial",
        input_format=asset_type,
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v8.0",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:100000], "_truncated": len(raw_text) > 100000, "_page_images": page_images, "_page_texts": [{"page_number": p["page_number"], "text": p.get("text", "")} for p in pdf_result["pages"]] if pdf_result else [], "_ocr_strategy": ocr_strategy},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(
        run_with_job_limit(lambda: _run_pipeline_with_session(job_id))
    ).add_done_callback(_log_task_exception)

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


@router.post("/text", response_model=JobResponse)
async def ingest_text(
    text: str = Form(...),
    content_origin: str = Form("unofficial"),
    source_exam_code: str = Form(""),
    source_subject_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if content_origin not in ("official", "unofficial"):
        raise HTTPException(status_code=422, detail="content_origin must be 'official' or 'unofficial'")
    if len(text) > 50000:
        raise HTTPException(status_code=413, detail=f"Text too long ({len(text):,} chars). Maximum is 50,000. Split into smaller segments.")
    source_subject_code, source_section_code, source_module_code = _normalize_source_metadata(
        source_subject_code,
        source_section_code,
        source_module_code,
    )

    settings = get_settings()
    now = datetime.now(timezone.utc)
    job_id = uuid.uuid4()

    source_metadata = {
        k: v for k, v in {
            "source_exam_code": source_exam_code or None,
            "source_subject_code": source_subject_code,
            "source_section_code": source_section_code or None,
            "source_module_code": source_module_code or None,
        }.items() if v
    }

    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin=content_origin,
        input_format="text",
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v8.0",
        rules_version=settings.rules_version,
        pass1_json={"raw_text": text, "source_metadata": source_metadata},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(
        run_with_job_limit(lambda: _run_pipeline_with_session(job_id))
    ).add_done_callback(_log_task_exception)

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


async def _run_reannotate_pipeline(job: QuestionJob, db: AsyncSession):
    """Reannotation pipeline — skips extraction and goes straight to annotation."""
    from app.llm.factory import get_provider
    from app.prompts.annotate_prompt import build_annotate_prompt_parts
    from app.parsers.json_parser import extract_json_from_text, normalize_annotation

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=_provider_api_key(settings, job.provider_name),
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )
    extract_json = {}
    if job.pass1_json:
        extract_json = {k: v for k, v in job.pass1_json.items() if not k.startswith("_")}

    # Skip extraction, go straight to annotation
    job.status = "annotating"
    await db.commit()

    from app.prompts.annotate_prompt import enforce_nullability, _detect_domain
    sys_static, sys_dynamic, user = build_annotate_prompt_parts(
        {**extract_json, "content_origin": job.content_origin}
    )
    try:
        result = await provider.complete_cached(
            system_static=sys_static, system_dynamic=sys_dynamic, user=user, max_tokens=8192,
        )
        annotate_json = normalize_annotation(
            extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
        )
        # Hard-enforce domain nullability rules after LLM output
        domain = _detect_domain(extract_json)
        annotate_json = enforce_nullability(annotate_json, domain)
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms, "token_usage": getattr(result, "token_usage", None) or {}}}
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [error_payload("annotating", e)]
        await db.commit()
        return

    # Validate
    merged = _merge_for_validation(extract_json, annotate_json)
    errors = validate_question(merged, content_origin=job.content_origin)
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
        await db.commit()
        return

    job.status = "approved"

    # Create new annotation and version, update question
    now = datetime.now(timezone.utc)
    question = await db.get(Question, job.question_id)
    if not question:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": "Question not found"}]
        await db.commit()
        return

    latest_version_result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == question.id)
        .order_by(QuestionVersion.version_number.desc())
        .limit(1)
    )
    latest_version = latest_version_result.scalars().first()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()

    # Load current-version option rows before advancing latest_version_id
    old_opts_stmt = select(QuestionOption).where(QuestionOption.question_id == question.id)
    if question.latest_version_id:
        old_opts_stmt = old_opts_stmt.where(QuestionOption.question_version_id == question.latest_version_id)
    old_opts_result = await db.execute(old_opts_stmt.order_by(QuestionOption.option_label))
    old_options = old_opts_result.scalars().all()

    db.add(QuestionVersion(
        id=version_id,
        question_id=question.id,
        version_number=(latest_version.version_number + 1) if latest_version else 1,
        change_source="reprocess",
        question_text=extract_json.get("question_text", question.current_question_text),
        passage_text=extract_json.get("passage_text", question.current_passage_text),
        choices_jsonb=extract_json.get("options", []),
        correct_option_label=extract_json.get("correct_option_label", question.current_correct_option_label),
        explanation_text=annotate_json.get("explanation_short", question.current_explanation_text),
        created_at=now,
    ))
    await db.flush()  # persist version before annotation FK references it

    annotate_json = sanitize_annotation_keys(annotate_json, job_id=str(job.id))
    db.add(QuestionAnnotation(
        id=annotation_id,
        question_id=question.id,
        question_version_id=version_id,
        provider_name=job.provider_name,
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        rules_version=job.rules_version,
        annotation_jsonb=annotate_json,
        explanation_jsonb={"explanation_full": annotate_json.get("explanation_full", "")},
        generation_profile_jsonb=_generation_profile_payload(extract_json, annotate_json),
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))
    await db.flush()  # ensure annotation ID is visible before setting circular FKs

    question.current_explanation_text = annotate_json.get(
        "explanation_short", question.current_explanation_text
    )
    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id
    question.annotation_stale = False
    question.updated_at = now

    # Clone option rows for the new version, applying fresh annotation fields
    correct_label = extract_json.get("correct_option_label", question.current_correct_option_label)
    opt_analyses = option_analyses_by_label(annotate_json)
    for opt in old_options:
        db.add(QuestionOption(
            id=uuid.uuid4(),
            question_id=question.id,
            question_version_id=version_id,
            option_label=opt.option_label,
            option_text=opt.option_text,
            is_correct=opt.option_label == correct_label,
            option_role="correct" if opt.option_label == correct_label else "distractor",
            created_at=now,
            **option_annotation_fields(opt_analyses.get(opt.option_label, {})),
        ))

    await db.commit()


async def _run_reannotate_pipeline_with_session(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_reannotate_pipeline(job, db)


@router.post("/unofficial/batch", response_model=list[JobResponse])
async def ingest_unofficial_batch(
    files: list[UploadFile] = File(...),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    ocr_strategy: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if ocr_strategy and ocr_strategy not in {"glm", "deepseek", "ollama", "vision", "anthropic", "openai", "auto"}:
        raise HTTPException(status_code=422, detail="ocr_strategy must be 'glm', 'deepseek', 'ollama', 'vision', 'anthropic', 'openai', or 'auto'")
    results = []
    for file in files:
        resp = await ingest_unofficial_file(
            file=file, provider_name=provider_name, model_name=model_name, ocr_strategy=ocr_strategy, db=db, _auth=_auth
        )
        results.append(resp)
    return results


@router.post("/reannotate/{question_id}", response_model=JobResponse)
async def reannotate_question(
    question_id: str,
    body: ReannotateRequest = Body(default_factory=ReannotateRequest),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        qid = uuid.UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    result = await db.execute(
        select(QuestionJob)
        .where(QuestionJob.question_id == qid)
        .order_by(QuestionJob.created_at.desc())
        .limit(1)
    )
    existing_job = result.scalars().first()

    # Always synthesize pass1_json from current DB state so the single-question
    # format (question_text, options, etc. at top level) is guaranteed.
    # The old job's pass1_json may be a full-batch extraction (questions list),
    # which the reannotate pipeline cannot validate as a single question.
    ver_result = await db.execute(
        select(QuestionVersion).where(QuestionVersion.id == q.latest_version_id)
    )
    ver = ver_result.scalars().first()
    choices = ver.choices_jsonb if ver else []
    synthesized_pass1 = {
        "question_text": q.current_question_text,
        "passage_text": q.current_passage_text,
        "paired_passage_text": q.current_paired_passage_text,
        "underlined_text": q.current_underlined_text,
        "options": choices,
        "correct_option_label": q.current_correct_option_label,
        "stem_type_key": q.stem_type_key,
        "stimulus_mode_key": q.stimulus_mode_key,
        "source_exam_code": q.source_exam_code,
        "source_section_code": q.source_section_code,
        "source_module_code": q.source_module_code,
        "source_question_number": q.source_question_number,
    }

    settings = get_settings()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    job = QuestionJob(
        id=job_id,
        job_type="reannotate",
        content_origin=q.content_origin,
        input_format="reannotate",
        status="annotating",
        provider_name=body.provider_name,
        model_name=body.model_name,
        prompt_version="v8.0",
        rules_version=settings.rules_version,
        pass1_json=synthesized_pass1,
        question_id=qid,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(
        run_with_job_limit(lambda: _run_reannotate_pipeline_with_session(job_id))
    ).add_done_callback(_log_task_exception)

    return JobResponse(id=str(job_id), job_type="reannotate", status="annotating", question_id=question_id, created_at=now)


@router.post("/benchmark/ocr")
async def ingest_benchmark_ocr(
    file: UploadFile = File(...),
    strategies: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Submit a file to run all available OCR strategies in parallel.

    strategies: comma-separated list of strategies to run (deepseek, ollama, anthropic, openai).
    Defaults to all strategies that are configured and available.
    Returns comparison_group_id for polling via GET /benchmark/ocr/{comparison_group_id}.
    """
    mime_type = _validate_upload_mime(file.content_type)
    content = await _safe_read(file, MAX_FILE_SIZE)
    settings = get_settings()
    now = datetime.now(timezone.utc)
    checksum = compute_checksum(content)
    comparison_group_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    source_metadata: dict = {}

    requested = [s.strip().lower() for s in (strategies or "").split(",") if s.strip()]
    available = _available_ocr_strategies(settings)
    to_run = [s for s in requested if s in available] if requested else available
    if not to_run:
        raise HTTPException(
            status_code=422,
            detail="No OCR strategies available. Configure deepseek_ocr_base_url, ollama, or API keys.",
        )

    asset_type = _asset_type_from_mime(mime_type)
    raw_text = ""
    page_images: list = []
    if asset_type == "pdf":
        pdf_result = _parse_pdf_content(content)
        raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
        page_images = _store_pdf_page_renders(
            pdf_result=pdf_result,
            asset_id=asset_id,
            job_id=comparison_group_id,
            content_origin="unofficial",
            source_metadata=source_metadata,
            source_stem=Path(file.filename or "upload").stem,
            max_images=len(pdf_result["pages"]),
        )
    elif asset_type in ("text", "markdown"):
        raw_text = content.decode("utf-8", errors="replace")
    elif asset_type == "image":
        from app.parsers.image_parser import parse_image
        import pathlib
        suffix = pathlib.Path(file.filename or "img").suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            img_data = parse_image(tmp_path)
        finally:
            pathlib.Path(tmp_path).unlink(missing_ok=True)
        source_stem = Path(file.filename or "upload").stem
        ext = suffix.lstrip(".")
        page_images = [
            _store_page_render(
                asset_id=asset_id,
                job_id=comparison_group_id,
                content_origin="unofficial",
                source_metadata=source_metadata,
                source_stem=source_stem,
                page_number=0,
                b64=img_data["b64"],
                ext=ext,
            )
        ]

    # DeepSeek is an image-only OCR provider — skip it for text-based content.
    has_images = bool(page_images)
    if not has_images:
        to_run = [s for s in to_run if s != "deepseek"]
    if not to_run:
        raise HTTPException(
            status_code=422,
            detail="No OCR strategies available for this content type. Upload a scanned PDF or image to test DeepSeek.",
        )

    storage_path = _store_raw_upload(
        asset_id=asset_id,
        job_id=comparison_group_id,
        content_origin="unofficial",
        source_metadata={},
        filename=file.filename or "upload",
        content=content,
        mime_type=mime_type,
    )
    db.add(QuestionAsset(
        id=asset_id,
        content_origin="unofficial",
        asset_type=asset_type,
        storage_path=storage_path,
        mime_type=mime_type,
        source_name=_sanitize_source_name(file.filename),
        checksum=checksum,
        created_at=now,
    ))

    job_infos = []
    for strategy in to_run:
        prov = strategy if strategy in ("anthropic", "openai", "ollama") else settings.default_annotation_provider
        _, model = _resolve_provider_and_model(settings, prov, None)
        job_id = uuid.uuid4()
        db.add(QuestionJob(
            id=job_id,
            job_type="ingest",
            content_origin="unofficial",
            input_format=asset_type,
            status="parsing",
            provider_name=prov,
            model_name=model,
            prompt_version="v8.0",
            rules_version=settings.rules_version,
            raw_asset_id=asset_id,
            comparison_group_id=comparison_group_id,
            pass1_json={
                "raw_text": raw_text[:100000],
                "_truncated": len(raw_text) > 100000,
                "_page_images": page_images,
                "_ocr_strategy": strategy,
            },
            created_at=now,
            updated_at=now,
        ))
        job_infos.append({"id": str(job_id), "strategy": strategy})

    await db.commit()

    for info in job_infos:
        asyncio.create_task(
            run_with_job_limit(lambda job_id=uuid.UUID(info["id"]): _run_pipeline_with_session(job_id))
        ).add_done_callback(_log_task_exception)

    return {"comparison_group_id": str(comparison_group_id), "jobs": job_infos, "has_images": has_images}


@router.get("/benchmark/ocr/{comparison_group_id}", response_model=OCRBenchmarkResponse)
async def get_benchmark_ocr(
    comparison_group_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Poll results for a benchmark group created via POST /benchmark/ocr."""
    try:
        group_uuid = uuid.UUID(comparison_group_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid comparison_group_id")

    result = await db.execute(
        select(QuestionJob).where(QuestionJob.comparison_group_id == group_uuid)
    )
    jobs = result.scalars().all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found for this comparison group")

    terminal_statuses = {"approved", "failed", "needs_review"}
    ready = all(j.status in terminal_statuses for j in jobs)

    results = []
    has_images = False
    for j in jobs:
        p1 = j.pass1_json or {}
        p2 = j.pass2_json or {}
        ocr_meta = p1.get("_ocr_meta")
        if p1.get("_page_images") or ocr_meta:
            has_images = True
        strategy = (ocr_meta or {}).get("strategy") or p1.get("_ocr_strategy") or "unknown"
        results.append(OCRJobResult(
            job_id=str(j.id),
            strategy=strategy,
            status=j.status,
            ocr_meta=ocr_meta,
            llm_meta=p1.get("_llm_meta"),
            pass2_meta=p2.get("_pass2_meta"),
            questions_extracted=p1.get("_extracted_count", 0),
            questions_created=len(p1.get("_created_question_ids") or []),
            validation_errors=j.validation_errors_jsonb,
        ))

    return OCRBenchmarkResponse(
        comparison_group_id=comparison_group_id,
        results=results,
        ready=ready,
        has_images=has_images,
    )


@router.post("/gc/images")
async def gc_page_images(
    max_age_days: int = 30,
    _auth: str = Depends(admin_required),
):
    """Delete page image files older than max_age_days (default 30) from archive/images/.

    Returns the number of files deleted.
    """
    settings = get_settings()
    deleted = _gc_page_images(settings.local_archive_mirror, max_age_days=max_age_days)
    return {"deleted": deleted, "max_age_days": max_age_days}


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Poll the status of an ingest/reannotate job."""
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    job = await db.get(QuestionJob, jid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pass1 = job.pass1_json or {}
    return JobResponse(
        id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        question_id=str(job.question_id) if job.question_id else None,
        created_at=job.created_at,
        validation_errors=job.validation_errors_jsonb or None,
        ocr_meta=pass1.get("_ocr_meta"),
        llm_meta=pass1.get("_llm_meta"),
    )
