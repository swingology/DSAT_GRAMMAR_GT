# Rules v2 Migration Map

This file maps the original working rule files into the v2 layout. It exists to
prevent future drift.

## Source Files

- Grammar source: `rules_agent_dsat_grammar_ingestion_generation_v3.md`
- Reading source: `rules_agent_dsat_reading_v1.md`

The original source files are proven against existing Claude ground-truth tests.
The v2 files reorganize them; they do not intentionally rename production keys
or change validator semantics.

## v2 File Responsibilities

| v2 file | Responsibility | Source sections |
|---|---|---|
| `README.md` | load order, source authority, production compatibility | original important notes and operational assumptions |
| `rules_core_generation.md` | shared output shape, stimulus/stem approved values, option contract, precision_score scale, difficulty calibration rubric, generation workflow, realism, student failure modes (shared + domain-specific), provenance, batch/error format, amendment process (with frequency_estimate and example_count) | grammar 1-2, 3.1-3.3, 10.4, 14, 17.12-17.14, domain-neutral parts of 20-29; reading 1-2, 12.3-12.4, 16, 20 |
| `rules_dsat_grammar_module.md` | grammar taxonomy, all syntactic trap keys (13 approved values), passage construction rules (all focus keys), distractor heuristics (all focus keys), evidence span rules (grammar), grammar validation, grammar generation, no-change rules, tense/register metadata, complete worked examples | grammar 3-13, 17-20, grammar-specific parts of 21-29, complete examples from 20.5 |
| `rules_dsat_reading_module.md` | reading taxonomy, all passage architecture keys (17 values), reading validation, reading generation, evidence/trap/cross-text/quantitative rules, evidence span rules (reading), option_error_focus_key guidance, Words in Context three-level distinction, response-stem critical rule | reading 3-20 |

## Intentional De-Duplications

The following now live only in `rules_core_generation.md`:

- top-level output shape
- shared question fields
- shared option fields
- shared difficulty fields and calibration rubric
- shared topic controls
- stimulus_mode_key and stem_type_key approved value enumerations
- precision_score scale (1/2/3)
- general generation workflow
- general realism and distractor-competition fields
- all approved student failure mode keys (shared, grammar-specific, reading-specific)
- provenance and audit trail
- batch and error response formats
- amendment process shape (with frequency_estimate, example_count, examples)

The following now live only in `rules_dsat_grammar_module.md`:

- `grammar_role_key`
- `grammar_focus_key`
- `secondary_grammar_focus_keys`
- `syntactic_trap_key` (13 approved values including `early_clause_anchor`, `pronoun_ambiguity`, `temporal_sequence_ambiguity`, `multiple`)
- grammar role/focus mapping table
- grammar disambiguation rules (14 priority rules)
- grammar decision tree (10 steps)
- no-change metadata and no-change generation rules
- tense/register metadata and approved register/tense keys
- grammar frequency bands
- passage construction rules for ALL approved grammar focus keys (~30 rules)
- distractor heuristics for ALL major grammar focus families (~18 tables)
- evidence span selection rules (grammar-specific)
- option text format rules (fill-in-blank, full-replacement, punctuation-only)
- grammar explanation requirements
- grammar validator checklist
- complete worked generation examples (subject-verb agreement, semicolon use)

The following now live only in `rules_dsat_reading_module.md`:

- `skill_family_key`
- `reading_focus_key`
- `secondary_reading_focus_keys`
- `reasoning_trap_key` (16 Information and Ideas traps, 13 Craft and Structure traps)
- `text_relationship_key` (6 approved values)
- reading skill/focus mapping table
- reading disambiguation rules (6 priority rules)
- answer mechanism keys (7 values) and solver pattern keys (8 values)
- Cross-Text `paired_passage_text` requirements and response-stem critical rule
- Quantitative CoE `table_data`/`graph_data` requirements
- reading passage architecture keys (17 values)
- `option_error_focus_key` guidance for reading domains
- Words in Context three-level wrong-answer distinction
- reading distractor heuristics and failure mode tables by skill
- evidence span selection rules (reading-specific)
- reading difficulty calibration by skill
- reading validator checklist

## Compatibility Checks Before Replacing Prompts

Before using v2 as the only LLM rule source in production prompts, confirm:

- [ ] a grammar ingestion prompt using core + grammar produces the same top-level
      sections as the original grammar file
- [ ] a reading ingestion prompt using core + reading produces the same top-level
      sections as the original reading file
- [ ] a mixed-domain ingestion prompt using all three v2 files correctly routes
      Expression of Ideas to grammar and Information/Craft items to reading
- [ ] generated grammar items include role, focus, trap, frequency, option
      error keys, and no-change/tense fields when required
- [ ] generated reading items include skill, focus, reasoning trap, evidence
      span, and null grammar keys
- [ ] Cross-Text generated items always include `paired_passage_text`
- [ ] Quantitative CoE generated items always include `table_data` or
      `graph_data`
- [ ] no production output includes keys not listed in core or the active domain
      module
- [ ] all 13 syntactic trap keys from the v3 source are available and functional
- [ ] passage construction rules exist for every approved grammar focus key
- [ ] distractor heuristic tables exist for every major grammar focus family
- [ ] student_failure_mode_key values used in grammar and reading heuristics are
      all present in the core approved list (§8.4)
- [ ] evidence span selection rules are applied for both grammar and reading items
- [ ] amendment proposals include frequency_estimate and example_count fields
- [ ] precision_score scale and difficulty calibration rubric are accessible from
      core without loading a domain module
- [ ] Words in Context items classify wrong-option failures at the three-level
      denotation/connotation/register distinction

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

Load all three v2 rule files, then require the model to:

1. select domain first
2. discard inactive domain taxonomies
3. emit exactly one domain's classification fields
4. run core validation
5. run active-domain validation

