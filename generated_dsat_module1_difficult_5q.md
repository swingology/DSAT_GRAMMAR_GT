# DSAT Reading & Writing — Module 1 — Generated Difficult Items (5)

**Source spec:** `rules_agent_dsat_grammar_ingestion_generation_v3.md`
**Ground-truth reference:** SAT Practice Test 4 (Digital), Section 1, Module 1 (Q1–Q33)
**Generation date:** 2026-04-22
**Target difficulty:** `difficulty_overall: high` across the set
**Coverage rationale:** spans the five highest-difficulty Module-1 families — (1) words-in-context with polarity trap, (2) SEC colon vs. semicolon boundary, (3) SEC subject–verb agreement with long interruption, (4) transition logic under contrast trap, (5) logical completion requiring multi-step inference.

---

## Question 1 — Words in Context (polarity / double-negative trap)

*Modeled after PT4 M1 Q3 ("less ______ in many other animals") and Q4 ("It is by no means ______ to recognize…").*

**Passage**

Archaeologist Lynn Meskell's argument that early monumental architecture primarily served political rather than religious functions has proven remarkably ______; although her thesis was fiercely contested when first published, it now anchors most scholarly interpretations of sites such as Göbekli Tepe and Çatalhöyük.

**Which choice completes the text with the most logical and precise word or phrase?**

- A) contentious
- B) provisional
- C) durable
- D) obscure

**Correct answer:** C) durable

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 1,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text with the most logical and precise word or phrase?",
    "correct_option_label": "C",
    "explanation_short": "The semicolon clause establishes that Meskell's thesis, once contested, now anchors the field, so the blank requires a word meaning lasting or resilient.",
    "explanation_full": "The structure 'although X, Y' signals concession: the thesis was contested early but now anchors most interpretations. The blank must therefore capture resilience over time. 'Durable' (C) fits precisely. 'Contentious' (A) captures only the initial-contest clause and contradicts 'now anchors.' 'Provisional' (B) implies tentative or temporary, the opposite of what 'now anchors most scholarly interpretations' indicates. 'Obscure' (D) contradicts the thesis's current dominance.",
    "evidence_span_text": "remarkably ______; ... now anchors most scholarly interpretations"
  },
  "classification": {
    "domain": "Craft and Structure",
    "skill_family": "Craft and Structure",
    "subskill": "words in context — abstract-quality adjective with concession structure",
    "question_family_key": "craft_and_structure",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": "scope_of_negation",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "history",
    "topic_fine": "archaeology",
    "reading_scope": "sentence-level",
    "reasoning_demand": "polarity inference across concession",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "classification_rationale": "Item tests precision of word choice where the concession structure ('although X, Y') inverts the polarity cue nearest the blank."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "contentious",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "semantic_imprecision",
      "plausibility_source_key": "common_idiom_pull",
      "why_plausible": "The word 'contested' in the concession clause strongly primes 'contentious.'",
      "why_wrong": "It describes only the initial-contest phase, not the thesis's current status of anchoring the field.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "provisional",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "Academic register matches; 'provisional' commonly collocates with 'thesis.'",
      "why_wrong": "Provisional means tentative or temporary, contradicting 'now anchors most scholarly interpretations.'",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "durable",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Captures the lasting acceptance signaled by 'now anchors most scholarly interpretations.'",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "obscure",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "grammar_fit_only",
      "why_plausible": "Archaeological sites may sound 'obscure' to general readers.",
      "why_wrong": "The thesis is explicitly dominant in current scholarship, the opposite of obscure.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Word choice must reconcile the concession clause's polarity with the main clause's claim of current dominance.",
    "trap_mechanism": "The word 'contested' adjacent to the blank pulls test-takers toward 'contentious,' which describes only the early phase.",
    "correct_answer_reasoning": "'Durable' names the lasting quality that reconciles 'was contested' with 'now anchors.'",
    "distractor_analysis_summary": "A echoes local wording; B and D reverse the polarity of the main clause."
  },
  "generation_profile": {
    "target_grammar_role_key": null,
    "target_grammar_focus_key": null,
    "target_syntactic_trap_key": "scope_of_negation",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "high",
    "passage_template": "[Scholar]'s argument that [thesis] has proven remarkably ______; although [concession], it now [dominance claim].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.93,
    "needs_human_review": false,
    "review_notes": "Difficulty driven by polarity inversion plus academic-register distractors."
  }
}
```

---

## Question 2 — SEC: Colon vs. Semicolon vs. Comma (sentence boundary with elaboration)

*Modeled after PT4 M1 Q23 (sampler/stacks) and Q25 (species, both native and nonnative). Tests whether the second clause elaborates on an antecedent, requiring a colon rather than a semicolon or period.*

**Passage**

The supermassive black hole at the center of the Milky Way, Sagittarius A*, exhibits an unusual phenomenon ______ flares of X-ray radiation appear at roughly daily intervals, a rhythm that astronomers have yet to explain.

**Which choice completes the text so that it conforms to the conventions of Standard English?**

- A) phenomenon;
- B) phenomenon,
- C) phenomenon.
- D) phenomenon:

**Correct answer:** D) phenomenon:

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 2,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "correct_option_label": "D",
    "explanation_short": "A colon introduces the explanation of what the 'unusual phenomenon' is, following a grammatically complete independent clause.",
    "explanation_full": "The first clause is independent and ends on the abstract noun 'phenomenon,' which is then specified by the second clause ('flares … appear … daily intervals'). A colon is the correct punctuation to introduce such a specifying elaboration, so D is correct. A (semicolon) is wrong because a semicolon merely equates two independent clauses; it does not flag the second as definitional. B (comma) creates a comma splice. C (period) is grammatically possible but breaks the tight appositive-like relationship the writer has set up between 'phenomenon' and its specification, and fails to capitalize 'flares' if the period were retained — making it the inferior punctuation choice.",
    "evidence_span_text": "phenomenon : flares"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Sentence Boundaries",
    "subskill": "colon introducing elaboration after independent clause",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "colon_dash_use",
    "secondary_grammar_focus_keys": ["semicolon_use", "sentence_boundary", "comma_splice"],
    "syntactic_trap_key": "none",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "eliminate_by_boundary",
    "topic_broad": "science",
    "topic_fine": "astrophysics",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "sentence_boundary > punctuation",
    "classification_rationale": "All four options produce valid sentence-boundary behavior, but only a colon correctly signals that the second clause specifies the noun 'phenomenon.'"
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "phenomenon;",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "semicolon_use",
      "why_plausible": "A semicolon is grammatically permissible between two independent clauses and sounds formal.",
      "why_wrong": "A semicolon merely equates the clauses; it does not mark the second as a definition of 'phenomenon.' A colon is required for this explanatory relationship.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2
    },
    {
      "option_label": "B",
      "option_text": "phenomenon,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "comma_splice",
      "why_plausible": "A comma is the default punctuation and can look natural between the noun and its elaboration.",
      "why_wrong": "A comma alone cannot join two independent clauses; this produces a comma splice.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "phenomenon.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "sentence_boundary",
      "why_plausible": "A period correctly ends an independent clause.",
      "why_wrong": "A period would require capitalizing 'flares,' which is not in the underlined options; even assuming capitalization, a period severs the definitional tie between 'phenomenon' and its specification.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "phenomenon:",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "A colon following an independent clause introduces a specifying elaboration.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "A colon follows an independent clause to introduce a list, quotation, or elaboration of a preceding noun.",
    "trap_mechanism": "The semicolon distractor is tempting because both clauses are independent, but the rule requires a punctuation mark that signals specification, not mere equivalence.",
    "correct_answer_reasoning": "The second clause specifies what the 'unusual phenomenon' is, so a colon is the only punctuation that marks that semantic relation.",
    "distractor_analysis_summary": "A equates rather than specifies; B is a comma splice; C severs the definitional tie (and requires capitalization not offered)."
  },
  "generation_profile": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "colon_dash_use",
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "medium",
    "target_distractor_pattern": [
      "semicolon that equates but does not specify",
      "comma that produces a comma splice",
      "period that severs definitional relation"
    ],
    "passage_template": "[Subject] exhibits an unusual [abstract noun] ______ [specifying independent clause].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.92,
    "needs_human_review": false,
    "review_notes": "Clean colon vs. semicolon item. Semicolon is the high-strength distractor."
  }
}
```

---

## Question 3 — SEC: Subject–Verb Agreement across a long interrupting phrase

*Modeled after PT4 M1 Q22 (triangle representing the mountain ... among the few defined figures). Long intervening prepositional + participial material hides the true singular subject.*

**Passage**

The extensive collection of manuscripts attributed to the fifteenth-century Italian humanist Poggio Bracciolini, including copies rediscovered in monastic libraries scattered across France, Germany, and northern Italy, ______ essential to the modern understanding of classical rhetoric.

**Which choice completes the text so that it conforms to the conventions of Standard English?**

- A) are
- B) have been
- C) remain
- D) is

**Correct answer:** D) is

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 3,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "correct_option_label": "D",
    "explanation_short": "The singular subject 'collection' takes the singular verb 'is,' despite multiple intervening plural nouns.",
    "explanation_full": "The grammatical subject is the singular noun 'collection,' not 'manuscripts,' 'copies,' or 'libraries.' Therefore the verb must be singular: 'is' (D). A ('are') and C ('remain') are plural and attracted by the nearest plural noun. B ('have been') is plural in auxiliary agreement ('has been' would be needed) and also introduces an unnecessary tense shift to present perfect where simple present suffices to state an ongoing scholarly reality.",
    "evidence_span_text": "The ... collection ... is essential"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Form, Structure, and Sense",
    "subskill": "subject-verb agreement with long intervening phrase containing multiple plural nouns",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "agreement",
    "grammar_focus_key": "subject_verb_agreement",
    "secondary_grammar_focus_keys": ["verb_tense_consistency"],
    "syntactic_trap_key": "long_distance_dependency",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "history",
    "topic_fine": "Renaissance humanism",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application under long-distance dependency",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "subject_verb_agreement > noun_countability",
    "classification_rationale": "Tests singular S-V agreement where three plural nouns ('manuscripts,' 'copies,' 'libraries') intervene between subject and verb."
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
      "why_plausible": "Three plural nouns immediately precede the verb slot.",
      "why_wrong": "The subject is the singular 'collection,' not 'libraries.' A plural verb creates a S-V agreement error.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "have been",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "Present perfect sounds scholarly and matches 'rediscovered' in tense feel.",
      "why_wrong": "'have' is plural and does not agree with 'collection'; 'has been' would be the singular form, not offered.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "remain",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "'Remain essential' is a natural academic collocation.",
      "why_wrong": "'remain' is the plural form; the singular subject 'collection' requires 'remains.'",
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
      "why_plausible": "Singular verb correctly agreeing with the singular subject 'collection.'",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    }
  ],
  "reasoning": {
    "primary_rule": "A singular subject takes a singular verb, regardless of intervening plural nouns.",
    "trap_mechanism": "Three plural nouns sit between the singular subject 'collection' and the verb slot, tempting plural agreement by attraction.",
    "correct_answer_reasoning": "'The ... collection ... is essential' is the minimal grammatical skeleton.",
    "distractor_analysis_summary": "A, B, and C are all plural forms attracted by the intervening material."
  },
  "generation_profile": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "long_distance_dependency",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "target_distractor_pattern": [
      "plural verb attracted by nearest noun",
      "plural auxiliary in present perfect",
      "plural verb in a natural collocation with 'essential'"
    ],
    "passage_template": "The [singular collection noun] of [plural N1] ..., including [plural N2] in [plural N3], ______ [predicate].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Three distinct plural attractors maximize the long-distance dependency trap."
  }
}
```

---

## Question 4 — Transition (contrast with embedded concession)

*Modeled after PT4 M1 Q28 (Mauna Loa / Pūhāhonu) and Q29 (Coleridge-Taylor). Contrast transition must survive a misleading temporal cue that nudges toward 'Consequently.'*

**Passage**

For much of the twentieth century, historians credited Johannes Gutenberg with inventing movable-type printing around 1450, an innovation they portrayed as without precedent. ______ recent scholarship has shown that Korean artisans were using movable metal type nearly two centuries earlier to produce works such as the *Jikji*, a Buddhist anthology printed in 1377.

**Which choice completes the text with the most logical transition?**

- A) Consequently,
- B) Similarly,
- C) However,
- D) Moreover,

**Correct answer:** C) However,

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 4,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "choose_best_transition",
    "prompt_text": "Which choice completes the text with the most logical transition?",
    "correct_option_label": "C",
    "explanation_short": "The second sentence contradicts the first's claim of no precedent, so a contrast transition ('However') is required.",
    "explanation_full": "The first sentence asserts that Gutenberg's innovation was 'without precedent.' The second sentence presents a Korean precedent two centuries earlier, directly undercutting that claim. A contrast transition is therefore required. 'However' (C) is correct. 'Consequently' (A) signals causal result and is wrong because the second sentence does not follow from the first. 'Similarly' (B) signals reinforcement and is wrong because the sentences contradict rather than echo each other. 'Moreover' (D) signals addition of parallel evidence, not contradiction.",
    "evidence_span_text": "without precedent. However, recent scholarship has shown that Korean artisans ... nearly two centuries earlier"
  },
  "classification": {
    "domain": "Expression of Ideas",
    "skill_family": "Transitions",
    "subskill": "contrast transition overriding temporal cue",
    "question_family_key": "expression_of_ideas",
    "grammar_role_key": "expression_of_ideas",
    "grammar_focus_key": "transition_logic",
    "syntactic_trap_key": "presupposition_trap",
    "evidence_scope_key": "paragraph",
    "evidence_location_key": "transition_zone",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "evaluate_transition",
    "topic_broad": "history",
    "topic_fine": "history of printing",
    "reading_scope": "cross-sentence",
    "reasoning_demand": "logical relationship inference",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "medium",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "medium",
    "distractor_strength": "high",
    "disambiguation_rule_applied": "transition_logic > conjunction_usage",
    "classification_rationale": "Tests which transition captures the logical relation between a claim of uniqueness and counter-evidence."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Consequently,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "'Consequently' pairs with 'have credited' and may sound like scholarly progression.",
      "why_wrong": "The second sentence refutes the first; it is not a consequence of it.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "Similarly,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "Both sentences discuss printing, which may cue 'Similarly.'",
      "why_wrong": "The sentences express opposed, not similar, claims about precedence.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "C",
      "option_text": "However,",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Marks the contrast between the claim of 'no precedent' and the cited Korean precedent.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "D",
      "option_text": "Moreover,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "'Moreover' signals scholarly escalation and sounds register-appropriate.",
      "why_wrong": "'Moreover' adds a parallel point; the second sentence undermines the first.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "Transition words must match the logical relation between the two clauses.",
    "trap_mechanism": "Shared topic (printing history) and register pull students toward additive or causal transitions.",
    "correct_answer_reasoning": "Sentence 1 claims unique invention; sentence 2 supplies prior evidence. That is a direct contradiction, so 'However' is required.",
    "distractor_analysis_summary": "A inverts the logical direction; B and D both treat the sentences as parallel rather than opposed."
  },
  "generation_profile": {
    "target_grammar_role_key": "expression_of_ideas",
    "target_grammar_focus_key": "transition_logic",
    "target_syntactic_trap_key": "presupposition_trap",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "causal transition reversing direction",
      "similarity transition treating sentences as parallel",
      "additive transition masquerading as contrast"
    ],
    "passage_template": "[Claim of uniqueness/priority]. ______ [counter-evidence predating the claim].",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.94,
    "needs_human_review": false,
    "review_notes": "All three distractors are register-matched; strength comes from logical mismatch, not tone."
  }
}
```

---

## Question 5 — Logical Completion (multi-step inference)

*Modeled after PT4 M1 Q18 (Pompeii cupid / Venus). Final blank must be a claim that correctly follows from two premises — difficulty comes from distractors that are each one logical step off.*

**Passage**

Paleontologist Stephen Brusatte argues that *Tyrannosaurus rex* likely possessed at least some feathers. His reasoning relies on phylogenetic bracketing — the principle that if two closely related groups both share a trait, their common ancestor almost certainly had that trait as well. Because *Yutyrannus*, a close tyrannosauroid relative, and modern birds, which descend from the same theropod lineage, both display feathered integument, Brusatte concludes that ______

**Which choice most logically completes the text?**

- A) feathers must have evolved independently in *Yutyrannus* and in modern birds.
- B) the presence of feathers in *T. rex* is more plausible than their absence.
- C) *T. rex* must have shed its feathers before reaching adulthood.
- D) phylogenetic bracketing cannot be applied reliably to extinct species.

**Correct answer:** B) the presence of feathers in *T. rex* is more plausible than their absence.

### V3 Annotation

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 5,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice most logically completes the text?",
    "correct_option_label": "B",
    "explanation_short": "Phylogenetic bracketing licenses the inference that a trait shared by two flanking relatives was probably present in the intermediate species.",
    "explanation_full": "The passage defines phylogenetic bracketing and states that two species bracketing T. rex share feathered integument. The conclusion the argument licenses is that T. rex probably also had feathers — i.e., their presence is more plausible than their absence (B). A contradicts the bracketing principle, which would treat independent evolution as the less parsimonious explanation. C introduces an ad-hoc claim about ontogenetic shedding that the passage provides no basis for. D repudiates the very principle that the passage endorses as the basis for the conclusion.",
    "evidence_span_text": "if two closely related groups both share a trait, their common ancestor almost certainly had that trait ... Yutyrannus ... and modern birds ... both display feathered integument"
  },
  "classification": {
    "domain": "Expression of Ideas",
    "skill_family": "Rhetorical Synthesis",
    "subskill": "logical completion requiring multi-step inference from a stated principle",
    "question_family_key": "expression_of_ideas",
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "syntactic_trap_key": "presupposition_trap",
    "evidence_scope_key": "paragraph",
    "evidence_location_key": "closing_sentence",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "evaluate_transition",
    "topic_broad": "science",
    "topic_fine": "paleontology",
    "reading_scope": "paragraph-level",
    "reasoning_demand": "multi-step inference from stated principle",
    "register": "formal academic",
    "tone": "objective",
    "difficulty_overall": "high",
    "difficulty_reading": "high",
    "difficulty_grammar": "low",
    "difficulty_inference": "high",
    "difficulty_vocab": "high",
    "distractor_strength": "high",
    "classification_rationale": "The correct completion must be the single inference licensed by the stated principle plus the empirical premise."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "feathers must have evolved independently in Yutyrannus and in modern birds.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "formal_register_match",
      "why_plausible": "Independent evolution is a familiar biological concept and sounds scientifically sophisticated.",
      "why_wrong": "It contradicts the bracketing principle endorsed in the passage, which infers shared ancestry rather than independent origin.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "B",
      "option_text": "the presence of feathers in T. rex is more plausible than their absence.",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "why_plausible": "Directly applies bracketing to the bracketed taxon, T. rex.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": "T. rex must have shed its feathers before reaching adulthood.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "partially_supported",
      "plausibility_source_key": "common_idiom_pull",
      "why_plausible": "Echoes a popular-science framing of adult T. rex as scaly, which might sound familiar.",
      "why_wrong": "No premise in the passage supports an ontogenetic shedding claim; it is an unsupported leap.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    },
    {
      "option_label": "D",
      "option_text": "phylogenetic bracketing cannot be applied reliably to extinct species.",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "logical_mismatch",
      "plausibility_source_key": "grammar_fit_only",
      "why_plausible": "Sounds like an appropriately cautious methodological disclaimer.",
      "why_wrong": "It rejects the very principle the passage endorses as the basis of Brusatte's conclusion.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1
    }
  ],
  "reasoning": {
    "primary_rule": "A conclusion must follow from all stated premises: a definitional principle plus its satisfied conditions.",
    "trap_mechanism": "Distractors either accept the premises but reject the conclusion, or introduce unstated ad-hoc claims.",
    "correct_answer_reasoning": "Bracketing + shared feathered integument in both flanking taxa → feathered T. rex is the most parsimonious inference.",
    "distractor_analysis_summary": "A contradicts bracketing; C adds ungrounded ontogeny; D rejects the endorsed principle."
  },
  "generation_profile": {
    "target_grammar_role_key": null,
    "target_grammar_focus_key": null,
    "target_syntactic_trap_key": "presupposition_trap",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "medium",
    "target_distractor_pattern": [
      "contradicts the endorsed principle",
      "adds unsupported ad-hoc mechanism",
      "rejects the principle outright"
    ],
    "passage_template": "[Scientist] argues that [taxon] likely had [trait]. The reasoning relies on [principle]. Because [relative A] and [relative B] both display [trait], [scientist] concludes that ______",
    "generation_timestamp": "2026-04-22T00:00:00Z",
    "model_version": "rules_agent_v3.0"
  },
  "review": {
    "annotation_confidence": 0.9,
    "needs_human_review": false,
    "review_notes": "Strong item; each distractor is one logical move off the correct inference."
  }
}
```

---

## Answer Key

| # | Type | Correct | Focus key | Trap key |
|---|------|---------|-----------|----------|
| 1 | Words in context | C | `precision_word_choice` (craft_and_structure) | `scope_of_negation` |
| 2 | SEC — punctuation | D | `colon_dash_use` | none (rule-based) |
| 3 | SEC — agreement | D | `subject_verb_agreement` | `long_distance_dependency` |
| 4 | Transition | C | `transition_logic` | `presupposition_trap` |
| 5 | Logical completion | B | `logical_relationships` | `presupposition_trap` |

## Generation notes

Per V3 §17.12 (difficulty calibration), all five items sit at `difficulty_overall: high` because distractor strength is high across the set, not because every dimension is maxed — each item has at least one high-strength distractor that mirrors a genuine SAT trap family (nearest-noun attraction, register-matched wrong transition, ad-hoc conclusion, concession-polarity flip, colon-vs-semicolon confusion). Per V3 §17.11, all four options in each item use a single option format (fill-in-blank word, punctuation-only, or completion clause). Per V3 §17.8, every classification with a conflict between two plausible labels (Q2, Q3, Q4) records the `disambiguation_rule_applied`.
