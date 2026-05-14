"""
Live OCR ingestion test — no database required.

Exercises the full extraction chain for each available provider:
  image → provider.complete_vision() → extract_json_from_text() → normalize_annotation()

Run from backend/ dir:
    source .venv/bin/activate
    python test_ocr_live.py [--image /path/to/image.png] [--strategies ollama,anthropic,openai]
"""
import asyncio
import base64
import json
import os
import sys
import time
import argparse
from pathlib import Path


def load_image_as_b64(path: str):
    from app.llm.base import ImageContent
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    suffix = Path(path).suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix[1:], "image/png")
    return ImageContent(b64=b64, mime_type=mime)


async def test_ollama(image, model: str, base_url: str) -> dict:
    from app.llm.ollama_provider import OllamaProvider
    from app.parsers.json_parser import extract_json_from_text, normalize_annotation
    from app.prompts.extract_prompt import build_vision_extract_prompt

    provider = OllamaProvider(base_url=base_url, default_model=model)
    system, user = build_vision_extract_prompt({})

    t0 = time.time()
    try:
        result = await provider.complete_vision(
            system=system, user=user, images=[image], model=model, max_tokens=16000
        )
        elapsed = time.time() - t0
        parsed = extract_json_from_text(result.raw_text, "ollama", model)
        return {
            "strategy": f"ollama/{model}",
            "status": "ok",
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage,
            "questions_extracted": len(parsed.get("questions", [parsed] if parsed.get("question_text") else [])),
            "has_correct_option": bool(parsed.get("correct_option_label") or
                any(q.get("correct_option_label") for q in parsed.get("questions", []))),
            "raw_text_preview": result.raw_text[:300],
            "parsed_keys": sorted(parsed.keys()),
        }
    except Exception as e:
        return {"strategy": f"ollama/{model}", "status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}
    finally:
        await provider.close()


async def test_anthropic(image, model: str, api_key: str) -> dict:
    from app.llm.anthropic_provider import AnthropicProvider
    from app.parsers.json_parser import extract_json_from_text
    from app.prompts.extract_prompt import build_vision_extract_prompt

    provider = AnthropicProvider(api_key=api_key, default_model=model)
    system, user = build_vision_extract_prompt({})

    t0 = time.time()
    try:
        result = await provider.complete_vision(
            system=system, user=user, images=[image], model=model, max_tokens=16000
        )
        elapsed = time.time() - t0
        parsed = extract_json_from_text(result.raw_text, "anthropic", model)
        return {
            "strategy": f"anthropic/{model}",
            "status": "ok",
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage,
            "questions_extracted": len(parsed.get("questions", [parsed] if parsed.get("question_text") else [])),
            "has_correct_option": bool(parsed.get("correct_option_label") or
                any(q.get("correct_option_label") for q in parsed.get("questions", []))),
            "raw_text_preview": result.raw_text[:300],
            "parsed_keys": sorted(parsed.keys()),
        }
    except Exception as e:
        return {"strategy": f"anthropic/{model}", "status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}


async def test_openai(image, model: str, api_key: str) -> dict:
    from app.llm.openai_provider import OpenAIProvider
    from app.parsers.json_parser import extract_json_from_text
    from app.prompts.extract_prompt import build_vision_extract_prompt

    provider = OpenAIProvider(api_key=api_key, default_model=model)
    system, user = build_vision_extract_prompt({})

    t0 = time.time()
    try:
        result = await provider.complete_vision(
            system=system, user=user, images=[image], model=model, max_tokens=16000
        )
        elapsed = time.time() - t0
        parsed = extract_json_from_text(result.raw_text, "openai", model)
        return {
            "strategy": f"openai/{model}",
            "status": "ok",
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage,
            "questions_extracted": len(parsed.get("questions", [parsed] if parsed.get("question_text") else [])),
            "has_correct_option": bool(parsed.get("correct_option_label") or
                any(q.get("correct_option_label") for q in parsed.get("questions", []))),
            "raw_text_preview": result.raw_text[:300],
            "parsed_keys": sorted(parsed.keys()),
        }
    except Exception as e:
        return {"strategy": f"openai/{model}", "status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}


async def test_deepseek(image, base_url: str, model: str) -> dict:
    from app.parsers.ocr import DeepSeekOCRClient

    client = DeepSeekOCRClient(base_url=base_url, model=model)
    t0 = time.time()
    try:
        result = await client.extract([image])
        return {
            "strategy": f"deepseek/{model}",
            "status": "ok",
            "latency_ms": result.latency_ms,
            "token_usage": result.token_usage,
            "raw_text_preview": result.raw_text[:500],
            "raw_text_length": len(result.raw_text),
        }
    except Exception as e:
        return {"strategy": f"deepseek/{model}", "status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}
    finally:
        await client.close()


def print_result(r: dict):
    status_icon = "✓" if r["status"] == "ok" else "✗"
    print(f"\n{'='*60}")
    print(f"  {status_icon}  {r['strategy']}")
    print(f"{'='*60}")
    if r["status"] == "error":
        print(f"  ERROR: {r['error']}")
        print(f"  Latency: {r['latency_ms']}ms")
        return

    print(f"  Latency:    {r['latency_ms']}ms")
    if r.get("token_usage"):
        u = r["token_usage"]
        print(f"  Tokens:     {u.get('input',0)} in / {u.get('output',0)} out")
    if "questions_extracted" in r:
        print(f"  Questions:  {r['questions_extracted']}")
        print(f"  Has answer: {r['has_correct_option']}")
    if "parsed_keys" in r:
        print(f"  Keys:       {', '.join(r['parsed_keys'])}")
    if "raw_text_length" in r:
        print(f"  OCR chars:  {r['raw_text_length']}")
    print(f"\n  Preview:")
    print(f"  {r['raw_text_preview']!r}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="/tmp/test_page_sample.png", help="Path to test image")
    parser.add_argument("--strategies", default="ollama", help="Comma-separated: ollama,anthropic,openai,deepseek")
    parser.add_argument("--ollama-model", default="qwen2.5vl:7b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--anthropic-model", default="claude-sonnet-4-6")
    parser.add_argument("--openai-model", default="gpt-4o")
    parser.add_argument("--deepseek-url", default="http://localhost:8001")
    parser.add_argument("--deepseek-model", default="deepseek-ai/DeepSeek-OCR-2")
    args = parser.parse_args()

    strategies = [s.strip() for s in args.strategies.split(",")]
    print(f"\nLoading image: {args.image}")
    image = load_image_as_b64(args.image)
    print(f"Image loaded: {image.mime_type}")

    results = []
    tasks = []

    # Run all strategies concurrently
    coros = []
    if "ollama" in strategies:
        coros.append(test_ollama(image, args.ollama_model, args.ollama_url))
    if "anthropic" in strategies:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("  SKIP anthropic — ANTHROPIC_API_KEY not set")
        else:
            coros.append(test_anthropic(image, args.anthropic_model, api_key))
    if "openai" in strategies:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("  SKIP openai — OPENAI_API_KEY not set")
        else:
            coros.append(test_openai(image, args.openai_model, api_key))
    if "deepseek" in strategies:
        coros.append(test_deepseek(image, args.deepseek_url, args.deepseek_model))

    print(f"Running {len(coros)} strategy/strategies concurrently...\n")
    results = await asyncio.gather(*coros)

    for r in results:
        print_result(r)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        icon = "✓" if r["status"] == "ok" else "✗"
        latency = f"{r['latency_ms']}ms"
        tokens = ""
        if r.get("token_usage"):
            u = r["token_usage"]
            tokens = f"  {u.get('input',0)}in/{u.get('output',0)}out tok"
        qs = f"  {r.get('questions_extracted','?')}q" if r["status"] == "ok" and "questions_extracted" in r else ""
        print(f"  {icon} {r['strategy']:<30} {latency:>8}{tokens}{qs}")


if __name__ == "__main__":
    asyncio.run(main())
