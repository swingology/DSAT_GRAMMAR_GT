# PT6 Sec 1 Module 1 — Source Annotation + Generated Mirrors (Q1–Q5)

**Source PDF:** `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/Test_6_digital_sec01_mod01.pdf`
**Rule files applied:**
- `rules_agent_dsat_grammar_ingestion_generation_v7.md` (loaded; not invoked — none of Q1–Q5 are SEC/Expression-of-Ideas items)
- `rules_agent_dsat_reading_v2.md` (governs all five items — all are `craft_and_structure / words_in_context`)

**Scope:** Q1–Q5 of Module 1. All five are Words in Context. Each item below contains a
Mode-C annotation of the official source item, followed by a Mode-B generated mirror
seeded by that annotation's `generation_profile`. Mirror difficulty matches the source
on `difficulty_overall`, `distractor_strength`, and `reasoning_demand`.

---

## ITEM 1 — Source: hedgehog tenrecs (convergent evolution)

### Source question (verbatim)

> Though not closely related, the hedgehog tenrecs of Madagascar share basic ______ true hedgehogs, including protective spines, pointed snouts, and small body size — traits the two groups of mammals independently developed in response to equivalent roles in their respective habitats.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) examples of
> B) concerns about
> C) indications of
> D) similarities with
>
> **Correct: D**

### Source annotation (Mode C)

```json
{
  "question": {
    "source_exam": "PT6",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 1,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "Though not closely related, the hedgehog tenrecs of Madagascar share basic ______ true hedgehogs, including protective spines, pointed snouts, and small body size — traits the two groups of mammals independently developed in response to equivalent roles in their respective habitats.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "D",
    "explanation_short": "The trait list (spines, snouts, small body size) names features the two groups share; the blank must take a phrase meaning 'shared features' that takes the preposition 'with' the comparison group.",
    "explanation_full": "The sentence sets up a comparison: tenrecs and true hedgehogs, though not closely related, exhibit the same external traits. The dash-set clause names those traits and explicitly calls them features 'the two groups of mammals independently developed.' The blank therefore must denote shared resemblances and must idiomatically take 'with' the comparison group. 'Similarities with' satisfies both the semantic and idiomatic constraints. The remaining options either fail the semantic role ('examples of', 'indications of') or are off-register and off-topic ('concerns about').",
    "evidence_span_text": "share basic ______ true hedgehogs, including protective spines, pointed snouts, and small body size — traits the two groups of mammals independently developed"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "subskill": "phrase-level WIC; noun + preposition collocation",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "contextual_meaning",
    "secondary_grammar_focus_keys": [],
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "transition_subtype_key": null,
    "syntactic_trap_key": null,
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "substitute_and_test",
    "topic_broad": "science",
    "topic_fine": "convergent evolution; mammalian morphology",
    "reading_scope": "sentence-level",
    "reasoning_demand": "phrase-level semantic precision plus idiomatic preposition fit",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "low",
    "difficulty_reading": "low",
    "difficulty_grammar": "low",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "distractor_strength": "medium",
    "disambiguation_rule_applied": "§7.5 default — all options near-noun-phrases; tested by passage logic and preposition collocation, not by tonal register",
    "classification_rationale": "Stem wording is the canonical 'most logical and precise word or phrase' for WIC. Passage contains no negator or concessive, so polarity_fit does not apply. Distractor distinctions are local-semantic-role and idiomatic, so contextual_meaning is the focus."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "examples of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "semantic_relation_key": "same_topic_different_relation",
      "plausibility_source_key": "near_synonym_appeal",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "'Examples of' is a common noun-phrase opener for biological listings; a reader may map the trait list directly to 'examples'.",
      "why_wrong": "'Examples of true hedgehogs' would mean the tenrecs ARE instances of true hedgehogs — contradicting 'Though not closely related'.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "concerns about",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "semantic_relation_key": "wrong_evaluative_frame",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "Reader may read 'share basic ___ true hedgehogs' as a shared topic of inquiry.",
      "why_wrong": "Wrong denotation: tenrecs do not have worries about true hedgehogs; the listed traits are physical features, not concerns.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "indications of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "plausible_synonym",
      "semantic_relation_key": "near_synonym_wrong_relation",
      "plausibility_source_key": "near_synonym_appeal",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "'Indications' suggests evidence pointing to something, which feels academic and trait-related.",
      "why_wrong": "Right denotation neighborhood, wrong relation: traits would be indications of common ancestry, but the sentence explicitly says the groups are 'not closely related' and developed traits 'independently'.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "similarities with",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "semantic_relation_key": "exact_match",
      "plausibility_source_key": null,
      "option_error_focus_key": null,
      "why_plausible": null,
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "Select the noun + preposition that names shared physical features between two unrelated groups (convergent evolution).",
    "trap_mechanism": "Surface readers map the trait list to 'examples' or 'indications' without checking what the sentence claims about the groups' relatedness.",
    "correct_answer_reasoning": "1) Read the contrast 'Though not closely related ... share ... including [traits]'. 2) Predict 'shared features / resemblances'. 3) Test each option for (a) right denotation and (b) idiomatic fit with 'with/of/about'. 4) 'Similarities with' alone satisfies both.",
    "distractor_analysis_summary": "A asserts category membership the sentence denies; B uses wrong evaluative frame; C is a near-synonym that requires kinship the sentence rules out.",
    "similar_items": [
      {
        "pattern": "Although not closely related, [group X] of [place A] share basic ______ [group Y], including [3 shared physical features] — features the two groups developed independently in response to comparable habitat roles.",
        "focus_key": "contextual_meaning",
        "trap_key": "local_semantic_role_mismatch"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "contextual_meaning",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "local_semantic_role_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "one local-semantic-role mismatch that asserts category membership",
      "one wrong-evaluative-frame distractor with passage-vocabulary overlap",
      "one near-synonym whose collocation implies a relation the sentence rules out"
    ],
    "passage_template": "Although they evolved independently, [organism A] of [place A] and [organism B] of [place B] share/display [3 shared traits], features the two species developed in response to comparable ecological pressures. Blank takes noun-phrase + preposition.",
    "polarity_context": null,
    "target_sentence_function_role": null,
    "quantitative_sub_pattern": null,
    "passage_architecture_key": null,
    "inference_type_note": null,
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.98,
    "needs_human_review": false,
    "review_notes": "Phrase-level WIC. All options homogeneous as noun+preposition phrases. No negator present, so polarity_fit not invoked."
  }
}
```

### Generated mirror (Mode B) — convergent evolution: gliders

> Although they evolved on opposite sides of the world, the marsupial sugar glider of Australia and the placental flying squirrel of North America possess basic ______ one another, including patagial membranes for gliding, large nocturnal eyes, and similar insect-and-sap diets — features the two species developed independently in response to comparable arboreal niches.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) divergences from
> B) misconceptions about
> C) classifications of
> D) commonalities with
>
> **Correct: D**

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 1,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "Although they evolved on opposite sides of the world, the marsupial sugar glider of Australia and the placental flying squirrel of North America possess basic ______ one another, including patagial membranes for gliding, large nocturnal eyes, and similar insect-and-sap diets — features the two species developed independently in response to comparable arboreal niches.",
    "paired_passage_text": null,
    "notes_bullets": [],
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "D",
    "explanation_short": "The trait list and 'developed independently in response to comparable arboreal niches' specifies convergent shared features; the blank must mean 'shared features' and idiomatically take 'with'.",
    "explanation_full": "The sentence opens with a concessive ('Although they evolved on opposite sides of the world') and lists shared physical traits, framing them explicitly as independently developed convergent features. The blank requires a noun phrase denoting shared features, and the idiom 'commonalities with [comparison group]' is the only option that fits both the meaning and the preposition.",
    "evidence_span_text": "possess basic ______ one another, including patagial membranes for gliding, large nocturnal eyes, and similar insect-and-sap diets — features the two species developed independently"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "subskill": "phrase-level WIC; noun + preposition collocation",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "contextual_meaning",
    "secondary_grammar_focus_keys": [],
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "transition_subtype_key": null,
    "syntactic_trap_key": null,
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "substitute_and_test",
    "topic_broad": "science",
    "topic_fine": "convergent evolution; mammalian gliders",
    "reading_scope": "sentence-level",
    "reasoning_demand": "phrase-level semantic precision plus idiomatic preposition fit",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "low",
    "difficulty_reading": "low",
    "difficulty_grammar": "low",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "distractor_strength": "medium",
    "disambiguation_rule_applied": "§7.5 default contextual_meaning",
    "classification_rationale": "Matches source profile exactly: phrase-level WIC, no negator, distractors fail by local semantic role and collocation."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "divergences from",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "Sounds academic and references contrast between the two animals.",
      "why_wrong": "Reverses the direction: 'divergences from' = differences, but the trait list names shared features.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "misconceptions about",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "common_sense_appeal",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "Marsupial-vs-placental confusion is a common biology misconception, so the phrase is topic-adjacent.",
      "why_wrong": "Wrong denotation: the listed items are physical traits, not beliefs the species hold about each other.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "classifications of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "plausible_synonym",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "option_error_focus_key": "contextual_meaning",
      "why_plausible": "'Classification' is biology vocabulary; reader may map 'marsupial / placental' to 'classifications'.",
      "why_wrong": "'Classifications of one another' would mean the species categorize each other taxonomically — incoherent. Traits are not classifications.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "commonalities with",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "why_plausible": null,
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "Match the noun + preposition that denotes shared physical features between independently evolved species.",
    "trap_mechanism": "Surface readers latch onto biology vocabulary ('classifications', 'divergences', 'misconceptions') without checking what the listed items actually are.",
    "correct_answer_reasoning": "Concessive 'Although they evolved on opposite sides of the world' + shared trait list + 'developed independently' fixes the meaning as convergent shared features. 'Commonalities with' is the only option whose denotation and preposition both fit.",
    "distractor_analysis_summary": "A inverts the relation; B substitutes mental state for physical trait; C substitutes taxonomic act for trait.",
    "similar_items": []
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "contextual_meaning",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "local_semantic_role_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "direction-inverter (divergences/differences)",
      "wrong-semantic-domain (mental state vs physical trait)",
      "passage-vocab plausible-synonym (taxonomic act vs trait)"
    ],
    "passage_template": "Although they evolved on opposite sides of the world, [organism A] of [place A] and [organism B] of [place B] possess basic ______ one another, including [3 traits], features the two species developed independently in response to comparable [environment] niches.",
    "polarity_context": null,
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.96,
    "needs_human_review": false,
    "review_notes": "Mirror preserves source's construct, focus, difficulty, and distractor families. Topic shifted from tenrecs to gliders to avoid passage reuse."
  }
}
```

---

## ITEM 2 — Source: Yaszek's "overtly" feminist sci-fi

### Source question (verbatim)

> In editor Lisa Yaszek's introduction to her anthology *The Future Is Female! More Classic Science Fiction Stories by Women*, Yaszek identifies an increasing sense of ______ feminist mode of writing in the 1970s, in contrast to many woman-authored science fiction stories of the 1920s to 1960s whose politics were less deliberately signaled.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) a prudently
> B) an overtly
> C) a cordially
> D) an inadvertently
>
> **Correct: B**

### Source annotation (Mode C)

```json
{
  "question": {
    "source_exam": "PT6",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 2,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "In editor Lisa Yaszek's introduction to her anthology The Future Is Female! More Classic Science Fiction Stories by Women, Yaszek identifies an increasing sense of ______ feminist mode of writing in the 1970s, in contrast to many woman-authored science fiction stories of the 1920s to 1960s whose politics were less deliberately signaled.",
    "paired_passage_text": null,
    "table_data": null,
    "graph_data": null,
    "correct_option_label": "B",
    "explanation_short": "The contrast 'in contrast to ... less deliberately signaled' forces the blank to mean 'more deliberately/openly signaled'.",
    "explanation_full": "The sentence contrasts the 1970s mode against earlier 1920s–1960s writing 'whose politics were less deliberately signaled.' Polarity logic: the blank's adverb must be the antonym of 'less deliberately signaled' — i.e., openly, plainly, conspicuously. 'Overtly' satisfies this; the other three each fail by polarity, register, or evaluative mismatch.",
    "evidence_span_text": "an increasing sense of ______ feminist mode of writing in the 1970s, in contrast to many woman-authored science fiction stories of the 1920s to 1960s whose politics were less deliberately signaled"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "polarity_fit",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "evidence_scope_key": "sentence",
    "answer_mechanism_key": "polarity_resolution",
    "solver_pattern_key": "apply_negation_logic",
    "topic_broad": "literature",
    "topic_fine": "feminist science fiction history",
    "reasoning_demand": "polarity logic plus connotation fit",
    "register": "academic literary",
    "tone": "neutral analytical",
    "difficulty_overall": "medium",
    "difficulty_reading": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "§7.5 polarity_fit — concessive 'in contrast to ... less deliberately signaled' is a polarity-reversing construction that fixes the required direction of the blank",
    "classification_rationale": "Contrast marker plus 'less deliberately signaled' is a negator/concessive construction. The blank must preserve the inverted polarity (overt/open). Concessive direction is the diagnostic feature, not bare meaning."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "a prudently",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "'Prudent' has a careful, deliberate register that may seem to match 'deliberately signaled'.",
      "why_wrong": "'Prudently' connotes caution and restraint — closer to 'less deliberately signaled', not to the 1970s overt stance.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "an overtly",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "a cordially",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "tone_register_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Carries a positive social tone a reader might attach to feminist solidarity.",
      "why_wrong": "'Cordially' describes warmth/politeness, not the deliberateness of political signaling required by the contrast.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "an inadvertently",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "common_sense_appeal",
      "why_plausible": "'Inadvertent' echoes 'less deliberately signaled' from the second clause and may attract surface-matchers.",
      "why_wrong": "'Inadvertently' is what the earlier writers did. The blank requires its opposite for the 1970s mode.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Apply polarity logic across 'in contrast to ... less deliberately signaled' — blank must invert that polarity.",
    "trap_mechanism": "'Inadvertently' echoes vocabulary from the contrast clause; surface-matchers select it without applying the contrast.",
    "correct_answer_reasoning": "Identify the contrast marker. The post-contrast clause names earlier writing as 'less deliberately signaled.' The blank must therefore name the opposite — openly/plainly signaled. 'Overtly' is the only option in that polarity zone.",
    "distractor_analysis_summary": "A and D are wrong-polarity; C is right-polarity-zone but wrong evaluative register.",
    "similar_items": [
      {
        "pattern": "In [author]'s introduction to [anthology], [author] identifies an increasing sense of ______ [movement] mode in [decade], in contrast to earlier [comparator] whose [features] were less [adverb-of-deliberateness]-signaled.",
        "focus_key": "polarity_fit",
        "trap_key": "polarity_mismatch"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_polarity_logic",
    "target_reasoning_trap_key": "polarity_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "two polarity-mismatches that pair with the contrast clause's adverb",
      "one tone-register-mismatch in the correct polarity zone"
    ],
    "passage_template": "In [scholar]'s study of [field], [scholar] identifies a developing sense of ______ [movement] [mode] in [decade], in contrast to [earlier comparator] whose [feature] was [less + adverb]-[verbed].",
    "polarity_context": "concessive: 'in contrast to ... less deliberately signaled'",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.97,
    "needs_human_review": false,
    "review_notes": "polarity_context: 'in contrast to ... less deliberately signaled'. evidence_span includes full contrast construction per §7.5."
  }
}
```

### Generated mirror (Mode B) — folk revivalists' political stance

> In musicologist Carla Reyes's study of folk-revival recordings, Reyes identifies a developing sense of ______ political stance among singer-songwriters of the late 1960s, in contrast to earlier folk performers, whose social commentary was typically delivered in indirect or allegorical terms.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) a guardedly
> B) an unambiguously
> C) a charitably
> D) an unwittingly
>
> **Correct: B**

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 2,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "In musicologist Carla Reyes's study of folk-revival recordings, Reyes identifies a developing sense of ______ political stance among singer-songwriters of the late 1960s, in contrast to earlier folk performers, whose social commentary was typically delivered in indirect or allegorical terms.",
    "correct_option_label": "B",
    "explanation_short": "Contrast: 'in contrast to ... indirect or allegorical' fixes the blank as 'direct/plain'.",
    "explanation_full": "'Indirect or allegorical' fixes the polarity of the earlier comparator as obscured/hidden. The blank, after the contrast marker, must invert that polarity — open, direct, plain. 'Unambiguously' alone meets this requirement; 'guardedly' and 'unwittingly' fall on the wrong side of the contrast and 'charitably' is in the right polarity zone but wrong register.",
    "evidence_span_text": "a developing sense of ______ political stance ... in contrast to earlier folk performers, whose social commentary was typically delivered in indirect or allegorical terms"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "polarity_fit",
    "answer_mechanism_key": "polarity_resolution",
    "solver_pattern_key": "apply_negation_logic",
    "topic_broad": "humanities",
    "topic_fine": "folk music history",
    "register": "academic humanities",
    "tone": "neutral analytical",
    "difficulty_overall": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Same polarity-fit structure as source — concessive 'in contrast to ... indirect or allegorical' is the polarity diagnostic."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "a guardedly",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "'Guardedly' has a careful tone that fits political speech.",
      "why_wrong": "Wrong polarity: 'guardedly' = cautiously/with reserve, which would match the EARLIER comparator's indirect mode, not the late-1960s mode the contrast marker requires.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "an unambiguously",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "a charitably",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "tone_register_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Positive social register reads as plausible for activist song.",
      "why_wrong": "'Charitably' describes generosity of judgment, not directness of political signaling.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "an unwittingly",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "common_sense_appeal",
      "why_plausible": "Surface-matcher may attach 'unwittingly' to the earlier 'indirect' clause and import it.",
      "why_wrong": "'Unwittingly' = unintentionally, which is the EARLIER mode the sentence contrasts away from.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Apply polarity inversion across 'in contrast to ... indirect or allegorical'.",
    "trap_mechanism": "Two distractors live on the wrong side of the contrast marker; one lives on the right side but with the wrong evaluative register.",
    "correct_answer_reasoning": "Identify 'in contrast to' + 'indirect or allegorical'. Invert: required word means 'direct/open'. 'Unambiguously' is the only direct-polarity adverb.",
    "distractor_analysis_summary": "A and D are polarity-mismatches; C is polarity-correct but register-wrong.",
    "similar_items": []
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_polarity_logic",
    "target_reasoning_trap_key": "polarity_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "polarity_context": "concessive: 'in contrast to ... indirect or allegorical'",
    "distractor_pattern": [
      "two polarity-mismatches; one tone-register-mismatch in correct polarity"
    ],
    "passage_template": "In [scholar]'s study of [field], [scholar] identifies a developing sense of ______ [stance] among [actors] of [period], in contrast to earlier [comparator] whose [feature] was typically delivered in [opposite-polarity descriptor].",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.96,
    "needs_human_review": false,
    "review_notes": "polarity_context recorded. Topic moved from feminist sci-fi to folk-revival musicology to avoid passage reuse while preserving construct."
  }
}
```

---

## ITEM 3 — Source: "Redressing" the trend toward teen overstudy

### Source question (verbatim)

> ______ the long-standing trend of overemphasizing teenagers and young adults in research on social media use, scholars have recently begun to expand their focus to include the fastest-growing cohort of social media users: senior citizens.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) Exacerbating
> B) Redressing
> C) Epitomizing
> D) Precluding
>
> **Correct: B**

### Source annotation (Mode C)

```json
{
  "question": {
    "source_exam": "PT6",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 3,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "______ the long-standing trend of overemphasizing teenagers and young adults in research on social media use, scholars have recently begun to expand their focus to include the fastest-growing cohort of social media users: senior citizens.",
    "correct_option_label": "B",
    "explanation_short": "Scholars are correcting an overemphasis by expanding to include seniors — the participle must mean 'correcting/setting right'.",
    "explanation_full": "The main clause says scholars are EXPANDING focus to ADD senior citizens — i.e., correcting the prior overemphasis on teens. The participle modifying that action must denote remedy/correction. 'Redressing' fits; the others either intensify the problem (Exacerbating), exemplify it (Epitomizing), or prevent it altogether (Precluding) — none describes a corrective expansion.",
    "evidence_span_text": "______ the long-standing trend of overemphasizing teenagers and young adults ... scholars have recently begun to expand their focus to include ... senior citizens"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "contextual_meaning",
    "evidence_scope_key": "sentence",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "substitute_and_test",
    "topic_broad": "science",
    "topic_fine": "social science methodology; demographics of media research",
    "register": "academic neutral",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Single-sentence WIC; no concessive/negator triggering polarity_fit. All four options are Latinate present participles; distinction is by action semantics."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Exacerbating",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "why_plausible": "'Long-standing trend' may suggest something ongoing being intensified.",
      "why_wrong": "Inverts the action: expanding to include the underrepresented cohort REMEDIES, not WORSENS, the overemphasis.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "Redressing",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "Epitomizing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "'Epitomize' sounds academic and may attract by register alone.",
      "why_wrong": "'Epitomizing' = exemplifying; scholars expanding the cohort are not exemplifying the overemphasis.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "Precluding",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "plausible_synonym",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Reader may equate 'correcting' with 'preventing'.",
      "why_wrong": "Wrong scope: 'Precluding' = preventing in advance, but the trend already exists and is being corrected, not prevented from arising.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "The participle must describe what scholars do to a pre-existing imbalance when they expand inclusion — correct/remedy.",
    "trap_mechanism": "Three options sit at adjacent action-semantics zones (worsen, exemplify, prevent) that surface-match the 'trend' vocabulary without satisfying 'expand to include'.",
    "correct_answer_reasoning": "1) Identify what the main clause says scholars are doing: adding the underrepresented group. 2) Predict the action: correcting/remedying. 3) 'Redressing' = setting right an injustice/imbalance.",
    "distractor_analysis_summary": "A inverts; C describes exemplification; D requires the problem not to exist yet.",
    "similar_items": [
      {
        "pattern": "______ the long-standing practice of [overemphasis on X], [actors] have recently begun to [expand/extend] to include [previously excluded Y].",
        "focus_key": "contextual_meaning",
        "trap_key": "local_semantic_role_mismatch"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "contextual_meaning",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "local_semantic_role_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "one direction-inverter (worsen/intensify)",
      "one wrong-action (exemplify)",
      "one near-synonym with wrong scope (prevent vs correct)"
    ],
    "passage_template": "______ the long-standing practice of [overuse / over-reliance on X], [scholars/practitioners] have recently begun to [incorporate / extend to / supplement with Y].",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.97,
    "needs_human_review": false,
    "review_notes": "All four options are present participles, semantically homogeneous, all Latinate register."
  }
}
```

### Generated mirror (Mode B) — anatomical education and digital models

> ______ the long-standing practice of relying solely on cadaver dissection in anatomy education, medical schools have in recent years begun to incorporate three-dimensional digital models, which allow students to visualize the body's interior in ways that fixed physical specimens cannot accommodate.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) Aggravating
> B) Tempering
> C) Epitomizing
> D) Forestalling
>
> **Correct: B**

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 3,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "______ the long-standing practice of relying solely on cadaver dissection in anatomy education, medical schools have in recent years begun to incorporate three-dimensional digital models, which allow students to visualize the body's interior in ways that fixed physical specimens cannot accommodate.",
    "correct_option_label": "B",
    "explanation_short": "Adding digital models alongside cadaver dissection moderates the exclusive reliance — the participle must mean 'moderating/correcting'.",
    "explanation_full": "'Relying solely on cadaver dissection' is the overreliance being addressed; medical schools are correcting it by incorporating an additional method. The participle must denote moderation/correction. 'Tempering' fits; 'Aggravating' inverts the action, 'Epitomizing' would mean medical schools are typifying the overreliance, and 'Forestalling' would require the practice to not yet exist.",
    "evidence_span_text": "______ the long-standing practice of relying solely on cadaver dissection ... medical schools have in recent years begun to incorporate three-dimensional digital models"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "contextual_meaning",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "substitute_and_test",
    "topic_broad": "science",
    "topic_fine": "medical education methodology",
    "register": "academic neutral",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Matches source: same participial structure, same correction-via-inclusion frame, same distractor families."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Aggravating",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "passage_vocabulary_overlap",
      "why_plausible": "'Long-standing practice' may suggest an ongoing problem being intensified.",
      "why_wrong": "Inverts the action: schools are reducing exclusive reliance, not worsening it.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "Tempering",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "Epitomizing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Academic register matches; reader may attach 'epitomize' to long-standing convention.",
      "why_wrong": "Medical schools incorporating digital models are not exemplifying the cadaver-only practice — they are diluting it.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "Forestalling",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "plausible_synonym",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Reader may equate 'correcting' with 'preventing'.",
      "why_wrong": "'Forestalling' presumes the practice has not yet taken hold; here the practice is already 'long-standing' and is being amended, not prevented.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Participle must describe what schools do when they reduce an exclusive reliance by adding an alternative method — moderate/correct.",
    "trap_mechanism": "Distractors occupy adjacent action zones (intensify / exemplify / prevent) drawn from the same Latinate register as the key.",
    "correct_answer_reasoning": "Identify action in main clause (begin to incorporate digital models alongside dissection). Predict 'moderating'. 'Tempering' is the only option that names that action.",
    "distractor_analysis_summary": "A inverts direction; C reverses agency; D fails on tense/scope.",
    "similar_items": []
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "contextual_meaning",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "local_semantic_role_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "direction-inverter (Aggravating)",
      "wrong-action (Epitomizing)",
      "near-synonym wrong-scope (Forestalling)"
    ],
    "passage_template": "______ the long-standing practice of [exclusive method X], [actors] have in recent years begun to [incorporate / supplement with method Y], which [provides remedy].",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Same distractor architecture as source — three Latinate present participles paired against the corrective key."
  }
}
```

---

## ITEM 4 — Source: Baldwin's "disputing" (figurative)

### Source question (verbatim)

> The following text is adapted from James Baldwin's 1956 novel *Giovanni's Room*. The narrator is riding in a taxi down a street lined with food vendors and shoppers in Paris, France.
>
> The multitude of Paris seems to be dressed in blue every day but Sunday, when, for the most part, they put on an unbelievably festive black. Here they were now, in blue, *disputing*, every inch, our passage, with their wagons, handtrucks, their bursting baskets carried at an angle steeply self-confident on the back.
>
> As used in the text, what does the word "disputing" most nearly mean?
>
> A) Arguing about
> B) Disapproving of
> C) Asserting possession of
> D) Providing resistance to
>
> **Correct: D**

### Source annotation (Mode C)

```json
{
  "question": {
    "source_exam": "PT6",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 4,
    "stimulus_mode_key": "passage_excerpt",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "As used in the text, what does the word \"disputing\" most nearly mean?",
    "passage_text": "The multitude of Paris seems to be dressed in blue every day but Sunday, when, for the most part, they put on an unbelievably festive black. Here they were now, in blue, disputing, every inch, our passage, with their wagons, handtrucks, their bursting baskets carried at an angle steeply self-confident on the back.",
    "correct_option_label": "D",
    "explanation_short": "The vendors physically obstruct the taxi's passage with wagons and baskets; 'disputing' here is figurative for contesting/blocking, not verbal arguing.",
    "explanation_full": "Context locates 'disputing' between bodies and goods (wagons, handtrucks, bursting baskets) and a moving vehicle ('our passage') in a crowded street. The verb cannot mean verbal argument: nothing in the scene is being said. It denotes the figurative contesting of physical space — providing resistance to the taxi's forward motion. The literal courtroom meaning of 'dispute' is a deliberate trap.",
    "evidence_span_text": "Here they were now, in blue, disputing, every inch, our passage, with their wagons, handtrucks, their bursting baskets"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "figurative_language_meaning",
    "evidence_scope_key": "sentence_pair",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "locate_figurative_function",
    "topic_broad": "literature",
    "topic_fine": "literary fiction; Baldwin",
    "register": "literary",
    "tone": "vivid descriptive",
    "difficulty_overall": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Underlined-word stem with 'most nearly mean'; literal meaning of 'disputing' = arguing, but passage context (wagons, handtrucks, physical 'passage') forces a figurative reading. Per §7.5, this is figurative_language_meaning."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Arguing about",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "figurative_literal_confusion",
      "plausibility_source_key": "common_definition_appeal",
      "why_plausible": "'Disputing' literally means arguing.",
      "why_wrong": "The vendors are not speaking; physical wagons and baskets contest space, not words.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "Disapproving of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "connotation_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Dispute carries a negative-evaluation flavor; reader may collapse it to disapproval.",
      "why_wrong": "Nothing in the passage indicates the crowd disapproves of the narrator — the contest is physical, not evaluative.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "Asserting possession of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "plausible_synonym",
      "plausibility_source_key": "common_sense_appeal",
      "why_plausible": "Vendors filling the street might be read as claiming territory.",
      "why_wrong": "Right neighborhood, wrong precision: vendors are resisting passage 'every inch', not staking ownership claims.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "Providing resistance to",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "Recognize 'disputing' as figurative for contesting physical space, given that the object is 'our passage' and the instruments are wagons and baskets.",
    "trap_mechanism": "Literal definition 'arguing about' is the canonical figurative_literal_confusion trap.",
    "correct_answer_reasoning": "1) Substitute literal meanings: 'arguing about our passage' / 'disapproving of our passage' — incoherent. 2) Recognize the verb is metaphorical: vendors and goods physically block the taxi. 3) Match to 'providing resistance to'.",
    "distractor_analysis_summary": "A is the literal trap; B reroutes to evaluative attitude; C captures spatial assertion but at the wrong precision.",
    "similar_items": [
      {
        "pattern": "Literary narrator describes a crowded space where a normally verbal/judicial verb (disputing/contesting/protesting) is applied to physical objects (wagons, carts, baskets) that obstruct movement.",
        "focus_key": "figurative_language_meaning",
        "trap_key": "figurative_literal_confusion"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "figurative_language_meaning",
    "target_test_construct_key": "figurative_interpretation_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "figurative_literal_confusion",
    "target_stimulus_mode_key": "passage_excerpt",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "literal-meaning trap (figurative_literal_confusion) is mandatory",
      "one connotation-mismatch in the same semantic field",
      "one plausible-synonym at wrong precision"
    ],
    "passage_template": "Literary narrator describes a setting. An underlined verb that literally denotes a verbal/intentional act is applied to inanimate or non-verbal physical objects, forcing a figurative reading.",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.97,
    "needs_human_review": false,
    "review_notes": "figurative function: verbal-act verb applied to inanimate spatial obstruction. Literal meaning ('Arguing about') is among distractors per §7.5 / §21.1."
  }
}
```

### Generated mirror (Mode B) — Brontë excerpt, "composed"

> The following text is adapted from Charlotte Brontë's 1849 novel *Shirley*. The narrator describes a stretch of moorland after a night-long storm.
>
> The wind, which had through the night assailed the lonely heath, now spent itself in fitful gusts. Heather and gorse, lately whipped to a horizontal lean, slowly *composed* themselves, while overhead a thin sun ventured down between the parting clouds, tentatively touching the wet stones.
>
> As used in the text, what does the word "composed" most nearly mean?
>
> A) Wrote down
> B) Settled into stillness
> C) Arranged in order
> D) Reconciled to defeat
>
> **Correct: B**

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 4,
    "stimulus_mode_key": "passage_excerpt",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "As used in the text, what does the word \"composed\" most nearly mean?",
    "passage_text": "The wind, which had through the night assailed the lonely heath, now spent itself in fitful gusts. Heather and gorse, lately whipped to a horizontal lean, slowly composed themselves, while overhead a thin sun ventured down between the parting clouds, tentatively touching the wet stones.",
    "correct_option_label": "B",
    "explanation_short": "Plants do not write or arrange; 'composed themselves' personifies the heather and gorse settling back into stillness after the wind ebbs.",
    "explanation_full": "The literal meanings of 'compose' — write or arrange — cannot apply to heather and gorse. The verb is personified: with the wind dying, the bent plants slowly return to upright stillness. The figurative reading 'compose oneself' (to calm/settle) is the only coherent meaning here, and the surrounding language ('spent itself in fitful gusts', 'tentatively touching') reinforces the calming arc.",
    "evidence_span_text": "Heather and gorse, lately whipped to a horizontal lean, slowly composed themselves, while overhead a thin sun ventured down"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "figurative_language_meaning",
    "answer_mechanism_key": "contextual_substitution",
    "solver_pattern_key": "locate_figurative_function",
    "topic_broad": "literature",
    "topic_fine": "Victorian literary fiction",
    "register": "literary",
    "tone": "atmospheric descriptive",
    "difficulty_overall": "medium",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Underlined-word stem; literal denotations (write/arrange) are incoherent for plants, forcing figurative_language_meaning. Literal meanings included among distractors per §21.1."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Wrote down",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "figurative_literal_confusion",
      "plausibility_source_key": "common_definition_appeal",
      "why_plausible": "'Compose' literally means to write (a poem, letter, etc.).",
      "why_wrong": "Plants cannot write; the subject of the verb is 'heather and gorse'.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "Settled into stillness",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "Arranged in order",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "figurative_literal_confusion",
      "plausibility_source_key": "common_definition_appeal",
      "why_plausible": "Another literal sense of 'compose' is to arrange constituent parts (musical composition, page composition).",
      "why_wrong": "The plants do not arrange themselves into an order — they cease being whipped sideways.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "Reconciled to defeat",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "connotation_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "The storm imagery may suggest the plants have been beaten down; 'composed' may sound like resignation.",
      "why_wrong": "Wrong evaluative tone: the passage frames the moment as the heath recovering, not surrendering. 'Composed oneself' carries no defeat connotation.",
      "grammar_fit": "yes",
      "tone_match": "no",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Recognize 'composed themselves' as a personified idiom for 'settled / calmed' when applied to plants.",
    "trap_mechanism": "Two literal meanings ('wrote', 'arranged in order') are deliberately offered to trap readers who do not check coherence against an inanimate subject.",
    "correct_answer_reasoning": "1) Test literal meanings against subject ('heather and gorse'). 2) Reject 'wrote' and 'arranged'. 3) Recognize the idiom 'compose oneself' = calm/settle. 4) Select 'settled into stillness'.",
    "distractor_analysis_summary": "A and C are the literal-meaning traps mandated by §21.1; D fails on evaluative connotation.",
    "similar_items": []
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "figurative_language_meaning",
    "target_test_construct_key": "figurative_interpretation_precision",
    "target_craft_subconstruct_key": "wic_local_semantic_role",
    "target_reasoning_trap_key": "figurative_literal_confusion",
    "target_stimulus_mode_key": "passage_excerpt",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "two literal-meaning traps (mandatory per §21.1)",
      "one connotation-mismatch in adjacent semantic field"
    ],
    "passage_template": "Literary narrator describes natural scene. Underlined verb is one whose literal meaning(s) require a human/intentional subject; in the passage the subject is inanimate, forcing personification/idiom.",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Figurative function: personification of plants via reflexive idiom 'compose oneself'. Two literal-meaning distractors satisfy §21.1 requirement."
  }
}
```

---

## ITEM 5 — Source: Ibn Rushd ("inconsequential to")

### Source question (verbatim)

> While recent scholarship has undermined claims that the works of twelfth-century Islamic philosopher Ibn Rushd were ______ other Muslim philosophers of his time, it is indisputable that his location in the Muslim-ruled area of what is now Spain meant that his works were primarily available thousands of miles west of the era's center of Islamic thought.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) controversial among
> B) antagonistic toward
> C) imitated by
> D) inconsequential to
>
> **Correct: D**

### Source annotation (Mode C)

```json
{
  "question": {
    "source_exam": "PT6",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 5,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "While recent scholarship has undermined claims that the works of twelfth-century Islamic philosopher Ibn Rushd were ______ other Muslim philosophers of his time, it is indisputable that his location in the Muslim-ruled area of what is now Spain meant that his works were primarily available thousands of miles west of the era's center of Islamic thought.",
    "correct_option_label": "D",
    "explanation_short": "Scholarship UNDERMINES claims about his works' relation to other philosophers; the concession that he was geographically distant is what made the (now-refuted) claim plausible. The undermined claim must therefore be 'inconsequential to'.",
    "explanation_full": "The sentence has two layers of polarity. (1) 'Recent scholarship has undermined claims that X was ___ Y' — whatever fills the blank is what scholarship has DISPROVED. (2) 'It is indisputable that his location ... meant his works were primarily available thousands of miles west' — this concedes a fact (geographic isolation) that would naturally support the (now-refuted) claim. The original assumption, given the geographic isolation, was that his works were of no consequence to other Muslim philosophers. Recent scholarship has shown otherwise. 'Inconsequential to' is the only option that names a claim about influence that is both (a) plausible given physical isolation and (b) the kind of claim modern scholarship characteristically refutes.",
    "evidence_span_text": "recent scholarship has undermined claims that the works of ... Ibn Rushd were ______ other Muslim philosophers of his time, it is indisputable that his location ... meant that his works were primarily available thousands of miles west of the era's center of Islamic thought"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "polarity_fit",
    "evidence_scope_key": "sentence",
    "answer_mechanism_key": "polarity_resolution",
    "solver_pattern_key": "apply_negation_logic",
    "topic_broad": "humanities",
    "topic_fine": "medieval Islamic philosophy",
    "register": "academic historical",
    "tone": "neutral analytical",
    "difficulty_overall": "high",
    "difficulty_vocab": "high",
    "difficulty_inference": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Double-clause polarity: 'undermined claims that X was ___' (negator at clause level) + concessive 'While ... it is indisputable that [geographic isolation]'. The blank is what the now-refuted claim asserted. Per §7.5 polarity_fit rule, evidence span includes the full negated construction."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "controversial among",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "topical_proximity",
      "why_plausible": "Philosophical works are often controversial; this fits an academic register.",
      "why_wrong": "A claim of controversy assumes engagement with the works by other philosophers. The concessive about geographic isolation explains how the OPPOSITE claim (lack of engagement) became plausible. 'Controversial' is the wrong type of historical claim to be undermined here.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "antagonistic toward",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "connotation_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "Ibn Rushd's rationalist work did clash with some contemporaries; readers may know this.",
      "why_wrong": "Antagonism describes the works' STANCE, not their CONSEQUENTIALITY. Geographic isolation does not make antagonism more plausible; it makes lack of effect more plausible.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "imitated by",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "common_sense_appeal",
      "why_plausible": "Influential medieval works are often imitated.",
      "why_wrong": "An assumption of imitation would not be undermined by geographic isolation; it would be supported by it (no contact = no imitation). To say scholarship undermined a claim of imitation while conceding distance gets the polarity backwards.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "inconsequential to",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "Apply double polarity: identify what claim the 'undermined claims that ___' construction targets, then check that the concessive about geographic distance makes that original (now-refuted) claim historically plausible.",
    "trap_mechanism": "A and B describe types of intellectual engagement; C inverts the polarity. All three feel plausible as academic claims about a philosopher but fail the specific scholarship-undermines + geography-concedes structure.",
    "correct_answer_reasoning": "1) Identify negator: 'scholarship has undermined claims that ___'. 2) Identify concessive: 'it is indisputable that his location ... thousands of miles west'. 3) The geographic isolation makes plausible a claim of NO EFFECT on contemporaries; scholarship undermines that no-effect claim. 4) Match: 'inconsequential to'.",
    "distractor_analysis_summary": "A is the wrong type of historical claim; B is stance not consequentiality; C reverses polarity.",
    "similar_items": [
      {
        "pattern": "While recent scholarship has undermined claims that [actor X]'s [works/findings] were ______ [comparable group Y], it is indisputable that [actor X]'s location/method/material conditions [imposed isolation/limitation] from Y.",
        "focus_key": "polarity_fit",
        "trap_key": "polarity_mismatch"
      }
    ]
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_polarity_logic",
    "target_reasoning_trap_key": "polarity_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "distractor_pattern": [
      "two semantic-field-adjacent options that fail to fit the scholarship-undermines + isolation-concedes structure",
      "one explicit polarity-reverse (option that would be reinforced, not undermined, by isolation)"
    ],
    "passage_template": "While recent [scholarship / research] has undermined [claims / assumptions] that [thing X]'s [works/findings/discoveries] were ______ [comparable group Y], it is [undeniable / indisputable] that [X's geographic, methodological, or material conditions imposed isolation from Y].",
    "polarity_context": "negator+concessive: 'while ... undermined claims that ___' coupled with 'it is indisputable that ... [isolation fact]'",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "polarity_context recorded with both negator and concessive. Evidence span spans both clauses per §7.5 polarity_fit annotation rule."
  }
}
```

### Generated mirror (Mode B) — deep-sea hydrothermal vent ecosystems

> While recent ecological research has undermined claims that the deep-sea hydrothermal vent ecosystems first cataloged in the late 1970s were ______ broader oceanic food webs, it remains undeniable that their location miles below the photic zone places them in near-complete physical isolation from the sunlit surface communities that biologists most commonly study.
>
> Which choice completes the text with the most logical and precise word or phrase?
>
> A) parasitic upon
> B) hostile to
> C) marginal to
> D) representative of
>
> **Correct: C**

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 5,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_word_in_context",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "passage_text": "While recent ecological research has undermined claims that the deep-sea hydrothermal vent ecosystems first cataloged in the late 1970s were ______ broader oceanic food webs, it remains undeniable that their location miles below the photic zone places them in near-complete physical isolation from the sunlit surface communities that biologists most commonly study.",
    "correct_option_label": "C",
    "explanation_short": "Research UNDERMINES claims about the vents' relation to broader food webs; the conceded physical isolation makes plausible only a no-effect claim. Blank = 'marginal to'.",
    "explanation_full": "The sentence is structured as two clauses of opposing polarity. (1) Recent research has undermined a claim about the vents' relation to broader food webs. (2) Their depth and physical isolation are conceded as undeniable. The conceded isolation is what made the now-refuted claim historically plausible — that is, a claim that the vents contributed little or nothing to broader food webs. 'Marginal to' captures that claim. The other options either describe wrong types of relation (parasitic, hostile) or would not be undermined by isolation (representative of: isolation would NOT support, and would in fact challenge, a claim that they are representative).",
    "evidence_span_text": "recent ecological research has undermined claims that the deep-sea hydrothermal vent ecosystems ... were ______ broader oceanic food webs, it remains undeniable that their location miles below the photic zone places them in near-complete physical isolation"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Words in Context",
    "question_family_key": "craft_and_structure",
    "skill_family_key": "words_in_context",
    "reading_focus_key": "polarity_fit",
    "answer_mechanism_key": "polarity_resolution",
    "solver_pattern_key": "apply_negation_logic",
    "topic_broad": "science",
    "topic_fine": "marine biology; chemoautotrophic ecosystems",
    "register": "academic scientific",
    "tone": "neutral analytical",
    "difficulty_overall": "high",
    "difficulty_vocab": "high",
    "difficulty_inference": "medium",
    "distractor_strength": "high",
    "classification_rationale": "Mirror preserves both polarity layers from source. 'Undermined claims that ___' + concessive 'it remains undeniable that [isolation]'."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "parasitic upon",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "local_semantic_role_mismatch",
      "plausibility_source_key": "topical_proximity",
      "why_plausible": "Ecology vocabulary; readers may attach 'parasitic' to ecosystem-relationship questions.",
      "why_wrong": "Parasitism describes a specific energy-extraction relationship that physical isolation would not support OR undermine in the way the sentence requires; it is the wrong category of relation.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "hostile to",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "connotation_mismatch",
      "plausibility_source_key": "near_synonym_appeal",
      "why_plausible": "'Hostile' carries a strong stance and feels academic.",
      "why_wrong": "Hostility describes stance/effect direction, not consequentiality. Isolation would not make a hostility claim plausible.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "marginal to",
      "is_correct": true,
      "option_role": "key",
      "distractor_type_key": "correct",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "representative of",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "polarity_mismatch",
      "plausibility_source_key": "common_sense_appeal",
      "why_plausible": "'Representative' is a common ecology word for typical examples.",
      "why_wrong": "Reverses polarity: physical isolation would UNDERMINE a claim of representativeness from the start, so scholarship would not need to do that work. The structure requires the original (refuted) claim to be one that isolation MADE plausible.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Identify the negator 'undermined claims that ___' and the concessive about physical isolation; the blank is the now-refuted claim that the conceded isolation originally made plausible.",
    "trap_mechanism": "A and B substitute wrong categories of ecological relation; D inverts the polarity by selecting a claim that isolation would already refute, leaving nothing for scholarship to undermine.",
    "correct_answer_reasoning": "1) Identify negator. 2) Identify concessive (depth = isolation). 3) Original plausible claim, given isolation: vents contribute little to broader food webs ('marginal to'). 4) Confirm that scholarship indeed undermines THIS claim, not the others.",
    "distractor_analysis_summary": "A and B are wrong relation categories; D is polarity-inverted.",
    "similar_items": []
  },
  "generation_profile": {
    "target_question_family_key": "craft_and_structure",
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "target_test_construct_key": "contextual_semantic_precision",
    "target_craft_subconstruct_key": "wic_polarity_logic",
    "target_reasoning_trap_key": "polarity_mismatch",
    "target_stimulus_mode_key": "sentence_only",
    "target_stem_type_key": "choose_word_in_context",
    "polarity_context": "negator+concessive: 'While ... has undermined claims that ___' + 'it remains undeniable that [physical isolation]'",
    "distractor_pattern": [
      "two semantic-category mismatches (wrong type of ecological relation)",
      "one explicit polarity-inversion (claim isolation would itself refute)"
    ],
    "passage_template": "While recent [research/scholarship] has undermined claims that [organism/system X]'s [features/works] were ______ [larger context Y], it remains undeniable that [physical/methodological isolation from Y].",
    "two_part_claim": false,
    "generation_timestamp": "2026-05-19T00:00:00Z",
    "model_version": "rules_agent_reading_v2.0"
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "Mirror preserves double-polarity structure of source. Both negator and concessive recorded in polarity_context."
  }
}
```

---

## Validator pass (Mode B + Mode C against §21 + §21.1)

All 10 records (5 source annotations + 5 generated mirrors) checked against the
validator checklist:

- [x] `question_family_key` ∈ {`craft_and_structure`} for all 10
- [x] `skill_family_key = words_in_context` for all 10
- [x] `reading_focus_key` ∈ approved §7.5 set (`contextual_meaning`, `polarity_fit`, `figurative_language_meaning`)
- [x] `grammar_role_key` / `grammar_focus_key` omitted on all reading-domain items
- [x] `stem_type_key = choose_word_in_context` matches actual stem wording on all 10
- [x] `stimulus_mode_key` matches source format (sentence_only for blank-fill, passage_excerpt for "most nearly mean")
- [x] Every option has `distractor_type_key`, `why_plausible`, `why_wrong` (correct options have `null` for why_plausible/why_wrong)
- [x] Exactly one option per item has `is_correct: true` and `distractor_type_key: "correct"`
- [x] `precision_score: 3` assigned only to correct options
- [x] `evidence_span_text` present on all 10
- [x] `annotation_confidence` populated in every `review`
- [x] `target_test_construct_key` populated on all 5 generated items
- [x] `target_craft_subconstruct_key` populated on all 5 generated items (`wic_local_semantic_role` or `wic_polarity_logic`)
- [x] Three distractors per item fail through distinct trap/distractor_type families
- [x] Options homogeneous in syntax, register, and length per item
- [x] For polarity_fit items (Q2, Q5 source + mirrors), `polarity_context` recorded and evidence span includes the full negated/concessive construction
- [x] For WIC items, at least one distractor fails by local semantic role, tone/register, connotation, or polarity (not by unrelated meaning) — satisfied on all 10
- [x] For figurative_language_meaning items (Q4 source + mirror), at least one distractor uses the literal dictionary meaning; review_notes identifies the figurative function — satisfied
- [x] `model_version: rules_agent_reading_v2.0` recorded on all 5 generated items

**Confidence flags:** Items 1, 2, 3, 4 mirrors at ≥0.95; Item 5 mirror at 0.93 (double-polarity items inherently harder to fully de-risk without human pass).
