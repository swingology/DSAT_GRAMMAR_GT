# DSAT Core Generation Rules

## Purpose

Shared generation infrastructure for all DSAT Reading and Writing item
generation. This file defines the common workflow, output contract, realism
standards, and validation lifecycle. It does not define domain taxonomies.

Load order: this file first, then exactly one domain module.

---

## 1. Scope and Load Order

This document covers:

- global operating principles
- shared output schema
- generation request schema
- common passage quality rules
- distractor engineering standards
- SAT realism layer
- anti-clone and diversity controls
- provenance and audit trail
- shared validation lifecycle

This document does not cover:

- grammar taxonomy keys (see `rules_dsat_grammar_module.md`)
- reading taxonomy keys (see `rules_dsat_reading_module.md`)
- domain-specific distractor heuristics

Required load order:

1. This file (always)
2. `rules_dsat_grammar_module.md` OR `rules_dsat_reading_module.md`

Never load both domain modules for the same item generation run.

---

## 2. Core Operating Principles

### 2.1 Separate the task layers

For every item, separate:

1. what the item tests
2. how the item is structured
3. what rule or reasoning mechanism solves it
4. why the correct answer is correct
5. why each wrong option is tempting
6. why each wrong option is wrong

### 2.2 Controlled keys only

The agent must use only approved lookup keys. If no key fits, propose an
amendment. Do not invent production keys.

### 2.3 Evidence before invention
               
The correct answer must be supportable from the passage alone. If the passage
does not provide enough information to justify the correct answer, rewrite
the passage.

### 2.4 No direct database writes

Output structured JSON or markdown for validation. A deterministic backend
validator performs all database writes.

### 2.5 One active domain module per item

Do not mix grammar keys and reading keys within a single item's classification.

---

## 3. Shared Output Contract

Every generated item must include:

```json
{
  "question": {},
  "classification": {},
  "options": [],
  "reasoning": {},
  "generation_profile": {},
  "review": {}
}
```

Required top-level fields:

- `source_exam`: `"GENERATED"` for synthetic items
- `stimulus_mode_key`: controls passage type
- `stem_type_key`: controls question wording
- `correct_option_label`: A, B, C, or D
- `explanation_short`: ≤25 words
- `explanation_full`: ≤150 words

---

## 4. Shared Generation Request Schema

```json
{
  "generation_request": {
    "domain": "Standard English Conventions | Expression of Ideas | ...",
    "target_focus_key": "...",
    "difficulty_overall": "low | medium | high",
    "topic_broad": "science | history | literature | ...",
    "topic_fine": "free text",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only | passage_excerpt | ...",
    "stem_type_key": "complete_the_text | ...",
    "avoid_recent_exam_ids": [],
    "generation_context": "free text explaining the generation goal"
  }
}
```

Reject any request that:

- Uses an unapproved focus key
- Maps a focus key to the wrong role key
- Requests a `very_low` frequency item without justification
- Omits required fields

---

## 5. Common Generation Workflow

Execute in this exact order. Each step is blocking.

1. Select domain (grammar or reading)
2. Load the correct domain module
3. Build passage or stimulus
4. Build stem
5. Build correct answer
6. Build distractors
7. Assemble metadata
8. Run validation
9. Retry or fail

---

## 6. Shared Passage and Stimulus Quality Rules

All passages must be:

- Self-contained: no outside knowledge required
- Academic register: no contractions, slang, or first person
- One unambiguous correct answer: the passage must provide enough information
  to justify exactly one choice
- Formal and neutral: no partisan, offensive, or trivially entertaining content
- Not trivia-dependent: the grammar or reasoning should be testable without
  knowing facts about the topic

Passage length by stimulus mode:

| Mode              | Word count |
| ----------------- | ---------- |
| `sentence_only`   | 20–40      |
| `passage_excerpt` | 80–150     |
| `prose_single`    | 100–200    |
| `prose_paired`    | 80–120 each |

---

## 7. Shared Distractor Engineering Rules

### 7.1 One named failure mode per distractor

Every distractor must fail for exactly one primary reason. Do not create
distractors that are wrong for multiple unrelated reasons; they are too easy
to eliminate.

### 7.2 One plausibility source per distractor

Every distractor must be tempting for a documented reason:

- vocabulary overlap with passage
- near-synonym appeal
- partial truth
- common-definition appeal
- register match
- formal-sounding surface correctness
- local detail match
- structural resemblance to correct answer

### 7.3 One student failure mode per distractor

Every distractor must include a `student_failure_mode_key` identifying the
psychological mechanism causing students to select it. See `mcq_realism_rules.md`
for the complete approved list.

### 7.4 No accidental second error

A distractor that contains two unrelated errors is easier to eliminate than
one with a single precise error. Do not introduce extra errors to make a
distractor feel "more wrong."

### 7.5 Distractors must survive first-pass elimination

Every wrong option must be plausible to a moderately skilled reader on
first encounter. If a student can reject an option instantly without applying
the target rule, the distractor is not functioning.

### 7.6 Three functioning distractors required

A distractor counts as functioning only if a reasonable but mistaken student
could select it for a specific articulable reason. Filler distractors fail
validation.

---

## 8. SAT Realism Layer

This section defines the targets that distinguish a realistic DSAT item from
a generic practice item.

### 8.1 Distractor distance

```json
{ "distractor_distance": "tight" }
```

- `wide`: wrong answers are clearly different from the correct answer
- `moderate`: wrong answers are somewhat close
- `tight`: wrong answers are closely competitive with the correct answer

`tight` is required for `difficulty_overall: high`. Preferred for `medium`.

### 8.2 Plausible wrong count

```json
{ "plausible_wrong_count": 3 }
```

Target: 3 for hard items. At least 2 for medium items.

### 8.3 Answer separation strength

```json
{ "answer_separation_strength": "low" }
```

- `high`: correct answer is clearly better than all others
- `medium`: correct answer is better, but one distractor competes
- `low`: multiple choices look competitive; only careful analysis resolves

Target: `low` for hard items.

### 8.4 All-Four-Plausible requirement

For `difficulty_overall: medium` or `high`:

- Every option — including all three wrong answers — must be plausible English
  when read in isolation
- No option may be eliminated by ear-test alone
- The correct answer must not "sound better" to a reader who has not applied
  the target rule

### 8.5 Difficulty comes from reasoning, not obscurity

Hard SAT items are hard because:

- the syntactic trap is deeply embedded (not superficially visible)
- multiple options seem equally good on first pass
- elimination requires precise rule application
- the passage uses formal academic register that makes all options "feel" right

Hard SAT items are NOT hard because:

- vocabulary is rare or obscure
- the topic is unfamiliar
- the question is confusingly worded
- the passage is ambiguous

### 8.6 Realism scoring expectations

Production target: `official_similarity_score` ≥ 0.82. Preferred ≥ 0.90.

Compared against released official College Board items from:
- PT1–PT11
- Bluebook
- Official practice tests

---

## 9. Anti-Clone and Diversity Controls

### 9.1 Structural similarity threshold

If a generated item has structural similarity > 0.75 to any item in the
anti-clone pool, regenerate the passage. Structural similarity counts
overlapping passage templates, same focus key + same trap key + same topic.

### 9.2 Topic rotation

In a batch:

- No two consecutive items share the same `topic_broad`
- No two items within a 5-item window share the same `topic_fine`

### 9.3 Exam ID avoidance

If `avoid_recent_exam_ids` is provided, generated passages must not closely
resemble items from those exams.

---

## 10. Provenance and Audit Trail

Every generated item must include:

```json
{
  "generation_provenance": {
    "source_template_used": "...",
    "generation_chain": ["passage_generated", "distractors_generated", "validator_run"],
    "model_version": "rules_agent_v3.0",
    "generation_timestamp": "..."
  }
}
```

Human override logs must be recorded when a reviewer changes a classification:

```json
{
  "human_override_log": {
    "original_classification": "...",
    "reviewer_change": "...",
    "reason": "..."
  }
}
```

---

## 11. Shared Validation Lifecycle

Validation runs in two phases:

1. **Core validation** (this file): output shape, shared distractor rules,
   realism thresholds, anti-clone checks
2. **Domain validation** (domain module): focus key mapping, trap coverage,
   domain-specific distractor heuristics

Maximum 3 retries per component. After 3 failures, return a structured error
response.

### Core validation checklist

- [ ] All required JSON sections present
- [ ] Exactly four options
- [ ] Exactly one `is_correct: true`
- [ ] Each distractor has `student_failure_mode_key`
- [ ] `distractor_distance` is present and calibrated
- [ ] `plausible_wrong_count` meets minimum for declared difficulty
- [ ] All options produce plausible English sentences
- [ ] No option eliminable by ear-test alone
- [ ] `explanation_full` addresses all three wrong options by label
- [ ] `passage_architecture_key` is a valid value
- [ ] `official_similarity_score` ≥ 0.82 (or explicitly flagged for review)
- [ ] `structural_similarity_score` < 0.75
- [ ] `empirical_difficulty_estimate` assigned
- [ ] `generation_provenance` complete

---

## 12. Amendment and Escalation Framework

### When to propose an amendment

- A grammar type is encountered that does not fit any existing focus key
- A trap mechanism is encountered that has no approved key
- A passage architecture is needed that has no approved template

### When to reject the request

- Requested focus key is not in the approved list
- Focus key maps to the wrong role key
- `very_low` frequency requested without justification

### When to require human review

- Two focus keys seem equally valid
- The passage supports multiple correct answers
- Classification confidence < 0.80

---

## 13. Cross-References

Grammar module exposes:

- `grammar_role_key` taxonomy
- `grammar_focus_key` taxonomy
- `syntactic_trap_key` taxonomy
- passage construction rules by focus key
- distractor heuristics by focus key
- no-change generation rules

Reading module exposes:

- `skill_family` taxonomy
- `reading_focus_key` taxonomy
- `answer_mechanism_key` taxonomy
- evidence location and scope rules
- paired-passage and quantitative passage rules

---

## Notes on Source Derivation

Primary inputs:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md` sections 14, 20–29
- `rules_agent_dsat_reading_v1.md` sections 16 and 20
- `mcq_realism_rules.md` (all sections)
- Khan Academy Digital SAT Standard English Conventions category structure
- College Board DSAT test specifications (Boundaries; Form, Structure, and Sense)
