#!/usr/bin/env python3
"""Standalone OCR benchmark runner.

Exercises the full two-step pipeline (OCR → extraction LLM) against a real SAT
PDF without requiring the backend API server or database.

Uses the same extraction prompt as the real ingest pipeline for accurate results.

Always generates markdown reports in benchmark_results/ and updates SUMMARY.md.
Use --save to additionally save raw JSON results.

Usage:
    cd backend && uv run python run_ocr_benchmark.py [OPTIONS]

Examples:
    # Default: glm-ocr + qwen3-vl on Test 1 Mod01
    uv run python run_ocr_benchmark.py

    # Specific PDF, specific strategies
    uv run python run_ocr_benchmark.py --pdf ../TESTS/"DATA_SRC/2025-2026 Tests Answers/VERBAL/Test_6_digital_sec01_mod01.pdf" --ocr glm --extract qwen3-vl:235b-instruct-cloud,deepseek-v4-pro:cloud

    # Only certain pages for faster testing
    uv run python run_ocr_benchmark.py --pages 3,4,5

    # Save JSON along with markdown reports
    uv run python run_ocr_benchmark.py --save
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Same extraction prompt as the real pipeline ──────────────────────────────

EXTRACT_SYSTEM_PROMPT = """You are a DSAT question extraction specialist. Your job is to extract ALL questions from raw text extracted from SAT practice material.

CRITICAL: Extract EVERY numbered question in the text. A single SAT module contains 27–33 questions. Do not stop after the first question — scan the entire text and include all of them in the "questions" array.

When a passage is shared across multiple questions, use the same passage_text for each of those questions.

You must output valid JSON matching this schema:
{
  "passage_text": "The shared passage text, or null if no passage",
  "paired_passage_text": null,
  "source_exam_code": "e.g. PT1, PT4, PT11, or null — use the value from the source metadata if provided",
  "source_subject_code": "verbal or math or null",
  "source_section_code": "01 or 02 or null",
  "source_module_code": "01 or 02 or null",
  "questions": [
    {
      "question_text": "The prompt/stem text",
      "source_question_number": 1 or null,
      "options": [
        {"label": "A", "text": "option A text"},
        {"label": "B", "text": "option B text"},
        {"label": "C", "text": "option C text"},
        {"label": "D", "text": "option D text"}
      ],
      "correct_option_label": "A or B or C or D",
      "stimulus_mode_key": "sentence_only or passage_excerpt etc.",
      "stem_type_key": "complete_the_text or choose_main_idea etc."
    }
  ],
  "table_data": null,
  "graph_data": null
}

Rules:
- Always produce exactly 4 options labeled A, B, C, D per question
- Identify the correct answer from the answer key or context
- Preserve the original wording as closely as possible
- If no passage, set passage_text to null
- For a single question, return a questions array with one element
- Output ONLY valid JSON, no markdown fences"""


# ── HTTP helpers ─────────────────────────────────────────────────────────────

async def ollama_vision_request(model: str, system: str, user: str, images: list[dict],
                                 max_tokens: int = 4096, temperature: float = 0.0) -> dict:
    import httpx

    content = [{"type": "text", "text": user}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:{img['mime_type']};base64,{img['b64']}"}})

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    t0 = time.time()
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(f"{OLLAMA_BASE}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
    elapsed_ms = int((time.time() - t0) * 1000)

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"raw_text": text, "latency_ms": elapsed_ms, "token_usage": usage}


async def ollama_text_request(model: str, system: str, user: str,
                              max_tokens: int = 16000, temperature: float = 0.0) -> dict:
    import httpx

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    t0 = time.time()
    async with httpx.AsyncClient(timeout=900) as client:
        resp = await client.post(f"{OLLAMA_BASE}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
    elapsed_ms = int((time.time() - t0) * 1000)

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"raw_text": text, "latency_ms": elapsed_ms, "token_usage": usage}


# ── PDF / page helpers ───────────────────────────────────────────────────────

def render_pdf_to_images(pdf_path: str, dpi: int = 200) -> list[dict]:
    import fitz

    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        b64 = base64.b64encode(pix.tobytes("png")).decode()
        images.append({
            "page_number": page_num + 1,
            "b64": b64,
            "mime_type": "image/png",
            "width": pix.width,
            "height": pix.height,
        })
    doc.close()
    return images


def extract_embedded_text(pdf_path: str) -> tuple[str, list[dict]]:
    import fitz

    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    text = "\n\n".join(texts)
    doc.close()

    images = render_pdf_to_images(pdf_path)
    return text, images


# ── JSON parsing (same as pipeline) ─────────────────────────────────────────

def extract_json_from_text(text: str) -> dict | list | None:
    """Extract JSON from LLM output, handling markdown fences and prefix text."""
    # Strip markdown fences
    import re
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object or array
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    return None


# ── Benchmark runner ──────────────────────────────────────────────────────────

async def run_ocr_benchmark(pdf_path: str, ocr_engine: str, extract_model: str,
                            pages: list[int] | None = None) -> dict:
    print(f"\n{'='*70}")
    print(f"OCR: {ocr_engine}  |  Extract: {extract_model}")
    print(f"PDF: {Path(pdf_path).name}")
    if pages:
        print(f"Pages: {pages}")
    print(f"{'='*70}")

    # Step 0: Render PDF pages
    print("Rendering PDF pages...")
    all_images = render_pdf_to_images(pdf_path)
    print(f"  Rendered {len(all_images)} pages")

    if pages:
        selected = [img for img in all_images if img["page_number"] in pages]
    else:
        selected = all_images

    print(f"  Selected {len(selected)} pages for OCR")

    # Step 1: OCR each page
    ocr_pages = []  # (page_number, ocr_text, latency_ms)
    ocr_total_latency = 0
    ocr_total_tokens = {}

    if ocr_engine == "glm":
        model = "glm-ocr:latest"
        ocr_system = (
            "You are a precise OCR engine. Extract all text from the image exactly as it "
            "appears. Preserve question numbers on their own lines, option labels (A/B/C/D), "
            "and blank markers (______). Return only the extracted text."
        )

        for img in selected:
            pn = img["page_number"]
            print(f"  OCR page {pn}...", end=" ", flush=True)
            result = await ollama_vision_request(
                model=model, system=ocr_system, user="Extract all text from this image.",
                images=[img], max_tokens=4096, temperature=0.0,
            )
            ocr_pages.append((pn, result["raw_text"], result["latency_ms"]))
            ocr_total_latency += result["latency_ms"]
            ocr_total_tokens = _merge_usage(ocr_total_tokens, result.get("token_usage", {}))
            print(f"{result['latency_ms']}ms, {len(result['raw_text'])} chars")

    elif ocr_engine == "deepseek":
        try:
            from app.parsers.ocr import OCRClient
            ocr_client = OCRClient(base_url="http://localhost:8001", model="deepseek-ai/DeepSeek-OCR-2")
            result = await ocr_client.extract(selected)
            combined_text = result.raw_text
            ocr_total_latency = result.latency_ms
            # No per-page breakdown for DeepSeek
            ocr_pages.append(("all", combined_text, ocr_total_latency))
        except Exception as e:
            print(f"  DeepSeek OCR failed: {e}")
            return {"error": str(e), "strategy": f"{ocr_engine}+{extract_model}"}
    else:
        return {"error": f"Unknown OCR engine: {ocr_engine}"}

    # Combine OCR text
    if ocr_engine == "glm":
        combined_text = "\n\n".join(f"--- Page {pn} ---\n{text}" for pn, text, _ in ocr_pages)
    else:
        combined_text = ocr_pages[0][1]

    print(f"  OCR total: {ocr_total_latency:,}ms, {len(combined_text)} chars")

    # Step 2: Extract questions — send all OCR text in one call (matches real pipeline)
    all_questions = []
    extract_total_latency = 0
    extract_total_tokens = {}

    # Build full OCR text from all pages
    full_ocr_text = "\n\n".join(f"--- Page {pn} ---\n{text}" for pn, text, _ in ocr_pages if text.strip())

    user_msg = f"""Extract ALL questions from the following raw text. Include every numbered question you find — do not stop early.

---
{full_ocr_text}
---"""

    print(f"  Extracting all pages with {extract_model}...", end=" ", flush=True)
    try:
        result = await ollama_text_request(
            model=extract_model, system=EXTRACT_SYSTEM_PROMPT, user=user_msg,
            max_tokens=32000, temperature=0.0,
        )
        extract_total_latency += result["latency_ms"]
        extract_total_tokens = _merge_usage(extract_total_tokens, result.get("token_usage", {}))

        parsed = extract_json_from_text(result["raw_text"])
        if parsed is None:
            print(f"{result['latency_ms']}ms, PARSE FAILED")
            print(f"  Raw text preview: {result['raw_text'][:300]}")
        else:
            questions = parsed.get("questions", []) if isinstance(parsed, dict) else parsed
            if not questions and isinstance(parsed, dict) and parsed.get("question_text"):
                questions = [parsed]
            print(f"{result['latency_ms']}ms, {len(questions)} questions")
            all_questions = questions

    except Exception as e:
        print(f"ERROR: {e}")

    # Deduplicate by question number
    seen_nums = set()
    deduped = []
    for q in all_questions:
        qnum = q.get("source_question_number") or q.get("question_number") or q.get("number")
        if qnum and qnum in seen_nums:
            continue
        if qnum:
            seen_nums.add(qnum)
        deduped.append(q)
    all_questions = deduped

    # Compile results
    total_latency = ocr_total_latency + extract_total_latency
    total_tokens = _merge_usage(ocr_total_tokens, extract_total_tokens)

    questions_with_all_opts = sum(1 for q in all_questions if _has_all_options(q))
    found_nums = sorted(set(
        q.get("source_question_number") or q.get("question_number") or q.get("number")
        for q in all_questions
        if q.get("source_question_number") or q.get("question_number") or q.get("number")
    ))

    # Determine expected question count
    max_q = max(found_nums) if found_nums else 0
    expected = list(range(1, max_q + 1)) if max_q else []
    missing = [n for n in expected if n not in found_nums]

    result = {
        "strategy": f"{ocr_engine}+{extract_model}",
        "ocr_engine": ocr_engine,
        "extract_model": extract_model,
        "ocr_latency_ms": ocr_total_latency,
        "extract_latency_ms": extract_total_latency,
        "total_latency_ms": total_latency,
        "ocr_chars": len(combined_text),
        "pages_processed": len(selected),
        "questions_extracted": len(all_questions),
        "questions_with_all_options": questions_with_all_opts,
        "found_question_numbers": found_nums,
        "missing_question_numbers": missing,
        "per_page_ocr": [{"page": pn, "latency_ms": ms, "chars": len(t)} for pn, t, ms in ocr_pages],
        "token_usage": total_tokens,
        "questions": all_questions,
    }

    return result


def _has_all_options(q: dict) -> bool:
    opts = q.get("options", [])
    if isinstance(opts, dict):
        return all(k in opts for k in ["A", "B", "C", "D"])
    if isinstance(opts, list):
        labels = {o.get("label", "") for o in opts}
        return all(l in labels for l in ["A", "B", "C", "D"])
    return False


def _merge_usage(a: dict, b: dict) -> dict:
    merged = dict(a)
    for k, v in b.items():
        if isinstance(v, int):
            merged[k] = merged.get(k, 0) + v
    return merged


def generate_markdown_report(result: dict, pdf_path: str, output_dir: Path) -> Path:
    """Generate a markdown report from benchmark results, mirroring the reference format."""
    import re

    pdf_name = Path(pdf_path).stem
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")

    # Derive test descriptor from pdf name
    test_label = pdf_name.replace("_digital_", " ").replace("_", " ").title()

    # Strategy description
    if "strategy" in result and "+" in result.get("strategy", ""):
        ocr = result.get("ocr_engine", "?")
        ext = result.get("extract_model", "?")
        mode = "full-text extraction"
        strategy_desc = f"{ocr}-ocr + {ext} ({mode})"
    elif result.get("ocr_engine") == "pymupdf":
        strategy_desc = "PyMuPDF embedded-text extraction + deterministic question/option parser"
    else:
        strategy_desc = result.get("strategy", "unknown")

    # Count questions with A-D options
    questions = result.get("questions", [])
    total_qs = len(questions)
    with_opts = sum(1 for q in questions if _has_all_options(q))

    lines = []
    lines.append(f"# Benchmark: {test_label} Questions")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Source PDF: `{pdf_path}`")
    lines.append(f"- Benchmark mode: {strategy_desc}")
    lines.append(f"- Pages parsed: {result.get('pages_processed', '?')}")

    if result.get("ocr_engine") == "pymupdf":
        lines.append("- OCR status: skipped; PDF contains embedded text")
        lines.append(f"- Embedded text characters: {result.get('ocr_chars', 0)}")
    else:
        lines.append(f"- OCR status: {result.get('ocr_engine', '?')} ({result.get('ocr_latency_ms', 0):,} ms)")
        lines.append(f"- Extraction LLM: {result.get('extract_model', '?')} ({result.get('extract_latency_ms', 0):,} ms)")
        lines.append(f"- Total latency: {result.get('total_latency_ms', 0):,} ms")
        lines.append(f"- OCR text characters: {result.get('ocr_chars', 0)}")

    lines.append(f"- Parse latency: {result.get('extract_latency_ms', result.get('total_latency_ms', 0)):,} ms")
    lines.append(f"- Questions parsed: {total_qs} / {total_qs}")
    lines.append(f"- Questions with A-D options: {with_opts} / {total_qs}")

    if result.get("found_question_numbers"):
        lines.append(f"- Found question numbers: {result['found_question_numbers']}")
    if result.get("missing_question_numbers"):
        lines.append(f"- Missing question numbers: {result['missing_question_numbers']}")

    lines.append("")
    lines.append("## Questions And Options")
    lines.append("")

    for q in questions:
        qnum = q.get("source_question_number") or q.get("question_number") or q.get("number")
        qnum_str = str(qnum) if qnum else "?"
        qtext = q.get("question_text", "").strip()

        lines.append(f"### Question {qnum_str}")
        lines.append("")
        lines.append(qtext)
        lines.append("")

        opts = q.get("options", [])
        if isinstance(opts, dict):
            for label in ["A", "B", "C", "D"]:
                if label in opts:
                    lines.append(f"- **{label})** {opts[label]}")
        elif isinstance(opts, list):
            for opt in opts:
                label = opt.get("label", "?")
                text = opt.get("text", "")
                lines.append(f"- **{label})** {text}")

        lines.append("")

    # Write file
    slug = re.sub(r"[^a-z0-9]+", "_", strategy_desc.lower()).strip("_")[:40]
    filename = f"{ts}_benchmark_{slug}.md"
    out_path = output_dir / filename
    out_path.write_text("\n".join(lines))
    return out_path


def update_summary_md(summary_path: Path, report_rel_path: str, result: dict, pdf_path: str) -> None:
    """Update SUMMARY.md with a row for the new benchmark report."""
    today = datetime.now().strftime("%Y-%m-%d")

    if not summary_path.exists():
        return

    content = summary_path.read_text()

    # Update last-updated date
    import re
    content = re.sub(
        r"\*\*Last updated:\*\* \S+",
        f"**Last updated:** {today}",
        content,
    )

    # Build new row
    pdf_name = Path(pdf_path).stem
    test_label = pdf_name.replace("_digital_", " ").replace("_", " ").title()
    strategy = result.get("strategy", "?")

    new_row = f"| {test_label} — {strategy} | [`{report_rel_path}`]({report_rel_path}) |"

    # Find the Detail Reports table and append
    if "## Detail Reports" in content:
        # Append before the next ## section or end of file
        detail_start = content.index("## Detail Reports")
        after_detail = content[detail_start:]
        next_section = re.search(r"\n## \w", after_detail[20:])  # skip the heading itself
        if next_section:
            insert_at = detail_start + 20 + next_section.start()
            content = content[:insert_at] + "\n" + new_row + content[insert_at:]
        else:
            content = content.rstrip() + "\n" + new_row + "\n"
    else:
        # No detail reports section yet — append one
        content = content.rstrip() + f"\n\n## Detail Reports\n\n{new_row}\n"

    summary_path.write_text(content)


def run_deterministic_extraction(pdf_path: str) -> dict:
    """Extract questions from PDF using PyMuPDF embedded text + regex parsing."""
    import re

    doc = fitz.open(pdf_path)
    t0 = time.time()

    all_text_parts = []
    total_images = 0
    for page in doc:
        all_text_parts.append(page.get_text())
        total_images += len(page.get_images())
    full_text = "\n\n".join(all_text_parts)
    embedded_chars = sum(len(t) for t in all_text_parts)
    pages_count = len(doc)
    doc.close()

    elapsed_ms = int((time.time() - t0) * 1000)

    # Parse questions from embedded text using regex
    # SAT digital tests typically have questions numbered 1-33 with A-D options
    questions = _parse_questions_from_text(full_text)

    # Sort by question number
    questions.sort(key=lambda q: q.get("source_question_number", 0))

    found_nums = [q.get("source_question_number") for q in questions if q.get("source_question_number")]
    max_q = max(found_nums) if found_nums else 0
    expected = list(range(1, max_q + 1)) if max_q else []
    missing = [n for n in expected if n not in found_nums]

    with_opts = sum(1 for q in questions if _has_all_options(q))

    return {
        "strategy": "pymupdf",
        "ocr_engine": "pymupdf",
        "extract_model": "deterministic",
        "ocr_latency_ms": 0,
        "extract_latency_ms": elapsed_ms,
        "total_latency_ms": elapsed_ms,
        "ocr_chars": embedded_chars,
        "pages_processed": pages_count,
        "questions_extracted": len(questions),
        "questions_with_all_options": with_opts,
        "found_question_numbers": found_nums,
        "missing_question_numbers": missing,
        "per_page_ocr": [],
        "token_usage": {},
        "questions": questions,
        "embedded_images_detected": total_images,
    }


def _parse_questions_from_text(text: str) -> list[dict]:
    """Parse numbered questions and A-D options from raw SAT text using regex."""
    import re

    # Split on question number boundaries: a newline followed by a number at line start
    # SAT questions typically appear as "\n1\n" or "\n1 " at the start of a question
    blocks = re.split(r"\n(?=\d+\n)", text)

    questions = []
    seen_nums = set()

    for block in blocks:
        # Extract question number
        num_match = re.match(r"(\d+)\s*\n", block)
        if not num_match:
            continue
        qnum = int(num_match.group(1))
        if qnum in seen_nums:
            continue
        seen_nums.add(qnum)

        body = block[num_match.end():]

        # Split off options — look for A) or A\n pattern
        opt_split = re.split(r"\n(\s*A\s*[\.\)]\s*)", body, maxsplit=1)
        if len(opt_split) < 2:
            # Try alternate split: lines starting with A.
            opt_split = re.split(r"\n(A\.[^\n]*)", body, maxsplit=1)

        if len(opt_split) >= 2:
            question_text = opt_split[0].strip()
            options_block = opt_split[1] + (opt_split[2] if len(opt_split) > 2 else "")
        else:
            question_text = body.strip()
            options_block = ""

        # Clean question text: remove extra whitespace
        question_text = re.sub(r"\s+", " ", question_text).strip()

        # Parse options A-D from options block
        options = []
        opt_pattern = re.compile(r"\s*([A-D])\s*[\.\)]\s*(.*?)(?=\s*[A-D]\s*[\.\)]|\Z)", re.DOTALL)
        for m in opt_pattern.finditer(options_block):
            label = m.group(1)
            text = re.sub(r"\s+", " ", m.group(2)).strip()
            if label not in {"A", "B", "C", "D"}:
                continue
            # Avoid duplicates
            if any(o.get("label") == label for o in options):
                continue
            options.append({"label": label, "text": text})

        # Only include if we have both question text and at least some options
        if question_text and len(options) >= 2:
            questions.append({
                "question_text": question_text,
                "source_question_number": qnum,
                "options": options,
            })

    return questions


def print_results(results: list[dict], pdf_name: str):
    ts = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*80}")
    print(f"  OCR BENCHMARK RESULTS — {ts}")
    print(f"  PDF: {pdf_name}")
    print(f"{'='*80}\n")

    print(f"{'#':<3} {'OCR':<12} {'Extract LLM':<30} {'Qs':<5} {'A-D':<5} "
          f"{'OCR ms':>9} {'Ext ms':>9} {'Total ms':>9} {'Missing':<12}")
    print(f"{'─'*3} {'─'*12} {'─'*30} {'─'*5} {'─'*5} {'─'*9} {'─'*9} {'─'*9} {'─'*12}")

    for i, r in enumerate(results, 1):
        if "error" in r:
            print(f"{i:<3} {r.get('strategy','?'):<44} ERROR: {r['error']}")
            continue
        missing = r.get("missing_question_numbers", [])
        miss_str = str(missing) if missing else "—"
        print(
            f"{i:<3} {r['ocr_engine']:<12} "
            f"{r['extract_model']:<30} "
            f"{r['questions_extracted']:<5} "
            f"{r['questions_with_all_options']:<5} "
            f"{r['ocr_latency_ms']:>9,} "
            f"{r['extract_latency_ms']:>9,} "
            f"{r['total_latency_ms']:>9,} "
            f"{miss_str:<12}"
        )

    print()
    valid = [r for r in results if "error" not in r]
    if valid:
        best_quality = max(valid, key=lambda r: r["questions_extracted"])
        fastest = min(valid, key=lambda r: r["total_latency_ms"])
        print(f"  Most questions: {best_quality['strategy']} — {best_quality['questions_extracted']} qs, "
              f"{best_quality['questions_with_all_options']} with A-D, missing: {best_quality.get('missing_question_numbers', [])}")
        print(f"  Fastest: {fastest['strategy']} — {fastest['total_latency_ms']:,}ms, "
              f"{fastest['questions_extracted']} questions")


async def main():
    parser = argparse.ArgumentParser(description="OCR Benchmark Runner")
    parser.add_argument("--pdf", default=None, help="Path to PDF file")
    parser.add_argument("--ocr", default="glm", help="OCR engine: glm, deepseek, or auto")
    parser.add_argument("--extract", default="qwen3-vl:235b-instruct-cloud,deepseek-v4-pro:cloud",
                        help="Comma-separated extraction models")
    parser.add_argument("--pages", default=None, help="Comma-separated page numbers (1-based). Default: all pages")
    parser.add_argument("--save", action="store_true", help="Save detailed results to benchmark_results/")
    args = parser.parse_args()

    if args.pdf:
        pdf_path = args.pdf
    else:
        pdf_path = str(Path(__file__).parent.parent / "TESTS" / "DATA_SRC" /
                        "2025-2026 Tests Answers" / "VERBAL" / "Test_1_digital_sec01_mod01.pdf")

    if not Path(pdf_path).exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    extract_models = [m.strip() for m in args.extract.split(",")]
    pages = [int(p.strip()) for p in args.pages.split(",")] if args.pages else None

    ocr_engines = []
    if args.ocr == "auto":
        ocr_engines = ["glm"]
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://localhost:8001/health")
                if resp.status_code == 200:
                    ocr_engines.append("deepseek")
        except Exception:
            pass
    else:
        ocr_engines = [args.ocr]

    # Run benchmarks
    results = []
    for ocr_engine in ocr_engines:
        for extract_model in extract_models:
            try:
                result = await run_ocr_benchmark(pdf_path, ocr_engine, extract_model, pages)
                results.append(result)
            except Exception as e:
                results.append({"strategy": f"{ocr_engine}+{extract_model}", "error": str(e)})

    pdf_name = Path(pdf_path).stem
    print_results(results, pdf_name)

    # Always generate markdown reports and update SUMMARY.md
    out_dir = Path(__file__).parent / "benchmark_results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    summary_path = out_dir / "SUMMARY.md"

    # Generate markdown reports for each LLM strategy
    for result in results:
        if "error" in result:
            continue
        md_path = generate_markdown_report(result, pdf_path, out_dir)
        print(f"Markdown report saved to {md_path}")
        update_summary_md(summary_path, md_path.name, result, pdf_path)

    # Run deterministic PyMuPDF extraction and generate its report
    print(f"\n{'='*80}")
    print("  Deterministic PyMuPDF extraction (ground truth)")
    print(f"{'='*80}")
    det_result = run_deterministic_extraction(pdf_path)
    print(f"  Pages: {det_result['pages_processed']}, Embedded text chars: {det_result['ocr_chars']:,}, "
          f"Images: {det_result.get('embedded_images_detected', 0)}, "
          f"Parse latency: {det_result['extract_latency_ms']}ms")
    print(f"  Questions parsed: {det_result['questions_extracted']}, "
          f"with A-D options: {det_result['questions_with_all_options']}")
    det_md = generate_markdown_report(det_result, pdf_path, out_dir)
    print(f"  Deterministic report saved to {det_md}")
    update_summary_md(summary_path, det_md.name, det_result, pdf_path)

    print(f"\nSUMMARY.md updated: {summary_path}")

    # Save JSON if requested
    if args.save and results:
        out_file = out_dir / f"{ts}_benchmark.json"
        out_file.write_text(json.dumps(results, indent=2, default=str))
        print(f"JSON results saved to {out_file}")

    return results


if __name__ == "__main__":
    asyncio.run(main())