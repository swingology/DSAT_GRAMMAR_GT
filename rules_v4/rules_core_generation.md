# DSAT Rules Core Generation Contract

## 1. Purpose

This file defines shared rules for DSAT Reading and Writing ingestion,
classification, validation, and generation. It is domain-neutral infrastructure.
It must be loaded before a domain module.

Core owns:
- top-level output shape
- shared question fields
- shared option fields
- stimulus/stem approved values
- passage quality, distractor engineering, SAT realism, difficulty, topic,
  provenance, anti-clone, amendment process, and validation lifecycle
- error and batch response formats

Core does not own:
- domain-specific taxonomy keys (`grammar_role_key`, `skill_family_key`, etc.)
- domain-specific stem families or passage constraints
- domain-specific distractor heuristics

**Source files**: This core contract is derived from shared infrastructure in:
- `rules_agent_dsat_grammar_ingestion_generetion_v7.md` Part A
- `rules_agent_dsat_reading_v2.md` §1-2

## 2. Core Operating Principles

For every item, separate these layers:
1. what the item tests
2. how the item is structured
3. what rule or reasoning mechanism solves it
4. why the correct answer is correct
5. why each wrong answer is tempting
6. why each wrong answer is wrong

**Controlled keys only.** Use approved lookup keys. If no key fits, output an
amendment proposal instead of inventing a production key.

**Evidence before invention.** The correct answer must be supportable from the
passage alone. If the passage does not provide enough information to justify
exactly one correct answer, rewrite the passage.

**No direct database writes.** The LLM emits JSON or markdown records; a
deterministic backend validator performs all database writes.

**One active domain module per item.** Do not mix grammar keys and reading keys
within a single item's classification.

## 3. Domain Selection

Classify the domain before filling domain-specific fields.

Approved domain families:
| Domain family | Covered by |
|---|---|
| Standard English Conventions | grammar module |
| Expression of Ideas, grammar-adjacent | grammar module |
| Information and Ideas | reading module |
| Craft and Structure | reading module |

Domain isolation rules:
- Information and Ideas and Craft and Structure must not use grammar taxonomy keys.
- SEC and grammar-adjacent Expression of Ideas must not use reading-only
  taxonomy keys.
- If a reading bucket contains Transitions, Rhetorical Synthesis, concision,
  register, or grammar-adjacent Expression of Ideas, route to the grammar
  module's Expression of Ideas handling.

## 4. Required Output Shape

Every accepted annotation or generated item must produce exactly this top-level
shape:

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

All generated DSAT multiple-choice items must include exactly four answer
options labeled A, B, C, and D, and exactly one correct option.

### 4.1 Shared Question Fields

```json
{
  "source_exam": "GENERATED | PT1 | null",
  "source_section": "RW | null",
  "source_module": "M1 | M2 | null",
  "source_question_number": 1,
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text",
  "prompt_text": "...",
  "passage_text": "...",
  "paired_passage_text": null,
  "notes_bullets": [],
  "table_data": null,
  "graph_data": null,
  "correct_option_label": "A",
  "explanation_short": "...",
  "explanation_full": "...",
  "evidence_span_text": "..."
}
```

### 4.2 Shared Classification Fields

```json
{
  "domain": "Standard English Conventions | Expression of Ideas | Information and Ideas | Craft and Structure",
  "skill_family": "Boundaries | Form, Structure, and Sense | ...",
  "subskill": "Free-text specific skill description",
  "question_family_key": "...",
  "evidence_scope_key": "sentence | paragraph | passage | paired_passage | table | graph | notes",
  "evidence_location_key": "main_clause | subordinate_clause | surrounding_sentence | opening_sentence | closing_sentence | transition_zone | data_zone | entire_passage",
  "answer_mechanism_key": "...",
  "solver_pattern_key": "...",
  "topic_broad": "science | history | literature | social_studies | arts | economics | technology | environment | humanities",
  "topic_fine": "marine biology",
  "reading_scope": "sentence-level | passage-level | cross-text | data-integrated",
  "reasoning_demand": "...",
  "register": "formal academic | neutral informational | academic informational",
  "tone": "neutral | objective | cautious | analytical",
  "difficulty_overall": "low | medium | high",
  "difficulty_reading": "low | medium | high",
  "difficulty_grammar": "low | medium | high",
  "difficulty_inference": "low | medium | high",
  "difficulty_vocab": "low | medium | high",
  "distractor_strength": "low | medium | high",
  "classification_rationale": "..."
}
```

### 4.3 Shared Reasoning Section

```json
{
  "primary_rule": "The rule, evidence mechanism, or skill that selects the correct answer.",
  "trap_mechanism": "How the primary wrong-answer trap misleads test-takers.",
  "correct_answer_reasoning": "Step-by-step justification for the correct option.",
  "distractor_analysis_summary": "One-sentence summary of why the three wrong options fail.",
  "similar_items": [
    {
      "pattern": "sentence, passage, or option template",
      "focus_key": "domain-specific focus key",
      "trap_key": "domain-specific trap key"
    }
  ]
}
```

## 5. Shared Stimulus Mode and Stem Type Approved Values

### 5.1 `stimulus_mode_key` values

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph` — confirmed graphic subtypes: bar chart, line graph,
  scatterplot, pie chart, map
- `notes_bullets`
- `poem`

### 5.2 `stem_type_key` values

Grammar and Expression of Ideas stems (grammar module):

- `complete_the_text`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`

Reading stems (reading module):

- `choose_best_support`
- `choose_best_illustration`
- `choose_best_weakener`
- `choose_best_completion_from_data`
- `choose_main_idea`
- `choose_detail`
- `most_logically_completes`
- `choose_word_in_context`
- `choose_main_purpose`
- `choose_sentence_function`
- `choose_text_relationship`
- `choose_agreement_across_texts`
- `choose_difference_across_texts`
- `choose_cross_text_connection`
- `choose_best_inference`
- `choose_command_of_evidence_textual`
- `choose_command_of_evidence_quantitative`

Shared stems (appear in both domains):

- `choose_structure_description`
- `choose_likely_response`
- `choose_best_quote`

## 6. Shared Passage and Stimulus Quality Rules

All passages must be:
- **Self-contained**: No outside knowledge is required.
- **Academic register**: No contractions, slang, or first person.
- **One unambiguous correct answer**: The passage must provide enough
  information to justify exactly one choice.
- **Formal and neutral**: No partisan, offensive, or trivially entertaining content.
- **Not trivia-dependent**: The grammar or reasoning should be testable without
  knowing facts about the topic.

Passage length by stimulus mode:
| Mode | Word count |
|---|---|
| `sentence_only` | 20–40 |
| `passage_excerpt` | 80–150 |
| `prose_single` | 100–200 |
| `prose_paired` | 80–120 each |

## 7. Shared Option Contract and Distractor Engineering Rules

Each option must include:

```json
{
  "option_label": "A",
  "option_text": "...",
  "is_correct": false,
  "option_role": "distractor",
  "distractor_type_key": "...",
  "semantic_relation_key": "...",
  "plausibility_source_key": "...",
  "option_error_focus_key": "...",
  "student_failure_mode_key": "...",
  "why_plausible": "...",
  "why_wrong": "...",
  "grammar_fit": "yes",
  "tone_match": "yes",
  "precision_score": 1,
  "distractor_distance": "moderate",
  "distractor_competition_score": 0.8
}
```

### 7.1 Correct Option Requirements
- `is_correct: true`
- `option_role: "correct"`
- `distractor_type_key: "correct"`
- `precision_score: 3`
- `why_wrong` may be omitted or set to null.

### 7.2 Distractor Engineering Rules
A distractor counts as functioning only if a reasonable but mistaken student
could select it for a specific articulable reason. Filler distractors fail
validation.

- **One named failure mode per distractor**: Every distractor must fail for
  exactly one primary reason. Do not create distractors that are wrong for
  multiple unrelated reasons; they are too easy to eliminate.
- **One plausibility source per distractor**: Every distractor must be tempting
  for a documented reason: vocabulary overlap, near-synonym appeal, partial
  truth, register match, local detail match, or structural resemblance.
- **One student failure mode per distractor**: Every distractor must include a
  `student_failure_mode_key` identifying the psychological mechanism causing
  students to select it (e.g., `nearest_noun_reflex`, `scope_blindness`,
  `surface_similarity_bias`).
- **No accidental second error**: A distractor that contains two unrelated
  errors is easier to eliminate than one with a single precise error. Do not
  introduce extra errors to make a distractor feel "more wrong."
- **Distractors must survive first-pass elimination**: Every wrong option must
  be plausible to a moderately skilled reader on first encounter.

## 8. SAT Realism Layer and Distractor Competition

Generated items should be hard because wrong answers compete, not because the
question is vague, the vocabulary is obscure, or the text is confusing.

Required realism fields for generation:

```json
{
  "distractor_distance": "wide | moderate | tight",
  "answer_separation_strength": "low | medium | high",
  "plausible_wrong_count": 3,
  "official_similarity_score": 0.9,
  "structural_similarity_score": 0.4,
  "rewrite_required": false,
  "empirical_difficulty_estimate": 0.64
}
```

### 8.1 Distractor Distance and Separation
- **`distractor_distance`**: `tight` means wrong answers are closely
  competitive. Required for `high` difficulty, preferred for `medium`.
- **`answer_separation_strength`**: `low` means multiple choices look
  competitive and only careful analysis resolves the conflict. Target `low` for
  hard items.
- **`distractor_competition_score`**: Minimum acceptable target is `0.75`;
  preferred is `0.85+`.

### 8.2 All-Four-Plausible Requirement
For `difficulty_overall: medium` or `high`:
- Every option—including all three wrong answers—must be plausible English when
  read in isolation.
- No option may be eliminated by ear-test alone.
- The correct answer must not "sound better" to a reader who has not applied the
  target rule.

### 8.3 Difficulty comes from reasoning, not obscurity
Hard SAT items are hard because the syntactic trap is deeply embedded, multiple
options seem equally good on first pass, elimination requires precise rule
application, and formal academic register makes all options "feel" right. Hard
items are NOT hard because vocabulary is rare, the topic is unfamiliar, the stem
is confusing, or the passage is ambiguous.

### 8.4 Approved Student Failure Modes

Shared (used in both grammar and reading domains):

- `nearest_noun_reflex`
- `comma_fix_illusion`
- `formal_word_bias`
- `longer_answer_bias`
- `punctuation_intimidation`
- `surface_similarity_bias`
- `scope_blindness`
- `modifier_hitchhike`
- `chronological_assumption`
- `extreme_word_trap`
- `overreading`
- `underreading`
- `grammar_fit_only`
- `register_confusion`
- `pronoun_anchor_error`
- `parallel_shape_bias`
- `transition_assumption`
- `idiom_memory_pull`
- `false_precision`

Grammar-specific (used in grammar module distractor heuristics):

- `ear_test_pass` — option sounds natural in speech but violates a written rule
- `tense_proximity_pull` — tense attracted by a nearby time-marker clause rather
  than the passage register
- `possessive_contraction_confusion` — student confuses possessive/contraction
  homophones (its/it's, whose/who's)

Reading-specific (used in reading module distractor heuristics):

- `local_detail_fixation` — student selects an option supported by a small
  detail but not the broader claim
- `overreach` — student selects an option that goes further than the passage supports
- `underreach` — student selects an option too narrow for the full claim
- `text_label_swap` — in cross-text items, student assigns an author's position
  to the wrong text
- `topic_association` — student selects an option merely because it mentions the
  same topic
- `inverse_logic` — student selects an option that inverts the passage's
  direction of argument
- `false_agreement` — in cross-text items, student assumes both texts agree when
  they do not
- `negation_blindness` — student misses a negative qualifier that reverses meaning
- `polarity_blindness` — student fails to detect that WIC option polarity
  conflicts with passage context
- `exact_value_misread` — student misreads a specific value in table/graph data
- `wrong_time_window` — student selects data from the wrong time period
- `individual_from_aggregate` — student draws individual-level conclusion from
  aggregate data
- `all_measures_not_checked` — student confirms one measure but not all relevant ones
- `subgroup_overgeneralization` — student extends subgroup finding to whole population
- `two_part_claim_partial_match` — student verifies only half of a two-part claim
- `control_group_misidentification` — student misidentifies which group is the control
- `parenthetical_function_confusion` — student misidentifies the function of a
  parenthetical element
- `connotation_surface_match` — student matches connotation without verifying
  denotation
- `rhetorical_verb_partial` — student selects a rhetorical verb that is partially
  correct but imprecise
- `evidence_scope_mismatch` — student cites evidence that supports a narrower or
  broader claim
- `wrong_comparison_direction` — student inverts the direction of a comparison

## 9. Generation Request Contract

Requests may target domain, difficulty, topics, focus keys, traps, passage
architecture, and option style. Reject a request if it asks for illegal key
combinations or maps a focus key to the wrong role.

```json
{
  "generation_request": {
    "domain": "grammar | reading",
    "target_question_family_key": "...",
    "target_focus_key": "...",
    "target_trap_key": "...",
    "target_stimulus_mode_key": "...",
    "target_stem_type_key": "...",
    "target_difficulty_overall": "low | medium | high",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "passage_architecture_key": "science_setup_finding_implication",
    "avoid_recent_exam_ids": ["PT4"],
    "generation_context": "Module needs one medium item."
  }
}
```

Approved shared `passage_architecture_key` values:
`science_setup_finding_implication`, `science_hypothesis_method_result`,
`history_claim_evidence_limitation`, `history_assumption_revision`,
`literature_observation_interpretation_shift`,
`literature_character_conflict_reveal`, `economics_theory_exception_example`,
`economics_problem_solution_tradeoff`, `rhetoric_claim_counterclaim_resolution`,
`notes_fact_selection_contrast`, `research_summary`,
`claim_evidence_explanation`, `unexpected_finding`, `cautionary_framing`,
`problem_solution`, `compare_contrast`, `chronological_sequence`

## 10. Common Generation Workflow

Execute in this exact order. Each step is blocking.

1. Validate request keys against core and selected domain.
2. Select domain module and reject cross-domain fields.
3. Build passage, sentence, data, notes, or paired text. Ensure correct answer
   is *required*, not merely plausible.
4. Build stem using approved stem wording.
5. Pre-answer before generating options.
6. Generate correct option.
7. Generate three distractors from explicit failure modes (no random associations).
8. Normalize option set for length, register, category, grammatical frame, and
   abstraction level.
9. Assemble metadata, reasoning, generation profile, provenance, and review.
10. Run core validation.
11. Run domain validation.
12. Retry the failed component, or return a structured error after three failed
    attempts.

## 11. Difficulty Targeting

Difficulty fields are not averaged. `difficulty_overall` reflects the dimension
that creates the most challenge.

To generate a harder item:
- Increase distractor closeness before increasing passage obscurity.
- Make wrong answers partially true or structurally appealing.
- Keep the correct answer precise but not visually signaled.
- Preserve one unambiguous correct answer.

To generate a focused item: target one domain focus key, target one primary trap
key, and keep passage topic and stem wording from creating a second hidden skill
test.

## 12. Anti-Clone, Diversity Controls, and Batching

Batch requirements (max batch size: 10 items):
- Vary `topic_broad` and `topic_fine`. No two consecutive items share `topic_broad`.
- No two items within a 5-item window share `topic_fine`.
- Avoid repeated `(focus_key, trap_key)` pairs.
- Distribute correct answer positions equally (A/B/C/D around 25% each).

Anti-Clone threshold:
- If `structural_similarity_score > 0.75` to any item in the anti-clone pool,
  regenerate the passage.
- If `avoid_recent_exam_ids` is provided, generated passages must not closely
  resemble items from those exams.

Batch response format:
```json
{
  "batch_results": [
    { "item_index": 0, "status": "success", "item": {} },
    { "item_index": 1, "status": "error", "error": {} }
  ]
}
```

## 13. Explanation Requirements

- `explanation_short`: <=25 words. States the core rule or evidence basis.
- `explanation_full`: <=150 words. Explains why the correct answer is correct
  and why *every* wrong option is wrong by label. Must reference the relevant
  passage evidence or target rule.

## 14. Review Object

```json
{
  "annotation_confidence": 0.95,
  "needs_human_review": false,
  "review_notes": "Any ambiguity, conflict, amendment, or validator concern.",
  "human_override_log": null
}
```

Set `needs_human_review: true` when classification depends on an unresolved
boundary, no approved key fits, the evidence is only plausible (not required),
or output needed >3 repairs.

## 15. Provenance and Audit Trail

Generated items must include:

```json
{
  "generation_provenance": {
    "source_template_used": "...",
    "generation_chain": ["request_validated", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated", "validator_adjusted"],
    "avoid_recent_exam_ids": [],
    "model_version": "rules_v4",
    "generation_timestamp": "..."
  }
}
```
Never hallucinate an official exam ID for synthetic content. Use `GENERATED`.

## 16. Amendment Process

If no approved key fits:

```json
{
  "amendment_proposal": {
    "proposed_key": "...",
    "proposed_parent_key": "...",
    "reason": "...",
    "evidence_text": "...",
    "status": "proposed",
    "frequency_estimate": "very_low | low | medium | high | very_high",
    "example_count": 0,
    "examples": []
  }
}
```

`proposed_parent_key` must be an existing `grammar_role_key` (for grammar
amendments) or `skill_family_key` (for reading amendments), or a new parent
proposal with justification. `evidence_text` must quote the exact item text that
triggered the proposal. `frequency_estimate` predicts how often this pattern
appears on official SATs. `example_count` tracks how many observed items support
the proposal. Both `frequency_estimate` and `example_count` are required.

Do not insert proposed keys into production records until reviewed and promoted
to `approved`.

## 17. Error Response

```json
{
  "error": {
    "error_code": "INVALID_KEY | DOMAIN_MISMATCH | ROLE_FOCUS_MISMATCH | VERY_LOW_FREQUENCY_UNJUSTIFIED | GENERATION_FAILURE | VALIDATION_FAILURE",
    "error_message": "Human-readable description.",
    "failed_component": "passage | stem | correct_option | distractor | validation",
    "retry_count": 3
  }
}
```

## 18. `precision_score` Scale

| Value | Meaning |
|---|---|
| `1` | Incorrect option. Contains a clear error (grammar, logic, scope, attribution, evidence). |
| `2` | Partially acceptable but inferior. Grammatically or logically valid in isolation but less effective than the correct answer (e.g., a period where a semicolon is better, or a word that fits but is less precise). |
| `3` | Correct option. Fully satisfies the tested rule or evidence requirement with no compromise. |

Only the correct option may have `precision_score: 3`. Distractors must have
`precision_score: 1` or, in rare cases, `precision_score: 2`.

## 19. Difficulty Calibration Rubric

Use this rubric to assign `difficulty_overall` and sub-difficulty fields:

| Dimension | `low` | `medium` | `high` |
|---|---|---|---|
| `difficulty_reading` | Common vocabulary, short sentences, familiar topic | Some academic vocabulary, compound sentences, neutral topic | Dense academic prose, embedded clauses, unfamiliar topic |
| `difficulty_grammar` | Single, visible rule application | Rule requires cross-sentence parsing or trap navigation | Multiple rules interact, or trap is deeply embedded |
| `difficulty_inference` | No inference required; answer is directly in the text | One-step inference (e.g., register shift) | Multi-step inference combining grammar and rhetoric |
| `difficulty_vocab` | All words below 10th-grade level | Some words at 11th-12th grade or academic register | Rare words, technical terms, or archaic usage |
| `distractor_strength` | Distractors are obviously wrong on inspection | One distractor is tempting; others are moderate | All three distractors are plausible on first read |

`difficulty_overall` is not an average. It reflects the dimension that creates
the most challenge. A sentence with easy reading but a high-strength trap is
`medium` or `high` overall.

## 20. Core Validation Lifecycle

Validation runs in two phases:
1. **Core validation** (this checklist): output shape, shared distractor rules,
   realism thresholds, anti-clone checks.
2. **Domain validation** (domain module): focus key mapping, trap coverage,
   domain-specific distractor heuristics.

### Core Validator Checklist:
- [ ] Top-level sections present
- [ ] Exactly four options
- [ ] Exactly one option is correct (`is_correct: true`, `precision_score: 3`)
- [ ] No distractor has `precision_score: 3`
- [ ] Every distractor has `why_plausible`, `why_wrong`,
  `student_failure_mode_key`, and `plausibility_source_key`
- [ ] No two distractors fail for the exact same reason
- [ ] All options share the same format, register, and grammatical frame
- [ ] All options produce plausible English sentences (no elimination by
  ear-test alone)
- [ ] `explanation_short` and `explanation_full` satisfy length and content
  requirements
- [ ] Difficulty fields, `distractor_distance`, and `plausible_wrong_count` are
  present and calibrated
- [ ] `classification_rationale` is present
- [ ] `structural_similarity_score` < 0.75
- [ ] Generation provenance is complete
- [ ] No unapproved keys are used
- [ ] One and only one domain module's taxonomy appears in the final item
