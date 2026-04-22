# LLM Generation Workflow

**Purpose**: Document how the LLM uses `GROUND_TRUTH_GRAMMAR.md` during question generation, from constraint selection through drift detection and corpus conformance.

**Scope**: Generation Run Creation → Seed Selection → Prompt Building → LLM Generation → Pass 2 Annotation → Drift Detection → Corpus Conformance → Human Review

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       GENERATION PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User POST /generate                                                    │
│  - template_id (e.g., conventions_grammar_v1)                           │
│  - seed_question_ids (1-5 official CB questions)                        │
│  - target_constraints (target_grammar_focus_key, etc.)                  │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 1: SEED SELECTION                                          │   │
│  │ - Embed target constraints                                      │   │
│  │ - Query question_embeddings for closest match                   │   │
│  │ - Fallback to round-robin if no embeddings                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 2: PROMPT BUILDING                                         │   │
│  │ - Load GROUND_TRUTH_GRAMMAR.md rules for SEC constraints        │   │
│  │ - Build system prompt with Pass 1 schema                        │   │
│  │ - Build user prompt with seed exemplar + grouped constraints    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 3: LLM GENERATION (Pass 1)                                 │   │
│  │ - temperature=0.7 for creativity                                │   │
│  │ - Output: stem, passage, choices, correct_answer                │   │
│  │ - source_exam_code, source_module_code, source_question_number  │   │
│  │   MUST be null (generated, not official)                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 4: PASS 2 ANNOTATION                                       │   │
│  │ - Classify using GROUND_TRUTH_GRAMMAR.md                        │   │
│  │ - Select grammar_role_key + grammar_focus_key                   │   │
│  │ - Annotate difficulty, syntax, rhetoric, distractors            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 5: DRIFT DETECTION                                         │   │
│  │ - Compare Pass 2 classification vs. target constraints          │   │
│  │ - Compute DriftReport (critical_drifts, soft_drifts)            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 6: CORPUS CONFORMANCE                                      │   │
│  │ - Check against v_corpus_fingerprint                            │   │
│  │ - Compute ConformanceReport (critical_misses, soft_misses)      │   │
│  │ - Replaces subjective LLM realism judge                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 7: QUALITY GATE                                            │   │
│  │ - If conformant + no critical drift → stage for review          │   │
│  │ - If drift/critical fail + attempt < 3 → retry generation       │   │
│  │ - If attempt 3 fails → mark conformance_failed                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STEP 8: HUMAN REVIEW → APPROVAL                                 │   │
│  │ - PATCH /jobs/{id}/status (approved)                            │   │
│  │ - Rewrite content_origin: 'generated' → 'ai_human_revised'      │   │
│  │ - Trigger IRT refresh + corpus fingerprint refresh              │   │
│  │ - Generate coaching annotations                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Seed Selection

### Purpose
Select the best official CB question to use as a style/difficulty reference.

### Vector Similarity Selection

```python
# From app/pipeline/generate.py: select_seed_question()

# 1. Build text description of target constraints
description = " ".join([
    target_passage_source_type_key,
    target_prose_register_key,
    target_difficulty_overall,
    target_syntactic_complexity_key,
    target_lexical_tier_key,
])

# 2. Embed the description
target_embedding = await get_embedding(description)

# 3. Query question_embeddings (embedding_type='taxonomy_summary')
seed_id = await conn.fetchval("""
    SELECT question_id
    FROM public.question_embeddings
    WHERE embedding_type = 'taxonomy_summary'
      AND question_id = ANY($1::uuid[])
    ORDER BY embedding <=> $2::vector
    LIMIT 1
""", seed_question_ids, str(target_embedding))

# 4. Fallback to round-robin if no embeddings exist
```

### Why Vector Selection Matters

Vector similarity ensures the seed question matches the **semantic profile** of the target constraints, not just exact keyword matches. This is critical for:
- `target_prose_register_key` — academic vs. journalistic vs. literary
- `target_syntactic_complexity_key` — simple vs. compound-complex sentences
- `target_lexical_tier_key` — Tier 1 vs. Tier 3 vocabulary

### Fallback Behavior

If no embeddings exist for the candidate seeds, fall back to round-robin:
```python
return seed_question_ids[round_robin_index % len(seed_question_ids)]
```

---

## Step 2: Prompt Building

### System Prompt

```python
# From app/prompts/generation.py

SYSTEM_PROMPT = build_generation_system_prompt(template_skeleton)

# The template skeleton contains <<pass1_schema>> which is replaced with
# the Pass 1 output schema (stem, passage, choices, correct_answer, etc.)
```

**Key rules in system prompt**:
- `source_exam_code`, `source_module_code`, `source_question_number` MUST be null
- All passage text must be original — do NOT copy the seed exemplar
- Temperature=0.7 for creative generation

### User Prompt — Three Sections

#### Section 1: Seed Exemplar

```
=== SEED EXEMPLAR ===
Use as style and difficulty reference — do NOT copy.

Passage:
{seed_passage}

Question:
{seed_stem}

Choices:
  A) {choice_a}
  B) {choice_b}
  C) {choice_c}
  D) {choice_d}

Correct answer: {correct_label}
```

#### Section 2: Target Specifications (Grouped Constraints)

Constraints are rendered in **grouped sections** for better LLM processing:

```
=== TARGET SPECIFICATIONS ===

[PASSAGE STYLE]
  - Source type: {target_passage_source_type_key}
  - Register: {target_prose_register_key}
  - Tone: {target_prose_tone_key}

[SYNTACTIC STRUCTURE]
  - Sentence complexity: {target_syntactic_complexity_key}
  - Interruption pattern: {target_syntactic_interruption_key}
  - Syntactic trap to embed: {target_syntactic_trap_key}

[GRAMMAR (SEC)]
  - Grammar rule being tested: {target_grammar_focus_key}
  - Grammatical role: {target_grammar_role_key}

[ITEM MECHANICS]
  - Difficulty: {target_difficulty_overall}
  - Blank position: {target_blank_position_key}
  ...
```

**Grouping improves compliance** — the LLM processes categorized constraints more reliably than a flat list.

#### Section 3: Difficulty Anchor (Optional)

```
=== DIFFICULTY ANCHOR ===
Reference difficulty (IRT b): 0.42 — target a question of similar difficulty
unless target_difficulty_overall overrides this.
```

---

## Step 3: LLM Generation (Pass 1)

### API Call

```python
# From app/pipeline/generate.py: process_generation_run()

provider = get_provider(llm_provider, llm_model)
response = await provider.complete(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    temperature=0.7,  # Creative generation
    max_tokens=2048,
)
```

### Output Validation

The LLM must output valid JSON matching the Pass 1 schema:

```json
{
  "stem": "Which choice completes the text?",
  "passage": "The researcher studied the data...",
  "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_option_label": "B",
  "source_exam_code": null,
  "source_module_code": null,
  "source_question_number": null,
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text"
}
```

**Validation rules**:
- `source_*` fields MUST be null (generated, not official)
- `choices` must have exactly A, B, C, D keys
- `correct_option_label` must match one of the choices

### LLM API Error Handling

```python
# Retry logic for LLM API errors (timeout, rate limit, malformed JSON)
for attempt in range(3):
    try:
        response = await provider.complete(...)
        break
    except (TimeoutError, RateLimitError, json.JSONDecodeError):
        await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s

# If all 3 retries fail: mark job status='failed', break attempt loop
# These retries do NOT consume a drift-attempt slot
```

---

## Step 4: Pass 2 Annotation

### Purpose
Classify the generated question using the same taxonomy schema as official CB questions.

### Instructions for LLM

```python
# From app/prompts/pass2_annotation.py

SYSTEM_PROMPT = """
You are annotating a GENERATED Digital SAT question.

CLASSIFICATION RULES:

1. Use GROUND_TRUTH_GRAMMAR.md to classify SEC questions:
   
   a) Select grammar_role_key from 7 allowed values
   b) Select grammar_focus_key from 26 specific rules
   c) Apply disambiguation rules if multiple rules could apply

2. For SEC questions, the grammar_focus_key is CRITICAL:
   - This is the primary rule being tested
   - Must match the target_grammar_focus_key from generation constraints
   - If the question tests multiple rules, select the PRIMARY rule

3. If the question does NOT fit any existing grammar_focus_key:
   - Classify with the closest matching rule
   - Add an amendment_proposal to the reasoning section
   - Set annotation_confidence = "low"

OUTPUT SCHEMA:
{
  "classification": {
    "domain_key": "standard_english_conventions",
    "skill_family_key": "form_structure_sense" | "boundaries",
    "grammar_role_key": str,
    "grammar_focus_key": str,
    "difficulty_overall": "easy" | "medium" | "hard",
    ...
  },
  "options": [...],
  "reasoning": {
    "primary_solver_steps": [...],
    "annotation_confidence": "high" | "medium" | "low"
  }
}
"""
```

### Grammar Classification Decision Tree

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
                     │  rules (GROUND_TRUTH    │
                     │  GRAMMAR.md Part 4)     │
                     └───────────┬──────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │  Write classification   │
                     │  to question_classifi-  │
                     │  cations table          │
                     └─────────────────────────┘
```

---

## Step 5: Drift Detection

### Purpose
Compare the Pass 2 classification against the generation target constraints to detect if the LLM honored the spec.

### DriftReport Computation

```python
# From app/pipeline/drift.py

CRITICAL_DIMENSIONS = {
    "target_difficulty_overall":       "difficulty_overall",
    "target_syntactic_complexity_key": "syntactic_complexity_key",
    "target_prose_register_key":       "prose_register_key",
    "target_epistemic_stance_key":     "epistemic_stance_key",
    "target_rhetorical_structure_key": "rhetorical_structure_key",
}

SEC_CRITICAL_DIMENSIONS = {
    "target_grammar_focus_key":         "grammar_focus_key",
    "target_grammar_role_key":          "grammar_role_key",
}

def detect_drift(expected: dict, actual: dict) -> DriftReport:
    """
    expected: {classification_column: expected_value} from target constraints
    actual: {classification_column: actual_value} from Pass 2 annotation
    """
    critical_drifts = []
    soft_drifts = []
    
    for col, expected_val in expected.items():
        actual_val = actual.get(col)
        if actual_val is None:
            continue  # Skip if Pass 2 didn't classify this dimension
        if str(expected_val) != str(actual_val):
            if col in CRITICAL_DIMENSIONS.values():
                critical_drifts.append(col)
            else:
                soft_drifts.append(col)
    
    is_critical = len(critical_drifts) > 0
    
    return DriftReport(
        critical_drifts=critical_drifts,
        soft_drifts=soft_drifts,
        is_critical=is_critical,
        summary=". ".join([...]),
    )
```

### Critical vs. Soft Drift

| Type | Dimensions | Consequence |
|------|------------|-------------|
| **Critical** | `difficulty_overall`, `syntactic_complexity_key`, `prose_register_key`, `epistemic_stance_key`, `rhetorical_structure_key`, `grammar_focus_key` (SEC), `grammar_role_key` (SEC) | Triggers rerun (if attempts remain) |
| **Soft** | `lexical_tier_key`, `passage_source_type_key`, `narrator_perspective_key` | Logged but does NOT trigger rerun |

### SEC-Specific Critical Dimensions

For `conventions_grammar` family questions, the grammar dimensions are CRITICAL:
- `grammar_focus_key` — the specific rule being tested (e.g., `subject_verb_agreement`)
- `grammar_role_key` — the broad category (e.g., `agreement`)

A generated grammar question that drifts on `grammar_focus_key` has failed to test the intended rule — this is a fundamental failure.

---

## Step 6: Corpus Conformance

### Purpose
Replace the subjective LLM realism judge with an objective measurement against approved CB ground truth.

### How It Works

```python
# From app/pipeline/drift.py: corpus_conformance_score()

def corpus_conformance_score(
    annotation: dict,
    family_key: str,
    corpus_rows: list[dict],
    top_n: int = 3,
) -> ConformanceReport:
    """
    Check if annotated dimensions fall within top-N modal values
    for this question family in the approved CB corpus.
    """
    # 1. Determine critical dimensions for this family
    critical = list(CRITICAL_DIMENSIONS.values())
    if family_key == "conventions_grammar":
        critical += list(SEC_CRITICAL_DIMENSIONS.values())
    
    # 2. Filter corpus rows to this family
    family_rows = [r for r in corpus_rows if r["question_family_key"] == family_key]
    corpus_n = sum(r["n"] for r in family_rows)
    
    # 3. Bypass if corpus too small (<5 approved questions)
    if corpus_n < 5:
        return ConformanceReport(
            critical_misses=[],
            soft_misses=[],
            corpus_n=corpus_n,
            is_conformant=True,
            explanation=f"Corpus too small ({corpus_n}) — gate bypassed"
        )
    
    # 4. Compute top-N modal values for each dimension
    def top_n_values(dim: str) -> set:
        counts = {}
        for r in family_rows:
            v = r.get(dim)
            if v:
                counts[v] = counts.get(v, 0) + r["n"]
        return set(sorted(counts, key=counts.get, reverse=True)[:top_n])
    
    # 5. Check if annotated values are in top-N
    critical_misses = []
    for dim in critical:
        actual_val = annotation.get(dim)
        acceptable = top_n_values(dim)
        if acceptable and actual_val not in acceptable:
            critical_misses.append(dim)
    
    is_conformant = len(critical_misses) == 0
    
    return ConformanceReport(
        critical_misses=critical_misses,
        soft_misses=[],
        corpus_n=corpus_n,
        is_conformant=is_conformant,
        explanation=f"Conformant against {corpus_n} CB questions" if is_conformant
                    else f"Fails on: {', '.join(critical_misses)} (corpus n={corpus_n})"
    )
```

### Why This Replaces the LLM Realism Judge

| LLM Realism Judge | Corpus Conformance |
|-------------------|--------------------|
| Subjective (0.00-1.00 score) | Objective (in/out of corpus norms) |
| No calibration baseline | Grounded in approved CB questions |
| Uninterpretable ("0.82") | Explainable ("fails on grammar_focus_key") |
| Shared biases with generator | Independent ground truth |

### Bootstrap Behavior

When the corpus has fewer than 5 approved questions for a family:
- The conformance gate is **bypassed** (`is_conformant=True`)
- A warning is logged
- Drift detection still runs (target constraints must be honored)

This allows generation to function during early corpus building while becoming stricter as the corpus grows.

---

## Step 7: Quality Gate

### Decision Logic

```python
# From app/pipeline/generate.py: process_generation_run()

for attempt in range(1, 4):  # Max 3 drift attempts
    # 1. Generate (Pass 1)
    # 2. Annotate (Pass 2)
    # 3. Detect drift
    drift_report = detect_drift(target_constraints, pass2_classification)
    
    # 4. Check corpus conformance
    conformance_report = corpus_conformance_score(
        pass2_classification,
        family_key=question_family,
        corpus_rows=corpus_rows,
    )
    
    # 5. Write generation_result_jsonb (audit trail)
    await conn.execute("""
        UPDATE question_ingestion_jobs
        SET generation_result_jsonb = $1,
            status = CASE
                WHEN $2 OR NOT $3 THEN 'drift_failed'
                ELSE 'reviewed'
            END
        WHERE id = $4
    """, json.dumps({
        "attempt_number": attempt,
        "drift_report": asdict(drift_report),
        "conformance_report": asdict(conformance_report),
        "model_name": llm_model,
        "provider": llm_provider,
        "seed_question_id": str(seed_id),
        "target_constraints_snapshot": target_constraints,
    }), drift_report.is_critical, conformance_report.is_conformant, job_id)
    
    # 6. Decide: rerun or stage?
    if should_rerun(drift_report, conformance_report, attempt):
        # Create new job for next attempt
        continue
    elif not conformance_report.is_conformant and attempt == 3:
        # Terminal failure on attempt 3
        await conn.execute(
            "UPDATE question_ingestion_jobs SET status = 'conformance_failed' WHERE id = $1",
            job_id,
        )
        break
    else:
        # Success — stage for human review
        break
```

### Attempt Accounting

| Outcome | Status | Next Action |
|---------|--------|-------------|
| Conformant + no critical drift (attempt 1-3) | `reviewed` | Stage for human review |
| Critical drift or conformance fail (attempt 1-2) | `drift_failed` | Retry generation |
| Critical drift or conformance fail (attempt 3) | `conformance_failed` | Log failure, move to next item |
| LLM API error (all retries exhausted) | `failed` | Log error, move to next item |

**Drift-failed attempts are NEVER hard-deleted.** They are preserved in `question_ingestion_jobs` with `status='drift_failed'` for prompt calibration and audit.

---

## Step 8: Human Review → Approval

### Review Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /generate/runs/{run_id}/jobs` | View all staging jobs (including `drift_failed` attempts) |
| `GET /generate/runs/{run_id}/drift` | View drift + conformance reports for the run |
| `PATCH /jobs/{id}/status` | Approve or reject individual jobs |

### Approval Hook

When a generated job is approved:

```python
# From app/routers/jobs.py: PATCH /jobs/{id}/status

if job["content_origin"] == "generated" and new_status == "approved":
    # 1. Rewrite content_origin before upsert
    # 'generated' → 'ai_human_revised' (migration 036 constraint)
    job["content_origin"] = "ai_human_revised"
    job["source_type"] = "generated"  # Override pass1_json.source_type if needed
    
    # 2. Upsert to production tables (questions, question_classifications, etc.)
    await upsert_question(conn, job)
    
    # 3. Trigger IRT refresh (background)
    await conn.execute("SELECT public.fn_refresh_irt_b($1::uuid)", question_id)
    
    # 4. Trigger corpus fingerprint refresh (background)
    await conn.execute("SELECT public.fn_refresh_corpus_fingerprint()")
    
    # 5. Trigger coaching generation (background)
    background_tasks.add_task(generate_coaching_for_question, pool, settings, question_id)
```

### Content Origin Transition

```
┌─────────────────────────────────────────────────────────────┐
│  content_origin lifecycle for generated questions           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Generation time:                                           │
│    question_ingestion_jobs.content_origin = 'generated'     │
│                                                             │
│  Approval time:                                             │
│    questions.content_origin = 'ai_human_revised'            │
│    (NOT 'generated' — migration 036 disallows 'generated')  │
│                                                             │
│  Production:                                                │
│    generated_questions.content_origin = 'ai_human_revised'  │
│    questions.content_origin = 'ai_human_revised'            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Ground Truth Integration

### How GROUND_TRUTH_GRAMMAR.md Is Used

| Step | Usage |
|------|-------|
| **Prompt Building** | SEC constraint groups reference grammar_focus_key values from Part 3 |
| **Pass 2 Annotation** | LLM selects grammar_role_key + grammar_focus_key using disambiguation rules from Part 4 |
| **Drift Detection** | `grammar_focus_key` and `grammar_role_key` are CRITICAL for SEC questions |
| **Corpus Conformance** | `v_corpus_fingerprint` includes `grammar_focus_key` and `grammar_role_key` columns |
| **Amendment Proposal** | If no rule fits, LLM proposes amendment via `grammar_amendment.md` format |

### Amendment Proposals During Generation

When the LLM encounters a generated question that doesn't fit existing rules:

```json
{
  "reasoning": {
    "amendment_proposal": {
      "proposal_type": "new_grammar_focus_key",
      "priority": "medium",
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
      "rationale": "Generated question tests matched-pair rule not explicitly covered."
    },
    "annotation_confidence": "low"
  }
}
```

---

## Metrics

Track these metrics to monitor generation quality:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Pass rate (first attempt) | >60% | <40% |
| Pass rate (by attempt 3) | >90% | <80% |
| Critical drift rate | <15% | >25% |
| Conformance fail rate | <10% | >20% |
| Amendment proposal rate | <5% | >10% |
| Corpus bypass rate (corpus_n < 5) | <20% | >50% |

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `LLM timeout` | API latency or overload | Retry with exponential backoff (1s, 2s, 4s) |
| `Malformed JSON` | LLM output invalid JSON | Retry LLM call; if all 3 fail, mark `status='failed'` |
| `Critical drift on grammar_focus_key` | Generated question tests wrong rule | Rerun generation (if attempt < 3) |
| `Conformance fail: grammar_focus_key` | Annotated value not in corpus top-N | Rerun generation; check if target constraint is realistic |
| `Corpus too small` | <5 approved questions for family | Log warning; bypass conformance gate; drift still enforced |

### Rerun Strategy

```python
# From app/pipeline/drift.py: should_rerun()

def should_rerun(report: DriftReport, conformance: ConformanceReport, attempt: int) -> bool:
    """
    Returns True if critical drift or conformance failure, and attempts remain.
    """
    has_critical_issue = report.is_critical or not conformance.is_conformant
    return has_critical_issue and attempt < 3
```

---

## Testing the Pipeline

### Test Cases

```python
# From tests/test_generation.py

class TestCorpusConformance:
    def test_conformant_case_passes(self):
        # Annotation matches corpus top-N values
        report = corpus_conformance_score(annotation, "words_in_context", corpus_rows)
        assert report.is_conformant == True
        assert report.critical_misses == []
    
    def test_critical_miss_triggers_rerun(self):
        # Annotation value not in corpus top-N
        report = corpus_conformance_score(annotation, "words_in_context", corpus_rows)
        assert report.is_conformant == False
        assert "grammar_focus_key" in report.critical_misses
    
    def test_sec_grammar_dimensions_critical(self):
        # conventions_grammar family: grammar_focus_key is critical
        report = corpus_conformance_score(annotation, "conventions_grammar", corpus_rows)
        assert "grammar_focus_key" in report.critical_misses
    
    def test_small_corpus_bypasses_gate(self):
        # corpus_n < 5: bypass conformance
        report = corpus_conformance_score(annotation, "words_in_context", corpus_rows, top_n=3)
        assert report.is_conformant == True
        assert "Corpus too small" in report.explanation

class TestDriftDetection:
    def test_critical_drift_detected(self):
        # Target: difficulty=medium, Actual: difficulty=hard
        report = detect_drift(expected, actual)
        assert report.is_critical == True
        assert "difficulty_overall" in report.critical_drifts
    
    def test_sec_grammar_drift_critical(self):
        # Target: grammar_focus_key=subject_verb_agreement, Actual: parallel_structure
        report = detect_drift(expected, actual)
        assert report.is_critical == True
        assert "grammar_focus_key" in report.critical_drifts
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-18 | Initial workflow documentation |

---

*This document should be updated when `GROUND_TRUTH_GRAMMAR.md`, `app/prompts/generation.py`, or `app/pipeline/drift.py` change.*
