"""Tests for the review JSON parser and validator."""
import json

import pytest

from app.review.parser import (
    ReviewParseError,
    parse_review_json,
    validate_review_scores,
    REQUIRED_SCORE_KEYS,
    VALID_VERDICTS,
    MIN_SCORE,
    MAX_SCORE,
)


VALID_REVIEW = {
    "realism_score": 8.7,
    "sat_fidelity_score": 8.4,
    "difficulty_match_score": 7.9,
    "distractor_quality_score": 8.1,
    "taxonomy_match_score": 9.0,
    "explanation_quality_score": 8.2,
    "copy_risk_score": 1.1,
    "verdict": "accept",
}


class TestParseReviewJson:
    """Test parse_review_json happy path and error cases."""

    def test_parse_valid_review_json(self):
        raw = json.dumps(VALID_REVIEW)
        result = parse_review_json(raw)
        assert result["verdict"] == "accept"
        assert len(result["scores_jsonb"]) == 7
        assert result["scores_jsonb"]["realism_score"] == 8.7
        assert result["raw_response_jsonb"]["verdict"] == "accept"

    def test_parse_review_with_reasons(self):
        review = {
            **VALID_REVIEW,
            "reasons": {"copy_risk_score": "Paraphrase of source line 3"},
        }
        result = parse_review_json(json.dumps(review))
        assert result["review_notes"] is not None
        assert "copy_risk_score" in result["review_notes"]

    def test_parse_review_with_empty_reasons(self):
        review = {**VALID_REVIEW, "reasons": {}}
        result = parse_review_json(json.dumps(review))
        assert result["review_notes"] is None

    def test_parse_review_missing_required_score(self):
        for key in REQUIRED_SCORE_KEYS:
            broken = {k: v for k, v in VALID_REVIEW.items() if k != key}
            with pytest.raises(ReviewParseError, match=key):
                parse_review_json(json.dumps(broken))

    def test_parse_review_invalid_verdict(self):
        broken = {**VALID_REVIEW, "verdict": "maybe"}
        with pytest.raises(ReviewParseError, match="verdict"):
            parse_review_json(json.dumps(broken))

    def test_parse_review_score_out_of_range_high(self):
        broken = {**VALID_REVIEW, "realism_score": 11.0}
        with pytest.raises(ReviewParseError, match="out of range"):
            parse_review_json(json.dumps(broken))

    def test_parse_review_negative_score(self):
        broken = {**VALID_REVIEW, "realism_score": -1.0}
        with pytest.raises(ReviewParseError, match="out of range"):
            parse_review_json(json.dumps(broken))

    def test_parse_review_score_at_boundaries(self):
        # 0.0 and 10.0 should be valid
        for val in (0.0, 10.0):
            review = {**VALID_REVIEW, "realism_score": val}
            result = parse_review_json(json.dumps(review))
            assert result["scores_jsonb"]["realism_score"] == val

    def test_parse_review_with_markdown_fences(self):
        raw = f"```json\n{json.dumps(VALID_REVIEW)}\n```"
        result = parse_review_json(raw)
        assert result["verdict"] == "accept"

    def test_parse_review_needs_human_review_verdict(self):
        review = {**VALID_REVIEW, "verdict": "needs_human_review"}
        result = parse_review_json(json.dumps(review))
        assert result["verdict"] == "needs_human_review"

    def test_parse_review_reject_verdict(self):
        review = {**VALID_REVIEW, "verdict": "reject"}
        result = parse_review_json(json.dumps(review))
        assert result["verdict"] == "reject"

    def test_parse_review_extra_fields_ignored_in_scores(self):
        review = {**VALID_REVIEW, "extra_field": "ignored"}
        result = parse_review_json(json.dumps(review))
        assert "extra_field" in result["raw_response_jsonb"]
        assert "extra_field" not in result["scores_jsonb"]

    def test_parse_review_non_numeric_score(self):
        broken = {**VALID_REVIEW, "realism_score": "high"}
        with pytest.raises(ReviewParseError, match="numeric"):
            parse_review_json(json.dumps(broken))

    def test_parse_review_integer_scores_accepted(self):
        # Integer scores should be accepted (isinstance check includes int)
        review = {k: int(v) if isinstance(v, float) else v for k, v in VALID_REVIEW.items()}
        result = parse_review_json(json.dumps(review))
        assert result["scores_jsonb"]["realism_score"] == 8.0

    def test_parse_review_reasons_not_dict(self):
        broken = {**VALID_REVIEW, "reasons": "bad"}
        with pytest.raises(ReviewParseError, match="dict"):
            parse_review_json(json.dumps(broken))

    def test_parse_review_with_provider_name(self):
        # Provider and model name should be passed through to extract_json_from_text
        raw = json.dumps(VALID_REVIEW)
        result = parse_review_json(raw, provider_name="openai", model_name="gpt-4o")
        assert result["verdict"] == "accept"


class TestValidateReviewScores:
    """Test threshold validation for consensus logic."""

    def test_all_scores_above_threshold(self):
        scores = {
            "realism_score": 9.0,
            "sat_fidelity_score": 8.5,
            "distractor_quality_score": 8.0,
            "taxonomy_match_score": 9.0,
            "copy_risk_score": 1.0,
        }
        result = validate_review_scores(scores)
        assert result == []

    def test_realism_below_threshold(self):
        scores = {
            "realism_score": 5.0,
            "sat_fidelity_score": 8.5,
            "distractor_quality_score": 8.0,
            "taxonomy_match_score": 9.0,
            "copy_risk_score": 1.0,
        }
        result = validate_review_scores(scores)
        assert "realism_score" in result

    def test_copy_risk_above_threshold(self):
        scores = {
            "realism_score": 9.0,
            "sat_fidelity_score": 8.5,
            "distractor_quality_score": 8.0,
            "taxonomy_match_score": 9.0,
            "copy_risk_score": 7.5,
        }
        result = validate_review_scores(scores)
        assert "copy_risk_score" in result

    def test_multiple_below_threshold(self):
        scores = {
            "realism_score": 5.0,
            "sat_fidelity_score": 5.0,
            "distractor_quality_score": 5.0,
            "taxonomy_match_score": 5.0,
            "copy_risk_score": 6.0,
        }
        result = validate_review_scores(scores)
        assert "realism_score" in result
        assert "sat_fidelity_score" in result
        assert "distractor_quality_score" in result
        assert "taxonomy_match_score" in result
        assert "copy_risk_score" in result

    def test_missing_keys_ignored(self):
        # Only present keys are checked
        scores = {"realism_score": 5.0}
        result = validate_review_scores(scores)
        assert result == ["realism_score"]


class TestConstants:
    """Test that constants match the rubric spec."""

    def test_required_score_keys_count(self):
        assert len(REQUIRED_SCORE_KEYS) == 7

    def test_required_score_keys_match_rubric(self):
        expected = {
            "realism_score",
            "sat_fidelity_score",
            "difficulty_match_score",
            "distractor_quality_score",
            "taxonomy_match_score",
            "explanation_quality_score",
            "copy_risk_score",
        }
        assert set(REQUIRED_SCORE_KEYS) == expected

    def test_valid_verdicts(self):
        assert VALID_VERDICTS == ("accept", "needs_human_review", "reject")

    def test_score_range(self):
        assert MIN_SCORE == 0.0
        assert MAX_SCORE == 10.0