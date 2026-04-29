# Benchmark: Evaluating DSAT Grammar Question Generation Quality

## Purpose

Define a rigorous, repeatable benchmark for measuring the quality of
AI-generated DSAT Grammar (Standard English Conventions + grammar-adjacent
Expression of Ideas) questions. The benchmark must detect regressions, surface
real differences between generation strategies, and ultimately give confidence
that generated questions approach the quality of official College Board items.

---

## 1. What Exists: Landscape Review

### 1.1 Academic Benchmarks

**QGEval** (Fu et al., EMNLP 2024) — The standard NLP benchmark for question
generation evaluation. 7 dimensions (Fluency, Clarity, Conciseness, Relevance,
Consistency, Answerability, Answer Consistency) over 3,000 questions from 15
models. Key finding: no automatic metric correlates above 0.6 with human
judgment. Answerability and Answer Consistency are the hardest dimensions.
- https://arxiv.org/abs/2406.05707
- https://github.com/WeipingFu/QGEval

**EQGBench** (Stanford SCALE, 2025) — Educational question generation benchmark
with 5 dimensions (Knowledge Point Alignment, Question Type Alignment, Item
Quality, Solution Explanation Quality, Competence-Oriented Guidance). Uses
DeepSeek R1 as multi-round voting judge; 88%+ human consistency.
- https://scale.stanford.edu/ai/repository/answers-questions-eqgbench-evaluating-llms-educational-question-generation

**AGIEval** (Microsoft, NAACL 2024) — Human-centric benchmark using SAT, LSAT,
Gaokao. 8,062 questions across 20 tasks. GPT-4 scored 95% on SAT Math. Useful
as a reference for format and difficulty calibration but measures *answering*
not *generating*.
- https://github.com/ruixiangcui/AGIEval

**OpenLearnLM Benchmark** (2025) — 124K+ items across Knowledge, Skills,
Attitude (KSA) dimensions. Educational LLM evaluation, not generation-specific,
but the KSA framework is relevant for pedagogical depth assessment.
- https://arxiv.org/html/2601.13882v1

### 1.2 Evaluation Methodologies

**LLM-as-Judge** — Dominant approach across all recent work. A frontier LLM
scores generated questions against a multi-criteria rubric. G-EVAL (CoT
scoring) achieves the highest correlation with human judges. Key risk: judge
bias (systematic differences between evaluator models).

**24-Criterion Rubric** (Drexel SAT Math study, 2026) — 6 categories with 24
specific criteria. Generated questions scored 4.64-4.89/5 on average, but TOST
equivalence testing showed strict equivalence to human-vetted items was never
achieved. Weakest areas: skill depth, cognitive engagement, difficulty
calibration.
- https://arxiv.org/pdf/2602.18891v1

**IRT-Based Evaluation** (Frontiers in AI, 2026) — Item Response Theory (3PL
model) with real student response data to measure difficulty, discrimination,
and distractor quality. Gold standard for psychometric validity but requires
large-scale student piloting (1,000+ responses per item).
- https://www.frontiersin.org/articles/10.3389/frai.2026.1692465/full

**College Board Technical Manual** — Official standard: 3PL IRT + Graded
Response Model, fixed-item calibration, DIF analysis with Mantel-Haenszel.
Distractor quality control: flag any distractor with total-score correlation
> 0.05. Parent model approach: if one child item fails, the entire parent
model is flagged.
- https://research.collegeboard.org/media/pdf/Digital%20SAT%20Suite%20of%20Assessments%20Technical%20Manual-FINAL.pdf

**D-GEN Ranking Alignment** (ACL 2025) — Novel distractor evaluation using
Spearman rank correlation (ρ = 0.99) and entropy analysis. Compares model
confidence distributions between original and generated distractors.
- https://aclanthology.org/2025.findings-acl.174/

**LLM-as-Simulated-Student** (Zelikman 2023, Liu 2025) — Use LLMs as
artificial test-takers to estimate item parameters without human piloting.
Promising for rapid iteration but not yet validated against real student data
for distractor-level analysis.

### 1.3 Key Findings Across All Research

| Finding | Consensus |
|---------|-----------|
| Surface quality (fluency, grammar) | Near-perfect across all studies (4.9+/5) |
| Distractor plausibility | Consistently the weakest dimension |
| Skill depth / cognitive engagement | Second-weakest; hard to calibrate |
| Difficulty calibration | AI tends to generate easier questions |
| Domain/skill alignment | Good overall, but fine-grained alignment is weak |
| LLM-as-Judge reliability | 85-97% human consistency, but judge bias is real |

**No existing benchmark is purpose-built for DSAT Grammar generation.** The
Drexel SAT Math study comes closest, but Grammar (SEC) has different failure
modes, taxonomy requirements, and distractor architectures than Math or Reading.

---

## 2. Proposed Benchmark Architecture

The benchmark should operate at **three tiers**, each trading cost for fidelity:

### Tier 1: Automated Rubric (CI Gate — minutes, <$1/run)

A multi-dimensional rubric scored by an LLM judge (GPT-4o or Claude Opus 4.7)
with the following dimensions and weights:

| # | Dimension | Weight | What It Measures |
|---|-----------|--------|------------------|
| 1 | **Grammar Accuracy** | 20% | Correct answer is grammatically right; distractors violate specific SEC rules |
| 2 | **Distractor Plausibility** | 20% | Each distractor is tempting for a named reason; not eliminable by ear-test |
| 3 | **Taxonomy Alignment** | 15% | grammar_role_key, grammar_focus_key, stem_type_key, stimulus_mode_key are valid and match the question |
| 4 | **Passage Quality** | 10% | Self-contained, academic register, appropriate length, no trivia dependence |
| 5 | **Stimulus-Question Fit** | 10% | The question depends on the passage; cannot be answered without it |
| 6 | **Option Homogeneity** | 10% | All options same category, register, length band, grammatical form |
| 7 | **No Technical Clues** | 10% | Correct answer not signaled by length, precision, or structural difference |
| 8 | **Difficulty Calibration** | 5% | Difficulty matches the requested level (easy/medium/hard) |

Each dimension scored 1-5. Total weighted score = 0-5. Thresholds:
- **Pass**: ≥ 4.0
- **Needs Review**: 3.0 - 3.99
- **Fail**: < 3.0

**Scoring protocol**: LLM judge receives the passage, question, options,
correct answer, and the declared taxonomy keys. It scores each dimension with
a 1-sentence justification, then produces the weighted total. Run 2 judges
independently; if scores diverge by > 0.5, run a third as tiebreaker.

### Tier 2: Structural & Psychometric Analysis (Batch — minutes, <$5/run)

Apply automated metrics that don't require human raters:

- **Distractor Ranking Alignment** (from D-GEN): Feed each option to a
  language model; verify the correct answer has the highest likelihood and
  distractors rank below it with plausible separation.

- **Entropy Analysis**: Model confidence distribution over the 4 options.
  Excessively high confidence on the correct answer suggests the distractors
  are too weak.

- **Option Length Variance**: Coefficient of variation of option lengths.
  Flag if CV > 0.25 (one option visually sticks out).

- **Taxonomy Key Validation**: Programmatically verify every taxonomy key
  against the approved ontology. Flag invalid, deprecated, or cross-domain
  keys.

- **Passage Overlap (Anti-Clone)**: Jaccard similarity against existing
  questions in the corpus. Flag if > 0.70 with any existing item.

- **Distractor-Set Overlap**: Within-item overlap between distractors. Flag
  if two distractors have cosine similarity > 0.85 (they're too similar to
  each other).

### Tier 3: Human Expert Review (Release Gate — hours, ~$50-200/run)

A structured review by a domain expert (SAT tutor or curriculum designer)
using the same 8-dimension rubric but with expert judgment. Add:

- **Pedagogical Value**: Does this question test something worth testing?
- **Official-Style Fit**: Would this question look out of place on a real DSAT?
- **Error Diagnosis Accuracy**: Are the named student failure modes realistic?
- **Overall Rating**: 1-5 holistic score.

Target: 20 questions per review batch (statistically significant sample).

### Tier 4: Real-Student Piloting (Psychometric Gate — weeks, high cost)

The gold standard, aligned with College Board methodology:

1. Embed generated questions as pretest items alongside operational questions
2. Collect 500-1,000 student responses per item
3. Fit a 3PL IRT model to estimate:
   - **a (discrimination)**: Target > 0.8
   - **b (difficulty)**: Should span -2 to +2 across the item set
   - **c (pseudo-guessing)**: Should be ~0.25 for 4-option MCQs
4. Classical distractor analysis: flag any distractor with point-biserial > 0.05
5. Compare difficulty distribution to official College Board items

---

## 3. Recommended Approach: Phased Rollout

```
Phase 1 (Now)        Tier 1 (Automated Rubric) + Tier 2 (Structural)
                     └─ Run on every generation PR. CI gate: Tier 1 ≥ 3.5.

Phase 2 (2-4 weeks)  Tier 1 calibration against human raters
                     └─ 50 questions scored by both LLM judge and expert.
                         Adjust rubric weights and thresholds based on
                         correlation analysis.

Phase 3 (1-2 months) Tier 3 (Human Expert Review)
                     └─ Monthly batch of 20-50 questions. Release gate
                         before using generated questions with students.

Phase 4 (6+ months)  Tier 4 (Real-Student Piloting)
                     └─ Partner with a tutor or classroom. Embed items
                         in practice tests. Fit IRT models.
```

---

## 4. Implementation Plan

### 4.1 Benchmark Code

Create `backend/benchmark/` with:

- `benchmark/__init__.py`
- `benchmark/rubric.py` — The 8-dimension rubric definition, scoring logic,
  aggregation, and pass/fail thresholds
- `benchmark/judge.py` — LLM judge interface (calls the configured provider
  with a structured prompt, parses scores)
- `benchmark/structural.py` — Tier 2 metrics (option length variance,
  distractor-set overlap, taxonomy validation, passage overlap)
- `benchmark/runner.py` — Orchestrator that takes a batch of generated
  questions, runs all enabled tiers, produces a report
- `benchmark/cli.py` — CLI entry point for ad-hoc evaluation
- `tests/test_benchmark.py` — Tests for the benchmark itself

### 4.2 Data Format

Each benchmarked question is a JSON object:

```json
{
  "question_id": "uuid",
  "passage_text": "...",
  "question_text": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_option_label": "A",
  "metadata": {
    "grammar_role_key": "conventions",
    "grammar_focus_key": "subject_verb_agreement",
    "stem_type_key": "complete_sentence",
    "stimulus_mode_key": "passage",
    "difficulty_overall": "medium",
    "source_exam_code": "PT8",
    "source_section_code": "sec01",
    "source_module_code": "mod01"
  }
}
```

### 4.3 Report Output

The benchmark produces a markdown report:

```markdown
# Benchmark Report: 2026-04-27

## Summary
- Questions evaluated: 20
- Tier 1 pass rate: 85% (17/20)
- Tier 2 flags: 2 (1 clone risk, 1 taxonomy violation)
- Mean weighted score: 4.12/5

## Dimension Breakdown
| Dimension | Mean | Min | Max | Flagged |
|-----------|------|-----|-----|---------|
| Grammar Accuracy       | 4.6 | 3.0 | 5.0 | 1 |
| Distractor Plausibility | 3.8 | 2.0 | 5.0 | 3 |
| Taxonomy Alignment     | 4.5 | 2.0 | 5.0 | 1 |
| ...                   | ... | ... | ... | ... |

## Per-Question Detail
- Q_001: 4.8 PASS
- Q_002: 2.9 FAIL — distractors eliminable by ear-test
- ...
```

---

## 5. Open Questions for Discussion

1. **Judge model selection**: GPT-4o vs Claude Opus 4.7 vs ensemble. Each has
   known biases. Should we run dual judges and flag disagreements?

2. **Rubric weight tuning**: The proposed weights are a starting point. Should
   Distractor Plausibility be weighted higher (its the hardest dimension)?

3. **Pass threshold**: Is ≥ 4.0/5 the right CI gate? Too strict (many PRs
   fail) or too lax (low-quality questions merge)?

4. **Reference set**: We need a held-out set of ~50 official College Board
   Grammar questions to calibrate the rubric. How do we source and curate
   these? (They're the "human baseline" for TOST equivalence testing.)

5. **Ground truth grammar rules**: The benchmark's Grammar Accuracy dimension
   depends on a ground-truth grammar rules document. The GROUND_TRUTH_GRAMMAR.md
   work feeds directly into this.

6. **Cost budget**: Tier 1 costs ~$0.05-0.10 per question with GPT-4o.
   A 20-question CI run = $1-2. A 50-question expert review = $50-200.
   What monthly budget is acceptable?

7. **What about reading questions?** This benchmark covers Grammar only.
   A Reading module would need different dimensions (evidence alignment,
   passage dependency, inference validity, etc.).

---

## References

- Fu et al., "QGEval: Benchmarking Multi-dimensional Evaluation for Question
  Generation," EMNLP 2024. https://arxiv.org/abs/2406.05707
- Isley et al., "Assessing the Quality of AI-Generated Exams," AAAI 2026.
  https://ojs.aaai.org/index.php/AAAI/article/view/41205
- An, "Orchestrating LLM Agents for Scientific Research: MCQ Generation and
  Evaluation," arXiv 2026. https://arxiv.org/pdf/2602.18891v1
- "Artificial test-takers as transformed controls: measuring SAT difficulty
  drift," Frontiers in AI, 2026.
  https://www.frontiersin.org/articles/10.3389/frai.2026.1692465/full
- College Board, "Digital SAT Suite of Assessments Technical Manual," 2024.
  https://research.collegeboard.org/media/pdf/Digital%20SAT%20Suite%20of%20Assessments%20Technical%20Manual-FINAL.pdf
- D-GEN: Automatic Distractor Generation and Evaluation, ACL 2025 Findings.
  https://aclanthology.org/2025.findings-acl.174/
- EQGBench, Stanford SCALE, 2025.
  https://scale.stanford.edu/ai/repository/answers-questions-eqgbench-evaluating-llms-educational-question-generation
- OpenLearnLM Benchmark, arXiv 2025. https://arxiv.org/html/2601.13882v1
- Bhandari et al., "Evaluating the psychometric properties of ChatGPT-generated
  questions," Computers and Education: AI, 2024.
- Liu, Bhandari & Pardos, "Leveraging LLM respondents for item evaluation,"
  British Journal of Educational Technology, 2025.
