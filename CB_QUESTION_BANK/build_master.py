#!/usr/bin/env python
"""Build cb_verbal_master.json — the structured master base of every CB verbal PDF.

Reads page LAYOUT (fonts, positions, vector drawings), not flat text, so the things
flat extraction destroys are kept:

  notes      bulleted notes stay a list        (bullets are small filled dots at the left)
  paired     Text 1 / Text 2 stay separate     (labels are set in Roboto-Black)
  table      tables stay rows and cells        (ruled grid -> find_tables, clipped)
  figure     graph text is kept OUT of the passage and the figure is rendered to PNG
             (all graph text is set in CrimsonText; prose is Roboto)
  underline  the underlined words are recorded (a filled stroke under the words)
  rationale  College Board's explanation is included

Every verbal PDF under CB_QUESTION_BANK/ is read. A question that appears in several
PDFs is stored once, from the copy that has an answer and rationale, with every PDF it
appears in listed under `appears_in`. Adding a new CB export and re-running is enough.

Bar heights / line positions inside a graph are NOT digitised: the figure is an image
plus its title and labels. Reading values off it needs a vision model.

Usage: uv run --with pymupdf python CB_QUESTION_BANK/build_master.py [--limit N] [-v]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
from datetime import date

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "09_2026"))
from audit_labels import SKILL_CANON, discover, field  # noqa: E402
from extract_cb_bank import FAMILY_BY_DOMAIN, SKILL_FAMILY  # noqa: E402

OUT = HERE / "cb_verbal_master.json"
FIG_DIR = HERE / "figures"
QUANT_STEM = re.compile(r"\b(graph|table|data in the)\b", re.I)
CHOICE = re.compile(r"^([A-D])\.\s+(.*)$")
INK = 0.1176  # fill of underline strokes and bullet dots


def clean(s: str) -> str:
    return " ".join(s.replace("\xa0", " ").split())


class Line:
    __slots__ = ("page", "x0", "y0", "x1", "y1", "font", "size", "text", "rotated")

    def __init__(self, page, bbox, font, size, text, rotated=False):
        self.page, self.font, self.size, self.text = page, font, size, text
        self.x0, self.y0, self.x1, self.y1 = bbox
        self.rotated = rotated  # axis labels run bottom-to-top


SUP = str.maketrans("0123456789+-−", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻")
SUB = str.maketrans("0123456789+-−", "₀₁₂₃₄₅₆₇₈₉₊₋₋")


SCRIPT = re.compile(r"^([0-9+\-−]{1,4})([.,;:)?!]*)$")


def assemble(words: list[tuple]) -> str:
    """Join PDF words (x0, y0, x1, y1, text) into text, restoring super/subscripts.

    A small all-digit word ("13" in (13C), "3" in NH3, "2" in cm2) becomes a real
    super/subscript character and is glued, without a space, to whichever neighbour it
    touches. Normal text is 11.5pt tall here; script digits are under 10.7.
    """
    rows: list[list[tuple]] = []
    for w in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        tall = w[3] - w[1] >= 10.7
        for row in rows:
            ref = next((r for r in row if r[3] - r[1] >= 10.7), row[0])
            if abs((w[1] + w[3]) / 2 - (ref[1] + ref[3]) / 2) < (4 if tall else 7):
                row.append(w)
                break
        else:
            rows.append([w])
    out = []
    for row in rows:
        row.sort(key=lambda w: w[0])
        mains = [w for w in row if w[3] - w[1] >= 10.7]
        mid = sum((w[1] + w[3]) / 2 for w in mains) / len(mains) if mains else None
        text, prev = "", None
        for w in row:
            m = SCRIPT.match(w[4]) if (w[3] - w[1] < 10.7 and mid is not None) else None
            piece = (m.group(1).translate(SUP if (w[1] + w[3]) / 2 < mid else SUB) + m.group(2)) if m else w[4]
            touching = prev is not None and w[0] - prev[0][2] < 1.5 and (m or prev[1])
            text += piece if (not text or touching) else " " + piece
            prev = (w, bool(m))
        out.append(text)
    return " ".join(out)


def page_lines(page, pno: int) -> list[Line]:
    raw = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"]:
            continue
        for ln in b["lines"]:
            text = "".join(s["text"] for s in ln["spans"])
            if text.strip():
                sp = max(ln["spans"], key=lambda s: len(s["text"]))
                raw.append(Line(pno, ln["bbox"], sp["font"], sp["size"], text,
                                rotated=abs(ln["dir"][1]) > 0.5))

    def is_script(l):
        return l.size < 9 and not l.rotated and SCRIPT.match(l.text.strip())

    def same_row(a, b):
        return abs((a.y0 + a.y1) / 2 - (b.y0 + b.y1) / 2) < 7

    # A digit super/subscript arrives as its own small line: after its host, before it
    # (87Sr), or in a gap inside it (NH3 mid-sentence). Attach each to its host row, re-join
    # the pieces the PDF split off around it ('carbon-13, (' + 13 + 'C)'), then rebuild
    # that row's text from word positions so the script lands where it belongs.
    hosts = [l for l in raw if not is_script(l)]
    grew = set()
    for sc in (l for l in raw if is_script(l)):
        host = next((h for h in hosts if h.size >= 9 and not h.rotated and same_row(h, sc)
                     and sc.x1 >= h.x0 - 2 and sc.x0 <= h.x1 + 6), None)
        if host is None:
            hosts.append(sc)          # a lone small number: leave it as it is
            continue
        host.x0, host.x1 = min(host.x0, sc.x0), max(host.x1, sc.x1)
        grew.add(id(host))

    merged = []
    for l in sorted(hosts, key=lambda l: l.x0):
        left = next((h for h in merged if id(h) in grew and same_row(h, l) and not l.rotated
                     and -2 <= l.x0 - h.x1 <= 6), None)
        if left is None:
            merged.append(l)
        else:
            left.x1 = max(left.x1, l.x1)
    if grew:
        words = page.get_text("words")
        for l in merged:
            if id(l) in grew:
                box = pymupdf.Rect(l.x0 - 1, l.y0 - 4, l.x1 + 1, l.y1)
                l.text = assemble([w for w in words if box.contains(
                    pymupdf.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2))])
    # same visual row -> left to right
    return sorted(merged, key=lambda l: (round(l.y0 / 3), l.x0))


def paragraphs(lines: list[Line]) -> list[str]:
    """Group wrapped lines into paragraphs by vertical gap (a new page continues one)."""
    paras, cur, prev = [], [], None
    for l in lines:
        new = prev is not None and (
            (l.page == prev.page and l.y0 - prev.y0 > 1.55 * (prev.y1 - prev.y0) + 3)
            or (l.page != prev.page and prev.x1 < 480))
        if new and cur:
            paras.append(clean(" ".join(cur)))
            cur = []
        cur.append(l.text)
        prev = l
    if cur:
        paras.append(clean(" ".join(cur)))
    return paras


def underlined_text(page, band: pymupdf.Rect, skip: list[pymupdf.Rect]) -> list[str]:
    strokes = []
    for d in page.get_drawings():
        r, fill = d["rect"], d.get("fill")
        if (d["type"] == "f" and fill and abs(fill[0] - INK) < 0.02 and r.height < 2.5
                and r.width > 8 and band.y0 < r.y0 < band.y1
                and not any(r.intersects(s) for s in skip)):
            strokes.append(r)
    if not strokes:
        return []
    words = page.get_text("words")
    runs, prev_y = [], None
    for r in sorted(strokes, key=lambda r: (r.y0, r.x0)):
        hit = [w[4] for w in words
               if (w[1] + w[3]) / 2 < r.y0 <= w[3] + 3
               and min(w[2], r.x1) - max(w[0], r.x0) > 0.5 * (w[2] - w[0])]
        if not hit:
            continue
        if prev_y is not None and r.y0 - prev_y < 20:
            runs[-1].extend(hit)      # stroke on the next wrapped line: same underlined span
        else:
            runs.append(hit)
        prev_y = r.y0
    return [clean(" ".join(run)) for run in runs]


def readable_passage(stim: dict) -> str:
    """One plain-text passage a person can read; the structure stays in `stimulus`."""
    parts = []
    if "figure" in stim:
        f = stim["figure"]
        parts.append(f"[Figure: {f['title'] or 'untitled'} — see {f['image']}]")
    if "table" in stim:
        t = stim["table"]
        rows = [" | ".join(t["header"])] + [" | ".join(r) for r in t["rows"]]
        parts.append((f"[Table: {t['title']}]\n" if t["title"] else "[Table]\n") + "\n".join(rows))
    parts.extend(stim["paragraphs"])
    if "notes" in stim:
        parts.append("\n".join(f"• {n}" for n in stim["notes"]))
    for t in stim.get("texts", []):
        parts.append(t["label"] + "\n" + "\n\n".join(t["paragraphs"]))
    return "\n\n".join(p for p in parts if p)


def render_figure(page, rect: pymupdf.Rect, qid: str) -> str:
    FIG_DIR.mkdir(exist_ok=True)
    rect = (rect + (-6, -6, 6, 6)) & page.rect
    page.get_pixmap(clip=rect, matrix=pymupdf.Matrix(2, 2)).save(FIG_DIR / f"{qid}.png")
    return f"figures/{qid}.png"


def parse_question(doc, pages: list[int]) -> dict | None:
    first = doc[pages[0]]
    text0 = first.get_text().replace("\xa0", " ")
    qid = re.search(r"Question ID ([0-9a-f]{8})", text0).group(1)
    head = text0.split("\n")
    domain, skill = field(head, "Domain"), field(head, "Skill")
    skill = SKILL_CANON.get(skill, skill)

    lines = [l for p in pages for l in page_lines(doc[p], p)]
    id_marks = [i for i, l in enumerate(lines) if "Bold" in l.font and re.match(rf"ID: {qid}\b", l.text.strip())]
    if len(id_marks) < 1:
        return None
    start = id_marks[0]
    answer_i = next((i for i in id_marks if lines[i].text.strip().endswith("Answer")), None)
    body = lines[start + 1: answer_i if answer_i is not None else len(lines)]
    tail = lines[answer_i + 1:] if answer_i is not None else []
    # The header block repeats nowhere, but it sits ABOVE the ID mark on page one, and
    # a tall figure can push the last choices onto page two.
    band = pymupdf.Rect(0, lines[start].y1, first.rect.width,
                        lines[answer_i].y0 if answer_i is not None and lines[answer_i].page == pages[0]
                        else first.rect.height)

    # ---- choices
    ci = next((i for i, l in enumerate(body) if l.x0 < 26 and CHOICE.match(l.text.strip())
               and CHOICE.match(l.text.strip()).group(1) == "A"), None)
    if ci is None:
        return None
    choices, cur = {}, None
    for l in body[ci:]:
        m = CHOICE.match(l.text.strip()) if l.x0 < 26 else None
        if m and m.group(1) not in choices:
            cur = m.group(1)
            choices[cur] = m.group(2)
        elif cur:
            choices[cur] += " " + l.text
    choices = {k: clean(v) for k, v in choices.items()}
    stim_lines = body[:ci]

    # ---- figure: every CrimsonText line is graph text
    fig_lines = [l for l in stim_lines if l.font.startswith("Crimson") and l.page == pages[0]]
    skip, figure = [], None
    if fig_lines:
        rect = pymupdf.Rect(min(l.x0 for l in fig_lines), min(l.y0 for l in fig_lines),
                            max(l.x1 for l in fig_lines), max(l.y1 for l in fig_lines))
        text_rect = pymupdf.Rect(rect)
        for d in first.get_drawings():
            r = d["rect"]
            # chart ink only: inside the text's vertical band and near its horizontal extent
            # (the page carries a scrollbar-like element at the far right)
            if (text_rect.y0 - 8 <= r.y0 and r.y1 <= text_rect.y1 + 8
                    and r.x0 >= text_rect.x0 - 20 and r.x1 <= text_rect.x1 + 120):
                rect |= r
        skip.append(rect)
        flat = [l for l in fig_lines if not l.rotated]
        texts = [clean(l.text) for l in flat]
        n_title = next((i for i, t in enumerate(texts) if re.fullmatch(r"[\d.,%−\-–$]+", t)), len(texts))
        figure = {"image": render_figure(first, rect, qid),
                  "title": clean(" ".join(texts[:n_title])) or None,
                  "axis_labels": [clean(l.text) for l in fig_lines if l.rotated],
                  "labels": texts[n_title:]}

    # ---- table: a ruled grid inside the stimulus band
    table = None
    stim_band = pymupdf.Rect(0, band.y0, first.rect.width,
                             body[ci].y0 - 2 if body[ci].page == pages[0] else band.y1)
    rules = [d["rect"] for d in first.get_drawings()
             if d["rect"].height < 2.5 and d["rect"].width > 8 and stim_band.contains(d["rect"])]
    if len({round(r.y0) for r in rules}) >= 3 and not fig_lines:
        tabs = [t for t in first.find_tables(clip=stim_band, strategy="lines_strict").tables
                if t.row_count >= 2 and t.col_count >= 2]
        if tabs:
            t = max(tabs, key=lambda t: t.row_count * t.col_count)
            trect = pymupdf.Rect(t.bbox)
            skip.append(trect)
            page_words = first.get_text("words")

            def cell_text(c):
                if c is None:
                    return ""
                box = pymupdf.Rect(c)
                return clean(assemble([w for w in page_words if box.contains(
                    pymupdf.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2))]))
            rows = [[cell_text(c) for c in row.cells] for row in t.rows]
            rows = [r for r in rows if any(r)]
            title = [l for l in stim_lines if l.y1 <= trect.y0 + 2 and l.x0 > 30
                     and abs((l.x0 + l.x1) / 2 - first.rect.width / 2) < 40]
            skip.extend(pymupdf.Rect(l.x0, l.y0, l.x1, l.y1) for l in title)
            table = {"title": clean(" ".join(l.text for l in title)) or None,
                     "header": rows[0], "rows": rows[1:]}

    def in_skip(l):
        if l.page != pages[0]:
            return False
        c = pymupdf.Point((l.x0 + l.x1) / 2, (l.y0 + l.y1) / 2)
        return any(s.contains(c) for s in skip)

    prose = [l for l in stim_lines if not in_skip(l) and not l.font.startswith("Crimson")]

    # ---- stem = last paragraph before choice A (always its own paragraph in the layout)
    cut = len(prose)
    for i in range(len(prose) - 1, 0, -1):
        a, b = prose[i - 1], prose[i]
        if (a.page == b.page and b.y0 - a.y0 > 1.55 * (a.y1 - a.y0) + 3) or (a.page != b.page and a.x1 < 480):
            cut = i
            break
    else:
        cut = 0
    stem = clean(" ".join(l.text for l in prose[cut:]))
    prose = prose[:cut]

    # ---- notes: a line with a bullet dot to its left starts a note
    dots = [d["rect"] for d in first.get_drawings()
            if d["type"] == "f" and d["rect"].width < 6 and d["rect"].height < 6
            and band.y0 < d["rect"].y0 < band.y1]
    notes, intro = [], []
    if dots:
        for l in prose:
            mid = (l.y0 + l.y1) / 2
            if any(abs((d.y0 + d.y1) / 2 - mid) < 6 and d.x1 <= l.x0 for d in dots):
                notes.append(l.text)
            elif notes and l.x0 > 40:
                notes[-1] += " " + l.text
            else:
                intro.append(l)
        notes = [clean(n) for n in notes]
        prose = intro

    # ---- paired texts
    texts = []
    labels = [i for i, l in enumerate(prose) if re.fullmatch(r"Text [12]", l.text.strip())]
    if len(labels) == 2:
        a, b = labels
        texts = [{"label": "Text 1", "paragraphs": paragraphs(prose[a + 1:b])},
                 {"label": "Text 2", "paragraphs": paragraphs(prose[b + 1:])}]
        prose = prose[:a]

    paras = paragraphs(prose)
    kind = ("notes" if notes else "paired" if texts else "figure" if figure
            else "table" if table else "prose")

    # ---- answer, rationale, difficulty
    tail_text = "\n".join(l.text for l in tail)
    ans = re.search(r"Correct Answer:\s*([A-D])", tail_text)
    diff = re.search(r"Question Difficulty:\s*(\w+)", tail_text)
    rat = []
    seen_rationale = False
    for l in tail:
        t = l.text.strip()
        if t.startswith("Question Difficulty:"):
            break
        if seen_rationale and not (l.page == pages[0] and l.y0 < 140 and False):
            rat.append(l)
        if t == "Rationale":
            seen_rationale = True
    # continuation pages carry no header; first-page header lines sit above the ID mark
    rat = [l for l in rat if not (l.page != pages[0] and l.y0 < 40 and re.fullmatch(r"\d+", l.text.strip()))]

    family = FAMILY_BY_DOMAIN.get(domain, "")
    skill_key = SKILL_FAMILY.get(skill, "")
    if skill_key == "command_of_evidence":
        skill_key += "_quantitative" if QUANT_STEM.search(stem) else "_textual"

    stimulus = {
        "kind": kind,
        "paragraphs": paras,
        **({"notes": notes} if notes else {}),
        **({"texts": texts} if texts else {}),
        **({"table": table} if table else {}),
        **({"figure": figure} if figure else {}),
    }
    return {
        # the five core fields first
        "domain": domain,
        "skill": skill,
        "passage": readable_passage(stimulus),
        "question": stem,
        "choices": choices,
        # everything else
        "question_id": qid,
        "difficulty": diff.group(1) if diff else "",
        "correct_answer": ans.group(1) if ans else "",
        "domain_key": family, "skill_key": skill_key,
        "underlined": underlined_text(first, band, skip),
        "stimulus": stimulus,
        "rationale": paragraphs(rat),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="questions per PDF (for a quick trial)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    best: dict[str, dict] = {}
    appears = collections.defaultdict(list)
    for rel in discover():
        doc = pymupdf.open(HERE / rel)
        starts = [i for i in range(len(doc)) if "Question ID" in doc[i].get_text()]
        if args.limit:
            starts = starts[:args.limit]
        bad = 0
        for n, p0 in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else (len(doc) if not args.limit else p0 + 1)
            q = parse_question(doc, list(range(p0, end)))
            if q is None:
                bad += 1
                continue
            appears[q["question_id"]].append(rel)
            have = best.get(q["question_id"])
            # keep the richest copy: one with an answer and a rationale
            if have is None or (not have["rationale"] and q["rationale"]):
                q["source_pdf"] = rel
                best[q["question_id"]] = q
        doc.close()
        print(f"{len(starts):5d} questions  {bad:3d} unparsed  {rel}")

    rows = sorted(best.values(), key=lambda q: q["question_id"])
    for q in rows:
        q["appears_in"] = appears[q["question_id"]]
    if not args.limit:
        live = {q["stimulus"]["figure"]["image"].split("/")[1] for q in rows if "figure" in q["stimulus"]}
        for f in FIG_DIR.glob("*.png"):
            if f.name not in live:
                f.unlink()
    OUT.write_text(json.dumps({
        "about": "Structured master base of every College Board MyPractice verbal PDF in this folder.",
        "built_at": date.today().isoformat(), "builder": "CB_QUESTION_BANK/build_master.py",
        "source_pdfs": discover(), "question_count": len(rows),
        "questions": rows}, indent=1, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(rows)} questions -> {OUT.name}")
    print("stimulus kinds:", dict(collections.Counter(q["stimulus"]["kind"] for q in rows)))


if __name__ == "__main__":
    main()
