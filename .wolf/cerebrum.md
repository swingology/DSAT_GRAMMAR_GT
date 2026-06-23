# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-05-15

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **/dev-stack uses Docker Compose** — The `/dev-stack` skill orchestrates the full development environment (PostgreSQL + FastAPI + React) via `docker-compose up`. It handles image building, service health checks, and dependency ordering. Node.js v22 runs in the frontend container (Alpine Linux). No local `uv`, `npm`, or Node.js installation needed if using containers. Run `/dev-stack` to start, `/dev-stack stop` to stop, `/dev-stack logs` to stream.
- **Official Student App — APP/STUDENT_APP_REDUX/** — The canonical React student application is `APP/STUDENT_APP_REDUX/`. All student-facing UI, grammar practice features, dashboards, and components target this location. The deprecated `grammar-app.html` at root is archived in `_deprecated/`. All student app development is React-based in STUDENT_APP_REDUX.
- **Grammar Practice App — STUDENT_APP_REDUX is canonical** — The official grammar practice implementation is `APP/STUDENT_APP_REDUX/src/components/GrammarPractice.tsx` (React). The standalone `grammar-app.html` at root was replaced and is archived in `_deprecated/`. All grammar UI development targets the React component only.
- **VLM-fused extraction (qwen3-vl) drops `passage_text`** — the model ignores the schema field and dumps passage content into `question_text` instead. `_split_passage_from_question()` (stem-opener regex) and `_recover_passage_from_raw_text()` (pymupdf fallback) in `_normalize_extracted_questions()` fix this. The stem openers must be high-confidence only (not "the author"/"the narrator" which appear in passages); `_______` blanks count as sentence boundaries.
- **Pymupdf raw_text recovery requires 2000-char lookback** — SAT passages can be 600+ chars between question number and stem. The 500-char window was too small for Q1.

- **Project:** DSAT_REDUX_MD
- Backend PRD lives at `docs/PRD/INGESTION_PRD.md`; older Wolf anatomy/root references to `INGESTION_PRD.md` can be stale.
- Backend PRD v2.1 Known Open Gaps are not fully current: OCR code exists in `backend/app/routers/ingest.py`, but the PRD still describes OCR strategies as not implemented.
- Answer-obfuscation fixes belong primarily in `rules_agent_dsat_reading_v2.md` for Craft/reading traps and constructs; grammar v7 should receive only shared option-quality/clue-control gates unless the issue is SEC-specific.
- `CB_ANSWERS_QUESTIONS_ANALYSIS.md` recommendations are mostly already reflected in current rules; remaining useful imports are quantitative distractor traps/failure modes for reading v2 and finer notes-synthesis goal/audience/content/failure keys for grammar v7.
- Exhaustive DSAT trap audits should split quantitative evidence traps into `rules_agent_dsat_reading_v2.md` and notes-synthesis goal/content/audience/failure metadata into `rules_agent_dsat_grammar_ingestion_generation_v7.md`; avoid duplicating reading-only constructs into grammar rules.
- Grammar v7 B.3 passage construction rules and B.4 distractor heuristic tables were incomplete for several promoted production keys (`comparative_structures`, `illogical_comparison`, `adjective_adverb_distinction`, `commonly_confused_words`, `preposition_idiom`, `pronoun_antecedent_agreement`, `pronoun_clarity`, `hyphen_usage`, `quotation_punctuation`, `logical_predication`); any newly promoted focus key must receive both a B.3 and a B.4 entry at promotion time.
- Reading v2 had no `figurative_language_meaning` WIC focus key, `figurative_interpretation_precision` construct key, or `figurative_meaning_blindness` failure mode — these are needed for metaphor/idiom/figurative WIC items where the literal definition is always a distractor.
- `causal_specification` text relationship (Text 2 explains *how/why* Text 1's phenomenon occurs) was missing from §11; differs from `broad_support` (corroboration) and `confirmation_with_qualification` (conditional agreement).
- When adding a new failure mode to §19.7 summary table, use an alphabetical sub-label (e.g., `5a`) rather than renumbering all subsequent rows, to preserve backward compatibility with existing annotation references.
- `backend/app/prompts/generate_prompt.py` now uses targeted section extraction for generation-critical grammar/reading rules; future prompt-loader changes should preserve inclusion of grammar B.4/B.13 and reading §16/§21.
- Keep production rule docs schema-aligned: grammar B.3/B.4 should cover every D.8 production `grammar_focus_key`, reading §16 should mention every §7 `reading_focus_key`, and `syntactic_trap_key` examples must remain within D.5/backend ontology.
- Layout detection is an enrichment step (never a gate): if `detect_layout()` fails, questions still persist with `NULL` crop_path/layout_json_path. It runs after OCR, independent of OCR strategy, gated only on `settings.layout_detection_enabled` + `settings.glm_ocr_model` + page renders existing.
- When adding new config settings (like `layout_detection_enabled`), update all `SimpleNamespace` test fixtures in `test_pipeline.py` and `test_backend_regressions.py` — missing attributes cause `AttributeError` at runtime.
- `_collect_page_images()` in ingest.py strips `page_number` from entries; layout code must use raw `_page_images` dicts instead, which carry `page_number`.
- Crop must happen inside `_persist_single_question()` because `question_id` is generated there; cropping earlier would lack the ID needed for the storage path.
- `_persist_single_question` now does 3 `db.flush()` calls (question+version, annotation+options, source_span); tests asserting `db.flush_count == 2` must be updated to `3`.
- `detect_layout()` uses `OllamaProvider` imported inside the function; patch at `app.llm.ollama_provider.OllamaProvider` in tests, not `app.storage.crop_detector.OllamaProvider`.
- `_stimulus_candidates()` reads from `q_data["stimulus_assets"]` / `q_data["visual_assets"]` / per-type keys; the extraction prompt must include `stimulus_assets` in the per-question schema or these will always be empty.
- **2-Phase Ingestion Performance — FIXED:** Phase 1b (DeepSeek extraction) can exceed 120s timeout on large documents (27-page test: 153.7s) but has retry/backoff recovery. Phase 2 was the bottleneck: reading grammar/reading rules from disk 27 times caused I/O overhead that pushed large tests past 30-minute timeout. **FIX APPLIED:** Added `@lru_cache` to `_read_file()`, `_grammar_context()`, and `_reading_context()` in `annotate_prompt.py`. Now rules are read once, cached in memory for all 27 questions. Estimated 40-75s speedup per ingestion (5-7% reduction). Large tests (25+ pages) should now fit within timeout.
- Stimulus region processing (crop + annotation + source span) is gated on `matched_region is not None`; if no question block was matched, stimulus regions on the page are skipped rather than guessed.
- `_annotate_layout_stimulus()` uses `provider.complete_vision()` — degrades gracefully for text-only providers since all failures return `{}`.
- `table_crop`, `chart_crop`, `figure_crop`, and `figure_asset` must exist as `object_kinds` in `storage_layout.yaml` for `put_object()` to resolve their bucket paths; they were previously only listed as `object_keys` inside a bucket, which is not the same thing.
- `_persist_single_question` now accepts an optional `provider` parameter for stimulus annotation; call sites that don't pass it receive no-op annotation (provider defaults to None).
- YAML export `_build_question_record()` strips `_`-prefixed keys from `stimulus_assets` entries before writing — the pipeline adds `_layout_label` and `_crop_path` as internal metadata that should not appear in the archive.

- `config.py` `rules_version` field is the metadata label stamped onto every `question_annotations.rules_version`. It was still `"v3"` long after `annotate_prompt.py` switched to loading v7 rules — so the annotation *content* was v7-quality but the label said v3. When upgrading the rules file, update `config.py:rules_version` **and** all `prompt_version="vN.0"` hardcodes in routers (ingest.py, generate.py, student.py) atomically.
- `scripts/reannotate_official_v7.py` — bulk re-annotation script that calls `/ingest/reannotate/{question_id}` for every `content_origin='official'` question; run it after fixing config.py to backfill v7 labels onto the 569 official questions.

## Do-Not-Repeat

- [2026-06-20] Do NOT use `SpacedRepetitionState.__new__(SpacedRepetitionState)` to build fake SR objects in unit tests. SQLAlchemy InstrumentedAttribute descriptors require a properly initialised mapper context; assigning attributes on a `__new__` instance raises `AttributeError: 'NoneType' object has not attribute 'set'`. Use a plain Python class (`class _FakeSR`) with the same fields instead.
- [2026-06-20] SM-2 interval grows exponentially — applying quality=5 thirty times causes `OverflowError: date value out of range` when computing `now + timedelta(days=interval_days)`. In EF-cap tests, reset `repetition_count` and `interval_days` before each iteration to keep dates in range while still exercising the EF formula.
- [2026-06-20] Vitest WASM/V8 segfault occurs on Node.js > 22.12.0 (native Ubuntu, not WSL2). Always run `nvm use 22.12.0` before `npx vitest run`. Running multiple test files in parallel can also trigger transient segfaults; if a test segfaults, re-run it individually — the code is fine, it's V8 multi-worker instability.



<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-06-18] Node 24.8.0 hits WASM compilation crash in V8 when running Vite/npm dev with esbuild on this machine (native Ubuntu, not WSL2). Switch to Node 22.12.0 via NVM. Use `source ~/.nvm/nvm.sh && nvm use 22.12.0` before npm commands.
- [2026-06-18] Vitest requires both setup file inclusion AND tsconfig.json types declaration for testing-library matchers. Missing either causes `toBeInTheDocument` to fail TS compilation. Fix: (1) create `src/vitest.setup.ts` with `import '@testing-library/jest-dom'`, (2) add `"types": ["vitest/globals", "@testing-library/jest-dom"]` to tsconfig.json compiler options, (3) reference setup file in vitest.config.ts `setupFiles: ['src/vitest.setup.ts']`.
- [2026-06-18] Hook tests with API mocks fail when the mock is set up via `vi.mock()` module-level but the hook's fetch call doesn't resolve in test time. Root cause: hook fetches in useEffect, but test awaits only `setTimeout(0)`. Solution: either skip hook-level API fetch tests and test via component (where async resolve is more visible), or rewrite hook to accept injected API client. Chose skip for Phase 1 since component tests are reliable.
- [2026-05-14] Do not assume root `INGESTION_PRD.md` exists from stale anatomy output; use `docs/PRD/INGESTION_PRD.md` for backend PRD audits.
- [2026-05-14] When inserting new numbered sections into long rule docs, immediately rg the affected heading prefix (e.g. `^### 16\.`) to catch duplicate/out-of-order numbering.
- [2026-05-16] When replacing text in DEBUG_LOG.md with python `content.replace()`, double-check that variable names (`old5` vs `new9`) match — a typo caused finding #5's text to be replaced with finding #9's text instead of finding #5's strikethrough version.
- [2026-05-18] `backend/app/models/ontology.py` is a GENERATED file — do not hand-edit it, nor the `<!-- VOCAB:... -->` appendix blocks in the rules docs. Edit `vocabulary/master.json` and run `python scripts/gen_vocab.py --generate`. `--check` is the drift gate.
- [2026-05-18] When LLM output fields drift from expected schema names, prefer observational logging (log which fallbacks were used) over deterministic constraints (JSON schema in prompt). User explicitly rejects adding JSON schema to prompts — it makes LLM output formula-based.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-05-25] **Draft re-activation + backup on promotion:** `gen_vocab.py --promote` must (1) before any mutation, snapshot all files under a single shared timestamp — vocabulary files to `vocabulary/backups/YYYY-MM-DDTHH-MM-SS/` (`master.json`, `aliases.json`, `candidates.json`) AND rules docs to `rules_backups/YYYY-MM-DDTHH-MM-SS/` (`rules_agent_dsat_grammar_ingestion_generation_v8.md`, `rules_agent_dsat_reading_v3.md`) — restore all on any failure; (2) after successful `--generate`, automatically set all `draft` questions whose controlled-vocab key was just promoted to `practice_status="approved"` in a single DB update.

- [2026-05-25] **Alias storage:** Use a separate `vocabulary/aliases.json` flat map (`{ "from": "to" }`), not inline fields in `master.json`. Keeps master.json canonical-only. `gen_vocab.py --promote` writes both files atomically. CI checks all alias targets resolve to active master.json keys.

- [2026-05-25] **Candidate promotion workflow (agreed):** After any ingestion beyond baseline, unrecognized keys land in `candidates.json` non-blocking. Promotion to `master.json` requires two gates: (1) LLM triage — three parallel model calls (Claude, OpenAI, Ollama `deepseek-v4-pro:cloud`) each independently classify every candidate as promote/alias/reject; review report shows all three verdicts side-by-side with dissent flagged; (2) admin confirms or overrides before `gen_vocab.py --promote` runs. No key enters `master.json` without both gates. Dev tooling: CLI-first via `review-candidates` skill; dashboard UI to follow. This is the only sanctioned promotion path.

- [2026-05-18] Controlled vocabulary: `vocabulary/master.json` is the single source of truth; `ontology.py` and rules-doc VOCAB blocks are generated from it. New keys the LLM invents go to `vocabulary/candidates.json` (non-blocking review queue), promoted via `gen_vocab.py --promote`. Chose master-JSON-canonical over ontology-canonical for strongest consistency, and a review queue over auto-append so vocabulary growth stays human-controlled. options.py option-level validators demoted from hard `ValueError` to non-blocking candidate recording.

- 2026-05-18 — Ingest jobs with any non-blocking validation warning (e.g.
  qnum_ocr_crosscheck) now route to `needs_review` instead of `approved`, and
  their questions persist as `practice_status="draft"` (held out of student
  rotation) until an admin clears them. Chosen over a passive jobs-list badge
  because warnings on auto-approved jobs were otherwise invisible. Trigger is
  any entry in `all_errors`; `defer_activation` flag in `_run_pipeline` is
  computed before the persist loop and passed to `_persist_single_question`.

## Key Learnings (diagnostic bank, 2026-06-23)
- The active question bank is 60 OFFICIAL questions only; the generated bank is empty (1 draft, 0 generation_batches). DB name is `dsat_dev` (not `dsat`), container `dsat-db` on port 5434.
- `annotation_jsonb.difficulty_overall` in the live bank only ever holds `low`/`medium` (+ null). No `high` exists despite ontology DIFFICULTY_KEYS including it.
- CRITICAL: grammar-v8 pipeline annotated ALL questions. Reading is classified via `skill_family_key` (singular); `reading_skill_family_key`/`reading_focus_key` are NULL on all 60. The student `/questions` reading filter and `diagnostic_submit` domain-derivation key off the empty fields → reading is unqueryable through that path (bug-761). Classify: reading if skill_family_key set, else grammar if grammar_role_key set.
- Student `/questions` (student_recall) leaks `current_correct_option_label` to clients (bug-760).

## Decision Log (2026-06-23) — diagnostic vs practice stats
- Weakness profile / recommendations (top_targets) must be driven by DIAGNOSTIC rows only
  (UserProgress.diagnostic_session_id IS NOT NULL). Practice answers do NOT feed it. Keep
  self_study_lookback_days decay; diagnostics stack within the window. Practice gets its own
  isolated improvement view (diagnostic_session_id IS NULL) via a new /study/practice-progress
  endpoint. Rationale: diagnostic = comprehensive weakness measurement; practice = remediation.
  Tasks: diagnostic_task.md TASK-B07 (profile filter) + TASK-B08 (practice endpoint).

## Decision Log (2026-06-23) — REVERT: practice stays in weakness profile
- Reverted the same-day "diagnostics only" decision. Weakness profile (top_targets) POOLS diagnostic
  + practice — the existing _compute_weakness_targets behavior; do NOT add a diagnostic_session_id
  filter. Practice-only improvement view (TASK-B08) is additive/optional, not a profile split.
  TASK-B07 dropped.
