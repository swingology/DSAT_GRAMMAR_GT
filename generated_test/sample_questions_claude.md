# Sample Question Analysis — DSAT Inference Items (PT10 Sec01 Mod02 Q17, Coll/Bianchi census item + generated variants)

Items 0–3 written on Sonnet 5; **Item 4 written on Opus 5** as an independent re-run of the same task against the same rule set; **Items 5–6 written on Sonnet 5** from a second user-supplied source question (Coll/Bianchi Mediterranean biodiversity census).

**Known gap:** an earlier Fable 5.1 pass covering this same task existed in this session but was overwritten by a full-file rewrite and is not reflected below. Not restored — say the word if you want it recovered from session history.

Rules basis: `rules_refactor/rules/reading/` — `core_taxonomy.md` (§3, §4, §10, §12, §17), `skills/inferences.md` (§7.4, §13.4, §16.9), `generation_core.md` (§14–§16, §23), `style_fingerprint.md` (§22), `annotation_core.md` (§21).

## Rules alignment notes (what changed vs. the first draft)

1. **Option-level keys.** The DB annotation for Q17 uses `distractor_type_key: scope_extension` (C) and `outside_knowledge` (D). Under §12.1 neither is a valid *option-level* key — both exist only in §10.1 as question-level `reasoning_trap_key` values. Corrected below to `scope_error` and `topical_relevance_without_logical_connection`. → Amendment candidate (§20): promote `outside_knowledge` to §12.1, since §13.4's own generation recipe names it as a distractor type.
2. **"Traps" = §10 `reasoning_trap_key` (one per question) + §12.1 `distractor_type_key` (one per option) + §12.2 `plausibility_source_key`.** These are the controlled vocabularies. `semantic_relation_key` is free-text (§4 field-status note) and is dropped from the templates.
3. **"Disruptors" is not a rules term.** The nearest controlled equivalents are `passage_structure_pattern` (§15.2), `passage_architecture_key` (§15.3), `inference_type_note` (§13.4), and the §22.2 sentence-level features (S1–S8). Disruptor lists below are kept for readability but each bullet is tagged to its rules counterpart.
4. **Grammar keys.** §1 / §18: `grammar_role_key` and `grammar_focus_key` must be `null` for every `information_and_ideas` item; validator rejects otherwise. Confirmed for all three items.
5. **Word count.** §15.1 Inferences norm is **60–120 words**. Original = 78. Both generated passages were rewritten to 106–117 words (first drafts were mis-counted).
6. **Style gate.** Both first-draft generated passages failed §22.7: FAILURE-03 (anonymous "researchers"/"epidemiologists"), FAILURE-04 (no appositive), S8 (no colon/dash/semicolon at >80 words). Rewritten to pass. Note: the *official* Q17 passage would also fail S4 and S5 (anonymous "researchers", parenthesized binomial) — the rules are stricter than College Board on attribution.
7. **Distractor recipe.** §13.4 `study_design_isolation_limit` prescribes: correct = "cannot determine which co-varying factor was responsible"; wrong = attributes to one factor (overreach) / concludes no effect (contradiction) / flawed for unrelated reasons (outside_knowledge). Generated Item 1 and Item 2 now follow this recipe exactly; the first draft mislabeled the "no effect" distractor as overreach.

---

# Item 0 — Official PT10 M2 Q17 (annotated against rules_refactor)

**question_family_key:** information_and_ideas · **skill_family_key:** inferences · **reading_focus_key:** implication_inference · **stem_type_key:** most_logically_completes · **disambiguation_rule_applied:** §17 rule 1

> In a study of the cognitive abilities of white-faced capuchin monkeys (*Cebus imitator*), researchers neglected to control for the physical difficulty of the tasks they used to evaluate the monkeys. The cognitive abilities of monkeys given problems requiring little dexterity, such as sliding a panel to retrieve food, were judged by the same criteria as were those of monkeys given physically demanding problems, such as unscrewing a bottle and inserting a straw. The results of the study, therefore, ______

**Which choice most logically completes the text?**

| | Option | `distractor_type_key` (§12.1) | `plausibility_source_key` (§12.2) | why_wrong |
|---|---|---|---|---|
| **A ✅** | could suggest that there are differences in cognitive ability among the monkeys even though such differences may not actually exist. | `correct` | — | Logically required: uncontrolled task difficulty → performance gaps attributable to task, not monkey → apparent cognitive differences may be artifacts. |
| B | are useful for identifying tasks that the monkeys lack the cognitive capacity to perform but not for identifying tasks that the monkeys can perform. | `overreach` | `topical_proximity` | Converts "difficulty not controlled" into an asymmetric claim about what the results are *good for*; passage makes no usefulness claim. |
| C | should not be taken as indicative of the cognitive abilities of any monkey species other than *C. imitator*. | `scope_error` | `topical_proximity` | Redirects doubt to *other species*; the passage undermines the results for capuchins themselves. |
| D | reveal more about the monkeys' cognitive abilities when solving artificial problems than when solving problems encountered in the wild. | `topical_relevance_without_logical_connection` | `common_sense_appeal` | Imports an artificial-vs-wild contrast no sentence in the passage addresses. |

**Question-level trap (§10.1):** `reasoning_trap_key: overreach` — matches the §13.4 mandatory field set for Inferences.
**evidence_span_text:** "researchers neglected to control for the physical difficulty of the tasks they used to evaluate the monkeys."
**Shared distractor signature:** B, C, D each treat the results as *informative about something*; only A says they may be *artifacts*.

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| Flaw stated in S1, consequence withheld to the blank | `passage_structure_pattern: research_summary` (§15.2) with `cautionary_framing` closing; review_notes in DB: "research_summary_with_confound" |
| Mirrored "such as" example pairs pulling attention to examples, not "same criteria" | S5 parenthetical clarification density (§22.2) |
| Inverted comparative "as were those of" — where the confound lives | S2 subordinate clause density; `evidence_location_key: main_clause` |
| Sentence-final "therefore" signals a deduction, not a restatement | `solver_pattern_key: identify_logical_gap` (§9) |
| Parenthesized binomial | Would fail S8 under §22 (parentheses reserved for dates/citations) — official item, so noted, not corrected |

### Template — Item 0

| Field | Value |
|---|---|
| Passage length | 78 words / 3 sentences |
| stimulus_mode_key | passage_excerpt |
| stem_type_key | most_logically_completes |
| reading_focus_key · skill_family_key | implication_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · main_clause |
| target_test_construct_key (§2.3) | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key | research_summary · none (no control condition; closest §13.4 recipe is `study_design_isolation_limit`) |
| reasoning_trap_key | overreach |
| distractor_type_keys (B/C/D) | overreach / scope_error / topical_relevance_without_logical_connection |
| plausibility_source_keys (B/C/D) | topical_proximity / topical_proximity / common_sense_appeal |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | medium / medium / medium / low |

---

# Item 1 — Generated, `high` (study_design_isolation_limit, two co-varying factors)

### Phase 1 — generation_profile (§23.2)

```json
{
  "topic_broad_key": "science",
  "topic_fine": "animal cognition",
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "implication_inference",
  "target_test_construct_key": "inference_boundary_control",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "overreach",
  "passage_structure_pattern": "research_summary",
  "passage_architecture_key": "experiment_hypothesis_control_result",
  "inference_type_note": "study_design_isolation_limit",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "target_difficulty_overall": "high",
  "target_distractor_pattern": [
    "overreach — attributes the result to the intended factor (observational learning) despite the confound",
    "contradiction — concludes no effect exists",
    "topical_relevance_without_logical_connection — dismisses the study for a reason unrelated to the confound"
  ],
  "polarity_context": null, "target_sentence_function_role": null,
  "quantitative_sub_pattern": null, "two_part_claim": false
}
```

### Phase 2 — Passage (109 words; sentence lengths 33 / 10 / 6 / 33 / 27)

> In a 2021 study, Mara Lindqvist and colleagues at the University of Gothenburg tested whether captive octopuses could learn a foraging task by observing a trained conspecific, a member of their own species. One group watched a demonstrator pry open a latched container; a control group received no demonstration. The demonstration sessions, however, were run each morning immediately after the animals' overnight fast, whereas the control trials, for logistical reasons, took place several hours later, after a partial ration had been provided. Because an octopus's motivation to manipulate an unfamiliar object appears to vary with its hunger level, any advantage the observer group displayed in solving the container task ______

§22.7 check: S1 ✓ (6–33) · S2 ✓ (~2 subordinate/100w) · S3 ✓ ("appears to vary") · S4 ✓ (named researcher + institution + year) · S5 ✓ ("conspecific, a member of their own species") · S6 ✓ (demonstration, motivation) · S7 ✓ (2 passive: "were run," "had been provided") · S8 ✓ (semicolon) · no contractions · Tier 2: demonstrate, manipulate, vary ✓ · opening = research-finding lead ✓ · closing = limitation ✓ · FAILURE-01…10 clear.

### Phase 3 — Stem
"Which choice most logically completes the text?" (§3.2 canonical, unaltered)

### Phase 4 — Options

| | Option | `distractor_type_key` | `plausibility_source_key` | why_wrong |
|---|---|---|---|---|
| **A ✅** | cannot be confidently attributed to observational learning rather than to the difference in hunger between the two groups. | `correct` | — | Recipe-exact isolation-limit inference: two factors co-vary (demonstration + feeding state), so neither can be isolated. **evidence_span_text:** "the demonstration sessions, however, were run each morning immediately after the animals' overnight fast, whereas the control trials … took place several hours later, after a partial ration had been provided." |
| B | confirms that octopuses are capable of acquiring a novel foraging skill by watching a member of their own species. | `overreach` | `partial_truth` | States the conclusion the study *set out* to show, ignoring the confound the passage just established. Survives first pass — it is what a skimming reader expects. |
| C | indicates that watching a demonstrator has no measurable effect on an octopus's ability to open a container. | `contradiction` | `topical_proximity` | Passage says the *design* cannot isolate the cause, not that the effect is absent; "no measurable effect" is the opposite error from B. |
| D | should be discounted because captive octopuses rarely encounter latched containers outside the laboratory. | `topical_relevance_without_logical_connection` | `common_sense_appeal` | Dismisses the study for an ecological-validity reason the passage never raises; the stated flaw is the feeding-time confound. |

§16.4 gate: distinct failure paths ✓ · options 16–19 words, all declarative claims about the result ✓ · key not longest/most hedged ✓ · ≥2 survive first pass (B, C) ✓.

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| Two co-varying factors (demonstration + hunger) must be tracked across two groups on two timelines | `passage_architecture_key: experiment_hypothesis_control_result` + `inference_type_note: study_design_isolation_limit` |
| Confound arrives as a "however … whereas … for logistical reasons" chain | S2 (two subordinate clauses in one sentence); `evidence_location_key: subordinate_clause` |
| Causal premise buried in a sentence-initial "Because" clause | S2; §14.2 high — "multiple passage elements must be held simultaneously" |
| Short sentence 2/3 (10 + 6 words) gives a false sense of simplicity before the 33-word confound sentence | S1 mixed length |

### Template — Item 1

| Field | Value |
|---|---|
| Passage length | 109 words / 4 sentences (one semicolon-joined) |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | implication_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · subordinate_clause |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key · inference_type_note | research_summary · experiment_hypothesis_control_result · study_design_isolation_limit |
| reasoning_trap_key | overreach |
| distractor_type_keys (B/C/D) | overreach / contradiction / topical_relevance_without_logical_connection |
| plausibility_source_keys (B/C/D) | partial_truth / topical_proximity / common_sense_appeal |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / high / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "inference_type: study_design_isolation_limit — demonstration condition co-varies with feeding state; correct option states non-attributability." |

---

# Item 2 — Generated, `high` (unit-of-analysis confound; ecological aggregation)

### Phase 1 — generation_profile

```json
{
  "topic_broad_key": "environment",
  "topic_fine": "urban heat / public health",
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "implication_inference",
  "target_test_construct_key": "inference_boundary_control",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "overreach",
  "passage_structure_pattern": "cautionary_framing",
  "passage_architecture_key": null,
  "inference_type_note": "study_design_isolation_limit",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "target_difficulty_overall": "high",
  "target_distractor_pattern": [
    "contradiction — concludes no effect exists",
    "scope_error — redirects the limitation to other cities",
    "cause_effect_misalignment — assigns a direction of bias using an unstated demographic relationship"
  ],
  "polarity_context": null, "target_sentence_function_role": null,
  "quantitative_sub_pattern": null, "two_part_claim": false
}
```

### Phase 2 — Passage (106 words; sentence lengths 33 / 13 / 41 / 19)

> In a 2019 analysis of hospital records from Phoenix, Arizona, epidemiologist Dana Okafor and colleagues examined whether urban tree canopy—the layer of leaves and branches that shades the ground—reduces heat-related illness. Neighborhoods with denser canopy reported markedly fewer heat-related admissions during summer heat waves. The neighborhoods, however, were defined by administrative boundaries that in several cases encompassed both heavily shaded residential blocks and sparsely planted commercial districts, and the team assigned each neighborhood a single average canopy value rather than measuring shade at individual residences. Given that residents of one neighborhood may therefore have experienced substantially different degrees of shading, the study's neighborhood-level comparison ______

§22.7 check: S1 ✓ (13–41) · S2 ✓ · S3 ✓ ("may therefore") · S4 ✓ (named epidemiologist + year + dataset) · S5 ✓ (em-dash appositive defining "tree canopy") · S6 ✓ (analysis, admissions, comparison) · S7 ✓ ("were defined") · S8 ✓ (em dash pair) · Tier 2: encompass, substantially, markedly ✓ · opening = research-finding lead ✓ · closing = limitation ✓ · FAILURE-09 check: the positive finding survives the qualification (canopy may still matter; the design just can't show *who* benefited) ✓.

### Phase 3 — Stem
"Which choice most logically completes the text?"

### Phase 4 — Options

| | Option | `distractor_type_key` | `plausibility_source_key` | why_wrong |
|---|---|---|---|---|
| **A ✅** | cannot establish whether the residents who were actually shaded by dense canopy were the ones who avoided hospitalization. | `correct` | — | Required by the aggregation flaw: a neighborhood average hides within-neighborhood variation, so individual exposure cannot be linked to individual outcome. **evidence_span_text:** "assigned each neighborhood a single average canopy value rather than measuring shade at individual residences." |
| B | indicates that canopy density has no genuine effect on heat-related illness in Phoenix. | `contradiction` | `topical_proximity` | A coarse measurement cannot *disprove* the effect; the passage only limits what can be inferred. |
| C | cannot be extended to cities whose neighborhoods are defined by natural rather than administrative boundaries. | `scope_error` | `topical_proximity` | The problem is internal (heterogeneous units), not transferability to other cities. |
| D | likely understated the benefits of canopy, since residential blocks tend to house more heat-vulnerable people than commercial districts do. | `cause_effect_misalignment` | `common_sense_appeal` | Assigns a *direction* of bias via a demographic relationship the passage never states; the passage supports only "cannot tell," not "understated." Survives first pass because it sounds like informed reasoning. |

§16.4 gate: distinct failure paths ✓ · options 14–21 words ✓ · key not longest ✓ · ≥2 survive first pass (D, and B for readers who equate "flawed" with "null") ✓.

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| Positive finding in S2, undercut in S3 — reader has already formed a belief | `passage_structure_pattern: cautionary_framing` (§15.2); §22.3 tension arc |
| Two-part flaw split across a compound sentence (heterogeneous units **and** single averaged value) — both halves needed | S2; §14.2 high "multiple elements held simultaneously" |
| Abstract confound (level of measurement) vs. the original's concrete one (task difficulty) | `inference_type_note: study_design_isolation_limit`; difficulty_inference: high |
| "Given that … may therefore …" nests an inference inside a presupposition | S2 nominal/adverbial clause; `evidence_location_key: subordinate_clause` |

### Template — Item 2

| Field | Value |
|---|---|
| Passage length | 106 words / 4 sentences |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | implication_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · subordinate_clause |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key · inference_type_note | cautionary_framing · null · study_design_isolation_limit |
| reasoning_trap_key | overreach |
| distractor_type_keys (B/C/D) | contradiction / scope_error / cause_effect_misalignment |
| plausibility_source_keys (B/C/D) | topical_proximity / topical_proximity / common_sense_appeal |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / high / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "inference_type: study_design_isolation_limit — ecological aggregation; correct option states individual-level attribution is unavailable." |

---

# Item 3 — Generated, **extra-hard** (alternative_explanation_ruled_out + subgroup limit stacked)

Difficulty lever: §14.2 high requires "trap answers feel like defensible logical positions but exceed the evidence by one step." This item stacks two §15.3 architectures so that the correct inference must honor **both** the ruled-out alternative **and** a subgroup restriction; each distractor drops exactly one constraint.

### Phase 1 — generation_profile

```json
{
  "topic_broad_key": "science",
  "topic_fine": "marine ecology / larval settlement",
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "causal_inference",
  "target_test_construct_key": "inference_boundary_control",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "scope_extension",
  "passage_structure_pattern": "research_summary",
  "passage_architecture_key": "alternative_explanation_ruled_out",
  "inference_type_note": "subgroup_overgeneralization_limit (secondary architecture: studied_subgroup_generalization_limit)",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "target_difficulty_overall": "high",
  "target_distractor_pattern": [
    "cause_effect_misalignment — attributes settlement to the ruled-out explanation (chemical cues) [§15.3 mandatory for this architecture]",
    "scope_error — extends the acoustic result from nocturnal settlers to all settlers, dropping the subgroup constraint [primary trap]",
    "overreach — leaps from larval attraction to reef population recovery"
  ],
  "polarity_context": null, "target_sentence_function_role": null,
  "quantitative_sub_pattern": null, "two_part_claim": false
}
```

### Phase 2 — Passage (117 words; sentence lengths 19 / 23 / 14 / 25 / 31 / 5)

> Larval reef fish, which drift at sea for weeks before settling, tend to colonize healthy reefs rather than degraded ones. Marine biologist Tomás Herrera and colleagues proposed that larvae navigate by sound, since healthy reefs teem with snapping shrimp and grunting fish; a rival account holds that larvae instead follow chemical cues released by live coral. To distinguish the two, recordings of healthy-reef sound were broadcast from speakers placed on rubble patches, areas of dead coral fragments with no living tissue. Larvae of nocturnally settling damselfish arrived at the broadcast patches at rates comparable to those observed on intact reef, whereas larvae of species that settle by day showed no such response. Herrera's results therefore suggest that ______

§22.7 check: S1 ✓ (5–31) · S2 ✓ (relative + adverbial + "whereas") · S3 ✓ ("tend to," "proposed," "suggest") · S4 ✓ (named biologist) · S5 ✓ ("rubble patches, areas of dead coral fragments with no living tissue") · S6 ✓ (settlement, response, account) · S7 ✓ ("were broadcast") · S8 ✓ (semicolon) · Tier 2: colonize, distinguish, comparable ✓ · Tier 3 defined: rubble patches ✓ · opening = definitional/contextual lead ✓ · closing = implication ✓ · §15.3 `alternative_explanation_ruled_out` elements present: X (sound) proposed ✓, Y (chemical cues) identified ✓, test that rules Y out (no live coral present, larvae still arrive) ✓, conclusion at blank ✓. Secondary architecture `studied_subgroup_generalization_limit`: subgroup named (nocturnal settlers) ✓, explicit warning (diurnal settlers showed no response) ✓.

### Phase 3 — Stem
"Which choice most logically completes the text?"

### Phase 4 — Options

| | Option | `distractor_type_key` | `plausibility_source_key` | why_wrong |
|---|---|---|---|---|
| **A ✅** | sound alone may be sufficient to attract nocturnally settling larvae, even in the absence of live coral. | `correct` | — | Honors both constraints: Y ruled out (no live coral, larvae still came) **and** result restricted to the nocturnal subgroup. **evidence_span_text:** "Larvae of nocturnally settling damselfish arrived at the broadcast patches at rates comparable to those observed on intact reef, whereas larvae of species that settle by day showed no such response." |
| B | chemical cues from live coral, rather than sound, are the primary signal guiding larvae to settlement sites. | `cause_effect_misalignment` | `passage_vocabulary_overlap` | Attributes the result to the *ruled-out* explanation — the test patches had no living coral, so chemical cues cannot account for arrival. |
| C | reef sound is sufficient to attract settling larvae regardless of whether they settle by day or by night. | `scope_error` | `partial_truth` | Correct about sound; drops the subgroup constraint. The passage *states* diurnal settlers showed no response. Differs from A by one clause — the §14.2 "exceeds evidence by one step" trap. |
| D | broadcasting healthy-reef sound could allow degraded reefs to recover their former fish populations. | `overreach` | `common_sense_appeal` | Leaps from larval *arrival* to population *recovery*; passage measures attraction, not survival or recruitment. Also a prescription-style closer §22.3 flags as inauthentic. |

§16.4 gate: three distinct keys ✓ · options 15–18 words, all mechanism claims ✓ · key not longest (B and C are equal length) ✓ · ≥2 survive first pass: **C** (one word — "regardless" — is the only error) and **B** (chemical cues appear verbatim in the passage and are widely believed) ✓ · §15.3 mandatory ruled-out-explanation distractor present (B) ✓ · §21 subgroup-limit distractor present (C) ✓.

### Why this is harder than Items 1–2

| Lever | Item 1/2 | Item 3 |
|---|---|---|
| Constraints the correct answer must satisfy | 1 (non-attributability) | 2 (Y ruled out **and** subgroup-only) |
| Distractors that survive first-pass elimination | 2 | 2, but C differs from the key by a single adverb |
| Focus key | implication_inference | causal_inference — student must state what the manipulation *reveals about mechanism* (§13.4 mechanism-test note) |
| Architectures stacked | 1 | 2 (§15.3 `alternative_explanation_ruled_out` + `studied_subgroup_generalization_limit`) |
| Reading load | Track 2 groups × 1 confound | Track 2 hypotheses × 1 manipulation × 2 subgroups |

### Template — Item 3

| Field | Value |
|---|---|
| Passage length | 117 words / 5 sentences (one semicolon-joined) |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | causal_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · main_clause (result sentence) |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key · inference_type_note | research_summary · alternative_explanation_ruled_out · subgroup_overgeneralization_limit |
| reasoning_trap_key | scope_extension |
| distractor_type_keys (B/C/D) | cause_effect_misalignment / scope_error / overreach |
| plausibility_source_keys (B/C/D) | passage_vocabulary_overlap / partial_truth / common_sense_appeal |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / high / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "inference_type: subgroup_overgeneralization_limit stacked on alternative_explanation_ruled_out; correct option must retain the nocturnal-settler restriction; C is the canonical one-step overextension." |

---
---

# Item 4 — Opus 5 re-run · **extra-hard** (`indirect_effect_mediation`, severed-mediator prediction)

Independent re-run of the same task on a different model, same rule set. Design goal: fill a cell of the rules matrix that Items 0–3 left empty, rather than re-skinning the confound pattern all four share.

| Dimension | Items 0–3 | Item 4 |
|---|---|---|
| `passage_architecture_key` | none / `experiment_hypothesis_control_result` / none / `alternative_explanation_ruled_out` + subgroup | **`indirect_effect_mediation`** (§15.3, previously unused) |
| `reading_focus_key` | implication_inference ×3, causal_inference ×1 | **`predictive_inference`** (§7.4, previously unused) |
| `reasoning_trap_key` | overreach ×3, scope_extension ×1 | **`cause_effect_misalignment`** |
| `passage_structure_pattern` | research_summary ×3, cautionary_framing ×1 | **`claim_evidence_explanation`** |
| Reasoning move | "the design cannot isolate the cause" (all four) | "the mediator has been severed — predict the downstream effect fails **despite** the upstream cause firing normally" |

The difficulty lever is not passage length. It is that the airborne route is **closed in sentence 4 and never mentioned again**: the correct prediction, and the elimination of the primary trap, both depend on carrying that constraint across two sentence boundaries to a trial described only in terms of the mesh.

### Phase 1 — generation_profile (§23.2)

```json
{
  "topic_broad_key": "science",
  "topic_fine": "plant-soil ecology",
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "predictive_inference",
  "target_test_construct_key": "inference_boundary_control",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "cause_effect_misalignment",
  "passage_structure_pattern": "claim_evidence_explanation",
  "passage_architecture_key": "indirect_effect_mediation",
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "target_difficulty_overall": "high",
  "target_distractor_pattern": [
    "opposite trend — predicts the defense strengthens, via an invented allocation trade-off",
    "wrong condition — reinstates the direct airborne route the bags have closed [primary trap; also satisfies the §15.3 'ignores the mediation chain' requirement]",
    "extrapolate beyond evidence — projects one signaling trial onto a season-long outcome"
  ],
  "polarity_context": null,
  "target_sentence_function_role": null,
  "quantitative_sub_pattern": null,
  "inference_type_note": null,
  "two_part_claim": false
}
```

`inference_type_note` is `null` by design: §16.8 makes it mandatory only for `mechanism_manipulation_test` and `studied_subgroup_generalization_limit`. Inventing a value here would violate §1.3 (no unapproved production keys). The mediation logic is recorded in `review_notes` instead.

### Phase 2 — Passage (107 words; sentence lengths 20 / 9 / 17 / 34 / 23 / 5)

> Aphids attacking a bean plant trigger the release of volatile compounds, prompting nearby plants to raise their own chemical defenses. The warning appears to travel below ground as well. Ecologist Priya Raghunathan attributed this second route to mycorrhizae—fungal filaments linking the roots of separate plants. Every shoot was kept sealed in an airtight bag, so no neighbor could receive airborne cues; even so, neighbors mounted a defense whenever their roots shared a fungal network with an attacked plant. In a further trial, a fine mesh separated the roots of a pair, and aphids were introduced to one of the two plants. Raghunathan predicted that its neighbor ______

**§15.3 `indirect_effect_mediation` required elements**

| Required element | Where |
|---|---|
| (1) factor A → factor C relationship stated | S1: aphid attack → neighbors raise defenses |
| (2) additional factor B identified as mediator | S3: mycorrhizae proposed as the second route |
| (3) evidence that A→B→C rather than A→C directly | S4: every shoot bagged (airborne A→C closed) yet neighbors sharing a root network still responded |

**§16.5 self-containment** — the final trial states its own trigger ("aphids were introduced to one of the two plants"), so the correct answer does not rest on an unstated premise. Everything the prediction needs is on the page.

**§22.7 style gate**

| Check | Result |
|---|---|
| S1 mixed length — one ≤15, one ≥25 | ✓ 5, 9 and 34 |
| S1 — no 3 consecutive within 5 words | ✓ gaps 11 / 8 / 17 / 11 / 18 |
| S2 subordinate density 1–2 per 100w | ✓ 2 finite ("whenever their roots shared…", "that its neighbor…") ≈ 1.9/100; participles and the coordinating "so" carry the rest |
| S3 epistemic hedging | ✓ "appears to travel", "attributed", "predicted" |
| S4 named attribution | ✓ "Ecologist Priya Raghunathan" (approved *named researcher only* form) |
| S5 appositive | ✓ em-dash: "mycorrhizae—fungal filaments linking the roots of separate plants" |
| S6 nominalization ≥2/100w | ✓ release, defenses, protection, trial |
| S7 passive 20–35% (science) | ✓ 2 of 6 = 33% ("was kept sealed", "were introduced") — the §22.5 agentless methods pattern |
| S8 internal punctuation at >80w | ✓ one em-dash pair, one semicolon |
| Register / Tier 2 / Tier 3 defined | ✓ no contractions or intensifiers; attributed, predicted, prompting; mycorrhizae defined |
| Opening / arc / closing (§22.3) | ✓ definitional-contextual lead; claim→evidence→test; closes on the prediction |
| FAILURE-01…10 | ✓ none present (blank is final — FAILURE-08 clear) |

### Phase 3 — Stem
"Which choice most logically completes the text?" (§3.2 canonical, unaltered)
**disambiguation_rule_applied:** §17 rule 1 — blank at passage end ⇒ `inferences`, not `command_of_evidence_textual`.

### Phase 4 — Options

| | Option | `distractor_type_key` (§12.1) | `plausibility_source_key` (§12.2) | §16.9 recipe slot | why_wrong |
|---|---|---|---|---|---|
| **A ✅** | would fail to raise its chemical defenses, because severing the filaments closes the last route open to the signal. | `correct` | — | — | Both routes are shut: the bags closed the airborne path (S4), the mesh closes the hyphal path (S5). The prediction follows necessarily from Raghunathan's own hypothesis. **evidence_span_text:** "Every shoot was kept sealed in an airtight bag, so no neighbor could receive airborne cues." |
| B | would mount an even stronger defense, since plants cut off from fungal partners invest more heavily in chemical protection. | `inverted_logic` | `common_sense_appeal` | opposite trend | Predicts the reverse direction using a resource-allocation trade-off the passage never mentions. Plausible to students who know mycorrhizae also carry nutrients. |
| C | would still mount its usual defense, because the attacked plant remains close enough for its volatile compounds to reach it. | `cause_effect_misalignment` | `partial_truth` | wrong condition | Reinstates the direct A→C airborne route. That route is genuinely real (S1) — but every shoot is bagged, a constraint stated once, two sentences earlier, and never repeated. **Primary trap.** Also the §15.3-mandatory "ignores the mediation chain" option. |
| D | would remain vulnerable to aphid damage for the rest of the season, unlike neighbors with intact fungal connections. | `overreach` | `partial_truth` | extrapolate beyond evidence | Projects a single signaling trial onto a season-long outcome. The passage measures whether defenses are raised, never survival, damage, or duration. |

**§16.9 per-focus recipe (`predictive_inference`)** — required distractor behavior is "extrapolate beyond evidence, choose wrong condition, or predict opposite trend." All three slots are filled, one each. (§23.5 Step 4d.)

**§16.4 quality gate**

- Incorrectness — each `why_wrong` names a specific textual defeater ✓
- Plausibility — every distractor has a non-null `plausibility_source_key` ✓
- Diversity — three distinct `distractor_type_key` values and three distinct reasoning paths (opposite direction / blocked route reinstated / horizon extended) ✓
- Construct alignment — all three fail `inference_boundary_control`, none by topic mismatch ✓
- Clue control — options 18–20 words; the key is *not* the longest ✓
- Homogeneity — all four open with "would" + verb phrase, same abstraction level, same semantic category (predicted outcome for the neighbor) ✓
- Separation margin — **all three survive first-pass elimination**: none is defeated by the mesh alone; B needs the direction of the hypothesis, C needs the bags from S4, D needs the scope of what was measured ✓

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| The airborne route is closed in S4 and never mentioned again; the S5 trial is described only in terms of the mesh | §14.2 Inferences `high`: "multiple passage elements must be held simultaneously" |
| The real, stated airborne route (S1) is exactly what distractor C reinstates — the passage arms its own best trap | `plausibility_source_key: partial_truth`; §16.2 surface-plausible distractor |
| Mediator vs. cause: "route", "travels", "linking" all frame mycorrhizae as a channel, never a source | §15.3 `indirect_effect_mediation` generation note |
| A 9-word and a 5-word sentence flank the 34-word mechanism sentence, lowering the reader's guard on either side | S1 mixed sentence length (§22.2) |
| The blank sits inside a reported prediction ("Raghunathan predicted that…"), so the answer must be what *she* expects under her hypothesis, not what is independently true | `answer_mechanism_key: inference`; §7.4 `predictive_inference` |

### §21 Validator checklist

`question_family_key` information_and_ideas ✓ · `skill_family_key` inferences ✓ · `reading_focus_key` predictive_inference ∈ §7.4 list ✓ · `grammar_role_key` null ✓ · `grammar_focus_key` null ✓ · `stem_type_key` matches §3.2 wording ✓ · `stimulus_mode_key` prose_single ✓ · `paired_passage_text` null ✓ · `table_data`/`graph_data` null ✓ · every option has `distractor_type_key` + `why_wrong` ✓ · exactly one `is_correct: true` with `distractor_type_key: "correct"` ✓ · `precision_score: 3` on A only ✓ · `evidence_span_text` populated ✓ · `annotation_confidence` populated ✓ · `target_test_construct_key` populated ✓ · `target_craft_subconstruct_key` null (not Craft) ✓ · no distractor co-correct ✓ · three distinct distractor keys ✓ · key not exposed by length/register/polish ✓ · options homogeneous ✓ · §18 forbidden patterns — none present ✓

### Template — Item 4

| Field | Value |
|---|---|
| Passage length | 107 words / 6 sentences (one semicolon-joined) |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | predictive_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · main_clause |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key · inference_type_note | claim_evidence_explanation · indirect_effect_mediation · null |
| reasoning_trap_key | cause_effect_misalignment |
| distractor_type_keys (B/C/D) | inverted_logic / cause_effect_misalignment / overreach |
| plausibility_source_keys (B/C/D) | common_sense_appeal / partial_truth / partial_truth |
| §16.9 slots (B/C/D) | opposite trend / wrong condition / extrapolate beyond evidence |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / high / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "Mediation chain A(aphid attack)→B(hyphal network)→C(neighbor defense). The manipulation severs B while A fires normally and the airborne A→C path stays closed by the bagging protocol established two sentences earlier; the correct option predicts C fails. Primary trap (C) reinstates the closed direct path." |

---

## Rules findings from this pass (Opus 5)

1. **§22.2 Rule S2 contradicts the rules' own exemplar.** S2 targets *1–2 subordinate clauses per 100 words* and calls 3+ a failure. The §23.7 worked-example passage contains ~5 finite subordinate clauses in ~100 words, and the official PT10 Q17 passage runs ~3 per 78 words. A 1–2/100w ceiling produces prose flatter than any released DSAT passage. **Amendment candidate (§20): raise S2 to 3–5 per 100 words**, or restate the target as *finite* subordinate clauses only and let participial/reduced forms run free — which is how Item 4 was written to pass.
2. **§22.7 and §21 cannot catch a missing experimental trigger.** Item 4's first draft described the final trial's manipulation (mesh inserted) without stating that aphids were introduced, leaving the correct answer resting on an unstated premise. Both checklists passed it; only §16.5 ("self-contained — passage provides all information needed") catches it, and §16.5 has no checklist row. **Amendment candidate (§20): add a §21 row — "for items whose correct answer depends on an experimental result, the passage states the manipulation *and* its trigger."**
3. **§16.4 and §16.9 are separate gates and §23.5 requires both.** A distractor set can pass §16.4 (diversity, homogeneity, separation) while missing a §16.9 slot for the target focus key. Item 4's first draft had a `contradiction` distractor that filled none of `predictive_inference`'s three slots; re-keyed to `overreach` / extrapolate-beyond-evidence.
4. **§22.5 "typical architectures" is soft guidance, not a constraint.** `indirect_effect_mediation` is listed only under `science`, which is why Item 4 stayed in that domain despite Items 1 and 3 already using it. Moving mediation architectures to `social_studies` or `economics` would need an §20 amendment to the domain table.
5. Confirms the Sonnet 5 finding: DB `annotation_jsonb.options[].distractor_type_key` stores §10.1 question-level keys (`scope_extension`, `outside_knowledge`) that are not in the §12.1 option-level list. Item 4 uses §12.1 values only.

---
---

# Item 5 — Official Coll/Bianchi Mediterranean Biodiversity Census (annotated against rules_refactor)

Source: user-supplied screenshot (real-time messaging app), transcribed by hand. One character was reconstructed: the source rendered the sentence break before "a difference only partly attributable…" as `=`, almost certainly an em dash lost in screenshot OCR/font rendering — reproduced below as `—`. Everything else is verbatim as supplied.

**question_family_key:** information_and_ideas · **skill_family_key:** inferences · **reading_focus_key:** implication_inference · **stem_type_key:** most_logically_completes · **disambiguation_rule_applied:** §17 rule 1

> Marta Coll and colleagues' 2010 Mediterranean Sea biodiversity census reported approximately 17,000 species, nearly double the number reported in Carlo Bianchi and Carla Morri's 2000 census—a difference only partly attributable to the description of new invertebrate species in the interim. Another factor is that the morphological variability of microorganisms is poorly understood compared to that of vertebrates, invertebrates, plants, and algae, creating uncertainty about how to evaluate microorganisms as species. Researchers' decisions on such matters therefore can be highly consequential. Indeed, the two censuses reported similar counts of vertebrate, plant, and algal species, suggesting that ______

**Which choice most logically completes the text?**

| | Option | `distractor_type_key` (§12.1) | `plausibility_source_key` (§12.2) | why_wrong |
|---|---|---|---|---|
| **A** | Coll and colleagues reported a much higher number of species than Bianchi and Morri did largely due to the inclusion of invertebrate species that had not been described at the time of Bianchi and Morri's census. | `overreach` | `passage_vocabulary_overlap` | Upgrades S1's explicit qualifier "**only partly** attributable" into "**largely** due to." Directly contradicted by the passage's own hedge, and it never engages the final sentence's evidence (matching vertebrate/plant/algal counts) at all — it just re-states S1. |
| **B ✅** | some differences observed in microorganisms may have been treated as variations within species by Bianchi and Morri but treated as indicative of distinct species by Coll and colleagues. | `correct` | — | Required by the chain: microorganism species-boundary criteria are uncertain (S2) → researchers' *decisions* on such boundaries are consequential (S3) → other, better-understood groups counted the same both times (S4) → the disparity must be concentrated in microorganisms, and specifically in how each team *decided* to classify borderline variation. **evidence_span_text:** "creating uncertainty about how to evaluate microorganisms as species. Researchers' decisions on such matters therefore can be highly consequential." |
| **C** | Bianchi and Morri may have been less sensitive to the degree of morphological variation displayed within a typical species of microorganism than Coll and colleagues were. | `inverted_logic` | `near_synonym_appeal` | Swaps S3's "decisions" for "sensitivity" — but check the direction: less sensitivity to how much variation is *normal within* one species means novel-looking variants look like distinct species more readily, which predicts Bianchi/Morri counting **more** microorganism species, not fewer. Bianchi and Morri's count was the lower one. The option reverses the sign of its own mechanism relative to the passage's numbers. **Primary trap.** |
| **D** | the absence of clarity regarding how to differentiate among species of microorganisms may have resulted in Coll and colleagues underestimating the number of microorganism species. | `partial_match` | `common_sense_appeal` | Reuses the correct mechanism (classification uncertainty → miscount) but points it at the wrong referent: "underestimating" is measured against the *true, unknown* diversity of microorganisms, which the passage never addresses. The passage only supports a claim about the difference **between the two censuses**, and on that comparison Coll's count went up, not down. |

**Question-level trap (§10.1):** `reasoning_trap_key: inverted_logic` — C is the item's real center of difficulty; A and D are both defeated by a single sentence each (S1's "only partly," S4's higher-not-lower direction), but C requires tracing a two-step mechanism to its logical (reversed) conclusion.
**passage_architecture_key:** `null`. This is not a §15.3 experimental architecture — there is no manipulation and no ruled-out alternative. S1 explicitly keeps the invertebrate-description explanation partially valid ("only partly attributable," not "not attributable"), so nothing is *ruled out*; this is a comparative-census pattern, and the elimination logic (why the microorganism-specific gap must be decision-driven) lives in `review_notes`, not in an architecture key.
**passage_structure_pattern:** `compare_contrast` (§15.2) — the entire passage is organized around a group-by-group comparison of two censuses.

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| Explanation 1 (new invertebrate species) is given credit but explicitly capped at "only partly" — reader must not let it absorb the whole effect | S1 hedge; `distractor_type_key: overreach` is the predictable failure to cap it |
| The abstract mechanism ("researchers' decisions... consequential") is stated **before** the concrete evidence that requires it (matching non-microorganism counts) — student must hold the mechanism in mind across two sentences and apply it retroactively | §14.2 high — "multiple passage elements must be held simultaneously"; `evidence_location_key: main_clause` (S3) applied to evidence in S4 |
| C's within-species-variation direction runs opposite to the stated result | `reasoning_trap_key: inverted_logic`; no §21/§16.4/§22.7 checklist row catches a per-option direction error — it is a by-hand check, same class of gap as Item 4's §16.9 miss |
| D shifts the comparison's referent from "vs. Bianchi/Morri" to "vs. true diversity" | `plausibility_source_key: common_sense_appeal`; §16.2 surface-plausible distractor |

### Template — Item 5

| Field | Value |
|---|---|
| Passage length | 95 words / 4 sentences |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | implication_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · main_clause |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key | compare_contrast · null |
| reasoning_trap_key | inverted_logic |
| distractor_type_keys (A/C/D) | overreach / inverted_logic / partial_match |
| plausibility_source_keys (A/C/D) | passage_vocabulary_overlap / near_synonym_appeal / common_sense_appeal |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / medium / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "No §15.3 architecture — invertebrate-description explanation is explicitly retained in part, not ruled out. Correct answer requires combining S2–S4 into a decision-based (not discovery-based) account of the microorganism-specific gap. C's failure is directional, not merely terminological: 'less sensitive to within-species variation' predicts over-splitting (a higher count) for Bianchi/Morri, contrary to their actually lower count." |

---

# Item 6 — Generated, `high` (mirrors Item 5's exact trap/distractor recipe, new domain)

Per request: same traps, same distractor shapes, new content. Domain moved from marine biology/taxonomy to historical linguistics — the "species problem" (is this variation enough to name a new species?) has a well-known structural twin in linguistics (is this variation enough to name a new language, as opposed to a dialect?), which lets every mechanism in Item 5 carry over without forcing the taxonomy vocabulary.

### Phase 1 — generation_profile (§23.2)

```json
{
  "topic_broad_key": "social_studies",
  "topic_fine": "historical linguistics / language classification",
  "target_skill_family_key": "inferences",
  "target_reading_focus_key": "implication_inference",
  "target_test_construct_key": "inference_boundary_control",
  "target_craft_subconstruct_key": null,
  "target_reasoning_trap_key": "inverted_logic",
  "passage_structure_pattern": "compare_contrast",
  "passage_architecture_key": null,
  "inference_type_note": null,
  "target_stimulus_mode_key": "prose_single",
  "target_stem_type_key": "most_logically_completes",
  "target_difficulty_overall": "high",
  "target_distractor_pattern": [
    "overreach — upgrades the passage's explicit 'only partly' qualifier into the full explanation [mirrors Item 5 option A]",
    "inverted_logic — swaps the decision-based mechanism for a perceptual/attentiveness one, with the direction reversed relative to the stated result [primary trap; mirrors Item 5 option C]",
    "partial_match — reuses the correct mechanism but points it at an unaddressed absolute referent instead of the stated comparison [mirrors Item 5 option D]"
  ],
  "polarity_context": null, "target_sentence_function_role": null,
  "quantitative_sub_pattern": null, "two_part_claim": false
}
```

`passage_architecture_key` is `null` by design, mirroring Item 5: the documentation-of-new-languages explanation is kept explicitly partial, never ruled out, so no §15.3 architecture applies. `inference_type_note` is `null` for the same reason §13.4's isolation/subgroup recipes don't apply here — there is no study design and no subgroup claim, only a comparative count.

### Phase 2 — Passage (108 words; sentence lengths 46 / 35 / 11 / 16)

> Linguist Elena Marchetti and colleagues' 2015 survey of a mountainous border region identified roughly 140 distinct languages, nearly double the number recorded in a 1985 survey conducted by Klaus Reinholt—a difference only partly explained by Marchetti's team documenting several previously unrecorded languages spoken in isolated valleys. Another factor is that the criteria for distinguishing a language from a dialect are especially unsettled for varieties linked in a dialect continuum—a chain of neighboring speech communities that shade gradually into one another. Linguists' judgments on such borderline cases can therefore carry substantial weight. Indeed, the two surveys reported similar counts of languages that possess long-established written literatures, suggesting that ______

**§22.7 style gate**

| Check | Result |
|---|---|
| S1 mixed length — one ≤15, one ≥25 | ✓ 11 and 46/35 |
| S1 — no 3 consecutive within 5 words | ✓ gap(1,2,3)=35, gap(2,3,4)=24 |
| S2 subordinate density | 3 finite clauses ("that the criteria…are unsettled," "that shade gradually…," "that possess long-established…") in 108w ≈ 2.8/100w — within the amended 3–5/100w range flagged in the Item 4 findings, over the un-amended 1–2/100w rule as written |
| S3 epistemic hedging | ✓ "roughly," "may have been," "can therefore carry" |
| S4 named attribution | ✓ "Linguist Elena Marchetti," "Klaus Reinholt" (named-researcher-only form) |
| S5 appositive | ✓ em-dash: "a dialect continuum—a chain of neighboring speech communities that shade gradually into one another" |
| S6 nominalization | ✓ survey, difference, judgments, criteria |
| S7 passive | 1 of 4 sentences ("are especially unsettled," adjectival passive) = 25% |
| S8 internal punctuation at >80w | ✓ two em dashes |
| Register / Tier 2 / Tier 3 defined | ✓ no contractions or intensifiers; "dialect continuum" defined in-line |
| Opening / arc / closing (§22.3) | ✓ research-finding lead; claim → two contributing factors → comparative evidence; closes on the inference |
| FAILURE-01…10 | ✓ none present (blank is final — FAILURE-08 clear; named researchers — FAILURE-03 clear) |

### Phase 3 — Stem
"Which choice most logically completes the text?" (§3.2 canonical, unaltered)
**disambiguation_rule_applied:** §17 rule 1 — blank at passage end ⇒ `inferences`.

### Phase 4 — Options

| | Option | `distractor_type_key` (§12.1) | `plausibility_source_key` (§12.2) | §16.9 slot (implication_inference) | why_wrong |
|---|---|---|---|---|---|
| **A** | Marchetti and colleagues identified far more languages than Reinholt did largely because they documented languages in isolated valleys that had gone unrecorded in 1985. | `overreach` | `passage_vocabulary_overlap` | contradicted by a constraint | Upgrades S1's "only partly explained" into "largely because," and ignores S4's evidence entirely — a re-statement of S1, not a completion of S4's inference. |
| **B ✅** | some speech varieties that Reinholt classified as dialects of a single language may have been classified by Marchetti and colleagues as distinct languages. | `correct` | — | — | Required by the chain: language/dialect boundary criteria are unsettled (S2) → linguists' judgments on such cases are consequential (S3) → counts of clearly-established languages matched across both surveys (S4) → the gap must sit in the boundary cases, and specifically in how each survey's team classified them. **evidence_span_text:** "the criteria for distinguishing a language from a dialect are especially unsettled… Linguists' judgments on such borderline cases can therefore carry substantial weight." |
| **C** | Reinholt may have been less aware of how much variation ordinarily occurs among the dialects of a single language than Marchetti and colleagues were. | `inverted_logic` | `near_synonym_appeal` | plausible but not required | Swaps "judgment/classification" for "awareness of the normal range," and reverses the direction: someone *less aware* of how much dialectal variation is ordinary within one language would more readily read an observed variant as a separate language — over-splitting, i.e. a **higher** count. Reinholt's count was the lower one. Same primary-trap shape as Item 5's option C. (An earlier draft read "less attentive to the differences" — that wording predicts noticing *fewer* differences, i.e. lumping, i.e. a lower count, which does not contradict the passage. Reworded to "less aware of how much variation ordinarily occurs" so the mechanism is unambiguously about the normal-range judgment, not raw attentiveness.) |
| **D** | the lack of clear criteria for distinguishing languages from dialects may have caused Marchetti and colleagues to undercount the true number of distinct languages spoken in the region. | `partial_match` | `common_sense_appeal` | too broad | Reuses the correct mechanism (unclear criteria → miscount) but points it at the true, unaddressed number of languages in the region rather than at the stated Marchetti-vs-Reinholt comparison — on that comparison Marchetti's count went up, not down. |

**§16.9 per-focus recipe (`implication_inference`)** — required distractor behavior is "plausible but not required, too broad, or contradicted by a constraint." All three slots filled, one each, matching the slot pattern implicit in Item 5. (§23.5 Step 4d.)

**§16.4 quality gate**

- Incorrectness — each `why_wrong` names a specific textual defeater ✓
- Plausibility — every distractor has a non-null `plausibility_source_key` ✓
- Diversity — three distinct `distractor_type_key` values ✓
- Construct alignment — all three fail `inference_boundary_control`, none by topic mismatch ✓
- Clue control — options 23–28 words (A 24 / B 23 / C 24 / D 28); key is neither the longest nor a conspicuous outlier ✓
- Homogeneity — all four are declarative claims about what happened in the two surveys ✓
- Separation margin — A and C both survive a first pass (A reads as a plausible restatement until "only partly" is checked; C reads as a plausible mechanism swap until its direction is checked); D is the most exposed, since "true number in the region" is visibly untethered from the passage's actual comparison ✓

### Disruptors → rules counterparts

| Disruptor | Rules counterpart |
|---|---|
| S1's "only partly" cap must survive into option evaluation, or A looks correct | `distractor_type_key: overreach`; S1 hedge |
| The classification-judgment mechanism (S2–S3) is stated in the abstract, then must be applied to concrete evidence two sentences later (S4) | §14.2 high — "multiple passage elements held simultaneously" |
| C requires tracking the direction of a within-category-variation mechanism against the passage's actual (lower) count for Reinholt | `reasoning_trap_key: inverted_logic`; same by-hand check gap noted in Item 5 |
| D's referent shift (comparison vs. true regional total) is one word-group ("true number... in the region") away from being correct | `plausibility_source_key: common_sense_appeal` |

### Template — Item 6

| Field | Value |
|---|---|
| Passage length | 108 words / 4 sentences |
| stimulus_mode_key · stem_type_key | prose_single · most_logically_completes |
| reading_focus_key · skill_family_key | implication_inference · inferences |
| answer_mechanism_key · solver_pattern_key | inference · identify_logical_gap |
| evidence_scope_key · evidence_location_key | passage · main_clause |
| target_test_construct_key | inference_boundary_control |
| passage_structure_pattern · passage_architecture_key · inference_type_note | compare_contrast · null · null |
| reasoning_trap_key | inverted_logic |
| distractor_type_keys (A/C/D) | overreach / inverted_logic / partial_match |
| plausibility_source_keys (A/C/D) | passage_vocabulary_overlap / near_synonym_appeal / common_sense_appeal |
| §16.9 slots (A/C/D) | contradicted by a constraint / plausible but not required / too broad |
| grammar_role_key · grammar_focus_key | null · null |
| difficulty overall/reading/inference/vocab | high / medium / high / medium |
| review | annotation_confidence: high · needs_human_review: false · review_notes: "Mirrors Item 5's mechanism (boundary-classification decisions, not discovery, explain a category-specific count gap) in a new domain (language vs. dialect boundaries). C is the deliberate primary trap: the 'less attentive' mechanism, if true, predicts the opposite of Reinholt's actual (lower) count." |

---

## Rules findings from this pass

1. **Direction-of-effect errors aren't caught by any existing gate — and this pass caught a live instance of the gap in its own output, not just in the source item.** §21, §16.4, and §22.7 all check completeness, diversity, and style — none verifies that a distractor's causal mechanism, if actually true, would point toward the passage's stated result rather than away from it. Item 5's option C is built on this trap deliberately. But the *first draft* of Item 6's mirrored option C ("less attentive to the differences… among the dialects") independently fell into the same trap by accident: "less attentive to differences" predicts noticing *fewer* differences (lumping, a lower count) — the opposite direction from what the option needed to assert, and a direction that happened to be *consistent* with the passage rather than contradicted by it, which would have silently broken the item. Advisor review caught it; no rules checklist would have. This is the same class of gap as the Item 4 finding on §16.5/§16.9 (checklists validate structure, not per-option semantic correctness) — **amendment candidate (§20): add a §16.4 sub-check, "for any distractor asserting a causal or comparative mechanism, restate the mechanism as a prediction and confirm that prediction's direction against the passage's stated result — do this for generated distractors, not only annotated ones."**
2. **A "which explanation was ruled out" read is a trap for the annotator, not just the student.** Item 5 was initially miscoded `passage_architecture_key: alternative_explanation_ruled_out` because the passage discusses two candidate explanations for a count gap — but §15.3 architectures require an actual test that eliminates one candidate, and here the first explanation (new species/languages documented) is explicitly kept "only partly" valid, never ruled out. Comparative-count passages that mention more than one contributing factor should default to `passage_architecture_key: null` unless a specific ruling-out test is present in the text.
3. **§16.9's three `implication_inference` slots are coarser than the defeaters they're meant to cover.** C in both Item 5 and Item 6 is mapped to "plausible but not required," but its actual defeater is a direction contradiction — closer in kind to "contradicted by a constraint" (A's slot) than to genuine unrequired-but-possible territory. The three-slot menu doesn't have a category for "the option's own mechanism, followed through, contradicts the passage" — noted here rather than re-keyed, since forcing it into "contradicted by a constraint" would make A and C indistinguishable at the slot level despite having different textual defeaters (an explicit hedge vs. a derived direction).
4. **The "species problem" structural pattern generalizes across domains without needing a new architecture or trap key.** Boundary-classification-under-uncertainty (species vs. variation, language vs. dialect, and by extension: era vs. period in history, genre vs. subgenre in the arts) all fit `reading_focus_key: implication_inference` + `reasoning_trap_key: inverted_logic`/`overreach`/`partial_match` with no rules changes — only `topic_broad_key`/`topic_fine` change. Useful for future item generation: this recipe is a reusable template, not a one-off.
