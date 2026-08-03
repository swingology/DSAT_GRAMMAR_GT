# Adoption TODO — changes outside rules_refactor/

Work identified during the 2026-08-02 rules review/refactor that must land
outside this sandbox before or alongside adoption. Ordered by urgency.

## 1. Fix the live loader bug (independent of the refactor — reading generation is broken TODAY)

`backend/app/prompts/generate_prompt.py`: the file list labels the reading doc
`"Reading v3"` (line 9) but `_generation_sections` (line 53) and the domain
filter in `_load_generation_rule_context` (line 106) compare against
`"Reading v2"`. Consequences: reading-targeted generation via
`build_generate_prompt_parts` loads **zero rules**, and grammar/"both" calls
append the **entire raw reading doc** (~42k tokens). One-line fix either way;
logged as bug-824 in `.wolf/buglog.json` and in DEBUG_LOG.md.

## 2. Replace string-marker extraction with the manifest loader

When adopting `rules/`:
- Rewrite `_load_generation_rule_context` / `build_generate_prompt_parts` to
  read `rules/manifest.json`, resolve the request's `target_grammar_focus_key`
  / `target_reading_focus_key` (or skill family), and concatenate the listed
  files. Cache the shared+core prefix; batch generation by skill family to
  keep prompt-cache hits high.
- Same change in `annotate_prompt.py` (use the `annotate` load sets; the
  existing STEM_TYPE_DOMAIN routing maps stem → domain, manifest maps
  key → files) and `review_prompt.py`.
- Update `rule_doc_patcher.py` DOC_BY_AFFECTED_DOC if amendments should patch
  the new monolith locations (recommended: amendments keep patching the
  monoliths; `split_rules.py` re-derives the modules — one source of truth).
- Update `ingestion_analysis.py` RULES_HASH paths to hash the corrected
  monoliths (and optionally `rules/manifest.json`).

## 3. vocabulary/master.json amendments (body↔appendix drift found in review)

- `REASONING_TRAP_KEYS`: **add `scope_error` and `relationship_fabrication`**
  — both defined at length in reading §10.2 but absent from the generated
  vocab, so body-legal annotations fail validation.
- `STUDENT_FAILURE_MODE_KEYS`: reading §19.7 claims `wrong_time_window` and
  `same_direction_assumption` as failure modes; the vocab only has them as
  trap/distractor keys. Either add failure-mode entries or strike the two
  rows from §19.7 — decide, then align.
- `STEM_TYPE_KEYS`: carries ~15 legacy/alias keys never defined in either
  doc body plus the near-duplicate pair `choose_words_in_context` /
  `choose_word_in_context`. Deprecate aliases (status: retired) or document
  each in a body section.
- `PASSAGE_ARCHITECTURE_KEYS`: 10 generic keys (reading §15.2) and 10
  domain-keyed keys (grammar B.7) are defined in one doc each but emitted
  into both appendices; four appear in no body at all. Reconcile.
- `STIMULUS_MODE_KEYS`: `notes_summary` exists only in the generated vocab —
  define it in a body section or retire it.
- `TOPIC_BROAD_KEYS`: reading §23.2 says "seven approved domains", vocab has
  9 (`humanities`, `arts` extra). Align the §23.2 wording.
- `scripts/gen_vocab.py`: emitted section labels are stale ("V3 §…" on
  grammar v8 blocks). Regenerate labels from current section numbers, or drop
  the labels.

## 4. Pending amendments queue (vocabulary/amendments/pending/)

All 3 pending amendments have **empty `rationale` fields** — the pipeline that
creates them isn't populating rationale/evidence (C.5 requires it). Also:
`amd-d9e2c4c66518` proposes `verb_form` into READING_SKILL_FAMILY_KEYS with
parent `conventions_grammar` — a domain-boundary leak; recommend reject and
re-route to the grammar taxonomy.

## 5. Content gaps (from the coverage review — new authoring work)

- **Poetry**: `poem` is a legal stimulus mode with zero governing rules in
  either doc. Author style/architecture/skill-mapping rules or retire the key.
- **Central Ideas & Details**: only reading skill family without a dedicated
  distractor-construction block (§16.3 covers craft families only).
- **Graphic construction**: quant CoE has no rules for building the
  table/graph itself for generated items.
- **`absolute_phrase`**: only production grammar key without a B.4 distractor
  table.
- Grammar `sentence_fragment` sub-patterns 1–2 trap assignments
  (`nominalization_obscures_subject`) flagged as directionally questionable in
  review — human check requested (kept as-is in the copies).
- PT citation spot-checks: `punctuation_comma` sub-pattern citations (PT10 M1
  Q25, PT9 M2 Q23, PT1 M1 Q20) don't obviously match their described patterns;
  4 EoI keys (`precision_word_choice`, `register_style_consistency`,
  `emphasis_meaning_shifts`, `data_interpretation_claims`) carry Tier-B PT
  counts backed by notes-synthesis items that don't test the named skill.
  Verify against the PDFs before trusting those tiers.

## 6. Drift-watch upgrades (process)

- Consistency linter: parse body enum mentions in the monoliths and diff
  against `master.json`/`ontology.py`; run in CI. Would have mechanically
  caught nearly every item in §3 above.
- Auto re-tiering: promote Tier C→B/A sub-patterns from ingestion
  classifications (B.3.0.5 explicitly allows patch-level re-tiering); the
  tier table is dated a month before the doc version.
- Umbrella-residue report: periodically list items classified under umbrella
  keys (`sentence_boundary`, `verb_form`) or carrying `review_notes`
  sub-pattern labels — that's where new official patterns surface first.
- D.8.3 frequency bands added in v8.2-refactor for 16 keys were assigned from
  tier counts + module composition; validate against ingestion statistics.
