"""Tests for vocabulary consistency scanner."""
from __future__ import annotations

import importlib.util
import asyncio
import json
import sys
from types import SimpleNamespace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER = REPO_ROOT / "scripts" / "check_vocab_consistency.py"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("check_vocab_consistency_under_test", SCANNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _master(path: Path) -> Path:
    data = {
        "schema_version": 1,
        "vocabularies": [
            {
                "name": "QUESTION_FAMILY_KEYS",
                "kind": "flat",
                "entries": [
                    {"value": "information_and_ideas", "status": "active"},
                    {"value": "standard_english_conventions", "status": "active"},
                ],
            },
            {
                "name": "READING_QUESTION_FAMILY_KEYS",
                "kind": "flat",
                "entries": [{"value": "information_and_ideas", "status": "active"}],
            },
            {
                "name": "READING_SKILL_FAMILY_KEYS",
                "kind": "flat",
                "entries": [
                    {"value": "command_of_evidence_textual", "status": "active"},
                    {"value": "command_of_evidence_quantitative", "status": "active"},
                    {"value": "cross_text_connections", "status": "active"},
                ],
            },
            {
                "name": "READING_FOCUS_BY_SKILL_FAMILY",
                "kind": "hierarchical",
                "entries": [
                    {
                        "value": "evidence_supports_claim",
                        "parent": "command_of_evidence_textual",
                        "status": "active",
                    },
                    {
                        "value": "data_supports_claim",
                        "parent": "command_of_evidence_quantitative",
                        "status": "active",
                    },
                    {
                        "value": "text2_response_to_text1",
                        "parent": "cross_text_connections",
                        "status": "active",
                    },
                ],
            },
            {
                "name": "GRAMMAR_ROLE_KEYS",
                "kind": "flat",
                "entries": [{"value": "boundaries", "status": "active"}],
            },
            {
                "name": "GRAMMAR_FOCUS_BY_ROLE",
                "kind": "hierarchical",
                "entries": [
                    {"value": "comma_splice", "parent": "boundaries", "status": "active"},
                    {"value": "old_focus", "parent": "boundaries", "status": "deprecated"},
                ],
            },
            {
                "name": "STIMULUS_MODE_KEYS",
                "kind": "flat",
                "entries": [
                    {"value": "prose", "status": "active"},
                    {"value": "prose_paired", "status": "active"},
                    {"value": "prose_plus_table", "status": "active"},
                    {"value": "prose_plus_graph", "status": "active"},
                ],
            },
            {
                "name": "STEM_TYPE_KEYS",
                "kind": "flat",
                "entries": [{"value": "main_idea", "status": "active"}],
            },
            {
                "name": "DISTRACTOR_TYPE_KEYS",
                "kind": "flat",
                "entries": [{"value": "opposite", "status": "active"}],
            },
            {
                "name": "PLAUSIBILITY_SOURCE_KEYS",
                "kind": "flat",
                "entries": [{"value": "surface_match", "status": "active"}],
            },
            {
                "name": "STUDENT_FAILURE_MODE_KEYS",
                "kind": "flat",
                "entries": [{"value": "scope_error", "status": "active"}],
            },
            {
                "name": "DISTRACTOR_DISTANCE_KEYS",
                "kind": "flat",
                "entries": [{"value": "near", "status": "active"}],
            },
            {
                "name": "CUSTOM_PARENT_KEYS",
                "kind": "flat",
                "entries": [{"value": "parent_a", "status": "active"}],
            },
            {
                "name": "CUSTOM_FOCUS_BY_PARENT",
                "kind": "hierarchical",
                "parent_set": "CUSTOM_PARENT_KEYS",
                "entries": [{"value": "child_a", "parent": "parent_a", "status": "active"}],
            },
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _codes(issues):
    return {issue["code"] for issue in issues}


def test_scanner_reports_unknown_deprecated_wrong_parent_domain_and_shape_errors(tmp_path):
    scanner = _load_scanner()
    index = scanner.load_vocab_index(_master(tmp_path / "master.json"))
    records = [
        {
            "source": "question_jobs.pass1_json",
            "source_id": "job-unknown",
            "payload": {"stem_type_key": "missing_stem"},
        },
        {
            "source": "question_jobs.pass2_json",
            "source_id": "job-deprecated",
            "payload": {"grammar_role_key": "boundaries", "grammar_focus_key": "old_focus"},
        },
        {
            "source": "question_annotations.annotation_jsonb",
            "source_id": "ann-parent",
            "payload": {
                "skill_family_key": "cross_text_connections",
                "reading_focus_key": "evidence_supports_claim",
            },
        },
        {
            "source": "question_annotations.annotation_jsonb",
            "source_id": "ann-domain",
            "payload": {
                "question_family_key": "information_and_ideas",
                "skill_family_key": "command_of_evidence_textual",
                "reading_focus_key": "evidence_supports_claim",
                "grammar_role_key": "boundaries",
            },
        },
        {
            "source": "question_jobs.pass2_json",
            "source_id": "job-cross",
            "payload": {
                "reading_skill_family_key": "cross_text_connections",
                "reading_focus_key": "text2_response_to_text1",
                "stimulus_mode_key": "prose",
            },
        },
        {
            "source": "question_jobs.pass2_json",
            "source_id": "job-quant",
            "payload": {
                "reading_skill_family_key": "command_of_evidence_quantitative",
                "reading_focus_key": "data_supports_claim",
                "stimulus_mode_key": "prose",
            },
        },
        {
            "source": "question_annotations.annotation_jsonb",
            "source_id": "ann-reverse-domain",
            "payload": {
                "question_family_key": "standard_english_conventions",
                "reading_focus_key": "evidence_supports_claim",
            },
        },
    ]

    issues = scanner.scan_records(records, index)

    assert {
        "unknown_key",
        "deprecated_key",
        "wrong_parent",
        "domain_mismatch",
        "cross_text_missing_prose_paired",
        "quantitative_missing_graphic_data",
    }.issubset(_codes(issues))


def test_shared_field_mapping_stays_in_sync():
    from app.models.vocab_fields import BASE_FIELD_TO_VOCAB
    from app.models import vocab_candidates
    from app.pipeline import amendments

    assert vocab_candidates.FIELD_TO_VOCAB is BASE_FIELD_TO_VOCAB
    assert amendments.FIELD_TO_VOCAB is BASE_FIELD_TO_VOCAB


def test_scanner_parent_rules_are_derived_for_hierarchical_vocabularies(tmp_path, monkeypatch):
    scanner = _load_scanner()
    monkeypatch.setitem(scanner.FIELD_TO_VOCAB, "custom_parent_key", "CUSTOM_PARENT_KEYS")
    monkeypatch.setitem(scanner.FIELD_TO_VOCAB, "custom_focus_key", "CUSTOM_FOCUS_BY_PARENT")
    monkeypatch.setitem(scanner.PARENT_ALIAS_FIELDS, "CUSTOM_PARENT_KEYS", ("custom_parent_key",))
    index = scanner.load_vocab_index(_master(tmp_path / "master.json"))

    issues = scanner.scan_records([
        {
            "source": "exports",
            "source_id": "custom.json",
            "payload": {"custom_parent_key": "wrong_parent", "custom_focus_key": "child_a"},
        }
    ], index)

    assert "wrong_parent" in _codes(issues)


def test_scanner_reports_question_option_vocab_errors(tmp_path):
    scanner = _load_scanner()
    index = scanner.load_vocab_index(_master(tmp_path / "master.json"))

    issues = scanner.scan_option_rows([
        {
            "id": "opt-1",
            "distractor_type_key": "not_real",
            "student_failure_mode_key": "scope_error",
        }
    ], index)

    assert any(issue["source"] == "question_options" and issue["field"] == "distractor_type_key" for issue in issues)


def test_scanner_json_report_is_machine_readable(tmp_path):
    scanner = _load_scanner()
    index = scanner.load_vocab_index(_master(tmp_path / "master.json"))

    report = scanner.report_summary(scanner.scan_records([
        {"source": "exports", "source_id": "x.json", "payload": {"stem_type_key": "missing"}}
    ], index))

    assert report["ok"] is False
    assert report["counts_by_code"]["unknown_key"] == 1
    json.dumps(report)


def test_exit_code_no_fail_still_fails_on_blocking_issues(tmp_path):
    scanner = _load_scanner()
    review_report = {
        "ok": False,
        "issues": [{"severity": "review", "code": "unknown_key"}],
    }
    blocking_report = {
        "ok": False,
        "issues": [{"severity": "blocking", "code": "domain_mismatch"}],
    }

    assert scanner.exit_code_for_report(review_report, no_fail=True) == 0
    assert scanner.exit_code_for_report(blocking_report, no_fail=True) == 1


def test_collect_export_records_reads_json_and_yaml(tmp_path):
    scanner = _load_scanner()
    (tmp_path / "one.json").write_text(json.dumps({"stem_type_key": "main_idea"}), encoding="utf-8")
    (tmp_path / "two.yaml").write_text("stem_type_key: missing\n", encoding="utf-8")

    records = scanner.collect_export_records(tmp_path)

    assert {record["source_id"] for record in records} == {
        str(tmp_path / "one.json"),
        str(tmp_path / "two.yaml"),
    }


def test_collect_db_records_streams_rows_from_async_session():
    scanner = _load_scanner()

    class AsyncStream:
        def __init__(self, rows):
            self.rows = rows

        def __aiter__(self):
            self._iter = iter(self.rows)
            return self

        async def __anext__(self):
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def stream_scalars(self, stmt):
            text = str(stmt)
            if "question_jobs" in text:
                return AsyncStream([
                    SimpleNamespace(
                        id="job-1",
                        pass1_json={"stem_type_key": "missing"},
                        pass2_json=None,
                        validation_errors_jsonb=None,
                    )
                ])
            if "question_annotations" in text:
                return AsyncStream([
                    SimpleNamespace(
                        id="ann-1",
                        annotation_jsonb={"grammar_focus_key": "comma_splice"},
                        explanation_jsonb={},
                        generation_profile_jsonb=None,
                    )
                ])
            if "question_options" in text:
                return AsyncStream([
                    SimpleNamespace(
                        id="opt-1",
                        question_id="q-1",
                        distractor_type_key="not_real",
                        plausibility_source_key=None,
                        student_failure_mode_key=None,
                        distractor_distance=None,
                    )
                ])
            return AsyncStream([])

    def fake_session_factory():
        return FakeSession()

    records, option_rows = asyncio.run(scanner.collect_db_records(fake_session_factory))

    assert any(record["source"] == "question_jobs.pass1_json" for record in records)
    assert any(record["source"] == "question_annotations.annotation_jsonb" for record in records)
    assert option_rows[0]["id"] == "opt-1"
