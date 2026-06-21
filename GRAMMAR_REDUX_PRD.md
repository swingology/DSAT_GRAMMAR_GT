# GRAMMAR_REDUX_PRD.md
# Grammar Practice — Sentence Span Annotation & DB Restructure

**Status:** Planned  
**Version:** 1.0 — 2026-06-21  
**Author:** CB-17  
**References:** `future_features.md §Grammar Practice`, `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10`

---

## 1. Problem Statement

The grammar practice UI shows key pills (Sentence Anatomy and Grammar Concepts) that
students can click to highlight relevant parts of the passage. Today this does not work
reliably:

- Most grammar questions have **no span data in the DB at all**. The backend constructs
  `passage_tokens` on the fly at query time by tagging the **entire passage** as one block
  with the question's grammar focus key. Clicking any key lights up the whole passage.
- The local frontend tokenizer (`sentenceTokenizer.ts`) is heuristic-only — it finds
  prepositional phrases, clause boundaries, and blanks by rule, but cannot identify
  subjects precisely or detect modifier placements, appositives, or parallel elements
  without real parse data.
- The taxonomy conflates two distinct things in a single flat `tags` array: **structural
  elements** (what a span IS — subject, prepositional phrase) and **grammar concepts**
  (why a span MATTERS — subject-verb agreement distractor, nearest-noun attraction).

The result: the key pills panel either shows nothing or highlights the entire passage,
giving students no useful visual anatomy of the sentence they are being tested on.

---

## 2. Goals

1. **Word-level span annotation stored in DB** for all official practice questions.
2. **Two distinct tag arrays per token** — `anatomy` (structure) and `concept_tags`
   (grammar rule) — so clicking "Prepositional Phrase" and clicking "Subject-Verb
   Agreement" can highlight the same span for two different reasons.
3. **A human-readable label** per question describing the structural pattern at a glance,
   without parsing the token array.
4. **Independent update cadence** — span data can be regenerated or improved without
   re-running the full grammar taxonomy annotation.
5. **No breaking changes** to the existing frontend or API — the new data slots into the
   existing priority chain.
6. **Correct blank-slot anatomy** — the blank is tagged as `transition_word`,
   `pronoun`, `punctuation_mark`, or `main_verb` based on what the tested word
   actually is, not hardcoded as a verb for every question.

### Non-goals

- Rewriting the existing Pass 1 (OCR) or Pass 2 (grammar taxonomy annotation) pipelines.
- Changing the `annotation_jsonb` schema used by Pass 2.
- Modifying the grammar rules taxonomy (D.1–D.9) — D.10 is additive only.
- Generated questions (for now) — backfill targets `content_origin = 'official'` only.

---

## 3. Current Architecture

```
PDF
 └─ Pass 1 (OCR / extraction)
     └─ questions table  ←  current_passage_text, current_question_text, current_underlined_text
         └─ Pass 2 (grammar annotation)
             └─ question_annotations.annotation_jsonb
                 ├─ grammar_role_key, grammar_focus_key, syntactic_trap_key
                 ├─ options[].distractor_type_key, why_wrong, why_plausible
                 └─ passage_tokens  ← KEY MISSING for most rows
```

**`passage_tokens` today (computed on-the-fly in `_fallback_passage_tokens`):**

```
1. Check annotation_jsonb["passage_tokens"]  → usually absent
2. Try to find current_underlined_text span in passage  → often absent
3. Fallback: return [{"text": <whole passage>, "tags": [grammar_role_key, grammar_focus_key, syntactic_trap_key]}]
```

Result: one blob, whole passage tagged → everything highlights when any key is active.

---

## 4. Target Architecture

```
PDF
 └─ Pass 1 (OCR)  [unchanged]
     └─ questions table  [unchanged]
         └─ Pass 2 (grammar annotation)  [unchanged]
             └─ question_annotations.annotation_jsonb  [unchanged]
                 └─ Pass 3 (span annotation)  ← NEW
                     └─ question_annotations.passage_spans  ← NEW COLUMN
                         ├─ label            (string)
                         ├─ anatomy_present  (string[])
                         ├─ concepts_present (string[])
                         └─ tokens[]
                             ├─ text
                             ├─ anatomy[]
                             ├─ concept_tags[]
                             └─ is_blank
```

---

## 5. DB Schema Changes

### 5.1 New column on `question_annotations`

```sql
ALTER TABLE question_annotations
  ADD COLUMN passage_spans   JSONB    NULL,
  ADD COLUMN span_annotated_at TIMESTAMPTZ NULL,
  ADD COLUMN span_model_name   VARCHAR(100) NULL;
```

`passage_spans` is nullable — absence means "not yet span-annotated; fall back to
existing behaviour." `span_annotated_at` enables incremental backfill queries.
`span_model_name` records which LLM produced the spans (for quality tracking and re-runs).

### 5.2 GIN index for analytics

```sql
CREATE INDEX ix_qa_passage_spans_gin
  ON question_annotations USING GIN (passage_spans);
```

Enables fast queries like:
- "All questions with a `subject` span" → `passage_spans @> '{"anatomy_present":["subject"]}'`
- "All questions with `nearest_noun_attraction` concept" → `passage_spans @> '{"concepts_present":["nearest_noun_attraction"]}'`

### 5.3 `span_review_queue` table

Holds Pass 3 failures for manual triage, same pattern as existing `needs_review` job status.

```sql
CREATE TABLE span_review_queue (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id   UUID NOT NULL REFERENCES questions(id),
  error_type    VARCHAR(80) NOT NULL,   -- 'concat_mismatch' | 'invalid_anatomy' | 'invalid_concept' | 'missing_primary_concept'
  error_detail  TEXT,
  raw_llm_output JSONB,
  created_at    TIMESTAMPTZ DEFAULT now(),
  resolved_at   TIMESTAMPTZ
);
```

### 5.4 Migration file

`backend/migrations/versions/033_passage_spans.py`

---

## 6. `passage_spans` JSON Structure

```jsonc
{
  // Human-readable label — auto-generated, stored, queryable.
  // Format: "{primary_concept}: {key anatomy elements present}"
  "label": "SVA: subject + PP distractor + verb blank",

  // Deduplicated union of all anatomy[] values across tokens.
  // Drives the "Sentence Anatomy" key pills panel on load.
  "anatomy_present": ["subject", "prepositional_phrase", "main_verb"],

  // Deduplicated union of all concept_tags[] values across tokens.
  // Drives the "Grammar Concepts" key pills panel on load.
  "concepts_present": ["subject_verb_agreement", "nearest_noun_attraction", "verb_form"],

  // Which questions-table column was used as the tokenization input.
  // "current_passage_text" for passage questions; "current_question_text" for pure-stem.
  // Used by the validator and triage scripts to compare against the correct source string.
  "passage_text_source": "current_passage_text",

  // Word-level token array.
  // INVARIANT: "".join(t["text"] for t in tokens) == the field named by passage_text_source exactly.
  "tokens": [
    {
      "text":         "The number",
      "anatomy":      ["subject"],
      "concept_tags": [],
      "is_blank":     false
    },
    {
      "text":         " ",
      "anatomy":      [],
      "concept_tags": [],
      "is_blank":     false
    },
    {
      "text":         "of students",
      "anatomy":      ["prepositional_phrase"],
      "concept_tags": ["subject_verb_agreement", "nearest_noun_attraction"],
      "is_blank":     false
    },
    {
      "text":         " in the class",
      "anatomy":      ["prepositional_phrase"],
      "concept_tags": ["subject_verb_agreement"],
      "is_blank":     false
    },
    {
      "text":         " ",
      "anatomy":      [],
      "concept_tags": [],
      "is_blank":     false
    },
    {
      "text":         "_______",
      "anatomy":      ["main_verb"],
      "concept_tags": ["verb_form"],
      "is_blank":     true
    }
  ]
}
```

**Token rules:**
- Whitespace tokens (`" "`) are required to preserve concatenation invariant.
- A token may carry both `anatomy` and `concept_tags` simultaneously — same span, two reasons.
- `is_blank: true` tokens must have at least one `anatomy` entry (from the blank-slot mapping, §D.10.8).
- Empty arrays `[]` are preferred over omitting the field.

---

## 7. Approved Key Vocabularies

### 7.1 `anatomy` approved values

Full reference: `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10`

**Core clause/predicate:** `independent_clause`, `subject`, `predicate`, `main_verb`,
`verb_phrase`, `object`, `complement`

**Subordinate clauses:** `subordinate_clause`, `adverbial_clause`, `relative_clause`,
`restrictive_clause`, `nonrestrictive_clause`, `noun_clause`

**Phrases:** `prepositional_phrase`, `participial_phrase`, `infinitive_phrase`,
`gerund_phrase`, `absolute_phrase`, `adverbial_phrase`, `noun_phrase`

**Modifiers:** `modifier`, `appositive`, `nonrestrictive_element`

**Position/punctuation structures:** `introductory_element`, `parenthetical`,
`series_item`

**Conjunctions/connectors:** `subordinating_conj`, `coordinating_conjunction`,
`correlative_conjunction`, `conjunctive_adverb`, `transition_word`

**Pronouns/reference:** `pronoun`, `antecedent`

**Blank-slot only:** `determiner`, `punctuation_mark`

### 7.2 `concept_tags` approved values

Full reference: `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.2` and `§D.5`

Includes all D.2 Grammar Focus Keys (e.g. `subject_verb_agreement`,
`verb_tense_consistency`, `transition_logic`, `pronoun_antecedent_agreement`, …)
and all D.5 Syntactic Trap Keys (e.g. `nearest_noun_attraction`, `garden_path`,
`interruption_breaks_subject_verb`, …).

See rules file for the full enumerated lists. No invented keys permitted.

### 7.3 Blank-slot anatomy mapping

| `grammar_focus_key` group | Blank `anatomy` tag(s) |
|---|---|
| `verb_tense_consistency`, `verb_form`, `subject_verb_agreement`, `voice_active_passive` | `main_verb`, `verb_form`, `verb_tense_consistency` |
| `transition_logic`, `conjunctive_adverb_usage`, `logical_relationships` | `transition_word`, `conjunctive_adverb` |
| `pronoun_antecedent_agreement`, `pronoun_case`, `pronoun_clarity` | `pronoun` |
| `determiners_articles`, `noun_countability` | `determiner` |
| `punctuation_comma`, `semicolon_use`, `colon_dash_use`, `apostrophe_use`, `appositive_punctuation` | `punctuation_mark` |
| default | `main_verb`, `verb_form`, `verb_tense_consistency` |

Any new `grammar_focus_key` added to D.2 must be assigned here before Pass 3 can annotate
questions using that key.

---

## 8. Pass 3 — Span Annotation Pipeline

### 8.1 Trigger conditions

Pass 3 runs after Pass 2 completes and is independent of it. It can also be triggered:
- On demand for a single question via admin endpoint `POST /admin/questions/{id}/annotate-spans`
- In batch via `scripts/reannotate_spans.py` for backfill
- Automatically when Pass 2 completes a new ingestion job (optional, queue-based)

### 8.2 Inputs

```python
{
    "question_id":          uuid,
    "current_passage_text": str,          # from questions table
    "grammar_focus_key":    str | None,   # from annotation_jsonb
    "grammar_role_key":     str | None,
    "syntactic_trap_key":   str | None,
    "secondary_grammar_focus_keys": list[str],
}
```

### 8.3 LLM prompt structure

**System context:**
- Inject §D.10 (anatomy key vocabulary) and the D.5 syntactic trap keys as the
  allowed vocabulary. The agent must not invent keys outside these lists.
- Instruct the agent to return a JSON array of tokens where concatenation exactly
  reconstructs the input passage text.
- Include the blank-slot mapping table (§7.3 above) so the agent tags blanks correctly.
- Provide 3–5 annotated examples covering different grammar_focus_key types.

**User message:**
```
Passage text: "{current_passage_text}"
grammar_focus_key: "{grammar_focus_key}"
grammar_role_key:  "{grammar_role_key}"
syntactic_trap_key: "{syntactic_trap_key}"

Tokenize the passage into word-level spans. For each span output:
  text, anatomy[], concept_tags[], is_blank.
Return a JSON array only.
```

**Recommended model:** claude-sonnet-4-6 (fast, accurate for structured output).
Fall back to claude-haiku-4-5 for high-volume backfill if cost is a concern.

### 8.4 Validation — all must pass before writing to DB

| Check | Rule | Failure type |
|---|---|---|
| Concatenation invariant | `"".join(t["text"] for t in tokens) == current_passage_text` | `concat_mismatch` |
| Anatomy vocabulary | Every `anatomy` value is in the approved list (§7.1) | `invalid_anatomy` |
| Concept vocabulary | Every `concept_tags` value is in the approved list (§7.2) | `invalid_concept` |
| Primary concept present | `grammar_focus_key` appears in at least one token's `concept_tags` | `missing_primary_concept` |
| Blank tagged | At least one token with `is_blank: true` exists if `_______` is in the passage | `missing_blank_token` |
| Blank anatomy correct | Blank token's `anatomy` matches the mapping in §7.3 | `wrong_blank_anatomy` |

On any failure: log to `span_review_queue` with `raw_llm_output`; do not write
`passage_spans`; question continues to use existing fallback chain.

### 8.5 Label generation (rule-based, post-validation)

```python
def generate_label(grammar_focus_key, anatomy_present, concepts_present):
    # Primary concept label prefix
    prefix_map = {
        "subject_verb_agreement":       "SVA",
        "verb_tense_consistency":       "Verb tense",
        "transition_logic":             "Transition logic",
        "pronoun_antecedent_agreement": "Pronoun agreement",
        "modifier_placement":           "Modifier placement",
        "punctuation_comma":            "Comma mechanics",
        "semicolon_use":                "Semicolon use",
        "parallel_structure":           "Parallel structure",
        "apostrophe_use":               "Apostrophe use",
        # ... full map from D.2 keys
    }
    prefix = prefix_map.get(grammar_focus_key, grammar_focus_key.replace("_", " ").title())

    # Anatomy suffix — list the key structural elements present
    anatomy_labels = {
        "subject":             "subject",
        "prepositional_phrase":"PP distractor",
        "participial_phrase":  "participial phrase",
        "introductory_element":"introductory element",
        "parenthetical":       "parenthetical",
        "appositive":          "appositive",
        "main_verb":           "verb blank",
        "transition_word":     "transition blank",
        "pronoun":             "pronoun blank",
        "series_item":         "parallel items",
    }
    suffix_parts = [anatomy_labels[k] for k in anatomy_present if k in anatomy_labels]
    suffix = " + ".join(suffix_parts[:4])  # cap at 4 elements for readability

    # Trap annotation
    trap_note = ""
    for trap in ["nearest_noun_attraction", "interruption_breaks_subject_verb",
                 "garden_path", "long_distance_dependency"]:
        if trap in concepts_present:
            trap_note = f" [{trap.replace('_', ' ')}]"
            break

    return f"{prefix}: {suffix}{trap_note}" if suffix else prefix
```

Example outputs:
- `"SVA: subject + PP distractor + verb blank [nearest noun attraction]"`
- `"Verb tense: scientific present, verb blank"`
- `"Transition logic: transition blank"`
- `"Pronoun agreement: antecedent + pronoun blank"`
- `"Comma mechanics: introductory element + parenthetical"`

### 8.6 Write path

```python
annotation.passage_spans = {
    "label":               label,
    "anatomy_present":     sorted(set(anatomy_present)),
    "concepts_present":    sorted(set(concepts_present)),
    "tokens":              validated_tokens,
    "passage_text_source": passage_text_source,  # "current_passage_text" | "current_question_text"
}
annotation.span_annotated_at = datetime.utcnow()
annotation.span_model_name   = model_name_used
db.commit()
```

---

## 9. Backfill Strategy

### 9.1 Script: `scripts/reannotate_spans.py`

```bash
# Backfill all official questions with no span annotation yet
python scripts/reannotate_spans.py --status missing

# Re-run all official questions (upgrade quality)
python scripts/reannotate_spans.py --status all --content-origin official

# Single question
python scripts/reannotate_spans.py --question-id <uuid>

# Dry-run — validate only, don't write
python scripts/reannotate_spans.py --status missing --dry-run
```

**Priority order for backfill:**
1. Questions in active practice rotation (`practice_status = 'active'`)
2. Questions with high `syntactic_trap_intensity` (most pedagogically valuable)
3. Remaining official questions

### 9.2 Span review queue triage

`scripts/review_span_queue.py` — prints all unresolved failures grouped by `error_type`,
with the raw LLM output. Manual fix paths:
- `concat_mismatch` → re-run with stricter prompt; or hand-edit tokens and mark resolved
- `invalid_anatomy` / `invalid_concept` → check if a key amendment to D.10 is needed
- `missing_primary_concept` → check if `grammar_focus_key` is present in annotation

### 9.3 Re-annotation without regression

Because `passage_spans` is a separate column, re-running Pass 3 never touches
`annotation_jsonb`. The grammar taxonomy annotation is always preserved.

---

## 10. Frontend Read Path

### 10.1 Priority chain (updated)

```
0. passage_spans.tokens                     ← TARGET: word-level, anatomy + concept_tags
1. annotation_jsonb["passage_tokens"]       ← existing: chunk-level, flat tags
2. _fallback_passage_tokens() on-the-fly    ← existing: whole-passage fallback
3. Local structural tokenizer               ← graceful degradation, always available
```

### 10.2 Backend change — `_fallback_passage_tokens`

Add step 0 before the existing logic:

```python
def _fallback_passage_tokens(question, ann_data, annotation=None):
    # Step 0: prefer stored passage_spans (new)
    if annotation is not None and annotation.passage_spans:
        spans = annotation.passage_spans
        tokens = spans.get("tokens", [])
        if tokens:
            # Merge anatomy + concept_tags into a flat tags list for
            # backward compat with the frontend's findActiveKeyForToken
            result = []
            for t in tokens:
                merged_tags = list(t.get("anatomy", [])) + list(t.get("concept_tags", []))
                result.append({
                    "text":     t["text"],
                    "tags":     merged_tags,
                    "anatomy":  t.get("anatomy", []),
                    "concept_tags": t.get("concept_tags", []),
                    "is_blank": t.get("is_blank", False),
                })
            return result

    # Steps 1–3: existing logic unchanged
    ...
```

The `annotation` object (SQLAlchemy `QuestionAnnotation`) must be passed into
`_fallback_passage_tokens` at call sites in `student.py` (lines 472 and 1221).

### 10.3 API payload change — `StudentQuestionResponse`

Add two new optional fields to `payload.py`:

```python
class StudentQuestionResponse(BaseModel):
    ...
    passage_tokens: Optional[List[dict]] = None        # existing (flat tags, backward compat)
    passage_spans:  Optional[dict]       = None        # new: full label + anatomy_present + concepts_present
```

Populate `passage_spans` from `annotation.passage_spans` when present (omit the
`tokens` array from the API response — it is already surfaced via `passage_tokens`).
The frontend uses `passage_spans.label`, `anatomy_present`, and `concepts_present`
for the pill panel; `passage_tokens` for word-level highlighting.

### 10.4 Frontend hook change — `useGrammarSession.ts`

```typescript
// Existing: derive passageKeyIds from flat passage_tokens tags
const passageKeyIds = useMemo(() => {
  const ids = new Set<string>()
  passageTokens.forEach(token => token.tags.forEach(tag => ids.add(tag)))
  return ids
}, [passageTokens])
```

When `passage_spans` is present, `anatomy_present` and `concepts_present` are already
deduplicated — prefer those over scanning the tokens:

```typescript
const passageKeyIds = useMemo(() => {
  const q = state.question as any
  const spans = q?.passage_spans
  if (spans) {
    return new Set([
      ...(spans.anatomy_present   ?? []),
      ...(spans.concepts_present  ?? []),
    ])
  }
  // Fallback: derive from flat passage_tokens tags
  const ids = new Set<string>()
  passageTokens.forEach(token => token.tags.forEach(tag => ids.add(tag)))
  return ids
}, [state.question, passageTokens])
```

---

## 11. Grammar Key Pill Color System

Both anatomy and concept key pills must have unique, non-repeating hues. The lightness
tier signals which category the pill belongs to.

### 11.1 Color tiers

| Category | Border / text | Background |
|---|---|---|
| Sentence Anatomy | `hsl(H, 50%, 32%)` | `hsl(H, 40%, 93%)` |
| Grammar Concepts | `hsl(H, 70%, 26%)` | `hsl(H, 65%, 89%)` |

Anatomy pills read softer/structural. Concept pills read richer/active.

### 11.2 Hue allocation

- **Anatomy keys (≈20):** hues 10°–178°, step ≈ 8°, warm-to-cool arc
- **Concept keys (≈60):** hues 182°–355°, step ≈ 3°, cool-to-warm arc

The two arcs keep anatomy and concept hues on opposite halves of the wheel.
The same nearby hue but different lightness tier distinguishes a warm anatomy pill
from a warm concept pill.

### 11.3 `assignKeyColor(id, category)` utility

Deterministic: hash the key's string ID (djb2 or similar) → map into the
category's hue arc. Same key always gets the same hue regardless of list position.
No `Math.random()`.

```typescript
function assignKeyColor(id: string, category: 'anatomy' | 'concept'): { color: string, lightBg: string } {
  const hash = djb2(id)
  const hue = category === 'anatomy'
    ? 10 + (hash % 20) * 8          // 10°–170°, 20 slots
    : 182 + (hash % 60) * 2.88      // 182°–355°, 60 slots
  const [sat, light, bgSat, bgLight] = category === 'anatomy'
    ? [50, 32, 40, 93]
    : [70, 26, 65, 89]
  return {
    color:   `hsl(${hue.toFixed(0)}, ${sat}%, ${light}%)`,
    lightBg: `hsl(${hue.toFixed(0)}, ${bgSat}%, ${bgLight}%)`,
  }
}
```

**Active state:** invert — use `color` as background, white as text. Same rule for
both categories so "active" is unambiguous regardless of lightness tier.

Replace hardcoded `color`/`lightBg` values in `SYNTAX_ANATOMY_KEYS`
(`src/data/syntaxAnatomyKeys.ts`) with `assignKeyColor(id, 'anatomy')` calls.
Update the dynamic backend key generator in `useGrammarSession.ts` to call
`assignKeyColor(id, 'concept')` instead of the current ad-hoc hue formula.

---

## 12. Grammar Key Pills Panel — UI Structure

Two groups side by side (or stacked on narrow screens):

```
┌─ Sentence Anatomy ─────────────────────────────────────────────┐
│  [Subject]  [Prepositional Phrase]  [Main Verb]  [Appositive]  │
│  (muted pastel pills, anatomy hue arc 10°–178°)                │
└────────────────────────────────────────────────────────────────┘
┌─ Grammar Concepts ─────────────────────────────────────────────┐
│  [Subject-Verb Agreement]  [Nearest Noun Attraction]            │
│  (richer, darker pills, concept hue arc 182°–355°)             │
└────────────────────────────────────────────────────────────────┘
```

- All `SYNTAX_ANATOMY_KEYS` always visible in the Sentence Anatomy group (static list).
- Concept key pills only appear when the question has `concepts_present` data (from
  `passage_spans`) or when a key appears in the legacy `passage_tokens` tags.
- Clicking a pill activates it; active state = full-color background, white text.
- Clicking again deactivates. Multiple pills can be active simultaneously.
- "Find Traps" button auto-activates the question's primary `grammar_focus_key` and
  any `syntactic_trap_key` pills, then scrolls to the first highlighted span.

---

## 13. Backward Compatibility

| Scenario | Behaviour |
|---|---|
| `passage_spans` present | Use it; merge `anatomy` + `concept_tags` into flat `tags` for `findActiveKeyForToken` |
| `passage_spans` absent, `annotation_jsonb.passage_tokens` present (old chunk-level) | Use old format; multi-token backend path in `normalizePassageTokens` |
| Both absent, `current_underlined_text` or `evidence_span_text` findable | `_fallback_passage_tokens` span-splits into 2–3 tokens |
| Nothing found | Whole-passage single-token → local tokenizer fallback (current behaviour) |
| Old flat `tags` array (pre-split format) | Treat as `anatomy` for rendering; no concept highlighting |

The local structural tokenizer (`sentenceTokenizer.ts`) remains as the final
graceful degradation path for all cases — it always produces something renderable.

---

## 14. File & Code Map

| What | Where |
|---|---|
| DB model change | `backend/app/models/db.py` — add `passage_spans`, `span_annotated_at`, `span_model_name` to `QuestionAnnotation` |
| Migration | `backend/migrations/versions/033_passage_spans.py` |
| `span_review_queue` table | Same migration file |
| Pass 3 prompt | `backend/app/prompts/span_prompt.py` (new file) |
| Pass 3 runner | `backend/app/services/span_annotator.py` (new file) |
| Admin endpoint | `POST /admin/questions/{id}/annotate-spans` in `backend/app/routers/admin.py` |
| Backfill script | `scripts/reannotate_spans.py` (new file) |
| Review queue script | `scripts/review_span_queue.py` (new file) |
| Backend read path | `backend/app/routers/student.py` — `_fallback_passage_tokens` |
| API payload | `backend/app/models/payload.py` — `StudentQuestionResponse` |
| Frontend tokenizer | `APP/STUDENT_APP_REDUX/src/utils/sentenceTokenizer.ts` — minor update |
| Color utility | `APP/STUDENT_APP_REDUX/src/utils/keyColors.ts` (new file) |
| Anatomy key data | `APP/STUDENT_APP_REDUX/src/data/syntaxAnatomyKeys.ts` — replace hardcoded colors |
| Hook | `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts` — `passageKeyIds` update |
| Taxonomy reference | `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10` |

---

## 15. Success Criteria

| Metric | Target |
|---|---|
| Official questions with `passage_spans` | 100% of `practice_status = 'active'` rows |
| Concatenation invariant pass rate | 100% (hard gate — failures go to review queue) |
| Vocabulary conformance | 100% (no invented keys written to DB) |
| `missing_primary_concept` failures | < 5% (primary focus key appears in at least one token) |
| Span review queue resolution | < 20 unresolved items after initial backfill |
| Frontend: clicking a concept key highlights ≥ 1 span | ≥ 90% of active questions |
| Frontend: no whole-passage highlight on concept key click | 100% |
| Anatomy key pills always visible | 100% (static list, independent of DB data) |

---

## 16. Open Questions

1. **Granularity for punctuation questions** — for `punctuation_comma`, should the comma
   itself be a token? Or the surrounding clause boundary? Current plan: tokenise the
   comma as a `punctuation_mark` span with `concept_tags: ["punctuation_comma"]`.

2. **Multi-sentence passages** — passages with two sentences (e.g. transition logic
   questions) should have the transition blank in the second sentence. Pass 3 must not
   merge both sentences into one token. Add an explicit rule to the prompt.

3. **Generated questions** — initially out of scope, but the same Pass 3 runner can be
   applied to generated questions once the official backfill is stable. Gated on
   reviewing span quality for generated content.

4. **Absolute phrase disambiguation** — the absolute phrase anatomy key overlaps with
   participial phrase in some constructions. Add 2–3 clear examples to the Pass 3 prompt
   to prevent the LLM from guessing the wrong key.

5. **Color system rollout** — replace `SYNTAX_ANATOMY_KEYS` hardcoded colours
   simultaneously with the UI restructure (§12), not before — changing colours mid-session
   would confuse students already familiar with the current colours.
