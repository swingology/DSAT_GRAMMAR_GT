"""
One-time migration: split concatenated passage+stem in current_question_text
into separate current_passage_text (passage body) and current_question_text (stem).

Affects questions where current_passage_text is null/empty and current_question_text
contains both the passage and the question stem joined as one string.

Updates both:
  - questions.current_passage_text / current_question_text
  - question_versions.passage_text / question_text  (for the latest version)

Safe to re-run — skips questions that already have current_passage_text populated.
"""
import re
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.db import Question, QuestionVersion


# Patterns that mark the start of a question stem
STEM_STARTERS = [
    re.compile(r'Which choice\b'),
    re.compile(r'Which finding\b'),
    re.compile(r'Which quotation\b'),
    re.compile(r'Which statement\b'),
    re.compile(r'As used in the text\b'),
    re.compile(r'According to the text\b'),
    re.compile(r'Based on the text\b'),
    re.compile(r'It can (?:most )?reasonably be inferred\b'),
    re.compile(r'Compared to\b'),
    re.compile(r'Which (?:detail|example|idea|information)\b'),
]


def split_passage_and_stem(text: str) -> tuple[str | None, str]:
    """
    Split a combined passage+stem string.
    Returns (passage, stem) — passage is None if no split point found.
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())

    for i in range(len(sentences) - 1, 0, -1):
        candidate = ' '.join(sentences[i:])
        if any(pat.search(candidate) for pat in STEM_STARTERS):
            passage = ' '.join(sentences[:i]).strip()
            stem = candidate.strip()
            if passage:  # Only split when there's a real passage body
                return passage, stem

    return None, text  # No split found — entire text is the stem


async def main(dry_run: bool = True):
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch all active questions with empty passage
        result = await session.execute(
            select(Question)
            .where(
                Question.practice_status == 'active',
                (Question.current_passage_text == None) |  # noqa: E711
                (Question.current_passage_text == ''),
            )
        )
        questions = result.scalars().all()

        print(f"Found {len(questions)} questions with empty passage_text\n")

        updated = 0
        skipped = 0

        for q in questions:
            original_text = q.current_question_text or ''
            passage, stem = split_passage_and_stem(original_text)

            if passage is None:
                skipped += 1
                print(f"  SKIP  {q.id} — no passage body detected")
                print(f"        stem: {stem[:80]}...")
                continue

            print(f"  SPLIT {q.id}")
            print(f"        passage: {passage[:80]}...")
            print(f"        stem:    {stem[:80]}...")

            if not dry_run:
                # Update questions table
                await session.execute(
                    update(Question)
                    .where(Question.id == q.id)
                    .values(
                        current_passage_text=passage,
                        current_question_text=stem,
                    )
                )

                # Update the latest question_version too
                if q.latest_version_id:
                    await session.execute(
                        update(QuestionVersion)
                        .where(QuestionVersion.id == q.latest_version_id)
                        .values(
                            passage_text=passage,
                            question_text=stem,
                        )
                    )

            updated += 1

        if not dry_run:
            await session.commit()
            print(f"\nCommitted. Updated {updated}, skipped {skipped}.")
        else:
            print(f"\nDRY RUN — would update {updated}, skip {skipped}.")
            print("Re-run with --apply to commit changes.")

    await engine.dispose()


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    asyncio.run(main(dry_run=dry_run))
