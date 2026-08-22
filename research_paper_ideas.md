

• Your strongest paper is not “I built an AI SAT generator.” That is a software project. A stronger research contribution is:

  > Can LLM reviewers reliably identify flawed AI-generated standardized-test questions, and can a calibrated review gate reduce human review effort without allowing more bad questions
  > through?

  This fits your existing system extremely well and produces measurable, potentially publishable results.

  ## Why this is the best direction

  Your repository already contains:

  - generation batches and per-question provenance;
  - official-example retrieval and source rotation;
  - seven-dimensional LLM review scores;
  - deterministic consensus logic;
  - overlap/copy-risk detection;
  - human approve/reject decisions;
  - token counts and reviewer latency.

  The relevant foundations are already in docs/GENERATION_ARCHITECTURE.md, backend/app/review/runner.py, backend/app/review/consensus.py, and backend/app/prompts/review_prompt.py.

  However, I checked the live database: it currently has 1,438 active official questions but zero generation batches, generated questions, review results, or consensus results. Therefore,
  you have excellent experimental infrastructure but do not yet have research data. The next step should be a deliberately designed benchmark, not analysis of existing results.

  ## Recommended paper

  Possible title:

  Independent or Illusory? Evaluating LLM Judges for Quality Control of AI-Generated Standardized-Test Items

  Research questions:

  1. How closely do individual LLM reviewers agree with blinded human reviewers?
  2. Do genuinely different model families outperform multiple provider names routed to the same underlying model?
  3. Does a model score questions produced by itself more favorably?
  4. Which rubric dimensions are reliably judged—correctness, fidelity, distractor quality, difficulty, or copy risk?
  5. Can uncertain cases be sent to humans while confidently safe or unsafe cases are handled automatically?
  6. What are the quality–cost–latency tradeoffs of one judge, several judges, and a selective gate?

  The provider-diversity question is particularly relevant because your project previously discovered that nominally different providers could route to the same local model. That is a
  genuine methodological issue, not merely an implementation bug.

  ### Suggested experiment

  Generate approximately 200–300 balanced questions:

  - grammar and reading;
  - easy, medium, and hard targets;
  - multiple question families;
  - at least three generator models;
  - matched prompts and source examples;
  - several deterministic seeds.

  Have three blinded human raters score each item using your existing seven dimensions:

  - realism;
  - SAT-style fidelity;
  - difficulty match;
  - distractor quality;
  - taxonomy match;
  - explanation quality;
  - copy risk.

  Do not show raters the generator or reviewer identity.

  Evaluate:

  - Single LLM judges
  - Majority voting
  - Your existing deterministic threshold gate
  - Three nominal providers sharing one base model
  - Three genuinely distinct model families
  - An uncertainty-aware gate that escalates ambiguous cases to humans

  Measurements:

   Question                   Metrics
  ━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Numeric-score agreement    ICC, Spearman correlation, MAE
  ─────────────────────────  ────────────────────────────────────────────────────────
   Verdict agreement          Macro-F1, balanced accuracy, weighted kappa
  ─────────────────────────  ────────────────────────────────────────────────────────
   Safety                     False-acceptance rate, recall of human-rejected items
  ─────────────────────────  ────────────────────────────────────────────────────────
   Calibration                Brier score, expected calibration error
  ─────────────────────────  ────────────────────────────────────────────────────────
   Reviewer diversity         Score correlation, error overlap, disagreement entropy
  ─────────────────────────  ────────────────────────────────────────────────────────
   Efficiency                 Tokens, latency, estimated cost per reviewed item
  ─────────────────────────  ────────────────────────────────────────────────────────
   Selective review           Human-review coverage versus error rate
  ─────────────────────────  ────────────────────────────────────────────────────────
   Statistical uncertainty    Bootstrap 95% confidence intervals

  Reserve part of the dataset for setting thresholds and a separate held-out portion for final evaluation. Otherwise, tuning thresholds and reporting results on the same questions will
  inflate performance.

  This direction aligns with recent work showing that AI-generated items can perform well when subjected to real psychometric evaluation—but it avoids requiring a 1,700-student field study
  for your first paper. Isley et al.’s field study (https://arxiv.org/abs/2508.08314) used student responses and item-response theory, illustrating the evidentiary bar for claims about item
  validity. Research also documents self-preference in LLM judges, which directly motivates your independence experiment. Beyond the Surface (https://aclanthology.org/2025.emnlp-main.86/) is
  a useful methodological reference.

  ## Other viable topics

  ### 1. Retrieval strategy and generation quality

  Question: Does retrieving official examples matched by skill and difficulty produce better questions than random, static, or zero-shot examples?

  Conditions:

  - no examples;
  - fixed examples;
  - randomly selected examples;
  - taxonomy-matched examples;
  - taxonomy-matched examples with source rotation.

  Measure human-rated quality, schema compliance, diversity, copy risk, tokens, and latency.

  This is highly feasible because your generator already performs matched source selection and rotation. Prior distractor-generation research found advantages from retrieved in-context
  examples over static and zero-shot prompting, giving you a solid baseline to extend. Bitew et al. (https://arxiv.org/abs/2307.16338)

  ### 2. Cost-efficient AI quality control

  Question: What is the cheapest review policy that catches at least 95% of human-rejected questions?

  Compare:

  - one small local judge;
  - one frontier judge;
  - three-judge ensemble;
  - cheap judge followed by expensive judge;
  - disagreement-triggered escalation;
  - human review of every item.

  This is practical, mathematically clean, and directly useful. Your database already records tokens and latency.

  ### 3. Can LLMs control question difficulty?

  Generate items targeting easy, medium, and hard levels, then test whether those levels are reflected in:

  - blinded expert ratings;
  - response accuracy;
  - response time;
  - point-biserial discrimination;
  - Rasch or 2PL item parameters.

  This becomes an excellent psychometrics paper if you can obtain real student responses. Without them, call the outcome “perceived difficulty,” not psychometric difficulty. Recent research
  reports weak-to-moderate LLM performance for predicting empirical difficulty and particularly weak performance for discrimination, so synthetic solver responses should not be treated as
  ground truth. Difficulty study (https://arxiv.org/abs/2607.28634), discrimination study (https://arxiv.org/abs/2606.18709)

  ### 4. Generating better distractors from student misconceptions

  Compare ordinary distractor generation against a method that explicitly models common error mechanisms:

  - punctuation-boundary confusion;
  - agreement errors;
  - modifier attachment;
  - transition-logic mistakes;
  - evidence-selection errors.

  Measure plausibility, uniqueness, grammaticality, misconception alignment, and how often students select each distractor. This is narrower and easier to explain than an entire generation
  pipeline.

  ### 5. Measuring copyright and source leakage

  Question: How do source-selection strategy, number of examples, and temperature affect copying risk?

  Use:

  - normalized n-gram overlap;
  - longest common substring;
  - embedding similarity;
  - passage/stem/option-specific comparisons;
  - blinded human leakage judgments.

  Your system already records source lineage and runs official-overlap checks. Do not publish official question text; publish aggregate measurements, identifiers, hashes, and generated
  artifacts that pass legal review.

  ### 6. Does iterative critique actually improve questions?

  Compare:

  - single-pass generation;
  - generate → critique → revise;
  - generate → multiple critics → revise;
  - repeated revision until threshold;
  - human-edited final version.

  Measure improvement relative to cost and determine whether repeated critique eventually plateaus or damages items. This is approachable, although recent multi-agent and iterative-
  generation work makes it less novel unless your experimental controls are unusually strong.

  ## My ranking

  1. LLM-judge reliability and genuine reviewer independence — strongest and most distinctive.
  2. Matched source retrieval versus random/static examples — cleanest causal experiment.
  3. Cost-efficient selective review — most engineering-oriented.
  4. Misconception-based distractor generation — best narrow educational contribution.
  5. Difficulty control with student responses — potentially strongest scientifically, but hardest operationally.
  6. Whole-pipeline architecture paper — easiest, but weakest empirically.

  Your existing ARXIV-IDEAS.md proposes a consensus-gated systems paper. I would sharpen it into the empirical judge-reliability study above. A top technical university will usually learn
  more from a carefully controlled experiment—including negative findings—than from the size of the application.

  ## Benchmark code I would build

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

  Every result row should preserve:

  - experiment and condition IDs;
  - actual resolved model—not merely provider alias;
  - prompt, rubric, and rules versions;
  - seed and temperature;
  - source-question IDs;
  - raw output hash;
  - scores and verdict;
  - tokens, latency, and estimated cost;
  - human ratings and adjudication;
  - software commit SHA.

  I recommend beginning with a 20-question pilot. That will expose rubric ambiguity and pipeline problems before spending money generating the full 200–300-item dataset. Then freeze the
  protocol, preregister the hypotheses and metrics, and run the main experiment.

  If human participants—including raters or students—are recruited for publishable research, obtain an institutional IRB determination before collecting data, especially if any participants
  are minors. Until then, the benchmark can be developed entirely with generated data and researcher annotations.

---

# Addendum (2026-08-21): Review notes and additional directions

## Review fixes for the judge-reliability plan above

1. **Rating-labor math doesn't close.** 250 items × 3 raters × 7 dimensions ≈ 5,250 ratings plus adjudication. Either cut human rating to 4 dimensions (correctness, fidelity, distractor quality, copy risk), or rate 2 dims at full N and the rest on a subsample. Run a power calculation before freezing N.
2. **Single train/held-out split on ~250 items gives wide CIs.** Use k-fold cross-validation for threshold tuning; report bootstrap CIs over folds.
3. **RQ3 (self-preference) constrains the model matrix:** every judge model must also be a generator, fully crossed. State and budget this explicitly.
4. **Define a gold-verdict protocol** for verdict-agreement metrics (majority / senior rater / discuss-to-consensus). Report human inter-rater reliability as the ceiling against which LLM judges are compared.
5. **Copy-risk must also be checked against the crackap corpus**, not only official items — 669/1285 unmatched items show third-party prep content is a second leakage surface.
6. **Local-model cost:** report wall-clock / GPU-seconds / energy, not "$" estimates.
7. **Two documents, one dataset.** `RESERACH_PAPER_TODO.md` (rules × examples × model class) should produce the generated corpus; its human ratings then feed the judge-reliability paper. Generate once, preregister the two studies separately.
8. **Stratify by item format** (passage-based reading vs standalone grammar; stimulus vs none). Judges likely behave differently across them.

## Additional paper directions (ranked by feasibility with existing assets)

### A. Solver disagreement as an answer-key error detector  — *data already on disk*
Evidence of wrong keys exists: LLM-written explanation MDs with bad keys, Codex-vs-PDF disagreements on 2024 PT1, one item disagreeing across three test versions. Question: does disagreement among N independent LLM solvers flag key errors in third-party prep items at useful precision/recall? Gold = 1,438 official items; test set = crackap 1,285. No new generation, no raters beyond adjudicating flagged items.

### B. How often are LLM explanations of official items wrong, and can a second model catch it?  — *data on disk*
Sibling of A. Measure explanation error rate by model and error type (wrong key / right key + wrong reasoning / hallucinated rule), and whether a cheap verifier pass catches them. Short-paper scope.

### C. LLM auto-annotation reliability against an expert taxonomy  — *data mostly on disk*
49 vocabularies / 632 entries, 1,438 annotated items, amendment queue. Measure kappa between LLM annotation and expert labels per vocabulary; which labels are reliable vs noisy; whether unknown-key emission rate predicts annotation error; whether ontology completeness improves across amendment rounds. The amendment-contract system is a longitudinal observable few others have.

### D. Rulebook ablation — do 7,000 lines of rules help?  — *extension of the TODO study*
Grammar v8 = 6,994 lines. Section-dropout ablation: full rules / minus section k / rule summary / none. Yields marginal value per section and the context-cost curve. Turns "rules vs no rules" into "which rules, at what token price."

### E. Generated-vs-official discrimination ("item Turing test")
Can blinded humans and LLMs distinguish generated from official items, and does detectability correlate with quality ratings? Cheap on the same corpus; one intuitive headline number; sanity check on "SAT fidelity." Official text stays private to raters; publish aggregates only.

### F. Math as a verifiable oracle for judge calibration
Math item correctness is checkable by a symbolic solver. Generate math items, have LLM judges score correctness, calibrate against executable ground truth, then test whether judge calibration transfers to verbal. Strongest methodological extension of the judge paper: replaces "agreement with humans" with "agreement with truth" for one dimension. Depends on the math pipeline being built.

### G. Offline evaluation of item-selection policies via simulated students
Weakness-weighted mixed practice, SM-2, and trap-taxonomy tracking already exist. Simulate IRT-based students with per-skill weaknesses; compare random / SM-2 / weakness-weighted / diagnostic-informed selection on learning-proxy metrics. No IRB; state plainly that sim→real transfer is unvalidated. Workshop-paper scope or the framework section of a later student study.

### H. Does the syntactic-trap taxonomy predict distractor attractiveness?
`QuestionOption` carries distractor metadata; `UserProgress` records `missed_syntactic_trap_key`. With a few hundred student responses, test whether trap type predicts chosen distractor and whether an LLM predicts it. Needs data + IRB — park it, but design logging now so it is free later.

### I. Structured-extraction benchmark for exam PDFs  — *niche, document-AI venue*
OCR → extraction → annotation with hand-verified output for 19+ modules; two-column layouts, underlined spans, figures, duplicate detection. Small benchmark + failure taxonomy. Lowest priority.

## Suggested sequencing

1. **A + B** — no new generation, 2–4 weeks, builds solver/verifier tooling reused later.
2. **Rules × examples × model generation run** (TODO doc) — produces the corpus.
3. **Judge-reliability paper (#1) + E** on that corpus's human ratings.
4. **D** and **C** as follow-ups reusing infrastructure.
5. **F** once the math pipeline exists; **G/H** when student data or IRB is in place.
