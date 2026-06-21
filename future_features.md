# Future Features & Outstanding Work

Consolidated from `future_tasks.md` and `_deprecated/rules_v*/future_plans.md`.

---

## QA — Student App

Phases 1–5 of `APP/STUDENT_APP_REDUX/` are complete. Remaining QA:

- [ ] **Manual QA** — walk the full student journey with a real `VITE_TEST_USER_TOKEN` against the live backend: load dashboard → view weak concepts → run diagnostic → answer questions → check test mode → verify missed questions tab populates
- [ ] **designqc** — run `openwolf designqc --url http://localhost:5173` for visual polish review; check spacing, typography, color contrast, responsive layout
- [ ] **Backend endpoint tests** — add pytest tests for `GET /api/study/missed` covering: success response, domain filter, sort_by options, empty result, invalid token
- [ ] **Performance check** — measure `/study/recommendations` fetch latency, React Query cache hit rates, no N+1 queries on backend

---

## Admin Dashboard — Remaining Work

`APP/ADMIN_APP/` Phase 2 (frontend) is scaffolded. Remaining:

- [ ] **QA Admin UI** — run against live backend with a real admin token; verify all 4 pages load, filters work, approve/reject mutations persist
- [ ] **Auth guard** — add admin token validation and redirect to login if token is missing or invalid
- [ ] **designqc** — run `openwolf designqc --url http://localhost:5174` for visual polish
- [ ] **Student Performance deep-dive** — add cohort view: accuracy across all students per focus key, which questions have the highest miss rates system-wide
- [ ] **Data Management — question detail page** — click into a single question to view full annotation, version history, audit log, and edit form
- [ ] **Backend endpoint tests** — pytest tests for admin question approve/reject/edit endpoints

---

## Generation Pipeline — Batch Scheduler

Not yet built. Currently generation is triggered manually.

- [ ] **Production batch scheduler** — automatically maintains the 100-question blueprint, produces generation batches by domain/difficulty target, respects rotation rules (no repeated `topic_broad` consecutively, no repeated `topic_fine` within a 5-item window)
- [ ] **Stats-driven module requests** — scheduler auto-emits module generation requests when updated `practice_exam_stats` snapshot is available, using real distribution data to drive domain and difficulty targeting
- [ ] **Adaptive second module generation** — automated generation of `sec01_mod02` higher/lower route with correct difficulty ramp (`clustered_progressive` for higher, `gentle_progressive` for lower), triggered by student module 1 performance score

---

## Generation Pipeline — Validation & Repair

Validator passes 1–6 exist. Pass 7 and automated repair loop are missing.

- [ ] **Pass 7: Set-level distribution validator** — checks full 27-question module for answer-position streaks (max 3 same answer in a row), domain coverage balance, difficulty ramp compliance, question-family repetition limits
- [ ] **Automated repair loop** — structured re-prompting of failed validator items: report failures as structured JSON, re-generate with failure context injected into prompt, re-validate, max 3 repair attempts before flagging for manual review
- [ ] **Second-model review pass** — dedicated SAT realism review on accepted items using a separate model (e.g. GPT-4o or Claude Opus) before export to production question bank; checks: realistic SAT style, distractor plausibility, passage authenticity

---

## Generation Pipeline — Module Blueprints

- [ ] **Module blueprint registry** — store `sec01_mod01`, `sec01_mod02_higher`, `sec01_mod02_lower` blueprints as versioned config; allow overrides per course, diagnostic set, or remediation target
- [ ] **Blueprint-driven generation UI** — admin page to select a blueprint, override domain/difficulty quotas, and trigger a generation run with live progress tracking

---

## Grammar Practice — Anatomy Highlighting (Backend Plan)

The local tokenizer (Pass 2 in `sentenceTokenizer.ts`) uses heuristics for structural
annotation: prepositional phrases, subject, and appositives. This is approximate — it
cannot reliably detect verbs, objects, or complex modifier placements without a real parser.

**Plan B — Word-level span annotation pipeline and DB design:**

**Where the data lives today:**
`passage_tokens` is NOT a dedicated DB column. It is a key inside `annotation_jsonb` (the
JSONB blob on `question_annotations`). `_fallback_passage_tokens` in `student.py` checks
for it first (line 191–193); if missing, it builds tokens on-the-fly at query time using
`grammar_role_key` / `grammar_focus_key` / `syntactic_trap_key` as tags on a whole-passage
chunk. Most grammar questions currently have no `passage_tokens` key in the JSONB at all.

**Target DB design — `passage_spans` column:**

Add a dedicated `passage_spans` JSONB column to `question_annotations` (separate from
`annotation_jsonb` so span data can be regenerated independently without touching the
grammar taxonomy annotation). Three levels of data live inside it:

```json
{
  "label": "SVA: subject + PP distractor + verb blank",
  "anatomy_present":   ["subject", "prepositional_phrase", "main_verb"],
  "concepts_present":  ["subject_verb_agreement", "nearest_noun_attraction", "verb_form"],
  "tokens": [
    {"text": "The number",    "anatomy": ["subject"],              "concept_tags": [],                                           "is_blank": false},
    {"text": " ",             "anatomy": [],                       "concept_tags": [],                                           "is_blank": false},
    {"text": "of students",   "anatomy": ["prepositional_phrase"], "concept_tags": ["subject_verb_agreement", "nearest_noun_attraction"], "is_blank": false},
    {"text": " in the class", "anatomy": ["prepositional_phrase"], "concept_tags": ["subject_verb_agreement"],                   "is_blank": false},
    {"text": " ",             "anatomy": [],                       "concept_tags": [],                                           "is_blank": false},
    {"text": "_______",       "anatomy": ["main_verb"],            "concept_tags": ["verb_form"],                                "is_blank": true}
  ]
}
```

**Three levels explained:**

- **`label`** (string) — auto-generated one-line title describing the structural pattern.
  Human-readable at a glance in the admin dashboard, searchable, filterable. Format:
  `"{primary_concept}: {key anatomy elements}"`. Examples:
  - `"SVA: subject + PP distractor + verb blank"`
  - `"Verb tense: scientific present, simple-present blank"`
  - `"Transition logic: contrast, blank at sentence boundary"`
  - `"Pronoun agreement: antecedent + pronoun blank"`
  - `"Modifier placement: dangling participial phrase"`

- **`anatomy_present`** (string[]) — deduplicated union of all `anatomy` tags across tokens.
  Drives the "Sentence Anatomy" key pills panel: any key in this list gets a pill shown even
  if the student hasn't clicked anything yet. Also used for analytics and filtering.

- **`concepts_present`** (string[]) — deduplicated union of all `concept_tags` across tokens.
  Drives the "Grammar Concepts" key pills panel. Replaces the current on-the-fly derivation
  from `grammar_focus_key` / `syntactic_trap_key`.

- **`tokens`** (object[]) — word-level spans. Each token carries `text`, `anatomy[]`,
  `concept_tags[]`, and `is_blank`. Concatenating all `text` fields must exactly reconstruct
  `current_passage_text` (enforced by the pipeline validator).

**Why a separate column instead of adding to `annotation_jsonb`:**
- Span data can be regenerated (improved model, better prompts) without touching the
  grammar taxonomy annotation — different pipeline, different update cadence
- `annotation_jsonb` is already dense; keeping spans separate keeps both schemas readable
- PostgreSQL can GIN-index `passage_spans` for fast `anatomy_present @> '["subject"]'`
  queries (e.g. "find all SVA questions that have a PP distractor span annotated")
- Admin dashboard can show `label` without parsing the full token array

**Ingestion pipeline — three-pass design:**

```
Pass 1 (existing) — OCR / PDF extraction
Pass 2 (existing) — Grammar taxonomy annotation (annotation_jsonb)
Pass 3 (new)      — Span annotation → passage_spans column
```

Pass 3 runs after Pass 2 and is independent of it:

1. **Input**: `current_passage_text` + Pass 2 annotation fields
   (`grammar_focus_key`, `grammar_role_key`, `syntactic_trap_key`, `secondary_grammar_focus_keys`)
2. **LLM prompt**: Ask the model to tokenize the passage into spans and tag each span with
   anatomy keys and concept_tags. The approved key lists (from the anatomy and concept
   references below) are injected into the prompt as the allowed vocabulary.
3. **Validation**:
   - Concatenated `token.text` values must equal `current_passage_text` exactly
   - All `anatomy` values must be in the approved anatomy list
   - All `concept_tags` values must be in the approved concept_tags list
   - `concepts_present` must include `grammar_focus_key` (the primary concept must be tagged somewhere)
   - At least one token must have `is_blank: true` if the passage contains `_______`
4. **Label generation**: Rule-based from `concepts_present` + `anatomy_present`:
   primary concept → label prefix; key anatomy elements → label suffix
5. **Storage**: Write to `passage_spans` column; set `span_annotated_at` timestamp

**Frontend read path — priority chain:**

```
1. passage_spans.tokens (new, word-level, anatomy + concept_tags)   ← target state
2. annotation_jsonb.passage_tokens (old, chunk-level flat tags)     ← current state for annotated rows
3. _fallback_passage_tokens() on-the-fly construction               ← current state for most rows
4. Local structural tokenizer (sentenceTokenizer.ts)                ← graceful degradation
```

`_fallback_passage_tokens` gains a step 0: check `passage_spans` first. If present, convert
`anatomy` + `concept_tags` into the unified `tags` array the frontend already reads (merge
both arrays), preserving full backward compat with `findActiveKeyForToken`.

**Backfill strategy for existing official questions:**
- `scripts/reannotate_spans.py` — runs Pass 3 over all `content_origin='official'` questions
  that have no `passage_spans` entry; can be re-run to upgrade span quality
- Failed validations land in a `span_review_queue` table (question_id, error, raw_llm_output)
  for manual triage — same pattern as the existing `needs_review` job status

**What Plan B does:**
- During the annotation pass (`backend/app/prompts/annotate_prompt.py`), prompt the LLM to
  identify word-level spans for each grammar anatomy element in the passage: subject noun
  phrase, main verb, prepositional phrases, appositives, modifiers.
- Write the result as a `passage_tokens` key directly into `annotation_jsonb`, e.g.:
  ```json
  [
    {"text": "The number",        "tags": ["subject"]},
    {"text": " ",                 "tags": []},
    {"text": "of students",       "tags": ["prepositional_phrase"]},
    {"text": " in the class",     "tags": ["prepositional_phrase"]},
    {"text": " ",                 "tags": []},
    {"text": "_______",           "tags": ["main_verb"], "is_blank": true}
  ]
  ```
- Because `_fallback_passage_tokens` already checks `ann_data.get("passage_tokens")` first,
  the frontend picks up the stored tokens automatically — no schema migration, no new column,
  no frontend changes needed.
- Requires: updating `annotate_prompt.py` to request span output, running
  `scripts/reannotate_official_v7.py` to backfill existing questions, validating accuracy.

**Official questions: store anatomy AND grammar concepts in DB**

For official practice questions, both layers of span data should be stored explicitly in
`annotation_jsonb` rather than computed on the fly or guessed by the local tokenizer.

Two separate tag arrays per token:

- **`anatomy`** — structural sentence elements (full list below). These describe WHAT part
  of the sentence the span is — things you can physically point to.

- **`concept_tags`** — SAT grammar rules/skills the span illustrates (full list below).
  These describe WHY the span matters for the question being tested. Named `concept_tags` to
  distinguish them from the question-level `grammar_focus_key` and from the structural `anatomy`.

Proposed token format:
```json
[
  {"text": "The number",    "anatomy": ["subject"],              "concept_tags": []},
  {"text": " ",             "anatomy": [],                       "concept_tags": []},
  {"text": "of students",   "anatomy": ["prepositional_phrase"], "concept_tags": ["subject_verb_agreement"]},
  {"text": " in the class", "anatomy": ["prepositional_phrase"], "concept_tags": ["subject_verb_agreement"]},
  {"text": " ",             "anatomy": [],                       "concept_tags": []},
  {"text": "_______",       "anatomy": ["main_verb"],            "concept_tags": ["verb_tense_consistency", "verb_form"], "is_blank": true}
]
```

**Highlighting behaviour:**
A span can carry both tags simultaneously — e.g. a prepositional phrase that is also the
subject-verb-agreement distractor gets `anatomy: ["prepositional_phrase"]` AND
`concept_tags: ["subject_verb_agreement"]`. Clicking the *Prepositional Phrase* anatomy pill
highlights it as a structural element; clicking the *Subject-Verb Agreement* concept pill
highlights it as the trap. Same words, two different reasons to highlight — the dual array
makes both possible without conflict.

The frontend highlights a token whenever its active key appears in EITHER `anatomy` OR
`concept_tags`. `passageKeyIds` merges both arrays; `findActiveKeyForToken` checks both.
The grammar key pills panel gains a second group — "Grammar Concepts" — alongside the
existing "Sentence Anatomy" group, each pill triggering only spans tagged for that key.

---

### Anatomy key reference (from `rules_agent_dsat_grammar_ingestion_generation_v8.md`)

Structural sentence elements — things you can point to in the sentence. Sourced from
D.1 role categories and structural sub-elements implied by D.2 focus keys and D.5 trap keys.

**Currently in `SYNTAX_ANATOMY_KEYS` (frontend, already highlighting):**
- `subject` — primary noun phrase performing the main verb's action
- `main_verb` — primary verb of the independent clause; also used for the blank slot
- `prepositional_phrase` — phrase beginning with a preposition; frequent SVA distractor
- `subordinate_clause` — dependent clause opened by a subordinating conjunction
- `subordinating_conj` — the conjunction that opens a subordinate clause
- `relative_clause` — clause introduced by who/which/whom/whose
- `appositive` — noun phrase that renames an adjacent noun, set off by commas
- `modifier` — word or phrase that qualifies another element (adjective, adverb, participial)

**Additional anatomy keys to add (derived from v8 taxonomy):**
- `coordinating_conjunction` — and/but/or/nor/yet/so/for; structural link between parallel elements
- `conjunctive_adverb` — however/therefore/moreover/consequently etc.; connects independent clauses and requires semicolon before + comma after
- `parallel_element` — one item in a list or paired structure that must be grammatically symmetric
- `pronoun` — the pronoun word itself as a structural element (distinct from its antecedent)
- `antecedent` — the noun or noun phrase a pronoun refers back to
- `absolute_phrase` — nominative absolute (noun + participial phrase modifying the whole clause); requires comma boundary
- `object` — direct or indirect object of the main verb
- `complement` — subject complement or object complement after a linking verb
- `transition_word` — a conjunctive adverb or transitional phrase filling the blank slot
- `verb_phrase` — full verb group including auxiliaries (expands `main_verb` for complex tenses)
- `determiner` — article or determiner (a/an/the/this/these/those) filling the blank slot
- `punctuation_mark` — a punctuation character filling the blank slot (comma, semicolon, colon, dash)

**Additional anatomy keys from DSAT Standard English Conventions research:**

The following structural elements appear across DSAT Boundaries, Form/Structure/Sense, and
punctuation questions. Sources: College Board official practice, Khan Academy SAT prep,
Test Innovators DSAT grammar guide, PrepScholar SAT grammar rules, The Critical Reader.

*Clause-level structures:*
- `independent_clause` — a subject-predicate unit that can stand alone as a complete sentence;
  the fundamental unit tested in Boundaries questions (comma splice, run-on, fragment)
- `predicate` — the full verb + objects + complements + adverbials of the main clause;
  broader than `main_verb` which marks only the head verb
- `noun_clause` — a subordinate clause functioning as a noun (subject, object, or complement);
  introduced by that/what/whether/who; e.g. "that she won" in "He believes that she won"
- `adverbial_clause` — a subordinate clause functioning as an adverb, modifying the main verb
  (overlaps with `subordinate_clause` but specifies function; used when the clause answers
  when/where/why/how/under what condition)
- `restrictive_clause` — an essential relative clause introduced by "that" with NO comma;
  identifies which specific noun is meant; removing it changes the sentence's meaning
- `nonrestrictive_clause` — a non-essential relative clause introduced by "which" WITH commas;
  adds extra information about an already-identified noun; can be removed without changing core meaning

*Phrase-level structures:*
- `participial_phrase` — a phrase headed by a present (-ing) or past (-ed/-en) participle,
  functioning as an adjective; must immediately follow the noun it modifies or appear at the
  sentence opening followed by a comma and then the noun it modifies (dangling modifier trap)
- `infinitive_phrase` — a "to + verb" phrase; can function as noun, adjective, or adverb;
  e.g. "to complete the study" as subject or purpose modifier
- `gerund_phrase` — an "-ing verb" phrase functioning as a noun (subject, object, or complement);
  e.g. "Running every day" as sentence subject; distinct from a participial phrase which
  functions as an adjective
- `adverbial_phrase` — a non-clause phrase modifying a verb, adjective, or adverb; includes
  prepositional phrases used adverbially (already tagged `prepositional_phrase` for structure,
  `adverbial_phrase` marks its grammatical function)

*Sentence position / punctuation-defined structures:*
- `introductory_element` — any phrase or clause at the start of a sentence that must be
  followed by a comma before the main clause; includes adverbial clauses ("Although X,"),
  participial phrases ("Having completed Y,"), prepositional phrases ("In 2013,"), and
  transitional words/phrases ("However,", "For example,")
- `parenthetical` — any interrupting element set off by a matching pair of delimiters
  (comma–comma, dash–dash, or parenthesis–parenthesis); the opening delimiter must match
  the closing delimiter — mixing types is always wrong on the DSAT
- `nonrestrictive_element` — the content inside a parenthetical; can be an appositive, a
  nonrestrictive clause, or a supplementary phrase; non-essential to the sentence's meaning
- `series_item` — one element in a parallel list or series (two or more items joined by
  a coordinating conjunction); all items must share the same grammatical form

*Conjunction structures:*
- `correlative_conjunction` — a paired conjunction requiring parallel structure on both sides:
  either/or, neither/nor, both/and, not only/but also, as/as, more/than; each half of the
  pair is tagged separately as `correlative_conjunction`

**Blank slot anatomy — `grammar_focus_key` → anatomy tag mapping:**

The blank (`_______`) is not always a verb. The anatomy tag assigned to the blank must
reflect what the word in the blank actually is. This mapping drives the local tokenizer
(`blankTags()` in `sentenceTokenizer.ts`) and must be preserved when Plan B span annotation
is implemented so that `passage_spans.tokens` uses the same anatomy tag for the blank.

| `grammar_focus_key` group | Blank anatomy tags |
|---|---|
| `verb_tense_consistency`, `verb_form`, `subject_verb_agreement`, `voice_active_passive` | `main_verb`, `verb_form`, `verb_tense_consistency` |
| `transition_logic`, `conjunctive_adverb_usage`, `logical_relationships` | `transition_word`, `conjunctive_adverb` |
| `pronoun_antecedent_agreement`, `pronoun_case`, `pronoun_clarity` | `pronoun` |
| `determiners_articles`, `noun_countability` | `determiner` |
| `punctuation_comma`, `semicolon_use`, `colon_dash_use`, `apostrophe_use`, `appositive_punctuation` | `punctuation_mark` |
| all others / default | `main_verb`, `verb_form`, `verb_tense_consistency` |

This table is the authoritative source. Any new `grammar_focus_key` added to the v8 taxonomy
must be assigned a blank anatomy tag here before span annotation can produce correct output.

---

### Concept key reference (from `rules_agent_dsat_grammar_ingestion_generation_v8.md`)

Grammar rules/skills — why a span matters for the question. Drawn from D.2 Grammar Focus
Keys and D.5 Syntactic Trap Keys. These become `concept_tags` on specific token spans.

**Sentence boundary concepts (D.2.1):**
- `sentence_fragment` — span is a dependent clause or phrase incorrectly standing alone
- `comma_splice` — span shows two independent clauses joined only by a comma
- `run_on_sentence` — span shows two independent clauses fused without punctuation
- `sentence_boundary` — general boundary issue when none of the above is more specific

**Agreement concepts (D.2.2):**
- `subject_verb_agreement` — span is the subject or an interference phrase affecting verb number
- `pronoun_antecedent_agreement` — span is the pronoun or its antecedent
- `noun_countability` — span shows a count/mass noun whose number determines the verb
- `determiners_articles` — span involves a/an/the/this/these chosen for number or specificity

**Pronoun concepts (D.2.3):**
- `pronoun_case` — span is a pronoun requiring nominative/objective/possessive case
- `pronoun_clarity` — span is an ambiguous pronoun or its possible antecedents

**Verb form concepts (D.2.4):**
- `verb_tense_consistency` — span is the verb slot; tense must match passage register
- `verb_form` — span involves finite vs non-finite, gerund vs infinitive, or mood
- `voice_active_passive` — span involves active vs passive voice choice
- `negation` — span tests scope of negation (not all vs all not)

**Modifier concepts (D.2.5):**
- `modifier_placement` — span is a dangling or misplaced modifier
- `absolute_phrase` — span is a nominative absolute requiring comma boundary
- `comparative_structures` — span is a comparison requiring grammatical symmetry
- `illogical_comparison` — span compares a noun to an action or dissimilar category
- `adjective_adverb_distinction` — span is an adjective/adverb choice (esp. after linking verbs)
- `logical_predication` — span makes a nonsensical or category-mismatched attribution
- `relative_pronouns` — span is who/which/that chosen for restrictive vs non-restrictive use

**Punctuation concepts (D.2.6):**
- `punctuation_comma` — span shows a comma placement choice
- `colon_dash_use` — span involves a colon or dash introducing a list or explanation
- `semicolon_use` — span involves a semicolon between independent clauses
- `conjunctive_adverb_usage` — span is a conjunctive adverb requiring semicolon + comma
- `apostrophe_use` — span involves possessive or plural apostrophe placement
- `possessive_contraction` — span tests its/it's or whose/who's distinction
- `appositive_punctuation` — span is an appositive requiring matching comma or dash delimiters
- `hyphen_usage` — span involves a compound modifier requiring a hyphen
- `quotation_punctuation` — span involves punctuation inside or outside quotation marks
- `unnecessary_internal_punctuation` — span has a comma/dash that breaks a required syntactic unit
- `end_punctuation_question_statement` — span tests period vs question mark based on sentence type

**Parallel structure concepts (D.2.7):**
- `parallel_structure` — span is an element in a list or pair that must match in grammatical form
- `elliptical_constructions` — span involves an implied element that must be grammatically recoverable
- `conjunction_usage` — span is a conjunction whose choice affects structure or logic

**Expression of ideas concepts (D.2.8):**
- `redundancy_concision` — span contains words that repeat information already established
- `precision_word_choice` — span requires the most precise word among near-synonyms
- `register_style_consistency` — span uses informal or inconsistent register
- `logical_relationships` — span states a cause, contrast, or sequence that must be logically accurate
- `emphasis_meaning_shifts` — span placement or word order shifts the sentence's emphasis
- `data_interpretation_claims` — span makes a claim that must accurately reflect referenced data
- `transition_logic` — span is the transition word/phrase expressing the correct logical relationship
- `commonly_confused_words` — span tests affect/effect, principle/principal, allusion/illusion etc.
- `preposition_idiom` — span tests an idiomatic verb-preposition or adjective-preposition pairing

**Syntactic trap concepts (D.5) — tag the distractor span, not the blank:**
- `nearest_noun_attraction` — the noun closest to the blank that incorrectly attracts agreement; tag that noun span
- `garden_path` — span leads the reader toward a wrong parse before the blank resolves it
- `early_clause_anchor` — opening clause/phrase that causes the reader to misidentify the subject
- `nominalization_obscures_subject` — nominalized verb phrase hiding the true grammatical subject
- `interruption_breaks_subject_verb` — the interrupting phrase (appositive, relative clause, PP) between subject and verb
- `long_distance_dependency` — span where subject and verb are separated by many intervening words
- `pronoun_ambiguity` — span where two possible antecedents make pronoun reference unclear
- `scope_of_negation` — span where negation scope is ambiguous
- `modifier_attachment_ambiguity` — span where a modifier could attach to two different words
- `presupposition_trap` — span that assumes a fact not established in the passage
- `temporal_sequence_ambiguity` — span where time ordering of events is unclear

**Backward-compatibility requirement:**

- The new word-level `passage_tokens` must be a strict superset of the old format. Existing
  rows that have chunk-level tokens (1–2 sentences per token, grammar focus key tags) must
  continue to render correctly — the frontend multi-token path already handles those.
- Old single-token whole-passage rows (the ones that currently fall back to the local
  tokenizer) will be upgraded in-place by the re-annotation script; no schema migration needed.
- The re-annotation script must validate that the concatenated text of all new word-level
  tokens exactly reconstructs the original `current_passage_text`, so no passage content
  is silently dropped or altered.
- Any question the re-annotation LLM cannot confidently span-annotate should be left with
  its existing chunk-level tokens (or the whole-passage fallback) rather than storing
  incorrect spans — the frontend local tokenizer remains the graceful degradation path.
- Tokens without the new `anatomy`/`concept_tags` fields (old format using a flat `tags`
  array) must still render: treat a flat `tags` array as `anatomy` for backward compat.

---

## Grammar Practice — Key Pill Color System

Each grammar key pill (both anatomy and concept) must have a unique hue so no two keys
share the same color. The darkness level coordinates with the pill's category so students
can tell at a glance whether a pill is a sentence structure key or a grammar concept key.

**Design rules:**

1. **Unique hues** — assign one hue from the HSL color wheel to each key. Spread all keys
   evenly across 0–359° so adjacent keys are visually distinct. With ~20 anatomy keys and
   ~60 concept keys (~80 total), the step between assigned hues is ~4.5°.

2. **Category darkness** — the lightness dimension signals category membership:

   | Category | Border / text color | Background (pill face) |
   |---|---|---|
   | Sentence Anatomy (`anatomy`) | `hsl(H, 50%, 32%)` — medium-dark, muted | `hsl(H, 40%, 93%)` — very light, low saturation |
   | Grammar Concepts (`concept_tags`) | `hsl(H, 70%, 26%)` — darker, richer | `hsl(H, 65%, 89%)` — slightly deeper, more saturated |

   Anatomy pills read as softer/structural. Concept pills read as richer/active. A student
   scanning the panel can tell the groups apart by overall brightness before reading labels.

3. **Hue allocation** — split the wheel between categories to prevent any anatomy hue from
   being too close to a concept hue:
   - Anatomy keys: hues **10°–178°** (warm-to-cool arc; ~20 keys, step ≈ 8°)
   - Concept keys: hues **182°–355°** (cool-to-warm arc; ~60 keys, step ≈ 3°)
   - The two arcs wrap in opposite directions so the brightest anatomy key (10°, red-orange)
     and the brightest concept key (355°, red) are close in hue but distinct in darkness.

4. **Active state** — when a pill is clicked/active, invert: use the `color` as the
   background and white as the text. Both categories should look clearly "on" regardless of
   their lightness tier.

5. **No repeats across sessions** — the hue assignment is deterministic and keyed to the
   key's string ID (not its list position), so the same key always gets the same hue even
   if new keys are added to the list later.

**Implementation notes:**

- Replace the hardcoded `color`/`lightBg` values in `SYNTAX_ANATOMY_KEYS`
  (`src/data/syntaxAnatomyKeys.ts`) with computed values from a shared `assignKeyColor(id,
  category)` utility function.
- The dynamic backend key generator in `useGrammarSession.ts` (currently uses
  `hsl(${hue} 65% 38%)`) must also call the same utility so dynamically-generated concept
  pills share the same system.
- `assignKeyColor(id, category)` — deterministic hue from a hash of `id` (so the same key
  always gets the same hue), then apply the saturation/lightness tier based on `category`.
  Use a simple string hash (e.g. djb2) mapped to the category's hue arc, not `Math.random()`.

**Approximate hue assignments (reference, not exhaustive):**

Anatomy (10°–178°, step ≈ 8°):
```
subject                  →  10°  (red-orange)
main_verb                →  18°  (orange)
verb_phrase              →  26°
prepositional_phrase     →  34°  (amber)
object                   →  42°
complement               →  50°  (yellow-green)
subordinating_conj       →  58°
subordinate_clause       →  68°  (green)
relative_clause          →  80°
appositive               →  92°  (teal-green)
modifier                 → 104°
absolute_phrase          → 114°  (teal)
conjunctive_adverb       → 124°
coordinating_conjunction → 134°  (cyan)
parallel_element         → 144°
transition_word          → 152°  (sky)
pronoun                  → 160°
antecedent               → 168°  (blue)
determiner               → 174°
punctuation_mark         → 178°  (indigo-adjacent)
```

Concept keys (182°–355°, step ≈ 3°) follow the same evenly-spaced pattern across all ~60
D.2 focus keys and ~11 D.5 trap keys in the order they appear in the concept key reference
above (sentence boundary → agreement → pronoun → verb form → modifier → punctuation →
parallel → expression of ideas → syntactic traps).

---

## Student App — Future Enhancements

Ideas not in current scope but worth tracking:

- [ ] **Spaced repetition** — resurface missed questions using SM-2 or similar algorithm instead of fixed resurface window
- [ ] **Progress over time** — chart student accuracy trend by week/month per domain
- [ ] **Full test simulation** — two-module adaptive test (mod01 → mod02 higher/lower based on mod01 score), with score estimate at the end
- [ ] **Passage-based questions** — student UI support for displaying passages alongside questions (currently grammar-only)
