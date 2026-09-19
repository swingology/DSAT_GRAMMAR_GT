# Annotation Workflow Improvements

## Short Answer

The annotation workflow is not tight enough yet for "ground truth" grammatical and stylistic analysis.

The prompt/rules approach is directionally right, but the current system still depends too much on the LLM obeying instructions and too little on deterministic canonicalization, validation, and audit gates. The live database already shows this: among 93 active questions with latest annotations, 21 are missing top-level `question_family_key`, 21 are missing top-level `difficulty_overall`, 22 grammar-family rows are missing top-level `syntactic_trap_key`, 1 grammar-family row is missing `grammar_role_key`/`grammar_focus_key`, and 2 reading-family rows are missing `reading_focus_key`.

A representative row from the June 26 v8 run has valid nested values under `classification.question_family_key`, `classification.difficulty_overall`, and `classification.syntactic_trap_key`, but those values did not reach the top-level fields consumed by the student API and generation source-selection logic. That means some "NULL errors" are not analysis failures; they are shape/canonicalization failures.

## What Is Working

- `backend/app/prompts/annotate_prompt.py` now routes to grammar v8 or reading v3 rule context instead of loading everything for every question.
- The allowed-key block gives the model exact ontology keys from `backend/app/models/ontology.py`.
- `_detect_domain()` has explicit grammar/reading/ambiguous routing instead of relying only on the model.
- `enforce_nullability()` prevents reading annotations from leaking grammar keys and clears reading difficulty on grammar annotations.
- `annotation_sanitizer.py` catches invalid controlled-vocabulary values and records candidates for later vocabulary review.
- Ingestion artifacts now include hashes for rules, ontology, and `master.json`, which is important for later calibration.

## Main Failure Modes

### 1. Nested-vs-flat annotation shape is leaking NULLs

The rules files ask for a structured object:

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

But the runtime API mostly reads flat top-level keys from `annotation_jsonb`, for example:

- `grammar_role_key`
- `grammar_focus_key`
- `syntactic_trap_key`
- `skill_family_key`
- `reading_focus_key`
- `difficulty_overall`
- `question_family_key`

The current `normalize_annotation()` only partially flattens nested fields. It should be treated as a critical canonicalization step, not a convenience repair. It should recursively copy canonical fields out of `question`, `classification`, `review`, `reasoning`, and `generation_profile` before validation and persistence.

Important rule: a nested non-empty canonical value should fill a missing, `null`, empty-string, or `"none"` top-level value when that top-level value is not a valid domain value.

### 2. Prompt instructions and generated vocabulary disagree

`annotate_prompt.py` tells the model to use:

- `very_high` difficulty

But `DIFFICULTY_KEYS` in `backend/app/models/ontology.py` only allows:

- `low`
- `medium`
- `high`

The generated vocab blocks in both rule docs also list only `low`, `medium`, and `high`. Remove `very_high` from the annotation prompt or add it to `vocabulary/master.json` and regenerate ontology/docs. Do not leave this split.

There is also a domain nullability contradiction:

- `annotate_prompt.py` says `difficulty_grammar` must be `null` for reading-domain questions.
- `rules_agent_dsat_reading_v3.md` includes reading examples with `difficulty_grammar: "low"`.
- `annotate_prompt.py` says `difficulty_reading` must be `null` for grammar-domain questions.
- `rules_agent_dsat_grammar_ingestion_generation_v8.md` includes grammar examples with `difficulty_reading: "low"`.

Pick one semantic model:

- Either cross-domain difficulty fields are always `null` when not applicable.
- Or they are calibrated secondary-load dimensions.

For ground truth and practice selection, the cleaner choice is: keep `difficulty_overall`, keep the relevant domain difficulty, and use `null` only for not-applicable domain difficulty.

### 3. Grammar `skill_family_key` is conceptually confused

The latest amendment candidate tried to add grammar values such as `verb_form` to `skill_family_key`. That is a symptom of unclear schema language.

Right now `skill_family_key` is reading-only in the ontology. Grammar should use:

- `question_family_key`
- `grammar_role_key`
- `grammar_focus_key`
- `syntactic_trap_key`

If a human-readable grammar `skill_family` label is useful, keep it as display text only. Do not let grammar questions propose new `skill_family_key` values unless the ontology intentionally adds a separate grammar skill-family key.

### 4. Sanitizer silently converts invalid analysis into NULL

`annotation_sanitizer.py` currently nulls invalid controlled-vocabulary keys when no near match exists. That is acceptable for a recovery queue, but not for ground truth.

For official questions, a no-match sanitizer event should set:

- `needs_human_review: true`
- `_annotation_quality.invalid_fields`
- `_annotation_quality.missing_required_fields`

It should also create a blocking or review validation record before the row is considered usable for practice/generation. Silent nulling is how bad labels become invisible data debt.

### 5. Validation is not domain-complete

`validate_question()` checks reading-domain requiredness when `question_family_key` is reading, but it does not fully validate grammar-domain completeness. It also cannot catch fields that are only present inside nested `classification`.

Add a separate `validate_annotation_completeness(annotation)` gate after canonicalization and sanitizer:

For grammar / Expression of Ideas:

- require `question_family_key`
- require `grammar_role_key`
- require `grammar_focus_key`
- require valid role/focus pairing
- require `syntactic_trap_key` with `"none"` allowed
- require `difficulty_overall`
- require `skill_family_key` to be null/omitted unless the ontology explicitly changes

For reading:

- require `question_family_key`
- require `skill_family_key`
- require `reading_focus_key`
- require valid skill/focus pairing
- require `difficulty_overall`
- require `grammar_role_key` and `grammar_focus_key` to be null/omitted
- strongly prefer non-null `reasoning_trap_key`

Use this gate in all paths:

- normal official ingest
- reannotation
- generation annotation
- any bulk reannotation script

### 6. Generated-question annotation path is weaker than ingest

`backend/app/routers/generate.py` normalizes generated annotations but does not currently apply the same `enforce_nullability()` and sanitizer path used by ingestion. Generated questions should use the exact same canonicalize -> enforce nullability -> sanitize -> validate completeness pipeline as official questions.

Otherwise generated practice data can drift from official-ground-truth data even when both claim to use the same rules version.

### 7. Domain routing should be verified, not merely inferred

`_detect_domain()` routes before annotation using the extracted `stem_type_key` and question text. That is useful, but Pass 1 stem labels can be wrong or too generic, especially around `complete_the_text`.

Recommended behavior:

1. Route with `_detect_domain()` before annotation.
2. Annotate.
3. Infer domain from the canonical annotation.
4. If inferred domain conflicts with routed domain, re-annotate once with the other rule context or mark for review.

Do not rely on post-hoc nullability cleanup alone; it can hide a wrong rules context.

### 8. Pass 2 and Pass 3 should stay separate

Grammar v8 still asks Pass 2 to emit `passage_tokens`, but the code now has a dedicated Pass 3 span annotator that writes `passage_spans`.

For a stable ground-truth workflow:

- Pass 2 should own item-level taxonomy and option-level reasoning.
- Pass 3 should own token/span/anatomy annotation.
- If Pass 2 emits `classification.passage_tokens`, canonicalize it to top-level `passage_tokens` only as a fallback for older UI behavior.
- Do not make Pass 2 tokenization a hard requirement if Pass 3 is the authoritative word-level analysis.

## Concrete Implementation Plan

### Step 1: Add a canonical annotation normalizer

Create a dedicated function, for example:

```python
canonicalize_annotation(raw: dict) -> dict
```

It should:

- preserve the original nested sections
- promote canonical fields from nested sections to top-level
- overwrite missing/null/empty top-level values with nested valid values
- copy `classification.passage_tokens` to top-level `passage_tokens`
- normalize aliases such as `reading_skill_family_key` -> `skill_family_key`
- normalize review fields from `review.annotation_confidence` and `review.needs_human_review`
- attach `_annotation_quality` metadata for any repair or conflict

Then replace direct calls to `normalize_annotation()` with:

```python
annotate_json = canonicalize_annotation(normalize_annotation(parsed))
annotate_json = enforce_nullability(annotate_json, _detect_domain(q_data))
annotate_json = sanitize_annotation_keys(annotate_json, job_id=str(job.id))
errors = validate_annotation_completeness(annotate_json)
```

### Step 2: Make completeness validation blocking for active data

Official questions with missing canonical fields should not become `active` practice data. Either:

- persist them as draft/needs-review, or
- persist the raw annotation but block `latest_annotation_id` promotion until fixed.

This is stricter, but it matches the goal: ground truth should be reliable enough to drive practice and generation.

### Step 3: Align prompt and rules

Patch the following:

- remove `very_high` from `annotate_prompt.py` difficulty calibration unless vocabulary changes
- update reading examples so reading-domain `difficulty_grammar` is `null`, or explicitly define it as a secondary-load field
- update grammar examples so grammar-domain `difficulty_reading` is `null`, or explicitly define it as a secondary-load field
- state clearly that grammar annotations must not populate `skill_family_key`
- update `generate_prompt.py` to use canonical `skill_family_key`, not `reading_skill_family_key`, unless an alias layer intentionally supports both

### Step 4: Add regression tests around the actual failure

Add tests with a fixture shaped like the live failing row:

- `classification.question_family_key` exists, top-level `question_family_key` missing
- `classification.difficulty_overall` exists, top-level `difficulty_overall` missing
- `classification.syntactic_trap_key` exists, top-level `syntactic_trap_key` missing

Expected result:

- canonical top-level fields are populated
- student API payload exposes them
- generation source selection can sort/filter by them

Also add tests for:

- grammar annotation with missing `grammar_focus_key` fails completeness validation
- grammar annotation with missing `syntactic_trap_key` gets `"none"` only if allowed by role/focus policy, otherwise review/block
- reading annotation with non-null grammar keys fails validation
- invalid sanitizer no-match sets review metadata rather than silently producing usable null fields
- prompt text does not mention difficulty values absent from `DIFFICULTY_KEYS`

### Step 5: Add an annotation quality audit

Add a script or extend `scripts/quality_audit.py` to fail when active questions have missing canonical fields.

Minimum audit query:

```sql
SELECT
  COUNT(*) FILTER (WHERE annotation_jsonb->>'question_family_key' IS NULL) AS missing_question_family,
  COUNT(*) FILTER (WHERE annotation_jsonb->>'difficulty_overall' IS NULL) AS missing_difficulty,
  COUNT(*) FILTER (
    WHERE annotation_jsonb->>'question_family_key' IN ('conventions_grammar', 'expression_of_ideas')
      AND annotation_jsonb->>'syntactic_trap_key' IS NULL
  ) AS grammar_missing_trap,
  COUNT(*) FILTER (
    WHERE annotation_jsonb->>'question_family_key' IN ('information_and_ideas', 'craft_and_structure')
      AND annotation_jsonb->>'reading_focus_key' IS NULL
  ) AS reading_missing_focus
FROM questions q
JOIN question_annotations qa ON qa.id = q.latest_annotation_id
WHERE q.practice_status = 'active';
```

This should run after ingest/reannotation and before generated-question release.

### Step 6: Reannotate or repair existing active rows

After the canonicalizer and validator are in place:

1. Run a repair pass that canonicalizes existing `annotation_jsonb` rows from nested values.
2. Re-run completeness audit.
3. Reannotate only rows still missing required values.
4. Run Pass 3 span annotation for grammar rows without `passage_spans`.

Do not use the old `scripts/reannotate_official_v7.py` as-is. It is still named and stamped for v7 and should be updated for v8/current prompt hashes before it is used for calibration data.

## Priority Order

1. Canonicalize nested annotation shape into flat top-level fields.
2. Add domain-aware completeness validation before active persistence.
3. Align prompt/rules vocabulary contradictions.
4. Apply the same annotation pipeline to generated questions.
5. Add a live annotation quality audit.
6. Repair/reannotate existing active rows.
7. Keep Pass 2 item taxonomy separate from Pass 3 span/token annotation.

## Bottom Line

The current workflow is close enough to expose useful official-question analysis, but not tight enough to call the output ground truth. The biggest fix is not another prompt paragraph; it is a deterministic canonicalization and validation layer that makes the LLM's nested reasoning shape match the flat schema consumed by practice and generation.
