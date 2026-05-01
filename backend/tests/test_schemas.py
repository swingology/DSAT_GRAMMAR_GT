import pytest
from pydantic import ValidationError


def test_question_extract_valid():
    from app.models.extract import QuestionExtract
    data = {
        "question_text": "Which choice completes the text?",
        "passage_text": "The colony of corals ______ an important role.",
        "options": [
            {"label": "A", "text": "play"},
            {"label": "B", "text": "have played"},
            {"label": "C", "text": "plays"},
            {"label": "D", "text": "is playing"},
        ],
        "correct_option_label": "C",
        "source_exam_code": "PT4",
        "source_module_code": "M1",
        "source_question_number": 1,
    }
    q = QuestionExtract(**data)
    assert q.correct_option_label == "C"
    assert len(q.options) == 4


def test_question_extract_rejects_bad_label():
    from app.models.extract import QuestionExtract
    with pytest.raises(ValidationError):
        QuestionExtract(
            question_text="test",
            options=[{"label": "E", "text": "bad"}],
            correct_option_label="E",
        )


def test_question_annotation_valid():
    from app.models.annotation import QuestionAnnotation
    data = {
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
        "explanation_short": "Singular subject requires singular verb.",
        "explanation_full": "The grammatical subject is the singular noun colony.",
        "annotation_confidence": 0.95,
        "needs_human_review": False,
    }
    a = QuestionAnnotation(**data)
    assert a.grammar_focus_key == "subject_verb_agreement"


def test_question_annotation_valid_reading_domain():
    from app.models.annotation import QuestionAnnotation
    data = {
        "question_family_key": "information_and_ideas",
        "skill_family_key": "command_of_evidence_textual",
        "reading_focus_key": "evidence_supports_claim",
        "register": "academic informational",
        "difficulty_overall": "medium",
        "explanation_short": "The evidence directly supports the claim.",
        "explanation_full": "The cited detail is the only option that directly supports the stated claim.",
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    a = QuestionAnnotation(**data)
    assert a.reading_focus_key == "evidence_supports_claim"
    assert a.register_label == "academic informational"


def test_question_annotation_rejects_bad_focus():
    from app.models.annotation import QuestionAnnotation
    with pytest.raises(ValidationError):
        QuestionAnnotation(
            grammar_role_key="agreement",
            grammar_focus_key="not_a_real_key",
            syntactic_trap_key="none",
            difficulty_overall="medium",
            explanation_short="test",
            explanation_full="test",
            annotation_confidence=0.5,
            needs_human_review=False,
        )


def test_option_schema_valid():
    from app.models.options import OptionAnalysis
    data = {
        "option_label": "A",
        "option_text": "play",
        "is_correct": False,
        "option_role": "distractor",
        "distractor_type_key": "grammar_error",
        "why_plausible": "Nearest noun attraction",
        "why_wrong": "Subject is singular",
        "grammar_fit": "no",
        "tone_match": "yes",
        "precision_score": 1,
    }
    o = OptionAnalysis(**data)
    assert o.precision_score == 1


def test_question_recall_response():
    from app.models.payload import QuestionRecallResponse
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "content_origin": "official",
        "current_question_text": "Which choice completes the text?",
        "current_passage_text": "A passage here.",
        "current_correct_option_label": "C",
        "practice_status": "active",
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "difficulty_overall": "medium",
        "source_subject_code": "verbal",
        "source_section_code": "01",
        "source_module_code": "02",
        "generation_profile": {"model_version": "rules_agent_v7.0"},
    }
    r = QuestionRecallResponse(**data)
    assert r.practice_status == "active"
    assert r.generation_profile == {"model_version": "rules_agent_v7.0"}
    assert r.source_subject_code == "verbal"


def test_question_detail_response():
    from app.models.payload import QuestionDetailResponse
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "content_origin": "generated",
        "current_question_text": "Which choice completes the text?",
        "current_passage_text": "A passage here.",
        "current_correct_option_label": "C",
        "practice_status": "draft",
        "official_overlap_status": "none",
        "is_admin_edited": False,
        "generation_profile": {"model_version": "rules_agent_v7.0"},
    }
    r = QuestionDetailResponse(**data)
    assert r.generation_profile == {"model_version": "rules_agent_v7.0"}


def test_generation_request_valid():
    from app.models.payload import GenerationRequest
    req = GenerationRequest(
        target_grammar_role_key="agreement",
        target_grammar_focus_key="subject_verb_agreement",
        target_syntactic_trap_key="nearest_noun_attraction",
        difficulty_overall="medium",
    )
    assert req.target_grammar_focus_key == "subject_verb_agreement"


def test_generation_compare_request_valid():
    from app.models.payload import GenerationCompareRequest
    req = GenerationCompareRequest(
        target_grammar_role_key="agreement",
        target_grammar_focus_key="subject_verb_agreement",
        providers=["anthropic", "openai"],
    )
    assert len(req.providers) == 2


def test_job_response_model():
    from app.models.payload import JobResponse
    j = JobResponse(id="abc-123", job_type="ingest", status="parsing", question_id=None)
    assert j.status == "parsing"
