# Controlled Vocabulary Governance

`vocabulary/master.json` is the compiled enforcement manifest for controlled
vocabulary. It is not the normative authoring surface for new rules.

## Invariant

Rule-document body approval comes before active vocabulary growth.

Official ingestion may propose an amendment when an approved key does not fit.
That proposal is review input. A key may become active only after an approved
amendment updates the body of the relevant rule document:

- `rules_agent_dsat_reading_v2.md`
- `rules_agent_dsat_grammar_ingestion_generation_v8.md`

Only after the rule-doc body is approved should the corresponding vocabulary
entry be added to `vocabulary/master.json`, followed by regeneration of:

- `backend/app/models/ontology.py`
- generated VOCAB appendix blocks in the rule docs

## Candidate Queue

`vocabulary/candidates.json` records unknown keys observed during validation.
Candidates are non-blocking review input. They do not make a key active and must
not be promoted directly into `master.json` in the normal workflow.

`scripts/gen_vocab.py --list-candidates` is safe for review. Legacy direct
promotion with `--promote` is blocked unless `--unsafe-direct-promote` is passed;
that flag is for isolated development only.

## Current Development Gap

The approved promotion path is still being built. Phase 5 will add
`--promote-from-amendment AMENDMENT_ID` and share the same policy checks as the
admin API. Until then, active vocabulary growth should be handled as a reviewed
repo change that includes the approved rule-doc body patch and regenerated
artifacts.
