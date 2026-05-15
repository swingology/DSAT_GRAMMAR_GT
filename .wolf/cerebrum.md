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

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-05-14] Do not assume root `INGESTION_PRD.md` exists from stale anatomy output; use `docs/PRD/INGESTION_PRD.md` for backend PRD audits.
- [2026-05-14] When inserting new numbered sections into long rule docs, immediately rg the affected heading prefix (e.g. `^### 16\.`) to catch duplicate/out-of-order numbering.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
