# Deep analysis reference

The authoritative supplemental contract and controlled `da.*` vocabulary are in
[deep analysis v1.0.0](../../../chatgpt_refactor_rules/deep_analysis/1.0.0/RULES.md).
Use those local terms only in the report; existing production keys still come
from the master vocabulary. This document is the report checklist.

## Required report fields

### Source and preservation

- `question_id`, release year, test/exam, section, module, question number
- source content origin, version IDs, current text, paired text, graph/table data
- exact original annotation JSON and option rows, clearly marked as snapshots
- retrieval timestamp, database name, read-only method, rules and vocabulary versions

### Classification

- `question_family_key`, domain, skill family, focus key, stem type
- answer mechanism, solver pattern, reasoning or syntactic trap
- difficulty requested/annotated/estimated, confidence, review state
- grammar role/focus only when grammar is the assessed construct

### Sentence and clause anatomy

For grammar items, identify spans and relations rather than only labels:

- clause boundaries and independent/dependent status
- finite verbs, verbals, auxiliaries, tense/aspect/voice
- subject head and agreement controller; intervening nouns or clauses
- modifier span, attachment target, dangling risk, relative/appositive role
- coordination, subordination, complement structure, comparison terms
- punctuation mark, opening/closing delimiter, and construction function
- blank/underlined span and the constraint it imposes

For reading items, annotate the sentence structures that affect interpretation,
but keep those observations separate from the assessed reading skill.

### Style observations

Record observed evidence for genre, register, stance, attribution, hedging,
information flow, sentence-length variation, nominalization, passive use,
technical vocabulary, and rhetorical architecture. Do not require every style
feature in every short passage; mark not applicable when appropriate.

### Trap and distractor anatomy

For the question: structural/reasoning trap, target construct, and evidence
that instantiates it. For each option: correctness, primary error, violated
constraint, plausibility source, student failure hypothesis, evidence or rule
that defeats it, and whether the option is co-correct or malformed.

Use only active values from `vocabulary/master.json`. A proposed or publisher
label may be recorded as `source_label` with provenance, never silently promoted
to a production key.

## Validation checklist

- The original payload is unchanged in the snapshot.
- Exactly four options are present when the source format requires four.
- Exactly one option is defensible; otherwise set `needs_human_review`.
- The stored answer label agrees with the option marked correct.
- Every option has an analysis; every distractor has a named primary error.
- Canonical keys validate against the active vocabulary and correct domain.
- Evidence spans occur in the source text or are marked unavailable.
- Grammar fields are null for reading items unless a separate observed feature
  is explicitly stored outside classification.
- Style observations are evidence-based and do not become skill labels.
- Unknown, ambiguous, and not-applicable states are distinct.
- No database mutation, historical rewrite, or invented metric is claimed.
