# rules_agent_dsat_grammar_ingestion_generation_v8.md

## Purpose

This is the consolidated v8 production rule file for the DSAT grammar
ingestion and generation agent. It extends v7 with PT-cited sub-patterns
across all production grammar_focus_keys, layered on the v7 taxonomy
(unchanged). v7 itself extends v6 with taxonomy corrections and additions
derived from a cross-referenced audit against College Board official
documentation, Khan Academy, The Critical Reader, PrepScholar, Test Innovators,
Albert.io, and released practice tests PT1–PT11.

**v8 changes from v7:**

- B.3 expanded with PT-cited sub-patterns for every grammar_focus_key (max 3 per key, hard cap)
- Each sub-pattern carries a citation in format `(PT{exam} M{module} Q{number}: "short quote")` or a `[NO PT EVIDENCE — source: <web>]` marker
- Evidence tiers documented per focus key in §B.3.0 (Tier A ≥5 PT examples, B 1–4, C 0)
- Anti-rigidity preamble added at §B.3.0: sub-patterns are attested variants, not exhaustive templates. Generators MAY produce items matching no listed sub-pattern.
- `model_version` updated to `rules_agent_v8.0`
- No changes to taxonomy keys (D.1–D.9) — all additions are documentary, not classificatory
- v7 grammar_focus_key, grammar_role_key, syntactic_trap_key, and all distractor-mechanism keys carry over unchanged

**v7 source:** `rules_agent_dsat_grammar_ingestion_generation_v7.md`

The agent must not invent new taxonomy keys unless explicitly using the
amendment process (C.7).

---

# PART A — MODE ROUTING

---

## A.1 Operating Principles

### A.1.1 Separate the tasks

For every question, separate:

1. what the item tests
2. how the item is structured
3. what rule or reasoning mechanism solves it
4. why the correct answer is correct
5. why each wrong option is tempting
6. why each wrong option is wrong
7. what pattern should be used to generate a similar item

### A.1.2 Do not write directly to the database

The agent must output structured JSON or markdown records for validation. A
deterministic backend validator checks all keys before insertion.

### A.1.3 Use controlled keys

The agent must use only approved lookup keys from Part D. If no key fits, it
must propose an amendment (C.7) instead of inventing a new production key.

### A.1.4 Meaning over surface form

When grammar and meaning overlap, classify the item by the main reason the
correct answer is required.

### A.1.5 Official SAT alignment

For Standard English Conventions, classify according to:

- sentence boundaries
- form, structure, and sense
- grammar role
- grammar focus
- syntactic trap
- distractor mechanics

---

## A.2 Task Mode Detection

Determine mode from the request context before any other action. Do not mix
generation and annotation outputs in a single response.

### Generation Mode

Triggered when the request:

- contains a `generation_request` JSON block
- specifies a `target_grammar_focus_key` and asks for a new item
- asks to "generate," "create," or "write" a new grammar question
- asks to batch-generate a module or item set

**Action:** proceed to Part B.

### Annotation / Ingestion Mode

Triggered when the request:

- provides question text and answer options to classify
- asks to "annotate," "ingest," "classify," or "review" an existing item
- provides a raw PDF passage or already-structured question record

**Action:** proceed to Part C, then validate output against Part D.

### Ambiguous Requests

If the request contains both an existing question and a generation target,
process annotation first, then use the annotation output as the
`generation_profile` seed for the generation request.

---

## A.3 Required Output Shape and Formal Schemas

Every item must produce these five top-level sections:

```json
{
  "question": {},
  "classification": {},
  "options": [],
  "reasoning": {},
  "generation_profile": {},
  "review": {}
}
```

### `question` section schema

```json
{
  "source_exam": "PT4 | GENERATED",
  "source_section": "RW | S1 | S2",
  "source_module": "M1 | M2",
  "source_question_number": 1,
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text",
  "prompt_text": "...",
  "passage_text": "...",
  "paired_passage_text": null,
  "notes_bullets": [],
  "table_data": null,
  "graph_data": null,
  "correct_option_label": "B",
  "explanation_short": "...",
  "explanation_full": "...",
  "evidence_span_text": "..."
}
```

### `classification` section schema

```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Form, Structure, and Sense",
  "subskill": "subject-verb agreement with plural prepositional object",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "agreement",
  "grammar_focus_key": "subject_verb_agreement",
  "secondary_grammar_focus_keys": [],
  "passage_tokens": [
    {"word": "The", "tags": []},
    {"word": "researcher,", "tags": ["subject_verb_agreement", "nearest_noun_attraction"]},
    {"word": "who", "tags": []}
  ],
  "transition_subtype_key": null,
  "syntactic_trap_key": "nearest_noun_attraction",
  "evidence_scope_key": "sentence",
  "evidence_location_key": "main_clause",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "topic_broad": "science",
  "topic_fine": "...",
  "reading_scope": "sentence-level",
  "reasoning_demand": "rule application",
  "register": "neutral informational",
  "tone": "objective",
  "difficulty_overall": "medium",
  "difficulty_reading": "low",
  "difficulty_grammar": "medium",
  "difficulty_inference": "low",
  "difficulty_vocab": "low",
  "distractor_strength": "high",
  "disambiguation_rule_applied": null,
  "classification_rationale": "..."
}
```

### `reasoning` section schema

```json
{
  "primary_rule": "The grammar rule that selects the correct answer.",
  "trap_mechanism": "How the syntactic trap misleads test-takers.",
  "correct_answer_reasoning": "Step-by-step justification for the correct option.",
  "distractor_analysis_summary": "One-sentence summary of why the three wrong options fail.",
  "similar_items": [
    {
      "pattern": "sentence template describing the structural pattern",
      "focus_key": "grammar_focus_key",
      "trap_key": "syntactic_trap_key"
    }
  ]
}
```

### `generation_profile` section schema

```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "high",
  "target_frequency_band": "very_high",
  "target_distractor_pattern": [
    "one nearest-noun plural verb distractor",
    "one plural auxiliary distractor",
    "one unnecessary progressive distractor"
  ],
  "passage_template": "The [singular collective noun] of [plural noun], [relative clause], ______ [role/action].",
  "test_format_key": "digital_app_adaptive",
  "source_stats_format": "official_digital",
  "generation_timestamp": "2026-04-29T00:00:00Z",
  "model_version": "rules_agent_v8.0"
}
```

### `review` section schema

```json
{
  "annotation_confidence": 0.95,
  "needs_human_review": false,
  "review_notes": "Any ambiguity or concern about the classification."
}
```

---

# PART B — GENERATION

---

## B.1 Generation Input Specification

```json
{
  "generation_request": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "difficulty_overall": "medium",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs two more medium-difficulty subject-verb agreement items.",
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital"
  }
}
```

**`test_format_key` values:**

| Value | Module length | When to use |
|---|---|---|
| `digital_app_adaptive` | 27 questions | Default; standard Bluebook adaptive digital SAT |
| `nondigital_linear_accommodation` | 33 questions | Paper accommodation format; PT4–PT11 source tests |

**`source_stats_format` values:**

| Value | Description |
|---|---|
| `official_digital` | Position statistics from Bluebook adaptive modules |
| `official_nondigital_linear` | Position statistics from PT4–PT11 paper accommodation modules |

When `test_format_key` is `nondigital_linear_accommodation`, use 33 questions
and these domain-band position ranges (observed PT4–PT11):

```
Reading / Craft / Information:     Q1–Q18  (±1)
Standard English Conventions:      Q19–Q26 (±1; may start as late as Q18 in M2)
Transitions:                        Q27–Q30 (variable; 1–5 items)
Notes Synthesis:                    Q30–Q33 (variable start; always ends at Q33)
```

The validator must reject any 33-question module with
`test_format_key: "digital_app_adaptive"` and any 27-question module with
`test_format_key: "nondigital_linear_accommodation"`.

Reject any request that uses an unapproved `grammar_focus_key`, maps a focus
key to the wrong role, or requests a `very_low` frequency item without
explicit justification.

### B.1.1 Mandatory generation input fields

- `target_grammar_focus_key` (must match an approved key from D.2)
- `target_grammar_role_key` (must map correctly per D.8.1)
- `target_frequency_band` (not `very_low` without justification)
- `difficulty_overall`
- `test_format_key`
- `stimulus_mode_key`
- `stem_type_key`

For `transition_logic` items, also required:

- `target_transition_subtype_key` (from B.5.2)
- `distractor_transition_subtypes` (array of three values from B.5.2)

For `choose_best_notes_synthesis` items, also required:

- `target_synthesis_goal_key` (from B.6.2)
- `target_audience_knowledge_key` (from B.6.3)
- `target_required_content_key` (from B.6.4)
- `distractor_synthesis_failures` (array of three values from B.6.5)

---

## B.2 Step-by-Step Generation Workflow

Each step is blocking. Maximum 3 retries per component. After 3 failures,
abort and return the error response from B.14.

### Step 1: Validate the generation request

Confirm all mandatory fields are present. Confirm `grammar_focus_key` maps
to `grammar_role_key` per D.8.1. Reject `very_low` frequency items without
justification.

### Step 2: Generate the passage sentence

20–40 words for `sentence_only`; 80–150 for passage excerpts. Formal
academic register, self-contained, error location unambiguous.

Name the syntactic trap before writing the passage. Choose a passage
architecture key from B.7 if stimulus is passage-length.

### Step 3: Generate the stem

Standard SAT stem for SEC:
> "Which choice completes the text so that it conforms to the conventions
> of Standard English?"

Standard SAT stem for transitions:
> "Which choice completes the text with the most logical transition?"

Standard SAT stem for notes synthesis:
> "The student wants to [goal]. Which choice most effectively uses
> relevant information from the notes to accomplish this goal?"

### Step 4: Generate the correct option

Grammatically flawless, resolves the trap, preserves register and meaning.

### Step 5: Generate three distractors

Each must have a distinct `student_failure_mode_key`. At least one must
target the declared syntactic trap. No two distractors may share the same
`option_error_focus_key`. No unintended second error in any distractor.

Consult B.4 for distractor heuristics by focus key.

### Step 6: Assemble all metadata

Populate all required fields per D.9.

### Step 7: Run the validation checklist

Run all 25 checks from B.13 before emitting output.

---

## B.3.0 Sub-Pattern Policy and Evidence Tiers

### B.3.0.1 What sub-patterns are

Sub-patterns are *attested trap variants* observed in official DSAT practice
tests or documented in verified prep sources (College Board, Khan Academy,
The Critical Reader, PrepScholar, Albert.io, Test Innovators). They are
documentary, not classificatory: every sub-pattern resolves to the parent
`grammar_focus_key` and an existing `syntactic_trap_key` from D.5. Sub-patterns
do not create new keys.

### B.3.0.2 Sub-patterns are not rails

Sub-patterns are examples of variation, not an exhaustive menu. **Generators
MAY produce items that match no listed sub-pattern** as long as the canonical
construction for the focus key is honored, distractors target distinct failure
modes, and B.13 validation passes. Annotators MAY classify items that match no
listed sub-pattern; the sub-pattern field is descriptive, not required.

### B.3.0.3 Citation format

Every sub-pattern carries either:

1. A PT citation: `(PT{exam} M{module} Q{number}: "short quote")`
   Example: `(PT7 M2 Q14: "a toxin that is deadly to nematodes that comes in contact with it")`
2. A web-source marker: `[NO PT EVIDENCE — source: <name>]` when no calibration-set example exists.

### B.3.0.4 Hard cap

Maximum 3 sub-patterns per `grammar_focus_key`. Adding a fourth requires
demoting one. Use the v7→v8 generation log to track demotions.

### B.3.0.5 Evidence tiers

Each focus key is assigned a tier in §B.3.0.6 based on PT example count in
`analysis/calibration/official_classifications.json` as of the v8 cut.

| Tier | PT examples | Sub-pattern policy |
|---|---|---|
| A | ≥5 | All 3 sub-patterns PT-cited |
| B | 1–4 | At least 1 PT-cited; remainder may be web-only |
| C | 0 | All web-only with `[NO PT EVIDENCE]` markers |

Tier C sub-patterns should be re-promoted to Tier B/A as new PT examples are
classified. Re-tiering does not require a version bump; it can be done as a
patch.

### B.3.0.6 Tier table (as of v8 cut, 2026-05-23)

| Focus key | Tier | PT examples |
|---|---|---|
| `transition_logic` | A | 60 |
| `subject_verb_agreement` | A | 23 |
| `logical_relationships` | A | 22 |
| `verb_tense_consistency` | A | 17 |
| `punctuation_comma` | A | 12 |
| `unnecessary_internal_punctuation` | A | 9 |
| `appositive_punctuation` | A | 8 |
| `sentence_boundary` | A | 8 |
| `pronoun_antecedent_agreement` | A | 7 |
| `logical_predication` | A | 6 |
| `comma_splice` | A | 5 |
| `end_punctuation_question_statement` | A | 5 |
| `semicolon_use` | A | 5 |
| `conjunctive_adverb_usage` | B | 4 |
| `colon_dash_use` | B | 3 |
| `sentence_fragment` | B | 3 |
| `verb_form` | B | 3 |
| `possessive_contraction` | B | 2 |
| `precision_word_choice` | B | 2 |
| `register_style_consistency` | B | 2 |
| `data_interpretation_claims` | B | 1 |
| `emphasis_meaning_shifts` | B | 1 |
| `preposition_idiom` | B | 1 |
| `pronoun_case` | B | 1 |
| `relative_pronouns` | B | 1 |
| `run_on_sentence` | B | 1 |
| `adjective_adverb_distinction` | C | 0 |
| `affirmative_agreement` | C | 0 |
| `apostrophe_use` | C | 0 |
| `commonly_confused_words` | C | 0 |
| `comparative_structures` | C | 0 |
| `conjunction_usage` | C | 0 |
| `determiners_articles` | C | 0 |
| `elliptical_constructions` | C | 0 |
| `hyphen_usage` | C | 0 |
| `illogical_comparison` | C | 0 |
| `modifier_placement` | C | 0 |
| `negation` | C | 0 |
| `noun_countability` | C | 0 |
| `parallel_structure` | C | 0 |
| `pronoun_clarity` | C | 0 |
| `quotation_punctuation` | C | 0 |
| `redundancy_concision` | C | 0 |
| `voice_active_passive` | C | 0 |

### B.3.0.7 Web source allowlist

Sub-patterns marked `[NO PT EVIDENCE]` must cite a source from this allowlist:

| Source | Use for |
|---|---|
| College Board (collegeboard.org, Bluebook docs) | Authoritative sub-pattern naming |
| Khan Academy SAT R&W course | Skill family taxonomy, sub-pattern names |
| The Critical Reader (Erica Meltzer) | Trap mechanism descriptions |
| PrepScholar | Sub-pattern frequency and examples |
| Albert.io | Distractor pattern catalogs |
| Test Innovators | DSAT-specific item structure |

Manhattan Review, PrepMaven, UWorld, and TestPrepKart may be used as cross-reference but should not be the sole source.

---

## B.3 Passage Construction Rules by Grammar Focus

### `subject_verb_agreement`

Use a singular collective, abstract, or inverted subject. Insert a plural
prepositional object or appositive between subject and verb.

**Sub-pattern — Intervening Phrase Between Subject and Verb**

(PT10 M2 Q24: "Mathematician Grigori Perelman, sometimes in conjunction with mathematicians")

Construct a singular subject and separate it from the verb with a prepositional
phrase or appositive containing one or more plural attractor nouns. The blank
sits at the verb slot, far enough from the head noun that the reader's working
memory latches onto the nearer plural. The genuine subject must still control
number.

Distractors: offer plural verb forms that agree with the most recent plural
noun inside the intervening phrase, plus a tense-mismatched plural form.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Gerund or Nominalization as Singular Subject**

(PT5 M1 Q22: "Using copyrighted songs without permission")

Construct an `-ing` gerund phrase or an abstract nominalization
("her writing," "the frog's range") as the subject. The gerund head looks
verb-like and often governs a plural object inside the phrase, tempting the
reader to read the whole subject as plural. The required verb is singular.

Distractors: plural verb forms (and a non-finite distractor such as a
participle) that match the embedded plural object inside the gerund phrase.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Relative Pronoun with Quantifier-Partitive Antecedent**

(PT9 M2 Q21: "biomedical scientists—many of whom")

Construct a plural noun followed by a partitive or quantifier phrase ("many of
whom," "each one of which," "one of those that") that introduces a relative
clause; the blank is the verb inside that relative clause. The verb must agree
with the plural antecedent of the relative pronoun, not with the singular
quantifier word ("one," "each," "many") that sits immediately before the
pronoun.

Distractors: singular verb forms that agree with the nearer quantifier word,
plus one form that agrees with an unrelated singular noun earlier in the
sentence.

Classify with `syntactic_trap_key: "long_distance_dependency"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

### `pronoun_antecedent_agreement`

Use a singular antecedent that looks plural ("the team," "everyone"). Place a
plural noun nearby.

### `verb_tense_consistency`

Open with a time marker. Place a distractor tense that matches a nearby
noun's temporal implication.

**Literary register variant:** Frame as discussion of a named literary work.
Target verb describes a character's action or the text's pattern. Correct
option: simple present. Wrong options: simple past, present perfect, past
perfect. Classify with `passage_tense_register_key: "literary_present"`.

**Secondary trap patterns:**
- *Scientific-present interrupted by historical narrative* — passage mixes
  present-tense scientific generalization with a past-tense anecdote; the blank
  straddles the boundary. Distractors import the anecdote's past tense into the
  general claim.
- *Past-perfect time shift* — two sequenced past events require past perfect for
  the earlier one ("By the time X occurred, Y **had established/established**
  the pattern"). Distractors offer simple past, conflating temporal ordering.

### `verb_form`

Use the umbrella `verb_form` focus when the tested convention is finite vs.
nonfinite form, modal-governed base form, auxiliary construction, or verb form
after an opening phrase rather than tense alone. Prefer one of the documented
subpatterns below: `finite_verb_in_relative_clause`,
`finite_verb_in_main_clause`, or `modal_plus_plain_form`.

Correct option: the only verb form that can serve the required syntactic role.
Wrong options: participle, infinitive, inflected form after a modal, or a verb
form that leaves the sentence without a finite main predicate.

### `modifier_placement` / `dangling_modifier`

Start with a participial phrase whose logical subject is not the grammatical
subject.

### `punctuation_comma`

Create a compound sentence with or without a coordinating conjunction. Test
FANBOYS comma, introductory phrase comma, or nonrestrictive element comma.

**Secondary trap patterns:**
- *Introductory-clause comma* — open with a subordinate clause ("Although the
  study was small, **[blank]** the results were significant"). Distractors omit
  the comma or place it mid-clause. Classify with
  `syntactic_trap_key: "early_clause_anchor"` and note
  `punctuation_subpattern: "introductory_clause_comma"`.
- *Nonrestrictive-element comma* — embed an optional relative clause or
  participial phrase ("The researcher, **who had studied the region for a
  decade**, concluded…"). Distractors make the element restrictive by omitting
  one or both commas. Classify with
  `syntactic_trap_key: "modifier_attachment_ambiguity"` and note
  `punctuation_subpattern: "nonrestrictive_element_comma"`.

### `semicolon_use`

Use two closely related independent clauses. Place a transitional phrase
after the semicolon zone.

**Secondary trap patterns:**
- *Conjunctive adverb pattern* — place a conjunctive adverb ("however,"
  "therefore," "consequently") between the two independent clauses: "The data
  were inconclusive**; however,** the team proceeded." The required form is
  semicolon before + comma after the adverb. Distractors use a comma-only
  splice before the adverb, or omit the post-adverb comma, or replace the
  semicolon with a colon. Classify with
  `syntactic_trap_key: "early_clause_anchor"` and note
  `punctuation_subpattern: "conjunctive_adverb_semicolon"`.

### `apostrophe_use`

Use a plural possessive or a possessive pronoun that looks like a
contraction.

### `appositive_punctuation`

Use a noun phrase that renames an adjacent noun. Test comma vs no comma for
essential vs nonessential appositive.

**Sub-pattern A — restrictive appositive:**
When an appositive uniquely identifies its antecedent, no punctuation
surrounds it. Example: "the chemical compound aluminum oxide" — no commas.

**Sub-pattern B — title/role noun before proper name:**
When a professional title immediately precedes a proper name as a restrictive
identifier, no comma separates them. Example: "plant cell biologist Yuree Lee."

**Sub-pattern C — coordinated restrictive appositive:**
Two restrictive appositives joined by "and" take no surrounding punctuation.
Example: "the writer and scholar James Baldwin."

Distractor pattern for restrictive sub-patterns:

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma before proper name after title/role | `punctuation_style_bias` |
| 2 | Commas around restrictive appositive | `grammar_fit_only` |
| 3 | Dash before restrictive appositive | `formal_register_match` |

### `relative_pronouns`

Use a clause that is either essential or nonessential. Test `that` vs
`which` or comma placement.

### `colon_dash_use`

Create a sentence where an independent clause is followed by an explanation,
list, or elaboration.

### `conjunctive_adverb_usage`

Join two independent clauses with a conjunctive adverb.

### `parallel_structure`

Create a list or correlative construction where one element breaks form
symmetry.

### `pronoun_case`

Use a compound subject or object where pronoun case is tested.

### `pronoun_clarity`

Create a sentence with multiple possible antecedents for a pronoun.

### `possessive_contraction`

Use a context where `it's` vs `its` or `who's` vs `whose` is tested.

### `hyphen_usage`

Use a compound modifier before a noun where hyphenation is required.

### `logical_predication`

Create a sentence where the subject and predicate are grammatically possible
but logically incompatible.

### `comparative_structures`

Create a comparison where the things being compared are not grammatically
parallel.

### `unnecessary_internal_punctuation`

Insert a comma or dash at one of these five positions:

1. between subject and main verb
2. between transitive verb and its direct object
3. between verb and subject complement
4. between preposition and its noun complement
5. inside an integrated relative clause before the verb

Correct option: no punctuation at the target boundary.
Wrong options: comma, dash, or colon at the forbidden location.

### `end_punctuation_question_statement`

**Variant A — indirect question embedded in declarative:**
Use a main clause like "The researchers wondered / asked / considered"
followed by a subordinate question clause. Correct: period. Wrong options:
question mark, comma with no end mark.

**Variant B — coordinated direct questions:**
Use two question clauses joined by "or" or "and." Correct: single question
mark. Wrong options: period, comma, question mark after each clause.

### `finite_verb_in_relative_clause`

Construct a sentence where a relative clause (introduced by "which," "that,"
or "who") requires a finite verb. Wrong options substitute a nonfinite
participle or infinitive.

Template:
`[Noun phrase], which ______ [object or complement], [main verb phrase].`

Correct option: finite verb agreeing with the relative pronoun's antecedent.
Wrong options: nonfinite -ing participle, bare past participle, infinitive.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"`.

### `finite_verb_in_main_clause`

Construct a sentence where the main clause requires a finite verb but wrong
options offer nonfinite forms. Common trigger: an opening subordinate clause
or participial phrase that tempts continued nonfinite structure.

Template:
`[Opening subordinate clause or participial phrase], [Subject] ______ [object].`

Correct option: finite present or past tense verb.
Wrong options: -ing participle, past participle without auxiliary, infinitive.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"`.

### `modal_plus_plain_form`

Construct a sentence where a modal auxiliary (would, could, should, might,
must, will, can, shall) governs the main verb. Wrong options offer inflected
forms after the modal.

Template:
`[Subject] would/could/should/might ______ [object or complement].`

Shared-helping-verb trap:
Use a coordinated verb phrase where the modal auxiliary appears before the
first verb but governs both verbs joined by "and." The second coordinated verb
must also be plain/base form, even though the auxiliary is not repeated.

Template:
`[Subject] would/could/should/might [plain verb] [object] and ______ [object or complement].`

Correct option: plain (base) form of the second coordinated verb.
Wrong options: past tense, third-person singular, gerund, or participle that
incorrectly treats the second verb as independent of the shared modal.

Correct option: plain (base) form of the verb.
Wrong options: third-person singular inflected, past tense, continuous.

Classification: `grammar_role_key: "verb_form"`, `grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "none"`.

### `singular_event_reference` (pronoun)

Construct a sentence where the pronoun refers back to an entire preceding
event, fact, or clause. The pronoun must be singular ("this," "it," "that").
Wrong options offer plural pronouns or ambiguous pronouns.

Template:
`[Complete prior event stated as a sentence or clause]. ______ [effect or significance].`

Correct pronoun: singular "this," "it," or "that."
Wrong options: plural pronoun, ambiguous pronoun, pronoun with wrong case.

Annotation note: Use `grammar_role_key: "pronoun"`,
`grammar_focus_key: "pronoun_antecedent_agreement"`, and add to
`review_notes`: "antecedent is a full clause/event, not a noun."

### `sentence_boundary`

Use this umbrella focus only when the item tests whether clauses should be
joined, separated, or completed, but the official source does not cleanly map to
only `sentence_fragment`, `comma_splice`, or `run_on_sentence`. Build the item
around two clause units whose independence must be diagnosed.

Correct option: produces one or more complete, correctly bounded sentences.
Wrong options: create a fragment, comma splice, fused sentence, or boundary that
breaks an essential modifier from its clause.

**Sub-pattern — appositive-comma illusion masking a sentence boundary:**
Use a first sentence ending in a noun phrase, followed by a second sentence that
begins with a capitalized appositive-like noun phrase and then continues into a
main clause. The tempting distractor attaches the second sentence with a comma
because the opening noun phrase appears to rename the prior noun, but the
following main clause makes the comma choice a comma splice. The correct option
uses a period or another valid sentence boundary. Classify with
`grammar_focus_key: "sentence_boundary"` or `"comma_splice"` depending on
the final error, keep `syntactic_trap_key` at the closest approved broad key
or `"none"`, and use `student_failure_mode_key: "comma_fix_illusion"` with a
review note naming this subpattern.

### `sentence_fragment`

Subordinate clause presented as a complete sentence.

### `comma_splice`

Two independent clauses joined with only a comma.

### `run_on_sentence`

Two independent clauses fused with no punctuation or conjunction.

### `noun_countability`

Mass noun with plural article or vice versa.

### `determiners_articles`

Article where none is needed, or omitted required article.

### `affirmative_agreement`

`so` / `neither` / `nor` responses with inverted auxiliary matching.

### `voice_active_passive`

Active/passive voice creates ambiguity or inconsistency.

### `negation`

Negation placed where scope ambiguity creates multiple interpretations.

### `logical_predication`

Subject-predicate incompatibility.

### `quotation_punctuation`

Comma placement with quotation marks.

### `transition_logic`

Two adjacent sentences with a logical relationship that must be named
precisely. Place the blank at the transition position. See B.5 for the full
subtype vocabulary. Choose distractor transitions from different relationship
families (contrast, causal, additive, etc.) so each wrong option tests a
distinct confusion.

### `choose_best_notes_synthesis`

Provide 3–5 bullet-note facts covering a research study, historical figure,
or literary work. Write a stem specifying the rhetorical goal. See B.6 for
metadata fields. Each distractor must fail via a distinct
`synthesis_distractor_failure` value.

### `redundancy_concision`

Construct a sentence where several options express the same core idea with
different amounts of repetition or unnecessary wording. The correct answer is
the most concise option that preserves all required meaning and logical
relationships.

Wrong options repeat a noun or idea already present, add a redundant modifier,
or delete a necessary qualifier while becoming shorter.

### `precision_word_choice`

Create a context where several real words share a broad semantic field but only
one has the exact denotation, connotation, or selectional fit required by the
sentence. Do not use commonly confused pair items here; those belong to
`commonly_confused_words`.

Wrong options are grammatically viable and topic-related but too broad, too
strong, too weak, or mismatched to the noun/verb they modify.

### `register_style_consistency`

Use a formal academic sentence or passage with a blank where only one option
matches the established register, stance, and idiomatic style. The correct
option should be natural in College Board explanatory prose.

Wrong options include conversational phrasing, inflated pseudo-academic diction,
technical diction from the wrong field, or a tone shift that clashes with the
surrounding passage.

### `logical_relationships`

Construct adjacent clauses or sentences where the blank must preserve a cause,
contrast, concession, condition, example, or continuation relationship. Use this
focus when the tested expression is not a standalone transition word covered by
`transition_logic`.

Wrong options signal the wrong relationship, reverse cause and effect, overstate
certainty, or connect two ideas that the passage keeps separate.

### `emphasis_meaning_shifts`

Create a sentence where word order, modifier placement, or phrase choice changes
what information is emphasized. The correct option foregrounds the fact named in
the stem without changing the underlying claim.

Wrong options are factually compatible but emphasize the wrong actor, quantity,
contrast, time period, or implication.

### `data_interpretation_claims`

Use a short table, graph, or data description with a sentence that must
accurately state a claim supported by the data. The correct option names the
right variable, group, direction, and constraint.

Wrong options cite real values while using the wrong comparison, wrong group,
wrong time window, or wrong proportional/absolute interpretation.

### `conjunction_usage`

Build a sentence where a subordinating, coordinating, or correlative conjunction
determines the logical relation between clauses. The correct option supplies the
only conjunction or paired conjunction that preserves the intended relationship
and syntax.

Wrong options are grammatically possible but signal the wrong relation, leave a
correlative pair incomplete, or create a clause-type mismatch.

### `elliptical_constructions`

Use a comparison or parallel structure where repeated words are omitted
legitimately only if the remaining structure is still recoverable and parallel.
The correct option preserves the omitted material's role without ambiguity.

Wrong options omit too much, omit from only one side of a comparison, or create
an elliptical phrase whose missing words would not match the prior structure.

### `comparative_structures`

Use two items in an explicit "more/less/better than" comparison where one element is a noun and the other is an action, process, or dissimilar form. The trap: students do not notice the compared terms are structurally mismatched.

Correct option: uses "that of" or "those of" or a matched parallel noun form.
Wrong options: preserve the bare unparalleled comparison in varied surface forms.

### `illogical_comparison`

Construct a sentence comparing a noun directly to an action, process, or dissimilar category (e.g., "the revenue of Company X exceeded Company Y"). The error is logical, not formal: both elements exist but they belong to different categories.

Correct option: inserts "that of" or restructures so both compared items are the same grammatical and logical category.
Wrong options: preserve the illogical pairing in different surface wordings.

Classification: `grammar_role_key: "modifier"`, `grammar_focus_key: "illogical_comparison"`.

### `adjective_adverb_distinction`

**Variant A — linking verb:** Use a linking verb (appear, feel, seem, remain, become, look, sound, taste, smell) followed by the blank. Correct option: adjective (subject complement). Wrong options: adverb, comparative adverb, past participle.

**Variant B — action verb:** Use an action verb followed by a manner blank. Correct option: adverb. Wrong options: adjective, comparative adjective, noun phrase.

Classification: `grammar_role_key: "modifier"`, `grammar_focus_key: "adjective_adverb_distinction"`.

### `commonly_confused_words`

Select one pair of commonly confused non-homophone words:
`affect/effect`, `principle/principal`, `allusion/illusion`, `elicit/illicit`, `imply/infer`, `complement/compliment`, `compose/comprise`, `disinterested/uninterested`, `emigrate/immigrate`.

Write a passage where the meaning distinction is essential to the sentence. Wrong options present the other member(s) of the confused pair plus one additional plausible but incorrect option.

Do NOT use homophone possession pairs (its/it's, whose/who's) — those belong to `possessive_contraction`.

Classification: `grammar_role_key: "expression_of_ideas"`, `grammar_focus_key: "commonly_confused_words"`.

### `preposition_idiom`

Construct a sentence with a verb-preposition or adjective-preposition collocation where the correct preposition is idiomatic: `composed of`, `differ from`, `responsible for`, `interested in`, `capable of`, `independent of`, `account for`, `result in`, `consistent with`, `conducive to`.

Wrong options substitute near-correct prepositions that are grammatically viable but idiomatically non-standard ("composed in," "differ with," "responsible to," "account on").

Classification: `grammar_role_key: "expression_of_ideas"`, `grammar_focus_key: "preposition_idiom"`.

---

## B.4 Distractor Generation Heuristics by Grammar Focus

### `subject_verb_agreement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Plural verb (nearest noun attraction) | `nearest_noun_attraction` |
| 2 | Singular verb but wrong tense | `auditory_similarity` |
| 3 | Compound or auxiliary verb that breaks agreement | `grammar_fit_only` |

### `verb_tense_consistency`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Tense matching a nearby temporal noun | `auditory_similarity` |
| 2 | Present perfect when simple past is required | `formal_register_match` |
| 3 | Conditional/future that sounds sophisticated | `grammar_fit_only` |

### `punctuation_comma`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Missing comma (comma splice or run-on) | `punctuation_style_bias` |
| 2 | Unnecessary comma (before essential clause) | `grammar_fit_only` |
| 3 | Semicolon where comma is correct | `formal_register_match` |

### `semicolon_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma splice | `punctuation_style_bias` |
| 2 | Colon instead of semicolon | `formal_register_match` |
| 3 | Period that creates a fragment | `grammar_fit_only` |

### `apostrophe_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | No apostrophe (plural instead of possessive) | `auditory_similarity` |
| 2 | Apostrophe after s (wrong singular possessive) | `nearest_noun_attraction` |
| 3 | Apostrophe in a pronoun (it's vs its) | `common_idiom_pull` |

### `modifier_placement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Modifier placed next to wrong noun | `nearest_noun_attraction` |
| 2 | Modifier split from its head noun | `grammar_fit_only` |
| 3 | Dangling modifier preserved | `formal_register_match` |

### `relative_pronouns`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | `which` without comma for essential clause | `punctuation_style_bias` |
| 2 | `that` with comma for nonessential clause | `grammar_fit_only` |
| 3 | `who` for inanimate antecedent | `nearest_noun_attraction` |

### `colon_dash_use`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma instead of colon/dash | `punctuation_style_bias` |
| 2 | Semicolon where colon is required | `formal_register_match` |
| 3 | No punctuation (run-on elaboration) | `grammar_fit_only` |

### `appositive_punctuation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma around essential appositive | `punctuation_style_bias` |
| 2 | No comma around nonessential appositive | `grammar_fit_only` |
| 3 | Dash where comma is sufficient | `formal_register_match` |

### `parallel_structure`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Gerund where infinitive is required | `grammar_fit_only` |
| 2 | Noun phrase where verb phrase is required | `nearest_noun_attraction` |
| 3 | Prepositional phrase that breaks parallelism | `formal_register_match` |

### `pronoun_case`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Subject pronoun in object position | `nearest_noun_attraction` |
| 2 | Reflexive pronoun where simple object is required | `formal_register_match` |
| 3 | Possessive pronoun where object pronoun is required | `common_idiom_pull` |

### `conjunctive_adverb_usage`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma only (comma splice) | `punctuation_style_bias` |
| 2 | Period before conjunctive adverb with lowercase | `grammar_fit_only` |
| 3 | Semicolon but no comma after adverb | `formal_register_match` |

### `unnecessary_internal_punctuation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma between subject and verb | `punctuation_style_bias` |
| 2 | Dash between subject and verb | `formal_register_match` |
| 3 | Comma between verb and object/complement | `grammar_fit_only` |

### `end_punctuation_question_statement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Question mark on an indirect question | `punctuation_style_bias` |
| 2 | Comma after the main clause, no end mark | `punctuation_style_bias` |
| 3 | Period on a coordinated direct question | `formal_register_match` |

### `pronoun_antecedent_agreement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Plural pronoun for singular collective antecedent ("team," "everyone") | `nearest_noun_attraction` |
| 2 | Reflexive pronoun where simple personal pronoun is required | `formal_register_match` |
| 3 | Singular masculine/feminine pronoun where gender-neutral is required | `grammar_fit_only` |

### `pronoun_clarity`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Ambiguous pronoun with two plausible antecedents in adjacent clauses | `nearest_noun_attraction` |
| 2 | Pronoun that refers to a noun three or more clauses back | `formal_register_match` |
| 3 | Implied antecedent that does not appear as an explicit noun in the sentence | `grammar_fit_only` |

### `hyphen_usage`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | No hyphen in compound modifier before noun ("well known scientist") | `punctuation_style_bias` |
| 2 | Hyphen after adverb ending in -ly ("rapidly-changing") | `grammar_fit_only` |
| 3 | Hyphen in predicative position where none is required ("the results were well-known") | `formal_register_match` |

### `quotation_punctuation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma placed outside the closing quotation mark | `punctuation_style_bias` |
| 2 | No comma before attribution after a direct quotation | `grammar_fit_only` |
| 3 | Colon before a short embedded quotation requiring only a comma | `formal_register_match` |

### `logical_predication`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Nominalized subject produces a predicate that cannot logically apply to it | `formal_register_match` |
| 2 | Passive construction masks the logical mismatch | `formal_register_match` |
| 3 | Wordy prepositional phrase disguises the predication error | `grammar_fit_only` |

### `comparative_structures`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | "Than" used without a parallel noun form for the second compared element | `nearest_noun_attraction` |
| 2 | "As" begins a comparison but the construction is not completed with a second "as" | `grammar_fit_only` |
| 3 | Implied second comparison term that is too ambiguous to identify | `formal_register_match` |

### `illogical_comparison`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Compares noun to action or process directly (bare illogical comparison) | `nearest_noun_attraction` |
| 2 | Inserts pronoun ("that") but applies it to the wrong antecedent | `grammar_fit_only` |
| 3 | Restructures sentence but introduces a new mismatch between compared categories | `formal_register_match` |

### `adjective_adverb_distinction`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Adverb form after linking verb (e.g., "feels badly") | `auditory_similarity` |
| 2 | Adjective form after action verb (e.g., "worked careful") | `grammar_fit_only` |
| 3 | Comparative form of the wrong class (e.g., "more carefully" after a linking verb where "more careful" is required) | `formal_register_match` |

### `commonly_confused_words`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Primary confused partner (same or similar sound, categorically different meaning) | `auditory_similarity` |
| 2 | Secondary word from the same semantic area but wrong specific meaning | `grammar_fit_only` |
| 3 | Plausible synonym that is imprecise in context | `formal_register_match` |

### `preposition_idiom`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Near-correct preposition that forms a real but wrong idiom with the governing word | `common_idiom_pull` |
| 2 | Preposition from a closely related but distinct construction the student knows | `formal_register_match` |
| 3 | Grammatically viable preposition that creates a non-standard collocation | `grammar_fit_only` |

### `sentence_boundary`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Complete clause attached with only a comma | `punctuation_style_bias` |
| 2 | Clause boundary omitted entirely | `grammar_fit_only` |
| 3 | Period or semicolon inserted where the following material is not independent | `formal_register_match` |
| 4 | Appositive-looking phrase attached with comma, but following main clause creates comma splice | `comma_fix_illusion` |

### `sentence_fragment`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Subordinate clause punctuated as a sentence | `punctuation_style_bias` |
| 2 | Participial phrase presented as a complete clause | `grammar_fit_only` |
| 3 | Appositive or relative clause detached from the noun it modifies | `formal_register_match` |

### `comma_splice`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Two independent clauses joined by comma alone | `punctuation_style_bias` |
| 2 | Comma plus conjunctive adverb without semicolon or period | `formal_register_match` |
| 3 | Comma before a transition that cannot coordinate clauses | `grammar_fit_only` |
| 4 | Appositive-comma illusion where the comma appears to introduce a renaming phrase but actually joins two clauses | `comma_fix_illusion` |

### `run_on_sentence`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Two independent clauses fused with no punctuation | `grammar_fit_only` |
| 2 | Coordinating conjunction omitted between two parallel clauses | `nearest_noun_attraction` |
| 3 | Long sentence sounds polished but contains no legal boundary | `formal_register_match` |

### `verb_form`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Nonfinite participle where a finite main or relative-clause verb is required | `grammar_fit_only` |
| 2 | Inflected verb after a modal auxiliary, including a second coordinated verb governed by a shared modal | `auditory_similarity` |
| 3 | Bare infinitive or past participle that leaves the clause without a predicate | `grammar_fit_only` |

### `voice_active_passive`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Passive voice reverses or hides the agent required by context | `formal_register_match` |
| 2 | Active voice assigns the action to the wrong noun | `nearest_noun_attraction` |
| 3 | Passive auxiliary tense does not match the sentence's time frame | `grammar_fit_only` |

### `negation`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Negator scopes over the wrong clause or phrase | `grammar_fit_only` |
| 2 | Double negative reverses intended polarity | `grammar_fit_only` |
| 3 | Concessive wording sounds logical but cancels the intended contrast | `formal_register_match` |

### `possessive_contraction`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Contraction where possessive determiner is required | `auditory_similarity` |
| 2 | Possessive determiner where contraction is required | `grammar_fit_only` |
| 3 | Wrong possessive/contraction pair with the same sound pattern | `common_idiom_pull` |

### `noun_countability`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Plural count form used for a mass noun | `auditory_similarity` |
| 2 | Singular article used before an uncountable noun | `grammar_fit_only` |
| 3 | Quantifier fits nearby noun but not the head noun | `nearest_noun_attraction` |

### `determiners_articles`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Definite article where a generic or first-mentioned noun needs no article | `formal_register_match` |
| 2 | Missing article before a singular count noun | `grammar_fit_only` |
| 3 | Demonstrative or quantifier agrees with the nearest noun but not the head noun | `nearest_noun_attraction` |

### `affirmative_agreement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | "So/neither/nor" response uses the wrong auxiliary | `auditory_similarity` |
| 2 | Response polarity does not match the preceding clause | `grammar_fit_only` |
| 3 | Subject-auxiliary inversion omitted after agreement expression | `grammar_fit_only` |

### `conjunction_usage`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Subordinating conjunction signals the wrong logical relation | `formal_register_match` |
| 2 | Correlative conjunction pair is mismatched or incomplete | `grammar_fit_only` |
| 3 | Coordinating conjunction joins unequal clause types | `nearest_noun_attraction` |

### `elliptical_constructions`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Omitted words cannot be recovered from the parallel structure | `grammar_fit_only` |
| 2 | Ellipsis makes the second comparison term ambiguous | `grammar_fit_only` |
| 3 | Surface parallelism hides a missing required preposition or auxiliary | `formal_register_match` |

### `redundancy_concision`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Repeats information already stated in the sentence | `grammar_fit_only` |
| 2 | Sounds official but adds empty padding or circular phrasing | `formal_register_match` |
| 3 | Shorter option deletes a required qualifier or contrast | `formal_register_match` |

### `precision_word_choice`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Same semantic field but wrong degree, direction, or selectional fit | `grammar_fit_only` |
| 2 | Stronger or weaker word than the context supports | `formal_register_match` |
| 3 | Formal word sounds plausible but does not fit the sentence logic | `formal_register_match` |

### `register_style_consistency`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Colloquial or conversational expression in academic prose | `grammar_fit_only` |
| 2 | Overly inflated academic diction that changes meaning | `formal_register_match` |
| 3 | Technical term from the wrong field or register | `grammar_fit_only` |

### `logical_relationships`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Connector reverses cause, contrast, concession, or condition | `grammar_fit_only` |
| 2 | Correct topic but wrong logical relation between clauses | `formal_register_match` |
| 3 | Vague connector hides the fact that no supported relation is stated | `formal_register_match` |

### `emphasis_meaning_shifts`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Emphasizes the wrong actor, object, or time period | `grammar_fit_only` |
| 2 | Preserves facts but changes the intended contrast or focus | `formal_register_match` |
| 3 | Adds an intensifier or limiting phrase unsupported by the passage | `formal_register_match` |

### `data_interpretation_claims`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Uses the right data source but wrong row, column, group, or time window | `grammar_fit_only` |
| 2 | States an absolute change when the claim requires proportion or percentage | `formal_register_match` |
| 3 | Accurate value answers a different question than the stem asks | `grammar_fit_only` |

### `transition_logic`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Transition from the wrong relation family (contrast vs. cause vs. addition) | `grammar_fit_only` |
| 2 | Correct broad family but wrong subtype or degree | `formal_register_match` |
| 3 | Familiar transition phrase creates an unsupported logical bridge | `formal_register_match` |

---

## B.5 Transition Subtype Vocabulary

### B.5.1 `transition_subtype_key` field

**In classification and annotation** (stored per item and per option):

```json
{ "transition_subtype_key": "causal_chain" }
```

**In generation input** (one target + three distractor subtypes):

```json
{
  "target_transition_subtype_key": "causal_chain",
  "distractor_transition_subtypes": [
    "contrast_refutation",
    "addition",
    "chronology"
  ]
}
```

`transition_subtype_key` is the stored annotation field on both items and
options. `target_transition_subtype_key` is the generation request field
specifying which relationship the correct option should express.

This field is optional for legacy item annotation but mandatory for
generation. For every transition distractor, annotate `transition_subtype_key`
with the wrong relationship the distractor signals.

### B.5.2 Approved `transition_subtype_key` values

| Key | Canonical word(s) | Logical relationship |
|---|---|---|
| `sequence_final_event` | `finally`, `last`, `ultimately` (sequential) | The described step is last in an ordered process |
| `contrast_refutation` | `however`, `but`, `yet`, `still` | Refutes or contradicts the prior claim |
| `addition` | `additionally`, `furthermore`, `also`, `moreover` | Adds another supporting point |
| `result_consequence` | `therefore`, `thus`, `hence`, `as a result`, `consequently`, `for this reason`, `accordingly`, `as such` | Second statement follows causally from the first |
| `chronology` | `previously`, `later`, `then`, `next`, `afterward`, `subsequently` | Events or steps in time order |
| `alternative` | `instead`, `alternatively`, `rather`, `otherwise` | Substitutes one option for another |
| `emphasis_support` | `indeed`, `in fact`, `certainly` | Reinforces or intensifies the prior claim |
| `causal_chain` | `in turn` | Second event follows directly from the first as part of a causal sequence |
| `specificity_elaboration` | `specifically`, `in particular`, `namely` | Narrows or details a general claim |
| `purpose_action` | `to that end`, `to this end`, `for this purpose` | Describes an action taken to fulfill the preceding goal |
| `frequency_difference` | `more often`, `less often` | Emphasizes a relative frequency difference |
| `simultaneity` | `meanwhile`, `at the same time` | Two events or processes occur concurrently |
| `similarity` | `similarly`, `likewise` | Second claim parallels the first |
| `appropriateness` | `fittingly`, `aptly`, `appropriately` | Second statement is well-suited to the prior context |
| `change_over_time` | `increasingly`, `over time`, `progressively` | A trend or direction is developing |
| `exception` | `though`, `although`, `even so`, `nevertheless` | Marks a qualification or exception to the prior claim |
| `final_realization` | `ultimately` (non-sequential) | Describes what something comes down to or reveals in the end |
| `converse_opposite` | `conversely`, `on the other hand`, `by contrast`, `on the contrary` | States the opposite tendency to the prior claim |
| `present_continuation` | `currently`, `today`, `now`, `at present` | Shift from historical context to the present state |
| `direct_refutation` | `on the contrary` | Directly disputes an assumption or claim |
| `logical_consequence` | `as such`, `therefore`, `thus` | Logical inference from the preceding statement |
| `concession_qualification` | `admittedly`, `granted`, `to be sure` | Concedes a point before a counter-argument |
| `example` | `for example`, `for instance`, `to illustrate` | Specific instance of a general claim |
| `restatement_clarification` | `in other words`, `that is`, `i.e.` | Rephrases or clarifies the prior statement without adding new information; distinct from `example` (which adds a concrete instance) and `addition` (which adds new material) |

---

## B.6 Notes Synthesis Metadata

### B.6.1 Required fields for all `choose_best_notes_synthesis` items

**Annotation:**

```json
{
  "synthesis_goal_key": "emphasize_similarity",
  "audience_knowledge_key": "audience_unfamiliar",
  "required_content_key": "comparison_needed"
}
```

**Generation input:**

```json
{
  "target_synthesis_goal_key": "emphasize_similarity",
  "target_audience_knowledge_key": "audience_unfamiliar",
  "target_required_content_key": "comparison_needed",
  "distractor_synthesis_failures": [
    "wrong_goal",
    "omits_required_content",
    "correct_topic_wrong_comparison"
  ]
}
```

`synthesis_goal_key`, `audience_knowledge_key`, and `required_content_key`
are mandatory for generation; recommended for annotation.

### B.6.2 Approved `synthesis_goal_key` values

| Key | Description |
|---|---|
| `emphasize_similarity` | Highlight that two things share a feature |
| `emphasize_difference` | Highlight a contrast between two things |
| `explain_advantage` | State why one option is better than another |
| `explain_mechanism` | Describe how something works |
| `present_research` | Summarize a study for an unfamiliar reader |
| `present_theory` | Introduce a theory to an unfamiliar audience |
| `introduce_work` | Introduce a named literary or artistic work |
| `describe_work` | Describe what a work does or is about |
| `emphasize_achievement` | Highlight a named person's accomplishment |
| `make_generalization` | Draw a broad conclusion from the notes |
| `contrast_quantities` | Compare two numerical or measured values |
| `compare_measurements` | Compare lengths, sizes, masses, or other units |
| `emphasize_sample` | Highlight a specific representative example |
| `identify_category` | Name the classification group something belongs to |
| `identify_profession` | State a person's professional role or title |
| `identify_setting` | State where a story or work takes place |
| `identify_title` | Name the title of a work |
| `identify_year` | State when something was published, created, or completed |
| `identify_duration` | State how long something took or lasted |
| `identify_distance` | State a measured distance or range |
| `identify_author_pseudonym` | Reveal who wrote under a pen name |
| `contrast_structural_types` | Compare two structural or formal categories |
| `present_study_aim` | State what a study was trying to find out |
| `identify_statistical_method` | Name or describe the statistical approach used |
| `identify_statistical_authorship_method` | Name or describe a statistical method used to attribute authorship |
| `explain_technique_advantage` | Describe why a specific technique is useful |
| `explain_misconception_naming` | Explain why something is incorrectly named |
| `challenge_with_quotation` | Use a quotation from notes to dispute an explanation |
| `challenge_explanation_with_quote` | Use a quotation from the notes to challenge or weaken a proposed explanation |
| `present_study_overview` | High-level summary of a study's design and result |
| `present_methodology` | Describe the methods used in a study |
| `present_study_conclusions` | State what a study found or concluded |
| `emphasize_significance` | State why a discovery or result matters |
| `explain_format_advantage` | Describe why a format or medium is useful |
| `emphasize_duration_and_purpose` | State both how long something took and why |
| `emphasize_size_similarity` | Highlight that two things are similar in size or scale |
| `contrast_origins` | Compare where two words, practices, or traditions came from |
| `provide_historical_overview` | Summarize the development of something over time |
| `contrast_formal_structures` | Compare formal or structural features (e.g., poetic meter) |
| `contextualize_changing_beliefs` | Situate a document or event within a shift in thinking |
| `compare_hypothesis_scope` | Contrast the breadth or narrowness of two hypotheses |
| `emphasize_age_similarity` | Note that two things are similar in age or date |

### B.6.3 Approved `audience_knowledge_key` values

| Key | When to use |
|---|---|
| `audience_familiar` | Reader already knows a named source, author, or context |
| `audience_unfamiliar` | Reader needs identifying context (author name, work title, field, year) |
| `not_specified` | Audience assumption is not the distinguishing factor |

### B.6.4 Approved `required_content_key` values

| Key | What the correct sentence must include |
|---|---|
| `comparison_needed` | At least one explicit comparison |
| `definition_needed` | A definition or explanation of a named term is required |
| `background_omit` | Background should be omitted because the target audience already knows it |
| `measurement_values_needed` | At least one specific number, unit, or measured value |
| `result_needed` | The outcome or finding |
| `title_and_content_needed` | Both the title of a work and a description |
| `achievement_needed` | A statement of what a person accomplished |
| `owner_of_achievement_needed` | The person or group responsible for the achievement must be named |
| `category_label_needed` | The name of the classification group |
| `sample_location_needed` | The specific example or location highlighted |
| `profession_label_needed` | The person's job title or field |
| `setting_needed` | The place or time setting of a work |
| `year_needed` | A specific year or date |
| `duration_needed` | A length of time |
| `distance_needed` | A measured distance |
| `author_identity_needed` | The real name of an author who used a pseudonym |
| `mechanism_needed` | A description of the causal or functional process |
| `structural_roles_needed` | Names of structural or formal elements being compared |
| `study_aim_needed` | The stated research question or objective |
| `statistical_method_needed` | The specific analytical approach |
| `misconception_needed` | The false belief that explains a name or label |
| `quotation_needed` | A direct quotation from the notes |
| `study_finding_summary_needed` | A summary of the result or conclusion |
| `method_needed` | A description of the procedure or approach |
| `conclusion_needed` | The conclusion reached |
| `significance_needed` | A statement of importance or impact |
| `advantage_needed` | A statement of why something is preferable |
| `purpose_needed` | A statement of intention or goal |
| `origin_labels_needed` | The named sources or languages of origin |
| `timeline_needed` | A sequence of events or developments |
| `formal_feature_labels_needed` | Specific names of structural or formal features |
| `scope_terms_needed` | Terms describing breadth or narrowness |

### B.6.5 Wrong-option annotation for notes synthesis

For every notes synthesis distractor, annotate `synthesis_distractor_failure`
(per-option field, singular string):

| Value | Description |
|---|---|
| `wrong_goal` | Sentence does something other than what the stem requests |
| `omits_required_content` | On-topic but leaves out a required content element |
| `adds_background_audience_does_not_need` | Provides context the audience already has, or provides irrelevant background |
| `correct_topic_wrong_comparison` | Mentions the right subjects but states the wrong comparison, direction, or scope |
| `omits_unfamiliar_context` | Fails to include identifying context required for an unfamiliar audience |
| `wrong_audience_assumption` | Assumes the audience is familiar when it is not, or unfamiliar when it is familiar |
| `misstates_required_relationship` | Uses the right note facts but states the wrong similarity, difference, causal, temporal, or scope relationship |
| `irrelevant_background` | Adds accurate background information that does not serve the requested rhetorical goal |

**Field name conventions:**

- Per-option annotation: `"synthesis_distractor_failure": "wrong_goal"` (singular string on each option)
- Generation input spec: `"distractor_synthesis_failures": ["wrong_goal", "omits_required_content", "correct_topic_wrong_comparison"]` (array on the request, one value per planned distractor)

---

## B.7 Passage Architecture Templates

```json
{ "passage_architecture_key": "science_setup_finding_implication" }
```

Approved values:

- `science_setup_finding_implication`
- `science_hypothesis_method_result`
- `history_claim_evidence_limitation`
- `history_assumption_revision`
- `literature_observation_interpretation_shift`
- `literature_character_conflict_reveal`
- `economics_theory_exception_example`
- `economics_problem_solution_tradeoff`
- `rhetoric_claim_counterclaim_resolution`
- `notes_fact_selection_contrast`
- `experiment_hypothesis_control_result` — hypothesis, experimental group,
  control condition, predicted direction, observed outcome; enables
  support/weaken/inference items requiring correct group identification
- `indirect_effect_mediation` — initial condition, intermediate mediating
  variable, final outcome, explicit claim that effect operates through
  the mediator
- `alternative_explanation_ruled_out` — observed change, named alternative
  cause, control or finding that eliminates the alternative, remaining
  explanation
- `mechanism_manipulation_test` — observed phenomenon, candidate mechanism,
  experimental component replacement or manipulation, predicted result if
  causal, observed result
- `studied_subgroup_generalization_limit` — broad population, well-studied
  subgroup, evidence concentrated in the subgroup, explicit or implicit
  warning that results may not generalize

---

## B.8 Difficulty Calibration for Generation

### Target difficulty by trap and distractor profile

| Difficulty | Trap intensity | Distractor plausibility | Passage complexity |
|---|---|---|---|
| `low` | `none` or `low` | Obviously wrong forms | Short sentence, common vocabulary |
| `medium` | `medium` | One strong distractor, two moderate | Standard academic vocabulary, one clause |
| `high` | `high` | All three plausible on first read | Dense vocabulary, multiple clauses, unfamiliar topic |

### Difficulty dimension rubric

| Dimension | `low` | `medium` | `high` |
|---|---|---|---|
| `difficulty_reading` | Common vocabulary, short sentences | Academic vocabulary, compound sentences | Dense prose, embedded clauses, unfamiliar topic |
| `difficulty_grammar` | Single visible rule application | Rule requires cross-sentence parsing or trap navigation | Multiple rules interact or trap is deeply embedded |
| `difficulty_inference` | No inference required | One-step inference | Multi-step inference combining grammar and rhetoric |
| `difficulty_vocab` | Below 10th-grade level | 11th–12th grade or academic register | Rare, technical, or archaic usage |
| `distractor_strength` | Obviously wrong on inspection | One distractor tempting | All three distractors plausible on first read |

`difficulty_overall` reflects the dimension that creates the most challenge,
not an average.

Hard SAT questions are difficult because distractors are close to correct,
wrong answers are attractive, elimination requires precise reasoning, and
multiple answers appear initially plausible. Difficulty must come from
distractor competition, not obscure vocabulary.

---

## B.9 Batch, Deduplication, and Option Ordering

### Batch rules

Maximum batch size: 10 items. Items must not share the same
`(grammar_focus_key, syntactic_trap_key)` pair unless explicitly requested.
Vary `topic_broad` and `topic_fine`. Return array of complete item objects.
On failure after 3 retries, return the error for that item index and halt.

### Topic rotation

1. No two consecutive items may share the same `topic_broad`.
2. No two items within a 5-item window may share the same `topic_fine`.
3. If structural similarity exceeds 80% (same structure with only noun
   substitution), regenerate the passage.
4. Respect `avoid_recent_exam_ids` when provided.

### Option ordering

Correct answer may appear in any position. Over 10+ items: 20–30% per
position. No module may have more than 40% correct answers in any single
position.

### Distractor strategy diversity (module-bank constraint)

Over any window of 5 consecutive items sharing the same `grammar_focus_key`:

1. **Trap diversity** — For focus keys with ≥3 available `syntactic_trap_key`
   variants (see D.5), at least 2 distinct trap keys must appear across the 5
   items. Focus keys with only 1–2 available trap variants are exempt from
   this count.
2. **Failure-mode cap** — No single `student_failure_mode_key` may account for
   more than 40% of all distractor slots in the window (max 6 of 15 distractor
   slots for a 5-item window; max 12 of 30 slots for a 10-item window).
3. **Secondary pattern requirement** — At least 1 item per 5-item window must
   use a secondary trap pattern documented in B.3 rather than the canonical
   construction for that focus key.

These constraints prevent item banks from converging on a small set of
predictable distractor patterns at scale. The anti-clone check (E.4) handles
passage-level surface similarity; this constraint handles distractor-strategy-
level similarity across items that are surface-distinct but mechanically
identical.

---

## B.10 Explanation Requirements

| Field | Maximum length | Required content |
|---|---|---|
| `explanation_short` | 25 words | Core rule and why correct answer satisfies it |
| `explanation_full` | 150 words | Why correct is correct; why each wrong option fails by label, naming the specific grammar focus key |

Additional rules:

1. `explanation_short` ≤25 words, state the core rule.
2. `explanation_full` ≤150 words: why correct is correct; each wrong option
   by label with specific error; passage evidence when relevant.
3. For No-Change items, explicitly justify why the original text needs no
   correction.
4. For verb-form items, reference `passage_tense_register_key`.

---

## B.11 No-Change Generation

Approximately 20% of official SAT grammar questions have the original text
as the correct answer.

Generation rule: write a grammatically flawless passage; make option A the
original text (correct); distractors B, C, D each introduce a different
grammar error.

Annotation rule: do not assume an error exists. If original wording is
correct, explain why no correction is needed. Populate:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

---

## B.12 Complete Generation Examples

### Example A — `subject_verb_agreement`, medium difficulty

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": null,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "The series of experiments conducted by the research team over the past five years ______ conclusive evidence that the treatment reduces inflammation.",
    "correct_option_label": "B",
    "explanation_short": "The singular noun 'series' requires the singular present perfect verb 'has produced.'",
    "explanation_full": "The subject is 'series,' a singular collective noun. The plural prepositional phrase 'of experiments' and the participial phrase 'conducted by the research team' interrupt the subject-verb connection but do not change the subject's number. 'Has produced' (B) correctly agrees with the singular subject. (A) 'Have produced' agrees with the plural 'experiments,' not the subject 'series.' (C) 'Were producing' shifts to past progressive and introduces a number error. (D) 'Are producing' uses present progressive and the plural auxiliary 'are,' failing agreement.",
    "evidence_span_text": "The series of experiments ... ______ conclusive evidence"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Form, Structure, and Sense",
    "subskill": "subject-verb agreement with plural prepositional object",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "agreement",
    "grammar_focus_key": "subject_verb_agreement",
    "secondary_grammar_focus_keys": [],
    "transition_subtype_key": null,
    "syntactic_trap_key": "nearest_noun_attraction",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "science",
    "topic_fine": "medical research",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "medium",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "distractor_strength": "high",
    "disambiguation_rule_applied": null,
    "classification_rationale": "The collective noun 'series' is the subject; plural object 'experiments' creates the nearest-noun trap."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "have produced",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "The plural noun 'experiments' immediately before the blank attracts a plural verb.",
      "why_wrong": "The subject is 'series,' a singular noun. Plural verb 'have produced' fails agreement.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "nearest_noun_reflex",
      "distractor_distance": "tight"
    },
    {
      "option_label": "B",
      "option_text": "has produced",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_agreement",
      "plausibility_source_key": null,
      "option_error_focus_key": null,
      "why_plausible": null,
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "student_failure_mode_key": null,
      "distractor_distance": null
    },
    {
      "option_label": "C",
      "option_text": "were producing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "tense_mismatch",
      "plausibility_source_key": "auditory_similarity",
      "option_error_focus_key": "verb_tense_consistency",
      "why_plausible": "Past progressive sounds formal and matches a reader's assumption about completed research.",
      "why_wrong": "Shifts to past progressive; 'were' also fails agreement with singular 'series.'",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "tense_proximity_pull",
      "distractor_distance": "moderate"
    },
    {
      "option_label": "D",
      "option_text": "are producing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "subject_verb_agreement",
      "why_plausible": "Present tense matches the general-truth register; plural auxiliary fits 'experiments.'",
      "why_wrong": "Present progressive 'are producing' fails agreement with singular 'series' and implies ongoing action rather than a completed finding.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "nearest_noun_reflex",
      "distractor_distance": "moderate"
    }
  ],
  "reasoning": {
    "primary_rule": "A singular collective noun ('series') governs verb number regardless of intervening plural modifiers.",
    "trap_mechanism": "The plural noun 'experiments' in the prepositional phrase immediately precedes the blank, creating nearest-noun attraction.",
    "correct_answer_reasoning": "'Series' is singular; the intervening phrase does not change subject number; simple present perfect 'has produced' correctly agrees and matches the established-finding register.",
    "distractor_analysis_summary": "A fails agreement via nearest-noun reflex; C introduces a tense shift to past progressive; D uses plural auxiliary while retaining present register."
  },
  "generation_profile": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "very_high",
    "target_distractor_pattern": [
      "plural verb via nearest-noun attraction (tight)",
      "past progressive tense shift (moderate)",
      "present progressive with plural auxiliary (moderate)"
    ],
    "passage_template": "The [singular collective noun] of [plural noun], [participial phrase], ______ [direct object or complement].",
    "passage_tense_register_key": "established_finding_present",
    "expected_tense_key": "simple_present",
    "tense_shift_allowed": false,
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital",
    "generation_timestamp": "2026-04-29T00:00:00Z",
    "model_version": "rules_agent_v8.0"
  },
  "review": {
    "annotation_confidence": 0.98,
    "needs_human_review": false,
    "review_notes": ""
  }
}
```

### Example B — `transition_logic`, medium difficulty

```json
{
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": null,
    "stimulus_mode_key": "passage_excerpt",
    "stem_type_key": "choose_best_transition",
    "prompt_text": "Which choice completes the text with the most logical transition?",
    "passage_text": "Early studies of the compound showed that it could bind to certain proteins under controlled laboratory conditions. ______, researchers began testing whether the same binding occurred in living tissue samples.",
    "correct_option_label": "A",
    "explanation_short": "The second sentence describes the next chronological research phase, requiring a time-sequence transition.",
    "explanation_full": "The passage moves from initial laboratory findings to a subsequent testing phase. 'Subsequently' (A) signals that the second action followed the first in time—the correct logical relationship. 'However' (B) signals contrast or refutation; the second sentence does not contradict the first. 'Therefore' (C) signals that the second action is a causal consequence of the first; the transition to tissue testing is a next step, not a necessary inference. 'Additionally' (D) signals a parallel addition; tissue-sample testing is not a contemporaneous companion activity but a sequential next phase.",
    "evidence_span_text": "...controlled laboratory conditions. ______ researchers began testing..."
  },
  "classification": {
    "domain": "Expression of Ideas",
    "skill_family": "Transitions",
    "subskill": "chronological sequence transition",
    "question_family_key": "expression_of_ideas",
    "grammar_role_key": "expression_of_ideas",
    "grammar_focus_key": "transition_logic",
    "transition_subtype_key": "chronology",
    "secondary_grammar_focus_keys": [],
    "syntactic_trap_key": "none",
    "evidence_scope_key": "paragraph",
    "evidence_location_key": "transition_zone",
    "answer_mechanism_key": "inference",
    "solver_pattern_key": "evaluate_transition",
    "topic_broad": "science",
    "topic_fine": "biochemistry research",
    "reading_scope": "sentence-pair",
    "reasoning_demand": "logical relationship identification",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "low",
    "difficulty_inference": "medium",
    "difficulty_vocab": "low",
    "distractor_strength": "medium",
    "disambiguation_rule_applied": null,
    "classification_rationale": "Second sentence describes next research phase; relationship is chronological sequence, not contrast, cause-effect, or parallel addition."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "Subsequently,",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": null,
      "plausibility_source_key": null,
      "option_error_focus_key": null,
      "why_plausible": null,
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "student_failure_mode_key": null,
      "distractor_distance": null,
      "transition_subtype_key": "chronology"
    },
    {
      "option_label": "B",
      "option_text": "However,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "'However' is a high-frequency, formal transition that fits many scientific passage contexts.",
      "why_wrong": "Signals contrast or refutation; the second sentence continues the same line of research rather than contradicting the first.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "transition_wrong_direction",
      "distractor_distance": "moderate",
      "transition_subtype_key": "contrast_refutation"
    },
    {
      "option_label": "C",
      "option_text": "Therefore,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "The move from lab work to the next test might seem like a logical consequence.",
      "why_wrong": "Signals causal consequence; moving to tissue samples is the next step in a research sequence, not a result that necessarily follows from the protein-binding finding.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "transition_wrong_direction",
      "distractor_distance": "tight",
      "transition_subtype_key": "result_consequence"
    },
    {
      "option_label": "D",
      "option_text": "Additionally,",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "transition_mismatch",
      "semantic_relation_key": null,
      "plausibility_source_key": "transition_assumption",
      "option_error_focus_key": "transition_logic",
      "why_plausible": "The research expansion could superficially appear to be an additional, parallel activity.",
      "why_wrong": "Signals a parallel addition; tissue-sample testing is a chronologically subsequent phase, not a contemporaneous companion activity.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 1,
      "student_failure_mode_key": "transition_assumption",
      "distractor_distance": "tight",
      "transition_subtype_key": "addition"
    }
  ],
  "reasoning": {
    "primary_rule": "The transition must signal the correct logical relationship between the two sentences: temporal sequence (first event then next event).",
    "trap_mechanism": "Both 'Therefore' (causal) and 'Additionally' (additive) are common in scientific prose and superficially fit the research context.",
    "correct_answer_reasoning": "'Subsequently' correctly signals that tissue-sample testing came after—not because of, and not concurrently with—the protein-binding laboratory work.",
    "distractor_analysis_summary": "B (However) signals contrast where none exists; C (Therefore) implies causal inference rather than sequence; D (Additionally) implies parallel addition rather than sequential progression."
  },
  "generation_profile": {
    "target_grammar_role_key": "expression_of_ideas",
    "target_grammar_focus_key": "transition_logic",
    "target_transition_subtype_key": "chronology",
    "distractor_transition_subtypes": ["contrast_refutation", "result_consequence", "addition"],
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "low",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "contrast transition (However) — signals refutation where none exists",
      "causal transition (Therefore) — confuses sequence with consequence",
      "additive transition (Additionally) — confuses sequence with parallel addition"
    ],
    "passage_template": "[Research phase A description]. ______, [researchers/team] [next research phase B description].",
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital",
    "generation_timestamp": "2026-04-29T00:00:00Z",
    "model_version": "rules_agent_v8.0"
  },
  "review": {
    "annotation_confidence": 0.96,
    "needs_human_review": false,
    "review_notes": ""
  }
}
```

---

## B.13 Generation Validation Checklist

Run all 25 checks before emitting output. Maximum 3 retries per component.
After 3 failures, abort and return error response (B.14).

| # | Check | Failure action |
|---|---|---|
| 1 | `grammar_focus_key` belongs to `grammar_role_key` per D.8.1 | Regenerate classification |
| 2 | Exactly 4 options exist | Regenerate all options |
| 3 | Exactly 1 option has `is_correct: true` | Regenerate options |
| 4 | No two distractors share the same `option_error_focus_key` | Regenerate one distractor |
| 5 | At least one distractor targets the declared `target_syntactic_trap_key` | Regenerate distractors |
| 6 | Correct option contains no grammar error | Regenerate correct option |
| 7 | Passage is 20–40 words for sentence-only items | Regenerate passage |
| 8 | Passage requires no outside knowledge | Regenerate passage |
| 9 | Register is formal academic; no contractions or slang | Regenerate passage |
| 10 | `difficulty_overall` matches declared target | Regenerate item |
| 11 | `target_frequency_band` is not `very_low` without justification | Reject or add justification |
| 12 | `disambiguation_rule_applied` is present if any label conflict exists | Add rule or set `needs_human_review: true` |
| 13 | `explanation_full` explains why every wrong option is wrong | Regenerate explanations |
| 14 | `generation_profile` includes all required fields from D.9 | Add missing fields |
| 15 | All JSON keys are from approved lists; no invented keys | Replace or propose amendment |
| 16 | `evidence_span_text` follows format rules from D.8.13 | Reformat |
| 17 | Option text format is consistent | Regenerate options |
| 18 | For `transition_logic` items, `transition_subtype_key` is present in classification and on each option | Add subtype or `needs_human_review: true` |
| 19 | For `choose_best_notes_synthesis` items, `synthesis_goal_key`, `audience_knowledge_key`, and `required_content_key` are present | Add fields |
| 20 | For generated notes synthesis, `synthesis_distractor_failure` covers all three wrong options | Add missing failure modes |
| 21 | For `unnecessary_internal_punctuation` items, correct option has no punctuation at the target syntactic boundary | Regenerate correct option |
| 22 | For `end_punctuation_question_statement` items, correct option end mark matches sentence type | Regenerate correct option |
| 23 | For generated modules, `test_format_key` is present and module length matches (27 for digital, 33 for accommodation) | Add field or correct length |
| 24 | For `verb_form` items targeting finite vs nonfinite, generation pattern is one of: `finite_verb_in_relative_clause`, `finite_verb_in_main_clause`, `modal_plus_plain_form` | Reclassify or add pattern note |
| 25 | For `verb_tense_consistency` items in a literary passage, `passage_tense_register_key` is `literary_present` | Update tense register |
| 26 | For `adjective_adverb_distinction` items, correct option uses adverb after an action verb and adjective after a linking verb; no distractor is grammatically correct | Regenerate correct option or distractors |
| 27 | For `illogical_comparison` items, correct option uses "that of" / "those of" or an explicit parallel noun form; all distractors preserve the illogical bare comparison in some form | Regenerate correct option |
| 28 | For `commonly_confused_words` items, all four options are real English words in common use; exactly one is correct for the passage context; no option is a spelling error or nonsense word | Regenerate options |
| 29 | For `preposition_idiom` items, all four options are real English prepositions; the correct option forms the established idiomatic collocation; at least two wrong options form plausible but non-standard collocations | Regenerate options |

---

## B.14 Error Response Format

```json
{
  "error": {
    "error_code": "INVALID_FOCUS_KEY | ROLE_FOCUS_MISMATCH | VERY_LOW_FREQUENCY_UNJUSTIFIED | GENERATION_FAILURE | VALIDATION_FAILURE",
    "error_message": "Human-readable description.",
    "failed_component": "passage | stem | correct_option | distractor | metadata | validation",
    "retry_count": 3,
    "recommendation": "Suggested fix or fallback."
  }
}
```

---

## B.15 Real-Time Constraints

Emit valid JSON on the first attempt ≥90% of the time. Complete generation
end-to-end in ≤3 reasoning steps. Never hallucinate an exam ID (use
`"GENERATED"`). Cache passage templates for identical
`(grammar_focus_key, syntactic_trap_key)` pairs.

---

# PART C — ANNOTATION / INGESTION

---

## C.1 Question Fields

```json
{
  "source_exam": "PT4",
  "source_section": "RW",
  "source_module": "M1",
  "source_question_number": 1,
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text",
  "prompt_text": "...",
  "passage_text": null,
  "paired_passage_text": null,
  "notes_bullets": [],
  "table_data": null,
  "graph_data": null,
  "correct_option_label": "B",
  "explanation_short": "...",
  "explanation_full": "...",
  "evidence_span_text": "..."
}
```

### C.1.1 `stimulus_mode_key` values

- `sentence_only` — single sentence with a blank (default for SEC grammar questions)
- `passage_excerpt` — short multi-sentence excerpt (2–4 sentences)
- `prose_single` — single labeled prose passage (50–150 words), one question
- `prose_paired` — two labeled texts (Text 1 / Text 2); exclusive to Cross-Text Connections questions
- `prose_plus_table` — prose passage with an embedded data table
- `prose_plus_graph` — prose passage with an embedded informational graphic.
  Confirmed graphic subtypes: bar chart, line graph, scatterplot (with or
  without line of best fit), pie chart, map. All subtypes share this key;
  the specific graphic subtype is free-text in `graph_data`.
- `notes_bullets` — bulleted student-notes stimulus ("While researching a
  topic, a student has taken the following notes:"); exclusive to Rhetorical
  Synthesis questions
- `poem` — poetry excerpt

### C.1.2 `stem_type_key` values

**Standard English Conventions:**
- `complete_the_text` — fill-in-the-blank grammar (SEC); most common SEC stem
- `choose_best_grammar_revision` — full-sentence or clause replacement (SEC)

**Information and Ideas:**
- `choose_main_idea` — Central Ideas and Details: main idea of passage
- `choose_central_detail` — Central Ideas and Details: specific supporting detail
- `choose_best_inference` — Inferences: logical conclusion not explicitly stated
- `choose_command_of_evidence_textual` — Command of Evidence (Textual): best quote or detail supporting a claim
- `choose_best_quote` — alias for `choose_command_of_evidence_textual` (legacy; prefer explicit form)
- `choose_command_of_evidence_quantitative` — Command of Evidence (Quantitative): best completion using data from table or graph
- `choose_best_completion_from_data` — alias for `choose_command_of_evidence_quantitative` (legacy; prefer explicit form)

**Craft and Structure:**
- `choose_words_in_context` — Words in Context: meaning or function of a word/phrase in context; most frequent question type (~28% of section)
- `choose_main_purpose` — Text Structure and Purpose: author's main purpose
- `choose_structure_description` — Text Structure and Purpose: how passage is structured
- `choose_sentence_function` — Text Structure and Purpose: function of a specific sentence
- `choose_likely_response` — Text Structure and Purpose: how one writer would likely respond to another
- `choose_cross_text_connection` — Cross-Text Connections: relationship between paired texts (Text 1 / Text 2); only valid with `stimulus_mode_key: "prose_paired"`

**Expression of Ideas:**
- `choose_best_transition` — Transitions: most logical transition between sentences
- `choose_best_notes_synthesis` — Rhetorical Synthesis: best sentence synthesizing student notes toward a stated goal
- `choose_best_support` — legacy key; reclassify as `choose_command_of_evidence_textual` or `choose_best_notes_synthesis` as appropriate

### C.1.3 Approved values for undocumented fields

| Field | Approved values |
|---|---|
| `answer_mechanism_key` | `rule_application`, `pattern_matching`, `evidence_location`, `inference`, `data_synthesis` |
| `solver_pattern_key` | `apply_grammar_rule_directly`, `locate_error_zone`, `compare_register`, `evaluate_transition`, `synthesize_notes`, `eliminate_by_boundary` |
| `semantic_relation_key` | `nearest_noun_agreement`, `comma_splice`, `boundary_not_closed`, `boundary_overly_strong`, `wrong_boundary_type`, `correct_agreement`, `correct_boundary`, `unnecessary_auxiliary`, `tense_mismatch`, `modifier_misplaced`, `pronoun_ambiguous`, `parallel_broken`, `idiom_violation`, `adjective_for_adverb`, `adverb_for_adjective`, `illogical_comparison_mismatch`, `confused_word_substitution`, `wrong_preposition_idiom` |
| `evidence_scope_key` | `sentence`, `paragraph`, `passage`, `paired_passage`, `table`, `graph`, `notes` |
| `evidence_location_key` | `main_clause`, `subordinate_clause`, `surrounding_sentence`, `opening_sentence`, `closing_sentence`, `transition_zone`, `data_zone`, `entire_passage` |
| `distractor_strength` | `low`, `medium`, `high` |
| `difficulty_overall`, `difficulty_reading`, `difficulty_grammar`, `difficulty_inference`, `difficulty_vocab` | `low`, `medium`, `high` |
| `skill_family` | **Standard English Conventions:** `Boundaries`, `Form, Structure, and Sense` — **Expression of Ideas:** `Transitions`, `Rhetorical Synthesis` — **Craft and Structure:** `Words in Context`, `Text Structure and Purpose`, `Cross-Text Connections` — **Information and Ideas:** `Central Ideas and Details`, `Inferences`, `Command of Evidence` |
| `subskill` | Free-text describing the specific skill |
| `topic_broad` | `science`, `history`, `literature`, `social_studies`, `humanities`, `arts`, `economics`, `technology`, `environment` — Note: `humanities` is an official College Board content area. `arts`, `economics`, `technology`, `environment` are project-internal sub-tags within the four official CB areas (Literature, History/Social Studies, Humanities, Science). |
| `topic_fine` | Free-text subtopic |

---

## C.2 Option-Level Analysis

Each option must include:

```json
{
  "option_label": "A",
  "option_text": "...",
  "is_correct": false,
  "option_role": "distractor",
  "distractor_type_key": "punctuation_error",
  "semantic_relation_key": "boundary_not_closed",
  "plausibility_source_key": "punctuation_style_bias",
  "option_error_focus_key": "sentence_boundary",
  "why_plausible": "The dash punctuation looks sophisticated.",
  "why_wrong": "It fails to create a valid sentence boundary.",
  "grammar_fit": "no",
  "tone_match": "yes",
  "precision_score": 1,
  "student_failure_mode_key": "punctuation_intimidation",
  "distractor_distance": "moderate"
}
```

For notes synthesis options, also include `synthesis_distractor_failure`
(wrong options only; see B.6.5).

For transition options, also include `transition_subtype_key` on every option
(see B.5.1).

### C.2.1 `option_error_focus_key`

For wrong options in SEC questions, populate `option_error_focus_key` with
the specific grammar focus key that explains the error.

| Wrong option surface error | Required `option_error_focus_key` |
|---|---|
| Wrong semicolon | `semicolon_use` |
| Wrong apostrophe | `apostrophe_use` |
| Wrong tense | `verb_tense_consistency` |
| Wrong relative clause | `relative_pronouns` |
| Comma splice | `comma_splice` |
| Dangling modifier | `modifier_placement` |
| Comma inside subject–verb | `unnecessary_internal_punctuation` |
| Question mark on indirect question | `end_punctuation_question_statement` |

### C.2.2 Distractor type keys

**Wrong options:** `semantic_imprecision`, `logical_mismatch`, `scope_error`,
`tone_mismatch`, `grammar_error`, `punctuation_error`, `transition_mismatch`,
`data_misread`, `goal_mismatch`, `partially_supported`, `overstatement`,
`understatement`, `rhetorical_irrelevance`

**Correct option:** `correct`

### C.2.3 Grammar-specific plausibility sources

`nearest_noun_attraction`, `punctuation_style_bias`, `auditory_similarity`,
`grammar_fit_only`, `formal_register_match`, `common_idiom_pull`

### C.2.4 `precision_score` scale

| Value | Meaning |
|---|---|
| `1` | Incorrect. Contains a clear grammar error or fails the tested rule. |
| `2` | Partially acceptable but inferior. Grammatically valid in isolation but less effective. |
| `3` | Correct. Fully satisfies the tested rule. |

### C.2.5 `grammar_fit` and `tone_match` semantics

| Field | `yes` | `no` |
|---|---|---|
| `grammar_fit` | Grammatically possible in some context | Contains a clear grammar error impossible in any standard context |
| `tone_match` | Maintains formal academic register | Introduces slang, contractions, or register shift |

### C.2.6 `secondary_grammar_focus_keys`

Identify the single primary rule that eliminates the most wrong options.
Store it in `grammar_focus_key`. Store every other applicable rule in
`secondary_grammar_focus_keys`. For each wrong option, store the specific
error rule in `option_error_focus_key`.

### C.2.7 Option text format rules

1. **Fill-in-blank** (default for `complete_the_text`): options contain only
   the word or phrase that fills the blank.
2. **Full-replacement** (for `choose_best_grammar_revision`): options contain
   the full revised sentence or clause.
3. **Punctuation-only**: options contain only the punctuation mark.

Do not mix formats within a single item.

---

## C.3 No-Change and Original-Text Rule

When the original text is an option:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

Do not assume an error exists. If original wording is correct, explain why
no correction is needed.

---

## C.4 Multi-Error Rule

When multiple error types appear across choices:

1. Classify the primary tested rule in `grammar_focus_key`
2. Store secondary rules in `secondary_grammar_focus_keys`
3. Store option-specific errors in `option_error_focus_key`
4. Note ambiguity in `review.review_notes`

---

## C.5 Amendment Process

```json
{
  "amendment_proposal": {
    "proposed_key": "...",
    "proposed_parent_role_key": "...",
    "reason": "...",
    "evidence_text": "...",
    "status": "proposed",
    "frequency_estimate": "very_low | low | medium | high | very_high",
    "example_count": 0
  }
}
```

`proposed_parent_role_key` must be an existing `grammar_role_key` or a new
role proposal with justification. `evidence_text` must quote the exact item
text that triggered the proposal.

Do not insert proposed keys into production records until reviewed.

---

## C.6 Review Flags

Set `needs_human_review: true` when:

- More than one grammar focus seems equally plausible
- The question tests grammar and rhetoric simultaneously
- Option text is incomplete
- No existing key fits
- The original text may be correct but classification is uncertain

---

## C.7 Pilot Ingestion Examples

### Example 1: Plural possessive

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "apostrophe_use", "syntactic_trap_key": "none" }
```

### Example 2: Sentence boundary with interruption

```json
{ "grammar_role_key": "sentence_boundary", "grammar_focus_key": "sentence_boundary", "syntactic_trap_key": "interruption_breaks_subject_verb" }
```

### Example 3: Essential relative clause

```json
{ "grammar_role_key": "modifier", "grammar_focus_key": "relative_pronouns", "syntactic_trap_key": "none" }
```

### Example 4: No punctuation between subject and verb

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "unnecessary_internal_punctuation", "syntactic_trap_key": "none" }
```

### Example 5: Period on sentence ending in indirect question

```json
{ "grammar_role_key": "punctuation", "grammar_focus_key": "end_punctuation_question_statement", "syntactic_trap_key": "none" }
```

---

# PART D — TAXONOMY REFERENCE

---

## D.1 Grammar Role Keys

Use `grammar_role_key` only for Standard English Conventions or
grammar-adjacent questions.

Approved keys: `sentence_boundary`, `agreement`, `verb_form`, `modifier`,
`punctuation`, `parallel_structure`, `pronoun`, `expression_of_ideas`

### D.1.1 When to use `sentence_boundary`

Fragments, run-ons, comma splices, and punctuation required to divide sentence
units (periods, semicolons, commas, dashes at clause boundaries).

### D.1.2 When to use `agreement`

Subject-verb agreement, pronoun-antecedent agreement, countability and number
agreement, and determiners/articles where noun number is the central issue.

### D.1.3 When to use `verb_form`

Tense consistency, finite vs nonfinite verbs, gerunds and infinitives, voice,
mood and conditional logic, and scientific present / general truth.

### D.1.4 When to use `modifier`

Dangling modifiers, misplaced modifiers, modifier scope, comparative
structures, and logical predication.

### D.1.5 When to use `punctuation`

Comma mechanics, semicolon mechanics, colon/dash mechanics, apostrophes,
appositives, quotation punctuation, hyphens, absence of punctuation inside
required syntactic units, and end-punctuation type (question mark vs period)
when determined by sentence type.

### D.1.6 When to use `parallel_structure`

Parallel lists, correlative conjunctions, comparison structures when form
symmetry is primary, and elliptical constructions.

### D.1.7 When to use `pronoun`

Pronoun case, pronoun clarity, and ambiguous pronoun reference.

### D.1.8 When to use `expression_of_ideas`

Only when the question is grammar-adjacent but primarily about concision,
register, transition logic, precision of expression, data claim accuracy, or
rhetorical effectiveness.

---

## D.2 Grammar Focus Keys

Use the most specific applicable `grammar_focus_key`.

### D.2.1 Sentence boundary focus keys

- `sentence_fragment`
- `comma_splice`
- `run_on_sentence`
- `sentence_boundary`

### D.2.2 Agreement focus keys

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`
- `affirmative_agreement` ⚠️ `dsat_confidence: low` — so/neither inversion and
  tag questions appear primarily in ACT conventions; exclude from DSAT
  generation profiles

### D.2.3 Pronoun focus keys

- `pronoun_case`
- `pronoun_clarity`

### D.2.4 Verb form focus keys

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation` ⚠️ `dsat_confidence: low` — double negatives and hardly/scarcely
  inversions are ACT patterns; retain only for scope-of-negation coverage
  ("not all" vs "all not"); exclude double-negative and inversion patterns
  from DSAT generation profiles

### D.2.5 Modifier focus keys

- `modifier_placement`
- `comparative_structures` — comparisons where the compared elements are not
  grammatically parallel; includes implied/incomplete comparisons
- `illogical_comparison` — comparing a noun to an action or dissimilar category
  (e.g., "the results of Study 1 were better than Study 2"); distinct from
  `comparative_structures` because the error is logical, not formal
- `adjective_adverb_distinction` — adjective vs. adverb selection, particularly
  after linking verbs ("feel bad" not "feel badly"); promoted from pending D.2.9
- `logical_predication`
- `relative_pronouns`

### D.2.6 Punctuation focus keys

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`
- `unnecessary_internal_punctuation`
- `end_punctuation_question_statement`

#### `unnecessary_internal_punctuation` — rule definition

No punctuation may appear inside a required syntactic unit. The units the SAT
tests are: subject–verb, verb–object, verb–complement, preposition–complement,
and integrated relative clause. Inserting a comma, dash, or colon inside any
of these units is always wrong. The correct option has no punctuation at the
target boundary.

#### `end_punctuation_question_statement` — rule definition

A sentence that contains an indirect (reported) question ends with a period,
not a question mark, because the sentence as a whole is declarative. A
sentence consisting of two coordinated direct questions requires a question
mark. Wrong options typically swap the end mark or omit it.

### D.2.7 Parallel structure focus keys

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

### D.2.8 Expression of Ideas focus keys

- `redundancy_concision`
- `precision_word_choice`
- `register_style_consistency`
- `logical_relationships`
- `emphasis_meaning_shifts`
- `data_interpretation_claims`
- `transition_logic`
- `commonly_confused_words` — non-homophone semantic confusion pairs (affect/effect,
  allusion/illusion, elicit/illicit, principle/principal, etc.); homophone
  possession confusion (its/it's, whose/who's) is covered by `possessive_contraction`;
  frequency: low; promoted from pending D.2.9
- `preposition_idiom` — verb-preposition and adjective-preposition collocations
  where the correct preposition is idiomatic (responsible *for*, different *from*,
  composed *of*, interested *in*); frequency: low

### D.2.9 Proposed keys (pending review — not yet in production)

These keys appeared in College Board practice test analysis but have not yet
been formally adopted. Do not use in production records. Propose via C.5 if
evidence warrants.

| Proposed key | Proposed parent role | Evidence source | Note |
|---|---|---|---|
| `subjunctive_mood` | `verb_form` | PT analysis; counterfactual and hypothetical conditional constructions | Extremely rare (~1 per official book); document as sub-pattern of `verb_form` rather than standalone key |

Keys previously pending that were **promoted to production in v7:**
`adjective_adverb_distinction` → D.2.5 (modifier),
`illogical_comparison` → D.2.5 (modifier),
`commonly_confused_words` → D.2.8 (expression_of_ideas)

---

## D.3 Disambiguation Rules

Apply these priority rules whenever multiple labels seem possible.

1. `sentence_boundary` > general `punctuation`
2. `logical_predication` > `modifier_placement`, `comparative_structures`, `parallel_structure`, `conjunction_usage`
3. `transition_logic` > `conjunction_usage`, `parallel_structure`
4. `conjunctive_adverb_usage` > general `punctuation`, `conjunction_usage`
5. `negation` > `logical_predication`, `parallel_structure`, `modifier_placement`, `verb_form`
6. `pronoun_case` > `pronoun_antecedent_agreement`
7. `pronoun_clarity` > `pronoun_antecedent_agreement`
8. `comparative_structures` > `parallel_structure`, `modifier_placement`
9. `voice_active_passive` > general `verb_form`
10. `noun_countability` > `subject_verb_agreement`
11. `relative_pronouns` > `modifier_placement`
12. `possessive_contraction` > `apostrophe_use`
13. `hyphen_usage` > general `punctuation`, `modifier_placement`
14. `preposition_idiom` > `conjunction_usage` — specific verb-preposition pairings take precedence over general conjunction mechanics
15. `unnecessary_internal_punctuation` > general `punctuation_comma` when the test is whether punctuation should be absent inside a syntactic unit
16. `end_punctuation_question_statement` > general `punctuation` when the test is period vs question mark based on sentence type
17. `commonly_confused_words` > `precision_word_choice` when competing options are words that sound or look similar but differ categorically in meaning (`affect`/`effect`, `principle`/`principal`); use `precision_word_choice` only when options are synonyms of varying specificity within the same semantic field

Always write the selected rule in `disambiguation_rule_applied`.

---

## D.4 Decision Tree for Grammar Annotation

### Step 1: Is this Standard English Conventions?

If the answer is chosen because of grammar, punctuation, sentence structure,
or usage → `conventions_grammar`. If because of transition logic, note
synthesis, concision, or rhetorical goal → Expression of Ideas.

### Step 2: Is the issue a sentence boundary?

Fragment, comma splice, run-on, period vs semicolon vs comma at clause
boundaries → sentence-boundary keys.

### Step 3: Is the issue punctuation mechanics?

- comma → `punctuation_comma`
- semicolon → `semicolon_use`
- colon/dash → `colon_dash_use`
- apostrophe → `apostrophe_use`
- conjunctive adverb punctuation → `conjunctive_adverb_usage`
- appositive punctuation → `appositive_punctuation`
- absent punctuation inside a syntactic unit → `unnecessary_internal_punctuation`
- period vs question mark based on sentence type → `end_punctuation_question_statement`

### Step 4: Is the issue agreement?

`subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`,
`determiners_articles`.

### Step 5: Is the issue verb form?

`verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation`.

### Step 6: Is the issue modifier logic?

`modifier_placement`, `comparative_structures`, `logical_predication`,
`relative_pronouns`.

### Step 7: Is the issue pronoun-specific?

`pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement`.

### Step 8: Is the issue parallel or idiomatic structure?

`parallel_structure`, `elliptical_constructions`, `conjunction_usage`.

### Step 9: If multiple rules apply

Choose the primary rule that eliminates the most wrong options. Store others
in `secondary_grammar_focus_keys`.

---

## D.5 Syntactic Trap Keys

Use `syntactic_trap_key` to describe the difficulty mechanism, not the rule
being tested.

Approved keys:

- `none`
- `nearest_noun_attraction`
- `garden_path`
- `early_clause_anchor`
- `nominalization_obscures_subject`
- `interruption_breaks_subject_verb`
- `long_distance_dependency`
- `pronoun_ambiguity`
- `scope_of_negation`
- `modifier_attachment_ambiguity`
- `presupposition_trap`
- `temporal_sequence_ambiguity`
- `multiple`

Use `review_notes` for narrower subpatterns such as inversion agreement,
introductory-clause comma, nonrestrictive-element comma, or conjunctive-adverb
semicolon patterns. Do not invent new `syntactic_trap_key` values for those
subpatterns unless they are first added to the backend ontology.

`syntactic_trap_intensity` values: `low`, `medium`, `high`. Required for all
generation profiles.

---

## D.6 Tense and Register Keys

### D.6.1 `passage_tense_register_key` values

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`
- `literary_present`

### D.6.2 Expected patterns

- Narrative/literary passages → past tense
- Scientific facts → simple present
- Historical accounts → past tense
- Study procedures → past tense
- Established findings → present tense
- Past perfect → events completed before another past event
- **Literary present** → when a passage discusses actions, events, or
  patterns *inside* a literary work (novel, poem, play, short story),
  use simple present even if the work was written in the past. Verbs
  describing what characters do, what the text says, or what patterns
  appear in the work use simple present. Frame: "In the novel / poem /
  story, [character] ______." Wrong options offer past tense or present
  perfect.

### D.6.3 Required fields for verb-form questions

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

Allowed `expected_tense_key` values: `simple_present`, `simple_past`,
`present_perfect`, `past_perfect`, `future`, `conditional`, `subjunctive`,
`imperative`.

This block is mandatory for every question where `grammar_role_key` is
`verb_form` or `grammar_focus_key` is `verb_tense_consistency`, `verb_form`,
or `voice_active_passive`.

---

## D.7 Student Failure Mode Keys

Every distractor must include `student_failure_mode_key`.

### Reading-oriented failure modes

`nearest_noun_reflex`, `comma_fix_illusion`, `formal_word_bias`,
`longer_answer_bias`, `punctuation_intimidation`, `surface_similarity_bias`,
`scope_blindness`, `modifier_hitchhike`, `chronological_assumption`,
`extreme_word_trap`, `overreading`, `underreading`, `grammar_fit_only`,
`register_confusion`, `pronoun_anchor_error`, `parallel_shape_bias`,
`transition_assumption`, `idiom_memory_pull`, `false_precision`,
`tense_proximity_pull`

### Grammar-specific failure modes

`internal_unit_punctuation_insertion` — student inserts comma or dash inside
a required syntactic unit (subject–verb, verb–object, preposition–complement)

`declarative_question_confusion` — student applies a question mark to a
sentence that contains an embedded indirect question but is itself declarative

`restrictive_appositive_comma_insertion` — student adds commas around a
restrictive appositive that requires none

`title_name_comma_insertion` — student inserts a comma between a title/role
noun and the proper name that follows it

`nonfinite_for_finite` — student chooses a participle or infinitive where a
finite verb is required in a main clause or relative clause

`inflected_after_modal` — student chooses a past-tense, third-person-singular,
gerund, or participle form after a modal auxiliary, including when the modal is
shared across coordinated verbs joined by "and"

`plural_pronoun_for_clause_antecedent` — student chooses a plural pronoun when
the antecedent is an entire preceding clause or event

`past_tense_for_literary_present` — student uses simple past when discussing
events inside a literary work, which conventionally uses simple present

`transition_wrong_direction` — student chooses a transition word that signals
the opposite logical relationship (e.g., "however" for a result, "therefore"
for a contrast)

`notes_synthesis_wrong_goal` — student chooses a sentence that addresses the
right topic but performs a different rhetorical action than the stem requires

`notes_synthesis_audience_mismatch` — student chooses a sentence appropriate
for a familiar audience when the stem requires one for an unfamiliar audience,
or vice versa

`adverb_adjective_confusion` — student selects adjective form after an action
verb, or adverb form after a linking verb, by failing to identify the verb class

`illogical_comparison_blindness` — student does not notice that the compared
elements belong to different grammatical or logical categories because the
sentence reads fluently on first pass

`confused_word_substitution` — student selects a word that sounds or looks like
the correct one but belongs to a different semantic category (e.g., "effect"
for "affect"), typically because the two words share phonological similarity

`preposition_idiom_error` — student selects a preposition based on a related
but incorrect idiomatic collocation, often drawn from a superficially similar
verb-preposition pair

`notes_synthesis_content_omission` — student selects a sentence that addresses
the rhetorical goal but omits a specific required content element (a numerical
value, title, year, quoted text, or other named content) required by the stem

---

## D.8 Schema Guardrails and Enforcement

### D.8.1 `grammar_role_key` → `grammar_focus_key` mapping

| `grammar_role_key` | Allowed `grammar_focus_key` values |
|---|---|
| `sentence_boundary` | `sentence_fragment`, `comma_splice`, `run_on_sentence`, `sentence_boundary` |
| `agreement` | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`, `determiners_articles`, `affirmative_agreement` |
| `verb_form` | `verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation` |
| `modifier` | `modifier_placement`, `comparative_structures`, `illogical_comparison`, `adjective_adverb_distinction`, `logical_predication`, `relative_pronouns` |
| `punctuation` | `punctuation_comma`, `colon_dash_use`, `semicolon_use`, `conjunctive_adverb_usage`, `apostrophe_use`, `possessive_contraction`, `appositive_punctuation`, `hyphen_usage`, `quotation_punctuation`, `unnecessary_internal_punctuation`, `end_punctuation_question_statement` |
| `parallel_structure` | `parallel_structure`, `elliptical_constructions`, `conjunction_usage` |
| `pronoun` | `pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement` |
| `expression_of_ideas` | `redundancy_concision`, `precision_word_choice`, `register_style_consistency`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `transition_logic`, `commonly_confused_words`, `preposition_idiom` |

### D.8.2 Domain separation

| Official SAT domain | `question_family_key` | Official skill families | `grammar_role_key` usage |
|---|---|---|---|
| Standard English Conventions | `conventions_grammar` | `Boundaries`, `Form, Structure, and Sense` | Required |
| Expression of Ideas | `expression_of_ideas` | `Transitions`, `Rhetorical Synthesis` | Optional; only if grammar-adjacent |
| Craft and Structure | `craft_and_structure` | `Words in Context`, `Text Structure and Purpose`, `Cross-Text Connections` | Forbidden |
| Information and Ideas | `information_and_ideas` | `Central Ideas and Details`, `Inferences`, `Command of Evidence` | Forbidden |

### D.8.3 Frequency table

| Frequency band | Grammar focus keys |
|---|---|
| `very_high` | `punctuation_comma`, `subject_verb_agreement` |
| `high` | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation` |
| `medium` | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure`, `unnecessary_internal_punctuation`, `end_punctuation_question_statement`, `finite_verb_in_main_clause` (verb_form sub-pattern), `modal_plus_plain_form` (verb_form sub-pattern), `adjective_adverb_distinction`, `illogical_comparison` |
| `low` | `voice_active_passive`, `logical_predication`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation`, `finite_verb_in_relative_clause` (verb_form sub-pattern), `singular_event_reference` (pronoun sub-pattern), `literary_present` (tense register), `commonly_confused_words`, `preposition_idiom`, `conjunction_usage` |
| `very_low` | `affirmative_agreement` ⚠️, `negation` ⚠️, `noun_countability`, `determiners_articles`, `elliptical_constructions` — ⚠️ = dsat_confidence: low; do not use in generation |

The generation profile must include `target_frequency_band`. Do not generate
a `very_low` frequency item unless explicitly instructed.

### D.8.4 Evidence span selection rules

Quote the minimal text that justifies the correct answer. Include the
grammatical subject and corrected element. Use `"..."` ellipsis for spans
exceeding 8 words. For punctuation items, include words immediately before
and after the punctuation decision.

### D.8.5 `disambiguation_rule_applied` must be explicit

Quote the exact priority rule from D.3 when a conflict is resolved.

### D.8.6 Amendment proposals must include parent role and evidence

`proposed_parent_role_key` must be an existing `grammar_role_key` or a new
role proposal with justification. `evidence_text` must quote the exact item
text that triggered the proposal.

---

## D.9 Final Output Field Requirements

The agent must return:

- Valid JSON in ingestion mode
- No invented keys
- Exactly four answer options
- Exactly one correct option
- `grammar_focus_key` only when appropriate
- `option_error_focus_key` for grammar distractors
- `generation_profile` for every ingested item
- `secondary_grammar_focus_keys` when multiple rules apply
- `disambiguation_rule_applied` when any label conflict was resolved
- `classification_rationale` for every classification
- `is_no_change_question` when original text is an option
- `passage_tense_register_key` and `expected_tense_key` for all verb-form items
- `syntactic_trap_intensity` for all generation profiles
- `target_frequency_band` for all generation profiles
- `transition_subtype_key` on classification and all options for transition items
- `synthesis_goal_key`, `audience_knowledge_key`, `required_content_key` for notes synthesis items
- `test_format_key` on all generated modules

---

# PART E — QUALITY PROTOCOLS

---

## E.1 SAT Realism and Distractor Competition

### E.1.1 Core principle

Hard SAT questions are difficult because distractors are close to correct,
wrong answers are attractive, elimination requires precise reasoning, and
multiple answers appear initially plausible. Difficulty must come from
distractor competition, not obscure vocabulary.

### E.1.2 Distractor distance

```json
{ "distractor_distance": "tight" }
```

Allowed values: `wide`, `moderate`, `tight`. `tight` required for realistic
hard SAT items.

### E.1.3 Distractor competition score

```json
{ "distractor_competition_score": 0.91 }
```

Minimum acceptable: 0.75. Preferred: 0.85+.

### E.1.4 Answer separation strength

```json
{ "answer_separation_strength": "low" }
```

Official hard SAT items usually use `low`.

### E.1.5 Plausible wrong count

```json
{ "plausible_wrong_count": 3 }
```

Preferred production target: 3.

---

## E.2 Robust Distractor Engineering Protocol

Each distractor must satisfy:

1. One distinct failure mode only
2. One identifiable student failure mechanism (`student_failure_mode_key`)
3. No accidental second error
4. Plausible formal English
5. Must survive first-pass elimination
6. Must compete under time pressure
7. Must be wrong for a specific named reason

### E.2.1 Shared option-quality gate

Before finalizing any generated item, verify:

- **Incorrectness:** no distractor is defensibly co-correct with the key
- **Plausibility:** each distractor maps to a named student mistake and has
  a non-null `plausibility_source_key`
- **Diversity:** no two distractors fail through the same reasoning path or
  duplicate the same wrong idea
- **Construct alignment:** each distractor fails the tested grammar/usage
  construct, not an unrelated side issue
- **Clue control:** the key is not consistently longer, more precise, more
  academic, more idiomatic, or more polished than the distractors
- **Option homogeneity:** all four options share comparable syntax, register,
  abstraction level, and semantic category
- **Separation margin:** the key remains the single best answer, while hard
  items include at least two distractors that survive first-pass elimination

Each question must include:

- A primary trap distractor (targets the declared syntactic trap)
- A formal-sounding wrong answer (uses `formal_register_match`)
- A close semantic competitor (tight distractor distance)

The best hard SAT distractors are almost correct but not precise enough.

---

## E.3 Ground Truth Comparison

```json
{ "official_similarity_score": 0.93 }
```

Compared against PT1–PT6, Bluebook, and official released College Board items.
Production minimum: 0.82. Preferred: 0.90+.

---

## E.4 Anti-Clone Protection

```json
{ "structural_similarity_score": 0.81, "rewrite_required": true }
```

If similarity > 0.75: regenerate passage.

---

## E.5 Empirical Difficulty Calibration

```json
{ "empirical_difficulty_estimate": 0.64 }
```

Represents predicted miss rate.

---

## E.6 Human Override Resolution

```json
{
  "human_override_log": {
    "original_classification": "semicolon_use",
    "reviewer_change": "conjunctive_adverb_usage",
    "reason": "Semicolon required because conjunctive adverb follows."
  }
}
```

---

## E.7 Generation Provenance and Audit Trail

```json
{
  "generation_provenance": {
    "source_template_used": "agreement_template_v2",
    "generation_chain": ["passage_generated", "distractors_generated", "validator_adjusted"]
  }
}
```

---

## E.8 Final Validation

Before output validate:

- `distractor_distance` present on each distractor
- `student_failure_mode_key` present for every distractor
- `distractor_competition_score` >= 0.75
- `plausible_wrong_count` >= 2
- `answer_separation_strength` calibrated
- `passage_architecture_key` valid (from B.7) when stimulus is passage-length
- `official_similarity_score` >= threshold
- `structural_similarity_score` acceptable (not > 0.75)
- `empirical_difficulty_estimate` assigned
- Provenance complete
- `transition_subtype_key` present on classification and all options for `transition_logic` items
- `synthesis_goal_key`, `audience_knowledge_key`, `required_content_key` present for all `choose_best_notes_synthesis` items
- `synthesis_distractor_failure` present on all three wrong options for notes synthesis items
- `test_format_key` present on all generated modules
- Module question count matches `test_format_key`

If any fail: regenerate.

---

## Reference Quick-Index

| Concept | Location |
|---|---|
| Task mode detection | A.2 |
| Required output shape and all schemas | A.3 |
| Generation input specification | B.1 |
| Step-by-step generation workflow | B.2 |
| Passage construction rules by focus key | B.3 |
| Distractor heuristics by focus key | B.4 |
| Transition subtype vocabulary | B.5 |
| Notes synthesis metadata | B.6 |
| Passage architecture templates | B.7 |
| Difficulty calibration | B.8 |
| Batch, deduplication, ordering | B.9 |
| Explanation requirements | B.10 |
| No-Change generation | B.11 |
| Complete generation examples | B.12 |
| Generation validation checklist (checks 1–25) | B.13 |
| Error response format | B.14 |
| Real-time constraints | B.15 |
| Question fields | C.1 |
| stem_type_key values (all 17 types incl. Words in Context, Cross-Text, Inference) | C.1.2 |
| stimulus_mode_key values (incl. prose_plus_graph subtypes) | C.1.1 |
| Option-level analysis | C.2 |
| option_error_focus_key table | C.2.1 |
| precision_score scale | C.2.4 |
| grammar_fit / tone_match semantics | C.2.5 |
| No-change and original-text rule | C.3 |
| Multi-error rule | C.4 |
| Amendment process | C.5 |
| Review flags | C.6 |
| Pilot ingestion examples | C.7 |
| Grammar role keys | D.1 |
| Grammar focus keys | D.2 |
| Proposed keys (pending) | D.2.9 |
| Disambiguation rules | D.3 |
| Decision tree | D.4 |
| Syntactic trap keys | D.5 |
| Tense/register keys (incl. literary_present) | D.6 |
| Student failure mode keys | D.7 |
| Role→focus mapping | D.8.1 |
| Domain separation | D.8.2 |
| Frequency table | D.8.3 |
| Evidence span rules | D.8.4 |
| Final output field requirements | D.9 |
| SAT realism / distractor competition | E.1 |
| Robust distractor engineering | E.2 |
| Ground truth comparison | E.3 |
| Anti-clone protection | E.4 |
| Empirical difficulty calibration | E.5 |
| Human override resolution | E.6 |
| Generation provenance | E.7 |
| Final validation | E.8 |

---

*Document version: v7.0 — 2026-04-29*
*Taxonomy audit and corrections vs official College Board documentation*
*Extends v6.0 (which merged v3.md + v3_1.md)*
*Agent: Claude Sonnet 4.6 (`claude-sonnet-4-6`)*
*Domain coverage: Standard English Conventions, Expression of Ideas*
*Companion file: `rules_agent_dsat_reading_v2.md`*

## Appendix V — Controlled Vocabulary (generated)

The key lists below are generated from `vocabulary/master.json` by
`scripts/gen_vocab.py`. Do not hand-edit them — edit master.json and
regenerate. They stay in lockstep with the validator enums in
`backend/app/models/ontology.py`.

<!-- VOCAB:system:CONTENT_ORIGINS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CONTENT_ORIGINS`** — Content origin

- `official`
- `unofficial`
- `generated`
<!-- VOCAB:system:CONTENT_ORIGINS END -->

<!-- VOCAB:system:JOB_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`JOB_TYPES`** — Job types

- `ingest`
- `generate`
- `reannotate`
- `overlap_check`
<!-- VOCAB:system:JOB_TYPES END -->

<!-- VOCAB:system:JOB_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`JOB_STATUSES`** — Job statuses (state machine)

- `pending`
- `parsing`
- `extracting`
- `generating`
- `annotating`
- `overlap_checking`
- `validating`
- `approved`
- `needs_review`
- `failed`
- `failed_transient` — Job failed with a transient error after auto-retry exhaustion (HTTP 429, 5xx, timeout, provider rate limit). Eligible for admin retry via /generate/batches/{id}/retry-failed.
- `failed_permanent` — Job failed with a non-recoverable error (malformed JSON after repair, model refusal, validation failure). Does not auto-retry; admin must regenerate-from-spec.
- `retrying` — Row-level guard set during a retry attempt to prevent duplicate concurrent retries of the same job.
<!-- VOCAB:system:JOB_STATUSES END -->

<!-- VOCAB:system:PRACTICE_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PRACTICE_STATUSES`** — Practice status

- `draft`
- `active`
- `retired`
- `rejected` — Failed quality review; terminal state, audit-preserved. Distinct from retired (post-active removal).
<!-- VOCAB:system:PRACTICE_STATUSES END -->

<!-- VOCAB:system:OVERLAP_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`OVERLAP_STATUSES`** — Overlap status

- `none`
- `possible`
- `confirmed`
<!-- VOCAB:system:OVERLAP_STATUSES END -->

<!-- VOCAB:system:RELATION_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`RELATION_TYPES`** — Relation types

- `overlaps_official`
- `derived_from`
- `near_duplicate`
- `generated_from`
- `adapted_from`
<!-- VOCAB:system:RELATION_TYPES END -->

<!-- VOCAB:system:ASSET_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`ASSET_TYPES`** — Asset types

- `pdf`
- `image`
- `screenshot`
- `markdown`
- `json`
- `text`
<!-- VOCAB:system:ASSET_TYPES END -->

<!-- VOCAB:system:CHANGE_SOURCES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CHANGE_SOURCES`** — Change sources

- `ingest`
- `generate`
- `admin_edit`
- `reprocess`
<!-- VOCAB:system:CHANGE_SOURCES END -->

<!-- VOCAB:shared:STIMULUS_MODE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STIMULUS_MODE_KEYS`** — V3 §3.1 stimulus_mode_key

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `notes_bullets`
- `notes_summary`
- `poem`
<!-- VOCAB:shared:STIMULUS_MODE_KEYS END -->

<!-- VOCAB:system:TEST_FORMAT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TEST_FORMAT_KEYS`** — Rules v7 generation format keys

- `digital_app_adaptive`
- `nondigital_linear_accommodation`
<!-- VOCAB:system:TEST_FORMAT_KEYS END -->

<!-- VOCAB:system:SOURCE_STATS_FORMAT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SOURCE_STATS_FORMAT_KEYS`** — Rules v7 source stats format keys

- `official_digital`
- `official_nondigital_linear`
<!-- VOCAB:system:SOURCE_STATS_FORMAT_KEYS END -->

<!-- VOCAB:shared:STEM_TYPE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STEM_TYPE_KEYS`** — V3 §3.2 stem_type_key

- `complete_the_text`
- `choose_main_idea`
- `choose_main_purpose`
- `choose_structure_description`
- `choose_sentence_function`
- `choose_likely_response`
- `choose_best_support`
- `choose_best_quote`
- `choose_best_completion_from_data`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`
- `choose_words_in_context`
- `choose_word_in_context`
- `choose_cross_text_connection`
- `choose_text_relationship`
- `choose_agreement_across_texts`
- `choose_difference_across_texts`
- `choose_best_inference`
- `choose_command_of_evidence_textual`
- `choose_command_of_evidence_quantitative`
- `choose_central_detail`
- `choose_detail`
- `choose_best_illustration`
- `choose_best_weakener`
- `conform_to_standard_english`
- `most_logically_completes`
- `synthesize_information`
- `compare_contributions`
<!-- VOCAB:shared:STEM_TYPE_KEYS END -->

<!-- VOCAB:grammar:GRAMMAR_ROLE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`GRAMMAR_ROLE_KEYS`** — V3 §5 grammar_role_key

- `sentence_boundary`
- `agreement`
- `verb_form`
- `modifier`
- `punctuation`
- `parallel_structure`
- `pronoun`
- `expression_of_ideas`
<!-- VOCAB:grammar:GRAMMAR_ROLE_KEYS END -->

<!-- VOCAB:grammar:GRAMMAR_FOCUS_BY_ROLE START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`GRAMMAR_FOCUS_BY_ROLE`** — V3 §6 grammar_focus_key (grouped by role)

- **`sentence_boundary`**
  - `sentence_fragment`
  - `comma_splice`
  - `run_on_sentence`
  - `sentence_boundary`
- **`agreement`**
  - `subject_verb_agreement`
  - `pronoun_antecedent_agreement`
  - `noun_countability`
  - `determiners_articles`
  - `affirmative_agreement`
- **`verb_form`**
  - `verb_tense_consistency`
  - `verb_form`
  - `voice_active_passive`
  - `negation`
- **`modifier`**
  - `modifier_placement`
  - `comparative_structures`
  - `illogical_comparison`
  - `adjective_adverb_distinction`
  - `logical_predication`
  - `relative_pronouns`
- **`punctuation`**
  - `punctuation_comma`
  - `colon_dash_use`
  - `semicolon_use`
  - `conjunctive_adverb_usage`
  - `apostrophe_use`
  - `possessive_contraction`
  - `appositive_punctuation`
  - `hyphen_usage`
  - `quotation_punctuation`
  - `unnecessary_internal_punctuation`
  - `end_punctuation_question_statement`
- **`parallel_structure`**
  - `parallel_structure`
  - `elliptical_constructions`
  - `conjunction_usage`
- **`pronoun`**
  - `pronoun_case`
  - `pronoun_clarity`
  - `pronoun_antecedent_agreement`
- **`expression_of_ideas`**
  - `redundancy_concision`
  - `precision_word_choice`
  - `register_style_consistency`
  - `logical_relationships`
  - `emphasis_meaning_shifts`
  - `data_interpretation_claims`
  - `transition_logic`
  - `commonly_confused_words`
  - `preposition_idiom`
<!-- VOCAB:grammar:GRAMMAR_FOCUS_BY_ROLE END -->

<!-- VOCAB:grammar:SYNTACTIC_TRAP_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SYNTACTIC_TRAP_KEYS`** — V3 §9 syntactic_trap_key

- `none`
- `nearest_noun_attraction`
- `garden_path`
- `early_clause_anchor`
- `nominalization_obscures_subject`
- `interruption_breaks_subject_verb`
- `long_distance_dependency`
- `pronoun_ambiguity`
- `scope_of_negation`
- `modifier_attachment_ambiguity`
- `presupposition_trap`
- `temporal_sequence_ambiguity`
- `multiple`
<!-- VOCAB:grammar:SYNTACTIC_TRAP_KEYS END -->

<!-- VOCAB:shared:DISTRACTOR_TYPE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DISTRACTOR_TYPE_KEYS`** — V3 §12.1 distractor_type_key (option-level)

- `semantic_imprecision`
- `logical_mismatch`
- `scope_error`
- `tone_mismatch`
- `grammar_error`
- `punctuation_error`
- `transition_mismatch`
- `data_misread`
- `goal_mismatch`
- `partially_supported`
- `overstatement`
- `understatement`
- `rhetorical_irrelevance`
- `partial_match`
- `correct`
- `topical_relevance_without_logical_connection`
- `indirect_evidence`
- `inverted_logic`
- `detail_trap`
- `overreach`
- `data_context_mismatch`
- `connotation_mismatch`
- `plausible_synonym`
- `wrong_action_verb`
- `reversed_attribution`
- `confirmed_when_contradicted`
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `cause_effect_misalignment`
- `contradiction`
- `figurative_literal_confusion`
- `false_concession_trap`
<!-- VOCAB:shared:DISTRACTOR_TYPE_KEYS END -->

<!-- VOCAB:shared:ANSWER_MECHANISM_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`ANSWER_MECHANISM_KEYS`** — V3 §3.3 answer_mechanism_key

- `rule_application`
- `pattern_matching`
- `evidence_location`
- `inference`
- `data_synthesis`
- `evidence_matching`
- `contextual_substitution`
- `rhetorical_classification`
- `cross_text_comparison`
- `polarity_resolution`
<!-- VOCAB:shared:ANSWER_MECHANISM_KEYS END -->

<!-- VOCAB:shared:SOLVER_PATTERN_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SOLVER_PATTERN_KEYS`** — V3 §3.3 solver_pattern_key

- `apply_grammar_rule_directly`
- `locate_error_zone`
- `compare_register`
- `evaluate_transition`
- `synthesize_notes`
- `eliminate_by_boundary`
- `locate_claim_then_match_evidence`
- `read_graphic_then_match_claim`
- `summarize_then_compare`
- `locate_detail_directly`
- `identify_logical_gap`
- `substitute_and_test`
- `classify_rhetorical_move`
- `summarize_both_then_compare`
- `apply_negation_logic`
- `locate_figurative_function`
<!-- VOCAB:shared:SOLVER_PATTERN_KEYS END -->

<!-- VOCAB:shared:STUDENT_FAILURE_MODE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`STUDENT_FAILURE_MODE_KEYS`** — V3 §21.3 student_failure_mode_key

- `nearest_noun_reflex`
- `comma_fix_illusion`
- `formal_word_bias`
- `longer_answer_bias`
- `punctuation_intimidation`
- `surface_similarity_bias`
- `scope_blindness`
- `modifier_hitchhike`
- `chronological_assumption`
- `extreme_word_trap`
- `overreading`
- `underreading`
- `grammar_fit_only`
- `register_confusion`
- `pronoun_anchor_error`
- `parallel_shape_bias`
- `transition_assumption`
- `idiom_memory_pull`
- `false_precision`
- `negation_blindness`
- `connotation_surface_match`
- `local_role_misread`
- `register_tone_blindness`
- `figurative_meaning_blindness`
- `exact_value_misread`
- `individual_from_aggregate`
- `all_measures_not_checked`
- `wrong_comparison_direction`
- `wrong_group_selected`
- `wrong_row_column_lookup`
- `single_measure_overread`
- `local_maximum_overread`
- `absolute_value_overweighting`
- `constraint_ignored`
- `two_part_claim_partial_match`
- `control_group_misidentification`
- `evidence_scope_mismatch`
- `subgroup_overgeneralization`
- `parenthetical_function_confusion`
- `rhetorical_verb_partial`
- `scope_role_confusion`
- `author_action_overread`
- `attribution_swap`
- `agreement_degree_overread`
- `relationship_simplification`
- `polarity_blindness`
- `tense_proximity_pull`
- `internal_unit_punctuation_insertion`
- `declarative_question_confusion`
- `restrictive_appositive_comma_insertion`
- `title_name_comma_insertion`
- `nonfinite_for_finite`
- `inflected_after_modal`
- `plural_pronoun_for_clause_antecedent`
- `past_tense_for_literary_present`
- `transition_wrong_direction`
- `notes_synthesis_wrong_goal`
- `notes_synthesis_audience_mismatch`
- `adverb_adjective_confusion`
- `illogical_comparison_blindness`
- `confused_word_substitution`
- `preposition_idiom_error`
- `notes_synthesis_content_omission`
<!-- VOCAB:shared:STUDENT_FAILURE_MODE_KEYS END -->

<!-- VOCAB:shared:DISTRACTOR_DISTANCE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DISTRACTOR_DISTANCE_KEYS`** — V3 §21.2 distractor_distance

- `wide`
- `moderate`
- `tight`
<!-- VOCAB:shared:DISTRACTOR_DISTANCE_KEYS END -->

<!-- VOCAB:shared:DIFFICULTY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`DIFFICULTY_KEYS`** — V3 §3.3 difficulty keys

- `low`
- `medium`
- `high`
<!-- VOCAB:shared:DIFFICULTY_KEYS END -->

<!-- VOCAB:shared:FREQUENCY_BANDS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`FREQUENCY_BANDS`** — V3 §3.3 frequency bands

- `very_high`
- `high`
- `medium`
- `low`
- `very_low`
<!-- VOCAB:shared:FREQUENCY_BANDS END -->

<!-- VOCAB:shared:TENSE_REGISTER_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TENSE_REGISTER_KEYS`** — V3 §17.6 tense register keys

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`
- `literary_present`
<!-- VOCAB:shared:TENSE_REGISTER_KEYS END -->

<!-- VOCAB:shared:PASSAGE_ARCHITECTURE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PASSAGE_ARCHITECTURE_KEYS`** — V3 §22 passage_architecture_key

- `science_setup_finding_implication`
- `science_hypothesis_method_result`
- `history_claim_evidence_limitation`
- `history_assumption_revision`
- `literature_observation_interpretation_shift`
- `literature_character_conflict_reveal`
- `economics_theory_exception_example`
- `economics_problem_solution_tradeoff`
- `rhetoric_claim_counterclaim_resolution`
- `notes_fact_selection_contrast`
- `unexpected_finding`
- `cautionary_framing`
- `problem_solution`
- `compare_contrast`
- `chronological_sequence`
- `research_summary`
- `claim_evidence_explanation`
- `analogy_driven_argument`
- `multi_perspective_presentation`
- `qualification_restatement`
- `experiment_hypothesis_control_result`
- `indirect_effect_mediation`
- `alternative_explanation_ruled_out`
- `mechanism_manipulation_test`
- `studied_subgroup_generalization_limit`
<!-- VOCAB:shared:PASSAGE_ARCHITECTURE_KEYS END -->

<!-- VOCAB:shared:QUESTION_FAMILY_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`QUESTION_FAMILY_KEYS`** — question_family_key

- `conventions_grammar`
- `expression_of_ideas`
- `craft_and_structure`
- `information_and_ideas`
<!-- VOCAB:shared:QUESTION_FAMILY_KEYS END -->

<!-- VOCAB:grammar:TRANSITION_SUBTYPE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TRANSITION_SUBTYPE_KEYS`** — Grammar v7 transition_subtype_key

- `sequence_final_event`
- `contrast_refutation`
- `addition`
- `result_consequence`
- `chronology`
- `alternative`
- `emphasis_support`
- `causal_chain`
- `specificity_elaboration`
- `purpose_action`
- `frequency_difference`
- `simultaneity`
- `similarity`
- `appropriateness`
- `change_over_time`
- `exception`
- `final_realization`
- `converse_opposite`
- `present_continuation`
- `direct_refutation`
- `logical_consequence`
- `concession_qualification`
- `example`
- `restatement_clarification`
<!-- VOCAB:grammar:TRANSITION_SUBTYPE_KEYS END -->

<!-- VOCAB:grammar:SYNTHESIS_GOAL_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SYNTHESIS_GOAL_KEYS`** — Grammar v7 notes synthesis goal keys

- `emphasize_similarity`
- `emphasize_difference`
- `explain_advantage`
- `explain_mechanism`
- `present_research`
- `present_theory`
- `introduce_work`
- `describe_work`
- `emphasize_achievement`
- `make_generalization`
- `contrast_quantities`
- `compare_measurements`
- `emphasize_sample`
- `identify_category`
- `identify_profession`
- `identify_setting`
- `identify_title`
- `identify_year`
- `identify_duration`
- `identify_distance`
- `identify_author_pseudonym`
- `contrast_structural_types`
- `present_study_aim`
- `identify_statistical_method`
- `identify_statistical_authorship_method`
- `explain_technique_advantage`
- `explain_misconception_naming`
- `challenge_with_quotation`
- `challenge_explanation_with_quote`
- `present_study_overview`
- `present_methodology`
- `present_study_conclusions`
- `emphasize_significance`
- `explain_format_advantage`
- `emphasize_duration_and_purpose`
- `emphasize_size_similarity`
- `contrast_origins`
- `provide_historical_overview`
- `contrast_formal_structures`
- `contextualize_changing_beliefs`
- `compare_hypothesis_scope`
- `emphasize_age_similarity`
<!-- VOCAB:grammar:SYNTHESIS_GOAL_KEYS END -->

<!-- VOCAB:grammar:AUDIENCE_KNOWLEDGE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`AUDIENCE_KNOWLEDGE_KEYS`** — Grammar v7 audience knowledge keys

- `audience_familiar`
- `audience_unfamiliar`
- `not_specified`
<!-- VOCAB:grammar:AUDIENCE_KNOWLEDGE_KEYS END -->

<!-- VOCAB:grammar:REQUIRED_CONTENT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REQUIRED_CONTENT_KEYS`** — Grammar v7 required content keys

- `comparison_needed`
- `definition_needed`
- `background_omit`
- `measurement_values_needed`
- `result_needed`
- `title_and_content_needed`
- `achievement_needed`
- `owner_of_achievement_needed`
- `category_label_needed`
- `sample_location_needed`
- `profession_label_needed`
- `setting_needed`
- `year_needed`
- `duration_needed`
- `distance_needed`
- `author_identity_needed`
- `mechanism_needed`
- `structural_roles_needed`
- `study_aim_needed`
- `statistical_method_needed`
- `misconception_needed`
- `quotation_needed`
- `study_finding_summary_needed`
- `method_needed`
- `conclusion_needed`
- `significance_needed`
- `advantage_needed`
- `purpose_needed`
- `origin_labels_needed`
- `timeline_needed`
- `formal_feature_labels_needed`
- `scope_terms_needed`
<!-- VOCAB:grammar:REQUIRED_CONTENT_KEYS END -->

<!-- VOCAB:grammar:SYNTHESIS_DISTRACTOR_FAILURE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SYNTHESIS_DISTRACTOR_FAILURE_KEYS`** — Grammar v7 synthesis distractor failure keys

- `wrong_goal`
- `omits_required_content`
- `adds_background_audience_does_not_need`
- `correct_topic_wrong_comparison`
- `omits_unfamiliar_context`
- `wrong_audience_assumption`
- `misstates_required_relationship`
- `irrelevant_background`
<!-- VOCAB:grammar:SYNTHESIS_DISTRACTOR_FAILURE_KEYS END -->

<!-- VOCAB:shared:TOPIC_BROAD_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TOPIC_BROAD_KEYS`** — Broad topic keys

- `science`
- `history`
- `literature`
- `social_studies`
- `humanities`
- `arts`
- `economics`
- `technology`
- `environment`
<!-- VOCAB:shared:TOPIC_BROAD_KEYS END -->

<!-- VOCAB:shared:PLAUSIBILITY_SOURCE_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`PLAUSIBILITY_SOURCE_KEYS`** — V3 §10.3 plausibility_source_key

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`
- `none`
- `passage_vocabulary_overlap`
- `topical_proximity`
- `partial_truth`
- `common_sense_appeal`
- `common_definition_appeal`
- `near_synonym_appeal`
- `rhetorical_surface_similarity`
- `attribution_swap`
<!-- VOCAB:shared:PLAUSIBILITY_SOURCE_KEYS END -->

<!-- VOCAB:system:REVIEW_TASK_TYPES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_TASK_TYPES`** — Review task types for the generation review swarm

- `generation_realism_review` — Multi-model quality review of generated DSAT questions
<!-- VOCAB:system:REVIEW_TASK_TYPES END -->

<!-- VOCAB:system:REVIEW_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_STATUSES`** — Per-reviewer outcome status

- `ok` — Review completed successfully
- `transient_failed` — Review failed due to transient error (rate limit, network)
- `permanent_failed` — Review failed permanently (malformed output, model refusal)
<!-- VOCAB:system:REVIEW_STATUSES END -->

<!-- VOCAB:system:REVIEW_RUN_STATUSES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_RUN_STATUSES`** — Review run lifecycle status

- `running` — Review run in progress
- `complete` — All reviewers completed successfully
- `partial` — Some reviewers failed but minimum completed
- `failed` — Review run failed entirely
<!-- VOCAB:system:REVIEW_RUN_STATUSES END -->

<!-- VOCAB:system:TRIGGERED_BY_VALUES START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`TRIGGERED_BY_VALUES`** — What triggered a review run

- `auto_on_save` — Automatically triggered when a generated question is saved
- `manual_question` — Admin manually triggered review for a single question
- `manual_batch` — Admin manually triggered review for a batch
- `recalibration` — Re-review triggered by calibration threshold change
- `rubric_bump` — Re-review triggered by rubric version change
<!-- VOCAB:system:TRIGGERED_BY_VALUES END -->

<!-- VOCAB:system:REVIEW_VERDICTS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REVIEW_VERDICTS`** — Per-reviewer verdict on a generated question

- `accept` — Question meets all quality thresholds
- `needs_human_review` — Borderline quality; human review recommended
- `reject` — Question fails quality thresholds
<!-- VOCAB:system:REVIEW_VERDICTS END -->

<!-- VOCAB:system:CONSENSUS_VERDICTS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`CONSENSUS_VERDICTS`** — Consensus verdict after multi-model review (Phase 5)

- `admin_review_ready` — All thresholds cleared; ready for admin review
- `reject_recommended` — Consensus recommends rejection
- `regenerate_recommended` — Consensus recommends regeneration
- `blocked_overlap` — Unresolved official overlap blocks approval
- `insufficient_reviews` — Fewer than 2 reviewers succeeded
<!-- VOCAB:system:CONSENSUS_VERDICTS END -->
