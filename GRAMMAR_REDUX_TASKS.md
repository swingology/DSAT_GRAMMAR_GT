# GRAMMAR_REDUX_TASKS.md
# Grammar Practice — Span Annotation & DB Restructure — Implementation Task List

**PRD:** `GRAMMAR_REDUX_PRD.md`  
**Rules reference:** `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10`  
**Status:** Not started  
**Last updated:** 2026-06-21

---

## Execution Order

```
Phase 1 — DB Foundation          TASK-001, TASK-002
Phase 2 — Backend Pipeline       TASK-003 → TASK-008   (TASK-003 must precede 004–007)
Phase 3 — Backend Read Path      TASK-009, TASK-010, TASK-011  (after TASK-001)
Phase 4 — Backfill Scripts       TASK-012, TASK-013    (after TASK-007)
Phase 5 — Frontend Color System  TASK-014, TASK-015, TASK-016
Phase 6 — Frontend Hook & Data   TASK-017, TASK-018, TASK-019  (after TASK-011)
Phase 7 — Frontend UI            TASK-020 → TASK-024   (after TASK-017, TASK-014)
Phase 8 — Tests                  TASK-025 → TASK-032   (parallel with phases 2–7)
Phase 9 — Backfill Execution     TASK-033 → TASK-036   (after all above)
```

Critical path: **001 → 002 → 003 → 007 → 009 → 010 → 011 → 017 → 020**

---

## Phase 1 — DB Foundation

---

### TASK-001 — DB migration: passage_spans column + span_review_queue table

**Complexity:** M  
**Depends on:** nothing  
**Files:**
- CREATE: `backend/migrations/versions/033_passage_spans.py`

**Subtasks:**

1. Create the migration file. Use the project's existing Alembic pattern (see any
   existing migration in `backend/migrations/versions/` for the header/import style).

2. In `upgrade()` write:
   ```sql
   ALTER TABLE question_annotations
     ADD COLUMN passage_spans      JSONB         NULL,
     ADD COLUMN span_annotated_at  TIMESTAMPTZ   NULL,
     ADD COLUMN span_model_name    VARCHAR(100)  NULL;

   CREATE INDEX ix_qa_passage_spans_gin
     ON question_annotations USING GIN (passage_spans);

   CREATE TABLE span_review_queue (
     id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
     question_id    UUID         NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
     annotation_id  UUID         NULL REFERENCES question_annotations(id) ON DELETE SET NULL,
     error_type     VARCHAR(80)  NOT NULL,
     error_detail   TEXT,
     raw_llm_output JSONB,
     created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
     resolved_at    TIMESTAMPTZ  NULL,
     resolved_by    VARCHAR(100) NULL,
     resolution_note TEXT        NULL
   );

   CREATE INDEX ix_srq_question_id  ON span_review_queue (question_id);
   CREATE INDEX ix_srq_error_type   ON span_review_queue (error_type);
   CREATE INDEX ix_srq_unresolved   ON span_review_queue (created_at) WHERE resolved_at IS NULL;
   ```

3. In `downgrade()` write the exact reverse:
   ```sql
   DROP TABLE IF EXISTS span_review_queue;
   DROP INDEX IF EXISTS ix_qa_passage_spans_gin;
   ALTER TABLE question_annotations
     DROP COLUMN IF EXISTS span_model_name,
     DROP COLUMN IF EXISTS span_annotated_at,
     DROP COLUMN IF EXISTS passage_spans;
   ```

4. Run `alembic upgrade head` inside the backend container and verify with
   `\d question_annotations` and `\dt span_review_queue`.

**Acceptance criteria:**
- `alembic upgrade head` completes without error
- `alembic downgrade -1` then `alembic upgrade head` also completes cleanly (round-trip)
- `passage_spans`, `span_annotated_at`, `span_model_name` columns exist on `question_annotations`
- `span_review_queue` table exists with all columns and indices
- GIN index `ix_qa_passage_spans_gin` exists on `question_annotations`
- Existing rows have `passage_spans = NULL` (nullable, no data loss)

---

### TASK-002 — SQLAlchemy model: add new fields to QuestionAnnotation

**Complexity:** S  
**Depends on:** TASK-001  
**Files:**
- MODIFY: `backend/app/models/db.py`

**Subtasks:**

1. In `class QuestionAnnotation(Base)` (currently at line 149), add three new columns
   after the existing `confidence_jsonb` column:
   ```python
   passage_spans      = Column(JSONB,           nullable=True)
   span_annotated_at  = Column(DateTime(timezone=True), nullable=True)
   span_model_name    = Column(String(100),     nullable=True)
   ```

2. Add a new SQLAlchemy model for `span_review_queue`:
   ```python
   class SpanReviewQueue(Base):
       __tablename__ = "span_review_queue"

       id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       question_id     = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
       annotation_id   = Column(UUID(as_uuid=True), ForeignKey("question_annotations.id", ondelete="SET NULL"), nullable=True)
       error_type      = Column(String(80), nullable=False)
       error_detail    = Column(Text, nullable=True)
       raw_llm_output  = Column(JSONB, nullable=True)
       created_at      = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
       resolved_at     = Column(DateTime(timezone=True), nullable=True)
       resolved_by     = Column(String(100), nullable=True)
       resolution_note = Column(Text, nullable=True)

       question   = relationship("Question", foreign_keys=[question_id])
       annotation = relationship("QuestionAnnotation", foreign_keys=[annotation_id])
   ```

3. Add `SpanReviewQueue` to the `__all__` export list at the bottom of `db.py`
   (or wherever models are exported from).

4. Verify the app starts cleanly after the change:
   `docker compose restart backend && curl -s http://localhost:8000/docs | grep -c "operationId"`
   — should return a number > 0 with no startup error in `docker compose logs backend`.

**Acceptance criteria:**
- `QuestionAnnotation` has `passage_spans`, `span_annotated_at`, `span_model_name` attributes
- `SpanReviewQueue` model exists and maps to `span_review_queue` table
- Backend starts without SQLAlchemy mapping errors
- `from app.models.db import SpanReviewQueue` works in a Python shell inside the container

---

## Phase 2 — Backend Pipeline

---

### TASK-003 — Vocabulary constants: approved anatomy and concept_tags key sets

**Complexity:** S  
**Depends on:** nothing (pure data, no DB needed)  
**Files:**
- CREATE: `backend/app/services/span_vocab.py`

**Subtasks:**

1. Create `backend/app/services/span_vocab.py`. This module is the single source of
   truth for all approved keys. The validator (TASK-005), prompt builder (TASK-006),
   and label generator (TASK-004) all import from here.

2. Define `ANATOMY_KEYS: frozenset[str]` containing every key from PRD §7.1:
   ```python
   ANATOMY_KEYS: frozenset[str] = frozenset({
       # Core clause / predicate
       "independent_clause", "subject", "predicate", "main_verb",
       "verb_phrase", "object", "complement",
       # Subordinate clause types
       "subordinate_clause", "adverbial_clause", "relative_clause",
       "restrictive_clause", "nonrestrictive_clause", "noun_clause",
       # Phrases
       "prepositional_phrase", "participial_phrase", "infinitive_phrase",
       "gerund_phrase", "absolute_phrase", "adverbial_phrase", "noun_phrase",
       # Modifiers
       "modifier", "appositive", "nonrestrictive_element",
       # Position / punctuation structures
       "introductory_element", "parenthetical", "series_item",
       # Conjunctions / connectors
       "subordinating_conj", "coordinating_conjunction", "correlative_conjunction",
       "conjunctive_adverb", "transition_word",
       # Pronouns / reference
       "pronoun", "antecedent",
       # Blank-slot only
       "determiner", "punctuation_mark",
   })
   ```

3. Define `CONCEPT_KEYS: frozenset[str]` containing every key from D.2 and D.5:
   ```python
   CONCEPT_KEYS: frozenset[str] = frozenset({
       # D.2.1 Sentence boundary
       "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
       # D.2.2 Agreement
       "subject_verb_agreement", "pronoun_antecedent_agreement",
       "noun_countability", "determiners_articles",
       # D.2.3 Pronoun
       "pronoun_case", "pronoun_clarity",
       # D.2.4 Verb form
       "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
       # D.2.5 Modifier
       "modifier_placement", "absolute_phrase", "comparative_structures",
       "illogical_comparison", "adjective_adverb_distinction",
       "logical_predication", "relative_pronouns",
       # D.2.6 Punctuation
       "punctuation_comma", "colon_dash_use", "semicolon_use",
       "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
       "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
       "unnecessary_internal_punctuation", "end_punctuation_question_statement",
       # D.2.7 Parallel structure
       "parallel_structure", "elliptical_constructions", "conjunction_usage",
       # D.2.8 Expression of ideas
       "redundancy_concision", "precision_word_choice", "register_style_consistency",
       "logical_relationships", "emphasis_meaning_shifts", "data_interpretation_claims",
       "transition_logic", "commonly_confused_words", "preposition_idiom",
       # D.5 Syntactic traps
       "nearest_noun_attraction", "garden_path", "early_clause_anchor",
       "nominalization_obscures_subject", "interruption_breaks_subject_verb",
       "long_distance_dependency", "pronoun_ambiguity", "scope_of_negation",
       "modifier_attachment_ambiguity", "presupposition_trap",
       "temporal_sequence_ambiguity",
   })
   ```

4. Define `BLANK_ANATOMY_MAP: dict[str, list[str]]` — the full blank-slot mapping
   from PRD §7.3:
   ```python
   BLANK_ANATOMY_MAP: dict[str, list[str]] = {
       # Verb keys
       "verb_tense_consistency":       ["main_verb", "verb_form", "verb_tense_consistency"],
       "verb_form":                    ["main_verb", "verb_form", "verb_tense_consistency"],
       "subject_verb_agreement":       ["main_verb", "verb_form", "verb_tense_consistency"],
       "voice_active_passive":         ["main_verb", "verb_form", "verb_tense_consistency"],
       # Transition keys
       "transition_logic":             ["transition_word", "conjunctive_adverb"],
       "conjunctive_adverb_usage":     ["transition_word", "conjunctive_adverb"],
       "logical_relationships":        ["transition_word", "conjunctive_adverb"],
       # Pronoun keys
       "pronoun_antecedent_agreement": ["pronoun"],
       "pronoun_case":                 ["pronoun"],
       "pronoun_clarity":              ["pronoun"],
       # Determiner keys
       "determiners_articles":         ["determiner"],
       "noun_countability":            ["determiner"],
       # Punctuation keys
       "punctuation_comma":            ["punctuation_mark"],
       "semicolon_use":                ["punctuation_mark"],
       "colon_dash_use":               ["punctuation_mark"],
       "apostrophe_use":               ["punctuation_mark"],
       "appositive_punctuation":       ["punctuation_mark"],
   }

   BLANK_ANATOMY_DEFAULT: list[str] = ["main_verb", "verb_form", "verb_tense_consistency"]

   def blank_anatomy_for(grammar_focus_key: str | None) -> list[str]:
       return BLANK_ANATOMY_MAP.get(grammar_focus_key or "", BLANK_ANATOMY_DEFAULT)
   ```

**Acceptance criteria:**
- `from app.services.span_vocab import ANATOMY_KEYS, CONCEPT_KEYS, blank_anatomy_for` works
- `len(ANATOMY_KEYS) >= 28` (all keys from PRD §7.1 present)
- `len(CONCEPT_KEYS) >= 49` (all D.2 + D.5 keys present)
- `blank_anatomy_for("transition_logic") == ["transition_word", "conjunctive_adverb"]`
- `blank_anatomy_for("subject_verb_agreement") == ["main_verb", "verb_form", "verb_tense_consistency"]`
- `blank_anatomy_for(None) == ["main_verb", "verb_form", "verb_tense_consistency"]`
- `blank_anatomy_for("unknown_key") == ["main_verb", "verb_form", "verb_tense_consistency"]`

---

### TASK-004 — Label generator

**Complexity:** S  
**Depends on:** TASK-003  
**Files:**
- CREATE: `backend/app/services/span_label.py`

**Subtasks:**

1. Create `backend/app/services/span_label.py`.

2. Implement `generate_span_label(grammar_focus_key, anatomy_present, concepts_present) -> str`
   exactly as specified in PRD §8.5. Include the full `prefix_map` for all D.2 keys —
   don't leave stubs. Every key in `CONCEPT_KEYS` should have a readable prefix:
   ```python
   PREFIX_MAP: dict[str, str] = {
       "subject_verb_agreement":           "SVA",
       "verb_tense_consistency":           "Verb tense",
       "verb_form":                        "Verb form",
       "voice_active_passive":             "Active/passive voice",
       "transition_logic":                 "Transition logic",
       "pronoun_antecedent_agreement":     "Pronoun agreement",
       "pronoun_case":                     "Pronoun case",
       "pronoun_clarity":                  "Pronoun clarity",
       "modifier_placement":               "Modifier placement",
       "absolute_phrase":                  "Absolute phrase",
       "comparative_structures":           "Comparative structure",
       "illogical_comparison":             "Illogical comparison",
       "adjective_adverb_distinction":     "Adjective/adverb",
       "logical_predication":              "Logical predication",
       "relative_pronouns":                "Relative pronoun",
       "punctuation_comma":                "Comma mechanics",
       "semicolon_use":                    "Semicolon",
       "colon_dash_use":                   "Colon/dash",
       "conjunctive_adverb_usage":         "Conjunctive adverb",
       "apostrophe_use":                   "Apostrophe",
       "possessive_contraction":           "Possessive/contraction",
       "appositive_punctuation":           "Appositive punctuation",
       "hyphen_usage":                     "Hyphen",
       "quotation_punctuation":            "Quotation punctuation",
       "unnecessary_internal_punctuation": "Unnecessary punctuation",
       "end_punctuation_question_statement":"End punctuation",
       "parallel_structure":               "Parallel structure",
       "elliptical_constructions":         "Elliptical construction",
       "conjunction_usage":                "Conjunction choice",
       "sentence_fragment":                "Fragment",
       "comma_splice":                     "Comma splice",
       "run_on_sentence":                  "Run-on",
       "sentence_boundary":                "Sentence boundary",
       "noun_countability":                "Countability",
       "determiners_articles":             "Determiner/article",
       "negation":                         "Negation",
       "redundancy_concision":             "Concision",
       "precision_word_choice":            "Word choice",
       "register_style_consistency":       "Register",
       "logical_relationships":            "Logical relationship",
       "emphasis_meaning_shifts":          "Emphasis/meaning",
       "data_interpretation_claims":       "Data claim",
       "commonly_confused_words":          "Confused words",
       "preposition_idiom":                "Preposition idiom",
   }
   ```

3. Implement the anatomy suffix logic (up to 4 elements, PRD §8.5 `anatomy_labels` map).

4. Implement the trap_note annotation for D.5 trap keys in `concepts_present`.

5. Return `prefix` alone when no anatomy elements are found (e.g. transition-logic
   questions where anatomy is just the blank).

6. Write unit tests inline (or in `backend/tests/test_span_label.py`) covering:
   - SVA with PP distractor → `"SVA: subject + PP distractor + verb blank [nearest noun attraction]"`
   - Transition blank → `"Transition logic: transition blank"`
   - Comma mechanics with introductory element + parenthetical → `"Comma mechanics: introductory element + parenthetical"`
   - Unknown focus key → falls back to title-cased key string
   - `anatomy_present = []` → label is just the prefix, no suffix

**Acceptance criteria:**
- `generate_span_label("subject_verb_agreement", ["subject","prepositional_phrase","main_verb"], ["subject_verb_agreement","nearest_noun_attraction"])` returns `"SVA: subject + PP distractor + verb blank [nearest noun attraction]"`
- `generate_span_label("transition_logic", ["transition_word"], ["transition_logic"])` returns `"Transition logic: transition blank"`
- All PREFIX_MAP keys are covered (no fallback for known keys)
- Labels are ≤ 80 characters in all test cases

---

### TASK-005 — Span validator

**Complexity:** M  
**Depends on:** TASK-003  
**Files:**
- CREATE: `backend/app/services/span_validator.py`

**Subtasks:**

1. Create `backend/app/services/span_validator.py`.

2. Define a `SpanValidationError` dataclass:
   ```python
   @dataclass
   class SpanValidationError:
       error_type: str   # matches span_review_queue.error_type values
       error_detail: str
   ```

3. Implement `validate_tokens(tokens, passage_text, grammar_focus_key) -> list[SpanValidationError]`.
   Run all 6 checks from PRD §8.4 in order. Collect ALL errors (don't short-circuit on
   first failure) so the review queue gets the full picture:

   - **concat_mismatch**: `"".join(t["text"] for t in tokens) != passage_text`
     - Detail: show first N chars of expected vs actual
   - **invalid_anatomy**: any `anatomy` value not in `ANATOMY_KEYS`
     - Detail: list the offending values
   - **invalid_concept**: any `concept_tags` value not in `CONCEPT_KEYS`
     - Detail: list the offending values
   - **missing_primary_concept**: `grammar_focus_key` not found in any token's `concept_tags`
     - Only check if `grammar_focus_key` is not None
   - **missing_blank_token**: passage contains `_______` but no token has `is_blank: True`
   - **wrong_blank_anatomy**: blank token's `anatomy` list doesn't match `blank_anatomy_for(grammar_focus_key)`
     - Detail: show expected vs actual

4. Implement `derive_summaries(tokens) -> tuple[list[str], list[str]]`:
   Returns `(anatomy_present, concepts_present)` — deduplicated sorted lists of all
   anatomy and concept_tag values across all tokens.

5. Implement `is_valid(errors: list[SpanValidationError]) -> bool`:
   Returns True iff `len(errors) == 0`.

6. Write tests in `backend/tests/test_span_validator.py` covering each error type
   individually, plus a clean passing case.

**Acceptance criteria:**
- Clean token list for a real SVA question returns no errors
- Concatenation check catches single-character gaps (e.g. missing space token)
- Anatomy check catches `"foobar"` as an invalid key
- Concept check catches `"made_up_concept"` as an invalid key
- Missing blank token detected when `_______` is in passage but `is_blank` absent
- Wrong blank anatomy detected: e.g. `transition_logic` question where blank has `["main_verb"]` anatomy
- Multiple errors collected simultaneously (not short-circuited)

---

### TASK-006 — Pass 3 LLM prompt: span_prompt.py

**Complexity:** L  
**Depends on:** TASK-003  
**Files:**
- CREATE: `backend/app/prompts/span_prompt.py`

**Token efficiency — two-layer caching (mirrors annotate_prompt.py pattern):**
- **Python layer:** `@lru_cache(maxsize=1)` on both static and dynamic prompt builders.
  Prevents string reconstruction on every call within a process.
- **Anthropic layer:** call `provider.complete_cached(system_static, system_dynamic, user)`
  instead of `provider.complete(system, user)`. The `system_static` block is sent with
  `cache_control: ephemeral` so Anthropic caches it server-side for up to 5 minutes.
  During a backfill run processing hundreds of questions in sequence, every call after
  the first reads from the cache (~10% of normal input token cost for the static block).

**Split boundary:**
- `system_static` — vocabulary tables (anatomy keys, concept keys, blank-slot mapping)
  + 5 full annotated examples. This is ~90% of the prompt by tokens and never changes.
- `system_dynamic` — role definition, output format spec, concatenation invariant rule,
  phrase-grouping rule, blank-slot rule. Short, mostly static, but logically "instructions"
  rather than "reference data" — sent fresh each call.

**Subtasks:**

1. Create `backend/app/prompts/span_prompt.py` following the structure of the existing
   `backend/app/prompts/annotate_prompt.py` (two-part cached prompt + user message builder).

2. Write `build_span_prompt_static() -> str` decorated with `@lru_cache(maxsize=1)`.
   This is `system_static` — the heavy reference block sent with `cache_control: ephemeral`.
   Include:

   a. **Blank-slot mapping table** — paste the full table from PRD §7.3 verbatim.

   b. **Anatomy key vocabulary** — paste the full list from `span_vocab.ANATOMY_KEYS`
      with one-line descriptions for each key (drawn from D.10 in the rules file).

   c. **Concept key vocabulary** — paste the full D.2 and D.5 key lists.

   d. **Absolute phrase vs participial phrase disambiguation** (addressing open
      question #4): 2–3 side-by-side examples showing which is which.

   e. **5 full annotated examples** covering:
      - SVA with PP distractor (subject_verb_agreement + nearest_noun_attraction)
      - Verb tense (scientific present)
      - Transition logic (two-sentence passage, blank at sentence start)
      - Pronoun agreement (antecedent + pronoun blank)
      - Comma mechanics with introductory element and appositive

3. Write `build_span_prompt_dynamic() -> str` decorated with `@lru_cache(maxsize=1)`.
   This is `system_dynamic` — the short instructions block sent fresh each call.
   Include:

   a. **Role definition:** "You are a DSAT sentence anatomy annotator. Given a passage
      from an official SAT grammar question and its grammar taxonomy annotation, you
      tokenize the passage into grammatical-unit spans and tag each span with anatomy and
      grammar concept labels."

   b. **Phrase-level grouping rule** (resolves Q5): "Group tokens by grammatical unit,
      not by individual word. A prepositional phrase like 'of students' is ONE token, not
      three. A subject like 'The number' is ONE token. Only split at clause boundaries,
      phrase boundaries, or where the grammar_focus_key requires distinguishing adjacent
      elements. Whitespace between units must be preserved as separate `' '` tokens to
      maintain the concatenation invariant."

   c. **Output format specification:** Return a JSON array only. No prose before or after.
      Each element: `{"text": str, "anatomy": [str], "concept_tags": [str], "is_blank": bool}`.
      Whitespace between units must be separate `' '` tokens.

   d. **Concatenation invariant rule** (stated explicitly): "The concatenation of all
      `text` values must exactly equal the input passage text, character for character.
      Whitespace between units must appear as separate tokens. Do not merge or drop any
      characters."

   e. **Multi-sentence rule** (addressing open question #2): "If the passage contains
      two sentences, annotate each sentence's tokens separately. Never merge both
      sentences into a single token. The transition blank in sentence 2 belongs to
      sentence 2's token sequence."

   f. **Blank slot rule:** "Identify `_______` as a blank token (`is_blank: true`).
      Assign the blank's `anatomy` using the focus_key mapping table in the reference
      block above. Do not tag a blank as `main_verb` if the question tests a transition
      word or pronoun."

   g. **Dual-tagging rule:** "A single span may carry both anatomy and concept tags.
      Example: `'of students'` in an SVA question gets anatomy=['prepositional_phrase']
      AND concept_tags=['subject_verb_agreement', 'nearest_noun_attraction']."

   h. **Punctuation token rule** (addressing open question #1): "For punctuation
      questions, tokenize the comma/semicolon/colon/dash itself as a separate token
      with anatomy=['punctuation_mark'] and the relevant concept_tag."

4. Write `build_span_user_message(passage_text, grammar_focus_key, grammar_role_key, syntactic_trap_key, secondary_keys) -> str`:
   ```
   Passage text: "{passage_text}"
   grammar_focus_key: "{grammar_focus_key}"
   grammar_role_key: "{grammar_role_key}"
   syntactic_trap_key: "{syntactic_trap_key}"
   secondary_grammar_focus_keys: {secondary_keys}

   Tokenize this passage into word-level spans. Return a JSON array only.
   ```

5. Write `parse_llm_span_response(raw: str) -> list[dict]`: strips any markdown
   code fences (`` ```json ``) and calls `json.loads`. Raises `ValueError` on
   parse failure so the caller can log to `span_review_queue`.

**Acceptance criteria:**
- `build_span_prompt_static()` returns a string > 3000 chars; same object returned on every call (lru_cache working)
- `build_span_prompt_dynamic()` returns a string; same object returned on every call (lru_cache working)
- Static block contains all 5 example passages, blank-slot mapping table, and both vocabulary lists
- Dynamic block contains phrase-grouping rule, concatenation invariant rule, and output format spec
- `build_span_user_message(...)` returns a string with the passage text quoted
- `parse_llm_span_response('```json\n[{"text":"The","anatomy":[],"concept_tags":[],"is_blank":false}]\n```')` returns a list with one dict
- `parse_llm_span_response('not json')` raises `ValueError`

---

### TASK-007 — span_annotator.py service

**Complexity:** L  
**Depends on:** TASK-002, TASK-003, TASK-004, TASK-005, TASK-006  
**Files:**
- CREATE: `backend/app/services/span_annotator.py`

**Subtasks:**

1. Create `backend/app/services/span_annotator.py`.

2. Implement `async def annotate_spans(question_id, db, provider=None) -> dict`:
   The main entrypoint. Takes a question UUID, fetches the required data, calls the
   LLM, validates, labels, and writes to DB.

   Full implementation:
   ```python
   async def annotate_spans(question_id: UUID, db: AsyncSession, provider=None) -> dict:
       # 1. Fetch question + its latest annotation
       q = await db.get(Question, question_id)
       if not q:
           raise ValueError(f"Question {question_id} not found")
       if not q.latest_annotation_id:
           raise ValueError(f"Question {question_id} has no annotation — run Pass 2 first")

       ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
       ann_data = ann.annotation_jsonb or {}

       if q.current_passage_text:
           passage_text = q.current_passage_text
           passage_text_source = "current_passage_text"
       elif q.current_question_text:
           passage_text = q.current_question_text
           passage_text_source = "current_question_text"
       else:
           passage_text = ""
           passage_text_source = None
       grammar_focus_key = ann_data.get("grammar_focus_key")
       grammar_role_key  = ann_data.get("grammar_role_key")
       syntactic_trap_key= ann_data.get("syntactic_trap_key")
       secondary_keys    = ann_data.get("secondary_grammar_focus_keys") or []

       if not passage_text:
           raise ValueError(f"Question {question_id} has no passage text")

       # 2. Build prompt and call LLM
       system = build_span_system_prompt()
       user   = build_span_user_message(passage_text, grammar_focus_key,
                                        grammar_role_key, syntactic_trap_key, secondary_keys)

       # Pass 3 always uses Anthropic — concatenation invariant requires reliable JSON output
       if provider is None:
           settings = get_settings()
           provider = AnthropicProvider(
               api_key=settings.anthropic_api_key,
               default_model=settings.span_annotator_model,
           )
       raw = await provider.complete(system=system, user=user, max_tokens=4096)

       # 3. Parse response
       try:
           tokens = parse_llm_span_response(raw)
       except ValueError as e:
           await _log_failure(db, question_id, ann.id, "parse_error", str(e), raw)
           return {"status": "failed", "error_type": "parse_error"}

       # 4. Validate
       errors = validate_tokens(tokens, passage_text, grammar_focus_key)
       if errors:
           for err in errors:
               await _log_failure(db, question_id, ann.id,
                                  err.error_type, err.error_detail,
                                  {"tokens": tokens, "raw": raw})
           return {"status": "failed", "error_types": [e.error_type for e in errors]}

       # 5. Derive summaries + label
       anatomy_present, concepts_present = derive_summaries(tokens)
       label = generate_span_label(grammar_focus_key, anatomy_present, concepts_present)

       # 6. Write to DB
       ann.passage_spans = {
           "label":                label,
           "anatomy_present":      anatomy_present,
           "concepts_present":     concepts_present,
           "tokens":               tokens,
           "passage_text_source":  passage_text_source,
       }
       ann.span_annotated_at = datetime.utcnow()
       ann.span_model_name   = provider.model_name
       await db.commit()

       return {
           "status":           "ok",
           "label":            label,
           "anatomy_present":  anatomy_present,
           "concepts_present": concepts_present,
           "token_count":      len(tokens),
       }
   ```

3. Implement `async def _log_failure(db, question_id, annotation_id, error_type, error_detail, raw)`:
   Inserts a row into `span_review_queue` and commits. Never raises.

4. Handle the case where `passage_text` comes from `current_question_text` when
   `current_passage_text` is None (some single-sentence questions store everything
   in `current_question_text`).

5. Add retry logic: on parse failure, retry once with a stricter prompt note appended
   ("Your previous response was not valid JSON. Return ONLY a JSON array, nothing else.").
   Only log to `span_review_queue` if the retry also fails.

**Acceptance criteria:**
- `annotate_spans(known_question_id, db)` succeeds for a real grammar question in the dev DB
- On success: `ann.passage_spans` is set, `ann.span_annotated_at` is set, `ann.span_model_name` is set
- On validation failure: `span_review_queue` receives a row; `ann.passage_spans` is NOT set
- On parse error: retry fires once before logging to `span_review_queue`
- Concatenation invariant holds for every written `passage_spans`

---

### TASK-008 — Admin endpoint: POST /admin/questions/{id}/annotate-spans

**Complexity:** S  
**Depends on:** TASK-007  
**Files:**
- MODIFY: `backend/app/routers/admin.py`

**Subtasks:**

1. Add endpoint to admin router:
   ```python
   @router.post("/questions/{question_id}/annotate-spans")
   async def trigger_span_annotation(
       question_id: UUID,
       db: AsyncSession = Depends(get_db),
       _: str = Depends(admin_required),
   ):
       result = await annotate_spans(question_id, db)
       if result["status"] == "failed":
           raise HTTPException(status_code=422, detail=result)
       return result
   ```

2. Import `annotate_spans` from `app.services.span_annotator`.

3. Verify the endpoint appears in `/docs` after restart.

4. Test manually via curl:
   ```bash
   curl -s -X POST "http://localhost:8000/admin/questions/<uuid>/annotate-spans" \
     -H "x-api-key: <admin_key>" | python3 -m json.tool
   ```
   — should return `{"status": "ok", "label": "...", ...}`.

**Acceptance criteria:**
- Endpoint returns 200 with label and summary arrays on success
- Endpoint returns 422 with error detail on validation failure
- Endpoint returns 404 if question UUID doesn't exist
- Endpoint requires admin auth (returns 403 without valid key)
- Endpoint visible in `/docs`

---

## Phase 3 — Backend Read Path

---

### TASK-009 — Update `_fallback_passage_tokens` to check passage_spans first

**Complexity:** M  
**Depends on:** TASK-002  
**Files:**
- MODIFY: `backend/app/routers/student.py`

**Subtasks:**

1. Update the function signature to accept the `annotation` ORM object:
   ```python
   def _fallback_passage_tokens(
       question: Question,
       ann_data: dict[str, Any],
       annotation: QuestionAnnotation | None = None,   # NEW
   ) -> list[dict[str, Any]] | None:
   ```

2. Add Step 0 at the top of the function body (before the existing `ann_data.get("passage_tokens")` check):
   ```python
   # Step 0: prefer stored passage_spans — word-level, anatomy + concept_tags
   if annotation is not None and annotation.passage_spans:
       tokens = annotation.passage_spans.get("tokens", [])
       if tokens:
           result = []
           for t in tokens:
               merged_tags = list(t.get("anatomy", [])) + list(t.get("concept_tags", []))
               result.append({
                   "text":         t["text"],
                   "tags":         merged_tags,       # backward compat flat list
                   "anatomy":      t.get("anatomy", []),
                   "concept_tags": t.get("concept_tags", []),
                   "is_blank":     t.get("is_blank", False),
               })
           return result
   ```

3. Leave the rest of the function body unchanged.

4. Update both call sites (currently lines 472 and 1221) to pass `annotation=ann`:
   ```python
   passage_tokens=_fallback_passage_tokens(q, ann_data, annotation=ann),
   ```
   where `ann` is the `QuestionAnnotation` ORM object already fetched at that point
   (check what variable name is used at each call site — it may be `ann` or fetched
   via `ann_map.get(q.latest_annotation_id)`).

**Acceptance criteria:**
- For a question with `passage_spans` set in the DB:
  - `_fallback_passage_tokens` returns tokens from `passage_spans.tokens`
  - Each returned token has `tags` (merged flat list), `anatomy`, `concept_tags`, `is_blank`
- For a question without `passage_spans`: existing behaviour unchanged (still returns chunk-level or on-the-fly tokens)
- Both call sites in `student.py` pass `annotation=ann`
- Existing tests in `test_student_retrieval.py` still pass

---

### TASK-010 — API payload: add passage_spans to StudentQuestionResponse

**Complexity:** S  
**Depends on:** TASK-009  
**Files:**
- MODIFY: `backend/app/models/payload.py`
- MODIFY: `backend/app/routers/student.py`

**Subtasks:**

1. In `payload.py`, add `passage_spans` field to `StudentQuestionResponse`:
   ```python
   class StudentQuestionResponse(BaseModel):
       ...
       passage_tokens: Optional[List[dict]] = None   # existing
       passage_spans:  Optional[dict]       = None   # NEW
   ```

2. In `student.py`, at the two `StudentQuestionResponse(...)` call sites, populate
   `passage_spans` with the summary-only view (NOT the full token array — that is
   already in `passage_tokens`):
   ```python
   passage_spans = None
   if ann is not None and ann.passage_spans:
       ps = ann.passage_spans
       passage_spans = {
           "label":           ps.get("label"),
           "anatomy_present": ps.get("anatomy_present", []),
           "concepts_present":ps.get("concepts_present", []),
       }
   ```

   Rationale: the frontend uses `passage_spans.anatomy_present` and `concepts_present`
   for the pills panel, and uses `passage_tokens` (the merged flat-tag array) for
   token-level highlighting. Sending the full `tokens` array in both fields would
   double the payload size unnecessarily.

3. Verify with curl that a question with `passage_spans` in the DB returns the new
   field:
   ```bash
   curl -s "http://localhost:8000/api/questions?domain=grammar&limit=1" \
     -H "x-api-key: student-test-key" | python3 -c "
   import json,sys; q=json.load(sys.stdin)['items'][0]
   print('passage_spans:', q.get('passage_spans'))
   "
   ```

**Acceptance criteria:**
- `StudentQuestionResponse` has `passage_spans: Optional[dict]`
- For questions with `passage_spans` in DB: API response includes `passage_spans.label`, `anatomy_present`, `concepts_present`
- `passage_spans` in API response does NOT include the `tokens` array
- For questions without `passage_spans` in DB: `passage_spans` is `null` in API response
- `passage_tokens` field unchanged — still carries the flat merged-tag token list

---

### TASK-011 — Pass annotation object through student query path

**Complexity:** S  
**Depends on:** TASK-009  
**Files:**
- MODIFY: `backend/app/routers/student.py`

**Note:** Verified 2026-06-21 — both call sites already follow the pattern
`ann = ann_map.get(q.latest_annotation_id)` (ORM object) then
`ann_data = ann.annotation_jsonb`. No restructuring needed; TASK-009 only needs to
pass `annotation=ann` at lines 472 and 1221. TASK-011 is effectively a no-op — mark
complete once TASK-009 is done.

**Subtasks:**

1. In `student_recall` (the `GET /api/questions` handler), verify that at the point where
   `_fallback_passage_tokens` is called (around line 472), the `ann` ORM object is
   available. Currently `ann = ann_map.get(q.latest_annotation_id)` fetches the
   `QuestionAnnotation` object — confirm this is the ORM object (not just the JSONB dict).

2. At the second call site (~line 1221, likely in a diagnostic or study endpoint), verify
   the same. If `annotation` is not available as an ORM object at that call site, add it
   to the query.

3. Check `ann_map` construction: confirm it maps annotation UUID → `QuestionAnnotation`
   ORM object (not a plain dict). If it maps to a dict, restructure to map to ORM objects.
   This may require changing the SQLAlchemy query that populates `ann_map`.

**Acceptance criteria:**
- At both `_fallback_passage_tokens` call sites, `annotation=ann` is a `QuestionAnnotation` ORM object with `.passage_spans` accessible
- `ann.passage_spans` returns the JSONB dict (or None) without an extra DB query

---

## Phase 4 — Backfill Scripts

---

### TASK-012 — Backfill script: reannotate_spans.py

**Complexity:** M  
**Depends on:** TASK-007  
**Files:**
- CREATE: `scripts/reannotate_spans.py`

**Subtasks:**

1. Create `scripts/reannotate_spans.py` with `uv run python` compatibility
   (same pattern as `scripts/reannotate_official_v7.py`).

2. Implement CLI with argparse:
   ```
   --status       missing|all         (default: missing)
   --content-origin official|generated|all  (default: official)
   --question-id  UUID                (single question mode)
   --limit        INT                 (cap on questions processed; default: unlimited)
   --dry-run                          (validate only, don't write)
   --concurrency  INT                 (parallel API calls; default: 5)
   --priority     active|all          (default: active first, then rest)
   ```

3. Main loop:
   ```python
   # Build query
   stmt = select(Question).where(
       Question.content_origin == content_origin,
       Question.question_family_key == "conventions_grammar",
   )
   if status == "missing":
       stmt = stmt.join(QuestionAnnotation, ...).where(
           QuestionAnnotation.passage_spans.is_(None)
       )

   # Priority: active questions first
   stmt = stmt.order_by(
       case((Question.practice_status == "active", 0), else_=1),
       Question.created_at,
   )

   if limit:
       stmt = stmt.limit(limit)

   questions = (await db.execute(stmt)).scalars().all()
   ```

4. For each question: call `annotate_spans(q.id, db)`, print result.
   In dry-run mode: call `validate_tokens` on the LLM output but don't write.

5. Print a summary table at the end:
   ```
   Total:    247
   Success:  231 (93.5%)
   Failed:     9 (3.6%)
   Skipped:    7 (2.8%)  ← questions with no passage text
   Review queue entries added: 9
   ```

6. On `KeyboardInterrupt`, print partial summary and exit cleanly.

**Acceptance criteria:**
- `python scripts/reannotate_spans.py --status missing --dry-run --limit 5` runs without error
- `python scripts/reannotate_spans.py --question-id <uuid>` annotates a single question and prints the label
- `python scripts/reannotate_spans.py --status missing --limit 10` writes `passage_spans` to 10 questions (or fewer if less are missing)
- Summary table printed on completion
- Failed questions logged to `span_review_queue`, not to stdout (stdout is for progress/summary only)

---

### TASK-013 — Review queue script: review_span_queue.py

**Complexity:** S  
**Depends on:** TASK-001  
**Files:**
- CREATE: `scripts/review_span_queue.py`

**Subtasks:**

1. Create `scripts/review_span_queue.py`.

2. CLI:
   ```
   --error-type   filter by error type
   --show-raw     include raw_llm_output in output (verbose)
   --resolve <id> mark a queue entry as resolved manually
   --note         resolution note (used with --resolve)
   ```

3. Default output: grouped table of unresolved entries:
   ```
   span_review_queue — 12 unresolved entries

   concat_mismatch (3):
     [uuid] Q: "Lê Lương Minh became..." | Expected len: 214, Got: 213 | 2026-06-21 10:14

   missing_primary_concept (6):
     [uuid] Q: "Historians agree..." | focus_key: transition_logic | 2026-06-21 10:15
     ...

   invalid_anatomy (3):
     [uuid] Q: "Maria Martinez..." | Bad keys: ['noun'] | 2026-06-21 10:16
   ```

4. `--resolve <id> --note "Re-ran manually, now OK"` updates `resolved_at = now()`,
   `resolved_by = 'manual'`, `resolution_note` in the DB.

**Acceptance criteria:**
- Script runs and shows a clean table
- `--error-type concat_mismatch` filters to that type only
- `--show-raw` prints the LLM output for each entry
- `--resolve <uuid> --note "..."` marks entry as resolved in DB

---

## Phase 5 — Frontend Color System

---

### TASK-014 — Create keyColors.ts utility

**Complexity:** S  
**Depends on:** nothing  
**Files:**
- CREATE: `APP/STUDENT_APP_REDUX/src/utils/keyColors.ts`

**Subtasks:**

1. Implement `djb2(str) -> number` — a simple deterministic string hash:
   ```typescript
   function djb2(str: string): number {
     let hash = 5381
     for (let i = 0; i < str.length; i++) {
       hash = ((hash << 5) + hash) + str.charCodeAt(i)
       hash |= 0  // force 32-bit int
     }
     return Math.abs(hash)
   }
   ```

2. Implement `assignKeyColor(id: string, category: 'anatomy' | 'concept'): { color: string, lightBg: string }`:
   ```typescript
   export function assignKeyColor(
     id: string,
     category: 'anatomy' | 'concept'
   ): { color: string; lightBg: string } {
     const hash = djb2(id)
     const hue = category === 'anatomy'
       ? 10 + (hash % 20) * 8        // 10°–170°, 20 slots, step 8°
       : 182 + (hash % 60) * 2.88    // 182°–355°, 60 slots, step ~3°
     const [sat, light, bgSat, bgLight] =
       category === 'anatomy'
         ? [50, 32, 40, 93]
         : [70, 26, 65, 89]
     return {
       color:   `hsl(${Math.round(hue)}, ${sat}%, ${light}%)`,
       lightBg: `hsl(${Math.round(hue)}, ${bgSat}%, ${bgLight}%)`,
     }
   }
   ```

3. Export `activeKeyStyle(color: string): React.CSSProperties`:
   ```typescript
   export function activeKeyStyle(color: string): React.CSSProperties {
     return { backgroundColor: color, color: '#ffffff', borderColor: color }
   }
   ```

4. Export `inactiveKeyStyle(color: string, lightBg: string): React.CSSProperties`:
   ```typescript
   export function inactiveKeyStyle(color: string, lightBg: string): React.CSSProperties {
     return { backgroundColor: lightBg, color, borderColor: color }
   }
   ```

5. Verify determinism: `assignKeyColor("subject", "anatomy")` returns the same value
   every call. Write a quick test verifying 5 known IDs produce consistent hues.

**Acceptance criteria:**
- `assignKeyColor("subject", "anatomy").color` matches `hsl(H, 50%, 32%)` format
- `assignKeyColor("subject_verb_agreement", "concept").color` matches `hsl(H, 70%, 26%)` format
- Same input always produces same output (deterministic)
- Anatomy hue is in 10°–178° range
- Concept hue is in 182°–355° range
- `assignKeyColor("a", "anatomy")` ≠ `assignKeyColor("b", "anatomy")` (collision is acceptable but infrequent — hash spread is sufficient for 80 keys)

---

### TASK-015 — Replace hardcoded colors in SYNTAX_ANATOMY_KEYS

**Complexity:** S  
**Depends on:** TASK-014  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/data/syntaxAnatomyKeys.ts`

**Subtasks:**

1. Import `assignKeyColor` at the top of the file.

2. For every entry in the `SYNTAX_ANATOMY_KEYS` array, replace the hardcoded `color`
   and `lightBg` values with computed values:
   ```typescript
   const _c = assignKeyColor('subject', 'anatomy')
   {
     id: 'subject',
     label: 'Primary Subject',
     group: 'Sentence Anatomy',
     color:   _c.color,
     lightBg: _c.lightBg,
     description: '...',
     rule: '...',
     priority: 10,
   }
   ```
   Or more concisely, compute inline:
   ```typescript
   { id: 'subject', ...assignKeyColor('subject', 'anatomy'), label: '...', ... }
   ```

3. Add new anatomy keys defined in PRD §7.1 that are NOT currently in the file:
   All the new keys added in `future_features.md` — `independent_clause`,
   `participial_phrase`, `infinitive_phrase`, `gerund_phrase`, `adverbial_clause`,
   `restrictive_clause`, `nonrestrictive_clause`, `noun_clause`, `introductory_element`,
   `parenthetical`, `series_item`, `coordinating_conjunction`, `correlative_conjunction`,
   `conjunctive_adverb`, `pronoun`, `antecedent`, `absolute_phrase`, `object`,
   `complement`, `transition_word`, `verb_phrase`, `determiner`, `punctuation_mark`.

   For each new key, use the descriptions from `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10`.

4. Verify the frontend still compiles: `npx tsc --noEmit` with no errors.

5. Visually verify in the browser that all pills render with visible colors and that
   no two visible pills have the exact same hue (they may be close, but should be
   distinguishable).

**Acceptance criteria:**
- `npx tsc --noEmit` passes
- All existing 8 anatomy keys still present with computed colors (not hardcoded)
- All new anatomy keys from PRD §7.1 are in the array
- No two keys share the exact same `color` string
- Grammar practice page loads and shows anatomy pills without console errors

---

### TASK-016 — Update dynamic concept key color generation in useGrammarSession.ts

**Complexity:** S  
**Depends on:** TASK-014  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`

**Subtasks:**

1. Import `assignKeyColor` at the top of `useGrammarSession.ts`.

2. Find the `allKeys` useMemo block that generates backend keys dynamically:
   ```typescript
   const backendKeys = [...passageKeyIds]
     .filter((id) => !knownIds.has(id))
     .map((id, index) => {
       const hue = (index * 67 + 215) % 360  // ← current ad-hoc formula
       return {
         id,
         label: id.replace(/_/g, ' ').replace(/\b\w/g, ...),
         group: 'Backend Grammar Keys',
         color: `hsl(${hue} 65% 38%)`,        // ← replace this
         lightBg: `hsl(${hue} 75% 94%)`,      // ← replace this
         ...
       }
     })
   ```

3. Replace the ad-hoc hue formula with `assignKeyColor(id, 'concept')`:
   ```typescript
   const { color, lightBg } = assignKeyColor(id, 'concept')
   return {
     id,
     label: id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
     group: 'Grammar Concepts',          // rename from 'Backend Grammar Keys'
     color,
     lightBg,
     description: `Grammar concept: ${id.replace(/_/g, ' ')}.`,
     rule: 'Highlighted spans come from the stored span annotation.',
     priority: 30,
   }
   ```

4. Update the group name from `'Backend Grammar Keys'` to `'Grammar Concepts'` to match
   the UI panel label spec in PRD §12.

**Acceptance criteria:**
- Dynamic concept key pills use `assignKeyColor` for deterministic colors
- Group name is `'Grammar Concepts'`
- Same concept key always renders with the same color regardless of question order
- `npx tsc --noEmit` passes

---

## Phase 6 — Frontend Hook & Data

---

### TASK-017 — Update passageKeyIds to prefer passage_spans summaries

**Complexity:** S  
**Depends on:** TASK-010 (API returns passage_spans)  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`

**Subtasks:**

1. Replace the existing `passageKeyIds` useMemo with the updated version from PRD §10.4:
   ```typescript
   const passageKeyIds = useMemo((): Set<string> => {
     const q = state.question as any
     const spans = q?.passage_spans
     if (spans) {
       return new Set<string>([
         ...(spans.anatomy_present   as string[] ?? []),
         ...(spans.concepts_present  as string[] ?? []),
       ])
     }
     // Fallback: derive from flat passage_tokens tags
     const ids = new Set<string>()
     passageTokens.forEach((token) => token.tags.forEach((tag) => ids.add(tag)))
     return ids
   }, [state.question, passageTokens])
   ```

2. Remove the old dependency on `state.question` being the only trigger — the new version
   depends on both `state.question` (for `passage_spans`) and `passageTokens` (for
   fallback). The deps array `[state.question, passageTokens]` is correct.

**Acceptance criteria:**
- For a question with `passage_spans` in the API response: `passageKeyIds` is populated from `anatomy_present` + `concepts_present`
- For a question without `passage_spans`: `passageKeyIds` is populated from `passageTokens` tags (existing behaviour)
- Key pills panel shows anatomy keys for questions with span data

---

### TASK-018 — Update normalizePassageTokens to handle anatomy+concept_tags format

**Complexity:** S  
**Depends on:** TASK-009  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/utils/sentenceTokenizer.ts`

**Subtasks:**

1. The `BackendPassageToken` interface currently only recognises `text`, `word`, `tags`,
   `is_blank`, `isBlank`. Add the new fields:
   ```typescript
   interface BackendPassageToken {
     text?:         unknown
     word?:         unknown
     tags?:         unknown      // legacy flat array
     anatomy?:      unknown      // new: structural tags
     concept_tags?: unknown      // new: grammar rule tags
     is_blank?:     unknown
     isBlank?:      unknown
   }
   ```

2. In the `normalizePassageTokens` mapping function, merge `anatomy` and `concept_tags`
   into the `tags` array for backward compat with `findActiveKeyForToken`, while also
   preserving them separately on the token for future use:
   ```typescript
   const anatomy = Array.isArray(token.anatomy)
     ? (token.anatomy as unknown[]).filter((t): t is string => typeof t === 'string')
     : []
   const conceptTags = Array.isArray(token.concept_tags)
     ? (token.concept_tags as unknown[]).filter((t): t is string => typeof t === 'string')
     : []
   const legacyTags = Array.isArray(token.tags)
     ? (token.tags as unknown[]).filter((t): t is string => typeof t === 'string')
     : []

   // Merge: anatomy + concept_tags + any legacy flat tags (deduped)
   const tags = [...new Set([...anatomy, ...conceptTags, ...legacyTags])]

   return {
     text,
     tags,
     isBlank: token.is_blank === true || token.isBlank === true,
   }
   ```

3. Verify `npx tsc --noEmit` passes.

**Acceptance criteria:**
- A token with `anatomy: ["subject"]` and `concept_tags: ["subject_verb_agreement"]` results in `tags: ["subject", "subject_verb_agreement"]`
- Legacy tokens with only `tags: [...]` still work unchanged
- Whitespace-only tokens with empty arrays still render without errors
- `npx tsc --noEmit` passes

---

### TASK-019 — Verify findActiveKeyForToken works with merged tags

**Complexity:** S  
**Depends on:** TASK-018  
**Files:**
- READ ONLY: `APP/STUDENT_APP_REDUX/src/utils/sentenceTokenizer.ts`

**Subtasks:**

1. Read the `findActiveKeyForToken` implementation. It currently checks
   `tags.includes(k.id) && activeKeys.has(k.id)`. Since TASK-018 merges anatomy and
   concept_tags into the flat `tags` array, this function should work without changes.

2. Verify this assumption by tracing through a test case:
   - Token: `{text: "of students", tags: ["prepositional_phrase", "subject_verb_agreement"]}`
   - Active keys: `new Set(["subject_verb_agreement"])`
   - `allKeys` includes an entry with `id: "subject_verb_agreement"`
   - `findActiveKeyForToken` should return that entry → span highlights

3. If the function works as-is, this task is a no-op (mark as verified). If changes are
   needed, make them.

**Acceptance criteria:**
- Clicking a concept key pill highlights spans where that concept_tag appears in the merged `tags` array
- Clicking an anatomy key pill highlights spans where that anatomy value appears in the merged `tags` array
- No changes needed to `findActiveKeyForToken` itself (it operates on the flat `tags` array which TASK-018 populates correctly)

---

## Phase 7 — Frontend UI Restructure

---

### TASK-020 — Restructure renderGrammarKeys to two explicit groups

**Complexity:** M  
**Depends on:** TASK-015, TASK-016, TASK-017  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`

**Subtasks:**

1. Update `renderGrammarKeys` to return two separate groups explicitly rather than
   relying on the dynamic `group` field of each key. The PRD specifies a fixed
   two-panel layout: "Sentence Anatomy" always shown, "Grammar Concepts" shown
   when concepts are present.

2. Replace the current implementation:
   ```typescript
   const renderGrammarKeys = useCallback(() => {
     const knownIds = new Set(SYNTAX_ANATOMY_KEYS.map((k) => k.id))

     // Group 1: ALL anatomy keys (always visible — static list)
     const anatomyGroup = {
       group: 'Sentence Anatomy',
       keys: SYNTAX_ANATOMY_KEYS.sort((a, b) => b.priority - a.priority),
       activeKeys: SYNTAX_ANATOMY_KEYS.filter((k) => state.activeKeys.has(k.id)),
     }

     // Group 2: concept keys that have real tagged spans for this question
     const conceptKeys = allKeys.filter(
       (k) => !knownIds.has(k.id) && passageKeyIds.has(k.id)
     )
     const conceptGroup = conceptKeys.length > 0 ? {
       group: 'Grammar Concepts',
       keys: conceptKeys.sort((a, b) => b.priority - a.priority),
       activeKeys: conceptKeys.filter((k) => state.activeKeys.has(k.id)),
     } : null

     return [anatomyGroup, ...(conceptGroup ? [conceptGroup] : [])]
   }, [state.activeKeys, passageKeyIds, allKeys])
   ```

3. The return type changes from a variable-length array of groups to always returning
   `[anatomyGroup]` or `[anatomyGroup, conceptGroup]`. Components consuming
   `renderGrammarKeys()` must handle both.

**Acceptance criteria:**
- "Sentence Anatomy" group always present with all anatomy keys
- "Grammar Concepts" group appears only when `passageKeyIds` contains non-anatomy keys
- Active state correctly tracked per group
- `npx tsc --noEmit` passes

---

### TASK-021 — Update GrammarAnalysisSection to render two-panel layout

**Complexity:** M  
**Depends on:** TASK-020  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/components/grammar/GrammarAnalysisSection.tsx` (or wherever grammar keys are rendered)
- MODIFY: `APP/STUDENT_APP_REDUX/src/components/GrammarPractice.css`

**Subtasks:**

1. Find where grammar key groups are currently rendered (search for `renderGrammarKeys`
   usage in the component tree).

2. Render the two panels side-by-side on wide screens, stacked on narrow:
   ```tsx
   <div className="grammar-keys-panels">
     {grammar.renderGrammarKeys().map((group) => (
       <div key={group.group} className="grammar-keys-group">
         <div className="grammar-keys-group-header">{group.group}</div>
         <div className="grammar-keys-list">
           {group.keys.map((key) => (
             <button
               key={key.id}
               className={`grammar-key-pill ${state.activeKeys.has(key.id) ? 'active' : ''}`}
               style={
                 state.activeKeys.has(key.id)
                   ? activeKeyStyle(key.color)
                   : inactiveKeyStyle(key.color, key.lightBg)
               }
               onClick={() => grammar.toggleKey(key.id)}
               title={key.description}
             >
               {key.label}
             </button>
           ))}
         </div>
       </div>
     ))}
   </div>
   ```

3. Import `activeKeyStyle` and `inactiveKeyStyle` from `keyColors.ts`.

4. Add CSS:
   ```css
   .grammar-keys-panels {
     display: flex;
     gap: 1rem;
     flex-wrap: wrap;
   }
   .grammar-keys-group {
     flex: 1;
     min-width: 200px;
   }
   .grammar-keys-group-header {
     font-size: 0.7rem;
     font-weight: 600;
     text-transform: uppercase;
     letter-spacing: 0.06em;
     color: #6b7280;
     margin-bottom: 0.5rem;
   }
   .grammar-keys-list {
     display: flex;
     flex-wrap: wrap;
     gap: 0.4rem;
   }
   .grammar-key-pill {
     border: 1.5px solid currentColor;
     border-radius: 999px;
     padding: 2px 10px;
     font-size: 0.75rem;
     font-weight: 500;
     cursor: pointer;
     transition: background-color 0.15s, color 0.15s;
   }
   .grammar-key-pill.active {
     /* Inline style from activeKeyStyle() handles color; class sets transition */
     transition: background-color 0.15s, color 0.15s;
   }
   ```

5. Visually verify in the browser: two panels render, pills have correct colors,
   clicking toggles active state with invert effect.

**Acceptance criteria:**
- "Sentence Anatomy" panel always visible with all anatomy keys
- "Grammar Concepts" panel appears for questions with span annotation
- Active pills invert (full color bg, white text)
- Inactive pills show light background with colored border and text
- Two panels side-by-side on desktop, stacked on mobile (flex-wrap)
- No regression in existing grammar practice flow

---

### TASK-022 — Find Traps button: scroll to first highlighted span

**Complexity:** S  
**Depends on:** TASK-021  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`
- MODIFY: `APP/STUDENT_APP_REDUX/src/components/grammar/QuestionSection.tsx`

**Subtasks:**

1. Update `findTraps` in `useGrammarSession.ts` to also activate `concepts_present`
   keys from `passage_spans` (not just the anatomy-based `focusKeyToAnatomyKeys` map):
   ```typescript
   const findTraps = useCallback(() => {
     if (!state.question) return
     const q = state.question as any

     // Concept keys from passage_spans (if available)
     const spanConceptKeys = (q?.passage_spans?.concepts_present as string[]) ?? []

     // Existing anatomy key mapping
     const grammar_focus_key = q.grammar_focus_key
     const anatomyKeys = (focusKeyToAnatomyKeys[grammar_focus_key] || [])
       .filter((id: string) => passageKeyIds.has(id))

     const backendKeys = [
       q.grammar_role_key,
       q.grammar_focus_key,
       q.syntactic_trap_key,
     ].filter((id): id is string => typeof id === 'string')

     const allTrapKeys = new Set([
       ...backendKeys,
       ...spanConceptKeys,
       ...anatomyKeys,
     ])

     setState((prev) => ({ ...prev, activeKeys: allTrapKeys }))
   }, [state.question, passageKeyIds])
   ```

2. Add a `data-highlight-first` attribute to the first highlighted token span in
   `QuestionSection.tsx`, and in `findTraps` (or via a `useEffect` after activating keys),
   scroll that element into view:
   ```typescript
   setTimeout(() => {
     const firstHighlight = document.querySelector('[data-highlight-first="true"]')
     firstHighlight?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
   }, 50)
   ```

3. In `QuestionSection.tsx`, add `data-highlight-first="true"` to the first token span
   that has a `matchingKey`:
   ```tsx
   let firstHighlightSet = false
   {tokens.map((token, i) => {
     const matchingKey = findActiveKeyForToken(...)
     const isFirstHighlight = matchingKey && !firstHighlightSet
     if (isFirstHighlight) firstHighlightSet = true
     return (
       <span
         key={i}
         data-highlight-first={isFirstHighlight ? "true" : undefined}
         ...
       >
   ```

**Acceptance criteria:**
- Clicking "Find Traps" activates both the grammar_focus_key concept pill and any anatomy keys relevant to the question
- Page scrolls to the first highlighted token after activating traps
- Clicking "Find Traps" a second time deactivates all keys (toggle behaviour)

---

### TASK-023 — Display passage_spans label in question header

**Complexity:** S  
**Depends on:** TASK-010 (API returns passage_spans)  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/components/grammar/Header.tsx`

**Subtasks:**

1. The `Header` component receives `question` as a prop. Add rendering of
   `question.passage_spans?.label` below the question counter, as a subtle tag:
   ```tsx
   {(question as any).passage_spans?.label && (
     <div className="span-label">
       {(question as any).passage_spans.label}
     </div>
   )}
   ```

2. CSS:
   ```css
   .span-label {
     font-size: 0.68rem;
     color: #9ca3af;
     font-style: italic;
     margin-top: 2px;
   }
   ```

3. Only show the label when `passage_spans` is present — questions without span
   annotation render the header unchanged.

**Acceptance criteria:**
- For span-annotated questions, label like "SVA: subject + PP distractor + verb blank" appears in small italic below the counter
- For non-annotated questions, no label element is rendered
- Label does not overflow its container on long labels

---

### TASK-024 — Add anatomy_present + concepts_present to passage_spans in API (stripe token array)

**Complexity:** S  
**Depends on:** TASK-010  
**Note:** This task verifies the API payload is correct and the frontend handles
it correctly. May be a no-op if TASK-010 fully covered it.

**Subtasks:**

1. Confirm via curl that `passage_spans` in the API response for a span-annotated question
   contains `label`, `anatomy_present`, `concepts_present` but NOT `tokens`.

2. If `tokens` is accidentally included, fix `student.py` to strip it from the
   `passage_spans` dict before including it in the response.

3. Confirm `passage_tokens` in the API response carries the merged flat-tag token list
   (from TASK-009 Step 0).

**Acceptance criteria:**
- API response `passage_spans` has keys: `label`, `anatomy_present`, `concepts_present` only
- API response `passage_tokens` has the full token list with merged `tags` arrays
- No `tokens` key in `passage_spans` API response field

---

## Phase 8 — Tests

---

### TASK-025 — Backend unit tests: span validator

**Complexity:** M  
**Depends on:** TASK-005  
**Files:**
- CREATE: `backend/tests/test_span_validator.py`

**Subtasks:**

Write pytest tests for every validation rule in `span_validator.py`:

1. `test_clean_sva_question` — a correctly annotated SVA passage passes all checks.
2. `test_concat_mismatch_detected` — missing space token causes `concat_mismatch`.
3. `test_concat_mismatch_extra_char` — extra character in a token causes `concat_mismatch`.
4. `test_invalid_anatomy_detected` — `anatomy: ["foobar"]` causes `invalid_anatomy`.
5. `test_invalid_concept_detected` — `concept_tags: ["made_up"]` causes `invalid_concept`.
6. `test_missing_primary_concept` — SVA question where no token has `subject_verb_agreement` in concept_tags.
7. `test_missing_blank_token` — passage has `_______` but no `is_blank: true` token.
8. `test_wrong_blank_anatomy_verb_vs_transition` — transition question where blank has `["main_verb"]` anatomy.
9. `test_multiple_errors_collected` — two errors present, both returned (not short-circuited).
10. `test_derive_summaries` — verify deduplication and sorting of anatomy_present and concepts_present.
11. `test_blank_anatomy_for_all_focus_keys` — call `blank_anatomy_for` for every key in `BLANK_ANATOMY_MAP`, verify non-empty result.

**Acceptance criteria:**
- `pytest backend/tests/test_span_validator.py` passes with 11/11 tests green
- Each test is independent (no shared state)

---

### TASK-026 — Backend unit tests: label generator

**Complexity:** S  
**Depends on:** TASK-004  
**Files:**
- CREATE: `backend/tests/test_span_label.py`

**Subtasks:**

1. `test_sva_with_pp_distractor` → expected label contains "SVA" and "PP distractor"
2. `test_sva_with_trap_note` → label ends with `[nearest noun attraction]`
3. `test_transition_logic` → label is `"Transition logic: transition blank"`
4. `test_pronoun_agreement` → label contains "Pronoun agreement"
5. `test_unknown_focus_key` → falls back to title-case of key string
6. `test_empty_anatomy_present` → label is just the prefix, no colon/suffix
7. `test_label_max_length` → even with 10 anatomy keys, label is ≤ 80 chars (suffix capped at 4)
8. `test_all_prefix_map_keys` — iterate all keys in PREFIX_MAP, call `generate_span_label`, verify no KeyError

**Acceptance criteria:**
- `pytest backend/tests/test_span_label.py` passes with 8/8 tests green

---

### TASK-027 — Backend integration tests: Pass 3 runner with mock LLM

**Complexity:** M  
**Depends on:** TASK-007  
**Files:**
- CREATE: `backend/tests/test_span_annotator.py`

**Subtasks:**

1. Create fixture: a grammar question + annotation in the test DB (use existing
   test factories if available, or create minimal rows).

2. `test_annotate_spans_success` — mock the LLM to return a valid token list,
   verify `passage_spans` is written to the annotation, `span_annotated_at` is set.

3. `test_annotate_spans_validation_failure` — mock LLM to return tokens with a
   `concat_mismatch` error; verify `passage_spans` is NOT written and `span_review_queue`
   gets one row.

4. `test_annotate_spans_parse_error` — mock LLM to return `"not json"` twice
   (first call + retry); verify `span_review_queue` gets one row with
   `error_type = "parse_error"`.

5. `test_annotate_spans_retry_succeeds` — mock LLM to return bad JSON on first call,
   valid tokens on second; verify success (no queue entry written).

6. `test_annotate_spans_no_passage_text` — question with empty `current_passage_text`
   and empty `current_question_text` raises `ValueError` without calling LLM.

**Acceptance criteria:**
- `pytest backend/tests/test_span_annotator.py` passes 6/6 tests
- No real LLM calls made in tests (fully mocked)
- `span_review_queue` entries inspectable via the test DB session

---

### TASK-028 — Backend integration tests: _fallback_passage_tokens priority chain

**Complexity:** M  
**Depends on:** TASK-009  
**Files:**
- MODIFY: `backend/tests/test_student_retrieval.py`

**Subtasks:**

Add three new tests alongside existing ones:

1. `test_passage_spans_takes_priority_over_passage_tokens` — annotation has both
   `passage_spans` and `annotation_jsonb["passage_tokens"]`; verify that
   `_fallback_passage_tokens` returns from `passage_spans`, not the old path.

2. `test_passage_spans_merges_anatomy_and_concept_tags` — passage_spans token with
   `anatomy: ["subject"]` and `concept_tags: ["subject_verb_agreement"]`; verify
   returned token has `tags: ["subject", "subject_verb_agreement"]`.

3. `test_passage_spans_absent_falls_through` — annotation has no `passage_spans`;
   verify the existing `annotation_jsonb["passage_tokens"]` or fallback path is used.

**Acceptance criteria:**
- All three new tests pass
- Existing tests in `test_student_retrieval.py` still pass (no regression)

---

### TASK-029 — Backend API contract tests: passage_spans in response

**Complexity:** S  
**Depends on:** TASK-010  
**Files:**
- MODIFY: `backend/tests/test_student_api_contracts.py`

**Subtasks:**

1. Add a test asserting that when `passage_spans` is set on an annotation, the API
   response includes `passage_spans.label`, `anatomy_present`, `concepts_present`.

2. Add a test asserting `passage_spans` in API response does NOT contain a `tokens` key.

3. Add a test asserting `passage_spans` is `null` in API response when annotation
   has no `passage_spans`.

**Acceptance criteria:**
- 3 new tests pass
- Existing contract tests pass

---

### TASK-030 — Frontend unit tests: keyColors utility

**Complexity:** S  
**Depends on:** TASK-014  
**Files:**
- CREATE: `APP/STUDENT_APP_REDUX/src/utils/__tests__/keyColors.test.ts`

**Subtasks:**

1. `test_djb2_deterministic` — same string always returns same hash.
2. `test_anatomy_hue_range` — `assignKeyColor("subject", "anatomy").color` hue is in 10–178°.
3. `test_concept_hue_range` — `assignKeyColor("subject_verb_agreement", "concept").color` hue is in 182–355°.
4. `test_anatomy_lighter_than_concept` — anatomy lightBg background L% > concept lightBg L%.
5. `test_different_ids_different_hues` — "subject" and "main_verb" have different hue values.
6. `test_activeKeyStyle_returns_correct_bg` — `activeKeyStyle(color).backgroundColor == color`.
7. `test_inactiveKeyStyle_returns_lightBg` — `inactiveKeyStyle(color, lightBg).backgroundColor == lightBg`.

**Acceptance criteria:**
- `npx vitest run src/utils/__tests__/keyColors.test.ts` passes 7/7

---

### TASK-031 — Frontend unit tests: normalizePassageTokens with anatomy+concept_tags

**Complexity:** S  
**Depends on:** TASK-018  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/utils/__tests__/sentenceTokenizer.test.ts`

**Subtasks:**

Add tests for the new BackendPassageToken fields:

1. `test_anatomy_and_concept_tags_merged` — token with `anatomy: ["subject"]`,
   `concept_tags: ["subject_verb_agreement"]` results in `tags: ["subject", "subject_verb_agreement"]`.

2. `test_legacy_flat_tags_unchanged` — token with only `tags: ["transition_logic"]`
   still works (no regression).

3. `test_deduplication` — token with both `anatomy: ["subject"]` and
   `tags: ["subject"]` does not result in `tags: ["subject", "subject"]`.

4. `test_single_token_falls_back_to_local_tokenizer` — single-token backend array
   still triggers local tokenizer.

5. `test_multi_token_with_anatomy_uses_backend` — two-token array with `anatomy`
   fields uses backend spans, not local tokenizer.

**Acceptance criteria:**
- All 5 new tests pass alongside existing sentenceTokenizer tests

---

### TASK-032 — Frontend integration tests: highlighting with new data format

**Complexity:** M  
**Depends on:** TASK-019, TASK-021  
**Files:**
- MODIFY: `APP/STUDENT_APP_REDUX/src/components/__tests__/GrammarPractice.test.tsx` or a new integration test file

**Subtasks:**

1. `test_concept_key_pill_shown_when_concepts_present` — mock API response with
   `passage_spans.concepts_present: ["subject_verb_agreement"]`; verify a pill with
   label "Subject Verb Agreement" is rendered in the "Grammar Concepts" group.

2. `test_anatomy_key_pills_always_shown` — even with `passage_spans: null`, all
   anatomy key pills in `SYNTAX_ANATOMY_KEYS` are visible.

3. `test_clicking_concept_key_highlights_span` — mock tokens where one span has
   `concept_tags: ["subject_verb_agreement"]`; click the concept pill; verify that
   span gets highlight styling.

4. `test_clicking_anatomy_key_highlights_span` — mock tokens where one span has
   `anatomy: ["prepositional_phrase"]`; click the anatomy pill; verify highlight.

5. `test_active_pill_has_inverted_colors` — active pill's background should equal
   its `color` value (invert style applied).

**Acceptance criteria:**
- All 5 tests pass
- Tests run with `npx vitest run` without network calls (mocked API)

---

## Phase 9 — Backfill Execution & Monitoring

---

### TASK-033 — Dry-run backfill: validate without writing

**Complexity:** S  
**Depends on:** TASK-012, all Phase 2 tasks  
**Files:** none (operational)

**Subtasks:**

1. Run:
   ```bash
   python scripts/reannotate_spans.py \
     --status missing \
     --content-origin official \
     --limit 20 \
     --dry-run
   ```
2. Review output: how many would succeed? How many would fail? What error types?
3. If `missing_primary_concept` > 10%, inspect raw LLM output for a failed question
   and adjust the prompt (TASK-006) before running live.
4. If `concat_mismatch` > 5%, check whether the passage_text contains special
   characters the LLM is escaping differently; add a note to the prompt.

**Acceptance criteria:**
- Dry-run completes without script error
- At least 80% of the 20 test questions would pass validation
- No `passage_spans` rows written to DB

---

### TASK-034 — Backfill: active official questions

**Complexity:** S  
**Depends on:** TASK-033 (dry-run passed)  
**Files:** none (operational)

**Subtasks:**

1. Run:
   ```bash
   python scripts/reannotate_spans.py \
     --status missing \
     --content-origin official \
     --priority active
   ```
2. Monitor: check `span_review_queue` row count after completion.
3. Spot-check 5 annotated questions via curl + the admin dashboard.
4. Verify in the frontend: open the grammar practice page, navigate to 3–4 questions,
   verify pills highlight correctly.

**Acceptance criteria:**
- All `practice_status = 'active'` official grammar questions have `passage_spans` set
- `span_review_queue` has < 5 unresolved entries
- Frontend highlighting works for at least 90% of spot-checked questions

---

### TASK-035 — Triage span_review_queue

**Complexity:** S  
**Depends on:** TASK-034  
**Files:** none (operational + possible TASK-006 prompt adjustments)

**Subtasks:**

1. Run `python scripts/review_span_queue.py` and review all unresolved entries.
2. For each `concat_mismatch`: inspect the LLM output. If the issue is escapable
   (e.g. Unicode, em-dash), add handling to `parse_llm_span_response` in TASK-006.
3. For each `missing_primary_concept`: check whether the `grammar_focus_key` in
   the annotation is in `CONCEPT_KEYS`. If it's a new key not in the vocabulary,
   add it to `CONCEPT_KEYS` in TASK-003 and re-run.
4. For each `invalid_anatomy` or `invalid_concept`: check whether the LLM invented
   a plausible key that should be added to the vocabulary. If so, update `span_vocab.py`
   and the D.10 rules file.
5. Manually resolve any entries that can be fixed by hand.

**Acceptance criteria:**
- `span_review_queue` has ≤ 5 unresolved entries after triage
- Any new keys added to vocabulary are documented in `rules_agent_dsat_grammar_ingestion_generation_v8.md §D.10`

---

### TASK-036 — Backfill: all remaining official questions

**Complexity:** S  
**Depends on:** TASK-035  
**Files:** none (operational)

**Subtasks:**

1. Run:
   ```bash
   python scripts/reannotate_spans.py \
     --status missing \
     --content-origin official
   ```
2. Verify final counts:
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE qa.passage_spans IS NOT NULL) AS annotated,
     COUNT(*) FILTER (WHERE qa.passage_spans IS NULL)     AS pending,
     COUNT(*) AS total
   FROM questions q
   JOIN question_annotations qa ON qa.id = q.latest_annotation_id
   WHERE q.content_origin = 'official'
     AND q.question_family_key = 'conventions_grammar';
   ```
3. Run `python scripts/review_span_queue.py` for final queue check.

**Acceptance criteria:**
- 100% of active official grammar questions have `passage_spans`
- ≥ 95% of all official grammar questions have `passage_spans`
- `span_review_queue` unresolved count ≤ success metric from PRD §15
- Frontend highlighting works end-to-end in the live dev stack

---

## Summary Table

| Task | Title | Phase | Complexity | Depends on |
|---|---|---|---|---|
| TASK-001 | DB migration | 1 | M | — |
| TASK-002 | SQLAlchemy model | 1 | S | 001 |
| TASK-003 | Vocabulary constants | 2 | S | — |
| TASK-004 | Label generator | 2 | S | 003 |
| TASK-005 | Span validator | 2 | M | 003 |
| TASK-006 | Pass 3 LLM prompt | 2 | L | 003 |
| TASK-007 | span_annotator.py | 2 | L | 002,003,004,005,006 |
| TASK-008 | Admin endpoint | 2 | S | 007 |
| TASK-009 | _fallback_passage_tokens update | 3 | M | 002 |
| TASK-010 | API payload: passage_spans | 3 | S | 009 |
| TASK-011 | Pass annotation object to fallback | 3 | S | 009 |
| TASK-012 | reannotate_spans.py | 4 | M | 007 |
| TASK-013 | review_span_queue.py | 4 | S | 001 |
| TASK-014 | keyColors.ts | 5 | S | — |
| TASK-015 | SYNTAX_ANATOMY_KEYS colors | 5 | S | 014 |
| TASK-016 | Dynamic concept key colors | 5 | S | 014 |
| TASK-017 | passageKeyIds prefers passage_spans | 6 | S | 010 |
| TASK-018 | normalizePassageTokens: anatomy+concept | 6 | S | 009 |
| TASK-019 | Verify findActiveKeyForToken | 6 | S | 018 |
| TASK-020 | renderGrammarKeys: two explicit groups | 7 | M | 015,016,017 |
| TASK-021 | Two-panel pills UI | 7 | M | 020 |
| TASK-022 | Find Traps: scroll to first highlight | 7 | S | 021 |
| TASK-023 | Header: show passage_spans label | 7 | S | 010 |
| TASK-024 | Verify API strips tokens from passage_spans | 7 | S | 010 |
| TASK-025 | Tests: span validator | 8 | M | 005 |
| TASK-026 | Tests: label generator | 8 | S | 004 |
| TASK-027 | Tests: Pass 3 runner (mock LLM) | 8 | M | 007 |
| TASK-028 | Tests: _fallback_passage_tokens chain | 8 | M | 009 |
| TASK-029 | Tests: API contract (passage_spans) | 8 | S | 010 |
| TASK-030 | Tests: keyColors utility | 8 | S | 014 |
| TASK-031 | Tests: normalizePassageTokens | 8 | S | 018 |
| TASK-032 | Tests: highlighting integration | 8 | M | 019,021 |
| TASK-033 | Dry-run backfill (20 questions) | 9 | S | 012 |
| TASK-034 | Backfill: active official questions | 9 | S | 033 |
| TASK-035 | Triage span_review_queue | 9 | S | 034 |
| TASK-036 | Backfill: all remaining official | 9 | S | 035 |

**Total tasks:** 36  
**Estimated complexity:** 3 L + 10 M + 23 S  
**Critical path (minimum viable highlighting):** 001 → 002 → 003 → 007 → 009 → 010 → 017 → 020 → 034
