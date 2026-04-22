# Migrations PRD: Schema Excellence for DSAT Question Intelligence

**Document Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Draft — Pending Engineering Review  
**References:** `docs/GRAMMAR_GUIDE/GROUND_TRUTH_GRAMMAR.md` v1.2, `taxonomy/DSAT_Verbal_Master_Taxonomy_v2.md` v2.6, migrations 001–042

---

## Executive Summary

The current DSAT schema (migrations 001–042) achieves functional but uneven performance across three core intelligence goals. This PRD specifies migrations 043–060 to close the identified gaps and reach excellence at each goal.

| Goal | Current Grade | Target Grade | Primary Gap |
|------|:---:|:---:|---|
| Reading & analyzing actual test questions | B+ | A | Missing grammar_focus completeness, no word-count metadata, no structural "No Change" marker, image ingestion gap |
| Explaining why an answer is correct | C+ | B+ | Dropped `primary_solver_steps_jsonb` never replaced; coaching spans lack option linkage; no structured solver steps table |
| Generating questions as realistic as the real test | B- | B+ | Missing empirical frequency data, no paired passage support, target_* mirror-status tracking absent, per-slot distractor profiles missing |

Migration block overview:

| Block | Migrations | Goal Addressed |
|-------|-----------|----------------|
| **A – Ingestion Fidelity** | 043–048 | Goal 1: Reading & analyzing |
| **B – Explanation Depth** | 049–053 | Goal 2: Explaining correctness |
| **C – Generation Realism** | 054–060 | Goal 3: Realistic generation |

---

## Goal 1: Reading & Analyzing Actual Test Questions

### Current State (B+)

**Strengths:**
- 41-table lookup taxonomy fully FK-enforced in the validator
- SHA-256 content hash deduplication prevents duplicate ingestion
- `question_ingestion_jobs` staging table captures full Pass 1 / Pass 2 JSON for audit
- `lookup_grammar_role` (7 roles) + `lookup_grammar_focus` (27 keys after migration 042) covers the majority of SEC question types

**Gaps identified against `GROUND_TRUTH_GRAMMAR.md` v1.2 and `DSAT_Verbal_Master_Taxonomy_v2.md` v2.6:**

1. **Missing grammar_focus_key values** (§GROUND_TRUTH §3, Taxonomy §7.9):
   - `run_on_sentence` — listed as v2.6 addition, maps to `sentence_boundary` role, NOT in any migration
   - `colon_dash_use` — listed as v2.5 addition, maps to `punctuation` role, NOT in any migration
   - `appositive_punctuation` — defined in GROUND_TRUTH §3.4, maps to `punctuation` role, NOT in migrations
   - `quotation_punctuation` — defined in GROUND_TRUTH §3.4, maps to `punctuation` role, NOT in migrations
   - `preposition_idiom` — added in v1.2 as priority 12 in disambiguation rules (GROUND_TRUTH §5.12), NOT in migrations

2. **No structural marker for "No Change" questions** (GROUND_TRUTH §8.1):
   - ~20% of SEC questions have "NO CHANGE" as correct answer
   - These require different solver step logic (validate what's already there, not what to fix)
   - No boolean or enum tracks this distinction at the DB layer

3. **Multi-error question handling** (GROUND_TRUTH §8.2):
   - Questions with 2+ grammar errors should classify by primary error only
   - No `multi_error_flag` or `primary_error_field` to record this decision

4. **No passage/stem word count metadata** (needed for Lexile validation and generation targeting):
   - `questions.passage_text` is stored but word count is never computed
   - DSAT passages range 25–150 words (specified in Pass 2 prompt); there is no DB-layer enforcement

5. **Image question ingestion gap**:
   - `question_images` table listed in CLAUDE.md but not present in any migration 001–042
   - Questions with charts, graphs, or tables cannot be ingested without OCR text storage

6. **`topic_broad` / `topic_fine` are free-text**:
   - No normalization; inconsistent LLM outputs cause false duplicates and break topic-based analysis
   - No `lookup_passage_topic_fine` table exists

7. **SEC grammar_focus enforcement is app-layer only**:
   - Taxonomy §7.8: "if domain_key = 'standard_english_conventions', grammar_role_key AND grammar_focus_key must be non-null"
   - Currently enforced only in `validator.py`; a direct DB write bypasses this rule

---

### Migration 043 — `question_images` Table

**Problem:** Questions containing charts, tables, or infographics cannot be stored or analyzed without a dedicated image store. OCR text from image ingestion has nowhere to go.

**Solution:** Create `question_images` with OCR text, raw image bytes, and vision model description.

```sql
CREATE TABLE question_images (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    image_source    text NOT NULL CHECK (image_source IN ('pdf_extract', 'upload', 'url')),
    image_data      bytea,
    ocr_text        text,
    alt_description text,              -- vision model output
    display_order   smallint NOT NULL DEFAULT 1,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_question_images_question_id ON question_images(question_id);
```

**App-layer changes:**
- `parsers/image_parser.py`: write OCR output to `ocr_text` column
- `pipeline/ingest.py`: call vision model if `image_data` present; store result in `alt_description`
- Pass 1 prompt: include `alt_description` in assembled context when available

---

### Migration 044 — Computed Word Count Columns

**Problem:** Pass 2 prompt specifies passage word count bands (25–50, 51–100, 101–150 words), but word count is never stored. Lexile range validation and generation targeting both need this.

**Solution:** Add `passage_word_count` and `stem_word_count` integer columns with an AFTER INSERT OR UPDATE trigger that computes them from `passage_text` and `stem`.

```sql
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS passage_word_count int,
    ADD COLUMN IF NOT EXISTS stem_word_count    int;

CREATE OR REPLACE FUNCTION fn_set_word_counts()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.passage_word_count := array_length(
        regexp_split_to_array(trim(NEW.passage_text), '\s+'), 1
    );
    NEW.stem_word_count := array_length(
        regexp_split_to_array(trim(NEW.stem), '\s+'), 1
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_set_word_counts
    BEFORE INSERT OR UPDATE OF passage_text, stem
    ON questions
    FOR EACH ROW EXECUTE FUNCTION fn_set_word_counts();
```

**Constraint:** Add a CHECK on `passage_word_count` for non-null passages:

```sql
ALTER TABLE questions ADD CONSTRAINT chk_passage_word_count
    CHECK (passage_text IS NULL OR passage_word_count BETWEEN 1 AND 500);
```

**App-layer changes:**
- `pipeline/ingest.py` upsert path: no changes needed (trigger fires automatically)
- `v_corpus_fingerprint`: add `AVG(passage_word_count)` to style fingerprint aggregation

---

### Migration 045 — Normalize `topic_broad` / `topic_fine`

**Problem:** `questions.topic_broad` and `questions.topic_fine` are free-text columns. LLM variation (e.g., "US History", "U.S. History", "american history") creates false distinct values and breaks topic-based analysis.

**Solution:** Create `lookup_passage_topic_fine` referencing `lookup_domain`. Convert free-text columns to FK columns via a two-step migration (add FK columns, backfill with a mapping function, drop old columns).

```sql
-- Step 1: Lookup table
CREATE TABLE lookup_passage_topic_fine (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    domain_key   text NOT NULL REFERENCES lookup_domain(key),
    sort_order   int  NOT NULL DEFAULT 0
);

INSERT INTO lookup_passage_topic_fine (key, display_name, domain_key, sort_order) VALUES
  ('us_history',          'U.S. History',               'history_social_studies', 10),
  ('world_history',       'World History',               'history_social_studies', 20),
  ('economics',           'Economics',                   'history_social_studies', 30),
  ('civics_government',   'Civics & Government',         'history_social_studies', 40),
  ('biology',             'Biology',                     'science',                10),
  ('chemistry',           'Chemistry',                   'science',                20),
  ('physics',             'Physics',                     'science',                30),
  ('earth_science',       'Earth Science',               'science',                40),
  ('literary_fiction',    'Literary Fiction',            'literature',             10),
  ('narrative_nonfiction','Narrative Nonfiction',        'literature',             20),
  ('personal_essay',      'Personal Essay',              'literature',             30),
  ('argumentative_essay', 'Argumentative Essay',         'literature',             40),
  ('humanities',          'Humanities',                  'literature',             50),
  ('sec_no_passage',      'SEC (No Passage)',            'standard_english_conventions', 10);

-- Step 2: Add FK column alongside free-text (backfill separately)
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS topic_fine_key text REFERENCES lookup_passage_topic_fine(key);

-- Step 3: After backfill script runs, drop old free-text columns
-- (Run in a subsequent deployment step)
-- ALTER TABLE questions DROP COLUMN topic_fine;
-- ALTER TABLE questions DROP COLUMN topic_broad;
```

**App-layer changes:**
- Pass 2 prompt: replace free-text topic field with an enum list from `lookup_passage_topic_fine`
- `models/annotation.py`: replace `topic_fine: str` with `topic_fine_key: str` validated against ontology
- `pipeline/validator.py`: add `topic_fine_key` to FK validation list
- `pipeline/upsert.py`: write `topic_fine_key` instead of `topic_fine`

---

### Migration 046 — "No Change" and Multi-Error Markers

**Problem:** GROUND_TRUTH §8.1 describes "NO CHANGE" answer questions (~20% of SEC): the correct answer validates the existing text rather than fixing it. The solver steps differ fundamentally from fix-type questions. GROUND_TRUTH §8.2 describes multi-error questions where classification picks the primary error. Neither case is tracked at the DB layer.

**Solution:** Add three columns to `question_classifications`.

```sql
ALTER TABLE question_classifications
    ADD COLUMN IF NOT EXISTS no_change_is_correct  boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS multi_error_flag       boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS primary_error_field    text;

-- Validate that primary_error_field names a real grammar_focus_key
ALTER TABLE question_classifications
    ADD CONSTRAINT fk_primary_error_grammar_focus
        FOREIGN KEY (primary_error_field)
        REFERENCES lookup_grammar_focus(key)
        DEFERRABLE INITIALLY DEFERRED;

-- Rule: primary_error_field must be set when multi_error_flag is true
ALTER TABLE question_classifications
    ADD CONSTRAINT chk_multi_error_primary_required
        CHECK (NOT multi_error_flag OR primary_error_field IS NOT NULL);
```

**Pass 2 prompt changes:**
- Add rule: "If correct_option_label's text is 'NO CHANGE', set `no_change_is_correct: true`"
- Add rule: "If the question tests more than one grammar rule, set `multi_error_flag: true` and `primary_error_field` to the dominant rule's grammar_focus_key"

---

### Migration 047 — SEC Grammar Enforcement Trigger

**Problem:** Taxonomy §7.8 requires that SEC questions (domain_key = 'standard_english_conventions') have non-null `grammar_role_key` and `grammar_focus_key`. This is enforced only in `validator.py`. A direct upsert or admin action bypasses it.

**Solution:** Add a DB-level BEFORE INSERT OR UPDATE trigger on `question_classifications`.

```sql
CREATE OR REPLACE FUNCTION fn_enforce_sec_grammar_fields()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.domain_key = 'standard_english_conventions' THEN
        IF NEW.grammar_role_key IS NULL THEN
            RAISE EXCEPTION 'grammar_role_key required for SEC questions (domain_key = standard_english_conventions)';
        END IF;
        IF NEW.grammar_focus_key IS NULL THEN
            RAISE EXCEPTION 'grammar_focus_key required for SEC questions (domain_key = standard_english_conventions)';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_sec_grammar
    BEFORE INSERT OR UPDATE OF domain_key, grammar_role_key, grammar_focus_key
    ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_enforce_sec_grammar_fields();
```

**No app-layer changes required** — the validator already enforces this; the trigger adds defense-in-depth.

---

### Migration 048 — Missing `lookup_grammar_focus` Keys

**Problem:** Five grammar_focus_key values are defined in authoritative taxonomy sources but absent from all 42 migrations:

| Key | Source | Role mapping |
|-----|--------|-------------|
| `run_on_sentence` | Taxonomy v2.6 (new in v2.6) | `sentence_boundary` |
| `colon_dash_use` | Taxonomy v2.5, GROUND_TRUTH §3.3 | `punctuation` |
| `appositive_punctuation` | GROUND_TRUTH §3.4 | `punctuation` |
| `quotation_punctuation` | GROUND_TRUTH §3.4 | `punctuation` |
| `preposition_idiom` | GROUND_TRUTH §5.12, v1.2 | `verb_form` (closest role; see note) |

> **Note on `preposition_idiom`**: GROUND_TRUTH §5.12 adds it as priority 12 to the grammar_focus disambiguation rules. The Taxonomy v2.6 `grammar_focus_key → grammar_role_key` mapping table does not yet list this key. Assign it to `verb_form` as the closest available role pending a taxonomy update; the `lookup_grammar_focus` table should add a `grammar_role_key` denorm column in this migration to make the mapping queryable.

```sql
-- Add grammar_role_key denorm to lookup_grammar_focus for queryability
ALTER TABLE lookup_grammar_focus
    ADD COLUMN IF NOT EXISTS grammar_role_key text REFERENCES lookup_grammar_role(key);

-- Backfill existing keys' role mappings
UPDATE lookup_grammar_focus SET grammar_role_key = 'sentence_boundary'
    WHERE key IN ('comma_splice','sentence_fragment','sentence_boundary');
UPDATE lookup_grammar_focus SET grammar_role_key = 'agreement'
    WHERE key IN ('subject_verb_agreement','pronoun_antecedent_agreement','noun_countability');
UPDATE lookup_grammar_focus SET grammar_role_key = 'pronoun'
    WHERE key IN ('pronoun_case');
UPDATE lookup_grammar_focus SET grammar_role_key = 'modifier'
    WHERE key IN ('modifier_placement','logical_predication','comparative_structures','relative_pronouns');
UPDATE lookup_grammar_focus SET grammar_role_key = 'verb_form'
    WHERE key IN ('verb_tense_consistency','verb_form','voice_active_passive',
                  'affirmative_agreement','negation','elliptical_constructions');
UPDATE lookup_grammar_focus SET grammar_role_key = 'parallel_structure'
    WHERE key IN ('parallel_structure','conjunction_usage');
UPDATE lookup_grammar_focus SET grammar_role_key = 'punctuation'
    WHERE key IN ('semicolon_use','apostrophe_use','punctuation_comma',
                  'possessive_contraction','hyphen_usage');

-- Insert the 5 missing keys
INSERT INTO lookup_grammar_focus (key, display_name, grammar_role_key, sort_order) VALUES
    ('run_on_sentence',       'Run-On Sentence',          'sentence_boundary', 35),
    ('colon_dash_use',        'Colon / Dash Use',         'punctuation',       55),
    ('appositive_punctuation','Appositive Punctuation',   'punctuation',       56),
    ('quotation_punctuation', 'Quotation Punctuation',    'punctuation',       57),
    ('preposition_idiom',     'Preposition & Idiom',      'verb_form',         95);

-- Add disambiguation priority column for Pass 2 prompt ordering
ALTER TABLE lookup_grammar_focus
    ADD COLUMN IF NOT EXISTS disambiguation_priority smallint;

UPDATE lookup_grammar_focus SET disambiguation_priority = CASE key
    WHEN 'comma_splice'                    THEN 1
    WHEN 'sentence_fragment'               THEN 2
    WHEN 'run_on_sentence'                 THEN 3
    WHEN 'subject_verb_agreement'          THEN 4
    WHEN 'pronoun_antecedent_agreement'    THEN 5
    WHEN 'pronoun_case'                    THEN 6
    WHEN 'modifier_placement'              THEN 7
    WHEN 'logical_predication'             THEN 8
    WHEN 'parallel_structure'              THEN 9
    WHEN 'verb_tense_consistency'          THEN 10
    WHEN 'verb_form'                       THEN 11
    WHEN 'preposition_idiom'               THEN 12
    ELSE 99
END;
```

**Pass 2 prompt changes:**
- Regenerate the `GRAMMAR_FOCUS_KEYS` block in `ontology_ref.py` from the live table (already done dynamically — just needs the new rows to appear)
- Confirm disambiguation priority order in prompt matches `disambiguation_priority` column

**Validator changes:**
- No changes required; FK validation against `lookup_grammar_focus` will automatically include the new keys

---

## Goal 2: Explaining Why an Answer Is Correct

### Current State (C+)

**Strengths:**
- `question_coaching_annotations` stores span-level highlights (7 types: syntactic_trap, key_evidence, np_cluster, clause_boundary, blank_context, distractor_lure, rhetorical_move)
- `coaching_summary` on `question_reasoning` provides 2–4 sentence prose explanation
- `question_reasoning` stores `solver_pattern_key`, `hidden_clue_type_key`, `evidence_span_text`

**Critical gaps:**

1. **`primary_solver_steps_jsonb` was dropped in migration 034 and never structurally replaced.** The field stored step-by-step solver reasoning. After its removal, there is no structured representation of how a solver works through a question. `evidence_span_text` is a single free-text field — not steps.

2. **Coaching spans are not linked to specific answer options.** `question_coaching_annotations` has no `option_label` column — a span marked `distractor_lure` cannot indicate *which* option it implicates.

3. **No structured contrast between correct answer and distractors.** `question_options.why_wrong` exists but is free-text and not contrasted against the correct answer specifically.

4. **`explanation_short` / `explanation_full` on `questions`** were intended as pipeline outputs but the Pass 2 prompt marks them as legacy and does not populate them. Their purpose is ambiguous and they conflict with the coaching layer.

5. **Character-level evidence location is absent.** `evidence_span_text` on `question_reasoning` is free-text. Finding *where in the passage* the evidence lives requires re-parsing.

---

### Migration 049 — Option Linkage in Coaching Annotations

**Problem:** `question_coaching_annotations` marks spans but cannot indicate which answer option a span implicates. A `distractor_lure` span needs to be tied to option B, C, or D specifically for full explanation coverage.

**Solution:** Add `option_label` and a coaching completion status flag.

```sql
ALTER TABLE question_coaching_annotations
    ADD COLUMN IF NOT EXISTS option_label char(1)
        CHECK (option_label IN ('A','B','C','D'));

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS coaching_completion_status text
        NOT NULL DEFAULT 'pending'
        CHECK (coaching_completion_status IN ('pending','ready','failed'));

COMMENT ON COLUMN question_coaching_annotations.option_label IS
    'If this span implicates a specific answer option, record it here. NULL means applies to the stem/passage globally.';
COMMENT ON COLUMN questions.coaching_completion_status IS
    'Tracks whether the coaching annotation pipeline has completed for this question.';
```

**Pass 2 prompt changes:**
- `coaching_annotations` items: add optional `option_label` field
- Rule: "For `distractor_lure` spans, always populate `option_label` with the distractor option it describes"
- Rule: "For `key_evidence` spans that justify the correct answer, set `option_label` to the correct option label"

---

### Migration 050 — Structured `solver_steps` Table

**Problem:** `primary_solver_steps_jsonb` was dropped in migration 034. It stored the step-by-step solver reasoning that is essential for explanation generation. Nothing replaced it. The coaching layer stores span annotations but not the reasoning *sequence* that connects them.

**Solution:** Create a normalized `solver_steps` table that formalizes the replacement.

```sql
CREATE TABLE solver_steps (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id           uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    step_index            smallint NOT NULL CHECK (step_index BETWEEN 1 AND 10),
    step_type_key         text NOT NULL REFERENCES lookup_reasoning_step_type(key),
    step_description      text NOT NULL,
    step_evidence_text    text,           -- quoted excerpt from passage/stem
    grammar_rule_applied  text REFERENCES lookup_grammar_focus(key),  -- SEC questions
    created_at            timestamptz NOT NULL DEFAULT now(),

    UNIQUE (question_id, step_index)
);

CREATE INDEX idx_solver_steps_question_id ON solver_steps(question_id);

COMMENT ON TABLE solver_steps IS
    'Structured replacement for the dropped primary_solver_steps_jsonb column (migration 034). '
    'Each row is one step in the expert solver path through the question.';
```

**Pass 2 prompt changes:**
- Add `solver_steps` array output field (replaces the dropped field)
- Each item: `{ step_index, step_type, step_description, step_evidence_text, grammar_rule_applied }`
- Rule: "SEC questions must include a `grammar_rule_applied` step that names the rule being tested"
- Provide `lookup_reasoning_step_type` key list in prompt context

**App-layer changes:**
- `models/annotation.py`: Add `SolverStep` and `ReasoningAnnotation.solver_steps: list[SolverStep]`
- `pipeline/upsert.py`: Insert rows into `solver_steps` from `pass2_json`

---

### Migration 051 — Deprecate Legacy Explanation Columns

**Problem:** `questions.explanation_short` and `questions.explanation_full` were marked as legacy in the Pass 2 prompt comments but no DB-layer record of their deprecated status exists. Consumers may write to them, creating confusion about which explanation source is authoritative.

**Solution:** Add a `canonical_explanation_source` enum that records which layer owns the explanation, and add deprecation comments to the legacy columns.

```sql
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS canonical_explanation_source text
        CHECK (canonical_explanation_source IN ('coaching_layer','solver_steps','legacy'))
        DEFAULT 'legacy';

COMMENT ON COLUMN questions.explanation_short IS
    'DEPRECATED as of migration 051. Use question_coaching_annotations + coaching_summary instead. '
    'Retained for backward compatibility with pre-migration 049 data.';

COMMENT ON COLUMN questions.explanation_full IS
    'DEPRECATED as of migration 051. Use solver_steps table instead. '
    'Retained for backward compatibility with pre-migration 049 data.';

COMMENT ON COLUMN questions.canonical_explanation_source IS
    'coaching_layer = question_coaching_annotations + coaching_summary is authoritative. '
    'solver_steps = solver_steps table is authoritative. '
    'legacy = explanation_short/explanation_full (pre-migration 049 data only).';
```

**App-layer changes:**
- `pipeline/upsert.py`: Set `canonical_explanation_source = 'coaching_layer'` for all new upserts
- Admin UI: Use `canonical_explanation_source` to determine which field to display in review UI

---

### Migration 052 — Distractor Contrast Notes

**Problem:** `question_options.why_wrong` explains why an option is incorrect in isolation. It does not explain *how it differs from the correct answer* — the key insight for SAT prep (why did this option fool students? what's the contrast?).

**Solution:** Add `distractor_contrast_note` for structured contrast explanation.

```sql
ALTER TABLE question_options
    ADD COLUMN IF NOT EXISTS distractor_contrast_note text;

COMMENT ON COLUMN question_options.distractor_contrast_note IS
    'For incorrect options: explains the specific contrast with the correct answer. '
    'Goes beyond why_wrong to describe the eliminability mechanism. NULL for the correct option.';
```

**Pass 2 prompt changes:**
- Add `distractor_contrast_note` to `OptionAnnotation` output for each incorrect option
- Rule: "Contrast note should reference the specific evidence or rule that makes the correct option clearly superior, not just why this option is wrong"

---

### Migration 053 — Character-Level Evidence Span on `question_reasoning`

**Problem:** `question_reasoning.evidence_span_text` is free text. There is no character offset linking it to the passage, making it impossible for the app to highlight the passage at the correct location automatically.

**Solution:** Add character offset columns to `question_reasoning`. The offsets reference `questions.passage_text` by character position.

```sql
ALTER TABLE question_reasoning
    ADD COLUMN IF NOT EXISTS evidence_span_start_char int,
    ADD COLUMN IF NOT EXISTS evidence_span_end_char   int;

ALTER TABLE question_reasoning
    ADD CONSTRAINT chk_evidence_span_offsets
        CHECK (
            (evidence_span_start_char IS NULL AND evidence_span_end_char IS NULL)
            OR (evidence_span_start_char IS NOT NULL
                AND evidence_span_end_char IS NOT NULL
                AND evidence_span_start_char >= 0
                AND evidence_span_end_char > evidence_span_start_char)
        );

COMMENT ON COLUMN question_reasoning.evidence_span_start_char IS
    'Zero-based character offset of key evidence start in questions.passage_text. '
    'NULL for SEC questions without a passage.';
COMMENT ON COLUMN question_reasoning.evidence_span_end_char IS
    'Zero-based character offset of key evidence end (exclusive) in questions.passage_text.';
```

**Pass 2 prompt changes:**
- Add `evidence_span_start_char` and `evidence_span_end_char` integer fields to reasoning output
- Rule: "For passage-based questions, locate the key evidence span and provide character offsets. For SEC or sentence-only questions, leave null."

---

## Goal 3: Generating Questions as Realistic as the Real Test

### Current State (B-)

**Strengths:**
- `v_corpus_fingerprint` view aggregates official CB question style fingerprints by question family
- Generation conformance gate: generated questions annotated and compared against fingerprint (max 3 retries)
- `question_generation_profiles` has ~40 `target_*` columns mirroring classification
- `generation_templates` table with 9 seeded templates (migration 038)
- Drift detection: `pipeline/generation/drift.py` compares annotation against `target_constraints` snapshot

**Gaps:**

1. **No empirical frequency distribution for grammar_focus_key values.** GROUND_TRUTH §5 and Taxonomy §7.10 provide per-module frequency data (e.g., `punctuation_comma` and `subject_verb_agreement` appear 2–3 times per module; `affirmative_agreement` and `negation` appear 0 times — they're ACT-adjacent). Without this data in the DB, the generation system cannot set realistic distribution targets.

2. **`question_generation_profiles` is missing `target_grammar_role_key`.** The profile has `target_grammar_focus_key` but not the parent role. A generator targeting a SEC question cannot know which role family to sample from without re-deriving it.

3. **No cross-dimension semantic validation.** Contradictory classification bundles (e.g., `passage_source_type='literary_fiction'` + `lexical_tier='academic'` + `epistemic_stance='assertive'`) can be stored and then used as generation targets, producing unrealistic questions.

4. **Per-slot distractor profiles are absent.** The corpus fingerprint tracks distractor types in aggregate, but generation cannot specify *which* distractor type to place in slot B vs. D. Realistic SAT distractors have a structural distribution.

5. **No quantitative IRT adjustment for quantitative questions.** Tables, graphs, and charts add reading/reasoning difficulty beyond what the text-based IRT formula captures. `fn_compute_irt_b_v1()` has no way to account for this.

6. **`target_*` fields in `question_generation_profiles` are not tracked for mirror status.** There is no way to know if a profile's `target_*` fields were auto-populated from classification (good — consistent) or manually set (risky — may be inconsistent) or drifted (LLM wrote inconsistent values).

7. **Paired passage questions have no set linkage.** Two questions that reference the same paired passages must be retired together; currently there is no mechanism to enforce this or even track the pairing.

---

### Migration 054 — `grammar_focus_frequency` Table

**Problem:** Generation needs empirical per-module frequency data for grammar_focus_key values to produce realistic SEC question distributions. GROUND_TRUTH §5 and Taxonomy §7.10 provide this data but it is not stored in the DB.

**Solution:** Create `grammar_focus_frequency` with per-module statistics from authoritative sources.

```sql
CREATE TABLE grammar_focus_frequency (
    grammar_focus_key       text PRIMARY KEY REFERENCES lookup_grammar_focus(key),
    avg_questions_per_module numeric(4,2) NOT NULL DEFAULT 0,
    frequency_label         text NOT NULL
        CHECK (frequency_label IN ('very_high','high','medium','low','very_low','not_tested')),
    is_dsat_confirmed       boolean NOT NULL DEFAULT false,
    source_tests            text[] NOT NULL DEFAULT '{}',
    notes                   text,
    last_updated_at         timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE grammar_focus_frequency IS
    'Empirical frequency data for grammar_focus_key values derived from GROUND_TRUTH_GRAMMAR.md §5 '
    'and DSAT_Verbal_Master_Taxonomy_v2.md §7.10. Used by generation system to set realistic '
    'distribution targets per module.';

-- Seed from GROUND_TRUTH §5 and Taxonomy §7.10
INSERT INTO grammar_focus_frequency
    (grammar_focus_key, avg_questions_per_module, frequency_label, is_dsat_confirmed, notes)
VALUES
    ('punctuation_comma',           2.50, 'very_high', true,  '2-3 per module per taxonomy §7.10'),
    ('subject_verb_agreement',      2.00, 'very_high', true,  '2-3 per module per taxonomy §7.10'),
    ('pronoun_antecedent_agreement',1.50, 'high',      true,  NULL),
    ('verb_tense_consistency',      1.50, 'high',      true,  NULL),
    ('parallel_structure',          1.25, 'high',      true,  NULL),
    ('comma_splice',                1.00, 'high',      true,  NULL),
    ('semicolon_use',               1.00, 'high',      true,  NULL),
    ('modifier_placement',          0.75, 'medium',    true,  NULL),
    ('apostrophe_use',              0.75, 'medium',    true,  NULL),
    ('sentence_fragment',           0.50, 'medium',    true,  NULL),
    ('pronoun_case',                0.50, 'medium',    true,  NULL),
    ('verb_form',                   0.50, 'medium',    true,  NULL),
    ('logical_predication',         0.50, 'medium',    true,  NULL),
    ('conjunction_usage',           0.25, 'low',       true,  NULL),
    ('run_on_sentence',             0.25, 'low',       true,  'Added taxonomy v2.6'),
    ('colon_dash_use',              0.25, 'low',       true,  'Added taxonomy v2.5'),
    ('voice_active_passive',        0.25, 'low',       false, 'Estimate — confirm with CB data'),
    ('comparative_structures',      0.10, 'very_low',  false, 'Estimate'),
    ('relative_pronouns',           0.10, 'very_low',  false, 'Estimate'),
    ('hyphen_usage',                0.10, 'very_low',  false, 'Estimate'),
    ('possessive_contraction',      0.10, 'very_low',  false, 'Estimate'),
    ('appositive_punctuation',      0.10, 'very_low',  false, 'Added GROUND_TRUTH §3.4'),
    ('quotation_punctuation',       0.10, 'very_low',  false, 'Added GROUND_TRUTH §3.4'),
    ('sentence_boundary',           0.10, 'very_low',  false, 'Catch-all — specific keys preferred'),
    ('elliptical_constructions',    0.05, 'very_low',  false, 'Estimate'),
    ('noun_countability',           0.05, 'very_low',  false, 'Estimate'),
    ('affirmative_agreement',       0.00, 'not_tested', false,'ACT-adjacent; 0/module per GROUND_TRUTH §5'),
    ('negation',                    0.00, 'not_tested', false,'ACT-adjacent; 0/module per GROUND_TRUTH §5'),
    ('preposition_idiom',           0.05, 'very_low',  false, 'Added GROUND_TRUTH §5.12 v1.2');
```

**App-layer changes:**
- `pipeline/generation/`: Read `grammar_focus_frequency` when sampling SEC question types for a generation batch; weight selection by `avg_questions_per_module`
- Generation API: Expose `GET /ontology/grammar-focus-frequency` for admin inspection

---

### Migration 055 — Add `target_grammar_role_key` to Generation Profiles

**Problem:** `question_generation_profiles` has `target_grammar_focus_key` but lacks `target_grammar_role_key`. When generating a SEC question, the generator must know the role family. Currently it must re-derive this by joining to `lookup_grammar_focus.grammar_role_key` (added in migration 048), which is indirect and error-prone.

**Solution:** Add the FK column directly.

```sql
ALTER TABLE question_generation_profiles
    ADD COLUMN IF NOT EXISTS target_grammar_role_key text
        REFERENCES lookup_grammar_role(key);

COMMENT ON COLUMN question_generation_profiles.target_grammar_role_key IS
    'For SEC generation targets: the grammar role family. '
    'Should mirror question_classifications.grammar_role_key. '
    'Can be derived from target_grammar_focus_key via lookup_grammar_focus.grammar_role_key.';
```

**App-layer changes:**
- `pipeline/upsert.py`: When writing `question_generation_profiles`, derive and write `target_grammar_role_key` from `target_grammar_focus_key` via lookup join
- Pass 2 prompt: Add `target_grammar_role_key` to `GenerationProfileAnnotation` fields

---

### Migration 056 — Cross-Dimension Semantic Validation

**Problem:** The schema allows contradictory classification bundles that would be impossible on the real SAT — for example, a literary fiction passage with purely academic lexical tier and assertive epistemic stance, which does not match any real CB question fingerprint. These bundles corrupt the corpus fingerprint and generate unrealistic questions.

**Solution:** Create a `lookup_dimension_compatibility` table recording which dimension value combinations are invalid, enforced by a trigger on `question_classifications`.

```sql
CREATE TABLE lookup_dimension_compatibility (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_a     text NOT NULL,  -- column name in question_classifications
    value_a         text NOT NULL,  -- value that triggers the constraint
    dimension_b     text NOT NULL,  -- column name to check
    incompatible_value_b text NOT NULL,  -- value that is incompatible with value_a
    reason          text,
    severity        text NOT NULL DEFAULT 'warning' CHECK (severity IN ('warning','error'))
);

COMMENT ON TABLE lookup_dimension_compatibility IS
    'Records dimension value pairs that are semantically incompatible on real DSAT questions. '
    'Enforced by trg_check_dimension_compatibility. severity=error blocks the write; '
    'severity=warning is logged to ontology_proposals for human review.';

-- Seed known incompatibilities
INSERT INTO lookup_dimension_compatibility
    (dimension_a, value_a, dimension_b, incompatible_value_b, reason, severity)
VALUES
    ('passage_source_type_key', 'literary_fiction', 'lexical_tier_key', 'technical', 
     'Literary fiction does not use technical register vocabulary', 'error'),
    ('domain_key', 'standard_english_conventions', 'passage_source_type_key', 'literary_fiction',
     'SEC questions use sentences only, not full literary passages', 'warning'),
    ('stimulus_mode_key', 'sentence_only', 'evidence_scope_key', 'multi_passage',
     'Sentence-only questions cannot have multi-passage evidence scope', 'error'),
    ('question_family_key', 'paired_passages', 'stimulus_mode_key', 'sentence_only',
     'Paired passage questions require a passage', 'error');

CREATE OR REPLACE FUNCTION fn_check_dimension_compatibility()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    rec lookup_dimension_compatibility%ROWTYPE;
    val_a text;
    val_b text;
BEGIN
    FOR rec IN SELECT * FROM lookup_dimension_compatibility WHERE severity = 'error' LOOP
        EXECUTE format('SELECT ($1).%I::text', rec.dimension_a) INTO val_a USING NEW;
        EXECUTE format('SELECT ($1).%I::text', rec.dimension_b) INTO val_b USING NEW;
        IF val_a = rec.value_a AND val_b = rec.incompatible_value_b THEN
            RAISE EXCEPTION 'Incompatible classification dimensions: %.% = % conflicts with %.% = %. Reason: %',
                TG_TABLE_NAME, rec.dimension_a, val_a,
                TG_TABLE_NAME, rec.dimension_b, val_b, rec.reason;
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_check_dimension_compatibility
    BEFORE INSERT OR UPDATE ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_check_dimension_compatibility();
```

---

### Migration 057 — Per-Slot Distractor Profiles

**Problem:** The corpus fingerprint tracks distractor type distribution in aggregate. The generation system cannot specify which distractor archetype to place in which answer slot. Real SAT questions have a structural distractor distribution (e.g., one plausible-but-wrong paraphrase, one out-of-scope trap, one grammar-correct but semantically wrong option). Without per-slot specs, generated questions have random distractor structures.

**Solution:** Create `distractor_slot_profiles` linking generation profiles to per-slot distractor specifications.

```sql
CREATE TABLE distractor_slot_profiles (
    id                         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id                uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    slot_label                 char(1) NOT NULL CHECK (slot_label IN ('A','B','C','D')),
    target_distractor_type_key text REFERENCES lookup_distractor_type(key),
    target_distractor_subtype_key text REFERENCES lookup_distractor_subtype(key),
    target_eliminability_key   text REFERENCES lookup_eliminability(key),
    construction_note          text,  -- free-text guidance for generation
    created_at                 timestamptz NOT NULL DEFAULT now(),

    UNIQUE (question_id, slot_label)
);

COMMENT ON TABLE distractor_slot_profiles IS
    'Per-slot distractor specification for generation. Each row constrains one answer slot '
    '(A–D) for a source question used as a generation template. '
    'Enables realistic distractor distribution matching corpus fingerprint targets.';

CREATE INDEX idx_distractor_slot_profiles_question_id ON distractor_slot_profiles(question_id);
```

**Pass 2 prompt changes (generation path only):**
- Add `distractor_slot_profiles` array to `GenerationProfileAnnotation` for template questions
- Each item: `{ slot_label, target_distractor_type_key, target_distractor_subtype_key, target_eliminability_key, construction_note }`

---

### Migration 058 — IRT B Quantitative Adjustment

**Problem:** `fn_compute_irt_b_v1()` uses 6 text-based classification dimensions (inference_distance, evidence_distribution, syntactic_complexity, lexical_tier, syntactic_trap, noun_phrase_complexity) to estimate difficulty. Questions with charts, tables, or quantitative data have additional reading difficulty from interpreting the visual/quantitative content that the formula does not capture. This causes systematic underprediction of difficulty for data-interpretation questions.

**Solution:** Add `irt_b_quantitative_adjustment numeric(3,2)` to `question_classifications` — an additive offset applied after the formula.

```sql
ALTER TABLE question_classifications
    ADD COLUMN IF NOT EXISTS irt_b_quantitative_adjustment numeric(3,2)
        NOT NULL DEFAULT 0.00
        CHECK (irt_b_quantitative_adjustment BETWEEN -1.00 AND 1.00);

COMMENT ON COLUMN question_classifications.irt_b_quantitative_adjustment IS
    'Additive offset applied to fn_compute_irt_b_v1() result for questions with quantitative content '
    '(charts, tables, graphs). Range: -1.00 to +1.00. Default 0.00 (no adjustment). '
    'Set by human reviewer or future fn_compute_quantitative_adjustment() function.';
```

**`fn_compute_irt_b_v1()` update:**

```sql
-- Update the IRT function to add the adjustment after computing the base score
-- (Modify the existing function body — not reproduced in full here)
-- Final line changes from:
--   RETURN ROUND(b_estimate::numeric, 2);
-- To:
--   RETURN ROUND((b_estimate + qc.irt_b_quantitative_adjustment)::numeric, 2);
-- where qc is the question_classifications row joined via question_id
```

---

### Migration 059 — Generation Profile Mirror Status

**Problem:** `question_generation_profiles.target_*` columns are supposed to mirror `question_classifications.*` fields. But there is no record of whether they were:
- Auto-populated by the pipeline (reliable, consistent)
- Manually set by a human (intentional override)
- Written by LLM with inconsistent values (dangerous — drift from classification)

Without this, the corpus conformance gate cannot distinguish intentional overrides from pipeline errors.

**Solution:** Add `target_mirror_status` enum column and an updated_by_pipeline boolean.

```sql
ALTER TABLE question_generation_profiles
    ADD COLUMN IF NOT EXISTS target_mirror_status text
        NOT NULL DEFAULT 'manual'
        CHECK (target_mirror_status IN ('auto_mirrored','manual','drift'));

ALTER TABLE question_generation_profiles
    ADD COLUMN IF NOT EXISTS mirror_computed_at timestamptz;

COMMENT ON COLUMN question_generation_profiles.target_mirror_status IS
    'auto_mirrored: target_* fields were populated by pipeline from question_classifications. '
    'manual: fields were set by human reviewer. '
    'drift: LLM wrote values inconsistent with classification (detected by drift.py). '
    'Default manual to be conservative for pre-migration data.';
```

**App-layer changes:**
- `pipeline/upsert.py`: Set `target_mirror_status = 'auto_mirrored'` and `mirror_computed_at = now()` when auto-populating from classification
- `pipeline/generation/drift.py`: On drift detection, update `target_mirror_status = 'drift'`
- Generation gate: Skip fingerprint conformance retry for `manual` status (human override is intentional)

---

### Migration 060 — Paired Passage Sets

**Problem:** Questions referencing paired passages (Passage 1 + Passage 2) must be treated as a unit for generation and retirement. The current schema has no mechanism to:
- Link the two passages as a set
- Prevent retiring one paired question without the other
- Generate paired questions from a shared passage set

**Solution:** Create `paired_passage_sets` and add `paired_passage_set_id` FK to `questions`.

```sql
CREATE TABLE paired_passage_sets (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_a_text       text NOT NULL,
    passage_b_text       text NOT NULL,
    relationship_key     text REFERENCES lookup_rhetorical_structure(key),
    passage_a_source     text,  -- bibliographic note
    passage_b_source     text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS paired_passage_set_id uuid
        REFERENCES paired_passage_sets(id) ON DELETE RESTRICT;

CREATE INDEX idx_questions_paired_passage_set ON questions(paired_passage_set_id)
    WHERE paired_passage_set_id IS NOT NULL;

-- Prevent retiring one question in a pair without the other
CREATE OR REPLACE FUNCTION fn_check_paired_retirement()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    sibling_count int;
    active_sibling_count int;
BEGIN
    IF NEW.retirement_status = 'retired' AND OLD.retirement_status != 'retired'
       AND NEW.paired_passage_set_id IS NOT NULL
    THEN
        SELECT COUNT(*), COUNT(*) FILTER (WHERE retirement_status != 'retired')
        INTO sibling_count, active_sibling_count
        FROM questions
        WHERE paired_passage_set_id = NEW.paired_passage_set_id
          AND id != NEW.id;

        IF sibling_count > 0 AND active_sibling_count > 0 THEN
            RAISE EXCEPTION
                'Cannot retire question % without retiring all sibling questions in paired_passage_set %',
                NEW.id, NEW.paired_passage_set_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_check_paired_retirement
    BEFORE UPDATE OF retirement_status ON questions
    FOR EACH ROW EXECUTE FUNCTION fn_check_paired_retirement();
```

**App-layer changes:**
- `models/extract.py`: Add optional `paired_passage_set_id` field to `QuestionExtract`
- `pipeline/upsert.py`: Upsert `paired_passage_sets` if `paired_passage_a_text` and `paired_passage_b_text` present in Pass 1 output
- Generation API: Add `GET /questions/paired-sets` endpoint for browsing paired sets

---

## Migration Dependency Order

```
043 question_images               (standalone, no deps on new tables)
044 word_count_columns            (standalone)
045 topic_fine_normalization      (requires lookup_domain exists — ✓ migration 025)
046 no_change_multi_error         (requires lookup_grammar_focus — ✓ migration 019)
047 sec_grammar_trigger           (requires lookup_grammar_focus — ✓; run after 046)
048 grammar_focus_missing_keys    (requires lookup_grammar_focus, lookup_grammar_role — ✓)
    ↳ must run BEFORE 054 (grammar_focus_frequency seeds these keys)
049 coaching_option_linkage       (requires question_coaching_annotations — ✓ migration 029)
050 solver_steps_table            (requires lookup_reasoning_step_type — ✓ migration 006)
051 deprecate_explanation_columns (standalone; run after 050)
052 distractor_contrast           (requires question_options — ✓ migration 006)
053 evidence_span_offsets         (requires question_reasoning — ✓ migration 006)
054 grammar_focus_frequency       (REQUIRES 048 — new keys must exist first)
055 target_grammar_role_key       (REQUIRES 048 — grammar_role_key denorm must exist)
056 dimension_compatibility       (requires question_classifications — ✓)
057 distractor_slot_profiles      (requires lookup_distractor_type, lookup_distractor_subtype,
                                   lookup_eliminability — ✓ migrations 006, 025)
058 irt_quantitative_adjustment   (requires question_classifications — ✓)
059 generation_mirror_status      (requires question_generation_profiles — ✓ migration 021)
060 paired_passage_sets           (requires lookup_rhetorical_structure — ✓ migration 006)
```

**Recommended batching for deployment:**

| Batch | Migrations | Rationale |
|-------|-----------|-----------|
| Batch 1 | 043, 044, 045 | Non-breaking additions; can run in parallel |
| Batch 2 | 046, 047 | SEC markers; 047 enforces 046's new columns |
| Batch 3 | 048 | Grammar focus key additions (prerequisite for Batches 4-5) |
| Batch 4 | 049, 050, 051, 052, 053 | Explanation depth; no inter-dependencies |
| Batch 5 | 054, 055 | Requires Batch 3 complete |
| Batch 6 | 056, 057, 058, 059, 060 | Generation quality; no inter-dependencies |

---

## App-Layer Change Summary

### `prompts/pass2_annotation.py`
| Migration | Change |
|-----------|--------|
| 046 | Add `no_change_is_correct`, `multi_error_flag`, `primary_error_field` fields |
| 048 | Regenerate grammar_focus_key enum list from DB (new keys auto-included via ontology_ref.py) |
| 049 | Add `option_label` to coaching_annotations items; add rule for distractor_lure spans |
| 050 | Add `solver_steps` array field with step schema |
| 052 | Add `distractor_contrast_note` to OptionAnnotation |
| 053 | Add `evidence_span_start_char`, `evidence_span_end_char` to ReasoningAnnotation |
| 055 | Add `target_grammar_role_key` to GenerationProfileAnnotation |
| 057 | Add `distractor_slot_profiles` array to GenerationProfileAnnotation |

### `models/annotation.py`
| Migration | Change |
|-----------|--------|
| 046 | Add `no_change_is_correct: bool`, `multi_error_flag: bool`, `primary_error_field: Optional[str]` to `ClassificationAnnotation` |
| 049 | Add `option_label: Optional[Literal['A','B','C','D']]` to coaching annotation item model |
| 050 | Create `SolverStep` model; add `solver_steps: list[SolverStep]` to `ReasoningAnnotation` |
| 052 | Add `distractor_contrast_note: Optional[str]` to `OptionAnnotation` |
| 053 | Add `evidence_span_start_char: Optional[int]`, `evidence_span_end_char: Optional[int]` to `ReasoningAnnotation` |
| 055 | Add `target_grammar_role_key: Optional[str]` to `GenerationProfileAnnotation` |

### `pipeline/validator.py`
| Migration | Change |
|-----------|--------|
| 045 | Add `topic_fine_key` to FK validation list |
| 046 | Add validation: if `multi_error_flag` is True, `primary_error_field` must be non-null |
| 047 | Validation already present — trigger provides defense-in-depth |
| 050 | Add validation: `step_type` in each `SolverStep` must be a valid `lookup_reasoning_step_type` key |

### `pipeline/upsert.py`
| Migration | Change |
|-----------|--------|
| 043 | Upsert `question_images` from Pass 1 image data |
| 045 | Write `topic_fine_key` instead of `topic_fine` |
| 050 | Insert `solver_steps` rows |
| 051 | Set `canonical_explanation_source = 'coaching_layer'` |
| 055 | Derive and write `target_grammar_role_key` |
| 059 | Set `target_mirror_status = 'auto_mirrored'` |
| 060 | Upsert `paired_passage_sets` when paired passages present |

---

## Success Criteria

### Goal 1 — Reading & Analyzing (A)
- [ ] All 5 missing grammar_focus_key values inserted and validated in ontology
- [ ] `no_change_is_correct` flag set correctly on ≥95% of ingested SEC questions where correct answer is "NO CHANGE"
- [ ] `passage_word_count` populated on all non-SEC questions
- [ ] Zero ingestion failures due to invalid grammar_focus_key after migration 048
- [ ] SEC trigger blocks insertion of grammar_role_key=NULL for domain=SEC

### Goal 2 — Explaining Correctness (B+)
- [ ] `solver_steps` table populated for ≥80% of newly ingested questions
- [ ] `distractor_lure` coaching annotations carry `option_label` for ≥90% of cases
- [ ] `canonical_explanation_source` is `coaching_layer` for all post-migration 051 questions
- [ ] `evidence_span_start_char` / `evidence_span_end_char` populated for ≥70% of passage-based questions

### Goal 3 — Generating Realistic Questions (B+)
- [ ] `grammar_focus_frequency` seeded with empirical data for all 27+ grammar_focus_key values
- [ ] Generation batch for SEC questions weighted by `avg_questions_per_module`
- [ ] `target_mirror_status` tracks `auto_mirrored` for pipeline-generated profiles
- [ ] `distractor_slot_profiles` populated for all template questions (those used in active `generation_templates`)
- [ ] Paired passage questions cannot be retired individually (trigger enforced)

---

## Open Questions

1. **`preposition_idiom` grammar_role_key assignment**: The taxonomy v2.6 mapping table does not include `preposition_idiom`. This PRD assigns it to `verb_form` as the closest available role. A taxonomy v2.7 update should formally define this mapping before migration 048 is deployed.

2. **`grammar_focus_frequency` data source**: The seeded values in migration 054 are derived from GROUND_TRUTH §5 and Taxonomy §7.10 but many are marked `is_dsat_confirmed = false`. A systematic review of official CB practice test answer keys is needed to confirm the low-frequency key counts before using them for generation weighting.

3. **`lookup_dimension_compatibility` completeness**: Migration 056 seeds only the most obvious incompatibilities. A full audit of the corpus fingerprint view data would reveal which actual bundles never appear in official CB questions — those are candidates for additional incompatibility rules.

4. **`topic_fine` backfill script**: Migration 045 adds the FK column but defers the `DROP COLUMN` of the old free-text columns. A backfill script mapping existing free-text values to `lookup_passage_topic_fine.key` must be written and reviewed before the old columns can be dropped. Risk: some existing topic_fine values may not map cleanly — those need human triage.

5. **Grammar_focus total count discrepancy**: After migration 042, the DB has 27 keys. DSAT_Verbal_Master_Taxonomy_v2.6 describes 26 total keys. Adding the 5 from migration 048 brings the DB to 32. Taxonomy v2.7 should be updated to match when it is next revised.
