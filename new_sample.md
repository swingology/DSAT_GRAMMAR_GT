# Source and generated DSAT sample

## Original database question

Source ID: `04fa6cf2-4b38-5863-ad69-b6cce7d405eb`  
Release year: 2024; exam: 05; section: 01; module: 02B; question: 17.

In a painting titled “The Milkmaid” by Johannes Vermeer, the artist prominently features a bread basket, milk pitcher, and bowl. Such quotidian objects, depicted in exquisite detail by Vermeer, a painter celebrated for his naturalism, _____ the daily minutiae of a seventeenth-century Dutch household.

Which choice completes the text so that it conforms to the conventions of Standard English?

- **A.** was revealing
- **B.** has revealed
- **C.** reveals
- **D.** reveal

**Correct answer: D**

**Explanation:** The subject of the second sentence is the plural noun **objects**. The intervening descriptions do not change its number. **Reveal** agrees with that subject; the other three choices use singular verb forms.

**Source metadata caveat:** The stored annotation says the passage was missing when it was annotated. The current database passage is present and reproduced above. The source was passed through the existing source-example loader, including that older annotation; it was not silently corrected in the database.

## Newly generated question

The intricate root systems of the mangrove, a tree that thrives in brackish coastal waters, ______ the shoreline against erosion.

Which choice completes the text so that it conforms to the conventions of Standard English?

- **A.** stabilizes
- **B.** stabilizing
- **C.** are stabilize
- **D.** stabilize

**Correct answer: D**

**Reviewed explanation:** The main subject is **systems**, which is plural. “Of the mangrove” is a prepositional phrase; “a tree that thrives in brackish coastal waters” supplies an appositive description of the mangrove. Neither changes the number of **systems**. **Stabilize** correctly supplies the main finite verb.

| Choice | Assessment |
|---|---|
| A. stabilizes | Singular verb; does not agree with plural **systems**. |
| B. stabilizing | Nonfinite participle; leaves the main clause without a finite verb. **Thrives** belongs to the embedded relative clause. |
| C. are stabilize | Malformed verb construction: **are** cannot combine with the bare form **stabilize** this way. |
| D. stabilize | Correct finite verb for plural **systems**. |

**Quality assessment:** D is the only defensible choice in this option set. C is conspicuously malformed, so this is a working sample, not a calibrated medium-difficulty assessment item. The model requested medium difficulty; that label has not been empirically established. The explanation above was editorially reviewed: the generation output incorrectly claimed that the hypothetical phrase “are stabilizing” would be singular. It is plural and would be grammatical, but it is not an offered choice.

## Actual method and results

- Generated on 2026-09-06 UTC on branch `RULES_REFACTOR_v3`.
- Source: one official database question, retrieved in a read-only transaction.
- Model: `deepseek-v4-pro:cloud`, through the configured Ollama endpoint `http://localhost:11434`. Ollama's model metadata resolves it to remote model `deepseek-v4-pro` at `https://ollama.com:443`; this was a cloud-backed call.
- Generation: `DSAT_GENERATION_RULES_MODE=modules`, using the existing manifest and baseline rule modules. No ontology proposal was activated.
- Annotation: a second model call through the existing ingestion-compatible annotation builder, followed by canonicalization, nullability enforcement, key sanitization, and question/completeness validation. **Modular annotation is not implemented.** OCR/extraction was unnecessary because the source already existed in the database.
- Annotation identified `agreement` / `subject_verb_agreement`, with `nearest_noun_attraction`.
- The first attempt returned reasoning without usable JSON. A retry produced an ambiguous item with multiple grammatical answers; that item was rejected during review. This final item was regenerated with explicit feedback prioritizing unique-answer correctness over artificial diversity in error labels.
- Final calls requested up to 32,768 output tokens with the Ollama adapter's `disable_thinking=True` option. Generation temperature was 0.7; annotation used the provider default. No claim is made that the cloud endpoint honored the thinking option.
- No database question was inserted or changed. This file is the deliverable.

### Machine validation

No blocking findings were returned. One review finding remains:

> `explanation`: No explanation text provided.

The model supplied reasoning, and its generation response included nested explanation fields, but the pipeline's validated merged payload did not expose the expected explanation field. The reviewed explanation above addresses readability in this file; it does not repair the pipeline's field handling. Passing structural validation alone did not detect the rejected item's multiple-answer flaw.

### Selected generation modules

- `shared/00_mode_and_schemas.md`
- `grammar/generation_core.md`
- `grammar/taxonomy.md`
- `grammar/skills/subject_verb_agreement.md`
- `grammar/examples/subject_verb_agreement.md`

Generation rule context: **73,607 characters**, including module labels and the active allowed-key block. The 65 baseline modules remain unchanged.

### Final successful call measurements

These counters cover the final generation and annotation only; they exclude the failed attempt and rejected draft and are not total run cost.

| Stage | Input tokens reported | Output tokens reported | Latency |
|---|---:|---:|---:|
| Generation | 22,533 | 5,098 | 23.66 seconds |
| Annotation | 27,185 | 5,948 | 26.47 seconds |


---

## Additional DeepSeek/Ollama run

Recorded: 2026-09-06T09:18:12.467921+00:00

Same source question: `04fa6cf2-4b38-5863-ad69-b6cce7d405eb` (the original question above). This run reused its exact saved database snapshot, including the original annotation, and the same generation specification and revision guidance as the previous successful run.

Model: `deepseek-v4-pro:cloud` via Ollama at `http://localhost:11434`; metadata identifies remote model `deepseek-v4-pro` at `https://ollama.com:443`. This is cloud inference through Ollama, not local-weight inference.

### New question

The intricate structures of a single cell, when examined under high magnification by a researcher, ______ a remarkable degree of organization.

Which choice completes the text so that it conforms to the conventions of Standard English?

- **A.** reveals
- **B.** reveal
- **C.** revealing
- **D.** has reveal

**Correct answer: B**

**Reviewed explanation:** The main subject is the plural noun **structures**. “Of a single cell” and “when examined under high magnification by a researcher” do not change the subject's number. **Reveal** supplies the correct main finite verb.

| Option | Assessment |
|---|---|
| A. reveals | Singular verb; disagrees with plural **structures**. |
| B. reveal | Correct agreement and complete main clause. |
| C. revealing | Nonfinite participle; leaves the main clause without a finite verb. |
| D. has reveal | Malformed perfect construction: **has** requires a past participle here; the singular auxiliary also disagrees with **structures**. |

**Review:** B is the sole defensible option. D is an obvious malformed distractor, so the requested medium difficulty remains unverified. The wording and option design resemble the earlier sample; this run is not evidence of strong output diversity.

### Annotation and validation

The existing ingestion-compatible annotation pass identified `conventions_grammar`, `agreement`, `subject_verb_agreement`, and `nearest_noun_attraction`. Generation used the new modular loader; annotation still used the existing loader. No database writes were made.

Machine validation returned no blocking findings and one review finding: `explanation: No explanation text provided`. Reasoning was returned, but the expected explanation field was missing from the validated merged payload. The reviewed explanation in this file does not fix that pipeline issue.

### Runtime and token usage

| Stage | Model-call runtime | Input/context tokens | Output tokens | Input + output |
|---|---:|---:|---:|---:|
| Generation | 25.087 s | 22,533 | 5,471 | 28,004 |
| Annotation | 39.366 s | 27,112 | 8,439 | 35,551 |
| **Full pass** | **64.453 s** | **49,645** | **13,910** | **63,555** |

Measured script elapsed time: **64.507 seconds**, including setup, prompt building, parsing, and validation through the measurement point. It excludes this Markdown append and manual review.

### Context usage

The calls have separate context windows; their token totals do not accumulate into one context.

| Stage | Input tokens | Actual input + output | Input + requested maximum output | Rule block characters | Full input characters |
|---|---:|---:|---:|---:|---:|
| Generation | 22,533 | 28,004 | 55,301 | 73,607 | 88,814 |
| Annotation | 27,112 | 35,551 | 59,880 | 95,560 | 112,910 |

Both calls requested a maximum of 32,768 output tokens. “Input + requested maximum output” is a planning allowance, not actual token consumption. Input/output counts are reported by the provider; hidden reasoning and cache hits were not separately reported. Full input characters count static rules, dynamic instructions, and the user payload, excluding transport formatting. No context-window utilization percentage is claimed because this run did not verify the effective endpoint limit.

### Attempt accounting

Before this successful retry, another generation-and-annotation attempt returned a question but failed annotation parsing: the model produced reasoning without usable JSON. That attempt's counters were not checkpointed, so its exact token usage and total runtime are unavailable. The tables above cover **only the successful retry**, not the entire request including that failed attempt. The retry saved response counters before parsing. No further attempts were needed.

The earlier sample and its recorded statistics above are preserved unchanged.
