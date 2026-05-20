"""Phase 1 (generation factory) — batch endpoint, request validation,
idempotency, and source-id validation tests.

These tests use FastAPI dependency overrides to inject a stateful fake
session that captures inserts and supports a small subset of SELECT/DELETE
operations needed by the batch endpoint. They cover behavior without
requiring a live PostgreSQL connection.
"""

import uuid as _uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient


AUTH = {"X-API-Key": "admin-test-key"}


# ---------------------------------------------------------------------------
# Minimal in-memory session capable of supporting create_generation_batch.
# ---------------------------------------------------------------------------

class _Result:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeBatchSession:
    """In-memory session that records added rows and handles the SELECT /
    DELETE statements the batch endpoint issues.
    """

    def __init__(self, *, existing_questions=None, existing_annotations=None,
                 existing_idem=None,
                 pending_batch_count=0):
        # rows the endpoint adds during the request
        self.batches: list = []
        self.jobs: list = []
        self.idem_keys: list = []
        # rows present before the request
        self.existing_questions = existing_questions or {}
        self.existing_annotations = existing_annotations or {}
        self.existing_idem = list(existing_idem or [])
        self._pending_batch_count = pending_batch_count

    # ORM-style API used by FastAPI handler ---------------------------------

    def add(self, obj):
        cls = type(obj).__name__
        if cls == "GenerationBatch":
            if getattr(obj, "id", None) is None:
                obj.id = _uuid.uuid4()
            self.batches.append(obj)
        elif cls == "QuestionJob":
            self.jobs.append(obj)
        elif cls == "GenerationBatchIdempotencyKey":
            if getattr(obj, "id", None) is None:
                obj.id = _uuid.uuid4()
            self.idem_keys.append(obj)
        else:
            raise AssertionError(f"Unexpected add() for {cls}")

    async def flush(self):
        # batch.id was assigned in add(); nothing else to do.
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def get(self, model, pk):
        if model.__name__ == "GenerationBatch":
            for b in self.batches:
                if b.id == pk:
                    return b
        return None

    async def execute(self, stmt):
        # Best-effort interpreter of the specific statements the endpoint
        # issues. Inspect stmt.__class__.__name__ for routing.
        cls = stmt.__class__.__name__

        if cls == "Delete":
            # DELETE FROM generation_batch_idempotency_keys WHERE expires_at <= now
            now = datetime.now(timezone.utc)
            self.existing_idem = [
                row for row in self.existing_idem if row.expires_at > now
            ]
            return _Result([])

        # SELECT statements: poke at the description / column list.
        text = str(stmt).lower()

        if "from generation_batch_idempotency_keys" in text:
            # Find a non-expired key matching the WHERE filters we can infer
            # from the bind parameters. The endpoint only ever filters by
            # idempotency_key + requested_by + (optional) expiry.
            params = getattr(stmt, "compile", lambda: None)()
            return _Result(self.existing_idem)

        if "from generation_batches" in text:
            # Two distinct call sites:
            #   1) Idempotency replay -> by-id lookup, expects .first() to
            #      return the just-created batch.
            #   2) Pending-batch cap  -> status-IN count, expects
            #      .scalars().all() length.
            if self._pending_batch_count > 0:
                fakes = [
                    type("B", (), {"id": _uuid.uuid4()})()
                    for _ in range(self._pending_batch_count)
                ]
                return _Result(fakes)
            # Otherwise, return whatever batches the session knows about.
            # The replay path's .first() picks up the most recent; the cap
            # path's len(.all()) sees the current pending size.
            return _Result(self.batches)

        if "from questions" in text:
            # source_question_ids validation path
            return _Result(list(self.existing_questions.values()))

        if "from question_annotations" in text:
            return _Result(list(self.existing_annotations.values()))

        if "from question_jobs" in text:
            return _Result(self.jobs)

        return _Result([])


def _make_client(session: _FakeBatchSession) -> TestClient:
    from app.main import app
    from app.database import get_db

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def _release_client():
    from app.main import app
    from app.database import get_db
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Request validation — rules-doc completeness enforcement
# ---------------------------------------------------------------------------

def _grammar_body(**overrides):
    body = {
        "requested_count": 3,
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_frequency_band": "very_high",
        "difficulty_overall": "medium",
        "test_format_key": "digital_app_adaptive",
        "stimulus_mode_key": "sentence_only",
        "stem_type_key": "complete_the_text",
    }
    body.update(overrides)
    return body


def _reading_body(**overrides):
    body = {
        "requested_count": 2,
        "target_skill_family_key": "command_of_evidence_textual",
        "target_reading_focus_key": "evidence_supports_claim",
        "target_test_construct_key": "evidence_relation_precision",
        "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
        "target_distractor_pattern": ["a", "b", "c"],
        "passage_structure_pattern": "research_summary",
        "stimulus_mode_key": "prose_single",
        "stem_type_key": "choose_best_support",
        "difficulty_overall": "medium",
    }
    body.update(overrides)
    return body


def _fake_question(qid, *, domain="grammar", canonical=False, exam="1", number=1):
    return type(
        "Q",
        (),
        {
            "id": qid,
            "content_origin": "official",
            "practice_status": "active",
            "current_passage_text": "Reading passage" if domain == "reading" else None,
            "latest_annotation_id": _uuid.uuid4(),
            "is_canonical_source": canonical,
            "source_exam_code": exam,
            "source_question_number": number,
        },
    )()


def _fake_annotation(question, payload):
    return type(
        "A",
        (),
        {
            "id": question.latest_annotation_id,
            "question_id": question.id,
            "annotation_jsonb": payload,
        },
    )()


def test_batch_grammar_complete_request_creates_batch():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=_grammar_body(), headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["requested_count"] == 3
    assert len(body["job_ids"]) == 3
    assert body["idempotent_replay"] is False
    # 1 batch + 3 jobs added
    assert len(session.batches) == 1
    assert len(session.jobs) == 3
    assert session.batches[0].request_jsonb["requested_by"] == "admin"
    assert session.batches[0].request_jsonb["student_id"] is None
    assert session.batches[0].request_jsonb["requested_by_user_token"] is None
    # Per-job request lacks `requested_count` (batch-level metadata stripped)
    assert all("requested_count" not in j.generation_request_jsonb for j in session.jobs)
    assert all(j.generation_request_jsonb["requested_by"] == "admin" for j in session.jobs)
    assert all(j.generation_request_jsonb["provider_name"] for j in session.jobs)
    assert all(j.generation_request_jsonb["model_name"] for j in session.jobs)
    assert all(j.generation_request_jsonb["retry_attempt"] == 0 for j in session.jobs)
    assert all("seed" in j.generation_request_jsonb for j in session.jobs)
    assert all(j.generation_request_jsonb["source_question_ids"] == [] for j in session.jobs)


def test_batch_reading_complete_request_creates_batch():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=_reading_body(), headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["requested_count"] == 2
    assert len(body["job_ids"]) == 2


def test_batch_rejects_unknown_release_policy():
    body = _grammar_body(release_policy="publish_now")
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "release_policy" in str(resp.json()["detail"])


def test_batch_caller_supplied_sources_are_frozen_on_each_job():
    source_id = _uuid.uuid4()
    source = _fake_question(source_id, domain="grammar")
    session = _FakeBatchSession(existing_questions={source_id: source})
    try:
        client = _make_client(session)
        resp = client.post(
            "/generate/batches",
            json=_grammar_body(source_question_ids=[str(source_id)]),
            headers=AUTH,
        )
    finally:
        _release_client()

    assert resp.status_code == 200, resp.text
    assert all(
        j.generation_request_jsonb["source_question_ids"] == [str(source_id)]
        for j in session.jobs
    )


def test_batch_auto_selects_rotated_official_sources_at_job_creation():
    q1 = _fake_question(_uuid.uuid4(), domain="grammar", exam="1", number=1)
    q2 = _fake_question(_uuid.uuid4(), domain="grammar", exam="2", number=2)
    q3 = _fake_question(_uuid.uuid4(), domain="grammar", exam="3", number=3)
    questions = {q.id: q for q in (q1, q2, q3)}
    annotations = {
        q.latest_annotation_id: _fake_annotation(
            q,
            {
                "grammar_role_key": "agreement",
                "grammar_focus_key": "subject_verb_agreement",
                "difficulty_overall": "medium",
            },
        )
        for q in (q1, q2, q3)
    }
    session = _FakeBatchSession(
        existing_questions=questions,
        existing_annotations=annotations,
    )
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=_grammar_body(), headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 200, resp.text
    source_sets = [
        tuple(j.generation_request_jsonb["source_question_ids"])
        for j in session.jobs
    ]
    assert all(len(source_ids) == 3 for source_ids in source_sets)
    assert len(set(source_sets)) > 1


def test_batch_grammar_missing_mandatory_field_rejected():
    body = _grammar_body()
    del body["target_frequency_band"]
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    detail = resp.json()["detail"]
    # Body of error mentions the missing field and the rules section
    msg = str(detail)
    assert "target_frequency_band" in msg
    assert "B.1.1" in msg


def test_batch_grammar_very_low_frequency_rejected():
    body = _grammar_body(target_frequency_band="very_low")
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "very_low" in str(resp.json()["detail"])


def test_batch_grammar_transition_logic_requires_subtype():
    body = _grammar_body(
        target_grammar_focus_key="transition_logic",
        target_grammar_role_key="transition_logic",
    )
    # Missing target_transition_subtype_key and distractor_transition_subtypes
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    detail = str(resp.json()["detail"])
    assert "target_transition_subtype_key" in detail
    assert "distractor_transition_subtypes" in detail


def test_batch_reading_missing_distractor_pattern_rejected():
    body = _reading_body()
    del body["target_distractor_pattern"]
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "target_distractor_pattern" in str(resp.json()["detail"])


def test_batch_reading_distractor_pattern_must_be_three_items():
    body = _reading_body(target_distractor_pattern=["a", "b"])
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "exactly 3" in str(resp.json()["detail"])


def test_batch_reading_polarity_fit_requires_polarity_context():
    body = _reading_body(target_reading_focus_key="polarity_fit")
    # Missing polarity_context
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "polarity_context" in str(resp.json()["detail"])


def test_batch_mixing_grammar_and_reading_rejected():
    body = _grammar_body()
    body["target_reading_focus_key"] = "evidence_supports_claim"
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "one domain" in str(resp.json()["detail"]).lower()


def test_batch_no_target_rejected():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post(
            "/generate/batches",
            json={"requested_count": 1, "difficulty_overall": "medium"},
            headers=AUTH,
        )
    finally:
        _release_client()

    assert resp.status_code == 422


def test_batch_requested_count_must_be_positive():
    body = _grammar_body(requested_count=0)
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422


def test_batch_requested_count_capped_by_config():
    """Above GENERATION_MAX_BATCH_SIZE returns 422 with a helpful detail."""
    body = _grammar_body(requested_count=999)
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 422
    assert "GENERATION_MAX_BATCH_SIZE" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_batch_idempotency_first_call_creates_then_second_replays():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        first = client.post(
            "/generate/batches",
            json=_grammar_body(),
            headers={**AUTH, "Idempotency-Key": "client-abc"},
        )
        # After first call, the in-memory session has one batch + one idem row.
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["idempotent_replay"] is False
        assert len(session.idem_keys) == 1

        # Move the just-created idem row into existing_idem so the second
        # request sees it via the SELECT path.
        session.existing_idem = list(session.idem_keys)
        session.idem_keys = []

        second = client.post(
            "/generate/batches",
            json=_grammar_body(requested_count=99),  # different body
            headers={**AUTH, "Idempotency-Key": "client-abc"},
        )
    finally:
        _release_client()

    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    # Replay returns the ORIGINAL batch id, not a new one
    assert second_body["id"] == first_body["id"]
    # No additional batch or jobs were created on replay
    assert len(session.batches) == 1


def test_batch_no_idempotency_header_opts_out():
    """Two POSTs without an Idempotency-Key create two distinct batches."""
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        r1 = client.post("/generate/batches", json=_grammar_body(), headers=AUTH)
        r2 = client.post("/generate/batches", json=_grammar_body(), headers=AUTH)
    finally:
        _release_client()

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] != r2.json()["id"]
    assert r1.json()["idempotent_replay"] is False
    assert r2.json()["idempotent_replay"] is False


# ---------------------------------------------------------------------------
# Pending-batch cap
# ---------------------------------------------------------------------------

def test_batch_pending_cap_returns_429():
    session = _FakeBatchSession(pending_batch_count=1000)
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=_grammar_body(), headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 429
    assert "GENERATION_MAX_PENDING_BATCHES" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Source-question-id validation
# ---------------------------------------------------------------------------

def test_batch_invalid_source_uuid_rejected():
    body = _grammar_body(source_question_ids=["not-a-uuid"])
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 400
    assert "Invalid source_question_id" in resp.json()["detail"]


def test_batch_unknown_source_id_rejected():
    src_id = _uuid.uuid4()
    body = _grammar_body(source_question_ids=[str(src_id)])
    # No matching question in session
    session = _FakeBatchSession(existing_questions={})
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "unknown" in detail["error"].lower()
    assert str(src_id) in detail["missing"]


def test_batch_non_official_source_id_rejected():
    src_id = _uuid.uuid4()
    fake_q = type(
        "Q", (),
        {"id": src_id, "content_origin": "generated", "current_passage_text": None},
    )()
    body = _grammar_body(source_question_ids=[str(src_id)])
    session = _FakeBatchSession(existing_questions={src_id: fake_q})
    try:
        client = _make_client(session)
        resp = client.post("/generate/batches", json=body, headers=AUTH)
    finally:
        _release_client()

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "official" in detail["error"].lower()
    assert str(src_id) in detail["non_official"]


def test_batch_annotation_domain_mismatch_rejected():
    src_id = _uuid.uuid4()
    source = _fake_question(src_id, domain="reading")
    annotation = _fake_annotation(
        source,
        {
            "reading_skill_family_key": "command_of_evidence_textual",
            "reading_focus_key": "evidence_supports_claim",
        },
    )
    session = _FakeBatchSession(
        existing_questions={src_id: source},
        existing_annotations={annotation.id: annotation},
    )
    try:
        client = _make_client(session)
        resp = client.post(
            "/generate/batches",
            json=_grammar_body(source_question_ids=[str(src_id)]),
            headers=AUTH,
        )
    finally:
        _release_client()

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "mismatch" in detail["error"]
    assert str(src_id) in detail["mismatched"]


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------

def test_get_batch_not_found_returns_404():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.get(
            f"/generate/batches/{_uuid.uuid4()}",
            headers=AUTH,
        )
    finally:
        _release_client()
    assert resp.status_code == 404


def test_get_batch_invalid_uuid_returns_400():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.get("/generate/batches/not-a-uuid", headers=AUTH)
    finally:
        _release_client()
    assert resp.status_code == 400


def test_get_batch_questions_invalid_uuid_returns_400():
    session = _FakeBatchSession()
    try:
        client = _make_client(session)
        resp = client.get("/generate/batches/not-a-uuid/questions", headers=AUTH)
    finally:
        _release_client()
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Backward compatibility — legacy /generate/questions still works
# ---------------------------------------------------------------------------

def test_legacy_generate_questions_endpoint_still_accepted(client):
    """Phase 1 must not break the one-off admin generation endpoint."""
    resp = client.post(
        "/generate/questions",
        headers={**AUTH, "Content-Type": "application/json"},
        json={
            "target_grammar_role_key": "agreement",
            "target_grammar_focus_key": "subject_verb_agreement",
            "target_syntactic_trap_key": "none",
            "difficulty_overall": "medium",
        },
    )
    # The endpoint may return 200 or 500 depending on environment; what
    # matters here is that the legacy looser validation is still in place
    # (no 422 against the simpler body that Phase 1's batch endpoint
    # would now reject).
    assert resp.status_code != 422
