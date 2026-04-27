# Outline: rules_core_generation.md

## Purpose

Shared generation infrastructure for all DSAT Reading and Writing item
generation. This file defines the common workflow, output contract, realism
standards, and validation lifecycle. It does not define domain taxonomies.

## Proposed Outline

### 1. Scope and Load Order

- what this document covers
- what it explicitly does not cover
- required load order with one domain module

### 2. Core Operating Principles

- separate task layers
- controlled keys only
- evidence before invention
- no direct database writes
- one active domain module per item

### 3. Shared Output Contract

- top-level JSON shape
- required sections
- minimum required fields for generation outputs
- review object contract

### 4. Shared Generation Request Schema

- generation request object
- required fields
- optional fields
- invalid request conditions

### 5. Common Generation Workflow

- step 1 select domain
- step 2 load target module
- step 3 build passage or stimulus
- step 4 build stem
- step 5 build correct answer
- step 6 build distractors
- step 7 assemble metadata
- step 8 run validation
- step 9 retry or fail

### 6. Shared Passage and Stimulus Quality Rules

- self-contained
- no trivia dependence
- academic register
- one unambiguous correct answer
- difficulty from reasoning, not obscurity

### 7. Shared Distractor Engineering Rules

- every distractor needs one named failure mode
- every distractor needs a plausibility source
- no accidental second error
- distractors must survive first-pass elimination
- wrong answers should be attractive for a specific reason

### 8. SAT Realism Layer

- distractor distance
- answer separation strength
- plausible wrong count
- realism scoring expectations
- official similarity thresholds

### 9. Anti-Clone and Diversity Controls

- structural similarity threshold
- rewrite requirements
- topic rotation
- recent-exam avoidance

### 10. Provenance and Audit Trail

- template used
- generation chain
- validator interventions
- human override slot

### 11. Shared Validation Lifecycle

- core validation first
- domain validation second
- retry policy
- failure response shape

### 12. Amendment and Escalation Framework

- when to propose amendment
- when to reject request
- when to require human review

### 13. Cross-References

- required interfaces exposed by the grammar module
- required interfaces exposed by the reading module

## Notes on Source Derivation

Primary inputs:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md` sections 14, 20, 21-29
- `rules_agent_dsat_reading_v1.md` sections 16 and 20
