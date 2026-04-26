# rules_agent_dsat_reading_v1.md

## IMPORTANT NOTE

This file is the companion reading-comprehension rules layer to
`rules_agent_dsat_grammar_ingestion_generation_v3.md`.

The V3 grammar file covers:
- Standard English Conventions (SEC)
- Grammar-adjacent Expression of Ideas (Transitions, Rhetorical Synthesis)

This file covers the remaining two domains, which the V3 grammar file
explicitly **forbids** `grammar_role_key` from classifying:

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
propose an amendment using the amendment process (§15) rather than inventing a
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

Every item annotation must produce these sections, mirroring V3:

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
  "generation_timestamp": "2026-04-25T00:00:00Z",
  "model_version": "rules_agent_reading_v1.0"
}
```

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

Use the controlled vocabulary from the V3 grammar file. All values apply here:

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
V3 grammar-domain stem types (`choose_best_grammar_revision`, `choose_best_transition`,
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

- `contextual_meaning` — correct word is determined by surrounding sentences (most common variant)
- `connotation_fit` — multiple synonyms; correct word determined by tone, register, or evaluative stance
- `precision_fit` — correct word is the most specific/precise among near-synonyms
- `register_fit` — correct word matches the academic or formal register of the passage
- `underlined_word_meaning` — "most nearly mean" stem; word is underlined rather than blank

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

These fields retain the same semantics as V3 but apply differently in reading domains:

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

- If the correct option cites a single absolute value → `data_completes_example`
- If the correct option requires comparing two values → `data_comparison`
- If the correct option requires recognizing a directional pattern → `data_trend`

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

- If all four options are near-synonyms and the distinction is evaluative/tonal → `connotation_fit`
- If the distinction is degree of specificity → `precision_fit`
- If the blank or word is in a passage with a pronounced formal or technical register → `register_fit`
- If stem uses "most nearly mean" with an underlined word → `underlined_word_meaning`

**Mandatory annotation:**

The `why_wrong` field for each distractor must explain whether the failure is:
(a) wrong denotation, (b) right denotation but wrong connotation, or (c) right denotation
and connotation but wrong register. This three-level distinction is diagnostic for generation.

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

### 14.1 Difficulty fields

Use the same four-component difficulty rating as V3:

```json
{
  "difficulty_overall": "medium",
  "difficulty_reading": "high",
  "difficulty_grammar": "low",
  "difficulty_inference": "medium",
  "difficulty_vocab": "low"
}
```

For reading-domain questions, `difficulty_grammar` will almost always be `low`.
The meaningful difficulty axes are `difficulty_reading`, `difficulty_inference`,
and `difficulty_vocab`.

### 14.2 Difficulty anchors by skill

**Command of Evidence — Textual:**

| Level | Characteristics |
|---|---|
| `low` | Claim in final sentence, stated explicitly; one option directly addresses it; three are off-topic |
| `medium` | Claim requires inference across two sentences; one trap option addresses the outcome from the wrong cause |
| `high` | Claim embedded in complex structure; multiple options partially match; correct answer requires distinguishing direct from indirect causal evidence; weaken variants |

**Command of Evidence — Quantitative:**

| Level | Characteristics |
|---|---|
| `low` | Two-row/column graphic; claim is obvious; correct answer cites the highest or lowest value |
| `medium` | Multi-category graphic; correct answer requires comparing two non-obvious groups |
| `high` | Passage claim is indirect; multiple options have accurate data readings; correct answer requires recognizing a required contrast (not an absolute value); direction reversal (weaken) |

**Central Ideas and Details:**

| Level | Characteristics |
|---|---|
| `low` | Main idea stated in first or last sentence; wrong answers clearly off-topic |
| `medium` | Main idea must be inferred across two or three sentences; one wrong option correctly describes a supporting detail |
| `high` | Passage is structured around an unexpected finding; correct answer captures the author's evaluative stance; wrong answers use passage vocabulary but flip the author's position |

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
   the same domain bucket — classify using the V3 grammar file's `expression_of_ideas`
   keys, not this file. Information and Ideas and Craft and Structure are the two domains
   covered here; Expression of Ideas and SEC are covered in V3.

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

Any annotation with these patterns should be rerouted to the V3 grammar file.

---

## 19. Amendment Process

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

## 20. Validator Checklist

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

---

*Document version: v1.0 — 2026-04-25*
*Agent: Claude Sonnet 4.6 (`claude-sonnet-4-6`)*
*Domain coverage: Information and Ideas, Craft and Structure*
*Companion file: `rules_agent_dsat_grammar_ingestion_generation_v3.md`*
