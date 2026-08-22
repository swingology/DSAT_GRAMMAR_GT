# Research Paper TODO: Rules, Examples, and Model Class in AI-Generated Reading Questions

## Working Title

**Rules, Examples, or Neither? A Controlled Evaluation of Frontier and Open-Weight Models for Generating DSAT-Style Reading Questions**

## Research Objective

Determine how explicit reading rules and retrieved official source examples affect the quality, validity, originality, cost, and latency of AI-generated DSAT-style reading questions across proprietary frontier models and open-weight models.

This is a controlled generation study, not a claim that generated questions have established psychometric validity. Human judgments are the primary quality reference. Student-response difficulty and discrimination are out of scope unless a separately approved participant study is completed.

## Primary Research Question

How does generation condition affect the human-rated usability of generated DSAT-style reading questions, and does that effect differ across model families?

## Secondary Research Questions

1. How much do reading rules improve correctness, taxonomy alignment, difficulty matching, and distractor quality?
2. After rules are present, how much additional value do matched official examples provide?
3. Do examples increase source-copying or semantic-overlap risk?
4. Do frontier and open-weight models benefit differently from rules and examples?
5. Which condition gives the best quality-cost-latency tradeoff?
6. How well do blinded LLM reviewers agree with blinded human reviewers?
7. Can reviewer disagreement identify questions that require human review?

## Scope Lock

- Study reading questions only. A separate grammar cohort can be added after the reading study is complete.
- Generate original practice items, not official items or paraphrases of official items.
- Use official questions only as private calibration examples.
- Do not publish official question text. Publish source IDs, hashes, overlap statistics, and permitted generated artifacts.
- Do not claim learning improvement, item difficulty, item discrimination, or test validity without student-response evidence.

## Three Generation Versions

All three versions receive the same short invariant instruction, target specification, and required JSON output schema. "No rules" does not mean no format instructions; removing the shared schema would make outputs incomparable.

### Version 1: Reading Rules plus Matched Source Examples

- Include the selected Reading v3 generation-rule sections.
- Include a fixed number of official examples matched by reading skill, focus, and requested difficulty.
- Use the same source-example set for every model generating a given target specification.
- Explicitly instruct the model not to copy passages, stems, options, or explanations.

### Version 2: No Reading Rules and No Source Examples

- Include only the invariant base instruction, target specification, and output schema.
- Exclude Reading v3 content.
- Exclude official examples.
- Use this as the minimal baseline.

### Version 3: Reading Rules without Source Examples

- Include exactly the same Reading v3 rule text used in Version 1.
- Exclude official examples.
- Keep every other prompt component identical to Version 1.

### Planned Contrasts

- **Rules effect:** Version 3 minus Version 2.
- **Incremental examples effect:** Version 1 minus Version 3.
- **Full grounding effect:** Version 1 minus Version 2.

This three-version design cannot estimate an examples-only effect or a rules-by-examples interaction. Doing that would require a fourth condition containing examples without rules. Do not claim either effect from this experiment.

## Model Matrix

Run every target specification under every prompt version and every model. Model and prompt condition must be crossed; never give one condition only to one model class.

### Frontier, Proprietary Models

Initial candidates:

1. OpenAI GPT-5.6 Sol (`gpt-5.6-sol` or the dated snapshot available when the protocol is frozen).
2. One current Anthropic Claude Sonnet or Opus snapshot, verified directly against Anthropic before the pilot.

### Open-Weight Models

Initial candidates already available through the local Ollama installation:

1. Qwen 3.6 27B (`qwen3.6:27b`).
2. Gemma 4 31B (`gemma4:31b-cloud`), with hosting mode recorded as cloud even though the model family is open-weight.

Use the term **open-weight**, not automatically "open source," unless the exact license satisfies the paper's stated definition of open source.

### Model Integrity Requirement

- Pin an exact model ID or snapshot where the provider permits it.
- Record provider, requested model, returned model, endpoint, hosting mode, and model-family classification.
- Run a routing probe before the pilot and save the raw response metadata.
- Do not treat provider aliases as different models.
- The current `litellm/config.yaml` routes `gpt-4o`, `claude-sonnet-4-6`, and `deepseek-v4-pro:cloud` to the same `qwen3.6:27b` model. Those aliases cannot be used as independent frontier models.
- Direct hosted endpoints must be configured and verified before frontier-model data collection.
- If a chosen model is retired before the main run, replace it before collecting main-study data and record the protocol amendment. Never mix silent model upgrades within a study cell.

## Experimental Unit and Sampling

The experimental block is one target specification. The same target specification is sent to all 12 model-condition cells:

```text
3 prompt versions x 4 models = 12 outputs per target specification
```

### Pilot

```text
6 target specifications x 3 versions x 4 models = 72 generated questions
```

Pilot goals:

- verify all model routes;
- verify prompt isolation;
- detect malformed-output and validation problems;
- estimate cost and runtime;
- refine the human rubric;
- estimate outcome variance and acceptance prevalence;
- perform a power analysis for the main experiment.

Pilot results must not be included in the confirmatory main-study results unless that decision is made before examining condition differences.

### Provisional Main Study

```text
30 target specifications x 3 versions x 4 models = 360 generated questions
```

If the pilot shows high stochastic variability, use two independent repetitions:

```text
30 target specifications x 3 versions x 4 models x 2 repetitions = 720 questions
```

Finalize the main sample size using the pilot power analysis, budget, and realistic human-rating capacity.

### Target-Specification Balance

- Balance active reading skill families and reading-focus keys.
- Balance easy, medium, and hard targets.
- Use only taxonomy values valid in `vocabulary/master.json`.
- Freeze the target manifest before running the first main-study generation.
- Give each specification a stable `specification_id`.
- Do not replace failed questions selectively. Retain and count failures as outcomes.

## Generation Controls

Hold constant as far as each provider permits:

- invariant base prompt;
- target specification;
- Reading v3 rules text and hash;
- output JSON schema;
- number and identity of examples;
- maximum output-token budget;
- sampling or reasoning settings;
- retry policy;
- validation code;
- repository commit;
- vocabulary snapshot;
- generation time window.

Randomize execution order across condition and model so that outages, load, or time-of-day effects do not align with one condition.

### Reproducibility Warning

The current generation job stores a seed but the provider protocol does not pass that seed to the model. Until seed handling is implemented and verified, treat generations as stochastic repetitions and do not describe them as seed-reproducible.

## Source-Example Protocol

For Version 1:

1. Select examples from active official reading questions only.
2. Match the target reading skill and focus exactly when possible.
3. Match requested difficulty secondarily.
4. Use a fixed `k` examples for all Version 1 prompts. Select `k` during the pilot and freeze it.
5. Freeze example IDs in the experiment manifest before generation.
6. Use the identical example set across all four models for a specification.
7. Record source exam codes and IDs privately.
8. Never use the generated candidate itself or another generated item as a source example.

## Measurements

### Primary Outcome

Blinded human judgment:

> Is this question usable without editing?

Allowed labels:

- `usable_without_editing`
- `usable_with_minor_edit`
- `not_usable`

The confirmatory primary analysis uses `usable_without_editing` versus all other labels.

### Human-Rated Secondary Outcomes

Use a common anchored rubric for all raters:

- answer correctness and unambiguity;
- DSAT-style fidelity;
- difficulty match;
- distractor quality;
- taxonomy match;
- explanation quality;
- source-copying risk;
- overall quality.

Use numeric scores only when every score point has a written anchor. Include a free-text defect code and optional notes.

### Deterministic Automated Measurements

- valid JSON rate;
- schema-validation rate;
- pipeline-validation error count and categories;
- exactly four options and one correct answer;
- annotation/taxonomy validity;
- requested-versus-produced skill match;
- requested-versus-produced difficulty label match;
- official-overlap detector status;
- exact and normalized duplicate rate;
- word and character n-gram overlap with source examples;
- longest-common-substring ratio by passage, stem, and options;
- embedding similarity to each source example and nearest official question;
- lexical and semantic diversity within each condition;
- generation success, retry, and permanent-failure rates.

### Performance and Resource Measurements

- end-to-end latency;
- provider-reported latency when available;
- input tokens;
- cached input tokens;
- output tokens;
- reasoning tokens when reported;
- estimated monetary cost using a dated pricing snapshot;
- local wall-clock time;
- local peak memory and GPU/CPU utilization where measurable;
- energy measurement only if instrumentation is reliable enough to describe precisely.

### Reviewer Measurements

- seven rubric scores;
- accept, needs-review, or reject verdict;
- parse-failure rate;
- reviewer latency and token usage;
- agreement with individual humans and adjudicated human labels;
- inter-reviewer correlation;
- verdict disagreement;
- false-acceptance rate;
- recall of human-rejected questions;
- calibration error;
- quality-cost-latency tradeoff.

## Blinded Human Review Plan

1. Remove model, provider, version, source IDs, prompt condition, latency, and cost from the rater export.
2. Randomize question order independently for each rater.
3. Use at least two raters per question; three is preferred.
4. Create a calibration set with examples of each rubric label before formal rating.
5. Do not allow raters to discuss main-study questions before independent scoring.
6. Adjudicate disagreements using a documented procedure.
7. Record original ratings and adjudicated ratings separately.
8. Measure inter-rater reliability with weighted kappa for ordinal labels and ICC for numeric scores.
9. Obtain an institutional IRB determination before recruiting research participants when required, especially if minors or student-response data are involved.

## LLM Reviewer Plan

Human ratings remain the reference. LLM reviewers are evaluated instruments, not ground truth.

### Reviewer Research Question

Can independent LLM reviewers predict blinded human judgments of generated-question quality, and can a calibrated review gate reduce human-review workload without increasing the rate at which flawed questions are accepted?

### Reviewer Hypotheses

- **JH1:** Reviewer performance will vary substantially by rubric dimension; objective defects will align with humans better than difficulty or stylistic judgments.
- **JH2:** A panel of genuinely distinct model families will outperform an equal-sized homogeneous panel of repeated calls to one underlying model.
- **JH3:** Same-model and same-family reviewers will score their own family's generated questions more favorably after controlling for human ratings.
- **JH4:** Reviewer disagreement will identify questions with low human agreement or a high probability of human rejection.
- **JH5:** A selective gate can reduce human-review volume while retaining at least 95% recall of questions humans classify as `not_usable`.

### Proposed Reviewer Models

Use the four verified generation models as reviewers so the study contains both self-review and cross-family review pairs:

1. OpenAI GPT-5.6 Sol.
2. The frozen Anthropic Claude model selected before the pilot.
3. Qwen 3.6 27B.
4. Gemma 4 31B.

Optionally add a fifth judge-only model family that generated no questions. This provides a fully held-out reviewer but is secondary to completing the balanced four-reviewer matrix.

Every reviewer must evaluate every eligible generated question. For a 360-question main dataset and four reviewers, this produces:

```text
360 questions x 4 reviewers = 1,440 reviewer calls
```

Estimate this cost during the pilot before authorizing the main reviewer run.

### Reviewer Blinding and Independence

1. Remove generator identity, model class, prompt version, generation condition, source IDs, latency, cost, and generation metadata from reviewer prompts.
2. Give every reviewer byte-identical question content and the same versioned rubric.
3. Do not include another reviewer's scores or verdict in an independent review call.
4. Verify requested model, returned model, endpoint, and backend before every reviewer run.
5. Preserve raw output, parsed output, failures, token use, and latency.
6. Treat reviewer calls as independent only when they resolve to genuinely distinct model families.
7. Do not describe different provider aliases pointing to one model as a multi-model ensemble.

### Homogeneous-versus-Diverse Panel Test

On a preselected subset or the full dataset if budget permits, compare equal-sized panels:

- **Single judge:** one reviewer result.
- **Homogeneous panel:** three independent calls to the same underlying model, clearly labeled as repeated sampling.
- **Diverse panel:** one result from each of three genuinely different model families.
- **All-reviewer panel:** all four verified reviewer families.

Use the same number of votes when directly comparing homogeneous and diverse panels. This tests whether model-family diversity adds information beyond repeated sampling from one model.

### Self-Preference and Family-Preference Test

For every generator-reviewer pair, assign one relationship label:

- `self_model`: exact same model generated and reviewed the item;
- `same_family`: different model or size from the same family;
- `cross_family`: independently developed model family;
- `unknown`: relationship cannot be verified.

The primary reviewer-accuracy analysis excludes `self_model` pairs. A separate bias analysis compares reviewer-minus-human score residuals across the relationship labels. Report whether self or same-family reviewers are systematically more favorable, not merely whether their raw scores are higher.

### Review Policies to Compare

1. Each individual reviewer.
2. Majority vote over reviewer verdicts.
3. Mean-score thresholding.
4. The existing ordered deterministic consensus gate in `backend/app/review/consensus.py`.
5. A homogeneous repeated-model panel.
6. A genuinely diverse model-family panel.
7. Disagreement-triggered human escalation.
8. A calibrated gate trained only on the calibration partition.
9. Human review of every question as the workload reference.

The calibrated or selective gate must never be evaluated on the same questions used to select its thresholds.

### Reviewer Dataset Split

Split by `specification_id`, not individual question row, so variants of one target cannot appear in both partitions:

- 30% calibration partition for threshold selection and model fitting;
- 70% held-out evaluation partition for final reviewer results.

Stratify the split by generation version, generator model, reading skill, difficulty, and human usability label where possible. Freeze and hash the split before fitting a gate.

### Reviewer Evaluation Metrics

#### Numeric Rubric Scores

- ICC for absolute agreement with humans;
- Spearman rank correlation;
- mean absolute error;
- signed reviewer-minus-human score bias;
- dimension-specific performance and confidence intervals.

#### Verdict Accuracy

- macro-F1;
- balanced accuracy;
- weighted kappa;
- false-acceptance rate;
- recall of human `not_usable` questions;
- precision of accept and reject decisions.

#### Calibration and Selective Review

- Brier score;
- expected calibration error;
- risk-coverage curve;
- percentage of questions escalated to humans;
- human-workload reduction at fixed flawed-question recall;
- residual error rate among automatically accepted questions.

#### Reviewer Diversity

- pairwise score correlation;
- verdict agreement;
- error overlap against human labels;
- disagreement entropy;
- homogeneous-versus-diverse ensemble gain.

#### Efficiency

- reviewer input and output tokens;
- wall-clock and provider latency;
- dated estimated monetary cost;
- cost per human-rejected question detected;
- quality-cost-latency Pareto frontier.

### Reviewer Analysis Models

Use a mixed-effects model for reviewer score error or favorability:

```text
reviewer_score_minus_human_score
  ~ reviewer_generator_relationship
  + rubric_dimension
  + generation_version
  + generator_model
  + reviewer_model
  + (1 | question_id)
```

For verdict correctness, fit an analogous mixed-effects logistic model. Cluster bootstrap confidence intervals by `specification_id` so all versions and model outputs from one target remain together.

### Reviewer Claims Boundary

- A high correlation does not prove the reviewer is a valid replacement for humans.
- Agreement must be reported separately from absolute calibration.
- Do not use the existing LLM consensus verdict as the human reference label.
- Do not claim provider diversity when providers share an underlying model.
- Do not claim a human-workload reduction unless the required flawed-question recall is met on held-out data.
- Report negative findings, parsing failures, missing token data, and provider errors.

## Statistical Analysis Plan

### Confirmatory Analysis

Fit a mixed-effects logistic regression for the primary binary outcome:

```text
usable_without_editing
  ~ generation_version * model_id
  + difficulty
  + reading_skill_family
  + (1 | specification_id)
  + (1 | human_rater_id)
```

Use planned contrasts:

- Version 3 versus Version 2;
- Version 1 versus Version 3;
- Version 1 versus Version 2;
- each contrast within each model;
- contrasts averaged descriptively within frontier and open-weight groups.

With only two models per model class, do not claim the results generalize to all frontier or all open-weight models. Treat model ID as the primary comparison and model-class summaries as secondary.

### Secondary Analyses

- ordinal mixed models for usability and rubric scores;
- clustered bootstrap confidence intervals, resampling by specification;
- condition-specific failure and overlap rates;
- human-LLM agreement using weighted kappa, ICC, macro-F1, and balanced accuracy;
- calibration using Brier score and expected calibration error;
- selective-review risk-coverage curves;
- Pareto plots for quality, cost, and latency.

Report effect sizes and 95% confidence intervals. Correct secondary multiple comparisons or label them exploratory. Do not present p-values without effect sizes.

## Required Code Work Before the Pilot

- [ ] Add a benchmark-only `generation_version` enum with the three locked conditions.
- [ ] Make `rule_mode` explicit instead of inferring it from normal production behavior.
- [ ] Make `example_mode=none` bypass automatic source selection.
- [ ] Make Version 1 and Version 3 use byte-identical Reading v3 rule content.
- [ ] Fix the current `Reading v2` versus `Reading v3` label mismatch in `backend/app/prompts/generate_prompt.py`.
- [ ] Add regression tests proving each condition contains and excludes the intended prompt sections.
- [ ] Add snapshot hashes for the invariant prompt, rules, examples, and full request.
- [ ] Record input, cached-input, output, and reasoning tokens when providers return them.
- [ ] Record the actual returned model name and endpoint class.
- [ ] Either implement provider-supported seeds or remove claims that the stored seed controls generation.
- [ ] Add a routing-verification command that fails if two supposedly distinct model IDs resolve to the same backend unexpectedly.
- [ ] Ensure failed generations remain in the experiment dataset.
- [ ] Keep benchmark outputs separate from production questions and student retrieval.

## Proposed Benchmark Layout

```text
backend/benchmark/generation_research/
├── README.md
├── experiment.yaml
├── schemas.py
├── build_manifest.py
├── verify_model_routes.py
├── render_prompts.py
├── run_generation.py
├── validate_outputs.py
├── measure_similarity.py
├── export_blind_human_review.py
├── import_human_review.py
├── run_llm_reviewers.py
├── analyze_generation.py
├── analyze_reviewers.py
├── report_tables.py
├── fixtures/
├── manifests/
├── results/
└── tests/
```

Generated outputs should be append-only. Never overwrite a previous run.

## Minimum Result Record

```json
{
  "experiment_id": "reading-generation-v1",
  "run_id": "uuid",
  "specification_id": "read-001",
  "repetition": 1,
  "generation_version": "rules_and_examples",
  "rule_mode": "reading_v3",
  "example_mode": "matched",
  "source_question_ids": ["private-id"],
  "provider": "openai",
  "requested_model": "gpt-5.6-sol",
  "returned_model": "provider-returned-id",
  "model_class": "frontier_proprietary",
  "hosting_mode": "hosted_api",
  "temperature": null,
  "reasoning_setting": "locked-value",
  "prompt_hash": "sha256",
  "rules_hash": "sha256-or-null",
  "examples_hash": "sha256-or-null",
  "repository_commit": "git-sha",
  "status": "success",
  "latency_ms": 0,
  "token_usage": {},
  "validation": {},
  "similarity": {},
  "raw_output_path": "append-only-path"
}
```

## Execution Phases

### Phase 0: Freeze the Protocol

- [ ] Confirm the paper title and research questions.
- [ ] Lock the three generation versions.
- [ ] Decide the exact number of examples in Version 1.
- [ ] Select and verify the four models.
- [ ] Define the open-weight licensing terminology used in the paper.
- [ ] Define the primary outcome and human rubric anchors.
- [ ] Create the target-specification manifest.
- [ ] Pre-register hypotheses, exclusions, contrasts, and analysis.

### Phase 1: Build the Benchmark Harness

- [ ] Complete every item under Required Code Work.
- [ ] Add unit tests for condition isolation.
- [ ] Add integration tests using fake providers.
- [ ] Verify append-only output behavior.
- [ ] Verify no benchmark question can become student-visible.

### Phase 2: Run the Pilot

- [ ] Run routing probes.
- [ ] Generate the 72-question pilot.
- [ ] Inspect failures without comparing condition winners prematurely.
- [ ] Run deterministic measurements.
- [ ] Conduct human-rubric calibration.
- [ ] Estimate costs, variance, and human-review workload.
- [ ] Perform the power analysis.
- [ ] Amend and re-freeze the protocol if necessary.

### Phase 3: Run Main Generation

- [ ] Freeze repository commit and manifests.
- [ ] Randomize execution order.
- [ ] Run all planned generation cells.
- [ ] Verify expected versus completed cells.
- [ ] Preserve every success and failure.
- [ ] Export an immutable run manifest and checksums.

### Phase 4: Gather Automated Measurements

- [ ] Run schema and taxonomy validation.
- [ ] Run answer-consistency checks.
- [ ] Run exact, lexical, and semantic overlap measurements.
- [ ] Compute diversity measurements.
- [ ] Aggregate latency, tokens, failures, and cost.
- [ ] Produce a blinded human-review export.

### Phase 5: Conduct Human Review

- [ ] Collect independent blinded ratings.
- [ ] Measure inter-rater agreement.
- [ ] Adjudicate according to the frozen procedure.
- [ ] Lock the human-reference dataset before evaluating LLM-reviewer performance.

### Phase 6: Conduct LLM Reviewer Evaluation

- [ ] Verify reviewer routes.
- [ ] Run each independent reviewer on all eligible candidates.
- [ ] Preserve parse failures and raw outputs.
- [ ] Run consensus and disagreement policies.
- [ ] Freeze the calibration/held-out split.
- [ ] Evaluate agreement, safety, calibration, cost, and latency.

### Phase 7: Analyze Results

- [ ] Run the confirmatory mixed-effects analysis.
- [ ] Calculate planned contrasts and confidence intervals.
- [ ] Run secondary and exploratory analyses separately.
- [ ] Produce condition-by-model tables.
- [ ] Produce quality-cost-latency Pareto plots.
- [ ] Perform sensitivity checks including failed generations.
- [ ] Document all deviations from the frozen protocol.

### Phase 8: Write the Paper

- [ ] Abstract: question, design, sample, primary result, limitation.
- [ ] Introduction: why controlled item generation matters.
- [ ] Related work: automatic item generation, in-context examples, rule grounding, LLM judges, psychometrics.
- [ ] Methods: conditions, models, sampling, blinding, metrics, statistics.
- [ ] Results: primary analysis first, then secondary analyses.
- [ ] Discussion: mechanisms, tradeoffs, negative results, and limitations.
- [ ] Ethics and copyright statement.
- [ ] Reproducibility statement.
- [ ] Appendix with prompt templates, rubric, and non-copyrighted aggregate data.

## Success Criteria

The project is complete when:

- all planned cells have either an immutable output or an explicitly recorded failure;
- human ratings are blinded and agreement is reported;
- primary outcomes and contrasts match the pre-registered plan;
- frontier aliases are proven to resolve to distinct frontier models;
- automated and LLM metrics are compared against human judgments rather than treated as truth;
- effect sizes and uncertainty are reported;
- official source text is not released;
- claims stay within the evidence collected;
- the analysis can be reproduced from the frozen manifest and result records.

## Reference Starting Points

- Existing system framing: `ARXIV-IDEAS.md`
- Generation architecture: `docs/GENERATION_ARCHITECTURE.md`
- Generation prompt composition: `backend/app/prompts/generate_prompt.py`
- Source-example selection: `backend/app/routers/generate.py::_select_source_question_ids_for_batch`
- Review runner: `backend/app/review/runner.py`
- Deterministic consensus: `backend/app/review/consensus.py`
- Human/admin overrides: `backend/app/models/db.py::ReviewerAdminOverride`
- Official OpenAI GPT-5.6 Sol documentation: <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
