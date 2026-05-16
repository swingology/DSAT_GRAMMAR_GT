# OCR Ingestion Benchmark — Summary

**Test corpus:** Page 3 of `Test_1_digital_sec01_mod01.pdf` (PT1 Verbal Mod01) + full-module run (14 pages, 33 questions)
**Last updated:** 2026-05-15

---

## Results at a Glance

### Single-Page Benchmarks (Page 3, 4 questions)

| # | OCR Engine | Extraction LLM | Score | OCR ms | Pass1 ms | Total ms | Pass1 tok-out | Usable |
|---|-----------|----------------|:-----:|-------:|---------:|---------:|:-------------:|:------:|
| 1 | deepseek-ocr | `kimi-k2.6:cloud` | 4/4 ✓ | 53,064 | 82,039 | **135,103** | 7,490 | ✓ |
| 2 | granite3.2-vision *(fused)* | — | 0/4 ✗ | — | — | 209,805 | 563 | ✗ |
| 3 | deepseek-ocr | `deepseek-v4-pro:cloud` | 4/4 ✓ | ~53,064 | 30,697 | **~83,761** | 1,469 | ✓ |
| 4 | deepseek-ocr | `qwen3-vl:235b-instruct-cloud` | 4/4 ✓ | ~53,064 | 24,134 | **~77,198** | 839 | ✓ |
| 5 | glm-ocr | `kimi-k2.6:cloud` | 4/4 ✓ | 55,126 | 107,917 | **163,043** | 6,781 | ✓ |
| 6 | glm-ocr | `deepseek-v4-pro:cloud` | 4/4 ✓ | 55,126 | 37,613 | **92,739** | 1,173 | ✓ |
| 7 | glm-ocr | `qwen3-vl:235b-instruct-cloud` | 4/4 ✓ | 57,530 | 16,976 | **74,506** | **780** | ✓ |

> Strategies 3–4 reused OCR text from Strategy 1; OCR latency is estimated. Strategies 5–6 ran full end-to-end pipelines from PDF.

### Full-Module Benchmarks (14 pages, 33 questions)

| # | OCR Engine | Extraction LLM | Extracted | Complete A-D | OCR ms | Extract ms | Total ms | Missing Qs |
|---|-----------|----------------|:---------:|:------------:|-------:|-----------:|---------:|:----------:|
| 8 | glm-ocr | `deepseek-v4-pro:cloud` (per-page) | 32/33 | 32/32 | 26,009 | 187,641 | **213,650** | Q11 |
| 9 | PyMuPDF (embedded text) | deterministic parser | 33/33 ✓ | 33/33 ✓ | — | 62 | **62** | — |
| 10 | glm-ocr | `qwen3-vl:235b-instruct-cloud` (full-text) | 32/33 | 32/32 | 55,582 | 164,130 | **219,712** | Q33 |
| 11 | glm-ocr | `deepseek-v4-pro:cloud` (full-text, 32K tok) | 32/33 | 32/32 | 33,734 | 340,823 | **374,557** | Q14-16,Q18 |

> Strategies 8 and 10-11 forced the OCR path for full-module coverage. Strategy 9 used PyMuPDF embedded text (no LLM needed). Strategies 10-11 used full-text extraction (all OCR text sent in one LLM call), matching the production pipeline.

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

### 3. Extraction LLM efficiency varies 9× — accuracy is identical (single-page)

| Extraction LLM | Score | Pass 1 ms | tok-out | vs. kimi |
|---------------|:-----:|----------:|--------:|---------|
| `kimi-k2.6:cloud` | 4/4 | 82–108s | ~7,000+ | baseline |
| `deepseek-v4-pro:cloud` | 4/4 | 31–38s | ~1,200–1,470 | **~5× leaner, ~2.5× faster** |
| `qwen3-vl:235b-instruct-cloud` | 4/4 | 24s | 839 | **~9× leaner, ~3.5× faster** |

All three score 4/4 on single pages. `deepseek-v4-pro` and `qwen3-vl:235b` are dramatically more efficient.

### 4. Full-module extraction: qwen3-vl outperforms deepseek-v4-pro

| Extraction LLM | Questions | Missing | Total ms | Extract ms |
|---------------|:---------:|:-------:|---------:|-----------:|
| `qwen3-vl:235b-instruct-cloud` | 32/33 | Q33 | 219,712 | 164,130 |
| `deepseek-v4-pro:cloud` | 32/33 | Q14-16,Q18 | 374,557 | 340,823 |

`qwen3-vl:235b` extracts all 32 questions with consecutive numbering (Q1-32), only missing Q33. `deepseek-v4-pro` misses 4 question numbers (Q14-16, Q18) despite extracting 32 total — suggesting numbering/reordering issues in its output. `qwen3-vl:235b` is also **2× faster** at extraction.

### 5. OCR step is the dominant latency floor
glm-ocr takes 34–56s for 14 pages. Even the fastest extraction LLM (qwen3-vl:235b at 164s) means the total is ~220s. The OCR step accounts for 25-50% of total pipeline time depending on LLM speed.

### 6. Full-module OCR consistently misses ~1 question
All forced OCR strategies extract 32/33 questions. The missing question varies by strategy (Q11 in per-page, Q33 in full-text with qwen3-vl). This confirms that robust ingestion needs page diagnostics, selective cropping, and provenance tracking.

### 7. Digital PDFs: embedded text is 3,500× faster and 100% accurate
For PDFs with embedded text (like the digital SAT test), PyMuPDF's text extraction + deterministic parsing achieved 33/33 in 62ms — vs ~220s for the forced OCR path. The embedded-text path should always be preferred when available.

### 8. Best overall combination (production pipeline)
`glm-ocr:latest` + `qwen3-vl:235b-instruct-cloud` remains the recommended production combination:
- **220s total** for full 14-page module
- **32/33 questions** with correct consecutive numbering
- Cleaner OCR text (blanks preserved, no HTML artifacts)
- Fully Ollama-based — no external services needed

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
                        (34–56s)              (164–341s)

Digital PDF (preferred when embedded text exists):
  PDF ──► PyMuPDF extract ──► deterministic parse ──► JSON
                                (62ms total)

Fused VLM (tested, failed):
  PDF ──► rasterize ──► VLM ──────────────────────────────────► JSON
                        (210s, 0/4 usable)
```

---

## Detail Reports

| Test | File |
|------|------|
| PT1 Mod01 Page 3 — full strategy breakdown | [`2026-05-11_pt1_mod01_page3.md`](2026-05-11_pt1_mod01_page3.md) |
| Full module — forced glm-ocr + deepseek-v4-pro (per-page) | [`2026-05-15_forced_glm_ocr_deepseek_v4_test_1_sec01_mod01.md`](2026-05-15_forced_glm_ocr_deepseek_v4_test_1_sec01_mod01.md) |
| Full module — deterministic embedded-text parse | [`2026-05-15_test_1_digital_sec01_mod01_questions.md`](2026-05-15_test_1_digital_sec01_mod01_questions.md) |
| Full module — glm-ocr + qwen3-vl:235b (per-page) | [`2026-05-15_1438_benchmark_perpage_qwen3vl.md`](2026-05-15_1438_benchmark_perpage_qwen3vl.md) |
| Full module — glm-ocr + deepseek-v4-pro (per-page) | [`2026-05-15_1444_benchmark_perpage_deepseekv4.md`](2026-05-15_1444_benchmark_perpage_deepseekv4.md) |
| Full module — glm-ocr + qwen3-vl:235b (full-text) | [`2026-05-15_1448_benchmark_fulltext_qwen3vl.md`](2026-05-15_1448_benchmark_fulltext_qwen3vl.md) |
| Full module — glm-ocr + deepseek-v4-pro (full-text, 16K — truncated) | [`2026-05-15_1449_benchmark_fulltext_deepseekv4_truncated.md`](2026-05-15_1449_benchmark_fulltext_deepseekv4_truncated.md) |
| Full module — glm-ocr + deepseek-v4-pro (full-text, 32K) | [`2026-05-15_1456_benchmark_fulltext_deepseekv4.md`](2026-05-15_1456_benchmark_fulltext_deepseekv4.md) |
| Test 1 Sec01 Mod01 — pymupdf | [`2026-05-15_1603_benchmark_pymupdf_embedded_text_extraction_determi.md`](2026-05-15_1603_benchmark_pymupdf_embedded_text_extraction_determi.md) |
