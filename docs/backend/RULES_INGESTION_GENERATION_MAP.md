# Rules, Ingestion, and Generation Map

This document explains how the current rules and vocabulary files participate
in DSAT ingestion and generation.

## Current Wiring Summary

| File | Current role | Ingestion | Generation | Notes |
|---|---|---|---|---|
| `rules_agent_dsat_reading_v3.md` | Present in repo, not currently wired | Not loaded by current prompt code | Not loaded by current prompt code | The live backend still loads `rules_agent_dsat_reading_v2.md` for reading rules. |
| `rules_agent_dsat_grammar_ingestion_generation_v8.md` | Active grammar rules file | Loaded for grammar routing, annotation, taxonomy, and amendment guidance | Loaded for grammar generation, sub-pattern guidance, distractor heuristics, validation checklist, and review | This is the active replacement for v7. |
| `vocabulary/master.json` | Active controlled-vocabulary source of truth | Compiled into `backend/app/models/ontology.py`, which validators and prompts import | Same compiled ontology constrains generation request schema and generated-question validation | Rule-doc appendix blocks are generated from this file. |
| `vocabulary/master_samples.json` | Advisory examples companion for `master.json` | Can be retrieved by vocabulary/value to help an annotator choose labels consistently | Can be retrieved by target vocabulary/value to make generated items express the intended labels clearly | Does not define active keys and is not currently compiled into `ontology.py`. |
| `vocabulary/candidates.json` | Non-blocking review queue for unknown keys | Receives unknown LLM-produced keys during validation or amendment capture | Not used to allow generation keys; only review input | Candidates are not active vocabulary. Promotion must go through approved amendment workflow. |

## Ingestion Flow

Official or generated input enters the ingestion pipeline as extracted question
data. Pass 2 annotation then loads rule context and asks the LLM to produce
structured annotations.

### Grammar Questions

`backend/app/prompts/annotate_prompt.py` loads:

- `rules_agent_dsat_grammar_ingestion_generation_v8.md`
- `rules_agent_dsat_reading_v2.md`

For grammar questions, the prompt extracts from grammar v8:

- Part A: mode routing
- Part C: annotation / ingestion rules
- Part D: taxonomy reference

The grammar file tells the annotator which fields to emit, which taxonomy keys
are valid, how to disambiguate grammar roles/focuses, and how to propose
amendments when an official item exposes a real rules gap.

### Reading Questions

The live annotation code currently loads `rules_agent_dsat_reading_v2.md`, not
`rules_agent_dsat_reading_v3.md`.

For reading questions, the prompt extracts reading sections covering question
fields, skill/focus taxonomy, difficulty calibration, disambiguation, and
student failure modes. Grammar v8 may still be included for routing/taxonomy
context, but reading-domain questions must not set grammar keys.

### Validation and Unknown Keys

`backend/app/pipeline/validator.py` validates extracted/annotated questions
against constants imported from `backend/app/models/ontology.py`.

`ontology.py` is generated from `vocabulary/master.json`, so active allowed keys
come from `master.json`, not from ad hoc LLM output.

`vocabulary/master_samples.json` is a companion analysis file. It mirrors every
active `master.json` entry by vocabulary name and value, then adds synthetic
use cases, near-miss distinctions, and ingestion/generation guidance. It can
help a human or retrieval layer explain why an active key fits, but it does not
make any key valid.

If validation sees an unknown controlled-vocabulary value, it records that value
through `backend/app/models/vocab_candidates.py` into
`vocabulary/candidates.json`. This is intentionally non-blocking review input:
it does not make the key valid.

### Amendment Proposals

Official-source annotations may include `reasoning.amendment_proposal`.

`backend/app/pipeline/amendments.py` captures those proposals into pending
amendment files and links matching entries in `vocabulary/candidates.json`.

Approved promotion uses `backend/app/pipeline/amendment_review.py`:

1. Validate the amendment.
2. Patch the relevant rule doc body.
3. Update `vocabulary/master.json`.
4. Regenerate `backend/app/models/ontology.py`.
5. Regenerate VOCAB appendix blocks in the rule docs.
6. Remove the promoted candidate from `vocabulary/candidates.json`.

For grammar amendments, the active target rule doc is
`rules_agent_dsat_grammar_ingestion_generation_v8.md`.

For reading amendments, the current code still targets
`rules_agent_dsat_reading_v2.md`.

## Generation Flow

Generation starts from a `GenerationRequest` or batch request. The request
declares either a grammar target or a reading target.

### Grammar Generation

`backend/app/prompts/generate_prompt.py` loads
`rules_agent_dsat_grammar_ingestion_generation_v8.md` as `Grammar v8`.

For grammar generation, it extracts:

- Purpose and mode routing
- Generation input specification
- Step-by-step generation workflow
- B.3.0 sub-pattern policy and evidence tiers
- B.3 passage construction rules
- B.4 distractor heuristics
- Transition and notes-synthesis metadata
- Difficulty, batch, explanation, and validation rules
- Disambiguation, syntactic trap, failure mode, and schema guardrails
- Quality protocols

The important v8 addition is that B.3.0 and B.3 give the generator calibrated
sub-patterns without making them hard templates. The generator should use these
as evidence-backed variation, not as a fixed menu.

### Reading Generation

The live generation code currently loads `rules_agent_dsat_reading_v2.md` as
`Reading v2`. `rules_agent_dsat_reading_v3.md` is not yet used by this path.

When the request is reading-domain, generation loads reading sections covering:

- Required output shape
- Reading question fields
- Answer mechanism keys
- Skill-specific annotation rules
- Difficulty calibration
- Passage architecture requirements
- Reading generation rules
- Disambiguation rules
- Student failure modes
- Validator checklist

### Controlled Vocabulary During Generation

Generation request schemas and downstream validation rely on the same compiled
ontology constants generated from `vocabulary/master.json`.

`vocabulary/master_samples.json` can assist generation when a request targets a
specific key. The useful retrieval pattern is:

1. Read the target key from the generation request.
2. Join to `master_samples.json` by `vocabulary` and `value`.
3. Add only the matching sample guidance to the prompt.
4. Generate content that makes that target key objectively recoverable.

Loading the whole samples file into every generation prompt is not recommended;
it is large and advisory. The rules files remain the normative instructions,
and `master.json` remains the authoritative key set.

`vocabulary/candidates.json` does not authorize generation. A generated question
that emits an unknown key can be recorded as a candidate during validation, but
the key remains inactive until approved and promoted.

## Review Flow

`backend/app/prompts/review_prompt.py` loads:

- `rules_agent_dsat_review_v1.md`
- `rules_agent_dsat_grammar_ingestion_generation_v8.md`
- `rules_agent_dsat_reading_v2.md` for reading or mixed-domain candidates

Grammar v8 is always loaded for review. Reading rules are loaded additively
when the candidate is reading-domain or ambiguous.

The review prompt uses the rules for taxonomy matching, SAT realism, copy-risk
assessment, distractor quality, and explanation quality. Review does not update
`master.json` or `candidates.json`; it only evaluates generated output.

## Vocabulary File Responsibilities

### `vocabulary/master.json`

`master.json` is the compiled enforcement manifest. It is the source used by
`scripts/gen_vocab.py` to generate:

- `backend/app/models/ontology.py`
- VOCAB appendix blocks in the active rule docs

Normal active vocabulary growth should happen only after a rule-doc amendment is
approved.

### `vocabulary/master_samples.json`

`master_samples.json` is a comprehensive advisory companion to `master.json`.
It samples every active `master.json` entry and stores:

- when to use the key
- when not to use it
- synthetic positive examples
- near-miss distinctions
- ingestion guidance
- generation guidance
- validation/join guidance

It helps analysis by making the ontology explainable. The ontology still comes
from `master.json`; `master_samples.json` only helps an annotator, generator, or
reviewer choose among valid keys more consistently.

Join contract:

- flat vocabularies: `vocabulary name + value`
- hierarchical vocabularies: `vocabulary name + parent + value`

Recommended prompt use is selective retrieval. For example, if a generation
request targets `grammar_focus_key: subject_verb_agreement`, retrieve only the
`GRAMMAR_FOCUS_BY_ROLE / agreement / subject_verb_agreement` sample entry.

### `vocabulary/candidates.json`

`candidates.json` is a queue of unknown keys observed in practice. It stores
candidate value, field/vocab, occurrence count, sample job IDs, and contexts.

It exists to prevent silent vocabulary drift while preserving useful evidence
from LLM output. It is not an allowlist and should not be treated as production
taxonomy.

## Reading v3 Status

`rules_agent_dsat_reading_v3.md` exists in the repo, but current live references
still point to `rules_agent_dsat_reading_v2.md` in:

- `backend/app/prompts/annotate_prompt.py`
- `backend/app/prompts/generate_prompt.py`
- `backend/app/prompts/review_prompt.py`
- `scripts/gen_vocab.py`
- amendment and rule-doc patching paths

If `rules_agent_dsat_reading_v3.md` is intended to become active, the next
implementation step is to switch the reading file constants and docs from v2 to
v3, then run `scripts/gen_vocab.py --generate` and the prompt/amendment tests.
