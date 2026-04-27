# DSAT Grammar Module v2

## 1. Scope

Load this file after `rules_core_generation.md` when the item belongs to:

- Standard English Conventions
- grammar-adjacent Expression of Ideas
- Transitions, Rhetorical Synthesis, concision, register, precision, or
  data-claim accuracy when the item is handled by the grammar V3 taxonomy

This module owns grammar classification, grammar focus keys, grammar
disambiguation, syntactic traps, grammar option analysis, grammar generation,
and grammar validation.

This module does not own Information and Ideas or Craft and Structure reading
classification. Those domains must use `rules_dsat_reading_module.md`.

Source authority:

- This module reorganizes the proven root grammar source; it does not narrow
  that source.
- The root `rules_agent_dsat_grammar_ingestion_generation_v3.md` and existing
  backend validator behavior remain compatibility references.
- If this module is silent about a proven grammar behavior, preserve the root
  source behavior rather than inventing a new rule.

## 2. Domain Boundary

Use grammar taxonomy when the correct answer is required by:

- grammar
- punctuation
- sentence structure
- agreement
- verb form
- modifier logic
- pronoun logic
- parallel structure
- grammar-adjacent Expression of Ideas

Do not force a reading item into grammar just because the passage contains
grammar-like wording. Classify by the cognitive skill needed to choose the
correct answer.

Expression of Ideas handling:

- If the item tests transition logic, concision, register, rhetorical synthesis,
  precision, emphasis, or data-claim accuracy, classify as Expression of Ideas.
- `grammar_role_key` may be `expression_of_ideas` only when the item is
  grammar-adjacent.
- If Expression of Ideas has no grammar relevance, `grammar_role_key` may be
  null or omitted, but the item still routes through this module rather than the
  reading module.

## 3. Grammar Question Fields

Common grammar-compatible `stem_type_key` values:

- `complete_the_text`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`

Grammar-compatible `stimulus_mode_key` values for ingestion:

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `notes_bullets`
- `prose_plus_table`
- `prose_plus_graph`
- `poem`

Recommended grammar generation modes:

- `sentence_only`
- `passage_excerpt`
- `notes_bullets`
- `prose_plus_table`
- `prose_plus_graph`

Use `prose_single`, `prose_paired`, or `poem` in generation only when the
request explicitly asks for a grammar or Expression of Ideas item embedded in
that stimulus format. Do not reject those modes during ingestion solely because
they are uncommon for grammar.

Default grammar stem wording:

> Which choice completes the text so that it conforms to the conventions of
> Standard English?

For revision questions, the stem must explicitly name the revision goal.
For no-change questions, the stem must not imply that an error exists.

## 4. Classification Fields

Grammar outputs use this classification shape:

```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Sentence Boundaries",
  "subskill": "sentence boundary with interruption",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "sentence_boundary",
  "grammar_focus_key": "comma_splice",
  "secondary_grammar_focus_keys": [],
  "syntactic_trap_key": "interruption_breaks_subject_verb",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "disambiguation_rule_applied": "sentence_boundary > punctuation",
  "classification_rationale": "The correct option repairs a comma splice."
}
```

Approved `question_family_key` values in this module:

- `conventions_grammar`
- `expression_of_ideas`

For `question_family_key: "expression_of_ideas"`, `grammar_role_key` may be
`expression_of_ideas` when grammar-adjacent, or null/omitted when the item is
Expression of Ideas but not grammar-adjacent. In both cases, keep the item in
this module rather than routing it to the reading module.

Approved `answer_mechanism_key` values:

- `rule_application`
- `pattern_matching`
- `evidence_location`
- `inference`
- `data_synthesis`

Approved `solver_pattern_key` values:

- `apply_grammar_rule_directly`
- `locate_error_zone`
- `compare_register`
- `evaluate_transition`
- `synthesize_notes`
- `eliminate_by_boundary`

## 5. Grammar Role Keys

Approved `grammar_role_key` values:

- `sentence_boundary`
- `agreement`
- `verb_form`
- `modifier`
- `punctuation`
- `parallel_structure`
- `pronoun`
- `expression_of_ideas`

Use `sentence_boundary` for fragments, run-ons, comma splices, and decisions
about whether sentence units are correctly joined or separated.

Use `agreement` for subject-verb agreement, pronoun-antecedent agreement,
countability, number agreement, and determiner/article issues where number or
specificity is central.

Use `verb_form` for tense consistency, finite/nonfinite verbs, gerunds,
infinitives, voice, mood, conditional logic, and scientific/general present.

Use `modifier` for dangling modifiers, misplaced modifiers, modifier scope,
comparative structures, and logical predication when subject-predicate
compatibility is central.

Use `punctuation` for comma mechanics, semicolons, colons, dashes, apostrophes,
appositives, quotation punctuation, and hyphens.

Use `parallel_structure` for parallel lists, correlative conjunctions,
comparison symmetry, and elliptical constructions.

Use `pronoun` for pronoun case, clarity, and ambiguous reference.

Use `expression_of_ideas` for grammar-adjacent concision, register, transition
logic, precision, data-claim accuracy, rhetorical effectiveness, and emphasis.

## 6. Grammar Focus Keys

Use the most specific applicable `grammar_focus_key`.

Sentence boundary:

- `sentence_fragment`
- `comma_splice`
- `run_on_sentence`
- `sentence_boundary`

Agreement:

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`
- `affirmative_agreement`

Pronoun:

- `pronoun_case`
- `pronoun_clarity`
- `pronoun_antecedent_agreement`

Verb form:

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation`

Modifier:

- `modifier_placement`
- `comparative_structures`
- `logical_predication`
- `relative_pronouns`

Punctuation:

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`

Parallel structure:

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

Expression of Ideas:

- `redundancy_concision`
- `precision_word_choice`
- `register_style_consistency`
- `logical_relationships`
- `emphasis_meaning_shifts`
- `data_interpretation_claims`
- `transition_logic`

## 7. Role to Focus Mapping

The agent must never emit a `grammar_focus_key` outside the declared
`grammar_role_key`.

| `grammar_role_key` | Allowed `grammar_focus_key` values |
|---|---|
| `sentence_boundary` | `sentence_fragment`, `comma_splice`, `run_on_sentence`, `sentence_boundary` |
| `agreement` | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`, `determiners_articles`, `affirmative_agreement` |
| `verb_form` | `verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation` |
| `modifier` | `modifier_placement`, `comparative_structures`, `logical_predication`, `relative_pronouns` |
| `punctuation` | `punctuation_comma`, `colon_dash_use`, `semicolon_use`, `conjunctive_adverb_usage`, `apostrophe_use`, `possessive_contraction`, `appositive_punctuation`, `hyphen_usage`, `quotation_punctuation` |
| `parallel_structure` | `parallel_structure`, `elliptical_constructions`, `conjunction_usage` |
| `pronoun` | `pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement` |
| `expression_of_ideas` | `redundancy_concision`, `precision_word_choice`, `register_style_consistency`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `transition_logic` |

If the focus cannot be mapped, propose an amendment.

## 8. Disambiguation Rules

Apply these priority rules whenever multiple labels seem possible:

1. `sentence_boundary` > general `punctuation`
2. `logical_predication` > `modifier_placement`, `comparative_structures`,
   `parallel_structure`, `conjunction_usage`
3. `transition_logic` > `conjunction_usage`, `parallel_structure`
4. `conjunctive_adverb_usage` > general `punctuation`, `conjunction_usage`
5. `negation` > `logical_predication`, `parallel_structure`,
   `modifier_placement`, `verb_form`
6. `pronoun_case` > `pronoun_antecedent_agreement`
7. `pronoun_clarity` > `pronoun_antecedent_agreement`
8. `comparative_structures` > `parallel_structure`, `modifier_placement`
9. `voice_active_passive` > general `verb_form`
10. `noun_countability` > `subject_verb_agreement`
11. `relative_pronouns` > `modifier_placement`
12. `possessive_contraction` > `apostrophe_use`
13. `hyphen_usage` > general `punctuation`, `modifier_placement`
14. idiom-like conjunction usage > general `conjunction_usage`

`preposition_idiom` is not an approved production focus key in the source list.
If an idiom/preposition case cannot be represented by an approved focus key,
propose an amendment rather than emitting `preposition_idiom`.

Whenever a conflict is resolved, write the exact rule in
`disambiguation_rule_applied`. If no listed rule resolves the conflict, set
`needs_human_review: true`.

## 9. Grammar Decision Tree

1. Is the answer selected because of grammar, punctuation, sentence structure,
   or usage? If yes, use `conventions_grammar`.
2. Is the item transition logic, notes synthesis, concision, register, or
   rhetorical goal? If yes, use `expression_of_ideas`.
3. Does the issue join or separate sentence units? Use sentence-boundary keys.
4. Does punctuation decide the answer without sentence-boundary logic? Use the
   specific punctuation focus.
5. Does agreement decide the answer? Use an agreement focus.
6. Does verb tense, form, voice, mood, or negation decide the answer? Use a
   verb-form focus.
7. Does modifier attachment, comparison, relative-pronoun logic, or predicate
   compatibility decide the answer? Use a modifier focus.
8. Does pronoun case or reference decide the answer? Use a pronoun focus.
9. Does form symmetry decide the answer? Use `parallel_structure`.
10. If multiple rules appear, identify the primary rule that eliminates the
    most wrong options and store other visible rules in
    `secondary_grammar_focus_keys`.

## 10. Syntactic Trap Keys

Use `syntactic_trap_key` for the mechanism that makes the grammar decision hard.

Approved values:

- `nearest_noun_attraction`
- `interruption_breaks_subject_verb`
- `modifier_attachment_ambiguity`
- `garden_path`
- `nominalization_obscures_subject`
- `long_distance_dependency`
- `scope_of_negation`
- `parallel_shape_bias`
- `punctuation_style_bias`
- `none`

Generation profiles must also include:

```json
{
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "low | medium | high"
}
```

## 11. Grammar Option Analysis

For grammar distractors, populate `option_error_focus_key` with a specific
grammar focus key whenever possible.

Required specificity examples:

| Wrong option surface error | Forbidden general label | Required `option_error_focus_key` |
|---|---|---|
| wrong semicolon | `punctuation_error` | `semicolon_use` |
| wrong apostrophe | `punctuation_error` | `apostrophe_use` |
| wrong tense | `grammar_error` | `verb_tense_consistency` |
| wrong relative clause | `grammar_error` | `relative_pronouns` |
| comma splice | `grammar_error` | `comma_splice` |
| dangling modifier | `grammar_error` | `modifier_placement` |

Approved grammar distractor type keys:

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
- `correct`

Approved grammar plausibility source keys:

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`
- `surface_similarity_bias`
- `transition_assumption`
- `register_confusion`

`grammar_fit` semantics:

- `yes`: the option is grammatically possible in some context, even if it fails
  the tested rule or the current passage.
- `no`: the option contains a clear grammar error that makes it impossible in
  standard usage.

`tone_match` semantics:

- `yes`: formal or neutral academic register is preserved.
- `no`: slang, contractions, colloquial wording, or register shift appears.

## 12. No-Change and Original-Text Rule

When original passage wording appears as one option, populate:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

No-change generation rules:

1. Generate a grammatically flawless passage with no error at the target zone.
2. Make option A the original text and the correct option unless a caller
   explicitly requests a different no-change position for experiment-only
   generation.
3. The three distractors each introduce a different grammar error.
4. The stem must be neutral and must not assume an error exists.
5. `explanation_full` must explicitly justify why no change is needed.

No-change generation requests use:

```json
{
  "is_no_change_target": true,
  "no_change_position": "A"
}
```

No-change items are common enough to be supported deterministically. The source
rules target roughly 20% of official-style grammar items as original-text
correct when a batch requests no-change coverage.

## 13. Multi-Error Rule

When more than one grammar concept is visible:

1. Store the primary rule in `grammar_focus_key`.
2. Store other visible rules in `secondary_grammar_focus_keys`.
3. Store each wrong option's specific error in `option_error_focus_key`.
4. Do not leave `secondary_grammar_focus_keys` empty when a secondary rule is
   visibly present.

The primary rule is the rule that most directly explains why the correct answer
is required or eliminates the largest number of wrong options.

## 14. Verb-Form Tense/Register Metadata

For `grammar_role_key: "verb_form"` or focus keys `verb_tense_consistency`,
`verb_form`, or `voice_active_passive`, output:

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

Approved `passage_tense_register_key` values:

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`

Approved `expected_tense_key` values:

- `simple_present`
- `simple_past`
- `present_perfect`
- `past_perfect`
- `future`
- `conditional`
- `subjunctive`
- `imperative`

If the register cannot be determined, set `needs_human_review: true`.

## 15. Grammar Generation Request Extension

Grammar generation requests must include:

```json
{
  "generation_request": {
    "domain": "grammar",
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
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs one medium S-V agreement item."
  }
}
```

Reject requests that:

- use an unapproved `grammar_focus_key`
- map a focus to the wrong role
- request `very_low` frequency without explicit justification
- request a reading-only skill or focus key
- request no-change behavior but omit no-change metadata

Frequency bands:

| Frequency band | Grammar focus keys |
|---|---|
| `very_high` | `punctuation_comma`, `subject_verb_agreement` |
| `high` | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation` |
| `medium` | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure` |
| `low` | `voice_active_passive`, `logical_predication`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation` |
| `very_low` | `affirmative_agreement`, `negation`, `noun_countability`, `determiners_articles`, `elliptical_constructions` |

Do not generate `very_low` frequency items unless the request explicitly asks
for niche coverage.

Generated grammar items must populate `generation_profile` with:

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
  "passage_template": "The [singular noun] of [plural noun], [relative clause], ______ [predicate].",
  "generation_timestamp": "ISO-8601 timestamp",
  "model_version": "rules_v2"
}
```

## 16. Grammar Generation Workflow

1. Validate role/focus/trap/frequency request.
2. Generate the passage or sentence.
3. Generate the stem.
4. Generate the correct option.
5. Generate three distractors.
6. Assemble metadata, classification, reasoning, and generation profile.
7. Run core validation.
8. Run grammar validation.
9. Retry failed component up to three times.

Passage requirements:

- 20-40 words for `sentence_only`; 80-150 for passage excerpts
- formal academic register; no contractions, slang, or first person
- self-contained meaning
- one clear target grammar decision
- target trap embedded naturally
- no outside knowledge required

Option requirements:

- exactly four options
- one correct answer
- no mixed option formats
- at least one distractor targets the declared syntactic trap
- no two distractors share the same `option_error_focus_key`

Difficulty calibration:

| Difficulty | Trap intensity | Distractor plausibility | Passage complexity |
|---|---|---|---|
| `low` | `none` or `low` | errors are clear but not malformed | short sentence, common vocabulary |
| `medium` | `medium` | one strong distractor, two moderate | standard academic vocabulary, one clause |
| `high` | `high` | all three distractors plausible | dense vocabulary, multiple clauses, unfamiliar topic |

When `target_syntactic_trap_key` is `none`, cap `difficulty_overall` at
`medium` unless the request explicitly uses intentionally complex syntax or
high distractor competition to justify `high`.

## 17. Passage Generation Rules by Focus

Use these as construction constraints, not as literal templates.

| Focus key | Passage construction rule |
|---|---|
| `subject_verb_agreement` | Place an intervening plural noun or phrase between subject and verb. |
| `pronoun_antecedent_agreement` | Separate pronoun from antecedent or introduce a number/gender distractor. |
| `verb_tense_consistency` | Establish a clear tense/register, then make one option shift improperly. |
| `modifier_placement` | Use an opening or embedded modifier with a plausible wrong attachment; dangling-modifier cases are classified under this approved focus key. |
| `punctuation_comma` | Create appositive, nonessential, introductory, or list punctuation pressure. |
| `semicolon_use` | Join two independent but closely related clauses. |
| `apostrophe_use` | Contrast plural, singular possessive, plural possessive, or contraction forms. |
| `appositive_punctuation` | Use essential vs nonessential naming logic. |
| `relative_pronouns` | Contrast `who`, `whom`, `which`, `that`, comma use, or essential clause logic. |
| `colon_dash_use` | Make the second element explain, define, list, or elaborate the first. |
| `conjunctive_adverb_usage` | Place a conjunctive adverb between independent clauses. |
| `parallel_structure` | Build a list, comparison, or correlative construction with one broken form. |
| `pronoun_case` | Put the pronoun in subject/object/reflexive position. |
| `pronoun_clarity` | Include competing antecedents and require clear reference. |
| `possessive_contraction` | Contrast possessive pronoun with contraction forms. |
| `hyphen_usage` | Use compound modifiers or number-word compounds. |
| `sentence_fragment` | Create a subordinate clause or phrase presented as a complete sentence. |
| `comma_splice` | Join two independent clauses with only a comma. |
| `run_on_sentence` | Fuse two independent clauses without required punctuation or conjunction. |
| `noun_countability` | Use a mass noun or count noun where article/number matters. |
| `determiners_articles` | Test required, forbidden, or wrong article use. |
| `affirmative_agreement` | Test `so`, `neither`, `nor`, or auxiliary inversion agreement. |
| `voice_active_passive` | Make active/passive voice affect grammaticality or sense. |
| `negation` | Place negation where scope matters. |
| `logical_predication` | Require subject-predicate compatibility. |
| `quotation_punctuation` | Test punctuation placement with quotation marks. |
| `transition_logic` | Create clear logical relation between adjacent claims. |
| `redundancy_concision` | Include repeated or unnecessary information. |
| `precision_word_choice` | Contrast near-synonyms by meaning, connotation, or register. |
| `register_style_consistency` | Make one option too casual, too formal, or stylistically inconsistent. |
| `data_interpretation_claims` | Require a claim to accurately reflect provided data. |

If a requested focus key is not listed here but is approved in Section 6, use
the closest construction family above and document the choice in
`classification_rationale`. If the requested focus is not approved in Section 6,
reject or propose an amendment.

## 18. Distractor Heuristics by Grammar Focus

| Focus key | Strong distractor pattern |
|---|---|
| `subject_verb_agreement` | verb agrees with nearest noun instead of true subject |
| `verb_tense_consistency` | plausible tense shift based on nearby time phrase |
| `punctuation_comma` | comma inserted where a stronger boundary or no punctuation is needed |
| `semicolon_use` | comma splice, colon where not explanatory, or period that changes flow |
| `apostrophe_use` | plural/possessive/contraction confusion |
| `modifier_placement` | grammatically smooth but logically attached to wrong subject |
| `relative_pronouns` | plausible pronoun with wrong essential/nonessential structure |
| `colon_dash_use` | semicolon or comma where elaboration punctuation is required |
| `appositive_punctuation` | missing or unnecessary commas around essential/nonessential appositive |
| `parallel_structure` | same meaning but mismatched form |
| `pronoun_case` | formal-sounding but wrong subject/object/reflexive case |
| `conjunctive_adverb_usage` | comma-only or period-only treatment of conjunctive adverb |
| `transition_logic` | same topic with wrong logical relation |
| `precision_word_choice` | near-synonym with wrong precision or connotation |

Forbidden distractor constructions:

- gibberish or impossible English unless impossibility is the tested contrast
- an accidental second grammar error unrelated to the target focus
- one option that is visibly longer, safer, or more polished than the rest
- distractors that all fail for the same focus key
- reading-only evidence traps in a SEC item
- grammar-error distractors in a pure non-grammar Expression of Ideas item

Every generated distractor must be plausible English and must be wrong for a
specific named reason.

## 19. Option Text Format Rules

Use one format per item:

1. Fill-in-blank: options contain only the word or phrase that fills the blank.
2. Full-replacement: options contain the full revised sentence, clause, or
   phrase.
3. Punctuation-only: options contain only the punctuation mark or punctuation
   sequence.

Do not mix formats within a single item.

## 20. Grammar Explanation Requirements

`explanation_short` must state the core rule in at most 25 words.

`explanation_full` must:

- explain why the correct answer is correct
- name each wrong option by label
- identify each wrong option's specific grammar error
- reference `passage_tense_register_key` for verb-form items
- explicitly justify no-change items when original text is correct

## 21. Grammar Validator Checklist

Before finalizing a grammar item:

- [ ] `question_family_key` is `conventions_grammar` or `expression_of_ideas`
- [ ] role/focus mapping is legal when `grammar_role_key` is non-null
- [ ] non-grammar Expression of Ideas items either use
      `grammar_role_key: "expression_of_ideas"` or omit/null grammar keys
      consistently
- [ ] reading-only keys are null or omitted
- [ ] `secondary_grammar_focus_keys` is populated when secondary rules are
      visible
- [ ] every grammar distractor has a specific `option_error_focus_key`
- [ ] no two distractors fail for the same exact reason
- [ ] no-change metadata is present when original text is an option
- [ ] tense/register metadata is present for verb-form items
- [ ] `disambiguation_rule_applied` is present when labels conflict
- [ ] option text format is consistent
- [ ] `evidence_span_text` is minimal and relevant
- [ ] `generation_profile` includes target role/focus/trap/frequency for
      generated items
- [ ] `generation_profile` includes `passage_template`,
      `generation_timestamp`, and `model_version`
- [ ] `difficulty_overall` matches the requested target and respects the
      `target_syntactic_trap_key: "none"` cap
- [ ] no unapproved grammar keys are used
- [ ] core validator checklist passes

## 22. Minimal Worked Examples

Subject-verb agreement classification:

```json
{
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "agreement",
  "grammar_focus_key": "subject_verb_agreement",
  "syntactic_trap_key": "nearest_noun_attraction",
  "secondary_grammar_focus_keys": [],
  "disambiguation_rule_applied": null,
  "classification_rationale": "The true singular subject is separated from the verb by a plural intervening noun."
}
```

Expression of Ideas transition classification:

```json
{
  "question_family_key": "expression_of_ideas",
  "grammar_role_key": "expression_of_ideas",
  "grammar_focus_key": "transition_logic",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "evaluate_transition",
  "classification_rationale": "The correct answer supplies the logical relationship between adjacent claims."
}
```

No-change metadata:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```
