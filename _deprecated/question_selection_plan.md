# Question Selection Plan

Status: Draft for implementation tasking  
Last updated: 2026-06-25

## Purpose

Define one shared backend strategy for choosing questions across all student test
and practice modes.

The current app has several independent question-picking paths:

- Diagnostic uses `backend/app/diagnostic/selector.py`.
- Practice test uses `GET /api/questions`.
- Adaptive module 2 uses inline logic in `backend/app/routers/student.py`.
- Mixed practice fetches random single questions.
- Concept practice routes through grammar practice filters.
- Spaced repetition and missed-question review have their own student-progress
  logic.

This plan consolidates those paths into a reusable selector layer so each mode
has clear product rules, server-side filtering, stable fallbacks, and testable
behavior.

## Goals

1. Centralize question selection in backend code.
2. Prevent answer-key leakage for test-condition modes.
3. Make practice-test and adaptive modules SAT-like: 27 English questions,
   32 minutes, server-selected module order.
4. Preserve practice modes that give immediate feedback.
5. Use student stats when the mode calls for personalization.
6. Make thin-bank fallback explicit and auditable.
7. Keep frontend components focused on presentation, not selection policy.

## Non-Goals

- Full CAT or IRT scoring.
- Public production deployment hardening.
- Generated-bank selection beyond a controlled fallback policy.
- Replacing all practice UI in the first implementation slice.

## Current Bank Reality

As of the current local DB:

- 60 active official verbal questions.
- Source module `01`: 33 active questions.
- Source module `02`: 27 active questions.
- Generated active questions: 0.
- The bank is enough for a first 27-question English module, but not enough for
  unlimited no-repeat adaptive testing.

The selector must therefore support:

- Exact official-module selection where available.
- Blueprint-based selection from a larger pool.
- Fallback with a coverage report when the bank is thin.
- Optional reuse after recency/seen filters are exhausted.

## Shared Selection Service

Create a backend package:

```text
backend/app/questions/
  selection.py
  policies.py
  payloads.py
```

The core function should be mode-agnostic:

```python
async def select_questions(
    db: AsyncSession,
    request: QuestionSelectionRequest,
) -> QuestionSelectionResult:
    ...
```

Input shape:

```python
class QuestionSelectionRequest(BaseModel):
    user_id: int
    mode: Literal[
        "diagnostic",
        "practice_test",
        "adaptive_module_1",
        "adaptive_module_2_lower",
        "adaptive_module_2_higher",
        "grammar_practice",
        "mixed_practice",
        "review",
    ]
    count: int
    domain: Literal["grammar", "reading", "mixed"] | None = None
    source_policy: Literal["official_only", "generated_ok", "mixed"] = "official_only"
    exclude_recent_days: int | None = None
    exclude_seen_correct: bool = False
    blueprint_id: str | None = None
    focus_keys: list[str] = []
    difficulty_policy: str | None = None
    seed: str | None = None
```

Output shape:

```python
class QuestionSelectionResult(BaseModel):
    question_ids: list[str]
    mode: str
    count_requested: int
    count_returned: int
    coverage_report: dict
    selection_meta: dict
```

## Shared Rules

All modes:

1. Only select active questions unless a mode explicitly requests otherwise.
2. Do not duplicate question IDs within one selection result.
3. Prefer current canonical question versions.
4. Prefer official questions in test-condition modes.
5. Return questions in presentation order, not arbitrary DB order.
6. Record fallback levels in `coverage_report`.
7. Keep answer-key fields out of no-answer payloads.

Fallback ladder:

1. Exact slot match.
2. Drop focus/trap preference.
3. Drop difficulty.
4. Drop recent/seen exclusion.
5. Drop source-module preference.
6. Any active question in same domain.
7. Any active question, marked as a gap.

## Mode Policies

### Diagnostic

Purpose: produce a first weakness profile under test-like conditions.

Current behavior:

- 16-question blueprint.
- Answers hidden during test.
- Uses diagnostic session endpoints.
- Timer continues as overtime after 0 rather than auto-ending.

Selection policy:

- Use fixed `diagnostic_v1` blueprint.
- Prefer unseen active official questions.
- Keep 10 grammar / 6 reading balance until v2.
- Return no-answer payload.
- Persist ordered `question_ids` on `DiagnosticSession`.

Future v2:

- Optionally move to a 27-question English module diagnostic after the bank can
  support enough coverage.

### Practice Test

Purpose: SAT-like English module practice.

Locked behavior:

- 27 questions maximum and default.
- 32 minutes.
- Auto-submit when time expires.
- Same runner style as diagnostic should be the target.

Selection policy:

- Use `practice_test_english_v1`.
- Count is capped at 27 server-side even if the frontend sends a larger count.
- Prefer official active verbal questions.
- For now, select from available English modules or a balanced blueprint.
- Do not expose answer keys during the test.
- On submit, backend computes correctness and writes `UserProgress`.

Open decision:

- Whether practice test should always mirror source module `02` exactly or use a
  27-slot blueprint randomized within slots. Recommendation: blueprint
  randomized within slots, with a source-module mode available for official
  replay.

### Adaptive English Test

Purpose: two-module English test flow.

Target behavior:

- Module 1: 27 questions, 32 minutes, auto-submit.
- Module 2: 27 questions, 32 minutes, auto-submit.
- Module 2 route is `higher` or `lower` based on module 1 score.
- Same UI shell as diagnostic/test runner.

Selection policy:

- Module 1 uses `adaptive_english_module_1_v1`.
- Module 2 lower uses easier/broader slots.
- Module 2 higher uses harder slots plus weak-area targeting.
- Both module selections must be server-side.
- Module 1 accuracy must be computed server-side from submitted answers, not
  frontend-only fields.

Current gap:

- Existing module 2 endpoint accepts frontend-computed module 1 accuracy.
- Existing frontend runner computes accuracy from `_isCorrect`, which is not
  populated.
- This must be replaced before adaptive routing can be trusted.

### Grammar Practice

Purpose: targeted drill with immediate feedback.

Selection policy:

- Accept explicit domain/focus filters.
- Prefer weak concepts from student stats when no focus is provided.
- Feedback and explanations can be shown after each answer.
- Answer keys may be used after submission, not before.
- Generated questions may be allowed later if tagged and reviewed.

### Mixed Practice

Purpose: lightweight practice session across weak areas.

Selection policy:

- Blend three pools:
  - high weakness score,
  - unseen official questions,
  - due or recently missed review questions.
- Do not use pure random as the primary policy.
- Immediate feedback is allowed.
- Count is user-configurable with a reasonable cap.

Recommended starting mix:

- 50% weakest current focus areas.
- 30% unseen active questions.
- 20% review/missed questions.

### Review / Spaced Repetition

Purpose: reinforce previously missed or due material.

Selection policy:

- Due spaced-repetition questions first.
- Then unresolved missed questions.
- Sort by due date, weakness score, and recency.
- Do not require module-style coverage.

## Payload Contracts

Test-condition payloads must not include:

- `current_correct_option_label`
- `current_explanation_text`
- `explanation_short`
- option correctness flags
- any answer-key equivalent

Practice-feedback payloads may include explanations only after an answer is
submitted, or through a post-submit result endpoint.

## API Direction

Add selector-backed endpoints:

```text
POST /api/test-session/start
POST /api/test-session/{session_id}/answer
POST /api/test-session/{session_id}/complete
POST /api/practice/select
```

Keep existing endpoints during migration, but route their selection through the
shared selector as they are touched.

## Session Persistence

Test-condition modes need persisted sessions:

- `DiagnosticSession` can remain diagnostic-specific.
- `TestSessionResults` should become the adaptive/practice test session anchor,
  or be replaced by a more complete `TestSession` model.

Required per-session data:

- user id
- mode
- module number
- route difficulty
- ordered question ids
- started/completed timestamps
- total/correct/accuracy
- duration
- coverage report

## Frontend Direction

The diagnostic runner should become the reference UI:

- one question at a time
- numbered question palette
- back/next
- flag
- no answer reveal during test
- finish/submit button
- test-condition timer behavior by mode

Timer behavior by mode:

- Diagnostic: after time runs out, switch to overtime stopwatch.
- Practice/adaptive test: auto-submit at 32 minutes.

## Acceptance Criteria

The selection system is ready when:

1. Diagnostic still returns its 16-question blueprint.
2. Practice test gets no more than 27 questions and no answer keys during test.
3. Adaptive module 1 and module 2 both use server-side selected question IDs.
4. Module 2 routing is based on server-computed module 1 score.
5. Mixed practice no longer uses pure random as its only policy.
6. Selection reports explain fallback and coverage gaps.
7. Frontend no longer computes test routing accuracy from unavailable fields.
