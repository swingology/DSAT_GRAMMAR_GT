# rules_refactor — Decomposed DSAT Rules Documents

Working sandbox (2026-08-02). Nothing here is wired into the live pipeline yet;
the live docs at the repo root and `backend/app/prompts/` are untouched.

## What's here

| Path | What it is |
|---|---|
| `rules_agent_dsat_grammar_ingestion_generation_v8.md` | Corrected copy — **v8.2-refactor** (see version footer for the fix list) |
| `rules_agent_dsat_reading_v3.md` | Corrected copy — **v3.1-refactor** (see version footer) |
| `rules_agent_dsat_review_v1.md` | Unmodified copy of the review rubric |
| `split_rules.py` | Deterministic splitter: corrected monoliths → `rules/` modules |
| `rules/` | Generated output — 65 modules + `manifest.json` + `split_report.json` |
| `TODO_out_of_scope.md` | Changes needed **outside** this directory to adopt the refactor |

## The decomposition

```
rules/
  shared/00_mode_and_schemas.md      Purpose + Part A (mode routing, output schemas)
  grammar/
    generation_core.md               B.1–B.2, B.3.0, B.7–B.11, B.13–B.15, Part E
    annotation_core.md               Part C + D.4 decision tree
    taxonomy.md                      D.1–D.3, D.5–D.9
    future_anatomy.md                D.10 (future Pass-3 span annotation; not loaded)
    conditional/transitions.md       B.5 — only for transition_logic
    conditional/notes_synthesis.md   B.6 + B.3 stub — only for choose_best_notes_synthesis
    examples/<key>.md                B.12 worked examples, loaded only for their key
    skills/<focus_key>.md            44 files: B.3 block(s) + B.4 distractor table
                                     (+ Matching Delimiter cross-key note on the
                                     5 delimiter-sensitive punctuation keys)
  reading/
    core_taxonomy.md                 Purpose, §1–§6, §8–§12, §17–§18, §20
    generation_core.md               §14–§16.8, §23 (minus per-family §16.9 rows)
    annotation_core.md               §21 validator checklist
    style_fingerprint.md             §22 — generation only
    skills/<skill_family>.md         7 files: §7.x + §13.x + §19.x + that family's
                                     §16.9 recipe rows
  manifest.json                      focus_key / skill_family → ordered load set
                                     (separate "generate" and "annotate" sets),
                                     plus stem-type overrides and do_not_generate
  split_report.json                  per-source line accounting; the splitter
                                     fails loudly on any unassigned line
```

**Deliberately excluded from prompt modules:** Appendix V (generated VOCAB
blocks — validator-side truth lives in `vocabulary/master.json` /
`backend/app/models/ontology.py`; embedding a drifting copy in prompts was
actively harmful), the Reference Quick-Index (human navigation aid), and D.10
(spec for a pipeline that doesn't exist yet — emitted as `future_anatomy.md`
but in no load set).

## Measured effect

| Call | Before (monolith) | After (manifest load set) |
|---|---|---|
| Generate one `semicolon_use` item | ~80k tokens grammar doc (+ the entire raw 42k reading doc due to the loader label bug) | **~10k tokens** |
| Generate one `words_in_context` item | zero rules (loader bug) or 42k raw | **~21k tokens, correct content** |

## Workflow

1. Edit the corrected monoliths (they remain the human-maintained source).
2. `python3 split_rules.py` — regenerates `rules/` from scratch; it exits
   non-zero if any source line goes unassigned or a B.3/B.4 heading doesn't
   map to a known focus key (so new skills added to the monolith can't be
   silently dropped).
3. Consumers read `manifest.json` and concatenate the listed files in order.

## Corrections applied to the copies (vs. the live root docs)

Grammar (v8.2-refactor): duplicate `logical_predication` B.3 entries merged
(the deleted copy carried two invalid enum values and contradictory
classifications), `comparative_structures` stub removed, `absolute_phrase`
added to D.8.1 (was failing B.13 check #1), invalid plausibility-source values
in B.4 and the B.12 Example B fixed, D.8.3 frequency bands completed for all
44 focus keys, `affirmative_agreement`/`negation` marked ANNOTATION REFERENCE
ONLY, five→six sections, 25→29 checks, C.7→C.5 amendment refs, SVA 7-sub-pattern
cap exception documented, companion-file pointer v2→v3.

Reading (v3.1-refactor): title/Purpose/model_version corrected to v3,
§2.2 §15.2→§15.3 cross-ref, `wrong_table_row_or_column` key name in §13.2,
§14.2 trap-vs-failure-mode wording, §19.7 renumbered 1–29 with synonym note,
worked-example `overstatement`→`overreach`, §4 field-status note separating
controlled-vocabulary fields from free-text fields.

Full audit trail: DEBUG_LOG.md entry 2026-08-02 at the repo root.
