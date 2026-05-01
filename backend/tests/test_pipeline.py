import pytest
import uuid
from types import SimpleNamespace
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


def test_validate_reading_question_rejects_grammar_keys():
    q = {
        "question_text": "Which choice best supports the claim?",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
        "question_family_key": "information_and_ideas",
        "skill_family_key": "command_of_evidence_textual",
        "reading_focus_key": "evidence_supports_claim",
        "grammar_role_key": "agreement",
        "difficulty_overall": "medium",
        "explanation_short": "Because A.",
    }
    errors = validate_question(q, content_origin="official")
    assert any(e["field"] == "grammar_keys" and e["severity"] == "blocking" for e in errors)


def test_validate_cross_text_requires_paired_passage():
    q = {
        "question_text": "Based on the texts, how would Text 2 respond to Text 1?",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
        "question_family_key": "craft_and_structure",
        "skill_family_key": "cross_text_connections",
        "reading_focus_key": "text2_response_to_text1",
        "stimulus_mode_key": "prose_single",
        "difficulty_overall": "medium",
        "explanation_short": "Because A.",
    }
    errors = validate_question(q, content_origin="official")
    assert any(e["field"] == "stimulus_mode_key" and e["severity"] == "blocking" for e in errors)
    assert any(e["field"] == "paired_passage_text" and e["severity"] == "blocking" for e in errors)


def test_validate_quantitative_requires_graphic_data():
    q = {
        "question_text": "Which choice most effectively uses data from the graph?",
        "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"},
                    {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
        "correct_option_label": "A",
        "question_family_key": "information_and_ideas",
        "skill_family_key": "command_of_evidence_quantitative",
        "reading_focus_key": "data_supports_claim",
        "stimulus_mode_key": "prose_plus_graph",
        "difficulty_overall": "medium",
        "explanation_short": "Because A.",
    }
    errors = validate_question(q, content_origin="official")
    assert any(e["field"] == "graphic_data" and e["severity"] == "blocking" for e in errors)


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


# --- Multi-question passage tests ---

class _ScalarResult:
    def __init__(self, items=None, first_item=None):
        self._items = items or []
        self._first_item = first_item

    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._first_item


class _FakeDB:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.executed = []
        self.get_map = {}
        self.execute_results = []
        self.commit_count = 0
        self.flush_count = 0

    def add(self, obj):
        self.added.append(obj)

    async def get(self, model, pk):
        return self.get_map.get((model, pk))

    async def execute(self, stmt):
        self.executed.append(stmt)
        if self.execute_results:
            return self.execute_results.pop(0)
        return _ScalarResult()

    async def commit(self):
        self.commit_count += 1

    async def flush(self):
        self.flush_count += 1

    async def delete(self, obj):
        self.deleted.append(obj)

    async def refresh(self, obj):
        return None


def _make_mock_job(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        content_origin="official",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "raw text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_mock_provider(responses: list) -> SimpleNamespace:
    """Create a mock provider that returns canned LLM responses."""
    return SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text=r, provider="anthropic", model="m1", latency_ms=10)
                for r in responses
            ]
        )
    )


class TestNormalizeExtractedQuestions:
    """Tests for _normalize_extracted_questions()."""

    def test_new_format_with_questions_array(self):
        """New format {passage_text, questions: [...]} extracts the array."""
        from app.routers.ingest import _normalize_extracted_questions

        extract = {
            "passage_text": "Shared passage.",
            "source_exam_code": "PT4",
            "source_module_code": "M1",
            "questions": [
                {"question_text": "Q1", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "A", "source_question_number": 1},
                {"question_text": "Q2", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "B", "source_question_number": 2},
            ],
        }
        questions, shared_passage, shared_source = _normalize_extracted_questions(extract)

        assert len(questions) == 2
        assert questions[0]["question_text"] == "Q1"
        assert questions[1]["question_text"] == "Q2"
        assert shared_passage == "Shared passage."
        assert shared_source["source_exam_code"] == "PT4"

    def test_legacy_single_question_format(self):
        """Legacy flat format wraps into a single-element list."""
        from app.routers.ingest import _normalize_extracted_questions

        extract = {
            "question_text": "Single Q",
            "passage_text": "A passage.",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
            "source_exam_code": "PT1",
            "source_question_number": 1,
        }
        questions, shared_passage, shared_source = _normalize_extracted_questions(extract)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Single Q"
        assert shared_passage == "A passage."

    def test_shared_source_merged_into_questions(self):
        """Source fields from the top level propagate into each question dict."""
        from app.routers.ingest import _normalize_extracted_questions

        extract = {
            "passage_text": "P",
            "source_exam_code": "PT5",
            "source_section_code": "S1",
            "source_module_code": "M2",
            "questions": [
                {"question_text": "Q1", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "A", "source_question_number": 1},
            ],
        }
        questions, _, _ = _normalize_extracted_questions(extract)

        assert questions[0]["source_exam_code"] == "PT5"
        assert questions[0]["source_section_code"] == "S1"
        assert questions[0]["source_module_code"] == "M2"

    def test_empty_questions_array(self):
        """An empty questions array returns an empty list."""
        from app.routers.ingest import _normalize_extracted_questions

        extract = {"passage_text": "P", "questions": []}
        questions, _, _ = _normalize_extracted_questions(extract)
        assert questions == []


class TestMultiQuestionPipeline:
    """Integration tests for _run_pipeline with multi-question extracts."""

    @pytest.mark.asyncio
    async def test_multi_question_batch_creates_multiple_questions(self, monkeypatch):
        """The pipeline creates N Question rows for N extracted questions."""
        from app.routers import ingest as ingest_router
        from app.models.db import Question

        db = _FakeDB()
        job = _make_mock_job(content_origin="unofficial")

        extract_json = {
            "passage_text": "Shared passage for two questions.",
            "questions": [
                {"question_text": "Q1", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "A", "source_question_number": 1},
                {"question_text": "Q2", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "B", "source_question_number": 2},
            ],
        }
        annotate_json = {"explanation_short": "E", "explanation_full": "F", "annotation_confidence": 0.9, "needs_human_review": False}

        responses = iter([extract_json, annotate_json, annotate_json])
        provider = _make_mock_provider(["extract", "annotate", "annotate"])

        monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
        monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
        monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
        monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(
            anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434",
            local_archive_mirror="/tmp/test_archive",
        ))

        await ingest_router._run_pipeline(job, db)

        questions = [obj for obj in db.added if isinstance(obj, Question)]
        assert len(questions) == 2
        assert questions[0].current_question_text == "Q1"
        assert questions[1].current_question_text == "Q2"
        # Shared passage text stored on each question
        assert questions[0].current_passage_text == "Shared passage for two questions."
        assert questions[1].current_passage_text == "Shared passage for two questions."
        # passage_group_id is set and identical for multi-question batches
        assert questions[0].passage_group_id is not None
        assert questions[0].passage_group_id == questions[1].passage_group_id
        # Source question numbers from the array
        assert questions[0].source_question_number == 1
        assert questions[1].source_question_number == 2

    @pytest.mark.asyncio
    async def test_single_question_legacy_format_no_passage_group_id(self, monkeypatch):
        """Single-question legacy format sets passage_group_id to None."""
        from app.routers import ingest as ingest_router
        from app.models.db import Question

        db = _FakeDB()
        job = _make_mock_job(content_origin="unofficial")

        extract_json = {
            "question_text": "Single Q",
            "passage_text": "A passage.",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}],
            "source_question_number": 1,
        }
        annotate_json = {"explanation_short": "E", "explanation_full": "F", "annotation_confidence": 0.9, "needs_human_review": False}

        responses = iter([extract_json, annotate_json])
        provider = _make_mock_provider(["extract", "annotate"])

        monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
        monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
        monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
        monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(
            anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434",
            local_archive_mirror="/tmp/test_archive",
        ))

        await ingest_router._run_pipeline(job, db)

        questions = [obj for obj in db.added if isinstance(obj, Question)]
        assert len(questions) == 1
        assert questions[0].passage_group_id is None

    @pytest.mark.asyncio
    async def test_partial_failure_second_question_fails(self, monkeypatch):
        """When question 2 of 3 fails annotation, questions 1 and 3 are persisted."""
        from app.routers import ingest as ingest_router
        from app.models.db import Question

        db = _FakeDB()
        job = _make_mock_job(content_origin="unofficial")

        extract_json = {
            "passage_text": "Shared passage.",
            "questions": [
                {"question_text": "Q1", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "A", "source_question_number": 1},
                {"question_text": "Q2", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "B", "source_question_number": 2},
                {"question_text": "Q3", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "C", "source_question_number": 3},
            ],
        }

        annotate_json = {"explanation_short": "E", "explanation_full": "F", "annotation_confidence": 0.9, "needs_human_review": False}

        # LLM returns annotate OK, then FAIL, then OK
        provider = _make_mock_provider(["extract", "annotate", "annotate", "annotate"])

        call_log = {"count": 0}

        def mock_extract_json(text):
            idx = call_log["count"]
            call_log["count"] += 1
            # idx 0 = extraction pass, idx 1 = q1 annotate, idx 2 = q2 annotate (fail), idx 3 = q3 annotate
            if idx == 2:
                raise ValueError("LLM error on question 2")
            if idx == 0:
                return extract_json
            return annotate_json

        monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
        monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr(ingest_router, "extract_json_from_text", mock_extract_json)
        monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
        monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(
            anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434",
            local_archive_mirror="/tmp/test_archive",
        ))

        await ingest_router._run_pipeline(job, db)

        questions = [obj for obj in db.added if isinstance(obj, Question)]
        assert len(questions) == 2  # Q1 and Q3 persisted, Q2 failed
        assert questions[0].current_question_text == "Q1"
        assert questions[1].current_question_text == "Q3"
        # passage_group_id links them
        assert questions[0].passage_group_id == questions[1].passage_group_id
        # Job status should not be "failed" (partial success)
        assert job.status != "failed"

    @pytest.mark.asyncio
    async def test_all_questions_fail_job_fails(self, monkeypatch):
        """When all sub-questions fail validation, job ends in failed."""
        from app.routers import ingest as ingest_router
        from app.models.db import Question

        db = _FakeDB()
        job = _make_mock_job(content_origin="unofficial")

        extract_json = {
            "passage_text": "Shared passage.",
            "questions": [
                {"question_text": "Q1", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "A", "source_question_number": 1},
                {"question_text": "Q2", "options": [{"label": "A", "text": "a"}, {"label": "B", "text": "b"}, {"label": "C", "text": "c"}, {"label": "D", "text": "d"}], "correct_option_label": "B", "source_question_number": 2},
            ],
        }
        annotate_json = {"explanation_short": "E", "explanation_full": "F", "annotation_confidence": 0.9, "needs_human_review": False}

        responses = iter([extract_json, annotate_json, annotate_json])
        provider = _make_mock_provider(["extract", "annotate", "annotate"])

        monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
        monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
        monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
        monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [{"severity": "blocking", "field": "question_text", "message": "Missing"}])
        monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(
            anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434",
            local_archive_mirror="/tmp/test_archive",
        ))

        await ingest_router._run_pipeline(job, db)

        questions = [obj for obj in db.added if isinstance(obj, Question)]
        assert len(questions) == 0
        assert job.status == "failed"


class TestExtractJsonArrayFromText:
    """Tests for extract_json_array_from_text()."""

    def test_direct_array(self):
        from app.parsers.json_parser import extract_json_array_from_text
        result = extract_json_array_from_text('[{"a": 1}, {"a": 2}]')
        assert result == [{"a": 1}, {"a": 2}]

    def test_markdown_fence_array(self):
        from app.parsers.json_parser import extract_json_array_from_text
        text = "Some text\n```json\n[{\"x\": 1}, {\"x\": 2}]\n```"
        result = extract_json_array_from_text(text)
        assert result == [{"x": 1}, {"x": 2}]

    def test_single_object_fallback(self):
        from app.parsers.json_parser import extract_json_array_from_text
        result = extract_json_array_from_text('{"single": true}')
        assert result == [{"single": True}]
