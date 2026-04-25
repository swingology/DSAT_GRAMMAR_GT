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
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive"))

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    assert question.practice_status == "draft"
    assert job.question_id == question.id
    assert db.flush_count == 2
    assert question.latest_version_id is not None
    assert question.latest_annotation_id is not None


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
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive"))
    monkeypatch.setattr("app.pipeline.overlap.detect_overlaps", AsyncMock(return_value=overlaps))
    monkeypatch.setattr("app.pipeline.overlap.persist_overlap_relations", persist_overlap_relations)

    await ingest_router._run_pipeline(job, db)

    question = next(obj for obj in db.added if isinstance(obj, Question))
    assert question.official_overlap_status == "possible"
    assert job.question_id == question.id
    assert db.flush_count == 2
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
    assert db.flush_count == 1
    assert question.latest_version_id is not None
    assert question.latest_annotation_id is not None
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
async def test_approve_question_blocks_official_items():
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
    monkeypatch.setattr(ingest_router, "get_settings", lambda: SimpleNamespace(anthropic_api_key="k", openai_api_key=None, ollama_base_url="http://localhost:11434", local_archive_mirror="/tmp/test_archive"))

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
    db = _FakeDB()
    user = SimpleNamespace(id=7)
    db.get_map[(student_router.User, 7)] = user

    await student_router.delete_user(7, db=db, _auth="ok")

    assert len(db.executed) == 1
    assert db.executed[0].is_delete
    assert db.executed[0].table.name == "user_progress"
    assert len(db.deleted) == 1
    assert db.deleted[0] is user
    assert db.commit_count == 1
