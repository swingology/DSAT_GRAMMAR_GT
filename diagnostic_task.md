# Diagnostic Test — Execution Tasks

Companion to `DIAGNOSTIC_TEST_PLAN.md`. Each task is **self-contained**: an LLM can pick up any
single task, read only this file + the named source files, and complete it without re-deriving
context. Tasks are ordered by dependency; the **Depends** field is authoritative.

---

## 0. How to use this document

- Work one task at a time. Read the task's **Files**, **Spec**, and **Acceptance** sections.
- Do **not** start a task whose **Depends** are unmet (unless stubbing behind an interface).
- After each task: run its **Verify** command, then tick the **Done-when** checklist.
- Commit per task using the message in **Commit** (see §1 conventions). One task ≈ one commit.
- If you discover a bug, append to `.wolf/buglog.json`; if you learn a convention, update
  `.wolf/cerebrum.md` (project rule).

### Decisions already locked (do not relitigate)
1. This **replaces** the adaptive `DiagnosticTab` runner entirely.
2. Question source = **generated/annotated bank** (not official PDFs).
3. Format = **fixed blueprint** (v1 = **16 slots** vs official bank), **low→medium** ramp
   (no `high` exists in the bank; no CAT, no 2-module). The original "27-slot easy→hard" vision is
   deferred to a v2 that requires a generated bank — see `DIAGNOSTIC_TEST_PLAN.md` §7b.
4. **Test mode**: timer, answers hidden until a review/report screen at the end.

---

## 1. Shared conventions & environment

### Repo paths
- Repo root: `/home/jb/DSAT_REDUX_MD`
- Backend (FastAPI, SQLAlchemy async): `backend/app/`
  - Routers: `backend/app/routers/student.py`
  - ORM models: `backend/app/models/db.py`
  - Pydantic payloads: `backend/app/models/payload.py`
  - Taxonomy/ontology: `backend/app/models/ontology.py`
  - Tests: `backend/tests/`
- Frontend (React + TS + Vite + react-query + framer-motion + Tailwind): `APP/STUDENT_APP_REDUX/`
  - Pages: `src/pages/`, Components: `src/components/`, API: `src/api/client.ts`, Types: `src/types.ts`
  - Hooks: `src/hooks/`

### Backend test runner (the repo `.venv` is broken — use this exact workaround)
```bash
cd /home/jb/DSAT_REDUX_MD/backend
export UV_PROJECT_ENVIRONMENT=$PWD/.venv-jb
uv sync --frozen --all-extras          # first time only
.venv-jb/bin/python -m pytest tests/<file> -v
```
Do **not** delete the root-owned `.venv`.

### Frontend test runner (must use node 20 — node 24 crashes V8 WASM on WSL2)
```bash
cd /home/jb/DSAT_REDUX_MD/APP/STUDENT_APP_REDUX
source ~/.nvm/nvm.sh && nvm use 20.20.2
npx vitest run <file>          # add { timeout: 5000 } to waitFor — jsdom is slow here
npx tsc --noEmit               # typecheck
```

### Dev stack (needed for P0 + any live/E2E task)
```bash
/dev-stack            # Postgres :5434 (dsat/dsat_dev) + backend :8000 + frontend :5173
/dev-stack status
```

### Commit message rules (project)
- Never reference "Claude/AI/assistant". Active voice, technical, describe the change.
- Format: `feat(diagnostic): <what>` / `fix(diagnostic): <what>` / `test(diagnostic): <what>`.

### Difficulty values — RESOLVED (TASK-B00, 2026-06-23)
The live bank's `annotation_jsonb.difficulty_overall` contains **only `low` and `medium`** (+ many
`null`). **No `high`.** So v1 ramp is **low → medium**; `DIFFICULTY_TIERS = ("low","medium")`.
`null`-difficulty questions are common (esp. expression_of_ideas) — treat as `medium` for ordering
or sort last within tier (TASK-B01 decides). Ontology still defines `high`; just don't require it.

### Domain & reading classification — CRITICAL (TASK-B00, bug-761)
This bank is annotated by the **grammar v8 pipeline only**. It classifies:
- **grammar** via `annotation_jsonb.grammar_role_key` (non-null on 27 Qs)
- **reading** via `annotation_jsonb.skill_family_key` *(singular!)* (non-null on 13 Qs)
- **`reading_skill_family_key` / `reading_focus_key` are NULL on all 60** — the existing
  `/questions` reading filter and `diagnostic_submit` domain-derivation that key off them **return
  nothing for reading**. Do NOT use them. Classify domain as: reading if `skill_family_key` set,
  else grammar if `grammar_role_key` set. Every question also has `stem_type_key`.

### Bank reality (build blueprint from `DIAGNOSTIC_TEST_PLAN.md` §7b TRUE coverage map)
60 active, all `content_origin=official` (generated bank empty). Usable classified = 27 grammar +
13 reading. Missing grammar roles: parallel_structure, pronoun. Missing reading families:
command_of_evidence_quantitative, cross_text_connections. v1 blueprint ≈ **16 Q** (10 grammar +
6 reading), single-attempt.

---

## 2. Reference: existing schemas & endpoints (read-only context)

### DiagnosticSession ORM (`db.py:527`)
Columns: `id(UUID)`, `user_id(int FK)`, `started_at`, `completed_at`, `created_at`,
`total_questions(int=0)`, `correct_count(int=0)`, `accuracy(float?)`,
`question_ids(JSONB list[str])`, `diagnostic_type(str20?)`, `focus_areas(JSONB?)`,
`is_archived(bool)`. Relationship: `progress_records` → `UserProgress`.

### UserProgress miss fields (`db.py:500`)
`is_correct`, `selected_option_label`, `diagnostic_session_id`, `missed_grammar_focus_key`,
`missed_syntactic_trap_key`, `missed_reading_focus_key`, `missed_reading_skill_family_key`,
`question_domain`, `question_difficulty`.

### Existing diagnostic endpoints (`student.py`)
- `POST /diagnostic/start` (1578) → `DiagnosticSessionStartResponse{session_id, max_questions=8, estimated_duration_minutes=12}`
- `POST /diagnostic/{id}/submit` (1599) → computes `is_correct` server-side, writes `UserProgress`,
  appends to `question_ids`, bumps `correct_count`. Returns `DiagnosticAnswerResponse{is_correct,
  progress_id, question_number, total_questions=8 (HARDCODED), correct_so_far}`.
- `POST /diagnostic/{id}/complete` (1684) → sets `completed_at`, `accuracy`; returns
  `DiagnosticSessionResult{session_id,total_questions,correct_count,accuracy,duration_seconds,
  weakest_focus_areas:[{focus_key,miss_count}]}`.
- `GET /diagnostic/history` (1746), `GET /diagnostic/{id}` (1810).

### Selection primitive (`student.py:242`) — REUSE THIS
`_build_question_filter_stmt(*, domain, difficulty, grammar_role_key, grammar_focus_key,
reading_skill_family_key, reading_focus_key, stimulus_mode_key, origin, ...) -> Select`.
Filters on `Question.practice_status=="active"`, excludes dry-run, and joins `QuestionAnnotation`
on `Question.latest_annotation_id` filtering `annotation_jsonb[...]` fields.

### Student question payload (`payload.py:8`, `StudentQuestionResponse`)
Includes `current_correct_option_label` — **LEAKS THE KEY (bug-760)**. The diagnostic must use a
stripped payload (TASK-B03).

### Taxonomy (`ontology.py`)
- `GRAMMAR_ROLE_KEYS` (8): sentence_boundary, agreement, verb_form, modifier, punctuation,
  parallel_structure, pronoun, expression_of_ideas
- `GRAMMAR_FOCUS_BY_ROLE` (dict role→focuses, ~50 total)
- `READING_SKILL_FAMILY_KEYS` (7): command_of_evidence_textual, command_of_evidence_quantitative,
  central_ideas_and_details, inferences, words_in_context, text_structure_and_purpose,
  cross_text_connections
- `READING_FOCUS_BY_SKILL_FAMILY` (dict, ~40 total)
- `QUESTION_FAMILY_KEYS` (4): conventions_grammar, expression_of_ideas, craft_and_structure,
  information_and_ideas
- `SYNTACTIC_TRAP_KEYS` (13), `REASONING_TRAP_KEYS` (~48), `DISTRACTOR_TYPE_KEYS` (~45)

### Frontend API client (`src/api/client.ts:47`)
`api.getQuestions(params)`→`/questions?<qs>`; `api.diagnosticStart`, `diagnosticSubmit(sessionId,
data)`, `diagnosticComplete(sessionId,{user_token})`, `diagnosticHistory`, `diagnosticDetail`.
`USER_TOKEN = import.meta.env.VITE_TEST_USER_TOKEN`.

---

## PHASE P0 — Validate bank & resolve unknowns  *(gates everything)*

### TASK-B00 — Bank coverage report + difficulty-key resolution  ✅ DONE (2026-06-23)
Findings recorded in §1 (Difficulty/Domain/Bank reality) and `DIAGNOSTIC_TEST_PLAN.md` §7b.
Outcome: official-bank v1, low→medium, ~16 Q, reading via `skill_family_key`, no `high`.
The committed coverage script (below) is still worth landing for repeatability but is **optional**;
the numbers it would print are already captured. Original spec retained for reference:

**Depends:** none. **Files:** new `backend/scripts/diagnostic_coverage.py`. **Needs:** dev stack up.

**Spec:** Write a script that connects via the app's async DB session (mirror an existing script in
`backend/scripts/`) and prints:
1. Count of active, non-dry-run questions grouped by `(domain, difficulty_overall)` where domain is
   derived as in `diagnostic_submit` (reading if reading_* keys present, else grammar if grammar_*).
2. Count grouped by `(question_family_key, difficulty_overall)`.
3. Count grouped by `(grammar_role_key)` and by `(reading_skill_family_key)`.
4. The **distinct set of `difficulty_overall` values actually present** (answers: low/medium/high vs
   easy/medium/hard).
5. For the 27 blueprint cells (see TASK-B01 blueprint), print each cell's available unseen-agnostic
   count and flag cells with `< 3` questions as **THIN** and `0` as **EMPTY**.

**Acceptance / Done-when:**
- [ ] Running the script prints all five sections without error.
- [ ] The actual `difficulty_overall` vocabulary is recorded at the **top of this file under
      §1 "Difficulty values"** (edit it) and in `.wolf/cerebrum.md` Key Learnings.
- [ ] Any EMPTY/THIN cells are listed in `DIAGNOSTIC_TEST_PLAN.md` §7 and the blueprint focuses in
      TASK-B01 are adjusted (or generation queued) to avoid EMPTY cells.

**Verify:** `cd backend && export UV_PROJECT_ENVIRONMENT=$PWD/.venv-jb && .venv-jb/bin/python scripts/diagnostic_coverage.py`
**Commit:** `chore(diagnostic): add bank coverage report script`

---

## PHASE P1 — Key-fix, blueprint + selector

### TASK-B0A — Fix domain/reading classification to match the v8 bank  ✅ DONE (2026-06-23)
Implemented `app/diagnostic/queries.py` (`derive_domain`, `build_pool_stmt`); switched both
`/submit` and `diagnostic_submit` domain logic to `derive_domain`. 10 DB-free tests pass
(`tests/test_diagnostic_api.py`); existing diagnostic+contract suites still green (55). Live-verified:
`skill_family_key='inferences'` → 5 active questions; legacy `reading_skill_family_key` → 0.
Commit `fix(diagnostic): classify reading via skill_family_key (bug-761)`.

**Depends:** none. **Files:** new `backend/app/diagnostic/queries.py`,
`backend/app/routers/student.py` (`diagnostic_submit` domain logic),
`backend/tests/test_diagnostic_api.py` (new). **Root cause:** bug-761.

**Spec:** Build the classification/query layer the diagnostic uses (the legacy reading path is broken):
1. `derive_domain(ann: dict) -> str|None`: `"reading"` if `ann.get("skill_family_key")`, else
   `"grammar"` if `ann.get("grammar_role_key")`, else `None`. Mirror into `diagnostic_submit` so
   reading misses are tagged with the right `question_domain`.
2. `build_pool_stmt(*, domain, difficulty=None, grammar_role_key=None, skill_family_key=None,
   stem_type_key=None, exclude_question_ids=(), exclude_seen_user_id=None) -> Select(Question)`:
   joins `QuestionAnnotation` on `latest_annotation_id`; filters the **real** keys —
   grammar→`annotation_jsonb['grammar_role_key']`, reading→`annotation_jsonb['skill_family_key']`
   *(singular)*, difficulty→`annotation_jsonb['difficulty_overall']` (skip if None); reuse the
   active + non-dry-run guards from `_build_question_filter_stmt` (`student.py:262-273`);
   `exclude_seen_user_id` excludes questions with a prior `UserProgress` row for that user.
3. Leave `_build_question_filter_stmt` untouched for other callers.

**Acceptance / Done-when:**
- [ ] `derive_domain` unit test (no DB): reading for skill_family_key-only, grammar for
      grammar_role_key-only, None for neither.
- [ ] Live/faked test: `build_pool_stmt(domain='reading', skill_family_key='inferences')` matches the
      5 inference questions.
- [ ] `diagnostic_submit` tags reading misses correctly.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_api.py -v`
**Commit:** `fix(diagnostic): classify reading via skill_family_key (bug-761)`

### TASK-B01 — Blueprint module (official-bank v1, 16 slots, low→medium)
**Depends:** TASK-B00 (done). **Files:** new
`backend/app/diagnostic/__init__.py`, `backend/app/diagnostic/blueprint.py`,
new `backend/tests/test_diagnostic_blueprint.py`.

**Spec:** Define, with **no DB imports** (pure):
```python
from dataclasses import dataclass

DIFFICULTY_TIERS = ("low", "medium")   # bank has NO 'high' (TASK-B00); null→treat as medium

@dataclass(frozen=True)
class Slot:
    seq: int                 # 1..16
    difficulty: str          # "low" | "medium"
    domain: str              # "grammar" | "reading"
    role_or_skill: str       # grammar_role_key (grammar) OR skill_family_key (reading)  ← singular
    focus: str | None = None # optional & soft
    trap_preference: str | None = None  # optional & soft

BLUEPRINT_V1: tuple[Slot, ...] = ( ... )   # exactly 16 slots
```
Compose `BLUEPRINT_V1` from the **TRUE coverage map** (`DIAGNOSTIC_TEST_PLAN.md` §7b), ~10 grammar
+ ~6 reading:
- Grammar roles (all 6 present): expression_of_ideas (deepest cell, ×3), punctuation (×2),
  agreement, modifier, sentence_boundary, verb_form. **Do NOT** use parallel_structure or pronoun (0 in bank).
- Reading families (all 5 present, as `skill_family_key` values): inferences (×2),
  text_structure_and_purpose (×2), central_ideas_and_details, command_of_evidence_textual,
  words_in_context. **Do NOT** use command_of_evidence_quantitative or cross_text_connections (0 in bank).
- Ramp: seq 1–6 `low`, 7–16 `medium`; rotate domain so no 3 consecutive slots share a domain.
- Reading `role_or_skill` is a `skill_family_key` value; validate against `READING_SKILL_FAMILY_KEYS`
  (same vocabulary, different annotation field) and grammar against `GRAMMAR_ROLE_KEYS`.

Provide helpers: `tier_for_seq(seq:int)->str`, `validate_blueprint(bp)->None` (raises `ValueError`
on: wrong length, seq not 1..N contiguous, unknown taxonomy key, ramp violation [`low` after
`medium`], excluded zero-bank role/family, 3-in-a-row same domain), and `blueprint_coverage(bp)->dict`.

**Acceptance / Done-when:**
- [ ] `len(BLUEPRINT_V1) == 16`; `validate_blueprint(BLUEPRINT_V1)` passes.
- [ ] All 6 present grammar roles + all 5 present reading families appear ≥1 time.
- [ ] Difficulty ∈ {low, medium}; low=6, medium=10 (tune ±, keep ramp).
- [ ] No excluded (zero-bank) role/family referenced.
- [ ] Tests: valid passes; each bad-blueprint failure mode raises.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_blueprint.py -v`
**Commit:** `feat(diagnostic): add official-bank v1 blueprint (16 slots, low→medium)`

### TASK-B02 — Selector with fallback ladder
**Depends:** B0A, B01. **Files:** new `backend/app/diagnostic/selector.py`,
new `backend/tests/test_diagnostic_selector.py`.

**Spec:**
```python
async def assemble_diagnostic(
    db: AsyncSession, *, user_id: int, blueprint=BLUEPRINT_V1, exclude_seen: bool = True,
) -> "AssembledDiagnostic"
```
For each `Slot`, select **one** unseen, active, non-dry-run `Question` using **`build_pool_stmt`
from TASK-B0A** (NOT the legacy reading filter). Apply the **fallback ladder**, first hit wins,
never reusing a question already chosen in this assembly (pass chosen ids via `exclude_question_ids`):
1. difficulty + domain + role/skill (+ focus, + trap_preference)
2. drop trap_preference
3. drop focus
4. drop difficulty (pool is tiny; include `null`-difficulty questions)
5. any unseen active question in the domain
6. (only if domain exhausted) any unseen active question — record `gap=True`

Because the bank is thin (~27 grammar / 13 reading usable), expect frequent level-3/4 fallback;
acceptable for v1 — surface counts in `coverage_report`.
`exclude_seen` excludes questions with a prior `UserProgress` row for `user_id`
(via `build_pool_stmt(exclude_seen_user_id=...)`). Return:
```python
@dataclass
class ChosenQuestion: slot: Slot; question_id: str; fallback_level: int; gap: bool
@dataclass
class AssembledDiagnostic: questions: list[ChosenQuestion]; coverage_report: dict
```
`coverage_report` summarizes fallback_level distribution + any gaps.

**Acceptance / Done-when:**
- [ ] Returns exactly `len(blueprint)` distinct question_ids when the (faked) bank is rich.
- [ ] With a faked thin bank, falls back per ladder and never returns duplicates.
- [ ] Excludes seen questions when `exclude_seen=True`.
- [ ] Unit tests use a fake/stub async session (no live DB) — mirror patterns in
      `backend/tests/test_student_api_contracts.py` (`_QueueDB`).

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_selector.py -v`
**Commit:** `feat(diagnostic): add blueprint selector with graceful fallback ladder`

---

## PHASE P2 — Endpoints & scoring

### TASK-B03 — Stripped diagnostic question payload (no answer key)
**Depends:** none (can parallel P1). **Files:** `backend/app/models/payload.py`,
`backend/tests/test_student_api_contracts.py`.

**Spec:** Add `DiagnosticQuestionPayload(BaseModel)` — same student-visible fields as
`StudentQuestionResponse` **except it has NO `current_correct_option_label`** and options carry no
`is_correct`/answer hints. Include: `id, current_question_text, current_passage_text,
passage_spans, options[{label,text,distractor_type_key?}], domain, grammar_role_key,
grammar_focus_key, reading_skill_family_key, reading_focus_key, difficulty_overall,
question_family_key, stimulus_mode_key, seq` (presentation order). Also add response model
`DiagnosticStartV1Response{session_id, total_questions, time_limit_seconds, questions:
list[DiagnosticQuestionPayload], coverage_report: dict}`.

**Acceptance / Done-when:**
- [ ] New contract test asserts a serialized `DiagnosticQuestionPayload` has **no**
      `current_correct_option_label` key and options expose no correctness flag.
- [ ] `npx tsc`-equivalent (pydantic import) — module imports cleanly.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_student_api_contracts.py -v`
**Commit:** `feat(diagnostic): add answer-key-free diagnostic question payload`

### TASK-B04 — `POST /diagnostic/start` blueprint mode
**Depends:** B0A, B01, B02, B03. **Files:** `backend/app/routers/student.py`,
`backend/tests/test_diagnostic_api.py` (new).

**Spec:** Extend `diagnostic_start`: when `body.diagnostic_type == "blueprint_v1"`, call
`assemble_diagnostic(db, user_id=user.id)`, persist `session.question_ids` (ordered),
`session.total_questions = len(...)`, `session.diagnostic_type="blueprint_v1"`,
`session.started_at = now`, then return `DiagnosticStartV1Response` (questions in slot order,
**no answer key**, `time_limit_seconds=DIAGNOSTIC_TIME_LIMIT_SECONDS` — a module constant set to
**1140** (≈19 min, 16 Q × ~70s)). Keep legacy behavior for other `diagnostic_type` values OR, since
we're replacing the adaptive flow, make `"blueprint_v1"` the default and leave the old branch only
for back-compat history. Build each payload by reusing the annotation-fetch logic already in
`student_recall` (extract a helper `_build_diagnostic_payload(q, ann_data, ann, seq)` to avoid dup).

**Acceptance / Done-when:**
- [ ] Start returns 16 questions in slot order, none containing the correct label.
- [ ] `DiagnosticSession.question_ids` persisted in order; `total_questions==16`; `started_at` set.
- [ ] Test (faked DB or live) asserts response shape + count + no-key.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_api.py -v`
**Commit:** `feat(diagnostic): blueprint_v1 start endpoint returns full ordered module`

### TASK-B05 — Dynamic counts in submit + per-area breakdown in complete
**Depends:** B04. **Files:** `backend/app/routers/student.py`, `backend/app/models/payload.py`,
`backend/tests/test_diagnostic_api.py`.

**Spec:**
1. `diagnostic_submit`: replace hardcoded `total_questions=8` with
   `session.total_questions or len(session.question_ids)`. (For blueprint mode the set is
   pre-persisted at start, so submit should **not** append duplicates — guard: only append to
   `question_ids` if the qid isn't already in the pre-seeded list; always still write `UserProgress`
   and bump `correct_count`.)
2. Extend `DiagnosticSessionResult` with `breakdown: DiagnosticBreakdown` where:
```python
class DiagnosticBreakdown(BaseModel):
    by_family: dict[str, CorrectTotal]      # question_family_key -> {correct,total}
    by_difficulty: dict[str, CorrectTotal]  # low/medium/high -> {correct,total}
    by_trap: dict[str, CorrectTotal]        # syntactic/reasoning trap -> {correct,total}
    weakest_areas: list[{area_key, domain, correct, total, accuracy}]  # sorted worst-first, top 5
```
   Compute from the session's `UserProgress` rows joined to each question's annotation.
3. Fix `DiagnosticSessionStartResponse.max_questions` default usage (no longer 8 for blueprint).

**Acceptance / Done-when:**
- [ ] Submit response `total_questions` reflects 16, not 8.
- [ ] Complete returns a populated `breakdown`; `by_difficulty` keys equal the tier set; numbers
      reconcile (`sum(by_family.total) == total answered`).
- [ ] No duplicate `question_ids` after answering all 16.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_api.py -v`
**Commit:** `feat(diagnostic): dynamic counts + per-area weakness breakdown on complete`

### TASK-B06 — Profile seeding sanity test
**Depends:** B05. **Files:** `backend/tests/test_diagnostic_api.py`.

**Spec:** Add a test proving that after a blueprint diagnostic with deliberate misses, the misses
are written to `UserProgress` with the right `missed_*`/`question_domain`/`question_difficulty`, so
the existing `top_targets`/recommendations path surfaces them. No new production code expected
(the submit path already writes misses) — if a gap is found, fix it minimally and note in buglog.

**Acceptance / Done-when:**
- [ ] Test asserts ≥1 `UserProgress` row per wrong answer with populated miss keys.
**Verify:** same as B05. **Commit:** `test(diagnostic): assert diagnostic seeds weakness profile`

### TASK-B07 — ~~Weakness profile = diagnostics only~~  ❌ DROPPED (reverted 2026-06-23)
Decision reverted: the weakness profile **includes practice** (pooled diagnostic + practice), which
is the existing `_compute_weakness_targets` behavior. **No code change** — this task is cancelled.
See §7c Stream 1.

### TASK-B08 — Practice-only improvement endpoint  *(§7c Stream 2 — additive, optional)*
**Depends:** none. **Files:** `backend/app/routers/student.py` (new endpoint),
`backend/app/models/payload.py` (response model), `backend/tests/test_diagnostic_api.py`.

**Spec:** Add `GET /study/practice-progress?user_token=...` (or POST with body, matching the
existing study endpoints' auth pattern). Query `UserProgress` WHERE
`diagnostic_session_id IS NULL` for the user; return a historical practice-improvement series:
overall accuracy bucketed by day/week, plus per-domain (grammar/reading via `question_domain`) and
optionally per-focus accuracy trend. Response model `PracticeProgressResponse{ buckets:
[{period, attempts, correct, accuracy}], by_domain: {...}, total_attempts }`. **No diagnostic data
mixed in.** This is the data source for the practice-track UI (a later frontend task, e.g. on
`ProgressPage`).

**Acceptance / Done-when:**
- [ ] Endpoint returns practice-only rows; a diagnostic-only user gets empty/zeroed series.
- [ ] Accuracy math reconciles (sum(correct)/sum(attempts) per bucket).
- [ ] Auth boundary tested (403 missing key / 404 bad token), mirroring existing study endpoints.

**Verify:** `.venv-jb/bin/python -m pytest tests/test_diagnostic_api.py -v`
**Commit:** `feat(diagnostic): practice-only improvement endpoint (§7c)`

> **Frontend follow-up (P4-adjacent):** add a practice-improvement view on `ProgressPage` consuming
> `/study/practice-progress`, kept visually distinct from the diagnostic report/trend. Tracked as a
> sub-item of TASK-F04/F05 scope; spec it when those land.

---

## PHASE P3 — Frontend test runner

### TASK-F01 — API client + types for blueprint diagnostic
**Depends:** B03/B04 (shape only — can stub). **Files:** `src/api/client.ts`, `src/types.ts`.

**Spec:** Add types `DiagnosticQuestion` (mirror `DiagnosticQuestionPayload`, **no correct label**),
`DiagnosticStartV1Response`, `DiagnosticBreakdown`, `DiagnosticResult`. Add
`api.diagnosticStartV1(user_token)` → POST `/diagnostic/start` with
`{user_token, diagnostic_type:'blueprint_v1'}`. Extend `diagnosticComplete` result typing to include
`breakdown`.

**Acceptance / Done-when:** `npx tsc --noEmit` clean. **Commit:** `feat(diagnostic): client+types for blueprint_v1`

### TASK-F02 — `DiagnosticTestRunner` component (timer + navigation, hidden answers)
**Depends:** F01. **Files:** new `src/components/diagnostic/DiagnosticTestRunner.tsx`,
new `src/hooks/useDiagnosticTimer.ts`, test
`src/components/__tests__/DiagnosticTestRunner.test.tsx`.

**Spec:** Props `{ sessionId, questions: DiagnosticQuestion[], timeLimitSeconds, onComplete }`.
- **Timer:** `useDiagnosticTimer(timeLimitSeconds)` counts down (MM:SS), pinned in header; at 0 it
  **auto-calls `onComplete`**. Pause not allowed.
- **One question at a time** with **Next/Back**; a **question palette** (grid of seq numbers) shows
  answered / flagged / current / unanswered states and jumps on click.
- **Mark for review** toggle per question.
- **Selecting an option** records the choice locally **and** fires `api.diagnosticSubmit(sessionId,
  {...})` silently (do NOT use the response to reveal correctness; ignore `is_correct` in UI).
  Allow changing the answer before final submit (re-submit overwrites — backend writes a new
  `UserProgress`; acceptable for v1, note it).
- **Submit** button → confirm dialog → `onComplete`. Show count of unanswered before confirming.
- **No correctness styling anywhere during the test** (no green/red).

**Acceptance / Done-when:**
- [ ] Timer renders and decrements; reaching 0 triggers `onComplete` (test with fake timers).
- [ ] Palette reflects answered/flagged state; Back/Next bound at edges.
- [ ] No element exposes correctness during the test (assert no `is_correct`-driven class).
- [ ] `waitFor(..., {timeout:5000})` used; tests pass on node 20.

**Verify:** `nvm use 20.20.2 && npx vitest run src/components/__tests__/DiagnosticTestRunner.test.tsx`
**Commit:** `feat(diagnostic): test-mode runner with timer, palette, hidden answers`

### TASK-F03 — Pre-test screen + wire into `DiagnosticPage`, replace adaptive runner
**Depends:** F02. **Files:** `src/pages/DiagnosticPage.tsx`, `src/components/dashboard/DiagnosticTab.tsx`
(**remove the adaptive runner**), `src/components/diagnostic/DiagnosticIntro.tsx` (new).

**Spec:** `DiagnosticIntro` explains format ("16 questions · ~19 minutes · answers shown at the
end") and a Start button that calls `api.diagnosticStartV1`, then renders `DiagnosticTestRunner`
with the returned questions. **Works with no prior profile** (no `top_targets` dependency). Delete
the old `DiagnosticRunner`/`DiagnosticQuestionCard` reveal-mode code and any now-dead imports.

**Acceptance / Done-when:**
- [ ] `/diagnostic` route renders intro → runner → calls complete.
- [ ] Old adaptive reveal-mode code is gone; `npx tsc --noEmit` clean; existing
      `DiagnosticCard.test.tsx`/`DashboardPage.test.tsx` updated or still pass.
**Verify:** `npx vitest run src/components/__tests__` + `npx tsc --noEmit`
**Commit:** `feat(diagnostic): replace adaptive diagnostic with blueprint test flow`

---

## PHASE P4 — Report / review

### TASK-F04 — `DiagnosticReport` (breakdown viz + review + practice CTAs)
**Depends:** F03, B05. **Files:** new `src/components/diagnostic/DiagnosticReport.tsx`,
test `src/components/__tests__/DiagnosticReport.test.tsx`.

**Spec:** Renders the `complete` result:
- Headline: score %, `correct/total`, time used.
- **Breakdown bars**: by family, by difficulty tier, by trap type (use `breakdown` from B05).
- **Top 3–5 weakest areas** with a "Practice this" button → navigate to
  `/practice/grammar` or `/practice/concepts` pre-filtered to that focus (use existing route params).
- **Question-by-question review**: now the answer key IS shown — fetch full detail via
  `api.diagnosticDetail(sessionId, userToken)` (admin-grade detail incl. correct option +
  explanation + the trap on the chosen distractor). Mark each Q correct/incorrect here (allowed —
  test is over).

**Acceptance / Done-when:**
- [ ] Renders bars + weakest list from a mocked result; CTAs navigate with correct params.
- [ ] Review list shows correct vs chosen + explanation.
**Verify:** `npx vitest run src/components/__tests__/DiagnosticReport.test.tsx`
**Commit:** `feat(diagnostic): results report with weakness breakdown and review`

### TASK-F05 — Point history/detail pages at the new report
**Depends:** F04. **Files:** `src/pages/DiagnosticDetailPage.tsx`, `src/pages/DiagnosticHistoryPage.tsx`.

**Spec:** `DiagnosticDetailPage` reuses `DiagnosticReport` (or a read-only variant) for past
sessions. History list shows score + date + a trend sparkline (data already in
`DiagnosticHistoryResponse.improvement_trend`).
**Acceptance / Done-when:** [ ] Both pages render via the shared report; tsc clean.
**Commit:** `feat(diagnostic): history+detail reuse report component`

---

## PHASE P5 — Integration, polish, cleanup

### TASK-Q01 — End-to-end happy path + timeout path
**Depends:** all. **Needs:** dev stack. **Files:** `backend/tests/test_diagnostic_e2e.py` and/or
a `/browse` or Playwright script.

**Spec:** Drive start → answer a known mix (some wrong) → complete; assert score, breakdown, and
that misses seeded the profile. Separately assert the **timer auto-submit** path completes a session
with partial answers. Use the `/browse` skill for the UI flow if doing it in-browser.
**Done-when:** [ ] Both paths green; screenshots/log attached if UI. **Commit:** `test(diagnostic): e2e happy + timeout`

### TASK-Q02 — Cleanup & docs
**Depends:** Q01. **Files:** dead code removal, `CHANGELOG.md`, `.wolf/cerebrum.md`,
`DIAGNOSTIC_TEST_PLAN.md` (mark phases done), `.wolf/anatomy.md` (new files).

**Spec:** Remove any leftover adaptive-diagnostic code/types; add a CHANGELOG entry; record the
difficulty-vocab learning and the answer-key-leak fix (bug-760) in cerebrum; update anatomy for all
new files. **Done-when:** [ ] No dead refs; docs updated. **Commit:** `chore(diagnostic): cleanup + docs after blueprint diagnostic ship`

---

## 3. Dependency graph (quick view)

```
B00(✅) ─► B01 ─► B02 ─┐
B0A ──────────► B02 ───┼─► B04 ─► B05 ─► B06
B03 ───────────────────┘                 │
                                          ▼
F01 ─► F02 ─► F03 ─► F04 ─► F05 ─► Q01 ─► Q02
                      ▲
                   (needs B05)
```
B0A, B03, and F01/F02 can start in parallel with B01 using the agreed payload shape as a contract.

## 4. Global definition of done
- [ ] All listed tests green (backend via `.venv-jb`, frontend via node 20).
- [ ] No answer key reaches the client during a test (bug-760 contract test passes).
- [ ] Reading classified via `skill_family_key`, not `reading_skill_family_key` (bug-761).
- [ ] Blueprint covers all **6 present** grammar roles + **5 present** reading families; low→medium
      ramp intact. (parallel_structure, pronoun, quantitative-evidence, cross-text are documented v1 gaps.)
- [ ] New student with empty profile can complete a full diagnostic and gets a weakness report.
- [ ] Adaptive reveal-mode diagnostic code removed.
