"""Phase 5 (consensus gate) — deterministic verdict computation tests.

Tests cover each verdict path of the ordered first-match-wins algorithm:
  1. blocked_overlap (any unresolved official overlap)
  2. insufficient_reviews (fewer than two successful reviewers)
  3. reject_recommended (high copy risk)
  4. reject_recommended (low realism)
  5. admin_review_ready with high_disagreement_flag
  6. regenerate_recommended (below-threshold dimension)
  7. admin_review_ready (all thresholds cleared)
"""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.review.consensus import compute_consensus


def _make_review_result(
    *,
    realism_score: float = 8.0,
    sat_fidelity_score: float = 8.0,
    difficulty_match_score: float = 7.5,
    distractor_quality_score: float = 7.5,
    taxonomy_match_score: float = 8.0,
    explanation_quality_score: float = 7.5,
    copy_risk_score: float = 2.0,
    verdict: str = "accept",
    review_status: str = "ok",
) -> MagicMock:
    """Return a mock LlmReviewResult with the given scores and verdict."""
    result = MagicMock()
    result.review_status = review_status
    result.verdict = verdict
    result.scores_jsonb = {
        "realism_score": realism_score,
        "sat_fidelity_score": sat_fidelity_score,
        "difficulty_match_score": difficulty_match_score,
        "distractor_quality_score": distractor_quality_score,
        "taxonomy_match_score": taxonomy_match_score,
        "explanation_quality_score": explanation_quality_score,
        "copy_risk_score": copy_risk_score,
    }
    return result


def _make_settings(**overrides):
    """Return mock settings with consensus threshold defaults."""
    defaults = dict(
        generation_min_realism_score=7.0,
        generation_min_sat_fidelity_score=7.0,
        generation_min_distractor_quality_score=6.5,
        generation_min_taxonomy_match_score=7.5,
        generation_max_copy_risk_score=5.0,
        generation_max_reviewer_disagreement=1.5,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Verdict path 1: blocked_overlap
# ---------------------------------------------------------------------------

class TestBlockedOverlap:

    def test_confirmed_overlap_yields_blocked_overlap(self):
        """Confirmed overlap status produces blocked_overlap regardless of scores."""
        settings = _make_settings()
        reviews = [_make_review_result(realism_score=9.5), _make_review_result(realism_score=9.0)]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="confirmed")
        assert result["consensus_verdict"] == "blocked_overlap"
        assert "confirmed" in result["reasons_jsonb"][0].lower()

    def test_possible_overlap_yields_blocked_overlap(self):
        """Possible overlap is unresolved overlap and blocks consensus approval."""
        settings = _make_settings()
        reviews = [_make_review_result(realism_score=8.0), _make_review_result(realism_score=8.5)]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="possible")
        assert result["consensus_verdict"] == "blocked_overlap"
        assert any("possible" in r.lower() for r in result["reasons_jsonb"])


# ---------------------------------------------------------------------------
# Verdict path 2: insufficient_reviews
# ---------------------------------------------------------------------------

class TestInsufficientReviews:

    def test_no_reviews_yields_insufficient(self):
        """Zero successful reviews produces insufficient_reviews."""
        result = compute_consensus([], overlap_status="none")
        assert result["consensus_verdict"] == "insufficient_reviews"
        assert result["reviewer_count"] == 0
        assert result["average_realism"] is None

    def test_all_failed_reviews_yields_insufficient(self):
        """Reviews with review_status != 'ok' are filtered out."""
        failed = _make_review_result(review_status="permanent_failed")
        result = compute_consensus([failed], overlap_status="none")
        assert result["consensus_verdict"] == "insufficient_reviews"
        assert result["reviewer_count"] == 0

    def test_transient_failed_also_filtered(self):
        failed = _make_review_result(review_status="transient_failed")
        result = compute_consensus([failed], overlap_status="none")
        assert result["consensus_verdict"] == "insufficient_reviews"

    def test_single_successful_review_yields_insufficient(self):
        result = compute_consensus([_make_review_result()], overlap_status="none")
        assert result["consensus_verdict"] == "insufficient_reviews"
        assert result["reviewer_count"] == 1


# ---------------------------------------------------------------------------
# Verdict path 3: reject_recommended (high copy risk)
# ---------------------------------------------------------------------------

class TestRejectHighCopyRisk:

    def test_copy_risk_above_threshold(self):
        """Any reviewer reporting copy risk > 5.0 triggers reject_recommended."""
        settings = _make_settings()
        reviews = [
            _make_review_result(copy_risk_score=6.0, realism_score=9.0),
            _make_review_result(copy_risk_score=2.0, realism_score=9.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "reject_recommended"
        assert "copy risk" in result["reasons_jsonb"][0].lower()

    def test_copy_risk_at_threshold_rejected(self):
        """Copy risk exactly at threshold (5.0) triggers reject."""
        settings = _make_settings()
        reviews = [
            _make_review_result(copy_risk_score=5.0, realism_score=8.0),
            _make_review_result(copy_risk_score=2.0, realism_score=8.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "reject_recommended"


# ---------------------------------------------------------------------------
# Verdict path 4: reject_recommended (low realism)
# ---------------------------------------------------------------------------

class TestRejectLowRealism:

    def test_low_realism_yields_reject(self):
        """Average realism below threshold triggers reject_recommended."""
        settings = _make_settings()
        reviews = [_make_review_result(realism_score=5.0), _make_review_result(realism_score=6.0)]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "reject_recommended"
        assert "realism" in result["reasons_jsonb"][0].lower()

    def test_realism_at_threshold_not_rejected(self):
        """Realism exactly at threshold (7.0) does NOT trigger reject."""
        settings = _make_settings()
        reviews = [_make_review_result(realism_score=7.0), _make_review_result(realism_score=7.0)]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "admin_review_ready"


class TestRejectLowSatFidelity:

    def test_low_sat_fidelity_yields_reject(self):
        """Average SAT fidelity below threshold triggers reject_recommended."""
        settings = _make_settings()
        reviews = [
            _make_review_result(realism_score=8.0, sat_fidelity_score=5.0),
            _make_review_result(realism_score=8.0, sat_fidelity_score=6.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "reject_recommended"
        assert "sat fidelity" in result["reasons_jsonb"][0].lower()


# ---------------------------------------------------------------------------
# Verdict path 5: high_disagreement_flag
# ---------------------------------------------------------------------------

class TestHighDisagreement:

    def test_high_disagreement_sets_flag(self):
        """High reviewer disagreement sets high_disagreement_flag but still
        produces admin_review_ready (not reject)."""
        settings = _make_settings()
        reviews = [
            _make_review_result(realism_score=10.0, distractor_quality_score=9.0),
            _make_review_result(realism_score=6.0, distractor_quality_score=9.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        # All thresholds pass, so verdict is admin_review_ready
        # but disagreement should be flagged
        assert result["consensus_verdict"] == "admin_review_ready"
        assert result["high_disagreement_flag"] is True

    def test_verdict_disagreement_sets_flag(self):
        """Different reviewer verdicts also trigger disagreement."""
        settings = _make_settings()
        reviews = [
            _make_review_result(verdict="accept"),
            _make_review_result(verdict="needs_human_review"),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "admin_review_ready"
        assert result["high_disagreement_flag"] is True


# ---------------------------------------------------------------------------
# Verdict path 6: regenerate_recommended
# ---------------------------------------------------------------------------

class TestRegenerateRecommended:

    def test_taxonomy_below_threshold_yields_regenerate(self):
        """A dimension below threshold (but not realism or copy risk) produces
        regenerate_recommended instead of reject_recommended."""
        settings = _make_settings()
        reviews = [
            _make_review_result(taxonomy_match_score=6.0, realism_score=8.0),
            _make_review_result(taxonomy_match_score=6.0, realism_score=8.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "regenerate_recommended"
        assert "taxonomy" in result["reasons_jsonb"][0].lower()

    def test_distractor_below_threshold_yields_regenerate(self):
        settings = _make_settings()
        reviews = [
            _make_review_result(distractor_quality_score=5.5, realism_score=8.0),
            _make_review_result(distractor_quality_score=5.5, realism_score=8.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "regenerate_recommended"


# ---------------------------------------------------------------------------
# Verdict path 7: admin_review_ready
# ---------------------------------------------------------------------------

class TestAdminReviewReady:

    def test_all_thresholds_cleared(self):
        """All thresholds met produces admin_review_ready."""
        settings = _make_settings()
        reviews = [
            _make_review_result(
                realism_score=8.5,
                sat_fidelity_score=8.0,
                distractor_quality_score=7.5,
                taxonomy_match_score=8.0,
                copy_risk_score=2.0,
            ),
            _make_review_result(
                realism_score=8.0,
                sat_fidelity_score=8.0,
                distractor_quality_score=7.5,
                taxonomy_match_score=8.0,
                copy_risk_score=2.0,
            ),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "admin_review_ready"
        assert result["reviewer_count"] == 2
        assert result["accept_votes"] == 2
        assert result["reject_votes"] == 0
        assert result["average_realism"] == 8.25

    def test_multiple_reviewers_averages(self):
        """Averages are computed correctly across multiple reviewers."""
        settings = _make_settings()
        reviews = [
            _make_review_result(realism_score=8.0, copy_risk_score=2.0, verdict="accept"),
            _make_review_result(realism_score=9.0, copy_risk_score=3.0, verdict="accept"),
            _make_review_result(realism_score=7.5, copy_risk_score=1.0, verdict="needs_human_review"),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "admin_review_ready"
        assert result["reviewer_count"] == 3
        assert result["accept_votes"] == 2
        assert result["needs_review_votes"] == 1
        assert result["reject_votes"] == 0
        assert abs(result["average_realism"] - 8.17) < 0.01
        assert result["max_copy_risk"] == 3.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_failed_reviewer_excluded_from_averages(self):
        """Reviewers with review_status != 'ok' are excluded from averages."""
        settings = _make_settings()
        ok_review = _make_review_result(realism_score=8.0, copy_risk_score=2.0)
        second_ok_review = _make_review_result(realism_score=8.0, copy_risk_score=2.0)
        failed_review = _make_review_result(
            realism_score=3.0, copy_risk_score=8.0,
            review_status="permanent_failed", verdict="reject"
        )
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus([ok_review, second_ok_review, failed_review], overlap_status="none")
        # Only successful reviews counted
        assert result["reviewer_count"] == 2
        assert result["average_realism"] == 8.0
        assert result["max_copy_risk"] == 2.0
        assert result["consensus_verdict"] == "admin_review_ready"

    def test_copy_risk_priority_over_low_realism(self):
        """Copy risk check happens before realism check in the ordered algorithm.
        A question with both high copy risk AND low realism gets reject_recommended
        with a copy risk reason, not a realism reason."""
        settings = _make_settings()
        reviews = [
            _make_review_result(copy_risk_score=7.0, realism_score=5.0),
            _make_review_result(copy_risk_score=2.0, realism_score=5.0),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="none")
        assert result["consensus_verdict"] == "reject_recommended"
        assert "copy risk" in result["reasons_jsonb"][0].lower()

    def test_blocked_overlap_overrides_everything(self):
        """Even with perfect scores, confirmed overlap blocks."""
        settings = _make_settings()
        reviews = [
            _make_review_result(realism_score=10.0, copy_risk_score=0.5),
            _make_review_result(realism_score=9.5, copy_risk_score=0.5),
        ]
        with pytest.MonkeyPatch.context() as mp:
            for key, val in vars(settings).items():
                mp.setattr(f"app.config.Settings.{key}", val, raising=False)
            result = compute_consensus(reviews, overlap_status="confirmed")
        assert result["consensus_verdict"] == "blocked_overlap"
