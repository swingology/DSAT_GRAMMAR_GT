"""Focused contracts for the missed-question review endpoints."""

from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.models.db import Question, QuestionAnnotation, QuestionOption
from app.routers import student as student_router


USER_TOKEN = "00000000-0000-0000-0000-000000000001"


class _Result:
    def __init__(self, *, items=None, first=None, scalar=None, row=None):
        self._items = list(items or [])
        self._first = first
        self._scalar = scalar
        self._row = row

    def scalars(self):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._items

    def scalar_one(self):
        return self._scalar

    def one(self):
        return self._row


class _QueueDB:
    def __init__(self, results):
        self.results = list(results)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)


def _question(question_id, version_id, annotation_id):
    return SimpleNamespace(
        id=question_id,
        latest_version_id=version_id,
        latest_annotation_id=annotation_id,
        current_passage_text="Passage",
        current_paired_passage_text=None,
        current_underlined_text="underlined",
        current_question_text="Which option is correct?",
        current_correct_option_label="B",
        stem_type_key="transitions",
        content_origin="official",
        source_test_name="Bluebook 1",
        source_section_code="RW",
        source_module_code="M1",
        source_question_number=7,
    )


def _option(question_id, version_id, label, *, is_correct=False):
    return SimpleNamespace(
        question_id=question_id,
        question_version_id=version_id,
        option_label=label,
        option_text=f"Option {label}",
        is_correct=is_correct,
    )


def _review_row(question_id):
    return SimpleNamespace(
        question_id=question_id,
        selected_option_label="A",
        source_type="drill",
        question_domain="reading",
        question_difficulty="medium",
        missed_grammar_focus_key=None,
        missed_reading_focus_key=None,
        missed_reading_skill_family_key="information_and_ideas",
        miss_count=3,
        last_missed_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
        source_types=["practice", "drill"],
    )


async def _call_review(db, **overrides):
    params = {
        "user_token": USER_TOKEN,
        "source_type": None,
        "source_test_name": None,
        "source_section_code": None,
        "source_module_code": None,
        "domain": None,
        "focus_key": None,
        "stem_type_key": None,
        "difficulty": None,
        "content_origin": None,
        "page": 1,
        "page_size": 20,
        "db": db,
        "_auth": "student-test-key",
    }
    params.update(overrides)
    return await student_router.get_review_questions(**params)


def _postgres_sql(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


@pytest.mark.parametrize(
    ("raw", "allowed", "expected"),
    [
        (None, {"drill"}, None),
        ("", {"drill"}, None),
        ("all", {"drill"}, None),
        (" drill,practice,drill ", {"drill", "practice"}, ["drill", "practice"]),
    ],
)
def test_parse_review_csv_filter(raw, allowed, expected):
    assert student_router._parse_review_csv_filter(
        raw,
        allowed=allowed,
        field_name="source_type",
    ) == expected


@pytest.mark.parametrize("raw", ["all,drill", "diagnostic,bogus"])
def test_parse_review_csv_filter_rejects_invalid_values(raw):
    with pytest.raises(HTTPException) as exc_info:
        student_router._parse_review_csv_filter(
            raw,
            allowed={"diagnostic", "drill"},
            field_name="source_type",
        )
    assert exc_info.value.status_code == 422


def test_reading_focus_falls_back_to_skill_family():
    focus_key, source = student_router._review_focus_key(
        _review_row(uuid.uuid4())
    )
    assert focus_key == "information_and_ideas"
    assert source == "reading_skill_family_key"


def test_review_options_prefers_single_current_version_flag(caplog):
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    question = _question(question_id, version_id, None)
    question.current_correct_option_label = "A"
    options = [
        _option(question_id, version_id, "A"),
        _option(question_id, version_id, "B", is_correct=True),
    ]

    payload, correct_label = student_router._review_options(question, options)

    assert correct_label == "B"
    assert [option.label for option in payload if option.is_correct] == ["B"]
    assert "Review answer mismatch" in caplog.text


def test_review_options_normalizes_invalid_flags_to_question_label():
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    question = _question(question_id, version_id, None)
    options = [
        _option(question_id, version_id, "A", is_correct=True),
        _option(question_id, version_id, "B", is_correct=True),
    ]

    payload, correct_label = student_router._review_options(question, options)

    assert correct_label == "B"
    assert [option.label for option in payload if option.is_correct] == ["B"]


def test_review_options_rejects_unresolvable_answer_data():
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    question = _question(question_id, version_id, None)
    question.current_correct_option_label = "D"

    with pytest.raises(HTTPException) as exc_info:
        student_router._review_options(
            question,
            [_option(question_id, version_id, "A")],
        )
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_review_empty_result_preserves_requested_page():
    user = SimpleNamespace(id=12)
    db = _QueueDB([_Result(first=user), _Result(scalar=0)])

    response = await _call_review(db, page=4, page_size=5)

    assert response.items == []
    assert response.total == 0
    assert response.page == 4
    assert response.page_size == 5
    assert response.has_more is False


@pytest.mark.asyncio
async def test_review_assembles_latest_attempt_and_current_version_content():
    user = SimpleNamespace(id=12)
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()
    question = _question(question_id, version_id, annotation_id)
    row = _review_row(question_id)
    options = [
        _option(question_id, version_id, "A"),
        _option(question_id, version_id, "B", is_correct=True),
    ]
    annotation = SimpleNamespace(
        id=annotation_id,
        explanation_jsonb={"short": "Because B is correct."},
        annotation_jsonb={},
    )
    db = _QueueDB([
        _Result(first=user),
        _Result(scalar=1),
        _Result(items=[row]),
        _Result(items=[question]),
        _Result(items=options),
        _Result(items=[annotation]),
    ])

    response = await _call_review(db, page_size=1)

    assert response.total == 1
    assert response.has_more is False
    item = response.items[0]
    assert item.user_answer == "A"
    assert item.source_type == "drill"
    assert item.source_types == ["drill", "practice"]
    assert item.miss_count == 3
    assert item.focus_key == "information_and_ideas"
    assert item.focus_key_source == "reading_skill_family_key"
    assert item.correct_option_label == "B"
    assert item.explanation == "Because B is correct."

    page_sql = _postgres_sql(db.statements[2])
    option_sql = _postgres_sql(db.statements[4])
    assert "row_number() OVER" in page_sql
    assert "timestamp DESC NULLS LAST" in page_sql
    assert "progress_id DESC" in page_sql
    assert "question_id ASC" in page_sql
    assert "question_options.question_version_id IN" in option_sql


@pytest.mark.asyncio
async def test_review_treats_null_source_as_unknown_and_reports_more_pages():
    user = SimpleNamespace(id=12)
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    question = _question(question_id, version_id, None)
    row = _review_row(question_id)
    row.source_type = None
    row.source_types = ["unknown"]
    db = _QueueDB([
        _Result(first=user),
        _Result(scalar=2),
        _Result(items=[row]),
        _Result(items=[question]),
        _Result(items=[
            _option(question_id, version_id, "A"),
            _option(question_id, version_id, "B", is_correct=True),
        ]),
    ])

    response = await _call_review(db, page_size=1)

    assert response.items[0].source_type == "unknown"
    assert response.items[0].source_types == ["unknown"]
    assert response.has_more is True


@pytest.mark.asyncio
async def test_review_query_contains_all_filters_and_null_source_fallback():
    user = SimpleNamespace(id=12)
    db = _QueueDB([_Result(first=user), _Result(scalar=0)])

    await _call_review(
        db,
        source_type="unknown,drill",
        source_test_name="Bluebook 1",
        source_section_code="RW",
        source_module_code="M1",
        domain="reading",
        focus_key="information_and_ideas",
        stem_type_key="transitions",
        difficulty="medium",
        content_origin="official,generated",
    )

    sql = _postgres_sql(db.statements[1])
    assert "coalesce(user_progress.source_type" in sql
    assert "questions.source_test_name" in sql
    assert "questions.source_section_code" in sql
    assert "questions.source_module_code" in sql
    assert "user_progress.question_domain" in sql
    assert "user_progress.missed_grammar_focus_key" in sql
    assert "user_progress.missed_reading_focus_key" in sql
    assert "user_progress.missed_reading_skill_family_key" in sql
    assert "questions.stem_type_key" in sql
    assert "user_progress.question_difficulty" in sql
    assert "questions.content_origin" in sql
    assert "SELECT count(*)" in sql
    assert "FROM review_miss_stats" in sql


@pytest.mark.asyncio
async def test_review_filters_are_student_scoped_missed_only_and_flatten_focus_keys():
    user = SimpleNamespace(id=12)
    aggregate = SimpleNamespace(
        source_types=["unknown", "diagnostic", None],
        source_test_names=["Bluebook 1", None],
        source_section_codes=["RW", None],
        source_module_codes=["M1", None],
        domains=["reading", "grammar", None],
        grammar_focus_keys=["commas", None],
        reading_focus_keys=["inference", None],
        reading_skill_family_keys=["information_and_ideas", "inference", None],
        stem_type_keys=["transitions", None],
        difficulties=["medium", None],
        content_origins=["official", None],
    )
    db = _QueueDB([_Result(first=user), _Result(row=aggregate)])

    response = await student_router.get_review_filters(
        user_token=USER_TOKEN,
        db=db,
        _auth="student-test-key",
    )

    assert response.source_types == ["diagnostic", "unknown"]
    assert response.focus_keys == ["commas", "inference", "information_and_ideas"]
    assert response.domains == ["grammar", "reading"]
    sql = _postgres_sql(db.statements[1])
    assert "user_progress.user_id" in sql
    assert "user_progress.is_correct = false" in sql
    assert "coalesce(user_progress.source_type" in sql


@pytest.mark.asyncio
async def test_review_filters_empty_state():
    user = SimpleNamespace(id=12)
    aggregate = SimpleNamespace(
        source_types=None,
        source_test_names=None,
        source_section_codes=None,
        source_module_codes=None,
        domains=None,
        grammar_focus_keys=None,
        reading_focus_keys=None,
        reading_skill_family_keys=None,
        stem_type_keys=None,
        difficulties=None,
        content_origins=None,
    )
    db = _QueueDB([_Result(first=user), _Result(row=aggregate)])

    response = await student_router.get_review_filters(
        user_token=USER_TOKEN,
        db=db,
        _auth="student-test-key",
    )

    assert response.model_dump() == {
        "source_types": [],
        "source_test_names": [],
        "source_section_codes": [],
        "source_module_codes": [],
        "domains": [],
        "focus_keys": [],
        "stem_type_keys": [],
        "difficulties": [],
        "content_origins": [],
    }


def test_review_routes_require_user_token_and_student_auth():
    review_route = next(
        route for route in student_router.router.routes
        if route.path == "/api/study/review"
    )
    filters_route = next(
        route for route in student_router.router.routes
        if route.path == "/api/study/review/filters"
    )

    for route in (review_route, filters_route):
        user_token = next(
            param for param in route.dependant.query_params
            if param.name == "user_token"
        )
        assert user_token.field_info.is_required() is True
        assert any(
            dependency.call is student_router.student_required
            for dependency in route.dependant.dependencies
        )
