#!/usr/bin/env python3
"""
Normalize question_assets source metadata to a consistent canonical label.

Target format: YEAR_TEST_N_SEC_S_MOD_M
  e.g.  2025_TEST_1_SEC1_MOD1
        2025_TEST_4_SEC1_MOD2A
        2024_TEST_2_SEC1_MOD2B

Normalizes:
  source_test_name  →  "Test N"  (e.g. "Test 1", "Test 4")
  source_exam_code  →  "SAT"     (always)
  source_section_code → zero-padded "01"
  source_module_code  → canonical "01" / "02" / "02A" / "02B"

Run in dry-run mode (default):
  uv run python scripts/normalize_source_labels.py

Apply changes:
  uv run python scripts/normalize_source_labels.py --apply
"""

import argparse
import re
import sys
import asyncio

import asyncpg


DB_DSN = "postgresql://dsat:dsat_dev@localhost:5434/dsat_dev"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_test_number(asset: dict) -> int | None:
    """Return the test number as an integer, trying multiple fields."""
    candidates = [
        asset.get("source_test_name") or "",
        asset.get("source_name") or "",
        asset.get("source_exam_code") or "",
    ]
    for text in candidates:
        # Match patterns: "Test 4", "Test04", "Test_4", "test04", "PT1", etc.
        m = re.search(r"(?:test|pt)[_\s\-]?0*(\d+)", text, re.IGNORECASE)
        if m:
            return int(m.group(1))
        # Bare number like exam_code "3", "10", "01"
        m = re.fullmatch(r"0*(\d+)", text.strip())
        if m:
            n = int(m.group(1))
            if 1 <= n <= 20:   # sanity: test numbers are 1-20
                return n
    return None


def _normalize_module(code: str | None) -> str | None:
    if not code:
        return None
    c = code.strip().upper()
    aliases = {
        "M1": "01", "MOD1": "01", "MODULE1": "01", "1": "01", "01": "01",
        "M2": "02", "MOD2": "02", "MODULE2": "02", "2": "02", "02": "02",
        "M2A": "02A", "MOD2A": "02A", "2A": "02A", "02A": "02A",
        "M2B": "02B", "MOD2B": "02B", "2B": "02B", "02B": "02B",
    }
    return aliases.get(c, c)


def _normalize_section(code: str | None) -> str | None:
    if not code:
        return None
    c = code.strip()
    return c.zfill(2) if c.isdigit() else c


def _format_module(code: str | None) -> str:
    """Format module code for display: 01→1, 02→2, 02A→2A, 02B→2B."""
    if not code:
        return "?"
    c = code.strip().upper()
    mapping = {"01": "1", "02": "2", "02A": "2A", "02B": "2B"}
    return mapping.get(c, c)


def _canonical_label(year: int | None, test_num: int | None,
                     section: str | None, module: str | None) -> str:
    year_s = str(year) if year else "UNKN"
    test_s = f"TEST_{test_num}" if test_num else "TEST_?"
    sec_num = int(section) if section and section.isdigit() else section or "?"
    sec_s = f"SEC{sec_num}"
    mod_s = f"MOD{_format_module(module)}"
    return f"{year_s}_{test_s}_{sec_s}_{mod_s}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(apply: bool) -> None:
    conn = await asyncpg.connect(DB_DSN)

    rows = await conn.fetch("""
        SELECT id, source_test_name, source_exam_code, source_subject_code,
               source_section_code, source_module_code, source_release_year,
               source_name, content_origin
        FROM question_assets
        WHERE content_origin = 'official'
        ORDER BY source_release_year NULLS LAST, source_test_name, source_module_code
    """)

    changes = []
    warnings = []

    for row in rows:
        asset = dict(row)
        test_num = _extract_test_number(asset)
        norm_module = _normalize_module(asset["source_module_code"])
        norm_section = _normalize_section(asset["source_section_code"])
        year = asset["source_release_year"]

        new_test_name = f"Test {test_num}" if test_num else None
        new_exam_code = "SAT"
        new_label = _canonical_label(year, test_num, norm_section, norm_module)

        # Collect what would change
        updates = {}
        if asset["source_test_name"] != new_test_name and new_test_name:
            updates["source_test_name"] = new_test_name
        if asset["source_exam_code"] != new_exam_code:
            updates["source_exam_code"] = new_exam_code
        if asset["source_module_code"] != norm_module and norm_module:
            updates["source_module_code"] = norm_module
        if asset["source_section_code"] != norm_section and norm_section:
            updates["source_section_code"] = norm_section

        if not test_num:
            warnings.append(f"  ⚠ Could not extract test number: {asset['source_name']}")

        changes.append({
            "id": asset["id"],
            "source_name": asset["source_name"],
            "canonical_label": new_label,
            "updates": updates,
        })

    # Print preview
    print(f"\n{'='*72}")
    print(f"{'CANONICAL LABEL NORMALIZATION PREVIEW':^72}")
    print(f"{'='*72}")
    print(f"{'Source File':<40} {'Canonical Label':<30} {'Changes'}")
    print(f"{'-'*72}")

    total_changes = 0
    for c in changes:
        change_summary = ", ".join(
            f"{k}: {v!r}" for k, v in c["updates"].items()
        ) if c["updates"] else "—"
        fname = c["source_name"][:38] if c["source_name"] else "(unknown)"
        print(f"{fname:<40} {c['canonical_label']:<30} {change_summary}")
        total_changes += len(c["updates"])

    if warnings:
        print(f"\n{'WARNINGS':}")
        for w in warnings:
            print(w)

    print(f"\n{len(rows)} assets | {total_changes} field updates needed")

    if not apply:
        print("\nDry run — pass --apply to commit changes.\n")
        await conn.close()
        return

    # Apply
    print("\nApplying changes...")
    updated = 0
    async with conn.transaction():
        for c in changes:
            if not c["updates"]:
                continue
            set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(c["updates"]))
            values = list(c["updates"].values())
            await conn.execute(
                f"UPDATE question_assets SET {set_clauses} WHERE id = $1",
                c["id"], *values
            )
            updated += 1

    print(f"Done — {updated} assets updated.\n")
    await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize question_assets source labels.")
    parser.add_argument("--apply", action="store_true", help="Commit changes to DB (default: dry run)")
    args = parser.parse_args()
    asyncio.run(run(apply=args.apply))
