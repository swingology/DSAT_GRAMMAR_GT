# Ingestion Pipeline Refactor — Speed & Token Efficiency Tasks

Source audit: 2026-05-19 conversation. Targets the official PDF ingestion
flow (`backend/app/routers/ingest.py` and its prompts/providers). Tasks are
ordered by ROI; numbered for easy cross-reference.

## Current pipeline (one module)

```
PDF parse (pymupdf) → OCR (VLM-fused or two-step) → Pass 1 extract
  → _normalize_extracted_questions → per-question Pass 2 annotate
  → validate → persist → optional layout detection / overlap check
```

Per-module cost today (rough):
- Pass 1: 1 LLM call, ~30K input + ~10K output
- Pass 2: 33 LLM calls × (~50K rules doc + ~1K question payload + ~2K output) = ~1.65M input, ~66K output
- Layout detection: 1 glm-ocr call per page (~5-10 pages) — currently runs even on text-only modules

## Confirmed not-a-problem (skip)

- **Parallel annotation.** Already done at `ingest.py:2061` via
  `asyncio.gather`. Concurrency cap is `settings.ollama_max_concurrent` (8).
- **`_normalize_extracted_questions` silent drops.** Fixed in commit
  `e3be02b` (composite dedupe key + surfaced norm_errors).
- **OCR cross-check false positives from passage line numbers.** Fixed in
  commit `657570b` (strict +1 contiguity).
- **`stem_type_key` / `stimulus_mode_key` VARCHAR(40/30) overflow.** Fixed
  in commit `765bea0` via migration 019 + db.py reconcile.

---

## Tier 1 — Big wins (do first)

### Task 1. Anthropic prompt caching on the annotation rules doc
**Where:** `backend/app/llm/anthropic_provider.py:30`, `backend/app/prompts/annotate_prompt.py`

**Problem:** `system` is passed as a plain string. The system prompt contains
the entire rules doc (~50K tokens of static reference material). Across 33
questions per module the same 50K tokens are re-billed 33 times = ~1.65M
input tokens per module, almost all redundant.

**Fix:**
1. In `anthropic_provider.py`, change `system=system` to a content-block list:
   ```python
   system=[
       {"type": "text", "text": rules_text, "cache_control": {"type": "ephemeral"}},
       {"type": "text", "text": per_question_instructions_text},
   ]
   ```
2. In `build_annotate_prompt`, split the returned `system` into a stable rules
   prefix and a per-question suffix. Provider receives both and applies
   `cache_control` to the prefix.
3. Optionally extend `AnthropicProvider.complete()` signature to accept the
   split system parts so the prompt builder owns the boundary.

**Expected savings:**
- Cached read pricing on Sonnet is ~10% of fresh write pricing.
- For a 33-question module: ~$5 → ~$0.50 annotation cost.
- Wall-clock: cached reads stream materially faster — expect 30–50% wall-time
  reduction on Pass 2.

**Risk:** Low. Cache hits require an exact prefix match. As long as the rules
doc isn't edited mid-job (it's a file read at module load), the prefix is
stable across all 33 calls.

**Verification:** Inspect `response.usage` after the call — Anthropic returns
`cache_read_input_tokens` and `cache_creation_input_tokens` once caching is
wired up. Add a log line in `anthropic_provider.complete()`.

---

### Task 2. Drop raw_text from VLM-fused extraction prompt
**Where:** `backend/app/prompts/extract_prompt.py:71` (`build_vision_extract_prompt`)

**Problem (suspected):** When `ocr_strategy=ollama` the vision model already
has the page images. Sending ~30K chars of pymupdf raw_text alongside is
redundant input and may be contributing to qwen3-vl's mis-numbering and
truncation behavior (extra context to wade through).

**Fix:** Audit `build_vision_extract_prompt` and confirm whether raw_text is
included. If yes, drop it from the vision path while keeping it for the
text-only Pass 1 path. Keep `extract_root["raw_text"]` populated for the
passage-recovery helper.

**Expected savings:** ~30K input tokens per Pass 1 call on the VLM-fused
path. Smaller than Task 1 but additive.

**Risk:** Medium. Need to confirm the VLM doesn't depend on raw_text for any
field; the post-extraction normalization (`_recover_passage_from_raw_text`)
already pulls raw_text from `extract_root` separately and is unaffected.

---

### Task 3. Trim rules doc per stem family
**Where:** `backend/app/prompts/annotate_prompt.py:294` (`build_annotate_prompt`)

**Problem:** Grammar questions get the full reading-v2 doc (~20K tokens) for
no reason; reading questions get the full grammar-v7 doc (~30K tokens) for
no reason. The `_detect_domain()` helper already exists and is used for
nullability enforcement — we just don't use it to gate prompt content.

**Fix:**
1. In `build_annotate_prompt`, branch on `_detect_domain(q_data)`:
   - `"grammar"` → load grammar-v7 only
   - `"reading"` → load reading-v2 only
   - `"unknown"` → load both (current behavior, fallback)
2. Combine with Task 1: cache each domain's rules block separately so domain
   switches inside a batch still hit cache.

**Expected savings:** 40-50% input token reduction on annotation BEFORE
caching; compounds with Task 1.

**Risk:** Low. The domain detector is already trusted for nullability rules,
so trusting it for prompt content is a parallel use.

---

## Tier 2 — Medium wins

### Task 4. Skip Pass 2 on questions with blocking pre-validation errors
**Where:** `backend/app/routers/ingest.py:2021` (`_annotate_one`)

**Problem:** Questions flagged by `_validate_question_numbers` or
`qnum_ocr_crosscheck` as blocking still go through full annotation even
though they won't be auto-approved. Each skipped call saves one Pass 2
round-trip.

**Fix:** Build a `should_annotate(idx)` predicate from `suspect_qnum_indices`
+ any blocking validation errors and short-circuit in `_annotate_one`. Write
a stub `annotate_json` payload (`{"explanation_short": "skipped: blocking
pre-validation", "needs_human_review": True}`) so persistence still works.

**Expected savings:** Variable — on clean PDFs zero; on problem PDFs up to
50% of Pass 2 cost.

**Risk:** Low. The questions are headed to manual review anyway.

---

### Task 5. Gate layout detection on table/chart presence
**Where:** `backend/app/routers/ingest.py:1900` (`layout_detection_enabled`
block) and `backend/app/storage/crop_detector.py`

**Problem:** Layout detection runs glm-ocr per page on every job. On
text-only reading modules (most of them) it returns no useful regions but
takes ~30s/page. Live log from Test_6 mod02 showed `crop_detector` warnings
like `"No valid JSON found in text"` — model is being called for nothing.

**Fix:** After `_normalize_extracted_questions`, scan
`questions_data` for any `table_data` or `graph_data` keys (or any
`stimulus_mode_key` indicating a visual stimulus). If none, skip layout
detection entirely. If some, run layout detection only on those questions'
page indices.

**Expected savings:** ~30s × (5-10 pages) = ~2-5 min wall-clock per text-only
module. Most modules are text-only.

**Risk:** Low. Layout detection is described in code comments as enrichment,
"never a gate" — skipping it cannot block valid questions from saving.

---

### Task 6. Reduce text-call timeout
**Where:** `backend/app/llm/ollama_provider.py` (`TEXT_TIMEOUT = 300.0`)

**Problem:** 300s timeout × 3 retries = 15-min worst case per Pass 1 text
call. With Task 1 caching landing, cached calls will return in seconds.

**Fix:** Pull `TEXT_TIMEOUT` to 120s. If real production p99 exceeds 120s,
revisit — but the existing 300s was set defensively for large pre-cache
payloads.

**Expected savings:** Bounded worst-case time only; no average improvement.

**Risk:** Low; can be reverted instantly.

---

## Tier 3 — Smaller wins

### Task 7. Page-render caching
**Where:** `backend/app/routers/ingest.py:_render_page_b64`,
`_store_page_render`, layout-detection block

**Problem:** Page images are rendered once for the VLM and again for layout
detection. Check whether `pass1_json._page_images` is reused or re-rendered.

**Fix:** If duplicated, ensure both consumers read from the same cache key.

**Expected savings:** ~1-2s/page wall-clock.

**Risk:** Low.

---

### Task 8. Drop unused OCR fallbacks early
**Where:** `backend/app/routers/ingest.py:_build_ocr_chain`

**Problem:** `_build_ocr_chain` returns the full chain `[primary, fallback1,
fallback2]` regardless of whether the primary succeeds. Verify no eager work
(like page renders or warmup calls) is done for fallback providers.

**Fix:** Lazy provider init inside the chain loop, not at chain construction.

**Expected savings:** Marginal; mostly avoids wasted setup.

---

### Task 9. Increase polling interval
**Where:** `.claude/skills/ingestion-test/run.sh`

**Problem:** Test runner polls `/ingest/jobs/{id}` every few seconds — log
noise more than anything.

**Fix:** Bump polling to 10s. Optional; only affects test loop UX.

---

## Suggested implementation order

1. **Task 1** (prompt caching) — biggest single win, well-isolated change.
2. **Task 3** (per-domain rules) — compounds with Task 1.
3. **Task 5** (layout-detection gate) — biggest wall-clock win.
4. **Task 4** (skip Pass 2 on blocked questions).
5. **Task 2** (drop raw_text in VLM-fused prompt) — needs investigation first.
6. Remaining tier 3 tasks.

## Verification per task

Each task should land with:
- A test that exercises the gated/cached/trimmed path (real DB fixture preferred over `_MockSession`).
- A line in `DEBUG_LOG.md` recording before/after token counts on one
  representative module (Test_7 mod01 is a good baseline now that it has a
  clean 33/33 expected).
- An entry in `.wolf/cerebrum.md` `## Key Learnings` capturing any quirk
  discovered during implementation.
