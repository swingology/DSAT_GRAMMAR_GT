# rules_agent_dsat_reading_v1_1.md

## Purpose

This file is the v1.1 addendum to `rules_agent_dsat_reading_v1.md`.

It adds only what is missing or underspecified after cross-referencing the v1
reading file against College Board official answer explanations for PT4–PT11
(documented in `CB_ANSWERS_QUESTIONS_ANALYSIS.md`).

Load order: v1 base → this file.

All additions are non-breaking extensions. No existing key is renamed or
removed. New keys proposed here are production-ready unless marked
`proposed_only`.

---

## 1. Words in Context Additions

### 1.1 Add `polarity_fit` reading focus key

**Gap source:** PT4 M1 Q4 ("by no means" negation context), PT5 M1 Q5
("ameliorate unrepresentative samples"), PT6 M1 Q5 ("not inconsequential"
meaning significant). Coverage audit confirms: `negation` exists in the
grammar module but the reading module's WIC keys have no polarity-specific
variant.

**Add to §7.5 Words in Context focus keys:**

- `polarity_fit`

**Rule definition:**

> The passage contains a negator, a concessive phrase, or a double-negative
> construction ("by no means," "not atypical," "hardly insignificant") that
> reverses or qualifies the polarity of the target word or phrase. The correct
> word must preserve the logical polarity of the full construction, not the
> surface meaning of the surrounding words taken in isolation. Wrong answers
> select a word that is correct for the surface context but inverts the meaning
> when the negator is applied.

**Reading focus disambiguation:**

- If all four options are near-synonyms differing only in their evaluative
  direction when the negator is applied → `polarity_fit`
- If the passage has no negator or concessive and the distinction is purely
  tonal → `connotation_fit`

**Mandatory annotation requirement:**

For every WIC item where a negator, concessive phrase, or contrast marker
is present within the evidence span, annotate `evidence_span_text` with
the full phrase including the negator, not just the word immediately
surrounding the blank. Example: annotate "by no means ______" not just
"______."

Add to `review_notes`: "polarity_context: [name the negator or concessive]."

**Generation rule:**

When generating a `polarity_fit` item:
- Embed a negator, concessive, or double-negative construction in the
  passage at or adjacent to the blank
- All four options must be grammatically viable after the negator
- The correct option must produce the intended meaning when combined
  with the negator
- At least two wrong options must produce the opposite or an illogical
  meaning when combined with the negator — do not use options that are
  simply off-topic

Example construction:
```
The critic found the performance by no means ______ ; every detail
had been carefully rehearsed.
```
Correct: "unremarkable" (meaning it was remarkable, double negation)
Wrong traps: "brilliant" (ignores negator), "adequate" (ignores
negation direction), "poor" (inverts to wrong direction)

---

### 1.2 Add `polarity_mismatch` reasoning trap key

**Gap source:** Same items as §1.1.

**Add to §10.2 Craft and Structure reasoning trap keys:**

- `polarity_mismatch`

**Rule definition:**

> The option is a plausible word in isolation but inverts the intended
> meaning when combined with the passage's negator or concessive
> construction. The student selected the option by reading the surrounding
> words without applying the negator to the target blank.

**Use in option-level annotation:**

```json
{
  "distractor_type_key": "polarity_mismatch",
  "why_wrong": "The negator 'by no means' requires a word meaning X, but this option means the opposite of X when the negator is applied."
}
```

---

### 1.3 Extend phrase-level WIC generation notes

**Gap source:** PT6 M2 Q4 ("manifest in" as apparent from evidence), PT7 M1
Q7 (phrase-level meaning "proponent of"). Coverage audit confirms: stem
wording already allows "word or phrase" but no generation note enforces
phrase-level construction.

**Add to §16.4 generation stem wording conventions:**

> WIC items may test a multi-word phrase, not only a single word. When the
> correct answer is a phrase (e.g., "set out to," "made up for," "held
> back"), generate all four options as phrases of comparable length and
> structure so that no option is obviously wrong on length alone. Annotate
> `reading_focus_key: "contextual_meaning"` (default) or `"precision_fit"`
> if the distinction is between phrases of different scope or precision.
> Record `evidence_span_text` with the full phrase in context, not just the
> blank.

---

### 1.4 Add `negation_blindness` student failure mode key

**Add to §19 reading-specific `student_failure_mode_key` values:**

- `negation_blindness` — student selects an option that is contextually
  correct for the surface words but ignores a negator or concessive phrase
  in the evidence span, producing a meaning opposite to what the passage
  requires

---

## 2. Text Structure and Purpose Additions

### 2.1 Named rhetorical moves for sentence_function items

**Gap source:** Coverage audit line: "Purpose/function items may identify
concessions, limitations, conventional approaches, or detail elaboration —
add named rhetorical-move examples." Also: PT5 M1 Q9 (underlined concession
about unlikely ridership transfer), PT6 M2 Q8 (underlined concession /
limitation), PT7 M1 Q7 (parenthetical definition clarifies term), PT11 M2 Q6
(parenthetical definition of microfilm).

The current v1 §13.6 lists rhetorical verbs for `overall_purpose` but does
not enumerate the specific functional roles available for `sentence_function`
items. Official CB explanations for sentence-function questions always name
a specific rhetorical move.

**Add to §13.6 Text Structure and Purpose — Sentence function annotation
rule:**

The following named functional roles are approved for use in
`review_notes` and generation profiles when the focus key is
`sentence_function`. Each entry shows the functional label and the
typical stem answer phrasing.

| Functional role | Typical answer phrasing |
|---|---|
| `concession` | "to acknowledge a limitation of / an objection to the preceding claim" |
| `elaboration` | "to provide additional detail supporting the preceding claim" |
| `contrast_motivation` | "to introduce a contrast that motivates the explanation that follows" |
| `parenthetical_definition` | "to clarify the meaning of a term introduced in the sentence" |
| `example` | "to provide a specific example of the general claim" |
| `consequence` | "to describe the effect or result of the preceding event or condition" |
| `hypothesis` | "to present the question or hypothesis the study is designed to test" |
| `counter_evidence` | "to present evidence that complicates or challenges the main claim" |
| `scope_qualification` | "to limit the range of the preceding claim to specific conditions" |
| `conventional_approach` | "to describe the standard or prior method that the text then challenges" |
| `obstacle` | "to describe a difficulty that the following text explains how to overcome" |
| `background_setup` | "to establish the context necessary for the main finding to be meaningful" |

**Generation rule for sentence_function items:**

When generating a `sentence_function` item, select one functional role
from the table above before writing the passage. The passage must contain
a sentence that unambiguously performs exactly that role. Record the
functional role in `generation_profile` under:

```json
{
  "target_sentence_function_role": "parenthetical_definition"
}
```

Wrong options must use incorrect functional labels from the same table or
closely related labels (e.g., offering `elaboration` when the correct
answer is `concession`). At least one wrong option must describe a plausible
but wrong action verb (e.g., "to challenge" when the sentence actually
concedes).

---

### 2.2 Add `parenthetical_definition` as a named sentence function pattern

**Gap source:** PT7 M1 Q7, PT11 M2 Q6. Both items test whether the student
identifies that a parenthetical phrase defines or clarifies a term just
introduced, not that it provides broader passage context.

**Add to §16 Generation Rules — additional sentence_function generation
constraint:**

> Parenthetical-definition items require a passage where a technical or
> specialized term is introduced in a sentence and immediately followed by a
> parenthetical phrase that defines it (enclosed in parentheses, dashes, or
> commas). Wrong options describe broader passage purposes (to explain the
> importance of X, to argue that X is significant) rather than the local
> defining function. The correct answer must identify the clarification of a
> term, not a broader rhetorical move.

---

## 3. Quantitative Evidence Additions

### 3.1 Named quantitative sub-patterns with distractor trap controls

**Gap source:** Coverage audit §5 "Expand Quantitative Evidence Patterns."
The current v1 `data_completes_example`, `data_comparison`, and `data_trend`
focus keys exist but do not specify the distractor traps for the sub-patterns
confirmed across PT6–PT11. Official items include at least seven distinct
quantitative construction patterns that require separate distractor
engineering.

**Add to §13.2 Command of Evidence — Quantitative, Focus disambiguation
section:**

Extend the three-case rule to cover all confirmed sub-patterns:

| Pattern | `reading_focus_key` | When to use | Primary distractor trap |
|---|---|---|---|
| Single absolute value from a table | `data_completes_example` | Correct option cites one specific cell value | `wrong_row_or_column` — option cites an adjacent cell |
| Comparing two or more values | `data_comparison` | Correct option requires comparing groups, conditions, or time points | `single_sector_focus` — option states one value without comparison |
| Directional trend in a graph | `data_trend` | Correct option identifies a direction (increasing, decreasing, stable) | `direction_reversal` — option states the opposite trend |
| Supports or weakens a claim | `data_supports_claim` / `data_weakens_claim` | Correct option is chosen because of its logical relationship to a passage claim | `data_context_mismatch` — option has accurate data but answers the wrong question |
| Exact lookup constrained by a row or column identifier | `data_completes_example` (with `exact_value_lookup` sub-pattern note) | Correct option requires finding a specific cell identified by two coordinates (row ID + column ID) | `wrong_table_row_or_column` — option uses the right column but wrong row, or right row but wrong column |
| Timing-constrained comparison | `data_comparison` (with `timing_constrained` sub-pattern note) | Correct option must use only data from a specified time window; other windows are excluded by the passage's claim | `wrong_time_window` — option uses real data from a different time window than the passage's constraint |
| All-measures comparison across groups | `data_comparison` (with `all_measures` sub-pattern note) | Correct option requires checking every row or column and confirming the comparison holds across all of them | `single_measure_focus` — option is true for one measure but not all |
| Highest value across all time periods | `data_comparison` (with `repeated_highest` sub-pattern note) | Correct option identifies a value that is highest not just at one time point but consistently | `local_maximum_trap` — option cites a locally high value that is not globally highest |
| Two-variable opposite trend | `data_trend` (with `two_variable_opposite` sub-pattern note) | Correct option identifies that two tracked variables move in opposite directions | `same_direction_assumption` — option incorrectly describes both variables moving the same way |
| Composition change over time | `data_trend` (with `composition_change` sub-pattern note) | Correct option identifies a change in relative proportions (percentages) not just absolute values | `absolute_value_confusion` — option correctly describes an absolute change but ignores the proportional shift |
| Binned distribution inference limit | `data_comparison` (with `binned_distribution` sub-pattern note) | Correct option uses only aggregate-level claims; individual-level inference is not supported by the graphic | `individual_from_aggregate` — option infers individual-level information from a distribution that only shows aggregates |

**Add to classification schema for all quantitative items:**

```json
{
  "quantitative_sub_pattern": "exact_value_lookup"
}
```

This field is optional for annotation of legacy items but required for
generation profiles.

Approved `quantitative_sub_pattern` values:
- `standard` (default; no sub-pattern constraint needed)
- `exact_value_lookup`
- `timing_constrained`
- `all_measures`
- `repeated_highest`
- `two_variable_opposite`
- `composition_change`
- `binned_distribution`

---

### 3.2 Add quantitative-specific reasoning trap keys

**Add to §10.1 Information and Ideas reasoning trap keys:**

- `wrong_row_or_column` — quantitative; option uses the correct table but
  cites the wrong row or column identifier
- `wrong_time_window` — quantitative; option uses real data that is accurate
  for a different time period than the one the passage's constraint specifies
- `all_measures_not_checked` — quantitative; option is true for one measure
  or one time point but the passage claim requires the comparison to hold
  across all measures or all periods
- `individual_from_aggregate` — quantitative; option infers individual-level
  information from a binned or aggregated graphic that only supports
  group-level claims
- `direction_reversal` — quantitative; option correctly identifies the
  variable being tracked but states the opposite direction of change

---

### 3.3 Add quantitative-specific student failure mode keys

**Add to §19 reading-specific `student_failure_mode_key` values:**

- `exact_value_misread` — student selects the value from an adjacent row or
  column rather than the cell specified by the two-coordinate constraint
- `wrong_time_window` — student selects data from the correct variable but
  the wrong time period, ignoring a stated temporal constraint
- `individual_from_aggregate` — student treats a binned distribution as if
  individual data points are recoverable from aggregate bars or slices
- `all_measures_not_checked` — student confirms the comparison for one row
  or column without checking that it holds for all rows or columns as
  required by the claim

---

## 4. Passage Architecture Additions

### 4.1 Add five experimental passage architectures

**Gap source:** Coverage audit §3 "Add Experimental-Control Architecture."
PT4–PT11 repeatedly produce support, weaken, inference, and quantitative items
that require the student to reason about hypotheses, controls, outcomes,
indirect effects, alternative explanations, and mechanism tests. The current
v1 §15.2 does not include architectures for these constructions.

**Add to §15.2 Passage structure patterns:**

- `experiment_hypothesis_control_result` — passage states a hypothesis,
  describes an experimental group, names a control condition or comparison
  baseline, states a predicted direction, and reports an observed outcome.
  Enables CoE-Textual support/weaken items and inference items that require
  distinguishing the experimental group from the control.

  Required elements:
  - Named hypothesis or research question
  - At least one experimental group with a described condition
  - Control group or comparison baseline
  - Predicted direction of effect
  - Observed outcome

- `indirect_effect_mediation` — passage describes an initial attitude,
  condition, or input; an intermediate variable that is affected by the input;
  and a final behavior or outcome, with the claim that the effect operates
  through the intermediate variable rather than directly.

  Required elements:
  - Initial condition or input
  - Intermediate variable (the mediator)
  - Final outcome
  - Explicit claim linking the effect to the mediator

- `alternative_explanation_ruled_out` — passage describes an observed change,
  names a possible alternative cause, presents a control or finding that
  eliminates the alternative cause, and states the remaining explanation.

  Required elements:
  - Observed change or pattern
  - Named alternative cause
  - Control or additional finding that removes the alternative
  - Remaining explanation

- `mechanism_manipulation_test` — passage describes a phenomenon, proposes a
  candidate mechanism, describes an experimental replacement or manipulation
  of one component, states the predicted result if the mechanism is causal,
  and reports the observed result.

  Required elements:
  - Observed phenomenon
  - Candidate mechanism
  - Component that was replaced or manipulated
  - Predicted result if mechanism is causal
  - Observed result of the manipulation

- `studied_subgroup_generalization_limit` — passage presents evidence
  concentrated in a well-studied subgroup and either explicitly warns or
  implicitly implies that the evidence may not generalize to the broader
  population or category.

  Required elements:
  - Broad population or category
  - Well-studied subgroup within that population
  - Evidence limited to the subgroup
  - Explicit or implicit scope limitation

**Generation note for all five architectures:**

When generating items on these architectures:
- For CoE Textual support/weaken: the correct option must address the
  specific causal mechanism, control condition, or scope limitation, not
  merely the general topic
- For Inferences: the correct completion must follow from the outcome,
  the mediation result, or the scope warning — not from an extrapolation
  beyond the described evidence
- Primary distractor trap for experimental architectures:
  `topical_relevance_without_logical_connection` — option mentions the
  study's subject but addresses the wrong group, the wrong variable, or
  the wrong direction

---

## 5. Inference Additions

### 5.1 Add `study_design_isolation_limit` inference pattern

**Gap source:** PT6 M2 Q18 (cannot isolate effect of one creative condition),
PT10 M2 Q17 (study design cannot distinguish simpler vs harder task outcomes).
Both items require the student to infer that the study's design prevents
isolating the causal contribution of one variable.

**Add to §13.4 Inferences — Evidentiary standard annotation:**

> Inference items may require identifying what a study *cannot* conclude
> based on its design, not only what it can conclude. When the passage
> describes a study where two conditions co-vary or where a control
> comparison is absent, the logically required inference may be a
> limitation: "the researchers cannot determine whether X or Y caused
> the result." Annotate these items with `reading_focus_key:
> "implication_inference"` and add to `review_notes`:
> "inference_type: study_design_isolation_limit."

**Generation note:**

```
Target: study_design_isolation_limit

Construct a passage where a study manipulates two things simultaneously
or lacks a comparison condition needed to isolate one variable. The blank
requires the student to infer that the design prevents attribution to
either variable alone.

Correct option: states that the researchers cannot determine which of
  the two co-varying factors was responsible.
Wrong options:
  - attributes the result to one factor specifically (overreach)
  - concludes no effect exists (contradiction)
  - suggests the study was flawed for unrelated reasons (outside_knowledge)
```

---

### 5.2 Add `subgroup_overgeneralization` inference pattern

**Gap source:** PT11 M1 Q18 (bumblebee evidence may not generalize to all
wild bees). Coverage audit confirms: `scope_extension` trap exists but no
named generation pattern for the specific case where evidence from one
well-studied subgroup tempts the student to draw a conclusion about the
broader category.

**Add to §13.4 Inferences — Evidentiary standard annotation:**

> Inference items built on `studied_subgroup_generalization_limit`
> architecture require the student to recognize that evidence from one
> subgroup does not automatically support a claim about the broader
> category. The correct inference either applies only to the subgroup
> or explicitly notes the limitation. Annotate these items with
> `reading_focus_key: "implication_inference"` and add to `review_notes`:
> "inference_type: subgroup_overgeneralization_limit."

**Generation note:**

```
Target: subgroup_overgeneralization_limit

Construct a passage that presents evidence about a named subgroup and
includes a warning (explicit or implicit) that the subgroup may not
represent the broader population.

Correct option: applies the conclusion only to the subgroup, or states
  that the broader conclusion cannot be drawn from the subgroup evidence.
Primary wrong trap: scope_extension — option extrapolates from the
  subgroup to the broader population without qualification.
Secondary wrong trap: overreach — option states a stronger causal
  claim than the evidence supports even within the subgroup.
```

**Add `subgroup_overgeneralization` to §19 student failure mode keys:**

- `subgroup_overgeneralization` — student extrapolates from evidence about
  a studied subgroup to the broader population or category, ignoring a
  passage warning about generalization limits

---

### 5.3 Annotation requirement for mechanism-test inference items

**Gap source:** PT10 M1 Q19 (ELF3 replacement and flowering at high
temperature — mechanism manipulation test architecture).

**Add to §13.4 Inferences:**

> When the passage uses the `mechanism_manipulation_test` architecture,
> inference items typically require the student to identify what the
> manipulation result reveals about the candidate mechanism. Annotate
> these items with `reading_focus_key: "causal_inference"` and add to
> `review_notes`: "inference_type: mechanism_manipulation_test — correct
> answer must follow from the observed manipulation result, not from the
> general topic."

---

## 6. Command of Evidence — Textual Additions

### 6.1 Two-part claim annotation requirement for quote-illustration items

**Gap source:** PT6 M2 Q12 (quotation must illustrate a two-part claim — both
elements required). Coverage audit: "`partial_match` trap covered" but no
explicit generation rule requiring two-part claim construction.

**Add to §13.1 Command of Evidence — Textual, mandatory reasoning check:**

> For `evidence_illustrates_claim` items (literary quotation variants), the
> claim in the stem may have two required elements (e.g., both "X" and "Y").
> When annotating or generating such an item:
>
> 1. Annotate `evidence_span_text` with the full claim, marking both elements.
> 2. For every distractor, check whether it satisfies one element but not
>    both. If so, annotate `distractor_type_key: "partial_match"` and
>    `why_wrong`: "satisfies [element A] but not [element B]."
> 3. For generation: explicitly construct the claim with two required elements
>    and ensure at least one distractor satisfies exactly one of the two.

**Add `two_part_claim_partial_match` to §19 student failure mode keys:**

- `two_part_claim_partial_match` — student selects a quotation that addresses
  one part of a two-element claim while ignoring the second required element

---

### 6.2 Control-group and alternative-cause distractor patterns

**Gap source:** PT4 M2 Q18 (inference about control group design), PT6 M2 Q11
(unchanged composition rules out alternative cause). Coverage audit: "add
control-of-alternative-explanation pattern."

**Add to §13.1 Command of Evidence — Textual:**

> For items on `alternative_explanation_ruled_out` or
> `experiment_hypothesis_control_result` passage architectures, the most
> common distractor trap is `topical_relevance_without_logical_connection`:
> the wrong option addresses the same general topic (the experiment) but
> does not specifically engage with the alternative cause being ruled out
> or the control condition being tested. Annotate with
> `reasoning_trap_key: "topical_relevance_without_logical_connection"` and
> document in `why_wrong` which part of the causal logic the option fails
> to address.

**Add `control_group_misidentification` to §19 student failure mode keys:**

- `control_group_misidentification` — student selects evidence from the
  experimental group when the question requires evidence from the control
  group, or vice versa

---

## 7. Cross-Text Connections Additions

### 7.1 Qualified-disagreement pattern generation note

**Gap source:** PT4 M1 Q9, PT6 M1 Q9. Coverage audit: "confirmed
disagreement-oriented response rule" and "confirmed qualified-disagreement
response rule." Both are already in v1, but v1 does not include a generation
note specifying how to construct a `confirmation_with_qualification` item
that still passes the response-stem rule.

**Add to §16.5 Cross-Text Connections generation constraints:**

> For `confirmation_with_qualification` items:
> - Text 2 must explicitly concede one element of Text 1's claim
>   (e.g., "this approach has merit in limited conditions")
> - Text 2 must then qualify or restrict the claim
>   (e.g., "but it cannot explain the broader pattern")
> - The correct response option must capture both the concession and the
>   restriction, not just one
> - Wrong options include: (a) full agreement (no qualification), (b) full
>   rejection (ignores the concession), (c) methodological critique (wrong
>   relationship type), (d) correct concession but wrong restriction
> - This item type is harder than `direct_contradiction` and should be
>   calibrated at `difficulty_overall: "high"` unless the concession
>   and restriction are both stated in single sentences

---

## 8. Additional Student Failure Mode Keys

**Add to §19 reading-specific `student_failure_mode_key` values:**

- `parenthetical_function_confusion` — in sentence-function items, student
  selects an option that correctly describes the broader passage purpose
  rather than the local clarifying function of a parenthetical phrase
- `polarity_blindness` — synonym for `negation_blindness`; student applies
  the correct meaning of a word to the blank without accounting for a
  negator or concessive construction that inverts the required polarity
- `connotation_surface_match` — in WIC items, student selects a word whose
  common dictionary meaning matches the topic but whose connotation
  (evaluative, emotional, or tonal charge) mismatches the passage's stance
- `rhetorical_verb_partial` — in text-structure items, student selects an
  option whose content description is accurate but whose action verb is wrong
  (e.g., "to introduce" when the function is "to challenge")
- `evidence_scope_mismatch` — student selects evidence that is logically
  related to the claim but applies to a different variable, population, or
  direction than the one specified in the claim
- `wrong_comparison_direction` — student selects data that supports the
  opposite comparison (e.g., lowest when highest is required, or the smaller
  group when the larger is required)

---

## 9. Reading Focus Key List Updates

### 9.1 Updated §7.5 Words in Context focus keys (complete replacement)

Replace the §7.5 list in v1 with this complete list:

- `contextual_meaning` — correct word determined by surrounding sentence context
- `connotation_fit` — near-synonyms; correct word determined by evaluative or emotional register
- `precision_fit` — correct word is the most specific among near-synonyms
- `register_fit` — correct word matches the academic, formal, or technical register
- `underlined_word_meaning` — "most nearly mean" stem; word is underlined
- `polarity_fit` *(new in v1.1)* — correct word must preserve logical polarity when a negator or concessive is present

---

## 10. Reasoning Trap Key List Updates

### 10.1 Updated §10.1 Information and Ideas trap keys (additions only)

Add to the existing list:

- `wrong_row_or_column` *(new in v1.1)*
- `wrong_time_window` *(new in v1.1)*
- `all_measures_not_checked` *(new in v1.1)*
- `individual_from_aggregate` *(new in v1.1)*
- `direction_reversal` *(new in v1.1)*

### 10.2 Updated §10.2 Craft and Structure trap keys (additions only)

Add to the existing list:

- `polarity_mismatch` *(new in v1.1)*

---

## 11. Validator Checklist Additions

Add to §20 Validator Checklist:

- [ ] For WIC items with a negator or concessive in the passage,
      `reading_focus_key` is `polarity_fit` and `evidence_span_text`
      includes the full negated construction
- [ ] For `evidence_illustrates_claim` items where the stem claim has
      two required elements, at least one distractor is annotated with
      `distractor_type_key: "partial_match"` and `why_wrong` names both
      elements
- [ ] For `sentence_function` items, `review_notes` includes the
      `target_sentence_function_role` from the approved list in §2.1
- [ ] For quantitative items using a constrained lookup, the
      `quantitative_sub_pattern` field is populated with the appropriate
      sub-pattern value
- [ ] For quantitative items where `quantitative_sub_pattern` is
      `timing_constrained`, at least one distractor is annotated with
      `distractor_type_key` corresponding to `wrong_time_window`
- [ ] For quantitative items where `quantitative_sub_pattern` is
      `binned_distribution`, no distractor or correct option infers
      individual-level information from the aggregate graphic
- [ ] For inference items on `studied_subgroup_generalization_limit`
      architecture, `review_notes` includes
      "inference_type: subgroup_overgeneralization_limit"
- [ ] For inference items on `mechanism_manipulation_test` architecture,
      `review_notes` includes
      "inference_type: mechanism_manipulation_test"
- [ ] For items on `experiment_hypothesis_control_result` architecture,
      the correct option addresses the specific group (experimental or
      control) named in the claim, not the general topic

---

## 12. Generation Profile Extension

For reading generation profiles, add these optional fields that are
mandatory when the corresponding condition applies:

```json
{
  "generation_profile": {
    "target_skill_family_key": "words_in_context",
    "target_reading_focus_key": "polarity_fit",
    "polarity_context": "negator: 'by no means'",
    "target_sentence_function_role": null,
    "quantitative_sub_pattern": null,
    "passage_architecture_key": "studied_subgroup_generalization_limit",
    "inference_type_note": "subgroup_overgeneralization_limit",
    "two_part_claim": false
  }
}
```

| Field | Mandatory when |
|---|---|
| `polarity_context` | `target_reading_focus_key` is `polarity_fit` |
| `target_sentence_function_role` | `target_reading_focus_key` is `sentence_function` |
| `quantitative_sub_pattern` | `target_skill_family_key` is `command_of_evidence_quantitative` |
| `passage_architecture_key` | passage uses one of the five experimental architectures |
| `inference_type_note` | passage architecture is `mechanism_manipulation_test` or `studied_subgroup_generalization_limit` |
| `two_part_claim` | `target_reading_focus_key` is `evidence_illustrates_claim` |

---

*Document version: v1.1 — 2026-04-29*
*Addendum to: `rules_agent_dsat_reading_v1.md`*
*Source authority: `CB_ANSWERS_QUESTIONS_ANALYSIS.md` (PT4–PT11 official explanation cross-reference)*
*Domain coverage: Information and Ideas, Craft and Structure*
