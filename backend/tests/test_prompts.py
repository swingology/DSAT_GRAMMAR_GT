from app.prompts.extract_prompt import (
    build_extract_prompt,
    EXTRACT_SYSTEM_PROMPT,
    canonicalize_stem,
    canonicalize_stimulus_mode,
)
from app.prompts.annotate_prompt import build_annotate_prompt, STEM_TYPE_DOMAIN
from app.prompts.generate_prompt import build_generate_prompt
from app.models.ontology import STEM_TYPE_KEYS


def test_stem_domain_covers_all_vocab():
    """Every canonical STEM_TYPE_KEYS value must have a domain attribution.

    Guards against routing drift: _READING_STEMS / _GRAMMAR_STEMS are derived
    from STEM_TYPE_DOMAIN, so a stem added to the controlled vocabulary without
    a domain attribution would silently route to "unknown" (pulling in grammar
    Part D). This fails fast instead.
    """
    assert set(STEM_TYPE_KEYS) == set(STEM_TYPE_DOMAIN), (
        "every STEM_TYPE_KEYS value needs a STEM_TYPE_DOMAIN attribution; "
        f"missing: {set(STEM_TYPE_KEYS) - set(STEM_TYPE_DOMAIN)}; "
        f"extra: {set(STEM_TYPE_DOMAIN) - set(STEM_TYPE_KEYS)}"
    )
    valid_domains = {"grammar", "reading", "ambiguous"}
    assert set(STEM_TYPE_DOMAIN.values()) <= valid_domains
    for domain in valid_domains:
        assert any(v == domain for v in STEM_TYPE_DOMAIN.values()), (
            f"no stems attributed to domain {domain!r}"
        )


def test_extract_prompt_contains_instructions():
    system, user = build_extract_prompt(raw_text="The colony of corals plays a role.")
    assert "extract" in system.lower()
    assert "colony" in user


def test_annotate_prompt_loads_current_rules():
    system, user = build_annotate_prompt(
        extract_json={"question_text": "test", "options": [], "correct_option_label": "A"},
    )
    assert "Grammar v8 RULES REFERENCE" in system
    assert "Reading v3 RULES REFERENCE" in system
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
    assert "Grammar v8 RULES REFERENCE" in system
    assert "Reading v3 RULES REFERENCE" in system
    assert "## B.3.0 Sub-Pattern Policy and Evidence Tiers" in system
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
    assert "Grammar v8 RULES REFERENCE" in system
    assert "Reading v3 RULES REFERENCE" in system
    assert "## 16. Generation Rules" in system
    assert "### 16.9 Per-focus generation and distractor recipes" in system
    assert "## 21. Validator Checklist" in system


def test_generate_prompt_names_official_source_examples_as_foundational():
    request = {
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
    }
    examples = [
        {
            "source_question_id": "00000000-0000-0000-0000-000000000001",
            "question_text": "Which choice completes the text?",
            "annotation": {"grammar_focus_key": "subject_verb_agreement"},
        }
    ]
    _system, user = build_generate_prompt(generation_request=request, source_examples=examples)
    assert "Stored official questions are serving as the foundational source for generation" in user
    assert "Do not copy passages, stems, or options" in user
    assert "00000000-0000-0000-0000-000000000001" in user


def test_extract_prompt_constrains_stem_vocab():
    """Pass 1 must instruct the LLM to emit canonical stem_type_key values."""
    system, _ = build_extract_prompt(raw_text="Some SAT text with a question.")
    assert "CONTROLLED VOCABULARY" in system
    # every canonical stem is listed as an allowed value
    from app.models.ontology import STEM_TYPE_KEYS
    for stem in STEM_TYPE_KEYS:
        assert stem in system
    # the cross-text rule uses the canonical key, not the old "compare_texts"
    assert "choose_cross_text_connection" in system
    assert 'stem_type_key to "compare_texts"' not in system


def test_canonicalize_stem_maps_known_aliases():
    # canonical values pass through unchanged
    assert canonicalize_stem("choose_words_in_context") == "choose_words_in_context"
    assert canonicalize_stem("complete_the_text") == "complete_the_text"
    # observed non-canonical aliases map to canonical keys
    assert canonicalize_stem("analyze_text_structure") == "choose_structure_description"
    assert canonicalize_stem("retrieve_detail") == "choose_detail"
    assert canonicalize_stem("support_claim") == "choose_best_support"
    assert canonicalize_stem("synthesize_notes") == "choose_best_notes_synthesis"
    assert canonicalize_stem("compare_texts") == "choose_cross_text_connection"
    # unknown alias returns None (caller leaves the value; routes to "unknown")
    assert canonicalize_stem("some_invented_stem") is None
    assert canonicalize_stem(None) is None
    # stimulus_mode canonicalization
    assert canonicalize_stimulus_mode("paired_prose") == "prose_paired"
    assert canonicalize_stimulus_mode("sentence_only") == "sentence_only"
    assert canonicalize_stimulus_mode("nonsense") is None


def test_stem_alias_targets_are_all_canonical():
    """Every alias must map to a real STEM_TYPE_KEYS value (never to another alias).

    Guards the Pass 1 safety-net so a typo'd target can't silently route a
    question to the wrong domain.
    """
    from app.prompts.extract_prompt import _STEM_ALIASES
    from app.models.ontology import STEM_TYPE_KEYS
    bad = {k: v for k, v in _STEM_ALIASES.items() if v not in STEM_TYPE_KEYS}
    assert not bad, f"alias targets not in STEM_TYPE_KEYS: {bad}"
