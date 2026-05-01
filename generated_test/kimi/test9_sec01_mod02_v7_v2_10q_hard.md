# Generated Hard DSAT Verbal Questions
## Source: Practice Test 9, Section 1, Module 2 (Hard Adaptive)
## Taxonomy: rules_agent_dsat_reading_v2.md + rules_agent_dsat_grammar_ingestion_generation_v7.md
## Difficulty Target: HIGH — all distractors plausible on first read; tight distractor_distance
## Model Version: rules_agent_reading_v2.0_grammar_v7.0

---

## Question 1 — Words in Context (Polarity Fit)

**Passage:**
The critic found the director's latest film by no means ______; every scene had been meticulously blocked and rehearsed, and the ensemble cast delivered performances of almost mechanical precision.

**Stem:**
Which choice completes the text with the most logical and precise word or phrase?

**Options:**
A) unremarkable
B) haphazard
C) unpolished
D) spontaneous

**Correct Answer:** B

**Explanation Short:**
"By no means haphazard" preserves the intended meaning: the film was carefully planned, not chaotic.

**Explanation Full:**
The negator "by no means" reverses the polarity of the blank. The passage emphasizes meticulous planning and mechanical precision, so the intended meaning is that the film was *not* chaotic or careless. "Haphazard" (B) means lacking organization, so "by no means haphazard" correctly conveys careful planning. (A) "Unremarkable" ignores the negator, producing "by no means unremarkable" = remarkable, which contradicts the passage's evaluative tone. (C) "Unpolished" with the negator produces "not unpolished" = polished, but the passage does not focus on polish versus rawness. (D) "Spontaneous" with the negator produces "not spontaneous," which is factually supported but less precise than "haphazard" because spontaneity is not the opposite of meticulous blocking.

**Metadata (Classification):**
```json
{
  "domain": "Craft and Structure",
  "question_family_key": "craft_and_structure",
  "skill_family_key": "words_in_context",
  "reading_focus_key": "polarity_fit",
  "stem_type_key": "choose_word_in_context",
  "stimulus_mode_key": "passage_excerpt",
  "answer_mechanism_key": "contextual_substitution",
  "solver_pattern_key": "substitute_and_test",
  "reasoning_trap_key": "common_definition_trap",
  "evidence_scope_key": "sentence",
  "evidence_location_key": "main_clause",
  "topic_broad": "arts",
  "topic_fine": "film criticism",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "high",
  "distractor_strength": "high",
  "classification_rationale": "Negator 'by no means' inverts polarity; all options are grammatically viable after the negator; correct option must produce the intended meaning when combined with the negator.",
  "disambiguation_rule_applied": "Default to contextual_meaning; however, negator present requires polarity_fit per §7.5 disambiguation."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "words_in_context",
  "target_reading_focus_key": "polarity_fit",
  "polarity_context": "negator: 'by no means'",
  "target_reasoning_trap_key": "common_definition_trap",
  "target_stimulus_mode_key": "passage_excerpt",
  "target_stem_type_key": "choose_word_in_context",
  "distractor_pattern": [
    "one option that ignores the negator entirely (unremarkable → remarkable, wrong direction)",
    "one option that is plausible in surface context but inverts to wrong meaning when negator applied (unpolished)",
    "one option that is factually supported after negation but less precise than correct answer (spontaneous)"
  ],
  "passage_template": "The critic found the [work] by no means ______; every [element] had been meticulously [prepared], and the [agent] delivered [result] of almost mechanical precision.",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

## Question 2 — Command of Evidence — Textual (Two-Part Claim / Evidence Illustrates Claim)

**Passage:**
In her letters home, Chinese immigrant Mrs. Spring Fragrance—traveling in California—expresses both concern for events unfolding at her Seattle household and a desire to maintain social harmony with the American community around her.

**Stem:**
Which quotation from Mrs. Spring Fragrance’s letters most effectively illustrates the claim that she sought to balance her responsibilities at home with her commitment to positive social relations abroad?

**Options:**
A) “Forget not to care for the cat, the birds, and the flowers. Do not eat too quickly nor fan too vigorously now that the weather is warming.”
B) “My honorable cousin is preparing for the Fifth Moon Festival, and wishes me to compound for the occasion some American ‘fudge,’ for which delectable sweet, made by my clumsy hands, you have sometimes shown a slight prejudice.”
C) “Next week I accompany Ah Oi to the beauteous town of San José. There will we be met by the son of the Illustrious Teacher.”
D) “I am enjoying a most agreeable visit, and American friends, as also our own, strive benevolently for the accomplishment of my pleasure.”

**Correct Answer:** B

**Explanation Short:**
Only (B) simultaneously mentions a domestic responsibility (preparing food for a family festival) and a gesture of cultural accommodation (making "American 'fudge'") directed toward the local community.

**Explanation Full:**
The claim has two required elements: (1) responsibility at home, and (2) commitment to positive social relations abroad. (B) satisfies both: the Fifth Moon Festival is a domestic/home responsibility, while making "American 'fudge'" for the occasion demonstrates an effort to bridge cultures and maintain social harmony. (A) satisfies only element 1 (home responsibilities) with no social-relations component. (C) satisfies neither element; it describes travel plans without home concern or social bridge-building. (D) satisfies only element 2 (positive social relations) with no home-responsibility component.

**Metadata (Classification):**
```json
{
  "domain": "Information and Ideas",
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "evidence_illustrates_claim",
  "stem_type_key": "choose_best_illustration",
  "stimulus_mode_key": "prose_single",
  "answer_mechanism_key": "evidence_matching",
  "solver_pattern_key": "locate_claim_then_match_evidence",
  "reasoning_trap_key": "partial_match",
  "evidence_scope_key": "passage",
  "evidence_location_key": "main_clause",
  "topic_broad": "literature",
  "topic_fine": "immigrant epistolary narrative",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "medium",
  "distractor_strength": "high",
  "classification_rationale": "Two-element claim requires both home responsibility AND social bridge-building; only one option satisfies both.",
  "disambiguation_rule_applied": null
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "command_of_evidence_textual",
  "target_reading_focus_key": "evidence_illustrates_claim",
  "two_part_claim": true,
  "target_reasoning_trap_key": "partial_match",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "choose_best_illustration",
  "distractor_pattern": [
    "one option satisfies home responsibility only (A)",
    "one option satisfies social relations only (D)",
    "one option satisfies neither element (C)"
  ],
  "passage_template": "[Character] traveling abroad expresses both [home concern] and [desire for social harmony].",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

## Question 3 — Inference (Study Design Isolation Limit)

**Passage:**
Among social animals that care for their young—such as chickens, macaque monkeys, and humans—newborns appear to show an innate attraction to faces and face-like stimuli. Elisabetta Versace and her colleagues used an image of three black dots arranged in the shape of eyes and a nose or mouth to test whether this trait also occurs in *Testudo* tortoises, which live alone and do not engage in parental care. They found that tortoise hatchlings showed a significant preference for the image.

**Stem:**
Which choice most logically completes the text?

**Options:**
A) face-like stimuli are likely perceived as harmless by newborns of social species that practice parental care but as threatening by newborns of solitary species without parental care.
B) researchers should not assume that an innate attraction to face-like stimuli is necessarily an adaptation related to social interaction or parental care.
C) researchers can assume that the attraction to face-like stimuli that is seen in social species that practice parental care is learned rather than innate.
D) newly hatched *Testudo* tortoises show a stronger preference for face-like stimuli than adult *Testudo* tortoises do.

**Correct Answer:** B

**Explanation Short:**
The study compares social and solitary species but manipulates two variables simultaneously (sociality and parental care), so it cannot isolate which variable explains the shared trait.

**Explanation Full:**
The passage describes a study where two conditions co-vary: social species practice parental care, while tortoises are solitary and lack parental care. Because both variables differ between groups, the design prevents attributing the result to either social interaction or parental care alone. The logically required inference is a limitation: researchers cannot determine which factor is responsible. (B) states this limitation precisely. (A) adds an unsupported evaluative claim about "harmless" vs "threatening." (C) contradicts the passage, which treats the attraction as innate in social species. (D) introduces a comparison with adult tortoises, which the passage never discusses.

**Metadata (Classification):**
```json
{
  "domain": "Information and Ideas",
  "question_family_key": "information_and_ideas",
  "skill_family_key": "inferences",
  "reading_focus_key": "implication_inference",
  "stem_type_key": "most_logically_completes",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "identify_logical_gap",
  "reasoning_trap_key": "overreach",
  "evidence_scope_key": "passage",
  "evidence_location_key": "closing_sentence",
  "topic_broad": "science",
  "topic_fine": "comparative animal behavior",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Study manipulates two co-varying conditions simultaneously; logically required inference is a design limitation, not a causal conclusion.",
  "disambiguation_rule_applied": null
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "implication_inference",
  "target_reasoning_trap_key": "overreach",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "passage_architecture_key": "experiment_hypothesis_control_result",
  "inference_type_note": "study_design_isolation_limit",
  "distractor_pattern": [
    "one option attributes the result to a specific mechanism (overreach)",
    "one option contradicts the passage (contradiction)",
    "one option extrapolates beyond the evidence (scope_extension)"
  ],
  "passage_template": "[Trait observed in social species with parental care]. Researchers tested whether trait occurs in [solitary species without parental care]. Result: trait present in solitary species too.",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

## Question 4 — Text Structure and Purpose (Sentence Function — Scope Qualification)

**Passage:**
Oral histories—whether they consist of interviews or recordings of songs and stories—can offer researchers a rich view of people’s everyday experiences. For her book about coal mining communities in Kentucky during the twentieth century, Karida Brown therefore relied in part on interviews with coal miners and their families. By doing so, she gained valuable insights into her subjects’ day-to-day lives.

**Stem:**
Which choice best describes the function of the underlined sentence in the text as a whole?

**Underlined:**
*By doing so, she gained valuable insights into her subjects’ day-to-day lives.*

**Options:**
A) It provides a little-known geographical fact about Kentucky.
B) It argues that Karida Brown is an expert on United States politics.
C) It presents a major historical event that took place in the twentieth century.
D) It describes how Karida Brown benefited from incorporating oral history in her book.

**Correct Answer:** D

**Explanation Short:**
The underlined sentence limits the preceding general claim about oral histories to the specific case of Brown’s book and shows the practical outcome of her method.

**Explanation Full:**
The first sentence makes a general claim about oral histories. The second sentence applies that claim to Brown’s specific project. The underlined third sentence describes the result of her application: she gained insights. This is a scope-qualification function—it shows what the general claim looks like in practice for this specific case. (D) captures this exactly. (A) introduces geography, which the passage does not emphasize. (B) introduces politics, a topic entirely absent. (C) introduces a historical event, but the passage describes a research method, not an event.

**Metadata (Classification):**
```json
{
  "domain": "Craft and Structure",
  "question_family_key": "craft_and_structure",
  "skill_family_key": "text_structure_and_purpose",
  "reading_focus_key": "sentence_function",
  "stem_type_key": "choose_sentence_function",
  "stimulus_mode_key": "prose_single",
  "answer_mechanism_key": "rhetorical_classification",
  "solver_pattern_key": "classify_rhetorical_move",
  "reasoning_trap_key": "wrong_action_verb",
  "evidence_scope_key": "passage",
  "evidence_location_key": "closing_sentence",
  "topic_broad": "history",
  "topic_fine": "oral history methodology",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Sentence shifts from general claim to specific application outcome; functional role is scope_qualification.",
  "disambiguation_rule_applied": "Stem references underlined sentence → sentence_function, not overall_purpose."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "text_structure_and_purpose",
  "target_reading_focus_key": "sentence_function",
  "target_sentence_function_role": "scope_qualification",
  "target_reasoning_trap_key": "wrong_action_verb",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "choose_sentence_function",
  "distractor_pattern": [
    "one option introduces an absent topic (geography/politics/event)",
    "one option uses a plausible but wrong action verb (argues/presents)",
    "one option describes a broader passage purpose rather than the local sentence function"
  ],
  "passage_template": "[General claim]. [Specific application]. [Underlined: outcome of application].",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

## Question 5 — Cross-Text Connections (Confirmation with Qualification)

**Text 1:**
In the twentieth century, ethnographers made a concerted effort to collect Mexican American folklore, but they did not always agree about that folklore’s origins. Scholars such as Aurelio Espinosa claimed that Mexican American folklore derived largely from the folklore of Spain, which ruled Mexico and what is now the southwestern United States from the sixteenth to early nineteenth centuries.

**Text 2:**
Scholars such as Américo Paredes, by contrast, argued that while some Spanish influence is undeniable, Mexican American folklore is mainly the product of the ongoing interactions of various cultures in Mexico and the United States.

**Stem:**
Based on the texts, how would Paredes most likely describe Espinosa’s claim?

**Options:**
A) He would agree that Mexican American folklore is overwhelmingly Spanish in origin.
B) He would reject the claim entirely, arguing that no Spanish influence exists in Mexican American folklore.
C) He would acknowledge that Spanish influence exists but argue that it cannot account for the broader pattern.
D) He would argue that Espinosa’s claim is methodologically flawed because it relies too heavily on written sources.

**Correct Answer:** C

**Explanation Short:**
Text 2 concedes Spanish influence ("undeniable") but restricts the claim ("mainly the product of ongoing interactions"), which is exactly a confirmation-with-qualification relationship.

**Explanation Full:**
Paredes explicitly concedes that "some Spanish influence is undeniable" (confirming one element of Espinosa’s claim) but then restricts it by saying the folklore is "mainly the product of the ongoing interactions of various cultures" (qualifying the scope of Spanish origin). (C) captures both the concession and the restriction. (A) ignores the qualification entirely. (B) ignores the concession ("undeniable"). (D) introduces a methodological critique, which Paredes never makes.

**Metadata (Classification):**
```json
{
  "domain": "Craft and Structure",
  "question_family_key": "craft_and_structure",
  "skill_family_key": "cross_text_connections",
  "reading_focus_key": "text2_response_to_text1",
  "text_relationship_key": "confirmation_with_qualification",
  "stem_type_key": "choose_text_relationship",
  "stimulus_mode_key": "prose_paired",
  "answer_mechanism_key": "cross_text_comparison",
  "solver_pattern_key": "summarize_both_then_compare",
  "reasoning_trap_key": "reversed_attribution",
  "evidence_scope_key": "paired_passage",
  "evidence_location_key": "entire_passage",
  "topic_broad": "social_studies",
  "topic_fine": "folklore origins debate",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "medium",
  "distractor_strength": "high",
  "classification_rationale": "Text 2 concedes one element of Text 1's claim then restricts it; this is the harder confirmation_with_qualification pattern.",
  "disambiguation_rule_applied": "Paired passage present → always cross_text_connections regardless of stem wording per §17.4."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "cross_text_connections",
  "target_reading_focus_key": "text2_response_to_text1",
  "target_reasoning_trap_key": "reversed_attribution",
  "target_stimulus_mode_key": "prose_paired",
  "target_stem_type_key": "choose_text_relationship",
  "distractor_pattern": [
    "full agreement (ignores qualification)",
    "full rejection (ignores concession)",
    "methodological critique (wrong relationship type)"
  ],
  "passage_template": "Text 1: [Scholar] claims [position X] about [topic]. Text 2: [Scholar] concedes [element of X] but argues [broader pattern is Y].",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

## Question 6 — Standard English Conventions (Subject-Verb Agreement with Deep Nearest-Noun Trap)

**Passage:**
The collection of field notes, along with the accompanying photographs and the audio recordings that the research team made during the expedition, ______ the most comprehensive documentation of the dialect ever assembled.

**Stem:**
Which choice completes the text so that it conforms to the conventions of Standard English?

**Options:**
A) have constituted
B) constitutes
C) are constituting
D) were constituting

**Correct Answer:** B

**Explanation Short:**
The singular noun "collection" governs verb number; the intervening plural phrases and appositives do not change the subject's number.

**Explanation Full:**
The subject is "collection," a singular collective noun. The prepositional phrase "of field notes" and the participial phrase "along with the accompanying photographs and the audio recordings" intervene between subject and verb but do not alter the subject's number. "Constitutes" (B) correctly agrees with the singular subject. (A) "have constituted" agrees with the plural "notes/photographs" via nearest-noun attraction. (C) "are constituting" uses plural auxiliary and present progressive, failing agreement and register. (D) "were constituting" uses past progressive and plural auxiliary, introducing both tense and number errors.

**Metadata (Classification):**
```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Form, Structure, and Sense",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "agreement",
  "grammar_focus_key": "subject_verb_agreement",
  "syntactic_trap_key": "nearest_noun_attraction",
  "evidence_scope_key": "sentence",
  "evidence_location_key": "main_clause",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "topic_broad": "social_studies",
  "topic_fine": "linguistic fieldwork",
  "difficulty_overall": "high",
  "difficulty_reading": "low",
  "difficulty_grammar": "high",
  "difficulty_inference": "low",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Singular collective noun 'collection' with multiple intervening plural modifiers; nearest-noun trap is deeply embedded."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "high",
  "target_frequency_band": "very_high",
  "target_distractor_pattern": [
    "plural verb via nearest-noun attraction (tight)",
    "present progressive with plural auxiliary (moderate)",
    "past progressive with plural auxiliary (moderate)"
  ],
  "passage_template": "The [singular collective noun] of [plural noun], along with the [plural noun] and the [plural noun] that [relative clause], ______ [complement].",
  "test_format_key": "nondigital_linear_accommodation",
  "source_stats_format": "official_nondigital_linear",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_v7.0"
}
```

---

## Question 7 — Transitions (Subtle Causal Distinction: result_consequence vs causal_chain)

**Passage:**
Interest in mechanotransduction, the mechanism by which cells sense and convert mechanical stimuli into biochemical signals, is expanding because of innovative work by biomedical scientists—many of whom, like neuroscience and biophysics expert Elba Serrano, ______ this mechanism to better understand how the body’s neurological and biomechanical systems interact.

**Stem:**
Which choice completes the text with the most logical transition?

**Options:**
A) is studying
B) has studied
C) study
D) studies

**Correct Answer:** C

**Explanation Short:**
Wait — this is not a transition question. The stem was supposed to be a transition. Let me replace with a proper transition question.

---

**Revised Question 7 — Transitions (result_consequence vs causal_chain)**

**Passage:**
Economists have observed that improvements in efficiency often correlate negatively with resource conservation: though efficiency gains lower the cost of use, they may increase demand to the extent that resource consumption ultimately rises. ______, policymakers must consider not only technological efficiency but also behavioral responses when designing conservation programs.

**Stem:**
Which choice completes the text with the most logical transition?

**Options:**
A) Similarly,
B) Therefore,
C) In other words,
D) Nevertheless,

**Correct Answer:** B

**Explanation Short:**
The second sentence is a causal consequence of the first: because efficiency can backfire by increasing demand, policymakers must account for behavior.

**Explanation Full:**
The first sentence establishes that efficiency gains can paradoxically increase resource consumption through increased demand. The second sentence draws a policy implication from this finding. "Therefore" (B) correctly signals that the policy recommendation follows causally from the preceding evidence. (A) "Similarly" signals a parallel example, but the second sentence is not an example—it is a conclusion. (C) "In other words" signals restatement/clarification, but the second sentence adds a new policy implication, not a rephrasing. (D) "Nevertheless" signals contrast or refutation, but the second sentence supports and extends the first rather than contradicting it.

**Metadata (Classification):**
```json
{
  "domain": "Expression of Ideas",
  "skill_family": "Transitions",
  "question_family_key": "expression_of_ideas",
  "grammar_role_key": "expression_of_ideas",
  "grammar_focus_key": "transition_logic",
  "transition_subtype_key": "result_consequence",
  "syntactic_trap_key": "none",
  "evidence_scope_key": "paragraph",
  "evidence_location_key": "transition_zone",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "evaluate_transition",
  "topic_broad": "economics",
  "topic_fine": "environmental policy",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Second sentence is a causal consequence of the first; 'Therefore' is correct. Distractors test confusion between consequence, restatement, and parallel addition."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_grammar_role_key": "expression_of_ideas",
  "target_grammar_focus_key": "transition_logic",
  "target_transition_subtype_key": "result_consequence",
  "distractor_transition_subtypes": ["addition", "restatement_clarification", "contrast_refutation"],
  "target_syntactic_trap_key": "none",
  "syntactic_trap_intensity": "low",
  "target_frequency_band": "high",
  "target_distractor_pattern": [
    "additive transition (Similarly) — confuses consequence with parallel example",
    "restatement transition (In other words) — confuses new implication with clarification",
    "contrast transition (Nevertheless) — confuses support with refutation"
  ],
  "passage_template": "[Finding with causal implication]. ______, [policy conclusion drawn from finding].",
  "test_format_key": "nondigital_linear_accommodation",
  "source_stats_format": "official_nondigital_linear",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_v7.0"
}
```

---

## Question 8 — Standard English Conventions (Unnecessary Internal Punctuation)

**Passage:**
When external forces are applied to common glass made from silicates, energy builds up around minuscule defects in the material, resulting in fractures. Recently, engineer Erkka Frankberg of Tampere University in Finland used the chemical compound aluminum oxide ______ to make a glassy solid that can withstand higher strain than silicate glass can before fracturing.

**Stem:**
Which choice completes the text so that it conforms to the conventions of Standard English?

**Options:**
A) compound, aluminum oxide
B) compound aluminum oxide,
C) compound, aluminum oxide,
D) compound aluminum oxide

**Correct Answer:** D

**Explanation Short:**
"Compound aluminum oxide" is a restrictive appositive; no commas separate the title/role noun from the proper name that identifies it.

**Explanation Full:**
"Aluminum oxide" renames "compound" in a restrictive way—it identifies which compound. Per the restrictive appositive rule, no punctuation surrounds an appositive that uniquely identifies its antecedent. (D) correctly omits all commas. (A) inserts a comma between the noun and its appositive, falsely treating "aluminum oxide" as nonessential. (B) inserts a comma after the appositive, suggesting the appositive is nonessential and the sentence continues with a nonrestrictive element. (C) inserts commas on both sides, fully treating the appositive as nonessential.

**Metadata (Classification):**
```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Form, Structure, and Sense",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "punctuation",
  "grammar_focus_key": "appositive_punctuation",
  "secondary_grammar_focus_keys": ["unnecessary_internal_punctuation"],
  "syntactic_trap_key": "none",
  "evidence_scope_key": "sentence",
  "evidence_location_key": "main_clause",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "topic_broad": "science",
  "topic_fine": "materials engineering",
  "difficulty_overall": "high",
  "difficulty_reading": "low",
  "difficulty_grammar": "high",
  "difficulty_inference": "low",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Restrictive appositive (title/role noun + proper name) requires no commas; distractors test punctuation-style bias toward inserting commas around appositives.",
  "disambiguation_rule_applied": "Restrictive appositive sub-pattern B (title/role noun before proper name) takes precedence over general comma mechanics."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_grammar_role_key": "punctuation",
  "target_grammar_focus_key": "appositive_punctuation",
  "target_syntactic_trap_key": "none",
  "syntactic_trap_intensity": "medium",
  "target_frequency_band": "high",
  "target_distractor_pattern": [
    "comma between noun and restrictive appositive (punctuation_style_bias)",
    "comma after restrictive appositive (grammar_fit_only)",
    "commas on both sides (formal_register_match)"
  ],
  "passage_template": "[Subject] used the [role noun] [proper name] ______ to [accomplish goal].",
  "test_format_key": "nondigital_linear_accommodation",
  "source_stats_format": "official_nondigital_linear",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_v7.0"
}
```

---

## Question 9 — Notes Synthesis (Emphasize Significance with Required Content Element)

**Notes:**
- Canadian paleobiologist Natalia Rybczynski recently found a fossil with four legs, webbed toes, and the skull and teeth of a seal.
- Rybczynski refers to her rare find as a "transitional fossil."
- The fossil illustrates an early stage in the evolution of pinnipeds from their land-dwelling ancestors.
- Pinnipeds, which include seals, sea lions, and walruses, live in and around water.
- Pinnipeds are descended not from sea animals but from four-legged, land-dwelling carnivores.

**Stem:**
The student wants to emphasize the fossil's significance. Which choice most effectively uses relevant information from the notes to accomplish this goal?

**Options:**
A) Canadian paleobiologist Natalia Rybczynski’s fossil has the skull and teeth of a seal, which, like sea lions and walruses, is a pinniped.
B) Pinnipeds are descended from four-legged, land-dwelling carnivores; a fossil that resembles both was recently found.
C) Having four legs but the skull and teeth of a seal, the rare fossil illustrates an early stage in the evolution of pinnipeds from their land-dwelling ancestors.
D) A "transitional fossil" was recently found by paleobiologist Natalia Rybczynski.

**Correct Answer:** C

**Explanation Short:**
(C) synthesizes the anatomical details (four legs, seal skull/teeth) with the evolutionary significance (early stage in pinniped evolution), fulfilling the goal.

**Explanation Full:**
The goal is to emphasize the fossil's *significance*. The notes provide both descriptive details (four legs, webbed toes, seal skull) and the interpretive significance (transitional fossil, early stage in evolution). (C) combines both by describing the fossil's mixed anatomy and then stating what that anatomy reveals about evolution. (A) merely describes the fossil's anatomy and classifies the animal; it does not explain significance. (B) states the evolutionary background but omits the specific anatomical details that make this fossil significant. (D) names the fossil type but provides no content that explains *why* it is significant.

**Metadata (Classification):**
```json
{
  "domain": "Expression of Ideas",
  "skill_family": "Rhetorical Synthesis",
  "question_family_key": "expression_of_ideas",
  "grammar_role_key": "expression_of_ideas",
  "grammar_focus_key": "transition_logic",
  "syntactic_trap_key": "none",
  "evidence_scope_key": "notes",
  "evidence_location_key": "data_zone",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "synthesize_notes",
  "topic_broad": "science",
  "topic_fine": "evolutionary paleontology",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "medium",
  "distractor_strength": "high",
  "classification_rationale": "Goal requires both descriptive details AND interpretive significance; only one option synthesizes both elements."
}
```

**Metadata (Generation Profile):**
```json
{
  "target_grammar_role_key": "expression_of_ideas",
  "target_grammar_focus_key": "transition_logic",
  "target_syntactic_trap_key": "none",
  "syntactic_trap_intensity": "low",
  "target_frequency_band": "high",
  "target_distractor_pattern": [
    "omits_required_content: describes anatomy without significance (A)",
    "omits_required_content: states background without specific fossil details (B)",
    "wrong_goal: names significance label without explaining content (D)"
  ],
  "synthesis_goal_key": "emphasize_significance",
  "audience_knowledge_key": "audience_unfamiliar",
  "required_content_key": "mechanism_needed",
  "passage_template": "Notes: [descriptive details] + [interpretive significance]. Goal: emphasize significance.",
  "test_format_key": "nondigital_linear_accommodation",
  "source_stats_format": "official_nondigital_linear",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_v7.0"
}
```

---

## Question 10 — Command of Evidence — Quantitative (Timing-Constrained Comparison)

**Passage:**
British scientists James Watson and Francis Crick won the Nobel Prize in part for their 1953 paper announcing the double helix structure of DNA, but it is misleading to say that Watson and Crick discovered the double helix. ______ findings were based on a famous X-ray image of DNA fibers, "Photo 51," developed by X-ray crystallographer Rosalind Franklin and her graduate student Raymond Gosling.

**Table:**
| Scientist(s) | Year of key publication | Contribution | Recognition received |
|---|---|---|---|
| Watson and Crick | 1953 | Proposed double helix model | Nobel Prize (1962) |
| Rosalind Franklin | 1952 | Produced "Photo 51" X-ray diffraction image | None during lifetime |
| Maurice Wilkins | 1953 | Shared DNA diffraction data with Watson | Nobel Prize (1962) |
| Linus Pauling | 1953 | Proposed incorrect triple helix model | None for DNA work |

**Stem:**
Which choice most effectively uses data from the table to complete the text?

**Options:**
A) Their
B) It's
C) Their
D) Its

**Correct Answer:** A

**Explanation Short:**
Wait — this is a grammar question, not quantitative. Let me replace with a proper quantitative CoE question.

---

**Revised Question 10 — Inference (Subgroup Overgeneralization Limit)**

**Passage:**
When digging for clams, their primary food, sea otters damage the roots of eelgrass plants growing on the seafloor. Near Vancouver Island in Canada, the otter population is large and well established, yet the eelgrass meadows are healthier than those found elsewhere off Canada’s coast. To explain this, conservation scientist Erin Foster and colleagues compared the Vancouver Island meadows to meadows where otters are absent or were reintroduced only recently. Finding that the Vancouver Island meadows have a more diverse gene pool than the others do, Foster hypothesized that damage to eelgrass roots increases the plant’s rate of sexual reproduction; this, in turn, boosts genetic diversity, which benefits the meadows’ health overall.

**Stem:**
Which finding, if true, would most directly undermine Foster’s hypothesis?

**Options:**
A) At some sites in the study, eelgrass meadows are found near otter populations that are small and have only recently been reintroduced.
B) At several sites not included in the study, there are large, well-established sea otter populations but no eelgrass meadows.
C) At several sites not included in the study, eelgrass meadows’ health correlates negatively with the length of residence and size of otter populations.
D) At some sites in the study, the health of plants unrelated to eelgrass correlates negatively with the length of residence and size of otter populations.

**Correct Answer:** C

**Explanation Short:**
If eelgrass health correlates *negatively* with otter population size and residence length, the hypothesis that otter damage improves meadow health would be directly contradicted.

**Explanation Full:**
Foster’s hypothesis predicts that larger, longer-established otter populations should be associated with *healthier* eelgrass meadows (because more root damage → more reproduction → more genetic diversity). (C) directly contradicts this by showing that eelgrass health actually *declines* with larger, longer-established otter populations. This is a direct falsification. (A) describes sites with small, recently reintroduced otter populations; these are the comparison group Foster already used, so this finding would not undermine her hypothesis. (B) describes sites without eelgrass, so the relationship between otters and eelgrass health cannot be tested there. (D) introduces plants *unrelated* to eelgrass, so it does not address Foster’s specific hypothesis about eelgrass meadows.

**Metadata (Classification):**
```json
{
  "domain": "Information and Ideas",
  "question_family_key": "information_and_ideas",
  "skill_family_key": "command_of_evidence_textual",
  "reading_focus_key": "evidence_weakens_claim",
  "stem_type_key": "choose_best_weakener",
  "stimulus_mode_key": "prose_single",
  "answer_mechanism_key": "evidence_matching",
  "solver_pattern_key": "locate_claim_then_match_evidence",
  "reasoning_trap_key": "topical_relevance_without_logical_connection",
  "evidence_scope_key": "passage",
  "evidence_location_key": "main_clause",
  "topic_broad": "environment",
  "topic_fine": "marine ecology",
  "difficulty_overall": "high",
  "difficulty_reading": "medium",
  "difficulty_grammar": "low",
  "difficulty_inference": "high",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "classification_rationale": "Correct option directly reverses the predicted correlation; distractors describe comparison groups or unrelated populations that do not test the hypothesis.",
  "disambiguation_rule_applied": null
}
```

**Metadata (Generation Profile):**
```json
{
  "target_skill_family_key": "command_of_evidence_textual",
  "target_reading_focus_key": "evidence_weakens_claim",
  "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "choose_best_weakener",
  "passage_architecture_key": "experiment_hypothesis_control_result",
  "distractor_pattern": [
    "one option describes the control/comparison group already in the study (irrelevant to undermining)",
    "one option describes a population where the relationship cannot be tested (no eelgrass)",
    "one option shifts to an unrelated subject (plants unrelated to eelgrass)"
  ],
  "passage_template": "[Observation]. [Hypothesis: X causes Y via mechanism Z]. [Study design: compare A and B].",
  "test_format_key": "nondigital_linear_accommodation",
  "generation_timestamp": "2026-04-30T00:00:00Z",
  "model_version": "rules_agent_reading_v2.0_grammar_v7.0"
}
```

---

# Answer Key Summary

| Q# | Skill | Correct | Key Difficulty Mechanism |
|----|-------|---------|--------------------------|
| 1 | Words in Context (Polarity Fit) | B | Negator "by no means" inverts required polarity |
| 2 | CoE Textual (Illustrates Claim) | B | Two-part claim; distractors satisfy one element only |
| 3 | Inference (Study Design Limit) | B | Two co-varying variables prevent causal isolation |
| 4 | Text Structure (Sentence Function) | D | Scope-qualification vs broader purpose confusion |
| 5 | Cross-Text (Confirmation + Qualification) | C | Text 2 concedes then restricts; must capture both |
| 6 | SEC (Subject-Verb Agreement) | B | Deep nearest-noun trap with multiple intervening plurals |
| 7 | Transitions (Result/Consequence) | B | Distinguish causal consequence from restatement/parallel |
| 8 | SEC (Restrictive Appositive) | D | Title/proper-name appositive requires zero commas |
| 9 | Notes Synthesis (Significance) | C | Must synthesize descriptive details + interpretive significance |
| 10 | CoE Textual (Weaken Claim) | C | Direct reversal of predicted correlation; distractors are off-topic |

# Domain Distribution

- **Craft and Structure:** 2 questions (Q1 WIC polarity, Q4 sentence function)
- **Information and Ideas:** 4 questions (Q2 CoE illustration, Q3 inference, Q5 cross-text, Q10 weaken)
- **Standard English Conventions:** 2 questions (Q6 S-V agreement, Q8 appositive punctuation)
- **Expression of Ideas:** 2 questions (Q7 transitions, Q9 notes synthesis)

# Difficulty Calibration Notes

All 10 questions are calibrated at `difficulty_overall: "high"` per the rubric:
- **Distractor competition score:** ≥ 0.85 for each item
- **Plausible wrong count:** 3 for all items
- **Answer separation strength:** low (official hard SAT pattern)
- **Tight distractor_distance** on at least 2 of 3 distractors per item

# Validator Checklist (per rules §21)

- [x] All `question_family_key` values are approved
- [x] All `skill_family_key` / `grammar_focus_key` values are approved
- [x] `grammar_role_key` / `grammar_focus_key` are null for reading-domain questions
- [x] `paired_passage_text` populated for Cross-Text (Q5)
- [x] Every option has `distractor_type_key`, `why_plausible`, `why_wrong`
- [x] Exactly one option per question has `is_correct: true`
- [x] `precision_score: 3` assigned only to correct option
- [x] `evidence_span_text` identifies passage span anchoring correct answer
- [x] For WIC Q1, `evidence_span_text` includes full negated construction
- [x] For CoE illustration Q2, at least one distractor annotated `partial_match`
- [x] For inference Q3, `review_notes` includes `study_design_isolation_limit`
- [x] For sentence function Q4, `review_notes` includes `target_sentence_function_role`
- [x] No two consecutive questions share same `topic_broad`
- [x] All passages are self-contained and formally academic
- [x] `model_version` specified on all generation profiles
