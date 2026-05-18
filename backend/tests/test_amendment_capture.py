"""Tests for extracting and storing Pass 2 amendment proposals."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.pipeline.amendments import (
    capture_amendment_proposal,
    capture_amendments_from_completed_official_jobs,
    capture_amendments_from_job,
    extract_amendment_proposal,
    iter_job_amendment_payloads,
)


def _job(content_origin: str = "official", job_id: str = "job-123"):
    return SimpleNamespace(
        id=job_id,
        job_type="ingest",
        content_origin=content_origin,
        status="needs_review",
        pass1_json=None,
        pass2_json=None,
        validation_errors_jsonb=None,
        source_exam_code="PT04",
        source_subject_code="verbal",
        source_section_code="01",
        source_module_code="01",
    )


def _q_data(q_num: int = 6):
    return {
        "source_exam_code": "PT04",
        "source_subject_code": "verbal",
        "source_section_code": "01",
        "source_module_code": "01",
        "source_question_number": q_num,
        "question_text": "Official evidence text.",
        "skill_family_key": "information_and_ideas",
    }


def _proposal(value: str = "evidence_scope_shift"):
    return {
        "affected_doc": "reading",
        "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
        "proposed_value": value,
        "parent_key": "information_and_ideas",
        "definition": "Evidence scope distinction.",
        "current_best_fit": "central_idea",
        "why_current_rules_are_insufficient": "Current rules do not separate evidence scope.",
        "official_evidence": "Exact official evidence.",
        "rule_doc_patch": {
            "target_section": "Reading focus keys",
            "before": "- `central_idea`",
            "after": "- `central_idea`\n- `evidence_scope_shift`",
            "rationale": "Official evidence requires it.",
        },
        "master_json_patch": {
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": value,
            "parent_key": "information_and_ideas",
            "description": "Evidence scope distinction.",
        },
    }


def test_extract_amendment_proposal_prefers_reasoning_block():
    annotate_json = {
        "amendment_proposal": {"proposed_value": "legacy"},
        "reasoning": {"amendment_proposal": {"proposed_value": "nested"}},
    }

    assert extract_amendment_proposal(annotate_json)["proposed_value"] == "nested"


def test_capture_amendment_proposal_writes_pending_file_and_links_candidate(tmp_path):
    pending = tmp_path / "pending"
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps({
        "schema_version": 1,
        "candidates": [{
            "vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "value": "evidence_scope_shift",
            "field": "reading_focus_key",
            "occurrences": 1,
        }],
    }))

    amendment = capture_amendment_proposal(
        job=_job(),
        q_data=_q_data(),
        annotate_json={"reasoning": {"amendment_proposal": _proposal()}},
        pending_dir=pending,
        candidates_path=candidates,
    )

    assert amendment is not None
    path = pending / f"{amendment.amendment_id}.json"
    assert path.exists()
    saved = json.loads(path.read_text())
    assert saved["content_origin"] == "official"
    assert saved["affected_vocab"] == "READING_FOCUS_BY_SKILL_FAMILY"
    linked = json.loads(candidates.read_text())["candidates"][0]
    assert linked["amendment_ids"] == [amendment.amendment_id]


def test_capture_amendment_proposal_deduplicates_by_vocab_value_parent(tmp_path):
    pending = tmp_path / "pending"
    q1 = _q_data(6)
    q2 = _q_data(7)

    first = capture_amendment_proposal(
        job=_job(job_id="job-1"),
        q_data=q1,
        annotate_json={"reasoning": {"amendment_proposal": _proposal()}},
        pending_dir=pending,
        candidates_path=tmp_path / "missing_candidates.json",
    )
    second = capture_amendment_proposal(
        job=_job(job_id="job-2"),
        q_data=q2,
        annotate_json={"reasoning": {"amendment_proposal": _proposal()}},
        pending_dir=pending,
        candidates_path=tmp_path / "missing_candidates.json",
    )

    assert first is not None
    assert second is not None
    assert first.amendment_id == second.amendment_id
    saved = json.loads((pending / f"{first.amendment_id}.json").read_text())
    assert len(saved["supporting_examples"]) == 2


def test_duplicate_proposals_preserve_conflicting_body_fields_in_review_notes(tmp_path):
    pending = tmp_path / "pending"
    first = capture_amendment_proposal(
        job=_job(job_id="job-1"),
        q_data=_q_data(6),
        annotate_json={"reasoning": {"amendment_proposal": _proposal()}},
        pending_dir=pending,
        candidates_path=tmp_path / "missing_candidates.json",
    )
    changed = _proposal()
    changed["definition"] = "A different definition from another official item."
    changed["rule_doc_patch"] = {
        **changed["rule_doc_patch"],
        "after": "- `evidence_scope_shift` - Different wording.",
    }

    second = capture_amendment_proposal(
        job=_job(job_id="job-2"),
        q_data=_q_data(7),
        annotate_json={"reasoning": {"amendment_proposal": changed}},
        pending_dir=pending,
        candidates_path=tmp_path / "missing_candidates.json",
    )

    assert first is not None
    assert second is not None
    saved = json.loads((pending / f"{first.amendment_id}.json").read_text())
    assert len(saved["supporting_examples"]) == 2
    assert len(saved["review_notes"]) == 1
    note = json.loads(saved["review_notes"][0])
    assert note["type"] == "conflicting_duplicate_proposal"
    assert "definition" in note["conflicts"]
    assert note["conflicts"]["definition"]["incoming"] == "A different definition from another official item."


def test_capture_amendment_proposal_maps_additional_ontology_fields(tmp_path):
    syntactic = {
        "affected_field": "syntactic_trap_key",
        "proposed_value": "new_syntax_trap",
        "definition": "A new syntactic trap.",
        "official_evidence": "Official evidence.",
    }
    transition = {
        "affected_field": "transition_subtype_key",
        "proposed_value": "new_transition_subtype",
        "definition": "A new transition subtype.",
        "official_evidence": "Official evidence.",
    }

    first = capture_amendment_proposal(
        job=_job(),
        q_data=_q_data(),
        annotate_json={"reasoning": {"amendment_proposal": syntactic}},
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "missing_candidates.json",
    )
    second = capture_amendment_proposal(
        job=_job(),
        q_data=_q_data(7),
        annotate_json={"reasoning": {"amendment_proposal": transition}},
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "missing_candidates.json",
    )

    assert first is not None
    assert first.affected_vocab == "SYNTACTIC_TRAP_KEYS"
    assert second is not None
    assert second.affected_vocab == "TRANSITION_SUBTYPE_KEYS"


def test_capture_amendment_proposal_ignores_non_official_jobs(tmp_path):
    job = _job(content_origin="generated")
    result = capture_amendment_proposal(
        job=job,
        q_data=_q_data(),
        annotate_json={"reasoning": {"amendment_proposal": _proposal()}},
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "candidates.json",
    )

    assert result is None
    assert not (tmp_path / "pending").exists()
    assert job.validation_errors_jsonb == [{
        "step": "amendment_proposal",
        "severity": "warning",
        "code": "non_official_amendment_proposal_dropped",
        "error": "Amendment proposal ignored because content_origin is 'generated'.",
    }]


def test_capture_amendment_proposal_accepts_legacy_rule_doc_fields(tmp_path):
    legacy = {
        "proposed_key": "legacy_scope_key",
        "proposed_parent_skill_key": "information_and_ideas",
        "reason": "Current rules lack this scope distinction.",
        "evidence_text": "Exact official text.",
    }

    amendment = capture_amendment_proposal(
        job=_job(),
        q_data=_q_data(),
        annotate_json={"amendment_proposal": legacy},
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "candidates.json",
    )

    assert amendment is not None
    assert amendment.affected_vocab == "READING_FOCUS_BY_SKILL_FAMILY"
    assert amendment.proposed_value == "legacy_scope_key"


def test_iter_job_amendment_payloads_reads_multi_question_metadata():
    job = _job()
    job.pass2_json = {
        "_amendment_proposals": [{
            "source_question_number": 6,
            "q_data": _q_data(6),
            "amendment_proposal": _proposal(),
        }]
    }

    payloads = iter_job_amendment_payloads(job)

    assert len(payloads) == 1
    q_data, annotate_json = payloads[0]
    assert q_data["source_question_number"] == 6
    assert annotate_json["reasoning"]["amendment_proposal"]["proposed_value"] == "evidence_scope_shift"


def test_capture_amendments_from_job_backfills_pending_file(tmp_path):
    job = _job()
    job.pass2_json = {
        "_amendment_proposals": [{
            "source_question_number": 6,
            "q_data": _q_data(6),
            "amendment_proposal": _proposal(),
        }]
    }

    amendments = capture_amendments_from_job(
        job,
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "candidates.json",
    )

    assert len(amendments) == 1
    assert (tmp_path / "pending" / f"{amendments[0].amendment_id}.json").exists()


class _FakeScalarResult:
    def __init__(self, jobs):
        self._jobs = jobs

    def all(self):
        return self._jobs


class _FakeExecuteResult:
    def __init__(self, jobs):
        self._jobs = jobs

    def scalars(self):
        return _FakeScalarResult(self._jobs)


class _FakeDb:
    """Fake async session that honors the WHERE clause of the scan query.

    The real ``capture_amendments_from_completed_official_jobs`` query filters
    to ``job_type == "ingest"``, ``content_origin == "official"``, a completed
    status, and non-null ``pass2_json``. This fake applies the same predicate so
    a regression that drops a filter would change the captured set.
    """

    def __init__(self, jobs, *, statuses=("needs_review", "completed", "done", "approved")):
        self.jobs = jobs
        self._statuses = set(statuses)
        self.last_stmt = None

    def _matches(self, job):
        return (
            getattr(job, "job_type", None) == "ingest"
            and getattr(job, "content_origin", None) == "official"
            and getattr(job, "status", None) in self._statuses
            and getattr(job, "pass2_json", None) is not None
        )

    async def execute(self, stmt):
        self.last_stmt = stmt
        return _FakeExecuteResult([job for job in self.jobs if self._matches(job)])


@pytest.mark.asyncio
async def test_capture_amendments_from_completed_official_jobs_scans_db(tmp_path):
    job = _job()
    job.pass2_json = {
        "_amendment_proposals": [{
            "source_question_number": 6,
            "q_data": _q_data(6),
            "amendment_proposal": _proposal(),
        }]
    }

    db = _FakeDb([job])
    amendments = await capture_amendments_from_completed_official_jobs(
        db,
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "candidates.json",
    )

    assert len(amendments) == 1
    assert amendments[0].proposed_value == "evidence_scope_shift"
    # The scan issued a real SELECT against question_jobs.
    assert "question_jobs" in str(db.last_stmt)


@pytest.mark.asyncio
async def test_capture_amendments_skips_jobs_that_fail_query_filter(tmp_path):
    """Non-official, non-ingest, null-pass2 jobs must be filtered out by the scan."""
    proposals = {
        "_amendment_proposals": [{
            "source_question_number": 6,
            "q_data": _q_data(6),
            "amendment_proposal": _proposal(),
        }]
    }
    official = _job(job_id="official-job")
    official.pass2_json = dict(proposals)

    non_official = _job(content_origin="generated", job_id="generated-job")
    non_official.pass2_json = dict(proposals)

    no_pass2 = _job(job_id="no-pass2-job")
    no_pass2.pass2_json = None

    wrong_type = _job(job_id="wrong-type-job")
    wrong_type.job_type = "generate"
    wrong_type.pass2_json = dict(proposals)

    db = _FakeDb([official, non_official, no_pass2, wrong_type])
    amendments = await capture_amendments_from_completed_official_jobs(
        db,
        pending_dir=tmp_path / "pending",
        candidates_path=tmp_path / "candidates.json",
    )

    # Only the official ingest job with non-null pass2_json is captured.
    assert len(amendments) == 1
    assert {a.source_job_id for a in amendments} == {"official-job"}
