# Calibration Set Report

Generated: 2026-05-23 22:29 UTC
Rules: `rules_agent_v7.0` + `rules_agent_dsat_reading_v2`

## Overall DB Stats
- Total official questions: **569**
- Calibration eligible: **542**
  - Grammar eligible: 175
  - Reading eligible: 367

## Quality Flags Found
| Flag | Count |
|---|---|
| `inconsistent_skill_family_casing` | 76 |
| `missing_difficulty` | 14 |
| `non_standard_grammar_focus_key` | 13 |

## Selected Calibration Set (40 questions)

### Grammar Questions (20)
| # | Exam | Q# | grammar_focus_key | skill_family | Difficulty |
|---|---|---|---|---|---|
| 1 | PT1 02 | Q19 | `subject_verb_agreement` | Form, Structure, and Sense | medium |
| 2 | PT1 01 | Q23 | `verb_tense_consistency` | Form, Structure, and Sense | medium |
| 3 | PT1 01 | Q29 | `transition_logic` | expression_of_ideas | medium |
| 4 | PT1 02 | Q20 | `punctuation_comma` | Boundaries | medium |
| 5 | PT1 02 | Q22 | `sentence_boundary` | Boundaries | medium |
| 6 | PT10 01 | Q21 | `comma_splice` | Boundaries | medium |
| 7 | PT1 01 | Q22 | `appositive_punctuation` | Form, Structure, and Sense | medium |
| 8 | PT1 01 | Q20 | `semicolon_use` | Boundaries | medium |
| 9 | PT11 01 | Q22 | `unnecessary_internal_punctuation` | Punctuation | medium |
| 10 | PT1 01 | Q25 | `pronoun_antecedent_agreement` | agreement | medium |
| 11 | PT6 01 | Q19 | `verb_form` | Form, Structure, and Sense | medium |
| 12 | PT1 02 | Q21 | `logical_predication` | Form, Structure, and Sense | medium |
| 13 | PT1 01 | Q27 | `end_punctuation_question_statement` | Boundaries | medium |
| 14 | PT1 01 | Q24 | `colon_dash_use` | Boundaries | medium |
| 15 | PT11 01 | Q23 | `logical_relationships` | Form, Structure, and Sense | medium |
| 16 | PT4 01 | Q19 | `possessive_contraction` | expression_of_ideas | low |
| 17 | PT4 02 | Q21 | `relative_pronouns` | Boundaries | medium |
| 18 | PT6 02 | Q20 | `register_style_consistency` | Form, Structure, and Sense | medium |
| 19 | PT1 01 | Q19 | `pronoun_antecedent_agreement` | Agreement | low |
| 20 | PT6 02 | Q22 | `semicolon_use` | Boundaries | medium |

### Grammar Focus Key Distribution
| grammar_focus_key | count |
|---|---|
| `semicolon_use` | 2 |
| `pronoun_antecedent_agreement` | 2 |
| `subject_verb_agreement` | 1 |
| `verb_tense_consistency` | 1 |
| `transition_logic` | 1 |
| `punctuation_comma` | 1 |
| `sentence_boundary` | 1 |
| `comma_splice` | 1 |
| `appositive_punctuation` | 1 |
| `unnecessary_internal_punctuation` | 1 |
| `verb_form` | 1 |
| `logical_predication` | 1 |
| `end_punctuation_question_statement` | 1 |
| `colon_dash_use` | 1 |
| `logical_relationships` | 1 |
| `possessive_contraction` | 1 |
| `relative_pronouns` | 1 |
| `register_style_consistency` | 1 |

### Reading Questions (20)
| # | Exam | Q# | skill_family_key | reading_focus_key | Difficulty |
|---|---|---|---|---|---|
| 1 | PT4 01 | Q1 | Words in Context | None | medium |
| 2 | PT1 01 | Q1 | words_in_context | contextual_meaning | medium |
| 3 | PT1 01 | Q4 | words_in_context | precision_fit | medium |
| 4 | PT11 02 | Q5 | words_in_context | underlined_word_meaning | medium |
| 5 | PT4 01 | Q2 | Words in Context | None | medium |
| 6 | PT1 01 | Q10 | central_ideas_and_details | supporting_detail | medium |
| 7 | PT1 02 | Q10 | central_ideas_and_details | central_idea | medium |
| 8 | PT10 01 | Q12 | central_ideas_and_details | character_or_author_detail | medium |
| 9 | PT4 02 | Q30 | central_ideas_and_details | passage_summary | medium |
| 10 | PT1 01 | Q7 | text_structure_and_purpose | overall_purpose | medium |
| 11 | PT1 01 | Q8 | text_structure_and_purpose | sentence_function | medium |
| 12 | PT10 01 | Q7 | text_structure_and_purpose | structural_pattern | medium |
| 13 | PT1 01 | Q9 | text_structure_and_purpose | sentence_function | medium |
| 14 | PT11 02 | Q17 | Inferences | None | medium |
| 15 | PT1 01 | Q17 | inferences | causal_inference | medium |
| 16 | PT1 02 | Q11 | inferences | motivational_inference | medium |
| 17 | PT1 02 | Q32 | rhetorical_synthesis | None | medium |
| 18 | PT1 02 | Q33 | rhetorical_synthesis | None | medium |
| 19 | PT10 02 | Q11 | Command of Evidence | None | low |
| 20 | PT11 01 | Q9 | cross_text_connections | text2_response_to_text1 | medium |

### Reading Skill Family Distribution
| skill_family_key | count |
|---|---|
| words_in_context | 5 |
| central_ideas_and_details | 4 |
| text_structure_and_purpose | 4 |
| inferences | 3 |
| rhetorical_synthesis | 2 |
| command_of_evidence | 1 |
| cross_text_connections | 1 |

## Negative Controls (10 — NOT YET GENERATED)

Must be generated separately: 10 deliberately weak questions (low-quality prompt, no source examples, mixed grammar_focus_key + reading). See TASKS_GENERATION.md calibration plan.

These must be generated with deliberately weak prompts (no source examples,
mixed grammar_focus_key + reading targets) to serve as true negative controls.
Generate them via `POST /generate/batches` with a dedicated batch.

## Next Steps
1. Run the review swarm against these 40 official questions
2. Admin labels each `would_approve` / `would_reject` / `borderline`
3. Generate 10 weak negative controls and add to the swarm run
4. Pick consensus thresholds at the inflection where admin rejection rate flips
5. Update `CONSENSUS_THRESHOLDS` in `backend/app/config.py`