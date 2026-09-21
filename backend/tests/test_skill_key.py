"""questions.skill_key resolution — app.pipeline.skill_key."""
from types import SimpleNamespace

from app.models.ontology import SKILL_FAMILY_KEYS
from app.pipeline.skill_key import apply_skill_key, load_rules, resolve_skill_key

RULES = (
    {"choose_best_transition": "transitions"},                 # by stem_type_key
    {"punctuation/colon_dash_use": "boundaries"},              # by role/focus
    {"agreement": "form_structure_and_sense"},                 # by role
)


def resolve(**kw):
    base = dict(cb_skill_key=None, stem_text="", stem_type_key=None, annotation={}, rules=RULES)
    return resolve_skill_key(**{**base, **kw})


def test_cb_label_wins_over_everything():
    got = resolve(cb_skill_key="boundaries", stem_type_key="choose_best_transition",
                  annotation={"skill_family_key": "inferences"})
    assert got == ("boundaries", "cb")


def test_command_of_evidence_split_by_stem():
    quant = "Which choice most effectively uses data from the table to complete the text?"
    text = "Which finding, if true, would most directly support the team's conclusion?"
    assert resolve(cb_skill_key="command_of_evidence", stem_text=quant) == (
        "command_of_evidence_quantitative", "cb")
    assert resolve(cb_skill_key="command_of_evidence", stem_text=text) == (
        "command_of_evidence_textual", "cb")


def test_unknown_cb_label_is_not_trusted():
    assert resolve(cb_skill_key="not_a_cb_skill") == (None, None)


def test_existing_reading_skill_is_reused():
    assert resolve(annotation={"skill_family_key": "inferences"}) == ("inferences", "annotation")


def test_grammar_value_in_skill_family_key_is_ignored():
    # skill_family_key is reading-only; a grammar value there must not be echoed back.
    assert resolve(annotation={"skill_family_key": "boundaries"}) == (None, None)


def test_map_order_stem_then_focus_then_role():
    ann = {"grammar_role_key": "agreement", "grammar_focus_key": "subject_verb_agreement"}
    assert resolve(stem_type_key="choose_best_transition", annotation=ann) == ("transitions", "map")
    assert resolve(annotation={"grammar_role_key": "punctuation",
                               "grammar_focus_key": "colon_dash_use"}) == ("boundaries", "map")
    assert resolve(annotation=ann) == ("form_structure_and_sense", "map")


def test_annotation_stem_type_beats_the_column():
    # Generated questions never set questions.stem_type_key; the annotation is canonical.
    got = resolve(stem_type_key="complete_the_text",
                  annotation={"stem_type_key": "choose_best_transition"})
    assert got == ("transitions", "map")


def test_unresolved_returns_none_rather_than_guessing():
    ann = {"grammar_role_key": "expression_of_ideas", "grammar_focus_key": "precision_word_choice"}
    assert resolve(stem_type_key="complete_the_text", annotation=ann) == (None, None)


def _question(**kw):
    base = dict(cb_skill_key=None, current_question_text="", stem_type_key=None,
                skill_key=None, skill_key_source=None)
    return SimpleNamespace(**{**base, **kw})


def test_apply_sets_both_columns():
    q = _question()
    apply_skill_key(q, {"skill_family_key": "words_in_context"})
    assert (q.skill_key, q.skill_key_source) == ("words_in_context", "annotation")


def test_apply_never_touches_a_manual_label():
    q = _question(skill_key="boundaries", skill_key_source="manual")
    apply_skill_key(q, {"skill_family_key": "inferences"})
    assert (q.skill_key, q.skill_key_source) == ("boundaries", "manual")


def test_apply_does_not_erase_a_label_when_nothing_resolves():
    q = _question(skill_key="transitions", skill_key_source="map")
    apply_skill_key(q, {})
    assert (q.skill_key, q.skill_key_source) == ("transitions", "map")


def test_shipped_map_only_yields_legal_skills():
    by_stem, by_focus, by_role = load_rules()
    assert by_stem, "cb_skill_map.json missing or has no deterministic stem rules"
    for table in (by_stem, by_focus, by_role):
        assert set(table.values()) <= set(SKILL_FAMILY_KEYS)
    assert by_stem["choose_best_transition"] == "transitions"
