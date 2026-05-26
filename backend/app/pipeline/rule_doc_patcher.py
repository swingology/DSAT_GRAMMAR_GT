"""Rule-document body patch engine for approved vocabulary amendments."""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from app.models.amendments import AmendmentStatus, RuleAmendment

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_BY_AFFECTED_DOC = {
    "reading": "rules_agent_dsat_reading_v3.md",
    "grammar": "rules_agent_dsat_grammar_ingestion_generation_v8.md",
}
PENDING_DIR = REPO_ROOT / "vocabulary" / "amendments" / "pending"
NEEDS_MANUAL_PATCH_DIR = REPO_ROOT / "vocabulary" / "amendments" / "needs_manual_patch"


@dataclass(frozen=True)
class RuleDocPatchResult:
    ok: bool
    amendment_id: str
    affected_doc: str
    doc_path: Path | None
    diff: str = ""
    error: str = ""
    conflict_details: dict | None = None


def dry_run_rule_doc_patch(
    amendment: RuleAmendment,
    *,
    repo_root: Path = REPO_ROOT,
) -> RuleDocPatchResult:
    """Return the rule-doc body diff without writing files."""
    return _build_patch_result(amendment, repo_root=repo_root)


def apply_rule_doc_patch(
    amendment_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    regenerate_appendix: bool = False,
) -> RuleDocPatchResult:
    """Apply one amendment's rule-doc body patch.

    Failure updates the amendment file to ``needs_manual_patch`` and moves it
    into ``vocabulary/amendments/needs_manual_patch`` when possible.
    Generated appendix regeneration is intentionally opt-in; callers should set
    ``regenerate_appendix=True`` only after the amendment has been promoted into
    ``vocabulary/master.json``.
    """
    amendment = _load_amendment(amendment_path)
    return apply_loaded_rule_doc_patch(
        amendment,
        amendment_path,
        repo_root=repo_root,
        regenerate_appendix=regenerate_appendix,
    )


def apply_loaded_rule_doc_patch(
    amendment: RuleAmendment,
    amendment_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    regenerate_appendix: bool = False,
) -> RuleDocPatchResult:
    """Apply a previously loaded amendment's rule-doc body patch."""
    result = _build_patch_result(amendment, repo_root=repo_root)
    if not result.ok:
        _mark_needs_manual_patch(amendment_path, amendment, result, repo_root=repo_root)
        return result

    if result.doc_path is None:
        result = RuleDocPatchResult(
            ok=False,
            amendment_id=amendment.amendment_id,
            affected_doc=str(amendment.affected_doc),
            doc_path=None,
            error="rule document patch succeeded without a resolved document path",
            conflict_details={"step": "apply_rule_doc_patch"},
        )
        _mark_needs_manual_patch(amendment_path, amendment, result, repo_root=repo_root)
        return result
    if regenerate_appendix and not _master_json_contains_amendment_value(amendment, repo_root=repo_root):
        result = RuleDocPatchResult(
            ok=False,
            amendment_id=amendment.amendment_id,
            affected_doc=str(amendment.affected_doc),
            doc_path=result.doc_path,
            error="cannot regenerate VOCAB appendices before amendment value is active in master.json",
            conflict_details={
                "step": "regenerate_vocab_appendices",
                "affected_vocab": amendment.affected_vocab,
                "proposed_value": amendment.proposed_value,
                "parent_key": amendment.parent_key,
            },
        )
        _mark_needs_manual_patch(amendment_path, amendment, result, repo_root=repo_root)
        return result

    result.doc_path.write_text(_patched_text(result.doc_path.read_text(), amendment), encoding="utf-8")
    if regenerate_appendix:
        regen = regenerate_vocab_appendices(repo_root=repo_root)
        if not regen.ok:
            _mark_needs_manual_patch(amendment_path, amendment, regen, repo_root=repo_root)
            return regen
    return result


def regenerate_vocab_appendices(*, repo_root: Path = REPO_ROOT) -> RuleDocPatchResult:
    """Regenerate ontology.py and generated VOCAB appendices from master.json."""
    script = repo_root / "scripts" / "gen_vocab.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--generate"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return RuleDocPatchResult(
            ok=False,
            amendment_id="",
            affected_doc="",
            doc_path=None,
            error=f"regeneration failed: {exc}",
            conflict_details={"step": "regenerate_vocab_appendices"},
        )
    if completed.returncode != 0:
        return RuleDocPatchResult(
            ok=False,
            amendment_id="",
            affected_doc="",
            doc_path=None,
            error="regeneration failed",
            conflict_details={
                "step": "regenerate_vocab_appendices",
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )
    return RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)


def _load_amendment(path: Path) -> RuleAmendment:
    try:
        return RuleAmendment.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"invalid amendment file {path}: {exc}") from exc


def _build_patch_result(amendment: RuleAmendment, *, repo_root: Path) -> RuleDocPatchResult:
    doc_path = repo_root / DOC_BY_AFFECTED_DOC[str(amendment.affected_doc)]
    if not doc_path.exists():
        return RuleDocPatchResult(
            ok=False,
            amendment_id=amendment.amendment_id,
            affected_doc=str(amendment.affected_doc),
            doc_path=doc_path,
            error=f"rule document not found: {doc_path}",
            conflict_details={"path": str(doc_path)},
        )

    text = doc_path.read_text(encoding="utf-8")
    validation_error = _validate_body_patch_target(text, amendment)
    if validation_error:
        return RuleDocPatchResult(
            ok=False,
            amendment_id=amendment.amendment_id,
            affected_doc=str(amendment.affected_doc),
            doc_path=doc_path,
            error=validation_error,
            conflict_details={
                "target_section": amendment.rule_doc_patch.target_section,
                "before": amendment.rule_doc_patch.before,
            },
        )

    new_text = _patched_text(text, amendment)
    return RuleDocPatchResult(
        ok=True,
        amendment_id=amendment.amendment_id,
        affected_doc=str(amendment.affected_doc),
        doc_path=doc_path,
        diff=_unified_diff(doc_path, text, new_text),
    )


def _patched_text(text: str, amendment: RuleAmendment) -> str:
    patch = amendment.rule_doc_patch
    return text.replace(patch.before, patch.after, 1)


def _validate_body_patch_target(text: str, amendment: RuleAmendment) -> str | None:
    patch = amendment.rule_doc_patch
    if "VOCAB:" in patch.target_section or "Generated Vocabulary" in patch.target_section:
        return "rule_doc_patch.target_section appears to target a generated VOCAB appendix"
    count = text.count(patch.before)
    if count == 0:
        return "rule_doc_patch.before does not match the target rule document"
    if count > 1:
        return "rule_doc_patch.before is ambiguous in the target rule document"
    index = text.find(patch.before)
    if _inside_generated_vocab_block(text, index):
        return "rule_doc_patch.before targets a generated VOCAB appendix block"
    if patch.target_section and patch.target_section not in text:
        return "rule_doc_patch.target_section was not found in the target rule document"
    return None


def _inside_generated_vocab_block(text: str, index: int) -> bool:
    start_match = None
    for match in re.finditer(r"<!-- VOCAB:([^>]+) START -->", text):
        if match.start() <= index:
            start_match = match
        else:
            break
    if start_match is None:
        return False

    block_name = start_match.group(1)
    end_marker = f"<!-- VOCAB:{block_name} END -->"
    block_end = text.find(end_marker, start_match.end())
    if block_end == -1:
        return False
    return start_match.start() <= index < block_end + len(end_marker)


def _master_json_contains_amendment_value(amendment: RuleAmendment, *, repo_root: Path) -> bool:
    master_path = repo_root / "vocabulary" / "master.json"
    if not master_path.exists():
        return False
    master = json.loads(master_path.read_text(encoding="utf-8"))
    vocab = next(
        (item for item in master.get("vocabularies", []) if item.get("name") == amendment.affected_vocab),
        None,
    )
    if vocab is None:
        return False
    for entry in vocab.get("entries", []):
        if entry.get("value") != amendment.proposed_value:
            continue
        if entry.get("status") != "active":
            continue
        if amendment.parent_key is not None and entry.get("parent") != amendment.parent_key:
            continue
        return True
    return False


def _unified_diff(path: Path, old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{path.name}:before",
            tofile=f"{path.name}:after",
        )
    )


def _mark_needs_manual_patch(
    amendment_path: Path,
    amendment: RuleAmendment,
    result: RuleDocPatchResult,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    data = amendment.model_dump(mode="json")
    data["status"] = AmendmentStatus.NEEDS_MANUAL_PATCH.value
    notes = list(data.get("review_notes") or [])
    notes.append(json.dumps({
        "type": "rule_doc_patch_failure",
        "error": result.error,
        "conflict_details": result.conflict_details or {},
    }, sort_keys=True))
    data["review_notes"] = notes
    needs_manual_patch_dir = repo_root / "vocabulary" / "amendments" / "needs_manual_patch"
    needs_manual_patch_dir.mkdir(parents=True, exist_ok=True)
    target = needs_manual_patch_dir / amendment_path.name
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if amendment_path.exists() and amendment_path.resolve() != target.resolve():
        amendment_path.unlink()
