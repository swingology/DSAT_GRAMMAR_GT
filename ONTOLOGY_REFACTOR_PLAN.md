# Grammar Rules + Ontology Refactor — Plan & Task List

**Date:** 2026-09-20 · **Branch:** RULES_REFACTOR_v3 · **Base commit:** da02823
**Scope:** Verbal only. Math (`CB_QUESTION_BANK/NEW_QUESTION_SETS/Math/`) is explicitly out of scope.
**Target base ontology:** [`DOMAINS_SKILLS.md`](DOMAINS_SKILLS.md) — 4 CB domains × 10 CB skills.

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
split in two). `skill_family_key` becomes universal and **required** for every verbal question.

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

### 2.6 Migration hazards carried forward

1. **Hand-corrected annotations.** `_run_reannotate_pipeline` writes a fresh `QuestionVersion`
   from LLM output — manual fixes (bug-819 PT1 Q13, bug-805 PT5 mod02, bug-811 vocab repair)
   survive in history but stop being current. Exclusion predicate:
   `questions.is_admin_edited = true`, plus any question with a `question_versions` row where
   `change_source = 'admin_edit'`.
2. **`user_progress` is not migrated by reannotate.** `question_domain`,
   `missed_grammar_focus_key`, `missed_reading_focus_key`, `missed_reading_skill_family_key`
   (`backend/app/models/db.py:552-558`) are denormalized onto historical attempt rows. Rename a
   key and the weakness profile silently degrades. Needs its own backfill using the same map.
3. **Migration cursor.** `question_annotations.rules_version` is stamped per annotation — use it
   to select un-migrated rows. `questions.annotation_stale` is the right flag for the queue.
4. **Safety property.** Blocking validation errors route a job to `needs_review` rather than
   writing the row, so a bad ontology surfaces as a review pile, not corruption.
5. **Port discrepancy (prerequisite).** `scripts/reannotate_official_v7.py:31` hardcodes
   `localhost:5437/dsat_dev`; CLAUDE.md and the dev stack say `5434/dsat`. Nothing is listening on
   either right now. Resolve before any task that touches the live DB.

---

## Part 3 — Task list

Dependencies in brackets. Tasks marked **[DB]** are blocked until the port question is settled.

### Phase 0 — Prerequisites & decisions

- [ ] **TASK-00** Resolve the 5434/5437 DSN discrepancy; bring the dev stack up; pin one DSN in
      `scripts/*.py`. *Blocks every [DB] task.*
- [ ] **TASK-01** Decide `stem_type_key` relationship (§2.5): derived-and-asserted, or documented
      as orthogonal. Record as an ADR under `docs/adr/`.
- [ ] **TASK-02** Decide whether `skill_family_key` becomes **required** (non-null) for all verbal
      questions, or stays optional during migration. Recommendation: optional during, required at
      the end, enforced by validator flip in TASK-22.

### Phase 1 — Lock the source of truth

- [x] **TASK-03** ~~Fix the `DOMAINS_SKILLS.md` footnote: the `Cross-text Connections` casing
      variant occurs **3×** (MED, HARD, Results11), not 2×.~~ **Done 2026-09-20** — footnote corrected, verification provenance added. [§1.4]
- [ ] **TASK-04** Promote `scratchpad/audit_cb.py` to `CB_QUESTION_BANK/09_2026/audit_labels.py`
      as a committed, re-runnable integrity check (the nine assertions in §1.3).
- [ ] **TASK-05** Re-extract the bank JSON over the **full 1,845** (not 752), sourcing text from
      the Bank PDF and difficulty + correct answer from the difficulty splits. Output
      `09_2026_New_Verbal_Bank_full.json`. [TASK-04]
- [ ] **TASK-06** Re-run the CoE textual/quantitative stem check over all 1,845 CoE questions
      (277, vs the 123 audited). Confirm zero `figure|chart|bar graph` leakage before locking the
      derivation. [TASK-05]

### Phase 2 — Validate the map before writing it

- [ ] **TASK-07** **[DB]** Build the 55-question calibration crosstab from
      `09_2026/db_overlap_check.md`: CB `skill` (ground truth) × existing
      `grammar_role_key` / `skill_family_key`. This is the cheapest thing that can falsify the
      §2.4 map. *Caveat: n=55, skewed to CB ∩ official tests — validates reading well, grammar
      thinly. Do not oversell the result.* [TASK-00]
- [ ] **TASK-08** **[DB]** Extend calibration: match more of the 1,845 against the DB by
      normalized stem text (the overlap script already does fuzzy matching at ≥0.997). Target
      ≥200 matched grammar questions before trusting Bucket B. [TASK-07]
- [ ] **TASK-09** Write `vocabulary/mappings/cb_skill_map.json` — the explicit old→new map with a
      per-entry `bucket: A|B|C` and a `confidence` field. This file is the single artifact that
      both the deterministic remap and the `user_progress` backfill read. [TASK-07, TASK-08]
- [ ] **TASK-10** Hand-adjudicate a 30-question sample from Bucket C to estimate LLM agreement
      rate before committing to a full LLM pass. [TASK-09]

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
- [ ] **TASK-18** Migration: add `questions.source_bank_question_id VARCHAR(8)` (indexed) so the
      1,845 CB IDs are first-class. No such column exists today. [TASK-13]

### Phase 4 — Data migration

- [ ] **TASK-19** **[DB]** Deterministic remap (Buckets A + B): a Python/SQL script that reads
      `cb_skill_map.json` and writes `skill_family_key` into `annotation_jsonb` **in place**,
      versioned, `change_source='reprocess'`. Must be idempotent and dry-runnable.
      **Excludes `is_admin_edited = true`.** [TASK-09, TASK-14]
- [ ] **TASK-20** **[DB]** Mark Bucket C residue with `annotation_stale = true`; report the count
      per domain before spending anything. [TASK-19]
- [ ] **TASK-21** **[DB]** Scoped LLM reannotate over Bucket C only, reusing
      `POST /reannotate/{question_id}` (it synthesizes `pass1_json` from DB state — no PDF, no
      re-extraction). Adapt `scripts/reannotate_official_v7.py`, which did the v3→v7 migration
      the same way. [TASK-20, TASK-10]
- [ ] **TASK-22** **[DB]** Backfill `user_progress`: add `question_skill_family_key`, and remap
      `question_domain` / `missed_*` keys through `cb_skill_map.json` so historical attempts keep
      pointing at live vocabulary. Without this the weakness profile degrades silently. [TASK-19]
- [ ] **TASK-23** **[DB]** Hand-corrected set: review the excluded `is_admin_edited` questions and
      apply `skill_family_key` manually (should be a small list — size it in TASK-19's dry run).
      [TASK-19]

### Phase 5 — Verify

- [ ] **TASK-24** **[DB]** Assert every active verbal question has a `skill_family_key` and that
      the (family, skill) pair is one of the 10 legal combinations. Zero exceptions. [TASK-21..23]
- [ ] **TASK-25** **[DB]** Re-run the calibration crosstab (TASK-07) post-migration: agreement
      with CB ground truth should be ~100% on the matched set. This is the acceptance gate. [TASK-24]
- [ ] **TASK-26** **[DB]** Verify the weakness profile and diagnostic pool still return sane
      results (`backend/app/diagnostic/queries.py` — `derive_domain` may now be replaceable by a
      direct `question_family_key` read). [TASK-22]
- [ ] **TASK-27** Ingest the 1,845 CB questions with `source_bank_question_id` populated and
      CB-supplied `question_family_key` / `skill_family_key` taken as **ground truth**, bypassing
      LLM classification for those two fields. ~1,170 are new to the DB. [TASK-18, TASK-24]
- [ ] **TASK-28** CHANGELOG entry + DEBUG_LOG audit entry; update `.wolf/cerebrum.md` with the
      new ontology shape.

---

## Recommended order

`TASK-00 → 01/02 → 03-06 (source lock) → 07-10 (validate map) → 11-18 (code) → 19-23 (data) → 24-28 (verify)`

The single highest-value early task is **TASK-07**. It costs almost nothing and is the only cheap
thing that can prove the §2.4 grammar map wrong before it is written into `master.json`.
