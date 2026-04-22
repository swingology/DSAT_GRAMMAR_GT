# alpha-v3-codex Schema & Code Gap Audit

**Date:** 2026-04-04
**Branch:** `alpha-v3-codex`
**Status:** 239/239 tests pass in the **working tree**. All fixes below exist as unstaged edits only — not committed. The committed HEAD still contains all original bugs. Migrations 014–037.

---

## What's Committed is Stable

The following were confirmed absent or correct in the committed HEAD (pre-working-tree):

- `primary_solver_steps_jsonb` in upsert — not present (migration 034 dropped it)
- `target_distractor_pattern_jsonb` / `target_topic_constraints_jsonb` in upsert — not present (migration 032 dropped them)
- Model has all `target_lexile_min/max`, `target_word_count_min/max`, `target_passage_source_type_key`
- `target_distractor_construction_key`, `target_syntactic_*_key` present in `_GENERATION_PROFILE_FIELDS`
- `stimulus_mode_key` present in `_EXTRACT_FIELDS` (proposals.py:108)
- All three upserts (classification, reasoning, generation profiles) have matching INSERT cols and SET clauses — validated with line-isolated parsing

---

## Genuine Bugs (Working-Tree Fixes Uncommitted)

All items below have fixes in the working tree. Run `uv run pytest tests/ -v` to confirm 239/239 pass. Nothing is committed yet.

### Bug 1 — `subskill` in model + upsert but dropped from DB by migration 030

**Severity:** High — runtime crash on fresh DB
**Files affected:**
- `annotation.py` — `ClassificationAnnotation` has `subskill: str` field
- `upsert.py` — `question_classifications` INSERT lists `subskill`, SET updates it, Python params pass `c.subskill`
- `pass2_annotation.py` — output schema includes `"subskill"`

**Root cause:** Migration 025 creates the `question_classifications` table without `subskill`. Migration 030 drops `subskill` from the column. But the model still has it and upsert.py still writes it. On a fresh DB (014+), the column does not exist, so every upsert fails with `column "subskill" does not exist`.

**Working-tree fix:** Remove `subskill` from all three files.

---

### Bug 2 — `passage_source_key` vs `passage_source_type_key` column name collision

**Severity:** High — silent wrong-column writes
**Files affected:**
- `annotation.py:158` — model field is `passage_source_key` (the WRONG name — DB column is `passage_provenance_key`)
- `upsert.py` — writes `c.passage_source_key` → maps to the `passage_source_key` model field which is wrong
- `migration 020` — `v_item_anatomy_profile` view references `qc.domain` (non-existent column since migration 025) and `qc.passage_source_key` (wrong name)

**Root cause:** Two separate columns with similar names:
- `passage_provenance_key` (migration 020) — whether original/adapted/AI-generated/public_domain
- `passage_source_type_key` (migration 024) — genre: academic_journal, literary_fiction, etc.

The model uses `passage_source_key` which matches neither. On upsert, `c.passage_source_key` (Literal model field) gets written to `passage_source_key` column but that column doesn't exist. The `passage_provenance_key` column (the one the DB actually has) silently remains NULL.

**Working-tree fix:** Rename model field to `passage_provenance_key`; fix migration 020 view to use correct column names.

---

### Bug 3 — `target_evidence_distribution_key` missing from Pass 2 prompt, model, and upsert

**Severity:** Low — silent NULL on all generation profiles
**Files affected:**
- `pass2_annotation.py` — not in output schema
- `annotation.py` — not in `GenerationProfileAnnotation`
- `upsert.py` — not in INSERT/SET/params for `question_generation_profiles`
- `ontology.py` — present in `FIELD_TO_TABLE` and `LOOKUP_TABLES` since migration 031

**Working-tree fix:** Add to all three layers.

---

### Bug 4 — `ontology_ref.py` only rendered 12 of 41 lookup tables

**Severity:** Moderate — incomplete ontology injection
**File:** `ontology_ref.py:7–20`

`render_ontology_reference()` labels dict has only 12 tables. All prose/complexity/discourse/style/taxonomy fields are absent from the Pass 2 `=== ONTOLOGY REFERENCE ===` section.

**Working-tree fix:** Add all 41 tables to the `labels` dict.

---

### Bug 5 — Pass 1 prompt `stimulus_mode_key`: 8 values, duplicate, wrong count

**Severity:** Moderate — LLM can never emit 4 missing values
**File:** `pass1_extraction.py:26`

Current (committed): `sentence_only | passage_excerpt | prose_single | prose_paired | prose_plus_table | prose_plus_graph | notes_bullets | poem | passage_only | dual_passage | no_stimulus | graphic_and_passage`

Problems:
- `passage_only` appears **twice** (duplicate)
- Missing from prompt: `prose_plus_table`, `prose_plus_graph`, `notes_bullets`, `poem` (wait — those ARE present)
- Actually missing: `passage_only`, `dual_passage`, `no_stimulus`, `graphic_and_passage` — 4 values absent

**Working-tree fix:** Replace line with full 12-value list from `lookup_stimulus_mode` in conftest.py, no duplicates.

---

### Bug 6 — Pass 1 prompt `stem_type_key`: 3 values missing

**Severity:** Moderate
**File:** `pass1_extraction.py:27`

Missing: `fill_in_the_blank`, `direct_question`, `command`. These are used in `VALID_PASS1_DATA` but absent from the prompt's allowed-values list.

**Working-tree fix:** Add `| fill_in_the_blank | direct_question | command` to the line.

---

### Bug 7 — `drift.py` SOFT_DIMENSIONS maps to wrong column `passage_source_key`

**Severity:** High — drift detection always misses passage source type drift
**File:** `pipeline/drift.py:21`

```python
SOFT_DIMENSIONS: dict[str, str] = {
    ...
    "target_passage_source_type_key":  "passage_source_key",  # WRONG
    ...
}
```

The DB column is `passage_provenance_key` (migration 020). `passage_source_key` does not exist in `question_classifications`. This means any generation run targeting a specific passage source type will silently fail drift detection on that dimension — the expected value is compared against the wrong column, which is always NULL, so the comparison is skipped.

**Working-tree fix:** Change `"passage_source_key"` → `"passage_provenance_key"` in SOFT_DIMENSIONS.

---

### Bug 8 — `v_item_anatomy_profile` references `qc.domain` (should be `qc.domain_key`)

**Severity:** High — view broken on any DB with questions
**File:** `migrations/020_item_anatomy_passage_fingerprint.sql:310`

```sql
SELECT
    qc.domain,           -- WRONG: column does not exist
    qc.question_family_key,
    ...
```

Migration 025 renamed `domain` → `domain_key`. The view was created in migration 020 and never updated. Every query against `v_item_anatomy_profile` fails with `column qc.domain does not exist`.

**Working-tree fix:** Change `qc.domain` → `qc.domain_key` in the view definition.

---

### Bug 8 — `v_option_anatomy_distribution` references `qo.distractor_type_key` (does not exist)

**Severity:** High — view broken on fresh 014+ DB
**File:** `migrations/020_item_anatomy_passage_fingerprint.sql:335`

```sql
SELECT ... qo.distractor_type_key ...
```

In the deprecated 001–006 migrations, `question_options` had a `distractor_type_key` column referencing `lookup_distractor_type`. In the 014+ migration path, this column was **never added** — only `distractor_subtype_key` was ever added (migration 025). The view references a column that doesn't exist, making the entire view fail on `CREATE OR REPLACE`.

**Working-tree fix:** Replace `qo.distractor_type_key` with `qo.distractor_subtype_key` in the view (and add `qo.distractor_construction_key` since Part 6 added that column but the view's SELECT and GROUP BY missed it).

---

## Deferred (No Working-Tree Fix)

### Deferred 1 — Character-Level Span Offsets never migrated

**Severity:** Moderate
**Proposal doc:** `FULL_PLAN/docs/FUTURE_PLANS.md`

Requires: `blank_char_start/end`, `evidence_char_start/end` on `question_classifications`; `anchor_text`, `anchor_char_start/end` on `question_options`.

---

### Deferred 2 — Multi-Stage Derivation Tracking never migrated

**Severity:** Moderate
**Proposal doc:** `FULL_PLAN/docs/FUTURE_PLANS.md`

Requires: `questions.parent_question_id` + `question_revisions` table.

---

## Summary

| Priority | Item | Working-Tree Fix |
|----------|------|-----------------|
| **High** | `subskill` in model+upsert but dropped from DB | Remove from annotation.py, upsert.py, pass2_annotation.py |
| **High** | `passage_source_key` wrong name — provenance silently NULL | Rename to `passage_provenance_key` in model + migration 020 view fix |
| **Moderate** | Pass 1 `stimulus_mode_key` 8/12 values + duplicate | Sync to full 12-value list, dedupe |
| **Moderate** | Pass 1 `stem_type_key` missing 3 values | Add `fill_in_the_blank \| direct_question \| command` |
| **Moderate** | `ontology_ref.py` renders 12/41 tables | Add all 41 to labels dict |
| **Low** | `target_evidence_distribution_key` absent from prompt/model/upsert | Add to all three layers |
| **Moderate** | Character-level span offsets | Deferred |
| **Moderate** | Derivation tracking | Deferred |
