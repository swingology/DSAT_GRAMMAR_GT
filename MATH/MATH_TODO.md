# MATH_TODO — Adding DSAT Math to the Existing Backend

Decision (2026-08-03): **same repo, same backend.** Math shares the job
system, review swarm, vocabulary governance, auth, admin dashboard, student
app, and Docker/LiteLLM stack. The work below is what actually changes.
Companion ontology: `MATH/rules_agent_dsat_math_v1.md` (all keys proposed).

**Isolation contract** (mirror of the grammar↔reading rule): math gets its
own router/module and validator branch keyed off `math_domain_key`; verbal
classification fields stay null on math items and vice versa. Shared tables,
shared infra — never intermingled classification logic.

---

## Phase 0 — Vocabulary promotion (blocks everything else)

- [ ] Promote the proposed vocabularies from `MATH/rules_agent_dsat_math_v1.md`
      into `vocabulary/master.json` via the amendment pipeline:
      `MATH_DOMAIN_KEYS` (4), `MATH_SKILL_KEYS` (19), `MATH_TRAP_KEYS` (~60),
      `MATH_METHOD_KEYS` (34), `MATH_FORMAT_KEYS` (2: `mc_4choice`, `spr`),
      `DESMOS_ADVANTAGE_KEYS` (3: high/medium/low).
- [ ] Re-run `scripts/gen_vocab.py --generate` → `ontology.py` + appendices.
- [ ] Extend `QUESTION_FAMILY_KEYS` with a math axis (decide: one `math`
      family + `math_domain_key` sub-axis, or 4 family keys — recommend the
      former to keep the family enum stable).
- [ ] Amendment queue hygiene: populate `rationale` on the 3 pending verbal
      amendments while touching this pipeline (they're empty — see
      TODO_out_of_scope.md §4 in rules_refactor/).

## Phase 1 — Schema (the two hard verbal assumptions)

- [ ] `backend/app/models/db.py:93` — `current_correct_option_label`
      `Column(String(1), nullable=False)`. SPR items have **no options**.
      Migration: make nullable with a CHECK tied to `answer_format`, or use a
      sentinel `"S"`; recommend **nullable + CHECK** (`answer_format = 'spr'
      ⇔ label IS NULL`). ⚠ This column's NOT NULL already silently dropped
      questions once (2026-07-28 finding) — the migration must be paired with
      the validator change in Phase 2 in the same release.
- [ ] Add `answer_format` column (`mc_4choice` | `spr`) to `Question`,
      default `mc_4choice` so all existing verbal rows are valid unchanged.
- [ ] New `question_spr_answers` table: question_id/version_id FK, canonical
      answer (exact string), numeric value (Decimal), acceptable-forms policy
      (fraction/decimal equivalence, precision window, negative handling —
      SPR field is 5 chars, 6 with minus). One row per accepted answer;
      multiple valid answers allowed.
- [ ] `QuestionOption` unchanged for math MC. Confirm option queries filter
      by `latest_version_id` on the new paths (standing convention).
- [ ] Reuse `QuestionStimulusAsset` + `StimulusExtractionJob` for geometry
      figures and data graphics — infra already handles graph/table/poem
      crops; add math figure types to `stimulus_type` values if needed.
- [ ] Store math text as LaTeX-in-markdown in existing text columns (no
      schema change; rendering handled in Phase 3).

## Phase 2 — Validation & payload branches

- [ ] `backend/app/pipeline/validator.py:54` — `len(options) != 4` is a
      blocking check. Branch on `answer_format`: MC keeps the 4-option rule;
      SPR requires zero options + ≥1 SPR answer row.
- [ ] Add the math key branch alongside the grammar/reading branches:
      `math_skill_key` ∈ skills of `math_domain_key` (build a
      `MATH_SKILL_BY_DOMAIN` map, analog of `GRAMMAR_FOCUS_BY_ROLE`),
      verbal keys must be null on math items, math keys null on verbal.
- [ ] Keep `record_unknown_field` wired for all math_* fields so vocab drift
      feeds `vocabulary/candidates.json` from day one.
- [ ] `backend/app/models/payload.py` — add the math classification block
      (domain, skill, archetype id, trap primary + per-distractor, method
      primary + alternates, format, desmos_advantage, difficulty) per
      `MATH/rules_agent_dsat_math_v1.md` §8; conditional requirements keyed
      off `answer_format`.
- [ ] SPR grading service: equivalence checker (0.5 ≡ 1/2 ≡ 2/4; precision
      truncation vs rounding both accepted per CB rules; reject
      over-length entries). Unit-test heavily — this is the correctness core
      of math practice.

## Phase 3 — Rendering (student app + admin)

- [ ] KaTeX in `APP/STUDENT_APP_REDUX` — render LaTeX in `QuestionCard`,
      practice/diagnostic runners, and explanation views. Admin dashboard
      question browser/modal too.
- [ ] SPR input component: free-entry field with live character-count
      (5/6 chars), fraction slash, decimal point, minus; preview of the
      parsed value; no options list.
- [ ] Figure display: stimulus asset image path already exists — verify
      sizing for geometry diagrams.
- [ ] Desmos: decide embed vs external. DSAT embeds Desmos; for practice
      fidelity an embedded calculator panel is worth it (Desmos API is free
      for this use). Defer if scope-tight — students can use desmos.com.

## Phase 4 — Ingestion (highest technical risk)

- [ ] **Evaluate OCR on equation-dense pages before anything else.** GLM-OCR
      is proven on prose; math layout (fractions, radicals, exponents,
      figures) is a different regime. Bench candidates: GLM-OCR as-is,
      a math-capable VLM via LiteLLM, or MathPix-style dedicated OCR.
      Acceptance bar: ≥95% faithful LaTeX on a 2-module sample before
      building the pipeline.
- [ ] Extend Pass-2 annotation prompts with a math branch (stem→domain
      routing in `annotate_prompt.py` STEM_TYPE_DOMAIN gains math stems).
- [ ] Math answer keys: official score reports give answers per module —
      same audit workflow as the verbal PT audits (`2024_PT*_audit.md`
      pattern).
- [ ] Add math source PDFs dir to `config.py` (analog of
      `official_test_verbal_dir`).

## Phase 5 — Rules loading + generation

- [ ] Slot the math ontology into the rules_refactor structure when adopted:
      `rules/math/` beside `rules/grammar/` and `rules/reading/` —
      `MATH/rules_agent_dsat_math_v1.md` §4 archetypes are already shaped for
      per-skill splitting (26 archetypes → fragments; splitter extension is
      mechanical).
- [ ] Generation prompts: math branch in `generate_prompt.py` (after the
      manifest-loader rewrite — see rules_refactor/TODO_out_of_scope.md §1–2;
      do NOT extend the string-marker extractor).
- [ ] Distractor architecture per ontology §5.2 (trap distractor /
      procedural-slip / wrong-target; no two distractors fail identically).
- [ ] Generated-item guard: numeric answer verification — solve the generated
      item programmatically (sympy) and confirm the keyed answer before it
      reaches the review swarm. Math gives us machine-checkable ground truth
      the verbal pipeline never had; use it.
- [ ] Review rubric: extend `rules_agent_dsat_review_v1.md` with math
      criteria (answer verified, trap declared matches a distractor, Desmos
      policy §7 respected, SPR answer set complete).

## Phase 6 — Student experience

- [ ] Practice/diagnostic runners: SPR flow (submit → equivalence-grade →
      explain), reference-sheet popover (CB formula sheet), module timing
      (35 min / 22 q) for full-test mode.
- [ ] Progress tracking: extend weakness profile with `math_trap_key` — the
      math analog of `missed_syntactic_trap_key` already tracked in
      UserProgress; weakness-weighted mixed practice then covers math free.
- [ ] Section toggle in dashboard: R&W vs Math views of diagnostics/progress.

---

## Sequencing & effort sketch

Phase 0 → 1 → 2 are strictly ordered (vocab → schema → validators) and are
the enabling core (~1 week). Phase 3 rendering can run parallel to Phase 4
OCR evaluation. Phase 4 gates real content; if OCR fails the bar, math can
still launch with **generated-only** items (Phase 5's sympy verification
makes generated math trustworthy) while OCR is solved. Phases 5–6 iterate.

## Open questions (decide before Phase 1)

1. `question_family_key`: one `math` value + domain sub-axis, or 4 new
   family values? (Recommend one `math` value.)
2. Desmos embed now or defer?
3. Adaptive module-2 simulation in scope for math diagnostics, or fixed
   difficulty mix like current verbal practice?
4. Does the review swarm get a math-capable local model, or is qwen3.6:27b
   sufficient for review? (Generation likely wants a stronger math model via
   LiteLLM cloud fallback.)
