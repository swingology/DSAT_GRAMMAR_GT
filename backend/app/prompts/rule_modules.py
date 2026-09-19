"""Opt-in baseline module loading; this is not an ontology release compiler."""
import json
from pathlib import Path


RULES_DIR = Path(__file__).resolve().parents[3] / "rules_refactor" / "rules"


def load_generation_modules(request: dict) -> str:
    """Resolve an explicit generation target, preserving manifest dependency order.

    Unknown or conflicting targets fail before inference in this experimental path.
    Files are read afresh so a cached bundle cannot hide changes during adoption.
    """
    manifest = json.loads((RULES_DIR / "manifest.json").read_text(encoding="utf-8"))

    def value(*keys):
        values = {request[k] for k in keys if request.get(k)}
        if len(values) > 1:
            raise ValueError(f"Conflicting rule targets: {keys}")
        return next(iter(values), None)

    grammar = value("target_grammar_focus_key", "grammar_focus_key")
    focus = value("target_reading_focus_key", "reading_focus_key")
    family = value("target_skill_family_key", "target_reading_skill_family_key", "reading_skill_family_key")
    stem = value("stem_type_key", "target_stem_type_key")
    override = manifest["grammar"]["stem_type_overrides"].get(stem)
    if (grammar or override) and (focus or family):
        raise ValueError("Conflicting grammar and reading rule targets")
    entries = []
    if grammar or override:
        if grammar in manifest["grammar"]["do_not_generate"]:
            raise ValueError(f"Annotation-only rule target: {grammar}")
        if grammar:
            entry = manifest["grammar"]["skills"].get(grammar)
            if entry is None:
                raise ValueError(f"Unknown grammar rule target: {grammar}")
            entries.append(entry)
        if override:
            entries.append(override)
    else:
        candidates = [entry for key, entry in manifest["reading"]["skills"].items()
                      if (not family or key == family)
                      and (not focus or focus in entry["focus_keys"])]
        if not (family or focus) or len(candidates) != 1:
            raise ValueError("Generation needs one known, consistent reading family/focus or grammar focus")
        entries = candidates
    paths = list(dict.fromkeys(path for entry in entries for path in entry["generate"]))
    if not paths:
        raise ValueError("Empty generation module load set")
    sections = []
    root = RULES_DIR.resolve()
    for name in paths:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Rule module escapes rules directory: {name}")
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError(f"Empty required rule module: {name}")
        sections.append(f"MODULE {name}:\n{content}")
    # Reuse active validator vocabulary; baseline modules omit Appendix V.
    from app.prompts.annotate_prompt import _build_allowed_keys_block

    return "\n\n".join([f"RULE MODULES: {manifest['version']}", *sections,
                          _build_allowed_keys_block()])
