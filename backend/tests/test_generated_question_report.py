"""Renderer check for the generated-question Markdown report (pure function,
no DB). Fails if lineage, options, self-check, or review sections stop
rendering from the admin serializer's item shape."""

from app.reports.generated_question_report import render_generated_question_report


def _item():
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "practice_status": "draft",
        "official_overlap_status": "none",
        "domain": "reading",
        "question_text": "Which choice most logically completes the text?",
        "passage_text": "First sentence here. Second, longer sentence with a clause; and a semicolon. Third ______",
        "correct_option_label": "B",
        "annotation": {
            "question_family_key": "information_and_ideas",
            "reading_skill_family_key": "inferences",
            "reading_focus_key": "implication_inference",
            "reasoning_trap_key": "overreach",
            "difficulty_overall": "high",
            "evidence_span_text": "Second, longer sentence",
            "annotation_confidence": 0.9,
        },
        "annotation_explanation": {"explanation_full": "Because the passage says so."},
        "generation_profile": {"target_reading_focus_key": "implication_inference"},
        "self_check": {"distractor_directions_verified": True, "notes": "none"},
        "generation_source_set": {
            "source_question_ids": ["aaaa"],
            "target_reading_focus_key": "implication_inference",
            "difficulty_overall": "high",
        },
        "derived_from_question_id": "aaaa",
        "options": [
            {"label": "A", "text": "wrong | with pipe", "is_correct": False,
             "distractor_type_key": "contradiction", "plausibility_source_key": "topical_proximity",
             "precision_score": 1, "why_wrong": "Says the opposite."},
            {"label": "B", "text": "right", "is_correct": True, "distractor_type_key": "correct", "precision_score": 3},
        ],
        "job": {"id": "job1", "status": "approved", "provider_name": "anthropic", "model_name": "claude-opus-5",
                "validation_errors_jsonb": [{"severity": "review", "field": "x", "message": "check me"}]},
        "batch": {"id": "batch1", "status": "completed", "release_policy": "admin_review_required"},
        "consensus": {"consensus_verdict": "admin_review_ready", "reviewer_count": 1,
                      "accept_votes": 1, "needs_review_votes": 0, "reject_votes": 0,
                      "reviewer_disagreement": 0.0, "high_disagreement_flag": False,
                      "average_realism": 8.5, "reasons_jsonb": {}},
        "review_results": [
            {"provider_name": "ollama", "model_name": "kimi-k3:cloud", "verdict": "accept",
             "review_status": "ok", "scores_jsonb": {"realism_score": 8.5, "copy_risk_score": 1.0},
             "review_notes": "Solid item."},
        ],
        "source_examples": [{"id": "aaaa", "source_test_name": "PT10", "source_module_code": "M2",
                             "source_question_number": 17, "question_text": "Ref stem"}],
        "created_at": "2026-09-05T00:00:00+00:00",
    }


def test_report_renders_every_section():
    md = render_generated_question_report(_item())
    for needle in (
        "# Generated Question Report — reading · inferences · implication_inference · high",
        "## Lineage", "`aaaa` — PT10 · Mod M2 · Q17",
        "## Phase 1 — generation_profile", '"target_reading_focus_key": "implication_inference"',
        "## Phase 2 — Passage (", "3 sentences",
        "## Phase 4 — Options", "**B ✅**", "wrong \\| with pipe",   # pipe escaped so the table survives
        "## Template (annotation)", "| reasoning_trap_key | overreach |",
        "## Phase 5 — Generator self-check", "**distractor_directions_verified:** true",
        "## Review swarm", "ollama/kimi-k3:cloud", "`admin_review_ready`",
        "## Validation notes", "check me",
    ):
        assert needle in md, needle
    # source_question_ids is lineage, not part of the target spec block
    assert '"source_question_ids"' not in md


def test_report_tolerates_sparse_item():
    md = render_generated_question_report({"id": "x", "options": [], "annotation": None})
    assert "_no generation_profile stored_" in md
    assert "_no reviewer results yet_" in md
    assert "_no self_check emitted" in md
