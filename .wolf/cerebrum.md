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

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-05-14] Do not assume root `INGESTION_PRD.md` exists from stale anatomy output; use `docs/PRD/INGESTION_PRD.md` for backend PRD audits.
- [2026-05-14] When inserting new numbered sections into long rule docs, immediately rg the affected heading prefix (e.g. `^### 16\.`) to catch duplicate/out-of-order numbering.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
