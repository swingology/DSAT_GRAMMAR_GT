# LLM Ingestion Conformity

How LLM responses are constrained to conform to the database ontology during the two-pass ingestion pipeline.

Last updated: 2026-04-16.

---

## Overview

Three components work in sequence to enforce ontology conformity:

```
DB lookup tables
      ↓
app/prompts/ontology_ref.py    — formats valid values as prompt context (runtime injection)
      ↓
app/prompts/pass2_annotation.py — instructs LLM: use only these values, defines output schema
      ↓
LLM response (JSON with _key fields)
      ↓
app/pipeline/validator.py      — checks every _key against DB; rejects hallucinations
```

---

## 1. `app/prompts/ontology_ref.py` — Constraint Source

**What it does:** Renders all valid lookup table values into a compact reference block that is injected into the Pass 2 system prompt at request time.

**How:** Reads `app.state.ontology` (loaded from Supabase at server startup) and formats each lookup table as:
```
field_name: value1 | value2 | value3 | ...
```

**Covers 37 lookup tables** across all migration groups:

| Migration Group | Fields |
|----------------|--------|
| Core (001–013) | `question_family_key`, `stimulus_mode_key`, `stem_type_key`, `evidence_scope_key`, `evidence_location_key`, `clue_distribution_key`, `answer_mechanism_key`, `solver_pattern_key`, `distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`, `generation_pattern_family_key` |
| Prose grammar (017) | `syntactic_complexity_key`, `syntactic_interruption_key`, `evidence_distribution_key`, `syntactic_trap_key` |
| Writing style (018) | `lexical_tier_key`, `rhetorical_structure_key`, `noun_phrase_complexity_key`, `vocabulary_profile_key` |
| Discourse (019) | `cohesion_device_key`, `epistemic_stance_key`, `inference_distance_key`, `transitional_logic_key`, `target_grammar_focus_key` |
| Item anatomy (020) | `distractor_construction_key`, `passage_topic_domain_key`, `argument_role_key` |
| Style composition (024) | `prose_register_key`, `prose_tone_key`, `passage_source_type_key`, `craft_signals_array values` |
| Consolidation (025) | `domain_key`, `skill_family_key`, `passage_type_key`, `evidence_mode_key`, `reading_scope_key`, `reasoning_demand_key`, `grammar_role_key`, `hidden_clue_type_key`, `distractor_subtype_key` |

**Key design:** Values are loaded live from the DB at startup — if the ontology evolves (new lookup values added via migration), the prompt reference updates automatically without code changes.

---

## 2. `app/prompts/pass2_annotation.py` — LLM Instructions

**What it does:** Defines the full Pass 2 system prompt template. Injects the ontology reference block from `ontology_ref.py` at `{ontology_reference}` and defines the exact JSON output schema the LLM must produce.

**Key rules enforced via prompt:**

- `"Use ONLY the allowed values listed in the ontology reference. Never invent new keys."`
- Options array must have exactly 4 items (A, B, C, D)
- Exactly one option must have `is_correct=true`
- Correct option: `distractor_type_key = "correct"`, `distractor_subtype_key = "correct"`
- `irt_b_estimate` and `irt_b_source`: always output `null` (populated from field test data, never annotation)
- `domain_key` and `skill_family_key` must be consistent (e.g., `words_in_context` belongs to `craft_and_structure`)
- `grammar_role_key`: only populate for Standard English Conventions questions
- Prose grammar/style fields describe the PASSAGE, not the stem — set to `null` for sentence-only (SEC) questions
- `hidden_clue_type_key`: use `"none"` when absent (not `null`) to make absence explicit
- `style_traits` allowlist of ~30 tags (e.g., `heavy_nominalization`, `em_dash_interruption`, `garden_path`, etc.)

**Output sections covered:**
1. `classification` — ~50 fields covering taxonomy, prose style, grammar, passage fingerprint
2. `options` — 4 entries with distractor analysis per option
3. `reasoning` — coaching summary, elimination notes, hidden clue analysis
4. `generation_profile` — ~40 `target_*` mirror fields for generation constraints

---

## 3. `app/pipeline/validator.py` — Post-Response Enforcement

**What it does:** After the LLM responds, validates every `_key` field against the actual lookup table values loaded from the DB. Any hallucinated or invalid value produces a `ValidationError` and the job status is set to `validation_failed`.

**Validation checks:**

### Pass 1 (extract) checks
- `stem` is non-empty
- `choices` has exactly keys A, B, C, D
- `correct_option_label` exists in `choices`
- `stimulus_mode_key` and `stem_type_key` are valid lookup values

### Pass 2 classification checks (28 lookup fields)
Every `_key` field in `classification` is checked against its lookup table:
- Core taxonomy: `domain_key`, `skill_family_key`, `passage_type_key`, `evidence_mode_key`, `reading_scope_key`, `reasoning_demand_key`, `grammar_role_key`, `question_family_key`, `evidence_scope_key`, `evidence_location_key`, `answer_mechanism_key`, `solver_pattern_key`
- Prose grammar: `syntactic_complexity_key`, `syntactic_interruption_key`, `evidence_distribution_key`, `syntactic_trap_key`
- Writing style: `lexical_tier_key`, `rhetorical_structure_key`, `noun_phrase_complexity_key`, `vocabulary_profile_key`
- Discourse: `cohesion_device_key`, `epistemic_stance_key`, `inference_distance_key`, `transitional_logic_key`
- Item anatomy: `passage_topic_domain_key`, `argument_role_key`
- Style: `prose_register_key`, `prose_tone_key`, `passage_source_type_key`

### Cross-field taxonomy check
- `skill_family_key` must belong to `domain_key` per the `skill_family_domain_map` (loaded from `lookup_skill_family.domain_key`)
- `target_skill_family_key` must belong to `target_domain_key` (same rule for generation profile)

### Options checks
- Exactly 4 options
- Labels exactly {A, B, C, D}
- Exactly one `is_correct=true`
- Correct option label matches `extract.correct_option_label`
- Per-option lookup validation: `distractor_type_key`, `distractor_subtype_key`, `semantic_relation_key`, `plausibility_source_key`, `distractor_construction_key`

### Reasoning checks
- `clue_distribution_key` valid
- `hidden_clue_type_key` valid

### Generation profile checks (21 lookup fields)
All `target_*_key` fields validated: `generation_pattern_family_key`, `target_domain_key`, `target_skill_family_key`, `target_passage_type_key`, `target_syntactic_complexity_key`, `target_vocabulary_profile_key`, `target_noun_phrase_complexity_key`, `target_cohesion_device_key`, `target_inference_distance_key`, `target_transitional_logic_key`, `target_grammar_focus_key`, `target_passage_topic_domain_key`, `target_epistemic_stance_key`, `target_argument_role_key`, `target_lexical_tier_key`, `target_rhetorical_structure_key`, `target_prose_register_key`, `target_prose_tone_key`, `target_passage_source_type_key`, `target_syntactic_interruption_key`, `target_syntactic_trap_key`, `target_distractor_construction_key`

---

## Job Status Flow

```
pending
  → processing (Pass 1 runs)
  → processing (Pass 2 runs)
  → validation_failed  ← any _key field not in ontology, or structural error
  → reviewed           ← validation passed, awaiting human approval
  → approved           ← human approved, written to production tables
  → rejected           ← human rejected
```

`validation_failed` jobs can be rerun via `POST /jobs/{id}/rerun` after investigating the `validation_errors_json` field on the job record.

---

## Notes

- Ontology is loaded once at server startup (`app/main.py: _load_ontology()`) into `app.state.ontology`
- If new lookup values are added via SQL migration, the server must be restarted to pick them up
- The validator only checks fields that are non-null — null values pass through (optional fields are allowed to be unset)
- `style_traits` and `craft_signals_array` are free-form arrays validated by allowlist in the prompt only (not DB-backed FK tables)
