# Grammar Rules + Ontology Refactor — Plan & Task List

**Date:** 2026-09-20 · **Branch:** RULES_REFACTOR_v3 · **Base commit:** da02823
**Scope:** Verbal only. Math (`CB_QUESTION_BANK/NEW_QUESTION_SETS/Math/`) is explicitly out of scope.
**Target base ontology:** [`DOMAINS_SKILLS.md`](DOMAINS_SKILLS.md) — 4 CB domains × 10 CB skills.

---

## Governing constraint: ADDITIVE ONLY

**This refactor adds a field per question. It does not rewrite, replace, or remove existing
annotation data.** Every task below is bound by this. Concretely:

| Rule | Consequence |
|---|---|
| No existing vocabulary is deleted or renamed | `GRAMMAR_ROLE_KEYS`, `GRAMMAR_FOCUS_KEYS`, `READING_*`, `STEM_TYPE_KEYS` all keep their current values and meanings |
| `skill_family_key` is **added** to grammar questions, never substituted for `grammar_role_key` | roles become a *child* layer by documentation and validator rule, not by data movement |
| Writes are **field-level merges** into the existing `question_annotations` row | `annotation_jsonb` gains one key; every other key is byte-identical afterward |
| No new `QuestionVersion`, no `change_source='reprocess'` | the current-version pointer never moves, so hand-corrections stay current |
| `user_progress` gains a column; existing columns are not remapped | historical attempt rows keep pointing at the vocabulary they were written with |

**Precedent in this codebase:** `backend/app/services/span_annotator.py:229` does exactly this —
`ann.passage_spans = {...}` plus `ann.span_annotated_at`, committed on the existing row. It is the
model for every write in Phase 4, and `scripts/reannotate_spans.py` is the model for the bulk driver.

**What this rules out:** `POST /ingest/reannotate/{id}` and
`scripts/reannotate_official_v7.py`. `_run_reannotate_pipeline` regenerates the *entire* annotation
from the LLM and writes a fresh `QuestionVersion` — correct for a v3→v7 rules migration, wrong here.
Adding one classification field must not put the other ~40 annotation keys back through a model.

**Rollback:** because every write is one added key, rollback is
`annotation_jsonb = annotation_jsonb - 'skill_family_key'` plus dropping the added column. No restore
from backup, no version surgery.

---

## Part 1 — Source data audit (COMPLETE)

Independent re-parse of every verbal PDF, extracting `Question ID` / `Domain` / `Skill` /
`Question Difficulty` / `Correct Answer` with a parser written from scratch (not
`extract_cb_bank.py`), then cross-checked. Script: `scratchpad/audit_cb.py`, `scratchpad/dedup.py`.

### 1.1 File inventory — what is actually distinct

`NEW_QUESTION_SETS/VERBAL/` is a **byte-identical copy** of the five `09_2026/` verbal PDFs,
renamed (verified by md5). It contains no new data.

| md5-distinct PDF | Questions | Role |
|---|---|---|
| `09_2026/09_2026_New_Verbal_Bank.pdf` | 752 | Full bank, with rationales |
| `09_2026/…Bank  - Questions ONLY.pdf` | 752 | Same 752 IDs, rationales stripped |
| `09_2026/MyPractice …Results - easy.pdf` | 611 | Difficulty split |
| `09_2026/MyPractice …Results medium.pdf` | 624 | Difficulty split |
| `09_2026/MyPractice …Results - Verbal Hard.pdf` | 610 | Difficulty split |
| `MyPractice …Results11.pdf` | 503 | Partial export (no SEC domain) |
| `MyPractice …Results part 2.pdf` | 367 | ⊂ Verbal Hard |
| `MyPractice …part 1 page 1-5.pdf` | 238 | ⊂ part 2 ⊂ Verbal Hard |
| `MyPractice …Results - exclude active.pdf` | 8 | ⊂ Bank, ⊂ Results11 |

### 1.2 Canonical pool

- **1,845 unique question IDs** across all nine PDFs.
- `EASY ∪ MED ∪ HARD` = **exactly 1,845 with zero pairwise overlap** — a clean partition
  (611 + 624 + 610 = 1,845). Every other PDF is a strict subset of that union.
- The 752-item Bank is a strict subset (752/752 inside the union). It is **not** the full pool;
  the difficulty splits are.
- `Assessment` / `Test` is `SAT` / `Reading and Writing` on all 4,465 parsed rows — no Math
  contamination, no PSAT rows.

### 1.3 Label integrity — zero conflicts

Across all 4,465 rows (i.e. every appearance of every ID in every PDF):

| Check | Result |
|---|---|
| IDs with conflicting `Domain` | **0** |
| IDs with conflicting `Skill` (case-normalized) | **0** |
| IDs with conflicting `Question Difficulty` | **0** |
| IDs with conflicting `Correct Answer` | **0** |
| IDs missing difficulty anywhere | **0** |
| IDs missing correct answer anywhere | **0** |
| Blank `Domain` / `Skill` fields | **0 / 0** |

The Bank PDFs carry no `Question Difficulty:` or `Correct Answer:` line (752 blanks); every
one of those IDs recovers both from its difficulty-split PDF. No data is lost.

### 1.4 Domain × Skill over the canonical 1,845

| Domain | Skill | n |
|---|---|---|
| Craft and Structure | Cross-Text Connections | 61 |
| Craft and Structure | Text Structure and Purpose | 149 |
| Craft and Structure | Words in Context | 261 |
| Expression of Ideas | Rhetorical Synthesis | 204 |
| Expression of Ideas | Transitions | 194 |
| Information and Ideas | Central Ideas and Details | 138 |
| Information and Ideas | Command of Evidence | 277 |
| Information and Ideas | Inferences | 140 |
| Standard English Conventions | Boundaries | 213 |
| Standard English Conventions | Form, Structure, and Sense | 208 |

**Exactly 10 combinations. Each skill belongs to exactly one domain.** `DOMAINS_SKILLS.md` is
confirmed correct and is a safe base for the refactor.

One cosmetic defect: `Cross-text Connections` (lowercase *t*) appears **3 times** — once each in
MED, HARD, and Results11 — against 61 correct `Cross-Text Connections`. Normalize on ingest;
do not treat as a distinct label. (`DOMAINS_SKILLS.md` says "one each in MED and HARD"; the
third instance is in `Results11.pdf`, which that note did not cover. Footnote needs a one-word fix.)

### 1.5 `09_2026_New_Verbal_Bank.json` — extraction fidelity

752 records, flat list, keys: `question_id, question_family_key, skill_family_key, domain,
skill, difficulty, passage, stem, choices, correct_answer`. Domain/skill counts match the
PDF re-parse exactly. **But:** `difficulty` is empty for all 752 (source PDF has no difficulty
line) — the JSON must be re-derived against the difficulty splits, and should cover all 1,845,
not 752.

`extract_cb_bank.py` already emits keys for an ontology **that does not exist yet**:
`boundaries`, `form_structure_and_sense`, `rhetorical_synthesis`, `transitions` are not in
`READING_SKILL_FAMILY_KEYS`. Treat the script as a *specification of intent*, and make this
refactor the thing that makes those keys legal.

### 1.6 Command of Evidence textual/quantitative split — validated

CB gives one `Command of Evidence` label; the DB splits it in two. The current derivation is a
stem regex `\b(graph|table|data in the)\b` → 54 quantitative / 69 textual (of 123 in the Bank).

Audited: all 123 CoE stems. Quantitative-bucket passages begin with axis-label number runs or
table headers; textual-bucket passages are prose. **Zero** of the 69 textual stems contain
`figure`, `chart`, `bar graph`, `graphic`, or a bare `data`. The heuristic has no leakage on
this corpus and is safe to ship. Re-run the same check over all 1,845 before locking it in.

---

## Part 2 — Ontology gap analysis

### 2.1 Correction to an earlier statement

I said previously that "the 4-domain CB header level doesn't exist in the DB." **That was wrong.**
`QUESTION_FAMILY_KEYS` (`backend/app/models/ontology.py:294`) is exactly the four CB domains:
`conventions_grammar`, `expression_of_ideas`, `craft_and_structure`, `information_and_ideas`.
The domain layer is already correct and needs no change. The gap is one level down.

### 2.2 What is actually missing

| CB layer | DB today | Gap |
|---|---|---|
| Domain (4) | `question_family_key` — 4 values, exact match | ✅ none |
| Reading skills (6) | `skill_family_key` — 7 values (CoE split in two) | ✅ aligned, superset by design |
| **Grammar skills (4)** | **nothing** — grammar questions carry `grammar_role_key` (8 finer linguistic values) instead | ❌ **the refactor** |

`skill_family_key`'s validator (`backend/app/models/annotation.py:101`) restricts it to
`READING_SKILL_FAMILY_KEYS`, so a grammar question structurally cannot carry a skill. There is no
key anywhere for Boundaries, Form/Structure/Sense, Transitions, or Rhetorical Synthesis.
`rhetorical_synthesis` exists only as an unmerged amendment
(`vocabulary/amendments/pending/amd-1a6b9e6c9e18.json`) and a vocab candidate
(`vocabulary/candidates.json:250`).

### 2.3 Target shape

```
question_family_key   (4)  ← CB Domain          [unchanged]
  └─ skill_family_key (11) ← CB Skill           [EXTENDED: + 4 grammar families]
       └─ grammar_role_key / reading_focus_key  [RE-PARENTED under skill_family_key]
            └─ grammar_focus_key
```

New `GRAMMAR_SKILL_FAMILY_KEYS = ("boundaries", "form_structure_and_sense", "transitions",
"rhetorical_synthesis")`. `SKILL_FAMILY_KEYS = READING + GRAMMAR` (11 total; 10 CB skills, CoE
split in two). `skill_family_key` becomes **legal** for every verbal question — a widened
enum, not a narrowed one. `grammar_role_key` keeps every value and every meaning it has today;
"re-parenting" is a documentation and validator-whitelist change, not data movement. Nothing in
`annotation_jsonb` is removed or rewritten.

### 2.4 The grammar map — three buckets, only one costs LLM calls

**Bucket A — deterministic (role-level, no ambiguity):**

| `grammar_role_key` | → CB skill |
|---|---|
| `sentence_boundary` | Boundaries |
| `agreement`, `verb_form`, `modifier`, `parallel_structure`, `pronoun` | Form, Structure, and Sense |

**Bucket B — deterministic at focus-key level (needs spot review, not LLM):**

| `grammar_focus_key` (role `punctuation`) | → CB skill |
|---|---|
| `semicolon_use`, `colon_dash_use`, `comma_splice`, `run_on_sentence`, `conjunctive_adverb_usage`, `appositive_punctuation` | Boundaries |
| `apostrophe_use`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation`, `end_punctuation_question_statement` | Form, Structure, and Sense |
| `transition_logic` (role `expression_of_ideas`) | Transitions |

**Bucket C — genuinely per-question, requires LLM adjudication:**

- `punctuation_comma` and `unnecessary_internal_punctuation` — split by whether the edit point
  joins two independent clauses (Boundaries) or sits inside one (Form/Structure/Sense).
- All remaining `expression_of_ideas` focus keys (`redundancy_concision`,
  `precision_word_choice`, `emphasis_meaning_shifts`, `logical_relationships`, …) — these span
  Transitions, Rhetorical Synthesis, and Form/Structure/Sense with no reliable antecedent.
- **Rhetorical Synthesis has no antecedent key at all.** Every question that belongs to it must be
  identified by model or by `stem_type_key = choose_best_notes_synthesis` (see 2.5).

The plan is therefore **hybrid, not a blanket reannotate**: deterministic jsonb remap for A and B,
scoped LLM reannotate only for C. That is cheaper, reversible, idempotent, and — critically — it
does not overwrite hand-corrected annotations for the large majority of rows.

### 2.5 Second migration surface: `stem_type_key`

`STEM_TYPE_KEYS` (29 values) already encodes overlapping distinctions —
`choose_best_notes_synthesis` ≈ Rhetorical Synthesis, `choose_best_transition` ≈ Transitions,
`conform_to_standard_english` ≈ SEC generally. Left alone, this becomes a second source of truth
that drifts from `skill_family_key` (cf. bug-811, "stem_type strays still open").

**Decision required (TASK-00):** either (a) derive `skill_family_key` partly from `stem_type_key`
and assert consistency in the validator, or (b) formally document `stem_type_key` as a
*surface-form* axis orthogonal to the *skill* axis, and add a cross-check. Do not leave it implicit.

### 2.7 Unresolved: how much of the CB bank is already in the DB

Two figures are on record from the same date (2026-09-12) and they disagree:

| Source | Denominator | Matched | Method |
|---|---|---|---|
| `09_2026/db_overlap_check.md` (committed) | 752 (Bank subset) | **55** | exact/near-exact stem match, ≥0.997 |
| Project memory note | 1,845 (full pool) | **669** | 27 direct stem + 642 passage+stem, sample-verified |

Different scope and different matchers, so both can be internally correct: 55/752 strict-on-a-subset
vs 669/1,845 fuzzy-on-everything (36% of the bank; 44% of the DB's 1,514 official verbal questions).
Neither has been re-verified — Postgres is down, see hazard 5.

This is not a bookkeeping detail. It sets the size of the calibration set that TASK-07b uses to
prove or disprove the §2.4 grammar map, and it sets the true "new questions" count for TASK-27
(~697 vs ~1,176). **Resolve it first (TASK-07a).**

### 2.8 Identity: generated PK, CB ID as a data field (DECIDED 2026-09-20)

`questions.id` stays the generated UUID primary key. `cb_question_id` is a **plain nullable data
column** — never a key, never a join target in place of `id`. Migration 035 already provides it
(`VARCHAR(8) UNIQUE`); it is now declared on the model (bug-830).

**Consequence for bank ingest.** Official-test questions get a deterministic **UUIDv5** from
`_official_question_uuid` (`backend/app/routers/ingest.py:132`), keyed on
`exam:subject:section:module:question_number`. Re-ingesting the same practice test therefore
produces the same UUID and is idempotent by construction. (54 of the 55 IDs in
`db_overlap_check.md` are v5; 1 is v4.)

CB bank questions carry **no test/section/module/question number**, so that derivation does not
apply and they fall through to `uuid.uuid4()` (`ingest.py:1027`). That is the intended behaviour —
but it means **the UUIDv5 idempotency guard does not cover bank ingest**. Re-running the ingest
would insert duplicate rows under fresh random UUIDs.

**Therefore:** `cb_question_id` is the idempotency key for bank ingest. TASK-27 must upsert on it
(`ON CONFLICT (cb_question_id) DO NOTHING`, or an explicit pre-check), not rely on UUID derivation.
Do **not** extend `_official_question_uuid` to hash bank content — that would make the PK depend on
question text, so any later text correction would change the primary key and orphan every
`user_progress`, `question_versions`, and `question_annotations` row pointing at it.

### 2.6 Migration hazards carried forward

1. **Hand-corrected annotations.** *Largely neutralized by the additive-only constraint* — a
   field-level merge cannot demote a manual fix, because no new version is written. The residual
   risk is narrow: if a `skill_family_key` was already set by hand, do not overwrite it. Predicate
   for "leave this field alone": `questions.is_admin_edited = true` **and** the key is already
   present. This replaces the blanket exclusion the earlier draft required.
2. **`user_progress` denormalized keys.** `question_domain`, `missed_grammar_focus_key`,
   `missed_reading_focus_key`, `missed_reading_skill_family_key` (`backend/app/models/db.py:552-558`)
   are copied onto historical attempt rows. Under additive-only these are **not remapped** — no key
   is renamed, so nothing goes stale. The work is to *add* `missed_skill_family_key` and backfill it
   for past attempts by joining to the question's newly-populated value. Old columns stay as written.
3. **Migration cursor.** `question_annotations.rules_version` is stamped per annotation — use it
   to select un-migrated rows. `questions.annotation_stale` is the right flag for the queue.
4. **Safety property.** Blocking validation errors route a job to `needs_review` rather than
   writing the row, so a bad ontology surfaces as a review pile, not corruption.
5. **Port discrepancy (prerequisite).** `scripts/reannotate_official_v7.py:31` hardcodes
   `localhost:5437/dsat_dev`; CLAUDE.md and the dev stack say `5434/dsat`. Nothing is listening on
   either right now. Resolve before any task that touches the live DB.

---

## Part 2b — Phase 2 results (2026-09-20)

Full detail: `CB_QUESTION_BANK/09_2026/db_overlap_full.md`. Scripts: `match_bank_to_db.py`
(read-only matcher), `calibration_report.py` (derives the map).

### 2b.1 Overlap — resolved

**733 of the 1,845 bank questions are already in the DB, covering 1,414 of its 1,514 official
rows (93.4%).** 11 need human review; 1,101 are new. Zero DB rows claimed by two bank IDs.
Both earlier figures were right for what they measured: 55 was a strict stem matcher on the
752-item subset; 669 was passage+stem on the full pool. §2.7 is closed.

Matching is two signals — normalized passage+stem *as one string*, and the four choices. Scoring
passage and stem separately rejects true matches, because CB keeps the "The student wants to…"
goal sentence in the stem and the DB stores it in the passage.

### 2b.2 The DB stores each question ~2 times

| DB copies per bank question | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| bank questions | 267 | 301 | 118 | 44 | 3 |

1,414 rows are 733 distinct questions — the same item ingested from the 2024 and 2025 releases
and from untitled re-imports. (An md5 check found only 177 groups; whitespace differs between
copies.) **Every per-question write must reach every copy**, so the fill is keyed on `db_id`
from `db_overlap_full.json`, not on `cb_question_id`.

### 2b.3 The consequence: CB ground truth replaces most of the map

93% of official rows take their skill **directly from the CB label** — no inference, no map, no
model. The old→new map is needed only for the ~100 unmatched official rows and for generated /
unofficial questions. This removes almost all of the LLM work originally planned for Phase 4.

### 2b.4 The map — §2.4 was partly wrong, now derived from data

`vocabulary/mappings/cb_skill_map.json` is generated from 655 grammar calibration rows; each rule
carries `n` and `purity`, and is `deterministic` only at n ≥ 5 and purity ≥ 95%. Corrections to
the hand-written §2.4 table, which is **superseded**:

| §2.4 claimed | Data says |
|---|---|
| `punctuation_comma`, `unnecessary_internal_punctuation` need LLM adjudication | 96.4% / 95.5% **Boundaries** — deterministic |
| `end_punctuation_question_statement`, `quotation_punctuation` → Form/Structure/Sense | **Boundaries**, 9/9 and 2/2 |
| all of role `sentence_boundary` → Boundaries | `sentence_fragment` is 3/3 **Form/Structure/Sense**; `comma_splice` only 71% pure |
| most of `expression_of_ideas` needs LLM adjudication | `transition_logic` → Transitions 159/159; the rest → Rhetorical Synthesis, except `logical_relationships` (79%) |

`stem_type_key` is the strongest single signal: `choose_best_notes_synthesis` /
`synthesize_information` → Rhetorical Synthesis (145/145), `choose_best_transition` → Transitions
(48/48). This settles TASK-01 empirically: derive from `stem_type_key` first, then role/focus.
Deterministic coverage of the 655: role/focus 544, stem 193, role 151.

### 2b.5 Existing annotations disagree with CB — needs a decision

| Check against CB ground truth | Result |
|---|---|
| `question_family_key` (domain) agrees | 1,213 / 1,414 (85.8%) |
| Reading `skill_family_key` agrees | 633 / 759 — 104 missing, **22 present but wrong** |
| Words in Context rows annotated as a *grammar* question | **79** (`expression_of_ideas` / `precision_word_choice`) |

Under ADDITIVE ONLY the fill **adds `skill_family_key` where it is absent and touches nothing
else**. It does not correct the 22 wrong skills or the 201 domain disagreements — those are
reported, not rewritten (TASK-23). Overwriting an existing value with the CB label is defensible
(CB is the authority) but it is a rewrite, so it is **the user's call, not this migration's**.

### 2.9 `cb_question_id` is UNIQUE but questions are duplicated — needs a decision

Migration 035 made `questions.cb_question_id` `UNIQUE`. With ~2 DB copies per question, only one
copy can carry the ID, so 681 of the 1,414 matched rows can never be labelled with it. Options:
(a) drop the unique constraint so every copy carries its CB ID — simplest, but bank-ingest
idempotency (§2.8) then needs a `WHERE NOT EXISTS` pre-check instead of `ON CONFLICT`;
(b) keep it unique and label only the canonical copy, pointing the others at it via the existing
`canonical_official_question_id`; (c) de-duplicate the DB first. **Recommend (b)** — it is
additive, uses a column that already exists for exactly this, and keeps §2.8 intact. Not blocking:
the skill fill keys on `db_id` and does not depend on the outcome.

## Part 2c — CB label columns (DONE 2026-09-20) — the merge now keys on these

College Board's four labels are first-class columns on `questions`, kept apart from the
LLM-derived `annotation_jsonb`:

| Column | Holds | Filled |
|---|---|---|
| `cb_question_id` | CB's 8-hex bank ID | 1,414 rows / 733 distinct questions |
| `cb_domain_key` | one of the 4 `QUESTION_FAMILY_KEYS` | 1,414 |
| `cb_skill_key` | one of CB's **10** skills — `command_of_evidence` is *not* split | 1,414 |
| `cb_difficulty` | `easy` / `medium` / `hard`, as CB rates it | 1,414 |

Null on the 100 official rows with no CB match and on all generated / unofficial questions.
Migration `036_cb_label_columns.py`; filled by `CB_QUESTION_BANK/09_2026/fill_cb_columns.py`
(dry-run by default, one transaction, idempotent — a second run changes 0 rows, and a checksum
guard aborts if any non-`cb_` column moves). Pre-migration backup:
`backups/cb_columns_pre_migration_20260920_221833.dump`.

**§2.9 is decided:** `cb_question_id` went from `UNIQUE` to a plain index, because every copy of a
duplicated question carries its labels. Consequence for §2.8: bank ingest (TASK-27) can no longer
use `ON CONFLICT (cb_question_id)`; it pre-checks `WHERE NOT EXISTS` instead.

**Why `cb_skill_key` keeps Command of Evidence whole.** The textual/quantitative split is this
project's refinement, not College Board's. The column records what CB said; the split is derived
from it at merge time (stem regex, 174/174 agreement with existing annotations — §2b.5).

**`cb_difficulty` vs `difficulty_overall`.** The existing key is a model estimate and agrees with
CB on only ~39% of matched rows (easy→low, hard→high); it says `high` on 3 rows where CB says Hard
on 481. Both are kept. Anything difficulty-driven — adaptive module 2, the diagnostic pool —
should prefer `cb_difficulty` where it is non-null. Switching those readers is a separate change,
not part of this refactor (TASK-29).

**Backfill path for future CB exports:** add the PDF → `audit_labels.py` → `build_full_bank.py` →
`match_bank_to_db.py` → `fill_cb_columns.py --apply`. Every step is idempotent.

### How the merge changes

The skill fill no longer reads a JSON file or infers anything for matched rows. It is a join:

```sql
-- additive: only where the annotation has no skill yet
update question_annotations a
   set annotation_jsonb = a.annotation_jsonb || jsonb_build_object('skill_family_key', <derived>)
  from questions q
 where a.id = q.latest_annotation_id
   and q.cb_skill_key is not null
   and coalesce(a.annotation_jsonb->>'skill_family_key', '') = '';
```

`<derived>` is `q.cb_skill_key`, except `command_of_evidence`, which becomes `_textual` or
`_quantitative` by the stem regex. Conflict reporting (TASK-23) becomes three plain queries
comparing `cb_domain_key` / `cb_skill_key` with the annotation.

## Part 3 — Task list

Dependencies in brackets. Tasks marked **[DB]** are blocked until the port question is settled.

### Phase 0 — Prerequisites & decisions

- [x] **TASK-00** ~~Resolve the 5434/5437 DSN discrepancy; bring the dev stack up; pin one DSN in `scripts/*.py`. *Blocks every [DB] task.*~~
      **Done 2026-09-20** — the running `dsat-db` container maps **5437**, database `dsat_dev`; all 8 scripts already agree. `CLAUDE.md` (5434) was the outlier and is corrected.
- [x] **TASK-01** ~~Decide `stem_type_key` relationship (§2.5): derived-and-asserted, or documented as orthogonal. Record as an ADR under `docs/adr/`.~~
      **Done 2026-09-20** — settled empirically (§2b.4): `stem_type_key` is 100% pure for the two EoI skills, so it is applied *first*, then role/focus. ADR still to be written.
- [ ] **TASK-02** Decide whether `skill_family_key` becomes **required** (non-null) for all verbal
      questions, or stays optional. Recommendation: stays **optional** in the Pydantic model
      throughout — a required field would make every not-yet-filled legacy annotation fail
      validation, which is the one way an additive change can still break reads. Enforce
      completeness with the TASK-24 assertion instead of with the validator.

### Phase 1 — Lock the source of truth

- [x] **TASK-03** ~~Fix the `DOMAINS_SKILLS.md` footnote: the `Cross-text Connections` casing
      variant occurs **3×** (MED, HARD, Results11), not 2×.~~ **Done 2026-09-20** — footnote corrected, verification provenance added. [§1.4]
- [x] **TASK-04** ~~Promote `scratchpad/audit_cb.py` to `CB_QUESTION_BANK/09_2026/audit_labels.py`
      as a committed, re-runnable integrity check.~~ **Done 2026-09-20** — `audit_labels.py`,
      10 assertions, exits non-zero on failure; all pass. Replaced the two ad-hoc scripts.
- [x] **TASK-05** ~~Re-extract the bank JSON over the **full 1,845**.~~ **Done 2026-09-20** —
      `build_full_bank.py` → `09_2026_New_Verbal_Bank_full.json`, 1,845 records, every one with
      difficulty and correct answer. *Simpler than planned:* the three difficulty PDFs carry full
      passage/stem/choices too, so they are the sole source and the Bank PDF is only a cross-check
      (label agreement on all 752 — passes). Surfaced and fixed a parser bug (bug-831). [TASK-04]
- [x] **TASK-06** ~~Re-run the CoE textual/quantitative stem check over all 277 CoE questions.~~
      **Done 2026-09-20** — 277 CoE → **133 quantitative / 144 textual**; zero of the 144 textual
      stems contain `figure|chart|bar graph|graphic|diagram|data`. Derivation is safe to lock. [TASK-05]

### Phase 2 — Validate the map before writing it

- [x] **TASK-07a** ~~**[DB]** **Reconcile the two conflicting overlap figures** (§2.7) by re-running the match over all 1,845 against the live DB. Commit the script and the result; the existing `db_overlap_check.md` covers only the 752-item Bank and must be superseded by a full-pool artifact. *The calibration-set size for everything below depends on this.* [TASK-00]~~
      **Done 2026-09-20** — 733 bank questions ↔ 1,414 DB rows; `db_overlap_full.json` / `.md` supersede `db_overlap_check.md` (§2b.1).
- [x] **TASK-07b** ~~**[DB]** Build the calibration crosstab over whatever TASK-07a returns: CB `skill` (ground truth) × existing `grammar_role_key` / `skill_family_key`. This is the cheapest thing that can falsify the §2.4 map. At n≈669 it carries the grammar side; at n≈55 it validates reading only and Bucket B stays unproven. [TASK-07a]~~
      **Done 2026-09-20** — crosstab over 655 grammar + 759 reading rows; falsified four claims in §2.4 (§2b.4).
- [x] **TASK-08** ~~**[DB]** If TASK-07a lands near the low figure, extend coverage by matching on normalized passage+stem rather than stem alone (the method the 669 figure used). Target ≥200 matched **grammar** questions before trusting Bucket B. [TASK-07b]~~
      **Done 2026-09-20** — not needed — 07a landed at the high figure with 655 grammar calibration rows, well past the ≥200 target.
- [x] **TASK-09** ~~Write `vocabulary/mappings/cb_skill_map.json` — the explicit old→new map with a per-entry `bucket: A|B|C` and a `confidence` field. This file is the single artifact that both the deterministic remap and the `user_progress` backfill read. [TASK-07b, TASK-08]~~
      **Done 2026-09-20** — `vocabulary/mappings/cb_skill_map.json`, **derived** by `calibration_report.py` rather than hand-written; every rule carries n, purity and a deterministic/review status.
- [x] **TASK-10** ~~Hand-adjudicate a 30-question sample from Bucket C to estimate LLM agreement rate before committing to a full LLM pass. [TASK-09]~~
      **Done 2026-09-20** — moot — the residue needing a model shrank from 'most of expression_of_ideas' to a handful of `review` rules; adjudicate those directly in TASK-21.

### Phase 3 — Ontology change (code, no data)

- [ ] **TASK-11** Merge `vocabulary/amendments/pending/amd-1a6b9e6c9e18.json` (rhetorical
      synthesis) — resolve the recorded `conflicting_duplicate_proposal` first.
- [ ] **TASK-12** Edit `vocabulary/master.json`: add `GRAMMAR_SKILL_FAMILY_KEYS` (4) and
      `SKILL_FAMILY_KEYS` (11); re-parent `GRAMMAR_ROLE_KEYS` under the grammar families;
      re-parent `READING_SKILL_FAMILY_KEYS` under `READING_QUESTION_FAMILY_KEYS`. [TASK-11]
- [ ] **TASK-13** `python scripts/gen_vocab.py --generate` → regenerate
      `backend/app/models/ontology.py`. Never hand-edit it. [TASK-12]
- [ ] **TASK-14** Widen `QuestionAnnotation.validate_skill_family_key`
      (`backend/app/models/annotation.py:101`) from `READING_SKILL_FAMILY_KEYS` to
      `SKILL_FAMILY_KEYS`. [TASK-13]
- [ ] **TASK-15** Add a validator rule: `skill_family_key` must be a child of the declared
      `question_family_key` (the 10-pair table in `DOMAINS_SKILLS.md` is the whitelist). This is
      what makes an invalid pairing impossible rather than merely unlikely. [TASK-14]
- [ ] **TASK-16** Update grammar rules docs under `rules_refactor/rules/grammar/` to describe
      skills as the top grammar layer and roles as children. Bump `rules_version`. [TASK-13]
- [ ] **TASK-17** Update the annotate prompt (`backend/app/prompts/annotate_prompt.py`) to request
      `skill_family_key` for grammar questions. [TASK-16]
- [x] **TASK-18** ~~Migration: add `questions.source_bank_question_id VARCHAR(8)`. No such column
      exists today.~~ **Superseded 2026-09-20 — the column already existed.** Migration
      `035_cb_question_id.py` added `questions.cb_question_id VARCHAR(8)` with a unique constraint,
      but the ORM model never declared it, so it was invisible to the app (bug-830). Declared it on
      `Question`, matching the migration exactly. **No new migration needed.** Remaining work moves
      to TASK-27 (populate it). [TASK-13]

### Phase 4 — Data migration

*Every task in this phase is an additive field-level merge. See the governing constraint above.*

- [ ] **TASK-19** **[DB]** **Skill fill from `cb_skill_key`** — the join in Part 2c: add
      `skill_family_key` to the latest annotation of every row where `cb_skill_key` is set and the
      annotation has none. CoE split by stem regex. JSONB key merge; no new `QuestionVersion`; no
      other key touched; existing values never overwritten. Dry-run default with a checksum guard,
      same pattern as `fill_cb_columns.py`. **Blocked on TASK-14** — the four grammar values are
      not legal until the validator is widened. [TASK-14]
- [ ] **TASK-20** **[DB]** **Map fill** — for rows where `cb_skill_key IS NULL` (100 official +
      generated / unofficial), apply `cb_skill_map.json` in order (stem → role/focus → role),
      `deterministic` rules only. Same additive write. Rows landing on a `review` rule get
      `annotation_stale = true` and are counted, not guessed. [TASK-19]
- [ ] **TASK-21** **[DB]** Residue only — whatever TASK-20 left on `review` rules (expected: a
      few dozen rows, chiefly `comma_splice` and `logical_relationships`). Hand-label if the count
      is small; build the narrow single-key classifier only if it is not. The full reannotate path
      stays out of bounds. *Originally scoped as an LLM pass over most of `expression_of_ideas`;
      Phase 2 showed that is unnecessary.* [TASK-20]
- [ ] **TASK-22** **[DB]** `user_progress`: **add** `missed_skill_family_key` (and index it);
      backfill for historical attempts by joining to the question's new value. Existing
      `question_domain` / `missed_*` columns are left exactly as written — nothing is remapped,
      because nothing was renamed. [TASK-19]
- [ ] **TASK-23** **[DB]** **Conflict report, not a rewrite** — plain SQL comparing the `cb_*`
      columns with the annotation: `question_family_key` ≠ `cb_domain_key`, reading
      `skill_family_key` ≠ `cb_skill_key`, Words in Context rows carrying a `grammar_role_key`
      (§2b.5). Correcting them is a rewrite and needs the user's sign-off. [TASK-19]

### Phase 5 — Verify

- [ ] **TASK-24** **[DB]** Assert every active verbal question has a `skill_family_key` and that
      the (family, skill) pair is one of the 10 legal combinations. Zero exceptions.
      **Plus the additive check:** diff every touched `annotation_jsonb` against a pre-migration
      snapshot and assert `skill_family_key` is the *only* key that differs, everywhere. If any
      other key moved, the migration was destructive and must be rolled back. [TASK-21..23]
- [ ] **TASK-25** **[DB]** Re-run the calibration crosstab (TASK-07b) post-migration: agreement
      with CB ground truth should be ~100% on the matched set. This is the acceptance gate. [TASK-24]
- [ ] **TASK-26** **[DB]** Verify the weakness profile and diagnostic pool still return sane
      results (`backend/app/diagnostic/queries.py` — `derive_domain` may now be replaceable by a
      direct `question_family_key` read). [TASK-22]
- [ ] **TASK-27** Ingest the ~1,101 CB questions new to the DB: `questions.id` generated as usual,
      all four `cb_*` columns populated at insert, and `question_family_key` / `skill_family_key`
      seeded from them instead of LLM-classified. Idempotency by `WHERE NOT EXISTS` on
      `cb_question_id` (Part 2c). [TASK-24]
- [ ] **TASK-29** *(follow-up, outside this refactor)* Point difficulty-driven readers — adaptive
      module 2, diagnostic pool, weakness profile — at `cb_difficulty` where non-null, falling back
      to `difficulty_overall`. Needs its own review: it changes student-facing behaviour.
- [ ] **TASK-28** CHANGELOG entry + DEBUG_LOG audit entry; update `.wolf/cerebrum.md` with the
      new ontology shape.

---

## Recommended order

`TASK-00 → 01/02 → 03-06 (source lock) → 07-10 (validate map) → 11-18 (code) → 19-23 (data) → 24-28 (verify)`

The single highest-value early task is **TASK-07**. It costs almost nothing and is the only cheap
thing that can prove the §2.4 grammar map wrong before it is written into `master.json`.
