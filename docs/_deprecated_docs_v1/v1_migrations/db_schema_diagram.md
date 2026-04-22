# DSAT Database Schema Diagram

**42 migrations applied** | Source of truth extracted from `backend/migrations/001–042`

Tables marked ~~strikethrough~~ were dropped in later migrations. Columns in *italics* were added by a specific migration number noted inline.

---

## Entity Relationship Overview

```mermaid
erDiagram
    %% ─── Exam Hierarchy ─────────────────────────────────────────────────
    exams {
        uuid id PK
        text exam_code UK
        text title
        text vendor
        text exam_type
        bool is_official
    }
    exam_sections {
        uuid id PK
        uuid exam_id FK
        text section_code
        int  sort_order
    }
    exam_modules {
        uuid id PK
        uuid section_id FK
        text module_code
        text difficulty_band
        jsonb target_composition_jsonb
    }
    exam_module_form_targets {
        uuid id PK
        uuid module_id FK
        text constraint_type
        text dimension_key
        int  min_count
        int  max_count
        num  target_pct
    }

    %% ─── Core Question Tables ────────────────────────────────────────────
    questions {
        uuid    id PK
        uuid    exam_id FK
        uuid    section_id FK
        uuid    module_id FK
        int     source_question_number
        text    source_type
        text    content_origin
        text    stimulus_mode_key FK
        text    stem_type_key FK
        text    passage_text
        text    prompt_text
        text    paired_passage_text
        text    correct_option_label
        text    content_hash
        text    retirement_status
        text    tokenization_status
        bool    is_active
        bool    is_official
    }
    question_classifications {
        uuid  question_id PK_FK
        text  domain_key FK
        text  skill_family_key FK
        text  question_family_key FK
        text  passage_type_key FK
        text  difficulty_overall
        num   irt_b_estimate
        text  irt_b_source
        text  irt_b_rubric_version
        text  grammar_role_key FK
        text  grammar_focus_key FK
        text  annotation_source
        text  annotated_by
        num   annotation_confidence
    }
    question_options {
        uuid  id PK
        uuid  question_id FK
        char  option_label
        text  option_text
        bool  is_correct
        text  option_role
        text  distractor_type_key FK
        text  distractor_subtype_key FK
        text  semantic_relation_key FK
        text  plausibility_source_key FK
        text  distractor_construction_key FK
    }
    question_reasoning {
        uuid  question_id PK_FK
        text  predicted_answer_before_choices
        text  elimination_order_notes
        text  common_student_error
        text  coaching_tip
        text  coaching_summary
        text  hidden_clue_type_key FK
        bool  evidence_after_blank_flag
        text  clue_distribution_key FK
    }
    question_generation_profiles {
        uuid  question_id PK_FK
        uuid  generation_template_ref_id FK
        text  generation_pattern_family_key FK
        text  target_domain_key FK
        text  target_skill_family_key FK
        text  target_question_family_key FK
        text  target_difficulty_overall
        text  target_syntactic_complexity_key FK
        text  target_prose_register_key FK
        text  target_passage_source_type_key FK
        text  target_grammar_focus_key FK
        bool  reuse_for_generation
        num   annotation_confidence
    }
    question_embeddings {
        uuid    id PK
        uuid    question_id FK
        text    embedding_type
        text    embedding_text
        vector  embedding
    }

    %% ─── Ingestion Pipeline ──────────────────────────────────────────────
    question_ingestion_jobs {
        uuid  id PK
        text  source_file
        text  input_format
        text  raw_input_text
        jsonb pass1_json
        jsonb pass2_json
        jsonb validation_errors_json
        text  status
        text  llm_provider
        text  llm_model
        text  content_origin
        uuid  question_id FK
        uuid  generation_run_id FK
        uuid  seed_question_id FK
    }

    %% ─── Generation Lifecycle ────────────────────────────────────────────
    generation_templates {
        uuid  id PK
        text  template_code UK
        text  question_family_key FK
        int   version
        bool  is_active
        text  prompt_skeleton
        jsonb constraint_schema
        num   quality_gate_threshold
    }
    generation_runs {
        uuid  id PK
        uuid  template_id FK
        text  model_name
        jsonb model_params
        uuid_arr seed_question_ids
        jsonb target_constraints
        int   item_count
        text  status
    }
    generated_questions {
        uuid  id PK
        uuid  run_id FK
        uuid  question_id FK
        uuid  seed_question_id FK
        int   generation_rank
        text  review_status
        num   realism_score
        jsonb generation_params_snapshot_jsonb
        text  generation_model_name
        text  generation_provider
    }

    %% ─── Performance & Coaching ──────────────────────────────────────────
    question_performance_records {
        uuid  id PK
        uuid  question_id FK
        text  student_cohort
        text  source_type
        int   attempts
        num   correct_rate
        num   irt_b_observed
        jsonb distractor_pick_rates
    }
    question_coaching_annotations {
        uuid  id PK
        uuid  question_id FK
        text  span_field
        int   span_start_char
        int   span_end_char
        int   span_sentence_index
        text  annotation_type FK
        text  label
        text  coaching_note
        text  show_condition
    }

    %% ─── Token Annotations ───────────────────────────────────────────────
    question_token_annotations {
        uuid  id PK
        uuid  question_id FK
        int   token_index
        text  token_text
        bool  is_blank
        text_arr grammar_tags
    }
    grammar_keys {
        text  id PK
        text  label
        text  color
        text  light_bg
        text  mid_bg
        text  description
        text  sat_rule
    }

    %% ─── Ontology Proposals ──────────────────────────────────────────────
    ontology_proposals {
        uuid  id PK
        text  lookup_table
        text  proposed_key
        text  proposed_label
        uuid  source_job_id FK
        int   proposal_count
        text  status
    }

    %% ─── Relationships ───────────────────────────────────────────────────
    exams ||--o{ exam_sections : "has"
    exam_sections ||--o{ exam_modules : "has"
    exam_modules ||--o{ exam_module_form_targets : "targets"
    exam_modules ||--o{ questions : "contains"
    exams ||--o{ questions : "source"
    exam_sections ||--o{ questions : "source"

    questions ||--|| question_classifications : "classified by"
    questions ||--o{ question_options : "has 4"
    questions ||--|| question_reasoning : "explained by"
    questions ||--|| question_generation_profiles : "profiled by"
    questions ||--o{ question_embeddings : "embedded as"
    questions ||--o{ question_performance_records : "tracked by"
    questions ||--o{ question_coaching_annotations : "annotated by"
    questions ||--o{ question_token_annotations : "tokenized by"

    question_ingestion_jobs ||--o| questions : "produces"
    question_ingestion_jobs ||--o| generation_runs : "belongs to run"
    question_ingestion_jobs ||--o| ontology_proposals : "triggers"

    generation_templates ||--o{ generation_runs : "drives"
    generation_runs ||--o{ generated_questions : "produces"
    generated_questions }o--|| questions : "approved as"
    generated_questions }o--o| questions : "seeded from"
    question_generation_profiles }o--o| generation_templates : "references"
```

---

## 1. Exam Hierarchy

```
exams
├── id uuid PK
├── exam_code text UNIQUE NOT NULL
├── title text NOT NULL
├── vendor text
├── exam_type text DEFAULT 'DSAT_RW'
├── is_official boolean DEFAULT false
├── notes text
├── created_at / updated_at timestamptz

exam_sections
├── id uuid PK
├── exam_id uuid FK→exams (CASCADE)
├── section_code text NOT NULL
├── title text NOT NULL
├── sort_order int NOT NULL CHECK(>0)
├── UNIQUE(exam_id, section_code)
└── created_at / updated_at

exam_modules
├── id uuid PK
├── section_id uuid FK→exam_sections (CASCADE)
├── module_code text NOT NULL
├── title text NOT NULL
├── sort_order int NOT NULL CHECK(>0)        UNIQUE per section [032]
├── difficulty_band text                      CHECK(easy|medium|hard|adaptive) [032]
├── target_composition_jsonb jsonb            DEPRECATED since 030
├── UNIQUE(section_id, module_code)
└── created_at / updated_at

exam_module_form_targets  [030]
├── id uuid PK
├── module_id uuid FK→exam_modules (CASCADE)
├── constraint_type text CHECK(domain|difficulty|passage_type|question_family)
├── dimension_key text NOT NULL
├── min_count smallint
├── max_count smallint
├── target_pct numeric(5,4)
└── UNIQUE(module_id, constraint_type, dimension_key)
```

---

## 2. Questions (Core)

```
questions
├── id uuid PK
├── exam_id uuid FK→exams (SET NULL)
├── section_id uuid FK→exam_sections (SET NULL)
├── module_id uuid FK→exam_modules (SET NULL)
├── source_question_number int                CHECK(>0)
├── source_type text DEFAULT 'official'       CHECK(official|adapted|practice|generated) [025]
├── content_origin text NOT NULL DEFAULT 'official'  [020]
│     CHECK(official|human_authored|generated|ai_human_revised|adapted)
│     NOTE: 'generated' blocked by chk_no_generated_in_questions [036]
├── is_official boolean NOT NULL DEFAULT false
├── is_active boolean NOT NULL DEFAULT true
├── retirement_status text DEFAULT 'active'   [022]
│     CHECK(active|flagged|retired|under_review)
├── retirement_reason text                    [022]
├── stimulus_mode_key text FK→lookup_stimulus_mode NOT NULL
├── stem_type_key text FK→lookup_stem_type NOT NULL
├── prompt_text text
├── prompt_summary text
├── passage_text text
├── paired_passage_text text
├── notes_bullets_jsonb jsonb                 shape: {title, bullets[]}
├── table_data_jsonb jsonb                    shape: {title, headers[], rows[][], units, source_note}
├── graph_data_jsonb jsonb                    shape: {graph_type, title, x_axis, y_axis, series[]}
├── correct_option_label char(1)              CHECK(A|B|C|D)
├── explanation_short text
├── explanation_full text
├── evidence_span_text text
├── answer_confidence numeric(5,4)
├── content_hash text                         SHA-256, auto-computed by trigger [027]
├── tokenization_status text                  [040] CHECK(pending|ready|failed)
├── UNIQUE(module_id, source_question_number)
└── created_at / updated_at
```

**Cross-column constraints [036]:**
- `source_type='official'` → `content_origin='official'`
- `source_type='adapted'` → `content_origin IN (official, adapted, human_authored)`
- `source_type='generated'` → `content_origin='ai_human_revised'`

---

## 3. Question Classifications

One row per question (1:1 with `questions`).

```
question_classifications
├── question_id uuid PK FK→questions (CASCADE)
│
│── CORE TAXONOMY ──────────────────────────────────
├── domain_key text NOT NULL FK→lookup_domain           [025]
├── skill_family_key text NOT NULL FK→lookup_skill_family [025]
├── question_family_key text NOT NULL FK→lookup_question_family
├── passage_type_key text FK→lookup_passage_type         [025]
├── evidence_scope_key text NOT NULL FK→lookup_evidence_scope
├── evidence_location_key text NOT NULL FK→lookup_evidence_location
├── answer_mechanism_key text NOT NULL FK→lookup_answer_mechanism
├── solver_pattern_key text NOT NULL FK→lookup_solver_pattern
├── evidence_mode_key text FK→lookup_evidence_mode       [025]
├── reading_scope_key text FK→lookup_reading_scope       [025]
├── reasoning_demand_key text FK→lookup_reasoning_demand [025]
│
│── GRAMMAR / SEC ──────────────────────────────────
├── grammar_role_key text FK→lookup_grammar_role         [025]
├── grammar_focus_key text FK→lookup_grammar_focus       [019]
│   (Trigger enforces grammar_role/focus cross-consistency) [029]
│
│── DIFFICULTY ─────────────────────────────────────
├── difficulty_overall text CHECK(easy|medium|hard)
├── difficulty_reading text CHECK(low|medium|high)       [037]
├── difficulty_grammar text CHECK(low|medium|high)       [037]
├── difficulty_inference text CHECK(low|medium|high)     [037]
├── difficulty_vocab text CHECK(low|medium|high)         [037]
├── distractor_strength text CHECK(low|medium|high)      [037]
├── irt_b_estimate numeric(4,2)                          [021]
│   CHECK(BETWEEN -4 AND 4) [033]; computed by fn_compute_irt_b_v1()
├── irt_b_source text CHECK(human_estimate|model_estimate|field_test) [021]
├── irt_b_rubric_version text CHECK(v1|empirical|manual)  [033]
│
│── PASSAGE STYLE FINGERPRINT ──────────────────────
├── syntactic_complexity_key text FK→lookup_syntactic_complexity [017]
├── syntactic_interruption_key text FK→lookup_syntactic_interruption [017]
├── syntactic_trap_key text FK→lookup_syntactic_trap     [017]
├── evidence_distribution_key text FK→lookup_evidence_distribution [017]
├── clause_depth int CHECK(0–4)                          [017, 032]
├── nominalization_density text CHECK(low|medium|high)   [017]
├── sentence_length_profile text CHECK(short|medium|long|mixed) [017]
├── lexical_density text CHECK(low|medium|high)          [017]
├── lexical_tier_key text FK→lookup_lexical_tier          [018]
├── rhetorical_structure_key text FK→lookup_rhetorical_structure [018]
├── noun_phrase_complexity_key text FK→lookup_noun_phrase_complexity [018]
├── vocabulary_profile_key text FK→lookup_vocabulary_profile [018]
├── cohesion_device_key text FK→lookup_cohesion_device    [019]
├── epistemic_stance_key text FK→lookup_epistemic_stance  [019]
├── inference_distance_key text FK→lookup_inference_distance [019]
├── transitional_logic_key text FK→lookup_transitional_logic [019]
├── passage_word_count_band text                          [019]
│   CHECK(very_short|short|medium|long|very_long)
├── prose_register_key text FK→lookup_prose_register      [024]
├── prose_tone_key text FK→lookup_prose_tone              [024]
├── passage_source_type_key text FK→lookup_passage_source_type [024]
├── craft_signals_array text[]                            [024]
│
│── ITEM ANATOMY ───────────────────────────────────
├── blank_position_key text CHECK(early|middle|late|sentence_final) [020]
├── evidence_distance int CHECK(≥0)                      [020]
├── blank_sentence_index int CHECK(>0)                   [020]
├── passage_topic_domain_key text FK→lookup_passage_topic_domain [020]
├── narrator_perspective_key text                         [020]
│   CHECK(first_person|third_person|institutional|impersonal)
├── argument_role_key text FK→lookup_argument_role        [020]
├── passage_era_key text CHECK(contemporary|modern|historical|timeless) [020]
├── passage_provenance_key text                           [020]
│   CHECK(original_source|adapted|ai_generated|public_domain)
│
│── FREE-FORM FIELDS ───────────────────────────────
├── topic_broad text
├── topic_fine text
├── style_traits_jsonb jsonb                              [037]
├── taxonomy_notes_jsonb jsonb                            [037]
│
│── ANNOTATION PROVENANCE ──────────────────────────
├── annotation_source text                               [030]
│   CHECK(llm_pass1|llm_pass2|human_review|human_override|import)
├── annotated_by text                                    [030]
├── annotation_job_id uuid FK→question_ingestion_jobs    [030]
├── annotation_confidence numeric(5,4)                   [030]
└── created_at / updated_at
```

---

## 4. Question Options

Four rows per question (A/B/C/D).

```
question_options
├── id uuid PK
├── question_id uuid FK→questions (CASCADE)
├── option_label char(1) NOT NULL CHECK(A|B|C|D)
├── option_text text NOT NULL
├── is_correct boolean NOT NULL DEFAULT false
├── option_role text NOT NULL CHECK(correct|distractor)
│
│── DISTRACTOR ANALYSIS ────────────────────────────
├── distractor_type_key text FK→lookup_distractor_type
├── distractor_subtype_key text FK→lookup_distractor_subtype [025]
├── distractor_construction_key text FK→lookup_distractor_construction [020]
├── semantic_relation_key text FK→lookup_semantic_relation
├── plausibility_source_key text FK→lookup_plausibility_source
├── why_plausible text
├── why_wrong text
│
│── OPTION ANATOMY ─────────────────────────────────
├── option_pos_key text CHECK(noun|verb|adjective|adverb|phrase) [020]
├── option_register_key text CHECK(formal|informal|technical|neutral|archaic) [020]
├── semantic_distance_key text CHECK(near|moderate|far) [020]
├── eliminability_key text CHECK(easy|medium|hard)      [020]
│
│── SCORING ────────────────────────────────────────
├── grammar_fit text CHECK(yes|no|partial)
├── tone_match text CHECK(yes|no|partial)
├── precision_score int CHECK(1–5)
├── confidence_score numeric(5,4)
├── UNIQUE(question_id, option_label)
└── created_at / updated_at
```

---

## 5. Question Reasoning

One row per question (1:1).

```
question_reasoning
├── question_id uuid PK FK→questions (CASCADE)
├── predicted_answer_before_choices text
├── elimination_order_notes text
├── common_student_error text
├── coaching_tip text                   (one-liner)
├── coaching_summary text               [034] (2–4 sentence explanation)
├── hidden_clue_type_key text FK→lookup_hidden_clue_type [025]
├── evidence_after_blank_flag boolean NOT NULL DEFAULT false
├── clue_distribution_key text FK→lookup_clue_distribution
└── created_at / updated_at

DROPPED: primary_solver_steps_jsonb [034], hidden_clue_type text [025]
```

---

## 6. Question Generation Profiles

One row per question (1:1). All `target_*` columns are nullable.

```
question_generation_profiles
├── question_id uuid PK FK→questions (CASCADE)
├── generation_template_ref_id uuid FK→generation_templates [020]
├── generation_pattern_family_key text FK→lookup_generation_pattern_family
├── reuse_for_generation boolean NOT NULL DEFAULT true
├── generation_notes text
├── annotation_confidence numeric(5,4)  [038]
│
│── CORE TAXONOMY TARGETS ──────────────────────────
├── target_domain_key text FK→lookup_domain               [025]
├── target_skill_family_key text FK→lookup_skill_family   [025]
├── target_question_family_key text FK→lookup_question_family [025]
├── target_difficulty_overall text CHECK(easy|medium|hard) [025]
├── target_passage_type_key text FK→lookup_passage_type    [025]
│
│── PASSAGE STYLE TARGETS ──────────────────────────
├── target_syntactic_complexity_key text FK→lookup_syntactic_complexity [025]
├── target_syntactic_interruption_key text FK→lookup_syntactic_interruption [026]
├── target_syntactic_trap_key text FK→lookup_syntactic_trap [026]
├── target_clause_depth_min smallint CHECK(≥0)             [026]
├── target_clause_depth_max smallint CHECK(≥0, ≥min)       [026]
├── target_nominalization_density text CHECK(low|medium|high) [026]
├── target_lexical_density text CHECK(low|medium|high)     [026]
├── target_sentence_length_profile text                    [031]
│   CHECK(short|medium|long|mixed)
├── target_noun_phrase_complexity_key text FK→lookup_noun_phrase_complexity [031]
├── target_evidence_distribution_key text FK→lookup_evidence_distribution  [031]
├── target_lexical_tier_key text FK→lookup_lexical_tier    [018]
├── target_rhetorical_structure_key text FK→lookup_rhetorical_structure [018]
├── target_prose_register_key text FK→lookup_prose_register [024]
├── target_prose_tone_key text FK→lookup_prose_tone        [024]
├── target_passage_source_type_key text FK→lookup_passage_source_type [032]
├── target_vocabulary_profile_key text FK→lookup_vocabulary_profile [031]
├── target_epistemic_stance_key text FK→lookup_epistemic_stance [025]
├── target_argument_role_key text FK→lookup_argument_role  [025]
├── target_passage_topic_domain_key text FK→lookup_passage_topic_domain [025]
├── target_craft_signals_jsonb text[]                      [024]
├── target_style_traits_jsonb text[]                       [024]
│
│── DISCOURSE TARGETS ──────────────────────────────
├── target_cohesion_device_key text FK→lookup_cohesion_device [019]
├── target_inference_distance_key text FK→lookup_inference_distance [019]
├── target_transitional_logic_key text FK→lookup_transitional_logic [019]
├── target_grammar_focus_key text FK→lookup_grammar_focus  [019]
│
│── ITEM ANATOMY TARGETS ───────────────────────────
├── target_blank_position_key text                         [020]
│   CHECK(early|middle|late|sentence_final)
├── target_evidence_distance int CHECK(≥0)                 [020]
├── target_answer_pos_key text CHECK(noun|verb|adjective|adverb|phrase) [020]
├── target_register_contrast text CHECK(none|slight|strong) [020]
├── target_narrator_perspective_key text                   [025]
│   CHECK(first_person|third_person|institutional|impersonal)
├── target_passage_era_key text                            [025]
│   CHECK(contemporary|modern|historical|timeless)
│
│── DISTRACTOR TARGETS ─────────────────────────────
├── target_distractor_construction_key text FK→lookup_distractor_construction [026]
├── target_distractor_difficulty_spread text               [026]
│   CHECK(uniform_hard|tiered|two_hard_one_easy|two_easy_one_hard)
│
│── LEXILE / WORD COUNT ────────────────────────────
├── target_lexile_min smallint CHECK(600–1800)             [024]
├── target_lexile_max smallint CHECK(600–1800, ≥min)       [024]
├── target_word_count_min smallint CHECK(15–300)           [025]
├── target_word_count_max smallint CHECK(15–300, ≥min)     [025]
└── created_at / updated_at

DROPPED: target_reading_level, target_sentence_complexity, target_passage_length [025]
         generation_template_id (text) [025]
         target_style_constraints_jsonb [024]
         target_distractor_pattern_jsonb [032]
         target_topic_constraints_jsonb [032]
```

---

## 7. Question Embeddings

```
question_embeddings
├── id uuid PK
├── question_id uuid FK→questions (CASCADE)
├── embedding_type text NOT NULL
│   (full_item | passage_only | explanation | taxonomy_summary | generation_profile)
├── embedding_text text NOT NULL
├── embedding vector(1536) NOT NULL
├── UNIQUE(question_id, embedding_type)
└── created_at

INDEX: IVFFlat on embedding (vector_cosine_ops) lists=100
       Rebuild via fn_rebuild_embedding_index() when corpus > 500 rows [030]
```

---

## 8. Ingestion Pipeline

```
question_ingestion_jobs
├── id uuid PK
├── source_file text
├── input_format text NOT NULL
│   CHECK(pdf|markdown|image|json|text|generated) [038 adds 'generated']
├── raw_input_text text
├── pass1_json jsonb           (QuestionExtract — stem, choices, correct answer)
├── pass2_json jsonb           (QuestionAnnotation — all classification FKs)
├── validation_errors_json jsonb  ([{field, message, value}])
├── review_notes text
├── llm_provider text NOT NULL
├── llm_model text NOT NULL
│
│── STATUS WORKFLOW ────────────────────────────────
├── status text NOT NULL DEFAULT 'pending'
│   CHECK(pending|extracting|annotating|draft|reviewed|
│          approved|rejected|failed)
│   [038 extended for generation: +drift_failed|conformance_failed]
│
│── GENERATION CONTEXT ─────────────────────────────
├── content_origin text DEFAULT 'official'           [038]
│   CHECK(official|generated|ai_human_revised)
├── generation_run_id uuid FK→generation_runs        [038]
├── seed_question_id uuid FK→questions               [038]
│
│── PRODUCTION LINK ────────────────────────────────
├── question_id uuid FK→questions (SET NULL)         [038]
└── created_at / updated_at
```

**Status transitions:**
```
pending → extracting → annotating → draft → reviewed → approved → (upsert to production)
                                  ↘ failed
                                  ↘ drift_failed       (generation only; preserved)
                                  ↘ conformance_failed (generation only; terminal)
```

---

## 9. Generation Lifecycle

```
generation_templates
├── id uuid PK
├── template_code text UNIQUE NOT NULL
├── question_family_key text FK→lookup_question_family
├── version int DEFAULT 1
├── is_active bool DEFAULT true
├── prompt_skeleton text NOT NULL
├── constraint_schema jsonb    ({required: [...], recommended: [...]})
├── quality_gate_threshold numeric(3,2) CHECK(0–1)
├── description text
└── created_at / updated_at

generation_runs
├── id uuid PK
├── template_id uuid FK→generation_templates
├── model_name text NOT NULL
├── model_params jsonb
├── seed_question_ids uuid[]
├── target_constraints jsonb
├── item_count int
├── status text DEFAULT 'running'
│   CHECK(running|complete|failed|cancelled)
│   [extended: +partial_complete]
├── run_notes text
└── created_at / updated_at

generated_questions
├── id uuid PK
├── run_id uuid FK→generation_runs (CASCADE)
├── question_id uuid NOT NULL FK→questions (CASCADE)
├── seed_question_id uuid FK→questions
├── generation_rank int
├── review_status text DEFAULT 'unreviewed'
│   CHECK(unreviewed|approved|rejected|needs_revision)
├── review_notes text
├── realism_score numeric(3,2) CHECK(0–1)
├── approved_by text
├── approved_at timestamptz
├── generation_params_snapshot_jsonb jsonb  [035] immutable
├── generation_model_name text             [035]
├── generation_provider text               [035]
│   CHECK(anthropic|openai|openrouter|ollama)
├── UNIQUE(run_id, question_id)
└── created_at / updated_at
```

---

## 10. Performance Tracking

```
question_performance_records
├── id uuid PK
├── question_id uuid FK→questions (CASCADE)
├── student_cohort text NOT NULL
├── source_type text DEFAULT 'practice'
│   CHECK(practice|field_test|live)
├── attempts int DEFAULT 0 CHECK(≥0)
├── correct_rate numeric(4,3) CHECK(0–1)
├── avg_time_seconds int CHECK(>0)
├── distractor_pick_rates jsonb    ({"A":0.xx,"B":0.xx,"C":0.xx,"D":0.xx})
├── irt_b_observed numeric(4,2) CHECK(-3 to 3)
├── irt_b_ci_lower / irt_b_ci_upper numeric(4,2)
├── notes text
├── recorded_at timestamptz
├── UNIQUE(question_id, student_cohort, source_type)
└── created_at
```

---

## 11. Coaching Annotations

```
lookup_coaching_annotation_type
├── key text PK
│   (syntactic_trap|key_evidence|np_cluster|clause_boundary|
│    blank_context|distractor_lure|rhetorical_move)
├── display_name text NOT NULL
├── description text
├── ui_color text
└── sort_order int

question_coaching_annotations
├── id uuid PK
├── question_id uuid FK→questions (CASCADE)
├── span_field text NOT NULL
│   CHECK(passage_text|prompt_text|paired_passage_text)
├── span_start_char int CHECK(≥0)     zero-indexed, half-open
├── span_end_char int CHECK(≥0)
├── span_sentence_index int CHECK(≥0)  fallback when char offsets stale
├── annotation_type text FK→lookup_coaching_annotation_type
├── label text NOT NULL
├── coaching_note text NOT NULL
├── show_condition text DEFAULT 'on_request'
│   CHECK(always|on_error|on_request)
├── sort_order int DEFAULT 0
└── created_at
```

---

## 12. Grammar Token Annotations

```
grammar_keys
├── id text PK
│   (subordinate_clause|subject|main_verb|relative_clause|
│    subordinating_conj|modifier)
├── label text NOT NULL
├── color text NOT NULL          (hex)
├── light_bg / mid_bg text NOT NULL
├── description text NOT NULL
├── sat_rule text NOT NULL
└── created_at

question_token_annotations
├── id uuid PK
├── question_id uuid FK→questions (CASCADE)
├── token_index int NOT NULL
├── token_text text NOT NULL
├── is_blank boolean DEFAULT false
├── grammar_tags text[] NOT NULL DEFAULT '{}'
│   (array of grammar_keys.id values)
├── UNIQUE(question_id, token_index)
└── created_at
```

---

## 13. Ontology Proposals

```
ontology_proposals
├── id uuid PK
├── lookup_table text NOT NULL    (e.g. 'lookup_question_family')
├── proposed_key text NOT NULL
├── proposed_label text
├── context_field text
├── description text
├── source_job_id uuid FK→question_ingestion_jobs (SET NULL)
├── proposal_count int DEFAULT 1 CHECK(≥1)
├── status text DEFAULT 'pending'
│   CHECK(pending|approved|rejected)
├── review_notes text
├── reviewed_by / reviewed_at
├── UNIQUE(lookup_table, proposed_key)
└── created_at / updated_at
```

---

## 14. Lookup Tables (Controlled Vocabulary)

All lookup tables share the same structure: `key text PK, display_name text NOT NULL, is_active bool, sort_order int, created_at, updated_at`. Tables added in 017+ also include a `description text` column.

| Table | Migration | FK Used By | Key Count |
|---|---|---|---|
| `lookup_question_family` | 004 | `question_classifications`, `generation_templates`, `question_generation_profiles` | 17 |
| `lookup_stimulus_mode` | 004 | `questions` | 8 |
| `lookup_stem_type` | 004 | `questions` | 12 |
| `lookup_evidence_scope` | 004 | `question_classifications` | 9 |
| `lookup_evidence_location` | 004 | `question_classifications` | 9 |
| `lookup_clue_distribution` | 004 | `question_reasoning` | 7 |
| `lookup_answer_mechanism` | 004 | `question_classifications` | 10 |
| `lookup_solver_pattern` | 004 | `question_classifications` | 13 |
| `lookup_distractor_type` | 004 | `question_options` | 14 |
| `lookup_semantic_relation` | 004 | `question_options` | 21 |
| `lookup_plausibility_source` | 004 | `question_options` | 16 |
| `lookup_generation_pattern_family` | 004 | `question_generation_profiles` | 18 |
| `lookup_syntactic_complexity` | 017+018 | `question_classifications`, `question_generation_profiles` | 16 |
| `lookup_syntactic_interruption` | 017+018 | `question_classifications`, `question_generation_profiles` | 13 |
| `lookup_evidence_distribution` | 017+018 | `question_classifications`, `question_generation_profiles` | 12 |
| `lookup_syntactic_trap` | 017+018 | `question_classifications`, `question_generation_profiles` | 21 |
| `lookup_lexical_tier` | 018 | `question_classifications`, `question_generation_profiles` | 6 |
| `lookup_rhetorical_structure` | 018 | `question_classifications`, `question_generation_profiles` | 11 |
| `lookup_noun_phrase_complexity` | 018 | `question_classifications`, `question_generation_profiles` | 8 |
| `lookup_vocabulary_profile` | 018 | `question_classifications`, `question_generation_profiles` | 7 |
| `lookup_cohesion_device` | 019 | `question_classifications`, `question_generation_profiles` | 8 |
| `lookup_epistemic_stance` | 019 | `question_classifications`, `question_generation_profiles` | 7 |
| `lookup_inference_distance` | 019 | `question_classifications`, `question_generation_profiles` | 6 |
| `lookup_transitional_logic` | 019 | `question_classifications`, `question_generation_profiles` | 10 |
| `lookup_grammar_focus` | 019+041+042 | `question_classifications`, `question_generation_profiles` | 27 |
| `lookup_distractor_construction` | 020 | `question_options`, `question_generation_profiles` | 11 |
| `lookup_passage_topic_domain` | 020 | `question_classifications`, `question_generation_profiles` | 12 |
| `lookup_argument_role` | 020 | `question_classifications`, `question_generation_profiles` | 11 |
| `lookup_prose_register` | 024 | `question_classifications`, `question_generation_profiles` | 6 |
| `lookup_prose_tone` | 024 | `question_classifications`, `question_generation_profiles` | 8 |
| `lookup_passage_source_type` | 024 | `question_classifications`, `question_generation_profiles` | 7 |
| `lookup_craft_signal` | 024 | (app-layer validated; referenced via `craft_signals_array`) | 8 |
| `lookup_domain` | 025 | `question_classifications`, `lookup_skill_family`, `question_generation_profiles` | 4 |
| `lookup_skill_family` | 025 | `question_classifications`, `question_generation_profiles` | 11 |
| `lookup_passage_type` | 025 | `question_classifications`, `question_generation_profiles` | 5 |
| `lookup_evidence_mode` | 025 | `question_classifications` | 3 |
| `lookup_reading_scope` | 025 | `question_classifications` | 2 |
| `lookup_reasoning_demand` | 025 | `question_classifications` | 3 |
| `lookup_grammar_role` | 025 | `question_classifications` | 7 |
| `lookup_hidden_clue_type` | 025 | `question_reasoning` | 8 |
| `lookup_distractor_subtype` | 025 | `question_options` | 7 |
| `lookup_coaching_annotation_type` | 034 | `question_coaching_annotations` | 7 |

**Hierarchy:** `lookup_domain` → `lookup_skill_family` (domain_key FK enforces domain→skill_family pairing; cross-checked by trigger `check_skill_family_domain` [029])

---

## 15. Analytical Views

| View | Tables Joined | Purpose |
|---|---|---|
| `question_flat_export` | questions + exams + sections + modules + classifications + reasoning + generation_profiles | Full denormalized export |
| `v_question_distribution` | questions + modules + classifications | Counts by domain/family/difficulty per module |
| `v_distractor_effectiveness` | questions + classifications + options | Distractor type effectiveness by family |
| `v_embedding_coverage` | questions + modules + embeddings | Which embedding types are present/missing per question |
| `v_ingestion_pipeline_summary` | question_ingestion_jobs | Job count by status/model |
| `v_prose_complexity_profile` | questions + classifications | Aggregate syntactic/style fingerprint counts |
| `v_style_complexity_distribution` | questions + classifications | Lexical × rhetorical structure × difficulty cross-tab |
| `v_style_composition_profile` | questions + classifications | Full style fingerprint per question |
| `v_item_anatomy_profile` | questions + classifications | Blank position/evidence distribution counts |
| `v_option_anatomy_distribution` | question_options | Distractor construction/eliminability breakdown |
| `v_difficulty_calibration` | questions + classifications + performance_records | IRT estimated vs observed b comparison |
| `v_distractor_pick_analysis` | performance_records + questions + classifications | Raw distractor pick rates with context |
| `v_generation_run_summary` | generation_runs + generated_questions + generation_profiles | Per-run stats: requested/approved/avg_realism |
| `v_generation_traceability` | generated_questions + generation_runs + classifications | Snapshot targets vs actual classification (drift detection) |
| `v_coaching_panel` | questions + reasoning + classifications + coaching_annotations + coaching_annotation_type | All UI coaching data per question |
| `v_module_form_spec` | exam_module_form_targets + modules + sections + exams | Human-readable module composition spec |
| `v_duplicate_questions` | questions + exams + modules | Questions sharing same content_hash |
| `v_ontology_proposal_queue` | ontology_proposals | Pending proposals ranked by frequency |
| `v_corpus_fingerprint` (planned 042) | question_classifications + questions | Materialized: style fingerprint per family from approved official questions |

---

## 16. Database Functions & Triggers

### Functions

| Function | Returns | Purpose |
|---|---|---|
| `set_updated_at()` | trigger | Auto-stamps `updated_at` on every UPDATE across all major tables |
| `fn_set_content_hash()` | trigger | Computes SHA-256 of passage+prompt+paired_passage into `content_hash` on questions [027] |
| `check_skill_family_domain()` | trigger | Validates `skill_family_key` belongs to `domain_key` on question_classifications [029] |
| `check_gen_profile_taxonomy()` | trigger | Same validation on question_generation_profiles [029] |
| `fn_check_active_retirement_consistency()` | trigger | Blocks `is_active=true` + `retirement_status='retired'` [032] |
| `fn_compute_irt_b_v1(uuid)` | numeric(4,2) | Rubric-based IRT b from 6 classification dimensions; never written by LLM [033] |
| `fn_refresh_irt_b(uuid=NULL)` | int | Batch-recomputes b-estimates for a question or full corpus; skips empirical/manual rows [033] |
| `fn_rebuild_embedding_index(int=NULL)` | text | Rebuilds IVFFlat index with auto-computed `lists` value [030] |

### IRT B Formula (v1)

```
raw = (inference_distance × 0.30)
    + (evidence_distribution × 0.20)
    + (syntactic_complexity × 0.20)
    + (lexical_tier × 0.15)
    + (syntactic_trap × 0.10)
    + (noun_phrase_complexity × 0.05)

b = clamp( (raw − 3.125) / 2.225 × 3.0, −3.0, 3.0 )
```

---

## 17. Dropped Tables

| Table | Created | Dropped | Reason |
|---|---|---|---|
| `taxonomy_nodes` | 008 | 028 | Replaced by direct FK lookup tables |
| `taxonomy_edges` | 008 | 028 | Replaced by `lookup_skill_family.domain_key` hierarchy |
| `question_taxonomy_links` | 008 | 028 | Replaced by FK columns on `question_classifications` |

---

## 18. Key Constraints Summary

| Constraint | Table | Rule |
|---|---|---|
| `chk_source_origin_consistency` | questions | source_type ↔ content_origin must be semantically consistent [036] |
| `chk_no_generated_in_questions` | questions | `content_origin='generated'` blocked; staging-only state [036] |
| `chk_irt_b_range` | question_classifications | `irt_b_estimate BETWEEN -4 AND 4` [033] |
| `chk_clause_depth_bound` | question_classifications | `clause_depth BETWEEN 0 AND 4` [032] |
| `chk_clause_depth_range` | question_generation_profiles | `max ≥ min` when both set [026] |
| `chk_word_count_range` / `both_or_neither` | question_generation_profiles | max≥min; both or neither [032] |
| `chk_lexile_range` / `both_or_neither` | question_generation_profiles | max≥min; both or neither [032] |
| `chk_difficulty_band` | exam_modules | `CHECK(easy\|medium\|hard\|adaptive\|NULL)` [032] |
| `uq_module_sort_order_per_section` | exam_modules | sort_order unique per section [032] |
| `trg_qclass_taxonomy_check` | question_classifications | skill_family_key must belong to domain_key [029] |
| `trg_qgenprof_taxonomy_check` | question_generation_profiles | target_skill_family must belong to target_domain [029] |
| `trg_check_active_retirement` | questions | retired question cannot be is_active=true [032] |
