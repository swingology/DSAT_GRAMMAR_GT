# Annotation Pipeline Refactor — Task Sheet

Derived from `annotations_improvements.md` review (2026-06-26). Goal: replace LLM-obedience
dependence with a deterministic canonicalize → enforce-nullability → sanitize → validate-completeness
pipeline so nested LLM reasoning shape always matches the flat schema consumed by practice/generation.

Status legend: `[ ]` todo · `[x]` done · `[~]` partial/deferred

---

## Phase 1 — Deterministic canonicalization (highest leverage)

- [x] **T1.1** Add `canonicalize_annotation(raw: dict) -> dict` in `backend/app/parsers/json_parser.py`
  - [x] Promote canonical fields from nested `question`, `classification`, `review`, `reasoning`, `generation_profile` to top level
  - [x] Fill a top-level value that is **missing, null, empty-string, or `"none"`** (when `"none"` is not a valid domain value for that field) from a valid nested value
  - [x] **Conflict policy (multi-LLM safety):** when top-level AND nested are both non-null and *different*, keep top-level, record `_annotation_quality.conflicts[]`, set `needs_human_review = true`. Never silently pick a winner.
  - [x] Normalize alias `reading_skill_family_key` → `skill_family_key`
  - [x] Normalize `skill_family` display name → `skill_family_key` (reuse `_SKILL_FAMILY_DISPLAY_TO_KEY`)
  - [x] Copy `classification.passage_tokens` → top-level `passage_tokens` as a **soft fallback only** (Pass 3 is authoritative)
  - [x] Lift `review.annotation_confidence` / `review.needs_human_review` to top level
  - [x] Attach `_annotation_quality` metadata (`promoted_fields`, `conflicts`, `repaired_from_nested`)
- [x] **T1.2** Make it a single canonicalization step (do NOT double-promote by wrapping `normalize_annotation`); fold promotion logic so there is one source of truth
- [x] **T1.3** Replace `normalize_annotation(...)` call in ingest annotate path (`ingest.py:2095`) with `canonicalize_annotation(...)`

## Phase 2 — Domain-complete validation gate

- [x] **T2.1** Add `SYNTACTIC_TRAP_REQUIRED_ROLES` constant to `ontology.py` (`agreement, pronoun, modifier, verb_form, sentence_boundary`) — single source shared with the prompt
- [x] **T2.2** Add `validate_annotation_completeness(annotation) -> List[Dict]` in `backend/app/pipeline/validator.py`
  - [x] Grammar (`conventions_grammar`, `expression_of_ideas`): require `question_family_key`, `grammar_role_key`, `grammar_focus_key`, valid role/focus pairing, `difficulty_overall`; require `syntactic_trap_key` (`"none"` allowed only when role NOT in `SYNTACTIC_TRAP_REQUIRED_ROLES`); `skill_family_key` must be null/omitted
  - [x] Reading (`craft_and_structure`, `information_and_ideas`): require `question_family_key`, `skill_family_key`, `reading_focus_key`, valid skill/focus pairing, `difficulty_overall`; `grammar_role_key`/`grammar_focus_key` must be null; strongly prefer non-null `reasoning_trap_key` (review severity)
- [x] **T2.3** Wire completeness gate into ingest pipeline after sanitize, before persistence

## Phase 3 — Apply identical pipeline to generated questions

- [x] **T3.1** Route `generate.py` annotation through `canonicalize_annotation → enforce_nullability → sanitize_annotation_keys → validate_annotation_completeness` (currently only calls `normalize_annotation`)

## Phase 4 — Fix prompt/rules/ontology vocabulary contradictions

> CORRECTION (verified against master.json + ontology.py): `DIFFICULTY_KEYS` = `low, medium, high`
> in master.json, ontology, AND both rules-doc generated blocks. The prompt is the lone outlier
> adding `very_high`. The doc's original remedy was right: REMOVE `very_high` from the prompt.

- [x] **T4.1** Remove invalid `very_high` from the prompt difficulty calibration (both template blocks); fold its description into `high`. `very_high` is not in `DIFFICULTY_KEYS`.
- [x] **T4.2** Cross-domain difficulty: adopt "null for not-applicable". Edit primary reading example (`reading_v3` `difficulty_grammar`) and grammar example (`grammar_v8` `difficulty_reading`) to `null` so examples match `enforce_nullability` runtime behavior
- [x] **T4.3** State explicitly in prompt that grammar annotations must NOT populate `skill_family_key`

## Phase 5 — Repair existing active rows (deterministic, cheap)

- [x] **T5.1** Repair script `backend/scripts/repair_annotation_canonical.py`: runs `canonicalize_annotation → enforce_nullability` over existing `annotation_jsonb` for active rows, writes back promoted top-level fields (no LLM calls). Also fixed `_infer_domain_from_annotation` to match canonical snake_case keys + `question_family_key` (was only matching display-name substrings).
- [x] **T5.2** Ran repair: 30 rows changed, 0 conflicts. `missing_question_family` 21→0, `missing_difficulty` 21→2, `reading_with_grammar_difficulty` 0. Remaining gaps (2 difficulty, 2 reading_focus, grammar trap debt) are genuinely-missing → need re-annotation, not repair.

## Phase 6 — Tests + live audit

- [x] **T6.1** Regression tests in `tests/test_parsers.py` shaped like live failing rows (nested-only `question_family_key`, `difficulty_overall`, `syntactic_trap_key` → promoted to top level)
- [x] **T6.2** Conflict-policy test: top-level + nested disagree → top-level kept, `needs_human_review`, conflict recorded
- [x] **T6.3** Completeness tests: grammar missing `grammar_focus_key` fails; reading with non-null grammar keys fails; grammar `agreement` with null `syntactic_trap_key` fails
- [x] **T6.4** Extend/add annotation quality audit (SQL: missing question_family / difficulty / grammar-missing-trap / reading-missing-focus on active rows)

## Phase 7 — Wrap-up

- [x] **T7.1** All tests green (refactor scope: test_parsers.py + test_validator_completeness.py = 40 passed, 2 skipped; unrelated pre-existing failures in student_retrieval/config/vocab_sync/ingest_router noted in CHANGELOG)
- [x] **T7.2** Copy finished task list to `CHANGELOG.md`
- [x] **T7.3** DEBUG_LOG.md entry

---

### Deferred (out of scope this pass, noted for follow-up)

- Route-vs-inferred domain re-annotation loop (review item #7) — needs an extra LLM round-trip; design separately so it doesn't amplify 429 pressure.
- Pass 2 / Pass 3 token ownership split (review item #8) — `passage_tokens` handled as soft fallback only here.
