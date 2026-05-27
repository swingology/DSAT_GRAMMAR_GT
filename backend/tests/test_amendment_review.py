"""Tests for admin amendment review and promotion operations."""
from __future__ import annotations

import json
from pathlib import Path

from types import SimpleNamespace

from app.models.amendments import RuleAmendment
from app.pipeline import amendment_review
from app.pipeline.rule_doc_patcher import RuleDocPatchResult


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
    (tmp_path / "rules_agent_dsat_grammar_ingestion_generation_v8.md").write_text(
        "# Grammar Rules\n",
        encoding="utf-8",
    )
    master = {
        "schema_version": 1,
        "vocabularies": [
            {
                "name": "READING_SKILL_FAMILY_KEYS",
                "kind": "flat",
                "entries": [{
                    "value": "information_and_ideas",
                    "status": "active",
                    "added": "2026-05-18",
                    "description": "",
                }],
            },
            {
                "name": "READING_FOCUS_BY_SKILL_FAMILY",
                "kind": "hierarchical",
                "parent_set": "READING_SKILL_FAMILY_KEYS",
                "entries": [{
                    "value": "central_idea",
                    "parent": "information_and_ideas",
                    "status": "active",
                    "added": "2026-05-18",
                    "description": "",
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


def _write_pending(repo: Path, amendment: RuleAmendment) -> Path:
    path = repo / "vocabulary" / "amendments" / "pending" / f"{amendment.amendment_id}.json"
    path.write_text(json.dumps(amendment.to_file_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def _write_amendment(repo: Path, directory: str, amendment: RuleAmendment) -> Path:
    path = repo / "vocabulary" / "amendments" / directory / f"{amendment.amendment_id}.json"
    path.write_text(json.dumps(amendment.to_file_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def test_approve_validates_patch_and_links_or_creates_candidate(tmp_path):
    repo = _repo(tmp_path)
    _write_pending(repo, _amendment())

    result = amendment_review.approve_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is True
    assert result.amendment is not None
    assert result.amendment.status == "approved"
    candidates = json.loads((repo / "vocabulary" / "candidates.json").read_text(encoding="utf-8"))
    assert candidates["candidates"][0]["amendment_ids"] == ["amd-test"]


def test_approve_rejects_invalid_status_transition(tmp_path):
    repo = _repo(tmp_path)
    _write_amendment(repo, "rejected", _amendment(status="rejected"))

    result = amendment_review.approve_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "Cannot approve" in result.error


def test_reject_moves_file_and_updates_status(tmp_path):
    repo = _repo(tmp_path)
    pending = _write_pending(repo, _amendment())

    result = amendment_review.reject_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is True
    assert result.amendment is not None
    assert result.amendment.status == "rejected"
    assert not pending.exists()
    assert (repo / "vocabulary" / "amendments" / "rejected" / "amd-test.json").exists()


def test_reject_blocks_promoted_amendment(tmp_path):
    repo = _repo(tmp_path)
    _write_amendment(repo, "approved", _amendment(status="promoted"))

    result = amendment_review.reject_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "Cannot reject" in result.error


def test_request_more_evidence_updates_pending_file(tmp_path):
    repo = _repo(tmp_path)
    _write_pending(repo, _amendment())

    result = amendment_review.request_more_evidence("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is True
    assert result.amendment is not None
    assert result.amendment.status == "more_evidence_requested"


def test_request_more_evidence_rejects_invalid_status_transition(tmp_path):
    repo = _repo(tmp_path)
    _write_pending(repo, _amendment(status="approved"))

    result = amendment_review.request_more_evidence("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "Cannot request_more_evidence" in result.error


def test_promote_patches_doc_updates_master_regenerates_and_moves_file(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    amendment = _amendment(status="approved")
    pending = _write_pending(repo, amendment)
    calls = []
    reappraisal_calls = []

    def fake_regenerate(*, repo_root):
        # Regeneration only runs after master.json + the doc body have been
        # updated; verify the regeneration would see the new vocab entry.
        calls.append(repo_root)
        master_at_call = json.loads(
            (repo_root / "vocabulary" / "master.json").read_text(encoding="utf-8")
        )
        focus_at_call = next(
            v for v in master_at_call["vocabularies"]
            if v["name"] == "READING_FOCUS_BY_SKILL_FAMILY"
        )
        assert any(e["value"] == "evidence_scope_shift" for e in focus_at_call["entries"])
        doc_at_call = (repo_root / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")
        assert "`evidence_scope_shift` - Evidence scope distinction." in doc_at_call
        return RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None)

    monkeypatch.setattr("app.pipeline.rule_doc_patcher.regenerate_vocab_appendices", fake_regenerate)
    monkeypatch.setattr(
        "app.pipeline.ingestion_analysis.write_reappraisals_for_master_growth",
        lambda *, repo_root: reappraisal_calls.append(repo_root),
    )

    result = amendment_review.promote_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is True
    assert result.amendment is not None
    assert result.amendment.status == "promoted"
    assert not pending.exists()
    promoted_path = repo / "vocabulary" / "amendments" / "approved" / "amd-test.json"
    assert promoted_path.exists()
    assert "`evidence_scope_shift`" in (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")
    master = json.loads((repo / "vocabulary" / "master.json").read_text(encoding="utf-8"))
    focus = next(item for item in master["vocabularies"] if item["name"] == "READING_FOCUS_BY_SKILL_FAMILY")
    new_entry = next(e for e in focus["entries"] if e["value"] == "evidence_scope_shift")
    assert new_entry["status"] == "active"
    assert new_entry["parent"] == "information_and_ideas"
    assert new_entry["description"] == "Evidence scope distinction."
    # Promoted amendment file records the promotion in its status + review_notes.
    promoted = json.loads(promoted_path.read_text(encoding="utf-8"))
    assert promoted["status"] == "promoted"
    assert any('"type": "promotion"' in note for note in promoted.get("review_notes", []))
    # Candidate row dropped once the amendment is promoted into master.json.
    candidates = json.loads((repo / "vocabulary" / "candidates.json").read_text(encoding="utf-8"))
    assert not any(
        row.get("value") == "evidence_scope_shift" for row in candidates["candidates"]
    )
    assert calls == [repo]
    assert reappraisal_calls == [repo]


def test_promote_restores_master_and_doc_when_regeneration_fails(monkeypatch, tmp_path):
    repo = _repo(tmp_path)
    pending = _write_pending(repo, _amendment(status="approved"))
    master_before = (repo / "vocabulary" / "master.json").read_text(encoding="utf-8")
    doc_before = (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")

    def fake_regenerate(*, repo_root):
        return RuleDocPatchResult(
            ok=False,
            amendment_id="",
            affected_doc="",
            doc_path=None,
            error="regeneration failed",
            conflict_details={"step": "regenerate_vocab_appendices"},
        )

    monkeypatch.setattr("app.pipeline.rule_doc_patcher.regenerate_vocab_appendices", fake_regenerate)

    result = amendment_review.promote_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert result.error == "regeneration failed"
    # master.json and the rule doc are rolled back to their pre-promotion state.
    assert (repo / "vocabulary" / "master.json").read_text(encoding="utf-8") == master_before
    assert (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8") == doc_before
    # Amendment file state: regeneration failure routes the file to
    # needs_manual_patch (it is no longer in pending or promoted to approved).
    assert not pending.exists()
    assert not (repo / "vocabulary" / "amendments" / "approved" / "amd-test.json").exists()
    manual = repo / "vocabulary" / "amendments" / "needs_manual_patch" / "amd-test.json"
    assert manual.exists()
    manual_data = json.loads(manual.read_text(encoding="utf-8"))
    assert manual_data["status"] == "needs_manual_patch"
    assert any(
        '"type": "rule_doc_patch_failure"' in note
        for note in manual_data.get("review_notes", [])
    )


def test_promote_rejects_unapproved_amendment(tmp_path):
    repo = _repo(tmp_path)
    _write_pending(repo, _amendment())

    result = amendment_review.promote_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "approved before promotion" in result.error


def test_promote_rejects_approved_file_outside_pending_directory(tmp_path):
    repo = _repo(tmp_path)
    _write_amendment(repo, "rejected", _amendment(status="approved"))

    result = amendment_review.promote_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "pending review directory" in result.error


def test_capture_approve_promote_reappraisal_end_to_end(monkeypatch, tmp_path):
    """Full pipeline: capture proposal -> approve -> promote -> re-appraisal.

    Each step has unit coverage; this test verifies they compose - the captured
    pending file is approvable, promotable, and that promotion triggers a real
    re-appraisal report when a prior analysis carries an older master hash.
    """
    from app.pipeline import amendments as amendments_mod

    repo = _repo(tmp_path)

    # A prior analysis report pinned to the pre-promotion master.json hash.
    analysis_dir = repo / "analysis" / "ingestion" / "PT04" / "run_old"
    analysis_dir.mkdir(parents=True)
    (analysis_dir / "taxonomy_coverage.json").write_text(
        json.dumps({
            "hashes": {"master_json_hash": "stale-hash-from-an-earlier-run"},
            "coverage": {},
        }, indent=2),
        encoding="utf-8",
    )

    job = SimpleNamespace(
        id="job-e2e",
        job_type="ingest",
        content_origin="official",
        status="needs_review",
        pass1_json=None,
        pass2_json=None,
        validation_errors_jsonb=None,
        source_exam_code="PT04",
        source_subject_code="verbal",
        source_section_code="01",
        source_module_code="01",
    )
    q_data = {
        "source_exam_code": "PT04",
        "source_subject_code": "verbal",
        "source_section_code": "01",
        "source_module_code": "01",
        "source_question_number": 6,
        "question_text": "Official evidence text.",
        "skill_family_key": "information_and_ideas",
    }
    proposal = {
        "affected_doc": "reading",
        "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
        "proposed_value": "evidence_scope_shift",
        "parent_key": "information_and_ideas",
        "definition": "Evidence scope distinction.",
        "current_best_fit": "central_idea",
        "why_current_rules_are_insufficient": "Current rules do not separate evidence scope.",
        "official_evidence": "Exact official evidence.",
        "rule_doc_patch": {
            "target_section": "## Reading focus keys",
            "before": "- `central_idea` - Existing central idea guidance.",
            "after": (
                "- `central_idea` - Existing central idea guidance.\n"
                "- `evidence_scope_shift` - Evidence scope distinction."
            ),
            "rationale": "Official evidence requires it.",
        },
        "master_json_patch": {
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": "evidence_scope_shift",
            "parent_key": "information_and_ideas",
            "description": "Evidence scope distinction.",
        },
    }

    # gen_vocab regeneration shells out; stub only that external step so the
    # rest of the pipeline runs for real.
    monkeypatch.setattr(
        "app.pipeline.rule_doc_patcher.regenerate_vocab_appendices",
        lambda *, repo_root: RuleDocPatchResult(
            ok=True, amendment_id="", affected_doc="", doc_path=None),
    )

    # Step 1: capture the proposal into a pending amendment file.
    pending_dir = repo / "vocabulary" / "amendments" / "pending"
    candidates_path = repo / "vocabulary" / "candidates.json"
    captured = amendments_mod.capture_amendment_proposal(
        job=job,
        q_data=q_data,
        annotate_json={"reasoning": {"amendment_proposal": proposal}},
        pending_dir=pending_dir,
        candidates_path=candidates_path,
    )
    assert captured is not None
    amendment_id = captured.amendment_id
    assert (pending_dir / f"{amendment_id}.json").exists()

    # Step 2: approve.
    approved = amendment_review.approve_amendment(amendment_id, reviewer="tester", repo_root=repo)
    assert approved.ok is True
    assert approved.amendment.status == "approved"

    # Step 3 + 4: promote (which triggers write_reappraisals_for_master_growth).
    promoted = amendment_review.promote_amendment(amendment_id, reviewer="tester", repo_root=repo)
    assert promoted.ok is True
    assert promoted.amendment.status == "promoted"

    master = json.loads((repo / "vocabulary" / "master.json").read_text(encoding="utf-8"))
    focus = next(v for v in master["vocabularies"] if v["name"] == "READING_FOCUS_BY_SKILL_FAMILY")
    assert any(e["value"] == "evidence_scope_shift" for e in focus["entries"])

    # Step 4 verification: the stale prior analysis got a re-appraisal report
    # named for the new master.json hash.
    reappraisals = list(analysis_dir.glob("reappraisal_*.md"))
    assert len(reappraisals) == 1, f"expected one re-appraisal report, got {reappraisals}"


def test_approve_rejects_already_active_key(tmp_path):
    repo = _repo(tmp_path)
    _write_pending(repo, _amendment(
        proposed_value="central_idea",
        master_json_patch={
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": "central_idea",
            "parent_key": "information_and_ideas",
            "description": "Central idea.",
        },
    ))

    result = amendment_review.approve_amendment("amd-test", reviewer="tester", repo_root=repo)

    assert result.ok is False
    assert "already active" in result.error
