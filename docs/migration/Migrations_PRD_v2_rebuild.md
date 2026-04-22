# Migrations PRD v2 — Full Rebuild Plan

**Document Version:** 2.0  
**Date:** 2026-04-19  
**Status:** Draft — Engineering Review Required  
**Supersedes:** `docs/Migrations_PRD.md` v1.0 (append-only patches on 001–042)  
**References:**  
- `docs/GRAMMAR_GUIDE/GROUND_TRUTH_GRAMMAR.md` v1.2  
- `taxonomy/DSAT_Verbal_Master_Taxonomy_v2.md` v2.6  
- `backend/migrations/001–042` (historical reference)  
- `docs/db_schema_diagram.md` (current final state)

---

## Why a Rebuild?

Migrations 001–042 grew organically over time — tables were created, then had columns added, renamed, or dropped as understanding deepened. The result is a schema that is functionally correct but carries the weight of its evolution:

- `primary_solver_steps_jsonb` was created, then dropped in migration 034 and never structurally replaced
- Grammar focus taxonomy arrived in migration 019 but was missing 5 keys even after migration 042
- `topic_broad` / `topic_fine` were never normalized despite being free-text from day 1
- `lookup_grammar_focus` has no `grammar_role_key` denorm, no `disambiguation_priority`, no frequency data — all query-critical metadata living only in documentation
- Coaching annotations (migration 034) have no `option_label` — critical for distractor explanation
- Generation profiles lack `target_grammar_role_key` and `target_mirror_status` — both obvious in hindsight
- SEC grammar enforcement exists only in app code; no DB-level trigger

This document specifies a **clean rebuild from migration 001** that bakes every lesson learned into the right place from day 1. The 42 historical migrations are kept as reference — the rebuild does not require deleting or modifying them. It is a parallel fresh schema plan for greenfield deployments or future schema resets.

---

## Design Goals

| Goal | Current Grade (001–042) | Target (Rebuild) |
|------|:---:|:---:|
| 1. Reading & analyzing actual test questions | B+ | A |
| 2. Explaining why an answer is correct | C+ | B+ |
| 3. Generating questions as realistic as the real test | B- | B+ |

---

## Migration Phase Overview

```
Phase 0 — Platform Foundation        M-001 to M-004
Phase 1 — Core Question Schema       M-005 to M-009
Phase 2 — Content & Media            M-010 to M-011
Phase 3 — Ingestion Pipeline         M-012 to M-013
Phase 4 — Generation System          M-014 to M-016
Phase 5 — Intelligence & Coaching    M-017 to M-019
Phase 6 — Integrity & Enforcement    M-020 to M-022
Phase 7 — Reporting & Observability  M-023 to M-025
Phase 8 — Seed Data                  M-026 to M-028
```

**Total: 28 migrations** vs. 42+ in the organic evolution.
**Seed coverage:** All 44 lookup tables seeded across M-004, M-022–M-028 —
zero FK-orphan risk on first ingest.  
**Key improvements baked in from day 1, not patched:**  
- Complete `lookup_grammar_focus` (39 keys with role mapping, disambiguation priority, frequency band)  
- `solver_steps` table — never dropped  
- `option_label` on coaching annotations — from creation  
- `target_grammar_role_key` on generation profiles — from creation  
- `target_mirror_status` — from creation  
- `passage_word_count` / `stem_word_count` — computed columns from day 1  
- `no_change_is_correct` / `multi_error_flag` — on classifications from day 1  
- SEC enforcement trigger — installed at schema creation  
- `paired_passage_sets` — exists before `questions` references it  
- Cross-dimension compatibility — enforced at schema creation

---

## Phase 0 — Platform Foundation

### M-001 — Extensions & Utility Functions

**Goals served:** All three (infrastructure prerequisite)  
**Improvement over 001–042:** Functions and extensions combined in one atomic migration; `set_word_counts()` trigger function defined here so it's available when `questions` is created in M-005.

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Auto-timestamp trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

-- Content hash trigger: SHA-256 of passage+prompt+paired_passage
CREATE OR REPLACE FUNCTION fn_set_content_hash()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.content_hash := encode(
        digest(
            coalesce(NEW.passage_text,'') || '|' ||
            coalesce(NEW.prompt_text,'') || '|' ||
            coalesce(NEW.paired_passage_text,''),
            'sha256'
        ), 'hex'
    );
    RETURN NEW;
END;
$$;

-- Word count trigger (passage + stem)
CREATE OR REPLACE FUNCTION fn_set_word_counts()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.passage_text IS NOT NULL THEN
        NEW.passage_word_count := array_length(
            regexp_split_to_array(trim(NEW.passage_text), '\s+'), 1
        );
    END IF;
    NEW.stem_word_count := array_length(
        regexp_split_to_array(trim(NEW.prompt_text), '\s+'), 1
    );
    RETURN NEW;
END;
$$;

-- Retirement consistency guard
CREATE OR REPLACE FUNCTION fn_check_active_retirement_consistency()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.is_active = true AND NEW.retirement_status = 'retired' THEN
        RAISE EXCEPTION 'A retired question cannot be is_active=true';
    END IF;
    RETURN NEW;
END;
$$;

-- Paired passage retirement guard
-- (blocks retiring one question in a paired set without retiring siblings)
-- NOTE: This function body references the `questions` table, which does not exist
-- until M-005. PostgreSQL compiles PL/pgSQL function bodies lazily — at first
-- invocation, not at CREATE FUNCTION time — so this forward reference is valid and
-- will not error during M-001 execution. The trigger that calls this function is
-- created in M-005 after `questions` exists.
CREATE OR REPLACE FUNCTION fn_check_paired_retirement()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE active_siblings int;
BEGIN
    IF NEW.retirement_status = 'retired'
       AND OLD.retirement_status != 'retired'
       AND NEW.paired_passage_set_id IS NOT NULL
    THEN
        SELECT COUNT(*) INTO active_siblings
        FROM questions
        WHERE paired_passage_set_id = NEW.paired_passage_set_id
          AND id != NEW.id
          AND retirement_status != 'retired';
        IF active_siblings > 0 THEN
            RAISE EXCEPTION
                'Cannot retire question % without retiring all siblings in paired_passage_set %',
                NEW.id, NEW.paired_passage_set_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

-- ── MIGRATION TRACKING & CONCURRENT SAFETY (gap C4) ──────────────────────
-- Every migration MUST INSERT a row into schema_migrations on successful completion.
-- fn_acquire_migration_lock() MUST be called before each migration to prevent
-- concurrent execution from two terminals or CI pipelines.
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id    text PRIMARY KEY,          -- e.g. 'M-001', 'M-002', ...
    applied_at      timestamptz NOT NULL DEFAULT now(),
    applied_by      text,                      -- user/CI identity
    execution_ms    int                         -- optional timing
);

CREATE OR REPLACE FUNCTION fn_acquire_migration_lock(p_migration_id text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    locked boolean;
BEGIN
    -- Try advisory lock (hash of migration ID for int4 range)
    SELECT pg_try_advisory_lock(
        hashtext(p_migration_id)
    ) INTO locked;
    IF NOT locked THEN
        RAISE EXCEPTION 'Migration % is already running on another connection', p_migration_id;
    END IF;
    -- Check if already applied
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE migration_id = p_migration_id) THEN
        RAISE NOTICE 'Migration % already applied at % — skipping', p_migration_id,
            (SELECT applied_at FROM schema_migrations WHERE migration_id = p_migration_id);
        PERFORM pg_advisory_unlock(hashtext(p_migration_id));
        RETURN;
    END IF;
END;
$$;
```

---

### M-002 — Exam Hierarchy

**Goals served:** Goal 1 (question source provenance)  
**Improvement over 001–042:** `exam_module_form_targets` included from creation (no `target_composition_jsonb` to later deprecate); `difficulty_band` constraint correct from day 1.

```sql
CREATE TABLE exams (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_code   text NOT NULL UNIQUE,
    title       text NOT NULL,
    vendor      text,
    exam_type   text NOT NULL DEFAULT 'DSAT_RW',
    is_official boolean NOT NULL DEFAULT false,
    notes       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT exams_exam_code_nonempty CHECK (length(trim(exam_code)) > 0),
    CONSTRAINT exams_title_nonempty CHECK (length(trim(title)) > 0)
);

CREATE TABLE exam_sections (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id      uuid NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    section_code text NOT NULL,
    title        text NOT NULL,
    sort_order   int  NOT NULL CHECK (sort_order > 0),
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (exam_id, section_code)
);

CREATE TABLE exam_modules (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id      uuid NOT NULL REFERENCES exam_sections(id) ON DELETE CASCADE,
    module_code     text NOT NULL,
    title           text NOT NULL,
    sort_order      int  NOT NULL CHECK (sort_order > 0),
    difficulty_band text CHECK (difficulty_band IN ('easy','medium','hard','adaptive')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (section_id, module_code),
    UNIQUE (section_id, sort_order)
);

-- Structured module form targets (replaces target_composition_jsonb)
CREATE TABLE exam_module_form_targets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id       uuid NOT NULL REFERENCES exam_modules(id) ON DELETE CASCADE,
    constraint_type text NOT NULL CHECK (constraint_type IN ('domain','difficulty','passage_type','question_family')),
    dimension_key   text NOT NULL,
    min_count       smallint,
    max_count       smallint,
    target_pct      numeric(5,4),
    UNIQUE (module_id, constraint_type, dimension_key)
);

CREATE INDEX idx_exam_sections_exam ON exam_sections(exam_id);
CREATE INDEX idx_exam_modules_section ON exam_modules(section_id);
CREATE INDEX idx_exam_module_targets_module ON exam_module_form_targets(module_id);

CREATE TRIGGER trg_exams_updated_at BEFORE UPDATE ON exams
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_exam_sections_updated_at BEFORE UPDATE ON exam_sections
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_exam_modules_updated_at BEFORE UPDATE ON exam_modules
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

### M-003 — Complete Lookup Tables (All Controlled Vocabulary)

**Goals served:** All three  
**Improvement over 001–042:** All lookup tables created in one migration with consistent structure. Critically:
- `lookup_grammar_focus` includes `grammar_role_key` FK + `disambiguation_priority` + `frequency_label` from creation — never needs patching
- `lookup_grammar_focus` ships with all 39 keys (not 27 added piecemeal across migrations 019, 041, 042)
- `lookup_passage_topic_fine` normalizes what was free-text `topic_fine` in original schema
- `lookup_grammar_focus_frequency` exists as a view-ready companion

**Standard lookup structure** (all tables below use this pattern):
```sql
-- Pattern for every lookup table:
-- key text PK, display_name text NOT NULL, description text,
-- is_active boolean DEFAULT true, sort_order int, created_at, updated_at
```

> **IMPORTANT — LIKE and triggers:** `CREATE TABLE ... (LIKE other INCLUDING ALL)` copies
> column definitions, constraints, indexes, and defaults but does **NOT** copy triggers
> (triggers are instance-level objects, not part of the table definition). Every lookup
> table created with LIKE therefore needs its own `set_updated_at` trigger registered
> explicitly. The block at the end of this migration registers all of them.

```sql
-- ── QUESTION FAMILY & STIMULUS ──────────────────────────────────────────
CREATE TABLE lookup_question_family (
    key text PRIMARY KEY, display_name text NOT NULL, description text,
    is_active boolean NOT NULL DEFAULT true, sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE lookup_stimulus_mode (
    key text PRIMARY KEY, display_name text NOT NULL, description text,
    is_active boolean NOT NULL DEFAULT true, sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE lookup_stem_type (
    key text PRIMARY KEY, display_name text NOT NULL, description text,
    is_active boolean NOT NULL DEFAULT true, sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── EVIDENCE & REASONING ────────────────────────────────────────────────
CREATE TABLE lookup_evidence_scope (
    key text PRIMARY KEY, display_name text NOT NULL, description text,
    is_active boolean NOT NULL DEFAULT true, sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE lookup_evidence_location (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_evidence_mode (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_evidence_distribution (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_answer_mechanism (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_solver_pattern (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_hidden_clue_type (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_clue_distribution (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_reasoning_step_type (LIKE lookup_evidence_scope INCLUDING ALL);

-- ── DISTRACTOR TAXONOMY ──────────────────────────────────────────────────
CREATE TABLE lookup_distractor_type (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_distractor_subtype (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_distractor_construction (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_semantic_relation (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_plausibility_source (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_eliminability (LIKE lookup_evidence_scope INCLUDING ALL);

-- ── GENERATION ───────────────────────────────────────────────────────────
CREATE TABLE lookup_generation_pattern_family (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_coaching_annotation_type (LIKE lookup_evidence_scope INCLUDING ALL);

-- ── PROSE STYLE ──────────────────────────────────────────────────────────
CREATE TABLE lookup_syntactic_complexity (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_syntactic_interruption (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_syntactic_trap (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_lexical_tier (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_rhetorical_structure (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_noun_phrase_complexity (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_vocabulary_profile (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_cohesion_device (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_epistemic_stance (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_inference_distance (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_transitional_logic (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_prose_register (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_prose_tone (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_passage_source_type (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_craft_signal (LIKE lookup_evidence_scope INCLUDING ALL);

-- ── DOMAIN & SKILL HIERARCHY ─────────────────────────────────────────────
CREATE TABLE lookup_domain (LIKE lookup_evidence_scope INCLUDING ALL);

CREATE TABLE lookup_skill_family (
    key        text PRIMARY KEY,
    display_name text NOT NULL,
    description  text,
    domain_key text NOT NULL REFERENCES lookup_domain(key),  -- hierarchy enforced here
    is_active  boolean NOT NULL DEFAULT true,
    sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── PASSAGE TAXONOMY ─────────────────────────────────────────────────────
CREATE TABLE lookup_passage_type (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_reading_scope (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_reasoning_demand (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_passage_topic_domain (LIKE lookup_evidence_scope INCLUDING ALL);
CREATE TABLE lookup_argument_role (LIKE lookup_evidence_scope INCLUDING ALL);

-- Normalized topic (replaces free-text topic_fine from original schema)
CREATE TABLE lookup_passage_topic_fine (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    description  text,
    domain_key   text NOT NULL REFERENCES lookup_domain(key),
    is_active    boolean NOT NULL DEFAULT true,
    sort_order   int,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

-- ── GRAMMAR — COMPLETE FROM DAY 1 ────────────────────────────────────────
-- Improvement: role lookup exists before focus lookup; focus has role FK + priority

CREATE TABLE lookup_grammar_role (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    description  text,
    is_active    boolean NOT NULL DEFAULT true,
    sort_order   int,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE lookup_grammar_focus (
    key                    text PRIMARY KEY,
    display_name           text NOT NULL,
    description            text,
    grammar_role_key       text NOT NULL REFERENCES lookup_grammar_role(key),
    -- Disambiguation priority per GROUND_TRUTH Part 4 — lower = higher precedence
    disambiguation_priority smallint NOT NULL DEFAULT 99,
    -- Empirical frequency band per GROUND_TRUTH Part 5
    frequency_label        text NOT NULL DEFAULT 'medium'
        CHECK (frequency_label IN ('very_high','high','medium_high','medium','low_medium','low','very_low','not_tested')),
    avg_questions_per_module numeric(4,2),
    is_dsat_confirmed      boolean NOT NULL DEFAULT false,
    is_active              boolean NOT NULL DEFAULT true,
    sort_order             int,
    created_at             timestamptz NOT NULL DEFAULT now(),
    updated_at             timestamptz NOT NULL DEFAULT now()
);

-- Cross-dimension compatibility for validation trigger (M-020)
CREATE TABLE lookup_dimension_compatibility (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_a          text NOT NULL,
    value_a              text NOT NULL,
    dimension_b          text NOT NULL,
    incompatible_value_b text NOT NULL,
    reason               text,
    severity             text NOT NULL DEFAULT 'error' CHECK (severity IN ('error','warning'))
);

-- ── PASSAGE TENSE REGISTER (GROUND_TRUTH §8.4) ────────────────────────────
-- Maps passage_type → expected tense register for realistic question generation
CREATE TABLE lookup_passage_tense_register (
    key text PRIMARY KEY, display_name text NOT NULL, description text,
    is_active boolean NOT NULL DEFAULT true, sort_order int,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── GRAMMAR FOCUS FREQUENCY EVIDENCE (provenance for frequency data) ────────
-- Tracks which practice tests confirmed each frequency data point (gap M8)
CREATE TABLE grammar_focus_frequency_evidence (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    grammar_focus_key     text NOT NULL REFERENCES lookup_grammar_focus(key),
    source_tests          text[] NOT NULL,
    notes                 text,
    last_updated_at       timestamptz NOT NULL DEFAULT now(),
    created_at            timestamptz NOT NULL DEFAULT now()
);

-- Register set_updated_at triggers for all lookup tables created with LIKE.
-- (LIKE copies columns/constraints/indexes but NOT triggers — each table needs its own.)
DO $$
DECLARE
    tbl text;
    lookup_tables text[] := ARRAY[
        'lookup_question_family','lookup_stimulus_mode','lookup_stem_type',
        'lookup_evidence_scope','lookup_evidence_location','lookup_evidence_mode',
        'lookup_evidence_distribution','lookup_answer_mechanism','lookup_solver_pattern',
        'lookup_hidden_clue_type','lookup_clue_distribution','lookup_reasoning_step_type',
        'lookup_distractor_type','lookup_distractor_subtype','lookup_distractor_construction',
        'lookup_semantic_relation','lookup_plausibility_source','lookup_eliminability',
        'lookup_generation_pattern_family','lookup_coaching_annotation_type',
        'lookup_syntactic_complexity','lookup_syntactic_interruption','lookup_syntactic_trap',
        'lookup_lexical_tier','lookup_rhetorical_structure','lookup_noun_phrase_complexity',
        'lookup_vocabulary_profile','lookup_cohesion_device','lookup_epistemic_stance',
        'lookup_inference_distance','lookup_transitional_logic','lookup_prose_register',
        'lookup_prose_tone','lookup_passage_source_type','lookup_craft_signal',
        'lookup_domain','lookup_passage_type','lookup_reading_scope',
        'lookup_reasoning_demand','lookup_passage_topic_domain','lookup_argument_role',
        'lookup_grammar_role','lookup_grammar_focus','lookup_passage_topic_fine',
        'lookup_passage_tense_register'
    ];
BEGIN
    FOREACH tbl IN ARRAY lookup_tables LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %s
             FOR EACH ROW EXECUTE FUNCTION set_updated_at()',
            replace(tbl, 'lookup_', ''), tbl
        );
    END LOOP;
END;
$$;
```

---

### M-004 — Seed Critical Lookup Tables (Grammar, Domain, Topic, Annotation)

**Goals served:** All three
**Improvement over 001–042:** Critical seeds in one migration. `lookup_grammar_focus` seeded with all 39 keys from GROUND_TRUTH v1.5 — no piecemeal additions required in later migrations. Remaining 37+ tables seeded in M-022 through M-028 (no NOT NULL FK dependencies on those).

```sql
-- ── lookup_grammar_role (8 roles) ────────────────────────────────────────
INSERT INTO lookup_grammar_role (key, display_name, description, sort_order) VALUES
('sentence_boundary', 'Sentence Boundary',   'Fragments, run-ons, comma splices, boundary punctuation', 10),
('agreement',         'Agreement',           'Subject-verb, pronoun-antecedent, case, number', 20),
('verb_form',         'Verb Form',           'Tense, mood, voice, finite/nonfinite, participles', 30),
('modifier',          'Modifier',            'Placement, dangling, comparative, logical predication', 40),
('punctuation',       'Punctuation',         'Comma, semicolon, colon, dash, apostrophe mechanics', 50),
('parallel_structure','Parallel Structure',  'Lists, correlative conjunctions, comparisons', 60),
('pronoun',           'Pronoun',             'Pronoun-specific errors: ambiguity, case, agreement', 70),
('expression_of_ideas','Expression of Ideas','Rhetorical effectiveness, concision, precision, register', 80)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_grammar_focus (39 keys) ───────────────────────────────────────
-- Source: GROUND_TRUTH Part 3 + Part 5 frequency data + Part 3.9 Expression of Ideas
-- Source: Taxonomy v2.6 §7.9 role mappings
-- All 39 keys present from day 1; no patch migrations needed
-- Count breakdown: 4 sentence_boundary + 5 agreement + 4 verb_form +
--   4 modifier + 9 punctuation + 4 parallel_structure + 2 pronoun + 7 expression_of_ideas = 39
-- (elliptical_constructions and preposition_idiom map to parallel_structure per GROUND_TRUTH §3.6/§3.8)

INSERT INTO lookup_grammar_focus
  (key, display_name, grammar_role_key, disambiguation_priority, frequency_label, avg_questions_per_module, is_dsat_confirmed, sort_order)
VALUES
  -- Sentence Boundary (priority 1 family per GROUND_TRUTH §4 priority 1)
  ('comma_splice',               'Comma Splice',                'sentence_boundary', 1,  'high',        1.75, true,  10),
  ('sentence_fragment',          'Sentence Fragment',           'sentence_boundary', 2,  'medium',      0.75, true,  20),
  ('run_on_sentence',            'Run-On Sentence',             'sentence_boundary', 3,  'low_medium',  0.25, true,  30),
  ('sentence_boundary',          'Sentence Boundary (General)', 'sentence_boundary', 99, 'high',        1.50, true,  40),

  -- Agreement
  ('subject_verb_agreement',     'Subject-Verb Agreement',      'agreement', 4,  'very_high',   2.50, true,  50),
  ('pronoun_antecedent_agreement','Pronoun-Antecedent Agreement','agreement', 6,  'medium',      1.00, true,  60),
  ('noun_countability',          'Noun Countability',           'agreement', 7,  'low_medium',  0.35, true,  70),
  ('affirmative_agreement',      'Affirmative Agreement',       'agreement', 99, 'not_tested',  0.00, false, 80),
  ('determiners_articles',       'Determiners & Articles',      'agreement', 99, 'low_medium',  0.35, true,  85),

  -- Verb Form (4 keys: verb_tense_consistency, verb_form, voice_active_passive, negation)
  ('verb_tense_consistency',     'Verb Tense Consistency',      'verb_form', 10, 'high',        1.50, true,  90),
  ('verb_form',                  'Verb Form (General)',          'verb_form', 11, 'medium',      1.00, true,  100),
  ('voice_active_passive',       'Active/Passive Voice',        'verb_form', 2,  'low',         0.25, true,  110),
  ('negation',                   'Negation',                    'verb_form', 8,  'not_tested',  0.00, false, 120),
  ('elliptical_constructions',   'Elliptical Constructions',    'parallel_structure', 99, 'low',         0.10, false, 130),

  -- Modifier
  ('modifier_placement',         'Modifier Placement',          'modifier', 99, 'medium',       1.00, true,  140),
  ('logical_predication',        'Logical Predication',         'modifier', 3,  'low',          0.25, true,  150),
  ('comparative_structures',     'Comparative Structures',      'modifier', 6,  'medium',       1.00, true,  160),
  ('relative_pronouns',          'Relative Pronouns',           'modifier', 9,  'high',         1.25, true,  170),

  -- Punctuation
  ('punctuation_comma',          'Comma Usage',                 'punctuation', 99, 'very_high',  2.50, true,  180),
  ('semicolon_use',              'Semicolon Use',               'punctuation', 99, 'high',       1.50, true,  190),
  ('conjunctive_adverb_usage',   'Conjunctive Adverb Usage',    'punctuation', 4,  'high',       1.25, true,  195),
  ('apostrophe_use',             'Apostrophe Use',              'punctuation', 99, 'high',       1.25, true,  200),
  ('colon_dash_use',             'Colon / Dash Use',            'punctuation', 99, 'medium_high',1.50, true,  210),
  ('appositive_punctuation',     'Appositive Punctuation',      'punctuation', 99, 'medium_high',1.50, true,  220),
  ('possessive_contraction',     'Possessive vs Contraction',   'punctuation', 10, 'medium',     1.00, true,  230),
  ('hyphen_usage',               'Hyphen Usage',                'punctuation', 11, 'low_medium', 0.35, true,  240),
  ('quotation_punctuation',      'Quotation Punctuation',       'punctuation', 99, 'low',        0.15, false, 250),

  -- Parallel Structure (elliptical_constructions and preposition_idiom belong here per GROUND_TRUTH §3.6/§3.8)
  ('parallel_structure',         'Parallel Structure',          'parallel_structure', 99, 'medium_high', 1.25, true, 260),
  ('conjunction_usage',          'Conjunction Usage',           'parallel_structure', 4,  'medium',      1.00, true, 270),
  ('elliptical_constructions',   'Elliptical Constructions',    'parallel_structure', 99, 'low',         0.10, false, 130),
  ('preposition_idiom',          'Preposition & Idiom',         'parallel_structure', 12, 'low_medium',  0.35, false, 290),

  -- Pronoun (pronoun_case + pronoun_clarity — pronoun_antecedent_agreement is under 'agreement' above;
  -- GROUND_TRUTH §4 priority 5 gives pronoun_case > pronoun_antecedent_agreement, hence priority 5 vs 6)
  ('pronoun_case',               'Pronoun Case',                'pronoun', 5,  'medium',       1.00, true,  280),
  ('pronoun_clarity',            'Pronoun Clarity',             'pronoun', 7,  'medium',       1.00, true,  285),

  -- Expression of Ideas (7 keys — not SEC; rhetorical effectiveness)
  ('redundancy_concision',       'Redundancy & Concision',      'expression_of_ideas', 99, 'medium',      1.00, true,  300),
  ('precision_word_choice',      'Precision & Word Choice',     'expression_of_ideas', 99, 'high',        1.50, true,  310),
  ('register_style_consistency', 'Register & Style Consistency','expression_of_ideas', 99, 'medium',      1.00, true,  320),
  ('logical_relationships',      'Logical Relationships',       'expression_of_ideas', 99, 'high',        1.50, true,  330),
  ('emphasis_meaning_shifts',    'Emphasis & Meaning Shifts',   'expression_of_ideas', 99, 'low_medium',  0.35, true,  340),
  ('data_interpretation_claims', 'Data Interpretation & Claims','expression_of_ideas', 99, 'medium',      1.00, true,  350),
  ('transition_logic',           'Transition Logic',              'expression_of_ideas', 3,  'high',        1.50, true,  360)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_domain (4 domains) ─────────────────────────────────────────────
INSERT INTO lookup_domain (key, display_name, sort_order) VALUES
('information_and_ideas',      'Information and Ideas',            10),
('craft_and_structure',        'Craft and Structure',              20),
('expression_of_ideas',        'Expression of Ideas',              30),
('standard_english_conventions','Standard English Conventions',    40)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_passage_topic_fine (normalized, was free-text) ────────────────
INSERT INTO lookup_passage_topic_fine (key, display_name, domain_key, sort_order) VALUES
('us_history',           'U.S. History',            'information_and_ideas', 10),
('world_history',        'World History',            'information_and_ideas', 20),
('economics',            'Economics',                'information_and_ideas', 30),
('civics_government',    'Civics & Government',      'information_and_ideas', 40),
('biology',              'Biology',                  'information_and_ideas', 50),
('chemistry',            'Chemistry',                'information_and_ideas', 60),
('physics',              'Physics',                  'information_and_ideas', 70),
('earth_science',        'Earth Science',            'information_and_ideas', 80),
('literary_fiction',     'Literary Fiction',         'craft_and_structure',   10),
('narrative_nonfiction', 'Narrative Nonfiction',     'craft_and_structure',   20),
('argumentative_essay',  'Argumentative Essay',      'craft_and_structure',   30),
('personal_essay',       'Personal Essay',           'craft_and_structure',   40),
('humanities',           'Humanities',               'craft_and_structure',   50),
('sec_no_passage',       'SEC (No Passage)',         'standard_english_conventions', 10)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_coaching_annotation_type (7 types) ────────────────────────────
INSERT INTO lookup_coaching_annotation_type (key, display_name, sort_order) VALUES
('syntactic_trap',   'Syntactic Trap',    10),
('key_evidence',     'Key Evidence',      20),
('np_cluster',       'NP Cluster',        30),
('clause_boundary',  'Clause Boundary',   40),
('blank_context',    'Blank Context',     50),
('distractor_lure',  'Distractor Lure',   60),
('rhetorical_move',  'Rhetorical Move',   70)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_reasoning_step_type (solver step types) ───────────────────────
INSERT INTO lookup_reasoning_step_type (key, display_name, sort_order) VALUES
('read_passage',      'Read Passage for Context',      10),
('identify_blank',    'Identify Blank/Underline',       20),
('predict_answer',    'Predict Answer Before Choices',  30),
('apply_rule',        'Apply Grammar Rule',             40),
('locate_evidence',   'Locate Supporting Evidence',     50),
('eliminate_option',  'Eliminate Distractor Option',    60),
('confirm_correct',   'Confirm Correct Answer',         70),
('check_consistency', 'Check Register/Tone Consistency',80)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_dimension_compatibility (incompatible bundles) ─────────────────
INSERT INTO lookup_dimension_compatibility
  (dimension_a, value_a, dimension_b, incompatible_value_b, reason, severity)
VALUES
  ('passage_source_type_key','literary_fiction','lexical_tier_key','technical',
   'Literary fiction does not use technical vocabulary register','error'),
  ('domain_key','standard_english_conventions','passage_source_type_key','literary_fiction',
   'SEC questions use single sentences, not literary passages','warning'),
  ('stimulus_mode_key','sentence_only','evidence_scope_key','multi_passage',
   'Sentence-only questions cannot have multi-passage evidence scope','error'),
  ('question_family_key','paired_passages','stimulus_mode_key','sentence_only',
   'Paired passage questions require a passage','error')
ON CONFLICT (dimension_a, value_a, dimension_b, incompatible_value_b) DO NOTHING;

-- ── lookup_passage_tense_register (GROUND_TRUTH §8.4) ─────────────────────
INSERT INTO lookup_passage_tense_register (key, display_name, sort_order) VALUES
('past',       'Past Tense (Narrative)',       10),
('present',    'Present Tense (Scientific)',   20),
('historical', 'Historical Present',           30),
('future',     'Future Tense (Conditional)',   40),
('mixed',      'Mixed Register',              50)
ON CONFLICT (key) DO NOTHING;
```

---

## Phase 1 — Core Question Schema

### M-005 — `paired_passage_sets` + `questions`

**Goals served:** Goals 1 & 3  
**Improvement over 001–042:** `paired_passage_sets` defined before `questions` (proper dependency order); `passage_word_count` and `stem_word_count` are computed by trigger from creation; `content_hash` trigger wired immediately; `retirement_status` present from creation; `tokenization_status` present from creation.

```sql
-- Paired passage sets — created BEFORE questions so FK can exist
CREATE TABLE paired_passage_sets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_a_text  text NOT NULL,
    passage_b_text  text NOT NULL,
    relationship_key text REFERENCES lookup_rhetorical_structure(key),
    passage_a_source text,
    passage_b_source text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE questions (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Source location
    exam_id                uuid REFERENCES exams(id) ON DELETE SET NULL,
    section_id             uuid REFERENCES exam_sections(id) ON DELETE SET NULL,
    module_id              uuid REFERENCES exam_modules(id) ON DELETE SET NULL,
    source_question_number int  CHECK (source_question_number > 0),

    -- Origin & provenance
    source_type   text NOT NULL DEFAULT 'official'
        CHECK (source_type IN ('official','adapted','practice','generated')),
    content_origin text NOT NULL DEFAULT 'official'
        CHECK (content_origin IN ('official','human_authored','generated','ai_human_revised','adapted')),
    is_official   boolean NOT NULL DEFAULT false,
    is_active     boolean NOT NULL DEFAULT true,

    -- Lifecycle
    retirement_status text NOT NULL DEFAULT 'active'
        CHECK (retirement_status IN ('active','flagged','retired','under_review')),
    retirement_reason text,
    tokenization_status text NOT NULL DEFAULT 'pending'
        CHECK (tokenization_status IN ('pending','ready','failed')),

    -- Coaching pipeline status
    coaching_completion_status text NOT NULL DEFAULT 'pending'
        CHECK (coaching_completion_status IN ('pending','ready','failed')),

    -- Explanation source (coaching_layer = authoritative post M-017)
    canonical_explanation_source text NOT NULL DEFAULT 'coaching_layer'
        CHECK (canonical_explanation_source IN ('coaching_layer','solver_steps','legacy')),

    -- Classification keys (denormed from lookup tables for fast querying)
    stimulus_mode_key text NOT NULL REFERENCES lookup_stimulus_mode(key),
    stem_type_key     text NOT NULL REFERENCES lookup_stem_type(key),
    passage_tense_register_key text REFERENCES lookup_passage_tense_register(key),  -- GROUND_TRUTH §8.4

    -- Content
    prompt_text          text,
    prompt_summary       text,
    passage_text         text,
    paired_passage_text  text,
    paired_passage_set_id uuid REFERENCES paired_passage_sets(id) ON DELETE RESTRICT,

    -- Structured data fields (charts, tables, graphs)
    notes_bullets_jsonb jsonb,
    table_data_jsonb    jsonb,
    graph_data_jsonb    jsonb,

    -- Answer
    correct_option_label char(1) CHECK (correct_option_label IN ('A','B','C','D')),

    -- Computed fields (set by triggers)
    passage_word_count  int,   -- auto-set by fn_set_word_counts()
    stem_word_count     int,   -- auto-set by fn_set_word_counts()
    content_hash        text,  -- SHA-256, auto-set by fn_set_content_hash()

    -- Answer confidence
    answer_confidence numeric(5,4),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chk_source_origin_consistency CHECK (
        NOT (source_type = 'official' AND content_origin != 'official')
    ),
    CONSTRAINT chk_no_generated_content_origin CHECK (
        content_origin != 'generated'  -- 'generated' only allowed in staging jobs
    ),
    CONSTRAINT chk_passage_word_count CHECK (
        passage_text IS NULL OR passage_word_count BETWEEN 1 AND 800
    ),
    UNIQUE (module_id, source_question_number)
);

-- Triggers
CREATE TRIGGER trg_paired_passage_sets_updated_at
    BEFORE UPDATE ON paired_passage_sets FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_questions_updated_at
    BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_questions_content_hash
    BEFORE INSERT OR UPDATE OF passage_text, prompt_text, paired_passage_text
    ON questions FOR EACH ROW EXECUTE FUNCTION fn_set_content_hash();

CREATE TRIGGER trg_questions_word_counts
    BEFORE INSERT OR UPDATE OF passage_text, prompt_text
    ON questions FOR EACH ROW EXECUTE FUNCTION fn_set_word_counts();

CREATE TRIGGER trg_questions_retirement_consistency
    BEFORE UPDATE OF is_active, retirement_status
    ON questions FOR EACH ROW EXECUTE FUNCTION fn_check_active_retirement_consistency();

CREATE TRIGGER trg_questions_paired_retirement
    BEFORE UPDATE OF retirement_status
    ON questions FOR EACH ROW EXECUTE FUNCTION fn_check_paired_retirement();

-- Indexes
CREATE INDEX idx_questions_module_qnum ON questions(module_id, source_question_number);
CREATE INDEX idx_questions_stimulus_stem ON questions(stimulus_mode_key, stem_type_key);
CREATE INDEX idx_questions_source ON questions(source_type, is_official, is_active);
CREATE INDEX idx_questions_exam_section_module ON questions(exam_id, section_id, module_id);
CREATE INDEX idx_questions_content_hash ON questions(content_hash);
CREATE INDEX idx_questions_paired_set ON questions(paired_passage_set_id)
    WHERE paired_passage_set_id IS NOT NULL;
CREATE INDEX idx_questions_retirement ON questions(retirement_status) WHERE retirement_status != 'active';
CREATE INDEX idx_questions_active_retired ON questions(is_active, retirement_status);
```

---

### M-006 — `question_classifications`

**Goals served:** Goals 1, 2, 3  
**Improvement over 001–042:**  
- All domain/skill/grammar columns are FK from day 1 (no free-text `domain text` to later normalize in migration 025)  
- `grammar_role_key` + `grammar_focus_key` both present from creation with FK enforcement  
- `no_change_is_correct` + `multi_error_flag` + `primary_error_field` present from creation (not added in migration 046)  
- `topic_fine_key` FK to `lookup_passage_topic_fine` (not free-text `topic_fine`)  
- `irt_b_quantitative_adjustment` present from creation  
- All style fingerprint columns in a single logical block

```sql
CREATE TABLE question_classifications (
    question_id uuid PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,

    -- ── DOMAIN HIERARCHY ──────────────────────────────────────────────────
    domain_key        text NOT NULL REFERENCES lookup_domain(key),
    skill_family_key  text NOT NULL REFERENCES lookup_skill_family(key),
    question_family_key text NOT NULL REFERENCES lookup_question_family(key),
    passage_type_key  text REFERENCES lookup_passage_type(key),

    -- ── EVIDENCE & MECHANISM ─────────────────────────────────────────────
    evidence_scope_key    text NOT NULL REFERENCES lookup_evidence_scope(key),
    evidence_location_key text NOT NULL REFERENCES lookup_evidence_location(key),
    evidence_mode_key     text REFERENCES lookup_evidence_mode(key),
    answer_mechanism_key  text NOT NULL REFERENCES lookup_answer_mechanism(key),
    solver_pattern_key    text NOT NULL REFERENCES lookup_solver_pattern(key),
    reading_scope_key     text REFERENCES lookup_reading_scope(key),
    reasoning_demand_key  text REFERENCES lookup_reasoning_demand(key),

    -- ── GRAMMAR / SEC ────────────────────────────────────────────────────
    grammar_role_key  text REFERENCES lookup_grammar_role(key),
    grammar_focus_key text REFERENCES lookup_grammar_focus(key),
    -- "No Change" answer type per GROUND_TRUTH §8.1 (~20% of SEC questions)
    no_change_is_correct boolean NOT NULL DEFAULT false,
    -- Multi-error questions per GROUND_TRUTH §8.2
    multi_error_flag     boolean NOT NULL DEFAULT false,
    primary_error_field  text REFERENCES lookup_grammar_focus(key),

    -- ── DIFFICULTY & IRT ─────────────────────────────────────────────────
    difficulty_overall text CHECK (difficulty_overall IN ('easy','medium','hard')),
    difficulty_reading text CHECK (difficulty_reading IN ('low','medium','high')),
    difficulty_grammar text CHECK (difficulty_grammar IN ('low','medium','high')),
    difficulty_inference text CHECK (difficulty_inference IN ('low','medium','high')),
    difficulty_vocab   text CHECK (difficulty_vocab IN ('low','medium','high')),
    distractor_strength text CHECK (distractor_strength IN ('low','medium','high')),
    irt_b_estimate     numeric(4,2) CHECK (irt_b_estimate BETWEEN -4 AND 4),
    irt_b_source       text CHECK (irt_b_source IN ('human_estimate','model_estimate','field_test')),
    irt_b_rubric_version text CHECK (irt_b_rubric_version IN ('v1','empirical','manual')),
    -- Additive offset for chart/table/graph questions (text-based IRT underpredicts)
    irt_b_quantitative_adjustment numeric(3,2) NOT NULL DEFAULT 0.00
        CHECK (irt_b_quantitative_adjustment BETWEEN -1.00 AND 1.00),

    -- ── PASSAGE STYLE FINGERPRINT ─────────────────────────────────────────
    syntactic_complexity_key   text REFERENCES lookup_syntactic_complexity(key),
    syntactic_interruption_key text REFERENCES lookup_syntactic_interruption(key),
    syntactic_trap_key         text REFERENCES lookup_syntactic_trap(key),
    evidence_distribution_key  text REFERENCES lookup_evidence_distribution(key),
    clause_depth               int  CHECK (clause_depth BETWEEN 0 AND 4),
    nominalization_density     text CHECK (nominalization_density IN ('low','medium','high')),
    sentence_length_profile    text CHECK (sentence_length_profile IN ('short','medium','long','mixed')),
    lexical_density            text CHECK (lexical_density IN ('low','medium','high')),
    lexical_tier_key           text REFERENCES lookup_lexical_tier(key),
    rhetorical_structure_key   text REFERENCES lookup_rhetorical_structure(key),
    noun_phrase_complexity_key text REFERENCES lookup_noun_phrase_complexity(key),
    vocabulary_profile_key     text REFERENCES lookup_vocabulary_profile(key),
    cohesion_device_key        text REFERENCES lookup_cohesion_device(key),
    epistemic_stance_key       text REFERENCES lookup_epistemic_stance(key),
    inference_distance_key     text REFERENCES lookup_inference_distance(key),
    transitional_logic_key     text REFERENCES lookup_transitional_logic(key),
    passage_word_count_band    text CHECK (passage_word_count_band IN
        ('very_short','short','medium','long','very_long')),

    -- ── PROSE REGISTER & TONE ─────────────────────────────────────────────
    prose_register_key       text REFERENCES lookup_prose_register(key),
    prose_tone_key           text REFERENCES lookup_prose_tone(key),
    passage_tense_register_key text REFERENCES lookup_passage_tense_register(key),  -- GROUND_TRUTH §8.4
    passage_source_type_key  text REFERENCES lookup_passage_source_type(key),
    craft_signals_array      text[],

    -- ── ITEM ANATOMY ──────────────────────────────────────────────────────
    blank_position_key       text CHECK (blank_position_key IN ('early','middle','late','sentence_final')),
    evidence_distance        int  CHECK (evidence_distance >= 0),
    blank_sentence_index     int  CHECK (blank_sentence_index > 0),
    passage_topic_domain_key text REFERENCES lookup_passage_topic_domain(key),
    topic_fine_key           text REFERENCES lookup_passage_topic_fine(key),  -- normalized FK
    narrator_perspective_key text CHECK (narrator_perspective_key IN
        ('first_person','third_person','institutional','impersonal')),
    argument_role_key        text REFERENCES lookup_argument_role(key),
    passage_era_key          text CHECK (passage_era_key IN ('contemporary','modern','historical','timeless')),
    passage_provenance_key   text CHECK (passage_provenance_key IN
        ('original_source','adapted','ai_generated','public_domain')),

    -- ── ANNOTATION PROVENANCE ──────────────────────────────────────────────
    annotation_source     text CHECK (annotation_source IN
        ('llm_pass1','llm_pass2','human_review','human_override','import')),
    annotated_by          text,
    annotation_confidence numeric(5,4),
    -- FK added after question_ingestion_jobs exists (M-012); NULL until first annotation
    annotation_job_id     uuid,  -- FK→question_ingestion_jobs added in M-012 via ALTER TABLE
    style_traits_jsonb    jsonb,
    taxonomy_notes_jsonb  jsonb,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chk_multi_error_primary_required CHECK (
        NOT multi_error_flag OR primary_error_field IS NOT NULL
    ),
    CONSTRAINT chk_irt_b_range CHECK (
        irt_b_estimate IS NULL OR irt_b_estimate BETWEEN -4 AND 4
    )
);

CREATE TRIGGER trg_qclass_updated_at BEFORE UPDATE ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_qclass_domain_skill ON question_classifications(domain_key, skill_family_key);
CREATE INDEX idx_qclass_family ON question_classifications(question_family_key);
CREATE INDEX idx_qclass_grammar ON question_classifications(grammar_role_key, grammar_focus_key);
CREATE INDEX idx_qclass_grammar_focus ON question_classifications(grammar_focus_key);
CREATE INDEX idx_qclass_domain_difficulty ON question_classifications(domain_key, difficulty_overall);
CREATE INDEX idx_qclass_difficulty ON question_classifications(difficulty_overall, irt_b_estimate);
CREATE INDEX idx_qclass_topic ON question_classifications(topic_fine_key);
```

---

### M-007 — `question_options`

**Goals served:** Goals 2 & 3  
**Improvement over 001–042:** `distractor_contrast_note` present from creation; `eliminability_key` FK from day 1 (not inline CHECK); all distractor anatomy FKs present from creation.

```sql
CREATE TABLE question_options (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id  uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_label char(1) NOT NULL CHECK (option_label IN ('A','B','C','D')),
    option_text  text NOT NULL,
    is_correct   boolean NOT NULL DEFAULT false,
    option_role  text NOT NULL CHECK (option_role IN ('correct','distractor')),

    -- ── DISTRACTOR ANALYSIS ───────────────────────────────────────────────
    distractor_type_key         text REFERENCES lookup_distractor_type(key),
    distractor_subtype_key      text REFERENCES lookup_distractor_subtype(key),
    distractor_construction_key text REFERENCES lookup_distractor_construction(key),
    semantic_relation_key       text REFERENCES lookup_semantic_relation(key),
    plausibility_source_key     text REFERENCES lookup_plausibility_source(key),
    why_plausible               text,
    why_wrong                   text,
    -- Specific contrast: how this distractor fails vs. the CORRECT answer
    distractor_contrast_note    text,  -- NULL for correct option

    -- ── OPTION ANATOMY ────────────────────────────────────────────────────
    option_pos_key       text CHECK (option_pos_key IN ('noun','verb','adjective','adverb','phrase')),
    option_register_key  text CHECK (option_register_key IN ('formal','informal','technical','neutral','archaic')),
    semantic_distance_key text CHECK (semantic_distance_key IN ('near','moderate','far')),
    eliminability_key    text REFERENCES lookup_eliminability(key),

    -- ── SCORING ───────────────────────────────────────────────────────────
    grammar_fit      text CHECK (grammar_fit IN ('yes','no','partial')),
    tone_match       text CHECK (tone_match IN ('yes','no','partial')),
    precision_score  int  CHECK (precision_score BETWEEN 1 AND 5),
    confidence_score numeric(5,4),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, option_label)
);

CREATE TRIGGER trg_qoptions_updated_at BEFORE UPDATE ON question_options
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_qoptions_question ON question_options(question_id);
CREATE INDEX idx_qoptions_correct ON question_options(question_id, is_correct);
CREATE INDEX idx_qoptions_distractor ON question_options(distractor_type_key, semantic_relation_key);
```

---

### M-008 — `solver_steps` + `question_reasoning`

**Goals served:** Goal 2 (Explanation Depth)  
**Improvement over 001–042:** `solver_steps` table created **before** `question_reasoning` so reasoning can reference it. `primary_solver_steps_jsonb` was created in migration 006, dropped in 034, and never replaced — this rebuild starts with the normalized table and never uses the JSONB column. `evidence_span_start_char` / `evidence_span_end_char` present from creation.

```sql
-- Structured solver steps — replaces dropped primary_solver_steps_jsonb
CREATE TABLE solver_steps (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id          uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    step_index           smallint NOT NULL CHECK (step_index BETWEEN 1 AND 10),
    step_type_key        text NOT NULL REFERENCES lookup_reasoning_step_type(key),
    step_description     text NOT NULL,
    step_evidence_text   text,    -- quoted excerpt supporting this step
    grammar_rule_applied text REFERENCES lookup_grammar_focus(key),  -- SEC only
    created_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, step_index)
);

CREATE INDEX idx_solver_steps_question ON solver_steps(question_id);

CREATE TABLE question_reasoning (
    question_id                uuid PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    predicted_answer_before_choices text,
    elimination_order_notes    text,
    common_student_error       text,
    coaching_tip               text,   -- one-liner
    coaching_summary           text,   -- 2-4 sentence explanation (coaching_layer authoritative)
    hidden_clue_type_key       text REFERENCES lookup_hidden_clue_type(key),
    evidence_after_blank_flag  boolean NOT NULL DEFAULT false,
    clue_distribution_key      text REFERENCES lookup_clue_distribution(key),
    -- Character-level evidence offsets into questions.passage_text
    evidence_span_start_char   int,
    evidence_span_end_char     int,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chk_evidence_span_offsets CHECK (
        (evidence_span_start_char IS NULL AND evidence_span_end_char IS NULL)
        OR (evidence_span_start_char IS NOT NULL
            AND evidence_span_end_char IS NOT NULL
            AND evidence_span_start_char >= 0
            AND evidence_span_end_char > evidence_span_start_char)
    )
);

CREATE TRIGGER trg_qreasoning_updated_at BEFORE UPDATE ON question_reasoning
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

### M-009 — `question_generation_profiles`

**Goals served:** Goals 1 & 3  
**Improvement over 001–042:** `target_grammar_role_key` present from creation; `target_mirror_status` tracks provenance of `target_*` fields from day 1; `target_passage_topic_fine_key` FK to normalized lookup (not free-text).

```sql
CREATE TABLE question_generation_profiles (
    question_id uuid PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    generation_template_ref_id uuid,  -- FK to generation_templates added in M-014
    generation_pattern_family_key text REFERENCES lookup_generation_pattern_family(key),
    reuse_for_generation boolean NOT NULL DEFAULT true,
    generation_notes     text,
    annotation_confidence numeric(5,4),

    -- Mirror status — tracks whether target_* fields are auto-populated or manually set.
    -- NULL = unset/unknown (detectable pipeline failure).
    -- Do NOT default to 'manual': on a greenfield schema that would silently mask any
    -- upsert.py code path that forgets to set this field.
    -- The pipeline always writes 'auto_mirrored'; human override writes 'manual'.
    target_mirror_status text DEFAULT NULL
        CHECK (target_mirror_status IS NULL OR target_mirror_status IN ('auto_mirrored','manual','drift')),
    mirror_computed_at   timestamptz,

    -- ── CORE TAXONOMY TARGETS ─────────────────────────────────────────────
    target_domain_key          text REFERENCES lookup_domain(key),
    target_skill_family_key    text REFERENCES lookup_skill_family(key),
    target_question_family_key text REFERENCES lookup_question_family(key),
    target_difficulty_overall  text CHECK (target_difficulty_overall IN ('easy','medium','hard')),
    target_passage_type_key    text REFERENCES lookup_passage_type(key),

    -- ── GRAMMAR TARGETS (both role AND focus, paired) ─────────────────────
    target_grammar_role_key  text REFERENCES lookup_grammar_role(key),
    target_grammar_focus_key text REFERENCES lookup_grammar_focus(key),

    -- ── PASSAGE STYLE TARGETS ─────────────────────────────────────────────
    target_syntactic_complexity_key   text REFERENCES lookup_syntactic_complexity(key),
    target_syntactic_interruption_key text REFERENCES lookup_syntactic_interruption(key),
    target_syntactic_trap_key         text REFERENCES lookup_syntactic_trap(key),
    target_clause_depth_min   smallint CHECK (target_clause_depth_min >= 0),
    target_clause_depth_max   smallint CHECK (target_clause_depth_max >= 0),
    target_nominalization_density text CHECK (target_nominalization_density IN ('low','medium','high')),
    target_lexical_density    text CHECK (target_lexical_density IN ('low','medium','high')),
    target_sentence_length_profile text CHECK (target_sentence_length_profile IN ('short','medium','long','mixed')),
    target_noun_phrase_complexity_key text REFERENCES lookup_noun_phrase_complexity(key),
    target_evidence_distribution_key  text REFERENCES lookup_evidence_distribution(key),
    target_lexical_tier_key    text REFERENCES lookup_lexical_tier(key),
    target_rhetorical_structure_key text REFERENCES lookup_rhetorical_structure(key),
    target_prose_register_key  text REFERENCES lookup_prose_register(key),
    target_prose_tone_key      text REFERENCES lookup_prose_tone(key),
    target_passage_source_type_key text REFERENCES lookup_passage_source_type(key),
    target_vocabulary_profile_key  text REFERENCES lookup_vocabulary_profile(key),
    target_epistemic_stance_key    text REFERENCES lookup_epistemic_stance(key),
    target_passage_topic_domain_key text REFERENCES lookup_passage_topic_domain(key),
    target_passage_topic_fine_key   text REFERENCES lookup_passage_topic_fine(key),

    -- ── DISCOURSE TARGETS ─────────────────────────────────────────────────
    target_cohesion_device_key    text REFERENCES lookup_cohesion_device(key),
    target_inference_distance_key text REFERENCES lookup_inference_distance(key),
    target_transitional_logic_key text REFERENCES lookup_transitional_logic(key),
    target_argument_role_key      text REFERENCES lookup_argument_role(key),

    -- ── ITEM ANATOMY TARGETS ──────────────────────────────────────────────
    target_blank_position_key    text CHECK (target_blank_position_key IN ('early','middle','late','sentence_final')),
    target_evidence_distance     int  CHECK (target_evidence_distance >= 0),
    target_answer_pos_key        text CHECK (target_answer_pos_key IN ('noun','verb','adjective','adverb','phrase')),
    target_register_contrast     text CHECK (target_register_contrast IN ('none','slight','strong')),
    target_narrator_perspective_key text CHECK (target_narrator_perspective_key IN
        ('first_person','third_person','institutional','impersonal')),
    target_passage_era_key       text CHECK (target_passage_era_key IN
        ('contemporary','modern','historical','timeless')),

    -- ── DISTRACTOR TARGETS ────────────────────────────────────────────────
    target_distractor_construction_key text REFERENCES lookup_distractor_construction(key),
    target_distractor_difficulty_spread text CHECK (target_distractor_difficulty_spread IN
        ('uniform_hard','tiered','two_hard_one_easy','two_easy_one_hard')),

    -- ── LEXILE / WORD COUNT ───────────────────────────────────────────────
    target_lexile_min   smallint CHECK (target_lexile_min BETWEEN 600 AND 1800),
    target_lexile_max   smallint CHECK (target_lexile_max BETWEEN 600 AND 1800),
    target_word_count_min smallint CHECK (target_word_count_min BETWEEN 15 AND 300),
    target_word_count_max smallint CHECK (target_word_count_max BETWEEN 15 AND 300),

    -- ── STYLE ARRAYS ──────────────────────────────────────────────────────
    target_craft_signals_jsonb text[],
    target_style_traits_jsonb  text[],

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT chk_target_clause_depth_range CHECK (
        target_clause_depth_min IS NULL OR target_clause_depth_max IS NULL
        OR target_clause_depth_max >= target_clause_depth_min
    ),
    CONSTRAINT chk_target_lexile_range CHECK (
        target_lexile_min IS NULL OR target_lexile_max IS NULL
        OR target_lexile_max >= target_lexile_min
    ),
    CONSTRAINT chk_target_word_count_range CHECK (
        target_word_count_min IS NULL OR target_word_count_max IS NULL
        OR target_word_count_max >= target_word_count_min
    )
);

CREATE TRIGGER trg_qgenprof_updated_at BEFORE UPDATE ON question_generation_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Phase 2 — Content & Media

### M-010 — `question_images`

**Goals served:** Goal 1 (image question ingestion)  
**Improvement over 001–042:** This table never existed in migrations 001–042. Image questions were ingested without a dedicated storage table.

```sql
CREATE TABLE question_images (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    image_source    text NOT NULL CHECK (image_source IN ('pdf_extract','upload','url')),
    image_data      bytea,
    ocr_text        text,           -- Tesseract OCR output
    alt_description text,           -- vision model description
    display_order   smallint NOT NULL DEFAULT 1,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_question_images_question ON question_images(question_id);
```

**App-layer changes:**
- `parsers/image_parser.py`: Write OCR output to `ocr_text`
- `pipeline/ingest.py`: Call vision model if `image_data` present; write to `alt_description`
- Pass 1 prompt: Include `alt_description` in assembled context when present

---

### M-011 — `question_embeddings` + `question_performance_records`

**Goals served:** Goal 3 (semantic similarity for generation)

```sql
CREATE TABLE question_embeddings (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id    uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    embedding_type text NOT NULL CHECK (embedding_type IN
        ('full_item','passage_only','explanation','taxonomy_summary','generation_profile')),
    embedding_text text NOT NULL,
    embedding      vector(1536) NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, embedding_type)
);

CREATE INDEX idx_qembed_ivfflat ON question_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_qembed_question ON question_embeddings(question_id);

CREATE TABLE question_performance_records (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    student_cohort  text NOT NULL,
    source_type     text NOT NULL DEFAULT 'practice'
        CHECK (source_type IN ('practice','field_test','live')),
    attempts        int  NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    correct_rate    numeric(4,3) CHECK (correct_rate BETWEEN 0 AND 1),
    avg_time_seconds int CHECK (avg_time_seconds > 0),
    distractor_pick_rates jsonb,
    irt_b_observed  numeric(4,2) CHECK (irt_b_observed BETWEEN -3 AND 3),
    irt_b_ci_lower  numeric(4,2),
    irt_b_ci_upper  numeric(4,2),
    notes           text,
    recorded_at     timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, student_cohort, source_type)
);

CREATE INDEX idx_qperf_question ON question_performance_records(question_id);
```

---

## Phase 3 — Ingestion Pipeline

### M-012 — `question_ingestion_jobs` + `ontology_proposals`

**Goals served:** Goal 1 (ingestion audit trail)  
**Improvement over 001–042:** Status workflow includes generation-specific states from creation; `canonical_explanation_source` is not needed here (it's on `questions`).

```sql
CREATE TABLE question_ingestion_jobs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file     text,
    input_format    text NOT NULL CHECK (input_format IN
        ('pdf','markdown','image','json','text','generated')),
    raw_input_text  text,
    pass1_json      jsonb,
    pass2_json      jsonb,
    validation_errors_json jsonb,
    review_notes    text,
    llm_provider    text NOT NULL,
    llm_model       text NOT NULL,
    content_origin  text NOT NULL DEFAULT 'official'
        CHECK (content_origin IN ('official','generated','ai_human_revised')),
    generation_run_id uuid,        -- FK to generation_runs added in M-013
    seed_question_id  uuid REFERENCES questions(id),
    question_id       uuid REFERENCES questions(id) ON DELETE SET NULL,

    status text NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending','extracting','annotating','draft','reviewed',
        'approved','rejected','failed',
        'drift_failed','conformance_failed'
    )),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_ingest_jobs_updated_at BEFORE UPDATE ON question_ingestion_jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Wire annotation_job_id FK now that question_ingestion_jobs exists
ALTER TABLE question_classifications
    ADD CONSTRAINT fk_qclass_annotation_job
    FOREIGN KEY (annotation_job_id)
    REFERENCES question_ingestion_jobs(id)
    ON DELETE SET NULL;

CREATE INDEX idx_ingest_jobs_status ON question_ingestion_jobs(status);
CREATE INDEX idx_ingest_jobs_question ON question_ingestion_jobs(question_id);

CREATE TABLE ontology_proposals (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lookup_table   text NOT NULL,
    proposed_key   text NOT NULL,
    proposed_label text,
    context_field  text,
    description    text,
    source_job_id  uuid REFERENCES question_ingestion_jobs(id) ON DELETE SET NULL,
    proposal_count int  NOT NULL DEFAULT 1 CHECK (proposal_count >= 1),
    status         text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','approved','rejected')),
    review_notes   text,
    reviewed_by    text,
    reviewed_at    timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (lookup_table, proposed_key)
);

CREATE TRIGGER trg_ontology_proposals_updated_at BEFORE UPDATE ON ontology_proposals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_ontology_proposals_status ON ontology_proposals(status);
```

---

## Phase 4 — Generation System

### M-013 — `generation_templates` + `generation_runs` + `generated_questions`

**Goals served:** Goal 3

```sql
CREATE TABLE generation_templates (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_code         text NOT NULL UNIQUE,
    question_family_key   text REFERENCES lookup_question_family(key),
    version               int  NOT NULL DEFAULT 1,
    is_active             boolean NOT NULL DEFAULT true,
    prompt_skeleton       text NOT NULL,
    constraint_schema     jsonb,  -- {required: [...], recommended: [...]}
    quality_gate_threshold numeric(3,2) CHECK (quality_gate_threshold BETWEEN 0 AND 1),
    description           text,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE generation_runs (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id       uuid REFERENCES generation_templates(id),
    model_name        text NOT NULL,
    model_params      jsonb,
    seed_question_ids uuid[],
    target_constraints jsonb,
    item_count        int,
    status            text NOT NULL DEFAULT 'running'
        CHECK (status IN ('running','complete','partial_complete','failed','cancelled')),
    run_notes         text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

-- Add FK from ingestion jobs to generation runs
ALTER TABLE question_ingestion_jobs
    ADD CONSTRAINT fk_ingest_jobs_gen_run
    FOREIGN KEY (generation_run_id) REFERENCES generation_runs(id);

-- Add FK from generation profiles to templates
ALTER TABLE question_generation_profiles
    ADD CONSTRAINT fk_qgenprof_template
    FOREIGN KEY (generation_template_ref_id) REFERENCES generation_templates(id);

CREATE TABLE generated_questions (
    id                             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                         uuid NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    question_id                    uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    seed_question_id               uuid REFERENCES questions(id),
    generation_rank                int,
    review_status                  text NOT NULL DEFAULT 'unreviewed'
        CHECK (review_status IN ('unreviewed','approved','rejected','needs_revision')),
    review_notes                   text,
    realism_score                  numeric(3,2) CHECK (realism_score BETWEEN 0 AND 1),
    approved_by                    text,
    approved_at                    timestamptz,
    generation_params_snapshot_jsonb jsonb,  -- immutable audit record
    generation_model_name          text,
    generation_provider            text
        CHECK (generation_provider IN ('anthropic','openai','openrouter','ollama')),
    created_at                     timestamptz NOT NULL DEFAULT now(),
    updated_at                     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, question_id)
);

CREATE TRIGGER trg_gen_templates_updated_at BEFORE UPDATE ON generation_templates
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_gen_runs_updated_at BEFORE UPDATE ON generation_runs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_gen_questions_updated_at BEFORE UPDATE ON generated_questions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_gen_questions_run ON generated_questions(run_id);
CREATE INDEX idx_gen_questions_seed ON generated_questions(seed_question_id);
CREATE INDEX idx_gen_runs_status ON generation_runs(status);
```

---

### M-014 — `distractor_slot_profiles`

**Goals served:** Goal 3 (per-slot distractor specification for generation)  
**Improvement over 001–042:** Never existed. Per-slot distractor profiling enables realistic answer choice distribution matching corpus fingerprint.

```sql
CREATE TABLE distractor_slot_profiles (
    id                            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id                   uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    slot_label                    char(1) NOT NULL CHECK (slot_label IN ('A','B','C','D')),
    target_distractor_type_key    text REFERENCES lookup_distractor_type(key),
    target_distractor_subtype_key text REFERENCES lookup_distractor_subtype(key),
    target_eliminability_key      text REFERENCES lookup_eliminability(key),
    construction_note             text,
    created_at                    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, slot_label)
);

CREATE INDEX idx_distractor_slot_profiles_question ON distractor_slot_profiles(question_id);

COMMENT ON TABLE distractor_slot_profiles IS
    'Per-slot distractor specification for generation. Enables realistic distractor '
    'distribution (which archetype goes in slot B vs. D) based on corpus fingerprint data.';
```

---

## Phase 5 — Intelligence & Coaching

### M-015 — `question_coaching_annotations`

**Goals served:** Goal 2 (Explanation Depth)  
**Improvement over 001–042:** `option_label` present from creation — in original schema (migration 034) this was missing, making it impossible to link a `distractor_lure` span to a specific answer option.

```sql
CREATE TABLE question_coaching_annotations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    span_field          text NOT NULL CHECK (span_field IN
        ('passage_text','prompt_text','paired_passage_text')),
    span_start_char     int  CHECK (span_start_char >= 0),
    span_end_char       int  CHECK (span_end_char >= 0),
    span_sentence_index int  CHECK (span_sentence_index >= 0),
    annotation_type     text REFERENCES lookup_coaching_annotation_type(key),
    label               text NOT NULL,
    coaching_note       text NOT NULL,
    -- Which answer option this span implicates (NULL = applies to stem/passage globally)
    option_label        char(1) CHECK (option_label IN ('A','B','C','D')),
    show_condition      text NOT NULL DEFAULT 'on_request'
        CHECK (show_condition IN ('always','on_error','on_request')),
    sort_order          int  NOT NULL DEFAULT 0,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_span_char_order CHECK (
        span_start_char IS NULL OR span_end_char IS NULL
        OR span_end_char > span_start_char
    ),
    CONSTRAINT chk_span_has_anchor CHECK (
        annotation_type = 'blank_context'
        OR span_start_char IS NOT NULL
        OR span_sentence_index IS NOT NULL
    )
);

CREATE INDEX idx_coaching_annotations_question ON question_coaching_annotations(question_id);
CREATE INDEX idx_coaching_annotations_type ON question_coaching_annotations(annotation_type);
CREATE INDEX idx_coaching_annotations_question_type ON question_coaching_annotations(question_id, annotation_type);
CREATE INDEX idx_coaching_annotations_on_error ON question_coaching_annotations(question_id)
    WHERE show_condition = 'on_error';

COMMENT ON COLUMN question_coaching_annotations.option_label IS
    'If this span implicates a specific answer option, record it here. '
    'For distractor_lure annotations, always populate with the specific distractor option. '
    'For key_evidence annotations, set to the correct option label. '
    'NULL = span applies globally to the stem or passage.';
```

---

### M-016 — `question_token_annotations` + `grammar_keys`

**Goals served:** Goal 1 (token-level grammar analysis)

```sql
CREATE TABLE grammar_keys (
    id          text PRIMARY KEY,
    label       text NOT NULL,
    color       text NOT NULL,
    light_bg    text NOT NULL,
    mid_bg      text NOT NULL,
    description text NOT NULL,
    sat_rule    text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE question_token_annotations (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id  uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    token_index  int  NOT NULL,
    token_text   text NOT NULL,
    is_blank     boolean NOT NULL DEFAULT false,
    grammar_tags text[] NOT NULL DEFAULT '{}',
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, token_index)
);

CREATE INDEX idx_token_annotations_question ON question_token_annotations(question_id);
```

---

## Phase 6 — Integrity & Enforcement

### M-017 — Cross-Dimension Compatibility Trigger

**Goals served:** Goals 1 & 3  
**Improvement over 001–042:** Never existed. Prevents impossible classification bundles from being stored and corrupting corpus fingerprint.

```sql
-- DESIGN NOTE — Dynamic SQL in this trigger:
-- The EXECUTE format approach dereferences column names stored in lookup_dimension_compatibility
-- at runtime. Two known risks:
-- 1. PERFORMANCE: This loop fires on every INSERT/UPDATE to question_classifications.
--    Acceptable for a test-prep corpus (thousands of rows), not for millions.
--    If the compatibility rule count stays < 20, the per-row cost is ~microseconds.
-- 2. SILENT NULL on column rename/drop: If dimension_a or dimension_b references a column
--    that no longer exists, the dynamic dereference returns NULL (not an error in PG composite
--    row access). The NULL != value_a check then silently passes. Mitigation: add a
--    startup-time validation function that verifies all dimension_a/dimension_b values in
--    lookup_dimension_compatibility are actual columns of question_classifications.
CREATE OR REPLACE FUNCTION fn_check_dimension_compatibility()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    rec  lookup_dimension_compatibility%ROWTYPE;
    va   text;
    vb   text;
BEGIN
    FOR rec IN SELECT * FROM lookup_dimension_compatibility WHERE severity = 'error' LOOP
        EXECUTE format('SELECT ($1).%I::text', rec.dimension_a) INTO va USING NEW;
        EXECUTE format('SELECT ($1).%I::text', rec.dimension_b) INTO vb USING NEW;
        IF va = rec.value_a AND vb = rec.incompatible_value_b THEN
            RAISE EXCEPTION
                'Incompatible classification: %=% conflicts with %=%. Reason: %',
                rec.dimension_a, va, rec.dimension_b, vb, rec.reason;
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_qclass_dimension_compatibility
    BEFORE INSERT OR UPDATE ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_check_dimension_compatibility();

-- Index for trigger lookups (M-017 gap fix H3/M3)
CREATE INDEX IF NOT EXISTS idx_dim_compat_severity
    ON lookup_dimension_compatibility (severity);
```

---

### M-018 — SEC Grammar Enforcement + Skill Family Validation Triggers

**Goals served:** Goal 1  
**Improvement over 001–042:** SEC enforcement existed only in `validator.py`. DB trigger provides defense-in-depth that protects against any write path, not just the API.

```sql
-- SEC: grammar_role_key + grammar_focus_key required for domain = SEC
-- Source: Taxonomy v2.6 §7.8
CREATE OR REPLACE FUNCTION fn_enforce_sec_grammar_fields()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.domain_key = 'standard_english_conventions' THEN
        IF NEW.grammar_role_key IS NULL THEN
            RAISE EXCEPTION
                'grammar_role_key required for SEC questions (domain = standard_english_conventions)';
        END IF;
        IF NEW.grammar_focus_key IS NULL THEN
            RAISE EXCEPTION
                'grammar_focus_key required for SEC questions (domain = standard_english_conventions)';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_qclass_sec_grammar
    BEFORE INSERT OR UPDATE OF domain_key, grammar_role_key, grammar_focus_key
    ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_enforce_sec_grammar_fields();

-- Skill family must belong to declared domain
CREATE OR REPLACE FUNCTION fn_check_skill_family_domain()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected_domain text;
BEGIN
    IF NEW.skill_family_key IS NOT NULL AND NEW.domain_key IS NOT NULL THEN
        SELECT domain_key INTO expected_domain
        FROM lookup_skill_family WHERE key = NEW.skill_family_key;
        IF expected_domain != NEW.domain_key THEN
            RAISE EXCEPTION 'skill_family_key % belongs to domain %, not %',
                NEW.skill_family_key, expected_domain, NEW.domain_key;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_qclass_skill_family_domain
    BEFORE INSERT OR UPDATE OF domain_key, skill_family_key
    ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_check_skill_family_domain();

-- Same enforcement on generation profiles
CREATE OR REPLACE FUNCTION fn_check_gen_profile_taxonomy()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected_domain text;
BEGIN
    IF NEW.target_skill_family_key IS NOT NULL AND NEW.target_domain_key IS NOT NULL THEN
        SELECT domain_key INTO expected_domain
        FROM lookup_skill_family WHERE key = NEW.target_skill_family_key;
        IF expected_domain != NEW.target_domain_key THEN
            RAISE EXCEPTION 'target_skill_family_key % belongs to domain %, not %',
                NEW.target_skill_family_key, expected_domain, NEW.target_domain_key;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_qgenprof_taxonomy
    BEFORE INSERT OR UPDATE OF target_domain_key, target_skill_family_key
    ON question_generation_profiles
    FOR EACH ROW EXECUTE FUNCTION fn_check_gen_profile_taxonomy();

-- Grammar focus must map to declared grammar role
CREATE OR REPLACE FUNCTION fn_check_grammar_focus_role()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected_role text;
BEGIN
    IF NEW.grammar_focus_key IS NOT NULL AND NEW.grammar_role_key IS NOT NULL THEN
        SELECT grammar_role_key INTO expected_role
        FROM lookup_grammar_focus WHERE key = NEW.grammar_focus_key;
        -- Allow if focus key has a different primary role only when role override is explicit
        -- (e.g., pronoun_antecedent_agreement can be classified under either 'agreement' or 'pronoun')
        -- Soft warning only — raise notice not exception
        IF expected_role != NEW.grammar_role_key THEN
            RAISE NOTICE 'grammar_focus_key % has primary role %, but grammar_role_key is %',
                NEW.grammar_focus_key, expected_role, NEW.grammar_role_key;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_qclass_grammar_focus_role
    BEFORE INSERT OR UPDATE OF grammar_role_key, grammar_focus_key
    ON question_classifications
    FOR EACH ROW EXECUTE FUNCTION fn_check_grammar_focus_role();
```

---

### M-019 — IRT B-Estimate Function

**Goals served:** Goals 1 & 3  
**Improvement over 001–042:** `fn_compute_irt_b_v1()` adds `irt_b_quantitative_adjustment` from creation; function is documented with the formula.

```sql
-- IRT B-Estimate Formula v1
-- Rubric weights from domain expertise:
--   inference_distance    × 0.30
--   evidence_distribution × 0.20
--   syntactic_complexity  × 0.20
--   lexical_tier          × 0.15
--   syntactic_trap        × 0.10
--   noun_phrase_complexity × 0.05
--
-- b = clamp( (raw − 3.125) / 2.225 × 3.0, −3.0, 3.0 )
-- Plus irt_b_quantitative_adjustment additive offset for data-interpretation questions

CREATE OR REPLACE FUNCTION fn_compute_irt_b_v1(p_question_id uuid)
RETURNS numeric(4,2) LANGUAGE plpgsql AS $$
DECLARE
    qc    question_classifications%ROWTYPE;
    raw   numeric;
    b     numeric;

    v_inference_distance    numeric;
    v_evidence_distribution numeric;
    v_syntactic_complexity  numeric;
    v_lexical_tier          numeric;
    v_syntactic_trap        numeric;
    v_noun_phrase_complexity numeric;
BEGIN
    SELECT * INTO qc FROM question_classifications WHERE question_id = p_question_id;
    IF NOT FOUND THEN RETURN NULL; END IF;

    -- Map lookup keys to numeric scores (1-5 scale).
    -- IMPORTANT: No ELSE fallback — unknown keys return NULL, which propagates to a NULL
    -- b-estimate rather than silently producing a wrong middle value. If a new key is added
    -- to a lookup table without updating this function, the b-estimate will be NULL (detectable)
    -- not 3 (silent error). A RAISE NOTICE surfaces the unknown key in the PG log.
    v_inference_distance := CASE qc.inference_distance_key
        WHEN 'literal'            THEN 1
        WHEN 'near_inference'     THEN 2
        WHEN 'moderate_inference' THEN 3
        WHEN 'deep_inference'     THEN 4
        WHEN 'abstract_synthesis' THEN 5
        ELSE NULL END;
    IF v_inference_distance IS NULL AND qc.inference_distance_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown inference_distance_key=%', qc.inference_distance_key;
        RETURN NULL;
    END IF;

    v_evidence_distribution := CASE qc.evidence_distribution_key
        WHEN 'single_sentence' THEN 1
        WHEN 'adjacent_sent'   THEN 2
        WHEN 'same_paragraph'  THEN 3
        WHEN 'across_passage'  THEN 4
        WHEN 'paired_passages' THEN 5
        ELSE NULL END;
    IF v_evidence_distribution IS NULL AND qc.evidence_distribution_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown evidence_distribution_key=%', qc.evidence_distribution_key;
        RETURN NULL;
    END IF;

    v_syntactic_complexity := CASE qc.syntactic_complexity_key
        WHEN 'simple'           THEN 1
        WHEN 'compound'         THEN 2
        WHEN 'complex'          THEN 3
        WHEN 'compound_complex' THEN 4
        WHEN 'multi_embedded'   THEN 5
        ELSE NULL END;
    IF v_syntactic_complexity IS NULL AND qc.syntactic_complexity_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown syntactic_complexity_key=%', qc.syntactic_complexity_key;
        RETURN NULL;
    END IF;

    v_lexical_tier := CASE qc.lexical_tier_key
        WHEN 'conversational' THEN 1
        WHEN 'general'        THEN 2
        WHEN 'academic'       THEN 3
        WHEN 'technical'      THEN 4
        WHEN 'specialized'    THEN 5
        ELSE NULL END;
    IF v_lexical_tier IS NULL AND qc.lexical_tier_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown lexical_tier_key=%', qc.lexical_tier_key;
        RETURN NULL;
    END IF;

    v_syntactic_trap := CASE qc.syntactic_trap_key
        WHEN 'none'                              THEN 1
        WHEN 'nearest_noun_attraction'           THEN 2
        WHEN 'early_clause_anchor'               THEN 2
        WHEN 'nominalization_obscures_subject'   THEN 3
        WHEN 'pronoun_ambiguity'                 THEN 3
        WHEN 'scope_of_negation'                 THEN 3
        WHEN 'modifier_attachment_ambiguity'     THEN 3
        WHEN 'temporal_sequence_ambiguity'        THEN 3
        WHEN 'garden_path'                       THEN 4
        WHEN 'interruption_breaks_subject_verb'   THEN 4
        WHEN 'long_distance_dependency'          THEN 4
        WHEN 'presupposition_trap'               THEN 4
        WHEN 'multiple'                          THEN 5
        ELSE NULL END;
    IF v_syntactic_trap IS NULL AND qc.syntactic_trap_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown syntactic_trap_key=%', qc.syntactic_trap_key;
        RETURN NULL;
    END IF;

    v_noun_phrase_complexity := CASE qc.noun_phrase_complexity_key
        WHEN 'simple'   THEN 1
        WHEN 'moderate' THEN 3
        WHEN 'complex'  THEN 5
        ELSE NULL END;
    IF v_noun_phrase_complexity IS NULL AND qc.noun_phrase_complexity_key IS NOT NULL THEN
        RAISE NOTICE 'fn_compute_irt_b_v1: unknown noun_phrase_complexity_key=%', qc.noun_phrase_complexity_key;
        RETURN NULL;
    END IF;

    raw := (v_inference_distance     * 0.30)
         + (v_evidence_distribution  * 0.20)
         + (v_syntactic_complexity   * 0.20)
         + (v_lexical_tier           * 0.15)
         + (v_syntactic_trap         * 0.10)
         + (v_noun_phrase_complexity * 0.05);

    b := GREATEST(-3.0, LEAST(3.0, (raw - 3.125) / 2.225 * 3.0));

    -- Add quantitative adjustment (for chart/table/graph questions)
    b := GREATEST(-4.0, LEAST(4.0, b + coalesce(qc.irt_b_quantitative_adjustment, 0)));

    RETURN ROUND(b::numeric, 2);
END;
$$;

-- Batch refresh function: recomputes b for all v1 rows or a single question
CREATE OR REPLACE FUNCTION fn_refresh_irt_b(p_question_id uuid DEFAULT NULL)
RETURNS int LANGUAGE plpgsql AS $$
DECLARE updated int := 0;
BEGIN
    UPDATE question_classifications
    SET irt_b_estimate = fn_compute_irt_b_v1(question_id),
        irt_b_source = 'model_estimate',
        irt_b_rubric_version = 'v1',
        updated_at = now()
    WHERE (p_question_id IS NULL OR question_id = p_question_id)
      AND (irt_b_rubric_version = 'v1' OR irt_b_source IS NULL)
      AND irt_b_source != 'field_test'
      AND irt_b_rubric_version NOT IN ('empirical','manual');
    GET DIAGNOSTICS updated = ROW_COUNT;
    RETURN updated;
END;
$$;
```

---

## Phase 7 — Reporting & Observability

### M-020 — Analytical Views

**Goals served:** All three

```sql
-- Full denormalized export
CREATE OR REPLACE VIEW question_flat_export AS
SELECT
    q.id, q.source_type, q.content_origin, q.is_official, q.is_active,
    q.retirement_status, q.stimulus_mode_key, q.stem_type_key,
    q.passage_text, q.prompt_text, q.paired_passage_text,
    q.correct_option_label, q.content_hash,
    q.passage_word_count, q.stem_word_count,
    e.exam_code, e.is_official AS exam_is_official,
    es.section_code, em.module_code, em.difficulty_band,
    qc.domain_key, qc.skill_family_key, qc.question_family_key,
    qc.grammar_role_key, qc.grammar_focus_key,
    qc.difficulty_overall, qc.irt_b_estimate,
    qc.no_change_is_correct, qc.multi_error_flag,
    qr.coaching_summary, qr.coaching_tip
FROM questions q
LEFT JOIN exams e ON e.id = q.exam_id
LEFT JOIN exam_sections es ON es.id = q.section_id
LEFT JOIN exam_modules em ON em.id = q.module_id
LEFT JOIN question_classifications qc ON qc.question_id = q.id
LEFT JOIN question_reasoning qr ON qr.question_id = q.id;

-- Corpus fingerprint: style fingerprint per question family from official questions
CREATE MATERIALIZED VIEW v_corpus_fingerprint AS
SELECT
    qc.question_family_key,
    qc.domain_key,
    qc.syntactic_complexity_key,
    qc.lexical_tier_key,
    qc.inference_distance_key,
    qc.evidence_distribution_key,
    qc.prose_register_key,
    AVG(q.passage_word_count) AS avg_passage_word_count,
    AVG(qc.irt_b_estimate)    AS avg_irt_b,
    COUNT(*)                   AS sample_count
FROM questions q
JOIN question_classifications qc ON qc.question_id = q.id
WHERE q.is_official = true
  AND q.retirement_status = 'active'
  AND q.is_active = true
GROUP BY
    qc.question_family_key, qc.domain_key,
    qc.syntactic_complexity_key, qc.lexical_tier_key,
    qc.inference_distance_key, qc.evidence_distribution_key,
    qc.prose_register_key;

CREATE UNIQUE INDEX idx_v_corpus_fingerprint
    ON v_corpus_fingerprint(question_family_key, syntactic_complexity_key,
                            lexical_tier_key, inference_distance_key,
                            evidence_distribution_key, prose_register_key);

-- Duplicate detection
CREATE OR REPLACE VIEW v_duplicate_questions AS
SELECT content_hash, COUNT(*) AS count, array_agg(id) AS question_ids
FROM questions
WHERE content_hash IS NOT NULL
GROUP BY content_hash
HAVING COUNT(*) > 1;

-- Generation traceability: snapshot vs. actual classification
CREATE OR REPLACE VIEW v_generation_traceability AS
SELECT
    gq.id AS gen_question_id,
    gq.run_id, gq.review_status, gq.realism_score,
    gq.generation_params_snapshot_jsonb,
    qc.domain_key, qc.question_family_key,
    qc.grammar_role_key, qc.grammar_focus_key,
    qc.difficulty_overall, qc.irt_b_estimate,
    qgp.target_mirror_status
FROM generated_questions gq
JOIN questions q ON q.id = gq.question_id
LEFT JOIN question_classifications qc ON qc.question_id = q.id
LEFT JOIN question_generation_profiles qgp ON qgp.question_id = q.id;

-- Coaching panel: all UI coaching data per question
CREATE OR REPLACE VIEW v_coaching_panel AS
SELECT
    q.id AS question_id,
    q.prompt_text, q.passage_text,
    qc.grammar_role_key, qc.grammar_focus_key,
    qc.no_change_is_correct,
    qr.coaching_summary, qr.coaching_tip,
    qr.evidence_span_start_char, qr.evidence_span_end_char,
    q.coaching_completion_status,
    q.canonical_explanation_source,
    json_agg(json_build_object(
        'annotation_type', ca.annotation_type,
        'span_field', ca.span_field,
        'span_start_char', ca.span_start_char,
        'span_end_char', ca.span_end_char,
        'option_label', ca.option_label,
        'label', ca.label,
        'coaching_note', ca.coaching_note
    ) ORDER BY ca.sort_order) AS coaching_annotations,
    json_agg(DISTINCT json_build_object(
        'step_index', ss.step_index,
        'step_type_key', ss.step_type_key,
        'step_description', ss.step_description,
        'step_evidence_text', ss.step_evidence_text,
        'grammar_rule_applied', ss.grammar_rule_applied
    ) ORDER BY ss.step_index) AS solver_steps
FROM questions q
LEFT JOIN question_classifications qc ON qc.question_id = q.id
LEFT JOIN question_reasoning qr ON qr.question_id = q.id
LEFT JOIN question_coaching_annotations ca ON ca.question_id = q.id
LEFT JOIN solver_steps ss ON ss.question_id = q.id
GROUP BY q.id, qc.grammar_role_key, qc.grammar_focus_key, qc.no_change_is_correct,
         qr.coaching_summary, qr.coaching_tip,
         qr.evidence_span_start_char, qr.evidence_span_end_char,
         q.coaching_completion_status, q.canonical_explanation_source;

-- Difficulty calibration: IRT estimated vs. observed
CREATE OR REPLACE VIEW v_difficulty_calibration AS
SELECT
    q.id, qc.domain_key, qc.question_family_key,
    qc.difficulty_overall, qc.irt_b_estimate, qc.irt_b_source,
    AVG(pr.irt_b_observed) AS avg_irt_b_observed,
    AVG(pr.correct_rate)   AS avg_correct_rate
FROM questions q
JOIN question_classifications qc ON qc.question_id = q.id
LEFT JOIN question_performance_records pr ON pr.question_id = q.id
GROUP BY q.id, qc.domain_key, qc.question_family_key,
         qc.difficulty_overall, qc.irt_b_estimate, qc.irt_b_source;

-- Ontology proposal queue: pending proposals ranked by frequency
CREATE OR REPLACE VIEW v_ontology_proposal_queue AS
SELECT lookup_table, proposed_key, proposed_label, proposal_count, status, created_at
FROM ontology_proposals
WHERE status = 'pending'
ORDER BY proposal_count DESC, created_at ASC;

-- Corpus fingerprint refresh function
-- Wraps REFRESH MATERIALIZED VIEW CONCURRENTLY so the generation pipeline has a
-- single callable entry point rather than a manual instruction buried in app-layer notes.
-- CONCURRENTLY requires the unique index on v_corpus_fingerprint (defined above) and
-- performs two sequential scans — do not call this inside a transaction block.
-- The generation conformance gate calls this before each run if the last refresh was
-- > 50 approved official questions ago (tracked via a simple counter in generation_runs).
CREATE OR REPLACE FUNCTION fn_refresh_corpus_fingerprint()
RETURNS text LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_corpus_fingerprint;
    RETURN 'refreshed at ' || now()::text;
EXCEPTION WHEN OTHERS THEN
    -- Concurrent refresh failed (e.g., called inside transaction) — fall back to blocking refresh
    RAISE NOTICE 'fn_refresh_corpus_fingerprint: CONCURRENTLY failed (%), falling back to blocking refresh', SQLERRM;
    REFRESH MATERIALIZED VIEW v_corpus_fingerprint;
    RETURN 'blocking refresh at ' || now()::text;
END;
$$;

-- ── ADDITIONAL ANALYTICAL VIEWS ──────────────────────────────────────────────
-- These views existed in the 001-042 schema and are critical for admin UI,
-- corpus analysis, and generation quality monitoring.

-- Counts by domain/family/difficulty per module
CREATE OR REPLACE VIEW v_question_distribution AS
SELECT
    em.module_code, em.difficulty_band,
    qc.domain_key, qc.question_family_key, qc.difficulty_overall,
    COUNT(*) AS question_count
FROM questions q
JOIN exam_modules em ON em.id = q.module_id
JOIN question_classifications qc ON qc.question_id = q.id
WHERE q.is_active = true AND q.retirement_status = 'active'
GROUP BY em.module_code, em.difficulty_band, qc.domain_key, qc.question_family_key, qc.difficulty_overall;

-- Distractor type effectiveness by question family
CREATE OR REPLACE VIEW v_distractor_effectiveness AS
SELECT
    qc.question_family_key,
    qo.distractor_type_key,
    COUNT(*) AS distractor_count,
    AVG(qo.confidence_score) AS avg_confidence
FROM question_options qo
JOIN questions q ON q.id = qo.question_id
JOIN question_classifications qc ON qc.question_id = q.id
WHERE qo.option_role = 'distractor'
GROUP BY qc.question_family_key, qo.distractor_type_key;

-- Which embedding types are present/missing per question
CREATE OR REPLACE VIEW v_embedding_coverage AS
SELECT
    q.id, q.source_type, q.is_official,
    e.embedding_type IS NOT NULL AS has_embedding,
    COUNT(e.id) AS embedding_count
FROM questions q
LEFT JOIN question_embeddings e ON e.question_id = q.id
GROUP BY q.id, q.source_type, q.is_official, e.embedding_type;

-- Job count by status/model
CREATE OR REPLACE VIEW v_ingestion_pipeline_summary AS
SELECT
    status, llm_model, content_origin,
    COUNT(*) AS job_count,
    MIN(created_at) AS earliest_job,
    MAX(created_at) AS latest_job
FROM question_ingestion_jobs
GROUP BY status, llm_model, content_origin;

-- Aggregate syntactic/style fingerprint counts
CREATE OR REPLACE VIEW v_prose_complexity_profile AS
SELECT
    qc.syntactic_complexity_key, qc.lexical_tier_key, qc.prose_register_key,
    qc.difficulty_overall,
    COUNT(*) AS question_count,
    AVG(q.passage_word_count) AS avg_word_count
FROM questions q
JOIN question_classifications qc ON qc.question_id = q.id
WHERE q.is_official = true AND q.is_active = true
GROUP BY qc.syntactic_complexity_key, qc.lexical_tier_key, qc.prose_register_key, qc.difficulty_overall;

-- Lexical × rhetorical structure × difficulty cross-tab
CREATE OR REPLACE VIEW v_style_complexity_distribution AS
SELECT
    qc.lexical_tier_key, qc.rhetorical_structure_key, qc.difficulty_overall,
    COUNT(*) AS question_count
FROM questions q
JOIN question_classifications qc ON qc.question_id = q.id
WHERE q.is_official = true
GROUP BY qc.lexical_tier_key, qc.rhetorical_structure_key, qc.difficulty_overall;

-- Full style fingerprint per question
CREATE OR REPLACE VIEW v_style_composition_profile AS
SELECT
    qc.question_id,
    qc.syntactic_complexity_key, qc.syntactic_interruption_key, qc.syntactic_trap_key,
    qc.lexical_tier_key, qc.rhetorical_structure_key, qc.prose_register_key,
    qc.prose_tone_key, qc.vocabulary_profile_key
FROM question_classifications qc;

-- Blank position / evidence distribution counts
CREATE OR REPLACE VIEW v_item_anatomy_profile AS
SELECT
    qc.blank_position_key, qc.evidence_distribution_key, qc.evidence_distance,
    qc.question_family_key,
    COUNT(*) AS question_count
FROM question_classifications qc
GROUP BY qc.blank_position_key, qc.evidence_distribution_key, qc.evidence_distance, qc.question_family_key;

-- Distractor construction / eliminability breakdown
CREATE OR REPLACE VIEW v_option_anatomy_distribution AS
SELECT
    qo.distractor_construction_key, qo.eliminability_key,
    COUNT(*) AS option_count
FROM question_options qo
WHERE qo.option_role = 'distractor'
GROUP BY qo.distractor_construction_key, qo.eliminability_key;

-- Raw distractor pick rates with context
CREATE OR REPLACE VIEW v_distractor_pick_analysis AS
SELECT
    pr.question_id, pr.student_cohort, pr.source_type,
    pr.correct_rate, pr.irt_b_observed,
    pr.distractor_pick_rates,
    qc.question_family_key, qc.difficulty_overall
FROM question_performance_records pr
JOIN question_classifications qc ON qc.question_id = pr.question_id;

-- Per-run generation stats
CREATE OR REPLACE VIEW v_generation_run_summary AS
SELECT
    gr.id AS run_id, gr.model_name, gr.status,
    gr.item_count AS requested_count,
    COUNT(gq.id) AS generated_count,
    COUNT(gq.id) FILTER (WHERE gq.review_status = 'approved') AS approved_count,
    AVG(gq.realism_score) AS avg_realism
FROM generation_runs gr
LEFT JOIN generated_questions gq ON gq.run_id = gr.id
GROUP BY gr.id, gr.model_name, gr.status, gr.item_count;

-- Human-readable module composition spec
CREATE OR REPLACE VIEW v_module_form_spec AS
SELECT
    e.exam_code, es.section_code, em.module_code, em.difficulty_band,
    emft.constraint_type, emft.dimension_key,
    emft.min_count, emft.max_count, emft.target_pct
FROM exam_module_form_targets emft
JOIN exam_modules em ON em.id = emft.module_id
JOIN exam_sections es ON es.id = em.section_id
JOIN exams e ON e.id = es.exam_id;

-- ── EMBEDDING INDEX REBUILD ─────────────────────────────────────────────────
-- Rebuild IVFFlat index with auto-computed lists parameter.
-- Call after bulk embedding ingestion when corpus > 500 rows.
-- Source: db_schema_diagram.md (function existed in 001-042 schema as migration 030)
CREATE OR REPLACE FUNCTION fn_rebuild_embedding_index(p_lists int DEFAULT NULL)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE
    v_row_count int;
    v_lists     int;
BEGIN
    SELECT COUNT(*) INTO v_row_count FROM question_embeddings;
    IF v_row_count < 100 THEN
        RETURN 'skipped: only ' || v_row_count || ' rows (need >= 100 for IVFFlat)';
    END IF;
    v_lists := COALESCE(p_lists, GREATEST(100, v_row_count / 10));
    -- Drop and recreate — cannot change lists parameter on existing index
    DROP INDEX IF EXISTS idx_qembed_ivfflat;
    EXECUTE format('CREATE INDEX idx_qembed_ivfflat ON question_embeddings
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s)', v_lists);
    RETURN 'rebuilt with lists=' || v_lists || ' for ' || v_row_count || ' rows at ' || now()::text;
END;
$$;
```

---

### M-021 — Row-Level Security Policies

**Goals served:** Infrastructure

```sql
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_ingestion_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_questions ENABLE ROW LEVEL SECURITY;

-- Read-all policy for authenticated users (admin UI)
CREATE POLICY questions_read_authenticated ON questions
    FOR SELECT TO authenticated USING (true);
CREATE POLICY questions_write_service_role ON questions
    FOR ALL TO service_role USING (true);

CREATE POLICY qclass_read_authenticated ON question_classifications
    FOR SELECT TO authenticated USING (true);
CREATE POLICY qclass_write_service_role ON question_classifications
    FOR ALL TO service_role USING (true);

CREATE POLICY ingest_jobs_read_authenticated ON question_ingestion_jobs
    FOR SELECT TO authenticated USING (true);
CREATE POLICY ingest_jobs_write_service_role ON question_ingestion_jobs
    FOR ALL TO service_role USING (true);

-- RLS for remaining data tables
ALTER TABLE question_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE solver_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_reasoning ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_generation_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_coaching_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_token_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_performance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE paired_passage_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE distractor_slot_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ontology_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE grammar_keys ENABLE ROW LEVEL SECURITY;

-- Apply consistent read/write policy pattern to all data tables
DO $$
DECLARE
    tbl text;
    data_tables text[] := ARRAY[
        'question_options','solver_steps','question_reasoning',
        'question_generation_profiles','question_coaching_annotations',
        'question_token_annotations','question_embeddings',
        'question_performance_records','question_images',
        'paired_passage_sets','generation_templates','generation_runs',
        'distractor_slot_profiles','ontology_proposals','grammar_keys'
    ];
BEGIN
    FOREACH tbl IN ARRAY data_tables LOOP
        EXECUTE format(
            'CREATE POLICY %I_read_authenticated ON %I FOR SELECT TO authenticated USING (true)',
            tbl, tbl
        );
        EXECUTE format(
            'CREATE POLICY %I_write_service_role ON %I FOR ALL TO service_role USING (true)',
            tbl, tbl
        );
    END LOOP;
END;
$$;
```

---

## Phase 8 — Seed Data

### M-022 — Seed `lookup_question_family` + `lookup_stimulus_mode` + `lookup_stem_type`

```sql
-- lookup_question_family (17 keys)
INSERT INTO lookup_question_family (key, display_name, sort_order) VALUES
('central_idea_main_purpose',  'Central Idea / Main Purpose',   10),
('detail_retrieval',           'Detail Retrieval',               20),
('author_purpose_method',      'Author Purpose / Method',        30),
('text_structure_function',    'Text Structure & Function',      40),
('cross_text_connection',      'Cross-Text Connection',          50),
('vocabulary_in_context',      'Vocabulary in Context',          60),
('command_of_evidence_textual','Command of Evidence — Textual',  70),
('command_of_evidence_quant',  'Command of Evidence — Quantitative', 80),
('inferences',                 'Inferences',                     90),
('paired_passages',            'Paired Passages',                100),
('transition_words',           'Transition Words',               110),
('rhetorical_synthesis',       'Rhetorical Synthesis',           120),
('revision_precision',         'Revision — Precision',           130),
('boundaries',                 'Boundaries (SEC)',               140),
('form_structure_sense',       'Form, Structure & Sense (SEC)',  150),
('data_interpretation',        'Data Interpretation',            160),
('sentence_completion',        'Sentence Completion',            170)
ON CONFLICT (key) DO NOTHING;

-- lookup_stimulus_mode (8 keys)
INSERT INTO lookup_stimulus_mode (key, display_name, sort_order) VALUES
('passage_only',        'Passage Only',               10),
('sentence_only',       'Sentence Only (SEC)',        20),
('passage_and_chart',   'Passage + Chart',            30),
('passage_and_table',   'Passage + Table',            40),
('passage_and_graph',   'Passage + Graph',            50),
('paired_passages',     'Paired Passages',            60),
('notes_bullets',       'Notes / Bullet Points',      70),
('quote_attribution',   'Quote Attribution',          80)
ON CONFLICT (key) DO NOTHING;

-- lookup_stem_type (12 keys) — NOT NULL FK on questions, must be seeded before any ingest
INSERT INTO lookup_stem_type (key, display_name, sort_order) VALUES
('fill_in_blank',           'Fill-in-the-Blank',              10),
('best_completes',          'Which Best Completes',           20),
('most_logical',            'Most Logical Completion',        30),
('main_idea',               'Main Idea / Central Claim',      40),
('primary_purpose',         'Primary Purpose',                50),
('function_of_detail',      'Function of a Detail',           60),
('words_in_context',        'Words in Context',               70),
('command_of_evidence',     'Command of Evidence',            80),
('data_interpretation',     'Data Interpretation',            90),
('paired_text_connection',  'Paired Text Connection',        100),
('transition_selection',    'Transition Word Selection',     110),
('rhetorical_goal',         'Rhetorical Goal / Synthesis',   120)
ON CONFLICT (key) DO NOTHING;
```

---

### M-023 — Seed `lookup_skill_family` + Passage & Mechanism Taxonomy Tables

```sql
-- lookup_skill_family (11 keys with domain_key FK)
INSERT INTO lookup_skill_family (key, display_name, domain_key, sort_order) VALUES
('central_ideas_details',    'Central Ideas & Details',   'information_and_ideas', 10),
('command_of_evidence',      'Command of Evidence',       'information_and_ideas', 20),
('inferences',               'Inferences',                'information_and_ideas', 30),
('words_in_context',         'Words in Context',          'craft_and_structure',   10),
('text_structure_purpose',   'Text Structure & Purpose',  'craft_and_structure',   20),
('cross_text_connections',   'Cross-Text Connections',    'craft_and_structure',   30),
('rhetorical_synthesis',     'Rhetorical Synthesis',      'expression_of_ideas',   10),
('transitions',              'Transitions',               'expression_of_ideas',   20),
('boundaries_skill',         'Boundaries',                'standard_english_conventions', 10),
('form_structure_sense_skill','Form, Structure & Sense',  'standard_english_conventions', 20),
('usage_skill',              'Usage & Conventions',       'standard_english_conventions', 30)
ON CONFLICT (key) DO NOTHING;

-- lookup_passage_type (5 keys)
INSERT INTO lookup_passage_type (key, display_name, sort_order) VALUES
('literary',          'Literary',           10),
('informational',     'Informational',      20),
('argumentative',     'Argumentative',      30),
('paired',            'Paired Passages',    40),
('not_applicable',    'Not Applicable (SEC)', 50)
ON CONFLICT (key) DO NOTHING;

-- lookup_reading_scope (2 keys)
INSERT INTO lookup_reading_scope (key, display_name, sort_order) VALUES
('local',   'Local (sentence/clause level)', 10),
('global',  'Global (passage level)',         20)
ON CONFLICT (key) DO NOTHING;

-- lookup_reasoning_demand (3 keys)
INSERT INTO lookup_reasoning_demand (key, display_name, sort_order) VALUES
('recall',     'Recall / Retrieval',       10),
('inference',  'Inference / Interpretation', 20),
('evaluation', 'Evaluation / Synthesis',   30)
ON CONFLICT (key) DO NOTHING;

-- lookup_evidence_scope (9 keys)
INSERT INTO lookup_evidence_scope (key, display_name, sort_order) VALUES
('single_sentence',   'Single Sentence',          10),
('adjacent_sentences','Adjacent Sentences',        20),
('same_paragraph',    'Same Paragraph',            30),
('across_paragraphs', 'Across Paragraphs',         40),
('full_passage',      'Full Passage',              50),
('multi_passage',     'Multi-Passage',             60),
('quantitative',      'Quantitative (Data)',       70),
('no_passage',        'No Passage (SEC)',          80),
('notes_bullets',     'Notes / Bullet Points',    90)
ON CONFLICT (key) DO NOTHING;

-- lookup_evidence_location (9 keys)
INSERT INTO lookup_evidence_location (key, display_name, sort_order) VALUES
('before_blank',      'Before Blank',             10),
('after_blank',       'After Blank',              20),
('both_sides',        'Both Sides of Blank',      30),
('passage_wide',      'Passage-Wide',             40),
('intro_paragraph',   'Intro Paragraph',          50),
('concluding_para',   'Concluding Paragraph',     60),
('data_source',       'Data Source (Chart/Table)',70),
('paired_passage_b',  'Paired Passage B',         80),
('distributed',       'Distributed Throughout',   90)
ON CONFLICT (key) DO NOTHING;

-- lookup_evidence_mode (3 keys)
INSERT INTO lookup_evidence_mode (key, display_name, sort_order) VALUES
('textual',      'Textual',      10),
('quantitative', 'Quantitative', 20),
('mixed',        'Mixed',        30)
ON CONFLICT (key) DO NOTHING;

-- lookup_answer_mechanism (10 keys)
INSERT INTO lookup_answer_mechanism (key, display_name, sort_order) VALUES
('predict_then_match',    'Predict Then Match',         10),
('locate_evidence',       'Locate Evidence',            20),
('eliminate_distractors', 'Eliminate Distractors',      30),
('apply_grammar_rule',    'Apply Grammar Rule',         40),
('cross_text_compare',    'Cross-Text Compare',         50),
('infer_author_intent',   'Infer Author Intent',        60),
('interpret_data',        'Interpret Data',             70),
('complete_rhetorical',   'Complete Rhetorical Goal',   80),
('select_transition',     'Select Transition Word',     90),
('select_precise_word',   'Select Precise Word',       100)
ON CONFLICT (key) DO NOTHING;

-- lookup_solver_pattern (13 keys)
INSERT INTO lookup_solver_pattern (key, display_name, sort_order) VALUES
('read_predict_match',    'Read → Predict → Match',       10),
('skim_locate_verify',    'Skim → Locate → Verify',       20),
('eliminate_confirm',     'Eliminate → Confirm',          30),
('rule_apply',            'Identify Rule → Apply',        40),
('compare_contrast',      'Compare → Contrast',           50),
('inference_chain',       'Build Inference Chain',        60),
('data_integrate',        'Integrate Data with Text',     70),
('tone_register_check',   'Check Tone/Register Fit',      80),
('two_pass_elimination',  'Two-Pass Elimination',         90),
('bracket_and_test',      'Bracket and Test Each Option', 100),
('meaning_in_context',    'Derive Meaning from Context',  110),
('structural_cue',        'Follow Structural Cue',        120),
('parallel_alignment',    'Align Parallel Elements',      130)
ON CONFLICT (key) DO NOTHING;

-- lookup_passage_topic_domain (12 keys)
INSERT INTO lookup_passage_topic_domain (key, display_name, sort_order) VALUES
('life_science',        'Life Science',               10),
('physical_science',    'Physical Science',           20),
('earth_space_science', 'Earth & Space Science',      30),
('social_science',      'Social Science',             40),
('us_founding_docs',    'U.S. Founding Documents',   50),
('global_conversations','Global Conversations',       60),
('literary_narrative',  'Literary Narrative',         70),
('humanities',          'Humanities',                 80),
('economics_business',  'Economics & Business',       90),
('technology',          'Technology',                100),
('health_medicine',     'Health & Medicine',         110),
('not_applicable',      'Not Applicable',            120)
ON CONFLICT (key) DO NOTHING;

-- lookup_argument_role (11 keys)
INSERT INTO lookup_argument_role (key, display_name, sort_order) VALUES
('thesis',            'Thesis / Central Claim',      10),
('supporting_evidence','Supporting Evidence',         20),
('counterargument',   'Counterargument',             30),
('concession',        'Concession',                  40),
('rebuttal',          'Rebuttal',                    50),
('background',        'Background / Context',        60),
('example',           'Example / Illustration',      70),
('conclusion',        'Conclusion',                  80),
('method',            'Method / Procedure',          90),
('finding',           'Finding / Result',           100),
('not_applicable',    'Not Applicable',             110)
ON CONFLICT (key) DO NOTHING;

-- lookup_hidden_clue_type (8 keys)
INSERT INTO lookup_hidden_clue_type (key, display_name, sort_order) VALUES
('none',                'None',                          10),
('pronoun_reference',   'Pronoun Reference',             20),
('transitional_signal', 'Transitional Signal',           30),
('contrast_marker',     'Contrast Marker',               40),
('parallel_structure',  'Parallel Structure Cue',        50),
('punctuation_cue',     'Punctuation Cue',               60),
('semantic_chain',      'Semantic Chain / Repetition',   70),
('discourse_marker',    'Discourse Marker',              80)
ON CONFLICT (key) DO NOTHING;

-- lookup_clue_distribution (7 keys)
INSERT INTO lookup_clue_distribution (key, display_name, sort_order) VALUES
('single_local',     'Single Local Clue',      10),
('adjacent_local',   'Adjacent Local Clues',   20),
('distributed',      'Distributed Clues',      30),
('passage_global',   'Passage-Global Cue',     40),
('no_clue',          'No External Clue',       50),
('quantitative',     'Quantitative Data Clue', 60),
('multi_source',     'Multi-Source Clue',      70)
ON CONFLICT (key) DO NOTHING;
```

---

### M-024 — Seed Generation Templates

**9 templates covering all major question families:**

```sql
INSERT INTO generation_templates (template_code, question_family_key, version, prompt_skeleton, constraint_schema, quality_gate_threshold, description) VALUES

('tmpl_coi_001', 'central_idea_main_purpose', 1,
 'Generate a DSAT-style "Central Idea" question for the following passage. The question should ask about the main purpose or central claim. Provide 4 answer choices (A-D) with exactly one correct answer.',
 '{"required": ["passage_text", "target_lexical_tier_key", "target_difficulty_overall"], "recommended": ["target_rhetorical_structure_key", "target_prose_register_key"]}',
 0.75, 'Central Idea / Main Purpose question generation'),

('tmpl_voc_001', 'vocabulary_in_context', 1,
 'Generate a DSAT-style "Vocabulary in Context" question. Choose a word from the passage and ask what it most nearly means in context.',
 '{"required": ["passage_text", "target_lexical_tier_key"], "recommended": ["target_inference_distance_key"]}',
 0.80, 'Vocabulary in Context question generation'),

('tmpl_coe_textual_001', 'command_of_evidence_textual', 1,
 'Generate a DSAT-style "Command of Evidence" question asking which quotation from the passage best supports a given claim.',
 '{"required": ["passage_text", "target_evidence_distribution_key"], "recommended": ["target_inference_distance_key", "target_rhetorical_structure_key"]}',
 0.75, 'Command of Evidence — Textual question generation'),

('tmpl_coe_quant_001', 'command_of_evidence_quant', 1,
 'Generate a DSAT-style "Command of Evidence — Quantitative" question integrating data from a table or graph.',
 '{"required": ["passage_text", "table_data_jsonb", "target_difficulty_overall"], "recommended": ["target_lexical_tier_key"]}',
 0.75, 'Command of Evidence — Quantitative question generation'),

('tmpl_transition_001', 'transition_words', 1,
 'Generate a DSAT-style "Transitions" question. The passage should have a blank where a transition word or phrase is needed. Ask which choice best completes the sentence.',
 '{"required": ["passage_text", "target_transitional_logic_key", "target_cohesion_device_key"], "recommended": ["target_rhetorical_structure_key"]}',
 0.80, 'Transitions / Expression of Ideas question generation'),

('tmpl_rhetorical_001', 'rhetorical_synthesis', 1,
 'Generate a DSAT-style "Rhetorical Synthesis" question using bullet-point notes. Ask which sentence best accomplishes a stated rhetorical goal.',
 '{"required": ["notes_bullets_jsonb", "target_argument_role_key"], "recommended": ["target_rhetoric_structure_key"]}',
 0.75, 'Rhetorical Synthesis question generation'),

('tmpl_boundaries_001', 'boundaries', 1,
 'Generate a DSAT-style "Boundaries" SEC question. The sentence should have a blank requiring selection of correct punctuation to delimit clauses.',
 '{"required": ["target_grammar_role_key", "target_grammar_focus_key", "target_difficulty_overall"], "recommended": ["no_change_is_correct"]}',
 0.85, 'Boundaries SEC question generation'),

('tmpl_fss_001', 'form_structure_sense', 1,
 'Generate a DSAT-style "Form, Structure & Sense" SEC question testing grammar rule application.',
 '{"required": ["target_grammar_role_key", "target_grammar_focus_key", "target_difficulty_overall"], "recommended": ["no_change_is_correct", "multi_error_flag"]}',
 0.85, 'Form, Structure & Sense SEC question generation'),

('tmpl_infer_001', 'inferences', 1,
 'Generate a DSAT-style "Inferences" question. Ask which choice most logically completes the passage given the evidence presented.',
 '{"required": ["passage_text", "target_inference_distance_key", "target_evidence_distribution_key"], "recommended": ["target_lexical_tier_key", "target_difficulty_overall"]}',
 0.80, 'Inferences question generation')
ON CONFLICT (template_code) DO NOTHING;
```

---

### M-025 — Seed Grammar Keys + Coaching Annotation Types

```sql
-- grammar_keys (token annotation grammar parts)
INSERT INTO grammar_keys (id, label, color, light_bg, mid_bg, description, sat_rule) VALUES
('subordinate_clause',   'Subordinate Clause',   '#6366f1', '#ede9fe', '#c4b5fd',
 'Dependent clause introduced by subordinating conjunction',
 'Subordinate clauses cannot stand alone; they create fragments if punctuated as sentences.'),
('subject',              'Subject',              '#10b981', '#d1fae5', '#6ee7b7',
 'Noun phrase functioning as grammatical subject',
 'Subject must agree with verb in number. Identify true subject, not nearest noun.'),
('main_verb',            'Main Verb',            '#f59e0b', '#fef3c7', '#fcd34d',
 'Finite verb expressing the main predication',
 'Main verb must agree with subject and maintain tense consistency.'),
('relative_clause',      'Relative Clause',      '#3b82f6', '#dbeafe', '#93c5fd',
 'Adjective clause introduced by relative pronoun (who, which, that)',
 'Restrictive (no commas) vs. non-restrictive (commas) determines which vs. that.'),
('subordinating_conj',   'Subordinating Conjunction', '#8b5cf6', '#f3e8ff', '#d8b4fe',
 'Conjunction making following clause dependent (because, although, since, etc.)',
 'Subordinating conjunctions create dependency. The subordinate clause cannot stand alone.'),
('modifier',             'Modifier',             '#ef4444', '#fee2e2', '#fca5a5',
 'Adjective, adverb, phrase, or clause modifying a noun or verb',
 'Modifiers must be placed adjacent to the word they modify. Dangling modifiers are errors.')
ON CONFLICT (id) DO NOTHING;
```

---

### M-026 — Seed IRT-Critical Dimension Lookup Tables

**Goals served:** Goals 1 & 3  
**Why critical:** All 6 tables below are referenced by hardcoded CASE statements in
`fn_compute_irt_b_v1()` (M-019). Any key not present here produces a NULL IRT estimate
and a `RAISE NOTICE` log line. These seeds must match the CASE keys exactly — no aliases,
no synonyms. A schema with these tables empty cannot compute a single difficulty estimate.

```sql
-- ── lookup_inference_distance (5 keys — IRT dimension 1, weight 0.30) ────────
-- Keys must match CASE statement in fn_compute_irt_b_v1() exactly.
INSERT INTO lookup_inference_distance (key, display_name, sort_order) VALUES
('literal',            'Literal / Retrieval',           10),
('near_inference',     'Near Inference',                 20),
('moderate_inference', 'Moderate Inference',             30),
('deep_inference',     'Deep Inference',                 40),
('abstract_synthesis', 'Abstract Synthesis',             50)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_evidence_distribution (5 keys — IRT dimension 2, weight 0.20) ──────
-- Key 'adjacent_sent' (not 'adjacent_sentences') matches IRT CASE exactly.
INSERT INTO lookup_evidence_distribution (key, display_name, sort_order) VALUES
('single_sentence', 'Single Sentence',              10),
('adjacent_sent',   'Adjacent Sentences',           20),
('same_paragraph',  'Same Paragraph',               30),
('across_passage',  'Across Passage',               40),
('paired_passages', 'Paired Passages',              50)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_syntactic_complexity (5 keys — IRT dimension 3, weight 0.20) ───────
INSERT INTO lookup_syntactic_complexity (key, display_name, sort_order) VALUES
('simple',           'Simple',                      10),
('compound',         'Compound',                    20),
('complex',          'Complex',                     30),
('compound_complex', 'Compound-Complex',            40),
('multi_embedded',   'Multi-Embedded Clauses',      50)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_lexical_tier (5 keys — IRT dimension 4, weight 0.15) ───────────────
INSERT INTO lookup_lexical_tier (key, display_name, sort_order) VALUES
('conversational', 'Conversational',                10),
('general',        'General / Everyday',            20),
('academic',       'Academic',                      30),
('technical',      'Technical / Discipline-Specific', 40),
('specialized',    'Highly Specialized / Archaic',  50)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_syntactic_trap (13 keys — GROUND_TRUTH Part 7 diagnostic vocabulary) ──────
-- These specific trap types drive realistic distractor construction and IRT difficulty scoring.
-- The IRT function (M-019) maps these 13 keys to ordinal difficulty scores (1-5).
-- IMPORTANT: The 5 ordinal keys (minor, moderate, significant, extreme) from the legacy
-- 001-042 schema are NOT used in this rebuild. Any existing data using those keys must be
-- migrated to the corresponding GROUND_TRUTH diagnostic key.
INSERT INTO lookup_syntactic_trap (key, display_name, description, sort_order) VALUES
('none',                            'None',                                   'No notable syntactic trap present', 10),
('nearest_noun_attraction',         'Nearest Noun Attraction',                'Verb matches closest noun instead of head noun', 20),
('garden_path',                     'Garden Path',                            'Initial parse leads down wrong path requiring revision', 30),
('early_clause_anchor',             'Early Clause Anchor',                    'Initial subordinate clause causes anchoring on wrong main subject', 40),
('nominalization_obscures_subject', 'Nominalization Obscures Subject',       'Heavy nominalization hides who is doing what', 50),
('interruption_breaks_subject_verb','Interruption Breaks Subject-Verb',      'Long interrupting phrase between subject and verb', 60),
('long_distance_dependency',        'Long Distance Dependency',               'Grammatical relationship spans many words', 70),
('pronoun_ambiguity',               'Pronoun Ambiguity',                      'Pronoun could refer to multiple antecedents', 80),
('scope_of_negation',               'Scope of Negation',                      'Negation word scope misunderstood (not all vs all not)', 90),
('modifier_attachment_ambiguity',  'Modifier Attachment Ambiguity',          'Participial or prepositional phrase could attach to multiple NPs', 100),
('presupposition_trap',             'Presupposition Trap',                    'Sentence presupposes something incorrectly accepted as stated', 110),
('temporal_sequence_ambiguity',     'Temporal Sequence Ambiguity',            'Order of events unclear due to mixed tense or non-linear narration', 120),
('multiple',                        'Multiple Traps',                         'More than one syntactic trap present', 130)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_noun_phrase_complexity (3 keys — IRT dimension 6, weight 0.05) ─────
-- Ordinal scores: simple=1, moderate=3, complex=5 (non-linear by design — see M-019)
INSERT INTO lookup_noun_phrase_complexity (key, display_name, sort_order) VALUES
('simple',   'Simple NP (bare noun / short phrase)', 10),
('moderate', 'Moderate NP (postmodified)',           20),
('complex',  'Complex NP (stacked / embedded)',      30)
ON CONFLICT (key) DO NOTHING;
```

---

### M-027 — Seed Prose Style & Passage Feature Lookup Tables

**Goals served:** Goals 1 & 3  
**Why here:** These tables drive the style-fingerprint profile used by the generation
conformance gate. They are not referenced by `fn_compute_irt_b_v1()` but are required
for `v_corpus_fingerprint` columns and `question_generation_profiles` FKs to resolve
without FK-violation errors on the first ingest.

```sql
-- ── lookup_syntactic_interruption (13 keys) ───────────────────────────────────
INSERT INTO lookup_syntactic_interruption (key, display_name, sort_order) VALUES
('none',                       'None',                            10),
('parenthetical_phrase',       'Parenthetical Phrase',            20),
('appositive',                 'Appositive',                      30),
('adverbial_clause',           'Adverbial Clause',                40),
('relative_clause_nonrestrictive','Non-Restrictive Relative Clause', 50),
('participial_phrase',         'Participial Phrase',              60),
('absolute_phrase',            'Absolute Phrase',                 70),
('prepositional_phrase',       'Long Prepositional Phrase',       80),
('embedded_question',          'Embedded Question / Indirect Q',  90),
('noun_clause',                'Noun Clause',                    100),
('gerund_phrase',              'Gerund Phrase',                  110),
('infinitive_phrase',          'Infinitive Phrase',              120),
('multiple',                   'Multiple Interruptions',         130)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_rhetorical_structure (11 keys) ─────────────────────────────────────
-- Used by paired_passage_sets.relationship_key and generation_profiles.
INSERT INTO lookup_rhetorical_structure (key, display_name, sort_order) VALUES
('narrative',          'Narrative',                    10),
('argument',           'Argument / Persuasion',        20),
('analysis',           'Analysis / Interpretation',    30),
('description',        'Description',                  40),
('compare_contrast',   'Compare / Contrast',           50),
('cause_effect',       'Cause & Effect',               60),
('problem_solution',   'Problem / Solution',           70),
('definition',         'Definition / Classification',  80),
('example_illustration','Example / Illustration',      90),
('data_synthesis',     'Data / Evidence Synthesis',   100),
('mixed',              'Mixed / Hybrid',              110)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_vocabulary_profile (7 keys) ────────────────────────────────────────
INSERT INTO lookup_vocabulary_profile (key, display_name, sort_order) VALUES
('conversational',    'Conversational',              10),
('general_academic',  'General Academic',            20),
('discipline_specific','Discipline-Specific',        30),
('technical',         'Technical',                   40),
('archaic',           'Archaic / Historical',        50),
('neologism',         'Neologism / Coined Term',     60),
('colloquial',        'Colloquial / Informal',       70)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_cohesion_device (8 keys) ───────────────────────────────────────────
INSERT INTO lookup_cohesion_device (key, display_name, sort_order) VALUES
('lexical_chain',       'Lexical Chain / Repetition', 10),
('pronoun_reference',   'Pronoun Reference',          20),
('synonym_substitution','Synonym Substitution',       30),
('transitional_phrase', 'Transitional Phrase',        40),
('parallelism',         'Parallelism',                50),
('conjunction',         'Conjunction',                60),
('ellipsis',            'Ellipsis',                   70),
('discourse_marker',    'Discourse Marker',           80)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_epistemic_stance (7 keys) ──────────────────────────────────────────
INSERT INTO lookup_epistemic_stance (key, display_name, sort_order) VALUES
('certain',     'Certain / Definitive',     10),
('probable',    'Probable',                 20),
('possible',    'Possible',                 30),
('hedged',      'Hedged / Qualified',       40),
('speculative', 'Speculative',              50),
('uncertain',   'Uncertain',                60),
('imperative',  'Imperative / Directive',   70)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_transitional_logic (10 keys) ───────────────────────────────────────
-- Used by generation_templates.constraint_schema and coaching annotations.
INSERT INTO lookup_transitional_logic (key, display_name, sort_order) VALUES
('addition',    'Addition (furthermore, also)',           10),
('contrast',    'Contrast (however, but, yet)',           20),
('concession',  'Concession (although, even though)',     30),
('cause',       'Cause (because, since, as)',             40),
('effect',      'Effect (therefore, thus, consequently)', 50),
('sequence',    'Sequence (first, then, finally)',        60),
('example',     'Example (for example, such as)',         70),
('emphasis',    'Emphasis (indeed, in fact)',             80),
('summary',     'Summary (in short, overall)',            90),
('comparison',  'Comparison (similarly, likewise)',      100)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_prose_register (6 keys) ───────────────────────────────────────────
INSERT INTO lookup_prose_register (key, display_name, sort_order) VALUES
('formal',        'Formal',       10),
('academic',      'Academic',     20),
('journalistic',  'Journalistic', 30),
('literary',      'Literary',     40),
('conversational','Conversational',50),
('technical',     'Technical',    60)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_prose_tone (8 keys) ────────────────────────────────────────────────
INSERT INTO lookup_prose_tone (key, display_name, sort_order) VALUES
('neutral',      'Neutral / Objective',    10),
('analytical',   'Analytical',            20),
('critical',     'Critical',              30),
('enthusiastic', 'Enthusiastic / Positive', 40),
('cautious',     'Cautious / Measured',   50),
('ironic',       'Ironic / Sardonic',     60),
('persuasive',   'Persuasive',            70),
('descriptive',  'Descriptive',           80)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_passage_source_type (7 keys) ──────────────────────────────────────
INSERT INTO lookup_passage_source_type (key, display_name, sort_order) VALUES
('academic_journal',   'Academic Journal Article',  10),
('literary_fiction',   'Literary Fiction',           20),
('nonfiction_book',    'Nonfiction Book / Excerpt',  30),
('newspaper_article',  'Newspaper / Magazine Article',40),
('historical_document','Historical Document',         50),
('scientific_report',  'Scientific Report / Study',  60),
('not_applicable',     'Not Applicable (SEC)',        70)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_craft_signal (8 keys) ─────────────────────────────────────────────
-- Text-level signals the author uses; recognized by coaching annotations.
INSERT INTO lookup_craft_signal (key, display_name, sort_order) VALUES
('contrast_word',     'Contrast Signal (however, but)',       10),
('concession_word',   'Concession Signal (although, despite)', 20),
('causal_word',       'Causal Signal (because, therefore)',   30),
('sequence_word',     'Sequence Signal (first, next)',        40),
('emphasis_signal',   'Emphasis Signal (indeed, notably)',    50),
('qualification_word','Qualification Signal (some, often)',   60),
('example_signal',    'Example Signal (for instance, such as)',70),
('summary_signal',    'Summary Signal (overall, in sum)',     80)
ON CONFLICT (key) DO NOTHING;
```

---

### M-028 — Seed Distractor Taxonomy & Generation Pattern Lookup Tables

**Goals served:** Goals 2 & 3  
**Why here:** Distractor taxonomy drives coaching annotation richness (Goal 2) and
generation quality gates (Goal 3). `lookup_eliminability` is an FK on `question_options`
and cannot be null if the eliminability scoring feature is active. `lookup_generation_pattern_family`
is required before `question_generation_profiles.generation_pattern_family_key` can be written.

```sql
-- ── lookup_distractor_type (14 keys) ─────────────────────────────────────────
-- Source: Taxonomy v2.6 §6 Distractor Taxonomy
INSERT INTO lookup_distractor_type (key, display_name, sort_order) VALUES
('scope_error',           'Scope Error (too broad/narrow)',      10),
('near_miss',             'Near Miss (close but wrong)',         20),
('opposite',              'Opposite Direction',                  30),
('out_of_scope',          'Out of Scope',                        40),
('true_but_irrelevant',   'True but Irrelevant',                 50),
('misread_trap',          'Misread Trap',                        60),
('syntactic_trap_word',   'Syntactic Trap Word',                 70),
('word_usage_error',      'Word Usage / Register Error',         80),
('partial_truth',         'Partial Truth',                       90),
('overclaiming',          'Overclaiming',                       100),
('underclaiming',         'Underclaiming',                      110),
('wrong_referent',        'Wrong Referent / Subject',           120),
('attractive_wrong',      'Attractive Wrong Answer',            130),
('grammar_confusion',     'Grammar Confusion',                  140)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_distractor_subtype (7 keys) ───────────────────────────────────────
INSERT INTO lookup_distractor_subtype (key, display_name, sort_order) VALUES
('synonym_swap',       'Synonym Swap',            10),
('pronoun_confusion',  'Pronoun Confusion',        20),
('negation_flip',      'Negation Flip',            30),
('scope_broad',        'Scope Too Broad',          40),
('scope_narrow',       'Scope Too Narrow',         50),
('register_mismatch',  'Register Mismatch',        60),
('tense_shift',        'Tense / Form Shift',       70)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_distractor_construction (11 keys) ─────────────────────────────────
INSERT INTO lookup_distractor_construction (key, display_name, sort_order) VALUES
('recycled_passage_language','Recycled Passage Language',    10),
('plausible_inference',      'Plausible Inference',          20),
('common_misconception',     'Common Misconception',         30),
('overgeneralization',       'Overgeneralization',           40),
('extreme_qualifier',        'Extreme Qualifier',            50),
('partial_match',            'Partial Match',                60),
('antonym_trap',             'Antonym Trap',                 70),
('near_paraphrase',          'Near Paraphrase',              80),
('wrong_character',          'Wrong Character / Subject',    90),
('wrong_time_frame',         'Wrong Time Frame',            100),
('conflation',               'Conflation of Two Ideas',     110)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_semantic_relation (21 keys) ───────────────────────────────────────
-- Used by distractor_slot_profiles and option-level coaching.
INSERT INTO lookup_semantic_relation (key, display_name, sort_order) VALUES
('synonym',         'Synonym',              10),
('antonym',         'Antonym',              20),
('hypernym',        'Hypernym (broader)',   30),
('hyponym',         'Hyponym (narrower)',   40),
('meronym',         'Meronym (part of)',    50),
('holonym',         'Holonym (whole of)',   60),
('cause',           'Cause',               70),
('effect',          'Effect',              80),
('instrument',      'Instrument',          90),
('agent',           'Agent',              100),
('patient',         'Patient / Object',   110),
('location',        'Location',           120),
('manner',          'Manner',             130),
('degree',          'Degree',             140),
('analogy',         'Analogy',            150),
('contrast',        'Contrast',           160),
('comparison',      'Comparison',         170),
('elaboration',     'Elaboration',        180),
('exemplification', 'Exemplification',    190),
('restatement',     'Restatement',        200),
('qualification',   'Qualification',      210)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_plausibility_source (16 keys) ─────────────────────────────────────
-- Why a distractor option feels correct to a test-taker who chooses wrong.
INSERT INTO lookup_plausibility_source (key, display_name, sort_order) VALUES
('passage_language_reuse', 'Passage Language Reuse',        10),
('common_knowledge',       'Common Knowledge / Assumption', 20),
('inference_extrapolation','Inference Overextension',       30),
('emotional_appeal',       'Emotional Appeal',              40),
('surface_similarity',     'Surface / Lexical Similarity',  50),
('topic_association',      'Topic Association',             60),
('partial_evidence',       'Partial Evidence',              70),
('overgeneralized_evidence','Overgeneralized Evidence',     80),
('misread_scope',          'Misread Scope',                 90),
('temporal_confusion',     'Temporal Confusion',           100),
('syntactic_parsing_error','Syntactic Parsing Error',      110),
('word_form_familiarity',  'Word Form Familiarity',        120),
('register_confusion',     'Register Confusion',           130),
('test_strategy_trap',     'Test Strategy Trap',           140),
('negation_confusion',     'Negation Confusion',           150),
('quantity_confusion',     'Quantity / Degree Confusion',  160)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_eliminability (3 keys) ─────────────────────────────────────────────
-- Ordinal difficulty of eliminating a distractor option, FK on question_options.
INSERT INTO lookup_eliminability (key, display_name, sort_order) VALUES
('easy',   'Easy to Eliminate (obviously wrong)',         10),
('medium', 'Medium (requires careful reading)',           20),
('hard',   'Hard (requires full passage + topic knowledge)', 30)
ON CONFLICT (key) DO NOTHING;

-- ── lookup_generation_pattern_family (18 keys) ───────────────────────────────
-- Maps to question families in generation_templates; drives batch generation weighting.
INSERT INTO lookup_generation_pattern_family (key, display_name, sort_order) VALUES
('word_in_context',      'Word in Context',              10),
('main_idea',            'Main Idea / Central Theme',    20),
('author_purpose',       'Author Purpose',               30),
('function_of_text',     'Function of Text Element',     40),
('supporting_detail',    'Supporting Detail',            50),
('inference',            'Inference',                    60),
('passage_organization', 'Passage Organization',         70),
('rhetorical_effect',    'Rhetorical Effect',            80),
('vocabulary_denotation','Vocabulary Denotation',        90),
('vocabulary_connotation','Vocabulary Connotation',     100),
('transitions_choice',   'Transitions Choice',          110),
('boundary_repair',      'Boundary / SEC Repair',       120),
('subject_verb_repair',  'Subject-Verb Agreement Repair', 130),
('tense_repair',         'Verb Tense / Form Repair',    140),
('modifier_repair',      'Modifier Placement Repair',   150),
('parallel_repair',      'Parallel Structure Repair',   160),
('pronoun_repair',       'Pronoun Form / Reference Repair', 170),
('sentence_combination', 'Sentence Combination',        180)
ON CONFLICT (key) DO NOTHING;
```

---

## Summary: Improvement Mapping

The table below maps every gap identified in the evaluation against where it is fixed in this rebuild vs. where it was introduced (or not introduced) in the 001–042 migrations.

| Gap / Issue | 001–042 Migration | v2 Rebuild Migration | Fix Type |
|---|---|---|---|
| Missing `run_on_sentence` | Added in patch 041 | M-004 (seed day 1) | Baked in |
| Missing `colon_dash_use` | Added in patch 042 | M-004 (seed day 1) | Baked in |
| Missing `appositive_punctuation` | Never added | M-004 (seed day 1) | New |
| Missing `quotation_punctuation` | Never added | M-004 (seed day 1) | New |
| Missing `preposition_idiom` | Never added | M-004 (seed day 1) | New |
| `lookup_grammar_focus` no role mapping | Added as patch PRD v1 | M-003 (column from creation) | Baked in |
| `lookup_grammar_focus` no priority | Never added | M-003 (column from creation) | New |
| `lookup_grammar_focus` no frequency | Never added | M-003 (column from creation) | New |
| `topic_fine` free-text (not FK) | M-025 normalized it | M-003 `lookup_passage_topic_fine` | Baked in |
| `solver_steps` dropped, not replaced | Dropped M-034 | M-008 (from creation, never JSONB) | Rebuilt |
| `option_label` missing on coaching | Never added | M-015 (from creation) | New |
| `coaching_completion_status` | Never added | M-005 (on questions from creation) | New |
| `canonical_explanation_source` | Never added | M-005 (on questions from creation) | New |
| `evidence_span_start/end_char` | Never added | M-008 (on question_reasoning) | New |
| `distractor_contrast_note` | Never added | M-007 (on question_options) | New |
| `target_grammar_role_key` missing | Never added | M-009 (from creation) | New |
| `target_mirror_status` missing | Never added | M-009 (from creation) | New |
| `target_passage_topic_fine_key` | Was free-text | M-009 FK from creation | Rebuilt |
| `irt_b_quantitative_adjustment` | Never added | M-006 (on classifications) | New |
| `no_change_is_correct` marker | Never added | M-006 (on classifications) | New |
| `multi_error_flag` + `primary_error_field` | Never added | M-006 (on classifications) | New |
| `passage_word_count` computed | Never added | M-005 (trigger from creation) | New |
| `question_images` table | Never created | M-010 | New |
| `paired_passage_sets` table | Never created | M-005 / M-002 area | New |
| SEC enforcement trigger | App-layer only | M-018 (DB trigger) | New |
| Cross-dimension compatibility | Never added | M-017 (trigger from creation) | New |
| `distractor_slot_profiles` | Never added | M-014 | New |
| Grammar frequency seeded | Never added | M-004 (on lookup_grammar_focus) | New |
| `target_composition_jsonb` deprecated | M-030 deprecated it | Never created (M-002 uses structured) | Baked in |
| `taxonomy_nodes/edges` dropped | Created M-008, dropped M-028 | Never created | Avoided |
| `primary_solver_steps_jsonb` dropped | Created M-006, dropped M-034 | Never created | Avoided |
| `style_profile_jsonb` dropped | Created then dropped M-024 | Never created | Avoided |

---

## App-Layer Changes Required

All changes listed are **in addition** to updating the SQL schema. These are the pipeline code changes necessary to utilize the new schema correctly.

### Pass 1 (`prompts/pass1_extraction.py`)
- Add `paired_passage_a_text` / `paired_passage_b_text` as optional output fields
- Include `alt_description` from `question_images` in assembled context when present

### Pass 2 (`prompts/pass2_annotation.py`)
- `ClassificationAnnotation`: add `no_change_is_correct`, `multi_error_flag`, `primary_error_field`
- `ClassificationAnnotation`: add `passage_tense_register_key: Optional[str]` (GROUND_TRUTH §8.4; set when verb_tense_consistency error is a passage-level register mismatch; NULL for non-SEC and non-tense questions)
- `ClassificationAnnotation`: replace `topic_fine: str` with `topic_fine_key: str` (FK-validated)
- `OptionAnnotation`: add `distractor_contrast_note: Optional[str]`
- `OptionAnnotation`: remove all distractor options from generating `distractor_contrast_note`
- `ReasoningAnnotation`: add `solver_steps: list[SolverStep]`, `evidence_span_start_char`, `evidence_span_end_char`
- `CoachingAnnotation` items: add `option_label: Optional[Literal['A','B','C','D']]`
- `GenerationProfileAnnotation`: add `target_grammar_role_key`, `target_passage_topic_fine_key`, `target_mirror_status` (always output `auto_mirrored`)
- `irt_b_estimate`: still always output null (computed server-side by `fn_compute_irt_b_v1`)
- Grammar focus disambiguation: rules must reference `disambiguation_priority` from `lookup_grammar_focus` (GROUND_TRUTH Part 4 priority table)
- `syntactic_trap_key` validation: must be one of the 13 GROUND_TRUTH Part 7 keys (`none`, `nearest_noun_attraction`, `garden_path`, `early_clause_anchor`, `nominalization_obscures_subject`, `interruption_breaks_subject_verb`, `long_distance_dependency`, `pronoun_ambiguity`, `scope_of_negation`, `modifier_attachment_ambiguity`, `presupposition_trap`, `temporal_sequence_ambiguity`, `multiple`) — not the 5 ordinal keys from the legacy schema. The IRT function maps these 13 keys to ordinal difficulty scores internally.

### `models/annotation.py`
- `SolverStep` model: `step_index`, `step_type_key`, `step_description`, `step_evidence_text`, `grammar_rule_applied`
- `ClassificationAnnotation`: new fields as above
- `OptionAnnotation`: add `distractor_contrast_note`
- All FK-validated fields: validate against `lookup_grammar_focus`, `lookup_grammar_role`, `lookup_passage_topic_fine` (added to ontology_ref.py)

### `models/ontology.py`
- Add `lookup_passage_topic_fine` to `LOOKUP_TABLE_NAMES`
- Add `lookup_passage_tense_register` to `LOOKUP_TABLE_NAMES`
- Add `lookup_reasoning_step_type` to `LOOKUP_TABLE_NAMES`
- Add `lookup_eliminability` to `LOOKUP_TABLE_NAMES`
- Add `lookup_syntactic_trap` to `LOOKUP_TABLE_NAMES` (13 GROUND_TRUTH keys, not 5 ordinal keys)

### `pipeline/validator.py`
- Add `topic_fine_key` to FK validation list
- Add `target_grammar_role_key` to generation profile FK validation
- Add `solver_steps[*].step_type_key` validation against `lookup_reasoning_step_type`
- Add rule: if `multi_error_flag = true`, `primary_error_field` must be non-null
- SEC check (`grammar_role_key` + `grammar_focus_key` non-null) remains as defense-in-depth alongside trigger

### `pipeline/upsert.py`
- Upsert `solver_steps` rows from `pass2_json.reasoning.solver_steps` using `ON CONFLICT (question_id, step_index) DO UPDATE SET step_type_key=EXCLUDED.step_type_key, step_description=EXCLUDED.step_description, step_evidence_text=EXCLUDED.step_evidence_text, grammar_rule_applied=EXCLUDED.grammar_rule_applied` — re-annotation must overwrite, not hard-fail
- For `question_coaching_annotations`: on re-annotation, `DELETE FROM question_coaching_annotations WHERE question_id = $1` first, then INSERT fresh rows — there is no unique constraint on (question_id, span_start_char, annotation_type) since a question can have multiple annotations of the same type, so DELETE+INSERT is the correct idempotency strategy rather than ON CONFLICT
- Write `topic_fine_key` (not `topic_fine`)
- Set `target_mirror_status = 'auto_mirrored'` and `mirror_computed_at = now()`
- Derive `target_grammar_role_key` from `target_grammar_focus_key` via `lookup_grammar_focus.grammar_role_key`
- Upsert `question_images` if `image_data` present in job context
- Upsert `paired_passage_sets` if `passage_a_text` / `passage_b_text` present in Pass 1 output
- Set `coaching_completion_status = 'ready'` after successful annotation insert
- Set `canonical_explanation_source = 'coaching_layer'` for all new upserts

### `pipeline/generation/drift.py`
- On drift detection: set `target_mirror_status = 'drift'` on `question_generation_profiles`
- Conformance gate: read `v_corpus_fingerprint` materialized view; call `fn_refresh_corpus_fingerprint()` (defined in M-020) when corpus grows > 50 new approved official questions since last refresh — do not inline the `REFRESH` SQL directly, use the function so the fallback-to-blocking logic is always applied

---

## Deployment Order

```
M-001  Platform foundation (functions, extensions)
M-002  Exam hierarchy
M-003  All lookup table structures (no data yet)
M-004  Seed critical lookup tables (grammar_role, grammar_focus, domain, passage_topic_fine, coaching_annotation_type, reasoning_step_type, dimension_compatibility)
M-005  questions + paired_passage_sets
M-006  question_classifications
M-007  question_options
M-008  solver_steps + question_reasoning
M-009  question_generation_profiles
M-010  question_images
M-011  question_embeddings + question_performance_records
M-012  question_ingestion_jobs + ontology_proposals
M-013  generation_templates + generation_runs + generated_questions (+ backfill FKs)
M-014  distractor_slot_profiles
M-015  question_coaching_annotations
M-016  question_token_annotations + grammar_keys
M-017  Cross-dimension compatibility trigger
M-018  SEC grammar enforcement + skill family + grammar focus/role triggers
M-019  IRT b-estimate function + batch refresh function
M-020  All analytical views + v_corpus_fingerprint materialized view
M-021  Row-level security policies
M-022  Seed question_family, stimulus_mode, stem_type lookup keys
M-023  Seed skill_family, domain, passage taxonomy lookup keys
M-024  Seed generation templates (9 templates)
M-025  Seed grammar_keys + coaching annotation type keys
M-026  Seed IRT-critical dimension lookup tables (6 tables: inference_distance, evidence_distribution, syntactic_complexity, lexical_tier, syntactic_trap, noun_phrase_complexity)
M-027  Seed prose style & passage feature lookup tables (10 tables: syntactic_interruption, rhetorical_structure, vocabulary_profile, cohesion_device, epistemic_stance, transitional_logic, prose_register, prose_tone, passage_source_type, craft_signal)
M-028  Seed distractor taxonomy & generation pattern lookup tables (7 tables: distractor_type, distractor_subtype, distractor_construction, semantic_relation, plausibility_source, eliminability, generation_pattern_family)
```

**Dependency rules:**
- M-003 before M-004 (structures before seeds)
- M-004 before M-005 (lookup_grammar_role/focus before question_classifications references)
- **M-022 MUST run before M-005** (lookup_stem_type and lookup_stimulus_mode are NOT NULL FKs on questions; their seed values must exist before any INSERT into questions)
- **M-023 MUST run before M-006** (lookup_skill_family is a NOT NULL FK on question_classifications; lookup_passage_type is an FK on question_classifications)
- M-005 before M-006 through M-009 (questions must exist for 1:1 satellite tables)
- M-012 before M-013 (ingestion_jobs before generation_runs FK backfill)
- M-017 and M-018 before first production ingest (triggers must be in place)
- M-019 before first IRT computation — **M-026 must run before M-019** (IRT function's CASE keys must exist in their lookup tables before any IRT computation is triggered)
- M-020 before any reporting or fingerprint conformance gate
- M-022, M-023, M-026 MUST all run before M-005 (NOT NULL FK seeds required before first question insert)
- M-024, M-025, M-027, M-028 can run in parallel after M-003 (no NOT NULL FK dependencies)
- M-026 is the highest-priority seed migration: run it before opening the system to any classification writes
- M-001 creates `schema_migrations` table; every subsequent migration MUST INSERT a row into it on successful completion
- Advisory lock function `fn_acquire_migration_lock()` MUST be called before each migration to prevent concurrent execution

---

## Success Criteria

### Goal 1 — A (Reading & Analyzing)
- [ ] All 39 grammar_focus_key values present in `lookup_grammar_focus` with role, priority, frequency
- [ ] SEC enforcement trigger blocks grammar_role/focus = NULL on insert and update
- [ ] `passage_word_count` computed automatically for every question with a passage
- [ ] `topic_fine_key` FK to normalized lookup (zero free-text values accepted)
- [ ] `question_images` ingested with OCR text + vision description
- [ ] `no_change_is_correct` correctly set on ≥95% of NO CHANGE answer questions
- [ ] Cross-dimension compatibility trigger blocks contradictory bundles

### Goal 2 — B+ (Explaining Correctness)
- [ ] `solver_steps` table populated for ≥80% of newly ingested questions (≥3 steps each)
- [ ] `distractor_lure` coaching annotations have `option_label` populated for ≥90% of cases
- [ ] `evidence_span_start/end_char` populated for ≥70% of passage-based questions
- [ ] `distractor_contrast_note` present for all incorrect options (≥90% non-null for distractors)
- [ ] `canonical_explanation_source = 'coaching_layer'` for all post-migration inserts

### Goal 3 — B+ (Realistic Generation)
- [ ] `target_mirror_status = 'auto_mirrored'` for all pipeline-generated profiles
- [ ] `target_grammar_role_key` auto-derived from `target_grammar_focus_key` for all SEC profiles
- [ ] Generation batch weights SEC question types by `avg_questions_per_module` from `lookup_grammar_focus`
- [ ] `distractor_slot_profiles` populated for all active generation template questions
- [ ] `v_corpus_fingerprint` refreshed after every 50 new official questions are approved
- [ ] Paired passage questions cannot be individually retired (trigger enforced)
- [ ] Generated question conformance gate uses refreshed fingerprint with `passage_word_count` in profile

### Seed Completeness Gate (prerequisite for all three goals)
- [ ] All 44 lookup tables have ≥ 1 row (verified by: `SELECT tablename FROM pg_tables WHERE tablename LIKE 'lookup_%' AND NOT EXISTS (SELECT 1 FROM ... LIMIT 1)` returning 0 rows)
- [ ] All 6 IRT-critical tables (`lookup_inference_distance`, `lookup_evidence_distribution`, `lookup_syntactic_complexity`, `lookup_lexical_tier`, `lookup_syntactic_trap`, `lookup_noun_phrase_complexity`) seeded with exact keys matching `fn_compute_irt_b_v1()` CASE statements
- [ ] `fn_compute_irt_b_v1()` returns a non-null value for at least one test classification row before system goes live
- [ ] Zero FK-orphan errors on the first batch ingest of 10 official questions after M-028 is applied
