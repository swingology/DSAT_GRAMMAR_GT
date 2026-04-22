# PRD v2 vs. Deprecated Migrations (001–042): Gap Analysis

**Date:** 2026-04-20  
**References:** `docs/Migrations_PRD_v2_rebuild.md`, `backend/migrations/001–042`

---

## Structure: 42 → 28 migrations

| | Deprecated (001–042) | PRD v2 (M-001–M-028) |
|---|---|---|
| Migration count | 42 | 28 |
| Organization | Linear/appended | 8 semantic phases |
| Seed data | Scattered | Consolidated in M-004, M-022–M-028 |

---

## Phase-by-Phase Gaps

### Phase 0 — Foundation (M-001–M-004)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `fn_set_content_hash()` | Added in 027 | Defined in M-001 before questions table |
| `fn_set_word_counts()` | Never exists as trigger function | Defined in M-001, wired in M-005 |
| `fn_check_active_retirement_consistency()` | Not a DB trigger | Defined in M-001 |
| `fn_check_paired_retirement()` | Not in schema | Defined in M-001 |
| `lookup_grammar_focus` columns | No `grammar_role_key` FK, no `disambiguation_priority`, no `frequency_label` (through 042) | Full structure in M-003 |
| `lookup_grammar_focus` seed count | 27 keys (039+041+042 piecemeal patches) | All 29 keys in M-004 from day 1 |
| `lookup_grammar_role` | Absent; never existed | Created in M-003 before `lookup_grammar_focus` |
| `lookup_passage_topic_fine` | Free-text `topic_fine` column, never normalized | Normalized FK lookup table in M-003 |
| `lookup_dimension_compatibility` | Absent | Created in M-003 |
| `exam_module_form_targets` | Absent; `target_composition_jsonb` used instead | Structured table in M-002 |
| `exam_modules.difficulty_band` CHECK constraint | Missing — free text | Constrained in M-002 |
| New lookup tables | Missing: `lookup_distractor_construction`, `lookup_eliminability`, `lookup_coaching_annotation_type`, `lookup_syntactic_interruption`, `lookup_syntactic_trap`, `lookup_noun_phrase_complexity`, `lookup_vocabulary_profile`, `lookup_cohesion_device`, `lookup_epistemic_stance`, `lookup_inference_distance`, `lookup_transitional_logic`, `lookup_passage_topic_domain`, `lookup_argument_role` | All present in M-003 |

### Phase 1 — Core Schema (M-005–M-009)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `paired_passage_sets` table | Absent — `paired_passage_text` is a raw column on `questions` | Proper table created before `questions` in M-005 |
| `passage_word_count` / `stem_word_count` | Added in 020 as plain columns; no trigger | Computed by trigger from M-005 creation |
| `content_hash` | Added in 027 | Trigger-computed from M-005 creation |
| `retirement_status` | Added in 025/020 | Present from M-005 creation |
| `tokenization_status` | Added in 040 | Present from M-005 creation |
| `coaching_completion_status` | Absent | Present from M-005 |
| `canonical_explanation_source` | Absent | Present from M-005 |
| `question_classifications.domain_key` | Free-text `domain text` (normalized in 025) | FK to `lookup_domain` from M-006 |
| `grammar_role_key` on classifications | Absent through 042 | Present from M-006 |
| `no_change_is_correct` / `multi_error_flag` | Never in deprecated schema | Present from M-006 |
| `topic_fine_key` | Free-text | FK to `lookup_passage_topic_fine` in M-006 |
| `irt_b_quantitative_adjustment` | Added in 031 | Present from M-006 |
| `solver_steps` table | Created as `primary_solver_steps_jsonb` column in 006, dropped in 034, never replaced | Proper normalized table in M-008 |
| `question_reasoning.coaching_summary` | Added in 034 | Present from M-008 creation |
| `evidence_span_start_char` / `_end_char` | Absent | Present from M-008 |
| `question_generation_profiles.target_grammar_role_key` | Absent | Present from M-009 |
| `question_generation_profiles.target_mirror_status` | Absent | Present from M-009 |
| `target_passage_topic_fine_key` | Free-text or absent | FK in M-009 |

### Phase 2 — Content & Media (M-010–M-011)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `question_images` table | Absent | New in M-010 |
| `question_embeddings` | Existed in deprecated schema | Consolidated in M-011 |
| `question_performance_records` | `student_performance` table in 022 | Renamed/restructured in M-011 |

### Phase 4 — Generation (M-013–M-014)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `generation_templates` table | Absent | New in M-013 |
| `distractor_slot_profiles` table | Absent | New in M-014 |
| `generated_questions` traceability | Added in 035 | Present from M-013 |
| `generation_params_snapshot_jsonb` | Absent | Present from M-013 |

### Phase 5 — Coaching (M-015–M-016)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `question_coaching_annotations.option_label` | **Missing** from 034 — can't link distractor_lure spans to specific options | Present from M-015 creation |
| `grammar_keys` table | Added in 039 | Present from M-016 |
| `question_token_annotations` | Added in 039/040 | Present from M-016 |

### Phase 6 — Integrity (M-017–M-019)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| Cross-dimension compatibility trigger | Absent — app-code only in `validator.py` | DB trigger `trg_qclass_dimension_compatibility` in M-017 |
| SEC grammar enforcement | App-code only | DB trigger `trg_qclass_sec_grammar` in M-018 |
| Skill family ↔ domain validation | App-code only | DB trigger `trg_qclass_skill_family_domain` in M-018 |
| Grammar focus ↔ role validation | App-code only | DB trigger `trg_qclass_grammar_focus_role` in M-018 |
| `fn_compute_irt_b_v1()` with `irt_b_quantitative_adjustment` | Added in 033 without adjustment | Correct formula from M-019 |

### Phase 7 — Reporting (M-020)

| Issue | Deprecated | PRD Fix |
|---|---|---|
| `v_corpus_fingerprint` materialized view | Absent | New in M-020 |
| `v_generation_traceability` view | Absent | New in M-020 |
| `v_difficulty_calibration` view | Absent | New in M-020 |
| `v_coaching_panel` view | Added in 034 (without `option_label`, `solver_steps`) | Full version with both in M-020 |
| `fn_refresh_corpus_fingerprint()` | Absent | New in M-020 |

---

## Summary

### Net-new tables (never in deprecated)
`paired_passage_sets`, `exam_module_form_targets`, `lookup_grammar_role`, `lookup_passage_topic_fine`, `lookup_dimension_compatibility`, `question_images`, `generation_templates`, `distractor_slot_profiles` + 13 new lookup tables

### Fixed structural defects (existed but wrong)
- `lookup_grammar_focus` — missing 2 keys + missing 3 columns (`grammar_role_key`, `disambiguation_priority`, `frequency_label`)
- `question_coaching_annotations` — missing `option_label` (can't link distractor_lure spans to answer options)
- `question_classifications.domain_key` — free-text normalized to FK
- `solver_steps` — replaced dropped `primary_solver_steps_jsonb` column with proper table
- `question_generation_profiles` — missing `target_grammar_role_key` and `target_mirror_status`
- `exam_modules.difficulty_band` — unconstrained text

### Enforcement moved from app-code to DB triggers
SEC grammar fields, dimension compatibility, skill-family/domain consistency, grammar-focus/role mapping

### Consolidation wins
42 migrations → 28 by eliminating patch chains: grammar_focus seeds, content_hash, word_count triggers, retirement columns, tokenization columns all arrived late in the deprecated sequence and are baked in from day 1 in v2.
