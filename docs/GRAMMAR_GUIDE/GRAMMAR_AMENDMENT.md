# Grammar Amendment Proposals

**Purpose**: Allow the LLM to suggest amendments to `GROUND_TRUTH_GRAMMAR.md` during ingestion when official College Board questions reveal gaps, edge cases, or patterns not covered by existing rules.

**Process**: LLM proposes → Human reviews quarterly → Migration updates lookup tables if approved

---

## When to Propose an Amendment

Propose an amendment if **ANY** of the following conditions are met:

### 1. No Matching Rule
The question clearly tests Standard English Conventions, but no existing `grammar_focus_key` accurately describes the rule being tested.

**Example**: A question tests a punctuation pattern not covered (e.g., ellipsis punctuation, slash usage).

### 2. Disambiguation Failure
The question fits multiple `grammar_focus_key` values, but the disambiguation priority rules don't resolve which to use.

**Example**: A question tests both modifier placement AND logical predication in a way not covered by existing priority rules.

### 3. New Distractor Pattern
The question uses a distractor pattern not documented in Part 6 (Distractor Patterns) of `GROUND_TRUTH_GRAMMAR.md`.

**Example**: A new type of agreement trap not covered by `nearest_noun_attraction` or `intervening_phrase_trap`.

### 4. New Syntactic Trap
The question exploits a parsing ambiguity not covered in Part 7 (Syntactic Traps).

**Example**: A new type of garden-path sentence structure.

### 5. Frequency Mismatch
The question appears frequently in official tests but is classified as "Very Low" frequency, suggesting the frequency data needs updating.

---

## Amendment Proposal Format

When proposing an amendment, the LLM should output a structured JSON block in the `reasoning.amendment_proposal` field of the Pass 2 annotation:

```json
{
  "amendment_proposal": {
    "proposal_type": "new_grammar_focus_key | new_distractor_pattern | new_syntactic_trap | disambiguation_update | frequency_update | rule_clarification",
    "priority": "high | medium | low",
    "question_id": "pt4_rw_m1_q21",
    "current_classification": {
      "grammar_role_key": "punctuation",
      "grammar_focus_key": "punctuation_comma"
    },
    "proposed_change": {
      "field": "grammar_focus_key",
      "new_value": "ellipsis_punctuation",
      "definition": "Punctuation with elliptical constructions where words are omitted",
      "mapping_to_grammar_role": "punctuation",
      "example_from_question": "The first study was completed, but the second [was completed] was not."
    },
    "rationale": "This question tests punctuation in an elliptical construction where the verb phrase is omitted. Existing punctuation_comma key covers non-restrictive clauses and series, but not ellipsis-specific punctuation patterns. This pattern appears in 3 of 10 official tests analyzed.",
    "supporting_evidence": {
      "official_tests_with_pattern": ["PT4_M1", "PT5_M2", "PT7_M1"],
      "estimated_frequency": "Low-Medium (1 per 3-4 modules)",
      "distractor_pattern": "Students omit comma before elliptical clause because 'was completed' is implied"
    },
    "disambiguation_note": "If question tests both ellipsis AND comma splice, prioritize sentence_boundary > ellipsis_punctuation per new Priority 12."
  }
}
```

---

## Proposal Types

### `new_grammar_focus_key`
Add a new specific rule to `lookup_grammar_focus`.

**Required fields**:
- `new_value`: The new key name
- `definition`: Clear rule definition
- `mapping_to_grammar_role`: Which broad category it belongs to
- `example_from_question`: Concrete example from the official question
- `disambiguation_note`: Where it fits in priority order

### `new_distractor_pattern`
Add a new distractor pattern to Part 6 of `GROUND_TRUTH_GRAMMAR.md`.

**Required fields**:
- `pattern_name`: Descriptive name for the pattern
- `description`: How the distractor works
- `example`: Concrete example from the question
- `affected_rule_keys`: Which `grammar_focus_key` values this pattern applies to

### `new_syntactic_trap`
Add a new trap to `lookup_syntactic_trap` and Part 7 of `GROUND_TRUTH_GRAMMAR.md`.

**Required fields**:
- `trap_key`: The new trap identifier
- `description`: How the trap works
- `example`: Concrete example
- `cognitive_mechanism`: Why students fall for it (parsing ambiguity, working memory load, etc.)

### `disambiguation_update`
Modify the priority rules or decision tree in Part 4.

**Required fields**:
- `current_rule`: The existing rule that needs modification
- `proposed_rule`: The updated rule
- `rationale`: Why the change is needed

### `frequency_update`
Update frequency data in Part 5 based on new official test evidence.

**Required fields**:
- `grammar_focus_key`: The rule to update
- `current_frequency`: Current listed frequency
- `proposed_frequency`: New frequency based on evidence
- `evidence`: List of official tests supporting the change

### `rule_clarification`
Add clarification or examples to an existing rule definition.

**Required fields**:
- `grammar_focus_key`: The rule to clarify
- `clarification`: What needs to be added or clarified
- `example`: Example that motivated the clarification

---

## Human Review Process

### Quarterly Review Checklist

Human reviewers evaluate proposals using these criteria:

1. **College Board Alignment**: Is this pattern actually tested on the Digital SAT, or is it ACT-adjacent or outdated paper SAT content?

2. **Frequency Threshold**: Does this pattern appear in at least 2 official Digital SAT practice tests?

3. **Distinctness**: Is this pattern distinct from existing rules, or is it a subtype already covered?

4. **Classification Stability**: Will adding this rule improve LLM classification consistency, or create more ambiguity?

5. **Generation Value**: Will this rule help generate more authentic questions?

### Approval Workflow

```
LLM Proposal (grammar_amendment.md)
         ↓
Human Review (quarterly)
         ↓
    ┌────┴────┐
    │         │
  Approved   Rejected
    │         │
    ↓         ↓
Create    Add to
Migration  "Rejected Proposals" log
    │
    ↓
Update lookup tables
    │
    ↓
Update GROUND_TRUTH_GRAMMAR.md
    │
    ↓
Deploy to production
```

---

## Rejected Proposals Log

**Purpose**: Track proposals that were rejected so the LLM doesn't re-propose them.

| Date | Proposal Type | Proposed Change | Reason for Rejection |
|------|---------------|-----------------|---------------------|
| *Empty — add rejected proposals here* | | | |

---

## Approved Amendments Log

**Purpose**: Track what changes were made and when.

| Date | Proposal Type | Change Made | Migration # |
|------|---------------|-------------|-------------|
| *Empty — add approved amendments here* | | | |

---

## LLM Instructions

When you encounter a question that doesn't fit existing rules:

1. **Do NOT force a classification** — If no rule fits, don't invent a value.
2. **Classify with best available rule** — Use the closest matching rule for the current ingestion.
3. **Add amendment proposal** — Include the `amendment_proposal` JSON in the `reasoning` section.
4. **Set confidence flag** — Set `annotation_confidence` to "low" if the classification is uncertain.
5. **Continue ingestion** — Don't block the pipeline; the amendment is for future improvement.

**Example Pass 2 Output with Amendment**:

```json
{
  "classification": {
    "domain_key": "standard_english_conventions",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "punctuation_comma",
    ...
  },
  "reasoning": {
    "amendment_proposal": {
      "proposal_type": "new_grammar_focus_key",
      "priority": "medium",
      "question_id": "pt11_rw_m2_q24",
      "current_classification": {
        "grammar_role_key": "punctuation",
        "grammar_focus_key": "punctuation_comma"
      },
      "proposed_change": {
        "field": "grammar_focus_key",
        "new_value": "nonessential_pair_consistency",
        "definition": "Nonessential elements must be set off by matched pairs (two commas, two dashes, or two parentheses — never mix types)",
        "mapping_to_grammar_role": "punctuation",
        "example_from_question": "The study—published in 2020), received attention."
      },
      "rationale": "This question tests the matched-pair rule for nonessential elements. Existing punctuation_comma covers individual comma usage but not the consistency requirement across pair types. This pattern appears in 4 of 10 official tests analyzed.",
      "supporting_evidence": {
        "official_tests_with_pattern": ["PT4_M1", "PT4_M2", "PT5_M1", "PT11_M2"],
        "estimated_frequency": "Medium (1 per 2-3 modules)"
      }
    },
    "annotation_confidence": "low"
  }
}
```

---

## Template: Copy-Paste for Proposals

```json
{
  "amendment_proposal": {
    "proposal_type": "",
    "priority": "high | medium | low",
    "question_id": "",
    "current_classification": {
      "grammar_role_key": "",
      "grammar_focus_key": ""
    },
    "proposed_change": {
      "field": "",
      "new_value": "",
      "definition": "",
      "mapping_to_grammar_role": "",
      "example_from_question": ""
    },
    "rationale": "",
    "supporting_evidence": {
      "official_tests_with_pattern": [],
      "estimated_frequency": ""
    },
    "disambiguation_note": ""
  }
}
```

---

*This document is maintained alongside `GROUND_TRUTH_GRAMMAR.md`. Review quarterly.*
