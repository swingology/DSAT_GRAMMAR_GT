# Diagnostic Test Redesign — Plan

**Status:** Draft for review
**Date:** 2026-06-22
**Author:** CB-17

## 1. Goal

Replace the current adaptive 8-question diagnostic with a **full-coverage, test-condition
diagnostic** that mimics a real SAT Reading & Writing module and produces a reliable
first-pass weakness profile for a brand-new student.

The diagnostic must:

1. Run under **test conditions** — countdown timer, answers hidden until the end, review screen
   after submit (not the current reveal-after-each-question practice mode).
2. **Ramp difficulty** easy → medium → hard across the test.
3. **Cover the breadth** of the verbal section — every grammar role and reading skill family is
   sampled at least once, so weaknesses surface no matter where they hide.
4. Deliberately vary **distractor types and traps** so the report can say *which kind of trap*
   a student falls for, not just *which topic*.
5. Be **well-ordered and deterministic in structure** (fixed blueprint) so results are
   comparable across students and across retakes.

### Decisions (locked 2026-06-22)
- **Replaces** the existing adaptive `DiagnosticTab` flow entirely.
- **Question source:** the generated/annotated question bank (rich trap + difficulty + focus
  labels; infinite fresh questions; every student gets a different test).
- **Format:** fixed blueprint with an easy→hard ramp (not CAT, not two-module routing — those
  remain possible future work via the existing `TestSessionResults` table).

## 2. What exists today (and what changes)

| Piece | Today | After |
|---|---|---|
| `DiagnosticTab.tsx` | Adaptive: 8 Q from `top_targets`, reveal-each-answer, no timer, needs prior profile | **Replaced** by a blueprint test runner |
| `DiagnosticSession` table + start/submit/complete/history endpoints | ✅ Phase 1 complete | Reused; `diagnostic_type` becomes `"blueprint_v1"` |
| `/questions` endpoint | Filters by domain/difficulty/role/focus/skill_family + exclude_seen | Reused as the selection primitive |
| `UserProgress` miss tracking (`missed_*`, `question_domain`, `question_difficulty`) | Written per submit | Reused — diagnostic still feeds the same recommendations machinery |
| Weakness profile / recommendations (`top_targets`) | Built from `UserProgress` | Now seeded by the diagnostic on completion |

The selection query path already supports everything the blueprint needs
(`_build_question_filter_stmt` in `student.py:242`), so most backend work is *orchestration*,
not new query plumbing.

## 3. The blueprint

A single ~27-question module (≈32 min), the natural "real test" unit. Expressed as a declarative
list of **slots**, each a filter spec the selector fills from the bank. The blueprint lives in a
new module `backend/app/diagnostic/blueprint.py` so it can be versioned and unit-tested without DB.

### 3.1 Coverage targets (27 slots)

Mirrors real SAT R&W domain weighting while guaranteeing breadth:

| Question family | Slots | Skill areas covered (≥1 each) |
|---|---|---|
| Standard English Conventions (grammar) | 8 | sentence_boundary, agreement, verb_form, modifier, punctuation, parallel_structure, pronoun (+1 floater) |
| Expression of Ideas (grammar) | 5 | transition_logic, redundancy_concision, precision_word_choice, rhetorical synthesis, logical_relationships |
| Information & Ideas (reading) | 8 | central_ideas_and_details, command_of_evidence_textual, command_of_evidence_quantitative, inferences |
| Craft & Structure (reading) | 6 | words_in_context, text_structure_and_purpose, cross_text_connections |

### 3.2 Difficulty ramp

Slots are ordered into three tiers; family rotates within each tier so the test doesn't run
"all grammar then all reading":

- **Slots 1–7 — easy** (`low`): one from each major area, builds confidence, confirms the floor.
- **Slots 8–19 — medium** (`medium`): the diagnostic core; widest taxonomy spread.
- **Slots 20–27 — hard** (`high`): stress tier; concentrates the hardest traps to separate
  strong from average students.

### 3.3 Trap variety

Medium and hard slots carry an optional `trap_preference` (e.g. `nearest_noun_attraction`,
`modifier_attachment_ambiguity`, `inverted_logic`, `scope_extension`). The selector treats it as
a **soft** filter — preferred but not required — so a thin bank cell never blocks the test.

### 3.4 Slot schema

```python
@dataclass(frozen=True)
class Slot:
    seq: int                       # 1..27, presentation order
    difficulty: str                # "low" | "medium" | "high"
    domain: str                    # "grammar" | "reading"
    family: str                    # question_family_key
    role_or_skill: str             # grammar_role_key | reading_skill_family_key
    focus: str | None = None       # optional narrower target
    trap_preference: str | None = None   # soft preference
```

### 3.5 Selection algorithm (fill with graceful fallback)

For each slot, fetch one unseen question via the existing filter path, **widening on miss**:

1. Exact: difficulty + domain + role/skill + focus + trap_preference, `exclude_seen=true`.
2. Drop `trap_preference`.
3. Drop `focus` (keep role/skill).
4. Relax difficulty by ±1 tier.
5. Last resort: any unseen question in the domain (and log the gap).

Selection runs server-side in one new endpoint that returns all 27 questions up front (a real
test shows the whole module), recording the chosen `question_ids` on the `DiagnosticSession`.

### 3.6 Findings from code review (must-fix, fold into tasks)

- **Answer-key leak (bug-760):** the student `GET /questions` path (`student_recall`, `student.py:~487`)
  sets `current_correct_option_label=q.current_correct_option_label`. A hidden-answer test must
  **never** receive the key. The diagnostic will use a dedicated stripped payload + a contract test.
- **Hardcoded `8`:** `diagnostic_submit` returns `total_questions=8` and
  `DiagnosticSessionStartResponse.max_questions=8` are hardcoded. The blueprint length (27) must
  flow through dynamically.
- **`exclude_seen`/inventory:** `/questions` returns `StudentQuestionsListResponse{items, inventory}`
  (note: `items`, not `questions`). The selector calls the underlying filter helper directly rather
  than the HTTP route, so it controls exclude-seen and ordering itself.

## 4. Backend work

1. **`backend/app/diagnostic/blueprint.py`** — the `Slot` dataclass + `BLUEPRINT_V1` list +
   pure helpers (`tier_for_seq`, `validate_blueprint`). No DB; fully unit-testable.
2. **`backend/app/diagnostic/selector.py`** — `async def assemble_diagnostic(db, user, blueprint)`:
   runs the fallback algorithm, dedupes, returns ordered questions + a coverage report
   (which slots hit exact vs. fell back). Reuses `_build_question_filter_stmt`.
3. **New endpoint** `POST /diagnostic/start` (extend existing): when
   `diagnostic_type == "blueprint_v1"`, call the selector, persist `question_ids`, and return the
   full ordered question payload (answers/correctness **excluded** — verify against the existing
   student contract tests that no answer key leaks).
4. **Scoring on complete** — `diagnostic_complete` already aggregates `UserProgress`; extend the
   `DiagnosticSessionResult` to also return a **per-area breakdown** (correct/total by family,
   by difficulty tier, by trap type) so the report can be rendered without a second call.
5. **Profile seeding** — confirm completion writes the misses that `top_targets`/recommendations
   read, so the *next* practice session is already personalized.
6. **Difficulty-key validation** (see §7) — confirm the generated bank stores
   `difficulty_overall ∈ {low, medium, high}` (ontology) vs `{easy, medium, hard}` (admin UI).
   Normalize in the selector if they diverge.

## 5. Frontend work

Replace `DiagnosticTab.tsx`'s runner with a **test-mode experience**:

1. **Pre-test screen** — explains format ("27 questions, ~32 minutes, answers shown at the end"),
   Start button. No dependency on an existing weakness profile (works for new students).
2. **Test runner** (`DiagnosticTestRunner.tsx`):
   - **Countdown timer** (config, default 32:00) pinned to the header; auto-submits at 0.
   - One question at a time, **Next/Back navigation**, a question palette (answered/flagged/current).
   - **Mark for review** flag.
   - **No correctness reveal** — selecting an option just records it locally; submission happens
     per-question to `/diagnostic/{id}/submit` silently (server computes `is_correct` but the UI
     never shows it during the test).
   - Progress + difficulty-tier indicator (subtle).
3. **Submit confirmation** → calls `/diagnostic/{id}/complete`.
4. **Results / review screen** (`DiagnosticReport.tsx`):
   - Headline score + time used.
   - **Per-area breakdown** bars (by family, by difficulty tier, by trap type) — *this is the
     "points out weaknesses" payload*.
   - Top 3–5 weakest areas with a "Practice this" CTA into the existing grammar/concept practice.
   - Full question-by-question review (your answer vs. correct, explanation, the trap you fell for).
5. Keep the existing `/diagnostic/history` and `/diagnostic/:sessionId` detail pages; point them at
   the new report component.

## 6. Phasing & estimates

| Phase | Scope | Est. |
|---|---|---|
| **P0 — Validate bank** | Coverage script: count generated questions per (domain, family, difficulty, focus). Confirm the blueprint is fillable; tune slot focuses to bank reality. Resolve the difficulty-key question. | 0.5 day |
| **P1 — Blueprint + selector** | `blueprint.py`, `selector.py`, unit tests (blueprint validity, fallback ladder with a fake DB). | 1.5 days |
| **P2 — Endpoints** | Extend start/complete, per-area breakdown in results, contract tests (no answer-key leak, breakdown correctness). | 1.5 days |
| **P3 — Frontend runner** | Timer, navigation, palette, flag, silent submit. | 2 days |
| **P4 — Report** | Breakdown viz + review screen + practice CTAs. | 1.5 days |
| **P5 — Polish & test** | E2E (start→answer→time-out→complete→report), retake comparability, remove dead adaptive code. | 1 day |

**~8 days.** P0 gates everything (bank may force blueprint tuning).

## 7. Open questions / risks

1. **Difficulty key mismatch** — ontology says `low/medium/high`; admin UI offers `easy/medium/hard`.
   Must confirm what the generated bank actually stores before the ramp can filter. (P0)
2. **Bank thinness** — some taxonomy cells (e.g. `command_of_evidence_quantitative` at `high`) may
   have few questions. The fallback ladder protects test assembly, but heavy fallback weakens
   coverage claims. P0 quantifies this; if a cell is empty, either soften that slot or queue
   generation for it.
3. **Reading passages** — reading questions need stimulus passages; confirm the payload already
   ships `stimulus`/passage data to the student runner (it does for grammar; verify reading).
4. **Timer integrity** — client timer is advisory; server should stamp `started_at`/`completed_at`
   and could reject/flag submissions far past the limit. Decide how strict for v1.
5. **Retake freshness** — `exclude_seen` means retakes pull new questions automatically; good for
   freshness but means two attempts aren't the *same* items. Acceptable for a diagnostic (we compare
   area scores, not item scores), but note it in the report copy.

## 7b. TASK-B00 result (2026-06-23) — BANK IS INSUFFICIENT (blocker)

Ran the coverage probe against the live dev DB (`dsat_dev`):
- **Generated bank empty:** all 60 active questions are `content_origin='official'`; only 1 generated
  question exists and it is `draft`; 0 generation batches. The locked "generated bank as source"
  decision is currently un-buildable.
- **No hard tier:** `difficulty_overall` present values are only `low` and `medium` (+ many null).
  The easy→**hard** ramp cannot reach hard.
- **Thin + unclassified:** 60 total = 27 grammar / 13 reading / **20 unclassified domain**; 36 lack
  `question_family_key`. A 27-slot full-coverage blueprint is not fillable, and `exclude_seen` would
  exhaust the bank after a single attempt.

**DECISION (2026-06-23): Option B — ship official-bank v1 now.** Smaller blueprint, low→medium ramp,
single-attempt, partial coverage. Generation/full-vision v2 deferred.

### Annotation-key investigation (root cause of the "unclassified 20")
All 60 active questions are annotated by the **grammar v8 pipeline** (`prompt_version=v8.0`,
`rules_agent_dsat_grammar_ingestion_generation_v8`) — a single schema, not version drift. That
pipeline annotates **reading questions too**, but classifies reading under **`skill_family_key`
(singular)** and **never sets `reading_skill_family_key`/`reading_focus_key`**. Every question also
carries a `stem_type_key`. So the "unclassified 20" were really reading/expression questions the
current domain-derivation can't see. **bug-761**: the `/questions` reading filter and
`diagnostic_submit` domain logic must classify via `grammar_role_key` (grammar) vs
`skill_family_key` (reading), not `reading_skill_family_key`.

### TRUE usable coverage map (build the blueprint from THIS)
Clean split — **0 questions** have both `grammar_role_key` and `skill_family_key`.

**Grammar — 27 (via `grammar_role_key`):**
| role | low | medium | null | total |
|---|---|---|---|---|
| expression_of_ideas | 3 | 0 | 10 | 13 |
| punctuation | 2 | 2 | 3 | 7 |
| agreement | 0 | 1 | 2 | 3 |
| modifier | 2 | 0 | 0 | 2 |
| sentence_boundary | 1 | 0 | 0 | 1 |
| verb_form | 0 | 0 | 1 | 1 |
| **missing** | parallel_structure (0), pronoun (0) | | | |

**Reading — 13 (via `skill_family_key`):**
| skill family | low | medium | total |
|---|---|---|---|
| inferences | 1 | 4 | 5 |
| text_structure_and_purpose | 2 | 2 | 4 |
| central_ideas_and_details | 1 | 1 | 2 |
| command_of_evidence_textual | 0 | 1 | 1 |
| words_in_context | 0 | 1 | 1 |
| **missing** | command_of_evidence_quantitative (0), cross_text_connections (0) | | |

### Revised v1 blueprint (official bank)
- **Length:** ~16 questions (≈ 40% of the 40 usable — leaves headroom; single attempt per student
  is acceptable for a diagnostic, noted in report copy).
- **Domains:** ~10 grammar + ~6 reading (matches the bank's own grammar-heavy skew).
- **Coverage goal:** all **6** present grammar roles + all **5** present reading families ≥1 each;
  the two missing roles and two missing families are **explicitly out of v1** (documented gaps).
- **Ramp:** **low → medium** only (no hard tier exists). `null`-difficulty questions are treated as
  `medium` for ordering, OR sorted last within their tier — selector decides (TASK-B01).
- **Trap variety:** soft-preference only; bank too thin to require specific traps.
- **Time limit:** scale to length — ~19 min (16 Q × ~70s), constant `DIAGNOSTIC_TIME_LIMIT_SECONDS`.

## 7c. Stats / tracking architecture (DECISION 2026-06-23, revised)

Shared `UserProgress` table; rows tagged by `diagnostic_session_id` (non-null = diagnostic,
null = practice).

### Stream 1 — Weakness profile ("what to practice next") = DIAGNOSTIC **+ PRACTICE** (pooled)
- **REVERTED to include practice** (2026-06-23). `_compute_weakness_targets` (student.py:669) pools
  both diagnostic and practice rows — this is the **existing** behavior, so **no code change** is
  required here. Both diagnostic and practice answers feed `top_targets` / recommendations.
- **Keep `self_study_lookback_days`** rolling decay (unchanged). Diagnostic and practice rows both
  age out of the window together.
- Rationale: practice activity is real signal about current strengths/weaknesses; including it keeps
  the profile responsive between diagnostics. A student can build a profile from practice alone
  (does not strictly require a diagnostic first).

### Stream 2 — Practice-only improvement view (additive display)
- A separate, optional view that filters `UserProgress.diagnostic_session_id.is_(None)` and reports
  practice-only historical improvement (accuracy over time, by domain). This is a **display**, not a
  separation of the profile — the weakness profile still pools everything (Stream 1).

### Stream 3 (already exists) — Diagnostic snapshot/trend
- `DiagnosticSession` per-session `accuracy` + `/diagnostic/history` `improvement_trend` give the
  diagnostic-over-diagnostic baseline progression. Unchanged.

## 8. Out of scope (future)
- CAT / IRT adaptive difficulty.
- Two-module SAT-authentic routing (the `TestSessionResults` table is already there for it).
- Spaced-repetition resurfacing of missed diagnostic items (PRD Phase 2).
