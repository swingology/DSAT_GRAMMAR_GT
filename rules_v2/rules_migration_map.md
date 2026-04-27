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
| `rules_core_generation.md` | shared output shape, option contract, generation workflow, realism, difficulty controls, provenance, batch/error format | grammar 1-2, 14, domain-neutral parts of 20-29; reading 1-2, 16, 20 |
| `rules_dsat_grammar_module.md` | grammar taxonomy, grammar validation, grammar generation, grammar-specific traps and heuristics | grammar 3-13, 17-20, grammar-specific parts of 21-29 |
| `rules_dsat_reading_module.md` | reading taxonomy, reading validation, reading generation, evidence/trap/cross-text/quantitative rules | reading 3-20 |

## Intentional De-Duplications

The following now live only in `rules_core_generation.md`:

- top-level output shape
- shared question fields
- shared option fields
- shared difficulty fields
- shared topic controls
- general generation workflow
- general realism and distractor-competition fields
- provenance and audit trail
- batch and error response formats
- amendment process shape

The following now live only in `rules_dsat_grammar_module.md`:

- `grammar_role_key`
- `grammar_focus_key`
- `secondary_grammar_focus_keys`
- `syntactic_trap_key`
- grammar role/focus mapping
- no-change metadata
- tense/register metadata
- grammar frequency bands
- grammar passage/distractor heuristics

The following now live only in `rules_dsat_reading_module.md`:

- `skill_family_key`
- `reading_focus_key`
- `secondary_reading_focus_keys`
- `reasoning_trap_key`
- `text_relationship_key`
- reading skill/focus mapping
- Cross-Text `paired_passage_text` requirements
- Quantitative CoE `table_data`/`graph_data` requirements
- reading passage architecture and distractor heuristics

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

