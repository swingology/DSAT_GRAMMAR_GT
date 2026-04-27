# DSAT Rules Core Generation Contract

## 1. Purpose

This file defines shared rules for DSAT Reading and Writing ingestion,
classification, validation, and generation. It is domain-neutral infrastructure.
It must be loaded before a domain module.

Core owns:

- top-level output shape
- shared question fields
- shared option fields
- generation request controls
- difficulty, topic, realism, provenance, anti-clone, and validation lifecycle
- error and batch response formats

Core does not own:

- `grammar_role_key`
- `grammar_focus_key`
- `syntactic_trap_key`
- `skill_family_key`
- `reading_focus_key`
- `reasoning_trap_key`
- `text_relationship_key`
- domain-specific stem families or passage constraints

## 2. Operating Principles

For every item, separate these layers:

1. what the item tests
2. how the item is structured
3. what rule or reasoning mechanism solves it
4. why the correct answer is correct
5. why each wrong answer is tempting
6. why each wrong answer is wrong
7. what pattern could generate a similar item

Use controlled keys only. If no approved key fits, output an amendment proposal
instead of inventing a production key.

Do not write directly to the database. The LLM emits JSON or markdown records;
the backend validator decides whether they can be persisted.

Difficulty must come from reasoning competition, not trivia, ambiguity,
malformed distractors, or obscure vocabulary.

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

- Information and Ideas and Craft and Structure must not use grammar taxonomy
  keys.
- SEC and grammar-adjacent Expression of Ideas must not use reading-only
  taxonomy keys.
- If a stem appears grammar-like but the correct answer requires evidence,
  purpose, word meaning, or cross-text comparison, use the reading module.
- If a reading bucket contains Transitions, Rhetorical Synthesis, concision,
  register, or grammar-adjacent Expression of Ideas, route to the grammar
  module's Expression of Ideas handling.

## 4. Required Output Shape

Every accepted annotation or generated item must produce:

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

## 5. Shared Question Fields

```json
{
  "source_exam": "PT4 | PT1 | GENERATED | null",
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

Shared `stimulus_mode_key` values:

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `notes_bullets`
- `poem`

Domain modules restrict which modes and stems are legal for a given skill.

## 6. Shared Classification Fields

These fields can appear in either domain when applicable:

```json
{
  "domain": "Standard English Conventions | Expression of Ideas | Information and Ideas | Craft and Structure",
  "question_family_key": "...",
  "evidence_scope_key": "sentence | paragraph | passage | paired_passage | table | graph | notes",
  "evidence_location_key": "main_clause | subordinate_clause | surrounding_sentence | opening_sentence | closing_sentence | transition_zone | data_zone | entire_passage",
  "answer_mechanism_key": "...",
  "solver_pattern_key": "...",
  "topic_broad": "science",
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

Shared topic controls:

- `topic_broad`: `science`, `history`, `literature`, `social_studies`,
  `arts`, `economics`, `technology`, `environment`
- `topic_fine`: free-text subtopic under `topic_broad`

## 7. Shared Reasoning Section

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

## 8. Shared Option Contract

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

Correct option requirements:

- `is_correct: true`
- `option_role: "correct"`
- `distractor_type_key: "correct"`
- `precision_score: 3`
- `why_wrong` may be omitted or set to null

Distractor requirements:

- exactly three wrong options
- each has one primary failure mode
- each has one plausibility source
- each has a specific `why_plausible`
- each has a specific `why_wrong`
- no two distractors should fail for the exact same reason
- no distractor may contain an accidental second error that makes it obviously
  inferior

`precision_score` scale:

| Value | Meaning |
|---|---|
| `1` | Incorrect; clear rule, logic, scope, attribution, evidence, or fit error |
| `2` | Partially acceptable but inferior; rare for distractors |
| `3` | Correct; fully satisfies the target rule or evidence requirement |

Only the correct option may have `precision_score: 3`.

## 9. Realism and Distractor Competition

Generated items should be hard because wrong answers compete, not because the
question is vague.

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

Targets:

- `tight` distractor distance is expected for high-difficulty items.
- `distractor_competition_score` minimum acceptable target is `0.75`;
  preferred is `0.85+`.
- `plausible_wrong_count` should be `3`; minimum acceptable is `2` only for
  review-mode drafts.
- `official_similarity_score` target is `0.82+`; preferred is `0.90+`.
- If `structural_similarity_score > 0.75`, regenerate the passage or option
  structure.

Approved `student_failure_mode_key` values:

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

Generation must reject:

- answer sets with one visibly longer or more polished correct answer
- one option in a different grammatical form or semantic category
- one option that directly answers the stem while others do not
- "all of the above" or "none of the above"
- bizarre, joke-like, or filler distractors

## 10. Generation Request Contract

Generation requests may target domain, difficulty, topics, focus keys, traps,
passage architecture, and option style. A request must be rejected if it asks for
illegal key combinations.

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
    "target_difficulty_reading": "low | medium | high",
    "target_difficulty_grammar": "low | medium | high",
    "target_difficulty_inference": "low | medium | high",
    "target_difficulty_vocab": "low | medium | high",
    "target_distractor_strength": "low | medium | high",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "passage_architecture_key": "science_setup_finding_implication",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs one medium item targeting this focus."
  }
}
```

Approved shared `passage_architecture_key` values:

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
- `research_summary`
- `claim_evidence_explanation`
- `unexpected_finding`
- `cautionary_framing`
- `problem_solution`
- `compare_contrast`
- `chronological_sequence`

Domain modules define additional required generation request fields.

## 11. Generation Workflow

Generate in this order. Each step is blocking.

1. Validate request keys against core and selected domain.
2. Select domain module and reject cross-domain fields.
3. Build passage, sentence, data, notes, or paired text.
4. Build stem using approved stem wording.
5. Pre-answer before generating options.
6. Generate correct option.
7. Generate three distractors from explicit failure modes.
8. Normalize option set for length, register, category, grammatical frame, and
   abstraction level.
9. Assemble metadata, reasoning, generation profile, provenance, and review.
10. Run core validation.
11. Run domain validation.
12. Retry the failed component, or return a structured error after three failed
    attempts.

## 12. Difficulty Targeting

Difficulty fields are not averaged. `difficulty_overall` reflects the dimension
that creates the most challenge.

General anchors:

| Level | Reading / passage | Rule or evidence demand | Distractors |
|---|---|---|---|
| `low` | direct, short, familiar | one visible rule or direct evidence span | mostly obvious |
| `medium` | one inference or moderate syntax | one trap or distributed clue | one strong distractor |
| `high` | dense, indirect, multi-part | multiple constraints or subtle evidence | all three plausible |

To generate a harder item:

- increase distractor closeness before increasing passage obscurity
- make wrong answers partially true or structurally appealing
- keep the correct answer precise but not visually signaled
- preserve one unambiguous correct answer

To generate a focused item:

- target one domain focus key
- target one primary trap key
- document secondary keys only when they are actually present
- keep passage topic and stem wording from creating a second hidden skill test

## 13. Explanation Requirements

Generated and ingested items must include:

- `explanation_short`: at most 25 words; states the core rule or evidence basis
- `explanation_full`: at most 150 words; explains why the correct answer is
  correct and why every wrong option is wrong by label

For generated items, `explanation_full` must reference the relevant passage
evidence or target rule. Domain modules add extra requirements.

## 14. Review Object

```json
{
  "annotation_confidence": 0.95,
  "needs_human_review": false,
  "review_notes": "Any ambiguity, conflict, amendment, or validator concern.",
  "human_override_log": null
}
```

Set `needs_human_review: true` when:

- classification depends on an unresolved domain boundary
- no approved key fits
- evidence is only plausible rather than required
- the answer set may have two defensible correct answers
- generated output needed more than three repair attempts

## 15. Provenance and Audit Trail

Generated items must include:

```json
{
  "generation_provenance": {
    "source_template_used": "template_key_or_description",
    "generation_chain": [
      "request_validated",
      "passage_generated",
      "stem_generated",
      "correct_option_generated",
      "distractors_generated",
      "validator_adjusted"
    ],
    "avoid_recent_exam_ids": [],
    "validator_interventions": [],
    "model_version": "rules_v2"
  }
}
```

Never hallucinate an official exam ID for synthetic content. Use `GENERATED`.

## 16. Batch Generation

Maximum batch size: 10 items.

Batch requirements:

- vary `topic_broad` and `topic_fine`
- avoid repeated `(focus_key, trap_key)` pairs unless explicitly requested
- distribute correct answer positions over 10+ items:
  - A: 20-30%
  - B: 20-30%
  - C: 20-30%
  - D: 20-30%
- no module should have more than 40% of correct answers in one position

Batch response:

```json
{
  "batch_results": [
    { "item_index": 0, "status": "success", "item": {} },
    { "item_index": 1, "status": "error", "error": {} }
  ]
}
```

If an item fails after three retries, return the error for that item index and
halt the batch unless the caller explicitly allows partial success.

## 17. Amendment Process

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

Do not use proposed keys in production fields until approved.

## 18. Error Response

```json
{
  "error": {
    "error_code": "INVALID_KEY | DOMAIN_MISMATCH | ROLE_FOCUS_MISMATCH | VERY_LOW_FREQUENCY_UNJUSTIFIED | GENERATION_FAILURE | VALIDATION_FAILURE",
    "error_message": "Human-readable description of the failure.",
    "failed_component": "domain | passage | stem | correct_option | distractor | metadata | validation",
    "retry_count": 3,
    "recommendation": "Suggested fix or fallback action."
  }
}
```

## 19. Core Validator Checklist

Before output:

- [ ] top-level sections are present
- [ ] exactly four options exist
- [ ] exactly one option is correct
- [ ] correct option has `precision_score: 3`
- [ ] no distractor has `precision_score: 3`
- [ ] every distractor has `why_plausible` and `why_wrong`
- [ ] every distractor has a named failure mode and plausibility source
- [ ] all options share the same format, category, register, and grammatical
      frame
- [ ] `explanation_short` and `explanation_full` satisfy length and content
      requirements
- [ ] `classification_rationale` is present
- [ ] difficulty fields are populated
- [ ] generation provenance is complete for generated items
- [ ] no unapproved keys are used
- [ ] one and only one domain module's taxonomy appears in the final item

