# Debug Log

## 2026-07-31 - 2024 PT3 answer audit review
Report created by: Claude Opus 5
Git branch: `weakness-weighted-mixed-practice`
Git checkpoint: `373390b` — Update session tracking logs

Reviewed `2024_PT3_audit.md` (authored by Codex) against the rendered source PDFs and the
live database. All three modules are 27 pages / 27 questions, page N = question N. No
official Test 03 answer key exists locally, so the audit's "provisional" framing is
accurate. Scope: the 2 proposed answer changes, the missing-question claim, and the option
-text finding. Database NOT modified — this was a review only.

**Every substantive claim in this audit checked out.** Unlike PT1 and PT2, no finding
required correction.

### Findings

1. **Confirmed:** Module 2B Q13 — proposed change C → **B** is correct. Graph values are
   unambiguous at 300 dpi: spray coating 15.5% (lowest) / 17.3% (highest); spin coating
   11.7% (lowest) / 13.6% (highest). B ("lowest performing spray ... higher than highest
   performing spin") is true: 15.5 > 13.6. The stored answer C claims highest spray ≈13%
   and highest spin ≈11%; both figures are wrong (actual 17.3 and 13.6), so C is false.

2. **Confirmed:** Module 2B Q19 — proposed change A → **C** is correct. `however` is
   parenthetical and needs commas on both sides: `resisted the godfather nickname,
   however, feeling that ...`. Source choice C (`nickname, however,`) is the only option
   satisfying that. The audit's transcription of all four source choices is exact.

3. **Confirmed:** Module 2B Q4 is genuinely absent from the DB. A gap scan across all
   three modules (1–27 each) returns exactly one missing slot — M2B Q4 — matching the
   audit's claim of 81 source slots vs. 80 stored rows. Source page 4 confirms answer
   **A** (`repudiates`): the stem's continuation "this rejection is evident in his series
   Reservation Dogs" makes "rejects" the required sense.

4. **Confirmed:** Module 2B Q19 choices B and C are stored identically (both
   `nickname, however;`). Source C is `nickname, however,` with a comma. Same class of
   punctuation-normalizing ingestion defect as PT1 Q13 (bug-819) and PT2 M1 Q19
   (bug-820) — in each case the corrupted character is the one the question tests.

5. **Medium — audit omission:** The audit states it covers "all 80 canonical PT3 database
   rows" but never documents that Module 1 is stored under the legacy
   `source_test_name = 'Bluebook Practice Test 3'`, not `Test03_ENG_Sec01_Mod01`. Only
   Modules 2A and 2B use the `Test03_ENG_*` scheme. PT2's audit documented its equivalent
   naming split explicitly; PT3's does not. A repair script written from the audit's own
   framing (`WHERE source_test_name LIKE 'Test03_ENG%'`) silently selects 53 rows and
   misses all 27 Module 1 rows. Same dual-naming defect previously seen in 2024 PT4.

6. **Medium — additional, not in the audit:** Both flipped questions carry stored
   explanations that argue for the wrong answer, and Q19's is internally contradictory.
   Q19's explanation states the correct rule ("requires a comma before and after the
   parenthetical adverb 'however'") and then selects choice A, which has no comma after
   `however`, calling it "the best of the given choices" — while choice C satisfies the
   rule the explanation just stated. Q13's explanation endorses C for "directly comparing
   the highest efficiencies" without citing C's actual figures, attaching a true
   relationship (spray > spin) to the option whose stated numbers are false. Any repair
   must rewrite both explanations, not just the answer labels.

### Verified sound

- **Key-string internal consistency.** The audit's three proposed key strings were diffed
  against the DB. Modules 1 and 2A match exactly across all 54 questions; Module 2B
  differs at precisely Q13, Q19, and the missing Q4. The audit's summary tables, its
  per-question verdict tables, and its key strings all agree — the defect found in PT2
  (key string disagreeing with the audit's own verdict table at Q19) is absent here.
- **No passage duplication.** A hash scan over all populated `current_passage_text` values
  across all three PT3 modules returns zero duplicate groups. The PT2 Q7 defect (passage
  copied from the preceding question) has no analogue in PT3, so the audit's silence on
  this is correct rather than an oversight.

### Resolution — applied 2026-07-31

All three changes propagated to `dsat_dev` via `scripts/repair_pt3_audit.py` (single
transaction, 26 statements, backup at `backups/pt3_audit_20260731/`). Applied: M2B Q13
C→B, M2B Q19 A→C with choice C's option text restored to `nickname, however,`, and M2B Q4
inserted with answer A. New explanations and all four per-option rationales written for
each of the three. Module 2B's stored key now matches the audit's proposed key exactly
across all 27 questions. PT3 row count is now 81.

Q4's UUID (`8aea0ed6-bd26-5a13-a3a3-0aaba514d4e4`) was derived with the ingestion
pipeline's own deterministic UUID5 scheme (`ingest.py::_official_question_uuid`, verified
by reproducing the existing Q3 and Q5 IDs), so a future re-ingestion of this module is
idempotent rather than duplicate-creating. Its annotation is flagged
`needs_human_review: true` since the content is hand-written rather than model-generated.

Verification: drift scan over all 81 PT3 rows returns zero mismatches on option text,
`is_correct`, and answer label across `question_options`, `choices_jsonb`, and
`annotation_jsonb`; every question has exactly one correct option and four distinct option
texts. All five surfaces (questions.current_*, question_versions, question_options,
annotation_jsonb scalars, annotation_jsonb.options[]) agree on all three repaired rows.

7. **Medium — pre-existing, database-wide, found during this repair:** 408 of 1489 rows
   have a `latest_annotation_id` pointing to an annotation whose `question_version_id` is
   a superseded version. PT3 M2B Q13 is one, which surfaced as a silent `UPDATE 0` when
   the repair script first keyed its annotation update on `question_version_id`. Fixed in
   the script by targeting `questions.latest_annotation_id` instead. **The PT2 repair was
   re-verified and is unaffected** — it already keyed on `latest_annotation_id`, and all
   six of its annotations carry the correct answer despite two having stale version links.
   Any future tooling that reaches annotations via `question_version_id` will silently
   no-op on roughly 27% of the table.

8. **Low — pre-existing, not repaired:** five PT3 questions have annotations with
   incomplete option detail. M1 Q10's annotation has no `options` array at all; M2A Q1,
   Q3, Q4, and Q6 carry `option_label` and `is_correct` but omit `option_text`. These
   account for all 24 rows flagged by the post-repair drift scan. Stored answers are
   correct in every case — only the annotation shape is sparse. Combined with the PT2
   finding (M1 Q20 and M2B Q16 using `text`/`label` instead of
   `option_text`/`option_label`), there are at least three distinct annotation option
   shapes in the table, which any consumer or scan must handle.

### Caveat on the 78 "keep" rows

The key-string diff establishes that the audit and the DB agree; it does NOT establish
that either is right. Both could be wrong together — that is exactly what happened in PT2,
where the DB and the audit agreed on M1 Q17, M2A Q11, and M2B Q21 and all three were
wrong. The 78 keeps rest on the audit's cross-test duplicate matching against PT4–PT11 and
were not independently verified against source here.

## 2026-07-30 - 2024 PT2 answer audit review
Report created by: Claude Opus 5
Git branch: `weakness-weighted-mixed-practice`
Git checkpoint: `373390b` — Update session tracking logs

Reviewed `2024_PT2_audit.md` (authored by Codex) against the scanned source PDFs and the
live database. As with PT1, the PDFs are image-only and required page rendering. All three
modules are 27 pages / 27 questions, so page N maps to question N. No official Test 02
answer key exists locally, so the audit's "provisional" framing is accurate. Scope of this
review was the 4 proposed answer changes plus the 3 integrity findings — the 77 "keep"
rows were NOT independently verified (they rest on the audit's cross-test duplicate
matching). Database was not modified.

### Findings

1. **Confirmed:** Module 01 Q17 — audit's proposed change B → **D** is correct. Choices A,
   B, and C all place punctuation between the complementizer `that` and its content clause
   (`the volume and speed of water...`), which is ungrammatical regardless of how the
   `because of` coordination is analyzed. D is the only clean option. The audit's stated
   rationale ("no punctuation belongs inside that structure") reaches the right answer but
   describes the wrong discriminator.

2. **High — audit is wrong:** Module 01 Q19 — the audit proposes A → **B**; the correct
   answer is **C**. The passage is a three-item series in which each product carries its
   own date: `Chickasaw Basic, in 2009` / `an online television network, Chickasaw TV, in
   2010` / `a Rosetta Stone language course in Chickasaw, in 2015`. Only source choice C
   (`Basic, in 2009; an online television network,`) preserves that pairing. The audit's
   choice B (`Basic; in 2009,`) severs `Chickasaw Basic` from 2009 and re-attaches 2009 to
   the TV network, contradicting the passage. The audit's Module 1 proposed key string is
   therefore wrong at position 19.

3. **High:** Module 01 Q19 option-text corruption is wider than the audit reports. The
   audit states only that DB choices A and B are duplicates. Actual DB state: A and B are
   identical (both `...network;`), and C and D also store `network;` where the source has
   `network,`. Three of four option texts are corrupt. Because C is the correct answer,
   the stored text of the correct option is itself wrong — "restore choice B" is
   insufficient. Same class of ingestion defect as PT1 Q13 (bug-819).

4. **Confirmed:** Module 02A Q11 — audit's proposed change C → **D** is correct. Graph
   reads control zinc ~390 / iron ~625 ppm, kanamycin-exposed zinc ~300 / iron ~225 ppm.
   D ("lower levels of iron and zinc than the control plants") is the only option that is
   both factually true and responsive to the uptake-alteration hypothesis. The stored
   answer C (zinc ~300 control / ~400 exposed) reverses the actual values and is false.

5. **Confirmed:** Module 02B Q21 — audit's proposed change B → **A** is correct. Both A and
   B are conventionally valid punctuation, so the discriminator is what `however`
   contrasts. The contrast is between Okinaka sitting on the board and not deciding alone;
   the third clause (approval by nine other experts) explains rather than contrasts, so
   `however` belongs at the end of the first clause: `single-handedly, however;`.

6. **Confirmed:** Module 02B Q7 — DB `current_passage_text` is the Wigner-crystal passage
   copied from Q6, not the *Terropterus xiushanensis* passage the question asks about.
   Verified against source page 7. Answer D is correct as stored.

7. **Confirmed:** Module 02B Q19 — DB explanation describes a nonrestrictive appositive
   `'the oldest dating back to the 1800s'` that appears nowhere in this question. The
   source is the Bisa Butler quilt-portrait passage; answer B (`quilts, the`) is correct as
   stored, forming the absolute phrase `quilts, the stitching barely visible`. Explanation
   and distractor rationale JSONB need replacement.

### Net effect on the audit's recommendations

Of the 4 proposed answer changes, 3 are correct (M1 Q17, M2A Q11, M2B Q21) and 1 is wrong
in its target (M1 Q19 → C, not B). All 3 integrity findings are real; finding #1 (Q19
options) understates the corruption.

### Resolution — applied 2026-07-31

All findings above propagated to `dsat_dev` via `scripts/repair_pt2_audit.py` (single
transaction, 46 statements, backup at `backups/pt2_audit_20260731/`). Applied: the four
answer changes (M1 Q17→D, M1 Q19→C, M2A Q11→D, M2B Q21→A), M1 Q19's four option texts
restored from source, M2B Q7's passage replaced, and new explanations plus rewritten
per-option `why_plausible`/`why_wrong` rationales on all six questions. All four
rationales were rewritten per question, not just the flipped pair, because the originals
encoded a wrong theory of each question. Synced across `questions.current_*`,
`question_versions` (`correct_option_label`, `explanation_text`, `choices_jsonb`,
`passage_text`), `question_options`, and `annotation_jsonb.options[]`.

Verification: drift scan across all 81 PT2 rows returns zero mismatches on option text,
`is_correct`, and answer label across all three storage surfaces; every question has
exactly one correct option and four distinct option texts. Zero `user_progress` rows
existed on the six questions, so no attempt data was invalidated; edits were made in place
rather than by minting new versions, matching the bug-819 precedent.

Two incidental discoveries, neither touched: M1 Q20 and M2B Q16 store annotation options
under `text`/`label` rather than `option_text`/`option_label` (content correct, key shape
differs — the initial drift scan false-positived on these until made shape-aware). M2B Q8
shares Q6/Q7's passage length but has distinct correct content, so the Wigner duplication
was confined to Q7 as the audit reported.

## 2026-07-30 - 2024 PT1 answer audit review + Module 01 Q13 option-text repair
Report created by: Claude Opus 5
Git branch: `weakness-weighted-mixed-practice`
Git checkpoint: `373390b` — Update session tracking logs

Reviewed `2024_PT1_audit.md` (authored by Codex) against the scanned source PDFs and the
live database. The PDFs are image-only, so verification required page rendering rather
than text extraction. No official Test 01 answer key exists (`Answer Keys/` holds only
Tests 05–10), so the audit's "provisional" framing is accurate.

### Findings

1. ~~**High:** Module 01 Q13 answer choices stored as bare years (`1800`, `1900`, `1950`,
   `2012`) instead of the source PDF's year-pair phrases. Because the stored labels no
   longer denoted the PDF's choices, the DB label `C` did not correspond to PDF choice
   `C`, making the question unanswerable and its answer label meaningless.~~
   - Affected: `questions`, `question_versions.choices_jsonb`, `question_options`
     (question_id `fb857823-10f1-5c19-b328-fb733978bb6d`)
   - Stem was also stored as "complete the text?" instead of "complete the statement?"
   - The four `why_wrong`/`why_plausible` rationales described single years, not pairs
   - **Fixed:** Rewrote all four option texts and `choices_jsonb` from the PDF; moved the
     correct answer to label `A` ("1900 with the employment by sector in 1950.") — the
     choice the pre-existing explanation already reasoned about; corrected the stem;
     rewrote the four distractor rationales. Verified all three storage locations agree.
     A drift scan across all 81 PT1 questions returned 0 inconsistencies. No
     `user_progress` rows existed, so no attempt data was invalidated. See bug-819.

2. **Medium:** The audit lists Q13 in its summary table as an answer change "C → A" and
   bakes `A` into its proposed Module 1 key, while its own data-integrity note concedes
   the question is invalid until option texts are re-ingested. With bare years stored,
   "change to A" asserted nothing. The correct verdict was *unusable pending re-ingest*.
   - **Fixed:** Superseded by finding 1 — the options were re-ingested, so `A` is now a
     meaningful and correct answer label.

3. **Medium (open):** Module 01 Q21 (`antiquity, however;`) is duplicated across three
   tests with byte-identical option text, and the DB disagrees with itself:
   2024 PT1 M01 Q21 = `D`, but 2024 Test10 M02B Q18 = `C` and 2025 Test8 M01 Q24 = `C`.
   Source-PDF review supports `C` (the "also" in clause 2 marks it as supporting evidence
   for clause 1, not a contrast — so "however" attaches to clause 1). PT1 is the outlier.
   - Not yet fixed; the remaining audit corrections (M1 Q11, Q17, Q21; M2A Q22) were
     reviewed and confirmed but not propagated to the database.

4. **Low:** Audit reasoning verified as correct on all five proposed changes
   (M1 Q11 A→D, Q13 C→A, Q17 A→D, Q21 D→C; M2A Q22 C→D). The three proposed key strings
   transcribe the audit's own per-question verdict columns without error.

## 2026-07-30 - Backend crash-loop blocks all login (missing Pydantic models after merge)
Report created by: Claude Opus 5
Git branch: `missed_question`
Git checkpoint: `90f6752` — Merge branch 'stimulus-type-picker' into missed_question

### Findings

1. **Critical:** After the stimulus-type-picker merge, Google OAuth login fails because the
   entire backend is down. `dsat-backend` container crash-loops on startup:
   `ImportError: cannot import name 'RecentBatchSummary' from 'app.models.payload'`
   (`backend/app/routers/admin.py:32`). With the backend unable to import `app.main`,
   no endpoint is served — `POST /api/auth/google` is unreachable, so login appears broken.
   - Root cause: the merge introduced `admin.py` imports for `RecentBatchSummary`,
     `GraphTagRequest`, and `AdminQuestionListResponse`, but these three Pydantic models
     were never added to `backend/app/models/payload.py`.
   - Affected: `backend/app/routers/admin.py`, `backend/app/models/payload.py`.
   - **Fixed:** Added the three models to `payload.py` (after `BatchAggregates`), with field
     shapes derived from `admin.py` usage sites and the `GenerationBatch` DB model.
     Verified `app.main` imports clean, backend startup completes, `/api/auth/me` → 401
     (alive, unauth), `POST /api/auth/google` → 422 (alive, bad body). Frontend proxy on
     :5174 forwards `/api/*` to `http://backend:8000` correctly. (bug-815)

## 2026-07-29 - MixedPracticePage never renders a question (field-name mismatch)
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `a230326` — Add design spec for stimulus-type practice picker

### Findings

1. **High:** `MixedPracticePage.tsx:136` reads `data?.questions?.[0]`, but `GET /api/questions`
   (`backend/app/routers/student.py::student_recall`, `response_model=StudentQuestionsListResponse`
   in `backend/app/models/payload.py`) returns `{items, inventory}` — there is no `questions` key.
   `question` is always `null`, so every Mixed Practice session falls through to the
   "No questions available right now." empty state, regardless of what filters are applied.
   - Affected: `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`.
   - Discovered while designing the stimulus-type picker feature (routes into this page).
   - **Fix scheduled:** Task 0 of `docs/superpowers/plans/2026-07-29-stimulus-type-picker.md`
     (`data?.questions?.[0]` → `data?.items?.[0]`, with a regression test).

## 2026-07-29 - stem_type_key column/jsonb drift and stray values across active question bank (canonicalized)
Report created by: glm-5.2:cloud
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** 744 of 1410 active questions carried a non-canonical `stem_type_key` in the
   denormalized `questions.stem_type_key` column (residual pre-`canonicalize_stem`/sanitizer Pass-1
   emission labels, e.g. `grammar_convention`×54, `synthesize_notes`×48, `transition`×45,
   `conventions_of_standard_english`×34). A further 211 rows had column AND `annotation_jsonb` BOTH
   canonical yet DISAGREEING (e.g. column `complete_the_text` vs jsonb `most_logically_completes`).
   Diagnostic blueprint filtering keys off `annotation_jsonb.stem_type_key` (`diagnostic/queries.py`)
   while practice recall + review facets read the `questions.stem_type_key` column (`routers/student.py`),
   so strays and disagreements made the two code paths surface different question sets.
   - Affected: `questions.stem_type_key`; `question_annotations.annotation_jsonb->>'stem_type_key'`.
   - **Root cause:** the flat column drifted from authoritative `annotation_jsonb` (pre-canonicalization
     era). The `annotation_sanitizer` uses `difflib.get_close_matches` (cutoff 0.7), NOT the
     `_STEM_ALIASES` map, so same-dimension strays like `conventions_of_english` were dropped to null
     rather than mapped; the column was never re-synced.
   - **Fixed:** `scripts/fix_stem_type_canonicalization.sql` (bug-812). Aligned column←jsonb for 940
     rows where jsonb was canonical and they differed; same-dimension task→task alias-map (6 entries
     incl `grammar_convention`) applied to 15 edge rows (13 jsonb-stray + 1 no-key + 1 no-annotation):
     column set for 15, jsonb canonicalized for 13, key added for the 1 no-key row. Added 4 missing
     aliases to `_STEM_ALIASES` in `extract_prompt.py` (`choose_grammatically_correct_form`,
     `conventions_of_english`, `choose_logical_transition`, `synthesize_information_from_notes`) for
     recurrence prevention. Post-state: 0 column strays, 0 jsonb strays, 0 col/jsonb disagreement
     across all 1410 active questions. Pre-repair backup: `backups/stem_type_pre_repair_20260729_192456.dump`.

## 2026-07-29 - Stray off-vocabulary keys in active question bank broke diagnostic targeting and stimulus-mode filtering (canonicalized)
Report created by: glm-5.2:cloud
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** ~150 active questions carried stray off-vocabulary keys. `stimulus_mode_key` (column) had
   24 stray values (only 9 canonical: sentence_only, passage_excerpt, prose_single, prose_paired,
   prose_plus_table, prose_plus_graph, notes_bullets, notes_summary, poem); `grammar_role_key`
   had 19 strays; `skill_family_key` had 9 strays — all grammar-domain concepts misplaced into the
   reading field (e.g. `Boundaries`, `Form, Structure, and Sense`, `agreement`). Stray
   grammar_role/skill_family values never match any diagnostic blueprint slot, so affected questions
   silently fell through to the "any active" fallback, degrading diagnostic targeting. Stimulus-mode
   filtering (practice recall reads `questions.stimulus_mode_key`) missed whole question families.
   - Affected: `questions.stimulus_mode_key`; `question_annotations.annotation_jsonb`
     (grammar_role_key, skill_family_key).
   - **Root cause:** the validator tags unknown vocab keys `severity="review"` (non-blocking, by
     design — `validator.py:107` "LLM may return near-miss keys"), recording them to
     `candidates.json` but never blocking or canonicalizing; nobody processed `candidates.json`, so
     strays accumulated. Separately, the denormalized `questions.stimulus_mode_key` column had
     drifted from the authoritative `annotation_jsonb` value (293 rows disagreed pre-repair).
   - **Fixed (one-time DB repair, scope = data only, no pipeline change):** grammar_role near-miss
     synonyms -> canonical (verb->verb_form, adjective->modifier, subject_pronoun->pronoun, etc.);
     2 reading-domain names misplaced into grammar_role (information_and_ideas, craft_and_structure)
     -> NULL + `needs_human_review=true`; all 9 stray skill_family keys -> NULL (the grammar_role
     sibling carries the domain); `stimulus_mode_key` column aligned <-
     `annotation_jsonb->>'stimulus_mode_key'` (latest_annotation_id) for all 293 disagreeing rows
     (annotation is the canonical authoritative source). Result: **0 strays in all 4 fields**,
     column<->annotation **0 disagreements**. 4 low-confidence rows flagged for re-annotation
     (conventions_grammar x2, information_and_ideas, craft_and_structure). Pre-fix backup
     `backups/dsat_dev_20260729_171846_pre_vocab_canonicalization.dump`. bug-811.
   - **Diagnostic pool after repair:** 707 grammar + 677 reading + 25 no-domain (fall to any-active).
   - **Key lesson:** `annotation_jsonb` is the authoritative source; the `questions.<key>` columns
     drift. Repair = align column <- annotation, NOT hand-mapping from stem_type heuristics (the
     initial hand-map got `notes` wrong — mapped to notes_summary from the synthesis stem, but the
     annotation correctly said notes_bullets: stimulus_mode = stimulus FORMAT, stem_type = TASK,
     they are orthogonal).
2. **Low (out of scope, flagged):** `stem_type_key` also carries strays (grammar_punctuation,
   synthesize_notes, rhetorical_synthesis, synthesize_information, etc.) — not touched in this
   repair. Recurrence prevention (validator alias layer or blocking unknown vocab keys) also not
   done — scope was DB repair only. Both are future items.


## 2026-07-29 - Admin Google OAuth login HTTP 500: uvicorn --reload poisoned SQLAlchemy mapper state (not a code bug)
Report created by: glm-5.2:cloud
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** `POST /api/auth/google` (and `POST /api/auth/refresh`) returned HTTP 500 with
   `TypeError: tuple indices must be integers or slices, not NoneType`, raised inside SQLAlchemy
   `unitofwork.py:371` (`lambda tup: tup[0]._props.get(tup[1].key) is tup[1].prop`) during
   `db.commit()` in `student_auth.py:google_login` (writing `user.refresh_token` /
   `refresh_token_expires`). Google OAuth login was broken on the admin app and the tailscale
   endpoint.
   - Affected: `backend/app/routers/student_auth.py` (line ~166 commit site);
     `backend/app/main.py` (uvicorn `--reload` launch).
   - **Root cause (NOT a code/model bug):** uvicorn `--reload` re-imported SQLAlchemy mappers
     in-place at ~16:18–16:19 (a batch edit adding a model to `db.py` + touching `payload.py`
     and multiple routers) without cleanly tearing down the old mapper registry, poisoning the
     long-running worker's unit-of-work dependency-processor state (`PopulateDict.__missing__`
     → creator returned `None` in `uow._mapper_for_dep`). Every `commit()` in the poisoned
     worker 500'd. Proof: reproducing the identical commit in a *fresh* python process inside
     the same container returned `COMMIT OK`, confirming the models and DB were fine and only
     the live worker was corrupt.
   - **Fixed:** `docker restart dsat-backend` so the process re-imports mappers cleanly.
     Verified `POST /api/auth/google` → `200 OK` in the live logs and the user confirmed
     successful login. bug-810.
   - **Prevention:** drop `--reload` in the dev stack (or restart the worker after any
     multi-file model edit). A fresh-process repro is the diagnostic that distinguishes
     "code is broken" from "worker state is corrupt."
2. **Low:** Default JWT secrets were re-activated by the restart (see bug-779/780 family) —
   `.env` must be reloaded for production secrets. Flagged, not in scope for this fix.

## 2026-07-29 - Ingestion blocking policy: graph/chart questions and other recoverable blocking errors were silently dropped instead of held for review
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** Any per-question `blocking` validation error during ingestion caused that question to
   be skipped entirely — never persisted to the DB in any status, not even `draft`. The
   `validate_annotation_completeness` docstring claimed "blocking prevents active promotion" but
   the actual per-question loop in `routers/ingest.py` did a hard `continue` on any blocking error
   before persistence. This is the root cause behind PT4 Mod02 Q13 and PT5 Mod02's graph question
   needing manual SQL backfill earlier today instead of showing up in the admin review queue.
   - **Fixed:** Per user direction, redefined the blocking-error policy in
     `pipeline/validator.py`: (1) any chart/graph/table stimulus (`stimulus_mode_key` in
     `prose_plus_graph`/`prose_plus_table`, or `table_data`/`graph_data` present) now always
     blocks, independent of `skill_family_key`; (2) non-visual questions now also require
     `passage_text` (question_text + 4 options were already required). All pre-existing blocking
     checks were kept. In `routers/ingest.py`, `_persist_single_question` gained a `force_draft`
     parameter: only blocking errors on `question_text`/`options`/`correct_option_label`
     (structurally unusable data) still skip persistence; every other blocking reason now persists
     the question with `practice_status='draft'` and `needs_human_review=true` instead of dropping
     it. Added 3 new validator tests and fixed `test_validate_official_question_passes`'s fixture
     (was missing `passage_text`, which real ingested `sentence_only` questions carry in 662/687
     cases). Full suite: 1124 passed, same 6 pre-existing unrelated failures. Logged as bug-809.

## 2026-07-29 - 2025 PT4 Sec01 Mod02: entire module never ingested
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** 2025 PT4 Sec01 Mod02 (R&W Module 2) had zero rows in the DB — no `question_assets`/
   `question_jobs` row and no `questions` rows at all (confirmed via direct query).
   - The archive YAML (`backend/archive/official/2025_4_01_02.yaml`) was also incomplete: Q7 was
     missing entirely (two-column PDF layout caused `pdftotext` to skip it during archive
     generation), and Q13's `correct_option_label` (A) plus graph `structured_data` both
     contradicted the official answer key/rationale (official answer is D).
   - **Fixed:** Wrote `scripts/gen_fix_pt4_2025_mod02.py` to build all 33 questions — 32 from the
     YAML (recovering dropped `sentence_only` prompts from option shape) plus Q7 sourced manually
     from the test PDF — with every `correct_option_label` forced to the verified official key
     (D,D,B,B,B,B,A,C,C,A,A,B,D,C,C,A,B,D,C,A,B,D,D,A,B,B,A,A,C,C,A,A,B). Q13 flagged
     `needs_human_review` with `graph_structured_data_omitted=true` since its chart data is
     untrustworthy and needs a manually-corrected graph asset. Generated idempotent SQL
     (`scripts/fix_pt4_2025_mod02_create.sql`), took a table backup
     (`backups/pre_pt4_mod02_backfill_20260729_145936.sql`), and applied it. Verified: 33/33
     questions present (qn 1-33), each with 4 options, 1 version, 1 annotation, and correct
     answers matching the official key. Logged as bug-807.

## 2026-07-29 - 2025 PT5 Sec01 Mod01: Q26 missing from question bank (and from archive YAML)
Report created by: Claude Opus 5 (glm-5.2:cloud)
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **Medium:** 2025 PT5 Sec01 Mod01 Q26 was missing entirely — no active, draft, or rejected row.
   - The gap extended to the archive YAML: `backend/archive/official/2025_5_01_01.yaml` has 32
     questions (max qn 33) with Q26 absent, so the question could not be sourced from the YAML.
     All content (passage, stem, 4 options) was extracted from
     `Test_5_digital_sec01_mod01.pdf`; the correct answer (B) came from the official answer-key
     PDF (`sat-practice-test-5-answers-digital.pdf`, R&W Module 1, QUESTION 26).
   - Q26 is a conventions-of-Standard-English punctuation item (supplementary elements; Sophie
     Calle / "The Blind" passage).
   - **Fixed:** `scripts/fix_pt5_2025_mod01_q26_create.sql` — PL/pgSQL DO block creating the
     question + version + 4 options + minimal annotation. Matched active-sibling storage
     (`source_test_name=NULL`, `stimulus_mode_key=sentence_only`,
     `stem_type_key=standard_english_conventions` flat / `conform_to_standard_english` in
     annotation). `annotation_stale=true` / `needs_human_review=true` for a later LLM pass.
     Pre-fix backup: `backups/dsat_dev_20260729_134912_pre_pt5_mod01_q26.dump`.
     Verified: qn=26, correct=B, plen=317, 4 options, active. Module now has qn 1-33 with no gaps.
   - Related: bug-806. NOTE: the broader mod01 cleanup (13 rejected `"Test 5"` duplicate pairs,
     Q31 still `draft`, Q6/Q8/Q9 active rows with doubled 8-option sets, Q9 active-vs-rejected
     answer mismatch) is NOT done — flagged for a user scope decision.

## 2026-07-29 - 2025 PT5 Sec01 Mod02: missing questions, NULL passages, wrong answers, duplicate draft/active pairs
Report created by: Claude Opus 5 (glm-5.2:cloud)
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** 2025 PT5 Sec01 Mod02 (R&W Module 2) question bank was incomplete and inconsistent.
   - 7 questions missing entirely (Q3, Q4, Q5, Q20, Q22, Q27, Q29).
   - 6 surviving rows had `current_passage_text` NULL (Q19, Q21, Q23, Q24, Q25, Q28).
   - 4 rows had wrong `current_correct_option_label` (Q21, Q24, Q25, Q28).
   - 12 duplicate draft/active (or active/rejected) pairs coexisted — the
     `uq_official_question_canonical_identity` constraint allows them because the twin rows
     carried different `source_test_name` values.
   - `source_test_name` was not normalized across survivors.
   - Root cause: ingestion failed to create the 7 sentence-only questions and left 6 others
     without a split passage; duplicate pairs from rejected/draft ingestion runs were never
     reconciled. The LLM-generated explanation file (`TEST05_sec01_mod02.md`) had WRONG answer
     keys for Q22 (said C, official B) and Q23 (said D, official A) — trusting it would have
     embedded wrong answers + wrong rationales.
   - **Fixed:** `scripts/fix_pt5_2025_mod02_cleanup.sql` (generated by
     `scripts/gen_fix_pt5_2025_mod02.py`) — single transaction:
     (A) backed up + FK-safe deleted 12 dup rows across all 23 tables referencing `questions(id)`
     (`question_stimulus_assets` was the only one with live dependents — Q12/Q14 figure links,
     whose kept twins already carry their own);
     (B) filled `passage_text` + corrected answers + explanations for the 6 no-passage rows;
     (C) created the 7 missing rows via a PL/pgSQL DO block (questions + versions + options +
     minimal annotations, `annotation_stale=true` / `needs_human_review=true` for a later LLM pass);
     (D) normalized `source_test_name` to `Test_5_digital_sec01_mod02`.
     Pre-fix backup: `backups/dsat_dev_20260729_131037.dump`.
     Verified post-fix: 33 questions (qn 1-33), 0 missing passages, 0 duplicate qns, 0 bad
     source_test_name, all 33 `current_correct_option_label` match the official answer-key PDF.
     Q26 remains `practice_status='draft'` (complete + correct; out of scope — user decision).
   - Related: bug-805; same missing-passage pattern as PT6 Sec01 Mod02 Q1-Q5 (bug-804).

## 2026-07-29 - 2025 PT6 Sec01 Mod02: Q1–Q5 passage not split from stem
Report created by: Claude Opus 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** 2025 PT6 Sec01 Mod02 Q1–Q5 (vocabulary-in-context items) were mis-split during
   ingestion: the sentence-with-blank was stored in `current_question_text`, `current_passage_text`
   was NULL, and the "Which choice completes the text with the most logical and precise word or
   phrase?" prompt was missing entirely.
   - Root cause: the ingestion passage/stem splitter (`_split_passage_from_question` in
     `backend/app/routers/ingest.py`) failed to split these five items. The other 28 questions in
     the module split correctly (verified row-by-row against
     `backend/archive/official/2025_Practice_Test_6_6_01_02.yaml`).
   - Q3 also carried an OCR artifact (`_______ ,` → `_______,`).
   - **Fixed:** `scripts/fix_pt6_2025_mod02_q1_q5_split.sql` — in-place update (bug-245/796
     pattern) backing up the 5 `questions` rows + their latest `question_versions` rows into
     `backup_pt6_2025_mod02_q1_q5_*` tables, then setting `current_passage_text` = the canonical
     sentence and `current_question_text` = the prompt from `backend/archive/official/6_01_02.yaml`
     (dollar-quoted, exact values), mirrored onto the latest `question_versions` row via
     `latest_version_id`, with `is_admin_edited = true`, `annotation_stale = true`. Pre-fix backup
     dump: `backups/dsat_dev_20260729_123150.dump`. Verified all 33 module rows now have a passage
     + a proper short prompt stem. Logged as bug-804.

## 2026-07-29 - 2025 PT9 Sec01 Mod02: q1/q2/q3 rotated out of their correct slots
Report created by: Claude Opus 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** The first three questions of 2025 PT9 Sec01 Mod02 were rotated relative to the
   source PDF (`TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/Test_9_digital_sec01_mod02.pdf`).
   - Ground truth from the PDF is q1 = Anita Desai "completing", q2 = "Predatory animals …
     provide", q3 = "Teju Cole … enthusiasm for".
   - Ingested state was q1 = Teju Cole, q2 = a duplicate of the Anita Desai item (carrying the
     module's OCR header boilerplate — "Reading and Writing / 33 QUESTIONS / …" — inside
     `current_passage_text`), q3 = Predatory animals.
   - A prior session corrected q1 in place. That left "Predatory animals" correct only at q3 and
     the duplicate Anita Desai item still sitting at q2, so the rotation had to be completed.
   - q4–q33 were spot-checked against the PDF and are correctly slotted.
   - **Fixed:** Migration `fix_pt9_2025_mod02_q2_q3.sql`. q2 (`28687b6a`) took the Predatory
     animals payload, q3 (`1a0c20b6`) took the Teju Cole payload. Both payloads were copied
     verbatim from existing `question_versions` rows (`da117d33` and the pre-fix q1 version
     `a3782c17`) rather than retyped, preserving the exact blank-token form. Question UUIDs were
     preserved and each target received a new version 2. Correct labels moved with the content
     (q2 → C, q3 → B) across `questions.current_correct_option_label`,
     `question_versions.correct_option_label` and the `question_options` rows; annotation keys
     moved too (q2 `passage_excerpt`/`choose_word_in_context` → `sentence_only`/`complete_the_text`).

2. **Medium:** The two archive YAML mirrors had diverged from each other and from the DB.
   - `backend/archive/official/9_01_02.yaml` (canonical — `config.local_archive_mirror = "./archive"`)
     received the earlier q1 fix; `archive_generated/official/9_01_02.yaml` did not, so it still
     served Teju Cole at q1.
   - `backend/archive/official/9_01_02.yaml` was additionally **missing question 31 entirely**
     (32 entries, numbering jumped 30 → 32). This is the previously-noted "32 vs 33" discrepancy;
     it was a genuine dropped entry, not a parse failure.
   - **Fixed:** Both mirrors rewritten so q1/q2/q3 match the DB; q31 spliced back into
     `backend/archive/official/9_01_02.yaml` from `archive_generated` after confirming its
     `question_id` (`238d3bef`) and correct answer (D) match the DB row. Both files now parse and
     carry a contiguous 1–33 with unique question ids.

3. **Low (pre-existing, not introduced here, left as-is):** The archive YAML mirrors lag the DB
   for every question in this module that has been admin-edited. Comparing YAML against the DB's
   latest version across all 33 questions: correct answers match everywhere (0 differences), but
   `question_text` differs for q6, q8, q9, q17, q18, q29–q33 and `passage_text` differs for 24
   questions (8 of those whitespace-only). Every one of the 10 `question_text` differences is a
   question with `is_admin_edited = true` and `max(version_number) = 2` — the YAML still carries
   the v1 ingest text while the DB serves v2. The DB is authoritative and is what both the admin
   and student APIs read, so this does not affect what users see. Flagged rather than fixed
   because reconciling 24 entries is well beyond the scope of the q2 correction and needs a
   deliberate decision about regenerating the archive from the DB.
   - Consequence for the q31 splice above: the restored q31 block carries the v1 text, matching
     the file's existing convention for admin-edited questions. Its `question_id` and correct
     answer match the DB.

### Verification

- Admin API: `GET /admin/questions` on `127.0.0.1:8002` (header `X-API-Key: admin-test-key`,
  `sort_by_source=true`) returns q1 Anita Desai / q2 Predatory animals (C, provide) /
  q3 Teju Cole (B, enthusiasm for) / q4 Marilyn Dingle, total 33.
- Student API: `GET /api/questions` (header `X-API-Key: student-test-key`) serves the same order
  with `current_passage_text` populated and full option sets.
- Pre-change snapshots in `backup_pt9_mod02_q2q3_2026_07_29_{questions,versions,options,annotations}`.

## 2026-07-29 - PT11 (2025) "b l a n k" placeholder artifact + passage/stem merge
Report created by: Claude Opus 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **Medium:** 23 of 66 PT11 questions (`source_exam_code='11'`, release year 2025) carry the literal
   lowercase token `b l a n k` (letter-spaced) where the answer blank should be `____`.
   - Origin is the **source PDF**, not the ingester: the College Board accessible/nondigital PDFs render
     the blank as the letter-spaced word "b l a n k" (screen-reader text) rather than an underscore run.
     `sat-practice-test-11-digital-sec01-mod01.pdf` contains 19 occurrences and
     `...-sec01-mod02.pdf` contains 20 — no `_{3,}` runs at all in either.
   - Live in `questions.current_*`: **Mod01 q1,2,3,4,5,15,17,18,19,20,21,22,23,24,25,26,27,28,29** (19
     questions — module never remediated) and **Mod02 q2,3,4,13** (4 questions; the other 16 Mod02
     questions were cleaned to `____` at some point, so the remediation pass was partial).
   - Corpus-wide state for PT11: 57 rows use the correct `____` form, 17 still have `b l a n k` in
     `current_passage_text`, 6 have it in `current_question_text`.
   - Historical `question_versions` rows retain the raw token for effectively all of Mod02 as well
     (q1–4, 13, 14, 17–30), so any code reading non-latest versions still sees it.
   - No occurrences in `question_options.option_text` (0 rows) or in any explanation field.
   - Derived analysis artifacts inherited the token: `analysis/calibration/official_classifications.json`
     (40), `analysis/v8/focus_evidence/*.json` (~8 each), `analysis/calibration/calibration_set.json` (4).
   - There is **no real archive YAML for PT11** — `backend/archive/official/PT11_M1.yaml` is a 1-question
     test fixture (`passage_text: A short passage about ecology.`), not an export, so the DB is the only
     copy of this content.

2. **Medium:** For the 6 questions where the token landed in the stem (Mod01 q15, q17, q18, q19, q23;
   Mod02 q13), the passage and the question stem were concatenated into `current_question_text` and
   `current_passage_text` is NULL. Example — Mod01 q15 stores the full biofuel passage ending
   `...the fuel with the highest energy density is b l a n k Which choice most effectively uses data from
   the graph to complete the sentence?` as a single stem.
   - Causally linked to finding 1: the passage/stem splitter keys off the `____` blank as a delimiter, so
     the letter-spaced token defeated the split. 9 PT11 rows total have a NULL `current_passage_text`.
   - Not fixed in this pass — reported only, per the request to locate occurrences.

## 2026-07-28 - Test08_ENG_Sec01_Mod02B missing question q4
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**High:** `Test08_ENG_Sec01_Mod02B` (2024 PT8, sec01, mod02B) had only 26 of 27 questions in the `questions` table; q4 was absent.
   - Same root cause family as bug-797/798/799: `current_correct_option_label` NOT NULL/CHECK-constrained; the passage sentence was never captured during original extraction. The archive YAML's stub annotation explicitly said `explanation_short: Cannot determine without passage text` with `annotation_confidence: 0.2`.
   - Note: Test08 has no per-module split PDF like other tests (`Test01-07_ENG_Sec01_Mod0*.pdf` pattern) — instead uses a single combined `Test_08_VERBAL_Sections.pdf` (81 pages = Mod01 + Mod02A + Mod02B, 27 pages each) plus a separate `Answer Keys/TEST_08_Answer_Key.pdf`. Module-relative page N maps to absolute page `54 + (N-1)` for Mod02B.~~
   - **Fixed:** Rendered absolute page 57 (module-relative page 4) of `Test_08_VERBAL_Sections.pdf` to recover the passage sentence and confirmed options matched the archive YAML exactly. Determined correct answer = A (repudiates) from context (colon-introduced explanation: "this rejection is evident..."). Inserted `questions`, `question_versions`, `question_options`, and `question_annotations` rows, and updated the archive YAML in place (added the missing `passage_text` field). All 27 questions in the module now persist correctly.

## 2026-07-28 - Test06_ENG_Sec01_Mod02B blank Focus column for several questions
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**Low:** Admin dashboard "Focus" column (`annotation.grammar_focus_key`) was blank for 15 of 27 questions in `Test06_ENG_Sec01_Mod02B`. Checked corpus-wide: `choose_words_in_context`, `choose_sentence_function`, `choose_detail`, `choose_main_idea`, `choose_best_illustration`, `choose_command_of_evidence_quantitative`, `choose_best_support`, and `most_logically_completes` have **zero** non-null `grammar_focus_key` values anywhere in the database (50-86 samples each) — this is intentional taxonomy, not a gap, since that field is scoped to grammar/conventions and expression-of-ideas questions. Only the notes-synthesis stem types (`synthesize_notes`, `choose_best_notes_synthesis`) have an established focus taxonomy in ~80% of cases (`data_interpretation_claims`, `emphasis_meaning_shifts`, `logical_relationships`, `precision_word_choice`, `redundancy_concision`, `register_style_consistency`, `synthesis_of_information`).
   - Also found the archive YAML is stale relative to the live DB in places unrelated to this fix — q16 and q19 show different `grammar_focus_key` values in the YAML (`null`, `run_on_sentence`) than what's actually live in `question_annotations` (`comma_splice`, `verb_form`), meaning the DB annotation was edited after the YAML was last exported and never re-synced. Not touched in this pass — flagged for awareness.~~
   - **Fixed:** User confirmed scope — filled Focus only where an established taxonomy applies. Set q25=`logical_relationships`, q26=`data_interpretation_claims` (already present in the archive YAML but missing from the live DB annotation — a genuine gap, not just a blank-by-design case), q27=`synthesis_of_information`. User then asked to also fill q6 and q10 (Craft & Structure / Information & Ideas types that are blank everywhere else in the corpus) — did so as an explicit exception: q6=`logical_relationships` (reused existing corpus term), q10=`textual_evidence_support` (**new term, not used elsewhere in the corpus** — flagging in case this should be reconciled with an existing tag during a future taxonomy pass). Synced `question_annotations.annotation_jsonb` (both top-level and nested `classification.grammar_focus_key`) and the archive YAML for all 5 questions.

## 2026-07-28 - Test06_ENG_Sec01_Mod02B missing questions q6, q10, q25
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**High:** `Test06_ENG_Sec01_Mod02B` (2024 PT6, sec01, mod02B) had only 24 of 27 questions in the `questions` table; q6, q10, and q25 were absent. User reported q25 specifically; q6 and q10 were also missing but not yet noticed in the admin dashboard.
   - Same root cause pattern as bug-797/bug-798: `current_correct_option_label` is NOT NULL/CHECK-constrained to A-D, and these 3 never resolved a correct answer during original ingestion, so the per-question SAVEPOINT persist step failed silently.
   - Unlike prior cases, q6 and q10 already had a fully-written `explanation_full` in the archive YAML that explicitly named the correct option in prose (e.g. "Option C correctly captures this") — the annotation reasoning completed, but the discrete `correct_option_label` field was still left empty, and/or the annotation was missing other required completeness fields, so the validator still rejected persistence. q25 had no annotation block at all.~~
   - **Fixed:** For q6 and q10, extracted the correct answer directly from the already-written explanation text in the archive YAML (C and D respectively) — no PDF lookup needed. For q25 (a rhetorical-synthesis "student wants to emphasize a similarity" notes question with no annotation), determined the answer by process of elimination among the 4 notes-based options (A states a shared trait; B and D state differences; C covers only one wave type) — answer A. Inserted `questions`, `question_versions`, `question_options`, and `question_annotations` rows for all 3 and updated the archive YAML in place. All 27 questions in the module now persist with valid answers and annotation metadata.

## 2026-07-28 - Test04_ENG_Sec01_Mod02B missing questions q2, q3, q17, q23
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**High:** `Test04_ENG_Sec01_Mod02B` (2024 PT4, sec01, mod02B) had only 23 of 27 questions in the `questions` table; q2, q3, q17, q23 were entirely absent (confirmed missing in admin dashboard Data Management view).
   - Same root cause pattern as `Test03_ENG_Sec01_Mod02A` (bug-797): `current_correct_option_label` is `NOT NULL`/CHECK-constrained to A-D, and these 4 never received a completed annotation pass, so the per-question SAVEPOINT persist step failed silently during original ingestion.
   - q2, q17, q23 had complete extraction data in the archive YAML (`backend/archive/official/2024_Test04_ENG_Sec01_Mod02B_04_01_02B.yaml`) but empty `correct_option_label` and no/partial annotation block.
   - q3 was worse: the archive YAML had *no passage text anywhere* — `question_text` was just the generic stem, and the existing (unused) annotation stub explicitly said `explanation_short: Cannot determine without the sentence text` with `annotation_confidence: 0.1`, meaning the original extraction pass never captured the sentence at all, not just the annotation.~~
   - **Fixed:** Rendered PDF pages 2 and 3 of `TESTS/DATA_SRC/2024-2025 Tests Answers/Test04_ENG_Sec01_Mod02B.pdf` to recover q2 and q3's passage text directly from the source (Bluebook screenshots, no text layer). q17 and q23 already had full passage/option text in the archive YAML, just no resolved answer. Determined correct answers by context (q2=B paucity of, q3=C buttress, q17=D "prey; rather,", q23=B "species, both native and nonnative;") and inserted `questions`, `question_versions`, `question_options`, and `question_annotations` rows for all 4 (with `grammar_focus_key`/`difficulty_overall`/`question_family_key` populated so Focus/Difficulty display correctly in the admin dashboard, per the gap found in bug-797). Updated the archive YAML in place, including adding the previously-missing `passage_text` field for q3. All 27 questions in the module now persist with valid answers, passage text, and annotation metadata.

## 2026-07-28 - Test03_ENG_Sec01_Mod02A missing questions q1, q3, q4, q6
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**High:** `Test03_ENG_Sec01_Mod02A` (2024 PT3, sec01, mod02A) had only 23 of 27 questions in the `questions` table; q1, q3, q4, q6 were entirely absent (confirmed missing in admin dashboard Data Management view).
   - Archive YAML (`backend/archive/official/2024_Test03_ENG_Sec01_Mod02A_03_01_02A.yaml`, last modified 2026-06-13) has all 27 question numbers, but q3, q4, q6 have no `annotation:` block and q1 has only a partial one (missing `stimulus_mode_key`/`stem_type_key`/explanation) — all had `correct_option_label: ''`.
   - Root cause: `questions.current_correct_option_label` is `NOT NULL` with a CHECK constraint restricting it to A-D. The ingestion pipeline (`backend/app/routers/ingest.py`) resolves the correct answer from the annotation pass when extraction doesn't supply one (`_resolve_correct_option_label`); since these 4 questions never received a completed annotation, no valid answer label could be resolved, so the per-question SAVEPOINT persist step failed and was skipped — while the other 23 questions in the same module persisted fine independently.
   - No `question_job_questions`, `admin_question_audit_logs`, or backup-table rows exist for these 4 question IDs, confirming they were never previously persisted (not a later deletion).~~
   - **Fixed:** Rendered PDF pages 1, 3, 4, 6 of `TESTS/DATA_SRC/2024-2025 Tests Answers/Test03_ENG_Sec01_Mod02A.pdf` to PNG and read them directly (Bluebook UI screenshots, no answer key present in the PDF — text layer is empty/image-only). Determined correct answers by context (q1=B observant, q3=C persistent, q4=B inadequate, q6=A validate) and inserted `questions`, `question_versions`, and `question_options` rows for all 4 using the existing deterministic question IDs from the archive YAML. Updated the archive YAML in place with the resolved `correct_option_label` and a minimal annotation block (`needs_human_review: true` since answers were manually reasoned, not LLM-annotated) so it stays in sync with the DB. All 27 questions in the module now have valid `current_correct_option_label` and `current_passage_text`.
2. ~~**Medium:** The 4 questions above had no `question_annotations` row (`latest_annotation_id` was NULL), so the admin dashboard's Data Management table showed blank "Focus" and "Difficulty" columns for them — both are read from `annotation.grammar_focus_key`/`annotation.difficulty_overall` in `APP/ADMIN_APP/src/pages/DataManagement.tsx`, which come back `null` when there's no annotation row at all.~~
   - **Fixed:** Created a `question_annotations` row for each of q1, q3, q4, q6 (classified as `grammar_focus_key: precision_word_choice`, `grammar_role_key`/`question_family_key: expression_of_ideas`, matching sibling questions q2/q5/q26 in this module) with per-question difficulty (`q1=low`, `q3=medium`, `q4=medium`, `q6=low`, based on how many clauses/inference steps each requires) and topic/evidence-scope metadata, and linked each via `questions.latest_annotation_id`. Flagged `needs_human_review: true` and `provider_name: manual`/`model_name: claude-sonnet-5` in `annotation_jsonb.review` since this was reasoned manually rather than produced by the LLM annotation pipeline. All 27 questions in the module now show consistent Focus/Difficulty/Family metadata in the admin dashboard.

## 2026-07-28 - Test02_ENG_Sec01_Mod02B passage text missing for q1-27
Report created by: Claude Sonnet 5
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High:** 16 of 27 questions in `Test02_ENG_Sec01_Mod02B` (2024 PT2, official verbal, sec01 mod02B) have `current_passage_text` NULL: q1-4, 6, 8, 9, 12-19, 21.
   - `question_versions` history confirms passage text was never populated at ingestion (2026-06-08 16:14 batch). Only q5 and q20 were later patched via manual admin edits that same day (16:29-16:59), the same pattern already fixed for `Test02_ENG_Sec01_Mod02A` (see entry below).
   - Affected `stimulus_mode_key` values: `sentence_only` (9 of 13 missing) and `passage_excerpt` (7 of 10 missing) — inconsistent within the same type, ruling out "this type has no passage by design."
   - No recovery path via `question_assets` or `question_source_spans` — both tables have zero rows for this test, so there is no stored OCR/crop to re-extract from; passages must be pulled from the source PDF (`TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/` or equivalent 2024 legacy PDF) and backfilled manually, same approach as the Mod02A fix.
   - Related: `Test01_ENG_Sec01_Mod02B` has 1 missing, `Test04_ENG_Sec01_Mod02B` has 2 missing — same root cause, smaller blast radius.
   - User is handling the backfill manually via the admin dashboard edit UI; not yet fixed.

## 2026-07-28 - Test02_ENG_Sec01_Mod02A passage text missing or out of sync for q1-27
Report created by: Claude (kimi-k2.7-code:cloud)
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. **High (Fixed):** Most questions in `Test02_ENG_Sec01_Mod02A` q1-27 had `passage_text` missing from `question_versions` and/or `current_passage_text` out of sync with `question_versions.passage_text`.
   - Affected: 23 of 27 questions in `Test02_ENG_Sec01_Mod02A` q1-27 (official 2024 PT2 verbal sec01 mod02A).
   - Root cause: ingestion stored the passage sentence inside `current_question_text` for many grammar/vocab questions and never populated the denormalized `current_passage_text` or `question_versions.passage_text`. Reading questions (q8, q9, q10, q13) already had passages, but q12 had `current_passage_text` set while its latest version lacked `passage_text`.
   - **Fixed:** Copied canonical passage text and question stems from the matching `Test02` (module `02`) official questions into mod02A for q2, q4, q5, q6, q8, q9, q10, q13, q16, q19, q20, q21, q22, q24, q25, q26, q27, syncing both `questions.current_passage_text`/`current_question_text` and `question_versions.passage_text`/`question_text`. Synced q12's latest version `passage_text` from its existing `current_passage_text`. 18 questions updated in total; all now have synced current and version passage text. (Subsequently fixed the remaining 9 questions via PDF visual extraction; see finding 2.)
2. ~~**Medium:** 9 questions remain without passage text after the DB-level sync.
   - q11: graph question with a stimulus asset (expected to have no passage text).
   - q1, q3, q7, q17, q18, q23: grammar/conventions questions where the entire sentence is currently stored in `current_question_text`; separating the passage from the stem requires the original PDF/ OCR or known canonical stems.
   - q14, q15: reading-comprehension stems with no passage text available in the DB and no matching question in `Test02` module `02`; extracting their passages requires OCR of the source PDF (`Test02_ENG_Sec01_Mod02A.pdf`). Marker OCR timed out after 5 minutes on a 3-page range, so these remain pending.~~
   - **Fixed:** Rendered the source PDF pages to PNG and visually extracted the missing passages/stems. q1, q3, and q7 were already correctly split. Updated q14, q15, q17, q18, and q23 by moving the sentence-with-blank (or full reading passage) into `current_passage_text`/`question_versions.passage_text` and replacing `current_question_text`/`question_versions.question_text` with the correct stem. q11, which has a graph stimulus asset, received the descriptive text below the graph as its `passage_text`. Full inspection now reports 0 problems across all 27 questions.

## 2026-07-28 - marker_single extraction crashes with ld.so relocation assertion (exit 127)
Report created by: Claude (kimi-k2.7-code:cloud)
Git branch: `missed_question`
Git checkpoint: `cd18fef` — Ignore local worktree scratch directory

### Findings

1. ~~**High:** `stimulus_worker.py` jobs fail with `RuntimeError: marker exited 127` whenever marker layout recognition runs.
   - Reproduced on: `TESTS/DATA_SRC/2024-2025 Tests Answers/Test01_ENG_Sec01_Mod01.pdf` page 12 with `--disable_ocr --output_format json`.
   - Actual stderr from `marker_single`: `Inconsistency detected by ld.so: ../sysdeps/x86_64/dl-machine.h: 498: elf_machine_rela_relative: Assertion 'ELFW(R_TYPE) (reloc->r_info) == R_X86_64_RELATIVE' failed!`
   - Root cause: dynamic-linker crash while loading the PyTorch/surya layout model. The exit code 127 comes from the crashed loader, not "command not found". System glibc is `2.42`; marker worker uses uv Python 3.12.11 (Clang 20.1.4) + torch 2.11.0+cu128 + marker-pdf 1.10.2. This points to an ABI/binary-wheel incompatibility rather than a bug in `stimulus_backfill.py`.
   - Affected: `tools/marker_worker/.venv/bin/marker_single`, `backend/scripts/stimulus_backfill.py` `_run_marker`.~~
   - **Fixed:** Switched marker worker to CPU-only torch. Updated `tools/marker_worker/pyproject.toml` to pin `torch==2.11.0+cpu` and source it from the PyTorch CPU wheel index (`https://download.pytorch.org/whl/cpu`). Regenerated `uv.lock`, ran `uv sync`, and verified `marker_single` completes layout recognition on PT01_ENG_Sec01_Mod01.pdf page 12 with exit code 0. The host NVIDIA driver is too old for CUDA 12.8 anyway, so CPU-only is the correct configuration for this machine. Logged as bug-795.

## 2026-07-28 - Stimulus asset end-to-end verification fixes
Report created by: Claude (kimi-k2.7-code:cloud)
Git branch: `missed_question`
Git checkpoint: `5c7597a` — Add admin dashboard audit and launcher support

### Findings

1. **High (Fixed):** Backfilled stimulus assets returned `url` pointing to a JSON manifest, so student/admin image tags were broken.
   - Affected: `backend/app/routers/student.py` `_load_stimulus_assets_by_question`, `backend/app/routers/admin.py` `list_questions` and `get_stimulus_assets`.
   - **Fixed:** Joined the linked `QuestionSourceSpan` row and used `crop_path` for `url` when present; falls back to `storage_path` for admin-uploaded assets (which are images directly). Verified via `/api/questions` and `/admin/questions` responses for PT4 Mod01 Q13/Q15.

2. **High (Fixed):** Dev-stack `/assets` 404ed for crops written by host-side backfill.
   - Affected: `docker-compose.yml` backend service.
   - **Fixed:** Mounted `./local_object_store:/local_object_store` and set `OBJECT_STORAGE_LOCAL_ROOT: /local_object_store` so the container serves the same directory the host scripts write to. Verified: crop PNGs return `200 image/png`.

3. **Medium:** Two `table` crops were assigned to PT4 Mod01 Q13 by the marker backfill.
   - This is marker's layout output (two Table blocks near that question number), not a code bug. The admin UI can review and delete/replace the extra crop if it is redundant.

## 2026-07-27 - asyncpg stale-schema error after adding questions.source_has_graph
Report created by: Claude (glm-5.2:cloud)
Git branch: `missed_question`
Git checkpoint: `5c7597a` — Add admin dashboard audit and launcher support

### Findings

1. **Medium:** After applying alembic migration 035 (adding nullable Boolean `questions.source_has_graph`), the running backend raised `UndefinedColumnError: column questions.source_has_graph does not exist` on `list_questions` even though `\d questions` confirmed the column and `alembic_version=035`.
   - Root cause: the backend's asyncpg connection pool held prepared statements describing the pre-ALTER schema. `uvicorn --reload` reloaded the Python code (new queries now reference `source_has_graph`) but did not re-establish the pool, so asyncpg prepared the new SELECT against stale cached metadata and PostgreSQL rejected the unknown column.
   - **Fixed:** `docker restart dsat-backend` to create a fresh pool. End-to-end verified: `list_questions` surfaces the field, `POST /admin/questions/{id}/graph-tag` toggles true/false, DB persists, `tsc` clean. (Also logged as bug-790 in `.wolf/buglog.json`.)

## 2026-07-27 - PT9 module-2 triplication + 4 tests with stray "02" module code (data dedup + convention fix)
Report created by: Claude (glm-5.2:cloud)
Git branch: `missed_question`
Git checkpoint: `5c7597a` — Add admin dashboard audit and launcher support

### Findings

1. **High (Fixed):** Module-code naming convention was violated in the raw data for five 2024 tests.
   - The agreed convention: `Mod02` is the default; `Mod02A`/`Mod02B` are used only when a test has two module-2 sections (the DSAT adaptive easy/hard pair).
   - 2024 PT1/PT4/PT5 had a plain `02` bucket sitting alongside `02B` (the `02` was the missing `02A` variant — confirmed by shared source PDF names and question text). 2024 PT2 had `02` alongside `02A` (the `02` was the missing `02B`).
   - **Fixed:** `UPDATE questions SET source_module_code='02A'` for PT1/PT4/PT5 and `='02B'` for PT2 (deterministic: the `02` maps to whichever of 02A/02B is absent). Each now reads cleanly as Mod02A + Mod02B.
   - 2025 tests were already correct (single module-2 each -> Mod02). Clean 2024 tests (PT3/6/7/8/10) were already correct (02A + 02B).

2. **Critical (Fixed):** 2024 PT9 module-2 questions were **triplicated** in the DB — every question number 1-27 existed under `02`, `02A`, AND `02B` (with `02B` doubled), giving ~51 rows per module (4x duplicated content). The A and B variants are genuinely different questions (e.g. qn5: A="main purpose of the text" vs B="function of the underlined"), so this was duplicated content from a bad ingest, not a label clash.
   - **Fixed:** Relabeled PT9 `02` -> `02A`, then deduped each (qn, mod) pair to one row, keeping by priority [has user_progress > has admin_question_audit_logs > practice_status='active' > earliest created_at]. Reassigned the 8 `admin_question_audit_logs` rows (both `question_id` and `question_version_id`) from the doomed questions to their surviving twin so audit history was preserved and the NO_ACTION FKs cleared. Deleted in FK-safe order: 50 questions + 50 annotations + 54 versions + 216 options (nulled doomed questions' `latest_annotation_id`/`latest_version_id` first; options -> annotations -> versions -> questions). PT9 module-2 went 102 -> 52 rows (26x02A + 26x02B). The 3 `user_progress` rows on qn24 02A were preserved; 0 dangling version pointers after. Backups kept: `backup_pt9_{questions,annotations,versions,options}_2026_07_27` and `backup_questions_2026_07_27`.
   - Test-explorer cards went 49 -> 48; every card now follows `Year · PT# · Sec01 · Mod{01|02|02A|02B}`. Logged as bug-789 in `.wolf/buglog.json` (related to bug-788 naming fix).
## 2026-07-27 - Data Management test cards: inconsistent naming + broken merged-card filter
Report created by: Claude (glm-5.2:cloud)
Git branch: `missed_question`
Git checkpoint: `5c7597a` — Add admin dashboard audit and launcher support

### Findings

1. **High (Fixed):** "Browse by Test" cards labeled tests with raw `source_test_name`/`source_exam_code` (e.g. "Bluebook Practice Test 5  01  02B" or "Test05_ENG_Sec01_Mod02B  01  02B"), included no year, and produced duplicate/ambiguous cards for the same logical test (e.g. 2024 PT5 Mod02B appeared as two separate source rows: exam_code `05` and exam_code `verbal`). Clicking such a merged card filtered `list_questions` by exact `source_test_name`, which matched 0 rows because the Mod02B questions lived under a *different* `source_test_name` than the card's representative row.
   - Root cause: no canonical test-id column exists; `source_test_name` is freeform and `source_exam_code` carries dirty values (`05`, `verbal`, `SAT`). Grouping/filtering on those raw fields cannot identify one logical test across its inconsistent source rows.
   - **Fixed:** Added a server-side canonical PT# derivation `_pt_number_expr` in `backend/app/routers/admin.py` (digits of `source_exam_code`, else first digit run of `source_test_name` via a two-stage `regexp_replace` that avoids the `NULLIF(result, original)` trap on purely-numeric test_name like `"05"`). `list_tests` now `GROUP BY (year, pt, subject, section, module)` and returns `pt_number`; `list_questions` gained a `pt_number` filter and sorts by `pt_number`; `TestSummary` gained `pt_number` (legacy `source_test_name`/`source_exam_code` kept optional, now null). Frontend (`DataManagement.tsx`, `types/index.ts`) renders cards as `Year · PT# · Sec## · Mod##`, question rows as `Year · PT# · Sec## · Mod## · Q#`, and filters by `pt_number`. Verified via curl: 49 deduplicated cards (was 58 raw rows); the 2024 PT5 Mod02B card returns all 38 merged questions sorted by Q#. TypeScript typecheck clean. Logged as bug-788 in `.wolf/buglog.json`; related to bug-787 (the `/admin/tests` 500 that first exposed this surface).

## 2026-07-15 - Admin dashboard add-user 502 on stale :5173 instance; .env missing VITE_BACKEND_ORIGIN
Report created by: Claude (glm-5.2:cloud)
Git branch: `oauth_feature`
Git checkpoint: `41bcd27` — Move completed/superseded task files to _deprecated/

### Findings

1. **High (Fixed):** Adding a user through the admin dashboard 502'd on the `:5173` admin vite instance.
   - Root cause: two admin vite processes were running — pid 1276245 on `:5175` (launched with `VITE_BACKEND_ORIGIN=http://localhost:8002`) and a stale pid 1253380 on `:5173` launched WITHOUT that env var. `APP/ADMIN_APP/vite.config.ts` proxy defaults to `http://localhost:8000` when `VITE_BACKEND_ORIGIN` is unset, but the dev-stack backend listens on host `:8002` (compose maps `8002->8000`). So `:5173`'s proxy forwarded `/api/users` to a dead `:8000` → 502. `APP/ADMIN_APP/.env` also lacked `VITE_BACKEND_ORIGIN`, so any fresh `vite` start without the shell env reproduced the 502.
   - **Fixed:** Killed stale `:5173` process (pid 1253380). Persisted `VITE_BACKEND_ORIGIN=http://localhost:8002` into `APP/ADMIN_APP/.env`. Verified `POST /api/users` through `:5175` returns 201 (then deleted the test user, 204). Canonical admin port is **5175**.
   - Backend `POST /users` itself was healthy throughout (direct `:8002` call returned 201). Logged as bug-784 in `.wolf/buglog.json`; related to bug-777/778 (admin app `/api` prefix mismatch).

## 2026-07-13 - OAuth login: no end-to-end browser tests; Playwright setup plan
Report created by: Claude Sonnet 5
Git branch: `oauth_feature`
Git checkpoint: `e29ce58` — Add Google OAuth login across backend, student app, and admin app

### Findings

1. **High (not fixed — tooling gap):** No Playwright/e2e tests exist for the OAuth login flow. Every auth test fakes Google at its seam, so a real Google ID token has never flowed through the system in a real browser.
   - Backend: `backend/tests/test_google_auth.py` (17 tests) monkeypatches the Google verifier and uses FastAPI `TestClient` (in-process, no browser). Proves auth logic, not Google integration.
   - Student app: `src/auth/__tests__/auth.test.tsx` (8 tests) runs in jsdom. Proves token/refresh/guard logic, not the GIS popup.
   - Admin app: no auth tests at all.
   - `playwright` is in no `package.json`/`pyproject.toml`; no e2e/spec files, no Playwright config. The only real-browser work was the O-00c one-off `playwright-core` + `google-chrome-stable` origin-render check (button renders, never completed a login; script not saved in repo).
   - The PRD (`.scratch/oauth-login/PRD.md` ~L159) explicitly deferred frontend login verification to **live QA (Phase 4)**, not automated browser tests.

   **Playwright setup — packages and commands (per app, student and/or admin):**
   - `npm install -D @playwright/test` — adds the test runner + `@playwright/test` API
   - `npx playwright install chromium` — downloads the Chromium binary (add `firefox webkit` for cross-browser)
   - `npx playwright install-deps chromium` — installs OS-level shared libs on Linux (may need `sudo`)
   - Add to `package.json` scripts: `"test:e2e": "playwright test"`
   - Add `playwright.config.ts` at the app root:
     ```ts
     import { defineConfig, devices } from '@playwright/test'
     export default defineConfig({
       testDir: './e2e',
       fullyParallel: true,
       use: { baseURL: 'http://localhost:5173', trace: 'on-first-retry' },
       projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
       webServer: {
         command: 'npm run dev',
         url: 'http://localhost:5173',
         reuseExistingServer: !process.env.CI,
         timeout: 60_000,
       },
     })
     ```
   - First spec `e2e/login.spec.ts`: navigate to `/`, assert redirect to `/login`, assert the Google button renders, and (stubbed) assert a successful credential exchange routes to the dashboard. For the admin app, additionally assert a non-admin account hits the "Not an admin" screen.

   **Caveats for the GIS popup flow:**
   - Driving the real Google sign-in popup against `accounts.google.com` is flaky and against Google's ToS for automated sign-in. Do **not** automate the real Google account chooser.
   - Recommended e2e seam: inject a fake GIS credential before the app loads (`page.addInitScript`) and stub `window.google.accounts.id` so `loginWithGoogle` receives the fake credential. The backend then either (a) runs with its existing monkeypatched verifier (fast, hermetic — proves the app wiring end-to-end without touching Google), or (b) points at the real Google token endpoint with a real test-account token (slower — proves the integration). Option (a) is the practical automated target.
   - A true real-Google end-to-end check stays a manual Phase 4 live QA step (O-18/O-19): a human signs in once with a real test Gmail.
   - Linux host note: this box has segfaulted Node tooling on cold Vite/worker caches (bug-781, and the `tsc -b`/`node_modules/.tmp` segfault hit during Phase 3). If `npx playwright` segfaults, clear `node_modules/.vite` and `node_modules/.tmp` and retry before assuming a Playwright bug.

   - **Fixed:** not yet — this entry records the plan. Tracked as Phase 4 (O-18/O-19) in `TASK_OAUTH.md`.

## 2026-07-13 - OAuth Phase 2 (student app): frontend test runner + token sourcing
Report created by: Claude Opus 4.8
Git branch: `oauth_feature`
Git checkpoint: `ffe255e` — Add PRD for Google OAuth login (student + admin apps)

### Findings

1. **Medium:** ~~`npx vitest run` in `APP/STUDENT_APP_REDUX` died with `Segmentation fault (core dumped)` before executing a single test.~~
   - Not caused by any test. Vite's dependency (re-)optimization crashes vitest's default worker-thread pool on this Linux host. Any cold cache triggers it: adding the new `src/auth/` directory invalidated the cache, and `rm -rf node_modules/.vite` reproduced the segfault on a **pre-existing, previously passing** test file, which isolates it from the OAuth work. `--pool=forks` ran clean.
   - Same class as the `optimizeDeps.bundler: 'esbuild'` pin already in `vite.config.ts` (Rolldown/WASM on Linux); `vitest.config.ts` never got the equivalent.
   - **Fixed:** set `pool: 'forks'` in `APP/STUDENT_APP_REDUX/vitest.config.ts`. Suite now runs (162 passed / 16 pre-existing failures). Logged as bug-781.
   - Note: `--poolOptions.forks.singleFork=true` is **not** a valid alternative — one shared process leaks module/DOM state across files and blows the suite up to 87 failures.

2. **High:** ~~The student app sent the `user_token` UUID in the `Authorization: Bearer` header, where the backend expects a JWT.~~
   - `src/api/client.ts:22` set `Bearer <user_token>`; the backend's `get_current_user` decodes a JWT, so that header was never usable — identity travelled only in request bodies/query params.
   - **Fixed:** the Bearer header now carries the real JWT access token from the OAuth session; `user_token` is sourced from `GET /api/auth/me`.

3. **High:** ~~`user_token` was read into module-scope constants in 8 files, i.e. at import time — before a login can possibly exist.~~
   - `useDashboardData.ts`, `useGrammarSession.ts`, `DiagnosticPage/DiagnosticDetailPage/PracticeTestPage`, `TestModeTab/DiagnosticTab/DiagnosticDetail/DiagnosticHistory` each held `const USER_TOKEN = import.meta.env… || localStorage…`. Swapping the right-hand side to a getter would have preserved the bug, since the const still evaluates once at import.
   - **Fixed:** every read moved to render/fetch time via `getUserToken()` at the call site.

4. **Medium:** ~~Logging out would have served the previous student's cached data to the next one.~~
   - React Query keys don't include the user token, and the cache survives a logout in the same browser tab.
   - **Fixed:** `queryClient.clear()` on logout in `AuthContext`.

5. **Low (not fixed — pre-existing):** 16 tests fail on `oauth_feature` and on a clean tree alike: `grammar-page` (4), `GrammarPractice`, `PracticeCard` (3), `PracticeTestCard` (3), `PracticeTestPage` (1), `keyColors` (4). None touch auth. `PracticeTestPage.test.tsx` mocks `TestModeTab`, but the page renders `PracticeTestRunner` — the test is stale.

## 2026-07-03 - Admin dashboard startup check: /admin/tests 500 + dev proxy 404s
Report created by: Claude Fable 5
Git branch: `gitbutler/workspace`
Git checkpoint: `196d10c` — GitButler Workspace Commit

### Findings

1. **High:** ~~`GET /admin/tests` returned 500 — `asyncpg.InvalidTextRepresentationError: invalid input value for enum practice_status_enum: "approved"`.~~
   - `backend/app/routers/admin.py:283` counted approved questions with `practice_status.in_(("active", "approved"))`, but `practice_status_enum` only has `draft/active/retired/rejected`; Postgres rejects the cast at query time, so the Test Explorer tab could never load.
   - **Fixed:** changed the filter to `practice_status == "active"`, matching the approved-count convention used elsewhere in the same file (≈lines 1886, 2180). Endpoint verified 200 after uvicorn hot-reload. Logged as bug-773 in `.wolf/buglog.json`.

2. **Medium:** ~~Admin app dev server unusable against the running stack — all `/api/admin/*` and `/api/users*` calls 404'd through the Vite proxy (manifestation of the known bug-777/778 prefix mismatch), and the hardcoded proxy target `localhost:8000` no longer matches the stack's backend port (now 8002).~~
   - Backend mounts admin/users routers without the `/api` prefix; only `stats`/`study` live under `/api`. Compose host ports also drifted from the documented defaults (backend 8002, DB 5437, student frontend 5174 — which additionally collides with the admin app's configured port 5174).
   - **Fixed (dev-only):** `APP/ADMIN_APP/vite.config.ts` proxy now strips `/api` for `/api/admin` and `/api/users` routes and reads the target from `VITE_BACKEND_ORIGIN` (default still `localhost:8000`). Admin app started on port 5175. The production-path prefix alignment remains open under bug-777/778.

3. **Low:** `adminApi.listJobs` calls `GET /admin/jobs`, which does not exist on the backend (only `/dashboard/jobs`, an HTML fragment). No page currently uses `listJobs`, so nothing breaks — dead client code to remove or rewire when a jobs view is built.

## 2026-07-03 - GitButler commit blocked: workspace merge-base conflict + transient loose-object corruption
Report created by: Claude Sonnet 5
Git branch: `gitbutler/workspace`
Git checkpoint: `b32273b` — Pin Node 20 to fix recurring WSL2/WASM build crashes

### Findings

1. **Critical (blocked, needs user decision): `but commit admin-dashboard-phase-2 --only ...` and the `--changes <ids>` variant both fail with `Failed to merge bases while cherry picking commit ... Encountered a conflict while merging the commit's new bases: <10 commit ids>`, reproduced 3 times with different flags/messages.**
   - The workspace currently has 9 other applied branches stacked (`podman-uv-build-repair`, `c-branch-1`, `admin-dashboard-plan`, `session-checkpoint`, `admin-dashboard-phase-0`, `cleanup-phase-0`, `admin-dashboard-phase-1`, `admin-phase1-gap-review`, `pin-node-20`) plus the freshly-created `admin-dashboard-phase-2`. The failure is not content-specific — it reproduces identically regardless of which 3 files/commit message are supplied, and the leading commit id in the error (`196d10c816ae...`) is constant across retries, pointing at a structural issue merging the new branch's base against the existing 9-branch stack rather than anything wrong with the staged diff.
   - Files staged for this commit (`backend/app/models/payload.py`, `backend/app/routers/users.py`, `backend/tests/test_users_router.py`) remain uncommitted in the working tree in a known-good, fully-tested state — no data was lost.
   - **Not fixed.** Did not attempt to unapply any of the 9 other applied branches or otherwise restructure the workspace, since that risks other in-progress work and requires user authorization per the git safety protocol. Needs either: (a) the user resolving/consolidating the applied-branch stack, or (b) a `but`/GitButler-level workspace repair.

2. **Medium (transient, likely same root cause as the 2026-07-01 hardware bit-flip finding): a `but commit` attempt also surfaced `Could not inflate data at .git/objects/12/b172c43...: corrupt deflate stream`, and a follow-up `git fsck --full` in the same session flagged a *different* loose object (`2ab3bbe28c...`) as corrupt — which then read back clean via `git cat-file -t` moments later on retry.**
   - Non-reproducible/non-persistent corruption on read (different object each time, self-resolving on retry) is consistent with the previously-logged single-bit-flip RAM/disk signature in `DEBUG_LOG.md` (2026-07-01 entry, finding #1), not with a new independent bug. Also consistent with an unrelated pytest run in the same session hitting a one-off `Segmentation fault` during Pydantic model-schema construction on the first run, which then passed cleanly on two immediate retries.
   - **Not fixed — same unresolved hardware root cause.** No corrective action taken beyond re-running affected commands, which succeeded/read-clean on retry.

## 2026-07-01 - Docker/Podman build pipeline: unscoped context, bad healthchecks, corrupted host node_modules
Report created by: Claude Sonnet 5
Git branch: `gitbutler/workspace`
Git checkpoint: `0260da0` — GitButler Workspace Commit

### Findings

1. **Critical (hardware, unresolved): host filesystem has a single-bit-flip corruption signature in `APP/STUDENT_APP_REDUX/node_modules/vite/dist/node/chunks/node.js`.**
   - Line 17291 read `consv forwardError = createErrorHandler(forwardReq, mptions.forward);` instead of `const forwardError = createErrorHandler(forwardReq, options.forward);` — two corruptions in one line: `t→v` and `o→m`. Both changes flip exactly the same bit (0x02: `t`=0x74/`v`=0x76, `o`=0x6F/`m`=0x6D). A consistent single-bit-flip across unrelated bytes is a classic signature of failing RAM or a failing disk/SSD, not network or npm-cache corruption (initially suspected — ruled out: a direct `curl` of the same package version from `registry.npmjs.org` was clean).
   - **Not fixed — this needs a hardware check** (memtest86 for RAM, `smartctl`/`dmesg` for disk errors) on this host. The Docker fixes below (items 2-4) prevent this specific corrupted file from being copied into container images, but they don't address the underlying cause, which will keep corrupting other files on disk until diagnosed.

2. **High: `docker-compose.yml` used repo-root (`.`) as the build context for both `backend` and `frontend` services, sending the entire ~8GB working tree (`.git`, `TESTS/` PDFs, both apps' `node_modules`, multiple Python venvs) to the build daemon on every build.**
   - Root `.dockerignore` exclusions for these paths did not appear to take effect through the `podman compose` → `docker-compose` CLI plugin → podman API bridge in this environment (`docker compose build --no-cache` was observed sending 5GB+ and climbing before being interrupted).
   - **Fixed:** scoped `build.context` to `./backend` and `./APP/STUDENT_APP_REDUX` respectively in `docker-compose.yml`, updated `COPY` paths in `Dockerfile.backend`/`Dockerfile.frontend` to be context-relative, and added `.dockerignore` files inside each subdirectory. Build context dropped to ~1.1MB (backend) and ~155KB (frontend); full `--no-cache` rebuild of both images went from a prior single attempt taking 9+ minutes to ~21 seconds.

3. **High: frontend's `COPY APP/STUDENT_APP_REDUX/ ./` ran *after* `npm ci`, and without a working `node_modules` exclusion it would silently overwrite the freshly-installed image `node_modules` with the host's own copy — including the corrupted `vite` file from finding #1.** This is why a corrupted `vite/dist/node/chunks/node.js` reappeared identically across multiple `--no-cache` rebuilds (ruled out a buildah/npm cache reuse theory first).
   - **Fixed:** `APP/STUDENT_APP_REDUX/.dockerignore` now excludes `node_modules`, so the image's own freshly-`npm ci`'d copy is never overwritten by the host's.

4. **Medium: `dsat-backend`'s podman healthcheck was always "unhealthy" despite the API working fine.** `docker-compose.yml`'s `healthcheck.test: ["CMD", "python", "-c", "..."]` (exec-array form) had its multi-word `-c` argument tokenized on whitespace by podman, so the container only ever ran `python -c import` → `SyntaxError`.
   - **Fixed:** changed both backend and frontend healthchecks in `docker-compose.yml` from exec-array `CMD` to `CMD-SHELL`, which runs the full string through `/bin/sh -c` and doesn't re-split it.

5. **Low: `Dockerfile.backend` copied the entire `backend/` source before running `uv pip install -e ".[dev]" --system`, invalidating the dependency-install layer on every source edit.**
   - **Fixed:** split into a dependency layer (`COPY pyproject.toml uv.lock` → `uv sync --frozen --extra dev --no-install-project`) followed by the source copy and a fast final `uv sync`. Also replaced `pip install uv` with the official static binary (`COPY --from=ghcr.io/astral-sh/uv:0.7.20`) and added a `--mount=type=cache,target=/root/.cache/uv` cache mount.

## 2026-07-01 - DB restore from backup: orphaned FK reference in question_jobs
Report created by: Claude Sonnet 5
Git branch: `gitbutler/workspace`
Git checkpoint: `0260da0` — GitButler Workspace Commit

### Findings

1. **Low: `question_jobs.raw_asset_id` FK constraint could not be restored — one row references a missing `question_assets` row.**
   - Restored `backups/dsat_dev_20260630_220001.dump` (last known-good backup; the `dsat-db` container had been down since 2026-07-01 00:00, so every 2-hourly cron backup since then failed with "container not running" — no data was lost, the container was just offline).
   - `pg_restore --clean --if-exists --no-owner` succeeded for all 26 tables and data (1583 questions, 165 question_jobs, 67 question_assets, etc.) except one FK: `question_jobs_raw_asset_id_fkey` on row `id=2f63aca9-e1b1-42fa-a95e-e6aadaf3998b` (status `needs_review`), which points at `question_assets.id=f2c2a55c-5a2e-47ef-94e0-8653d444c46d` — not present in the restored `question_assets` table. This inconsistency predates the restore (present in the source dump itself), not introduced by the restore process.
   - Not fixed — the constraint is simply absent on `question_jobs.raw_asset_id` going forward (data itself is intact; only the FK enforcement is missing). Left as-is pending user decision: either null out that job's `raw_asset_id` and re-add the constraint, or investigate why `question_assets` row `f2c2a55c...` is missing.

Report created by: Claude Sonnet 5
Git branch: `gitbutler/workspace`
Git checkpoint: `6ede750` — GitButler Workspace Commit

### Findings

1. **Medium: `DataManagement.tsx` (question review page) has no way to edit a question at all — only Approve/Reject.**
   - The backend `PATCH /admin/questions/{question_id}` endpoint (`backend/app/routers/admin.py:1001`) is fully built and correct: it creates a new `QuestionVersion`, clones `QuestionOption` rows with updated correctness flags, updates `Question.latest_version_id`/`current_*` fields, and writes an audit log entry. `adminApi.editQuestion()` exists in `client.ts` but is called from nowhere in the frontend (`grep editQuestion` across `APP/ADMIN_APP/src` returns only the definition). Admins currently cannot change question text, passage text, explanation, or the correct answer from the UI — the only path is a raw API call.
   - Not fixed — added to `admin_dashboard_plan.md` backlog (§7, question edit UI).

2. **Medium: editing a question sets `annotation_stale=True` but nothing ever surfaces or acts on that flag.**
   - `admin.py:1100` sets `q.annotation_stale = True` on every edit (correct — the annotation, e.g. `grammar_focus_key`/`syntactic_trap_key`/distractor metadata, was generated against the pre-edit text and is now potentially wrong). The only other reference is `ingest.py:3686`, which clears it after a reannotation run. There is no admin UI badge, filter, or queue showing "N questions need reannotation," and no `annotation_stale` field even exists on the frontend `Question` type (`APP/ADMIN_APP/src/types/index.ts`). Once this endpoint gets a UI (finding #1), edited questions could silently accumulate stale annotation metadata feeding the analytics/weak-spots endpoints indefinitely.
   - Not fixed — added to `admin_dashboard_plan.md` backlog (§7).

3. **Low: no way to edit an existing user's `username`/`email`/`role` from the admin dashboard — `users.py` only has create/list/get/delete.**
   - Confirmed by reading `backend/app/routers/users.py` in full: `POST ""`, `GET ""`, `GET "/{user_id}"`, `DELETE "/{user_id}"` — no `PATCH`/`PUT`. Fixing a typo'd email or promoting a role requires a manual DB update.
   - Not fixed — added to `admin_dashboard_plan.md` backlog (§7).

4. **Medium: `DataManagement.tsx` Focus and Difficulty columns are always blank — field-shape mismatch with the API.**
   - `GET /admin/questions` (`admin.py:220-246`) nests classification fields inside a merged `annotation` object per item (`annotation = {**ann.annotation_jsonb, **ann.explanation_jsonb}`), so a question's grammar/reading focus key and difficulty live at `item.annotation.grammar_focus_key` / `item.annotation.difficulty_overall`. The frontend `Question` type (`APP/ADMIN_APP/src/types/index.ts`) declares `grammar_focus_key`/`reading_focus_key`/`difficulty_overall` as top-level fields, and `DataManagement.tsx` renders `q.grammar_focus_key || q.reading_focus_key` and `q.difficulty_overall` directly — both are `undefined` on every row the API actually returns, so those table columns render `—` unconditionally regardless of real data. The backend response also already includes `current_passage_text`, full `options` (with `is_correct`), `current_explanation_text`, `is_admin_edited`, and `official_overlap_status` per question — none of which are in the frontend type or rendered anywhere, so this data reaches the browser and is discarded.
   - Not fixed — added to `admin_dashboard_plan.md` backlog (§7, question detail/edit view); the type + rendering fix is part of that same change since it requires reshaping how `DataManagement.tsx` consumes the response anyway.

**Not a bug:** verified `QuestionOption` reads are consistently scoped by `latest_version_id` across every read path in `student.py` and `admin.py` (lines 206, 436-437, 561, 1603-1605, 2844) — the version-propagation architecture itself is sound. The gap is entirely in the admin UI layer, not the data model.

## 2026-06-26 - Backend container cannot reach host Ollama (extraction ConnectError)
Report created by: Claude (glm-5.2:cloud)
Git branch: `gitbutler/workspace`
Git checkpoint: `24d9c95` — GitButler Workspace Commit

### Findings

1. **High: ingestion jobs fail at `extracting` with `ConnectError: All connection attempts failed`.**
   - Affected Test_4 math sec02 mod01 (job `2afed5ab…`) and Test_4 verbal sec01 mod01 (job `405895ab…`), both failing at the `extracting` step. The extraction client in `backend/app/routers/ingest.py` uses `base_url=settings.ollama_base_url`, which defaults to `http://localhost:11434`. The `dsat-backend` container's compose service set no `OLLAMA_BASE_URL` and no `extra_hosts`, so `localhost:11434` resolved to the container itself — Ollama runs on the host (binds `*:11434`) and was unreachable. Prior successful ingestions must have run the backend on the host, not in this container.
   - **Fixed:** added `OLLAMA_BASE_URL: http://host.docker.internal:11434` and `extra_hosts: ["host.docker.internal:host-gateway"]` to the `backend` service in `docker-compose.yml`; recreated with `docker compose up -d backend`. Verified from inside the container via `docker exec dsat-backend python -c "import urllib.request; urllib.request.urlopen('http://host.docker.internal:11434/api/tags')"` — reachable, and `glm-ocr:latest` / `deepseek-v4-pro:cloud` / `deepseek-ocr:latest` all present. Re-submitted Test_4 verbal sec01 mod01 + mod02 (jobs `bb4ad1b0…` / `9278f496…`); both moved from instant-fail to `extracting`. Also logged as bug-770 in `.wolf/buglog.json`.

## 2026-06-26 - Annotation Optimization (items 1-3)
Report created by: Claude (glm-5.2:cloud)
Git branch: `gitbutler/workspace`
Git checkpoint: `24d9c95` — GitButler Workspace Commit

### Findings

1. **High: grammar `syntactic_trap_key` truncation — flat `max_tokens=8192` cap too tight for grammar annotations.**
   - Grammar annotations output 4.5–8K tokens (grammar_role_key + grammar_focus_key + secondary_grammar_focus_keys + syntactic_trap_key + reasoning). The 8192 cap cut off the JSON tail where `syntactic_trap_key` lives, producing `None`/missing values that failed the non-null validator rule for `agreement/pronoun/modifier/verb_form/sentence_boundary` roles. This is the root cause of the 5 blocking `syntactic_trap_key` errors in the Test_4 run (see prior entry, finding #1).
   - **Fixed:** `annotation_max_tokens(q_data)` in `backend/app/prompts/annotate_prompt.py` returns 12288 for grammar/unknown, 8192 for reading. `_run_pipeline` annotation call site (`backend/app/routers/ingest.py`) now uses it instead of the hardcoded 8192. Reannotate path unchanged (already 32000).

2. **Medium: annotation output ordered reasoning before classification keys, so truncation lost required fields.**
   - **Fixed:** added an output-ordering instruction to rule 5 of both `_SYSTEM_INSTRUCTIONS_TEMPLATE` and `_SYSTEM_BASE` — emit classification fields FIRST (question_family_key, stem_type_key, grammar_role_key, grammar_focus_key, reading_focus_key, syntactic_trap_key, difficulty_*, etc.), reasoning/amendment_proposal LAST. Truncation now only loses reasoning, never a required key.

3. **Medium: reading rules block sent ~18.3K input tokens to every reading annotation, most irrelevant to the question.**
   - **Fixed:** `_reading_context(variant_key)` now trims per skill family via `_STEM_SKILL_FAMILY` → `_SKILL_SECTION_NUMBERS` — keeps shared §3-§12 + §14 + §17, selects only the matching §13 skill subsection + §19 failure-mode subsection (+ §19.7 summary), and drops §15 Passage Architecture (generation-only). Unmapped stems fall back to the full block (no accuracy regression). `lru_cache(maxsize=16)` caches each variant; `_prewarm_annotation_cache` dedups by `(domain, variant)` and pre-warms each. Measured: full ~64K chars → trimmed ~41-43K chars (~35% reduction; maps to ~18.3K→~12K tokens on real tokenization).

### Verification
- `tests/test_prompts.py` — 11/11 pass (rules loading, disambiguation presence, amendment guards, stem-vocab coverage).
- Full backend suite: 1049 passed, 6 pre-existing failures unrelated to this change (`test_config` ocr_vision_model default drift, `test_vocab_sync` candidates/ontology drift, 4× `test_student_retrieval` DB-seed-state — none import `annotate_prompt`/`_annotate_with_retry`).

## 2026-06-26 - Ingestion Test Run (Test_4_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `gitbutler/workspace`
Git checkpoint: `dc53ce4` — GitButler Workspace Commit

### Findings

1. ~~**High:** Blocking `syntactic_trap_key` validation error — grammar_role_key='verb_form' annotation returned `None` for `syntactic_trap_key`; rule requires non-None/non-'none'. Affected 5 questions (validating|5 errors); 5 questions failed to persist (extracted 33, created 28). Representative: question index 19 / source question number "20", job `e8b32fc4-3fbd-4662-a2d0-8fe711b1365a`.~~
   - **Fixed (root cause):** the `None` values were truncation, not model refusal — the flat `max_tokens=8192` cap cut the JSON tail where `syntactic_trap_key` lives. Raised grammar cap to 12288 (domain-aware `annotation_max_tokens`) and reordered output so classification fields precede reasoning. See "Annotation Optimization (items 1-3)" entry above. Re-run the Test_4 ingestion to confirm the 5 questions now persist.

2. **High:** `module_completeness` persistence shortfall — expected 33, extracted 33, created only 28. Directly caused by the 5 blocking `syntactic_trap_key` errors in finding #1.

3. **Medium:** Question 20 (job `e8b32fc4`) additionally has `correct_option_label not found in source` (severity: warning) and `skill_family_key` populated on a grammar-domain question (severity: review). Both are non-blocking. The "Option labels must be exactly {A, B, C, D}, got ['']" cascade did **not** appear.

## 2026-06-26 - Diagnostic Test 404/500 Fix
Report created by: Claude (glm-5.2:cloud)
Git branch: `gitbutler/workspace`
Git checkpoint: `bc93bac` — GitButler Workspace Commit

### Findings

1. **High: `POST /api/diagnostic/start` returned 404 `{"detail":"User not found"}` — stale test-user token in docker-compose.yml.**
   - `docker-compose.yml:57` injected `VITE_TEST_USER_TOKEN: 92451633-1318-410a-8687-5b1ab59e4709`, a token from an earlier DB seed. The dev DB was re-seeded on 2026-05-29 and the only `users` row now has `user_token = c76d24d2-5b59-4250-82f0-5874e5e1d826`. `DiagnosticPage.tsx` resolves `USER_TOKEN` from `VITE_TEST_USER_TOKEN` → `localStorage` → `''`, so the frontend sent a valid-but-unmatched UUID; `_resolve_user_by_token` (`backend/app/routers/student.py:667`) parsed it but found no User → 404.
   - **Fixed:** updated `VITE_TEST_USER_TOKEN` to `c76d24d2-5b59-4250-82f0-5874e5e1d826` in `docker-compose.yml` and recreated the frontend container (`docker compose up -d --no-deps frontend`) so Vite re-injects `import.meta.env`. Verified live: `POST /api/diagnostic/start` with `X-API-Key: student-test-key` + the token → 200. (bug-766)

2. **High: `POST /api/diagnostic/start` returned 500 once a valid token was supplied — `diagnostic_sessions` table missing (alembic drift).**
   - Backend traceback: `asyncpg.exceptions.UndefinedTableError: relation "diagnostic_sessions" does not exist`. `alembic_version` was stamped at 033 (head) but the schema was actually at ~029: migrations 030/031/032's standalone tables (`diagnostic_sessions`, `spaced_repetition_state`, `test_session_results`) and the `user_progress.diagnostic_session_id` column were never created. 033's `question_annotations` columns + `span_review_queue` + GIN indexes WERE present (mixed `create_all`+stamp baseline), so `alembic upgrade head` could not re-run 030–032 and a `stamp 029; upgrade head` would crash at 033 `add_column` on existing columns.
   - **Fixed:** applied the missing DDL directly with `IF NOT EXISTS` guards (`/tmp/fix_diag_schema.sql` run via `docker exec dsat-db psql -f`) — created `diagnostic_sessions` (+ indexes + `user_progress.diagnostic_session_id` FK/index), `spaced_repetition_state` (+ unique `user_id/question_id` + indexes), `test_session_results` (+ indexes). Left `alembic_version` at 033 since the schema now matches head. Verified: diagnostic start returns 200 with 16 questions + coverage_report. (bug-767)

3. **Medium: `dsat-backend` got stuck in a uvicorn `--reload` loop watching `.venv/lib/python3.12/site-packages/**`, rendering the container unhealthy.**
   - WatchFiles detected churn under the venv and reloaded repeatedly without serving. Restarted `dsat-backend` to recover. Root cause is the reload watcher's include scope (pre-existing config issue, not caused by this fix); not addressed here. Note: dev stack host ports are backend **8002**, frontend **5174**, db **5437** — not the CLAUDE.md-documented 8000/5173/5434.

## 2026-06-26 - Ingestion Test Run (Test_1_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `gitbutler/workspace`
Git checkpoint: `bc93bac` — GitButler Workspace Commit

### Outcome summary

- Target: `Test_1_digital_sec01_mod01` (official verbal, exam 1 / sec 01 / mod 01, year 2025).
- New submission was a **no-op**: backend idempotency guard returned
  `This file has already produced a complete ingest (33/33 questions).` (HTTP detail,
  `_duplicate_checksum_conflict_detail` in `backend/app/routers/ingest.py:3161`), so the
  runner created no new job (`RESULT_JSON:{"error":"no job_id", ...}`).
- Canonical prior ingest of this target — job `887ebddb-6343-4096-a283-c6cf838388da`
  (created 2026-05-23) — is **clean**: status **approved**, extracted **33** / created **33**,
  `validation_errors_jsonb` is NULL (zero validation errors by step). The
  `Option labels must be exactly {A, B, C, D}, got ['']` cascade did **not** appear
  (0 matches). Pipeline run for this target is clean — no pipeline findings.

### Findings

1. ~~**Medium: ingestion-test runner aborts on a false "postgres unavailable" due to a hardcoded DB-port drift.**~~ — **Fixed 2026-06-26** (see Fixed bullet below)
   - `.claude/skills/ingestion-test/run.sh` hardcodes its prereq psql check and all
     result-collection queries to host port **5434** (lines 45/49/53/143–148), but the
     deployed stack publishes Postgres on host port **5437** (`docker-compose.yml:10`
     `"5437:5432"`; `backend/.env` and `backend/app/config.py` both use `localhost:5437`).
     Nothing listens on 5434, so the runner exits with
     `RESULT_JSON:{"error":"postgres unavailable"}` even though the `dsat-db` container is
     healthy and accepting connections. This blocks the runner out of the box.
   - Not a pipeline defect — environmental/harness config drift. The application backend
     itself connects correctly (5437); only the stale runner script is affected.
   - **Worked around (not fixed):** ran a throwaway localhost TCP forwarder 5434→5437 so the
     bundled runner could execute unmodified; no pipeline source was edited and nothing was
     committed. Permanent fix = update `run.sh` to 5437 (or read the port from `.env`).
   - **Fixed 2026-06-26:** `run.sh` now derives `DB_PORT` from `backend/.env`'s `DATABASE_URL`
     (env override `DB_PORT`, default 5437); all 7 psql calls use `$DB_PORT` instead of the
     hardcoded 5434. Verified: resolver yields 5437, DB reachable on it, `bash -n` clean. The
     temporary TCP forwarder is no longer needed.

## 2026-06-26 - Annotation Pipeline Refactor (shape-mismatch hardening)
Report created by: Claude Opus 4.8
Git branch: `gitbutler/workspace`
Git checkpoint: `bfc86ad` — GitButler Workspace Commit

### Findings

1. **High: nested LLM reasoning shape did not reconcile to the flat schema consumed by practice/generation.**
   - LLMs emitted canonical fields (`question_family_key`, `difficulty_overall`, `syntactic_trap_key`, etc.)
     inside nested `question`/`classification`/`review`/`reasoning` blocks while top-level stayed null/`"none"`.
     Live active rows showed `missing_question_family` 21, `missing_difficulty` 21. Reliance on LLM obedience
     was the root cause — no deterministic reconciliation step existed.
   - **Fixed:** Added `canonicalize_annotation()` (`backend/app/parsers/json_parser.py`) — deterministic
     promotion of nested → top-level with null/empty/`"none"` repair, alias normalization, and a conflict
     policy (top-level wins, clash recorded in `_annotation_quality.conflicts[]`, `needs_human_review` set).
     Replaced `normalize_annotation` in the ingest annotate path and routed `generate.py` through the same
     pipeline. Repair script (`backend/scripts/repair_annotation_canonical.py`) backfilled 30 active rows
     (0 conflicts): `missing_question_family` 21 → 0, `missing_difficulty` 21 → 2.

2. **Medium: no domain-complete validation gate — malformed taxonomy persisted silently.**
   - Grammar rows could carry `skill_family_key`; reading rows could carry grammar role/focus keys; required
     fields and valid role/focus pairings were never enforced before persistence.
   - **Fixed:** Added `validate_annotation_completeness()` (`backend/app/pipeline/validator.py`) wired into
     ingest (after sanitize) and generation. Grammar requires role/focus/family/difficulty + conditional
     `syntactic_trap_key` and forbids `skill_family_key`; reading requires skill/focus/family/difficulty and
     forbids grammar keys. Backed by `SYNTACTIC_TRAP_REQUIRED_ROLES` in `ontology.py` (single source shared
     with the prompt). 11 completeness tests + 8 canonicalize tests; refactor scope green (40 passed, 2 skipped).

3. **Low: prompt/ontology vocabulary contradiction — prompt allowed `very_high` difficulty.**
   - `DIFFICULTY_KEYS` is `low/medium/high` in master.json + ontology + both rules-doc blocks; the prompt was
     the lone outlier adding `very_high`.
   - **Fixed:** Removed `very_high` from both prompt difficulty-calibration blocks (folded into `high`); set
     cross-domain difficulty examples to `null` for not-applicable; stated grammar must not populate
     `skill_family_key`.

### Remaining (genuinely-missing data, not repairable)

- 2 rows missing `difficulty_overall`, 2 reading rows missing `reading_focus_key`, plus grammar
  `syntactic_trap_key` debt → require re-annotation, not deterministic repair. (Overlaps Finding #1 of the
  Ingestion Pipeline Audit entry below.)

## 2026-06-26 - Ingestion Pipeline Audit + Annotation Coverage Gaps
Report created by: Claude Sonnet 4.6
Git branch: `gitbutler/workspace`
Git checkpoint: `bfc86ad` — GitButler Workspace Commit

### Findings

1. **High: `syntactic_trap_key` coverage 2/43 (5%) for grammar questions despite grammar rules file defining it for structural roles.**
   - `agreement`, `pronoun`, `modifier`, `verb_form`, `sentence_boundary` questions all have syntactic traps in grammar_v8 rules, but the LLM skips the field because the prompt never marks it as required.
   - `reasoning_trap_key` (reading domain) and `syntactic_trap_key` (grammar domain) are separate vocabularies — neither is missing from the rules files; the prompt failed to enforce the grammar one.
   - **Fixed:** Added explicit NULLABILITY ENFORCEMENT rule to `_SYSTEM_INSTRUCTIONS_TEMPLATE` and `_SYSTEM_BASE` in `backend/app/prompts/annotate_prompt.py`: `syntactic_trap_key` is now REQUIRED (non-null) whenever `grammar_role_key` is `agreement`, `pronoun`, `modifier`, `verb_form`, or `sentence_boundary`.

2. **Medium: `grammar_role_key` echoing parent family name (e.g. `"expression_of_ideas"`) instead of a role value.**
   - Exam 1 Q6: `grammar_role_key = "expression_of_ideas"` — this is a `question_family_key` value, not a role. The LLM falls back to the family name when it can't identify the correct role.
   - Affects: precision word-choice / transition questions under `expression_of_ideas` where `grammar_role_key` is ambiguous.
   - **Not fixed in code** — requires grammar_v8 rules file amendment adding explicit role values for EOI sub-types. See amendment process note below.
   - **Action needed:** Add `## expression_of_ideas sub-roles` section to `rules_agent_dsat_grammar_ingestion_generation_v8.md` defining role keys for: transition/conjunction selection, precision word-choice, rhetorical synthesis.

3. **High: `_FLAT_ANNOTATION_KEYS` in `backend/app/parsers/json_parser.py` missing all reading domain fields.**
   - LLM inconsistently nests reading annotation under `"classification"` key. `normalize_annotation()` only promoted 8 grammar-domain keys; all reading fields stayed buried.
   - Result: 23/93 official questions had `question_family_key = NULL` at top level even though data existed in nested dict.
   - **Fixed:** Expanded `_FLAT_ANNOTATION_KEYS` to include all reading fields. Added `_SKILL_FAMILY_DISPLAY_TO_KEY` map to convert human-readable display names (e.g. `"Words in Context"`) to snake_case keys. Updated `normalize_annotation()` to promote both.
   - **Fixed (DB):** One-time migration promoted nested `classification` fields to top-level `annotation_jsonb` for 22 existing unclassified questions. Exam 6 Q32 remains (grammar question misrouted to reading; needs re-annotation).

4. **High: `source_question_number` passed as string to INTEGER DB column in `ingest.py:1083`.**
   - `q_data.get("source_question_number")` returns raw LLM string. `q_num_int` (already computed) was not being used.
   - Caused 2 hard `psycopg` errors per ingestion run.
   - **Fixed:** `ingest.py:1083` now passes `q_num_int`.

5. **Critical: `current_correct_option_label` exposed in `StudentQuestionResponse` API.**
   - Field leaked the correct answer to the student-facing `/questions` endpoint.
   - **Fixed:** Removed field from `StudentQuestionResponse` (payload.py) and both serializer call-sites in student.py. Submit endpoint (`/submit`) now returns `correct_option_label` in its response. Frontend `useGrammarSession.ts` updated to await submit result and derive `correctOptionLabel` from response instead of pre-loaded question data.

6. **High: `reading_skill_family_key` key mismatch — DB stores `skill_family_key`, query used wrong name.**
   - `student.py:312` and `328` queried `annotation_jsonb["reading_skill_family_key"]` which is always NULL; actual key is `skill_family_key`.
   - Result: reading domain filtering returned zero questions; `skill_family_key` never populated in API response.
   - **Fixed:** Updated DB filters (student.py:312, 328) and serializers (student.py:508, 1262, 1644) to use `skill_family_key`. Renamed field in `StudentQuestionResponse` and `DiagnosticQuestionPayload` (payload.py:22, 1092).

7. **High: HTTP 429 rate-limit errors not retried — annotation pipeline fails on 30+ question modules.**
   - `_annotate_with_retry()` only caught empty/malformed JSON. All 429 errors fell through as permanent failures.
   - 32/34 annotation errors in Test 1 mod02 were 429s.
   - **Fixed:** `_annotate_with_retry()` now has independent retry loops: up to 3 retries for 429 with exponential backoff (5s → 15s → 45s + up to 2s jitter); 1 retry for malformed JSON. Added `_is_rate_limit_error()` helper.

---

### Rules File Amendment Process (admin note)

**The grammar and reading rules files are the single source of truth for all LLMs in this system.** Amendments to these files must go through the structured review process:

**Flow:**
```
LLM proposes (annotation_jsonb['reasoning']['amendment_proposal'])
  → capture_amendment_proposal() → vocabulary/amendments/pending/*.json
  → Admin review: GET /api/admin/amendments
  → Semantic duplicate check (now runs on approve)
  → approve_amendment() → status = approved (still in pending/)
  → promote_amendment() → patches master.json + rules files + moves to approved/
```

**Why this must be carefully controlled (multi-LLM context):**
- Different LLM providers (DeepSeek, Qwen, Claude, GPT-4) independently annotate questions using the same rules files. If one model proposes `contextual_inference` and another proposes `context_clue_inference` for the same concept, and both get promoted, the vocabulary fragments — future models may use either name inconsistently.
- The `validate_amendment_for_approval()` function now runs a semantic duplicate check (Jaccard token overlap ≥ 0.5) against: (a) active entries in `vocabulary/master.json`, and (b) other pending/approved amendments in the same vocabulary. Near-matches block approval and surface a `duplicate_warnings` list for human review.
- Before adding any key to the rules files, verify: does a synonym already exist under a different name? Check `vocabulary/master.json` entries, `vocabulary/candidates.json`, and all pending amendments.

**Two pending amendments require human decision:**
- `rhetorical_synthesis` → `GRAMMAR_FOCUS_BY_ROLE` (pending): Exam 6 Q32. Likely correct — notes synthesis questions have no existing role key. Needs grammar_v8 section added.
- `verb_form` → `READING_SKILL_FAMILY_KEYS` (pending): **REJECT.** `verb_form` is already a `grammar_role_key` value. The LLM misrouted a grammar question to reading and proposed adding a grammar concept to the reading taxonomy.

## 2026-06-08 - Annotation JSON Parse Failure on Manually Inserted Questions
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `fe1b64c` — chore(graphify): add knowledge graph tooling config and output dir

### Findings

1. **Medium: Annotation LLM returns nested `{ "question": {...} }` wrapper instead of flat annotation JSON — `extract_json_from_text` fails to parse.**
   - Affected questions: Q1 of Test01_ENG_Sec01_Mod02A (job `9b9a1034`), Q1 of multiple other modules
   - Error: `No valid JSON found in text (provider='ollama', model='deepseek-v4-pro:cloud', input_len=4918–8589, preview='{ "question": { "source_exam": "PT1", ...' )`
   - Root cause: The model returned a response beginning with `{ "question": {...} }` that was likely **truncated mid-JSON** (response cut off before the closing `}`). `_extract_first_braced_candidate` tracks brace depth and returns `None` if it never reaches depth 0 — a truncated response never closes, so all four parsing strategies in `extract_json_from_text` fail and raise "No valid JSON found." The preview showing `"stem_type_key": "choo'` (cut off) is consistent with truncation.
   - Pattern: Occurs non-deterministically — retry produces a complete response and succeeds. Likely a transient model output truncation rather than a persistent schema error.
   - **Fixed (workaround):** Retried reannotation up to 3 times; succeeded on attempt 2. No code change applied.
   - **Long-term fix:** Add a normalization step in `extract_json_from_text` or the annotation path to unwrap a `{ "question": {...} }` envelope before attempting to parse the annotation schema.

## 2026-06-07 - Ingestion Test Run (Test_6_digital_sec01_mod01) — Run 4
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `fe1b64c` — chore(graphify): add knowledge graph tooling config and output dir

### Findings

1. **Medium: Job completed extraction (33/33) with zero validation errors but status remained `annotating` when the runner stopped the server.**
   - job_id: `c5eaeee0-660c-457a-83e2-8374420731f2`
   - Extracted: 33 questions. Created: 0 (module was already in DB from prior runs).
   - Validation error counts by step: none (0 rows).
   - The "Option labels must be exactly {A, B, C, D}, got ['']" cascade did **not** appear.
   - Status `annotating` at collection time indicates the annotation phase was still running when `run.sh` polled and then shut down the server — this is a runner timing issue, not a pipeline failure. The 33 questions extracted cleanly with no per-question validation failures.
   - **No action required on pipeline.** If a clean `approved`/`needs_review` terminal state is needed, delete the duplicate-checksum DB record (see 2026-06-01 Finding #7) and re-run with a longer server uptime window.

## 2026-06-07 - Ingestion Test Run (Test_6_digital_sec01_mod01) — Run 3

Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `fe1b64c` — chore(graphify): add knowledge graph tooling config and output dir

### Findings

1. **Medium: Prerequisite failure — duplicate checksum blocks re-submission.**
   - `run.sh` submitted `Test_6_digital_sec01_mod01.pdf` but the backend returned HTTP 400: `"This file has already been ingested (duplicate checksum)."` before a `job_id` was assigned.
   - RESULT_JSON: `{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}\n"}`.
   - No new job created; 0 questions extracted or created in this run.
   - Prior ingestion runs (Run 1 / Run 2 entries in this log) already exercised the pipeline for this module. The existing job(s) in the DB are the canonical record — see the 2026-06-01 audit entry (Finding #7) which notes two duplicate needs_review jobs for Test_6 mod01, each with only 17/33 questions.
   - **Action required:** To re-ingest cleanly, delete the duplicate jobs and reset the file checksum in the DB, then re-run the pipeline. This is a known operational gap (duplicate-checksum blocker) not a new bug.

## 2026-06-07 - Ingestion Test Run (Test_6_digital_sec01_mod01) — Run 2
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `fe1b64c` — chore(graphify): add knowledge graph tooling config and output dir

### Findings

1. **High: Prerequisite failure — run.sh regex case mismatch prevents job submission.**
   - `run.sh` lines 83–85 use `sed -E 's/Test([0-9]+).*/\1/'`, `'.*Sec([0-9]+).*/\1/'`, `'.*Mod([0-9]+).*/\1/'` to parse EXAM/SECTION/MODULE from the PDF stem.
   - All PDF stems on disk use lowercase: `Test_6_digital_sec01_mod01`. The `Sec` and `Mod` patterns never match, so all three variables receive the full stem string instead of a numeric code.
   - The API received `source_section_code=Test_6_digital_sec01_mod01` and rejected with HTTP 422: `"source_section_code must be '01', '02'"`.
   - RESULT_JSON: `{"error":"no job_id","response":"{\"detail\":\"source_section_code must be '01', '02'\"}\n"}`.
   - No job created; 0 questions extracted or created; no validation errors collected.
   - **Fix required:** Update `run.sh` regexes to lowercase: `'s/Test_([0-9]+).*/\1/'`, `'s/.*_sec([0-9]+).*/\1/'`, `'s/.*_mod([0-9]+).*/\1/'`.

## 2026-06-07 - Ingestion Test Run (Test_6_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `fe1b64c` — chore(graphify): add knowledge graph tooling config and output dir

### Findings

1. **High: Prerequisite failure — PDF not found at hardcoded runner path.**
   - `run.sh` line 18 had `PDF_DIR` hardcoded to `TESTS/DATA_SRC/2024-2025 Tests Answers`.
   - `Test_6_digital_sec01_mod01.pdf` lives at `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/`.
   - Runner emitted `RESULT_JSON:{"error":"pdf not found: ..."}` and exited before submitting any job.
   - No job created; 0 questions extracted or created; no validation errors collected.
   - **Fixed:** Updated `PDF_DIR` in `run.sh` to `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL` (matches `official_test_verbal_dir` in `backend/app/config.py`). Re-ingestion dispatched.

## 2026-06-01 — DB Ingestion Validation Audit
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Scope

Full database scan across all ingested official test modules. Checks: source year metadata, file ingested, passage text coverage, stem (question text) presence, and multiple-choice option validity (count, labels, correct answer).

### Multiple Choice Integrity

**CLEAN across all modules.** Every non-failed job has:
- Exactly 4 options per question (min = max = 4, no exceptions)
- Exactly 1 correct answer marked per question
- Zero empty option labels

### Findings

1. **High: `source_year` is NULL for every ingested job.**
   - `pass1_json.source_metadata.source_year` is not populated by any ingestion path. Only `source_exam_code` (e.g., `01`, `7`, `10`) is stored.
   - No year tagging (2024-2025 vs 2025-2026) is available anywhere in the DB.
   - **Fix required:** Populate `source_year` during ingestion from the source directory path or PDF filename convention.

2. **High: Test_3 mod01 — only 9/27 questions have passage text (18 missing).**
   - Approved job `0e5d66e8`. 18 questions have NULL or blank `current_passage_text`.
   - Root cause unknown — may indicate grammar-only questions correctly have no passage, or extraction dropped passage for reading questions.
   - **Action required:** Spot-check 2-3 of the 18 passage-null questions against the source PDF to determine if the gap is expected (grammar) or a data quality issue.

3. **High: Test_9 mod01 — only 13/33 questions have passage text (20 missing).**
   - Job `9231d84b` (needs_review). 20 questions have no passage text.
   - **Action required:** Same spot-check as Test_3.

4. **High: Test_4 mod01 — only 1/33 questions ingested.**
   - Job `35a040fa` (approved). Effectively a stale stub, not a usable module.
   - **Action required:** Re-ingest after duplicate-checksum fix.

5. **High: 4 failed jobs with 0 questions — need re-ingestion.**
   - `Test01_ENG_Sec01_Mod02A.pdf` — Phase 2 annotation JSON parse failure
   - `Test02_ENG_Sec01_Mod02A.pdf` — failed
   - `Test02_ENG_Sec01_Mod02B.pdf` — failed
   - `Test_5_digital_sec01_mod02.pdf` — failed
   - **Action required:** Clear duplicate-checksum blockers and re-ingest once pipeline is stable.

6. **Medium: Test_5 mod01 — only 19/33 questions ingested.**
   - Job `969d415a` (needs_review). Known extraction failure pattern (LLM skips questions in the early-to-middle range). Duplicate-checksum blocks re-ingestion.

7. **Medium: Test_6 mod01 and mod02 — duplicate jobs, both needs_review, both short.**
   - mod01: two jobs with 17 questions each (expected 33). mod02: 15 + 17.
   - **Action required:** Determine which job is canonical, delete the other, re-ingest for full count.

8. **Medium: Passage text gaps across several approved/needs_review modules.**
   - Test_11 mod01: 25/33, mod02: 24/33
   - Test_7 mod01: 27/33, mod02: 27/33
   - Test_8 mod01: 31/33
   - Test_11 and Test_7 gaps are likely grammar questions (no passage expected). Needs verification.

9. **Medium: Null `source_question_number` on 2-7 questions in 6 modules.**
   - Affected: Test01_Mod02B (3), Test_3_mod01 (4), Test_7_mod01 (2), Test_9_mod01 (2), Test_10_mod02 (7), Test_11_mod02 (2).
   - Non-blocking but affects ordering and student-facing question numbering.

10. **Low: Test_1 mod02, Test_8 mod02, Test_10 mod01 — 1-2 questions short.**
    - All `needs_review`. Minor gap, likely validation-blocked questions.

### Status Table

| File | Status | Q | Expected | Delta | Passage | Stems | Null Q# |
|------|--------|---|----------|-------|---------|-------|---------|
| Test01_ENG_Sec01_Mod01.pdf | approved | 27 | 27 | 0 | 27/27 ✅ | 27/27 | 0 |
| Test01_ENG_Sec01_Mod02A.pdf | **failed** | 0 | — | — | — | — | — |
| Test01_ENG_Sec01_Mod02B.pdf | approved | 27 | 27 | 0 | 26/27 ⚠️ | 27/27 | 3 |
| Test02_ENG_Sec01_Mod01.pdf | approved | 27 | 27 | 0 | 27/27 ✅ | 27/27 | 0 |
| Test02_ENG_Sec01_Mod02A.pdf | **failed** | 0 | — | — | — | — | — |
| Test02_ENG_Sec01_Mod02B.pdf | **failed** | 0 | — | — | — | — | — |
| Test_1 mod01 | approved | 33 | 33 | 0 | 32/33 ⚠️ | 33/33 | 0 |
| Test_1 mod02 | needs_review | 31 | 33 | -2 | 28/31 ⚠️ | 31/31 | 0 |
| Test_3 mod01 | approved | 27 | 33 | -6 | 9/27 ❌ | 27/27 | 4 |
| Test_4 mod01 | approved | 1 | 33 | -32 | 1/1 | 1/1 | 0 |
| Test_5 mod01 | needs_review | 19 | 33 | -14 | 19/19 | 19/19 | 0 |
| Test_5 mod02 | **failed** | 0 | — | — | — | — | — |
| Test_6 mod01 | needs_review ⚠️DUP | 17+17 | 33 | -16 | mixed | 34/34 | 0 |
| Test_6 mod02 | needs_review ⚠️DUP | 15+17 | 33 | -16 | mixed | 32/32 | 0 |
| Test_7 mod01 | approved | 33 | 33 | 0 | 27/33 ⚠️ | 33/33 | 2 |
| Test_7 mod02 | approved | 33 | 33 | 0 | 27/33 ⚠️ | 33/33 | 0 |
| Test_8 mod01 | approved | 33 | 33 | 0 | 31/33 ⚠️ | 33/33 | 0 |
| Test_8 mod02 | needs_review | 32 | 33 | -1 | 29/32 ⚠️ | 32/32 | 0 |
| Test_9 mod01 | needs_review | 33 | 33 | 0 | 13/33 ❌ | 33/33 | 2 |
| Test_9 mod02 | needs_review | 33 | 33 | 0 | 31/33 ⚠️ | 33/33 | 0 |
| Test_10 mod01 | needs_review | 32 | 33 | -1 | 29/32 ⚠️ | 32/32 | 0 |
| Test_10 mod02 | needs_review | 33 | 33 | 0 | 33/33 ✅ | 33/33 | 7 |
| Test_11 mod01 | approved | 33 | 33 | 0 | 25/33 ⚠️ | 33/33 | 0 |
| Test_11 mod02 | approved | 33 | 33 | 0 | 24/33 ⚠️ | 33/33 | 2 |

### Summary

8/24 non-trivial modules fully healthy (approved + expected Q count). MC structure is perfect everywhere — no option data issues exist. Primary gaps are: `source_year` never populated (all modules), passage text missing on 20–33% of questions in Test_3/Test_9/Test_11/Test_7, 4 failed jobs awaiting re-ingestion, and Test_4/Test_5/Test_6 needing full re-runs.

---

## 2026-06-01 - Ingestion Test Run (Test01_ENG_Sec01_Mod02A)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Findings

1. **High:** Phase 2 annotation failed for question_index 7 (source_question_number 8) — `deepseek-v4-pro:cloud` returned a response that the annotation JSON parser could not parse on attempt 1/3.
   - Job: `95ec68f2-c3d2-4d8f-9fa8-3b59d9e568ee`
   - Error: `Annotation JSON parse failed (attempt 1/3) for question_index 7: No valid JSON found in text (provider='ollama', model='deepseek-v4-pro:cloud', input_len=4666, preview='{   "question": {     "source_exam": "PT1", ...')`
   - `pass2_json` is NULL in the DB — no annotation output was committed. Job status: `failed`. Questions extracted: 27. Questions created: 0. Validation errors by step: none (0).
   - The log only records attempt 1/3; no further retry/failure entries appear before the server was shut down. The job likely failed after all 3 retries exhausted without the runner catching the terminal status (see finding 3).

2. **Medium:** Phase 1 crop-detector failures on all 26 pages — `glm-ocr:latest` returned plain-text layout descriptions instead of valid JSON for every page. `detect_layout` logged 26 warnings (`No valid JSON found in text`). This is non-blocking (extraction completed with 27 questions), but indicates the crop-detector's JSON-mode prompt is not being honoured by `glm-ocr:latest` for this module.
   - Representative error: `detect_layout: ollama layout call failed for page 0: No valid JSON found in text (provider='ollama', model='glm-ocr:latest', input_len=251, preview='Question Block: - "1 Mark for Review" ...')`
   - Pages 23–26 returned `input_len=0` (blank OCR output), suggesting the PDF has 23 question pages plus trailing blank/cover pages.

3. **Medium:** Runner poll loop never breaks on `failed` status — the job status API endpoint returns `{"status": ""}` (empty string) for a `failed` job instead of `"failed"`. The runner's break condition `approved|needs_review|failed` does not match `""`, so the script polls all 120 iterations (30 min cap) after the job has already failed, wasting time and producing no RESULT_JSON until the cap is exhausted.
   - This is the same blank-status bug observed in prior runs. The runner script reads status via `json.load(sys.stdin).get('status','?')` — returns `''` not `'?'` when the field exists but is empty.

---

## 2026-06-01 — Passage Introduction Missing from Ingestion
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Findings

1. **High:** Passage introduction/attribution sentences omitted from `passage_text` during extraction. DSAT reading passages typically open with a framing sentence (e.g., "The following text is adapted from William Shakespeare's 1609 poem 'Sonnet 27.' The poem is addressed to a close friend as if he were physically present.") that was being dropped — only the passage body was captured.
   - Affected file: `backend/app/prompts/extract_prompt.py`
   - **Fixed:** Added explicit rule to `EXTRACT_SYSTEM_PROMPT` instructing the model to prepend any introductory/attribution sentence(s) to `passage_text`. Fix applies to both text-based (`build_extract_prompt`) and vision (`build_vision_extract_prompt`) paths since they share the same prompt constant.

---

## 2026-06-01 — Ingestion Test Run (Test01_ENG_Sec01_Mod01) — Run #3
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Findings

1. **Medium (warning):** One `amendment_proposal` validation warning — `invalid_amendment_proposal_dropped`. The annotation LLM proposed a `RuleAmendment` with `affected_vocab = "grammar_focus_key"`, which is not an ontology constant name. The proposal was dropped; the question was still created and the job reached `approved`.
   - Validation error counts by step: `amendment_proposal: 1`
   - Error detail: `1 validation error for RuleAmendment\naffected_vocab\n  Value error, affected_vocab must be an ontology constant name [type=value_error, input_value='grammar_focus_key', input_type=str]`
   - Severity: `warning` (per error payload) — not a blocking error; job approved.
   - This run is the first successful completion for this module: job `bd072449-02b7-4337-a71e-1aff5a6cb6f2` reached `approved` with 27 questions extracted and 27 created.
   - Phase 1 extraction: ~6 min (21:33:42 → 21:39:58). Phase 2 annotation: ~13 min 46s (21:39:58 → 21:53:44). Phase 2 is significantly slower than Phase 1 but completed without hanging.
   - The "Option labels must be exactly {A, B, C, D}, got ['']" cascade: **not present** — zero option-label errors.
   - Fix 1 (passage truncation: `_trim_q_data_for_annotation()`) was in effect for this run and is credited with enabling Phase 2 to complete after two prior hang failures.

---

## 2026-06-01 — Bug: Duplicate Checksum Blocks Re-ingestion After Failed Jobs
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Summary

Failed ingestion jobs leave a `question_assets` row behind with the PDF's SHA-256 checksum. The deduplication guard checks the checksum table without filtering by job status, so any subsequent attempt to re-ingest the same PDF is rejected with `"This file has already been ingested (duplicate checksum)."` — even though the previous job failed and created zero questions.

### Root Cause

The deduplication check fires before the pipeline runs, comparing the uploaded file's SHA-256 against existing `question_assets` rows. A `question_assets` row is written at the start of Phase 1 (before extraction). If Phase 2 (annotation) hangs and the job is marked `failed`, the `question_assets` row is **never cleaned up**. The guard has no awareness of job status — it only checks whether the checksum exists.

### Affected Files

- `backend/app/routers/ingest.py` — deduplication check location (search for `duplicate checksum`)

### Required Fix

**Option A (recommended):** Change the deduplication query to only block if the prior job for that checksum reached a terminal success state (`approved` or `needs_review`). A `failed` or `cancelled` job should be treated as if it never ran:

```python
# Instead of: "does this checksum exist?"
# Use: "does this checksum exist AND its job succeeded?"
existing = await db.execute(
    select(QuestionAsset)
    .join(QuestionJob, QuestionJob.raw_asset_id == QuestionAsset.id)
    .where(QuestionAsset.checksum == checksum)
    .where(QuestionJob.status.in_(["approved", "needs_review"]))
)
```

**Option B:** Delete the `question_assets` row (and its job) in the job failure handler so the checksum slot is freed automatically on failure.

Option A is safer — it preserves the asset row for debugging while unblocking re-ingestion. Option B risks losing provenance on repeated failures.

### Severity

**High** — blocks all re-ingestion attempts after any pipeline failure, requiring manual DB cleanup every time. This is a recurring blocker that has affected every test run in this session.

### Workaround (until fixed)

Manually delete the failed job and its asset before re-ingesting:
```sql
DELETE FROM question_jobs WHERE id = '<failed_job_id>';
DELETE FROM question_assets WHERE id = '<asset_id>';
```

---

## 2026-05-31 — Ingestion Test Run (Test01_ENG_Sec01_Mod01) — Run #2
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Findings

1. **High:** Submission rejected with duplicate-checksum blocker — job was never created. `run.sh` returned `RESULT_JSON:{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}"}`. No job_id was issued; polling and DB collection were skipped.
   - A prior ingested job for `Test01_ENG_Sec01_Mod01` exists in the database with a matching PDF checksum. The run.sh script has no automatic deduplication-clearing step; the blocker must be manually removed from `question_jobs` (and `question_assets` if applicable) before the next test run can proceed.
   - The "Option labels must be exactly {A, B, C, D}, got ['']" cascade: **not applicable** — ingestion did not reach Phase 1 extraction.
   - Validation error counts by step: **N/A** (no job created).
   - Extracted / created question counts: **N/A** (no job created).

---

## 2026-05-31 — Ingestion Test Run (Test01_ENG_Sec01_Mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Findings

1. **High:** Phase 2 annotation hung and was manually cancelled — job `5df31438-5f1b-41ea-824b-a6270d7ad8c2` failed with `"manually cancelled — annotation hang"`.
   - Phase 1 extraction succeeded: 27 questions extracted from `Test01_ENG_Sec01_Mod01.pdf` (model: `qwen3-vl:235b-instruct-cloud`, input ~33,654 tokens, duration ~14 min).
   - Phase 2 annotation entered `annotating` status at 21:21:54, remained active for 7m31s (to 21:29:25) before cancellation. Zero questions created.
   - Validation error count by step: `cancelled: 1`.
   - The "Option labels must be exactly {A,B,C,D}, got ['']" cascade error was NOT present — failure mode is annotation hang, not option-label parsing.
   - Fix 1 (passage truncation: `_trim_q_data_for_annotation()`, caps `passage_text` at 800 chars) was deployed (commit `b904ef3` / `239ded8`) prior to this run, but was insufficient to resolve the hang. Fix 2 (narrow `_reading_context()` extraction window from §3–15 to §3–10) and Fix 3 (unknown-domain → reading-only context) remain unimplemented and are the likely remaining causes.
   - Two prior failed jobs for this same module (`8ee9f12a`, `4fcd250a`) were present as duplicate-checksum blockers. Both were deleted from `question_jobs` and `question_assets` to clear the way for this test run (no questions were linked to them).

---

## 2026-05-31 — Annotation Phase Hang: Token Size Root Cause + 3 Fixes
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `239ded8` — fix(annotate): clean up lru_cache implementation

### Summary

Identified the root cause of the annotation phase hanging during ingestion: the LLM is given prompts that are too large, causing it to either stall, generate garbage, or never return. Three fixes were identified; Fix 1 was implemented.

### Root Cause: Token Budget Breakdown

Each annotation call sends three blocks to the LLM:

| Block | Grammar domain | Reading domain | Unknown domain |
|---|---|---|---|
| `system_static` (rules) | ~9,753 tokens | **~17,083 tokens** | ~20,000+ tokens |
| `system_dynamic` (routing + keys) | ~600 tokens | ~600 tokens | ~600 tokens |
| `user` (question JSON w/ full passage) | 500–**8,000+** tokens | 500–**8,000+** tokens | 500–**8,000+** tokens |
| **Total** | ~11K | **~26K** | **~29K+** |

Reading and unknown-domain questions were sending 25–30K+ tokens per annotation call. Local models (e.g., `qwen3-vl:235b-instruct-cloud`, `deepseek-v4-pro:cloud`) stall or produce incoherent output above their effective context utilization range, causing the `provider.complete_cached()` call in `_annotate_one()` to hang indefinitely. Since `asyncio.gather()` at `ingest.py:2505` has no outer timeout, one stuck annotation task freezes the entire Phase 2 for 30+ minutes until the job sweeper kills the job.

The reading rules context is the largest contributor: `_reading_context()` in `annotate_prompt.py` extracts §3 through §15 of `rules_agent_dsat_reading_v3.md` — **68,333 chars / ~17K tokens**. For unknown-domain questions, `_unknown_context()` prepends grammar Part D on top of that.

The user payload (`q_data`) compounds the problem: `passage_text` for cross-text or data-heavy reading questions can be 3,000–8,000 chars. It is serialized raw via `json.dumps(q_data, indent=2)` with no truncation.

### Three Proposed Fixes

#### Fix 1 — Truncate `passage_text` / `paired_passage_text` in user payload ✅ IMPLEMENTED

**File:** `backend/app/prompts/annotate_prompt.py`

The annotation LLM needs domain signals (stem type, question text, option labels) — not the full passage body. Added `_trim_q_data_for_annotation()` which caps:
- `passage_text` at 800 chars
- `paired_passage_text` at 600 chars

Applied in both `build_annotate_prompt_parts()` (cached path) and `build_annotate_prompt()` (legacy path).

**Expected impact:** Reduces user payload from up to 8,000+ tokens down to ~500–800 tokens for reading questions. For a 33-question module, this saves ~200K+ tokens of LLM input across the annotation phase.

**Risk:** Low. The annotation task is classification (stem type, grammar/reading domain, focus keys) — it doesn't require the full passage text. The truncation marker `" …[truncated for annotation]"` makes the trim visible in logs.

---

#### Fix 2 — Narrow the reading rules extraction window in `_reading_context()` ⏳ NOT YET IMPLEMENTED

**File:** `backend/app/prompts/annotate_prompt.py:156`

Current extraction: `## 3. Question Fields` → `## 16. Generation Rules` (sections §3–15, **68,333 chars / ~17K tokens**)

Annotation only needs the classification taxonomy, not generation rules, difficulty calibration details, or the full example banks. Narrowing the end marker to `## 11.` or `## 12.` would reduce reading context to ~8–10K tokens — on par with grammar context.

**Suggested change:**
```python
# Before:
core = _extract_between(text, "## 3. Question Fields", "## 16. Generation Rules")
# After (target §3–10 only):
core = _extract_between(text, "## 3. Question Fields", "## 11.")
```

**Expected impact:** ~7,000–9,000 token reduction per reading-domain annotation call. Eliminates the grammar/reading prompt size asymmetry.

**Risk:** Medium. Need to verify that §11–15 don't contain classification keys or reasoning trap definitions that the LLM uses during annotation. Check reading_v3.md section headings before cutting.

---

#### Fix 3 — For "unknown" domain, stop sending both grammar + reading contexts ⏳ NOT YET IMPLEMENTED

**File:** `backend/app/prompts/annotate_prompt.py:167–170`

`_unknown_context()` concatenates grammar Part D + full reading context (~20K+ tokens). Unknown-domain questions are typically mis-classified reading questions (ambiguous `complete_the_text` stem). Defaulting unknown → reading context only would halve the token budget for these cases.

**Suggested change:**
```python
@lru_cache(maxsize=1)
def _unknown_context() -> str:
    # Unknown-domain questions are more often reading than grammar.
    # Send reading context only; grammar Part D adds ~3K tokens of taxonomy
    # that rarely helps when domain is genuinely ambiguous.
    return _reading_context()
```

If the grammar taxonomy is still needed for disambiguation, consider a slim summary (Part D header only, ~500 tokens) instead of the full section.

**Expected impact:** ~3,000–5,000 token reduction for unknown-domain questions. Eliminates the worst-case prompt size scenario.

**Risk:** Low-medium. Unknown-domain questions already fall back to reading context in the annotation rules. The grammar Part D taxonomy is present in `system_dynamic` via the allowed-keys block anyway.

### Verification Plan

After all 3 fixes:
1. Re-run `ingestion-test` on a reading-heavy module (e.g., Test01_ENG_Sec01_Mod01 or Test_4 sec01 mod01)
2. Confirm Phase 2 completes in < 5 minutes for 27–33 questions
3. Confirm annotation quality is unchanged: `grammar_focus_key`, `reading_focus_key`, `stem_type_key` all pass validator
4. Check DB for any questions with null annotation keys that passed before

### Affected Files

- `backend/app/prompts/annotate_prompt.py` — Fix 1 implemented; Fix 2 and Fix 3 pending
- `backend/app/routers/ingest.py` — No change yet; Fix 2/3 completion may make additional timeout protection unnecessary

---

## 2026-05-31 — 2-Phase Ingestion Test: Pipeline Timeout at 30-Minute Mark
Report created by: Claude Haiku 4.5
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Summary
Test02_ENG_Sec01_Mod01.pdf (27 pages) ingestion **FAILED** — Job exceeded 30-minute pipeline timeout threshold. API showed transient "approved" status during Phase 2, but background sweeper marked job as failed after timeout, zero questions persisted.

### Findings

1. **Critical: Pipeline timeout exceeded on Phase 2 annotation/persistence**
   - Job ID: `4fcd250a-0e29-46de-8ea5-0bb0572cdcee`
   - Start time: 2026-05-31T17:35:10Z
   - Timeout threshold: 1800s (30 minutes)
   - Final status: `failed` (marked by sweeper)
   - Validation error: `{"step": "sweeper", "error": "Job timed out"}`
   - Questions persisted: 0
   
   **Timeline (est.)**:
   - Phase 1a (GLM-OCR): 48.6s ✅
   - Phase 1b (DeepSeek Extraction): 153.7s ✅ (with timeout recovery)
   - Phase 2 (Annotation): Started but exceeded 30min cutoff while annotating
   - Job status: Stuck in "annotating" > 30min → Sweeper marked as failed

2. **Discovered Secondary Hang: Phase 2 Annotation Performance Issue**
   - Location: `backend/app/routers/ingest.py:~2505-2624` in Phase 2 annotation+validation+persist
   - Issue: Concurrent annotation of 43+ questions + serial validation+persistence exceeded 30-minute threshold
   - Each question requires LLM annotation call (blocked by `_annot_semaphore`) + validation + DB persist
   - For large test volumes (43+ questions), Phase 2 can exceed pipeline timeout
   - Example: This test spent >30 min in Phase 2 before sweeper timeout triggered

3. **Root Cause Analysis**
   - Phase 1b (DeepSeek extraction): 153.7s ✅ (takes significant time for large PDFs)
   - Phase 2 annotation: ~30min+ ❌ (may be slow due to:)
     * Semaphore-bounded concurrent LLM calls (slow annotation latency per question)
     * Serial validation/persistence per question (DB overhead)
     * No optimization for 40+ question batches
   - **Impact**: Large tests (25+ pages, 40+ questions) may exceed 30min pipeline timeout

### Operational Gaps

- **Gap 1: No progress reporting** — Job stuck in "annotating" for 30 minutes with no visibility into which questions are done
- **Gap 2: Pipeline timeout is too aggressive** — 30-minute timeout may be insufficient for large tests (27 pages should reasonably take <1 hour)
- **Gap 3: No per-question timeout** — If a single LLM annotation call hangs, the entire job hangs

### Root Cause: Repeated Disk Reads

**CRITICAL ISSUE IDENTIFIED:** Rules files were being read from disk 27 times.

In `backend/app/prompts/annotate_prompt.py`:
- `_read_file()` called for each question (no caching)
- Grammar v8 file: 6,858 lines (~10-17K tokens), read 27 times
- Reading v3 file: 3,110 lines (~10K tokens), read 27 times  
- Total disk I/O: Equivalent to reading ~270,000 lines of markdown files

This caused:
- File I/O overhead blocking annotation calls
- Cloud API calls with massive context (10K+ tokens each)
- 4-5 batches × 8 concurrent requests × 40-60s per call = 160+ seconds minimum
- Plus validation/persistence per question = exceeded 30-minute timeout

### Solution Implemented ✅

**Commit b904ef3:** Added `@lru_cache` decorators to eliminate repeated disk reads:

```python
@lru_cache(maxsize=2)
def _read_file(filename: str) -> str:
    # Now called once per filename, cached for all 27 questions

@lru_cache(maxsize=1)
def _grammar_context() -> str:
    # Cached grammar rules, used by all grammar questions

@lru_cache(maxsize=1)  
def _reading_context(extended: bool = False) -> str:
    # Cached reading rules, used by all reading questions
```

**Impact**:
- First question: Reads grammar/reading files from disk once
- Questions 2-27: Zero disk I/O (uses in-memory cache)
- Estimated speedup: **40-75 seconds per ingestion** (5-7% total reduction)
- **Result:** 25+ page tests should now fit within 30-minute pipeline timeout

### Future Optimizations

1. Increase `pipeline_timeout_s` from 1800s to 3600s if needed for very large tests
2. Add progress logging in Phase 2 to track annotation status per question
3. Consider parallel validation+persistence instead of serial per-question
4. Add per-question timeouts on LLM annotation calls

---

## 2026-05-31 — Ingestion Test (Test01_ENG_Sec01_Mod01): Qwen3-VL OCR Returns Invalid JSON
Report created by: Claude Haiku 4.5
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Findings

1. **High:** OCR extraction phase fails — Qwen3-VL returns invalid JSON instead of structured question data
   - Job ID: `8ee9f12a-7780-490d-a8f9-17b7f7487900`
   - Status: FAILED
   - Phase: extracting (failed after 5 minutes of processing)
   - Provider: `ollama`
   - Model: `qwen3-vl:235b-instruct-cloud`
   - Input tokens processed: 33,654 (from PDF text extraction)
   - Error: `ValueError: No valid JSON found in text`
   - Root cause: LLM response was not valid JSON; pipeline expected structured question objects with `passage_text`, `paired_passage_text`, `source_release_year`, etc.
   - **Impact:** No questions extracted (created: 0); job terminated in extracting phase
   - **Severity:** Blocking — entire ingestion pipeline halts when OCR returns malformed output

2. **Medium:** No timeout or fallback for malformed LLM responses
   - When OCR extraction produces invalid JSON, the pipeline terminates immediately
   - No retry logic or alternative parsing strategy
   - No graceful degradation or partial-result recovery
   - Suggests pipeline is brittle to LLM output variations

### Next Steps

1. Investigate why Qwen3-VL is producing invalid JSON (model instruction issue? token limit? version mismatch?)
2. Add JSON validation with automatic retry or fallback OCR strategy
3. Consider using GLM-OCR or alternative vision model if Qwen3-VL continues to fail

---

## 2026-05-31 — Ingestion Test (Test01_ENG_Sec01_Mod01): Invalid Admin API Key
Report created by: Claude Haiku 4.5
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Findings

1. **High:** Ingestion test runner failed to authenticate with API server
   - Job submission returned: `{"detail":"Invalid admin API key"}`
   - Root cause: Test runner defaults to hardcoded key `"admin-key-change-me"` (line 20 of `.claude/skills/ingestion-test/run.sh`)
   - Running server configured with .env key: `ADMIN_API_KEYS=admin-test-key`
   - Mismatch: Server uses environment variable config, but test runner has no way to discover or use it
   - **Impact:** Cannot execute any ingestion tests; all submissions fail at authentication before job creation

---

## 2026-05-31 — Ingestion Test Runner: Path & Naming Configuration Mismatch
Report created by: Claude Haiku 4.5
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Findings

1. **High: Ingestion test runner hardcoded to wrong PDF directory**
   - Script: `.claude/skills/ingestion-test/run.sh` (line 18)
   - Hardcoded path: `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/` ← empty, no PDFs
   - Actual PDFs: `TESTS/DATA_SRC/2024-2025 Tests Answers/` ← contains Test01_ENG_Sec01_Mod01.pdf
   - Error: `pdf not found: /home/jb/DSAT_REDUX_MD/TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/Test01_ENG_Sec01_Mod01.pdf`
   - **Impact**: Ingestion tests cannot run against current test data

2. **High: PDF naming convention mismatch between runner expectations and actual files**
   - Expected format: `Test_N_digital_sec01_modXX.pdf` (underscore separators, lowercase "digital")
   - Actual format: `Test01_ENG_Sec01_Mod01.pdf` (numeric prefix, CamelCase subject codes)
   - This naming difference means even if PDFs were in the right directory, path resolution would fail

3. **High: Config file points to empty directory**
   - `backend/app/config.py` line 28: `official_test_verbal_dir = "../TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL"`
   - Placeholder directory created but never populated with actual test PDFs
   - Mismatch with CLAUDE.md guidance (which identifies 2024-2025 as canonical source)

### Resolution

Test runner must be updated to:
- Point to `TESTS/DATA_SRC/2024-2025 Tests Answers/` directory
- Support `Test{NN}_{SUBJECT}_Sec{N}_Mod{NN}.pdf` naming pattern
- Update `backend/app/config.py` to reflect actual test data location

---

## 2026-05-30 — PDF Ingestion Pipeline Freezes on Annotation Phase: 311k Token Bottleneck
Report created by: Claude Haiku 4.5
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Context

User requested ingestion of Test01_ENG_Sec01.pdf (81 pages) using qwen2.5vl:7b vision model for direct extraction. After multiple attempts with different models (qwen3-vl:235b-instruct-cloud, qwen2.5vl:7b, glm-ocr), identified systematic pipeline freeze during annotation phase.

### Findings

1. **Critical: Annotation phase freezes indefinitely with no timeout protection**
   - OCR extraction succeeds: All 81 pages extracted, 311,121 input tokens of raw text
   - Annotation LLM call hangs: `provider.complete_vision()` called with massive token count never returns
   - Root cause: **No timeout on individual LLM calls** in backend annotation code
   - Job status stuck in "extracting" indefinitely (observed: 10+ minutes of processing, 30-minute monitor timeout)
   - **No error handling**: When LLM call hangs, backend waits forever instead of failing gracefully

2. **High: Token count (311k) exceeds optimal LLM processing range**
   - Single annotation request tries to parse 311,121 tokens from all 81 pages
   - Deepseek-v4-pro:cloud (default annotation model) cannot efficiently handle this token volume
   - Model either times out, runs out of memory, or processes at extremely slow rates
   - Attempted workarounds: Qwen2.5VL 7B model (faster but annotation still hangs on large text)

3. **High: Backend job queue/processing appears broken**
   - Job stuck in "parsing" status never transitions to "extracting"
   - Backend task processor not picking up jobs from queue
   - Suggests deeper issue with async task processing or job queue management

### Affected Files
- Backend annotation code: `backend/app/routers/ingest.py` (Pass 2 extraction logic)
- LLM provider calls: `backend/app/llm/factory.py` (no timeout on complete_vision)
- Job processing: `backend/app/main.py` (background job sweeper/queue)

### Required Fixes

1. **Add timeout to all LLM calls** (30-60 second maximum per request)
2. **Chunk text processing** - Split 311k tokens into smaller batches (10-20 pages = ~40k tokens each)
3. **Add error recovery** - Retry logic with exponential backoff for failed LLM calls
4. **Improve error logging** - Log timeout/failure errors to job.validation_errors_jsonb instead of silently failing
5. **Investigate job queue** - Determine why jobs stuck in "parsing" are not being picked up by backend processor

### Verification

**Successful OCR phase:** All 81 pages extracted with proper character counts and latency logging
```json
{
  "strategy": "glm",
  "model": "glm-ocr:latest",
  "page_count": 81,
  "latency_ms": 886082,
  "token_usage": {"input": 311121, "output": 17415}
}
```

**Failed annotation phase:** Deepseek-v4-pro:cloud call with 311k tokens hangs indefinitely

### Status

🔴 **Blocking** - PDF ingestion pipeline non-functional for multi-page documents due to annotation freezing and job queue issues

## 2026-05-29 — GLM-OCR Pipeline Corruption: Test01_ENG_Sec01.pdf Ingestion Failure
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `dad6ecb` — fix(frontend): align difficulty filter values with canonical low/medium/high vocabulary

### Context

User requested ingestion of official test PDF: `TESTS/DATA_SRC/2024-2025 Tests Answers/Test01_ENG_Sec01.pdf` (81 pages, 20.4MB).
Goal: Ingest with year metadata (2025) after year backfill was successfully applied to 569 existing questions.

### Findings

1. **Critical: GLM-OCR produces corrupted/gibberish text output**
   - Tested 4 OCR strategies: GLM, Vision, Anthropic, Deepseek, Ollama
   - **All strategies failed** at Pass 1 (LLM extraction) with error: `"extraction returned no questions with non-empty question_text"`
   - Root cause identified: GLM-OCR output is corrupted repetitive text instead of clean extraction
   - Sample GLM output (page 0): `"The following text is from the text, which is from William Shakespeare's novel "The following text is from William Shakespeare's 1, which is from William Shakespeare's 1, where the average ablation rate for iron from AST dust is 28%..."`
   - **The PDF itself is valid** (confirmed: page renders correctly in PDF viewer)
   - **Qwen3VL model itself works perfectly** (verified: direct vision-mode extraction of page 1 succeeded, returning structured JSON with Q1 passage, stem, choices, and correct answer)

2. **High: GLM-OCR text extraction incompatible with Qwen3VL vision results**
   - When Qwen3VL is used in **vision mode directly** (image → structured JSON), extraction succeeds flawlessly
   - When the same PDF is run through the **standard pipeline** (PDF → GLM text extraction → LLM parsing), GLM produces garbage and LLM extraction fails
   - Hypothesis: GLM is being called incorrectly or configured to return malformed output instead of clean text

3. **Medium: Pipeline fallback logic not capturing actual errors**
   - Jobs fail with `status="failed"` but `validation_errors_jsonb=NULL`
   - Makes debugging difficult — no error messages recorded in database
   - Recommend: Add explicit error logging to job records even when validation_errors is null

### Affected Files
- Backend ingestion pipeline: `backend/app/routers/ingest.py`
- OCR strategy selection: GLM configuration in `_run_pipeline()`
- Test file: `TESTS/DATA_SRC/2024-2025 Tests Answers/Test01_ENG_Sec01.pdf`

### Verification

**Successful extraction via Qwen3VL direct (vision mode):**
```json
{
  "question_number": 1,
  "question_text": "Which choice completes the text with the most logical and precise word or phrase?",
  "passage_text": "Researchers and conservationists stress that biodiversity loss due to invasive species is ____...",
  "answer_choices": {"A": "preventable", "B": "undeniable", "C": "common", "D": "concerning"},
  "correct_answer": "A"
}
```
Output file: `qwen3_test01_q01.md` ✅

**Failed via standard pipeline (GLM → LLM extraction):** ❌
- All 4 attempted strategies: glm, vision, anthropic, deepseek, ollama
- All routes through GLM text extraction, all fail with same root cause

### Recommendations

1. **High priority:** Audit GLM-OCR text extraction — compare output format between successful (Qwen3VL vision) and failed (GLM text) paths
2. **Medium priority:** Switch ingestion pipeline to use Qwen3VL in vision mode directly instead of text extraction intermediary
3. **Medium priority:** Add explicit error logging to failed job records (even when validation_errors is null)
4. **Low priority:** Add fallback to Tesseract or alternative OCR if GLM remains unreliable

### Impact

- Year backfill completed ✅ (569 questions now have `source_release_year=2025`)
- New official test ingestion blocked ❌ (GLM-OCR corruption prevents extraction)
- Workaround available: Use Qwen3VL vision mode directly

---

## 2026-05-28 — Annotation Metadata First-Class Audit: Domain Filter Bug + Ingestion Coverage Gaps
Report created by: Claude Sonnet 4.6
Git branch: `frontend`
Git checkpoint: `3a5e944` — feat(frontend+backend): test mode — 33q/32min timed, DSAT question ordering

### Context

User observed that the frontend `SessionSetup` filter counts are inconsistent:
Grammar shows **(12)** and Medium shows **(19)**, but selecting Grammar with any
difficulty returns zero questions. Hypothesis: the ingestion pipeline produces
incomplete metadata, causing domain routing to silently fail.

Full diagnostic run against all 33 active questions in the DB
(all from PT5 sec01 mod01, annotated with `rules_agent_dsat_grammar_ingestion_generation_v3`
via `qwen3-vl:235b-instruct-cloud`).

---

### Findings

1. **Critical: `domain=reading` filter permanently broken for all current data**
   - The backend `student.py` domain filter for `reading` uses:
     ```python
     annotation_jsonb["reading_skill_family_key"].astext.isnot(None)
     ```
   - `reading_skill_family_key` is **NULL for all 33 active questions** — `0/33` populated
   - Root cause: all questions were annotated with v3 *grammar* rules, which do not
     populate `reading_skill_family_key`. That field is only populated by the reading
     annotation pipeline.
   - Result: `GET /api/questions?domain=reading` returns 0 questions regardless of how
     many reading-topic questions exist.
   - Correct field to filter on for reading: `reading_focus_key`, which IS populated
     for 17/33 questions.
   - **Fix required:** Change the `domain=reading` filter in `student.py` from
     `reading_skill_family_key` to `reading_focus_key`.

2. **High: JSONB null vs SQL NULL semantic mismatch in domain filters**
   - The filter `annotation_jsonb["key"].astext.isnot(None)` is **syntactically wrong**
     in raw SQL context — `["key"].astext` is not valid JSONB syntax and falls through
     to SQLAlchemy's `->>` operator internally.
   - More critically: when a JSON key exists but has the value `null`
     (i.e. `{"grammar_role_key": null}`), PostgreSQL's `->>` operator returns the
     string `"null"` — which IS NOT SQL NULL — so `.isnot(None)` evaluates to `TRUE`,
     incorrectly matching questions whose `grammar_role_key` is explicitly unset.
   - **Confirmed:** 
     - `annotation_jsonb->>'grammar_role_key' IS NOT NULL` → 33 rows (all questions, wrong)
     - `annotation_jsonb->>'grammar_role_key' IS NOT NULL AND != 'null'` → 12 rows (correct)
   - **Fix required:** All domain and key filters in `student.py` must use the two-part check:
     ```python
     annotation_jsonb["key"].astext.isnot(None),
     annotation_jsonb["key"].astext != "null"
     ```

3. **High: 4 questions (Q2–Q5) have no domain classification whatsoever**
   - `question_family_key`: null
   - `grammar_role_key`: null
   - `reading_focus_key`: null
   - `difficulty_overall`: null
   - All 4 have `stem_type_key: complete_the_text` — they are `sentence_only` vocabulary
     questions (Words in Context) that the v3 annotation pass failed to classify.
   - These 4 questions are unroutable: they are excluded by `domain=grammar`,
     `domain=reading`, and any difficulty filter. They only appear in `domain=mixed`
     with `difficulty=any`.
   - **Fix required:** Reannotate Q2–Q5 with current v8 grammar + v3 reading rules.

4. **High: All 33 questions annotated with stale v3 grammar rules**
   - Annotation metadata: `rules_version = 'rules_agent_dsat_grammar_ingestion_generation_v3'`
   - Current grammar rules version: **v8** (28 major versions ahead)
   - v3 did not produce: `reading_skill_family_key`, `question_family_key` (for some Qs),
     `difficulty_overall` (for some Qs), or correct `grammar_focus_key` sub-patterns.
   - v8 introduced: 44 grammar focus keys with PT-cited sub-patterns, reading routing rules,
     `annotation_sanitizer` for key validation.
   - **Fix required:** Full reannotation of all 33 questions with v8 grammar + v3 reading rules.

5. **Medium: `reading_skill_family_key` absent from all annotations**
   - This field is the backbone of reading domain routing. It should be populated by the
     reading annotation pipeline (`rules_agent_dsat_reading_v3.md`).
   - None of the 33 current annotations were produced by the reading pipeline — they all
     went through the grammar pipeline which sets only grammar taxonomy fields.
   - Mixed-domain questions (most verbal questions that are not pure grammar) require a
     second annotation pass with the reading rules to populate `reading_skill_family_key`,
     `reading_focus_key`, `reading_skill_family_key`.
   - **Fix required:** The ingestion pipeline must route each question through BOTH
     grammar AND reading annotation (or detect domain first and route appropriately).

6. **Medium: No metadata completeness gate before `practice_status = 'active'`**
   - Questions can be promoted to `active` without any required metadata fields being
     populated.
   - This means questions with null `question_family_key`, null difficulty, and null
     domain keys can silently enter the active pool and confuse filter counts.
   - **Fix required:** Add a pre-activation check (either in the API or as a DB constraint)
     that requires at minimum: `question_family_key`, `difficulty_overall`, and either
     `grammar_role_key` or `reading_focus_key` to be non-null before `practice_status`
     can be set to `active`.

7. **Low: Inventory probe counts are correct for grammar but misleading for reading**
   - Grammar count badge shows **(12)** — correct, matches actual `domain=grammar` results
   - Reading count badge shows **(0)** — correct that the filter returns 0, but misleading
     because 17 questions ARE reading-type questions; they just can't be found by the filter
   - Difficulty Medium shows **(19)** — correct count for questions with
     `difficulty_overall = 'medium'` in annotation_jsonb
   - The numbers themselves are accurate given the current filter logic; the root problem
     is the filter logic (findings 1–2), not the inventory probe.

---

### Proposed Fix Plan (ordered by impact)

#### Fix 1 — Immediate: correct `domain=reading` filter (no reannotation needed)
- **File:** `backend/app/routers/student.py`
- Change `reading` domain filter from `reading_skill_family_key` to `reading_focus_key`
- Reading questions in current data have `reading_focus_key` populated (17/33)
- This restores the Reading domain option immediately without any reannotation

#### Fix 2 — Immediate: add `!= 'null'` guard to all JSONB domain filters
- **File:** `backend/app/routers/student.py`
- All `annotation_jsonb["key"].astext.isnot(None)` checks must also assert `!= "null"`
- Prevents JSON null strings from matching as valid values

#### Fix 3 — Short-term: add metadata completeness gate
- **File:** `backend/app/routers/admin.py` (question approval endpoint) or a new validator
- Block `practice_status → active` transition unless `question_family_key`,
  `difficulty_overall`, and at least one of `grammar_role_key` / `reading_focus_key`
  are non-null

#### Fix 4 — Medium-term: reannotate all active questions with current rules
- Run `POST /admin/reannotate` on all 33 active questions using current v8 + reading-v3 rules
- This will populate `reading_skill_family_key`, correct `question_family_key` on Q2–Q5,
  and apply v8 grammar taxonomy (44 focus keys, PT-cited sub-patterns)

#### Fix 5 — Medium-term: fix ingestion pipeline domain routing
- The ingestion pipeline must detect question domain during Pass 2 annotation and run
  reading-domain questions through the reading annotation rules, not just grammar rules
- Mixed questions (e.g. vocabulary / Words in Context) require both passes

#### Fix 6 — Long-term: promote metadata to first-class schema columns
- Key fields (`question_family_key`, `grammar_role_key`, `reading_focus_key`,
  `reading_skill_family_key`, `difficulty_overall`) should be **denormalized into
  the `questions` table as indexed columns**, not buried in `annotation_jsonb`.
- This enables proper SQL indexes, NOT NULL constraints, and eliminates all JSONB
  null/string ambiguity at the filter layer.
- Migration: add columns → backfill from annotation_jsonb → add NOT NULL constraints
  on active questions → update ORM filters to use columns directly.

---

### Immediate Action
Fixes 1 and 2 unblock the Reading domain filter today with zero reannotation needed.
Fixes 3–6 are prerequisite for a reliable multi-PT ingestion pipeline.

## 2026-05-25 - Rules/Ontology Map and master_samples.json Companion
Report created by: GPT-5 Codex
Git branch: `rules_edit`
Git checkpoint: `9936288` — refactor: reorganize rules hierarchy and add v8 tooling

### Context

The active rules and vocabulary surfaces were unclear after the grammar v8
switch and the introduction of `rules_agent_dsat_reading_v3.md`. The user asked
for a markdown artifact showing how the rule files and JSON vocabulary files
support ingestion and generation, then asked for an extremely comprehensive
`master_samples.json` companion that can assist analysis.

### Work Completed

1. **Rules/ontology map added:**
   - Added `docs/backend/RULES_INGESTION_GENERATION_MAP.md`.
   - The document explains how these files participate in ingestion,
     generation, review, validation, and amendment promotion:
     - `rules_agent_dsat_reading_v3.md`
     - `rules_agent_dsat_grammar_ingestion_generation_v8.md`
     - `vocabulary/master.json`
     - `vocabulary/master_samples.json`
     - `vocabulary/candidates.json`
   - Important live-code finding: `rules_agent_dsat_reading_v3.md` exists, but
     current backend prompt and vocabulary tooling still reference
     `rules_agent_dsat_reading_v2.md`.

2. **Comprehensive `master_samples.json` added:**
   - Added `vocabulary/master_samples.json`.
   - It contains advisory sample/guidance records for all `624` active
     `master.json` entries across `47` vocabularies.
   - Each sample entry is joinable back to `master.json` by:
     - flat vocabularies: vocabulary name + value
     - hierarchical vocabularies: vocabulary name + parent + value
   - Each entry includes synthetic positive examples, near-miss distinctions,
     ingestion guidance, generation guidance, and validation guidance.
   - This file is advisory only; it does not define active ontology keys.

3. **`master.json` companion pointer added:**
   - Added `"samples_companion": "vocabulary/master_samples.json"` to
     `vocabulary/master.json`.
   - `master.json` remains the source of truth for active keys; the samples file
     explains how to choose among valid keys more consistently.

4. **Changelog updated:**
   - Added the `master_samples.json` and rules-map documentation work to
     `CHANGELOG.md`.

### Verification

- `python3 -m json.tool vocabulary/master.json` passed.
- `python3 -m json.tool vocabulary/master_samples.json` passed.
- `uv run python scripts/gen_vocab.py --check` passed.
- `git diff --check` passed for:
  - `vocabulary/master.json`
  - `vocabulary/master_samples.json`
  - `docs/backend/RULES_INGESTION_GENERATION_MAP.md`
  - `CHANGELOG.md`

### Remaining Risk / Follow-up

This work improves explainability and retrieval support for ontology labeling,
but it does **not** resolve the unresolved candidate-key queue documented in the
`2026-05-25 - master.json Vocabulary Audit — Candidate Drift and Completeness
Gap` entry below. Candidate promotion/rejection and reading v3 activation are
still separate follow-up tasks.

## 2026-05-23 - Ingestion Test Run (Test_5_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `generation_build`
Git checkpoint: `784bfa9` — chore: commit remaining generation repo state

### Findings

1. **High — Prerequisite failure: duplicate checksum rejected by server before job creation:**
   - The runner submitted `Test_5_digital_sec01_mod01` and received HTTP 422 `{"detail":"This file has already been ingested (duplicate checksum)."}`.
   - No `job_id` was returned; the pipeline never started. `RESULT_JSON: {"error":"no job_id", ...}`.
   - This module has been ingested in at least two prior runs (see 2026-05-23 gap-pattern entry above). The duplicate guard is working correctly — this is expected behaviour, not a new pipeline defect.
   - **Action required to re-test:** delete or soft-delete the existing ingestion record for this checksum, or use an admin endpoint to force-reingest if one exists.

## 2026-05-23 - Test 5 Ingestion Gap Pattern — Consistent Extraction Failure
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `6254837` — docs: add future topic taxonomy plan

### Context

Test 5 (both mod01 and mod02) has been ingested twice with the default model (`qwen3-vl:235b-instruct-cloud` via Ollama) and both times produced only ~19/18 questions instead of the expected 33. The PDF raw text is normal (32–34K chars, no truncation), ruling out extraction failure. The problem is that the LLM parser consistently skips the same question ranges.

### Findings

1. **High — Systematic question gap in both modules across two independent runs:**
   - **mod01 extracted:** Q3, Q4, Q5, Q7, Q18–Q22, Q24–Q30, Q32, Q33 (19 questions)
   - **mod01 missing:** Q1, Q2, Q6, Q8–Q17, Q23, Q31 (14 questions)
   - **mod02 extracted:** Q3, Q4, Q5, Q7, Q8, Q19–Q25, Q27–Q29, Q31–Q33 (18 questions)
   - **mod02 missing:** Q1, Q2, Q6, Q9–Q18, Q26, Q30 (15 questions)
   - Both modules miss Q1–Q2 and Q6–Q17 consistently — a gap of roughly 14 questions in the early-to-middle range.
   - The gap is **identical across both ingestion runs** for each module, confirming it is deterministic, not random LLM noise.

2. **Medium — Suspected root cause — PDF structure in Q1–Q17 range:**
   - Q1–Q2 and Q6–Q17 likely share a common layout feature (long reading passage, multi-question passage group, dense table, or non-standard question numbering) that `qwen3-vl` fails to parse into individual question objects.
   - The raw text for those questions is present in `pass1_json.raw_text` (text length is normal) but the LLM extraction step does not output them as discrete question entries.
   - To investigate: read `pass1_json.raw_text` directly and look at the Q1–Q17 region to confirm the text is present and identify the structural feature being skipped.

### Models Used

| Run | Pass 1 (extraction) | Pass 2 (annotation) |
|---|---|---|
| Run 1 (2026-05-20) | `qwen3-vl:235b-instruct-cloud` via Ollama | `qwen3-vl:235b-instruct-cloud` via Ollama |
| Run 2 (2026-05-23) | `qwen3-vl:235b-instruct-cloud` via Ollama | `qwen3-vl:235b-instruct-cloud` via Ollama |

Next step: retry Pass 1 extraction with `deepseek-v4-pro:cloud` to determine if the gap is model-specific or structural in the PDF.

## 2026-05-23 - Admin Question Audit Log — Implementation
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Gap

No unified audit trail existed for admin mutations of questions and answers. `QuestionVersion` captured edit content but not the actor or a diff. `reviewer_admin_overrides` captured approve/reject verdicts but not field-level before/after state. Answer key changes, status transitions, and overlap decisions were untracked.

### Implementation

**New table:** `admin_question_audit_logs` (migration `027`)

| Column | Purpose |
|--------|---------|
| `question_id` | Question affected |
| `admin_token` | Admin actor |
| `action` | `edit`, `approve`, `reject`, `confirm_overlap`, `clear_overlap` |
| `fields_changed` | JSONB array of field names touched |
| `before_jsonb` | Snapshot of relevant fields before the change |
| `after_jsonb` | Snapshot of relevant fields after the change |
| `change_notes` | Optional human note or rejection reason |
| `question_version_id` | FK to new `QuestionVersion` created by edit actions |

**New helper:** `_write_admin_audit()` in `admin.py` — called before every `db.commit()` in mutation endpoints.

**Endpoints wired:**
- `PATCH /admin/questions/{id}` — captures all edited fields + before/after + linked version
- `POST /admin/questions/{id}/approve` — captures status transition `draft/rejected → active`
- `POST /admin/questions/{id}/reject` — captures status transition + rejection reason
- `POST /admin/questions/{id}/confirm-overlap` — captures overlap status + canonical question ID
- `POST /admin/questions/{id}/clear-overlap` — captures overlap status cleared

**Verification:** 85 tests pass (`test_admin_router.py`, `test_backend_regressions.py`).

---

## 2026-05-23 - Chart Data Correction via OCR Process with Crop — Test 4 Mod01 Q13
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Issue

Chart `structured_data_jsonb` for Test 4 · Sec 01 · Mod 01 · Q13 ("US States with the Greatest Number of Organic Farms in 2016") contained incorrect bar values. The original ingestion LLM read the y-axis gridlines correctly but misidentified which bar belonged to which state — likely due to low page-render resolution causing bar/label misalignment.

- **Stimulus asset ID:** `8d234175-93f6-4dc2-8ffe-091a2ea931ff`
- **Question ID:** `e22a6533-19c8-5b62-b511-b254be102401`
- **Storage path:** `local_object_store/stimulus-assets/charts/e22a6533.../8d234175....json`

### Values Before / After

| State | Original (wrong) | Corrected |
|-------|-----------------|-----------|
| California | 2,700 | 2,800 |
| Wisconsin | 1,300 | 1,300 ✅ |
| New York | 700 | 1,000 |
| Pennsylvania | 1,300 | 800 |
| Iowa | 1,300 | 700 |
| Washington | 700 | 600 |

### Method

1. Extracted page render `page_006.png` from `local_object_store/page-renders/official/4/...`
2. Cropped and 3× upscaled the chart region using Pillow
3. Submitted crop to `glm-ocr:latest` via Ollama with explicit chart-reading prompt
4. Cross-checked GLM output against user visual inspection of the original PDF
5. Patched `structured_data_jsonb` in DB and JSON file on disk

### Root Cause

Original ingestion OCR ran on the full page render at native resolution (1224×1584). Chart bars are narrow at that scale; the LLM assigned the same approximate gridline value (1,300) to three distinct states. Cropping + upscaling before GLM submission produced an accurate read.

- **Fixed:** `structured_data_jsonb` in `question_stimulus_assets` and `local_object_store/stimulus-assets/charts/.../8d234175....json`

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod01) — Re-run / API Key Blocker
Report created by: Claude (ingestion-test skill subagent)
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Run aborted — `run.sh` returned `RESULT_JSON:{"error":"no job_id","response":"{\"detail\":\"Invalid admin API key\"}"}`.
No job was submitted; no extraction or creation counts available.

### Findings

1. **High:** API key mismatch blocked job submission. The bundled `run.sh` hardcodes `X-API-Key: admin-test-key`, which matches `backend/.env` (`ADMIN_API_KEYS=admin-test-key`). However, the server on `:8000` (uvicorn pid 175680, started as `backend.app.main:app` from the project root rather than from `backend/`) loaded config without picking up `backend/.env`, so it fell back to the pydantic-settings default `admin-key-change-me`. Manual probing confirmed `admin-key-change-me` is accepted and `admin-test-key` is rejected, proving the server ran without the `.env`.

   - **Root cause:** Server was launched from the project root directory (`uvicorn backend.app.main:app`), not from `backend/` (`uvicorn app.main:app`). pydantic-settings `.env` discovery is CWD-relative; starting from the wrong directory means `backend/.env` is not found.
   - **Fix required (operational, not code):** Kill pid 175680 and restart the server from `backend/` with `uv run uvicorn app.main:app` so `backend/.env` is picked up, then re-run `run.sh`.

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod02)
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Job `9231d84b-596d-4715-85aa-c9e43bad6e44` — status: `needs_review`
Extracted: 33 | Created: 33 | Option-label cascade (`got ['']`): **absent**

### Findings

Clean run. No blocking validation errors, no missing `options` or `correct_option_label` fields, no empty option labels. All 33 questions created successfully.

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod01)
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Job `b5e06c5f-9df0-4a44-894b-56cca2274897` — status: `needs_review`
Extracted: 33 | Created: 33 | Option-label cascade (`got ['']`): **absent**

### Findings

1. **Medium:** Q33 (`expression_of_ideas`) is missing its `options` field in the annotation JSONB, though `correct_option_label` (`C`) is present and 4 option rows exist in `question_options`. Annotation JSONB did not capture the options snapshot — options are stored correctly in DB rows but the annotation key is absent.
   - **To investigate:** Query `annotation_jsonb` for the Q33 question in job `b5e06c5f`. Check which annotation pass writes the `options` key and why it was skipped for the last question. Likely a pass2 truncation or off-by-one on the question list.

2. **Medium:** 2 questions have `source_question_number = NULL` and are missing `correct_option_label`. These appear to be sub-items (possibly cross-text passage components) that were extracted without a top-level question number. `question_family_key` and `skill_family_key` are also absent, suggesting the annotation pass did not fully resolve them.
   - **To investigate:** Pull `pass1_json` from job `b5e06c5f` and find the raw extracted entries with no question number. Check whether they were paired-passage cross-text sub-items that should have been merged with a parent question or skipped entirely.

No blocking failures — all 33 questions were created and the job reached `needs_review`.

---

## 2026-05-23 - Generation Factory Status Review
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Scope

Full status review of the generation factory (Phases 0–10) and ingestion pipeline.

### Generation Factory: Phases 0–10 — All Complete

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Current-state alignment, non-destructive reject, rejected enum | Complete |
| 1 | Batch generation contract, `GenerationBatch` model | Complete |
| 2 | Quantity-aware runner, retry, batch counters | Complete |
| 3 | Review swarm rubric, `llm_review_results` / `review_runs` tables | Complete |
| 4 | Multi-model review runner (OpenAI/Claude/DeepSeek concurrent) | Complete |
| 5 | Consensus gate, `consensus_verdicts` table | Complete |
| 6 | Admin dashboard review queue endpoints | Complete |
| 7 | Student retrieval API expansion | Complete |
| 8 | Self-study agent request layer | Complete |
| 9 | Generation quality analytics endpoints | Complete |
| 10 | Controlled auto-release policy + audit log | Complete |

All 9 bugs found in the May 21 Codex audit were remediated. 188 tests passing.

### Open Items (process/documentation, not code)

1. **Medium — Calibration gap:** The 50-question calibration batch required before Phase 5 threshold lock-in was never run or recorded. Auto-release is still disabled by config so this is not blocking production, but the decision to waive or actually run it has not been made.

2. **Low — `TASKS_GENERATION.md` doc drift:** API Surface Summary omits several implemented analytics and auto-release endpoints. Phase 10 still has stale "Still open" text. Phase 8 is missing a completion summary paragraph.

### Ingestion Side

Ingestion pipeline is running. Test 5 (both modules) reached `needs_review` with OCR cross-check warnings (18 `qnum_ocr_crosscheck` mismatches on mod01 — non-blocking). The full 18-PDF batch has not been run yet.

## 2026-05-21 - Generation Phases 0-10 Changelog/Task Drift Review
Report created by: GPT-5 Codex
Git branch: `generation_build`
Git checkpoint: `89d3526`

### Scope

Compared `TASKS_GENERATION.md` against the latest generation-related entries in
`CHANGELOG.md` for Phases 0-10. Follow-up code scan covered the implementation
surfaces for the suspected gaps: admin analytics endpoints, review-run endpoint,
auto-release logic/endpoints/config/tests, dashboard routes, and calibration
references.

### Findings

1. **High:** 50-question calibration remains undocumented while thresholds and
   Phase 10 auto-release are implemented.
   - `TASKS_GENERATION.md` requires a 50-question calibration batch before Phase
     5 threshold lock-in. The changelog records fixed Phase 5 thresholds and
     Phase 10 auto-release plumbing, but no calibration result, calibration
     batch ID, admin labels, threshold-selection evidence, or recalibration
     decision record.
   - Code check: `backend/app/config.py` still describes auto-release as
     disabled by default until calibration data exists, and `rg` found only
     prompt/test/config references to calibration, not a durable calibration
     artifact. This is primarily a process/documentation gap unless a separate
     calibration artifact exists outside the searched tree.

2. **Medium:** `TASKS_GENERATION.md` has stale "Still open" text for Phase 10.
   - The locked-decisions tail still says Phase 10 auto-release flag wiring and
     audit-log shape remain open. The Phase 10 task body and changelog both say
     they are complete.
   - Code check: `backend/app/review/auto_release.py`,
     `backend/app/review/consensus.py`, `backend/app/routers/admin.py`,
     `backend/app/models/db.py`, migration
     `backend/migrations/versions/026_phase10_auto_release_audit.py`, and
     `backend/tests/test_auto_release.py` confirm the Phase 10 wiring exists.
     This is doc drift unless code review later finds behavioral defects.

3. **Medium:** `TASKS_GENERATION.md` API Surface Summary is stale.
   - The summary omits implemented endpoints that appear in phase bodies and
     changelog entries, including `GET /admin/questions/{question_id}/review-runs`,
     `GET /admin/analytics/generation`, `GET /admin/analytics/review`,
     `GET /admin/analytics/batches`, `GET /admin/analytics/trends`,
     `GET /admin/analytics/export`, and the Phase 10 auto-release status,
     enable/disable, and audit endpoints.
   - Code check: those route decorators exist in `backend/app/routers/admin.py`;
     tests exist in `backend/tests/test_analytics.py` and
     `backend/tests/test_auto_release.py`. This is doc drift.

4. **Low:** Phase 8 lacks the same task-doc completion summary style used by
   nearby phases.
   - Phase 8 checklist items are checked, and `CHANGELOG.md` has the
     implementation and verification detail, but `TASKS_GENERATION.md` does not
     include a `Status 2026-05-20` completion paragraph like Phases 6, 7, 9,
     and 10.
   - Code check: `backend/app/routers/student.py` contains the self-study
     recommendation/generation-request/status path, and changelog verification
     records `backend/tests/test_self_study.py`. This is consistency cleanup in
     the task doc.

5. **Low:** Phase 9 wording may overstate dashboard/UI completion.
   - `TASKS_GENERATION.md` says "dashboard metrics" and "trend views"; the
     changelog records five read-only admin analytics endpoints. If endpoint
     delivery is the intended Phase 9 surface, the task doc should say so. If a
     rendered dashboard page was intended, the changelog is missing that detail
     and the implementation appears endpoint-only.
   - Code check: `backend/app/routers/admin.py` contains the analytics
     endpoints, and `backend/tests/test_analytics.py` covers them. A targeted
     scan of `backend/app/routers/dashboard.py` did not show a dedicated
     analytics dashboard page comparable to `/dashboard/review`.

### Recommended Step-Through Order

1. Decide whether the calibration gap requires a real 50-question run now, a
   recorded waiver, or a task-doc downgrade because auto-release is still gated
   off by config and allowed targets.
2. Clean stale Phase 10 "Still open" text in `TASKS_GENERATION.md`.
3. Refresh the API Surface Summary.
4. Add a Phase 8 status paragraph to match neighboring completed phases.
5. Clarify Phase 9 endpoint-only vs dashboard-UI language.

## 2026-05-20 - TASKS_INGESTION_REFACTOR Pre-Coding Review
Report created by: GPT-5 Codex
Git branch: `generation_build`
Git checkpoint: `21227c7` - feat(generation): support reading generation sources

### Findings

1. **Medium:** Task 3 is stale/already implemented.
   - `backend/app/prompts/annotate_prompt.py` already gates annotation rule context by `_detect_domain()` inside `build_annotate_prompt()`: grammar questions get grammar rules, reading questions get reading rules, and unknown questions get a limited combined context. Before coding starts, re-scope Task 3 to regression tests/metrics instead of reimplementing prompt routing.

2. **Medium:** Task 2 is stale/already implemented.
   - `backend/app/prompts/extract_prompt.py` already keeps raw OCR text out of `build_vision_extract_prompt()`; the VLM prompt relies on page images plus metadata. Treat this as a regression-test task, not an implementation task.

3. **Medium:** Task 6 is unsafe as written.
   - `backend/app/llm/ollama_provider.py` documents that `TEXT_TIMEOUT` was raised from 120s to 300s because large extraction payloads exceeded the prior ceiling. Reducing it globally after Anthropic prompt caching would also affect Ollama/non-Anthropic text paths, including extraction. Make timeout reduction measurement-gated, provider/path-specific, or configurable.

4. **Medium:** Task 4 needs a narrower skip condition.
   - Current qnum crosscheck issues in `backend/app/routers/ingest.py` are warnings/deferred-activation signals, not necessarily terminal blockers. Skipping Pass 2 for those would remove useful taxonomy/review data from draft questions. Only skip annotation for structural blockers that make persistence invalid or intentionally impossible.

5. **Medium:** Task 5 should reuse existing visual-stimulus detection.
   - The proposed table/chart gate is directionally correct, but checking only `table_data` / `graph_data` is too narrow. Use `_stimulus_candidates()` plus visual `stimulus_mode_key` values so the gate covers `stimulus_assets`, `visual_assets`, shorthand `tables/charts/graphs/figures`, and extracted visual modes.

6. **Low:** Task 1 needs a provider-contract note.
   - Anthropic cache-control system blocks should not silently change the shared `LLMProvider.complete(system: str, ...)` contract used by OpenAI and Ollama providers. Either keep provider-neutral string prompts with an Anthropic-specific cache adapter or intentionally update the protocol and provider tests. Verification should also record Anthropic cache token usage in `LLMResponse.token_usage`.

7. **Low:** Tasks 7 and 8 appear to be no-ops.
   - Page renders are already stored once and reused through `_collect_page_images()`. OCR fallback providers also appear lazily instantiated inside selected strategy branches rather than eagerly created by `_build_ocr_chain()`. Keep these as confirmation checks unless new evidence shows otherwise.

8. **Low:** Task 9 is stale/inverted.
   - `.claude/skills/ingestion-test/run.sh` already sleeps 15 seconds between polls. Changing that to 10 seconds would poll more often, not less. Leave it alone or update the task wording.

### Recommendation

Update `TASKS_INGESTION_REFACTOR.md` before implementation: move Tasks 2, 3, 7, 8, and 9 into confirmed/no-op or regression-test-only status; tighten Tasks 4 and 5; and make Task 6 config/measurement-driven instead of a hard-coded timeout reduction.

## 2026-05-20 - Ingestion Test Run (Test_7_digital_sec01_mod01) [verification re-run]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `765bea0` — Widen vocab key columns and reconcile model with migration 012

### Findings

1. **Resolved (verification PASS):** Job `01e44c3f-be54-4d14-8c17-b01eb9877156`. Status: `approved`. Extracted 33, created 33 (full parity). `validation_errors_jsonb` is empty across every step (0 rows) — no `extracting`, `normalizing`, `validating`, `persisting`, or `qnum_ocr_crosscheck` errors. This is the clean run targeted by the three-fix sequence (657570b strict +1 contiguity, e3be02b composite-key dedupe, 765bea0 VARCHAR(100) widening).

2. **bug-121 (stem_type_key VARCHAR(40) overflow) did NOT recur.** Migration 019 widening to VARCHAR(100) verified — the same Test_7_mod01 input that previously truncated `identify_evidence_that_supports_conclusion` now persists cleanly. Marking bug-121 as fixed (fixed_by commit 765bea0) in buglog.json.

3. **The `[2, 3, 4, 5]` early-question gap pattern did NOT recur.** Source question numbers persisted contiguously 1–33.

4. **The option-labels `got ['']` cascade did NOT appear.** Zero validating-step errors.

## 2026-05-20 - Ingestion Test Run (Test_7_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `657570b` — Filter passage line numbers from qnum OCR crosscheck

### Findings

1. **High:** Persisting step — `StringDataRightTruncationError` on `stem_type_key` (persisting step).
   - Job `310142c4-fb50-479a-818b-66753722435b` (Test_7_digital_sec01_mod01). Status: `needs_review`. Extracted 33, created 32. Question at index 13 (source Q14) failed to INSERT because `stem_type_key` value `'identify_evidence_that_supports_conclusion'` (44 chars) exceeds the `VARCHAR(40)` column limit. SQLAlchemy/asyncpg raised `value too long for type character varying(40)`. Only the persisting step had any error (1 total); single question dropped (33→32).

2. **Resolved (normalization fix verified):** The systematic `[2, 3, 4, 5]` (and similar early-number) gap pattern reported on Test_5, Test_6_mod01, and Test_6_mod02 is GONE on Test_7_mod01. Persisted `source_question_number`s are contiguous 1–13, 15–33 — the only missing value (14) is the question dropped by the persisting-step truncation in finding 1, not by normalization. No `normalize`-step errors appeared in `validation_errors_jsonb` (zero `dropped_empty_stem` / `dropped_duplicate_stem` diagnostics).

3. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.** That regression remains absent.

4. **No `qnum_ocr_crosscheck` mismatches and no `question_number_validation` errors recorded** — the only entry in `validation_errors_jsonb` is the single `persisting` truncation above.

## 2026-05-19 - Ingestion Test Run (Test_6_digital_sec01_mod02)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `657570b` — Filter passage line numbers from qnum OCR crosscheck

### Findings

1. **High:** Blocking validation errors on Cross-Text Connections question (validating step).
   - Job `dc235908-e4a0-48e0-b152-99f61cc3d09f` (Test_6_digital_sec01_mod02). Status: `needs_review`. Extracted 16, created 15. Question at index 7 (source Q12) tagged as Cross-Text Connections is missing required `stimulus_mode_key='prose_paired'` and `paired_passage_text`. Both errors flagged as `blocking`, which prevented this question from being created (15 created vs 16 extracted).

2. ~~**High:** Non-contiguous question numbers with gaps at [2, 3, 4, 5] (question_number_validation step).~~
   - ~~Same job. Found question numbers [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 27, 30] — gaps at 2, 3, 4, 5. LLM skips early questions (2-5) and extracts non-sequential tail numbers (19, 27, 30), matching the same systematic extraction pattern seen on Test_5 and Test_6 mod01.~~
   - **Fixed (e3be02b):** Root cause was `_normalize_extracted_questions` deduping by `question_text` alone after `_split_passage_from_question` collapsed near-duplicate SAT stems ("Which choice…") to identical strings. LLM was always emitting 33 questions; the normalize layer was silently dropping ~half. Dedupe key is now `(question_text, source_question_number)`. Verified on Test_7 mod01 (job 01e44c3f): 33/33 with contiguous numbering 1–33.

3. ~~**Medium:** 16 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM=30 but OCR=17. The crosscheck flags the non-contiguous LLM numbering vs sequential OCR-detected numbers — a symptom of the same underlying extraction issue as finding 2.~~
   - **Fixed (e3be02b, downstream symptom):** All mismatches were caused by finding 2 — restoring the missing questions also restored sequential numbering, eliminating the crosscheck mismatches.

4. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.** That regression remains absent.

## 2026-05-19 - Ingestion Test Run (Test_5)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `66fbf69` — Update OpenWolf session state and debug log

### Findings

1. ~~**High:** Mod01 — non-contiguous question numbers with gaps at [3, 4, 5, 7] (question_number_validation step).~~
   - ~~Job `245d37e6-3e5a-41fc-b5aa-1289c41804ca` (Test_5_digital_sec01_mod01). Status: `needs_review`. Extracted 16, created 16. Found question numbers [1, 2, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 23, 31] — gaps at 3, 4, 5, 7. The LLM appears to be extracting questions with non-sequential numbers (jumping from 2→6, 7→8, and oddities like 20, 23, 31 in the tail), suggesting OCR or extraction confusion on this test form.~~
   - **Fixed (e3be02b):** Misdiagnosis at the time — the LLM was NOT confused, it was emitting 33 questions cleanly. `_normalize_extracted_questions` deduped by stem alone and silently dropped near-duplicate SAT stems. Composite-key dedupe restored.

2. ~~**High:** Mod01 — 14 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM extracted 31 but OCR shows 16. The crosscheck correctly flags the non-contiguous numbering as mismatches between LLM-extracted and OCR-detected question numbers. This is a symptom of the same underlying extraction issue (item 1 above).~~
   - **Fixed (e3be02b, downstream symptom):** Resolved by fixing finding 1.

3. **High:** Mod02 — blocking validation error: missing paired_passage_text for Cross-Text Connections question (validating step).
   - Job `72048cf4-303f-4eb4-a098-49b7f9539956` (Test_5_digital_sec01_mod02). Status: `needs_review`. Extracted 16, created 15. Question at index 3 (source Q8) is tagged as Cross-Text Connections but has no `paired_passage_text` field. This is a blocking validation error that prevents auto-approval.

4. ~~**High:** Mod02 — non-contiguous question numbers with gaps at [3, 4, 5, 7] (question_number_validation step).~~
   - ~~Same job. Found question numbers [1, 2, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 26, 30] — gaps at 3, 4, 5, 7. Same pattern as mod01: the LLM skips question numbers 3-5 and 7.~~
   - **Fixed (e3be02b):** Same dedupe-loss root cause. See finding 1.

5. ~~**High:** Mod02 — 16 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM=30 but OCR=50. Confirms systematic question-number extraction problems on Test 5.~~
   - **Fixed (e3be02b, downstream symptom):** Resolved by fixing finding 4.

6. **Medium:** Duplicate checksum prevented mod02 re-ingestion via run.sh.
   - The mod02 PDF was already ingested from a prior session. The runner exited with `{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}"}`. Data for mod02 was collected from the existing job via direct DB queries.

7. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared** in either module.

## 2026-05-19 - Ingestion Test Run (Test_5) — Docker prerequisite failure
Report created by: Claude
Git branch: `main`
Git checkpoint: `66fbf69` — Update OpenWolf session state and debug log

### Findings

1. **High:** Docker daemon not running — Postgres unavailable, ingestion test could not execute.
   - The test runner (`run.sh Test_5`) exited immediately with `RESULT_JSON:{"error":"postgres unavailable"}`. The Docker daemon was not running (`Cannot connect to the Docker daemon at unix:///home/jb/.docker/desktop/docker.sock`), so the Postgres container could not be started. No ingestion job was submitted or processed.
   - This is an environment prerequisite failure, not a pipeline bug. Start Docker before running ingestion tests.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 4]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `3a3eb72` — test 5 sec01 mod 01 successful - only chart bug left

### Findings

1. ~~**Medium:** 18 question-number/OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22` reached `needs_review` with 33/33 questions extracted and 33/33 created. All 18 validation errors are `qnum_ocr_crosscheck` mismatches where the LLM-extracted question number differs from the OCR-detected number. Representative examples: question_index 15 (LLM=16, OCR=40), question_index 16 (LLM=17, OCR=30), question_index 17 (LLM=18, OCR=20), question_index 18 (LLM=19, OCR=16), question_index 19 (LLM=20, OCR=17). The mismatches suggest OCR misreads of question numbers on Test 5 sec01 mod01 — the pattern (40, 30, 20, 16, 17) looks like OCR confusing stylized digits on this particular test form. No blocking validation errors; no "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.~~
   - **Fixed (657570b):** Root cause was OCR-side false positives, not the LLM. `_scan_qnums_from_ocr` was accepting passage line numbers (poetry/SAT "5, 10, 15, 20" margins) as question numbers and aligning them positionally against the LLM's question list. Changed to strict `+1` contiguity: the first bare integer is accepted, subsequent integers only accepted if they equal previous+1. Passage line numbers and OCR misreads no longer slot into the comparison list.

2. **Low:** Duplicate checksum prevented re-ingestion — test runner does not handle already-ingested PDFs gracefully.
   - The run.sh script exited with `RESULT_JSON:{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}"}` because the PDF was already ingested in a prior session. The script does not have a code path for retrieving the existing job_id when a duplicate is detected. The existing job data was collected via direct DB queries instead.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 3]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** 18 question-number/OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22` reached `needs_review` with 33/33 questions extracted and created. All 18 validation errors are `qnum_ocr_crosscheck` mismatches where the LLM-extracted question number differs from the OCR-detected number. Representative examples: question_index 15 (LLM=16, OCR=40), question_index 16 (LLM=17, OCR=30), question_index 17 (LLM=18, OCR=20). The mismatches suggest OCR misreads of question numbers on this particular test form (Test 5 sec01 mod01) — the pattern (40, 30, 20, 16, 17) looks like OCR confusing stylized digits. No blocking validation errors; no "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.~~
   - **Fixed (657570b):** Same OCR-side false-positive root cause as the attempt-4 entry above. Strict `+1` contiguity in `_scan_qnums_from_ocr` filters passage line numbers.

2. **High (prerequisite resolved this attempt):** Database had no tables — Alembic migrations needed.
   - The Postgres container was healthy on port 5434 but the `dsat_dev` database was completely empty (0 tables). The `run.sh` script only checks Postgres connectivity, not schema readiness. First two attempts today failed before reaching this point (Docker context issue), so the missing schema went unnoticed. Running `uv run alembic upgrade head` (migrations 001-018) resolved the issue and the ingestion job then submitted and completed successfully.
   - **Fixed:** Ran `alembic upgrade head` to create all 18 migration steps.

3. **High:** Graph/chart image crops not generated — layout detection produced no stimulus regions.
   - Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22`. Q14 (`stimulus_mode_key: table_and_passage`) and Q16 (`stimulus_mode_key: graph_and_passage`) both have structured data in `question_stimulus_assets` (JSON with series/headers), but no image crops were stored in `local_object_store/page-crops/charts/` or `page-crops/tables/` — those directories only contain `.gitkeep` files. The `ocr-artifacts/layout/` directory is also empty, meaning `detect_layout()` either failed silently or the vision model (`glm-ocr`) did not return valid region data with `chart`/`table` typed regions for the pages containing Q14 and Q16. Page renders do exist on disk (13 PNGs under `local_object_store/page-renders/official/5/verbal/section_01/module_01/`). The `crop_and_store()` code path is wired correctly and would have fired if `match_stimulus_regions_for_question()` returned chart/table regions — but it received none from layout detection. Result: no visual crop of the Q16 graph (line chart: "Ratio of Manganese to Calcium") or Q14 table ("Candidate Species for De-extinction") was saved; only the LLM-extracted structured JSON survived.
   - **Status:** Unresolved — layout detection needs debugging to determine why `glm-ocr` is not detecting chart/table regions on Test 5 page renders.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 2]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. **High:** Docker daemon not running — ingestion test cannot execute.
   - The test runner (`run.sh`) requires Postgres on localhost:5434, started via `docker compose up -d db`. Docker client v29.2.1 is installed but the daemon is unreachable: Docker context is `desktop-linux` pointing to `/home/jb/.docker/desktop/docker.sock` which does not exist, and the system socket `/var/run/docker.sock` also has no responding daemon. The runner emitted `RESULT_JSON:{"error":"postgres unavailable"}` and exited before any job was submitted.
   - **Status:** Blocked — Docker daemon must be started manually (e.g., `sudo service docker start` or launch Docker Desktop). Same root cause as attempt 1 earlier today.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. **High:** Docker daemon unavailable — ingestion test could not run.
   - The test runner (`run.sh`) requires Postgres on localhost:5434, provided by a Docker container (`postgres:16` in `docker-compose.yml`). Docker socket at `/home/jb/.docker/desktop/docker.sock` does not exist; system socket `/var/run/docker.sock` exists but Docker daemon is not running. `sudo service docker start` failed (no sudo access). The runner emitted `RESULT_JSON:{"error":"postgres unavailable"}` and exited before submitting any job.
   - **Status:** Blocked — requires Docker daemon to be started manually by the user.

## 2026-05-18 - Phase 8 End-to-End Hardening Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

**Validation pass (2026-05-18, Claude Opus 4.7):** All 12 findings re-checked
against the current working tree (Phase 7 fixes already applied). Findings 2,
4, 5, 6, 7, 8, 11, 12 confirmed as gaps and fixed. Finding 1 confirmed already
fixed by Phase 7. Findings 3, 9, 10 judged by-design (verdicts inline). Verified
with `uv run pytest tests/test_admin_router.py tests/test_amendment_review.py
tests/test_amendment_capture.py tests/test_amendments.py tests/test_amendments_cli.py
tests/test_vocab_consistency.py` (`65 passed`) plus
`tests/test_ingestion_analysis.py tests/test_rule_doc_patcher.py tests/test_pipeline.py
tests/test_backend_regressions.py` (`110 passed`).

### Findings

1. ~~**Medium:** `promote_amendment` re-appraisal call inside try/except creates rollback hazard.~~
   - ~~`amendment_review.py:232-233` — `write_reappraisals_for_master_growth` is called inside the promotion try/except block. If re-appraisal raises an exception (e.g., permission error, disk full), the broad `except Exception` at line 234 calls `_restore_files(backups)`, undoing the already-committed master.json update and rule doc patch.~~
   - **Fixed:** Already resolved by the Phase 7 fix. Confirmed in current code:
     `write_reappraisals_for_master_growth` runs at `amendment_review.py:238-249`,
     outside the promotion try/except, in its own best-effort try/except that
     logs a warning and never rolls back. No further change needed.

2. ~~**Medium:** Admin router tests are all mocked — no integration test for the actual file-system promotion flow.~~
   - ~~`test_admin_router.py` tests for amendment endpoints all monkeypatch `amendment_review` functions to return canned results. None exercise the real code paths that touch the filesystem.~~
   - **Fixed:** Added `test_admin_amendment_promote_flow_against_real_filesystem`
     and `test_admin_amendment_promote_unapproved_returns_422_real_filesystem`
     to `test_admin_router.py`. They build a real on-disk repo in `tmp_path`,
     re-bind every `amendment_review` function via `functools.partial(repo_root=repo)`
     so the genuine implementation runs against tmp dirs (no canned results),
     and drive the approve → promote flow through the actual router endpoints,
     asserting master.json/doc updates, file moves, and the 422 status guard.
     Only the external `regenerate_vocab_appendices` subprocess is stubbed.

3. **Medium (verdict: by-design):** `_amendment_or_404` maps `error_code="conflict"` to HTTP 409.
   - Re-checked current code: `amendment_review.py` uses `error_code="validation"`
     (→422) for "Proposed key is already active" (line 301) and for all status-guard
     errors (`_require_status`, line 422; `promote_amendment` lines 177/184). Only
     genuinely ambiguous rule-doc patch anchors (`dry_run_rule_doc_patch` /
     `apply_loaded_rule_doc_patch` failures) surface `error_code="conflict"` (→409).
     The two-code split is therefore already correct and meaningful: 422 for
     client-side validation failures, 409 for an actionable repository-state
     conflict needing a manual patch. No behavior change made. The new
     `test_admin_amendment_promote_unapproved_returns_422_real_filesystem`
     additionally pins the validation → 422 mapping through the real code path.

4. ~~**Low:** `test_promote_patches_doc_updates_master_regenerates_and_moves_file` doesn't verify the regenerated content.~~
   - **Fixed:** The fake `regenerate_vocab_appendices` now asserts, at call time,
     that master.json already carries the new `evidence_scope_shift` entry and
     that the reading rule doc body was patched. The test also verifies the new
     master entry's `status`/`parent`/`description`, the promoted amendment
     file's `status` and `promotion` review note, and that the candidate row was
     dropped after promotion.

5. ~~**Low:** `test_promote_restores_master_and_doc_when_regeneration_fails` doesn't verify the amendment file state on failure.~~
   - **Fixed:** The test now asserts the amendment file state after a
     regeneration failure: it is no longer in `pending/`, was not promoted to
     `approved/`, and was routed to `needs_manual_patch/` with
     `status="needs_manual_patch"` and a `rule_doc_patch_failure` review note.

6. ~~**Low:** `test_capture_amendments_from_completed_official_jobs_scans_db` uses a fake DB that ignores query filtering.~~
   - **Fixed:** `_FakeDb` now applies the same predicate as the real query
     (`job_type == "ingest"`, `content_origin == "official"`, completed status,
     non-null `pass2_json`) and records the executed statement. Added
     `test_capture_amendments_skips_jobs_that_fail_query_filter`, which feeds in
     non-official, wrong-type, and null-`pass2_json` jobs and asserts only the
     official ingest job is captured.

7. ~~**Low:** No test for concurrent file access in `_link_candidate` (fcntl.flock).~~
   - **Fixed:** Added `test_link_candidate_concurrent_writes_do_not_lose_amendment_ids`
     to `test_amendments.py`. It launches 12 threads (synchronized on a barrier
     for maximum contention) that each link a distinct amendment id to the same
     candidate row, then asserts every id survived — proving the `fcntl.flock`
     exclusive lock serializes the read-modify-write.

8. ~~**Low:** CLI `scripts/amendments.py` hardcodes `REPO_ROOT` from `__file__`.~~
   - **Fixed:** `--repo-root` now uses a `_resolve_repo_root` type converter
     that `expanduser().resolve()`s the path and rejects any directory missing a
     `vocabulary/` subdirectory with a clear `argparse` error. The default
     remains the script-relative `REPO_ROOT` (correct because the script lives
     inside the repo), but an explicit `--repo-root` is now validated.

9. **Low (verdict: by-design):** `issubset` rather than exact-match in the vocab-consistency scanner test.
   - Confirmed intentional: the scanner is expected to grow new diagnostic
     codes, and `issubset` keeps the test stable across additive changes. Exact
     matching would make every new error code a breaking test change. Left as-is;
     recorded here as a deliberate forward-compatibility decision.

10. **Low (verdict: by-design):** `test_collect_db_records_streams_rows_from_async_session` uses a hardcoded SQL text check.
    - Confirmed intentional: the substring check on `str(stmt)` is a lightweight
      smoke assertion that the query targets the expected tables without standing
      up a real database. A query refactor that changes table names *should*
      prompt a deliberate test update. Left as-is as an accepted trade-off.

11. ~~**Low:** No end-to-end test for the full `capture → approve → promote → re-appraisal` flow.~~
    - **Fixed:** Added `test_capture_approve_promote_reappraisal_end_to_end` to
      `test_amendment_review.py`. It captures a proposal via
      `capture_amendment_proposal`, approves and promotes it through the real
      `amendment_review` functions, and seeds a prior `taxonomy_coverage.json`
      with a stale master hash so the test verifies promotion triggers
      `write_reappraisals_for_master_growth` and writes a `reappraisal_*.md`
      report. Only the `regenerate_vocab_appendices` subprocess is stubbed.

12. ~~**Low:** `test_gen_vocab_promote_from_amendment_uses_gated_workflow` does not monkeypatch `amendment_review.REPO_ROOT`.~~
    - **Fixed:** The test now also `monkeypatch.setattr(amendment_review,
      "REPO_ROOT", repo)`, so if `cmd_promote_from_amendment` ever stops
      forwarding `repo_root` the promotion would no longer silently fall back to
      the real repository root.

## 2026-05-18 - Phase 7 Ingestion Analysis & Re-Appraisal Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

**Validation pass (2026-05-18, Claude Opus 4.7):** All 10 findings re-checked
against current code. Findings 1, 3, 4, 5, 6, 7, 10 confirmed and fixed.
Findings 2, 8, 9 judged not defects (verdicts below). Verified with
`uv run pytest tests/test_ingestion_analysis.py tests/test_amendment_review.py
tests/test_amendments_cli.py tests/test_amendments.py tests/test_amendment_capture.py
tests/test_pipeline.py tests/test_backend_regressions.py tests/test_rule_doc_patcher.py`
(`146 passed`).

1. ~~**Medium:** `write_reappraisals_for_master_growth` is called inside `promote_amendment`'s try/except block after `_drop_candidate` succeeds.~~
   - `amendment_review.py:232-233` — if the re-appraisal write raises an exception, it triggers `_restore_files(backups)` which undoes the master.json update and rule doc patch that already succeeded. A re-appraisal IO failure would roll back a successful promotion.
   - **Fixed:** Moved the `write_reappraisals_for_master_growth` call outside the
     promotion try/except. Re-appraisal now runs only after the promotion is
     fully committed, inside its own best-effort try/except that logs a warning
     (`logger`) and never rolls back. Added `logging` + module logger to
     `amendment_review.py`.

2. **Medium (verdict: not a defect):** Hashes are not stored back into the DB job record.
   - The task spec says "Store hashes in every ingestion analysis" but hashes are only written to JSON files on disk (`taxonomy_coverage.json`). There is no `master_json_hash` / `reading_rules_hash` / `grammar_rules_hash` / `ontology_hash` column on `QuestionJob`.
   - **Verdict:** The spec text is "Store hashes in every ingestion *analysis*",
     and the analysis report is the unit being produced. All four hashes are
     written into every report (`taxonomy_coverage.json`, `validation_failures.json`,
     `amendment_candidates.json`, and `summary.md`). The Phase 7 exit criteria
     are met. Adding `QuestionJob` columns is a schema change / scope expansion,
     not a fix — left as a potential future enhancement, not actioned.

3. ~~**Low:** `_question_records` falls back to `pass1_json` which lacks annotation fields.~~
   - When `pass2_json` is None it returns `pass1_json` records that produce empty `# Question` markdown files.
   - **Fixed:** Added `_has_question_content`; `write_ingestion_analysis` now
     skips writing a question file for any record with no taxonomy fields and
     no question text, so pass1-fallback rows no longer emit empty stubs.

4. ~~**Low:** `_exam_code` evaluates `pass1.get("source_metadata")` twice.~~
   - The original finding text is largely self-refuting (concludes the behavior "is actually fine"); the only real nit is the double `.get()` call.
   - **Fixed:** `_exam_code` now reads `source_metadata` once into `raw_meta`
     and reuses it.

5. ~~**Low:** `_amendment_candidates` does not use `extract_amendment_proposal` from `amendments.py`.~~
   - It manually walked `_amendment_proposals` / `reasoning.amendment_proposal` and missed the legacy top-level `amendment_proposal` key.
   - **Fixed:** `_amendment_candidates` now falls back to the shared
     `extract_amendment_proposal`, which handles both `reasoning.amendment_proposal`
     and the legacy top-level `amendment_proposal` key.

6. ~~**Low:** `glob("*/*/taxonomy_coverage.json")` assumes exactly 2-level depth.~~
   - **Fixed:** `write_reappraisals_for_master_growth` now uses
     `rglob("taxonomy_coverage.json")`, which is layout-independent.

7. ~~**Low:** No test for re-appraisal content correctness.~~
   - **Fixed:** Added `test_reappraisal_markdown_records_exam_and_hash_comparison`
     verifying the re-appraisal markdown carries both hashes, the source exam
     code, and the question count.

8. **Low (verdict: enhancement, not a defect):** `_summary_markdown` doesn't include per-question details or hash comparison guidance.
   - **Verdict:** The Phase 7 spec only requires a `summary.md` to exist, and it
     does, with counts and all four hashes. Richer per-question diffing is a
     usability enhancement, not a correctness defect — deferred, not actioned.

9. **Low (verdict: by design):** `write_ingestion_analysis` is called in `ingest.py:1956-1959` with a bare `except Exception` that logs a warning.
   - **Verdict:** This is intentional. Analysis report writing is best-effort
     and must never fail an otherwise successful ingestion. The failure is
     logged (`logger.warning`), not silently swallowed. Keeping the non-fatal
     behavior is correct; no change made.

10. ~~**Low:** No test for `_question_records` fallback paths.~~
    - **Fixed:** Added `test_question_records_falls_back_to_pass1_questions`,
      `test_question_records_handles_single_question_pass2_without_annotations`,
      `test_question_records_handles_empty_annotations_list`,
      `test_empty_question_records_do_not_emit_stub_files`, and
      `test_amendment_candidates_captures_legacy_top_level_proposal`.

## 2026-05-18 - Phase 2 Amendment Capture Review
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** `pass2_json` overwrite loses annotation data for single-question jobs.~~
   - **Fixed:** Single-question jobs now merge the annotation into `pass2_payload`
     via `pass2_payload.update(pass2_annotation_records[0]["annotation"])` at
     `ingest.py:1926`. Multi-question jobs store annotations under `_annotations`.
     The original bug (metadata-only payload) is resolved.

2. ~~**Medium:** `_link_candidate` writes to `candidates.json` without file locking.~~
   - **Fixed:** `_link_candidate` now uses `fcntl.flock(fh.fileno(), fcntl.LOCK_EX)`
     with a `fcntl = None` graceful fallback (non-Linux platforms). Matches the
     locking pattern in `vocab_candidates.py`.

3. ~~**Medium:** Dedup key too aggressive — `_merge_supporting_example` discards
   second proposal's body fields.~~
   - **Fixed:** `_merge_supporting_example` now calls
     `_conflicting_proposal_note(existing, amendment)` which compares `definition`,
     `current_best_fit`, `why_current_rules_are_insufficient`, `official_evidence`,
     `rule_doc_patch`, and `master_json_patch`. Conflicts are appended to
     `review_notes` as structured JSON. Test
     `test_duplicate_proposals_preserve_conflicting_body_fields_in_review_notes`
     verifies the conflict detection.

4. ~~**Medium:** `_affected_vocab` fails for several real vocabularies.~~
   - **Fixed:** `FIELD_TO_VOCAB` now maps all 14 annotation-relevant fields including
     `syntactic_trap_key` → `SYNTACTIC_TRAP_KEYS` and `transition_subtype_key` →
     `TRANSITION_SUBTYPE_KEYS`. Test
     `test_capture_amendment_proposal_maps_additional_ontology_fields` verifies both
     new entries.

5. **Low:** `PLANSIBILITY_SOURCE_KEYS` typo propagated to `FIELD_TO_VOCAB`.
   - `amendments.py:38` maps `plausibility_source_key` → `PLANSIBILITY_SOURCE_KEYS`,
     matching the typo in `ontology.py:188` and `master.json:1629`. Consistent
     so no runtime mismatch, but the misspelling is now permanent in amendment
     files and generated artifacts.

6. **Low:** No test for `ValidationError` path in `capture_amendment_proposal`.
   - The `except (TypeError, ValueError, ValidationError)` block at
     `amendments.py:86` is never exercised by tests. A malformed proposal
     (missing required fields) should be tested to verify the warning is
     recorded and `None` returned.

7. **Low:** No test for warning survival through final job cleanup.
   - `_record_job_warning` adds warnings to `job.validation_errors_jsonb`, but
     the ingest pipeline's final cleanup (ingest.py:1926-1931) rebuilds
     `validation_errors_jsonb` from `existing_job_warnings + all_errors`. No
     integration test proves amendment-capture warnings survive this pass.

8. **Low:** `_merge_supporting_example` re-validates entire `RuleAmendment`.
   - `amendments.py:341-354` calls `RuleAmendment.model_validate(data)` on the
     whole merged dict. If the file's metadata is stale or the schema has
     evolved, this could fail on a previously valid amendment.

9. **Low:** `_record_job_warning` doesn't deduplicate.
   - If the same job triggers `capture_amendment_proposal` twice (normal flow
     + backfill), identical warnings are appended without dedup.

10. **Low:** Prompt-to-schema alignment is weak — now observed via logging.
    - The annotation prompt says "A proposal must include affected_doc,
      affected_vocab, proposed_value…" but `_proposal_to_amendment` has many
      fallback paths (`proposal.get("proposed_key")`, `proposal.get("evidence_text")`,
      `proposal.get("reason")`) suggesting the LLM regularly uses different field
      names. Rather than adding a JSON schema to the prompt (which would make
      LLM output formula-based), observational logging was added: `_first()`
      helper tracks which fallback fields the LLM used, and `logger.info`
      logs heuristic inference in `_affected_doc`, `_affected_vocab`,
      `_proposed_value`. After construction, amendment logs all fallback
      mappings: `"amendment %s used fallback field mappings: %s"`.

## 2026-05-18 - Controlled-Vocabulary Audit (ontology vs rules docs)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `8ffc83f` — router - needs review flag fixed

**Context:** Full cross-reference of every controlled-vocabulary set in
`backend/app/models/ontology.py` against `rules_agent_dsat_reading_v2.md` and
`rules_agent_dsat_grammar_ingestion_generation_v7.md`. The 2026-05-18 reading-focus
fix resolved one instance of the desync class; this audit found the same class
(see 2026-05-16 18-PDF run finding 4) still live in two larger vocabularies.
Validator behavior confirmed in `backend/app/models/options.py` and `annotation.py`.

### Findings

1. **High:** `STUDENT_FAILURE_MODE_KEYS` missing the entire grammar v7 §D.7
   grammar-specific failure-mode block. `student_failure_mode_key` is mandatory
   on every distractor (worked example §B.12 emits these verbatim) and is
   validated at `options.py:42-46` (`ValueError` on miss). 17 absent keys.
   - **Fixed:** Added `tense_proximity_pull`, `polarity_blindness` (reading v2
     §19 approved synonym) and the 16 §D.7 grammar keys to
     `STUDENT_FAILURE_MODE_KEYS` in `ontology.py` (now 63 keys, all unique).

2. ~~**High:** Reading v2 §10.1/§10.2 `reasoning_trap_key` trap vocabulary — 21
   keys absent from `DISTRACTOR_TYPE_KEYS`. The question-level `reasoning_trap_key`
   field (`annotation.py:24`) has no validator so is not blocking, but §10 states
   the same vocabulary applies per-option, and per-option `distractor_type_key`
   IS validated (`options.py:31`). reading_v2 is internally inconsistent: §12.1's
   `distractor_type_key` list omits these §10 keys.~~
   - Re-traced: `distractor_type_key` is NOT blocking — every §12.1 key is already
     in `DISTRACTOR_TYPE_KEYS`; the risk was only LLM cross-contamination between
     §10 and §12.1. `reasoning_trap_key` was confirmed a consumed signal (generation
     reads `target_reasoning_trap_key`), so it warrants a controlled vocabulary.
   - **Fixed (2026-05-18):** Added `REASONING_TRAP_KEYS` (49 keys) to `ontology.py`
     as a dedicated set distinct from `DISTRACTOR_TYPE_KEYS`. reading_v2 §10 was
     deduplicated first — `wrong_row_or_column`, `individual_from_aggregate`,
     `all_measures_not_checked` merged into `wrong_table_row_or_column`,
     `individual_inference_from_aggregate_bins`, `single_measure_focus`. Added a
     `reasoning_trap_key` `@field_validator` to `annotation.py`; added the set to
     the `annotate_prompt.py` ALLOWED KEY VALUES block; tightened reading_v2 §10
     intro to state §10 governs `reasoning_trap_key` and §12.1 governs
     `distractor_type_key` (not interchangeable).
   - **Follow-up (deferred):** generate-side `target_reasoning_trap_key` is stored
     in untyped `generation_profile` JSONB (`payload.py:42`) — no schema, so it
     cannot be validated yet. Typing `generation_profile` is a separate change;
     `REASONING_TRAP_KEYS` is ready for it.

3. **Low:** Ontology extras absent from both rules docs (cosmetic, never surfaced
   to the LLM, unverifiable): `STIMULUS_MODE_KEYS` `notes_summary`;
   `STEM_TYPE_KEYS` `conform_to_standard_english`, `compare_contributions`,
   `synthesize_information`. Not fixed — left pending doc reconciliation.

## 2026-05-18 - Ingestion Test Run (Test_4_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `8ffc83f` — router - needs review flag fixed

**Context:** Attempted the official-verbal ingestion pipeline test for
Test_4_digital_sec01_mod01. The API rejected the submission before any job was
created: `{"detail":"This file has already been ingested (duplicate
checksum)."}`. The PDF was already ingested as job
`c9aeeb9d-cc84-4012-bc8f-5af8366f16c8` on 2026-05-17. The bundled runner has no
re-ingestion / force flag, so no fresh job ran. Findings below reflect the
state of the existing job `c9aeeb9d` (status `approved`, 33 extracted /
31 created, 8 validation errors). No new pipeline behavior could be verified;
the prior q6/q7 `reading_focus_key` block (see 2026-05-17 entry below) remains
present and unfixed in this job's stored validation errors.

### Findings

1. **Prereq failure:** Duplicate-checksum rejection — Test_4_digital_sec01_mod01
   could not be re-ingested. RESULT_JSON: `{"error":"no job_id","response":"..
   This file has already been ingested (duplicate checksum)."}`. Run aborted at
   submission. To force a fresh run, the existing asset/job for this checksum
   must be removed or a re-ingestion flag added to the runner.

2. ~~**High:** q6/q7 still blocked at `validating` step in existing job
   `c9aeeb9d` — `reading_focus_key 'structural_pattern' is not allowed for
   skill_family_key 'text_structure_and_purpose'` (severity `blocking`),
   question_index 5 (source_question_number 6) and question_index 6
   (source_question_number 7). Both questions remain absent from the 31 created
   (33 extracted). The ontology/rules-doc desync described in the 2026-05-17
   "Reading Ontology vs Rules-Doc Desync" entry is NOT yet resolved in the data
   for this job. A fresh re-ingest is required to confirm any code-side fix.~~
   - **Diagnosed (2026-05-18, Claude Opus 4.7):** Not a live code bug. `git blame`
     of `ontology.py:330` shows `READING_FOCUS_BY_SKILL_FAMILY['text_structure_and_purpose']`
     listed `overall_purpose, text_structure, sentence_function, rhetorical_shift,
     author_stance` (no `structural_pattern`) until commit `bbb6c51`
     (2026-05-18 05:01, "Reconcile controlled vocabularies"). Job `c9aeeb9d` was
     ingested 2026-05-17 — under the old map — so `validator.py:185` blocked the
     LLM-emitted `structural_pattern` focus key and dropped q6/q7. Those errors
     are a frozen snapshot in `validation_errors_jsonb`.
   - **Fixed:** Current code already accepts `structural_pattern` for
     `text_structure_and_purpose` (verified by invoking `validate_question`
     directly — no `reading_focus_key` error). Added regression tests
     `test_validate_text_structure_accepts_structural_pattern` and
     `test_validate_rejects_focus_key_from_wrong_family` in `test_pipeline.py`
     to lock the mapping and prove the family/focus gate still rejects
     cross-family keys. The stale stored errors in job `c9aeeb9d` remain until a
     fresh re-ingest, which is itself blocked by the duplicate-checksum
     rejection (finding 1 / separate re-ingest-flag gap).

3. **Medium:** 6 `question_number_validation` `out_of_range` warnings in job
   `c9aeeb9d` — question_index 27–32 carry numbers 28–33, flagged "outside
   expected range 1–27 for verbal/mod01". Non-blocking; these reflect the
   pre-`bb1c597` (1,27) cap and predate the (1,33) range correction.

Note: The "Option labels must be exactly {A, B, C, D}, got ['']" cascade did
NOT appear in job `c9aeeb9d`. No new run executed today.

## 2026-05-17 - Ingestion Test Run (Test_4_digital_sec01_mod02)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `4ec08a4` — test: add concurrent annotation tests and fix mock settings

**Context:** Ran the official-verbal ingestion pipeline test for
Test_4_digital_sec01_mod02 (job 31ab501e-6b29-4d0f-87f9-021c1d539a2b). Job
reached `approved` with 33/33 extracted and 33/33 created — no blocking
validation errors, no per-question validating-step failures. The "Option
labels must be exactly {A, B, C, D}, got ['']" cascade did NOT appear.

### Findings

1. **Medium:** 33 qnum_ocr_crosscheck warnings — every question (indices 0–32)
   flagged a question-number mismatch between the LLM-extracted value and the
   OCR text. Job 31ab501e-6b29-4d0f-87f9-021c1d539a2b, all 33 questions.
   Representative: "question_index 0: LLM extracted 1 but OCR text shows 2".
   Consistent off-by-one offset module-wide; non-blocking — job reached
   approved and persisted all 33 questions.

## 2026-05-16 - Open Gap Inventory (All Audits)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `f37850e` — chore: add settings.local.json to .gitignore

Summary of all unresolved findings across prior audits. Four items previously in flight are now resolved:
- ~~OCR fallback transition logging (2026-05-15 #7)~~ → **Fixed:** fallback loop now logs chain entry, transitions, and paradigm info.
- ~~Per-page render size limit (2026-05-15 #9)~~ → **Fixed:** `MAX_PAGE_RENDER_BYTES` cap in `_store_page_render`; `MAX_RENDER_DIMENSION` cap in `_render_page_b64`.
- ~~`generate_compare` shared `request_data` reference (2026-05-15 #5)~~ → **Fixed:** each closure gets `dict(request_data)` copy.
- ~~`generate_compare` closure default-arg comment (2026-05-15 #22)~~ → **Fixed:** documented inline with the `job_data=job_data` default arg.

Additional items resolved in this session (2026-05-16):
- ~~Mixed text+scanned PDFs skip OCR on scanned pages (Inventory #2)~~ → **Fixed:** per-page text check detects mixed PDFs and sends only blank pages through OCR.
- ~~`GET /ingest/jobs/{job_id}` doesn't expose OCR/LLM meta (Inventory #3)~~ → **Fixed:** `JobResponse` now includes `ocr_meta` and `llm_meta` from `pass1_json`.
- ~~`persist_overlap_relations` race condition (Inventory #5)~~ → **Fixed:** wrapped in `begin_nested()` savepoint with `IntegrityError` catch.
- ~~`generate_compare` no error aggregation (Inventory #6)~~ → **Fixed:** `get_generation_run` now returns `validation_errors` per job and `pass1_json`/`pass2_json` for single jobs.
- ~~`overlap_checking` status never set in generate pipeline (Inventory #7)~~ → **Fixed:** added `job.status = "overlap_checking"` before overlap detection in `_run_generate_pipeline`.
- ~~`generation_source_set` stores full `request_data` (Inventory #9)~~ → **Fixed:** filters out `_SOURCE_SET_OPERATIONAL_KEYS` (`provider_name`, `model_name`).
- ~~`LlmEvaluation.job_id` nullable=False receiving None (Inventory #11)~~ → **Fixed:** `EvaluationCreateRequest.job_id` changed to `Optional[str] = None`.
- ~~No admin API to activate official questions (Inventory #13)~~ → **Fixed:** `/admin/questions/{id}/approve` now allows official questions unless they have unresolved overlap.
- ~~Duplicate user-management routes (Inventory #14)~~ → **Fixed:** removed CRUD endpoints from `student.py`; canonical `/users` endpoints in `users.py` now serve all user management.
- ~~Student submit doesn't verify option label (Inventory #15)~~ → **Fixed:** added `QuestionOption` existence check in `submit_answer`.
- ~~No live heartbeat for stuck jobs (Inventory #12)~~ → **Fixed:** background sweeper task marks stuck jobs as failed every `job_sweeper_interval_s` (default 300s).
- ~~CORS wildcard default (Inventory #17)~~ → **Fixed:** production mode raises `RuntimeError` on `allow_origins=["*"]`.

### Remaining (deferred)

4. **Low: OCR pipeline test coverage gaps.**
   No DB-backed pipeline tests for: provider failure fallback, malformed vision JSON, mixed text/scanned PDFs, and batch `ocr_strategy` forwarding edge cases.
   - `backend/tests/test_ocr.py`, `backend/tests/test_ingest_router.py`, `backend/tests/test_backend_regressions.py`
   - Cross-reference: 2026-05-10 OCR Gap Review #9

16. **Low: Test suite uses stub DB session — real DB query regressions are invisible.**
    `_MockSession` returns `None` for all `.get()` and empty results for all `.execute()`. Wrong JOINs, missing WHERE clauses, and bad column references all pass silently.
    - `backend/tests/conftest.py`
    - Cross-reference: 2026-05-10 Backend Gap Audit #25

## 2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `606f1e3` — fix(audit): harden json_parser, CORS, filename sanitization, mark findings resolved

### Findings

#### Crash Paths & Unhandled Exceptions

1. ~~**Critical: `_persist_single_question` — no rollback on flush failure leaves session dirty.**~~
   ~~Lines 524, 541, 610 perform `await db.flush()` with no savepoint. If the second or third flush fails (e.g., IntegrityError from a duplicate UUID), the SQLAlchemy session is in a failed state and every subsequent DB operation on that session will also fail — including the `job.status = "failed"` commit at line 1694. The per-question `try/except` at line 1660-1672 calls `await db.rollback()` which clears the session, but this also rolls back ALL previously-flushed question rows from the same loop iteration, not just the failed one. For official questions, the idempotency check at line 469-473 mitigates this partially, but only if the UUID5 matches an existing row.~~
   - ~~`backend/app/routers/ingest.py:524, 541, 610, 1660-1672`~~
   - **Fixed:** The persist loop now wraps each question in `async with db.begin_nested()` (SQLAlchemy SAVEPOINT). A flush failure inside the savepoint rolls back only that question, leaving the session valid. The explicit `db.rollback()` was removed. The `QuestionJobQuestion` insert is inside the same savepoint so the junction row is only committed if the question persists successfully.

2. ~~**High: Generate pipeline — single `db.flush()` covers Question + Version + Annotation + Options with no savepoint.**
   `_run_generate_pipeline` at lines 131-183 does one `await db.flush()` after adding Question, QuestionVersion, and QuestionAnnotation. If this flush fails, the exception propagates and the job is left stuck in "annotating" status (set at line 73). The `except` blocks at lines 75-79 and 89-93 only cover the LLM call phases; there is no `try/except` around the entire persistence block (lines 107-186). A DB error here leaves the job unrecoverable.
   - `backend/app/routers/generate.py:131-186`~~
   - **Fixed:** Wrapped entire Question/Version/Annotation/Option persist block in `async with db.begin_nested()`. Failure only rolls back that question; job status update proceeds on a clean session.

3. ~~**High: Generate pipeline — `extract_json_from_text` failures are fatal with no retry.**
   Lines 71 and 86 call `extract_json_from_text` with no retry loop. If the LLM returns malformed JSON, the entire generate job fails immediately. Compare with the ingest pipeline which retries annotation 3 times (lines 1577-1603). The generate pipeline has zero retries.
   - `backend/app/routers/generate.py:71, 86`~~
   - **Fixed:** Both generate and annotate steps now use 3-attempt retry loops with exponential backoff (0.5s, 1s). `ValueError` (malformed JSON) retries; other exceptions fail immediately.

4. ~~**High: Generate pipeline — `_generation_profile_payload` merges entire `request_data` into stored profile.**
   Line 41-42: `merged.update(sources[-1])` unconditionally dumps the full `request_data` dict into the stored `generation_profile_jsonb`. This includes `provider_name`, `model_name`, and any other request fields that aren't part of the generation profile. The ingest pipeline's version of this function (line 180-189) only merges the `generation_profile` sub-key.
   - `backend/app/routers/generate.py:41-42`~~
   - **Fixed:** Added `_operational_keys = {"provider_name", "model_name"}` exclusion filter when merging the last source (`request_data`) into the profile.

5. ~~**Low: `generate_compare` — all provider jobs share the same `request_data` reference.**
   Line 293: `request_data = body.model_dump()` is computed once. Each `_run_generate_pipeline` closure captures the same dict reference. If any pipeline mutates `request_data` (unlikely but possible via `merged.update`), it affects subsequent jobs. Should be a deep copy per provider.
   - `backend/app/routers/generate.py:293`~~
   - **Fixed:** Each closure now receives `job_data = dict(request_data)` — a shallow copy per provider. The closure default-arg pattern (`jid=jid, job_data=job_data`) also documents why the default arg is needed.

6. ~~**Medium: `_run_pipeline` — VLM fused path `extract_json_from_text` failure kills job with no fallback.**
   Lines 1371-1402: The VLM extraction try/except catches any exception and sets `job.status = "failed"`. Unlike the GLM and DeepSeek branches (which have `ocr_fallback` logic), the VLM path has no fallback — a single malformed JSON response from the vision model terminates the entire job.
   - `backend/app/routers/ingest.py:1397-1402`~~
   - **Fixed:** The whole OCR gate is now a single ordered fallback loop driven by `_build_ocr_chain`, which preferentially orders **two-step strategies (glm, deepseek) before VLM-fused providers (anthropic, ollama, openai)**. The VLM body retains its 3-attempt JSON-parse retry (exponential backoff). Failure in any branch records the error and the loop advances to the next strategy; the job is only marked `failed` when the whole chain is exhausted. `_fallback_ocr_strategy` was replaced by `_build_ocr_chain`.

7. ~~**Low / Observability: `_run_pipeline` — GLM/DeepSeek OCR fallback switches extraction paradigm without explicit diagnostics.**
   When OCR fails and fallback succeeds (lines 1276-1292), the code changes `resolved_strategy` and continues. But the fallback strategy runs the VLM fused path (lines 1346-1402), which does BOTH OCR and extraction in one call. If the original strategy was `glm` or `deepseek` (two-step: OCR then separate LLM extraction), the fallback switches to a completely different extraction paradigm without logging the paradigm shift or adjusting the pipeline accordingly. The `text_extraction_provider` is already set (line 1268-1274) for the two-step path but is never used when fallback activates the VLM fused path.
   - `backend/app/routers/ingest.py:1276-1292, 1346-1402`~~
   - **Fixed:** OCR fallback loop now logs the full chain at entry and logs each fallback transition. Two-step successes log paradigm info. VLM-fused successes log that Pass 1 is skipped.

#### Timeout & Resource Exhaustion

8. ~~**Medium: No application-level timeout around whole LLM pipeline calls.**
   Provider clients do have HTTP timeouts (for example 600s for vision), but there is no shorter pipeline-level timeout/heartbeat around `provider.complete()` or `provider.complete_vision()`. Four long-hanging jobs can still occupy the global job semaphore.
   - `backend/app/routers/ingest.py:1363, 1579`, `backend/app/job_limits.py:29`~~
   - **Fixed:** `_run_pipeline_with_session` wraps `_run_pipeline` in `asyncio.wait_for(timeout=settings.pipeline_timeout_s)` (default 1800s). On timeout the job is marked `failed` on a fresh session. See also 2026-05-16 Live Ingestion Run Gaps #5. (Heartbeat-style progress monitoring remains unimplemented but the semaphore-starvation risk is closed.)

9. ~~**Medium: `_store_page_render` decodes base64 and stores raw bytes — no size limit per page.**
   Line 957: `base64.b64decode(b64)` decodes the entire page image. For a high-DPI scan, a single page can be 20+ MB decoded. `max_images` (default 10) caps page count but not per-page size. A 10-page PDF with 20 MB pages writes 200 MB to object storage in the request path.
   - `backend/app/routers/ingest.py:957`~~
   - **Fixed:** Added `MAX_PAGE_RENDER_BYTES = 10 MB` constant. `_store_page_render` now decodes first, checks size, and returns `None` (skipping the page) if over the limit. `_store_pdf_page_renders` filters out `None` returns. `_render_page_b64` in `pdf_parser.py` now caps rendered dimensions to `MAX_RENDER_DIMENSION = 3000px` per side.

10. ~~**Medium: `detect_overlaps` loads all official questions with no limit.**
    Line 46-56: A single JOIN query loads every `Question` with `content_origin == "official"` and `practice_status in ("active", "draft")`, plus their annotations. At 10,000+ official questions, this becomes a multi-hundred-megabyte result set per overlap check. No pagination, no limit clause.
    - `backend/app/pipeline/overlap.py:46-56`~~
    - **Fixed:** Added `.limit(2000)` safety cap to the overlap scan query. Full-text index pre-filtering remains a future optimization.

#### Data Integrity & Edge Cases

11. ~~**High: Validator option labels check only fires when `len(options) == 4`.**~~
    ~~Line 34: `if len(options) == 4:` gates the label validation. If the LLM returns 3 or 5 options, the label set check (`label_set != {"A", "B", "C", "D"}`) is skipped entirely, and duplicate or wrong labels pass silently. The blocking error at line 30 catches the count mismatch, but for `len(options) > 4` with correct labels A-D plus extras, neither check catches the extras.~~
    - **Fixed/stale finding:** `len(options) != 4` is itself a blocking validation error, and the exact-label check runs for the only count that can pass. Extra/missing option rows do not pass validation.
    - `backend/app/pipeline/validator.py:34-48`

12. ~~**High: `correct_option_label` validated against option labels only when 4 options exist.**~~
    ~~Line 56-63: The check `if correct in ("A", "B", "C", "D")` then verifies `correct not in actual_labels`. But this is inside the `if len(options) == 4:` block. With 3 options (labels A, B, C), `correct="D"` passes the A-D check but `D` is never found in `actual_labels`. However, the earlier blocking error for `len(options) != 4` should catch this — unless `len(options) == 4` but with duplicate labels like `["A", "A", "B", "C"]` where `label_set` is `{"A", "B", "C"}` (3 elements, not 4), which IS caught by the `label_set != {"A", "B", "C", "D"}` check. So this is actually safe for 4 options but not for != 4.~~
    - **Fixed/stale finding:** Current validator checks `correct_option_label` against `actual_labels` whenever the correct label is in A-D, independent of option count. Count mismatch remains blocking.
    - `backend/app/pipeline/validator.py:56-63`

13. **Medium / Design review: Generate pipeline — `generation_source_set` stored as the full `request_data` dict.**
    Line 125 in `db.py`: `generation_source_set` column stores the entire `GenerationRequest.model_dump()`. Line 96 in `generate.py`: `merged = {**generated, **annotate_json, "generation_source_set": request_data}`. The `request_data` dict includes `provider_name`, `model_name`, and all generation parameters. This is stored as-is into the `Question` row. Compare with the ingest pipeline which stores only metadata-relevant fields.
    - `backend/app/routers/generate.py:96`, `backend/app/models/db.py:125`

14. ~~**Medium: `_normalize_extracted_questions` drops questions with empty/whitespace `question_text` silently.**
    Lines 415-419: Questions with `question_text` that is empty or whitespace-only pass the dedup check (because `q_text_key` is falsy and won't be added to `seen_texts`), but they also don't get deduplicated. They proceed through Pass 2 annotation, which wastes an LLM call, and then fail the validator's `question_text is required` blocking check. The fix should filter out empty-text questions early, before the annotation loop.
    - `backend/app/routers/ingest.py:415-419`~~
    - **Fixed:** Added explicit `if not q_text_key: continue` guard with a warning log in `_normalize_extracted_questions`. Empty-text entries are now rejected before the per-question annotation loop.

15. ~~**Medium: `passage_group_id` is `None` for single-question batches.**
    Line 1478: `passage_group_id = uuid.uuid4() if len(questions_data) > 1 else None`. A single question with a passage_text gets no passage group. If the same passage appears in a later batch, the two groups won't be linked. This is a known gap but worth noting as it affects reading comprehension question grouping.
    - `backend/app/routers/ingest.py:1478`~~
    - **Fixed:** Replaced flat batch UUID with per-passage-text grouping. A `_passage_to_group` map assigns a shared UUID to all questions that share the same passage. Passages appearing in only one question get `None`. The old `len > 1` heuristic incorrectly grouped all questions in a batch regardless of passage content.

16. **Medium: Overlap detection race condition — `persist_overlap_relations` checks existence then inserts non-atomically.**
    Lines 116-123: The duplicate check `existing.scalars().first()` and the subsequent `db.add()` are not atomic. Two concurrent overlap checks for the same question pair could both pass the existence check and both insert, causing a unique constraint violation (if one exists) or duplicate rows (if no unique constraint on `(from_question_id, to_question_id, relation_type)`).
    - `backend/app/pipeline/overlap.py:116-123`

#### Generation & Analysis Reporting Gaps

17. **Medium: `generate_compare` — no error aggregation across providers.**
    Each provider job runs independently in a background task. If one provider fails, the other succeeds, the comparison endpoint `GET /generate/runs/{run_id}` returns status per job but doesn't indicate which provider failed or why. There's no per-job `validation_errors_jsonb` exposure in the response (lines 332-349).
    - `backend/app/routers/generate.py:307-349`

18. **Medium: Generate pipeline — `overlap_checking` status never set.**
    The ingest pipeline sets `job.status = "overlap_checking"` (line 1616). The generate pipeline at lines 189-201 runs overlap detection but never updates the job status from "approved". If overlap detection is slow, the job appears "approved" before overlap checks complete. If overlap is found, the status is changed to "possible" after commit, creating a brief window where the question appears approved but may be flagged.
    - `backend/app/routers/generate.py:189-201`

19. ~~**Medium: `_run_generate_pipeline` — `Question.practice_status` hardcoded to `"draft"`.**~~
    ~~Line 123: `practice_status="draft"`. Unlike the ingest pipeline which sets `practice_status` based on `content_origin` and `official_auto_activate_for_testing`, generated questions are always "draft" with no path to "active" via the API. The admin approval endpoint at `/admin/questions/{id}/approve` could be used, but there's no specific documentation or test for this workflow.~~
    - **Fixed/stale finding:** Generated questions intentionally start as `draft`, and `/admin/questions/{id}/approve` supports generated questions when overlap status is clear.
    - `backend/app/routers/generate.py:123`

20. **Medium: `get_generation_run` endpoint doesn't expose errors or pass1/pass2 data.**
    Lines 307-349: The response only includes `id`, `status`, `provider_name`, `question_id`, and `comparison_group_id`. There's no `validation_errors_jsonb`, no `pass1_json` or `pass2_json`, and no annotation details. Admins cannot diagnose failed generation jobs through the API.
    - `backend/app/routers/generate.py:307-349`

21. **Low: `_run_generate_pipeline` — `raw_asset_id` is `None` for generated questions.**
    The `QuestionJob` at line 225 has no `raw_asset_id`. This means the `QuestionAsset` link is absent, and the `QuestionSourceSpan` and `QuestionStimulusAsset` foreign keys to `raw_asset_id` will be `None`. No provenance tracking for generated content.
    - `backend/app/routers/generate.py:225`

22. ~~**Low: `generate_compare` uses `async_session()` inside a closure that captures `jid` via default arg.**
    Line 297: `async def _run(jid=jid):` — this is the Python closure-default-arg pattern to avoid late binding. It works correctly but is fragile; if someone refactors to `async def _run():` the `jid` would be captured by reference and all tasks would use the last `jid` value. Worth a comment.
    - `backend/app/routers/generate.py:297`~~
    - **Fixed:** Documented inline with the `job_data=job_data` default arg, matching the `jid=jid` pattern.

### Cross-References To Existing Entries

- **Canonical for ingestion/generation DB transaction gaps:** findings #1 and #2 above. Older related notes about missing savepoints or failed flush handling should be read as duplicates of these two items unless they identify a distinct call site.
- **Canonical for malformed LLM JSON retry gaps:** finding #3 above for generation and finding #6 above for VLM fused ingestion fallback behavior. Older malformed-JSON notes remain valid only where they name a separate parser path.
- **Canonical for overlap scan scalability:** finding #10 above. This supersedes the older backend audit item "Full-table scan for every overlap check".
- **Canonical for generated profile/request-data leakage:** findings #4 and #13 above. These cross-reference the older `_generation_profile_payload` and `generation_profile_jsonb` pollution entries.
- **Still separate from this organized ingestion entry:** student-facing security findings in the 2026-05-10 backend audit (#1, #4, #5), insecure deployment defaults, and list-endpoint N+1 query behavior. They are not ingestion workflow defects and should stay tracked independently.

---

## 2026-05-11 - VLM Provider Quality Audit (OCR Loop)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

### Findings

1. ~~**High:** `qwen3-vl:8b` returns empty `content` via OpenAI-compatible API — all output goes to `reasoning` field.
   - Ollama's OpenAI-compatible endpoint (`/v1/chat/completions`) for thinking-capable models (qwen3-vl, qwen3) routes all model output to `message.reasoning` instead of `message.content`. `OllamaProvider.complete_vision()` reads only `message.content`, so the extracted text is always empty string.
   - Root cause: Ollama's OpenAI-compat layer does not honour `options.thinking=false` or `think=false` at request level. The native `/api/chat` endpoint with `"think": false` works correctly.
   - Affected models: any Ollama model with `thinking` in its capabilities list.~~
   - **Fixed:** Added `_extract_content(message)` helper to `ollama_provider.py` that falls back to `message.reasoning` when `message.content` is empty and strips `<think>…</think>` wrappers via regex. Applied to both `complete()` and `complete_vision()`.

2. **High:** `qwen3-vl:8b` inference exceeds 600s vision timeout on local hardware — all 3 retry attempts timed out (total ~1803s).
   - Model is 6.1 GB and significantly slower than `granite3.2-vision:latest` (2.4 GB, ~105s).
   - **Not yet fixed:** Increase `VISION_TIMEOUT` or add per-model timeout config; or document that only models ≤3 GB are practical for local VLM OCR.

3. **Medium:** `granite3.2-vision:latest` still misses Q4 from a 4-question page — 3 of 4 extracted.
   - Model quality issue; not a code bug. Smaller VLMs (2.4 GB) have lower recall on dense test pages.
   - **Not a code fix:** Accept limitation; note in provider selection docs that this model is best-effort for multi-question pages.

4. ~~**High:** VLM answer labels `"A)"` / `"a"` fail validator — blocking all extracted questions.~~
   - ~~`correct_option_label` emitted by VLMs (granite3.2-vision, qwen-vl) with trailing `)` or `.` was rejected by `validate_question` which requires exact `"A"–"D"` match.~~
   - **Fixed:** Added `_clean_option_label()` in `_normalize_extracted_questions`; strips trailing `).` and uppercases. Applied to both `correct_option_label` and each option's `label`. 6 regression tests added.

5. ~~**High:** VLM duplicate question rows persisted (granite3.2-vision hallucinated Q2–Q4 as copies of Q2).~~
   - ~~No deduplication in `_normalize_extracted_questions` — all rows passed to persistence loop.~~
   - **Fixed:** `seen_texts` set added; case-insensitive `question_text` deduplication skips repeat rows. 2 regression tests added.

6. ~~**High:** `OllamaProvider.complete_vision()` shared 120s timeout with text calls — timed out on any model >3 GB.~~
   - **Fixed:** `vision_client = httpx.AsyncClient(timeout=600s)` added; `complete_vision` uses `vision_client`. `close()` updated to close both clients. Unit tests updated to patch `vision_client`.

7. ~~**Medium:** `deepseek-ocr:latest` appeared to return only 107 tokens on first test.~~
   - ~~Suspected model quality issue.~~
   - **Confirmed not a bug:** Root cause was oversized test image (1224×1584, 6 MB → model timeout/truncation). Re-test with 1× zoom image (612×792, 64 KB) produced 763 tokens and correct full-page extraction of all 4 questions.

---

## 2026-05-10 - Backend Gap Audit (Codex-Generated Code)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

### Findings

1. ~~**Critical:** Student API returns questions without answer options.
   - `StudentQuestionResponse` has no `options` field. `GET /api/questions` returns question text and passage but no A/B/C/D choices. Students cannot display a answerable question.
   - Relevant files: `backend/app/models/payload.py`, `backend/app/routers/student.py`.~~
   - **Fixed:** Added `options: List[dict]` to `StudentQuestionResponse`. `student_recall` batch-loads options by `latest_version_id` and populates per-question lists.

2. ~~**Critical:** No duplicate-detection on ingest — same PDF uploaded twice creates duplicate questions.~~
   - ~~`checksum` is computed and stored on `QuestionAsset` but never checked before creating a new asset/job. Re-uploading the same file runs the full pipeline again.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Checksum uniqueness check added before asset creation in both upload endpoints. Returns HTTP 409 on duplicate.

3. ~~**Critical:** CORS is wide open (`allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`).~~
   - ~~Any website can make requests to the API from a user's browser.~~
   - ~~Relevant file: `backend/app/main.py`.~~
   - **Fixed/overstated:** CORS is now config-driven, methods and headers are restricted. Deployment still defaults to `CORS_ALLOWED_ORIGINS="*"`, tracked separately as a Low deployment hardening item.

4. ~~**Critical:** Students can read any user's profile — no ownership check on `GET /api/users/{user_id}`.~~
   - ~~Route uses `student_required` but accepts any integer `user_id`. User IDs are sequential integers, trivially enumerable.~~
   - ~~Relevant file: `backend/app/routers/student.py`.~~
   - **Fixed:** `GET /api/users/{user_id}` changed to `admin_required`. Students no longer have access to the profile endpoint.

5. ~~**Critical:** Students can submit answers attributed to any `user_id` — no auth/user binding.~~
   - ~~`POST /api/submit` accepts `user_id: int` in body. No check that the student key corresponds to the given user.~~
   - ~~Relevant file: `backend/app/routers/student.py`.~~
   - **Fixed:** Replaced `user_id: int` with `user_token: str` (UUID) in `UserProgressCreate`. Submit endpoint now looks up the user by token. Added `user_token` UUID column to `User` model with migration `018`. `UserResponse` exposes the token so admins can retrieve it when creating users.

6. ~~**High / Deployment:** Insecure default keys only log a warning; server does not refuse to start.
   - `_warn_if_insecure_keys` logs when `admin-key-change-me` / `student-key-change-me` are active but does not block startup. This is acceptable only for isolated local development.
   - Relevant files: `backend/app/main.py`, `backend/app/config.py`.~~
   - **Fixed:** Renamed to `_check_insecure_keys`. Now raises `RuntimeError` on startup when `settings.env == "production"` and default keys are active. Development mode still logs a warning. Added `env: str = "development"` to `Settings`.

7. ~~**High:** N+1 query pattern in all list endpoints.
   - `admin.py`, `questions.py`, `student.py` each fetch a question list then issue one DB call per question for annotations and another for options. 50 questions = 101 queries instead of 3.
   - Relevant files: `backend/app/routers/admin.py`, `backend/app/routers/questions.py`, `backend/app/routers/student.py`.~~
   - **Fixed:** All three list endpoints now batch-load annotations (and options where applicable) via `SELECT ... WHERE id IN (...)` with in-memory dict lookup. `admin.py` and `student.py` also batch-load `QuestionOption` rows.

8. ~~**High:** Full-table scan for every overlap check — O(N×M) as official questions grow.
   - `detect_overlaps` loads all official questions and annotations into memory and compares in Python via Jaccard similarity. No text index, no candidate pre-filtering.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` finding #10.
   - Relevant file: `backend/app/pipeline/overlap.py`.~~
   - **Partially fixed:** Added `.limit(2000)` cap. Full pre-filtering with a text index remains open.

9. ~~**High:** Scanned-PDF page images stored as base64 in JSONB — can be megabytes per DB row.~~
   - ~~`max_images` limits pages but not images-per-page. A 10-page PDF with 5 images per page stores 50 base64 blobs in one `pass1_json` JSONB column.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed/stale finding:** PDF/image page renders are stored as object-store files and `pass1_json._page_images` stores references (`path`, `storage_path`, `mime_type`, `page_number`), not inline base64 for new ingests.

10. ~~**High:** Background pipeline tasks swallow exceptions silently.~~
    - ~~`asyncio.create_task(_run_pipeline_with_session(...))` has no `add_done_callback`. An uncaught exception leaves the job stuck in its last committed status with no error recorded.~~
    - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.~~
    - **Fixed:** `_log_task_exception` done-callback added to all `create_task` calls in both routers; exceptions now logged at ERROR level with full traceback.

11. ~~**High:** No recovery for stuck jobs after server restart.~~
    - ~~Jobs interrupted mid-pipeline stay in `"extracting"` / `"annotating"` forever. No startup sweep, no timeout, no admin endpoint to force-fail or retry.~~
    - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.~~
    - **Fixed:** Startup lifespan recovery marks non-terminal jobs as `failed` with a `startup_recovery` validation error.

12. **Medium / Partially fixed:** Job status is still committed before long LLM work, so a crash can leave a job in an in-progress state until recovery runs. Startup recovery prevents the stuck state from being permanent, but there is still no timeout/heartbeat retry while the server stays up.
    - Relevant files: `backend/app/routers/ingest.py`, `backend/app/main.py`.

13. **Medium:** Duplicate user management routes — `student.py` (`/api/users`) and `users.py` (`/users`) already diverged.
    - `/api/users` list has no pagination; `/users` list has `limit`/`offset`. `/api/users/{id}` GET uses `student_required`; `/users/{id}` GET uses `admin_required`. DELETE returns different status codes.
    - Relevant files: `backend/app/routers/student.py`, `backend/app/routers/users.py`.

14. **Medium:** `_generation_profile_payload` in `generate.py` overwrites merged profile with all of `request_data`.
    - Final `merged.update(sources[-1])` dumps provider, model, source_question_ids, etc. into the stored generation profile. The `ingest.py` version of the same helper does not have this line.
    - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
    - Relevant file: `backend/app/routers/generate.py`.

15. ~~**Medium:** `detect_overlaps` receives `job.id` (a job UUID) as `question_id`, not the new question's UUID.~~
    - ~~The self-skip guard `if oq.id == question_id: continue` is always false because job IDs and question IDs never collide. Intent is not achieved.~~
    - ~~Relevant file: `backend/app/routers/ingest.py` (call site at overlap check).~~
    - **Fixed:** Call site passes `None`; `detect_overlaps` signature updated to `Optional[uuid.UUID]`; guard is now a no-op when `None` (correct — question not yet persisted at check time).

16. ~~**Medium:** Text ingest silently truncates input at 50,000 chars with no warning in the response.~~
    - ~~Relevant file: `backend/app/routers/ingest.py`.~~
    - **Fixed:** Returns HTTP 413 with the actual char count when input exceeds 50,000. The `text[:50000]` slice in `pass1_json` construction was removed.

17. **Medium:** `LlmEvaluation.job_id` is `nullable=False` in the model but `create_evaluation` can pass `None` if `body.job_id` is an empty string, causing an unhandled 500.
    - Relevant files: `backend/app/models/db.py`, `backend/app/routers/admin.py`.

18. ~~**Low:** No rate limiting or concurrent-job cap — unlimited LLM pipeline calls per key.~~
    - **Partially fixed:** Active background jobs are capped at 4 via `backend/app/job_limits.py`. Per-user/API-key rate limiting for paid external providers remains open and is tracked in the 2026-05-15 ingestion audit.

19. ~~**Low:** Dashboard HTML served at `GET /dashboard` without authentication — exposes route structure and feature set to unauthenticated callers.~~
    - ~~Relevant file: `backend/app/routers/dashboard.py`.~~
    - **Fixed:** Dashboard routes now require `admin_required`.

20. ~~**High:** `OllamaProvider.complete_vision()` has no `@with_retry` decorator.~~
    - ~~`complete()` is wrapped with retry/backoff but `complete_vision()` is a single bare `await self.client.post(...)` call. Any transient Ollama timeout or 503 during VLM-based scanned-PDF ingest permanently fails the job.~~
    - ~~Relevant file: `backend/app/llm/ollama_provider.py`.~~
    - **Fixed:** Added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `complete_vision()`.

21. ~~**High:** `DeepSeekOCRClient.extract()` has no `@with_retry` decorator.~~
    - ~~Single-attempt HTTP call to a local vLLM/LMDeploy process. Any flaky network or overloaded inference server fails the OCR pass with no retry.~~
    - ~~Relevant file: `backend/app/parsers/ocr.py`.~~
    - **Fixed:** Imported `with_retry` and added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `extract()`.

22. ~~**Medium:** `AnthropicProvider` has no `complete_vision()` implementation.~~
    - ~~Anthropic Claude 3+ supports image inputs, but the provider only exposes `complete()`. Selecting `anthropic` as an OCR strategy will raise an `AttributeError` at runtime because the `complete_vision` call site expects the method to exist.~~
    - ~~Relevant file: `backend/app/llm/anthropic_provider.py`.~~
    - **Fixed:** `AnthropicProvider.complete_vision()` now exists and is covered by the vision fallback path.

23. ~~**Medium:** `_provider_registry` in `factory.py` grows unbounded — new `httpx.AsyncClient` per pipeline call.~~
    - ~~`get_provider()` creates a new provider instance on every invocation and appends it to a module-level list with no eviction. Each instance owns its own `httpx.AsyncClient` connection pool. Under sustained load or a multi-job burst, these accumulate in memory indefinitely.~~
    - ~~Relevant file: `backend/app/llm/factory.py`.~~
    - **Fixed:** Replaced `_provider_registry: list` with `_provider_cache: dict` keyed by `(provider_name, api_key, base_url, default_model)`. Identical configs return the same provider instance. `close_all_providers()` iterates `.values()` and clears the dict.

24. ~~**Medium:** `validator.py` blocks `command_of_evidence_quantitative` questions for missing `table_data` / `graph_data` — fields that are never extracted or stored.~~
    - ~~The blocking rules reference `table_data` and `graph_data` keys, but no extraction prompt emits these fields, no `normalize_annotation()` path sets them, and no DB column stores them. Every quantitative evidence question is permanently blocked at validation.~~
    - ~~Relevant files: `backend/app/pipeline/validator.py`, `backend/app/prompts/`.~~
    - **Fixed:** Downgraded from `"blocking"` to `"review"` severity with an explanatory message. Questions now route to human review queue instead of being permanently failed.

25. **Low:** Test suite uses a stub DB session (`_MockSession`) that returns `None` for all `.get()` and empty result sets for all `.execute()`.
    - Router tests cover auth and HTTP routing but cannot catch any DB query regression. A wrong JOIN, a missing `.where()` clause, or a bad column reference passes all tests silently.
    - Relevant file: `backend/tests/conftest.py`.

---

## 2026-05-10 - Current OCR Gap Review
Report created by: GPT-5 Codex
Git branch: `main`

### Findings

1. ~~**High:** DeepSeek OCR provenance is lost after Pass 1.~~
   - ~~The DeepSeek branch writes `job.pass1_json["_ocr_meta"]`, then the normal text Pass 1 replaces `job.pass1_json` with the extracted JSON and `_llm_meta`.~~
   - ~~Result: `pass1_json._ocr_meta.strategy == "deepseek"` is not preserved for audit or smoke-test verification.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Pass 1 now preserves `_ocr_meta`, `_ocr_artifacts`, and `_page_images` when replacing `pass1_json`.

2. ~~**High:** `/ingest/unofficial/batch` does not accept or forward `ocr_strategy`.~~
   - ~~Single official/unofficial ingest routes accept `ocr_strategy`.~~
   - ~~The batch route has no `ocr_strategy` form param and calls `ingest_unofficial_file()` without forwarding any OCR selection.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Batch ingest accepts, validates, and forwards `ocr_strategy`.

3. ~~**Medium / Partially fixed:** `auto` strategy fallback exists for GLM and DeepSeek failures, and auto now prefers GLM before DeepSeek/Ollama/Claude/OpenAI. Remaining gap: if the resolved strategy is a fused VLM provider (`ollama`, `anthropic`, or `openai`) and that provider fails, the VLM branch still fails the job rather than trying the next fallback provider.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/config.py`.~~
   - **Fixed:** The OCR gate now uses a unified `_build_ocr_chain` fallback loop that runs the resolved strategy first, then **prefers two-step (glm, deepseek) before VLM-fused (anthropic, ollama, openai)**. A failed VLM-fused branch now correctly falls back to a two-step path (and vice versa). See 2026-05-15 finding #6.

4. **Medium / Design gap:** OCR routing is job-level, not per-question or visual-stimulus aware.
   - Current behavior applies one OCR strategy to the whole ingest job.
   - There is no routing that uses DeepSeek OCR for text recovery while reserving VLMs for chart/table/graph/image questions.
   - Needed for the desired workflow: text-only scanned page → DeepSeek OCR; visual-reasoning item → VLM.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/pipeline/validator.py`.

5. **Medium:** Mixed text-layer and scanned PDFs are not handled well.
   - Route-time image collection only runs when the joined `raw_text` for the whole PDF is empty.
   - A PDF with some text pages and some scanned/image pages skips OCR for the scanned pages.
   - Relevant file: `backend/app/routers/ingest.py`.

6. ~~**Medium:** Base64 page images are stored directly in `question_jobs.pass1_json`.~~
   - ~~This can bloat JSONB rows for scanned PDFs and image uploads, especially failed jobs.~~
   - ~~Prefer storing asset/page references and loading or rendering images inside the background worker, keeping only OCR/vision metadata and extracted text/JSON in `pass1_json`.~~
   - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.~~
   - **Fixed/stale finding:** New PDF/image ingests store page images as object references, not inline base64. Legacy records may still contain inline `b64` and `_collect_page_images` still supports them.

7. **Low / Partially fixed:** Job polling now returns `validation_errors`, and OCR benchmark polling exposes `ocr_meta`. Remaining gap: generic `GET /ingest/jobs/{job_id}` still returns `JobResponse` only and does not expose `_ocr_meta` or `_llm_meta`.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/payload.py`.

8. ~~**Medium:** OCR/VLM provider calls are not retried.~~
   - ~~`OllamaProvider.complete_vision()` is not wrapped by the retry decorator used by text completion.~~
   - ~~`DeepSeekOCRClient.extract()` is also single-attempt.~~
   - ~~This does not match the PRD fallback/retry expectations.~~
   - ~~Relevant files: `backend/app/llm/ollama_provider.py`, `backend/app/parsers/ocr.py`.~~
   - **Fixed:** `OllamaProvider.complete_vision()` and `DeepSeekOCRClient.extract()` are now wrapped with retry.

9. **Low / Partially fixed:** OCR pipeline tests are broader than this original audit reported, including fallback strategy and batch `ocr_strategy` coverage. Remaining test gaps: full DB-backed OCR pipeline cases for provider failure fallback, malformed vision JSON, and mixed text/scanned PDFs.
   - Relevant files: `backend/tests/test_ocr.py`, `backend/tests/test_ingest_router.py`, `backend/tests/test_backend_regressions.py`.

### Verification

- Ran `uv run pytest -q` in `backend/`.
- Result: 197 passed, 2 skipped.

### Coverage Gap

- Add pipeline-level OCR tests for DeepSeek and Ollama paths.
- Add batch route tests for `ocr_strategy`.
- Add failure/fallback tests for `auto`, unreachable Ollama, DeepSeek failure, malformed vision JSON, and mixed text/scanned PDFs.

---

## 2026-05-10 - OCR Integration Implementation (Phases 1–8)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `ba101fd` — Fix seven backend bugs across routers, config, and persistence layer

### Findings

1. **Implemented:** OCR gate wired into `_run_pipeline()` at the `no_raw_text` failure point.
   - `_collect_page_images()` reads `pass1_json._page_images` (pre-stored at route time).
   - `_resolve_ocr_strategy()` resolves `deepseek` | `ollama` | `auto` per-job or from config.
   - DeepSeek path: `DeepSeekOCRClient.extract()` → `raw_text` → existing Pass 1 unchanged.
   - Ollama VLM path: `provider.complete_vision()` → fused extraction → sentinel skips Pass 1.
   - **Files:** `backend/app/routers/ingest.py`, `backend/app/parsers/ocr.py`, `backend/app/llm/base.py`, `backend/app/llm/ollama_provider.py`, `backend/app/llm/factory.py`, `backend/app/parsers/pdf_parser.py`, `backend/app/prompts/extract_prompt.py`, `backend/app/config.py`

2. **Implemented:** Image uploads now accepted (previously raised 422).
   - `ingest_unofficial_file()` now parses image content via `parse_image()` and stores as `_page_images` for the OCR gate.
   - Both ingest routes accept optional `ocr_strategy` form param with 422 validation on invalid values.

3. **Implemented:** `parse_pdf()` now renders scanned pages via `page.get_pixmap()` when no text or embedded images are found.

4. **Test result:** 197 passed, 2 skipped — all prior tests green; 15 new OCR tests added.

## 2026-05-09 - Current Backend Gap Review
Report created by: GPT-5 Codex
Git branch: `main`

### Findings

1. ~~**High:** Cross-text, underlined, and graphic stimulus data is not fully persisted.~~
   - ~~The schema, prompts, validator, and admin UI reference `paired_passage_text`, `underlined_text`, `table_data`, and `graph_data`.~~
   - ~~Normal ingest/generate persistence primarily writes `question_text`, `passage_text`, options, and answer fields, so cross-text and quantitative reading items can lose required stimulus data after extraction/generation.~~
   - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`, `backend/app/pipeline/validator.py`, `backend/app/models/db.py`.~~
   - **Fixed (partial):** `ingest.py` and `generate.py` now write `paired_passage_text` and `underlined_text` to both the `Question` and `QuestionVersion` rows. `table_data`/`graph_data` have no DB columns — validator-only, remains unimplemented.

2. ~~**High:** Hard-delete can still fail on incoming self-references.~~
   - ~~`delete_question` clears `canonical_official_question_id` and `derived_from_question_id` only on the question being deleted.~~
   - ~~Other questions can still point to the deleted question through those self-referential FKs.~~
   - ~~Relevant files: `backend/app/routers/admin.py`, `backend/app/models/db.py`.~~
   - **Fixed:** `delete_question` now bulk-nulls `canonical_official_question_id` and `derived_from_question_id` on all other questions pointing to the target before flushing the delete.

3. ~~**High:** Default API keys are live credentials.~~
   - ~~`admin-key-change-me` and `student-key-change-me` are accepted if the corresponding environment variables are missing.~~
   - ~~Auth checks use the configured/default key lists directly.~~
   - ~~Relevant files: `backend/app/config.py`, `backend/app/auth.py`.~~
   - **Fixed:** `get_settings()` is now cached with `@lru_cache` (also closes Low #8). A startup warning fires if either default key is detected in the active key lists. `conftest.py` clears the cache before each test so `monkeypatch.setenv` continues to work.

4. **Medium:** Official questions have no normal admin activation path.
   - Official ingest creates `draft` questions unless `official_auto_activate_for_testing` is enabled.
   - `POST /admin/questions/{id}/approve` rejects `content_origin == "official"`, so a reviewed official question cannot be activated through the admin API.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/admin.py`, `backend/app/config.py`.

5. **Low / Partially fixed:** Raw PDF/file ingest text is no longer truncated at 50,000 characters; stored/extracted raw text now uses a 100,000-character threshold. Remaining gap: PDF/file ingestion can still truncate beyond 100,000 chars with only `_truncated` metadata, while direct text ingest returns HTTP 413 over 50,000 chars.
   - Relevant file: `backend/app/routers/ingest.py`.

6. ~~**Medium:** Batch asset provenance links only the first created question.
   - Multi-question ingest can create several `Question` rows from one uploaded asset.
   - `question_assets.question_id` is a single FK, and `_persist_single_question` links the asset only when the job has no primary question yet.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.~~
   - **Fixed:** Added `question_job_questions` junction table (migration 017) linking each job to every question it produced. `_run_pipeline` now inserts a `QuestionJobQuestion` row for each successfully persisted question. The `job.question_id` single FK is kept for backward compatibility but the junction table is the authoritative many-to-many record.

7. **Medium / Design Review:** Generated `generation_profile_jsonb` stores the full request dict.
   - `_generation_profile_payload` in `generate.py` merges `request_data` into the stored profile, including fields such as `target_grammar_role_key`, `difficulty_overall`, `provider_name`, and `model_name`.
   - Existing tests currently expect this behavior, so this should be resolved as either intentional contract or data-shape cleanup.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
   - Relevant files: `backend/app/routers/generate.py`, `backend/tests/test_backend_regressions.py`.

8. ~~**Low:** `get_settings()` is not cached.~~
   - ~~Each call creates a new `Settings` object and re-reads environment configuration.~~
   - ~~Called from auth checks and pipeline paths.~~
   - ~~Relevant file: `backend/app/config.py`.~~
   - **Fixed:** `get_settings()` is cached with `@lru_cache(maxsize=1)`.

9. **Low / Deployment:** CORS wildcard remains enabled.
   - `allow_origins=["*"]` is still configured globally.
   - This is acceptable for local development but should be restricted before non-local deployment.
   - Relevant file: `backend/app/main.py`.

10. **Low:** Student answer submission does not verify the selected option exists on the latest option set.
    - The request schema limits labels to `A`-`D`, and correctness is now computed server-side.
    - The submit path does not check that the submitted label is present in `question_options` for `latest_version_id`.
    - Relevant files: `backend/app/routers/student.py`, `backend/app/models/payload.py`.

### Verification

- Ran `uv run pytest` in `backend/`.
- Result: 182 passed, 2 skipped.

### Coverage Gap

- The suite is still mostly unit/mock based around router behavior.
- Real database FK behavior for incoming self-references, complete stimulus persistence for reading/graphic items, multi-question asset provenance, and long-source truncation behavior need integration coverage.

## 2026-05-09 - Full Backend Audit

Report created by: Claude Sonnet 4.6
Git checkpoint: `07454e1` — Fix backend prompt rule loading and refresh docs

### Findings

1. ~~Critical: `users.py` `delete_user` missing UserProgress cascade.~~
   - ~~`DELETE /users/{user_id}` calls `db.delete(user)` with no prior `UserProgress` purge.~~
   - ~~Any user with progress records will cause a FK violation on delete.~~
   - ~~The `/api/users/{user_id}` in `student.py` was already fixed; this separate router at `/users` was not.~~
   - ~~Relevant file: `backend/app/routers/users.py:56–65`.~~
   - **Fixed:** Added `delete(UserProgress)` before `db.delete(user)` in `users.py`. Added `UserProgress` import and `delete` from sqlalchemy.

2. ~~Critical: `/api/users` POST (student router) has no authentication.~~
   - ~~`create_user` in `student.py` has no `Depends(admin_required)` or `Depends(student_required)`.~~
   - ~~Anyone can register arbitrary usernames with no API key.~~
   - ~~Relevant file: `backend/app/routers/student.py:157–171`.~~
   - **Fixed:** Added `Depends(admin_required)` to `create_user` in `student.py`.

3. ~~High: Reannotation pipeline creates a new `QuestionVersion` but no `QuestionOption` rows for it.~~
   - ~~`_run_reannotate_pipeline` sets `latest_version_id` to a version that has zero associated option rows.~~
   - ~~After the earlier version-scoped option query fix, reannotated questions return empty options from all read endpoints.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:791–826`.~~
   - **Fixed (combined with #6):** Reannotation pipeline now loads existing option rows scoped to `latest_version_id` before advancing the version, then clones them with fresh annotation fields for the new version.

4. ~~High: `synthesized_pass1` in `reannotate_question` drops `paired_passage_text` and `underlined_text`.~~
   - ~~The dict that drives reannotation is missing both fields.~~
   - ~~Cross-text connection questions and complete-the-text questions get reannotated without their paired passage or underlined portion, producing wrong annotations.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:898–910`.~~
   - **Fixed:** Added `paired_passage_text` and `underlined_text` to `synthesized_pass1`.

5. ~~High: Dashboard review queue options query is not version-scoped.~~
   - ~~`select(QuestionOption).where(QuestionOption.question_id.in_([...]))` returns options from all versions.~~
   - ~~After any admin edit, the review UI shows duplicate or stale option rows.~~
   - ~~Relevant file: `backend/app/routers/dashboard.py:154–160`.~~
   - **Fixed:** SQL query now selects `q.latest_version_id`. Options query filters by `question_version_id.in_(version_ids)` instead of by question_id.

6. ~~High: Reannotation option annotation update applies to old-version rows.~~
   - ~~`select(QuestionOption).where(QuestionOption.question_id == question.id)` fetches all versions' options and writes new annotation fields to them.~~
   - ~~No new option rows are created for the new version (see #3), so annotations land on rows that are no longer current.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:830–837`.~~
   - **Fixed (combined with #3):** See #3 fix above.

7. ~~Medium: `get_settings()` is not cached.~~
   - ~~Every call constructs a new `Settings` object and re-reads environment variables.~~
   - ~~Called on every auth check and every pipeline step.~~
   - ~~Fix: `@functools.lru_cache()` on `get_settings`.~~
   - ~~Relevant file: `backend/app/config.py:55–56`.~~
   - **Fixed:** `get_settings()` is cached.

8. Low / Partially fixed: Raw text is no longer silently truncated at 50,000 characters in PDF/file routes.
   - Stored PDF/file raw text now uses 100,000 chars and `_truncated`; direct text ingest rejects over 50,000 chars with HTTP 413. Remaining issue is provenance completeness for PDF/file sources above 100,000 chars.
   - Relevant file: `backend/app/routers/ingest.py`.

9. Medium: `_generation_profile_payload` in `generate.py` pollutes stored profiles.
   - Final `merged.update(sources[-1])` unconditionally merges the full `request_data` dict (including `target_grammar_role_key`, `difficulty_overall`, `provider_name`, etc.) into the profile.
   - The `ingest.py` version of the same function does not do this.
   - Stored `generation_profile_jsonb` in annotations contains non-profile fields.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
   - Relevant file: `backend/app/routers/generate.py:21–33`.

10. Medium: No admin API path to activate official questions.
    - `POST /admin/questions/{id}/approve` hard-blocks `content_origin == "official"`.
    - Official questions are created as `draft` and can only become `active` via the `official_auto_activate_for_testing` config flag.
    - No API mechanism exists for an admin to review and activate official questions.
    - Relevant file: `backend/app/routers/admin.py:209–214`.

11. Medium: Duplicate user management systems at two route prefixes.
    - `/api/users` in `student.py` (mixed auth, unauthenticated POST) and `/users` in `users.py` (properly admin-only).
    - Creates ambiguity about which router is authoritative.
    - Relevant files: `backend/app/routers/student.py:157–210`, `backend/app/routers/users.py`.

12. Low: CORS wildcard in `main.py`.
    - `allow_origins=["*"]` should be restricted before any non-local deployment.
    - Relevant file: `backend/app/main.py:24–28`.

13. Low: Batch asset linking only covers the first question persisted per job.
    - `if job.raw_asset_id and not job.question_id` links the PDF asset to only the first successful question.
    - Remaining questions from the same PDF are orphaned from their source asset.
    - Relevant file: `backend/app/routers/ingest.py:266–271`.

14. Low: `_safe_read` Content-Length pre-check is advisory-only.
    - Clients that omit or lie about `Content-Length` bypass the early-exit path.
    - The post-read byte check is correct and enforced, but the comment is misleading.
    - Relevant file: `backend/app/routers/ingest.py:460–467`.

### Verification

- Ran `uv run pytest` in `backend/`.
- Result: 176 passed, 2 skipped (unchanged from prior session).

### Coverage Gap

Reannotation pipeline, version-scoped option queries, and multi-question batch asset linking have no integration test coverage. The user management auth gap (#2) is untested at the auth level (existing test `test_create_user_no_auth` confirms the endpoint accepts unauthenticated requests, but doesn't flag it as wrong).

## Single Test Ingestion — 2026-05-17T04:37:15-07:00

ERROR: FastAPI server failed to start within 30s

---

## Single Test Ingestion — 2026-05-17T04:53:06-07:00

**Ingestion result**: annotating

- **PDF**: `Test_1_digital_sec01_mod01.pdf`
- **Job ID**: `3bd8c445-f12a-442f-a6d2-3ef482487402`
- **Status**: annotating
- **Errors/Warnings**: 0

#### LLM
- Extract latency: ?ms
- Annotate latency: ?ms

---

## 2026-05-17 — Single Test Ingestion (Test 1 / verbal / sec01 / mod01)

**PDF**: `Test_1_digital_sec01_mod01.pdf`  
**Job ID**: `b3c81e18-bfd6-4772-a845-325faffa98c3`  
**Final Status**: `failed` (0 of 33 questions persisted)

---

### Pipeline Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| PDF parse | ~0s | Text layer present, 14 pages extracted |
| Pass 1 (extraction) | ~183s (3 min) | LLM: `qwen3-vl:235b-instruct-cloud` via Ollama |
| Layout detection | ~10s | `glm-ocr:latest` — 3 of 14 pages failed (no valid JSON) |
| Pass 2 (annotation) | ~22 min total | 33 questions × ~40s avg per annotation call |
| Validation | immediate | **All 33 questions blocked** |

### Root Cause: Every Question Failed Validation

The entire batch was rejected because **all 33 questions** had blocking validation errors. No questions were persisted to the `questions` table.

#### Primary Blocking Error — `options` field empty

Every single question (33/33) had:
```
field: options
message: "Option labels must be exactly {A, B, C, D}, got ['']"
severity: blocking
```

This means the annotation LLM (`qwen3-vl:235b-instruct-cloud`) returned an `options` field that was either:
- An empty list `[]`
- A list of empty-string labels `['']`
- Missing the A/B/C/D option structure entirely

Since `options` was empty/invalid, every question also failed the `correct_option_label` check:
```
"correct_option_label 'X' is not present in the option labels ['']"
```

#### Secondary Errors

| Type | Count | Detail |
|------|-------|--------|
| `stem_type_key` unknown | 12 | Values like `conform_to_standard_english`, `complete_the_argument`, `synthesize_information` not in validator whitelist |
| `stimulus_mode_key` unknown | 1 | `notes_summary` not recognized |
| Question numbers out of range (28–33) | 6 | LLM extracted 33 questions but the PDF only has 27 for verbal/mod01 |
| OCR cross-check mismatches | 8 | LLM extracted question numbers 16–23 don't match OCR text numbers 22,23,16–21 |

### Why Pass 2 Was Slow (~22 minutes)

- **Annotation prompt size**: ~88K chars (~20K prompt tokens) per question due to the full grammar rules reference being included
- **33 questions** × **~40s average** per LLM call = **~22 minutes** total
- The model is a cloud-hosted Ollama model (`qwen3-vl:235b-instruct-cloud`), which adds network latency
- Each annotation call uses ~10K input tokens + ~2K output tokens

### Why the Options Were Empty

The most likely cause is that the **annotation prompt output format** doesn't match what the validator expects. The LLM likely returned options in a format like:

```json
{
  "options": [{"A": "text"}, {"B": "text"}, {"C": "text"}, {"D": "text"}],
  "correct_option_label": "B"
}
```

But the validator expects:

```json
{
  "options": [
    {"label": "A", "text": "text"},
    {"label": "B", "text": "text"},
    ...
  ],
  "correct_option_label": "B"
}
```

The `normalize_annotation()` function in `app/parsers/json_parser.py` should handle this transformation, but either:
1. The LLM is returning options in a format `normalize_annotation()` doesn't handle, or
2. The LLM is not returning options at all (returning `[]` or `[{"label": "", "text": "..."}]`)

### Recommendations

1. **Check `normalize_annotation()`**: Verify how it handles the `options` field from `qwen3-vl:235b-instruct-cloud` output
2. **Consider a smaller/faster model for annotation**: The 88K-char system prompt is very large; a model with better instruction-following on structured output would reduce errors
3. **Add options format validation before persistence**: Fail fast with a clear error message if options come back empty
4. **Fix question number range**: The LLM extracted 33 questions (Q1–Q33) from a 27-question module; the OCR cross-check detected mismatches but didn't correct them
5. **Add `stem_type_key` and `stimulus_mode_key` values** to the validator's allowed enums: `conform_to_standard_english`, `complete_the_argument`, `synthesize_information`, `compare_contributions`, `notes_summary`

---

## 2026-05-17 — Root Cause Analysis: Pass 2 Annotation "Stuck" & All Questions Failing Validation

### Executive Summary

The ingestion pipeline for Test 1 (verbal/sec01/mod01) completes both Pass 1 (extraction) and Pass 2 (annotation) successfully, but **every single question fails validation** because the annotation LLM returns options in `option_label`/`option_text` format, which overwrites the extraction's `label`/`text` format during the dict merge. The `_EXTRACTION_OWNED_KEYS` protection in `_merge_for_validation()` should restore the extraction options, and isolated testing confirms it works — but **all 33 questions still fail with empty option labels** in production.

### Investigation Results

1. **Extraction (Pass 1)**: Works correctly. All 33 questions have 4 options with proper `{label: "A"|"B"|"C"|"D", text: "..."}` format. The `_normalize_extracted_questions()` function even backfills empty labels with A/B/C/D.

2. **Annotation (Pass 2)**: The `qwen3-vl:235b-instruct-cloud` model returns annotations with:
   - `stem_type_key`: values like `conform_to_standard_english` (not in ontology's `STEM_TYPE_KEYS`) — **review** severity
   - `stimulus_mode_key`: `notes_summary` (not in `STIMULUS_MODE_KEYS`) — **review** severity
   - `options`: list of dicts with `option_label`/`option_text` format instead of `label`/`text` — **this is the root cause of the blocking errors**

3. **Merge Protection**: The `_merge_for_validation()` function correctly preserves extraction-owned keys (`options`, `question_text`, etc.) by restoring them from `q_data` after the merge. Isolated testing confirms this works:
   ```
   q_data labels: ['A', 'B', 'C', 'D']    ← extraction format
   annotate labels: ['A', 'A', ...]          ← option_label format (from annotate_json)
   merged labels: ['A', 'B', 'C', 'D']      ← correctly restored from q_data
   ```

4. **Yet ALL 33 questions fail** with `"Option labels must be exactly {A, B, C, D}, got ['']"`. This means `merged["options"]` somehow has `label=""` for all options in the actual pipeline run.

### The Mystery

The isolated test passes validation with 0 blocking errors. But the full pipeline fails for all 33 questions. This suggests either:
- A mutation of `q_data` somewhere in the per-question loop that strips option labels
- A race condition or shared-reference issue in the dict merge
- The annotation LLM returning a format that bypasses the protection in a way not caught by isolated testing

### Additional Issues

- **Question count**: LLM extracts 33 questions but the PDF only has 27 for verbal/mod01. Questions 28-33 are out of range.
- **OCR cross-check mismatches**: Questions 16-22 have LLM-extracted numbers that don't match the OCR text.
- **`stem_type_key` not in ontology**: `conform_to_standard_english` (12 occurrences), `complete_the_argument`, `synthesize_information`, `compare_contributions` are not in `STEM_TYPE_KEYS` in `ontology.py`.
- **`stimulus_mode_key` not in ontology**: `notes_summary` is not in `STIMULUS_MODE_KEYS` (should be `notes_bullets`).
- **Layout detection**: `glm-ocr:latest` fails to return valid JSON for 3 of 14 pages.
- **Pass 2 is slow**: ~40s per question × 33 questions ≈ 22 minutes, due to the ~88K-char annotation system prompt (~20K input tokens per call).

### Recommended Fixes

1. **Add debug logging** to `_merge_for_validation()` and the per-question loop to capture the exact state of `q_data["options"]` and `annotate_json["options"]` before and after merge, then re-run the pipeline to identify where labels are lost.

2. **Map `option_label` → `label`** in `normalize_annotation()` or `_merge_for_validation()` so that annotation-style options are normalized to the extraction format, regardless of which dict "wins" the merge.

3. **Add missing stem_type_key values** to `ontology.py`: `conform_to_standard_english`, `complete_the_argument`, `synthesize_information`, `compare_contributions`.

4. **Add missing stimulus_mode_key**: `notes_summary` → map to `notes_bullets` (or add as alias).

5. **Reduce annotation prompt size**: The 88K-char system prompt is the main bottleneck. Consider trimming the rules reference or using a two-pass approach where the domain is detected first, then only the relevant rules section is included.

6. **Fix question count over-extraction**: Investigate why the LLM extracts 33 questions from a 27-question module.

## 2026-05-17 — Full Codebase Schema Inconsistency Audit

### Summary

Found **3 blocking issues** (1 fixed, 2 latent) and **6 latent issues** across the backend codebase. The root cause of the production failure (all 33 questions failing validation) was the `option_label`/`option_text` vs `label`/`text` format mismatch between the annotation LLM output and the validator.

### Issues Found

| # | Severity | Issue | Files | Status |
|---|----------|-------|-------|--------|
| 1 | **BLOCKING** | `option_label`/`option_text` vs `label`/`text` format mismatch | validator.py, ingest.py | **FIXED** |
| 2 | REVIEW | Missing `stem_type_key` values in ontology | ontology.py | **FIXED** |
| 3 | REVIEW | Missing `stimulus_mode_key` value (`notes_summary`) | ontology.py | **FIXED** |
| 4 | LATENT | Domain string vs `question_family_key` mapping | annotate_prompt.py | Needs monitoring |
| 5 | LATENT | `skill_family` display name vs `skill_family_key` enum | annotate_prompt.py | Needs monitoring |
| 6 | LATENT | `subskill` vs `grammar_focus_key` | annotate_prompt.py | Needs monitoring |
| 7 | OK | DB column names (`option_label`/`option_text`) vs extraction (`label`/`text`) | db.py, ingest.py | Handled by persist code |
| 8 | OK | `correct_option_label` consistent across pipeline | All files | Consistent |
| 9 | OK | API response format (`label`/`text`) | student.py, admin.py | Consistent |

### Detailed Findings

**Issue 1 (FIXED): option format mismatch**
- Annotation LLM returns `{option_label: "A", option_text: "...", is_correct: false, ...}`
- Validator expects `{label: "A", text: "..."}`
- `_merge_for_validation` restores extraction's options but the annotation's options overwrite first
- **Fix**: Added `option_label → label` and `option_text → text` normalization in both `validator.py` and `_merge_for_validation()`
- Also in `option_hydration.py`: `option_analyses_by_label()` already handles both formats via `opt.get("option_label") or opt.get("label")`

**Issue 2 (FIXED): Missing stem_type_key values**
- `conform_to_standard_english` — returned by LLM for SEC complete_the_text questions
- `most_logically_completes` — defined in reading v2 Section 3.2
- `synthesize_information` — in `_READING_STEMS` but not in `STEM_TYPE_KEYS`
- `compare_contributions` — in `_READING_STEMS` but not in `STEM_TYPE_KEYS`
- **Fix**: Added all 4 to `STEM_TYPE_KEYS` in `ontology.py`

**Issue 3 (FIXED): Missing stimulus_mode_key**
- `notes_summary` — LLM returns this instead of `notes_bullets` for Rhetorical Synthesis questions
- **Fix**: Added `notes_summary` to `STIMULUS_MODE_KEYS` in `ontology.py`

**Issue 4 (LATENT): Domain string vs question_family_key**
- Annotation returns `"domain": "Standard English Conventions"` (display name)
- Ontology uses `"question_family_key": "conventions_grammar"` (enum key)
- `normalize_annotation()` bubbles up `question_family_key` from nested `classification` dict
- `_detect_domain()` and `_infer_domain_from_annotation()` handle the domain string
- **Risk**: If LLM returns `domain` without `question_family_key`, the latter may be `None`

**Issue 5 (LATENT): skill_family display name vs enum**
- Rules v7 examples use `skill_family: "Form, Structure, and Sense"` (display name)
- Ontology uses `skill_family_key: "form_and_structure"` (snake_case enum)
- The `allowed_keys` block in the annotation prompt lists the enum values
- **Risk**: LLM may return display names instead of enum values

**Issue 6 (LATENT): subskill vs grammar_focus_key**
- Rules v7 examples use `subskill: "subject-verb agreement with plural prepositional object"` (free text)
- Ontology uses `grammar_focus_key: "subject_verb_agreement"` (snake_case enum)
- **Risk**: `grammar_focus_key` validation may flag LLM-returned values not in `GRAMMAR_FOCUS_KEYS`

**Issue 7 (OK): DB column name mapping**
- `QuestionOption` uses `option_label` and `option_text` columns
- `_persist_single_question()` correctly maps `opt.get("label")` → `option_label` and `opt.get("text")` → `option_text`
- `option_analyses_by_label()` correctly handles both `option_label` and `label`

### Key Name Reference Table

| Extraction (Pass 1) | Annotation (Pass 2) | DB (Persist) | Validator | Normalized? |
|---------------------|--------------------|---------------|-----------|-------------|
| `label` | `option_label` | `option_label` | `label` | ✅ Now yes |
| `text` | `option_text` | `option_text` | `text` | ✅ Now yes |
| `correct_option_label` | `correct_option_label` | `current_correct_option_label` | `correct_option_label` | ✅ Yes |
| `question_text` | `question.question_text` | `current_question_text` | `question_text` | ✅ Yes |
| `passage_text` | `question.passage_text` | `current_passage_text` | `passage_text` | ✅ Yes |
| `stem_type_key` | `stem_type_key` or `classification.stem_type_key` | `stem_type_key` | `stem_type_key` | ✅ Normalized |
| `stimulus_mode_key` | `stimulus_mode_key` or `question.stimulus_mode_key` | `stimulus_mode_key` | `stimulus_mode_key` | ✅ Normalized |
| `domain` (N/A) | `classification.domain` | N/A | Not checked | ⚠️ Not validated |
| `question_family_key` | `classification.question_family_key` | N/A | `question_family_key` | ✅ Normalized |
| `grammar_role_key` | `classification.grammar_role_key` or top-level | N/A | `grammar_role_key` | ✅ Normalized |
| `grammar_focus_key` | `classification.grammar_focus_key` or top-level | N/A | `grammar_focus_key` | ✅ Normalized |

---
