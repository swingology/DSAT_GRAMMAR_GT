# Seed Data Addendum: Lookup Table Seeds for M-022–M-028

**Date:** 2026-04-21
**Purpose:** Define seed data for all lookup tables created in M-003 that are seeded in M-022–M-028 (not shown in PRD doc)
**Sources:** GROUND_TRUTH_GRAMMAR.md, DSAT_Verbal_Master_Taxonomy_v2.md

---

## lookup_syntactic_interruption (4 keys)

Measures how much an intervening structure breaks a grammatical connection. Distinct from `syntactic_trap` — interruption is about structural distance; trap is about misleading patterns.

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `none` | No Interruption | Direct subject-verb or modifier-head connection | 10 |
| `minor` | Minor Interruption | Short prepositional phrase or single modifier between connected elements | 20 |
| `moderate` | Moderate Interruption | Appositive phrase, short parenthetical, or coordinate expansion between connected elements | 30 |
| `severe` | Severe Interruption | Long interrupting clause, stacked modifiers, or multiple parentheticals between connected elements | 40 |

---

## lookup_syntactic_trap (13 keys)

Source: GROUND_TRUTH_GRAMMAR.md Part 7

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `none` | No Trap | No notable syntactic trap present | 10 |
| `nearest_noun_attraction` | Nearest-Noun Attraction | Verb matches closest noun instead of head noun | 20 |
| `garden_path` | Garden Path | Initial parse leads down wrong path requiring mid-sentence revision | 30 |
| `early_clause_anchor` | Early Clause Anchor | Initial subordinate clause causes anchoring on wrong subject for main clause | 40 |
| `nominalization_obscures_subject` | Nominalization Obscures Subject | Heavy nominalization hides agent or action | 50 |
| `interruption_breaks_subject_verb` | Interruption Breaks Subject-Verb | Long interrupting phrase between subject and verb causes agreement errors | 60 |
| `long_distance_dependency` | Long-Distance Dependency | Grammatical relationship spans many words; high working memory load | 70 |
| `pronoun_ambiguity` | Pronoun Ambiguity | Pronoun could refer to multiple antecedents; discourse context required | 80 |
| `scope_of_negation` | Scope of Negation | Negation word has wide scope but students apply it narrowly, or vice versa | 90 |
| `modifier_attachment_ambiguity` | Modifier Attachment Ambiguity | Participial or prepositional phrase could attach to multiple NPs | 100 |
| `presupposition_trap` | Presupposition Trap | Sentence presupposes something students incorrectly accept as stated | 110 |
| `temporal_sequence_ambiguity` | Temporal Sequence Ambiguity | Order of events unclear due to mixed tense or non-linear narration | 120 |
| `multiple` | Multiple Traps | More than one syntactic trap present | 999 |

---

## lookup_distractor_type (4 keys)

Source: Taxonomy v2 Section 4 — 4 major distractor families

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `meaning_trap` | Meaning Trap | Distractor exploits semantic confusion: wrong scope, wrong relationship, imprecise synonym | 10 |
| `grammar_trap` | Grammar Trap | Distractor exploits grammatical confusion: agreement bait, tense bait, formal-but-wrong punctuation | 20 |
| `style_trap` | Style Trap | Distractor exploits stylistic confusion: wrong register, wordiness, tone mismatch, redundancy | 30 |
| `logic_trap` | Logic Trap | Distractor exploits logical confusion: reversed causation, misread concession, true-but-irrelevant detail | 40 |

---

## lookup_distractor_subtype (25 keys)

Source: Taxonomy v2 Section 4.1–4.5

### Meaning Traps (8)

| Key | Display Name | Parent Type | Sort Order |
|---|---|---|---|
| `broadly_related_imprecise` | Broadly Related But Imprecise | meaning_trap | 10 |
| `opposite_meaning` | Opposite Meaning | meaning_trap | 20 |
| `partially_supported_incomplete` | Partially Supported But Incomplete | meaning_trap | 30 |
| `too_extreme' | Too Extreme (Overstatement) | meaning_trap | 40 |
| `wrong_scope' | Wrong Scope | meaning_trap | 50 |
| `wrong_relationship' | Wrong Relationship | meaning_trap | 60 |
| `echoes_wording_shifted_meaning' | Echoes Wording, Shifted Meaning | meaning_trap | 70 |
| `sophisticated_but_weakens_logic' | Sophisticated But Weakens Logic | meaning_trap | 80 |

### Grammar Traps (4)

| Key | Display Name | Parent Type | Sort Order |
|---|---|---|---|
| `agreement_bait` | Agreement Bait | grammar_trap | 10 |
| `tense_bait` | Tense Bait | grammar_trap | 20 |
| `formal_punctuation_error` | Formal Punctuation That Is Wrong | grammar_trap | 30 |
| `modifier_attachment_trap` | Modifier Attachment Trap | grammar_trap | 40 |

### Style Traps (5)

| Key | Display Name | Parent Type | Sort Order |
|---|---|---|---|
| `too_casual` | Too Casual | style_trap | 10 |
| `too_wordy` | Too Wordy | style_trap | 20 |
| `too_vague` | Too Vague | style_trap | 30 |
| `tone_mismatch` | Tone Mismatch | style_trap | 40 |
| `redundant_nearby_wording` | Redundant with Nearby Wording | style_trap | 50 |

### Logic Traps (5)

| Key | Display Name | Parent Type | Sort Order |
|---|---|---|---|
| `reverses_cause_effect` | Reverses Cause and Effect | logic_trap | 10 |
| `confuses_contrast_support` | Confuses Contrast with Support | logic_trap | 20 |
| `misreads_concession` | Misreads Concession | logic_trap | 30 |
| `substitutes_detail_for_point` | Substitutes Detail for Main Point | logic_trap | 40 |
| `sophistication_bias` | Sophistication Bias | logic_trap | 50 |

### DSAT-Specific Patterns (3)

| Key | Display Name | Parent Type | Sort Order |
|---|---|---|---|
| `all_grammatical_only_one_precise` | All Grammatical, Only One Precise | meaning_trap | 90 |
| `all_plausible_only_one_supported` | All Plausible, Only One Text-Supported | meaning_trap | 100 |
| `numerically_true_not_responsive` | Numerically True But Not Responsive | logic_trap | 60 |

---

## lookup_distractor_construction (8 keys)

Source: Taxonomy v2 Section 4.5 + 4.6 — how the distractor is built

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `semantic_overlap` | Semantic Overlap | Shares partial meaning with correct answer | 10 |
| `antonym_swap` | Antonym Swap | Replaces key word with opposite | 20 |
| `scope_shift` | Scope Shift | Broadens or narrows the correct answer's claim | 30 |
| `register_substitution` | Register Substitution | Same idea in wrong formality level | 40 |
| `passage_echo` | Passage Echo | Uses passage wording in wrong context | 50 |
| `valence_match` | Valence Match | Matches emotional direction but wrong content | 60 |
| `category_mismatch` | Category Mismatch | Right general category, wrong specific type | 70 |
| `connotation_shift` | Connotation Shift | Denotation fits, connotation doesn't | 80 |

---

## lookup_semantic_relation (8 keys)

Source: Taxonomy v2 Section 4.7

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `near_synonym_wrong_scope` | Near Synonym, Wrong Scope | Similar meaning, different application | 10 |
| `grammatically_valid_unsupported` | Grammatically Valid, Unsupported | Fits sentence but not supported by text | 20 |
| `contradiction` | Contradiction | Opposite of what passage states | 30 |
| `tone_fit_logic_fail` | Tone Fit, Logic Fail | Right register, wrong reasoning | 40 |
| `too_broad` | Too Broad | General when specific needed | 50 |
| `too_narrow` | Too Narrow | Specific when general needed | 60 |
| `wrong_connotation` | Wrong Connotation | Denotation fits, connotation doesn't | 70 |
| `wrong_collocation` | Wrong Collocation | Word pairing that doesn't co-occur in standard usage | 80 |

---

## lookup_plausibility_source (6 keys)

Source: Taxonomy v2 Section 4.6 — why the wrong answer attracts

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `grammar_fit_only` | Grammar Fit Only | Grammatically valid but semantically empty or wrong | 10 |
| `topical_association` | Topical Association | Related to passage topic but not to specific question | 20 |
| `formal_register_match` | Formal Register Match | Sounds academic but misses meaning | 30 |
| `partial_semantic_overlap` | Partial Semantic Overlap | Shares some meaning but not enough | 40 |
| `echoes_passage_wording` | Echoes Passage Wording | Uses words from passage in wrong context | 50 |
| `valence_match` | Positive/Negative Valence Match | Right emotional direction, wrong specific content | 60 |

---

## lookup_eliminability (3 keys)

| Key | Display Name | Description | Sort Order |
|---|---|---|---|
| `easy` | Easy to Eliminate | Clearly wrong upon careful reading | 10 |
| `moderate` | Moderate to Eliminate | Requires rule application or evidence check | 20 |
| `hard` | Hard to Eliminate | Very close to correct; requires precise distinction | 30 |

---

## Style / Difficulty Lookup Tables

### lookup_syntactic_complexity (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `simple` | Simple (one clause) | 10 |
| `compound` | Compound (two independent clauses) | 20 |
| `complex` | Complex (independent + dependent) | 30 |
| `compound_complex` | Compound-Complex | 40 |
| `multi_embedded` | Multi-Embedded (deep nesting) | 50 |

### lookup_lexical_tier (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `conversational` | Conversational | 10 |
| `general` | General Academic | 20 |
| `academic` | Academic | 30 |
| `technical` | Technical | 40 |
| `specialized` | Specialized | 50 |

### lookup_inference_distance (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `literal` | Literal | 10 |
| `near_inference` | Near Inference | 20 |
| `moderate_inference` | Moderate Inference | 30 |
| `deep_inference` | Deep Inference | 40 |
| `abstract_synthesis` | Abstract Synthesis | 50 |

### lookup_evidence_distribution (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `single_sentence` | Single Sentence | 10 |
| `adjacent_sent` | Adjacent Sentences | 20 |
| `same_paragraph` | Same Paragraph | 30 |
| `across_passage` | Across Passage | 40 |
| `paired_passages` | Paired Passages | 50 |

### lookup_noun_phrase_complexity (3 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `simple` | Simple NP | 10 |
| `moderate` | Moderate NP (1-2 modifiers) | 20 |
| `complex` | Complex NP (3+ modifiers, stacking) | 30 |

### lookup_vocabulary_profile (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `k1` | K1 (most frequent 1000) | 10 |
| `k2` | K2 (next 1000) | 20 |
| `academic_word` | Academic Word List | 30 |
| `domain_specific` | Domain-Specific | 40 |
| `technical_specialized` | Technical / Specialized | 50 |

### lookup_cohesion_device (6 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `lexical_chain` | Lexical Chain (repetition/synonym) | 10 |
| `pronoun_reference` | Pronoun Reference | 20 |
| `transitional_marker` | Transitional Marker (however, therefore) | 30 |
| `conjunction` | Conjunction (and, but, because) | 40 |
| `ellipsis_substitution` | Ellipsis / Substitution | 50 |
| `parallel_structure_cohesion` | Parallel Structure Cohesion | 60 |

### lookup_epistemic_stance (5 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `certain` | Certain (will, must, always) | 10 |
| `probable` | Probable (should, likely, probably) | 20 |
| `possible` | Possible (may, might, could) | 30 |
| `hedged` | Hedged (appears to, seems to, suggests) | 40 |
| `tentative` | Tentative (it is possible that, one might argue) | 50 |

### lookup_transitional_logic (6 keys)

| Key | Display Name | Sort Order |
|---|---|---|
| `addition` | Addition (furthermore, moreover) | 10 |
| `contrast` | Contrast (however, nevertheless) | 20 |
| `cause_effect` | Cause/Effect (therefore, consequently) | 30 |
| `temporal` | Temporal (then, subsequently, meanwhile) | 40 |
| `exemplification` | Exemplification (for example, for instance) | 50 |
| `concession` | Concession (admittedly, of course) | 60 |