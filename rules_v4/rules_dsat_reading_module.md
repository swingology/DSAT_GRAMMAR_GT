# DSAT Reading Module

## 1. Purpose

This file defines the reading domain taxonomy, generation rules, annotation
rules, and validation contract. It covers:

- **Information and Ideas** — Command of Evidence (Textual and Quantitative),
  Central Ideas and Details, Inferences
- **Craft and Structure** — Words in Context, Text Structure and Purpose,
  Cross-Text Connections

Load `rules_core_generation.md` before this module. Core owns the shared output
shape, option contract, distractor engineering rules, SAT realism layer,
difficulty calibration rubric, provenance, anti-clone, and batch/error formats.
This module owns reading-specific taxonomy, skill-family classification,
reasoning traps, evidence mechanisms, cross-text rules, quantitative evidence
rules, and reading validation.

**Source file**: `rules_agent_dsat_reading_v2.md`
(Merges reading v1.0 + v1.1 PT4–PT11 gap-analysis addendum, 2026-04-29)

---

## 2. Reading Operating Principles

### 2.1 Domain isolation

Questions classified under `information_and_ideas` or `craft_and_structure`
must never use grammar taxonomy keys. `grammar_role_key`, `grammar_focus_key`,
and `syntactic_trap_key` must be null or omitted for all reading-domain items.

### 2.2 Evidence over inference

The SAT's evidentiary standard is "indicated in or directly supported by the
text." Correct answers are never merely consistent with the text — they are
*required* by it.

### 2.3 Controlled keys only

Use only approved lookup keys from this module. If no key fits, propose an
amendment (§14) rather than inventing a production key.

---

## 3. Reading Output Shape

Reading domain items use core's top-level output shape (§4 of core) plus the
domain-specific classification and reasoning fields below.

### 3.1 Classification fields (reading-specific)

```json
{
  "domain": "Information and Ideas | Craft and Structure",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "best_support_for_claim",
  "secondary_reading_focus_keys": [],
  "reasoning_trap_key": "surface_similarity_bias",
  "text_relationship_key": null,
  "answer_mechanism_key": "evidence_location",
  "solver_pattern_key": "find_evidence_in_text",
  "student_failure_mode_key": "local_detail_fixation"
}
```

Grammar-specific keys (`grammar_role_key`, `grammar_focus_key`,
`syntactic_trap_key`) must be null or omitted.

### 3.2 Reasoning section (reading-specific additions)

```json
{
  "primary_rule": "...",
  "trap_mechanism": "...",
  "correct_answer_reasoning": "...",
  "distractor_analysis_summary": "..."
}
```

---

## 4. Question Family Keys

| `question_family_key` | Domain | When to use |
|---|---|---|
| `information_and_ideas` | Information and Ideas | CoE Textual/Quantitative, Central Ideas, Inferences |
| `craft_and_structure` | Craft and Structure | WIC, Text Structure/Purpose, Cross-Text Connections |

### 4.1 When to use `information_and_ideas`
- The stem asks for evidence to support/weaken/illustrate a claim
- The stem asks for a central/main idea or specific detail
- The stem asks the student to complete a text with the most logical conclusion
- The stem asks the student to draw an inference from quantitative data + text
- The stem asks "which finding would most directly support..."

### 4.2 When to use `craft_and_structure`
- The stem asks for the meaning of a word/phrase "as used in the text"
- The stem asks about the "main purpose" or "function" of a sentence or text
- The stem asks about organizational structure or patterns
- The stem asks about the relationship between two paired texts
- The stem asks about author stance or attitude

---

## 5. Skill Family Keys

Seven approved values:

| `skill_family_key` | Domain |
|---|---|
| `command_of_evidence_textual` | Information and Ideas |
| `command_of_evidence_quantitative` | Information and Ideas |
| `central_ideas_and_details` | Information and Ideas |
| `inferences` | Information and Ideas |
| `words_in_context` | Craft and Structure |
| `text_structure_and_purpose` | Craft and Structure |
| `cross_text_connections` | Craft and Structure |

---

## 6. Reading Focus Keys

### 6.1 Command of Evidence — Textual
- `best_support_for_claim` — quotation selection that most directly supports a stated claim
- `best_illustration_of_claim` — example/passage that illustrates a stated position
- `best_weakener_of_hypothesis` — evidence that most directly weakens a stated hypothesis
- `two_part_claim` — two claims in the stem; correct evidence must support both
- `control_group_patterns` — evidence must distinguish treatment from control condition

### 6.2 Command of Evidence — Quantitative
- `best_completion_from_data` — blank completes a claim based on table/graph data
- `best_support_from_data` — selecting the option best supported by the quantitative evidence
- `best_weaken_from_data` — selecting the option most directly weakened by the qualitative text
- `data_interpretation` — student must interpret what data means, not just read values
- `trend_extrapolation` — student must extrapolate from data trend to unsampled condition

Eight approved `quantitative_sub_pattern` values (optional annotation field):
- `direct_value_read`
- `simple_comparison_two_bars`
- `trend_over_time`
- `multi_variable_interaction`
- `threshold_crossing`
- `proportional_comparison`
- `ranking_task`
- `margin_of_error_awareness`

### 6.3 Central Ideas and Details
- `main_idea` — correct option states what the passage as a whole conveys
- `specific_detail` — correct option restates a specific passage detail
- `function_of_detail` — correct option explains why the author included a detail

### 6.4 Inferences
- `most_logically_completes` — blank at end of passage; must follow logically
- `inference_from_passage` — which statement is most directly supported by the passage
- `study_design_isolation` — correct inference isolates the study design from confounds
- `subgroup_boundary_awareness` — correct inference respects subgroup boundaries;
  wrong inferences overgeneralize (overreach)
- `mechanism_test_annotation` — the passage tests a mechanism; wrong answers confuse
  correlation with mechanism

### 6.5 Words in Context
- `contextual_meaning` — correct word determined by surrounding sentences (default)
- `connotation_fit` — near-synonyms; distinction is evaluative or emotional register
- `precision_fit` — distinction is degree of specificity/precision among near-synonyms
- `register_fit` — distinction is level of formality: academic, formal, technical
- `underlined_word_meaning` — "most nearly mean" stem with underlined word
- `polarity_fit` — correct word must preserve logical polarity when a negator,
  concessive, or contrast marker is present

#### WIC Disambiguation (apply in order):
1. If stem uses "most nearly mean" with an underlined word → `underlined_word_meaning`
2. If the passage contains a negator, concessive, or contrast marker and all options
   are near-synonyms differing in evaluative direction → `polarity_fit`
3. If all four options are near-synonyms and the distinction is evaluative/tonal →
   `connotation_fit`
4. If the distinction is degree of specificity → `precision_fit`
5. If the blank or word is in a passage with pronounced formal/technical register →
   `register_fit`
6. Otherwise → `contextual_meaning` (default)

#### `polarity_fit` rule (full):

The passage contains a negator, concessive phrase, or double-negative construction
("by no means," "not atypical," "hardly insignificant") that reverses or qualifies
the polarity of the target word. The correct word must preserve the logical polarity
of the full construction, not the surface meaning of the surrounding words.

**Annotation requirement**: For every WIC item with a negator/concessive present,
annotate `evidence_span_text` with the full phrase including the negator. Add to
`review_notes`: "polarity_context: [name the negator or concessive]."

**Generation rule**: Embed a negator/concessive at or adjacent to the blank. All
four options must be grammatically viable after the negator. The correct option
produces the intended meaning when combined with the negator. At least two wrong
options must produce the opposite or illogical meaning when combined with the
negator (not merely off-topic).

#### Three-Level WIC Error Analysis:

When annotating WIC wrong options, classify the failure at the deepest applicable
level:

| Level | Question | Key |
|---|---|---|
| **Denotation** (most basic) | Is the word's dictionary meaning correct in context? | `contextual_meaning` / `precision_fit` |
| **Connotation** (mid-level) | Does the word carry the right evaluative or emotional tone? | `connotation_fit` |
| **Register** (highest-level) | Does the word match the passage's academic or formal register? | `register_fit` |

A WIC distractor may have correct denotation but wrong connotation, or correct
connotation but wrong register. Classify the deepest failure level.

### 6.6 Text Structure and Purpose
- `overall_purpose` — correct option states what the text as a whole does
- `sentence_function` — correct option describes the rhetorical role of one
  underlined sentence or paragraph
- `structural_pattern` — correct option identifies the organizational pattern
- `author_stance` — correct option identifies the author's evaluative position

#### Twelve Sentence Function Roles (from v1.1 §2.1):

| Role | Description |
|---|---|
| `introduce_claim` | First sentence presents the main thesis |
| `provide_context` | Background information a reader needs before the argument |
| `present_counterclaim` | Acknowledges opposing view |
| `offer_concession` | Partially accepts opposing point before rebuttal |
| `state_objection` | Raises specific objection |
| `refute_objection` | Dismisses or rebuts objection |
| `qualify_claim` | Limits or conditions the main claim |
| `support_with_example` | Provides specific example as evidence |
| `support_with_data` | Provides data/statistics as evidence |
| `support_with_expertise` | Cites expert/expert consensus |
| `explain_mechanism` | Explains how or why a phenomenon works |
| `draw_conclusion` | Final sentence states the logical conclusion |

### 6.7 Cross-Text Connections
- `text2_response_to_text1` — how Text 2's author/evidence would characterize Text 1's claim
- `both_texts_agree` — the simplest claim both texts endorse
- `texts_disagree` — the key point of divergence
- `text2_qualifies_text1` — Text 2 accepts under specific conditions, rejects broadly
- `text2_contradicts_text1` — Text 2's conclusion is the opposite of Text 1's
- `methodological_critique` — Text 2 challenges Text 1's method/scope, not conclusion
- `expectation_violation` — Text 2 expected Text 1's theory to hold but found contrary evidence

---

## 7. Answer Mechanism Keys

Seven approved values:

| `answer_mechanism_key` | When to use |
|---|---|
| `evidence_location` | Find a specific span of text that directly answers the question |
| `inference` | Deduce a conclusion not stated but logically required |
| `data_synthesis` | Integrate graphic data with surrounding passage text |
| `evidence_matching` | Match a proposed claim to the most logically supportive option |
| `contextual_substitution` | Test words by substituting each into the passage |
| `rhetorical_classification` | Identify the type of rhetorical move or structural pattern |
| `cross_text_comparison` | Hold two passage summaries in mind and determine their relationship |

---

## 8. Solver Pattern Keys

Eight approved values:

| `solver_pattern_key` | When to use |
|---|---|
| `find_evidence_in_text` | Locate and cite specific text |
| `read_data_and_text_together` | Cross-reference data with passage claim |
| `trace_argument_structure` | Follow the logical chain of reasoning |
| `predict_from_preceding` | Most logically completes; answer must follow prior content |
| `substitute_and_test_meaning` | Test each option by substitution into blank |
| `compare_two_passage_positions` | Hold two passages simultaneously to find relationship |
| `classify_ rhetorical_function` | Categorize the function of a sentence or passage |
| `identify_pattern_in_passage` | Recognize the organizational pattern |

---

## 9. Reasoning Trap Keys

### 9.1 Information and Ideas (16 traps)

- `surface_similarity_bias` — option shares words with passage but doesn't match logically
- `scope_blindness` — student cannot distinguish claim scope (overreach/underreach)
- `extreme_word_trap` — option uses "always," "never," "most," "only" where passage is qualified
- `chronological_assumption` — student treats sequence in passage as causation
- `topic_association` — option mentions same topic but wrong logical relationship
- `nearest_detail_fixation` — student selects option anchored to a local detail
- `overreading` — reading more into the passage than it contains
- `underreading` — missing the full scope or implication
- `inverse_logic` — option inverts the direction of reasoning
- `partial_evidence_match` — evidence partially matches but doesn't fully support
- `data_misreading` — misreading a value, axis, or scale in table/graph
- `confound_confusion` — student confuses correlation with causation
- `wrong_data_window` — selecting data from the wrong time point or condition
- `individual_from_aggregate` — drawing individual conclusions from group data
- `all_measures_not_checked` — verifying one measure but not all relevant data
- `control_group_misidentification` — misidentifying which group is the control

### 9.2 Craft and Structure (13 traps)

- `connotation_surface_match` — matching connotation without verifying denotation
- `rhetorical_verb_partial` — rhetorical verb is partially correct but imprecise
- `text_label_swap` — assigning one author's position to the other text
- `false_agreement` — assuming texts agree when they do not
- `polarity_mismatch` — WIC option polarity conflicts with passage register/context
- `register_confusion` — formal/informal, academic/colloquial mismatch
- `denotation_only` — student checks dictionary meaning without verifying contextual fit
- `near_synonym_halo` — student selects near-synonym without checking register/precision
- `parenthetical_misread` — parenthetical element misleads about sentence function
- `transition_assumption` — student assumes a rhetorical move that is not present
- `structure_misclassification` — misclassifying the organizational pattern
- `stance_misread` — misreading the author's evaluative position
- `cross_text_false_equivalence` — treating distinct author claims as equivalent

---

## 10. Text Relationship Keys (Cross-Text Connections)

Six approved values:

| `text_relationship_key` | Meaning |
|---|---|
| `text2_supports_text1` | Text 2's evidence or reasoning reinforces Text 1's claim |
| `text2_contradicts_text1` | Text 2's conclusion is the direct opposite |
| `text2_qualifies_text1` | Text 2 accepts under limited conditions, broadly rejects |
| `text2_critiques_method` | Text 2 challenges method, scope, or design |
| `text2_extends_text1` | Text 2 accepts Text 1 and extends to new domain |
| `independent_agreement` | Both reach the same conclusion independently |

---

## 11. Passage Architecture (Reading-Specific)

### 11.1 Base patterns (7)

Same as core `passage_architecture_key` values. Reading passages additionally
respect these structural norms per skill family.

### 11.2 Experimental architectures (from v1.1 §4.1)

Five additional passage architecture templates for reading:

1. **`null_result_with_implications`**: Study tests a hypothesis, finds no
   significant effect. Passage discusses what the null result implies.

2. **`replication_success`**: Study replicates prior finding with different
   sample/method. Passage emphasizes generalizability.

3. **`replication_failure`**: Study fails to replicate prior finding. Passage
   discusses boundary conditions or methodological differences.

4. **`meta_analysis_synthesis`**: Passage summarizes findings across multiple
   studies, identifying convergent or divergent patterns.

5. **`mechanism_mediation_test`**: Passage tests whether a mediating variable
   explains the relationship between two other variables.

### 11.3 Passage length norms (Digital SAT)

| Skill family | Word count |
|---|---|
| `command_of_evidence_textual` | 100–150 |
| `command_of_evidence_quantitative` | 80–120 (+ table/graph) |
| `central_ideas_and_details` | 100–150 |
| `inferences` | 80–130 |
| `words_in_context` | 50–100 (sentence or short paragraph) |
| `text_structure_and_purpose` | 100–150 |
| `cross_text_connections` | 80–120 per text |

---

## 12. Option-Level Rules (Reading Domain)

### 12.1 Distractor type keys

| `distractor_type_key` | Description |
|---|---|
| `too_broad` | Goes beyond passage scope |
| `too_narrow` | Too specific; misses broader claim |
| `surface_match` | Shares words but wrong relationship |
| `inverse` | Direction of reasoning reversed |
| `extreme` | Passage qualified but option uses extreme language |
| `off_topic` | Relevant to topic but not supported |
| `text_label_swap` | Cross-text; author misassigned |
| `false_agreement` | Claims agreement where there is none |
| `plausible_but_unsupported` | Reasonable claim but passage doesn't support it |
| `partial_match` | Partially correct, partially wrong |
| `wrong_denotation` | Dictionary meaning wrong in context (WIC) |
| `wrong_connotation` | Polar register wrong for context (WIC) |
| `wrong_register` | Incorrect level of formality (WIC) |

### 12.2 Plausibility sources

| `plausibility_source_key` | Description |
|---|---|
| `lexical_overlap` | Option shares vocabulary with passage |
| `near_synonym_appeal` | Word close in meaning; distinction is hard (WIC) |
| `partial_truth` | Part of option is correct |
| `topic_relevance` | Option touches the same broad topic |
| `register_match` | Option matches passage register/formality |
| `structural_resemblance` | Option mirrors passage sentence structure |
| `detail_from_wrong_zone` | Option uses a correct detail from the wrong text or section |
| `common_sense_appeal` | Option appeals to general knowledge, not passage evidence |

### 12.3 Word in Context wrong-answer classification

For every WIC wrong option, classify the student failure at the deepest level
via `option_error_focus_key`:

| `option_error_focus_key` | Level | Meaning |
|---|---|---|
| `wrong_denotation` | Denotation | Word doesn't mean what the blank requires |
| `wrong_connotation` | Connotation | Word has correct denotation but wrong evaluative/emotional tone |
| `wrong_register` | Register | Word has correct denotation and connotation but wrong formality level |

---

## 13. Skill-Specific Annotation Rules

### 13.1 Command of Evidence — Textual

**Evidence span**: The exact passage text that supports the correct claim.
Must be verbatim passage text. If two spans equally support different claims,
the passage is ambiguous — rewrite.

**Two-part claim rule**: When the stem contains two distinct requirements
(e.g., "supports X AND Y"), the evidence span must support both parts. A
partial match is a distractor (`two_part_claim_partial_match`).

**Control-group rule**: When the passage describes a treatment and control
group, the evidence span must distinguish between them. Distractors that
conflate the groups use `control_group_misidentification`.

### 13.2 Command of Evidence — Quantitative

**Mandatory fields**: `table_data` or `graph_data` with structured data.

Eleven quantitative sub-patterns:
1. `direct_value_read` — read exact value from table/chart
2. `simple_comparison_two_bars` — compare two explicit data points
3. `trend_over_time` — identify direction of trend across time points
4. `multi_variable_interaction` — two or more IVs interact
5. `threshold_crossing` — value crosses a meaningful threshold
6. `proportional_comparison` — compare proportions, not raw values
7. `ranking_task` — rank entities by a metric
8. `margin_of_error_awareness` — answer turns on recognizing error bars / uncertainty
9. `null_result_reading` — answer is "no significant difference"
10. `disaggregation_insight` — aggregate hides subgroup differences
11. `ceiling_floor_effect` — answer constrained by measurement limits

Five quantitative-specific reasoning traps:
- `exact_value_misread`
- `wrong_time_window`
- `individual_from_aggregate` (ecological fallacy)
- `all_measures_not_checked`
- `subgroup_overgeneralization`

### 13.3 Central Ideas and Details

Correct main-idea answers must account for every major paragraph or section.
If the passage introduces a qualification in the final sentence, the main
idea must reflect that qualification.

**Parenthetical constraint**: When a passage contains a parenthetical
definition or qualification, the correct main idea must incorporate the
parenthetical's role. Distractors that ignore the parenthetical fail via
`parenthetical_function_confusion`.

### 13.4 Inferences

Inferences must be *logically required*, not merely plausible. If a
reasonable reader could accept or reject the inference based on the same
passage, the stem and distractor set need reconstruction.

**Study design isolation**: The correct inference isolates what the study
design tests. If the study uses random assignment, the inference must reflect
causal language. If observational, causal language in an option is overreach.

**Subgroup overgeneralization**: When the passage only discusses a subgroup
(e.g., "among adolescents from low-income households"), the correct inference
must preserve that subgroup boundary. Options that extend the finding to the
full population fail via `subgroup_overgeneralization`.

**Mechanism-test annotation**: When the passage tests a mechanism, annotate
which variable is the proposed mediator. Wrong options that confuse
correlation with mechanism fail via `overreach`.

### 13.5 Words in Context

**Substitution test**: Replace the target word with each option. The correct
option preserves meaning, register, and connotation. Wrong options fail at
exactly one of the three levels.

See §6.5 for disambiguation rules and the `polarity_fit` rule.

### 13.6 Text Structure and Purpose

**Sentence function annotation**: For `sentence_function` items, annotate
which of the 12 functional roles (§6.6) the underlined sentence serves.
Wrong options name adjacent but incorrect roles.

**`author_stance` annotation**: Classify stance as positive, negative,
qualified/cautious, neutral/descriptive, or skeptical. Wrong options shift
the valence or certainty one category from the true stance.

### 13.7 Cross-Text Connections

**Mandatory field**: `paired_passage_text` must be populated for all
cross-text items. The stem must mention both texts.

**Response-stem critical rule**: When the stem asks for Text 2's response
to Text 1, the correct answer is determined by Text 2's explicit position.
Do not infer a relationship from Text 1 alone.

**Qualified disagreement (from v1.1 §7.1)**: When generating a
`text2_qualifies_text1` item, the passage must explicitly show:
1. Text 1's broad claim
2. Text 2's acceptance of claim under limited conditions
3. Text 2's rejection of claim under other conditions

The three distractors should be:
- Both texts fully agree (*false_agreement*)
- Texts fully contradict (*scope_blindness* — misses qualification)
- Text 2's position is misattributed to Text 1 (*text_label_swap*)

**Cross-Text Connections generation constraints**:
- Always use `stimulus_mode_key: "prose_paired"`
- Both passages must be self-contained and of similar length
- The two passages must have a genuine structural relationship (agreement, contradiction, qualification, methodological critique)
- One distractor should assign the relationship in reverse (swap Text 1 and Text 2 positions)

---

## 14. Student Failure Mode Keys

All 14 approved reading-specific failure mode keys, organized by category:

### Words in Context
- `negation_blindness` — student misses a negative qualifier that reverses meaning
- `polarity_blindness` — student fails to detect that WIC option polarity conflicts with passage context
- `connotation_surface_match` — matches connotation without verifying denotation

### Quantitative
- `exact_value_misread` — misreads a specific value in table/graph data
- `wrong_time_window` — selects data from the wrong time period
- `individual_from_aggregate` — draws individual-level conclusion from aggregate data
- `all_measures_not_checked` — confirms one measure but not all relevant ones
- `subgroup_overgeneralization` — extends subgroup finding to whole population

### Command of Evidence
- `two_part_claim_partial_match` — verifies only half of a two-part claim
- `control_group_misidentification` — misidentifies which group is the control

### Inference
- `evidence_scope_mismatch` — cites evidence supporting narrower/broader claim

### Text Structure and Purpose
- `rhetorical_verb_partial` — rhetorical verb partially correct but imprecise
- `parenthetical_function_confusion` — misidentifies function of a parenthetical

### Cross-Text
- `wrong_comparison_direction` — inverts the direction of a comparison

---

## 15. Reading Difficulty Calibration

### Per-skill difficulty profiles:

| Skill | Low | Medium | High |
|---|---|---|---|
| `command_of_evidence_textual` | Claim directly in text; evidence span short | Claim requires paragraph-level comprehension | Claim requires cross-text synthesis |
| `command_of_evidence_quantitative` | Single value read | Two variables compared | Multi-variable interaction + inference |
| `central_ideas_and_details` | Topic sentences directly convey idea | Need to integrate across paragraph breaks | Need to reconcile nuance/qualification |
| `inferences` | One-step logical completion | Requires integration of two passage facts | Requires distinguishing confound from mechanism |
| `words_in_context` | Common word; one meaning fits | Near-synonyms; register fit | Near-synonyms; polarity_fit with negator |
| `text_structure_and_purpose` | Single identifiable purpose | Function of specific sentence | Distinguish among close rhetorical verbs |
| `cross_text_connections` | Simple agree/disagree | Qualified agreement | Methodological critique |

---

## 16. Generation Rules

### 16.1 Mandatory generation output

Every generated reading item must produce:
- Complete passage text(s) of appropriate length per §11.3
- Stem using an approved `stem_type_key` from core §5.2
- Four options: one correct, three distractors
- Each distractor with `student_failure_mode_key`, `why_plausible`, `why_wrong`
- For WIC items: wrong-answer `option_error_focus_key` at the three-level distinction

### 16.2 Cross-Text generation constraints

- Always `stimulus_mode_key: "prose_paired"`
- Always populated `paired_passage_text`
- Both passages same length band (80-120 words)
- Genuine structural relationship (agree/disagree/qualify/critique)
- One distractor reverses Text 1/Text 2 positions

### 16.3 Quantitative generation constraints

- Always `stimulus_mode_key: "prose_plus_table"` or `"prose_plus_graph"`
- `table_data` or `graph_data` populated with structured data
- At least one distractor using `exact_value_misread`

### 16.4 Stem wording conventions

- `choose_best_support`: "Which quotation from the text most directly supports..."
- `choose_best_illustration`: "Which finding, if true, would most directly illustrate..."
- `choose_best_weakener`: "Which finding, if true, would most directly weaken..."
- `choose_best_completion_from_data`: "Which choice completes the text so that it accurately reflects the data?"
- `choose_main_idea`: "Which choice best expresses the main idea of the text?"
- `choose_detail`: "According to the text, ..."
- `most_logically_completes`: "Which choice most logically completes the text?"
- `choose_word_in_context`: "As used in the text, what does the word '...' most nearly mean?"
- `choose_main_purpose`: "Which choice best describes the overall purpose of the text?"
- `choose_sentence_function`: "Which choice best describes the function of the underlined sentence?"
- `choose_text_relationship`: "Which choice best describes the relationship between the two texts?"
- `choose_agreement_across_texts`: "On which point would the authors of Text 1 and Text 2 most likely agree?"
- `choose_difference_across_texts`: "How would the author of Text 2 most likely respond to the claim in Text 1?"

### 16.5 Generation profile extension fields (reading)

```json
{
  "target_skill_family_key": "words_in_context",
  "target_reading_focus_key": "polarity_fit",
  "target_reasoning_trap_key": "polarity_mismatch",
  "target_quantitative_sub_pattern": null,
  "text_relationship_key": null,
  "paired_text_role": null,
  "sentence_function_role_key": null,
  "target_student_failure_mode": "negation_blindness",
  "option_error_distribution": {
    "wrong_denotation_count": 1,
    "wrong_connotation_count": 1,
    "wrong_register_count": 1
  }
}
```

---

## 17. Disambiguation Rules

Six priority rules for resolving reading classification conflicts:

1. **Cross-Text before Text Structure**: If a paired-text stem asks about
   "relationship" or "response," classify as `cross_text_connections`, even
   if a structure-analysis reading is possible.

2. **CoE before Inference**: If the stem asks "which quotation/finding supports"
   or provides explicit options to evaluate against the passage, classify as
   `command_of_evidence_textual` or `command_of_evidence_quantitative`.

3. **Inference before Central Idea**: If the stem uses "most logically
   completes" or "suggests/infers" with a blank at passage end, classify as
   `inferences`.

4. **WIC when blank tests word meaning**: If the blank substitutes a single
   word or the stem asks for meaning of an underlined word, classify as
   `words_in_context`.

5. **Quantitative when table/graph data is decision-critical**: If the
   correct answer cannot be determined without the data, classify as
   `command_of_evidence_quantitative`.

6. **Skill family key must be singular**: Do not populate `secondary_reading_focus_keys`
   unless a genuine secondary skill is tested (rare in official SAT).

---

## 18. Forbidden Patterns

- **No grammar key leakage**: `grammar_role_key`, `grammar_focus_key`,
  `syntactic_trap_key` must be null/omitted in reading items.
- **No knowledge-dependent passages**: Passage must not assume cultural,
  historical, or scientific knowledge.
- **No ambiguous evidence**: If two options are equally supported, the
  passage is invalid.
- **No single-text cross-text stems**: Do not use cross-text stems without
  `paired_passage_text`.
- **No quantitative stems without data**: Do not use CoE-Quant stems
  without `table_data` or `graph_data`.
- **No colloquial register in passages or options**: All output must be
  formal academic English.
- **No extreme-language correct answers**: Correct options must not use
  "always," "never," or "only" unless the passage uses equally absolute language.
- **No correct answers that merely paraphrase the question**: The correct
  option must add genuine reasoning.

---

## 19. Reading Validator Checklist

### Base checks (14 items):
- [ ] `grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key` are null/omitted
- [ ] `domain` is `Information and Ideas` or `Craft and Structure`
- [ ] `skill_family_key` is one of the 7 approved values
- [ ] `reading_focus_key` maps to the correct `skill_family_key`
- [ ] `question_family_key` is `information_and_ideas` or `craft_and_structure`
- [ ] `reasoning_trap_key` is from the approved lists (§9) and relevant to the skill
- [ ] `answer_mechanism_key` is one of the 7 approved values
- [ ] `solver_pattern_key` is one of the 8 approved values
- [ ] `evidence_span_text` is verbatim passage text (not paraphrased)
- [ ] `evidence_scope_key` and `evidence_location_key` are populated
- [ ] All distractors have `student_failure_mode_key`, `why_plausible`, `why_wrong`
- [ ] Cross-text items have `paired_passage_text` populated
- [ ] Quantitative items have `table_data` or `graph_data` populated
- [ ] `topic_broad` and `topic_fine` are present

### v1.1 additional checks (9 items):
- [ ] WIC items annotate `polarity_context` in `review_notes` when a negator is present
- [ ] WIC wrong-answer `option_error_focus_key` is at the correct three-level depth
- [ ] `polarity_fit` items include the negator in `evidence_span_text`
- [ ] `sentence_function` items reference one of the 12 approved roles
- [ ] `cross_text_connections` items include `text_relationship_key`
- [ ] `command_of_evidence_quantitative` items include `quantitative_sub_pattern`
  when a recognized pattern is present
- [ ] `two_part_claim` distractors verify both parts are needed for correctness
- [ ] `study_design_isolation` items annotate design type (observational/experimental)
- [ ] `qualified_disagreement` items include three required structural elements

---

## 20. Amendment Process (Reading-Specific)

Reading-domain amendment proposals must use `proposed_parent_key` set to an
existing `skill_family_key`. Include `frequency_estimate`, `example_count`,
and `examples` as required by core §16.

Do not insert proposed keys into production records until reviewed and promoted.
