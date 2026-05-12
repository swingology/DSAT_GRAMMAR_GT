# OCR Ingestion Benchmark — Summary

**Test corpus:** Page 3 of `Test_1_digital_sec01_mod01.pdf` (PT1 Verbal Mod01)
**Questions:** 4 SAT vocabulary-in-context items. Ground truth: Q1=D, Q2=A, Q3=B, Q4=A.
**Last updated:** 2026-05-12

---

## Results at a Glance

| # | OCR Engine | Extraction LLM | Score | OCR ms | Pass1 ms | Total ms | Pass1 tok-out | Usable |
|---|-----------|----------------|:-----:|-------:|---------:|---------:|:-------------:|:------:|
| 1 | deepseek-ocr | `kimi-k2.6:cloud` | 4/4 ✓ | 53,064 | 82,039 | **135,103** | 7,490 | ✓ |
| 2 | granite3.2-vision *(fused)* | — | 0/4 ✗ | — | — | 209,805 | 563 | ✗ |
| 3 | deepseek-ocr | `deepseek-v4-pro:cloud` | 4/4 ✓ | ~53,064 | 30,697 | **~83,761** | 1,469 | ✓ |
| 4 | deepseek-ocr | `qwen3-vl:235b-instruct-cloud` | 4/4 ✓ | ~53,064 | 24,134 | **~77,198** | 839 | ✓ |
| 5 | glm-ocr | `kimi-k2.6:cloud` | 4/4 ✓ | 55,126 | 107,917 | **163,043** | 6,781 | ✓ |
| 6 | glm-ocr | `deepseek-v4-pro:cloud` | 4/4 ✓ | 55,126 | 37,613 | **92,739** | 1,173 | ✓ |

> Strategies 3–4 reused OCR text from Strategy 1; OCR latency is estimated. Strategies 5–6 ran full end-to-end pipelines from PDF.

---

## Key Findings

### 1. Two-step pipeline is necessary — fused VLM fails
Every two-step strategy (OCR engine → extraction LLM) achieved 4/4. The only fused VLM tested (`granite3.2-vision`) produced 0 usable questions — hallucinated 4 identical rows, failed to separate stems, and mixed options across questions.

### 2. OCR engine quality: glm-ocr preserves blank markers, deepseek-ocr does not

| OCR Engine | Latency | Blank `______` | HTML noise | Chars |
|-----------|---------|:--------------:|:---------:|-------|
| `deepseek-ocr:latest` | 53s | ✗ stripped | ✓ some table wrapping | 1,978 |
| `glm-ocr:latest` | 55s | ✓ preserved as `_____` | ✗ none | 1,924 |

GLM-OCR produces cleaner, more structured text at similar speed. Preserving the blank marker matters for the extraction LLM to correctly identify the fill-in-the-blank position.

### 3. Extraction LLM efficiency varies 9× — accuracy is identical

| Extraction LLM | Score | Pass 1 ms | tok-out | vs. kimi |
|---------------|:-----:|----------:|--------:|---------|
| `kimi-k2.6:cloud` | 4/4 | 82–108s | ~7,000+ | baseline |
| `deepseek-v4-pro:cloud` | 4/4 | 31–38s | ~1,200–1,470 | **~5× leaner, ~2.5× faster** |
| `qwen3-vl:235b-instruct-cloud` | 4/4 | 24s | 839 | **~9× leaner, ~3.5× faster** |

All three score 4/4. `deepseek-v4-pro` and `qwen3-vl:235b` are dramatically more efficient.

### 4. OCR step is the dominant latency floor
Both OCR engines take ~53–55s. Even the fastest extraction LLM (qwen3-vl:235b at 24s) brings total to ~77s. The OCR step accounts for ~68% of total pipeline time.

### 5. Best overall combination
`glm-ocr:latest` + `deepseek-v4-pro:cloud` offers the best quality/speed balance:
- Cleaner OCR text (blanks preserved, no HTML)
- Fast extraction (38s Pass 1)
- Total ~93s end-to-end from PDF
- 1,173 output tokens (cost-efficient at cloud rates)

`deepseek-ocr` + `qwen3-vl:235b-instruct-cloud` is faster (~77s) but relies on the dedicated deepseek-ocr service (port 8001) which is not always running.

---

## Model Status

| Model | Role | Status |
|-------|------|--------|
| `deepseek-ocr:latest` (port 8001) | OCR engine | ✓ Working when service is up |
| `glm-ocr:latest` (Ollama) | OCR engine | ✓ Working — better quality |
| `kimi-k2.6:cloud` | Extraction LLM | ✓ Working — verbose output |
| `deepseek-v4-pro:cloud` | Extraction LLM | ✓ Working — fast, efficient |
| `qwen3-vl:235b-instruct-cloud` | Extraction LLM | ✓ Working — fastest, most efficient |
| `granite3.2-vision:latest` | Fused VLM | ✗ Unusable — hallucinated duplicates |
| `glm-5.1:cloud` | — | ✗ No vision — cannot OCR |
| `qwen2.5vl:7b` | Extraction LLM | ✗ OOM — needs 12.5 GB |
| `qwen3.6:27b` | Extraction LLM | ✗ OOM — needs 20.7 GB |
| `qwen3-vl:8b` | Fused VLM | ✗ Thinking-mode bug — empty content via OpenAI-compat API |
| `claude-sonnet-4-6` | Fused VLM | ⏳ Needs `ANTHROPIC_API_KEY` |
| `gpt-4o` | Fused VLM | ⏳ Needs `OPENAI_API_KEY` |

---

## Pipeline Architecture

```
Two-step (recommended):
  PDF ──► rasterize ──► OCR engine ──► text ──► Extraction LLM ──► JSON
                        (53–55s)              (24–108s)

Fused VLM (tested, failed):
  PDF ──► rasterize ──► VLM ──────────────────────────────────► JSON
                        (210s, 0/4 usable)
```

---

## Detail Reports

| Test | File |
|------|------|
| PT1 Mod01 Page 3 — full strategy breakdown | [`2026-05-11_pt1_mod01_page3.md`](2026-05-11_pt1_mod01_page3.md) |
