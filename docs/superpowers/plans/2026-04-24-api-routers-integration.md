# API Routers + Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing LLM/parsers/pipeline layer to 19 FastAPI endpoints across 5 routers, enabling PDF ingestion, question generation, question recall, admin review, and student practice.

**Architecture:** Five router modules (ingest, generate, questions, admin, student) each mounted on a distinct prefix. All routers use the shared `get_db` session, `admin_required`/`student_required` auth, and the existing pipeline orchestrator + LLM factory. Read-only endpoints (questions, student) first, then admin mutations, then the complex async ingestion/generation pipeline.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, python-multipart (uploads), httpx

**Prerequisites:** Plans 1 (foundation) and 2 (LLM/parsers/pipeline) are fully implemented and tested. Docker Postgres on port 5434 with `alembic upgrade head` applied. 61 existing tests all pass.

---

## File Map

```
backend/app/routers/
├── __init__.py          # (exists)
├── health.py            # (exists, no change)
├── questions.py         # GET /questions/recall, GET /questions/{id}, GET /questions/{id}/versions
├── student.py           # GET /api/questions, POST /api/submit, GET /api/stats/{user_id}
├── admin.py             # PATCH + POST endpoints for review/approval/edit/overlap/eval
├── ingest.py            # POST endpoints for PDF upload, file upload, batch, reannotate
└── generate.py          # POST + GET endpoints for generation, comparison, run inspection

backend/app/models/payload.py  # (modify: add missing request/response models)
backend/app/main.py            # (modify: include all 5 new routers)
backend/tests/
├── test_questions_router.py
├── test_student_router.py
├── test_admin_router.py
├── test_ingest_router.py
└── test_generate_router.py
```

---

## Chunk 1: Read-Only Routers (Questions + Student)

### Task 1: Add missing request/response models to payload.py

**Files:**
- Modify: `backend/app/models/payload.py`
- Test: `backend/tests/test_schemas.py` (add validation tests)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_schemas.py`:

```python
def test_generation_request_valid():
    from app.models.payload import GenerationRequest
    req = GenerationRequest(
        target_grammar_role_key="agreement",
        target_grammar_focus_key="subject_verb_agreement",
        target_syntactic_trap_key="nearest_noun_attraction",
        difficulty_overall="medium",
    )
    assert req.target_grammar_focus_key == "subject_verb_agreement"


def test_generation_compare_request_valid():
    from app.models.payload import GenerationCompareRequest
    req = GenerationCompareRequest(
        target_grammar_role_key="agreement",
        target_grammar_focus_key="subject_verb_agreement",
        providers=["anthropic", "openai"],
    )
    assert len(req.providers) == 2


def test_job_response_model():
    from app.models.payload import JobResponse
    j = JobResponse(id="abc-123", job_type="ingest", status="parsing", question_id=None)
    assert j.status == "parsing"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_schemas.py::test_generation_request_valid -v`
Expected: FAIL (import error)

- [ ] **Step 3: Write implementation**

Add to `app/models/payload.py`:

```python
class GenerationRequest(BaseModel):
    target_grammar_role_key: str
    target_grammar_focus_key: str
    target_syntactic_trap_key: str = "none"
    difficulty_overall: str = "medium"
    source_question_ids: Optional[List[str]] = None


class GenerationCompareRequest(BaseModel):
    target_grammar_role_key: str
    target_grammar_focus_key: str
    target_syntactic_trap_key: str = "none"
    difficulty_overall: str = "medium"
    providers: List[str] = Field(default_factory=lambda: ["anthropic"])
    source_question_ids: Optional[List[str]] = None


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    question_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IngestPdfRequest(BaseModel):
    source_exam_code: Optional[str] = None
    source_module_code: Optional[str] = None
    provider_name: str = "anthropic"
    model_name: str = "claude-sonnet-4-6"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/payload.py backend/tests/test_schemas.py
git commit -m "feat: add generation, comparison, and job response payload models"
```

---

### Task 2: Create Questions router (3 endpoints)

**Files:**
- Create: `backend/app/routers/questions.py`
- Create: `backend/tests/test_questions_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_questions_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_recall_empty(client):
    resp = await client.get("/questions/recall", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_question_detail_not_found(client):
    resp = await client.get("/questions/00000000-0000-0000-0000-000000000000", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_question_versions_not_found(client):
    resp = await client.get("/questions/00000000-0000-0000-0000-000000000000/versions", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_questions_router.py -v`
Expected: FAIL (404 — route not registered)

- [ ] **Step 3: Write implementation**

```python
# app/routers/questions.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.auth import admin_required
from app.models.db import Question, QuestionVersion, QuestionAnnotation, QuestionOption
from app.models.payload import QuestionRecallResponse, QuestionDetailResponse

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/recall", response_model=list[QuestionRecallResponse])
async def recall_questions(
    grammar_focus: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    stmt = select(Question).where(Question.practice_status == "active").offset(offset).limit(limit)
    result = await db.execute(stmt)
    questions = result.scalars().all()

    responses = []
    for q in questions:
        # Fetch latest annotation for grammar_focus/difficulty
        grammar_role_key = None
        grammar_focus_key = None
        difficulty_overall = None
        if q.latest_annotation_id:
            ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
            if ann:
                grammar_role_key = ann.annotation_jsonb.get("grammar_role_key")
                grammar_focus_key = ann.annotation_jsonb.get("grammar_focus_key")
                difficulty_overall = ann.annotation_jsonb.get("difficulty_overall")

        # Apply filters
        if grammar_focus and grammar_focus_key != grammar_focus:
            continue
        if difficulty and difficulty_overall != difficulty:
            continue
        if origin and q.content_origin != origin:
            continue

        responses.append(QuestionRecallResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            current_correct_option_label=q.current_correct_option_label,
            practice_status=q.practice_status,
            grammar_role_key=grammar_role_key,
            grammar_focus_key=grammar_focus_key,
            difficulty_overall=difficulty_overall,
            stimulus_mode_key=q.stem_type_key,
            source_exam_code=q.source_exam_code,
        ))
    return responses


@router.get("/{question_id}", response_model=QuestionDetailResponse)
async def get_question_detail(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    from uuid import UUID
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # Fetch annotation
    latest_annotation = None
    if q.latest_annotation_id:
        ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
        if ann:
            latest_annotation = {**ann.annotation_jsonb, **ann.explanation_jsonb}

    # Fetch options
    opts_result = await db.execute(
        select(QuestionOption).where(QuestionOption.question_id == qid)
    )
    options = [
        {
            "label": o.option_label,
            "text": o.option_text,
            "is_correct": o.is_correct,
            "role": o.option_role,
            "why_plausible": o.why_plausible,
            "why_wrong": o.why_wrong,
        }
        for o in opts_result.scalars().all()
    ]

    # Lineage
    lineage = None
    if q.derived_from_question_id or q.generation_source_set:
        lineage = {
            "derived_from": str(q.derived_from_question_id) if q.derived_from_question_id else None,
            "generation_source_set": q.generation_source_set,
        }

    return QuestionDetailResponse(
        id=str(q.id),
        content_origin=q.content_origin,
        current_question_text=q.current_question_text,
        current_passage_text=q.current_passage_text,
        current_correct_option_label=q.current_correct_option_label,
        current_explanation_text=q.current_explanation_text,
        practice_status=q.practice_status,
        official_overlap_status=q.official_overlap_status,
        is_admin_edited=q.is_admin_edited,
        source_exam_code=q.source_exam_code,
        source_module_code=q.source_module_code,
        latest_annotation=latest_annotation,
        options=options,
        lineage=lineage,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


@router.get("/{question_id}/versions", response_model=list[dict])
async def get_question_versions(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    from uuid import UUID
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == qid)
        .order_by(QuestionVersion.version_number)
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "change_source": v.change_source,
            "question_text": v.question_text,
            "correct_option_label": v.correct_option_label,
            "change_notes": v.change_notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
```

- [ ] **Step 4: Register the router in main.py**

Add to `app/main.py`:

```python
from app.routers import health, questions

app.include_router(health.router)
app.include_router(questions.router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_questions_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/questions.py backend/tests/test_questions_router.py backend/app/main.py
git commit -m "feat: add questions router with recall, detail, and versions endpoints"
```

---

### Task 3: Create Student router (3 endpoints)

**Files:**
- Create: `backend/app/routers/student.py`
- Create: `backend/tests/test_student_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_student_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_student_recall_empty(client):
    resp = await client.get("/api/questions", headers={"X-API-Key": "student-key-change-me"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_student_submit_invalid_question(client):
    resp = await client.post("/api/submit", json={
        "user_id": 1,
        "question_id": "00000000-0000-0000-0000-000000000000",
        "is_correct": True,
        "selected_option_label": "A",
    }, headers={"X-API-Key": "student-key-change-me"})
    assert resp.status_code in (404, 400)


@pytest.mark.asyncio
async def test_student_stats_not_found(client):
    resp = await client.get("/api/stats/99999", headers={"X-API-Key": "student-key-change-me"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_answered"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_student_router.py -v`
Expected: FAIL (route not registered)

- [ ] **Step 3: Write implementation**

```python
# app/routers/student.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.auth import student_required
from app.models.db import Question, User, UserProgress, QuestionAnnotation
from app.models.payload import QuestionRecallResponse, UserProgressCreate, UserStats

router = APIRouter(prefix="/api", tags=["student"])


@router.get("/questions", response_model=list[QuestionRecallResponse])
async def student_recall(
    grammar_focus: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Student practice recall — mirrors /questions/recall but uses student auth."""
    stmt = select(Question).where(Question.practice_status == "active").offset(offset).limit(limit)
    result = await db.execute(stmt)
    questions = result.scalars().all()

    responses = []
    for q in questions:
        grammar_focus_key = None
        difficulty_overall = None
        if q.latest_annotation_id:
            ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
            if ann:
                grammar_focus_key = ann.annotation_jsonb.get("grammar_focus_key")
                difficulty_overall = ann.annotation_jsonb.get("difficulty_overall")

        if grammar_focus and grammar_focus_key != grammar_focus:
            continue
        if difficulty and difficulty_overall != difficulty:
            continue
        if origin and q.content_origin != origin:
            continue

        responses.append(QuestionRecallResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            current_correct_option_label=q.current_correct_option_label,
            practice_status=q.practice_status,
            grammar_focus_key=grammar_focus_key,
            difficulty_overall=difficulty_overall,
            stimulus_mode_key=q.stem_type_key,
            source_exam_code=q.source_exam_code,
        ))
    return responses


@router.post("/submit")
async def submit_answer(
    body: UserProgressCreate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Record a student's answer attempt."""
    from uuid import UUID
    try:
        qid = UUID(body.question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    user = await db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    progress = UserProgress(
        user_id=body.user_id,
        question_id=qid,
        is_correct=body.is_correct,
        selected_option_label=body.selected_option_label,
        missed_grammar_focus_key=body.missed_grammar_focus_key,
        missed_syntactic_trap_key=body.missed_syntactic_trap_key,
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return {"id": progress.id, "is_correct": progress.is_correct}


@router.get("/stats/{user_id}", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Retrieve user accuracy stats and top missed keys."""
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    records = result.scalars().all()

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = correct / total if total > 0 else 0.0

    # Count missed grammar focus keys
    from collections import Counter
    focus_counts = Counter(r.missed_grammar_focus_key for r in records if r.missed_grammar_focus_key and not r.is_correct)
    trap_counts = Counter(r.missed_syntactic_trap_key for r in records if r.missed_syntactic_trap_key and not r.is_correct)

    return UserStats(
        total_answered=total,
        total_correct=correct,
        accuracy=round(accuracy, 3),
        top_missed_focus_keys=[k for k, _ in focus_counts.most_common(5)],
        top_missed_trap_keys=[k for k, _ in trap_counts.most_common(5)],
    )
```

- [ ] **Step 4: Register the router in main.py**

Add import and include: `from app.routers import health, questions, student`
Add: `app.include_router(student.router)`

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_student_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/student.py backend/tests/test_student_router.py backend/app/main.py
git commit -m "feat: add student router with recall, submit, and stats endpoints"
```

---

## Chunk 2: Admin Router

### Task 4: Create Admin router (6 endpoints)

**Files:**
- Create: `backend/app/routers/admin.py`
- Create: `backend/tests/test_admin_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_admin_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_admin_edit_not_found(client):
    resp = await client.patch(
        "/admin/questions/00000000-0000-0000-0000-000000000000",
        json={"question_text": "new text"},
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_approve_not_found(client):
    resp = await client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/approve",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_reject_not_found(client):
    resp = await client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/reject",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_confirm_overlap_not_found(client):
    resp = await client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/confirm-overlap",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_clear_overlap_not_found(client):
    resp = await client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/clear-overlap",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_eval_score_not_found(client):
    resp = await client.post(
        "/admin/evaluations/00000000-0000-0000-0000-000000000000/score",
        json={"score_overall": 8.0},
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_admin_router.py -v`
Expected: FAIL (routes not registered)

- [ ] **Step 3: Write implementation**

```python
# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.auth import admin_required
from app.models.db import (
    Question, QuestionVersion, QuestionAnnotation,
    QuestionOption, LlmEvaluation,
)
from app.models.payload import AdminEditRequest, EvaluationScoreRequest

router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_uuid(question_id: str) -> UUID:
    try:
        return UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")


@router.patch("/questions/{question_id}")
async def edit_question(
    question_id: str,
    body: AdminEditRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Edit question content — creates a new version and updates the question."""
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    now = datetime.now(timezone.utc)

    # Create new version
    latest_version = None
    if q.versions:
        latest_version = max(q.versions, key=lambda v: v.version_number)

    new_version = QuestionVersion(
        question_id=qid,
        version_number=(latest_version.version_number + 1) if latest_version else 1,
        change_source="admin_edit",
        question_text=changes.get("question_text", q.current_question_text),
        passage_text=changes.get("passage_text", q.current_passage_text),
        choices_jsonb=[],
        correct_option_label=changes.get("correct_option_label", q.current_correct_option_label),
        explanation_text=changes.get("explanation_text", q.current_explanation_text),
        change_notes=changes.get("change_notes"),
        created_at=now,
    )
    db.add(new_version)

    # Update question
    if "question_text" in changes:
        q.current_question_text = changes["question_text"]
    if "passage_text" in changes:
        q.current_passage_text = changes["passage_text"]
    if "correct_option_label" in changes:
        q.current_correct_option_label = changes["correct_option_label"]
    if "explanation_text" in changes:
        q.current_explanation_text = changes["explanation_text"]
    q.is_admin_edited = True
    q.updated_at = now

    await db.commit()
    return {"id": str(q.id), "version": new_version.version_number, "changes": list(changes.keys())}


@router.post("/questions/{question_id}/approve")
async def approve_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.practice_status = "active"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "practice_status": "active"}


@router.post("/questions/{question_id}/reject")
async def reject_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.practice_status = "retired"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "practice_status": "retired"}


@router.post("/questions/{question_id}/confirm-overlap")
async def confirm_overlap(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.official_overlap_status = "confirmed"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "official_overlap_status": "confirmed"}


@router.post("/questions/{question_id}/clear-overlap")
async def clear_overlap(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.official_overlap_status = "none"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "official_overlap_status": "none"}


@router.post("/evaluations/{evaluation_id}/score")
async def score_evaluation(
    evaluation_id: str,
    body: EvaluationScoreRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    eid = _parse_uuid(evaluation_id)
    ev = await db.get(LlmEvaluation, eid)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if body.score_overall is not None:
        ev.score_overall = body.score_overall
    if body.score_metadata is not None:
        ev.score_metadata = body.score_metadata
    if body.score_explanation is not None:
        ev.score_explanation = body.score_explanation
    if body.score_generation is not None:
        ev.score_generation = body.score_generation
    if body.review_notes is not None:
        ev.review_notes = body.review_notes
    if body.recommended_for_default is not None:
        ev.recommended_for_default = body.recommended_for_default

    await db.commit()
    return {"id": str(ev.id), "score_overall": ev.score_overall}
```

- [ ] **Step 4: Register the router in main.py**

Add: `from app.routers import health, questions, student, admin`
Add: `app.include_router(admin.router)`

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_admin_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/admin.py backend/tests/test_admin_router.py backend/app/main.py
git commit -m "feat: add admin router with edit, approve, reject, overlap, and eval endpoints"
```

---

## Chunk 3: Ingestion + Generation Routers (Async Pipeline)

### Task 5: Create Ingest router (4 endpoints)

**Files:**
- Create: `backend/app/routers/ingest.py`
- Create: `backend/tests/test_ingest_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ingest_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_ingest_pdf_no_file(client):
    resp = await client.post("/ingest/official/pdf", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 422  # missing file


@pytest.mark.asyncio
async def test_ingest_unofficial_no_file(client):
    resp = await client.post("/ingest/unofficial/file", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_batch_no_files(client):
    resp = await client.post("/ingest/unofficial/batch", headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reannotate_not_found(client):
    resp = await client.post(
        "/ingest/reannotate/00000000-0000-0000-0000-000000000000",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_ingest_router.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/routers/ingest.py
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import admin_required
from app.config import get_settings
from app.models.db import QuestionJob, QuestionAsset, Question, QuestionAnnotation, QuestionVersion, QuestionOption
from app.storage.local_store import save_asset, compute_checksum
from app.parsers.pdf_parser import parse_pdf
from app.parsers.json_parser import extract_json_from_text
from app.pipeline.orchestrator import JobOrchestrator
from app.pipeline.validator import validate_question
from app.models.payload import JobResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "text/markdown", "text/plain", "application/json",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def _run_pipeline(job: QuestionJob, db: AsyncSession):
    """Background task: run the 2-pass LLM pipeline on a job."""
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        settings.default_annotation_provider,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
    )
    orch = JobOrchestrator(str(job.id), job.content_origin, job.job_type)

    raw_text = (job.pass1_json or {}).get("raw_text", "")
    if not raw_text:
        orch.fail("extracting", "no_raw_text", "No raw text available")
        job.status = "failed"
        await db.commit()
        return

    # Pass 1: Extract
    orch.advance()  # parsing → extracting
    job.status = "extracting"
    await db.commit()

    system, user = build_extract_prompt(raw_text[:30000])
    try:
        result = await provider.complete(system=system, user=user)
        extract_json = extract_json_from_text(result.raw_text)
        job.pass1_json = {**extract_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("extracting", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "extracting", "error": str(e)}]
        await db.commit()
        return

    # Pass 2: Annotate
    orch.advance()  # extracting → annotating
    job.status = "annotating"
    await db.commit()

    system, user = build_annotate_prompt(extract_json)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = extract_json_from_text(result.raw_text)
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("annotating", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
        await db.commit()
        return

    # Validate
    orch.advance()  # annotating → validating
    job.status = "validating"
    merged = {**extract_json, **annotate_json}
    errors = validate_question(merged, content_origin=job.content_origin)
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
    else:
        job.status = "approved"
    await db.commit()


def _asset_type_from_mime(mime: str) -> str:
    if "pdf" in mime:
        return "pdf"
    elif "image" in mime:
        return "image"
    elif "markdown" in mime:
        return "markdown"
    elif "json" in mime:
        return "json"
    return "text"


@router.post("/official/pdf", response_model=JobResponse)
async def ingest_official_pdf(
    file: UploadFile = File(...),
    source_exam_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Upload an official exam PDF for ingestion."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    # Save to local storage
    storage_path = await save_asset(file.filename or "upload.pdf", content, subfolder="official")
    checksum = compute_checksum(content)

    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()

    # Parse PDF to extract raw text
    from app.parsers.pdf_parser import parse_pdf as parse_pdf_file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        pdf_result = parse_pdf_file(tmp.name)

    raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])

    # Create asset
    asset = QuestionAsset(
        id=asset_id,
        content_origin="official",
        asset_type="pdf",
        storage_path=storage_path,
        mime_type=file.content_type,
        page_start=0,
        page_end=len(pdf_result["pages"]) - 1,
        source_name=file.filename,
        source_exam_code=source_exam_code or None,
        source_module_code=source_module_code or None,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    # Create job
    settings = get_settings()
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="official",
        input_format="pdf",
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v1",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:50000], "pages": len(pdf_result["pages"]), "source_metadata": {
            "source_exam_code": source_exam_code,
            "source_module_code": source_module_code,
        }},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    # Start pipeline in background
    import asyncio
    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


async def _run_pipeline_with_session(job_id: uuid.UUID):
    """Run pipeline with a fresh DB session (background tasks can't reuse the request session)."""
    from app.database import async_session
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_pipeline(job, db)


@router.post("/unofficial/file", response_model=JobResponse)
async def ingest_unofficial_file(
    file: UploadFile = File(...),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Upload a single unofficial asset."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    storage_path = await save_asset(file.filename or "upload", content, subfolder="unofficial")
    checksum = compute_checksum(content)
    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()

    asset_type = _asset_type_from_mime(file.content_type or "")

    asset = QuestionAsset(
        id=asset_id,
        content_origin="unofficial",
        asset_type=asset_type,
        storage_path=storage_path,
        mime_type=file.content_type,
        source_name=file.filename,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    # Extract raw text based on asset type
    raw_text = ""
    if asset_type == "pdf":
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            pdf_result = parse_pdf(tmp.name)
            raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
    elif asset_type in ("text", "markdown"):
        raw_text = content.decode("utf-8", errors="replace")
    elif asset_type == "json":
        import json
        try:
            data = json.loads(content)
            raw_text = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            raw_text = content.decode("utf-8", errors="replace")

    settings = get_settings()
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="unofficial",
        input_format=asset_type,
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v1",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:50000]},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    import asyncio
    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


@router.post("/unofficial/batch", response_model=list[JobResponse])
async def ingest_unofficial_batch(
    files: list[UploadFile] = File(...),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Batch upload mixed unofficial assets."""
    results = []
    for file in files:
        # Reuse the single-file endpoint logic
        resp = await ingest_unofficial_file(
            file=file, provider_name=provider_name, model_name=model_name, db=db, _auth=_auth
        )
        results.append(resp)
    return results


@router.post("/reannotate/{question_id}", response_model=JobResponse)
async def reannotate_question(
    question_id: str,
    provider_name: str = "anthropic",
    model_name: str = "claude-sonnet-4-6",
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Re-run Pass 2 annotation on an existing question."""
    from uuid import UUID
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # Find the latest job for this question to get pass1_json
    from sqlalchemy import select
    result = await db.execute(
        select(QuestionJob)
        .where(QuestionJob.question_id == qid)
        .order_by(QuestionJob.created_at.desc())
        .limit(1)
    )
    existing_job = result.scalars().first()
    if not existing_job or not existing_job.pass1_json:
        raise HTTPException(status_code=400, detail="No existing extract data for this question")

    settings = get_settings()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    job = QuestionJob(
        id=job_id,
        job_type="reannotate",
        content_origin=q.content_origin,
        input_format="reannotate",
        status="annotating",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v1",
        rules_version=settings.rules_version,
        pass1_json=existing_job.pass1_json,
        question_id=qid,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    import asyncio
    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="reannotate", status="annotating", question_id=question_id, created_at=now)
```

- [ ] **Step 4: Register the router in main.py**

Add: `from app.routers import health, questions, student, admin, ingest`
Add: `app.include_router(ingest.router)`

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_ingest_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/ingest.py backend/tests/test_ingest_router.py backend/app/main.py
git commit -m "feat: add ingest router with PDF upload, file upload, batch, and reannotate"
```

---

### Task 6: Create Generate router (3 endpoints)

**Files:**
- Create: `backend/app/routers/generate.py`
- Create: `backend/tests/test_generate_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generate_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_generate_questions_schema(client):
    """Test that generate endpoint accepts valid request body."""
    resp = await client.post("/generate/questions", json={
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "none",
        "difficulty_overall": "medium",
    }, headers={"X-API-Key": "admin-key-change-me"})
    # Will likely return a job ID even though LLM call may fail
    assert resp.status_code in (200, 201, 500)


@pytest.mark.asyncio
async def test_generate_compare_schema(client):
    resp = await client.post("/generate/questions/compare", json={
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "providers": ["anthropic"],
    }, headers={"X-API-Key": "admin-key-change-me"})
    assert resp.status_code in (200, 201, 500)


@pytest.mark.asyncio
async def test_generate_run_not_found(client):
    resp = await client.get(
        "/generate/runs/00000000-0000-0000-0000-000000000000",
        headers={"X-API-Key": "admin-key-change-me"},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_generate_router.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/routers/generate.py
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import admin_required
from app.config import get_settings
from app.models.db import QuestionJob, Question, QuestionAnnotation, QuestionVersion, QuestionOption
from app.parsers.json_parser import extract_json_from_text
from app.pipeline.orchestrator import JobOrchestrator
from app.pipeline.validator import validate_question
from app.models.payload import GenerationRequest, GenerationCompareRequest, JobResponse

router = APIRouter(prefix="/generate", tags=["generate"])


async def _run_generate_pipeline(job: QuestionJob, db: AsyncSession, request_data: dict):
    """Run generation + annotation pipeline."""
    from app.llm.factory import get_provider
    from app.prompts.generate_prompt import build_generate_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
    )

    # Generate
    system, user = build_generate_prompt(generation_request=request_data)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192, temperature=0.7)
        generated = extract_json_from_text(result.raw_text)
        job.pass1_json = {**generated, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
        job.status = "annotating"
        await db.commit()
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "generating", "error": str(e)}]
        await db.commit()
        return

    # Annotate (the generated output should already contain annotation data,
    # but we run a dedicated annotation pass for consistency)
    system, user = build_annotate_prompt(generated)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = extract_json_from_text(result.raw_text)
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
        await db.commit()
        return

    # Validate and create question
    merged = {**generated, **annotate_json, "generation_source_set": request_data}
    errors = validate_question(merged, content_origin="generated")
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
    else:
        job.status = "approved"

    # Create question record
    question_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    question = Question(
        id=question_id,
        content_origin="generated",
        current_question_text=generated.get("question_text", ""),
        current_passage_text=generated.get("passage_text"),
        current_correct_option_label=generated.get("correct_option_label", ""),
        current_explanation_text=annotate_json.get("explanation_short", ""),
        practice_status="draft",
        official_overlap_status="none",
        generation_source_set=request_data,
        is_admin_edited=False,
        metadata_managed_by_llm=True,
        created_at=now,
        updated_at=now,
    )
    db.add(question)
    job.question_id = question_id
    await db.commit()


@router.post("/questions", response_model=JobResponse)
async def generate_questions(
    body: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Generate new questions from a specification."""
    settings = get_settings()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    job = QuestionJob(
        id=job_id,
        job_type="generate",
        content_origin="generated",
        input_format="spec",
        status="extracting",
        provider_name=settings.default_annotation_provider,
        model_name=settings.default_annotation_model,
        prompt_version="v1",
        rules_version=settings.rules_version,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    request_data = body.model_dump()
    import asyncio
    async def _run():
        from app.database import async_session
        async with async_session() as db2:
            j = await db2.get(QuestionJob, job_id)
            if j:
                await _run_generate_pipeline(j, db2, request_data)
    asyncio.create_task(_run())

    return JobResponse(id=str(job_id), job_type="generate", status="extracting", created_at=now)


@router.post("/questions/compare", response_model=list[JobResponse])
async def generate_compare(
    body: GenerationCompareRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Generate questions with multiple LLMs for comparison."""
    settings = get_settings()
    comparison_group = uuid.uuid4()
    results = []
    now = datetime.now(timezone.utc)

    for provider_name in body.providers:
        job_id = uuid.uuid4()
        job = QuestionJob(
            id=job_id,
            job_type="generate",
            content_origin="generated",
            input_format="spec",
            status="extracting",
            provider_name=provider_name,
            model_name=settings.default_annotation_model,  # will use provider's default
            prompt_version="v1",
            rules_version=settings.rules_version,
            comparison_group_id=comparison_group,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        results.append(JobResponse(id=str(job_id), job_type="generate", status="extracting", created_at=now))

    await db.commit()

    # Fire off pipeline for each job
    request_data = body.model_dump()
    for resp in results:
        jid = uuid.UUID(resp.id)
        async def _run(jid=jid):
            from app.database import async_session
            async with async_session() as db2:
                j = await db2.get(QuestionJob, jid)
                if j:
                    await _run_generate_pipeline(j, db2, request_data)
        asyncio.create_task(_run())

    return results


@router.get("/runs/{run_id}")
async def get_generation_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Inspect a generation run's lineage and review state."""
    from uuid import UUID
    try:
        rid = UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    # run_id could be a job_id or a comparison_group_id
    result = await db.execute(
        select(QuestionJob).where(QuestionJob.id == rid)
    )
    job = result.scalars().first()

    if not job:
        # Try as comparison group
        result = await db.execute(
            select(QuestionJob).where(QuestionJob.comparison_group_id == rid)
        )
        jobs = result.scalars().all()
        if not jobs:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "comparison_group_id": str(rid),
            "jobs": [
                {
                    "id": str(j.id),
                    "status": j.status,
                    "provider_name": j.provider_name,
                    "question_id": str(j.question_id) if j.question_id else None,
                }
                for j in jobs
            ],
        }

    return {
        "id": str(job.id),
        "status": job.status,
        "provider_name": job.provider_name,
        "question_id": str(job.question_id) if job.question_id else None,
        "comparison_group_id": str(job.comparison_group_id) if job.comparison_group_id else None,
    }
```

- [ ] **Step 4: Register the router in main.py**

Add: `from app.routers import health, questions, student, admin, ingest, generate`
Add: `app.include_router(generate.router)`

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_generate_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/generate.py backend/tests/test_generate_router.py backend/app/main.py
git commit -m "feat: add generate router with generation, comparison, and run inspection"
```

---

### Task 7: Update main.py with all routers and CORS

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the final main.py**

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, questions, student, admin, ingest, generate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB pool already configured in database.py
    yield
    # Shutdown: close DB pool
    from app.database import engine
    await engine.dispose()


app = FastAPI(title="DSAT Grammar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(questions.router)
app.include_router(student.router)
app.include_router(admin.router)
app.include_router(ingest.router)
app.include_router(generate.router)
```

- [ ] **Step 2: Run all tests**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v`
Expected: All tests pass (existing 61 + new router tests)

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: register all 5 routers with CORS middleware"
```

---

### Task 8: Full integration test and verification

- [ ] **Step 1: Run the full test suite**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 2: Start the server and verify Swagger UI**

```bash
cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` to see all 19 endpoints in Swagger UI.

- [ ] **Step 3: Test recall with curl**

```bash
curl -H "X-API-Key: admin-key-change-me" http://localhost:8000/questions/recall
```
Expected: `[]` (empty list, no questions yet)

- [ ] **Step 4: Final commit**

```bash
git add -A backend/
git commit -m "feat: complete API routers — all 19 endpoints with integration tests"
```

---

## Next Steps

After this plan is executed:
1. **Manual test with real PDF** using `scripts/manual_test.py` (already created)
2. **Manual generation test** via Swagger UI or `scripts/manual_test.py generate`
3. **Add python-multipart dependency** for file upload support: add to `pyproject.toml`
4. **Add overlap detection** logic (currently returns "none" for all questions)
5. **Add proper background task queue** (replace `asyncio.create_task` with Celery/arq for production)

---

## Summary

| Chunk | Routers | Endpoints | Key Feature |
|-------|---------|-----------|-------------|
| 1 | questions, student | 6 | Read-only: recall, detail, versions, submit, stats |
| 2 | admin | 6 | Mutations: edit, approve, reject, overlap, eval |
| 3 | ingest, generate | 7 | Async pipeline: upload → parse → extract → annotate |

**Total: 19 endpoints, 5 routers, 5 test files**