# MCQ Realism Rules

## Purpose

This document defines concrete rules for generating more realistic multiple-
choice answer sets for DSAT-style questions.

It is designed to strengthen distractor quality, reduce obvious correct answers,
and improve realism for both:

- Craft and Structure / Information and Ideas items
- Standard English Conventions / grammar-adjacent items

This file is intended as a generation supplement. It does not replace domain
taxonomy rules.

## Core Principle

Generated multiple-choice items should become difficult because:

- wrong answers are plausible
- distractors compete closely with the correct answer
- each wrong answer reflects a specific likely mistake
- the correct answer is not visually, stylistically, or structurally signaled

Difficulty must come from competitive reasoning, not from vagueness, trivia,
trick wording, or malformed distractors.

## All-Four-Plausible Rule (Hard-Item Requirement)

This rule is mandatory for any item targeting `difficulty_overall: high` and
strongly preferred for `medium`.

**Every answer choice — including all three wrong answers — must be a
grammatically well-formed, contextually plausible English sentence or phrase
when read in isolation.** No option may be eliminated by a quick ear-test,
by sounding awkward out loud, or by appearing obviously broken on first scan.

This means:

- A student who skips careful rule analysis must still be unable to eliminate
  any option on surface feel alone.
- All four options must survive first-pass plausibility for a moderately
  skilled reader.
- The difference between correct and incorrect must only become visible under
  deliberate, rule-specific analysis.

### What "plausible" means for grammar items

For Standard English Conventions items:

- Every option must produce a structurally complete English sentence when
  inserted into the blank.
- No option may introduce obvious gibberish, incoherent word order, or a
  clearly missing verb.
- Comma-placement options must produce sentences that at least sound natural;
  a student should have to reason about whether a comma splice is present,
  not hear it immediately.
- Tense options must all be standard English tense forms; no made-up
  constructions.
- Agreement options must all be conjugations that exist in English, even if
  they agree with the wrong noun.

### Difficulty gradient for grammar items

| Level  | Description                                                                               |
| ------ | ----------------------------------------------------------------------------------------- |
| `low`  | 1–2 options are immediately eliminable; rule is visible without parsing                   |
| `medium` | All 4 options are surface-plausible; one strong trap; requires deliberate rule check    |
| `high` | All 4 options are surface-plausible; 2+ distractors compete closely; trap is embedded; correct answer does not "sound better" than the top distractor |

The target for realistic DSAT question generation is `medium` or `high`.
`low` items are only acceptable as scaffolding for early-module placement.

## Student Failure Mode Requirement

Every distractor must include a `student_failure_mode_key` that names the
psychological mechanism causing students to choose it.

Required keys:

- `nearest_noun_reflex` — verb agrees with nearest noun, not the true subject
- `comma_fix_illusion` — comma feels like it "fixes" the sentence structurally
- `formal_word_bias` — longer or more formal phrasing seems more correct
- `ear_test_pass` — the option sounds acceptable when read aloud even though it is wrong
- `punctuation_intimidation` — complex punctuation looks sophisticated, gains credibility
- `surface_similarity_bias` — option resembles the correct answer in structure or length
- `scope_blindness` — student applies the right rule to the wrong span
- `modifier_hitchhike` — student mentally attaches the modifier to the wrong noun
- `tense_proximity_pull` — tense is attracted to the time marker of the nearest clause, not the passage register
- `parallel_shape_bias` — option looks parallel because items share a syntactic pattern, even if one element breaks the underlying form
- `pronoun_anchor_error` — student connects the pronoun to the nearest noun, not the correct antecedent
- `possessive_contraction_confusion` — its/it's or whose/who's swap; both sound identical
- `grammar_fit_only` — option is grammatically valid in some context but wrong here
- `register_confusion` — formal-sounding option is chosen because formality signals correctness
- `false_precision` — option appears more specific or exact, which feels like accuracy
- `idiom_memory_pull` — student selects a familiar phrase without checking contextual fit

This field is mandatory for all generated distractors.

## Global Rules

### 1. Every distractor must be based on a named failure mode

Do not generate generic wrong answers.

Each distractor must be wrong for one specific reason that can be named in
metadata or internal reasoning, such as:

- scope error
- connotation mismatch
- wrong rhetorical verb
- reversed attribution
- nearest-noun attraction
- comma-splice repair illusion
- tense attraction
- semantic imprecision

If a distractor cannot be assigned a specific failure mode, regenerate it.

### 2. Every distractor must have a plausibility source

Each wrong answer must be tempting for a reason.

Allowed plausibility sources include:

- vocabulary overlap with the passage
- near-synonym appeal
- partial truth
- common-definition appeal
- register match
- formal-sounding surface correctness
- local detail match
- structural resemblance to the correct answer

If the only explanation for a distractor is "it is related to the topic," it is
too weak.

### 3. All options must be homogeneous

All answer choices must:

- answer the same question
- belong to the same semantic category
- match the same grammatical form
- match the same register
- appear equally viable at first glance

Examples:

- If the correct answer is an infinitive phrase, all options should be
  infinitive phrases.
- If the correct answer is a single word, all options should be single words or
  highly similar short phrases.
- If the correct answer is a cross-text relationship statement, all options
  should describe comparable relationships.

Do not mix:

- summary statements with detail statements
- verbs with noun phrases
- formal phrasing with casual phrasing
- broad claims with one narrow factual fragment

### 4. The correct answer must not be easier to spot than to reason to

Reject any item where the correct answer stands out because it is:

- longer
- more precise than all others by an obvious margin
- the only grammatically smooth option
- the only option in the correct register
- the only option that directly answers the stem form
- the only moderate or nuanced option among extreme distractors

The correct answer should win because it is best, not because it is cleaner.

### 5. Each distractor should fail on exactly one primary axis

A distractor should usually contain one main flaw, not several.

Preferred:

- close but wrong on scope
- close but wrong on attribution
- close but wrong on tone
- close but wrong on agreement

Avoid distractors that are obviously wrong for multiple unrelated reasons,
because these are eliminated too easily.

### 6. Use the cover-the-options test

Before generating answer choices, determine the answer from the stem and
passage alone.

If the item cannot be answered without looking at the options, the item is
under-specified or the stem is weak.

The options should create competition around a known target answer, not create
the question retroactively.

### 7. Avoid technical clues

Reject answer sets containing:

- one option much longer than the others
- one option with noticeably different syntax
- one option with repeated passage wording when others do not compete
- one option with hedged nuance while others are cartoonishly extreme
- "all of the above" or "none of the above"
- joke-like, bizarre, or trivial distractors

### 8. Three functioning wrong answers are required

Because SAT format uses 4 options, all 3 distractors must function.

A distractor counts as functioning only if a reasonable but mistaken student
could select it for a specific articulated reason.

Do not include filler distractors simply to satisfy option count.

## Craft And Structure Rules

### Words in Context

All options should be near-neighbors.

Required pattern:

- one distractor with correct broad meaning but wrong connotation
- one distractor with correct semantic field but wrong precision
- one distractor with plausible dictionary meaning but wrong contextual fit

Rules:

- keep part of speech identical across all options
- keep register close across all options
- avoid one option that is dramatically more academic or obscure than the rest
- if the correct answer is subtle, the distractors must also be subtle

Reject if:

- one wrong answer is obviously colloquial
- one wrong answer is semantically unrelated
- one wrong answer is only wrong because it sounds awkward out loud

### Text Structure and Purpose

All options must describe plausible rhetorical actions.

Required pattern:

- one distractor with the right topic but wrong action verb
- one distractor with the right local move but wrong overall scope
- one distractor with the right general purpose but overstated stance

Rules:

- keep rhetorical frame parallel across all options
- use comparable infinitive phrasing when the correct answer uses infinitives
- keep all options at similar abstraction level

Reject if:

- the correct answer is the only option describing what the text actually does
- distractors are merely about what the text mentions
- one distractor is obviously factual while others are rhetorical

### Cross-Text Connections

All options must encode plausible text relationships.

Required pattern:

- one reversed-attribution distractor
- one false-agreement or false-disagreement distractor
- one overstatement or wrong-qualification distractor

Rules:

- both texts must be summarized internally before option generation
- distractors should differ in stance logic, not just surface wording
- options must preserve the same comparison frame

Reject if:

- one option is clearly the only one referencing both texts correctly
- wrong options misuse text labels in an obvious way
- wrong options are too extreme to be seriously considered

### Information and Ideas

Use evidence competition rather than topical proximity alone.

Required pattern:

- one topically related but logically disconnected distractor
- one partial-match distractor
- one overreach, scope-extension, or inverted-logic distractor

Rules:

- distractors should often contain true or nearly true content
- wrongness should come from logical relation to the claim, not random mismatch
- quantitative items should include plausible but misaligned data readings

Reject if:

- only one option actually addresses the claim
- wrong options can be dismissed without consulting the passage
- data distractors are numerically absurd

## Grammar And SEC Rules

### General SEC Rule

For grammar items, distractors should be attractive because they look valid on
surface scan, not because they are nonsense.

Every wrong option must:

- preserve plausible English
- resemble the correct option in structure
- target a common editing reflex or grammar misconception
- be eliminable only by precise rule application, not by ear

### Required SEC distractor family

For each item, include:

- one primary trap distractor tied to the tested grammar mechanism
- one formal-sounding distractor that appears polished but is wrong
- one close competitor that is grammatically tempting but fails on the target
  rule

All three must produce grammatically plausible-sounding English when read aloud.

### SEC rejection rules

Reject grammar answer sets where:

- one option is the only grammatical sentence
- one option is obviously broken on punctuation or agreement
- one wrong option contains an extra unrelated error
- one wrong option differs so much in rhythm or shape that it becomes easy to
  eliminate
- any option can be eliminated simply by reading aloud without rule analysis
- the correct option is the only one that "sounds right" to a non-expert reader

### SEC Distractor Architecture by Grammar Type

Each grammar focus requires a specific distractor design to achieve
all-four-plausible construction.

#### Subject-Verb Agreement

All four options must be real English conjugations.

- Correct: singular verb matching the true grammatical subject
- Trap 1: plural verb attracted by the nearest intervening noun
  (`nearest_noun_reflex`)
- Trap 2: singular verb with a wrong tense (e.g., present perfect when simple
  present is required) (`formal_word_bias`)
- Trap 3: progressive or auxiliary construction that sounds sophisticated but
  is not standard for the passage register (`grammar_fit_only`)

#### Verb Tense Consistency

All four options must be real, well-formed tense constructions.

- Correct: tense matching the established passage tense register
- Trap 1: tense attracted by the time marker of the nearest clause rather than
  the passage's overall register (`tense_proximity_pull`)
- Trap 2: present perfect, which sounds formal and is valid in many contexts
  (`formal_word_bias`)
- Trap 3: conditional or future tense that sounds appropriately hedged but
  disrupts consistency (`grammar_fit_only`)

Key: no option may be a nonexistent verb form or an obvious conjugation error.

#### Punctuation — Semicolons and Commas

All four options must be punctuation marks that exist in standard usage.

- Correct: the mark that properly connects or separates the clauses
- Trap 1: comma, which is the default mark and feels natural (`comma_fix_illusion`)
- Trap 2: colon or dash, which looks sophisticated (`punctuation_intimidation`)
- Trap 3: period, which is technically valid but severs a related clause
  (`scope_blindness`)

For comma questions, all four options must be arrangements that look
professionally edited — no obviously missing marks.

#### Apostrophe / Possessive vs. Plural

All four options must be real English word forms.

- Correct: the form that fits the grammatical role (possessive or plural or
  contraction)
- Trap 1: plural form without apostrophe (students choose when they skip
  possession check) (`ear_test_pass`)
- Trap 2: singular possessive when plural possessive is correct, or vice versa
  (`nearest_noun_reflex`)
- Trap 3: possessive pronoun or contraction that is homophonous with correct
  answer (its/it's, whose/who's) (`possessive_contraction_confusion`)

#### Modifier Placement

All four options must produce structurally complete sentences.

- Correct: modifier attached to the noun it logically modifies
- Trap 1: passive construction that obscures the logical subject
  (`modifier_hitchhike`)
- Trap 2: modifier placed next to a semantically related but incorrect noun
  (`modifier_hitchhike`)
- Trap 3: restructured clause that sounds natural but produces a dangling
  modifier (`ear_test_pass`)

#### Parallel Structure

All four options must contain real English grammatical forms.

- Correct: form matching the established parallel pattern (gerund, infinitive,
  or noun)
- Trap 1: different form that sounds natural in context (`parallel_shape_bias`)
- Trap 2: nominalization (noun form) that sounds formal and educated
  (`formal_word_bias`)
- Trap 3: infinitive or gerund switch that preserves surface meaning but breaks
  the form (`grammar_fit_only`)

#### Pronoun Agreement and Case

All four options must be real English pronouns.

- Correct: pronoun matching antecedent in number, gender, and case
- Trap 1: pronoun attracted by the nearest noun, not the correct antecedent
  (`pronoun_anchor_error`)
- Trap 2: reflexive pronoun that sounds more precise or formal
  (`formal_word_bias`)
- Trap 3: pronoun of wrong case that sounds natural in speech (e.g., "between
  you and I") (`ear_test_pass`)

#### Adjective vs. Adverb

All four options must be real English words from the same semantic field.

- Correct: the form (adjective or adverb) required by the word's syntactic role
- Trap 1: adjective used where adverb is required, or vice versa; sounds
  natural in everyday speech (`ear_test_pass`)
- Trap 2: comparative form that sounds more precise (e.g., "more carefully"
  vs. "carefully") (`false_precision`)
- Trap 3: adverb applied to the wrong element in the sentence
  (`modifier_hitchhike`)

#### Illogical Comparisons

All four options must be phrases that produce grammatically complete comparisons.

- Correct: comparison between two parallel things (e.g., noun to noun)
- Trap 1: comparison between a thing and a person or possessive, which is
  the most common illogical comparison error (`scope_blindness`)
- Trap 2: comparison using "more" or "less" without "than" (`grammar_fit_only`)
- Trap 3: comparison that introduces a redundant "other" or omits a required
  "other" (`false_precision`)

#### Sentence Boundary (Comma Splice / Fragment / Run-On)

All four options must produce sentences that sound like they could be real
edited prose.

- Correct: the punctuation or conjunction that produces valid sentence
  boundaries
- Trap 1: comma that creates a comma splice but sounds natural as a pause
  (`comma_fix_illusion`)
- Trap 2: dash or semicolon that creates a boundary but is the wrong type
  (`punctuation_intimidation`)
- Trap 3: coordinating conjunction added unnecessarily, or omitted when
  required (`grammar_fit_only`)

#### Subjunctive Mood

All four options must be real English verb forms.

- Correct: subjunctive form (were, be, etc.) required by the conditional or
  hypothetical context
- Trap 1: indicative form that matches the tense of the surrounding clause
  (`tense_proximity_pull`)
- Trap 2: past tense that sounds natural in a counterfactual context
  (`ear_test_pass`)
- Trap 3: conditional form (would, could) that sounds appropriately tentative
  but is the wrong construction (`formal_word_bias`)

#### Transition Logic (Expression of Ideas)

All four options must be real English transition words or phrases.

- Correct: transition that reflects the actual logical relationship between
  clauses
- Trap 1: transition with opposite direction (e.g., "however" when the passage
  continues, not contrasts) (`transition_assumption`)
- Trap 2: transition that sounds formal and authoritative regardless of
  direction (`register_confusion`)
- Trap 3: additive transition that is plausible but weakens the logical
  relationship (`scope_blindness`)

## Generator Workflow Rules

### Step 1. Pre-answer before options

Write the answer privately before generating choices.

### Step 2. Choose the syntactic trap

Before writing distractors, name the specific syntactic trap embedded in the
passage. This trap determines the primary distractor. Common traps:

- nearest noun between subject and verb
- participial phrase that dangling-attaches to wrong noun
- two possible antecedents for the pronoun
- time marker that pulls tense in the wrong direction
- clause that could be read as dependent or independent depending on punctuation
- compound subject that obscures singular/plural agreement

If no syntactic trap is present, the item difficulty cap is `medium`.

### Step 3. Generate distractors from failure modes

Do not perturb wording randomly.

Instead:

- choose 3 student failure modes from the approved list
- assign 1 plausibility source to each
- write 1 distractor per failure mode
- verify each distractor produces plausible English when read in isolation

### Step 4. Normalize the option set

After drafting the options, force-check:

- same category
- same register
- same length band
- same abstraction level
- same grammatical frame
- all four options sound like real edited English

### Step 5. Run elimination pressure check

Ask:

- Can a smart student eliminate any option instantly for a superficial reason?
- Is any wrong option obviously less polished than the others?
- Is the correct answer visibly safer or more exact than the others?
- Can any option be eliminated by reading aloud without rule analysis?
- Does the correct answer "sound better" to someone who hasn't applied the rule?

If yes to any, revise.

### Step 6. Run all-four-plausible verification

Insert each option into the passage blank and read the resulting sentence aloud.

Ask for each wrong option:

- Is this a real English sentence?
- Would a moderately skilled reader hesitate before rejecting it?
- Does it fail only when the specific grammar rule is consciously applied?

If any wrong option fails this check, it is too easy. Regenerate it.

### Step 7. Run competitive ranking check

The final option set should support this statement:

"A partially skilled student could defend at least two wrong answers before
careful analysis resolves the item."

If that is not true, the item is too easy at the option level.

## Validator Rules

Before accepting a generated item, confirm:

- exactly one correct answer
- three functioning distractors
- each distractor has one primary failure mode
- each distractor has one plausibility source
- each distractor has one `student_failure_mode_key`
- all options are homogeneous
- no option is obviously signaled by length, grammar, tone, or structure
- the correct answer is not the only nuanced option
- difficulty comes from reasoning competition, not formatting artifacts
- all four options produce plausible English sentences when inserted into the blank
- no option is eliminable by ear-test alone
- `distractor_distance` is `tight` for high-difficulty items
- `plausible_wrong_count` is 3 for high-difficulty items; at least 2 for medium
- at least one distractor directly exploits the passage's syntactic trap

### Hard-Item Validator Checklist (additional checks for `difficulty_overall: high`)

- No distractor fails for more than one reason
- No two distractors exploit the same student failure mode
- The correct answer is not the only option that sounds formal or academic
- The correct answer is not noticeably shorter or longer than distractors
- A student who reads only the passage and one distractor (not all options)
  should find that distractor genuinely tempting
- The item cannot be answered by substitution and ear-test alone; rule
  knowledge is required

## Implementation Guidance

This document is best used in combination with:

- domain taxonomy rules
- official-example retrieval
- corpus conformance checks
- anti-clone checks

Recommended runtime order:

1. select domain and skill family
2. retrieve nearest official exemplars
3. generate stem and pre-answer
4. generate distractors using these realism rules
5. validate with domain rules
6. validate with realism rules
7. rerun if any realism rule fails

## Source Basis

This document is informed by:

- NBME Item-Writing Guide, 2024 edition
- Haladyna, Downing, and Rodriguez on multiple-choice item-writing guidelines
- ETS distractor-analysis research
- distractor-development literature emphasizing misconception-based distractors

References:

- https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf
- https://doi.org/10.1207/S15324818AME1503_5
- https://www.ets.org/research/policy_research_reports/publications/report/2019/kbgc.html
- https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.00825/full
- https://journals.sagepub.com/doi/10.1177/0013164493053004013
