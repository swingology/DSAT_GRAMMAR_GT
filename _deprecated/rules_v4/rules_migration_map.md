# Rules v4 Migration Map

This file maps the production source files into the v4 modular layout. It exists
to prevent future drift and to provide loading recipes for generation and
ingestion.

## Source Files

- Grammar source: `rules_agent_dsat_grammar_ingestion_generetion_v7.md` (2,413 lines)
- Reading source: `rules_agent_dsat_reading_v2.md` (1,450 lines)

Both source files are proven against Claude ground-truth tests. The v4 files
reorganize them into a core + domain-module layout; they do not intentionally
rename production keys or change validator semantics.

## v4 File Responsibilities

| v4 file | Responsibility | Source sections |
|---|---|---|
| `README.md` | load order, source authority, production compatibility | v7 preamble, A.1; reading_v2 preamble, §Source Authority, §1 |
| `rules_core_generation.md` | shared output shape, stimulus/stem approved values, option contract, distractor engineering, SAT realism, difficulty calibration rubric, generation workflow, anti-clone, provenance, amendment process, error/batch formats, student failure modes (shared + all domain-specific) | v7 A.1, A.3, B.1 (shared parts), D.7, D.8.2, D.8.4, D.8.5, E.1-E.8; reading_v2 §2, §4 (shared fields), §10 (traps ref), §12.3, §12.4, §14 (difficulty rubric), §15.1, §16.3, §17, §19 (all 14 failure modes), §20 |
| `rules_dsat_grammar_module.md` | grammar taxonomy, role/focus keys, role→focus mapping, syntactic trap keys (13 values), passage construction rules (~34 focus keys), distractor heuristics (~14 families), transition subtype vocabulary, notes synthesis metadata, passage architecture templates, no-change rules, tense/register metadata, grammar decision tree, disambiguation rules (16 priority), evidence span rules (grammar), option format rules, grammar validator checklist, worked examples, **v3 research additions: Boundaries Decision Tree (§20.1), FSS Edge Case Appendix (§20.2), Authenticity Anti-Patterns (§20.3), DSAT Trends (§20.4)** | v7 Part B (B.2-B.15), Part C (C.1-C.7), Part D (D.1-D.6, D.8.1, D.8.3, D.8.6, D.9); v3 research additions from rules_v3 grammar module §25-28 |
| `rules_dsat_reading_module.md` | reading taxonomy, 7 skill families with focus keys, answer mechanism keys (7), solver pattern keys (8), reasoning trap keys (16 I&I + 13 C&S), text relationship keys (6), passage architecture (7 base + 5 experimental), WIC three-level error analysis, polarity_fit full rules, 12 sentence function roles, 11 quantitative sub-patterns, cross-text generation constraints, reading difficulty by skill, reading validator checklist (14 base + 9 v1.1) | reading_v2 §3-18, §21 |

## Intentional De-Duplications

The following now live only in `rules_core_generation.md`:

- top-level output shape (question, classification, options, reasoning, generation_profile, review)
- shared question fields (source_exam, stimulus_mode_key, stem_type_key, passage_text, etc.)
- shared classification fields (domain, topic_broad, difficulty fields, register, tone, etc.)
- stimulus_mode_key and stem_type_key approved value enumerations
- shared option contract (option_label, option_text, is_correct, precision_score, etc.)
- distractor engineering rules (one failure mode per distractor, one plausibility source, etc.)
- SAT realism layer (distractor_distance, answer_separation_strength, plausible_wrong_count, etc.)
- precision_score scale (1/2/3)
- difficulty calibration rubric
- all approved student failure mode keys (shared, grammar-specific, reading-specific)
- generation request contract and shared passage_architecture_key values
- common generation workflow (12 steps)
- anti-clone, diversity controls, batching
- explanation requirements
- review object
- provenance and audit trail
- amendment process shape (with frequency_estimate, example_count, examples)
- error response format
- core validation lifecycle and checklist

The following now live only in `rules_dsat_grammar_module.md`:

- `grammar_role_key` (8 approved values)
- `grammar_focus_key` (~45 approved values)
- `secondary_grammar_focus_keys`
- `syntactic_trap_key` (13 approved values)
- `transition_subtype_key` (9 approved values)
- `synthesis_goal_key`, `audience_knowledge_key`, `required_content_key`
- grammar role→focus mapping table
- grammar disambiguation rules (16 priority rules)
- grammar decision tree (9 steps)
- no-change metadata and no-change generation rules
- tense/register metadata and approved register/tense keys
- grammar frequency bands
- passage construction rules for ALL approved grammar focus keys (~34 rules)
- distractor heuristics for ALL major grammar focus families (~14 tables)
- evidence span selection rules (grammar-specific)
- option text format rules (fill-in-blank, full-replacement, punctuation-only)
- grammar validator checklist (generation + annotation)
- complete worked generation examples
- pilot annotation examples
- v3 research additions: Boundaries Decision Tree, FSS Edge Case Appendix, Authenticity Anti-Patterns, DSAT Trends

The following now live only in `rules_dsat_reading_module.md`:

- `skill_family_key` (7 approved values)
- `reading_focus_key` (~40 approved values)
- `secondary_reading_focus_keys`
- `reasoning_trap_key` (16 Information and Ideas traps, 13 Craft and Structure traps)
- `text_relationship_key` (6 approved values)
- `answer_mechanism_key` (7 approved values)
- `solver_pattern_key` (8 approved values)
- reading skill→focus mapping and WIC disambiguation
- Words in Context three-level wrong-answer distinction (denotation/connotation/register)
- `polarity_fit` full rule with annotation and generation requirements
- 12 sentence function roles with descriptions
- 11 quantitative sub-patterns (8 approved `quantitative_sub_pattern` values)
- 5 experimental passage architectures
- Cross-Text `paired_passage_text` requirements and response-stem critical rule
- Quantitative CoE `table_data`/`graph_data` requirements
- `option_error_focus_key` guidance for WIC three-level classification
- reading difficulty profiles by skill (7 profiles)
- reading validator checklist (14 base + 9 v1.1 additional)

## Prompt Loading Recipes

### Grammar Generation

Load:
1. `rules_core_generation.md`
2. `rules_dsat_grammar_module.md`

Then provide a `generation_request` with `domain: "grammar"` and the desired
`target_grammar_role_key`, `target_grammar_focus_key`, difficulty, topic, and
trap fields.

### Reading Generation

Load:
1. `rules_core_generation.md`
2. `rules_dsat_reading_module.md`

Then provide a `generation_request` with `domain: "reading"` and the desired
`target_skill_family_key`, `target_reading_focus_key`, difficulty, topic, and
reasoning trap fields.

### Ingestion / Unknown Classification

Load all three v4 rule files, then require the model to:
1. select domain first
2. discard inactive domain taxonomies
3. emit exactly one domain's classification fields
4. run core validation
5. run active-domain validation

### Minimal Grammar-Only Load

Load:
1. `rules_core_generation.md`
2. `rules_dsat_grammar_module.md`

### Minimal Reading-Only Load

Load:
1. `rules_core_generation.md`
2. `rules_dsat_reading_module.md`

## V4-Specific Additions

v4 carries forward v3's externally-researched enhancements from
`rules_v3/research_report_v3.md`.

### Research-Backed Sections in Grammar Module

| Section | Title | Source |
| ------- | ----- | ------ |
| §20.1 | Boundaries Decision Tree & Anti-Trap Rules | Test Innovators, NUM8ERS, multiple prep sources |
| §20.2 | FSS Edge Case Appendix | UWorld, PrepScholar, The Test Advantage |
| §20.3 | Authenticity Anti-Patterns (14 rules) | ChatSAT Benchmark Study (May 2025), InGenius Prep (Feb 2026) |
| §20.4 | 2025-2026 DSAT Trends | Gateplus analysis, College Board framework v3.01 |

### Reading Module Enhancements (from reading_v2/reading v1.1)

| Section | Title | Source |
| ------- | ----- | ------ |
| §6.5 | `polarity_fit` WIC key with full disambiguation | PT4–PT11 answer explanations |
| §6.6 | 12 sentence function roles | CB_ANSWERS_QUESTIONS_ANALYSIS.md |
| §11.2 | 5 experimental passage architectures | PT4–PT11 gap analysis |
| §13.2 | 11 quantitative sub-patterns + 5 quantitative traps | PT4–PT11 quantitative items |
| §13.7 | Qualified disagreement generation rules | Cross-text PT4–PT11 analysis |
| §14 | 14 student failure mode keys (consolidated) | v1.1 addendum synthesis |

## Compatibility Checks Before Replacing Prompts

Before using v4 as the only LLM rule source in production prompts, confirm:

- [ ] a grammar ingestion prompt using core + grammar produces the same top-level
      sections as grammar_v7
- [ ] a reading ingestion prompt using core + reading produces the same top-level
      sections as reading_v2
- [ ] a mixed-domain ingestion prompt using all three v4 files correctly routes
      Expression of Ideas to grammar and Information/Craft items to reading
- [ ] generated grammar items include role, focus, trap, frequency, option
      error keys, and no-change/tense fields when required
- [ ] generated reading items include skill, focus, reasoning trap, evidence
      span, and null grammar keys
- [ ] Cross-Text generated items always include `paired_passage_text`
- [ ] Quantitative CoE generated items always include `table_data` or `graph_data`
- [ ] no production output includes keys not listed in core or the active domain module
- [ ] all 13 syntactic trap keys from grammar_v7 are available and functional
- [ ] passage construction rules exist for every approved grammar focus key
- [ ] distractor heuristic tables exist for every major grammar focus family
- [ ] student_failure_mode_key values used in grammar and reading heuristics are
      all present in core's approved list (§8.4)
- [ ] evidence span selection rules are applied for both grammar and reading items
- [ ] amendment proposals include frequency_estimate and example_count fields
- [ ] precision_score scale and difficulty calibration rubric are accessible from
      core without loading a domain module
- [ ] Words in Context items classify wrong-option failures at the three-level
      denotation/connotation/register distinction
- [ ] `polarity_fit` items annotate the negator/concessive in evidence_span_text
      and review_notes
- [ ] `sentence_function` items reference one of the 12 approved roles
- [ ] `qualified_disagreement` cross-text items include the three required
      structural elements

## Compatibility Note

All v4 additions are backwards-compatible with grammar_v7 and reading_v2. No
approved keys were renamed or removed. The v4 modular layout is a strict
reorganization of the source files. Loading v4 modules where a monolithic
file was previously loaded produces identical classification output; new
heuristics and edge cases from the v3 research additions only affect generation
quality and edge-case classification accuracy.

## Relationship to rules_v3/

rules_v3/ and rules_v4/ share the same modular architecture pattern but are
sourced from different baselines:

| Aspect | rules_v3/ | rules_v4/ |
|---|---|---|
| Grammar source | Deprecated v3 grammar file | grammar_v7 (current production) |
| Reading source | Old v2 reading module (781 lines) | reading_v2 (1,450 lines, v1.0 + v1.1) |
| Research additions | Original placement | Carried forward into grammar module §20 |
| Production compatibility | Proven against v3 baseline | Proven against v7/v2 baseline |

rules_v4/ supersedes rules_v3/ as the recommended modular rule architecture.
