"""Write reproducible ingestion analysis reports and re-appraisals."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis" / "ingestion"
HASH_PATHS = {
    "master_json_hash": REPO_ROOT / "vocabulary" / "master.json",
    "reading_rules_hash": REPO_ROOT / "rules_agent_dsat_reading_v2.md",
    "grammar_rules_hash": REPO_ROOT / "rules_agent_dsat_grammar_ingestion_generation_v8.md",
    "ontology_hash": REPO_ROOT / "backend" / "app" / "models" / "ontology.py",
}


def current_analysis_hashes(*, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    return {
        name: _sha256((repo_root / path.relative_to(REPO_ROOT)))
        for name, path in HASH_PATHS.items()
    }


def write_ingestion_analysis(job: Any, *, repo_root: Path = REPO_ROOT) -> Path | None:
    """Write one immutable analysis folder for an official ingestion job."""
    if getattr(job, "content_origin", None) != "official":
        return None
    exam = _exam_code(job) or "UNKNOWN_EXAM"
    run_id = f"run_{datetime.now(timezone.utc).date().isoformat()}_{getattr(job, 'id', 'unknown')}"
    root = repo_root / "analysis" / "ingestion" / exam / run_id
    questions_dir = root / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)

    hashes = current_analysis_hashes(repo_root=repo_root)
    question_records = _question_records(job)
    coverage = _taxonomy_coverage(question_records, hashes, job)
    failures = _validation_failures(job, hashes)
    amendments = _amendment_candidates(job, hashes)

    _write_json(root / "taxonomy_coverage.json", coverage)
    _write_json(root / "validation_failures.json", failures)
    _write_json(root / "amendment_candidates.json", amendments)
    (root / "summary.md").write_text(_summary_markdown(job, hashes, coverage, failures, amendments), encoding="utf-8")
    for idx, record in enumerate(question_records, start=1):
        # Skip records with no usable content (e.g. pass1 fallback rows that
        # carry no taxonomy fields and no question text) so the report does
        # not emit empty "# Question" stub files.
        if not _has_question_content(record):
            continue
        q_num = record.get("source_question_number") or idx
        (questions_dir / f"q{int(q_num):03d}.md").write_text(_question_markdown(record), encoding="utf-8")
    return root


def write_reappraisals_for_master_growth(
    *,
    repo_root: Path = REPO_ROOT,
    analysis_root: Path | None = None,
) -> list[Path]:
    """Create re-appraisal reports for prior analyses with older master hashes."""
    analysis_root = analysis_root or repo_root / "analysis" / "ingestion"
    current_hash = current_analysis_hashes(repo_root=repo_root)["master_json_hash"]
    written: list[Path] = []
    if not analysis_root.exists():
        return written
    for coverage_path in analysis_root.rglob("taxonomy_coverage.json"):
        try:
            data = json.loads(coverage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        old_hash = data.get("hashes", {}).get("master_json_hash")
        if not old_hash or old_hash == current_hash:
            continue
        target = coverage_path.parent / f"reappraisal_{current_hash[:12]}.md"
        if target.exists():
            continue
        target.write_text(_reappraisal_markdown(data, old_hash, current_hash), encoding="utf-8")
        written.append(target)
    return written


def _question_records(job: Any) -> list[dict[str, Any]]:
    pass2 = getattr(job, "pass2_json", None) or {}
    if isinstance(pass2, dict) and isinstance(pass2.get("_annotations"), list):
        return [
            {
                **(record.get("annotation") or {}),
                "source_question_number": record.get("source_question_number"),
            }
            for record in pass2["_annotations"]
            if isinstance(record, dict)
        ]
    if isinstance(pass2, dict) and pass2:
        return [pass2]
    pass1 = getattr(job, "pass1_json", None)
    if isinstance(pass1, dict) and isinstance(pass1.get("questions"), list):
        return [q for q in pass1["questions"] if isinstance(q, dict)]
    if isinstance(pass1, dict):
        return [pass1]
    return []


def _taxonomy_coverage(question_records: list[dict[str, Any]], hashes: dict[str, str], job: Any) -> dict[str, Any]:
    fields = [
        "question_family_key",
        "grammar_role_key",
        "grammar_focus_key",
        "skill_family_key",
        "reading_focus_key",
        "reasoning_trap_key",
        "stimulus_mode_key",
        "stem_type_key",
    ]
    counts = {field: dict(Counter(record.get(field) for record in question_records if record.get(field))) for field in fields}
    return {
        "job_id": str(getattr(job, "id", "")),
        "source_exam_code": _exam_code(job),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hashes": hashes,
        "question_count": len(question_records),
        "field_counts": counts,
    }


def _validation_failures(job: Any, hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "job_id": str(getattr(job, "id", "")),
        "hashes": hashes,
        "validation_errors": getattr(job, "validation_errors_jsonb", None) or [],
    }


def _amendment_candidates(job: Any, hashes: dict[str, str]) -> dict[str, Any]:
    pass2 = getattr(job, "pass2_json", None) or {}
    proposals = []
    if isinstance(pass2, dict):
        if isinstance(pass2.get("_amendment_proposals"), list):
            proposals = pass2["_amendment_proposals"]
        else:
            # Fall back to the shared extractor, which handles both
            # reasoning.amendment_proposal and the legacy top-level
            # amendment_proposal key for single-proposal jobs.
            from app.pipeline.amendments import extract_amendment_proposal

            single = extract_amendment_proposal(pass2)
            if single:
                proposals = [single]
    return {
        "job_id": str(getattr(job, "id", "")),
        "hashes": hashes,
        "amendment_candidates": proposals,
    }


def _summary_markdown(job: Any, hashes: dict[str, str], coverage: dict[str, Any], failures: dict[str, Any], amendments: dict[str, Any]) -> str:
    return "\n".join([
        f"# Ingestion Analysis {getattr(job, 'id', '')}",
        "",
        f"- source_exam_code: `{_exam_code(job) or ''}`",
        f"- status: `{getattr(job, 'status', '')}`",
        f"- question_count: `{coverage['question_count']}`",
        f"- validation_failure_count: `{len(failures['validation_errors'])}`",
        f"- amendment_candidate_count: `{len(amendments['amendment_candidates'])}`",
        "",
        "## Hashes",
        *[f"- {name}: `{value}`" for name, value in hashes.items()],
        "",
    ])


_QUESTION_FIELDS = (
    "question_family_key",
    "grammar_role_key",
    "grammar_focus_key",
    "skill_family_key",
    "reading_focus_key",
    "stimulus_mode_key",
    "stem_type_key",
)


def _has_question_content(record: dict[str, Any]) -> bool:
    """True when a record carries enough to produce a non-empty question file."""
    return bool(record.get("question_text")) or any(
        record.get(field) for field in _QUESTION_FIELDS
    )


def _question_markdown(record: dict[str, Any]) -> str:
    title = record.get("source_question_number") or ""
    lines = [f"# Question {title}", ""]
    for field in _QUESTION_FIELDS:
        if record.get(field):
            lines.append(f"- {field}: `{record[field]}`")
    if record.get("question_text"):
        lines.extend(["", "## Question Text", "", str(record["question_text"])])
    return "\n".join(lines) + "\n"


def _reappraisal_markdown(data: dict[str, Any], old_hash: str, current_hash: str) -> str:
    return "\n".join([
        "# Vocabulary Re-Appraisal",
        "",
        f"- previous_master_json_hash: `{old_hash}`",
        f"- current_master_json_hash: `{current_hash}`",
        f"- source_exam_code: `{data.get('source_exam_code') or ''}`",
        f"- question_count: `{data.get('question_count') or 0}`",
        "",
        "This report records that the analysis should be re-appraised against the current compiled vocabulary.",
        "",
    ])


def _exam_code(job: Any) -> str | None:
    if getattr(job, "source_exam_code", None):
        return str(job.source_exam_code)
    pass1 = getattr(job, "pass1_json", None)
    if isinstance(pass1, dict):
        raw_meta = pass1.get("source_metadata")
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        return pass1.get("source_exam_code") or meta.get("source_exam_code")
    return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
