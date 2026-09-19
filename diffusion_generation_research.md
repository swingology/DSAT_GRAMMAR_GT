# Diffusion vs. Controlled Generation for DSAT Items

Status: Research report
Date: 2026-09-07
Method: Two `/deep-research` workflow runs (5 search angles each, top sources fetched, claims adversarially verified by 3-vote), followed by a comparison written against the current generation pipeline in this repo.

## Question

If the official DSAT question bank (~1,700 annotated items) is vectorized, can a seed of those vectors plus a diffusion model produce highly controlled new questions that match a target profile: question family, difficulty, writing style, distractor types, and reasoning traps?

## Current pipeline (for reference)

- Bank: ~1,700 official items, each with `annotation_jsonb` carrying categorical features (`skill_family_key`, `stem_type_key`, `difficulty_overall`, per-option `distractor_type_key` / `plausibility_source_key`, `reasoning_trap_key`, `solver_pattern_key`, register, tone).
- Generation: `POST /generate/questions` with a 5-phase prompt (`backend/app/prompts/generate_prompt.py`, `rule_modules.py`), seeded by `source_question_ids` / `derived_from_question_id`, followed by a post-generation review swarm and admin approval inbox.
- Observed: seeding from a matching official question produces tight distractors (confirmed in prior sessions).

---

## 1. Controllable item generation with LLMs

Deep-research run 1. 6 search angles, 23 sources fetched, 62 claims extracted, 25 verified by 3-vote adversarial panel, 22 confirmed, 3 refuted, 8 findings after semantic merge.

### 1.1 Prompting frontier models already clears the quality bar

**Confidence: high.** Zero-shot and few-shot prompting of frontier models (GPT-4 class) produces reading-comprehension MCQs that human raters judge acceptable, with no fine-tuning. The gap between frontier and mid-tier open models is large and consistent (GPT-4 far above Llama 2). Two independent studies also found that having a model attempt to answer its own generated item is the automatic evaluation signal that best tracks human judgment, with GPT-4 as the judge aligning closest.

- READI @ LREC-COLING 2024, multilingual MCRC generation: <https://aclanthology.org/2024.readi-1.3/>
- German L2 MCRC study: <https://arxiv.org/html/2404.07720v1>

Implication for this repo: the current prompting-plus-review-swarm architecture is on the evidenced path, not a stopgap.

### 1.2 The real weakness is misconception targeting, not fluency

**Confidence: high.** LLMs reliably produce distractors that are *technically valid* but systematically fail to capture the specific misconceptions and error patterns real students produce. This is the single most replicated negative finding in the area, holding across independent studies and model generations from 2024 into 2026.

- Feng, Lee, McNichols et al., NAACL 2024 Findings: <https://arxiv.org/abs/2404.02124>
- Corroborated by ICER 2025 work on programming distractors and later arXiv work modeling incorrect student reasoning.

Implication: this is exactly what the `distractor_type_key` / `reasoning_trap_key` / `plausibility_source_key` annotations encode. Explicitly naming the misconception per option is a direct countermeasure to the documented failure mode.

### 1.3 Retrieval seeding helps, but unevenly

**Confidence: medium.** k-NN exemplar retrieval beats random exemplar selection for distractor generation, but gains are strongly dataset-dependent. F1@3 rose substantially on MCQL (19.06 to 24.44) and MedQA (11.90 to 15.08), yet only 0.1 to 1.4 points on MCQ, SciQ, and ARC-Easy/Challenge. Chain-of-thought rationale augmentation gave mixed results on automatic metrics while improving human-rated interpretability.

- <https://arxiv.org/pdf/2604.17574>

Important negative result: the stronger claim from the same paper, that k-NN in-context learning substantially outperforms *fine-tuned* baselines broadly, was **refuted** on 3-vote verification (1-2 against). Do not use it to argue against fine-tuning.

### 1.4 Structured, expert-heuristic constraints beat implicit model knowledge

**Confidence: medium.** Embedding human-derived distractor-design heuristics into the generation schema, rather than relying on the model's implicit knowledge, improves distractor quality over prior LLM-only approaches. This is the most direct published support for schema-constrained generation that assigns each option an explicit design role.

- ICCE 2025: <https://library.apsce.net/index.php/ICCE/article/view/5928>
- Single-paper, author-reported comparison; not independently replicated.

### 1.5 Fine-tuning and distillation are viable, and can beat bigger models

**Confidence: medium.** A distilled Bart-base model with roughly 200x fewer parameters, trained with two-stage dual-task training plus counterfactual contrastive decoding, surpassed GPT-3.5-turbo on distractor quality without human-annotated distractor training data.

- Qu, Sun, Wu, ACL 2024 Findings: <https://arxiv.org/pdf/2406.01306>
- Single-paper result, partly reliant on automatic metrics.

### 1.6 LLM-judge verifier loops are precise

**Confidence: medium.** Purpose-built LLM-judge validators for exam-item quality and answer-key validity were stress-tested across 17 commercial and open-source models on both clean and deliberately defective items. The largest and most recent models are highly precise validators, meaning few false alarms, supporting consensus-review pipelines.

- ACM SAC 2026: <https://doi.org/10.1145/3748522.3779926>

### 1.7 Difficulty prediction works at rank level but is miscalibrated at the extremes

**Confidence: high.** This is the most consequential finding for any pipeline that promises to hit a target difficulty tier. Predictions compress toward the middle of the scale: the easiest items are overpredicted as harder, the hardest underpredicted as easier. Rank correlation stays decent while absolute calibration does not.

| Metric | Value | Source |
|---|---|---|
| BEA 2024 best difficulty RMSE | 0.308 | BEA 2024 shared task |
| BEA 2024 best response-time RMSE | 27.474 | BEA 2024 shared task |
| Easiest-item overprediction bias | +1.21 | BEA 2026 vocabulary task |
| Hardest-item underprediction bias | -0.30 | BEA 2026 vocabulary task |
| Kendall tau (rank agreement) | ~0.63-0.65 | BEA 2026 vocabulary task |

Response time is consistently easier to predict than difficulty. One team found simpler PCA-based linear models (Lasso, random forest) outperformed complex language-model ensembles.

- <https://aclanthology.org/2024.bea-1.49/>
- <https://aclanthology.org/2024.bea-1.43/>
- <https://arxiv.org/html/2606.24501>

### 1.8 Synthetic item characteristic curves: promising, not yet proven

**Confidence: low.** A January 2026 preprint fine-tunes decoder LLMs with LoRA (Qwen-3, 1.7B to 32B) to generate simulated MCQ responses conditioned on discrete student-ability descriptors, then backs out IRT difficulty and discrimination from the simulated response curve, avoiding human field testing. Demonstrated on Grade-6 ELA items plus BEA 2024 data.

- <https://arxiv.org/pdf/2601.02580>
- Two stronger claims from this paper, on specific correlation/RMSE figures beating published baselines and on the authors' own reliability characterization, were **refuted** on verification. Only the method description is supported.

### 1.9 Claims that failed verification

Three claims were killed by 1-2 votes and are excluded from the findings above:

1. That k-NN in-context learning substantially outperforms fine-tuned distractor baselines across six benchmarks.
2. That a specific Qwen-8B model beat published BEA baselines at Pearson 0.381 / RMSE 0.288.
3. That the synthetic-ICC authors described their correlations as only "modest" and "not yet reliable."

### 1.10 Caveats on this section

Most difficulty-calibration evidence comes from medical-licensing or vocabulary items, not SAT or GRE reading items, so application to DSAT Reading and Writing is by analogy rather than direct replication. Several results (distillation beating GPT-3.5, expert-heuristic distractors beating priors) are single-study and author-reported.

Critically: **no source in this evidence set addresses LoRA fine-tuning conditioned on a full structured annotation JSON** covering question family, stem type, per-option distractor type, reasoning trap, and register as one end-to-end recipe. The evidence supports each component separately. It does not validate the unified pipeline this repo would build.

### 1.11 Open questions the literature does not answer

- Has anyone fine-tuned on a full multi-attribute annotation schema jointly, rather than one label dimension at a time?
- What is the minimum labeled bank size before LoRA beats retrieval-augmented few-shot for multi-attribute categorical conditioning? Is ~1,700 enough?
- Is there published evidence on embedding-based novelty detection specifically for generated MCQs, as opposed to open-ended text?
- Does the difficulty-miscalibration pattern generalize to verbal/reading items, or is it partly an artifact of the medical and vocabulary domains studied?

---

## 2. Text diffusion: state of the art

Deep-research run 2. 5 search angles, 21 sources fetched, 83 claims extracted, 25 verified by 3-vote panel, 22 confirmed, 3 refuted, 6 findings after merge.

### 2.1 The seed-vector idea is directly refuted

**Confidence: high.** This is the finding that answers the original question most directly.

Embedding-to-text inversion (vec2text and successors ZSInvert, MultiVec2Text) recovers text with high fidelity, up to 92% exact recovery and BLEU 97, **but only at short lengths**. The models are trained and optimized for sequences of roughly 32 tokens and work best on lowercase text. Quality degrades sharply beyond that, requiring retraining or chunk-and-concatenate workarounds. Zero-shot methods remove the need to train per embedding space but do not fix the length ceiling.

A DSAT item is 150 to 250 words, roughly 200 to 350 tokens, which is six to ten times past the regime where inversion is known to work.

More decisively, the claim that **averaged or interpolated multi-document embeddings can still be decoded into usable text was explicitly checked and refuted by a 0-3 vote.** Blending the embeddings of several source questions and decoding the result is not a supported operation. The intuition that you can average question vectors and read a new question out the other side does not hold.

- <https://arxiv.org/pdf/2310.06816>
- <https://arxiv.org/pdf/2504.00147>
- <https://github.com/siebeniris/MultiVec2Text>
- <https://aclanthology.org/2024.acl-long.422.pdf>
- <https://arxiv.org/pdf/2607.01276>

### 2.2 Pretraining scale dwarfs a 1,700-item fine-tune

**Confidence: high.**

| Model | Family | Pretraining scale |
|---|---|---|
| LLaDA | discrete/masked | 2.3T tokens |
| MDLM | discrete/masked | ~622B tokens (524B independently computed) |
| Dream-7B | discrete/masked | 580B tokens, adapted from Qwen2.5-7B |
| SSD-LM | continuous/simplex | 123B tokens |
| D3PM | discrete | 65B tokens |
| LD4LG | latent | 5.2M sentence pairs |

Against 65 billion to 2.3 trillion pretraining tokens, a 1,700-example fine-tune is a vanishingly small adaptation signal. Notably, several recent models (DiffuGPT, DiffuLLaMA, Dream-7B) are adapted *from autoregressive checkpoints* rather than trained from scratch, with adaptation matching or exceeding from-scratch training at similar compute. The field is converging toward AR initialization, not away from it.

- <https://arxiv.org/html/2508.10875v1>
- <https://arxiv.org/html/2508.15487v1>
- <https://github.com/kuleshov-group/mdlm>

### 2.3 Checkpoints exist, but none on structured educational text

**Confidence: medium.** Pretrained checkpoints are publicly available in both families: discrete (MDLM's `kuleshov-group/mdlm-owt` on HuggingFace, LLaDA and Dream-7B open weights) and continuous (Diffusion-LM, SSD-LM). None were trained on long structured educational or test-item text. The domain gap would have to be closed entirely by your 1,700 examples.

### 2.4 Control mechanisms are real and are the genuine appeal

**Confidence: high.** The literature converges on a consistent taxonomy:

- **Classifier guidance.** An auxiliary classifier's gradients steer generation. Diffusion-LM does this in continuous latent space, enabling plug-and-play control without retraining the base model. SSD-LM reintroduces off-the-shelf classifiers in vocabulary-simplex space.
- **Classifier-free guidance.** One model trained with and without conditioning, combined at inference.
- **Reward guidance and EDLM.**
- **DINGO**, DFA-based dynamic programming that *guarantees* hard structural constraint satisfaction.

This is the strongest argument for diffusion. Plug-and-play attribute control without retraining is genuinely something autoregressive models do less cleanly, and DINGO-style guaranteed constraint satisfaction is attractive for enforcing a four-option schema.

- <https://arxiv.org/html/2508.10875v1>, <https://arxiv.org/pdf/2205.14217>, <https://arxiv.org/pdf/2210.17432>, <https://arxiv.org/pdf/2506.13759>

### 2.5 Quality comparisons are against GPT-2, not frontier models

**Confidence: medium**, split 2-1 on sub-claims. SSD-LM matches or outperforms GPT-2-scale AR models on quality and diversity for unconstrained generation. MDLM reaches state of the art perplexity among diffusion models, closing but not eliminating the AR gap (23.00 vs 20.86 on LM1B).

The critical gap: **no source reports diffusion beating strong modern AR LLMs on long-form, multi-part, factually-grounded structured text.** Every comparison found is against GPT-2 or against other diffusion models. The true gap to a frontier model on a passage-plus-question-plus-options item is likely larger than these benchmarks suggest.

### 2.6 Commercial diffusion LLMs are a speed play

**Confidence: high.** Mercury and Gemini Diffusion achieve roughly 10x faster decoding, around 1000 tokens/sec, at comparable quality. Third-party benchmarking by Artificial Analysis independently confirmed Mercury's throughput and near-parity code and math quality.

But this is demonstrated on code and math, not controllable long-form educational content. A vendor claim that Mercury beats Claude 4.5 Haiku on general quality was **refuted 0-3**, indicating the quality edge is benchmark-specific rather than general.

- <https://arxiv.org/pdf/2506.13759>, <https://www.inceptionlabs.ai/blog/mercury-refreshed>, <https://arxiv.org/pdf/2506.17298>

### 2.7 Caveats on this section

No source directly measured hallucination or factual-error rates for diffusion-generated passages over 100 words, so the factual-accuracy conclusion is inferred from architecture and training scale rather than measured. MDLM's exact token count has a minor unresolved discrepancy (622B claimed vs 524B computed) that does not affect the conclusion. This is a fast-moving area and commercial benchmarks in particular may shift.

### 2.8 Open questions

- Has any diffusion LM been fine-tuned end-to-end on a small (1k to 5k) labeled dataset with multi-attribute categorical conditioning for long structured documents? No such study surfaced.
- What is the practical minimum fine-tune size for MDLM/LLaDA/Dream-style models given their pretraining scale?
- Do any inversion methods beyond 32 to 128 tokens reach quality sufficient for a 150 to 250 word item?
- No direct head-to-head between LoRA fine-tuning a modern AR LLM and any diffusion approach on this exact task exists in the surveyed literature.

---

## 3. Pro and con comparison

Two candidate architectures for generating a new DSAT item that matches a target feature profile:

- **Approach A.** Annotation-conditioned autoregressive LLM: retrieval-seeded exemplars, schema-constrained output assigning each option a distractor role, verifier/judge loop, optional LoRA fine-tune on the annotated bank.
- **Approach B.** Text diffusion seeded from embeddings of the item bank, with classifier or classifier-free guidance on the categorical attributes.

### 3.1 Head to head

| Dimension | A: Annotation-conditioned AR LLM | B: Text diffusion from embeddings |
|---|---|---|
| Control over categorical features | Strong. Attributes passed as explicit schema fields; expert-heuristic constraints measurably improve distractor quality (1.4) | Strong in principle. Classifier guidance and CFG are mature; DINGO guarantees hard constraints (2.4) |
| Seeding from existing questions | Works. k-NN retrieval improves over random exemplars, unevenly (1.3) | **Refuted.** Averaged/interpolated embeddings do not decode to usable text, 0-3 vote (2.1) |
| Reconstructing an item from a vector | Not needed; vectors used for retrieval only | **Blocked.** Inversion caps near 32 tokens; a DSAT item is 200-350 (2.1) |
| Data needed | 1,700 annotated items is ample for retrieval and few-shot; adequate for LoRA | 1,700 vs 65B-2.3T pretraining tokens. Vanishingly small (2.2) |
| Domain fit of available checkpoints | Frontier models already produce acceptable MCQs zero-shot (1.1) | No checkpoint trained on structured educational text (2.3) |
| Long-form coherence (>100 words) | Proven at frontier scale | Unproven. All comparisons are vs GPT-2 or other diffusion models (2.5) |
| Factual accuracy of passages | Frontier-model baseline; verifiable by judge loop | Not measured by any source for >100-word passages (2.7) |
| Answer-key validity | LLM judges are precise validators (1.6); content validity remains weakest dimension | No published verifier tooling for diffusion item output |
| Difficulty targeting | Miscalibrated at extremes, compresses to middle (1.7). Applies to both approaches | Same problem, plus no published difficulty-conditioned diffusion for items |
| Maturity / tooling | Mature. LoRA, structured output, judge frameworks all production-grade | Research-grade. No small-data multi-attribute study exists (2.8) |
| Speed | Standard AR latency | ~10x faster decode, but demonstrated on code/math only (2.6) |
| Fit with this repo | Direct. Extends the existing 5-phase prompt, review swarm, `derived_from_question_id` lineage | Would require a parallel stack with no reuse of current pipeline |

### 3.2 Where diffusion genuinely wins

Two advantages are real and should not be dismissed:

1. **Plug-and-play attribute control without retraining the base model.** Classifier guidance in latent space lets you add a new controlled attribute by training a small classifier, not by re-tuning the generator.
2. **Guaranteed hard-constraint satisfaction.** DINGO-style DFA-constrained decoding provably satisfies structural constraints, which is stronger than schema prompting, which merely requests them.

If the bank were 100x larger and the items were short, the calculus would be different.

### 3.3 Where it fails for this specific case

The seed-vector premise is the part that breaks. The idea depends on two operations that the evidence does not support: inverting an embedding back to a faithful 200-350 token item, and blending several item embeddings into a meaningful new point. Inversion is documented to work near 32 tokens and to degrade sharply past it. Embedding averaging was directly tested and refuted.

Layered on top: 1,700 examples against a 65B-to-2.3T-token pretrained model is not enough signal to teach DSAT conventions, and no available checkpoint has seen structured educational text.

### 3.4 Recommendation

**Build Approach A. Use vectors for retrieval and evaluation, not as a generative seed.**

Concretely, in priority order:

1. **Keep and sharpen schema-constrained generation.** Require each option to carry its `distractor_type_key` and `plausibility_source_key` explicitly. This is the direct countermeasure to the most replicated failure in the literature, that LLM distractors are valid but miss real student misconceptions (1.2), and expert-heuristic constraints are the best-evidenced quality lever (1.4).
2. **Embed the bank for retrieval, not decoding.** Nearest-neighbor exemplar seeding is evidenced to help (1.3) and is what `source_question_ids` already does. Add an embedding-based novelty gate so generated items that land too close to an existing item are rejected.
3. **Keep the review swarm.** LLM judges are precise validators of item quality and answer keys (1.6). Content validity is their weakest dimension, so keep admin approval in the loop.
4. **Treat difficulty as the least reliable control.** The compression-to-the-middle pattern (1.7) means a request for a hard item will tend to land mid-range. Validate difficulty against student response data rather than trusting the label. This is the single most important caveat in the whole report.
5. **Consider LoRA only if prompting plateaus.** Annotation JSON as prompt, item as completion, on the 1,700 items. Distillation into a small model beat GPT-3.5 on distractor quality (1.5), so this path is real. But note the literature has never validated a full multi-attribute annotation schema end to end (1.10), so it would be novel work.

### 3.5 What the embedding vectors are actually good for

- **Exemplar retrieval.** Nearest neighbors to a target profile become few-shot exemplars.
- **Novelty gating.** Reject generated items that fall too close to an existing bank item.
- **Difficulty regression.** Train a small model from embedding to difficulty tier as a second opinion, mindful that rank correlation is decent while absolute calibration is not.
- **Landing-zone checks.** Confirm a generated item falls inside the intended cluster for its family and style.

None of these require inverting a vector back into text, which is exactly why they work.

## Sources

**Section 1, controllable item generation**

- <https://aclanthology.org/2024.readi-1.3/> — multilingual MCRC generation, READI @ LREC-COLING 2024
- <https://arxiv.org/html/2404.07720v1> — German L2 MCRC generation and evaluation
- <https://arxiv.org/abs/2404.02124> — distractor generation, misconception gap, NAACL 2024 Findings
- <https://arxiv.org/pdf/2604.17574> — k-NN retrieval and CoT for distractor generation
- <https://arxiv.org/pdf/2406.01306> — unsupervised distillation for distractor generation, ACL 2024 Findings
- <https://doi.org/10.1145/3748522.3779926> — LLM-judge exam-item validators, ACM SAC 2026
- <https://library.apsce.net/index.php/ICCE/article/view/5928> — expert-informed distractor heuristics, ICCE 2025
- <https://aclanthology.org/2024.bea-1.49/>, <https://aclanthology.org/2024.bea-1.43/> — BEA 2024 difficulty/response-time shared task
- <https://aclanthology.org/2026.bea-1.71/>, <https://arxiv.org/html/2606.24501> — BEA 2026 vocabulary difficulty, miscalibration
- <https://arxiv.org/pdf/2601.02580> — synthetic ICC / IRT simulation via LoRA
- <https://arxiv.org/abs/2510.27313> — novelty and diversity in generated items
- <https://arxiv.org/html/2512.04106v1> — retrieval-augmented exemplar seeding

**Section 2, text diffusion**

- <https://arxiv.org/html/2508.10875v1>, <https://arxiv.org/pdf/2506.13759> — diffusion LM surveys
- <https://arxiv.org/pdf/2205.14217> — Diffusion-LM
- <https://arxiv.org/pdf/2210.17432> — SSD-LM
- <https://github.com/kuleshov-group/mdlm> — MDLM
- <https://arxiv.org/html/2508.15487v1> — Dream 7B
- <https://arxiv.org/pdf/2310.06816> — vec2text
- <https://arxiv.org/pdf/2504.00147>, <https://github.com/siebeniris/MultiVec2Text> — inversion successors
- <https://aclanthology.org/2024.acl-long.422.pdf>, <https://arxiv.org/pdf/2607.01276> — inversion limits, embedding averaging
- <https://www.inceptionlabs.ai/blog/mercury-refreshed>, <https://arxiv.org/pdf/2506.17298> — Mercury

## Method note

Both sections come from the `/deep-research` workflow: question decomposed into search angles, parallel web search, source fetch with URL dedup, falsifiable claim extraction, then 3-vote adversarial verification per claim requiring 2 of 3 to refute. Orchestrated by Fable, subagents on Sonnet.

| Run | Angles | Sources | Claims extracted | Verified | Confirmed | Refuted | Findings | Agents |
|---|---|---|---|---|---|---|---|---|
| 1, item generation | 6 | 23 | 62 | 25 | 22 | 3 | 8 | 106 |
| 2, text diffusion | 5 | 21 | 83 | 25 | 22 | 3 | 6 | 103 |

An earlier attempt at both runs in parallel exhausted the session rate limit and lost every verification panel. Re-run serially with Sonnet subagents, both completed with zero agent errors.
