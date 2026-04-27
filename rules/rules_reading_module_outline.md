# Outline: rules_dsat_reading_module.md

## Purpose

Domain module for Information and Ideas plus Craft and Structure. This file
defines reading-specific taxonomies, evidence models, reasoning trap types,
generation heuristics, and validation rules. It assumes the shared core
generation file is already loaded.

## Proposed Outline

### 1. Scope and Domain Boundary

- covered domains
- explicit prohibition on grammar-role taxonomy
- domain selection rules

### 2. Reading-Specific Question Fields

- reading-relevant stimulus modes
- reading stem families
- paired-passage and quantitative field requirements

### 3. Classification Model

- question family keys
- skill family keys
- reading focus keys
- answer mechanism keys
- solver pattern keys

### 4. Skill Families and Focus Keys

- command of evidence textual
- command of evidence quantitative
- central ideas and details
- inferences
- words in context
- text structure and purpose
- cross-text connections

### 5. Reasoning Trap Taxonomy

- reading trap keys
- plausibility sources
- evidence-location semantics

### 6. Text Relationship Framework

- cross-text relationship keys
- agreement vs contradiction vs qualification
- when paired passages are required

### 7. Skill-Specific Annotation Rules

- evidence support items
- quantitative evidence items
- central idea items
- inference completions
- words in context items
- purpose and sentence-function items
- cross-text items

### 8. Reading Generation Request Constraints

- allowed stimulus modes by skill
- allowed stem types by skill
- passage architecture expectations
- difficulty and passage-length guidance

### 9. Reading Generation Workflow Additions

- passage construction by skill family
- claim/evidence alignment checks
- paired-passage generation sequence
- quantitative graphic integration rules

### 10. Reading Distractor Heuristics by Skill Family

- topical but unsupported distractors
- downstream evidence distractors
- inverted-logic distractors
- overbroad summary distractors
- local-detail traps
- tone/precision traps
- cross-text stance traps

### 11. Reading Realism Constraints

- evidence must directly anchor the correct answer
- difficulty from competition, not obscure content
- quantitative items must use data accurately
- cross-text tension must be genuine

### 12. Reading Validation Checklist

- legal skill/focus pairing
- evidence span completeness
- paired-passage requirements
- table/graph requirements
- exactly one supported answer
- cross-domain key rejection

### 13. Worked Examples

- one example per major skill family
- one paired-passage example
- one quantitative evidence example

## Notes on Source Derivation

Primary inputs:

- `rules_agent_dsat_reading_v1.md` sections 3-20

Expansion required:

- reading needs a more detailed generation workflow and distractor heuristics so
  it reaches parity with the grammar module's operational specificity
