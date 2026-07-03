AUTH = {"X-API-Key": "admin-test-key"}


def test_admin_edit_invalid_uuid(client):
    resp = client.patch(
        "/admin/questions/not-a-uuid",
        json={"question_text": "new text"},
        headers=AUTH,
    )
    assert resp.status_code == 400


def test_admin_edit_not_found(client):
    resp = client.patch(
        "/admin/questions/00000000-0000-0000-0000-000000000000",
        json={"question_text": "new text"},
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_approve_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/approve",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_reject_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/reject",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_generated_questions_list_empty(client):
    resp = client.get("/admin/generated-questions", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "limit": 25, "offset": 0, "next_offset": None}


def test_admin_reject_is_non_destructive(monkeypatch):
    """Rejecting a question flips practice_status to 'rejected', records the
    reason/timestamp/admin token, and does NOT delete linked evaluations,
    annotations, relations, or option annotation fields.
    """
    import uuid as _uuid
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient

    from app.main import app
    from app.database import get_db
    from app.routers import admin as admin_router

    qid = _uuid.uuid4()

    class FakeQuestion:
        def __init__(self):
            self.id = qid
            self.practice_status = "draft"
            self.rejection_reason = None
            self.rejected_at = None
            self.rejected_by_admin_token = None
            self.updated_at = datetime.now(timezone.utc)
            self.latest_annotation_id = _uuid.uuid4()

    fake_q = FakeQuestion()
    execute_calls = []

    class FakeSession:
        async def get(self, model, pk):
            if pk == qid:
                return fake_q
            return None

        async def execute(self, stmt):
            # Phase 6 may read review-run rows to capture reviewer/admin
            # agreement, but the reject path must not delete or clear linked
            # evidence rows.
            execute_calls.append(stmt)

            class _R:
                def scalars(self_inner):
                    return self_inner

                def all(self_inner):
                    return []

                def first(self_inner):
                    return None

                def unique(self_inner):
                    return self_inner

            return _R()

        async def flush(self):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

        def add(self, obj):
            pass

    fake = FakeSession()

    async def _override_get_db():
        yield fake

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post(
                f"/admin/questions/{qid}/reject",
                json={"reason": "off-topic stimulus"},
                headers=AUTH,
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["practice_status"] == "rejected"
    assert body["rejection_reason"] == "off-topic stimulus"
    assert body["rejected_at"] is not None

    # In-memory state on the fake row reflects the metadata-only update
    assert fake_q.practice_status == "rejected"
    assert fake_q.rejection_reason == "off-topic stimulus"
    assert fake_q.rejected_at is not None
    assert fake_q.rejected_by_admin_token == "admin-test-key"
    # The destructive path used to null this — confirm it stays set
    assert fake_q.latest_annotation_id is not None

    assert body["reviewer_admin_override_count"] == 0
    assert not any(stmt.__class__.__name__ == "Delete" for stmt in execute_calls), (
        "Rejection must not issue DELETE against linked tables; "
        f"saw {len(execute_calls)} statement(s)."
    )


def test_admin_reject_accepts_empty_body(monkeypatch):
    """Reject must work even when no reason is supplied (body is optional)."""
    import uuid as _uuid
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient

    from app.main import app
    from app.database import get_db

    qid = _uuid.uuid4()

    class FakeQuestion:
        def __init__(self):
            self.id = qid
            self.practice_status = "draft"
            self.rejection_reason = None
            self.rejected_at = None
            self.rejected_by_admin_token = None
            self.updated_at = datetime.now(timezone.utc)
            self.latest_annotation_id = None

    fake_q = FakeQuestion()

    class FakeSession:
        async def get(self, model, pk):
            return fake_q if pk == qid else None

        async def execute(self, stmt):
            class _R:
                def scalars(self_inner):
                    return self_inner

                def all(self_inner):
                    return []

                def first(self_inner):
                    return None

                def unique(self_inner):
                    return self_inner

            return _R()

        async def flush(self):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

        def add(self, obj):
            pass

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post(f"/admin/questions/{qid}/reject", headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json()["practice_status"] == "rejected"
    assert resp.json()["rejection_reason"] is None


def test_admin_confirm_overlap_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/confirm-overlap",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_clear_overlap_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/clear-overlap",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_eval_score_not_found(client):
    resp = client.post(
        "/admin/evaluations/00000000-0000-0000-0000-000000000000/score",
        json={"score_overall": 8.0},
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_amendments_list(client, monkeypatch):
    from app.routers import admin as admin_router

    monkeypatch.setattr(
        admin_router.amendment_review,
        "list_amendments",
        lambda: [{"amendment_id": "amd-test", "status": "pending"}],
    )

    resp = client.get("/admin/amendments", headers=AUTH)

    assert resp.status_code == 200
    assert resp.json()[0]["amendment_id"] == "amd-test"


def test_admin_amendment_show_not_found(client, monkeypatch):
    from app.routers import admin as admin_router

    monkeypatch.setattr(
        admin_router.amendment_review,
        "load_amendment_by_id",
        lambda amendment_id: admin_router.amendment_review.AmendmentOperationResult(
            ok=False,
            error="Amendment not found",
            error_code="not_found",
        ),
    )

    resp = client.get("/admin/amendments/missing", headers=AUTH)

    assert resp.status_code == 404


def test_admin_amendment_validation_error_returns_422(client, monkeypatch):
    from app.routers import admin as admin_router

    monkeypatch.setattr(
        admin_router.amendment_review,
        "approve_amendment",
        lambda amendment_id, reviewer, notes: admin_router.amendment_review.AmendmentOperationResult(
            ok=False,
            error="Proposed key is already active",
            error_code="validation",
        ),
    )

    resp = client.post("/admin/amendments/amd-test/approve", headers=AUTH)

    assert resp.status_code == 422


def test_admin_amendment_approve(client, monkeypatch):
    from app.routers import admin as admin_router

    class Amendment:
        def to_file_dict(self):
            return {"amendment_id": "amd-test", "status": "approved"}

    monkeypatch.setattr(
        admin_router.amendment_review,
        "approve_amendment",
        lambda amendment_id, reviewer, notes: admin_router.amendment_review.AmendmentOperationResult(
            ok=True,
            amendment=Amendment(),
        ),
    )

    resp = client.post(
        "/admin/amendments/amd-test/approve",
        json={"reviewer": "tester", "notes": "ok"},
        headers=AUTH,
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_admin_amendment_reject(client, monkeypatch):
    from app.routers import admin as admin_router

    class Amendment:
        def to_file_dict(self):
            return {"amendment_id": "amd-test", "status": "rejected"}

    monkeypatch.setattr(
        admin_router.amendment_review,
        "reject_amendment",
        lambda amendment_id, reviewer, notes: admin_router.amendment_review.AmendmentOperationResult(
            ok=True,
            amendment=Amendment(),
        ),
    )

    resp = client.post("/admin/amendments/amd-test/reject", headers=AUTH)

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_admin_amendment_request_more_evidence(client, monkeypatch):
    from app.routers import admin as admin_router

    class Amendment:
        def to_file_dict(self):
            return {"amendment_id": "amd-test", "status": "more_evidence_requested"}

    monkeypatch.setattr(
        admin_router.amendment_review,
        "request_more_evidence",
        lambda amendment_id, reviewer, notes: admin_router.amendment_review.AmendmentOperationResult(
            ok=True,
            amendment=Amendment(),
        ),
    )

    resp = client.post("/admin/amendments/amd-test/request-more-evidence", headers=AUTH)

    assert resp.status_code == 200
    assert resp.json()["status"] == "more_evidence_requested"


def test_admin_amendment_promote(client, monkeypatch):
    from app.routers import admin as admin_router

    class Amendment:
        def to_file_dict(self):
            return {"amendment_id": "amd-test", "status": "promoted"}

    monkeypatch.setattr(
        admin_router.amendment_review,
        "promote_amendment",
        lambda amendment_id, reviewer, notes: admin_router.amendment_review.AmendmentOperationResult(
            ok=True,
            amendment=Amendment(),
        ),
    )

    resp = client.post("/admin/amendments/amd-test/promote", headers=AUTH)

    assert resp.status_code == 200
    assert resp.json()["status"] == "promoted"


def _amendment_repo(tmp_path):
    """Build a real on-disk repo layout for amendment integration tests."""
    import json

    for name in ("pending", "approved", "rejected", "needs_manual_patch"):
        (tmp_path / "vocabulary" / "amendments" / name).mkdir(parents=True)
    (tmp_path / "rules_agent_dsat_reading_v3.md").write_text(
        "\n".join([
            "# Reading Rules",
            "",
            "## Reading focus keys",
            "- `central_idea` - Existing central idea guidance.",
            "",
            "<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY START -->",
            "- `central_idea`",
            "<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY END -->",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "rules_agent_dsat_grammar_ingestion_generation_v8.md").write_text(
        "# Grammar Rules\n", encoding="utf-8"
    )
    master = {
        "schema_version": 1,
        "vocabularies": [
            {
                "name": "READING_SKILL_FAMILY_KEYS",
                "kind": "flat",
                "entries": [{
                    "value": "information_and_ideas",
                    "status": "active",
                    "added": "2026-05-18",
                    "description": "",
                }],
            },
            {
                "name": "READING_FOCUS_BY_SKILL_FAMILY",
                "kind": "hierarchical",
                "parent_set": "READING_SKILL_FAMILY_KEYS",
                "entries": [{
                    "value": "central_idea",
                    "parent": "information_and_ideas",
                    "status": "active",
                    "added": "2026-05-18",
                    "description": "",
                }],
            },
        ],
    }
    (tmp_path / "vocabulary" / "master.json").write_text(
        json.dumps(master, indent=2) + "\n", encoding="utf-8"
    )
    (tmp_path / "vocabulary" / "candidates.json").write_text(
        json.dumps({"schema_version": 1, "candidates": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def _amendment_payload(**overrides):
    payload = {
        "amendment_id": "amd-int",
        "source_job_id": "job-1",
        "source_exam_code": "PT04",
        "source_subject_code": "verbal",
        "source_section_code": "01",
        "source_module_code": "01",
        "source_question_number": 6,
        "content_origin": "official",
        "affected_doc": "reading",
        "proposal_type": "new_controlled_vocab_key",
        "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
        "proposed_value": "evidence_scope_shift",
        "parent_key": "information_and_ideas",
        "definition": "Evidence scope distinction.",
        "current_best_fit": "central_idea",
        "why_current_rules_are_insufficient": "Existing rules do not split evidence scope.",
        "official_evidence": "Official evidence.",
        "rule_doc_patch": {
            "target_section": "## Reading focus keys",
            "before": "- `central_idea` - Existing central idea guidance.",
            "after": (
                "- `central_idea` - Existing central idea guidance.\n"
                "- `evidence_scope_shift` - Evidence scope distinction."
            ),
            "rationale": "Official evidence requires it.",
        },
        "master_json_patch": {
            "affected_vocab": "READING_FOCUS_BY_SKILL_FAMILY",
            "proposed_value": "evidence_scope_shift",
            "parent_key": "information_and_ideas",
            "description": "Evidence scope distinction.",
        },
        "supporting_examples": [{
            "source_job_id": "job-1",
            "source_exam_code": "PT04",
            "source_subject_code": "verbal",
            "source_section_code": "01",
            "source_module_code": "01",
            "source_question_number": 6,
            "official_evidence": "Official evidence.",
        }],
    }
    payload.update(overrides)
    return payload


def _bind_repo(monkeypatch, repo):
    """Re-bind every amendment_review function default to a real tmp repo.

    Each amendment_review function takes a ``repo_root`` keyword that defaults
    to the module-level ``REPO_ROOT``. Wrapping every function in a
    ``functools.partial`` with ``repo_root`` pre-bound redirects both the
    router-level calls (which pass no ``repo_root``) and the internal
    function-to-function calls (which pass ``repo_root`` explicitly; partial
    keyword override keeps that consistent) at the genuine tmp repo. Unlike the
    canned-result stubs above, this exercises the real filesystem code paths,
    status transitions, and amendment file writes/moves.
    """
    import functools

    from app.routers import admin as admin_router

    module = admin_router.amendment_review
    for name in (
        "list_amendments",
        "load_amendment_by_id",
        "approve_amendment",
        "reject_amendment",
        "request_more_evidence",
        "promote_amendment",
    ):
        real = getattr(module, name)
        monkeypatch.setattr(module, name, functools.partial(real, repo_root=repo))


def test_admin_amendment_promote_flow_against_real_filesystem(client, monkeypatch, tmp_path):
    """End-to-end: approve then promote a real on-disk amendment via the router.

    Exercises the genuine amendment_review code paths (no canned results) so a
    miswired error-code mapping or file-move bug would fail here.
    """
    import json

    repo = _amendment_repo(tmp_path)
    pending = repo / "vocabulary" / "amendments" / "pending" / "amd-int.json"
    pending.write_text(json.dumps(_amendment_payload(), indent=2) + "\n", encoding="utf-8")

    # gen_vocab regeneration shells out; stub only that external step.
    monkeypatch.setattr(
        "app.pipeline.rule_doc_patcher.regenerate_vocab_appendices",
        lambda *, repo_root: __import__(
            "app.pipeline.rule_doc_patcher", fromlist=["RuleDocPatchResult"]
        ).RuleDocPatchResult(ok=True, amendment_id="", affected_doc="", doc_path=None),
    )
    monkeypatch.setattr(
        "app.pipeline.ingestion_analysis.write_reappraisals_for_master_growth",
        lambda *, repo_root: [],
    )
    _bind_repo(monkeypatch, repo)

    approve = client.post("/admin/amendments/amd-int/approve", headers=AUTH)
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    promote = client.post("/admin/amendments/amd-int/promote", headers=AUTH)
    assert promote.status_code == 200
    assert promote.json()["status"] == "promoted"

    assert not pending.exists()
    assert (repo / "vocabulary" / "amendments" / "approved" / "amd-int.json").exists()
    master = json.loads((repo / "vocabulary" / "master.json").read_text(encoding="utf-8"))
    focus = next(v for v in master["vocabularies"] if v["name"] == "READING_FOCUS_BY_SKILL_FAMILY")
    assert any(e["value"] == "evidence_scope_shift" for e in focus["entries"])
    doc = (repo / "rules_agent_dsat_reading_v3.md").read_text(encoding="utf-8")
    assert "`evidence_scope_shift`" in doc


def test_admin_amendment_promote_unapproved_returns_422_real_filesystem(client, monkeypatch, tmp_path):
    """Promoting a still-pending amendment hits the real status guard -> 422."""
    import json

    repo = _amendment_repo(tmp_path)
    pending = repo / "vocabulary" / "amendments" / "pending" / "amd-int.json"
    pending.write_text(json.dumps(_amendment_payload(), indent=2) + "\n", encoding="utf-8")
    _bind_repo(monkeypatch, repo)

    resp = client.post("/admin/amendments/amd-int/promote", headers=AUTH)

    assert resp.status_code == 422
    assert "approved before promotion" in resp.json()["detail"]["error"]
    # File untouched - still pending.
    assert pending.exists()


def test_admin_relations_list_accepts_pagination(client):
    resp = client.get("/admin/relations?limit=10&offset=0", headers=AUTH)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_admin_relations_list_rejects_zero_limit(client):
    resp = client.get("/admin/relations?limit=0", headers=AUTH)
    assert resp.status_code == 422


def test_admin_list_questions_includes_annotation_stale(monkeypatch):
    import uuid as _uuid
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class FakeQuestion:
        def __init__(self):
            self.id = _uuid.uuid4()
            self.content_origin = "official"
            self.practice_status = "active"
            self.official_overlap_status = None
            self.source_release_year = 2024
            self.source_test_name = "Test_4"
            self.source_exam_code = None
            self.source_subject_code = None
            self.source_section_code = None
            self.source_module_code = None
            self.source_question_number = 1
            self.current_passage_text = None
            self.current_question_text = "Sample question text"
            self.current_correct_option_label = "A"
            self.current_explanation_text = None
            self.is_admin_edited = True
            self.annotation_stale = True
            self.latest_annotation_id = None
            self.latest_version_id = None
            self.created_at = datetime.now(timezone.utc)

    fake_q = FakeQuestion()

    class _Result:
        def unique(self):
            return self

        def scalars(self):
            return self

        def all(self):
            return [fake_q]

    class FakeSession:
        async def execute(self, stmt):
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get("/admin/questions", headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["annotation_stale"] is True


def test_admin_list_questions_options_use_option_label_and_text_keys():
    import uuid as _uuid
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    version_id = _uuid.uuid4()
    option_id = _uuid.uuid4()

    class FakeQuestion:
        def __init__(self):
            self.id = _uuid.uuid4()
            self.content_origin = "official"
            self.practice_status = "active"
            self.official_overlap_status = None
            self.source_release_year = 2024
            self.source_test_name = "Test_4"
            self.source_exam_code = None
            self.source_subject_code = None
            self.source_section_code = None
            self.source_module_code = None
            self.source_question_number = 1
            self.current_passage_text = None
            self.current_question_text = "Sample question text"
            self.current_correct_option_label = "A"
            self.current_explanation_text = None
            self.is_admin_edited = False
            self.annotation_stale = False
            self.latest_annotation_id = None
            self.latest_version_id = version_id
            self.created_at = datetime.now(timezone.utc)

    fake_q = FakeQuestion()

    class FakeOption:
        def __init__(self):
            self.id = option_id
            self.question_version_id = version_id
            self.option_label = "A"
            self.option_text = "Sample option text"
            self.is_correct = True

    fake_opt = FakeOption()

    class _QuestionResult:
        def unique(self):
            return self

        def scalars(self):
            return self

        def all(self):
            return [fake_q]

    class _OptionResult:
        def scalars(self):
            return self

        def all(self):
            return [fake_opt]

    class FakeSession:
        def __init__(self):
            self.call_count = 0

        async def execute(self, stmt):
            self.call_count += 1
            if self.call_count == 1:
                return _QuestionResult()
            return _OptionResult()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get("/admin/questions", headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["options"] == [{
        "id": str(option_id),
        "option_label": "A",
        "option_text": "Sample option text",
        "is_correct": True,
    }]


def test_admin_list_questions_filters_by_subject_section_module_code():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    captured: dict = {}

    class _Result:
        def unique(self):
            return self

        def scalars(self):
            return self

        def all(self):
            return []

    class FakeSession:
        async def execute(self, stmt):
            captured["stmt"] = stmt
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get(
                "/admin/questions",
                params={
                    "source_subject_code": "verbal",
                    "source_section_code": "sec01",
                    "source_module_code": "mod02",
                },
                headers=AUTH,
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    compiled = str(captured["stmt"].compile(compile_kwargs={"literal_binds": True}))
    assert "source_subject_code" in compiled and "'verbal'" in compiled
    assert "source_section_code" in compiled and "'sec01'" in compiled
    assert "source_module_code" in compiled and "'mod02'" in compiled


def test_admin_list_tests_empty(client):
    resp = client.get("/admin/tests", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []


def test_admin_list_tests_aggregates_by_source():
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    fake_row = SimpleNamespace(
        source_release_year=2024,
        source_test_name="Test_4",
        source_exam_code="digital",
        source_subject_code="verbal",
        source_section_code="sec01",
        source_module_code="mod01",
        question_count=33,
        approved_count=30,
    )

    class _Result:
        def all(self):
            return [fake_row]

    class FakeSession:
        async def execute(self, stmt):
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get("/admin/tests", headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json() == [{
        "source_release_year": 2024,
        "source_test_name": "Test_4",
        "source_exam_code": "digital",
        "source_subject_code": "verbal",
        "source_section_code": "sec01",
        "source_module_code": "mod01",
        "question_count": 33,
        "approved_count": 30,
    }]
