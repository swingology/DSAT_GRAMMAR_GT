# rules_agent_dsat_grammar_ingestion_generation_v3_1.md

## Purpose

This file is the v3.1 addendum to
`rules_agent_dsat_grammar_ingestion_generation_v3.md`.

It adds only what is missing or underspecified after cross-referencing the v3
grammar file against College Board official answer explanations for PT4–PT11
(documented in `CB_ANSWERS_QUESTIONS_ANALYSIS.md`).

Load order: v3 baseline → this file.

All additions are non-breaking extensions. No existing key is renamed or
removed. New keys proposed here are production-ready unless marked
`proposed_only`.

---

## 1. New Punctuation Focus Keys

The current v3 `punctuation` role is missing two high-frequency official
patterns and has insufficient specificity for the appositive punctuation key.

### 1.1 Add `unnecessary_internal_punctuation`

**Gap source:** PT4 M2 Q20 (no punctuation between preposition and complement),
PT5 M2 Q19 (no punctuation between subject and verb), PT6 M1 Q20 (no
punctuation between verb and object), PT7 M2 Q21 (same), PT9 M2 Q22 (same),
PT11 M2 Q21 (same).

**Add to §6.6 Punctuation focus keys:**

- `unnecessary_internal_punctuation`

**Rule definition:**

> No punctuation may appear inside a required syntactic unit. The most common
> units the SAT tests are: subject–verb, verb–object, verb–complement,
> preposition–complement, and integrated relative clause. Inserting a comma,
> dash, or colon inside any of these units is always wrong.

**Passage construction rules (add to §20.3):**

```
Target: unnecessary_internal_punctuation

Insert a comma or dash at one of these five positions:
  1. between subject and main verb
  2. between transitive verb and its direct object
  3. between verb and subject complement (linking verb structure)
  4. between preposition and its noun complement
  5. inside an integrated relative clause before the verb

Wrong options always add punctuation at the forbidden location.
Correct option has no punctuation at that location.
```

**Distractor table (add to §20.4):**

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma between subject and verb | `punctuation_style_bias` |
| 2 | Dash between subject and verb | `formal_register_match` |
| 3 | Comma between verb and object/complement | `grammar_fit_only` |

**Add to §17.10 Frequency table:**

| Frequency band | Add to existing entry |
|---|---|
| `medium` | `unnecessary_internal_punctuation` |

**Add to §20.6 validation checklist:** If `grammar_focus_key` is
`unnecessary_internal_punctuation`, confirm the correct option has no
punctuation at the target syntactic boundary.

---

### 1.2 Add `end_punctuation_question_statement`

**Gap source:** PT6 M2 Q19 (question mark for coordinated direct questions),
PT11 M1 Q19 (period for declarative sentence ending in indirect question),
PT11 M2 Q19 (same).

**Add to §6.6 Punctuation focus keys:**

- `end_punctuation_question_statement`

**Rule definition:**

> A sentence that contains an indirect (reported) question ends with a period,
> not a question mark, because the sentence as a whole is declarative. A
> sentence consisting of two coordinated direct questions requires a question
> mark. The test distinguishes these two cases.

**Passage construction rules (add to §20.3):**

```
Target: end_punctuation_question_statement

Variant A — indirect question embedded in declarative:
  Use a main clause like "The researchers wondered / asked / considered"
  followed by a subordinate question clause. End with period.
  Wrong options offer a question mark or no end punctuation.

Variant B — coordinated direct questions:
  Use two question clauses joined by "or" or "and."
  End with a single question mark.
  Wrong options offer a period, a comma, or a question mark after each clause.
```

**Distractor table (add to §20.4):**

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Question mark on an indirect question | `surface_similarity_bias` (looks like a question) |
| 2 | Comma after the main clause, no end mark | `punctuation_style_bias` |
| 3 | Period on a coordinated direct question | `formal_register_match` |

**Add to §17.10 Frequency table:**

| Frequency band | Add to existing entry |
|---|---|
| `medium` | `end_punctuation_question_statement` |

---

### 1.3 Extend `appositive_punctuation` with two sub-patterns

**Gap source:** PT5 M1 Q25 (no punctuation between title/role noun and proper
name), PT8 M1 Q21 (coordinated restrictive appositive, no punctuation), PT9 M1
Q23 (same as PT5), PT9 M2 Q24 (restrictive appositive, no punctuation).

The current `appositive_punctuation` key does not distinguish the
**restrictive appositive** (no punctuation) from the **nonrestrictive
appositive** (commas or dashes). Add the following sub-pattern notes to
§20.3 under `appositive_punctuation`.

**Sub-pattern A — restrictive appositive:**

> When an appositive uniquely identifies its antecedent (because removing it
> would change the referent), no punctuation surrounds it.
> Example: "the chemical compound aluminum oxide" — "aluminum oxide" is a
> restrictive appositive, no commas.

**Sub-pattern B — title/role noun before proper name:**

> When a title or professional role immediately precedes a proper name and
> functions as a restrictive identifier, no comma separates them.
> Example: "plant cell biologist Yuree Lee" — no comma between "biologist"
> and "Yuree Lee."

**Sub-pattern C — coordinated restrictive appositive:**

> When two restrictive appositives are joined by "and" and together identify
> the antecedent, no punctuation surrounds either.
> Example: "the writer and scholar James Baldwin" — no commas around
> "writer and scholar."

**Distractor pattern additions for these sub-patterns:**

| Distractor | Error | Plausibility source |
|---|---|---|
| 1 | Comma before proper name after title/role | `punctuation_style_bias` |
| 2 | Commas around restrictive appositive (treating as nonrestrictive) | `grammar_fit_only` |
| 3 | Dash before restrictive appositive | `formal_register_match` |

**Add to §17.10 Frequency table:**

Increase `appositive_punctuation` from `high` to `very_high` because the
restrictive/nonrestrictive distinction appears in every official module
reviewed.

---

## 2. New Verb Form Generation Patterns

The current v3 `verb_form` role handles tense, finite/nonfinite, and voice
but lacks explicit named generation patterns for three high-frequency College
Board constructions identified in PT4–PT11.

### 2.1 Add `finite_verb_in_relative_clause` generation pattern

**Gap source:** PT9 M1 Q19 (finite verb required in relative clause).

**Add to §20.3 Passage generation rules by grammar focus:**

```
Target: finite_verb_in_relative_clause

Construct a sentence where a relative clause (introduced by "which," "that,"
or "who") requires a finite verb. Generate wrong options that substitute a
nonfinite participle (-ing or past participle without auxiliary) or an
infinitive for the required finite verb.

Template:
  [Noun phrase], which ______ [object or complement], [main verb phrase].
  [Noun phrase] that ______ [object or complement] is [description].

Correct option: finite verb form agreeing with the relative pronoun's antecedent.
Wrong options: nonfinite -ing participle, bare past participle without
  auxiliary, infinitive.
```

**Classification:** `grammar_role_key: "verb_form"`,
`grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"` (the relative clause opener makes a
participle look grammatical on first pass).

---

### 2.2 Add `finite_verb_in_main_clause` generation pattern

**Gap source:** PT5 M1 Q21 (finite verb required in main clause), PT5 M2 Q18
(same), PT8 M2 Q19 (same), PT8 M2 Q22 (same).

**Add to §20.3:**

```
Target: finite_verb_in_main_clause

Construct a sentence where the main clause requires a finite verb but the
wrong options offer nonfinite forms. Common trigger: an opening subordinate
clause or participial phrase that tempts the writer to continue with another
nonfinite form.

Template:
  [Opening subordinate clause or participial phrase], [Subject] ______ [object].

Correct option: finite present or past tense verb.
Wrong options: -ing participle, past participle without auxiliary, infinitive.
```

**Classification:** `grammar_role_key: "verb_form"`,
`grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "garden_path"`.

---

### 2.3 Add `modal_plus_plain_form` generation pattern

**Gap source:** PT8 M1 Q20 (modal "would" requires nonfinite plain-form verb).

**Add to §20.3:**

```
Target: modal_plus_plain_form

Construct a sentence where a modal auxiliary (would, could, should, might,
must, will, can, shall) governs the main verb. Wrong options offer inflected
present (-s), past (-ed), or continuous (-ing) forms after the modal.

Template:
  [Subject] would/could/should/might ______ [object or complement].

Correct option: plain (base) form of the verb.
Wrong options: third-person singular inflected form, past tense form,
  continuous form.
```

**Classification:** `grammar_role_key: "verb_form"`,
`grammar_focus_key: "verb_form"`,
`syntactic_trap_key: "none"`.

**Add to §17.10 Frequency table:**

The `finite_verb_in_main_clause` and `modal_plus_plain_form` patterns appear
multiple times across PT5–PT11 and should be treated as `medium` frequency
alongside the existing `verb_form` entries.

---

## 3. New Pronoun Generation Pattern

### 3.1 Add `singular_event_reference` pattern

**Gap source:** PT5 M1 Q20 (singular pronoun "this" referring to an entire
preceding event or fact, not a noun).

**Add to §20.3 under `pronoun_antecedent_agreement`:**

```
Target: singular_event_reference

Construct a sentence where the pronoun refers back to an entire preceding
event, fact, or clause (not a single noun antecedent). The pronoun must be
singular ("this," "it," or "that"). Wrong options offer plural pronouns
("these," "they") or vague pronouns that introduce agreement problems.

Template:
  [Complete prior event or fact stated as a sentence or clause].
  ______ [effect, significance, or consequence].

Correct pronoun: singular "this," "it," or "that."
Wrong options: plural pronoun, ambiguous pronoun, pronoun with wrong case.
```

**Annotation note:** When classifying an official item of this type, use
`grammar_role_key: "pronoun"`, `grammar_focus_key: "pronoun_antecedent_agreement"`,
and add to `review_notes`: "antecedent is a full clause/event, not a noun."

---

## 4. New Tense Register Key

### 4.1 Add `literary_present` to `passage_tense_register_key`

**Gap source:** PT10 M1 Q24 (literary present tense for discussing events or
patterns inside a literary work).

**Add to §13.1 and §17.6 allowed values for `passage_tense_register_key`:**

- `literary_present`

**Rule definition:**

> When a passage discusses actions, events, or patterns *inside* a literary
> work (novel, poem, play, short story), the convention is to use present
> tense even if the work was written in the past or the discussion itself
> uses past tense for biographical context. Verbs describing what characters
> do, what the text says, or what patterns appear in the work use simple
> present.

**Add to §13.2 expected patterns:**

- `literary_present` → `expected_tense_key: "simple_present"`; applies when
  passage frame is "In the novel / poem / story, [character] ______."
  Wrong options offer past tense or present perfect.

**Add to §20.3 passage generation note for `verb_tense_consistency`:**

```
Literary register variant:
  Frame the passage as a discussion of a named literary work.
  Target verb slot describes a character's action or the text's pattern.
  Correct option: simple present.
  Wrong options: simple past, present perfect, past perfect.
  Classify with passage_tense_register_key: "literary_present".
```

---

## 5. Expression of Ideas — Transition Subtypes

The current v3 `transition_logic` focus key is correct but lacks named
subtypes for specific transition words. Official College Board explanations
always name the logical relationship by the transition word used. The
following additions should be stored as `transition_subtype_key` metadata
alongside `grammar_focus_key: "transition_logic"`.

### 5.1 Add `transition_subtype_key` field

Add to the classification schema for all `transition_logic` items:

```json
{
  "transition_subtype_key": "causal_chain"
}
```

This field is optional for annotation (legacy items need not be re-annotated)
but mandatory for generation.

### 5.2 Approved `transition_subtype_key` values

The following table consolidates all subtypes observed across PT4–PT11 that
were either missing from v3 or listed as "add subtype" in the coverage audit.

| Key | Canonical transition word(s) | Logical relationship |
|---|---|---|
| `sequence_final_event` | `finally`, `last`, `ultimately` (sequential) | The described step is the last in an ordered process |
| `contrast_refutation` | `however`, `but`, `yet`, `still` | Refutes or contradicts the prior claim |
| `addition` | `additionally`, `furthermore`, `also`, `moreover` | Adds another supporting point |
| `result_consequence` | `therefore`, `thus`, `hence`, `as a result`, `consequently`, `for this reason`, `accordingly`, `as such` | The second statement follows causally from the first |
| `chronology` | `previously`, `later`, `then`, `next`, `afterward`, `subsequently` | Places events or steps in time order |
| `alternative` | `instead`, `alternatively`, `rather`, `otherwise` | Substitutes one option for another |
| `emphasis_support` | `indeed`, `in fact`, `certainly` | Reinforces or intensifies the prior claim |
| `causal_chain` | `in turn` | The second event follows directly from the first as part of a sequence of causes |
| `specificity_elaboration` | `specifically`, `in particular`, `namely` | Narrows or details a general claim |
| `purpose_action` | `to that end`, `to this end`, `for this purpose` | Describes an action taken to fulfill the preceding goal |
| `frequency_difference` | `more often`, `less often` | Emphasizes a relative frequency difference |
| `simultaneity` | `meanwhile`, `at the same time` | Two events or processes occur concurrently |
| `similarity` | `similarly`, `likewise` | The second claim parallels the first |
| `appropriateness` | `fittingly`, `aptly`, `appropriately` | The second statement is well-suited to the prior context |
| `change_over_time` | `increasingly`, `over time`, `progressively` | A trend or direction is described as developing |
| `exception` | `though`, `although`, `even so`, `nevertheless` (within a statement) | Marks a qualification or exception to the prior claim |
| `final_realization` | `ultimately` (non-sequential use) | Describes what something comes down to or reveals in the end |
| `converse_opposite` | `conversely`, `on the other hand`, `by contrast`, `on the contrary` | States the opposite tendency to the prior claim |
| `present_continuation` | `currently`, `today`, `now`, `at present` | Signals a shift from historical context to the present state |
| `direct_refutation` | `on the contrary` | Directly disputes an assumption or claim |
| `logical_consequence` | `as such`, `therefore`, `thus` | Logical inference from the preceding statement |
| `concession_qualification` | `admittedly`, `granted`, `to be sure` | Concedes a point before a counter-argument |
| `example` | `for example`, `for instance`, `to illustrate` | Provides a specific instance of a general claim |

### 5.3 Wrong-option annotation requirement

For every transition distractor, add a `transition_subtype_key` to the
option-level annotation describing which wrong relationship the distractor
signals. This mirrors the existing requirement for `option_error_focus_key`.

Example:

```json
{
  "option_label": "B",
  "option_text": "However,",
  "is_correct": false,
  "distractor_type_key": "transition_mismatch",
  "transition_subtype_key": "contrast_refutation",
  "why_wrong": "The relationship is addition, not contrast."
}
```

### 5.4 Generation requirement

When generating a transition item, the generation profile must specify both
the correct subtype and the wrong subtype for each distractor:

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

---

## 6. Expression of Ideas — Notes Synthesis Subtypes

The current `choose_best_notes_synthesis` stem type is handled as a single
bucket. Official CB explanations for PT4–PT11 show that every notes synthesis
item has a specific rhetorical goal and a specific audience assumption.
Generation without these controls produces items that do not match official
behavior.

### 6.1 Add `synthesis_goal_key`, `audience_knowledge_key`, and
`required_content_key` fields

These fields are mandatory for generated notes synthesis items and
recommended for annotated items.

```json
{
  "synthesis_goal_key": "emphasize_similarity",
  "audience_knowledge_key": "audience_unfamiliar",
  "required_content_key": "comparison_needed"
}
```

### 6.2 Approved `synthesis_goal_key` values

Derived from all notes synthesis items observed in PT4–PT11:

| Key | Description |
|---|---|
| `emphasize_similarity` | Highlight that two things share a feature |
| `emphasize_difference` | Highlight a contrast between two things |
| `explain_advantage` | State why one option is better than another |
| `explain_mechanism` | Describe how something works |
| `present_research` | Summarize a study for a reader unfamiliar with it |
| `present_theory` | Introduce a theory to an unfamiliar audience |
| `introduce_work` | Introduce a named literary or artistic work |
| `describe_work` | Describe what a work does or is about |
| `emphasize_achievement` | Highlight a named person's accomplishment |
| `make_generalization` | Draw a broad conclusion from the notes |
| `contrast_quantities` | Compare two numerical or measured values |
| `compare_measurements` | Compare lengths, sizes, masses, or other units |
| `emphasize_sample` | Highlight a specific representative example |
| `identify_category` | Name the classification or group something belongs to |
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
| `explain_technique_advantage` | Describe why a specific technique is useful |
| `explain_misconception_naming` | Explain why something is incorrectly named |
| `challenge_with_quotation` | Use a quotation from notes to dispute an explanation |
| `present_study_overview` | Give a high-level summary of a study's design and result |
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

### 6.3 Approved `audience_knowledge_key` values

| Key | When to use |
|---|---|
| `audience_familiar` | The target sentence should assume the reader already knows a named source, author, or context |
| `audience_unfamiliar` | The target sentence must provide identifying context (author name, work title, field, year) for a reader who does not know it |
| `not_specified` | Audience assumption is not the distinguishing factor for this item |

### 6.4 Approved `required_content_key` values

| Key | What the correct sentence must include |
|---|---|
| `comparison_needed` | At least one explicit comparison (more/less/similar/different) |
| `measurement_values_needed` | At least one specific number, unit, or measured value |
| `result_needed` | The outcome or finding of the study or event |
| `title_and_content_needed` | Both the title of a work and a description of it |
| `achievement_needed` | A statement of what a person accomplished |
| `category_label_needed` | The name of the classification group |
| `sample_location_needed` | The specific example or location highlighted |
| `profession_label_needed` | The person's job title or field |
| `setting_needed` | The place or time setting of a work |
| `year_needed` | A specific year or date |
| `duration_needed` | A length of time |
| `distance_needed` | A measured distance |
| `author_identity_needed` | The real name of an author who used a pseudonym |
| `mechanism_needed` | A description of the causal or functional process |
| `structural_roles_needed` | Names of the structural or formal elements being compared |
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

### 6.5 Wrong-option annotation requirement for notes synthesis

For every notes synthesis distractor, annotate what it gets wrong using one
of these four failure modes:

```json
{
  "synthesis_distractor_failure": "wrong_goal | omits_required_content | adds_background_audience_does_not_need | correct_topic_wrong_comparison"
}
```

| Failure | Description |
|---|---|
| `wrong_goal` | The sentence does something other than what the stem requests |
| `omits_required_content` | The sentence is on-topic but leaves out a required content element |
| `adds_background_audience_does_not_need` | Provides context the audience already has, or provides irrelevant background |
| `correct_topic_wrong_comparison` | Mentions the right subjects but states the wrong comparison, direction, or scope |

### 6.6 Generation requirement for notes synthesis

Generation profiles for notes synthesis must include:

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

---

## 7. Module Format Field

### 7.1 Add `test_format_key` to generation requests

**Gap source:** CB_ANSWERS_QUESTIONS_ANALYSIS.md §Recommended Rule Additions
§1 (Paper-Accommodation Module Blueprint). PT4–PT11 verbal modules have 33
questions each; the digital adaptive app default is 27. Generation without
a format flag will produce modules with the wrong length and wrong
domain-boundary positions.

**Add to §20.1 Generation Input Specification:**

```json
{
  "generation_request": {
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital"
  }
}
```

**Approved `test_format_key` values:**

| Value | Module length | When to use |
|---|---|---|
| `digital_app_adaptive` | 27 questions | Default; standard Bluebook adaptive digital SAT |
| `nondigital_linear_accommodation` | 33 questions | Paper accommodation format; PT4–PT11 source tests |

**Approved `source_stats_format` values:**

| Value | Description |
|---|---|
| `official_digital` | Position statistics derived from Bluebook adaptive modules |
| `official_nondigital_linear` | Position statistics derived from PT4–PT11 paper accommodation modules |

**Generation enforcement rule:**

When `test_format_key` is `nondigital_linear_accommodation`, the module
blueprint must use 33 questions and the following domain-band ranges
(derived from PT4–PT11 observation):

```
Reading/Craft/Information: Q1–Q18 (±1)
Standard English Conventions: Q19–Q26 (±1; may start as late as Q18 in M2)
Transitions: Q27–Q30 (variable; can be as few as 1 or as many as 5)
Notes Synthesis: Q30–Q33 (variable start; always ends at Q33)
```

When `test_format_key` is `digital_app_adaptive`, use the existing 27-question
blueprint and digital-format statistics.

**Validation rule:** The validator must reject any 33-question module
generated with `test_format_key: "digital_app_adaptive"` and any 27-question
module generated with `test_format_key: "nondigital_linear_accommodation"`.

---

## 8. Grammar-Specific Student Failure Mode Keys

The current v3 §21.3 student failure mode keys are oriented toward reading
domains. Add the following grammar-specific values to the approved list.

**Add to §21.3 approved `student_failure_mode_key` values:**

| Key | When to use |
|---|---|
| `internal_unit_punctuation_insertion` | Student inserts a comma or dash inside a required syntactic unit (subject–verb, verb–object, preposition–complement) |
| `declarative_question_confusion` | Student applies a question mark to a sentence that contains an embedded indirect question but is itself declarative |
| `restrictive_appositive_comma_insertion` | Student adds commas around a restrictive appositive that requires none |
| `title_name_comma_insertion` | Student inserts a comma between a title/role noun and the proper name that follows it |
| `nonfinite_for_finite` | Student chooses a participle or infinitive where a finite verb is required (main clause or relative clause) |
| `inflected_after_modal` | Student chooses a past-tense, third-person-singular, or continuous form after a modal auxiliary |
| `plural_pronoun_for_clause_antecedent` | Student chooses a plural pronoun when the antecedent is an entire preceding clause or event |
| `past_tense_for_literary_present` | Student uses simple past when discussing events inside a literary work, which conventionally uses simple present |
| `transition_wrong_direction` | Student chooses a transition word that signals the opposite logical relationship (e.g., "however" for a result, "therefore" for a contrast) |
| `notes_synthesis_wrong_goal` | Student chooses a sentence that addresses the right topic but performs a different rhetorical action than the stem requires |
| `notes_synthesis_audience_mismatch` | Student chooses a sentence that is appropriate for a familiar audience when the stem requires a sentence for an unfamiliar audience, or vice versa |

---

## 9. Updated §6.6 Punctuation Focus Key List (complete replacement)

Replace the §6.6 list in v3 with this complete list that includes the two
new keys from §1 of this file:

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`
- `unnecessary_internal_punctuation` *(new in v3.1)*
- `end_punctuation_question_statement` *(new in v3.1)*

---

## 10. Updated §17.1 `grammar_role_key` → `grammar_focus_key` Mapping (partial update)

Add the two new punctuation focus keys to the `punctuation` row:

| `grammar_role_key` | Add to allowed `grammar_focus_key` values |
|---|---|
| `punctuation` | `unnecessary_internal_punctuation`, `end_punctuation_question_statement` |

---

## 11. Updated §17.10 Frequency Table (partial update)

| Frequency band | Add these keys |
|---|---|
| `medium` | `unnecessary_internal_punctuation`, `end_punctuation_question_statement`, `finite_verb_in_main_clause`, `modal_plus_plain_form` |
| `low` | `finite_verb_in_relative_clause`, `singular_event_reference`, `literary_present` (tense register) |

---

## 12. Updated §22 Passage Architecture Templates (additions)

Add to the approved `passage_architecture_key` values in §22:

- `experiment_hypothesis_control_result` — passage describes a hypothesis,
  an experimental group, a control/baseline, and an observed outcome. Enables
  support, weaken, inference, and quantitative items that test whether the
  student correctly identifies which group provides the relevant evidence.

- `indirect_effect_mediation` — passage describes an initial condition, an
  intermediate variable, and a final outcome, with the claim that the effect
  operates through the intermediate variable.

- `alternative_explanation_ruled_out` — passage describes an observed change,
  a possible alternative cause, a control or finding that eliminates the
  alternative, and the remaining explanation.

- `mechanism_manipulation_test` — passage describes a phenomenon, a candidate
  mechanism, an experimental manipulation, and the result, testing whether the
  student can identify what the manipulation reveals about the mechanism.

- `studied_subgroup_generalization_limit` — passage provides evidence about a
  well-studied subgroup and explicitly warns that the evidence may not
  generalize to the broader population or category.

*(These architecture keys are also relevant to the reading module but are
listed here because the v3 grammar file owns the `passage_architecture_key`
vocabulary in §22.)*

---

## 13. Validator Checklist Additions

Add to §20.6 Pre-Output Validation Checklist:

| # | Check | Failure action |
|---|---|---|
| 18 | For `transition_logic` items, `transition_subtype_key` is present in classification and in each option | Add subtype or set `needs_human_review: true` |
| 19 | For `choose_best_notes_synthesis` items, `synthesis_goal_key`, `audience_knowledge_key`, and `required_content_key` are present | Add fields |
| 20 | For generated notes synthesis, `distractor_synthesis_failures` covers all three wrong options | Add missing failure modes |
| 21 | For `unnecessary_internal_punctuation` items, correct option has no punctuation at the target syntactic boundary | Regenerate correct option |
| 22 | For `end_punctuation_question_statement` items, correct option end mark matches sentence type (declarative vs direct question) | Regenerate correct option |
| 23 | For generated modules, `test_format_key` is present and module length matches (27 for digital, 33 for accommodation) | Add field or correct length |
| 24 | For `verb_form` items targeting finite vs nonfinite, generation pattern is one of: `finite_verb_in_relative_clause`, `finite_verb_in_main_clause`, `modal_plus_plain_form` | Reclassify or add pattern note |
| 25 | For `verb_tense_consistency` items in a literary passage, `passage_tense_register_key` is `literary_present` | Update tense register |

---

*Document version: v3.1 — 2026-04-29*
*Addendum to: `rules_agent_dsat_grammar_ingestion_generation_v3.md`*
*Source authority: `CB_ANSWERS_QUESTIONS_ANALYSIS.md` (PT4–PT11 official explanation cross-reference)*
*Domain coverage: Standard English Conventions, Expression of Ideas (Transitions, Notes Synthesis)*
