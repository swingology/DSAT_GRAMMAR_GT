#!/usr/bin/env python
"""Verify cb_verbal_master.json. Exit 1 on any failure.

Two independent extractions of the same PDFs must agree: the layout-based master
(build_master.py) and the older flat-text extraction
(09_2026/09_2026_New_Verbal_Bank_full.json). The flat one loses structure but not
words, so word-for-word agreement means the master dropped and invented nothing.

Usage: python3 CB_QUESTION_BANK/verify_master.py [-v]
"""
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
VERBOSE = "-v" in sys.argv


SUPSUB = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₀₁₂₃₄₅₆₇₈₉₊₋"


def words(s: str) -> collections.Counter:
    # The flat extraction drops super/subscripts entirely, so ignore them when comparing.
    s = s.translate({ord(c): None for c in SUPSUB})
    return collections.Counter(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def all_stimulus_text(q: dict) -> str:
    s = q["stimulus"]
    parts = list(s["paragraphs"]) + s.get("notes", [])
    for t in s.get("texts", []):
        parts += [t["label"]] + t["paragraphs"]
    if "table" in s:
        parts += [s["table"]["title"] or ""] + s["table"]["header"] + [c for r in s["table"]["rows"] for c in r]
    if "figure" in s:
        f = s["figure"]
        parts += [f["title"] or ""] + f["labels"] + f["axis_labels"]
    return " ".join(parts)


def main() -> None:
    M = json.load(open(HERE / "cb_verbal_master.json"))["questions"]
    F = {q["question_id"]: q for q in
         json.load(open(HERE / "09_2026/09_2026_New_Verbal_Bank_full.json"))["questions"]}
    fails = collections.defaultdict(list)
    flat_defects: list[str] = []

    ids = [q["question_id"] for q in M]
    if len(ids) != len(set(ids)):
        fails["duplicate ids"].append("-")
    if set(ids) != set(F):
        fails["id set differs from flat extraction"].append(f"{len(set(ids) ^ set(F))} ids")

    for q in M:
        qid, s, f = q["question_id"], q["stimulus"], F.get(q["question_id"])
        for k in ("domain", "skill", "passage", "question"):
            if not q[k]:
                fails[f"empty {k}"].append(qid)
        if sorted(q["choices"]) != ["A", "B", "C", "D"] or not all(q["choices"].values()):
            fails["choices not A-D / empty"].append(qid)
        if q["correct_answer"] not in ("A", "B", "C", "D"):
            fails["no correct answer"].append(qid)
        if q["difficulty"] not in ("Easy", "Medium", "Hard"):
            fails["no difficulty"].append(qid)
        if not q["rationale"]:
            fails["no rationale"].append(qid)
        if not q["question"].rstrip().endswith("?"):
            fails["question does not end with '?'"].append(qid)

        # structure must match the skill / the question's own wording
        if (q["skill"] == "Rhetorical Synthesis") != (s["kind"] == "notes"):
            fails["notes <-> Rhetorical Synthesis"].append(qid)
        if s["kind"] == "notes" and len(s["notes"]) < 2:
            fails["fewer than 2 notes"].append(qid)
        if (q["skill"] == "Cross-Text Connections") != (s["kind"] == "paired"):
            fails["paired <-> Cross-Text"].append(qid)
        wants_table = bool(re.search(r"\btable\b", q["question"], re.I))
        wants_graph = bool(re.search(r"\bgraph\b", q["question"], re.I))
        if wants_table and "table" not in s:
            fails["question says table, none found"].append(qid)
        if wants_graph and "figure" not in s:
            fails["question says graph, none found"].append(qid)
        if "figure" in s and not (HERE / s["figure"]["image"]).is_file():
            fails["figure image missing on disk"].append(qid)
        if "underlined" in q["question"].lower() and not q["underlined"]:
            fails["question says underlined, none found"].append(qid)

        if f:
            for a, b, name in ((q["domain"], f["domain"], "domain"), (q["skill"], f["skill"], "skill"),
                               (q["correct_answer"], f["correct_answer"], "answer"),
                               (q["difficulty"], f["difficulty"], "difficulty")):
                if a != b:
                    fails[f"{name} differs from flat extraction"].append(qid)
            # whitespace-insensitive: "( C)" in the flat file is "(¹³C)" here
            strip = lambda x: re.sub(r"\s+", "", x.translate({ord(c): None for c in SUPSUB}))
            for k in "ABCD":
                a, b = strip(q["choices"].get(k, "")), strip(f["choices"][k])
                if a == b:
                    continue
                # known defect of the FLAT extraction: the page header leaks into the last
                # choice of a question that spills onto a second page
                if b.startswith(a) and "AssessmentSAT" in b:
                    flat_defects.append(qid)
                else:
                    fails["choices differ from flat extraction"].append(qid)
            new = words(all_stimulus_text(q) + " " + q["question"])
            old = words(f["passage"] + " " + f["stem"])
            if new != old:
                fails["stimulus+question words differ from flat extraction"].append(qid)
                if VERBOSE and len(fails["stimulus+question words differ from flat extraction"]) <= 6:
                    print(f"  {qid} [{s['kind']}] only-new={dict((new - old).most_common(6))} "
                          f"only-old={dict((old - new).most_common(6))}")

    print(f"{len(M)} questions | kinds {dict(collections.Counter(q['stimulus']['kind'] for q in M))}")
    print(f"underlined spans recorded: {sum(1 for q in M if q['underlined'])}")
    print(f"super/subscripts recovered in: {sum(1 for q in M if any(c in json.dumps(q, ensure_ascii=False) for c in SUPSUB))} questions")
    print(f"defects found in the OLD flat extraction (header leaked into a choice): {len(set(flat_defects))}")
    if not fails:
        print("ALL CHECKS PASSED")
        return
    for name, qids in sorted(fails.items(), key=lambda kv: -len(kv[1])):
        print(f"  FAIL {len(qids):5d}  {name}   e.g. {qids[:4]}")
    sys.exit(1)


if __name__ == "__main__":
    main()
