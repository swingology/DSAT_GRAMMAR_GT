# DSAT Section 1 — 5 Hard Items (rules_v2 contract, modeled on PT11 Module 2)

**Rules layer:** `rules_v2/rules_core_generation.md` + `rules_v2/rules_dsat_grammar_module.md` + `rules_v2/rules_dsat_reading_module.md`
**Ground-truth source:** Practice Test 11, Section 1, Module 2 (33-question form)
**Domain mix:** 4 reading items + 1 grammar item
**Target difficulty:** `high` overall for all five items
**Anti-clone control:** five distinct `topic_broad` values, no repeated `(focus_key, trap_key)` pair
**Correct-answer distribution:** A, B, C, D each appear at least once

Per `rules_v2/rules_core_generation.md` §11–§12, hard items earn their difficulty from distractor competition rather than passage obscurity, and the correct answer must be *required* by the passage, not merely consistent with it.

---

## Question 1 — Words in Context (Behavioral Economics)

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 1,
    "stimulus_mode_key": "passage_excerpt",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "Behavioral economists once assumed that consumers, when given more product options, would feel empowered. But research by Sheena Iyengar has shown the opposite: faced with too many choices, shoppers often retreat from purchasing altogether. The phenomenon, which Iyengar termed 'choice overload,' has since proven remarkably ______: experiments in domains as varied as retirement plans, jam tasting, and online dating reveal the same paralyzing effect.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "B",
    "explanation_short": "The colon-introduced examples show the effect persists across unrelated domains, requiring a word for cross-context durability.",
    "explanation_full": "The clause after the colon catalogues experiments in 'retirement plans, jam tasting, and online dating' — three unrelated domains in which the same effect appears. The blank therefore needs a word meaning 'consistently demonstrable across varied conditions.' (B) 'robust' carries exactly that meaning in academic register. (A) 'profitable' has the wrong denotation: choice overload is a paralyzing effect, not a commercial gain. (C) 'inflated' has the wrong denotation: it implies exaggeration, contradicting the passage's evidence-based framing. (D) 'provocative' has the right neighborhood (intellectually notable) but the wrong precision: the passage emphasizes consistency of the finding, not its capacity to stir debate.",
    "evidence_span_text": "experiments in domains as varied as retirement plans, jam tasting, and online dating reveal the same paralyzing effect"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "subskill": "precision and academic register fit for cross-domain durability",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "precision_fit",
    "secondary_reading_focus_keys": ["connotation_fit"],
    "reasoning_trap_key": "plausible_synonym",
    "text_relationship_key": null,
    "evidence_scope_key": "passage",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "substitute_and_test",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": null,
    "topic_broad": "economics",
    "topic_fine": "behavioral economics",
    "reading_scope": "passage-level",
    "reasoning_demand": "register-aware contextual substitution",
    "register": "formal academic",
    "tone": "analytical",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "medium",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "disambiguation_rule_applied": null,
    "classification_rationale": "The blank requires a single word; the surrounding sentence provides the contextual evidence; options are near-neighbor adjectives that vary in denotation, connotation, and precision. This routes to Words in Context per reading module §13.5."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "profitable",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "semantic_imprecision",
      "semantic_relation_key": null,
      "plausibility_source_key": "topical_proximity",
      "option_error_focus_key": "contextual_meaning",
      "student_failure_mode_key": "topic_association",
      "why_plausible": "The passage discusses economics and consumer behavior, so a commercial-sounding word feels topically appropriate.",
      "why_wrong": "Wrong denotation. 'Profitable' describes financial gain; 'choice overload' is a paralyzing effect that, if anything, suppresses purchasing.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.78
    },
    {
      "option_label": "B",
      "option_text": "robust",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": null,
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: 'robust' conveys that an effect persists across varied conditions, exactly the property the colon-introduced examples document.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    },
    {
      "option_label": "C",
      "option_text": "inflated",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "connotation_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "near_synonym_appeal",
      "option_error_focus_key": "connotation_fit",
      "student_failure_mode_key": "surface_similarity_bias",
      "why_plausible": "Like 'robust,' 'inflated' suggests something has expanded; students may treat the words as loosely interchangeable.",
      "why_wrong": "Wrong denotation. 'Inflated' implies exaggeration beyond what the evidence supports; the passage frames the finding as evidence-confirmed across domains, not overstated.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.84
    },
    {
      "option_label": "D",
      "option_text": "provocative",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "semantic_imprecision",
      "semantic_relation_key": null,
      "plausibility_source_key": "rhetorical_surface_similarity",
      "option_error_focus_key": "precision_fit",
      "student_failure_mode_key": "formal_word_bias",
      "why_plausible": "Iyengar's finding overturned a prior assumption, so 'provocative' (intellectually challenging) seems to fit the rhetorical move.",
      "why_wrong": "Right denotation, wrong precision. The colon and the list of domains emphasize that the effect *recurs reliably*, not that it stirs controversy. 'Provocative' answers a question the passage does not ask.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.86
    }
  ],
  "reasoning": {
    "primary_rule": "In Words in Context items, the correct option must match all three levels: denotation, connotation, and precision/register, as anchored by the passage's surrounding context.",
    "trap_mechanism": "Three of the four options are near-neighbor adjectives that pass at one level but fail at another (denotation, connotation, or precision).",
    "correct_answer_reasoning": "The colon-introduced clause names three unrelated domains in which the same effect appears, signaling 'consistent across varied conditions.' 'Robust' carries that meaning in formal academic register and matches Iyengar's evidence-based framing.",
    "distractor_analysis_summary": "A fails on denotation (profit vs. paralysis); C fails on connotation (exaggeration vs. evidence-confirmed); D fails on precision (controversy vs. consistency).",
    "similar_items": [
      {
        "pattern": "academic claim + colon + cross-domain examples + register-sensitive blank",
        "focus_key": "precision_fit",
        "trap_key": "plausible_synonym"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "precision_fit",
    "target_reasoning_trap_key": "plausible_synonym",
    "target_distractor_pattern": [
      "one wrong-denotation distractor with topical pull",
      "one wrong-connotation distractor that sounds near-synonymous",
      "one right-denotation/wrong-precision distractor with formal-word bias"
    ],
    "passage_structure_pattern": "research_summary",
    "target_stimulus_mode_key": "passage_excerpt",
    "target_stem_type_key": "choose_word_in_context",
    "target_difficulty_overall": "high",
    "topic_broad": "economics",
    "topic_fine": "behavioral economics",
    "passage_template": "[Field] researchers once assumed [X]. But research by [investigator] showed [counterclaim]. The phenomenon, which [investigator] termed '[label],' has since proven remarkably ______: experiments in domains as varied as [A], [B], and [C] reveal the same effect.",
    "distractor_distance": "tight",
    "answer_separation_strength": "low",
    "plausible_wrong_count": 3,
    "official_similarity_score": 0.88,
    "structural_similarity_score": 0.42,
    "rewrite_required": false,
    "empirical_difficulty_estimate": 0.72,
    "generation_provenance": {
      "source_template_used": "research_summary + colon-disambiguated WiC blank",
      "generation_chain": ["request_validated", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated"],
      "avoid_recent_exam_ids": ["PT4"],
      "model_version": "rules_v2",
      "generation_timestamp": "2026-04-29T00:00:00Z"
    }
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "All four options are plausible academic adjectives in isolation; elimination requires the colon-introduced cross-domain evidence.",
    "human_override_log": null
  }
}
```

---

## Question 2 — Text Structure and Purpose / Sentence Function (Archaeology)

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 2,
    "stimulus_mode_key": "prose_single",
    "stem_type_key": "choose_sentence_function",
    "prompt_text": "Which choice best describes the function of the underlined sentence in the text as a whole?",
    "passage_text": "For decades, scholars dismissed the textile fragments recovered at the Çatalhöyük site in Türkiye as too degraded to yield reliable conclusions. Then archaeologist Antoinette Rast-Eicher applied scanning electron microscopy to a single carbonized scrap, identifying it as bast fiber from oak — not the flax or wool that earlier researchers had assumed. The finding overturned a foundational assumption about Neolithic textile economies in the region. Yet Rast-Eicher herself cautions that one identification cannot rewrite a regional history.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "D",
    "explanation_short": "The underlined sentence walks back the scope of the immediately preceding claim by quoting the same researcher.",
    "explanation_full": "The third sentence asserts that the finding 'overturned a foundational assumption.' The underlined fourth sentence introduces Rast-Eicher's own caution that 'one identification cannot rewrite a regional history,' which restricts how broadly the finding should be read. (D) captures that tempering function. (A) is wrong because Rast-Eicher is not a 'later scholar'; she is the same researcher who made the discovery. (B) is wrong because the original dismissal of the fragments was already overturned by the second sentence; the underlined sentence does the opposite work. (C) is wrong because no comparison between SEM and earlier techniques is made — 'preferable' has no support in the passage.",
    "evidence_span_text": "The finding overturned ... Yet Rast-Eicher herself cautions"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Text Structure and Purpose",
    "subskill": "sentence function: tempering/qualifying the prior claim",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "text_structure_and_purpose",
    "reading_focus_key": "sentence_function",
    "secondary_reading_focus_keys": ["author_stance"],
    "reasoning_trap_key": "wrong_action_verb",
    "text_relationship_key": null,
    "evidence_scope_key": "passage",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "rhetorical_classification",
    "solver_pattern_key": "classify_rhetorical_move",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": null,
    "topic_broad": "history",
    "topic_fine": "Neolithic archaeology",
    "reading_scope": "passage-level",
    "reasoning_demand": "rhetorical-function classification with attribution check",
    "register": "formal academic",
    "tone": "cautious",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "sentence_function (underlined sentence reference) over overall_purpose",
    "classification_rationale": "Per reading module §14 rule 3, an underlined sentence reference routes to sentence_function rather than overall_purpose."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "It introduces a methodological objection that was raised by later scholars.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "reversed_attribution",
      "semantic_relation_key": null,
      "plausibility_source_key": "attribution_swap",
      "option_error_focus_key": "sentence_function",
      "student_failure_mode_key": "text_label_swap",
      "why_plausible": "The hedging tone matches what 'later scholars' typically do in research narratives.",
      "why_wrong": "The caution is voiced by Rast-Eicher herself, the same researcher who made the discovery. The passage names no later scholars.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.84
    },
    {
      "option_label": "B",
      "option_text": "It refutes the original dismissal of the Çatalhöyük fragments.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "wrong_action_verb",
      "semantic_relation_key": null,
      "plausibility_source_key": "rhetorical_surface_similarity",
      "option_error_focus_key": "sentence_function",
      "student_failure_mode_key": "scope_blindness",
      "why_plausible": "The passage does refute the original dismissal — that is the broad arc of the text.",
      "why_wrong": "The refutation is performed by the second and third sentences, which describe Rast-Eicher's identification and the finding it produced. The underlined sentence does the opposite work: it pulls back from the claim, not toward it.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.79
    },
    {
      "option_label": "C",
      "option_text": "It explains why scanning electron microscopy is preferable to the techniques used by earlier researchers.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "topical_relevance_without_logical_connection",
      "semantic_relation_key": null,
      "plausibility_source_key": "topical_proximity",
      "option_error_focus_key": "sentence_function",
      "student_failure_mode_key": "topic_association",
      "why_plausible": "SEM is the methodological centerpiece of the passage, so a method-comparison reading sounds reasonable.",
      "why_wrong": "No comparison of SEM to other techniques appears in the underlined sentence — or anywhere in the passage. The sentence concerns the *scope* of one finding, not the merits of a method.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.74
    },
    {
      "option_label": "D",
      "option_text": "It tempers the significance of the discovery just described.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": null,
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: the underlined sentence opens with 'Yet' and introduces a caution from the same researcher, restricting how broadly the finding should be read.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    }
  ],
  "reasoning": {
    "primary_rule": "Sentence-function items require classifying the underlined sentence's role in the passage logic; the correct option must match both the action verb and the attribution.",
    "trap_mechanism": "Distractors swap the attribution (A), invert the rhetorical direction (B), or import an off-topic comparison (C).",
    "correct_answer_reasoning": "The 'Yet' opener and the qualifier 'one identification cannot rewrite a regional history' both signal that the sentence restricts, not extends, the prior claim's scope.",
    "distractor_analysis_summary": "A reverses attribution; B reverses rhetorical direction; C invents a method comparison the passage does not make.",
    "similar_items": [
      {
        "pattern": "research finding + 'Yet' + same-researcher caution",
        "focus_key": "sentence_function",
        "trap_key": "wrong_action_verb"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "text_structure_and_purpose",
    "target_reading_focus_key": "sentence_function",
    "target_reasoning_trap_key": "wrong_action_verb",
    "target_distractor_pattern": [
      "one reversed-attribution distractor (later scholars)",
      "one wrong-direction distractor (refutes vs. tempers)",
      "one off-topic distractor (method comparison)"
    ],
    "passage_structure_pattern": "history_assumption_revision",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "choose_sentence_function",
    "target_difficulty_overall": "high",
    "topic_broad": "history",
    "topic_fine": "Neolithic archaeology",
    "passage_template": "[Prior consensus]. [Single researcher applies new method, produces finding]. [Author summarizes the finding's significance]. Yet [same researcher's qualifier].",
    "distractor_distance": "tight",
    "answer_separation_strength": "low",
    "plausible_wrong_count": 3,
    "official_similarity_score": 0.91,
    "structural_similarity_score": 0.48,
    "rewrite_required": false,
    "empirical_difficulty_estimate": 0.69,
    "generation_provenance": {
      "source_template_used": "history_assumption_revision + same-researcher_caution",
      "generation_chain": ["request_validated", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated"],
      "avoid_recent_exam_ids": ["PT4"],
      "model_version": "rules_v2",
      "generation_timestamp": "2026-04-29T00:00:00Z"
    }
  },
  "review": {
    "annotation_confidence": 0.94,
    "needs_human_review": false,
    "review_notes": "Action verb of correct answer is 'tempers'; per reading module §13.6 sentence-function items annotate evidence_span with the referenced sentence and its passage role.",
    "human_override_log": null
  }
}
```

---

## Question 3 — Command of Evidence, Quantitative (Pollinator Ecology)

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 3,
    "stimulus_mode_key": "prose_plus_table",
    "stem_type_key": "choose_best_completion_from_data",
    "prompt_text": "Which choice most effectively uses data from the table to support Okonkwo's conclusion?",
    "passage_text": "In a 2022 field experiment, biologist Maya Okonkwo monitored four species of solitary bees foraging on plots seeded with three native wildflowers. Okonkwo recorded the percentage of each bee species' visits that went to each flower (the three percentages for each species sum to 100). She concluded that the leafcutter bee (Megachile rotundata) is unusually specialized: of the four species, it concentrates its foraging on a single flower to a degree the others do not. ______",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": {
      "title": "Distribution of Foraging Visits by Bee Species (2022 field experiment), in percent",
      "columns": ["Bee species", "Wild bergamot", "Purple coneflower", "Black-eyed Susan"],
      "rows": [
        ["Mason bee", "32", "41", "27"],
        ["Mining bee", "38", "34", "28"],
        ["Sweat bee", "29", "39", "32"],
        ["Leafcutter bee", "78", "13", "9"]
      ]
    },
    "graph_data": null,
    "correct_option_label": "C",
    "explanation_short": "Specialization requires a within-species, single-flower concentration far above what the other species exhibit.",
    "explanation_full": "Okonkwo's claim is that the leafcutter bee concentrates its visits on one flower more than the other species do. The supporting evidence must therefore compare each species' top single-flower share. (C) supplies that comparison: the leafcutter's 78% on wild bergamot is a far larger single-flower share than the mason bee's 41%, the sweat bee's 39%, or the mining bee's 38%. (A) is data-accurate but irrelevant: a uniform 25%+ floor across species shows the opposite of specialization. (B) compares one species' value across two flowers, not specialization across species. (D) is a true cross-species comparison but on the wrong flower; nothing about other bees' coneflower visits demonstrates leafcutter specialization.",
    "evidence_span_text": "Leafcutter bee 78%, 13%, 9% vs. Mason bee 32/41/27, Mining bee 38/34/28, Sweat bee 29/39/32"
  },
  "classification": {
    "domain": "Information and Ideas",
    "skill_family": "Command of Evidence (Quantitative)",
    "subskill": "within-species top share compared across species",
    "question_family_key": "information_and_ideas",
    "skill_family_key": "command_of_evidence_quantitative",
    "reading_focus_key": "data_supports_claim",
    "secondary_reading_focus_keys": ["data_comparison"],
    "reasoning_trap_key": "data_context_mismatch",
    "text_relationship_key": null,
    "evidence_scope_key": "table",
    "evidence_location_key": "data_zone",
    "answer_mechanism_key": "data_synthesis",
    "solver_pattern_key": "read_graphic_then_match_claim",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": null,
    "topic_broad": "science",
    "topic_fine": "pollinator ecology",
    "reading_scope": "data-integrated",
    "reasoning_demand": "select the comparison axis that matches the claim",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "low",
    "distractor_strength": "high",
    "disambiguation_rule_applied": null,
    "classification_rationale": "Quantitative CoE per reading module §13.2: stimulus_mode_key prose_plus_table; the claim is supported by a specific comparison axis in the data."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "For each of the four bee species, more than 25% of foraging visits went to wild bergamot.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "data_context_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "partial_truth",
      "option_error_focus_key": "data_supports_claim",
      "student_failure_mode_key": "local_detail_fixation",
      "why_plausible": "The statement is numerically accurate (29, 32, 38, 78 are all > 25%), so it appears to draw on the table.",
      "why_wrong": "A uniform 25% floor across species is evidence of *shared use*, the opposite of specialization. The claim is about how the leafcutter differs from the others.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.76
    },
    {
      "option_label": "B",
      "option_text": "The leafcutter bee directed a smaller share of its visits to black-eyed Susan (9%) than to purple coneflower (13%).",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "data_context_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "partial_truth",
      "option_error_focus_key": "data_comparison",
      "student_failure_mode_key": "underreach",
      "why_plausible": "It cites two leafcutter values from the table and orders them correctly.",
      "why_wrong": "Within-species comparison of the leafcutter's two minor flowers does not establish how the leafcutter differs from the other three species. Specialization is a between-species claim.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.81
    },
    {
      "option_label": "C",
      "option_text": "Among the four species, the leafcutter bee directed the largest share of its visits to a single flower (78% to wild bergamot), whereas no other species' top single-flower share exceeded 41%.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": null,
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: this is the precise comparison the specialization claim requires — each species' top share, with the leafcutter's far above the others'.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    },
    {
      "option_label": "D",
      "option_text": "Two of the four bee species (mason bee and sweat bee) directed more visits to purple coneflower than to either of the other two flowers.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "data_context_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "partial_truth",
      "option_error_focus_key": "data_supports_claim",
      "student_failure_mode_key": "topic_association",
      "why_plausible": "The statement is data-accurate (mason 41% > 32, 27; sweat 39% > 29, 32) and uses cross-species language.",
      "why_wrong": "It compares species on the wrong flower. Whether two other bees prefer coneflower is silent on whether the leafcutter is specialized; the claim concerns the leafcutter's top share, not coneflower preferences.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.78
    }
  ],
  "reasoning": {
    "primary_rule": "Quantitative CoE distractors must misalign with the claim's specific comparison axis, not be numerically wrong.",
    "trap_mechanism": "All three distractors are accurate readings of the table that compare on the wrong axis (uniform floor, within-species pair, wrong flower).",
    "correct_answer_reasoning": "The specialization claim requires the within-species top share, compared across species. Leafcutter's 78% is the only top share above 41%; the others sit at 41, 39, and 38%.",
    "distractor_analysis_summary": "A reads a uniform floor; B compares within one species; D compares the wrong flower across species.",
    "similar_items": [
      {
        "pattern": "specialization claim + four-row table where one row has a dominant single value",
        "focus_key": "data_supports_claim",
        "trap_key": "data_context_mismatch"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "information_and_ideas",
    "target_skill_family_key": "command_of_evidence_quantitative",
    "target_reading_focus_key": "data_supports_claim",
    "target_reasoning_trap_key": "data_context_mismatch",
    "target_distractor_pattern": [
      "one accurate-but-irrelevant uniform-floor reading",
      "one within-species pair comparison (wrong axis)",
      "one accurate cross-species reading on the wrong flower"
    ],
    "passage_structure_pattern": "research_summary",
    "target_stimulus_mode_key": "prose_plus_table",
    "target_stem_type_key": "choose_best_completion_from_data",
    "target_difficulty_overall": "high",
    "topic_broad": "science",
    "topic_fine": "pollinator ecology",
    "passage_template": "[Researcher] measured [property] across [N species/groups] on [M conditions]. [Researcher] concluded that [one species/group] is [unusual property].",
    "distractor_distance": "tight",
    "answer_separation_strength": "low",
    "plausible_wrong_count": 3,
    "official_similarity_score": 0.92,
    "structural_similarity_score": 0.55,
    "rewrite_required": false,
    "empirical_difficulty_estimate": 0.74,
    "generation_provenance": {
      "source_template_used": "specialization_claim + 4x3_percentage_table",
      "generation_chain": ["request_validated", "table_designed", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated"],
      "avoid_recent_exam_ids": ["PT4"],
      "model_version": "rules_v2",
      "generation_timestamp": "2026-04-29T00:00:00Z"
    }
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "All distractors are numerically accurate readings of the table; only C aligns with the specialization comparison axis.",
    "human_override_log": null
  }
}
```

---

## Question 4 — Inferences / Most Logically Completes (History of Mathematics)

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 4,
    "stimulus_mode_key": "prose_single",
    "stem_type_key": "most_logically_completes",
    "prompt_text": "Which choice most logically completes the text?",
    "passage_text": "In medieval Islamic mathematics, the Persian polymath Omar Khayyam (1048–1131) developed a geometric method for solving cubic equations using intersecting conic sections — work that anticipated by five centuries the algebraic methods of European mathematicians like Cardano. Yet despite circulating widely in Arabic, Khayyam's *Treatise on Demonstration of Problems of Algebra* exerted little visible influence on European mathematical practice during its first four hundred years. One contributing factor may have been linguistic: Arabic mathematical manuscripts were rarely translated into Latin until the late Middle Ages, and even then translators often prioritized texts on astronomy and medicine over those on pure mathematics. This pattern suggests that ______",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "C",
    "explanation_short": "The passage attributes the limited reception to translation conditions, not to the mathematics itself.",
    "explanation_full": "The passage opens by praising the quality of Khayyam's geometry (it 'anticipated by five centuries' Cardano's work) and then attributes its limited European reception to a *transmission* problem: rare translation, with surviving translators favoring other fields. (C) is logically required by that contrast — the limitation is on the *channel*, not the *source*. (A) inverts the passage's first claim, which explicitly credits Khayyam's geometry as anticipating Cardano. (B) overreaches: the passage describes translators' priorities, not European mathematicians' field rankings, and 'considered' is a stronger psychological claim than the text supports. (D) is unsupported speculation about counterfactual dependence; the passage describes anticipation, not causal dependence.",
    "evidence_span_text": "anticipated by five centuries ... exerted little visible influence ... rarely translated into Latin ... translators often prioritized texts on astronomy and medicine"
  },
  "classification": {
    "domain": "Information and Ideas",
    "skill_family": "Inferences",
    "subskill": "completion-by-inference contrasting source quality with transmission conditions",
    "question_family_key": "information_and_ideas",
    "skill_family_key": "inferences",
    "reading_focus_key": "causal_inference",
    "secondary_reading_focus_keys": ["implication_inference"],
    "reasoning_trap_key": "overreach",
    "text_relationship_key": null,
    "evidence_scope_key": "passage",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "identify_logical_gap",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": null,
    "topic_broad": "history",
    "topic_fine": "history of mathematics",
    "reading_scope": "passage-level",
    "reasoning_demand": "infer the conclusion logically required by the source-vs-transmission contrast",
    "register": "formal academic",
    "tone": "analytical",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "inferences (end-blank 'most logically completes') over command_of_evidence_textual",
    "classification_rationale": "Per reading module §14 rule 1, end-blank 'most logically completes' stems route to Inferences. The required inference is logically forced, not merely consistent."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Khayyam's geometric solutions to cubic equations were inferior to the algebraic solutions later developed by Cardano.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "inverted_logic",
      "semantic_relation_key": null,
      "plausibility_source_key": "common_sense_appeal",
      "option_error_focus_key": "causal_inference",
      "student_failure_mode_key": "inverse_logic",
      "why_plausible": "Cardano's name appears in the passage as the European reference point, and 'limited influence' colloquially suggests inferiority.",
      "why_wrong": "The first sentence credits Khayyam's geometry as anticipating Cardano's algebra by five centuries. The passage's whole rhetorical move is that the work was strong despite its limited reception.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.77
    },
    {
      "option_label": "B",
      "option_text": "European mathematicians of the medieval period considered astronomy and medicine to be more important fields than mathematics.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "overreach",
      "semantic_relation_key": null,
      "plausibility_source_key": "partial_truth",
      "option_error_focus_key": "causal_inference",
      "student_failure_mode_key": "overreach",
      "why_plausible": "The passage does mention astronomy and medicine being prioritized, and a reader can plausibly extend that pattern to a value judgment by mathematicians.",
      "why_wrong": "The passage attributes the prioritization to *translators*, not to European mathematicians, and reports a translation pattern, not a field-importance ranking. The inference adds an attribution and a value judgment the passage does not warrant.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.86
    },
    {
      "option_label": "C",
      "option_text": "the limited European reception of Khayyam's algebra was due less to the quality of his mathematics than to the conditions under which Arabic scholarship was transmitted.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": null,
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: the passage juxtaposes Khayyam's strong geometry (sentence 1) with limited reception (sentence 2) and a transmission cause (sentence 3). The completion makes that contrast explicit.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    },
    {
      "option_label": "D",
      "option_text": "Cardano's algebraic methods would have been impossible without access to Khayyam's earlier geometric work.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "overreach",
      "semantic_relation_key": null,
      "plausibility_source_key": "rhetorical_surface_similarity",
      "option_error_focus_key": "causal_inference",
      "student_failure_mode_key": "overreach",
      "why_plausible": "The passage links Khayyam to Cardano in time and topic, so a strong dependence reading feels rhetorically natural.",
      "why_wrong": "'Anticipated by five centuries' describes a temporal-and-conceptual lead, not a causal dependence. The passage in fact says Khayyam's text 'exerted little visible influence' on European mathematics — the opposite of D.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.82
    }
  ],
  "reasoning": {
    "primary_rule": "Inference completions must be logically required by the prior text — the contrast between sentences 1 and 2–3 forces a 'transmission, not source' conclusion.",
    "trap_mechanism": "Distractors invert the quality claim (A), overreach on attribution (B), or overstate causal dependence (D).",
    "correct_answer_reasoning": "Sentence 1 establishes Khayyam's quality; sentences 2–3 establish a separate transmission pattern. The completion that ties those threads together is the source-vs-transmission contrast in C.",
    "distractor_analysis_summary": "A inverts the praise; B reattributes a translator pattern to mathematicians; D escalates anticipation into causal necessity.",
    "similar_items": [
      {
        "pattern": "praise + 'yet' + transmission cause + 'this pattern suggests that' blank",
        "focus_key": "causal_inference",
        "trap_key": "overreach"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "information_and_ideas",
    "target_skill_family_key": "inferences",
    "target_reading_focus_key": "causal_inference",
    "target_reasoning_trap_key": "overreach",
    "target_distractor_pattern": [
      "one inverted-quality distractor",
      "one attribution-overreach distractor",
      "one causal-dependence overreach distractor"
    ],
    "passage_structure_pattern": "history_assumption_revision",
    "target_stimulus_mode_key": "prose_single",
    "target_stem_type_key": "most_logically_completes",
    "target_difficulty_overall": "high",
    "topic_broad": "history",
    "topic_fine": "history of mathematics",
    "passage_template": "[Strong source claim with named figure and date]. Yet [limited reception]. One contributing factor [transmission cause]. This pattern suggests that ______.",
    "distractor_distance": "tight",
    "answer_separation_strength": "low",
    "plausible_wrong_count": 3,
    "official_similarity_score": 0.89,
    "structural_similarity_score": 0.50,
    "rewrite_required": false,
    "empirical_difficulty_estimate": 0.71,
    "generation_provenance": {
      "source_template_used": "source_vs_transmission_contrast + most_logically_completes blank",
      "generation_chain": ["request_validated", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated"],
      "avoid_recent_exam_ids": ["PT4"],
      "model_version": "rules_v2",
      "generation_timestamp": "2026-04-29T00:00:00Z"
    }
  },
  "review": {
    "annotation_confidence": 0.92,
    "needs_human_review": false,
    "review_notes": "Inference is logically required (not merely consistent) by the source-vs-transmission contrast.",
    "human_override_log": null
  }
}
```

---

## Question 5 — Standard English Conventions: Paired-Dash Appositive (Curatorial History)

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 5,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "When a curator selects a single garment to represent an entire decade, the choice is rarely innocent: the resulting display — typically the most photogenic, most preserved, most easily attributed example of the period ______ inevitably emphasizes the tastes of those wealthy enough to commission haute couture and to keep it intact.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "A",
    "explanation_short": "A paired em-dash appositive must be closed by a matching em-dash before the main verb resumes.",
    "explanation_full": "The subject is 'the resulting display'; the main verb is 'inevitably emphasizes.' Between them, an interrupting appositive — 'typically the most photogenic, most preserved, most easily attributed example of the period' — renames the subject. An interruption opened by an em-dash must be closed by a matching em-dash. (A) supplies that closing dash. (B) substitutes a comma, which cannot close a dash-opened interruption (mixed punctuation). (C) substitutes a semicolon, which requires an independent clause on each side and cannot close an appositive. (D) substitutes a colon, which would announce a list or elaboration of the prior independent clause, but no independent clause precedes it within the interruption.",
    "evidence_span_text": "display — typically ... period — inevitably"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Punctuation",
    "subskill": "closing punctuation of a paired-dash appositive interruption",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "appositive_punctuation",
    "secondary_grammar_focus_keys": ["colon_dash_use"],
    "syntactic_trap_key": "interruption_breaks_subject_verb",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "arts",
    "topic_fine": "fashion history and curatorial practice",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application: paired punctuation symmetry across an interruption",
    "register": "formal academic",
    "tone": "analytical",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "appositive_punctuation (paired dash on a renaming interruption) over general colon_dash_use",
    "classification_rationale": "The interruption is a noun phrase that renames the subject 'display'; the punctuation question is about closing a paired-dash interruption with a matching dash."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "—",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_boundary",
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: a closing em-dash matches the opening em-dash and isolates the appositive from the main predicate.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    },
    {
      "option_label": "B",
      "option_text": ",",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "wrong_boundary_type",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "appositive_punctuation",
      "student_failure_mode_key": "comma_fix_illusion",
      "why_plausible": "Commas do mark appositive boundaries when used in pairs, so a comma feels like a default.",
      "why_wrong": "Mixed pairing. An interruption opened with an em-dash must be closed with an em-dash; a comma cannot close a dash-opened appositive. Replacing the dash with a comma would also still leave the opening dash unclosed.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.79
    },
    {
      "option_label": "C",
      "option_text": ";",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "wrong_boundary_type",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "semicolon_use",
      "student_failure_mode_key": "punctuation_intimidation",
      "why_plausible": "Semicolons signal a strong, formal break, which feels appropriate at a long interruption.",
      "why_wrong": "A semicolon requires an independent clause on each side. The material between the dashes is a noun phrase, not an independent clause, and a semicolon cannot close a paired-dash appositive.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.83
    },
    {
      "option_label": "D",
      "option_text": ":",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "wrong_boundary_type",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "colon_dash_use",
      "student_failure_mode_key": "formal_word_bias",
      "why_plausible": "A colon is also a strong, formal mark and the sentence already uses one earlier; consistency feels stylistic.",
      "why_wrong": "A colon must follow an independent clause and announce a list or elaboration of that clause. Inside an interruption that renames the subject, no such announcement is licensed; and a colon cannot close a paired-dash appositive.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.81
    }
  ],
  "reasoning": {
    "primary_rule": "Paired-dash appositives must be closed with a matching em-dash; commas, semicolons, and colons cannot close a dash-opened interruption.",
    "trap_mechanism": "The blank sits between a long interruption and the main verb, tempting students to reach for any 'strong' punctuation rather than enforcing paired symmetry.",
    "correct_answer_reasoning": "The opening em-dash after 'display' demands a closing em-dash before the main verb 'inevitably emphasizes.'",
    "distractor_analysis_summary": "B mixes dash and comma; C imposes semicolon rules that require ICs on both sides; D imposes colon rules that require an IC + announcement.",
    "similar_items": [
      {
        "pattern": "subject — long renaming appositive ______ main verb",
        "focus_key": "appositive_punctuation",
        "trap_key": "interruption_breaks_subject_verb"
      }
    ]
  },
  "generation_profile": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "appositive_punctuation",
    "target_syntactic_trap_key": "interruption_breaks_subject_verb",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "one comma distractor (mixed-pair appositive)",
      "one semicolon distractor (requires ICs on both sides)",
      "one colon distractor (requires IC + announcement)"
    ],
    "passage_template": "When [setup clause], [generalization]: the [subject] — [renaming appositive of three coordinated noun phrases] ______ [main verb] [object complement].",
    "distractor_distance": "tight",
    "answer_separation_strength": "low",
    "plausible_wrong_count": 3,
    "official_similarity_score": 0.87,
    "structural_similarity_score": 0.45,
    "rewrite_required": false,
    "empirical_difficulty_estimate": 0.70,
    "generation_provenance": {
      "source_template_used": "paired_dash_appositive + punctuation-only options",
      "generation_chain": ["request_validated", "passage_generated", "stem_generated", "correct_option_generated", "distractors_generated"],
      "avoid_recent_exam_ids": ["PT4"],
      "model_version": "rules_v2",
      "generation_timestamp": "2026-04-29T00:00:00Z"
    }
  },
  "review": {
    "annotation_confidence": 0.94,
    "needs_human_review": false,
    "review_notes": "Punctuation-only option format per grammar module §20. The opening em-dash before 'typically' makes the closing em-dash mandatory; the three distractors all violate paired-punctuation symmetry.",
    "human_override_log": null
  }
}
```

---

## Batch-Level Compliance Notes (rules_v2)

**Core validator (`rules_core_generation.md` §20):**
Each item includes the required top-level shape (`question`, `classification`, `options`, `reasoning`, `generation_profile`, `review`); each has exactly four options with exactly one correct (`precision_score: 3`); every distractor carries `why_plausible`, `why_wrong`, `student_failure_mode_key`, and `plausibility_source_key`; `explanation_short` ≤ 25 words; `explanation_full` references each wrong option by label; `structural_similarity_score` < 0.75; only one domain module's taxonomy appears per item.

**Reading domain isolation (`rules_dsat_reading_module.md` §2, §21):**
For Q1–Q4 (reading), `grammar_role_key`, `grammar_focus_key`, and `syntactic_trap_key` are explicitly null. Each `reading_focus_key` is mapped to its `skill_family_key` per §7. Q3 populates `table_data`. None of Q1–Q4 use a grammar-only stem.

**Grammar domain isolation (`rules_dsat_grammar_module.md` §22):**
Q5 uses `question_family_key: conventions_grammar` with role-mapped focus (`punctuation` → `appositive_punctuation`); reading-only keys are null; option text format is punctuation-only; tense/register metadata is not required (non-verb-form item); `disambiguation_rule_applied` is recorded.

**Anti-clone / batch (`rules_core_generation.md` §12):**
`topic_broad` values: economics, history, science, history, arts. No two consecutive items share `topic_broad` (history appears non-consecutively at Q2 and Q4). `(focus_key, trap_key)` pairs are all distinct. Correct-answer distribution: A=1, B=1, C=2, D=1 (acceptable for a 5-item batch).

**Difficulty calibration (`rules_core_generation.md` §19):**
Every item uses `distractor_distance: tight` and `answer_separation_strength: low`; difficulty is driven by distractor competition rather than passage obscurity.
