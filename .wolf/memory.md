# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.
| 16:14 | Created ../.claude/projects/-home-jb-DSAT-REDUX-MD/memory/feedback_debug-log-workflow.md | — | ~207 |
| session | Exhaustive gap-fill: grammar v7 +B.3/B.4 rules for 5 promoted keys, 2 new syntactic traps, 5 failure modes, checks 26–29, D.3 rule 17; reading v2 +figurative WIC key, polarity_resolution mech, 5 TSP verbs, 3 passage archs, CoE-T vs CID disambiguation, false_concession_trap, causal_specification | rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md | success | ~110k |
| 13:39 | Created plan_benchmarking_backend.md — benchmark dir plan with runners + HTMX dashboard | plan_benchmarking_backend.md | ~600 |
| 16:14 | Created ../.claude/projects/-home-jb-DSAT-REDUX-MD/memory/project_backend-option-versioning.md | — | ~247 |
| 16:14 | Created ../.claude/projects/-home-jb-DSAT-REDUX-MD/memory/project_dual-user-routers.md | — | ~210 |
| 16:14 | Edited ../.claude/projects/-home-jb-DSAT-REDUX-MD/memory/MEMORY.md | 5→8 lines | ~215 |

## Session: 2026-05-09 16:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 20:11 | Inspected OpenWolf protocol/config and confirmed Wolf is enabled for repo workflow | .wolf/OPENWOLF.md, .wolf/config.json, .wolf/hooks/package.json | Will follow anatomy/memory/cerebrum rules for future repo work | ~700 |
| 20:56 | Audited backend PRD against backend routers/models for incomplete features and gaps | docs/PRD/INGESTION_PRD.md, backend/app/routers/*.py, backend/app/models/db.py | Identified PRD-known gaps plus stale OCR and auth/generation mismatches | ~9000 |
| 21:02 | Queried OpenWolf CLI help and subcommand help | openwolf CLI | Confirmed installed version 1.0.4 and available commands/options | ~1500 |
| 21:05 | Ran openwolf status | OpenWolf CLI | Core files/hooks present; anatomy tracks 670 files; daemon initialized | ~100 |
| 21:10 | Researched answer-choice/distractor standards and added report gaps section | answer_obfuscation_report.md | Added research-backed ## GAPS covering College Board, item-writing, metrics, and code drift | ~4500 |
| 21:16 | Located trap/failure-mode sections in reading and grammar rule files | rules_agent_dsat_reading_v2.md, rules_agent_dsat_grammar_ingestion_generation_v7.md | Identified exact sections/line ranges for reasoning traps, syntactic traps, and distractor engineering | ~2500 |
| 21:22 | Ported answer-obfuscation gaps into rule files | rules_agent_dsat_reading_v2.md, rules_agent_dsat_grammar_ingestion_generation_v7.md | Added reading construct/trap/failure-mode taxonomy and shared option-quality gate; fixed heading numbering | ~4500 |
| 21:28 | Compared CB answer analysis recommendations to current rules and added remaining gaps | CB_ANSWERS_QUESTIONS_ANALYSIS.md, rules_agent_dsat_reading_v2.md, rules_agent_dsat_grammar_ingestion_generation_v7.md | Added quantitative traps/failure modes and notes synthesis goal/content/failure keys | ~6500 |
| 21:45 | Exhaustive gap-fill audit — applied 21 targeted edits across grammar v7 and reading v2 | rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md | Added B.3/B.4/B.13/C.1.3/D.3/D.5/D.7/D.8.3 grammar additions; §2.3/§7.5/§8/§9/§10.2/§11/§12.1/§13.6/§15.2/§17/§19.1/§19.7/§21.1 reading additions | ~18000 |
| 16:25 | Edited backend/tests/test_backend_regressions.py | modified test_delete_user_removes_progress_before_user_delete() | ~526 |
| 16:26 | Edited backend/tests/test_student_router.py | modified test_student_stats_empty() | ~192 |
| 16:26 | Edited backend/tests/test_admin_router.py | modified test_admin_eval_score_not_found() | ~175 |
| 16:26 | Edited backend/app/routers/student.py | 5→7 lines | ~82 |
| 16:27 | Edited backend/app/routers/student.py | 4→4 lines | ~78 |
| 16:27 | Edited backend/app/routers/student.py | removed 16 lines | ~15 |
| 16:27 | Edited backend/app/routers/admin.py | 6→8 lines | ~119 |
| 16:27 | Edited backend/app/routers/admin.py | modified list_relations() | ~249 |
| 16:27 | Edited backend/app/routers/student.py | 4→3 lines | ~27 |
| 16:28 | Edited backend/tests/test_backend_regressions.py | 3→2 lines | ~23 |
| 16:29 | Session end: 10 writes across 5 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 10 reads | ~12342 tok |
| 16:31 | Edited CHANGELOG.md | expanded (+38 lines) | ~387 |
| 16:31 | Session end: 11 writes across 6 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 11 reads | ~19760 tok |
| 16:32 | Created .claude/rules/debug-log.md | — | ~401 |
| 16:33 | Edited DEBUG_LOG.md | expanded (+21 lines) | ~364 |
| 16:33 | Session end: 13 writes across 8 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 14 reads | ~23367 tok |
| 17:20 | Edited backend/app/routers/ingest.py | 3→5 lines | ~99 |
| 17:20 | Edited backend/app/routers/ingest.py | 3→5 lines | ~82 |
| 17:20 | Edited backend/app/routers/generate.py | 3→5 lines | ~91 |
| 17:20 | Edited backend/app/routers/generate.py | 3→5 lines | ~82 |
| 17:20 | Edited backend/app/routers/admin.py | inline fix | ~13 |
| 17:20 | Edited backend/app/routers/admin.py | expanded (+12 lines) | ~180 |
| 17:21 | Edited DEBUG_LOG.md | modified Fixed() | ~230 |
| 17:21 | Edited DEBUG_LOG.md | 4→5 lines | ~155 |
| 17:21 | Session end: 21 writes across 10 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 18 reads | ~30834 tok |
| 17:23 | Session end: 21 writes across 10 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 18 reads | ~32045 tok |
| 17:24 | Edited backend/app/config.py | added 1 import(s) | ~28 |
| 17:24 | Edited backend/app/config.py | modified get_settings() | ~22 |
| 17:24 | Edited backend/app/main.py | modified _warn_if_insecure_keys() | ~298 |
| 17:25 | Edited backend/tests/conftest.py | modified _clear_settings_cache() | ~58 |
| 17:25 | Edited DEBUG_LOG.md | 4→5 lines | ~156 |
| 17:25 | Session end: 26 writes across 13 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 21 reads | ~32619 tok |
| 17:32 | Session end: 26 writes across 13 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 21 reads | ~32619 tok |
| 17:33 | Session end: 26 writes across 13 files (test_backend_regressions.py, test_student_router.py, test_admin_router.py, student.py, admin.py) | 23 reads | ~38116 tok |
| 17:36 | Created INGESTION_PRD.md | — | ~8098 |

## Session: 2026-05-10 17:38

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:17 | Created docs/PRD/INGESTION_PRD.md | — | ~10647 |
| 18:17 | Updated INGESTION_PRD.md to v2.1: added §8 OCR Strategy with Option A (DeepSeek) and Option B (Ollama VLM), renumbered §8-22 to §9-23 | docs/PRD/INGESTION_PRD.md | success | ~4800 |
| 18:17 | Session end: 1 writes across 1 files (INGESTION_PRD.md) | 3 reads | ~22762 tok |
| 18:40 | Edited docs/PRD/INGESTION_PRD.md | modified data() | ~644 |
| 18:40 | Edited docs/PRD/INGESTION_PRD.md | 5→5 lines | ~70 |
| 18:40 | Edited docs/PRD/INGESTION_PRD.md | 2→2 lines | ~75 |
| 18:40 | Edited docs/PRD/INGESTION_PRD.md | 11→13 lines | ~152 |
| 18:40 | Updated INGESTION_PRD.md §8.6-8.7: both OCR options configured simultaneously, admin selects per-job via ocr_strategy param | docs/PRD/INGESTION_PRD.md | success | ~800 |
| 18:40 | Session end: 5 writes across 1 files (INGESTION_PRD.md) | 3 reads | ~23771 tok |
| 19:16 | Edited docs/PRD/INGESTION_PRD.md | modified options() | ~846 |
| 19:17 | Edited docs/PRD/INGESTION_PRD.md | 13→13 lines | ~192 |
| 19:17 | Edited docs/PRD/INGESTION_PRD.md | 3→3 lines | ~62 |
| 19:58 | Created DEEPSEEK_OCR.md | — | ~3361 |
| 19:58 | Edited docs/PRD/INGESTION_PRD.md | VL2() → Tiny() | ~67 |
| 19:58 | Edited docs/PRD/INGESTION_PRD.md | inline fix | ~23 |
| 19:58 | Created DEEPSEEK_OCR.md: local setup guide for Linux and Mac, DeepSeek-OCR-2 vs VL2, vLLM/LMDeploy/MPS paths | DEEPSEEK_OCR.md | success | ~3200 |
| 19:58 | Session end: 11 writes across 2 files (INGESTION_PRD.md, DEEPSEEK_OCR.md) | 3 reads | ~28647 tok |
| 20:09 | Created TASKS_OCR.md | — | ~7616 |

## Session: 2026-05-10 20:12

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 20:12 | Edited backend/app/config.py | 6→10 lines | ~125 |
| 20:12 | Edited backend/app/llm/base.py | modified complete() | ~282 |
| 20:12 | Edited backend/app/llm/ollama_provider.py | modified complete_vision() | ~477 |
| 20:13 | Created backend/app/parsers/ocr.py | — | ~668 |
| 20:13 | Edited backend/app/llm/factory.py | modified get_ocr_client() | ~93 |
| 20:13 | Edited backend/app/prompts/extract_prompt.py | modified build_vision_extract_prompt() | ~229 |
| 20:15 | Edited backend/app/routers/ingest.py | modified _collect_page_images() | ~1926 |
| 20:16 | Edited backend/app/routers/ingest.py | modified ingest_official_pdf() | ~1042 |
| 20:16 | Edited backend/app/routers/ingest.py | modified ingest_unofficial_file() | ~982 |
| 20:16 | Edited backend/app/parsers/pdf_parser.py | expanded (+6 lines) | ~240 |
| 20:17 | Created backend/tests/test_ocr.py | — | ~1990 |
| 20:18 | Edited backend/tests/test_ingest_router.py | modified test_safe_read_body_too_large() | ~370 |
| 20:18 | Edited backend/tests/test_ingest_router.py | 3→1 lines | ~10 |
| 22:07 | Edited TASKS_OCR.md | 26→26 lines | ~469 |
| 22:08 | Edited DEBUG_LOG.md | expanded (+22 lines) | ~413 |
| 22:08 | Session end: 15 writes across 12 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 12 reads | ~42452 tok |
| 22:15 | Edited CHANGELOG.md | modified path() | ~846 |
| 22:15 | Session end: 16 writes across 13 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 13 reads | ~50720 tok |
| 11:44 | Created ../.claude/plans/wiggly-shimmying-leaf.md | — | ~1372 |
| 11:52 | Session end: 17 writes across 14 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 18 reads | ~65759 tok |
| 11:52 | Session end: 17 writes across 14 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 18 reads | ~65759 tok |
| 11:53 | Session end: 17 writes across 14 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 18 reads | ~65759 tok |
| 12:02 | Session end: 17 writes across 14 files (config.py, base.py, ollama_provider.py, ocr.py, factory.py) | 18 reads | ~65759 tok |

## Session: 2026-05-10 12:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 13:39 | Created plan_benchmarking_backend.md | — | ~886 |
| 13:40 | Session end: 1 writes across 1 files (plan_benchmarking_backend.md) | 0 reads | ~949 tok |
| 13:49 | Session end: 1 writes across 1 files (plan_benchmarking_backend.md) | 0 reads | ~949 tok |

## Session: 2026-05-11 17:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:10 | Edited DEBUG_LOG.md | modified feat() | ~1543 |
| 18:11 | Session end: 1 writes across 1 files (DEBUG_LOG.md) | 16 reads | ~31247 tok |
| 18:13 | Session end: 1 writes across 1 files (DEBUG_LOG.md) | 16 reads | ~31247 tok |
| 18:15 | Edited backend/app/pipeline/overlap.py | modified detect_overlaps() | ~62 |
| 18:15 | Edited backend/app/pipeline/overlap.py | 3→3 lines | ~30 |
| 18:15 | Edited backend/app/routers/ingest.py | 7→7 lines | ~72 |
| 18:15 | Edited backend/app/routers/ingest.py | 5→8 lines | ~46 |
| 18:15 | Edited backend/app/routers/ingest.py | modified _log_task_exception() | ~78 |
| 18:16 | Edited backend/app/routers/ingest.py | 3→3 lines | ~55 |
| 18:16 | Edited backend/app/routers/ingest.py | 3→3 lines | ~67 |
| 18:16 | Edited backend/app/routers/generate.py | modified _log_task_exception() | ~98 |
| 18:16 | Edited backend/app/routers/generate.py | modified _run() | ~78 |
| 18:16 | Edited backend/app/routers/generate.py | modified _run() | ~86 |
| 18:16 | Edited backend/app/routers/ingest.py | modified first() | ~136 |
| 18:16 | Edited backend/app/routers/ingest.py | modified first() | ~136 |
| 18:17 | Edited backend/app/routers/ingest.py | modified in() | ~121 |
| 18:17 | Edited backend/app/routers/ingest.py | inline fix | ~22 |
| 18:17 | Edited CHANGELOG.md | modified signature() | ~644 |
| 18:17 | Edited DEBUG_LOG.md | 3→4 lines | ~124 |
| 18:17 | Edited DEBUG_LOG.md | 3→4 lines | ~138 |
| 18:17 | Edited DEBUG_LOG.md | 3→4 lines | ~146 |
| 18:18 | Edited DEBUG_LOG.md | 2→3 lines | ~85 |
| 18:18 | Session end: 20 writes across 5 files (DEBUG_LOG.md, overlap.py, ingest.py, generate.py, CHANGELOG.md) | 17 reads | ~44472 tok |
| 18:18 | Session end: 20 writes across 5 files (DEBUG_LOG.md, overlap.py, ingest.py, generate.py, CHANGELOG.md) | 17 reads | ~44472 tok |
| 18:28 | Session end: 20 writes across 5 files (DEBUG_LOG.md, overlap.py, ingest.py, generate.py, CHANGELOG.md) | 19 reads | ~45072 tok |

## Session: 2026-05-11 18:33

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:34 | Edited backend/app/llm/ollama_provider.py | modified complete_vision() | ~85 |
| 18:34 | Edited backend/app/parsers/ocr.py | added 1 import(s) | ~58 |
| 18:34 | Edited backend/app/parsers/ocr.py | modified extract() | ~46 |
| 18:35 | Edited DEBUG_LOG.md | added error handling | ~769 |
| 18:35 | Edited CHANGELOG.md | expanded (+22 lines) | ~316 |
| 18:35 | Edited backend/app/llm/factory.py | append() → values() | ~550 |
| 18:36 | Edited backend/app/pipeline/validator.py | modified get() | ~110 |
| 18:36 | Edited DEBUG_LOG.md | 7→9 lines | ~380 |
| 18:36 | Edited CHANGELOG.md | expanded (+20 lines) | ~504 |

## Session: 2026-05-11 18:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:46 | Edited CHANGELOG.md | modified feat() | ~1478 |
| 18:46 | Session end: 1 writes across 1 files (CHANGELOG.md) | 11 reads | ~34594 tok |
| 18:51 | Edited backend/app/llm/anthropic_provider.py | modified __init__() | ~819 |
| 18:51 | Edited backend/app/llm/openai_provider.py | modified __init__() | ~837 |
| 18:52 | Edited backend/app/models/payload.py | modified ReannotateRequest() | ~147 |
| 18:52 | Edited backend/app/routers/ingest.py | inline fix | ~28 |
| 18:52 | Edited backend/app/routers/ingest.py | modified _resolve_ocr_strategy() | ~587 |
| 18:52 | Edited backend/app/routers/ingest.py | modified in() | ~1245 |
| 18:52 | Edited backend/app/routers/ingest.py | expanded (+13 lines) | ~389 |
| 18:53 | Edited backend/app/routers/ingest.py | 3→4 lines | ~43 |
| 18:53 | Edited backend/app/routers/ingest.py | expanded (+7 lines) | ~272 |
| 18:53 | Edited backend/app/routers/ingest.py | 2→4 lines | ~53 |
| 18:53 | Edited backend/app/routers/ingest.py | 3→3 lines | ~94 |
| 18:53 | Edited backend/app/routers/ingest.py | 6→7 lines | ~79 |
| 18:53 | Edited backend/app/routers/ingest.py | 3→3 lines | ~88 |
| 18:53 | Edited backend/app/routers/ingest.py | inline fix | ~42 |
| 18:54 | Edited backend/app/routers/ingest.py | modified ingest_benchmark_ocr() | ~1714 |
| 18:54 | Edited backend/app/routers/ingest.py | inline fix | ~24 |
| 18:54 | Edited backend/app/routers/ingest.py | inline fix | ~25 |
| 18:54 | Edited backend/app/routers/ingest.py | inline fix | ~23 |

## Session: 2026-05-11 19:00

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 19:06 | Edited backend/app/routers/ingest.py | inline fix | ~22 |
| 19:09 | Edited backend/app/routers/ingest.py | modified getattr() | ~122 |
| 19:12 | Edited backend/app/llm/factory.py | values() → append() | ~609 |
| 19:14 | Edited backend/app/routers/ingest.py | inline fix | ~58 |
| 19:14 | Edited backend/app/routers/ingest.py | 2→2 lines | ~15 |
| 19:15 | Edited backend/app/models/payload.py | modified JobResponse() | ~72 |
| 19:15 | Edited backend/app/routers/ingest.py | reduced (-6 lines) | ~80 |
| 19:16 | Created backend/migrations/versions/014_add_comparison_group_index.py | — | ~126 |
| 19:16 | Edited backend/app/models/db.py | 4→5 lines | ~63 |
| 19:20 | Edited CHANGELOG.md | expanded (+54 lines) | ~943 |
| 19:21 | Fixed 9 ingest pipeline gaps: token_usage getattr, OCR strategy priority, factory _provider_registry, validator severity, reannotate meta, dead code, job status response, comparison_group_id index | ingest.py factory.py validator.py payload.py db.py migration-014 | 197/197 tests pass | ~4000 |
| 19:21 | Session end: 10 writes across 6 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 11 reads | ~44813 tok |
| 19:37 | Session end: 10 writes across 6 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 11 reads | ~46179 tok |
| 19:39 | Session end: 10 writes across 6 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 11 reads | ~46179 tok |
| 19:40 | Session end: 10 writes across 6 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 11 reads | ~46179 tok |
| 19:45 | Edited backend/tests/test_ingest_router.py | modified test_ingest_unofficial_file_rejects_invalid_ocr_strategy() | ~844 |
| 20:48 | Edited backend/app/models/payload.py | modified OCRBenchmarkResponse() | ~41 |
| 20:48 | Edited backend/app/routers/ingest.py | expanded (+10 lines) | ~276 |
| 20:48 | Edited backend/app/routers/ingest.py | inline fix | ~30 |
| 20:48 | Edited backend/app/routers/ingest.py | 22→26 lines | ~253 |
| 20:57 | Session end: 15 writes across 7 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 12 reads | ~49707 tok |
| 23:07 | Edited backend/app/llm/retry.py | modified _sdk_connection_types() | ~429 |
| 23:08 | Edited backend/tests/test_llm_providers.py | modified test_retry_fires_on_429_status_code() | ~458 |
| 23:09 | Session end: 17 writes across 9 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 14 reads | ~51494 tok |
| 23:21 | Session end: 17 writes across 9 files (ingest.py, factory.py, payload.py, 014_add_comparison_group_index.py, db.py) | 14 reads | ~51494 tok |

## Session: 2026-05-11 01:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:34 | Edited backend/app/routers/ingest.py | added 1 import(s) | ~37 |
| 01:34 | Edited backend/app/routers/ingest.py | 9→10 lines | ~142 |
| 01:34 | Edited backend/app/routers/ingest.py | 2→3 lines | ~41 |
| 01:34 | Edited backend/app/parsers/json_parser.py | 4→4 lines | ~47 |
| 01:36 | Edited backend/app/routers/ingest.py | 3→2 lines | ~22 |
| 01:36 | Edited backend/app/routers/ingest.py | 10→12 lines | ~156 |
| 01:36 | Edited backend/app/routers/ingest.py | 3→5 lines | ~48 |
| 01:39 | Edited CHANGELOG.md | expanded (+30 lines) | ~710 |
| 01:41 | Session end: 8 writes across 3 files (ingest.py, json_parser.py, CHANGELOG.md) | 11 reads | ~47648 tok |
| 01:44 | Session end: 8 writes across 3 files (ingest.py, json_parser.py, CHANGELOG.md) | 11 reads | ~47648 tok |
| 01:51 | Session end: 8 writes across 3 files (ingest.py, json_parser.py, CHANGELOG.md) | 11 reads | ~47648 tok |
| 11:36 | Created backend/test_ocr_live.py | — | ~2654 |

## Session: 2026-05-11 12:04

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:06 | Edited backend/app/routers/ingest.py | modified _clean_option_label() | ~710 |
| 12:09 | Edited backend/tests/test_backend_regressions.py | modified test_normalize_questions_strips_trailing_paren_from_correct_label() | ~873 |
| 12:13 | Edited CHANGELOG.md | expanded (+25 lines) | ~652 |
| 12:15 | Fix: VLM label normalization (bug-025) + dedup (bug-026) in _normalize_extracted_questions | ingest.py | 29 tests pass | ~500 |
| 12:15 | Live-test: deepseek-ocr:latest on small image → 763 tokens, all 4Q extracted (prior failure was oversized image) | — | verified | ~200 |
| 12:15 | Logged bug-025, bug-026 to buglog.json; updated CHANGELOG round 4 | .wolf/buglog.json, CHANGELOG.md | done | ~300 |
| 12:24 | Edited backend/app/routers/ingest.py | expanded (+6 lines) | ~154 |
| 12:24 | Edited backend/app/models/payload.py | modified OCRJobResult() | ~89 |
| 12:24 | Edited backend/app/llm/ollama_provider.py | modified __init__() | ~145 |
| 12:24 | Edited backend/app/llm/ollama_provider.py | modified close() | ~302 |
| 12:24 | Edited backend/app/routers/ingest.py | 10→11 lines | ~129 |
| 12:42 | Edited backend/tests/test_ocr.py | modified test_ollama_complete_vision_sends_image_url_blocks() | ~245 |
| 12:58 | Edited CHANGELOG.md | expanded (+10 lines) | ~347 |
| 13:10 | Edited backend/tests/test_config.py | 4→4 lines | ~71 |
| 13:28 | Edited backend/app/llm/ollama_provider.py | 12→15 lines | ~184 |
| 13:33 | Session end: 12 writes across 7 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 11 reads | ~52738 tok |
| 13:34 | Edited DEBUG_LOG.md | modified feat() | ~927 |
| 13:34 | Session end: 13 writes across 8 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 12 reads | ~61446 tok |
| 13:35 | Session end: 13 writes across 8 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 12 reads | ~61446 tok |
| 13:43 | Created backend/benchmark_results/2026-05-11_pt1_mod01_page3.md | — | ~2200 |
| 13:44 | Session end: 14 writes across 9 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 12 reads | ~63803 tok |
| 13:47 | Session end: 14 writes across 9 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 12 reads | ~63803 tok |
| 13:57 | Session end: 14 writes across 9 files (ingest.py, test_backend_regressions.py, CHANGELOG.md, payload.py, ollama_provider.py) | 12 reads | ~63803 tok |

## Session: 2026-05-11 14:01

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:02 | Edited backend/app/routers/ingest.py | modified _save_page_image() | ~584 |
| 14:02 | Edited backend/app/routers/ingest.py | modified strip() | ~234 |
| 14:02 | Edited backend/app/routers/ingest.py | modified strip() | ~616 |
| 14:02 | Edited backend/app/routers/ingest.py | modified strip() | ~522 |
| 14:02 | Edited backend/app/routers/ingest.py | modified gc_page_images() | ~145 |
| 22:48 | Session end: 5 writes across 1 files (ingest.py) | 1 reads | ~19014 tok |
| 01:41 | Session end: 5 writes across 1 files (ingest.py) | 1 reads | ~19014 tok |
| 01:42 | Session end: 5 writes across 1 files (ingest.py) | 1 reads | ~19014 tok |
| 01:43 | Session end: 5 writes across 1 files (ingest.py) | 2 reads | ~19623 tok |
| 01:46 | Session end: 5 writes across 1 files (ingest.py) | 3 reads | ~22277 tok |
| 01:48 | Session end: 5 writes across 1 files (ingest.py) | 3 reads | ~22277 tok |
| 01:49 | Session end: 5 writes across 1 files (ingest.py) | 3 reads | ~22277 tok |
| 01:50 | Session end: 5 writes across 1 files (ingest.py) | 3 reads | ~22277 tok |
| 01:52 | Created backend/benchmark_results/2026-05-11_pt1_mod01_page3.md | — | ~2398 |
| 01:52 | Created backend/benchmark_results/SUMMARY.md | — | ~994 |
| 01:54 | Session end: 7 writes across 3 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md) | 4 reads | ~27974 tok |
| 02:14 | Created backend/benchmark_results/2026-05-11_pt1_mod01_page3.md | — | ~1406 |
| 02:14 | Created backend/benchmark_results/SUMMARY.md | — | ~1223 |
| 02:14 | Session end: 9 writes across 3 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md) | 5 reads | ~31220 tok |
| 02:18 | Edited backend/benchmark_results/2026-05-11_pt1_mod01_page3.md | expanded (+14 lines) | ~222 |
| 02:18 | Edited backend/benchmark_results/2026-05-11_pt1_mod01_page3.md | 8→9 lines | ~178 |
| 02:18 | Edited backend/benchmark_results/SUMMARY.md | 8→9 lines | ~229 |
| 02:18 | Edited backend/benchmark_results/SUMMARY.md | 8→9 lines | ~117 |
| 02:19 | Session end: 13 writes across 3 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md) | 5 reads | ~31274 tok |
| 02:19 | Session end: 13 writes across 3 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md) | 5 reads | ~31274 tok |
| 02:34 | Session end: 13 writes across 3 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md) | 6 reads | ~35352 tok |
| 02:48 | Edited backend/app/routers/ingest.py | modified _should_auto_activate_official() | ~286 |
| 02:48 | Edited backend/app/routers/ingest.py | modified all() | ~250 |
| 02:48 | Edited backend/app/routers/ingest.py | expanded (+15 lines) | ~340 |
| 02:48 | Created backend/migrations/versions/015_official_question_unique_constraint.py | — | ~272 |
| 03:14 | Session end: 17 writes across 4 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md, 015_official_question_unique_constraint.py) | 7 reads | ~37044 tok |
| 03:21 | Session end: 17 writes across 4 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md, 015_official_question_unique_constraint.py) | 7 reads | ~37044 tok |
| 10:07 | Edited backend/app/routers/ingest.py | modified _validate_question_numbers() | ~1008 |
| 10:07 | Edited backend/app/routers/ingest.py | expanded (+10 lines) | ~329 |
| 10:07 | Edited backend/tests/test_backend_regressions.py | modified test_normalize_questions_dedup_is_case_insensitive() | ~854 |
| 10:09 | Edited backend/app/routers/ingest.py | modified enumerate() | ~275 |
| 10:10 | Session end: 21 writes across 5 files (ingest.py, 2026-05-11_pt1_mod01_page3.md, SUMMARY.md, 015_official_question_unique_constraint.py, test_backend_regressions.py) | 8 reads | ~51523 tok |
| 13:04 | Edited backend/app/config.py | 10→13 lines | ~169 |
| 13:04 | Edited backend/app/routers/ingest.py | modified _resolve_ocr_strategy() | ~379 |
| 13:04 | Edited backend/app/routers/ingest.py | modified _available_ocr_strategies() | ~166 |
| 13:05 | Edited backend/app/routers/ingest.py | expanded (+48 lines) | ~1076 |
| 13:05 | Edited backend/app/routers/ingest.py | modified _scan_qnums_from_ocr() | ~740 |
| 13:05 | Edited backend/app/routers/ingest.py | expanded (+11 lines) | ~278 |
| 13:05 | Edited backend/app/routers/ingest.py | "deepseek" → "glm" | ~26 |
| 13:05 | Edited backend/app/routers/ingest.py | inline fix | ~27 |
| 13:06 | Edited backend/tests/test_backend_regressions.py | modified test_official_question_uuid_differs_by_field() | ~787 |
| 13:07 | Edited backend/tests/test_ocr.py | modified test_resolve_ocr_strategy_auto_prefers_glm() | ~430 |

## Session: 2026-05-12 13:09

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 21:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 10:51

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 12:54

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-15 21:01

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-15 21:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:32 | Exhaustive trap/test-construct audit | CB_ANSWERS_QUESTIONS_ANALYSIS.md, rules_agent_dsat_reading_v2.md, rules_agent_dsat_grammar_ingestion_generation_v7.md | Added missing quantitative traps/failure modes, validator checks, and notes-synthesis metadata to the correct rule files; verified with rg and diff stat | ~9000 |
| 21:42 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+43 lines) | ~842 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+80 lines) | ~1143 |

## Session: 2026-05-15 21:43

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | 5→9 lines | ~287 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | inline fix | ~119 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | 3→4 lines | ~135 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | 4→6 lines | ~154 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+19 lines) | ~325 |
| 21:43 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | inline fix | ~91 |
| 21:43 | Edited rules_agent_dsat_reading_v2.md | 4→5 lines | ~129 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 10→12 lines | ~322 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 5→6 lines | ~97 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 5→7 lines | ~156 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | modified established() | ~203 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 5→6 lines | ~100 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 6→8 lines | ~40 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 4→9 lines | ~264 |
| 21:44 | Edited rules_agent_dsat_reading_v2.md | 3→6 lines | ~275 |
| 21:45 | Edited rules_agent_dsat_reading_v2.md | 6→9 lines | ~262 |
| 21:45 | Edited rules_agent_dsat_reading_v2.md | modified the() | ~115 |
| 21:45 | Edited rules_agent_dsat_reading_v2.md | 9→10 lines | ~113 |
| 21:45 | Edited rules_agent_dsat_reading_v2.md | 6→7 lines | ~138 |
| 21:47 | Session end: 19 writes across 2 files (rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md) | 1 reads | ~25534 tok |
| 21:48 | Session end: 19 writes across 2 files (rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md) | 3 reads | ~71617 tok |
| 21:51 | Session end: 19 writes across 2 files (rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md) | 3 reads | ~71617 tok |
| 21:55 | Session end: 19 writes across 2 files (rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md) | 3 reads | ~71617 tok |

## Session: 2026-05-15 22:01

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 22:01 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+10 lines) | ~208 |
| 22:01 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+9 lines) | ~225 |
| 22:02 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+11 lines) | ~215 |
| 22:02 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+9 lines) | ~171 |
| 22:02 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+21 lines) | ~355 |
| 22:02 | Added B.3 secondary trap patterns (SVA, tense, comma, semicolon) + B.9 diversity gate | rules_agent_dsat_grammar_ingestion_generation_v7.md | complete | ~600 |
| 22:02 | Session end: 5 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 1 reads | ~27856 tok |
| 22:35 | Session end: 5 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28686 tok |
| 22:41 | Session end: 5 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28686 tok |
| 22:42 | Session end: 5 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28686 tok |
| 22:48 | Session end: 5 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28686 tok |
| 22:48 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | removed 10 lines | ~6 |
| 22:48 | Session end: 6 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28692 tok |
| 22:51 | Edited rules_agent_dsat_grammar_ingestion_generation_v7.md | expanded (+9 lines) | ~193 |
| 22:51 | Session end: 7 writes across 1 files (rules_agent_dsat_grammar_ingestion_generation_v7.md) | 2 reads | ~28773 tok |
| 22:55 | Audited active rule files for classification/generation completeness | rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md, backend/app/prompts/generate_prompt.py, backend/app/prompts/annotate_prompt.py | Found strong corpus coverage but remaining operational gaps: generation prompt truncation, missing per-key generation/distractor sections, internal syntactic-trap inconsistencies, and reading disambiguation extraction omission | ~12000 |
| 23:05 | Fixed prompt loading and per-key generation gaps | backend/app/prompts/generate_prompt.py, backend/app/prompts/annotate_prompt.py, backend/tests/test_prompts.py, rules_agent_dsat_grammar_ingestion_generation_v7.md, rules_agent_dsat_reading_v2.md | Replaced truncating loader with targeted section extraction, fixed reading section extraction, added grammar B.3/B.4 coverage for all production focus keys, added reading 16.9 per-focus recipes, normalized trap keys, and verified with prompt tests/scans | ~14000 |
| 23:06 | Ran backend verification | backend/tests, backend/test_ocr_live.py | `uv run pytest tests` passed 237/237 with 2 skipped; full `uv run pytest` still collects preexisting live OCR helpers that lack an `image` fixture | ~3000 |
| 23:12 | Updated changelog for all post-commit changes | CHANGELOG.md | Added top-level 2026-05-15 entry covering prompt loader fixes, rule-file completeness updates, reading refinements, tests, known OCR caveat, and Wolf metadata | ~2500 |
