"""Tests for rule-document body patching from amendment files."""
from __future__ import annotations

from pathlib import Path
import json

from app.models.amendments import RuleAmendment
from app.pipeline import rule_doc_patcher


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "vocabulary" / "amendments" / "pending").mkdir(parents=True)
    (tmp_path / "vocabulary" / "amendments" / "needs_manual_patch").mkdir(parents=True)
    (tmp_path / "rules_agent_dsat_reading_v3.md").write_text(
        "\n".join([
            "# Reading Rules",
            "",
            "## Reading focus keys",
            "- `central_idea` - Existing central idea guidance.",
            "",
            "<!-- VOCAB:shared:STEM_TYPE_KEYS START -->",
            "- `generated_only`",
            "<!-- VOCAB:shared:STEM_TYPE_KEYS END -->",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "rules_agent_dsat_grammar_ingestion_generation_v8.md").write_text(
        "# Grammar Rules\n\n## Grammar taxonomy section\n- `agreement` - Existing.\n",
        encoding="utf-8",
    )
    return tmp_path


def _amendment(**overrides) -> RuleAmendment:
    payload = {
        "amendment_id": "amd-test",
        "source_job_id": "job-1",
        "source_exam_code": "PT04",
        "source_subject_code": "verbal",
        "source_section_code": "01",
        "source_module_code": "01",
        "source_question_number": 6,
        "content_origin": "official",
        "affected_doc": "reading",
        "proposal_type": "new_controlled_vocab_key",
        "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
        "proposed_value": "evidence_scope_shift",
        "parent_key": "information_and_ideas",
        "definition": "Evidence scope distinction.",
        "current_best_fit": "central_idea",
        "why_current_rules_are_insufficient": "Existing rules do not split evidence scope.",
        "official_evidence": "Official evidence.",
        "rule_doc_patch": {
            "target_section": "## Reading focus keys",
            "before": "- `central_idea` - Existing central idea guidance.",
            "after": "- `central_idea` - Existing central idea guidance.\n- `evidence_scope_shift` - Evidence scope distinction.",
            "rationale": "Official evidence requires it.",
        },
        "master_json_patch": {
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": "evidence_scope_shift",
            "parent_key": "information_and_ideas",
            "description": "Evidence scope distinction.",
        },
        "supporting_examples": [{
            "source_job_id": "job-1",
            "source_exam_code": "PT04",
            "source_subject_code": "verbal",
            "source_section_code": "01",
            "source_module_code": "01",
            "source_question_number": 6,
            "official_evidence": "Official evidence.",
        }],
    }
    payload.update(overrides)
    return RuleAmendment.model_validate(payload)


def _write_amendment(path: Path, amendment: RuleAmendment) -> Path:
    path.write_text(json.dumps(amendment.to_file_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def _write_master(repo: Path, amendment: RuleAmendment) -> None:
    master = {
        "schema_version": 1,
        "vocabularies": [{
            "name": amendment.affected_vocab,
            "kind": "hierarchical" if amendment.parent_key else "flat",
            "entries": [{
                "value": amendment.proposed_value,
                "parent": amendment.parent_key,
                "status": "active",
                "added": "2026-05-18",
                "description": amendment.definition,
            }],
        }],
    }
    (repo / "vocabulary" / "master.json").write_text(
        json.dumps(master, indent=2) + "\n",
        encoding="utf-8",
    )


def test_dry_run_rule_doc_patch_returns_body_diff(tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment()

    result = rule_doc_patcher.dry_run_rule_doc_patch(amendment, repo_root=repo)

    assert result.ok is True
    assert "evidence_scope_shift" in result.diff
    assert (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8").count("evidence_scope_shift") == 0


def test_apply_rule_doc_patch_updates_body_without_regenerating_by_default(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    amendment_path = _write_amendment(
        repo / "vocabulary" / "amendments" / "pending" / "amd-test.json",
        _amendment(),
    )
    calls = []

    def fake_regenerate(*, repo_root):
        calls.append(repo_root)
        return rule_doc_patcher.RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr(rule_doc_patcher, "regenerate_vocab_appendices", fake_regenerate)

    result = rule_doc_patcher.apply_rule_doc_patch(amendment_path, repo_root=repo)

    assert result.ok is True
    assert calls == []
    text = (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")
    assert "`evidence_scope_shift`" in text


def test_apply_rule_doc_patch_regenerates_only_after_master_json_contains_value(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment()
    _write_master(repo, amendment)
    amendment_path = _write_amendment(
        repo / "vocabulary" / "amendments" / "pending" / "amd-test.json",
        amendment,
    )
    calls = []

    def fake_regenerate(*, repo_root):
        calls.append(repo_root)
        return rule_doc_patcher.RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr(rule_doc_patcher, "regenerate_vocab_appendices", fake_regenerate)

    result = rule_doc_patcher.apply_rule_doc_patch(
        amendment_path,
        repo_root=repo,
        regenerate_appendix=True,
    )

    assert result.ok is True
    assert calls == [repo]


def test_apply_rule_doc_patch_rejects_regeneration_before_master_json_promotion(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    amendment_path = _write_amendment(
        repo / "vocabulary" / "amendments" / "pending" / "amd-test.json",
        _amendment(),
    )
    calls = []

    def fake_regenerate(*, repo_root):
        calls.append(repo_root)
        return rule_doc_patcher.RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr(rule_doc_patcher, "regenerate_vocab_appendices", fake_regenerate)

    result = rule_doc_patcher.apply_rule_doc_patch(
        amendment_path,
        repo_root=repo,
        regenerate_appendix=True,
    )

    assert result.ok is False
    assert "before amendment value is active in master.json" in result.error
    assert calls == []
    assert "`evidence_scope_shift`" not in (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")
    assert not amendment_path.exists()


def test_rule_doc_patch_rejects_generated_vocab_block_target(tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment(
        rule_doc_patch={
            "target_section": "## Reading focus keys",
            "before": "- `generated_only`",
            "after": "- `new_generated_only`",
            "rationale": "Should not patch generated blocks.",
        }
    )

    result = rule_doc_patcher.dry_run_rule_doc_patch(amendment, repo_root=repo)

    assert result.ok is False
    assert "generated VOCAB appendix" in result.error


def test_rule_doc_patch_allows_anchor_immediately_after_generated_vocab_end_marker(tmp_path):
    repo = _repo(tmp_path)
    (repo / "rules_agent_dsat_reading_v3.md").write_text(
        "\n".join([
            "# Reading Rules",
            "",
            "## Reading focus keys",
            "<!-- VOCAB:shared:STEM_TYPE_KEYS START -->",
            "- `generated_only`",
            "<!-- VOCAB:shared:STEM_TYPE_KEYS END -->- `safe_after_end` - Editable body text.",
            "",
        ]),
        encoding="utf-8",
    )
    amendment = _amendment(
        rule_doc_patch={
            "target_section": "## Reading focus keys",
            "before": "- `safe_after_end` - Editable body text.",
            "after": "- `safe_after_end` - Editable body text.\n- `evidence_scope_shift` - Evidence scope distinction.",
            "rationale": "Anchor is outside the generated block.",
        }
    )

    result = rule_doc_patcher.dry_run_rule_doc_patch(amendment, repo_root=repo)

    assert result.ok is True


def test_rule_doc_patch_rejects_ambiguous_before_anchor(tmp_path):
    repo = _repo(tmp_path)
    (repo / "rules_agent_dsat_reading_v3.md").write_text(
        "\n".join([
            "# Reading Rules",
            "",
            "## Reading focus keys",
            "- `central_idea` - Existing central idea guidance.",
            "- `central_idea` - Existing central idea guidance.",
            "",
        ]),
        encoding="utf-8",
    )
    amendment = _amendment()

    result = rule_doc_patcher.dry_run_rule_doc_patch(amendment, repo_root=repo)

    assert result.ok is False
    assert "ambiguous" in result.error


def test_apply_rule_doc_patch_rejects_missing_doc_path_result(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    amendment_path = _write_amendment(
        repo / "vocabulary" / "amendments" / "pending" / "amd-test.json",
        _amendment(),
    )

    def fake_build_patch_result(amendment, *, repo_root):
        return rule_doc_patcher.RuleDocPatchResult(
            ok=True,
            amendment_id=amendment.amendment_id,
            affected_doc=str(amendment.affected_doc),
            doc_path=None,
        )

    monkeypatch.setattr(rule_doc_patcher, "_build_patch_result", fake_build_patch_result)

    result = rule_doc_patcher.apply_rule_doc_patch(amendment_path, repo_root=repo)

    assert result.ok is False
    assert "without a resolved document path" in result.error
    assert not amendment_path.exists()


def test_patch_failure_marks_amendment_needs_manual_patch(tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment(
        rule_doc_patch={
            "target_section": "## Reading focus keys",
            "before": "- `missing_anchor`",
            "after": "- `missing_anchor`\n- `evidence_scope_shift`",
            "rationale": "Anchor missing.",
        }
    )
    amendment_path = _write_amendment(
        repo / "vocabulary" / "amendments" / "pending" / "amd-test.json",
        amendment,
    )

    result = rule_doc_patcher.apply_rule_doc_patch(amendment_path, repo_root=repo)

    assert result.ok is False
    assert not amendment_path.exists()
    moved = repo / "vocabulary" / "amendments" / "needs_manual_patch" / "amd-test.json"
    saved = json.loads(moved.read_text(encoding="utf-8"))
    assert saved["status"] == "needs_manual_patch"
    assert "rule_doc_patch_failure" in saved["review_notes"][0]


def test_patch_rejects_missing_target_section(tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment(
        rule_doc_patch={
            "target_section": "## Missing section",
            "before": "- `central_idea` - Existing central idea guidance.",
            "after": "- `central_idea` - Existing central idea guidance.\n- `evidence_scope_shift` - Evidence scope distinction.",
            "rationale": "Wrong section.",
        }
    )

    result = rule_doc_patcher.dry_run_rule_doc_patch(amendment, repo_root=repo)

    assert result.ok is False
    assert "target_section was not found" in result.error
