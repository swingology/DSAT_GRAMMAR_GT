# Inconsistent Taxonomy Keys in Official Question Annotations

Extracted from the DB (`question_annotations.annotation_jsonb`) for all 569
official questions. Each section lists non-standard values found alongside the
canonical approved value from `rules_agent_dsat_grammar_ingestion_generation_v7.md`.

---

## `grammar_focus_key` — Non-Standard Values

Valid approved keys are defined in D.2 of the grammar rules file.

| Non-Standard Value | Occurrences | Canonical Replacement | Notes |
|---|---|---|---|
| `colon_introducing_explanation` | 1 | `colon_dash_use` | Sub-pattern of colon use; no standalone key in D.2.6 |
| `colon_usage` | 1 | `colon_dash_use` | Alias; D.2.6 uses `colon_dash_use` |
| `precision` | 1 | `precision_word_choice` | Truncated key; D.2.8 uses `precision_word_choice` |
| `rhetorical_synthesis` | 1 | *(remove from grammar_focus_key)* | This is a `skill_family_key`, not a `grammar_focus_key` |
| `similarity_emphasis` | 1 | `emphasis_meaning_shifts` | Non-standard alias; D.2.8 uses `emphasis_meaning_shifts` |
| `subject_aux_inversion_and_punctuation` | 1 | `sentence_boundary` | Over-specific; no such key in D.2; use `sentence_boundary` |
| `synthesis_of_information` | 2 | *(remove from grammar_focus_key)* | Belongs as a `skill_family_key` for Expression of Ideas, not a `grammar_focus_key` |
| `synthesize_information` | 1 | *(remove from grammar_focus_key)* | Same issue as `synthesis_of_information` |
| `verb_tense` | 2 | `verb_tense_consistency` | Truncated key; D.2.4 uses `verb_tense_consistency` |
| `word_choice` | 2 | `precision_word_choice` | Vague alias; D.2.8 uses `precision_word_choice` |

**Standard keys found (no action needed):** `appositive_punctuation`,
`colon_dash_use`, `comma_splice`, `conjunctive_adverb_usage`,
`data_interpretation_claims`, `emphasis_meaning_shifts`,
`end_punctuation_question_statement`, `logical_predication`,
`logical_relationships`, `possessive_contraction`, `precision_word_choice`,
`preposition_idiom`, `pronoun_antecedent_agreement`, `pronoun_case`,
`punctuation_comma`, `register_style_consistency`, `relative_pronouns`,
`run_on_sentence`, `semicolon_use`, `sentence_boundary`, `sentence_fragment`,
`subject_verb_agreement`, `transition_logic`, `unnecessary_internal_punctuation`,
`verb_form`, `verb_tense_consistency`

---

## `skill_family_key` — Non-Standard Values

Valid approved keys follow the College Board skill names. The canonical
snake_case form is used throughout the rules file.

### Standard English Conventions domain

| Non-Standard Value | Occurrences | Canonical Replacement | Notes |
|---|---|---|---|
| `agreement` | 8 | `Form, Structure, and Sense` | Too granular; not a College Board skill family name |
| `Agreement` | 1 | `Form, Structure, and Sense` | Same issue, wrong casing |
| `expression_of_ideas` | 63 | `Expression of Ideas` | Wrong casing (snake_case vs Title Case) |
| `Expression of Ideas` | 1 | *(correct — but misrouted)* | SEC questions in Expression of Ideas should be `transition_logic` or `logical_relationships` under the right skill family |
| `punctuation` | 1 | `Boundaries` | Non-standard; CB calls this skill family `Boundaries` |
| `Punctuation` | 2 | `Boundaries` | Same — Title Case but wrong name |
| `sentence_boundaries` | 1 | `Boundaries` | Plural form; CB uses `Boundaries` |
| `standard_english_conventions` | 4 | *(needs subdomain)* | Too broad; should be `Boundaries` or `Form, Structure, and Sense` based on `grammar_focus_key` |
| `verb_tense` | 1 | `Form, Structure, and Sense` | Not a valid skill family name; this is a `grammar_focus_key` value |

### Expression of Ideas domain

| Non-Standard Value | Occurrences | Canonical Replacement | Notes |
|---|---|---|---|
| `Rhetorical Synthesis` | 2 | `rhetorical_synthesis` | Wrong casing (Title Case vs snake_case) |
| `synthesis_of_information` | 1 | `rhetorical_synthesis` | Non-standard alias |

### Null domain (missing `domain` field)

| Non-Standard Value | Occurrences | Likely Domain | Notes |
|---|---|---|---|
| `Command of Evidence` | 2 | `Information and Ideas` | Title Case; should be `command_of_evidence` |
| `command_of_evidence_quantitative` | 2 | `Information and Ideas` | Over-specific; use `command_of_evidence` |
| `Expression of Ideas` | 2 | `Expression of Ideas` | Missing domain; skill family is correct Title Case |
| `Inferences` | 6 | `Information and Ideas` | Title Case; should be `inferences` |
| `Transitions` | 3 | `Expression of Ideas` | Not a CB skill family name; use `rhetorical_synthesis` or reclassify as `transition_logic` under `grammar_focus_key` |
| `Words in Context` | 12 | `Craft and Structure` | Title Case; should be `words_in_context` |

### Information and Ideas domain — over-specific keys

| Non-Standard Value | Occurrences | Canonical Replacement | Notes |
|---|---|---|---|
| `command_of_evidence_quantitative` | 38 | `command_of_evidence` | CB uses one skill family; quantitative/textual distinction lives in `stem_type_key` |
| `command_of_evidence_textual` | 41 | `command_of_evidence` | Same — use `command_of_evidence` |

---

## Summary

| Category | Distinct Non-Standard Values | Total Affected Rows |
|---|---|---|
| `grammar_focus_key` | 10 | ~13 |
| `skill_family_key` casing inconsistency | 8 | ~76 |
| `skill_family_key` wrong name | 10 | ~17 |
| `skill_family_key` over-specific | 2 | ~79 |
| Missing `domain` with non-null sfk | 6 | ~25 |

## Recommended Fix

Run a one-time migration or UPDATE script against `question_annotations.annotation_jsonb`
using `jsonb_set` to patch the non-standard values. Alternatively, add a
normalization step to the ingestion pipeline so new annotations are validated
against `VALID_GRAMMAR_FOCUS_KEYS` and `VALID_SKILL_FAMILY_KEYS` before save.
The `build_calibration_set.py` script already does this validation and flags
affected questions — it can be extended to emit an UPDATE script.
