# DSAT Grammar Module — Rules and Generation Guide

## Purpose

Domain module for Standard English Conventions and grammar-adjacent Expression
of Ideas. This file defines grammar-specific classification keys, trap models,
generation heuristics, and validation rules. It is loaded alongside
`rules_core_generation.md` for every grammar item.

Load order: `rules_core_generation.md` → this file.

---

## 1. Scope and Domain Boundary

### Covered domains

- Standard English Conventions (SEC)
- Expression of Ideas questions that are grammar-adjacent (transition logic,
  concision, register, precision)

### Excluded domains

- Information and Ideas: use `rules_dsat_reading_module.md`
- Craft and Structure: use `rules_dsat_reading_module.md`

### Rule-domain separation

If the question requires choosing the correct word because of grammar
(agreement, tense, punctuation), classify as SEC. If the question requires
choosing the correct word because it best expresses the writer's idea,
classify as Expression of Ideas. When both apply, use section 2.4 below.

---

## 2. Grammar Role Keys (Official Taxonomy)

Approved `grammar_role_key` values and when to use each:

| Role key            | Use when...                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| `sentence_boundary` | Fragments, run-ons, comma splices, or punctuation required to close/open sentence units        |
| `agreement`         | Subject-verb agreement, pronoun-antecedent agreement, noun countability, determiners/articles  |
| `verb_form`         | Tense consistency, finite/nonfinite choice, voice, mood, subjunctive, conditional              |
| `modifier`          | Dangling/misplaced modifiers, comparative structures, logical predication, relative pronouns   |
| `punctuation`       | Comma mechanics, semicolons, colons/dashes, apostrophes, appositives, hyphens, quotation marks |
| `parallel_structure`| Parallel lists, correlative conjunctions, comparison form symmetry, elliptical constructions   |
| `pronoun`           | Pronoun case (who/whom), pronoun clarity, pronoun-antecedent agreement                        |
| `expression_of_ideas` | Concision, register, transition logic, precision, rhetorical effectiveness, data accuracy   |

### 2.1 Grammar Focus Keys by Role

#### `sentence_boundary` focus keys
- `sentence_fragment` — subordinate clause or phrase presented as complete sentence
- `comma_splice` — two independent clauses joined with only a comma
- `run_on_sentence` — two independent clauses fused without punctuation or conjunction
- `sentence_boundary` — generic boundary (use when boundary type is ambiguous)

#### `agreement` focus keys
- `subject_verb_agreement` — verb must match true grammatical subject
- `pronoun_antecedent_agreement` — pronoun must match antecedent in number and person
- `noun_countability` — mass noun vs. count noun article/plural conflict
- `determiners_articles` — article choice (a/an/the/zero article)
- `affirmative_agreement` — so/neither/nor response with inverted auxiliary

#### `verb_form` focus keys
- `verb_tense_consistency` — tense must match passage tense register
- `verb_form` — gerund vs. infinitive, finite vs. nonfinite
- `voice_active_passive` — active/passive consistency or correctness
- `negation` — scope of negation; not/never/no placement
- `subjunctive_mood` — were/be required in hypothetical, conditional, or wish clauses

#### `modifier` focus keys
- `modifier_placement` — dangling or misplaced participial/adjectival phrases
- `comparative_structures` — more/less + than; as...as; illogical comparisons
- `logical_predication` — subject and predicate are logically incompatible
- `relative_pronouns` — that vs. which, who vs. that, comma placement for essential/nonessential clauses

#### `punctuation` focus keys
- `punctuation_comma` — FANBOYS comma, introductory phrase comma, nonrestrictive element
- `colon_dash_use` — colon or dash introducing explanation, list, or elaboration
- `semicolon_use` — semicolon between two independent clauses
- `conjunctive_adverb_usage` — semicolon + comma pattern with however/therefore/moreover
- `apostrophe_use` — singular possessive, plural possessive, contractions
- `possessive_contraction` — its/it's, whose/who's, your/you're, their/they're
- `appositive_punctuation` — essential vs. nonessential appositive comma rules
- `hyphen_usage` — compound modifier before noun
- `quotation_punctuation` — comma/colon placement with quotation marks

#### `parallel_structure` focus keys
- `parallel_structure` — list or paired items must share grammatical form
- `elliptical_constructions` — omitted repeated words in parallel structures
- `conjunction_usage` — correlative conjunctions (both/and, either/or, neither/nor,
  not only/but also) must join grammatically parallel elements

#### `pronoun` focus keys
- `pronoun_case` — who/whom, I/me, he/him in compound constructions
- `pronoun_clarity` — pronoun with ambiguous antecedent

#### `expression_of_ideas` focus keys
- `redundancy_concision` — eliminate wordy or redundant phrasing
- `precision_word_choice` — choose the most precise word for the context
- `register_style_consistency` — avoid mixing formal/informal tone
- `logical_relationships` — choose conjunction or phrase that best reflects
  the logical connection between ideas
- `emphasis_meaning_shifts` — word order or phrasing that shifts meaning
- `data_interpretation_claims` — claim must accurately reflect table or graph
- `transition_logic` — transition word must match the direction of the argument

### 2.2 Missing-From-Taxonomy Grammar Types (Propose Amendment)

The following grammar types appear in official SAT prep materials and in
released tests but do not map cleanly to existing focus keys. When
encountered, use the amendment process and propose the key below.

| Grammar type                   | Proposed focus key             | Parent role key   |
| ------------------------------ | ------------------------------ | ----------------- |
| Adjective vs. adverb           | `adjective_adverb_distinction` | `modifier`        |
| Illogical comparison (unlike things) | `illogical_comparison`   | `modifier`        |
| Commonly confused word pairs   | `commonly_confused_words`      | `expression_of_ideas` |
| Subjunctive mood               | `subjunctive_mood`             | `verb_form`       |

#### Adjective vs. Adverb

Rule: adjectives modify nouns; adverbs modify verbs, adjectives, and other
adverbs. Students frequently choose an adjective where an adverb is required
(e.g., "ran quick" instead of "ran quickly") or an adverb where an adjective
is required (e.g., "felt badly" instead of "felt bad" when the verb is a
linking verb).

Key traps:
- Linking verbs (feel, seem, appear, taste, smell) take adjective complements
- Flat adverbs (fast, hard, late) look like adjectives
- Comparative forms (more carefully vs. more careful) can be hard to place

#### Illogical Comparisons

Rule: only compare grammatically and logically parallel things.

Common errors:
- Comparing a thing to a person: "Her writing is better than Mark" (should be
  "than Mark's" or "than his")
- Comparing a thing to itself: "The city is larger than any city" (should be
  "any other city")
- Missing possessive: "The team's results are better than the opponent" (should
  be "the opponent's")

Key traps: all four options often sound natural; the error is structural.

#### Commonly Confused Word Pairs

Pairs tested on released SATs:
- affect (verb) / effect (noun/verb)
- accept (receive) / except (excluding)
- between (two) / among (three or more)
- fewer (countable) / less (uncountable)
- imply (speaker) / infer (listener)
- principle (rule) / principal (main, or administrator)
- precede (come before) / proceed (continue)
- complement (complete) / compliment (praise)

These are classified under `precision_word_choice` when the meaning is tested,
or `commonly_confused_words` (proposed key) when the form itself is tested.

#### Subjunctive Mood

Rule: use the subjunctive in:
- Hypothetical or counterfactual conditions: "If she were here..."
- Wishes: "I wish he were able to..."
- Recommendations or demands: "The committee recommended that he be removed."
- After phrases like "as though" and "as if": "She acted as though it were true."

Key traps: "was" instead of "were" in hypotheticals; indicative after "that"
clauses of recommendation ("recommended that he was" instead of "be").

### 2.3 Grammar Role to Focus Mapping Enforcement

The agent must never emit a `grammar_focus_key` that does not belong to the
declared `grammar_role_key`. See the mapping table in the source V3 document
section 17.1 for the full enforcement table.

### 2.4 SEC vs. Expression of Ideas Triage

| Deciding factor                                    | Classification             |
| -------------------------------------------------- | -------------------------- |
| Question is about grammar, agreement, or punctuation | `conventions_grammar`     |
| Question is about transition, concision, or rhetoric | `expression_of_ideas`     |
| Both apply                                         | Classify by primary eliminating rule; store secondary in `secondary_grammar_focus_keys` |

---

## 3. Frequency Guidance

Prioritize high-frequency rules in practice set composition.

| Frequency band | Focus keys                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| `very_high`    | `punctuation_comma`, `subject_verb_agreement`                                                                |
| `high`         | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation`   |
| `medium`       | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure`, `transition_logic`, `possessive_contraction` |
| `low`          | `voice_active_passive`, `logical_predication`, `hyphen_usage`, `quotation_punctuation`, `pronoun_case`, `comparative_structures`, `subjunctive_mood` |
| `very_low`     | `affirmative_agreement`, `negation`, `noun_countability`, `determiners_articles`, `elliptical_constructions`, `conjunction_usage` |

Do not generate a `very_low` frequency item without explicit justification.

---

## 4. Syntactic Trap Taxonomy

The syntactic trap describes the difficulty mechanism — how the question
misleads — not the rule being tested.

| Trap key                          | What it does                                                                                      | Most common grammar focus |
| --------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------- |
| `nearest_noun_attraction`         | A noun near the verb has different number from the true subject                                   | `subject_verb_agreement`  |
| `interruption_breaks_subject_verb`| A parenthetical phrase separates subject and verb, obscuring agreement                           | `subject_verb_agreement`, `sentence_boundary` |
| `garden_path`                     | The sentence begins in a way that leads the reader to mis-parse the structure                    | `sentence_boundary`, `modifier_placement` |
| `early_clause_anchor`             | The first clause sets up a tense expectation that the correct answer resists                     | `verb_tense_consistency`  |
| `nominalization_obscures_subject` | A nominalized verb form (e.g., "The discovery of X") hides the true subject                      | `subject_verb_agreement`  |
| `long_distance_dependency`        | A pronoun or verb is separated from its antecedent or subject by multiple clauses               | `pronoun_antecedent_agreement`, `subject_verb_agreement` |
| `pronoun_ambiguity`               | Two or more nouns could be the pronoun's antecedent                                              | `pronoun_clarity`         |
| `scope_of_negation`               | Negation can scope over two different parts of the sentence                                      | `negation`                |
| `modifier_attachment_ambiguity`   | A modifier could attach to two different nouns                                                   | `modifier_placement`      |
| `presupposition_trap`             | The sentence structure implies a fact that is not stated                                         | `logical_predication`     |
| `temporal_sequence_ambiguity`     | Multiple time markers create competing tense expectations                                        | `verb_tense_consistency`  |
| `parallel_shape_bias`             | Items look parallel because they share surface structure, masking a deeper form mismatch         | `parallel_structure`      |
| `multiple`                        | More than one trap operates simultaneously                                                       | Any                       |
| `none`                            | No syntactic trap; difficulty comes from rule knowledge alone                                    | Any                       |

---

## 5. Passage Construction Rules by Grammar Focus

Each grammar focus requires the passage to embed the rule in a specific way.

### Subject-Verb Agreement

- Use a singular collective, abstract, or inverted subject.
- Insert a plural prepositional phrase or relative clause between subject and verb.
- Template: "The [singular collective noun] of [plural noun], [relative clause],
  ______ [verb phrase]."
- Example: "The committee of senior researchers, who have studied this phenomenon
  for decades, ______ its findings annually."

### Verb Tense Consistency

- Open the sentence with a strong time marker (last year, in 1984, by the time).
- Include a second time marker or temporal clause that could pull the tense in
  a different direction.
- Template: "[Time marker], [subject] [establishes action], and the [related
  noun] ______ [result]."

### Modifier Placement / Dangling Modifier

- Open with a participial phrase whose logical subject differs from the
  grammatical subject.
- Template: "[Participial phrase], [noun that did NOT do the action] ______."
- Example: "After analyzing the data, ______ revised to reflect the
  new findings."

### Punctuation — Semicolon

- Use two closely related independent clauses.
- Place a conjunctive adverb (however, therefore, moreover, thus) in the
  second clause if targeting `conjunctive_adverb_usage`.
- Template: "[IC1] ______ [transition], [IC2]."

### Apostrophe / Possessive

- Use a possessive where the noun ends in s (plural possessive trap).
- Or use a possessive pronoun next to a contraction homophone.
- Template: "The [plural noun] ______ [relationship to something] were
  recognized at the ceremony."

### Parallel Structure

- Create a list of three where two items share form and one breaks form.
- Or use a correlative conjunction (not only...but also) where both elements
  must match.
- Template: "The program teaches students to [verb], [verb], and ______."

### Pronoun Case

- Use a compound subject or object so the case of the individual pronoun is
  less obvious.
- Template: "The award was presented to [name] and ______ for outstanding work."

### Comparative Structures / Illogical Comparisons

- Create a comparison where the two things being compared are different types
  unless the correct answer adds the possessive or "other."
- Template: "The [noun] of [subject] was greater than ______."

### Adjective vs. Adverb

- Use a linking verb followed by a blank where both adjective and adverb
  forms are common but only one is correct.
- Or use a verb modified by an adverb where the adjective form feels natural
  in speech.
- Template: "The results were [surprisingly / more surprisingly / surprising /
  more surprising] consistent."

### Subjunctive Mood

- Use a conditional, wish, or recommendation clause where subjunctive is
  required.
- Template: "The review board recommended that the proposal ______ before
  publication."

### Transition Logic

- Write two clauses with a specific logical relationship (contrast, cause,
  continuation) and present four transition words — one correct, three from
  different logical relationships.
- Template: "[Statement A] ______; [statement B that [contrasts / elaborates /
  results from] A]."

---

## 6. Distractor Heuristics by Grammar Focus

Each distractor family below gives the three required distractors for the
most common version of that focus key. Primary trap distractor comes first.

### Subject-Verb Agreement

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Plural verb, attracted by nearest plural noun | `nearest_noun_reflex` |
| 2 | Singular verb with wrong tense (often present perfect) | `formal_word_bias` |
| 3 | Progressive or compound auxiliary that agrees in form but not convention | `grammar_fit_only` |

### Verb Tense Consistency

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Tense matching nearest time-marker clause, not overall passage register | `tense_proximity_pull` |
| 2 | Present perfect (sounds formal and correct) | `formal_word_bias` |
| 3 | Conditional or future (sounds appropriately hedged) | `grammar_fit_only` |

### Semicolon Use

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comma alone (comma splice) | `comma_fix_illusion` |
| 2 | Colon (looks sophisticated; wrong type) | `punctuation_intimidation` |
| 3 | Period (valid but severs the relationship; precision_score: 2) | `scope_blindness` |

### Apostrophe Use

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Plural without apostrophe | `ear_test_pass` |
| 2 | Singular possessive when plural possessive required | `nearest_noun_reflex` |
| 3 | Possessive/contraction homophone (its/it's, whose/who's) | `possessive_contraction_confusion` |

### Modifier Placement

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Passive construction that hides the dangling modifier | `modifier_hitchhike` |
| 2 | Modifier placed next to semantically related but grammatically wrong noun | `modifier_hitchhike` |
| 3 | Restructured clause that sounds natural but preserves the dangle | `ear_test_pass` |

### Parallel Structure

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Different form that sounds natural (gerund for infinitive or vice versa) | `parallel_shape_bias` |
| 2 | Nominalization (sounds formal and educated) | `formal_word_bias` |
| 3 | Prepositional phrase that reads naturally but breaks the established pattern | `grammar_fit_only` |

### Pronoun Case

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Subject pronoun in object position (especially in compound; "between you and I") | `ear_test_pass` |
| 2 | Reflexive pronoun (sounds more precise or emphatic) | `formal_word_bias` |
| 3 | Possessive pronoun where object pronoun is required | `idiom_memory_pull` |

### Comparative Structures / Illogical Comparisons

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comparison between unlike things (noun compared to person) | `scope_blindness` |
| 2 | Comparison omitting "other" ("more than any city" vs. "any other city") | `false_precision` |
| 3 | Comparison with doubled comparative ("more better") | `grammar_fit_only` |

### Adjective vs. Adverb

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Adjective where adverb required (sounds natural in speech) | `ear_test_pass` |
| 2 | Comparative adverb where simple adverb is sufficient | `false_precision` |
| 3 | Adverb attached to wrong element in sentence | `modifier_hitchhike` |

### Subjunctive Mood

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Indicative "was" where subjunctive "were" required | `ear_test_pass` |
| 2 | Past tense form that sounds naturally hypothetical | `tense_proximity_pull` |
| 3 | Modal construction (would, could) that sounds appropriately tentative | `formal_word_bias` |

### Transition Logic

| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Transition with opposite logical direction (contrast when agreement needed) | `transition_assumption` |
| 2 | Formal transition that sounds authoritative regardless of direction | `register_confusion` |
| 3 | Additive transition that is plausible but weakens the relationship | `scope_blindness` |

---

## 7. No-Change Questions

Approximately 20% of official SAT grammar questions present the original
sentence text as the correct answer (no change needed).

Rules for generating no-change items:

1. Write a passage that is grammatically correct at the blank location.
2. Make option A the original correct text.
3. Distractors B, C, D must each introduce a different, plausible grammar error.
4. Use neutral stem wording: do not imply an error exists.
5. The `explanation_full` must explicitly state why the original text needs no
   correction.

No-change distractor requirements:

| Position | Must introduce... |
| -------- | ----------------- |
| B | Primary grammar error for the target focus key |
| C | Different grammar error (secondary focus key) |
| D | Plausible-sounding error that violates a common rule |

---

## 8. Multi-Error and Ambiguous Questions

When multiple grammar rules apply across the four options:

1. Classify the primary tested rule in `grammar_focus_key`.
2. Store secondary rules in `secondary_grammar_focus_keys`.
3. Store the specific error for each wrong option in `option_error_focus_key`.
4. Note ambiguity in `review.review_notes`.

Do not label the whole question by a distractor-only error.

---

## 9. Special Cases

### Passage-Level Tense Register

For all verb-form questions, determine the passage tense register:

- `narrative_past` — literary or personal narrative
- `scientific_general_present` — biological/physical facts
- `historical_past` — events completed in the past
- `study_procedure_past` — research methodology
- `established_finding_present` — accepted scientific conclusions
- `mixed_with_explicit_shift` — passage has a documented tense shift

The correct answer must match the established register unless the item
specifically tests a shift.

### Correlative Conjunctions

Correlative pairs require grammatically parallel elements on both sides:

- both [X] and [Y] — X and Y must be the same form
- either [X] or [Y] — same form
- neither [X] nor [Y] — same form
- not only [X] but also [Y] — same form

Distractor design: make options differ only in whether the form after the
second conjunction matches the first. All options should be plausible English.

---

## 10. Grammar Validation Checklist

Before accepting a grammar item:

- [ ] `grammar_focus_key` belongs to declared `grammar_role_key`
- [ ] Exactly four options
- [ ] Exactly one correct option
- [ ] No two distractors share the same `option_error_focus_key`
- [ ] At least one distractor targets the declared `syntactic_trap_key`
- [ ] All options are grammatically plausible English sentences
- [ ] No option eliminable by ear-test alone
- [ ] Correct option contains no grammar error
- [ ] Passage is in formal academic register
- [ ] `student_failure_mode_key` assigned to every distractor
- [ ] `disambiguation_rule_applied` present if any classification conflict exists
- [ ] `explanation_full` explains every wrong option by label
- [ ] No-change metadata populated when applicable
- [ ] Tense register metadata populated for all verb-form items

---

## 11. Source Derivation

Primary inputs:

- `rules_agent_dsat_grammar_ingestion_generation_v3.md` sections 3–13, 17–20
- Research from College Board DSAT test specifications
- Khan Academy SAT Standard English Conventions category structure (Boundaries;
  Form, Structure, and Sense)
- PrepScholar, Magoosh, and Princeton Review DSAT grammar rule inventories

Additional grammar types added in this revision based on research gaps:

- `adjective_adverb_distinction` (proposed)
- `illogical_comparison` (proposed)
- `commonly_confused_words` (proposed)
- `subjunctive_mood` (added to `verb_form` family)
- `correlative_conjunction` patterns (added to `parallel_structure` family)
