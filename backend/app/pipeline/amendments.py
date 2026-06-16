"""Capture and persist official-source rule amendment proposals."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

try:  # POSIX file locking - present on the Linux deploy target.
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import QuestionJob
from app.models.vocab_fields import BASE_FIELD_TO_VOCAB
from app.models.amendments import (
    MasterJsonPatch,
    RuleAmendment,
    RuleDocPatch,
    SupportingExample,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
PENDING_DIR = REPO_ROOT / "vocabulary" / "amendments" / "pending"
CANDIDATES_PATH = REPO_ROOT / "vocabulary" / "candidates.json"
COMPLETED_INGEST_STATUSES = ("approved", "needs_review")

FIELD_TO_VOCAB = BASE_FIELD_TO_VOCAB

_PARENTHETICAL_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")
_AFFECTED_VOCAB_ALIASES = {
    "skill_family": "READING_SKILL_FAMILY_KEYS",
}


def extract_amendment_proposal(annotate_json: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return ``reasoning.amendment_proposal`` or legacy top-level proposal."""
    if not isinstance(annotate_json, dict):
        return None
    reasoning = annotate_json.get("reasoning")
    if isinstance(reasoning, dict) and isinstance(reasoning.get("amendment_proposal"), dict):
        return reasoning["amendment_proposal"]
    proposal = annotate_json.get("amendment_proposal")
    if isinstance(proposal, dict):
        return proposal
    return None


def capture_amendment_proposal(
    *,
    job: Any,
    q_data: dict[str, Any],
    annotate_json: dict[str, Any],
    pending_dir: Path = PENDING_DIR,
    candidates_path: Path = CANDIDATES_PATH,
) -> RuleAmendment | None:
    """Persist one pending amendment file from an official job annotation."""
    proposal = extract_amendment_proposal(annotate_json)
    if not proposal:
        return None

    content_origin = getattr(job, "content_origin", None)
    if content_origin != "official":
        _record_job_warning(
            job,
            code="non_official_amendment_proposal_dropped",
            message=f"Amendment proposal ignored because content_origin is {content_origin!r}.",
        )
        logger.warning(
            "dropping amendment proposal from non-official job %s (origin=%s)",
            getattr(job, "id", None),
            content_origin,
        )
        return None

    try:
        amendment = _proposal_to_amendment(job, q_data, proposal)
    except (TypeError, ValueError, ValidationError) as exc:
        _record_job_warning(
            job,
            code="invalid_amendment_proposal_dropped",
            message=str(exc),
        )
        logger.warning(
            "dropping invalid amendment proposal from job %s q%s: %s",
            getattr(job, "id", None),
            q_data.get("source_question_number"),
            exc,
        )
        return None

    pending_dir.mkdir(parents=True, exist_ok=True)
    path = pending_dir / f"{amendment.amendment_id}.json"
    if path.exists():
        amendment = _merge_supporting_example(path, amendment)
    path.write_text(json.dumps(amendment.to_file_dict(), indent=2, ensure_ascii=False) + "\n")
    _link_candidate(candidates_path, amendment)
    return amendment


async def capture_amendments_from_completed_official_jobs(
    db: AsyncSession,
    *,
    pending_dir: Path = PENDING_DIR,
    candidates_path: Path = CANDIDATES_PATH,
    statuses: tuple[str, ...] = COMPLETED_INGEST_STATUSES,
) -> list[RuleAmendment]:
    """Backfill pending amendment files from completed official ingest jobs.

    This supports review/replay after an ingestion has already completed. It
    reads amendment proposals from either a single-question Pass 2 payload or
    the multi-question ``_amendment_proposals`` metadata written by the normal
    ingest pipeline.
    """
    stmt = select(QuestionJob).where(
        QuestionJob.job_type == "ingest",
        QuestionJob.content_origin == "official",
        QuestionJob.status.in_(statuses),
        QuestionJob.pass2_json.isnot(None),
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    captured: list[RuleAmendment] = []
    for job in jobs:
        captured.extend(
            capture_amendments_from_job(
                job,
                pending_dir=pending_dir,
                candidates_path=candidates_path,
            )
        )
    return captured


def capture_amendments_from_job(
    job: Any,
    *,
    pending_dir: Path = PENDING_DIR,
    candidates_path: Path = CANDIDATES_PATH,
) -> list[RuleAmendment]:
    """Capture all amendment proposals available on one job's Pass 2 payload."""
    captured: list[RuleAmendment] = []
    for q_data, annotate_json in iter_job_amendment_payloads(job):
        amendment = capture_amendment_proposal(
            job=job,
            q_data=q_data,
            annotate_json=annotate_json,
            pending_dir=pending_dir,
            candidates_path=candidates_path,
        )
        if amendment is not None:
            captured.append(amendment)
    return captured


def iter_job_amendment_payloads(job: Any) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return ``(q_data, annotate_json)`` pairs carrying amendment proposals.

    Supported shapes:
    - single-question job.pass2_json with ``reasoning.amendment_proposal``
    - multi-question job.pass2_json["_amendment_proposals"] records
    """
    pass2_json = getattr(job, "pass2_json", None)
    if not isinstance(pass2_json, dict):
        return []

    records = pass2_json.get("_amendment_proposals")
    if isinstance(records, list):
        payloads: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            proposal = record.get("amendment_proposal")
            if not isinstance(proposal, dict):
                continue
            q_data = record.get("q_data")
            if not isinstance(q_data, dict):
                q_data = _source_q_data_from_job(job, record.get("source_question_number"))
            payloads.append((q_data, {"reasoning": {"amendment_proposal": proposal}}))
        return payloads

    if extract_amendment_proposal(pass2_json):
        return [(_source_q_data_from_job(job, pass2_json.get("source_question_number")), pass2_json)]
    return []


def _proposal_to_amendment(
    job: Any,
    q_data: dict[str, Any],
    proposal: dict[str, Any],
) -> RuleAmendment:
    source_job_id = str(getattr(job, "id", "") or "")
    exam = _require_source("source_exam_code", job, q_data)
    subject = _require_source("source_subject_code", job, q_data)
    section = _require_source("source_section_code", job, q_data)
    module = _require_source("source_module_code", job, q_data)
    q_num = int(q_data.get("source_question_number") or proposal.get("source_question_number"))

    affected_doc = _affected_doc(subject, proposal, q_data)
    affected_vocab = _affected_vocab(proposal)
    proposed_value = _proposed_value(proposal)
    parent_key = _parent_key(proposal)

    _fallbacks: list[str] = []

    def _first(key: str, *fallbacks: str) -> str | None:
        val = proposal.get(key)
        if val is not None:
            return val
        for fb in fallbacks:
            val = proposal.get(fb)
            if val is not None:
                _fallbacks.append(f"{key}←{fb}")
                return val
        return None

    official_evidence = (
        _first("official_evidence", "evidence_text", "evidence")
        or q_data.get("question_text")
        or ""
    )
    definition = _first("definition", "reason") or ""
    if definition == "" and proposal.get("reason"):
        _fallbacks.append("definition←reason")
        definition = proposal["reason"]
    current_best_fit = _first("current_best_fit", "current_key") or "unknown"
    insufficient_raw = _first("why_current_rules_are_insufficient", "reason")
    insufficient = (
        insufficient_raw
        or "Official item does not fit the current approved controlled vocabulary."
    )

    amendment_id = _amendment_id(affected_vocab, proposed_value, parent_key)
    patch = _rule_doc_patch(proposal, affected_doc, proposed_value, definition, official_evidence)
    master_patch = MasterJsonPatch(
        affected_vocab=affected_vocab,
        proposed_value=proposed_value,
        parent_key=parent_key,
        description=definition,
    )
    example = SupportingExample(
        source_job_id=source_job_id,
        source_exam_code=exam,
        source_subject_code=subject,
        source_section_code=section,
        source_module_code=module,
        source_question_number=q_num,
        official_evidence=official_evidence,
    )

    amendment = RuleAmendment(
        amendment_id=amendment_id,
        source_job_id=source_job_id,
        source_exam_code=exam,
        source_subject_code=subject,
        source_section_code=section,
        source_module_code=module,
        source_question_number=q_num,
        content_origin="official",
        affected_doc=affected_doc,
        proposal_type=proposal.get("proposal_type") or "new_controlled_vocab_key",
        affected_vocab=affected_vocab,
        proposed_value=proposed_value,
        parent_key=parent_key,
        definition=definition,
        current_best_fit=current_best_fit,
        why_current_rules_are_insufficient=insufficient,
        official_evidence=official_evidence,
        rule_doc_patch=patch,
        master_json_patch=master_patch,
        supporting_examples=[example],
    )

    if _fallbacks:
        logger.info(
            "amendment %s used fallback field mappings: %s",
            amendment_id,
            ", ".join(_fallbacks),
        )

    return amendment


def _require_source(name: str, job: Any, q_data: dict[str, Any]) -> str:
    value = q_data.get(name) or getattr(job, name, None)
    if value in (None, ""):
        raise ValueError(f"missing {name}")
    return str(value)


def _affected_doc(subject: str, proposal: dict[str, Any], q_data: dict[str, Any]) -> str:
    explicit = proposal.get("affected_doc")
    if explicit in {"reading", "grammar"}:
        return explicit
    if proposal.get("proposed_parent_role_key") or q_data.get("grammar_role_key"):
        logger.info("affected_doc inferred as grammar from proposal/q_data heuristics")
        return "grammar"
    if proposal.get("proposed_parent_skill_key") or q_data.get("skill_family_key"):
        logger.info("affected_doc inferred as reading from proposal/q_data heuristics")
        return "reading"
    logger.info("affected_doc inferred from subject=%s", subject)
    return "reading" if subject == "verbal" else "grammar"


def _affected_vocab(proposal: dict[str, Any]) -> str:
    vocab = proposal.get("affected_vocab")
    if vocab:
        normalized = _normalize_affected_vocab(str(vocab))
        if normalized != str(vocab).strip():
            logger.info("affected_vocab normalized from %r to %s", vocab, normalized)
        return normalized
    field = proposal.get("affected_field")
    if field and field in FIELD_TO_VOCAB:
        logger.info("affected_vocab inferred from affected_field=%s → %s", field, FIELD_TO_VOCAB[field])
        return FIELD_TO_VOCAB[field]
    if proposal.get("proposed_parent_role_key"):
        logger.info("affected_vocab inferred from proposed_parent_role_key → GRAMMAR_FOCUS_BY_ROLE")
        return "GRAMMAR_FOCUS_BY_ROLE"
    if proposal.get("proposed_parent_skill_key"):
        logger.info("affected_vocab inferred from proposed_parent_skill_key → READING_FOCUS_BY_SKILL_FAMILY")
        return "READING_FOCUS_BY_SKILL_FAMILY"
    raise ValueError("missing affected_vocab")


def _normalize_affected_vocab(value: str) -> str:
    cleaned = _PARENTHETICAL_SUFFIX_RE.sub("", value.strip())
    if cleaned.upper() == cleaned:
        return cleaned

    alias = cleaned.lower()
    if alias in _AFFECTED_VOCAB_ALIASES:
        return _AFFECTED_VOCAB_ALIASES[alias]
    if alias in FIELD_TO_VOCAB:
        return FIELD_TO_VOCAB[alias]
    return cleaned


def _proposed_value(proposal: dict[str, Any]) -> str:
    value = proposal.get("proposed_value")
    if value:
        return str(value)
    value = proposal.get("proposed_key")
    if value:
        logger.info("proposed_value inferred from proposed_key fallback")
        return str(value)
    raise ValueError("missing proposed_value")


def _parent_key(proposal: dict[str, Any]) -> str | None:
    return (
        proposal.get("parent_key")
        or proposal.get("proposed_parent_skill_key")
        or proposal.get("proposed_parent_role_key")
    )


def _rule_doc_patch(
    proposal: dict[str, Any],
    affected_doc: str,
    proposed_value: str,
    definition: str,
    evidence: str,
) -> RuleDocPatch:
    raw_patch = proposal.get("rule_doc_patch")
    if isinstance(raw_patch, dict):
        return RuleDocPatch.model_validate(raw_patch)
    target = "Reading taxonomy section" if affected_doc == "reading" else "Grammar taxonomy section"
    return RuleDocPatch(
        target_section=target,
        before=proposal.get("current_best_fit") or "TBD",
        after=f"- `{proposed_value}` — {definition}",
        rationale=evidence,
    )


def _amendment_id(affected_vocab: str, proposed_value: str, parent_key: str | None) -> str:
    key = "|".join([affected_vocab, proposed_value, parent_key or ""])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"amd-{digest}"


def _merge_supporting_example(path: Path, amendment: RuleAmendment) -> RuleAmendment:
    existing = RuleAmendment.model_validate(json.loads(path.read_text()))
    examples = list(existing.supporting_examples)
    seen = {
        (e.source_job_id, e.source_question_number, e.official_evidence)
        for e in examples
    }
    for example in amendment.supporting_examples:
        key = (example.source_job_id, example.source_question_number, example.official_evidence)
        if key not in seen:
            examples.append(example)
    data = existing.model_dump()
    data["supporting_examples"] = examples
    review_notes = list(existing.review_notes)
    conflict_note = _conflicting_proposal_note(existing, amendment)
    if conflict_note and conflict_note not in review_notes:
        review_notes.append(conflict_note)
    data["review_notes"] = review_notes
    return RuleAmendment.model_validate(data)


def _link_candidate(path: Path, amendment: RuleAmendment) -> None:
    """Attach amendment id to a matching candidate row when present."""
    if not path.exists():
        return
    try:
        with open(path, "a+", encoding="utf-8") as fh:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.seek(0)
                raw = fh.read()
                if not raw.strip():
                    return
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("could not link amendment %s: candidates file is corrupt", amendment.amendment_id)
                    return
                changed = False
                for row in data.get("candidates", []):
                    if row.get("vocab") == amendment.affected_vocab and row.get("value") == amendment.proposed_value:
                        ids = row.setdefault("amendment_ids", [])
                        if amendment.amendment_id not in ids:
                            ids.append(amendment.amendment_id)
                            changed = True
                if changed:
                    fh.seek(0)
                    fh.truncate()
                    json.dump(data, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
            finally:
                if fcntl is not None:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        logger.warning("could not link amendment %s to candidates file: %s", amendment.amendment_id, exc)


def _conflicting_proposal_note(existing: RuleAmendment, incoming: RuleAmendment) -> str | None:
    conflict_fields = [
        "definition",
        "current_best_fit",
        "why_current_rules_are_insufficient",
        "official_evidence",
        "rule_doc_patch",
        "master_json_patch",
    ]
    incoming_data = incoming.model_dump(mode="json")
    existing_data = existing.model_dump(mode="json")
    conflicts = {
        field: {
            "existing": existing_data.get(field),
            "incoming": incoming_data.get(field),
        }
        for field in conflict_fields
        if existing_data.get(field) != incoming_data.get(field)
    }
    if not conflicts:
        return None
    examples = incoming_data.get("supporting_examples") or []
    source = examples[0] if examples else {}
    note = {
        "type": "conflicting_duplicate_proposal",
        "source_job_id": source.get("source_job_id") or incoming.source_job_id,
        "source_question_number": source.get("source_question_number") or incoming.source_question_number,
        "conflicts": conflicts,
    }
    return json.dumps(note, sort_keys=True, ensure_ascii=False)


def _source_q_data_from_job(job: Any, source_question_number: Any = None) -> dict[str, Any]:
    pass1_json = getattr(job, "pass1_json", None)
    source_metadata = {}
    if isinstance(pass1_json, dict):
        source_metadata = pass1_json.get("source_metadata") or {}
    if not isinstance(source_metadata, dict):
        source_metadata = {}
    if isinstance(pass1_json, dict) and source_question_number is None:
        source_question_number = pass1_json.get("source_question_number")

    def _source_value(source_key: str, legacy_key: str) -> Any:
        pass1_value = pass1_json.get(source_key) if isinstance(pass1_json, dict) else None
        return (
            source_metadata.get(source_key)
            or source_metadata.get(legacy_key)
            or pass1_value
            or getattr(job, source_key, None)
        )

    return {
        "source_exam_code": _source_value("source_exam_code", "exam_code"),
        "source_subject_code": _source_value("source_subject_code", "subject_code"),
        "source_section_code": _source_value("source_section_code", "section_code"),
        "source_module_code": _source_value("source_module_code", "module_code"),
        "source_question_number": source_question_number,
    }


def _record_job_warning(job: Any, *, code: str, message: str) -> None:
    warning = {
        "step": "amendment_proposal",
        "severity": "warning",
        "code": code,
        "error": message,
    }
    existing = getattr(job, "validation_errors_jsonb", None)
    if isinstance(existing, list):
        job.validation_errors_jsonb = [*existing, warning]
    elif existing:
        job.validation_errors_jsonb = [existing, warning]
    else:
        job.validation_errors_jsonb = [warning]
