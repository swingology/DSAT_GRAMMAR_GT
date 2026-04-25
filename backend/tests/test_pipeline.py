import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
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


# --- V3 ontology key validation tests ---

def _base_official_question(**kwargs):
    q = {
        "question_text": "Which choice completes the text?",
        "options": [
            {"label": "A", "text": "play"}, {"label": "B", "text": "have played"},
            {"label": "C", "text": "plays"}, {"label": "D", "text": "is playing"},
        ],
        "correct_option_label": "C",
        "explanation_short": "Short explanation.",
        "source_exam_code": "PT1",
        "source_module_code": "M1",
        "source_question_number": 1,
    }
    q.update(kwargs)
    return q


def test_validate_bad_grammar_role_key():
    q = _base_official_question(grammar_role_key="not_a_real_role")
    errors = validate_question(q, content_origin="official")
    review = [e for e in errors if e["severity"] == "review"]
    assert any(e["field"] == "grammar_role_key" for e in review)


def test_validate_bad_grammar_focus_key():
    q = _base_official_question(grammar_focus_key="not_a_real_focus")
    errors = validate_question(q, content_origin="official")
    review = [e for e in errors if e["severity"] == "review"]
    assert any(e["field"] == "grammar_focus_key" for e in review)


def test_validate_bad_stimulus_mode_key():
    q = _base_official_question(stimulus_mode_key="bad_mode")
    errors = validate_question(q, content_origin="official")
    review = [e for e in errors if e["severity"] == "review"]
    assert any(e["field"] == "stimulus_mode_key" for e in review)


def test_validate_bad_stem_type_key():
    q = _base_official_question(stem_type_key="bad_stem")
    errors = validate_question(q, content_origin="official")
    review = [e for e in errors if e["severity"] == "review"]
    assert any(e["field"] == "stem_type_key" for e in review)


def test_validate_explanation_short_too_long():
    q = _base_official_question(explanation_short="x" * 301)
    errors = validate_question(q, content_origin="official")
    review = [e for e in errors if e["severity"] == "review"]
    assert any(e["field"] == "explanation_short" for e in review)


def test_validate_valid_ontology_keys_no_ontology_errors():
    """All valid V3 keys produce no ontology review errors."""
    q = _base_official_question(
        grammar_role_key="agreement",
        grammar_focus_key="subject_verb_agreement",
        stimulus_mode_key="sentence_only",
        stem_type_key="complete_the_text",
    )
    errors = validate_question(q, content_origin="official")
    ontology_fields = {"grammar_role_key", "grammar_focus_key", "stimulus_mode_key", "stem_type_key"}
    assert not any(e["field"] in ontology_fields for e in errors)


# --- Overlap detection tests ---

@pytest.mark.asyncio
async def test_detect_overlaps_no_official_questions():
    """When no official questions exist, detect_overlaps returns []."""
    from app.pipeline.overlap import detect_overlaps

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    overlaps = await detect_overlaps(
        question_id=uuid.uuid4(),
        annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"},
        passage_text="The scientist observed",
        question_text="Which word correctly fills the blank?",
        db=mock_db,
    )
    assert overlaps == []


@pytest.mark.asyncio
async def test_detect_overlaps_high_passage_similarity():
    """High Jaccard similarity on passage text triggers an overlap."""
    from app.pipeline.overlap import detect_overlaps

    official_q = MagicMock()
    official_q.id = uuid.uuid4()
    official_q.current_passage_text = "the scientist observed the phenomenon carefully"
    official_q.current_question_text = "which choice completes the sentence"

    official_ann = MagicMock()
    official_ann.annotation_jsonb = {"grammar_focus_key": "subject_verb_agreement"}

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [(official_q, official_ann)]
    mock_db.execute = AsyncMock(return_value=mock_result)

    overlaps = await detect_overlaps(
        question_id=uuid.uuid4(),
        annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"},
        passage_text="the scientist observed the phenomenon carefully",
        question_text="which choice completes the sentence",
        db=mock_db,
        threshold=0.4,
    )
    assert len(overlaps) == 1
    assert overlaps[0]["strength"] >= 0.4


@pytest.mark.asyncio
async def test_detect_overlaps_skips_self():
    """detect_overlaps never reports the question being checked as its own overlap."""
    from app.pipeline.overlap import detect_overlaps

    qid = uuid.uuid4()
    official_q = MagicMock()
    official_q.id = qid  # same ID
    official_q.current_passage_text = "identical passage text here"
    official_q.current_question_text = "identical question text here"

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [(official_q, None)]
    mock_db.execute = AsyncMock(return_value=mock_result)

    overlaps = await detect_overlaps(
        question_id=qid,
        annotation_jsonb={},
        passage_text="identical passage text here",
        question_text="identical question text here",
        db=mock_db,
    )
    assert overlaps == []