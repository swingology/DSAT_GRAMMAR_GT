# Proposed Canonical Vocabularies for DSAT Reading and Writing

**Status: Design proposal — not an active vocabulary or schema migration.**

**Baseline established 2026-09-06:** [STANDARD.md](STANDARD.md) is the v1.0.0
authority for official terminology, preserved internal keys, collision policy,
and migration records. Its versioned vocabulary directory contains the College
Board hierarchy, full compatibility snapshot, and explicit crosswalk. Candidate
terms below remain proposals; they do not become active through this document.

This document reviews `CANONICAL_VOCABULARIES.md` and proposes a more comprehensive, organized ontology for ingestion, generation, explanation, and review. The priority is fine-grained grammar, authentic writing styles, syntactic traps, and competitive distractors. All new keys below are candidates until defined, evidenced, reviewed, and promoted. Existing keys retain their current meanings until an explicit migration.

## 1. Main recommendation

Organize the ontology around six questions:

1. **What skill is tested?** Official domain, official skill, internal focus, and decisive rule.
2. **What is present in the text?** Sentence anatomy, grammatical features, discourse relations, and evidence spans.
3. **How is the text written?** Genre, register, voice, syntax, information flow, and rhetorical architecture.
4. **Why is each option right or wrong?** Correctness, violated constraint, error mechanism, and decisive evidence.
5. **Why might someone choose a wrong option?** Plausibility cue, structural trap, and hypothesized misconception.
6. **How trustworthy is the record?** Annotation provenance, uncertainty, review findings, and measured performance.

Keep operational states in a separate namespace. A job status is useful application vocabulary but does not describe a reading or writing construct.

Comprehensiveness should come from composable dimensions and explicit relationships, not an indefinitely growing flat list of highly specific labels. A new key should enable a useful distinction in annotation, generation, teaching, or evaluation.

## 2. Evidence and scope

Reviewed local sources:

- `CANONICAL_VOCABULARIES.md`: the supplied 49-category catalog.
- `rules_agent_dsat_grammar_ingestion_generation_v8.md`: taxonomy structure, option analysis, sentence anatomy (§D.10), and quality protocols.
- `rules_agent_dsat_reading_v3.md`: taxonomy structure and passage style guidance (§22).
- `grammar_rules_todo.md`: existing proposal to separate stem wording from skill and answer form.
- `RULES_ANATOMY.md`: architectural overview; references to older reading/grammar versions make it unsuitable as sole authority for current versions.
- `scripts/gen_vocab.py`: header describing the amendment and compiled-manifest workflow.

Official alignment: College Board organizes Reading and Writing into four domains. Standard English Conventions includes Boundaries and Form, Structure, and Sense; Expression of Ideas includes Transitions and Rhetorical Synthesis. The reading domains cover contextual vocabulary, structure/purpose, cross-text reasoning, central ideas/details, evidence, and inference. These official groupings anchor the proposed hierarchy. The detailed grammar, style, trap, and distractor keys below are **project proposals**, not an official College Board taxonomy. [College Board Reading and Writing specifications](https://satsuite.collegeboard.org/k12-educators/about/alignment/reading)

This is a document and rule-reference review, not a complete runtime audit or an empirical count of released questions. No proposed key is claimed to be frequent merely because it seems pedagogically useful.

## 3. Specific problems in the current catalog

| Finding | Concrete evidence | Improvement |
|---|---|---|
| Grammar distractors lack resolution | `grammar_error` and `punctuation_error` coexist with very specific reading/data errors | Add rule-linked grammar error families and concrete option-level subtypes |
| Axes are mixed | `STEM_TYPE_KEYS` contains wording forms, skills, and operations | Separate stem template, task operation, skill, stimulus, and answer form |
| Hierarchy is not strictly a tree | `pronoun_antecedent_agreement` appears under agreement and pronoun | Give concepts stable IDs; permit multiple relations while declaring one reporting parent |
| Correctness is an error category | `correct` appears in `DISTRACTOR_TYPE_KEYS` | Store correctness independently; correct options have no error labels |
| Multi-trap information is lost | `SYNTACTIC_TRAP_KEYS` includes `multiple` | Use a list of specific traps with one optional primary trap |
| Absence and uncertainty are blurred | `none`, null, and mandatory non-null trap policy | Distinguish assessed absence, unknown, and not applicable |
| Granularity varies sharply | `present_research` versus `identify_statistical_authorship_method` | Factor synthesis into operation, object, audience, and required content |
| Style is underrepresented | Tense/register bundles and topic-specific architecture labels dominate | Introduce independent style dimensions and measured syntax features |
| Anatomy is absent from this catalog | Grammar §D.10 defines span tags outside the supplied inventory | Catalog the anatomy layer explicitly, with corrected definitions |
| Labels overlap without boundaries | `tone_mismatch`/`tone_register_mismatch`; `overreach`/`scope_error`/`overstatement` | Define inclusion/exclusion tests before deciding aliases |
| Process policy is embedded in vocabulary | Required trap roles and lifecycle values appear alongside semantic categories | Separate ontology, validation policy, and workflow registries |
| Authoring instructions conflict | Catalog says edit this Markdown; generator header says approved rule amendments feed the manifest | Document one authoritative promotion path before implementation |

A repeated string in separate dimensions is not automatically wrong. A structural trap and the resulting option error can be related without being identical concepts. Use namespaced IDs and explicit relations rather than blindly deduplicating strings.

## 4. Proposed information architecture

| Layer / namespace | Main contents | Typical attachment |
|---|---|---|
| `assessment` | Domain, skill, task operation, target construct | Question |
| `grammar` | Rule family, rule focus, grammatical features | Question, clause, option |
| `anatomy` | Clause/phrase types, syntactic functions, dependency links | Span and relation |
| `discourse` | Logical relations, rhetorical moves, claim scope | Span pair, sentence, passage |
| `style` | Genre, register, voice, information flow, syntax profile | Passage and sentence |
| `item` | Stem template, stimulus layout, answer form, blank position | Question |
| `error` | Why an option fails the task | Option |
| `trap` | Structural or reasoning condition that invites an error | Span, question, option link |
| `plausibility` | Observable cue making an option attractive | Option |
| `misconception` | Hypothesized faulty strategy or rule belief | Option design; separately, learner evidence |
| `evidence` | Rule application, source spans, notes, data cells | Annotation assertion |
| `quality` | Ambiguity, fidelity, factuality, option competition | Review finding |
| `operations` | Jobs, assets, publication states, retries | Workflow record |

### 4.1 Stable term records

Every term needs more than a key:

```yaml
id: error.agreement.intervening_noun_number
label: Verb agrees with an intervening noun
status: candidate
introduced_in: proposal_v1
definition: The option uses a verb number matching an intervening noun rather than the subject head.
include_when: A conflicting intervening noun and the actual agreement controller are both identified.
exclude_when: The verb has the wrong number but no intervening noun explains the choice.
reporting_parent: error.agreement
related_rules: [grammar.subject_verb_agreement]
related_traps: [trap.nearest_noun_attraction]
applicable_entities: [option]
example: The collection of maps are valuable.
nonexample: The collection are valuable.
aliases: []
evidence_refs: []
```

The example demonstrates the mechanism, not official SAT provenance. `evidence_refs` remains empty until real reviewed evidence is attached. Term status and evidence strength are separate fields.

### 4.2 Cardinality and uncertainty

- One official domain and primary skill per classified item; unresolved ingestion may retain null plus a review state.
- One primary tested focus; zero or more secondary concepts. Merely appearing in a passage does not make a concept tested.
- Multiple anatomy and style observations per passage.
- One primary error and optional secondary errors per wrong option.
- Zero or more traps and plausibility sources, each linked to evidence.
- Preserve `annotation_state`: `resolved`, `unknown`, `not_applicable`, `needs_review`.
- `resolved` plus an empty list means a reviewer assessed the field and found no instances. Unknown must not be encoded as an empty list or `none`.
- Do not force a nontrivial trap into every grammar question. Straightforward rule application is valid.

## 5. Assessment alignment and item form

Retain current `question_family_key` values during migration. Add an official reporting crosswalk:

| Existing family | Official reporting domain | Skill layer |
|---|---|---|
| `conventions_grammar` | Standard English Conventions | `boundaries`, `form_structure_and_sense` |
| `expression_of_ideas` | Expression of Ideas | `transitions`, `rhetorical_synthesis` |
| `craft_and_structure` | Craft and Structure | Existing three reading skill families |
| `information_and_ideas` | Information and Ideas | Existing central ideas/details, evidence, inference families |

Internal concepts may cross these reporting groups. A transition word used in a punctuation question is not sufficient evidence to classify the item as Transitions. Classify by the decision required to select the answer.

Separate these fields:

- `stem_template_key`: stable wording pattern, following the direction of `grammar_rules_todo.md`.
- `task_operation_key`: `complete`, `identify`, `interpret`, `infer`, `support`, `weaken`, `illustrate`, `compare`, `synthesize`.
- `answer_form_key`: `word`, `phrase`, `punctuation_sequence`, `clause`, `sentence`, `quotation`, `claim_about_data`.
- `text_configuration_key`: `single_text`, `paired_texts`, `notes`.
- `text_genre_key`: separate prose/poetry/literary dimensions from layout.
- `support_asset_keys`: `table`, `bar_graph`, `line_graph`, `scatterplot` as candidate types requiring supported rendering and evidence.
- `target_locator`: span IDs or insertion anchor; distinguish a blank from an underlined target.

Do not infer skill solely from stem wording. Do not import the TODO's frequency claims or rare forms into production without source IDs and counts.

## 6. Grammar ontology: families and detailed candidate concepts

Use a broad family, a teachable focus, and construction features. Do not create a new focus for every combination of sentence structure and trap.

The following are candidate internal concepts. Their inclusion here does not establish that each is a standalone current DSAT testing point. Use `scope_status`: `official_skill_aligned`, `supporting_annotation`, or `experimental_extension`, with source evidence required before assigning the first status to a detailed leaf.

### 6.1 Clause completeness and boundaries

| Candidate focus | Distinction to represent |
|---|---|
| `independent_clause_completion` | A complete clause versus an unfinished structure |
| `missing_finite_predicate` | A participle or infinitive does not supply the required finite predicate |
| `dependent_clause_fragment` | Subordination leaves no independent clause |
| `relative_clause_only_fragment` | A noun plus its relative clause lacks a main predicate |
| `fused_independent_clauses` | Independent clauses meet without an appropriate boundary |
| `comma_splice` | A comma alone joins independent clauses |
| `independent_clause_coordination` | Clause structure supports coordinated joining |
| `compound_predicate_continuity` | A shared subject governs coordinated predicates |
| `subordinate_main_clause_boundary` | Distinguish dependent–independent from independent–independent joining |
| `conjunctive_adverb_boundary` | An adverb such as however does not itself coordinate clauses |

Construction features: clause count, finite-verb count, coordination level, subordinator position, interrupted clause, and blank at versus inside a boundary.

### 6.2 Punctuation by function

Punctuation identity alone is too coarse. Add functions:

- `supplement_delimitation`: set off a nonessential phrase or clause.
- `paired_delimiter_completion`: close a supplement consistently with its opening and context.
- `restrictive_element_integration`: keep an identifying element integrated.
- `appositive_restrictiveness`: determine whether the naming phrase identifies or supplements.
- `title_name_integration`: evaluate the actual title/name construction, not a universal comma rule.
- `colon_introduces_explanation`, `colon_introduces_list`: require a complete introductory clause in the intended construction.
- `dash_introduces_elaboration`: distinguish elaboration from paired interruption.
- `series_item_separation`, `complex_series_separation`: represent list structure and embedded punctuation.
- `introductory_element_boundary`: apply construction-specific punctuation rather than “every introductory phrase needs a comma.”
- `subject_predicate_no_split`, `verb_object_no_split`, `preposition_object_no_split`: identify an unjustified break inside a syntactic unit.
- `direct_question_termination`, `embedded_question_declarative_termination`: distinguish sentence force from embedded interrogative content.

Keep hyphenation and quotation mechanics as supporting/extension concepts until their intended assessment role is evidenced. A mark is not inherently correct: the completed syntax determines its validity.

### 6.3 Agreement and noun features

Expand `subject_verb_agreement` using reusable construction annotations:

- `simple_subject_head`, `postmodified_subject`, `clausal_subject`, `gerund_subject`.
- `compound_subject_and`, `alternative_subject_or_nor`.
- `inverted_subject`, `existential_there_subject`.
- `indefinite_pronoun_subject`, `relative_clause_agreement_controller`.
- `quantity_expression_head`, `collective_noun_interpretation`.
- `singular_form_plural_meaning`, `plural_form_singular_reference`.

Store `grammatical_number`, `grammatical_person`, and the controller span directly. Collective nouns and quantity expressions need context-sensitive definitions; avoid universal rules that ignore usage or intended meaning.

Keep countability, article selection, and determiner agreement distinct from subject–verb agreement. Reassess vague `affirmative_agreement`: retain only if a definition and examples demonstrate a useful separate construct.

### 6.4 Verb form, time, aspect, and voice

Separate concepts currently bundled under `verb_form` and tense/register:

| Dimension | Candidate values or foci |
|---|---|
| Finiteness | `finite`, `infinitive`, `present_participle`, `past_participle` |
| Morphological constraints | `base_after_modal`, `past_participle_after_perfect_auxiliary`, `participle_in_passive`, `irregular_verb_form` |
| Time reference | `past`, `present`, `future`, `generic`, `context_dependent` |
| Aspect | `simple`, `progressive`, `perfect`, `perfect_progressive` |
| Temporal relation | `simultaneous`, `anterior`, `subsequent`, `habitual`, `ongoing_at_reference_time` |
| Voice | `active`, `passive` |
| Contextual foci | `explicit_time_anchor`, `sequence_of_events`, `literary_present`, `reported_finding_vs_general_claim` |

Time reference is not identical to inflectional tense. Store auxiliary sequence and event/reference-time evidence. Do not choose a tense merely because it matches the nearest verb. Passive voice is a valid structure, not automatically a defect.

### 6.5 Pronouns, reference, and possession

- Agreement: `pronoun_number_agreement`, `pronoun_person_consistency`, `clause_antecedent_reference`.
- Reference: `ambiguous_antecedent`, `missing_antecedent`, `demonstrative_reference`, `relative_pronoun_reference`.
- Case: `subject_case`, `object_case`, `possessive_determiner_form`, `independent_possessive_form`, `reflexive_form`.
- Possession: `singular_noun_possessive`, `regular_plural_possessive`, `irregular_plural_possessive`, `joint_vs_separate_possession`.
- Orthographic contrast: `possessive_vs_contraction`, `plural_vs_possessive`.

Do not encode singular they as categorically ungrammatical. Annotate intended reference, number interpretation, and the actual constraints of the item. Treat usage-dependent ambiguities as review issues.

### 6.6 Modifiers, comparison, and parallel structure

- Attachment: `introductory_modifier_controller`, `dangling_modifier`, `misplaced_modifier`, `ambiguous_attachment`.
- Modifier form: `adjective_vs_adverb`, `participial_modifier`, `relative_modifier`, `absolute_construction`.
- Comparison: `like_entities_compared`, `comparison_complement`, `comparative_vs_superlative`, `comparison_ellipsis`.
- Parallelism: `coordinated_word_forms`, `coordinated_phrases`, `coordinated_clauses`, `correlative_balance`, `shared_complement_structure`.
- Scope: `limiting_modifier_scope`, `negation_scope`, `quantifier_scope`.

Parallel structures need corresponding grammatical functions; they need not have identical word counts or superficial endings. Absolute constructions have their own subjects and must not be misdiagnosed using a dangling-participle shortcut.

### 6.7 Usage and expression support

Preserve precision, concision, idiom, and register as useful teaching and review concepts, but distinguish their roles:

- `semantic_redundancy`, `unnecessary_metadiscourse`, `ambiguous_word_choice`.
- `collocational_fit`, `preposition_complement_selection`, `commonly_confused_lexeme`.
- `meaning_preservation`, `emphasis_alignment`, `register_consistency`.

These may be properties of a passage or answer rather than the official primary skill. “Shorter,” “more formal,” and “active voice” are not universal correctness criteria.

## 7. Sentence anatomy: add structure and relations

Bring grammar §D.10 into the catalog, but separate **form**, **function**, and **features**:

| Axis | Candidate concepts |
|---|---|
| Form | `noun_phrase`, `verb_phrase`, `prepositional_phrase`, `finite_clause`, `nonfinite_clause`, `relative_clause`, `appositive_phrase` |
| Function | `subject`, `predicate`, `direct_object`, `indirect_object`, `subject_complement`, `object_complement`, `modifier`, `adjunct` |
| Features | `restrictive`, `supplementary`, `coordinated`, `introductory`, `interrupted` |
| Relations | `head_of`, `subject_of`, `agrees_with`, `modifies`, `refers_to`, `coordinates_with`, `supplements`, `delimited_by` |

Priority definition corrections when preparing amendments:

- A subject is a grammatical function, not necessarily the performer of an action; passive subjects demonstrate this.
- Restrictive relatives are not defined solely by the word **that**; determine their identifying function in context.
- Appositives may be restrictive or supplementary; do not define all appositives as comma-delimited.
- A conjunctive adverb can follow a period or occur within a clause; it does not invariably require semicolon-before/comma-after.
- Modifier attachment depends on syntax and meaning; “the nearest noun” is not a universal rule.
- Some short introductory elements do not require commas. Avoid mandatory punctuation without construction evidence.
- Blank anatomy must follow the inserted option and its context; remove the proposed catch-all fallback to `main_verb` in future revisions.
- Keep `verb_form` and `verb_tense_consistency` in concept tags, not anatomy tags.

These are proposed corrections, not edits to the active rules. Before promotion, support each amendment with grammar references and reviewed examples/counterexamples.

Span contract: store text version/hash, text-view ID, start/end offsets, offset unit, and exact quoted text. Specify half-open intervals. Use Unicode code-point offsets in the proposed interchange format and explicitly convert for JavaScript UTF-16 consumers. A punctuation insertion can use a zero-width anchor. Analyze each completed option in its own text view so replacing a blank cannot silently invalidate offsets. Allow overlapping spans and relations between them.

## 8. Writing style: make it an explicit ontology

### 8.1 Separate genre, register, stance, and voice

| Field | Candidate values |
|---|---|
| `genre_key` | `research_summary`, `scholarly_argument`, `historical_exposition`, `literary_analysis`, `literary_narrative`, `poetry`, `biographical_exposition`, `explanatory_prose` |
| `register_key` | `academic_expository`, `technical_accessible`, `scholarly_interpretive`, `literary`, `conversational_quoted` |
| `stance_keys` | `descriptive`, `analytical`, `cautiously_inferential`, `evaluative`, `skeptical`, `concessive` |
| `narrative_perspective_key` | `first_person`, `third_person_limited`, `third_person_omniscient`, `impersonal_expository` |
| `attribution_form_keys` | `named_person`, `named_group`, `institution`, `publication`, `previously_established_source`, `unattributed` |
| `claim_commitment_key` | `asserted`, `qualified`, `possible`, `hypothetical`, `disputed` |

Attach commitment to claims, not just whole passages. A passage can report a certain measurement and cautiously interpret its cause.

### 8.2 Syntax and information flow

Candidate style features:

- `fronted_adverbial`, `delayed_main_predicate`, `embedded_relative_clause`, `supplementary_appositive`.
- `participial_compression`, `nominalization`, `passive_method_description`, `coordinated_predicates`.
- `given_to_new_progression`, `end_focus`, `contrastive_focus`, `topic_chain`, `pronoun_reference_chain`.
- `definition_on_first_mention`, `example_after_abstraction`, `claim_then_qualification`, `attributed_counterposition`.

Measure sentence lengths, clause depth, subject–verb distance, lexical repetition, passive clauses, and supplement counts as numeric features. Do not invent more enums for every numeric range. Document each measurement method and denominator.

### 8.3 Topic-neutral passage architecture

Keep topic separate from rhetorical structure. Candidate architecture building blocks:

`context → claim → evidence → implication`

`established_view → conflicting_observation → revised_explanation`

`problem → proposed_solution → limitation`

`observation → interpretation → qualification`

`entity_A → entity_B → comparison`

`expectation → reversal → explanation`

`scene → perception → character_response`

Store an ordered list of rhetorical moves. Keep convenient named presets such as `science_setup_finding_implication`, but make them references to a topic plus an architecture rather than unrelated atomic concepts.

### 8.4 Style controls versus validity rules

Reading v3 §22 already supplies useful style guidance. Some numerical targets and blanket restrictions should become **versioned generation-profile preferences**, not universal ontology truths: obligatory appositives, fixed passive percentages, compulsory named authorities, prescribed sentence-length variation, or a single preferred passage order.

Profiles should be based on reviewed source samples and conditioned on genre, skill, and length. Tiny passages make percentage targets unstable. Record sample counts and uncertainty. Do not invent researchers, journals, or studies simply to satisfy a named-attribution target; use verified source material or transparently fictional practice contexts without false real-world citations.

## 9. Traps, errors, plausibility, and misconceptions

### 9.1 Four distinct layers

For “The collection of maps ___ valuable,” with `is` versus `are`:

- **Rule:** subject–verb agreement.
- **Trap:** a plural noun intervenes between singular subject head and verb.
- **Option error:** `are` agrees with the intervening noun rather than the head.
- **Plausibility:** nearby plural noun supports a locally natural-sounding sequence.
- **Hypothesized misconception:** the nearest noun controls verb number.

An annotator may identify the first four from the text. Selecting `are` once does not prove the learner holds the fifth belief.

### 9.2 Expanded grammar trap families

| Family | Candidate traps |
|---|---|
| Agreement controller | `nearest_noun_attraction`, `intervening_relative_clause`, `inverted_subject_position`, `coordinated_noun_inside_modifier`, `misleading_noun_ending` |
| Clause recognition | `nonfinite_looks_like_predicate`, `relative_clause_masks_missing_main_verb`, `conjunctive_adverb_looks_like_coordinator`, `compound_predicate_looks_like_two_clauses` |
| Punctuation | `pause_based_boundary`, `long_subject_invites_comma`, `embedded_list_masks_clause_structure`, `supplement_closure_overlooked`, `colon_after_incomplete_lead_in` |
| Verb time/form | `nearest_tense_attraction`, `participle_finite_confusion`, `modal_inflection_attraction`, `narrative_time_overrides_explicit_anchor` |
| Reference/possession | `nearest_antecedent_attraction`, `clause_antecedent_as_plural_noun`, `plural_possessive_surface_confusion`, `contraction_possessive_homophony` |
| Modifier/comparison | `plausible_but_wrong_attachment`, `introductory_agent_mismatch`, `absolute_as_dangling_modifier`, `comparison_category_mismatch` |
| Parallelism/scope | `surface_ending_parallelism`, `correlative_scope_mismatch`, `limiting_word_scope_shift`, `negation_scope_shift` |

Reuse existing equivalent keys where definitions match. These labels do not mandate that generated questions contain every trap, nor that every distractor exploit a distinct one.

### 9.3 Fine-grained grammar option errors

Replace reliance on generic labels with a hierarchy; retain old generic labels as legacy/fallback categories.

| Parent | Candidate leaf errors |
|---|---|
| `error.boundary` | `comma_splice`, `fused_clauses`, `dependent_fragment`, `missing_main_predicate`, `split_compound_predicate` |
| `error.punctuation` | `subject_verb_split`, `verb_object_split`, `incomplete_colon_lead_in`, `unclosed_supplement`, `inconsistent_supplement_delimiters`, `restrictive_element_set_off`, `required_supplement_delimiter_missing` |
| `error.agreement` | `intervening_noun_number`, `wrong_subject_number`, `relative_controller_mismatch`, `pronoun_number_mismatch` |
| `error.verb` | `nonfinite_for_finite`, `inflected_after_modal`, `wrong_participle`, `time_anchor_conflict`, `aspect_relation_conflict` |
| `error.reference` | `wrong_antecedent`, `ambiguous_reference`, `case_mismatch`, `clause_reference_number_mismatch` |
| `error.possession` | `plural_for_possessive`, `singular_for_plural_possessive`, `possessive_for_contraction`, `contraction_for_possessive` |
| `error.modifier` | `dangling_controller`, `wrong_attachment`, `adjective_adverb_mismatch`, `unlike_comparison` |
| `error.parallelism` | `coordinate_function_mismatch`, `correlative_imbalance`, `shared_complement_mismatch` |

Require a completed-sentence explanation and the governing rule. Generic “sounds awkward” is insufficient.

### 9.4 Shared semantic and reasoning error hierarchy

Organize existing reading keys rather than discarding their detail:

- **Evidence status:** contradiction, unsupported addition, partial support, indirect evidence.
- **Scope:** too broad, too narrow, wrong entity, wrong time interval, wrong population.
- **Logical force:** excessive certainty, weakened force, possibility-to-necessity, some-to-all.
- **Relation:** cause/effect reversal, correlation-to-causation, contrast-to-concession confusion, wrong comparison direction.
- **Attribution:** swapped authors, blended positions, narrator/character confusion.
- **Lexical fit:** wrong contextual sense, near-synonym imprecision, polarity mismatch, connotation mismatch, collocation mismatch.
- **Rhetorical role:** topic-for-purpose, detail-for-main-idea, evidence-for-conclusion, example-for-counterargument.
- **Data:** retain wrong row/column, wrong group, aggregate-to-individual, single measure, timing constraint, and other existing detailed types.

Do not collapse `overstatement` into `scope_error`: a claim can retain the same population while changing certainty. Define whether `tone` means attitude and `register` means formality/social variety, then migrate the overlapping current labels accordingly.

### 9.5 Plausibility and option competition

Extend existing plausibility cues with:

`local_number_match`, `surface_parallel_shape`, `familiar_punctuation_pattern`, `pause_intuition`, `familiar_tense`, `partial_rule_application`, `shortest_option_bias`, `prestige_word_choice`, `copied_note_detail`, `correct_fact_wrong_goal`, `transition_keyword_association`.

Require concrete evidence for the cue. `shortest_option_bias` requires an actually shorter option; it is not a generic explanation for any distractor.

Model distractor distance on separate axes: surface similarity, syntactic similarity, semantic similarity, and number of reasoning steps needed to reject. Preserve `wide/moderate/tight` only as a derived summary with a rubric. High similarity is not enough: every distractor must remain decisively wrong.

## 10. Transitions and rhetorical synthesis

### 10.1 Transition logic as a relation between spans

Use broad relation families with optional subtypes:

| Family | Subtypes |
|---|---|
| Addition | reinforcement, parallel point |
| Contrast | direct opposition, comparison difference |
| Concession | expectation violated while the conceded claim remains true |
| Cause/result | reason, consequence, inferential conclusion |
| Elaboration | specification, example, restatement, clarification |
| Sequence | temporal succession, simultaneity, procedural step |
| Alternative | replacement, competing possibility |
| Qualification | restriction, exception, scope limitation |
| Summary | synthesis of preceding points |

Store source span, target span, relation direction, and discourse scope. A transition may connect the next sentence to the whole preceding argument rather than its nearest clause. Existing entries such as `final_realization` and `frequency_difference` should become construction/context features when appropriate.

Candidate transition errors: `wrong_relation_family`, `reversed_relation_direction`, `wrong_discourse_scope`, `false_concession`, `sequence_without_temporal_relation`, `example_without_generalization`, `conclusion_without_support`.

Do not build a one-to-one word-to-relation dictionary. Words such as “while,” “since,” and “still” depend on context.

### 10.2 Factor rhetorical synthesis goals

Replace new one-off compound goals with a structured goal object:

- `operation`: introduce, describe, explain, compare, contrast, emphasize, generalize, illustrate, qualify.
- `target_entity_ids`: the person, work, study, method, or objects involved.
- `content_focus`: identity, purpose, method, finding, mechanism, advantage, limitation, chronology, quantity, significance.
- `comparison_dimension`: size, age, duration, origin, method, outcome, structure, scope.
- `audience_knowledge`: retain the current three values, but attach familiarity to specific entities.
- `required_note_ids` and `excluded_note_ids`: evidence-linked constraints; allow alternative sufficient note sets.
- `required_relation`: the relationship the response must explicitly express.

Example: `emphasize_age_similarity` becomes operation `emphasize`, focus `quantity`, dimension `age`, relation `similarity`, plus the two relevant entities. Preserve the old key as a preset during migration.

Extend synthesis failures: `unsupported_note_addition`, `entity_attribute_swap`, `numerical_distortion`, `comparison_dimension_mismatch`, `factually_true_goal_irrelevant`, `relationship_left_implicit`, `overgeneralization_from_notes`. Keep current audience and omission failures. Define `relationship_left_implicit` narrowly: only when the stated goal requires an explicit relationship and the option does not communicate it adequately.

## 11. Reading refinements that support writing and distractor design

Retain the existing seven reading skill families. Add supporting annotations rather than forcing all distinctions into new skill IDs:

- **Claims:** proposition, claimant, polarity, modality, quantifier, time, population, and conditions.
- **Evidence:** supports/weakens/illustrates/qualifies relation, evidence span, target claim, and whether evidence is actual text or a hypothetical option premise.
- **Rhetorical action:** define, contextualize, exemplify, concede, challenge, distinguish, explain, qualify, conclude, propose.
- **Cross-text:** separate agreement about a finding from disagreement about explanation, method, scope, or implications.
- **Words in context:** grammatical category, local semantic role, selectional constraints, collocation, connotation, and figurative versus literal interpretation.
- **Inference:** explicit premises and bounded conclusion; flag outside assumptions instead of calling every plausible conclusion supported.

Avoid assigning `main_purpose` to both central ideas/details and structure/purpose without a decision rule. Primary classification follows the actual assessed task: what the passage says versus what the author is doing. Keep ambiguous legacy records for review.

## 12. Worked annotation and generation patterns

### 12.1 Agreement

**Original illustrative item:** “The collection of rare maps ___ unusually valuable.”

| Option | Correctness | Primary error | Plausibility |
|---|---|---|---|
| `is` | correct | none | Fits singular head `collection` |
| `are` | incorrect | intervening noun number | Nearby plural `maps` |
| `being` | incorrect | nonfinite for finite | Familiar participial form |
| `be` | incorrect | inappropriate bare form in this finite context | Recognizable base verb |

Primary focus: subject–verb agreement; secondary concept: finite predicate requirement. The trap is linked specifically to `are`, not automatically to all distractors. This miniature illustrates annotation; it is not a calibrated high-difficulty item.

### 12.2 Boundary

**Original illustrative item:** “The archive was small___ it contained several rare maps.”

Options: `;` (correct), `,` (comma splice), no punctuation (fused clauses), ` and although` (leaves the coordinated subordinate material without the needed structure).

Both spans are independent clauses in the correct completion. A period would also work here, so a period must not be offered as a supposedly wrong alternative. This is the kind of contextual equivalence check the ontology should support.

### 12.3 Transition

**Original illustrative passage:** “The revised process requires less energy than the earlier process. ___, it takes twice as long.”

`However` expresses a contrast between an advantage and a drawback. `Consequently` asserts an unsupported causal relationship; `For example` miscasts the drawback as an instance of energy reduction; `Similarly` signals an unsupported parallel. Store the two propositions and their relation, not just a transition-word label.

### 12.4 Synthesis

Notes say Method A takes two hours, Method B takes one hour, and both produce the same measured output. Goal: emphasize Method B's time advantage.

A correct response compares the time required. “Both methods produce the same output” is true but goal-irrelevant. “Method B produces twice as much output” is unsupported and confuses time with output. “Method A takes one hour” swaps an entity's attribute. These require different error keys even though all fail the same synthesis goal.

### 12.5 Proposed record fragment

```json
{
  "ontology_version": "proposal_v1",
  "classification": {
    "official_domain": "standard_english_conventions",
    "official_skill": "form_structure_and_sense",
    "primary_focus": "grammar.subject_verb_agreement",
    "secondary_concepts": ["grammar.finite_predicate_requirement"]
  },
  "annotation_state": "resolved",
  "traps": [{
    "key": "trap.nearest_noun_attraction",
    "controller_span_id": "subject_head",
    "attractor_span_id": "intervening_maps",
    "affected_option_ids": ["B"]
  }],
  "options": [{
    "id": "B",
    "text": "are",
    "correctness": "incorrect",
    "primary_error": "error.agreement.intervening_noun_number",
    "secondary_errors": [],
    "plausibility_keys": ["plausibility.local_number_match"],
    "evidence_span_ids": ["subject_head", "intervening_maps"],
    "misconception_hypotheses": ["nearest_noun_controls_agreement"]
  }]
}
```

This is an intentionally partial illustrative record, not a drop-in payload for existing validators. A complete record needs all options, resolved span objects, source provenance, and the current required question fields.

## 13. Ingestion and generation must share meaning, not certainty

### Ingestion

1. Preserve exact source text, option order, answer-key provenance, and extraction uncertainties.
2. Determine the tested skill from the completed item and evidence.
3. Annotate anatomy, decisive rules, errors, traps, and style observations.
4. Preserve unknowns; do not invent author intent or undocumented student behavior.
5. Queue unsupported keys as candidates with source examples.

### Generation

1. Select an approved domain/skill/focus combination and style profile.
2. Specify the decisive rule, required construction, and intended option-error plan.
3. Compose an original passage and correct completion.
4. Construct distractors from context-valid errors, with observable plausibility cues.
5. Re-annotate the actual output and compare it with the requested specification.
6. Review alternative correct answers, meaning, factual grounding, and stylistic authenticity.

Store `requested_profile` separately from `observed_annotation`. A requested agreement trap is not proof the generated passage contains one. Record mismatches explicitly.

## 14. Validation, evidence, and quality

### 14.1 Machine-checkable constraints

- Referenced keys exist and are active for the declared ontology version.
- Parent/child and allowed-domain relationships are valid.
- Derived subsets match their authoritative parent sets.
- Correct options carry no error tags; unresolved correctness stays unresolved.
- One designated answer exists for a publishable single-answer item.
- Span offsets reproduce quoted text in the correct text version.
- Synthesis note IDs, data cell references, and entity links resolve.
- Legacy `multiple` is not accepted in the new trap list.
- Unknown annotations cannot silently become assessed absence.

### 14.2 Semantic review requirements

- Exactly one option is defensible under the full context and task.
- Every rejected option has a demonstrable decisive failure.
- Grammar judgments do not depend solely on rhythm, taste, or an optional style convention.
- The target concept is actually necessary to distinguish the answer.
- Style preferences do not create false grammatical errors.
- Explanations identify the controller, boundary, relation, or evidence needed to solve the item.
- Data and notes-based options are evaluated against the correct referenced evidence.

A schema can enforce one answer label; it cannot prove one valid answer. Keep semantic review explicit.

### 14.3 Review finding vocabulary

Candidate findings: `multiple_defensible_answers`, `no_defensible_answer`, `ambiguous_reference`, `insufficient_context`, `optional_punctuation_only_distinction`, `unsupported_factual_claim`, `taxonomy_output_mismatch`, `implausible_distractor`, `answer_length_cue`, `option_structure_cue`, `style_profile_mismatch`, `explanation_rule_error`, `source_extraction_uncertain`.

Keep these distinct from job failures and learner errors.

### 14.4 Difficulty and frequency

Preserve `low/medium/high`, but record whether a label is requested, expert-estimated, or empirically estimated. Store structural features separately from performance measurements. Record sample size and cohort context for observed accuracy and distractor selection rates. Do not treat a high trap count as evidence of high difficulty.

Frequency bands require corpus ID, question count, denominator, date, and classification version. Use unknown when no defensible estimate exists. Generated inventory frequency must not be presented as official exam frequency.

## 15. Crosswalk for all existing catalog categories

| Existing category or group | Proposed treatment |
|---|---|
| CONTENT_ORIGINS, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES | Preserve in provenance/operations; separate content lineage from semantic relations |
| JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES, OVERLAP_STATUSES | Preserve in workflow registry; state transitions belong in policy |
| REVIEW_TASK_TYPES, REVIEW_STATUSES, REVIEW_RUN_STATUSES, TRIGGERED_BY_VALUES, REVIEW_VERDICTS, CONSENSUS_VERDICTS | Preserve operational values; add separate semantic review findings |
| TEST_FORMAT_KEYS, SOURCE_STATS_FORMAT_KEYS | Preserve with source and assessment metadata |
| STIMULUS_MODE_KEYS | Split layout, genre, and asset dimensions; keep legacy presets |
| STEM_TYPE_KEYS | Split template, task operation, skill, and answer form |
| QUESTION_FAMILY_KEYS and both family subsets | Preserve compatibility; add official reporting crosswalk |
| GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_BY_ROLE | Retain current IDs initially; add detailed rules and explicit relationships |
| SYNTACTIC_TRAP_KEYS | Specific multi-value annotations; migrate none/multiple with uncertainty preserved |
| SYNTACTIC_TRAP_REQUIRED_ROLES | Move to versioned validation policy and reconsider mandatory presence |
| DISTRACTOR_TYPE_KEYS | Separate correctness; organize errors hierarchically and expand grammar leaves |
| REASONING_TRAP_KEYS | Preserve detailed distinctions; define relationships to errors and cues |
| PLAUSIBILITY_SOURCE_KEYS | Option-level evidence-linked cues |
| ANSWER_MECHANISM_KEYS, SOLVER_PATTERN_KEYS | Separate cognitive operation from instructional procedure; link rather than merge blindly |
| STUDENT_FAILURE_MODE_KEYS | Treat as design hypotheses unless backed by learner evidence |
| DISTRACTOR_DISTANCE_KEYS | Derived rubric-backed summary of multiple distances |
| DIFFICULTY_KEYS, FREQUENCY_BANDS | Preserve labels; add provenance, sample context, and unknown state |
| TENSE_REGISTER_KEYS | Keep presets; factor time/aspect, genre/register, and discourse function |
| PASSAGE_ARCHITECTURE_KEYS, TOPIC_BROAD_KEYS | Separate topic from ordered rhetorical moves; keep presets |
| READING_SKILL_FAMILY_KEYS, READING_FOCUS_BY_SKILL_FAMILY | Preserve; clarify purpose/detail and overlapping focus decisions |
| TEST_CONSTRUCT_KEYS, CRAFT_SUBCONSTRUCT_KEYS | Retain useful precision goals; define relations to skills and errors |
| TEXT_RELATIONSHIP_KEYS | Model direction, attributed claims, agreement dimension, and degree |
| QUANTITATIVE_SUB_PATTERN_KEYS | Preserve detailed patterns, with explicit data constraints |
| SENTENCE_FUNCTION_ROLE_KEYS | Expand rhetorical actions; attach target span and passage context |
| TRANSITION_SUBTYPE_KEYS | Group under discourse relations; separate contextual features |
| SYNTHESIS_GOAL_KEYS | Preserve presets; factor operation, entity, focus, comparison dimension |
| AUDIENCE_KNOWLEDGE_KEYS | Preserve; attach familiarity to relevant entities |
| REQUIRED_CONTENT_KEYS | Convert requirements into evidence-linked constraints; separate include from omit |
| SYNTHESIS_DISTRACTOR_FAILURE_KEYS | Preserve and expand under option error hierarchy |

## 16. Migration and implementation order

### Phase 1 — Definitions and governance

- Resolve the authoring-source contradiction. Recommended flow, consistent with the generator header: approved rule amendment → compiled manifest → generated code and vocabulary views.
- Declare this document a proposal input, not the authoring bypass.
- Inventory all consumers before renaming any key.
- Add definitions, examples, counterexamples, applicability, and provenance to the highest-value terms.
- Clarify correctness, absence, unknown, primary focus, and multi-label semantics.

### Phase 2 — Grammar and distractor depth

- Add the fine-grained grammar error hierarchy and the controller/boundary evidence contract.
- Catalog sentence anatomy and propose amendments to oversimplified definitions.
- Link traps to specific distractors.
- Preserve existing API fields through explicit adapters.

### Phase 3 — Style and rhetorical composition

- Add independent style observations and versioned generation profiles.
- Factor transition and synthesis dimensions.
- Separate topic from passage architecture.
- Align template work with `grammar_rules_todo.md` after evidence review.

### Phase 4 — Migration evaluation

- Build a reviewed sample spanning all official skills, with extra coverage for grammar boundary cases and confusable distractors.
- Include ambiguous/negative examples, not only easy prototypes.
- Compare annotators on primary focus, primary option error, and evidence spans.
- Review confusion matrices and merge distinctions that cannot be annotated reliably.
- Test held-out generated questions for target fidelity, unique answers, style quality, and distractor plausibility.
- Report counts and uncertainty; no invented accuracy thresholds or claims of empirical improvement.

### Migration rules

- Alias only when meaning is equivalent; changing semantics requires a new ID.
- A broad old label cannot be automatically mapped to a precise new subtype without evidence.
- Keep original annotation, original version, migrated annotation, mapping method, and reviewer decision.
- Legacy `multiple` requires reannotation to recover actual traps.
- Legacy `none` must be checked against historical field semantics before conversion.
- Define rollback and old-version readers before changing production writers.
- Run the existing vocabulary synchronization check after an approved implementation, not as a substitute for semantic review.

## 17. Recommended first deliverable after this proposal

Start with a small, well-defined grammar pilot: subject–verb agreement, finite-versus-nonfinite predicates, clause boundaries, and supplement punctuation. For each, create term cards, annotated examples, counterexamples, option-error mappings, and compatible generation specifications.

This establishes the central structure the rest of the ontology needs: **tested rule → sentence evidence → tempting error → decisive explanation**. Expand through measured annotation gaps and generation failures rather than adding unvalidated labels wholesale.

## 18. Follow-up: existing refactor and execution workflow

A subsequent code and artifact audit is recorded in [refactor_plan_cgpt.md](refactor_plan_cgpt.md).

Recommendation: extend the existing `rules_refactor/` decomposition instead of creating another independent rules source tree. Its 66 generated modules reproduce exactly. Generation has an opt-in modular loader; legacy root loading remains the default, and modular annotation adoption is pending. The shared quality increment and v1.0.0 terminology baseline are implemented as documented in the plan and STANDARD.md. Most semantic ontology improvements above remain proposals.

The audit distinguishes the controlled-vocabulary JSON manifest from per-question PostgreSQL JSONB annotations, records the now-fixed reading-generation label defect, and specifies a versioned compiler/loader workflow. It also covers RAM bundle caches, disk checkpoints, provider prefix caching, and a conditional phased-generation experiment. Local storage caching alone does not reduce model context; stage-specific rules and payload selection do.
