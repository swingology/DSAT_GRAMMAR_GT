#!/usr/bin/env python3
"""Manual test script for DSAT ingestion and recall — runs without Plan 3 API.

Usage:
  # 1. Load a ground-truth PDF into the database
  python scripts/manual_test.py ingest-pdf <path-to-pdf>

  # 2. Recall questions from the database
  python scripts/manual_test.py recall [--grammar-focus KEY] [--limit N]

  # 3. Test generation (requires LLM API key)
  python scripts/manual_test.py generate --grammar-role agreement --grammar-focus subject_verb_agreement

  # 4. Run the full 2-pass pipeline on a single question's raw text
  python scripts/manual_test.py pipeline "The colony of corals ____ an important role in marine ecosystems."

Prerequisites:
  - Docker Postgres running on port 5434 (dsat-postgres container)
  - alembic upgrade head already applied
  - For LLM calls: set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env

This script imports the existing backend modules directly — no HTTP API needed.
"""
import asyncio
import sys
import os
import json
import uuid
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.config import get_settings
from app.database import async_session
from app.models.db import Question, QuestionVersion, QuestionAnnotation, QuestionOption, QuestionJob, QuestionAsset

# ── PDF Ingest (parse + store raw text, no LLM yet) ────────────────────

async def ingest_pdf(pdf_path: str):
    """Parse a PDF, create a question_job + question_assets, store raw text."""
    from app.parsers.pdf_parser import parse_pdf

    settings = get_settings()
    print(f"\n📄 Parsing PDF: {pdf_path}")
    result = parse_pdf(pdf_path)
    total_pages = len(result["pages"])
    total_chars = sum(len(p["text"]) for p in result["pages"])
    print(f"   Pages: {total_pages}, Total chars: {total_chars:,}")

    # Create DB records
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Combine all page text for raw_content
    raw_content = "\n\n".join(p["text"] for p in result["pages"])

    async with async_session() as session:
        # Create question_asset
        asset = QuestionAsset(
            id=asset_id,
            content_origin="official",
            asset_type="pdf",
            storage_path=pdf_path,
            mime_type="application/pdf",
            page_start=0,
            page_end=total_pages - 1,
            source_name=os.path.basename(pdf_path),
            checksum="",
            created_at=now,
        )
        session.add(asset)

        # Create question_job in 'parsing' state (will need manual LLM step)
        job = QuestionJob(
            id=job_id,
            job_type="ingest",
            content_origin="official",
            input_format="pdf",
            status="parsing",
            provider_name=settings.default_annotation_provider,
            model_name=settings.default_annotation_model,
            prompt_version="v3.0",
            rules_version=settings.rules_version,
            raw_asset_id=asset_id,
            pass1_json={"raw_text": raw_content[:50000], "pages": total_pages},
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        await session.commit()

    print(f"\n✅ Created:")
    print(f"   question_assets.id = {asset_id}")
    print(f"   question_jobs.id   = {job_id}")
    print(f"   Status: parsing (ready for LLM extract step)")
    print(f"\n   Next step: run `python scripts/manual_test.py pipeline-raw {job_id}`")
    print(f"   to send the raw text through the 2-pass LLM pipeline.")
    return job_id


async def pipeline_raw(job_id_str: str):
    """Take an existing job's raw text and run it through the 2-pass LLM pipeline."""
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt
    from app.parsers.json_parser import extract_json_from_text
    from app.pipeline.orchestrator import JobOrchestrator
    from app.pipeline.validator import validate_question

    settings = get_settings()
    job_uuid = uuid.UUID(job_id_str)

    async with async_session() as session:
        job = await session.get(QuestionJob, job_uuid)
        if not job:
            print(f"❌ Job {job_id_str} not found")
            return

        raw_text = job.pass1_json.get("raw_text", "") if job.pass1_json else ""
        if not raw_text:
            print("❌ No raw_text in job.pass1_json")
            return

        print(f"\n🔄 Running 2-pass pipeline for job {job_id_str}")
        print(f"   Raw text length: {len(raw_text):,} chars")

        # ── Pass 1: Extract ────────────────────────────────────────────
        provider = get_provider(
            settings.default_annotation_provider,
            api_key=settings.anthropic_api_key or settings.openai_api_key,
        )
        orch = JobOrchestrator(str(job.id), job.content_origin, job.job_type)

        # Advance to extracting
        orch.advance()  # parsing → extracting
        job.status = "extracting"
        print(f"\n   Pass 1: Extracting... (provider={settings.default_annotation_provider}, model={settings.default_annotation_model})")

        system, user = build_extract_prompt(raw_text[:30000])
        try:
            result = await provider.complete(system=system, user=user)
            extract_json = extract_json_from_text(result.raw_text)
            job.pass1_json = {**extract_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
            print(f"   ✅ Pass 1 complete ({result.latency_ms}ms)")
            print(f"   Extracted: {json.dumps(extract_json, indent=2)[:500]}...")
        except Exception as e:
            orch.fail("extracting", "llm_error", str(e))
            job.status = "failed"
            job.validation_errors_jsonb = [{"step": "extracting", "error": str(e)}]
            await session.commit()
            print(f"   ❌ Pass 1 failed: {e}")
            return

        # ── Pass 2: Annotate ───────────────────────────────────────────
        orch.advance()  # extracting → annotating
        job.status = "annotating"
        print(f"\n   Pass 2: Annotating...")

        system, user = build_annotate_prompt(extract_json)
        try:
            result = await provider.complete(system=system, user=user, max_tokens=8192)
            annotate_json = extract_json_from_text(result.raw_text)
            job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
            print(f"   ✅ Pass 2 complete ({result.latency_ms}ms)")
        except Exception as e:
            orch.fail("annotating", "llm_error", str(e))
            job.status = "failed"
            job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
            await session.commit()
            print(f"   ❌ Pass 2 failed: {e}")
            return

        # ── Validate ───────────────────────────────────────────────────
        orch.advance()  # annotating → validating
        job.status = "validating"

        merged = {**extract_json, **annotate_json}
        errors = validate_question(merged, content_origin=job.content_origin)
        job.validation_errors_jsonb = errors

        if any(e["severity"] == "blocking" for e in errors):
            job.status = "needs_review"
            print(f"\n   ⚠️  Validation found blocking errors:")
            for e in errors:
                print(f"      [{e['severity']}] {e['field']}: {e['message']}")
        else:
            job.status = "approved"
            print(f"\n   ✅ Validation passed")

        # ── Create question record ─────────────────────────────────────
        question_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        question = Question(
            id=question_id,
            content_origin=job.content_origin,
            source_exam_code=extract_json.get("source_exam_code"),
            source_module_code=extract_json.get("source_module_code"),
            source_question_number=extract_json.get("source_question_number"),
            stimulus_mode_key=extract_json.get("stimulus_mode_key"),
            stem_type_key=extract_json.get("stem_type_key"),
            current_question_text=extract_json.get("question_text", ""),
            current_passage_text=extract_json.get("passage_text"),
            current_correct_option_label=extract_json.get("correct_option_label", ""),
            current_explanation_text=annotate_json.get("explanation_short", ""),
            practice_status="active",
            official_overlap_status="none",
            is_admin_edited=False,
            metadata_managed_by_llm=True,
            created_at=now,
            updated_at=now,
        )
        session.add(question)
        job.question_id = question_id

        await session.commit()
        print(f"\n🎯 Created question: {question_id}")
        print(f"   Job status: {job.status}")
        return question_id


# ── Recall questions ───────────────────────────────────────────────────

async def recall_questions(grammar_focus: str = None, limit: int = 10):
    """Query questions from DB and display them."""
    from sqlalchemy import select

    async with async_session() as session:
        stmt = select(Question).where(Question.practice_status == "active").limit(limit)
        if grammar_focus:
            stmt = stmt.join(QuestionAnnotation, Question.id == QuestionAnnotation.question_id)
            stmt = stmt.where(QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == grammar_focus)

        result = await session.execute(stmt)
        questions = result.scalars().all()

        if not questions:
            print("\n📭 No questions found in database.")
            print("   Run `python scripts/manual_test.py ingest-pdf <path>` first.")
            return

        print(f"\n📋 Found {len(questions)} question(s):\n")
        for q in questions:
            print(f"  ID: {q.id}")
            print(f"  Origin: {q.content_origin}  Status: {q.practice_status}")
            print(f"  Q: {q.current_question_text[:100]}...")
            print(f"  Passage: {(q.current_passage_text or 'none')[:80]}...")
            print(f"  Answer: {q.current_correct_option_label}")
            print()


# ── Generate question ──────────────────────────────────────────────────

async def generate_question(grammar_role: str, grammar_focus: str, syntactic_trap: str = "none", difficulty: str = "medium"):
    """Generate a new question using the LLM."""
    from app.llm.factory import get_provider
    from app.prompts.generate_prompt import build_generate_prompt
    from app.parsers.json_parser import extract_json_from_text

    settings = get_settings()
    provider = get_provider(
        settings.default_annotation_provider,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
    )

    request = {
        "target_grammar_role_key": grammar_role,
        "target_grammar_focus_key": grammar_focus,
        "target_syntactic_trap_key": syntactic_trap,
        "difficulty_overall": difficulty,
    }

    print(f"\n🧬 Generating question:")
    print(f"   Role: {grammar_role}, Focus: {grammar_focus}")
    print(f"   Trap: {syntactic_trap}, Difficulty: {difficulty}")

    system, user = build_generate_prompt(generation_request=request)
    result = await provider.complete(system=system, user=user, max_tokens=8192, temperature=0.7)

    try:
        generated = extract_json_from_text(result.raw_text)
        print(f"\n✅ Generated ({result.latency_ms}ms):\n")
        print(json.dumps(generated, indent=2))
    except ValueError as e:
        print(f"\n❌ Could not parse LLM output: {e}")
        print(f"   Raw output:\n{result.raw_text[:2000]}")


# ── Direct pipeline on text (no PDF, no DB) ────────────────────────────

async def pipeline_text(raw_text: str):
    """Run the 2-pass pipeline directly on a text string. Quick test."""
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt
    from app.parsers.json_parser import extract_json_from_text

    settings = get_settings()
    provider = get_provider(
        settings.default_annotation_provider,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
    )

    print(f"\n🔄 2-pass pipeline on text ({len(raw_text)} chars)")

    # Pass 1
    system, user = build_extract_prompt(raw_text)
    print("   Pass 1: Extracting...")
    result1 = await provider.complete(system=system, user=user)
    extract_json = extract_json_from_text(result1.raw_text)
    print(f"   ✅ Pass 1 done ({result1.latency_ms}ms)")
    print(json.dumps(extract_json, indent=2)[:1000])

    # Pass 2
    system, user = build_annotate_prompt(extract_json)
    print("\n   Pass 2: Annotating...")
    result2 = await provider.complete(system=system, user=user, max_tokens=8192)
    annotate_json = extract_json_from_text(result2.raw_text)
    print(f"   ✅ Pass 2 done ({result2.latency_ms}ms)")
    print(json.dumps(annotate_json, indent=2)[:2000])


# ── CLI entry point ────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "ingest-pdf":
        if len(sys.argv) < 3:
            print("Usage: manual_test.py ingest-pdf <path-to-pdf>")
            sys.exit(1)
        asyncio.run(ingest_pdf(sys.argv[2]))

    elif command == "pipeline-raw":
        if len(sys.argv) < 3:
            print("Usage: manual_test.py pipeline-raw <job-id>")
            sys.exit(1)
        asyncio.run(pipeline_raw(sys.argv[2]))

    elif command == "recall":
        grammar_focus = None
        limit = 10
        for i, arg in enumerate(sys.argv[2:], 2):
            if arg == "--grammar-focus" and i + 1 < len(sys.argv):
                grammar_focus = sys.argv[i + 1]
            elif arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
        asyncio.run(recall_questions(grammar_focus=grammar_focus, limit=limit))

    elif command == "generate":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--grammar-role", required=True)
        parser.add_argument("--grammar-focus", required=True)
        parser.add_argument("--syntactic-trap", default="none")
        parser.add_argument("--difficulty", default="medium")
        args = parser.parse_args(sys.argv[2:])
        asyncio.run(generate_question(
            grammar_role=args.grammar_role,
            grammar_focus=args.grammar_focus,
            syntactic_trap=args.syntactic_trap,
            difficulty=args.difficulty,
        ))

    elif command == "pipeline":
        if len(sys.argv) < 3:
            print("Usage: manual_test.py pipeline \"<question text>\"")
            sys.exit(1)
        asyncio.run(pipeline_text(sys.argv[2]))

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()