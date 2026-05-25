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

Maximum 5 sub-patterns per `grammar_focus_key`. This cap was raised from 3
in the v8.1 patch to accommodate the additional attested patterns documented
via the missing-rules audit (see `missing_rules_v8.md`). Adding a sixth
requires demoting one. Use the generation log to track demotions.

### B.3.0.5 Evidence tiers

Each focus key is assigned a tier in §B.3.0.6 based on PT example count in
`analysis/calibration/official_classifications.json` as of the v8 cut.

| Tier | PT examples | Sub-pattern policy |
|---|---|---|
| A | ≥5 | All PT-cited sub-patterns; up to 5 permitted |
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

**Sub-pattern — Inverted Sentence Order (Existential and Fronted Constructions)**

[NO PT EVIDENCE — source: PrepScholar, The College Panda]

Construct a sentence in which the grammatical subject follows the verb:
an existential construction (`There is/are…`, `Here is/are…`) or a
sentence with a fronted prepositional phrase (`Among the artifacts ___
three bronze figurines`). The blank sits at the verb slot. The correct
option agrees with the post-verbal subject, not with any noun in the
fronted phrase. The trap is that students trained to find the subject
before the verb latch onto the nearest preceding noun — which is not
the subject.

Distractors: singular verb agreeing with a singular noun in the fronted
phrase (nearest-noun attraction applied to an inverted structure), wrong
tense combined with wrong number, and a plural verb when the post-verbal
subject is singular.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Indefinite Pronoun as Singular Subject**

[NO PT EVIDENCE — source: PrepScholar, Magoosh]

Construct a sentence in which the grammatical subject is a singular
indefinite pronoun (`each`, `everyone`, `anyone`, `someone`, `no one`,
`everybody`, `anybody`, `somebody`, `nobody`, `everything`, `anything`,
`something`, `nothing`, `either`, `neither`, `whoever`, `whatever`).
Follow the indefinite pronoun with a prepositional phrase containing a
plural noun to create the attractor. The blank is the verb. The correct
option is always singular.

Canonical template: `Each of the [plural noun] ___ [predicate].`

Distractors: plural verb agreeing with the plural object of the
prepositional phrase, a tense-shifted plural form, and a third-person
plural progressive that doubles the error.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Compound Subject Joined by `or`/`nor` (Proximity Rule)**

[NO PT EVIDENCE — source: PrepScholar, Magoosh, The Critical Reader]

Construct a sentence with two subjects joined by `or`, `nor`, `either…or`,
or `neither…nor`. The blank is the verb. The correct option agrees with the
subject **closest to the verb** (proximity rule). Vary which subject is
closer to test both directions.

Templates:
- `Either the [singular noun] or the [plural noun] ___ .` → plural verb
- `Either the [plural noun] or the [singular noun] ___ .` → singular verb
- `Neither the results nor the method ___ .` → singular verb (singular
  subject closest to verb)

Distractors: verb agreeing with the first subject rather than the second,
plural verb treating the compound as equivalent to an `and`-compound, and
singular verb regardless of proximity.

Distinguish from `and`-compounds, which always take a plural verb.

Classify with `syntactic_trap_key: "long_distance_dependency"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Stacked Relative Clauses**

(PT5 M2 Q21: "a toxin that is deadly to nematodes that ___ in contact with it")

Construct a sentence with two nested relative clauses where the second
relative pronoun (`that` or `which`) refers to the plural noun embedded
*inside* the first relative clause, not to the singular head noun of the
entire noun phrase. The blank is the verb inside the second relative clause.
The correct option is plural.

Template: `a [singular noun] that [predicate] [plural noun] that ___ [phrase]`

The antecedent of the second `that` is the plural noun two clauses back
(`nematodes`), not the singular head noun (`toxin`). Students anchor to
the distant singular head or to the nearest singular noun immediately
before the second relative pronoun.

Distractors: singular verb agreeing with the singular head noun, singular
verb agreeing with an intervening singular noun, and present perfect where
simple present is required.

Classify with `syntactic_trap_key: "long_distance_dependency"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

### `pronoun_antecedent_agreement`

Use a singular antecedent that looks plural ("the team," "everyone"). Place a
plural noun nearby.

**Sub-pattern — Reflexive Pronoun Matching Plural Agent**

(PT1 M1 Q25: "turtle barnacles can dissolve the cement-like secretions they use to attach ___ to a sea turtle shell")

Construct a sentence whose grammatical subject is an explicitly plural agent
(`turtle barnacles`, `researchers`, `the dancers`) and that takes a reflexive
pronoun as the object of a verb of orientation, attachment, or self-action
(`attach`, `position`, `arrange`, `distinguish`). The blank holds the reflexive,
which must be plural (`themselves`) because reflexives copy the number of the
clause subject, not of any nearer singular noun in a prepositional phrase
(`to a sea turtle shell`, `from the rest of the colony`).

Distractors: the singular reflexive `itself` (agreement with a nearer singular
locale noun), the third-person plural object pronoun `them` (drops the
reflexive marker entirely), and a possessive-plus-self form (`their selves`)
that mis-spells the reflexive.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Plural Demonstrative Determiner Matching Plural Antecedent**

(PT7 M1 Q20: "Eighteen letters ___ at the New York Historical Society. ___ letters demonstrate Alcott's keen business sense")

Build two adjacent sentences (or a sentence pair across a period) in which the
first introduces a counted plural noun (`Eighteen letters`, `Three sketches`,
`Several manuscripts`) and the second opens with a demonstrative determiner
plus the same noun (`___ letters`, `___ sketches`). The blank holds the
demonstrative, which must be the plural form `These` or `Those`. The trap is
that the demonstrative sits at sentence-initial position with no immediately
visible antecedent inside its own clause, tempting a singular default
(`This`, `That`).

Distractors: singular `This` or `That` (mismatched number), a possessive form
(`Its`) that picks a wrong category of pronoun, and a bare article (`The`) that
strips the demonstrative pointing function the passage requires.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "pronoun_anchor_error"`.

**Sub-pattern — Possessive Pronoun for Singular Collective Phrase with Plural Tail Noun**

(PT10 M1 Q26: "gone are the types of pop culture references that made the artist a star … In ___ place is a far more personal subject")

Construct a sentence whose antecedent is a singular collective phrase whose
head noun is plural-looking (`the types of pop culture references`, `the body
of early sketches`, `the catalog of recordings`) and which is then referred to
by a possessive pronoun (`in ___ place`, `its scope`, `its influence`). The
phrase as a whole denotes a single thematic unit, so the pronoun must be
singular (`its`). The trap is the immediately preceding plural tail noun
(`references`, `sketches`, `recordings`), which pulls the reader toward a
plural possessive (`their`).

Distractors: plural possessive (`their`) keyed to the nearer plural tail noun,
contraction (`it's`) that swaps possessive for `it is`, and an ambiguous
pronoun (`there`) that misreads the slot as locative.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Singular `they`/`their` for Gender-Neutral Singular Antecedent**

[NO PT EVIDENCE — source: College Board Skills Insight, PrepScholar]

Construct a sentence in which the antecedent is a singular noun that does
not specify gender (`a student`, `the researcher`, `anyone`, `each person`)
and the blank holds a pronoun that refers back to it. The correct option is
`they`/`their`/`them` (singular they). The DSAT treats singular `they` as
the preferred form over `he or she`/`his or her` for gender-neutral singular
referents.

Template: `When a student submits ___ assignment late, ___ must accept the penalty.`

Distractors: `he or she` / `his or her` (older formal convention, now
non-preferred on the DSAT), a restructured plural subject that removes the
pronoun agreement requirement but changes meaning, and `it`/`its` (always
wrong for persons).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "pronoun_anchor_error"`.

### `verb_tense_consistency`

Open with a time marker. Place a distractor tense that matches a nearby
noun's temporal implication.

**Literary register variant:** Frame as discussion of a named literary work.
Target verb describes a character's action or the text's pattern. Correct
option: simple present. Wrong options: simple past, present perfect, past
perfect. Classify with `passage_tense_register_key: "literary_present"`.

**Sub-pattern — Past Perfect for the Earlier of Two Past Events**

(PT11 M1 Q20: "By 2023, she ___ one of the most celebrated musicians in Latin America")

Open with an explicit later-past reference point (`By 2023`, `By the end of the
1990s`, `By the time the expedition arrived`) and a participial or adverbial
tail that names a still-earlier accomplishment (`having released six studio
albums`). The blank holds the verb describing the earlier action, which must be
past perfect (`had become`, `had grown`) because it was already complete at the
later past anchor. The trap is that the surrounding clause is already in the
past, so simple past feels safe — but simple past collapses the two-stage
timeline the passage explicitly sets up.

Distractors: simple past (`became`) that ignores the prior-completion
requirement, future-in-past (`would become`) that mistakes the anchor for a
prediction, and present perfect (`has become`) that wrongly bridges to the
present.

Classify with `syntactic_trap_key: "temporal_sequence_ambiguity"`,
`student_failure_mode_key: "chronological_assumption"`, and
`passage_tense_register_key: "historical_past"`.

**Sub-pattern — Simple Past Anchored by Explicit Historical Date**

(PT7 M2 Q20: "In 1613, a prop cannon ___ during a performance and ignited the Globe's thatched roof")

Open the sentence (or the immediately preceding sentence) with a concrete
historical year, decade, or dated event (`In 1613`, `In 1929`, `During the
1930s`, `In January 2023`). The blank must be filled with simple past
(`misfired`, `used`, `swept`, `published`) because the date locks the action to
a single completed moment in history. The trap is that the surrounding passage
may also contain present-tense framing of the institution or finding (`is a
reconstruction of`, `is associated with`), tempting a present or present-
perfect form.

Distractors: present perfect (`has misfired`) that wrongly leaves the event
open-ended, simple present (`misfires`) that pulls from the framing tense, and
a nonfinite participle (`misfiring`) that leaves the clause without a finite
predicate.

Classify with `syntactic_trap_key: "none"`,
`student_failure_mode_key: "tense_proximity_pull"`, and
`passage_tense_register_key: "historical_past"`.

**Sub-pattern — Tense Shift to Present Triggered by "Today" / "Now"**

(PT1 M2 Q23: "Today, Paik ___ widely regarded as a pioneer of video art")

Set up a past-tense biographical or historical sentence (`In 1963, X
exhibited…`) and then open the target sentence with an explicit present-time
adverbial (`Today`, `Now`, `In the present day`, `Currently`). The blank must
take simple present (`is`, `remains`, `stands`) because the adverbial overrides
the surrounding narrative past with a generalization about the present moment.
The trap is the lexical pull of the prior past-tense sentence and any nearby
past references (`his early career`, `the 1960s movement`).

Distractors: simple past (`was`) carried over from the prior sentence, past
perfect (`had been`) that mis-treats the present claim as prior to another
past, and a nonfinite form (`being`) that leaves no finite main verb.

Classify with `syntactic_trap_key: "none"`,
`student_failure_mode_key: "tense_proximity_pull"`, and
`passage_tense_register_key: "mixed_with_explicit_shift"`.

### `verb_form`

Use the umbrella `verb_form` focus when the tested convention is finite vs.
nonfinite form, modal-governed base form, auxiliary construction, or verb form
after an opening phrase rather than tense alone. Prefer one of the documented
subpatterns below: `finite_verb_in_relative_clause`,
`finite_verb_in_main_clause`, or `modal_plus_plain_form`.

Correct option: the only verb form that can serve the required syntactic role.
Wrong options: participle, infinitive, inflected form after a modal, or a verb
form that leaves the sentence without a finite main predicate.

**Sub-pattern — Infinitive After Enable-plus-Object**

(PT11 M2 Q20: "enables cartographers like Karachi Cartography founder Namra Khalid ___ maps")

Construct a sentence with a causative verb that takes an object plus an
infinitive complement (`enables`, `allows`, `permits`, `requires`). The blank
sits after the object noun phrase and must be filled by a `to`-infinitive. The
trap is that bare infinitive, gerund (`-ing`), and past participle distractors
all look grammatically admissible in isolation, but only the full infinitive
satisfies the syntactic frame set by the governing verb.

Distractors: bare infinitive (lacks the required `to` marker), gerund/-ing form
(wrong complement type after this verb class), and past participle (implies
passive or completed action, not purpose or capability).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Infinitive Complement After Decision Verb**

(PT7 M2 Q19: "the Olympic committee once decided ___ tug-of-war as an official Olympic event!")

Construct a sentence where a decision, intention, or plan verb (`decided`,
`chose`, `planned`, `hoped`) precedes the blank and must be followed by a
`to`-infinitive complement. The trap is that bare infinitive, gerund, and past
participle distractors are all plausible surface forms that students may select
by matching tense or by assuming the complement can be any non-finite form.

Distractors: past tense (matches surrounding past-tense narrative but cannot
serve as complement), gerund/-ing form (wrong complement type after decision
verbs), and bare infinitive (missing the `to` marker that the verb class
requires).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Past Participle as Sentence-Initial Modifier**

(PT6 M1 Q19: "_______ by businessman William A.G. Brown, the saloon was known")

Construct a sentence that opens with a blank followed by `by [agent]`, requiring
a past participle that modifies the subject of the main clause in passive voice.
The correct form is a past participle (`Created`, `Founded`, `Developed`). The
trap is that present participle (`Creating`, `Founding`), present tense
(`Creates`, `Founds`), and bare infinitive (`Create`, `Found`) distractors all
seem to connect to the subject noun, but only the past participle establishes
the correct passive-modifier relationship.

Distractors: present tense active verb (agrees with subject number but violates
the participial structure), present participle (implies active ongoing action
rather than completed passive origin), and bare infinitive (cannot function as
a participial modifier without an auxiliary).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Gerund vs. Infinitive Idiomatic Selection**

[NO PT EVIDENCE — source: The Critical Reader, PrepScholar, Magoosh]

Construct a sentence in which a governing verb requires either a gerund
(`-ing`) or a `to`-infinitive complement and the blank holds that
complement form. The correct option supplies the idiomatic form; all
distractors offer the wrong non-finite form or a tense-inflected form.

Gerund-only verbs (always followed by `-ing`): `enjoy`, `avoid`, `finish`,
`consider`, `suggest`, `recommend`, `deny`, `admit`, `practice`, `risk`,
`postpone`, `keep`.
→ "enjoyed *swimming*" not "enjoyed *to swim*"

Infinitive-only verbs (always followed by `to + base`): `decide`, `choose`,
`plan`, `hope`, `want`, `agree`, `offer`, `promise`, `refuse`, `expect`.
→ "decided *to leave*" not "decided *leaving*"

Meaning-change verbs (use context to determine which form is required):
- `stop doing` (cease the action) vs. `stop to do` (pause in order to do)
- `remember doing` (recall a past action) vs. `remember to do` (not forget)
- `try doing` (experiment with) vs. `try to do` (make an attempt)

Distractors: the wrong non-finite form (gerund where infinitive is needed
or vice versa), bare infinitive lacking `to`, and past-tense inflected
form that cannot serve as a complement.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Subjunctive Mood (Hypothetical, Mandative, and Necessity Constructions)**

[NO PT EVIDENCE — source: Admit Studio, The Critical Reader, Magoosh]

Use the subjunctive when the convention is the base form of the verb (or
`were` for `be`) rather than the indicative form. Three tested environments:

**Environment 1 — Hypothetical / contrary-to-fact conditional:**
`If [subject] were [predicate]…` or `If [subject] had [past participle]…`
The blank sits in the `if`-clause. Correct: `were` (not `was`).

**Environment 2 — Mandative `that`-clause after verbs of recommendation
or requirement:**
`[Verb] that [subject] [base form]`
Trigger verbs: `recommend`, `suggest`, `require`, `demand`, `insist`,
`propose`, `urge`, `request`, `mandate`.
Correct: base form (`be`, `vote`, `exercise`) — no `-s`, no past tense.
Template: "The committee *recommended* that the funding *be* approved."

**Environment 3 — Necessity adjective in `it is … that` construction:**
`It is [adjective] that [subject] [base form]`
Trigger adjectives: `essential`, `important`, `critical`, `necessary`,
`imperative`, `vital`.
Correct: base form ("It is essential *that the data be preserved*").

Distractors for all three environments: third-person singular indicative
(adds `-s` — the most common trap), past tense form, `to`-infinitive, and
present perfect.

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `modifier_placement` / `dangling_modifier`

Start with a participial phrase whose logical subject is not the grammatical
subject.

**Sub-pattern — Possessive Noun After Introductory Participial Phrase**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence that opens with a participial phrase describing a person
("Known for her innovative choreography," "Trained in classical violin," "Born
into a family of artists"), then place the blank immediately after the comma
where the subject must appear. The correct option uses the bare noun ("the
choreographer Twyla Tharp," "the violinist Midori"), while the most plausible
distractor uses the possessive form ("the choreographer's reputation," "Midori's
performances") — an abstract noun derived from the person. The possessive creates
a dangling modifier because an abstract noun like "reputation" cannot be the one
who was "known for her choreography." The trap exploits the fact that the
possessive sounds natural in context and the student must recognize that the
modifier demands a person as its subject, not a person's attribute.

Distractors: a possessive noun whose head cannot logically perform the action in
the participial phrase, a passive construction that relegates the logical agent
to a prepositional phrase, and a pronoun ("it") with no antecedent that matches
the modifier's agent.

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "nearest_noun_reflex"`.

**Sub-pattern — Misplaced Modifier Separated From Its Head Noun**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which a restrictive modifier (an adjective phrase,
participial modifier, or relative clause) is separated from the noun it should
describe by intervening material, causing it to attach to the nearest noun
instead. Place the blank at the modifier position or at the noun-phrase
boundary. The correct option repositions the modifier next to its intended head
noun; distractors either keep the modifier in its current misplaced position or
move it to a different wrong noun. The trap is that the misplaced version often
reads fluently because the modifier's new nearest noun is a plausible (but
incorrect) target, and students must parse the sentence's logical meaning
rather than rely on surface proximity.

Distractors: the modifier placed next to the nearest (wrong) noun, the modifier
kept in its original misplaced position, and a passive rewrite that obscures the
original agent but does not fix the misattachment.

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "modifier_hitchhike"`.

**Sub-pattern — Dangling Participial Phrase With Passive-Voice Main Clause**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence that opens with a participial phrase whose implied agent is
a person or active entity, then follows the comma with a passive-voice main
clause that does not name that agent as the subject ("Having studied the
specimen for months, the results were published by the team"). The blank sits at
the beginning of the main clause where the subject must appear. The correct
option supplies the active-voice construction with the logical agent as subject
("the team published the results"); distractors preserve the passive construction
with an abstract noun or non-agent subject, or restructure without resolving the
dangling modifier. The trap is that passive voice sounds formal and plausible,
masking the logical mismatch between the participial phrase's agent and the main
clause's grammatical subject.

Distractors: the passive construction preserving the dangling modifier ("the
results were published"), an inverted paraphrase where the participial phrase's
agent appears in a prepositional phrase ("by the team") but not as the subject,
and a gerund-subject version ("studying" as subject) that creates a different
dangling reference.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `absolute_phrase`

Construct a sentence containing an absolute phrase (nominative absolute): a
noun plus a participial phrase that modifies the entire main clause, not any
specific noun within it. The absolute phrase is separated from the main
clause by a comma. The blank sits either inside the absolute phrase (verb
form) or at the clause boundary (punctuation).

An absolute phrase is structurally distinct from a dangling modifier: its
nominal head is explicit and the phrase cannot be traced back to the main
clause's subject. It modifies the event or situation expressed by the whole
clause.

Structure: `[Noun] + [participial phrase], [main clause].`

**Sub-pattern — Absolute Phrase Requiring Comma Boundary**

[NO PT EVIDENCE — source: The Critical Reader, PrepScholar]

Construct a sentence opening with an absolute phrase and place the blank
at the comma boundary between the absolute phrase and the main clause.
The correct option supplies the comma. Distractors omit the comma
(creating a run-on reading), replace it with a semicolon (elevating the
absolute to clause status), or add a relative pronoun (`which`, `that`)
that turns the absolute into a relative clause and destroys the main
clause's predicate.

Templates:
- "The experiment completed, ___ the team published their findings."
  (blank before subject; comma is the only correct option)
- "Her voice trembling slightly, the professor ___ her lecture."
  (blank at verb; finite verb is required)
- "Weather permitting, we ___ proceed with the outdoor session."
  (blank at modal; `will` is correct)

Distractors: missing comma (run-on absolute attached directly to subject),
semicolon (makes the absolute an independent clause fragment), a relative
pronoun (`which` / `that`) that converts the absolute into a non-finite
relative structure, and a coordinating conjunction that misreads the
absolute as a coordinated clause.

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "modifier_hitchhike"`.

**Sub-pattern — Absolute vs. Dangling Modifier Disambiguation**

[NO PT EVIDENCE — source: The Critical Reader]

Construct two candidate sentences — one with a correct absolute phrase
(nominal head explicit) and one with a dangling modifier (nominal head
absent or mis-matched to main-clause subject). The blank holds the nominal
head of the modifier. Only the option that supplies an explicit nominal head
produces a well-formed absolute; all other options produce dangling modifiers.

Template: "___ completed, the team published the results."
Correct: "The experiment" (full noun phrase = well-formed absolute)
Wrong: bare `-ing` participle (dangling modifier)
Wrong: possessive noun phrase ("the experiment's") — possessives cannot
serve as absolute-phrase heads

Distractors: `-ing` participle without a nominal head (classic dangling
modifier), possessive noun phrase (structurally ineligible as absolute
head), and a finite clause with a subordinating conjunction (turns the
absolute into an adverbial clause, which changes the logical relationship).

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "modifier_hitchhike"`.

Classification: `grammar_role_key: "modifier"`,
`grammar_focus_key: "absolute_phrase"`.

### `punctuation_comma`

Create a compound sentence with or without a coordinating conjunction. Test
FANBOYS comma, introductory phrase comma, or nonrestrictive element comma.

**Sub-pattern — FANBOYS Comma Joining Two Independent Clauses**

(PT1 M2 Q20: "many dinosaurs and other animals to die ___ it left unexplored")

Write two independent clauses that are topically linked (a claim and its
limitation, an outcome and a residual issue) and place the blank where the
coordinating conjunction ("but," "and," "so," "yet," "for") sits. The correct
form is `comma + FANBOYS`. The trap lives in the fact that the second clause
often opens with a pronoun referring back to the first ("it," "this," "they"),
which makes the boundary feel like internal phrasing rather than a clause
break. Reuses the v7 canonical pattern, now PT-grounded.

Distractors: the conjunction with no preceding comma (run-on), a bare comma
with no conjunction (comma splice), and a stray comma after the verb but
before the conjunction is removed entirely.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`punctuation_subpattern: "fanboys_independent_clauses"` in review_notes.

**Sub-pattern — Introductory-Clause Comma**

(PT10 M1 Q25: "light intensity affects the chemical reaction rate of ___ as")

Open the sentence with an introductory prepositional phrase, participial
phrase, or subordinate clause (`Along with X`, `With a pressure cooker pot`,
`Although the study was small`) and place the blank at the boundary where the
main clause begins. The correct form is a single comma at the boundary. The
trap is that the introductory element is often long enough (or topically
continuous with the main clause) that students perceive no audible pause and
either omit the comma (run-on) or replace it with a heavier mark (colon,
semicolon, period) that misreads the boundary as a sentence break.

Distractors: a colon or semicolon at the boundary (mis-reads it as a
list/clause break), no punctuation (run-on), and an added coordinating
conjunction that creates a redundant connector.

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "punctuation_intimidation"`. Note
`punctuation_subpattern: "introductory_clause_comma"` in review_notes.

**Sub-pattern — Nonrestrictive-Element Comma**

(PT9 M2 Q23: "repackaging successful narrative formulas as new ___ even shows")

Embed an optional element (relative clause, participial phrase, short
adverbial like `in that era`, or a closing interrupter like `assuming X`)
inside an otherwise complete sentence. The correct form sets the element off
with paired commas — opening AND closing — when it sits mid-sentence, or with
a single comma when it closes one clause before the next begins. The trap is
asymmetric punctuation: distractors supply one comma but not the other, or
substitute a stronger mark (em dash, colon, semicolon) on one side, which
breaks the bracketing rule even though each half looks locally acceptable.

Distractors: a missing leading or trailing comma around the nonrestrictive
element, an em dash or colon paired against a comma (mismatched brackets),
and a semicolon that wrongly promotes the optional element to clause status.

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`. Note
`punctuation_subpattern: "nonrestrictive_element_comma"` in review_notes.

### `semicolon_use`

Use two closely related independent clauses. Place a transitional phrase
after the semicolon zone.

**Sub-pattern — Joining Two Independent Clauses Without a Coordinator**

(PT1 M1 Q20: "soul,” ___ positing that all life's virtues derived from this absence")

Construct two fully independent clauses on the same topic and place the blank
at the boundary, with no coordinating conjunction (`and`, `but`, `so`) present
in either clause around the blank. The correct option supplies a bare
semicolon, marking the two clauses as equal-rank and closely related. The trap
exploits the tonal smoothness of the prose: because the second clause
elaborates or extends the first, students reach for a comma or a colon, both
of which leave the clauses fused or mis-typed.

Distractors: a bare comma (comma splice), a colon (mis-types the second clause
as a definition/list rather than a coordinate IC), and a period with
capitalization that severs a tight elaborative link the passage marks as
single-thought.

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`punctuation_subpattern: "semicolon_joins_two_ICs"` in review_notes.

**Sub-pattern — Super-Comma in a Complex List with Internal Commas**

(PT8 M2 Q25: "a novel about the changing roles of women in 1950s Lagos ___ A Kind of Marriage, a television play…; and Head Above Water, her autobiography")

Construct a list of three or more items where each item is a noun phrase that
already contains an internal comma (a title plus a descriptive appositive, a
city plus a year, a name plus a role). Place the blank at the boundary between
the first and second list items, with a later list item already separated by a
semicolon visible in the choice context. The correct option supplies a
semicolon, promoting the list separators above the appositive-internal commas
and preserving parallel item structure across the series. The trap is the
local two-item appearance: the immediate left neighbor looks like a simple
appositive, so a comma seems sufficient.

Distractors: a bare comma (collapses the item boundary into the internal
appositive comma, producing an ambiguous list), a colon (mis-types the
following items as a definition of the first), and an asymmetric mix
(semicolon at one item boundary, comma at another) that breaks parallel list
punctuation.

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`. Note
`punctuation_subpattern: "semicolon_super_comma_in_list"` in review_notes.

**Sub-pattern — Semicolon Before a Conjunctive Adverb Joining Two ICs**

(PT8 M2 Q26: "Jetties can sometimes have the opposite effect ___ though obstructing the natural flow of sand along the shore can lead to increased erosion")

Construct two independent clauses whose logical relation is concessive,
adversative, or consequential and where the second clause is fronted by a
conjunctive adverb (`however`, `therefore`, `consequently`, `though` used
adverbially, `nevertheless`). Place the blank immediately before that adverb.
The correct option supplies a semicolon before the adverb (and, when the
adverb is sentence-initial multi-syllable, a following comma). The trap is
that the adverb feels conjunction-like: students bracket it with paired
commas, or use a comma before it as if it were a coordinator, producing a
comma splice.

Distractors: a bare comma before the adverb (comma splice — the canonical
error), paired commas around the adverb that leave the clause break
unmarked, and a comma plus the adverb followed by a stray semicolon
(`effect, though;`) that mis-locates the clause break.

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`punctuation_subpattern: "semicolon_before_conjunctive_adverb"` in
review_notes.

### `apostrophe_use`

Use a plural possessive or a possessive pronoun that looks like a
contraction.

**Sub-pattern — Possessive Pronoun vs. Contraction Homophone (its/it's, their/they're, whose/who's)**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which a possessive pronoun and its contraction
homophone both fit the surrounding syntax if the reader skips the expansion test
(e.g., "The organism lost ___ ability to regenerate" or "___ unclear why the
experiment failed"). The blank sits at the possessive-vs-contraction boundary.
The correct option is the possessive pronoun without an apostrophe (*its*,
*their*, *whose*) when the word shows ownership, or the contraction (*it's*,
*they're*, *who's*) when it expands to "it is," "they are," or "who is." The
trap exploits the auditory overlap — students hear *its* and *it's* as
identical in speech and default to the apostrophe form because it "looks more
complete."

Distractors: the contraction form where possession is required (*it's* for
*its*), the possessive form where a contraction is required (*its* for *it's*),
and a third homophone from the set (*there* for *their/they're*, *your* for
*you're*) that introduces an additional error type.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "idiom_memory_pull"`.

**Sub-pattern — Four-Way Possessive/Plural/Contraction Distinction**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which the same base noun can appear in four
morphological forms — plain plural, singular possessive, plural possessive, or
contraction — and context narrows the choice to exactly one (e.g., "The ___
findings were published last year," where the blank must be *researchers'*). The
correct option is determined by two checks: (1) is the noun singular or plural
(use verb agreement or a quantifier to signal), and (2) does the following noun
show possession (look for a noun that "belongs to" the blanked word). The trap is
that all four options look plausible on a quick read; the student must slow
down and run both checks rather than matching sound.

Distractors: the plain plural without an apostrophe (*researchers*, when the
next noun is possessed), the singular possessive with *'s* (*researcher's*,
when the antecedent is plural), and the contraction form (*researchers're*, a
non-word that exploits the apostrophe-reflex).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Irregular Plural Possessive With *'s***

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence with an irregular plural noun (*children*, *women*, *men*,
*people*, *geese*) followed by a possessed noun (e.g., "The ___ playground was
renovated over the summer"). The blank sits at the possessive form. The correct
option adds *'s* because the plural does not end in *s* (*children's*). The trap
is that students apply the regular-plural rule — "just add an apostrophe after
the *s*" — to a noun that is plural but has no *s* to put the apostrophe after,
producing *children'* or omitting the apostrophe entirely (*children*).

Distractors: the apostrophe-only form on a noun that lacks a trailing *s*
(*children'*), the bare plural with no possessive marker (*children*), and the
singular possessive (*child's*) when the context clearly requires a plural.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `appositive_punctuation`

Use a noun phrase that renames an adjacent noun. Test comma vs no comma for
essential vs nonessential appositive.

**Sub-pattern — Title/Role Noun Before a Proper Name (Restrictive)**

(PT1 M2 Q27: "plant cell ___ showed that lipid molecules")

Construct a sentence in which a professional title, occupational label, or
role noun (`biologist`, `critic`, `mathematician`, `artist`) sits immediately
before a proper name that uniquely identifies the referent. Place the blank
at the title-and-name boundary. The correct option has no comma there because
the proper name is restrictive — it specifies which biologist/critic/etc. —
and the title-plus-name combination is a single referring expression. The
trap exploits the surface resemblance to a nonrestrictive appositive, where
commas would be required.

Distractors: a comma between the title and the name (false nonrestrictive
reading), a comma after the name (asymmetric bracketing as if name were
parenthetical), and paired commas around the name (full nonrestrictive
treatment of an essential identifier).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "title_name_comma_insertion"`.

**Sub-pattern — Restrictive Identifying Noun Phrase Without a Title**

(PT4 M2 Q22: "the isotope carbon-13 (13C) to identify chemical signatures")

Construct a sentence in which a category noun (`compound`, `isotope`,
`species`, `novel`, `term`) is immediately followed by a uniquely-identifying
expression — a technical name, a chemical formula, a title in italics, a
parenthetical abbreviation, or a coordinated descriptor. Place the blank at
the category-and-identifier boundary. The correct option has no comma there
because the identifier is restrictive: without it, the reader cannot tell
which compound/isotope/etc. is meant. The trap relies on the visual weight
of the identifier (parentheses, italics, hyphenated form) making it look
like a parenthetical insertion.

Distractors: a comma before the identifier, a comma after the identifier
(asymmetric punctuation), and paired commas wrapping the identifier as if
it were nonrestrictive.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "restrictive_appositive_comma_insertion"`.

**Sub-pattern — Nonrestrictive Appositive Set Off by Paired Commas (or Matching Dash)**

(PT4 M1 Q25: "species ___ both native and nonnative ___ contribute to the wetland")

Construct a sentence in which a noun is followed by a supplementary noun
phrase that adds information but is not required to identify the noun —
typically because the noun is already definite (proper name, definite
description, prior antecedent). Place the blank at one or both ends of that
supplementary phrase. The correct option brackets the appositive symmetrically
with paired commas (or, when the surrounding sentence already uses em dashes
for another set-off element, paired dashes that match the existing register).
The trap is asymmetric punctuation: one comma but not the other, or a comma
paired with a semicolon/dash, which breaks the bracketing rule even though
each half looks locally acceptable.

Distractors: a missing leading or trailing comma (asymmetric bracketing), a
semicolon substituted for one of the commas (mis-promotes the appositive to
clause status), and no punctuation at the boundary (run-together appositive).

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

Distractor pattern for restrictive sub-patterns:

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma before proper name after title/role | `punctuation_style_bias` |
| 2 | Commas around restrictive appositive | `grammar_fit_only` |
| 3 | Dash before restrictive appositive | `formal_register_match` |

### `relative_pronouns`

Use a clause that is either essential or nonessential. Test `that` vs
`which` or comma placement.

**Sub-pattern — Restrictive Relative Clause With "That" After a Specific Noun**

(PT4 M2 Q21: "a book packaging company that specializes in the creation and promotion of stories")

Construct a sentence in which a singular noun (`company`, `system`, `program`) is
immediately followed by a blank and then a restrictive relative clause that
defines or limits the noun. The correct option inserts `that` with no comma; the
clause is essential to identifying which noun the sentence refers to, so no
comma is permitted. The trap is that students either insert a comma before the
noun (creating a false nonrestrictive appositive), omit the relative pronoun
entirely (producing a fused clause with no connector), or add a comma before
`that` (treating a restrictive clause as nonrestrictive).

Distractors: bare noun with comma before it (creates a false nonrestrictive
boundary), bare noun without any connector (leaves the clause grammatically
unanchored), and comma-plus-"that" (illegitimately opens a nonrestrictive clause
with "that," which Standard English reserves for "which").

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "restrictive_appositive_comma_insertion"`.

**Sub-pattern — "Which" in a Nonrestrictive Clause After a Comma**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence whose main IC ends with a comma, then place the blank at
the start of a nonrestrictive relative clause that adds supplementary
information about the preceding noun. The correct option is `which`; distractors
include `that` (Standard English does not use "that" to introduce a
nonrestrictive clause after a comma), a bare participle that drops the
relative pronoun entirely, and a comma-plus-"that" combo that mis-punctuates a
restrictive construction. The key distinction is that the clause is
nonessential — removing it does not change the reference — so the comma-plus-
"which" pattern is correct.

Distractors: `that` (cannot introduce a nonrestrictive clause), bare verb form
(produces a fused or ungrammatical clause), and comma-plus-"that" (violates the
comma/that rule for nonrestrictive clauses).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "punctuation_intimidation"`.

**Sub-pattern — Omitted Relative Pronoun in Contact Clause**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence with a subject–verb gap where the relative pronoun can be
grammatically omitted because it functions as the object of the embedded clause
(e.g., "the book ___ the author published" where the pronoun is the object of
"published"). The correct option is the blank with no word inserted (the contact
clause is grammatical), but the test offers `that`, `which`, and comma-plus-
`which` as distractors. The trap is that students feel the gap "must" be filled,
even though object-relative pronouns are optional in English. Inversely, a
variant can test whether students wrongly omit a subject-relative pronoun that
*cannot* be dropped.

Distractors: `that` (grammatically fine but unnecessary), `which` (adds a
relative pronoun where none is required), and comma-plus-"which" (introduces
an incorrect nonrestrictive boundary).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `colon_dash_use`

Create a sentence where an independent clause is followed by an explanation,
list, or elaboration.

**Sub-pattern — Colon Introducing an Explanatory IC After an Independent Clause**

(PT6 M2 Q25: "goats are notoriously indiscriminate: they will devour all kinds of shrubs")

Construct a first independent clause whose final noun or adjective invites
expansion (a category label like `indiscriminate`, `notorious`, `unusual`, or
a hedged claim that demands a "because"-style follow-up), and place the blank
at the boundary just before a second IC that explains, justifies, or
illustrates the first. The correct option is a colon, which licenses the
left-to-right "promise-and-payoff" relation between two ICs without naming the
logical link. The trap is that the second IC reads as if a coordinating
conjunction or comma alone could carry the relation; students reach for the
softer mark and produce a splice.

Distractors: comma alone (canonical splice between two ICs), comma plus
coordinating conjunction (binds the clauses but redundantly *names* a relation
the colon would leave implicit), and no punctuation (fused run-on).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`.

**Sub-pattern — Colon Introducing an Elaborating Clause After a Topically Open IC**

(PT1 M1 Q24: "in the opposite direction of Earth's magnetic field when searching for food:")

Construct an IC whose final phrase ends on a topically charged noun
(`food`, `prey`, `safety`, `survival`) that leaves the reader with an
unanswered "why" or "how," then attach a second IC that supplies the answer.
Place the blank at the boundary. The correct option is a colon. The trap is
that subordinator-led distractors (`while`, `because`, `since`) feel
explanatory in their own right and bait students into treating the boundary
as a subordinate-clause attachment rather than a clause-to-clause hand-off
between two grammatically equal ICs.

Distractors: a comma (canonical splice), a subordinator like `while` or
`because` (which would demote the second clause to a fragment dependent on the
first), and no punctuation (fused boundary).

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Colon Introducing a Contrastive or Result IC**

(PT9 M1 Q24: "emerged:")

Construct an IC whose verb (`emerged`, `revealed`, `resulted`, `proved`)
projects an upshot the reader expects to be stated next, and follow it with a
second IC that delivers that upshot (often a surprising or contrastive
finding). Place the blank at the boundary. The correct option is a colon,
which performs the result/contrast hand-off with maximal economy. The trap is
that the boundary "feels" like a list-introducer or a coordination, and any of
the comma/conjunction distractors produces a punctuation error (splice, fused
run-on, or incomplete coordination).

Distractors: comma alone (splice), bare coordinating conjunction with no
comma (fused boundary), and no punctuation (run-on).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`.

### `conjunctive_adverb_usage`

Join two independent clauses with a conjunctive adverb.

**Sub-pattern — Semicolon Before / Comma After `however` Between Two ICs**

(PT4 M1 Q26: "single-handedly; however,")

Construct two independent clauses on a single topic whose relation is
adversative (`however`, `nevertheless`, `nonetheless`), and place the blank at
the boundary so that the conjunctive adverb falls *between* the two ICs. The
correct option supplies a semicolon before the adverb and a comma after it, the
canonical SAT punctuation for a mid-sentence conjunctive adverb joining equal-
rank clauses. The trap is that every distractor preserves the adverb itself,
so students who lock onto the lexical contrast cue stop attending to the
punctuation layer.

Distractors: comma plus adverb plus comma (the canonical comma splice with
adverb), comma plus adverb plus semicolon (right marks in wrong order), and
comma plus adverb with no second mark (splice masked by a trailing IC).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`.

**Sub-pattern — Colon-Confusion Variant: Conjunctive Adverb Mid-Sentence**

(PT6 M2 Q24: "competitions; however,")

Construct two ICs with an adversative or resumptive adverb (`however`,
`indeed`, `therefore`) and design the distractor set so that one wrong option
swaps in a colon either before or after the adverb. The correct option is
again semicolon-before, comma-after. The colon distractor is uniquely
seductive because the second IC reads as an elaboration of the first, tempting
students to treat the boundary as an introduction rather than a coordination
of equal-rank clauses.

Distractors: colon after the adverb (`competitions, however:` — misreads the
second IC as an introduced explanation), comma after the adverb only (canonical
splice with adverb), and semicolon after the adverb (right mark in wrong slot).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "punctuation_intimidation"`.

**Sub-pattern — Missing-Comma-After Variant: Semicolon Present but Adverb Unflanked**

(PT9 M1 Q22: "nickname; however,")

Construct two ICs with a mid-sentence conjunctive adverb where the choice set
includes a near-correct option that supplies the semicolon before the adverb
but omits the required comma after it. The correct option restores both marks.
The trap is the partial-rule reflex: students who have memorized "semicolon
before `however`" but not "comma after" treat the half-applied rule as
sufficient because the boundary "looks" repaired.

Distractors: semicolon before the adverb but no comma after (the half-rule
trap), comma plus adverb with no second mark (splice), and comma plus adverb
plus comma (full splice with parenthetical-looking adverb).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `parallel_structure`

Create a list or correlative construction where one element breaks form
symmetry.

**Sub-pattern — Correlative Conjunction Parallelism**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence with a correlative conjunction pair (both/and, either/or,
neither/nor, not only/but also, whether/or) where the blank sits in the element
following the second half of the pair. The correct answer supplies a form that
matches the grammatical structure of the element after the first half (e.g., if
the first element is a gerund phrase, the second must also be a gerund phrase).
The trap is that mismatched forms ("not only singing but also to dance") sound
plausible in casual reading because the conjunction pair itself signals a
connection, masking the structural asymmetry.

Distractors: a non-parallel form that shifts part of speech or clause type across
the pair (gerund after first half, infinitive after second), a form that matches
the sentence's overall tense but not the parallel slot, and a form that adds an
unnecessary subject pronoun, breaking the shared-subject structure.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "parallel_shape_bias"`.

**Sub-pattern — Mid-List Form Shift**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence with a three-item list (connected by commas and a final
"and") where the first two items share one grammatical form and the third breaks
the pattern (e.g., "supervising staff, managing budgets, and to report to senior
management"). The blank sits at the third item. The correct answer supplies a
form matching the first two items. The trap is that the first two items lull the
reader into a rhythm and the break comes at the end, where attention has already
drifted; the non-parallel form sounds acceptable because it conveys the right
meaning even though it violates parallel structure.

Distractors: the non-parallel form that matches surface meaning but breaks
parallelism (infinitive after two gerunds, noun phrase after two verb phrases,
adjective after two adverbs), a form that partially matches by sharing one
feature (same tense but different voice, or same part of speech but different
number), and a form that introduces a new subject, turning the third item into
an independent clause.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "parallel_shape_bias"`.

**Sub-pattern — Comparison Parallelism Across As or Than**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which two elements are compared with "as…as" or
"more…than" and the blank sits on one side of the comparison. The correct answer
supplies a form that is grammatically parallel to the element on the other side
(e.g., "better to read than to watch" rather than "better to read than watching").
The trap is that the comparative construction makes the two halves feel
connected, and shifting form (infinitive to gerund, noun phrase to clause) does
not break the sentence's surface sense — it only breaks the structural
parallelism.

Distractors: a non-parallel form that shifts part of speech or clause type across
the comparison boundary, a form that substitutes a pronoun or demonstrative for
the parallel structure ("that" or "those" without the needed preposition), and a
form that adds unnecessary words that obscure the parallel relationship.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "parallel_shape_bias"`.

### `pronoun_case`

Use a compound subject or object where pronoun case is tested.

**Sub-pattern — Possessive Pronoun vs. Homophonous Contraction**

(PT1 M1 Q21: "Watson and Crick... _______ findings were based on a famous X-ray image")

Construct a sentence where a blank before a noun requires a possessive determiner,
and distractors include the homophonous contraction (`their` vs `they're`, `its`
vs `it's`, `whose` vs `who's`). The correct option is always the possessive
pronoun without an apostrophe. The trap is that the contraction form sounds
identical in speech and carries an apostrophe that students overgeneralize as a
possessive marker.

Distractors: the homophonous contraction (`they're`, `it's`, `who's`) which
expands to a subject-verb pair that cannot modify a noun, a singular possessive
pronoun (`its`) that fails number agreement with a plural antecedent, and a
singular possessive contraction (`it's`) that fails on both number and
part-of-speech grounds.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Pronoun Case in Compound Subject or Object**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence with a compound subject (`___ and I`) or compound object
(`between ___ and me`) where the blank holds a pronoun that must match the case
governed by the verb or preposition. The correct answer is the subjective-case
pronoun (`I`, `he`, `she`, `they`) in a compound subject or the objective-case
pronoun (`me`, `him`, `her`, `them`) in a compound object. The trap is that the
subjective case sounds formal and is overgeneralized to object positions
("between you and I"), while the objective case sounds informal and is
overgeneralized to subject positions ("me and Dave walked home").

Distractors: objective-case pronoun in a subject position (`Dave and me walked
home`), subjective-case pronoun in an object position (`invited Sandhya and I`),
and a reflexive pronoun that cannot serve the syntactic role (`myself and Dave`).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Who vs. Whom in Object Position**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where a relative clause or question requires `whom`
(objective case) as the object of a verb or preposition, but the subject-case
`who` is offered as a distractor. The correct answer is `whom`; the trap is that
`who` sounds natural as a clause-initial word, and students rarely apply the
substitution test (`he` → `who`, `him` → `whom`).

Distractors: `who` (subjective case, incorrectly used for object position),
`whose` (possessive form, wrong case entirely), and `whomever` (overgeneralized
objective form used where the pronoun is the subject of its own clause).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

### `pronoun_clarity`

Create a sentence with multiple possible antecedents for a pronoun.

**Sub-pattern — Vague Demonstrative "This/That" Without Noun Follow-Up**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which a demonstrative pronoun ("this," "that," "these,"
"those") stands alone and refers to an entire preceding clause, idea, or situation
rather than to a single specific noun. The blank sits at the demonstrative
position (e.g., "The economy recovered quickly, and ______ surprised many
analysts"). The correct answer replaces the bare demonstrative with a
demonstrative-plus-noun phrase ("this recovery") or a specific noun phrase ("the
recovery"). The trap is that bare "this" or "that" feels natural in speech and
students accept it as grammatically sufficient, but on the DSAT a lone
demonstrative that refers to a whole clause rather than a single noun is flagged
as vague.

Distractors: bare "this" with no noun follow-up (sounds natural in speech but
leaves the antecedent vague), "which" treated as a relative pronoun referring to
the entire clause (creates a comma splice or non-restrictive clause that mis-attaches),
and "it" whose antecedent is the entire preceding idea rather than a single noun
(generic pronoun with no specific referent).

Classify with `syntactic_trap_key: "pronoun_ambiguity"` and
`student_failure_mode_key: "pronoun_anchor_error"`.

**Sub-pattern — Dual-Gender or Same-Gender Antecedent Ambiguity**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence containing two same-gender nouns (two women, two men, two
plural groups) followed by a pronoun that could grammatically refer to either
(e.g., "When Nel and Katie got back from the movie, they took her dog for a walk"
— "her" could be Nel's or Katie's). The blank sits at the ambiguous pronoun.
The correct answer replaces the pronoun with the specific noun that resolves the
ambiguity. The trap is that both antecedents are equally plausible
syntactically, so the pronoun appears to "work" even though no reader can
determine which noun it modifies.

Distractors: the ambiguous pronoun that matches both antecedents in number and
gender (grammatically consistent but referentially unclear), a pronoun that
matches the nearer antecedent only (nearest-noun reflex), and a reflexive pronoun
("herself") that falsely appears more precise but still leaves the referent
ambiguous.

Classify with `syntactic_trap_key: "pronoun_ambiguity"` and
`student_failure_mode_key: "pronoun_anchor_error"`.

**Sub-pattern — Remote or Implied Antecedent**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which the pronoun's antecedent is separated by two or more
intervening clauses, or the antecedent is an entire clause or event that is never
named by a single noun (e.g., "The committee voted to delay the project, which
frustrated the engineers" — "which" refers to the delay-event, not "project").
The blank sits at the pronoun position. The correct answer supplies a concrete
noun phrase that names the event or idea the pronoun was meant to capture. The
trap is that the sentence reads fluently on first pass because the reader infers
the antecedent from context, but the pronoun has no explicit single-noun referent
in the sentence.

Distractors: a relative "which" that attaches to the nearest noun rather than the
whole-clause idea (grammatically valid but semantically wrong), a pronoun that
agrees in number with a nearer but incorrect noun (nearest-noun reflex), and a
restructured version that preserves the vague pronoun in a different position
(the ambiguity survives the rewrite).

Classify with `syntactic_trap_key: "pronoun_ambiguity"` and
`student_failure_mode_key: "underreading"`.

### `possessive_contraction`

Use a context where `it's` vs `its` or `who's` vs `whose` is tested.

**Sub-pattern — Plural Possessive with Irregular Plural Noun**

(PT4 M1 Q19: "professional authors who are paid to write other _______ but whose names")

Construct a sentence where a plural noun that does not end in `s` (`people`,
`children`, `women`, `men`) must take a possessive apostrophe-`s` to modify a
following noun. The correct form is the irregular-plural possessive (`people's`,
`children's`). The trap is distractors offer the base plural without apostrophe
(`peoples stories`), a regular-plural possessive form that treats the irregular
noun as if it ends in `s` (`peoples'`), or a double possessive that marks both
the owner and the possessed noun (`people's story's`).

Distractors: base plural without possessive apostrophe (omits ownership
entirely), regular-plural possessive that misapplies the `s'` pattern to an
irregular noun, and double possessive that apostrophizes both the owner noun and
the possessed noun.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Plural Noun Misidentified as Possessive**

(PT5 M1 Q23: "When you place your _______ the pitch will shift as your hands move through the air")

Construct a sentence where a plural noun serves as the object of a verb or
preposition and no possessive relationship exists, but distractors add
apostrophes that turn the plural into a possessive form. The correct option is
the bare plural with no apostrophe (`hands`, `antennas`). The trap is that
students overgeneralize the apostrophe rule and insert possessive markers on
nouns that are merely plural, not possessive.

Distractors: singular possessive with apostrophe-`s` (`hand's`), plural
possessive with apostrophe after `s` (`hands'`), and double possessive marking
both nouns (`hands' ... antennas'`).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Possessive Pronoun vs. Contraction Homophone**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence where a blank before a noun requires a possessive pronoun
(`its`, `their`, `your`, `whose`) and the most plausible distractor is the
homophonous contraction (`it's` = it is, `they're` = they are, `you're` = you
are, `who's` = who is). The correct option is always the possessive form without
an apostrophe. The trap is that the apostrophe in the contraction mimics the
apostrophe students associate with noun possessives, and the two forms sound
identical in speech.

Distractors: the contraction form that expands to a subject-verb pair but cannot
modify a noun (`it's`, `they're`), a singular possessive pronoun that fails
number agreement with a plural antecedent (`its` for a plural referent), and a
demonstrative or article form that cannot serve a possessive function (`that`,
`the`).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

### `hyphen_usage`

Use a compound modifier before a noun where hyphenation is required.

**Sub-pattern — Compound Adjective in Predicative Position (Hyphen Must Be Removed)**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which a compound adjective appears after a linking verb
in predicative position (e.g., "The results of the study were well ___ known" or
"The performance was first ___ rate"). The blank sits at the hyphen boundary
within the compound modifier. The correct option has no hyphen because compound
adjectives are hyphenated only before the noun they modify; after a linking verb,
the modifier is predicative and the hyphen is removed. The trap exploits
positional inertia — students see *well-known* hyphenated elsewhere and assume
the hyphen is permanent regardless of position.

Distractors: the hyphenated form in predicative position (*well-known* after a
linking verb), the unhyphenated form in attributive position (*well known
scientist* before the noun), and a fused compound (*wellknown*) that does not
exist in standard English.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

**Sub-pattern — *-ly* Adverb in a Compound Modifier (Hyphen Must Not Appear)**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which an *-ly* adverb modifies a following adjective
before a noun (e.g., "a ___ changing landscape" or "the ___ researched report").
The blank sits at the hyphen boundary. The correct option has no hyphen because
adverbs ending in *-ly* already unambiguously modify the next word, making the
hyphen redundant and incorrect (*rapidly changing*, not *rapidly-changing*). The
trap is that students generalize the "hyphenate compound modifiers" rule without
the *-ly* exception and insert a hyphen where it is grammatically forbidden.

Distractors: the hyphenated *-ly* compound (*rapidly-changing*), an
unhyphenated non-*-ly* compound (*well known scientist* before the noun — wrong
because *well* is not an *-ly* adverb and does need a hyphen in attributive
position), and a comma inserted between adverb and adjective (*rapidly, changing*
landscape), which breaks the compound entirely.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Suspended Hyphen in a Coordinated Compound Series**

[NO PT EVIDENCE — source: Albert.io]

Construct a sentence in which two compound adjectives share a base element and
must be coordinated with a suspended hyphen (e.g., "first- and ___ class
passengers" or "long- and ___ term effects"). The blank sits at the hyphen in
the second compound. The correct option repeats the hyphen before the shared
base (*first- and second-class*), or, in a more advanced variant, omits the
second hyphen when the base is already stated (*first- and second-class
passengers*). The trap is that students either drop both hyphens (*first and
second class*) or hyphenate both compounds fully without suspending (*first-class
and second-class*), failing to recognize the suspended-hyphen convention.

Distractors: no hyphens at all (*first and second class* before the noun), full
hyphenation without suspension (*first-class and second-class* — redundant but
not wrong, though it fails to match the suspended form tested), and a hyphen
only on the first compound without the coordinating hyphen on the second
(*first- and second class* — missing the suspended hyphen on *second-*).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `logical_predication`

Create a sentence where the subject and predicate are grammatically possible
but logically incompatible.

### `comparative_structures`

Create a comparison where the things being compared are not grammatically
parallel.

**Sub-pattern — Possessive-vs-Bare Noun Mismatch in Comparisons**

[NO PT EVIDENCE — source: PrepScholar]

Construct a comparison sentence in which one compared element is introduced with
a possessive noun ("Anya's cooking," "Jimmy's restaurant," "the novels of Jane
Austen") and the second element is a bare proper noun or common noun without the
corresponding possessive marker ("Nia," "Bob," "Charlotte Bronte"). The blank
sits at or near the second compared element. The correct option inserts the
possessive apostrophe ("Nia's"), adds the demonstrative pronoun ("those of
Charlotte Bronte"), or supplies a helper verb ("Bob does"); distractors preserve
the bare noun, producing an illogical comparison between a possessive attribute
and a person. The trap is that in casual speech "Jimmy's restaurant has more
customers than Bob" sounds natural, but it illogically compares "customers" to a
person rather than to "Bob's customers."

Distractors: the bare proper noun without possessive or demonstrative (compares
attribute to person), a helper verb attached to the wrong element ("those of"
with a singular antecedent), and a restructured sentence that fixes the
possessive mismatch but introduces a new grammatical error.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "illogical_comparison_blindness"`.

**Sub-pattern — Missing Demonstrative Pronoun ("that of" / "those of")**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a comparison sentence in which the first element names an attribute of
a person, place, or thing ("the size of Alaska," "the revenue of the company,"
"the speed of a cheetah") and the second element names the person, place, or
thing itself ("Texas," "its rival," "any land mammal"). The blank sits at the
point where the demonstrative pronoun must be inserted. The correct option
inserts "that of" (singular) or "those of" (plural) before the second compared
element; distractors omit the demonstrative pronoun entirely, insert the wrong
number ("that of" for a plural antecedent or "those of" for a singular
antecedent), or restructure in a way that preserves the category mismatch. The
trap exploits the fact that the sentence reads fluently without the demonstrative
pronoun, and students must recognize that "the size of Alaska is twice Texas"
illogically compares a size to a state.

Distractors: omission of the demonstrative pronoun (bare comparison of attribute
to entity), the singular "that of" where a plural "those of" is required (or
vice versa), and a restructuring that paraphrases the comparison but keeps the
two compared elements in different logical categories.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "illogical_comparison_blindness"`.

**Sub-pattern — Individual-vs-Category Comparison Without "Other"**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence that compares an individual member to the category that
includes it, omitting "other" or "else" ("A cheetah is faster than any land
mammal," "Shakespeare has sold more books than anyone"). The blank sits at the
comparison word or immediately after the compared element. The correct option
inserts "other" before the category noun or "else" after an indefinite pronoun;
distractors omit the qualifier (creating a logical impossibility — a cheetah
cannot be faster than itself), replace "other" with a comparative intensifier,
or restructure in a way that still omits the exclusion. The trap is that "faster
than any land mammal" sounds emphatic and natural but is logically incoherent
because the cheetah itself is a land mammal.

Distractors: the bare category noun without "other" (the cheetah is compared
against a group it belongs to), "any one" or "every" as a pseudo-qualifier that
does not exclude the individual, and a restructured comparison that changes the
word order but retains the logical error.

Classify with `syntactic_trap_key: "scope_of_negation"` and
`student_failure_mode_key: "overreading"`.

### `unnecessary_internal_punctuation`

Insert a comma or dash at one of these five positions:

1. between subject and main verb
2. between transitive verb and its direct object
3. between verb and subject complement
4. between preposition and its noun complement
5. inside an integrated relative clause before the verb

Correct option: no punctuation at the target boundary.
Wrong options: comma, dash, or colon at the forbidden location.

**Sub-pattern — Punctuation Between Subject and Verb**

(PT8 M2 Q23: "the porous rocks of the hills around Hot Springs ___ collect")

Construct a sentence in which a long or topically heavy subject (a noun head
trailed by prepositional phrases, a participial modifier, or an embedded
identifier) sits immediately before the main verb, and place the blank at the
subject–verb boundary. The correct option has no punctuation there because
nothing separates a subject from its verb in Standard English, even when the
subject is lengthy enough that a reader feels a pause. The trap relies on the
illusion that a long subject "earns" a comma the way a long introductory
phrase does.

Distractors: a comma at the boundary, a dash at the boundary, and a colon at
the boundary — each presenting a different "rhythmic" rationale (pause,
emphasis, list-style introduction) for inserting a mark where none is allowed.

Classify with `syntactic_trap_key: "interruption_breaks_subject_verb"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

**Sub-pattern — Punctuation Between Verb and Its Complement or Object**

(PT11 M2 Q21: "the part of a compound that determines the compound's color is called ___ the chromophore")

Construct a sentence in which a linking verb plus its subject complement, or a
transitive verb plus its direct object, forms a single required syntactic
unit; place the blank between the verb and the complement/object. The correct
option has no punctuation at that boundary because verb-and-complement (or
verb-and-object) is an integrated unit. The trap exploits the temptation to
"introduce" the complement with a comma, dash, or colon, treating the
complement as if it were a parenthetical definition or list item.

Distractors: a comma before the complement (most natural-sounding distractor),
a dash before the complement (emphasis play), and a colon before the
complement (mis-reads the boundary as an explanatory list).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

**Sub-pattern — Punctuation Inside a Noun Phrase (Title/Role + Name or Modifier + Noun)**

(PT7 M2 Q21: "Her portrait of novelist Zadie ___ is displayed")

Construct a noun phrase in which a common-noun premodifier (a professional
title, role label, category word, or descriptive modifier) sits immediately
before its restrictive identifier — typically a proper name, a specific
technical term, or another uniquely-identifying noun. Place the blank inside
that noun phrase. The correct option has no punctuation inside the noun phrase
because the modifier and the identifier together form one referring
expression. The trap relies on students misreading the identifier as a
nonrestrictive appositive that "deserves" commas, when in fact the identifier
is restrictive and the noun phrase is one unit.

Distractors: a comma between the modifier and the identifier (false
nonrestrictive reading), a dash at the same boundary (emphasis play), and a
colon at the same boundary (mis-reads the identifier as an explanatory item).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "restrictive_appositive_comma_insertion"`.

### `end_punctuation_question_statement`

Construct a sentence whose end punctuation must be chosen on the basis of
sentence type — declarative versus interrogative — even though a WH-word
(`how`, `why`, `which`, `what`) appears inside the clause. The blank is the
end of the sentence; the correct option pairs the right punctuation with the
right (declarative) word order.

**Sub-pattern — Indirect Question After Verb of Cognition**

(PT6 M1 Q22: "Researchers Amit Kumar and Nicholas Epley investigated how ___")

Open with a verb of cognition or inquiry (`investigated`, `wondered`,
`considered`, `examined`, `asked`) that takes a WH-headed complement
(`how X happens`, `why X matters`, `which X applies`). The blank closes the
sentence inside that embedded clause. Because the matrix sentence is
declarative, the embedded clause must keep normal subject–verb order
(`people perceive`, not `do people perceive`) and end in a period. The trap is
the WH-word at the head of the embedded clause, which superficially mimics a
direct question.

Distractors: a question mark with subject-auxiliary inversion (full direct-
question form), a question mark with declarative word order (correct order,
wrong mark), and subject-auxiliary inversion with a period (wrong order, right
mark).

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "declarative_question_confusion"`.

**Sub-pattern — Embedded WH-Clause Inside a Gerund or Participial Phrase**

(PT11 M1 Q19: "scanning a search results page and evaluating what you see before deciding which link ___")

Build a sentence whose blank closes an embedded WH-clause that is itself the
object of a gerund or participle (`deciding which link you should choose`,
`predicting how the system will respond`). The full matrix sentence is
declarative — typically a definition or generalization (`Click restraint is
the practice of …`) — so the sentence must end with a period, and the
embedded clause must keep declarative word order. The trap is the deeply
embedded WH-word plus a modal (`should`, `will`, `can`) that primes the
reader for a direct question.

Distractors: subject-auxiliary inversion with a period (right mark, wrong
order), declarative word order with a question mark (right order, wrong mark),
and subject-auxiliary inversion with a question mark (both wrong).

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "declarative_question_confusion"`.

**Sub-pattern — "Which Is Why" Declarative Despite WH-Marker**

(PT11 M2 Q19: "The clashing notes can echo a long way across the mountains, which is why ___")

Construct a sentence whose final clause is a non-restrictive `which is why`
(or `which is how`, `which is when`) tail attached to a declarative main
clause. The blank closes the `which is why` clause with a full predicate
(`ganga has been used as a communication method`). Because `which is why` is a
relative-clause connector — not a question stem — the whole sentence remains
declarative and must end in a period, with normal subject–verb order in the
tail. The trap is the WH-word `why` sitting visibly at the front of the tail
clause.

Distractors: declarative order with a question mark (right order, wrong mark),
subject-auxiliary inversion with a period (wrong order, right mark), and
inversion with a question mark (both wrong, full direct-question form).

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "declarative_question_confusion"`.

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

**Sub-pattern — Period Between Two Fully Independent Clauses**

(PT8 M2 Q21: "plastic-bag consumption decreased by up to ninety ___ taxes are subject to what economists call the 'rebound effect'")

Build two independent clauses on a shared topic where the second clause begins
with a noun phrase that could be misread as a continuation of the first
(`Geological structures…`, `Taxes are subject to…`, `These results
suggest…`). Place the blank at the boundary. The correct option supplies a
period (and capitalization on the second clause) — or, where the choice set
allows, a semicolon. The trap is topical continuity: because both clauses
elaborate the same idea, a comma or no punctuation feels like internal
phrasing rather than a clause break.

Distractors: a bare comma (comma splice), no punctuation (fused/run-on), and a
comma plus a conjunctive adverb (`however,` `therefore,`) without the required
heavier mark before it.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`boundary_subpattern: "period_between_independent_clauses"` in review_notes.

**Sub-pattern — Subordinating Conjunction Repairs a Fused Boundary**

(PT6 M1 Q25: "A ray diagram reveals how this ___ the hole's small size restricts light to a single ray")

Construct two clauses whose logical relation is causal, concessive, or
temporal (`because`, `although`, `while`, `since`, `when`) and place the blank
at the boundary so that the correct answer is the subordinating conjunction
that demotes one clause to a dependent role, resolving the fused boundary in
one move. The trap is that punctuation-only options (comma, semicolon, em
dash) all look "clean" but leave both clauses independent and either splice
them or stack them without showing the logical relation the passage requires.

Distractors: a comma alone (comma splice that also drops the logical
relation), a semicolon (joins as equals but ignores subordination cue), and a
coordinating conjunction (`and`, `but`) that flattens the causal/concessive
relation to mere addition or contrast.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "punctuation_intimidation"`. Note
`boundary_subpattern: "subordinator_resolves_fused_clauses"` in review_notes.

**Sub-pattern — Declarative vs. Interrogative Boundary**

(PT1 M2 Q22: "_______ Michel was determined to find out")

Set up a passage that poses or implies a question (`Michel wondered ___`,
`The team set out to ask ___`, `What are X, and how ___`) and place the blank
at the boundary between an embedded interrogative and a following declarative
frame. The correct option keeps the embedded question in declarative
word order (no subject-aux inversion, no question mark) because it is
syntactically a noun-clause complement, not a direct question. The trap is the
question-word lexical cue (`how`, `whether`, `what`), which pulls students
toward inverted order and a terminal question mark.

Distractors: subject-auxiliary inversion (`how do these plants grow?`) that
turns an embedded clause into a direct question, a terminal question mark on
what should be a declarative period, and a comma that leaves the embedded
clause dangling without a finite boundary.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "declarative_question_confusion"`. Note
`boundary_subpattern: "embedded_interrogative_declarative_frame"` in
review_notes.

### `sentence_fragment`

Subordinate clause presented as a complete sentence.

**Sub-pattern — Blank Must Supply a Finite IC Before a Trailing Participial Phrase**

(PT1 M1 Q28: "Upon recovering two years later, ___ forcing an angered Richard from the royal court")

Construct an introductory subordinator-led phrase (`Upon …`, `After …`,
`Despite …`) followed by a blank and then a trailing participial modifier
(`forcing …`, `marking …`, `driving …`). The correct option is a full IC
(subject + finite verb) that the participial phrase can attach to. The trap is
distractor options recast the same content as noun phrases (`the reign of
Henry resumed,`) or cleft constructions (`it was Henry who resumed his
reign,`) that lack a finite predicate at the surface boundary, leaving the
trailing participial dangling on a fragment.

Distractors: noun phrase masquerading as a clause (lacks finite verb), passive
or cleft restructuring that hides the absence of a finite predicate, and an
expletive-fronted clause whose finite verb is too distant to anchor the
participial.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Blank Must Supply a Complete IC Before a Colon-Introduced List**

(PT1 M2 Q26: "commercial plastics have two associated problems:")

Construct a sentence whose post-blank material begins with a colon and a list
or explanation, requiring the pre-colon material to be a stand-alone IC (the
canonical SAT colon rule). The correct option is a full IC ending on a count
noun or category label that the colon-list expands. The trap is distractor
options provide pseudo-clauses (existential `there are …`, possessive-fronted
`commercial plastics' two associated problems are that`, or passive
restructurings) that either lack a finite predicate or end in a complementizer
that cannot license a colon.

Distractors: existential `there are X` followed by a colon (creates an awkward
or fragmentary frame for the list), passive or possessive-fronted noun phrase
that fails to close an IC, and a `that`-complement form that demands a
following clause rather than a list.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Blank Must Supply a Noun-Phrase Subject for a Downstream Finite Verb**

(PT4 M1 Q24: "Julian's 1935 synthesis of the alkaloid physostigmine")

Construct a sentence whose post-blank material continues with a finite verb
(`led to …`, `inspired …`, `produced …`) that demands a single noun-phrase
subject. The correct option is a noun phrase (often a nominalization:
`Julian's 1935 synthesis of …`) that feeds the downstream verb cleanly. The
trap is distractor options provide complete ICs (`Julian synthesized the
alkaloid physostigmine in 1935; it`, `the alkaloid physostigmine was
synthesized by Julian in 1935 and`) that, when combined with the downstream
verb, produce either a fragment (no subject for the downstream verb) or a
run-on (two ICs fused at the boundary).

Distractors: full IC ending in semicolon-plus-pronoun (creates a run-on with
the downstream verb), full IC ending in `and` (parallel-coordination
distractor that strands the downstream verb without a subject), and full IC
ending in `which` (relative-clause distractor that breaks the downstream
predicate's subject requirement).

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `comma_splice`

Two independent clauses joined with only a comma.

**Sub-pattern — Comma plus Coordinating Conjunction Repairs the Splice**

(PT7 M1 Q22: "Leibniz wheel calculators were popular in the first half of the twentieth century ___ these ingenious devices were eventually replaced by electronic calculators")

Construct two independent clauses on a single topic whose relation is
adversative or additive (`but`, `and`, `so`, `yet`) and place the blank at the
boundary. The correct option supplies a comma followed by a coordinating
conjunction (FANBOYS), the canonical SAT fix that both binds the clauses and
names their logical relation in one move. The trap is the topical fluency of
the prose: students leave a bare comma (the canonical splice) or, equally
seductively, drop punctuation entirely on the assumption that a conjunction
alone licenses the join.

Distractors: a bare comma (the canonical splice), no punctuation (fused/run-on
sentence), and a bare coordinating conjunction with no comma (still a fused
boundary, since the comma is required before FANBOYS joining two ICs).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`comma_splice_subpattern: "comma_plus_FANBOYS_repair"` in review_notes.

**Sub-pattern — Semicolon Upgrade Repairs the Splice (No Conjunction Available)**

(PT4 M1 Q23: "Watt sewed strips of blankets together to craft a 10-by-13-inch sampler ___ in 2014, she arranged folded blankets into two large stacks")

Construct two independent clauses linked by parallel temporal or structural
markers (`in 2004 … in 2014`, `first … later`, `on one side … on the other`)
where no coordinating conjunction is present in the choice set. Place the
blank at the boundary. The correct option supplies a semicolon, the
conjunction-free repair for two equal-rank ICs. The trap is that the parallel
time/structure cue feels like internal phrasing rather than a clause break, so
students try a comma alone or a comma plus a redundant adverbial.

Distractors: a bare comma (canonical splice), a comma plus a stray adverbial
that does not change the boundary status (`sampler, later,`), and a comma
relocated to the wrong side of the parallel marker.

Classify with `syntactic_trap_key: "early_clause_anchor"` and
`student_failure_mode_key: "comma_fix_illusion"`. Note
`comma_splice_subpattern: "semicolon_upgrade_no_conjunction"` in review_notes.

**Sub-pattern — Demote One IC to a Participial/Non-Finite Modifier**

(PT9 M1 Q25: "This hypothesis ___ that certain trees, such as P. sylvestris, survived with little visible pollen output")

Construct a sentence whose subject is followed by a finite-verb slot and then
a `that`-clause complement (`This hypothesis ___ that …`, `These results
___ that …`, `The proposal ___ that …`). The choice set offers competing
verb forms, including finite tenses (`suggested`, `suggests`, `has suggested`)
and a participial form (`suggesting`). The correct option is the
participial/non-finite form, which demotes what would otherwise be a second
finite predicate to a modifying phrase attached to the subject noun — leaving
exactly one main clause and dissolving the splice at the verb-form layer
rather than the punctuation layer. The trap is that every finite option reads
locally as a verb the sentence needs, so students never recognize that a
finite choice would create two ICs separated only by an upstream comma.

Distractors: any finite tense (`suggests`, `suggested`, `has suggested`) that
turns the noun phrase into a second independent clause, producing a splice
with the preceding comma; subject-verb-agreement variants among the finite
options absorb the secondary error budget.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`. Note
`comma_splice_subpattern: "non_finite_verb_demotion_repair"` in review_notes.

### `run_on_sentence`

Two independent clauses fused with no punctuation or conjunction.

**Sub-pattern — Fused Boundary Repaired by Period (Sentence Break)**

(PT1 M2 Q24: "adjustments. Prior")

Construct two independent clauses that share topical continuity (a definition
plus an upstream-time contrast, a claim plus a justification) so that a
careless reader hears them as one breath, and place the blank at the boundary.
The correct option is a period (full sentence break), which is the only legal
repair when no coordinating conjunction is available and a semicolon is not in
the choice set. The trap is the smooth topical flow: students leave the
boundary unpunctuated (`adjustments prior`), drop in a bare comma, or insert a
coordinator (`adjustments and prior`) that fails to bind two ICs.

Distractors: no punctuation at all (the canonical fused run-on), comma alone
(canonical comma splice), and bare coordinating conjunction with no comma
(still a fused boundary, since `and` alone cannot join two ICs).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "comma_fix_illusion"`.

**Sub-pattern — Coordinating Conjunction Without Required Comma Between Two ICs**

[NO PT EVIDENCE — source: The Critical Reader]

Construct two independent clauses whose logical relation invites a FANBOYS
coordinator (`and`, `but`, `so`, `yet`) and design the choice set so that one
distractor supplies the conjunction but omits the comma required before it.
The correct option restores the comma-plus-conjunction pair. The trap is the
half-rule reflex: students remember that FANBOYS can join two ICs but forget
that the comma is mandatory when both flanks are independent, so a bare
coordinator looks "almost right" and the sentence reads as a run-on.

Distractors: bare coordinator with no comma (fused run-on disguised by the
conjunction), comma without coordinator (canonical splice), and conjunctive
adverb without semicolon (different rule misapplied to the same boundary).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Long Compound-Complex Sentence Missing a Legal IC Boundary**

[NO PT EVIDENCE — source: Khan Academy SAT R&W course]

Construct a sentence whose first stretch reads as a polished subordinate-plus-
main clause unit, then continues into a second independent clause without any
period, semicolon, colon, or comma-plus-FANBOYS at the IC boundary. Place the
blank at the second-IC boundary. The correct option supplies a legal boundary
mark (period or semicolon). The trap is rhetorical polish: the sentence
*sounds* fluent because subordinators, parallel phrases, and verb-tense
consistency mask the missing boundary, so students accept the bare or
comma-only join as legitimate.

Distractors: bare comma (splice), no punctuation (fused run-on), and a
relative-pronoun substitution (`which`, `that`) that would demote the second
IC to a fragment while still leaving a punctuation error.

Classify with `syntactic_trap_key: "long_distance_dependency"` and
`student_failure_mode_key: "surface_similarity_bias"`.

### `noun_countability`

Mass noun with plural article or vice versa.

**Sub-pattern — Fewer/Less and Number/Amount Quantifier Mismatch**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which a quantifier must be chosen that matches the
countability class of the head noun: a countable plural noun requires "fewer,"
"many," or "a number of," while an uncountable (mass) noun requires "less,"
"much," or "an amount of." The blank sits at the quantifier position. The trap
is that the sentence places a nearby noun of the opposite countability class in
a prepositional modifier, pulling students toward the wrong quantifier. Common
mass-noun traps include *information, equipment, research, advice, furniture,
knowledge, progress,* and *data* (treated as singular mass in Standard English).

Distractors: "less" before a countable plural (sounds natural in casual speech
but is ungrammatical in formal writing), "many" before a mass noun (students
overgeneralize from nearby countable nouns), and "amount of" before a countable
plural (students confuse the number/amount distinction).

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Plural Inflection on a Mass Noun**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence whose head noun is a mass noun that students frequently
mistake for a countable noun (*informations, equipments, researches, advices,
furnitures*). The blank is at the noun itself or at the verb that must agree
with it. If the noun position is blanked, the distractors include the
pluralized form of the mass noun; if the verb position is blanked, the
distractors include a plural verb triggered by treating the mass noun as
plural. The core trap is that many English mass nouns have countable cognates
in other languages, and students carry over the plural morphology.

Distractors: plural form of the mass noun (e.g., "informations"), singular
indefinite article before a mass noun ("an advice"), and a plural verb after a
mass subject ("The research show..." instead of "shows").

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Collective or "-s-Ending" Noun Takes a Singular Verb**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence whose subject is a collective noun (*committee, team,
group, audience, family*) or an "-s"-ending noun that is semantically singular
(*news, mathematics, physics, economics, gymnastics, measles*). The blank is
the verb position. The trap is twofold: the collective noun feels plural
because it denotes multiple members, and the "-s" ending on academic-discipline
nouns looks like a plural inflection. In Standard American English, these nouns
take a singular verb. Distractors exploit both misperceptions.

Distractors: plural verb after a collective noun (agrees with the implied
members, not the grammatical unit), plural verb after an "-s"-ending singular
noun (the suffix mimics a plural marker), and a quantifier that assumes the
noun is countable ("many news" instead of "much news").

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `determiners_articles`

Article where none is needed, or omitted required article.

**Sub-pattern — Definite Article Before a First-Mentioned or Generic Noun**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence that introduces a noun for the first time in the discourse
or uses it in a generic sense (e.g., "The researchers studied ___ effect of
sleep on memory"). The blank sits at the determiner position before the noun.
The correct answer is either the indefinite article "an" (first mention of a
singular countable noun) or no article (generic plural or mass noun). The trap
is that students over-apply "the" because the noun is important or specific in
context, but specificity in meaning is not the same as uniqueness in the
discourse — the definite article requires prior mention, a superlative, or an
ordinally identified referent.

Distractors: "the" before a first-mentioned singular count noun (sounds
specific but violates the given-new principle), no article before a singular
count noun (students confuse generic and specific omission), and "a" before an
uncountable noun (students default to an article whenever a noun follows).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Missing Indefinite Article Before a Singular Count Noun**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which a singular count noun in subject or object
position is preceded by a modifying adjective but has no article (e.g., "She
became ___ respected researcher in the field"). The blank sits at the
determiner position. The correct answer is the indefinite article ("a" or
"an"). The trap is that students skip the article when an adjective intervenes
between the article slot and the noun, or when the noun is an abstract role
(*researcher, scientist, leader*) that feels "generic enough" to omit the
article. In Standard English, every singular count noun requires a determiner.

Distractors: no article (students treat the adjective as a determiner
substitute), "the" (students assume a specific reference even though the noun
has not been previously mentioned), and a demonstrative ("this" or "that")
that over-specifies the reference.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Demonstrative-Determiner Agreement With a Distant Noun**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence where a demonstrative determiner ("this," "that," "these,"
"those") must agree in number with its head noun, but a prepositional phrase
intervenes containing a noun of the opposite number (e.g., "This ___ of
measurements was taken" or "Those ___ of equipment is obsolete"). The blank is
at the head-noun position. The correct answer is the noun whose number matches
the demonstrative. The trap is that students' attention lands on the
intervening noun (which has the opposite number) and they reverse the agreement
direction, choosing a head noun whose number conflicts with the demonstrative.

Distractors: a plural head noun after "this" (pulled by the plural noun in the
intervening phrase), a singular head noun after "those" (pulled by a singular
intervening noun), and an uncountable noun after "these" (students treat mass
nouns as plural).

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `affirmative_agreement`

`so` / `neither` / `nor` responses with inverted auxiliary matching.

**Sub-pattern — Wrong Auxiliary in So/Neither Agreement**

[NO PT EVIDENCE — source: Khan Academy]

Construct a two-sentence context in which the first sentence uses a specific
auxiliary or modal (*can, will, has, is, did*), and the second sentence
expresses agreement with "so" or "neither/nor" followed by a blank for the
auxiliary and then a new subject (e.g., "Marisol can solve differential
equations, and so ___ her brother"). The correct answer is the same auxiliary
or modal used in the first clause, inflected to agree with the *new* subject.
The trap is that students reach for a default "do/does/did" regardless of the
original verb form, or they select the auxiliary that matches the original
subject's number rather than the new subject's number.

Distractors: "does" when the original uses "can" (students default to
do/does/did), "do" when the new subject is singular (agreement with the
original plural subject instead of the new singular one), and "is" when the
original clause uses a lexical verb in present perfect (students confuse the
auxiliary role of "has").

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Polarity Mismatch in So/Neither Response**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence pair where the first clause is negative and the agreement
clause must use "neither/nor" (not "so"), or the first clause is affirmative and
the agreement clause must use "so" (not "neither"). The blank sits at the
agreement word position (e.g., "The committee members did not support the
amendment, and ___ did the chair"). The correct answer is "neither" (or "nor").
The trap is that students reverse the polarity — using "so" after a negative
statement or "neither" after an affirmative one — because they attend to the
overall semantic agreement (both parties agree in sentiment) rather than the
syntactic polarity of the trigger clause.

Distractors: "so" after a negative clause (students focus on shared sentiment,
not clause polarity), "neither" after an affirmative clause (the mirror error),
and "also" or "too" without inversion (students avoid the inversion requirement
entirely, producing a non-Standard-English structure).

Classify with `syntactic_trap_key: "scope_of_negation"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Omitted Subject-Auxiliary Inversion After So/Neither**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which "so" or "neither" introduces an agreement clause
and the blank requires inverted word order (auxiliary before subject) rather
than the standard SVO order (e.g., "The researchers welcomed the new protocol,
and so ___ the laboratory technicians"). The correct answer is a verb phrase
with inverted order ("did the laboratory technicians"); distractors present
non-inverted order ("the laboratory technicians did"). The trap is that
students expect normal subject-verb order and fail to recognize that "so" and
"neither" as sentence-initial adverbs trigger subject-auxiliary inversion in
Standard English. This pattern also appears with "nor" after a negative clause.

Distractors: non-inverted order (students default to SVO even after "so" or
"neither"), a double-negative auxiliary after "neither" (e.g., "neither don't
I" — students stack negation), and subject pronouns instead of subject nouns
that obscure the inversion (students accept "so did they" but reject "so did
the technicians" because the longer subject makes inversion feel unnatural).

Classify with `syntactic_trap_key: "garden_path"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `voice_active_passive`

Active/passive voice creates ambiguity or inconsistency.

**Sub-pattern — Passive Obscures Agent and Creates Wordiness**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which a passive construction ("was determined by the
committee," "were implemented by the researchers") is grammatically correct but
can be replaced by a shorter, clearer active construction ("the committee
determined," "the researchers implemented"). The blank sits at the verb phrase
position. The correct answer is the active-voice version that preserves the
original meaning while eliminating the "by"-agent phrase. The trap is twofold:
students assume passive voice is always acceptable in formal writing (it is
grammatically valid), and the passive version sounds suitably academic, so the
active alternative feels too "plain."

Distractors: the passive construction unchanged (grammatically correct but
wordier), a passive construction with the agent deleted entirely (creates a
truncated passive that hides who performed the action), and an active-voice
version that assigns the verb to the wrong noun (the nearest noun instead of the
logical agent).

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "formal_word_bias"`.

**Sub-pattern — Passive Auxiliary Tense Mismatch**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence whose surrounding clauses establish a specific time frame
(e.g., simple past narration or present-perfect recent action), and place a blank
at the auxiliary position of a passive verb. The correct answer uses the passive
auxiliary that matches the established tense ("was established" in a past-tense
passage, "has been established" in a present-perfect context). The trap is that
distractors offer passive auxiliaries in a different tense — students focus on the
"be + past participle" frame and accept any auxiliary that yields a well-formed
passive, ignoring whether the tense is consistent with the passage.

Distractors: present-perfect passive ("has been") in a past-tense context
(students accept "has been" because it sounds formal), past-perfect passive
("had been") in a simple-past context (students over-correct to past-perfect),
and future passive ("will be") when the passage describes a completed past action.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "tense_proximity_pull"`.

### `negation`

Negation placed where scope ambiguity creates multiple interpretations.

**Sub-pattern — Litotes Misinterpreted as Exact Positive**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence containing a litotes — a negation paired with a
negative-prefixed adjective or adverb ("not uncommon," "not insignificant,"
"not unlikely," "not unreasonable"). The blank sits at the litotes phrase
position. The correct answer preserves the litotes, which conveys a hedged,
understated affirmative. The trap is that students cancel the two negatives
mechanically and select an answer that replaces the litotes with the direct
positive ("common," "significant," "likely," "reasonable"), thereby overstating
the author's meaning. Litotes is always weaker than its direct positive:
"not uncommon" ≈ "somewhat common," not "common."

Distractors: the direct positive adjective ("common" for "not uncommon") —
overstates the claim, a reversal that inverts the litotes into a double-negative
affirmative of the wrong polarity, and a stronger qualifier than the original
("frequent" or "very common" for "not uncommon") that amplifies the hedged
meaning.

Classify with `syntactic_trap_key: "scope_of_negation"` and
`student_failure_mode_key: "overreading"`.

**Sub-pattern — Negation Scoped Over a Quantifier**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which "not" modifies a quantifier rather than the verb
("not all," "not every," "not always"), producing a partial-negation meaning.
The blank sits at the "not + quantifier" position. The correct answer preserves
the partial negation ("not all students," "not every attempt"). The trap is that
students treat the negation as scoping over the entire clause and select an
answer that replaces "not all" with "none," "not every" with "no," or "not
always" with "never" — turning a partial negation into a total negation that
overstates the sentence's meaning.

Distractors: total-negation equivalent ("none" for "not all," "never" for "not
always") — students collapse partial negation to total negation, a bare positive
without negation ("all students" — students drop the negation entirely), and a
repositioned negation that attaches to the verb instead of the quantifier ("All
students did not pass" — students shift the scope of negation, changing the
meaning from "some passed" to "none passed").

Classify with `syntactic_trap_key: "scope_of_negation"` and
`student_failure_mode_key: "scope_blindness"`.

### `logical_predication`

Subject-predicate incompatibility.

**Sub-pattern — Participial-Phrase Opener Demands a Logically Compatible Subject**

(PT6 M2 Q21: "Woven from recycled yarn and hand tufted [...] _______ so lush")

Open the sentence with a participial phrase that describes a *physical
property or process* (woven, painted, built, carved). The blank sits at the
matrix-clause subject. Only the option whose head noun can plausibly *be the
thing that was woven / painted / built* satisfies logical predication; options
that name the artist, the artist's biography, or an event built around the
artist create a dangling modifier even when the resulting sentence is
grammatical. The test is semantic, not syntactic: ask whether the participle
could literally have been applied to the candidate subject.

Distractors: an inverted construction in which the artist creates the artifact
(grammatical but mis-attaches the modifier); a biographical paraphrase
("X is an Argentine textile artist whose tapestries are...") that buries the
true subject one clause deeper; a temporal "when"-clause that swaps the modifier
out for a different relationship.

Classify with `syntactic_trap_key: "modifier_attachment_ambiguity"` and
`student_failure_mode_key: "modifier_hitchhike"`.

**Sub-pattern — Consequence-Marking Participle Where Finite Verb Misaligns**

(PT1 M2 Q21: "snow and ice cover, _______ the monkeys to hunt for marine animals")

Construct a sentence whose first clause names a cause (a condition, a finding,
an event) and end it with a comma followed by a blank that introduces the
downstream consequence. Only the present participle ("forcing," "leading,"
"prompting") attaches as a non-finite consequence-marking modifier of the
prior clause; a finite present-tense verb creates a comma splice, a past-tense
verb breaks tense alignment with the cause clause, and an infinitive
mis-asserts the action as a separate purpose. The subject of the consequence
participle must remain the same logical entity ("the snow," "the cover") that
brought the consequence about. Also exemplified by PT10 M1 Q22.

Distractors: a finite present-tense form ("forces") that produces a comma
splice; a finite past-tense form ("forced") that drifts the tense and re-anchors
the clause; an infinitive ("to force") that recodes consequence as purpose.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

**Sub-pattern — Real Agent Must Be the Grammatical Subject of the Reporting Verb**

(PT11 M2 Q25: "electrograms show that [...] the most highly skilled soccer players have")

Build a sentence whose first phrase names an instrument, recording, study, or
data source ("recordings of electrical activity in the brain"), then place the
blank where the matrix clause must begin. Only the option whose subject is the
true logical agent of the reporting verb ("electrograms show," "the study
finds") makes predication coherent; distractor options nominalize the responses
or push the players themselves into the subject slot, leaving the introductory
phrase without a logical predicate. The trap is that several distractors
preserve all the content words but attach them to a subject that cannot
*perform* the verb's action. Also exemplified by PT11 M2 Q24 (the subject
must logically *lack thermal energy*, not abstractly *explain its inability*).

Distractors: a paraphrase in which the human participants are the subject of
"have," leaving the recordings stranded; a nominalized subject ("responses
show," "the lack of thermal energy explains") that turns the active observation
into an abstract claim; a passive or "captured-in" construction that demotes
the true agent into a modifier.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `quotation_punctuation`

Comma placement with quotation marks.

**Sub-pattern — Comma and Period Inside Closing Quotation Marks (American Convention)**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence that ends with a direct quotation followed by a period or
comma attribution (e.g., "The author writes, 'This discovery ___'" or "She called
the result 'surprising ___' and continued her analysis"). The blank sits at the
punctuation boundary between the closing quotation mark and the sentence-level
punctuation. The correct option places the period or comma inside the closing
quotation mark, following Standard American English convention. The trap exploits
the logical intuition that punctuation should sit outside the quotation if it
belongs to the surrounding sentence — British convention allows this, but the
SAT follows American convention unconditionally.

Distractors: the period or comma placed outside the closing quotation mark
(British convention, wrong on the SAT), no comma before the opening quotation
mark when a verb of speaking introduces the quote, and a semicolon or colon
placed inside the closing quotation mark (these always go outside).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "punctuation_intimidation"`.

**Sub-pattern — Colon vs. Comma Before a Full-Sentence Quotation**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which a complete independent clause precedes a direct
quotation, and the blank sits at the punctuation mark introducing the quotation
(e.g., "The governor was clear about one thing___ 'The budget must be
balanced.'"). The correct option is a colon because the introductory clause is a
complete sentence and the quotation is a formal amplification. The trap is that
students reach for a comma — which is also valid after verbs of speaking — but
a comma after a non-speaking verb (*stated, emphasized, insisted*) in a full
declarative sentence is less conventional than a colon; meanwhile, a colon after
an incomplete thought (*The governor announced: "..."*) is always wrong.

Distractors: a comma after an incomplete introductory clause (*announced,*
instead of *announced:*), a colon after a fragment rather than a complete
independent clause, and no punctuation before the quotation at all (run-in
without attribution).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

**Sub-pattern — Integrated Short Quotation Without Introductory Comma**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which a short word or phrase is quoted and woven into
the surrounding syntax without an introductory verb of speaking (e.g., "The
researchers described the phenomenon as '___ unprecedented' in the field" or
"She argued that the policy was '___ counterproductive' from the start"). The
blank sits at the punctuation before the quotation. The correct option is no
comma — a short, integrated quotation needs no introductory punctuation. The
trap is that students insert a comma before every quotation mark, treating all
quotations as if they were introduced by a verb of speaking, when in fact only
full-sentence quotations after attribution verbs need introductory commas.

Distractors: a comma before the integrated quotation (students over-apply the
"comma before quote" rule), a colon before a short integrated phrase (students
treat any quotation as requiring formal introduction), and a period splitting the
quotation into a separate sentence (students break the integration).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "punctuation_intimidation"`.

### `transition_logic`

Two adjacent sentences with a logical relationship that must be named
precisely. Place the blank at the transition position. See B.5 for the full
subtype vocabulary. Choose distractor transitions from different relationship
families (contrast, causal, additive, etc.) so each wrong option tests a
distinct confusion.

**Sub-pattern — Causal Result After Mechanism Description**

(PT1 M2 Q28: "These spatulae temporarily bond with the atoms of whatever they touch")

Write a first sentence that names a mechanism, structure, or process, and a
second sentence that states the observable outcome that follows from it. The
blank sits at the head of the outcome sentence and must signal a
cause-to-effect relationship (`as a result`, `consequently`, `hence`,
`accordingly`). The trap is that the two sentences share topic and lexical
field, which makes additive or exemplifying transitions feel locally plausible
even though only causation accounts for why the second sentence is true.

Distractors: at least one exemplifying word (`for example`, `for instance`)
that treats the outcome as one of many cases, one contrast word (`however`,
`in contrast`) that wrongly opposes the two sentences, and one
temporal/additive word (`meanwhile`, `similarly`, `previously`) that ignores
the causal direction.

Classify with `syntactic_trap_key: "none"`,
`transition_subtype_key: "result_consequence"`, and
`student_failure_mode_key: "transition_assumption"`.

**Sub-pattern — Converse Pairing of Parallel Cases**

(PT1 M1 Q30: "Domesticated dogs, _______ can see, hear, and smell by the end of two weeks")

Build two sentences (or two clauses straddling the blank) that describe two
named entities, groups, or systems on the same measurable dimension, where
each entity sits at the opposite end of that dimension. The blank must signal
the converse relationship — not refutation of a claim, but a side-by-side
opposite (`by contrast`, `conversely`, `on the other hand`). The trap is
surface parallelism: the matched syntax and shared topic make additive or
similarity transitions feel right even though the substantive content is
opposed.

Distractors: a similarity word (`similarly`, `likewise`, `in addition`) that
collapses the contrast, an exemplifying word (`for example`, `for instance`)
that recasts the second case as a sub-case of the first, and a
restatement word (`in other words`, `in summary`) that wrongly treats the two
cases as the same point rephrased.

Classify with `syntactic_trap_key: "none"`,
`transition_subtype_key: "converse_opposite"`, and
`student_failure_mode_key: "transition_wrong_direction"`.

**Sub-pattern — Expectation Reversal After a Setup**

(PT11 M2 Q28: "jorō spiders are gentle giants")

Construct a first sentence that establishes an expectation — a hypothesis the
researchers held, a prediction the model implies, an assumption the reader
would default to — and a second sentence that reports a finding that defeats
that expectation. The blank takes a refutation or alternative transition
(`however`, `still`, `instead`, `nevertheless`, `though`). The trap is that
the setup sentence often reads as a positive forward-moving claim, so a
causal or confirming transition feels natural until the reader notices the
second sentence overturns rather than extends the setup.

Distractors: a causal/confirming word (`therefore`, `accordingly`, `indeed`)
that treats the finding as following from the setup, an exemplifying word
(`for example`, `for instance`) that treats the finding as an illustration
rather than a contradiction, and an additive word (`furthermore`, `in
addition`) that ignores the reversal.

Classify with `syntactic_trap_key: "none"`,
`transition_subtype_key: "contrast_refutation"`, and
`student_failure_mode_key: "transition_wrong_direction"`.

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

**Sub-pattern — Redundant Pairing**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence containing an adjacent word pair where the second word restates
the meaning already expressed by the first (e.g., "end result," "advance forward,"
"repeat again," "each and every," "reason is because"). The blank sits at the
redundant word. The correct answer deletes the redundant word or replaces the
pair with a single word. The trap is that the redundant word sounds emphatic or
formal rather than unnecessary — students accept "advance forward" because
"forward" seems to add directional precision, when in fact "advance" already
includes the forward direction.

Distractors: the redundant word retained (sounds more emphatic or specific but
adds no meaning), a synonym that also restates the first word in a different way
(e.g., "final result" instead of "end result" — still redundant), and a shorter
option that deletes the redundant word but also removes a necessary qualifier
or contrast word, making it too concise.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "longer_answer_bias"`.

**Sub-pattern — Nominalization Wordiness**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where a verb has been turned into a noun phrase preceded by a
weak verb ("make a decision," "carry out an investigation," "give an explanation
of"). The blank sits at the nominalized construction. The correct answer replaces
the nominalized phrase with the direct verb form ("decide," "investigate,"
"explain"). The trap is that the nominalized version sounds more formal or
academic, so students assume it must be the correct choice, when in fact the
DSAT rewards concision and the direct verb preserves all meaning in fewer words.

Distractors: the nominalized phrase retained (sounds formal but is wordy), an
even longer nominalization that adds unnecessary prepositional phrases ("make a
decision about the matter of"), and a shorter option that replaces the
nominalization with a verb but also deletes a necessary adverb or qualifier
("quickly decided" becomes just "decided"), losing precision along with the
wordiness.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "formal_word_bias"`.

**Sub-pattern — Shorter Option Deletes Required Qualifier**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence where several options express the same core idea with different
amounts of wording, and the shortest option removes a qualifier, contrast word, or
logical connector that is essential to the sentence's meaning (e.g., the shortest
drops "however" from a contrast sentence, or removes "only" from a restrictive
clause). The correct answer is the most concise option that still preserves the
required qualifier. The trap is the student's instinct to always pick the shortest
answer on concision questions, which leads to deleting a word that carries
irreplaceable logical content.

Distractors: the shortest option that deletes the essential qualifier (passes the
concision test but changes the meaning), the original wordy option that retains the
qualifier but also includes redundant phrasing (preserves meaning but is not
concise), and a mid-length option that retains the qualifier but adds unnecessary
synonyms or padding.

Classify with `syntactic_trap_key: "scope_of_negation"` and
`student_failure_mode_key: "underreading"`.

### `precision_word_choice`

Create a context where several real words share a broad semantic field but only
one has the exact denotation, connotation, or selectional fit required by the
sentence. Do not use commonly confused pair items here; those belong to
`commonly_confused_words`.

Wrong options are grammatically viable and topic-related but too broad, too
strong, too weak, or mismatched to the noun/verb they modify.

**Sub-pattern — Vague Pronoun vs. Specific Name in Rhetorical Synthesis**

(PT5 M1 Q31: "The real author of Adam Bede was Mary Ann Evans, who published the novel using the pseudonym George Eliot")

Construct a notes-synthesis prompt whose stated goal requires the student to
identify a specific person, entity, or value by name. The correct option names
the entity explicitly; distractors use vague pronominal references ("a woman,"
"someone," "they") or paraphrase around the name without actually stating it.
The trap is that vague options feel like they address the goal ("identifies the
author") while omitting the precise detail the goal demands (the actual name).
Students who prefer a fluent-sounding sentence over an exact one fall for the
vague option.

Distractors: partial-purpose option that restates context without naming the
target, a vague-pronoun option that gestures at the answer without specifying,
and an over-scope option that adds unsupported claims.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_content_omission"`.

**Sub-pattern — Qualified Generalization vs. Overstatement in Notes Synthesis**

(PT6 M1 Q33: "Although most materials used in dhow replicas are traditional, some modern materials are used")

Construct a notes-synthesis prompt whose goal asks for a generalization about a
topic where the notes include both a dominant pattern and a qualifier (e.g.,
"most X are Y" plus "some X are Z"). The correct option preserves the qualifier
("Although most…, some…"); distractors either drop the qualifier (pure
generalization), focus on a single detail, or shift scope to a different topic.
The trap is that the unqualified generalization sounds more confident and
"academic," but it overstates what the notes actually support.

Distractors: unqualified generalization that drops the qualifier, a narrow-
focus option that highlights one detail rather than generalizing, and a wrong-
scope option that discusses a related but irrelevant aspect.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

**Sub-pattern — Exact Word Selection in a Semantic Field**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence with a blank where four real words share a broad semantic
field but only one carries the precise denotation, connotation, or selectional
fit the context requires (e.g., "exacerbated" vs. "worsened" vs. "increased" vs.
"heightened" before "tensions"). The passage context narrows the choice to one
word whose exact shade of meaning matches the noun or verb it modifies. The
trap is that near-synonyms are all grammatically viable and feel "close enough,"
but only one is precise. This sub-pattern is for word-precision items in
grammar-land, not for commonly-confused-word pairs (which belong in
`commonly_confused_words`).

Distractors: a near-synonym that is too broad or neutral, a near-synonym that
is too strong or extreme, and a near-synonym whose connotation clashes with the
surrounding register or tone.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

### `register_style_consistency`

Use a formal academic sentence or passage with a blank where only one option
matches the established register, stance, and idiomatic style. The correct
option should be natural in College Board explanatory prose.

Wrong options include conversational phrasing, inflated pseudo-academic diction,
technical diction from the wrong field, or a tone shift that clashes with the
surrounding passage.

**Sub-pattern — Active Voice Over Passive in Sentence Completion**

(PT6 M2 Q20: "One of the few African American global explorers during the turn of the 20th century, _______")

Construct a sentence that opens with an introductory appositive or participial
phrase identifying a person, then place the blank where the main clause must
begin. The correct option supplies the proper noun as subject followed by an
active-voice predicate; distractors include a passive-voice variant, a cleft or
inverted construction, and a syntactically correct but stylistically indirect
rearrangement. All distractors are grammatically permissible but violate the
register and directness expected in Standard English explanatory prose. The trap
is that passive and inverted options "sound formal" to students who equate
complexity with correctness.

Distractors: passive-voice option ("were made by"), inverted emphasis option
placing temporal bounds first ("1891 and 1909 were the years between which…"),
and a redundant cleft construction ("was where…").

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "register_confusion"`.

**Sub-pattern — Appropriate Generalization Level in Rhetorical Synthesis**

(PT8 M1 Q33: "Researchers have used statistical methods to address questions of authorship within the field of music")

Construct a notes-synthesis prompt whose goal asks for a generalization about
the *type* or *kind* of study, approach, or phenomenon, not for a specific
finding or numerical result. The correct option generalizes at the right level
("statistical methods to address questions of authorship in music"); distractors
either over-specify by quoting a narrow finding, overreach by making a claim the
notes do not support, or shift scope to a different aspect. The trap is that
over-specific options feel "more accurate" because they include exact details,
but they fail the stated goal of generalizing.

Distractors: overreach option that states a definitive conclusion beyond the
data, over-specific option that quotes a particular finding or percentage, and
a scope-shift option that discusses the wrong aspect of the notes.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

**Sub-pattern — Formal Register vs. Casual or Inflated Diction**

[NO PT EVIDENCE — source: College Board]

Construct an academic passage with a blank at a word or phrase choice where one
option matches the register (formal, measured, objective), one option is too
casual or colloquial ("a whole lot of," "kind of," "really big"), one option is
overly inflated or pseudo-academic ("utilize" for "use," "facilitate" for
"help"), and one option introduces a tone shift that clashes with surrounding
prose. The trap is that students who favor formality select the inflated option
(the "utilize" trap), while students who process literally may choose the casual
option if it seems clear enough. Only the option that matches the established
register is correct.

Distractors: casual/colloquial option (wrong register), inflated/pseudo-academic
option (wrong register in the other direction), and a tone-shift option that
breaks consistency with the surrounding passage.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "formal_word_bias"`.

### `logical_relationships`

Construct adjacent clauses or sentences where the blank must preserve a cause,
contrast, concession, condition, example, or continuation relationship. Use this
focus when the tested expression is not a standalone transition word covered by
`transition_logic`.

Wrong options signal the wrong relationship, reverse cause and effect, overstate
certainty, or connect two ideas that the passage keeps separate.

**Sub-pattern — Infinitive of Purpose After an Action Verb**

(PT9 M2 Q20: "uses poetry rather than prose _______ the true story")

Construct a main clause whose verb names a deliberate action ("uses," "designed,"
"created," "wrote"), then place the blank where a downstream phrase must express
the *purpose* for which the action was undertaken. Only the bare-infinitive
("to tell," "to forge") encodes the purpose relationship; a finite verb would
turn the second clause into an independent claim, and a participle would shift
the relationship to manner or simultaneity. See B.5 (`purpose_action`) for the
related transition family. Also exemplified by PT4 M2 Q24 ("a contest [...] to
forge").

Distractors: a finite present or past form that creates a comma splice or
falsely asserts the action as a separate event; a bare gerund/participle that
recasts the relationship as accompaniment; a coordinated "and + -ing" form that
turns purpose into a second action.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "nonfinite_for_finite"`. The
`transition_subtype_key` for the correct option is `purpose_action`.

**Sub-pattern — Active Subject Preserves Causal Agency After a Causal Cue**

(PT11 M1 Q23: "the titles allow the listener to approach each piece free from expectations")

After a prior clause has named an *agent* and an *intended effect*, place the
blank at a continuation slot where one option makes the true agent the
grammatical subject of an active verb while distractor options bury the agent
in a "by"-phrase, a possessive ("the bioswales' mitigation"), or a
nominalization ("the mitigation of..."). All four options can be parsed, but
only the active-subject version preserves the causal relationship that the
prior sentence sets up. Also exemplified by PT4 M2 Q25 ("the bioswales have
mitigated [...] flooding").

Distractors: a passive construction that demotes the agent to an oblique
phrase; a nominalized-subject version that turns the action into an abstract
state; a possessive-headed paraphrase that obscures who is doing what.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "grammar_fit_only"`.

**Sub-pattern — Finite Verb Required to Anchor a Compound Subject**

(PT8 M2 Q22: "His energetic gestures [...] and his habit of barreling [...] _______ transform")

Build a sentence with a long compound subject (two parallel noun phrases joined
by "and") whose verb sits at the blank. The reader is tempted to extend the
nominal-modifier chain ("helping," "that helped," "to help") that ran through
the second conjunct, but the sentence still needs a *finite* verb to predicate
the compound subject; only the finite past form ("helped") closes the clause.
Also exemplified by PT7 M1 Q25, where only the option that supplies the
sentence's true subject and a finite predicate ("the Alaska Centennial
Commission sponsored a contest") completes the participial-phrase opener
coherently.

Distractors: a participle ("helping") that continues the modifier chain
without ever predicating; a relative clause ("that helped") that buries the
predication; an infinitive ("to help") that re-reads the relationship as
purpose.

Classify with `syntactic_trap_key: "long_distance_dependency"` and
`student_failure_mode_key: "nonfinite_for_finite"`.

### `emphasis_meaning_shifts`

Create a sentence where word order, modifier placement, or phrase choice changes
what information is emphasized. The correct option foregrounds the fact named in
the stem without changing the underlying claim.

Wrong options are factually compatible but emphasize the wrong actor, quantity,
contrast, time period, or implication.

**Sub-pattern — Distance or Quantity Foregrounding via Modifier Placement**

(PT8 M1 Q30: "The sixty-two-mile-long Philadelphia and Lancaster Turnpike connected")

Construct a notes-synthesis prompt whose goal explicitly asks the student to
emphasize a measurable quantity — distance, area, population, or duration. Place
the blank where the quantity modifier must attach to the subject noun phrase so
that it becomes the sentence's focal descriptor. The correct option front-loads
the quantity ("sixty-two-mile-long") and pairs it with the entity endpoints;
distractors either bury the quantity in a subordinate clause, omit it entirely,
or foreground a different attribute (historical primacy, construction date)
instead. The trap is that students who process content holistically may select a
factually accurate sentence that never actually foregrounds what the stem asks
them to emphasize.

Distractors: a wrong-scope option that highlights historical primacy or
chronological status instead of quantity, a partial-purpose option that mentions
the entity but omits the requested quantity, and a scope-shift option that
focuses on dates or categories rather than measurement.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

**Sub-pattern — Main-Clause vs. Subordinate-Clause Emphasis Shift**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where the stem asks the student to emphasize one fact, and
the answer choices vary which clause is main and which is subordinate. The
correct option places the emphasized information in the main clause and
subordinates the supporting detail; distractors reverse this hierarchy, placing
the emphasized fact in a dependent clause introduced by "although," "while," or
"despite," while the less important fact occupies the main clause. All options
are grammatically correct and factually true, but only the one whose clause
hierarchy matches the stem's emphasis goal is correct. The trap is that students
who check only factual accuracy — not rhetorical emphasis — miss the structural
cue.

Distractors: a reversed-emphasis option that subordinates the requested fact,
a balanced-coordination option that gives equal weight to both facts, and a
scope-shift option that emphasizes a tangential detail not requested by the stem.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

**Sub-pattern — Actor vs. Recipient Emphasis via Voice and Structure**

[NO PT EVIDENCE — source: Khan Academy]

Construct a passage or notes-synthesis prompt where the stem asks the student to
emphasize what a specific actor did. The correct option uses active voice with
the actor as subject; distractors include a passive-voice version that promotes
the recipient to subject, a cleft or existential construction that buries the
actor, and a nominalization that turns the action into an abstract noun phrase.
All four options convey the same underlying facts, but only the active-voice
option centers the actor as the stem requires. The trap is that passive
constructions sound "formal" and therefore correct to students who conflate
register with emphasis.

Distractors: a passive-voice option that promotes the recipient, a
nominalization option that turns the action into an abstract noun, and a
cleft/existential option that obscures agency.

Classify with `syntactic_trap_key: "nominalization_obscures_subject"` and
`student_failure_mode_key: "grammar_fit_only"`.

### `data_interpretation_claims`

Use a short table, graph, or data description with a sentence that must
accurately state a claim supported by the data. The correct option names the
right variable, group, direction, and constraint.

Wrong options cite real values while using the wrong comparison, wrong group,
wrong time window, or wrong proportional/absolute interpretation.

**Sub-pattern — Classification Logic Synthesis from Structured Notes**

(PT6 M2 Q33: "Having the potential to damage national security if disclosed, most routine diplomatic correspondence is classified as Confidential")

Construct a notes-synthesis prompt whose goal asks the student to apply a
classification or conditional rule from the notes to a specific case. The
correct option must combine two facts — the rule ("information causing 'damage'
is Confidential") and the case ("routine diplomatic correspondence causes damage
but not serious damage") — to produce a single sentence that identifies the
correct category. Distractors reverse the causal attribution (the government
classifies *as* Confidential rather than *because it is* Confidential), describe
the system without applying it, or broaden the scope to include irrelevant
details. The trap is that reversed-attribution options sound authoritative
because they use vocabulary directly from the notes.

Distractors: a reversed-attribution option that swaps the subject and predicate
of the classification rule, a partial-purpose option that restates the general
principle without specifying which category applies, and a scope-extension
option that introduces an irrelevant detail from the notes.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

**Sub-pattern — Proportional vs. Absolute Claim from Data**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a passage or data set where values increase in absolute terms but
decrease or remain flat in proportional (per-capita, percentage, rate) terms —
or vice versa. The stem asks which claim the data best supports. The correct
option frames the claim in the proportional dimension; distractors state the
absolute trend (which is technically true but answers the wrong question), claim
a causal mechanism the data does not support, or conflate the two dimensions.
The trap is that students who read only the directional trend (up or down)
without checking whether the unit is absolute or proportional will select the
absolute-trend distractor.

Distractors: an absolute-trend option that is directionally true but addresses
the wrong unit, a causal-claim option that overreaches beyond the data, and a
scope-blend option that mixes absolute and proportional language ambiguously.

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "overreading"`.

**Sub-pattern — Reversed Attribution in Data-Backed Claims**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence or synthesis prompt where a relationship between two
variables is described, and the correct option must preserve the direction of
the relationship (X predicts Y, not Y predicts X). Distractors reverse the
independent and dependent variables, present a correlational statement as
causal, or swap the compared groups. All distractors use vocabulary and values
drawn directly from the source material, making them feel substantiated. The
trap is that the reversed-attribution distractor is nearly identical to the
correct answer except for which variable is the subject and which is the
outcome.

Distractors: a reversed-direction option that swaps cause and effect, a
correlation-as-causation option that overstates the relationship, and a
wrong-group option that attributes the finding to the wrong population.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "scope_blindness"`.

### `conjunction_usage`

Build a sentence where a subordinating, coordinating, or correlative conjunction
determines the logical relation between clauses. The correct option supplies the
only conjunction or paired conjunction that preserves the intended relationship
and syntax.

Wrong options are grammatically possible but signal the wrong relation, leave a
correlative pair incomplete, or create a clause-type mismatch.

**Sub-pattern — Double Conjunction Error**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where a subordinating conjunction and a coordinating
conjunction both appear for the same logical relationship (e.g., "Although she
studied hard, but she still struggled"). The blank sits at one of the conjunction
positions. The correct answer removes one conjunction — either keep the
subordinating conjunction with no comma-plus-FANBOYS, or replace the subordinating
conjunction with a comma-plus-FANBOYS. The trap is that both words individually
signal the same logical relationship (contrast), so students assume adding both
strengthens the connection, when in fact the double conjunction creates a
grammatical error.

Distractors: retaining both conjunctions (sounds emphatic but is ungrammatical),
replacing the subordinating conjunction with a different subordinating conjunction
that preserves the redundancy (e.g., "Even though…but"), and removing the comma
between the clauses without removing either conjunction (creates a run-on rather
than fixing the double-conjunction error).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "transition_wrong_direction"`.

**Sub-pattern — Wrong Logical Relation Conjunction**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence where the blank is a conjunction or transitional adverb and
the surrounding context signals a specific logical relationship (cause, contrast,
concession, condition) that the correct answer must match. Distractors supply
conjunctions that are grammatically possible but signal the wrong relationship
(e.g., "therefore" in a contrast sentence, "however" in a cause-and-effect
sentence). The trap is that each distractor conjunction is a real, common
transition word — the student must determine which logical relationship the
sentence requires, not merely which word sounds formal or plausible.

Distractors: a conjunction signaling the opposite relationship (contrast for
cause, addition for concession), a conjunction that is vague or neutral and
fails to specify the relationship, and a conjunction that is grammatically
correct in isolation but creates a comma splice or fragment in the given
sentence structure.

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "transition_wrong_direction"`.

**Sub-pattern — Correlative Pair Mismatch**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence where a correlative conjunction pair appears with an
incorrect or incomplete second half (e.g., "neither…or" instead of "neither…nor",
"both…as well as" instead of "both…and", "not only…but" without "also"). The
blank sits at the second half of the pair. The correct answer supplies the
canonical partner. The trap is that the imposter pair sounds familiar ("both…as
well as" is common in speech; "neither…or" feels natural by analogy with
"either…or") and students do not verify that both halves form a recognized
correlative pair.

Distractors: the common but incorrect pairing ("neither…or," "both…as well as,"
"not only…but" without "also"), a coordinating conjunction that works
syntactically but does not complete the correlative pair ("neither…and"), and a
restructured version that removes the correlative pair entirely and uses a simple
conjunction, losing the emphasis the correlative pair provides.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "idiom_memory_pull"`.

### `elliptical_constructions`

Use a comparison or parallel structure where repeated words are omitted
legitimately only if the remaining structure is still recoverable and parallel.
The correct option preserves the omitted material's role without ambiguity.

Wrong options omit too much, omit from only one side of a comparison, or create
an elliptical phrase whose missing words would not match the prior structure.

**Sub-pattern — Pronoun Case After Than or As**

[NO PT EVIDENCE — source: PrepScholar]

Construct a comparison using "than" or "as" where the blank is a pronoun that
completes an elliptical clause (e.g., "She is taller than ______"). The correct
answer supplies the subjective-case pronoun ("I," "he," "she," "they") because
the omitted verb makes it the subject of the elliptical clause ("than I am"). The
trap is that the objective case ("me," "him," "her," "them") sounds natural in
casual speech and appears plausible because students fail to mentally supply the
omitted verb to test which case the pronoun must satisfy.

Distractors: objective-case pronoun (sounds natural in conversation but is
grammatically incorrect in the elliptical construction), reflexive pronoun
("myself," "himself" — adds false precision without satisfying the syntactic
slot), and possessive pronoun ("mine," "hers" — changes the comparison from
subject-to-subject to subject-to-possession).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Ambiguous Ellipsis After Than**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence with a "than" comparison where omitting the verb creates two
grammatically valid but logically distinct readings (e.g., "John likes Mary more
than Paul" — either John likes Mary more than Paul likes Mary, or John likes Mary
more than John likes Paul). The blank sits where a disambiguating verb or
pronoun should appear. The correct answer supplies the form that matches the
intended comparison. The trap is that both readings are grammatically possible, so
students accept the ambiguous version because it "sounds fine" without noticing
that the omission makes the sentence logically unclear.

Distractors: the ambiguous bare form with no disambiguating verb (both readings
are possible, so the student picks it by default), a verb that resolves the
ambiguity toward the wrong reading (correct grammar but wrong meaning), and a
restructured version that preserves the comparison but introduces an unnecessary
preposition or shifts the clause order.

Classify with `syntactic_trap_key: "pronoun_ambiguity"` and
`student_failure_mode_key: "underreading"`.

**Sub-pattern — Missing "That of / Those of" in Possessive Comparison**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence that compares a quality attributed to one entity with a
different entity directly rather than with the same quality of that entity
(e.g., "The population of China is larger than India" — should be "larger than
that of India" or "larger than India's"). The blank sits at the point where
"that of" or "those of" is needed. The correct answer inserts the demonstrative
pronoun plus preposition to restore logical parallelism. The trap is that the
sentence reads fluently without the demonstrative — the reader's mind
automatically supplies the missing comparison point — so the omission feels
natural even though it compares a population to a country rather than a
population to a population.

Distractors: the bare noun without the demonstrative (reads smoothly but makes
an illogical comparison), a possessive form that partially fixes the comparison
but changes the sentence structure unnecessarily, and a version that substitutes
"like" or "similar to" for "than," changing the comparison from inequality to
similarity.

Classify with `syntactic_trap_key: "pronoun_ambiguity"` and
`student_failure_mode_key: "illogical_comparison_blindness"`.

### `comparative_structures`

Use two items in an explicit "more/less/better than" comparison where one element is a noun and the other is an action, process, or dissimilar form. The trap: students do not notice the compared terms are structurally mismatched.

Correct option: uses "that of" or "those of" or a matched parallel noun form.
Wrong options: preserve the bare unparalleled comparison in varied surface forms.

### `illogical_comparison`

Construct a sentence comparing a noun directly to an action, process, or dissimilar category (e.g., "the revenue of Company X exceeded Company Y"). The error is logical, not formal: both elements exist but they belong to different categories.

Correct option: inserts "that of" or restructures so both compared items are the same grammatical and logical category.
Wrong options: preserve the illogical pairing in different surface wordings.

**Sub-pattern — Person-vs-Work Comparison**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence that compares a creative work or attribute of a person to
the person's bare name ("the novels of Jane Austen are more widely read than
Charlotte Bronte," "the paintings of Frida Kahlo are more influential than Diego
Rivera"). The blank sits at the point where the second compared element appears.
The correct option inserts "those of" (for plural works) or "that of" (for a
singular attribute) before the bare name, or uses the possessive form
("Charlotte Bronte's"); distractors keep the bare proper noun, which illogically
compares novels to a person. The trap exploits the fact that full names of
artists and authors are commonly used metonymically in casual speech, so the
illogical comparison sounds natural.

Distractors: the bare proper noun without possessive or demonstrative (compares
a work to a person), a possessive noun that still produces a category mismatch
("the novels of Jane Austen" compared to "Charlotte Bronte's reputation"), and
a restructuring that paraphrases the sentence but retains the person-vs-work
comparison in a different form.

Classify with `syntactic_trap_key: "nearest_noun_attraction"` and
`student_failure_mode_key: "illogical_comparison_blindness"`.

**Sub-pattern — Attribute-vs-Entity Comparison With Intervening Phrases**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence in which an attribute of one entity is compared to a
different entity entirely, with long prepositional phrases or nonrestrictive
clauses separating the two compared elements ("the mass of its tiny body is
smaller than humans, who have comparatively enormous frames"). The blank sits at
the second compared element. The correct option inserts "that of" before "humans"
or restructures to compare mass to mass ("the mass of its body is smaller than
that of a human"); distractors preserve the bare comparison of mass to people,
or add a helper verb that still compares an attribute to an entity. The trap
relies on the intervening descriptive material, which masks the category mismatch
by making the sentence sound complete and fluent.

Distractors: the bare noun comparison without "that of" (attribute compared to
entity), a helper verb ("humans do") that fails to resolve the category mismatch
because the verb describes human action rather than human mass, and a
restructuring that adds a prepositional phrase to the second element but
compares a different attribute than the first.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "illogical_comparison_blindness"`.

### `adjective_adverb_distinction`

**Variant A — linking verb:** Use a linking verb (appear, feel, seem, remain, become, look, sound, taste, smell) followed by the blank. Correct option: adjective (subject complement). Wrong options: adverb, comparative adverb, past participle.

**Variant B — action verb:** Use an action verb followed by a manner blank. Correct option: adverb. Wrong options: adjective, comparative adjective, noun phrase.

Classification: `grammar_role_key: "modifier"`, `grammar_focus_key: "adjective_adverb_distinction"`.

**Sub-pattern — Linking-Verb Sense Word Requires Adjective**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence in which a linking or sense verb (feel, smell, taste, look,
sound, appear, seem, remain, become) connects the subject to a blank that
describes the subject's state or quality, not the manner of the verb's action.
The correct option supplies an adjective ("feels bad," "smells sweet," "tastes
sour," "looks calm"). The trap exploits the fact that adding "-ly" to form an
adverb sounds more formal or "correct" to many students ("feels badly," "smells
sweetly," "tastes sourly"), when in fact the adverb form is almost always wrong
after a linking verb because it describes how the action of sensing is performed
rather than the subject's state. The only case where the adverb is correct is
when the verb describes an actual sensory action ("the dog smells carefully"),
and the SAT never tests this rare reading on the adjective/adverb distinction.

Distractors: the -ly adverb form after the linking verb ("badly" for "feels
badly"), the comparative adverb ("more sweetly"), and a past participle used as
a subject complement that creates a different meaning or tense error.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "adverb_adjective_confusion"`.

**Sub-pattern — Action-Verb Manner Blank Requires Adverb**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence in which an action verb (run, speak, work, examine, drive,
perform) is followed by a blank that modifies the verb, describing how the
action is performed. The correct option supplies an adverb ("spoke fluently,"
"examined the specimen carefully," "drove recklessly"). The trap exploits the
fact that many adjectives sound natural after common action verbs in casual
speech ("she drove careful," "he spoke fluent"), and students must recognize that
an adjective after an action verb is grammatically wrong because it has no noun
to modify. This sub-pattern pairs especially well with verbs that also function
as linking verbs in other contexts (e.g., "look" — "she looked carefully" vs.
"she looked calm"), testing whether the student can identify the verb's function
in the specific sentence.

Distractors: the adjective form after the action verb ("careful" instead of
"carefully"), the comparative adjective ("more careful"), and a noun phrase that
replaces the manner adverb with a prepositional phrase or object.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "adverb_adjective_confusion"`.

### `commonly_confused_words`

Select one pair of commonly confused non-homophone words:
`affect/effect`, `principle/principal`, `allusion/illusion`, `elicit/illicit`, `imply/infer`, `complement/compliment`, `compose/comprise`, `disinterested/uninterested`, `emigrate/immigrate`.

Write a passage where the meaning distinction is essential to the sentence. Wrong options present the other member(s) of the confused pair plus one additional plausible but incorrect option.

Do NOT use homophone possession pairs (its/it's, whose/who's) — those belong to `possessive_contraction`.

Classification: `grammar_role_key: "expression_of_ideas"`, `grammar_focus_key: "commonly_confused_words"`.

**Sub-pattern — Affect/Effect and Imply/Infer Reversal**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence where the blank requires one member of a commonly reversed
verb-noun pair ("affect" the verb vs. "effect" the noun, or "imply" the
speaker-action vs. "infer" the listener-action). The correct answer supplies the
word whose part of speech and meaning match the syntactic slot. The trap is that
both words share strong phonological similarity and semantic proximity — "affect"
and "effect" both relate to causation, "imply" and "infer" both relate to
conveying meaning — so the wrong member sounds plausible in the sentence until the
student checks whether the slot requires a verb or a noun, a speaker-action or a
listener-action.

Distractors: the reversed member of the pair ("effect" where "affect" is needed,
or "infer" where "imply" is needed — sounds nearly identical and occupies the same
semantic field), a third word from the same semantic field that is grammatically
correct but semantically wrong (e.g., "produce" where "affect" is needed), and a
more formal synonym that changes the sentence's register without fitting the
precise meaning (e.g., "insinuate" where "imply" is needed).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Near-Homophone Confusion (Principal/Principle, Stationary/Stationery)**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where the blank requires one member of a near-homophone pair
whose members differ by a single letter or vowel swap ("principal" vs.
"principle," "stationary" vs. "stationery," "complement" vs. "compliment,"
"discreet" vs. "discrete"). The correct answer supplies the word whose meaning
fits the sentence context. The trap is that both words sound identical or nearly
identical in speech and differ by only one letter in writing, so students who
process by sound rather than by meaning cannot distinguish them. The sentence
context must be specific enough that only one member of the pair fits — but the
other member has a plausible "sounds-right" reading.

Distractors: the near-homophone partner ("principle" where "principal" is needed,
"stationery" where "stationary" is needed — passes the "sounds right" test), a
word from an adjacent semantic field that is spelled differently but has a similar
meaning component (e.g., "rule" where "principle" is needed, but "rule" is not a
member of the tested pair), and a more common word that loosely fits the context
but is not the precise member of the confused pair (e.g., "main" where
"principal" is needed).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Elicit/Illicit and Complement/Compliment Context Trap**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence where the blank requires one member of a confused pair whose
members share a root or phonological form but differ in meaning and grammatical
function ("elicit" a verb meaning "draw out" vs. "illicit" an adjective meaning
"illegal"; "complement" a noun/verb meaning "completes" vs. "compliment" a
noun/verb meaning "praise"; "allusion" a noun meaning "reference" vs. "illusion"
a noun meaning "false perception"). The correct answer supplies the word whose
meaning and part of speech fit the sentence context. The trap is that the sentence
context does not strongly rule out the wrong member — "illicit response" could
seem to mean "drawing out a response" if the student confuses the two words, and
"compliment the design" could seem like "completing the design" if the student
blurs the distinction.

Distractors: the wrong member of the pair (occupies the same syntactic slot and
shares a phonological form — "illicit" where "elicit" is needed, "compliment"
where "complement" is needed), a synonym of the wrong member that is
grammatically correct but semantically off (e.g., "illegal" where "elicit" is
needed, changes the sentence meaning entirely), and a more generic word that
weakens the sentence without being outright wrong (e.g., "draw" where "elicit" is
needed — correct meaning but less precise).

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

**Sub-pattern — Transitive/Intransitive and Role-Confusion Pairs (lie/lay, imply/infer, comprise/compose)**

[NO PT EVIDENCE — source: PrepScholar, The Critical Reader, Magoosh]

Construct a sentence where the blank requires one member of a confused pair
whose members are distinguished by transitivity, direction of action, or
part-whole role.

Tested pairs in this sub-pattern:

| Pair | Rule |
|---|---|
| `lie` / `lay` | `lie` is intransitive (no object: "she *lies* down"); `lay` is transitive (takes object: "she *lays* the book down") |
| `imply` / `infer` | the speaker/writer *implies*; the listener/reader *infers* |
| `comprise` / `compose` | the whole *comprises* the parts ("the kit *comprises* three tools"); the parts *compose* the whole ("three tools *compose* the kit") |
| `farther` / `further` | `farther` for physical distance; `further` for figurative degree or extent |
| `assure` / `ensure` / `insure` | *assure* a person (remove doubt); *ensure* a result (make certain); *insure* against financial risk |
| `between` / `among` | `between` for exactly two items; `among` for three or more |
| `who` / `that` | persons are preferentially introduced by `who` not `that` |

Place the blank at the verb or determiner slot and ensure the sentence
context specifies the direction of action, transitivity, or part-whole
relationship unambiguously. The trap is that both members of the pair are
real English words occupying the same syntactic slot.

Distractors: the reversed member of the pair (most seductive — same
syntactic slot, overlapping semantics), a third word from the same semantic
field that is grammatically acceptable but semantically wrong, and a more
formal synonym that changes register without fitting the precise meaning.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.

### `preposition_idiom`

Construct a sentence with a verb-preposition or adjective-preposition collocation where the correct preposition is idiomatic: `composed of`, `differ from`, `responsible for`, `interested in`, `capable of`, `independent of`, `account for`, `result in`, `consistent with`, `conducive to`.

Wrong options substitute near-correct prepositions that are grammatically viable but idiomatically non-standard ("composed in," "differ with," "responsible to," "account on").

**Sub-pattern — Noun-Preposition Collocation with Internal Punctuation Distractors**

(PT4 M2 Q20: "explored themes of healing, self-discovery, and memory")

Construct a sentence where a noun-preposition collocation (`themes of`, `evidence
of`, `capacity for`) is followed by a list of noun phrases. The blank sits at the
preposition, and the correct option supplies the idiomatic preposition alone
(without punctuation). Distractors append a comma, dash, or colon after the
preposition, exploiting the student's instinct to punctuate before a list. The
trap is twofold: students must know the correct preposition *and* resist the urge
to insert internal punctuation that breaks the prepositional phrase's syntactic
unit. This sub-pattern combines a preposition-idiom test with the
unnecessary-internal-punctuation rule.

Distractors: the correct preposition plus a comma (`of,`), the correct
preposition plus a dash (`of—`), and the correct preposition plus a colon (`of:`)
— all inserting punctuation that violates the rule against breaking a syntactic
unit.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "internal_unit_punctuation_insertion"`.

**Sub-pattern — Verb-Preposition Collocation Swap**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence where the blank follows a verb that requires a specific
preposition (`result in`, `account for`, `differ from`, `conducive to`). All
four answer choices are prepositions. The correct option is the only one that
forms the idiomatic collocation; distractors substitute near-synonymous
prepositions drawn from related but different verb-preposition pairs (`result
from`, `account to`, `differ with`, `conducive for`). The trap is that the
wrong prepositions are grammatically possible in isolation and often appear in
other collocations, so students who rely on "sounds right" without knowing the
specific pairing will be drawn to a plausible but incorrect option.

Distractors: a preposition from a superficially similar collocation (e.g., "from"
when "in" is required), a preposition that forms a real but different idiom
with the same verb (e.g., "differ with" vs. "differ from"), and a preposition
that is common in general usage but wrong for this verb (e.g., "on" for
"result").

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "preposition_idiom_error"`.

**Sub-pattern — Adjective-Preposition Collocation Distractors**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a sentence where the blank follows an adjective that requires a
specific preposition (`capable of`, `interested in`, `consistent with`,
`independent of`). All four answer choices are prepositions. The correct option
completes the idiomatic adjective-preposition unit; distractors offer
prepositions that pair with other adjectives in the same semantic field (`capable
for`, `interested about`, `consistent to`, `independent from`). The trap is
that the wrong prepositions feel plausible because they collocate with nearby
adjectives the student may substitute mentally, and ESL students in particular
may transfer collocations from their first language.

Distractors: a preposition that pairs with a semantically related adjective (e.g.,
"for" from "responsible for" when "of" from "capable of" is required), a
preposition that is common in the general semantic domain (e.g., "about" for
"interested about" instead of "in"), and a preposition that follows a different
but phonologically similar adjective.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "preposition_idiom_error"`.

Classification: `grammar_role_key: "expression_of_ideas"`, `grammar_focus_key: "preposition_idiom"`.

---

## B.4 Distractor Generation Heuristics by Grammar Focus

### `subject_verb_agreement`

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Plural verb (nearest noun attraction) | `nearest_noun_attraction` |
| 2 | Singular verb but wrong tense | `auditory_similarity` |
| 3 | Compound or auxiliary verb that breaks agreement | `grammar_fit_only` |
| 4 | Plural verb after collective noun subject (team/committee/group implies multiple members) | `nearest_noun_attraction` |

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
| 4 | Passive-voice main clause places abstract noun as subject, leaving opening participial phrase dangling (sounds formal and academic) | `formal_register_match` |

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
| 4 | `restatement_clarification` (`in other words`) used where `example` (`for example`) is needed, or vice versa — both "continue" the prior idea but `restatement_clarification` only rephrases while `example` adds a new concrete instance | `transition_assumption` |
| 5 | `purpose_action` (`to that end`) confused with `result_consequence` (`therefore`) — `purpose_action` introduces an *intended future action* to achieve a prior goal; `result_consequence` introduces an *outcome that already follows* from a prior fact | `transition_assumption` |

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
- `absolute_phrase` — nominative absolute construction (noun + participial
  phrase modifying the entire main clause); requires comma boundary; distinct
  from `modifier_placement` because the nominal head is explicit and the phrase
  does not attach to the main-clause subject; promoted from pending in v8.1
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

#### Matching delimiter rule

When a parenthetical element is set off inside a sentence, the opening
delimiter must be matched by the **same type** of closing delimiter:
comma→comma, dash→dash, parenthesis→parenthesis. Mixing is never permitted
(e.g., opening comma + closing dash is always wrong). This rule applies to
all parenthetical elements: appositives, nonrestrictive clauses, and
mid-sentence interruptions. Distractors routinely exploit asymmetric
punctuation — verify both halves of every paired delimiter.

#### No comma before restrictive `that`

On the DSAT, `comma + that` for a relative clause is **never** correct.
`that` always introduces a restrictive (essential) relative clause, and
restrictive clauses are never preceded by a comma. `which` (nonrestrictive)
requires a comma. This distinction is absolute: if the relative pronoun is
`that`, there is no comma; if a comma is present, the relative pronoun must
be `which`.

#### No comma immediately before or after a preposition

No comma may appear directly before or after a preposition (`of`, `by`,
`to`, `at`, `for`, `from`, `with`, `in`, `on`, `that`). A long prepositional
phrase may feel like it earns a rhythmic pause, but the comma is always
wrong. This is a sub-rule of `unnecessary_internal_punctuation`; annotators
should use that key when the test is whether the comma is absent.

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
| `subjunctive_mood` | `verb_form` | PT analysis; counterfactual and hypothetical conditional constructions | Sub-patterns now documented in §B.3 `verb_form` (v8.1 patch). Classify as `grammar_focus_key: "verb_form"` with `subskill: "subjunctive mood"`. Do not create a standalone key. |

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
**`TEST_FORMAT_KEYS`** — Rules v8 generation format keys

- `digital_app_adaptive`
- `nondigital_linear_accommodation`
<!-- VOCAB:system:TEST_FORMAT_KEYS END -->

<!-- VOCAB:system:SOURCE_STATS_FORMAT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`SOURCE_STATS_FORMAT_KEYS`** — Rules v8 source stats format keys

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
**`TRANSITION_SUBTYPE_KEYS`** — Grammar v8 transition_subtype_key

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
**`SYNTHESIS_GOAL_KEYS`** — Grammar v8 notes synthesis goal keys

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
**`AUDIENCE_KNOWLEDGE_KEYS`** — Grammar v8 audience knowledge keys

- `audience_familiar`
- `audience_unfamiliar`
- `not_specified`
<!-- VOCAB:grammar:AUDIENCE_KNOWLEDGE_KEYS END -->

<!-- VOCAB:grammar:REQUIRED_CONTENT_KEYS START -->
<!-- generated from vocabulary/master.json — do not hand-edit -->
**`REQUIRED_CONTENT_KEYS`** — Grammar v8 required content keys

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
**`SYNTHESIS_DISTRACTOR_FAILURE_KEYS`** — Grammar v8 synthesis distractor failure keys

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
