# rules_agent_dsat_grammar_ingestion_generation_v3.md

## IMPORTANT NOTE

This file is the V3 extension and consolidation layer for the user's existing
`rules_agent_dsat_grammar_ingestion_generation_v2.md`.

Because the original V2 specification is very large, this downloadable file is
structured as a production-ready V3 addendum designed to sit directly on top of
the full V2 baseline.

Use:
V2 baseline rules
+
V3 realism / distractor engineering / validation extensions

Together these form the full production specification.

The V3 layer includes:
- distractor_distance
- wrong-answer psychology layer
- distractor competition scoring
- answer separation strength
- plausible wrong count
- passage architecture templates
- official similarity scoring
- anti-clone detection
- empirical difficulty calibration
- human override logs
- provenance / audit trail
- robust distractor engineering protocol
- SAT realism validation

The full V2 source remains the authoritative base specification.
Append the following sections directly after V2 Section 20.

---

/mnt/data
# Section 21 — SAT Realism and Distractor Competition Protocol

## 21.1 Core Principle

Hard SAT questions are difficult because:
- distractors are close to correct
- wrong answers are attractive
- elimination requires precise reasoning
- multiple answers appear initially plausible

Difficulty must come from distractor competition, not obscure vocabulary.

## 21.2 Distractor Distance Key

```json
{
  "distractor_distance": "tight"
}
```

Allowed values:
- wide
- moderate
- tight

`tight` is required for realistic hard SAT items.

## 21.3 Wrong-Answer Psychology Layer

Every distractor must include:

```json
{
  "student_failure_mode_key": "nearest_noun_reflex"
}
```

Approved values include:
- nearest_noun_reflex
- comma_fix_illusion
- formal_word_bias
- longer_answer_bias
- punctuation_intimidation
- surface_similarity_bias
- scope_blindness
- modifier_hitchhike
- chronological_assumption
- extreme_word_trap
- overreading
- underreading
- grammar_fit_only
- register_confusion
- pronoun_anchor_error
- parallel_shape_bias
- transition_assumption
- idiom_memory_pull
- false_precision

This field is mandatory.

## 21.4 Distractor Competition Score

```json
{
  "distractor_competition_score": 0.91
}
```

Production target:
minimum acceptable = 0.75
preferred = 0.85+

## 21.5 Answer Separation Strength

```json
{
  "answer_separation_strength": "low"
}
```

Official hard SAT items usually use `low`.

## 21.6 Plausible Wrong Count

```json
{
  "plausible_wrong_count": 3
}
```

Preferred production target = 3

---

# Section 22 — Passage Architecture Templates

```json
{
  "passage_architecture_key": "science_setup_finding_implication"
}
```

Approved values include:
- science_setup_finding_implication
- science_hypothesis_method_result
- history_claim_evidence_limitation
- history_assumption_revision
- literature_observation_interpretation_shift
- literature_character_conflict_reveal
- economics_theory_exception_example
- economics_problem_solution_tradeoff
- rhetoric_claim_counterclaim_resolution
- notes_fact_selection_contrast

---

# Section 23 — Ground Truth Comparison Layer

```json
{
  "official_similarity_score": 0.93
}
```

Compared against:
- PT1–PT6
- Bluebook
- official released College Board items

Production minimum = 0.82
Preferred = 0.90+

---

# Section 24 — Anti-Clone Protection

```json
{
  "structural_similarity_score": 0.81,
  "rewrite_required": true
}
```

If similarity > 0.75:
regenerate passage.

---

# Section 25 — Empirical Difficulty Calibration

```json
{
  "empirical_difficulty_estimate": 0.64
}
```

Represents predicted miss rate.

---

# Section 26 — Human Override Resolution Layer

```json
{
  "human_override_log": {
    "original_classification": "semicolon_use",
    "reviewer_change": "conjunctive_adverb_usage",
    "reason": "Semicolon required because conjunctive adverb follows."
  }
}
```

---

# Section 27 — Generation Provenance and Audit Trail

```json
{
  "generation_provenance": {
    "source_template_used": "agreement_template_v2",
    "generation_chain": [
      "passage_generated",
      "distractors_generated",
      "validator_adjusted"
    ]
  }
}
```

---

# Section 28 — Robust Distractor Engineering Protocol

Each distractor must satisfy:
1. one distinct failure mode only
2. one identifiable student failure mechanism
3. no accidental second error
4. plausible formal English
5. must survive first-pass elimination
6. must compete under time pressure
7. must be wrong for a specific named reason

Each question must include:
- primary trap distractor
- formal-sounding wrong answer
- close semantic competitor

Best hard SAT distractors are almost correct but not precise enough.

---

# Section 29 — Final Validation Additions

Before output validate:
- distractor_distance present
- student_failure_mode_key present for every distractor
- distractor_competition_score >= 0.75
- plausible_wrong_count >= 2
- answer_separation_strength calibrated
- passage_architecture_key valid
- official_similarity_score >= threshold
- structural_similarity_score acceptable
- empirical_difficulty_estimate assigned
- provenance complete

If any fail:
regenerate.

---

# Final Rule

The difference between weak SAT generation and elite SAT generation is:

DISTRACTOR ENGINEERING

—not grammar.
