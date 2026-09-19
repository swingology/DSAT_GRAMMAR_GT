#!/usr/bin/env python
"""Extract CB MyPractice question-bank PDF(s) into LLM-readable JSON.

Usage: uv run --with pymupdf python extract_cb_bank.py <input.pdf> <output.json>

Emits one object per question: question_id, question_family_key,
skill_family_key, domain, skill, difficulty, passage, stem, choices,
correct_answer. Rationale text is intentionally excluded.
"""
import json
import re
import sys
import unicodedata
from datetime import date

import pymupdf

# KEYS_MASTER.md QUESTION_FAMILY_KEYS, keyed by the PDF's Domain label
FAMILY_BY_DOMAIN = {
    "Information and Ideas": "information_and_ideas",
    "Craft and Structure": "craft_and_structure",
    "Expression of Ideas": "expression_of_ideas",
    "Standard English Conventions": "conventions_grammar",
}

# PDF Skill label -> READING_SKILL_FAMILY_KEYS (grammar skills snake_cased)
SKILL_FAMILY = {
    "Central Ideas and Details": "central_ideas_and_details",
    "Command of Evidence": "command_of_evidence",  # textual/quantitative derived from stem
    "Cross-Text Connections": "cross_text_connections",
    "Inferences": "inferences",
    "Text Structure and Purpose": "text_structure_and_purpose",
    "Words in Context": "words_in_context",
    "Boundaries": "boundaries",
    "Form, Structure, and Sense": "form_structure_and_sense",
    "Rhetorical Synthesis": "rhetorical_synthesis",
    "Transitions": "transitions",
}

# Question-opening phrases. Some questions start mid-line after the stimulus
# (vocab "As used in the text...", synthesis goal sentences, "Assuming..."
# research stems), so both the line-anchored walk and the in-stem re-split
# key off this list.
QUESTION_START = (
    r"Which|What|According to|Based on|In which|It can be"
    r"|As used in the text|Information in the text|The text makes"
    r"|Taken together|Assuming"
)
STEM_START = re.compile(rf"^(?:{QUESTION_START})\b")
Q_SPLIT = re.compile(rf"\b(?:{QUESTION_START})\b")


def clean(s: str) -> str:
    s = s.replace("\xa0", " ")
    return " ".join(s.split())


def parse_label_value(lines: list[str], label: str, known: dict | list) -> str:
    """Join wrapped lines after a label until the join matches known values."""
    keys = {k.lower(): k for k in (known if isinstance(known, dict) else {k: None for k in known})}
    for i, ln in enumerate(lines):
        if ln.strip() == label:
            for n in (1, 2, 3):
                j = clean(" ".join(lines[i + 1 : i + 1 + n]))
                if j.lower() in keys:
                    return j
                if n >= 3:
                    return j  # best effort; validation will flag it
    return ""


def parse_block(block: str) -> dict:
    block = block.replace("\xa0", " ")
    lines = block.split("\n")
    qid = re.match(r"Question ID ([0-9a-f]{8})", lines[0]).group(1)

    # choices: lines from "A. " through the line before "ID: <qid> Answer"
    idxA = next(i for i, ln in enumerate(lines) if re.match(r"^A\. ", ln))
    idx_end = next(i for i, ln in enumerate(lines) if re.match(r"^ID: [0-9a-f]{8} Answer$", ln))
    labels = {"A": idxA}
    prev = idxA
    for letter in ("B", "C", "D"):
        prev = next(
            i for i, ln in enumerate(lines) if i > prev and re.match(rf"^{letter}\. ", ln)
        )
        labels[letter] = prev
    choices = {}
    for letter, start in labels.items():
        stop = labels.get(chr(ord(letter) + 1), idx_end)
        raw = " ".join(lines[start:stop])
        choices[letter] = clean(raw[len(letter) + 2 :])  # drop "A. " prefix

    # stem: walk backwards from choice A until a line starts with a stem word
    i = idxA - 1
    stem_lines = []
    while i >= 2 and lines[i].strip():
        stem_lines.insert(0, lines[i])
        if STEM_START.match(lines[i].strip()):
            break
        i -= 1
    stem = clean(" ".join(stem_lines))
    passage = clean(" ".join(lines[2:i]))

    # questions that start mid-line (synthesis goal sentences, vocab
    # "As used in the text", "Assuming..." research stems) defeat the
    # backward walk: the whole passage lands in the stem. Re-split at the
    # first question phrase; keep the "The student wants..." goal sentence
    # with the stem, everything before it goes back to the passage.
    m = Q_SPLIT.search(stem)
    if m and m.start() > 0:
        head, tail = stem[: m.start()].rstrip(), stem[m.start():]
        goal = re.search(r"(?:The|This) (?:student|writer|researcher) wants to .*$", head, re.S)
        if goal:
            head, stem = head[: goal.start()].rstrip(), head[goal.start() :] + " " + tail
        else:
            stem = tail
        if head:
            passage = (head + " " + passage).strip()

    domain = parse_label_value(lines, "Domain", list(FAMILY_BY_DOMAIN))
    skill = parse_label_value(lines, "Skill", list(SKILL_FAMILY))
    difficulty = ""
    m = re.search(r"Question Difficulty: (\w+)", block)
    if m:
        difficulty = m.group(1)
    correct = ""
    m = re.search(r"Correct Answer: ([A-D])", block)
    if m:
        correct = m.group(1)

    family = FAMILY_BY_DOMAIN.get(domain, "")
    skey = SKILL_FAMILY.get(skill, skill.lower().replace(" ", "_").replace(",", "").replace("'", ""))
    if skey == "command_of_evidence":
        skey = (
            "command_of_evidence_quantitative"
            if re.search(r"\b(graph|table|data in the)\b", stem, re.I)
            else "command_of_evidence_textual"
        )

    return {
        "question_id": qid,
        "question_family_key": family,
        "skill_family_key": skey,
        "domain": domain,
        "skill": skill,
        "difficulty": difficulty,
        "passage": passage,
        "stem": stem,
        "choices": choices,
        "correct_answer": correct,
    }


def extract(pdf_path: str) -> list[dict]:
    doc = pymupdf.open(pdf_path)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    blocks = re.split(r"(?=Question ID [0-9a-f]{8})", text)
    return [parse_block(b) for b in blocks[1:]]


def validate(qs: list[dict]) -> int:
    problems = 0
    for q in qs:
        errs = []
        if not q["question_family_key"]:
            errs.append("no family key")
        if not q["skill_family_key"] or " " in q["skill_family_key"]:
            errs.append(f"bad skill key {q['skill_family_key']!r}")
        if len(q["choices"]) != 4 or any(not v for v in q["choices"].values()):
            errs.append("bad choices")
        if q["correct_answer"] not in "ABCD" or len(q["correct_answer"]) != 1:
            errs.append("no correct answer")
        if not q["stem"].endswith("?"):
            errs.append(f"stem not a question: {q['stem'][:60]!r}")
        if not q["passage"]:
            errs.append("empty passage")
        if not q["difficulty"]:
            errs.append("no difficulty")
        if errs:
            problems += 1
            print(f"  !! {q['question_id']}: {', '.join(errs)}")
    print(f"validation: {problems} problem(s) out of {len(qs)}")
    return problems


def main():
    pdf_path, out_path = sys.argv[1], sys.argv[2]
    qs = extract(pdf_path)
    problems = validate(qs)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_pdf": pdf_path.split("/")[-1],
                "extracted_at": date.today().isoformat(),
                "question_count": len(qs),
                "questions": qs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"wrote {len(qs)} questions -> {out_path}")
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()