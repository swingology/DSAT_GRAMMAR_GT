---
name: deep-question-analysis
description: Produce a deep, evidence-linked analysis of one DSAT question, including sentence anatomy, clause structure, grammatical controllers, style observations, trap and distractor anatomy, and annotation gaps. Use when the user asks to deeply analyze, reannotate, or document a question by database question ID or UUID.
---

# Deep Question Analysis

## Quick start

Run this skill with one database question UUID:

```text
/deep-question-analysis <question_id>
```

Use the read-only fetch helper first:

```bash
rtk proxy python3 .claude/skills/deep-question-analysis/scripts/fetch_question.py <question_id>
```

The helper prints the question, options, latest annotation, and source
metadata, latest version, stored passage spans, and stimulus assets as JSON.
It enforces a read-only database session. By default it uses `podman exec dsat-db`
and the container's `psql`. Set `DSAT_DATABASE_URL` to use host `psql` instead.

## Workflow

1. Fetch the current question, latest version, options, and latest annotation.
2. Save the exact JSON as `GENERATIONS/deep_analysis_<question_id>.source.json`.
   Preserve the original payload and source metadata exactly in the report.
   Compare current text, version text, annotation version, and answer labels;
   flag disagreements before analysis. Review stored passage spans as prior work.
3. Classify the assessed domain and skill using the active canonical vocabulary.
   Keep grammar fields null for reading items; do not force a grammar label.
4. Analyze the item at the appropriate depth:
   - sentence and clause structure; finite/nonfinite verbs; heads, modifiers,
     agreement controllers, attachment, scope, punctuation, and blank position
   - passage style: genre/register, stance, attribution, information flow,
     sentence-length texture, terminology, and evidence architecture
   - answer mechanism and evidence spans supporting the key
   - each option's plausibility source, primary error, trap relationship,
     student failure hypothesis, and why it is or is not defensibly wrong
5. Separate observed facts from interpretation. Mark missing, uncertain, or
   unsupported fields as `unknown` or `needs_review`; never infer learner
   misconceptions from an answer choice alone.
6. Follow [deep analysis rules](../../../chatgpt_refactor_rules/deep_analysis/1.0.0/RULES.md)
   and the checks in [REFERENCE.md](REFERENCE.md), including unique-answer,
   canonical-key, option-completeness, and source-preservation checks.
7. Write `GENERATIONS/deep_analysis_<question_id>.md` unless the user gives a
   different path. Include the question ID in the filename and report header.

## Output contract

The report must contain: source metadata; original question and options;
original annotation snapshot; assessed classification; evidence map; sentence
anatomy; clause/controller map; style observations; trap anatomy; per-option
distractor analysis; uncertainty and review findings; validation results; and
provenance with rule/vocabulary versions. Do not overwrite an existing report
without an explicit instruction. If either output exists, use the same UTC
timestamp suffix for both new files. Create files exclusively to avoid clobbering.

Use the current rules under `chatgpt_refactor_rules/` and the active
`vocabulary/master.json`. Treat publisher or research terms as source-labeled
references, not replacements for production keys. This skill creates a review
artifact; it does not migrate historical annotations or write deep fields to
the database.

Example: `/deep-question-analysis 063675a5-e319-5c9c-a8fd-b7846009bc5e`.
Use the [annotation guide](../../../chatgpt_refactor_rules/ANNOTATION_GUIDE.md)
for field definitions and the JSON template when structured analysis is requested.
On lookup failure, report the failure; never substitute a different question.
