# Grammar Taxonomy + DB Schema Alignment Design

**Date:** 2026-04-21
**Scope:** Resolve inconsistencies between GROUND_TRUTH_GRAMMAR.md, DSAT_Verbal_Master_Taxonomy_v2.md, and Migrations_PRD_v2_rebuild.md
**Approach:** Minimal Alignment (no new lookup tables, no schema changes)

---

## Inconsistencies Found

### 1. Missing grammar_focus keys in taxonomy v2 (3 keys)

The taxonomy v2 Section 7.4 lists 26 keys; the PRD seeds 29. Missing from taxonomy:
- `appositive_punctuation` (punctuation) — added to GROUND_TRUTH v1.1
- `quotation_punctuation` (punctuation) — added to GROUND_TRUTH v1.1
- `preposition_idiom` (verb_form) — added to GROUND_TRUTH v1.2

The taxonomy v2's Section 7.4 JSON was not updated when these keys were added to GROUND_TRUTH.

### 2. Role mapping conflicts (2 keys)

| Key | PRD role | Taxonomy v2 role | GROUND_TRUTH section | Resolution |
|---|---|---|---|---|
| `affirmative_agreement` | `agreement` | `verb_form` | Section 3.2 (Agreement Rules) | `agreement` — matches GROUND_TRUTH section placement |
| `elliptical_constructions` | `verb_form` | `parallel_structure` | Section 3.6 (Parallel Structure Rules) | `parallel_structure` — matches GROUND_TRUTH section placement |

The PRD seed data has `affirmative_agreement → agreement` (correct) but `elliptical_constructions → verb_form` (wrong — should be `parallel_structure`).

### 3. lookup_syntactic_interruption table undefined

PRD creates `lookup_syntactic_interruption` in M-003 and references it from `question_classifications.syntactic_interruption_key` and `question_generation_profiles.target_syntactic_interruption_key`. Neither GROUND_TRUTH nor taxonomy v2 defines what keys go in it.

The concept is distinct from `syntactic_trap`: interruption measures how much an intervening structure breaks a grammatical connection (e.g., subject-verb), while trap identifies the specific misleading structural pattern. An interruption can be present without a trap, and vice versa.

Proposed keys (4):

| Key | Display Name | Description |
|---|---|---|
| `none` | No Interruption | Direct subject-verb or modifier-head connection |
| `minor` | Minor Interruption | Short prepositional phrase or single modifier between connected elements |
| `moderate` | Moderate Interruption | Appositive phrase, short parenthetical, or coordinate expansion between connected elements |
| `severe` | Severe Interruption | Long interrupting clause, stacked modifiers, or multiple parentheticals between connected elements |

### 4. Distractor and style lookup tables missing seed data

PRD creates these tables in M-003 but seed data for them is in M-022–M-028 (not shown in the PRD doc). All need seed definitions aligned with taxonomy v2 Section 4.

### 5. Taxonomy v2 Section 7.4 missing disambiguation rule

GROUND_TRUTH Part 4 and taxonomy v2 Section 7.4 both list 12 priority rules, but the taxonomy v2 is missing priority 12 (`preposition_idiom > conjunction_usage`) because the key itself is missing from the taxonomy.

---

## Changes

### GROUND_TRUTH_GRAMMAR.md

1. **Add inline `mapping_to_grammar_role`** to each Part 3 entry header (currently says "Each key maps to a grammar_role_key via mapping_to_grammar_role" but doesn't show the mapping inline — readers must cross-reference the taxonomy v2)

2. **Add explicit role note for `affirmative_agreement`**: clarify that its canonical role is `agreement` despite some taxonomies mapping it to `verb_form`. The agreement interpretation matches: so/neither inversion agrees with the antecedent clause's auxiliary, which is an agreement pattern, not a verb-form pattern.

3. **Add cross-reference** to PRD lookup table names in Part 7 (Syntactic Traps) for `syntactic_interruption_key` — document the proposed 4-key set.

4. **Add Part 9: Lookup Table Seed Reference** — reference table listing each lookup table, its source document, and whether seeds are defined.

### DSAT_Verbal_Master_Taxonomy_v2.md (Section 7.4)

1. **Add 3 missing keys** to `grammar_focus_key.allowed_values` and `mapping`:
   - `appositive_punctuation` → `punctuation`
   - `quotation_punctuation` → `punctuation`
   - `preposition_idiom` → `verb_form`

2. **Fix `affirmative_agreement` mapping**: `verb_form` → `agreement`

3. **Add missing disambiguation rule**: priority 12 `preposition_idiom > conjunction_usage`

4. **Update amendment log** with v2.1 entry documenting these changes

### Migrations_PRD_v2_rebuild.md (M-004 seed data)

1. **Fix `elliptical_constructions` role**: change from `verb_form` to `parallel_structure` to match GROUND_TRUTH section placement

### New: Seed Data Addendum (`docs/seed_data_addendum.md`)

Define seed data for all lookup tables created in M-003 that are seeded in M-022–M-028:

- `lookup_syntactic_interruption` — 4 keys (defined above)
- `lookup_syntactic_trap` — 13 keys from GROUND_TRUTH Part 7
- `lookup_distractor_type` — 4 family keys from taxonomy v2 Section 4
- `lookup_distractor_subtype` — 25 specific patterns from taxonomy v2 Section 4.1–4.5
- `lookup_distractor_construction` — 8 keys from taxonomy v2 Section 4.5 + 4.6
- `lookup_semantic_relation` — 8 keys from taxonomy v2 Section 4.7
- `lookup_plausibility_source` — 6 keys from taxonomy v2 Section 4.6
- `lookup_eliminability` — 3 keys
- Style/difficulty lookup tables: `lookup_syntactic_complexity` (5), `lookup_lexical_tier` (5), `lookup_inference_distance` (5), `lookup_evidence_distribution` (5), `lookup_noun_phrase_complexity` (3), etc.

### New: REBUILD_FUTURE_PLANS.md

Document the full reconciliation approach (Approach 3 from brainstorming) for future implementation.

---

## Not Changing

- No new lookup tables (rhetorical_device, style_trait deferred)
- No restructuring of distractor tables into 4-family model
- No new grammar_focus keys beyond the 29 already defined
- No schema changes to question_classifications or question_generation_profiles