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

## 14. Realism Requirements Aligned to Core

Reading items must satisfy the same all-four-plausible requirement as grammar
items.

For reading items specifically:

- All four options must describe plausible interpretations of the passage on
  first read; no option may be obviously off-topic
- Wrong options should contain information that appears in the passage, but
  applied incorrectly (wrong scope, wrong inference, wrong attribution)
- The correct answer must be directly and unambiguously supported by evidence
  in the passage; the support cannot require an unanchored inference
- Difficulty comes from evidence competition, not from obscure or ambiguous
  passage content

Reading-specific `student_failure_mode_key` values:

- `local_detail_fixation` — student selects an option supported by a small
  detail but not the broader claim
- `overreach` — student selects an option that goes further than the passage
  supports
- `underreach` — student selects an option too narrow for the full claim
- `text_label_swap` — in cross-text items, student assigns an author's position
  to the wrong text
- `topic_association` — student selects an option merely because it mentions
  the same topic, without checking evidence
- `inverse_logic` — student selects an option that inverts the passage's
  direction of argument
- `false_agreement` — in cross-text items, student assumes both texts agree
  when they do not (or vice versa)

## Notes on Source Derivation

Primary inputs:

- `rules_agent_dsat_reading_v1.md` sections 3-20

Expansion required:

- reading needs a more detailed generation workflow and distractor heuristics so
  it reaches parity with the grammar module's operational specificity
- `student_failure_mode_key` values have been added in section 14 above and
  should be required for all reading item distractors in the same way they are
  required for grammar item distractors
