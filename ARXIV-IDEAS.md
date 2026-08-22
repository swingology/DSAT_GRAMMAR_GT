# ArXiv Paper Ideas

## Idea 1: A Consensus-Gated Pipeline for LLM-Generated Standardized Test Items

**Status:** scoped, not started. System-description paper — no empirical/eval results yet, architecture and design decisions only.

**Framing:** Not "we built a chatbot for SAT prep." The contribution is a *content pipeline architecture* for a hard sub-problem: generating multiple-choice items that must satisfy strict psychometric/style constraints (SAT fidelity, distractor quality, no copyright leakage), with an explicit human-in-the-loop gate rather than auto-publishing LLM output.

### Why this is paper-worthy

1. **Three-layer content model** — official exemplars → generated drafts → advisory review. Generated content stays non-authoritative (`content_origin="generated"`, `practice_status="draft"`) until explicit admin promotion. Clean provenance/trust architecture separating "in-context example," "candidate," and "verified."

2. **Seeding strategy** — generated items are matched to official exemplars by domain/difficulty (`_select_source_question_ids_for_batch`), with source-rotation across exam codes (`_rotate_source_ids`) to avoid overfitting to one source test, exclusion of recently-reused sources, and full lineage tracking (`Question.generation_source_set`) with operational metadata (provider/model/seed/temperature) stripped before storage. Reproducibility-relevant design choice.

3. **Consensus-as-threshold-gate, not voting** — `compute_consensus()` is an ordered first-match-wins decision tree over pooled rubric scores (realism, SAT fidelity, distractor quality, taxonomy match, copy-risk), not majority vote. `accept_votes`/`needs_review_votes`/`reject_votes` are computed and stored but never appear in a branching condition — audit metadata, not the decision mechanism. Worth being precise about this in the paper: "review swarm" sounds like voting and isn't.

4. **The honest failure mode (genuine methodological contribution)** — multi-provider "independence" collapses when all named providers (`gpt-4o`, `claude-sonnet-4-6`, `ollama`) route to the same underlying local model via the LiteLLM proxy, producing near-zero disagreement and a fake-looking consensus. The team's response: shrink to one honest reviewer (`generation_review_providers="ollama"`) rather than fake independence. This is a real warning for anyone building LLM-ensemble evaluation setups — "different provider names" does not imply "independent judges." Worth reporting as a finding, not hiding as a limitation.

5. **Controlled-vocabulary governance** — an amendment-contract system (`vocabulary/amendments/{pending,approved,rejected,needs_manual_patch}/`) to prevent taxonomy drift between what generation LLMs emit and what the schema/prompts accept, across 49 vocabularies / 632 active entries. Practical solution to a known problem in structured LLM output pipelines: unknown keys are non-blockingly queued (`vocab_candidates.record_unknown_field`) rather than failing the pipeline, and the invariant is rule-doc-body approval before vocabulary growth.

### What this paper should NOT claim

- No learning-outcome or pedagogical-efficacy claims — no student outcome data exists.
- No psychometric validity claims for generated items — no eval data exists.
- Not a "3-provider swarm achieves X% agreement" paper — the live default config is a single reviewer; the multi-provider path is built but not the deployed default. State this plainly rather than have it surface as a discovered inconsistency.
- Scope is architecture/systems, closer to a workshop paper or arXiv preprint than a venue submission with results tables.

### Grounding (as of 2026-08-08 survey)

- Ingestion: `backend/app/routers/ingest.py`, `docs/backend/INGESTION_ARCHITECTURE.md` (canonical, code-authoritative). State machine: `pending→parsing→extracting→annotating→(overlap_checking)→validating→approved|needs_review|failed`.
- OCR: `backend/app/parsers/ocr.py::DeepSeekOCRClient`, chain `glm→deepseek→anthropic→openai→ollama`, separate HTTP client bypassing LiteLLM proxy.
- Extraction/annotation default model: `qwen3.6:27b` via Ollama (`default_annotation_model`), not DeepSeek — despite the "GLM-OCR + deepseek" shorthand in older memory notes.
- Generation: `backend/app/routers/generate.py` (1,567 lines), `docs/GENERATION_ARCHITECTURE.md`, `TASKS_GENERATION.md` (11 phases, 0–6 implemented; 7+ unverified in this pass).
- Review swarm: `backend/app/review/runner.py::run_review_swarm()`, `backend/app/prompts/review_prompt.py` (`RUBRIC_VERSION="v1"`), `backend/app/review/parser.py::REQUIRED_SCORE_KEYS` (7 dimensions, 0–10), `backend/app/review/consensus.py::compute_consensus()`.
- Live config caveat: `backend/app/config.py:149`, `generation_review_providers: str = "ollama"` — single reviewer by default; `docs/litellm.md` documents the rollback reasoning.
- Auto-release: `backend/app/review/auto_release.py` (422 lines), fully implemented, gated off by `generation_auto_release_enabled: bool = False`.
- Vocabulary governance: `vocabulary/master.json`, `backend/app/pipeline/validator.py` (349 lines), `backend/app/pipeline/amendments.py`, `docs/backend/VOCABULARY_GOVERNANCE.md`. Amendment auto-promotion (`--promote-from-amendment`) is an acknowledged, unbuilt gap.
- Scale: rule docs — grammar v8 (6,994 lines), reading v3 (3,110 lines), review v1 (240 lines); MATH v1 (784 lines, explicitly not-yet-built extension, Phase 0 unchecked). Backend ~31,714 LOC, 35 Alembic migrations. Generation batch sizing: default 5, max 25, max 20 pending batches. 19 official verbal PDFs currently ingested.

### Open question before drafting

Scope check: is the paper about the whole pipeline end-to-end, or narrowed specifically to the consensus-gate mechanism (item 3+4 above) as the core contribution, with the rest as supporting system context? Narrower scope is likely a stronger single paper; the full-pipeline version risks reading as a system report rather than a contribution with a thesis.
