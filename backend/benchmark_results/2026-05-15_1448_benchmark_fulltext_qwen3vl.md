# OCR Benchmark: glm-ocr + qwen3-vl:235b (full-text extraction)

**Date:** 2026-05-15 14:48
**Mode:** Full-text extraction (all OCR text sent to LLM in one call)
**Strategy:** glm-ocr:latest → qwen3-vl:235b-instruct-cloud

---

## Summary

| Metric | Value |
|--------|-------|
| OCR Engine | glm-ocr:latest |
| Extraction LLM | qwen3-vl:235b-instruct-cloud |
| Extraction Mode | Full-text (single LLM call) |
| Questions Extracted | **32 / 33** |
| Complete A-D Options | **32 / 32** |
| Found Question Numbers | 1–32 (consecutive, no gaps) |
| Missing Question Numbers | None within range (Q33 not extracted) |
| OCR Latency | 55,582 ms |
| Extraction Latency | 164,130 ms |
| **Total Latency** | **219,712 ms (~3.7 min)** |
| OCR Characters | 23,949 |
| Token Usage | 74,161 prompt / 13,808 completion / 87,969 total |

## Per-Page OCR Results

| Page | Latency (ms) | Characters |
|-----:|-------------:|-----------:|
| 1 | 6,000 | 291 |
| 2 | 2,473 | 834 |
| 3 | 3,338 | 1,932 |
| 4 | 3,936 | 1,823 |
| 5 | 3,850 | 1,721 |
| 6 | 3,865 | 1,899 |
| 7 | 3,553 | 995 |
| 8 | 3,729 | 1,820 |
| 9 | 4,536 | 2,530 |
| 10 | 4,573 | 2,370 |
| 11 | 4,305 | 1,907 |
| 12 | 4,128 | 1,988 |
| 13 | 3,616 | 1,008 |
| 14 | 3,680 | 2,590 |

## Analysis

Best full-module result to date. qwen3-vl:235b extracted 32/33 questions with **consecutive numbering Q1–Q32 and no gaps** — all 32 have complete A-D options. Only Q33 was missed (likely the final question truncated by token limits). Token efficiency is excellent at 13,808 completion tokens. This is the recommended production combination.