"""Real prompt assembly checks; no provider calls or database needed."""
import json
import runpy

import pytest

from app.prompts import rule_modules
from app.prompts.generate_prompt import build_generate_prompt, build_generate_prompt_parts


def test_splitter_reproduces_modules_without_coverage_gaps(tmp_path):
    splitter = runpy.run_path(str(rule_modules.RULES_DIR.parent / "split_rules.py"))
    output = tmp_path / "rules"
    splitter["main"].__globals__["OUT"] = output
    splitter["main"]()
    expected = {p.relative_to(rule_modules.RULES_DIR): p.read_bytes()
                for p in rule_modules.RULES_DIR.rglob("*") if p.is_file()}
    actual = {p.relative_to(output): p.read_bytes()
              for p in output.rglob("*") if p.is_file()}
    assert actual == expected
    report = json.loads((output / "split_report.json").read_text())
    assert all(not entry["unassigned_nonblank_ranges"] for entry in report.values())
    assert "## E.1" not in (output / "grammar/future_anatomy.md").read_text()


def test_legacy_routes(monkeypatch):
    monkeypatch.delenv("DSAT_GENERATION_RULES_MODE", raising=False)
    for request, present, absent in [
        ({"target_grammar_focus_key": "semicolon_use"}, "Grammar v8", "Reading v3"),
        ({"target_reading_focus_key": "contextual_meaning"}, "Reading v3", "Grammar v8"),
    ]:
        static, _, _ = build_generate_prompt_parts(request)
        assert present + " RULES REFERENCE" in static
        assert absent + " RULES REFERENCE" not in static
        assert len(static) > 1000
    static, _, _ = build_generate_prompt_parts({})
    assert "Grammar v8 RULES REFERENCE" in static
    assert "Reading v3 RULES REFERENCE" in static


def test_every_manifest_generation_route(monkeypatch):
    monkeypatch.setenv("DSAT_GENERATION_RULES_MODE", "modules")
    manifest = json.loads((rule_modules.RULES_DIR / "manifest.json").read_text())
    for domain, target_key in [("grammar", "target_grammar_focus_key"),
                               ("reading", "target_skill_family_key")]:
        for key, entry in manifest[domain]["skills"].items():
            if key in manifest[domain].get("do_not_generate", []):
                continue
            static, _, _ = build_generate_prompt_parts({target_key: key})
            positions = [static.index(f"MODULE {name}:") for name in entry["generate"]]
            assert positions == sorted(positions)
            assert "future_anatomy.md:" not in static
            assert "ALLOWED KEY VALUES" in static
            assert static.count("MODULE shared/01_generation_quality.md:") == 1
            assert static.count("## E.1 Correctness and Difficulty") == 1
            assert "Three plausible distractors for high difficulty" in static
            assert "not a requirement that every" in static
            assert "Do not invent history, similarity scores" in static
            if domain == "reading":
                assert "MODULE reading/style_fingerprint.md:" in static
                assert "MODULE reading/annotation_core.md:" in static
                assert "canonical active `student_failure_mode_key`" in static
            assert static == build_generate_prompt_parts({target_key: key})[0]


def test_focus_routing_and_both_builders(monkeypatch):
    monkeypatch.setenv("DSAT_GENERATION_RULES_MODE", "modules")
    request = {"target_reading_focus_key": "contextual_meaning"}
    static, _, user = build_generate_prompt_parts(request)
    system, legacy_user = build_generate_prompt(request)
    assert static in system and user == legacy_user
    assert "MODULE reading/skills/words_in_context.md:" in static
    assert "MODULE grammar/" not in static
    assert static == build_generate_prompt_parts({
        "target_reading_skill_family_key": "words_in_context",
    })[0]


def test_notes_override_and_transition_dependencies():
    context = rule_modules.load_generation_modules({
        "target_grammar_focus_key": "transition_logic",
        "stem_type_key": "choose_best_notes_synthesis",
    })
    assert "MODULE grammar/conditional/transitions.md:" in context
    assert "MODULE grammar/conditional/notes_synthesis.md:" in context
    assert context.count("MODULE shared/00_mode_and_schemas.md:") == 1
    assert context.count("MODULE shared/01_generation_quality.md:") == 1


@pytest.mark.parametrize("target", [
    {}, {"target_grammar_focus_key": "unknown"},
    {"target_grammar_focus_key": "affirmative_agreement"},
    {"target_grammar_focus_key": "negation"},
    {"target_skill_family_key": "words_in_context", "target_reading_focus_key": "causal_inference"},
    {"target_grammar_focus_key": "semicolon_use", "reading_focus_key": "contextual_meaning"},
    {"target_grammar_focus_key": "semicolon_use", "grammar_focus_key": "verb_form"},
])
def test_invalid_targets_fail(target):
    with pytest.raises(ValueError):
        rule_modules.load_generation_modules(target)


@pytest.mark.parametrize("name,content,error", [
    ("missing.md", None, FileNotFoundError),
    ("empty.md", " ", ValueError),
    ("../escape.md", "outside", ValueError),
])
def test_required_modules_fail_closed(tmp_path, monkeypatch, name, content, error):
    root = tmp_path / "rules"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps({
        "version": "test", "grammar": {"stem_type_overrides": {}, "do_not_generate": [],
        "skills": {"semicolon_use": {"generate": [name]}}},
    }))
    if content is not None:
        (root / name).write_text(content)
    monkeypatch.setattr(rule_modules, "RULES_DIR", root)
    with pytest.raises(error):
        rule_modules.load_generation_modules({"grammar_focus_key": "semicolon_use"})
