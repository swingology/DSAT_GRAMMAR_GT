#!/usr/bin/env python
"""Data-integrity verification: question-bank JSON vs its source PDF.

Usage: uv run --with pymupdf python verify_cb_bank.py <input.pdf> <extracted.json>

Re-derives question blocks from the PDF with independent logic and checks
the JSON against them: coverage, field completeness, verbatim fidelity
(every passage/stem/choice word appears in the PDF, in order), stem
boundary placement, metadata match, and cross-record sanity.
Exit 1 on any failure.
"""
import json
import re
import sys
from collections import Counter

import pymupdf

QUESTION_START = (
    r"Which|What|According to|Based on|In which|It can be"
    r"|As used in the text|Information in the text|The text makes"
    r"|Taken together|Assuming"
)
GOAL = r"(?:The|This) (?:student|writer|researcher) wants to"
Q_SPLIT = re.compile(rf"\b(?:{QUESTION_START})\b")


def words(s: str) -> list[str]:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).split()


def flat(s: str) -> str:
    return " ".join(s.replace("\xa0", " ").split())


def main() -> None:
    pdf_path, json_path = sys.argv[1], sys.argv[2]
    doc = pymupdf.open(pdf_path)
    text = "".join(p.get_text() for p in doc)
    doc.close()

    data = json.load(open(json_path))
    qs = data["questions"]
    qmap = {q["question_id"]: q for q in qs}
    fails: list[str] = []

    def fail(qid: str, msg: str) -> None:
        fails.append(f"{qid}: {msg}")

    # 1. coverage: every PDF question present exactly once in the JSON
    pdf_ids = re.findall(r"Question ID ([0-9a-f]{8})", text)
    if len(pdf_ids) != len(qs):
        fail("PDF", f"{len(pdf_ids)} questions in PDF vs {len(qs)} in JSON")
    if [i for i, n in Counter(pdf_ids).items() if n > 1]:
        fail("PDF", "duplicate Question IDs inside the PDF")
    if set(pdf_ids) ^ set(qmap):
        fail("PDF", f"id set mismatch: {set(pdf_ids) ^ set(qmap)}")
    if data.get("question_count") != len(qs):
        fail("JSON", "header question_count != len(questions)")

    bmap: dict[str, str] = {}
    for m in re.finditer(r"Question ID ([0-9a-f]{8}).*?(?=Question ID [0-9a-f]{8}|\Z)", text, re.S):
        bmap[m.group(1)] = m.group(0)

    answer_dist: Counter[str] = Counter()
    seen: Counter[tuple[str, str]] = Counter()
    extra_report: list[tuple[int, str]] = []

    for q in qs:
        qid = q["question_id"]
        block = bmap[qid]
        bflat = flat(block)
        lines = block.replace("\xa0", " ").split("\n")

        # 2. field completeness
        if set(q["choices"]) != set("ABCD") or any(not v.strip() for v in q["choices"].values()):
            fail(qid, "choices incomplete")
        if len(set(q["choices"].values())) != 4:
            fail(qid, "duplicate choice text")
        if q["correct_answer"] not in "ABCD" or len(q["correct_answer"]) != 1:
            fail(qid, f"bad answer {q['correct_answer']!r}")
        if q["difficulty"] not in ("Easy", "Medium", "Hard"):
            fail(qid, f"bad difficulty {q['difficulty']!r}")
        if not q["question_family_key"] or not q["skill_family_key"]:
            fail(qid, "missing family key")
        if not q["passage"].strip():
            fail(qid, "empty passage")
        if not q["stem"].endswith("?"):
            fail(qid, f"stem not a question: {q['stem'][:50]!r}")

        # 3. verbatim fidelity: every JSON word must appear in the PDF
        #    stimulus region, in order (catches invented text, reordering,
        #    and rationale leakage into fields)
        stop = next(i for i, ln in enumerate(lines) if ln.strip() == f"ID: {qid} Answer")
        head_words = words(" ".join(lines[2:stop]))
        jw = words(" ".join([q["passage"], q["stem"], *(q["choices"][k] for k in "ABCD")]))
        it = iter(head_words)
        missing = [w for w in jw if w not in it]
        if missing:
            fail(qid, f"{len(missing)} word(s) not found in order in PDF: {missing[:5]}")

        # dropped-content report: PDF words unaccounted for by JSON fields
        # (choice labels A./B./C./D. account for the expected 4)
        extras = sum((Counter(head_words) - Counter(jw)).values())
        extra_report.append((extras, qid))

        # 4. stem boundary: first question phrase at stem start, or preceded
        #    only by a synthesis goal sentence
        m = Q_SPLIT.search(q["stem"])
        if not m:
            fail(qid, "no question phrase in stem")
        elif m.start() > 0 and not re.match(rf"^(?:{GOAL})", q["stem"][: m.start()]):
            fail(qid, f"text before question phrase: {q['stem'][: m.start()][:60]!r}")

        # 5. metadata verbatim from the PDF block
        if f"Correct Answer: {q['correct_answer']}" not in bflat:
            fail(qid, "answer key not found in PDF")
        if f"Question Difficulty: {q['difficulty']}" not in bflat:
            fail(qid, "difficulty not found in PDF")
        if q["domain"] not in bflat:
            fail(qid, f"domain {q['domain']!r} not found in PDF")
        if q["skill"] not in bflat:
            fail(qid, f"skill {q['skill']!r} not found in PDF")

        # 6. skill-specific shape invariants (both official CB vocab formats)
        if q["skill_family_key"] == "words_in_context" and not (
            q["stem"].startswith("As used in the text")
            or q["stem"].startswith("Which choice completes the text")
        ):
            fail(qid, f"vocab stem malformed: {q['stem'][:50]!r}")

        answer_dist[q["correct_answer"]] += 1
        seen[(q["passage"], q["stem"])] += 1

    # 7. cross-record sanity
    if [k for k, n in seen.items() if n > 1]:
        fail("JSON", "duplicate passage+stem pairs across records")
    if set("ABCD") - set(answer_dist):
        fail("JSON", f"answer letters never used: {set('ABCD') - set(answer_dist)}")

    print(f"answer distribution: {dict(sorted(answer_dist.items()))}")
    print("content dropped from PDF (words beyond the 4 choice labels), top 10:")
    for extras, qid in sorted(extra_report, reverse=True)[:10]:
        print(f"  {qid}: {extras - 4}")
    if fails:
        print(f"\nFAILURES ({len(fails)}):")
        for f in fails[:40]:
            print("  !!", f)
        if len(fails) > 40:
            print(f"  ... and {len(fails) - 40} more")
    print(f"integrity: {len(fails)} failure(s) out of {len(qs)} questions")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()