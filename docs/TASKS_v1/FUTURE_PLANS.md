# Future Plans

---

## Completed

| Migration | Name | Status |
|-----------|------|--------|
| `017_prose_grammar_complexity.sql` | Prose Grammar Complexity — 4 lookup tables, 8 classification columns (`syntactic_complexity_key`, `syntactic_interruption_key`, `evidence_distribution_key`, `syntactic_trap_key`, `clause_depth`, `nominalization_density`, `sentence_length_profile`, `lexical_density`) | ✅ Applied |
| `018_writing_style_complexity.sql` | Writing Style & Complexity Profiling — 4 new lookup tables (`lookup_lexical_tier`, `lookup_rhetorical_structure`, `lookup_noun_phrase_complexity`, `lookup_vocabulary_profile`), extended 4 existing lookup tables with research-grounded keys (Coh-Metrix, TAASSC, Biber), 5 classification columns, 2 generation profile columns | ✅ Applied |
| `019_discourse_generation_factors.sql` | Discourse & Generation Factors — 5 new lookup tables (`lookup_cohesion_device`, `lookup_epistemic_stance`, `lookup_inference_distance`, `lookup_transitional_logic`, `lookup_grammar_focus`), 5 classification columns, 4 generation profile columns | ✅ Applied |
| `024_style_composition.sql` | Style Composition — 4 new lookup tables (`lookup_prose_register`, `lookup_prose_tone`, `lookup_passage_source_type`, `lookup_craft_signal`); deprecates `style_profile_jsonb` and `target_style_constraints_jsonb` JSONB placeholders; adds `prose_register_key`, `prose_tone_key`, `passage_source_type_key`, `craft_signals_array` to classifications; adds `target_prose_register_key`, `target_prose_tone_key`, `target_passage_source_type_key`, `target_craft_signals_jsonb`, `target_style_traits_jsonb`, `target_lexile_min`, `target_lexile_max` to generation profiles. Total lookup tables: 32. | ✅ Applied |
| `025_consolidation.sql` | Schema Consolidation — 9 new lookup tables (`lookup_domain`, `lookup_skill_family`, `lookup_passage_type`, `lookup_evidence_mode`, `lookup_reading_scope`, `lookup_reasoning_demand`, `lookup_grammar_role`, `lookup_hidden_clue_type`, `lookup_distractor_subtype`); normalizes all free-text taxonomy fields to FK-backed keys; adds `irt_b_estimate`/`irt_b_source` to classifications; drops `grammar_subtype`, `register`, `tone`, `target_reading_level`, `target_sentence_complexity`, `target_passage_length`; adds 16 typed `target_*` columns to generation profiles; adds `hidden_clue_type_key` to reasoning and `distractor_subtype_key` to options. Total lookup tables: 41. | ✅ Applied |

**Re-annotation:** `scripts/reannotate_prose_grammar.py` is ready to populate all 18 new taxonomy fields on existing questions via `claude-sonnet-4-6`. Blocked on Anthropic API credits — run `uv run python scripts/reannotate_prose_grammar.py` once credits are topped up, then `uv run python scripts/generate_embeddings.py`.

---

## Database

### GENERATION DB SCHEMA IMPROVEMENTS

> **STATUS: Largely implemented.** See completed migrations below. Two items remain open — see dedicated sections further below.

| Item | Status | Migration |
|------|--------|-----------|
| Generated item lineage (`generated_questions`) | ✅ Done | 021 |
| Generation runs / batches (`generation_runs`) | ✅ Done | 021 |
| Review and approval workflow (`review_status`, `content_origin`) | ✅ Done | 020, 021 |
| Calibration metrics (`realism_score`, `irt_b_estimate`) | ✅ Done | 021 |
| Stimulus/span anchoring (sentence-level) | ✅ Done | 020 |
| Template/version management (`generation_templates`) | ✅ Done | 020 |
| Source segregation (`content_origin`) | ✅ Done | 020 |
| Student performance / field-testing loop | ✅ Done | 022 |
| Ontology proposals / approval workflow | ✅ Done | 023 |
| Span anchoring (character-level) | ❌ Open | See below |
| Multi-stage derivation tracking | ❌ Open | See below |
| Constraint execution records | 🔵 Low priority | Deferred |

---

### Multi-Stage Derivation Tracking

#### Problem

`generated_questions` tracks which official item was used as a seed (`seed_question_id`) but has no way to represent revision history. When a human editor improves an AI draft, the relationship between the draft and the revision is lost. Over time this means:

- You cannot measure what human editing actually changes (and whether it matters)
- You cannot train or prompt toward patterns that produce items closest to approved quality without a revision step
- If the same draft is revised twice, you cannot compare the two revision paths

#### What Is Missing

| Missing Structure | What To Add |
|------------------|-------------|
| Parent/child link on generated items | `parent_generated_question_id uuid` on `generated_questions` (or on `questions`) |
| Revision record | `question_revisions` table: captures what changed between two versions and why |
| Derivation chain view | View that walks the full chain: official seed → AI draft → human revision → approved |

#### Proposed Schema

```sql
-- On questions: link a revised version back to the AI draft it came from
ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS parent_question_id uuid REFERENCES public.questions(id);

-- Revision record: one row per human edit pass
CREATE TABLE IF NOT EXISTS public.question_revisions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         uuid NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    parent_question_id  uuid REFERENCES public.questions(id),
    revised_by          text,
    revision_notes      text NOT NULL,   -- what was changed and why
    fields_changed      text[],          -- e.g. ['prompt_text', 'option_B_text']
    revision_type       text NOT NULL    -- 'human_edit' | 'model_revision' | 'review_correction'
                        CHECK (revision_type IN ('human_edit', 'model_revision', 'review_correction')),
    created_at          timestamptz NOT NULL DEFAULT now()
);
```

#### Why It Matters for Generation

When you have derivation chains, you can:
1. Identify which generation patterns require the least human editing to reach approval → those are your best templates
2. Compare AI draft quality across model versions by measuring average edit distance to approval
3. Build a dataset of (AI draft, human revision) pairs that could eventually be used for fine-tuning or prompt improvement

#### Implementation Notes

- `parent_question_id` is nullable — most official items have no parent
- `revision_type = 'model_revision'` covers the case where a second LLM pass is used to improve a draft
- The chain is always: `official source ← seed_question_id ← generated_questions ← parent_question_id ← revision`

---

### Character-Level Span Offsets

#### Problem

Migration 020 added sentence-level anchoring for blank placement (`blank_position_key`, `evidence_distance`, `blank_sentence_index`). This is sufficient for generation prompting but not sufficient for:

1. **Programmatic validation of generated output** — confirming the blank is actually at the right character position in the generated text
2. **Distractor span anchoring** — knowing which exact passage text each distractor misreads, which enables automatic distractor quality checking
3. **Precise retrieval** — finding all questions where the blank appears after a semicolon, or where evidence is in a parenthetical

#### What Is Missing

| Column | Table | Type | Purpose |
|--------|-------|------|---------|
| `blank_char_start` | `question_classifications` | `int` | Character offset of blank in `prompt_text` |
| `blank_char_end` | `question_classifications` | `int` | End of blank position |
| `evidence_char_start` | `question_classifications` | `int` | Character offset of key evidence in `passage_text` |
| `evidence_char_end` | `question_classifications` | `int` | End of evidence span |
| `anchor_text` | `question_options` | `text` | Which passage text this distractor exploits |
| `anchor_char_start` | `question_options` | `int` | Character offset of that text in `passage_text` |
| `anchor_char_end` | `question_options` | `int` | End of anchor span |

#### Proposed Schema

```sql
-- On question_classifications
ALTER TABLE public.question_classifications
    ADD COLUMN IF NOT EXISTS blank_char_start    int CHECK (blank_char_start >= 0),
    ADD COLUMN IF NOT EXISTS blank_char_end      int CHECK (blank_char_end >= 0),
    ADD COLUMN IF NOT EXISTS evidence_char_start int CHECK (evidence_char_start >= 0),
    ADD COLUMN IF NOT EXISTS evidence_char_end   int CHECK (evidence_char_end >= 0);

-- On question_options
ALTER TABLE public.question_options
    ADD COLUMN IF NOT EXISTS anchor_text       text,
    ADD COLUMN IF NOT EXISTS anchor_char_start int CHECK (anchor_char_start >= 0),
    ADD COLUMN IF NOT EXISTS anchor_char_end   int CHECK (anchor_char_end >= 0);
```

#### Annotation Approach

Character offsets should be populated:
1. **For official questions** — by a post-processing script that locates the blank token in `prompt_text` and the `evidence_span_text` in `passage_text` using string search
2. **For generated questions** — by the generation pipeline itself, which knows where it placed the blank during construction
3. **For distractor anchors** — via a separate LLM pass or regex pass that identifies which passage substring each distractor is exploiting

#### Implementation Notes

- All offset columns are nullable — sentence-level anchoring (020) remains the baseline
- Char offsets are 0-based, half-open intervals: `text[blank_char_start:blank_char_end]` gives the blank token or `_____`
- Population of these fields is a separate script/pipeline step, not part of Pass 2 annotation (too detail-heavy for the main annotation LLM)

---

### Prose Grammar Complexity — Schema Extension

> **STATUS: IMPLEMENTED in Migration 017** — see Completed table above.

#### Context

A detailed audit of the existing ontology against real question samples revealed that the skeleton for prose grammar complexity already exists (`style_traits_jsonb`, `difficulty_grammar`, `target_sentence_complexity`) but none of these fields are granular enough to drive reliable generation of specific prose grammar patterns. The fields that exist are too coarse:

| Field | What It Captures | Limitation |
|-------|-----------------|------------|
| `difficulty_reading` | Overall reading difficulty (`low/medium/high`) | Too coarse — doesn't specify *why* it's hard |
| `target_sentence_complexity` | e.g. `"multi-sentence"`, `"data"` | Captures length/count only, not internal structure |
| `register` | e.g. `"technical explanatory"` | Captures formality, not syntactic complexity |
| `style_traits_jsonb` | Array of style descriptors | Currently `[]` in all samples — **unused** |
| `difficulty_vocab` | Vocabulary difficulty | Separate from grammar complexity |
| `difficulty_grammar` | Grammar difficulty rating | Only `low/medium/high` — no structural breakdown |

---

#### What's Missing

| Missing Field | What It Would Encode |
|---------------|---------------------|
| `syntactic_complexity_key` | `embedded_clauses`, `nominalized`, `interrupted_syntax`, `simple` |
| `clause_depth` | Integer — how many levels of subordination/embedding |
| `nominalization_density` | `low`, `medium`, `high` |
| `syntactic_interruption_type` | `em_dash`, `parenthetical`, `appositive`, `none` |
| `sentence_length_profile` | `short`, `medium`, `long`, `mixed` |
| `evidence_distribution_key` | `front_loaded`, `end_loaded`, `distributed` — where key evidence sits in the passage |
| `syntactic_trap_type` | `early_clause_anchor`, `nominalization_obscures_subject`, `interruption_breaks_chain` |

---

#### Proposed Approach

Two complementary changes — the quickest win and the most precise one.

**Option A — Populate `style_traits_jsonb` with controlled tags (quick win)**

`style_traits_jsonb` already exists on `question_classifications` and is always `[]`. Populate it with a controlled vocabulary of prose grammar tags:

```json
"style_traits_jsonb": [
  "heavy_nominalization",
  "em_dash_interruption",
  "distributed_evidence",
  "multi_level_embedding"
]
```

No schema change needed. Requires:
1. Defining the controlled tag vocabulary (document in a lookup reference)
2. Adding tags to the Pass 2 prompt
3. Adding validator check to reject unknown tags

**Option B — Restructure `difficulty_grammar` into a nested JSONB object (precise)**

Replace the scalar `difficulty_grammar text` with a structured JSONB column:

```sql
ALTER TABLE public.question_classifications
  DROP COLUMN IF EXISTS difficulty_grammar;

ALTER TABLE public.question_classifications
  ADD COLUMN difficulty_grammar_jsonb jsonb;
```

Shape:

```json
"difficulty_grammar_jsonb": {
  "overall": "high",
  "nominalization": "high",
  "clause_depth": 3,
  "interruption_type": "em_dash",
  "sentence_length_profile": "long",
  "syntactic_trap_type": "nominalization_obscures_subject"
}
```

New lookup tables:

```sql
CREATE TABLE public.lookup_syntactic_complexity (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    sort_order   int NOT NULL DEFAULT 0
);
-- Seeds: simple | compound | complex | compound_complex |
--        embedded_clauses | nominalized | interrupted_syntax | heavily_embedded

CREATE TABLE public.lookup_evidence_distribution (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    sort_order   int NOT NULL DEFAULT 0
);
-- Seeds: front_loaded | end_loaded | distributed | single_sentence | cross_paragraph
```

New columns on `question_classifications`:

```sql
ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    syntactic_complexity_key   text REFERENCES public.lookup_syntactic_complexity(key);

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    evidence_distribution_key  text REFERENCES public.lookup_evidence_distribution(key);

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    difficulty_grammar_jsonb   jsonb;
-- Shape: { overall, nominalization, clause_depth, interruption_type,
--           sentence_length_profile, syntactic_trap_type }
```

---

#### Pass 2 Prompt Addition

```json
"prose_grammar_profile": {
  "syntactic_complexity_key": "embedded_clauses",
  "clause_depth": 3,
  "nominalization_density": "high",
  "interruption_type": "em_dash",
  "sentence_length_profile": "long",
  "evidence_distribution_key": "distributed",
  "syntactic_trap_type": "nominalization_obscures_subject",
  "style_traits": ["heavy_nominalization", "em_dash_interruption", "distributed_evidence"]
}
```

---

#### Recommendation

Start with **Option A** (populate `style_traits_jsonb`) — zero schema cost, immediate value for generation. Validate that the controlled tag vocabulary is stable across ~50 questions before committing to Option B. Option B is the right long-term target but requires a careful migration of existing `difficulty_grammar` scalar values.

---

#### Implementation Order

1. Define controlled `style_traits` tag vocabulary — document in a reference file
2. Update Pass 2 prompt — add `prose_grammar_profile` section
3. Update `app/models/annotation.py` — add `prose_grammar_profile` to `ClassificationAnnotation`
4. Update `app/pipeline/validator.py` — validate style trait tags against allowed set
5. `migrations/018_prose_grammar_complexity.sql` — new lookup tables + new nullable columns (Option B)
6. Update `app/pipeline/upsert.py` — write new fields to DB on approval
7. Update `app/pipeline/embeddings.py` — include prose grammar profile in `taxonomy_summary` and `generation_profile` embedding text
8. Tests — validation, upsert, embedding text construction

---

### Writing Style and Complexity Profiling

> **STATUS: IMPLEMENTED in Migration 018** — see Completed table above.

#### Problem

The current ontology captures difficulty at a high level (`difficulty_overall`, `difficulty_reading`, `difficulty_vocab`) and has free-form fields for style (`style_traits_jsonb`, `text_register`, `tone`), but it does not model writing style and complexity with enough structure to:

- **Target generation** at a specific syntactic or lexical level (e.g. "generate a passage with heavy subordination and academic vocabulary")
- **Query by style** (e.g. "find all questions where the passage uses hedged claims and compound-complex sentences")
- **Compare passages** across complexity dimensions for curriculum sequencing

`target_sentence_complexity` in `question_generation_profiles` is a single free-text field with no controlled vocabulary — it cannot be queried, aggregated, or used reliably in generation prompts.

---

#### What Is Missing

| Dimension | Current State | Gap |
|-----------|--------------|-----|
| Sentence complexity | `target_sentence_complexity` (free text) | No controlled vocabulary; not queryable |
| Lexical tier | `difficulty_vocab` (single difficulty rating) | No distinction between academic, domain-specific, general vocab |
| Rhetorical structure | Not captured | Argument patterns (claim→evidence→concession) invisible |
| Lexical density | Not captured | Cannot distinguish dense academic prose from conversational text |
| Cohesion devices | Not captured | Pronoun chains, lexical repetition, transitional logic not modeled |
| Syntactic variety | Not captured | Mix of sentence types in a passage not recorded |
| Author's craft signals | Not captured | Irony, understatement, hedging, qualification patterns absent |

---

#### Proposed Data Model

New lookup tables:

```sql
CREATE TABLE public.lookup_sentence_complexity (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    sort_order   int NOT NULL DEFAULT 0
);
-- Seeds: simple | compound | complex | compound_complex | heavily_embedded

CREATE TABLE public.lookup_lexical_tier (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    sort_order   int NOT NULL DEFAULT 0
);
-- Seeds: general | academic | domain_specific | mixed

CREATE TABLE public.lookup_rhetorical_structure (
    key          text PRIMARY KEY,
    display_name text NOT NULL,
    sort_order   int NOT NULL DEFAULT 0
);
-- Seeds: claim_evidence | problem_solution | compare_contrast |
--        narrative_sequence | definition_expansion | concession_rebuttal
```

New columns on `question_classifications`:

```sql
ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    sentence_complexity_key  text REFERENCES public.lookup_sentence_complexity(key);

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    lexical_tier_key         text REFERENCES public.lookup_lexical_tier(key);

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    rhetorical_structure_key text REFERENCES public.lookup_rhetorical_structure(key);

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    lexical_density          text CHECK (lexical_density IN ('low', 'medium', 'high'));

ALTER TABLE public.question_classifications ADD COLUMN IF NOT EXISTS
    style_profile_jsonb      jsonb;
-- Structured keys: hedging, subordination_depth, sentence_variety,
--                  cohesion_type, craft_signals[]
```

Updated `question_generation_profiles`:

```sql
ALTER TABLE public.question_generation_profiles ADD COLUMN IF NOT EXISTS
    target_sentence_complexity_key text REFERENCES public.lookup_sentence_complexity(key);

ALTER TABLE public.question_generation_profiles ADD COLUMN IF NOT EXISTS
    target_lexical_tier_key        text REFERENCES public.lookup_lexical_tier(key);
```

---

#### Pass 2 Prompt Update

```json
"style_profile": {
  "sentence_complexity_key": "compound_complex",
  "lexical_tier_key": "academic",
  "rhetorical_structure_key": "claim_evidence",
  "lexical_density": "high",
  "hedging": true,
  "subordination_depth": "deep",
  "craft_signals": ["concession", "qualification"]
}
```

---

#### Safeguards

| Risk | Safeguard |
|------|-----------|
| LLM over-classifies complexity | Use ontology validation — keys must be in lookup tables |
| Style profile adds noise to embedding | Style profile fields are supplementary; embedding quality degrades gracefully |
| Backward compatibility | All new columns are nullable — existing rows unaffected |

---

#### Implementation Order

1. `migrations/017_style_complexity.sql` — new lookup tables + new columns (nullable, idempotent)
2. Seed lookup values for sentence_complexity, lexical_tier, rhetorical_structure
3. Update `app/models/annotation.py` — add `style_profile` to `ClassificationAnnotation`
4. Update `app/prompts/pass2_annotation.py` — add style profile instructions
5. Update `app/pipeline/validator.py` — validate new key fields against lookup tables
6. Update `app/pipeline/embeddings.py` — include style profile in `taxonomy_summary` embedding text
7. Tests — style profile validation, embedding text construction with style fields

---

### Ontology Evolution via Approval Workflow

#### Problem

The current ontology is **closed** — the 12 lookup tables are seeded once and the LLM must use only existing keys. If the LLM proposes a new key (e.g., a new `question_family_key` value it believes is needed), it gets flagged as a validation error and the job goes to `draft` status. The new concept is silently discarded.

As ingestion scales to new question types and practice tests, the ontology will need to grow. But unreviewed additions could corrupt the taxonomy. The fix: **capture proposed new keys, hold them pending, and add them to the lookup tables only after human approval.**

---

#### Proposed Workflow

```
LLM produces unknown key
        │
        ▼
Captured as ontology_proposal (status: pending)
        │
        ▼
Dashboard shows proposal with context
  ─ what key was proposed
  ─ which lookup table it belongs to
  ─ which question/job triggered it
  ─ how many times it has been proposed
        │
   ┌────┴────┐
   ▼         ▼
Approve    Reject
   │         │
   ▼         ▼
INSERT    mark rejected,
into      future instances
lookup    ignored silently
table
   │
   ▼
Ontology cache refreshed
(new key available for future ingestion)
```

---

#### Data Model

New table: `ontology_proposals`

```sql
CREATE TABLE public.ontology_proposals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lookup_table    text NOT NULL,          -- e.g. 'lookup_question_family'
    proposed_key    text NOT NULL,          -- e.g. 'paired_passage_synthesis'
    proposed_label  text,                   -- human-readable label (optional, LLM-suggested)
    description     text,                   -- LLM's rationale for why this key is needed
    source_job_id   uuid REFERENCES public.question_ingestion_jobs(id),
    proposal_count  int NOT NULL DEFAULT 1, -- how many jobs have proposed this same key
    status          text NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    review_notes    text,
    reviewed_by     text,                   -- future: user identity
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (lookup_table, proposed_key)     -- deduplicate across jobs
);
```

**Key design decision:** `UNIQUE (lookup_table, proposed_key)` — if 10 different jobs propose the same new key, it appears as one proposal with `proposal_count = 10`. High count = stronger signal that the key is genuinely needed.

---

#### Backend Changes

1. **Validator update** — when `is_valid_key()` returns False, upsert an `ontology_proposal` row (increment `proposal_count` if it already exists)
2. **Pass 2 prompt update** — add optional field `proposed_new_keys: list[{field, key, rationale}]`
3. **New API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ontology/proposals` | List proposals with `?status=pending\|approved\|rejected` filter |
| `GET` | `/ontology/proposals/{id}` | Single proposal with full context |
| `PATCH` | `/ontology/proposals/{id}/status` | Approve or reject with review notes |
| `GET` | `/ontology/proposals/stats` | Count by table, status — for dashboard summary |

4. **Approve action** — INSERT into lookup table → UPDATE proposal status → refresh `app.state.ontology`
5. **`POST /ontology/reload`** — force full reload of cached ontology from DB

---

#### Dashboard Design

Three views:

**View 1 — Proposal Queue** — pending proposals sorted by `proposal_count DESC`

```
┌─────────────────────────────────────────────────────────────────┐
│  ONTOLOGY PROPOSALS                          [Pending: 7]       │
├──────────────────┬──────────────────┬───────┬───────────────────┤
│ Lookup Table     │ Proposed Key     │ Count │ Actions           │
├──────────────────┼──────────────────┼───────┼───────────────────┤
│ question_family  │ paired_synthesis │  12   │ [Approve] [Reject]│
│ solver_pattern   │ back_solve       │   5   │ [Approve] [Reject]│
│ distractor_type  │ register_mismatch│   3   │ [Approve] [Reject]│
│ evidence_scope   │ cross_paragraph  │   1   │ [Approve] [Reject]│
└──────────────────┴──────────────────┴───────┴───────────────────┘
```

**View 2 — Proposal Detail** — full context, editable label, review notes, approve/reject

**View 3 — Ontology Browser** — read-only view of all 12 lookup tables with a search box to catch near-duplicates before approving

---

#### Safeguards

| Risk | Safeguard |
|------|-----------|
| LLM invents nonsense keys | `proposal_count` threshold — only surface proposals seen in ≥2 jobs by default |
| Near-duplicate keys pollute ontology | Ontology Browser search in dashboard; reviewer must check before approving |
| Approved key breaks existing jobs | Approval only *adds* to lookup tables — never renames or removes |
| Cache goes stale after approval | `/ontology/reload` endpoint + auto-reload on approval |
| Accidental bulk approve | Require `review_notes` to be non-empty for approval |

---

#### Implementation Order

1. `migrations/015_ontology_proposals.sql` — add the proposals table
2. Update `app/pipeline/validator.py` — upsert proposal on unknown key
3. `app/routers/ontology.py` — add proposal endpoints
4. `app/main.py` — add `/ontology/reload` and wire proposals
5. Dashboard UI — simple server-rendered HTML or Streamlit app
6. Tests — proposal creation, approve/reject flow, cache refresh

---

## Backend

### Image, Chart, and Graph Storage with Embedding Relationships

#### Problem

The current embeddings pipeline (`text-embedding-3-small`) is text-only. SAT questions — particularly data interpretation questions and Math modules — frequently include charts, graphs, tables, and diagrams. These visuals are invisible to the current embedding and search system: they cannot be indexed, searched, or related to their question's semantic content.

Additionally, `pytesseract` (the current image parser) performs poorly on structured visual content — it extracts raw characters but loses all meaning from charts and graphs.

#### Approach: Describe → Store → Embed

Rather than switching to a multimodal embedding model (complex, weaker on text), the recommended approach is:

1. **Store the image** in Supabase Storage (S3-compatible object store)
2. **Describe the image** using a vision model (`deepseek-ocr` locally, or GPT-4V/Claude for higher quality)
3. **Include the description** in the question's embedding text so it's fully searchable
4. **Link image → question** via a `question_images` table

This keeps the existing `text-embedding-3-small` pipeline intact and makes visual content searchable through natural language.

---

#### Data Model

New table: `question_images`

```sql
CREATE TABLE public.question_images (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     uuid NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    storage_path    text NOT NULL,       -- Supabase Storage bucket path
    public_url      text,                -- signed or public URL for retrieval
    image_type      text,                -- 'chart', 'graph', 'diagram', 'table', 'photo'
    alt_description text,                -- vision-model-generated description
    sort_order      int NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON public.question_images (question_id);
```

Supabase Storage bucket: `question-images`
Path convention: `{exam_code}/{module_code}/q{question_number}/{uuid}.png`

---

#### Embedding text construction (updated)

```
{stem}

{passage}

Answer choices: A) ... B) ... C) ... D) ...

Visual content: {alt_description from question_images, joined if multiple}
```

---

#### Vision model for description generation

| Model | Quality | Speed | Cost | Best for |
|-------|---------|-------|------|----------|
| `deepseek-ocr` (Ollama, local) | Good | Fast | Free | Charts, tables, structured text |
| GPT-4V / Claude (API) | Excellent | Slower | Per-token | Complex diagrams, ambiguous visuals |

**Recommended:** Use `deepseek-ocr` locally as default; allow override to API model for high-stakes descriptions.

---

#### Safeguards

| Risk | Safeguard |
|------|-----------|
| Vision model hallucination on image description | Store raw image; description is supplementary, not authoritative |
| Storage costs at scale | Images are typically small (PNG screenshots); Supabase Storage free tier covers thousands |
| Description quality degrades search | Description is additive — if absent, text embedding still works |
| Broken image URLs | Store `storage_path` as primary key; regenerate signed URLs on demand |

---

#### Implementation Order

1. `migrations/016_question_images.sql` — add `question_images` table + storage bucket
2. Extend `app/parsers/image_parser.py` — `deepseek-ocr` description generation
3. Update `app/pipeline/ingest.py` — image upload + `question_images` insert
4. Update `app/pipeline/embeddings.py` — include `alt_description` in embedding text
5. Update `app/routers/questions.py` — return images in question detail response
6. Tests — image upload, description generation, embedding text construction
