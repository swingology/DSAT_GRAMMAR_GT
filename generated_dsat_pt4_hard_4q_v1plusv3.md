# DSAT Reading & Writing — Generated Hard Items (4)

**Source specs (both applied):**
- `rules_agent_dsat_reading_v1.md` — Information and Ideas, Craft and Structure
- `rules_agent_dsat_grammar_ingestion_generation_v3.md` — Standard English Conventions, Expression of Ideas

**Ground-truth reference:** SAT Practice Test 4 (Digital), Section 1, Module 1
**Generation date:** 2026-04-25
**Target difficulty:** `difficulty_overall: high` on each item; `distractor_strength: high` across the set
**Coverage:** Cross-Text Connections (V1) · Command of Evidence Quantitative (V1) · Text Structure and Purpose (V1) · SEC paired-dash appositive (V3)

---

## Question 1 — Cross-Text Connections (V1 rules)

*Modeled on PT4 M1 Q9 (Graeber/Wengrow vs. conventional wisdom). Pushed harder by making Text 2 a **methodological** critique rather than a direct contradiction — the trap distractors will read it as full agreement or as direct contradiction.*

**Text 1**

In a 2023 study, paleoclimatologist Mia Carter and her team analyzed isotope ratios in Greenland ice cores spanning a 700-year window and concluded that medieval-era cooling in the North Atlantic was driven principally by a sequence of major tropical volcanic eruptions rather than by any reduction in solar irradiance. Carter's model attributes about 75 percent of the observed cooling to volcanic forcing, leaving solar variability a marginal role.

**Text 2**

Geophysicist Aamir Khan has cautioned that conclusions about medieval climate forcing are highly sensitive to the geographic distribution of the proxy records on which they depend. Greenland ice cores, he notes, reliably register North Atlantic atmospheric chemistry but provide little information about the Pacific or the Southern Hemisphere — regions where an independent solar signature, if present, would most plausibly appear. Any forcing study drawing on a single high-latitude basin, he warns, risks systematically underweighting the solar contribution.

**Based on the texts, how would Khan (Text 2) most likely describe Carter's conclusion (Text 1)?**

- A) As likely correct in identifying tropical eruptions as the principal driver but probably underestimating the magnitude of the solar contribution.
- B) As contradicted by Pacific and Southern Hemisphere isotope evidence that Carter's team had access to but chose not to consult.
- C) As constrained by a sampling strategy that may have systematically diminished the apparent role of solar variability.
- D) As fundamentally mistaken about the chronology of medieval tropical eruptions.

**Correct answer:** C

### V1 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 1,
    "stimulus_mode_key": "prose_paired",
    "stem_type_key": "choose_text_relationship",
    "prompt_text": "Based on the texts, how would Khan (Text 2) most likely describe Carter's conclusion (Text 1)?",
    "correct_option_label": "C",
    "explanation_short": "Khan's objection is methodological — the geographic scope of Carter's proxy record — not a substantive denial of the volcanic-primary conclusion or an alternative dataset.",
    "explanation_full": "Text 2 makes a single move: it argues that any conclusion drawn from Greenland ice cores alone is geographically biased in a way that would underweight the solar signal. Khan does not (a) endorse the volcanic-primary conclusion, (b) cite contradictory Pacific/Southern Hemisphere evidence, or (c) contest the eruption chronology. He flags a sampling problem. C captures exactly that: a constraint on the sampling strategy that 'may have systematically diminished the apparent role of solar variability.' A is the strongest distractor; it is wrong because Khan never endorses the volcanic-primary conclusion — he merely points out a bias in the method. B invents Pacific evidence that Text 2 explicitly says is missing. D is unsupported; nothing in Text 2 questions the eruption chronology.",
    "evidence_span_text": "Any forcing study drawing on a single high-latitude basin ... risks systematically underweighting the solar contribution."
  },
  "classification": {
    "domain": "Craft and Structure",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "cross_text_connections",
    "reading_focus_key": "text2_response_to_text1",
    "text_relationship_key": "methodological_critique",
    "secondary_reading_focus_keys": ["text2_qualifies_text1"],
    "reasoning_trap_key": "confirmed_when_contradicted",
    "evidence_scope_key": "paired_passage",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "cross_text_comparison",
    "solver_pattern_key": "summarize_both_then_compare",
    "stimulus_mode_key": "prose_paired",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "topic_broad": "science",
    "topic_fine": "paleoclimatology",
    "reading_scope": "paired-passage",
    "reasoning_demand": "methodological-critique recognition under endorsement and contradiction traps",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "cross_text_connections > inferences (paired passages present)",
    "classification_rationale": "Text 2 attacks Text 1's method, not its conclusion. The correct option must capture the methodological-critique relationship without inflating it into endorsement or contradiction."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "As likely correct in identifying tropical eruptions as the principal driver but probably underestimating the magnitude of the solar contribution.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "partial_match",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "text2_response_to_text1",
      "why_plausible": "Reuses Text 2's 'underweighting the solar contribution' phrasing and sounds like a balanced reading.",
      "why_wrong": "Khan never endorses the volcanic-primary conclusion. He flags a methodological bias; he does not concede the substantive finding.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2
    },
    {
      "option_label": "B",
      "option_text": "As contradicted by Pacific and Southern Hemisphere isotope evidence that Carter's team had access to but chose not to consult.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "overreach",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "text2_response_to_text1",
      "why_plausible": "Text 2 mentions the Pacific and Southern Hemisphere, priming the idea of contradicting evidence from those regions.",
      "why_wrong": "Text 2 explicitly says the relevant Pacific/Southern Hemisphere proxies are absent from Greenland ice cores. It does not claim such evidence exists and was ignored.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "As constrained by a sampling strategy that may have systematically diminished the apparent role of solar variability.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "plausibility_source_key": null,
      "why_plausible": "Captures Khan's exact methodological move: bias in geographic sampling underweights solar.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "As fundamentally mistaken about the chronology of medieval tropical eruptions.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "contradiction",
      "plausibility_source_key": "topical_proximity",
      "option_error_focus_key": "text2_response_to_text1",
      "why_plausible": "Sounds like a strong scholarly objection within the same topical area.",
      "why_wrong": "Text 2 does not address eruption chronology at all; it addresses geographic sampling.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "For response-stem Cross-Text items, classify the relationship type before reading options; the correct option must capture that exact relationship and no more.",
    "trap_mechanism": "Methodological critique looks superficially like both partial endorsement (A) and direct contradiction (B/D). Two of the three distractors borrow vocabulary directly from Text 2.",
    "correct_answer_reasoning": "Text 2 attacks the geographic sampling, not the conclusion or the chronology. C names that exact move ('constrained by a sampling strategy ... diminished the apparent role of solar variability').",
    "distractor_analysis_summary": "A inflates the critique into partial endorsement; B fabricates contradicting evidence; D shifts the critique to an unmentioned domain (chronology)."
  },
  "generation_profile": {
    "target_skill_family_key": "cross_text_connections",
    "target_reading_focus_key": "text2_response_to_text1",
    "target_text_relationship_key": "methodological_critique",
    "target_reasoning_trap_key": "confirmed_when_contradicted",
    "target_stimulus_mode_key": "prose_paired",
    "target_stem_type_key": "choose_text_relationship",
    "distractor_pattern": [
      "partial endorsement that grants Text 1's substantive conclusion",
      "overreach that invents contradicting evidence Text 2 does not cite",
      "contradiction shifted to a topic Text 2 does not address"
    ],
    "passage_template": "Text 1: [scientist X] concludes that [phenomenon] is driven principally by [factor A], not [factor B]. Text 2: [scientist Y] cautions that conclusions like X's are highly sensitive to [methodological constraint] and warns that the method may underweight [factor B].",
    "generation_timestamp": "2026-04-25T00:00:00Z",
    "model_version": "rules_agent_reading_v1.0"
  },
  "review": {
    "annotation_confidence": 0.92,
    "needs_human_review": false,
    "review_notes": "Per V1 §13.7 critical rule, response-type stems are disagreement-oriented; the correct answer reflects methodological challenge, not endorsement. A is precision_score 2 because it is closer to the right relationship type than B or D but still inflates the critique into substantive concession."
  }
}
```

---

## Question 2 — Command of Evidence — Quantitative (V1 rules)

*Modeled on PT4 M1 Q14 (Gómez-Bahamón flycatcher hypothesis) and Q17 (mycorrhizal fungi). Pushed harder by requiring a **multi-row comparison** (every native > every introduced), not a single value cite, and by including a partially-true single-pair comparison (D) as the strongest trap.*

**Passage**

Ecologist Jameson Patel investigated whether the bee species *Bombus impatiens* preferentially visits native versus introduced flowering plants in restored midwestern prairies. Patel and his team measured the average number of *B. impatiens* visits per hour to four flowering species over the bloom season — two native (purple coneflower, black-eyed Susan) and two introduced (red clover, oxeye daisy). Patel argues that *B. impatiens* preferentially visits native species. To support this claim, Patel cites data showing that ______

**Average *B. impatiens* visits per hour, by plant species**

| Plant species | Native to North America? | Avg visits per hour |
|---|---|---|
| Purple coneflower | yes | 14.3 |
| Black-eyed Susan | yes | 12.8 |
| Red clover | no | 7.9 |
| Oxeye daisy | no | 6.2 |

**Which choice most effectively uses data from the table to complete the statement?**

- A) purple coneflower received an average of 14.3 *B. impatiens* visits per hour over the bloom season.
- B) red clover, an introduced species, received an average of 7.9 visits per hour, more than oxeye daisy at 6.2.
- C) each of the two native species received more *B. impatiens* visits per hour than either of the two introduced species.
- D) purple coneflower, a native species, received nearly twice as many visits per hour as oxeye daisy, an introduced species.

**Correct answer:** C

### V1 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 2,
    "stimulus_mode_key": "prose_plus_table",
    "stem_type_key": "choose_best_completion_from_data",
    "prompt_text": "Which choice most effectively uses data from the table to complete the statement?",
    "correct_option_label": "C",
    "explanation_short": "The claim is a general preference for native over introduced; only an option spanning all four species establishes that pattern.",
    "explanation_full": "Patel claims B. impatiens 'preferentially visits native species' — a general statement about the native-vs-introduced contrast. The supporting data must demonstrate that pattern across the dataset. C does exactly that: each of the two native species (14.3, 12.8) received more visits than either of the two introduced species (7.9, 6.2). A states a single absolute value with no comparison and so cannot support a comparative claim. B compares two introduced species to each other, which is irrelevant to the native-vs-introduced claim. D states a single native-vs-introduced comparison (purple coneflower vs. oxeye daisy) — accurate, but a one-pair comparison does not establish the general preference, which requires that every native exceed every introduced.",
    "evidence_span_text": "Purple coneflower: 14.3 / Black-eyed Susan: 12.8 / Red clover: 7.9 / Oxeye daisy: 6.2",
    "table_data": [
      {"plant_species": "Purple coneflower", "native": "yes", "avg_visits_per_hour": 14.3},
      {"plant_species": "Black-eyed Susan", "native": "yes", "avg_visits_per_hour": 12.8},
      {"plant_species": "Red clover", "native": "no", "avg_visits_per_hour": 7.9},
      {"plant_species": "Oxeye daisy", "native": "no", "avg_visits_per_hour": 6.2}
    ]
  },
  "classification": {
    "domain": "Information and Ideas",
    "question_family_key": "information_and_ideas",
    "skill_family_key": "command_of_evidence_quantitative",
    "reading_focus_key": "data_supports_claim",
    "secondary_reading_focus_keys": ["data_comparison"],
    "reasoning_trap_key": "single_sector_focus",
    "evidence_scope_key": "table",
    "evidence_location_key": "data_zone",
    "answer_mechanism_key": "data_synthesis",
    "solver_pattern_key": "read_graphic_then_match_claim",
    "stimulus_mode_key": "prose_plus_table",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "topic_broad": "science",
    "topic_fine": "pollination ecology",
    "reading_scope": "passage-plus-data",
    "reasoning_demand": "general-claim verification across full dataset",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "low",
    "distractor_strength": "high",
    "classification_rationale": "Per V1 §13.2, this item is `data_supports_claim` because the correct option must validate Patel's general preference claim. Sub-focus is `data_comparison` because the claim cannot be verified from a single value or single pair."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "purple coneflower received an average of 14.3 B. impatiens visits per hour over the bloom season.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "data_context_mismatch",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "data_supports_claim",
      "why_plausible": "Cites the single highest value, which feels like strong supporting evidence.",
      "why_wrong": "A single absolute value cannot support a comparative claim about native vs. introduced species.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "red clover, an introduced species, received an average of 7.9 visits per hour, more than oxeye daisy at 6.2.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "data_context_mismatch",
      "plausibility_source_key": "topical_proximity",
      "option_error_focus_key": "data_supports_claim",
      "why_plausible": "Performs a real numerical comparison and references native/introduced labeling.",
      "why_wrong": "Compares two introduced species to each other; tells us nothing about whether native species are preferred over introduced ones.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "each of the two native species received more B. impatiens visits per hour than either of the two introduced species.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "plausibility_source_key": null,
      "why_plausible": "Spans the entire dataset; every native > every introduced — exactly what Patel's general preference claim requires.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "purple coneflower, a native species, received nearly twice as many visits per hour as oxeye daisy, an introduced species.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "partial_match",
      "plausibility_source_key": "partial_truth",
      "option_error_focus_key": "data_supports_claim",
      "why_plausible": "Numerically accurate (14.3 vs. 6.2) and crosses the native/introduced boundary, so it feels supportive.",
      "why_wrong": "A single native-vs-introduced pair does not establish a general preference. The claim requires that every native exceed every introduced, which D does not show.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2
    }
  ],
  "reasoning": {
    "primary_rule": "Quantitative evidence must match the scope of the claim; a general preference claim requires a comparison spanning the entire relevant dataset.",
    "trap_mechanism": "D is the maximum-strength trap because it crosses the native/introduced boundary and is numerically accurate, but it generalizes from a single pair rather than from the full 2×2 contrast.",
    "correct_answer_reasoning": "C names the universal-quantifier comparison: every native > every introduced.",
    "distractor_analysis_summary": "A is a single value (no comparison); B compares within the introduced group; D establishes only one pair, not the general pattern."
  },
  "generation_profile": {
    "target_skill_family_key": "command_of_evidence_quantitative",
    "target_reading_focus_key": "data_supports_claim",
    "target_reasoning_trap_key": "single_sector_focus",
    "target_stimulus_mode_key": "prose_plus_table",
    "target_stem_type_key": "choose_best_completion_from_data",
    "distractor_pattern": [
      "single absolute value with no comparison",
      "comparison within the wrong subgroup (introduced vs. introduced)",
      "single cross-group pair masquerading as a general pattern"
    ],
    "passage_structure_pattern": "research_summary",
    "passage_template": "[Researcher] argues that [subject] preferentially [does X] across [native vs. introduced / treated vs. untreated / etc.]. To support this claim, [researcher] cites data showing that ______",
    "generation_timestamp": "2026-04-25T00:00:00Z",
    "model_version": "rules_agent_reading_v1.0"
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "D is precision_score 2; it performs a real cross-group comparison but is scope-deficient relative to the claim. C is the only option whose scope matches the claim's scope."
  }
}
```

---

## Question 3 — Text Structure and Purpose: Sentence Function (V1 rules)

*Modeled on PT4 M1 Q8 (mimosa / B. terrenus, third-sentence function). Pushed harder by making the underlined sentence a **pivot** that simultaneously closes the framing of sentence 1 and opens the contrary finding of sentence 4 — three of the distractors describe rhetorical moves that are happening elsewhere in the passage.*

**Passage**

The Tyrrhenian flora — the assemblage of plant species native to Sardinia, Corsica, and the smaller islands of the western Mediterranean — has long been characterized as a botanical relict, the surviving remnant of vegetation once continuous across southern Europe before late-Cenozoic climatic shifts fragmented its range. Botanists Marco Conti and Sofia Rinaldi recently sequenced chloroplast DNA from 142 endemic species across the archipelago. **Their results suggested a far more recent evolutionary timeline than the relict hypothesis predicts.** Many of the supposedly ancient endemics, the data revealed, diverged from continental European populations within the past two million years — long after the supposed continuous distribution would have already fragmented.

**Which choice best describes the function of the underlined sentence in the text as a whole?**

- A) It restates the relict hypothesis introduced in the first sentence and clarifies its central prediction.
- B) It introduces a finding that complicates the framing established in the opening of the text.
- C) It supplies the methodological basis for the study described in the previous sentence.
- D) It anticipates an objection that the closing sentence then resolves in favor of the relict hypothesis.

**Correct answer:** B

### V1 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 3,
    "stimulus_mode_key": "prose_single",
    "stem_type_key": "choose_sentence_function",
    "prompt_text": "Which choice best describes the function of the underlined sentence in the text as a whole?",
    "correct_option_label": "B",
    "explanation_short": "The underlined sentence pivots the passage from the relict-hypothesis framing to the finding that contradicts it.",
    "explanation_full": "The passage opens by characterizing Tyrrhenian flora as a 'botanical relict' (sentence 1). Sentence 2 introduces Conti and Rinaldi's chloroplast-DNA study. The underlined sentence reports the headline result: a 'far more recent evolutionary timeline than the relict hypothesis predicts.' The closing sentence elaborates the finding (divergence within the past two million years). The underlined sentence's function is therefore to introduce a finding that complicates the opening framing — option B. A reverses direction (the sentence does not restate the relict hypothesis; it begins to undermine it). C misidentifies the sentence's content (methodology was given in sentence 2: 'sequenced chloroplast DNA from 142 endemic species'). D invents a resolution-in-favor-of-the-relict-hypothesis that the closing sentence does not provide; the closing sentence reinforces the contrary finding.",
    "evidence_span_text": "Their results suggested a far more recent evolutionary timeline than the relict hypothesis predicts."
  },
  "classification": {
    "domain": "Craft and Structure",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "text_structure_and_purpose",
    "reading_focus_key": "sentence_function",
    "secondary_reading_focus_keys": ["structural_pattern"],
    "reasoning_trap_key": "wrong_action_verb",
    "evidence_scope_key": "passage",
    "evidence_location_key": "transition_zone",
    "answer_mechanism_key": "rhetorical_classification",
    "solver_pattern_key": "classify_rhetorical_move",
    "stimulus_mode_key": "prose_single",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "topic_broad": "science",
    "topic_fine": "biogeography / plant evolution",
    "reading_scope": "passage-level",
    "reasoning_demand": "rhetorical-move classification with three plausible alternative moves",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "medium",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "classification_rationale": "The underlined sentence is the pivot from framing to contrary finding. The correct rhetorical verb is 'introduces' (a finding that complicates), per V1 §13.6 approved verbs."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "It restates the relict hypothesis introduced in the first sentence and clarifies its central prediction.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "wrong_action_verb",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "sentence_function",
      "why_plausible": "The sentence does mention the relict hypothesis by name, which can prime 'restates.'",
      "why_wrong": "The sentence reports a finding that contradicts the hypothesis; it does not restate or clarify the hypothesis.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "It introduces a finding that complicates the framing established in the opening of the text.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "plausibility_source_key": null,
      "why_plausible": "Names the pivot rhetorical move precisely: 'introduces a finding' that 'complicates' the opening framing.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "It supplies the methodological basis for the study described in the previous sentence.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "wrong_action_verb",
      "plausibility_source_key": "rhetorical_surface_similarity",
      "option_error_focus_key": "sentence_function",
      "why_plausible": "Research-summary passages often have a methodology sentence; this one feels like the right slot.",
      "why_wrong": "The methodology was already given in the previous sentence ('sequenced chloroplast DNA from 142 endemic species'). The underlined sentence reports results, not method.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "It anticipates an objection that the closing sentence then resolves in favor of the relict hypothesis.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "contradiction",
      "plausibility_source_key": "rhetorical_surface_similarity",
      "option_error_focus_key": "sentence_function",
      "why_plausible": "Anticipate-then-resolve is a recognizable academic structure that sounds sophisticated.",
      "why_wrong": "The closing sentence does not resolve in favor of the relict hypothesis; it reinforces the contrary finding ('long after the supposed continuous distribution would have already fragmented').",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Sentence-function items are decided by extracting the rhetorical action verb (per V1 §13.6) and confirming it matches the underlined sentence's role in the passage's logical flow.",
    "trap_mechanism": "Three plausible rhetorical moves are present in the passage (framing, methodology, finding); only one belongs to the underlined sentence.",
    "correct_answer_reasoning": "Sentence 1 frames; sentence 2 describes method; underlined sentence reports the headline result that complicates the framing; sentence 4 elaborates that result. The underlined sentence's verb is 'introduces (a finding that complicates).'",
    "distractor_analysis_summary": "A reverses direction; C misattributes methodology; D fabricates a resolution that the passage does not deliver."
  },
  "generation_profile": {
    "target_skill_family_key": "text_structure_and_purpose",
    "target_reading_focus_key": "sentence_function",
    "target_reasoning_trap_key": "wrong_action_verb",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "choose_sentence_function",
    "distractor_pattern": [
      "verb that reverses the direction of the move (restate vs. complicate)",
      "verb describing a different sentence's role (methodology vs. results)",
      "verb invoking a structure the passage does not actually realize (anticipate-and-resolve)"
    ],
    "passage_structure_pattern": "claim_evidence_explanation",
    "passage_template": "[Established framing claim]. [Researchers] [methodology]. **[Underlined: headline finding that contradicts the framing].** [Elaboration of finding].",
    "generation_timestamp": "2026-04-25T00:00:00Z",
    "model_version": "rules_agent_reading_v1.0"
  },
  "review": {
    "annotation_confidence": 0.91,
    "needs_human_review": false,
    "review_notes": "rhetorical_verb = 'to introduce (a finding that complicates).' Passage structure pattern: claim_evidence_explanation with the explanation contradicting the opening claim — a high-difficulty variant of research_summary."
  }
}
```

---

## Question 4 — SEC: Paired-dash appositive (V3 rules)

*Modeled on PT4 M1 Q23 (sampler/stacks) and Q26 (single-handedly, however). Pushed harder by making the **opening dash invisible to surface scanning** — students looking only at the blank can't tell a dash is required unless they read backward to find the matching opener.*

**Passage**

The supposed link between dietary saturated fat and cardiovascular disease ______ a hypothesis that dominated American nutritional science from the 1960s through the 1990s and shaped a generation of public-health guidelines — has been challenged repeatedly in the past decade by meta-analyses that find no consistent association between saturated-fat intake and coronary risk.

**Which choice completes the text so that it conforms to the conventions of Standard English?**

- A) disease,
- B) disease;
- C) disease —
- D) disease:

**Correct answer:** C

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 4,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "correct_option_label": "C",
    "explanation_short": "An em-dash later in the sentence closes a parenthetical appositive; the punctuation at the blank must be a matching em-dash that opens it.",
    "explanation_full": "The sentence has a parenthetical appositive ('a hypothesis that dominated American nutritional science … guidelines') that renames 'the supposed link.' That appositive ends with an em-dash before 'has been challenged.' Standard English requires that paired parenthetical punctuation be symmetrical: dash–dash, comma–comma, or parentheses–parentheses. Because the closing mark is fixed as a dash, the opening mark must also be a dash. C is correct. A (comma) would mismatch the closing dash and create asymmetric parenthetical punctuation. B (semicolon) would create a fragment — the material before the blank is not an independent clause, since the verb 'has been challenged' belongs to the main subject 'link.' D (colon) is wrong for the same reason as B: a colon must follow an independent clause, but the words before the blank do not form one.",
    "evidence_span_text": "link ... — a hypothesis ... guidelines — has been challenged"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Punctuation",
    "subskill": "paired-dash parenthetical appositive — opening mark must match closing mark",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "colon_dash_use",
    "secondary_grammar_focus_keys": ["appositive_punctuation", "sentence_boundary"],
    "syntactic_trap_key": "interruption_breaks_subject_verb",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "eliminate_by_boundary",
    "topic_broad": "science",
    "topic_fine": "nutritional epidemiology",
    "reading_scope": "sentence-level",
    "reasoning_demand": "paired-punctuation symmetry plus subject-verb integrity check",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "appositive_punctuation > general punctuation",
    "classification_rationale": "Two rules apply: (i) paired parenthetical punctuation must match, and (ii) the spine of the sentence must remain a single independent clause. Both rules pick the dash."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "disease,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "appositive_punctuation",
      "why_plausible": "A comma is the default mark for opening a nonrestrictive appositive.",
      "why_wrong": "The closing mark is a dash; paired parenthetical punctuation must match. A comma–dash pair is not standard.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "disease;",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "semicolon_use",
      "why_plausible": "A semicolon looks formal and might seem to mark a major break.",
      "why_wrong": "A semicolon must join two independent clauses; the words before the blank ('The supposed link between dietary saturated fat and cardiovascular disease') are a noun phrase, not an independent clause.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "disease —",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "plausibility_source_key": null,
      "why_plausible": "Matches the closing em-dash, producing the required symmetric parenthetical punctuation around the appositive.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "disease:",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "colon_dash_use",
      "why_plausible": "A colon is an acceptable mark to introduce an appositive elaboration in some contexts.",
      "why_wrong": "A colon must follow an independent clause, and the words before the blank do not form one. A colon also does not pair with a closing dash.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Paired parenthetical punctuation must be symmetrical; in addition, the punctuation must not break a noun phrase from its main verb.",
    "trap_mechanism": "Students who scan only the blank without reading backward to confirm the closing mark default to comma (A) or semicolon (B) and never notice the closing dash that forces the answer.",
    "correct_answer_reasoning": "The closing em-dash before 'has been challenged' is fixed; symmetry requires an opening em-dash. The dash also preserves 'link … has been challenged' as the sentence's main subject-verb spine.",
    "distractor_analysis_summary": "A breaks symmetry; B and D each fail the independent-clause requirement and also break symmetry."
  },
  "generation_profile": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "colon_dash_use",
    "target_syntactic_trap_key": "interruption_breaks_subject_verb",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "comma that breaks paired-mark symmetry",
      "semicolon that requires an independent clause that does not exist",
      "colon that requires an independent clause that does not exist"
    ],
    "passage_template": "[Noun phrase subject] ______ [parenthetical appositive renaming the subject] — [main verb of the subject] ...",
    "generation_timestamp": "2026-04-25T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Two-rule item: paired-mark symmetry plus independent-clause requirement. Both rules independently select C. The trap is failing to scan past the blank to find the closing dash."
  }
}
```

---

## Answer Key

| # | Domain | Skill | Correct | Trap key |
|---|---|---|---|---|
| 1 | Craft and Structure | Cross-Text Connections | C | `confirmed_when_contradicted` |
| 2 | Information and Ideas | Command of Evidence — Quantitative | C | `single_sector_focus` |
| 3 | Craft and Structure | Text Structure and Purpose (sentence function) | B | `wrong_action_verb` |
| 4 | Standard English Conventions | Punctuation (`colon_dash_use`) | C | `interruption_breaks_subject_verb` |

## How both rule sets are honored

Per the V1 reading rules: items 1, 2, and 3 carry `grammar_role_key: null` and `grammar_focus_key: null` (V1 §1.5 domain isolation, §18 forbidden patterns). Item 1 uses `prose_paired` per V1 §3.1 Cross-Text mandate; item 2 uses `prose_plus_table` with populated `table_data` per V1 §13.2; item 3 uses the V1 §13.6 rhetorical-verb classification. Per V1 §13.7, the response stem in item 1 is treated as disagreement-oriented — the correct option captures methodological challenge, not endorsement.

Per the V3 grammar rules: item 4 carries fully populated `grammar_role_key`, `grammar_focus_key`, `secondary_grammar_focus_keys`, `syntactic_trap_key`, and `disambiguation_rule_applied` per V3 §17.1, §17.3, §17.7, and §17.8. The distractor pattern follows the V3 §20.4 `colon_dash_use` heuristic table.

Per shared difficulty calibration (V3 §17.12, V1 §14.2): every item is `difficulty_overall: high` because at least one distractor is `precision_score: 2` (a defensible reading outperformed only on specificity or directness — see option A in Q1 and option D in Q2).
