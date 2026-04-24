# V3 Ontology Reference

This document lists all controlled vocabularies, enums, and ontology constants used by the DSAT backend. These values are enforced in the ORM, Pydantic schemas, and LLM prompts.

Source: `rules_agent_dsat_grammar_ingestion_generation_v3.md`

---

## Content Origins

| Value | Description |
|---|---|
| `official` | Official College Board material |
| `unofficial` | Third-party or user-submitted material |
| `generated` | AI-generated questions |

---

## Job Types

| Value | Description |
|---|---|
| `ingest` | Ingest raw assets into the corpus |
| `generate` | Generate new questions from source examples |
| `reannotate` | Re-run Pass 2 annotation on existing content |
| `overlap_check` | Check for overlap with official corpus |

---

## Job Statuses

The job state machine uses the following ordered statuses:

| Value | Description |
|---|---|
| `pending` | Job queued, not yet started |
| `parsing` | Parsing raw asset |
| `extracting` | Pass 1 extraction in progress |
| `generating` | Generation in progress |
| `annotating` | Pass 2 annotation in progress |
| `overlap_checking` | Overlap detection in progress |
| `validating` | Validation in progress |
| `approved` | Job completed, question approved |
| `needs_review` | Job completed, question needs admin review |
| `failed` | Job failed (terminal state) |

---

## Practice Statuses

| Value | Description |
|---|---|
| `draft` | Not yet approved for practice |
| `active` | Available for practice recall |
| `retired` | Excluded from practice recall |

---

## Overlap Statuses

| Value | Description |
|---|---|
| `none` | No overlap detected |
| `possible` | Possible overlap flagged |
| `confirmed` | Overlap confirmed by human review |

---

## Relation Types

| Value | Description |
|---|---|
| `overlaps_official` | Question overlaps with official corpus |
| `derived_from` | Derived from another question |
| `near_duplicate` | Near-duplicate of another question |
| `generated_from` | Generated from source question(s) |
| `adapted_from` | Adapted from another question |

---

## Asset Types

| Value | Description |
|---|---|
| `pdf` | Portable Document Format |
| `image` | Image file |
| `screenshot` | Screenshot capture |
| `markdown` | Markdown text |
| `json` | JSON data |
| `text` | Plain text |

---

## Change Sources

| Value | Description |
|---|---|
| `ingest` | Created via ingestion pipeline |
| `generate` | Created via generation pipeline |
| `admin_edit` | Edited by an admin user |
| `reprocess` | Reprocessed via pipeline |

---

## Stimulus Mode Keys (V3 Section 3.1)

| Value | Description |
|---|---|
| `sentence_only` | Single sentence, no passage |
| `passage_excerpt` | Short passage excerpt |
| `prose_single` | Single prose passage |
| `prose_paired` | Paired prose passages |
| `prose_plus_table` | Prose passage with table |
| `prose_plus_graph` | Prose passage with graph |
| `notes_bullets` | Bulleted notes |
| `poem` | Poem or verse |

---

## Stem Type Keys (V3 Section 3.2)

| Value | Description |
|---|---|
| `complete_the_text` | Complete the text |
| `choose_main_idea` | Choose the main idea |
| `choose_main_purpose` | Choose the main purpose |
| `choose_structure_description` | Choose the structure description |
| `choose_sentence_function` | Choose the sentence function |
| `choose_likely_response` | Choose the likely response |
| `choose_best_support` | Choose the best support |
| `choose_best_quote` | Choose the best quote |
| `choose_best_completion_from_data` | Choose best completion from data |
| `choose_best_grammar_revision` | Choose best grammar revision |
| `choose_best_transition` | Choose best transition |
| `choose_best_notes_synthesis` | Choose best notes synthesis |

---

## Grammar Role Keys (V3 Section 5)

| Value | Description |
|---|---|
| `sentence_boundary` | Sentence boundary issues |
| `agreement` | Subject-verb or pronoun agreement |
| `verb_form` | Verb tense and form |
| `modifier` | Modifier placement and logic |
| `punctuation` | Punctuation usage |
| `parallel_structure` | Parallel structure |
| `pronoun` | Pronoun case and clarity |
| `expression_of_ideas` | Expression of ideas |

---

## Grammar Focus Keys by Role (V3 Section 6)

### sentence_boundary

- `sentence_fragment`
- `comma_splice`
- `run_on_sentence`
- `sentence_boundary`

### agreement

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`
- `affirmative_agreement`

### verb_form

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation`

### modifier

- `modifier_placement`
- `comparative_structures`
- `logical_predication`
- `relative_pronouns`

### punctuation

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`

### parallel_structure

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

### pronoun

- `pronoun_case`
- `pronoun_clarity`
- `pronoun_antecedent_agreement`

### expression_of_ideas

- `redundancy_concision`
- `precision_word_choice`
- `register_style_consistency`
- `logical_relationships`
- `emphasis_meaning_shifts`
- `data_interpretation_claims`
- `transition_logic`

---

## Syntactic Trap Keys (V3 Section 9)

| Value | Description |
|---|---|
| `none` | No syntactic trap present |
| `nearest_noun_attraction` | Nearest noun attraction |
| `garden_path` | Garden path sentence |
| `early_clause_anchor` | Early clause anchor |
| `nominalization_obscures_subject` | Nominalization obscures subject |
| `interruption_breaks_subject_verb` | Interruption breaks subject-verb link |
| `long_distance_dependency` | Long-distance dependency |
| `pronoun_ambiguity` | Pronoun ambiguity |
| `scope_of_negation` | Scope of negation ambiguity |
| `modifier_attachment_ambiguity` | Modifier attachment ambiguity |
| `presupposition_trap` | Presupposition trap |
| `temporal_sequence_ambiguity` | Temporal sequence ambiguity |
| `multiple` | Multiple traps present |

---

## Distractor Type Keys (V3 Section 10.2)

| Value | Description |
|---|---|
| `semantic_imprecision` | Semantically imprecise |
| `logical_mismatch` | Logically mismatched |
| `scope_error` | Scope error |
| `tone_mismatch` | Tone mismatch |
| `grammar_error` | Contains a grammar error |
| `punctuation_error` | Contains a punctuation error |
| `transition_mismatch` | Transition mismatch |
| `data_misread` | Data misread |
| `goal_mismatch` | Goal mismatch |
| `partially_supported` | Partially supported |
| `overstatement` | Overstatement |
| `understatement` | Understatement |
| `rhetorical_irrelevance` | Rhetorically irrelevant |
| `correct` | Correct answer (not a distractor) |

---

## Plausibility Source Keys (V3 Section 10.3)

| Value | Description |
|---|---|
| `nearest_noun_attraction` | Nearest noun attraction |
| `punctuation_style_bias` | Punctuation style bias |
| `auditory_similarity` | Auditory similarity |
| `grammar_fit_only` | Grammar fit only |
| `formal_register_match` | Formal register match |
| `common_idiom_pull` | Common idiom pull |
| `none` | No special plausibility source |

---

## Answer Mechanism Keys (V3 Section 3.3)

| Value | Description |
|---|---|
| `rule_application` | Apply a grammar rule directly |
| `pattern_matching` | Pattern matching |
| `evidence_location` | Locate evidence in passage |
| `inference` | Inference from passage |
| `data_synthesis` | Synthesize data from notes/tables |

---

## Solver Pattern Keys (V3 Section 3.3)

| Value | Description |
|---|---|
| `apply_grammar_rule_directly` | Apply grammar rule directly |
| `locate_error_zone` | Locate the error zone |
| `compare_register` | Compare register/formality |
| `evaluate_transition` | Evaluate transition logic |
| `synthesize_notes` | Synthesize notes |
| `eliminate_by_boundary` | Eliminate by boundary |

---

## Student Failure Mode Keys (V3 Section 21.3)

| Value | Description |
|---|---|
| `nearest_noun_reflex` | Nearest noun reflex |
| `comma_fix_illusion` | Comma fix illusion |
| `formal_word_bias` | Formal word bias |
| `longer_answer_bias` | Longer answer bias |
| `punctuation_intimidation` | Punctuation intimidation |
| `surface_similarity_bias` | Surface similarity bias |
| `scope_blindness` | Scope blindness |
| `modifier_hitchhike` | Modifier hitchhike |
| `chronological_assumption` | Chronological assumption |
| `extreme_word_trap` | Extreme word trap |
| `overreading` | Overreading |
| `underreading` | Underreading |
| `grammar_fit_only` | Grammar fit only |
| `register_confusion` | Register confusion |
| `pronoun_anchor_error` | Pronoun anchor error |
| `parallel_shape_bias` | Parallel shape bias |
| `transition_assumption` | Transition assumption |
| `idiom_memory_pull` | Idiom memory pull |
| `false_precision` | False precision |

---

## Distractor Distance Keys (V3 Section 21.2)

| Value | Description |
|---|---|
| `wide` | Distractor is far from correct answer |
| `moderate` | Moderate distance |
| `tight` | Distractor is very close to correct answer |

---

## Difficulty Keys (V3 Section 3.3)

| Value | Description |
|---|---|
| `low` | Low difficulty |
| `medium` | Medium difficulty |
| `high` | High difficulty |

---

## Frequency Bands (V3 Section 3.3)

| Value | Description |
|---|---|
| `very_high` | Very high frequency |
| `high` | High frequency |
| `medium` | Medium frequency |
| `low` | Low frequency |
| `very_low` | Very low frequency |

---

## Tense Register Keys (V3 Section 17.6)

| Value | Description |
|---|---|
| `narrative_past` | Narrative past |
| `scientific_general_present` | Scientific general present |
| `historical_past` | Historical past |
| `study_procedure_past` | Study procedure past |
| `established_finding_present` | Established finding present |
| `mixed_with_explicit_shift` | Mixed with explicit shift |

---

## Passage Architecture Keys (V3 Section 22)

| Value | Description |
|---|---|
| `science_setup_finding_implication` | Science: setup, finding, implication |
| `science_hypothesis_method_result` | Science: hypothesis, method, result |
| `history_claim_evidence_limitation` | History: claim, evidence, limitation |
| `history_assumption_revision` | History: assumption, revision |
| `literature_observation_interpretation_shift` | Literature: observation, interpretation shift |
| `literature_character_conflict_reveal` | Literature: character, conflict, reveal |
| `economics_theory_exception_example` | Economics: theory, exception, example |
| `economics_problem_solution_tradeoff` | Economics: problem, solution, tradeoff |
| `rhetoric_claim_counterclaim_resolution` | Rhetoric: claim, counterclaim, resolution |
| `notes_fact_selection_contrast` | Notes: fact, selection, contrast |

---

## Question Family Keys

| Value | Description |
|---|---|
| `conventions_grammar` | Conventions of Grammar |
| `expression_of_ideas` | Expression of Ideas |
| `craft_and_structure` | Craft and Structure |
| `information_and_ideas` | Information and Ideas |
