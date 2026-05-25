# DSAT Grammar Module

## 1. Purpose

This file defines the grammar domain taxonomy, generation rules, annotation
rules, and validation contract. It covers:

- **Standard English Conventions** (SEC): Boundaries, Form/Structure/Sense
- **Expression of Ideas** (grammar-adjacent): Transitions, Rhetorical Synthesis

Load `rules_core_generation.md` before this module. Core owns the shared output
shape, option contract, distractor engineering rules, SAT realism layer,
difficulty calibration rubric, provenance, anti-clone, and batch/error formats.
This module owns grammar-specific taxonomy, passage construction, distractor
heuristics, syntactic traps, no-change rules, tense/register metadata, and
grammar validation.

**Source file**: `rules_agent_dsat_grammar_ingestion_generetion_v7.md`

---

## 2. Grammar Mode Routing

### 2.1 Task Mode Detection

**Generation Mode** — triggered when the request:
- contains a `generation_request` with `domain: "grammar"`
- specifies a `target_grammar_focus_key` and asks for a new item
- asks to "generate," "create," or "write" a new grammar question

**Annotation / Ingestion Mode** — triggered when the request:
- provides question text and answer options to classify
- asks to "annotate," "ingest," "classify," or "review" an existing item

### 2.2 Test Format Keys

| `test_format_key` | Module length | When to use |
|---|---|---|
| `digital_app_adaptive` | 27 questions | Default; standard Bluebook adaptive |
| `nondigital_linear_accommodation` | 33 questions | Paper accommodation; PT4–PT11 source tests |

### 2.3 `source_stats_format` values

| Value | Description |
|---|---|
| `official_digital` | Position statistics from Bluebook adaptive modules |
| `official_nondigital_linear` | Position statistics from PT4–PT11 paper accommodation |

When `test_format_key` is `nondigital_linear_accommodation`, use 33 questions
and these domain-band position ranges:
```
Reading / Craft / Information:     Q1–Q18  (+/-1)
Standard English Conventions:      Q19–Q26 (+/-1; may start as late as Q18 in M2)
Transitions:                        Q27–Q30 (variable; 1–5 items)
Notes Synthesis:                    Q30–Q33 (variable start; always ends at Q33)
```

---

## 3. Grammar Generation

### 3.1 Generation Input

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
    "stem_type_key": "complete_the_text",
    "avoid_recent_exam_ids": ["PT4", "PT5"],
    "generation_context": "Module needs two more medium-difficulty items.",
    "test_format_key": "digital_app_adaptive",
    "source_stats_format": "official_digital"
  }
}
```

Mandatory fields: `target_grammar_focus_key`, `target_grammar_role_key`,
`target_frequency_band`, `difficulty_overall`, `test_format_key`,
`stimulus_mode_key`, `stem_type_key`.

Reject any request that uses an unapproved `grammar_focus_key`, maps a focus
key to the wrong role, or requests a `very_low` frequency item without
explicit justification.

### 3.2 Generation Workflow

1. Validate request keys against approved grammar taxonomy.
2. Build passage/sentence. Ensure the correct answer is *required*.
3. Build stem using approved stem wording.
4. Pre-answer before generating options.
5. Generate correct option (including no-change if applicable).
6. Generate three distractors from explicit failure modes.
7. Normalize option set for length, register, grammatical frame.
8. Assemble metadata, reasoning, generation profile, provenance, review.
9. Run core validation.
10. Run grammar validation.
11. Retry failed component or return structured error after 3 attempts.

---

## 4. Passage Construction Rules by Grammar Focus

### 4.1 `subject_verb_agreement`
Insert a prepositional phrase or relative clause between the subject and the
blank so the nearest noun disagrees in number with the true subject. Use
collective nouns (team, committee, jury, group), inverted sentences, or
singular subjects ending in -s (analysis, crisis, species). For
`nearest_noun_attraction`, place a plural noun immediately before the blank.

### 4.2 `pronoun_antecedent_agreement`
Ensure the antecedent is separated from the pronoun by at least one clause
or a competing noun phrase. Embed the antecedent in a structure where another
noun of different number/gender sits closer to the pronoun blank.

### 4.3 `verb_tense_consistency`
Establish a clear temporal anchor in the passage (e.g., "In the 19th century,"
"Before the discovery of..."). Place competing time-marker phrases near the
blank to create `tense_proximity_pull`. For tense-sequence items, embed the
blank in reported speech or a conditional subordinate clause.

### 4.4 `modifier_placement` / `dangling_modifier`
Open with a participial phrase (-ing or -ed) or prepositional modifier
describing an agent that must appear immediately after the comma. The
distractors place the wrong noun in that position. For `squinting_modifier`,
place an adverb between two clauses either of which it could modify.

### 4.5 `punctuation_comma`
Construct sentences where commas either:
- Separate essential from non-essential elements (restrictive vs. non-restrictive clauses)
- Create or prevent a comma splice
- Mark items in a complex series
- Interact with introductory phrases

For `comma_boundary_camouflage`, wrap the boundary in an interrupting
parenthetical so the true clause break is visually obscured.

### 4.6 `semicolon_use`
Build two independent clauses with a strong logical connection. Use internal
commas in at least one clause so a comma-only join looks plausible. For
conjunctive-adverb semicolons, use `however`, `therefore`, `moreover`,
`consequently`, `nevertheless`, or `indeed`.

### 4.7 `apostrophe_use`
Construct possessives where the owning noun is a phrase (not a single word)
or plural possessives ending in s'. Include possessive/contraction homophones
(its/it's, whose/who's, their/they're) in distractor sets.

### 4.8 `appositive_punctuation`
Embed a noun-phrase appositive at mid-sentence. Vary whether it is essential
(no commas) or non-essential (paired commas or dash pair). Place proper
nouns as non-essential appositives after a descriptive noun.

### 4.9 `relative_pronouns`
Use "which" for non-restrictive clauses (preceded by a comma), "that" for
restrictive clauses (no comma). Include contexts where "who"/"whom" or
preposition + "which"/"whom" is tested.

### 4.10 `colon_dash_use`
Construct sentences where an independent clause is followed by a list,
explanation, or elaboration. The colon requires a complete independent
clause before it; a dash can follow a fragment. Test colon vs. dash vs.
comma in list-introduction contexts.

### 4.11 `conjunctive_adverb_usage`
Build two independent clauses joined by a conjunctive adverb. Test correct
punctuation (semicolon before, comma after the adverb) vs. comma-splice,
period-split, or missing-comma patterns.

### 4.12 `parallel_structure`
Create lists, paired conjunctions (both/and, either/or, neither/nor,
not only/but also), or comparison structures requiring matched grammatical
forms. Embed one non-parallel distractor that is plausible in isolation.

### 4.13 `pronoun_case`
Place the pronoun in a compound object or after a preposition where case is
tested. Use structures like "between you and ___" or comparatives where the
implied verb after the pronoun determines case (e.g., "taller than I [am]").

### 4.14 `pronoun_clarity`
Construct a sentence with two or more potential antecedents of the same
number/gender. The correct answer either repeats the noun or restructures the
sentence to remove ambiguity.

### 4.15 `possessive_contraction`
Position a possessive/contraction homophone pair (its/it's, whose/who's,
their/they're, your/you're) at the blank. The passage context must
disambiguate which is required.

### 4.16 `hyphen_usage`
Construct compound modifiers before a noun where hyphenation distinguishes
meaning (e.g., "small business owner" vs. "small-business owner").

### 4.17 `logical_predication`
Create a sentence where the subject and predicate are semantically
incompatible in one or more options (e.g., "the price of goods was
alleviated" vs. "the price of goods was increased").

### 4.18 `comparative_structures`
Build comparisons using "than" or "as...as" where the two elements must
be logically parallel. Test illogical comparisons (e.g., comparing a thing
to a person or an action to a noun).

### 4.19 `unnecessary_internal_punctuation`
Place a blank between a subject and verb, verb and object, or preposition
and object. Any punctuation inserted creates an error. Distractors insert
commas, dashes, or colons that would "feel" natural at a pause point.

### 4.20 `end_punctuation_question_statement`
Construct an indirect question (e.g., "The researchers asked whether the
results were replicable.") where a question mark distractor is tempting.

### 4.21 `finite_verb_in_relative_clause`
Embed a relative clause where the finite verb form is tested against
participles (-ing/-ed) or infinitives that would create fragments.

### 4.22 `finite_verb_in_main_clause`
Construct a sentence where a main-clause verb is tested against a verbal
noun (gerund) or participle in the subject position, making the fragment
option look structurally plausible.

### 4.23 `modal_plus_plain_form`
Place a modal auxiliary (can, could, will, would, shall, should, may, might,
must) before the blank. The correct answer is the plain form; distractors
use inflected forms (past tense, third-person singular -s).

### 4.24 `sentence_fragment`
Construct a passage where the correct option supplies a finite verb to
complete the main clause. Distractors offer participial or infinitival
phrases that read like natural continuations but leave the sentence
verbless.

### 4.25 `comma_splice`
Build two independent clauses with a comma between them. The correct answer
replaces the comma with a semicolon, period, or coordinating conjunction +
comma. Distractors offer comma-only or comma + non-coordinating adverb.

### 4.26 `run_on_sentence`
Join two independent clauses with no punctuation or conjunction. The correct
answer inserts a period, semicolon, or comma + FANBOYS conjunction.

### 4.27 `noun_countability`
Use nouns that switch countability (e.g., "research" is uncountable; "study"
is countable). Test "less" vs. "fewer," "amount" vs. "number," "much" vs. "many."

### 4.28 `determiners_articles`
Construct contexts where article/determiner choice (a, an, the, no article)
signals definiteness or countability. Include contexts where a possessive
determiner or quantifier competes with an article.

### 4.29 `affirmative_agreement`
*(dsat_confidence: low — ACT-adjacent; exclude from generation weighting)*

Use "so"/"too"/"neither"/"nor" + auxiliary inversion patterns.

### 4.30 `voice_active_passive`
Construct a sentence where active vs. passive voice changes the logical
subject performing the action. The passage context dictates which is correct.

### 4.31 `negation`
*(dsat_confidence: low — ACT-adjacent)*

Build negation structures where double-negation or scope-of-negation issues
create ambiguity.

### 4.32 `quotation_punctuation`
Embed quoted material where comma/period placement relative to quotation
marks is tested.

### 4.33 `transition_logic`
Build a paragraph with a clear logical relationship (cause/effect, contrast,
addition, sequence, example, emphasis, restatement) between sentences. The
blank is a transition word or phrase. Passages must supply enough context that
only one transition subtype is correct.

### 4.34 `rhetorical_synthesis` (`choose_best_notes_synthesis`)
Build notes bullets that contain overlapping but distinct information. The
correct synthesis selects some bullets (not necessarily all) to meet a
specific goal directed to a specific audience. Distractors include all
bullets indiscriminately, select wrong bullets, or misrepresent the goal.

---

## 5. Distractor Generation Heuristics by Grammar Focus

### 5.1 `subject_verb_agreement`
| Distractor pattern | Trap |
|---|---|
| Plural verb matching nearest (plural) noun | `nearest_noun_attraction` |
| Singular verb where plural is needed (or reverse) | `nearest_noun_attraction` |
| Verb matching a modifier's number | `modifier_hitchhike` |
| Verb matching an inverted subject's apparent number | `nearest_noun_reflex` |

### 5.2 `verb_tense_consistency`
| Distractor pattern | Trap |
|---|---|
| Tense matching a nearby time-marker clause | `tense_proximity_pull` |
| Perfect form where simple past is correct (or reverse) | `chronological_assumption` |
| Present tense distractor in a past-tense passage | `register_confusion` |
| Progressive form where simple is correct | `longer_answer_bias` |

### 5.3 `punctuation_comma`
| Distractor pattern | Trap |
|---|---|
| Comma before a restrictive clause | `comma_fix_illusion` |
| Missing comma before a non-restrictive clause | `ear_test_pass` |
| Comma between subject and verb | `punctuation_intimidation` |
| Comma after FANBOYS where period is correct | `surface_similarity_bias` |

### 5.4 `semicolon_use`
| Distractor pattern | Trap |
|---|---|
| Comma between independent clauses (comma splice) | `comma_fix_illusion` |
| Period splitting logically connected clauses | `punctuation_intimidation` |
| Colon where semicolon is correct | `formal_word_bias` |
| Comma + FANBOYS where semicolon alone is tighter | `surface_similarity_bias` |

### 5.5 `apostrophe_use`
| Distractor pattern | Trap |
|---|---|
| Singular possessive where plural is needed (or reverse) | `nearest_noun_reflex` |
| Contraction form where possessive is correct | `possessive_contraction_confusion` |
| Bare plural (-s only) where possessive plural (-s') is needed | `ear_test_pass` |
| Possessive pronoun competing with contraction | `idiom_memory_pull` |

### 5.6 `modifier_placement`
| Distractor pattern | Trap |
|---|---|
| Noun nearest the comma as implied subject | `nearest_noun_reflex` |
| Agent placed after a prepositional interruption | `scope_blindness` |
| Correct noun but wrong modifier form | `modifier_hitchhike` |
| Passive voice hiding the misplaced modifier | `formal_word_bias` |

### 5.7 `relative_pronouns`
| Distractor pattern | Trap |
|---|---|
| "which" without comma (restrictive context) | `comma_fix_illusion` |
| "that" after comma (non-restrictive context) | `ear_test_pass` |
| "who" where "whom" is correct (or reverse) | `register_confusion` |
| Preposition stranded (ending with preposition) | `formal_word_bias` |

### 5.8 `colon_dash_use`
| Distractor pattern | Trap |
|---|---|
| Colon after incomplete clause | `punctuation_intimidation` |
| Dash where colon is formally expected | `formal_word_bias` |
| Comma instead of colon before list | `comma_fix_illusion` |
| Semicolon instead of colon before elaboration | `surface_similarity_bias` |

### 5.9 `appositive_punctuation`
| Distractor pattern | Trap |
|---|---|
| Commas around essential (restrictive) appositive | `comma_fix_illusion` |
| No commas around non-essential appositive | `ear_test_pass` |
| Single comma (unpaired) before non-essential appositive | `punctuation_intimidation` |
| Dash pair where commas are correct | `formal_word_bias` |

### 5.10 `parallel_structure`
| Distractor pattern | Trap |
|---|---|
| One non-parallel form in a matched series | `parallel_shape_bias` |
| Gerund where infinitive is needed (or reverse) | `surface_similarity_bias` |
| Active where passive is required for parallelism | `register_confusion` |
| Missing auxiliary in paired structure | `ear_test_pass` |

### 5.11 `pronoun_case`
| Distractor pattern | Trap |
|---|---|
| Subject pronoun in object position (or reverse) | `register_confusion` |
| "who" where "whom" is correct (or reverse) | `formal_word_bias` |
| Reflexive pronoun where object pronoun is correct | `idiom_memory_pull` |
| "I" where "me" is correct in compound | `ear_test_pass` |

### 5.12 `conjunctive_adverb_usage`
| Distractor pattern | Trap |
|---|---|
| Comma before conjunctive adverb (comma splice) | `comma_fix_illusion` |
| Missing comma after conjunctive adverb | `ear_test_pass` |
| Period where semicolon is better for connected ideas | `punctuation_intimidation` |
| FANBOYS conjunction where conjunctive adverb is correct | `transition_assumption` |

### 5.13 `unnecessary_internal_punctuation`
| Distractor pattern | Trap |
|---|---|
| Comma between subject and verb | `ear_test_pass` |
| Comma between verb and object | `comma_fix_illusion` |
| Comma between preposition and object | `punctuation_intimidation` |
| Dash between modifier and modified word | `formal_word_bias` |

### 5.14 `end_punctuation_question_statement`
| Distractor pattern | Trap |
|---|---|
| Question mark on indirect question | `surface_similarity_bias` |
| Period where embedded question ends sentence | `punctuation_intimidation` |

---

## 6. Transition Subtype Vocabulary

### 6.1 `transition_subtype_key` field

Required for every `transition_logic` item. Classifies the logical
relationship the correct transition word encodes.

### 6.2 Approved `transition_subtype_key` values

| Value | Relationship | Example words |
|---|---|---|
| `addition` | Adds supporting information | moreover, furthermore, additionally, also, in addition |
| `contrast` | Opposes or qualifies a preceding idea | however, but, yet, nevertheless, on the other hand, conversely, in contrast, still, though, although, even so, nonetheless |
| `cause_effect` | One idea causes or results from another | therefore, consequently, as a result, thus, hence, accordingly, so |
| `sequence` | Temporal or procedural ordering | subsequently, previously, initially, ultimately, eventually, first, next, finally, then |
| `example` | Provides a specific instance | for example, for instance, in particular, specifically, namely, that is |
| `emphasis` | Reinforces or intensifies a preceding idea | indeed, in fact, as a matter of fact, undoubtedly, certainly |
| `restatement_clarification` | Restates or explains in different terms | in other words, that is to say, to put it differently, more precisely, i.e., namely |
| `concession` | Acknowledges a counterpoint before pivoting | granted, admittedly, to be sure, certainly, of course |
| `comparison` | Points out similarity | similarly, likewise, in the same way, by the same token, analogously |

---

## 7. Notes Synthesis Metadata

### 7.1 Required fields for `choose_best_notes_synthesis` items

Every notes-based rhetorical synthesis item must include:
- `notes_bullets` (3-7 items)
- `synthesis_goal_key`
- `audience_knowledge_key`
- `required_content_key`

### 7.2 Approved `synthesis_goal_key` values

| Value | Meaning |
|---|---|
| `compare_contrast` | Highlight similarities or differences between items |
| `support_claim` | Use notes to support a specific argumentative claim |
| `explain_cause` | Explain why or how something occurred |
| `describe_sequence` | Describe a process or sequence of events |
| `profile_subject` | Provide an overview of a person, place, or phenomenon |
| `propose_solution` | Frame findings as addressing a specific problem |
| `highlight_implication` | Emphasize what a finding implies for a broader context |

### 7.3 Approved `audience_knowledge_key` values

| Value | Meaning |
|---|---|
| `general_audience` | No specialized knowledge assumed |
| `informed_nonspecialist` | Some familiarity with the domain but not expert |
| `specialist` | Domain-knowledgeable audience |

### 7.4 Approved `required_content_key` values

| Value | Meaning |
|---|---|
| `all_bullets` | Every bullet must appear in the synthesis |
| `selective` | Only some bullets should appear; the goal + audience determines which |
| `compare_key_bullets` | Two or more bullets must be explicitly compared |
| `synthesize_generalization` | Bullets are woven into a general statement; no one-to-one mapping |

---

## 8. Passage Architecture Templates

| `passage_architecture_key` | Structure |
|---|---|
| `science_setup_finding_implication` | Topic intro → research finding → implication/consequence |
| `science_hypothesis_method_result` | Hypothesis → method → result → interpretation |
| `history_claim_evidence_limitation` | Historical claim → supporting evidence → limitation/complication |
| `history_assumption_revision` | Initial assumption → new evidence → revised understanding |
| `literature_observation_interpretation_shift` | Character observation → initial interpretation → later shift |
| `literature_character_conflict_reveal` | Character description → situation → conflict/contradiction reveals character |
| `economics_theory_exception_example` | Economic theory → apparent contradiction → example resolves |
| `economics_problem_solution_tradeoff` | Problem → proposed solution → tradeoff or unintended consequence |
| `rhetoric_claim_counterclaim_resolution` | Claim → counterclaim/objection → resolution/synthesis |
| `notes_fact_selection_contrast` | Bulleted facts → goal-directed selection → contrast between included/excluded |
| `research_summary` | Broad research context → specific study → key result |
| `claim_evidence_explanation` | Claim statement → evidence → explanation of how evidence supports claim |
| `unexpected_finding` | Expected outcome → actual (surprising) result → explanation |
| `cautionary_framing` | Promising finding → limitation/caution → tempered conclusion |
| `problem_solution` | Problem statement → attempted solution(s) → evaluation |
| `compare_contrast` | Two phenomena/approaches → similarities → differences → resolution |
| `chronological_sequence` | Early state → intermediate change → current state |

---

## 9. No-Change Generation Rules

A no-change option (option text: "NO CHANGE" or identical to the original
underlined/blanked text in the passage) is allowed for:

- `stem_type_key: "complete_the_text"` — the original passage text is one of the four options, labeled as is (not "NO CHANGE")
- `stem_type_key: "choose_best_grammar_revision"` — one option may represent leaving the sentence as-is

Use no-change options primarily for:
- `punctuation_comma` (the passage may be correct without added commas)
- `apostrophe_use` (possessive/contraction correctness may already be right)
- `transition_logic` (the original transition may be correct)

No-change metadata:
```json
{
  "no_change_option": {
    "is_no_change_option": true,
    "original_passage_text_at_blank": "..."
  }
}
```

The correct option may be the no-change option. When it is, `precision_score: 3`
applies. Do not use "NO CHANGE" as literal text; represent the original passage
text as a regular option and mark it with `is_no_change_option: true`.

---

## 10. Grammar Taxonomy Reference

### 10.1 Grammar Role Keys

| `grammar_role_key` | Domain |
|---|---|
| `sentence_boundary` | SEC — Boundaries |
| `agreement` | SEC — Form, Structure, and Sense |
| `verb_form` | SEC — Form, Structure, and Sense |
| `modifier` | SEC — Form, Structure, and Sense |
| `punctuation` | SEC — Boundaries |
| `parallel_structure` | SEC — Form, Structure, and Sense |
| `pronoun` | SEC — Form, Structure, and Sense |
| `expression_of_ideas` | Expression of Ideas |

#### Role descriptions:

**`sentence_boundary`**: The item tests how clauses are joined, separated,
or bounded — comma splices, run-ons, fragments, semicolons, colons, dashes,
period placement. If the primary tested skill is whether a sentence boundary
exists or is punctuated correctly, use `sentence_boundary`.

**`agreement`**: Subject-verb agreement, pronoun-antecedent agreement,
noun-number agreement. The primary skill is matching grammatical features
across constituents.

**`verb_form`**: Verb tense, aspect, mood, finite vs. non-finite forms,
modal + plain form, tense sequence in reported speech.

**`modifier`**: Modifier placement, dangling modifiers, squinting modifiers,
modifier logic (illogical comparisons, logical predication).

**`punctuation`**: Internal punctuation mechanics — commas, semicolons,
colons, apostrophes, dashes, hyphens, quotation marks. Use when the primary
skill is applying a punctuation rule (not boundary creation per se).

**`parallel_structure`**: Matched grammatical forms in series, paired
conjunctions, or comparisons.

**`pronoun`**: Pronoun case, clarity, and selection (not pronoun-antecedent
agreement — that goes under `agreement`).

**`expression_of_ideas`**: Transitions, rhetorical synthesis (notes to prose),
precision/word choice, register/style, redundancy/concision, emphasis/meaning
shifts, data interpretation claims. Items test rhetorical effectiveness,
not strictly grammatical correctness.

### 10.2 Grammar Focus Keys

#### Sentence boundary focus keys
- `comma_splice`
- `run_on_sentence`
- `sentence_fragment`
- `semicolon_use` — also serves as a boundary mechanism (semicolon joins independent clauses)
- `colon_dash_use` — colon/dash as boundary markers between clauses
- `end_punctuation_question_statement`

#### Agreement focus keys
- `subject_verb_agreement`
- `pronoun_antecedent_agreement`
- `noun_countability` — "less" vs. "fewer," "amount" vs. "number," "much" vs. "many"

#### Pronoun focus keys
- `pronoun_case` — I/me, who/whom, etc.
- `pronoun_clarity` — ambiguous reference resolution
- `singular_event_reference` — pronoun referring to a clause/event rather than a noun

#### Verb form focus keys
- `verb_tense_consistency`
- `finite_verb_in_relative_clause`
- `finite_verb_in_main_clause`
- `modal_plus_plain_form`

#### Modifier focus keys
- `modifier_placement` — dangling/misplaced modifiers
- `logical_predication` — semantically incompatible subject-predicate pairs
- `comparative_structures` — illogical comparisons, comparative logic
- `adjective_adverb_distinction`
- `illogical_comparison`

#### Punctuation focus keys
- `punctuation_comma`
- `apostrophe_use`
- `appositive_punctuation`
- `relative_pronouns` — which/that/who, restrictive vs. non-restrictive (punctuation dimension)
- `unnecessary_internal_punctuation`
- `possessive_contraction` — possessive/contraction homophones (its/it's, whose/who's)
- `hyphen_usage`
- `quotation_punctuation`
- `conjunctive_adverb_usage` — punctuation dimension (semicolon + comma with however/therefore etc.)

#### Parallel structure focus keys
- `parallel_structure`

#### Expression of Ideas focus keys
- `transition_logic`
- `rhetorical_synthesis` — notes to prose synthesis
- `precision_word_choice` — selecting the most precise word for context
- `register_style_consistency` — maintaining consistent register/style
- `redundancy_concision` — eliminating wordiness/redundancy
- `emphasis_meaning_shifts` — detecting how word choice shifts meaning/emphasis
- `data_interpretation_claims` — evaluating whether claims match data in notes
- `commonly_confused_words` — non-homophone semantic pairs (e.g., affect/effect, imply/infer)
- `preposition_idiom` — idiomatic preposition use
- `determiners_articles` — article/determiner choice
- `voice_active_passive` — active/passive voice selection
- `affirmative_agreement` — *(dsat_confidence: low)*
- `negation` — *(dsat_confidence: low)*

#### Proposed keys (pending review — not yet in production)
- `elliptical_constructions`

### 10.3 `grammar_role_key` → `grammar_focus_key` Mapping

| `grammar_role_key` | Approved `grammar_focus_key` values |
|---|---|
| `sentence_boundary` | `comma_splice`, `run_on_sentence`, `sentence_fragment`, `semicolon_use`, `colon_dash_use`, `end_punctuation_question_statement`, `conjunctive_adverb_usage` |
| `agreement` | `subject_verb_agreement`, `pronoun_antecedent_agreement`, `noun_countability` |
| `verb_form` | `verb_tense_consistency`, `finite_verb_in_relative_clause`, `finite_verb_in_main_clause`, `modal_plus_plain_form` |
| `modifier` | `modifier_placement`, `logical_predication`, `comparative_structures`, `adjective_adverb_distinction`, `illogical_comparison` |
| `punctuation` | `punctuation_comma`, `apostrophe_use`, `appositive_punctuation`, `relative_pronouns`, `unnecessary_internal_punctuation`, `possessive_contraction`, `hyphen_usage`, `quotation_punctuation`, `conjunctive_adverb_usage` |
| `parallel_structure` | `parallel_structure` |
| `pronoun` | `pronoun_case`, `pronoun_clarity`, `singular_event_reference` |
| `expression_of_ideas` | `transition_logic`, `rhetorical_synthesis`, `precision_word_choice`, `register_style_consistency`, `redundancy_concision`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `commonly_confused_words`, `preposition_idiom`, `determiners_articles`, `voice_active_passive`, `affirmative_agreement`, `negation` |

---

## 11. Syntactic Trap Keys

Thirteen approved values:

1. **`nearest_noun_attraction`** — A nearby noun (often in a prepositional phrase) pulls agreement away from the true subject. Most common trap in SEC.

2. **`early_clause_anchor`** — An early clause/sentence establishes a grammatical expectation that a later blank violates.

3. **`pronoun_ambiguity`** — Two or more potential antecedents of the same number/gender create ambiguity.

4. **`temporal_sequence_ambiguity`** — Multiple time markers create confusion about event ordering, or a time-marker clause near the blank pulls to a tense inconsistent with the broader passage.

5. **`comma_fix_reflex`** — Student reflexively inserts a comma at every "pause" point, even where commas are grammatically wrong (subject-verb, restrictive clauses).

6. **`nonrestrictive_restrictive_confusion`** — Student cannot distinguish whether a modifier/clause is essential (restrictive, no commas) or non-essential (non-restrictive, requires commas).

7. **`fragment_illusion`** — A participial or dependent-clause option reads like a natural continuation but leaves the sentence structurally incomplete.

8. **`boundary_camouflage`** — An interrupting phrase or parenthetical obscures the true clause boundary, making comma splices or run-ons harder to detect.

9. **`homophone_interference`** — Homophones (its/it's, whose/who's, their/they're, your/you're, affect/effect) create plausible wrong answers.

10. **`transition_misdirection`** — Two or more transition words are grammatically acceptable but encode different logical relationships; student selects based on surface continuity rather than logical relationship.

11. **`notes_overinclusion`** — Student selects a synthesis that includes all bullets indiscriminately rather than synthesizing selectively per the goal.

12. **`long_distance_dependency`** — The tested element is separated from its controller by extensive intervening material, taxing working memory.

13. **`multiple`** — More than one trap is active. Use only when truly necessary; prefer a single primary trap.

---

## 12. Disambiguation Rules

When multiple grammar focus keys could apply, apply these rules in priority order:

1. **Punctuation-as-boundary trump**: If a punctuation choice (comma, semicolon, colon, dash, period) directly determines whether a sentence is grammatically complete or spliced, classify under `sentence_boundary`, not `punctuation`.

2. **Agreement over modifier**: If a blank requires both correct number agreement AND correct modifier placement, `agreement` wins when the agreement error alone makes the wrong answers wrong.

3. **Verb form over agreement when tense is the sole driver**: If every option agrees in number but differs in tense/aspect/mood, classify under `verb_form`, not `agreement`.

4. **FSS first, punctuation second**: For items testing subject-verb agreement, pronoun-antecedent agreement, pronoun case, finite/non-finite verb forms, modifier placement, or logical comparison, classify under `Form, Structure, and Sense` (`agreement`, `verb_form`, `modifier`, `pronoun`, or `parallel_structure`), even if the options differ in punctuation. The punctuation difference is a surface artifact of the FSS choice.

5. **Transition over SEC**: When a blank could be resolved by grammar rules OR transition logic, classify under `expression_of_ideas` → `transition_logic` if the primary discriminator is rhetorical/logical, not syntactic.

6. **`pronoun` role split**: `pronoun_antecedent_agreement` → `agreement` role. `pronoun_case` / `pronoun_clarity` / `singular_event_reference` → `pronoun` role.

7. **Non-restrictive commas**: `which` requiring a comma = `punctuation` role, focus = `relative_pronouns`. Non-restrictive appositive requiring paired commas = `punctuation` role, focus = `appositive_punctuation`.

8. **Colon/semicolon disambiguation**: Semicolons joining independent clauses = `sentence_boundary`. Colons introducing lists or explanations following a complete clause = `sentence_boundary`. When colon/semicolon tested primarily as internal punctuation (within a sentence, not creating a boundary between independent clauses), classify under `punctuation`.

9. **Parallel structure over modifier**: If the primary skill is maintaining matched grammatical forms across a series or paired conjunction, classify under `parallel_structure`, not `modifier`.

10. **No-change rule**: A no-change is correct only when the original text is grammatically required. The option text must match the original passage segment exactly.

11. **Preposition + which/whom**: Formal "preposition + which/whom" belongs under `punctuation` with focus `relative_pronouns`, not under `sentence_boundary`.

12. **Multi-error resolution**: When options mix two rule categories, classify by the primary error that distinguishes the correct answer. The secondary error category goes in `secondary_grammar_focus_keys`. The `syntactic_trap_key` names the trap mechanism that makes the primary error hard to detect.

13. **Notes synthesis domain**: `choose_best_notes_synthesis` items always classify under `Expression of Ideas` with focus `rhetorical_synthesis`, never under `Information and Ideas`.

14. **Transition logic domain**: `choose_best_transition` items always classify under `Expression of Ideas` with focus `transition_logic`, never under `Craft and Structure`.

15. **Homophone pairs**: `possessive_contraction` focus (possessive/contraction homophones) and `apostrophe_use` focus (possessive formation) are in `punctuation` role. `commonly_confused_words` focus (non-homophone semantic pairs) is in `expression_of_ideas` role.

16. **Colon-as-evidence vs. colon-as-punctuation**: When the passage contains a colon that provides evidence of the correct answer (e.g., defining a term), the item's `grammar_role_key` is still determined by what the BLANK tests, not by the passage's internal colons.

---

## 13. Grammar Decision Tree

### Step 1: Is this Standard English Conventions?
Does the blank test a rule of English grammar (agreement, verb form, pronoun
selection, modifier logic, parallel structure) or sentence boundary/punctuation
mechanics? If yes → SEC. If the blank tests rhetorical/logical relationships
between ideas → Expression of Ideas.

### Step 2: Is the issue a sentence boundary?
Does the item test how clauses are joined or separated? Look for:
- comma splices, run-ons, fragments
- semicolons joining independent clauses
- periods between sentences
→ If yes: `sentence_boundary`.

### Step 3: Is the issue punctuation mechanics?
Does the item test internal punctuation — commas, apostrophes, appositives,
relative-pronoun punctuation, unnecessary internal punctuation, possessive/
contraction homophones, hyphens, quotation marks, conjunctive-adverb
punctuation? → If yes: `punctuation`.

### Step 4: Is the issue agreement?
Does the item test subject-verb or pronoun-antecedent agreement, or
noun-countability distinctions? → If yes: `agreement`.

### Step 5: Is the issue verb form?
Does the item test tense, aspect, mood, finite/non-finite, or modal + plain
form? → If yes: `verb_form`.

### Step 6: Is the issue modifier logic?
Does the item test modifier placement (dangling/misplaced), logical
predication, or comparison logic? → If yes: `modifier`.

### Step 7: Is the issue pronoun-specific?
Does the item test pronoun case, clarity, or singular event reference
(not pronoun-antecedent agreement)? → If yes: `pronoun`.

### Step 8: Is the issue parallel or idiomatic structure?
→ If yes: `parallel_structure`.

### Step 9: If multiple rules apply
Apply disambiguation rules (§12 above). Record the applied rule in
`disambiguation_rule_applied`.

---

## 14. Tense and Register Keys

### 14.1 `passage_tense_register_key` values

| Value | Description |
|---|---|
| `present_indicative` | Present tense, factual/descriptive register — most common in official SAT |
| `past_narrative` | Past tense narrative — historical topics, literary passages |
| `past_reporting_with_present_implication` | Past-tense reporting (e.g., "researchers found") with present-tense implications |
| `conditional_future` | Conditional or future-oriented statements |
| `present_perfect_continuity` | Present perfect signaling ongoing relevance from past to present |

### 14.2 Expected patterns

For `present_indicative` (most common):
- The passage and correct option are in present tense
- Distractors in past, future, or progressive pull students via `tense_proximity_pull`

For `past_narrative`:
- A temporal anchor (date, historical event) opens the passage
- The correct option is in simple past or past perfect
- Distractors in present or present perfect are tempting

### 14.3 Required fields for verb-form questions

Every item with `grammar_role_key: "verb_form"` must include:
- `passage_tense_register_key`
- Tense consistency across the full passage sentence

---

## 15. Grammar-Specific Rules

### 15.1 Option Text Format Rules

Three format modes for grammar items:

1. **Fill-in-blank**: The option text completes the passage sentence. This is
   the default for `stem_type_key: "complete_the_text"`.

2. **Full-replacement**: For `stem_type_key: "choose_best_grammar_revision"`,
   each option is a complete replacement for the underlined portion.

3. **Punctuation-only**: For punctuation focus keys where the blank contains
   only the punctuation mark(s). The option text may be a single punctuation
   mark (e.g., ";" or ",").

All options for a given item must use the same format mode.

### 15.2 No-Change and Original-Text Rule

When the original passage text is grammatically correct and stylistically
appropriate as-is:
- The option matching the original text is the correct answer.
- Mark it with `is_no_change_option: true`.
- Do not label it "NO CHANGE" unless the stem uses that convention
  (typically `choose_best_grammar_revision` items).
- For `complete_the_text` items, the original segment is one of four regular options.

### 15.3 Multi-Error Rule

When options mix two distinct rule categories, classify by the primary error
that selects the correct answer. Place the secondary category in
`secondary_grammar_focus_keys[0]`. The `syntactic_trap_key` names the trap
mechanism for the primary error.

### 15.4 Evidence Span Selection Rules (Grammar)

- For `sentence_boundary` items: the span includes the clause before the
  boundary, the boundary itself, and the clause after.
- For `agreement` items: the span includes the subject, any intervening
  material, and the verb.
- For `modifier` items: the span includes the modifying phrase and the word
  it modifies.
- For `punctuation` items: the span includes the punctuation mark and the
  immediately surrounding words sufficient to show its function.
- Sentence should be provided in full as `passage_text`.

### 15.5 `secondary_grammar_focus_keys`

Optional field. Populate only when a second grammar focus is genuinely tested
as a secondary discriminator. Do not populate merely because a distractor
accidentally introduces a second error.

### 15.6 `disambiguation_rule_applied` must be explicit

When a disambiguation rule from §12 resolves a classification conflict,
record which rule was applied.

---

## 16. Frequency Table

| Frequency band | `grammar_focus_key` examples |
|---|---|
| `very_high` | `subject_verb_agreement`, `punctuation_comma`, `verb_tense_consistency`, `transition_logic`, `comma_splice`, `run_on_sentence`, `semicolon_use`, `appositive_punctuation` |
| `high` | `pronoun_antecedent_agreement`, `modifier_placement`, `apostrophe_use`, `colon_dash_use`, `parallel_structure`, `relative_pronouns`, `sentence_fragment`, `conjunctive_adverb_usage`, `finite_verb_in_relative_clause` |
| `medium` | `pronoun_case`, `pronoun_clarity`, `logical_predication`, `unnecessary_internal_punctuation`, `finite_verb_in_main_clause`, `modal_plus_plain_form`, `end_punctuation_question_statement`, `comparative_structures`, `possessive_contraction`, `rhetorical_synthesis` |
| `low` | `hyphen_usage`, `quotation_punctuation`, `noun_countability`, `determiners_articles`, `singular_event_reference`, `precision_word_choice`, `register_style_consistency`, `redundancy_concision`, `emphasis_meaning_shifts`, `data_interpretation_claims`, `commonly_confused_words`, `preposition_idiom`, `voice_active_passive` |
| `very_low` | `affirmative_agreement`, `negation` — require explicit justification to generate |

---

## 17. Grammar Validator Checklist

### Generation Validation:
- [ ] `grammar_role_key` and `grammar_focus_key` are approved values
- [ ] `grammar_focus_key` maps to the correct `grammar_role_key` per §10.3
- [ ] `syntactic_trap_key` is one of the 13 approved values
- [ ] At least one functioning distractor per approved distractor heuristic
- [ ] No-change option is present and correctly formatted when applicable
- [ ] `passage_tense_register_key` is present for all verb-form items
- [ ] Tense is consistent across the full passage
- [ ] `transition_subtype_key` is present for all `transition_logic` items
- [ ] `synthesis_goal_key`, `audience_knowledge_key`, `required_content_key`
  are present for all `rhetorical_synthesis` items
- [ ] `notes_bullets` contains 3-7 items for `rhetorical_synthesis`
- [ ] `topic_broad` and `topic_fine` are present
- [ ] Option format mode is consistent across all four options
- [ ] Passage does not contain trivia-dependent or outside-knowledge material
- [ ] `secondary_grammar_focus_keys` is populated only when a second focus is genuinely tested
- [ ] `disambiguation_rule_applied` is recorded when a disambiguation rule resolved a conflict
- [ ] Reading-only keys (`skill_family_key`, `reading_focus_key`, `reasoning_trap_key`,
  `text_relationship_key`) are null or omitted

### Annotation Validation:
- [ ] `grammar_role_key` correctly classified per decision tree
- [ ] `grammar_focus_key` correctly identified and mapped
- [ ] `syntactic_trap_key` correctly identified
- [ ] `disambiguation_rule_applied` recorded if disambiguation was needed
- [ ] No-change status correctly determined
- [ ] `passage_tense_register_key` present for verb-form questions
- [ ] All option-level keys (`distractor_type_key`, `option_error_focus_key`,
  `student_failure_mode_key`) populated per option
- [ ] Correct option has `precision_score: 3` and `grammar_fit: "yes"`, `tone_match: "yes"`
- [ ] Distractors have `precision_score: 1` and documented `why_wrong`
- [ ] `evidence_span_text` and `evidence_location_key` present
- [ ] No two distractors fail for the same reason

---

## 18. Complete Worked Generation Example

### Example A — `subject_verb_agreement`, medium difficulty

**Generation request:**
```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "syntactic_trap_intensity": "high",
  "target_frequency_band": "very_high",
  "difficulty_overall": "medium",
  "topic_broad": "science",
  "topic_fine": "marine biology",
  "stimulus_mode_key": "sentence_only",
  "stem_type_key": "complete_the_text",
  "test_format_key": "digital_app_adaptive"
}
```

**Generated passage:**
> The population of migratory shorebirds, which researchers have tracked across three continents for more than a decade, ______ declined by nearly forty percent since the study began.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

**Options:**
- A: "has" (correct — singular verb agrees with singular subject "population")
- B: "have" (distractor — nearest noun "shorebirds" is plural; `nearest_noun_attraction`)
- C: "having" (distractor — participial form creates fragment; `fragment_illusion`)
- D: "were" (distractor — plural past, wrong number and tense; `nearest_noun_attraction`)

**Classification:**
- `domain`: "Standard English Conventions"
- `skill_family`: "Form, Structure, and Sense"
- `grammar_role_key`: "agreement"
- `grammar_focus_key`: "subject_verb_agreement"
- `syntactic_trap_key`: "nearest_noun_attraction"
- `evidence_scope_key`: "sentence"
- `evidence_location_key`: "main_clause"
- `difficulty_overall`: "medium"
- `difficulty_grammar`: "medium" (long-distance dependency + nearest noun interference)
- Register: `neutral informational`, tone: `objective`

### Example B — `transition_logic`, medium difficulty

**Passage excerpt:**
> In the early twentieth century, physicists assumed that the universe was static and unchanging. ______ Edwin Hubble's observations of galactic redshift in 1929 provided compelling evidence that the universe is expanding, fundamentally reshaping cosmological theory.

**Stem:** Which choice completes the text with the most logical transition?

**Options:**
- A: "However," (correct — contrast between static assumption and expansion evidence)
- B: "Moreover," (distractor — suggests addition/reinforcement; `transition_misdirection`)
- C: "Consequently," (distractor — suggests cause/effect; `transition_misdirection`)
- D: "For example," (distractor — suggests illustration; `transition_misdirection`)

**Classification:**
- `domain`: "Expression of Ideas"
- `question_family_key`: "conventions_transition"
- `grammar_role_key`: "expression_of_ideas"
- `grammar_focus_key`: "transition_logic"
- `transition_subtype_key`: "contrast"
- `syntactic_trap_key`: "transition_misdirection"
- `difficulty_overall`: "medium"

---

## 19. Pilot Annotation Examples

### Example 1: Plural possessive
"The ______ findings were published in Nature." (antecedent: "researchers")
→ `grammar_role_key`: "punctuation", `grammar_focus_key`: "apostrophe_use"

### Example 2: Sentence boundary with interruption
Two independent clauses joined by a comma, parenthetical interrupter masks the splice.
→ `grammar_role_key`: "sentence_boundary", `grammar_focus_key`: "comma_splice"

### Example 3: Essential relative clause
"That" introducing a restrictive clause — no comma.
→ `grammar_role_key`: "punctuation", `grammar_focus_key`: "relative_pronouns"

### Example 4: No punctuation between subject and verb
→ `grammar_role_key`: "punctuation", `grammar_focus_key`: "unnecessary_internal_punctuation"

### Example 5: Period on sentence ending in indirect question
→ `grammar_role_key`: "sentence_boundary", `grammar_focus_key`: "end_punctuation_question_statement"

---

## 20. V3 Research Additions (Carried Forward)

### 20.1 Boundaries Decision Tree & Anti-Trap Rules

#### Structured Punctuation Decision Framework

When classifying a boundary/punctuation item, apply this ordered checklist:

1. **Count the clauses**: How many independent clauses (IC) and dependent clauses (DC)?
2. **Locate the break**: Where does the first IC end and the next clause begin?
3. **Assess the relationship**: Are the ICs logically connected (cause/effect, contrast, restatement)?
4. **Select mechanism**:
   - IC + IC (no conjunction) → period, semicolon, or colon (if second explains first)
   - IC + IC (with FANBOYS) → comma + FANBOYS
   - IC + IC (with conjunctive adverb) → semicolon + adverb + comma
   - IC + DC → no punctuation (restrictive) or comma (non-restrictive)
   - Fragment attempting to be IC → needs subject, finite verb, or both

#### Eight Fatal Anti-Patterns

1. **Comma before "that"**: A comma before a restrictive "that" clause is always wrong on DSAT. Do not generate distractors with this pattern.

2. **Comma between subject and verb**: In the absence of an interrupting non-essential element, no comma may separate subject from verb. This is the single most tested punctuation rule.

3. **Single comma on non-essential**: Non-essential elements require paired commas (or paired dashes/parentheses). A single comma creates an unbalanced punctuation error.

4. **Colon after incomplete clause**: What precedes a colon must be a complete independent clause. Fragment + colon = always wrong.

5. **Semicolon before fragment**: A semicolon may join only independent clauses. Fragment after semicolon = always wrong.

6. **Comma splice**: Two independent clauses joined only by a comma (no FANBOYS) is always wrong on DSAT. This is the most common boundary error tested.

7. **Dash-as-comma confusion**: A single dash cannot replace a pair of delimiting commas. If an appositive opens with a dash, it must close with a dash.

8. **Question mark on indirect question**: An indirect/reported question ends with a period, not a question mark.

### 20.2 Form/Structure/Sense Edge Case Appendix

#### Collective Nouns
- Singular verbs: team, committee, jury, group, family, audience, staff, faculty
- When individuals act separately, plural may be acceptable but SAT strongly prefers singular
- "A number of" takes plural; "the number of" takes singular

#### Inverted Sentences
- Prepositional phrase + verb + subject: "Along the coast ______ several species of penguins."
  Correct: "live" (agreeing with "species" or treated as plural for "several species")

#### Tricky Singular Subjects
- Words ending in -s: analysis, crisis, hypothesis, species, means, series, news, mathematics, physics, politics, economics
- Gerund subjects: "Tracking migratory patterns ______ difficult." → singular "is"
- "Each," "every," "either," "neither" → always singular

#### Or/Nor Proximity
- "Neither the researchers nor the director ______" → agrees with nearest noun ("director" → singular verb)

#### Possessive/Contraction Matrix
| Contraction | Possessive | Meaning |
|---|---|---|
| it's (it is/it has) | its | belonging to it |
| who's (who is/who has) | whose | belonging to whom |
| they're (they are) | their | belonging to them |
| you're (you are) | your | belonging to you |

### 20.3 Authenticity Anti-Patterns

Fourteen rules preventing common AI-generation failure modes:

1. **No unnatural vocabulary**: Do not use rare words (e.g., "obstreperous," "pulchritudinous," "peregrination") to create difficulty. Official SAT uses academic but accessible vocabulary.

2. **No contrived sentence structures**: Do not nest 5+ clauses within a single sentence. Official SAT passages rarely exceed 3 clauses.

3. **No trick-for-trick's-sake**: Every distractor must be a documented student error, not an arbitrary alternative.

4. **No meta-awareness required**: Items must not require recognizing that the question is "about" a particular grammar rule; a student applying the rule naturally should succeed.

5. **No colloquial distractors**: Informal options ("gonna," "wanna," "like") never appear on the SAT and feel inauthentic.

6. **No hyper-specialized academic vocabulary**: Words like "ontological," "epistemological," "hermeneutic" do not appear in grammar items.

7. **Topic-appropriate register**: A science passage uses neutral academic register, not poetic or journalistic language.

8. **No extreme formality**: "One mustn't underestimate the proclivities of the aforementioned organisms" is not SAT style.

9. **Distractors must be student-plausible**: A distractor that only an ESL beginner would select fails validation.

10. **No puns or wordplay**: Grammar items are never humorous or pun-based.

11. **Balanced option lengths**: All four options should be within ~30% of the same word count.

12. **No political or partisan content**: Passages must be ideologically neutral.

13. **No first-person academic prose**: "I/we believe," "in my/our opinion," etc. are not SAT register.

14. **Consistent register across all options**: If the passage is formal academic, all options must be formal academic register. One colloquial distractor is a giveaway.

### 20.4 2025-2026 DSAT Trends

#### Poetry frequency increasing
- Practice Tests 9-11 include more literary/poetry passages
- Generation should include `poem` stimulus mode periodically

#### Table/data questions rising
- Quantitative evidence items appear in both modules, not just Module 2
- CoE-Quant frequency increasing

#### Module difficulty gap widening
- M2 difficult items are harder than in earlier practice tests
- Distractor competition in M2 is tighter

#### Passage length trend
- SEC sentences are getting longer (30-40 words vs. 20-30 in earlier tests)
- Reading passages remain stable at 100-150 words

#### Removed subtopics (confirmed absent from 2025-2026 tests)
- No comma with inverted clauses
- No semicolon in complex lists (only semicolon between ICs)
- No subjunctive mood items observed
- No "whom" in preposition stranding (only "to whom," "for which," etc.)

---

## 21. Amendment Process (Grammar-Specific)

Grammar-domain amendment proposals must use `proposed_parent_key` set to an
existing `grammar_role_key`. Include `frequency_estimate` and `example_count`
as required by core §16.

Do not insert proposed keys into production records until reviewed and promoted
to `approved`.
