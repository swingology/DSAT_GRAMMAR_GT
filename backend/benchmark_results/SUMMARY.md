# OCR Ingestion Benchmark — Summary

All tests run against page 3 of `Test_1_digital_sec01_mod01.pdf` (PT1 Verbal Mod01).
4 SAT vocabulary-in-context questions. Ground truth: Q1=D, Q2=A, Q3=B, Q4=A.

---

## Results at a Glance

| # | Pipeline | Pass 1 Model | Score | Total Latency | Pass 1 Tokens out | Usable |
|---|----------|-------------|:-----:|:-------------:|:-----------------:|:------:|
| 1 | deepseek-ocr + LLM | `kimi-k2.6:cloud` | 4/4 ✓ | 135s | 7,490 | ✓ |
| 2 | Fused VLM | `granite3.2-vision:latest` | 0/4 ✗ | 210s | 563 | ✗ |
| 3 | deepseek-ocr + LLM | `deepseek-v4-pro:cloud` | 4/4 ✓ | ~84s | 1,469 | ✓ |
| 4 | deepseek-ocr + LLM | `qwen3-vl:235b-instruct-cloud` | 4/4 ✓ | **~77s** | **839** | ✓ |

---

## Key Findings

### Two-step pipeline wins over fused VLM
Every two-step strategy (DeepSeek OCR → extraction LLM) achieved 4/4. The fused VLM (`granite3.2-vision`) produced 0 usable questions — it hallucinated 4 identical rows differing only in answer label, and failed to separate question stems or structure options.

### Extraction LLM efficiency varies 9×
All three extraction LLMs scored 4/4 but differ sharply in output verbosity:

| Model | Tokens out | vs. kimi baseline |
|-------|-----------|------------------|
| `kimi-k2.6:cloud` | 7,490 | baseline |
| `deepseek-v4-pro:cloud` | 1,469 | 5.1× leaner |
| `qwen3-vl:235b-instruct-cloud` | 839 | **8.9× leaner** |

Token output directly affects cost at cloud inference rates. `qwen3-vl:235b` and `deepseek-v4-pro` are dramatically more efficient for the same accuracy.

### Speed ranking (Pass 1 only)
1. `qwen3-vl:235b-instruct-cloud` — 24s
2. `deepseek-v4-pro:cloud` — 31s
3. `kimi-k2.6:cloud` — 82s

### OCR step is the dominant latency
DeepSeek OCR takes ~53s fixed regardless of which extraction LLM follows. Optimizing the extraction model from kimi to qwen3-vl:235b saves 58s on Pass 1 but total pipeline only drops from 135s to ~77s. Speeding up or parallelizing the OCR step would have larger impact.

---

## Pipeline Architecture

```
Fused VLM (one call):
  image ──────────────────────────► VLM ──► JSON

Two-step (two calls):
  image ──► deepseek-ocr ──► text ──► LLM ──► JSON
             (~53s fixed)        (24–82s varies)
```

The two-step approach gives a recovery point between steps, allows OCR output inspection, and lets the extraction LLM be swapped independently.

---

## Models Tested

| Model | Type | Result |
|-------|------|--------|
| `deepseek-ocr:latest` | OCR (local, Ollama) | ✓ Working — 53s, minor HTML table noise |
| `kimi-k2.6:cloud` | Extraction LLM (cloud, Ollama) | ✓ 4/4, verbose output |
| `deepseek-v4-pro:cloud` | Extraction LLM (cloud, Ollama) | ✓ 4/4, efficient |
| `qwen3-vl:235b-instruct-cloud` | Extraction LLM (cloud, Ollama) | ✓ 4/4, fastest + most efficient |
| `granite3.2-vision:latest` | Fused VLM (local, Ollama) | ✗ Unusable — hallucinated duplicates |
| `qwen3-vl:8b` | Fused VLM (local, Ollama) | ✗ Thinking-mode bug — empty content via OpenAI-compat API |
| `qwen3.6:27b` | Extraction LLM (local) | ✗ Insufficient RAM (needs 20.7 GB) |
| `claude-sonnet-4-6` | Fused VLM (Anthropic API) | ⏳ Not tested — needs API key |
| `gpt-4o` | Fused VLM (OpenAI API) | ⏳ Not tested — needs API key |

---

## Recommendation

For production ingestion use `deepseek-ocr:latest` + `qwen3-vl:235b-instruct-cloud`:
- Best latency (~77s total)
- Most token-efficient (839 tokens out per page)
- 4/4 accuracy on this test page
- Clean JSON output, no preamble

`deepseek-v4-pro:cloud` is a strong alternative with near-identical performance.

---

## Detail Pages

| Test | File |
|------|------|
| PT1 Mod01 Page 3 (4 questions) | [`2026-05-11_pt1_mod01_page3.md`](2026-05-11_pt1_mod01_page3.md) |
