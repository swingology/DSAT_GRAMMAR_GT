# DSAT rules and vocabulary standard — v1.0.0

Established 2026-09-06 as the reference baseline for subsequent work. This
standard freezes terminology and change policy; it is not a claim that a new
database schema or official-classification adapter has been deployed.

## Authority and scope

1. **Official assessment classification:** College Board's *Assessment Framework
   for the Digital SAT Suite*, version 3.01 (August 2024), Table A33, printed
   pages 184–185 (PDF pages 194–195). See the [source](https://satsuite.collegeboard.org/media/pdf/assessment-framework-for-digital-sat-suite.pdf#page=194).
   Its names and hierarchy are recorded in `vocabulary/v1.0.0/college_board.json`.
   The `cb.*` identifiers are our stable identifiers, not College Board-issued codes.
2. **Existing production vocabulary:** `../vocabulary/master.json`, following
   approved rule amendments. A byte-exact copy is frozen in
   `vocabulary/v1.0.0/master.snapshot.json`. Existing strings, parents, statuses,
   and meanings are preserved. This includes legacy inconsistencies, not an
   endorsement that every active key is an official testing point.
3. **Generation/annotation rules:** corrected monoliths and splitter in
   `../rules_refactor/`; `rules/` here is a generated reference snapshot.
   The baseline lock hashes every module and its source inputs. Generation
   quality rules, style guidance, and heuristics are project policy unless
   individually attributed to College Board. Annotation describes observed
   items; it must not force generation-design requirements onto official items.
4. **Research and publisher material:** candidate inputs only. The CGPT ontology
   proposal remains a proposal; it cannot override this standard or create
   production keys by being included in a prompt.

The official hierarchy has four domains and ten skills. Command of Evidence
has Textual and Quantitative subdivisions; keeping these separate in our
existing seven reading families yields eleven operational routes overall.
Detailed grammar testing points are preserved below their official skills.
Do not flatten domains, skills, and testing points into one key list.

## Identity and collision rules

- Identify an existing term by `(vocabulary category, value, parent if any)`.
  A repeated string in two fields does not make those fields interchangeable.
- Keep official classification (`cb.*`), existing internal concepts
  (`internal.<category>.<value>`), and imported research terms
  (`research.<source>.<local_id>`) separate. These namespaced identities are
  reference-layer IDs; do not put them into current database enum fields.
- Preserve imported label, publisher/paper, edition/date, source location,
  definition, example, and original annotation. Never normalize by spelling
  alone. Case-folding is allowed for lookup only within the declared source
  and field, after a mapping is approved.
- Every mapping declares `equivalent`, `narrower`, `broader`, `related`, or
  `unresolved`. Only a reviewed equivalent mapping is an alias. Broad-to-fine
  mappings require item evidence; one-to-many mappings require reannotation.
- Official skill labels such as Boundaries and Rhetorical Synthesis must not
  be written to `reading_skill_family_key`. This field is reading-only in the
  current contract. Preserve the source label and queue it for a future
  official-classification adapter; do not discard it or invent a reading key.
- Unknown or conflicting concepts enter the existing candidate/amendment
  workflow. They stay non-production until definitions, scope, examples,
  counterexamples, mappings, and consumer checks are reviewed.
- Precedence for tested scope: official framework and item evidence, then
  approved internal definitions. Publisher shortcuts cannot redefine a skill.
  Supporting grammar/style concepts remain useful without becoming standalone
  official generation targets.

## Frozen baseline and changes

`vocabulary/v1.0.0/` contains:

- `college_board.json`: sourced official hierarchy with local stable IDs.
- `master.snapshot.json`: complete existing vocabulary, unchanged.
- `crosswalk.json`: mappings for existing question families, reading families,
  all grammar focus entries (including parent distinctions), and synthesis
  routing. Mapping hints are not executable migration instructions.
- `changes.json`: initial change ledger and observed collision evidence.
- `baseline.lock.json`: SHA-256 hashes for the release files, rules, sources,
  and existing enforcement/prompt inputs. This is a filesystem baseline, not
  a database backup or reproducibility guarantee for a remote model.

No existing production key was renamed, removed, or reparented in v1.0.0.
No database rows or historical annotations were changed. Official IDs are
additive reference metadata. The frozen master remains the compatibility
baseline; the active master remains the runtime enforcement source.

Run `rtk proxy python3 chatgpt_refactor_rules/verify_standard.py` from the repo
root to check the frozen release, key coverage, and current-file drift. Do not
silently refresh the lock to make a drift check pass: record a new release.

## Required record for every later vocabulary change

Never edit a released snapshot in place. Add a release and ledger entry with:

| Field | Required contents |
|---|---|
| Identity | Change ID, old/new standard version, date, approved amendment and reviewer |
| Meaning | Old/new category, key, parent, definition, status; mapping relationship |
| Evidence | Source/version/location, examples, counterexamples, reason for change |
| Compatibility | Unchanged, alias, rename, merge, split, reparent, retirement, or new concept |
| Consumers | Model fields, relational rows, JSONB annotations, prompts, validators, APIs, UI, exports, analyses, cached artifacts |
| Migration | Script/revision, selection predicate, dry-run counts, ambiguous IDs, old/new checksums, validation results |
| History | Original annotation/version, derived annotation/version, method, timestamp, reviewer |
| Rollback | Backup/snapshot reference, inverse mapping where lossless, restoration procedure |

Patch releases clarify wording without changing meaning or accepted values.
Minor releases add compatible terms/mappings. Renames, removals, splits,
merges, reparenting, or changed meanings require a major release and an
explicit migration. Reusing a retired ID for another meaning is prohibited.

## Path to database adoption

1. Inventory consumers and stored values, including original JSONB, generated
   questions, exports, and prior analyses. Measure collision counts against
   the actual database; the candidate queue is not a database census.
2. Add a versioned official classification representation alongside existing
   internal classification. Do not overload reading-only fields. Validate
   domain–skill–testing-point relationships and retain source labels.
3. Use reviewed crosswalks to derive classifications. Conflicting evidence or
   broad legacy keys must produce a review queue, not a guessed subtype.
4. Dry-run migration and record before/after counts, unchanged records,
   unmapped records, and proposed changes. Preserve original payloads and IDs.
   Update derived datasets with a versioned transform rather than rewriting
   historical reports to look as if they originally used the new standard.
5. Promote approved amendments into the active master and run the existing
   vocabulary generator/checker; update prompts, source rules, split modules,
   and API/UI readers together. Check the generator's document targets first:
   its reading target currently names v2 while active generation uses v3.
6. Verify on reviewed annotation examples and matched generated items, then
   activate writers. Keep old-version readers and rollback artifacts.

## Release v1.1.0 (2026-09-20) — official skill adopted in the database

Minor release: adds compatible terms and mappings. Nothing was renamed, removed, split,
merged or reparented, and no historical annotation was changed. Ledger:
`vocabulary/v1.1.0/changes.json` (VOC-0004 to VOC-0007).

- **Adoption steps 1-4 are done.** Collisions were measured against the actual database
  (step 1). The official classification sits *alongside* the internal one in new columns —
  `questions.skill_key` plus College Board's source labels in `cb_*` — and the reading-only
  `skill_family_key` was deliberately not overloaded (step 2). Classifications are derived
  from College Board's own labels where a bank match exists, otherwise from a crosswalk
  derived from those labels; ambiguous keys stay NULL for review (step 3). Both fills were
  dry-run first with counts recorded (step 4).
- **The v1.0.0 crosswalk was tested against College Board ground truth** and agrees on
  95.5% of matched rows. Its two weak grammar entries, `comma_splice` and
  `run_on_sentence`, are the same two the derived map sends to review.
- **Steps 5-6 remain:** no reader uses `skill_key` yet. Every reader must take the domain
  from the skill, never from the annotation's routing domain — they disagree on about 100
  official rows.
- **Not versioned per row.** `skill_key` values are production keys from
  `SKILL_FAMILY_BY_QUESTION_FAMILY`; v1.1.0's crosswalk maps each one to its official ID.
  A per-row standard-version column was not added; add it with the first change that alters
  an existing key's meaning.
- To verify: `python3 chatgpt_refactor_rules/verify_standard.py`. It checks the latest
  release; `vocabulary/v1.0.0/` stays frozen as released.

v1.0.0 established the starting standard and compatibility record.
Runtime adapter implementation, database migration, semantic term promotion,
and measured question-quality evaluation are subsequent tracked work.
