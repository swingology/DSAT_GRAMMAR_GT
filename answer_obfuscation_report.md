# Answer Obfuscation Report

## Summary

When `rules_agent_dsat_reading_v1.md` and
`rules_agent_dsat_grammar_ingestion_generation_v3.md` are used together for
Craft and Structure generation, the answer choices can become too obvious.

This is not just a content problem in the rule files. It is also a prompt and
system-design problem in the backend.

## Main Finding

The current generation path is grammar-centric.

`backend/app/prompts/generate_prompt.py` hardcodes
`rules_agent_dsat_grammar_ingestion_generation_v3.md` as the governing
specification and explicitly asks the model to emit grammar-specific fields:

- `grammar_role_key`
- `grammar_focus_key`
- `syntactic_trap_key`

That is the wrong control surface for Craft and Structure generation.

## Evidence

### 1. Backend generation prompt is grammar-first

File:

- `backend/app/prompts/generate_prompt.py`

Key issue:

- The system prompt says the model is following
  `rules_agent_dsat_grammar_ingestion_generation_v3.md`
- The required output is grammar-shaped rather than reading-shaped

This means the model is being steered to think in Standard English
Conventions-style generation terms even when the requested item belongs to
Craft and Structure.

### 2. The two rule files conflict if both are active for one item

Grammar V3 explicitly says `grammar_role_key` usage is forbidden for:

- `craft_and_structure`
- `information_and_ideas`

Reading V1 explicitly says `grammar_role_key` and `grammar_focus_key` must be
null or omitted for questions in those reading domains.

So if both files are applied at once during a single generation pass, the model
receives mixed instructions:

- the grammar file provides the strongest operational generation machinery
- the reading file forbids the grammar taxonomy for Craft items

That creates an unstable generation setup.

### 3. Grammar V3 has much stronger operational generation rules

The grammar file contains a highly detailed procedural generation framework,
including:

- generation input specification
- step-by-step generation workflow
- passage rules by focus key
- distractor generation heuristics by focus key
- realism and distractor competition protocol
- option ordering rules
- validation additions

By contrast, the reading file contains good classification logic and trap
taxonomy, but its generation guidance is lighter and less operationalized.

Result:

- the model tends to follow the grammar document as the procedural engine
- the reading document functions more like a taxonomy overlay

That is a bad combination for Craft and Structure question generation.

### 4. Craft-specific trap labels exist, but the generation protocol is weaker

Reading V1 does contain strong Craft and Structure trap definitions, including:

- `common_definition_trap`
- `semantic_relatedness_without_precision`
- `plausible_synonym`
- `wrong_action_verb`
- `reversed_attribution`
- `confirmed_when_contradicted`

It also contains good skill-specific annotation requirements for:

- Words in Context
- Text Structure and Purpose
- Cross-Text Connections

But it does not provide the same level of enforced generation-time distractor
templates and workflow discipline that the grammar file provides.

This makes it easier for the model to generate distractors that are merely
reasonable, instead of distractors that are tightly competitive.

### 5. Annotation prompt truncation weakens later realism rules

`backend/app/prompts/annotate_prompt.py` truncates the loaded rules text to the
first 8000 characters when the rules file is long.

That matters because much of the strongest realism and distractor-competition
material in V3 lives far later in the file.

So even inside the grammar-only path, some of the most important answer-choice
hardening rules may not consistently reach the model.

## Why The Answers Feel Too Obvious

The answers likely feel obvious for four reasons:

1. Craft items are being generated under a grammar-shaped prompt contract.
2. The most procedural rule file in the system is the grammar file, not the
   reading file.
3. The reading file has strong classification and analysis logic, but weaker
   generation enforcement.
4. Late-file distractor competition rules may be lost in truncated prompt
   loading.

In practice, that means the system can produce:

- correct answers that are too semantically clean
- distractors that are topically related but not tightly competitive
- Craft items that feel classified correctly after the fact, but not generated
  from a truly Craft-native process

## Conclusion

Yes, the observed problem is real and expected under the current setup.

The system is not currently structured to run Craft and Structure generation
with a dedicated Craft-native prompt and rule contract. Instead, it relies on a
grammar-centered generation scaffold plus a reading-domain companion rules file.

That architecture is sufficient for taxonomy coverage, but not sufficient for
high-quality answer obfuscation in Craft generation.

## Recommended Direction

Do not merge the original documents into one monolith.

Instead:

1. keep the original source rule files unchanged
2. create a shared core generation rules layer
3. create one grammar module
4. create one reading module
5. ensure Craft generation loads the core plus the reading module, not the
   grammar module's output contract

This would allow Craft items to inherit the same level of distractor
engineering discipline without forcing grammar-shaped fields into a reading
task.

## GAPS

The report is useful and directionally correct, but it is not yet fully detailed
or comprehensive. It explains the local prompt/rule-file conflict, but it does
not yet anchor the diagnosis in external assessment-design research, psychometric
distractor behavior, or current-code drift.

### 1. The report should include College Board's stated distractor standard

College Board's Digital SAT Suite Technical Manual describes Reading and Writing
items as four-option multiple-choice questions with one keyed response and three
distractors. It states that each distractor should represent a common error a
student might reasonably make, with plausibility varying by intended item
difficulty, while still not competing with the key for students at the target
achievement level.

That matters because "answer obfuscation" should not mean hiding the answer with
arbitrary semantic noise. A DSAT-native standard is better framed as:

- every wrong answer should map to a plausible student error
- difficulty should control how attractive the distractors are
- no distractor should become defensibly co-correct
- the correct answer should remain the single best answer for the intended skill

Source: [College Board Digital SAT Suite Technical Manual, 2024](https://research.collegeboard.org/media/pdf/Digital%20SAT%20Suite%20of%20Assessments%20Technical%20Manual-FINAL.pdf)

### 2. The report should distinguish Craft and Structure subskills more sharply

The current report treats Craft and Structure as one broad generation problem.
College Board defines Craft and Structure as covering high-utility words and
phrases in context, rhetorical evaluation of texts, and connections between
topically related texts. Those are not one distractor problem; they require
different wrong-answer families.

Missing Craft-specific generation requirements:

- Words in Context: distractors should be contextually tempting but fail the
  local semantic role, tone, register, or passage logic.
- Text Structure and Purpose: distractors should preserve topic overlap while
  misidentifying rhetorical function, scope, or author action.
- Cross-Text Connections: distractors should mix attribution, agreement,
  disagreement, emphasis, or evidence relationships across the two texts.

Source: [College Board Reading and Writing Section overview](https://satsuite.collegeboard.org/sat/whats-on-the-test/reading-writing)

### 3. The report should add psychometric distractor-functioning criteria

The report says answers "feel too obvious," but it does not define measurable
distractor effectiveness. Item-writing research reviewed by Haladyna, Downing,
and Rodriguez found that standardized-test items often have only one or two
effectively functioning distractors, and items with more effective distractors
were more discriminating. That is directly relevant because the Digital SAT uses
four-option items, so the system needs all three distractors to do real work.

Missing evaluation criteria:

- each distractor should be selected by some lower-performing or partially
  informed examinees in pilot/student simulation
- distractors should not be uniformly ignored by the model or by students
- item discrimination should improve when distractors are more competitive
- distractor quality should be evaluated separately from key correctness

Source: [Haladyna, Downing, and Rodriguez, 2002](https://www.highpoint.edu/citl/files/2017/06/Review_MCQ_Item_Writing_Guidelines_Haladyna-Downing-Rodriguez_2002.pdf)

### 4. The report should include option-homogeneity and clue-control checks

General item-writing research emphasizes that options should be homogeneous in
content and grammatical structure so test takers focus on the intended construct
instead of superficial cues. The report mentions weak distractors, but it does
not list common answer-key giveaways.

Missing answer-choice checks:

- correct answer is not consistently longer, more precise, or more academic
- distractors share the same syntactic form and level of abstraction as the key
- options do not leak the key through repeated wording from the stem
- distractors do not fail merely because of grammar, tone, or category mismatch
- option ordering does not create a positional or semantic pattern

Source: [Haladyna, Downing, and Rodriguez, 2002](https://www.highpoint.edu/citl/files/2017/06/Review_MCQ_Item_Writing_Guidelines_Haladyna-Downing-Rodriguez_2002.pdf)

### 5. The report should add automated distractor-quality metrics

Recent NLP research treats distractor quality as a combination of incorrectness,
plausibility, and diversity. This is a useful backend framing: a distractor must
be wrong, tempting, and non-duplicative. The current report recommends a better
prompt architecture but does not propose a scoring loop for generated options.

Missing backend evaluation layer:

- incorrectness check: verify the distractor is not entailed as a valid answer
- plausibility check: ask a separate model to estimate attraction/confidence for
  each distractor before revealing the key
- diversity check: compare distractors against each other so they do not all
  express the same wrong idea
- key-vs-distractor margin: require the key to beat each distractor, but not by
  such a huge margin that the item becomes trivial

Sources: [Assessing Distractors in Multiple-Choice Tests](https://arxiv.org/abs/2311.04554),
[Distractor Generation in Multiple-Choice Tasks: A Survey](https://arxiv.org/abs/2402.01512)

### 6. The report should be updated for current-code drift

Some local-code claims in the report are now stale or incomplete:

- `backend/app/prompts/generate_prompt.py` no longer hardcodes only
  `rules_agent_dsat_grammar_ingestion_generation_v3.md`; it currently loads
  Grammar v7 and Reading v2 snippets.
- The generation prompt is still grammar-shaped because it requires
  `grammar_role_key`, `grammar_focus_key`, and `syntactic_trap_key`, so the
  core diagnosis still applies for Craft generation.
- Generation rule context is truncated to the first 6000 characters of each rule
  file, which can still omit late-file generation and distractor controls.
- `backend/app/prompts/annotate_prompt.py` no longer appears to use one simple
  8000-character truncation; it now extracts selected grammar and reading
  sections and enforces reading/grammar nullability after annotation.

The revised conclusion should be: the original report is a solid first-pass
architecture diagnosis, but it needs a research-backed definition of distractor
quality, measurable acceptance criteria, Craft-subskill-specific distractor
templates, and an update to reflect the current v7/v2 prompt-loading code.
