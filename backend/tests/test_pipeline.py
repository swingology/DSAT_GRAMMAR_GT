import pytest
from app.pipeline.orchestrator import (
    JobOrchestrator,
    can_transition,
    next_status,
)
from app.pipeline.validator import validate_question


# --- Orchestrator state machine tests ---

def test_can_transition_pending_to_parsing():
    assert can_transition("pending", "parsing") is True


def test_cannot_transition_pending_to_approved():
    assert can_transition("pending", "approved") is False


def test_can_transition_annotating_to_validating():
    assert can_transition("annotating", "validating") is True


def test_can_transition_validating_to_approved():
    assert can_transition("validating", "approved") is True


def test_can_transition_validating_to_failed():
    assert can_transition("validating", "failed") is True


def test_can_transition_any_to_failed():
    assert can_transition("parsing", "failed") is True
    assert can_transition("extracting", "failed") is True
    assert can_transition("annotating", "failed") is True


def test_next_status_official_ingest():
    """Official ingest follows: pending → parsing → extracting → annotating → validating → approved"""
    assert next_status("pending", content_origin="official", job_type="ingest") == "parsing"
    assert next_status("parsing", content_origin="official", job_type="ingest") == "extracting"
    assert next_status("extracting", content_origin="official", job_type="ingest") == "annotating"
    assert next_status("annotating", content_origin="official", job_type="ingest") == "validating"


def test_next_status_unofficial_includes_overlap():
    """Unofficial ingest adds overlap_checking between annotating and validating."""
    assert next_status("annotating", content_origin="unofficial", job_type="ingest") == "overlap_checking"
    assert next_status("overlap_checking", content_origin="unofficial", job_type="ingest") == "validating"


def test_next_status_generated_includes_overlap():
    """Generated questions also include overlap checking."""
    assert next_status("annotating", content_origin="generated", job_type="generate") == "overlap_checking"


# --- Orchestrator class tests ---

def test_job_orchestrator_advance():
    orch = JobOrchestrator(job_id="test-123", content_origin="official", job_type="ingest")
    assert orch.current_status == "pending"
    orch.advance()
    assert orch.current_status == "parsing"
    orch.advance()
    assert orch.current_status == "extracting"


def test_job_orchestrator_fail():
    orch = JobOrchestrator(job_id="test-123", content_origin="official", job_type="ingest")
    orch.fail("extracting", "llm_error", "API timeout", retries=1)
    assert orch.current_status == "failed"
    assert len(orch.errors) == 1
    assert orch.errors[0]["error_code"] == "llm_error"


# --- Validator tests ---

def test_validate_official_question_passes():
    q = {
        "question_text": "Which choice completes the text?",
        "options": [
            {"label": "A", "text": "play"},
            {"label": "B", "text": "have played"},
            {"label": "C", "text": "plays"},
            {"label": "D", "text": "is playing"},
        ],
        "correct_option_label": "C",
        "source_exam_code": "PT4",
        "source_module_code": "M1",
        "source_question_number": 1,
        "explanation_short": "Singular subject requires singular verb.",
    }
    errors = validate_question(q, content_origin="official")
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_validate_official_missing_source():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
    }
    errors = validate_question(q, content_origin="official")
    assert any("source_exam_code" in e["field"] for e in errors)


def test_validate_generated_missing_lineage():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
    }
    errors = validate_question(q, content_origin="generated")
    assert any("lineage" in e["field"] or "generation" in e["message"].lower() for e in errors)


def test_validate_bad_correct_label():
    q = {
        "question_text": "test",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "E",
    }
    errors = validate_question(q, content_origin="official")
    assert any("correct_option_label" in e["field"] for e in errors)