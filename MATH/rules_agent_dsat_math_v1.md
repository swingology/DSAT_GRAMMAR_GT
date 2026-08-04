# rules_agent_dsat_math_v1.md

## Purpose

This file is the DSAT **Math** ontology — the companion layer to
`rules_agent_dsat_grammar_ingestion_generation_v8.md` (SEC / Expression of
Ideas) and `rules_agent_dsat_reading_v3.md` (Information & Ideas / Craft &
Structure). It catalogs every official Digital SAT Math question type with:

- **Topic** — the field of math (`math_domain_key` → `math_skill_key`)
- **Trap** — the named error mechanism the item exploits (`math_trap_key`)
- **Intuition** — the conceptual insight that dissolves the trap
- **Named method** — a registered solution method (`math_method_key`)
- **Process** — the step-by-step execution of that method

Keys follow the house conventions: snake_case controlled vocabularies,
annotation uses only approved keys, and unknown patterns route through the
amendment process (§9) rather than invented keys. All keys in this v1 are
**proposed** — none are in `vocabulary/master.json` yet; promotion happens via
the standard amendment pipeline.

## Test facts (structural constants)

- Two adaptive modules, **22 questions each** (20 scored + 2 pretest), 35 min/module.
- ~75% four-option multiple choice (`mc_4choice`), ~25% student-produced
  response (`spr`). SPR: up to 5 characters (6 with a leading minus); fraction
  or decimal equivalents both accepted; never round early.
- **Desmos calculator available on every question.** Every archetype below
  notes when a Desmos path beats algebra.
- Domain weights: Algebra ~35% (13–15 q), Advanced Math ~35% (13–15 q),
  Problem-Solving & Data Analysis ~15% (5–7 q), Geometry & Trigonometry
  ~15% (5–7 q).

---

# 1. Taxonomy

## 1.1 `math_domain_key` (4)

| Key | Official domain |
|---|---|
| `algebra` | Algebra |
| `advanced_math` | Advanced Math |
| `problem_solving_data_analysis` | Problem-Solving and Data Analysis |
| `geometry_trigonometry` | Geometry and Trigonometry |

## 1.2 `math_skill_key` (19, grouped by domain)

| Domain | Skill keys |
|---|---|
| `algebra` | `linear_equations_one_var`, `linear_equations_two_var`, `linear_functions`, `systems_two_linear`, `linear_inequalities` |
| `advanced_math` | `equivalent_expressions`, `nonlinear_equations_and_systems`, `nonlinear_functions` |
| `problem_solving_data_analysis` | `ratios_rates_units`, `percentages`, `one_variable_data`, `two_variable_data`, `probability_conditional`, `sample_inference_moe`, `evaluating_statistical_claims` |
| `geometry_trigonometry` | `area_volume`, `lines_angles_triangles`, `right_triangles_trig`, `circles` |

## 1.3 `math_format_key` (2)

`mc_4choice` | `spr`

## 1.4 Difficulty

Same 3-band scale as the verbal docs (`low` / `medium` / `high`). Hard math
items are hard because of **trap density and multi-step chaining**, not exotic
content — mirror of the verbal doctrine that difficulty must come from
distractor competition, not obscure vocabulary.

---

# 2. Trap Taxonomy — `math_trap_key`

One primary trap per item; distractors in MC items should each embody a
distinct trap where possible (mirror of the verbal "no two distractors fail
for the same reason" rule).

## 2.1 Cross-domain traps (any skill)

| Key | Mechanism |
|---|---|
| `answers_intermediate_quantity` | Item asks for `2x + 1` or `y − x`; solver stops at `x`. The single most common DSAT math trap; the intermediate value is always a distractor. |
| `sign_error` | Dropped or flipped negative during isolation, distribution, or substitution |
| `order_of_operations` | Premature addition before multiplication/exponentiation; mis-nested fractions |
| `unit_mismatch` | Mixed units (min vs hr, cm vs m, cm² vs cm³) survive into the answer |
| `misread_quantity` | Solves for the right object but wrong instance (perimeter vs area, first year vs final year, Model A vs Model B) |
| `decimal_place_slip` | Percent ↔ decimal conversion off by factor of 100/10 |
| `rounded_too_early` | Intermediate rounding propagates; SPR answer misses accepted range |

## 2.2 Algebra traps

| Key | Mechanism |
|---|---|
| `inequality_flip_missed` | Dividing/multiplying inequality by a negative without reversing the sign |
| `slope_intercept_confusion` | Swaps m and b when interpreting `y = mx + b` in context; rate assigned to intercept or vice versa |
| `slope_direction_inverted` | Uses Δx/Δy; or reads decreasing line as positive slope |
| `no_vs_infinite_solutions` | Confuses parallel (no solution: equal slopes, different intercepts) with coincident (infinite: proportional everything) |
| `intercept_context_error` | Interprets x-intercept as starting value or y-intercept as break-even point |
| `boundary_inclusion_error` | Strict vs inclusive inequality (open vs closed boundary; "at least" vs "more than") |
| `parallel_perpendicular_swap` | Uses equal slope where negative reciprocal is required, or vice versa |
| `variable_role_swap` | Defines x as the wrong actor in a word problem; system equations transposed |

## 2.3 Advanced Math traps

| Key | Mechanism |
|---|---|
| `distributed_exponent` | `(a + b)² → a² + b²`; binomial square without middle term |
| `zero_sign_flip` | Factored form `(x − 3)` read as zero at `−3`; vertex form `(x − h)` read as `h` negative |
| `extraneous_solution_kept` | Squaring a radical equation or clearing a rational denominator introduces a root that fails the original; solver keeps it |
| `valid_solution_discarded` | Overcorrects: discards a legitimate root along with the extraneous one |
| `exponent_rule_blend` | Product/power/quotient rules cross-applied: `x²·x³ = x⁶`, `(x²)³ = x⁵` |
| `negative_exponent_error` | `x⁻²` treated as `−x²` |
| `function_notation_shift` | `f(x + 2)` conflated with `f(x) + 2`; horizontal shift direction inverted |
| `vertex_readoff_error` | Reads vertex from standard form without completing the square, or sign-flips `h` |
| `discriminant_misuse` | Sets discriminant `> 0` when "exactly one solution" (`= 0`) is required, or ignores it entirely for "no real solutions" |
| `growth_decay_swap` | Uses `(1 + r)` for decay or `(1 − r)` for growth; or treats exponential change as linear (`percent_as_linear`) |
| `domain_restriction_ignored` | Rational/radical function evaluated where undefined; denominator zero accepted as solution |
| `asymptote_as_intercept` | Treats horizontal asymptote value as an attainable output or intercept |

## 2.4 Problem-Solving & Data Analysis traps

| Key | Mechanism |
|---|---|
| `percent_wrong_base` | Percent computed off the wrong base (final instead of original; part instead of whole) |
| `successive_percent_added` | 20% up then 20% down treated as net 0%; compound change treated additively |
| `ratio_part_whole_confusion` | Part-to-part ratio used where part-to-whole is needed, or inverted |
| `proportion_inverted` | Cross-multiplication set up with mismatched correspondence |
| `rate_inverted` | Uses hours per mile where miles per hour is needed; unit-rate denominator flipped |
| `mean_median_conflation` | Applies mean reasoning to median questions; ignores skew/outlier asymmetry |
| `average_of_averages` | Averages two group means without weighting by group size |
| `spread_center_confusion` | Answers about standard deviation with center logic, or vice versa |
| `wrong_table_cell` | Two-way table lookup off by a row/column (shared ancestor of the verbal `wrong_table_row_or_column`) |
| `conditional_universe_error` | Conditional probability computed over the whole table instead of the restricting row/column |
| `and_or_probability_blend` | P(A and B) vs P(A or B) confusion; double-counts the intersection |
| `moe_misinterpretation` | Margin of error applied to individuals or to sample statistics rather than the population parameter; or "plausible range" read as certainty |
| `sample_size_moe_inverted` | Believes larger sample → larger margin of error |
| `causation_from_observation` | Infers causation without random assignment |
| `overgeneralized_sample` | Generalizes beyond the sampled population (no random sampling) — shares DNA with the reading `subgroup_overgeneralization` failure mode |
| `line_of_fit_point_confusion` | Reads a data point where the model prediction (line value) is asked, or vice versa; residual sign confusion |
| `extrapolation_beyond_data` | Trusts the fit line far outside the observed x-range |

## 2.5 Geometry & Trigonometry traps

| Key | Mechanism |
|---|---|
| `radius_diameter_swap` | Uses diameter where radius belongs (area, circle equation, volume) |
| `circle_equation_sign_flip` | Center read as `(−h, −k)` from `(x − h)² + (y − k)² = r²`; or `r²` reported as `r` |
| `angle_relationship_misuse` | Wrong pairing among vertical/supplementary/corresponding/alternate-interior angles |
| `similar_correspondence_error` | Ratio built from non-corresponding sides of similar triangles |
| `area_ratio_not_squared` | Linear scale factor k applied to area (should be k²) or volume (k³) |
| `trig_side_misidentified` | Opposite/adjacent assigned from the wrong acute angle |
| `cofunction_blindness` | Misses `sin x° = cos(90° − x°)` when the item is built on it |
| `pythagorean_leg_hypotenuse` | Treats a leg as the hypotenuse (or misses that the "hypotenuse" must be the longest side) |
| `special_triangle_misratio` | 30-60-90 / 45-45-90 side ratios misassigned |
| `arc_angle_proportion_error` | Arc length or sector area not scaled by central-angle/360 (or degree–radian mix) |
| `exterior_angle_misuse` | Exterior angle set equal to one remote interior angle instead of their sum |
| `volume_formula_blend` | Cone/cylinder/sphere formulas cross-contaminated (drops the 1/3, wrong power of r) |

---

# 3. Named Method Registry — `math_method_key`

Every archetype in Part 4 references one primary method from this registry
(plus optional fallbacks). Methods are teachable, nameable processes — the
math analog of the verbal solver_pattern_keys.

| Key | Name | One-line definition |
|---|---|---|
| `direct_translation` | Direct Translation | Convert words → symbols clause by clause; define variables with units before writing anything |
| `isolate_and_verify` | Isolate & Verify | Standard inverse-operations solve, then substitute the answer back into the ORIGINAL equation |
| `answer_the_question` | Answer-the-Question Check | Final step of every solve: re-read the stem, confirm the asked quantity (kills `answers_intermediate_quantity`) |
| `coefficient_matching` | Coefficient Matching | For identities / no-solution / infinite-solution items: equate coefficients of like terms on both sides |
| `slope_first_read` | Slope-First Read | In any linear context, identify and interpret the rate (slope) with its units before touching the intercept |
| `anchor_point_fit` | Anchor-Point Fit | Build a linear/exponential model from a table by locking one point, then fitting the rate from a second |
| `backsolving` | Backsolving | Plug answer choices into the stem, starting from B/C; MC only |
| `smart_numbers` | Smart Numbers | Replace abstract quantities with concrete convenient values (100 for percents, LCM for fractions); verify the target expression |
| `desmos_intersect` | Desmos Intersect | Graph both sides / both equations; read intersection coordinates directly |
| `desmos_zero_scan` | Desmos Zero Scan | Graph the single expression; read zeros, vertex, intercepts, asymptotes off the plot |
| `test_point_shading` | Test-Point Shading | For inequalities: test (0,0) (or another off-boundary point) to pick the half-plane; check boundary inclusion |
| `structure_spotting` | Structure Spotting | Treat a repeated sub-expression as a single unit u; rewrite, manipulate, substitute back |
| `zero_product_split` | Zero-Product Split | Factor to (·)(·) = 0 and split into cases; each factor is a candidate root |
| `complete_the_square` | Complete the Square | Force `(x ± h)²` structure to expose vertex or circle center/radius |
| `discriminant_census` | Discriminant Census | Compute b² − 4ac and map sign → number/type of real solutions before solving anything |
| `growth_template_match` | Growth-Template Match | Force the situation into `y = a·(1 ± r)^t`; identify a, direction, r, and the time unit of t |
| `exponent_ledger` | Exponent Ledger | Rewrite every term as a power of a common base; track exponents additively in one ledger line |
| `plug_in_check_domain` | Domain Gate | After solving radical/rational equations, test every root in the ORIGINAL equation; reject denominator-zeros and sign violations |
| `unit_chain` | Unit-Chain Cancellation | Dimensional analysis: chain conversion fractions so units cancel diagonally to the target unit |
| `base_lock` | Base Lock | Before any percent computation, write down "percent OF WHAT" — lock the base quantity explicitly |
| `weighted_balance` | Weighted Balance | Combined averages via total = Σ(group mean × group size); never average the averages |
| `outlier_stress_test` | Outlier Stress Test | To compare mean vs median: mentally remove/exaggerate the outlier and watch which measure moves |
| `moe_bracket` | MOE Bracket | Construct [estimate − MOE, estimate + MOE]; all claims must be about the population parameter inside that bracket |
| `randomization_gate` | Randomization Gate | Two independent switches: random SAMPLING → generalize to population; random ASSIGNMENT → infer causation. Check each separately |
| `row_restriction` | Row Restriction | For conditional probability: physically cover the table, keep only the restricting row/column as the new universe |
| `correspondence_lock` | Correspondence Lock | In similar figures: match vertices by angle FIRST, then build side ratios only from locked pairs |
| `angle_chase` | Angle Chasing | Propagate known angles through vertical/linear-pair/parallel-line/triangle-sum relations until the target falls out |
| `triangle_reorientation` | Triangle Re-Orientation | Redraw the triangle with the reference angle bottom-left before assigning opposite/adjacent/hypotenuse |
| `cofunction_swap` | Cofunction Swap | Apply sin x° = cos(90° − x°) whenever a sine and cosine of different acute angles are equated |
| `radius_extraction` | Radius Extraction | Rewrite any circle equation into standard form via complete_the_square; read center and r (not r²) deliberately |
| `central_angle_proportion` | Central-Angle Proportion | Arc/sector quantities = (central angle / 360°) × full-circle quantity; one proportion, everything scales |
| `pythagorean_anchor` | Pythagorean Anchor | Identify the right angle, anchor the hypotenuse opposite it, then apply a² + b² = c² or a known triple (3-4-5, 5-12-13) |
| `scale_factor_power` | Scale-Factor Power | Length ratio k → area ratio k² → volume ratio k³; decide the power before computing |
| `formula_sheet_recall` | Formula-Sheet Recall | The DSAT reference sheet carries all area/volume/special-triangle formulas — retrieve, don't reconstruct |

---

# 4. Question-Type Catalog

Format per archetype:

> **Topic** · **Trap** · **Intuition** · **Method** · **Process**

---

## 4.1 Domain: `algebra`

### `linear_equations_one_var`

**Archetype A1 — Solve and report a transformed quantity**
- **Topic**: algebra / linear equations in one variable
- **Trap**: `answers_intermediate_quantity` (primary), `sign_error`
- **Intuition**: The equation is never the question. DSAT deliberately asks
  for `3x − 2`, not `x`, because the x-value is a free distractor.
- **Method**: `isolate_and_verify` + `answer_the_question`
- **Process**:
  1. Isolate x with inverse operations, tracking signs each line.
  2. Substitute back into the original equation (10-second check).
  3. Re-read the stem; compute the actually-asked expression.
  4. SPR: enter exactly; MC: expect x itself among the distractors.

**Archetype A2 — No solution / infinitely many solutions (parameter hunt)**
- **Topic**: algebra / linear equations in one variable
- **Trap**: `no_vs_infinite_solutions`
- **Intuition**: A linear equation collapses only two ways: `0 = 0` (every x
  works — coefficients AND constants match) or `0 = k≠0` (nothing works —
  coefficients match, constants don't). Matching x-coefficients is the
  gateway to both; the constants decide which.
- **Method**: `coefficient_matching`
- **Process**:
  1. Expand both sides fully.
  2. Set x-coefficients equal → solve for the parameter.
  3. Compare constants: equal → infinite; unequal → none.
  4. Confirm against what the stem asked (which case, or the parameter value).

### `linear_equations_two_var`

**Archetype A3 — Interpret slope or intercept in context**
- **Topic**: algebra / linear equations in two variables
- **Trap**: `slope_intercept_confusion`, `intercept_context_error`
- **Intuition**: Slope is always "per one unit of x" with units attached;
  the y-intercept is the x = 0 snapshot (starting value), and the x-intercept
  is the y = 0 event (depletion/break-even). Units decide, not position in
  the equation.
- **Method**: `slope_first_read`
- **Process**:
  1. Write the model as y = mx + b; state m's units aloud ("dollars per month").
  2. Match the stem's phrase ("each additional", "initial", "when none remain")
     to m, b, or the x-intercept respectively.
  3. Eliminate options describing the co-quantity (the classic distractor pair
     swaps m and b descriptions).

**Archetype A4 — Build the equation from a described relationship**
- **Topic**: algebra / linear equations in two variables
- **Trap**: `variable_role_swap`, `unit_mismatch`
- **Intuition**: Every clause maps to exactly one term. Totals are sums of
  (rate × count) terms; fixed fees stand alone.
- **Method**: `direct_translation`
- **Process**:
  1. Define both variables with units in writing.
  2. Translate clause-by-clause; never merge two clauses in your head.
  3. Sanity-check with one concrete value pair.

### `linear_functions`

**Archetype A5 — Evaluate / invert function notation**
- **Topic**: algebra / linear functions
- **Trap**: `function_notation_shift`, `misread_quantity`
- **Intuition**: `f(3) = 7` is the point (3, 7). "Find x when f(x) = 7"
  reads the table/graph in the reverse direction — output given, input asked.
- **Method**: `isolate_and_verify` (+ `desmos_intersect` for graph-given items)
- **Process**:
  1. Decide direction: input→output or output→input.
  2. Substitute or solve accordingly.
  3. For tables: locate the value in the CORRECT column before reading across.

**Archetype A6 — Linear model from a table or two points**
- **Topic**: algebra / linear functions
- **Trap**: `slope_direction_inverted`, `answers_intermediate_quantity`
- **Intuition**: Two clean points fully determine the line; every extra table
  row is either confirmation or bait. Slope = Δy/Δx in that order.
- **Method**: `anchor_point_fit`
- **Process**:
  1. Pick the two cleanest points; compute m = (y₂−y₁)/(x₂−x₁).
  2. Anchor b through one point (or use point-slope directly).
  3. Verify against a third table row.
  4. Answer the asked quantity (often a prediction, not the equation).

### `systems_two_linear`

**Archetype A7 — Solve a system (value or expression of the solution)**
- **Topic**: algebra / systems of two linear equations
- **Trap**: `answers_intermediate_quantity` (asks x + y, not x), `sign_error`
- **Intuition**: DSAT systems are built for elimination — and when the ask is
  `x + y` or `x − y`, adding or subtracting the raw equations often yields it
  in ONE step without ever finding x or y.
- **Method**: `coefficient_matching` (elimination) with `desmos_intersect` fallback
- **Process**:
  1. Check whether adding/subtracting the equations as-is produces the asked
     combination directly.
  2. Otherwise scale one equation, eliminate, back-substitute.
  3. Desmos fallback: graph both, read the intersection, compute the ask.

**Archetype A8 — Number of solutions of a system / parameter for parallel**
- **Topic**: algebra / systems of two linear equations
- **Trap**: `no_vs_infinite_solutions`, `parallel_perpendicular_swap`
- **Intuition**: Same slope + different intercepts = parallel = no solution;
  proportional entire equations = same line = infinite. Slopes decide first.
- **Method**: `coefficient_matching`
- **Process**:
  1. Rewrite both to slope-intercept (or compare a₁/a₂ = b₁/b₂ ≟ c₁/c₂).
  2. Match slopes for the parameter; then compare intercepts to pick the case.

### `linear_inequalities`

**Archetype A9 — Solve / interpret one-variable inequality**
- **Topic**: algebra / linear inequalities
- **Trap**: `inequality_flip_missed`, `boundary_inclusion_error`
- **Intuition**: An inequality is an equation plus a direction; the direction
  flips exactly when you multiply/divide by a negative. "At least" ⇒ ≥,
  "more than" ⇒ >.
- **Method**: `isolate_and_verify` + boundary check
- **Process**:
  1. Isolate as with an equation, flipping on negative mult/div.
  2. Test one value from your solution set in the original.
  3. Match strict/inclusive language to the boundary symbol.

**Archetype A10 — System of inequalities / feasible region**
- **Topic**: algebra / linear inequalities in two variables
- **Trap**: `boundary_inclusion_error`, `misread_quantity`
- **Intuition**: Each inequality kills a half-plane; the answer lives in the
  intersection. A single test point classifies each half-plane instantly.
- **Method**: `test_point_shading` (+ `desmos_intersect` — Desmos shades systems natively)
- **Process**:
  1. Type both inequalities into Desmos; the doubly-shaded region is the set.
  2. Manually: boundary lines first (dashed vs solid), then test (0,0).
  3. For "which point is a solution": plug candidates into BOTH inequalities.

---

## 4.2 Domain: `advanced_math`

### `equivalent_expressions`

**Archetype B1 — Rewrite / factor / expand to an equivalent form**
- **Topic**: advanced_math / equivalent expressions
- **Trap**: `distributed_exponent`, `exponent_rule_blend`
- **Intuition**: Equivalence is checkable: two expressions equal for ALL x
  must agree at any convenient x. One evaluation kills three distractors.
- **Method**: `smart_numbers` (verification) over `structure_spotting` (derivation)
- **Process**:
  1. Derive algebraically if the structure is obvious (difference of squares,
     common factor, binomial square WITH middle term).
  2. Verify: evaluate original and candidate at x = 2 (avoid 0/1 — they hide
     errors).
  3. Desmos: graph both; identical graphs ⇒ equivalent.

**Archetype B2 — Exponent and radical manipulation**
- **Topic**: advanced_math / equivalent expressions
- **Trap**: `exponent_rule_blend`, `negative_exponent_error`
- **Intuition**: Every radical is a fractional exponent; once everything is a
  power of one base, only exponent arithmetic remains.
- **Method**: `exponent_ledger`
- **Process**:
  1. Convert radicals → fractional exponents; negative exponents → reciprocals.
  2. Express all terms over a common base.
  3. Add/subtract/multiply exponents per the operation; one ledger line.
  4. Verify numerically with base 2.

### `nonlinear_equations_and_systems`

**Archetype B3 — Solve a quadratic (roots, sum/product of roots)**
- **Topic**: advanced_math / nonlinear equations in one variable
- **Trap**: `zero_sign_flip`, `answers_intermediate_quantity`
- **Intuition**: `(x − r)` vanishes at `+r`. Sum of roots = −b/a and product
  = c/a fall out of factored form without solving — DSAT loves asking for the
  sum precisely so you don't need the roots.
- **Method**: `zero_product_split`; `desmos_zero_scan` fallback; Vieta shortcut
  for sum/product asks
- **Process**:
  1. Set = 0. Factor if the structure is visible; otherwise quadratic formula.
  2. Sign-check each root against its factor.
  3. If the ask is sum/product of solutions: use −b/a, c/a directly.
  4. Desmos: zeros off the graph settle any doubt.

**Archetype B4 — Number of real solutions (discriminant)**
- **Topic**: advanced_math / nonlinear equations
- **Trap**: `discriminant_misuse`
- **Intuition**: b² − 4ac is a census, not a solve: positive → 2, zero → 1
  (tangency), negative → 0. "Exactly one solution" of a line-parabola system
  means tangency means discriminant = 0.
- **Method**: `discriminant_census`
- **Process**:
  1. Reduce the system to one quadratic = 0 (substitute the linear into the
     nonlinear).
  2. Compute b² − 4ac in terms of the parameter.
  3. Set >0 / =0 / <0 per the stem's solution count; solve for the parameter.

**Archetype B5 — Radical and rational equations (extraneous roots)**
- **Topic**: advanced_math / nonlinear equations
- **Trap**: `extraneous_solution_kept`, `valid_solution_discarded`, `domain_restriction_ignored`
- **Intuition**: Squaring and denominator-clearing are one-way doors — they
  can create solutions that were never there. The original equation is the
  only judge.
- **Method**: `plug_in_check_domain`
- **Process**:
  1. Isolate the radical / identify forbidden denominator values FIRST.
  2. Square or clear denominators; solve the resulting polynomial.
  3. Test every candidate in the ORIGINAL equation; reject failures only.
  4. MC pattern: one option keeps both roots, one drops both, one keeps the
     extraneous — only the checked set survives.

### `nonlinear_functions`

**Archetype B6 — Quadratic/vertex: max-min, projectile, revenue**
- **Topic**: advanced_math / nonlinear functions (quadratic)
- **Trap**: `vertex_readoff_error`, `zero_sign_flip`, `misread_quantity`
- **Intuition**: The vertex is the whole story: x-vertex = when, y-vertex =
  how much. It sits at −b/2a, or midway between the zeros — symmetry is free
  information.
- **Method**: `complete_the_square` (or −b/2a shortcut); `desmos_zero_scan`
- **Process**:
  1. Identify which vertex coordinate the stem wants (time vs height ambush).
  2. x_v = −b/2a; y_v = f(x_v). Or read (h, k) from vertex form minding signs.
  3. Desmos: plot and click the extremum.

**Archetype B7 — Exponential growth/decay models**
- **Topic**: advanced_math / nonlinear functions (exponential)
- **Trap**: `growth_decay_swap`, `percent_as_linear` (see `moe`-style naming note §9), `decimal_place_slip`
- **Intuition**: Repeated percent change is multiplication, never addition:
  `a(1 ± r)^t`. `a` is the t = 0 value; the base tells growth (>1) or decay
  (<1); t's unit must match the compounding interval stated.
- **Method**: `growth_template_match`
- **Process**:
  1. Extract initial value a, direction, rate r (as a decimal), time unit.
  2. Assemble `y = a(1 ± r)^t`; rescale the exponent if units differ
     (e.g. t/12 for monthly rate, yearly t).
  3. Distractor scan: the linear `a ± art` form and the swapped-base form.

**Archetype B8 — Function transformations and graph reading**
- **Topic**: advanced_math / nonlinear functions
- **Trap**: `function_notation_shift`, `asymptote_as_intercept`
- **Intuition**: Inside the parentheses acts on x and moves opposite to its
  sign; outside acts on y and moves as written. `f(x − 3) + 2` = right 3, up 2.
- **Method**: `structure_spotting` + `desmos_zero_scan`
- **Process**:
  1. Decompose the change into inside (horizontal, inverted) vs outside
     (vertical, literal).
  2. Track one anchor point (vertex, intercept) through the transformation.
  3. Desmos: plot both original and transformed to confirm.

**Archetype B9 — Polynomial zeros, factors, and end behavior**
- **Topic**: advanced_math / nonlinear functions (polynomial)
- **Trap**: `zero_sign_flip`, `domain_restriction_ignored`
- **Intuition**: Factor ↔ zero ↔ x-intercept are one fact in three costumes;
  a remainder of 0 on division by (x − a) is the same fact in a fourth
  (f(a) = 0). Even-multiplicity zeros touch, odd cross.
- **Method**: `zero_product_split` + `desmos_zero_scan`
- **Process**:
  1. Translate the given form into zeros (mind signs).
  2. For "which is a factor": test f(a) = 0 by direct evaluation.
  3. Desmos for multiplicity/end-behavior asks.

---

## 4.3 Domain: `problem_solving_data_analysis`

### `ratios_rates_units`

**Archetype C1 — Unit conversion / rate chains**
- **Topic**: PSDA / ratios, rates, units
- **Trap**: `rate_inverted`, `unit_mismatch`
- **Intuition**: Units are algebra: they cancel diagonally like factors. If
  the units of the final fraction are wrong, the arithmetic is irrelevant.
- **Method**: `unit_chain`
- **Process**:
  1. Write the given as a fraction with units.
  2. Chain conversion fractions oriented so unwanted units cancel.
  3. Confirm the surviving unit matches the ask BEFORE computing digits.

**Archetype C2 — Ratio / proportion with part-whole structure**
- **Topic**: PSDA / ratios and proportions
- **Trap**: `ratio_part_whole_confusion`, `proportion_inverted`
- **Intuition**: A ratio a:b hides a whole of a + b parts. Scale the parts
  with one multiplier k; ak and bk stay honest.
- **Method**: `direct_translation` (k-multiplier form)
- **Process**:
  1. Write parts as 3k and 5k (etc.); total = 8k.
  2. Anchor k from whichever actual count is given.
  3. Compute the asked part; check part vs whole one last time.

### `percentages`

**Archetype C3 — Percent of / percent change / reverse percent**
- **Topic**: PSDA / percentages
- **Trap**: `percent_wrong_base`, `successive_percent_added`, `decimal_place_slip`
- **Intuition**: Every percent is multiplication by a decimal, and every
  percent has a base — "20% off then 15% off" is ×0.80 ×0.85, never −35%.
  Reverse questions ("after a 20% increase, the price is $x") divide by the
  multiplier, never multiply by the complement.
- **Method**: `base_lock` (+ `smart_numbers` with 100)
- **Process**:
  1. Write the base explicitly: "% of ___".
  2. Convert to a single multiplier; chain multipliers for successive changes.
  3. Reverse direction ⇒ divide by the multiplier.
  4. When abstract, run the whole stem with a starting value of 100.

### `one_variable_data`

**Archetype C4 — Center: mean vs median under skew/outliers**
- **Topic**: PSDA / one-variable data
- **Trap**: `mean_median_conflation`, `average_of_averages`
- **Intuition**: The mean chases outliers; the median ignores them. Right
  skew drags mean above median. Removing the largest value can only lower
  the mean but may not move the median at all.
- **Method**: `outlier_stress_test`; `weighted_balance` for combined means
- **Process**:
  1. Sketch/locate the outlier or skew direction.
  2. Ask which measure moves and which direction under the stated change.
  3. Combined groups: total sum = Σ(mean × n); never average the two means
     unless groups are equal-sized.

**Archetype C5 — Spread: standard deviation comparisons**
- **Topic**: PSDA / one-variable data
- **Trap**: `spread_center_confusion`
- **Intuition**: SD is distance-from-the-mean, never the size of the values:
  a dataset clustered tightly at 1000 has a smaller SD than one spread 0–10.
  DSAT never computes SD — it compares clustering visually/verbally.
- **Method**: `outlier_stress_test` (spread variant)
- **Process**:
  1. Ignore the means' sizes; look only at how bunched each set is around its
     own center.
  2. Tighter cluster → smaller SD. Same-shape shifted data → same SD.

### `two_variable_data`

**Archetype C6 — Scatterplot: line of best fit, prediction, residual**
- **Topic**: PSDA / two-variable data
- **Trap**: `line_of_fit_point_confusion`, `extrapolation_beyond_data`, `slope_intercept_confusion`
- **Intuition**: The line answers "predicted"; the dot answers "actual";
  the vertical gap (actual − predicted) is the residual. Slope of the fit
  line carries the same per-unit meaning as any linear model.
- **Method**: `slope_first_read` (fit-line variant)
- **Process**:
  1. Classify the ask: actual (dot), predicted (line), or difference (gap).
  2. Read the correct object at the given x.
  3. Treat predictions far outside the data cloud as suspect (that's often
     the point of the question).

### `probability_conditional`

**Archetype C7 — Probability from a two-way table (incl. conditional)**
- **Topic**: PSDA / probability and conditional probability
- **Trap**: `conditional_universe_error`, `wrong_table_cell`
- **Intuition**: "Given" shrinks the universe: P(A | B) lives entirely inside
  row/column B — the grand total is dead to you.
- **Method**: `row_restriction`
- **Process**:
  1. Find the "given" clause; cover everything outside that row/column.
  2. Numerator = the qualifying cell inside; denominator = the row/column total.
  3. No "given" ⇒ denominator is the grand total.
  4. Double-check the cell against BOTH headers (the wrong-neighbor cell is
     always a distractor).

### `sample_inference_moe`

**Archetype C8 — Margin of error interpretation**
- **Topic**: PSDA / inference from sample statistics
- **Trap**: `moe_misinterpretation`, `sample_size_moe_inverted`
- **Intuition**: Estimate ± MOE brackets the plausible values of the
  POPULATION parameter — not any individual, not the sample. Bigger random
  sample → tighter bracket.
- **Method**: `moe_bracket`
- **Process**:
  1. Build the interval [est − MOE, est + MOE].
  2. Accept only claims that (a) address the population parameter and
     (b) speak in plausibility, not certainty.
  3. Kill options about individuals, about the sample itself, or asserting
     certainty.

### `evaluating_statistical_claims`

**Archetype C9 — What can this study conclude?**
- **Topic**: PSDA / observational studies and experiments
- **Trap**: `causation_from_observation`, `overgeneralized_sample`
- **Intuition**: Two independent switches, two independent licenses: random
  SAMPLING licenses generalizing to the sampled population; random ASSIGNMENT
  licenses cause-and-effect. Each can be present or absent alone.
- **Method**: `randomization_gate`
- **Process**:
  1. Check switch 1: were subjects randomly SELECTED from a population?
     → generalization allowed to that population only.
  2. Check switch 2: were treatments randomly ASSIGNED? → causal language
     allowed.
  3. Pick the option matching the exact switch pattern; the best answer is
     usually the most cautious one that the switches permit.

---

## 4.4 Domain: `geometry_trigonometry`

### `area_volume`

**Archetype D1 — Area/volume computation and scaling**
- **Topic**: geometry / area and volume
- **Trap**: `radius_diameter_swap`, `volume_formula_blend`, `area_ratio_not_squared`
- **Intuition**: Formulas are on the reference sheet — the test is whether
  you feed them the right ingredients (radius, not diameter) and the right
  power of the scale factor (k² area, k³ volume).
- **Method**: `formula_sheet_recall` + `scale_factor_power`
- **Process**:
  1. Pull the formula from the reference sheet; list needed inputs.
  2. Convert given values to the formula's inputs (halve diameters!).
  3. For "doubled/tripled dimensions" asks: apply k, k², or k³ per the
     dimensionality of the asked quantity.
  4. Carry units through (cm → cm² → cm³).

### `lines_angles_triangles`

**Archetype D2 — Angle chases (parallel lines, triangle sums, polygons)**
- **Topic**: geometry / lines, angles, triangles
- **Trap**: `angle_relationship_misuse`, `exterior_angle_misuse`
- **Intuition**: Every diagram is a network of forced values: vertical pairs
  equal, linear pairs sum to 180°, parallel lines clone angles across the
  transversal, triangle sums to 180°, exterior angle = sum of the two REMOTE
  interiors. Push knowns until the target is forced.
- **Method**: `angle_chase`
- **Process**:
  1. Mark every given angle on (a redrawing of) the figure.
  2. Apply one relation at a time, writing each derived angle in.
  3. Stop the moment the target is determined; verify its triangle sums.

**Archetype D3 — Similar/congruent triangles**
- **Topic**: geometry / lines, angles, triangles
- **Trap**: `similar_correspondence_error`, `area_ratio_not_squared`
- **Intuition**: Similarity is an angle fact first; side ratios are only
  trustworthy AFTER vertices are matched by equal angles. Nested/overlapping
  triangles (a triangle inside a triangle sharing an angle) are the DSAT
  favorite.
- **Method**: `correspondence_lock`
- **Process**:
  1. Establish similarity (AA — two matching angles suffice).
  2. Write the vertex correspondence explicitly (△ABC ~ △XYZ order matters).
  3. Build ratios only between locked corresponding sides.
  4. Area ratio asks: square the side ratio.

### `right_triangles_trig`

**Archetype D4 — SOHCAHTOA evaluation and side-finding**
- **Topic**: geometry / right triangles and trigonometry
- **Trap**: `trig_side_misidentified`, `pythagorean_leg_hypotenuse`, `special_triangle_misratio`
- **Intuition**: Opposite and adjacent are relative to the chosen angle —
  physically re-orienting the triangle prevents the swap. The two acute
  angles' trig values interlock: sin of one = cos of the other.
- **Method**: `triangle_reorientation` + `pythagorean_anchor`
- **Process**:
  1. Redraw with the reference angle at bottom-left; label O, A, H.
  2. Pick the ratio that links the known pair to the target.
  3. Missing third side: Pythagorean theorem or a recognized triple.
  4. 30-60-90 (1 : √3 : 2) and 45-45-90 (1 : 1 : √2) from the reference sheet.

**Archetype D5 — Cofunction and similar-triangle trig identities**
- **Topic**: geometry / right triangles and trigonometry
- **Trap**: `cofunction_blindness`, `similar_correspondence_error`
- **Intuition**: In one right triangle, sin(A) = cos(B) because A + B = 90°.
  Similar triangles share ALL trig values — so a trig value transfers between
  similar triangles without any side lengths.
- **Method**: `cofunction_swap`
- **Process**:
  1. If sin(x°) = cos(y°) is given/asked: write x + y = 90 and solve.
  2. If two similar triangles: equate the corresponding trig ratios directly.

### `circles`

**Archetype D6 — Circle equations in the plane**
- **Topic**: geometry / circles
- **Trap**: `circle_equation_sign_flip`, `radius_diameter_swap`
- **Intuition**: `(x − h)² + (y − k)² = r²` — the center coordinates are the
  sign-flipped constants, and the right side is r SQUARED. General form is
  standard form in disguise; completing the square undresses it.
- **Method**: `radius_extraction` (via `complete_the_square`)
- **Process**:
  1. Group x-terms and y-terms; complete the square in each.
  2. Read center (h, k) minding the sign flip; take √ of the right side for r.
  3. Endpoint-of-diameter items: center = midpoint, r = half the distance.

**Archetype D7 — Arcs, sectors, and central angles**
- **Topic**: geometry / circles
- **Trap**: `arc_angle_proportion_error`, `radius_diameter_swap`
- **Intuition**: Everything in a circle scales by the same fraction:
  (central angle)/360 = arc/circumference = sector/area. One proportion
  answers every variant; radians just replace 360° with 2π.
- **Method**: `central_angle_proportion`
- **Process**:
  1. Write the three-way proportion; fill the two known slots.
  2. Solve for the third; keep degree/radian mode consistent.
  3. Confirm whether the ask is the minor or major arc.

---

# 5. Format-Specific Rules

## 5.1 SPR (student-produced response)

- No answer choices ⇒ `backsolving` unavailable; `answers_intermediate_quantity`
  is deadlier (no distractor list to warn you). `answer_the_question` is
  mandatory on every SPR.
- Enter fraction or decimal; decimals must fill the field to max precision
  (`rounded_too_early` guard). Negative answers cost one character.
- Multiple valid answers ⇒ enter any one.

## 5.2 MC distractor architecture (generation guidance)

Mirror of the verbal three-distractor framework:
1. **Trap distractor** — embodies the archetype's primary `math_trap_key`
   (e.g. the x-value when 2x is asked; the sign-flipped vertex).
2. **Procedural-slip distractor** — one common computational error deep
   (`sign_error`, `exponent_rule_blend`).
3. **Wrong-target distractor** — right math, wrong object (`misread_quantity`:
   the other coordinate, the other variable, the complement probability).
No two distractors may fail for the same reason (inherited rule).

---

# 6. Difficulty Calibration

| Band | Signature |
|---|---|
| `low` | One concept, one step, clean numbers, formula-sheet direct |
| `medium` | Two chained steps OR one trap (`answers_intermediate_quantity`, one sign flip); mild context translation |
| `high` | Multi-step chains across skills (e.g. system → discriminant → parameter), parameterized answers, dense context, trap stacked on trap; Desmos often the pressure-release valve |

Hard items concentrate in: parameter quadratics (B4), extraneous roots (B5),
weighted averages (C4), study-design inference (C9), nested similar triangles
(D3), circle completing-the-square (D6).

---

# 7. Desmos Policy (generation + solving)

Desmos is available on every item; realistic items must remain fair under it.

- Items intended to test algebraic structure (B1, B2) should ask for forms or
  parameters, not numeric answers Desmos can read off.
- Items where Desmos is the expected efficient path (A10, B3, B6) should not
  punish it — answer choices must be graph-distinguishable.
- Annotation records `desmos_advantage: high | medium | low` per item.

---

# 8. Annotation Field Summary

Per item: `math_domain_key`, `math_skill_key`, archetype id (e.g. `B4`),
`math_trap_key` (primary + per-distractor), `math_method_key` (primary
intended method + accepted alternates), `math_format_key`, difficulty band,
`desmos_advantage`, plus the shared envelope fields (options analysis,
reasoning, review) inherited from the verbal specification where applicable.

---

# 9. Amendment Process

Identical contract to grammar C.5 / reading §20: a question that fits no
archetype or exhibits an unlisted trap generates an `amendment_proposal`
(proposed key, parent skill, evidence text quoting the item, frequency
estimate) — never an invented production key. Naming note: prefer trap names
that describe the ERROR MECHANISM (`percent_wrong_base`), not the topic;
`percent_as_linear` referenced in B7 is intentionally listed here as the
first pending candidate rather than a production key.

Pending (v1): `percent_as_linear` (parent: `growth_decay_swap` or standalone
under advanced_math traps).

---

*Document version: v1.0 — 2026-08-03*
*Companion files: `rules_agent_dsat_grammar_ingestion_generation_v8.md` (SEC/EoI), `rules_agent_dsat_reading_v3.md` (I&I / C&S)*
*Domain coverage: Algebra, Advanced Math, Problem-Solving & Data Analysis, Geometry & Trigonometry — all 19 official skill areas, 26 archetypes*
*Status: all keys PROPOSED — not yet in vocabulary/master.json; promote via amendment pipeline before production annotation*
