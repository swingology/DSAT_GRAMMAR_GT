# DSAT Rules Refactor Plan

## Goal

Restructure the current rules system into three documents:

1. one shared core generation rules document
2. one grammar-domain module
3. one reading-domain module

The objective is to reduce duplication, improve retrieval during generation,
and preserve strict domain separation.

## Current State Summary

The current rule system is split across:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md`
- `rules_agent_dsat_reading_v1.md`

This split is directionally correct because the grammar and reading domains use
different taxonomies, different failure modes, and different generation logic.
However, the split is incomplete because:

- both documents repeat core operating principles and output shape rules
- the grammar document contains a much more mature generation protocol
- realism, distractor competition, validation, and provenance logic live only
  in the grammar document even though most of those ideas are cross-domain
  generation concerns
- reading generation guidance is lighter and less operationalized

## Recommendation

Do not merge everything into one monolithic file.

Adopt a three-document architecture:

1. `rules_core_generation.md`
2. `rules_dsat_grammar_module.md`
3. `rules_dsat_reading_module.md`

## Design Principles

- Keep domain-specific taxonomies out of the core file.
- Keep shared generation mechanics out of domain modules.
- Make the core file required for all generation tasks.
- Make exactly one domain module active per item.
- Preserve explicit domain boundaries:
  - grammar module covers Standard English Conventions plus
    grammar-adjacent Expression of Ideas
  - reading module covers Information and Ideas plus Craft and Structure
- Avoid duplicated validator logic unless the rule is truly domain-specific.

## Document Responsibilities

### 1. Core generation document

Owns:

- global operating principles
- shared output schema
- generation request schema
- common passage quality rules
- distractor engineering standards
- realism and anti-clone checks
- provenance and audit trail
- cross-domain validation lifecycle
- regeneration and failure handling

Must not own:

- grammar taxonomy keys
- reading taxonomy keys
- grammar-only distractor heuristics
- reading-only stem families or passage constraints

### 2. Grammar module

Owns:

- SEC and grammar-adjacent Expression of Ideas classification logic
- grammar role and focus taxonomies
- grammar disambiguation rules
- grammar-only distractor heuristics
- grammar-specific passage construction rules
- grammar-specific validation requirements

Depends on core for:

- shared workflow
- shared realism thresholds
- shared provenance fields
- shared output structure

### 3. Reading module

Owns:

- Information and Ideas taxonomy
- Craft and Structure taxonomy
- reading focus keys
- evidence mechanism rules
- text relationship rules
- reading-specific distractor heuristics
- paired-passage and quantitative passage constraints
- reading-specific validation requirements

Depends on core for:

- shared workflow
- shared realism thresholds
- shared provenance fields
- shared output structure

## Concrete Migration Plan

### Phase 1: Define the core boundary

Extract and normalize the sections that should become shared infrastructure:

- operating principles
- required output shape
- review/amendment framing where not domain-specific
- shared generation quality constraints
- distractor engineering philosophy
- realism scoring
- anti-clone rules
- provenance and audit trail
- final validation lifecycle

Primary source for this extraction:

- grammar V3 Sections 20-29

Secondary source:

- reading Sections 16-20 where those sections express cross-domain generation
  norms rather than reading-specific rules

### Phase 2: Slim the grammar module

Retain only grammar-owned logic:

- question fields only if grammar-specific
- grammar classification fields
- grammar role/focus mappings
- grammar decision tree
- syntactic trap keys
- grammar option-level analysis requirements
- no-change rules
- multi-error rules
- tense/register rules
- grammar generation heuristics by focus key

Remove or relocate to core:

- repeated output schema
- generic generation quality statements
- generic validation statements
- generic distractor philosophy
- provenance and realism framework

### Phase 3: Strengthen the reading module

Keep reading-owned logic:

- reading question families
- skill family keys
- reading focus keys
- answer mechanism keys
- solver pattern keys
- reasoning trap keys
- text relationship keys
- skill-specific annotation rules
- reading passage architecture constraints
- reading disambiguation rules

Add or expand:

- generation request schema aligned with core
- stepwise generation workflow parallel to grammar
- reading-specific distractor heuristics by skill family
- realism requirements adapted for evidence-based reading items
- stronger validation checklist for generation-time use

### Phase 4: Normalize cross-document contracts

Define exact handoff rules:

- every generation flow begins with the core document
- the domain is selected before domain rules are loaded
- once a domain is selected, only that module's taxonomy keys are legal
- the core validator runs first for shared checks
- the domain validator runs second for domain-specific checks

### Phase 5: Publish a load order

Recommended runtime load order:

1. `rules_core_generation.md`
2. `rules_dsat_grammar_module.md` or `rules_dsat_reading_module.md`

Never load both domain modules for the same item generation run unless the
task is meta-analysis rather than actual generation.

## Section Mapping From Current Files

### Move mostly into core

From grammar V3:

- section 1 operating principles
- section 2 output shape
- section 14 generic generation rules
- section 20 generation workflow shell
- sections 21-29 realism, competition, similarity, provenance, validation

From reading V1:

- section 1 operating principles
- section 2 output shape
- section 16 generic generation quality constraints
- section 20 validator checklist structure

### Keep in grammar module

From grammar V3:

- sections 3-13
- section 17 schema guardrails where grammar-specific
- section 18 correction examples
- section 19 final output requirements if grammar-specific
- section 20.3, 20.4, 20.8, 20.14, 20.15 where tied to grammar behavior

### Keep in reading module

From reading V1:

- sections 3-15
- section 16.4 words-in-context and cross-text constraints
- section 17 disambiguation rules
- section 18 forbidden patterns
- section 19 amendment process if reading-specific
- section 20 validator checklist for reading domains

## Risks To Manage

- The grammar document currently mixes baseline V2 content with V3 addendum
  language, so extraction can blur source authority unless the new files state
  precedence explicitly.
- Some realism rules were written with grammar items in mind and will need
  rewording before they become truly domain-neutral.
- Reading currently lacks the same level of operational generation detail as
  grammar, so the reading module will need genuine expansion rather than simple
  extraction.
- Shared schema fields must be declared in exactly one place to avoid drift.

## Acceptance Criteria

The refactor is successful when:

- an agent can generate a grammar item using only the core file plus grammar
  module
- an agent can generate a reading item using only the core file plus reading
  module
- no taxonomy key is defined in more than one file
- shared generation fields are defined only in the core file
- domain validators reject keys from the other domain
- the reading module reaches comparable operational specificity to the grammar
  module

## Recommended Build Order

1. Draft `rules_core_generation.md`.
2. Refactor the grammar module against the new core contract.
3. Refactor the reading module against the same core contract.
4. Add a short top-level loader note to each document describing when it should
   be used.
5. Run a consistency pass on field names, validation order, and required keys.
