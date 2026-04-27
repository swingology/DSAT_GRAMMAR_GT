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

### Required SEC distractor family

For each item, include:

- one primary trap distractor tied to the tested grammar mechanism
- one formal-sounding distractor that appears polished but is wrong
- one close competitor that is grammatically tempting but fails on the target
  rule

### SEC rejection rules

Reject grammar answer sets where:

- one option is the only grammatical sentence
- one option is obviously broken on punctuation or agreement
- one wrong option contains an extra unrelated error
- one wrong option differs so much in rhythm or shape that it becomes easy to
  eliminate

## Generator Workflow Rules

### Step 1. Pre-answer before options

Write the answer privately before generating choices.

### Step 2. Generate distractors from failure modes

Do not perturb wording randomly.

Instead:

- choose 3 failure modes
- assign 1 plausibility source to each
- write 1 distractor per failure mode

### Step 3. Normalize the option set

After drafting the options, force-check:

- same category
- same register
- same length band
- same abstraction level
- same grammatical frame

### Step 4. Run elimination pressure check

Ask:

- Can a smart student eliminate any option instantly for a superficial reason?
- Is any wrong option obviously less polished than the others?
- Is the correct answer visibly safer or more exact than the others?

If yes, revise.

### Step 5. Run competitive ranking check

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
- all options are homogeneous
- no option is obviously signaled by length, grammar, tone, or structure
- the correct answer is not the only nuanced option
- difficulty comes from reasoning competition, not formatting artifacts

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
