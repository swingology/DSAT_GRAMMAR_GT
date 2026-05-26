#!/usr/bin/env python3
"""Controlled-vocabulary generation and review-queue tooling.

`vocabulary/master.json` is the compiled enforcement manifest for every active
controlled vocabulary the ingestion/generation pipeline uses. New active keys
must originate as approved rule-document amendments; this file is the generated
enforcement surface after that approval, not the casual authoring surface for
new taxonomy rules.

This script keeps the two derived artefacts in sync with master.json:

  * ``backend/app/models/ontology.py``  — the Python constants the validators
    import.
  * the ``<!-- VOCAB:... -->`` appendix blocks in the rules docs.

Modes
-----
``--bootstrap``  One-time: import the *current* ontology.py and dump it to
                 master.json. Run once to seed the manifest, then never again.
``--generate``   Regenerate ontology.py and the rules-doc appendix blocks from
                 current master.json after an approved manifest change.
``--check``      Exit non-zero if ontology.py / the docs are out of sync with
                 master.json. Wired into CI.
``--list-candidates``
                 Inspect unknown keys captured during validation. Candidate
                 rows are review input only; they are not active vocabulary.
``--promote-from-amendment``
                 Promote one already-approved amendment through the same gated
                 library used by the admin API.
``--promote``    Legacy direct promotion path. Blocked by default because it
                 bypasses the amendment approval invariant. Development use
                 requires --unsafe-direct-promote and must not be used for the
                 normal rules-update workflow.

Only ``status == "active"`` entries are emitted into ontology.py and the docs;
``candidate`` and ``deprecated`` entries live in master.json for the review
queue but are not yet (or no longer) part of the enforced vocabulary.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import sys
from pathlib import Path

# --- Repo layout -----------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
ONTOLOGY_PATH = BACKEND_ROOT / "app" / "models" / "ontology.py"
MASTER_PATH = REPO_ROOT / "vocabulary" / "master.json"
RULES_DOCS = {
    "reading": REPO_ROOT / "rules_agent_dsat_reading_v2.md",
    "grammar": REPO_ROOT / "rules_agent_dsat_grammar_ingestion_generation_v8.md",
}

SCHEMA_VERSION = 1
TODAY = _dt.date.today().isoformat()

# --- Vocabulary registry ---------------------------------------------------
# Drives bootstrap order and metadata. `kind`: "flat" or "hierarchical".
# For hierarchical sets, `parent_set` names the role/family tuple and
# `derived_flat` names the flat tuple comprehension emitted alongside the dict.
REGISTRY: list[dict] = [
    {"name": "CONTENT_ORIGINS", "kind": "flat", "domain": "system",
     "comment": "Content origin"},
    {"name": "JOB_TYPES", "kind": "flat", "domain": "system",
     "comment": "Job types"},
    {"name": "JOB_STATUSES", "kind": "flat", "domain": "system",
     "comment": "Job statuses (state machine)"},
    {"name": "PRACTICE_STATUSES", "kind": "flat", "domain": "system",
     "comment": "Practice status"},
    {"name": "OVERLAP_STATUSES", "kind": "flat", "domain": "system",
     "comment": "Overlap status"},
    {"name": "RELATION_TYPES", "kind": "flat", "domain": "system",
     "comment": "Relation types"},
    {"name": "ASSET_TYPES", "kind": "flat", "domain": "system",
     "comment": "Asset types"},
    {"name": "CHANGE_SOURCES", "kind": "flat", "domain": "system",
     "comment": "Change sources"},
    {"name": "STIMULUS_MODE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.1 stimulus_mode_key"},
    {"name": "TEST_FORMAT_KEYS", "kind": "flat", "domain": "system",
     "comment": "Rules v8 generation format keys"},
    {"name": "SOURCE_STATS_FORMAT_KEYS", "kind": "flat", "domain": "system",
     "comment": "Rules v8 source stats format keys"},
    {"name": "STEM_TYPE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.2 stem_type_key"},
    {"name": "GRAMMAR_ROLE_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "V3 §5 grammar_role_key"},
    {"name": "GRAMMAR_FOCUS_BY_ROLE", "kind": "hierarchical", "domain": "grammar",
     "comment": "V3 §6 grammar_focus_key (grouped by role)",
     "parent_set": "GRAMMAR_ROLE_KEYS", "derived_flat": "GRAMMAR_FOCUS_KEYS"},
    {"name": "SYNTACTIC_TRAP_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "V3 §9 syntactic_trap_key"},
    {"name": "DISTRACTOR_TYPE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §12.1 distractor_type_key (option-level)"},
    {"name": "REASONING_TRAP_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 §10 reasoning_trap_key (question-level)"},
    {"name": "PLAUSIBILITY_SOURCE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §10.3 plausibility_source_key"},
    {"name": "ANSWER_MECHANISM_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.3 answer_mechanism_key"},
    {"name": "SOLVER_PATTERN_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.3 solver_pattern_key"},
    {"name": "STUDENT_FAILURE_MODE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §21.3 student_failure_mode_key"},
    {"name": "DISTRACTOR_DISTANCE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §21.2 distractor_distance"},
    {"name": "DIFFICULTY_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.3 difficulty keys"},
    {"name": "FREQUENCY_BANDS", "kind": "flat", "domain": "shared",
     "comment": "V3 §3.3 frequency bands"},
    {"name": "TENSE_REGISTER_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §17.6 tense register keys"},
    {"name": "PASSAGE_ARCHITECTURE_KEYS", "kind": "flat", "domain": "shared",
     "comment": "V3 §22 passage_architecture_key"},
    {"name": "QUESTION_FAMILY_KEYS", "kind": "flat", "domain": "shared",
     "comment": "question_family_key"},
    {"name": "READING_QUESTION_FAMILY_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading question families (subset of QUESTION_FAMILY_KEYS)"},
    {"name": "READING_SKILL_FAMILY_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading skill families"},
    {"name": "READING_FOCUS_BY_SKILL_FAMILY", "kind": "hierarchical",
     "domain": "reading",
     "comment": "Reading v2 reading_focus_key (grouped by skill family)",
     "parent_set": "READING_SKILL_FAMILY_KEYS", "derived_flat": "READING_FOCUS_KEYS"},
    {"name": "TEST_CONSTRUCT_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 target_test_construct_key"},
    {"name": "CRAFT_SUBCONSTRUCT_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 target_craft_subconstruct_key"},
    {"name": "TEXT_RELATIONSHIP_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 cross-text relationship keys"},
    {"name": "QUANTITATIVE_SUB_PATTERN_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 quantitative_sub_pattern"},
    {"name": "SENTENCE_FUNCTION_ROLE_KEYS", "kind": "flat", "domain": "reading",
     "comment": "Reading v2 target_sentence_function_role"},
    {"name": "TRANSITION_SUBTYPE_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "Grammar v8 transition_subtype_key"},
    {"name": "SYNTHESIS_GOAL_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "Grammar v8 notes synthesis goal keys"},
    {"name": "AUDIENCE_KNOWLEDGE_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "Grammar v8 audience knowledge keys"},
    {"name": "REQUIRED_CONTENT_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "Grammar v8 required content keys"},
    {"name": "SYNTHESIS_DISTRACTOR_FAILURE_KEYS", "kind": "flat", "domain": "grammar",
     "comment": "Grammar v8 synthesis distractor failure keys"},
    {"name": "TOPIC_BROAD_KEYS", "kind": "flat", "domain": "shared",
     "comment": "Broad topic keys"},
]
REGISTRY_BY_NAME = {r["name"]: r for r in REGISTRY}


# --- ontology import -------------------------------------------------------
def _load_ontology():
    """Load ontology.py directly by file path.

    Imported by path rather than as ``app.models.ontology`` so bootstrap does
    not drag in the SQLAlchemy models that ``app.models.__init__`` pulls in.
    ontology.py is a pure-constants module with no imports of its own.
    """
    spec = importlib.util.spec_from_file_location("_ontology", ONTOLOGY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- bootstrap: ontology.py -> master.json ---------------------------------
def bootstrap() -> dict:
    onto = _load_ontology()
    vocabularies = []
    for reg in REGISTRY:
        name = reg["name"]
        value = getattr(onto, name)
        entry = {
            "name": name,
            "kind": reg["kind"],
            "domain": reg["domain"],
            "comment": reg["comment"],
        }
        if reg["kind"] == "flat":
            entry["entries"] = [
                {"value": v, "status": "active", "added": TODAY, "description": ""}
                for v in value
            ]
        else:  # hierarchical
            entry["parent_set"] = reg["parent_set"]
            entry["derived_flat"] = reg["derived_flat"]
            rows = []
            for parent, children in value.items():
                for child in children:
                    rows.append({
                        "value": child, "parent": parent, "status": "active",
                        "added": TODAY, "description": "",
                    })
            entry["entries"] = rows
        vocabularies.append(entry)
    return {
        "schema_version": SCHEMA_VERSION,
        "note": ("Compiled controlled-vocabulary enforcement manifest. New active "
                 "keys must come from approved rule-document amendments; then run "
                 "scripts/gen_vocab.py --generate. ontology.py and the rules-doc "
                 "VOCAB blocks are generated artefacts — do not hand-edit them."),
        "vocabularies": vocabularies,
    }


# --- master.json -> ontology.py text ---------------------------------------
def _active(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("status", "active") == "active"]


def _fill_values(values: list[str], indent: str, width: int = 79) -> list[str]:
    """Wrap quoted values into indented lines, deterministic line-fill."""
    lines: list[str] = []
    cur = ""
    for v in values:
        tok = f'"{v}",'
        if cur and len(indent) + len(cur) + 1 + len(tok) > width:
            lines.append(indent + cur)
            cur = ""
        cur = tok if not cur else f"{cur} {tok}"
    if cur:
        lines.append(indent + cur)
    return lines


def render_ontology(master: dict) -> str:
    out: list[str] = [
        '"""Allowed keys, enums, and constants for the current DSAT ruleset.',
        "",
        "GENERATED FILE — do not edit by hand.",
        "Source of truth: vocabulary/master.json",
        "Regenerate: python scripts/gen_vocab.py --generate",
        '"""',
        "",
    ]
    for voc in master["vocabularies"]:
        name = voc["name"]
        out.append(f"# --- {voc['comment']} ---")
        if voc["kind"] == "flat":
            vals = [e["value"] for e in _active(voc["entries"])]
            out.append(f"{name} = (")
            out.extend(_fill_values(vals, "    "))
            out.append(")")
        else:  # hierarchical
            active = _active(voc["entries"])
            # group children by parent, preserving first-seen parent order
            groups: dict[str, list[str]] = {}
            for e in active:
                groups.setdefault(e["parent"], []).append(e["value"])
            out.append(f"{name} = {{")
            for parent, children in groups.items():
                out.append(f'    "{parent}": (')
                out.extend(_fill_values(children, "        "))
                out.append("    ),")
            out.append("}")
            out.append("")
            derived = voc["derived_flat"]
            out.append(f"{derived} = tuple(")
            out.append(f"    k for keys in {name}.values() for k in keys")
            out.append(")")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --- master.json -> rules-doc appendix blocks ------------------------------
def _vocab_block(voc: dict) -> str:
    """Render one fenced VOCAB block for a rules doc."""
    name = voc["name"]
    domain = voc["domain"]
    marker = f"VOCAB:{domain}:{name}"
    lines = [f"<!-- {marker} START -->",
             f"<!-- generated from vocabulary/master.json — do not hand-edit -->",
             f"**`{name}`** — {voc['comment']}", ""]
    if voc["kind"] == "flat":
        for e in _active(voc["entries"]):
            desc = f" — {e['description']}" if e.get("description") else ""
            lines.append(f"- `{e['value']}`{desc}")
    else:
        groups: dict[str, list[dict]] = {}
        for e in _active(voc["entries"]):
            groups.setdefault(e["parent"], []).append(e)
        for parent, rows in groups.items():
            lines.append(f"- **`{parent}`**")
            for e in rows:
                desc = f" — {e['description']}" if e.get("description") else ""
                lines.append(f"  - `{e['value']}`{desc}")
    lines.append(f"<!-- {marker} END -->")
    return "\n".join(lines)


APPENDIX_HEADING = "## Appendix V — Controlled Vocabulary (generated)"
APPENDIX_PREAMBLE = (
    "The key lists below are generated from `vocabulary/master.json` by\n"
    "`scripts/gen_vocab.py`. Do not hand-edit them. Active vocabulary growth\n"
    "must start with an approved rule-doc body amendment, then update\n"
    "`vocabulary/master.json` as the compiled enforcement manifest and\n"
    "regenerate. They stay in lockstep with the validator enums in\n"
    "`backend/app/models/ontology.py`."
)


def render_doc_blocks(master: dict, domain: str) -> list[tuple[str, str]]:
    """Return ordered [(marker, block_text), ...] for one rules doc.

    'shared' and 'system' vocabularies are emitted into every rules doc;
    domain-specific ones only into their own doc. Order follows master.json.
    """
    blocks = []
    for voc in master["vocabularies"]:
        if voc["domain"] in (domain, "shared", "system"):
            marker = f"VOCAB:{voc['domain']}:{voc['name']}"
            blocks.append((marker, _vocab_block(voc)))
    return blocks


def _apply_doc_blocks(doc_text: str, blocks: list[tuple[str, str]]) -> str:
    """Sync VOCAB blocks into doc_text.

    Existing blocks are replaced in place. Blocks not yet present are appended
    under the generated appendix section (created on first run). Idempotent:
    once every block exists, re-running only replaces in place.
    """
    missing = []
    for marker, block in blocks:
        start = f"<!-- {marker} START -->"
        end = f"<!-- {marker} END -->"
        i = doc_text.find(start)
        j = doc_text.find(end)
        if i == -1 or j == -1:
            missing.append((marker, block))
            continue
        doc_text = doc_text[:i] + block + doc_text[j + len(end):]
    if missing:
        doc_text = doc_text.rstrip() + "\n"
        if APPENDIX_HEADING not in doc_text:
            doc_text += f"\n{APPENDIX_HEADING}\n\n{APPENDIX_PREAMBLE}\n"
        for _marker, block in missing:
            doc_text += "\n" + block + "\n"
    return doc_text


# --- commands --------------------------------------------------------------
def cmd_bootstrap(args) -> int:
    master = bootstrap()
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    MASTER_PATH.write_text(json.dumps(master, indent=2, ensure_ascii=False) + "\n")
    n = sum(len(v["entries"]) for v in master["vocabularies"])
    print(f"bootstrapped {MASTER_PATH} — "
          f"{len(master['vocabularies'])} vocabularies, {n} entries")
    return 0


def cmd_generate(args) -> int:
    master = json.loads(MASTER_PATH.read_text())
    ONTOLOGY_PATH.write_text(render_ontology(master))
    print(f"wrote {ONTOLOGY_PATH}")
    for domain, path in RULES_DOCS.items():
        if not path.exists():
            print(f"  skip {path.name} (not found)")
            continue
        blocks = render_doc_blocks(master, domain)
        path.write_text(_apply_doc_blocks(path.read_text(), blocks))
        print(f"  wrote {path.name} ({len(blocks)} VOCAB blocks)")
    return 0


def cmd_check(args) -> int:
    master = json.loads(MASTER_PATH.read_text())
    drift = []
    if ONTOLOGY_PATH.read_text() != render_ontology(master):
        drift.append("ontology.py out of sync with master.json")
    for domain, path in RULES_DOCS.items():
        if not path.exists():
            continue
        blocks = render_doc_blocks(master, domain)
        current = path.read_text()
        if _apply_doc_blocks(current, blocks) != current:
            drift.append(f"{path.name} out of sync with master.json")
    if drift:
        for d in drift:
            print(f"DRIFT: {d}", file=sys.stderr)
        print("run: python scripts/gen_vocab.py --generate", file=sys.stderr)
        return 1
    print("vocabulary in sync")
    return 0


# --- candidates review queue ----------------------------------------------
CANDIDATES_PATH = REPO_ROOT / "vocabulary" / "candidates.json"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_candidates() -> dict:
    if not CANDIDATES_PATH.exists():
        return {"schema_version": SCHEMA_VERSION, "candidates": []}
    return json.loads(CANDIDATES_PATH.read_text())


def _save_candidates(data: dict) -> None:
    CANDIDATES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def cmd_list_candidates(args) -> int:
    data = _load_candidates()
    rows = data.get("candidates", [])
    if not rows:
        print("vocabulary review queue is empty")
        return 0
    print(f"{len(rows)} candidate(s) awaiting review:\n")
    for c in sorted(rows, key=lambda r: (-r.get("occurrences", 0), r["vocab"])):
        print(f"  {c['vocab']}  {c['value']!r}")
        print(f"    field={c.get('field')}  occurrences={c.get('occurrences')}  "
              f"last_seen={c.get('last_seen')}")
        if c.get("job_ids"):
            print(f"    jobs: {', '.join(c['job_ids'])}")
    print("\nCandidates are review input only. Active vocabulary promotion requires "
          "an approved amendment.")
    print("approved promote: python scripts/gen_vocab.py --promote-from-amendment AMENDMENT_ID")
    print("legacy unsafe promote: python scripts/gen_vocab.py --promote VOCAB VALUE "
          "[--parent PARENT] --unsafe-direct-promote")
    print("reject:  python scripts/gen_vocab.py --reject VOCAB VALUE")
    return 0


def _drop_candidate(data: dict, vocab: str, value: str) -> bool:
    before = len(data["candidates"])
    data["candidates"] = [
        c for c in data["candidates"]
        if not (c["vocab"] == vocab and c["value"] == value)
    ]
    return len(data["candidates"]) < before


def cmd_promote(args) -> int:
    if not args.unsafe_direct_promote:
        print(
            "error: direct --promote is blocked. Active vocabulary growth must "
            "come from an approved amendment; use "
            "--promote-from-amendment AMENDMENT_ID. For isolated development only, pass "
            "--unsafe-direct-promote.",
            file=sys.stderr,
        )
        return 2
    vocab_name, value = args.promote
    master = json.loads(MASTER_PATH.read_text())
    voc = next((v for v in master["vocabularies"] if v["name"] == vocab_name), None)
    if voc is None:
        print(f"error: no vocabulary named {vocab_name!r} in master.json",
              file=sys.stderr)
        return 1
    if any(e["value"] == value and e.get("parent") == args.parent
           for e in voc["entries"]):
        print(f"error: {value!r} already in {vocab_name}", file=sys.stderr)
        return 1
    if voc["kind"] == "hierarchical" and not args.parent:
        print(f"error: {vocab_name} is hierarchical — pass --parent PARENT",
              file=sys.stderr)
        return 1
    entry = {"value": value, "status": "active", "added": TODAY,
             "description": args.description or ""}
    if voc["kind"] == "hierarchical":
        entry["parent"] = args.parent
    voc["entries"].append(entry)
    MASTER_PATH.write_text(json.dumps(master, indent=2, ensure_ascii=False) + "\n")
    cands = _load_candidates()
    if _drop_candidate(cands, vocab_name, value):
        _save_candidates(cands)
    print(f"promoted {value!r} into {vocab_name} — regenerating artefacts")
    return cmd_generate(args)


def cmd_promote_from_amendment(args) -> int:
    from app.pipeline import amendment_review

    repo_root = args.repo_root.resolve()
    result = amendment_review.promote_amendment(
        args.promote_from_amendment,
        reviewer=args.reviewer,
        notes=args.notes,
        repo_root=repo_root,
    )
    if not result.ok:
        print(result.error, file=sys.stderr)
        if result.details:
            print(json.dumps(result.details, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1
    amendment = result.amendment
    print(
        f"promoted amendment {args.promote_from_amendment}"
        + (f" ({amendment.affected_vocab} {amendment.proposed_value})" if amendment else "")
    )
    print(f"regenerated ontology.py and VOCAB appendices from {repo_root / 'vocabulary' / 'master.json'}")
    return 0


def cmd_reject(args) -> int:
    vocab_name, value = args.reject
    cands = _load_candidates()
    if _drop_candidate(cands, vocab_name, value):
        _save_candidates(cands)
        print(f"rejected {value!r} from {vocab_name} review queue")
    else:
        print(f"no candidate {value!r} in {vocab_name}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--bootstrap", action="store_true",
                   help="seed master.json from current ontology.py (one-time)")
    g.add_argument("--generate", action="store_true",
                   help="regenerate ontology.py + rules-doc blocks from master.json")
    g.add_argument("--check", action="store_true",
                   help="exit non-zero if artefacts drift from master.json")
    g.add_argument("--list-candidates", action="store_true",
                   help="show the vocabulary review queue")
    g.add_argument("--promote", nargs=2, metavar=("VOCAB", "VALUE"),
                   help="legacy direct candidate promotion; blocked unless --unsafe-direct-promote is set")
    g.add_argument("--promote-from-amendment", metavar="AMENDMENT_ID",
                   help="promote an already-approved amendment through the gated workflow")
    g.add_argument("--reject", nargs=2, metavar=("VOCAB", "VALUE"),
                   help="drop a candidate key from the review queue")
    p.add_argument("--parent", help="parent key, required for hierarchical vocabularies")
    p.add_argument("--description", help="description for a promoted key")
    p.add_argument("--repo-root", type=Path, default=REPO_ROOT,
                   help="repository root for --promote-from-amendment")
    p.add_argument("--reviewer", default="gen_vocab_cli", help="reviewer name for amendment promotion metadata")
    p.add_argument("--notes", default="", help="review notes for amendment promotion metadata")
    p.add_argument("--unsafe-direct-promote", action="store_true",
                   help="development-only bypass for legacy --promote; do not use for approved vocabulary growth")
    args = p.parse_args()
    if args.bootstrap:
        return cmd_bootstrap(args)
    if args.generate:
        return cmd_generate(args)
    if args.list_candidates:
        return cmd_list_candidates(args)
    if args.promote:
        return cmd_promote(args)
    if args.promote_from_amendment:
        return cmd_promote_from_amendment(args)
    if args.reject:
        return cmd_reject(args)
    return cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
