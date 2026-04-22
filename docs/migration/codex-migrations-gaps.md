# Codex Review: Migrations PRD v2 Gap Analysis

**Date:** 2026-04-20  
**Reviewed:** `docs/Migrations_PRD_v2_rebuild.md` + `docs/superpowers/specs/2026-04-20-migrations-prd-v2-gap-analysis.md`  
**Verdict:** Not ready to execute as-is — all issues are fixable.

---

## Blocking SQL Bugs

### 1. `v_coaching_panel` will fail to create
**Location:** `Migrations_PRD_v2_rebuild.md` M-020  
`json_agg(DISTINCT json_build_object(...) ORDER BY ss.step_index)` is invalid in PostgreSQL — `json` has no equality operator required for `DISTINCT`.

**Fix:** Use a subquery to pre-order solver steps, or switch to `jsonb_agg`:
```sql
-- Instead of:
json_agg(DISTINCT json_build_object(...) ORDER BY ss.step_index)

-- Use:
(SELECT jsonb_agg(x ORDER BY x->>'step_index')
 FROM (SELECT DISTINCT jsonb_build_object(...) AS x FROM solver_steps ss WHERE ss.question_id = q.id) sub)
```

---

### 2. `v_corpus_fingerprint` unique index is incomplete
**Location:** `Migrations_PRD_v2_rebuild.md` M-020  
`domain_key` is included in the `GROUP BY` but is absent from the unique index. Two domains with the same style tuple would collide on `REFRESH MATERIALIZED VIEW CONCURRENTLY`.

**Fix:** Add `domain_key` to the unique index:
```sql
CREATE UNIQUE INDEX idx_v_corpus_fingerprint
    ON v_corpus_fingerprint(
        question_family_key, domain_key,  -- add domain_key
        syntactic_complexity_key, lexical_tier_key,
        inference_distance_key, evidence_distribution_key, prose_register_key
    );
```

---

### 3. `fn_refresh_irt_b()` silently skips NULL rows
**Location:** `Migrations_PRD_v2_rebuild.md` M-019  
`irt_b_source != 'field_test'` and `irt_b_rubric_version NOT IN ('empirical','manual')` both evaluate `NULL` as unknown — rows with no source/rubric set are silently excluded from the refresh.

**Fix:** Use `IS DISTINCT FROM`:
```sql
WHERE (p_question_id IS NULL OR question_id = p_question_id)
  AND (irt_b_rubric_version = 'v1' OR irt_b_source IS NULL)
  AND irt_b_source IS DISTINCT FROM 'field_test'
  AND (irt_b_rubric_version IS NULL
       OR irt_b_rubric_version NOT IN ('empirical','manual'));
```

---

### 4. RLS enabled on `generated_questions` with no policies
**Location:** `Migrations_PRD_v2_rebuild.md` M-021  
RLS is enabled but no row-level policies are defined. Authenticated clients get zero access; only service-role connections bypass this.

**Fix:** Either add policies alongside the `ENABLE ROW LEVEL SECURITY` call, or defer enabling RLS until policies are written:
```sql
-- Option A: add a permissive policy for service role reads
CREATE POLICY "service_role_all" ON generated_questions
    USING (true) WITH CHECK (true);

-- Option B: defer RLS — remove ALTER TABLE ... ENABLE ROW LEVEL SECURITY from M-021
```

---

## Seed / Dependency Ordering

The PRD states M-022–M-028 can run in parallel after M-003. **This is false.**

### Actual dependency chain:

| Migration | Depends On | Reason |
|---|---|---|
| M-022 | M-003 | Seeds `lookup_stimulus_mode`, `lookup_stem_type`, `lookup_question_family` — tables created in M-003 |
| M-023 | M-004 | `lookup_skill_family.domain_key` FK requires `lookup_domain` seeds from M-004 |
| M-024 | M-013 + M-022 | Inserts into `generation_templates` (created M-013); uses `question_family_key` values from M-022 seeds |
| M-025 | M-016 | Inserts into `grammar_keys` (created M-016) |

### Impact on first writes:
- `questions` has NOT NULL FKs to `lookup_stimulus_mode` / `lookup_stem_type` — no inserts succeed until M-022 runs
- `question_classifications` NOT NULL FKs also require M-023 seeds (`lookup_skill_family`, `lookup_evidence_scope`, `lookup_evidence_location`, `lookup_answer_mechanism`, `lookup_solver_pattern`)

### Fix options:
1. **Move critical lookup seeds into M-004** alongside the grammar seeds (preferred — keeps "all vocab seeded before first write" invariant)
2. **Document a strict rule:** no data writes until M-028 is complete

---

## Gap Analysis Accuracy (`migrations_diff.md`)

The gap analysis is mostly accurate. Key inconsistency:

- It correctly flags `lookup_skill_family` seed timing as a problem
- It **understates** the issue — doesn't capture the full M-022–M-028 interdependency chain
- The claim "M-022–M-028 can run in parallel after M-003" is repeated from the PRD without correction
- M-004 is mislabeled "Seed All Lookup Tables" — it only seeds a subset (grammar roles, grammar focus, domain, passage topic fine, coaching annotation types, reasoning step types, dimension compatibility)

---

## What Does Not Need Fixing

- **FK forward references** — no trigger or constraint references a table before it exists. `fn_check_paired_retirement()` references `questions` inside PL/pgSQL which is compiled lazily — valid.
- **M-017/M-018 trigger timing** — all integrity triggers are installed after their target tables exist.
- **Overall schema structure** — dependency ordering for tables is correct across all 8 phases.

---

## Priority Order for Fixes

| Priority | Issue | Effort |
|---|---|---|
| P0 | Seed ordering — move critical seeds to M-004 or enforce strict run order | Medium |
| P0 | Fix `v_coaching_panel` `json_agg(DISTINCT)` | Small |
| P1 | Fix `fn_refresh_irt_b()` NULL logic | Small |
| P1 | Fix `v_corpus_fingerprint` unique index (add `domain_key`) | Trivial |
| P2 | Add RLS policies for `generated_questions` or defer RLS | Small |
