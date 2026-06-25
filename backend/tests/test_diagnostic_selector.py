"""Tests for the diagnostic blueprint selector (TASK-B02). No live DB required."""

import uuid
import pytest
from types import SimpleNamespace

from app.diagnostic.blueprint import BLUEPRINT_V1, Slot
from app.diagnostic.selector import AssembledDiagnostic, ChosenQuestion, assemble_diagnostic


# ---------------------------------------------------------------------------
# Fake DB helpers (mirrors _QueueDB pattern from test_student_api_contracts.py)
# ---------------------------------------------------------------------------

def _qid():
    return str(uuid.uuid4())


def _make_question(qid=None):
    qid = qid or _qid()
    q = SimpleNamespace(id=qid)
    return q


class _ScalarIterable:
    """Iterates over a flat list of ORM-like objects for .scalars()."""

    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return iter(self._items)


class _RichDB:
    """Returns a configurable sequence of _ScalarIterable per execute() call.

    Each call pops the next result from the queue. If the queue is exhausted,
    returns an empty result (simulates no match — triggers next fallback level).
    """

    def __init__(self, call_results: list[list]):
        self._queue = [_ScalarIterable(items) for items in call_results]

    async def execute(self, _stmt):
        if self._queue:
            return self._queue.pop(0)
        return _ScalarIterable([])

    async def get(self, _model, _pk):
        return None

    def add(self, _obj):
        pass

    async def flush(self):
        pass

    async def commit(self):
        pass


def _make_blueprint_2_slots() -> tuple[Slot, ...]:
    """Minimal 2-slot blueprint for simple tests (avoids validate_blueprint constraints)."""
    return (
        Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),
        Slot(seq=2, difficulty="low", domain="reading", role_or_skill="inferences"),
    )


# ---------------------------------------------------------------------------
# Happy path — rich bank
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assembles_correct_number_of_slots():
    """Returns exactly len(blueprint) questions when bank is rich."""
    n = len(BLUEPRINT_V1)
    questions = [_make_question() for _ in range(n)]
    # Each slot will hit at fallback level 2 (first DB call per slot)
    db = _RichDB([[q] for q in questions])
    result = await assemble_diagnostic(db, user_id=1, blueprint=BLUEPRINT_V1)
    assert isinstance(result, AssembledDiagnostic)
    assert len(result.questions) == n


@pytest.mark.asyncio
async def test_no_duplicate_question_ids():
    """All returned question IDs are distinct."""
    n = len(BLUEPRINT_V1)
    questions = [_make_question() for _ in range(n)]
    db = _RichDB([[q] for q in questions])
    result = await assemble_diagnostic(db, user_id=1, blueprint=BLUEPRINT_V1)
    ids = [c.question_id for c in result.questions]
    assert len(ids) == len(set(ids))


@pytest.mark.asyncio
async def test_slot_order_preserved():
    """Chosen questions are in the same order as the blueprint slots."""
    n = len(BLUEPRINT_V1)
    questions = [_make_question() for _ in range(n)]
    db = _RichDB([[q] for q in questions])
    result = await assemble_diagnostic(db, user_id=1, blueprint=BLUEPRINT_V1)
    for i, cq in enumerate(result.questions):
        assert cq.slot.seq == BLUEPRINT_V1[i].seq


@pytest.mark.asyncio
async def test_coverage_report_present():
    """coverage_report dict is populated."""
    n = len(BLUEPRINT_V1)
    questions = [_make_question() for _ in range(n)]
    db = _RichDB([[q] for q in questions])
    result = await assemble_diagnostic(db, user_id=1, blueprint=BLUEPRINT_V1)
    report = result.coverage_report
    assert report["total"] == n
    assert "fallback_level_distribution" in report
    assert "gaps" in report


# ---------------------------------------------------------------------------
# Fallback ladder behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_when_first_call_empty():
    """When level 2 returns nothing, level 3 (drop difficulty) is tried."""
    bp = _make_blueprint_2_slots()
    q1 = _make_question()
    q2 = _make_question()
    # Slot 1: level-2 empty → level-3 hit; Slot 2: level-2 hit
    db = _RichDB([
        [],         # slot 1, level 2 — miss
        [q1],       # slot 1, level 3 — hit
        [q2],       # slot 2, level 2 — hit
    ])
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp)
    assert len(result.questions) == 2
    assert result.questions[0].fallback_level == 3
    assert result.questions[1].fallback_level == 2


@pytest.mark.asyncio
async def test_fallback_all_levels_gap():
    """When levels 2-5 all miss, level 6 sets gap=True.

    Fallback ladder makes exactly 5 DB calls: levels 2, 3, 4, 5, 6.
    """
    bp = (Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),)
    q1 = _make_question()
    # 4 misses (levels 2-5), then hit at level 6
    db = _RichDB([[], [], [], [], [q1]])
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp)
    assert result.questions[0].gap is True
    assert result.questions[0].fallback_level == 6
    assert result.coverage_report["gaps"] == 1


@pytest.mark.asyncio
async def test_exhausted_bank_raises():
    """RuntimeError raised when even level-6 returns nothing."""
    bp = (Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),)
    db = _RichDB([])  # all calls empty
    with pytest.raises(RuntimeError, match="Bank exhausted"):
        await assemble_diagnostic(db, user_id=1, blueprint=bp)


# ---------------------------------------------------------------------------
# Deduplication — same question not chosen twice
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_question_not_chosen_twice():
    """If the same question appears in multiple slot results, it is only chosen once."""
    shared = _make_question()
    q2 = _make_question()
    bp = _make_blueprint_2_slots()
    # Both slots would return shared first, then q2 as alternative
    db = _RichDB([
        [shared],        # slot 1 level 2 → takes shared
        [shared, q2],    # slot 2 level 2 → shared already chosen, takes q2
    ])
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp)
    ids = [c.question_id for c in result.questions]
    assert len(set(ids)) == 2
    assert str(shared.id) in ids
    assert str(q2.id) in ids


# ---------------------------------------------------------------------------
# exclude_seen flag
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exclude_seen_false_does_not_crash():
    """exclude_seen=False still assembles normally."""
    n = 2
    bp = _make_blueprint_2_slots()
    questions = [_make_question() for _ in range(n)]
    db = _RichDB([[q] for q in questions])
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp, exclude_seen=False)
    assert len(result.questions) == n


# ---------------------------------------------------------------------------
# coverage_report accuracy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coverage_report_no_gaps():
    bp = _make_blueprint_2_slots()
    db = _RichDB([[_make_question()] for _ in range(2)])
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp)
    assert result.coverage_report["gaps"] == 0
    assert result.coverage_report["gap_slots"] == []


@pytest.mark.asyncio
async def test_coverage_report_with_gap():
    bp = (Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),)
    q = _make_question()
    db = _RichDB([[], [], [], [], [q]])  # 4 misses then gap hit at level 6
    result = await assemble_diagnostic(db, user_id=1, blueprint=bp)
    assert result.coverage_report["gaps"] == 1
    assert result.coverage_report["gap_slots"] == [1]
