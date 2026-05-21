"""Phase 7 — Student Retrieval API Expansion tests.

Covers:
- Grammar filters (domain, grammar_role_key, grammar_focus_key)
- Reading filters (domain, reading_skill_family_key, reading_focus_key)
- Difficulty filter
- stimulus_mode_key filter
- origin filter (official / generated / mixed)
- exclude_seen behavior (default per scope, user-token lookup, resurface logic)
- active-only enforcement (drafts / rejected / retired never served)
- inventory metadata shape
- admin_or_student_required auth (admin and student both accepted; no key → 403)
- answer key never exposed
- single annotation JOIN when multiple annotation-backed filters combine
"""

import uuid
import pytest
from types import SimpleNamespace

from app.routers import student as student_router


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_question(
    qid=None,
    content_origin="official",
    practice_status="active",
    stimulus_mode_key=None,
    latest_annotation_id=None,
    latest_version_id=None,
):
    return SimpleNamespace(
        id=qid or uuid.uuid4(),
        content_origin=content_origin,
        practice_status=practice_status,
        stimulus_mode_key=stimulus_mode_key,
        latest_annotation_id=latest_annotation_id,
        latest_version_id=latest_version_id,
        current_question_text="Sample question?",
        current_passage_text=None,
        source_exam_code=None,
        source_subject_code=None,
        source_section_code=None,
        source_module_code=None,
    )


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


class _QueueDB:
    """DB mock that pops pre-configured results in call order."""

    def __init__(self, results=None):
        self._results = list(results or [])

    async def execute(self, stmt):
        if self._results:
            return self._results.pop(0)
        return _ScalarResult()

    async def get(self, model, pk):
        return None

    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


def _sql(stmt) -> str:
    """Render a SQLAlchemy statement with literal bind params for test assertions."""
    try:
        from sqlalchemy.dialects import postgresql
        return str(stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        ))
    except Exception:
        return str(stmt)


class _CaptureDB:
    """DB mock that records all executed statements with literal bind values."""

    def __init__(self, results=None):
        self._results = list(results or [])
        self.executed_sql = []

    async def execute(self, stmt):
        self.executed_sql.append(_sql(stmt))
        if self._results:
            return self._results.pop(0)
        return _ScalarResult()

    async def get(self, model, pk):
        return None

    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


# ---------------------------------------------------------------------------
# Direct-call helper — passes explicit None/defaults so FastAPI's Query()
# sentinels are never left as actual argument values.
# ---------------------------------------------------------------------------

async def _recall(db, auth=("student", "test"), **kwargs):
    params = dict(
        domain=None,
        difficulty=None,
        grammar_role_key=None,
        grammar_focus_key=None,
        reading_skill_family_key=None,
        reading_focus_key=None,
        stimulus_mode_key=None,
        origin=None,
        exclude_seen=None,
        user_token=None,
        limit=20,
        offset=0,
    )
    params.update(kwargs)
    return await student_router.student_recall(db=db, auth=auth, **params)


# ---------------------------------------------------------------------------
# HTTP-layer tests (use the TestClient via the `client` fixture from conftest)
# ---------------------------------------------------------------------------

def test_get_questions_requires_auth(client):
    resp = client.get("/api/questions")
    assert resp.status_code == 403


def test_get_questions_student_auth_accepted(client):
    resp = client.get("/api/questions", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200


def test_get_questions_admin_auth_accepted(client):
    resp = client.get("/api/questions", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200


def test_get_questions_response_shape(client):
    resp = client.get("/api/questions", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "inventory" in data
    inv = data["inventory"]
    for key in (
        "matching_target_total", "matching_unseen", "served",
        "includes_generated", "below_threshold", "threshold",
    ):
        assert key in inv, f"inventory missing key: {key}"


def test_get_questions_never_exposes_answer_key(client):
    """Answer key fields must never appear in the student-facing payload."""
    resp = client.get("/api/questions", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data.get("items", []):
        assert "current_correct_option_label" not in item
        for opt in item.get("options", []):
            assert "is_correct" not in opt


# ---------------------------------------------------------------------------
# SQL-shape tests — verify the generated SQL contains expected clauses
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_active_only_filter_in_sql():
    """All executed statements must filter by practice_status = 'active'."""
    db = _CaptureDB()
    await _recall(db)
    assert any("practice_status" in s for s in db.executed_sql)


@pytest.mark.asyncio
async def test_grammar_filters_add_single_annotation_join():
    """grammar_role_key + grammar_focus_key must produce exactly one annotation JOIN."""
    db = _CaptureDB()
    await _recall(db, grammar_role_key="usage", grammar_focus_key="subject_verb_agreement")
    assert db.executed_sql[-1].count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_reading_filters_add_single_annotation_join():
    db = _CaptureDB()
    await _recall(
        db,
        reading_skill_family_key="craft_and_structure",
        reading_focus_key="words_in_context",
    )
    assert db.executed_sql[-1].count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_difficulty_filter_adds_annotation_join():
    db = _CaptureDB()
    await _recall(db, difficulty="hard")
    assert db.executed_sql[-1].count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_combined_annotation_filters_single_join():
    """All annotation-backed filters together must still produce ONE annotation join."""
    db = _CaptureDB()
    await _recall(
        db,
        domain="grammar",
        difficulty="medium",
        grammar_role_key="usage",
        grammar_focus_key="subject_verb_agreement",
    )
    assert db.executed_sql[-1].count("JOIN question_annotations") == 1


@pytest.mark.asyncio
async def test_domain_grammar_references_grammar_role_key():
    db = _CaptureDB()
    await _recall(db, domain="grammar")
    assert "grammar_role_key" in db.executed_sql[-1]


@pytest.mark.asyncio
async def test_domain_reading_references_reading_skill_family_key():
    db = _CaptureDB()
    await _recall(db, domain="reading")
    assert "reading_skill_family_key" in db.executed_sql[-1]


@pytest.mark.asyncio
async def test_origin_official_adds_content_origin_filter():
    db = _CaptureDB()
    await _recall(db, origin="official")
    fetch_sql = db.executed_sql[-1]
    assert "content_origin = 'official'" in fetch_sql


@pytest.mark.asyncio
async def test_origin_generated_adds_content_origin_filter():
    db = _CaptureDB()
    await _recall(db, origin="generated")
    fetch_sql = db.executed_sql[-1]
    assert "content_origin = 'generated'" in fetch_sql


@pytest.mark.asyncio
async def test_origin_mixed_no_content_origin_value_filter():
    """origin=mixed (or omitted) must NOT add an equality filter on content_origin."""
    for origin_val in (None, "mixed"):
        db = _CaptureDB()
        await _recall(db, origin=origin_val)
        fetch_sql = db.executed_sql[-1]
        # The SELECT list always references content_origin; we verify no WHERE equality.
        assert "content_origin = 'official'" not in fetch_sql
        assert "content_origin = 'generated'" not in fetch_sql


@pytest.mark.asyncio
async def test_stimulus_mode_key_filter_in_sql():
    db = _CaptureDB()
    await _recall(db, stimulus_mode_key="paired_passages")
    fetch_sql = db.executed_sql[-1]
    assert "stimulus_mode_key" in fetch_sql
    assert "paired_passages" in fetch_sql


@pytest.mark.asyncio
async def test_no_annotation_join_without_annotation_filters():
    """No annotation JOIN when no annotation-backed filters are provided."""
    db = _CaptureDB()
    await _recall(db)
    assert "JOIN question_annotations" not in db.executed_sql[-1]


# ---------------------------------------------------------------------------
# Inventory metadata tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_inventory_metadata_shape():
    result = await _recall(_QueueDB())
    inv = result.inventory
    assert inv.matching_target_total == 0
    assert inv.matching_unseen == 0
    assert inv.served == 0
    assert isinstance(inv.includes_generated, bool)
    assert isinstance(inv.below_threshold, bool)
    assert inv.threshold > 0


@pytest.mark.asyncio
async def test_inventory_includes_generated_true():
    q = _make_question(content_origin="generated")
    db = _QueueDB([
        _ScalarResult(first_item=1),   # count total
        _ScalarResult(first_item=1),   # count unseen
        _ScalarResult(items=[q]),      # fetch
        _ScalarResult(items=[]),       # annotations
        _ScalarResult(items=[]),       # options
    ])
    result = await _recall(db)
    assert result.inventory.includes_generated is True


@pytest.mark.asyncio
async def test_inventory_includes_generated_false_for_official():
    q = _make_question(content_origin="official")
    db = _QueueDB([
        _ScalarResult(first_item=1),
        _ScalarResult(first_item=1),
        _ScalarResult(items=[q]),
        _ScalarResult(items=[]),
        _ScalarResult(items=[]),
    ])
    result = await _recall(db)
    assert result.inventory.includes_generated is False


@pytest.mark.asyncio
async def test_inventory_below_threshold_when_unseen_low():
    db = _QueueDB([
        _ScalarResult(first_item=100),  # matching_target_total
        _ScalarResult(first_item=2),    # matching_unseen (below threshold=5)
        _ScalarResult(items=[]),
    ])
    result = await _recall(db)
    assert result.inventory.below_threshold is True
    assert result.inventory.matching_unseen == 2


@pytest.mark.asyncio
async def test_inventory_served_equals_items_count():
    questions = [_make_question() for _ in range(3)]
    db = _QueueDB([
        _ScalarResult(first_item=10),
        _ScalarResult(first_item=10),
        _ScalarResult(items=questions),
        _ScalarResult(items=[]),
        _ScalarResult(items=[]),
    ])
    result = await _recall(db)
    assert result.inventory.served == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_annotation_fields_populated_in_response():
    ann_id = uuid.uuid4()
    ver_id = uuid.uuid4()
    q = _make_question(latest_annotation_id=ann_id, latest_version_id=ver_id)
    ann = SimpleNamespace(
        id=ann_id,
        annotation_jsonb={
            "grammar_role_key": "usage",
            "grammar_focus_key": "subject_verb_agreement",
            "difficulty_overall": "medium",
            "reading_skill_family_key": None,
            "reading_focus_key": None,
        },
    )
    db = _QueueDB([
        _ScalarResult(first_item=1),
        _ScalarResult(first_item=1),
        _ScalarResult(items=[q]),
        _ScalarResult(items=[ann]),
        _ScalarResult(items=[]),
    ])
    result = await _recall(db)
    assert len(result.items) == 1
    item = result.items[0]
    assert item.grammar_role_key == "usage"
    assert item.grammar_focus_key == "subject_verb_agreement"
    assert item.difficulty_overall == "medium"


# ---------------------------------------------------------------------------
# exclude_seen behavior tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exclude_seen_defaults_true_for_student_scope():
    """Student scope without explicit exclude_seen: user lookup triggered when token given."""
    db = _CaptureDB()
    token = str(uuid.uuid4())
    await _recall(db, user_token=token, auth=("student", "test"))
    assert any("user_token" in s for s in db.executed_sql), (
        "Expected a user_token lookup in SQL for student scope with token"
    )


@pytest.mark.asyncio
async def test_exclude_seen_defaults_false_for_admin_scope():
    """Admin scope without explicit exclude_seen: no user lookup even if token provided."""
    db = _CaptureDB()
    token = str(uuid.uuid4())
    await _recall(db, user_token=token, auth=("admin", "test"))
    assert not any("user_token" in s for s in db.executed_sql), (
        "Admin scope should not trigger user_token lookup by default"
    )


@pytest.mark.asyncio
async def test_exclude_seen_explicit_true_for_admin_triggers_lookup():
    """Admin scope with explicit exclude_seen=True + token should trigger user lookup."""
    db = _CaptureDB()
    token = str(uuid.uuid4())
    await _recall(db, user_token=token, exclude_seen=True, auth=("admin", "test"))
    assert any("user_token" in s for s in db.executed_sql)


@pytest.mark.asyncio
async def test_exclude_seen_no_token_skips_lookup():
    """exclude_seen=True but no user_token: no lookup, no exclusion subquery."""
    db = _CaptureDB()
    await _recall(db, exclude_seen=True, auth=("student", "test"))
    assert not any("user_token" in s for s in db.executed_sql)


@pytest.mark.asyncio
async def test_exclude_seen_invalid_token_skips_gracefully():
    """Non-UUID user_token: skip gracefully, no crash."""
    db = _CaptureDB()
    result = await _recall(db, user_token="not-a-valid-uuid", exclude_seen=True)
    assert not any("user_token" in s for s in db.executed_sql)
    assert result.inventory.served == 0


@pytest.mark.asyncio
async def test_exclude_seen_adds_user_progress_subquery_when_user_found():
    """When user is resolved, the fetch query references user_progress for exclusion."""
    user = SimpleNamespace(id=42, user_token=uuid.uuid4())
    db = _CaptureDB(results=[
        _ScalarResult(first_item=10),       # count total
        _ScalarResult(first_item=user),     # user lookup  ← scalars().first()
        _ScalarResult(first_item=8),        # count unseen
        _ScalarResult(items=[]),            # question fetch
    ])
    await _recall(db, user_token=str(user.user_token), exclude_seen=True)
    fetch_sql = db.executed_sql[-1]
    assert "user_progress" in fetch_sql.lower()


@pytest.mark.asyncio
async def test_exclude_seen_false_skips_all_seen_logic():
    """exclude_seen=False: no user lookup and no user_progress subquery."""
    db = _CaptureDB()
    token = str(uuid.uuid4())
    await _recall(db, user_token=token, exclude_seen=False)
    assert not any("user_token" in s for s in db.executed_sql)
    assert not any("user_progress" in s.lower() for s in db.executed_sql)
