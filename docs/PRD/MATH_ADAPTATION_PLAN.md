# MATH_ADAPTATION_PLAN.md

## Overview

The DSAT verbal system (`rules_agent_dsat_grammar_ingestion_generation_v7.md` +
`rules_agent_dsat_reading_v2.md`) can be replicated for the math section. The
architecture maps cleanly — the same LLM-rules-based approach applies: define a
taxonomy of question types, focus keys, and trap mechanisms; write generation
rules for constructing valid math problems; write annotation rules for
classifying existing problems; and enforce a validation checklist.

---

## Structural Parallels

| Verbal Component | Math Equivalent |
|---|---|
| `grammar_role_key` | `math_domain_key` (Algebra, Advanced Math, PSDA, Geometry) |
| `grammar_focus_key` | `math_focus_key` (e.g., `systems_linear_equations`, `quadratic_functions`) |
| `syntactic_trap_key` | `math_trap_key` (e.g., `sign_error`, `extraneous_solution`, `unit_conversion_error`) |
| `skill_family` (Boundaries, FSS) | `skill_family` (CB official: `Algebra`, `Advanced Math`, `Problem-Solving and Data Analysis`, `Geometry and Trigonometry`) |
| `stem_type_key` | `stem_type_key` (`multiple_choice` vs `student_produced_response`) |
| `distractor_type_key` | `distractor_type_key` (`arithmetic_error`, `algebraic_manipulation_error`, `wrong_formula`) |
| Passage construction rules (B.3) | Problem construction rules by focus key |
| B.13 validation checklist | Math-specific validation checklist |

---

## Key Differences Requiring New Design

### 1. Student-Produced Response (SPR) questions (~25%)

No answer choices. The output schema needs a branch:

```json
{
  "question_type": "spr",
  "correct_answer": "7/3",
  "answer_constraints": { "min": 0, "max": 9999, "decimal_allowed": true },
  "options": null
}
```

### 2. Distractor mechanics are numeric/algebraic, not textual

Instead of `nearest_noun_attraction`, math traps are:

| Trap key | Description |
|---|---|
| `sign_flip` | Student solves correctly but drops a negative |
| `extraneous_solution` | Student includes a root that fails domain check |
| `proportion_inversion` | Sets up `a/b` instead of `b/a` |
| `unit_mismatch` | Mixes meters and centimeters |
| `off_by_one_operation` | Applies one fewer or more step than required |
| `distribution_error` | Fails to distribute across all terms |
| `order_of_operations_error` | Wrong PEMDAS application |
| `wrong_formula` | Applies area formula to perimeter, etc. |
| `variable_substitution_error` | Substitutes into wrong variable or equation |
| `misread_graph` | Reads the wrong axis, data point, or interval |

### 3. Difficulty calibration uses step-count, not distractor-plausibility

In verbal, hard items have three highly plausible distractors. In math, hard
items have multi-step reasoning chains where each step is a potential error
point. The difficulty rubric needs a step-count dimension:

| Difficulty | Reasoning steps | Trap intensity | Context complexity |
|---|---|---|---|
| `low` | 1–2 direct steps | Single visible error opportunity | Numeric or simple algebraic |
| `medium` | 3–4 steps | One embedded trap; one plausible distractor | Word problem or graph read |
| `high` | 5+ steps | Multiple error points; all distractors are reachable via a plausible error path | Multi-variable, data interpretation, or geometry |

### 4. PSDA questions use tables and graphs (reuse existing schema)

Problem-Solving and Data Analysis questions embed data analogous to
`prose_plus_graph` and `prose_plus_table` in the verbal reading file. The
existing `table_data` and `graph_data` field schemas carry over unchanged.

---

## Proposed File Architecture

```
rules_agent_dsat_math_ingestion_generation_v1.md   ← analogous to grammar v7
                                                       covers all four math domains
```

A single unified file is preferred over splitting by domain because math domains
share more structural overlap than verbal's SEC/reading split. PSDA graphic
handling is included in the main file (not a separate companion), as the data
interpretation logic is tightly coupled to problem construction rules.

---

## What Carries Over Unchanged

The following sections from the verbal rules files require no structural changes,
only content substitution:

- **A.1** Operating Principles (separate what it tests / how structured / what rule solves it)
- **A.2** Mode routing (generation vs annotation detection)
- **A.3** Output shape (`question`, `classification`, `options`, `reasoning`, `generation_profile`, `review`)
- **B.2** Step-by-step generation workflow (validate → generate problem → generate correct answer → generate distractors → assemble metadata → validate)
- **B.9** Batch/deduplication and topic rotation rules
- **B.10** Explanation requirements (`explanation_short` ≤25 words, `explanation_full` ≤150 words)
- **B.13** Validation checklist structure (25-check pattern)
- **B.14** Error response format
- **C.5** Amendment process
- **C.6** Review flags
- The entire `review` section schema

---

## Taxonomy Skeleton (Part D Analog)

### `math_domain_key` values

Approved keys: `algebra`, `advanced_math`, `problem_solving_data_analysis`,
`geometry_trigonometry`

These map directly to the four official College Board math domains.

### `math_focus_key` values

#### Algebra focus keys

- `linear_equation_one_variable`
- `linear_equation_two_variables`
- `linear_function`
- `systems_linear_equations`
- `linear_inequalities`

#### Advanced Math focus keys

- `quadratic_equations`
- `quadratic_functions`
- `exponential_functions`
- `polynomial_operations`
- `rational_expressions`
- `radical_expressions`
- `function_notation`
- `equivalent_expressions`
- `systems_nonlinear_equations`

#### Problem-Solving and Data Analysis focus keys

- `ratios_rates_proportions`
- `percentages`
- `unit_conversion`
- `scatterplot_linear`
- `scatterplot_nonlinear`
- `key_features_of_graphs`
- `linear_vs_nonlinear_models`
- `probability`
- `conditional_probability`
- `sample_statistics`
- `statistical_inference`
- `two_way_table`
- `margin_of_error`

#### Geometry and Trigonometry focus keys

- `area_perimeter`
- `volume_surface_area`
- `lines_angles`
- `triangle_properties`
- `right_triangle_trig`
- `sine_cosine_relationship`
- `circles`
- `coordinate_geometry`
- `arc_length_sector_area`

---

## Disambiguation Rules Needed (D.3 Analog)

| Priority rule | Reason |
|---|---|
| `extraneous_solution` > `sign_flip` | Extraneous roots require domain checking; sign errors do not |
| `unit_conversion` > `ratios_rates_proportions` | Unit mismatch is the primary failure when units are present |
| `quadratic_equations` > `equivalent_expressions` | When solving is required, not simplifying |
| `linear_function` > `linear_equation_two_variables` | When the question asks about slope, intercept, or rate of change |
| `statistical_inference` > `sample_statistics` | When generalization to population is the tested skill |
| `coordinate_geometry` > `linear_function` | When a graph or coordinate plane is the primary medium |

---

## Recommended Build Sequence

1. **Define `math_focus_key` taxonomy** against the official CB skill breakdown,
   cross-referenced against PT1–PT11 math modules.

2. **Build problem construction rules** (B.3 analog) — one section per focus key
   with canonical problem templates, variable naming conventions, and number
   range constraints.

3. **Build distractor generation heuristics** (B.4 analog) — what wrong answers
   look like per focus key; at least three distinct distractor error types per key.

4. **Build SPR schema branch** — output schema for student-produced response
   questions including `answer_constraints`, `accepted_equivalent_forms`, and
   the No-SPR-distractor validation check.

5. **Port PSDA graphic handling** — reuse `table_data` and `graph_data` schemas
   from the reading file; add math-specific graph annotation rules (axis labels,
   units, scale).

6. **Write math validation checklist** (B.13 analog) — include math-specific
   checks: correct answer verified by back-substitution, no extraneous solutions
   included unintentionally, SPR answer falls within the gridded response range
   (0 to 9999, or fractions), distractor answers are all reachable via a named
   error path.

7. **Define difficulty calibration** using step-count rubric rather than
   distractor-plausibility rubric.

8. **Build example items** (B.12 analog) — one per major domain, with full
   annotated JSON output demonstrating both multiple-choice and SPR formats.

---

## Largest Design Decisions

| Decision | Options | Recommendation |
|---|---|---|
| Single file vs split by domain | One file vs four domain files | Single file; domains share too much structure |
| SPR handling | Separate schema vs conditional branch in main schema | Conditional branch with `question_type` field |
| PSDA as separate file | Companion to main math file (like reading v2) | Include in main file; PSDA is not as structurally different from algebra as reading is from grammar |
| Difficulty metric | Distractor-plausibility vs step-count | Step-count primary; distractor-plausibility secondary |
| Trap taxonomy | Reuse verbal keys vs build fresh | Build fresh; math traps are categorically different |

---

*Plan version: v1.0 — 2026-04-30*
*Based on: `rules_agent_dsat_grammar_ingestion_generation_v7.md` + `rules_agent_dsat_reading_v2.md`*
*Scope: Digital SAT Math Section — all four official CB domains*
