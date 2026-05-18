"""Tests for approval-gated rules amendment schemas."""
from __future__ import annotations

import json
import threading

from pydantic import ValidationError
import pytest

from app.models.amendments import RuleAmendment
from app.pipeline.amendments import _link_candidate


def _amendment_payload(**overrides):
    payload = {
        "amendment_id": "amd-pt04-v1-q006-focus",
        "status": "pending",
        "source_job_id": "job-123",
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
        "definition": "Tracks questions where the correct answer depends on the scope of cited evidence.",
        "current_best_fit": "central_idea",
        "why_current_rules_are_insufficient": "The existing key captures topic selection, not evidence scope.",
        "official_evidence": "Official question 6 requires distinguishing broad evidence from narrow evidence.",
        "rule_doc_patch": {
            "target_section": "Reading focus keys",
            "before": "- `central_idea`",
            "after": "- `central_idea`\n- `evidence_scope_shift`",
            "rationale": "Adds a narrower evidence-scope focus key.",
        },
        "master_json_patch": {
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": "evidence_scope_shift",
            "parent_key": "information_and_ideas",
            "description": "Evidence scope shift.",
        },
        "supporting_examples": [
            {
                "source_job_id": "job-123",
                "source_exam_code": "PT04",
                "source_subject_code": "verbal",
                "source_section_code": "01",
                "source_module_code": "01",
                "source_question_number": 6,
                "official_evidence": "Question 6 official evidence.",
            }
        ],
        "review_notes": [],
        "admin_decision": None,
    }
    payload.update(overrides)
    return payload


def test_rule_amendment_accepts_valid_official_payload():
    amendment = RuleAmendment.model_validate(_amendment_payload())

    assert amendment.content_origin == "official"
    assert amendment.status == "pending"
    assert amendment.to_file_dict()["amendment_id"] == "amd-pt04-v1-q006-focus"


@pytest.mark.parametrize("content_origin", ["unofficial", "generated"])
def test_rule_amendment_rejects_non_official_origins(content_origin):
    with pytest.raises(ValidationError, match="official"):
        RuleAmendment.model_validate(_amendment_payload(content_origin=content_origin))


def test_rule_amendment_requires_parent_for_hierarchical_vocab():
    payload = _amendment_payload(parent_key=None)
    payload["master_json_patch"] = {
        **payload["master_json_patch"],
        "parent_key": None,
    }

    with pytest.raises(ValidationError, match="parent_key is required"):
        RuleAmendment.model_validate(payload)


def test_rule_amendment_rejects_patch_mismatch():
    payload = _amendment_payload()
    payload["master_json_patch"] = {
        **payload["master_json_patch"],
        "proposed_value": "different_key",
    }

    with pytest.raises(ValidationError, match="proposed_value must match"):
        RuleAmendment.model_validate(payload)


def test_rule_amendment_rejects_unknown_extra_fields():
    payload = _amendment_payload(unexpected="nope")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RuleAmendment.model_validate(payload)


def test_rule_amendment_rejects_lowercase_vocab_name():
    with pytest.raises(ValidationError, match="ontology constant"):
        RuleAmendment.model_validate(_amendment_payload(affected_vocab="reading_focus"))


def test_link_candidate_concurrent_writes_do_not_lose_amendment_ids(tmp_path):
    """_link_candidate uses fcntl.flock so concurrent writers must not clobber.

    Spawns several threads, each linking a distinct amendment id to the same
    candidate row. Without the exclusive lock, read-modify-write races would
    drop ids. With the lock, every id survives.
    """
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(
        json.dumps({
            "schema_version": 1,
            "candidates": [{
                "vocab": "READING_FOCUS_BY_SKILL_FAMILY",
                "value": "evidence_scope_shift",
                "amendment_ids": [],
            }],
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    worker_count = 12
    amendment_ids = [f"amd-concurrent-{i:03d}" for i in range(worker_count)]
    barrier = threading.Barrier(worker_count)

    def link(amendment_id):
        amendment = RuleAmendment.model_validate(
            _amendment_payload(amendment_id=amendment_id)
        )
        barrier.wait()  # maximize contention
        _link_candidate(candidates_path, amendment)

    threads = [threading.Thread(target=link, args=(aid,)) for aid in amendment_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    data = json.loads(candidates_path.read_text(encoding="utf-8"))
    linked = set(data["candidates"][0]["amendment_ids"])
    assert linked == set(amendment_ids), "concurrent _link_candidate lost amendment ids"
