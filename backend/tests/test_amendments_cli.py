"""Tests for local development amendment CLI commands."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.models.amendments import RuleAmendment
from app.pipeline.rule_doc_patcher import RuleDocPatchResult

REPO_ROOT = Path(__file__).resolve().parents[2]
AMENDMENTS_CLI = REPO_ROOT / "scripts" / "amendments.py"
GEN_VOCAB = REPO_ROOT / "scripts" / "gen_vocab.py"


def _load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path) -> Path:
    for name in ("pending", "approved", "rejected", "needs_manual_patch"):
        (tmp_path / "vocabulary" / "amendments" / name).mkdir(parents=True)
    (tmp_path / "rules_agent_dsat_reading_v3.md").write_text(
        "\n".join([
            "# Reading Rules",
            "",
            "## Reading focus keys",
            "- `central_idea` - Existing central idea guidance.",
            "",
            "<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY START -->",
            "- `central_idea`",
            "<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY END -->",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "rules_agent_dsat_grammar_ingestion_generation_v8.md").write_text("# Grammar Rules\n")
    master = {
        "schema_version": 1,
        "vocabularies": [
            {
                "name": "READING_SKILL_FAMILY_KEYS",
                "kind": "flat",
                "entries": [{"value": "information_and_ideas", "status": "active"}],
            },
            {
                "name": "READING_FOCUS_BY_SKILL_FAMILY",
                "kind": "hierarchical",
                "parent_set": "READING_SKILL_FAMILY_KEYS",
                "entries": [{
                    "value": "central_idea",
                    "parent": "information_and_ideas",
                    "status": "active",
                }],
            },
        ],
    }
    (tmp_path / "vocabulary" / "master.json").write_text(json.dumps(master, indent=2) + "\n")
    (tmp_path / "vocabulary" / "candidates.json").write_text(
        json.dumps({"schema_version": 1, "candidates": []}, indent=2) + "\n",
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


def _write(repo: Path, directory: str, amendment: RuleAmendment) -> None:
    path = repo / "vocabulary" / "amendments" / directory / f"{amendment.amendment_id}.json"
    path.write_text(json.dumps(amendment.to_file_dict(), indent=2) + "\n", encoding="utf-8")


def test_amendments_cli_list_and_show(tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    assert cli.main(["--repo-root", str(repo), "list"]) == 0
    assert "amd-test" in capsys.readouterr().out

    assert cli.main(["--repo-root", str(repo), "show", "amd-test"]) == 0
    assert '"status": "pending"' in capsys.readouterr().out


def test_amendments_cli_request_more_evidence(tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    assert cli.main(["--repo-root", str(repo), "request-more-evidence", "amd-test"]) == 0
    assert '"status": "more_evidence_requested"' in capsys.readouterr().out


def test_amendments_cli_approve(tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    assert cli.main(["--repo-root", str(repo), "approve", "amd-test"]) == 0
    assert '"status": "approved"' in capsys.readouterr().out


def test_amendments_cli_reject(tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    assert cli.main(["--repo-root", str(repo), "reject", "amd-test"]) == 0
    assert '"status": "rejected"' in capsys.readouterr().out


def test_amendments_cli_blocks_unapproved_promotion(tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    assert cli.main(["--repo-root", str(repo), "promote", "amd-test"]) == 1

    assert "approved before promotion" in capsys.readouterr().err


def test_amendments_cli_promotes_approved_amendment(monkeypatch, tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment(status="approved"))
    cli = _load_script(AMENDMENTS_CLI, "amendments_cli_under_test")

    def fake_regenerate(*, repo_root):
        return RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr("app.pipeline.rule_doc_patcher.regenerate_vocab_appendices", fake_regenerate)

    assert cli.main(["--repo-root", str(repo), "promote", "amd-test"]) == 0

    assert '"status": "promoted"' in capsys.readouterr().out
    master = json.loads((repo / "vocabulary" / "master.json").read_text(encoding="utf-8"))
    focus = next(item for item in master["vocabularies"] if item["name"] == "READING_FOCUS_BY_SKILL_FAMILY")
    assert any(entry["value"] == "evidence_scope_shift" for entry in focus["entries"])


def test_gen_vocab_promote_from_amendment_uses_gated_workflow(monkeypatch, tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment(status="approved"))
    gen_vocab = _load_script(GEN_VOCAB, "gen_vocab_under_test_phase5")
    monkeypatch.setattr(gen_vocab, "REPO_ROOT", repo)
    # Also pin amendment_review.REPO_ROOT so the test fails loudly if
    # cmd_promote_from_amendment ever stops forwarding repo_root and the
    # promotion falls back to the module-level default.
    from app.pipeline import amendment_review
    monkeypatch.setattr(amendment_review, "REPO_ROOT", repo)

    def fake_regenerate(*, repo_root):
        return RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr("app.pipeline.rule_doc_patcher.regenerate_vocab_appendices", fake_regenerate)
    args = type("Args", (), {
        "promote_from_amendment": "amd-test",
        "repo_root": repo,
        "reviewer": "tester",
        "notes": "ok",
    })()

    assert gen_vocab.cmd_promote_from_amendment(args) == 0

    out = capsys.readouterr().out
    assert "promoted amendment amd-test" in out
    assert "regenerated ontology.py and VOCAB appendices" in out


def test_gen_vocab_promote_from_amendment_blocks_unapproved(monkeypatch, tmp_path, capsys):
    repo = _repo(tmp_path)
    _write(repo, "pending", _amendment())
    gen_vocab = _load_script(GEN_VOCAB, "gen_vocab_under_test_phase5")
    monkeypatch.setattr(gen_vocab, "REPO_ROOT", repo)
    args = type("Args", (), {
        "promote_from_amendment": "amd-test",
        "repo_root": repo,
        "reviewer": "tester",
        "notes": "ok",
    })()

    assert gen_vocab.cmd_promote_from_amendment(args) == 1

    assert "approved before promotion" in capsys.readouterr().err
