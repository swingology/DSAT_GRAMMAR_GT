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
