# Admin Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the five features specced in `admin_dashboard_plan.md` (§5–§9) — question
browsing/editing, user editing, admin password reset, a student activity heatmap, and a modular
widget dashboard — against the existing `APP/ADMIN_APP` React app and `backend/app/routers/`
FastAPI routers.

**Architecture:** All backend changes are additive endpoints/fields on the three existing
routers (`admin.py`, `users.py`, `student.py`) — no new routers, no schema migrations except
where noted. All frontend changes are additive components/pages within the existing
`APP/ADMIN_APP` Vite app — no new frontend app, no routing library change.

**Tech Stack:** FastAPI + SQLAlchemy async (backend, Python, pytest), React 19 + TypeScript +
Vite + TanStack Query v5 + react-router-dom v7 + Tailwind v4 (frontend). New frontend
dependency: `react-grid-layout` (Phase 5 only). `framer-motion` is already a dependency
(`package.json`, `^12.40.0`) — no install needed for it.

## Global Constraints

- Every new admin backend endpoint uses `Depends(admin_required)` (X-API-Key header), matching
  every existing endpoint in `admin.py`/`users.py`. Student-facing endpoints (Phase 4) use
  `Depends(student_required)`, matching the existing `/stats/{user_id}` endpoint.
- Backend tests use the `client` fixture and `AUTH = {"X-API-Key": "admin-test-key"}` header
  convention already established in `backend/tests/conftest.py`, `test_admin_router.py`, and
  `test_users_router.py`. The default `client` fixture's mock DB session returns `None` from
  `db.get()` and empty results from `db.execute()` — sufficient for 404/empty-state tests.
  Tests needing a populated row use a custom `FakeSession`/`FakeUser`/`FakeQuestion` class and
  `app.dependency_overrides[get_db]`, matching the pattern in
  `test_admin_router.py::test_admin_reject_is_non_destructive`.
- **`APP/ADMIN_APP` has no automated frontend test suite** (verified: no `vitest.config.ts`, no
  `*.test.tsx` files anywhere in the app). Frontend tasks are verified by manual QA against the
  dev server (`npm run dev` from `APP/ADMIN_APP`), not automated tests. Do not invent frontend
  test steps that don't correspond to real infrastructure — if automated frontend tests become
  a priority, that is its own separate task (setting up Vitest + Testing Library), out of scope
  here.
- Partial-update endpoints (`PATCH`) use Pydantic's `model_dump(exclude_unset=True)` pattern,
  matching the existing `AdminEditRequest`/`edit_question` in `admin.py:1001-1124`.
- All Pydantic request/response models go in `backend/app/models/payload.py`, matching every
  existing model.

---

## Phase 1: Question Browser, Detail View, Edit UI & Test Explorer

Implements `admin_dashboard_plan.md` §7. Fixes two live bugs (dead edit endpoint, broken
Focus/Difficulty columns) and adds test-based browsing.

### Task 1.1: Backend — expose `annotation_stale` in the question list response

**Files:**
- Modify: `backend/app/routers/admin.py:226-246` (the `items.append({...})` dict in `list_questions`)
- Test: `backend/tests/test_admin_router.py`

**Interfaces:**
- Consumes: `Question.annotation_stale` (existing column, `backend/app/models/db.py:100`)
- Produces: `annotation_stale: bool` key in every item of `GET /admin/questions`'s list response — consumed by Task 1.3 (frontend type) and Task 1.4 (stale badge)

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_admin_router.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_admin_router.py::test_admin_list_questions_includes_annotation_stale -v`
Expected: FAIL with `KeyError: 'annotation_stale'`

- [ ] **Step 3: Add the field to the response dict**

In `backend/app/routers/admin.py`, find this block (around line 226):

```python
        items.append({
            "id": str(q.id),
            "content_origin": q.content_origin,
            "practice_status": q.practice_status,
            "official_overlap_status": q.official_overlap_status,
            "source_release_year": q.source_release_year,
            "source_test_name": q.source_test_name,
            "source_exam_code": q.source_exam_code,
            "source_subject_code": q.source_subject_code,
            "source_section_code": q.source_section_code,
            "source_module_code": q.source_module_code,
            "source_question_number": q.source_question_number,
            "current_passage_text": q.current_passage_text,
            "current_question_text": q.current_question_text,
            "current_correct_option_label": q.current_correct_option_label,
            "current_explanation_text": q.current_explanation_text,
            "is_admin_edited": q.is_admin_edited,
            "annotation": annotation,
            "options": options,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })
```

Add `"annotation_stale": q.annotation_stale,` after the `is_admin_edited` line:

```python
            "is_admin_edited": q.is_admin_edited,
            "annotation_stale": q.annotation_stale,
            "annotation": annotation,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_admin_router.py::test_admin_list_questions_includes_annotation_stale -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/admin.py backend/tests/test_admin_router.py
git commit -m "Expose annotation_stale in admin question list response"
```

---

### Task 1.2: Backend — `GET /admin/tests` aggregation endpoint

**Files:**
- Modify: `backend/app/models/payload.py` (add `TestSummary`)
- Modify: `backend/app/routers/admin.py` (add endpoint, near `list_questions`)
- Test: `backend/tests/test_admin_router.py`

**Interfaces:**
- Consumes: `Question.source_release_year/source_test_name/source_exam_code/source_subject_code/source_section_code/source_module_code/practice_status` (existing columns, already used by `list_questions`'s `sort_by_source` filters)
- Produces: `GET /admin/tests` → `list[TestSummary]`, each `{source_release_year, source_test_name, source_exam_code, source_subject_code, source_section_code, source_module_code, question_count, approved_count}` — consumed by Task 1.5 (Tests browse tab)

- [ ] **Step 1: Add the `TestSummary` model**

In `backend/app/models/payload.py`, add:

```python
class TestSummary(BaseModel):
    source_release_year: Optional[int] = None
    source_test_name: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
    question_count: int
    approved_count: int
```

- [ ] **Step 2: Write the failing test (empty case)**

Add to `backend/tests/test_admin_router.py`:

```python
def test_admin_list_tests_empty(client):
    resp = client.get("/admin/tests", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == []
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_admin_router.py::test_admin_list_tests_empty -v`
Expected: FAIL with 404 (route doesn't exist yet)

- [ ] **Step 4: Add the endpoint**

In `backend/app/routers/admin.py`, add after `list_questions` (after line 248, before `def _parse_uuid`). `case` and `func` are already imported at the top of this file (used by the analytics endpoints below), no new imports needed:

```python
@router.get("/tests", response_model=list[TestSummary])
async def list_tests(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Aggregate questions by source test/section/module for the admin test explorer."""
    stmt = (
        select(
            Question.source_release_year,
            Question.source_test_name,
            Question.source_exam_code,
            Question.source_subject_code,
            Question.source_section_code,
            Question.source_module_code,
            func.count(Question.id).label("question_count"),
            func.count(
                case((Question.practice_status.in_(("active", "approved")), 1))
            ).label("approved_count"),
        )
        .group_by(
            Question.source_release_year,
            Question.source_test_name,
            Question.source_exam_code,
            Question.source_subject_code,
            Question.source_section_code,
            Question.source_module_code,
        )
        .order_by(
            Question.source_release_year.asc().nullslast(),
            Question.source_test_name.asc().nullslast(),
            Question.source_section_code.asc().nullslast(),
            Question.source_module_code.asc().nullslast(),
        )
    )
    result = await db.execute(stmt)
    return [
        TestSummary(
            source_release_year=r.source_release_year,
            source_test_name=r.source_test_name,
            source_exam_code=r.source_exam_code,
            source_subject_code=r.source_subject_code,
            source_section_code=r.source_section_code,
            source_module_code=r.source_module_code,
            question_count=r.question_count,
            approved_count=r.approved_count,
        )
        for r in result.all()
    ]
```

Also add `TestSummary` to the `payload` import list at the top of `admin.py` (find the existing
`from app.models.payload import (...)` block and add `TestSummary,` to it).

- [ ] **Step 5: Run empty-case test to verify it passes**

Run: `cd backend && pytest tests/test_admin_router.py::test_admin_list_tests_empty -v`
Expected: PASS

- [ ] **Step 6: Write and run the populated-case test**

Add to `backend/tests/test_admin_router.py`:

```python
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
```

Run: `cd backend && pytest tests/test_admin_router.py::test_admin_list_tests_aggregates_by_source -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/payload.py backend/app/routers/admin.py backend/tests/test_admin_router.py
git commit -m "Add GET /admin/tests aggregation endpoint for the test explorer"
```

---

### Task 1.3: Frontend — fix the `Question` type and the Focus/Difficulty columns

**Files:**
- Modify: `APP/ADMIN_APP/src/types/index.ts`
- Modify: `APP/ADMIN_APP/src/pages/DataManagement.tsx`

**Interfaces:**
- Consumes: the real `GET /admin/questions` response shape (verified by reading `admin.py:220-248` — nests classification fields under `item.annotation`, includes `current_passage_text`/`current_explanation_text`/full `options`/`annotation_stale` per item, none of which the current TS type declares)
- Produces: corrected `Question` type and a new `QuestionAnnotation` type — consumed by Task 1.4 (`QuestionDetailModal`)

- [ ] **Step 1: Fix the `Question` type**

In `APP/ADMIN_APP/src/types/index.ts`, replace:

```ts
export interface Question {
  id: string
  content_origin: 'official' | 'generated' | 'admin_created'
  practice_status: 'draft' | 'active' | 'approved' | 'rejected' | 'needs_review'
  current_question_text: string
  current_passage_text?: string
  current_correct_option_label: string
  grammar_focus_key?: string
  grammar_role_key?: string
  reading_focus_key?: string
  difficulty_overall?: string
  source_test_name?: string
  source_question_number?: number
  options?: QuestionOption[]
  updated_at?: string
  created_at?: string
}
```

with:

```ts
export interface QuestionAnnotation {
  grammar_focus_key?: string
  grammar_role_key?: string
  reading_focus_key?: string
  difficulty_overall?: string
  [key: string]: unknown
}

export interface Question {
  id: string
  content_origin: 'official' | 'generated' | 'admin_created'
  practice_status: 'draft' | 'active' | 'approved' | 'rejected' | 'needs_review'
  official_overlap_status?: string
  current_question_text: string
  current_passage_text?: string
  current_correct_option_label: string
  current_explanation_text?: string
  is_admin_edited?: boolean
  annotation_stale?: boolean
  annotation?: QuestionAnnotation | null
  source_release_year?: number
  source_test_name?: string
  source_exam_code?: string
  source_subject_code?: string
  source_section_code?: string
  source_module_code?: string
  source_question_number?: number
  options?: QuestionOption[]
  updated_at?: string
  created_at?: string
}
```

- [ ] **Step 2: Fix the Focus/Difficulty column rendering**

In `APP/ADMIN_APP/src/pages/DataManagement.tsx`, find:

```tsx
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {(q.grammar_focus_key || q.reading_focus_key || '—').replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                    {q.difficulty_overall ?? '—'}
                  </td>
```

Replace with:

```tsx
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {(q.annotation?.grammar_focus_key ?? q.annotation?.reading_focus_key ?? '—')
                      .toString()
                      .replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                    {q.annotation?.difficulty_overall ?? '—'}
                  </td>
```

- [ ] **Step 3: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/data`. Confirm the Focus and Difficulty columns
now show real values (e.g. `pronoun antecedent agreement`, `medium`) for questions that have
annotation data, instead of `—` on every row.

- [ ] **Step 4: Commit**

```bash
git add APP/ADMIN_APP/src/types/index.ts APP/ADMIN_APP/src/pages/DataManagement.tsx
git commit -m "Fix Question type and Focus/Difficulty columns to match actual API shape"
```

---

### Task 1.4: Frontend — `QuestionDetailModal` (view, edit, and stale badge)

**Files:**
- Modify: `APP/ADMIN_APP/src/pages/DataManagement.tsx` (add the modal component and wire it into the row click)

**Interfaces:**
- Consumes: `Question`/`QuestionAnnotation` types (Task 1.3), `adminApi.editQuestion(id, data)` (already exists in `client.ts`, currently dead code)
- Produces: `QuestionDetailModal` component — no other task depends on it directly

- [ ] **Step 1: Add the modal component**

In `APP/ADMIN_APP/src/pages/DataManagement.tsx`, add this component above `export function DataManagement()`:

```tsx
function QuestionDetailModal({ question, onClose }: { question: Question; onClose: () => void }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [questionText, setQuestionText] = useState(question.current_question_text)
  const [passageText, setPassageText] = useState(question.current_passage_text ?? '')
  const [correctLabel, setCorrectLabel] = useState(question.current_correct_option_label)
  const [explanationText, setExplanationText] = useState(question.current_explanation_text ?? '')
  const [changeNotes, setChangeNotes] = useState('')

  const editMutation = useMutation({
    mutationFn: () =>
      adminApi.editQuestion(question.id, {
        question_text: questionText,
        passage_text: passageText || undefined,
        correct_option_label: correctLabel,
        explanation_text: explanationText || undefined,
        change_notes: changeNotes || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['questions'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              {question.source_test_name ?? 'Question'}
              {question.source_question_number ? ` #${question.source_question_number}` : ''}
            </h2>
            <p className="text-xs text-gray-400 font-mono">{question.id}</p>
          </div>
          <div className="flex items-center gap-2">
            {question.annotation_stale && (
              <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full font-medium">
                Annotation stale
              </span>
            )}
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">
              ×
            </button>
          </div>
        </div>

        {!editing ? (
          <div className="space-y-4">
            {question.current_passage_text && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Passage</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.current_passage_text}</p>
              </div>
            )}
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Question</p>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{question.current_question_text}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Options</p>
              <div className="space-y-1">
                {(question.options ?? []).map((opt) => (
                  <div
                    key={opt.id ?? opt.option_label}
                    className={`text-sm px-3 py-1.5 rounded-lg border ${
                      opt.option_label === question.current_correct_option_label
                        ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                        : 'border-gray-200 text-gray-600'
                    }`}
                  >
                    <span className="font-medium">{opt.option_label}.</span> {opt.option_text}
                  </div>
                ))}
              </div>
            </div>
            {question.current_explanation_text && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Explanation</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.current_explanation_text}</p>
              </div>
            )}
            {question.annotation && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Annotation</p>
                <div className="flex flex-wrap gap-1">
                  {question.annotation.grammar_focus_key && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                      {String(question.annotation.grammar_focus_key).replace(/_/g, ' ')}
                    </span>
                  )}
                  {question.annotation.reading_focus_key && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                      {String(question.annotation.reading_focus_key).replace(/_/g, ' ')}
                    </span>
                  )}
                  {question.annotation.difficulty_overall && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full capitalize">
                      {String(question.annotation.difficulty_overall)}
                    </span>
                  )}
                </div>
              </div>
            )}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Edit
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {question.current_passage_text !== undefined && (
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  Passage
                </label>
                <textarea
                  value={passageText}
                  onChange={(e) => setPassageText(e.target.value)}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Question text
              </label>
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Correct option
              </label>
              <select
                value={correctLabel}
                onChange={(e) => setCorrectLabel(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {(question.options ?? []).map((opt) => (
                  <option key={opt.option_label} value={opt.option_label}>
                    {opt.option_label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Explanation
              </label>
              <textarea
                value={explanationText}
                onChange={(e) => setExplanationText(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Change notes
              </label>
              <input
                type="text"
                value={changeNotes}
                onChange={(e) => setChangeNotes(e.target.value)}
                placeholder="Why is this edit being made?"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {editMutation.isError && <p className="text-red-600 text-sm">Failed to save changes.</p>}
            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => editMutation.mutate()}
                disabled={editMutation.isPending}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
              >
                {editMutation.isPending ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire it into the row click**

In `DataManagement()`, add state:

```tsx
  const [detailTarget, setDetailTarget] = useState<Question | null>(null)
```

Find the question-text `<td>`:

```tsx
                  <td className="px-4 py-3 max-w-sm">
                    <p className="text-gray-800 line-clamp-2 text-xs leading-relaxed">{q.current_question_text}</p>
                    <p className="text-gray-400 font-mono text-xs mt-0.5">{q.id.slice(0, 8)}…</p>
                  </td>
```

Replace with (adds click-to-open):

```tsx
                  <td
                    className="px-4 py-3 max-w-sm cursor-pointer"
                    onClick={() => setDetailTarget(q)}
                  >
                    <p className="text-gray-800 line-clamp-2 text-xs leading-relaxed hover:underline">
                      {q.current_question_text}
                    </p>
                    <p className="text-gray-400 font-mono text-xs mt-0.5">{q.id.slice(0, 8)}…</p>
                  </td>
```

Find the closing `{rejectTarget && (...)}` block near the bottom of the returned JSX and add the
detail modal render right after it:

```tsx
      {rejectTarget && (
        <RejectModal
          question={rejectTarget}
          onReject={(reason) => rejectMutation.mutate({ id: rejectTarget.id, reason })}
          onClose={() => setRejectTarget(null)}
        />
      )}

      {detailTarget && (
        <QuestionDetailModal question={detailTarget} onClose={() => setDetailTarget(null)} />
      )}
```

- [ ] **Step 3: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/data`, click a question row. Confirm the modal
shows passage/question/options (correct one highlighted)/explanation/annotation. Click "Edit",
change the question text, click "Save". Confirm the modal closes, the table refreshes, and the
new text appears in the table. Re-open the same question and confirm the "Annotation stale"
badge now shows (since editing sets `annotation_stale=True` server-side, per Task 1.1).

- [ ] **Step 4: Commit**

```bash
git add APP/ADMIN_APP/src/pages/DataManagement.tsx
git commit -m "Add QuestionDetailModal with view, edit, and annotation-stale badge"
```

---

### Task 1.5: Frontend — "Tests" browse tab

**Files:**
- Modify: `APP/ADMIN_APP/src/api/client.ts` (add `getTests`)
- Modify: `APP/ADMIN_APP/src/types/index.ts` (add `TestSummary`)
- Modify: `APP/ADMIN_APP/src/pages/DataManagement.tsx` (add browse mode)

**Interfaces:**
- Consumes: `GET /admin/tests` (Task 1.2), existing `source_test_name` + `sort_by_source=true` params on `GET /admin/questions` (already supported server-side, verified in `admin.py:150-190`)
- Produces: none (leaf feature)

- [ ] **Step 1: Add `getTests` to the API client**

In `APP/ADMIN_APP/src/api/client.ts`, add inside the `adminApi` object, near `listQuestions`:

```ts
  getTests: () => apiCall('/admin/tests'),
```

- [ ] **Step 2: Add the `TestSummary` type**

In `APP/ADMIN_APP/src/types/index.ts`, add:

```ts
export interface TestSummary {
  source_release_year?: number
  source_test_name?: string
  source_exam_code?: string
  source_subject_code?: string
  source_section_code?: string
  source_module_code?: string
  question_count: number
  approved_count: number
}
```

- [ ] **Step 3: Add the `TestBrowser` component and browse-mode state**

In `APP/ADMIN_APP/src/pages/DataManagement.tsx`, add above `export function DataManagement()`:

```tsx
function TestBrowser({ onSelectTest }: { onSelectTest: (t: TestSummary) => void }) {
  const { data: tests, isLoading } = useQuery<TestSummary[]>({
    queryKey: ['admin-tests'],
    queryFn: () => adminApi.getTests(),
    retry: 1,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (!tests || tests.length === 0) {
    return <div className="p-8 text-center text-gray-400 text-sm">No source test data found.</div>
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {tests.map((t, i) => (
        <button
          key={i}
          onClick={() => onSelectTest(t)}
          className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-blue-300 hover:shadow-sm transition"
        >
          <p className="text-sm font-semibold text-gray-800">
            {t.source_test_name ?? 'Unknown'} {t.source_section_code ?? ''} {t.source_module_code ?? ''}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {t.question_count} questions · {t.approved_count} approved
          </p>
        </button>
      ))}
    </div>
  )
}
```

Update the import line at the top of the file to include `TestSummary`:

```tsx
import type { Question, TestSummary } from '../types'
```

- [ ] **Step 4: Add browse-mode state and toggle to `DataManagement()`**

Add state alongside the existing `status`/`origin`/`page` state:

```tsx
  const [mode, setMode] = useState<'list' | 'tests'>('list')
  const [testFilter, setTestFilter] = useState<TestSummary | null>(null)
```

Merge the test filter into the query params (find the existing `params` construction):

```tsx
  const params: Record<string, any> = { limit, offset: (page - 1) * limit }
  if (status !== 'all') params.practice_status = status
  if (origin !== 'all') params.content_origin = origin
  if (testFilter) {
    if (testFilter.source_test_name) params.source_test_name = testFilter.source_test_name
    params.sort_by_source = true
  }
```

Add a mode toggle next to the existing status/origin filter bar:

```tsx
        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
          <button
            onClick={() => { setMode('list'); setTestFilter(null) }}
            className={[
              'px-3 py-1.5 rounded-md text-xs font-medium transition',
              mode === 'list' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            All Questions
          </button>
          <button
            onClick={() => setMode('tests')}
            className={[
              'px-3 py-1.5 rounded-md text-xs font-medium transition',
              mode === 'tests' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            Browse by Test
          </button>
        </div>
```

Finally, wrap the existing table block: when `mode === 'tests' && !testFilter`, render
`<TestBrowser onSelectTest={setTestFilter} />` instead of the table; when `testFilter` is set,
show a "← Back to tests" button above the (now test-filtered) table:

```tsx
      {mode === 'tests' && !testFilter ? (
        <TestBrowser onSelectTest={setTestFilter} />
      ) : (
        <>
          {testFilter && (
            <button
              onClick={() => setTestFilter(null)}
              className="text-xs text-blue-600 hover:underline"
            >
              ← Back to tests
            </button>
          )}
          {/* existing table block unchanged */}
        </>
      )}
```

- [ ] **Step 5: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/data`, click "Browse by Test". Confirm test
cards render with question counts. Click a card. Confirm the question list filters to that test,
ordered by question number, with a "← Back to tests" link.

- [ ] **Step 6: Commit**

```bash
git add APP/ADMIN_APP/src/api/client.ts APP/ADMIN_APP/src/types/index.ts APP/ADMIN_APP/src/pages/DataManagement.tsx
git commit -m "Add test browser mode to Data Management"
```

---

## Phase 1 Gap Review (2026-07-02)

All five Phase 1 tasks (1.1–1.5) passed individual spec-compliance + code-quality review and are
committed on GitButler branch `admin-dashboard-phase-1` (commits `7b9aaef`..`75cb67e`). The final
whole-branch review (broad pass, cross-task integration) found the following gaps. **Verdict:
Ready to merge — With fixes.** Gap 1 is a live functional defect in the phase's headline feature
(the detail/edit modal) and should be fixed before Phase 2 builds on top of it; Gaps 2–3 are
scoped follow-ups; Gaps 4–6 are structural/polish notes.

### Gap 1 (Critical): `QuestionDetailModal` options are non-functional — field-name mismatch

`backend/app/routers/admin.py` (`list_questions`, ~line 216) serializes each option as
`{"label": opt.option_label, "text": opt.option_text, "is_correct": opt.is_correct}` — no `id`
field, and the keys are `label`/`text`. But `QuestionOption` (`APP/ADMIN_APP/src/types/index.ts:43-48`)
declares `id: string`, `option_label: string`, `option_text: string`, `is_correct?: boolean`, and
`QuestionDetailModal` (`APP/ADMIN_APP/src/pages/DataManagement.tsx`) reads those names throughout:

- View mode: `key={opt.id ?? opt.option_label}` → both `undefined` (duplicate/undefined React keys);
  `{opt.option_label}. {opt.option_text}` → renders ". " with no content; the
  `opt.option_label === question.current_correct_option_label` highlight check is always false, so
  the correct answer never highlights.
- Edit mode: the "Correct option" `<select>` renders options with empty labels/values — an admin
  cannot pick a correct answer while editing.

This is the same class of bug Task 1.3 fixed for the annotation fields (flat vs. nested shape
mismatch), left unfixed for options. `QuestionOption`'s declared shape predates Phase 1 and never
matched what `list_questions` actually returns; it went unnoticed until Task 1.4 built the first
UI that renders `.options`.

**Fix:** align the backend serialization to `option_label`/`option_text`/`id` (preferred — matches
the `current_correct_option_label` naming convention already used elsewhere in the same response
dict), or change `QuestionOption` + `QuestionDetailModal` to read `label`/`text`. Re-verify the
Task 1.4 manual QA (Step 3) against a question with populated options once fixed — the original
report claimed a pass, which is worth reconciling.

### Gap 2 (Important): Test-card drill-down granularity doesn't match the cards

`TestBrowser` renders one card per `(source_release_year, source_test_name, source_exam_code,
source_subject_code, source_section_code, source_module_code)` group (from `GET /admin/tests`,
`admin.py:list_tests`) and labels cards by section/module. But selecting a card filters
`list_questions` only by `source_test_name` (`DataManagement.tsx`) — `list_questions` accepts no
section/module query params at all. Clicking any of "Test_4 sec01 mod01", "…sec01 mod02", etc.
shows the same full-test result set behind visually distinct cards.

**Fix:** add `source_section_code`/`source_module_code` (and ideally `source_release_year`) query
params to `list_questions` and pass them from `testFilter`; or collapse the `/admin/tests`
grouping to test-level so cards and filtering agree.

### Gap 3 (Important): Pagination footer renders under the test-card grid

The `questions` query in `DataManagement()` is never disabled while browsing test cards
(`mode === 'tests' && !testFilter`), so the pager below the (hidden) table still renders based on
the background unfiltered question list — controls that don't correspond to what's on screen.

**Fix:** gate the pager on `!(mode === 'tests' && !testFilter)`; consider `enabled: false` on the
questions query while cards are showing to avoid a wasted fetch.

### Gap 4 (Minor): `DataManagement.tsx` is now a 543-line file

Three consecutive tasks (1.3, 1.4, 1.5) added to this one file — it now holds `StatusBadge`,
`RejectModal`, `QuestionDetailModal`, `TestBrowser`, and the page itself. Recommend splitting
`QuestionDetailModal`, `TestBrowser`, and `RejectModal` into `components/` before Phase 2 adds
more.

### Gap 5 (Minor): `adminApi.editQuestion(id, data: any)` is now load-bearing

`data: any` (`APP/ADMIN_APP/src/api/client.ts`) means a future payload-key typo compiles fine and
silently no-ops server-side (`AdminEditRequest` uses `exclude_unset`). Recommend typing the
parameter to match `AdminEditRequest`'s field set
(`{ question_text?; passage_text?; correct_option_label?; explanation_text?; change_notes? }`).

### Gap 6 (Minor): `key={i}` (array index) on test cards

`TestSummary` has no natural unique id. A composite key
(`${source_test_name}-${source_section_code}-${source_module_code}`) would be more correct than
index-as-key, at no real cost.

---

## Phase 2: User Edit Endpoint

Implements `admin_dashboard_plan.md` §8.

### Task 2.1: Backend — `PATCH /users/{user_id}`

**Files:**
- Modify: `backend/app/models/payload.py` (add `UserUpdate`)
- Modify: `backend/app/routers/users.py`
- Test: `backend/tests/test_users_router.py`

**Interfaces:**
- Consumes: `User.username/email/role/is_active` (existing columns, `backend/app/models/db.py`)
- Produces: `PATCH /users/{user_id}` → `UserResponse` — consumed by Task 2.2 (frontend)

- [ ] **Step 1: Add the `UserUpdate` model**

In `backend/app/models/payload.py`, add near `UserCreate`:

```python
class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
```

- [ ] **Step 2: Write the failing tests**

Add to `backend/tests/test_users_router.py`:

```python
def test_update_user_not_found(client):
    resp = client.patch("/users/999", json={"username": "new-name"}, headers=AUTH)
    assert resp.status_code == 404


def test_update_user_duplicate_username(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class FakeUser:
        def __init__(self):
            self.id = 1
            self.username = "alice"
            self.email = None
            self.role = "student"

    class ConflictingUser:
        username = "bob"

    fake_user = FakeUser()

    class _Result:
        def scalars(self):
            return self

        def first(self):
            return ConflictingUser()

    class FakeSession:
        async def get(self, model, pk):
            return fake_user if pk == 1 else None

        async def execute(self, stmt):
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.patch("/users/1", json={"username": "bob"}, headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 409


def test_update_user_success(monkeypatch):
    import uuid as _uuid
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class FakeUser:
        def __init__(self):
            self.id = 1
            self.username = "alice"
            self.email = "alice@example.com"
            self.role = "student"
            self.user_token = _uuid.uuid4()
            self.created_at = datetime.now(timezone.utc)

    fake_user = FakeUser()

    class _Result:
        def scalars(self):
            return self

        def first(self):
            return None

    class FakeSession:
        async def get(self, model, pk):
            return fake_user if pk == 1 else None

        async def execute(self, stmt):
            return _Result()

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.patch("/users/1", json={"role": "admin"}, headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert fake_user.role == "admin"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_users_router.py -k update_user -v`
Expected: FAIL (404 for all three — route doesn't exist yet)

- [ ] **Step 4: Add the endpoint**

In `backend/app/routers/users.py`, add `UserUpdate` to the existing payload import, then add
the endpoint after `get_user`:

```python
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    if "username" in changes and changes["username"] != user.username:
        existing = await db.execute(select(User).where(User.username == changes["username"]))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Username already exists")

    if "email" in changes and changes["email"] and changes["email"] != user.email:
        existing = await db.execute(select(User).where(User.email == changes["email"]))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Email already exists")

    for field, value in changes.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_users_router.py -k update_user -v`
Expected: PASS (all three)

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/payload.py backend/app/routers/users.py backend/tests/test_users_router.py
git commit -m "Add PATCH /users/{user_id} endpoint for admin user edits"
```

---

### Task 2.2: Frontend — `updateUser` + edit UI in `UserManagement.tsx`

**Files:**
- Modify: `APP/ADMIN_APP/src/api/client.ts`
- Modify: `APP/ADMIN_APP/src/pages/UserManagement.tsx`

**Interfaces:**
- Consumes: `PATCH /users/{user_id}` (Task 2.1)
- Produces: none (leaf feature)

- [ ] **Step 1: Add `updateUser` to the API client**

In `APP/ADMIN_APP/src/api/client.ts`, add next to `deleteUser`:

```ts
  updateUser: (id: number, data: { username?: string; email?: string; role?: string; is_active?: boolean }) =>
    apiCall(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
```

- [ ] **Step 2: Add an `EditUserModal` component**

In `APP/ADMIN_APP/src/pages/UserManagement.tsx`, add above `export function UserManagement()`
(mirrors the existing `CreateUserModal` pattern):

```tsx
function EditUserModal({ user, onClose }: { user: User; onClose: () => void }) {
  const qc = useQueryClient()
  const [email, setEmail] = useState(user.email ?? '')
  const mutation = useMutation({
    mutationFn: () => adminApi.updateUser(user.id, { email }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Edit User</h2>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {mutation.isError && <p className="text-red-600 text-sm mb-3">Failed to update user.</p>}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!email || mutation.isPending}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
          >
            {mutation.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Wire it into the row actions**

Add state to `UserManagement()`:

```tsx
  const [editTarget, setEditTarget] = useState<User | null>(null)
```

Find the row actions `<td>` (the one with the "Delete" button) and add an "Edit" button before it:

```tsx
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEditTarget(u)}
                      className="text-xs text-blue-500 hover:text-blue-700 transition mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete user ${u.email}?`)) deleteMutation.mutate(u.id)
                      }}
                      className="text-xs text-red-500 hover:text-red-700 transition"
                    >
                      Delete
                    </button>
                  </td>
```

Add the modal render next to `{showCreate && <CreateUserModal .../>}`:

```tsx
      {editTarget && <EditUserModal user={editTarget} onClose={() => setEditTarget(null)} />}
```

- [ ] **Step 4: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/users`, click "Edit" on a user, change the
email, save. Confirm the table refreshes with the new email.

- [ ] **Step 5: Commit**

```bash
git add APP/ADMIN_APP/src/api/client.ts APP/ADMIN_APP/src/pages/UserManagement.tsx
git commit -m "Add user edit UI to User Management"
```

---

## Phase 3: Admin Password Reset

Implements `admin_dashboard_plan.md` §6.

### Task 3.1: Backend — `POST /users/{user_id}/reset-password`

**Files:**
- Modify: `backend/app/models/payload.py` (add `AdminPasswordReset`)
- Modify: `backend/app/routers/users.py`
- Test: `backend/tests/test_users_router.py`

**Interfaces:**
- Consumes: `hash_password()` (existing, `backend/app/auth.py`), `User.password_hash/refresh_token/refresh_token_expires` (existing columns)
- Produces: `POST /users/{user_id}/reset-password` (204 on success) — consumed by Task 3.2

- [ ] **Step 1: Add the `AdminPasswordReset` model**

In `backend/app/models/payload.py`, add:

```python
class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
```

- [ ] **Step 2: Write the failing tests**

Add to `backend/tests/test_users_router.py`:

```python
def test_admin_reset_password_not_found(client):
    resp = client.post("/users/999/reset-password", json={"new_password": "supersecret123"}, headers=AUTH)
    assert resp.status_code == 404


def test_admin_reset_password_validates_min_length(client):
    resp = client.post("/users/1/reset-password", json={"new_password": "short"}, headers=AUTH)
    assert resp.status_code == 422


def test_admin_reset_password_success(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class FakeUser:
        def __init__(self):
            self.id = 1
            self.password_hash = "old-hash"
            self.refresh_token = "some-refresh-token"
            self.refresh_token_expires = None

    fake_user = FakeUser()

    class FakeSession:
        async def get(self, model, pk):
            return fake_user if pk == 1 else None

        async def commit(self):
            pass

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post("/users/1/reset-password", json={"new_password": "brandnewpassword123"}, headers=AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 204
    assert fake_user.password_hash != "old-hash"
    assert fake_user.refresh_token is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_users_router.py -k reset_password -v`
Expected: FAIL (404 for all — route doesn't exist yet)

- [ ] **Step 4: Add the endpoint**

In `backend/app/routers/users.py`, add `hash_password` to the imports (`from app.auth import
admin_required, hash_password`) and `AdminPasswordReset` to the payload import, then add:

```python
@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: int,
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    user.refresh_token = None
    user.refresh_token_expires = None
    await db.commit()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_users_router.py -k reset_password -v`
Expected: PASS (all three)

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/payload.py backend/app/routers/users.py backend/tests/test_users_router.py
git commit -m "Add admin password reset endpoint"
```

---

### Task 3.2: Frontend — `resetUserPassword` + `ResetPasswordModal`

**Files:**
- Modify: `APP/ADMIN_APP/src/api/client.ts`
- Modify: `APP/ADMIN_APP/src/pages/UserManagement.tsx`

**Interfaces:**
- Consumes: `POST /users/{user_id}/reset-password` (Task 3.1)
- Produces: none (leaf feature)

- [ ] **Step 1: Add `resetUserPassword` to the API client**

In `APP/ADMIN_APP/src/api/client.ts`, add next to `updateUser`:

```ts
  resetUserPassword: (id: number, newPassword: string) =>
    apiCall(`/users/${id}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    }),
```

- [ ] **Step 2: Add the `ResetPasswordModal` component**

In `APP/ADMIN_APP/src/pages/UserManagement.tsx`, add above `export function UserManagement()`:

```tsx
function ResetPasswordModal({ user, onClose }: { user: User; onClose: () => void }) {
  const [newPassword, setNewPassword] = useState('')
  const [done, setDone] = useState(false)
  const mutation = useMutation({
    mutationFn: () => adminApi.resetUserPassword(user.id, newPassword),
    onSuccess: () => setDone(true),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-2">Reset Password</h2>
        <p className="text-sm text-gray-500 mb-4">for {user.email}</p>

        {done ? (
          <>
            <p className="text-sm text-gray-700 mb-2">Password reset. Share this with the student:</p>
            <p className="font-mono text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 mb-4 break-all">
              {newPassword}
            </p>
            <div className="flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Done
              </button>
            </div>
          </>
        ) : (
          <>
            <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
            <input
              type="text"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {mutation.isError && <p className="text-red-600 text-sm mb-3">Failed to reset password.</p>}
            <div className="flex gap-2 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => mutation.mutate()}
                disabled={newPassword.length < 8 || mutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50 transition"
              >
                {mutation.isPending ? 'Resetting…' : 'Reset Password'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Wire it into the row actions**

Add state: `const [resetTarget, setResetTarget] = useState<User | null>(null)`.

Add a "Reset Password" button in the row actions `<td>` (from Task 2.2, now three buttons):

```tsx
                    <button
                      onClick={() => setResetTarget(u)}
                      className="text-xs text-amber-600 hover:text-amber-700 transition mr-3"
                    >
                      Reset Password
                    </button>
```

Add the modal render:

```tsx
      {resetTarget && <ResetPasswordModal user={resetTarget} onClose={() => setResetTarget(null)} />}
```

- [ ] **Step 4: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/users`, click "Reset Password" on a user, enter
a new password, confirm. Verify the modal shows the new password back. Separately, confirm via
`POST /api/auth/login` (e.g. with `curl`) that the new password now authenticates that user.

- [ ] **Step 5: Commit**

```bash
git add APP/ADMIN_APP/src/api/client.ts APP/ADMIN_APP/src/pages/UserManagement.tsx
git commit -m "Add admin password reset UI"
```

---

## Phase 4: Student Activity Heatmap

Implements `admin_dashboard_plan.md` §5.

### Task 4.1: Backend — `GET /api/stats/{user_id}/activity`

**Files:**
- Modify: `backend/app/models/payload.py` (add `ActivityDayCount`)
- Modify: `backend/app/routers/student.py`
- Test: `backend/tests/test_student_router.py`

**Interfaces:**
- Consumes: `UserProgress.timestamp` (existing column, `backend/app/models/db.py`); mirrors the exact `cast(UserProgress.timestamp, Date)` group-by pattern already used in this file (`student.py:2554-2559` and `:2601-2612`) — do not use `func.date_trunc`, it is not this file's convention.
- Produces: `GET /api/stats/{user_id}/activity` → `list[ActivityDayCount]`, each `{date: "YYYY-MM-DD", count: int}` — consumed by Task 4.2

- [ ] **Step 1: Add the `ActivityDayCount` model**

In `backend/app/models/payload.py`, add near `UserStats`:

```python
class ActivityDayCount(BaseModel):
    date: str
    count: int
```

- [ ] **Step 2: Write the failing test**

Add to `backend/tests/test_student_router.py` (check the file's existing `AUTH`/`STUDENT_AUTH`
header constants and reuse them — this project's convention, per `test_users_router.py`, is
`STUDENT_AUTH = {"X-API-Key": "student-test-key"}`):

```python
def test_student_activity_empty(client):
    resp = client.get("/api/stats/1/activity", headers=STUDENT_AUTH)
    assert resp.status_code == 200
    assert resp.json() == []


def test_student_activity_returns_daily_counts(monkeypatch):
    from datetime import date
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class _Row:
        def __init__(self, day, count):
            self.day = day
            self.count = count

    rows = [_Row(date(2026, 6, 30), 7), _Row(date(2026, 7, 1), 3)]

    class _Result:
        def all(self):
            return rows

    class FakeSession:
        async def execute(self, stmt):
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get("/api/stats/1/activity", headers=STUDENT_AUTH)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json() == [
        {"date": "2026-06-30", "count": 7},
        {"date": "2026-07-01", "count": 3},
    ]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_student_router.py -k activity -v`
Expected: FAIL with 404 (route doesn't exist yet)

- [ ] **Step 4: Add the endpoint**

In `backend/app/routers/student.py`, add `ActivityDayCount` to the existing payload import
block, then add the endpoint right after `get_user_stats` (after line 650):

```python
@router.get("/stats/{user_id}/activity", response_model=list[ActivityDayCount])
async def get_user_activity(
    user_id: int,
    days: int = Query(365, ge=1, le=400),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(UserProgress.timestamp, Date).label("day"),
            func.count().label("count"),
        )
        .where(UserProgress.user_id == user_id, UserProgress.timestamp >= cutoff)
        .group_by(cast(UserProgress.timestamp, Date))
        .order_by(cast(UserProgress.timestamp, Date))
    )
    return [
        ActivityDayCount(date=row.day.isoformat(), count=row.count)
        for row in result.all()
    ]
```

`datetime`, `timedelta`, `timezone`, `func`, `cast`, `Date`, and `Query` are all already
imported at the top of `student.py` — no new imports needed beyond the payload model.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_student_router.py -k activity -v`
Expected: PASS (both)

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/payload.py backend/app/routers/student.py backend/tests/test_student_router.py
git commit -m "Add per-day student activity endpoint for the admin heatmap"
```

---

### Task 4.2: Frontend — `ActivityHeatmap` widget in `StudentDetailPanel`

**Files:**
- Modify: `APP/ADMIN_APP/src/api/client.ts`
- Modify: `APP/ADMIN_APP/src/types/index.ts`
- Modify: `APP/ADMIN_APP/src/pages/StudentPerformance.tsx`

**Interfaces:**
- Consumes: `GET /stats/{user_id}/activity` (Task 4.1)
- Produces: `ActivityHeatmap` component — also used by Phase 5's dashboard (optional future widget, not required for Phase 5's v1 widget list)

- [ ] **Step 1: Add `getStudentActivity` to the API client**

In `APP/ADMIN_APP/src/api/client.ts`, add next to `getStudentStats`:

```ts
  getStudentActivity: (userId: number, days = 365) =>
    apiCall(`/stats/${userId}/activity?days=${days}`),
```

- [ ] **Step 2: Add the `ActivityDay` type**

In `APP/ADMIN_APP/src/types/index.ts`, add:

```ts
export interface ActivityDay {
  date: string
  count: number
}
```

- [ ] **Step 3: Add the `ActivityHeatmap` component**

In `APP/ADMIN_APP/src/pages/StudentPerformance.tsx`, add above `function StudentDetailPanel`:

```tsx
function bucketColor(count: number): string {
  if (count === 0) return 'bg-gray-100'
  if (count <= 2) return 'bg-emerald-200'
  if (count <= 5) return 'bg-emerald-300'
  if (count <= 10) return 'bg-emerald-500'
  return 'bg-emerald-700'
}

function ActivityHeatmap({ userId }: { userId: number }) {
  const { data, isLoading } = useQuery<ActivityDay[]>({
    queryKey: ['student-activity', userId],
    queryFn: () => adminApi.getStudentActivity(userId),
    retry: 1,
  })

  if (isLoading) return <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />

  const counts = new Map((data ?? []).map((d) => [d.date, d.count]))

  const today = new Date()
  const days: { date: string; count: number }[] = []
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    days.push({ date: key, count: counts.get(key) ?? 0 })
  }

  const weeks: { date: string; count: number }[][] = []
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7))
  }

  return (
    <div>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Activity</p>
      <div className="flex gap-0.5 overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-0.5">
            {week.map((day) => (
              <div
                key={day.date}
                title={`${day.date}: ${day.count} question${day.count === 1 ? '' : 's'}`}
                className={`w-2.5 h-2.5 rounded-sm ${bucketColor(day.count)}`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Render it in `StudentDetailPanel`**

Find the accuracy section in `StudentDetailPanel`:

```tsx
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Accuracy</p>
        <AccuracyBar value={stats.accuracy} />
      </div>
```

Add the heatmap right after it:

```tsx
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Accuracy</p>
        <AccuracyBar value={stats.accuracy} />
      </div>

      <ActivityHeatmap userId={user.id} />
```

- [ ] **Step 5: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/students`, expand a student with practice
history. Confirm a row of green/grey squares renders, darker green on days with more activity,
and hovering a square shows a tooltip with the date and count.

- [ ] **Step 6: Commit**

```bash
git add APP/ADMIN_APP/src/api/client.ts APP/ADMIN_APP/src/types/index.ts APP/ADMIN_APP/src/pages/StudentPerformance.tsx
git commit -m "Add student activity heatmap to Student Performance"
```

---

## Phase 5: Modular Widget Dashboard — Desktop

Implements `admin_dashboard_plan.md` §9 (desktop half). No backend changes — every widget
reuses an existing `adminApi` call.

### Task 5.1: Install `react-grid-layout`, build the panel shell

**Files:**
- Modify: `APP/ADMIN_APP/package.json`
- Create: `APP/ADMIN_APP/src/components/PanelShell.tsx`

**Interfaces:**
- Consumes: nothing
- Produces: `PanelShell` component (`{title, children}` props) — consumed by every widget in Task 5.2

- [ ] **Step 1: Install the dependency**

Run: `cd APP/ADMIN_APP && npm install react-grid-layout`

Verified compatible: `react-grid-layout@2.2.3`'s peer deps are `react: >= 16.3.0` /
`react-dom: >= 16.3.0` (checked via `npm view react-grid-layout peerDependencies`) — installs
cleanly against this app's React 19 without `--legacy-peer-deps`. It ships its own TypeScript
types (`dist/index.d.ts`); do not also install `@types/react-grid-layout` (that DefinitelyTyped
package is for the older v1 API and will conflict).

- [ ] **Step 2: Build the panel shell**

Create `APP/ADMIN_APP/src/components/PanelShell.tsx`:

```tsx
import type { ReactNode } from 'react'

export function PanelShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl h-full flex flex-col overflow-hidden">
      <div className="panel-drag-handle cursor-move px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between flex-shrink-0">
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{title}</span>
        <span className="text-gray-300 text-xs select-none">⠿</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4">{children}</div>
    </div>
  )
}
```

The `panel-drag-handle` class name is load-bearing — Task 5.3's grid config restricts dragging
to elements with this class (`draggableHandle=".panel-drag-handle"`), so panel content (buttons,
scrollable lists) stays clickable/scrollable instead of always initiating a drag.

- [ ] **Step 3: Manual verification**

Run `cd APP/ADMIN_APP && npm run build` — confirm it compiles with no TypeScript errors (this
step only adds an unused-for-now component, so there's no visual check yet).

- [ ] **Step 4: Commit**

```bash
git add APP/ADMIN_APP/package.json APP/ADMIN_APP/package-lock.json APP/ADMIN_APP/src/components/PanelShell.tsx
git commit -m "Add react-grid-layout dependency and panel shell component"
```

---

### Task 5.2: Build the v1 widgets

**Files:**
- Modify: `APP/ADMIN_APP/src/api/client.ts` (add `getWeakSpots`)
- Modify: `APP/ADMIN_APP/src/types/index.ts` (add `CohortWeakSpots`, `FocusAreaMissRate`)
- Create: `APP/ADMIN_APP/src/components/dashboard/widgets.tsx`

**Interfaces:**
- Consumes: `PanelShell` (Task 5.1); existing `adminApi.listUsers`, `getGenerationAnalytics`, `getAutoReleaseStatus`, `getBatchAnalytics`; new `adminApi.getWeakSpots` → `GET /admin/analytics/weak-spots` (existing backend endpoint, verified response shape by reading `admin.py:2305` / `payload.py`'s `CohortWeakSpotsResponse`/`FocusAreaMissRate` — this endpoint has zero frontend consumers today)
- Produces: `UsersWidget`, `GenerationWidget`, `AutoReleaseWidget`, `RecentBatchesWidget`, `WeakSpotsWidget` — consumed by Task 5.3

- [ ] **Step 1: Add `getWeakSpots` to the API client**

In `APP/ADMIN_APP/src/api/client.ts`, add next to `getTrendAnalytics`:

```ts
  getWeakSpots: (limit = 20) => apiCall(`/admin/analytics/weak-spots?limit=${limit}`),
```

- [ ] **Step 2: Add the weak-spots types**

In `APP/ADMIN_APP/src/types/index.ts`, add:

```ts
export interface FocusAreaMissRate {
  focus_key: string
  domain: string
  total_attempts: number
  unique_students: number
  miss_count: number
  miss_rate: number
}

export interface CohortWeakSpots {
  generated_at: string
  question_wise_misses: unknown[]
  focus_area_misses: FocusAreaMissRate[]
}
```

- [ ] **Step 3: Build the widgets**

Create `APP/ADMIN_APP/src/components/dashboard/widgets.tsx`:

```tsx
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../api/client'
import { PanelShell } from '../PanelShell'
import type { User, GenerationAnalytics, BatchAnalytics, CohortWeakSpots } from '../../types'

export function UsersWidget() {
  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => adminApi.listUsers(),
    retry: 1,
  })
  return (
    <PanelShell title="Users">
      {isLoading ? (
        <div className="h-12 bg-gray-100 rounded animate-pulse" />
      ) : (
        <p className="text-3xl font-bold text-gray-800">{users?.length ?? '—'}</p>
      )}
      <p className="text-xs text-gray-400 mt-1">Total registered students</p>
    </PanelShell>
  )
}

export function GenerationWidget() {
  const { data, isLoading } = useQuery<GenerationAnalytics>({
    queryKey: ['analytics-generation'],
    queryFn: () => adminApi.getGenerationAnalytics(),
    retry: 1,
  })
  const rate = data ? Math.round((data.approve_rate ?? 0) * 100) : null
  return (
    <PanelShell title="Generation Approve Rate">
      {isLoading ? (
        <div className="h-12 bg-gray-100 rounded animate-pulse" />
      ) : (
        <p className={`text-3xl font-bold ${rate !== null && rate >= 70 ? 'text-emerald-600' : 'text-amber-600'}`}>
          {rate !== null ? `${rate}%` : '—'}
        </p>
      )}
      <p className="text-xs text-gray-400 mt-1">{data?.total_generated ?? 0} generated total</p>
    </PanelShell>
  )
}

export function AutoReleaseWidget() {
  const { data } = useQuery({
    queryKey: ['auto-release-status'],
    queryFn: () => adminApi.getAutoReleaseStatus(),
    retry: 1,
  })
  return (
    <PanelShell title="Auto-Release">
      <p className={`text-lg font-semibold ${data?.enabled ? 'text-emerald-600' : 'text-red-500'}`}>
        {data?.enabled ? 'Enabled' : 'Disabled'}
      </p>
      <p className="text-xs text-gray-400 mt-1">Manage from Pipeline & Backend page</p>
    </PanelShell>
  )
}

export function RecentBatchesWidget() {
  const { data, isLoading } = useQuery<BatchAnalytics>({
    queryKey: ['analytics-batches'],
    queryFn: () => adminApi.getBatchAnalytics(),
    retry: 1,
  })
  const rows = data?.recent_batches?.slice(0, 5) ?? []
  return (
    <PanelShell title="Recent Batches">
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">No batches yet.</p>
      ) : (
        <ul className="space-y-1.5">
          {rows.map((b) => (
            <li key={b.id} className="flex justify-between text-xs">
              <span className="text-gray-500 font-mono">{b.id.slice(0, 8)}…</span>
              <span className="text-emerald-600">{b.accepted_count} ok</span>
              <span className="text-red-500">{b.rejected_count} rej</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  )
}

export function WeakSpotsWidget() {
  const { data, isLoading } = useQuery<CohortWeakSpots>({
    queryKey: ['analytics-weak-spots'],
    queryFn: () => adminApi.getWeakSpots(),
    retry: 1,
  })
  const top = data?.focus_area_misses?.slice(0, 5) ?? []
  return (
    <PanelShell title="Cohort Weak Spots">
      {isLoading ? (
        <div className="h-16 bg-gray-100 rounded animate-pulse" />
      ) : top.length === 0 ? (
        <p className="text-sm text-gray-400">Not enough data yet.</p>
      ) : (
        <ul className="space-y-1.5">
          {top.map((f) => (
            <li key={f.focus_key} className="flex justify-between text-xs">
              <span className="text-gray-600">{f.focus_key.replace(/_/g, ' ')}</span>
              <span className="text-red-500 font-medium">{Math.round(f.miss_rate * 100)}% miss</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  )
}
```

- [ ] **Step 4: Manual verification**

Run `cd APP/ADMIN_APP && npm run build` — confirm no TypeScript errors. Full visual
verification happens in Task 5.3 once these are placed on the grid.

- [ ] **Step 5: Commit**

```bash
git add APP/ADMIN_APP/src/api/client.ts APP/ADMIN_APP/src/types/index.ts APP/ADMIN_APP/src/components/dashboard/widgets.tsx
git commit -m "Add dashboard widget components"
```

---

### Task 5.3: `Dashboard` page — grid wiring and `localStorage` persistence

**Files:**
- Create: `APP/ADMIN_APP/src/pages/Dashboard.tsx`

**Interfaces:**
- Consumes: widgets from Task 5.2, `react-grid-layout`'s `Responsive`/`WidthProvider`/`Layout` exports
- Produces: `Dashboard` component — consumed by Task 5.4 (routing)

- [ ] **Step 1: Build the dashboard page**

Create `APP/ADMIN_APP/src/pages/Dashboard.tsx`:

```tsx
import { useCallback, useState } from 'react'
import { Responsive, WidthProvider, type Layout } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import {
  UsersWidget,
  GenerationWidget,
  AutoReleaseWidget,
  RecentBatchesWidget,
  WeakSpotsWidget,
} from '../components/dashboard/widgets'

const ResponsiveGridLayout = WidthProvider(Responsive)

const WIDGETS: Record<string, () => JSX.Element> = {
  users: UsersWidget,
  generation: GenerationWidget,
  autoRelease: AutoReleaseWidget,
  weakSpots: WeakSpotsWidget,
  recentBatches: RecentBatchesWidget,
}

const DEFAULT_LAYOUTS: Record<string, Layout[]> = {
  lg: [
    { i: 'users', x: 0, y: 0, w: 3, h: 3 },
    { i: 'generation', x: 3, y: 0, w: 3, h: 3 },
    { i: 'autoRelease', x: 6, y: 0, w: 3, h: 3 },
    { i: 'weakSpots', x: 9, y: 0, w: 3, h: 5 },
    { i: 'recentBatches', x: 0, y: 3, w: 9, h: 5 },
  ],
  md: [
    { i: 'users', x: 0, y: 0, w: 4, h: 3 },
    { i: 'generation', x: 4, y: 0, w: 4, h: 3 },
    { i: 'autoRelease', x: 0, y: 3, w: 4, h: 3 },
    { i: 'weakSpots', x: 4, y: 3, w: 4, h: 5 },
    { i: 'recentBatches', x: 0, y: 6, w: 8, h: 5 },
  ],
}

const STORAGE_KEY = 'admin-dashboard-layouts-v1'

function loadLayouts(): Record<string, Layout[]> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : DEFAULT_LAYOUTS
  } catch {
    return DEFAULT_LAYOUTS
  }
}

export function Dashboard() {
  const [layouts, setLayouts] = useState<Record<string, Layout[]>>(loadLayouts)

  const handleLayoutChange = useCallback((_current: Layout[], all: Record<string, Layout[]>) => {
    setLayouts(all)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
  }, [])

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Dashboard</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Drag panels by their header to rearrange. Layout is saved automatically.
        </p>
      </div>
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1024, md: 768, sm: 480 }}
        cols={{ lg: 12, md: 8, sm: 4 }}
        rowHeight={60}
        draggableHandle=".panel-drag-handle"
        onLayoutChange={handleLayoutChange}
      >
        {Object.entries(WIDGETS).map(([key, Widget]) => (
          <div key={key}>
            <Widget />
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  )
}
```

- [ ] **Step 2: Manual verification**

This page isn't routed yet (Task 5.4) — verify it compiles: `cd APP/ADMIN_APP && npm run build`.

- [ ] **Step 3: Commit**

```bash
git add APP/ADMIN_APP/src/pages/Dashboard.tsx
git commit -m "Add Dashboard page with react-grid-layout grid"
```

---

### Task 5.4: Route wiring — make `/dashboard` the default landing page

**Files:**
- Modify: `APP/ADMIN_APP/src/App.tsx`
- Modify: `APP/ADMIN_APP/src/components/Layout.tsx`

**Interfaces:**
- Consumes: `Dashboard` page (Task 5.3)
- Produces: none (leaf feature; completes Phase 5)

- [ ] **Step 1: Add the route and change the default redirect**

In `APP/ADMIN_APP/src/App.tsx`, add the import:

```tsx
import { Dashboard } from './pages/Dashboard'
```

Replace:

```tsx
            <Route index element={<Navigate to="/users" replace />} />
            <Route path="/users" element={<UserManagement />} />
```

with:

```tsx
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/users" element={<UserManagement />} />
```

- [ ] **Step 2: Add the nav link**

In `APP/ADMIN_APP/src/components/Layout.tsx`, prepend to the `NAV` array:

```tsx
const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/users', label: 'User Management', icon: '👥' },
  { to: '/data', label: 'Data Management', icon: '📋' },
  { to: '/students', label: 'Student Performance', icon: '📈' },
  { to: '/pipeline', label: 'Pipeline & Backend', icon: '⚙️' },
]
```

- [ ] **Step 3: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`. Confirm visiting `/` redirects to `/dashboard`, the nav
shows "Dashboard" first and highlights it as active, all 5 widgets render with real data, and
dragging a panel by its header (not its content) moves it — reload the page and confirm the
rearranged position persists.

- [ ] **Step 4: Commit**

```bash
git add APP/ADMIN_APP/src/App.tsx APP/ADMIN_APP/src/components/Layout.tsx
git commit -m "Make the modular dashboard the default landing page"
```

---

## Phase 6: iPad Interactivity Layer

Implements `admin_dashboard_plan.md` §9 (iPad half). Only start this phase after Phase 5 has
shipped and been used for a few days on desktop — the design's whole premise is desktop-first.

**Scope note:** `react-grid-layout` already handles touch dragging out of the box (its internal
`react-draggable` dependency responds to pointer events, which cover touch) and already animates
position changes via CSS transforms (`useCSSTransforms`, on by default) — so basic drag-to-
reorder already works on iPad after Phase 5 alone. This phase does NOT attempt to layer
`framer-motion`'s `layout` animation prop on top of `react-grid-layout`'s own absolute-position
transforms — the two systems both want to own an element's transform, and forcing them together
is a known source of visual jank, not a clean win. Instead, `framer-motion` is used only for an
additive entrance animation (does not touch a panel's position while it's grid-managed), and the
rest of this phase is touch-target sizing and a feature-parity QA pass.

### Task 6.1: `framer-motion` entrance stagger

**Files:**
- Modify: `APP/ADMIN_APP/src/pages/Dashboard.tsx`

**Interfaces:**
- Consumes: `framer-motion` (already installed — `package.json` `^12.40.0`)
- Produces: none (leaf feature)

- [ ] **Step 1: Wrap each panel in a staggered fade-in**

In `APP/ADMIN_APP/src/pages/Dashboard.tsx`, add the import:

```tsx
import { motion } from 'framer-motion'
```

Replace:

```tsx
        {Object.entries(WIDGETS).map(([key, Widget]) => (
          <div key={key}>
            <Widget />
          </div>
        ))}
```

with:

```tsx
        {Object.entries(WIDGETS).map(([key, Widget], index) => (
          <div key={key}>
            <motion.div
              className="h-full"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.25 }}
            >
              <Widget />
            </motion.div>
          </div>
        ))}
```

The outer `<div key={key}>` stays untouched by `framer-motion` — `react-grid-layout` applies its
positioning transform to that element; the `motion.div` inside it only animates opacity/y on
mount, which doesn't conflict.

- [ ] **Step 2: Manual verification**

Run: `cd APP/ADMIN_APP && npm run dev`, open `/dashboard`, hard-refresh. Confirm panels fade/
slide in with a slight stagger on load, and dragging still works exactly as before (the entrance
animation only plays once, on mount).

- [ ] **Step 3: Commit**

```bash
git add APP/ADMIN_APP/src/pages/Dashboard.tsx
git commit -m "Add entrance stagger animation to dashboard panels"
```

---

### Task 6.2: Touch drag-handle sizing for iPad

**Files:**
- Modify: `APP/ADMIN_APP/src/components/PanelShell.tsx`

**Interfaces:**
- Consumes: none
- Produces: none (leaf feature)

- [ ] **Step 1: Increase the drag handle's touch target at narrower (iPad-range) widths**

Apple's HIG minimum touch target is 44×44pt. The current handle bar is `py-2.5` (~36px tall
including text) — comfortable for a mouse, tight for touch. In
`APP/ADMIN_APP/src/components/PanelShell.tsx`, replace:

```tsx
      <div className="panel-drag-handle cursor-move px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between flex-shrink-0">
```

with:

```tsx
      <div className="panel-drag-handle cursor-move px-4 py-2.5 md:py-3.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between flex-shrink-0 touch-none">
```

`touch-none` (Tailwind's `touch-action: none`) prevents the browser's native scroll/zoom
gestures from fighting with `react-grid-layout`'s own touch-drag handling on the handle bar
specifically — it's scoped to the handle, not the whole panel, so the panel's own scrollable
content (e.g. `RecentBatchesWidget`'s list) still scrolls normally with touch.

- [ ] **Step 2: Manual verification**

In Chrome DevTools, toggle device emulation to "iPad Pro" (or an equivalent ~768-1024px width
touch device), open `/dashboard`. Confirm the drag handle bar is visibly taller/easier to grab,
touch-drag a panel to reorder it, and confirm scrolling inside a widget's content (if it
overflows) still works without triggering a drag.

- [ ] **Step 3: Commit**

```bash
git add APP/ADMIN_APP/src/components/PanelShell.tsx
git commit -m "Size dashboard drag handles for touch on iPad"
```

---

### Task 6.3: Feature-parity QA pass

**Files:** none (verification-only task)

- [ ] **Step 1: Build the parity checklist**

List every admin action reachable from desktop, gathered from this plan plus the existing
pages: create/edit/delete/reset-password user (Phases 2-3), approve/reject/edit question,
browse tests (Phase 1), view student activity heatmap (Phase 4), toggle auto-release, all
dashboard widgets (Phase 5).

- [ ] **Step 2: Walk the checklist on iPad**

Using either a physical iPad or Chrome DevTools device emulation at iPad width, go through
every item in the Step 1 list and confirm it's reachable and functional — same modals open,
same forms submit, same data displays. Record any item that's harder to use or visually broken
at iPad width.

- [ ] **Step 3: Fix any parity gaps found**

For each gap recorded in Step 2, make the minimal CSS/layout fix needed (e.g. a modal that's
too wide for the viewport, a button that's not reachable behind the grid). There's no
prescriptive code here since the gaps are unknown until Step 2 runs — this step is "fix what
Step 2 finds," not "implement nothing."

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Fix iPad feature-parity gaps found in QA pass"
```
