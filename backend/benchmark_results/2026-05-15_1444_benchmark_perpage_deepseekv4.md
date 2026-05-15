# OCR Benchmark: glm-ocr + deepseek-v4-pro (per-page extraction)

**Date:** 2026-05-15 14:44
**Mode:** Per-page extraction (each page's OCR text sent to LLM separately)
**Strategy:** glm-ocr:latest → deepseek-v4-pro:cloud

---

## Summary

| Metric | Value |
|--------|-------|
| OCR Engine | glm-ocr:latest |
| Extraction LLM | deepseek-v4-pro:cloud |
| Extraction Mode | Per-page |
| Questions Extracted | 26 / 33 |
| Complete A-D Options | 22 / 26 |
| Found Question Numbers | 1–6, 16–21 |
| Missing Question Numbers | 7–15 |
| OCR Latency | 54,085 ms |
| Extraction Latency | 497,641 ms |
| **Total Latency** | **551,726 ms (~9.2 min)** |
| OCR Characters | 23,945 |
| Token Usage | 80,185 prompt / 30,424 completion / 110,609 total |

## Per-Page OCR Results

| Page | Latency (ms) | Characters |
|-----:|-------------:|-----------:|
| 1 | 2,680 | 291 |
| 2 | 2,816 | 834 |
| 3 | 3,870 | 1,934 |
| 4 | 3,921 | 1,819 |
| 5 | 3,810 | 1,723 |
| 6 | 4,028 | 1,899 |
| 7 | 3,173 | 995 |
| 8 | 4,323 | 1,820 |
| 9 | 4,811 | 2,530 |
| 10 | 4,505 | 2,370 |
| 11 | 4,220 | 1,903 |
| 12 | 4,203 | 1,988 |
| 13 | 2,794 | 1,008 |
| 14 | 4,931 | 2,590 |

## Analysis

Per-page extraction with deepseek-v4-pro is even worse than qwen3-vl — 9 missing question numbers despite extracting 26 questions. The LLM struggles to maintain proper numbering across isolated page contexts. Total latency is also very high at ~9 minutes due to slow per-page extraction calls.