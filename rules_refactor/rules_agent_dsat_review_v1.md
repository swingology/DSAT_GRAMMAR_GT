# DSAT Generated Question Review Rubric v1

## Purpose

This rubric defines the scoring dimensions, anchor bands, verdict logic, and strict JSON output schema for multi-model review of generated DSAT questions. Reviewers assess each generated question against official DSAT standards and return a structured JSON verdict.

**Version:** v1

**Companion rules:**
- Grammar v8 (`rules_agent_dsat_grammar_ingestion_generation_v8.md`) is loaded **always** as the prose style canon for all DSAT writing.
- Reading v2 (`rules_agent_dsat_reading_v2.md`) is loaded **additively** when the candidate is a reading question.

These companion rules provide the classification taxonomy, distractor construction heuristics, and difficulty calibration benchmarks that reviewers use to evaluate taxonomy match and fidelity.

---

## Scoring Dimensions (10 criteria → 7 numeric scores)

The reviewer assesses ten quality criteria, mapped to seven numeric score keys:

| Assessment criterion | JSON score key | Threshold | Notes |
|---|---|---|---|
| DSAT realism | `realism_score` | ≥7.0 | Could this pass as an official College Board question? |
| SAT style fidelity | `sat_fidelity_score` | ≥7.0 | Does it match SAT format, register, and conventions? |
| Target taxonomy match | `taxonomy_match_score` | ≥7.5 | Does it test the declared focus/skill at the right cognitive level? |
| Difficulty match | `difficulty_match_score` | (informational) | Does apparent difficulty match the requested difficulty band? No threshold gate. |
| Distractor quality + correct-answer defensibility | `distractor_quality_score` | ≥6.5 | Are distractors plausible, distinct, and well-targeted? Is the correct answer defensible? |
| Explanation quality + student-facing clarity | `explanation_quality_score` | (informational) | Is the explanation accurate, clear, and free of ambiguity? |
| Copy/near-duplicate risk | `copy_risk_score` | ≤5.0 (inverted) | Does the question copy or closely paraphrase source material? Higher = more risk. |

**Notes:**
- Grammar/reading rule compliance is folded into `taxonomy_match_score`. A question that violates its declared domain's classification rules loses taxonomy points.
- Correct-answer defensibility is folded into `distractor_quality_score`. A correct answer that is arguably wrong drags down distractor quality.
- Student-facing ambiguity risk is folded into `explanation_quality_score`. An explanation that could mislead a student loses explanation points.

---

## Score Definitions and Anchor Bands

Each score is on a 0–10 scale. Reviewers must assign a numeric score with one decimal place (e.g., 7.3, 8.5). Whole integers are also acceptable.

### realism_score — DSAT Realism

Could this question appear on an actual digital SAT without raising suspicion?

| Band | Description |
|---|---|
| 0–2 | Clearly AI-generated; robotic phrasing, unnatural register, or structural patterns foreign to SAT |
| 3–4 | Attempt at SAT style but noticeable departures: awkward transitions, vocabulary mismatch, or tone inconsistency |
| 5–6 | Plausible surface appearance but fails on closer inspection: passage logic gaps, option construction tells, or register shifts |
| 7–8 | Could pass for official; minor imperfections only detectable by expert review (e.g., slightly long passage, one distractor too easy) |
| 9–10 | Indistinguishable from official DSAT output; passage, stem, and options all meet College Board production quality |

### sat_fidelity_score — SAT Style Fidelity

Does the question follow SAT format conventions?

| Band | Description |
|---|---|
| 0–2 | Format violations: wrong number of options, missing labels, incorrect stem type, or non-SAT passage structure |
| 3–4 | Mostly correct format but one or two convention violations: option label format, stem phrasing pattern, or passage length deviation |
| 5–6 | Correct format but style drift: register too casual or too academic for SAT, transition usage inconsistent with SAT norms |
| 7–8 | Faithful SAT format with minor style imperfections (e.g., one option slightly too long, passage could be tighter) |
| 9–10 | Perfect SAT format, register, and conventions. Passage length, option structure, stem type, and difficulty distribution all match official norms |

### taxonomy_match_score — Target Taxonomy Match

Does the question test the declared grammar focus, reading skill family, or reading focus at the appropriate cognitive level?

| Band | Description |
|---|---|
| 0–2 | Tests a different skill entirely; declared focus key does not match what the question actually assesses |
| 3–4 | Partially on-target but the primary cognitive demand drifts to an adjacent or easier skill |
| 5–6 | On-target but shallow: the question touches the declared skill but could be answered via a simpler strategy |
| 7–8 | Well-targeted: the question genuinely requires the declared skill and tests at the expected cognitive depth |
| 9–10 | Perfectly targeted: the question isolates the declared skill, uses appropriate trap mechanisms, and tests the precise sub-skill at the right depth |

**Grammar questions:** Check against grammar_role_key and grammar_focus_key taxonomy. The syntactic trap, distractor construction, and passage architecture must align with the declared focus.

**Reading questions:** Check against question_family_key, reading_skill_family_key, and reading_focus_key taxonomy. The stimulus mode, answer mechanism, and reasoning trap must align with the declared skill.

### difficulty_match_score — Difficulty Match

Does the question's apparent difficulty match the requested difficulty band?

| Band | Description |
|---|---|
| 0–2 | Gross mismatch: requested "hard" but question is trivial, or requested "easy" but question requires expert-level knowledge |
| 3–4 | Notable mismatch: one band off (requested "medium" but question is clearly "easy" or clearly "hard") |
| 5–6 | Acceptable range: question difficulty is in the right neighborhood but leans slightly easy or slightly hard |
| 7–8 | Good match: question difficulty aligns with the request, distractors create appropriate challenge for the band |
| 9–10 | Perfect match: question difficulty, passage complexity, trap depth, and distractor plausibility all calibrated to the requested band |

**Calibration anchors:**
- **Low/easy:** Straightforward application of a single rule, minimal trap complexity, one obviously wrong distractor
- **Medium:** Requires distinguishing between two plausible options, moderate passage complexity, distractors target common student errors
- **High/hard:** Requires elimination under time pressure, multi-step reasoning, distractors that exploit specific failure modes listed in the taxonomy

### distractor_quality_score — Distractor Quality + Correct-Answer Defensibility

Are distractors plausible, distinct, and well-targeted? Is the correct answer unambiguously defensible?

| Band | Description |
|---|---|
| 0–2 | Two or more distractors are obviously wrong; correct answer is arguably wrong or could be debated |
| 3–4 | One distractor is too easy to eliminate; correct answer has a minor defensibility issue; distractors fail for similar reasons |
| 5–6 | All distractors are somewhat plausible but one is noticeably weaker; correct answer is defensible but could be challenged |
| 7–8 | All three distractors are plausible and target distinct student failure modes; correct answer is clearly correct and well-defended by the explanation |
| 9–10 | Distractors are expertly crafted: each exploits a documented failure mode, no two share the same elimination reason, correct answer is unambiguous with precise textual support |

**Evaluation criteria:**
- Each distractor must target a distinct student failure mode from the taxonomy
- No two distractors should fail for the same reason
- The correct answer must have clear textual evidence in the passage/stimulus
- Plausibility sources must match the distractor taxonomy (semantic imprecision, logical mismatch, scope error, etc.)

### explanation_quality_score — Explanation Quality + Student-Facing Clarity

Is the explanation accurate, clear, and free of ambiguity?

| Band | Description |
|---|---|
| 0–2 | Explanation is wrong, misleading, or missing |
| 3–4 | Explanation is partially correct but omits key reasoning or uses confusing language |
| 5–6 | Explanation is correct but could be clearer; may include minor ambiguity or unnecessary jargon |
| 7–8 | Clear, accurate explanation that walks through the reasoning step by step; minor room for improvement |
| 9–10 | Exemplary explanation: concise, precise, references specific passage evidence, addresses why each distractor fails, and is accessible to a student at the target difficulty level |

**Student-facing ambiguity check:**
- The explanation must not use circular reasoning ("the answer is A because A is correct")
- Must reference specific textual evidence, not just restate the correct option
- Must address at least the most plausible distractor's failure mode
- Must not introduce external knowledge not present in the passage

### copy_risk_score — Copy/Near-Duplicate Risk (inverted: lower is better)

Does the question copy or closely paraphrase passage text, question stems, options, or explanations from the official source examples?

| Band | Description |
|---|---|
| 0–2 | Entirely original; no passage, stem, option, or explanation text overlaps with source examples beyond common academic vocabulary |
| 3–4 | Minor overlap: a phrase or sentence pattern echoes a source example but the question tests a different concept with different structure |
| 5–6 | Moderate overlap: passage topic or structural pattern is similar to a source example; one option may be a near-paraphrase |
| 7–8 | High overlap: passage or stem closely mirrors a source example; options are recognizable rephrasings |
| 9–10 | Near-duplicate: passage, stem, or options are essentially copied from a source example with minimal changes |

**Evaluation approach:** Compare the generated question against the source official examples provided in the review prompt. Assess whether a student who has seen the source example would recognize the generated question as a derivative. Common academic vocabulary and standard SAT phrasing do not count as overlap.

---

## Verdict Logic

After scoring all dimensions, assign one of three verdicts:

### `accept`
All of the following are true:
- `realism_score` ≥ 7.0
- `sat_fidelity_score` ≥ 7.0
- `taxonomy_match_score` ≥ 7.5
- `distractor_quality_score` ≥ 6.5
- `copy_risk_score` ≤ 5.0
- No significant structural problems

### `needs_human_review`
Any of the following:
- One or more scores are near the threshold (within 0.5 points above)
- The reviewer is uncertain but not confident enough to reject
- One distractor is borderline plausible but the others are strong
- The explanation is mostly clear but has a minor ambiguity
- `copy_risk_score` is 4.0–5.0 (elevated but not clearly derivative)

### `reject`
Any of the following:
- `realism_score` < 5.0
- `sat_fidelity_score` < 5.0
- `taxonomy_match_score` < 5.0
- `distractor_quality_score` < 4.0
- `copy_risk_score` > 7.0
- Fundamental structural problems: wrong number of options, missing correct answer, passage incoherent, or stem does not pose a clear question

**Important:** The verdict is advisory. The final decision rests with the human admin. When in doubt between `accept` and `needs_human_review`, choose `needs_human_review`. When in doubt between `needs_human_review` and `reject`, choose `needs_human_review`.

---

## Reasons Requirement

**Every score below its dimension threshold MUST include a short reason string.**

For example, if `distractor_quality_score` is 5.8 (below the 6.5 threshold), the `reasons` object must include:
```json
"distractor_quality_score": "Option C uses the same failure mode as Option B (semantic imprecision); both fail for similar reasons."
```

Scores meeting or exceeding their threshold MAY include reasons but are not required to. `copy_risk_score` reasons are especially valuable — even scores in the acceptable range (3.0–5.0) benefit from a brief explanation of what overlap was detected.

Reasons should be specific, not generic. "Low quality" is not helpful. "Option B is a distractor that uses `semantic_imprecision` but the passage does not contain the semantic hook needed to make it plausible" is helpful.

---

## Strict JSON Output Schema

You MUST return a single JSON object with exactly these keys. No additional keys at the top level. No prose before or after the JSON.

```json
{
  "realism_score": 8.7,
  "sat_fidelity_score": 8.4,
  "difficulty_match_score": 7.9,
  "distractor_quality_score": 8.1,
  "taxonomy_match_score": 9.0,
  "explanation_quality_score": 8.2,
  "copy_risk_score": 1.1,
  "verdict": "accept",
  "reasons": {
    "realism_score": "Optional: reason when below 7.0",
    "sat_fidelity_score": "Optional: reason when below 7.0",
    "difficulty_match_score": "Optional: reason when significantly mismatched",
    "distractor_quality_score": "Optional: reason when below 6.5",
    "taxonomy_match_score": "Optional: reason when below 7.5",
    "explanation_quality_score": "Optional: reason when explanation is unclear",
    "copy_risk_score": "Optional: reason when above 3.0"
  }
}
```

**Schema rules:**
1. All seven score keys MUST be present. No missing keys.
2. All scores MUST be numeric (integer or float) in the range [0, 10].
3. `verdict` MUST be exactly one of: `"accept"`, `"needs_human_review"`, `"reject"`.
4. `reasons` MUST be an object. Keys MUST be a subset of the seven score keys. Values MUST be strings.
5. Any score below its dimension threshold MUST have a corresponding reason.
6. No extra top-level keys. No nested objects beyond `reasons`.
7. Output valid JSON only. No markdown fences, no prose, no commentary outside the JSON object.

---

## Version

v1

This is a write-once rubric. Do not edit this version after it has been used for real reviews. Create a new file (e.g., `rules_agent_dsat_review_v2.md`) for any changes. Patch bumps (typo fixes, clarification, no semantic change) leave existing review rows on v1 and do not trigger re-calibration. Major bumps (added/removed dimension, retuned anchors, JSON schema change) require re-calibration of consensus thresholds.