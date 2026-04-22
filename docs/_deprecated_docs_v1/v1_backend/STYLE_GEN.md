# STYLE_GEN.md — Style & Generation Schema Audit

Generated from schema review of migrations 017–036. Last updated 2026-04-02.

---

## What This System Does

Each ground truth question gets annotated with a **style fingerprint** across ~25 dimensions on
`question_classifications`. Those same dimensions have parallel `target_*` columns on
`question_generation_profiles`, so when you run a generation job you can specify exactly what
stylistic profile the output passage should match.

The intended workflow:
1. Ingest a real SAT question → LLM Pass 2 annotates all style/prose/grammar fields
2. DB accumulates a corpus of fingerprinted ground-truth questions
3. To generate a new question, build a `question_generation_profiles` row with the desired
   `target_*` values, then query the corpus for similar questions to use as style exemplars
4. Generation prompt = target spec + exemplars → LLM output constrained to match both

---

## Full Dimension Inventory

### Syntax & Grammar Structure (migrations 017–018)

| Column on `question_classifications` | Lookup / Type | Values |
|--------------------------------------|---------------|--------|
| `syntactic_complexity_key` | `lookup_syntactic_complexity` | 16 values: simple, compound, complex, compound-complex, embedded-relative, nominalized, interrupted, heavily-embedded, parallel, inverted, mixed, right-branching, left-branching, center-embedded, phrasal-dominant, clausal-dominant |
| `syntactic_interruption_key` | `lookup_syntactic_interruption` | 13 values: none, em-dash, paired em-dash, parenthetical, appositive, non-restrictive relative, absolute phrase, participial phrase, delayed subject, multiple, reduced relative clause, fronted PP, interpolated attribution |
| `syntactic_trap_key` | `lookup_syntactic_trap` | 21 values: none, garden-path, early clause anchor, nominalization obscures subject, interruption breaks SV, long-distance dependency, nearest-noun attraction, pronoun ambiguity, scope of negation, modifier attachment, presupposition trap, temporal sequence ambiguity, multiple, agentless passive, full passive w/ by-phrase, object relative clause, stacked PPs, multiple negation, conditional stacking, long preverbal subject, tough-movement |
| `clause_depth` | `int` | 0–4 (CHECK added migration 032) |
| `nominalization_density` | check | low / medium / high |
| `sentence_length_profile` | check | short / medium / long / mixed |
| `lexical_density` | check | low / medium / high |
| `noun_phrase_complexity_key` | `lookup_noun_phrase_complexity` | 8 values: simple NP, adj-premodified, noun-stacked, PP-postmodified, non-finite postmodified, relative-clause postmodified, stacked premodifiers, multiply-postmodified |

### Vocabulary & Lexical (migration 018)

| Column | Lookup | Values |
|--------|--------|--------|
| `lexical_tier_key` | `lookup_lexical_tier` | 6 values: general, academic (AWL), domain-specific, mixed, low-frequency, archaic/literary |
| `vocabulary_profile_key` | `lookup_vocabulary_profile` | 7 values: high-freq dominant, mixed, AWL-heavy, low-freq heavy, domain-specific heavy, high TTR, archaic/literary |

### Discourse & Rhetorical Structure (migrations 018–019)

| Column | Lookup | Values |
|--------|--------|--------|
| `rhetorical_structure_key` | `lookup_rhetorical_structure` | 11 values: claim→evidence, problem→solution, compare/contrast, cause→effect, definition→expansion, narrative sequence, concession→rebuttal, classification/division, extended analogy, description→elaboration, mixed |
| `cohesion_device_key` | `lookup_cohesion_device` | 8 values: lexical repetition, pronoun chain, conjunctive adverb, transitional phrase, ellipsis, substitution, mixed, none |
| `epistemic_stance_key` | `lookup_epistemic_stance` | 7 values: assertive, hedged, speculative, tentative, evaluative, imperative, mixed |
| `inference_distance_key` | `lookup_inference_distance` | 6 values: within clause, within sentence, adjacent sentences, paragraph-level, cross-paragraph, unstated/implied |
| `transitional_logic_key` | `lookup_transitional_logic` | 10 values: additive, adversative, causal, concessive, temporal, exemplification, summative, clarification, conditional, none |
| `evidence_distribution_key` | `lookup_evidence_distribution` | 12 values: single sentence, adjacent, front-loaded, end-loaded, distributed, cross-paragraph, embedded in example, contrapositive, visual/data, center-loaded, sandwich, suspended disclosure |
| `passage_word_count_band` | check | very_short / short / medium / long / very_long |

### Prose Style & Register (migrations 020, 024)

| Column | Lookup / Type | Values |
|--------|---------------|--------|
| `prose_register_key` | `lookup_prose_register` | 6 values: formal_academic, semi_formal_narrative, technical_scientific, archaic_elevated, journalistic_analytical, literary_narrative |
| `prose_tone_key` | `lookup_prose_tone` | 8 values: analytical, narrative, persuasive, expository, descriptive, reflective, critical, mixed |
| `passage_source_type_key` | `lookup_passage_source_type` | 7 values: academic_journal, scientific_report, textbook_reference, literary_fiction, primary_document, memoir_personal_essay, journalism_analysis |
| `narrator_perspective_key` | check | first_person / third_person / institutional / impersonal |
| `passage_era_key` | check | contemporary / modern / historical / timeless |
| `craft_signals_array` | `text[]` (validated) | 8 values: concession, qualification, irony, understatement, analogy, antithesis, exemplification, hedged_assertion |

### Grammar Focus (migrations 019, 025)

| Column | Lookup | Values |
|--------|--------|--------|
| `grammar_role_key` | `lookup_grammar_role` | Broad grammatical role category |
| `grammar_focus_key` (generation target) | `lookup_grammar_focus` | 13 values: SV agreement, pronoun-antecedent, pronoun case, modifier placement, parallel structure, verb tense, verb form, comma splice, fragment, semicolon/colon, apostrophe, comma usage, sentence boundary |

### Difficulty (migration 033)

| Column | Type | Notes |
|--------|------|-------|
| `irt_b_estimate` | `numeric(4,2)` | Difficulty ranking [-3, +3]. Computed from classification columns via `fn_compute_irt_b_v1()` — never produced directly by the LLM, ensuring consistency across providers (Claude, Ollama, OpenRouter). |
| `irt_b_rubric_version` | text | `v1` (rubric-derived) / `empirical` (student data) / `manual` |
| `irt_b_source` | text | How the estimate was produced |

Rubric v1 weights: `inference_distance` 0.30 · `evidence_distribution` 0.20 · `syntactic_complexity` 0.20 · `lexical_tier` 0.15 · `syntactic_trap` 0.10 · `np_complexity` 0.05. Call `SELECT fn_refresh_irt_b();` after bulk Pass 2 annotation runs.

---

## Generation Profile Mirrors (`question_generation_profiles`)

All major classification dimensions now have `target_*` counterparts. Closed gaps:

| Migration | What was added |
|-----------|---------------|
| 026 | `target_syntactic_interruption_key`, `target_syntactic_trap_key`, `target_clause_depth_min/max`, `target_nominalization_density`, `target_lexical_density`, `target_distractor_construction_key`, `target_distractor_difficulty_spread` |
| 031 | `target_noun_phrase_complexity_key`, `target_evidence_distribution_key`, `target_sentence_length_profile`, `target_vocabulary_profile_key` |
| 032 | `target_passage_source_type_key` |

---

## Generation Traceability (migration 035)

Generated questions use **Flow B** (generation-first): `question_generation_profiles` is created
post-approval from Pass 2 classification output. A FK to the profile is therefore wrong.

Instead, `generated_questions` carries:
- `generation_params_snapshot_jsonb` — immutable snapshot of all `target_*` params used at
  generation time. Written once; never updated.
- `generation_model_name` / `generation_provider` — item-level model attribution, distinct from
  the batch-level `generation_runs.model_name` (covers fallbacks and multi-provider runs).

`v_generation_traceability` surfaces `difficulty_drifted` and `syntax_drifted` flags by comparing
snapshot targets against the approved question's classification. Use for prompt calibration.

---

## Coaching Annotation Layer (migration 034)

Difficult questions surface in the UI with highlighted spans. Each span is a row in
`question_coaching_annotations`:

| Layer | Location | What |
|-------|----------|------|
| `coaching_tip` | `question_reasoning` | One-liner |
| `coaching_summary` | `question_reasoning` | 2–4 sentence explanation of why the question is hard |
| `question_coaching_annotations` | own table | Per-span highlights with `coaching_note`, `show_condition` (always / on_error / on_request) |

Span location uses **character offsets** (primary) + **`span_sentence_index`** (fallback when
passage text is edited). See Task #1: app layer must invalidate char offsets on passage text update.

Annotation types: `syntactic_trap` · `key_evidence` · `np_cluster` · `clause_boundary` ·
`blank_context` · `distractor_lure` · `rhetorical_move`

---

## Table / Graph Questions (migration 020, updated d1c72d7)

`table_data_jsonb` and `graph_data_jsonb` remain JSONB (intentional — testing viability in first
build). Shapes are documented as `COMMENT ON COLUMN` in migration 020.

| Stimulus mode | Column | Shape |
|---------------|--------|-------|
| `prose_plus_table` | `table_data_jsonb` | `{ title, headers: [str], rows: [[str]], units?, source_note? }` |
| `prose_plus_graph` | `graph_data_jsonb` | `{ graph_type, title, x_axis, y_axis, series: [{name, values}], source_note? }` |
| `notes_bullets` | `notes_bullets_jsonb` | `{ title?, bullets: [str] }` |

Source/origin compatibility (migration 036):
- Official CB table/graph → `source_type='official'`, `content_origin='official'`
- Generated table/graph → `source_type='generated'`, `content_origin='ai_human_revised'`

---

## Is This Too Generic?

### What works

The combination of dimensions is genuinely constraining. Specifying:

> `formal_academic` + `analytical` + `claim→evidence` + `hedged` + `AWL-heavy` + `complex` +
> `em_dash` + `academic_journal` + `cross-paragraph` evidence + `stacked premodifiers`

...gives an LLM a very specific target that rules out most of the output space. The dimensions
are grounded in real linguistic research (Coh-Metrix, Biber, Halliday, Hyland) rather than
ad hoc intuition, which means they map to real stylistic variation.

`passage_source_type_key` is the most powerful single field — "academic_journal" carries an
implicit bundle of constraints (formal register, hedged assertions, third-person, heavy NP
complexity, AWL vocabulary) that a generation model trained on enough text already knows.

### Where it still breaks down

**1. Tags don't compose into prompts automatically.**
The `target_*` columns are data. Nothing currently translates them into a coherent generation
prompt. A prompt-builder is logged as a future task (see below).

**2. Categorical labels have wide variance within them.**
"Formal academic" encompasses a Victorian scientific paper and a 2023 *Nature* article.
The tags anchor generation to a region of style space, not a point.

**3. No exemplar pointer.**
The most reliable way to get stylistic fidelity is few-shot. Exemplar retrieval via
`question_embeddings` (passage_only type) is the intended mechanism but not yet formalized.

**4. Generation prompt compression.**
If all 20+ target dimensions are surfaced in a prompt, the LLM will satisfice — hitting
register and tone while drifting on NP complexity and cohesion device. Exemplars compensate
for this (point 3).

---

## Future Work

| Item | Notes |
|------|-------|
| **Prompt builder** | Reads `target_*` columns → outputs structured natural-language style spec for LLM. Also needs: exemplar retrieval via `question_embeddings` (passage_only), post-generation Pass 2 diff against target fingerprint. Full spec in memory. |
| **Normalize table/graph JSONB** | After first build validates viability, replace JSONB with typed tables. |
| **Empirical IRT calibration** | At ~500+ student responses per item, overwrite `irt_b_estimate` with empirical values and set `irt_b_rubric_version = 'empirical'`. |
| **Coaching annotation tooling** | App layer: invalidate char offsets on passage text edit (Task #1); UI: render `question_coaching_annotations` spans as interactive highlights. |
