# OCR Benchmark: glm-ocr + qwen3-vl:235b (per-page extraction)

**Date:** 2026-05-15 14:38
**Mode:** Per-page extraction (each page's OCR text sent to LLM separately)
**Strategy:** glm-ocr:latest → qwen3-vl:235b-instruct-cloud

---

## Summary

| Metric | Value |
|--------|-------|
| OCR Engine | glm-ocr:latest |
| Extraction LLM | qwen3-vl:235b-instruct-cloud |
| Extraction Mode | Per-page |
| Questions Extracted | 14 / 33 |
| Complete A-D Options | 14 / 14 |
| Found Question Numbers | 1–6, 12–13, 17–21 |
| Missing Question Numbers | 7–11, 14–16 |
| OCR Latency | 55,342 ms |
| Extraction Latency | 160,999 ms |
| **Total Latency** | **216,341 ms (~3.6 min)** |
| OCR Characters | 23,437 |
| Token Usage | 80,271 prompt / 12,997 completion / 93,268 total |

## Per-Page OCR Results

| Page | Latency (ms) | Characters |
|-----:|-------------:|-----------:|
| 1 | 5,318 | 291 |
| 2 | 2,454 | 834 |
| 3 | 3,322 | 1,932 |
| 4 | 3,930 | 1,817 |
| 5 | 3,871 | 1,721 |
| 6 | 3,903 | 1,899 |
| 7 | 3,613 | 995 |
| 8 | 3,753 | 1,820 |
| 9 | 4,624 | 2,530 |
| 10 | 4,611 | 2,370 |
| 11 | 4,314 | 1,903 |
| 12 | 4,258 | 1,988 |
| 13 | 3,371 | 506 |
| 14 | 4,000 | 2,590 |

## Analysis

Per-page extraction performed poorly — only 14/33 questions extracted with 8 missing question numbers. This is because the extraction LLM loses context when processing each page in isolation, especially for passages that span multiple pages. The full-text extraction approach (see strategy 10) is strongly preferred.