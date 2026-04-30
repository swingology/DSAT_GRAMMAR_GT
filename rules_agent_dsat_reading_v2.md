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

### 2.3 `review` section schema

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

**Reading focus disambiguation for Words in Context:**

- If all four options are near-synonyms and the distinction is evaluative/tonal → `connotation_fit`
- If the distinction is degree of specificity → `precision_fit`
- If the blank or word is in a passage with a pronounced formal or technical register → `register_fit`
- If stem uses "most nearly mean" with an underlined word → `underlined_word_meaning`
- If the passage contains a negator, concessive phrase, or contrast marker and all options are near-synonyms differing in evaluative direction when the negator is applied → `polarity_fit`
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

---

## 10. Reasoning Trap Keys

Use `reasoning_trap_key` to describe the primary wrong-answer mechanism for the question.
This applies at the question level (for the most dangerous trap) and at the option level
(per option).

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
- `contradiction` — states the opposite of what the text says or implies
- `absolute_language` — uses "always," "never," "all," "none" — the SAT rarely places absolute claims in correct answers
- `outside_knowledge` — true in the real world but not stated or implied by the passage
- `cause_effect_misalignment` — proposes a relationship the passage does not establish
- `scope_extension` — applies a conclusion to a population or domain the passage does not address
- `overspecification` — correct in direction but too specific (e.g., names a sub-group the passage does not specify)
- `wrong_row_or_column` — quantitative; option uses the correct table but cites the wrong row or column identifier
- `wrong_time_window` — quantitative; option uses real data that is accurate for a different time period than the one the passage's constraint specifies
- `all_measures_not_checked` — quantitative; option is true for one measure or one time point but the passage claim requires the comparison to hold across all measures or all periods
- `individual_from_aggregate` — quantitative; option infers individual-level information from a binned or aggregated graphic that only supports group-level claims
- `direction_reversal` — quantitative; option correctly identifies the variable being tracked but states the opposite direction of change

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
- `reversed_attribution` — facts from Text 1 attributed to Text 2 or vice versa — most common Cross-Text trap
- `extreme_language` — uses "always," "never," "completely," "impossible" — signals incorrect option in Cross-Text
- `textual_mimicry` — uses vocabulary directly from the passage but distorts the meaning or relationship
- `confirmed_when_contradicted` — describes Text 2 as supporting Text 1 when it contradicts it, or vice versa
- `polarity_mismatch` — the option is a plausible word in isolation but inverts the intended meaning when combined with the passage's negator or concessive construction; the student selected the option by reading the surrounding words without applying the negator to the target blank

---

## 11. Text Relationship Keys (Cross-Text Connections)

Use `text_relationship_key` for Cross-Text Connections questions only.

- `direct_contradiction` — authors reach opposite conclusions about the same question
- `confirmation_with_qualification` — Text 2 broadly supports Text 1 but identifies a limiting condition
- `expectation_violation` — Text 2 expected Text 1's theory but found contrary evidence
- `methodological_critique` — Text 2 challenges Text 1's method or scope rather than its conclusion
- `partial_agreement` — authors agree on one aspect while disagreeing on another
- `broad_support` — Text 2 provides additional evidence that corroborates Text 1

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
- `cause_effect_misalignment`
- `contradiction`

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

### 16.3 Generation must match SAT style

Generated items must be:

- Concise (passage within word-count norms for the skill)
- Formally or neutrally academic in register
- Self-contained — passage provides all information needed
- Free of trivia — the question tests reasoning, not prior knowledge
- One correct answer only — the three distractors must be unambiguously wrong on the tested reasoning

### 16.4 Generation must respect stem wording conventions

Use only the approved `stem_type_key` wording conventions from §3.2. Do not paraphrase
or invent new stem variants. SAT authenticity depends on recognizable stem patterns.

**Critical**: Words in Context generated items must use "most logical and precise word or
phrase" (blank-fill format) as the default, not "most nearly mean" (underlined format),
because the blank-fill format is the dominant contemporary variant.

### 16.5 Cross-Text Connections generation constraints

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

### 16.6 Generation profile extension fields (added in v2 from v1.1 §12)

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

### 19.6 Summary: all 14 approved failure mode keys

| # | Key | Domain |
|---|-----|--------|
| 1 | `negation_blindness` | Words in Context |
| 2 | `polarity_blindness` (synonym of #1) | Words in Context |
| 3 | `connotation_surface_match` | Words in Context |
| 4 | `exact_value_misread` | Quantitative CoE |
| 5 | `wrong_time_window` | Quantitative CoE |
| 6 | `individual_from_aggregate` | Quantitative CoE |
| 7 | `all_measures_not_checked` | Quantitative CoE |
| 8 | `wrong_comparison_direction` | Quantitative CoE |
| 9 | `two_part_claim_partial_match` | CoE-Textual |
| 10 | `control_group_misidentification` | CoE-Textual |
| 11 | `evidence_scope_mismatch` | CoE-Textual |
| 12 | `subgroup_overgeneralization` | Inferences |
| 13 | `parenthetical_function_confusion` | Text Structure and Purpose |
| 14 | `rhetorical_verb_partial` | Text Structure and Purpose |

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

---

*Document version: v2.0 — 2026-04-29*
*Merges: `rules_agent_dsat_reading_v1.md` (v1.0) + `rules_agent_dsat_reading_v1_1.md` (v1.1)*
*Source authority: CB_ANSWERS_QUESTIONS_ANALYSIS.md (PT4–PT11 official explanation cross-reference)*
*Agent: Claude Opus 4.6*
*Domain coverage: Information and Ideas, Craft and Structure*
*Companion file: `rules_agent_dsat_grammar_ingestion_generetion_v7.md`*
*Supersedes: v1.0 + v1.1 addendum — these remain as historical reference, not as active load targets*
