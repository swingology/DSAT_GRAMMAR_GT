# Question Selection Tasks

Companion to `question_selection_plan.md`.

Status: Draft task list  
Last updated: 2026-06-25

## 0. Working Rules

- Work one task at a time.
- Do not start a task whose dependencies are unmet.
- Keep selection policy server-side.
- Preserve current diagnostic behavior while migrating other modes.
- Test-condition modes must not leak answer keys.
- Frontend should not compute correctness for routed tests.

## 1. Current Code Map

Backend:

- Diagnostic selector: `backend/app/diagnostic/selector.py`
- Diagnostic blueprint: `backend/app/diagnostic/blueprint.py`
- Question pool query helpers: `backend/app/diagnostic/queries.py`
- Student endpoints: `backend/app/routers/student.py`
- Payloads: `backend/app/models/payload.py`
- ORM models: `backend/app/models/db.py`

Frontend:

- Diagnostic runner: `APP/STUDENT_APP_REDUX/src/components/diagnostic/DiagnosticTestRunner.tsx`
- Diagnostic page: `APP/STUDENT_APP_REDUX/src/pages/DiagnosticPage.tsx`
- Practice test page: `APP/STUDENT_APP_REDUX/src/pages/PracticeTestPage.tsx`
- Current adaptive/test runner: `APP/STUDENT_APP_REDUX/src/components/dashboard/TestModeTab.tsx`
- Mixed practice: `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`
- API client: `APP/STUDENT_APP_REDUX/src/api/client.ts`

## 2. Backend Tasks

### QS-B01 - Create Shared Selection Package

Depends: none

Files:

- `backend/app/questions/__init__.py`
- `backend/app/questions/selection.py`
- `backend/app/questions/policies.py`
- `backend/tests/test_question_selection.py`

Spec:

- Add `QuestionSelectionRequest`.
- Add `QuestionSelectionResult`.
- Add `select_questions(db, request)`.
- Implement active-question filtering and no-duplicate behavior.
- Keep the first implementation thin by reusing existing diagnostic query
  helpers where possible.

Acceptance:

- Unit test proves `count_requested` and `count_returned`.
- Unit test proves no duplicate question IDs.
- Unit test proves inactive questions are excluded.

Verify:

```bash
cd backend
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_question_selection.py -q
```

### QS-B02 - Move Diagnostic Selection Behind Shared Interface

Depends: QS-B01

Files:

- `backend/app/diagnostic/selector.py`
- `backend/app/questions/selection.py`
- `backend/app/routers/student.py`
- existing diagnostic tests

Spec:

- Keep `assemble_diagnostic()` API stable.
- Internally route slot filling through shared selection helpers.
- Preserve current `coverage_report` shape.

Acceptance:

- Existing diagnostic endpoint behavior is unchanged.
- `POST /diagnostic/start` still returns 16 no-answer questions.
- Existing diagnostic tests pass.

### QS-B03 - Define No-Answer Test Question Payload

Depends: QS-B01

Files:

- `backend/app/questions/payloads.py`
- `backend/app/models/payload.py`
- `backend/app/routers/student.py`

Spec:

- Create one serializer for test-condition questions.
- It must strip answer keys and explanation fields.
- Use it for diagnostic, practice test, and adaptive test endpoints.

Acceptance:

- Test payload has option labels/text only.
- Test payload does not contain `current_correct_option_label`.
- Test payload does not contain explanation text.

### QS-B04 - Add Practice Test Start Endpoint

Depends: QS-B01, QS-B03

Files:

- `backend/app/routers/student.py`
- `backend/app/models/payload.py`
- `backend/tests/test_practice_test_selection.py`

Endpoint:

```text
POST /api/test-session/start
```

Request:

```json
{
  "user_token": "...",
  "mode": "practice_test",
  "question_count": 27
}
```

Spec:

- Clamp `question_count` to 27.
- Select 27 English/verbal questions.
- Persist ordered question IDs.
- Return no-answer payload.
- Return `time_limit_seconds = 1920`.

Acceptance:

- Requesting 33 returns at most 27.
- Response has no answer keys.
- `coverage_report` is present.

### QS-B05 - Add Test Answer And Complete Endpoints

Depends: QS-B04

Files:

- `backend/app/routers/student.py`
- `backend/app/models/db.py`
- `backend/app/models/payload.py`
- `backend/tests/test_practice_test_submission.py`

Endpoints:

```text
POST /api/test-session/{session_id}/answer
POST /api/test-session/{session_id}/complete
```

Spec:

- Backend computes correctness from selected option.
- Writes `UserProgress`.
- Completion computes score from server-side records.
- Supports auto-submit with unanswered questions.

Acceptance:

- Frontend does not need answer keys.
- Unanswered questions count against total score.
- Completed session returns total/correct/accuracy/duration.

### QS-B06 - Replace Adaptive Module 1 Accuracy With Server Score

Depends: QS-B04, QS-B05

Files:

- `backend/app/routers/student.py`
- `backend/app/models/payload.py`
- `backend/tests/test_adaptive_test_routing.py`

Spec:

- Module 1 completion must use stored answer records.
- Remove trust in frontend-supplied `module_1_accuracy`.
- Keep threshold initially at 70%.

Acceptance:

- A student cannot route higher by sending fake accuracy.
- Routing result matches persisted module 1 score.

### QS-B07 - Move Module 2 Selection Into Shared Selector

Depends: QS-B06

Files:

- `backend/app/questions/policies.py`
- `backend/app/routers/student.py`
- `backend/tests/test_adaptive_test_routing.py`

Spec:

- Replace inline `module_2_blueprint` query with shared selector.
- Lower route uses lower/medium broader coverage.
- Higher route uses harder/weak-area-weighted selection.
- Still returns 27 questions.

Acceptance:

- Module 2 lower and higher return different policy metadata.
- Both return no-answer payloads.
- Both cap at 27.

### QS-B08 - Add Mixed Practice Selection Policy

Depends: QS-B01

Files:

- `backend/app/questions/policies.py`
- `backend/app/routers/student.py`
- `backend/tests/test_mixed_practice_selection.py`

Spec:

- Add a selector-backed practice endpoint or extend `/questions` with a named
  selection mode.
- Blend weak areas, unseen questions, and review/missed questions.
- Avoid pure random as the only policy.

Acceptance:

- New student gets unseen active questions.
- Returning student gets weak-area weighting.
- Selection metadata reports pool counts.

## 3. Frontend Tasks

### QS-F01 - Add API Client Methods For Test Sessions

Depends: QS-B04, QS-B05

Files:

- `APP/STUDENT_APP_REDUX/src/api/client.ts`
- `APP/STUDENT_APP_REDUX/src/types/index.ts`

Spec:

- Add `testSessionStart`.
- Add `testSessionAnswer`.
- Add `testSessionComplete`.
- Add typed no-answer test question response.

Acceptance:

- TypeScript compile passes.
- No existing diagnostic API methods break.

### QS-F02 - Extract Shared Test Runner From Diagnostic Runner

Depends: none

Files:

- `APP/STUDENT_APP_REDUX/src/components/diagnostic/DiagnosticTestRunner.tsx`
- `APP/STUDENT_APP_REDUX/src/components/test/QuestionModuleRunner.tsx`
- frontend tests

Spec:

- Extract reusable one-question-at-a-time runner.
- Preserve diagnostic behavior.
- Support timer mode:
  - `overtime` for diagnostic.
  - `autosubmit` for practice/adaptive tests.

Acceptance:

- Diagnostic still has no answer reveal.
- Practice mode can auto-submit.
- Runner has palette, back/next, flag, submit.

### QS-F03 - Wire Practice Test To Test Session API

Depends: QS-F01, QS-F02, QS-B04, QS-B05

Files:

- `APP/STUDENT_APP_REDUX/src/pages/PracticeTestPage.tsx`
- `APP/STUDENT_APP_REDUX/src/components/dashboard/TestModeTab.tsx`

Spec:

- Start server-side practice test session.
- Render returned 27 no-answer questions.
- Submit answers to server.
- Auto-submit at 32 minutes.
- Remove dependency on answer-key fields during test.

Acceptance:

- `/test?questions=33` still renders max 27.
- No answer keys are present in frontend test state.
- Expiry calls complete endpoint.

### QS-F04 - Wire Adaptive Module 1 And 2 To Test Session API

Depends: QS-F03, QS-B06, QS-B07

Files:

- `APP/STUDENT_APP_REDUX/src/components/dashboard/TestModeTab.tsx`
- `APP/STUDENT_APP_REDUX/src/pages/PracticeTestPage.tsx`

Spec:

- Module 1 uses server-selected 27 questions.
- Module 1 complete gets server-computed routing.
- Module 2 start gets routed 27 questions.
- Both modules use the shared runner.

Acceptance:

- No `_isCorrect` routing logic remains.
- Module 2 route is based on backend result.
- Both modules auto-submit after 32 minutes.

### QS-F05 - Wire Mixed Practice To Selection Policy

Depends: QS-B08, QS-F01

Files:

- `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`
- `APP/STUDENT_APP_REDUX/src/api/client.ts`

Spec:

- Stop fetching one random question per index.
- Start a mixed-practice selection session or fetch a selector batch.
- Keep immediate feedback behavior.

Acceptance:

- Mixed practice can explain selection source in metadata if needed.
- New student and returning student both get useful questions.

## 4. Data And Migration Tasks

### QS-D01 - Decide Test Session Storage Model

Depends: QS-B04

Spec:

- Decide whether to extend `TestSessionResults` or add a new `TestSession`
  table.
- Required fields:
  - user id
  - mode
  - module number
  - route difficulty
  - ordered question ids
  - coverage report
  - started/completed timestamps
  - scoring fields

Acceptance:

- ADR or plan update records the decision.
- Follow-up migration task is created if needed.

### QS-D02 - Add Session Storage Migration

Depends: QS-D01

Spec:

- Add/modify DB tables for practice/adaptive test sessions.
- Add unique constraints needed for one answer per session/question if upserting.

Acceptance:

- Alembic migration applies cleanly.
- Existing diagnostic and `UserProgress` rows remain valid.

## 5. Recommended Implementation Order

1. QS-B01 shared selector package.
2. QS-B03 no-answer payload serializer.
3. QS-B04 practice test start endpoint.
4. QS-B05 practice test answer/complete endpoints.
5. QS-F01 API client methods.
6. QS-F02 shared runner extraction.
7. QS-F03 practice test wiring.
8. QS-B06/QS-B07 adaptive server routing.
9. QS-F04 adaptive frontend wiring.
10. QS-B08/QS-F05 mixed practice.

## 6. Known Risks

- The current active bank is thin. A strict 27+27 no-repeat adaptive test will
  require reuse or more ingested/generated questions.
- Current `/questions` response leaks answer keys; test-condition flows must not
  use it directly.
- Current adaptive frontend scoring uses `_isCorrect`, which is not populated.
- Docker/Vite dev server is being used for Tailscale exposure; a future
  production deploy should serve built assets through a production server.
