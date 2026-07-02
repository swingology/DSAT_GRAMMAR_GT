# Test 1 — Verbal Section 01 Module 01 — Annotation Chart
- **Job ID:** `1ae88c80-b8f8-437d-bdc1-a3839e8bb5ba`
- **Annotated questions:** 33
- **Annotation model:** deepseek-v4-pro:cloud (reading_v3 §3–14 / grammar_v8 routing)
## Summary table

| Q# | stem_type | domain | question_family | reading_focus | grammar_role | grammar_focus | reasoning_trap | difficulty | conf | review |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | choose_word_in_context | Craft and Structure | craft_and_structure | contextual_meaning |  |  | semantic_relatedness_with… | low | None |  |
| 2 | choose_words_in_context | Craft and Structure | craft_and_structure | precision_fit |  |  | semantic_relatedness_with… | low | None |  |
| 3 | choose_word_in_context | Craft and Structure | craft_and_structure | contextual_meaning |  |  | semantic_relatedness_with… | low | None |  |
| 4 | choose_word_in_context | Craft and Structure | craft_and_structure | contextual_meaning |  |  | semantic_relatedness_with… | low | None |  |
| 5 | choose_words_in_context | Craft and Structure | craft_and_structure | contextual_meaning |  |  | plausible_synonym | medium | None |  |
| 6 | complete_the_text | Expression of Ideas | expression_of_ideas |  | expression_of_ide… | precision_word_choice |  | medium | None |  |
| 7 | choose_main_purpose | Craft and Structure | craft_and_structure | overall_purpose |  |  | partial_purpose | low | None |  |
| 8 | choose_sentence_function | Craft and Structure | craft_and_structure | sentence_function |  |  | also_true_trap | medium | None |  |
| 9 | choose_sentence_function | Craft and Structure | craft_and_structure | sentence_function |  |  | also_true_trap | low | None |  |
| 10 | choose_detail |  |  |  |  |  |  |  | None |  |
| 11 | choose_main_purpose | Craft and Structure | craft_and_structure | overall_purpose |  |  | textual_mimicry | low | None |  |
| 12 | choose_best_illustration | Information and Ideas | information_and_ideas | evidence_illustrates_claim |  |  | keyword_matching | low | None |  |
| 13 | choose_best_support | Information and Ideas | information_and_ideas | evidence_supports_claim |  |  | topical_relevance_without… | medium | None |  |
| 14 | choose_command_of_evidence_… |  |  |  |  |  |  |  | 0.98 |  |
| 15 | choose_best_support | Information and Ideas | information_and_ideas | data_supports_claim |  |  | data_context_mismatch | medium | None |  |
| 16 | choose_best_support | Information and Ideas | information_and_ideas | evidence_supports_claim |  |  | topical_relevance_without… | low | None |  |
| 17 | most_logically_completes |  |  |  |  |  |  |  | 0.95 |  |
| 18 | most_logically_completes | Information and Ideas | information_and_ideas | predictive_inference |  |  | overreach | medium | None |  |
| 19 | complete_the_text | Standard English Conv… | conventions_grammar |  | pronoun | pronoun_antecedent_ag… |  | low | None |  |
| 20 | complete_the_text | Standard English Conv… | conventions_grammar |  | punctuation | quotation_punctuation |  | low | None |  |
| 21 | complete_the_text | Standard English Conv… | conventions_grammar |  | pronoun | pronoun_antecedent_ag… |  | low | None |  |
| 22 | complete_the_text | Standard English Conv… | conventions_grammar |  | punctuation | appositive_punctuation |  | low | None |  |
| 23 | complete_the_text | Standard English Conv… | conventions_grammar |  | verb_form | verb_form |  | low | None |  |
| 24 | complete_the_text | conventions_grammar | conventions_grammar |  | punctuation | colon_dash_use |  | medium | None |  |
| 25 | conform_to_standard_english | Standard English Conv… | conventions_grammar |  | pronoun | pronoun_antecedent_ag… |  | low | None |  |
| 26 | complete_the_text | Standard English Conv… | conventions_grammar |  | agreement | subject_verb_agreement |  | low | None |  |
| 27 | complete_the_text | Standard English Conv… | conventions_grammar |  | punctuation | colon_dash_use |  | low | None |  |
| 28 | complete_the_text | Standard English Conv… | conventions_grammar |  | modifier | modifier_placement |  | low | None |  |
| 29 | complete_the_text |  |  |  | expression_of_ide… | transition_logic |  |  | 0.95 |  |
| 30 | complete_the_text |  |  |  | expression_of_ide… | transition_logic |  |  | 0.99 |  |
| 31 | complete_the_text |  |  |  | expression_of_ide… | transition_logic |  |  | 0.95 |  |
| 32 | choose_best_notes_synthesis |  |  |  | expression_of_ide… | precision_word_choice |  |  | None |  |
| 33 | choose_best_notes_synthesis |  |  |  | expression_of_ide… | precision_word_choice |  |  | None |  |

## Domain-isolation audit

`reading_v3`: grammar_focus_key must be NULL for information_and_ideas / craft_and_structure questions.

| Q# | stem_type | domain | has_reading_focus | has_grammar_focus | verdict |
|---|---|---|---|---|---|
| 1 | choose_word_in_context | Craft and Structure | yes | no | ok |
| 2 | choose_words_in_context | Craft and Structure | yes | no | ok |
| 3 | choose_word_in_context | Craft and Structure | yes | no | ok |
| 4 | choose_word_in_context | Craft and Structure | yes | no | ok |
| 5 | choose_words_in_context | Craft and Structure | yes | no | ok |
| 6 | complete_the_text | Expression of Ideas | no | yes | ok |
| 7 | choose_main_purpose | Craft and Structure | yes | no | ok |
| 8 | choose_sentence_function | Craft and Structure | yes | no | ok |
| 9 | choose_sentence_function | Craft and Structure | yes | no | ok |
| 10 | choose_detail |  | no | no | ok |
| 11 | choose_main_purpose | Craft and Structure | yes | no | ok |
| 12 | choose_best_illustration | Information and Ideas | yes | no | ok |
| 13 | choose_best_support | Information and Ideas | yes | no | ok |
| 14 | choose_command_of_evidence_… |  | no | no | ok |
| 15 | choose_best_support | Information and Ideas | yes | no | ok |
| 16 | choose_best_support | Information and Ideas | yes | no | ok |
| 17 | most_logically_completes |  | no | no | ok |
| 18 | most_logically_completes | Information and Ideas | yes | no | ok |
| 19 | complete_the_text | Standard English Conv… | no | yes | ok |
| 20 | complete_the_text | Standard English Conv… | no | yes | ok |
| 21 | complete_the_text | Standard English Conv… | no | yes | ok |
| 22 | complete_the_text | Standard English Conv… | no | yes | ok |
| 23 | complete_the_text | Standard English Conv… | no | yes | ok |
| 24 | complete_the_text | conventions_grammar | no | yes | ok |
| 25 | conform_to_standard_english | Standard English Conv… | no | yes | ok |
| 26 | complete_the_text | Standard English Conv… | no | yes | ok |
| 27 | complete_the_text | Standard English Conv… | no | yes | ok |
| 28 | complete_the_text | Standard English Conv… | no | yes | ok |
| 29 | complete_the_text |  | no | yes | ok |
| 30 | complete_the_text |  | no | yes | ok |
| 31 | complete_the_text |  | no | yes | ok |
| 32 | choose_best_notes_synthesis |  | no | yes | ok |
| 33 | choose_best_notes_synthesis |  | no | yes | ok |

## Per-question annotation detail + option/distractor analysis

### Q1 — `choose_word_in_context`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | contextual_meaning |
| reasoning_trap_key | semantic_relatedness_without_precision |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | vocabulary_precision |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option 'speculates' is directly supported by the context of uncertainty and the explici… |

**Explanation (short):** The word 'conjecture' in the following sentence signals that Ochoa is speculating, not demanding, doubting, or establishing.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | semantic_relatedness_… | topical_proximity | contextual_meaning | 1 |
| B | ✅ | correct | passage_vocabulary_overlap |  | 3 |
| C |  | connotation_mismatch | topical_proximity | contextual_meaning | 1 |
| D |  | semantic_relatedness_… | topical_proximity | contextual_meaning | 1 |

- **A** : plausible — The word 'demands' relates to necessity, which aligns with the idea that humans will need to live elsewhere.; wrong — It is too forceful; Ochoa is not insisting but rather offering a tentative opinion, as indicated by 'doesn’t have a definite idea' and 'conjecture.'
- **B** ✅: plausible — The word 'speculates' matches the tentative nature of the statement and is reinforced by the synonym 'conjecture.'; wrong — 
- **C** : plausible — The word 'doubts' is related to uncertainty, which is present in the passage.; wrong — It contradicts the intended meaning; Ochoa believes humans will need to live elsewhere, not that she doubts it. The uncertainty is about timing, not the event …
- **D** : plausible — The word 'establishes' suggests a firm conclusion, which might seem appropriate for a former astronaut.; wrong — It is too definitive; the passage emphasizes that Ochoa does not have a definite idea, so she is not establishing anything.
### Q2 — `choose_words_in_context`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | precision_fit |
| reasoning_trap_key | semantic_relatedness_without_precision |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | vocabulary_precision |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct word 'persistent' precisely captures the continuous, long-term nature of the effort des… |

**Explanation (short):** The word 'persistent' best captures the continuous, long-term nature of Wauneka's work.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | semantic_relatedness_… | topical_proximity | precision_fit | 1 |
| B |  | connotation_mismatch | none | precision_fit | 1 |
| C | ✅ | correct | passage_vocabulary_overlap |  | 3 |
| D |  | semantic_relatedness_… | topical_proximity | precision_fit | 1 |

- **A** : plausible — Impartiality is a desirable trait for a legislator, making it a plausible descriptor for Wauneka.; wrong — The sentence emphasizes the continuous, sustained nature of the effort, not its fairness or neutrality. 'Impartial' does not convey persistence.
- **B** : plausible — The word 'offhand' might be considered if one misreads the tone, but it is not plausible in context.; wrong — 'Offhand' means casual or without preparation, which directly contradicts the deliberate, sustained effort described.
- **C** ✅: plausible — The word 'persistent' directly echoes the idea of continuous work over decades.; wrong — 
- **D** : plausible — A mandatory effort might be seen as important and necessary, which could be associated with a legislator's work.; wrong — 'Mandatory' means required by rule or law, which does not describe the voluntary, sustained nature of Wauneka's work.
### Q3 — `choose_word_in_context`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | contextual_meaning |
| reasoning_trap_key | semantic_relatedness_without_precision |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | vocabulary |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option 'exemplifies' means 'serves as an example of,' which fits the context where the … |

**Explanation (short):** The word 'exemplifies' means 'serves as an example of,' which fits the context where the collaboration is an instance of the model.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | semantic_imprecision | topical_proximity | contextual_meaning | 1 |
| B |  | semantic_imprecision | topical_proximity | contextual_meaning | 1 |
| C |  | semantic_imprecision | topical_proximity | contextual_meaning | 1 |
| D | ✅ | correct | none | none | 3 |

- **A** : plausible — The word 'circumvents' might be associated with research or methodology, but it means to avoid or bypass, which is not the intended meaning.; wrong — The collaboration does not avoid the model; it follows it.
- **B** : plausible — The word 'eclipses' might be thought to mean 'surpasses' or 'outshines,' but it does not fit the context of being an example.; wrong — The collaboration does not overshadow the model; it is an instance of it.
- **C** : plausible — The word 'fabricates' might be associated with creating something, but it means to invent or make up, which is not the intended meaning.; wrong — The collaboration did not invent the model; it followed it.
- **D** ✅: plausible — N/A; wrong — N/A
### Q4 — `choose_word_in_context`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | contextual_meaning |
| reasoning_trap_key | semantic_relatedness_without_precision |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | vocabulary_precision |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option 'synchronization' directly matches the context of flowering at the same time; th… |

**Explanation (short):** The dodder synchronizes its flowering with the host by using a protein signal.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct | passage_vocabulary_overlap |  | 3 |
| B |  | semantic_imprecision | none | contextual_meaning | 1 |
| C |  | semantic_relatedness_… | topical_proximity | contextual_meaning | 1 |
| D |  | semantic_imprecision | none | contextual_meaning | 1 |

- **A** ✅: plausible — The word 'synchronization' means occurring at the same time, which matches the description of flowering simultaneously.; wrong — 
- **B** : plausible — Hibernation is a biological process, so it might seem relevant to a plant.; wrong — Hibernation refers to a dormant state, not to timing or synchronization.
- **C** : plausible — The dodder uses a protein that signals impending flowering, which could be seen as a prediction.; wrong — The dodder does not predict; it synchronizes its flowering with the host's actual flowering, not a forecast.
- **D** : plausible — Moderation might be misread as a biological regulation process.; wrong — Moderation means controlling or limiting, not timing synchronization.
### Q5 — `choose_words_in_context`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | contextual_meaning |
| reasoning_trap_key | plausible_synonym |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | medium |
| difficulty_reading | medium |
| difficulty_inference | low |
| difficulty_vocab | medium |
| reasoning_demand | vocabulary_in_context |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option 'a straightforward' contrasts with the later mention of a 'complex set of factor… |

**Explanation (short):** The word 'straightforward' contrasts with the later mention of a 'complex set of factors' and fits the logic that a nearly impossible phenomenon would lack a simple explanation.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | plausible_synonym | near_synonym_appeal | contextual_meaning | 1 |
| B | ✅ | correct | correct | correct | 3 |
| C |  | semantic_imprecision | topical_proximity | contextual_meaning | 1 |
| D |  | semantic_imprecision | topical_proximity | contextual_meaning | 1 |

- **A** : plausible — It means 'able to be perceived or recognized,' which could describe an explanation that is lacking.; wrong — The passage emphasizes the complexity of the explanation, not its detectability. 'Straightforward' better captures the contrast with the 'complex set of factor…
- **B** ✅: plausible — It directly contrasts with the later 'complex set of factors' and fits the logic that a nearly impossible phenomenon would lack a simple explanation.; wrong — N/A
- **C** : plausible — It relates to the idea that the explanation was not settled.; wrong — The phrase 'lacked an inconclusive explanation' would mean the explanation was not inconclusive, which is not the point. The intended meaning is that a simple …
- **D** : plausible — It could be seen as a desirable quality of an explanation.; wrong — The passage does not discuss bias; it discusses the difficulty of forming planets, so the lack of a straightforward explanation is the focus.
### Q6 — `complete_the_text`

| field | value |
|---|---|
| domain | Expression of Ideas |
| question_family_key | expression_of_ideas |
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | precision_word_choice |
| answer_mechanism_key | contextual_substitution |
| difficulty_overall | medium |
| difficulty_grammar | medium |
| difficulty_vocab | medium |
| reasoning_demand | word_choice |
| evidence_scope_key | sentence |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The blank requires a word meaning rejection, as indicated by the colon and 'this rejection'. 'Repud… |

**Explanation (short):** The colon indicates that the second clause explains the first: 'this rejection' signals that Harjo rejects the tendency, so 'repudiates' (meaning rejects) is the most logical and precise word.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | semantic_imprecision | topical_proximity | precision_word_choi… | 1 |
| C |  | semantic_imprecision | topical_proximity | precision_word_choi… | 1 |
| D |  | semantic_imprecision | topical_proximity | precision_word_choi… | 1 |

- **A** ✅: plausible — It means to reject or disown, which matches the context of rejecting a tendency.; wrong — 
- **B** : plausible — It is a verb that could describe a director's public statement, and it sounds similar to 'proclaims' as in declaring something.; wrong — It means to announce or declare, which does not convey rejection; the context requires a word meaning rejection.
- **C** : plausible — It is a verb that could be used in a sentence about a director's work, and it sounds like 'foretells' as in predicting.; wrong — It means to predict, which does not fit the context of rejecting a tendency; the colon indicates rejection, not prediction.
- **D** : plausible — It is a verb that could be used in a sentence about a director's stance, and it sounds like 'recants' as in taking back a statement.; wrong — It means to formally take back a statement or belief, which does not fit the context of rejecting a general tendency; the colon indicates rejection of a tenden…
### Q7 — `choose_main_purpose`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | overall_purpose |
| reasoning_trap_key | partial_purpose |
| answer_mechanism_key | rhetorical_classification |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | rhetorical_classification |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The text describes the invention of reCAPTCHA, making 'To discuss von Ahn’s invention of reCAPTCHA'… |

**Explanation (short):** The text primarily describes how von Ahn created reCAPTCHA, making option A correct.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct | passage_vocabulary_overlap | overall_purpose | 3 |
| B |  | detail_trap | passage_vocabulary_overlap | overall_purpose | 1 |
| C |  | partial_purpose | passage_vocabulary_overlap | overall_purpose | 1 |
| D |  | scope_error | common_sense_appeal | overall_purpose | 1 |

- **A** ✅: plausible — The passage discusses von Ahn's invention, so this option directly matches the content.; wrong — N/A
- **B** : plausible — The passage mentions digital scanners, so a student might think the purpose is to explain them.; wrong — The text only briefly mentions scanners as context; the main purpose is the invention, not scanner mechanics.
- **C** : plausible — The book-digitizing project is mentioned as the motivation, so it seems important.; wrong — The project is background; the main purpose is to discuss the invention that arose from it, not to call attention to the project itself.
- **D** : plausible — reCAPTCHA is widely used, so a student might infer the text aims to indicate its popularity.; wrong — The text never mentions popularity; it focuses on the invention's origin and function.
### Q8 — `choose_sentence_function`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | sentence_function |
| reasoning_trap_key | also_true_trap |
| answer_mechanism_key | rhetorical_classification |
| difficulty_overall | medium |
| difficulty_reading | medium |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | rhetorical_classification |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | literary |
| tone | reflective |
| classification_rationale | The underlined sentence illustrates the idea from the previous sentence that Lily is sensitive to s… |

**Explanation (short):** The underlined sentence illustrates the idea introduced in the previous sentence that Lily is sensitive to scenes that match her mood.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | also_true_trap | passage_vocabulary_overlap | sentence_function | 1 |
| B |  | contradiction | common_sense_appeal | sentence_function | 1 |
| C |  | relationship_fabricat… | rhetorical_surface_simila… | sentence_function | 1 |
| D | ✅ | correct |  |  | 3 |

- **A** : plausible — The sentence mentions the landscape and its features, which could be seen as creating an image of the setting.; wrong — The primary function is not to create a detailed image; that is done by the following sentence. This sentence's purpose is to connect the landscape to Lily's m…
- **B** : plausible — The sentence describes Lily finding something of herself in the landscape, which could be misinterpreted as a struggle.; wrong — The text describes a harmonious connection, not a conflict. Lily's mood is calm and expansive, not conflicted.
- **C** : plausible — The next sentence provides a detailed description of the landscape, which could be seen as expanding on the underlined sentence.; wrong — The underlined sentence is not an assertion; it is a reflection that illustrates the previous idea. The next sentence describes the scene but does not expand o…
- **D** ✅: plausible — The sentence directly follows the introduction of Lily's sensitivity to scenes that match her mood, and it describes the landscape as an enlargement of her moo…; wrong — 
### Q9 — `choose_sentence_function`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | sentence_function |
| reasoning_trap_key | also_true_trap |
| answer_mechanism_key | rhetorical_classification |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | function_identification |
| evidence_scope_key | passage |
| evidence_location_key | second_sentence |
| register | academic informational |
| tone | neutral |
| classification_rationale | The underlined sentence describes the data and comparison used, which is part of the study's method… |

**Explanation (short):** The underlined sentence describes the data and comparison method used in the study, which is part of the methodology.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | also_true_trap | passage_vocabulary_overlap | sentence_function | 1 |
| B |  | wrong_action_verb | topical_proximity | sentence_function | 1 |
| C | ✅ | correct | none |  | 3 |
| D |  | wrong_action_verb | topical_proximity | sentence_function | 1 |

- **A** : plausible — The passage does summarize results later, so the option seems plausible.; wrong — The underlined sentence describes the data and comparison method, not the results.
- **B** : plausible — The sentence mentions specific numbers, which might be mistaken for an example.; wrong — The sentence is not an example; it describes the methodology used for the entire study.
- **C** ✅: plausible — It accurately describes the sentence's role in explaining the data and comparison method.; wrong — 
- **D** : plausible — The sentence mentions data spanning many years, which could be seen as a challenge.; wrong — The sentence does not mention any challenge; it simply states the data and comparison.
### Q10 — `choose_detail`

| field | value |
|---|---|

**Explanation (short):** The passage states that Mother wrote stories and made up poetry for her children.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | contradiction | passage_vocabulary_overlap | supporting_detail | 1 |
| B |  | overreach | passage_vocabulary_overlap | supporting_detail | 1 |
| C | ✅ | correct | passage_vocabulary_overlap | supporting_detail | 3 |
| D |  | overreach | passage_vocabulary_overlap | supporting_detail | 1 |

- **A** : plausible — The passage mentions visits from ladies, so a student might infer she wants more.; wrong — The passage says she did not enjoy dull visits and was always there for the children, contradicting the idea that she wishes for more visits.
- **B** : plausible — The passage mentions birthdays as an occasion for poetry, so a student might assume they are her favorite.; wrong — The text does not state that birthdays are her favorite occasion; it only says she made poetry for birthdays and other great occasions.
- **C** ✅: plausible — The passage explicitly states she wrote stories and made up poetry for them.; wrong — 
- **D** : plausible — The passage says she read to them, so a student might infer it is her favorite activity.; wrong — The text does not state that reading is her favorite activity; it lists it as one of many things she did.
### Q11 — `choose_main_purpose`

| field | value |
|---|---|
| domain | Craft and Structure |
| question_family_key | craft_and_structure |
| reading_focus_key | overall_purpose |
| reasoning_trap_key | textual_mimicry |
| answer_mechanism_key | rhetorical_classification |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | rhetorical_classification |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | poetic |
| tone | admiring |
| classification_rationale | The poem is a direct address praising Dunbar's ability to understand human emotions and nature; the… |

**Explanation (short):** The poem praises Dunbar's perceptiveness about people and nature.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct | none |  | 3 |
| B |  | semantic_imprecision | passage_vocabulary_overlap | overall_purpose | 1 |
| C |  | overreach | topical_proximity | overall_purpose | 1 |
| D |  | contradiction | topical_proximity | overall_purpose | 1 |

- **A** ✅: plausible — Accurately describes the poem's content: praising Dunbar's perceptiveness about people and nature.; wrong — 
- **B** : plausible — Uses the word 'read' from the poem, which might lead a student to think the poem is about reading.; wrong — The poem uses 'read' metaphorically to mean understanding, not literal reading; the purpose is praise, not establishing reading habits.
- **C** : plausible — Mentions a writer, so it seems relevant.; wrong — The poem does not discuss the writer's writing process; it praises his perceptiveness.
- **D** : plausible — Mentions nature (flowers, brook), which might evoke a nature outing.; wrong — The poem is not a memory of a specific afternoon; it's a tribute to the writer's ability to connect with nature.
### Q12 — `choose_best_illustration`

| field | value |
|---|---|
| domain | Information and Ideas |
| question_family_key | information_and_ideas |
| reading_focus_key | evidence_illustrates_claim |
| reasoning_trap_key | keyword_matching |
| answer_mechanism_key | evidence_matching |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | evidence_matching |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | poetic |
| tone | reflective |
| classification_rationale | The correct option directly states that the reader has not known themselves, matching the claim. Di… |

**Explanation (short):** Option A directly states that the reader has not known themselves, perfectly illustrating the claim that readers have not fully understood themselves.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct | correct |  | 3 |
| B |  | topical_relevance_wit… | topical_proximity | evidence_illustrate… | 1 |
| C |  | topical_relevance_wit… | topical_proximity | evidence_illustrate… | 1 |
| D |  | keyword_matching | passage_vocabulary_overlap | evidence_illustrate… | 1 |

- **A** ✅: plausible — Directly states that the reader has not known themselves, matching the claim.; wrong — 
- **B** : plausible — Mentions the reader and uses Whitman's characteristic expansive imagery.; wrong — Describes the reader's vastness, not their lack of self-understanding.
- **C** : plausible — Addresses the reader directly, as the claim notes.; wrong — Focuses on the speaker's desire to address the reader, not on the reader's self-understanding.
- **D** : plausible — Contains the word 'understood,' which appears in the claim.; wrong — Refers to others' lack of understanding of the reader, not the reader's lack of self-understanding.
### Q13 — `choose_best_support`

| field | value |
|---|---|
| domain | Information and Ideas |
| question_family_key | information_and_ideas |
| reading_focus_key | evidence_supports_claim |
| reasoning_trap_key | topical_relevance_without_logical_connection |
| answer_mechanism_key | evidence_matching |
| difficulty_overall | medium |
| difficulty_reading | medium |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | evidence_matching |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option directly demonstrates the student's claim by showing Chambi captured diverse ele… |

**Explanation (short):** Option A directly supports the claim by showing Chambi documented both wealthy and Indigenous communities, capturing diverse elements of Peruvian society.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct | passage_vocabulary_overlap | evidence_supports_c… | 3 |
| B |  | topical_relevance_wit… | topical_proximity | evidence_supports_c… | 1 |
| C |  | topical_relevance_wit… | topical_proximity | evidence_supports_c… | 1 |
| D |  | topical_relevance_wit… | topical_proximity | evidence_supports_c… | 1 |

- **A** ✅: plausible — It directly shows Chambi documented diverse elements of Peruvian society, including Indigenous communities, aligning with the claim of ethnographic value.; wrong — 
- **B** : plausible — Mentions Chambi's photographs and technical skill, which might seem related to quality.; wrong — Technical skill does not demonstrate ethnographic value or the capture of diverse elements of society.
- **C** : plausible — Mentions Chambi's fame and international recognition, which could be seen as evidence of value.; wrong — Fame does not directly support the claim that his photographs have ethnographic value or capture diverse elements with dignity.
- **D** : plausible — Mentions the subjects Chambi photographed, which relates to the content of his work.; wrong — The fact that the subjects were already popular does not support the claim that Chambi's photographs have ethnographic value; it might even weaken it by sugges…
### Q14 — `choose_command_of_evidence_quantitative`

| field | value |
|---|---|
| annotation_confidence | 0.98 |
| needs_human_review | False |

**Explanation (short):** Option C directly supports the claim that the known counts are bare minimums by suggesting the actual numbers are higher.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | data_misread | surface_similarity_bias |  | 1 |
| B |  | data_misread | surface_similarity_bias |  | 1 |
| C | ✅ |  |  |  | 3 |
| D |  | data_misread | surface_similarity_bias |  | 1 |

- **A** : plausible — It accurately compares two data points from the table (35 vs. 66) and seems to use the data.; wrong — It merely states a comparison of known counts without supporting the claim that the counts are minimums; it does not complete the example as required.
- **B** : plausible — It mentions a specific number from the table (47) and seems to add a detail about timing.; wrong — The table shows Carewe was active 1912–1934, so his credited roles are from before 1934, not after. The statement is factually incorrect based on the data.
- **D** : plausible — It uses numbers from the table (33, 10) and seems to correct a misconception.; wrong — The table shows 33 as actor, 35 as director, and 10 as writer. The option incorrectly assigns 33 to directing and 10 to acting, misreading the data.
### Q15 — `choose_best_support`

| field | value |
|---|---|
| domain | Information and Ideas |
| question_family_key | information_and_ideas |
| reading_focus_key | data_supports_claim |
| reasoning_trap_key | data_context_mismatch |
| answer_mechanism_key | data_synthesis |
| difficulty_overall | medium |
| difficulty_reading | medium |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | evidence_matching |
| evidence_scope_key | passage |
| evidence_location_key | table |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option directly compares the observed percentages to the random expectation, showing a … |

**Explanation (short):** The data show that for each species, the percentage of juveniles in patches is much higher than the 15% expected by random distribution, supporting the claim that proximity to other plants provides an advantage.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | data_context_mismatch | partial_truth | data_supports_claim | 1 |
| B |  | wrong_table_row_or_co… | topical_proximity | data_supports_claim | 1 |
| C |  | contradiction | topical_proximity | data_supports_claim | 1 |
| D | ✅ | correct | passage_vocabulary_overlap | data_supports_claim | 3 |

- **A** : plausible — It is a true statement about the data.; wrong — It does not compare the observed percentages to the expected random distribution (15%), so it does not directly support the claim of an advantage.
- **B** : plausible — It mentions a specific species and patch count, which might seem relevant.; wrong — H. stoechas does not have the greatest number; H. squamatum does. Moreover, even if true, it wouldn't support the claim about advantage.
- **C** : plausible — It names specific species and compares to random expectation, which is the correct framework.; wrong — The percentages are actually higher than expected, not lower.
- **D** ✅: plausible — It directly compares the observed percentages to the random expectation, showing a substantial increase for all species.; wrong — 
### Q16 — `choose_best_support`

| field | value |
|---|---|
| domain | Information and Ideas |
| question_family_key | information_and_ideas |
| reading_focus_key | evidence_supports_claim |
| reasoning_trap_key | topical_relevance_without_logical_connection |
| answer_mechanism_key | evidence_matching |
| difficulty_overall | low |
| difficulty_reading | low |
| difficulty_inference | low |
| difficulty_vocab | low |
| reasoning_demand | evidence_matching |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| needs_human_review | False |
| classification_rationale | The correct option directly demonstrates that the plants actively dissolve rock to create channels,… |

**Explanation (short):** The finding that roots carve new entry points even when cracks are available directly supports the hypothesis that the plants actively dissolve rock to create channels.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | topical_relevance_wit… | passage_vocabulary_overlap | evidence_supports_c… | 1 |
| B |  | topical_relevance_wit… | passage_vocabulary_overlap | evidence_supports_c… | 1 |
| C | ✅ | correct | none | evidence_supports_c… | 3 |
| D |  | inverted_logic | topical_proximity | evidence_supports_c… | 1 |

- **A** : plausible — Mentions the same plant family and similar root structures, making it seem relevant to the hypothesis.; wrong — Does not address whether the plants use acid to dissolve rock or obtain phosphorus; the finding is about other species in different conditions, not about the m…
- **B** : plausible — Directly references the acids mentioned in the hypothesis, making it seem connected.; wrong — The proportion of acids is irrelevant to whether the acids dissolve rock and release phosphates; it does not support the functional claim.
- **C** ✅: plausible — N/A; wrong — N/A
- **D** : plausible — Mentions phosphates, which are central to the hypothesis, and seems to test the plants' dependence on rock-derived nutrients.; wrong — If the plants thrive without phosphates, it undermines the hypothesis that they depend on dissolving rock for phosphorus; this finding would weaken, not suppor…
### Q17 — `most_logically_completes`

| field | value |
|---|---|
| annotation_confidence | 0.95 |
| needs_human_review | False |

**Explanation (short):** The lack of evidence for CO2 spikes coinciding with sauropod evolution suggests that increased CO2 was not a necessary factor.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | topical_relevance_wit… | topical_relevance |  | 1 |
| B | ✅ |  |  |  | 3 |
| C |  | contradiction | causal_assumption |  | 1 |
| D |  | overstatement | extreme_language |  | 1 |

- **A** : plausible — It mentions CO2 and sauropod lineages, which are central to the passage.; wrong — The passage does not discuss differential effects on lineages; it only addresses the lack of evidence for CO2 spikes coinciding with evolution. This option int…
- **C** : plausible — It seems to align with the idea that more CO2 led to larger sizes, but the passage explicitly says there is no evidence of such spikes.; wrong — The passage states there is no evidence of CO2 spikes coinciding with sauropod evolution, so this claim directly contradicts the given information.
- **D** : plausible — It uses the same elements (CO2, size evolution) and seems to draw a conclusion about the relationship.; wrong — The passage only indicates a lack of evidence for CO2 spikes; it does not support the strong claim that even slightly higher CO2 would have prevented gigantism…
### Q18 — `most_logically_completes`

| field | value |
|---|---|
| domain | Information and Ideas |
| question_family_key | information_and_ideas |
| reading_focus_key | predictive_inference |
| reasoning_trap_key | overreach |
| answer_mechanism_key | inference |
| difficulty_overall | medium |
| difficulty_reading | medium |
| difficulty_inference | medium |
| difficulty_vocab | low |
| reasoning_demand | inference |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option logically follows from the premise that the strongest opinions consider and rebu… |

**Explanation (short):** The passage argues that the strongest opinions consider and rebut objections, so discussing conflicting views would help judges improve their arguments.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | overreach | topical_proximity | predictive_inference | 1 |
| B | ✅ | correct | passage_vocabulary_overlap |  | 3 |
| C |  | overreach | common_sense_appeal | predictive_inference | 1 |
| D |  | overreach | topical_proximity | predictive_inference | 1 |

- **A** : plausible — It mentions judicial opinions and philosophical works, which are central to the passage.; wrong — The passage does not suggest that discussing conflicting views would eliminate the need to consult philosophical works; it only suggests it would improve the a…
- **B** ✅: plausible — It directly follows from the premise that considering and rebutting objections strengthens opinions.; wrong — 
- **C** : plausible — It seems reasonable that considering opposing views could make opinions clearer to a general audience.; wrong — The passage does not address comprehensibility to non-experts; it focuses on the strength of the arguments, not accessibility.
- **D** : plausible — It connects discussing philosophers' views with aligning opinions with those views.; wrong — The passage does not suggest that discussing conflicting views would make opinions conform to broad philosophical consensus; it only suggests it would improve …
### Q19 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | pronoun |
| grammar_focus_key | pronoun_antecedent_agreement |
| difficulty_overall | low |
| difficulty_grammar | low |
| reasoning_demand | rule_application |
| register | academic informational |
| tone | neutral |
| classification_rationale | The pronoun must agree in number with its antecedent 'customers,' which is plural; 'they' is the on… |

**Explanation (short):** The pronoun must agree with its plural antecedent 'customers,' so 'they' is correct.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | pronoun_antecedent_ag… |  | pronoun_antecedent_… | 1 |
| C |  | pronoun_antecedent_ag… |  | pronoun_antecedent_… | 1 |
| D |  | pronoun_antecedent_ag… |  | pronoun_antecedent_… | 1 |

- **A** ✅: plausible — It is the only plural pronoun, matching the antecedent 'customers.'; wrong — 
- **B** : plausible — 'One' is a pronoun that can refer to people, but it is singular and impersonal, not matching the plural 'customers.'; wrong — It does not agree in number with the plural antecedent 'customers.'
- **C** : plausible — 'You' is a second-person pronoun that could be used in direct address, but the context is about customers in general, not the reader.; wrong — It shifts to second person, inconsistent with the third-person narrative and the plural antecedent 'customers.'
- **D** : plausible — 'It' is a singular neuter pronoun, but 'customers' is plural and human.; wrong — It does not agree in number or animacy with the antecedent 'customers.'
### Q20 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | punctuation |
| grammar_focus_key | quotation_punctuation |
| difficulty_overall | low |
| difficulty_grammar | low |
| classification_rationale | The correct answer uses a comma inside the closing quotation mark, which is the standard American E… |

**Explanation (short):** The comma belongs inside the quotation marks, and the participial phrase 'positing...' correctly modifies the preceding clause.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | semantic_imprecision | common_sense_appeal |  | 1 |
| C |  | semantic_imprecision | common_sense_appeal |  | 1 |
| D |  | semantic_imprecision | common_sense_appeal |  | 1 |

- **A** ✅: plausible — Correctly places the comma inside the closing quotation mark, as per American English conventions, and uses a participial phrase to modify the preceding clause.; wrong — 
- **B** : plausible — A colon can be used to introduce an explanation, which might seem appropriate here.; wrong — A colon is not standard after a quotation before a participial phrase; a comma is required.
- **C** : plausible — A semicolon can join two independent clauses, and 'positing' might be mistaken as an independent clause.; wrong — The phrase 'positing that...' is not an independent clause; it is a participial phrase, so a semicolon is incorrect.
- **D** : plausible — A period ends the sentence, and a new sentence begins with 'Positing', which might seem grammatically possible.; wrong — Starting a new sentence with 'Positing' creates a sentence fragment; the participial phrase should be attached to the previous clause with a comma.
### Q21 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | pronoun |
| grammar_focus_key | pronoun_antecedent_agreement |
| difficulty_overall | low |
| difficulty_grammar | low |
| reasoning_demand | rule_application |
| evidence_scope_key | passage |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The blank requires a possessive pronoun to modify 'findings'. The antecedent is 'Watson and Crick' … |

**Explanation (short):** The blank requires a plural possessive pronoun to modify 'findings' and agree with the plural antecedent 'Watson and Crick'. 'Their' is the correct choice.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | pronoun_agreement_err… | common_contraction_confus… | pronoun_antecedent_… | 1 |
| B |  | pronoun_agreement_err… | singular_pronoun_confusion | pronoun_antecedent_… | 1 |
| C | ✅ | correct |  |  | 3 |
| D |  | pronoun_agreement_err… | singular_possessive_confu… | pronoun_antecedent_… | 1 |

- **A** : plausible — They’re sounds identical to 'their' and is a common contraction, leading students to mistakenly use it as a possessive.; wrong — They’re is a contraction of 'they are', not a possessive pronoun.
- **B** : plausible — It’s is a contraction that might be incorrectly used as a possessive.; wrong — It’s is singular and refers to an inanimate object, not the plural scientists.
- **C** ✅: plausible — Their is the correct plural possessive pronoun.; wrong — 
- **D** : plausible — Its is a possessive pronoun, but it is singular.; wrong — Its is singular and does not agree with the plural antecedent 'Watson and Crick'.
### Q22 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | punctuation |
| grammar_focus_key | appositive_punctuation |
| difficulty_overall | low |
| difficulty_grammar | low |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct option omits commas around the name 'Stina Chyn' because the title 'critic' is not a se… |

**Explanation (short):** No commas are needed around the name 'Stina Chyn' because the title 'critic' is part of the name and not a separate appositive.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | unnecessary_punctuati… | comma_overuse | appositive_punctuat… | 1 |
| B |  | unnecessary_punctuati… | comma_overuse | appositive_punctuat… | 1 |
| C | ✅ | correct |  |  | 3 |
| D |  | unnecessary_punctuati… | comma_overuse | appositive_punctuat… | 1 |

- **A** : plausible — Commas are often used with appositives, so a student might think the name is an appositive that needs to be set off.; wrong — The commas incorrectly treat 'Stina Chyn' as a nonrestrictive appositive, but the title 'critic' is part of the name and should not be separated.
- **B** : plausible — Similar to A, but with an extra comma after 'claims', which might seem like a parenthetical insertion.; wrong — The commas around the name are unnecessary, and the comma after 'claims' is also incorrect because it separates the verb from its object.
- **D** : plausible — A single comma after the name might seem like a natural pause, but it is not standard.; wrong — The comma after 'Chyn' incorrectly separates the subject from the verb, and the comma after 'claims' is also unnecessary.
### Q23 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | verb_form |
| grammar_focus_key | verb_form |
| difficulty_overall | low |
| difficulty_grammar | low |
| register | academic informational |
| tone | neutral |
| classification_rationale | The sentence requires a main verb to complete the clause. 'Claim' is the correct finite verb form; … |

**Explanation (short):** The sentence requires a main verb. 'Claim' is the correct finite verb form for the plural subject 'historians'.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | semantic_imprecision | common_verb_form_error | verb_form | 1 |
| B | ✅ | correct | correct_verb_form | verb_form | 3 |
| C |  | semantic_imprecision | common_verb_form_error | verb_form | 1 |
| D |  | semantic_imprecision | common_verb_form_error | verb_form | 1 |

- **A** : plausible — The -ing form might be used after a preposition or as a participle, but here a main verb is needed.; wrong — The -ing form is a non-finite verb and cannot serve as the main verb of the clause.
- **B** ✅: plausible — The base form 'claim' functions as the present tense verb for the plural subject 'historians'.; wrong — 
- **C** : plausible — The perfect participle might be used in a reduced relative clause, but it cannot serve as the main verb.; wrong — The perfect participle is a non-finite verb and cannot serve as the main verb of the clause.
- **D** : plausible — The infinitive might be used after certain verbs, but not as the main verb after a subject.; wrong — The infinitive is a non-finite verb and cannot serve as the main verb of the clause.
### Q24 — `complete_the_text`

| field | value |
|---|---|
| domain | conventions_grammar |
| question_family_key | conventions_grammar |
| grammar_role_key | punctuation |
| grammar_focus_key | colon_dash_use |
| difficulty_overall | medium |
| difficulty_grammar | medium |
| reasoning_demand | conventions |
| register | academic informational |
| tone | neutral |
| needs_human_review | False |
| classification_rationale | The colon correctly introduces the explanation of why the roundworms move opposite the magnetic fie… |

**Explanation (short):** The colon after 'food' correctly introduces the explanation of the roundworms' behavior, avoiding a dangling modifier.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ |  |  |  | 3 |
| B |  | dangling_modifier |  |  | 1 |
| C |  | redundancy |  |  | 1 |
| D |  | dangling_modifier |  |  | 1 |

- **B** : plausible — A comma after an introductory clause is common, but here it creates a dangling modifier because the main clause subject is 'the magnetic field,' which cannot s…; wrong — The comma leaves the introductory clause 'when searching for food' modifying 'the magnetic field,' resulting in an illogical sentence.
- **C** : plausible — 'While' might seem to connect the searching and the location, but it is redundant with 'when' and creates an ungrammatical structure.; wrong — The phrase 'when searching for food while in the Northern Hemisphere' is redundant and awkward; 'while' is unnecessary and disrupts the sentence flow.
- **D** : plausible — No punctuation might seem acceptable, but it still results in a dangling modifier because the introductory clause lacks a logical subject.; wrong — Without punctuation, the phrase 'when searching for food in the Northern Hemisphere' still modifies 'the magnetic field,' creating an illogical sentence.
### Q25 — `conform_to_standard_english`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | pronoun |
| grammar_focus_key | pronoun_antecedent_agreement |
| answer_mechanism_key | agreement_check |
| difficulty_overall | low |
| difficulty_grammar | low |
| reasoning_demand | agreement |
| evidence_scope_key | sentence |
| evidence_location_key | main_clause |
| register | academic informational |
| tone | neutral |
| classification_rationale | The pronoun must be reflexive and agree with the plural antecedent 'turtle barnacles'. 'Themselves'… |

**Explanation (short):** The pronoun must be reflexive and agree with the plural antecedent 'turtle barnacles'. 'Themselves' is the correct plural reflexive pronoun.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | number_disagreement | common_pronoun_error | pronoun_antecedent_… | 1 |
| B | ✅ | correct | correct_form | pronoun_antecedent_… | 3 |
| C |  | non_reflexive_pronoun | common_pronoun_error | pronoun_antecedent_… | 1 |
| D |  | number_disagreement | common_pronoun_error | pronoun_antecedent_… | 1 |

- **A** : plausible — It is a pronoun that could refer to the barnacles.; wrong — It is singular and not reflexive, while the context requires a plural reflexive pronoun.
- **B** ✅: plausible — It is the correct plural reflexive pronoun.; wrong — N/A
- **C** : plausible — It is a plural pronoun that could refer to the barnacles.; wrong — It is plural but not reflexive; the context requires a reflexive pronoun.
- **D** : plausible — It is a reflexive pronoun that could refer to a singular noun.; wrong — It is singular reflexive, but the antecedent 'turtle barnacles' is plural.
### Q26 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | agreement |
| grammar_focus_key | subject_verb_agreement |
| answer_mechanism_key | rule_application |
| difficulty_overall | low |
| difficulty_grammar | low |
| reasoning_demand | rule_application |
| evidence_scope_key | sentence |
| evidence_location_key | main_clause |
| register | informational |
| tone | neutral |
| classification_rationale | The subject 'landing' is a gerund and takes a singular verb; 'allows' is the only singular present … |

**Explanation (short):** The gerund 'landing' is the subject and requires a singular verb; 'allows' is the only singular present tense option.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | subject_verb_agreemen… | proximity_to_plural_noun | subject_verb_agreem… | 1 |
| C |  | verb_tense_error | general_statement_context | verb_tense_consiste… | 1 |
| D |  | subject_verb_agreemen… | proximity_to_plural_noun | subject_verb_agreem… | 1 |

- **A** ✅: plausible — It is the singular present tense verb that agrees with the gerund subject.; wrong — 
- **B** : plausible — The plural verb 'are' might seem to agree with the nearby plural noun 'spaces.'; wrong — The subject is the singular gerund 'landing,' not 'spaces'; the progressive form is also unnecessary.
- **C** : plausible — The present perfect might be considered for a general statement about the game.; wrong — The simple present is required for a general fact; 'have allowed' is also plural and does not agree with the singular subject.
- **D** : plausible — The plural verb 'allow' might seem to agree with 'spaces.'; wrong — The subject is the singular gerund 'landing,' so the verb must be singular.
### Q27 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | punctuation |
| grammar_focus_key | colon_dash_use |
| difficulty_overall | low |
| difficulty_grammar | low |
| register | academic informational |
| tone | neutral |
| classification_rationale | The correct answer uses a colon to introduce an explanation after an independent clause. The other … |

**Explanation (short):** A colon is used after an independent clause to introduce an explanation or elaboration.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | punctuation_error | comma_splice_trap | comma_splice | 1 |
| C |  | punctuation_error | period_fragment_trap | sentence_fragment | 1 |
| D |  | punctuation_error | missing_punctuation_trap | missing_punctuation | 1 |

- **B** : plausible — A comma after 'though' might seem to continue the sentence smoothly.; wrong — Creates a comma splice by joining two independent clauses with only a comma.
- **C** : plausible — A period might seem to end the first thought cleanly.; wrong — Results in a fragment ('Though, as a pioneering computer programmer...') that cannot stand alone.
- **D** : plausible — Omitting punctuation might seem acceptable in informal writing.; wrong — Lacks necessary punctuation to separate the clauses and set off the conjunctive adverb, creating a run-on.
### Q28 — `complete_the_text`

| field | value |
|---|---|
| domain | Standard English Conventions |
| question_family_key | conventions_grammar |
| grammar_role_key | modifier |
| grammar_focus_key | modifier_placement |
| difficulty_overall | low |
| difficulty_grammar | low |
| register | academic informational |
| tone | neutral |
| classification_rationale | The sentence begins with a participial phrase 'Upon recovering two years later,' which must logical… |

**Explanation (short):** The participial phrase 'Upon recovering two years later' must modify the subject of the main clause, which should be Henry, not his reign.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A | ✅ | correct |  |  | 3 |
| B |  | dangling_modifier | word_order_variation | modifier_placement | 1 |
| C |  | dangling_modifier | word_order_variation | modifier_placement | 1 |
| D |  | wordiness | structural_variation | conciseness | 2 |

- **B** : plausible — Uses the same key terms (Henry, reign, resumed) as the correct answer.; wrong — Creates a dangling modifier because the subject 'the reign' is not the person who recovered.
- **C** : plausible — Uses the same key terms (Henry, reign, resumed) as the correct answer.; wrong — Creates a dangling modifier because the subject 'Henry's reign' is not the person who recovered.
- **D** : plausible — Grammatically correct and places 'Henry' in a position that could be seen as emphatic.; wrong — Although grammatically acceptable, it is unnecessarily wordy and less direct than the standard subject-verb construction, making it a less conventional choice.
### Q29 — `complete_the_text`

| field | value |
|---|---|
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | transition_logic |
| annotation_confidence | 0.95 |
| needs_human_review | False |

**Explanation (short):** 'For example' correctly introduces a specific instance of the hybrid works mentioned in the previous sentence.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | transition_mismatch | transition_assumption |  | 1 |
| B |  | transition_mismatch | transition_assumption |  | 1 |
| C |  | transition_mismatch | transition_assumption |  | 1 |
| D | ✅ |  |  |  | 3 |

- **A** : plausible — A reader might think the sentence contrasts with the previous one, but it actually provides an example.; wrong — It signals a contrast, but the second sentence does not oppose the first; it illustrates it.
- **B** : plausible — A reader might think the second sentence is a result of the first, but it is not a cause-effect relationship.; wrong — It signals a consequence, but the second sentence does not follow as a result of the first; it is an example.
- **C** : plausible — A reader might think the sentence is part of a sequence, but there is no preceding 'firstly' or list.; wrong — It signals a sequence, but the passage does not present a numbered list; it introduces an example.
- **D** ✅: plausible — It logically introduces an example of the hybrid works mentioned in the previous sentence.; wrong — 
### Q30 — `complete_the_text`

| field | value |
|---|---|
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | transition_logic |
| annotation_confidence | 0.99 |
| needs_human_review | False |

**Explanation (short):** The sentence contrasts wolves' limited senses with dogs' full senses, so 'by contrast' is the logical transition.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | transition_mismatch | transition_assumption |  | 1 |
| B |  | transition_mismatch | transition_assumption |  | 1 |
| C | ✅ | correct |  |  | 3 |
| D |  | transition_mismatch | transition_assumption |  | 1 |

- **A** : plausible — A student might think the second sentence restates the first, but it actually presents new, contrasting information.; wrong — 'In other words' signals restatement, but the second sentence does not rephrase the first; it introduces a contrasting fact.
- **B** : plausible — A student might see dogs as an example of a contrasting species, but the sentence is not providing an example of the previous statement.; wrong — 'For instance' introduces an example, but the second sentence is not an example of wolves' limited senses; it is a direct contrast.
- **D** : plausible — A student might think the second sentence follows logically from the first, but there is no cause-effect relationship.; wrong — 'Accordingly' signals a consequence, but the second sentence does not result from the first; it presents an independent contrasting fact.
### Q31 — `complete_the_text`

| field | value |
|---|---|
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | transition_logic |
| annotation_confidence | 0.95 |
| needs_human_review | False |

**Explanation (short):** The sentence describes a shift from working alone to collaborating, so 'Increasingly' indicates the growing trend.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | transition_mismatch | transition_assumption |  | 1 |
| B |  | transition_mismatch | transition_assumption |  | 1 |
| C |  | transition_mismatch | transition_assumption |  | 1 |
| D | ✅ | correct |  |  | 3 |

- **A** : plausible — The word 'similarly' might seem to connect the idea of a shift, but it actually suggests similarity rather than a change.; wrong — The passage describes a shift from working alone to collaborating, not a similarity between two situations.
- **B** : plausible — Students might think the shift is a reason for collaboration, but the sentence does not provide a cause.; wrong — The passage does not state a reason; it simply reports a trend.
- **C** : plausible — Students might think the sentence is adding information about mathematicians, but the focus is on a change.; wrong — The passage is not adding a similar point; it is describing a shift, so 'furthermore' is illogical.
- **D** ✅: plausible — It indicates a growing trend, which matches the shift from working alone to collaborating.; wrong — 
### Q32 — `choose_best_notes_synthesis`

| field | value |
|---|---|
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | precision_word_choice |

**Explanation (short):** Option D accurately presents the study's key finding (the bones belonged to juveniles) and the supporting evidence (few growth lines), while the other options omit the conclusion or include irrelevant details.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | incomplete_presentati… | partial_truth | precision_word_choi… | 1 |
| B |  | too_general | partial_truth | precision_word_choi… | 1 |
| C |  | includes_irrelevant_d… | partial_truth | precision_word_choi… | 1 |
| D | ✅ | correct | full_accuracy |  | 3 |

- **A** : plausible — Mentions the study and the initial uncertainty, which is part of the notes.; wrong — Omits the study's conclusion and the evidence that led to it, failing to present the findings.
- **B** : plausible — Accurately states the subject and location of the study.; wrong — Does not mention the researcher, the method, or the conclusion, so it does not present the study's findings.
- **C** : plausible — Mentions the researcher, the technique, and background about pterosaurs.; wrong — Includes irrelevant background (pterosaurs existed millions of years ago) and omits the key finding that the bones belonged to juveniles.
- **D** ✅: plausible — Accurately and concisely presents the study's method, evidence, and conclusion.; wrong — 
### Q33 — `choose_best_notes_synthesis`

| field | value |
|---|---|
| grammar_role_key | expression_of_ideas |
| grammar_focus_key | precision_word_choice |

**Explanation (short):** Option C directly compares the two women's specific contributions to the March on Washington: Hedgeman's behind-the-scenes work to include a woman speaker, and Bates being that speaker.

| label | correct | distractor_type | plausibility_source | option_error_focus | precision |
|---|---|---|---|---|---|
| A |  | partial_match | partial_truth | precision_word_choi… | 1 |
| B |  | topical_relevance_wit… | topical_proximity | precision_word_choi… | 1 |
| C | ✅ | correct | correct |  | 3 |
| D |  | overreach | topical_proximity | precision_word_choi… | 1 |

- **A** : plausible — It mentions both women and the march, and includes a specific detail about Bates.; wrong — It fails to specify Hedgeman's contribution, omitting the comparison of their specific roles.
- **B** : plausible — It compares the two women's backgrounds and general activism.; wrong — It does not address their specific contributions to the March on Washington, which is the stated goal.
- **C** ✅: plausible — It directly compares the two women's specific contributions to the march.; wrong — 
- **D** : plausible — It mentions both women and the fact that only one spoke.; wrong — It generalizes to many women and does not compare the two women's specific contributions; it focuses on the speaking role only.