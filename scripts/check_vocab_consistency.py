#!/usr/bin/env python3
"""Scan DB JSONB and exports against vocabulary/master.json."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
MASTER_PATH = REPO_ROOT / "vocabulary" / "master.json"
DEFAULT_EXPORTS_PATH = REPO_ROOT / "analysis"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.vocab_fields import SCANNER_FIELD_TO_VOCAB  # noqa: E402

FIELD_TO_VOCAB = SCANNER_FIELD_TO_VOCAB
KNOWN_PARENT_FIELD_BY_CHILD_FIELD = {
    "grammar_focus_key": "grammar_role_key",
    "target_grammar_focus_key": "target_grammar_role_key",
    "reading_focus_key": "skill_family_key",
    "target_reading_focus_key": "target_reading_skill_family_key",
}
PARENT_ALIAS_FIELDS = {
    "READING_SKILL_FAMILY_KEYS": ("skill_family_key", "reading_skill_family_key", "target_reading_skill_family_key"),
    "GRAMMAR_ROLE_KEYS": ("grammar_role_key", "target_grammar_role_key"),
}


@dataclass(frozen=True)
class VocabIndex:
    active: dict[str, set[str]]
    deprecated: dict[str, set[str]]
    parents: dict[str, dict[str, str]]
    parent_sets: dict[str, str]
    reading_question_families: set[str]


def load_vocab_index(master_path: Path = MASTER_PATH) -> VocabIndex:
    master = json.loads(master_path.read_text(encoding="utf-8"))
    active: dict[str, set[str]] = {}
    deprecated: dict[str, set[str]] = {}
    parents: dict[str, dict[str, str]] = {}
    parent_sets: dict[str, str] = {}
    for vocab in master.get("vocabularies", []):
        name = vocab["name"]
        active[name] = set()
        deprecated[name] = set()
        if vocab.get("kind") == "hierarchical":
            parents[name] = {}
            if vocab.get("parent_set"):
                parent_sets[name] = vocab["parent_set"]
        for entry in vocab.get("entries", []):
            status = entry.get("status", "active")
            value = entry.get("value")
            if not value:
                continue
            if status == "active":
                active[name].add(value)
            elif status == "deprecated":
                deprecated[name].add(value)
            if vocab.get("kind") == "hierarchical" and entry.get("parent"):
                parents[name][value] = entry["parent"]
    return VocabIndex(
        active=active,
        deprecated=deprecated,
        parents=parents,
        parent_sets=parent_sets,
        reading_question_families=active.get("READING_QUESTION_FAMILY_KEYS", set()),
    )


def scan_records(records: Iterable[dict[str, Any]], index: VocabIndex) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for record in records:
        payload = record.get("payload")
        if payload is None:
            continue
        source = str(record.get("source") or "unknown")
        source_id = str(record.get("source_id") or "")
        issues.extend(_scan_value(payload, index, source=source, source_id=source_id, path="$"))
    return issues


def scan_option_rows(rows: Iterable[dict[str, Any]], index: VocabIndex) -> list[dict[str, Any]]:
    records = [
        {
            "source": "question_options",
            "source_id": row.get("id") or row.get("question_id") or "",
            "payload": row,
        }
        for row in rows
    ]
    return scan_records(records, index)


def report_summary(issues: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue["code"]] = counts.get(issue["code"], 0) + 1
    return {"ok": not issues, "issue_count": len(issues), "counts_by_code": counts, "issues": issues}


def _scan_value(value: Any, index: VocabIndex, *, source: str, source_id: str, path: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        issues.extend(_scan_dict(value, index, source=source, source_id=source_id, path=path))
        for key, child in value.items():
            issues.extend(_scan_value(child, index, source=source, source_id=source_id, path=f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            issues.extend(_scan_value(child, index, source=source, source_id=source_id, path=f"{path}[{idx}]"))
    return issues


def _scan_dict(payload: dict[str, Any], index: VocabIndex, *, source: str, source_id: str, path: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field, vocab_name in FIELD_TO_VOCAB.items():
        raw = payload.get(field)
        for value in _values(raw):
            issues.extend(_check_vocab_value(index, vocab_name, value, source, source_id, f"{path}.{field}", field))

    issues.extend(_check_parent_mappings(payload, index, source, source_id, path))
    issues.extend(_check_domain_rules(payload, index, source, source_id, path))
    issues.extend(_check_reading_shape_rules(payload, index, source, source_id, path))
    return issues


def _check_vocab_value(
    index: VocabIndex,
    vocab_name: str,
    value: str,
    source: str,
    source_id: str,
    path: str,
    field: str,
) -> list[dict[str, Any]]:
    if value in index.active.get(vocab_name, set()):
        return []
    if value in index.deprecated.get(vocab_name, set()):
        return [_issue("warning", "deprecated_key", source, source_id, path, field, value, f"{value!r} is deprecated in {vocab_name}")]
    return [_issue("review", "unknown_key", source, source_id, path, field, value, f"{value!r} is not active in {vocab_name}")]


def _check_parent_mappings(
    payload: dict[str, Any],
    index: VocabIndex,
    source: str,
    source_id: str,
    path: str,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for child_field, parent_field in _parent_field_pairs(index).items():
        child = payload.get(child_field)
        parent = _first_string(payload, parent_field)
        if not child or not parent or not isinstance(child, str) or not isinstance(parent, str):
            continue
        vocab_name = FIELD_TO_VOCAB[child_field]
        expected = index.parents.get(vocab_name, {}).get(child)
        if expected and expected != parent:
            issues.append(_issue(
                "blocking",
                "wrong_parent",
                source,
                source_id,
                f"{path}.{child_field}",
                child_field,
                child,
                f"{child_field} {child!r} belongs under {expected!r}, not {parent!r}",
                {"expected_parent": expected, "actual_parent": parent, "parent_field": parent_field},
            ))
    return issues


def _check_domain_rules(
    payload: dict[str, Any],
    index: VocabIndex,
    source: str,
    source_id: str,
    path: str,
) -> list[dict[str, Any]]:
    question_family = payload.get("question_family_key")
    is_reading = (
        question_family in index.reading_question_families
        or bool(payload.get("skill_family_key"))
        or bool(payload.get("reading_skill_family_key"))
        or bool(payload.get("reading_focus_key"))
    )
    grammar_fields = ("grammar_role_key", "grammar_focus_key", "target_grammar_role_key", "target_grammar_focus_key")
    reading_fields = (
        "skill_family_key",
        "reading_skill_family_key",
        "reading_focus_key",
        "target_reading_skill_family_key",
        "target_reading_focus_key",
    )
    if payload.get("grammar_role_key") or payload.get("grammar_focus_key"):
        if is_reading:
            return [_issue(
                "blocking",
                "domain_mismatch",
                source,
                source_id,
                path,
                "grammar_keys",
                None,
                "Reading-domain question sets grammar_role_key or grammar_focus_key",
            )]
    is_grammar = (
        (isinstance(question_family, str) and question_family and question_family not in index.reading_question_families)
        or any(payload.get(field) for field in grammar_fields)
    )
    if is_grammar and any(payload.get(field) for field in reading_fields):
        return [_issue(
            "blocking",
            "domain_mismatch",
            source,
            source_id,
            path,
            "reading_keys",
            None,
            "Grammar-domain question sets reading skill/focus keys",
        )]
    return []


def _check_reading_shape_rules(
    payload: dict[str, Any],
    index: VocabIndex,
    source: str,
    source_id: str,
    path: str,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    skill = payload.get("skill_family_key") or payload.get("reading_skill_family_key")
    focus = payload.get("reading_focus_key") or payload.get("target_reading_focus_key")
    if not skill and isinstance(focus, str):
        skill = index.parents.get("READING_FOCUS_BY_SKILL_FAMILY", {}).get(focus)
    if skill == "cross_text_connections":
        if payload.get("stimulus_mode_key") != "prose_paired" or not payload.get("paired_passage_text"):
            issues.append(_issue(
                "blocking",
                "cross_text_missing_prose_paired",
                source,
                source_id,
                path,
                "stimulus_mode_key",
                payload.get("stimulus_mode_key"),
                "Cross-Text item requires stimulus_mode_key='prose_paired' and paired_passage_text",
            ))
    if skill == "command_of_evidence_quantitative":
        has_graphic = bool(payload.get("table_data") or payload.get("graph_data") or payload.get("structured_data"))
        if payload.get("stimulus_mode_key") not in {"prose_plus_table", "prose_plus_graph"} or not has_graphic:
            issues.append(_issue(
                "blocking",
                "quantitative_missing_graphic_data",
                source,
                source_id,
                path,
                "graphic_data",
                None,
                "Quantitative evidence item requires table or graph stimulus data",
            ))
    return issues


def _values(raw: Any) -> list[str]:
    if isinstance(raw, str) and raw:
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str) and item]
    return []


def _issue(
    severity: str,
    code: str,
    source: str,
    source_id: str,
    path: str,
    field: str,
    value: Any,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "source": source,
        "source_id": source_id,
        "path": path,
        "field": field,
        "value": value,
        "message": message,
        "details": details or {},
    }


async def collect_db_records(session_factory: Any | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from sqlalchemy import select
    from app.models.db import QuestionAnnotation, QuestionJob, QuestionOption
    if session_factory is None:
        from app.database import async_session as session_factory

    records: list[dict[str, Any]] = []
    option_rows: list[dict[str, Any]] = []
    async with session_factory() as db:
        job_stream = await db.stream_scalars(select(QuestionJob).execution_options(yield_per=500))
        async for job in job_stream:
            records.extend([
                {"source": "question_jobs.pass1_json", "source_id": str(job.id), "payload": job.pass1_json},
                {"source": "question_jobs.pass2_json", "source_id": str(job.id), "payload": job.pass2_json},
                {
                    "source": "question_jobs.validation_errors_jsonb",
                    "source_id": str(job.id),
                    "payload": job.validation_errors_jsonb,
                },
            ])
        ann_stream = await db.stream_scalars(select(QuestionAnnotation).execution_options(yield_per=500))
        async for ann in ann_stream:
            records.extend([
                {"source": "question_annotations.annotation_jsonb", "source_id": str(ann.id), "payload": ann.annotation_jsonb},
                {"source": "question_annotations.explanation_jsonb", "source_id": str(ann.id), "payload": ann.explanation_jsonb},
                {
                    "source": "question_annotations.generation_profile_jsonb",
                    "source_id": str(ann.id),
                    "payload": ann.generation_profile_jsonb,
                },
            ])
        opt_stream = await db.stream_scalars(select(QuestionOption).execution_options(yield_per=1000))
        async for opt in opt_stream:
            option_rows.append({
                "id": str(opt.id),
                "question_id": str(opt.question_id),
                "distractor_type_key": opt.distractor_type_key,
                "plausibility_source_key": opt.plausibility_source_key,
                "student_failure_mode_key": opt.student_failure_mode_key,
                "distractor_distance": opt.distractor_distance,
            })
    return records, option_rows


def _parent_field_pairs(index: VocabIndex) -> dict[str, str]:
    pairs = dict(KNOWN_PARENT_FIELD_BY_CHILD_FIELD)
    for field, vocab_name in FIELD_TO_VOCAB.items():
        parent_set = index.parent_sets.get(vocab_name)
        if not parent_set:
            continue
        parent_fields = PARENT_ALIAS_FIELDS.get(parent_set, ())
        for parent_field in parent_fields:
            if parent_field in FIELD_TO_VOCAB:
                pairs.setdefault(field, parent_field)
                break
    return pairs


def _first_string(payload: dict[str, Any], field_or_fields: str | tuple[str, ...]) -> str | None:
    fields = (field_or_fields,) if isinstance(field_or_fields, str) else field_or_fields
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def collect_export_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.suffix.lower() in {".json", ".yaml", ".yml"}]
    for file_path in files:
        try:
            if file_path.suffix.lower() == ".json":
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            else:
                payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            records.append({
                "source": "exports",
                "source_id": str(file_path),
                "payload": {"export_parse_error": str(exc)},
            })
            continue
        records.append({"source": "exports", "source_id": str(file_path), "payload": payload})
    return records


async def run_scan(args) -> dict[str, Any]:
    index = load_vocab_index(args.master)
    records: list[dict[str, Any]] = []
    option_rows: list[dict[str, Any]] = []
    if args.all or args.db:
        db_records, db_option_rows = await collect_db_records()
        records.extend(db_records)
        option_rows.extend(db_option_rows)
    if args.all or args.exports:
        records.extend(collect_export_records(args.exports or DEFAULT_EXPORTS_PATH))
    issues = scan_records(records, index)
    issues.extend(scan_option_rows(option_rows, index))
    return report_summary(issues)


def exit_code_for_report(report: dict[str, Any], *, no_fail: bool) -> int:
    has_blocking = any(issue["severity"] == "blocking" for issue in report["issues"])
    return 0 if report["ok"] or (no_fail and not has_blocking) else 1


def print_human(report: dict[str, Any]) -> None:
    if report["ok"]:
        print("vocabulary consistency OK")
        return
    print(f"vocabulary consistency found {report['issue_count']} issue(s)")
    for issue in report["issues"]:
        print(
            f"[{issue['severity']}] {issue['code']} "
            f"{issue['source']}:{issue['source_id']} {issue['path']} - {issue['message']}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", help="scan DB JSONB and default exports path")
    scope.add_argument("--db", action="store_true", help="scan DB JSONB only")
    scope.add_argument("--exports", type=Path, help="scan generated JSON/YAML exports at a file or directory")
    parser.add_argument("--master", type=Path, default=MASTER_PATH, help="path to vocabulary/master.json")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON report")
    parser.add_argument("--no-fail", action="store_true", help="exit 0 for non-blocking issues; blocking issues still fail")
    args = parser.parse_args(argv)
    report = asyncio.run(run_scan(args))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)
    return exit_code_for_report(report, no_fail=args.no_fail)


if __name__ == "__main__":
    raise SystemExit(main())
