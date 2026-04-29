# DSAT Reading & Writing — Generated Maximum-Difficulty Items (3)

**Source spec:** `rules_agent_dsat_grammar_ingestion_generation_v3.md`
**Ground-truth reference:** SAT Practice Test 4 (Digital), Section 1, Module 1
**Generation date:** 2026-04-22
**Target difficulty:** `difficulty_overall: high` on every dimension, `distractor_strength: high`, `syntactic_trap_intensity: high`
**Calibration goal:** each item should plausibly appear in the top quartile of a Module 2 (hard) form, not Module 1. All three items are built so that (a) at least three of four options are register-matched and grammatically permissible in isolation, and (b) the correct answer requires recognizing a structural feature that the distractors each violate along a different dimension.

---

## Question 1 — Words in Context: abstract-noun completion under compound concession

*Pushes PT4 M1 Q3/Q4 harder by embedding the blank in a conditional-structural claim, with two distractors that are close synonyms failing only on a precise semantic feature.*

**Passage**

Economist Dani Rodrik's political trilemma holds that a state cannot simultaneously pursue deep economic integration, robust national sovereignty, and mass democratic politics; as any two of these commitments tighten, the third necessarily becomes ______, a result Rodrik treats not as a contingent policy failure but as a structural feature of the postwar international economic order.

**Which choice completes the text with the most logical and precise word or phrase?**

- A) attenuated
- B) ancillary
- C) redundant
- D) untenable

**Correct answer:** D) untenable

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 1,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "correct_option_label": "D",
    "explanation_short": "The trilemma says only two of three commitments can be held at once, so when two tighten, the third becomes impossible to maintain — 'untenable.'",
    "explanation_full": "The trilemma is the claim that the three goals are mutually incompatible: choosing any two forces abandoning the third. The blank must therefore capture structural impossibility, not mere weakening or irrelevance. 'Untenable' (D) is exact. 'Attenuated' (A) is the strongest distractor: it means weakened, which is closer but does not capture the trilemma's claim that the third goal cannot be sustained at all. 'Ancillary' (B) means subordinate or supplementary — the trilemma is not about a hierarchy of goals. 'Redundant' (C) means superfluous; the third goal is not unnecessary, it is unattainable.",
    "evidence_span_text": "cannot simultaneously pursue ... the third necessarily becomes ______ ... a structural feature"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Craft and Structure",
    "subskill": "words in context — structural-necessity adjective under conditional",
    "question_family_key": "craft_and_structure",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": "scope_of_negation",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "compare_register",
    "topic_broad": "economics",
    "topic_fine": "political economy / globalization",
    "reading_scope": "sentence-level",
    "reasoning_demand": "semantic-precision inference from a structural claim",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "classification_rationale": "The correct word must reflect the trilemma's claim that the third goal is structurally impossible, not merely diminished."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "attenuated",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "semantic_imprecision",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "Academic register; 'attenuated' plausibly describes something weakened as the other two commitments tighten.",
      "why_wrong": "The trilemma claims the third goal becomes impossible, not merely weakened. 'Attenuated' understates the structural incompatibility.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2
    },
    {
      "option_label": "B",
      "option_text": "ancillary",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "Sounds like a sophisticated policy term.",
      "why_wrong": "Ancillary means supplementary or subordinate; the trilemma is not about rank-ordering goals but about their mutual exclusion.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "redundant",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "common_idiom_pull",
      "why_plausible": "'Redundant' is a familiar negative-valence word in policy contexts.",
      "why_wrong": "Redundant means unnecessary; the trilemma says the third goal is desired but unreachable, not superfluous.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "untenable",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Captures the trilemma's claim that the third goal becomes impossible to sustain once the other two tighten.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "Precision of word choice: the blank must reflect the exact logical claim — structural impossibility, not degree of difficulty.",
    "trap_mechanism": "'Attenuated' is a near-synonym that understates the claim; 'redundant' and 'ancillary' are register-matched but shift to unrelated semantic fields.",
    "correct_answer_reasoning": "The trilemma's central claim is that a state cannot hold all three commitments at once — so the third becomes untenable.",
    "distractor_analysis_summary": "A understates; B and C shift the semantic field entirely."
  },
  "generation_profile": {
    "target_grammar_role_key": null,
    "target_grammar_focus_key": null,
    "target_syntactic_trap_key": "scope_of_negation",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "medium",
    "target_distractor_pattern": [
      "near-synonym understating the claim",
      "register-matched word from an unrelated semantic field",
      "common negative-valence word misreading the relation"
    ],
    "passage_template": "[Scholar]'s [principle] holds that X, Y, and Z cannot all hold; as any two tighten, the third becomes ______, a result [scholar] treats as [structural vs. contingent claim].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.9,
    "needs_human_review": false,
    "review_notes": "A (attenuated) is a precision_score 2 distractor, not 1 — grammatically and tonally defensible but semantically under-calibrated. That is the intended maximum-difficulty pull."
  }
}
```

---

## Question 2 — SEC: Subject–verb agreement with inverted subject + intervening plural appositive + tense register

*Pushes PT4 M1 Q22 harder by (a) inverting the subject so the verb appears before the noun it governs, (b) supplying a plural attractor both before and after the verb, and (c) making tense a second testable dimension so two distractors fail for different reasons.*

**Passage**

Among the most striking features of Octavia Butler's later fiction ______ her relentless interrogation of power, kinship, and the biological basis of social hierarchy — themes that continue to unsettle and instruct contemporary readers of speculative literature.

**Which choice completes the text so that it conforms to the conventions of Standard English?**

- A) are
- B) were
- C) was
- D) is

**Correct answer:** D) is

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 2,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "correct_option_label": "D",
    "explanation_short": "In the inverted structure, the grammatical subject is the singular 'interrogation,' and the present-tense predicate 'continue to unsettle' anchors the sentence in established-finding present.",
    "explanation_full": "In sentences beginning 'Among the …', the real subject follows the verb. Here that subject is 'her relentless interrogation' (singular), not 'features' (plural, inside the prepositional phrase) and not 'themes' (a later appositive). The verb must therefore be singular. The closing clause 'themes that continue to unsettle' establishes the established-finding present register, so the verb must also be present tense. 'Is' (D) satisfies both constraints. 'Are' (A) is plural, attracted by 'features' or 'themes.' 'Were' (B) is plural and past, failing on both dimensions. 'Was' (C) is singular but past, contradicting the present-tense closing clause.",
    "evidence_span_text": "Among the ... features ... is her ... interrogation ... themes that continue"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Form, Structure, and Sense",
    "subskill": "subject-verb agreement with inverted subject plus tense-register constraint",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "agreement",
    "grammar_focus_key": "subject_verb_agreement",
    "secondary_grammar_focus_keys": ["verb_tense_consistency"],
    "syntactic_trap_key": "multiple",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "literature",
    "topic_fine": "speculative fiction",
    "reading_scope": "sentence-level",
    "reasoning_demand": "two-rule interaction under inversion",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "high",
    "difficulty_inference": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "passage_tense_register_key": "established_finding_present",
    "expected_tense_key": "simple_present",
    "tense_shift_allowed": false,
    "tense_register_notes": "The closing clause 'continue to unsettle and instruct contemporary readers' fixes the sentence in the established-finding present.",
    "disambiguation_rule_applied": "subject_verb_agreement > noun_countability",
    "classification_rationale": "Two rules interact: subject-verb agreement selects between singular/plural, and tense register selects between present and past. Only one option satisfies both."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "are",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "'Features' immediately precedes the verb slot; 'themes' follows it. Both are plural.",
      "why_wrong": "The real subject in this inverted structure is the singular 'interrogation,' so a plural verb creates an agreement error.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "were",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "Past tense seems natural for a deceased author's body of work.",
      "why_wrong": "Fails on two dimensions: plural form disagrees with the singular 'interrogation,' and past tense conflicts with the present-tense closing clause 'continue to unsettle.'",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "was",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "verb_tense_consistency",
      "why_plausible": "Singular form agrees with 'interrogation'; past tense plausibly matches 'later fiction.'",
      "why_wrong": "Past tense conflicts with 'continue to unsettle and instruct,' which fixes the sentence in the present.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "is",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Singular (agreeing with 'interrogation') and present (agreeing with 'continue').",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "In inverted 'Among the … ' constructions, the true subject follows the verb and controls agreement; present tense is required when the sentence states a continuing scholarly fact.",
    "trap_mechanism": "Two plural nouns ('features,' 'themes') flank the verb; past tense feels natural for a deceased author. Each distractor fails on a different dimension.",
    "correct_answer_reasoning": "'Is' is singular (agreeing with 'interrogation') and present (agreeing with 'continue to unsettle').",
    "distractor_analysis_summary": "A fails only on agreement; B fails on both; C fails only on tense — ensuring no two distractors fail identically, per V3 §20.2 Step 4."
  },
  "generation_profile": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "multiple",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "target_distractor_pattern": [
      "plural verb attracted by flanking plural nouns (agreement-only failure)",
      "plural + past verb (dual failure)",
      "singular + past verb (tense-only failure)"
    ],
    "passage_template": "Among the [plural attractor] of [author]'s [work corpus] ______ [singular subject] of [plural list] — [plural appositive] that continue to [present-tense predicate].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "Item intentionally tests two interacting rules. The four-cell distractor logic (singular/plural × present/past) is exhaustive: only D occupies the singular-present cell."
  }
}
```

---

## Question 3 — Logical Completion: multi-premise inference with principle-plus-empirics structure

*Pushes PT4 M1 Q18 (Pompeii/Venus) and the rhetorical-synthesis items harder by requiring the test-taker to (a) extract a principle stated abstractly in sentence 1, (b) map an empirical observation in sentence 2 onto the principle's variables, and (c) reject three distractors that each fail the mapping along a different axis — principle-reversal, variable-confusion, and overreach.*

**Passage**

Linguist Sarah Thomason has argued that the intensity of contact between speaker communities, rather than any genetic relatedness between the languages those communities speak, is the best predictor of how much grammatical material will be borrowed from one language into another. Ethnographic and historical records indicate that Michif, a language that arose among the nineteenth-century Métis of the northern plains, developed under continuous and roughly balanced daily contact with both Cree-speaking and French-speaking communities, while its speakers had no comparable exposure to other Algonquian languages that are, in strictly genetic terms, closer to Cree than French is. On Thomason's account, then, ______

**Which choice most logically completes the text?**

- A) Michif should exhibit grammatical borrowing patterns more similar to those of other Algonquian languages than to those of French.
- B) the degree of grammatical borrowing into Michif from French should roughly match the degree of grammatical borrowing from Cree.
- C) any grammatical borrowing from Cree into Michif must have been mediated by contact with other Algonquian languages.
- D) grammatical relatedness cannot be meaningfully assessed in languages that, like Michif, arose from sustained multilingual contact.

**Correct answer:** B) the degree of grammatical borrowing into Michif from French should roughly match the degree of grammatical borrowing from Cree.

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 3,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice most logically completes the text?",
    "correct_option_label": "B",
    "explanation_short": "Thomason's principle makes contact intensity, not genetic relatedness, the predictor; since Michif's contact with Cree and French was 'continuous and roughly balanced,' borrowing should be comparable.",
    "explanation_full": "The passage states two things: a principle ('contact intensity, not genetic relatedness, predicts grammatical borrowing') and an observation about Michif (balanced contact with both Cree and French, but no comparable contact with other Algonquian languages). Applying the principle to the observation yields only one licensed inference: because the intensity of contact with Cree and with French was roughly equal, the amount of borrowing from each should be roughly equal — option B. A reverses the principle by treating genetic relatedness as the predictor. C introduces a mediation claim the passage provides no basis for and that in fact contradicts 'no comparable exposure.' D overreaches: the passage does not deny the meaningfulness of genetic classification, only its predictive value for borrowing.",
    "evidence_span_text": "the intensity of contact ... is the best predictor of how much grammatical material will be borrowed ... continuous and roughly balanced daily contact with both Cree-speaking and French-speaking communities"
  },
  "classification": {
    "domain": "Expression of Ideas",
    "skill_family": "Rhetorical Synthesis",
    "subskill": "logical completion — principle-plus-empirics under reversal and overreach traps",
    "question_family_key": "expression_of_ideas",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": "presupposition_trap",
    "evidence_scope_key": "paragraph",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "evaluate_transition",
    "topic_broad": "social_studies",
    "topic_fine": "contact linguistics / language contact",
    "reading_scope": "paragraph-level",
    "reasoning_demand": "multi-step inference combining a principle and an empirical observation",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "classification_rationale": "The correct completion is the unique inference licensed when the stated principle is applied to the stated observation; each distractor fails the mapping along a distinct axis."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Michif should exhibit grammatical borrowing patterns more similar to those of other Algonquian languages than to those of French.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "common_idiom_pull",
      "why_plausible": "Genetic-family reasoning is the default frame for most readers; Algonquian relatedness sounds like it should matter.",
      "why_wrong": "This reverses Thomason's principle, which explicitly denies that genetic relatedness predicts borrowing. Moreover, the passage states that Michif's speakers had no comparable contact with other Algonquian languages.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "the degree of grammatical borrowing into Michif from French should roughly match the degree of grammatical borrowing from Cree.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Correct application: equal contact intensity, by Thomason's principle, predicts roughly equal borrowing.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "any grammatical borrowing from Cree into Michif must have been mediated by contact with other Algonquian languages.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "partially_supported",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "'Mediation' sounds like a scholarly hedge, and the mention of Algonquian languages primes the reader to give them a role.",
      "why_wrong": "The passage explicitly states that Michif's speakers had no comparable exposure to other Algonquian languages, so they cannot have mediated the Cree borrowing. The claim also ignores direct Cree contact, which the passage affirms.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "grammatical relatedness cannot be meaningfully assessed in languages that, like Michif, arose from sustained multilingual contact.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "overstatement",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "A sophisticated-sounding epistemic limit on genetic classification.",
      "why_wrong": "The passage denies that relatedness predicts borrowing, not that relatedness itself is meaningless. D overreaches into a methodological claim the text does not license.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "A logical completion must be the inference uniquely licensed by combining a stated principle with a stated empirical premise.",
    "trap_mechanism": "Distractor A reverses the principle; C invents a mediation mechanism the passage rules out; D turns a predictive claim into a metaphysical one.",
    "correct_answer_reasoning": "Principle: contact intensity predicts borrowing. Observation: contact intensity with Cree ≈ contact intensity with French. Conclusion: borrowing from Cree ≈ borrowing from French.",
    "distractor_analysis_summary": "A (principle-reversal), C (mechanism-invention that contradicts passage), D (overreach into a claim not made)."
  },
  "generation_profile": {
    "target_grammar_role_key": null,
    "target_grammar_focus_key": null,
    "target_syntactic_trap_key": "presupposition_trap",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "medium",
    "target_distractor_pattern": [
      "principle-reversal (treats the explicitly-denied variable as the predictor)",
      "mechanism-invention contradicting a stated premise",
      "overreach turning a predictive claim into a metaphysical one"
    ],
    "passage_template": "[Scholar] argues that [X], not [Y], predicts [outcome]. Evidence indicates that [subject] had [high X with two sources; low X with Y-related sources]. On [scholar]'s account, then, ______",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.9,
    "needs_human_review": false,
    "review_notes": "The three distractors are orthogonal failures (reversal, invention, overreach), ensuring no two fail for the same reason. The correct answer is the unique inference that respects both premises."
  }
}
```

---

## Answer Key

| # | Type | Correct | Key | Trap |
|---|------|---------|-----|------|
| 1 | Words in context | D | `precision_word_choice` (craft) | `scope_of_negation` |
| 2 | SEC — agreement + tense | D | `subject_verb_agreement` × `verb_tense_consistency` | `multiple` |
| 3 | Logical completion | B | `logical_relationships` | `presupposition_trap` |

## What makes this set harder than the previous five

Per V3 §17.12 the calibration dimension that escalates each item is listed below — these items are hardest on at least three of the five dimensions simultaneously, whereas the earlier five items were hardest on one or two.

- **Q1** raises `difficulty_vocab` and `difficulty_inference` to `high` simultaneously, and makes the strongest distractor (`attenuated`) a `precision_score: 2` near-synonym rather than a `precision_score: 1` outright error — the V3 maximum for a distractor.
- **Q2** is the first item in the set whose correct answer requires satisfying *two* interacting grammar rules (agreement and tense). The distractor grid is exhaustive (singular/plural × present/past), so each of the three wrong options fails on a distinct cell of the matrix. Per V3 §20.2 Step 4, no two distractors fail for identical reasons.
- **Q3** moves from a single-principle inference (as in earlier Q5) to a principle-plus-empirics inference, and each distractor fails along a different axis: reversal, mechanism-invention, and overreach. The correct answer is the unique inference that survives all three failure modes.
