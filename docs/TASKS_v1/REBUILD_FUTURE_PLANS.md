# REBUILD_FUTURE_PLANS.md

**Date:** 2026-04-21
**Status:** Deferred — not in scope for current alignment pass
**Trigger:** When question generation pipeline is active and needs rhetorical device / style trait targeting

---

## Plan: Full Taxonomy Reconciliation (Approach 3)

The current alignment pass (Approach 1) resolves inconsistencies and fills seed data gaps without changing the schema. This document captures the full reconciliation approach for when generation fidelity requires deeper taxonomy integration.

---

## 1. Add Rhetorical Device Lookup Table

**Source:** Taxonomy v2 Section 3.4

**New table:** `lookup_rhetorical_device`

| Key | Display Name | Sort Order |
|---|---|---|
| `concession` | Concession | 10 |
| `qualification` | Qualification | 20 |
| `exemplification` | Exemplification | 30 |
| `analogy` | Analogy | 40 |
| `hedging` | Hedging | 50 |

**Schema changes:**
- `question_classifications`: add `rhetorical_device_key text REFERENCES lookup_rhetorical_device(key)`
- `question_generation_profiles`: add `target_rhetorical_device_key text REFERENCES lookup_rhetorical_device(key)`

**Why defer:** The 5 rhetorical devices can be represented in `style_traits_jsonb` as an interim solution. A dedicated FK table adds value when the LLM generation pipeline needs to target specific rhetorical moves and verify them in the output.

---

## 2. Add Style Trait Lookup Table

**Source:** Taxonomy v2 Section 3.3

**New table:** `lookup_style_trait`

| Key | Display Name | Sort Order |
|---|---|---|
| `concise` | Concise | 10 |
| `evidence_driven` | Evidence-Driven | 20 |
| `descriptive` | Descriptive | 30 |
| `precise` | Precise | 40 |
| `restrained` | Restrained | 50 |
| `rhetorically_elevated` | Rhetorically Elevated | 60 |

**Schema changes:**
- `question_classifications`: add `style_traits_array text[]` (already exists as `craft_signals_array` pattern — can store style trait keys)
- `question_generation_profiles`: add `target_style_traits text[]` (already exists as `target_style_traits_jsonb text[]`)

**Why defer:** `style_traits_array` already exists on classifications; `target_style_traits_jsonb` already exists on generation profiles. Adding a FK lookup table makes validation stricter but the array fields already support free-text trait storage. Defer until we have enough ingested questions to know which traits are consistently used.

---

## 3. Restructure Distractor Taxonomy into 4-Family Model

**Current state:** 6 independent lookup tables (`lookup_distractor_type`, `lookup_distractor_subtype`, `lookup_distractor_construction`, `lookup_semantic_relation`, `lookup_plausibility_source`, `lookup_eliminability`)

**Proposed restructure:** Add `parent_type_key` FK to `lookup_distractor_subtype` pointing to `lookup_distractor_type`, creating explicit parent-child relationships matching the taxonomy v2 Section 4 structure.

```sql
ALTER TABLE lookup_distractor_subtype
    ADD COLUMN parent_type_key text REFERENCES lookup_distractor_type(key);
```

**Why defer:** The seed data addendum already aligns subtypes with their parent types. The FK relationship is nice-to-have for DB-level validation but the app layer can enforce the mapping. Defer until distractor analysis is a bottleneck in generation quality.

---

## 4. Grammar Focus Subcategory Depth

**Current state:** 29 `grammar_focus_key` values with 7 `grammar_role_key` parents.

**Potential extension:** Add a `grammar_subfocus` level for keys where multiple SAT-distinct patterns exist:

- `subject_verb_agreement` → subfocuses: `simple_agreement`, `intervening_phrase`, `compound_subject`, `inverted_order`, `indefinite_pronoun`
- `punctuation_comma` → subfocuses: `nonrestrictive_clause`, `introductory_element`, `coordinate_adjectives`, `series_separator`, `independent_clause_joiner`

**Why defer:** The 29 keys are sufficient for Pass 2 annotation. Subfocuses add value for coaching explanations (where the specific pattern drives the tutoring logic) but not for the initial classification. Defer until the coaching annotation pipeline needs this granularity.

---

## 5. Passage-Level Register Constraints

**Current state:** `prose_register_key` and `prose_tone_key` on `question_classifications` are per-question labels.

**Potential extension:** Add a `passage_register_profile` table that stores the dominant register, tone, and expected tense convention for a passage, so that questions within the same passage inherit consistent style constraints.

**Why defer:** The `prose_register_key` FK on each question is sufficient for per-question annotation. Passage-level profiles add value when generating multi-question sets from a single passage. Defer until passage-level generation is in scope.

---

## 6. College Board Test Pattern Library

**Potential extension:** After ingesting 500+ official questions, build a `v_corpus_pattern_library` materialized view that aggregates:
- Most common `grammar_focus_key` × `syntactic_trap_key` × `distractor_type_key` bundles
- Per-module difficulty distribution
- Distractor slot fingerprint per question family

**Why defer:** Requires substantial ingestion volume first. The `v_corpus_fingerprint` view in M-020 is the starting point; this extends it with cross-dimensional pattern mining.

---

## Trigger Criteria

Implement each plan when:
1. **Rhetorical device table**: When generation pipeline needs to target specific rhetorical moves and verify them
2. **Style trait table**: When enough questions are ingested to validate which traits are consistently used
3. **Distractor parent-child FK**: When distractor analysis becomes a generation quality bottleneck
4. **Grammar subfocus**: When coaching annotations need sub-pattern specificity
5. **Passage register profile**: When passage-level multi-question generation is in scope
6. **Pattern library**: When 500+ official questions are ingested and cross-dimensional analysis is needed