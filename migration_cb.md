# CB Question Bank Ingestion — Requirements

Requirements for importing the College Board MyPractice Question Bank into
the DSAT DB without duplicating official questions, and for organizing the
result under one ontology instead of two disconnected vocabularies.

**Source:** `CB_QUESTION_BANK/09_2026/09_2026_New_Verbal_Bank.json` (752
items, extracted from the CB PDF by `CB_QUESTION_BANK/09_2026/extract_cb_bank.py`).
Per-question fields: `question_id`, `question_family_key`,
`skill_family_key`, `domain`, `skill`, `difficulty`, `passage`, `stem`,
`choices` (A–D), `correct_answer`. The canonical CB corpus is larger — the
Sep difficulty trio (Easy/Medium/Hard results PDFs) unions to 1,845 items,
~1,093 beyond this one file — the ingester must be parametrized by input PDF,
not hardcoded to this file.

**Target:** `questions`, `question_versions`, `question_options`,
`question_annotations.annotation_jsonb` (101 distinct keys, see
`KEYS_MASTER.md`).

**Status:** `questions.cb_question_id` (migration `035_cb_question_id.py`)
is live. 55/752 items in this file already exist in the DB (matched on
normalized passage text, all ≥0.997) and are backfilled — see
`CB_QUESTION_BANK/09_2026/db_overlap_check.md`. Everything below is planning
for the full importer; nothing else has been executed against the DB.

## 1. Field mapping

### 1a. Aligned — pass through as-is

| Bank field | DB location | Notes |
|---|---|---|
| `question_id` | `questions.cb_question_id` | Verbatim CB 8-hex ID. Unique key for dedup/sync. |
| `domain` | `annotation_jsonb->>'domain'` | Stored verbatim, e.g. `"Information and Ideas"` — confirmed identical string in both. |
| `passage` | `questions.current_passage_text`, `question_versions.passage_text` | 1:1. |
| `stem` | `questions.current_question_text`, `question_versions.question_text` | 1:1. |
| `choices.A`–`D` | `question_options.option_text` | One bank object flattens to 4 rows (`option_label` A–D). |
| `correct_answer` | `questions.current_correct_option_label`, `question_versions.correct_option_label`, `question_options.is_correct` | 1:1, drives the boolean flag on the matching option row. |
| `question_family_key` | `annotation_jsonb->>'question_family_key'` | Same snake_case value space as `QUESTION_FAMILY_KEYS` (4 canonical values) — extractor already derives it via the same domain mapping. Lands in the annotation JSON, not a `questions` column. |

### 1b. Needs translation

| Bank field | DB equivalent | Misalignment | Fix |
|---|---|---|---|
| `skill_family_key` (reading domains) | `annotation_jsonb->>'skill_family_key'` (`READING_SKILL_FAMILY_KEYS`, 7 values) | Aligned — pass through directly. | — |
| `skill_family_key` (grammar/expression domains) | *(no equivalent field)* | Extractor emits `boundaries`, `form_structure_and_sense`, `rhetorical_synthesis`, `transitions` — **none exist in any DB controlled vocabulary.** Grammar questions use `grammar_role_key` (8) + `grammar_focus_key` (46) instead; Expression-of-Ideas uses its own key families (`transition_subtype_key`; `synthesis_goal_key`/`audience_knowledge_key`/`required_content_key`). | Do not write this value into `annotation_jsonb.skill_family_key`. Route `skill` as a coarse hint (§2) and let annotation derive the real key. |
| `skill` (human label) | *(no verbatim field stored)* | DB keeps only derived keys, never the CB label. For grammar, one label is coarser than DB's granularity — `"Boundaries"` spans 2 of 8 `grammar_role_key` values (`punctuation`, `sentence_boundary`); `"Form, Structure, and Sense"` spans the other 6. | Treat as a routing hint only (§2), not a stored value. |
| `difficulty` (`Easy`/`Medium`/`Hard`, title case) | `annotation_jsonb->>'difficulty_overall'` (canonical `low`/`medium`/`high`) | Case *and* value mismatch — not a literal lowercase. | Map `Easy→low`, `Medium→medium`, `Hard→high` on ingest (§4 decision on scope). |

### 1c. Bank provides nothing — annotation pipeline owns these

- `questions.content_origin` — set to `official` on insert.
- `questions.official_overlap_status` / `canonical_official_question_id` — dedupe bookkeeping the ingester computes itself.
- `questions.stimulus_mode_key`, `questions.stem_type_key` — derived by annotation only.
- All `question_options` distractor columns (`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`, `option_error_focus_key`, `why_plausible`, `why_wrong`, `grammar_fit`, `tone_match`, `precision_score`, `student_failure_mode_key`, `distractor_distance`, `distractor_competition_score`) — bank gives option text only, no rationale.
- The remaining ~90 of 101 `annotation_jsonb` keys (`grammar_focus_key`, `grammar_role_key`, `reasoning_trap_key`, `syntactic_trap_key`, `evidence_location_key`, `evidence_span_text`, `explanation_full`/`short`, `notes_bullets`, `reading_focus_key`, `topic_broad`/`topic_fine`, `register`, `tone`, etc.).

**Opportunity, not yet acted on:** `extract_cb_bank.py`'s docstring says
*"Rationale text is intentionally excluded"* — the source PDF's rationale
block is cleanly bounded (`Correct Answer: X` through `Question Difficulty:`)
and could seed `explanation_full`/`explanation_short` directly from CB
instead of via LLM generation — likely higher-fidelity. Deferred decision;
small extractor change once decided.

## 2. Unified ontology tree

CB's own ontology (`domain` → `question_family_key` → `skill`) is the outer
scaffold; DB's finer-grained vocabularies nest underneath.

```
question_family_key (CB "domain", 4 values — QUESTION_FAMILY_KEYS)
│
├── information_and_ideas ─┐
├── craft_and_structure    ┤  READING branch
│                          │
│   skill_family_key (CB "skill", 7 values — READING_SKILL_FAMILY_KEYS)
│     central_ideas_and_details · command_of_evidence_textual ·
│     command_of_evidence_quantitative · cross_text_connections ·
│     inferences · text_structure_and_purpose · words_in_context
│     │
│     ├── reading_focus_key (38, nested under skill_family_key —
│     │     READING_FOCUS_BY_SKILL_FAMILY)
│     ├── reasoning_trap_key (49, question-level trap)
│     ├── TEST_CONSTRUCT_KEYS (7) / CRAFT_SUBCONSTRUCT_KEYS (9)
│     │     — craft_and_structure-specific refinement
│     └── TEXT_RELATIONSHIP_KEYS (7) — cross_text_connections only
│
├── conventions_grammar ────┐  GRAMMAR branch — the grammar_role_key ring
│                           │  is shared by BOTH grammar-classified families
│                           │  (GRAMMAR_QUESTION_FAMILY_KEYS = this one
│                           │  + expression_of_ideas)
│   grammar_role_key (8 — GRAMMAR_ROLE_KEYS)
│     agreement · modifier · pronoun · verb_form · parallel_structure ·
│     punctuation · sentence_boundary · expression_of_ideas
│     │
│     ├── grammar_focus_key (46, nested under role — GRAMMAR_FOCUS_BY_ROLE)
│     └── syntactic_trap_key (13 — required only for 5 of the 8 roles,
│           SYNTACTIC_TRAP_REQUIRED_ROLES)
│
└── expression_of_ideas ────┐  also its own CB "domain" AND a
                            │  grammar-classified family: the same
                            │  grammar_role_key ring above applies here too
                            │  (live DB: 336 rows carry
                            │  role=expression_of_ideas under this family
                            │  vs 43 under conventions_grammar)
    skill = "Transitions"        → transition_subtype_key (24)
    skill = "Rhetorical Synthesis" → synthesis_goal_key (42)
                                     + audience_knowledge_key (3)
                                     + required_content_key (32)
                                     + synthesis_distractor_failure_key (8,
                                       option-level)

CROSS-CUTTING (not owned by one branch):
  stimulus_mode_key (9)        — passage form
  stem_type_key (29)           — question shape
  difficulty_* (low/medium/high — DIFFICULTY_KEYS; bank's Easy/Medium/Hard
                                  maps here, see §1b)

STYLISTIC layer (passage-level voice/register — cuts across all 4 families,
since even a grammar sentence-only stimulus carries a tense/register call):
  tense_register_key (7)       passage_architecture_key (25)
  topic_broad (9) + topic_fine (free text)
  register / tone              — free-text today, not controlled vocab (gap)

OPTION-LEVEL shared layer (every family's distractors):
  distractor_type_key (45)     plausibility_source_key (15)
  student_failure_mode_key (63) distractor_distance (3)
```

The bank only ever populates the **top two rings** — `question_family_key`
directly, `skill_family_key`/`skill` as a hint — and only cleanly for the
reading branch (§1b). Everything below that has zero bank coverage; the bank
is a stem/passage/answer source, not an annotation source.

## 3. Existing DB data-quality drift (found while validating the tree)

Live-DB counts, verified against `question_annotations.annotation_jsonb`:

| Drift | Rows |
|---|---|
| `difficulty_overall` = `easy` / `hard` (non-canonical, should be `low`/`high`) | 1 / 1 |
| `difficulty_overall` NULL | 49 |
| `question_family_key` = `standard_english_conventions` (not in the 4-value vocab — should be `conventions_grammar`) | 9 |
| `grammar_role_key` set, `question_family_key` blank | ~35 |
| `skill_family_key` = `transitions` on an `expression_of_ideas` row (should be `transition_subtype_key`, not `skill_family_key`) | 1 |
| `skill_family_key` = `punctuation_boundaries` on a `standard_english_conventions` row | 1 |

Pre-existing, not caused by bank ingestion. Cleanup is a separate pass (§5),
not a blocker for the importer — but the importer must not write into the
same broken patterns (e.g. must never write `standard_english_conventions`).

## 4. Open decisions (must be resolved before building the importer)

1. **Overlap-hit policy (the 55 in-DB items).** On a passage match, the plan
   backfills `cb_question_id` and skips insert — but is silent on whether
   the bank's `difficulty`/`domain`/`question_family_key` also overwrite
   those rows, which already carry LLM annotations. Options: ID-only write
   (recommended — don't clobber existing annotation); ID + `difficulty_overall`
   overwrite; stash under separate `cb_*` keys for later reconciliation.
2. **The 8 `exclude_active` IDs** (`15c0ed26`, `3009048e`, `4d671b68`,
   `5251e5c9`, `6264a75d`, `7e1dd168`, `87f45e64`, `92b43ac5`). All 8 are in
   this bank file and all 8 miss the DB — a naive importer inserts every one
   as new official content, but the original bank review flagged these for
   exclusion. Need a rule: skip / insert-but-flag-excluded / insert normally.
3. **Difficulty key ownership.** §1b pins `difficulty_overall` only; live DB
   actually carries a 5-key difficulty family (`difficulty_overall` 1,511 ·
   `difficulty_reading` 1,349 · `difficulty_grammar` 1,209 ·
   `difficulty_vocab` 993 · `difficulty_inference` 996). Decide whether the
   importer owns only `difficulty_overall` (recommended — annotation fills
   the rest) or pre-seeds the whole family.
4. **Rationale re-extraction** (§1c opportunity) — build it into this
   importer or defer.

## 5. Implementation plan

**Phase 1 — regroup this 752-item file by the tree (no LLM, no DB writes)**
Bucket `09_2026_New_Verbal_Bank.json` into
`question_family_key → skill (raw CB label) → [items]`, joined against
`db_overlap_check.md`'s in-DB/not-in-DB status. Output:
`CB_QUESTION_BANK/09_2026/ontology_bucketed.json` + a family×skill×count
summary table. Pure local reshuffle of data already on disk — no
dependencies, can run immediately.

**Phase 2 — codify the routing table**
Turn the CB `(domain, skill)` → DB `(question_family_key, skill_family_key |
grammar_role_key)` mapping in §1b/§2 into a small lookup
(`backend/app/pipeline/cb_ontology_map.py`, ~10-entry flat dict) so import
code doesn't re-derive it ad hoc.

**Phase 3 — build the importer, resolving §4's decisions**
Per bank item: passage-match against existing official `questions`
(as done for this file); on hit, backfill `cb_question_id` only (per
decision 1) and skip insert; on miss, insert a new `official`
question/version/options row set with `cb_question_id` set directly, wiring
`questions.latest_version_id` correctly (`question_options` reads must
filter by version — known bug class in this repo, don't repeat it). Apply
the `exclude_active` rule (decision 2). Write `domain`,
`question_family_key`, and (reading skills only) `skill_family_key` into
`annotation_jsonb`; map `difficulty` per §1b. Note: bank-derived
textual/quantitative Command-of-Evidence split, if attempted from the stem
text, is a heuristic only (chart items are vector graphics with jumbled
extracted text) — treat as a routing hint, let annotation re-derive it.

**Phase 4 — queue for annotation (not skippable)**
Every field in §1c requires the normal LLM annotation pass, same as OCR'd
official-test ingestion. The importer only gets a question to the point
where annotation can run with the right family/role already pinned.

**Phase 5 — validate & cleanup**
Re-run the §3 drift check against the post-import DB to confirm no new
stray keys were introduced, then separately clean up the pre-existing §3
drift (not blocking Phase 3/4).

## 6. Definition of done

- [ ] Migration `035_cb_question_id.py` applied (done).
- [ ] Decisions 1–4 in §4 recorded as resolved (not just noted).
- [ ] `cb_ontology_map.py` lookup exists and is unit-tested against §1b/§2.
- [ ] Importer runs against the full Sep difficulty trio (1,845 items), not
      just this 752-item file, and is idempotent on re-run (`cb_question_id`
      uniqueness enforces this).
- [ ] Zero new §3-style stray keys introduced by the importer.
- [ ] Every imported question queued for annotation before being marked
      practice-ready.
