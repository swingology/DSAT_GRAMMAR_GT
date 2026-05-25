# DSAT Grammar Module v2

## 1. Scope

Load this file after `rules_core_generation.md` when the item belongs to:

- Standard English Conventions
- grammar-adjacent Expression of Ideas
- Transitions, Rhetorical Synthesis, concision, register, precision, or
  data-claim accuracy when the item is handled by the grammar V3 taxonomy

This module owns grammar classification, grammar focus keys, grammar
disambiguation, syntactic traps, grammar option analysis, grammar generation,
and grammar validation.

This module does not own Information and Ideas or Craft and Structure reading
classification. Those domains must use `rules_dsat_reading_module.md`.

Source authority:

- This module reorganizes the proven root grammar source; it does not narrow
  that source.
- The root `rules_agent_dsat_grammar_ingestion_generation_v3.md` and existing
  backend validator behavior remain compatibility references.
- If this module is silent about a proven grammar behavior, preserve the root
  source behavior rather than inventing a new rule.

## 2. Domain Boundary

Use grammar taxonomy when the correct answer is required by:

- grammar
- punctuation
- sentence structure
- agreement
- verb form
- modifier logic
- pronoun logic
- parallel structure
- grammar-adjacent Expression of Ideas

Do not force a reading item into grammar just because the passage contains
grammar-like wording. Classify by the cognitive skill needed to choose the
correct answer.

Expression of Ideas handling:

- If the item tests transition logic, concision, register, rhetorical synthesis,
  precision, emphasis, or data-claim accuracy, classify as Expression of Ideas.
- `grammar_role_key` may be `expression_of_ideas` only when the item is
  grammar-adjacent.
- If Expression of Ideas has no grammar relevance, `grammar_role_key` may be
  null or omitted, but the item still routes through this module rather than the
  reading module.

## 3. Grammar Question Fields

Common grammar-compatible `stem_type_key` values:

- `complete_the_text`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`

Grammar-compatible `stimulus_mode_key` values for ingestion:

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `notes_bullets`
- `prose_plus_table`
- `prose_plus_graph`
- `poem`

Recommended grammar generation modes:

- `sentence_only`
- `passage_excerpt`
- `notes_bullets`
- `prose_plus_table`
- `prose_plus_graph`

Use `prose_single`, `prose_paired`, or `poem` in generation only when the
request explicitly asks for a grammar or Expression of Ideas item embedded in
that stimulus format. Do not reject those modes during ingestion solely because
they are uncommon for grammar.

Default grammar stem wording:

> Which choice completes the text so that it conforms to the conventions of
> Standard English?

For revision questions, the stem must explicitly name the revision goal.
For no-change questions, the stem must not imply that an error exists.

## 4. Classification Fields

Grammar outputs use this classification shape:

```json
{
  "domain": "Standard English Conventions",
  "skill_family": "Sentence Boundaries",
  "subskill": "sentence boundary with interruption",
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "sentence_boundary",
  "grammar_focus_key": "comma_splice",
  "secondary_grammar_focus_keys": [],
  "syntactic_trap_key": "interruption_breaks_subject_verb",
  "answer_mechanism_key": "rule_application",
  "solver_pattern_key": "apply_grammar_rule_directly",
  "disambiguation_rule_applied": "sentence_boundary > punctuation",
  "classification_rationale": "The correct option repairs a comma splice."
}
```

Approved `question_family_key` values in this module:

- `conventions_grammar`
- `expression_of_ideas`

For `question_family_key: "expression_of_ideas"`, `grammar_role_key` may be
`expression_of_ideas` when grammar-adjacent, or null/omitted when the item is
Expression of Ideas but not grammar-adjacent. In both cases, keep the item in
this module rather than routing it to the reading module.

Approved `answer_mechanism_key` values:

- `rule_application`
- `pattern_matching`
- `evidence_location`
- `inference`
- `data_synthesis`

Approved `solver_pattern_key` values:

- `apply_grammar_rule_directly`
- `locate_error_zone`
- `compare_register`
- `evaluate_transition`
- `synthesize_notes`
- `eliminate_by_boundary`

## 5. Grammar Role Keys

Approved `grammar_role_key` values:

- `sentence_boundary`
- `agreement`
- `verb_form`
- `modifier`
- `punctuation`
- `parallel_structure`
- `pronoun`
- `expression_of_ideas`

Use `sentence_boundary` for fragments, run-ons, comma splices, and decisions
about whether sentence units are correctly joined or separated.

Use `agreement` for subject-verb agreement, pronoun-antecedent agreement,
countability, number agreement, and determiner/article issues where number or
specificity is central.

Use `verb_form` for tense consistency, finite/nonfinite verbs, gerunds,
infinitives, voice, mood, conditional logic, and scientific/general present.

Use `modifier` for dangling modifiers, misplaced modifiers, modifier scope,
comparative structures, and logical predication when subject-predicate
compatibility is central.

Use `punctuation` for comma mechanics, semicolons, colons, dashes, apostrophes,
appositives, quotation punctuation, and hyphens.

Use `parallel_structure` for parallel lists, correlative conjunctions,
comparison symmetry, and elliptical constructions.

Use `pronoun` for pronoun case, clarity, and ambiguous reference.

Use `expression_of_ideas` for grammar-adjacent concision, register, transition
logic, precision, data-claim accuracy, rhetorical effectiveness, and emphasis.

## 6. Grammar Focus Keys

Use the most specific applicable `grammar_focus_key`.

Sentence boundary:

- `sentence_fragment`
- `comma_splice`
- `run_on_sentence`
- `sentence_boundary`

Agreement:

- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability`
- `determiners_articles`
- `affirmative_agreement`

Pronoun:

- `pronoun_case`
- `pronoun_clarity`
- `pronoun_antecedent_agreement`

Verb form:

- `verb_tense_consistency`
- `verb_form`
- `voice_active_passive`
- `negation`

Modifier:

- `modifier_placement`
- `comparative_structures`
- `logical_predication`
- `relative_pronouns`

Punctuation:

- `punctuation_comma`
- `colon_dash_use`
- `semicolon_use`
- `conjunctive_adverb_usage`
- `apostrophe_use`
- `possessive_contraction`
- `appositive_punctuation`
- `hyphen_usage`
- `quotation_punctuation`

Parallel structure:

- `parallel_structure`
- `elliptical_constructions`
- `conjunction_usage`

Expression of Ideas:

- `redundancy_concision`
- `precision_word_choice`
- `register_style_consistency`
- `logical_relationships`
- `emphasis_meaning_shifts`
- `data_interpretation_claims`
- `transition_logic`

## 7. Role to Focus Mapping

The agent must never emit a `grammar_focus_key` outside the declared
`grammar_role_key`.

| `grammar_role_key` | Allowed `grammar_focus_key` values |
|---|---|
| `sentence_boundary` | `sentence_fragment`, `comma_splice`, `run_on_sentence`, `sentence_boundary` |
| `agreement` | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability`, `determiners_articles`, `affirmative_agreement` |
| `verb_form` | `verb_tense_consistency`, `verb_form`, `voice_active_passive`, `negation` |
| `modifier` | `modifier_placement`, `comparative_structures`, `logical_predication`, `relative_pronouns` |
| `punctuation` | `punctuation_comma`, `colon_dash_use`, `semicolon_use`, `conjunctive_adverb_usage`, `apostrophe_use`, `possessive_contraction`, `appositive_punctuation`, `hyphen_usage`, `quotation_punctuation` |
| `parallel_structure` | `parallel_structure`, `elliptical_constructions`, `conjunction_usage` |
| `pronoun` | `pronoun_case`, `pronoun_clarity`, `pronoun_antecedent_agreement` |
| `expression_of_ideas` | `redundancy_concision`, `precision_word_choice`, `register_style_consistency`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `transition_logic` |

If the focus cannot be mapped, propose an amendment.

## 8. Disambiguation Rules

Apply these priority rules whenever multiple labels seem possible:

1. `sentence_boundary` > general `punctuation`
2. `logical_predication` > `modifier_placement`, `comparative_structures`,
   `parallel_structure`, `conjunction_usage`
3. `transition_logic` > `conjunction_usage`, `parallel_structure`
4. `conjunctive_adverb_usage` > general `punctuation`, `conjunction_usage`
5. `negation` > `logical_predication`, `parallel_structure`,
   `modifier_placement`, `verb_form`
6. `pronoun_case` > `pronoun_antecedent_agreement`
7. `pronoun_clarity` > `pronoun_antecedent_agreement`
8. `comparative_structures` > `parallel_structure`, `modifier_placement`
9. `voice_active_passive` > general `verb_form`
10. `noun_countability` > `subject_verb_agreement`
11. `relative_pronouns` > `modifier_placement`
12. `possessive_contraction` > `apostrophe_use`
13. `hyphen_usage` > general `punctuation`, `modifier_placement`
14. idiom-like conjunction usage > general `conjunction_usage`

`preposition_idiom` is not an approved production focus key in the source list.
If an idiom/preposition case cannot be represented by an approved focus key,
propose an amendment rather than emitting `preposition_idiom`.

Whenever a conflict is resolved, write the exact rule in
`disambiguation_rule_applied`. If no listed rule resolves the conflict, set
`needs_human_review: true`.

## 9. Grammar Decision Tree

1. Is the answer selected because of grammar, punctuation, sentence structure,
   or usage? If yes, use `conventions_grammar`.
2. Is the item transition logic, notes synthesis, concision, register, or
   rhetorical goal? If yes, use `expression_of_ideas`.
3. Does the issue join or separate sentence units? Use sentence-boundary keys.
4. Does punctuation decide the answer without sentence-boundary logic? Use the
   specific punctuation focus.
5. Does agreement decide the answer? Use an agreement focus.
6. Does verb tense, form, voice, mood, or negation decide the answer? Use a
   verb-form focus.
7. Does modifier attachment, comparison, relative-pronoun logic, or predicate
   compatibility decide the answer? Use a modifier focus.
8. Does pronoun case or reference decide the answer? Use a pronoun focus.
9. Does form symmetry decide the answer? Use `parallel_structure`.
10. If multiple rules appear, identify the primary rule that eliminates the
    most wrong options and store other visible rules in
    `secondary_grammar_focus_keys`.

## 10. Syntactic Trap Keys

Use `syntactic_trap_key` for the mechanism that makes the grammar decision hard.

Approved values:

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

Generation profiles must also include:

```json
{
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "low | medium | high"
}
```

## 11. Grammar Option Analysis

For grammar distractors, populate `option_error_focus_key` with a specific
grammar focus key whenever possible.

Required specificity examples:

| Wrong option surface error | Forbidden general label | Required `option_error_focus_key` |
|---|---|---|
| wrong semicolon | `punctuation_error` | `semicolon_use` |
| wrong apostrophe | `punctuation_error` | `apostrophe_use` |
| wrong tense | `grammar_error` | `verb_tense_consistency` |
| wrong relative clause | `grammar_error` | `relative_pronouns` |
| comma splice | `grammar_error` | `comma_splice` |
| dangling modifier | `grammar_error` | `modifier_placement` |

Approved grammar distractor type keys:

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
- `correct`

Approved grammar plausibility source keys:

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`
- `surface_similarity_bias`
- `transition_assumption`
- `register_confusion`

Approved grammar semantic relation keys:

- `nearest_noun_agreement`
- `comma_splice`
- `boundary_not_closed`
- `boundary_overly_strong`
- `wrong_boundary_type`
- `correct_agreement`
- `correct_boundary`
- `unnecessary_auxiliary`
- `tense_mismatch`
- `modifier_misplaced`
- `pronoun_ambiguous`
- `parallel_broken`
- `idiom_violation`

`grammar_fit` semantics:

- `yes`: the option is grammatically possible in some context, even if it fails
  the tested rule or the current passage.
- `no`: the option contains a clear grammar error that makes it impossible in
  standard usage.

`tone_match` semantics:

- `yes`: formal or neutral academic register is preserved.
- `no`: slang, contractions, colloquial wording, or register shift appears.

## 12. No-Change and Original-Text Rule

When original passage wording appears as one option, populate:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

No-change generation rules:

1. Generate a grammatically flawless passage with no error at the target zone.
2. Make option A the original text and the correct option unless a caller
   explicitly requests a different no-change position for experiment-only
   generation.
3. The three distractors each introduce a different grammar error.
4. The stem must be neutral and must not assume an error exists.
5. `explanation_full` must explicitly justify why no change is needed.

No-change distractor requirements:

| Position | Must introduce... |
| -------- | ----------------- |
| B | Primary grammar error for the target focus key |
| C | Different grammar error (secondary focus key) |
| D | Plausible-sounding error that violates a common rule |

No-change generation requests use:

```json
{
  "is_no_change_target": true,
  "no_change_position": "A"
}
```

No-change items are common enough to be supported deterministically. The source
rules target roughly 20% of official-style grammar items as original-text
correct when a batch requests no-change coverage.

## 13. Multi-Error Rule

When more than one grammar concept is visible:

1. Store the primary rule in `grammar_focus_key`.
2. Store other visible rules in `secondary_grammar_focus_keys`.
3. Store each wrong option's specific error in `option_error_focus_key`.
4. Do not leave `secondary_grammar_focus_keys` empty when a secondary rule is
   visibly present.

The primary rule is the rule that most directly explains why the correct answer
is required or eliminates the largest number of wrong options.

## 14. Verb-Form Tense/Register Metadata

For `grammar_role_key: "verb_form"` or focus keys `verb_tense_consistency`,
`verb_form`, or `voice_active_passive`, output:

```json
{
  "passage_tense_register_key": "scientific_general_present",
  "expected_tense_key": "simple_present",
  "tense_shift_allowed": false,
  "tense_register_notes": "The sentence states a general biological fact."
}
```

Approved `passage_tense_register_key` values:

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`

Approved `expected_tense_key` values:

- `simple_present`
- `simple_past`
- `present_perfect`
- `past_perfect`
- `future`
- `conditional`
- `subjunctive`
- `imperative`

If the register cannot be determined, set `needs_human_review: true`.

## 15. Grammar Generation Request Extension

Grammar generation requests must include:

```json
{
  "generation_request": {
    "domain": "grammar",
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
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "passage_length_words": "25-35",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs one medium S-V agreement item."
  }
}
```

Reject requests that:

- use an unapproved `grammar_focus_key`
- map a focus to the wrong role
- request `very_low` frequency without explicit justification
- request a reading-only skill or focus key
- request no-change behavior but omit no-change metadata

Frequency bands:

| Frequency band | Grammar focus keys |
|---|---|
| `very_high` | `punctuation_comma`, `subject_verb_agreement` |
| `high` | `verb_tense_consistency`, `semicolon_use`, `apostrophe_use`, `sentence_boundary`, `appositive_punctuation` |
| `medium` | `relative_pronouns`, `modifier_placement`, `colon_dash_use`, `pronoun_antecedent_agreement`, `parallel_structure` |
| `low` | `voice_active_passive`, `logical_predication`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation` |
| `very_low` | `affirmative_agreement`, `negation`, `noun_countability`, `determiners_articles`, `elliptical_constructions` |

Do not generate `very_low` frequency items unless the request explicitly asks
for niche coverage.

Generated grammar items must populate `generation_profile` with:

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
  "passage_template": "The [singular noun] of [plural noun], [relative clause], ______ [predicate].",
  "generation_timestamp": "ISO-8601 timestamp",
  "model_version": "rules_v3"
}
```

## 16. Grammar Generation Workflow

1. Validate role/focus/trap/frequency request.
2. Generate the passage or sentence.
3. Generate the stem.
4. Generate the correct option.
5. Generate three distractors.
6. Assemble metadata, classification, reasoning, and generation profile.
7. Run core validation.
8. Run grammar validation.
9. Retry failed component up to three times.

Passage requirements:

- 20-40 words for `sentence_only`; 80-150 for passage excerpts
- formal academic register; no contractions, slang, or first person
- self-contained meaning
- one clear target grammar decision
- target trap embedded naturally
- no outside knowledge required

Option requirements:

- exactly four options
- one correct answer
- no mixed option formats
- at least one distractor targets the declared syntactic trap
- no two distractors share the same `option_error_focus_key`

Difficulty calibration:

| Difficulty | Trap intensity | Distractor plausibility | Passage complexity |
|---|---|---|---|
| `low` | `none` or `low` | errors are clear but not malformed | short sentence, common vocabulary |
| `medium` | `medium` | one strong distractor, two moderate | standard academic vocabulary, one clause |
| `high` | `high` | all three distractors plausible | dense vocabulary, multiple clauses, unfamiliar topic |

When `target_syntactic_trap_key` is `none`, cap `difficulty_overall` at
`medium` unless the request explicitly uses intentionally complex syntax or
high distractor competition to justify `high`.

## 17. Passage Generation Rules by Focus

Each grammar focus requires the passage to embed the rule in a specific way. Use these as construction constraints.

### Subject-Verb Agreement
- Use a singular collective, abstract, or inverted subject.
- Insert a plural prepositional phrase or relative clause between subject and verb.
- Template: "The [singular collective noun] of [plural noun], [relative clause], ______ [verb phrase]."

### Verb Tense Consistency
- Open the sentence with a strong time marker (last year, in 1984, by the time).
- Include a second time marker or temporal clause that could pull the tense in a different direction.
- Template: "[Time marker], [subject] [establishes action], and the [related noun] ______ [result]."

### Modifier Placement / Dangling Modifier
- Open with a participial phrase whose logical subject differs from the grammatical subject.
- Template: "[Participial phrase], [noun that did NOT do the action] ______."

### Punctuation — Semicolon
- Use two closely related independent clauses.
- Place a conjunctive adverb (however, therefore, moreover, thus) in the second clause if targeting `conjunctive_adverb_usage`.
- Template: "[IC1] ______ [transition], [IC2]."

### Apostrophe / Possessive
- Use a possessive where the noun ends in s (plural possessive trap).
- Or use a possessive pronoun next to a contraction homophone.
- Template: "The [plural noun] ______ [relationship to something] were recognized at the ceremony."

### Parallel Structure
- Create a list of three where two items share form and one breaks form.
- Or use a correlative conjunction (not only...but also) where both elements must match.
- Template: "The program teaches students to [verb], [verb], and ______."

### Pronoun Case
- Use a compound subject or object so the case of the individual pronoun is less obvious.
- Template: "The award was presented to [name] and ______ for outstanding work."

### Comparative Structures / Illogical Comparisons
- Create a comparison where the two things being compared are different types unless the correct answer adds the possessive or "other."
- Template: "The [noun] of [subject] was greater than ______."

### Adjective vs. Adverb
- Use a linking verb followed by a blank where both adjective and adverb forms are common but only one is correct.
- Or use a verb modified by an adverb where the adjective form feels natural in speech.
- Template: "The results were [surprisingly / more surprisingly / surprising / more surprising] consistent."

### Subjunctive Mood
- Use a conditional, wish, or recommendation clause where subjunctive is required.
- Template: "The review board recommended that the proposal ______ before publication."

### Transition Logic
- Write two clauses with a specific logical relationship (contrast, cause, continuation) and present four transition words — one correct, three from different logical relationships.
- Template: "[Statement A] ______; [statement B that [contrasts / elaborates / results from] A]."

### Pronoun Antecedent Agreement
- Use a singular antecedent that looks plural ("the team," "everyone," "each").
- Place a plural noun nearby to attract the wrong pronoun.
- Template: "Every [singular noun] must submit [pronoun blank] ______ before [deadline]."

### Pronoun Clarity
- Create a sentence with two or more possible antecedents for a pronoun.
- Template: "When [person A] met with [person B], ______ presented the revised [deliverable]."

### Punctuation — Comma
- Create a compound sentence with or without a coordinating conjunction.
- Test FANBOYS comma, introductory phrase comma, or nonrestrictive element comma.
- Template: "[Subject] [verb phrase] and ______ [second predicate or clause]."

### Appositive Punctuation
- Use a noun phrase that renames an adjacent noun.
- Test comma vs no comma for essential vs nonessential appositive.
- Template: "The [title] [proper noun] ______ [appositive] [verb phrase]."

### Relative Pronouns
- Use a clause that is either essential or nonessential.
- Test `that` vs `which` or comma placement around the clause.
- Template: "The [noun] ______ [relative clause] [main predicate]."

### Colon and Dash Use
- Create a sentence where an independent clause is followed by an explanation, list, or elaboration.
- Test colon vs dash vs comma vs no punctuation.
- Template: "The researchers identified one primary cause ______ [elaboration] in [subject area]."

### Conjunctive Adverb Usage
- Join two independent clauses with a conjunctive adverb (however, therefore, moreover, thus).
- Test semicolon + comma vs comma only vs period + comma.
- Template: "The proposal was rejected ______ [conjunctive adverb], [second independent clause]."

### Possessive / Contraction Distinction
- Use a context where `it's` vs `its`, `who's` vs `whose`, or `they're` vs `their` is tested.
- Template: "The company expanded ______ operations overseas."

### Hyphen Usage
- Use a compound modifier before a noun where hyphenation is required or forbidden.
- Template: "The ______ [compound modifier] [noun] [verb phrase]."

### Sentence Fragment
- Create a subordinate clause presented as a complete sentence.
- The correct answer connects it to the main clause or rewrites it.
- Template: "Although [subordinate clause]. [Subject] ______ [main clause]."

### Comma Splice
- Join two independent clauses with only a comma.
- The correct answer repairs the splice with a semicolon, period, or conjunction.
- Template: "[IC1], ______ [IC2]."

### Run-On Sentence
- Fuse two independent clauses with no punctuation or conjunction.
- The correct answer inserts proper punctuation or a conjunction.
- Template: "[IC1] ______ [IC2]."

### Noun Countability
- Use a mass noun with a plural article or vice versa.
- Template: "The researchers collected ______ from three separate sources."

### Determiners and Articles
- Use an article where none is needed, or omit a required article.
- Template: "______ [noun] is essential for [process or field]."

### Affirmative Agreement
- Test `so` / `neither` / `nor` responses with inverted auxiliary matching.
- Template: "[First clause], and ______ [second subject]."

### Voice — Active vs Passive
- Create a passage where the choice between active and passive determines whether the agent is clear or buried.
- Template: "[Time marker], [subject] ______ [agent phrase]."
- Common trap: passive construction that obscures who performed the action when the context demands clarity, or active construction that foregrounds the wrong entity.
- Difficulty escalates when both active and passive are grammatically acceptable but only one matches the agent-focus conventions of the genre (e.g., scientific methods favor passive; narrative history favors active).

### Negation
- Place negation where scope ambiguity creates multiple interpretations.
- Template: "The study did not find significant differences ______ [scope qualifier]."
- Expanded construction: "The [subject] did not [verb phrase] ______ [scope-delimiting phrase]."
- High-difficulty versions nest negation inside a concessive or conditional structure where the scope of "not" is ambiguous across clause boundaries.
- Common trap: double negative that reads emphatically in speech but is nonstandard in formal writing.

### Logical Predication
- Create a sentence where the subject and predicate are grammatically possible but logically incompatible.
- Template: "The [abstract nominalization] ______ [predicate that requires an animate or concrete subject]."
- Expanded construction: "[Gerund or abstract quality] was [concrete action verb typically performed by people]."
- Common trap patterns:
  1. Inanimate subject paired with a verb requiring animate agency ("The theory investigated...")
  2. Abstract quality doing a concrete action ("Curiosity measured the distance...")
  3. Nominalization causing category confusion ("The decline of the empire was blue...")
- The correct answer typically restructures to assign the action to the proper logical subject.

### Quotation Punctuation
- Test comma or colon placement with direct quotations.
- Template: "The critic wrote ______ [opening quotation mark] [quoted text]."
- Expanded templates:
  1. "[Reporting verb] [comma/colon/no punctuation] [open quote] [quoted material] [close quote]."
  2. "[Quoted material] [comma/period] [close quote] [attribution phrase]."
- Rules: colon or comma before a full-sentence quotation after an independent clause; no punctuation before a quotation that flows as part of the sentence grammar; comma or period inside closing quotation marks (American convention).
- Common trap: colon when the quoted material is a sentence fragment; no punctuation when a full IC precedes a full-sentence quote.

### Noun Countability
- Use a mass noun where count syntax appears (or vice versa).
- Template: "The researchers collected ______ from three separate sources."
- Expanded templates:
  1. "[quantifier requiring count noun] ______ [mass noun] were analyzed." (forces count syntax onto uncountable noun)
  2. "The team gathered [much/many] ______ [noun that could be ambiguous] for the analysis."
- Key distinctions: *fewer/less, many/much, number/amount, fewer/less* — each pair maps to count vs. mass.
- Common trap: mass nouns that feel countable in casual speech (*research, evidence, equipment, information, advice, furniture*).

### Determiners and Articles
- Use an article where none is needed, or omit a required article.
- Template: "______ [noun] is essential for [process or field]."
- Expanded templates:
  1. "[Zero article] [plural/general noun] [verb] [specific context that may demand 'the']."
  2. "[Article choice] [singular noun] [relative clause that changes definiteness]."
- Rules: zero article for general plural/uncountable reference; *a/an* for first mention of singular count nouns; *the* for specific/known/shared reference or second mention.
- Common trap: proper nouns that conventionally take or omit *the* (*the Amazon* vs. *Amazon River* vs. *Lake Michigan*).

### Affirmative Agreement
- Test *so/neither/nor* responses with inverted auxiliary matching.
- Template: "[First clause], and ______ [second subject]."
- Expanded template: "[Subject A] [auxiliary] [verb], and [so/neither/nor] ______ [Subject B]."
- Rules: *so + auxiliary + subject* for positive agreement; *neither/nor + auxiliary + subject* for negative agreement. The auxiliary must match tense and number of the first clause.
- Common trap: wrong auxiliary in the inverted response (*"She has finished, and so do I"* instead of *"so have I"*).

### Elliptical Constructions
- Create a comparison or parallel where the second clause omits a verb, requiring the reader to infer the correct auxiliary from the first clause.
- Template: "[Subject A] [verb phrase], and [Subject B] ______ [remaining complement or nothing]."
- Expanded templates:
  1. "[Subject A] has [past participle], and [Subject B] ______ [as well / too / similarly]."
  2. "I run faster than [Subject B] ______."
- Rules: the omitted verb form must be recoverable from the first clause; when the tense/auxiliary differs between clauses, the second cannot be elliptical.
- Common trap: omitted verb that would differ in tense or number from the first clause, making the ellipsis ungrammatical.

### Conjunction Usage
- Use a conjunction whose logical meaning mismatches the clause relationship.
- Template: "[IC1] ______ [IC2 with particular logical relationship]."
- Expanded templates:
  1. Correlative: "Not only [phrase A] ______ [phrase B]." (requires *but also*)
  2. Paired: "[Whether / Either / Neither] [element A] ______ [element B]." (requires matching pair)
  3. Subordinating: "[DC with subordinator], ______ [IC]." (subordinator logic must match the relationship)
- Common correlative pairs: *not only...but also, either...or, neither...nor, both...and, whether...or, as...as*.
- Common trap: breaking a correlative pair with a plausible but wrong second element (*"not only brilliant but still humble"* instead of *"but also humble"*).

### Possessive / Contraction Distinction
- Use a context where *it's/its, who's/whose,* or *they're/their/there* is tested.
- Template: "The company expanded ______ operations overseas."
- Expanded construction: "[Noun phrase] [verb], and [pronoun form] ______ [complement that tests the distinction]."
- Test method: replace with the expanded form (*it's→it is, who's→who is, they're→they are*). If the sentence still works, contraction is correct. If not, possessive is required.
- Common trap: *its'* (nonstandard form used as a distractor).

### Rhetorical Synthesis — Passage Construction
- Provide 3-6 bulleted notes on a topic; the prompt specifies the exact rhetorical goal.
- Template bullet set: 
  - "[Researcher/Source], [year/date] — [specific finding or detail]"
  - "[Researcher/Source] — [contrasting or complementary finding]"
  - "[Subject] — [additional detail not needed for the goal]"
- Goal embedding rules:
  - Contrast goal: at least two bullets must describe different positions, methods, or findings from different sources
  - Similarity goal: at least two bullets must describe converging findings
  - Specific detail goal: exactly one bullet contains the target detail (time, measurement, person name)
  - Generalization goal: bullets draw from different aspects of the same phenomenon
- The distractor set must include: (a) accurate content failing the goal, (b) goal-achieving content distorting the data, (c) plausible content adding outside information.

### Precision / Word Choice — Passage Construction
- Use a word whose exact shade of meaning determines the logical or argumentative force of the sentence.
- Template: "The findings ______ [verb requiring precision: suggests/demonstrates/proves/indicates] a fundamental shift in the mechanism."
- Focus on near-synonyms where one is exactly right and others are slightly wrong (*suggests vs. demonstrates vs. establishes vs. confirms* when the data is preliminary).
- Common trap: more formal-sounding word that oversells the certainty.

### Register / Style Consistency — Passage Construction
- Embed a register shift at the target location within otherwise formal academic prose.
- Template: "[Formal academic sentence context] ______ [word or phrase choice that tests register] [rest of formal context]."
- Test: slang, contractions, colloquialisms, or informal phrasing in a passage that otherwise maintains formal academic register.
- Common trap: the informal choice sounds more natural or conversational; the formal choice may sound "stiff" to casual readers but is correct.

### Emphasis / Meaning Shifts — Passage Construction
- Create a sentence where word order, active/passive choice, or modifier placement shifts what the sentence foregrounds.
- Template: "[Clause element A] [verb] [clause element B], ______ [restructured version with different emphasis]."
- The correct option preserves both the meaning and the emphasis pattern appropriate to the surrounding context.
- Common trap: an option that is grammatically flawless and semantically equivalent but places emphasis on the wrong entity for the passage purpose.

### Data Interpretation Claims — Passage Construction
- Present a prose context making a claim, paired with a table or graph that the options must interpret correctly.
- Template: "[Claim about data]. The table shows ______ [data pattern that supports, partially supports, or contradicts]."
- Options must test whether the student correctly maps the quantitative pattern to the qualitative claim, without overstating or cherry-picking.
- Common trap: option accurately describing a number from the table but drawing the wrong qualitative conclusion.

If a requested focus key is not listed here but is approved in Section 6, use the closest construction family above and document the choice in `classification_rationale`.

## 18. Distractor Heuristics by Grammar Focus

Every distractor must be wrong for a specific reason and include a `student_failure_mode_key`.

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

### Punctuation — Comma
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Missing comma creating a run-on or comma splice | `comma_fix_illusion` |
| 2 | Unnecessary comma before an essential clause | `punctuation_intimidation` |
| 3 | Semicolon where comma is correct | `formal_word_bias` |

### Relative Pronouns
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | `which` without comma for essential clause | `punctuation_intimidation` |
| 2 | `that` with comma for nonessential clause | `grammar_fit_only` |
| 3 | `who` for inanimate antecedent | `nearest_noun_reflex` |

### Colon and Dash Use
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comma instead of colon or dash | `comma_fix_illusion` |
| 2 | Semicolon where colon is required | `formal_word_bias` |
| 3 | No punctuation (run-on elaboration) | `grammar_fit_only` |

### Appositive Punctuation
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comma around essential appositive (overcorrection) | `punctuation_intimidation` |
| 2 | No comma around nonessential appositive | `grammar_fit_only` |
| 3 | Dash where comma is sufficient | `formal_word_bias` |

### Conjunctive Adverb Usage
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comma only before conjunctive adverb (comma splice) | `comma_fix_illusion` |
| 2 | Period before conjunctive adverb with lowercase | `grammar_fit_only` |
| 3 | Semicolon but no comma after the adverb | `formal_word_bias` |

### Pronoun Antecedent Agreement
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Plural pronoun for singular antecedent (attracted by nearby plural) | `nearest_noun_reflex` |
| 2 | Wrong-gender or ambiguous pronoun | `pronoun_anchor_error` |
| 3 | Reflexive pronoun where simple pronoun is required | `formal_word_bias` |

### Possessive / Contraction Distinction
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Contraction where possessive is required (it's for its) | `idiom_memory_pull` |
| 2 | Possessive where contraction is required (its for it's) | `surface_similarity_bias` |
| 3 | Nonstandard form (its', who'se) | `grammar_fit_only` |

### Sentence Boundary (Fragment / Run-On / Comma Splice)
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Comma splice that sounds conversational | `comma_fix_illusion` |
| 2 | Period that creates a fragment | `scope_blindness` |
| 3 | Dash that looks stylish but does not repair the boundary | `punctuation_intimidation` |

### Negation / Scope of Negation
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Negation scoping over the wrong constituent | `scope_blindness` |
| 2 | Double negative that sounds emphatic | `ear_test_pass` |
| 3 | Negation removed entirely, changing the meaning | `grammar_fit_only` |

### Transition Logic
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Transition with opposite logical direction (contrast when agreement needed) | `transition_assumption` |
| 2 | Formal transition that sounds authoritative regardless of direction | `register_confusion` |
| 3 | Additive/sequence transition that is plausible but misrepresents the logical relationship | `scope_blindness` |

### Transition Logic — Extended Heuristics

The correct transition must match one of these approved logical relationship categories:

| Category | Approved transitions | Relationship type |
| -------- | -------------------- | ----------------- |
| Addition | *also, besides, furthermore, in addition, moreover, additionally* | Continue/support |
| Similarity | *likewise, similarly, by the same token* | Continue/parallel |
| Example | *for example, for instance, specifically, in particular, to illustrate* | Continue/illustrate |
| Clarification | *in other words, that is, namely, that is to say* | Continue/restate |
| Emphasis | *in fact, indeed, notably* | Continue/reinforce |
| Sequence | *afterward, eventually, previously, subsequently, then, ultimately, first/second/finally* | Continue/time-order |
| Direct Opposition | *however, nevertheless, nonetheless, conversely, yet, instead, rather* | Contrast/oppose |
| Concession | *admittedly, granted, that said, still, even so, regardless* | Contrast/concede |
| Difference | *by comparison, in contrast, by contrast, alternatively, alternately* | Contrast/compare |
| Causation | *therefore, thus, consequently, hence, accordingly, as a result, for this reason* | Cause-effect |
| Purpose | *to this end, to these ends, with this in mind* | Cause-purpose |
| Appropriateness | *fittingly, appropriately, unsurprisingly, naturally* | Fit/consequence |

Hard transitions (adverbs: *however, therefore, moreover, thus, consequently*): set off by comma; don't change clause independence. Soft transitions (FANBOYS: *but, yet, so*; subordinators: *although, whereas, despite*): no comma after; turn clauses dependent.

Two transition synonyms in the same item's option list is a signal that both are wrong. The SAT never presents two functionally identical correct answers.

When generating a transition item, the distractor set must pull transitions from at least two different relationship categories (e.g., one contrast + one causation + one addition, when the correct relationship is sequence).

### Transition Word Frequency Table (Bluebook Tests 4-10)

| Word | Category | Answer frequency |
| ---- | -------- | ---------------- |
| However | Contrast | 10x |
| Therefore | Causation | 8x |
| Conversely | Contrast | 8x |
| Nevertheless | Contrast | 7x |
| Accordingly | Causation | 6x |
| Thus | Causation | 6x |
| Consequently | Causation | 5x |
| For instance | Example | 4x |
| Instead | Contrast | 4x |
| Similarly | Similarity | 4x |

### Rhetorical Synthesis
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Accurate note content that does not accomplish the stated rhetorical goal | `goal_mismatch` |
| 2 | Achieves goal but distorts or exaggerates note content ("always," "never," "universally") | `scope_blindness` |
| 3 | Introduces information absent from the bulleted notes (outside knowledge) | `transition_assumption` |

Approved rhetorical goal categories:

| Goal Type | Required structure | Rejection signal |
| --------- | ------------------ | ---------------- |
| Contrast/Difference | Must mention both subjects; uses "whereas," "unlike," "while," "compared to" | Choice mentions only one subject |
| Similarity | Must mention both subjects; uses "both," "similarly," "also," "like," "in common" | Choice discusses only one subject |
| Summarize/Introduce | Must synthesize multiple bullets at a general level; breadth over depth | Choice drills into a single bullet detail |
| Specific Detail | Must include the exact keyword from the prompt (time, person, location, measurement) | Choice omits the keyword or paraphrases it loosely |
| Generalization | Must draw a cross-cutting claim supported by multiple bullets | Choice makes a claim not supported by multiple bullets |

Hard traps for high-difficulty synthesis items:
- **Correct Info, Wrong Goal**: choice faithfully reproduces notes but answers a different rhetorical task
- **The "Smart Student" Trap**: the most eloquent or sophisticated-sounding choice is wrong because it does not literally fulfill the prompt (these are data-retrieval tasks)
- **Reversed Causation**: choice implies A causes B when notes only establish correlation or the reverse direction
- **Logical Fallacy / Overgeneralization**: choice draws a universal conclusion from partial or qualified data

### Redundancy / Concision
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Wordy rephrase that preserves meaning but uses 3-5 extra words | `formal_word_bias` |
| 2 | Option that repeats information already present in the passage (definition-repetition) | `scope_blindness` |
| 3 | Option that cuts essential meaning while sounding crisper | `false_precision` |

Redundancy detection patterns (any of these make an option wrong):
- Word + its own definition in the same clause (e.g., "inaudible and could not be heard")
- *being* in the option when a shorter alternative exists without it
- Gerund chain (*the gaining of admission being their goal*) when noun + verb exists
- Passive construction (*X was done by Y*) when an active alternative is one of the options and preserves meaning
- Wordy phrases with known concise equivalents: *due to the fact that→because, at this point in time→now, has the ability to→can, in the event that→if, the reason why is because→because*

The shortest answer that remains grammatically correct and preserves all essential meaning is always correct.

### Precision / Word Choice
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Near-synonym that changes the precise meaning, tone, or logical implication | `surface_similarity_bias` |
| 2 | More formal-sounding word that introduces a semantic mismatch | `formal_word_bias` |
| 3 | Colloquial or informal word in a formal academic context | `register_confusion` |

### Register / Style Consistency
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Slang, contraction, or colloquialism in formal academic prose | `register_confusion` |
| 2 | Overly stiff or archaic phrasing inconsistent with passage register | `formal_word_bias` |
| 3 | First-person or second-person shift in a third-person passage | `ear_test_pass` |

### Emphasis / Meaning Shifts
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Option that shifts emphasis to a different clause element without changing grammaticality | `scope_blindness` |
| 2 | Option that subtly alters the degree of certainty (*suggests* vs. *proves*, *might* vs. *will*) | `false_precision` |
| 3 | Active/passive shift that foregrounds the wrong entity for the passage context | `grammar_fit_only` |

### Data Interpretation Claims
| Distractor | Error | Student failure mode |
| ---------- | ----- | -------------------- |
| 1 | Option that accurately quotes table/graph values but draws the wrong conclusion | `scope_blindness` |
| 2 | Option that overstates findings using absolute language (*proves, guarantees, universally*) when data is partial | `transition_assumption` |
| 3 | Option that confuses correlation with causation in the data relationship | `data_misread` |

Forbidden distractor constructions:

- gibberish or impossible English unless impossibility is the tested contrast
- an accidental second grammar error unrelated to the target focus
- one option that is visibly longer, safer, or more polished than the rest
- distractors that all fail for the same focus key
- reading-only evidence traps in a SEC item
- grammar-error distractors in a pure non-grammar Expression of Ideas item

## 19. Evidence Span Selection Rules (Grammar)

`evidence_span_text` must quote the minimal text that justifies the correct answer.

Rules:

- Include the grammatical subject and the corrected element.
- Use `"..."` ellipsis to omit intervening text when the span exceeds 8 words.
- Do not include the full sentence unless the entire sentence is the evidence.
- For punctuation items, include the words immediately before and after the punctuation decision.

Examples:

- S-V agreement: `"The colony ... plays"` (subject + verb, ellipsis for intervening clause)
- Semicolon: `"distances ; they"` (words surrounding the punctuation)
- Modifier: `"After reviewing the data, the team revised"` (participial phrase + corrected subject)
- Apostrophe: `"students' projects"` (possessive + noun)
- Comma: `"sculpture, and it"` (comma + conjunction + pronoun)

## 20. Option Text Format Rules

Use one format per item:

1. Fill-in-blank: options contain only the word or phrase that fills the blank.
2. Full-replacement: options contain the full revised sentence, clause, or
   phrase.
3. Punctuation-only: options contain only the punctuation mark or punctuation
   sequence.

Do not mix formats within a single item.

## 21. Grammar Explanation Requirements

`explanation_short` must state the core rule in at most 25 words.

`explanation_full` must:

- explain why the correct answer is correct
- name each wrong option by label
- identify each wrong option's specific grammar error
- reference `passage_tense_register_key` for verb-form items
- explicitly justify no-change items when original text is correct

## 22. Grammar Validator Checklist

Before finalizing a grammar item:

- [ ] `question_family_key` is `conventions_grammar` or `expression_of_ideas`
- [ ] role/focus mapping is legal when `grammar_role_key` is non-null
- [ ] non-grammar Expression of Ideas items either use
      `grammar_role_key: "expression_of_ideas"` or omit/null grammar keys
      consistently
- [ ] reading-only keys are null or omitted
- [ ] `secondary_grammar_focus_keys` is populated when secondary rules are
      visible
- [ ] every grammar distractor has a specific `option_error_focus_key`
- [ ] no two distractors fail for the same exact reason
- [ ] no-change metadata is present when original text is an option
- [ ] tense/register metadata is present for verb-form items
- [ ] `disambiguation_rule_applied` is present when labels conflict
- [ ] option text format is consistent
- [ ] `evidence_span_text` is minimal and relevant
- [ ] `generation_profile` includes target role/focus/trap/frequency for
      generated items
- [ ] `generation_profile` includes `passage_template`,
      `generation_timestamp`, and `model_version`
- [ ] `difficulty_overall` matches the requested target and respects the
      `target_syntactic_trap_key: "none"` cap
- [ ] no unapproved grammar keys are used
- [ ] core validator checklist passes

## 23. Complete Worked Generation Examples

### Example A: Subject-Verb Agreement with Nearest Noun Attraction

```json
{
  "generation_request": {
    "domain": "grammar",
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
    "stem_type_key": "complete_the_text"
  },
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M1",
    "source_question_number": 999,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "The colony of deep-sea corals, which live in near-total darkness off the coast of Australia, ______ an important role in the local ecosystem.",
    "correct_option_label": "C",
    "explanation_short": "The singular subject 'colony' requires the singular verb 'plays.'",
    "explanation_full": "The grammatical subject is the singular noun 'colony,' not the plural 'corals' in the intervening relative clause. Therefore, the main verb must be singular: 'plays.' Option A ('play') incorrectly uses a plural verb attracted by the nearby noun 'corals.' Option B ('have played') uses a plural auxiliary. Option D ('is playing') introduces an unnecessary progressive form that changes the meaning.",
    "evidence_span_text": "The colony ... plays"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Form, Structure, and Sense",
    "subskill": "subject-verb agreement with intervening noun",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "agreement",
    "grammar_focus_key": "subject_verb_agreement",
    "secondary_grammar_focus_keys": [],
    "syntactic_trap_key": "nearest_noun_attraction",
    "evidence_scope_key": "sentence",
    "evidence_location_key": "main_clause",
    "answer_mechanism_key": "rule_application",
    "solver_pattern_key": "apply_grammar_rule_directly",
    "topic_broad": "science",
    "topic_fine": "marine biology",
    "reading_scope": "sentence-level",
    "reasoning_demand": "rule application",
    "register": "neutral informational",
    "tone": "objective",
    "difficulty_overall": "medium",
    "difficulty_reading": "low",
    "difficulty_grammar": "high",
    "difficulty_inference": "low",
    "difficulty_vocab": "low",
    "distractor_strength": "high",
    "disambiguation_rule_applied": null,
    "classification_rationale": "The item tests subject-verb agreement with a singular subject separated from its verb by a plural intervening noun."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": "play",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "nearest_noun_attraction",
      "option_error_focus_key": "subject_verb_agreement",
      "student_failure_mode_key": "nearest_noun_reflex",
      "why_plausible": "The plural noun 'corals' is the nearest noun to the verb slot.",
      "why_wrong": "The grammatical subject is the singular 'colony,' not 'corals.'",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.91
    },
    {
      "option_label": "B",
      "option_text": "have played",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "nearest_noun_agreement",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "subject_verb_agreement",
      "student_failure_mode_key": "formal_word_bias",
      "why_plausible": "Present perfect sounds sophisticated and formal.",
      "why_wrong": "The plural auxiliary 'have' does not agree with the singular subject 'colony.'",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.82
    },
    {
      "option_label": "C",
      "option_text": "plays",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_agreement",
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: singular verb agrees with singular subject 'colony.'",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3,
      "distractor_distance": null,
      "distractor_competition_score": null
    },
    {
      "option_label": "D",
      "option_text": "is playing",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "grammar_error",
      "semantic_relation_key": "unnecessary_auxiliary",
      "plausibility_source_key": "grammar_fit_only",
      "option_error_focus_key": "verb_form",
      "student_failure_mode_key": "grammar_fit_only",
      "why_plausible": "Progressive form is grammatically valid in isolation.",
      "why_wrong": "Present progressive changes meaning; general ecological roles use simple present.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.72
    }
  ],
  "reasoning": {
    "primary_rule": "Subject-verb agreement requires a singular subject to take a singular verb.",
    "trap_mechanism": "A plural noun ('corals') intervenes between the singular subject and the verb, tempting plural verb selection.",
    "correct_answer_reasoning": "The singular subject 'colony' requires the singular present-tense verb 'plays.'",
    "distractor_analysis_summary": "A and B are plural verbs attracted by the nearest noun; D introduces an unnecessary progressive form.",
    "similar_items": [
      {
        "pattern": "singular subject + intervening plural noun + verb blank",
        "focus_key": "subject_verb_agreement",
        "trap_key": "nearest_noun_attraction"
      }
    ]
  },
  "generation_profile": {
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "syntactic_trap_intensity": "high",
    "target_frequency_band": "very_high",
    "target_distractor_pattern": [
      "one nearest-noun plural verb distractor",
      "one plural auxiliary / compound verb distractor",
      "one unnecessary progressive/auxiliary distractor"
    ],
    "passage_template": "The [singular collective noun] of [plural noun], [relative clause], ______ [role/action].",
    "generation_timestamp": "2026-04-27T00:00:00Z",
    "model_version": "rules_v3"
  },
  "review": {
    "annotation_confidence": 0.95,
    "needs_human_review": false,
    "review_notes": "Clean S-V agreement item. No ambiguity in classification."
  }
}
```

### Example B: Semicolon Use

```json
{
  "generation_request": {
    "domain": "grammar",
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "semicolon_use",
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "high",
    "difficulty_overall": "medium",
    "topic_broad": "history",
    "topic_fine": "ancient civilizations",
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text"
  },
  "question": {
    "source_exam": "GENERATED",
    "source_section": "RW",
    "source_module": "M2",
    "source_question_number": 999,
    "stimulus_mode_key": "sentence_only",
    "stem_type_key": "complete_the_text",
    "prompt_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
    "passage_text": "The Roman aqueducts transported water across vast distances ______ they enabled cities to grow far from natural sources.",
    "correct_option_label": "B",
    "explanation_short": "A semicolon correctly joins two closely related independent clauses.",
    "explanation_full": "The sentence contains two independent clauses. A semicolon (B) is the most effective punctuation. Option A (comma) creates a comma splice. Option C (period) is grammatically correct but severs the close logical relationship. Option D (colon) incorrectly suggests the second clause explains the first.",
    "evidence_span_text": "distances ; they"
  },
  "classification": {
    "domain": "Standard English Conventions",
    "skill_family": "Sentence Boundaries",
    "subskill": "semicolon between independent clauses",
    "question_family_key": "conventions_grammar",
    "grammar_role_key": "punctuation",
    "grammar_focus_key": "semicolon_use",
    "secondary_grammar_focus_keys": ["sentence_boundary"],
    "syntactic_trap_key": "none",
    "disambiguation_rule_applied": "sentence_boundary > punctuation",
    "classification_rationale": "The item tests the correct use of a semicolon between two independent clauses."
  },
  "options": [
    {
      "option_label": "A",
      "option_text": ",",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "comma_splice",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "comma_splice",
      "student_failure_mode_key": "comma_fix_illusion",
      "why_plausible": "A comma is the most common punctuation; students default to it.",
      "why_wrong": "A comma alone cannot join two independent clauses.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.88
    },
    {
      "option_label": "B",
      "option_text": ";",
      "is_correct": true,
      "option_role": "correct",
      "distractor_type_key": "correct",
      "semantic_relation_key": "correct_boundary",
      "plausibility_source_key": "none",
      "option_error_focus_key": null,
      "student_failure_mode_key": null,
      "why_plausible": "Correct: semicolon joins two closely related independent clauses.",
      "why_wrong": null,
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 3
    },
    {
      "option_label": "C",
      "option_text": ".",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "boundary_overly_strong",
      "plausibility_source_key": "punctuation_style_bias",
      "option_error_focus_key": "sentence_boundary",
      "student_failure_mode_key": "scope_blindness",
      "why_plausible": "A period creates two complete sentences, which is grammatically acceptable.",
      "why_wrong": "While valid, a period is less effective than a semicolon at showing the close relationship.",
      "grammar_fit": "yes",
      "tone_match": "yes",
      "precision_score": 2,
      "distractor_distance": "tight",
      "distractor_competition_score": 0.90
    },
    {
      "option_label": "D",
      "option_text": ":",
      "is_correct": false,
      "option_role": "distractor",
      "distractor_type_key": "punctuation_error",
      "semantic_relation_key": "wrong_boundary_type",
      "plausibility_source_key": "formal_register_match",
      "option_error_focus_key": "colon_dash_use",
      "student_failure_mode_key": "punctuation_intimidation",
      "why_plausible": "A colon looks sophisticated in formal writing.",
      "why_wrong": "A colon must introduce an explanation or list of the preceding clause. The second clause adds a consequence, not an explanation.",
      "grammar_fit": "no",
      "tone_match": "yes",
      "precision_score": 1,
      "distractor_distance": "moderate",
      "distractor_competition_score": 0.78
    }
  ],
  "generation_profile": {
    "target_grammar_role_key": "punctuation",
    "target_grammar_focus_key": "semicolon_use",
    "target_syntactic_trap_key": "none",
    "syntactic_trap_intensity": "medium",
    "target_frequency_band": "high",
    "target_distractor_pattern": [
      "one comma splice distractor",
      "one period distractor (grammatically valid but less effective)",
      "one colon distractor (wrong boundary type)"
    ],
    "passage_template": "[IC1] ______ [IC2 related by consequence or contrast].",
    "generation_timestamp": "2026-04-27T00:00:00Z",
    "model_version": "rules_v3"
  }
}
```

## 24. Minimal Classification Examples

Subject-verb agreement classification:

```json
{
  "question_family_key": "conventions_grammar",
  "grammar_role_key": "agreement",
  "grammar_focus_key": "subject_verb_agreement",
  "syntactic_trap_key": "nearest_noun_attraction",
  "secondary_grammar_focus_keys": [],
  "disambiguation_rule_applied": null,
  "classification_rationale": "The true singular subject is separated from the verb by a plural intervening noun."
}
```

Expression of Ideas transition classification:

```json
{
  "question_family_key": "expression_of_ideas",
  "grammar_role_key": "expression_of_ideas",
  "grammar_focus_key": "transition_logic",
  "answer_mechanism_key": "inference",
  "solver_pattern_key": "evaluate_transition",
  "classification_rationale": "The correct answer supplies the logical relationship between adjacent claims."
}
```

No-change metadata:

```json
{
  "is_no_change_question": true,
  "original_text_option_label": "A",
  "original_text_is_correct": true
}
```

## 25. Boundaries Decision Tree & Anti-Trap Rules

### Punctuation Decision Tree

Apply this framework for every Boundaries question during both classification and generation:

| Condition before blank | Condition after blank | Correct punctuation |
| ---------------------- | --------------------- | ------------------- |
| Independent Clause | Independent Clause | `.` or `;` or `, FANBOYS` |
| Independent Clause | List / Explanation / Elaboration | `:` or `—` |
| Independent Clause—extra info— | rest of Independent Clause | paired `, ... ,` or paired `— ... —` |
| Dependent Clause | Independent Clause | `,` |
| Independent Clause | Dependent Clause | no punctuation (usually) |
| Independent Clause | Independent Clause with conjunctive adverb | `; [adverb],` |

### Anti-Trap Rules

The following are NEVER correct on the DSAT. Any option matching these must be eliminated:

1. **Semicolon-Period Equivalence Trap**: If both a period and a semicolon appear as options with no other difference, BOTH are wrong. The DSAT never asks you to choose between interchangeable punctuation.

2. **Colon After Verb**: A colon must not follow a verb ("The species observed were: hawks..."). Eliminate immediately.

3. **Colon After Preposition**: A colon must not follow a preposition ("The study focused on: sleep..."). Eliminate immediately.

4. **Colon After Introducer Words**: *including, such as, like* must NEVER be followed by a colon. They already serve as introducers.

5. **Single Comma Between Subject and Verb**: A subject and its verb can be separated by 0 comma or 2 commas (non-essential clause), NEVER by exactly 1 comma. Example: "The oldest surviving bridge in London, is Richmond Bridge" is always wrong.

6. **Mismatched Paired Punctuation**: Opening with a dash and closing with a comma (or vice versa) is always wrong. Paired punctuation must match: both dashes or both commas.

7. **Semicolon Connecting IC to DC**: A semicolon must join two independent clauses. If either side is a dependent clause, the semicolon is wrong. Apply the "replace with period" test.

8. **Colon After Incomplete Clause**: What precedes a colon MUST be a complete independent clause. If the text before the colon can't stand as a sentence, the colon is wrong.

### Clause-Type Identification Quick Reference

| Clause Type | Signal Words | Can Stand Alone? |
| ----------- | ------------ | ----------------- |
| Independent (IC) | (none required) | Yes |
| Dependent (DC) | *although, because, when, which, who, if, since, while, whereas, unless, until, after, before, that* | No |
| Fragment | Missing subject or verb | No |

Every Boundaries question is fundamentally testing whether you can distinguish ICs from DCs and apply the Decision Tree mechanically.

## 26. Form, Structure, and Sense — Edge Case Appendix

Use these edge cases to construct authentic high-difficulty items and to validate classification accuracy.

### Collective Nouns

SAT treats all collectives as **singular** (requiring singular verbs and pronouns):

- *team, committee, jury, company, audience, staff, faculty, class, government, band, family, group, flock, herd, swarm*

Pattern: "The [collective noun] of [plural noun] [singular verb]..." — the subject is the collective, not the plural noun in the prepositional phrase.

Exception (rarely tested): collective as plural only when individuals act separately ("The jury disagree among themselves"). When in doubt, treat as singular.

### Inverted Sentences — 3 Patterns

1. **Prepositional Fronting**: "On my forehead reside five unsightly pimples." → Un-invert: "Five pimples reside on my forehead." The subject follows the verb.

2. **There-is/are Constructions**: "There are three reasons for the delay." Subject = *reasons* (plural). "There is one reason" → singular. The subject always follows the verb.

3. **Linking Verb Inversion**: "Less fun are its consequences." → Un-invert: "Its consequences are less fun."

Strategy: mentally restore normal subject→verb→complement order. The subject is NEVER inside a prepositional phrase.

### Tricky Singular Subjects (Always Singular on the SAT)

| Subject Pattern | Example | Rule |
| --------------- | ------- | ---- |
| *Each* | Each of the members **is** | Always singular |
| *Every / Everyone / Everybody* | Every person **is** | Always singular |
| Gerunds as subjects | Remembering all the names **is** | Always singular |
| Titles of works | *The Canterbury Tales* **has inspired** | Always singular (even if title is plural) |
| *The number of* | The number of applicants **is** | Singular |
| *A number of* | A number of issues **need** | Plural |
| Indefinite pronouns | Everyone/each/someone/anyone/no one | Always singular |

### Compound Subjects — Or/Nor Proximity Rule

- *And*: Always plural ("Justin and the SAT **are** friends.")
- *Or / Nor*: Verb agrees with subject **closest to the verb** ("Either the actors or the director **is** preparing." / "Either the director or the actors **are** preparing.")

### Possessive / Contraction Confusion Matrix

| Contraction | Possessive | Test |
| ----------- | ---------- | ---- |
| *it's* (it is) | *its* | Replace with "it is" — if sentence works, contraction is correct |
| *who's* (who is) | *whose* | Replace with "who is" |
| *they're* (they are) | *their* | Replace with "they are" |
| *you're* (you are) | *your* | Replace with "you are" |

Nonstandard forms (*its', who'se*) appear only as distractors.

### Plural-Form Words That Are Singular

- *News, measles, mumps, physics, mathematics, economics* — singular: "The news **is** alarming."
- *Politics, economics* — can be either depending on meaning: "Politics **is** a challenging field" (single topic) vs. "Her politics **are** controversial" (multiple views).

### Pronoun Agreement — Singular "They" Stance

Historically, the SAT has NOT accepted singular "they." Items testing pronoun-antecedent agreement with indefinite antecedents (*everyone, each, someone*) require *"he or she,"* *"his or her,"* or a gendered singular pronoun from context. 

**Note**: Verify current Bluebook stance by inspecting most recent official tests (PT7-PT10). If College Board has shifted, update this rule.

### Relative Pronoun Selection

| Pronoun | Use For |
| -------- | ------- |
| *who / whom* | People only |
| *which* | Things, animals, ideas (nonessential clauses) |
| *that* | Things, animals, ideas (essential clauses) |
| *where* | Physical locations only |
| *in which* | Abstract settings, books, media, societies, time periods |

Common trap: "a society **where** technology has eliminated privacy" → should be "a society **in which**..."

### Ambiguous Reference — "This / That / Which"

These pronouns need a **specific circled noun** — they cannot refer to an entire clause or idea:

- "Maria studied for 12 hours, **which** impressed her friends." → *Which* has no specific antecedent. Fix: "...a commitment that impressed her friends."

### One vs. You — Consistency Trap

Never shift person mid-sentence:

- "If **one** wants to succeed, **one** must practice." (not "you must practice")
- "If **you** want to succeed, **you** must practice." (not "one must practice")

Both are acceptable individually; mixing them is always wrong.

## 27. Authenticity Anti-Patterns

These rules prevent the most common failure modes that make AI-generated questions feel "off" compared to official College Board items.

### Structural Authenticity Rules

1. **All four options must produce coherent, meaningful sentences.** The difference between them must be structural (grammar/punctuation/logic), not semantic. If one option is gibberish while others are coherent, the item fails authenticity.

2. **Distractors must represent common student misconceptions.** Every wrong option must be traceable to a documented student failure mode (from Section 18 tables). Random errors, malformed English, or "trick" wording that no real student would choose are forbidden.

3. **Question phrasing must be standardized.** The stem text must match one of the approved stem_type_key formulations. Never invent a new stem wording without the amendment process. The default grammar stem is:
   > "Which choice completes the text so that it conforms to the conventions of Standard English?"

4. **Grammar must be tested in prose context.** Never present grammar as isolated rule identification. Even `sentence_only` items embed the target rule in a complete, self-contained sentence with authentic academic content.

5. **Topic distribution should match College Board content domains.** Mix passages across Literature, History/Social Studies, Humanities, and Science. Avoid over-concentration in any single domain within a batch.

### Distractor Authenticity Rules

6. **No option should be visibly longer, safer, or more polished than the rest.** Option length and register must be uniform. A correct answer that is obviously the shortest (in concision items) or the most formal is acceptable only when those properties ARE the construct being tested.

7. **Every distractor must be independently plausible.** A student who doesn't know the rule should find each distractor at least somewhat tempting. Implausible distractors produce artificially low difficulty.

8. **Precision score 2 options must be rare and intentional.** These are grammatically valid but suboptimal answers (e.g., a period where a semicolon is better). Use only when the SAT construct requires recognizing degrees of effectiveness. Document the reason in `why_wrong`.

### Passage Authenticity Rules

9. **Passages must read as authentic edited prose.** No placeholder names ("John Smith"), no generic descriptions ("a recent study"), no template artifacts. Use realistic proper nouns, plausible research scenarios, and specific-but-accessible academic content.

10. **No answer should depend on "which sounds right."** Every classification and generation must be deterministically traceable to an explicit rule in Sections 5-9. If the correct answer feels arbitrary without the rule, the item fails.

11. **Vocabulary must be SAT-appropriate.** Use tier-2 academic vocabulary that appears in authentic College Board passages. Avoid obscure/niche terms that test vocabulary knowledge rather than grammar. Avoid colloquial/casual terms that break formal register.

12. **Evidence span text must be mechanically extractable.** The correct answer's evidence must be isolatable to a specific span of the passage text. If the evidence is "the whole sentence" for every item, the distractors are insufficiently targeted.

### Quantitative Authenticity Targets

13. **Distractor competition scores**: Minimum 0.65 per distractor for medium difficulty; minimum 0.80 per distractor for high difficulty. If using V1+V2 combined loading, target 0.85+ average distractor competition.

14. **Ready-for-use rate**: Target >=90% of generated items passing full validation without repair-loop intervention. Document repair frequency per focus key to identify weak heuristics.

## 28. 2025-2026 DSAT Trends & Forward Guidance

These reflect observations from recent DSAT administrations and should inform generation strategy. They are guidance, not rigid constraints.

### Observed Trends

1. **Poetry passages** appear more frequently than in early DSAT versions. Questions focus on overall theme, tone, and figurative language (metaphor, personification). Trap answers are more prevalent. When generating poetry-based items, ensure the grammar module routes the classification correctly (poetry + grammar = rare but possible; poetry + Expression of Ideas = more common).

2. **Table-based questions** are now standard at 2-3 per module. These require rapid, accurate data retrieval rather than deep logical inference. Focus on speed and precision in distractor design.

3. **Module 1 has been slightly simplified.** Module 2 is significantly harder. A mistake in Module 1 can cost up to 30 points. This affects difficulty calibration: M1 items should cluster at low-medium; M2 items should cluster at medium-high with genuine high-difficulty spikes.

4. **Passage length** is trending to 110-120 words for logical completion items. Sentence-only grammar items remain at 20-40 words. Update passage_length_words targets accordingly.

5. **Scientific reasoning and experimental analysis** skills are increasingly tested. Passages from cognitive psychology, economics, and linguistics appear more frequently. Favor these topic domains over generic humanities passages for grammar items when the target difficulty is medium or high.

6. **Punctuation and sentence structure** questions are becoming more intricate. High-difficulty punctuation items now routinely test nuanced distinctions (colon vs. semicolon when both join ICs; dash pairs vs. comma pairs for non-essential elements).

### Items REMOVED from Paper SAT (Not Tested on DSAT)

Do not generate or classify items targeting these removed subtopics:
- Frequently confused words (e.g., *accept/except, affect/effect*) — not a separate DSAT testing point
- Conventional expression / idioms (e.g., *"prefer X over Y"* vs. *"prefer X to Y"*) — not tested unless covered by an approved focus key
- U.S. founding documents / Great Global Conversation passages — not a formal DSAT passage requirement
