# DSAT Rules v4 — Modular Rule Architecture

This directory provides a modular, single-source-of-truth rule architecture for
DSAT Reading and Writing ingestion, classification, generation, and validation.

v4 is built from the two current production-grade source files:

- `rules_agent_dsat_grammar_ingestion_generetion_v7.md` (grammar source)
- `rules_agent_dsat_reading_v2.md` (reading source)

v4 reorganizes them into a core + domain-module layout identical in structure to
rules_v3/, but sourced from the latest production files instead of the
deprecated v3 grammar baseline. The original source files remain authoritative;
v4 does not intentionally rename production keys or change validator semantics.

## What v4 Adds Over the Source Files

- **Modular load order**: Core loaded once, then only the needed domain module.
  Eliminates the need to load a 2,400-line monolithic file for every task.
- **Clean domain isolation**: Grammar and reading taxonomy keys are physically
  separated. No cross-domain key leakage.
- **Research-backed additions**: The v3 research additions (Boundaries Decision
  Tree, FSS Edge Case Appendix, Authenticity Anti-Patterns, DSAT Trends) are
  carried forward into the v4 grammar module.
- **Single reading source**: The reading module is sourced from the consolidated
  reading_v2 (1,450 lines, merging v1.0 + v1.1 addendum), replacing the older
  v2 reading module used in rules_v3/.

## Files

1. `rules_core_generation.md`
   - Shared output shape, generation workflow, realism controls, validation
     lifecycle, difficulty/topic targeting, provenance, errors, and batch rules.
   - No grammar or reading taxonomy is defined here.

2. `rules_dsat_grammar_module.md`
   - Standard English Conventions and grammar-adjacent Expression of Ideas.
   - Grammar role/focus keys, mappings, syntactic traps, no-change behavior,
     tense/register metadata, passage construction rules, distractor heuristics,
     grammar validator checklist, worked examples.
   - **Carried forward from v3**: Boundaries Decision Tree (§25), FSS Edge Case
     Appendix (§26), Authenticity Anti-Patterns (§27), DSAT Trends (§28).

3. `rules_dsat_reading_module.md`
   - Information and Ideas plus Craft and Structure.
   - 7 reading skill families with full classification schemas, 14 student
     failure mode keys, polarity_fit WIC rules, quantitative sub-patterns,
     cross-text rules, reading validator checklist.

4. `rules_migration_map.md`
   - Tracks which source sections mapped to which v4 files.
   - Loading recipes for grammar generation, reading generation, and ingestion.
   - Compatibility checklist for replacing production prompts.

## Runtime Load Order

### Ingestion / Classification of Unknown Items

1. Load `rules_core_generation.md`.
2. Load both domain modules.
3. Classify domain first.
4. Apply exactly one domain module to the final output.

### Generation with a Known Domain

1. Load `rules_core_generation.md`.
2. Load only the selected domain module.
3. Use `generation_request.domain` to reject cross-domain fields before writing
   an item.

### Minimal Load (Grammar Only)

1. Load `rules_core_generation.md`.
2. Load `rules_dsat_grammar_module.md`.

### Minimal Load (Reading Only)

1. Load `rules_core_generation.md`.
2. Load `rules_dsat_reading_module.md`.

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

The grammar source file is `rules_agent_dsat_grammar_ingestion_generetion_v7.md`
(a consolidation of v3 base + v3.1 PT4–PT11 gap additions, with v7 taxonomy
corrections from a cross-referenced audit against College Board official
documentation, Khan Academy, The Critical Reader, PrepScholar, Test Innovators,
Albert.io, and released practice tests PT1–PT11).

The reading source file is `rules_agent_dsat_reading_v2.md` (a consolidation of
reading v1.0 base + v1.1 PT4–PT11 gap-analysis addendum).

For conflict resolution:

1. Backend schema and validator behavior wins for persisted fields.
2. Root source files win over this refactor if a compatibility question arises.
3. This refactor wins for load order, domain separation, and reduced overlap.
4. New keys require an amendment proposal before production use.
5. Where v3 research additions (§25-28) conflict with grammar_v7, grammar_v7 wins.
