# rules_agent_dsat_reading_v2.md

## Purpose

This file is the consolidated reading-comprehension rules layer. It merges:

- `rules_agent_dsat_reading_v1.md` (v1.0, 2026-04-25) — base taxonomy
- `rules_agent_dsat_reading_v1_1.md` (v1.1, 2026-04-29) — PT4–PT11 gap-analysis addendum

All v1.1 additions are incorporated at their target sections. No dual loading required.

The grammar companion file covers:
- Standard English Conventions (SEC)
- Grammar-adjacent Expression of Ideas (Transitions, Rhetorical Synthesis)

This file covers the remaining two domains:

- **Information and Ideas** — Command of Evidence (Textual and Quantitative),
  Central Ideas and Details, Inferences
- **Craft and Structure** — Words in Context, Text Structure and Purpose,
  Cross-Text Connections

Together, these two files form the full production annotation specification
for all Digital SAT Reading & Writing question types.

**Do not apply `grammar_role_key` or `grammar_focus_key` to any question
classified under `information_and_ideas` or `craft_and_structure`. Those
fields must be `null` or omitted for all questions covered by this file.**

---

## Source Authority

Rules in this document are derived from:

- College Board Digital SAT Test Specifications (2024–2026)
- Khan Academy SAT Reading & Writing course (khanacademy.org)
- College Board Bluebook sample items
- College Board official answer explanations for PT4–PT11
  (cross-referenced in `CB_ANSWERS_QUESTIONS_ANALYSIS.md`)
- PrepScholar, PrepMaven, Manhattan Review, Test Ninjas, UWorld, TestPrepKart
  practitioner analyses of released Digital SAT items

---

## 1. Operating Principles

### 1.1 Separate the tasks

For every question, separate:

1. what the item tests (skill family and focus)
2. how the item is structured (stimulus mode, stem type)
3. what evidence mechanism solves it
4. why the correct answer is correct
5. why each wrong option is tempting
6. why each wrong option is wrong
7. what pattern should be used to generate a similar item

### 1.2 Do not write directly to the database

The agent must output structured JSON or markdown records for validation.
A deterministic backend validator checks all keys before insertion.

### 1.3 Use controlled keys

The agent must use only approved lookup keys from this file. If no key fits,
propose an amendment using the amendment process (§20) rather than inventing a
production key.

### 1.4 Evidence over inference

The SAT's evidentiary standard for all reading domains is "indicated in or
directly supported by the text." Correct answers are never merely consistent
with the text — they are required by it. Classify accordingly.

### 1.5 Domain isolation

Questions in `information_and_ideas` and `craft_and_structure` are never
reclassified into SEC even if grammar-like terminology appears in the passage.
Domain classification is determined by what cognitive skill the correct answer
requires, not by what appears in the question stem verbatim.

---

## 2. Required Output Shape

Every item annotation must produce these sections, mirroring the grammar file:

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

### 2.1 `reasoning` section schema

```json
{
  "primary_rule": "The reading skill or evidence mechanism that selects the correct answer.",
  "trap_mechanism": "How the primary wrong-answer trap misleads test-takers.",
  "correct_answer_reasoning": "Step-by-step justification for the correct option.",
  "distractor_analysis_summary": "One-sentence summary of why the three wrong options fail.",
  "similar_items": [
    {
      "pattern": "sentence template or passage template describing the structural pattern",
      "focus_key": "reading_focus_key",
      "trap_key": "reasoning_trap_key"
    }
  ]
}
```

### 2.2 `generation_profile` section schema

```json
{
  "target_skill_family_key": "command_of_evidence_textual",
  "target_reading_focus_key": "evidence_supports_claim",
  "target_test_construct_key": "evidence_relation_precision",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "choose_best_support",
  "distractor_pattern": [
    "one topically related but logically disconnected distractor",
    "one indirect/downstream evidence distractor",
    "one inverted logic distractor"
  ],
  "passage_template": "Template describing passage structure and the claim to be supported.",
  "polarity_context": null,
  "target_sentence_function_role": null,
  "quantitative_sub_pattern": null,
  "passage_architecture_key": null,
  "inference_type_note": null,
  "two_part_claim": false,
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0"
}
```

Additional generation profile fields (mandatory when the corresponding condition applies):

| Field | Mandatory when |
|---|---|
| `polarity_context` | `target_reading_focus_key` is `polarity_fit` |
| `target_sentence_function_role` | `target_reading_focus_key` is `sentence_function` |
| `quantitative_sub_pattern` | `target_skill_family_key` is `command_of_evidence_quantitative` |
| `passage_architecture_key` | passage uses one of the five experimental architectures (§15.2) |
| `inference_type_note` | passage architecture is `mechanism_manipulation_test` or `studied_subgroup_generalization_limit` |
| `two_part_claim` | `target_reading_focus_key` is `evidence_illustrates_claim` |
| `target_test_construct_key` | all generated reading-domain items |
| `target_craft_subconstruct_key` | `question_family_key` is `craft_and_structure` |

### 2.3 Test construct keys

Use `target_test_construct_key` to name the cognitive construct being tested.
This is separate from `reading_focus_key`: the focus key names the SAT skill
bucket, while the construct key names the exact reasoning operation that makes
the correct answer uniquely best.

Approved values:

- `contextual_semantic_precision` — the student must choose the word or phrase
  whose meaning, connotation, and logical role fit the local context
- `rhetorical_function_precision` — the student must identify what a sentence,
  phrase, or passage is doing rhetorically, not merely what topic it mentions
- `cross_text_relationship_precision` — the student must identify agreement,
  disagreement, qualification, or response between two labeled texts
- `evidence_relation_precision` — the student must match evidence to a claim
  without using merely related or downstream information
- `inference_boundary_control` — the student must infer only what the passage
  supports and avoid overextension
- `quantitative_constraint_tracking` — the student must apply the exact row,
  column, time window, comparison, or aggregate constraint in a graph/table item
- `figurative_interpretation_precision` — the student must recognize that a word or phrase is used metaphorically, idiomatically, or figuratively and select the option that captures the non-literal meaning; the literal definition of the target word is always represented among the distractors

### 2.4 Craft subconstruct keys

Use `target_craft_subconstruct_key` for Craft and Structure generation and
annotation. It prevents Craft items from being treated as a single generic
"reading" task.

Approved values:

- `wic_local_semantic_role` — Words in Context; the answer must satisfy the
  word's role in the sentence or passage logic
- `wic_tone_register_fit` — Words in Context; the answer must match the author's
  stance, register, or evaluative valence
- `wic_polarity_logic` — Words in Context; the answer must preserve negation,
  concession, or double-negative logic
- `tsp_global_rhetorical_purpose` — Text Structure and Purpose; the answer names
  the whole passage's dominant rhetorical purpose
- `tsp_local_sentence_function` — Text Structure and Purpose; the answer names
  what a sentence or phrase does locally within the passage
- `tsp_author_action_precision` — Text Structure and Purpose; the answer uses
  the correct action verb for the author's move
- `ctc_agreement_degree` — Cross-Text; the answer identifies exact agreement,
  qualified agreement, disagreement, or limitation
- `ctc_attribution_tracking` — Cross-Text; the answer keeps Text 1 and Text 2
  claims, evidence, and authors separate
- `ctc_response_to_claim` — Cross-Text; the answer predicts how one author or
  research team would respond to a specific claim in the other text

### 2.5 `review` section schema

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
  "source_exam": "PT1",
  "source_section": "RW",
  "source_module": "M1",
  "source_question_number": 14,
  "stimulus_mode_key": "prose_single",
  "stem_type_key": "choose_best_support",
  "prompt_text": "...",
  "passage_text": "...",
  "paired_passage_text": null,
  "notes_bullets": [],
  "table_data": null,
  "graph_data": null,
  "correct_option_label": "C",
  "explanation_short": "...",
  "explanation_full": "...",
  "evidence_span_text": "The exact span of passage text that anchors the correct answer."
}
```

### 3.1 stimulus_mode_key values (reading-relevant)

- `sentence_only` — single sentence with blank
- `passage_excerpt` — short excerpt, typically one to three sentences
- `prose_single` — one labeled prose passage (Text or Passage)
- `prose_paired` — two labeled passages (Text 1 and Text 2) — required for Cross-Text Connections
- `prose_plus_table` — prose with an embedded data table
- `prose_plus_graph` — prose with an embedded bar chart, line graph, or scatter plot
- `notes_bullets` — bulleted note list (rare in reading domains)
- `poem` — poetic extract

> **Cross-Text Connections always requires `prose_paired`.** Any Cross-Text question
> with `stimulus_mode_key` other than `prose_paired` is a classification error.

> **Command of Evidence — Quantitative always requires `prose_plus_table` or
> `prose_plus_graph`.** Questions without a graphic cannot be classified as
> `command_of_evidence_quantitative`.

### 3.2 stem_type_key values for reading domains

The following stem types apply specifically to reading-domain questions.
Grammar-domain stem types (`choose_best_grammar_revision`, `choose_best_transition`,
`choose_best_notes_synthesis`) do not apply here.

| Key | Canonical stem wording | Domain |
|---|---|---|
| `choose_best_support` | "Which choice best supports the claim that…" / "Which finding, if true, would most directly support…" | Information and Ideas |
| `choose_best_illustration` | "Which quotation from [work] would most effectively illustrate the claim…" | Information and Ideas |
| `choose_best_weakener` | "Which finding, if true, would most directly undermine / challenge…" | Information and Ideas |
| `choose_best_completion_from_data` | "Which choice most effectively uses data from the [table/graph] to…" | Information and Ideas |
| `choose_main_idea` | "Which choice best states the main idea of the text?" / "Which choice most accurately summarizes the text?" | Information and Ideas |
| `choose_detail` | "Based on the text, what is true about…?" / "The text indicates that…?" | Information and Ideas |
| `most_logically_completes` | "Which choice most logically completes the text?" | Information and Ideas |
| `choose_word_in_context` | "Which choice completes the text with the most logical and precise word or phrase?" / "As used in the text, what does the word '[word]' most nearly mean?" | Craft and Structure |
| `choose_main_purpose` | "Which choice best states the main purpose of the text?" / "Which choice best describes what the text does?" | Craft and Structure |
| `choose_sentence_function` | "Which choice best describes the function of the underlined sentence in the text as a whole?" | Craft and Structure |
| `choose_text_relationship` | "Based on the texts, how would [author/researchers in Text 2] most likely describe / respond to [Text 1]?" | Craft and Structure |
| `choose_agreement_across_texts` | "Based on the texts, both [Text 1 source] and [Text 2 source] would most likely agree with which statement?" | Craft and Structure |
| `choose_difference_across_texts` | "Which choice best describes a difference between the claims made in Text 1 and Text 2?" | Craft and Structure |

---

## 4. Classification Fields

```json
{
  "domain": "Information and Ideas",
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "evidence_supports_claim",
  "secondary_reading_focus_keys": [],
  "reasoning_trap_key": "topical_relevance_without_logical_connection",
  "evidence_scope_key": "passage",
  "evidence_location_key": "main_clause",
  "answer_mechanism_key": "evidence_location",
  "solver_pattern_key": "locate_claim_then_match_evidence",
  "grammar_role_key": null,
  "grammar_focus_key": null,
  "topic_broad": "science",
  "topic_fine": "ecology",
  "reading_scope": "passage-level",
  "reasoning_demand": "evidence_matching",
  "register": "academic informational",
  "tone": "neutral",
  "difficulty_overall": "medium",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "medium",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "The correct option directly demonstrates the stated hypothesis; all three distractors mention related phenomena but do not address the specific causal relationship the hypothesis predicts."
}
```

> `grammar_role_key` and `grammar_focus_key` must always be `null` for questions
> in this file's domains. The validator rejects non-null grammar keys in these domains.

---

## 5. Question Family Keys

Two controlled values for all questions in this file:

- `information_and_ideas`
- `craft_and_structure`

### 5.1 When to use `information_and_ideas`

The question requires the student to:
- Match evidence to a claim (textual or quantitative)
- Identify the central idea or a specific supporting detail
- Complete a logical inference from supplied information

Sub-skills: `command_of_evidence_textual`, `command_of_evidence_quantitative`,
`central_ideas_and_details`, `inferences`

### 5.2 When to use `craft_and_structure`

The question requires the student to:
- Determine the most contextually precise word or phrase
- Identify the purpose or structure of a text or text element
- Analyze the relationship between two paired texts

Sub-skills: `words_in_context`, `text_structure_and_purpose`, `cross_text_connections`

---

## 6. Skill Family Keys

Use `skill_family_key` to classify within the domain. One of these seven values:

- `command_of_evidence_textual`
- `command_of_evidence_quantitative`
- `central_ideas_and_details`
- `inferences`
- `words_in_context`
- `text_structure_and_purpose`
- `cross_text_connections`

---

## 7. Reading Focus Keys

Use the most specific applicable `reading_focus_key`.

### 7.1 Command of Evidence — Textual focus keys

- `evidence_supports_claim` — correct option directly proves the stated hypothesis/claim
- `evidence_weakens_claim` — correct option undermines or contradicts the stated claim
- `evidence_illustrates_claim` — literary variant; correct option is a quotation that exemplifies an interpretive claim
- `evidence_explains_claim` — correct option provides the causal mechanism behind the claim
- `evidence_qualifies_claim` — correct option shows a condition under which the claim does not hold

### 7.2 Command of Evidence — Quantitative focus keys

- `data_supports_claim` — correct option selects accurate data that directly validates the passage's argument
- `data_weakens_claim` — correct option selects accurate data that contradicts the passage's argument
- `data_completes_example` — correct option fills a blank sentence with the most relevant and precise data point
- `data_comparison` — correct option requires comparing two or more data values (e.g., highest vs. lowest)
- `data_trend` — correct option requires recognizing a directional pattern in the graphic

### 7.3 Central Ideas and Details focus keys

- `central_idea` — correct option captures the author's main point across the whole passage
- `main_purpose` — correct option states what the author is doing rhetorically (overlaps with Text Structure and Purpose; use Text Structure and Purpose if the stem asks "purpose" and the focus is rhetorical move)
- `passage_summary` — correct option accurately summarizes the full passage
- `supporting_detail` — correct option identifies a specific fact or claim stated in the passage
- `character_or_author_detail` — literary passages only; correct option describes a stated attribute, action, or feeling of a character or narrator

### 7.4 Inferences focus keys

- `causal_inference` — the blank requires the most logical cause or effect given the passage context
- `motivational_inference` — correct option infers what a person, group, or researcher must believe or intend
- `implication_inference` — correct option identifies what the passage implicitly rules in or out
- `predictive_inference` — correct option identifies the most likely outcome given the passage's evidence
- `cross_text_inference` — cross-text variant; correct option infers how one text's author would react to the other

### 7.5 Words in Context focus keys

- `contextual_meaning` — correct word determined by surrounding sentences (most common variant)
- `connotation_fit` — near-synonyms; correct word determined by evaluative or emotional register
- `precision_fit` — correct word is the most specific/precise among near-synonyms
- `register_fit` — correct word matches the academic, formal, or technical register
- `underlined_word_meaning` — "most nearly mean" stem; word is underlined rather than blank
- `polarity_fit` — correct word must preserve logical polarity when a negator or concessive is present
- `figurative_language_meaning` — target word or phrase is used metaphorically, idiomatically, or figuratively in the passage; correct answer captures the non-literal meaning; the literal dictionary definition of the word is always one of the wrong options

**Reading focus disambiguation for Words in Context:**

- If all four options are near-synonyms and the distinction is evaluative/tonal → `connotation_fit`
- If the distinction is degree of specificity → `precision_fit`
- If the blank or word is in a passage with a pronounced formal or technical register → `register_fit`
- If stem uses "most nearly mean" with an underlined word → `underlined_word_meaning`
- If the passage contains a negator, concessive phrase, or contrast marker and all options are near-synonyms differing in evaluative direction when the negator is applied → `polarity_fit`
- If the target word or phrase is clearly used non-literally (metaphorically, idiomatically) and the literal dictionary definition would be incoherent in the passage logic → `figurative_language_meaning`
- Otherwise → `contextual_meaning` (default)

**`polarity_fit` rule definition:**

The passage contains a negator, a concessive phrase, or a double-negative
construction ("by no means," "not atypical," "hardly insignificant") that
reverses or qualifies the polarity of the target word or phrase. The correct
word must preserve the logical polarity of the full construction, not the
surface meaning of the surrounding words taken in isolation. Wrong answers
select a word that is correct for the surface context but inverts the meaning
when the negator is applied.

**Mandatory annotation requirement for `polarity_fit`:**

For every WIC item where a negator, concessive phrase, or contrast marker
is present within the evidence span, annotate `evidence_span_text` with
the full phrase including the negator, not just the word immediately
surrounding the blank. Example: annotate "by no means ______" not just
"______."

Add to `review_notes`: "polarity_context: [name the negator or concessive]."

**Generation rule for `polarity_fit`:**

When generating a `polarity_fit` item:
- Embed a negator, concessive, or double-negative construction in the
  passage at or adjacent to the blank
- All four options must be grammatically viable after the negator
- The correct option must produce the intended meaning when combined
  with the negator
- At least two wrong options must produce the opposite or an illogical
  meaning when combined with the negator — do not use options that are
  simply off-topic

Example construction:
```
The critic found the performance by no means ______ ; every detail
had been carefully rehearsed.
```
Correct: "unremarkable" (meaning it was remarkable, double negation)
Wrong traps: "brilliant" (ignores negator), "adequate" (ignores
negation direction), "poor" (inverts to wrong direction)

### 7.6 Text Structure and Purpose focus keys

- `overall_purpose` — correct option states what the text as a whole does (infinitive verb phrase)
- `sentence_function` — correct option describes the rhetorical role of one underlined sentence or paragraph
- `structural_pattern` — correct option identifies the organizational pattern (problem-solution, compare-contrast, etc.)
- `author_stance` — correct option identifies the author's evaluative position toward the subject

### 7.7 Cross-Text Connections focus keys

- `text2_response_to_text1` — how Text 2's author or evidence would characterize or respond to Text 1's claim
- `both_texts_agree` — the simplest claim both texts endorse without contradiction
- `texts_disagree` — the key point of divergence between Text 1 and Text 2's claims
- `text2_qualifies_text1` — Text 2 accepts Text 1's claim under specific conditions while rejecting it broadly
- `text2_contradicts_text1` — Text 2's conclusion is the opposite of Text 1's
- `methodological_critique` — Text 2 challenges Text 1's method or scope rather than its conclusion
- `expectation_violation` — Text 2 researchers expected Text 1's theory to hold but found contrary evidence

---

## 8. Answer Mechanism Keys

Use `answer_mechanism_key` to describe the cognitive process required to select the correct answer.

| Key | When to use |
|---|---|
| `evidence_location` | The student must find a specific span of text that directly answers the question |
| `inference` | The student must deduce a conclusion not explicitly stated but logically required |
| `data_synthesis` | The student must integrate a graphic with the surrounding passage text |
| `evidence_matching` | The student must match a proposed claim to the most logically supportive option |
| `contextual_substitution` | The student must test words by substituting each into the passage to find the best fit |
| `rhetorical_classification` | The student must identify the type of rhetorical move or structural pattern |
| `cross_text_comparison` | The student must hold two passage summaries in mind and determine their relationship |
| `polarity_resolution` | The student must identify the logical direction imposed by a negating or concessive construction, then select the word that preserves the intended meaning when combined with that negation |

---

## 9. Solver Pattern Keys

Use `solver_pattern_key` to describe the step-by-step solving strategy.

| Key | Description |
|---|---|
| `locate_claim_then_match_evidence` | Identify the claim → pre-answer → test options against exact claim |
| `read_graphic_then_match_claim` | Read passage intent → pre-identify ideal data pattern → test each option |
| `summarize_then_compare` | Summarize passage in one sentence → compare to options |
| `locate_detail_directly` | Find the specific sentence → select matching option |
| `identify_logical_gap` | Break passage into propositions → find gap → bridge without overstepping |
| `substitute_and_test` | Insert each word option into the blank → evaluate naturalness and tone |
| `classify_rhetorical_move` | Identify the action verb of the rhetorical move → match to option's infinitive phrase |
| `summarize_both_then_compare` | Summarize Text 1 → summarize Text 2 → identify relationship type |
| `apply_negation_logic` | Identify the negator or concessive → determine the required logical direction under negation → substitute each option combined with the negator → select the option that produces the author's intended meaning |
| `locate_figurative_function` | Identify what literal meaning would produce in the sentence → recognize the incoherence → infer the figurative or idiomatic function → match to the option that names that function |

---

## 10. Reasoning Trap Keys

Use `reasoning_trap_key` to record the single most dangerous wrong-answer mechanism
for the **question as a whole**. Choose exactly one key from §10.1 or §10.2 below.

Per-option wrong-answer mechanisms are recorded separately in each option's
`distractor_type_key` field — use the §12.1 list for that field, not this one.
The two vocabularies overlap but are **not interchangeable**: `reasoning_trap_key`
(question-level) is drawn only from §10; `distractor_type_key` (option-level) is
drawn only from §12.1.

### 10.1 Information and Ideas reasoning trap keys

- `topical_relevance_without_logical_connection` — option mentions the same subject but does not prove or disprove the claim
- `partial_match` — option addresses one element of a multi-part claim while ignoring another
- `indirect_evidence` — option shows a downstream or secondary effect rather than the core causal relationship
- `inverted_logic` — option supports when the question asks to weaken, or weakens when asked to support
- `keyword_matching` — option contains vocabulary from the claim but lacks the required logical relationship
- `single_sector_focus` — quantitative; option states a true fact about one data point without meaningful comparison
- `data_context_mismatch` — quantitative; data reading is accurate but does not answer the passage's research question
- `detail_trap` — uses a real fact from the passage but misses the main idea
- `topic_trap` — names the correct topic but not the author's point about it
- `overreach` — adds an idea the author never claimed; goes beyond what the text supports
  - *Implied claim elevated to purpose* — distractor promotes a supporting fact or piece of evidence to the status of the passage's primary purpose or main claim; the promoted element is real and present in the text but functions as support, not as the point; distinct from `partial_purpose` (which misidentifies a supporting *rhetorical move*) — this misidentifies a supporting *fact or reason* as the central assertion
- `contradiction` — states the opposite of what the text says or implies
- `absolute_language` — uses "always," "never," "all," "none" — the SAT rarely places absolute claims in correct answers
- `outside_knowledge` — true in the real world but not stated or implied by the passage
- `cause_effect_misalignment` — proposes a relationship the passage does not establish
- `scope_extension` — applies a conclusion to a population or domain the passage does not address
- `overspecification` — correct in direction but too specific (e.g., names a sub-group the passage does not specify)
- `wrong_time_window` — quantitative; option uses real data that is accurate for a different time period than the one the passage's constraint specifies
- `direction_reversal` — quantitative; option correctly identifies the variable being tracked but states the opposite direction of change
- `wrong_table_row_or_column` — quantitative; option uses the correct table/graph but selects the wrong row, column, category, bar, or plotted point identifier
- `wrong_group_comparison` — quantitative; option compares the wrong treatment group, control group, population, or category
- `single_measure_focus` — quantitative; option is true for one measure or one time point but the claim requires the comparison to hold across all listed measures, conditions, or periods
- `local_maximum_trap` — quantitative; option cites a locally high value that is not highest across the full required interval or set
- `same_direction_assumption` — quantitative; option assumes two variables move in the same direction when the data show opposite movement
- `absolute_value_confusion` — quantitative; option accurately describes an absolute count or amount but misses a percentage, proportion, or composition shift
- `constraint_ignored` — quantitative; option is accurate in isolation but ignores a stated timing, population, measurement, or comparison constraint
- `individual_inference_from_aggregate_bins` — quantitative; option infers individual-level facts from binned or aggregate data

### 10.2 Craft and Structure reasoning trap keys

- `common_definition_trap` — selects the word's most familiar dictionary meaning, which does not fit the passage context
- `semantic_relatedness_without_precision` — word is in the same semantic field but wrong in register or scope
- `connotation_mismatch` — correct denotation but wrong emotional valence (e.g., "curious" vs. "skeptical")
- `plausible_synonym` — a synonym of the correct answer that sounds reasonable in isolation but fails in context
- `also_true_trap` — option describes something mentioned in the passage but is not the *main* purpose
- `wrong_scope` — option accurately describes one sentence applied to the whole text, or vice versa
- `wrong_action_verb` — content description is accurate but the rhetorical verb is wrong (e.g., "to challenge" vs. "to describe")
- `overstated_position` — author presents balanced information; option claims the author argues or advocates
- `partial_purpose` — captures a supporting move (provide an example) but not the overall purpose (argue that X)
- `scope_error` — option introduces a subject, time frame, population, or domain that the passage does not address; the distractor is plausible because its topic is adjacent to the passage's topic, but its scope is invented or extended beyond what the text covers
  - *Invented temporal scope* — distractor adds a time reference ("today," "currently," "in earlier decades") not present in the passage; most tempting when the passage's own time frame is explicit and the added reference sounds like a natural complement (e.g., passage covers the late 1800s; distractor claims the purpose is to compare with the present)
  - *Invented geographic or audience scope* — distractor extends the passage's subject to a population or place the passage mentions only as context (e.g., passage explains a city's demographics to explain a local trend; distractor claims the purpose involves that population as an audience or market)
  - *Invented comparative purpose* — distractor frames the passage's purpose as comparing X with Y, but the passage only describes or explains X; Y appears as a data point or contrast for scale, not as a co-subject of equal focus (e.g., passage describes El Paso's newspaper output; distractor says "to compare El Paso's newspapers with San Antonio's"); distinct from `relationship_fabrication` which invents causation — this invents a *comparison frame*
  - *Agent scope shift* — distractor attributes the passage's purpose to a different actor than the one the passage focuses on; the second actor either does not appear in the passage or is mentioned only in passing (e.g., passage explains what researchers discovered; distractor says the purpose is to explain what policymakers or students should do); most tempting when the passage's topic has obvious real-world stakeholders who are never actually mentioned
- `relationship_fabrication` — option implies a causal, influential, or directional relationship between two elements the passage mentions separately but never connects; the passage may contrast or compare them (different quantities, different roles) but makes no claim about one affecting the other; most common in main-purpose and sentence-function items where the passage juxtaposes two subjects for scale or context rather than to establish causation or influence
- `reversed_attribution` — facts from Text 1 attributed to Text 2 or vice versa — most common Cross-Text trap
- `extreme_language` — uses "always," "never," "completely," "impossible" — signals incorrect option in Cross-Text
- `textual_mimicry` — uses vocabulary directly from the passage but distorts the meaning or relationship
- `confirmed_when_contradicted` — describes Text 2 as supporting Text 1 when it contradicts it, or vice versa
- `polarity_mismatch` — the option is a plausible word in isolation but inverts the intended meaning when combined with the passage's negator or concessive construction; the student selected the option by reading the surrounding words without applying the negator to the target blank
- `local_semantic_role_mismatch` — word or phrase is topically plausible but fails the target word's local function in the sentence logic
- `tone_register_mismatch` — option has the right broad meaning but the wrong level of formality, stance, or evaluative force
- `rhetorical_scope_shift` — option describes a true local detail as if it were the whole passage purpose, or describes the global purpose when the stem asks for a local function
- `author_action_misclassification` — option names the right content but assigns the wrong rhetorical action, such as "refute" instead of "qualify"
- `evidence_relationship_blend` — Cross-Text option merges agreement, disagreement, qualification, or methodological critique into a simpler relationship than the texts support
- `attribution_blend` — Cross-Text option combines a claim from one text with evidence, method, or attitude from the other text
- `agreement_degree_mismatch` — Cross-Text option overstates or understates the degree of agreement between the two texts
- `figurative_literal_confusion` — option selects the literal or dictionary meaning of a word or phrase used figuratively or idiomatically; the literal reading produces a locally coherent sentence but misses the non-literal function established by the broader passage context
- `false_concession_trap` — Cross-Text option characterizes Text 2 as partially conceding or qualifying Text 1 when the actual relationship is full agreement, flat contradiction, or a purely methodological critique; the trap exploits students' tendency to infer nuance where the texts are unambiguous

---

## 11. Text Relationship Keys (Cross-Text Connections)

Use `text_relationship_key` for Cross-Text Connections questions only.

- `direct_contradiction` — authors reach opposite conclusions about the same question
- `confirmation_with_qualification` — Text 2 broadly supports Text 1 but identifies a limiting condition
- `expectation_violation` — Text 2 expected Text 1's theory but found contrary evidence
- `methodological_critique` — Text 2 challenges Text 1's method or scope rather than its conclusion
- `partial_agreement` — authors agree on one aspect while disagreeing on another
- `broad_support` — Text 2 provides additional evidence that corroborates Text 1
- `causal_specification` — Text 2 provides the specific causal mechanism or explanatory pathway for a phenomenon Text 1 describes; Text 2 deepens Text 1 by answering "how" or "why" rather than contradicting, qualifying, or corroborating its conclusion

---

## 12. Option-Level Analysis Rules

Each option must include:

```json
{
  "option_label": "A",
  "option_text": "...",
  "is_correct": false,
  "option_role": "distractor",
  "distractor_type_key": "topical_relevance_without_logical_connection",
  "semantic_relation_key": "same_topic_different_causal_chain",
  "plausibility_source_key": "passage_vocabulary_overlap",
  "option_error_focus_key": "evidence_supports_claim",
  "why_plausible": "Mentions the same subject (marine migration) as the hypothesis.",
  "why_wrong": "Shows a correlation with ocean temperature but does not demonstrate the food-source mechanism the hypothesis predicts.",
  "grammar_fit": "yes",
  "tone_match": "yes",
  "precision_score": 1
}
```

### 12.1 Distractor type keys for reading domains

**For distractors (wrong options):**

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
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `cause_effect_misalignment`
- `contradiction`
- `figurative_literal_confusion`
- `false_concession_trap`

**For the correct option:**

- `correct`

### 12.2 Plausibility sources for reading domains

| Key | When to use |
|---|---|
| `passage_vocabulary_overlap` | Option reuses words from the passage, creating false familiarity |
| `topical_proximity` | Option is about the same general subject as the correct answer |
| `partial_truth` | Option contains one accurate element alongside an inaccurate element |
| `common_sense_appeal` | Option aligns with what is generally true in the world, not what the passage says |
| `common_definition_appeal` | Option uses the dictionary meaning of the target word rather than the contextual meaning |
| `near_synonym_appeal` | Option is a legitimate synonym that fails on connotation or precision |
| `rhetorical_surface_similarity` | Option's action verb sounds like the correct rhetorical move but differs in direction or scope |
| `attribution_swap` | Option correctly describes one text but assigns it to the wrong text |

### 12.3 precision_score scale (reading adaptation)

| Value | Meaning |
|---|---|
| `1` | Incorrect option. Contains a clear error of logic, scope, attribution, or evidence matching. |
| `2` | Partially acceptable but inferior. The option is a defensible reading but is outperformed by the correct answer on specificity or directness. |
| `3` | Correct option. Fully satisfies the evidentiary or reasoning requirement with no compromise. |

### 12.4 grammar_fit and tone_match semantics for reading

These fields retain the same semantics as the grammar file but apply differently in reading domains:

| Field | `yes` | `no` |
|---|---|---|
| `grammar_fit` | The option is grammatically well-formed and stylistically appropriate | The option contains a grammatical error that would make it implausible on surface |
| `tone_match` | The option's language matches the formal or neutral academic register of the SAT | The option is colloquial, uses extreme language, or mismatches the passage's register |

In reading domains, `grammar_fit` is almost always `yes` for all four options; the
distinctions are logical and evidentiary rather than grammatical.

---
## 13. Skill-Specific Annotation Rules

### 13.1 Command of Evidence — Textual

**Mandatory classification fields:**

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

**Stem variant classification:**

| Stem wording | `reading_focus_key` | `stem_type_key` |
|---|---|---|
| "most directly support…" | `evidence_supports_claim` | `choose_best_support` |
| "most directly undermine/challenge/weaken…" | `evidence_weakens_claim` | `choose_best_weakener` |
| "most effectively illustrate the claim…" (quotation) | `evidence_illustrates_claim` | `choose_best_illustration` |

**Mandatory reasoning check:**

Before classifying, confirm the correct option has a *direct causal or logical relationship*
with the specific claim — not merely a topical relationship. Options that are
"relevant to the topic" without directly proving or disproving the claim are
always wrong. Annotate the `evidence_span_text` field with the exact claim text.

**Two-part claim annotation requirement for quote-illustration items:**

For `evidence_illustrates_claim` items (literary quotation variants), the
claim in the stem may have two required elements (e.g., both "X" and "Y").
When annotating or generating such an item:

1. Annotate `evidence_span_text` with the full claim, marking both elements.
2. For every distractor, check whether it satisfies one element but not
   both. If so, annotate `distractor_type_key: "partial_match"` and
   `why_wrong`: "satisfies [element A] but not [element B]."
3. For generation: explicitly construct the claim with two required elements
   and ensure at least one distractor satisfies exactly one of the two.

**Control-group and alternative-cause distractor patterns:**

For items on `alternative_explanation_ruled_out` or
`experiment_hypothesis_control_result` passage architectures, the most
common distractor trap is `topical_relevance_without_logical_connection`:
the wrong option addresses the same general topic (the experiment) but
does not specifically engage with the alternative cause being ruled out
or the control condition being tested. Annotate with
`reasoning_trap_key: "topical_relevance_without_logical_connection"` and
document in `why_wrong` which part of the causal logic the option fails
to address.

### 13.2 Command of Evidence — Quantitative

**Mandatory classification fields:**

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

> `stimulus_mode_key` must be `prose_plus_table` or `prose_plus_graph`. Any question
> without a graphic must not be classified as `command_of_evidence_quantitative`.

**Mandatory annotation:**

Populate `table_data` or `graph_data` fields with the structured data from the graphic.
The `evidence_span_text` field must contain the specific data values cited in the correct option.

**Reading focus disambiguation:**

Extend the three-case rule to cover all confirmed sub-patterns:

| Pattern | `reading_focus_key` | When to use | Primary distractor trap |
|---|---|---|---|
| Single absolute value from a table | `data_completes_example` | Correct option cites one specific cell value | `wrong_row_or_column` — option cites an adjacent cell |
| Comparing two or more values | `data_comparison` | Correct option requires comparing groups, conditions, or time points | `single_sector_focus` — option states one value without comparison |
| Directional trend in a graph | `data_trend` | Correct option identifies a direction (increasing, decreasing, stable) | `direction_reversal` — option states the opposite trend |
| Supports or weakens a claim | `data_supports_claim` / `data_weakens_claim` | Correct option is chosen because of its logical relationship to a passage claim | `data_context_mismatch` — option has accurate data but answers the wrong question |
| Exact lookup constrained by a row or column identifier | `data_completes_example` (with `exact_value_lookup` sub-pattern note) | Correct option requires finding a specific cell identified by two coordinates (row ID + column ID) | `wrong_table_row_or_column` — option uses the right column but wrong row, or right row but wrong column |
| Timing-constrained comparison | `data_comparison` (with `timing_constrained` sub-pattern note) | Correct option must use only data from a specified time window; other windows are excluded by the passage's claim | `wrong_time_window` — option uses real data from a different time window than the passage's constraint |
| All-measures comparison across groups | `data_comparison` (with `all_measures` sub-pattern note) | Correct option requires checking every row or column and confirming the comparison holds across all of them | `single_measure_focus` — option is true for one measure but not all |
| Highest value across all time periods | `data_comparison` (with `repeated_highest` sub-pattern note) | Correct option identifies a value that is highest not just at one time point but consistently | `local_maximum_trap` — option cites a locally high value that is not globally highest |
| Two-variable opposite trend | `data_trend` (with `two_variable_opposite` sub-pattern note) | Correct option identifies that two tracked variables move in opposite directions | `same_direction_assumption` — option incorrectly describes both variables moving the same way |
| Composition change over time | `data_trend` (with `composition_change` sub-pattern note) | Correct option identifies a change in relative proportions (percentages) not just absolute values | `absolute_value_confusion` — option correctly describes an absolute change but ignores the proportional shift |
| Binned distribution inference limit | `data_comparison` (with `binned_distribution` sub-pattern note) | Correct option uses only aggregate-level claims; individual-level inference is not supported by the graphic | `individual_from_aggregate` — option infers individual-level information from a distribution that only shows aggregates |

**Classification schema for all quantitative items:**

```json
{
  "quantitative_sub_pattern": "exact_value_lookup"
}
```

This field is optional for annotation of legacy items but required for
generation profiles.

Approved `quantitative_sub_pattern` values:
- `standard` (default; no sub-pattern constraint needed)
- `exact_value_lookup`
- `timing_constrained`
- `all_measures`
- `repeated_highest`
- `two_variable_opposite`
- `composition_change`
- `binned_distribution`

### 13.3 Central Ideas and Details

**Mandatory classification fields:**

```json
{
  "question_family_key": "information_and_ideas",
  "skill_family_key": "central_ideas_and_details",
  "reading_focus_key": "central_idea",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "summarize_then_compare",
  "reasoning_trap_key": "detail_trap"
}
```

**Sub-type disambiguation:**

- Stem asks "main idea" or "summarizes" → `reading_focus_key: "central_idea"`, `solver_pattern_key: "summarize_then_compare"`
- Stem asks "what is true about" or "indicates that" → `reading_focus_key: "supporting_detail"`, `solver_pattern_key: "locate_detail_directly"`, `answer_mechanism_key: "evidence_location"`
- Literary passage, stem asks about a character's feeling or attribute → `reading_focus_key: "character_or_author_detail"`, `solver_pattern_key: "locate_detail_directly"`

> When the stem uses "main purpose" phrasing and the answer choices use infinitive verb phrases
> (to argue, to describe, to compare), classify as `text_structure_and_purpose` /
> `reading_focus_key: "overall_purpose"` rather than `central_ideas_and_details`.
> The deciding signal is the infinitive-phrase format of the answer options.

### 13.4 Inferences

**Mandatory classification fields:**

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

**Evidentiary standard annotation:**

For Inferences, annotate `review.review_notes` with a one-sentence statement of what
the inference is and why it is logically required (not just consistent) with the
prior text. If the correct answer cannot be stated as logically required — only as
plausible — flag `needs_human_review: true`.

**Stem disambiguation:**

- `most_logically_completes` → standalone inference (blank at end of passage)
- `choose_text_relationship` → cross-text inference → reclassify as `cross_text_connections` / `reading_focus_key: "cross_text_inference"`

**Study design isolation limit inference pattern:**

Inference items may require identifying what a study *cannot* conclude
based on its design, not only what it can conclude. When the passage
describes a study where two conditions co-vary or where a control
comparison is absent, the logically required inference may be a
limitation: "the researchers cannot determine whether X or Y caused
the result." Annotate these items with `reading_focus_key:
"implication_inference"` and add to `review_notes`:
"inference_type: study_design_isolation_limit."

Generation note for `study_design_isolation_limit`:

```
Target: study_design_isolation_limit

Construct a passage where a study manipulates two things simultaneously
or lacks a comparison condition needed to isolate one variable. The blank
requires the student to infer that the design prevents attribution to
either variable alone.

Correct option: states that the researchers cannot determine which of
  the two co-varying factors was responsible.
Wrong options:
  - attributes the result to one factor specifically (overreach)
  - concludes no effect exists (contradiction)
  - suggests the study was flawed for unrelated reasons (outside_knowledge)
```

**Subgroup overgeneralization inference pattern:**

Inference items built on `studied_subgroup_generalization_limit`
architecture require the student to recognize that evidence from one
subgroup does not automatically support a claim about the broader
category. The correct inference either applies only to the subgroup
or explicitly notes the limitation. Annotate these items with
`reading_focus_key: "implication_inference"` and add to `review_notes`:
"inference_type: subgroup_overgeneralization_limit."

Generation note for `subgroup_overgeneralization_limit`:

```
Target: subgroup_overgeneralization_limit

Construct a passage that presents evidence about a named subgroup and
includes a warning (explicit or implicit) that the subgroup may not
represent the broader population.

Correct option: applies the conclusion only to the subgroup, or states
  that the broader conclusion cannot be drawn from the subgroup evidence.
Primary wrong trap: scope_extension — option extrapolates from the
  subgroup to the broader population without qualification.
Secondary wrong trap: overreach — option states a stronger causal
  claim than the evidence supports even within the subgroup.
```

**Mechanism-test inference annotation:**

When the passage uses the `mechanism_manipulation_test` architecture,
inference items typically require the student to identify what the
manipulation result reveals about the candidate mechanism. Annotate
these items with `reading_focus_key: "causal_inference"` and add to
`review_notes`: "inference_type: mechanism_manipulation_test — correct
answer must follow from the observed manipulation result, not from the
general topic."

### 13.5 Words in Context

**Mandatory classification fields:**

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

**Reading focus disambiguation:**

See §7.5 for the full disambiguation table and `polarity_fit` rules.

**Mandatory annotation:**

The `why_wrong` field for each distractor must explain whether the failure is:
(a) wrong denotation, (b) right denotation but wrong connotation, or (c) right denotation
and connotation but wrong register. This three-level distinction is diagnostic for generation.

For every WIC item where a negator, concessive phrase, or contrast marker
is present within the evidence span, annotate `evidence_span_text` with
the full phrase including the negator, not just the word immediately
surrounding the blank.

**Phrase-level WIC generation notes:**

WIC items may test a multi-word phrase, not only a single word. When the
correct answer is a phrase (e.g., "set out to," "made up for," "held
back"), generate all four options as phrases of comparable length and
structure so that no option is obviously wrong on length alone. Annotate
`reading_focus_key: "contextual_meaning"` (default) or `"precision_fit"`
if the distinction is between phrases of different scope or precision.
Record `evidence_span_text` with the full phrase in context, not just the
blank.

### 13.6 Text Structure and Purpose

**Mandatory classification fields:**

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

**Overall purpose annotation rule:**

Extract the action verb from the correct answer and annotate it in `review.review_notes`
as the `rhetorical_verb`. Correct answers to overall-purpose questions always use an
infinitive phrase. The first verb is the classification anchor.

Common approved rhetorical verbs:

- `to argue` — the author takes a position and defends it
- `to describe` — the author presents information without a central evaluative position
- `to explain` — the author walks through a mechanism or process
- `to compare` — the author places two subjects in explicit relation
- `to analyze` — the author examines components or causes
- `to critique` — the author identifies flaws or limitations
- `to illustrate` — the author uses an example or narrative to embody a concept
- `to trace` — the author follows a sequence or development over time
- `to challenge` — the author disputes a prior view
- `to suggest` — the author proposes tentatively without full commitment
- `to examine` — the author investigates components or evidence closely; implies careful scrutiny without a strong evaluative conclusion; more investigative than `to analyze`
- `to question` — the author raises doubts about an assumption, claim, or methodology without fully rejecting it; weaker than `to challenge`, which implies direct opposition
- `to introduce` — the author presents a concept, person, work, or field to the reader for the first time without taking a strong evaluative stance
- `to summarize` — the author condenses a larger body of evidence, argument, or work for the reader; implies fidelity to source material without addition
- `to distinguish` — the author separates two things that could be conflated or confused, making their differences explicit

Any wrong option using a verb not matching the actual rhetorical move should be annotated
with `distractor_type_key: "wrong_action_verb"`.

**Sentence function annotation rule:**

Annotate `evidence_span_text` with the underlined sentence. Annotate `review.review_notes`
with the sentence's position in the logical flow (e.g., "second sentence introduces the
counterexample that the final sentence resolves").

**Named rhetorical moves for sentence_function items:**

The following named functional roles are approved for use in
`review_notes` and generation profiles when the focus key is
`sentence_function`. Each entry shows the functional label and the
typical stem answer phrasing.

| Functional role | Typical answer phrasing |
|---|---|
| `concession` | "to acknowledge a limitation of / an objection to the preceding claim" |
| `elaboration` | "to provide additional detail supporting the preceding claim" |
| `contrast_motivation` | "to introduce a contrast that motivates the explanation that follows" |
| `parenthetical_definition` | "to clarify the meaning of a term introduced in the sentence" |
| `example` | "to provide a specific example of the general claim" |
| `consequence` | "to describe the effect or result of the preceding event or condition" |
| `hypothesis` | "to present the question or hypothesis the study is designed to test" |
| `counter_evidence` | "to present evidence that complicates or challenges the main claim" |
| `scope_qualification` | "to limit the range of the preceding claim to specific conditions" |
| `conventional_approach` | "to describe the standard or prior method that the text then challenges" |
| `obstacle` | "to describe a difficulty that the following text explains how to overcome" |
| `background_setup` | "to establish the context necessary for the main finding to be meaningful" |

**Generation rule for sentence_function items:**

When generating a `sentence_function` item, select one functional role
from the table above before writing the passage. The passage must contain
a sentence that unambiguously performs exactly that role. Record the
functional role in `generation_profile` under:

```json
{
  "target_sentence_function_role": "parenthetical_definition"
}
```

Wrong options must use incorrect functional labels from the same table or
closely related labels (e.g., offering `elaboration` when the correct
answer is `concession`). At least one wrong option must describe a plausible
but wrong action verb (e.g., "to challenge" when the sentence actually
concedes).

**Parenthetical-definition generation constraint:**

Parenthetical-definition items require a passage where a technical or
specialized term is introduced in a sentence and immediately followed by a
parenthetical phrase that defines it (enclosed in parentheses, dashes, or
commas). Wrong options describe broader passage purposes (to explain the
importance of X, to argue that X is significant) rather than the local
defining function. The correct answer must identify the clarification of a
term, not a broader rhetorical move.

### 13.7 Cross-Text Connections

**Mandatory classification fields:**

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

**Mandatory paired-passage annotation:**

For Cross-Text items, both `passage_text` (Text 1) and `paired_passage_text` (Text 2)
must be populated. Items with `paired_passage_text: null` fail validation.

**Stem disambiguation:**

| Stem wording | `reading_focus_key` | `stem_type_key` |
|---|---|---|
| "how would [Text 2 source] most likely describe / respond to…" | `text2_response_to_text1` | `choose_text_relationship` |
| "both [sources] would most likely agree with…" | `both_texts_agree` | `choose_agreement_across_texts` |
| "which best describes a difference between the claims…" | `texts_disagree` | `choose_difference_across_texts` |

**Critical rule (PrepMaven analysis confirmed on released items):**

Response stems ("how would Text 2 most likely respond to Text 1") are always
*disagreement-oriented*. The College Board does not use response stems for
agreement scenarios. A correct response-stem option will describe Text 2 as
finding Text 1's claim "problematic," "unsupported," "only conditionally valid,"
or "contradicted by evidence." Never select an option that describes Text 2
as fully endorsing Text 1 for a response-type stem.

---

## 14. Difficulty Calibration

### 14.1 Difficulty level definitions

| Level | precision_score | Characteristics |
|---|---|---|
| `low` | 3 | Correct answer is straightforward; distractors are clearly wrong on cursory reading |
| `medium` | 2–3 | One distractor is plausible; student must discriminate between two defensible options |
| `high` | 1–2 | Multiple distractors are competitive; correct answer requires discriminating fine semantic or logical distinctions |

### 14.2 Per-skill difficulty profiles

**Command of Evidence — Textual:**

| Level | Characteristics |
|---|---|
| `low` | Claim and evidence are in direct, explicit language; distractors quote unrelated claims |
| `medium` | One distractor quotes text that addresses the same topic but supports a different claim |
| `high` | Two distractors quote text that addresses the same topic; one uses text that supports a related but distinct claim; correct answer requires holding the exact wording of the claim against the exact wording of each quotation |

**Command of Evidence — Quantitative:**

| Level | Characteristics |
|---|---|
| `low` | Single-variable lookup; one bar or data point exactly matches the claim; distractors use obviously wrong values |
| `medium` | Two-variable comparison; one distractor uses a row or column adjacent to the correct one |
| `high` | Requires checking all measures or applying a timing constraint; multiple distractors are partially correct; `wrong_time_window` and `all_measures_not_checked` traps active |

**Central Ideas and Details:**

| Level | Characteristics |
|---|---|
| `low` | Main idea is stated in the first or last sentence; distractors contradict the passage |
| `medium` | Main idea must be synthesized from multiple sentences; one distractor overgeneralizes |
| `high` | "Which is true about" or literary variant; two distractors are factually true of the passage but do not answer the specific stem question; correct answer is a detail that requires cross-referencing two non-adjacent sentences |

**Inferences:**

| Level | Characteristics |
|---|---|
| `low` | Passage sets up a simple contrast or sequence; blank is clearly the logical continuation |
| `medium` | Two intermediate concepts must be connected; one wrong answer is a plausible but unsupported generalization |
| `high` | Multiple passage elements must be held simultaneously; correct inference does not overstate or understate; trap answers feel like defensible logical positions but exceed the evidence by one step |

**Words in Context:**

| Level | Characteristics |
|---|---|
| `low` | Blank adjacent to explicit context clues (contrast signal, example signal, appositive definition) |
| `medium` | Context clues distributed across multiple sentences; one trap is a plausible synonym |
| `high` | Correct word determined by subtle tonal or rhetorical signals; all four options grammatically valid and semantically close; passage register determines answer |

**Text Structure and Purpose:**

| Level | Characteristics |
|---|---|
| `low` | Single-sentence purpose obvious; clear rhetorical move; wrong answers pick irrelevant purposes |
| `medium` | Passage has two rhetorical moves; student must identify the dominant purpose |
| `high` | Purpose is to qualify or nuance another claim; requires distinguishing "to argue X is false" from "to suggest X requires additional conditions"; sentence-function questions in structurally complex passages |

**Cross-Text Connections:**

| Level | Characteristics |
|---|---|
| `low` | One text clearly supports; the other clearly contradicts; question asks for difference; reversed attribution is easy to catch |
| `medium` | Relationship is a qualification; response questions require holding the nuanced relationship |
| `high` | Both texts present complex multi-part arguments; relationship is a subtle methodological critique or expectation violation; trap answers overgeneralize or reverse direction slightly; question targets a specific claim in Text 1 |

---

## 15. Passage Architecture Requirements

### 15.1 Passage length norms (Digital SAT)

| Skill | Typical word count |
|---|---|
| Command of Evidence — Textual | 50–150 words |
| Command of Evidence — Quantitative | 40–100 words (passage only; graphic is separate) |
| Central Ideas and Details | 60–150 words |
| Inferences | 60–120 words |
| Words in Context | 30–80 words |
| Text Structure and Purpose | 50–150 words |
| Cross-Text Connections | 80–200 words total (40–100 per text) |

### 15.2 Passage structure patterns

Annotate `review.review_notes` with the structural pattern when it affects difficulty:

- `unexpected_finding` — sets up an expectation, then reveals a contrasting result
- `cautionary_framing` — describes evidence, then advocates for interpretive caution
- `problem_solution` — states a problem, then presents a response or intervention
- `compare_contrast` — two phenomena or views placed in explicit relation
- `chronological_sequence` — events or developments ordered in time
- `research_summary` — describes a study's design, findings, and implications
- `claim_evidence_explanation` — asserts a claim, provides supporting evidence, then explains the mechanism
- `analogy_driven_argument` — establishes a source domain (a known phenomenon), draws an explicit parallel to a target domain (the topic under discussion), then applies a conclusion to the target; questions test whether students track the analogical mapping and identify what the analogy implies about the target
- `multi_perspective_presentation` — presents two or more scholarly, cultural, or interpretive viewpoints without explicitly advocating for one; common in humanities texts; questions test whether students can identify the central organizing question or the author's framing role rather than one viewpoint's position
- `qualification_restatement` — presents a broad claim, qualifies it with a limiting condition or exception, then restates the refined claim; correct options capture both the claim and the qualification, not one alone

### 15.3 Experimental passage architectures (added in v2 from v1.1 §4.1)

These five architectures appear in PT4–PT11 and require specific distractor
design strategies. Annotate the architecture in `review.review_notes` as
`passage_architecture_key`.

| Architecture | Required passage elements | Typical question skills | Generation notes |
|---|---|---|---|
| `experiment_hypothesis_control_result` | (1) stated hypothesis or research question, (2) description of control vs experimental condition, (3) reported result with direction | CoE-Textual, CoE-Quant, Inferences | Distractors must include at least one option that uses a result from the wrong condition (experimental when control is needed, or vice versa) |
| `indirect_effect_mediation` | (1) factor A → factor C relationship stated, (2) additional factor B identified as mediator, (3) evidence that A → B → C rather than A → C directly | CoE-Textual, Inferences | Distractors must include at least one option that treats the mediator as an independent cause or ignores the mediation chain |
| `alternative_explanation_ruled_out` | (1) initial explanation X proposed, (2) alternative explanation Y identified, (3) test that rules Y in or out, (4) conclusion about whether X or Y survives | CoE-Textual, Inferences | Distractors must include at least one option that attributes the result to the ruled-out explanation |
| `mechanism_manipulation_test` | (1) phenomenon P described, (2) candidate mechanism M proposed, (3) manipulation that targets M specifically, (4) effect on P observed or not | CoE-Textual, Inferences | Correct answer must follow from the observed manipulation result; distractors may appeal to general topic knowledge or the broader phenomenon without engaging the mechanism |
| `studied_subgroup_generalization_limit` | (1) evidence about a named subgroup, (2) explicit or implicit warning that subgroup may not represent broader population | CoE-Textual, Inferences, Central Ideas | Distractors must include at least one option that extrapolates from the subgroup to the broader population without qualification |


---

## 16. Generation Rules

### 16.1 Mandatory generation output

When generating a reading item, specify:

```json
{
  "target_skill_family_key": "command_of_evidence_textual",
  "target_reading_focus_key": "evidence_supports_claim",
  "target_test_construct_key": "evidence_relation_precision",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
  "target_distractor_pattern": [
    "one topically related but logically disconnected option",
    "one indirect or downstream evidence option",
    "one inverted-logic option (weakens instead of supports)"
  ],
  "passage_structure_pattern": "research_summary",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "choose_best_support",
  "target_difficulty_overall": "medium"
}
```

### 16.2 Generation must include distractor design

Do not generate four random options. Each distractor must have a deliberate reason:

- A specific wrong-answer trap type (`reasoning_trap_key`)
- A plausibility source (`plausibility_source_key`)
- A clear, articulable error (`why_wrong`)

For every generated reading item, design the three distractors as:

1. one primary trap distractor targeting `target_reasoning_trap_key`
2. one surface-plausible distractor sharing topic, vocabulary, or form with the
   correct answer but failing the construct
3. one precision distractor that is almost right but fails by scope, polarity,
   attribution, or relationship degree

All three distractors must be incorrect, plausible, and mutually distinct. Do
not create filler answers that are obviously unrelated, grammatically malformed,
or implausible on first read.

### 16.3 Craft construct-specific distractor requirements

**Words in Context**

- Generate at least one distractor that fits the topic but fails the local
  semantic role (`local_semantic_role_mismatch`).
- Generate at least one distractor that is a plausible synonym in isolation but
  fails tone, register, connotation, polarity, or precision.
- If the passage includes negation, concession, or double-negative logic, include
  `polarity_context` and make `wic_polarity_logic` the construct.

**Text Structure and Purpose**

- Generate distractors that preserve passage topic overlap but misidentify
  rhetorical function, scope, or author action.
- At least one distractor should be a true detail from the passage that is not
  the requested function or main purpose (`rhetorical_scope_shift`).
- Avoid answers that can be eliminated only because they mention an unrelated
  topic; those are not competitive SAT-style distractors.

**Cross-Text Connections**

- Generate distractors that mix attribution, agreement degree, disagreement,
  qualification, method, or evidence relationships across Text 1 and Text 2.
- At least one distractor should be `attribution_blend` or
  `reversed_attribution`.
- At least one distractor should fail by relationship degree
  (`agreement_degree_mismatch` or `evidence_relationship_blend`), not by topic.

### 16.4 Distractor quality gate

Before finalizing options, verify:

- **Incorrectness:** each distractor is clearly wrong for a named reason in
  `why_wrong`; no distractor is defensibly co-correct
- **Plausibility:** each distractor maps to a common partial-reading mistake and
  has a non-null `plausibility_source_key`
- **Diversity:** no two distractors express the same wrong idea or fail through
  the same reasoning path
- **Construct alignment:** every wrong answer fails the target construct rather
  than failing because of random topic mismatch
- **Clue control:** the key is not consistently longer, more precise, more
  academic, or more grammatically polished than the distractors
- **Option homogeneity:** all options share comparable syntax, abstraction
  level, register, and semantic category
- **Separation margin:** the key must remain the single best answer, but hard
  items should have at least two distractors that survive first-pass elimination

### 16.5 Generation must match SAT style

Generated items must be:

- Concise (passage within word-count norms for the skill)
- Formally or neutrally academic in register
- Self-contained — passage provides all information needed
- Free of trivia — the question tests reasoning, not prior knowledge
- One correct answer only — the three distractors must be unambiguously wrong on the tested reasoning

**Passage prose authenticity**: In addition to the structural requirements above, every generated passage must satisfy the sentence-level style rules in §22.2, the vocabulary and register rules in §22.4, the domain-specific style signature in §22.5, and must pass the §22.7 Style Authenticity Checklist before finalizing. Passages that fail any of the ten generation failure modes listed in §22.6 must be revised before the item is submitted to the distractor design phase.

### 16.6 Generation must respect stem wording conventions

Use only the approved `stem_type_key` wording conventions from §3.2. Do not paraphrase
or invent new stem variants. SAT authenticity depends on recognizable stem patterns.

**Critical**: Words in Context generated items must use "most logical and precise word or
phrase" (blank-fill format) as the default, not "most nearly mean" (underlined format),
because the blank-fill format is the dominant contemporary variant.

### 16.7 Cross-Text Connections generation constraints

- Always generate two separate labeled passages (Text 1 and Text 2)
- Each passage must have a clear, standalone main argument
- The text relationship must be classifiable by one `text_relationship_key`
- The dominant generated relationship should be `direct_contradiction` or
  `confirmation_with_qualification` — these are the most common on released tests
- Do not generate Cross-Text items where Text 2 fully endorses Text 1 with no qualification —
  the SAT does not test simple agreement without tension

**Qualified-disagreement generation pattern** (added in v2 from v1.1 §7.1):

For `confirmation_with_qualification` items:
- Text 2 must explicitly concede one element of Text 1's claim
  (e.g., "this approach has merit in limited conditions")
- Text 2 must then qualify or restrict the claim
  (e.g., "but it cannot explain the broader pattern")
- The correct response option must capture both the concession and the
  restriction, not just one
- Wrong options include: (a) full agreement (no qualification), (b) full
  rejection (ignores the concession), (c) methodological critique (wrong
  relationship type), (d) correct concession but wrong restriction
- This item type is harder than `direct_contradiction` and should be
  calibrated at `difficulty_overall: "high"` unless the concession
  and restriction are both stated in single sentences

### 16.8 Generation profile extension fields (added in v2 from v1.1 §12)

For reading generation profiles, add these optional fields that are
mandatory when the corresponding condition applies:

```json
{
  "generation_profile": {
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "polarity_context": "negator: 'by no means'",
    "target_sentence_function_role": null,
    "quantitative_sub_pattern": null,
    "passage_architecture_key": "studied_subgroup_generalization_limit",
    "inference_type_note": "subgroup_overgeneralization_limit",
    "two_part_claim": false
  }
}
```

| Field | Mandatory when |
|---|---|
| `polarity_context` | `target_reading_focus_key` is `polarity_fit` |
| `target_sentence_function_role` | `target_reading_focus_key` is `sentence_function` |
| `quantitative_sub_pattern` | `target_skill_family_key` is `command_of_evidence_quantitative` |
| `passage_architecture_key` | passage uses one of the five experimental architectures in §15.3 |
| `inference_type_note` | passage architecture is `mechanism_manipulation_test` or `studied_subgroup_generalization_limit` |
| `two_part_claim` | `target_reading_focus_key` is `evidence_illustrates_claim` |

### 16.9 Per-focus generation and distractor recipes

Every generated reading item must bind the requested `target_reading_focus_key`
to a concrete passage shape and a concrete distractor family. Do not rely on the
broad skill family alone.

| `target_reading_focus_key` | Generated passage/stem shape | Required distractor behavior |
|---|---|---|
| `evidence_supports_claim` | Passage states a claim, hypothesis, or finding; options are possible evidence statements | One option is topically related but does not support the exact claim; one supports a related but different claim |
| `evidence_weakens_claim` | Passage states a claim; options are possible new findings | One option is neutral background; one strengthens instead of weakens |
| `evidence_illustrates_claim` | Stem asks which example best illustrates a claim, often with two required elements | One option satisfies only one element; one is a true detail with the wrong relation |
| `evidence_explains_claim` | Passage gives phenomenon; options provide possible mechanisms | One option is downstream effect rather than mechanism; one explains a different phenomenon |
| `evidence_qualifies_claim` | Passage presents broad claim needing limitation or condition | One option contradicts too strongly; one merely repeats support without qualifying |
| `data_completes_example` | Table/graph contains exact value or category needed to complete a statement | Include nearby row/column/category distractor and a real value from the wrong condition |
| `data_supports_claim` | Claim must be supported by data pattern | Include accurate data that answers the wrong claim and a wrong-group comparison |
| `data_weakens_claim` | Claim is undermined by a graph/table finding | Include data that is true but neutral and data that supports the claim |
| `data_comparison` | Correct answer depends on comparing groups, rows, columns, or intervals | Include single-measure focus, wrong group, and local-maximum traps as applicable |
| `data_trend` | Correct answer describes direction or proportional change over time/ordered values | Include direction reversal, same-direction assumption, and absolute-value confusion |
| `central_idea` | Passage organized around a single main claim | Distractors are true details, too broad summaries, or claims that omit the passage's qualifying turn |
| `supporting_detail` | Stem asks what the passage indicates or says about a specific topic | Distractors are nearby details, wrong referents, or unsupported extensions |
| `character_or_author_detail` | Literary/humanities passage asks what is true about a figure, character, or author | Distractors blend actions, motives, or attributes from adjacent sentences |
| `passage_summary` | Options summarize the passage as a whole | Distractors overemphasize one sentence, omit the central contrast, or add outside generalization |
| `author_stance` | Passage reveals attitude through evaluative language or framing | Distractors overstate, understate, reverse, or misattribute the stance |
| `expectation_violation` | Passage sets up an expected result and reports a surprising outcome | Distractors state the expected pattern, ignore the surprise, or identify the wrong variable |
| `implication_inference` | Final or mid-passage inference follows from stated evidence but is not directly stated | Distractors are plausible but not required, too broad, or contradicted by a constraint |
| `causal_inference` | Passage gives causes/effects or experimental result | Distractors reverse cause/effect, confuse mechanism with outcome, or ignore controls |
| `predictive_inference` | Passage establishes trend, condition, or mechanism; stem asks what is likely | Distractors extrapolate beyond evidence, choose wrong condition, or predict opposite trend |
| `motivational_inference` | Passage gives actions/choices that imply motive or purpose | Distractors use generic motives not anchored in text or infer too much psychology |
| `contextual_meaning` | Blank/underlined word requires local and distributed context | Distractors fit topic but fail role, connotation, precision, or sentence logic |
| `precision_fit` | Options are near-synonyms with different specificity or degree | Distractors are too broad, too narrow, too strong, or too weak |
| `connotation_fit` | Correct word must preserve evaluative charge | Distractors share denotation but wrong positive/negative/neutral charge |
| `register_fit` | Correct word/phrase must match formal or technical register | Distractors are colloquial, inflated, or from the wrong technical register |
| `underlined_word_meaning` | Stem asks what an underlined word/phrase most nearly means | Distractors include common dictionary meaning and nearby-topic meanings |
| `polarity_fit` | Passage contains negation, concession, contrast, or double-negative logic | Distractors reverse the intended polarity or ignore the negator/concessive |
| `figurative_language_meaning` | Passage uses metaphor, idiom, personification, or figurative phrase | One distractor is literal dictionary meaning; others miss the figurative function |
| `overall_purpose` | Stem asks purpose/function of the passage as a whole | Distractors describe a local paragraph, wrong rhetorical action, or too strong a claim |
| `main_purpose` | Stem asks the primary reason the author wrote the passage | Distractors are true details or secondary aims, not the central aim |
| `sentence_function` | Stem asks what a sentence/paragraph does in context | Distractors misclassify the local rhetorical move or describe content rather than function |
| `structural_pattern` | Stem asks how the passage is organized | Distractors preserve topic but use wrong organization sequence |
| `text2_response_to_text1` | Text 2 responds directly to Text 1 | Distractors miss whether Text 2 supports, challenges, qualifies, or explains Text 1 |
| `text2_contradicts_text1` | Text 2 rejects a claim, assumption, or conclusion from Text 1 | Distractors soften contradiction into qualification or broad support |
| `text2_qualifies_text1` | Text 2 partly accepts but limits Text 1 | Distractors state full agreement, full contradiction, or unrelated method difference |
| `both_texts_agree` | Both texts share a conclusion, premise, or concern | Distractors attribute agreement to only one text or overstate the degree of agreement |
| `texts_disagree` | Texts clearly differ in claim, explanation, method, or implication | Distractors choose a shared topic rather than the disagreement axis |
| `methodological_critique` | Text 2 challenges method, evidence, scope, or sample rather than conclusion alone | Distractors turn method critique into claim disagreement or simple corroboration |
| `cross_text_inference` | Correct answer follows from the relationship between both texts | Distractors use only one text, swap attribution, or simplify a nuanced relation |

**Construct binding rules:**

- `contextual_semantic_precision` → use with WIC keys where context determines
  denotation, connotation, register, polarity, or figurative role.
- `rhetorical_function_precision` → use with purpose, function, and structure
  keys; distractors must preserve topic but miss rhetorical action.
- `cross_text_relationship_precision` → use with all cross-text keys; at least
  one distractor must fail by attribution, relationship degree, or response type.
- `evidence_relation_precision` → use with textual evidence keys; each wrong
  option must name one unsupported, contradicted, indirect, or wrong-claim link.
- `inference_boundary_control` → use with inference keys; distractors must be
  plausible but not required by the text.
- `quantitative_constraint_tracking` → use with quantitative keys; distractors
  must test row/column, group, timing, all-measures, or proportion constraints.
- `figurative_interpretation_precision` → use with
  `figurative_language_meaning`; include a literal-meaning distractor.

---

## 17. Disambiguation Rules

Apply these priority rules when classification seems ambiguous.

1. `command_of_evidence_textual` vs. `inferences`: If the stem asks "which choice best
   supports the claim" and options are proposed research findings, classify as CoE-Textual.
   If the stem asks "which choice most logically completes the text" with a blank at the
   passage end, classify as Inferences.

2. `central_ideas_and_details` vs. `text_structure_and_purpose`: If answer options use
   infinitive verb phrases (to argue, to describe, to compare), classify as Text Structure
   and Purpose / `overall_purpose`. If options are factual summaries, classify as Central
   Ideas / `central_idea`.

3. `text_structure_and_purpose` (overall purpose) vs. `text_structure_and_purpose`
   (sentence function): If the stem references the text as a whole, use `overall_purpose`.
   If the stem references an underlined sentence or paragraph, use `sentence_function`.

4. `cross_text_connections` vs. `inferences` for response-type stems: If two labeled
   passages are present, always classify as `cross_text_connections` regardless of whether
   the stem uses "respond to" language. Paired passage = Cross-Text.

5. `words_in_context` vs. `central_ideas_and_details` / `supporting_detail`: The Words in
   Context question always has a blank or underlined word and asks the student to choose
   among four word or phrase options. If the options are full sentences or clauses, it is
   not a Words in Context question.

6. For Expression of Ideas questions (Transitions, Rhetorical Synthesis) that appear in
   the same domain bucket — classify using the grammar rules file's `expression_of_ideas`
   keys, not this file. Information and Ideas and Craft and Structure are the two domains
   covered here; Expression of Ideas and SEC are covered in the grammar companion file.

7. `command_of_evidence_textual` vs. `central_ideas_and_details` / `supporting_detail`:
   If the stem explicitly names a "claim," "hypothesis," "argument," or "finding" that the options must support, weaken, or illustrate → `command_of_evidence_textual`. If the stem asks what the passage "indicates," "suggests," or what is "true about" a topic without specifying a claim to match → `central_ideas_and_details` / `reading_focus_key: "supporting_detail"`. The key signal is whether the stem contains a named claim or just a topic.

Always record the resolved disambiguation in `classification.disambiguation_rule_applied`.

---

## 18. Forbidden Patterns

The validator will reject any annotation in this file's domains that includes:

- `grammar_role_key` with a non-null value
- `grammar_focus_key` with a non-null value
- `syntactic_trap_key` with a non-null value (grammar-domain field)
- `stem_type_key: "choose_best_grammar_revision"` (SEC-only stem)
- `stem_type_key: "choose_best_notes_synthesis"` (Expression of Ideas stem)
- `skill_family_key` not in the approved seven values for this file

Any annotation with these patterns should be rerouted to the grammar companion file.

---

## 19. Student Failure Mode Keys (added in v2)

These keys classify *why students select a specific wrong answer*.
They are distinct from reasoning trap keys: traps describe what the
*distractor* does wrong; failure mode keys describe what the *student*
failed to do when they selected it.

Use in `why_plausible` and `review_notes` to diagnose distractor effectiveness.

### 19.1 Words in Context failure modes

- `negation_blindness` — student applies the correct meaning of a word
  to the blank without accounting for a negator or concessive
  construction that inverts the required polarity. Also referred to
  as `polarity_blindness` (synonym).
- `connotation_surface_match` — student selects a word whose common
  dictionary meaning matches the topic but whose connotation
  (evaluative, emotional, or tonal charge) mismatches the passage's stance
- `local_role_misread` — student selects a word that belongs to the same
  semantic field but does not perform the required logical role in the sentence
- `register_tone_blindness` — student ignores whether the option's formality,
  stance, or evaluative charge matches the passage
- `figurative_meaning_blindness` — student applies the literal or dictionary meaning to a word or phrase used figuratively or idiomatically; the literal reading produces a locally coherent sentence but misses the non-literal function the passage context establishes

### 19.2 Quantitative failure modes

- `exact_value_misread` — student selects data that is numerically
  adjacent to the correct answer but off by one row, column, or bar
- `wrong_time_window` — student selects data from a time point or
  interval that is not the one specified in the claim or stem
- `individual_from_aggregate` — student infers an individual-level
  property from a graphic that reports only aggregate or binned data
- `all_measures_not_checked` — student selects a value that satisfies
  one measure but fails to verify all measures specified in the claim
- `wrong_comparison_direction` — student selects data that supports
  the opposite comparison (e.g., lowest when highest is required, or
  the smaller group when the larger is required)
- `wrong_group_selected` — student uses data from the wrong control group,
  treatment group, population, category, or comparison baseline
- `wrong_row_column_lookup` — student reads from the right table or graph but
  uses the wrong row, column, category, bar, or plotted point
- `single_measure_overread` — student chooses a value that satisfies one
  measure but does not check all measures required by the claim
- `local_maximum_overread` — student chooses a locally high value rather than
  the highest value across the full required interval or set
- `same_direction_assumption` — student assumes two variables move together
  when the data show opposite or divergent trends
- `absolute_value_overweighting` — student focuses on absolute counts or
  amounts when the correct answer depends on percentages, proportions, or
  composition
- `constraint_ignored` — student selects an answer that is accurate in
  isolation but violates a stated timing, population, measurement, or
  comparison constraint

### 19.3 Command of Evidence failure modes

- `two_part_claim_partial_match` — student selects a quotation that
  addresses one part of a two-element claim while ignoring the second
  required element
- `control_group_misidentification` — student selects evidence from the
  experimental group when the question requires evidence from the control
  group, or vice versa
- `evidence_scope_mismatch` — student selects evidence that is logically
  related to the claim but applies to a different variable, population,
  or direction than the one specified in the claim

### 19.4 Inference failure modes

- `subgroup_overgeneralization` — student draws a conclusion about the
  broader population from evidence that was explicitly restricted to a
  studied subgroup

### 19.5 Text Structure and Purpose failure modes

- `parenthetical_function_confusion` — in sentence-function items, student
  selects an option that correctly describes the broader passage purpose
  rather than the local clarifying function of a parenthetical phrase
- `rhetorical_verb_partial` — student selects an option whose content
  description is accurate but whose action verb is wrong (e.g., "to
  introduce" when the function is "to challenge")
- `scope_role_confusion` — student confuses local function with global purpose,
  or treats a supporting example as the passage's main rhetorical goal
- `author_action_overread` — student upgrades a neutral action such as
  "describe" or "explain" into a stronger action such as "criticize" or
  "advocate"

### 19.6 Cross-Text failure modes

- `attribution_swap` — student assigns a claim, method, evidence, or attitude
  from Text 1 to Text 2 or vice versa
- `agreement_degree_overread` — student treats qualified agreement, partial
  support, or methodological critique as full agreement or full contradiction
- `relationship_simplification` — student collapses a nuanced relationship
  such as "supports with a limitation" into a simpler relation such as
  "supports" or "contradicts"

### 19.7 Summary: all 29 approved failure mode keys

| # | Key | Domain |
|---|-----|--------|
| 1 | `negation_blindness` | Words in Context |
| 2 | `polarity_blindness` (synonym of #1) | Words in Context |
| 3 | `connotation_surface_match` | Words in Context |
| 4 | `local_role_misread` | Words in Context |
| 5 | `register_tone_blindness` | Words in Context |
| 5a | `figurative_meaning_blindness` | Words in Context |
| 6 | `exact_value_misread` | Quantitative CoE |
| 7 | `wrong_time_window` | Quantitative CoE |
| 8 | `individual_from_aggregate` | Quantitative CoE |
| 9 | `all_measures_not_checked` | Quantitative CoE |
| 10 | `wrong_comparison_direction` | Quantitative CoE |
| 11 | `wrong_group_selected` | Quantitative CoE |
| 12 | `wrong_row_column_lookup` | Quantitative CoE |
| 13 | `single_measure_overread` | Quantitative CoE |
| 14 | `local_maximum_overread` | Quantitative CoE |
| 15 | `same_direction_assumption` | Quantitative CoE |
| 16 | `absolute_value_overweighting` | Quantitative CoE |
| 17 | `constraint_ignored` | Quantitative CoE |
| 18 | `two_part_claim_partial_match` | CoE-Textual |
| 19 | `control_group_misidentification` | CoE-Textual |
| 20 | `evidence_scope_mismatch` | CoE-Textual |
| 21 | `subgroup_overgeneralization` | Inferences |
| 22 | `parenthetical_function_confusion` | Text Structure and Purpose |
| 23 | `rhetorical_verb_partial` | Text Structure and Purpose |
| 24 | `scope_role_confusion` | Text Structure and Purpose |
| 25 | `author_action_overread` | Text Structure and Purpose |
| 26 | `attribution_swap` | Cross-Text Connections |
| 27 | `agreement_degree_overread` | Cross-Text Connections |
| 28 | `relationship_simplification` | Cross-Text Connections |

---

## 20. Amendment Process

If the agent encounters a question that does not fit existing keys:

```json
{
  "amendment_proposal": {
    "proposed_key": "...",
    "proposed_parent_skill_key": "...",
    "reason": "...",
    "evidence_text": "...",
    "status": "proposed",
    "frequency_estimate": "very_low | low | medium | high | very_high",
    "example_count": 0,
    "examples": ["..."]
  }
}
```

Do not use the proposed key in production output until it is promoted to `approved`.

---

## 21. Validator Checklist

Before finalizing any annotation for an `information_and_ideas` or `craft_and_structure`
question, confirm:

- [ ] `question_family_key` is one of: `information_and_ideas`, `craft_and_structure`
- [ ] `skill_family_key` is one of the seven approved keys
- [ ] `reading_focus_key` is from the approved list for the selected `skill_family_key`
- [ ] `grammar_role_key` is `null` or omitted
- [ ] `grammar_focus_key` is `null` or omitted
- [ ] `stem_type_key` matches the actual stem wording convention
- [ ] `stimulus_mode_key` is appropriate for the skill (e.g., `prose_paired` for Cross-Text)
- [ ] `paired_passage_text` is populated for Cross-Text items
- [ ] `table_data` or `graph_data` is populated for Quantitative CoE items
- [ ] Every option has `distractor_type_key`, `why_plausible`, and `why_wrong`
- [ ] Exactly one option has `is_correct: true` and `distractor_type_key: "correct"`
- [ ] `precision_score: 3` is assigned only to the correct option
- [ ] `evidence_span_text` identifies the passage span anchoring the correct answer
- [ ] `annotation_confidence` is populated in `review`
- [ ] `target_test_construct_key` is populated for generated reading-domain items
- [ ] `target_craft_subconstruct_key` is populated for generated Craft and Structure items
- [ ] No distractor is defensibly co-correct with the key
- [ ] The three distractors fail through distinct `reasoning_trap_key` or
      `distractor_type_key` values
- [ ] The correct answer is not exposed by length, register, option shape,
      grammatical polish, or repeated wording from the stem
- [ ] All four options are homogeneous in syntax, abstraction level, register,
      and semantic category

### 21.1 Additional validator checks (added in v2 from v1.1 §11)

- [ ] For WIC items with a negator or concessive in the passage,
      `reading_focus_key` is `polarity_fit` and `evidence_span_text`
      includes the full negated construction
- [ ] For `evidence_illustrates_claim` items where the stem claim has
      two required elements, at least one distractor is annotated with
      `distractor_type_key: "partial_match"` and `why_wrong` names both
      elements
- [ ] For `sentence_function` items, `review_notes` includes the
      `target_sentence_function_role` from the approved list in §13.6
- [ ] For quantitative items using a constrained lookup, the
      `quantitative_sub_pattern` field is populated with the appropriate
      sub-pattern value
- [ ] For quantitative items where `quantitative_sub_pattern` is
      `timing_constrained`, at least one distractor is annotated with
      `distractor_type_key` corresponding to `wrong_time_window`
- [ ] For quantitative items where a claim names a group, baseline, treatment,
      or condition, at least one distractor tests `wrong_group_comparison`
- [ ] For quantitative items where all measures or the full interval must be
      checked, no option is accepted based on a single local value, local
      maximum, or single measure
- [ ] For quantitative items involving percentages or composition, distractors
      distinguish absolute-value changes from proportional changes
- [ ] For quantitative items where `quantitative_sub_pattern` is
      `binned_distribution`, no distractor or correct option infers
      individual-level information from the aggregate graphic
- [ ] For inference items on `studied_subgroup_generalization_limit`
      architecture, `review_notes` includes
      "inference_type: subgroup_overgeneralization_limit"
- [ ] For inference items on `mechanism_manipulation_test` architecture,
      `review_notes` includes
      "inference_type: mechanism_manipulation_test"
- [ ] For items on `experiment_hypothesis_control_result` architecture,
      the correct option addresses the specific group (experimental or
      control) named in the claim, not the general topic
- [ ] For Words in Context items, at least one distractor fails by local
      semantic role, tone/register, connotation, or polarity rather than by
      unrelated meaning
- [ ] For Text Structure and Purpose items, at least one distractor preserves
      topic overlap but fails by rhetorical scope, sentence function, or author
      action
- [ ] For Cross-Text items, at least one distractor fails by attribution,
      agreement degree, evidence relationship, or response-to-claim precision
- [ ] For WIC items where `reading_focus_key` is `figurative_language_meaning`, `target_test_construct_key` is `figurative_interpretation_precision`, at least one distractor uses the literal dictionary meaning of the target word, and `review_notes` identifies the figurative function (metaphor, idiom, or personification)

---

## 22. Passage Style Fingerprint and Generation Realism (added in v3)

This section governs prose style for all generated passages. Satisfaction of §16.5 structural requirements is necessary but not sufficient — passages must also satisfy the style authenticity rules here. The §22.7 checklist is a mandatory generation gate.

**Relationship to the grammar companion file**: Sentence-level grammar correctness is governed by `rules_agent_dsat_grammar_ingestion_generation_v8.md`. This section governs register, rhetorical texture, and stylistic authenticity. The two documents are complementary and both apply to generated passages.

### 22.1 Why passage style realism matters

DSAT passages are drawn from published academic, scholarly, and literary sources. Authentically styled passages produce more discriminating questions because:

- Students recognize authentic academic register and are not distracted by stylistic anomalies
- WIC items require precise register sensitivity — an off-register passage undermines that construct
- Text Structure and Purpose items require clear rhetorical texture — monotone passages make these items ambiguous
- Passages that do not sound like real sources fail the "free of trivia, tests reasoning" gate (§16.5)

Common failure patterns in generated passages: monotone sentence length, absence of epistemic hedging in science contexts, anonymous authority ("scientists have found"), missing appositives for technical terms, and colloquial register bleed. See §22.6 for the full failure mode catalog.

### 22.2 Sentence-level style rules

The following eight rules apply to every generated passage unless domain exceptions are noted.

**Rule S1 — Mixed sentence length**

Target sentence-length variation across every passage. Authentic DSAT passages mix short declarative sentences (8–15 words) with longer complex sentences (25–45 words). Never generate more than two consecutive sentences within 5 words of each other in length.

Enforcement: If all sentences are 20–25 words, revise by splitting the longest into two — a short declarative followed by the elaborating clause — or by combining the two shortest with a subordinating conjunction.

**Rule S2 — Subordinate clause density**

Target 1–2 subordinate clauses per 100 words. Zero subordinate clauses produces an oversimplified passage ("Dick and Jane" register). Three or more per 100 words produces a passage that fails the word-count norms for shorter skill types and is harder to read without adding useful complexity.

Approved subordination types for DSAT style: relative clauses (`which`, `that`, `who`, `whose`), adverbial clauses (`although`, `because`, `when`, `while`, `since`, `even though`), nominal clauses (`that X is the case`), and absolute phrases (see grammar v8 §B.3 `absolute_phrase`).

**Rule S3 — Epistemic hedging**

Mandatory for science, social science, and economics passages. Use `may`, `might`, `appears to`, `suggests`, `indicates`, `tends to`, `has been proposed`, `is thought to`, `remains unclear whether`. Reserve unhedged claims for established scientific consensus (e.g., "water is composed of hydrogen and oxygen") or reported findings with explicit attribution.

Forbidden in science passages: unqualified causal claims ("X causes Y") without attribution or qualification. Authentic DSAT passages say "X may cause Y," "X has been associated with Y," or "researchers found that X led to Y in [specific condition]."

Literary and historical passages: hedging density is lower. Authors may state interpretive claims with more confidence because they are offering an argument rather than reporting empirical evidence. Use qualifiers like "arguably," "in [author]'s view," "suggests that," or "can be read as" to preserve appropriate epistemic caution.

**Rule S4 — Named attribution**

Most authentic DSAT passages attribute findings, arguments, or observations to a named source. Acceptable attribution forms:
- Named researcher + institution: "Hernandez and colleagues at MIT"
- Named researcher only: "Smith found that"
- Named study or publication: "a 2019 study published in *Nature*"
- Named historical figure: "Jefferson argued that"
- Named institution: "researchers at the University of Chicago"

Weak attribution ("scientists," "experts," "researchers") is acceptable only as a secondary reference after the named source is established. Do not open a passage with anonymous authority.

**Rule S5 — Appositives and parenthetical clarification**

Include 1–2 appositives per passage. An appositive introduces or defines a technical term, proper noun, or specialized concept in a natural, self-contained way — matching the style of passages from published sources that assume readers may be unfamiliar with the term.

Form: `[technical term], [appositive definition],` (commas; see grammar v8 §B.3 `appositive_nonrestrictive`)

Examples:
- "The anterior cingulate cortex, a region involved in conflict monitoring, showed elevated activation."
- "Symbiosis, the long-term interaction between organisms of different species, takes several forms."
- "Ngũgĩ wa Thiong'o, the Kenyan novelist and theorist, has argued that..."

Do not use parentheses for appositives in generated DSAT passages — commas or em dashes are the attested forms.

**Rule S6 — Nominalization (measured use)**

DSAT academic passages use nominalized forms of verbs and adjectives: "the investigation" (← investigate), "the assessment" (← assess), "the observation" (← observe), "the emergence" (← emerge), "the predominance" (← predominate). Nominalization elevates register and is expected in scholarly prose.

Avoid weak nominalization that adds length without register value: "the making of" instead of "creation," "the doing of" instead of "performance." Two to four nominalizations per 100 words is the target range.

**Rule S7 — Active vs. passive voice balance**

Science passages about studies legitimately use passive voice for methods: "participants were randomly assigned," "samples were analyzed," "data were collected." Passive is also appropriate for outcomes where the agent is less important than the result: "the mechanism was identified," "the effect was observed."

Do not normalize every passive to active in science passages — that produces an unnaturally journalistic register. Aim for roughly 20–35% passive sentences in research passages; 5–15% in literary and historical passages.

**Rule S8 — Internal punctuation variety**

Authentic passages use em dashes and colons for inline elaboration and definition. Use one em dash pair or one colon per passage for definitional or illustrative elaboration. Zero is acceptable; two or more is unusual and may signal over-reliance on a single device.

Semicolons connect two closely related independent clauses. One to two semicolons per 150-word passage is authentic; zero is common in shorter passages.

Do not use parentheses as a substitute for comma-appositive style. Parentheses in DSAT passages are rare and typically enclose a date, citation, or quantitative value.

### 22.3 Passage-level texture

**Opening strategies**

Three patterns appear most frequently in authentic DSAT passages:

1. **Research-finding lead**: Opens with a specific study, year, and finding.
   > "In a 2019 study of migratory songbirds, researchers at the Cornell Lab of Ornithology found that..."

2. **Definitional or contextual lead**: Opens by situating a concept in its field.
   > "The concept of *embodied cognition*, first articulated by Merleau-Ponty in the mid-twentieth century, holds that..."

3. **Counterintuitive or tension lead**: Opens with the expected view, then signals a reversal.
   > "Despite widespread belief that increased competition drives innovation, economists have found..."

Do not open with a question ("What happens when...?") — this pattern does not appear in released DSAT passages. Do not open with a journalistic assertion ("Today, scientists know that...") without a year or specific attribution.

**Claim-support-explain arc**

For passages of three or more sentences, follow the attested structure:
1. State the claim, finding, or observation (often with attribution)
2. Provide specific evidence: a quoted result, a named example, a data point
3. Explain the mechanism, implication, or qualification

Avoid reversing this order. Starting with mechanism ("Because X, researchers found Y") is inauthentic for most DSAT domains.

**Closing strategies**

Authentic DSAT passages close with one of:
- An implication or significance statement ("This finding suggests that...")
- A qualification or limitation ("The results, however, apply only to...")
- An open question ("Whether this pattern extends to... remains to be determined")
- A broadened perspective ("These observations align with a growing body of evidence suggesting...")

Do not close with a simple restatement of the opening claim. Do not close with a prescription or recommendation ("Policymakers should therefore...") unless the passage's domain and purpose call for it.

### 22.4 Vocabulary and register

**Tier 2 academic vocabulary (mandatory)**

Target 2–4 Tier 2 words per 100 words. Tier 2 words are general academic vocabulary used across disciplines: `phenomenon`, `attribute`, `demonstrate`, `consequently`, `predominantly`, `comprise`, `vary`, `fundamental`, `significant`, `elaborate`, `interpret`, `constitute`, `generate`, `contribute`, `contrast`, `emerge`, `correspond`, `distinguish`.

Do not substitute simple words when Tier 2 equivalents are natural to the domain:
- Use "demonstrate" not "show"
- Use "indicate" not "point to"
- Use "constitute" not "make up"
- Use "consequently" not "so"

**Tier 3 domain vocabulary (contextually required)**

Include 1–3 domain-specific technical terms in each passage. Define at least one via appositive (Rule S5). Do not over-explain: a term already defined should not receive a second parenthetical explanation. For the WIC skill specifically, the tested word should be a Tier 2 or Tier 3 item used in a non-obvious sense, not a general vocabulary word with no domain constraint.

**Forbidden register markers**

The following are unconditionally prohibited in generated DSAT passages outside of literary direct quotation:

| Forbidden pattern | Examples | Correct alternative |
|---|---|---|
| Contractions | don't, can't, it's, they're | do not, cannot, it is, they are |
| Informal intensifiers | very, really, a lot, super | substantially, considerably, significantly, markedly |
| Colloquial hedges | kind of, sort of, I think, I guess | to some degree, may, arguably |
| Generic openers | Today, Recently, Nowadays | In [year], As of [date], In the past decade |
| First-person opinion | I believe, we can see | the evidence suggests, the passage indicates |
| Exclamation | Remarkable! This is surprising! | (use epistemic hedging instead) |

**Exception**: Literary passages that include first-person narration or direct quotation from a source may contain contractions or informal language if they appear within quotation marks or italicized narrative voice that is clearly distinct from the author's analytical voice.

### 22.5 Domain-specific style signatures

Each `topic_broad_key` domain has a characteristic style profile. When generating a passage, select the domain first, then apply the corresponding style signature. Mismatches between domain and style are the most common authenticity failures.

| Domain | Register | Hedging density | Attribution form | Typical architectures |
|---|---|---|---|---|
| `science` | Formal, technical | High — every empirical claim hedged | Named researcher + institution, or "a [year] study" | `research_summary`, `experiment_hypothesis_control_result`, `mechanism_manipulation_test`, `indirect_effect_mediation` |
| `social_studies` | Academic, interpretive | Medium-high — findings hedged, theoretical claims less so | Named scholar + discipline; reference to "scholars" after establishment | `claim_evidence_explanation`, `studied_subgroup_generalization_limit`, `compare_contrast`, `multi_perspective_presentation` |
| `history` / `humanities` | Scholarly narrative, interpretive | Low-medium — interpretive claims marked as argued/proposed; historical facts unhedged | Named figures, dates, events; named historians for contested claims | `chronological_sequence`, `history_claim_evidence_limitation`, `history_assumption_revision`, `multi_perspective_presentation` |
| `literature` / `arts` | Narrative-descriptive, analytical | Low (diegetic certainty in narration); interpretive hedging in analysis | Named author + work title; named character | `literature_observation_interpretation_shift`, `literature_character_conflict_reveal` |
| `economics` | Formal, argumentative | Medium — theoretical models stated with confidence; empirical applications hedged | Named theory, named economist, or "economic models suggest" | `economics_theory_exception_example`, `economics_problem_solution_tradeoff`, `claim_evidence_explanation` |
| `environment` | Formal to journalistic | High — projections and risk claims hedged | Named study, named dataset, or governmental body | `research_summary`, `cautionary_framing`, `unexpected_finding` |
| `technology` | Formal to semi-technical | Medium | Named researchers, companies, or publications | `research_summary`, `problem_solution`, `claim_evidence_explanation` |

**Natural science style notes**: Science passages frequently describe experimental design, controls, and results. The passive voice is expected for methodology ("participants were randomly assigned," "samples were processed"). Organism names follow standard conventions: genus and species italicized (*Apis mellifera*), common names not italicized.

**Social science style notes**: Social science passages often present a theoretical claim, then immediately introduce complicating evidence or a rival account. Signal phrases like "however," "yet," "subsequent work by [name] complicated this picture" are characteristic of the `multi_perspective_presentation` and `compare_contrast` architectures.

**Literary/humanities style notes**: Literary passages may include quoted or paraphrased direct speech from the work under discussion. Analytical sentences use literary present tense ("Gay describes," "Hemingway writes," "the narrator reflects"). Historical context may be given in past tense; analysis in present. Interpretive claims are often introduced with "arguably," "in [author]'s view," or "can be read as."

**Historical passage style notes**: Historical claims about events are stated in past tense without hedging ("The Treaty of Westphalia established...") unless the claim is contested, in which case it is attributed ("Gross argued that..."). Contested historical interpretations are a common `multi_perspective_presentation` architecture signal.

### 22.6 Generation failure modes (passage level)

These ten failure patterns cause generated passages to fail authenticity review. Each entry names the failure, its diagnostic signal, and the fix.

**FAILURE-01 — Monotone sentence length**
- Signal: All sentences within 5 words of each other in length
- Fix: Split the longest sentence at a natural clause boundary into one short declarative and one elaborating clause. Or combine the two shortest with a subordinating conjunction.

**FAILURE-02 — Certainty overclaim**
- Signal: Unhedged causal or empirical assertions in a science or social science passage ("X causes Y," "X leads to Z")
- Fix: Add epistemic qualifier ("X may cause Y," "X has been associated with Z," "researchers found that X led to Y under these specific conditions")

**FAILURE-03 — Anonymous authority**
- Signal: Passage opens with or relies on "scientists have found," "experts believe," "researchers discovered" without naming any researcher, institution, study, or date
- Fix: Name a researcher, institution, or publication ("researchers at [institution] found," "a 2021 study in [journal] reported")

**FAILURE-04 — Absent appositives**
- Signal: A technical term, proper noun, or discipline-specific concept appears in the passage with no parenthetical clarification
- Fix: Add one comma-delimited appositive after the first occurrence of the term ("the hippocampus, a brain region critical for memory formation,")

**FAILURE-05 — Colloquial register bleed**
- Signal: Contraction, informal intensifier, colloquial hedge, or first-person opinion voice in an academic passage
- Fix: Substitute formal equivalents (see §22.4 Forbidden Register Markers table)

**FAILURE-06 — Underdense academic vocabulary**
- Signal: Passage contains no Tier 2 academic vocabulary beyond basic connectives and common nouns; reads at middle-school prose level
- Fix: Introduce 2–3 Tier 2 words appropriate to the domain. Do not introduce vocabulary that conflicts with the passage's register or is unfamiliar to a 10th–12th grader.

**FAILURE-07 — Passive-voice overcorrection**
- Signal: Every sentence is in active voice in a science passage describing a controlled study, experiment, or data collection procedure
- Fix: Allow legitimate passive for methods ("participants were assigned," "samples were analyzed") and outcome reporting ("the effect was observed in...")

**FAILURE-08 — Opening with the blank**
- Signal: For WIC or Inferences items, the blank appears in the first sentence with no prior context to establish the passage's domain, topic, or rhetorical situation
- Fix: Add one sentence of context before the sentence containing the blank

**FAILURE-09 — Collapsed concession**
- Signal: In a `cautionary_framing`, `qualification_restatement`, or `compare_contrast` passage, the concessive or qualifying turn is so strong that the original main claim effectively collapses
- Fix: Ensure the qualification is genuinely limited in scope. The main claim must survive the qualification. If the original claim does not survive, redesign the passage architecture.

**FAILURE-10 — Missing implication**
- Signal: A `research_summary` or `experiment_hypothesis_control_result` passage ends at the finding with no statement of implication, significance, or limitation
- Fix: Add one closing sentence stating the implication ("This finding suggests that..."), a limitation ("The results, however, are limited to..."), or an open question ("Whether this pattern holds in naturalistic settings remains to be determined")

### 22.7 Style authenticity checklist (generation gate)

This checklist is a mandatory gate for all generated passages. A passage may not advance to distractor design until all applicable checks pass.

**Sentence-level (§22.2)**
- [ ] Sentence lengths vary: at least one sentence ≤15 words and one sentence ≥25 words
- [ ] Subordinate clause density: 1–2 subordinate clauses per 100 words
- [ ] Epistemic hedging present in all empirical claims (science, social science, economics domains)
- [ ] At least one named attribution: named researcher, institution, figure, study, or publication
- [ ] At least one appositive or parenthetical clarification for a technical or domain-specific term
- [ ] Nominalization present: ≥2 nominalized forms per 100 words
- [ ] Active/passive balance appropriate to domain (science passages: 20–35% passive; literary: ≤15%)
- [ ] Internal punctuation variety: at least one colon, em dash, or semicolon for passages >80 words

**Vocabulary and register (§22.4)**
- [ ] No contractions outside literary direct quotation
- [ ] No informal intensifiers (very, really, a lot) or colloquial hedges
- [ ] Tier 2 academic vocabulary density: ≥2 items per 100 words
- [ ] At least one Tier 3 domain-specific term with appositive clarification

**Passage-level (§22.3)**
- [ ] Opening strategy matches domain signature (§22.5): research-finding lead, definitional lead, or counterintuitive lead
- [ ] Claim-support-explain arc maintained for passages ≥3 sentences
- [ ] Closing strategy is implication, qualification, or open question — not a restatement

**Failure-mode check (§22.6)**
- [ ] FAILURE-01 (monotone length) — not present
- [ ] FAILURE-02 (certainty overclaim) — not present
- [ ] FAILURE-03 (anonymous authority) — not present
- [ ] FAILURE-04 (absent appositives) — not present
- [ ] FAILURE-05 (colloquial register bleed) — not present
- [ ] FAILURE-06 (underdense vocabulary) — not present
- [ ] FAILURE-07 (passive overcorrection) — not present
- [ ] FAILURE-08 (opening with the blank) — not present
- [ ] FAILURE-09 (collapsed concession) — not present
- [ ] FAILURE-10 (missing implication) — not present

### 22.8 Few-shot style exemplars

These exemplars demonstrate the target prose style for four domain types. Use them as reference when generating or evaluating passage authenticity. Each exemplar is annotated with its domain signature, architecture, and active style rules.

---

**Exemplar A — Natural science, `research_summary`, ~95 words**

> In a 2021 study examining the behavior of *Apis mellifera*, the common honeybee, researchers at the University of Toulouse found that foraging patterns shifted significantly in response to ambient temperature fluctuations exceeding 4°C. Bees exposed to such conditions allocated a greater proportion of their foraging time to shorter, more frequent trips rather than extended searches. The researchers suggested that this behavioral adjustment may function as a thermoregulatory strategy, reducing the metabolic cost of extended flight during periods of thermal stress. Whether this flexibility is heritable or exclusively environmentally induced remains an open question.

*Active rules: S1 (mixed length), S3 (hedging: "may function," "remains an open question"), S4 (named attribution: researchers at Toulouse), S5 (appositive: "the common honeybee"), S7 (no over-normalization of passive). Domain: science. Architecture: research_summary. Tier 2 vocab: "allocated," "proportion," "exclusively," "induced."*

---

**Exemplar B — Social science, `claim_evidence_explanation`, ~85 words**

> Linguistic accommodation—the tendency of speakers to adjust their speech patterns to match those of their interlocutors—has been documented across a wide range of social contexts. Giles and colleagues observed that individuals in lower-status positions converged more rapidly toward the speech patterns of higher-status speakers, while the reverse rarely occurred. This asymmetry, the researchers argued, reflects broader social hierarchies rather than strictly communicative efficiency. Subsequent studies have complicated this picture, noting that convergence rates also depend on the perceived identity salience of the interaction.

*Active rules: S1 (varied length), S3 (hedging: "has been documented," "have complicated"), S4 (named attribution: "Giles and colleagues"), S5 (em-dash appositive: "the tendency of..."), S8 (em dash internal punctuation). Domain: social_studies. Architecture: claim_evidence_explanation. Tier 2 vocab: "documented," "converged," "asymmetry," "reflect," "perceived."*

---

**Exemplar C — Historical/humanities, `multi_perspective_presentation`, ~75 words**

> Historians have long debated the extent to which the Treaty of Westphalia, signed in 1648, established the modern system of state sovereignty. Scholars such as Leo Gross characterized it as a foundational moment in international law, while critics like Andreas Osiander argued that the treaty's actual provisions were far more limited in scope than subsequent interpretation suggests. The debate reflects broader disagreements about whether legal concepts emerge from deliberate design or from retrospective narrativization.

*Active rules: S1 (varied length), S2 (relative clauses: "which the Treaty...established," "that the treaty's..."), S4 (named figures: Gross, Osiander), S5 (appositive: "signed in 1648"), S6 (nominalization: "interpretation," "narrativization," "disagreements"). Domain: history. Architecture: multi_perspective_presentation. Tier 2 vocab: "characterized," "subsequent," "interpretation," "emerge," "reflect."*

---

**Exemplar D — Literary/arts, `literature_observation_interpretation_shift`, ~65 words**

> In her memoir *Hunger*, Roxane Gay describes her relationship with her body not as a site of failure but as a form of protection—a fortress built in response to trauma. Gay's framing inverts common narratives of weight loss as reclamation, positioning the body's expansion as a response to pain rather than an abdication of self-control. The memoir challenges readers to reconsider the moral language typically applied to size.

*Active rules: S1 (varied length), S3 (interpretive hedging: "as a form of protection" frames the claim as Gay's interpretation), S4 (named author: Roxane Gay, named work: Hunger), S5 (em-dash appositive: "a fortress built in response..."), literary present tense throughout. Domain: literature. Architecture: literature_observation_interpretation_shift. Tier 2 vocab: "inverts," "positioning," "abdication," "reconsider."*

---

**Cross-domain register contrast (diagnostic)**

The following two passages cover the same topic at different registers. Use to calibrate register-checking:

*Authentic DSAT register:*
> A 2018 study conducted by Huang and colleagues at Stanford University found that undergraduate students who maintained consistent sleep schedules — defined as less than one hour of variation in sleep onset time across seven consecutive nights — demonstrated significantly higher academic performance than those with irregular schedules. The researchers proposed that circadian stability may support more effective consolidation of declarative memory during sleep.

*Inauthentic generated register (do not produce):*
> Scientists have found that students who sleep at the same time every night do a lot better in school. This is really interesting because it shows that sleep is very important. We can see that good sleep habits help students remember things better.

Failures in the inauthentic version: FAILURE-03 (anonymous authority), FAILURE-05 (colloquial register: "do a lot better," "This is really interesting," "very important," "We can see"), FAILURE-06 (no Tier 2 vocabulary), FAILURE-02 (certainty overclaim: "help students remember" stated without hedging), FAILURE-01 (monotone sentence length).

---

## 23. Generation Protocol (added in v3)

This section provides the step-by-step order of operations for generating a complete DSAT reading item from a blank slate. The five phases must be executed in order. Do not write passage prose before completing Phase 1, and do not design distractors before completing Phase 3.

**Relationship to other sections**: This protocol stitches together existing sections. It does not add new rules — it sequences them. Phase 2 delegates to §22. Phase 4 delegates to §16. Phase 5 delegates to §21 and §22.7.

---

### 23.1 Protocol overview

| Phase | Name | Delegates to |
|---|---|---|
| 1 | Profile selection | §23.2 — pick domain, skill, focus, architecture, difficulty, trap |
| 2 | Passage composition | §23.3 → §22, §15 |
| 3 | Stem construction | §23.4 → §3.2 |
| 4 | Option design | §23.5 → §16.2–16.4, §16.9 |
| 5 | Validation | §23.6 → §22.7, §21 |

Lock each phase before moving to the next. If a later phase reveals a problem with an earlier choice (e.g., the passage cannot support the intended distractor architecture), return to the earliest affected phase rather than patching the later one.

---

### 23.2 Phase 1 — Profile selection

Produce a completed `generation_profile` JSON before writing a single word of passage prose. All downstream decisions follow from this profile.

**Step 1a — Select `topic_broad_key`**

Choose from the seven approved domains: `science`, `social_studies`, `history`, `literature`, `economics`, `environment`, `technology`. Let skill family guide domain selection:

- `command_of_evidence_quantitative` → prefer `science`, `social_studies`, `economics` (these domains naturally produce graphable data)
- `cross_text_connections` → prefer `science`, `social_studies`, `history`, `literature` (two-text comparison is common in these domains)
- `words_in_context` → all domains equally; prefer domains with strong Tier 2–3 vocabulary contrast
- `inferences` → prefer `science`, `social_studies` (strongest evidence chains)
- `text_structure_and_purpose` → all domains; `history` and `literature` are especially strong for `sentence_function` items

**Step 1b — Select `skill_family_key`**

If not externally constrained, use the DSAT frequency distribution as a guide for realistic item pools:

| Skill family | Approx. share of a reading module | Priority for pool balance |
|---|---|---|
| `command_of_evidence_textual` | ~18% | High — generate frequently |
| `words_in_context` | ~16% | High |
| `text_structure_and_purpose` | ~16% | High |
| `central_ideas_and_details` | ~13% | Medium |
| `inferences` | ~10% | Medium |
| `command_of_evidence_quantitative` | ~9% | Medium |
| `cross_text_connections` | ~7% | Low — complex; generate deliberately |

**Step 1c — Select `reading_focus_key`**

Use the per-skill-family focus key lists in §7 and Appendix V `READING_FOCUS_BY_SKILL_FAMILY`. For each skill family, prefer the higher-frequency focus keys unless targeting a specific gap:

| Skill family | Primary focus keys | Secondary (gap-filling) focus keys |
|---|---|---|
| `command_of_evidence_textual` | `evidence_supports_claim`, `evidence_illustrates_claim` | `evidence_weakens_claim`, `evidence_explains_claim`, `evidence_qualifies_claim` |
| `command_of_evidence_quantitative` | `data_supports_claim`, `data_comparison` | `data_completes_example`, `data_weakens_claim`, `data_trend` |
| `central_ideas_and_details` | `central_idea`, `supporting_detail` | `passage_summary`, `character_or_author_detail`, `author_stance` |
| `inferences` | `causal_inference`, `implication_inference` | `motivational_inference`, `predictive_inference` |
| `words_in_context` | `contextual_meaning`, `precision_fit` | `polarity_fit`, `connotation_fit`, `figurative_language_meaning`, `register_fit` |
| `text_structure_and_purpose` | `overall_purpose`, `sentence_function` | `structural_pattern`, `author_stance` |
| `cross_text_connections` | `text2_response_to_text1`, `texts_disagree` | `both_texts_agree`, `text2_qualifies_text1`, `methodological_critique` |

**Step 1d — Select `passage_architecture_key`**

Choose an architecture from §15.2 or §15.3 that is compatible with the selected skill and focus key. Incompatible pairings:

- `most_logically_completes` stem (Inferences) → requires passage with a logical gap at the end; `research_summary` and `claim_evidence_explanation` are the most compatible architectures
- `choose_sentence_function` stem (Text Structure) → requires a passage with a sentence that performs a distinct, nameable rhetorical role; `claim_evidence_explanation`, `compare_contrast`, and `qualification_restatement` work well
- `command_of_evidence_textual` → any architecture works; `experiment_hypothesis_control_result` and `indirect_effect_mediation` produce stronger discriminating distractors
- `command_of_evidence_quantitative` → passage architecture is constrained by what the graphic supports; generate the graphic description first

**Step 1e — Select `difficulty_overall`**

See §14 for per-skill difficulty profiles. When generating for pool balance, target 40% `low`, 40% `medium`, 20% `high`.

**Step 1f — Select `reasoning_trap_key` and `target_distractor_pattern`**

Select the primary trap from the skill-compatible traps in §10 and the per-focus distractor recipe in §16.9. Record the trap before writing the passage — the passage should be drafted so that the primary trap is available (e.g., a `topical_relevance_without_logical_connection` distractor requires the passage to contain topically related content that does NOT support the claim).

**Completed profile template:**

```json
{
  "generation_profile": {
    "topic_broad_key": "science",
    "topic_fine": "neuroscience",
    "target_skill_family_key": "inferences",
    "target_reading_focus_key": "causal_inference",
    "target_test_construct_key": "inference_boundary_control",
    "target_craft_subconstruct_key": null,
    "target_reasoning_trap_key": "overreach",
    "passage_structure_pattern": "research_summary",
    "passage_architecture_key": "experiment_hypothesis_control_result",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "most_logically_completes",
    "target_difficulty_overall": "medium",
    "target_distractor_pattern": [
      "one overreach distractor — extends beyond what the evidence supports",
      "one reversal distractor — applies the finding to the wrong condition",
      "one outside_knowledge distractor — appeals to general topic knowledge not grounded in the passage"
    ],
    "polarity_context": null,
    "target_sentence_function_role": null,
    "quantitative_sub_pattern": null,
    "inference_type_note": null,
    "two_part_claim": false
  }
}
```

---

### 23.3 Phase 2 — Passage composition

With the generation profile locked, compose the passage in three steps.

**Step 2a — Apply the domain style signature (§22.5)**

Select the style profile for the chosen `topic_broad_key`. Note the expected hedging density, attribution form, and register before writing the first sentence.

**Step 2b — Apply the passage architecture (§15.2, §15.3)**

Draft the passage so it instantiates the selected `passage_architecture_key`. For experimental architectures (§15.3), ensure all required passage elements are present (e.g., `experiment_hypothesis_control_result` requires a stated hypothesis, a described control vs. experimental condition, and a reported result with direction).

**Step 2c — Apply sentence-level style rules (§22.2)**

During drafting, actively enforce Rules S1–S8. Do not apply them as a post-hoc patch — build them in from the first sentence.

Priority ordering for short passages (<80 words):
1. Named attribution (S4) — always required
2. Epistemic hedging (S3) — required for science/social science
3. Mixed sentence length (S1) — required
4. At least one appositive (S5) — required

**Step 2d — Check against §22.7 before proceeding**

Run the §22.7 Style Authenticity Checklist now. Do not proceed to Phase 3 with a passage that fails any applicable check.

**Step 2e — Verify the passage supports the intended distractor architecture**

Confirm the passage contains the elements needed for the primary trap distractor selected in Phase 1. If it does not, revise the passage — do not change the target trap to match the passage.

---

### 23.4 Phase 3 — Stem construction

**Step 3a — Select canonical stem wording from §3.2**

Use the `stem_type_key` selected in Phase 1 to retrieve the canonical wording from §3.2. Do not paraphrase or invent new wording variants. Only the approved canonical forms appear on released DSAT items.

**Step 3b — Apply per-skill stem construction rules**

Each skill family has a stem construction constraint in addition to the canonical wording:

**`command_of_evidence_textual`**
- The stem must quote or closely paraphrase the specific claim to be supported/weakened/illustrated. Do not use a vague stem like "Which choice best supports the text?" — the claim must be explicit.
- `choose_best_support` → "Which choice best supports the claim that [exact claim from or derived from passage]?"
- `choose_best_illustration` → "Which quotation from [work title] if used in the blank would most effectively illustrate the claim that [claim]?"
- `choose_best_weakener` → "Which finding, if true, would most directly undermine the researchers' conclusion that [conclusion]?"

**`command_of_evidence_quantitative`**
- The stem must specify the graphic (table or graph) and the stated claim or example to complete.
- `choose_best_completion_from_data` → "Which choice most effectively uses data from the [table/graph] to complete the [example/statement/claim]?"

**`central_ideas_and_details`**
- `choose_main_idea` → "Which choice best states the main idea of the text?" (for `central_idea` focus)
- `choose_detail` → "Based on the text, [what is true about X / the text indicates that X]?" (for `supporting_detail` focus)
- Do not use "What does the passage suggest?" — this phrasing belongs to `inferences`.

**`inferences`**
- `most_logically_completes` → the passage ends mid-sentence or at a logical gap, and the stem is always: "Which choice most logically completes the text?" The gap must be constructed so that one answer is logically required, not merely plausible. See §13.4 evidentiary standard annotation.
- The blank appears at the end of the passage, not mid-passage.

**`words_in_context`**
- Default stem (blank-fill): "Which choice completes the text with the most logical and precise word or phrase?" — the target word or phrase is removed and replaced with a blank in the passage.
- Alternate stem (underlined): "As used in the text, what does the word '[word]' most nearly mean?" — use only for the `underlined_word_meaning` focus key.
- Do not mix formats within one item. Do not use both a blank and an underlined word.

**`text_structure_and_purpose`**
- `choose_main_purpose` → "Which choice best states the main purpose of the text?" or "Which choice best describes what the text does?"
- `choose_sentence_function` → "Which choice best describes the function of the underlined sentence in the text as a whole?" The target sentence must be underlined in the passage and must perform exactly one named functional role from the §13.6 table.

**`cross_text_connections`**
- `choose_text_relationship` → "Based on the texts, how would [Text 2 source] most likely respond to [Text 1's claim that / Text 1's use of / the assertion in Text 1 that]?" — the specific Text 1 element must be named in the stem, not left generic.
- `choose_agreement_across_texts` → "Based on the texts, both [Text 1 source] and [Text 2 source] would most likely agree with which statement?"
- `choose_difference_across_texts` → "Which choice best describes a difference between the claims made in Text 1 and Text 2?"
- For all cross-text stems, the sources must be labeled "Text 1" and "Text 2" in the stimulus; refer to them by those labels in the stem.

**Step 3c — Record the stem in `prompt_text`**

Once the stem wording is finalized, record it in `prompt_text`. Do not alter the stem wording after Phase 4 begins.

---

### 23.5 Phase 4 — Option design

**Step 4a — Write the correct answer first**

Draft the correct option before drafting any distractor. The correct answer must:
- Unambiguously satisfy the stem and the target `reading_focus_key`
- Be anchored to an `evidence_span_text` — a specific passage excerpt
- Use comparable register, length, and syntactic form to what the distractors will use (do not write the correct answer and then match distractors to it; plan option homogeneity from the start)

**Step 4b — Design three distractors using the three-distractor framework (§16.2)**

Every item must contain:
1. **Primary trap distractor** — targets the `reasoning_trap_key` selected in Phase 1; uses the most common partial-reading error for the skill family
2. **Surface-plausible distractor** — shares topic, vocabulary, or structural form with the correct answer but fails the construct (wrong claim, wrong relationship, wrong direction)
3. **Precision distractor** — almost correct but fails by scope, polarity, attribution, degree, or relationship type; competitive enough to survive first-pass elimination for high-difficulty items

**Step 4c — Apply skill-specific distractor constraints (§16.3)**

Apply the mandatory distractor rules for the selected skill family from §16.3. These are in addition to the three-distractor framework.

**Step 4d — Apply the per-focus recipe (§16.9)**

Look up the `target_reading_focus_key` in the §16.9 table and verify the generated distractors match the required distractor behavior for that focus key.

**Step 4e — Apply the distractor quality gate (§16.4)**

Before finalizing options, run the seven-criterion quality gate from §16.4. Every criterion must pass:
- Incorrectness — each distractor has a named reason in `why_wrong`
- Plausibility — each distractor maps to a real student error pattern with a non-null `plausibility_source_key`
- Diversity — no two distractors fail through the same reasoning path
- Construct alignment — every wrong answer fails the target construct, not random topic mismatch
- Clue control — the key is not longer, more precise, or more polished than distractors
- Option homogeneity — all options share syntax, abstraction level, register, and semantic category
- Separation margin — the key is the single best answer; hard items have ≥2 distractors that survive first-pass elimination

---

### 23.6 Phase 5 — Validation

Run both checklists in full before submitting the item.

**§22.7 Style Authenticity Checklist** — passage prose only. If any check fails, return to Phase 2.

**§21 Validator Checklist** — structural and annotation completeness. If any check fails, return to the appropriate phase.

Additional cross-phase validation:

- [ ] The correct answer is grounded in a non-null `evidence_span_text` that directly supports the answer
- [ ] The primary trap distractor is grounded in the passage (topically related content, adjacent sentence, wrong condition, etc.) — not invented from outside the passage
- [ ] The stem wording exactly matches a canonical form from §3.2 — no paraphrase
- [ ] The `generation_profile` JSON is fully populated and all mandatory conditional fields are present (§16.8)
- [ ] The passage word count is within the skill-family norms from §15.1

If the item passes all Phase 5 checks, annotate `annotation_confidence: "high"` in `review` and set `needs_human_review: false`. If any check required a judgment call, annotate `annotation_confidence: "medium"` and record the judgment in `review_notes`.

---

### 23.7 Complete worked example

The following example executes all five phases for a single item. Use it as a reference template.

**Phase 1 — Profile**

```json
{
  "generation_profile": {
    "topic_broad_key": "social_studies",
    "topic_fine": "linguistics",
    "target_skill_family_key": "inferences",
    "target_reading_focus_key": "causal_inference",
    "target_test_construct_key": "inference_boundary_control",
    "target_craft_subconstruct_key": null,
    "target_reasoning_trap_key": "overreach",
    "passage_structure_pattern": "claim_evidence_explanation",
    "passage_architecture_key": "studied_subgroup_generalization_limit",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "most_logically_completes",
    "target_difficulty_overall": "medium",
    "target_distractor_pattern": [
      "overreach — extends the finding to the broader population beyond what the subgroup evidence supports",
      "reversal — attributes the effect to the wrong direction or wrong variable",
      "outside_knowledge — appeals to general claims about language change not supported by the passage"
    ],
    "inference_type_note": "subgroup_overgeneralization_limit",
    "two_part_claim": false
  }
}
```

**Phase 2 — Passage**

Domain style: `social_studies` → medium-high hedging, named scholar attribution, `claim_evidence_explanation` arc.

Architecture: `studied_subgroup_generalization_limit` → requires (1) evidence from a named subgroup, (2) explicit or implicit warning that the subgroup may not represent the broader population.

> A 2017 study by Labov and colleagues examined code-switching patterns among bilingual adolescents in Philadelphia schools — specifically, students who reported Spanish as their home language. The researchers found that these students shifted to English vocabulary at markedly higher rates during academic discussions than during informal peer interactions, a pattern the team attributed to perceived audience expectations rather than vocabulary limitations. The researchers noted, however, that their participants were drawn entirely from communities with high rates of Spanish-English bilingualism, and cautioned that their findings ________.

Style check (S1–S8): sentence lengths vary (14 / 40 / 32 / 23 words ✓), epistemic hedging ("attributed," "cautioned" ✓), named attribution ("Labov and colleagues" ✓), appositive ("specifically, students who reported Spanish as their home language" ✓), nominalization ("code-switching," "interactions," "limitations" ✓), passive voice limited to "were drawn" ✓.

**Phase 3 — Stem**

`most_logically_completes` → canonical wording: "Which choice most logically completes the text?"

Blank placement: end of the final sentence, after "cautioned that their findings." No alteration to canonical stem wording.

**Phase 4 — Options**

Correct answer (causal_inference / subgroup_overgeneralization_limit):
> **A. may not generalize to bilingual communities with different language environments or demographic profiles**

*Why correct*: Directly applies the stated limitation ("drawn entirely from high-bilingualism communities") to restrict the scope of the findings. Logically required by the passage's final cautionary clause.

Primary trap distractor (overreach):
> **B. demonstrate that code-switching is primarily driven by academic pressure rather than vocabulary competence across all bilingual adolescent populations**

*Why wrong*: Extrapolates the subgroup finding ("audience expectations" in one community) to "all bilingual adolescent populations" — the passage explicitly warns against this generalization. `distractor_type_key: "scope_error"`, `plausibility_source_key: "partial_truth"` (true within the subgroup, not beyond it).

Surface-plausible distractor (reversal — wrong variable):
> **C. suggest that vocabulary limitations, rather than audience expectations, account for the observed code-switching patterns**

*Why wrong*: Reverses the passage's stated explanation: the researchers attributed code-switching to perceived audience expectations, not vocabulary limitations. `distractor_type_key: "inverted_logic"`, `plausibility_source_key: "passage_vocabulary_overlap"` (both terms appear in the passage).

Precision distractor (outside_knowledge):
> **D. align with broader research showing that bilingual speakers consistently prefer English in academic settings**

*Why wrong*: Introduces a general claim not supported by the passage ("broader research," "consistently," "all bilingual speakers"). The passage describes findings for one subgroup and explicitly limits the scope. `distractor_type_key: "overstatement"`, `plausibility_source_key: "common_sense_appeal"`.

Option homogeneity check: All four options are 12–22 words, use subordinate clause structure, and operate at the same level of abstraction ✓. Clue control: the correct answer (A) is not noticeably longer or more qualified than the distractors ✓.

**Phase 5 — Validation**

§22.7: all sentence-level checks pass ✓. Passage contains `studied_subgroup_generalization_limit` elements ✓.

§21: `question_family_key: "information_and_ideas"` ✓, `skill_family_key: "inferences"` ✓, `reading_focus_key: "causal_inference"` ✓, `evidence_span_text: "drawn entirely from communities with high rates of Spanish-English bilingualism"` ✓, `paired_passage_text: null` ✓ (not cross-text), correct option has `is_correct: true` and `precision_score: 3` ✓, three distractors have distinct `distractor_type_key` values ✓.

`review_notes`: "inference_type: subgroup_overgeneralization_limit — correct answer restricts findings to source community; primary trap (B) is the canonical subgroup overgeneralization distractor."

`annotation_confidence: "high"`. `needs_human_review: false`.

---

*Document version: v3.0 — 2026-05-25*
*Merges: `rules_agent_dsat_reading_v1.md` (v1.0) + `rules_agent_dsat_reading_v1_1.md` (v1.1) + `rules_agent_dsat_reading_v2.md` (v2.0)*
*Source authority: CB_ANSWERS_QUESTIONS_ANALYSIS.md (PT4–PT11 official explanation cross-reference)*
*v3.0 additions: §22 Passage Style Fingerprint and Generation Realism — sentence-level rules, domain style signatures, generation failure modes, few-shot exemplars*
*Agent: Claude Sonnet 4.6*
*Domain coverage: Information and Ideas, Craft and Structure*
*Companion file: `rules_agent_dsat_grammar_ingestion_generation_v8.md` (v8.1)*
*Supersedes: v2.0 — remains as historical reference, not as active load target*

## Appendix V — Controlled Vocabulary (generated)

The key lists below are generated from `vocabulary/master.json` by
`scripts/gen_vocab.py`. Do not hand-edit them — edit master.json and
regenerate. They stay in lockstep with the validator enums in
`backend/app/models/ontology.py`.

<!-- VOCAB:system:CONTENT_ORIGINS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CONTENT_ORIGINS`** — Content origin

- `official`
- `unofficial`
- `generated`
<!-- VOCAB:system:CONTENT_ORIGINS END -->

<!-- VOCAB:system:JOB_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`JOB_TYPES`** — Job types

- `ingest`
- `generate`
- `reannotate`
- `overlap_check`
<!-- VOCAB:system:JOB_TYPES END -->

<!-- VOCAB:system:JOB_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`JOB_STATUSES`** — Job statuses (state machine)

- `pending`
- `parsing`
- `extracting`
- `generating`
- `annotating`
- `overlap_checking`
- `validating`
- `approved`
- `needs_review`
- `failed`
- `failed_transient` — Job failed with a transient error after auto-retry exhaustion (HTTP 429, 5xx, timeout, provider rate limit). Eligible for admin retry via /generate/batches/{id}/retry-failed.
- `failed_permanent` — Job failed with a non-recoverable error (malformed JSON after repair, model refusal, validation failure). Does not auto-retry; admin must regenerate-from-spec.
- `retrying` — Row-level guard set during a retry attempt to prevent duplicate concurrent retries of the same job.
<!-- VOCAB:system:JOB_STATUSES END -->

<!-- VOCAB:system:PRACTICE_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PRACTICE_STATUSES`** — Practice status

- `draft`
- `active`
- `retired`
- `rejected` — Failed quality review; terminal state, audit-preserved. Distinct from retired (post-active removal).
<!-- VOCAB:system:PRACTICE_STATUSES END -->

<!-- VOCAB:system:OVERLAP_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`OVERLAP_STATUSES`** — Overlap status

- `none`
- `possible`
- `confirmed`
<!-- VOCAB:system:OVERLAP_STATUSES END -->

<!-- VOCAB:system:RELATION_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`RELATION_TYPES`** — Relation types

- `overlaps_official`
- `derived_from`
- `near_duplicate`
- `generated_from`
- `adapted_from`
<!-- VOCAB:system:RELATION_TYPES END -->

<!-- VOCAB:system:ASSET_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`ASSET_TYPES`** — Asset types

- `pdf`
- `image`
- `screenshot`
- `markdown`
- `json`
- `text`
<!-- VOCAB:system:ASSET_TYPES END -->

<!-- VOCAB:system:CHANGE_SOURCES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CHANGE_SOURCES`** — Change sources

- `ingest`
- `generate`
- `admin_edit`
- `reprocess`
<!-- VOCAB:system:CHANGE_SOURCES END -->

<!-- VOCAB:shared:STIMULUS_MODE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STIMULUS_MODE_KEYS`** — V3 §3.1 stimulus_mode_key

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `notes_bullets`
- `notes_summary`
- `poem`
<!-- VOCAB:shared:STIMULUS_MODE_KEYS END -->

<!-- VOCAB:system:TEST_FORMAT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TEST_FORMAT_KEYS`** — Rules v8 generation format keys

- `digital_app_adaptive`
- `nondigital_linear_accommodation`
<!-- VOCAB:system:TEST_FORMAT_KEYS END -->

<!-- VOCAB:system:SOURCE_STATS_FORMAT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SOURCE_STATS_FORMAT_KEYS`** — Rules v8 source stats format keys

- `official_digital`
- `official_nondigital_linear`
<!-- VOCAB:system:SOURCE_STATS_FORMAT_KEYS END -->

<!-- VOCAB:shared:STEM_TYPE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STEM_TYPE_KEYS`** — V3 §3.2 stem_type_key

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
- `choose_words_in_context`
- `choose_word_in_context`
- `choose_cross_text_connection`
- `choose_text_relationship`
- `choose_agreement_across_texts`
- `choose_difference_across_texts`
- `choose_best_inference`
- `choose_command_of_evidence_textual`
- `choose_command_of_evidence_quantitative`
- `choose_central_detail`
- `choose_detail`
- `choose_best_illustration`
- `choose_best_weakener`
- `conform_to_standard_english`
- `most_logically_completes`
- `synthesize_information`
- `compare_contributions`
<!-- VOCAB:shared:STEM_TYPE_KEYS END -->

<!-- VOCAB:shared:DISTRACTOR_TYPE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DISTRACTOR_TYPE_KEYS`** — V3 §12.1 distractor_type_key (option-level)

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
- `partial_match`
- `correct`
- `topical_relevance_without_logical_connection`
- `indirect_evidence`
- `inverted_logic`
- `detail_trap`
- `overreach`
- `data_context_mismatch`
- `connotation_mismatch`
- `plausible_synonym`
- `wrong_action_verb`
- `reversed_attribution`
- `confirmed_when_contradicted`
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `cause_effect_misalignment`
- `contradiction`
- `figurative_literal_confusion`
- `false_concession_trap`
<!-- VOCAB:shared:DISTRACTOR_TYPE_KEYS END -->

<!-- VOCAB:reading:REASONING_TRAP_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REASONING_TRAP_KEYS`** — Reading v2 §10 reasoning_trap_key (question-level)

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
- `wrong_time_window`
- `direction_reversal`
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
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
- `polarity_mismatch`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `figurative_literal_confusion`
- `false_concession_trap`
<!-- VOCAB:reading:REASONING_TRAP_KEYS END -->

<!-- VOCAB:shared:ANSWER_MECHANISM_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`ANSWER_MECHANISM_KEYS`** — V3 §3.3 answer_mechanism_key

- `rule_application`
- `pattern_matching`
- `evidence_location`
- `inference`
- `data_synthesis`
- `evidence_matching`
- `contextual_substitution`
- `rhetorical_classification`
- `cross_text_comparison`
- `polarity_resolution`
<!-- VOCAB:shared:ANSWER_MECHANISM_KEYS END -->

<!-- VOCAB:shared:SOLVER_PATTERN_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SOLVER_PATTERN_KEYS`** — V3 §3.3 solver_pattern_key

- `apply_grammar_rule_directly`
- `locate_error_zone`
- `compare_register`
- `evaluate_transition`
- `synthesize_notes`
- `eliminate_by_boundary`
- `locate_claim_then_match_evidence`
- `read_graphic_then_match_claim`
- `summarize_then_compare`
- `locate_detail_directly`
- `identify_logical_gap`
- `substitute_and_test`
- `classify_rhetorical_move`
- `summarize_both_then_compare`
- `apply_negation_logic`
- `locate_figurative_function`
<!-- VOCAB:shared:SOLVER_PATTERN_KEYS END -->

<!-- VOCAB:shared:STUDENT_FAILURE_MODE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STUDENT_FAILURE_MODE_KEYS`** — V3 §21.3 student_failure_mode_key

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
- `negation_blindness`
- `connotation_surface_match`
- `local_role_misread`
- `register_tone_blindness`
- `figurative_meaning_blindness`
- `exact_value_misread`
- `individual_from_aggregate`
- `all_measures_not_checked`
- `wrong_comparison_direction`
- `wrong_group_selected`
- `wrong_row_column_lookup`
- `single_measure_overread`
- `local_maximum_overread`
- `absolute_value_overweighting`
- `constraint_ignored`
- `two_part_claim_partial_match`
- `control_group_misidentification`
- `evidence_scope_mismatch`
- `subgroup_overgeneralization`
- `parenthetical_function_confusion`
- `rhetorical_verb_partial`
- `scope_role_confusion`
- `author_action_overread`
- `attribution_swap`
- `agreement_degree_overread`
- `relationship_simplification`
- `polarity_blindness`
- `tense_proximity_pull`
- `internal_unit_punctuation_insertion`
- `declarative_question_confusion`
- `restrictive_appositive_comma_insertion`
- `title_name_comma_insertion`
- `nonfinite_for_finite`
- `inflected_after_modal`
- `plural_pronoun_for_clause_antecedent`
- `past_tense_for_literary_present`
- `transition_wrong_direction`
- `notes_synthesis_wrong_goal`
- `notes_synthesis_audience_mismatch`
- `adverb_adjective_confusion`
- `illogical_comparison_blindness`
- `confused_word_substitution`
- `preposition_idiom_error`
- `notes_synthesis_content_omission`
<!-- VOCAB:shared:STUDENT_FAILURE_MODE_KEYS END -->

<!-- VOCAB:shared:DISTRACTOR_DISTANCE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DISTRACTOR_DISTANCE_KEYS`** — V3 §21.2 distractor_distance

- `wide`
- `moderate`
- `tight`
<!-- VOCAB:shared:DISTRACTOR_DISTANCE_KEYS END -->

<!-- VOCAB:shared:DIFFICULTY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DIFFICULTY_KEYS`** — V3 §3.3 difficulty keys

- `low`
- `medium`
- `high`
<!-- VOCAB:shared:DIFFICULTY_KEYS END -->

<!-- VOCAB:shared:FREQUENCY_BANDS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`FREQUENCY_BANDS`** — V3 §3.3 frequency bands

- `very_high`
- `high`
- `medium`
- `low`
- `very_low`
<!-- VOCAB:shared:FREQUENCY_BANDS END -->

<!-- VOCAB:shared:TENSE_REGISTER_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TENSE_REGISTER_KEYS`** — V3 §17.6 tense register keys

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`
- `literary_present`
<!-- VOCAB:shared:TENSE_REGISTER_KEYS END -->

<!-- VOCAB:shared:PASSAGE_ARCHITECTURE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PASSAGE_ARCHITECTURE_KEYS`** — V3 §22 passage_architecture_key

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
- `unexpected_finding`
- `cautionary_framing`
- `problem_solution`
- `compare_contrast`
- `chronological_sequence`
- `research_summary`
- `claim_evidence_explanation`
- `analogy_driven_argument`
- `multi_perspective_presentation`
- `qualification_restatement`
- `experiment_hypothesis_control_result`
- `indirect_effect_mediation`
- `alternative_explanation_ruled_out`
- `mechanism_manipulation_test`
- `studied_subgroup_generalization_limit`
<!-- VOCAB:shared:PASSAGE_ARCHITECTURE_KEYS END -->

<!-- VOCAB:shared:QUESTION_FAMILY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`QUESTION_FAMILY_KEYS`** — question_family_key

- `conventions_grammar`
- `expression_of_ideas`
- `craft_and_structure`
- `information_and_ideas`
<!-- VOCAB:shared:QUESTION_FAMILY_KEYS END -->

<!-- VOCAB:reading:READING_QUESTION_FAMILY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`READING_QUESTION_FAMILY_KEYS`** — Reading question families (subset of QUESTION_FAMILY_KEYS)

- `craft_and_structure`
- `information_and_ideas`
<!-- VOCAB:reading:READING_QUESTION_FAMILY_KEYS END -->

<!-- VOCAB:reading:READING_SKILL_FAMILY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`READING_SKILL_FAMILY_KEYS`** — Reading skill families

- `command_of_evidence_textual`
- `command_of_evidence_quantitative`
- `central_ideas_and_details`
- `inferences`
- `words_in_context`
- `text_structure_and_purpose`
- `cross_text_connections`
<!-- VOCAB:reading:READING_SKILL_FAMILY_KEYS END -->

<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`READING_FOCUS_BY_SKILL_FAMILY`** — Reading v2 reading_focus_key (grouped by skill family)

- **`command_of_evidence_textual`**
  - `evidence_supports_claim`
  - `evidence_weakens_claim`
  - `evidence_illustrates_claim`
  - `evidence_explains_claim`
  - `evidence_qualifies_claim`
- **`command_of_evidence_quantitative`**
  - `data_supports_claim`
  - `data_weakens_claim`
  - `data_completes_example`
  - `data_comparison`
  - `data_trend`
- **`central_ideas_and_details`**
  - `central_idea`
  - `main_purpose`
  - `passage_summary`
  - `supporting_detail`
  - `character_or_author_detail`
- **`inferences`**
  - `causal_inference`
  - `motivational_inference`
  - `implication_inference`
  - `predictive_inference`
  - `cross_text_inference`
- **`words_in_context`**
  - `contextual_meaning`
  - `connotation_fit`
  - `precision_fit`
  - `register_fit`
  - `underlined_word_meaning`
  - `polarity_fit`
  - `figurative_language_meaning`
- **`text_structure_and_purpose`**
  - `overall_purpose`
  - `sentence_function`
  - `structural_pattern`
  - `author_stance`
- **`cross_text_connections`**
  - `text2_response_to_text1`
  - `both_texts_agree`
  - `texts_disagree`
  - `text2_qualifies_text1`
  - `text2_contradicts_text1`
  - `methodological_critique`
  - `expectation_violation`
<!-- VOCAB:reading:READING_FOCUS_BY_SKILL_FAMILY END -->

<!-- VOCAB:reading:TEST_CONSTRUCT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TEST_CONSTRUCT_KEYS`** — Reading v2 target_test_construct_key

- `contextual_semantic_precision`
- `rhetorical_function_precision`
- `cross_text_relationship_precision`
- `evidence_relation_precision`
- `inference_boundary_control`
- `quantitative_constraint_tracking`
- `figurative_interpretation_precision`
<!-- VOCAB:reading:TEST_CONSTRUCT_KEYS END -->

<!-- VOCAB:reading:CRAFT_SUBCONSTRUCT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CRAFT_SUBCONSTRUCT_KEYS`** — Reading v2 target_craft_subconstruct_key

- `wic_local_semantic_role`
- `wic_tone_register_fit`
- `wic_polarity_logic`
- `tsp_global_rhetorical_purpose`
- `tsp_local_sentence_function`
- `tsp_author_action_precision`
- `ctc_agreement_degree`
- `ctc_attribution_tracking`
- `ctc_response_to_claim`
<!-- VOCAB:reading:CRAFT_SUBCONSTRUCT_KEYS END -->

<!-- VOCAB:reading:TEXT_RELATIONSHIP_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TEXT_RELATIONSHIP_KEYS`** — Reading v2 cross-text relationship keys

- `direct_contradiction`
- `confirmation_with_qualification`
- `expectation_violation`
- `methodological_critique`
- `partial_agreement`
- `broad_support`
- `causal_specification`
<!-- VOCAB:reading:TEXT_RELATIONSHIP_KEYS END -->

<!-- VOCAB:reading:QUANTITATIVE_SUB_PATTERN_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`QUANTITATIVE_SUB_PATTERN_KEYS`** — Reading v2 quantitative_sub_pattern

- `standard`
- `exact_value_lookup`
- `timing_constrained`
- `all_measures`
- `repeated_highest`
- `two_variable_opposite`
- `composition_change`
- `binned_distribution`
<!-- VOCAB:reading:QUANTITATIVE_SUB_PATTERN_KEYS END -->

<!-- VOCAB:reading:SENTENCE_FUNCTION_ROLE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SENTENCE_FUNCTION_ROLE_KEYS`** — Reading v2 target_sentence_function_role

- `concession`
- `elaboration`
- `contrast_motivation`
- `parenthetical_definition`
- `example`
- `consequence`
- `hypothesis`
- `counter_evidence`
- `scope_qualification`
- `conventional_approach`
- `obstacle`
- `background_setup`
<!-- VOCAB:reading:SENTENCE_FUNCTION_ROLE_KEYS END -->

<!-- VOCAB:shared:TOPIC_BROAD_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TOPIC_BROAD_KEYS`** — Broad topic keys

- `science`
- `history`
- `literature`
- `social_studies`
- `humanities`
- `arts`
- `economics`
- `technology`
- `environment`
<!-- VOCAB:shared:TOPIC_BROAD_KEYS END -->

<!-- VOCAB:shared:PLAUSIBILITY_SOURCE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PLAUSIBILITY_SOURCE_KEYS`** — V3 §10.3 plausibility_source_key

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`
- `none`
- `passage_vocabulary_overlap`
- `topical_proximity`
- `partial_truth`
- `common_sense_appeal`
- `common_definition_appeal`
- `near_synonym_appeal`
- `rhetorical_surface_similarity`
- `attribution_swap`
<!-- VOCAB:shared:PLAUSIBILITY_SOURCE_KEYS END -->

<!-- VOCAB:system:REVIEW_TASK_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_TASK_TYPES`** — Review task types for the generation review swarm

- `generation_realism_review` — Multi-model quality review of generated DSAT questions
<!-- VOCAB:system:REVIEW_TASK_TYPES END -->

<!-- VOCAB:system:REVIEW_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_STATUSES`** — Per-reviewer outcome status

- `ok` — Review completed successfully
- `transient_failed` — Review failed due to transient error (rate limit, network)
- `permanent_failed` — Review failed permanently (malformed output, model refusal)
<!-- VOCAB:system:REVIEW_STATUSES END -->

<!-- VOCAB:system:REVIEW_RUN_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_RUN_STATUSES`** — Review run lifecycle status

- `running` — Review run in progress
- `complete` — All reviewers completed successfully
- `partial` — Some reviewers failed but minimum completed
- `failed` — Review run failed entirely
<!-- VOCAB:system:REVIEW_RUN_STATUSES END -->

<!-- VOCAB:system:TRIGGERED_BY_VALUES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TRIGGERED_BY_VALUES`** — What triggered a review run

- `auto_on_save` — Automatically triggered when a generated question is saved
- `manual_question` — Admin manually triggered review for a single question
- `manual_batch` — Admin manually triggered review for a batch
- `recalibration` — Re-review triggered by calibration threshold change
- `rubric_bump` — Re-review triggered by rubric version change
<!-- VOCAB:system:TRIGGERED_BY_VALUES END -->

<!-- VOCAB:system:REVIEW_VERDICTS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_VERDICTS`** — Per-reviewer verdict on a generated question

- `accept` — Question meets all quality thresholds
- `needs_human_review` — Borderline quality; human review recommended
- `reject` — Question fails quality thresholds
<!-- VOCAB:system:REVIEW_VERDICTS END -->

<!-- VOCAB:system:CONSENSUS_VERDICTS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CONSENSUS_VERDICTS`** — Consensus verdict after multi-model review (Phase 5)

- `admin_review_ready` — All thresholds cleared; ready for admin review
- `reject_recommended` — Consensus recommends rejection
- `regenerate_recommended` — Consensus recommends regeneration
- `blocked_overlap` — Unresolved official overlap blocks approval
- `insufficient_reviews` — Fewer than 2 reviewers succeeded
<!-- VOCAB:system:CONSENSUS_VERDICTS END -->
