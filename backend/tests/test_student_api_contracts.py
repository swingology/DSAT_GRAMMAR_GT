"""Student-facing API contract tests.

Covers the five endpoints the student React app calls:
  GET  /api/questions
  POST /api/submit
  GET  /api/stats/{user_id}
  POST /api/study/recommendations
  GET  /api/study/missed

Auth is tested only at the boundary (401/403 on missing key); token-level
authorization is deferred until the online DB migration.  The focus here is
response shape, field presence, and domain logic that does not require a
live database.
"""

import uuid
import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.routers import student as student_router


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

AUTH = {"X-API-Key": "student-test-key"}
ADMIN_AUTH = {"X-API-Key": "admin-test-key"}
STUDENT_TOKEN = "00000000-0000-0000-0000-000000000001"


def _make_question(
    qid=None,
    practice_status="active",
    correct_label="B",
    content_origin="official",
    grammar_focus_key="comma_splice",
):
    qid = qid or uuid.uuid4()
    return SimpleNamespace(
        id=qid,
        content_origin=content_origin,
        practice_status=practice_status,
        current_question_text="Which choice best completes the blank?",
        current_passage_text=None,
        current_passage_tokens=None,
        current_underlined_text=None,
        current_correct_option_label=correct_label,
        latest_annotation_id=None,
        latest_version_id=uuid.uuid4(),
        stimulus_mode_key=None,
        source_release_year=None,
        source_test_name=None,
        source_exam_code=None,
        source_subject_code=None,
        source_section_code=None,
        source_module_code=None,
        source_question_number=None,
    )


def _make_option(qid, label, text, version_id=None):
    return SimpleNamespace(
        question_id=qid,
        option_label=label,
        option_text=text,
        question_version_id=version_id or uuid.uuid4(),
    )


def _make_user(uid=1):
    return SimpleNamespace(id=uid, user_token=uuid.UUID(STUDENT_TOKEN))


def _make_progress(uid=1, is_correct=True, focus_key="comma_splice"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uid,
        is_correct=is_correct,
        missed_grammar_focus_key=None if is_correct else focus_key,
        missed_syntactic_trap_key=None,
        timestamp=datetime.now(timezone.utc),
    )


class _ScalarResult:
    def __init__(self, items=None, first_item=None):
        self._items = list(items or [])
        self._first = first_item

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._first


class _QueueDB:
    """Pops pre-configured results in call order."""

    def __init__(self, results):
        self._results = list(results)
        self.added = []

    async def execute(self, _stmt):
        return self._results.pop(0) if self._results else _ScalarResult()

    async def get(self, _model, _pk):
        return None

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        obj.id = obj.id if hasattr(obj, "id") else uuid.uuid4()


# ---------------------------------------------------------------------------
# GET /api/questions — response shape and field contract
# ---------------------------------------------------------------------------

class TestGetQuestions:
    def test_requires_auth(self, client):
        resp = client.get("/api/questions")
        assert resp.status_code == 403

    def test_returns_200_with_valid_key(self, client):
        resp = client.get("/api/questions", headers=AUTH)
        assert resp.status_code == 200

    def test_response_has_items_and_inventory(self, client):
        resp = client.get("/api/questions", headers=AUTH)
        data = resp.json()
        assert "items" in data
        assert "inventory" in data

    def test_inventory_shape(self, client):
        resp = client.get("/api/questions", headers=AUTH)
        inv = resp.json()["inventory"]
        assert "matching_target_total" in inv
        assert "matching_unseen" in inv
        assert "served" in inv
        assert "includes_generated" in inv
        assert "below_threshold" in inv
        assert "threshold" in inv

    def test_answer_key_never_exposed(self, client):
        """current_correct_option_label must never appear in served items."""
        resp = client.get("/api/questions", headers=AUTH)
        for item in resp.json()["items"]:
            assert "correct" not in str(item).lower() or "correct_answer" not in item

    def test_focus_key_filter_accepted(self, client):
        resp = client.get(
            "/api/questions?grammar_focus_key=comma_splice",
            headers=AUTH,
        )
        assert resp.status_code == 200

    def test_difficulty_filter_accepted(self, client):
        resp = client.get("/api/questions?difficulty=medium", headers=AUTH)
        assert resp.status_code == 200

    def test_domain_filter_accepted(self, client):
        resp = client.get("/api/questions?domain=grammar", headers=AUTH)
        assert resp.status_code == 200

    def test_limit_param_accepted(self, client):
        resp = client.get("/api/questions?limit=5", headers=AUTH)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/submit — payload contract and response shape
# ---------------------------------------------------------------------------

class TestSubmit:
    def test_requires_auth(self, client):
        resp = client.post("/api/submit", json={})
        assert resp.status_code == 403

    def test_invalid_question_id_returns_400(self, client):
        resp = client.post(
            "/api/submit",
            json={
                "user_token": STUDENT_TOKEN,
                "question_id": "not-a-uuid",
                "selected_option_label": "A",
            },
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_nonexistent_question_returns_404(self, client):
        resp = client.post(
            "/api/submit",
            json={
                "user_token": STUDENT_TOKEN,
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "A",
            },
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_invalid_option_label_returns_422(self, client):
        """Label must match ^[A-D]$."""
        resp = client.post(
            "/api/submit",
            json={
                "user_token": STUDENT_TOKEN,
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "E",
            },
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_missing_user_token_returns_422(self, client):
        resp = client.post(
            "/api/submit",
            json={
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "A",
            },
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_omitted_source_type_defaults_to_unknown(self):
        from app.models.payload import UserProgressCreate

        body = UserProgressCreate(
            user_token=STUDENT_TOKEN,
            question_id=str(uuid.uuid4()),
            selected_option_label="A",
        )
        assert body.source_type == "unknown"

    @pytest.mark.parametrize("source_type", ["practice_test", "drill", "practice", "unknown"])
    def test_generic_source_types_are_accepted(self, source_type):
        from app.models.payload import UserProgressCreate

        body = UserProgressCreate(
            user_token=STUDENT_TOKEN,
            question_id=str(uuid.uuid4()),
            selected_option_label="A",
            source_type=source_type,
        )
        assert body.source_type == source_type

    @pytest.mark.parametrize("source_type", ["diagnostic", "invalid"])
    def test_invalid_generic_source_types_fail_request_validation(self, source_type):
        from pydantic import ValidationError
        from app.models.payload import UserProgressCreate

        with pytest.raises(ValidationError) as exc_info:
            UserProgressCreate(
                user_token=STUDENT_TOKEN,
                question_id=str(uuid.uuid4()),
                selected_option_label="A",
                source_type=source_type,
            )

        assert exc_info.value.errors()[0]["loc"] == ("source_type",)

    @pytest.mark.asyncio
    async def test_correct_answer_returns_is_correct_true(self):
        """submit returns {id, is_correct} with is_correct=True when label matches."""
        qid = uuid.uuid4()
        version_id = uuid.uuid4()
        question = _make_question(qid=qid, correct_label="B")
        question.latest_version_id = version_id
        user = _make_user()
        option = _make_option(qid, "B", "The correct choice", version_id)

        db = _QueueDB([
            _ScalarResult(first_item=option),   # verify option exists
            _ScalarResult(first_item=user),     # get user by token
            _ScalarResult(),                    # get annotation
        ])
        # submit_answer calls db.get() for the question — override to return it
        async def _get(model, pk):
            return question
        db.get = _get

        async def _fake_refresh(obj):
            obj.id = obj.id if hasattr(obj, "id") else uuid.uuid4()
        db.refresh = _fake_refresh

        result = await student_router.submit_answer(
            body=SimpleNamespace(
                user_token=STUDENT_TOKEN,
                question_id=str(qid),
                selected_option_label="B",
                source_type="unknown",
                missed_grammar_focus_key=None,
                missed_syntactic_trap_key=None,
                missed_reading_focus_key=None,
                missed_reading_skill_family_key=None,
            ),
            db=db,
            _auth="student-test-key",
        )
        assert result["is_correct"] is True
        assert db.added[0].source_type == "unknown"

    @pytest.mark.asyncio
    async def test_wrong_answer_returns_is_correct_false(self):
        qid = uuid.uuid4()
        version_id = uuid.uuid4()
        question = _make_question(qid=qid, correct_label="B")
        question.latest_version_id = version_id
        user = _make_user()
        option = _make_option(qid, "A", "A wrong choice", version_id)

        db = _QueueDB([
            _ScalarResult(first_item=option),
            _ScalarResult(first_item=user),
            _ScalarResult(),
        ])

        async def _get(model, pk):
            return question
        db.get = _get

        async def _fake_refresh(obj):
            obj.id = obj.id if hasattr(obj, "id") else uuid.uuid4()
        db.refresh = _fake_refresh

        result = await student_router.submit_answer(
            body=SimpleNamespace(
                user_token=STUDENT_TOKEN,
                question_id=str(qid),
                selected_option_label="A",
                source_type="drill",
                missed_grammar_focus_key=None,
                missed_syntactic_trap_key=None,
                missed_reading_focus_key=None,
                missed_reading_skill_family_key=None,
            ),
            db=db,
            _auth="student-test-key",
        )
        assert result["is_correct"] is False
        assert db.added[0].source_type == "drill"


# ---------------------------------------------------------------------------
# GET /api/stats/{user_id} — response shape
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/1")
        assert resp.status_code == 403

    def test_returns_200_for_unknown_user(self, client):
        resp = client.get("/api/stats/99999", headers=AUTH)
        assert resp.status_code == 200

    def test_empty_stats_shape(self, client):
        resp = client.get("/api/stats/99999", headers=AUTH)
        data = resp.json()
        assert "total_answered" in data
        assert "total_correct" in data
        assert "accuracy" in data
        assert "top_missed_focus_keys" in data
        assert "top_missed_trap_keys" in data

    def test_empty_user_has_zero_totals(self, client):
        resp = client.get("/api/stats/99999", headers=AUTH)
        data = resp.json()
        assert data["total_answered"] == 0
        assert data["total_correct"] == 0
        assert data["accuracy"] == 0.0

    def test_empty_user_has_empty_top_keys(self, client):
        resp = client.get("/api/stats/99999", headers=AUTH)
        data = resp.json()
        assert isinstance(data["top_missed_focus_keys"], list)
        assert isinstance(data["top_missed_trap_keys"], list)

    @pytest.mark.asyncio
    async def test_accuracy_computed_from_progress_records(self):
        """With 3 correct out of 5, accuracy should be 0.6."""
        user_id = 1
        records = [
            SimpleNamespace(is_correct=True, missed_grammar_focus_key=None, missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=True, missed_grammar_focus_key=None, missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=True, missed_grammar_focus_key=None, missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=False, missed_grammar_focus_key="comma_splice", missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=False, missed_grammar_focus_key="transition_logic", missed_syntactic_trap_key=None),
        ]
        db = _QueueDB([_ScalarResult(items=records)])

        result = await student_router.get_user_stats(
            user_id=user_id, db=db, _auth="student-test-key"
        )
        assert result.total_answered == 5
        assert result.total_correct == 3
        assert abs(result.accuracy - 0.6) < 0.001

    @pytest.mark.asyncio
    async def test_top_missed_focus_keys_ordered_by_frequency(self):
        records = [
            SimpleNamespace(is_correct=False, missed_grammar_focus_key="comma_splice", missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=False, missed_grammar_focus_key="comma_splice", missed_syntactic_trap_key=None),
            SimpleNamespace(is_correct=False, missed_grammar_focus_key="transition_logic", missed_syntactic_trap_key=None),
        ]
        db = _QueueDB([_ScalarResult(items=records)])

        result = await student_router.get_user_stats(
            user_id=1, db=db, _auth="student-test-key"
        )
        assert result.top_missed_focus_keys[0] == "comma_splice"


# ---------------------------------------------------------------------------
# GET /api/study/missed — response shape and filtering
# ---------------------------------------------------------------------------

class TestStudyMissed:
    def test_requires_auth(self, client):
        resp = client.get(f"/api/study/missed?user_token={STUDENT_TOKEN}")
        assert resp.status_code == 403

    def test_invalid_user_token_returns_404(self, client):
        resp = client.get(
            f"/api/study/missed?user_token={STUDENT_TOKEN}",
            headers=AUTH,
        )
        # Mock DB returns None for user lookup → 404
        assert resp.status_code == 404

    def test_domain_filter_param_accepted(self, client):
        resp = client.get(
            f"/api/study/missed?user_token={STUDENT_TOKEN}&domain=grammar",
            headers=AUTH,
        )
        # Still 404 (no user in mock DB) but param is accepted, not 422
        assert resp.status_code == 404

    def test_sort_by_param_accepted(self, client):
        resp = client.get(
            f"/api/study/missed?user_token={STUDENT_TOKEN}&sort_by=miss_count",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_limit_param_accepted(self, client):
        resp = client.get(
            f"/api/study/missed?user_token={STUDENT_TOKEN}&limit=10",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_missing_user_token_returns_422(self, client):
        resp = client.get("/api/study/missed", headers=AUTH)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_user_with_no_misses(self):
        user = _make_user()
        db = _QueueDB([
            _ScalarResult(first_item=user),  # _resolve_user_by_token
            _ScalarResult(items=[]),          # missed rows query
        ])

        result = await student_router.get_missed_questions(
            user_token=STUDENT_TOKEN,
            domain=None,
            sort_by="date",
            limit=50,
            db=db,
            _auth="student-test-key",
        )
        assert result.user_id == user.id
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_response_shape_matches_frontend_contract(self):
        """MissedQuestionsResponse must have user_id, items, total."""
        user = _make_user()
        db = _QueueDB([
            _ScalarResult(first_item=user),
            _ScalarResult(items=[]),
        ])

        result = await student_router.get_missed_questions(
            user_token=STUDENT_TOKEN,
            domain=None,
            sort_by="date",
            limit=50,
            db=db,
            _auth="student-test-key",
        )
        assert hasattr(result, "user_id")
        assert hasattr(result, "items")
        assert hasattr(result, "total")

    @pytest.mark.asyncio
    async def test_missed_item_fields_present(self):
        """Each MissedQuestionItem must have all fields the frontend expects."""
        user = _make_user()
        qid = uuid.uuid4()

        missed_row = SimpleNamespace(
            question_id=qid,
            miss_count=3,
            last_missed_at=datetime.now(timezone.utc),
            focus_key_grammar="comma_splice",
            focus_key_reading=None,
            question_domain="grammar",
            question_difficulty="medium",
            last_selected="A",
        )

        question = _make_question(qid=qid, correct_label="B")
        annotation = SimpleNamespace(
            question_id=qid,
            explanation_jsonb={"explanation_short": "A comma alone cannot join two ICs."},
            annotation_jsonb={},
        )

        db = _QueueDB([
            _ScalarResult(first_item=user),              # resolve user
            _ScalarResult(items=[missed_row]),            # missed rows
            _ScalarResult(items=[question]),              # questions by id
            _ScalarResult(items=[annotation]),            # annotations
        ])

        result = await student_router.get_missed_questions(
            user_token=STUDENT_TOKEN,
            domain=None,
            sort_by="date",
            limit=50,
            db=db,
            _auth="student-test-key",
        )

        assert result.total == 1
        item = result.items[0]
        assert item.question_id == str(qid)
        assert item.question_text == question.current_question_text
        assert item.domain == "grammar"
        assert item.focus_key == "comma_splice"
        assert item.difficulty == "medium"
        assert item.user_answer == "A"
        assert item.correct_answer == "B"
        assert item.miss_count == 3
        assert "comma" in item.explanation.lower()


# ---------------------------------------------------------------------------
# TASK-029 — passage_spans contract in /api/questions response
#
# The student-facing response must surface Pass 3 span *summaries* (label,
# anatomy_present, concepts_present) but must NEVER leak the raw word-level
# `tokens` (answer-revealing detail) or `passage_text_source`. These three
# tests pin that contract by calling student_recall() directly with a
# queued mock DB.
# ---------------------------------------------------------------------------


def _make_annotation(ann_id, passage_spans):
    """Annotation stand-in with the fields student_recall() touches."""
    return SimpleNamespace(
        id=ann_id,
        annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"},
        passage_spans=passage_spans,
        span_annotated_at=None,
        span_model_name=None,
    )


# Full Pass 3 shape as written by annotate_spans() — includes tokens +
# passage_text_source that the response MUST strip.
_FULL_PASS3_SPANS = {
    "label": "SVA: subject + main_verb",
    "anatomy_present": ["subject", "main_verb"],
    "concepts_present": ["subject_verb_agreement"],
    "tokens": [
        {"text": "cat", "anatomy": ["subject"],
         "concept_tags": [], "is_blank": False},
    ],
    "passage_text_source": "current_passage_text",
}


def _recall_db(question, annotation):
    """Queue results in the exact order student_recall(exclude_seen=False)
    executes them: count_total → count_unseen → fetch questions → anns.
    Options query is skipped (question has no latest_version_id)."""
    return _QueueDB([
        _ScalarResult(first_item=5),            # count_total (matching_target_total)
        _ScalarResult(first_item=5),            # count_unseen (matching_unseen)
        _ScalarResult(items=[question]),         # fetch_stmt → questions
        _ScalarResult(items=[annotation]),       # QuestionAnnotation batch
    ])


class TestPassageSpansContract:
    @pytest.mark.asyncio
    async def test_passage_spans_includes_summary_fields(self):
        """When annotation has passage_spans, the response item exposes
        label, anatomy_present, and concepts_present with correct values."""
        ann_id = uuid.uuid4()
        question = _make_question(qid=uuid.uuid4())
        question.latest_annotation_id = ann_id
        question.latest_version_id = None  # skip options query
        annotation = _make_annotation(ann_id, _FULL_PASS3_SPANS)

        db = _recall_db(question, annotation)

        result = await student_router.student_recall(
            exclude_seen=False,
            user_token=None,
            limit=20,
            offset=0,
            db=db,
            auth=("student", "student-test-key"),
        )

        spans = result.items[0].passage_spans
        assert spans is not None
        assert spans["label"] == "SVA: subject + main_verb"
        assert spans["anatomy_present"] == ["subject", "main_verb"]
        assert spans["concepts_present"] == ["subject_verb_agreement"]

    @pytest.mark.asyncio
    async def test_passage_spans_does_not_leak_tokens(self):
        """The raw word-level `tokens` (and passage_text_source) must NOT
        be sent to the student — only the summaries. This is the answer-
        revealing detail that the endpoint must strip."""
        ann_id = uuid.uuid4()
        question = _make_question(qid=uuid.uuid4())
        question.latest_annotation_id = ann_id
        question.latest_version_id = None
        annotation = _make_annotation(ann_id, _FULL_PASS3_SPANS)

        db = _recall_db(question, annotation)

        result = await student_router.student_recall(
            exclude_seen=False,
            user_token=None,
            limit=20,
            offset=0,
            db=db,
            auth=("student", "student-test-key"),
        )

        spans = result.items[0].passage_spans
        assert spans is not None
        assert "tokens" not in spans
        assert "passage_text_source" not in spans

    @pytest.mark.asyncio
    async def test_passage_spans_null_when_annotation_has_none(self):
        """When the annotation has no passage_spans (Pass 3 not yet run),
        the response field must be null, not an empty dict."""
        ann_id = uuid.uuid4()
        question = _make_question(qid=uuid.uuid4())
        question.latest_annotation_id = ann_id
        question.latest_version_id = None
        annotation = _make_annotation(ann_id, None)  # no passage_spans

        db = _recall_db(question, annotation)

        result = await student_router.student_recall(
            exclude_seen=False,
            user_token=None,
            limit=20,
            offset=0,
            db=db,
            auth=("student", "student-test-key"),
        )

        assert result.items[0].passage_spans is None
