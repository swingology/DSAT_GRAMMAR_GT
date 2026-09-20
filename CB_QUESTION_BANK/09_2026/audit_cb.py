#!/usr/bin/env python
"""Independent audit of CB verbal PDFs: Question ID / Domain / Skill / Difficulty."""
import json, re, sys, collections, pathlib
import pymupdf

ROOT = pathlib.Path("/home/jb/DSAT_REDUX_MD/CB_QUESTION_BANK")
PDFS = [
    "09_2026/09_2026_New_Verbal_Bank.pdf",
    "09_2026/09_2026_New_Verbal_Bank  - Questions ONLY.pdf",
    "09_2026/MyPractice - Question Bank - Results - easy.pdf",
    "09_2026/MyPractice - Question Bank - Results medium.pdf",
    "09_2026/MyPractice - Question Bank - Results - Verbal Hard.pdf",
    "MyPractice - Question Bank - Results - exclude active.pdf",
    "MyPractice - Question Bank - Results part 2.pdf",
    "MyPractice - Question Bank - Results11.pdf",
    "MyPractice - Question Bank - part 1 page 1-5.pdf",
]

def blocks(path):
    doc = pymupdf.open(path)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    return re.split(r"(?=Question ID [0-9a-f]{8})", text)[1:]

def field(lines, label, maxjoin=3):
    """Label sits alone on a line; value wraps over following lines until next known label."""
    STOP = {"Question ID","ID","Assessment","Test","Domain","Skill","Difficulty",
            "Question Difficulty:","Correct Answer:","Rationale","Answer"}
    for i, ln in enumerate(lines):
        if ln.strip() == label:
            parts = []
            for j in range(i+1, min(i+1+maxjoin, len(lines))):
                s = lines[j].strip()
                if not s or s in STOP or s.startswith("ID: "):
                    break
                parts.append(s)
            return " ".join(parts)
    return ""

def norm(s):
    return " ".join(s.replace("\xa0"," ").split())

rows = []
per_pdf = {}
for rel in PDFS:
    p = ROOT / rel
    if not p.exists():
        print(f"MISSING {rel}"); continue
    recs = []
    for b in blocks(str(p)):
        b = b.replace("\xa0"," ")
        lines = b.split("\n")
        qid = re.match(r"Question ID ([0-9a-f]{8})", lines[0]).group(1)
        d = norm(field(lines, "Domain"))
        s = norm(field(lines, "Skill"))
        m = re.search(r"Question Difficulty:\s*(\w+)", b)
        diff = m.group(1) if m else ""
        ca = re.search(r"Correct Answer:\s*([A-D])", b)
        asmt = norm(field(lines, "Assessment", 1))
        test = norm(field(lines, "Test", 2))
        recs.append(dict(qid=qid, domain=d, skill=s, difficulty=diff,
                         correct=ca.group(1) if ca else "", assessment=asmt, test=test,
                         pdf=rel))
    per_pdf[rel] = recs
    rows.extend(recs)
    print(f"{len(recs):5d}  {rel}")

print("\n=== per-PDF domain x skill (raw labels) ===")
for rel, recs in per_pdf.items():
    c = collections.Counter((r["domain"], r["skill"]) for r in recs)
    print(f"\n-- {rel} ({len(recs)} q, {len(c)} combos)")
    for (d, s), n in sorted(c.items()):
        print(f"   {n:4d}  {d!r} | {s!r}")

print("\n=== ASSESSMENT / TEST values ===")
print(collections.Counter((r["assessment"], r["test"]) for r in rows))

print("\n=== difficulty values ===")
print(collections.Counter(r["difficulty"] for r in rows))

print("\n=== blank fields ===")
print("blank domain:", sum(1 for r in rows if not r["domain"]),
      "| blank skill:", sum(1 for r in rows if not r["skill"]),
      "| blank diff:", sum(1 for r in rows if not r["difficulty"]),
      "| blank correct:", sum(1 for r in rows if not r["correct"]))

json.dump(rows, open("/tmp/claude-1000/-home-jb-DSAT-REDUX-MD/636cbe72-4606-428d-8f8d-631620aa6c65/scratchpad/cb_rows.json","w"), indent=1)
print(f"\ntotal rows {len(rows)}")
