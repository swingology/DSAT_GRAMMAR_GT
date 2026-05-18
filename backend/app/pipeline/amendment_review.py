"""Admin review and promotion operations for rule amendments."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models.amendments import AdminDecision, AmendmentStatus, RuleAmendment
from app.pipeline.rule_doc_patcher import (
    REPO_ROOT,
    apply_loaded_rule_doc_patch,
    dry_run_rule_doc_patch,
)

logger = logging.getLogger(__name__)

AMENDMENTS_DIR = REPO_ROOT / "vocabulary" / "amendments"
PENDING_DIR = AMENDMENTS_DIR / "pending"
APPROVED_DIR = AMENDMENTS_DIR / "approved"
REJECTED_DIR = AMENDMENTS_DIR / "rejected"
CANDIDATES_PATH = REPO_ROOT / "vocabulary" / "candidates.json"
MASTER_PATH = REPO_ROOT / "vocabulary" / "master.json"


@dataclass(frozen=True)
class AmendmentOperationResult:
    ok: bool
    amendment: RuleAmendment | None = None
    path: Path | None = None
    error: str = ""
    details: dict[str, Any] | None = None
    error_code: str = "conflict"


def list_amendments(*, repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Return all reviewable amendment files across workflow directories."""
    rows: list[dict[str, Any]] = []
    base = repo_root / "vocabulary" / "amendments"
    for status_dir in ("pending", "approved", "rejected", "needs_manual_patch"):
        directory = base / status_dir
        for path in sorted(directory.glob("*.json")):
            result = load_amendment_by_id(path.stem, repo_root=repo_root)
            if result.ok and result.amendment:
                rows.append(_amendment_summary(result.amendment, result.path or path))
            else:
                rows.append({
                    "amendment_id": path.stem,
                    "status": "invalid",
                    "path": str(path),
                    "error": result.error,
                })
    return rows


def load_amendment_by_id(amendment_id: str, *, repo_root: Path = REPO_ROOT) -> AmendmentOperationResult:
    path = _find_amendment_path(amendment_id, repo_root=repo_root)
    if path is None:
        return AmendmentOperationResult(ok=False, error="Amendment not found", error_code="not_found")
    try:
        amendment = RuleAmendment.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValidationError) as exc:
        return AmendmentOperationResult(ok=False, path=path, error=f"Invalid amendment file: {exc}")
    return AmendmentOperationResult(ok=True, amendment=amendment, path=path)


def approve_amendment(
    amendment_id: str,
    *,
    reviewer: str,
    notes: str = "",
    repo_root: Path = REPO_ROOT,
) -> AmendmentOperationResult:
    loaded = load_amendment_by_id(amendment_id, repo_root=repo_root)
    if not loaded.ok or loaded.amendment is None or loaded.path is None:
        return loaded
    amendment = loaded.amendment
    status_guard = _require_status(
        amendment,
        {AmendmentStatus.PENDING.value, AmendmentStatus.MORE_EVIDENCE_REQUESTED.value},
        operation="approve",
    )
    if not status_guard.ok:
        return status_guard
    validation = validate_amendment_for_approval(amendment, repo_root=repo_root)
    if not validation.ok:
        return validation

    data = amendment.model_dump(mode="json")
    data["status"] = AmendmentStatus.APPROVED.value
    data["admin_decision"] = _decision(reviewer, "approve", notes)
    data["updated_at"] = _now()
    _write_json(loaded.path, data)
    return load_amendment_by_id(amendment_id, repo_root=repo_root)


def reject_amendment(
    amendment_id: str,
    *,
    reviewer: str,
    notes: str = "",
    repo_root: Path = REPO_ROOT,
) -> AmendmentOperationResult:
    loaded = load_amendment_by_id(amendment_id, repo_root=repo_root)
    if not loaded.ok or loaded.amendment is None or loaded.path is None:
        return loaded
    status_guard = _require_status(
        loaded.amendment,
        {
            AmendmentStatus.PENDING.value,
            AmendmentStatus.APPROVED.value,
            AmendmentStatus.MORE_EVIDENCE_REQUESTED.value,
            AmendmentStatus.NEEDS_MANUAL_PATCH.value,
        },
        operation="reject",
    )
    if not status_guard.ok:
        return status_guard
    data = loaded.amendment.model_dump(mode="json")
    data["status"] = AmendmentStatus.REJECTED.value
    data["admin_decision"] = _decision(reviewer, "reject", notes)
    data["updated_at"] = _now()
    target = repo_root / "vocabulary" / "amendments" / "rejected" / loaded.path.name
    _write_json(target, data)
    if loaded.path.resolve() != target.resolve():
        loaded.path.unlink()
    return load_amendment_by_id(amendment_id, repo_root=repo_root)


def request_more_evidence(
    amendment_id: str,
    *,
    reviewer: str,
    notes: str = "",
    repo_root: Path = REPO_ROOT,
) -> AmendmentOperationResult:
    loaded = load_amendment_by_id(amendment_id, repo_root=repo_root)
    if not loaded.ok or loaded.amendment is None or loaded.path is None:
        return loaded
    status_guard = _require_status(
        loaded.amendment,
        {AmendmentStatus.PENDING.value},
        operation="request_more_evidence",
    )
    if not status_guard.ok:
        return status_guard
    data = loaded.amendment.model_dump(mode="json")
    data["status"] = AmendmentStatus.MORE_EVIDENCE_REQUESTED.value
    data["admin_decision"] = _decision(reviewer, "request_more_evidence", notes)
    data["updated_at"] = _now()
    _write_json(loaded.path, data)
    return load_amendment_by_id(amendment_id, repo_root=repo_root)


def promote_amendment(
    amendment_id: str,
    *,
    reviewer: str,
    notes: str = "",
    repo_root: Path = REPO_ROOT,
) -> AmendmentOperationResult:
    loaded = load_amendment_by_id(amendment_id, repo_root=repo_root)
    if not loaded.ok or loaded.amendment is None or loaded.path is None:
        return loaded
    amendment = loaded.amendment
    if amendment.status != AmendmentStatus.APPROVED.value:
        return AmendmentOperationResult(
            ok=False,
            amendment=amendment,
            path=loaded.path,
            error="Amendment must be approved before promotion",
            error_code="validation",
        )
    if loaded.path.parent.name != "pending":
        return AmendmentOperationResult(
            ok=False,
            amendment=amendment,
            path=loaded.path,
            error="Approved amendment must be in pending review directory before promotion",
            error_code="validation",
        )
    validation = validate_amendment_for_approval(amendment, repo_root=repo_root)
    if not validation.ok:
        return validation

    touched = [
        repo_root / "vocabulary" / "master.json",
        repo_root / "backend" / "app" / "models" / "ontology.py",
        repo_root / "rules_agent_dsat_reading_v2.md",
        repo_root / "rules_agent_dsat_grammar_ingestion_generation_v7.md",
    ]
    backups = {path: path.read_text(encoding="utf-8") for path in touched if path.exists()}
    try:
        master_result = _promote_master_json(amendment, repo_root=repo_root)
        if not master_result.ok:
            return master_result
        patch_result = apply_loaded_rule_doc_patch(
            amendment,
            loaded.path,
            repo_root=repo_root,
            regenerate_appendix=True,
        )
        if not patch_result.ok:
            _restore_files(backups)
            return AmendmentOperationResult(
                ok=False,
                amendment=amendment,
                path=loaded.path,
                error=patch_result.error,
                details=patch_result.conflict_details,
                error_code="conflict",
            )
        data = amendment.model_dump(mode="json")
        data["status"] = AmendmentStatus.PROMOTED.value
        data["admin_decision"] = _decision(reviewer, "promote", notes)
        data["updated_at"] = _now()
        review_notes = list(data.get("review_notes") or [])
        review_notes.append(json.dumps({
            "type": "promotion",
            "promoted_at": _now(),
            "affected_vocab": amendment.affected_vocab,
            "proposed_value": amendment.proposed_value,
            "parent_key": amendment.parent_key,
        }, sort_keys=True))
        data["review_notes"] = review_notes
        target = repo_root / "vocabulary" / "amendments" / "approved" / loaded.path.name
        _write_json(target, data)
        if loaded.path.exists() and loaded.path.resolve() != target.resolve():
            loaded.path.unlink()
        _drop_candidate(repo_root / "vocabulary" / "candidates.json", amendment)
    except Exception:
        _restore_files(backups)
        raise
    # Re-appraisal runs only after the promotion has fully committed (master.json,
    # rule docs, and the amendment file are already updated). A failure here must
    # NOT roll back the committed promotion, so it is best-effort and logged.
    try:
        from app.pipeline.ingestion_analysis import write_reappraisals_for_master_growth
        write_reappraisals_for_master_growth(repo_root=repo_root)
    except Exception:
        logger.warning(
            "re-appraisal write failed after promoting amendment %s; promotion stands",
            amendment_id,
            exc_info=True,
        )
    return load_amendment_by_id(amendment_id, repo_root=repo_root)


def validate_amendment_for_approval(
    amendment: RuleAmendment,
    *,
    repo_root: Path = REPO_ROOT,
) -> AmendmentOperationResult:
    if amendment.content_origin != "official":
        return AmendmentOperationResult(
            ok=False,
            amendment=amendment,
            error="Amendment source must be official",
            error_code="validation",
        )
    patch_result = dry_run_rule_doc_patch(amendment, repo_root=repo_root)
    if not patch_result.ok:
        return AmendmentOperationResult(
            ok=False,
            amendment=amendment,
            path=patch_result.doc_path,
            error=patch_result.error,
            details=patch_result.conflict_details,
            error_code="conflict",
        )
    master_result = _validate_master_json_patch(amendment, repo_root=repo_root)
    if not master_result.ok:
        return master_result
    candidate_result = _ensure_candidate(amendment, repo_root=repo_root)
    if not candidate_result.ok:
        return candidate_result
    return AmendmentOperationResult(ok=True, amendment=amendment)


def _find_amendment_path(amendment_id: str, *, repo_root: Path) -> Path | None:
    base = repo_root / "vocabulary" / "amendments"
    for status_dir in ("pending", "approved", "rejected", "needs_manual_patch"):
        path = base / status_dir / f"{amendment_id}.json"
        if path.exists():
            return path
    return None


def _validate_master_json_patch(amendment: RuleAmendment, *, repo_root: Path) -> AmendmentOperationResult:
    master = _load_master(repo_root)
    vocab = _find_vocab(master, amendment.affected_vocab)
    if vocab is None:
        return AmendmentOperationResult(ok=False, amendment=amendment, error="Affected vocabulary not found in master.json", error_code="validation")
    for entry in vocab.get("entries", []):
        if entry.get("value") == amendment.proposed_value and entry.get("status") == "active":
            if amendment.parent_key is None or entry.get("parent") == amendment.parent_key:
                return AmendmentOperationResult(ok=False, amendment=amendment, error="Proposed key is already active", error_code="validation")
    kind = vocab.get("kind")
    if kind == "hierarchical":
        if not amendment.parent_key:
            return AmendmentOperationResult(ok=False, amendment=amendment, error="parent_key is required for hierarchical vocabulary", error_code="validation")
        parent_set = vocab.get("parent_set")
        parent_vocab = _find_vocab(master, parent_set)
        if parent_vocab is None:
            return AmendmentOperationResult(ok=False, amendment=amendment, error="Parent vocabulary not found in master.json", error_code="validation")
        if not any(
            entry.get("value") == amendment.parent_key and entry.get("status") == "active"
            for entry in parent_vocab.get("entries", [])
        ):
            return AmendmentOperationResult(ok=False, amendment=amendment, error="parent_key is not active in parent vocabulary", error_code="validation")
    elif amendment.parent_key:
        return AmendmentOperationResult(ok=False, amendment=amendment, error="parent_key is only valid for hierarchical vocabulary", error_code="validation")
    return AmendmentOperationResult(ok=True, amendment=amendment)


def _promote_master_json(amendment: RuleAmendment, *, repo_root: Path) -> AmendmentOperationResult:
    validation = _validate_master_json_patch(amendment, repo_root=repo_root)
    if not validation.ok:
        return validation
    master = _load_master(repo_root)
    vocab = _find_vocab(master, amendment.affected_vocab)
    if vocab is None:
        return AmendmentOperationResult(ok=False, amendment=amendment, error="Affected vocabulary not found in master.json", error_code="validation")
    entry = {
        "value": amendment.proposed_value,
        "status": "active",
        "added": datetime.now(timezone.utc).date().isoformat(),
        "description": amendment.master_json_patch.description or amendment.definition,
    }
    if vocab.get("kind") == "hierarchical":
        entry["parent"] = amendment.parent_key
    vocab.setdefault("entries", []).append(entry)
    _write_json(repo_root / "vocabulary" / "master.json", master)
    return AmendmentOperationResult(ok=True, amendment=amendment)


def _ensure_candidate(amendment: RuleAmendment, *, repo_root: Path) -> AmendmentOperationResult:
    path = repo_root / "vocabulary" / "candidates.json"
    now = _now()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return AmendmentOperationResult(ok=False, amendment=amendment, error=f"candidates.json is invalid: {exc}", error_code="validation")
    else:
        data = {"schema_version": 1, "candidates": []}
    candidates = data.setdefault("candidates", [])
    for row in candidates:
        if row.get("vocab") == amendment.affected_vocab and row.get("value") == amendment.proposed_value:
            ids = row.setdefault("amendment_ids", [])
            if amendment.amendment_id not in ids:
                ids.append(amendment.amendment_id)
                _write_json(path, data)
            return AmendmentOperationResult(ok=True, amendment=amendment)
    candidates.append({
        "vocab": amendment.affected_vocab,
        "value": amendment.proposed_value,
        "field": "",
        "first_seen": now,
        "last_seen": now,
        "occurrences": 0,
        "job_ids": [amendment.source_job_id],
        "contexts": [],
        "amendment_ids": [amendment.amendment_id],
    })
    _write_json(path, data)
    return AmendmentOperationResult(ok=True, amendment=amendment)


def _drop_candidate(path: Path, amendment: RuleAmendment) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidates"] = [
        row for row in data.get("candidates", [])
        if not (row.get("vocab") == amendment.affected_vocab and row.get("value") == amendment.proposed_value)
    ]
    _write_json(path, data)


def _amendment_summary(amendment: RuleAmendment, path: Path) -> dict[str, Any]:
    return {
        "amendment_id": amendment.amendment_id,
        "status": amendment.status,
        "affected_doc": amendment.affected_doc,
        "affected_vocab": amendment.affected_vocab,
        "proposed_value": amendment.proposed_value,
        "parent_key": amendment.parent_key,
        "source_job_id": amendment.source_job_id,
        "source_question_number": amendment.source_question_number,
        "path": str(path),
        "updated_at": amendment.updated_at.isoformat() if amendment.updated_at else None,
    }


def _load_master(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / "vocabulary" / "master.json").read_text(encoding="utf-8"))


def _find_vocab(master: dict[str, Any], name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    return next((item for item in master.get("vocabularies", []) if item.get("name") == name), None)


def _require_status(
    amendment: RuleAmendment,
    allowed: set[str],
    *,
    operation: str,
) -> AmendmentOperationResult:
    if amendment.status in allowed:
        return AmendmentOperationResult(ok=True, amendment=amendment)
    return AmendmentOperationResult(
        ok=False,
        amendment=amendment,
        error=f"Cannot {operation} amendment with status {amendment.status!r}",
        error_code="validation",
    )


def _decision(reviewer: str, decision: str, notes: str) -> dict[str, Any]:
    return AdminDecision(reviewer=reviewer, decision=decision, notes=notes).model_dump(mode="json")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _restore_files(backups: dict[Path, str]) -> None:
    for path, text in backups.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
