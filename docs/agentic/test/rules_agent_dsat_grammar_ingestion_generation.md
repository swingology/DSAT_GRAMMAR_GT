# rules_agent.md — DSAT Grammar Ingestion and Generation Rules

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
- `correct`
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

### 10.3 Grammar-specific plausibility sources
- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`

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
    "status": "proposed"
  }
}
```

Do not insert proposed keys into production records until reviewed.

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

## 17. Final Output Requirements

The agent must return:
- valid JSON only when used in ingestion mode
- no invented lookup keys
- exactly four answer options for SAT multiple-choice items
- exactly one correct option
- `grammar_focus_key` only when appropriate
- `option_error_focus_key` for grammar distractors when possible
- `generation_profile` for every ingested item

The agent must not directly write SQL. The backend validator converts approved JSON into database writes.

