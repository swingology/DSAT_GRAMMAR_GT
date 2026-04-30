# rules_agent_dsat_grammar_ingestion_generetion_v5.md

## Purpose

This is the consolidated v5 production rule file for the DSAT grammar
ingestion and generation agent. It merges:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md` (base)
- `rules_agent_dsat_grammar_ingestion_generation_v3_1.md` (PT4–PT11 gap additions)

All v3.1 additions are integrated inline. The addendum file is superseded
by this document.

The agent uses this file to produce consistent structured outputs for:

- question classification
- option-level distractor analysis
- grammar rule identification
- generation templates
- review/amendment proposals

The agent must not invent new taxonomy keys unless explicitly using the
amendment process.

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

The agent must output structured JSON or markdown records for validation. A
deterministic backend validator checks all keys before insertion.

### 1.3 Use controlled keys

The agent must use only approved lookup keys. If no key fits, it must propose
an amendment instead of inventing a new production key.

### 1.4 Meaning over surface form

When grammar and meaning overlap, classify the item by the main reason the
correct answer is required.

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

### 2.1 Formal schemas

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
  "generation_timestamp": "2026-04-29T00:00:00Z",
  "model_version": "rules_agent_v5.0"
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

| Field | Approved values |
|---|---|
| `answer_mechanism_key` | `rule_application`, `pattern_matching`, `evidence_location`, `inference`, `data_synthesis` |
| `solver_pattern_key` | `apply_grammar_rule_directly`, `locate_error_zone`, `compare_register`, `evaluate_transition`, `synthesize_notes`, `eliminate_by_boundary` |
| `semantic_relation_key` | `nearest_noun_agreement`, `comma_splice`, `boundary_not_closed`, `boundary_overly_strong`, `wrong_boundary_type`, `correct_agreement`, `correct_boundary`, `unnecessary_auxiliary`, `tense_mismatch`, `modifier_misplaced`, `pronoun_ambiguous`, `parallel_broken`, `idiom_violation` |
| `evidence_scope_key` | `sentence`, `paragraph`, `passage`, `paired_passage`, `table`, `graph`, `notes` |
| `evidence_location_key` | `main_clause`, `subordinate_clause`, `surrounding_sentence`, `opening_sentence`, `closing_sentence`, `transition_zone`, `data_zone`, `entire_passage` |
| `distractor_strength` | `low`, `medium`, `high` |
| `difficulty_overall`, `difficulty_reading`, `difficulty_grammar`, `difficulty_inference`, `difficulty_vocab` | `low`, `medium`, `high` |
| `skill_family` | `Sentence Boundaries`, `Form, Structure, and Sense`, `Agreement`, `Punctuation`, `Transitions`, `Rhetorical Synthesis`, `Craft and Structure` |
| `subskill` | Free-text describing the specific skill. |
| `topic_broad` | `science`, `history`, `literature`, `social_studies`, `arts`, `economics`, `technology`, `environment` |
| `topic_fine` | Free-text subtopic. |

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

Use `grammar_role_key` only when the question is Standard English Conventions
or grammar-adjacent.

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

Use for fragments, run-ons, comma splices, and punctuation required to divide
sentence units (periods, semicolons, commas, dashes at clause boundaries).

### 5.2 When to use `agreement`

Use for subject-verb agreement, pronoun-antecedent agreement, countability and
number agreement, and determiners/articles where noun number is the central
issue.

### 5.3 When to use `verb_form`

Use for tense consistency, finite vs nonfinite verbs, gerunds and infinitives,
voice, mood and conditional logic, and scientific present / general truth.

### 5.4 When to use `modifier`

Use for dangling modifiers, misplaced modifiers, modifier scope, comparative
structures, and logical predication.

### 5.5 When to use `punctuation`

Use for comma mechanics, semicolon mechanics, colon/dash mechanics,
apostrophes, appositives, quotation punctuation, hyphens, absence of
punctuation inside required syntactic units, and end-punctuation type
(question mark vs period) when determined by sentence type.

### 5.6 When to use `parallel_structure`

Use for parallel lists, correlative conjunctions, comparison structures when
form symmetry is primary, and elliptical constructions.

### 5.7 When to use `pronoun`

Use for pronoun case, pronoun clarity, and ambiguous pronoun reference.

### 5.8 When to use `expression_of_ideas`

Use only when the question is grammar-adjacent but primarily about concision,
register, transition logic, precision of expression, data claim accuracy, or
rhetorical effectiveness.

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
- `unnecessary_internal_punctuation`
- `end_punctuation_question_statement`

#### `unnecessary_internal_punctuation` — rule definition

No punctuation may appear inside a required syntactic unit. The units the SAT
tests are: subject–verb, verb–object, verb–complement, preposition–complement,
and integrated relative clause. Inserting a comma, dash, or colon inside any
of these units is always wrong. The correct option has no punctuation at the
target boundary.

#### `end_punctuation_question_statement` — rule definition

A sentence that contains an indirect (reported) question ends with a period,
not a question mark, because the sentence as a whole is declarative. A
sentence consisting of two coordinated direct questions requires a question
mark. Wrong options typically swap the end mark or omit it.

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
14. `unnecessary_internal_punctuation` > general `punctuation_comma` when the test is whether punctuation should be absent inside a syntactic unit
15. `end_punctuation_question_statement` > general `punctuation` when the test is period vs question mark based on sentence type

Always write the selected rule in `disambiguation_rule_applied`.

---

## 8. Decision Tree for Grammar Annotation

### Step 1: Is this Standard English Conventions?

If the answer is chosen because of grammar, punctuation, sentence structure,
or usage → `conventions_grammar`. If because of transition logic, note
synthesis, concision, or rhetorical goal → Expression of Ideas.

### Step 2: Is the issue a sentence boundary?

Fragment, comma splice, run-on, period vs semicolon vs comma at clause
boundaries → sentence-boundary keys.

### Step 3: Is the issue punctuation mechanics?

- comma → `punctuation_comma`
- semicolon → `semicolon_use`
- colon/dash → `colon_dash_use`
- apostrophe → `apostrophe_use`
- conjunctive adverb punctuation → `conjunctive_adverb_usage`
- appositive punctuation → `appositive_punctuation`
- absent punctuation inside a syntactic unit → `unnecessary_internal_punctuation`
- period vs question mark based on sentence type → `end_punctuation_question_statement`

### Step 4: Is the issue agreement?

`subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`,
`determiners_articles`.

### Step 5: Is the issue verb form?

`verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation`.

### Step 6: Is the issue modifier logic?

`modifier_placement`, `comparative_structures`, `logical_predication`,
`relative_pronouns`.

### Step 7: Is the issue pronoun-specific?

`pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement`.

### Step 8: Is the issue parallel or idiomatic structure?

`parallel_structure`, `elliptical_constructions`, `conjunction_usage`.

### Step 9: If multiple rules apply

Choose the primary rule that eliminates the most wrong options. Store others
in `secondary_grammar_focus_keys`.

---

## 9. Syntactic Trap Keys

Use `syntactic_trap_key` to describe the difficulty mechanism, not the rule
being tested.

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

For wrong options in SEC questions, populate `option_error_focus_key` with the
specific grammar focus key that explains the error.

### 10.2 Distractor type keys

**Wrong options:** `semantic_imprecision`, `logical_mismatch`, `scope_error`,
`tone_mismatch`, `grammar_error`, `punctuation_error`, `transition_mismatch`,
`data_misread`, `goal_mismatch`, `partially_supported`, `overstatement`,
`understatement`, `rhetorical_irrelevance`

**Correct option:** `correct`

### 10.3 Grammar-specific plausibility sources

`nearest_noun_attraction`, `punctuation_style_bias`, `auditory_similarity`,
`grammar_fit_only`, `formal_register_match`, `common_idiom_pull`

### 10.4 precision_score scale

| Value | Meaning |
|---|---|
| `1` | Incorrect. Contains a clear grammar error or fails the tested rule. |
| `2` | Partially acceptable but inferior. Grammatically valid in isolation but less effective. |
| `3` | Correct. Fully satisfies the tested rule. |

### 10.5 grammar_fit and tone_match semantics

| Field | `yes` | `no` |
|---|---|---|
| `grammar_fit` | Grammatically possible in some context | Contains a clear grammar error impossible in any standard context |
| `tone_match` | Maintains formal academic register | Introduces slang, contractions, or register shift |

---

## 11. No-Change and Original-Text Rule

When the original text is an option:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

Do not assume an error exists. If original wording is correct, explain why
no correction is needed.

---

## 12. Multi-Error Rule

When multiple error types appear across choices:

1. Classify the primary tested rule in `grammar_focus_key`
2. Store secondary rules in `secondary_grammar_focus_keys`
3. Store option-specific errors in `option_error_focus_key`
4. Note ambiguity in `review.review_notes`

---

## 13. Passage-Level Tense/Register Rule

### 13.1 Tense register keys

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`
- `literary_present`

### 13.2 Expected patterns

- Narrative/literary passages → past tense
- Scientific facts → simple present
- Historical accounts → past tense
- Study procedures → past tense
- Established findings → present tense
- Past perfect → events completed before another past event
- **Literary present** → when a passage discusses actions, events, or
  patterns *inside* a literary work (novel, poem, play, short story),
  use simple present even if the work was written in the past. Verbs
  describing what characters do, what the text says, or what patterns
  appear in the work use simple present. Frame: "In the novel / poem /
  story, [character] ______." Wrong options offer past tense or
  present perfect.

For tense questions, include:

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

Allowed `expected_tense_key` values: `simple_present`, `simple_past`,
`present_perfect`, `past_perfect`, `future`, `conditional`, `subjunctive`,
`imperative`.

---

## 14. Generation Rules

When generating a grammar item, specify:

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

Each distractor must have a rule violation, plausible surface attraction,
common student error, and relation to correct answer.

### 14.2 Generation must match SAT style

Concise, formal academic, self-contained, evidence-based, not
trivia-dependent, one correct answer only.

### 14.3 Generation must respect frequency

Prioritize high-frequency rules. Use `very_low` frequency rules only for
explicit niche gaps.

---

## 15. Amendment Process

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

---

## 16. Review Flags

Set `needs_human_review: true` when more than one grammar focus seems equally
plausible, the question tests grammar and rhetoric simultaneously, option text
is incomplete, no existing key fits, or the original text may be correct but
is uncertain.

---

## 17. Schema Guardrails and Enforcement Rules

### 17.1 `grammar_role_key` → `grammar_focus_key` mapping

| `grammar_role_key` | Allowed `grammar_focus_key` values |
|---|---|
| `sentence_boundary` | `sentence_fragment`, `comma_splice`, `run_on_sentence`, `sentence_boundary` |
| `agreement` | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`, `determiners_articles`, `affirmative_agreement` |
| `verb_form` | `verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation` |
| `modifier` | `modifier_placement`, `comparative_structures`, `logical_predication`, `relative_pronouns` |
| `punctuation` | `punctuation_comma`, `colon_dash_use`, `semicolon_use`, `conjunctive_adverb_usage`, `apostrophe_use`, `possessive_contraction`, `appositive_punctuation`, `hyphen_usage`, `quotation_punctuation`, `unnecessary_internal_punctuation`, `end_punctuation_question_statement` |
| `parallel_structure` | `parallel_structure`, `elliptical_constructions`, `conjunction_usage` |
| `pronoun` | `pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement` |
| `expression_of_ideas` | `redundancy_concision`, `precision_word_choice`, `register_style_consistency`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `transition_logic` |

### 17.2 `rule_domain` separation

| Official SAT domain | `question_family_key` | `grammar_role_key` usage |
|---|---|---|
| Standard English Conventions | `conventions_grammar` | Required |
| Expression of Ideas | `expression_of_ideas` | Optional; only if grammar-adjacent |
| Craft and Structure | `craft_and_structure` | Forbidden |
| Information and Ideas | `information_and_ideas` | Forbidden |

### 17.3 `secondary_grammar_focus_keys` must be populated when multiple rules apply

Identify the single primary rule that eliminates the most wrong options.
Store it in `grammar_focus_key`. Store every other applicable rule in
`secondary_grammar_focus_keys`. For each wrong option, store the specific
error rule in `option_error_focus_key`.

### 17.4 Option-level error keys must be grammar-specific

| Wrong option surface error | Required `option_error_focus_key` |
|---|---|
| Wrong semicolon | `semicolon_use` |
| Wrong apostrophe | `apostrophe_use` |
| Wrong tense | `verb_tense_consistency` |
| Wrong relative clause | `relative_pronouns` |
| Comma splice | `comma_splice` |
| Dangling modifier | `modifier_placement` |
| Comma inside subject–verb | `unnecessary_internal_punctuation` |
| Question mark on indirect question | `end_punctuation_question_statement` |

### 17.5 No-Change tracking is mandatory when original text is an option

Populate `is_no_change_question`, `original_text_option_label`, and
`original_text_is_correct`. The explanation must state why no correction
is needed.

### 17.6 Passage-level tense/register metadata is mandatory for verb-form questions

For every question where `grammar_role_key` is `verb_form` or
`grammar_focus_key` is `verb_tense_consistency`, `verb_form`, or
`voice_active_passive`, populate `passage_tense_register_key`,
`expected_tense_key`, `tense_shift_allowed`, and `tense_register_notes`.

### 17.7 Syntactic trap keys must include intensity for generation profiles

`syntactic_trap_intensity` values: `low`, `medium`, `high`.

### 17.8 `disambiguation_rule_applied` must be explicit

Quote the exact priority rule from §7 when a conflict is resolved.

### 17.9 Amendment proposals must include parent role and evidence

`proposed_parent_role_key` must be an existing `grammar_role_key` or a new
role proposal with justification. `evidence_text` must quote the exact item
text that triggered the proposal.

### 17.10 Frequency data must guide generation

| Frequency band | Grammar focus keys |
|---|---|
| `very_high` | `punctuation_comma`, `subject_verb_agreement` |
| `high` | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation` |
| `medium` | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure`, `unnecessary_internal_punctuation`, `end_punctuation_question_statement`, `finite_verb_in_main_clause` (verb_form sub-pattern), `modal_plus_plain_form` (verb_form sub-pattern) |
| `low` | `voice_active_passive`, `logical_predication`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation`, `finite_verb_in_relative_clause` (verb_form sub-pattern), `singular_event_reference` (pronoun sub-pattern), `literary_present` (tense register) |
| `very_low` | `affirmative_agreement`, `negation`, `noun_countability`, `determiners_articles`, `elliptical_constructions` |

The generation profile must include `target_frequency_band`. The agent must
not generate a `very_low` frequency item unless explicitly instructed.

### 17.11 Option text format rules

1. **Fill-in-blank** (default for `complete_the_text`): options contain only
   the word or phrase that fills the blank.
2. **Full-replacement** (for `choose_best_grammar_revision`): options contain
   the full revised sentence or clause.
3. **Punctuation-only**: options contain only the punctuation mark.

Do not mix formats within a single item.

### 17.12 Difficulty calibration rubric

| Dimension | `low` | `medium` | `high` |
|---|---|---|---|
| `difficulty_reading` | Common vocabulary, short sentences | Academic vocabulary, compound sentences | Dense prose, embedded clauses, unfamiliar topic |
| `difficulty_grammar` | Single visible rule application | Rule requires cross-sentence parsing or trap navigation | Multiple rules interact or trap is deeply embedded |
| `difficulty_inference` | No inference required | One-step inference | Multi-step inference combining grammar and rhetoric |
| `difficulty_vocab` | Below 10th-grade level | 11th–12th grade or academic register | Rare, technical, or archaic usage |
| `distractor_strength` | Obviously wrong on inspection | One distractor tempting | All three distractors plausible on first read |

`difficulty_overall` reflects the dimension that creates the most challenge,
not an average.

### 17.13 Evidence span selection rules

Quote the minimal text that justifies the correct answer. Include the
grammatical subject and corrected element. Use `"..."` ellipsis for spans
exceeding 8 words. For punctuation items, include words immediately before and
after the punctuation decision.

### 17.14 Explanation content requirements

| Field | Maximum length | Required content |
|---|---|---|
| `explanation_short` | 25 words | Core rule and why correct answer satisfies it |
| `explanation_full` | 150 words | Why correct is correct; why each wrong option fails by label, naming the specific grammar focus key |

---

## 18. Pilot Ingestion Pack Correction Examples

### Example 1: Plural possessive

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "apostrophe_use", "syntactic_trap_key": "none" }
```

### Example 2: Sentence boundary with interruption

```json
{ "grammar_role_key": "sentence_boundary", "grammar_focus_key": "sentence_boundary", "syntactic_trap_key": "interruption_breaks_subject_verb" }
```

### Example 3: Essential relative clause

```json
{ "grammar_role_key": "modifier", "grammar_focus_key": "relative_pronouns", "syntactic_trap_key": "none" }
```

### Example 4: No punctuation between subject and verb

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "unnecessary_internal_punctuation", "syntactic_trap_key": "none" }
```

### Example 5: Period on sentence ending in indirect question

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "end_punctuation_question_statement", "syntactic_trap_key": "none" }
```

---

## 19. Final Output Requirements

The agent must return valid JSON in ingestion mode, no invented keys, exactly
four answer options, exactly one correct option, `grammar_focus_key` only when
appropriate, `option_error_focus_key` for grammar distractors, `generation_profile`
for every ingested item, `secondary_grammar_focus_keys` when multiple rules
apply, `disambiguation_rule_applied` when any label conflict was resolved,
`classification_rationale` for every classification, `is_no_change_question`
when original text is an option, `passage_tense_register_key` and
`expected_tense_key` for all verb-form items, `syntactic_trap_intensity` for
all generation profiles, `target_frequency_band` for all generation profiles.

---

## 20. Real-Time Generation Protocol

### 20.1 Generation Input Specification

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
    "generation_context": "Module needs two more medium-difficulty subject-verb agreement items.",
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital"
  }
}
```

**`test_format_key` values:**

| Value | Module length | When to use |
|---|---|---|
| `digital_app_adaptive` | 27 questions | Default; standard Bluebook adaptive digital SAT |
| `nondigital_linear_accommodation` | 33 questions | Paper accommodation format; PT4–PT11 source tests |

**`source_stats_format` values:**

| Value | Description |
|---|---|
| `official_digital` | Position statistics from Bluebook adaptive modules |
| `official_nondigital_linear` | Position statistics from PT4–PT11 paper accommodation modules |

When `test_format_key` is `nondigital_linear_accommodation`, use 33 questions
and these domain-band ranges (observed PT4–PT11):

```
Reading/Craft/Information: Q1–Q18 (±1)
Standard English Conventions: Q19–Q26 (±1; may start as late as Q18 in M2)
Transitions: Q27–Q30 (variable; 1–5 items)
Notes Synthesis: Q30–Q33 (variable start; always ends at Q33)
```

The validator must reject any 33-question module with
`test_format_key: "digital_app_adaptive"` and any 27-question module with
`test_format_key: "nondigital_linear_accommodation"`.

Reject any request that uses an unapproved `grammar_focus_key`, maps a focus
key to the wrong role, or requests a `very_low` frequency item without
explicit justification.

### 20.2 Step-by-Step Generation Workflow

Each step is blocking. Maximum 3 retries per component before aborting.

#### Step 1: Generate the passage sentence

20–40 words for `sentence_only`; 80–150 for passage excerpts. Formal
academic register, self-contained, error location unambiguous.

#### Step 2: Generate the stem

Standard SAT stem: "Which choice completes the text so that it conforms to
the conventions of Standard English?"

#### Step 3: Generate the correct option

Grammatically flawless, resolves the trap, preserves register and meaning.

#### Step 4: Generate three distractors

Each must have a distinct failure mode. At least one targets the declared
syntactic trap. No two distractors fail for the same grammar reason. No
unintended second error.

#### Step 5: Assemble metadata

Populate all required fields from §17 and §19.

#### Step 6: Run the validation checklist

See §20.6.

### 20.3 Passage Generation Rules by Grammar Focus

#### `subject_verb_agreement`

Use a singular collective, abstract, or inverted subject. Insert a plural
prepositional object or appositive between subject and verb.

#### `pronoun_antecedent_agreement`

Use a singular antecedent that looks plural ("the team," "everyone"). Place a
plural noun nearby.

#### `verb_tense_consistency`

Open with a time marker. Place a distractor tense that matches a nearby noun's
temporal implication.

**Literary register variant:** Frame as discussion of a named literary work.
Target verb describes a character's action or the text's pattern. Correct
option: simple present. Wrong options: simple past, present perfect, past
perfect. Classify with `passage_tense_register_key: "literary_present"`.

#### `modifier_placement` / `dangling_modifier`

Start with a participial phrase whose logical subject is not the grammatical
subject.

#### `punctuation_comma`

Create a compound sentence with or without a coordinating conjunction. Test
FANBOYS comma, introductory phrase comma, or nonrestrictive element comma.

#### `semicolon_use`

Use two closely related independent clauses. Place a transitional phrase after
the semicolon zone.

#### `apostrophe_use`

Use a plural possessive or a possessive pronoun that looks like a contraction.

#### `appositive_punctuation`

Use a noun phrase that renames an adjacent noun. Test comma vs no comma for
essential vs nonessential appositive.

**Sub-pattern A — restrictive appositive:**
When an appositive uniquely identifies its antecedent, no punctuation
surrounds it. Example: "the chemical compound aluminum oxide" — no commas.

**Sub-pattern B — title/role noun before proper name:**
When a professional title immediately precedes a proper name as a restrictive
identifier, no comma separates them. Example: "plant cell biologist Yuree Lee."

**Sub-pattern C — coordinated restrictive appositive:**
Two restrictive appositives joined by "and" take no surrounding punctuation.
Example: "the writer and scholar James Baldwin."

Distractor pattern for restrictive sub-patterns:

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma before proper name after title/role | `punctuation_style_bias` |
| 2 | Commas around restrictive appositive | `grammar_fit_only` |
| 3 | Dash before restrictive appositive | `formal_register_match` |

#### `relative_pronouns`

Use a clause that is either essential or nonessential. Test `that` vs `which`
or comma placement.

#### `colon_dash_use`

Create a sentence where an independent clause is followed by an explanation,
list, or elaboration.

#### `conjunctive_adverb_usage`

Join two independent clauses with a conjunctive adverb.

#### `parallel_structure`

Create a list or correlative construction where one element breaks form
symmetry.

#### `pronoun_case`

Use a compound subject or object where pronoun case is tested.

#### `pronoun_clarity`

Create a sentence with multiple possible antecedents for a pronoun.

#### `possessive_contraction`

Use a context where `it's` vs `its` or `who's` vs `whose` is tested.

#### `hyphen_usage`

Use a compound modifier before a noun where hyphenation is required.

#### `logical_predication`

Create a sentence where the subject and predicate are grammatically possible
but logically incompatible.

#### `comparative_structures`

Create a comparison where the things being compared are not grammatically
parallel.

#### `unnecessary_internal_punctuation`

Insert a comma or dash at one of these five positions:
1. between subject and main verb
2. between transitive verb and its direct object
3. between verb and subject complement
4. between preposition and its noun complement
5. inside an integrated relative clause before the verb

Correct option: no punctuation at the target boundary.
Wrong options: comma, dash, or colon at the forbidden location.

#### `end_punctuation_question_statement`

**Variant A — indirect question embedded in declarative:**
Use a main clause like "The researchers wondered / asked / considered"
followed by a subordinate question clause. Correct: period. Wrong options:
question mark, comma with no end mark.

**Variant B — coordinated direct questions:**
Use two question clauses joined by "or" or "and." Correct: single question
mark. Wrong options: period, comma, question mark after each clause.

#### `finite_verb_in_relative_clause`

Construct a sentence where a relative clause (introduced by "which," "that,"
or "who") requires a finite verb. Wrong options substitute a nonfinite
participle or infinitive.

Template:
`[Noun phrase], which ______ [object or complement], [main verb phrase].`

Correct option: finite verb agreeing with the relative pronoun's antecedent.
Wrong options: nonfinite -ing participle, bare past participle, infinitive.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"`.

#### `finite_verb_in_main_clause`

Construct a sentence where the main clause requires a finite verb but wrong
options offer nonfinite forms. Common trigger: an opening subordinate clause
or participial phrase that tempts continued nonfinite structure.

Template:
`[Opening subordinate clause or participial phrase], [Subject] ______ [object].`

Correct option: finite present or past tense verb.
Wrong options: -ing participle, past participle without auxiliary, infinitive.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"`.

#### `modal_plus_plain_form`

Construct a sentence where a modal auxiliary (would, could, should, might,
must, will, can, shall) governs the main verb. Wrong options offer inflected
forms after the modal.

Template:
`[Subject] would/could/should/might ______ [object or complement].`

Correct option: plain (base) form of the verb.
Wrong options: third-person singular inflected, past tense, continuous.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "none"`.

#### `singular_event_reference` (pronoun)

Construct a sentence where the pronoun refers back to an entire preceding
event, fact, or clause. The pronoun must be singular ("this," "it," "that").
Wrong options offer plural pronouns or ambiguous pronouns.

Template:
`[Complete prior event stated as a sentence or clause]. ______ [effect or significance].`

Correct pronoun: singular "this," "it," or "that."
Wrong options: plural pronoun, ambiguous pronoun, pronoun with wrong case.

Annotation note: Use `grammar_role_key: "pronoun"`,
`grammar_focus_key: "pronoun_antecedent_agreement"`, and add to
`review_notes`: "antecedent is a full clause/event, not a noun."

### 20.4 Distractor Generation Heuristics by Grammar Focus

#### `subject_verb_agreement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Plural verb (nearest noun attraction) | `nearest_noun_attraction` |
| 2 | Singular verb but wrong tense | `auditory_similarity` |
| 3 | Compound or auxiliary verb that breaks agreement | `grammar_fit_only` |

#### `verb_tense_consistency`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Tense matching a nearby temporal noun | `temporal_sequence_ambiguity` |
| 2 | Present perfect when simple past is required | `formal_register_match` |
| 3 | Conditional/future that sounds sophisticated | `grammar_fit_only` |

#### `punctuation_comma`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Missing comma (comma splice or run-on) | `punctuation_style_bias` |
| 2 | Unnecessary comma (before essential clause) | `grammar_fit_only` |
| 3 | Semicolon where comma is correct | `formal_register_match` |

#### `semicolon_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma splice | `punctuation_style_bias` |
| 2 | Colon instead of semicolon | `formal_register_match` |
| 3 | Period that creates a fragment | `grammar_fit_only` |

#### `apostrophe_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | No apostrophe (plural instead of possessive) | `auditory_similarity` |
| 2 | Apostrophe after s (wrong singular possessive) | `nearest_noun_attraction` |
| 3 | Apostrophe in a pronoun (it's vs its) | `common_idiom_pull` |

#### `modifier_placement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Modifier placed next to wrong noun | `modifier_attachment_ambiguity` |
| 2 | Modifier split from its head noun | `grammar_fit_only` |
| 3 | Dangling modifier preserved | `formal_register_match` |

#### `relative_pronouns`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | `which` without comma for essential clause | `punctuation_style_bias` |
| 2 | `that` with comma for nonessential clause | `grammar_fit_only` |
| 3 | `who` for inanimate antecedent | `nearest_noun_attraction` |

#### `colon_dash_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma instead of colon/dash | `punctuation_style_bias` |
| 2 | Semicolon where colon is required | `formal_register_match` |
| 3 | No punctuation (run-on elaboration) | `grammar_fit_only` |

#### `appositive_punctuation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma around essential appositive | `punctuation_style_bias` |
| 2 | No comma around nonessential appositive | `grammar_fit_only` |
| 3 | Dash where comma is sufficient | `formal_register_match` |

#### `parallel_structure`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Gerund where infinitive is required | `grammar_fit_only` |
| 2 | Noun phrase where verb phrase is required | `nearest_noun_attraction` |
| 3 | Prepositional phrase that breaks parallelism | `formal_register_match` |

#### `pronoun_case`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Subject pronoun in object position | `nearest_noun_attraction` |
| 2 | Reflexive pronoun where simple object is required | `formal_register_match` |
| 3 | Possessive pronoun where object pronoun is required | `common_idiom_pull` |

#### `conjunctive_adverb_usage`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma only (comma splice) | `punctuation_style_bias` |
| 2 | Period before conjunctive adverb with lowercase | `grammar_fit_only` |
| 3 | Semicolon but no comma after adverb | `formal_register_match` |

#### `unnecessary_internal_punctuation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma between subject and verb | `punctuation_style_bias` |
| 2 | Dash between subject and verb | `formal_register_match` |
| 3 | Comma between verb and object/complement | `grammar_fit_only` |

#### `end_punctuation_question_statement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Question mark on an indirect question | `surface_similarity_bias` |
| 2 | Comma after the main clause, no end mark | `punctuation_style_bias` |
| 3 | Period on a coordinated direct question | `formal_register_match` |

### 20.5 Complete Generation Examples

*(See v3 base for full JSON examples A and B. Format is unchanged.)*

### 20.6 Pre-Output Validation Checklist

| # | Check | Failure action |
|---|---|---|
| 1 | `grammar_focus_key` belongs to `grammar_role_key` per §17.1 | Regenerate classification |
| 2 | Exactly 4 options exist | Regenerate all options |
| 3 | Exactly 1 option has `is_correct: true` | Regenerate options |
| 4 | No two distractors share the same `option_error_focus_key` | Regenerate one distractor |
| 5 | At least one distractor targets the declared `target_syntactic_trap_key` | Regenerate distractors |
| 6 | Correct option contains no grammar error | Regenerate correct option |
| 7 | Passage is 20–40 words for sentence-only items | Regenerate passage |
| 8 | Passage requires no outside knowledge | Regenerate passage |
| 9 | Register is formal academic; no contractions or slang | Regenerate passage |
| 10 | `difficulty_overall` matches declared target | Regenerate item |
| 11 | `target_frequency_band` is not `very_low` without justification | Reject or add justification |
| 12 | `disambiguation_rule_applied` is present if any label conflict exists | Add rule or set `needs_human_review: true` |
| 13 | `explanation_full` explains why every wrong option is wrong | Regenerate explanations |
| 14 | `generation_profile` includes all required fields from §19 | Add missing fields |
| 15 | All JSON keys are from approved lists; no invented keys | Replace or propose amendment |
| 16 | `evidence_span_text` follows format rules from §17.13 | Reformat |
| 17 | Option text format is consistent | Regenerate options |
| 18 | For `transition_logic` items, `transition_subtype_key` is present in classification and each option | Add subtype or `needs_human_review: true` |
| 19 | For `choose_best_notes_synthesis` items, `synthesis_goal_key`, `audience_knowledge_key`, and `required_content_key` are present | Add fields |
| 20 | For generated notes synthesis, `distractor_synthesis_failures` covers all three wrong options | Add missing failure modes |
| 21 | For `unnecessary_internal_punctuation` items, correct option has no punctuation at the target syntactic boundary | Regenerate correct option |
| 22 | For `end_punctuation_question_statement` items, correct option end mark matches sentence type | Regenerate correct option |
| 23 | For generated modules, `test_format_key` is present and module length matches (27 for digital, 33 for accommodation) | Add field or correct length |
| 24 | For `verb_form` items targeting finite vs nonfinite, generation pattern is one of: `finite_verb_in_relative_clause`, `finite_verb_in_main_clause`, `modal_plus_plain_form` | Reclassify or add pattern note |
| 25 | For `verb_tense_consistency` items in a literary passage, `passage_tense_register_key` is `literary_present` | Update tense register |

Maximum 3 retries per component. After 3 failures, abort and return an error
response.

### 20.7 Real-Time Constraints

Emit valid JSON on the first attempt ≥90% of the time. Complete generation
end-to-end in ≤3 reasoning steps. Never hallucinate an exam ID (use
`"GENERATED"`). Cache passage templates for identical `(grammar_focus_key,
syntactic_trap_key)` pairs.

### 20.8 No-Change Generation

~20% of official SAT grammar questions have the original text as the correct
answer. Generate a grammatically flawless passage; make option A the original
text (correct); distractors B, C, D each introduce a different grammar error.

### 20.9 Error Response Format

```json
{
  "error": {
    "error_code": "INVALID_FOCUS_KEY | ROLE_FOCUS_MISMATCH | VERY_LOW_FREQUENCY_UNJUSTIFIED | GENERATION_FAILURE | VALIDATION_FAILURE",
    "error_message": "Human-readable description.",
    "failed_component": "passage | stem | correct_option | distractor | metadata | validation",
    "retry_count": 3,
    "recommendation": "Suggested fix or fallback."
  }
}
```

### 20.10 Batch Generation Rules

Maximum batch size: 10 items. Items must not share the same
`(grammar_focus_key, syntactic_trap_key)` pair unless explicitly requested.
Vary `topic_broad` and `topic_fine`. Return array of complete item objects.
On failure after 3 retries, return the error for that item index and halt.

### 20.11 Topic Rotation and Deduplication

1. No two consecutive items may share the same `topic_broad`.
2. No two items within a 5-item window may share the same `topic_fine`.
3. If structural similarity exceeds 80% (same structure with only noun
   substitution), regenerate the passage.
4. Respect `avoid_recent_exam_ids` when provided.

### 20.12 Difficulty Calibration for Generation

| Difficulty | Trap intensity | Distractor plausibility | Passage complexity |
|---|---|---|---|
| `low` | `none` or `low` | Obviously wrong forms | Short sentence, common vocabulary |
| `medium` | `medium` | One strong distractor, two moderate | Standard academic vocabulary, one clause |
| `high` | `high` | All three plausible | Dense vocabulary, multiple clauses, unfamiliar topic |

### 20.13 Explanation Requirements for Generation

1. `explanation_short` ≤25 words, state the core rule.
2. `explanation_full` ≤150 words: why correct is correct; each wrong option
   by label with specific error; passage evidence when relevant.
3. For No-Change items, explicitly justify why the original text needs no
   correction.
4. For verb-form items, reference `passage_tense_register_key`.

### 20.14 Option Ordering Rules

Correct answer may appear in any position. Over 10+ items: 20–30% per
position. No module may have >40% correct answers in any single position.

### 20.15 Expanded Passage Generation Rules (All Focus Keys)

#### `sentence_fragment`

Subordinate clause presented as a complete sentence.

#### `comma_splice`

Two independent clauses joined with only a comma.

#### `run_on_sentence`

Two independent clauses fused with no punctuation or conjunction.

#### `noun_countability`

Mass noun with plural article or vice versa.

#### `determiners_articles`

Article where none is needed, or omitted required article.

#### `affirmative_agreement`

`so` / `neither` / `nor` responses with inverted auxiliary matching.

#### `voice_active_passive`

Active/passive voice creates ambiguity or inconsistency.

#### `negation`

Negation placed where scope ambiguity creates multiple interpretations.

#### `logical_predication`

Subject-predicate incompatibility.

#### `quotation_punctuation`

Comma placement with quotation marks.

---

## 21. SAT Realism and Distractor Competition Protocol

### 21.1 Core Principle

Hard SAT questions are difficult because distractors are close to correct,
wrong answers are attractive, elimination requires precise reasoning, and
multiple answers appear initially plausible. Difficulty must come from
distractor competition, not obscure vocabulary.

### 21.2 Distractor Distance Key

```json
{ "distractor_distance": "tight" }
```

Allowed values: `wide`, `moderate`, `tight`. `tight` required for realistic
hard SAT items.

### 21.3 Wrong-Answer Psychology Layer

Every distractor must include `student_failure_mode_key`.

Approved values:

**Reading-oriented:**
`nearest_noun_reflex`, `comma_fix_illusion`, `formal_word_bias`,
`longer_answer_bias`, `punctuation_intimidation`, `surface_similarity_bias`,
`scope_blindness`, `modifier_hitchhike`, `chronological_assumption`,
`extreme_word_trap`, `overreading`, `underreading`, `grammar_fit_only`,
`register_confusion`, `pronoun_anchor_error`, `parallel_shape_bias`,
`transition_assumption`, `idiom_memory_pull`, `false_precision`

**Grammar-specific (added v5):**
`internal_unit_punctuation_insertion` — student inserts comma or dash inside
a required syntactic unit (subject–verb, verb–object, preposition–complement)

`declarative_question_confusion` — student applies a question mark to a
sentence that contains an embedded indirect question but is itself declarative

`restrictive_appositive_comma_insertion` — student adds commas around a
restrictive appositive that requires none

`title_name_comma_insertion` — student inserts a comma between a title/role
noun and the proper name that follows it

`nonfinite_for_finite` — student chooses a participle or infinitive where a
finite verb is required in a main clause or relative clause

`inflected_after_modal` — student chooses a past-tense, third-person-singular,
or continuous form after a modal auxiliary

`plural_pronoun_for_clause_antecedent` — student chooses a plural pronoun when
the antecedent is an entire preceding clause or event

`past_tense_for_literary_present` — student uses simple past when discussing
events inside a literary work, which conventionally uses simple present

`transition_wrong_direction` — student chooses a transition word that signals
the opposite logical relationship (e.g., "however" for a result, "therefore"
for a contrast)

`notes_synthesis_wrong_goal` — student chooses a sentence that addresses the
right topic but performs a different rhetorical action than the stem requires

`notes_synthesis_audience_mismatch` — student chooses a sentence appropriate
for a familiar audience when the stem requires one for an unfamiliar audience,
or vice versa

`student_failure_mode_key` is mandatory for every distractor.

### 21.4 Distractor Competition Score

```json
{ "distractor_competition_score": 0.91 }
```

Minimum acceptable: 0.75. Preferred: 0.85+.

### 21.5 Answer Separation Strength

```json
{ "answer_separation_strength": "low" }
```

Official hard SAT items usually use `low`.

### 21.6 Plausible Wrong Count

```json
{ "plausible_wrong_count": 3 }
```

Preferred production target: 3.

---

## 22. Passage Architecture Templates

```json
{ "passage_architecture_key": "science_setup_finding_implication" }
```

Approved values:

- `science_setup_finding_implication`
- `science_hypothesis_method_result`
- `history_claim_evidence_limitation`
- `history_assumption_revision`
- `literature_observation_interpretation_shift`
- `literature_character_conflict_reveal`
- `economics_theory_exception_example`
- `economics_problem_solution_tradeoff`
- `rhetoric_claim_counterclaim_resolution`
- `notes_fact_selection_contrast`
- `experiment_hypothesis_control_result` — hypothesis, experimental group,
  control condition, predicted direction, observed outcome; enables
  support/weaken/inference items requiring correct group identification
- `indirect_effect_mediation` — initial condition, intermediate mediating
  variable, final outcome, explicit claim that effect operates through
  the mediator
- `alternative_explanation_ruled_out` — observed change, named alternative
  cause, control or finding that eliminates the alternative, remaining
  explanation
- `mechanism_manipulation_test` — observed phenomenon, candidate mechanism,
  experimental component replacement or manipulation, predicted result if
  causal, observed result
- `studied_subgroup_generalization_limit` — broad population, well-studied
  subgroup, evidence concentrated in the subgroup, explicit or implicit
  warning that results may not generalize

---

## 23. Ground Truth Comparison Layer

```json
{ "official_similarity_score": 0.93 }
```

Compared against PT1–PT6, Bluebook, and official released College Board items.
Production minimum: 0.82. Preferred: 0.90+.

---

## 24. Anti-Clone Protection

```json
{ "structural_similarity_score": 0.81, "rewrite_required": true }
```

If similarity > 0.75: regenerate passage.

---

## 25. Empirical Difficulty Calibration

```json
{ "empirical_difficulty_estimate": 0.64 }
```

Represents predicted miss rate.

---

## 26. Human Override Resolution Layer

```json
{
  "human_override_log": {
    "original_classification": "semicolon_use",
    "reviewer_change": "conjunctive_adverb_usage",
    "reason": "Semicolon required because conjunctive adverb follows."
  }
}
```

---

## 27. Generation Provenance and Audit Trail

```json
{
  "generation_provenance": {
    "source_template_used": "agreement_template_v2",
    "generation_chain": ["passage_generated", "distractors_generated", "validator_adjusted"]
  }
}
```

---

## 28. Robust Distractor Engineering Protocol

Each distractor must satisfy:

1. One distinct failure mode only
2. One identifiable student failure mechanism
3. No accidental second error
4. Plausible formal English
5. Must survive first-pass elimination
6. Must compete under time pressure
7. Must be wrong for a specific named reason

Each question must include a primary trap distractor, a formal-sounding wrong
answer, and a close semantic competitor. Best hard SAT distractors are almost
correct but not precise enough.

---

## 29. Final Validation Additions

Before output validate:

- `distractor_distance` present
- `student_failure_mode_key` present for every distractor
- `distractor_competition_score` >= 0.75
- `plausible_wrong_count` >= 2
- `answer_separation_strength` calibrated
- `passage_architecture_key` valid
- `official_similarity_score` >= threshold
- `structural_similarity_score` acceptable
- `empirical_difficulty_estimate` assigned
- provenance complete
- `transition_subtype_key` present for all `transition_logic` items
- `synthesis_goal_key`, `audience_knowledge_key`, `required_content_key`
  present for all `choose_best_notes_synthesis` items
- `test_format_key` present on all generated modules
- module question count matches `test_format_key`

If any fail: regenerate.

---

## 30. Transition Subtype Keys

### 30.1 `transition_subtype_key` field

Add to the classification schema for all `transition_logic` items:

```json
{ "transition_subtype_key": "causal_chain" }
```

This field is optional for annotation of legacy items but mandatory for
generation. For every transition distractor, annotate `transition_subtype_key`
with the wrong relationship the distractor signals.

### 30.2 Approved `transition_subtype_key` values

| Key | Canonical word(s) | Logical relationship |
|---|---|---|
| `sequence_final_event` | `finally`, `last`, `ultimately` (sequential) | The described step is last in an ordered process |
| `contrast_refutation` | `however`, `but`, `yet`, `still` | Refutes or contradicts the prior claim |
| `addition` | `additionally`, `furthermore`, `also`, `moreover` | Adds another supporting point |
| `result_consequence` | `therefore`, `thus`, `hence`, `as a result`, `consequently`, `for this reason`, `accordingly`, `as such` | Second statement follows causally from the first |
| `chronology` | `previously`, `later`, `then`, `next`, `afterward`, `subsequently` | Events or steps in time order |
| `alternative` | `instead`, `alternatively`, `rather`, `otherwise` | Substitutes one option for another |
| `emphasis_support` | `indeed`, `in fact`, `certainly` | Reinforces or intensifies the prior claim |
| `causal_chain` | `in turn` | Second event follows directly from the first as part of a causal sequence |
| `specificity_elaboration` | `specifically`, `in particular`, `namely` | Narrows or details a general claim |
| `purpose_action` | `to that end`, `to this end`, `for this purpose` | Describes an action taken to fulfill the preceding goal |
| `frequency_difference` | `more often`, `less often` | Emphasizes a relative frequency difference |
| `simultaneity` | `meanwhile`, `at the same time` | Two events or processes occur concurrently |
| `similarity` | `similarly`, `likewise` | Second claim parallels the first |
| `appropriateness` | `fittingly`, `aptly`, `appropriately` | Second statement is well-suited to the prior context |
| `change_over_time` | `increasingly`, `over time`, `progressively` | A trend or direction is developing |
| `exception` | `though`, `although`, `even so`, `nevertheless` | Marks a qualification or exception to the prior claim |
| `final_realization` | `ultimately` (non-sequential) | Describes what something comes down to or reveals in the end |
| `converse_opposite` | `conversely`, `on the other hand`, `by contrast`, `on the contrary` | States the opposite tendency to the prior claim |
| `present_continuation` | `currently`, `today`, `now`, `at present` | Shift from historical context to the present state |
| `direct_refutation` | `on the contrary` | Directly disputes an assumption or claim |
| `logical_consequence` | `as such`, `therefore`, `thus` | Logical inference from the preceding statement |
| `concession_qualification` | `admittedly`, `granted`, `to be sure` | Concedes a point before a counter-argument |
| `example` | `for example`, `for instance`, `to illustrate` | Specific instance of a general claim |

### 30.3 Generation requirement

```json
{
  "target_transition_subtype_key": "causal_chain",
  "distractor_transition_subtypes": [
    "contrast_refutation",
    "addition",
    "chronology"
  ]
}
```

---

## 31. Notes Synthesis Metadata

### 31.1 Required fields for all `choose_best_notes_synthesis` items

```json
{
  "synthesis_goal_key": "emphasize_similarity",
  "audience_knowledge_key": "audience_unfamiliar",
  "required_content_key": "comparison_needed"
}
```

Mandatory for generation. Recommended for annotation.

### 31.2 Approved `synthesis_goal_key` values

| Key | Description |
|---|---|
| `emphasize_similarity` | Highlight that two things share a feature |
| `emphasize_difference` | Highlight a contrast between two things |
| `explain_advantage` | State why one option is better than another |
| `explain_mechanism` | Describe how something works |
| `present_research` | Summarize a study for an unfamiliar reader |
| `present_theory` | Introduce a theory to an unfamiliar audience |
| `introduce_work` | Introduce a named literary or artistic work |
| `describe_work` | Describe what a work does or is about |
| `emphasize_achievement` | Highlight a named person's accomplishment |
| `make_generalization` | Draw a broad conclusion from the notes |
| `contrast_quantities` | Compare two numerical or measured values |
| `compare_measurements` | Compare lengths, sizes, masses, or other units |
| `emphasize_sample` | Highlight a specific representative example |
| `identify_category` | Name the classification group something belongs to |
| `identify_profession` | State a person's professional role or title |
| `identify_setting` | State where a story or work takes place |
| `identify_title` | Name the title of a work |
| `identify_year` | State when something was published, created, or completed |
| `identify_duration` | State how long something took or lasted |
| `identify_distance` | State a measured distance or range |
| `identify_author_pseudonym` | Reveal who wrote under a pen name |
| `contrast_structural_types` | Compare two structural or formal categories |
| `present_study_aim` | State what a study was trying to find out |
| `identify_statistical_method` | Name or describe the statistical approach used |
| `explain_technique_advantage` | Describe why a specific technique is useful |
| `explain_misconception_naming` | Explain why something is incorrectly named |
| `challenge_with_quotation` | Use a quotation from notes to dispute an explanation |
| `present_study_overview` | High-level summary of a study's design and result |
| `present_methodology` | Describe the methods used in a study |
| `present_study_conclusions` | State what a study found or concluded |
| `emphasize_significance` | State why a discovery or result matters |
| `explain_format_advantage` | Describe why a format or medium is useful |
| `emphasize_duration_and_purpose` | State both how long something took and why |
| `emphasize_size_similarity` | Highlight that two things are similar in size or scale |
| `contrast_origins` | Compare where two words, practices, or traditions came from |
| `provide_historical_overview` | Summarize the development of something over time |
| `contrast_formal_structures` | Compare formal or structural features (e.g., poetic meter) |
| `contextualize_changing_beliefs` | Situate a document or event within a shift in thinking |
| `compare_hypothesis_scope` | Contrast the breadth or narrowness of two hypotheses |
| `emphasize_age_similarity` | Note that two things are similar in age or date |

### 31.3 Approved `audience_knowledge_key` values

| Key | When to use |
|---|---|
| `audience_familiar` | Reader already knows a named source, author, or context |
| `audience_unfamiliar` | Reader needs identifying context (author name, work title, field, year) |
| `not_specified` | Audience assumption is not the distinguishing factor |

### 31.4 Approved `required_content_key` values

| Key | What the correct sentence must include |
|---|---|
| `comparison_needed` | At least one explicit comparison |
| `measurement_values_needed` | At least one specific number, unit, or measured value |
| `result_needed` | The outcome or finding |
| `title_and_content_needed` | Both the title of a work and a description |
| `achievement_needed` | A statement of what a person accomplished |
| `category_label_needed` | The name of the classification group |
| `sample_location_needed` | The specific example or location highlighted |
| `profession_label_needed` | The person's job title or field |
| `setting_needed` | The place or time setting of a work |
| `year_needed` | A specific year or date |
| `duration_needed` | A length of time |
| `distance_needed` | A measured distance |
| `author_identity_needed` | The real name of an author who used a pseudonym |
| `mechanism_needed` | A description of the causal or functional process |
| `structural_roles_needed` | Names of structural or formal elements being compared |
| `study_aim_needed` | The stated research question or objective |
| `statistical_method_needed` | The specific analytical approach |
| `misconception_needed` | The false belief that explains a name or label |
| `quotation_needed` | A direct quotation from the notes |
| `study_finding_summary_needed` | A summary of the result or conclusion |
| `method_needed` | A description of the procedure or approach |
| `conclusion_needed` | The conclusion reached |
| `significance_needed` | A statement of importance or impact |
| `advantage_needed` | A statement of why something is preferable |
| `purpose_needed` | A statement of intention or goal |
| `origin_labels_needed` | The named sources or languages of origin |
| `timeline_needed` | A sequence of events or developments |
| `formal_feature_labels_needed` | Specific names of structural or formal features |
| `scope_terms_needed` | Terms describing breadth or narrowness |

### 31.5 Wrong-option annotation for notes synthesis

For every notes synthesis distractor, annotate `synthesis_distractor_failure`:

| Value | Description |
|---|---|
| `wrong_goal` | Sentence does something other than what the stem requests |
| `omits_required_content` | On-topic but leaves out a required content element |
| `adds_background_audience_does_not_need` | Provides context the audience already has, or provides irrelevant background |
| `correct_topic_wrong_comparison` | Mentions the right subjects but states the wrong comparison, direction, or scope |

### 31.6 Generation requirement for notes synthesis

```json
{
  "target_synthesis_goal_key": "emphasize_similarity",
  "target_audience_knowledge_key": "audience_unfamiliar",
  "target_required_content_key": "comparison_needed",
  "distractor_synthesis_failures": [
    "wrong_goal",
    "omits_required_content",
    "correct_topic_wrong_comparison"
  ]
}
```

---

## Reference Quick-Index

| Concept | Section |
|---|---|
| Operating principles | 1 |
| Required output shape | 2 |
| Formal schemas | 2.1 |
| Question fields | 3 |
| stimulus_mode_key / stem_type_key values | 3.1, 3.2 |
| Approved values for undocumented fields | 3.3 |
| Classification fields | 4 |
| Grammar role keys | 5 |
| Grammar focus keys | 6 |
| Disambiguation rules | 7 |
| Decision tree | 8 |
| Syntactic trap keys | 9 |
| Option-level analysis | 10 |
| precision_score scale | 10.4 |
| grammar_fit / tone_match semantics | 10.5 |
| No-change rule | 11 |
| Multi-error rule | 12 |
| Tense/register (incl. literary_present) | 13 |
| Generation rules | 14 |
| Amendment process | 15 |
| Review flags | 16 |
| Schema guardrails | 17 |
| Role→focus mapping | 17.1 |
| Frequency table | 17.10 |
| Option text format rules | 17.11 |
| Difficulty calibration rubric | 17.12 |
| Evidence span selection rules | 17.13 |
| Explanation content requirements | 17.14 |
| Pilot corrections | 18 |
| Final output requirements | 19 |
| Real-time generation protocol | 20 |
| Generation input spec (incl. test_format_key) | 20.1 |
| Passage generation rules (incl. new verb/pronoun patterns) | 20.3 |
| Distractor heuristics (incl. new focus keys) | 20.4 |
| Validation checklist (checks 1–25) | 20.6 |
| No-Change generation | 20.8 |
| Error response format | 20.9 |
| Batch generation rules | 20.10 |
| Topic rotation / deduplication | 20.11 |
| Difficulty calibration for generation | 20.12 |
| Explanation requirements | 20.13 |
| Option ordering rules | 20.14 |
| Expanded passage generation rules | 20.15 |
| SAT realism / distractor competition | 21 |
| Student failure mode keys (incl. grammar-specific) | 21.3 |
| Passage architecture templates (incl. experimental) | 22 |
| Ground truth comparison | 23 |
| Anti-clone protection | 24 |
| Empirical difficulty calibration | 25 |
| Human override resolution | 26 |
| Generation provenance | 27 |
| Robust distractor engineering | 28 |
| Final validation additions | 29 |
| Transition subtype keys | 30 |
| Notes synthesis metadata | 31 |

---

*Document version: v5.0 — 2026-04-29*
*Merges: `rules_agent_dsat_grammar_ingestion_generation_v3.md` + `rules_agent_dsat_grammar_ingestion_generation_v3_1.md`*
*Agent: Claude Sonnet 4.6 (`claude-sonnet-4-6`)*
*Domain coverage: Standard English Conventions, Expression of Ideas*
*Companion file: `rules_agent_dsat_reading_v1.md` / `rules_agent_dsat_reading_v1_1.md`*
