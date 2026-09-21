"""Read-only validation of the frozen terminology baseline and current-file drift."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Always the latest release. Earlier release directories are frozen and never edited.
RELEASE = Path(__file__).resolve().parent / "vocabulary" / "v1.1.0"


def verify(root=ROOT, release=RELEASE):
    errors = []
    lock = json.loads((release / "baseline.lock.json").read_text())
    for group, directory in [("release_files", release), ("repository_files", root)]:
        for name, expected in lock[group].items():
            path = directory / name
            if not path.is_file():
                errors.append(f"Missing {group}: {name}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(f"Drift in {group}: {name}; record a new release")

    official = json.loads((release / "college_board.json").read_text())
    terms = official["terms"]
    by_id = {term["id"]: term for term in terms}
    if len(by_id) != len(terms):
        errors.append("Duplicate official reference ID")
    if sum(t["kind"] == "domain" for t in terms) != 4:
        errors.append("Expected four official domains")
    if sum(t["kind"] == "skill" for t in terms) != 10:
        errors.append("Expected ten official skills")
    for term in terms:
        parent = by_id.get(term["parent"])
        expected_kind = {"skill": "domain", "testing_point": "skill"}.get(term["kind"])
        if expected_kind and (parent is None or parent["kind"] != expected_kind):
            errors.append(f"Invalid parent for {term['id']}")
        if term["kind"] == "domain" and term["parent"] is not None:
            errors.append(f"Domain has a parent: {term['id']}")

    master = json.loads((release / "master.snapshot.json").read_text())
    identities = {(v["name"], e["value"], e.get("parent"))
                  for v in master["vocabularies"] for e in v["entries"]}
    required_categories = {"QUESTION_FAMILY_KEYS", "READING_SKILL_FAMILY_KEYS",
                           "GRAMMAR_FOCUS_BY_ROLE", "SKILL_FAMILY_BY_QUESTION_FAMILY"}
    required = {identity for identity in identities if identity[0] in required_categories}
    required.add(("STEM_TYPE_KEYS", "choose_best_notes_synthesis", None))
    mappings = json.loads((release / "crosswalk.json").read_text())["mappings"]
    seen = set()
    for mapping in mappings:
        old = mapping["legacy"]
        identity = (old["category"], old["value"], old["parent"])
        if identity not in identities or identity in seen:
            errors.append(f"Unknown or duplicate legacy identity: {identity}")
        seen.add(identity)
        if mapping["relationship"] not in {"equivalent", "narrower", "broader", "related", "unresolved"}:
            errors.append(f"Invalid relationship for {identity}")
        if any(target not in by_id for target in mapping["official_targets"]):
            errors.append(f"Unknown official target for {identity}")
        if mapping["automatic_database_rewrite"] is not False:
            errors.append(f"Baseline must not authorize automatic rewrites: {identity}")
    if seen != required:
        errors.append(f"Crosswalk coverage mismatch: missing {required - seen}, extra {seen - required}")
    original_root = root / "rules_refactor/rules"
    snapshot_root = root / "chatgpt_refactor_rules/rules"
    original_names = {p.relative_to(original_root) for p in original_root.rglob("*") if p.is_file()}
    snapshot_names = {p.relative_to(snapshot_root) for p in snapshot_root.rglob("*") if p.is_file()}
    if original_names != snapshot_names:
        errors.append("Rule snapshot file inventory mismatch")
    for path in original_root.rglob("*"):
        if path.is_file():
            snapshot = root / "chatgpt_refactor_rules/rules" / path.relative_to(root / "rules_refactor/rules")
            if not snapshot.is_file() or snapshot.read_bytes() != path.read_bytes():
                errors.append(f"Rule snapshot mismatch: {path.relative_to(root)}")
            if str(path.relative_to(root)) not in lock["repository_files"]:
                errors.append(f"Unrecorded rule artifact: {path.relative_to(root)}")
    return errors


if __name__ == "__main__":
    try:
        problems = verify()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems = [f"Invalid baseline: {exc}"]
    print("\n".join(problems) if problems else
          f"{RELEASE.name} OK: official hierarchy, complete legacy crosswalk, hashes, and rule snapshots match")
    raise SystemExit(bool(problems))
