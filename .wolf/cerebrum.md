# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-05-15

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

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
- Stimulus region processing (crop + annotation + source span) is gated on `matched_region is not None`; if no question block was matched, stimulus regions on the page are skipped rather than guessed.
- `_annotate_layout_stimulus()` uses `provider.complete_vision()` — degrades gracefully for text-only providers since all failures return `{}`.
- `table_crop`, `chart_crop`, `figure_crop`, and `figure_asset` must exist as `object_kinds` in `storage_layout.yaml` for `put_object()` to resolve their bucket paths; they were previously only listed as `object_keys` inside a bucket, which is not the same thing.
- `_persist_single_question` now accepts an optional `provider` parameter for stimulus annotation; call sites that don't pass it receive no-op annotation (provider defaults to None).
- YAML export `_build_question_record()` strips `_`-prefixed keys from `stimulus_assets` entries before writing — the pipeline adds `_layout_label` and `_crop_path` as internal metadata that should not appear in the archive.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-05-14] Do not assume root `INGESTION_PRD.md` exists from stale anatomy output; use `docs/PRD/INGESTION_PRD.md` for backend PRD audits.
- [2026-05-14] When inserting new numbered sections into long rule docs, immediately rg the affected heading prefix (e.g. `^### 16\.`) to catch duplicate/out-of-order numbering.
- [2026-05-16] When replacing text in DEBUG_LOG.md with python `content.replace()`, double-check that variable names (`old5` vs `new9`) match — a typo caused finding #5's text to be replaced with finding #9's text instead of finding #5's strikethrough version.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->

- 2026-05-18 — Ingest jobs with any non-blocking validation warning (e.g.
  qnum_ocr_crosscheck) now route to `needs_review` instead of `approved`, and
  their questions persist as `practice_status="draft"` (held out of student
  rotation) until an admin clears them. Chosen over a passive jobs-list badge
  because warnings on auto-approved jobs were otherwise invisible. Trigger is
  any entry in `all_errors`; `defer_activation` flag in `_run_pipeline` is
  computed before the persist loop and passed to `_persist_single_question`.
