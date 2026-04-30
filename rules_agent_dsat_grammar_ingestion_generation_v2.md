# rules_agent_v2.md — DSAT Grammar Ingestion and Generation Rules

## Purpose

This document is the operational rule file for an agent that ingests, classifies, validates, and generates Digital SAT Reading & Writing questions, with special focus on Standard English Conventions and grammar-adjacent Expression of Ideas.

The agent must use this document to produce consistent structured outputs for:

- question classification
- option-level distractor analysis
- grammar rule identification
- generation templates
- review/amendment proposals

The agent must not invent new taxonomy keys unless explicitly using the amendment process.

---

## 1. Operating Principles

### 1.1 Separate the tasks
For every question, separate:

1. what the item tests
2. how the item is structured
3. what rule or reasoning mechanism solves it
4. why the correct answer is correct
5. why each wrong option is tempting
6. why each wrong option is wrong
7. what pattern should be used to generate a similar item

### 1.2 Do not write directly to the database
The agent must output structured JSON or markdown records for validation. A deterministic backend validator should check all keys before insertion.

### 1.3 Use controlled keys
The agent must use only approved lookup keys. If no key fits, it must propose an amendment instead of inventing a new production key.

### 1.4 Meaning over surface form

When grammar and meaning overlap, classify the item by the main reason the correct answer is required. A sentence can be grammatically possible but logically invalid.

### 1.5 Official SAT alignment

For Standard English Conventions, classify according to:

- sentence boundaries
- form, structure, and sense
- grammar role
- grammar focus
- syntactic trap
- distractor mechanics

---

## 2. Required Output Shape

Every item annotation must produce these sections:

```json
{
  "question": {},
  "classification": {},
  "options": [],
  "reasoning": {},
  "generation_profile": {},
  "review": {}
}
```

### 2.1 Formal schemas for undocumented sections

The following schemas formally define fields that appear in examples but were previously undocumented.

#### `reasoning` section schema

```json
{
  "primary_rule": "The grammar rule that selects the correct answer.",
  "trap_mechanism": "How the syntactic trap misleads test-takers.",
  "correct_answer_reasoning": "Step-by-step justification for the correct option.",
  "distractor_analysis_summary": "One-sentence summary of why the three wrong options fail.",
  "similar_items": [
    {
      "pattern": "sentence template describing the structural pattern",
      "focus_key": "grammar_focus_key",
      "trap_key": "syntactic_trap_key"
    }
  ]
}
```

#### `generation_profile` section schema

```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "high",
  "target_frequency_band": "very_high",
  "target_distractor_pattern": [
    "one nearest-noun plural verb distractor",
    "one plural auxiliary distractor",
    "one unnecessary progressive distractor"
  ],
  "passage_template": "The [singular collective noun] of [plural noun], [relative clause], ______ [role/action].",
  "generation_timestamp": "2026-04-22T00:00:00Z",
  "model_version": "rules_agent_v2.0"
}
```

#### `review` section schema

```json
{
  "annotation_confidence": 0.95,
  "needs_human_review": false,
  "review_notes": "Any ambiguity or concern about the classification."
}
```

---

## 3. Question Fields
```json
{
  "source_exam": "PT4",
  "source_section": "RW",
  "source_module": "M1",
  "source_question_number": 1,
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text",
  "prompt_text": "...",
  "passage_text": null,
  "paired_passage_text": null,
  "notes_bullets": [],
  "table_data": null,
  "graph_data": null,
  "correct_option_label": "B",
  "explanation_short": "...",
  "explanation_full": "...",
  "evidence_span_text": "..."
}
```

### 3.1 stimulus_mode_key values
- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `notes_bullets`
- `poem`

### 3.2 stem_type_key values
- `complete_the_text`
- `choose_main_idea`
- `choose_main_purpose`
- `choose_structure_description`
- `choose_sentence_function`
- `choose_likely_response`
- `choose_best_support`
- `choose_best_quote`
- `choose_best_completion_from_data`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`

### 3.3 Approved values for undocumented fields

Fields appearing in JSON examples that require controlled vocabularies:

| Field | Approved values |
| --- | --- |
| `answer_mechanism_key` | `rule_application`, `pattern_matching`, `evidence_location`, `inference`, `data_synthesis` |
| `solver_pattern_key` | `apply_grammar_rule_directly`, `locate_error_zone`, `compare_register`, `evaluate_transition`, `synthesize_notes`, `eliminate_by_boundary` |
| `semantic_relation_key` | `nearest_noun_agreement`, `comma_splice`, `boundary_not_closed`, `boundary_overly_strong`, `wrong_boundary_type`, `correct_agreement`, `correct_boundary`, `unnecessary_auxiliary`, `tense_mismatch`, `modifier_misplaced`, `pronoun_ambiguous`, `parallel_broken`, `idiom_violation` |
| `evidence_scope_key` | `sentence`, `paragraph`, `passage`, `paired_passage`, `table`, `graph`, `notes` |
| `evidence_location_key` | `main_clause`, `subordinate_clause`, `surrounding_sentence`, `opening_sentence`, `closing_sentence`, `transition_zone`, `data_zone`, `entire_passage` |
| `distractor_strength` | `low`, `medium`, `high` |
| `difficulty_overall`, `difficulty_reading`, `difficulty_grammar`, `difficulty_inference`, `difficulty_vocab` | `low`, `medium`, `high` |
| `skill_family` | `Sentence Boundaries`, `Form, Structure, and Sense`, `Agreement`, `Punctuation`, `Transitions`, `Rhetorical Synthesis`, `Craft and Structure` |
| `subskill` | Free-text describing the specific skill within the family. Examples: `sentence boundary with interruption`, `subject-verb agreement with intervening noun`, `comma mechanics in compound sentences`. Use the most specific description possible. |
| `topic_broad` | `science`, `history`, `literature`, `social_studies`, `arts`, `economics`, `technology`, `environment` |
| `topic_fine` | Free-text subtopic under `topic_broad`. Examples: `marine biology`, `ancient civilizations`, `modern poetry`, `labor economics`. |

---

## 4. Classification Fields

```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Sentence Boundaries",
  "subskill": "sentence boundary with interruption",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "sentence_boundary",
  "grammar_focus_key": "sentence_boundary",
  "secondary_grammar_focus_keys": [],
  "syntactic_trap_key": "interruption_breaks_subject_verb",
  "evidence_scope_key": "sentence",
  "evidence_location_key": "surrounding_sentence",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "topic_broad": "history",
  "topic_fine": "sports history",
  "reading_scope": "sentence-level",
  "reasoning_demand": "rule application",
  "register": "neutral informational",
  "tone": "objective",
  "difficulty_overall": "medium",
  "difficulty_reading": "low",
  "difficulty_grammar": "high",
  "difficulty_inference": "low",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "disambiguation_rule_applied": "sentence_boundary > punctuation",
  "classification_rationale": "The correct option creates a valid sentence boundary after an interruption."
}
```

---

## 5. Grammar Role Keys

Use `grammar_role_key` only when the question is Standard English Conventions or grammar-adjacent.

Approved keys:

- `sentence_boundary`
- `agreement`
- `verb_form`
- `modifier`
- `punctuation`
- `parallel_structure`
- `pronoun`
- `expression_of_ideas`

### 5.1 When to use `sentence_boundary`

Use for:

- fragments
- run-ons
- comma splices
- punctuation required to divide sentence units
- boundary problems involving periods, semicolons, commas, or dashes

### 5.2 When to use `agreement`

Use for:

- subject-verb agreement
- pronoun-antecedent agreement
- countability and number agreement
- determiners/articles where noun number or specificity is the central issue

### 5.3 When to use `verb_form`

Use for:

- tense consistency
- finite vs nonfinite verbs
- gerunds and infinitives
- voice
- mood and conditional logic
- scientific present / general truth

### 5.4 When to use `modifier`

Use for:

- dangling modifiers
- misplaced modifiers
- modifier scope
- comparative structures
- logical predication when subject-predicate compatibility is central

### 5.5 When to use `punctuation`

Use for:

- comma mechanics
- semicolon mechanics
- colon/dash mechanics
- apostrophes
- appositives
- quotation punctuation
- hyphens

### 5.6 When to use `parallel_structure`

Use for:

- parallel lists
- correlative conjunctions
- comparison structures when form symmetry is primary
- elliptical constructions

### 5.7 When to use `pronoun`

Use for:

- pronoun case
- pronoun clarity
- ambiguous pronoun reference

### 5.8 When to use `expression_of_ideas`

Use only when the question is grammar-adjacent but primarily about:

- concision
- register
- transition logic
- precision of expression
- data claim accuracy
- rhetorical effectiveness

If the question is officially an Expression of Ideas question, do not force it into SEC just because grammar-like terminology appears.

**Clarification:** For Expression of Ideas questions that are genuinely grammar-adjacent (e.g., a transition question where punctuation mechanics are relevant), `grammar_role_key` may be set to `expression_of_ideas`. For Expression of Ideas questions with no grammar relevance, `grammar_role_key` must be `null` or omitted.

---

## 6. Grammar Focus Keys

Use the most specific applicable `grammar_focus_key`.

### 6.1 Sentence boundary focus keys

- `sentence_fragment`
- `comma_splice`
- `run_on_sentence`
- `sentence_boundary`

### 6.2 Agreement focus keys

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`
- `affirmative_agreement`

### 6.3 Pronoun focus keys

- `pronoun_case`
- `pronoun_clarity`

### 6.4 Verb form focus keys

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation`

### 6.5 Modifier focus keys

- `modifier_placement`
- `comparative_structures`
- `logical_predication`
- `relative_pronouns`

### 6.6 Punctuation focus keys

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`

### 6.7 Parallel structure focus keys

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

### 6.8 Expression of Ideas focus keys

- `redundancy_concision`
- `precision_word_choice`
- `register_style_consistency`
- `logical_relationships`
- `emphasis_meaning_shifts`
- `data_interpretation_claims`
- `transition_logic`

---

## 7. Disambiguation Rules

Apply these priority rules whenever multiple labels seem possible.

1. `sentence_boundary` > general `punctuation`
2. `logical_predication` > `modifier_placement`, `comparative_structures`, `parallel_structure`, `conjunction_usage`
3. `transition_logic` > `conjunction_usage`, `parallel_structure`
4. `conjunctive_adverb_usage` > general `punctuation`, `conjunction_usage`
5. `negation` > `logical_predication`, `parallel_structure`, `modifier_placement`, `verb_form`
6. `pronoun_case` > `pronoun_antecedent_agreement`
7. `pronoun_clarity` > `pronoun_antecedent_agreement`
8. `comparative_structures` > `parallel_structure`, `modifier_placement`
9. `voice_active_passive` > general `verb_form`
10. `noun_countability` > `subject_verb_agreement`
11. `relative_pronouns` > `modifier_placement`
12. `possessive_contraction` > `apostrophe_use`
13. `hyphen_usage` > general `punctuation`, `modifier_placement`
14. `preposition_idiom` or idiom-like focus > general `conjunction_usage`

Always write the selected rule in `disambiguation_rule_applied` if a conflict was resolved.

---

## 8. Decision Tree for Grammar Annotation

### Step 1: Is this Standard English Conventions?

If the answer is chosen because of grammar, punctuation, sentence structure, or usage, classify as `conventions_grammar`.

If the answer is chosen because of transition logic, note synthesis, concision, or rhetorical goal, classify under Expression of Ideas rather than SEC.

### Step 2: Is the issue a sentence boundary?

Use sentence-boundary keys if the item tests whether sentence units are correctly joined or separated.

Examples:

- fragment
- comma splice
- run-on
- period vs semicolon vs comma

### Step 3: Is the issue punctuation mechanics?

Use the specific punctuation focus:

- comma → `punctuation_comma`
- semicolon → `semicolon_use`
- colon/dash → `colon_dash_use`
- apostrophe → `apostrophe_use`
- conjunctive adverb punctuation → `conjunctive_adverb_usage`
- appositive punctuation → `appositive_punctuation`

### Step 4: Is the issue agreement?

Use:

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`

### Step 5: Is the issue verb form?

Use:

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation`

### Step 6: Is the issue modifier logic?

Use:

- `modifier_placement`
- `comparative_structures`
- `logical_predication`
- `relative_pronouns`

### Step 7: Is the issue pronoun-specific?

Use:

- `pronoun_case`
- `pronoun_clarity`
- `pronoun_antecedent_agreement`

### Step 8: Is the issue parallel or idiomatic structure?

Use:

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

### Step 9: If multiple rules apply

Choose the primary rule that eliminates the most wrong options. Store other applicable rules in `secondary_grammar_focus_keys`.

---

## 9. Syntactic Trap Keys

Use `syntactic_trap_key` to describe the difficulty mechanism, not the rule being tested.

Approved keys:

- `none`
- `nearest_noun_attraction`
- `garden_path`
- `early_clause_anchor`
- `nominalization_obscures_subject`
- `interruption_breaks_subject_verb`
- `long_distance_dependency`
- `pronoun_ambiguity`
- `scope_of_negation`
- `modifier_attachment_ambiguity`
- `presupposition_trap`
- `temporal_sequence_ambiguity`
- `multiple`

### Example

A question can have:

- `grammar_focus_key`: `subject_verb_agreement`
- `syntactic_trap_key`: `nearest_noun_attraction`

That means the rule is agreement, but the trap is the nearby plural noun.

---

## 10. Option-Level Analysis Rules

Each option must include:

```json
{
  "option_label": "A",
  "option_text": "...",
  "is_correct": false,
  "option_role": "distractor",
  "distractor_type_key": "punctuation_error",
  "semantic_relation_key": "boundary_not_closed",
  "plausibility_source_key": "punctuation_style_bias",
  "option_error_focus_key": "sentence_boundary",
  "why_plausible": "The dash punctuation looks sophisticated.",
  "why_wrong": "It fails to create a valid sentence boundary.",
  "grammar_fit": "no",
  "tone_match": "yes",
  "precision_score": 1
}
```

### 10.1 option_error_focus_key

For grammar items, every wrong option should point to the specific grammar focus key that explains its error when possible.

Examples:

- wrong apostrophe → `apostrophe_use`
- wrong tense → `verb_tense_consistency`
- wrong semicolon → `semicolon_use`
- subject-verb mismatch → `subject_verb_agreement`
- dangling modifier → `modifier_placement`

### 10.2 Distractor type keys

**For distractors (wrong options):**

- `semantic_imprecision`
- `logical_mismatch`
- `scope_error`
- `tone_mismatch`
- `grammar_error`
- `punctuation_error`
- `transition_mismatch`
- `data_misread`
- `goal_mismatch`
- `partially_supported`
- `overstatement`
- `understatement`
- `rhetorical_irrelevance`

**For the correct option:**

- `correct`

The value `correct` is reserved for the single correct option and is not a distractor type.

### 10.3 Grammar-specific plausibility sources

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`

### 10.4 precision_score scale

| Value | Meaning                                                                                                                                                      |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `1`   | Incorrect option. Contains a clear grammar error or fails the tested rule.                                                                                   |
| `2`   | Partially acceptable but inferior. Grammatically valid in isolation but less effective than the correct answer (e.g., a period where a semicolon is better). |
| `3`   | Correct option. Fully satisfies the tested rule with no compromise.                                                                                          |

Only the correct option may have `precision_score: 3`. Distractors must have `precision_score: 1` or, in rare cases, `precision_score: 2`.

### 10.5 grammar_fit and tone_match semantics

| Field         | `yes`                                                                                   | `no`                                                                                        |
| ------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `grammar_fit` | The option is grammatically possible in some context, even if it fails the tested rule. | The option contains a clear grammar error that makes it impossible in any standard context. |
| `tone_match`  | The option maintains the formal academic register of the passage.                       | The option introduces slang, contractions, colloquialisms, or a register shift.             |

---

## 11. No-Change and Original-Text Rule

Some grammar questions have the original text as the correct answer.

The agent must not assume an error exists.

Add these fields when applicable:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

If the original wording is correct, explain why no correction is needed.

---

## 12. Multi-Error Rule

Some questions contain multiple possible error types across choices.

The agent must:

1. classify the primary tested rule in `grammar_focus_key`
2. store secondary rules in `secondary_grammar_focus_keys`
3. store option-specific errors in `option_error_focus_key`
4. note ambiguity in `review.review_notes`

Do not label the whole question by a distractor-only error unless that error is the main tested rule.

---

## 13. Passage-Level Tense/Register Rule

For verb-tense questions, determine passage-level tense expectations.

### 13.1 Tense register keys

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`

### 13.2 Expected patterns

- narrative/literary passages usually use past tense
- scientific facts use simple present
- historical accounts use past tense
- study procedures use past tense
- established findings often use present tense
- past perfect is used for events completed before another past event

For tense questions, include:

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

---

## 14. Generation Rules

When generating a grammar item, the agent must specify:

```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "target_distractor_pattern": [
    "one correct singular verb",
    "one nearest-noun plural distractor",
    "one tense-shift distractor",
    "one formal-sounding but wrong auxiliary distractor"
  ]
}
```

### 14.1 Generation must include distractor design

Do not generate four random options. Each distractor must have a reason:

- rule violation
- plausible surface attraction
- common student error
- relation to correct answer

### 14.2 Generation must match SAT style

Generated items should be:

- concise
- formal or neutral academic
- self-contained
- evidence-based
- not trivia-dependent
- one correct answer only

### 14.3 Generation must respect frequency

Prioritize high-frequency rules in practice sets:

- punctuation comma
- subject-verb agreement
- verb tense consistency
- semicolon use
- apostrophe use
- sentence boundary
- appositive punctuation
- relative pronouns

Use very-low-frequency rules like `affirmative_agreement` and `negation` sparingly.

---

## 15. Amendment Process

If the agent encounters a question that does not fit existing keys, it must output:

```json
{
  "amendment_proposal": {
    "proposed_key": "...",
    "proposed_parent_role_key": "...",
    "reason": "...",
    "evidence_text": "...",
    "status": "proposed",
    "frequency_estimate": "very_low | low | medium | high | very_high",
    "example_count": 0
  }
}
```

Do not insert proposed keys into production records until reviewed.

**Note:** `frequency_estimate` predicts how often this pattern appears on official SATs. `example_count` tracks how many observed items support the proposal. Both fields are required for the proposal to be considered complete.

---

## 16. Review Flags

Set `needs_human_review` to true when:

- more than one grammar focus seems equally plausible
- the question tests grammar and rhetoric at the same time
- option text is incomplete or extracted poorly
- quote-selection options are missing exact quotation text
- no existing grammar focus key fits
- the original text may be correct but uncertain

Example:

```json
{
  "review": {
    "annotation_confidence": 0.78,
    "needs_human_review": true,
    "review_notes": "Could be appositive punctuation or colon_dash_use; chose colon_dash_use because the colon introduces an explanation after an independent clause."
  }
}
```

---

## 17. Schema Guardrails and Enforcement Rules

The following rules are mandatory. They ensure LLM ingestion output is structurally complete, validator-safe, and database-compatible.

### 17.1 `grammar_role_key` → `grammar_focus_key` mapping must be enforced

The agent must never emit a `grammar_focus_key` that does not belong to the declared `grammar_role_key`.

Approved mapping:

| `grammar_role_key`    | Allowed `grammar_focus_key` values                                                                                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sentence_boundary`   | `sentence_fragment`, `comma_splice`, `run_on_sentence`, `sentence_boundary`                                                                                                                       |
| `agreement`           | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`, `determiners_articles`, `affirmative_agreement`                                                                    |
| `verb_form`           | `verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation`                                                                                                                         |
| `modifier`            | `modifier_placement`, `comparative_structures`, `logical_predication`, `relative_pronouns`                                                                                                        |
| `punctuation`         | `punctuation_comma`, `colon_dash_use`, `semicolon_use`, `conjunctive_adverb_usage`, `apostrophe_use`, `possessive_contraction`, `appositive_punctuation`, `hyphen_usage`, `quotation_punctuation` |
| `parallel_structure`  | `parallel_structure`, `elliptical_constructions`, `conjunction_usage`                                                                                                                             |
| `pronoun`             | `pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement`                                                                                                                                 |
| `expression_of_ideas` | `redundancy_concision`, `precision_word_choice`, `register_style_consistency`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `transition_logic`               |

If the agent cannot map a focus key to its role, it must propose an amendment.

### 17.2 `rule_domain` separation (Standard English Conventions vs Expression of Ideas)

Do not classify an Expression of Ideas question under `grammar_role_key` or `grammar_focus_key` unless it is grammar-adjacent.

Use this triage:

| Official SAT domain          | `question_family_key`   | `grammar_role_key` usage                                  |
| ---------------------------- | ----------------------- | --------------------------------------------------------- |
| Standard English Conventions | `conventions_grammar`   | Required                                                  |
| Expression of Ideas          | `expression_of_ideas`   | Optional; only if a grammar pattern is genuinely adjacent |
| Craft and Structure          | `craft_and_structure`   | Forbidden                                                 |
| Information and Ideas        | `information_and_ideas` | Forbidden                                                 |

If a question tests transition logic, concision, register, rhetorical synthesis, or data-claim accuracy, classify it under Expression of Ideas. Do not force it into SEC.

### 17.3 `secondary_grammar_focus_keys` must be populated when multiple rules apply

When more than one grammar concept is present across the options, the agent must:

1. Identify the single primary rule that eliminates the most wrong options.
2. Store that primary rule in `grammar_focus_key`.
3. Store every other applicable rule in `secondary_grammar_focus_keys` as an array of valid focus keys.
4. For each wrong option, store the specific error rule in `option_error_focus_key`.

The agent must not leave `secondary_grammar_focus_keys` as an empty array when a secondary rule is visibly present.

### 17.4 Option-level error keys must be grammar-specific

For every wrong option in a Standard English Conventions question, the agent must populate `option_error_focus_key` with a key from the approved `grammar_focus_key` list.

Examples of required specificity:

| Wrong option surface error | Forbidden general label | Required `option_error_focus_key` |
| -------------------------- | ----------------------- | --------------------------------- |
| Wrong semicolon            | `punctuation_error`     | `semicolon_use`                   |
| Wrong apostrophe           | `punctuation_error`     | `apostrophe_use`                  |
| Wrong tense                | `grammar_error`         | `verb_tense_consistency`          |
| Wrong relative clause      | `grammar_error`         | `relative_pronouns`               |
| Comma splice               | `grammar_error`         | `comma_splice`                    |
| Dangling modifier          | `grammar_error`         | `modifier_placement`              |

If no specific key fits, use the amendment process.

### 17.5 No-Change tracking is mandatory when original text is an option

When the original passage wording appears as one of the four options, the agent must populate:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

If the original text is correct, the explanation must state explicitly why no change is needed. The agent must not assume an error exists.

### 17.6 Passage-level tense/register metadata must be populated for verb-form questions

For every question where `grammar_role_key` is `verb_form` or `grammar_focus_key` is one of `verb_tense_consistency`, `verb_form`, `voice_active_passive`, the agent must output:

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

Allowed values for `passage_tense_register_key`:

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`

Allowed values for `expected_tense_key`:

- `simple_present`
- `simple_past`
- `present_perfect`
- `past_perfect`
- `future`
- `conditional`
- `subjunctive`
- `imperative`

If the agent cannot determine the register, set `needs_human_review` to `true`.

### 17.7 Syntactic trap keys must include intensity for generation profiles

For ingestion, populate `syntactic_trap_key` with an approved key from section 9.

For generation profiles, also populate:

```json
{
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "high"
}
```

Allowed values for `syntactic_trap_intensity`:

- `low`
- `medium`
- `high`

The intensity reflects how strongly the trap competes with the correct answer. A singular subject next to a plural noun is `high` intensity; a short garden-path clause is `medium`; a straightforward appositive error with no nearby distractor is `low`.

### 17.8 `disambiguation_rule_applied` must be explicit

Whenever the agent resolves a conflict between two or more plausible grammar labels, it must record:

```json
{
  "disambiguation_rule_applied": "conjunctive_adverb_usage > general punctuation",
  "classification_rationale": "The semicolon is required because a conjunctive adverb follows it."
}
```

The value must quote the exact priority rule from section 7. If no rule from section 7 applies, set `needs_human_review` to `true`.

### 17.9 Amendment proposals must include parent role and evidence

When the agent proposes a new key, the output must contain:

```json
{
  "amendment_proposal": {
    "proposed_key": "...",
    "proposed_parent_role_key": "...",
    "reason": "...",
    "evidence_text": "...",
    "status": "proposed",
    "frequency_estimate": "...",
    "example_count": 0
  }
}
```

The `proposed_parent_role_key` must be an existing `grammar_role_key` or a new role proposal with justification. The `evidence_text` must quote the exact item text that triggered the proposal.

### 17.10 Frequency data must guide generation

When generating practice items, the agent must respect SAT frequency bands:

| Frequency band | Grammar focus keys                                                                                                |
| -------------- | ----------------------------------------------------------------------------------------------------------------- |
| `very_high`    | `punctuation_comma`, `subject_verb_agreement`                                                                     |
| `high`         | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation`        |
| `medium`       | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure` |
| `low`          | `voice_active_passive`, `logical_predication`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation`  |
| `very_low`     | `affirmative_agreement`, `negation`, `noun_countability`, `determiners_articles`, `elliptical_constructions`      |

The generation profile must include:

```json
{
  "target_frequency_band": "high",
  "justification": "Module needs more semicolon questions based on current mix."
}
```

The agent must not generate a `very_low` frequency item unless explicitly instructed to fill a niche gap.

### 17.11 Option text format rules

For generated items, option text must follow one of these formats:

1. **Fill-in-blank format** (default for `complete_the_text`): Options contain only the word or phrase that fills the blank.
   
   - Example: options are `"play"`, `"have played"`, `"plays"`, `"is playing"`
   - The passage contains `"______"` at the blank location.

2. **Full-replacement format** (for `choose_best_grammar_revision`): Options contain the full revised sentence or clause.
   
   - Example: options are `"The colony plays..."`, `"The colony play..."`
   - The stem must explicitly instruct the test-taker to choose the best revision.

3. **Punctuation-only format** (for punctuation focus keys): Options contain only the punctuation mark.
   
   - Example: options are `";"`, `"."`, `";"`, `";"`
   - The passage shows the blank at the punctuation location.

The agent must not mix formats within a single item. All four options must use the same format.

### 17.12 Difficulty calibration rubric

Use this rubric to assign `difficulty_overall` and sub-difficulty fields:

| Dimension              | `low`                                                         | `medium`                                                    | `high`                                                   |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------- |
| `difficulty_reading`   | Common vocabulary, short sentences, familiar topic            | Some academic vocabulary, compound sentences, neutral topic | Dense academic prose, embedded clauses, unfamiliar topic |
| `difficulty_grammar`   | Single, visible rule application (e.g., simple S-V agreement) | Rule requires cross-sentence parsing or trap navigation     | Multiple rules interact, or trap is deeply embedded      |
| `difficulty_inference` | No inference required; answer is directly in the text         | One-step inference (e.g., register shift)                   | Multi-step inference combining grammar and rhetoric      |
| `difficulty_vocab`     | All words below 10th-grade level                              | Some words at 11th–12th grade or academic register          | Rare words, technical terms, or archaic usage            |
| `distractor_strength`  | Distractors are obviously wrong on inspection                 | One distractor is tempting; others are moderate             | All three distractors are plausible on first read        |

`difficulty_overall` is not an average. It reflects the dimension that creates the most challenge. A sentence with easy reading but a high-strength trap is `medium` or `high` overall.

### 17.13 Evidence span selection rules

`evidence_span_text` must quote the minimal text that justifies the correct answer.

Rules:

- Include the grammatical subject and the corrected element.
- Use `"..."` ellipsis to omit intervening text when the span exceeds 8 words.
- Do not include the full sentence unless the entire sentence is the evidence.
- For punctuation items, include the words immediately before and after the punctuation decision.

Examples:

- S-V agreement: `"The colony ... plays"` (subject + verb, ellipsis for intervening clause)
- Semicolon: `"distances ; they"` (words surrounding the punctuation)
- Modifier: `"After reviewing the data, the team revised"` (participial phrase + corrected subject)

### 17.14 Explanation content requirements

| Field               | Maximum length | Required content                                                                                                                                                 |
| ------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `explanation_short` | 25 words       | State the core rule and why the correct answer satisfies it.                                                                                                     |
| `explanation_full`  | 150 words      | Explain why the correct answer is correct. Explain why each wrong option is wrong, naming the specific error. Reference evidence from the passage when relevant. |

For No-Change items, `explanation_full` must explicitly state why the original text needs no correction.

For generated items, `explanation_full` must address all three wrong options by label (A, B, C, D) and name the specific grammar focus key that explains each error.

---

## 18. Pilot Ingestion Pack Correction Examples

The following examples show how to upgrade broad free-text labels to exact schema keys.

### Example 1: Plural possessive (M1 Q19)

**Old label:** plural possessive

**Correct classification:**

```json
{
  "grammar_role_key": "punctuation",
  "grammar_focus_key": "apostrophe_use",
  "syntactic_trap_key": "none"
}
```

The item asks for "people's stories." The wrong options are apostrophe/plural traps.

### Example 2: Sentence boundary with interruption (M1 Q21)

**Old label:** sentence boundary with interruption

**Correct classification:**

```json
{
  "grammar_role_key": "sentence_boundary",
  "grammar_focus_key": "sentence_boundary",
  "syntactic_trap_key": "interruption_breaks_subject_verb"
}
```

The correct answer must create a valid sentence boundary: "ran—fast. During..."

### Example 3: Essential relative clause (M2 Q21)

**Old label:** relative clause / modifier

**Correct classification:**

```json
{
  "grammar_role_key": "modifier",
  "grammar_focus_key": "relative_pronouns",
  "syntactic_trap_key": "none"
}
```

The correct option is "company that," which creates an essential relative clause without an unnecessary comma.

---

## 19. Final Output Requirements (Revised)

The agent must return:

- valid JSON only when used in ingestion mode
- no invented lookup keys
- exactly four answer options for SAT multiple-choice items
- exactly one correct option
- `grammar_focus_key` only when appropriate
- `option_error_focus_key` for grammar distractors when possible
- `generation_profile` for every ingested item
- `secondary_grammar_focus_keys` populated when multiple rules apply
- `disambiguation_rule_applied` when any label conflict was resolved
- `classification_rationale` for every classification
- `is_no_change_question` when original text is an option
- `passage_tense_register_key` and `expected_tense_key` for all verb-form items
- `syntactic_trap_intensity` for all generation profiles
- `target_frequency_band` for all generation profiles

The agent must not directly write SQL. The backend validator converts approved JSON into database writes.

---

## 20. Real-Time Generation Protocol

This section governs automated, deterministic generation of SAT-style grammar questions from a specification. It supplements the ingestion rules with production-ready generation guardrails.

### 20.1 Generation Input Specification

The agent receives a generation request as structured input:

```json
{
  "generation_request": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "difficulty_overall": "medium",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs two more medium-difficulty subject-verb agreement items."
  }
}
```

The agent must reject any request that:

- Uses an unapproved `grammar_focus_key`
- Maps a `grammar_focus_key` to the wrong `grammar_role_key`
- Requests a `very_low` frequency item without explicit justification

### 20.2 Step-by-Step Generation Workflow

The agent must generate in this exact order. Each step is blocking: the next step cannot begin until the previous step passes validation.

#### Step 1: Generate the passage sentence

Requirements:

- 20–40 words for `sentence_only` items; 80–150 for passage excerpts
- One clear, non-trivia-dependent sentence that hosts the target grammar pattern
- Formal academic register; no contractions, slang, or first person
- Self-contained meaning (reader must not need outside knowledge)
- The error location must be unambiguous (one underline, one blank, or one revision zone)

The passage must embed the target syntactic trap naturally. Examples:

| `target_syntactic_trap_key`        | Passage construction rule                                                                          |
| ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| `nearest_noun_attraction`          | Place a plural noun or nominalization between the singular subject and the verb                    |
| `interruption_breaks_subject_verb` | Insert a parenthetical phrase between subject and verb                                             |
| `modifier_attachment_ambiguity`    | Open with a participial phrase whose implied subject differs from the sentence subject             |
| `garden_path`                      | Begin with a noun that looks like a subject but is actually an object in a reduced relative clause |
| `nominalization_obscures_subject`  | Use a nominalized verb form that hides the true grammatical subject                                |
| `long_distance_dependency`         | Separate a pronoun from its antecedent by multiple clauses                                         |
| `scope_of_negation`                | Place negation where it can scope over two different constituents                                  |

#### Step 2: Generate the stem

Requirements:

- Standard SAT stem wording: "Which choice completes the text so that it conforms to the conventions of Standard English?" or equivalent
- The stem must point to the exact location of the grammar decision
- For `choose_best_grammar_revision` items, the stem must explicitly name the revision goal

#### Step 3: Generate the correct option

Requirements:

- The correct option must be grammatically flawless
- It must resolve the syntactic trap without introducing a new error
- It must preserve register, tone, and meaning of the original passage
- It must not be longer than 150% of the original text at the revision zone

#### Step 4: Generate three distractors

Each distractor must have a distinct, documented failure mode. See 20.4 and 20.15 for heuristics by focus key.

Requirements:

- Exactly three wrong options
- Each must be tempting on first read
- No two distractors may fail for the exact same grammar reason
- At least one distractor must target the declared syntactic trap directly
- No distractor may contain an unintended second error that makes it "more wrong" than necessary
- Distractor text must be plausible English; gibberish is forbidden

#### Step 5: Assemble metadata

Populate all required fields from sections 17 and 19.

#### Step 6: Run the validation checklist

See 20.6. If any check fails, return to the failed step. Maximum 3 retries per component before aborting and returning an error response (see 20.9).

### 20.3 Passage Generation Rules by Grammar Focus

These rules constrain the passage so the target grammar error is natural and testable.

#### `subject_verb_agreement`

- Use a singular collective, abstract, or inverted subject
- Insert a plural prepositional object or appositive between subject and verb
- Example: "The flock of migratory birds ______ overhead each autumn."

#### `pronoun_antecedent_agreement`

- Use a singular antecedent that looks plural ("the team," "everyone")
- Place a plural noun nearby to attract the wrong pronoun
- Example: "Every student must submit their ______ before Friday."

#### `verb_tense_consistency`

- Open with a time marker that sets tense expectation
- Place a distractor tense that matches a nearby noun's temporal implication
- Example: "By the time researchers arrived, the specimen ______ (had vanished / vanished / has vanished / would vanish)."

#### `modifier_placement` / `dangling_modifier`

- Start the sentence with a participial phrase whose logical subject is not the grammatical subject
- Example: "After reviewing the data, the hypothesis ______ (was revised by the team / the team revised the hypothesis)."

#### `punctuation_comma`

- Create a compound sentence with or without a coordinating conjunction
- Test FANBOYS comma, introductory phrase comma, or nonrestrictive element comma
- Example: "The artist worked tirelessly on the sculpture and ______ (it was displayed / displayed it / it displayed) in the gallery."

#### `semicolon_use`

- Use two closely related independent clauses
- Place a transitional phrase after the semicolon zone
- Example: "The theory remains controversial ______ (however, it / ; however, it / , however it / : however it) has gained support."

#### `apostrophe_use`

- Use a plural possessive or a possessive pronoun that looks like a contraction
- Example: "The ______ (students' / student's / students / students's) projects were evaluated by a panel."

#### `appositive_punctuation`

- Use a noun phrase that renames an adjacent noun
- Test comma vs no comma for essential vs nonessential appositive
- Example: "The novel Beloved ______ (a powerful work / , a powerful work / ; a powerful work / : a powerful work) explores memory."

#### `relative_pronouns`

- Use a clause that is either essential or nonessential
- Test `that` vs `which` or comma placement around the clause
- Example: "The experiment ______ (that yielded / , which yielded / , that yielded / which yielded) surprising results was repeated."

#### `colon_dash_use`

- Create a sentence where an independent clause is followed by an explanation, list, or elaboration
- Test colon vs dash vs comma vs no punctuation
- Example: "The researchers identified one primary cause ______ (a deficiency / : a deficiency / — a deficiency / , a deficiency) in nutrient uptake."

#### `conjunctive_adverb_usage`

- Join two independent clauses with a conjunctive adverb
- Test semicolon + comma vs comma only vs period + comma
- Example: "The proposal was rejected ______ (however, the team / ; however, the team / , however, the team / . However, the team) revised it."

#### `parallel_structure`

- Create a list or correlative construction where one element breaks form symmetry
- Test gerund vs infinitive vs noun phrase consistency
- Example: "The artist is known for painting murals, sculpting bronze figures, and ______ (to create / creating / creation / create) public installations."

#### `pronoun_case`

- Use a compound subject or object where pronoun case is tested
- Place the pronoun next to a noun that suggests the wrong case
- Example: "The award was given to Maria and ______ (I / me / myself / mine) for our contributions."

#### `pronoun_clarity`

- Create a sentence with multiple possible antecedents for a pronoun
- Example: "When the architect met with the engineer, ______ (he / she / they / the architect) presented the revised blueprints."

#### `possessive_contraction`

- Use a context where `it's` vs `its` or `who's` vs `whose` is tested
- Example: "The company expanded ______ (its / it's / its' / it is) operations overseas."

#### `hyphen_usage`

- Use a compound modifier before a noun where hyphenation is required
- Example: "The ______ (well known / well-known / well, known / well known-) author signed copies of her novel."

#### `logical_predication`

- Create a sentence where the subject and predicate are grammatically possible but logically incompatible
- Example: "The discovery of the ancient manuscript ______ (was exciting to historians / excited historians / was exciting to read / excited the reading) when it was found."

#### `comparative_structures`

- Create a comparison where the things being compared are not grammatically parallel
- Example: "The novel is more challenging than ______ (the play / the playwright / writing / to write)."

### 20.4 Distractor Generation Heuristics by Grammar Focus

For each focus key, the agent must use the exact distractor pattern listed below. The pattern is ordered: distractor 1 targets the primary trap; distractors 2 and 3 introduce distinct secondary errors.

#### `subject_verb_agreement`

| Distractor | Error                                            | Plausibility source                             |
| ---------- | ------------------------------------------------ | ----------------------------------------------- |
| 1          | Plural verb (nearest noun attraction)            | `nearest_noun_attraction`                       |
| 2          | Singular verb but wrong tense                    | `auditory_similarity` / `formal_register_match` |
| 3          | Compound or auxiliary verb that breaks agreement | `grammar_fit_only`                              |

#### `verb_tense_consistency`

| Distractor | Error                                        | Plausibility source           |
| ---------- | -------------------------------------------- | ----------------------------- |
| 1          | Tense that matches a nearby temporal noun    | `temporal_sequence_ambiguity` |
| 2          | Present perfect when simple past is required | `formal_register_match`       |
| 3          | Conditional/future that sounds sophisticated | `grammar_fit_only`            |

#### `punctuation_comma`

| Distractor | Error                                       | Plausibility source      |
| ---------- | ------------------------------------------- | ------------------------ |
| 1          | Missing comma (comma splice or run-on)      | `punctuation_style_bias` |
| 2          | Unnecessary comma (before essential clause) | `grammar_fit_only`       |
| 3          | Semicolon where comma is correct            | `formal_register_match`  |

#### `semicolon_use`

| Distractor | Error                          | Plausibility source      |
| ---------- | ------------------------------ | ------------------------ |
| 1          | Comma splice                   | `punctuation_style_bias` |
| 2          | Colon instead of semicolon     | `formal_register_match`  |
| 3          | Period that creates a fragment | `grammar_fit_only`       |

#### `apostrophe_use`

| Distractor | Error                                          | Plausibility source       |
| ---------- | ---------------------------------------------- | ------------------------- |
| 1          | No apostrophe (plural instead of possessive)   | `auditory_similarity`     |
| 2          | Apostrophe after s (wrong singular possessive) | `nearest_noun_attraction` |
| 3          | Apostrophe in a pronoun (it's vs its)          | `common_idiom_pull`       |

#### `modifier_placement`

| Distractor | Error                              | Plausibility source             |
| ---------- | ---------------------------------- | ------------------------------- |
| 1          | Modifier placed next to wrong noun | `modifier_attachment_ambiguity` |
| 2          | Modifier split from its head noun  | `grammar_fit_only`              |
| 3          | Dangling modifier preserved        | `formal_register_match`         |

#### `relative_pronouns`

| Distractor | Error                                      | Plausibility source       |
| ---------- | ------------------------------------------ | ------------------------- |
| 1          | `which` without comma for essential clause | `punctuation_style_bias`  |
| 2          | `that` with comma for nonessential clause  | `grammar_fit_only`        |
| 3          | `who` for inanimate antecedent             | `nearest_noun_attraction` |

#### `colon_dash_use`

| Distractor | Error                               | Plausibility source      |
| ---------- | ----------------------------------- | ------------------------ |
| 1          | Comma instead of colon/dash         | `punctuation_style_bias` |
| 2          | Semicolon where colon is required   | `formal_register_match`  |
| 3          | No punctuation (run-on elaboration) | `grammar_fit_only`       |

#### `appositive_punctuation`

| Distractor | Error                                   | Plausibility source      |
| ---------- | --------------------------------------- | ------------------------ |
| 1          | Comma around essential appositive       | `punctuation_style_bias` |
| 2          | No comma around nonessential appositive | `grammar_fit_only`       |
| 3          | Dash where comma is sufficient          | `formal_register_match`  |

#### `parallel_structure`

| Distractor | Error                                        | Plausibility source       |
| ---------- | -------------------------------------------- | ------------------------- |
| 1          | Gerund where infinitive is required          | `grammar_fit_only`        |
| 2          | Noun phrase where verb phrase is required    | `nearest_noun_attraction` |
| 3          | Prepositional phrase that breaks parallelism | `formal_register_match`   |

#### `pronoun_case`

| Distractor | Error                                               | Plausibility source       |
| ---------- | --------------------------------------------------- | ------------------------- |
| 1          | Subject pronoun in object position                  | `nearest_noun_attraction` |
| 2          | Reflexive pronoun where simple object is required   | `formal_register_match`   |
| 3          | Possessive pronoun where object pronoun is required | `common_idiom_pull`       |

#### `conjunctive_adverb_usage`

| Distractor | Error                                           | Plausibility source      |
| ---------- | ----------------------------------------------- | ------------------------ |
| 1          | Comma only (comma splice)                       | `punctuation_style_bias` |
| 2          | Period before conjunctive adverb with lowercase | `grammar_fit_only`       |
| 3          | Semicolon but no comma after adverb             | `formal_register_match`  |

### 20.5 Complete Generation Examples

The following examples show the full JSON output the agent must produce.

#### Example A: Generated `subject_verb_agreement` with `nearest_noun_attraction`

```json
{
  "generation_request": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "difficulty_overall": "medium",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "generation_context": "Module needs one medium-difficulty S-V agreement item."
  },
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 999,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "The colony of deep-sea corals, which live in near-total darkness off the coast of Australia, ______ an important role in the local ecosystem.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "C",
    "explanation_short": "The singular subject 'colony' requires the singular verb 'plays.'",
    "explanation_full": "The grammatical subject of the sentence is the singular noun 'colony,' not the plural noun 'corals' in the intervening relative clause. Therefore, the main verb must be singular: 'plays.' Options A and B incorrectly use plural verbs, likely because the writer is distracted by the nearby plural noun 'corals.' Option D introduces an unnecessary auxiliary verb that disrupts the sentence structure.",
    "evidence_span_text": "The colony ... plays"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Form, Structure, and Sense",
    "subskill": "Agreement",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "agreement",
    "grammar_focus_key": "subject_verb_agreement",
    "secondary_grammar_focus_keys": [],
    "syntactic_trap_key": "nearest_noun_attraction",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "subject_verb_agreement > noun_countability",
    "classification_rationale": "The item tests subject-verb agreement with a singular subject separated from its verb by a plural intervening noun."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "play",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "The plural noun 'corals' is the nearest noun to the verb slot, making 'play' sound natural on a quick read.",
      "why_wrong": "The grammatical subject is the singular noun 'colony,' not 'corals.' A plural verb creates a subject-verb agreement error.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "have played",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "The present perfect sounds sophisticated and is grammatically possible in other contexts.",
      "why_wrong": "The plural auxiliary 'have' does not agree with the singular subject 'colony.'",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "plays",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_agreement",
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "why_plausible": "Correct: the singular verb agrees with the singular subject 'colony.'",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "is playing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "unnecessary_auxiliary",
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "verb_form",
      "why_plausible": "The progressive form is grammatically valid in isolation.",
      "why_wrong": "The present progressive changes the sentence meaning and is not the conventional way to state a general ecological role.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Subject-verb agreement requires that a singular subject take a singular verb.",
    "trap_mechanism": "A plural noun ('corals') intervenes between the singular subject and the verb, tempting test-takers to choose a plural verb.",
    "correct_answer_reasoning": "The singular subject 'colony' requires the singular present-tense verb 'plays.'",
    "distractor_analysis_summary": "A and B are plural verbs attracted by the nearest noun; D introduces an unnecessary progressive form.",
    "similar_items": [
      {
        "pattern": "singular subject + intervening plural noun + verb blank",
        "focus_key": "subject_verb_agreement",
        "trap_key": "nearest_noun_attraction"
      }
    ]
  },
  "generation_profile": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "target_distractor_pattern": [
      "one nearest-noun plural verb distractor",
      "one plural auxiliary / compound verb distractor",
      "one unnecessary progressive/auxiliary distractor"
    ],
    "passage_template": "The [singular collective noun] of [plural noun], [relative clause], ______ [role/action].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v2.0"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Clean S-V agreement item. No ambiguity in classification."
  }
}
```

#### Example B: Generated `semicolon_use` with `punctuation_style_bias`

```json
{
  "generation_request": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "semicolon_use",
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "high",
    "difficulty_overall": "medium",
    "topic_broad": "history",
    "topic_fine": "ancient civilizations",
    "passage_length_words": "20-30",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "generation_context": "Module needs one semicolon item."
  },
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 999,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "The Roman aqueducts transported water across vast distances ______ they enabled cities to grow far from natural sources.",
    "correct_option_label": "B",
    "explanation_short": "A semicolon correctly joins two independent clauses that are closely related.",
    "explanation_full": "The sentence contains two independent clauses: 'The Roman aqueducts transported water across vast distances' and 'they enabled cities to grow far from natural sources.' Because the clauses are closely related, a semicolon is the most effective punctuation. A comma alone creates a comma splice. A period is grammatically correct but less effective at showing the relationship. A colon would incorrectly suggest that the second clause explains the first.",
    "evidence_span_text": "distances ; they"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Boundaries",
    "subskill": "Sentence Boundaries",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "semicolon_use",
    "secondary_grammar_focus_keys": ["sentence_boundary"],
    "syntactic_trap_key": "none",
    "disambiguation_rule_applied": "sentence_boundary > punctuation",
    "classification_rationale": "The item tests the correct use of a semicolon between two independent clauses."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": ",",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "comma_splice",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "comma_splice",
      "why_plausible": "A comma is the most common punctuation mark; students often default to it.",
      "why_wrong": "A comma alone cannot join two independent clauses; it creates a comma splice.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": ";",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_boundary",
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "why_plausible": "Correct: a semicolon joins two closely related independent clauses.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": ".",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "boundary_overly_strong",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "sentence_boundary",
      "why_plausible": "A period creates two complete sentences, which is grammatically acceptable.",
      "why_wrong": "While grammatically valid, a period is less effective than a semicolon because it severs the close logical relationship between the clauses.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2
    },
    {
      "option_label": "D",
      "option_text": ":",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "wrong_boundary_type",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "colon_dash_use",
      "why_plausible": "A colon looks sophisticated and is common in formal writing.",
      "why_wrong": "A colon must introduce an explanation, list, or elaboration of the preceding clause. The second clause does not explain the first; it adds a related consequence.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "generation_profile": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "semicolon_use",
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "one comma splice distractor",
      "one period distractor (grammatically correct but less effective)",
      "one colon distractor (wrong boundary type)"
    ],
    "passage_template": "[Independent clause 1] ______ [independent clause 2 related by consequence or contrast].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v2.0"
  }
}
```

### 20.6 Pre-Output Validation Checklist

Before emitting any generated item, the agent must verify every check below. If any check fails, the agent must regenerate the failing component.

| #   | Check                                                                        | Failure action                                 |
| --- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| 1   | `grammar_focus_key` belongs to `grammar_role_key` per 17.1                   | Regenerate classification block                |
| 2   | Exactly 4 options exist                                                      | Regenerate all options                         |
| 3   | Exactly 1 option has `is_correct: true`                                      | Regenerate options                             |
| 4   | No two distractors share the same `option_error_focus_key`                   | Regenerate one distractor                      |
| 5   | At least one distractor targets the declared `target_syntactic_trap_key`     | Regenerate distractors                         |
| 6   | Correct option contains no grammar error                                     | Regenerate correct option                      |
| 7   | Passage is 20–40 words for sentence-only items                               | Regenerate passage                             |
| 8   | Passage requires no outside knowledge                                        | Regenerate passage                             |
| 9   | Register is formal academic; no contractions or slang                        | Regenerate passage                             |
| 10  | `difficulty_overall` matches declared target                                 | Regenerate item                                |
| 11  | `target_frequency_band` is not `very_low` without justification              | Reject request or add justification            |
| 12  | `disambiguation_rule_applied` is present if any label conflict exists        | Add rule or set `needs_human_review: true`     |
| 13  | `explanation_full` explains why every wrong option is wrong                  | Regenerate explanations                        |
| 14  | `generation_profile` includes all required fields from 19                    | Add missing fields                             |
| 15  | All JSON keys are from approved lists; no invented keys                      | Replace with approved key or propose amendment |
| 16  | `evidence_span_text` follows format rules from 17.13                         | Reformat evidence span                         |
| 17  | Option text format is consistent (all fill-in-blank or all full-replacement) | Regenerate options                             |

Maximum 3 retries per component. After 3 failures, abort and return an error response (see 20.9).

### 20.7 Real-Time Constraints

For production generation pipelines, the agent must:

- Emit valid JSON on the first attempt ≥90% of the time
- Complete generation end-to-end in ≤3 reasoning steps
- Never hallucinate an exam ID (use `"GENERATED"` for synthetic items)
- Cache and reuse passage templates for identical `(grammar_focus_key, syntactic_trap_key)` pairs to improve determinism
- Log any amendment proposal immediately; do not embed unapproved keys in production JSON

### 20.8 No-Change Generation

Approximately 20% of official SAT grammar questions have the original text as the correct answer. The agent must be able to generate No-Change items deterministically.

#### No-Change generation rules

1. Generate a grammatically flawless passage with no error at the target zone.
2. Make option A the original text (correct).
3. Distractors B, C, D must each introduce a different grammar error.
4. The stem must not assume an error exists. Use neutral wording: "Which choice completes the text so that it conforms to the conventions of Standard English?"

#### No-Change distractor requirements

| Distractor | Must introduce...                                       |
| ---------- | ------------------------------------------------------- |
| B          | A grammar error related to the target focus key         |
| C          | A different grammar error (secondary focus key allowed) |
| D          | A plausible-sounding error that violates a common rule  |

#### No-Change example specification

```json
{
  "generation_request": {
    "target_grammar_focus_key": "punctuation_comma",
    "is_no_change_target": true,
    "no_change_position": "A"
  }
}
```

Output must include:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

### 20.9 Error Response Format

If the agent rejects a generation request or fails after 3 retries on any component, it must return a structured error:

```json
{
  "error": {
    "error_code": "INVALID_FOCUS_KEY | ROLE_FOCUS_MISMATCH | VERY_LOW_FREQUENCY_UNJUSTIFIED | GENERATION_FAILURE | VALIDATION_FAILURE",
    "error_message": "Human-readable description of the failure.",
    "failed_component": "passage | stem | correct_option | distractor | metadata | validation",
    "retry_count": 3,
    "recommendation": "Suggested fix or fallback action."
  }
}
```

### 20.10 Batch Generation Rules

The agent may receive requests to generate multiple items at once.

Requirements:

- Maximum batch size: 10 items per request
- Items in a batch must not share the same `(grammar_focus_key, syntactic_trap_key)` pair unless explicitly requested
- Items in a batch must vary `topic_broad` and `topic_fine` to avoid clustering
- The agent must output an array of complete item JSON objects
- If any item in the batch fails validation after 3 retries, the agent must return the error for that specific item index and halt the batch

Batch response format:

```json
{
  "batch_results": [
    { "item_index": 0, "status": "success", "item": { ... } },
    { "item_index": 1, "status": "success", "item": { ... } },
    { "item_index": 2, "status": "error", "error": { ... } }
  ]
}
```

### 20.11 Topic Rotation and Deduplication

To ensure realistic module composition:

1. **Topic rotation:** No two consecutive generated items may share the same `topic_broad`.
2. **Subtopic spacing:** No two items within a 5-item window may share the same `topic_fine`.
3. **Pattern deduplication:** Before emitting a generated item, the agent must verify it is not a lexical variant of a previously generated item with the same `passage_template`. If similarity exceeds 80% (same structure with only noun substitution), regenerate the passage.
4. **Exam ID deduplication:** If `avoid_recent_exam_ids` is provided, ensure generated passages do not closely resemble items from those exams.

### 20.12 Difficulty Calibration for Generation

The agent must calibrate `difficulty_overall` at generation time using this rubric:

| Difficulty | Trap intensity  | Distractor plausibility                                              | Passage complexity                                   |
| ---------- | --------------- | -------------------------------------------------------------------- | ---------------------------------------------------- |
| `low`      | `none` or `low` | Obvious errors (e.g., gibberish not allowed, but clearly wrong form) | Short sentence, common vocabulary                    |
| `medium`   | `medium`        | One strong distractor, two moderate                                  | Standard academic vocabulary, one clause             |
| `high`     | `high`          | All three distractors plausible                                      | Dense vocabulary, multiple clauses, unfamiliar topic |

When `target_syntactic_trap_key` is `none`, cap `difficulty_overall` at `medium` unless the passage uses intentionally complex syntax.

### 20.13 Explanation Requirements for Generation

Generated items must include explanations that meet these standards:

1. `explanation_short` must be ≤25 words and state the core rule.
2. `explanation_full` must be ≤150 words and:
   - State why the correct answer is correct
   - Name each wrong option by label and explain its specific error
   - Reference the passage evidence when relevant
3. For No-Change items, `explanation_full` must explicitly justify why the original text needs no correction.
4. For verb-form items, `explanation_full` must reference the `passage_tense_register_key`.

### 20.14 Option Ordering Rules

The correct answer may appear in any position (A, B, C, or D). The agent must randomize correct option placement.

Distribution requirement over a batch of 10+ items:

- Correct answer in position A: 20–30%
- Correct answer in position B: 20–30%
- Correct answer in position C: 20–30%
- Correct answer in position D: 20–30%

No individual module may have more than 40% of correct answers in any single position.

### 20.15 Expanded Passage Generation Rules (All Focus Keys)

For focus keys not covered in 20.3, use these construction rules:

#### `sentence_fragment`

- Create a subordinate clause presented as a complete sentence
- Example: "Although the data supported the hypothesis. The researchers ______ (published / were published / publication / publishing) their findings immediately."

#### `comma_splice`

- Join two independent clauses with only a comma
- Example: "The artist finished the sculpture, ______ (it was / ; it was / however, it was / it) displayed in the gallery the next day."

#### `run_on_sentence`

- Fuse two independent clauses with no punctuation or conjunction
- Example: "The experiment succeeded ______ (the / ; the / , and the / . The) researchers celebrated their results."

#### `noun_countability`

- Use a mass noun with a plural article or vice versa
- Example: "The researchers collected ______ (a data / data / datas / datum) from three separate sources."

#### `determiners_articles`

- Use an article where none is needed, or omit a required article
- Example: "______ (The / A / An / —) oxygen is essential for cellular respiration."

#### `affirmative_agreement`

- Test `so` / `neither` / `nor` responses with inverted auxiliary matching
- Example: "The first speaker supported the proposal, and ______ (so did / so the / the / did) the second speaker."

#### `voice_active_passive`

- Create a sentence where active/passive voice creates ambiguity or inconsistency
- Example: "The novel ______ (was written by / wrote / written by / had wrote) the author in just three months."

#### `negation`

- Place negation where scope ambiguity creates multiple interpretations
- Example: "The study did not find significant differences between the two groups ______ (in most cases / in any case / in no case / in some cases)."

#### `logical_predication`

- Create subject-predicate incompatibility
- Example: "The discovery of the ancient manuscript ______ (was exciting to historians / excited historians / was exciting to read / excited the reading) when it was found."

#### `quotation_punctuation`

- Test comma placement with quotation marks
- Example: "The critic wrote ______ ('The /, 'The /: 'The /; 'The) novel is a masterpiece of modern literature.'"

---

## 21. Reference Quick-Index

| Concept                                                | Section  |
| ------------------------------------------------------ | -------- |
| Operating principles                                   | 1        |
| Required output shape                                  | 2        |
| Formal schemas (reasoning, generation_profile, review) | 2.1      |
| Question fields                                        | 3        |
| stimulus_mode_key / stem_type_key values               | 3.1, 3.2 |
| Approved values for undocumented fields                | 3.3      |
| Classification fields                                  | 4        |
| Grammar role keys                                      | 5        |
| Grammar focus keys                                     | 6        |
| Disambiguation rules                                   | 7        |
| Decision tree                                          | 8        |
| Syntactic trap keys                                    | 9        |
| Option-level analysis                                  | 10       |
| precision_score scale                                  | 10.4     |
| grammar_fit / tone_match semantics                     | 10.5     |
| No-change rule                                         | 11       |
| Multi-error rule                                       | 12       |
| Tense/register                                         | 13       |
| Generation rules                                       | 14       |
| Amendment process                                      | 15       |
| Review flags                                           | 16       |
| Schema guardrails                                      | 17       |
| Option text format rules                               | 17.11    |
| Difficulty calibration rubric                          | 17.12    |
| Evidence span selection rules                          | 17.13    |
| Explanation content requirements                       | 17.14    |
| Pilot corrections                                      | 18       |
| Final output requirements                              | 19       |
| Real-time generation protocol                          | 20       |
| No-Change generation                                   | 20.8     |
| Error response format                                  | 20.9     |
| Batch generation rules                                 | 20.10    |
| Topic rotation / deduplication                         | 20.11    |
| Difficulty calibration for generation                  | 20.12    |
| Explanation requirements for generation                | 20.13    |
| Option ordering rules                                  | 20.14    |
| Expanded passage generation rules                      | 20.15    |
| Reference quick-index                                  | 21       |
