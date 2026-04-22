# GROUND_TRUTH_GRAMMAR.md — Drift & Alignment Issues

**Date:** 2026-04-21
**Scope:** How GROUND_TRUTH flows through ingestion, annotation, generation, and validation — and where it breaks

---

## 1. Is GROUND_TRUTH Used During Ingestion?

Partially — and the linkage is fragile.

The ingestion pipeline has three layers that should all align with GROUND_TRUTH, but they don't:

| Layer | What it does | GROUND_TRUTH alignment | Drift risk |
|-------|-------------|----------------------|-----------|
| **`ontology_ref.py`** | Dynamically loads allowed keys from DB lookup tables → injects into LLM prompt | DB → prompt (live) | Low — keys come from DB |
| **`pass2_annotation.py`** | Hardcoded output schema + 11 disambiguation rules + field instructions | **Manually copied** from GROUND_TRUTH | **High** — any GROUND_TRUTH update requires manual sync |
| **`ontology.py` FIELD_TO_TABLE** | Maps field names to lookup tables for validation | Must match DB + prompt | Medium — schema drift |

The **disambiguation rules** in the prompt (lines 167-177) are a direct copy of GROUND_TRUTH Part 4 priorities 1-11. But priority 12 (`preposition_idiom > conjunction_usage`) is **missing** from the prompt. And the prompt says `conjunction_usage > parallel_structure` (priority 4), but in GROUND_TRUTH that rule applies **only when** "the error is about conjunction selection/punctuation" — the prompt doesn't carry that qualifier.

The `syntactic_trap_key` allowlist in the prompt (line 40) has **21 keys** while GROUND_TRUTH Part 7 defines **13 keys** and the v2 DB seeds exactly those 13. The prompt includes 8 extra keys (`agentless_passive`, `full_passive_by_phrase`, `object_relative_clause`, `stacked_prepositional_phrases`, `multiple_negation`, `conditional_stacking`, `long_preverbal_subject`, `tough_movement`) that **don't exist in the v2 lookup table**. The LLM will produce keys that FK-constraint-reject on insert.

---

## 2. Can GROUND_TRUTH Be Used as Generation Rules?

Yes — it already is, indirectly. The generation pipeline uses `target_*` fields from `question_generation_profiles` as constraints. These fields are populated during Pass 2 annotation, which is instructed by the GROUND_TRUTH-derived rules. So GROUND_TRUTH flows: annotation → generation profile → generation prompt constraints.

But there's a **structural gap**: GROUND_TRUTH contains knowledge that never reaches the generation prompt:

- **Distractor patterns** (Part 6) — `nearest_noun_attraction`, `tense_bait`, `partial_parallelism` etc. — these are NOT in the generation prompt or any `target_*` field. The generation prompt just says `target_distractor_construction_key` and `target_distractor_difficulty_spread`, which are too coarse to capture the specific trap pattern.
- **Disambiguation decision tree** (Part 4, Steps 1-13) — only 11 of 12 priorities are in the prompt, and the decision tree structure itself isn't provided to the LLM.
- **Passage-level tense register** (Part 8.4) — just added to the DB as `passage_tense_register_key` but the prompt doesn't reference it yet.
- **"No change" is correct** guidance (Part 8.1) — in the prompt but buried in a generic `RULES` section.

---

## 3. Overlaps

There are **4 categories of overlap** creating drift surfaces:

| Overlap | Where | Risk |
|---------|-------|------|
| **29 grammar_focus keys** | GROUND_TRUTH Part 3 ↔ DB `lookup_grammar_focus` ↔ prompt schema ↔ ontology.py | Medium — 4 copies to keep in sync |
| **12 disambiguation priorities** | GROUND_TRUTH Part 4 ↔ prompt RULES section ↔ DB `disambiguation_priority` column | High — prompt only has 11 of 12, and the DB `disambiguation_priority` column values just got corrected but the prompt still has old text |
| **13 syntactic_trap keys** | GROUND_TRUTH Part 7 ↔ DB `lookup_syntactic_trap` ↔ prompt allowlist ↔ IRT function CASE | **Critical** — prompt has 21 keys, DB has 13, IRT function has 13. 8 phantom keys in the prompt will produce FK-rejected inserts |
| **Distractor patterns** | GROUND_TRUTH Part 6 ↔ prompt instructions ↔ DB `lookup_distractor_type` | Medium — GROUND_TRUTH has specific patterns per grammar rule that never make it into `distractor_type_key` |

---

## 4. Handling Drift

Three mechanisms already exist, but none is sufficient:

1. **`ontology_proposals` table** (M-012) — lets the LLM propose new keys when it encounters a gap. This handles *discovery*, not *alignment*.

2. **`grammar_focus_frequency_evidence` table** (just added) — tracks provenance for frequency data. Doesn't prevent key mismatches.

3. **`validator.py` FK validation** — catches keys that don't exist in lookup tables. This is the **last line of defense**, not prevention.

**What's missing:**

The core problem is that **GROUND_TRUTH is a document, not a system of record**. Four places copy from it (DB seeds, prompt, ontology.py, IRT function), and there's no mechanism to detect when they diverge.

### A. Make GROUND_TRUTH the schema-of-record, not the DB

Generate the prompt's allowlists and disambiguation rules directly from DB lookup tables at runtime (which `ontology_ref.py` already does for keys). The prompt should **not** hardcode any key lists — it should inject `{ontology_reference}` for keys AND derive disambiguation rules from `lookup_grammar_focus.disambiguation_priority`.

### B. Move disambiguation rules into the DB

Currently they're just a `disambiguation_priority` integer on each `grammar_focus` row. Add a `lookup_disambiguation_rule` table with `priority`, `winner_key`, `loser_key`, `explanation` — then `ontology_ref.py` can render them dynamically.

### C. Add a startup integrity check

At app startup, after loading `app.state.ontology`, verify:

- Every key in the prompt's hardcoded allowlists exists in `ontology`
- Every `syntactic_trap_key` the IRT function handles exists in `lookup_syntactic_trap`
- Every `disambiguation_priority` pair in GROUND_TRUTH has a matching row
- Count mismatch → log warning, not crash

### D. Use the `grammar_amendment.md` process (GROUND_TRUTH Part 10) as the formal drift resolution mechanism

When the LLM proposes a new key via `ontology_proposals`, it should also trigger a GROUND_TRUTH review, not just a DB insert.

---

## 5. Most Urgent Fix

The **syntactic_trap key mismatch** (prompt has 21, DB has 13) is the most urgent — it will cause FK violations on every ingestion job that produces one of the 8 phantom keys. This needs fixing in `pass2_annotation.py` line 40 and `generation.py` line 145 before the next ingestion run.

The 8 phantom keys to remove from prompts:

| Phantom key | Status |
|-------------|--------|
| `agentless_passive` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `full_passive_by_phrase` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `object_relative_clause` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `stacked_prepositional_phrases` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `multiple_negation` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `conditional_stacking` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `long_preverbal_subject` | Not in GROUND_TRUTH Part 7, not in v2 DB |
| `tough_movement` | Not in GROUND_TRUTH Part 7, not in v2 DB |

If any of these are observed in real questions, they should be proposed via `ontology_proposals` and added to GROUND_TRUTH via the amendment process (Part 10), then seeded into the DB through a new migration. They should not be silently allowed in the prompt without DB backing.