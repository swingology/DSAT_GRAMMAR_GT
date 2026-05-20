"""Tests for the review prompt composer."""
import json
import os

import pytest

# Ensure the project root is on the path so the rules files are found.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _grammar_question():
    return {
        "question_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
        "passage_text": "The researchers noted that the compound, unlike its predecessors, ______ effective at lower concentrations.",
        "correct_option_label": "A",
        "options": [
            {"label": "A", "text": "remains"},
            {"label": "B", "text": "remain"},
            {"label": "C", "text": "are remaining"},
            {"label": "D", "text": "have remained"},
        ],
        "grammar_focus_key": "subject_verb_agreement",
        "grammar_role_key": "agreement",
    }


def _reading_question():
    q = _grammar_question()
    q["question_family_key"] = "craft_and_structure"
    q["reading_skill_family_key"] = "words_in_context"
    q["reading_focus_key"] = "contextual_meaning"
    return q


def _grammar_annotation():
    return {
        "grammar_focus_key": "subject_verb_agreement",
        "grammar_role_key": "agreement",
        "syntactic_trap_key": "nearest_noun_attraction",
        "annotation_confidence": 0.92,
    }


def _reading_annotation():
    return {
        "reading_skill_family_key": "words_in_context",
        "reading_focus_key": "contextual_meaning",
        "question_family_key": "craft_and_structure",
    }


class TestBuildReviewPrompt:
    """Test build_review_prompt composition."""

    def test_review_prompt_includes_rubric(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="none",
            generation_request={"target_grammar_focus_key": "subject_verb_agreement"},
        )
        # The rubric file should appear in the system prompt
        assert "Review v1 RULES REFERENCE" in system
        assert "realism_score" in system
        assert "verdict" in system.lower()

    def test_review_prompt_always_includes_grammar_v7(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="none",
        )
        assert "Grammar v7 RULES REFERENCE" in system

    def test_review_prompt_includes_reading_v2_for_reading_questions(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_reading_question(),
            annotation=_reading_annotation(),
            source_examples=[],
            overlap_status="none",
        )
        assert "Reading v2 RULES REFERENCE" in system

    def test_review_prompt_excludes_reading_v2_for_grammar_questions(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="none",
        )
        assert "Reading v2 RULES REFERENCE" not in system

    def test_review_prompt_includes_overlap_status(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="possible",
        )
        assert "overlap status: possible" in user

    def test_review_prompt_includes_source_examples(self):
        from app.prompts.review_prompt import build_review_prompt

        examples = [{"question_text": "Official Q1", "correct_option_label": "B"}]
        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=examples,
            overlap_status="none",
        )
        assert "Official source questions" in user
        assert "Official Q1" in user

    def test_review_prompt_includes_generation_request(self):
        from app.prompts.review_prompt import build_review_prompt

        request = {"target_grammar_focus_key": "subject_verb_agreement", "difficulty_overall": "medium"}
        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="none",
            generation_request=request,
        )
        assert "Original generation request" in user
        assert "subject_verb_agreement" in user

    def test_review_prompt_includes_annotation(self):
        from app.prompts.review_prompt import build_review_prompt

        system, user = build_review_prompt(
            question_data=_grammar_question(),
            annotation=_grammar_annotation(),
            source_examples=[],
            overlap_status="none",
        )
        assert "Question annotation" in user
        assert "subject_verb_agreement" in user


class TestReviewVersionConstants:
    """Test version and rules constants."""

    def test_rubric_version(self):
        from app.prompts.review_prompt import RUBRIC_VERSION

        assert RUBRIC_VERSION == "v1"

    def test_rules_versions(self):
        from app.prompts.review_prompt import RULES_VERSIONS

        assert "grammar" in RULES_VERSIONS
        assert "reading" in RULES_VERSIONS
        assert RULES_VERSIONS["grammar"] == "v7"
        assert RULES_VERSIONS["reading"] == "v2"


class TestInferReviewDomain:
    """Test domain inference for review prompts."""

    def test_grammar_question(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain(_grammar_question(), _grammar_annotation()) == "grammar"

    def test_reading_question(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain(_reading_question(), _reading_annotation()) == "reading"

    def test_default_both(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain({}, None) == "both"

    def test_reading_from_annotation(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain({}, {"reading_skill_family_key": "words_in_context"}) == "reading"

    def test_grammar_from_annotation(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain({}, {"grammar_focus_key": "subject_verb_agreement"}) == "grammar"

    def test_question_family_reading(self):
        from app.prompts.review_prompt import _infer_review_domain

        assert _infer_review_domain({"question_family_key": "craft_and_structure"}, None) == "reading"