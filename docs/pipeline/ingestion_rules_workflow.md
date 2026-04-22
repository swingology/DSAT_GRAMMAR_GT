# LLM Ingestion Rules Workflow

**Purpose**: Document how the LLM uses `GROUND_TRUTH_GRAMMAR.md` during the two-pass ingestion pipeline for Standard English Conventions (SEC) questions.

**Scope**: Pass 1 (Extraction) → Pass 2 (Annotation) → Validation → Amendment Proposal

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Raw Input (PDF/Image/Markdown/Text)                                    │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ PASS 1: EXTRACTION                                              │   │
│  │ - Extract stem, passage, choices, correct answer                │   │
│  │ - Identify if question is SEC (Standard English Conventions)    │   │
│  │ - Output: QuestionExtract JSON                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ PASS 2: ANNOTATION                                              │   │
│  │ - Classify using GROUND_TRUTH_GRAMMAR.md                        │   │
│  │ - Select grammar_role_key + grammar_focus_key                   │   │
│  │ - Analyze distractors, write reasoning                          │   │
│  │ - Propose amendments if rules don't fit                         │   │
│  │ - Output: QuestionAnnotation JSON                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ VALIDATION                                                      │   │
│  │ - Check grammar_role_key against lookup_grammar_role            │   │
│  │ - Check grammar_focus_key against lookup_grammar_focus          │   │
│  │ - Verify mapping_to_grammar_role consistency                    │   │
│  │ - Reject if hallucinated values                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGING → HUMAN REVIEW → PRODUCTION                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pass 1: Extraction

### Purpose
Extract raw question structure without taxonomy classification.

### Input
- Raw text from PDF, image OCR, Markdown, or JSON

### Instructions for LLM

```python
# From app/prompts/pass1_extraction.py

SYSTEM_PROMPT = """
You are extracting Digital SAT Reading & Writing questions into structured JSON.

TASK: Extract the question's raw structure only. Do NOT classify or analyze taxonomy.

OUTPUT SCHEMA:
{
  "stem": str,                    # The question prompt text
  "passage": str | null,          # Passage text (if any)
  "choices": {                    # Exactly 4 choices
    "A": str,
    "B": str,
    "C": str,
    "D": str
  },
  "correct_option_label": str,    # One of: A, B, C, D
  "stimulus_mode_key": str,       # From lookup: sentence_only, prose_single, notes_bullets, etc.
  "stem_type_key": str            # From lookup: complete_the_text, choose_best_grammar_revision, etc.
}

RULES:
1. Extract EXACTLY what appears in the question — no paraphrasing
2. For SEC (grammar/punctuation) questions, the "choices" will often be punctuation or verb form variants
3. Set passage to null if no passage context is provided
4. Identify stimulus_mode_key from the allowed lookup values only
5. Identify stem_type_key from the allowed lookup values only

SEC QUESTION INDICATORS:
- Underlined portion with punctuation variants (comma, semicolon, dash, colon)
- Verb form choices (survives, survived, had survived, would survive)
- Pronoun choices (their, there, they're, its, it's)
- Sentence boundary testing (period vs. semicolon vs. comma)

If you identify an SEC question, still only extract — classification happens in Pass 2.
"""
```

### Output Validation
- `stem` is non-empty
- `choices` has exactly keys A, B, C, D
- `correct_option_label` exists in choices
- `stimulus_mode_key` and `stem_type_key` are valid lookup values

---

## Pass 2: Annotation

### Purpose
Classify the question using the ground truth grammar taxonomy.

### Input
- Extracted JSON from Pass 1
- Ontology reference (injected at runtime from `app.state.ontology`)
- `GROUND_TRUTH_GRAMMAR.md` (referenced in prompt)

### Instructions for LLM

```python
# From app/prompts/pass2_annotation.py

SYSTEM_PROMPT = """
You are annotating Digital SAT Reading & Writing questions with taxonomy classifications.

GRAMMAR CLASSIFICATION RULES:

1. FIRST: Determine if this is a Standard English Conventions (SEC) question.
   
   SEC questions test:
   - Sentence boundaries (fragments, run-ons, comma splices)
   - Punctuation (commas, semicolons, colons, dashes, apostrophes)
   - Agreement (subject-verb, pronoun-antecedent)
   - Verb forms (tense, mood, voice, finite/nonfinite)
   - Modifiers (placement, dangling, comparative)
   - Parallel structure
   - Pronoun case
   - Possessives

2. If SEC: Use GROUND_TRUTH_GRAMMAR.md to classify:
   
   a) Select grammar_role_key from:
      - sentence_boundary
      - agreement
      - verb_form
      - modifier
      - punctuation
      - parallel_structure
      - pronoun
   
   b) Select grammar_focus_key from the detailed list in GROUND_TRUTH_GRAMMAR.md Part 3.
      Use the Disambiguation Rules (Part 4) if multiple rules could apply.
   
   c) Verify your selection matches the frequency patterns in Part 5.

3. If NOT SEC (e.g., Words in Context, Main Idea, Transitions):
   - Set grammar_role_key = null
   - Set grammar_focus_key = null

4. If the question reveals a pattern NOT covered by GROUND_TRUTH_GRAMMAR.md:
   - Classify with the closest matching rule
   - Add an amendment_proposal to the reasoning section (see grammar_amendment.md)
   - Set annotation_confidence = "low"

DISAMBIGUATION PRIORITY (from GROUND_TRUTH_GRAMMAR.md Part 4):

1. sentence_boundary > punctuation (structural issues take precedence)
2. voice_active_passive > verb_form
3. logical_predication > modifier_placement
4. conjunction_usage > parallel_structure
5. pronoun_case > pronoun_antecedent_agreement
6. comparative_structures > modifier_placement
7. noun_countability > subject_verb_agreement
8. negation > verb_form
9. relative_pronouns > modifier_placement
10. possessive_contraction > apostrophe_use
11. hyphen_usage > punctuation

OUTPUT SCHEMA:
{
  "classification": {
    "domain_key": "standard_english_conventions" | "information_and_ideas" | ...,
    "skill_family_key": "form_structure_sense" | "boundaries" | ...,
    "grammar_role_key": str | null,  # From lookup_grammar_role
    "grammar_focus_key": str | null, # From lookup_grammar_focus
    ...
  },
  "options": [...],  # 4 options with distractor analysis
  "reasoning": {
    "primary_solver_steps": [...],
    "amendment_proposal": {...} | null,  # See grammar_amendment.md
    "annotation_confidence": "high" | "medium" | "low"
  },
  "generation_profile": {...}
}

CRITICAL RULES:
- Use ONLY allowed values from the ontology reference
- Never invent new keys
- If uncertain, choose the closest match and explain in review_notes
- Always check disambiguation rules before finalizing classification
"""
```

### Classification Decision Tree

```
                    ┌─────────────────────────────┐
                    │  Is this an SEC question?   │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
        ┌──────────┐        ┌──────────────┐    ┌──────────────┐
        │   YES    │        │  BOUNDARY    │    │ FORM/STRUCT  │
        │          │        │  (punct,     │    │ (agreement,  │
        │          │        │  boundaries) │    │  verb, etc.) │
        └────┬─────┘        └──────┬───────┘    └──────┬───────┘
             │                     │                   │
             │                     ▼                   │
             │            ┌─────────────────┐          │
             │            │ grammar_role =  │          │
             │            │ sentence_boundary│         │
             │            │ OR punctuation  │          │
             │            └─────────────────┘          │
             │                                         │
             └──────────────────┬──────────────────────┘
                                │
                                ▼
                     ┌─────────────────────────┐
                     │  Select grammar_role_key │
                     │  from 7 allowed values   │
                     └───────────┬──────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │  Select grammar_focus_key│
                     │  from 26 specific rules  │
                     └───────────┬──────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │  Apply disambiguation   │
                     │  rules if needed        │
                     └───────────┬──────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │  Check if pattern fits  │
                     │  existing rules         │
                     └───────────┬──────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
         ┌────────┐       ┌─────────────┐   ┌─────────────┐
         │ YES    │       │ PARTIAL FIT │   │ NO FIT      │
         │        │       │ (uncertain) │   │ (gap)       │
         └───┬────┘       └──────┬──────┘   └──────┬──────┘
             │                  │                  │
             │                  ▼                  │
             │           ┌─────────────┐           │
             │           │ Classify +  │           │
             │           │ add proposal│           │
             │           └─────────────┘           │
             │                                     │
             ▼                                     ▼
        ┌─────────┐                         ┌──────────────┐
        │ Finalize│                         │ Classify +   │
        │ JSON    │                         │ add proposal │
        └─────────┘                         └──────────────┘
```

---

## Validation

### Purpose
Enforce ontology conformity — reject hallucinated values.

### Validator Logic

```python
# From app/pipeline/validator.py

def validate_grammar_keys(job: IngestionJob) -> list[ValidationError]:
    """Validate grammar_role_key and grammar_focus_key against database."""
    errors = []
    
    # 1. Check grammar_role_key is valid
    if job.pass2_json.classification.grammar_role_key:
        if not is_valid_key('lookup_grammar_role', 
                            job.pass2_json.classification.grammar_role_key):
            errors.append(ValidationError(
                field='grammar_role_key',
                value=job.pass2_json.classification.grammar_role_key,
                message=f"Invalid grammar_role_key. Must be one of: {VALID_ROLE_KEYS}"
            ))
    
    # 2. Check grammar_focus_key is valid
    if job.pass2_json.classification.grammar_focus_key:
        if not is_valid_key('lookup_grammar_focus',
                            job.pass2_json.classification.grammar_focus_key):
            errors.append(ValidationError(
                field='grammar_focus_key',
                value=job.pass2_json.classification.grammar_focus_key,
                message=f"Invalid grammar_focus_key. Must be one of: {VALID_FOCUS_KEYS}"
            ))
    
    # 3. Check mapping_to_grammar_role consistency
    if (job.pass2_json.classification.grammar_role_key and 
        job.pass2_json.classification.grammar_focus_key):
        expected_role = get_mapping(job.pass2_json.classification.grammar_focus_key)
        if expected_role != job.pass2_json.classification.grammar_role_key:
            errors.append(ValidationError(
                field='grammar_role_key',
                value=job.pass2_json.classification.grammar_role_key,
                message=f"Mismatch: {job.pass2_json.classification.grammar_focus_key} "
                        f"maps to {expected_role}, not {job.pass2_json.classification.grammar_role_key}"
            ))
    
    # 4. Cross-field check: SEC questions MUST have grammar keys populated
    if (job.pass2_json.classification.domain_key == 'standard_english_conventions'
        and not job.pass2_json.classification.grammar_role_key):
        errors.append(ValidationError(
            field='grammar_role_key',
            value=None,
            message="SEC questions must have grammar_role_key populated"
        ))
    
    return errors
```

### Job Status Flow

```
pending
    │
    ▼
extracting ──────┐
    │            │
    ▼            │
annotating ──────┤
    │            │
    ▼            │
validating ◄─────┘
    │
    ├────► validation_failed (reject, can rerun)
    │
    ▼
reviewed
    │
    ├────► approved (upsert to production)
    │
    ▼
rejected
```

---

## Amendment Proposal Workflow

### When to Propose

See `grammar_amendment.md` Section 1 (When to Propose an Amendment).

### How to Propose

Include the proposal in Pass 2 output:

```json
{
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
        "definition": "Nonessential elements must use matched pairs",
        "mapping_to_grammar_role": "punctuation",
        "example_from_question": "The study—published in 2020), received."
      },
      "rationale": "Matched-pair rule not explicitly covered.",
      "supporting_evidence": {
        "official_tests_with_pattern": ["PT4_M1", "PT11_M2"],
        "estimated_frequency": "Medium"
      }
    },
    "annotation_confidence": "low"
  }
}
```

### Human Review Queue

Proposals are aggregated and presented to human reviewers quarterly:

```sql
-- Query pending amendment proposals
SELECT 
    j.source_exam,
    j.source_question_number,
    j.pass2_json->'reasoning'->'amendment_proposal' as proposal
FROM question_ingestion_jobs j
WHERE j.status = 'reviewed'
  AND j.pass2_json->'reasoning'->'amendment_proposal' IS NOT NULL
ORDER BY j.created_at;
```

### Review Decision

```
Proposal Received
       │
       ▼
┌──────────────────┐
│ Reviewer evaluates: │
│ 1. CB Alignment    │
│ 2. Frequency       │
│ 3. Distinctness    │
│ 4. Stability       │
│ 5. Generation Value│
└─────────┬────────┘
          │
    ┌─────┴─────┐
    │           │
  Approved    Rejected
    │           │
    ▼           ▼
┌─────────┐ ┌────────────────┐
│ Create  │ │ Add to         │
│ SQL     │ │ Rejected Log   │
│ Migration│ │ with reason   │
└────┬────┘ └────────────────┘
     │
     ▼
┌─────────────────┐
│ Update lookup   │
│ tables          │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Update          │
│ GROUND_TRUTH_   │
│ GRAMMAR.md      │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Deploy to       │
│ production      │
└─────────────────┘
```

---

## Error Handling

### Common Validation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `Invalid grammar_focus_key` | LLM hallucinated a value | Rerun with stricter prompt; add to rejected log |
| `Mapping mismatch` | grammar_focus_key doesn't map to grammar_role_key | LLM misapplied disambiguation; rerun |
| `SEC missing grammar keys` | domain=SEC but grammar_role_key is null | LLM failed to identify as SEC; rerun |
| `Multiple proposals for same rule` | Several questions triggered same amendment | Consolidate into single proposal |

### Rerun Strategy

```python
# Rerun with stricter constraints
RERUN_PROMPT_ADDENDUM = """
PREVIOUS ATTEMPT FAILED VALIDATION.

ADDITIONAL CONSTRAINTS:
1. Use ONLY the grammar_focus_key values listed in the ontology reference
2. If no rule fits perfectly, choose the CLOSEST match — do NOT invent new keys
3. Apply disambiguation priority rules in order (1-11)
4. If still uncertain, set annotation_confidence = "low" and add review_notes

DO NOT retry the same classification. Re-read GROUND_TRUTH_GRAMMAR.md Part 3-4.
"""
```

---

## Testing the Pipeline

### Test Cases

```python
# Test SEC question with clear rule
def test_sec_subject_verb_agreement():
    job = run_ingestion("PT4_M1_Q22")  # Agreement question
    assert job.classification.grammar_role_key == "agreement"
    assert job.classification.grammar_focus_key == "subject_verb_agreement"
    assert job.validation_errors == []

# Test SEC question with ambiguous rule
def test_sec_boundary_punctuation():
    job = run_ingestion("PT11_M2_Q23")  # Boundary + punctuation
    # Should apply disambiguation priority 1
    assert job.classification.grammar_role_key == "sentence_boundary"
    assert job.validation_errors == []

# Test non-SEC question
def test_words_in_context():
    job = run_ingestion("PT4_M1_Q1")  # Vocabulary question
    assert job.classification.grammar_role_key is None
    assert job.classification.grammar_focus_key is None
    assert job.validation_errors == []

# Test amendment proposal
def test_amendment_triggered():
    job = run_ingestion("PT11_M2_Q24")  # Edge case
    assert job.reasoning.amendment_proposal is not None
    assert job.reasoning.annotation_confidence == "low"
```

---

## Metrics

Track these metrics to monitor pipeline health:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| SEC classification accuracy | >95% | <90% |
| Amendment proposal rate | <5% | >10% |
| Validation pass rate | >98% | <95% |
| Disambiguation overrides | <2% | >5% |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-18 | Initial workflow documentation |

---

*This document should be updated when `GROUND_TRUTH_GRAMMAR.md` or the ingestion prompts change.*
