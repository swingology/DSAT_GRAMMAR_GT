# OCR Benchmark: glm-ocr + deepseek-v4-pro (full-text extraction, 32K tokens)

**Date:** 2026-05-15 14:56
**Mode:** Full-text extraction (all OCR text sent to LLM in one call)
**Strategy:** glm-ocr:latest → deepseek-v4-pro:cloud

---

## Summary

| Metric | Value |
|--------|-------|
| OCR Engine | glm-ocr:latest |
| Extraction LLM | deepseek-v4-pro:cloud |
| Extraction Mode | Full-text (single LLM call, 32K max_tokens) |
| Questions Extracted | **32 / 33** |
| Complete A-D Options | **32 / 32** |
| Found Question Numbers | 1–13, 17, 19–33 |
| Missing Question Numbers | 14, 15, 16, 18 |
| OCR Latency | 33,734 ms |
| Extraction Latency | 340,823 ms |
| **Total Latency** | **374,557 ms (~6.2 min)** |
| OCR Characters | 23,943 |
| Token Usage | 74,067 prompt / 25,391 completion / 99,458 total |

## Per-Page OCR Results

| Page | Latency (ms) | Characters |
|-----:|-------------:|-----------:|
| 1 | 1,692 | 291 |
| 2 | 1,930 | 834 |
| 3 | 2,518 | 1,934 |
| 4 | 2,470 | 1,823 |
| 5 | 2,366 | 1,721 |
| 6 | 2,475 | 1,899 |
| 7 | 2,039 | 995 |
| 8 | 2,659 | 1,820 |
| 9 | 2,822 | 2,530 |
| 10 | 2,708 | 2,366 |
| 11 | 2,564 | 1,903 |
| 12 | 2,543 | 1,988 |
| 13 | 2,005 | 1,008 |
| 14 | 2,943 | 2,590 |

## Analysis

deepseek-v4-pro extracted 32 questions but with **4 gaps in numbering** (Q14, 15, 16, 18 missing from found numbers). Despite extracting 32 questions total, the LLM reordered or skipped some question numbers. This is worse than qwen3-vl:235b which produced clean consecutive numbering (Q1–Q32).

Key comparison with qwen3-vl:235b full-text (strategy 10):
- **Latency**: deepseek-v4-pro is 2.1× slower (341s vs 164s extraction, 375s vs 220s total)
- **Accuracy**: deepseek-v4-pro has numbering gaps; qwen3-vl produces clean consecutive numbering
- **Token efficiency**: deepseek-v4-pro uses 1.8× more completion tokens (25,391 vs 13,808)
- **OCR latency**: this run had faster OCR (34s vs 56s) due to model caching from prior runs