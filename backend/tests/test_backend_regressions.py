import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.db import LlmEvaluation, Question, QuestionAnnotation, QuestionJob, QuestionOption, QuestionRelation, QuestionVersion
from app.models.payload import AdminEditRequest
from app.routers import admin as admin_router
from app.routers import generate as generate_router
from app.routers import ingest as ingest_router
from app.routers import questions as questions_router
from app.routers import student as student_router


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

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_run_pipeline_keeps_official_questions_in_draft(monkeypatch):
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        content_origin="official",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "raw official text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )

    extract_json = {
        "question_text": "What is the answer?",
        "passage_text": "A passage",
        "correct_option_label": "A",
        "options": [
            {"label": "A", "text": "Correct"},
            {"label": "B", "text": "Wrong"},
        ],
        "source_exam_code": "PT01",
        "source_module_code": "M1",
        "source_question_number": 1,
        "stimulus_mode_key": "sentence_only",
        "stem_type_key": "complete_the_text",
    }
    annotate_json = {
        "explanation_short": "Because A is correct.",
        "explanation_full": "Long explanation",
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    responses = iter([extract_json, annotate_json])

    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="extract", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive", layout_detection_enabled=False, ollama_max_concurrent=8))

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    assert question.practice_status == "draft"
    assert job.question_id == question.id
    assert db.flush_count == 3  # question+version, annotation+options, source_span
    assert question.latest_version_id is not None
    assert question.latest_annotation_id is not None


@pytest.mark.asyncio
async def test_run_pipeline_auto_activates_official_questions_when_testing_flag_enabled(monkeypatch):
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        content_origin="official",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "raw official text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )

    extract_json = {
        "question_text": "What is the answer?",
        "passage_text": "A passage",
        "correct_option_label": "A",
        "options": [
            {"label": "A", "text": "Correct"},
            {"label": "B", "text": "Wrong"},
        ],
        "source_exam_code": "PT01",
        "source_module_code": "M1",
        "source_question_number": 1,
        "stimulus_mode_key": "sentence_only",
        "stem_type_key": "complete_the_text",
    }
    annotate_json = {
        "explanation_short": "Because A is correct.",
        "explanation_full": "Long explanation",
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    responses = iter([extract_json, annotate_json])

    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="extract", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ingest_router,
        "get_settings",
        lambda: SimpleNamespace(
            anthropic_api_key="k",
            openai_api_key=None,
            ollama_base_url="http://localhost:11434",
            local_archive_mirror="/tmp/test_archive",
            official_auto_activate_for_testing=True,
            layout_detection_enabled=False, ollama_max_concurrent=8,
        ),
    )

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    assert question.practice_status == "active"
    assert job.status == "approved"
    assert job.question_id == question.id


@pytest.mark.asyncio
async def test_run_pipeline_persists_overlap_after_question_creation(monkeypatch):
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        content_origin="unofficial",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "raw unofficial text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )

    extract_json = {
        "question_text": "Overlap question",
        "passage_text": "Shared passage",
        "correct_option_label": "B",
        "options": [
            {"label": "A", "text": "Wrong"},
            {"label": "B", "text": "Correct"},
        ],
    }
    annotate_json = {
        "explanation_short": "Because B is correct.",
        "explanation_full": "Long explanation",
        "annotation_confidence": 0.8,
        "needs_human_review": False,
    }
    overlaps = [{
        "official_question_id": uuid.uuid4(),
        "relation_type": "overlaps_official",
        "strength": 0.91,
        "detection_method": "question_similarity=0.91; grammar_focus_match",
    }]
    responses = iter([extract_json, annotate_json])

    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="extract", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )
    persist_overlap_relations = AsyncMock()

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive", layout_detection_enabled=False, ollama_max_concurrent=8))
    monkeypatch.setattr("app.pipeline.overlap.detect_overlaps", AsyncMock(return_value=overlaps))
    monkeypatch.setattr("app.pipeline.overlap.persist_overlap_relations", persist_overlap_relations)

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    assert question.official_overlap_status == "possible"
    assert job.question_id == question.id
    assert db.flush_count == 3  # question+version, annotation+options, source_span
    persist_overlap_relations.assert_awaited_once_with(
        question_id=question.id,
        overlaps=overlaps,
        db=db,
    )


@pytest.mark.asyncio
async def test_generate_pipeline_flushes_before_wiring_latest_pointers(monkeypatch):
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        validation_errors_jsonb=None,
        pass1_json=None,
        pass2_json=None,
        status="extracting",
        question_id=None,
    )
    generated = {
        "question_text": "Generated question",
        "passage_text": "Generated passage",
        "correct_option_label": "D",
        "options": [
            {"label": "A", "text": "Wrong"},
            {"label": "D", "text": "Correct"},
        ],
    }
    annotated = {
        "explanation_short": "Generated explanation",
        "explanation_full": "Long generated explanation",
        "annotation_confidence": 0.88,
        "needs_human_review": False,
        "generation_profile": {"model_version": "rules_agent_v7.0"},
    }
    responses = iter([generated, annotated])
    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="generate", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.generate_prompt.build_generate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr(generate_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(generate_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(generate_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive"))

    await generate_router._run_generate_pipeline(job, db, {"seed": "value"})

    question = next(obj for obj in db.added if isinstance(obj, Question))
    annotation = next(obj for obj in db.added if isinstance(obj, QuestionAnnotation))
    assert db.flush_count == 1
    assert question.latest_version_id is not None
    assert question.latest_annotation_id is not None
    assert job.question_id == question.id
    assert annotation.generation_profile_jsonb == {
        "model_version": "rules_agent_v7.0",
        "seed": "value",
    }


def test_provider_api_key_selection():
    settings = SimpleNamespace(
        anthropic_api_key="anthropic-key",
        openai_api_key="openai-key",
    )

    assert ingest_router._provider_api_key(settings, "anthropic") == "anthropic-key"
    assert ingest_router._provider_api_key(settings, "openai") == "openai-key"
    assert ingest_router._provider_api_key(settings, "ollama") == ""
    assert generate_router._provider_api_key(settings, "anthropic") == "anthropic-key"
    assert generate_router._provider_api_key(settings, "openai") == "openai-key"
    assert generate_router._provider_api_key(settings, "ollama") == ""


@pytest.mark.asyncio
async def test_run_pipeline_persists_reading_domain_question(monkeypatch):
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        content_origin="official",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "raw reading text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )

    extract_json = {
        "question_text": "Which choice best supports the claim?",
        "passage_text": "A short passage about ecology.",
        "correct_option_label": "A",
        "options": [
            {"label": "A", "text": "Correct"},
            {"label": "B", "text": "Wrong 1"},
            {"label": "C", "text": "Wrong 2"},
            {"label": "D", "text": "Wrong 3"},
        ],
        "source_exam_code": "PT11",
        "source_module_code": "M1",
        "source_question_number": 14,
        "stimulus_mode_key": "prose_single",
        "stem_type_key": "choose_best_support",
    }
    annotate_json = {
        "question_family_key": "information_and_ideas",
        "skill_family_key": "command_of_evidence_textual",
        "reading_focus_key": "evidence_supports_claim",
        "difficulty_overall": "medium",
        "difficulty_reading": "medium",
        "difficulty_grammar": "low",
        "difficulty_inference": "medium",
        "difficulty_vocab": "low",
        "distractor_strength": "high",
        "evidence_scope_key": "passage",
        "evidence_location_key": "main_clause",
        "answer_mechanism_key": "evidence_location",
        "solver_pattern_key": "locate_claim_then_match_evidence",
        "register": "academic informational",
        "tone": "neutral",
        "explanation_short": "Only A directly supports the stated claim.",
        "explanation_full": "A is the only option that provides direct support for the passage's claim.",
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    responses = iter([extract_json, annotate_json])

    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="extract", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive", layout_detection_enabled=False, ollama_max_concurrent=8))

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    annotation = next(obj for obj in db.added if isinstance(obj, QuestionAnnotation))
    assert question.current_question_text == "Which choice best supports the claim?"
    assert annotation.annotation_jsonb["question_family_key"] == "information_and_ideas"
    assert annotation.annotation_jsonb["skill_family_key"] == "command_of_evidence_textual"
    assert annotation.annotation_jsonb["reading_focus_key"] == "evidence_supports_claim"
    assert job.question_id == question.id


@pytest.mark.asyncio
async def test_admin_edit_updates_latest_version_pointer():
    db = _FakeDB()
    question_id = uuid.uuid4()
    original_version = QuestionVersion(
        id=uuid.uuid4(),
        question_id=question_id,
        version_number=1,
        change_source="ingest",
        question_text="Original",
        passage_text=None,
        choices_jsonb=[],
        correct_option_label="A",
    )
    question = Question(
        id=question_id,
        content_origin="official",
        current_question_text="Original",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text="Old explanation",
        practice_status="draft",
        official_overlap_status="none",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    question.versions = [original_version]
    db.get_map[(Question, question_id)] = question
    db.execute_results.append(_ScalarResult(first_item=original_version))
    db.execute_results.append(_ScalarResult(items=[
        QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=original_version.id,
            option_label="A",
            option_text="Choice A",
            is_correct=True,
            option_role="correct",
        )
    ]))

    await admin_router.edit_question(
        str(question_id),
        AdminEditRequest(explanation_text="Updated explanation"),
        db=db,
        _auth="ok",
    )

    new_version = next(obj for obj in db.added if isinstance(obj, QuestionVersion) and obj is not original_version)
    assert new_version.id is not None
    assert question.latest_version_id == new_version.id
    assert new_version.choices_jsonb == [{"label": "A", "text": "Choice A", "is_correct": True}]


@pytest.mark.asyncio
async def test_admin_edit_rewrites_choice_correctness_when_answer_changes():
    db = _FakeDB()
    question_id = uuid.uuid4()
    original_version = QuestionVersion(
        id=uuid.uuid4(),
        question_id=question_id,
        version_number=1,
        change_source="ingest",
        question_text="Original",
        passage_text=None,
        choices_jsonb=[],
        correct_option_label="A",
    )
    question = Question(
        id=question_id,
        content_origin="unofficial",
        current_question_text="Original",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text="Old explanation",
        practice_status="active",
        official_overlap_status="none",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    question.versions = [original_version]
    db.get_map[(Question, question_id)] = question
    db.execute_results.append(_ScalarResult(first_item=original_version))
    db.execute_results.append(_ScalarResult(items=[
        QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=original_version.id,
            option_label="A",
            option_text="Choice A",
            is_correct=True,
            option_role="correct",
        ),
        QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=original_version.id,
            option_label="B",
            option_text="Choice B",
            is_correct=False,
            option_role="distractor",
        ),
    ]))

    await admin_router.edit_question(
        str(question_id),
        AdminEditRequest(correct_option_label="B"),
        db=db,
        _auth="ok",
    )

    new_version = next(obj for obj in db.added if isinstance(obj, QuestionVersion) and obj is not original_version)
    assert new_version.correct_option_label == "B"
    assert new_version.choices_jsonb == [
        {"label": "A", "text": "Choice A", "is_correct": False},
        {"label": "B", "text": "Choice B", "is_correct": True},
    ]


@pytest.mark.asyncio
async def test_approve_question_allows_official_items():
    db = _FakeDB()
    question_id = uuid.uuid4()
    question = Question(
        id=question_id,
        content_origin="official",
        current_question_text="Official",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text=None,
        practice_status="draft",
        official_overlap_status="none",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    db.get_map[(Question, question_id)] = question

    result = await admin_router.approve_question(str(question_id), db=db, _auth="ok")
    assert question.practice_status == "active"
    assert result["practice_status"] == "active"


@pytest.mark.asyncio
async def test_approve_question_blocks_official_with_overlap():
    db = _FakeDB()
    question_id = uuid.uuid4()
    question = Question(
        id=question_id,
        content_origin="official",
        current_question_text="Official",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text=None,
        practice_status="draft",
        official_overlap_status="possible",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    db.get_map[(Question, question_id)] = question

    with pytest.raises(HTTPException) as exc:
        await admin_router.approve_question(str(question_id), db=db, _auth="ok")

    assert exc.value.status_code == 409
    assert question.practice_status == "draft"


@pytest.mark.asyncio
async def test_approve_question_blocks_generated_overlap_items():
    db = _FakeDB()
    question_id = uuid.uuid4()
    question = Question(
        id=question_id,
        content_origin="generated",
        current_question_text="Generated",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text=None,
        practice_status="draft",
        official_overlap_status="possible",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    db.get_map[(Question, question_id)] = question

    with pytest.raises(HTTPException) as exc:
        await admin_router.approve_question(str(question_id), db=db, _auth="ok")

    assert exc.value.status_code == 409
    assert question.practice_status == "draft"


@pytest.mark.asyncio
async def test_confirm_overlap_sets_canonical_question_and_confirms_relations():
    db = _FakeDB()
    question_id = uuid.uuid4()
    official_id = uuid.uuid4()
    question = Question(
        id=question_id,
        content_origin="generated",
        current_question_text="Generated",
        current_passage_text=None,
        current_correct_option_label="A",
        current_explanation_text=None,
        practice_status="draft",
        official_overlap_status="possible",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    relation = QuestionRelation(
        id=uuid.uuid4(),
        from_question_id=question_id,
        to_question_id=official_id,
        relation_type="overlaps_official",
        is_human_confirmed=False,
    )
    db.get_map[(Question, question_id)] = question
    db.execute_results.append(_ScalarResult(items=[relation]))

    result = await admin_router.confirm_overlap(str(question_id), db=db, _auth="ok")

    assert result["official_overlap_status"] == "confirmed"
    assert result["canonical_official_question_id"] == str(official_id)
    assert question.canonical_official_question_id == official_id
    assert relation.is_human_confirmed is True


@pytest.mark.asyncio
async def test_create_evaluation_404s_for_missing_question():
    db = _FakeDB()
    job_id = uuid.uuid4()
    db.get_map[(QuestionJob, job_id)] = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="official",
        input_format="pdf",
        status="approved",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
    )

    with pytest.raises(HTTPException) as exc:
        await admin_router.create_evaluation(
            admin_router.EvaluationCreateRequest(
                job_id=str(job_id),
                question_id=str(uuid.uuid4()),
            ),
            db=db,
            _auth="ok",
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_relation_rejects_invalid_relation_type():
    db = _FakeDB()

    with pytest.raises(HTTPException) as exc:
        await admin_router.create_relation(
            admin_router.RelationCreateRequest(
                from_question_id=str(uuid.uuid4()),
                to_question_id=str(uuid.uuid4()),
                relation_type="not_a_real_type",
            ),
            db=db,
            _auth="ok",
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_reannotate_updates_current_explanation_text():
    db = _FakeDB()
    question_id = uuid.uuid4()
    job = SimpleNamespace(
        question_id=question_id,
        content_origin="official",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={
            "question_text": "Original question",
            "passage_text": "Passage",
            "correct_option_label": "C",
            "options": [],
        },
        status="annotating",
        validation_errors_jsonb=None,
    )
    question = Question(
        id=question_id,
        content_origin="official",
        current_question_text="Original question",
        current_passage_text="Passage",
        current_correct_option_label="C",
        current_explanation_text="Old explanation",
        practice_status="draft",
        official_overlap_status="none",
        is_admin_edited=False,
        metadata_managed_by_llm=True,
    )
    question.versions = [
        QuestionVersion(
            id=uuid.uuid4(),
            question_id=question_id,
            version_number=1,
            change_source="ingest",
            question_text="Original question",
            passage_text="Passage",
            choices_jsonb=[],
            correct_option_label="C",
            explanation_text="Old explanation",
        )
    ]
    db.get_map[(Question, question_id)] = question

    provider = SimpleNamespace(
        complete=AsyncMock(
            return_value=SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10)
        )
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("system", "user"))
    monkeypatch.setattr("app.parsers.json_parser.extract_json_from_text", lambda *_: {
        "explanation_short": "Fresh explanation",
        "explanation_full": "Fresh full explanation",
        "annotation_confidence": 0.95,
        "needs_human_review": False,
    })
    monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive", layout_detection_enabled=False, ollama_max_concurrent=8))

    try:
        await ingest_router._run_reannotate_pipeline(job, db)
    finally:
        monkeypatch.undo()

    assert question.current_explanation_text == "Fresh explanation"
    assert question.latest_version_id is not None
    assert question.latest_annotation_id is not None


def test_question_relation_detection_method_is_unbounded_text():
    assert isinstance(QuestionRelation.detection_method.property.columns[0].type, type(Question.current_question_text.property.columns[0].type))


@pytest.mark.asyncio
async def test_recall_questions_combines_annotation_filters_with_one_join():
    class _StatementDB:
        def __init__(self):
            self.statement = None

        async def execute(self, stmt):
            self.statement = stmt
            return _ScalarResult(items=[])

    db = _StatementDB()
    await questions_router.recall_questions(
        grammar_focus="subject_verb_agreement",
        difficulty="medium",
        limit=20,
        offset=0,
        db=db,
        _auth="ok",
    )

    sql = str(db.statement)
    assert sql.count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_student_recall_combines_annotation_filters_with_one_join():
    class _StatementDB:
        def __init__(self):
            self.statement = None

        async def execute(self, stmt):
            self.statement = stmt
            return _ScalarResult(items=[])

    db = _StatementDB()
    await student_router.student_recall(
        grammar_focus="subject_verb_agreement",
        difficulty="medium",
        limit=20,
        offset=0,
        db=db,
        _auth="ok",
    )

    sql = str(db.statement)
    assert sql.count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_delete_user_removes_progress_before_user_delete():
    from app.routers import users as users_router
    db = _FakeDB()
    user = SimpleNamespace(id=7)
    db.get_map[(users_router.User, 7)] = user

    await users_router.delete_user(7, db=db, _auth="ok")

    assert len(db.executed) == 1
    assert db.executed[0].is_delete
    assert db.executed[0].table.name == "user_progress"
    assert len(db.deleted) == 1
    assert db.deleted[0] is user


@pytest.mark.asyncio
async def test_submit_answer_rejects_non_active_question():
    from app.models.payload import UserProgressCreate

    db = _FakeDB()
    qid = uuid.uuid4()
    draft_question = SimpleNamespace(
        id=qid,
        practice_status="draft",
        current_correct_option_label="A",
    )
    db.get_map[(student_router.Question, qid)] = draft_question

    with pytest.raises(HTTPException) as exc:
        await student_router.submit_answer(
            body=UserProgressCreate(
                user_token=str(uuid.uuid4()),
                question_id=str(qid),
                selected_option_label="A",
            ),
            db=db,
            _auth="ok",
        )
    assert exc.value.status_code == 400
    assert "not active" in exc.value.detail


@pytest.mark.asyncio
async def test_admin_create_relation_rejects_self_reference():
    db = _FakeDB()
    qid = uuid.uuid4()
    q = SimpleNamespace(id=qid)
    db.get_map[(admin_router.Question, qid)] = q

    with pytest.raises(HTTPException) as exc:
        await admin_router.create_relation(
            body=admin_router.RelationCreateRequest(
                from_question_id=str(qid),
                to_question_id=str(qid),
                relation_type="overlaps_official",
            ),
            db=db,
            _auth="ok",
        )
    assert exc.value.status_code == 400
    assert "itself" in exc.value.detail


# --- JSON parser routing tests ---

def test_extract_json_routes_all_ollama_through_repair_path():
    """Ollama provider with non-Kimi model uses repair path for fenced JSON output."""
    from app.parsers.json_parser import extract_json_from_text

    text = "Here is the extracted data:\n```json\n{\"question_text\": \"What is X?\", \"options\": []}\n```"
    result = extract_json_from_text(text, provider_name="ollama", model_name="llava:13b")
    assert result["question_text"] == "What is X?"


def test_extract_json_repair_path_handles_bare_keys_for_ollama():
    """Ollama repair path normalizes bare (unquoted) JSON keys from VLM output."""
    from app.parsers.json_parser import extract_json_from_text

    text = "{question_text: 'What is X?', correct_option_label: 'A'}"
    result = extract_json_from_text(text, provider_name="ollama", model_name="moondream:latest")
    assert result["question_text"] == "What is X?"


# --- Pipeline JSONB assignment tests ---

@pytest.mark.asyncio
async def test_run_pipeline_reassigns_pass1_json_with_created_ids(monkeypatch):
    """_created_question_ids must be stored via full dict reassignment so SQLAlchemy tracks the change."""
    db = _FakeDB()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        content_origin="unofficial",
        job_type="ingest",
        provider_name="anthropic",
        model_name="model",
        prompt_version="v3.0",
        rules_version="rules",
        pass1_json={"raw_text": "some unofficial text"},
        validation_errors_jsonb=None,
        raw_asset_id=None,
        status="parsing",
        question_id=None,
    )

    extract_json_data = {
        "question_text": "What is X?",
        "correct_option_label": "B",
        "options": [
            {"label": "A", "text": "Wrong"},
            {"label": "B", "text": "Right"},
            {"label": "C", "text": "Wrong"},
            {"label": "D", "text": "Wrong"},
        ],
    }
    annotate_json_data = {
        "explanation_short": "B is correct.",
        "explanation_full": "Long explanation",
        "annotation_confidence": 0.85,
        "needs_human_review": False,
    }
    responses = iter([extract_json_data, annotate_json_data])

    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                SimpleNamespace(raw_text="extract", provider="anthropic", model="m1", latency_ms=10),
                SimpleNamespace(raw_text="annotate", provider="anthropic", model="m1", latency_ms=10),
            ]
        )
    )

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.extract_prompt.build_extract_prompt", lambda *_: ("sys", "usr"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_: ("sys", "usr"))
    monkeypatch.setattr(ingest_router, "extract_json_from_text", lambda *_: next(responses))
    monkeypatch.setattr(ingest_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(
        anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434",
        local_archive_mirror="/tmp/test_archive", layout_detection_enabled=False, ollama_max_concurrent=8,
    ))

    await ingest_router._run_pipeline(job, db)

    # Verify dict was reassigned (not mutated) and _created_question_ids is present
    assert "_created_question_ids" in job.pass1_json
    assert len(job.pass1_json["_created_question_ids"]) == 1
    assert job.status == "approved"


# ── Label normalization & deduplication ──────────────────────────────────────

def test_normalize_questions_strips_trailing_paren_from_correct_label():
    """VLMs sometimes emit 'A)' instead of 'A' for correct_option_label."""
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {"question_text": "Q1", "correct_option_label": "A)", "options": []},
        ]
    })
    assert result[0]["correct_option_label"] == "A"


def test_normalize_questions_strips_trailing_period_from_correct_label():
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {"question_text": "Q1", "correct_option_label": "B.", "options": []},
        ]
    })
    assert result[0]["correct_option_label"] == "B"


def test_normalize_questions_lowercased_correct_label_upcased():
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {"question_text": "Q1", "correct_option_label": "c)", "options": []},
        ]
    })
    assert result[0]["correct_option_label"] == "C"


def test_normalize_questions_strips_option_label_parens():
    """Option labels like 'A)' should also be normalized."""
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {
                "question_text": "Q1",
                "correct_option_label": "A",
                "options": [
                    {"label": "A)", "text": "Choice A"},
                    {"label": "B.", "text": "Choice B"},
                    {"label": "c", "text": "Choice C"},
                    {"label": "D", "text": "Choice D"},
                ],
            }
        ]
    })
    labels = [o["label"] for o in result[0]["options"]]
    assert labels == ["A", "B", "C", "D"]


def test_normalize_questions_deduplicates_identical_question_text():
    """VLMs sometimes hallucinate duplicate question rows; only the first should survive."""
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {"question_text": "What is X?", "correct_option_label": "A", "options": []},
            {"question_text": "What is X?", "correct_option_label": "B", "options": []},
            {"question_text": "What is Y?", "correct_option_label": "C", "options": []},
        ]
    })
    assert len(result) == 2
    assert result[0]["question_text"] == "What is X?"
    assert result[0]["correct_option_label"] == "A"
    assert result[1]["question_text"] == "What is Y?"


def test_normalize_questions_dedup_is_case_insensitive():
    result, _, _ = ingest_router._normalize_extracted_questions({
        "questions": [
            {"question_text": "What is X?", "correct_option_label": "A", "options": []},
            {"question_text": "WHAT IS X?", "correct_option_label": "B", "options": []},
        ]
    })
    assert len(result) == 1


# ── _validate_question_numbers ────────────────────────────────────────────────

def _make_qs(numbers):
    return [{"source_question_number": n, "question_text": f"Q{n}"} for n in numbers]


def test_validate_qnums_clean_verbal():
    qs = _make_qs([3, 4, 5, 6])
    warns = ingest_router._validate_question_numbers(qs, "verbal", "01")
    assert warns == []


def test_validate_qnums_clean_math():
    qs = _make_qs([1, 2, 3])
    warns = ingest_router._validate_question_numbers(qs, "math", "02")
    assert warns == []


def test_validate_qnums_null_number():
    qs = _make_qs([3, None, 5])
    warns = ingest_router._validate_question_numbers(qs, "verbal", "01")
    issues = [w["issue"] for w in warns]
    assert "non_integer" in issues


def test_validate_qnums_out_of_range():
    qs = _make_qs([25, 26, 28])  # 28 > 27 for verbal
    warns = ingest_router._validate_question_numbers(qs, "verbal", "01")
    issues = [w["issue"] for w in warns]
    assert "out_of_range" in issues
    assert "non_contiguous" in issues


def test_validate_qnums_duplicate():
    qs = _make_qs([3, 4, 4, 5])
    warns = ingest_router._validate_question_numbers(qs, "verbal", "01")
    issues = [w["issue"] for w in warns]
    assert "duplicate" in issues


def test_validate_qnums_gap():
    qs = _make_qs([3, 4, 6])  # missing 5
    warns = ingest_router._validate_question_numbers(qs, "verbal", "01")
    issues = [w["issue"] for w in warns]
    assert "non_contiguous" in issues
    gap_warn = next(w for w in warns if w["issue"] == "non_contiguous")
    assert 5 in gap_warn["gaps"]


def test_validate_qnums_unknown_module_warns():
    qs = _make_qs([1, 2, 3])
    warns = ingest_router._validate_question_numbers(qs, "verbal", "03")
    issues = [w["issue"] for w in warns]
    assert "unknown_module" in issues


def test_official_question_uuid_deterministic():
    uid1 = ingest_router._official_question_uuid("PT1", "verbal", "01", "01", 3)
    uid2 = ingest_router._official_question_uuid("PT1", "verbal", "01", "01", 3)
    assert uid1 == uid2


def test_official_question_uuid_differs_by_field():
    base = ingest_router._official_question_uuid("PT1", "verbal", "01", "01", 3)
    diff_exam    = ingest_router._official_question_uuid("PT6", "verbal", "01", "01", 3)
    diff_section = ingest_router._official_question_uuid("PT1", "verbal", "02", "01", 3)
    diff_module  = ingest_router._official_question_uuid("PT1", "verbal", "01", "02", 3)
    diff_qnum    = ingest_router._official_question_uuid("PT1", "verbal", "01", "01", 4)
    assert len({base, diff_exam, diff_section, diff_module, diff_qnum}) == 5


# ── _scan_qnums_from_ocr ──────────────────────────────────────────────────────

def test_scan_qnums_glm_format():
    ocr = "3\nFollowing the principles...\n\n4\nThe parasitic dodder...\n\n5\nGiven that conditions..."
    assert ingest_router._scan_qnums_from_ocr(ocr) == [3, 4, 5]


def test_scan_qnums_ignores_non_standalone():
    # Numbers embedded in text should not be picked up
    ocr = "There are 3 types of things.\n\n4\nQuestion four text here."
    result = ingest_router._scan_qnums_from_ocr(ocr)
    assert result == [4]


def test_scan_qnums_accepts_trailing_punctuation():
    ocr = "3.\nQuestion text\n\n4)\nAnother question"
    assert ingest_router._scan_qnums_from_ocr(ocr) == [3, 4]


def test_scan_qnums_deduplicates():
    ocr = "3\nText\n\n3\nDuplicate"
    assert ingest_router._scan_qnums_from_ocr(ocr) == [3]


# ── _verify_qnums_against_ocr ─────────────────────────────────────────────────

def test_verify_qnums_clean_match():
    qs = [{"source_question_number": 3}, {"source_question_number": 4}]
    ocr = "3\nText one\n\n4\nText two"
    assert ingest_router._verify_qnums_against_ocr(qs, ocr) == []


def test_verify_qnums_mismatch():
    qs = [{"source_question_number": 5}, {"source_question_number": 4}]
    ocr = "3\nText one\n\n4\nText two"
    warns = ingest_router._verify_qnums_against_ocr(qs, ocr)
    issues = [w["issue"] for w in warns]
    assert "mismatch" in issues
    mw = next(w for w in warns if w["issue"] == "mismatch")
    assert mw["llm_value"] == 5
    assert mw["ocr_value"] == 3


def test_verify_qnums_llm_missing_ocr_found():
    qs = [{"source_question_number": None}, {"source_question_number": 4}]
    ocr = "3\nText one\n\n4\nText two"
    warns = ingest_router._verify_qnums_against_ocr(qs, ocr)
    issues = [w["issue"] for w in warns]
    assert "llm_missing_ocr_found" in issues


def test_verify_qnums_sparse_ocr_skips_check():
    # OCR found fewer numbers than questions — cross-check should be skipped
    qs = [{"source_question_number": 3}, {"source_question_number": 4}, {"source_question_number": 5}]
    ocr = "3\nOnly one number in OCR"
    assert ingest_router._verify_qnums_against_ocr(qs, ocr) == []


def test_sanitize_source_name_strips_path_separators():
    assert ingest_router._sanitize_source_name("../../etc/passwd") == ".._.._etc_passwd"


def test_sanitize_source_name_strips_control_chars():
    assert ingest_router._sanitize_source_name("file\x00name.pdf") == "file_name.pdf"


def test_sanitize_source_name_truncates_long_names():
    long = "a" * 300
    result = ingest_router._sanitize_source_name(long)
    assert len(result) == 200  # matches QuestionAsset.source_name column width


def test_sanitize_source_name_none_passthrough():
    assert ingest_router._sanitize_source_name(None) is None
