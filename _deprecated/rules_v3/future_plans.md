# Future Plans: Batch Generation and Automated Validation

This file describes the next production layer for using `rules_v2/` to generate
large realistic DSAT question sets with GPT-5.5, Claude, or another strong LLM.
It is planning guidance, not an active rule contract.

## Goal

Enable reliable generation of a 100-question DSAT Reading and Writing question
set while preserving:

- realistic SAT style
- controlled taxonomy keys
- balanced domain coverage
- difficulty targeting
- topic diversity
- answer-position distribution
- validator-safe JSON output

The recommended production pattern is not one 100-question prompt. Generate in
small batches, validate each batch, repair failed items, then continue.

## Recommended 100-Question Blueprint

Default domain mix:

| Domain area | Count |
|---|---:|
| Standard English Conventions | 35 |
| Expression of Ideas | 20 |
| Information and Ideas | 25 |
| Craft and Structure | 20 |
| Total | 100 |

Default difficulty mix:

| Difficulty | Count |
|---|---:|
| low | 20 |
| medium | 55 |
| high | 25 |

Default reading-specific quotas:

| Skill area | Count |
|---|---:|
| Command of Evidence, Textual | 6 |
| Command of Evidence, Quantitative | 4 |
| Central Ideas and Details | 5 |
| Inferences | 5 |
| Words in Context | 6 |
| Text Structure and Purpose | 8 |
| Cross-Text Connections | 6 |

Default grammar and Expression of Ideas quotas:

| Focus area | Count |
|---|---:|
| punctuation and sentence boundaries | 14 |
| agreement | 7 |
| verb form and tense | 6 |
| modifiers and logical predication | 5 |
| pronouns | 3 |
| parallel structure | 3 |
| transitions | 8 |
| concision, precision, register, synthesis, data claims | 9 |

These are starting targets. A production scheduler should allow overrides for a
specific course, diagnostic, or weak-skill remediation set.

## Batch Size

Generate 5-10 questions per batch.

Use smaller batches when:

- generating high-difficulty items
- generating Cross-Text items
- generating Quantitative CoE items
- changing domains
- testing a new prompt or model

Use larger batches only after validation pass rates are stable.

## Batch Generation Request Shape

Each batch request should include:

```json
{
  "batch_generation_request": {
    "batch_id": "set_001_batch_03",
    "target_count": 8,
    "active_rules": [
      "rules_core_generation.md",
      "rules_dsat_grammar_module.md"
    ],
    "domain": "grammar",
    "question_family_mix": {
      "conventions_grammar": 5,
      "expression_of_ideas": 3
    },
    "difficulty_mix": {
      "low": 1,
      "medium": 5,
      "high": 2
    },
    "target_focus_keys": [
      "subject_verb_agreement",
      "punctuation_comma",
      "transition_logic"
    ],
    "topic_broad_rotation": [
      "science",
      "history",
      "arts",
      "technology"
    ],
    "avoid_recent_exam_ids": ["PT4", "PT5", "PT6"],
    "answer_position_targets": {
      "A": 2,
      "B": 2,
      "C": 2,
      "D": 2
    },
    "special_quotas": {
      "no_change_items": 1,
      "quantitative_items": 0,
      "cross_text_items": 0
    }
  }
}
```

The model should output one complete item object per question, not prose
summaries. Failed items should return the structured error object from
`rules_core_generation.md`.

## Rotation Rules

For a 100-question set:

- No two consecutive questions should share the same `topic_broad`.
- No two questions within a 5-item window should share the same `topic_fine`.
- No three consecutive questions should use the same domain area.
- No focus key should appear more than twice in a 10-item window unless the
  batch explicitly targets remediation.
- Correct answer positions should stay between 20% and 30% each over the full
  set.
- No individual 10-question batch should put more than 4 correct answers in the
  same position.

## Special Quotas

Recommended minimums per 100-question set:

- 8-12 no-change grammar items
- 4-6 quantitative evidence items
- 5-8 Cross-Text items
- 8-12 Words in Context items
- 8-12 transition or rhetorical relationship items
- 10+ high-competition distractor sets where all three wrong answers are
  plausible

Recommended maximums:

- no more than 15 no-change items
- no more than 8 quantitative items unless the set is data-focused
- no more than 10 Cross-Text items unless the set is reading-heavy
- no more than 3 `very_low` frequency grammar focus items unless explicitly
  requested

## Section 1 Module Blueprints

This section defines a realistic full Reading and Writing Section 1 blueprint:

- `sec01_mod01`: standard first module
- `sec01_mod02`: adaptive second module

Digital SAT Reading and Writing modules should default to 27 questions unless
the active practice-exam stats source says otherwise.

Module blueprints must be data-driven. The fallback defaults below are only used
when updated practice-exam stats are unavailable or incomplete.

### Practice-Exam Stats Source

The generator should accept an external stats snapshot derived from the
canonical official verbal practice-test PDFs and/or approved explanations.

Canonical local source:

```text
TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/
```

Stats should be recomputed whenever new official or high-confidence practice
exam data is ingested.

Recommended stats snapshot shape:

```json
{
  "practice_exam_stats_snapshot": {
    "snapshot_id": "official_verbal_2026_04_27",
    "source_paths": [
      "TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/"
    ],
    "included_exam_codes": ["PT1", "PT4", "PT5", "PT6", "PT7", "PT8", "PT9", "PT10", "PT11"],
    "module_length": {
      "sec01_mod01": 27,
      "sec01_mod02": 27
    },
    "distributions": {
      "sec01_mod01": {
        "question_family_counts": {},
        "skill_family_counts": {},
        "focus_key_counts": {},
        "difficulty_counts": {},
        "position_band_counts": {},
        "answer_position_counts": {}
      },
      "sec01_mod02": {
        "question_family_counts": {},
        "skill_family_counts": {},
        "focus_key_counts": {},
        "difficulty_counts_by_route": {
          "higher": {},
          "lower": {}
        },
        "position_band_counts": {},
        "answer_position_counts": {}
      }
    },
    "sample_size_modules": {
      "sec01_mod01": 9,
      "sec01_mod02": 9
    },
    "generated_at": "ISO-8601 timestamp"
  }
}
```

The scheduler should use the stats snapshot first, then apply fallback defaults
only for missing fields.

Stats application rules:

- If `sample_size_modules >= 6`, use the observed distribution as the primary
  target.
- If `sample_size_modules < 6`, blend observed stats with fallback defaults.
- Round counts so each module sums to 27.
- Preserve minimum coverage for rare official item types such as Quantitative
  CoE and Cross-Text when they appear in the stats.
- Do not force an item type into a module if the active stats source shows it is
  absent for that module and route.
- Store the stats snapshot ID in every generated module record.

### Position Bands

Use position bands to preserve module feel:

| Band | Question range | Purpose |
|---|---:|---|
| opening_precision | 1-4 | vocabulary, concise word choice, quick precision |
| early_reading | 5-10 | evidence, central ideas, details, low/medium inference |
| mid_reading | 11-15 | purpose, structure, cross-text, harder inference |
| conventions_core | 16-22 | SEC grammar and punctuation |
| expression_finish | 23-27 | transitions, synthesis, concision, rhetorical goals |

If updated practice-exam stats show a different position distribution, use the
observed distribution but keep the band labels for validator reporting.

### Fallback Blueprint: `sec01_mod01`

Use this only when practice-exam stats are unavailable.

```json
{
  "module_blueprint": {
    "section_code": "sec01",
    "module_code": "mod01",
    "module_length": 27,
    "module_role": "standard_first_module",
    "stats_source": "fallback_defaults",
    "difficulty_ramp": "clustered_progressive",
    "question_family_counts": {
      "information_and_ideas": 8,
      "craft_and_structure": 7,
      "conventions_grammar": 7,
      "expression_of_ideas": 5
    },
    "skill_family_counts": {
      "command_of_evidence_textual": 2,
      "command_of_evidence_quantitative": 1,
      "central_ideas_and_details": 3,
      "inferences": 2,
      "words_in_context": 4,
      "text_structure_and_purpose": 2,
      "cross_text_connections": 1
    },
    "difficulty_counts": {
      "low": 8,
      "medium": 15,
      "high": 4
    },
    "answer_position_targets": {
      "A": 7,
      "B": 7,
      "C": 7,
      "D": 6
    }
  }
}
```

Recommended position slots:

| Range | Target item types | Difficulty tendency |
|---|---|---|
| Q1-Q4 | Words in Context / precision | low to medium |
| Q5-Q10 | CoE, central ideas, details, inference | low to medium |
| Q11-Q15 | purpose, structure, cross-text, harder inference | medium |
| Q16-Q22 | SEC grammar and punctuation | medium, with 1-2 high |
| Q23-Q27 | transitions, synthesis, concision, rhetorical goals | medium to high |

### Fallback Blueprint: `sec01_mod02` Higher Route

Use this for a hard adaptive second module when practice-exam stats are
unavailable.

```json
{
  "module_blueprint": {
    "section_code": "sec01",
    "module_code": "mod02",
    "module_role": "adaptive_second_module_higher",
    "module_length": 27,
    "stats_source": "fallback_defaults",
    "difficulty_ramp": "clustered_progressive",
    "question_family_counts": {
      "information_and_ideas": 9,
      "craft_and_structure": 7,
      "conventions_grammar": 6,
      "expression_of_ideas": 5
    },
    "skill_family_counts": {
      "command_of_evidence_textual": 3,
      "command_of_evidence_quantitative": 1,
      "central_ideas_and_details": 3,
      "inferences": 2,
      "words_in_context": 4,
      "text_structure_and_purpose": 2,
      "cross_text_connections": 1
    },
    "difficulty_counts": {
      "low": 3,
      "medium": 12,
      "high": 12
    },
    "answer_position_targets": {
      "A": 7,
      "B": 6,
      "C": 7,
      "D": 7
    }
  }
}
```

Higher-route generation should increase:

- distractor competition
- evidence precision
- scope and attribution traps
- grammar trap depth
- fatigue pressure in Q20-Q27

It must not increase:

- ambiguity
- outside knowledge dependence
- artificial wording
- multiple defensible correct answers

### Fallback Blueprint: `sec01_mod02` Lower Route

Use this when generating a lower adaptive second module, or when a practice set
needs an easier Module 2 variant.

```json
{
  "module_blueprint": {
    "section_code": "sec01",
    "module_code": "mod02",
    "module_role": "adaptive_second_module_lower",
    "module_length": 27,
    "stats_source": "fallback_defaults",
    "difficulty_ramp": "gentle_progressive",
    "question_family_counts": {
      "information_and_ideas": 8,
      "craft_and_structure": 7,
      "conventions_grammar": 7,
      "expression_of_ideas": 5
    },
    "difficulty_counts": {
      "low": 12,
      "medium": 12,
      "high": 3
    },
    "answer_position_targets": {
      "A": 7,
      "B": 7,
      "C": 6,
      "D": 7
    }
  }
}
```

Lower-route generation should keep the same official-feeling skill mix while
reducing passage density, inference distance, and distractor tightness.

### Stats-Driven Module Request

When updated stats are available, the batch scheduler should emit a module
request like this:

```json
{
  "module_generation_request": {
    "exam_code": "GENERATED",
    "section_code": "sec01",
    "module_code": "mod01",
    "module_length": 27,
    "module_role": "standard_first_module",
    "rules": [
      "rules_core_generation.md",
      "rules_dsat_grammar_module.md",
      "rules_dsat_reading_module.md"
    ],
    "stats_source": {
      "mode": "practice_exam_stats_snapshot",
      "snapshot_id": "official_verbal_2026_04_27",
      "fallback_policy": "fill_missing_fields_from_defaults"
    },
    "target_distribution": {
      "question_family_counts": "from_stats",
      "skill_family_counts": "from_stats",
      "focus_key_counts": "from_stats",
      "difficulty_counts": "from_stats",
      "position_band_counts": "from_stats",
      "answer_position_targets": "balanced_from_stats"
    },
    "constraints": {
      "max_same_question_family_streak": 3,
      "min_distinct_question_families_per_8_item_window": 3,
      "max_same_answer_streak": 3,
      "topic_broad_no_repeat_window": 2,
      "topic_fine_no_repeat_window": 5
    }
  }
}
```

### Module-Level Validator Additions

For `sec01_mod01` and `sec01_mod02`, add these checks to Pass 7:

- module has exactly 27 questions unless stats specify otherwise
- module uses the active stats snapshot or records fallback use
- generated counts match stats-derived targets within tolerance
- each position band has the expected dominant item types
- difficulty ramp is plausible for the module role
- Module 2 route is declared as `higher` or `lower` when adaptive behavior is
  being simulated
- answer-position distribution has no visible streak or imbalance
- no item family overclusters beyond the allowed window
- late-module difficulty increases precision pressure without reducing fairness
- module release sets `module_release_ready: false` if any distribution check
  fails

Suggested tolerance:

```json
{
  "module_distribution_tolerance": {
    "question_family_counts": 1,
    "skill_family_counts": 1,
    "difficulty_counts": 2,
    "answer_position_counts": 2,
    "position_band_counts": 1
  }
}
```

## Automated Validator Pass

The validator should run after every generated batch and before any item is
accepted into a persistent question bank.

### Pass 1: JSON Shape

Check:

- valid JSON
- required top-level sections exist
- exactly four options
- labels A-D present exactly once
- exactly one correct option
- required explanation and review fields present

Reject on failure.

### Pass 2: Domain Contract

Check:

- one active domain module per item
- grammar items do not emit reading-only taxonomy keys
- reading items have null or omitted grammar keys
- `question_family_key` matches the selected module
- `stem_type_key` is legal for the selected domain
- `stimulus_mode_key` is legal for the selected skill

Reject or reroute on failure.

### Pass 3: Controlled Keys

Check every controlled field against the active module:

- grammar role/focus mapping
- reading skill/focus mapping
- trap keys
- answer mechanism keys
- solver pattern keys
- distractor type keys
- plausibility source keys
- tense/register keys
- passage architecture keys

Reject or request repair on failure. Do not silently accept unknown keys.

### Pass 4: Required Domain Fields

Grammar checks:

- no-change metadata when original text is an option
- tense/register metadata for verb-form items
- `secondary_grammar_focus_keys` when secondary rules are visible
- `option_error_focus_key` for each grammar distractor
- generation profile includes role, focus, trap, frequency, template, timestamp,
  and model version

Reading checks:

- Cross-Text items include `paired_passage_text`
- Quantitative CoE items include `table_data` or `graph_data`
- `evidence_span_text` anchors the correct answer
- grammar keys are null or omitted
- skill/focus/stem/mode combination is legal

Reject or repair on failure.

### Pass 5: SAT Realism

Check:

- distractors are homogeneous in category, length band, register, and form
- no answer is visibly correct by length, specificity, or polish
- each distractor has `why_plausible` and `why_wrong`
- each distractor has a named failure mode
- distractor competition score meets the requested difficulty
- no distractor contains an accidental second error
- correct answer is not merely the only moderate or nuanced option

Flag for repair if realism fails.

### Pass 6: Difficulty and Targeting

Check:

- generated difficulty matches request
- `difficulty_overall` is justified by trap intensity, evidence complexity, or
  distractor competition
- grammar items with `target_syntactic_trap_key: "none"` are not high difficulty
  unless explicitly justified
- topic matches request
- focus key matches request
- no unintended second skill dominates the item

Flag for repair if targeting fails.

### Pass 7: Set-Level Distribution

Across the accumulated set, check:

- domain counts
- skill/focus counts
- difficulty counts
- answer-position distribution
- topic rotation
- no-change quota
- Cross-Text quota
- Quantitative quota
- repeated passage templates
- structural similarity against recent generated items and official exemplars

If distribution drifts, adjust the next batch request rather than rewriting
accepted items.

## Repair Loop

For each failed item:

1. Report validator failures as structured JSON.
2. Ask the model to repair only the failed fields or component.
3. Preserve accepted fields when possible.
4. Re-run all validator passes.
5. Allow at most three repair attempts.
6. After three failures, discard the item and request a replacement targeting
   the same slot in the blueprint.

Repair prompt shape:

```json
{
  "repair_request": {
    "item_id": "set_001_batch_03_item_04",
    "active_rules": [
      "rules_core_generation.md",
      "rules_dsat_reading_module.md"
    ],
    "failed_checks": [
      {
        "pass": "domain_fields",
        "field": "paired_passage_text",
        "message": "Cross-Text item requires Text 2."
      }
    ],
    "repair_scope": "failed_fields_only",
    "preserve": [
      "question_family_key",
      "skill_family_key",
      "reading_focus_key",
      "topic_broad",
      "difficulty_overall"
    ]
  }
}
```

## Suggested Implementation Path

1. Create a deterministic Python validator that reads the rule key lists from
   structured data files or constants.
2. Add a batch scheduler that maintains the 100-question blueprint and produces
   one batch request at a time.
3. Store every generated item with validator results and model metadata.
4. Run a second-model review pass on accepted items for SAT realism and
   ambiguity.
5. Only then export accepted questions to the production question bank.

## Open Design Decisions

- Whether key lists should remain in markdown only or be duplicated into JSON
  schemas for strict validation.
- Whether high-difficulty generation should require retrieval of nearest
  official exemplars before writing.
- Whether no-change answer position should remain fixed at A for compatibility
  or be randomized after ground-truth parity is confirmed.
- Whether the validator should automatically reroute ambiguous
  Expression-of-Ideas items between grammar and reading modules.
