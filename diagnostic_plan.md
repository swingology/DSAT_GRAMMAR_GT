# Diagnostic Blueprint V1 Plan

Status: Draft before task breakdown  
Last updated: 2026-06-25

## Purpose

Replace the current adaptive diagnostic with a fixed, test-condition diagnostic
that creates a first-pass student weakness profile without revealing answers
during the test.

The diagnostic should feel like a compact SAT Reading and Writing module:
students see one question at a time, move between numbered question pages, submit
at the end, and only then see score, answer review, and weakness breakdown.

This document is the product and architecture plan. A separate task file should
be created from this plan after the behavior is agreed.

## Locked Decisions

1. The current adaptive `DiagnosticTab` flow is replaced, not extended.
2. V1 uses the current active official/annotated bank because the generated bank
   is not ready.
3. V1 is a 16-question fixed blueprint.
4. Difficulty ramps from `low` to `medium`; the current bank has no `high`.
5. Answers and correctness are hidden until the diagnostic is submitted.
6. Each question gets its own navigable page/route.
7. Student weakness signals are stored through the existing `UserProgress` path.
8. The diagnostic should work for a brand-new student with no prior stats.

## Current Bank Reality

The active bank is thin but usable for a first diagnostic:

- 60 active questions.
- 27 grammar questions identified by `annotation_jsonb.grammar_role_key`.
- 13 reading questions identified by `annotation_jsonb.skill_family_key`.
- `reading_skill_family_key` and `reading_focus_key` are not populated in this
  bank and should not be used for diagnostic selection.
- Difficulty values are `low`, `medium`, and many `null`; no `high`.
- `null` difficulty should be treated as medium or placed after explicit medium
  questions within the medium tier.

V1 excludes empty bank areas:

- Grammar roles excluded: `parallel_structure`, `pronoun`.
- Reading families excluded: `command_of_evidence_quantitative`,
  `cross_text_connections`.

## Question Blueprint

The blueprint is an ordered list of 16 slots. Each slot describes the type of
question the backend should select.

Target coverage:

- Grammar: 10 questions.
- Reading: 6 questions.
- Low tier: questions 1-6.
- Medium tier: questions 7-16.
- No three consecutive questions should use the same domain.

Grammar roles to cover:

- `expression_of_ideas` appears 3 times.
- `punctuation` appears 2 times.
- `agreement` appears 1 time.
- `modifier` appears 1 time.
- `sentence_boundary` appears 1 time.
- `verb_form` appears 1 time.
- One extra grammar slot may be assigned to the strongest available pool,
  probably `expression_of_ideas` or `punctuation`.

Reading families to cover:

- `inferences` appears 2 times.
- `text_structure_and_purpose` appears 2 times.
- `central_ideas_and_details` appears 1 time.
- `command_of_evidence_textual` appears 1 time.
- `words_in_context` appears 1 time if there is room after balancing the final
  16 slots. If not, it must be represented in the next blueprint revision.

The final task file should turn this into an explicit `BLUEPRINT_V1` tuple with
stable slot numbers.

## Selection Rules

Backend selection should happen server-side at diagnostic start.

For each slot:

1. Try exact match: difficulty, domain, role or skill, optional focus, optional
   trap preference.
2. Drop trap preference.
3. Drop focus.
4. Drop difficulty and include `null` difficulty.
5. Fall back to any unseen active question in the same domain.
6. If that domain is exhausted, fall back to any unseen active question and mark
   the slot as a coverage gap.

Selection must:

- Return exactly 16 distinct question IDs.
- Exclude questions already selected in the same diagnostic.
- Prefer unseen questions for that student.
- Persist the ordered `question_ids` on `DiagnosticSession`.
- Return a `coverage_report` showing fallback levels and gaps.

## Backend Contract

`POST /api/diagnostic/start` with `diagnostic_type: "blueprint_v1"` should:

- Resolve the student from `user_token`.
- Create a `DiagnosticSession`.
- Assemble the 16-question blueprint.
- Persist `question_ids` in presentation order.
- Set `total_questions = 16`.
- Return the full ordered module.

Response shape:

```ts
type DiagnosticStartV1Response = {
  session_id: string
  total_questions: number
  time_limit_seconds: number
  questions: DiagnosticQuestion[]
  coverage_report: Record<string, unknown>
}
```

`DiagnosticQuestion` must not include:

- `current_correct_option_label`
- option `is_correct`
- explanation text that reveals the answer
- any correctness flag or answer key

It should include:

- `seq`
- `id`
- `domain`
- `current_question_text`
- `current_passage_text`
- `passage_spans`
- `options` with only `{ label, text, distractor_type_key? }`
- `grammar_role_key`
- `grammar_focus_key`
- `skill_family_key`
- `difficulty_overall`
- `question_family_key`
- `stimulus_mode_key`

## Answer Submission

Each question page can save an answer as soon as the student selects an option.
This should call:

`POST /api/diagnostic/{session_id}/submit`

The UI must ignore `is_correct` in the response during the test.

Submit behavior:

- Save or update the selected option for that question.
- Write a `UserProgress` row tagged with `diagnostic_session_id`.
- Populate `question_domain`, `question_difficulty`, and miss fields from the
  question annotation.
- Keep session counts dynamic; do not hardcode 8.
- Do not duplicate `question_ids` for blueprint sessions.

If answer-changing is allowed, v1 may write multiple `UserProgress` rows for the
same question. The report should use the latest submitted answer per question,
or the backend should upsert per session/question. The task file should make
this decision explicit before implementation.

## Completion And Stats

The final button calls:

`POST /api/diagnostic/{session_id}/complete`

Completion should:

- Mark `completed_at`.
- Compute `accuracy`.
- Return `correct_count`, `total_questions`, and `duration_seconds`.
- Return a weakness breakdown computed from diagnostic answers.
- Leave `UserProgress` populated so existing recommendations and student stats
  can use the diagnostic signal.

Required result breakdown:

```ts
type CorrectTotal = {
  correct: number
  total: number
}

type DiagnosticBreakdown = {
  by_family: Record<string, CorrectTotal>
  by_difficulty: Record<string, CorrectTotal>
  by_trap: Record<string, CorrectTotal>
  weakest_areas: Array<{
    area_key: string
    domain: "grammar" | "reading" | null
    correct: number
    total: number
    accuracy: number
  }>
}
```

The weakness profile for practice recommendations remains pooled: diagnostic
answers plus practice answers both contribute through `UserProgress`.

## Frontend Flow

Routes:

- `/diagnostic` shows the intro/start screen.
- `/diagnostic/:sessionId/q/:seq` shows one question page.
- `/diagnostic/:sessionId/review` shows the post-submit report.
- Existing `/diagnostic/history` and `/diagnostic/:sessionId` should reuse the
  report or a read-only variant after the v1 report exists.

Intro screen:

- States the format: 16 questions, about 19 minutes, answers shown at the end.
- Starts `blueprint_v1`.
- Does not require prior recommendations or `top_targets`.

Question page:

- Shows one question only.
- Shows the passage/stem and answer options.
- Does not show correctness, explanations, answer colors, or the correct answer.
- Lets the student select/change an option.
- Saves selected answer silently.
- Has Back and Next controls.
- Has a numbered question palette linking to every question page.
- Palette states: current, answered, unanswered, marked for review.
- Has a Mark for Review toggle.
- Shows a timer pinned in the header.
- Shows Finish/Submit on the last page and in the palette/header for early
  submission.

Finish behavior:

- If any questions are unanswered, show a confirmation that lists the count.
- On confirm, complete the diagnostic and navigate to the report.
- Timer expiry auto-completes with whatever answers have been saved.

Report screen:

- Shows score percentage and correct/total.
- Shows time used.
- Shows breakdown bars by family, difficulty, and trap.
- Shows top weak areas.
- Provides practice CTAs for weak grammar/concept areas.
- Shows question-by-question review only after completion, including selected
  answer, correct answer, explanation, and trap/focus context.

## Data Dependencies

Frontend needs:

- `VITE_STUDENT_API_KEY` for API-key auth.
- `VITE_TEST_USER_TOKEN` or localStorage `user_token` for user-scoped calls.

Backend needs:

- DB migrated through the latest revision.
- Active questions with latest annotations.
- `skill_family_key` support in diagnostic selection.
- A no-answer-key diagnostic payload.

## Acceptance Criteria

- A new student can start a diagnostic with no prior stats.
- Start returns 16 ordered questions.
- No answer key reaches the client during the test.
- Each question is accessible by route and by numbered palette link.
- Back/Next and direct number navigation preserve selected answers.
- Submit/finish works from the last question and early from the runner.
- Completing the diagnostic writes `UserProgress` rows tagged with the session.
- The result screen reports score and weakness breakdown.
- Existing recommendation logic can use diagnostic misses.
- The old adaptive reveal-mode diagnostic UI is removed.

## Out Of Scope For V1

- CAT/IRT adaptive routing.
- Two-module SAT routing.
- Hard difficulty tier.
- Full generated-bank coverage.
- Strict server-side timer enforcement.
- Separate diagnostic-only weakness profile.

## Open Decisions Before Task Breakdown

1. Should changing an answer update one existing diagnostic progress row or write
   another row and let reporting use the latest?
2. Should unanswered questions be submitted as blank/incorrect, or omitted from
   `UserProgress` and counted as unanswered in the report?
3. Should route refresh on `/diagnostic/:sessionId/q/:seq` reload the question
   list from the session, or should v1 require in-memory state after start?
4. Should `words_in_context` be guaranteed in the 16-slot blueprint even if that
   requires shifting one grammar slot to reading?
5. Should the timer be purely client-side in v1, or should late submissions be
   flagged server-side?
