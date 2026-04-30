# PT10 Sec02 Mod02 — Hard Generated Questions

**Source passage register:** `sat-practice-test-10-digital-sec02-mod02.pdf`
**Generation rules:** `rules_agent_dsat_grammar_ingestion_generetion_v5.md` (v5) / v6
**Difficulty:** High (all 4)
**Date generated:** 2026-04-29

---

## Question 1

**Focus key:** `unnecessary_internal_punctuation`
**Grammar role:** `punctuation`

### Passage

André Taylor's spray-coating method for producing electron transport layers in perovskite solar ______ more consistent power conversion efficiency than vacuum-deposited alternatives in laboratory conditions.

### Stem

Which choice completes the text so that it conforms to the conventions of Standard English?

### Options

- **A)** cells, delivers
- **B)** cells delivers
- **C)** cells; delivers
- **D)** cells—delivers

**Correct answer: B**

### Full JSON Annotation

```json
{
  "classification": {
    "domain": "SEC",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "unnecessary_internal_punctuation",
    "stem_type_key": "blank_completion",
    "stimulus_mode_key": "passage_only",
    "difficulty_overall": "high",
    "test_format_key": "nondigital_linear_accommodation",
    "position_band": "Q18-Q25"
  },
  "generation_profile": {
    "target_grammar_focus_key": "unnecessary_internal_punctuation",
    "target_syntactic_unit": "subject_verb",
    "target_trap": "long_distance_dependency",
    "passage_tense_register_key": "simple_present",
    "passage_domain": "materials_science",
    "passage_topic": "perovskite solar cells, spray-coating method",
    "blank_position": "inside_subject_noun_phrase",
    "blank_completion_type": "noun_plus_verb_boundary",
    "subject_length_words": 17,
    "subject_text": "André Taylor's spray-coating method for producing electron transport layers in perovskite solar cells",
    "verb_text": "delivers"
  },
  "reasoning": {
    "correct_rule": "No punctuation may appear between the grammatical subject and its finite verb. The 17-word noun phrase 'André Taylor's spray-coating method … in perovskite solar cells' is the undivided subject; inserting any punctuation mark before 'delivers' severs a required syntactic unit.",
    "distractor_analysis": {
      "A": {
        "text": "cells, delivers",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "syntactic_trap",
        "plausibility_source_key": "length_fatigue",
        "option_error_focus_key": "unnecessary_internal_punctuation",
        "why_plausible": "After 17 words, the reader expects a breath-pause before the verb; the comma feels like it marks the end of a complex phrase.",
        "why_wrong": "A comma between a grammatical subject and its main verb is never permitted in Standard English, regardless of subject length.",
        "grammar_fit": "ungrammatical",
        "tone_match": "neutral",
        "precision_score": 9,
        "student_failure_mode_key": "long_distance_dependency",
        "distractor_distance": 0.9,
        "distractor_competition_score": 0.88,
        "synthesis_distractor_failure": null
      },
      "B": {
        "text": "cells delivers",
        "distractor_type_key": "correct",
        "semantic_relation_key": null,
        "plausibility_source_key": null,
        "option_error_focus_key": null,
        "why_plausible": null,
        "why_wrong": null,
        "grammar_fit": "grammatical",
        "tone_match": "neutral",
        "precision_score": null,
        "student_failure_mode_key": null,
        "distractor_distance": null,
        "distractor_competition_score": null,
        "synthesis_distractor_failure": null
      },
      "C": {
        "text": "cells; delivers",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "punctuation_upgrade",
        "plausibility_source_key": "semicolon_confusion",
        "option_error_focus_key": "sentence_boundary",
        "why_plausible": "Students who know a comma is wrong may reach for the semicolon as a 'stronger' alternative, unaware it requires an independent clause on each side.",
        "why_wrong": "A semicolon must connect two independent clauses. 'André Taylor's spray-coating method … in perovskite solar cells' is not a clause; it is a noun phrase.",
        "grammar_fit": "ungrammatical",
        "tone_match": "neutral",
        "precision_score": 7,
        "student_failure_mode_key": "comma_fix_illusion",
        "distractor_distance": 0.7,
        "distractor_competition_score": 0.72,
        "synthesis_distractor_failure": null
      },
      "D": {
        "text": "cells—delivers",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "punctuation_upgrade",
        "plausibility_source_key": "dash_emphasis_heuristic",
        "option_error_focus_key": "unnecessary_internal_punctuation",
        "why_plausible": "Em-dashes can signal an abrupt interruption or special emphasis; students may see the long subject as a kind of parenthetical preamble.",
        "why_wrong": "A dash between subject and verb is no more permissible than a comma; it still breaks a required syntactic unit.",
        "grammar_fit": "ungrammatical",
        "tone_match": "neutral",
        "precision_score": 6,
        "student_failure_mode_key": "formal_word_bias",
        "distractor_distance": 0.65,
        "distractor_competition_score": 0.68,
        "synthesis_distractor_failure": null
      }
    }
  },
  "review": {
    "all_four_plausible": true,
    "ear_test_resolvable": false,
    "correct_uniquely_grammatical": true,
    "distractors_share_failure_mode": false,
    "validator_checklist_passed": true
  }
}
```

---

## Question 2

**Focus key:** `verb_tense_consistency` / `literary_present`
**Grammar role:** `verb_tense`

### Passage

Lewis Carroll's 1889 novel *Sylvie and Bruno* is rarely discussed alongside his better-known works, yet it offers a surprisingly pointed commentary on Victorian social hierarchies. In Carroll's novel, the narrator ______ this political chaos from the vantage point of the Warden's open window, rendering the spectacle absurd rather than alarming.

### Stem

Which choice completes the text so that it conforms to the conventions of Standard English?

### Options

- **A)** witnesses
- **B)** witnessed
- **C)** had witnessed
- **D)** was witnessing

**Correct answer: A**

### Full JSON Annotation

```json
{
  "classification": {
    "domain": "SEC",
    "grammar_role_key": "verb_tense",
    "grammar_focus_key": "verb_tense_consistency",
    "stem_type_key": "blank_completion",
    "stimulus_mode_key": "passage_only",
    "difficulty_overall": "high",
    "test_format_key": "nondigital_linear_accommodation",
    "position_band": "Q18-Q25",
    "subtype_note": "literary_present"
  },
  "generation_profile": {
    "target_grammar_focus_key": "verb_tense_consistency",
    "passage_tense_register_key": "literary_present",
    "passage_domain": "literary_criticism",
    "passage_topic": "Lewis Carroll, Sylvie and Bruno (1889), Victorian social commentary",
    "anchor_tense_in_passage": "simple_present",
    "anchor_verb_example": "is, offers",
    "blank_verb": "witnesses",
    "target_trap": "temporal_sequence_ambiguity",
    "trap_trigger": "explicit_year_1889_in_passage",
    "distractor_synthesis_failures": [
      "witnessed — past tense triggered by 1889 date; violates literary present convention",
      "had witnessed — past perfect triggered by sequence cue 'from the vantage point'; violates register",
      "was witnessing — progressive aspect suggests ongoing event in real time; violates literary present"
    ]
  },
  "reasoning": {
    "correct_rule": "When a passage discusses events inside a literary work, the literary-present convention requires simple present regardless of the work's publication date. The passage anchors in literary present ('is,' 'offers'); the blank must match.",
    "distractor_analysis": {
      "A": {
        "text": "witnesses",
        "distractor_type_key": "correct",
        "grammar_fit": "grammatical",
        "tone_match": "neutral",
        "student_failure_mode_key": null,
        "distractor_distance": null,
        "distractor_competition_score": null,
        "synthesis_distractor_failure": null
      },
      "B": {
        "text": "witnessed",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "tense_shift",
        "plausibility_source_key": "date_anchor_pull",
        "option_error_focus_key": "verb_tense_consistency",
        "why_plausible": "The year 1889 in the preceding sentence signals a historical event; students default to past tense when a date appears.",
        "why_wrong": "Literary present requires simple present when narrating events within a fictional work, regardless of publication year.",
        "grammar_fit": "contextually_wrong",
        "tone_match": "neutral",
        "precision_score": 9,
        "student_failure_mode_key": "temporal_sequence_ambiguity",
        "distractor_distance": 0.92,
        "distractor_competition_score": 0.91,
        "synthesis_distractor_failure": null
      },
      "C": {
        "text": "had witnessed",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "tense_shift",
        "plausibility_source_key": "sequence_cue_misread",
        "option_error_focus_key": "verb_tense_consistency",
        "why_plausible": "The phrase 'from the vantage point' suggests the narrator occupied a prior position before narrating; students interpret this as a past-before-past relationship.",
        "why_wrong": "No sequence relationship across time periods exists inside a fictional narration under literary present; past perfect is disallowed.",
        "grammar_fit": "contextually_wrong",
        "tone_match": "neutral",
        "precision_score": 7,
        "student_failure_mode_key": "tense_proximity_pull",
        "distractor_distance": 0.75,
        "distractor_competition_score": 0.73,
        "synthesis_distractor_failure": null
      },
      "D": {
        "text": "was witnessing",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "aspect_shift",
        "plausibility_source_key": "progressive_scene_heuristic",
        "option_error_focus_key": "verb_tense_consistency",
        "why_plausible": "The passage describes a vivid visual scene; past progressive feels appropriate for events unfolding in the background.",
        "why_wrong": "Progressive aspect in past tense breaks both the literary-present convention and tense consistency with the anchor verbs.",
        "grammar_fit": "contextually_wrong",
        "tone_match": "neutral",
        "precision_score": 6,
        "student_failure_mode_key": "ear_test_pass",
        "distractor_distance": 0.68,
        "distractor_competition_score": 0.65,
        "synthesis_distractor_failure": null
      }
    }
  },
  "review": {
    "all_four_plausible": true,
    "ear_test_resolvable": false,
    "correct_uniquely_grammatical": true,
    "distractors_share_failure_mode": false,
    "validator_checklist_passed": true
  }
}
```

---

## Question 3

**Focus key:** `verb_form` / `finite_verb_in_relative_clause`
**Grammar role:** `verb_form`

### Passage

Eleanor Roosevelt and Hansa Mehta are among the principal drafters of the 1948 Universal Declaration of Human Rights, which Roosevelt and Mehta ______ in close collaboration with representatives from nearly sixty nations over the preceding two years.

### Stem

Which choice completes the text so that it conforms to the conventions of Standard English?

### Options

- **A)** drafting
- **B)** drafted
- **C)** had drafted
- **D)** were drafting

**Correct answer: B**

### Full JSON Annotation

```json
{
  "classification": {
    "domain": "SEC",
    "grammar_role_key": "verb_form",
    "grammar_focus_key": "finite_verb_in_relative_clause",
    "stem_type_key": "blank_completion",
    "stimulus_mode_key": "passage_only",
    "difficulty_overall": "high",
    "test_format_key": "nondigital_linear_accommodation",
    "position_band": "Q18-Q25"
  },
  "generation_profile": {
    "target_grammar_focus_key": "finite_verb_in_relative_clause",
    "relative_clause_introducer": "which",
    "blank_verb_base": "draft",
    "correct_finite_form": "drafted",
    "target_trap": "garden_path",
    "trap_trigger": "participial_form_drafters_in_adjacent_clause",
    "passage_tense_register_key": "literary_present",
    "passage_domain": "history_human_rights",
    "passage_topic": "Eleanor Roosevelt, Hansa Mehta, UN Declaration of Human Rights (1948)",
    "distractor_synthesis_failures": [
      "drafting — nonfinite present participle; echoes 'drafters' from main clause, producing garden-path illusion of grammaticality",
      "had drafted — past perfect introduces unwanted temporal sequencing inside a relative clause already anchored by 'over the preceding two years'",
      "were drafting — progressive form suggests incomplete background action; contradicts 'principal drafters' (completed role) in main clause"
    ]
  },
  "reasoning": {
    "correct_rule": "A relative clause introduced by 'which' requires a finite verb. The nonfinite present participle 'drafting' cannot serve as the main verb of a relative clause; it would leave the clause without a predicate.",
    "distractor_analysis": {
      "A": {
        "text": "drafting",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "nonfinite_for_finite",
        "plausibility_source_key": "garden_path",
        "option_error_focus_key": "finite_verb_in_relative_clause",
        "why_plausible": "The word 'drafters' appears three words earlier in the same sentence; students who absorb the participial form from context may re-deploy 'drafting' without noticing the clause has no finite verb.",
        "why_wrong": "A relative clause introduced by 'which' must contain a finite verb. 'drafting' is a nonfinite present participle and cannot serve as the predicate of a relative clause.",
        "grammar_fit": "ungrammatical",
        "tone_match": "neutral",
        "precision_score": 9,
        "student_failure_mode_key": "parallel_shape_bias",
        "distractor_distance": 0.93,
        "distractor_competition_score": 0.92,
        "synthesis_distractor_failure": null
      },
      "B": {
        "text": "drafted",
        "distractor_type_key": "correct",
        "grammar_fit": "grammatical",
        "tone_match": "neutral",
        "student_failure_mode_key": null,
        "distractor_distance": null,
        "distractor_competition_score": null,
        "synthesis_distractor_failure": null
      },
      "C": {
        "text": "had drafted",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "tense_overcorrection",
        "plausibility_source_key": "sequence_cue_misread",
        "option_error_focus_key": "verb_tense_consistency",
        "why_plausible": "'Over the preceding two years' suggests a completed action prior to another past moment; students reach for past perfect to mark this anteriority.",
        "why_wrong": "The passage is in literary/historical present ('are among the principal drafters'). Introducing past perfect creates a tense inconsistency. Simple past 'drafted' correctly anchors the relative clause.",
        "grammar_fit": "contextually_wrong",
        "tone_match": "neutral",
        "precision_score": 7,
        "student_failure_mode_key": "tense_proximity_pull",
        "distractor_distance": 0.72,
        "distractor_competition_score": 0.70,
        "synthesis_distractor_failure": null
      },
      "D": {
        "text": "were drafting",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "aspect_shift",
        "plausibility_source_key": "progressive_scene_heuristic",
        "option_error_focus_key": "verb_tense_consistency",
        "why_plausible": "The collaborative, multi-year process feels like an ongoing background activity; past progressive captures that sense of extended work-in-progress.",
        "why_wrong": "Progressive aspect implies the action was not completed; the passage's 'principal drafters' and the fixed 1948 date mark the drafting as a completed event.",
        "grammar_fit": "contextually_wrong",
        "tone_match": "neutral",
        "precision_score": 6,
        "student_failure_mode_key": "ear_test_pass",
        "distractor_distance": 0.65,
        "distractor_competition_score": 0.62,
        "synthesis_distractor_failure": null
      }
    }
  },
  "review": {
    "all_four_plausible": true,
    "ear_test_resolvable": false,
    "correct_uniquely_grammatical": true,
    "distractors_share_failure_mode": false,
    "validator_checklist_passed": true
  }
}
```

---

## Question 4

**Focus key:** `transition_logic` / `result_consequence`
**Grammar role:** `expression_of_ideas`

### Passage

Sequoyah completed his Cherokee syllabary in 1821 after more than a decade of solitary work. His writing system spread rapidly through Cherokee communities, initially carried by travelers and later taught in formal schools. ______, within a decade, literacy rates among the Cherokee had reached levels that rivaled those of many European populations at the time.

### Stem

Which choice completes the text with the most logical transition?

### Options

- **A)** Fittingly,
- **B)** In turn,
- **C)** Consequently,
- **D)** Indeed,

**Correct answer: C**

### Full JSON Annotation

```json
{
  "classification": {
    "domain": "SEC",
    "grammar_role_key": "expression_of_ideas",
    "grammar_focus_key": "transition_logic",
    "stem_type_key": "blank_completion",
    "stimulus_mode_key": "passage_only",
    "difficulty_overall": "high",
    "test_format_key": "nondigital_linear_accommodation",
    "position_band": "Q26-Q30",
    "transition_subtype_key": "result_consequence"
  },
  "generation_profile": {
    "target_grammar_focus_key": "transition_logic",
    "target_transition_subtype_key": "result_consequence",
    "passage_domain": "history_linguistics",
    "passage_topic": "Sequoyah, Cherokee syllabary, literacy rates",
    "logical_relationship": "The rapid spread of the syllabary directly caused the high literacy rates; the third sentence is the outcome of the second.",
    "distractor_transition_subtypes": {
      "A": "appropriateness",
      "B": "causal_chain",
      "D": "emphasis_support"
    },
    "distractor_synthesis_failures": [
      "Fittingly — marks appropriateness or poetic justice, not direct causation; tempts students who see the literacy achievement as a 'fitting' reward for Sequoyah's work",
      "In turn — marks a causal chain where A→B→C, implying an intermediate step; literacy rates are the direct result of spread, not a further downstream effect",
      "Indeed — marks confirmation or emphasis, not causation; tempts students who read the third sentence as amplifying the second rather than resulting from it"
    ]
  },
  "reasoning": {
    "correct_rule": "The third sentence states the outcome (high literacy rates) of the event described in the second sentence (rapid spread of the syllabary). The logical relationship is direct causation; the required transition signals result or consequence.",
    "distractor_analysis": {
      "A": {
        "text": "Fittingly,",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "appropriateness_for_causation",
        "plausibility_source_key": "narrative_framing",
        "option_error_focus_key": "transition_logic",
        "why_plausible": "The high literacy rates feel like a deserved outcome given Sequoyah's decade of solitary work; 'Fittingly' matches the emotional arc of the passage.",
        "why_wrong": "The relationship between syllabary spread and literacy rates is causal, not evaluative. 'Fittingly' signals authorial commentary on appropriateness, not a logical consequence.",
        "grammar_fit": "grammatical",
        "tone_match": "contextually_wrong",
        "precision_score": 9,
        "student_failure_mode_key": "topic_association",
        "distractor_distance": 0.88,
        "distractor_competition_score": 0.87,
        "transition_subtype_key": "appropriateness",
        "synthesis_distractor_failure": null
      },
      "B": {
        "text": "In turn,",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "causal_chain_for_direct_result",
        "plausibility_source_key": "chain_sequence_heuristic",
        "option_error_focus_key": "transition_logic",
        "why_plausible": "'In turn' suggests one development leading to another, which broadly fits a passage about an invention spreading and then producing a social outcome.",
        "why_wrong": "'In turn' implies an intermediate step in a sequential chain (A→B, and B→C), but the relationship here is direct: the spread of the syllabary is the immediate cause of rising literacy. No intervening step is implied.",
        "grammar_fit": "grammatical",
        "tone_match": "contextually_wrong",
        "precision_score": 8,
        "student_failure_mode_key": "false_agreement",
        "distractor_distance": 0.82,
        "distractor_competition_score": 0.80,
        "transition_subtype_key": "causal_chain",
        "synthesis_distractor_failure": null
      },
      "C": {
        "text": "Consequently,",
        "distractor_type_key": "correct",
        "grammar_fit": "grammatical",
        "tone_match": "neutral",
        "transition_subtype_key": "result_consequence",
        "student_failure_mode_key": null,
        "distractor_distance": null,
        "distractor_competition_score": null,
        "synthesis_distractor_failure": null
      },
      "D": {
        "text": "Indeed,",
        "distractor_type_key": "plausible_error",
        "semantic_relation_key": "emphasis_for_causation",
        "plausibility_source_key": "amplification_heuristic",
        "option_error_focus_key": "transition_logic",
        "why_plausible": "The high literacy rates are a striking fact that could be read as confirming or intensifying the claim about rapid spread; 'Indeed' marks that intensification.",
        "why_wrong": "'Indeed' signals that the next statement confirms, amplifies, or provides evidence for what was just said — not that it resulted from it. The passage establishes causation, not confirmation.",
        "grammar_fit": "grammatical",
        "tone_match": "contextually_wrong",
        "precision_score": 7,
        "student_failure_mode_key": "overreach",
        "distractor_distance": 0.74,
        "distractor_competition_score": 0.72,
        "transition_subtype_key": "emphasis_support",
        "synthesis_distractor_failure": null
      }
    }
  },
  "review": {
    "all_four_plausible": true,
    "ear_test_resolvable": false,
    "correct_uniquely_correct": true,
    "distractors_share_failure_mode": false,
    "validator_checklist_passed": true
  }
}
```

---

## Summary Table

| # | Focus key | Syntactic trap | Tightest distractor | Difficulty |
|---|-----------|---------------|---------------------|------------|
| 1 | `unnecessary_internal_punctuation` | `long_distance_dependency` — 17-word subject before verb | **A** `cells, delivers` (comma between subject and verb) | High |
| 2 | `verb_tense_consistency` / `literary_present` | `temporal_sequence_ambiguity` — 1889 date pulls to past | **B** `witnessed` (past tense triggered by publication year) | High |
| 3 | `finite_verb_in_relative_clause` | `garden_path` — "drafting" echoed from adjacent "drafters" | **A** `drafting` (nonfinite participle carried from prior noun) | High |
| 4 | `transition_logic` / `result_consequence` | All three distractors exploit distinct relationship misreadings | **A** `Fittingly,` (causation misread as appropriateness) | High |
