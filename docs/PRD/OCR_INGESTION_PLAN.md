# OCR Ingestion System Plan — DSAT Grammar Backend

The current ingest pipeline requires raw text to proceed. PDFs from PyMuPDF `get_text("text")` work when the PDF has embedded text layers, but **scanned PDFs and standalone images produce empty raw_text** — the pipeline fails with "No raw text available" or extracts garbage. This plan compares OCR approaches and designs the integration.

---

## 1. Current State

```
Upload (PDF/Image/Markdown) → parse_pdf() or parse_image() → raw_text → Pass 1 (extract) → Pass 2 (annotate) → persist
```

- `parse_pdf()`: `page.get_text("text")` — works for text-layer PDFs only. Extracts images as base64 but **discards them** (the pipeline never sends images to the LLM).
- `parse_image()`: Returns base64 + mime type. **Not called by the ingest pipeline** at all — the router catches image MIME types but the pipeline sets raw_text to empty string.
- `LLMProvider.complete(system, user)` — text-only interface. No image input support in the protocol.
- `build_extract_prompt()` — accepts `raw_text: str` only. No mechanism to pass images.

**Gap:** The pipeline has no OCR step, no multimodal LLM call, and no image-to-text preprocessing stage. Any scanned PDF or image file is dead on arrival.

---

## 2. Approach Comparison

### A. Multimodal LLM (Claude, GPT-4o, Qwen-VL)

**How it works:** Send the page image(s) directly to a vision-capable model. The model returns structured JSON (question text, options, correct answer) in one shot — no separate OCR pass.

**Integration:** Add a `complete_vision()` method to `LLMProvider` that accepts `system: str, user: str, images: list[dict]` (each with `b64` and `mime_type`). The ingest router calls this instead of text-only `complete()` when the source is image-based.

**Pros:**
- Single pass from image → structured extraction (OCR + extraction fused)
- Handles complex layouts, tables, diagrams naturally
- No extra system dependencies (no Tesseract, no PaddleOCR)
- Claude and GPT-4o have excellent SAT/exam question reading ability
- Claude handles up to 20 images per request via `anthropic` provider

**Cons:**
- Token cost per page: ~1-2K image tokens per page (for Claude) plus output tokens
- Higher latency per call (3-10s for vision vs 1-3s for text-only)
- Requires API support for image inputs (Anthropic, OpenAI both support natively; Ollama depends on model)
- Qwen-VL via Ollama may have inconsistent vision quality compared to cloud models
- No separate OCR output — you can't cache or inspect the intermediate text

**Cost estimate per page (Claude Sonnet 4.6):** ~$0.010-0.025 input (image tokens) + ~$0.003 output

### B. DeepSeek OCR (dedicated OCR model)

**How it works:** DeepSeek released a dedicated OCR model (`deepseek-ocr`) that takes images and returns structured text — designed specifically for document OCR. It preserves layout, handles tables, and outputs Markdown-formatted text.

**Integration:** Add a new `DeepSeekOCRProvider` (or integrate into the existing openai provider since DeepSeek offers an OpenAI-compatible API at `api.deepseek.com`). Call it as a preprocessing step before Pass 1 extraction: image → DeepSeek OCR → raw text → existing extract prompt.

**Pros:**
- Purpose-built for document OCR
- Preserves layout structure (tables, multi-column)
- OpenAI-compatible API — reuse existing HTTP infrastructure
- Significantly cheaper than multimodal LLM: ~$0.002 per page
- Output is plain text → feeds directly into existing `build_extract_prompt()`

**Cons:**
- Chinese company (DeepSeek) — data residency/cross-border considerations
- API availability and uptime less established than Anthropic/OpenAI
- Dedicated external API key and endpoint to manage
- Two-pass on image files: OCR first, then LLM extraction → double latency
- Less capable with handwriting or heavily stylized text

**Cost estimate per page:** ~$0.002 (OCR) + ~$0.003 (LLM extraction) = ~$0.005 total

### C. GLM OCR (Zhipu AI GLM-4V)

**How it works:** GLM-4V from Zhipu AI is a multimodal model with strong OCR capabilities. It can process images and return structured text. Zhipu offers a dedicated OCR API endpoint (`glm-4v-ocr`).

**Integration:** Similar to DeepSeek — make HTTP calls to Zhipu API for OCR preprocessing, feed results into the existing extraction pipeline. Could also be used as a full multimodal provider (image → structured extraction in one call).

**Pros:**
- Strong Chinese/English bilingual OCR
- Competitive pricing (~¥0.001-0.005 per image)
- Can handle complex document layouts
- Dedicated OCR endpoint optimized for speed

**Cons:**
- Chinese company — data residency concerns
- API is China-based (latency from non-Asia regions ~200-400ms extra RTT)
- Less community adoption and documentation outside China
- No OpenAI-compatible SDK — requires custom HTTP client
- Two-pass if using OCR-only endpoint (same as DeepSeek)

**Cost estimate per page:** ~$0.001 (OCR endpoint) + ~$0.003 (LLM extraction) = ~$0.004 total

### D. Traditional Python OCR (Tesseract, EasyOCR, PaddleOCR)

**How it works:** Run OCR locally using Python libraries. Tesseract (pytesseract) is the oldest, EasyOCR is deep-learning-based with decent accuracy, PaddleOCR (Baidu) is the most accurate of the three for English document text.

**Integration:** Add OCR as a preprocessing step in `_run_pipeline()` or in the parser layer. For PDFs: render each page to an image with `pdf2image` (poppler), then run OCR. For images: run OCR directly. Store the resulting text as `raw_text` and proceed with the existing pipeline.

**Dependencies to add:**
- For Tesseract: `pytesseract`, system package `tesseract-ocr`
- For EasyOCR: `easyocr` (PyTorch dependency — ~800MB+)
- For PaddleOCR: `paddleocr`, `paddlepaddle` (even larger)
- Universal: `pdf2image` + system package `poppler-utils`

**Pros:**
- Zero per-page cost — runs entirely locally
- No external API dependencies
- Full control over preprocessing (denoising, binarization, skew correction)
- PaddleOCR achieves ~95% accuracy on clean English document text
- Data never leaves the machine — suitable for sensitive content

**Cons:**
- Heavy dependencies: Tesseract is light (~100MB), but EasyOCR/PaddleOCR need PyTorch (+2GB)
- Much lower accuracy than multimodal LLMs on complex layouts
- Tables, multi-column layouts, footnotes typically come out mangled
- Requires preprocessing pipeline (skew correction, contrast adjustment, DPI checks)
- No layout preservation — you get flat text, losing which text belongs to which question
- Setup complexity: poppler, tesseract binaries, language packs, GPU optional but slow on CPU
- Speed: 1-5s per page on CPU (Tesseract ~1s, PaddleOCR on CPU ~3-5s)

**Cost estimate per page:** $0 (local compute only)

---

## 3. Comparison Matrix

| Dimension | Multimodal LLM | DeepSeek OCR | GLM OCR | Traditional Python OCR |
|-----------|---------------|--------------|---------|----------------------|
| **Accuracy (clean)** | 98-99% | 96-98% | 95-97% | 90-95% |
| **Accuracy (complex layout)** | 95-98% | 93-96% | 92-95% | 70-85% |
| **Latency per page** | 3-10s | 2-5s | 2-5s | 1-5s |
| **Cost per page** | $0.010-0.025 | ~$0.002 | ~$0.001 | $0 |
| **Data residency risk** | Low (Anthropic/OpenAI) | Medium (DeepSeek CN) | High (Zhipu CN) | None (local) |
| **Layout preservation** | Excellent | Good | Good | Poor |
| **Deployment complexity** | Low (API key only) | Low (API key only) | Medium | High (binaries + deps) |
| **Dependency size** | None (HTTP) | None (HTTP) | None (HTTP) | 100MB–2GB+ |
| **Extra API key needed** | No (reuse existing) | Yes | Yes | No |
| **Maintenance burden** | None | Low | Low | Medium (system deps) |

---

## 4. Recommended Approaches

### Primary: Multimodal LLM (Pass-through)

Use the existing LLM provider (Anthropic or OpenAI) in vision mode. This is the simplest integration with the highest accuracy and zero additional dependencies.

**Flow:**
```
Scanned PDF → parse_pdf() extracts images → provider.complete_vision(system, user, images=[...]) 
                → returns structured JSON directly (no separate OCR step)
```

**Key benefit:** Fuses OCR + extraction into a single LLM call. No intermediate text to manage.

### Fallback: Traditional Python OCR (PaddleOCR)

For batch/bulk processing where API costs would be prohibitive, or for offline operation. PaddleOCR is the most accurate of the local options.

**Flow:**
```
Scanned PDF → pdf2image renders pages → PaddleOCR extracts text lines → raw_text → existing pipeline
```

### Not recommended: DeepSeek OCR or GLM OCR

Both require extra API keys, add a separate OCR step, and introduce data residency concerns. They don't offer enough accuracy advantage over multimodal LLMs to justify the operational overhead. Reconsider if a dedicated OCR service with better pricing emerges.

---

## 5. Integration Plan

### 5.1. Extend LLMProvider Protocol

Add an optional `complete_vision()` method to the provider base:

```python
@dataclass
class ImageContent:
    b64: str
    mime_type: str  # "image/png", "image/jpeg", etc.

class LLMProvider(Protocol):
    async def complete(self, system: str, user: str, ...) -> LLMResponse: ...

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list[ImageContent],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Fallback: raise NotImplementedError by default."""
        raise NotImplementedError(f"{type(self).__name__} does not support vision")
```

### 5.2. Implement by Provider

- **AnthropicProvider**: `complete_vision()` sends `system` + `user` text + image blocks via the Anthropic Messages API (`content: [{"type": "image", "source": {"type": "base64", ...}}]`).
- **OpenAIProvider**: `complete_vision()` sends via OpenAI Chat Completions with `content: [{"type": "image_url", "image_url": {"url": "data:{mime};base64,{b64}"}}]`.
- **OllamaProvider**: `complete_vision()` sends via Ollama API with `images: [b64]` field. Falls back to text-only if the loaded model doesn't support vision.

### 5.3. Create OCR Preprocessing Module

`app/parsers/ocr.py` — standalone OCR preprocessing for non-multimodal flows:

```python
def ocr_preprocess(pdf_path: str, strategy: str = "paddle") -> str:
    """Render PDF pages to images and run OCR. Returns concatenated text."""
    images = pdf_to_images(pdf_path)       # pdf2image
    text = run_ocr(images, engine=strategy)  # paddleocr / easyocr / tesseract
    return text
```

This module is **only used when the LLM provider doesn't support vision** (e.g., Ollama with a text-only model, or offline mode).

### 5.4. Modify Ingest Pipeline

In `_run_pipeline()` (ingest.py), add an OCR gate before the text check:

```python
raw_text = (job.pass1_json or {}).get("raw_text", "")

# If no raw_text and we have images, try vision or OCR
if not raw_text and images:
    if provider.supports_vision():
        # Use multimodal extraction (fuses OCR + extraction)
        orch.advance()
        job.status = "extracting"
        await db.commit()
        system, user = build_extract_prompt("")  # minimal system prompt, text is from images
        result = await provider.complete_vision(system, user, images)
        extract_json = extract_json_from_text(result.raw_text)
        job.pass1_json = {**extract_json, "_llm_meta": {...}}
    else:
        # Fall back to local OCR preprocessing
        raw_text = ocr_preprocess(asset_path, strategy="paddle")
        job.pass1_json = {"raw_text": raw_text, "ocr_source": "paddle"}
        # Then proceed with normal text extraction...

if not raw_text:
    orch.fail("extracting", "no_raw_text", "No raw text available")
```

### 5.5. Configuration

Add to `Settings`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OCR_STRATEGY` | `"auto"` | `auto` = use vision if provider supports it, else local OCR. `vision`, `deepseek`, `glm`, `paddle`, `tesseract`, `easyocr` |
| `OCR_FALLBACK` | `true` | If vision fails, fall back to local OCR |
| `VISION_MAX_IMAGES` | `10` | Max images per vision call (Anthropic limit ~20, safety buffer) |

### 5.6. Prompt Adjustments

`build_extract_prompt()` needs a variant for vision-mode: the system prompt stays the same, but the user prompt should instruct "read the question from the image(s)" rather than containing raw_text:

```python
def build_vision_extract_prompt() -> tuple[str, str]:
    system = EXTRACT_SYSTEM_PROMPT  # same schema expectations
    user = "Extract the question data from the image(s) above. Output valid JSON only."
    return system, user
```

### 5.7. Pipeline State Machine

No changes needed to `orchestrator.py`. The OCR/vision step happens during the existing "extracting" state. The new logic is:

```
pending → parsing → extracting (OCR/vision done here) → annotating → overlap_checking → validating → approved
```

### 5.8. YAML Export

No changes needed. The export step runs after persistence and uses the already-extracted JSON — whether that JSON came from text-based extraction or vision-based extraction.

---

## 6. Implementation Order

1. **Extend `LLMProvider` protocol** — add `complete_vision()` to base, implement for Anthropic, OpenAI, Ollama
2. **Create `app/parsers/ocr.py`** — PaddleOCR preprocessing module (with `pdf2image` rendering)
3. **Modify ingest pipeline** — add vision/OCR gate before the "no raw text" failure
4. **Create `build_vision_extract_prompt()`** — minimal user prompt for image-based extraction
5. **Add config** — `OCR_STRATEGY`, `OCR_FALLBACK`, `VISION_MAX_IMAGES` to settings
6. **Update dependencies** — add `pdf2image`, `paddleocr` / `easyocr` / `pytesseract` to pyproject.toml
7. **Test** — upload scanned PDF, verify vision extraction; test fallback with text-only Ollama + PaddleOCR; verify cost/accuracy tradeoffs

---

## 7. Edge Cases

| Case | Handling |
|------|----------|
| Scanned PDF with mixed text + image pages | `parse_pdf()` already extracts per-page images. Vision call gets all images; local OCR renders text-only pages to images too. |
| Multi-page PDF (10+ questions) | Vision calls are limited to `VISION_MAX_IMAGES` per batch. If more pages exist, batch them into multiple vision calls and merge results. |
| Image too low resolution | Preprocess: skip blank pages (low entropy), upscale pages below 150 DPI before sending to vision/OCR. |
| Provider doesn't support vision | `complete_vision()` raises `NotImplementedError` → catch and fall through to local OCR. |
| Vision API fails mid-batch | Already handled by existing retry decorator — retry 3x with backoff, then fall back to local OCR if `OCR_FALLBACK=true`. |
| Ollama vision model (e.g., llava) | Same `complete_vision()` path — Ollama API accepts `images: [b64]` in the request body. |
| Mixed image + text in same PDF | Use vision for all pages of a scanned PDF. Use text extraction for text-layer PDFs — no OCR needed. Detect by checking if `page.get_text("text")` returns meaningful content vs whitespace/scraps. |
