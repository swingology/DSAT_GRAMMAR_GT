# Rules Files Anatomy

How `rules_agent_dsat_review_v1.md`, `rules_agent_dsat_reading_v2.md`, and
`rules_agent_dsat_grammar_ingestion_generation_v8.md` work together as a system.

---

## Architecture

```
                    ┌─────────────────────┐
                    │   review_v1.md      │
                    │  (evaluation layer) │
                    └──────┬──────┬───────┘
                    always │      │ additive
                           ▼      ▼
          ┌────────────────┐    ┌─────────────────┐
          │  grammar_v8    │    │  reading_v2     │
          │ (SEC + Expr.   │    │ (Info & Ideas + │
          │  of Ideas)     │    │  Craft & Struct)│
          └────────────────┘    └─────────────────┘
```

---

## What Each File Does

### grammar_v8

The *specification* for Standard English Conventions and grammar-adjacent
Expression of Ideas questions. Covers both ingestion/annotation and generation
modes. Defines:

- Full taxonomy (`grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key`)
- Passage construction rules per focus (§B.3)
- Distractor heuristics per focus (§B.4)
- Generation workflow (§B.2) and validation checklist (§B.13)
- Difficulty calibration (§B.8)
- The canonical JSON output shape used by both ingestion and generation

### reading_v2

The *additive* counterpart for reading domains (Information and Ideas, Craft
and Structure). Uses the same JSON output shape as grammar_v7 but substitutes
reading-specific taxonomy keys:

- `question_family_key`
- `reading_skill_family_key`
- `reading_focus_key`

**Domain isolation rule:** `grammar_role_key` and `grammar_focus_key` must be
`null` for all questions covered by reading_v2. Classification is determined by
what cognitive skill the correct answer requires, not by surface phrasing.

### review_v1

The *evaluation layer* that sits on top of both. Loaded after generation to
score a candidate question against a 7-dimension rubric. Its dependency on the
companion files:

| Review dimension | Threshold | How companion files feed it |
|---|---|---|
| `taxonomy_match_score` | ≥7.5 | Checks grammar_role_key/grammar_focus_key (SEC) or question_family_key/reading_skill_family_key/reading_focus_key (reading) |
| `distractor_quality_score` | ≥6.5 | Evaluates against documented failure modes and distractor heuristics from grammar_v7 §B.4 or reading_v2 equivalents |
| `realism_score` | ≥7.0 | Implicitly validates against format conventions, register, and structure rules in both files |
| `sat_fidelity_score` | ≥7.0 | Validates stem type, option count, passage length, and style norms from both files |
| `copy_risk_score` | ≤5.0 | Compares against official source examples referenced in both files |
| `difficulty_match_score` | (informational) | Uses calibration anchors from grammar_v7 §B.8 |
| `explanation_quality_score` | (informational) | Checks explanation accuracy against the taxonomy in the relevant companion file |

---

## Loading Rule

review_v1 states this explicitly:

- **grammar_v7 is always loaded** — as the prose style canon for all DSAT R&W,
  even for reading questions, because all format norms and register conventions
  originate there.
- **reading_v2 is loaded additively** — only when the candidate question is from
  a reading domain (Information and Ideas or Craft and Structure).

| Question type | Files loaded for review |
|---|---|
| SEC / Expression of Ideas | review_v1 + grammar_v7 |
| Reading (Info & Ideas, Craft & Structure) | review_v1 + grammar_v7 + reading_v2 |

---

## Pipeline Flow

```
Ingestion / Generation
  (grammar_v7 for SEC questions)
  (reading_v2 for reading questions)
        ↓
  Produces a JSON question record
        ↓
  Review agent loads review_v1
  + grammar_v7 (always)
  + reading_v2 (if reading question)
        ↓
  Scores 7 dimensions → verdict:
    accept | needs_human_review | reject
        ↓
  Verdict is advisory.
  Final decision is human.
```

`taxonomy_match_score` is the hardest gate because it directly penalizes any
generated question that violates its declared companion-file classification rules.
A question whose distractor construction, syntactic trap, or skill target
doesn't align with the grammar_v7 or reading_v2 taxonomy loses taxonomy points
regardless of how well it scores on other dimensions.

---

## Version Tracking

| File | Current version | Notes |
|---|---|---|
| `rules_agent_dsat_grammar_ingestion_generation_v8.md` | v8.0 | Production; v7 frozen as audit trail |
| `rules_agent_dsat_grammar_ingestion_generation_v7.md` | v7.0 (frozen) | Superseded by v8 — kept for audit |
| `rules_agent_dsat_reading_v2.md` | v2.0 | Production; merges v1 + v1.1 gap addendum |
| `rules_agent_dsat_review_v1.md` | v1 | Write-once rubric; create v2 for semantic changes |
