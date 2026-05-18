from app.prompts.extract_prompt import build_extract_prompt
from app.prompts.annotate_prompt import build_annotate_prompt
from app.prompts.generate_prompt import build_generate_prompt


def test_extract_prompt_contains_instructions():
    system, user = build_extract_prompt(raw_text="The colony of corals plays a role.")
    assert "extract" in system.lower()
    assert "colony" in user


def test_annotate_prompt_loads_current_rules():
    system, user = build_annotate_prompt(
        extract_json={"question_text": "test", "options": [], "correct_option_label": "A"},
    )
    assert "rules_agent_dsat_grammar_ingestion_generetion_v7.md" in system or "Grammar v7 RULES REFERENCE" in system
    assert "Reading v2 RULES REFERENCE" in system
    assert "## 17. Disambiguation Rules" in system
    assert "JSON" in system


def test_annotate_prompt_includes_official_amendment_guard():
    system, _user = build_annotate_prompt(
        extract_json={"question_text": "test", "options": [], "correct_option_label": "A"},
        content_origin="official",
    )
    assert "Current content_origin: official" in system
    assert "reasoning.amendment_proposal" in system


def test_annotate_prompt_blocks_non_official_amendments():
    system, _user = build_annotate_prompt(
        extract_json={"question_text": "test", "options": [], "correct_option_label": "A"},
        content_origin="generated",
    )
    assert "Current content_origin: generated" in system
    assert 'If content_origin is not "official"' in system


def test_generate_prompt_includes_target():
    request = {
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
    }
    system, user = build_generate_prompt(generation_request=request)
    assert "subject_verb_agreement" in user
    assert "Grammar v7 RULES REFERENCE" in system
    assert "## B.4 Distractor Generation Heuristics by Grammar Focus" in system


def test_generate_prompt_loads_reading_generation_rules():
    request = {
        "target_skill_family_key": "words_in_context",
        "target_reading_focus_key": "figurative_language_meaning",
        "target_test_construct_key": "figurative_interpretation_precision",
        "difficulty_overall": "medium",
    }
    system, user = build_generate_prompt(generation_request=request)
    assert "figurative_language_meaning" in user
    assert "Reading v2 RULES REFERENCE" in system
    assert "## 16. Generation Rules" in system
    assert "### 16.9 Per-focus generation and distractor recipes" in system
    assert "## 21. Validator Checklist" in system
