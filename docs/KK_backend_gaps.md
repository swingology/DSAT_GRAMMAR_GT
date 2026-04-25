# DSAT Grammar Backend — Gap Audit Report

Generated: 2026-04-24

---

## app/main.py — Router Registration

**Status:** All 6 imported routers are implemented and registered. No gaps here.

---

## app/routers/*.py — Stubbed vs Implemented

| File | Status | Gaps |
|------|--------|------|
| `health.py` | Complete | Minimal but functional |
| `questions.py` | **Critical bug** | Python-side filtering breaks pagination; wrong field mapped to `stimulus_mode_key` |
| `student.py` | **Critical bug** | Same Python-side filtering breaks pagination |
| `admin.py` | **Data integrity gaps** | Hardcodes `choices_jsonb=[]`; never updates `latest_version_id` |
| `ingest.py` | **Critical pipeline gap** | Background task never creates `Question`/`QuestionOption`/`QuestionAnnotation`/`QuestionVersion` rows |
| `generate.py` | **Critical pipeline gap** | Creates `Question` row but never creates related `QuestionVersion`/`QuestionAnnotation`/`QuestionOption` rows |

---

## app/models/*.py — Schema / DB Alignment

| File | Status | Gaps |
|------|--------|------|
| `db.py` | Complete | 10 ORM tables defined, relationships configured |
| `ontology.py` | Complete | V3 vocabularies fully enumerated |
| `extract.py` | Complete | Pass 1 Pydantic schema with validators |
| `annotation.py` | Complete | Pass 2 Pydantic schema with validators |
| `options.py` | Complete | Per-option Pydantic schema with validators |
| `payload.py` | **Medium gaps** | Missing schemas for `QuestionAsset`, `QuestionRelation`, `User`, `LlmEvaluation` creation |

---

## app/pipeline/*.py

| File | Severity | Gap |
|------|----------|-----|
| `orchestrator.py` | Medium | State machine exists but is not used by routers to drive pipeline steps; no retry execution logic |
| `validator.py` | **Critical** | Extremely minimal: does not validate V3 ontology keys (`grammar_focus_key`, `stimulus_mode_key`, `stem_type_key`), option-level schema, explanation length limits, or that exactly one option is correct |
| *(missing)* | **Critical** | No overlap detection implementation despite `overlap_check` job type and `question_relations` table |

---

## app/parsers/*.py

| File | Status | Gaps |
|------|--------|------|
| `pdf_parser.py` | Complete | Text + image extraction implemented |
| `json_parser.py` | Complete | Robust fence/brace extraction |
| `image_parser.py` | Complete | Base64 encoding |
| `markdown_parser.py` | Complete | Front-matter extraction |
| *(missing)* | Low | No dedicated plain-text parser (handled inline in ingest router) |

---

## app/llm/*.py

| File | Status | Gaps |
|------|--------|------|
| `base.py` | Complete | Protocol + dataclass defined |
| `factory.py` | Complete | 3-provider dispatcher |
| `anthropic_provider.py` | Complete | Functional |
| `openai_provider.py` | Complete | Functional |
| `ollama_provider.py` | Complete | Functional |
| *(all providers)* | Medium | No retry logic, no rate-limit handling, no timeout recovery, no circuit breaker |

---

## app/storage/*.py

| File | Severity | Gap |
|------|----------|-----|
| `local_store.py` | Medium | Only local backend implemented despite `RAW_ASSET_STORAGE_BACKEND` config; no filename collision handling; no deduplication by checksum |

---

## Tests — Coverage Gaps

**Existing tests:** 15 test files covering auth, config, health, models, ontology, parsers, pipeline, prompts, schemas, and all routers.

| Missing / Deficient | Severity | Gap |
|---------------------|----------|-----|
| `test_storage.py` | Low | No storage tests |
| `test_database.py` | Low | No DB connection / session tests |
| Router happy-path tests | **Critical** | All router tests use a mock DB that returns `None`; no tests verify successful creation, recall with data, or pipeline completion |
| `test_generate_router.py` | Medium | Accepts HTTP 500 as pass (`assert resp.status_code in (200, 500)`) |
| Pipeline E2E tests | Medium | No integration test for full ingest -> question creation flow |
| Overlap detection tests | Medium | None exist |

---

## app/prompts/*.py

| File | Severity | Gap |
|------|----------|-----|
| `extract_prompt.py` | Medium | Does not provide allowed `stimulus_mode_key` / `stem_type_key` values to LLM; no V3 rules context |
| `annotate_prompt.py` | Low | Hard-truncates rules file to 8000 chars with no smart chunking or RAG fallback |
| `generate_prompt.py` | Medium | Same as extract: no allowed-value reference provided to LLM |

---

## TODOs, FIXMEs, Placeholders & Critical Code Gaps

### Critical Severity

1. **`backend/app/routers/ingest.py`** — `_run_pipeline` never persists extracted data into `questions`, `question_options`, `question_annotations`, or `question_versions`. After a job reaches `approved`, there is no corresponding question row. The manual test script does this manually, but the production router does not.

2. **`backend/app/routers/generate.py`** — `_run_generate_pipeline` creates a `Question` row but never creates `QuestionVersion`, `QuestionAnnotation`, or `QuestionOption` rows, leaving the question orphaned without options or metadata.

3. **`backend/app/routers/questions.py` & `app/routers/student.py`** — Both `recall` endpoints apply `grammar_focus`, `difficulty`, and `origin` filters in Python after fetching a fixed SQL limit. This breaks pagination: requesting `limit=20` may return 0 items if all 20 are filtered out.

4. **`backend/app/main.py`** — CORS configured with `allow_origins=["*"]` and `allow_credentials=True`. Browsers reject this combination; it is a security misconfiguration.

5. **`backend/migrations/versions/001_initial_schema.py`** — `downgrade()` references `enums` which is defined inside `upgrade()`. Running `alembic downgrade` will raise `NameError: name 'enums' is not defined`.

### Medium Severity

6. **`backend/app/routers/ingest.py`** — `_run_pipeline` ignores the job's `provider_name` and always uses `settings.default_annotation_provider`.

7. **`backend/app/routers/ingest.py`** — `reannotate` jobs run the full pipeline including Pass 1 extraction again. It should skip extraction and go straight to annotation.

8. **`backend/app/routers/admin.py`** — `edit_question` hardcodes `choices_jsonb=[]` in the new `QuestionVersion` instead of serializing the question's actual options. It also never updates `Question.latest_version_id`.

9. **`backend/app/routers/questions.py`** — Line 58 maps `stimulus_mode_key=q.stem_type_key` instead of `q.stimulus_mode_key`.

10. **`backend/app/pipeline/validator.py`** — Missing all V3 ontology validation, option schema validation, overlap logic, and deduplication checks.

11. **`backend/app/models/db.py`** — `latest_annotation_id` and `latest_version_id` on `Question` are never updated by any router or pipeline step.

12. **`backend/app/routers/ingest.py`** — `QuestionAsset.question_id` is never populated during ingestion.

13. **Missing router** — No endpoints exist for `QuestionRelation` CRUD or overlap detection despite the table and enums existing.

14. **Missing router** — No endpoint to create `LlmEvaluation` rows (only scoring existing ones via `/admin/evaluations/{id}/score`).

15. **Missing router** — No `User` creation or management endpoints.

16. **`backend/app/database.py`** — No `pool_pre_ping=True`; stale connections possible in production.

### Low Severity

17. **All `__init__.py` files** — Empty; no convenience exports.

18. **`backend/app/prompts/annotate_prompt.py`** — Rules context truncated to 8000 chars with no semantic chunking.

19. **`backend/app/models/payload.py`** — `IngestPdfRequest` Pydantic model is defined but never used (routers use `Form` parameters directly).

20. **`backend/scripts/manual_test.py`** — Duplicates pipeline logic instead of reusing `app.routers.ingest._run_pipeline`.

21. **No logging / tracing** — No structured logging, request IDs, or correlation context configured.

22. **`backend/app/config.py`** — `max_file_size` and `allowed_mime_types` are hardcoded in `ingest.py` instead of being configurable.

---

## Summary by Severity

| Severity | Count | Top Issues |
|----------|-------|------------|
| Critical | 5 | Ingest pipeline never creates question rows; generate pipeline incomplete; broken pagination; CORS security bug; broken Alembic downgrade |
| Medium | 10 | Wrong provider used in pipeline; reannotate re-runs extract; admin edit loses option data; wrong field mapping; missing overlap/relation/eval APIs; stale connection pool |
| Low | 6 | Empty `__init__.py` files; unused Pydantic models; prompt truncation; hardcoded config values; no storage backend abstraction |
