# DSAT Reading Module v2

## 1. Scope

Load this file after `rules_core_generation.md` when the item belongs to:

- Information and Ideas
- Craft and Structure

This module owns reading classification, reading focus keys, skill-family
logic, evidence mechanisms, reasoning traps, cross-text logic, quantitative
requirements, reading generation, and reading validation.

This module does not own Standard English Conventions or Expression of Ideas.
Do not apply grammar taxonomy keys to any item in this module's domains.

## 2. Domain Boundary

This module covers:

- Information and Ideas:
  - Command of Evidence, Textual
  - Command of Evidence, Quantitative
  - Central Ideas and Details
  - Inferences
- Craft and Structure:
  - Words in Context
  - Text Structure and Purpose
  - Cross-Text Connections

Hard prohibition:

```json
{
  "grammar_role_key": null,
  "grammar_focus_key": null,
  "syntactic_trap_key": null
}
```

For all Information and Ideas or Craft and Structure items, grammar fields must
be null or omitted. If a non-null grammar field is needed, reroute to
`rules_dsat_grammar_module.md`.

## 3. Reading Question Fields

Reading-compatible `stimulus_mode_key` values:

- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `passage_excerpt`
- `poem`

Rules:

- Cross-Text Connections always requires `prose_paired`.
- Command of Evidence, Quantitative always requires `prose_plus_table` or
  `prose_plus_graph`.
- Quantitative items must populate `table_data` or `graph_data`.
- Cross-Text items must populate both `passage_text` and
  `paired_passage_text`.

Reading-compatible `stem_type_key` values:

| Key | Canonical use |
|---|---|
| `choose_best_support` | supports a claim or hypothesis |
| `choose_best_illustration` | literary quotation illustrates a claim |
| `choose_best_weakener` | undermines or challenges a claim |
| `choose_best_completion_from_data` | uses data from a table or graph |
| `choose_main_idea` | states main idea or summary |
| `choose_detail` | identifies stated detail |
| `most_logically_completes` | completes text by inference |
| `choose_word_in_context` | most logical and precise word or phrase |
| `choose_main_purpose` | states main purpose |
| `choose_sentence_function` | describes function of sentence or paragraph |
| `choose_text_relationship` | Text 2 responds to Text 1 |
| `choose_agreement_across_texts` | both texts agree |
| `choose_difference_across_texts` | texts differ |

SEC-only and Expression-of-Ideas stems such as `choose_best_grammar_revision`
and `choose_best_notes_synthesis` are forbidden in this module.

## 4. Classification Fields

Reading outputs use this classification shape:

```json
{
  "domain": "Information and Ideas",
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "evidence_supports_claim",
  "secondary_reading_focus_keys": [],
  "reasoning_trap_key": "topical_relevance_without_logical_connection",
  "text_relationship_key": null,
  "evidence_scope_key": "passage",
  "evidence_location_key": "main_clause",
  "answer_mechanism_key": "evidence_matching",
  "solver_pattern_key": "locate_claim_then_match_evidence",
  "grammar_role_key": null,
  "grammar_focus_key": null,
  "classification_rationale": "The correct option directly supports the stated claim."
}
```

Approved `question_family_key` values:

- `information_and_ideas`
- `craft_and_structure`

## 5. Skill Family Keys

Approved `skill_family_key` values:

- `command_of_evidence_textual`
- `command_of_evidence_quantitative`
- `central_ideas_and_details`
- `inferences`
- `words_in_context`
- `text_structure_and_purpose`
- `cross_text_connections`

Use `information_and_ideas` when the item requires matching evidence, reading
data, identifying central/detail content, or completing an inference.

Use `craft_and_structure` when the item requires word meaning, rhetorical
purpose/function, or relationship between paired texts.

## 6. Reading Focus Keys

Use the most specific applicable `reading_focus_key`.

Command of Evidence, Textual:

- `evidence_supports_claim`
- `evidence_weakens_claim`
- `evidence_illustrates_claim`
- `evidence_explains_claim`
- `evidence_qualifies_claim`

Command of Evidence, Quantitative:

- `data_supports_claim`
- `data_weakens_claim`
- `data_completes_example`
- `data_comparison`
- `data_trend`

Central Ideas and Details:

- `central_idea`
- `main_purpose`
- `passage_summary`
- `supporting_detail`
- `character_or_author_detail`

Inferences:

- `causal_inference`
- `motivational_inference`
- `implication_inference`
- `predictive_inference`
- `cross_text_inference`

Words in Context:

- `contextual_meaning`
- `connotation_fit`
- `precision_fit`
- `register_fit`
- `underlined_word_meaning`

Text Structure and Purpose:

- `overall_purpose`
- `sentence_function`
- `structural_pattern`
- `author_stance`

Cross-Text Connections:

- `text2_response_to_text1`
- `both_texts_agree`
- `texts_disagree`
- `text2_qualifies_text1`
- `text2_contradicts_text1`
- `methodological_critique`
- `expectation_violation`

## 7. Skill to Focus Mapping

| `skill_family_key` | Allowed `reading_focus_key` values |
|---|---|
| `command_of_evidence_textual` | `evidence_supports_claim`, `evidence_weakens_claim`, `evidence_illustrates_claim`, `evidence_explains_claim`, `evidence_qualifies_claim` |
| `command_of_evidence_quantitative` | `data_supports_claim`, `data_weakens_claim`, `data_completes_example`, `data_comparison`, `data_trend` |
| `central_ideas_and_details` | `central_idea`, `main_purpose`, `passage_summary`, `supporting_detail`, `character_or_author_detail` |
| `inferences` | `causal_inference`, `motivational_inference`, `implication_inference`, `predictive_inference`, `cross_text_inference` |
| `words_in_context` | `contextual_meaning`, `connotation_fit`, `precision_fit`, `register_fit`, `underlined_word_meaning` |
| `text_structure_and_purpose` | `overall_purpose`, `sentence_function`, `structural_pattern`, `author_stance` |
| `cross_text_connections` | `text2_response_to_text1`, `both_texts_agree`, `texts_disagree`, `text2_qualifies_text1`, `text2_contradicts_text1`, `methodological_critique`, `expectation_violation` |

The validator must reject any focus key outside the selected skill family.

## 8. Answer Mechanism Keys

Approved `answer_mechanism_key` values:

- `evidence_location`
- `inference`
- `data_synthesis`
- `evidence_matching`
- `contextual_substitution`
- `rhetorical_classification`
- `cross_text_comparison`

Use `evidence_location` when the student must find a specific span.
Use `inference` when the answer is logically required but not directly stated.
Use `data_synthesis` when graphic data must be integrated with text.
Use `evidence_matching` when a proposed claim must be matched to support or
weakening evidence.
Use `contextual_substitution` for Words in Context.
Use `rhetorical_classification` for purpose, function, or structure.
Use `cross_text_comparison` for paired-text relations.

## 9. Solver Pattern Keys

Approved `solver_pattern_key` values:

- `locate_claim_then_match_evidence`
- `read_graphic_then_match_claim`
- `summarize_then_compare`
- `locate_detail_directly`
- `identify_logical_gap`
- `substitute_and_test`
- `classify_rhetorical_move`
- `summarize_both_then_compare`

## 10. Reasoning Trap Keys

Use `reasoning_trap_key` for the most dangerous wrong-answer mechanism at the
question level and per option when applicable.

Information and Ideas traps:

- `topical_relevance_without_logical_connection`
- `partial_match`
- `indirect_evidence`
- `inverted_logic`
- `keyword_matching`
- `single_sector_focus`
- `data_context_mismatch`
- `detail_trap`
- `topic_trap`
- `overreach`
- `contradiction`
- `absolute_language`
- `outside_knowledge`
- `cause_effect_misalignment`
- `scope_extension`
- `overspecification`

Craft and Structure traps:

- `common_definition_trap`
- `semantic_relatedness_without_precision`
- `connotation_mismatch`
- `plausible_synonym`
- `also_true_trap`
- `wrong_scope`
- `wrong_action_verb`
- `overstated_position`
- `partial_purpose`
- `reversed_attribution`
- `extreme_language`
- `textual_mimicry`
- `confirmed_when_contradicted`

## 11. Text Relationship Keys

Use `text_relationship_key` only for Cross-Text Connections.

Approved values:

- `direct_contradiction`
- `confirmation_with_qualification`
- `expectation_violation`
- `methodological_critique`
- `partial_agreement`
- `broad_support`

**Critical rule (confirmed on released College Board items):** Response stems
("how would Text 2 most likely respond to Text 1") are always
*disagreement-oriented*. The College Board does not use response stems for
agreement scenarios. A correct response-stem option will describe Text 2 as
finding Text 1's claim "problematic," "unsupported," "only conditionally valid,"
or "contradicted by evidence." Never select or generate an option that describes
Text 2 as fully endorsing Text 1 for a response-type stem.

The most realistic generated response relationships are
`direct_contradiction` and `confirmation_with_qualification`. Do not generate
Cross-Text items where Text 2 fully endorses Text 1 with no qualification —
the SAT does not test simple agreement without tension.

## 12. Reading Option Analysis

Each reading option must include the shared core option fields.

Approved reading distractor type keys:

- `topical_relevance_without_logical_connection`
- `indirect_evidence`
- `inverted_logic`
- `partial_match`
- `detail_trap`
- `overreach`
- `scope_error`
- `data_context_mismatch`
- `connotation_mismatch`
- `plausible_synonym`
- `semantic_imprecision`
- `wrong_action_verb`
- `reversed_attribution`
- `confirmed_when_contradicted`
- `cause_effect_misalignment`
- `contradiction`
- `correct`

Approved reading plausibility source keys:

- `passage_vocabulary_overlap`
- `topical_proximity`
- `partial_truth`
- `common_sense_appeal`
- `common_definition_appeal`
- `near_synonym_appeal`
- `rhetorical_surface_similarity`
- `attribution_swap`

### 12.1 `option_error_focus_key` in Reading Domains

For reading distractors, `option_error_focus_key` maps to the `reading_focus_key`
that the distractor fails on. This parallels grammar's use of `grammar_focus_key`
for the same field.

Examples:

| Wrong option failure | `option_error_focus_key` |
|---|---|
| Topically related but does not prove the claim | `evidence_supports_claim` |
| Accurate data point but wrong comparison | `data_comparison` |
| Detail rather than main idea | `central_idea` |
| Near-synonym with wrong connotation | `connotation_fit` |
| Right content but wrong rhetorical verb | `overall_purpose` |
| Attribution reversed between texts | `text2_response_to_text1` |

### 12.2 Words in Context Three-Level Wrong-Answer Distinction

For Words in Context distractors, the `why_wrong` field must classify the
failure at one of three levels:

1. **Wrong denotation**: the word's core meaning does not match the passage
   context.
2. **Right denotation, wrong connotation**: the word means roughly the right
   thing but carries the wrong evaluative, emotional, or tonal charge.
3. **Right denotation and connotation, wrong register or precision**: the word
   fits broadly but is too formal, too informal, too vague, or too specific for
   the passage context.

This three-level distinction is diagnostic for both annotation quality and
generation calibration.

### 12.3 `grammar_fit` and `tone_match` in Reading Domains

In reading domains, `grammar_fit` should almost always be `yes` for all four
options. Wrongness should come from logic, evidence, scope, attribution,
contextual fit, or rhetorical function, not from grammatical brokenness.

## 13. Skill-Specific Rules

### 13.1 Command of Evidence, Textual

Mandatory classification fields:

```json
{
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "evidence_supports_claim",
  "answer_mechanism_key": "evidence_matching",
  "solver_pattern_key": "locate_claim_then_match_evidence",
  "reasoning_trap_key": "topical_relevance_without_logical_connection"
}
```

Stem disambiguation:

| Stem wording | `reading_focus_key` | `stem_type_key` |
|---|---|---|
| most directly support | `evidence_supports_claim` | `choose_best_support` |
| most directly undermine/challenge/weaken | `evidence_weakens_claim` | `choose_best_weakener` |
| most effectively illustrate the claim | `evidence_illustrates_claim` | `choose_best_illustration` |

The correct option must directly support, weaken, illustrate, explain, or
qualify the specific claim. Merely topical options are wrong.

### 13.2 Command of Evidence, Quantitative

Mandatory fields:

```json
{
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_quantitative",
  "reading_focus_key": "data_supports_claim",
  "answer_mechanism_key": "data_synthesis",
  "solver_pattern_key": "read_graphic_then_match_claim",
  "stimulus_mode_key": "prose_plus_table"
}
```

Requirements:

- `stimulus_mode_key` must be `prose_plus_table` or `prose_plus_graph`.
- `table_data` or `graph_data` must be populated.
- `evidence_span_text` must include the specific data values or trend used.
- Distractors should include plausible but misaligned data readings, not absurd
  numbers.

Focus disambiguation:

- single absolute value: `data_completes_example`
- comparing values: `data_comparison`
- directional pattern: `data_trend`
- supports or weakens a claim: `data_supports_claim` or `data_weakens_claim`

### 13.3 Central Ideas and Details

Use for main ideas, passage summaries, supporting details, and literary
character/author details.

Disambiguation:

- "main idea" or "summarizes" -> `central_idea` or `passage_summary`
- "what is true about" or "indicates that" -> `supporting_detail`
- literary character feeling/attribute/action -> `character_or_author_detail`
- if answer options are infinitive rhetorical action phrases, use Text
  Structure and Purpose instead

### 13.4 Inferences

Mandatory fields:

```json
{
  "question_family_key": "information_and_ideas",
  "skill_family_key": "inferences",
  "reading_focus_key": "causal_inference",
  "stem_type_key": "most_logically_completes",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "identify_logical_gap",
  "reasoning_trap_key": "overreach"
}
```

The correct answer must be logically required by the prior text, not merely
consistent with it. If only plausible, set `needs_human_review: true`.

### 13.5 Words in Context

Mandatory fields:

```json
{
  "question_family_key": "craft_and_structure",
  "skill_family_key": "words_in_context",
  "reading_focus_key": "contextual_meaning",
  "answer_mechanism_key": "contextual_substitution",
  "solver_pattern_key": "substitute_and_test",
  "reasoning_trap_key": "common_definition_trap"
}
```

Generation default: use blank-fill "most logical and precise word or phrase"
format. Use underlined "most nearly mean" only when explicitly requested or
ingested.

Wrong-option explanations must distinguish:

- wrong denotation
- right denotation but wrong connotation
- right denotation/connotation but wrong register or precision

### 13.6 Text Structure and Purpose

Mandatory fields:

```json
{
  "question_family_key": "craft_and_structure",
  "skill_family_key": "text_structure_and_purpose",
  "reading_focus_key": "overall_purpose",
  "answer_mechanism_key": "rhetorical_classification",
  "solver_pattern_key": "classify_rhetorical_move",
  "reasoning_trap_key": "wrong_action_verb"
}
```

Overall-purpose answers usually use infinitive action phrases. Extract the
correct answer's action verb in `review.review_notes` when it matters.

Common rhetorical verbs:

- `to argue`
- `to describe`
- `to explain`
- `to compare`
- `to analyze`
- `to critique`
- `to illustrate`
- `to trace`
- `to challenge`
- `to suggest`

Sentence-function items must annotate `evidence_span_text` with the referenced
sentence and record its role in the passage's logic.

### 13.7 Cross-Text Connections

Mandatory fields:

```json
{
  "question_family_key": "craft_and_structure",
  "skill_family_key": "cross_text_connections",
  "reading_focus_key": "text2_response_to_text1",
  "text_relationship_key": "direct_contradiction",
  "answer_mechanism_key": "cross_text_comparison",
  "solver_pattern_key": "summarize_both_then_compare",
  "reasoning_trap_key": "reversed_attribution",
  "stimulus_mode_key": "prose_paired"
}
```

Requirements:

- `passage_text` is Text 1.
- `paired_passage_text` is Text 2.
- Both must be populated.
- Each text must have a clear standalone claim or argument.
- The relationship must be classifiable by one `text_relationship_key`.

Stem disambiguation:

| Stem wording | `reading_focus_key` | `stem_type_key` |
|---|---|---|
| how would Text 2 respond to Text 1 | `text2_response_to_text1` | `choose_text_relationship` |
| both texts would agree | `both_texts_agree` | `choose_agreement_across_texts` |
| difference between claims | `texts_disagree` | `choose_difference_across_texts` |

## 14. Reading Disambiguation Rules

1. `command_of_evidence_textual` vs `inferences`: support/weakener stems with
   proposed findings are CoE; end-blank "most logically completes" stems are
   Inferences.
2. `central_ideas_and_details` vs `text_structure_and_purpose`: factual summary
   options are central/details; infinitive rhetorical action options are
   structure/purpose.
3. `overall_purpose` vs `sentence_function`: whole text references use
   `overall_purpose`; underlined sentence/paragraph references use
   `sentence_function`.
4. `cross_text_connections` vs `inferences`: two labeled passages always route
   to Cross-Text.
5. `words_in_context` vs detail/central idea: word/phrase options with blank or
   underlined word route to Words in Context. Full sentence/claim options do not.
6. Expression of Ideas routes to the grammar module, not this module.

Always record the resolved rule in `classification.disambiguation_rule_applied`
when ambiguity exists.

## 15. Reading Difficulty Calibration

For reading domains, `difficulty_grammar` is usually `low`. The meaningful axes
are `difficulty_reading`, `difficulty_inference`, and `difficulty_vocab`.

| Skill | Low | Medium | High |
|---|---|---|---|
| CoE Textual | claim explicit; wrong answers off-topic | claim spans two sentences; one causal trap | claim embedded; multiple partial matches; weaken variants |
| CoE Quantitative | simple graphic; obvious value | multi-category comparison | indirect claim; accurate but misaligned data distractors |
| Central Ideas | main point stated directly | main point inferred across sentences | evaluative stance or unexpected finding |
| Inferences | simple contrast or sequence | two concepts must be connected | multiple passage elements; over/understatement traps |
| Words in Context | local context clue | distributed context clues | subtle tone/register; near-neighbor options |
| Text Structure/Purpose | one clear rhetorical move | two moves; dominant purpose needed | qualification/nuance; complex sentence function |
| Cross-Text | clear support/contradiction | qualification relationship | subtle methodological critique or expectation violation |

High-difficulty reading items should raise competition among answers before
raising outside-topic complexity.

## 16. Reading Passage Architecture

Typical passage lengths:

| Skill | Typical word count |
|---|---|
| Command of Evidence, Textual | 50-150 |
| Command of Evidence, Quantitative | 40-100, graphic separate |
| Central Ideas and Details | 60-150 |
| Inferences | 60-120 |
| Words in Context | 30-80 |
| Text Structure and Purpose | 50-150 |
| Cross-Text Connections | 80-200 total, 40-100 per text |

Useful architecture keys:

- `unexpected_finding`
- `cautionary_framing`
- `problem_solution`
- `compare_contrast`
- `chronological_sequence`
- `research_summary`
- `claim_evidence_explanation`
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

## 17. Reading Generation Request Extension

Reading generation requests must include:

```json
{
  "generation_request": {
    "domain": "reading",
    "target_question_family_key": "information_and_ideas",
    "target_skill_family_key": "command_of_evidence_textual",
    "target_reading_focus_key": "evidence_supports_claim",
    "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
    "target_distractor_pattern": [
      "one topically related but logically disconnected option",
      "one indirect or downstream evidence option",
      "one inverted-logic option"
    ],
    "passage_structure_pattern": "research_summary",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "choose_best_support",
    "target_difficulty_overall": "medium",
    "topic_broad": "science",
    "topic_fine": "ecology"
  }
}
```

Reject requests that:

- include non-null grammar keys
- use an unapproved `skill_family_key`
- map a focus to the wrong skill
- request Cross-Text without `prose_paired`
- request Quantitative CoE without table/graph mode
- request a grammar-only or Expression-of-Ideas stem

## 18. Reading Generation Workflow Additions

After the core workflow:

1. Select reading domain and skill family.
2. Select evidence mechanism before writing the passage.
3. Construct passage so the correct answer is required, not merely plausible.
4. Pre-answer from passage evidence.
5. Generate correct answer from the pre-answer.
6. Generate distractors by reasoning trap, not by random topic association.
7. Verify every wrong option has a specific evidence, scope, attribution, data,
   connotation, or rhetorical-function failure.
8. Run reading validation.

Skill-specific generation controls:

- CoE Textual: build a claim and decide whether the task supports, weakens,
  illustrates, explains, or qualifies it.
- CoE Quantitative: design the table/graph and passage claim together; all data
  distractors must be numerically plausible.
- Central Ideas: avoid one option being the only summary; include detail and
  overbroad traps.
- Inferences: the blank must require a conclusion logically forced by prior
  text.
- Words in Context: all options should be near-neighbors with same part of
  speech.
- Text Structure: all options should describe plausible rhetorical actions.
- Cross-Text: summarize both texts internally before generating options.

## 19. Reading Distractor Heuristics and Failure Modes

Every reading distractor must be tied to a specific student failure mode.

Reading-specific `student_failure_mode_key` values:
- `local_detail_fixation` — student selects an option supported by a small detail but not the broader claim
- `overreach` — student selects an option that goes further than the passage supports
- `underreach` — student selects an option too narrow for the full claim
- `text_label_swap` — in cross-text items, student assigns an author's position to the wrong text
- `topic_association` — student selects an option merely because it mentions the same topic, without checking evidence
- `inverse_logic` — student selects an option that inverts the passage's direction of argument
- `false_agreement` — in cross-text items, student assumes both texts agree when they do not (or vice versa)

| Skill | Strong distractor patterns |
|---|---|
| CoE Textual | topical but disconnected (`topic_association`), indirect evidence (`local_detail_fixation`), inverted support/weaken logic (`inverse_logic`) |
| CoE Quantitative | accurate but irrelevant value (`local_detail_fixation`), wrong comparison, trend misread |
| Central Ideas | supporting detail as main idea (`local_detail_fixation`), overbroad summary (`overreach`), topic without claim (`topic_association`) |
| Inferences | plausible but not required (`overreach`), cause/effect misalignment (`inverse_logic`) |
| Words in Context | common dictionary meaning, near-synonym with wrong connotation, wrong register |
| Text Structure/Purpose | right topic but wrong action verb, local function as whole purpose (`underreach`), overstated stance (`overreach`) |
| Cross-Text | reversed attribution (`text_label_swap`), false agreement/disagreement (`false_agreement`), wrong qualification |

Every generated distractor must survive a first-pass elimination check by a reasonable but mistaken student. Difficulty comes from evidence competition, not from obscure or ambiguous passage content. The correct answer must be directly and unambiguously supported by evidence in the passage; the support cannot require an unanchored inference.

## 20. Evidence Span Selection Rules (Reading)

`evidence_span_text` must identify the minimal passage span that anchors the
correct answer.

Rules:

- For CoE Textual, quote the specific claim sentence or clause that the correct
  option directly supports or weakens.
- For CoE Quantitative, cite the specific data values or trend description.
- For Central Ideas, quote the sentence or sentences that express the main point.
- For Inferences, quote the passage text that logically requires the inference.
- For Words in Context, quote the surrounding context clue(s) that determine the
  correct word.
- For Text Structure and Purpose, quote the sentence or structural element
  whose function is being tested.
- For Cross-Text, quote the key claim from each text that establishes their
  relationship.
- Use `"..."` ellipsis to omit intervening text when the span exceeds 10 words.
- Do not quote the full passage unless the full passage is the evidence.

## 21. Forbidden Patterns

Reject any reading-domain output containing:

- non-null `grammar_role_key`
- non-null `grammar_focus_key`
- non-null `syntactic_trap_key`
- `stem_type_key: "choose_best_grammar_revision"`
- `stem_type_key: "choose_best_notes_synthesis"`
- a `skill_family_key` outside the approved seven values
- Cross-Text with missing `paired_passage_text`
- Quantitative CoE with missing `table_data` or `graph_data`
- a correct answer that is merely consistent with, but not required by, the text

## 22. Reading Validator Checklist

Before finalizing a reading item:

- [ ] `question_family_key` is `information_and_ideas` or
      `craft_and_structure`
- [ ] `skill_family_key` is one of the seven approved keys
- [ ] `reading_focus_key` belongs to the selected `skill_family_key`
- [ ] grammar fields are null or omitted
- [ ] `stem_type_key` matches the actual stem wording
- [ ] `stimulus_mode_key` is legal for the skill
- [ ] `paired_passage_text` is populated for Cross-Text
- [ ] `table_data` or `graph_data` is populated for Quantitative CoE
- [ ] every option has `distractor_type_key`, `why_plausible`, and `why_wrong`
- [ ] exactly one option is correct
- [ ] only the correct option has `precision_score: 3`
- [ ] `evidence_span_text` anchors the correct answer
- [ ] `annotation_confidence` is populated
- [ ] generated items include target skill/focus/trap/stem/mode fields
- [ ] core validator checklist passes

