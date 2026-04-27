# DSAT Rules v2 Loader

This directory is the production refactor of the two proven root rule files:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md`
- `rules_agent_dsat_reading_v1.md`

The original files remain source-of-truth artifacts. This v2 directory preserves
their output contracts and controlled keys while separating shared behavior from
domain behavior so ingestion and generation are easier to load consistently.

## Files

1. `rules_core_generation.md`
   - Shared output shape, generation workflow, realism controls, validation
     lifecycle, difficulty/topic targeting, provenance, errors, and batch rules.
   - No grammar or reading taxonomy is defined here.

2. `rules_dsat_grammar_module.md`
   - Standard English Conventions and grammar-adjacent Expression of Ideas.
   - Grammar role/focus keys, mappings, syntactic traps, no-change behavior,
     tense/register metadata, grammar generation controls, and grammar
     validation.

3. `rules_dsat_reading_module.md`
   - Information and Ideas plus Craft and Structure.
   - Reading skill/focus keys, evidence mechanisms, reasoning traps,
     cross-text and quantitative requirements, reading generation controls, and
     reading validation.

## Runtime Load Order

For ingestion/classification of unknown Digital SAT Reading and Writing items:

1. Load `rules_core_generation.md`.
2. Load both domain modules.
3. Classify domain first.
4. Apply exactly one domain module to the final output.

For generation with a known domain:

1. Load `rules_core_generation.md`.
2. Load only the selected domain module.
3. Use `generation_request.domain` to reject cross-domain fields before writing
   an item.

Do not mix grammar and reading taxonomy keys in one item. A generation run may
target difficulty, topic, stem family, focus key, trap key, or passage
architecture, but the generated output must still satisfy the same controlled
key and validator contract as ingestion.

## Production Compatibility Contract

- Preserve the top-level output shape:
  `question`, `classification`, `options`, `reasoning`, `generation_profile`,
  `review`.
- Preserve exactly four answer options and exactly one correct option for DSAT
  multiple-choice items.
- Preserve the original controlled key names unless an amendment is explicitly
  proposed.
- Never emit proposed keys as production keys.
- For reading domains, `grammar_role_key`, `grammar_focus_key`, and
  `syntactic_trap_key` must be null or omitted.
- For grammar domains, reading-only keys must be null or omitted unless they are
  shared fields defined by the core contract.
- Backend validators remain authoritative for database writes.

## Source Authority

The grammar source file is a V3 consolidation layer on top of the user's larger
V2 grammar baseline. This v2 refactor must not be read as narrowing that
baseline. Where this refactor is silent, preserve the proven behavior from the
root source files and any existing validator expectations.

For conflict resolution:

1. Backend schema and validator behavior wins for persisted fields.
2. Root source files win over this refactor if a compatibility question arises.
3. This refactor wins for load order, domain separation, and reduced overlap.
4. New keys require an amendment proposal before production use.

