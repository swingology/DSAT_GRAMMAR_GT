# Outline: rules_dsat_grammar_module.md

## Purpose

Domain module for Standard English Conventions and grammar-adjacent Expression
of Ideas. This file defines grammar-specific classification keys, trap models,
generation heuristics, and validation rules. It assumes the shared core
generation file is already loaded.

## Proposed Outline

### 1. Scope and Domain Boundary

- covered domains
- excluded domains
- rule-domain separation from reading

### 2. Grammar-Specific Question Fields

- stimulus modes used in grammar generation
- grammar-relevant stem types
- domain-specific field constraints

### 3. Classification Model

- domain
- question family keys
- grammar role keys
- grammar focus keys
- expression-of-ideas handling

### 4. Grammar Role to Focus Mapping

- approved mappings
- invalid combinations
- amendment path for missing mappings

### 5. Decision Tree and Disambiguation

- SEC vs expression of ideas
- sentence boundary vs punctuation
- agreement vs verb form
- modifier vs logic
- multi-rule prioritization

### 6. Trap Taxonomy

- syntactic trap keys
- trap intensity
- when each trap applies

### 7. Option-Level Grammar Analysis

- wrong option error key requirements
- plausibility source rules
- grammar fit vs meaning fit handling
- precision score semantics

### 8. Special Grammar Cases

- no-change questions
- multi-error questions
- tense/register metadata
- original-text handling

### 9. Grammar Generation Constraints

- frequency guidance
- passage-length norms for grammar items
- revision-zone clarity
- grammar-specific stem wording

### 10. Passage Rules by Grammar Focus

- subject-verb agreement
- verb tense consistency
- modifier placement
- punctuation families
- pronouns
- parallel structure
- expression-of-ideas overlaps

### 11. Distractor Heuristics by Grammar Focus

- target primary trap distractor
- secondary distractor families
- forbidden distractor constructions

### 12. Grammar Validation Checklist

- role/focus consistency
- option error specificity
- no-change metadata
- tense/register completeness
- cross-domain key rejection

### 13. Worked Examples

- representative SEC examples
- representative expression-of-ideas examples
- correction examples for ambiguous cases

## Notes on Source Derivation

Primary inputs:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md` sections 3-13, 17-20
