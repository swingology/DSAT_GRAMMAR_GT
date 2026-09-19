# 20 Inference Questions — Science and Business, Trap-Engineered

**Purpose.** Twenty new DSAT-style Inference items (Information and Ideas → Inferences) written at medium-high to high difficulty. Each item is seeded from one or more official items in the 111-question extraction (`inference_stem_business_index.md` / `inference_stem_business_questions.md`) and is built on a documented passage architecture and a documented distractor-trap set from the project rules (`rules_refactor/rules/reading/skills/inferences.md`, `generation_core.md` §16, `KEYS_MASTER.md` → `REASONING_TRAP_KEYS`).

**Split.** 12 science / 8 business-economics. 15 text inferences (`most_logically_completes` or `choose_best_inference`), 5 quantitative inferences with embedded tables (`choose_best_completion_from_data`).

**Realism note.** Every researcher, study, institution, dataset and number below is fictional and constructed for the item. Nothing here should be read as a factual claim about real research.

**Difficulty target.** Every item is pitched at or above the medium band of its seed. Difficulty is raised by (a) using an architecture that requires holding two or three passage elements at once, (b) making at least one distractor competitive (defensible-sounding, same vocabulary, fails by exactly one step of scope, polarity, condition or timing), and (c) in tables, requiring a two-variable or timing comparison rather than a single lookup. No empirical calibration is claimed.

---

## Part A — What the research says about DSAT inference traps

### A.1 Project taxonomy used (from `KEYS_MASTER.md` / `inferences.md`)

Passage architectures (generation_core §22) used here:

| Architecture | What the passage must contain | Required distractor |
|---|---|---|
| `experiment_hypothesis_control_result` | hypothesis, control vs experimental condition, result with direction | an option that uses the result from the wrong condition |
| `indirect_effect_mediation` | A→C stated, mediator B identified, evidence A→B→C | an option that treats the mediator as an independent cause or ignores it |
| `alternative_explanation_ruled_out` | explanation X, alternative Y, a test, a survivor | an option that attributes the result to the ruled-out explanation |
| `mechanism_manipulation_test` | phenomenon P, candidate mechanism M, manipulation targeting M, effect on P | options that appeal to the general topic without engaging the manipulation result |
| `studied_subgroup_generalization_limit` | evidence about a named subgroup + warning it may not represent the population | an option that extrapolates to the population without qualification |
| `study_design_isolation_limit` (inferences.md §13.4) | two factors co-vary or a control is absent | correct = "cannot determine which factor"; wrong = attributes to one factor |

Reasoning-trap keys assigned to distractors below (all from `REASONING_TRAP_KEYS`): `overreach`, `scope_extension`, `contradiction`, `direction_reversal`, `cause_effect_misalignment`, `outside_knowledge`, `also_true_trap`, `constraint_ignored`, `wrong_time_window`, `wrong_table_row_or_column`, `wrong_group_comparison`, `single_measure_focus`, `partial_match`, `absolute_language`, `extreme_language`, `individual_inference_from_aggregate_bins`, `same_direction_assumption`, `confirmed_when_contradicted`, `textual_mimicry`, `topical_relevance_without_logical_connection`.

### A.2 Online research — how published prep sources describe the same traps

The published trap vocabularies map cleanly onto the project keys, which is the reason this document uses the project keys as the primary label and the public name as a gloss.

| Public name (source) | Project key |
|---|---|
| Over-inference / "one-step bridge, not a leap" (PrepMaven, Times Edu, Test Advantage) | `overreach` |
| Too broad / "some → all" (Times Edu) | `scope_extension`, `absolute_language` |
| Extreme language: always, never, only, primarily (Times Edu, Varsity Tutors) | `extreme_language` |
| Out of scope / outside info (Test Advantage "Outside Info", Times Edu) | `outside_knowledge` |
| Direct contradiction (Test Advantage) | `contradiction`, `confirmed_when_contradicted` |
| Reversed logic / flips cause and effect (PrepScholar, Times Edu) | `direction_reversal`, `cause_effect_misalignment` |
| Half-right / "one clause fails, whole option fails" (Times Edu) | `partial_match` |
| Recycled language / "same words, different meaning" (Times Edu, Test Advantage "Just Repeats") | `textual_mimicry`, `keyword_matching` |
| True but irrelevant (Times Edu, Test Advantage "Wrong Focus") | `also_true_trap`, `topical_relevance_without_logical_connection` |
| Ignores rule / wrong use (Test Advantage) | `constraint_ignored` |
| Unlikely cause / outside reasons (Test Advantage) | `outside_knowledge`, `cause_effect_misalignment` |

**Calibration item from a real administration.** The Test Advantage's write-up of a November 2025 hard science item (duckweed ecotypes, four water samples × three zinc levels, light and temperature *not* replicated; ecotypes grew equally well and zinc enhanced growth) has key **A**: "if each ecotype is indeed locally adapted as the researchers hypothesized, those adaptations are to other environmental conditions than the water each ecotype inhabits." Its distractors are labelled by the source as overgeneralization (B: "differences do not represent adaptations to local conditions" — the experiment did not test light/temperature), direct contradiction (C: "significant differences in resistance to zinc"), and speculation (D: zinc levels didn't match natural exposure). This is the `study_design_isolation_limit` / `overreach` / `contradiction` / `outside_knowledge` pattern in the project rules, confirmed on a live hard item. Items 2, 3 and 19 below are built to that standard.

Test Advantage's "logical conclusion" pattern list (synthesis of findings; application of a rule/model to a case; explaining an observation by the key distinction) is also used: items 7, 14 and 20 are rule-application items; items 1, 5, 6, 10, 11, 13, 16, 18 are explain-the-observation items; items 2, 3, 9, 19 are limit-of-inference items.

Sources:
- [Hard Digital SAT Science Question: Expert Method — The Test Advantage](https://thetestadvantage.com/blog/real-hard-digital-sat-science-question-nov-2025-expert-method)
- [Digital SAT Reading: 7 Logical Conclusion Patterns — The Test Advantage](https://thetestadvantage.com/blog/7-key-patterns-you-must-know-digital-sat-reading-logical-conclusions)
- [December 2025 Digital SAT Module 2 Hard Inference Question — The Test Advantage](https://thetestadvantage.com/blog/december-2025-digital-sat-module-2-hard-inference-question-solved)
- [Digital SAT Reading Trap Answers 2026 — Times Edu](https://times.edu.vn/en/sat/digital-sat-reading-trap-answers/)
- [Inferences on the SAT: 4-Step Strategy — PrepMaven](https://prepmaven.com/blog/test-prep/inferences-on-the-sat/)
- [Inference Questions on SAT Reading: 6 Strategies — PrepScholar](https://blog.prepscholar.com/inference-questions-on-sat-reading-6-strategies)
- [Solving Inferences Questions on the SAT — Test Ninjas](https://test-ninjas.com/sat-inferences)
- [Inferences — Varsity Tutors](https://www.varsitytutors.com/practice/subjects/sat/lessons/inferences)

---

## Part B — Questions

**CHATGPT review scale.** Difficulty: 1–3 easy, 4–5 medium, 6–7 medium–hard, 8–9 hard, 10 exceptional. Quality is separate: 1–4 substantial repair, 5–6 revision needed, 7–8 useful with targeted edits, 9–10 polished. These are editorial estimates, not empirical calibration. See [question-by-question review and improvements](inference_20q_science_business_traps_chatgpt_review.md).

### Science (1–12)

---

**1.** Coral bleaching—the expulsion of the symbiotic algae that supply corals with most of their energy—typically follows exposure to unusually warm water. A long-standing hypothesis holds that heat damages the algae first, causing them to leak reactive oxygen species (ROS) into coral tissue, and that the coral expels the algae in response to this chemical injury. Testing this account, marine biologist Ines Okonkwo and colleagues exposed fragments of the coral *Acropora tenuis* to a 4 °C temperature increase while bathing half of them in an antioxidant that neutralizes ROS. Both groups bleached at nearly identical rates. When the team instead applied a compound that blocks a heat-sensitive signaling protein in the coral's own cells, bleaching fell sharply even though ROS levels in the tissue rose as much as they had in untreated fragments. These results suggest that ______

**CHATGPT- DIFFICULTY:** 6/10 — Medium–hard. **CHATGPT- QUALITY:** 6/10. Strong two-manipulation structure; the key overstates causal exclusion. Revise.

Which choice most logically completes the text?

- **A.** neutralizing ROS is an ineffective strategy for protecting corals because the antioxidant used by the team was unable to penetrate coral tissue at the concentrations tested.
- **B.** heat-induced bleaching in *A. tenuis* is triggered by the coral's own detection of elevated temperature rather than by chemical injury from the algae's ROS.
- **C.** the algae in *A. tenuis* are more tolerant of warm water than the coral that hosts them, so heat stress would have to be prolonged before the algae would release ROS.
- **D.** ROS leaked by heat-damaged algae play no part in any of the physiological changes that corals undergo during warm-water events.

---

**2.** Juvenile zebra finches learn their songs by listening to an adult tutor, and neuroscientist Priya Raman hypothesized that the memory of the tutor's song is consolidated during sleep. Raman's team exposed two groups of juveniles to identical tutoring sessions each morning. One group then spent the afternoon in a dark, quiet chamber, where the birds slept; the other group spent the afternoon in a brightly lit chamber where recordings of unrelated bird calls played continuously, and these birds remained awake. After two weeks, the birds that had slept reproduced the tutor's song far more accurately. Raman's team acknowledges, however, that because the awake birds were also the only ones exposed to the recorded calls, ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 8/10. Valid confound inference, but the final sentence nearly supplies the answer.

Which choice most logically completes the text?

- **A.** the difference in song accuracy demonstrates that hearing unrelated calls interferes with song learning more than sleep loss does.
- **B.** the study cannot establish whether the awake birds' poorer performance resulted from lack of sleep, from exposure to the recordings, or from both.
- **C.** the superior accuracy of the sleeping birds should be regarded as a product of chance rather than of any experimental condition.
- **D.** the results would have been more informative had the team tutored the birds in the afternoon and tested them the following morning.

---

**3.** Ecologist Tomasz Wierzba and colleagues compared great tits (*Parus major*) living in the center of Warsaw with those in a forest 40 kilometers away, seeking to determine whether urban living selects for bolder individuals. Birds were captured using feeder traps—cages baited with seed that close when a bird enters—and each bird's boldness was later scored by how quickly it approached a novel object in an aviary. Urban birds approached the object much sooner on average. The team notes, however, that entering an unfamiliar baited cage is itself a bold act, and that urban great tits, which have many alternative food sources, have less need to take such a risk than forest birds do. If those observations are correct, ______

**CHATGPT- DIFFICULTY:** 6/10 — Medium–hard. **CHATGPT- QUALITY:** 8/10. Good differential sampling-bias inference; weak competing options limit difficulty.

Which choice most logically completes the text?

- **A.** the urban great tits that were captured may be bolder than typical urban great tits, so the results cannot establish that urban birds are bolder as a population.
- **B.** urban living does select for boldness, since even the urban birds with the least need to enter the traps did so more readily than forest birds.
- **C.** forest great tits are bolder than urban ones, because entering a baited cage despite having other food sources indicates greater caution rather than greater boldness.
- **D.** the difference in boldness between the two groups would disappear if birds in both locations were provided with the same number of alternative food sources.

---

**4.** Echolocating bats emit calls at frequencies that shape what they can detect: higher-frequency calls resolve smaller objects but fade quickly in air. Biologist Marisol Reyes has proposed that among insect-eating bats, call frequency is the primary determinant of prey size—bats using higher-frequency calls should consistently take smaller prey. A student examining the table argues that Reyes's proposal is too simple.

**CHATGPT- DIFFICULTY:** 4/10 — Medium; provisional until repaired. **CHATGPT- QUALITY:** 4/10. B is most direct, but C also supports the objection. Repair answer uniqueness.

**Foraging Characteristics of Four Insectivorous Bat Species**

| Species | Peak call frequency (kHz) | Mean prey length (mm) | Mean prey capture height (m) |
|---|---|---|---|
| Species A | 25 | 14.2 | 12 |
| Species B | 42 | 9.6 | 8 |
| Species C | 58 | 11.8 | 3 |
| Species D | 81 | 5.1 | 2 |

Which choice best describes data from the table that support the student's argument?

- **A.** Species D has the highest peak call frequency and the smallest mean prey length, while Species A has the lowest frequency and the largest mean prey length.
- **B.** Species C calls at a higher peak frequency than Species B yet takes prey that are, on average, longer than Species B's prey.
- **C.** Mean prey capture height declines steadily from Species A to Species D, whereas mean prey length does not.
- **D.** Species B and Species C differ by only 16 kHz in peak call frequency but by 5 meters in mean prey capture height.

---

**5.** Lake Vida, sealed beneath 20 meters of ice in Antarctica, contains brine so cold and salty that few organisms could survive in it, yet the brine holds unexpectedly high concentrations of methane. Geobiologist Hannah Strøm and colleagues considered two explanations: the methane is produced by microbes living in the brine today, or it is ancient gas released from sediments beneath the lake as the water froze. The two sources leave different chemical fingerprints—microbial methane is depleted in the heavy carbon isotope ¹³C relative to methane released from sediments. The team found that methane in the brine had the isotopic signature typical of microbial production. Because the brine has been isolated from the surface for at least 2,800 years, the team concluded that ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium; provisional until repaired. **CHATGPT- QUALITY:** 3/10. The isotope evidence identifies origin, not when production occurred. Repair the keyed inference.

Which choice most logically completes the text?

- **A.** the methane was released from sediments beneath the lake as the water froze and has persisted in the brine because no organisms are present to consume it.
- **B.** microbial communities have continued to produce methane within the brine long after the lake was cut off from the surface.
- **C.** the brine harbors a diverse ecosystem whose metabolic activity is comparable to that of microbial communities in temperate lakes.
- **D.** methane from sediments and methane from microbes cannot be distinguished once both have been trapped in brine for thousands of years.

---

**6.** During wildfire season, bumble bee visits to flowering plants decline sharply in areas blanketed by smoke, and ecologists initially attributed the decline to smoke irritating the bees or impairing their flight. Ecologist Dana Whitcombe and colleagues noticed, however, that smoke filters out much of the ultraviolet (UV) light that many flowers reflect in patterns bees use to locate nectar. In field plots under heavy smoke, the team placed UV lamps above some flower patches so that the flowers' reflective patterns remained visible to bees; other patches were left unlit. Bees visited the lit patches at rates comparable to those recorded on smoke-free days, while visits to unlit patches remained depressed. These findings suggest that ______

**CHATGPT- DIFFICULTY:** 5/10 — Medium. **CHATGPT- QUALITY:** 7/10. Useful mediator-restoration inference; qualify the claim that this is chiefly responsible.

Which choice most logically completes the text?

- **A.** smoke reduces bee visitation chiefly by obscuring the visual cues bees rely on to find flowers, rather than by directly harming the bees.
- **B.** bumble bees are physically unaffected by wildfire smoke and will forage normally in smoky conditions provided that nectar is available.
- **C.** flowers reflect UV light less strongly during wildfire season, which makes them harder for bees to locate even on smoke-free days.
- **D.** bumble bees can detect flowers only by their UV patterns, so any condition that blocks UV light will eliminate bee visitation entirely.

---

**7.** Sea urchin larvae build skeletons from calcium carbonate, a process that becomes more energetically costly as seawater acidifies. Using data from laboratory cultures of the urchin *Strongylocentrotus purpuratus*, marine biologist Kenji Aoyama developed a model predicting that larval skeletal growth slows measurably only when two conditions coincide: seawater pH falls below 7.8 and water temperature exceeds 18 °C. Below that temperature, Aoyama's model indicates, larvae grow slowly enough that the added cost of calcification is offset by their reduced metabolic demand. Oceanographers project that by 2060 the pH of the waters off a particular stretch of the northern California coast, where summer temperatures rarely rise above 15 °C, will decline from 8.0 to 7.7. If Aoyama's model is accurate, it can be predicted that in these waters, ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 8/10. Sound application of a two-condition rule; the key closely restates that rule.

Which choice most logically completes the text?

- **A.** *S. purpuratus* larvae will grow more slowly by 2060 because pH will have fallen below the model's threshold.
- **B.** *S. purpuratus* larval skeletal growth will not be measurably slowed by acidification unless summer temperatures also rise above 18 °C.
- **C.** *S. purpuratus* larvae will grow faster by 2060 because their reduced metabolic demand in cold water will more than compensate for acidification.
- **D.** the decline in pH will have a greater effect on adult *S. purpuratus* than on larvae because adults maintain much larger skeletons.

---

**8.** Glaciers lose or gain mass each year depending on snowfall and summer melt, and the resulting net change is called mass balance. Glaciologist Sigrid Halvorsen has argued that Ravn Glacier, which is fed by a high, shaded accumulation basin, registers the effect of an unusually warm summer only in the following year, whereas nearby Storr Glacier, which is exposed and low-lying, responds within the same year.

**CHATGPT- DIFFICULTY:** 6/10 — Medium–hard. **CHATGPT- QUALITY:** 7/10. Good time-lag comparison; only one complete warm-year/following-year pair is available.

**Summer Temperature Anomaly and Annual Mass Balance, 2018–2022**

| Year | Summer temperature anomaly (°C) | Storr Glacier mass balance (m water equivalent) | Ravn Glacier mass balance (m water equivalent) |
|---|---|---|---|
| 2018 | +0.3 | −0.4 | −0.2 |
| 2019 | +2.1 | −1.6 | −0.3 |
| 2020 | +0.2 | −0.5 | −1.4 |
| 2021 | −0.4 | −0.1 | −0.3 |
| 2022 | +1.8 | −1.5 | −0.2 |

Which choice best describes data from the table that support Halvorsen's argument?

- **A.** In 2019, when the summer temperature anomaly was +2.1 °C, Storr Glacier's mass balance was −1.6 m, whereas Ravn Glacier's most negative mass balance, −1.4 m, occurred in 2020.
- **B.** In 2019 and 2022, the two warmest summers in the table, Storr Glacier lost substantially more mass than Ravn Glacier did.
- **C.** Ravn Glacier's mass balance was −0.3 m in both 2019 and 2021, even though the summer temperature anomalies in those years differed by 2.5 °C.
- **D.** Storr Glacier's mass balance was more negative than Ravn Glacier's in every year except 2020, when the summer temperature anomaly was only +0.2 °C.

---

**9.** Amino acids produced by nonbiological chemistry occur in nearly equal proportions of two mirror-image forms, whereas life on Earth uses almost exclusively the "left-handed" form. An excess of left-handed amino acids in a meteorite has therefore been proposed as evidence that the chemistry favoring life's handedness began in space. Analyzing a meteorite that fell in 1969, astrochemist Leila Farahani and colleagues measured a left-handed excess of 4 percent in one amino acid, well above the sensitivity of their instruments. But the team also found the same amino acid in soil from the meteorite's landing site—at a left-handed excess of 4 percent—and noted that the meteorite fragment had been stored unsealed for decades.

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 8/10. Sound contamination limitation; the alternatives are readily eliminated.

Based on the text, Farahani and colleagues would most likely agree with which statement about the left-handed excess measured in the meteorite?

- **A.** It is too small to have been produced by any process other than contamination from terrestrial soil.
- **B.** It cannot be attributed to processes in space until contamination by terrestrial amino acids has been ruled out.
- **C.** It shows that the chemistry favoring left-handed amino acids operates identically in space and on Earth.
- **D.** It would have been larger had the fragment been sealed immediately after it fell.

---

**10.** Plant roots release a mixture of compounds into the surrounding soil, and botanist Ayo Adeyemi hypothesized that one such compound, sorgoleone, helps sorghum survive drought by recruiting soil bacteria that protect roots from water loss. Adeyemi's team grew ordinary sorghum plants alongside a mutant strain that cannot produce sorgoleone, in two kinds of soil: natural field soil and the same soil sterilized to eliminate microbes. After three weeks without water, ordinary plants in natural soil retained far more leaf moisture than mutant plants in natural soil, whereas in sterilized soil the two strains retained equally little. The results suggest that ______

**CHATGPT- DIFFICULTY:** 6/10 — Medium–hard. **CHATGPT- QUALITY:** 6/10. Good interaction/control reasoning; absence of any direct effect is stronger than the evidence.

Which choice most logically completes the text?

- **A.** sorgoleone protects sorghum roots from water loss directly, and soil bacteria simply amplify an effect that the compound produces on its own.
- **B.** sorgoleone's contribution to drought tolerance depends on the presence of soil microbes rather than on any direct effect of the compound on the plant.
- **C.** the mutant strain's inability to produce sorgoleone impairs its water retention regardless of whether microbes are present in the soil.
- **D.** sorghum grown in sterilized soil would have survived the drought had the team supplemented the soil with sorgoleone.

---

**11.** Male white-crowned sparrows on opposite banks of the Kern River sing distinct dialects, and ornithologist Beatriz Salcedo initially proposed that the river acts as a barrier to movement, so that each bank's population has evolved in isolation and the dialects reflect genetic divergence. Salcedo's team then sequenced DNA from 140 birds and found that genetic differences between the two banks were no greater than those between birds sampled a few hundred meters apart on the same bank—indicating that birds cross the river and interbreed freely. Because young sparrows learn their song from adult males near their hatching site during a brief window early in life, Salcedo now argues that ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 7/10. Coherent learned-dialect explanation; “fixed” is stronger than the stated learning premise.

Which choice most logically completes the text?

- **A.** the dialects persist because a bird's song is fixed by what it hears where it hatches, not because the populations on either bank are genetically distinct.
- **B.** the dialects will merge within a few generations now that birds have begun crossing the river in greater numbers.
- **C.** the river has never influenced any aspect of the sparrows' biology, since it fails to prevent interbreeding between the two banks.
- **D.** genetic divergence between the banks is too recent to be detected, even though it is sufficient to produce distinct dialects.

---

**12.** Many lizard species grow larger at higher elevations, where cooler temperatures favor larger bodies that retain heat. Herpetologist Owen Blackwood surveyed the lizard *Sceloporus occidentalis* at four elevations on a single mountainside, recording adult body mass. Blackwood concludes that in this population, body mass increases with elevation.

**CHATGPT- DIFFICULTY:** 3/10 — Easy. **CHATGPT- QUALITY:** 7/10. Clear quantitative-evidence item, but the answer is a direct trend reading.

**Adult Body Mass of *S. occidentalis* by Elevation Band**

| Elevation band (m) | Number of adults measured | Mean body mass (g) | Range of body mass (g) |
|---|---|---|---|
| 400–700 | 62 | 11.3 | 7.9–16.2 |
| 700–1000 | 58 | 12.8 | 8.4–17.5 |
| 1000–1300 | 41 | 14.1 | 9.0–19.8 |
| 1300–1600 | 27 | 15.9 | 9.6–21.4 |

Which choice best describes data from the table that support Blackwood's conclusion?

- **A.** Every adult measured in the 1300–1600 m band was heavier than every adult measured in the 400–700 m band.
- **B.** Mean body mass rose with each successive elevation band, from 11.3 g in the lowest band to 15.9 g in the highest.
- **C.** The number of adults measured declined with elevation, from 62 in the lowest band to 27 in the highest.
- **D.** The lightest adult in the 1300–1600 m band was heavier than the mean body mass of adults in the 400–700 m band.

---

### Business / Economics (13–20)

---

**13.** Firms that have shifted to a four-day workweek frequently report that output per employee rose after the change, and advocates cite such reports as evidence that the shorter week itself boosts productivity. Labor economist Marcus Oyelaran examined financial data for 212 firms that adopted the policy between 2019 and 2023 and found that, in the three years before adopting it, these firms had already been increasing output per employee at nearly twice the rate of comparable firms that never adopted the policy. Oyelaran's finding suggests that ______

**CHATGPT- DIFFICULTY:** 5/10 — Medium. **CHATGPT- QUALITY:** 8/10. Sound pre-existing-trend limitation; competitors need subtler errors.

Which choice most logically completes the text?

- **A.** the productivity gains reported by adopting firms may reflect trends that were under way before the policy was introduced rather than effects of the policy itself.
- **B.** firms adopt a four-day workweek in order to sustain the rapid productivity growth they have already achieved.
- **C.** a four-day workweek slows the growth of output per employee in firms whose productivity was already rising rapidly.
- **D.** firms that never adopted a four-day workweek would have seen their productivity rise as quickly as adopting firms' did if they had adopted the policy.

---

**14.** Behavioral economists have theorized that the first price a consumer encounters for a product serves as an anchor: subsequent prices are judged relative to it, so the same price seems more reasonable after a higher anchor than after a lower one. A streaming service tested two versions of its sign-up page. Half of visitors first saw a premium plan priced at $24 per month before scrolling to a standard plan at $12; the other half saw the standard plan first, with the premium plan listed below it. Visitors in the first group were 35 percent more likely to subscribe to the standard plan, though the two groups subscribed to the premium plan at the same rate. All other things being equal, if the anchoring theory is correct, this finding suggests that ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 7/10. Clear theory application; revise B to test the observed subscription result directly.

Which choice most logically completes the text?

- **A.** visitors who saw the premium plan first judged the standard plan's price more favorably than did visitors who saw the standard plan first.
- **B.** visitors who saw the standard plan first judged the premium plan's price less favorably than did visitors who saw the premium plan first.
- **C.** the service could increase standard-plan subscriptions further by raising the price of the premium plan.
- **D.** the premium plan is priced too high relative to the standard plan to attract subscribers in either group.

---

**15.** Online retailers absorb substantial costs when customers return merchandise, and returns have historically been more common for purchases made through mobile apps than for purchases made on desktop websites, a gap often attributed to the smaller product images shown on phones. A retail analyst examining one apparel retailer claims that improvements to the retailer's mobile app between 2022 and 2024 narrowed this gap across product categories.

**CHATGPT- DIFFICULTY:** 5/10 — Medium. **CHATGPT- QUALITY:** 7/10. Useful channel-gap comparison; the table alone does not establish what caused the change.

**Return Rate by Product Category and Purchase Channel (% of orders returned)**

| Product category | Mobile app, 2022 | Desktop, 2022 | Mobile app, 2024 | Desktop, 2024 |
|---|---|---|---|---|
| Footwear | 31 | 22 | 26 | 23 |
| Outerwear | 24 | 17 | 21 | 18 |
| Accessories | 12 | 9 | 11 | 10 |

Which choice best describes data from the table that support the analyst's claim?

- **A.** The mobile app return rate declined in every product category between 2022 and 2024, falling most sharply for footwear.
- **B.** In every product category, the difference between the mobile app return rate and the desktop return rate was smaller in 2024 than it had been in 2022.
- **C.** In 2024, desktop return rates were higher than they had been in 2022 for footwear, outerwear, and accessories alike.
- **D.** Footwear had the highest return rate of any category through both channels in both years, while accessories had the lowest.

---

**16.** Ride-hailing platforms raise fares during periods of high demand, and the platforms describe this "surge pricing" as a tool that increases the supply of drivers when riders most need them. Economist Yara Haddad tracked driver locations in a large metropolitan area minute by minute during 340 surge events. She found that the number of active drivers within a surge zone did rise, typically within ten minutes—but that nearly all of the increase consisted of drivers who had already been logged in and working in adjacent zones, and that the total number of drivers active across the metropolitan area was virtually unchanged during surges.

**CHATGPT- DIFFICULTY:** 3/10 — Easy. **CHATGPT- QUALITY:** 7/10. Mostly a paraphrase of redistribution evidence; qualify the exclusion of new drivers.

Based on the text, Haddad would most likely agree with which statement about surge pricing in the area she studied?

- **A.** It redistributes drivers who are already working toward areas of high demand rather than drawing additional drivers onto the platform.
- **B.** It fails to increase the number of drivers available to riders in the zone where a surge is in effect.
- **C.** It reduces the total number of drivers active across the metropolitan area by prompting drivers to leave low-demand zones.
- **D.** It would draw more new drivers onto the platform if surge fares remained in effect for longer periods.

---

**17.** A regional furniture chain's marketing director claims that the chain's television advertising affects sales with a delay: because customers rarely buy furniture on impulse, the director argues, a quarter's advertising shows up mainly in the following quarter's revenue rather than in the quarter when the ads run.

**CHATGPT- DIFFICULTY:** 5/10 — Medium. **CHATGPT- QUALITY:** 8/10. Two repeated lag patterns support A; this supports timing, not proof of causation.

**Quarterly Advertising Spending and Revenue, 2024–2025**

| Quarter | Advertising spending ($ thousands) | Revenue ($ millions) |
|---|---|---|
| Q1 2024 | 210 | 8.1 |
| Q2 2024 | 640 | 8.3 |
| Q3 2024 | 190 | 10.9 |
| Q4 2024 | 220 | 8.4 |
| Q1 2025 | 710 | 8.2 |
| Q2 2025 | 200 | 11.2 |

Which choice best describes data from the table that support the director's claim?

- **A.** Revenue was highest in Q3 2024 and Q2 2025, the quarters that immediately followed the two quarters with the highest advertising spending.
- **B.** In Q2 2024 and Q1 2025, when advertising spending was at its highest, revenue was no higher than in the quarters with the lowest advertising spending.
- **C.** Advertising spending in Q3 2024 was lower than in any other quarter, yet revenue in that quarter reached $10.9 million.
- **D.** Revenue rose from Q1 2024 to Q2 2024 as advertising spending more than tripled over the same period.

---

**18.** Several studies have found that firms whose engineers shifted to fully remote work during 2020 filed fewer patent applications in subsequent years than firms whose engineers returned to offices, and some commentators have concluded that remote work reduces the effort or focus of engineers. Management scholar Elif Demirci suspected instead that the decline stemmed from the loss of unplanned conversations between engineers on different teams, which office settings make routine. Demirci compared remote firms that had introduced structured weekly sessions pairing engineers from different teams with remote firms that had not. Patent filings at the first group of firms recovered to pre-2020 levels within two years, while filings at the second group did not. Demirci's findings suggest that ______

**CHATGPT- DIFFICULTY:** 5/10 — Medium; provisional until repaired. **CHATGPT- QUALITY:** 4/10. A identifies a plausible mechanism but unjustifiably declares it primary and excludes effort.

Which choice most logically completes the text?

- **A.** remote work lowers patent output primarily by removing opportunities for engineers on different teams to exchange ideas, not by diminishing individual engineers' effort.
- **B.** engineers at remote firms that did not introduce cross-team sessions exerted less effort than engineers at firms that did.
- **C.** structured cross-team sessions would raise patent filings above pre-2020 levels if adopted by firms whose engineers work in offices.
- **D.** the decline in patent filings after 2020 occurred only at firms whose engineers were fully remote, not at firms with hybrid arrangements.

---

**19.** Microloans—small loans extended to people without access to conventional credit—are often promoted as a way to help the poor launch businesses. Development economist Ngozi Achebe evaluated a microloan program in a district of Uganda by comparing recipients with similar residents who had applied for loans but been placed on a waiting list. After eighteen months, recipients' business income exceeded that of waitlisted applicants by an average of 22 percent. Achebe cautions, however, that the program accepted only applicants who had already been operating a business for at least a year. As a result, ______

**CHATGPT- DIFFICULTY:** 4/10 — Medium. **CHATGPT- QUALITY:** 8/10. Valid subgroup generalization limit; the eligibility warning makes the bridge short.

Which choice most logically completes the text?

- **A.** the program's effect on people who use microloans to start a new business cannot be inferred from the 22 percent difference.
- **B.** the program would have produced a larger income gain had it been open to applicants who were starting new businesses.
- **C.** the 22 percent difference overstates the program's effect on established business owners, because waitlisted applicants had less business experience.
- **D.** microloans are effective at raising business income only when recipients have at least a year of business experience.

---

**20.** In 2018 the United States imposed tariffs on imported steel, a policy intended to protect domestic steelmakers from foreign competition. Economist Rafael Montoya examined employment data through 2021 and found that steel producers added roughly 1,000 jobs during that period, but that manufacturers who use steel as an input—makers of appliances, machinery, and vehicles—faced higher material costs and shed an estimated 75,000 jobs that Montoya attributes to the tariffs. Montoya notes that steel-using industries employ about eighty times as many workers as steel producers do.

**CHATGPT- DIFFICULTY:** 4/10 — Medium; provisional until repaired. **CHATGPT- QUALITY:** 5/10. Net sector losses are supported; the key overextends to economy-wide employment and tariff success.

Based on the text, Montoya would most likely agree with which statement about the 2018 steel tariffs?

- **A.** They achieved their intended effect on the steel industry while reducing employment in the economy as a whole.
- **B.** They failed to protect domestic steelmakers, whose modest job gains were outweighed by losses in the same industry.
- **C.** They would have increased total employment had steel-using industries employed fewer workers relative to steel producers.
- **D.** They demonstrate that tariffs on any imported material harm the industries that produce that material domestically.

---

## Answer key

Answers and explanations are in the companion file `inference_20q_science_business_traps_KEY.md`.
