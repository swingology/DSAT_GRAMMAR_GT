# Answer Key and Explanations — 20 Inference Questions (Science and Business)

Companion to `inference_20q_science_business_traps.md`. Answers first, then per-item explanations.

## Answer Key

| # | Answer | # | Answer |
|---|---|---|---|
| 1 | B | 11 | A |
| 2 | B | 12 | B |
| 3 | A | 13 | A |
| 4 | B | 14 | A |
| 5 | B | 15 | B |
| 6 | A | 16 | A |
| 7 | B | 17 | A |
| 8 | A | 18 | A |
| 9 | B | 19 | A |
| 10 | B | 20 | A |

---

## Explanations, trap analysis, and seed lineage


Fields per item: **Seed** = official item(s) the passage logic was modelled on (QID from the extraction). **Architecture** = passage_architecture_key. **Focus** = reading_focus_key. **Why required** = the evidentiary-standard sentence required by `inferences.md` §13.4.

---

**1 — B.** Science · marine biology · `mechanism_manipulation_test` · `causal_inference`
Seed: 2025 PT8 M2 Q18 `71ad88e2…` (echinoderm body-plan genes, high); 2024 PT8 02B Q14 `c3920256…`.
Why required: the ROS-neutralizing manipulation did not change bleaching; the host-signal-blocking manipulation did, *with ROS still elevated*. Only B follows from both manipulation results together.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `outside_knowledge` | Invents a methodological failure (antioxidant penetration) the passage never raises; also fails to account for the second experiment. |
| C | `contradiction` | ROS levels "rose as much as they had in untreated fragments," so the algae did release ROS under the same heat exposure. |
| D | `extreme_language` / `overreach` | The experiments show ROS is not the *trigger for bleaching*; they say nothing about every other physiological change. "No part in any" exceeds the evidence by one step. |

---

**2 — B.** Science · neuroscience · `study_design_isolation_limit` · `implication_inference`
Seed: 2025 PT10 M2 Q17 `063675a5…` (capuchin task demands); 2025 PT5 M1 Q17 `24496760…` (Younger Dryas crater age). Live calibration: Test Advantage Nov 2025 duckweed item (untested variables → limit inference).
Why required: the sentence "because the awake birds were also the only ones exposed to the recorded calls" is a confound statement; the only conclusion a confound licenses is that attribution to either factor is blocked.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `overreach` / `direction_reversal` of the confound | Assigns the effect to one confounded factor and ranks it against the other; no comparison between the two factors was run. |
| C | `contradiction` | A confound makes the cause ambiguous; it does not make the (large, consistent) effect chance. |
| D | `outside_knowledge` | Reordering tutoring and testing is unrelated to the stated confound (recordings vs sleep). |

---

**3 — A.** Science · behavioral ecology · `studied_subgroup_generalization_limit` · `implication_inference`
Seed: 2024 PT5 M1 Q14 `4062dd8f…` (behavioral ecology); 2025 PT1 M2 Q18 `4482bb9a…` (tanager honest-signal).
Why required: if trap entry is bold and urban birds have less need to enter, the urban sample is selected for boldness. The sample can therefore not stand for the urban population; the population claim is unsupported, not disproved.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `inverted_logic` / `confirmed_when_contradicted` | Treats the sampling problem as though it strengthened the conclusion; the passage's "however" signals a limitation. |
| C | `direction_reversal` | Reverses the meaning of entering a cage despite alternatives (that is *more* bold, not more cautious), and reverses the finding. |
| D | `overreach` | Predicts the outcome of an experiment never run; the passage only identifies a sampling bias. |

---

**4 — B.** Science · quantitative · `data_weakens_claim` (all-measures check) · `choose_best_completion_from_data`
Seed: 2025 PT4 M1 Q17 `5add7d4f…` (mycorrhizal, "surprised to discover"); 2025 PT8 M2 Q15 `b75c52c1…` (bite-force methods).
Why required: the proposal says higher frequency → smaller prey *consistently*. B is the one row pair that violates monotonicity (58 kHz → 11.8 mm vs 42 kHz → 9.6 mm).

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `polarity_mismatch` | Accurate data, but it *supports* Reyes: the extremes obey the rule. Stem asks for data that support the student's objection. |
| C | `wrong_table_row_or_column` / `also_true_trap` | Capture height is not part of Reyes's proposal; noting that prey length "does not" decline steadily is the right idea but is not stated as a frequency–prey-length violation. |
| D | `wrong_table_row_or_column` | Compares frequency with capture height, a variable outside the claim. |

---

**5 — B.** Science · geobiology · `alternative_explanation_ruled_out` · `causal_inference`
Seed: 2025 PT6 M2 Q12 `8dd130d0…` (NH₃ biosignature—abiotic vs biotic sources); 2025 PT5 M1 Q17 `24496760…`.
Why required: the isotope test rules out the sediment source; the 2,800-year isolation rules out any surface origin. What survives is present-day microbial production inside the brine.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `confirmed_when_contradicted` | Names the explanation the isotope signature ruled out. |
| C | `overreach` / `scope_extension` | Methane production shows *some* microbial activity; "diverse," "comparable to temperate lakes" is unsupported. |
| D | `contradiction` | The team used exactly that distinction to reach its finding. |

---

**6 — A.** Science · pollination ecology · `indirect_effect_mediation` · `causal_inference`
Seed: 2024 PT7 02A Q13 `0d6ea69f…` (botany/ecology); 2025 PT8 M2 Q17 `aa185297…` (botany).
Why required: A (smoke) → C (fewer visits); B (loss of UV cues) proposed as mediator; restoring UV under smoke restored visits. The mediator, not direct harm, carries the effect.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `extreme_language` / `overreach` | "Physically unaffected," "forage normally" — the experiment shows visits recovered when cues were restored; it does not show zero physical effect. |
| C | `cause_effect_misalignment` | Moves the cause from smoke blocking light to flowers reflecting less; the smoke-free-day comparison in the passage contradicts "even on smoke-free days." |
| D | `absolute_language` | "Only," "entirely" — unlit patches were "depressed," not zero, so bees still found some flowers. |

---

**7 — B.** Science · marine science · rule application with conjunctive condition · `predictive_inference`
Seed: 2025 PT6 M1 Q18 `…` (ethical consumers: "if the theory is correct, this finding suggests"); 2024 PT7 02B Q10 `…` (Mahatta et al. conditional).
Why required: the model's slowdown requires *both* pH < 7.8 *and* T > 18 °C. The site meets only the pH condition. The rule therefore predicts no measurable slowdown.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `constraint_ignored` | Applies only the pH half of a two-part condition. |
| C | `direction_reversal` / `overreach` | The model says cost is *offset* (net neutral), not overcompensated; predicting faster growth reverses direction. |
| D | `scope_extension` / `outside_knowledge` | Adults are outside the model's scope entirely. |

---

**8 — A.** Science · glaciology · quantitative lag · `data_supports_claim`
Seed: 2024 PT1 M1 Q11 `03b74bdf…` (UK policy uncertainty divergence by year); 2025 PT1 M2 Q15 `…` (France/US sector timing).
Why required: Halvorsen's claim is a *timing* claim. Only A pairs the warm year (2019) with Storr's same-year response and Ravn's next-year response.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `single_measure_focus` / `partial_match` | Shows Storr's same-year response but says nothing about when Ravn responds; also mis-implies Ravn is simply less sensitive. |
| C | `also_true_trap` | True, but Ravn's *identical* balance in a warm and a cold year is exactly what the lag predicts *not* to be diagnostic; it doesn't show the lagged response. |
| D | `wrong_time_window` | Notes the 2020 exception but reads it against 2020's own anomaly instead of against 2019's, so it never expresses the lag. Most competitive distractor. |

---

**9 — B.** Science · astrochemistry · limit of inference / contamination · `implication_inference`
Seed: 2025 PT6 M2 Q12 `8dd130d0…` ("would most likely agree"); 2025 PT5 M1 Q17 `24496760…`.
Why required: same excess in landing-site soil + decades unsealed = an unexcluded terrestrial source. The scientists can neither claim nor deny a space origin.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `contradiction` / `overreach` | The excess is "well above the sensitivity" — size isn't the issue, and contamination is possible, not proven. |
| C | `keyword_matching` | Matching values suggest contamination, not identical chemistry in two environments. |
| D | `outside_knowledge` | Unsupported counterfactual; sealing would affect contamination risk, not the size of a genuine excess. |

---

**10 — B.** Science · plant biology · `experiment_hypothesis_control_result` (2×2 design) · `causal_inference`
Seed: 2025 PT4 M1 Q17 `5add7d4f…` (mycorrhizal host/nonhost × fungi/no-fungi table).
Why required: the strain difference appears only when microbes are present and vanishes in sterile soil; the compound's benefit is microbe-dependent.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `constraint_ignored` (control) | If sorgoleone acted directly, ordinary plants would beat mutants in sterile soil too. They didn't. |
| C | `wrong_group_comparison` (wrong condition) | Uses the natural-soil result as if it held in sterile soil, where the strains were equal. |
| D | `overreach` | Adding sorgoleone to sterile soil would still lack the microbes the effect depends on; the passage gives no basis for the prediction. |

---

**11 — A.** Science · ornithology/evolution · `alternative_explanation_ruled_out` · `causal_inference`
Seed: 2024 PT9 02B Q13 `7c9d0ecd…` (animal behavior); 2025 PT8 M1 Q18 `5dd4d2cd…` (ornithology).
Why required: genetic divergence is ruled out (no greater than within-bank); the passage then supplies the alternative mechanism (early-life learning at the hatching site). A is the only choice that uses both.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `contradiction` / `overreach` | Birds already cross freely ("have begun" is unsupported), and dialects persist despite that; nothing predicts merging. |
| C | `extreme_language` | "Never … any aspect" — the passage only shows the river is not a genetic barrier. |
| D | `confirmed_when_contradicted` | Re-asserts the ruled-out genetic explanation with an ad hoc rescue. |

---

**12 — B.** Science · herpetology · quantitative aggregate vs individual · `data_supports_claim`
Seed: 2024 PT4 02A Q10 `880e32e7…` (organic farming comparison); 2025 PT9 M1 Q13 `808525e0…`.
Why required: the conclusion is about the population trend; the band means are the population-level measure and rise monotonically.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `individual_inference_from_aggregate_bins` | Ranges overlap (9.6–21.4 vs 7.9–16.2); "every" is false. |
| C | `wrong_table_row_or_column` | Sample size is irrelevant to the mass claim. |
| D | `individual_inference_from_aggregate_bins` | The lightest high-band adult (9.6 g) is *lighter* than the low-band mean (11.3 g). Requires actually checking the numbers. |

---

**13 — A.** Business · labor economics · pre-trend / selection · `causal_inference`
Seed: 2024 PT3 02B Q17 / 2024 PT8 02B Q13 `…` (Acemoglu automation: "complicated this account"); 2025 PT11 M1 Q10 `6015715f…`.
Why required: adopters were already outgrowing non-adopters *before* adoption; post-adoption gains cannot be assigned to the policy without accounting for that pre-trend.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `overreach` (motivational) | Infers firms' intent from a correlation; nothing in the text addresses why firms adopt. |
| C | `direction_reversal` | The passage never reports post-adoption slowdowns. |
| D | `overreach` (counterfactual) | Asserts a counterfactual for non-adopters that the data cannot reach. |

---

**14 — A.** Business · consumer psychology · theory-application with a null result · `predictive_inference`
Seed: 2025 PT6 M1 Q18 (ethical consumers, "if the theory is correct"); 2024 PT1 02A Q16 `…` (digital book costs).
Why required: anchoring predicts that $12 looks more reasonable after $24. The group that saw $24 first subscribed more to the $12 plan; the premium rate was unchanged. The only supported change is in how the standard price was judged.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `wrong_group_comparison` / `contradiction` | Premium subscriptions were equal across groups, so no difference in how the premium price was judged is supported. |
| C | `overreach` | Extrapolates beyond the tested anchor; anchoring theory does not say a higher anchor always helps. |
| D | `outside_knowledge` | Premium subscribed at the same, non-zero rate; "too high to attract subscribers" is contradicted. |

---

**15 — B.** Business · e-commerce · quantitative two-variable gap across categories · `data_supports_claim`
Seed: 2024 PT4 M2 Q12 `…` (Guadalupe/Wulf/Rajan reporting lines); 2025 PT7 M1 Q16 `…` (China imports by type).
Why required: the claim is about the *gap* (mobile − desktop), *per category*, across time. Gaps: footwear 9→3, outerwear 7→3, accessories 3→1.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| A | `single_measure_focus` | Mobile falling alone cannot establish a narrowing gap (desktop could have fallen faster). |
| C | `also_true_trap` | Desktop rising is true and *contributes* to narrowing but is never linked to the mobile rates, so it doesn't describe the gap. |
| D | `wrong_group_comparison` | Compares categories to each other; irrelevant to channel gap. |

---

**16 — A.** Business · platform economics · `alternative_explanation_ruled_out` (supply increase vs redistribution) · `implication_inference`
Seed: 2025 PT6 M2 Q12 (would most likely agree); 2024 PT7 02B Q10 (Mahatta urban expansion).
Why required: in-zone count rose; metro-wide count unchanged; increase came from adjacent-zone drivers. That is redistribution, not new supply.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `contradiction` | In-zone drivers did rise. |
| C | `contradiction` | Metro-wide total was "virtually unchanged." |
| D | `overreach` | Duration was not varied; nothing supports the prediction. |

---

**17 — A.** Business · marketing · quantitative one-quarter lag · `data_supports_claim`
Seed: 2024 PT1 M1 Q11 / 2025 PT4 M2 Q13 (policy-uncertainty series by year); 2025 PT8 M1 Q13 (housing starts by month).
Why required: the claim is a lag claim. A pairs the two ad-spend peaks (Q2 2024, Q1 2025) with revenue peaks one quarter later (Q3 2024, Q2 2025).

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `partial_match` (one-sided) | Shows *no same-quarter effect* but never shows where the effect lands; consistent with "ads don't work" as much as with a lag. |
| C | `also_true_trap` | Reads as evidence that advertising is irrelevant; it only supports the director if you add the lag, which the choice does not state. |
| D | `wrong_time_window` / `same_direction_assumption` | Same-quarter pairing (the claim denies this) and a trivial $0.2M rise. |

---

**18 — A.** Business · innovation/management · `indirect_effect_mediation` · `causal_inference`
Seed: 2024 PT3 02B Q17 (Acemoglu: alternative driver); 2024 PT4 M2 Q12.
Why required: restoring the mediator (cross-team interaction) restored the outcome under remote work; the effort explanation does not predict that.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `cause_effect_misalignment` (mediator ignored) | Re-imports the effort explanation the finding undercuts; effort was never measured. |
| C | `scope_extension` / `overreach` | Sessions restored filings *to* pre-2020 levels in *remote* firms; nothing about exceeding them or about office-based firms. |
| D | `outside_knowledge` | Hybrid firms are never mentioned. |

---

**19 — A.** Business · development economics · `studied_subgroup_generalization_limit` · `implication_inference`
Seed: 2025 PT11 M1 Q10 `6015715f…` (Hincapié entrepreneurship); 2024 PT2 M1 Q14 (veterans, subgroup). Live calibration: duckweed item's "adaptations to other conditions" restriction logic.
Why required: the subgroup studied (≥1 year in business) excludes new-business founders, the very group the promotional claim targets. The finding is silent about them.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `direction_reversal` / `overreach` | Predicts a direction for an untested group. |
| C | `contradiction` | Waitlisted applicants were "similar residents" who also applied under the same ≥1-year rule. |
| D | `absolute_language` / `scope_extension` | Turns an eligibility restriction into an "only when" effectiveness condition. Most competitive distractor. |

---

**20 — A.** Business · trade policy · net-effect synthesis · `implication_inference`
Seed: 2024 PT3 02B Q17 / 2024 PT8 02B Q13 (Acemoglu: net reading of two findings); 2025 PT7 M1 Q16 (trade liberalization).
Why required: steel producers gained jobs (intended effect achieved); steel users lost far more (net employment down). A states exactly both.

| Choice | Trap key | Decisive flaw |
|---|---|---|
| B | `textual_mimicry` / `contradiction` | Losses were in *other* industries; steelmakers were protected. |
| C | `overreach` | A speculative counterfactual about employment ratios; Montoya reports the ratio, not what would happen if it differed. |
| D | `extreme_language` / `scope_extension` | "Any imported material" generalizes from one tariff; and the *producing* industry gained. |

---

## Part D — Coverage matrix

| # | Domain | Stem type | Architecture | Focus | Primary trap tested |
|---|---|---|---|---|---|
| 1 | Sci | most_logically_completes | mechanism_manipulation_test | causal | extreme_language |
| 2 | Sci | most_logically_completes | study_design_isolation_limit | implication | overreach |
| 3 | Sci | most_logically_completes | studied_subgroup_generalization_limit | implication | inverted_logic |
| 4 | Sci | completion_from_data | table, weaken | data_weakens_claim | polarity_mismatch |
| 5 | Sci | most_logically_completes | alternative_explanation_ruled_out | causal | confirmed_when_contradicted |
| 6 | Sci | most_logically_completes | indirect_effect_mediation | causal | cause_effect_misalignment |
| 7 | Sci | most_logically_completes | rule application (conjunctive) | predictive | constraint_ignored |
| 8 | Sci | completion_from_data | table, lag | data_supports_claim | wrong_time_window |
| 9 | Sci | choose_best_inference | contamination limit | implication | keyword_matching |
| 10 | Sci | most_logically_completes | experiment_hypothesis_control_result | causal | constraint_ignored (control) |
| 11 | Sci | most_logically_completes | alternative_explanation_ruled_out | causal | confirmed_when_contradicted |
| 12 | Sci | completion_from_data | table, aggregate bins | data_supports_claim | individual_inference_from_aggregate_bins |
| 13 | Biz | most_logically_completes | pre-trend / selection | causal | overreach (motivational) |
| 14 | Biz | most_logically_completes | theory application, null arm | predictive | wrong_group_comparison |
| 15 | Biz | completion_from_data | table, gap across groups | data_supports_claim | single_measure_focus |
| 16 | Biz | choose_best_inference | alternative_explanation_ruled_out | implication | contradiction |
| 17 | Biz | completion_from_data | table, lag | data_supports_claim | wrong_time_window |
| 18 | Biz | most_logically_completes | indirect_effect_mediation | causal | cause_effect_misalignment |
| 19 | Biz | most_logically_completes | studied_subgroup_generalization_limit | implication | scope_extension |
| 20 | Biz | choose_best_inference | net-effect synthesis | implication | textual_mimicry |

---

*Authored 2026-09-08. No database writes. Items are not ingested; to load them, run them through the admin Generate page or the ingestion path with `content_origin = generated`.*
