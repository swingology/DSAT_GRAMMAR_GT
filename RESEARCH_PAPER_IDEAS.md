# Research Paper Ideas for DSAT_REDUX_MD

**Merged:** September 18, 2026. Combines two earlier drafts written at different times by different agents — an initial proposal recommending a judge-reliability study (plus its 2026-08-21 review addendum) and a 2026-09-14 controlled-experiment proposal — plus the earlier `ARXIV-IDEAS.md` systems-paper idea, preserved as §6. Overlapping material is merged; unique material is preserved; all three source files are superseded by this document. `RESEARCH_PAPER_TODO.md` remains a separate companion document (the rules × examples × model run plan).

**Status:** Research proposals and experimental designs; no experimental results are claimed. All sample sizes are planning figures, not demonstrated power requirements.

The program supports two candidate first papers that share one dataset:

- **Paper A — Generation quality:** a controlled comparison of how accurately different LLMs generate DSAT-style questions, how authentic those questions appear, and how much explicit rules and matched examples improve them.
- **Paper B — Judge reliability:** whether LLM reviewers can reliably identify flawed AI-generated questions, and whether a calibrated review gate reduces human review effort without letting more bad questions through.

The adopted resolution (from the addendum's "two documents, one dataset" note): generate once, rate once, preregister two separate studies. Paper A creates the corpus and human reference ratings; Paper B consumes them. Quick-win studies on data already on disk come before either.

Both drafts agree on the core insight: "I built an AI SAT generator" is a software project, not a research contribution. A carefully controlled experiment — including negative findings — contributes more than the size of the application.

## 1. Program context and assets

### 1.1 What the repository already provides

- Generation batches with per-question provenance; configurable generation.
- Official-example retrieval matched by skill and difficulty, with source rotation.
- Seven-dimensional LLM review scores; deterministic consensus logic; human approve/reject decisions.
- Overlap/copy-risk detection.
- Token counts and reviewer latency.
- Stored review results and consensus recommendations.

Key implementation points: `docs/GENERATION_ARCHITECTURE.md`, `backend/app/review/runner.py`, `backend/app/review/consensus.py`, `backend/app/prompts/review_prompt.py`.

### 1.2 Gaps that shape the research design

- The current review prompt scores seven quality dimensions **without a separate correctness score**. The research rubric needs explicit correctness and answer-uniqueness judgments.
- The review runner excludes the generator's provider. A self-preference experiment therefore needs a separate benchmark configuration that deliberately includes those pairings and records actual model identities.
- The project previously discovered that nominally different providers could route to the same local model. That is a genuine methodological issue for any judge-diversity claim: verify actual endpoints and resolved model identities before collecting data.

### 1.3 Data reality check

A live-DB check found **1,438 active official questions but zero generation batches, generated questions, review results, or consensus results**. The infrastructure is excellent; the research data does not yet exist. The next step is a deliberately designed benchmark, not analysis of existing results.

## 2. The two candidate first papers

The first draft recommended the judge-reliability paper: with zero generated data, any first study must be a designed benchmark. The second draft recommended the generation-quality paper. These are compatible: the generation run produces the corpus, and the judge study reuses its human ratings.

### 2.1 Paper A — Generation quality (runs first)

**Working title:** *Accuracy, Authenticity, and Controllability of LLM-Generated Digital SAT Reading Questions: A Controlled Comparison of Models, Rules, and Examples*

**Central research question:** How do model choice, explicit generation rules, and matched official examples affect the correctness, authenticity, and usability of generated DSAT-style reading questions?

Scope notes:

- Keep the first paper focused on reading; grammar can become a separate comparison or replication. College Board's Reading and Writing section covers four domains, so a reading-only experiment should state its sampled skills and avoid claiming section-wide coverage. [College Board's content description](https://satsuite.collegeboard.org/sat/whats-on-the-test/reading-writing)
- The contribution is explaining *why* quality changes across models and methods, so the findings remain useful beyond whichever model wins.

Full design in §4.

### 2.2 Paper B — Judge reliability

**Working title:** *Independent or Illusory? Evaluating LLM Judges for Quality Control of AI-Generated Standardized-Test Items*

**Core question:** Can LLM reviewers reliably identify flawed AI-generated standardized-test questions, and can a calibrated review gate reduce human review effort without allowing more bad questions through?

**Research questions:**

1. How closely do individual LLM reviewers agree with blinded human reviewers?
2. Do genuinely different model families outperform multiple provider names routed to the same underlying model?
3. Does a model score questions produced by itself more favorably?
4. Which rubric dimensions are reliably judged — correctness, fidelity, distractor quality, difficulty, copy risk?
5. Can uncertain cases be sent to humans while confidently safe or unsafe cases are handled automatically?
6. What are the quality–cost–latency tradeoffs of one judge, several judges, and a selective gate?

RQ2 is particularly relevant given the same-model routing discovery in §1.2 — a genuine methodological issue, not merely an implementation bug.

**Corpus (from Paper A):** approximately 200–300 balanced items — grammar and reading; easy, medium, and hard targets; multiple question families; at least three generator models; matched prompts and source examples; several deterministic seeds. Three blinded human raters per item; generator and reviewer identity hidden.

**Review fixes integrated from the 2026-08-21 addendum:**

1. **Rating-labor math doesn't close** at 250 items × 3 raters × 7 dimensions ≈ 5,250 ratings plus adjudication. Cut human rating to 4 dimensions (correctness, fidelity, distractor quality, copy risk), or rate 2 dimensions at full N and the rest on a subsample. Run a power calculation before freezing N.
2. **A single train/held-out split on ~250 items gives wide CIs.** Use k-fold cross-validation for threshold tuning; report bootstrap CIs over folds.
3. **RQ3 constrains the model matrix:** every judge model must also be a generator — fully crossed. State and budget this explicitly.
4. **Define a gold-verdict protocol** (majority / senior rater / discuss-to-consensus) for verdict-agreement metrics; report human inter-rater reliability as the ceiling against which LLM judges are compared.
5. **Copy-risk checks must include the crackap corpus**, not only official items — 669 of 1,285 unmatched items show third-party prep content is a second leakage surface.
6. **Local-model cost:** report wall-clock / GPU-seconds / energy, not "$" estimates.
7. **Stratify by item format** (passage-based reading vs standalone grammar; stimulus vs none) — judges likely behave differently across them.

**Review configurations to compare:** single LLM judges; majority voting; the existing deterministic threshold gate; three nominal providers sharing one base model; three genuinely distinct model families; an uncertainty-aware gate that escalates ambiguous cases to humans.

**Measurements:**

| Question | Metrics |
|---|---|
| Numeric-score agreement | ICC, Spearman correlation, MAE |
| Verdict agreement | Macro-F1, balanced accuracy, weighted kappa |
| Safety | False-acceptance rate, recall of human-rejected items |
| Calibration | Brier score, expected calibration error |
| Reviewer diversity | Score correlation, error overlap, disagreement entropy |
| Efficiency | Tokens, latency, estimated cost per reviewed item |
| Selective review | Human-review coverage versus error rate |
| Statistical uncertainty | Bootstrap 95% confidence intervals |

Methodological references: Isley et al.'s ~1,700-student psychometric field study illustrates the evidentiary bar for item-validity claims, which Paper B deliberately avoids needing for a first paper [arXiv:2508.08314](https://arxiv.org/abs/2508.08314); documented self-preference in LLM judges directly motivates RQ3 [Beyond the Surface](https://aclanthology.org/2025.emnlp-main.86/).

### 2.3 Why two papers, not one

Putting generation quality and judge reliability into a single paper makes both contributions hard to assess. Generate once; preregister the two studies separately.

## 3. Shared evaluation methodology

### 3.1 Three kinds of accuracy — measured separately

- **Solver accuracy:** can the model answer an existing question correctly?
- **Generation accuracy:** does the model create a question with exactly one defensible answer and a correct explanation?
- **Reviewer accuracy:** can the model detect defects in someone else's question?

A model could be an excellent solver but a poor question writer or reviewer.

### 3.2 Generation rubric

| Dimension | Specific measurement | Example of a failure |
|---|---|---|
| Answer-key correctness | Independent experts determine whether the supplied key is correct. | The passage supports B, but the generated key says D. |
| Answer uniqueness | Experts identify every defensible option; exactly one must qualify. | Both A and C reasonably complete the passage. |
| Evidence sufficiency | Check whether the answer follows from the supplied text without an unsupported assumption. | A causal conclusion is drawn from correlation alone. |
| Explanation correctness | Assess the correct-answer rationale and each distractor explanation separately. | Correct key, but the explanation invents a grammar rule. |
| SAT authenticity | Blinded, anchored ratings of wording, passage construction, stem, options, and reasoning demand. | The question sounds academic but requires specialist knowledge. |
| Distractor quality | Rate whether each wrong answer is plausible, clearly wrong, and linked to an identifiable mistake. | Three obviously irrelevant options make the answer trivial. |
| Skill alignment | Compare the requested skill with an independent expert classification. | A requested inference question merely asks for a stated detail. |
| Difficulty match | Compare requested difficulty with blinded expert judgments; later validate using student responses. | "Hard" means longer vocabulary rather than harder reasoning. |
| Originality | Examine phrase overlap, semantic similarity, and human judgments of dependence on examples. | A source passage is reproduced with names and numbers changed. |
| Usability | Classify as usable unchanged, needs revision, or unusable. | A good passage requires two answer choices to be rewritten. |

Authenticity anchors: **1** = substantial departures from the target format; **3** = recognizable but needing revision; **5** = convincing professional-style construction.

Freeze the complete rubric and example ratings after the pilot and before the main study.

### 3.3 Primary outcome: usable-question yield

> Usable-question yield = questions judged usable without substantive revision / planned generation attempts.

- Count malformed outputs and failed attempts in the denominator; also report semantic correctness among completed outputs, so readers can distinguish technical failures from content defects.
- Predefine the defects that make a question unusable and the cosmetic-vs-substantive revision boundary.
- A high average realism score should never compensate for a wrong answer.

### 3.4 Blinded review procedure

Two qualified raters independently evaluate each item; a third adjudicates disagreements.

1. Show the question without its generated key or explanation.
2. Have each rater solve it and identify all defensible options.
3. Lock that judgment.
4. Reveal the supplied key and explanation for separate evaluation.
5. Record defects, usability, and anchored authenticity ratings.

Hide model identity, generation condition, and automated review scores. Standardize presentation and measure human agreement before adjudication.

### 3.5 Review workload

- **Paper A:** 480 generated questions + 60 official references, double-reviewed = **1,080 item reviews**. At an assumed 4–6 minutes each, budget **72–108 reviewer-hours** plus calibration and adjudication; the pilot should test that estimate.
- **Paper B:** at full scope, 250 items × 3 raters × 7 dimensions ≈ 5,250 ratings — apply the §2.2 fixes (cut dimensions or subsample) and run a power calculation before freezing N.

### 3.6 Analysis plan

- Compare models within the same specifications; use a statistical model that accounts for specification clustering and, for separate ordinal ratings, rater differences.
- Report effect sizes and confidence intervals; designate secondary comparisons in advance; keep the primary outcome distinct from exploratory analyses.
- Separate development and final evaluation by specification, keeping related outputs together. Do not tune a gate and report its final performance on the same items. For threshold tuning, use k-fold cross-validation with bootstrap CIs over folds (addendum fix #2).
- For Paper B, report human inter-rater reliability as the ceiling for judge agreement (fix #4).

### 3.7 Proposed figures

- Usable-question yield by model and generation condition.
- Defect rates by skill and defect type.
- Authenticity versus correctness, showing questions that look convincing but fail.
- Cost per usable question versus usable-question yield.

## 4. Paper A: experimental design

### 4.1 Four experimental conditions

| Condition | Generation rules | Matched official examples | Purpose |
|---|---|---|---|
| A: Minimal baseline | No | No | Measure performance from the task specification alone. |
| B: Rules only | Yes | No | Isolate the contribution of explicit rules. |
| C: Examples only | No | Yes | Isolate the contribution of examples. |
| D: Rules + examples | Yes | Yes | Test the complete method and the rules-by-examples interaction. |

All conditions receive the same task, target skill, requested difficulty, and output schema. Verify that the benchmark actually disables injected rules and automatic example selection in the appropriate conditions. The three-condition variant remains valid for narrower questions; the fourth condition is necessary to estimate the examples-only effect and the rules-by-examples interaction.

### 4.2 Model selection and provenance

- Four frozen model versions spanning different families — for example, two hosted proprietary and two open-weight. Verify actual endpoints and returned model identities before collecting data; conclusions concern those tested versions only, since four models cannot establish a universal proprietary-versus-open-weight result.
- Record per result row: experiment and condition IDs; the actual resolved model, not merely the provider alias; prompt, rules, and rubric versions; seed and temperature; source-question IDs; raw output hash; scores and verdict; tokens, latency, and estimated cost; human ratings and adjudication; provider limitations on reproducibility (never assume a stored seed guarantees deterministic output); and the software commit SHA.

### 4.3 Main study

- **Five reading skills:** Inferences; Central Ideas and Details; Words in Context; Text Structure and Purpose; Cross-Text Connections.
- **Three requested difficulty levels:** easy, medium, hard.
- **Two independently designed target specifications per skill–difficulty combination.**
- **Four models × four generation conditions.**

```text
5 skills × 3 difficulties × 2 specifications × 4 models × 4 conditions = 480 generated questions
```

Each specification is a content brief, not a finished question; every model receives the same brief under every condition. Example specification:

> Create a hard inference question about interpreting a scientific study. The correct answer must follow from a limitation in the study design. Wrong options should represent causal overreach, reversed evidence, and an unsupported generalization.

Use approximately **60 held-out official questions** as authenticity references, matched to the sampled skills and difficulty labels, kept separate from the examples used in generation. Stratify analysis by item format (passage-based vs standalone grammar; stimulus vs none — addendum fix #7).

### 4.4 Pilot

```text
6 specifications × 4 models × 4 conditions = 96 generation attempts
```

Use the pilot to refine the rubric, verify model routing and experimental-condition isolation, measure technical and semantic failure rates, estimate human review time and generation cost, and estimate the main study's required sample size.

The 480 is a planning figure containing only 30 independent specification blocks; adding more independent specifications may be more valuable than repeatedly generating from the same few briefs. Freeze the main protocol after the pilot, preserve failures, randomize execution order across models and conditions, and never selectively replace low-quality outputs.

### 4.5 Proposed manuscript structure and abstract

| Paper section | Specific content |
|---|---|
| 1. Introduction | The need for scalable practice material and the consequences of plausible-looking but defective questions; research questions and contributions. |
| 2. Related work | Automatic question generation, distractor generation, example retrieval, LLM evaluation, educational measurement. |
| 3. System and task | Only the parts of DSAT_REDUX_MD needed to understand the experiment: specifications, rules, examples, generation, validation, review. |
| 4. Experimental design | Models, four conditions, sampled skills, source separation, generation settings, failures, reproducibility records. |
| 5. Evaluation methodology | Correctness, uniqueness, authenticity, usability, blinding, adjudication, statistical analysis. |
| 6. Results | Primary outcome first, then component effects, model differences, defect patterns, and cost. Populate only after collecting data. |
| 7. Discussion and limitations | Implications, failure modes, possible training-data exposure, limited skill/model coverage, and the boundary between expert ratings and student evidence. |
| 8. Conclusion and reproducibility | Supported contribution; permitted artifacts, prompts, rubric, manifests, and analysis code. |

**Proposal abstract:**

> This study investigates how model choice, explicit generation rules, and matched examples affect the quality of AI-generated Digital SAT-style reading questions. We propose a crossed experiment comparing four language models under four prompting conditions. Independent blinded raters will assess answer correctness, answer uniqueness, authenticity, distractor quality, and usability. Automated measurements will characterize output failures, source overlap, and computational cost. The primary outcome will be the proportion of generation attempts producing questions usable without substantive revision. A secondary analysis will examine whether automated reviewers identify defects recognized by human experts. The study will distinguish perceived difficulty and authenticity from psychometric properties requiring student-response data.

## 5. Research direction catalog

Deduplicated and grouped from both drafts. Tags: **[on-disk data]** = data or tooling already exists; **[Paper A corpus]** = designed as a follow-up on the generated corpus and its ratings; **[students + IRB]** = requires student recruitment and ethics review; **[math pipeline]** = depends on the math generation pipeline; **[low priority]**.

### 5.1 Generation and prompting

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Retrieval strategy** [Paper A corpus] | Compare no examples; fixed examples; random examples; skill-matched examples; skill-plus-difficulty (taxonomy) matched examples; matched examples with source rotation. | Usability, schema compliance, alignment, copying, diversity, tokens, latency. Which example-selection method earns its additional cost. Extends distractor-generation research finding advantages from retrieved examples over static and zero-shot prompting [Bitew et al., arXiv:2307.16338](https://arxiv.org/abs/2307.16338); the DSAT-specific extension isolates the value of taxonomy and failure-mode annotations. |
| **Number of examples** [Paper A corpus] | Generate with 0, 1, 3, and 5 examples while holding the target task fixed. | Quality improvement per added input token, plus source dependence. Find where extra examples stop helping. |
| **Annotation-conditioned generation** [Paper A corpus] | Give models examples alone; examples with skill/difficulty labels; or examples with detailed reasoning and distractor annotations. | Target adherence and usable yield. Isolates the value of the annotation work already completed. |
| **Iterative critique and revision** [Paper A corpus] | Preserve versions after 0, 1, 2, and 3 revision rounds; compare self-critique with external and multiple critics; repeated revision until threshold; human-edited final version. | Defects repaired, new defects introduced, authenticity changes, marginal cost. Does revision improve questions or merely change them — and does repeated critique plateau or damage items? Recent multi-agent work makes this less novel unless the experimental controls are unusually strong. |
| **Rulebook ablation** [Paper A corpus] | Compare full rules; minus selected sections (section-dropout); skill-specific modules; a concise summary; no rules. Grammar v8 = 6,994 lines. | Marginal value per section and the context-cost curve. Turns "rules vs no rules" into "which rules, at what token price." |
| **Model size and quantization** [Paper A corpus] | Compare sizes within a family, or different quantizations of the same checkpoint, under matched conditions. | Usability, specific error types, memory, runtime, and energy if measured. Establishes a practical local-model quality frontier. |
| **Repeated-run reliability** [Paper A corpus] | Repeat identical generation specifications across runs and dates with frozen settings where possible. | Variance in quality, failure frequency, and stability of model rankings. Shows how dependable a reported average actually is. |
| **Robustness to irrelevant changes** [Paper A corpus] | Create human-checked equivalent versions changing names, harmless wording, option order, or formatting; remap answer keys correctly. | Answer consistency and reviewer-verdict changes. Identifies models relying on superficial cues. |

### 5.2 Distractors and misconceptions

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Misconception-based distractors** [Paper A corpus; students for selection data] | Compare generic wrong answers against distractors assigned specific failure mechanisms from the project's taxonomy: punctuation-boundary confusion, agreement errors, modifier attachment, transition-logic mistakes, evidence-selection errors. | Expert plausibility, uniqueness, grammaticality, misconception alignment; with students, selection frequencies by ability. Best narrow educational contribution — easier to explain than an entire generation pipeline. |
| **Trap taxonomy → distractor attractiveness** [students + IRB] | Does syntactic-trap type predict which distractor students choose, and can an LLM predict it? `QuestionOption` carries distractor metadata; `UserProgress` records `missed_syntactic_trap_key`. | With a few hundred student responses. Park for now; design logging now so it is free later. |

### 5.3 Review and quality control

Paper B (§2.2) covers reviewer reliability, self-preference, and diversity as its core. The following extend it:

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Selective human review / cost-efficient gate** [Paper A corpus] | Compare reviewing everything with policies that send only uncertain or disputed items to humans. Policy ladder: one small local judge; one frontier judge; three-judge ensemble; cheap-then-expensive cascade; disagreement-triggered escalation; all-human review. Tune on development specifications, test on untouched ones. | The cheapest review policy that catches at least 95% of human-rejected questions; human-review fraction and defect rate among automatically accepted items at a stated error tolerance. The DB already records tokens and latency. Report local-model cost in wall-clock / GPU-seconds / energy, not dollar estimates. |
| **Math as a verifiable oracle for judge calibration** [math pipeline] | Generate math items whose correctness is checkable by a symbolic solver; have LLM judges score correctness; calibrate against executable ground truth; test whether judge calibration transfers to verbal items. | Replaces "agreement with humans" with "agreement with truth" for one dimension — the strongest methodological extension of the judge paper. Depends on the math pipeline being built. |

### 5.4 Answer keys and explanations [on-disk data]

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Answer-key error detection via solver disagreement** | Use disagreement among N independent LLM solvers to flag suspect keys; experts audit flagged items plus a random unflagged sample. | Precision and missed-error estimates; auditing only flagged items cannot establish recall. Gold = 1,438 official items; test set = crackap 1,285. Evidence on disk already shows wrong keys: LLM-written explanation docs with bad keys, Codex-vs-PDF disagreements on 2024 PT1, one item disagreeing across three test versions. No new generation; no raters beyond adjudicating flagged items. |
| **Explanation reliability and verification** | Ask models to explain established questions; evaluate the key, supporting logic, and rejection of each distractor separately. Then test whether a cheap second-model verifier pass catches errors. | Explanation error rate by model and type: wrong key; right key with wrong reasoning; hallucinated rule. Invented rules, unsupported claims, verifier detection rates. Short-paper scope; data on disk. |

### 5.5 Annotations and taxonomy [mostly on-disk data]

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Auto-annotation reliability against an expert taxonomy** | Compare LLM-generated skill, focus, trap, and evidence-span labels with independent expert annotations. | Per-label precision/recall, confusion matrices, agreement, invalid vocabulary emissions. Assets: 49 vocabularies / 632 entries; 1,438 annotated items; amendment queue. Which labels are reliable vs noisy; whether unknown-key emission rate predicts annotation error; whether ontology completeness improves across amendment rounds — the amendment-contract system is a longitudinal observable few others have. |

### 5.6 Difficulty and psychometrics

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Difficulty control** [expert ratings first; students for calibration] | Generate matched easy, medium, and hard items across models; blinded expert ratings, then administer to students. | Whether observed difficulty follows the requested ordering, with uncertainty and ability adjustment. Metrics: expert ratings, response accuracy, response time, point-biserial discrimination, Rasch/2PL parameters. Without student responses, call the outcome "perceived difficulty," not psychometric difficulty. Recent work reports weak-to-moderate LLM performance predicting empirical difficulty and particularly weak performance for discrimination, so synthetic solver responses must not be treated as ground truth [difficulty, arXiv:2607.28634](https://arxiv.org/abs/2607.28634); [discrimination, arXiv:2606.18709](https://arxiv.org/abs/2606.18709). Potentially strongest scientifically, hardest operationally. |
| **Psychometric evaluation of generated items** [students + IRB] | Collect real student responses to screened items. | Proportion correct, response time, selection frequency for every distractor, corrected item–total correlation, and IRT parameters when sample and design support them. Isley et al.'s field study used nearly 1,700 students and IRT to evaluate AI-generated exam questions — it illustrates the additional evidence required for psychometric claims, and its findings do not automatically transfer to DSAT items [arXiv:2508.08314](https://arxiv.org/abs/2508.08314). |
| **Item Turing test (official-or-generated discrimination)** [Paper A corpus] | Blinded "official or generated?" classification by humans and LLMs on balanced, matched items, with confidence ratings; correlate detectability with quality ratings. | Detectability is only one aspect of realism: near-chance classification does not establish equal correctness, equal difficulty, or equivalent educational value. Record whether raters recognize previously seen official items. Cheap on the same corpus; one intuitive headline number; a sanity check on "SAT fidelity." Official text stays private to raters; publish aggregates only. |

### 5.7 Originality and leakage

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Source dependence and originality** [Paper A corpus] | Vary retrieval strategy, example count, and generation settings (including temperature); compare outputs against source examples and the broader accessible corpus. | Normalized n-gram overlap, longest common substring, embedding similarity, passage/stem/option-specific comparisons, structural reuse, topic diversity, and blinded human leakage judgments. Similarity alone does not prove memorization or infringement. Check against the crackap corpus too, not only official items — 669 of 1,285 unmatched items show third-party prep content is a second leakage surface. The system already records source lineage and runs official-overlap checks. Do not publish official question text; publish aggregate measurements, identifiers, hashes, and generated artifacts that pass legal review. |

### 5.8 Students and learning [students + IRB]

These directions require recruitment, consent, privacy protections, and applicable institutional ethics review.

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **Solver accuracy vs writing quality** [Paper A corpus] | Have each model solve a common held-out bank and generate questions from separate specifications. | Per-skill solver accuracy versus generation quality. With only four models, treat the relationship as exploratory. |
| **Learning effectiveness** | Randomly assign students to quality-screened generated practice or a matched comparison, holding practice time and feedback constant. | Improvement on an independent post-test and delayed retention test. Tests learning rather than resemblance. |
| **Personalized practice selection** | Compare random selection, skill-based selection, and the program's weakness/trap-informed policy using comparable item pools. | Learning gains per practice minute and retention. Simulations can test mechanics (see student simulation below); a student experiment is needed for learning claims. |
| **Fairness and accessibility** | Examine expert-flagged cultural assumptions and unnecessary language demands; with adequate student samples, compare item functioning across relevant groups at comparable ability. | Accessibility defects and differential item functioning. Raw subgroup accuracy differences alone do not demonstrate item bias. |
| **Human–AI authoring productivity** | Randomly assign comparable item briefs to experts writing from scratch or editing model drafts; blind review of final outputs. | Time per accepted item, revision burden, final quality. Tests whether the system improves the actual authoring workflow. |
| **Student simulation validity and offline policy evaluation** | Compare LLM-generated answer distributions with real student responses to the same items; separately, simulate IRT-based students with per-skill weaknesses and compare random / SM-2 / weakness-weighted / diagnostic-informed selection policies on learning-proxy metrics. | Agreement in item difficulty, distractor choices, and error patterns — where simulated students are useful and where they mislead. The weakness-weighted mixed practice, SM-2, and trap-taxonomy tracking already exist; the simulation needs no IRB, but state plainly that sim→real transfer is unvalidated (workshop scope or the framework section of a later student study). Recent educational-measurement work documents systematic human–chatbot response divergence using differential item functioning; artificial response patterns must not simply be assumed to represent students [EDM study](https://educationaldatamining.org/edm2026/proceedings/2026.EDM.short-papers.88/index.html). |

### 5.9 Data and infrastructure

| Direction | Experiment | Measurements and contribution |
|---|---|---|
| **PDF extraction and error propagation** [low priority] | Build a manually verified sample containing underlines, paired passages, tables, and difficult layouts; OCR → extraction → annotation across 19+ modules with duplicate detection; trace extraction errors into later annotations and explanations. | Exact text/option/span accuracy and downstream error rates. A small benchmark plus failure taxonomy; a distinct document-processing paper for a niche document-AI venue. |
| **Transfer beyond the initial task** [after method freeze] | Freeze the method, then evaluate new skills, grammar, or another assessment using appropriate experts and specifications. | Quality drop, required adaptation, and cost. Tests whether the approach generalizes beyond the original development setting. |

## 6. Optional companion paper: the systems architecture

**Superseded as a first-paper choice, preserved from `ARXIV-IDEAS.md` (scoped 2026-08-08, not started).** The ranked shortlist (§7.1) places it last; Papers A and B above carry the empirical contribution. Kept here because the architecture description is unique and the consensus-gate mechanism doubles as Paper B's subject matter.

**Working idea:** *A Consensus-Gated Pipeline for LLM-Generated Standardized Test Items*

**Framing:** Not "we built a chatbot for SAT prep." The contribution is a *content pipeline architecture* for a hard sub-problem: generating multiple-choice items that must satisfy strict psychometric/style constraints (SAT fidelity, distractor quality, no copyright leakage), with an explicit human-in-the-loop gate rather than auto-publishing LLM output.

### 6.1 What the systems paper would contribute

1. **Three-layer content model** — official exemplars → generated drafts → advisory review. Generated content stays non-authoritative (`content_origin="generated"`, `practice_status="draft"`) until explicit admin promotion: a provenance/trust architecture separating "in-context example," "candidate," and "verified."
2. **Seeding strategy** — generated items matched to official exemplars by domain/difficulty (`_select_source_question_ids_for_batch`), with source rotation across exam codes (`_rotate_source_ids`) to avoid overfitting to one source test, exclusion of recently reused sources, and full lineage tracking (`Question.generation_source_set`) with operational metadata (provider/model/seed/temperature) stripped before storage. A reproducibility-relevant design choice.
3. **Consensus-as-threshold-gate, not voting** — `compute_consensus()` is an ordered first-match-wins decision tree over pooled rubric scores (realism, SAT fidelity, distractor quality, taxonomy match, copy-risk), not majority vote. `accept_votes`/`needs_review_votes`/`reject_votes` are computed and stored but never appear in a branching condition — audit metadata, not the decision mechanism. Worth being precise about in any paper: "review swarm" sounds like voting and isn't.
4. **The honest failure mode (genuine methodological finding)** — multi-provider "independence" collapses when all named providers (`gpt-4o`, `claude-sonnet-4-6`, `ollama`) route to the same underlying local model via the LiteLLM proxy, producing near-zero disagreement and a fake-looking consensus. The team's response: shrink to one honest reviewer (`generation_review_providers="ollama"`) rather than fake independence. "Different provider names" does not imply "independent judges." Report as a finding, not a limitation — Paper B's RQ2 (§2.2) turns this into a controlled experiment.
5. **Controlled-vocabulary governance** — an amendment-contract system (`vocabulary/amendments/{pending,approved,rejected,needs_manual_patch}/`) to prevent taxonomy drift between what generation LLMs emit and what the schema/prompts accept, across 49 vocabularies / 632 active entries. Unknown keys are non-blockingly queued (`vocab_candidates.record_unknown_field`) rather than failing the pipeline; the invariant is rule-doc-body approval before vocabulary growth. (§5.5 builds the annotation-reliability study on this system.)

### 6.2 What this paper should NOT claim

- No learning-outcome or pedagogical-efficacy claims — no student outcome data exists.
- No psychometric validity claims for generated items — no eval data exists.
- Not a "3-provider swarm achieves X% agreement" paper — the live default config is a single reviewer; the multi-provider path is built but not the deployed default. State this plainly rather than let it surface as a discovered inconsistency.
- Scope is architecture/systems: closer to a workshop paper or arXiv preprint than a venue submission with results tables.

### 6.3 Grounding (as of the 2026-08-08 survey)

- Ingestion: `backend/app/routers/ingest.py`, `docs/backend/INGESTION_ARCHITECTURE.md` (canonical, code-authoritative). State machine: `pending→parsing→extracting→annotating→(overlap_checking)→validating→approved|needs_review|failed`.
- OCR: `backend/app/parsers/ocr.py::DeepSeekOCRClient`, chain `glm→deepseek→anthropic→openai→ollama`, separate HTTP client bypassing the LiteLLM proxy.
- Extraction/annotation default model: `qwen3.6:27b` via Ollama (`default_annotation_model`), not DeepSeek.
- Generation: `backend/app/routers/generate.py`, `docs/GENERATION_ARCHITECTURE.md`, `TASKS_GENERATION.md` (11 phases; now in `_deprecated/`).
- Review swarm: `backend/app/review/runner.py::run_review_swarm()`, `backend/app/prompts/review_prompt.py` (`RUBRIC_VERSION="v1"`), `backend/app/review/parser.py::REQUIRED_SCORE_KEYS` (7 dimensions, 0–10), `backend/app/review/consensus.py::compute_consensus()`.
- Live config: `backend/app/config.py` — `generation_review_providers = "ollama"` (single reviewer default; `docs/litellm.md` documents the rollback reasoning); auto-release implemented in `backend/app/review/auto_release.py` but gated off (`generation_auto_release_enabled = False`).
- Vocabulary governance: `vocabulary/master.json`, `backend/app/pipeline/validator.py`, `backend/app/pipeline/amendments.py`, `docs/backend/VOCABULARY_GOVERNANCE.md`. Amendment auto-promotion (`--promote-from-amendment`) is an acknowledged, unbuilt gap.
- Scale: rule docs — grammar v8 (6,994 lines), reading v3 (3,110 lines), review v1 (240 lines); MATH v1 (784 lines, explicitly not-yet-built extension). Backend ~31,714 LOC, 35 Alembic migrations. Generation batch sizing: default 5, max 25, max 20 pending batches. 19 official verbal PDFs ingested.

### 6.4 Scope decision before drafting

Is the paper about the whole pipeline end-to-end, or narrowed to the consensus-gate mechanism (items 3–4 above) as the core contribution, with the rest as supporting system context? The original draft's judgment: narrower scope is likely a stronger single paper; the full-pipeline version risks reading as a system report rather than a contribution with a thesis.

## 7. Ranked shortlist, sequencing, and tooling

### 7.1 Ranked shortlist

The first draft's ranking, reconciled with the merged sequencing:

1. **Judge reliability and genuine reviewer independence** — strongest and most distinctive (Paper B).
2. **Matched source retrieval versus random/static examples** — cleanest causal experiment.
3. **Cost-efficient selective review** — most engineering-oriented.
4. **Misconception-based distractor generation** — best narrow educational contribution.
5. **Difficulty control with student responses** — potentially strongest scientifically, but hardest operationally.
6. **Systems-architecture paper** — easiest, but weakest empirically; preserved in §6 as an optional workshop paper, with its own scope check favoring a narrowed consensus-gate focus. (The first draft's note: sharpen the consensus-gated systems paper into the empirical judge-reliability study above; a careful controlled experiment — including negative findings — teaches more than the size of the application.)

### 7.2 Recommended sequence

1. **Quick wins on existing data (2–4 weeks, no new generation):** answer-key error detection and explanation reliability (§5.4), plus auto-annotation reliability (§5.5). Builds the solver/verifier tooling reused later.
2. **Generation run (Paper A):** models × rules × examples (§4). Produces the benchmark corpus and human reference ratings.
3. **Judge-reliability paper (Paper B) plus the item Turing test** on the same corpus's human ratings (§2.2, §5.6).
4. **Infrastructure-reuse follow-ups:** rulebook ablation (D), retrieval / example-count / annotation-conditioned ablations, the cost-efficient selective-review gate, and difficulty control in its expert-ratings phase.
5. **Math oracle (§5.3)** once the math pipeline exists.
6. **Student studies** — learning effectiveness, personalized selection, fairness, simulation transfer, and the trap-taxonomy study (§5.8) — when student data and IRB are in place.

The first phases need no student-response collection, although expert evaluation still requires a clear research protocol. The student phase adds recruitment, consent, privacy protections, and applicable institutional ethics review.

### 7.3 Benchmark code skeleton

```text
backend/benchmark/generation_quality/
├── README.md
├── experiment.yaml
├── generate_corpus.py
├── verify_model_routes.py
├── run_judges.py
├── export_blind_ratings.py
├── import_human_ratings.py
├── analyze_agreement.py
├── analyze_calibration.py
├── analyze_cost_quality.py
├── schemas.py
└── tests/
```

### 7.4 Operational guardrails

- Start with a **20-question pilot** to expose rubric ambiguity and pipeline problems before paying for the full run; then freeze the protocol and preregister hypotheses and metrics before the main experiment.
- Preserve failures, randomize execution order across models and conditions, and never selectively replace low-quality outputs.
- If human participants — including raters or students — are recruited for publishable research, obtain an **institutional IRB determination before collecting data**, especially if any participants are minors. Until then, the benchmark can be developed entirely with generated data and researcher annotations.
- Never publish official question text; publish aggregate measurements, identifiers, hashes, and generated artifacts that pass legal review.
- Keep the two studies separate but the dataset shared: generate once, preregister Paper A and Paper B separately.